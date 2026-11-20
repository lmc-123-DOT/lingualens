"""Lightweight word lookup for the reading page.

Sources, in order:
- Youdao's public dictionary JSON for English / Chinese / Japanese / French etc.
- dictionaryapi.dev for English fallback.
- MyMemory as a last-resort meaning translation.

No API key is required. Results are cached in memory; the UI also caches them.
"""
from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from functools import lru_cache

from .net import SSL_CONTEXT
from .morphology import explain_in_context

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
TAG = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")

POS_LABELS = {
    "n": "名词", "v": "动词", "vt": "及物动词", "vi": "不及物动词",
    "adj": "形容词", "adv": "副词", "prep": "介词", "conj": "连词",
    "pron": "代词", "num": "数词", "art": "冠词", "int": "感叹词",
    "aux": "助动词", "abbr": "缩写", "phr": "短语", "prefix": "前缀",
    "suffix": "后缀", "modal": "情态动词",
}

LANG_LE = {"en": "en", "zh": "zh", "ja": "ja", "fr": "fr", "de": "de", "es": "es", "ru": "ru", "ko": "ko"}
SPEECH_LANG = {"en": "en-US", "zh": "zh-CN", "ja": "ja-JP", "fr": "fr-FR", "de": "de-DE", "es": "es-ES", "ru": "ru-RU", "ko": "ko-KR"}


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=9, context=SSL_CONTEXT) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def _plain(value) -> str:
    if isinstance(value, str):
        return SPACE.sub(" ", html.unescape(TAG.sub("", value))).strip()
    if isinstance(value, list):
        return "".join(_plain(part) for part in value if part)
    if isinstance(value, dict):
        if "#text" in value:
            return _plain(value["#text"])
        return "".join(_plain(v) for k, v in value.items() if k not in ("@action", "@href"))
    return ""


def _pos_label(raw: str) -> str:
    key = (raw or "").strip().lower().rstrip(".")
    return POS_LABELS.get(key, raw.strip().rstrip(".") if raw else "释义")


def _split_senses(text: str, limit: int = 6) -> list[str]:
    text = _plain(text)
    text = re.sub(r"^[a-z]{1,8}\.\s*", "", text, flags=re.I)
    parts = re.split(r"[；;]\s*|\n+", text)
    result = []
    for part in parts:
        part = part.strip(" 。；;")
        if len(part) < 1:
            continue
        if len(part) > 90:
            part = part[:88].rstrip() + "…"
        if part not in result:
            result.append(part)
        if len(result) >= limit:
            break
    return result


def _english(word: str) -> dict | None:
    data = _get_json("https://dict.youdao.com/jsonapi?q=" + urllib.parse.quote(word))
    ec = (data.get("ec") or {}).get("word") or []
    if not ec:
        return None
    item = ec[0]
    phonetic = item.get("usphone") or item.get("ukphone") or ""
    meanings = []
    for group in item.get("trs") or []:
        for tr in group.get("tr") or []:
            node = tr.get("l") or {}
            raw = _plain(node.get("i"))
            if not raw:
                continue
            match = re.match(r"^([a-zA-Z]{1,8}\.)\s*(.+)$", raw)
            pos, text = (match.group(1), match.group(2)) if match else ("", raw)
            for sense in _split_senses(text):
                meanings.append({"pos": _pos_label(pos), "text": sense})
    if not meanings:
        return None
    return {
        "word": word,
        "lang": "en",
        "phonetic": phonetic,
        "pos": list(dict.fromkeys(m["pos"] for m in meanings))[:4],
        "meanings": meanings[:6],
        "source": "有道词典",
        "sourceUrl": "https://dict.youdao.com/result?word=" + urllib.parse.quote(word) + "&lang=en",
        "speechLang": SPEECH_LANG["en"],
    }


def _chinese(word: str) -> dict | None:
    data = _get_json("https://dict.youdao.com/jsonapi?q=" + urllib.parse.quote(word))
    ce = (data.get("ce") or {}).get("word") or []
    ai = ((data.get("aiDefinition") or {}).get("words") or [])
    phonetic = ""
    meanings = []
    if ce:
        item = ce[0]
        phonetic = item.get("phone") or ""
        for group in item.get("trs") or []:
            for tr in group.get("tr") or []:
                node = tr.get("l") or {}
                pos = node.get("pos") or ""
                english = _plain(node.get("#tran") or node.get("i"))
                for sense in _split_senses(english, limit=3):
                    meanings.append({"pos": _pos_label(pos), "text": sense})
    if ai:
        content = _plain(ai[0].get("content"))
        if content:
            # The AI dictionary paragraph is prose; keep the first two sentences.
            first = re.split(r"(?<=[。！？])", content)[:2]
            summary = "".join(first).strip()
            if summary:
                meanings.insert(0, {"pos": "中文释义", "text": summary[:180]})
    if not meanings:
        return None
    return {
        "word": word,
        "lang": "zh",
        "phonetic": phonetic,
        "pos": list(dict.fromkeys(m["pos"] for m in meanings if m["pos"] != "中文释义"))[:4] or ["词语"],
        "meanings": meanings[:5],
        "source": "有道词典",
        "sourceUrl": "https://dict.youdao.com/result?word=" + urllib.parse.quote(word) + "&lang=zh",
        "speechLang": SPEECH_LANG["zh"],
    }


