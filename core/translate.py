"""Translation providers.

Order of preference:
1. A user-configured OpenAI-compatible LLM (best context, terminology, tone).
2. MyMemory's public translation memory (works without a key, block-by-block).
3. Google's public gtx endpoint (when reachable).
4. A clearly-labelled offline preview.

All providers are behind one block-level API so sentence/paragraph alignment is
preserved in the reader.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from . import store
from .net import SSL_CONTEXT
from .text import LANGUAGES, chunk_text, group_blocks, normalize_text

PROVIDER_LABELS = {
    "auto": "自动优选",
    "ai": "AI 精准模式",
    "mymemory": "MyMemory 免费引擎",
    "google": "Google 免费引擎",
    "offline": "本地预览",
}
PROVIDER_NOTES = {
    "ai": "上下文整段翻译，术语和语气最稳",
    "mymemory": "免密钥，逐段调用公共翻译记忆",
    "google": "免密钥，需网络可访问 Google",
    "offline": "仅用于断网演示，质量有限",
}

STYLE_PROMPTS = {
    "natural": "自然、流畅、像目标语言的母语写作；不要翻译腔。",
    "faithful": "忠实、克制、尽量保留原文句法和语气；不要增删信息。",
    "academic": "正式、学术、术语精确；适合论文、报告和知识类文章。",
    "literary": "保留文学性和节奏，允许意译，但不要改写情节或观点。",
}

_COOLDOWN: dict[str, float] = {}
_COOLDOWN_LOCK = threading.Lock()
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/138.0 Safari/537.36 LinguaLens/1.0")


class TranslationError(RuntimeError):
    pass


def _cooling(provider: str) -> bool:
    with _COOLDOWN_LOCK:
        return time.time() < _COOLDOWN.get(provider, 0)


def _cooldown(provider: str, seconds: int = 300) -> None:
    with _COOLDOWN_LOCK:
        _COOLDOWN[provider] = time.time() + seconds


def _urlopen_json(url: str, payload: dict | None = None, timeout: int = 22, headers: dict | None = None) -> dict | list:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url, data=data,
        headers={"User-Agent": _UA, "Accept": "application/json", **(headers or {})},
        method="GET" if data is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
            raw = response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        raise TranslationError(f"HTTP {exc.code}: {detail or exc.reason}") from exc
    except Exception as exc:
        raise TranslationError(str(exc)) from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TranslationError("翻译服务返回了无法解析的内容") from exc


def _join_chunks(chunks: list[str], target: str, original: str) -> str:
    if not chunks:
        return ""
    joiner = "" if target in ("zh-CN", "zh-TW", "ja", "ko", "th") else " "
    if any("\n" in c for c in chunks):
        joiner = "\n"
    text = joiner.join(c.strip() for c in chunks if c.strip())
    # Remove spaces the engine inserts between CJK characters.
    if target in ("zh-CN", "zh-TW", "ja", "ko"):
        text = re.sub(r"(?<=[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7a3])\s+(?=[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7a3])", "", text)
    # Restore paragraph breaks proportionally if the original had them.
    paragraphs = len([p for p in re.split(r"\n\s*\n", original) if p.strip()])
    if paragraphs > 1 and "\n" not in text:
        pieces = re.split(r"(?<=[。！？.!?])\s*", text)
        if len(pieces) >= paragraphs:
            per = max(1, len(pieces) // paragraphs)
            rebuilt, i = [], 0
            for _ in range(paragraphs - 1):
                rebuilt.append("".join(pieces[i:i + per]))
                i += per
            rebuilt.append("".join(pieces[i:]))
            text = "\n\n".join(p for p in rebuilt if p)
    return text.strip()


def _cache_key(provider: str, source: str, target: str, text: str) -> str:
    raw = f"{provider}|{source}|{target}|{text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _glossary_pairs(raw: str) -> list[tuple[str, str]]:
    pairs = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^(.+?)\s*(?:=>|->|\t|=)\s*(.+?)\s*$", line)
        if not match:
            continue
        source, target = match.group(1).strip(), match.group(2).strip()
        if source and target and source != target:
            pairs.append((source, target))
    return pairs


def _apply_glossary(text: str, raw: str) -> str:
    if not text or not raw:
        return text
    for source, target in _glossary_pairs(raw):
        if re.search(r"[A-Za-z]", source):
            text = re.sub(
                r"(?<![A-Za-z])" + re.escape(source) + r"(?![A-Za-z])",
                target, text, flags=re.I,
            )
        else:
            text = text.replace(source, target)
    return text


class MockOffline:
    """A graceful, clearly labelled fallback. Not sold as real translation."""

    PHRASES = {
        "hello": "你好", "world": "世界", "good morning": "早上好", "thank you": "谢谢",
        "language": "语言", "book": "书", "article": "文章", "reading": "阅读",
        "the": "", "a": "", "an": "", "and": "和", "of": "的", "to": "去",
    }

    @classmethod
    def translate(cls, text: str, target: str) -> str:
        if target not in ("zh-CN", "zh-TW"):
            return f"[离线预览] {text}"
        out = text
        for src, dst in sorted(cls.PHRASES.items(), key=lambda kv: -len(kv[0])):
            out = re.sub(rf"\b{re.escape(src)}\b", dst, out, flags=re.I)
        if not any("\u4e00" <= c <= "\u9fff" for c in out):
            out = "[离线预览，建议连接网络或配置 AI] " + text
        return out


# ---------------------------------------------------------------------------
# MyMemory
# ---------------------------------------------------------------------------

def mymemory_translate(text: str, source: str, target: str) -> str:
    if not text.strip():
        return ""
    chunks = chunk_text(text, 440)
    results = []
    for chunk in chunks:
        params = urllib.parse.urlencode({
            "q": chunk, "langpair": f"{source}|{target}", "mt": "1",
        })
        url = "https://api.mymemory.translated.net/get?" + params
        payload = _urlopen_json(url, timeout=22)
        if not isinstance(payload, dict):
            raise TranslationError("MyMemory 返回格式异常")
        status = payload.get("responseStatus")
        if status and int(status) >= 400:
            raise TranslationError(f"MyMemory: {payload.get('responseDetails') or status}")
        translated = ((payload.get("responseData") or {}).get("translatedText") or "").strip()
        if not translated:
            raise TranslationError("MyMemory 没有返回译文")
        if translated.upper().startswith("MYMEMORY WARNING"):
            raise TranslationError("MyMemory 今日额度已用完")
        results.append(translated)
        time.sleep(0.15)
    return _join_chunks(results, target, text)


# ---------------------------------------------------------------------------
# Google gtx
# ---------------------------------------------------------------------------

def google_translate(text: str, source: str, target: str) -> str:
    if not text.strip():
        return ""
    chunks = chunk_text(text, 1800)
    results = []
    for chunk in chunks:
        params = urllib.parse.urlencode({
            "client": "gtx", "sl": source, "tl": target, "dt": "t", "q": chunk,
        })
        url = "https://translate.googleapis.com/translate_a/single?" + params
        request = urllib.request.Request(url, headers={"User-Agent": _UA})
        try:
            with urllib.request.urlopen(request, timeout=12, context=SSL_CONTEXT) as response:
                data = json.loads(response.read().decode("utf-8", "replace"))
        except Exception as exc:
            _cooldown("google", 900)
            raise TranslationError(f"Google 无法访问：{exc}") from exc
        try:
            translated = "".join(part[0] for part in data[0] if part and part[0])
        except Exception as exc:
            raise TranslationError("Google 返回格式异常") from exc
        results.append(translated)
    return _join_chunks(results, target, text)


# ---------------------------------------------------------------------------
# OpenAI-compatible LLM
# ---------------------------------------------------------------------------

def _chat_url(base: str) -> str:
    base = (base or "https://api.deepseek.com/v1").strip().rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    if "api.openai.com" in base:
        return base + "/v1/chat/completions"
    return base + "/chat/completions"


class AIClient:
    def __init__(self, config: dict):
        self.api_key = (config or {}).get("apiKey", "").strip()
        self.base_url = (config or {}).get("baseUrl", "").strip() or "https://api.deepseek.com/v1"
        self.model = (config or {}).get("model", "").strip() or "deepseek-chat"
        self.temperature = float((config or {}).get("temperature", 0.2) or 0.2)
        self.translation_style = (config or {}).get("translationStyle", "natural") or "natural"

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def chat(self, system: str, user: str, json_mode: bool = True, max_tokens: int = 4096) -> str:
        if not self.configured:
            raise TranslationError("尚未配置 AI API Key")
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        last_error = None
        for attempt in range(2):
            payload = dict(body)
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            try:
                data = _urlopen_json(_chat_url(self.base_url), payload, timeout=120, headers=headers)
            except TranslationError as exc:
                last_error = exc
                if json_mode and ("response_format" in str(exc) or "400" in str(exc)):
                    json_mode = False
                    continue
                if attempt == 0:
                    time.sleep(0.8)
                    continue
                break
            if not isinstance(data, dict):
                last_error = TranslationError("AI 返回格式异常")
                continue
            choices = data.get("choices") or []
            if not choices:
                last_error = TranslationError((data.get("error") or {}).get("message") or "AI 没有返回内容")
                continue
            message = choices[0].get("message") or {}
            content = message.get("content") or ""
            if content:
                return content
            last_error = TranslationError("AI 返回内容为空")
        raise last_error or TranslationError("AI 请求失败")

    def translate_blocks(self, blocks: list[dict], source: str, target: str) -> dict[int, str]:
        out: dict[int, str] = {}
        groups = group_blocks(blocks, max_chars=7600, max_blocks=22)
        src_name = LANGUAGES.get(source, {}).get("name", source)
        tgt_name = LANGUAGES.get(target, {}).get("name", target)
        for group in groups:
            items = [{"id": b["id"], "type": b.get("type", "paragraph"), "text": b["text"]} for b in group]
            system = (
                "You are a senior literary and technical translator. Translate faithfully and naturally, "
                "preserving tone, register, terminology and all factual detail. Never summarize, explain, "
                "or add content. Keep names, numbers, citations and markdown symbols intact. "
                "Return ONLY valid JSON."
            )
            user = (
                f"Translate these blocks from {src_name} ({source}) into {tgt_name} ({target}).\n"
                f"Style: {STYLE_PROMPTS.get(self.translation_style, STYLE_PROMPTS['natural'])}\n"
                "Translate every block, including headings and list items. Keep the same id. "
                "Use consistent terminology across blocks. For Chinese use Simplified unless the target is zh-TW. "
                "For Japanese use natural written Japanese (です・ます for expository prose).\n"
                'Return JSON exactly in this shape: {"translations":[{"id":1,"text":"..."}]}.\n\n'
                "BLOCKS:\n" + json.dumps(items, ensure_ascii=False)
            )
            content = self.chat(system, user, json_mode=True, max_tokens=min(8192, 1500 + len(group) * 380))
            parsed = _parse_json_response(content)
            translations = parsed.get("translations") if isinstance(parsed, dict) else parsed
            if isinstance(translations, list):
                by_id = {}
                for item in translations:
                    if not isinstance(item, dict):
                        continue
                    try:
                        by_id[int(item.get("id"))] = str(item.get("text") or "").strip()
                    except (TypeError, ValueError):
                        continue
                for block in group:
                    if by_id.get(block["id"]):
                        out[block["id"]] = by_id[block["id"]]
            missing = [b for b in group if b["id"] not in out]
            if missing and len(missing) == len(group):
                raise TranslationError("AI 未返回可用的逐段译文")
        return out


def _parse_json_response(content: str) -> dict | list:
    text = (content or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    start_candidates = [i for i in (text.find("{"), text.find("[")) if i >= 0]
    if start_candidates:
        start = min(start_candidates)
        end = max(text.rfind("}"), text.rfind("]"))
        if end > start:
            text = text[start:end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise TranslationError("AI 返回的 JSON 无法解析") from exc


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def _provider_order(requested: str, settings: dict) -> list[str]:
    ai_ready = AIClient(settings.get("ai", {})).configured
    if requested == "ai":
        return ["ai", "mymemory", "offline"]
    if requested == "mymemory":
        return ["mymemory", "google", "offline"]
    if requested == "google":
        return ["google", "mymemory", "offline"]
    if requested == "offline":
        return ["offline"]
    order = []
    if ai_ready:
        order.append("ai")
    order.extend(["mymemory", "google", "offline"])
    return order


def translate_blocks(blocks: list[dict], source: str, target: str, provider: str = "auto",
                     settings: dict | None = None, use_cache: bool = True) -> dict:
    settings = settings or store.get_settings(include_secret=True)
    translatable = [b for b in blocks if b.get("translate") is not False]
    if not translatable:
        return {"translations": {}, "provider": "none", "warnings": [], "cached": 0}
    if source == target:
        return {
            "translations": {b["id"]: b["text"] for b in translatable},
            "provider": "copy", "warnings": ["源语言与目标语言相同，已保留原文。"], "cached": 0,
        }

    cache_hits: dict[int, str] = {}
    if use_cache:
        for block in translatable:
            key = _cache_key(provider, source, target, block["text"])
            cached = store.cache_get(key)
            if cached:
                cache_hits[block["id"]] = cached
    pending = [b for b in translatable if b["id"] not in cache_hits]
    warnings: list[str] = []
    used = []

    def finalize(translations: dict[int, str], used_provider: str) -> dict:
        merged = {**{b["id"]: b["text"] for b in blocks if b.get("translate") is False}, **cache_hits, **translations}
        glossary = settings.get("glossary", "")
        if glossary:
            targets = {b["id"] for b in blocks if b.get("translate") is not False}
            merged = {bid: (_apply_glossary(value, glossary) if bid in targets and isinstance(value, str) else value)
                      for bid, value in merged.items()}
        if used_provider != "offline":
            _cache_results(pending, translations, provider, source, target)
        return {
            "translations": merged,
            "provider": used_provider,
            "providerLabel": PROVIDER_LABELS.get(used_provider, used_provider),
            "warnings": warnings,
            "cached": len(cache_hits),
        }

    if not pending:
        return finalize({}, "cache" if not cache_hits else provider)

    for name in _provider_order(provider, settings):
        if name == "offline":
            # Keep source + explicit marker instead of pretending this is a translation.
            offline = {b["id"]: MockOffline.translate(b["text"], target) for b in pending}
            warnings.append("已切换到离线预览；配置 AI Key 或联网后可获得真实翻译。")
            return finalize(offline, "offline")
        if _cooling(name):
            warnings.append(f"{PROVIDER_LABELS.get(name, name)} 暂时不可用，已跳过。")
            continue
        try:
            if name == "ai":
                ai_config = dict(settings.get("ai", {}))
                ai_config["translationStyle"] = settings.get("translationStyle", "natural")
                client = AIClient(ai_config)
                if not client.configured:
                    continue
                result = client.translate_blocks(pending, source, target)
                missing = [b for b in pending if b["id"] not in result]
                if missing:
                    # Fill missing blocks via MyMemory without discarding good AI work.
                    warnings.append(f"AI 漏译 {len(missing)} 段，已用免费引擎补齐。")
                    for block in missing:
                        try:
                            result[block["id"]] = mymemory_translate(block["text"], source, target)
                        except Exception:
                            result[block["id"]] = block["text"]
                    used.append("ai")
                    final = finalize(result, "mixed")
                    return final
                used.append("ai")
                final = finalize(result, "ai")
                return final
            if name == "mymemory":
                result = {}
                for block in pending:
                    result[block["id"]] = mymemory_translate(block["text"], source, target)
                used.append("mymemory")
                final = finalize(result, "mymemory")
                return final
            if name == "google":
                result = {}
                for block in pending:
                    result[block["id"]] = google_translate(block["text"], source, target)
                used.append("google")
                final = finalize(result, "google")
                return final
        except Exception as exc:
            message = str(exc).replace("\n", " ")[:240]
            warnings.append(f"{PROVIDER_LABELS.get(name, name)} 失败：{message}")
            if name in ("google",):
                _cooldown(name, 900)
            continue

    offline = {b["id"]: MockOffline.translate(b["text"], target) for b in pending}
    warnings.append("所有在线翻译服务均不可用，已返回离线预览。")
    return finalize(offline, "offline")


def _cache_results(blocks: list[dict], translations: dict[int, str], provider: str, source: str, target: str) -> None:
    for block in blocks:
        value = translations.get(block["id"])
        if value:
            store.cache_set(_cache_key(provider, source, target, block["text"]), value)


def translate_text(text: str, source: str, target: str, provider: str = "auto",
                   settings: dict | None = None) -> dict:
    from .text import blocks_to_text, split_blocks
    blocks = split_blocks(text)
    result = translate_blocks(blocks, source, target, provider, settings)
    result["text"] = blocks_to_text(blocks, {str(k): v for k, v in result["translations"].items()})
    result["blocks"] = blocks
    return result


def provider_catalog(settings: dict | None = None) -> list[dict]:
    settings = settings or store.get_settings()
    ai_ready = AIClient(settings.get("ai", {})).configured
    return [
        {"id": "auto", "label": PROVIDER_LABELS["auto"], "available": True,
         "note": "有 AI Key 用 AI，否则用免费引擎"},
        {"id": "ai", "label": PROVIDER_LABELS["ai"], "available": ai_ready,
         "note": PROVIDER_NOTES["ai"] if ai_ready else "先在设置中填入 API Key"},
        {"id": "mymemory", "label": PROVIDER_LABELS["mymemory"], "available": True,
         "note": PROVIDER_NOTES["mymemory"]},
        {"id": "google", "label": PROVIDER_LABELS["google"], "available": True,
         "note": PROVIDER_NOTES["google"]},
        {"id": "offline", "label": PROVIDER_LABELS["offline"], "available": True,
         "note": PROVIDER_NOTES["offline"]},
    ]