def _suggest(word: str, lang: str) -> dict | None:
    le = LANG_LE.get(lang, lang)
    url = (
        "https://dict.youdao.com/suggest?num=5&ver=3.0&doctype=json&cache=false"
        f"&le={urllib.parse.quote(le)}&q={urllib.parse.quote(word)}"
    )
    data = _get_json(url)
    entries = ((data.get("data") or {}).get("entries") or [])
    if not entries:
        return None
    entry = entries[0]
    explain = _plain(entry.get("explain"))
    if not explain:
        return None
    pinyin = ""
    shown = _plain(entry.get("show"))
    if "|" in shown:
        pinyin = shown.split("|", 1)[1].strip()
    pos = []
    for tag in re.findall(r"【([^】]+)】", explain):
        for part in re.split(r"[・/、]", tag):
            part = part.strip()
            if part:
                pos.append(part)
    explain = re.sub(r"^【[^】]+】\s*", "", explain).strip()
    meanings = [{"pos": pos[0] if pos else ("日汉" if lang == "ja" else "释义"), "text": sense}
                for sense in _split_senses(explain, limit=5)]
    if not meanings:
        return None
    return {
        "word": word,
        "lang": lang,
        "phonetic": pinyin,
        "pos": pos[:4] or (["日汉"] if lang == "ja" else ["释义"]),
        "meanings": meanings,
        "source": "有道词典",
        "sourceUrl": f"https://dict.youdao.com/result?word={urllib.parse.quote(word)}&lang={le}",
        "speechLang": SPEECH_LANG.get(lang, "en-US"),
    }


def _english_fallback(word: str) -> dict | None:
    try:
        data = _get_json("https://api.dictionaryapi.dev/api/v2/entries/en/" + urllib.parse.quote(word))
    except Exception:
        return None
    if not isinstance(data, list) or not data:
        return None
    item = data[0]
    phonetic = item.get("phonetic") or ""
    meanings = []
    for group in item.get("meanings") or []:
        pos = group.get("partOfSpeech") or ""
        for definition in (group.get("definitions") or [])[:3]:
            text = definition.get("definition") or ""
            if text:
                meanings.append({"pos": _pos_label(pos), "text": text[:150]})
    if not meanings:
        return None
    return {
        "word": word, "lang": "en", "phonetic": phonetic,
        "pos": list(dict.fromkeys(m["pos"] for m in meanings))[:4],
        "meanings": meanings[:6], "source": "Free Dictionary",
        "sourceUrl": "https://api.dictionaryapi.dev/api/v2/entries/en/" + urllib.parse.quote(word),
        "speechLang": SPEECH_LANG["en"],
    }


def _machine(word: str, lang: str) -> dict | None:
    try:
        source = "en" if lang == "unknown" else lang
        url = (
            "https://api.mymemory.translated.net/get?q=" + urllib.parse.quote(word)
            + "&langpair=" + urllib.parse.quote(source) + "%7Czh-CN"
        )
        data = _get_json(url)
        text = ((data.get("responseData") or {}).get("translatedText") or "").strip()
        if not text or text.lower() == word.lower():
            return None
        return {
            "word": word, "lang": source, "phonetic": "", "pos": ["机器翻译"],
            "meanings": [{"pos": "释义", "text": text}], "source": "MyMemory",
            "sourceUrl": "https://mymemory.translated.net/", "speechLang": SPEECH_LANG.get(source, "en-US"),
        }
    except Exception:
        return None


@lru_cache(maxsize=1024)
def lookup_word(word: str, lang: str = "en", context: str = "") -> dict:
    word = (word or "").strip()
    if not word or len(word) > 64:
        return {"ok": False, "error": "请输入一个单词或短语"}
    lang = (lang or "en").lower()
    if lang in ("zh-cn", "zh-tw"):
        lang = "zh"
    if lang not in LANG_LE and lang != "zh":
        lang = "en" if re.search(r"[A-Za-z]", word) else "zh"
    original = word
    query = word.lower() if lang == "en" else word
    try:
        if lang == "en":
            result = _english(query) or _english_fallback(query)
        elif lang == "zh":
            result = _chinese(query)
        else:
            result = _suggest(query, lang) or _machine(query, lang)
        if not result:
            result = _machine(query, lang)
        if not result:
            return {"ok": False, "error": "暂未找到这个词的释义"}
        result["word"] = original
        result["ok"] = True
        result["morphology"] = explain_in_context(original, lang, context)
        result["context"] = (context or "")[:220]
        return result
    except Exception as exc:
        fallback = _machine(word, lang)
        if fallback:
            fallback["ok"] = True
            fallback["morphology"] = explain_in_context(original, lang, context)
            fallback["context"] = (context or "")[:220]
            return fallback
        return {"ok": False, "error": f"查询失败：{exc}"[:160]}
