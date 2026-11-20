"""LinguaLens local server.

Run:  python server.py
Open: http://127.0.0.1:8765
"""
from __future__ import annotations

import argparse
import base64
import hmac
import json
import mimetypes
import os
import re
import socket
import sys
import threading
import time
import traceback
import urllib.parse
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import ai as ai_grammar  # noqa: E402
from core import batch, paths, store  # noqa: E402
from core.analyze import analyze_article  # noqa: E402
from core import lexicon  # noqa: E402
from core.docx_export import build_article_docx  # noqa: E402
from core.words import lookup_word  # noqa: E402
from core.documents import extract_bytes, fetch_url, read_document  # noqa: E402
from core.grammar import all_library, analyze, detail as grammar_detail, library_stats  # noqa: E402
from core.text import (LANGUAGES, blocks_to_text, count_stats, detect_language,  # noqa: E402
                       split_blocks, title_from_text)
from core.translate import (AIClient, PROVIDER_LABELS, TranslationError,  # noqa: E402
                            provider_catalog, translate_blocks)
from grammar_data import get as get_grammar, public_entry  # noqa: E402

APP_NAME = "语镜 LinguaLens"
VERSION = "2.0.0"
RESOURCE_ROOT = paths.resource_root()
WEB_DIR = paths.resource_path("web")
SINGLE_FILE = WEB_DIR / "single.html"
DATA_DIR = paths.data_dir()
MAX_TEXT = 160_000
MAX_UPLOAD = 48 * 1024 * 1024
QUIT_EVENT = None

try:  # Keep Chinese log lines readable in the Windows launcher console.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def log(*args):
    print(time.strftime("[%H:%M:%S]"), *args, flush=True)


def public_grammar(entry: dict) -> dict:
    return {k: entry.get(k) for k in (
        "id", "language", "title", "english", "category", "cefr", "formula", "summary",
        "sections", "examples", "pitfalls", "related", "links", "source",
    )}


def merge_grammar(rule_result: dict, ai_result: dict) -> dict:
    points = list(rule_result.get("points", []))
    seen = {p.get("title", "").strip().lower() for p in points}
    for p in ai_result.get("points", []):
        if p.get("title", "").strip().lower() in seen:
            continue
        points.append(p)
        seen.add(p.get("title", "").strip().lower())
    points = points[:30]
    categories, cefr = {}, {}
    for p in points:
        categories[p.get("category", "其他")] = categories.get(p.get("category", "其他"), 0) + 1
        cefr[p.get("cefr", "—")] = cefr.get(p.get("cefr", "—"), 0) + 1
    return {
        "language": rule_result.get("language"),
        "detected": rule_result.get("detected"),
        "points": points,
        "summary": {"total": len(points), "categories": categories, "cefr": cefr},
    }


def analyze_full(text: str, source: str, settings: dict) -> tuple[dict, list[str]]:
    warnings = []
    result = analyze(text, source)
    lang = result.get("language", "en")
    if settings.get("aiGrammar", True) and AIClient(settings.get("ai", {})).configured:
        enhanced = ai_grammar.enhance(text, lang, result.get("points", []), settings)
        if enhanced.get("warning"):
            warnings.append(enhanced["warning"])
        if enhanced.get("points"):
            result = merge_grammar(result, enhanced)
    return result, warnings


def render_article_markdown(payload: dict, base_url: str = "") -> str:
    source = payload.get("source", {})
    target = payload.get("target", {})
    grammar = payload.get("grammar", {})
    lines = [
        f"# {payload.get('title', '未命名文章')}", "",
        f"> {source.get('label', '')} → {target.get('label', '')} ｜ "
        f"{source.get('stats', {}).get('chars', 0)} 字 ｜ "
        f"{grammar.get('summary', {}).get('total', 0)} 个语法点", "",
        "## 译文", "", target.get("text", ""), "", "---", "", "## 原文", "", source.get("text", ""), "",
    ]
    if grammar.get("points"):
        lines.extend(["---", "", "## 语法索引", ""])
        for p in grammar["points"]:
            url = f"{base_url.rstrip('/')}/grammar/{p['id']}" if base_url else f"/grammar/{p['id']}"
            lines.append(f"- **[{p['title']} · {p['english']}]({url})**（{p['category']} · {p['cefr']} · {p['count']} 处）")
    return "\n".join(lines).strip() + "\n"


class Handler(BaseHTTPRequestHandler):
    server_version = f"LinguaLens/{VERSION}"
    protocol_version = "HTTP/1.1"

    # ----- helpers ---------------------------------------------------------
    def _json(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def _error(self, message: str, status: int = 400, exc: Exception | None = None):
        if exc:
            log("ERROR", message, repr(exc))
        self._json({"ok": False, "error": message}, status)

    def _authorized(self, path: str) -> bool:
        """Optional single-user Basic Auth for public deployments."""
        password = os.environ.get("LINGUALENS_PASSWORD", "")
        if not password or path == "/api/health":
            return True
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(header[6:]).decode("utf-8", "replace")
            _, _, supplied = decoded.partition(":")
        except Exception:
            return False
        return hmac.compare_digest(supplied, password)

    def _unauthorized(self):
        raw = json.dumps({"ok": False, "error": "需要密码访问"}, ensure_ascii=False).encode("utf-8")
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="LinguaLens", charset="UTF-8"')
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _body(self, max_bytes: int = MAX_UPLOAD + 8 * 1024 * 1024) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        if length > max_bytes:
            raise ValueError("请求内容过大")
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise ValueError("请求体不是合法 JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("请求体必须是 JSON 对象")
        return data

    def _base_url(self) -> str:
        host = self.headers.get("Host") or f"127.0.0.1:{self.server.server_port}"
        return f"http://{host}"

    def _send_file(self, path: Path, cache: bool = False):
        if not path.is_file():
            self._error("文件不存在", 404)
            return
        data = path.read_bytes()
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if path.suffix.lower() in (".js", ".css", ".html", ".json", ".svg", ".webmanifest"):
            mime += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=300" if cache else "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    # ----- routing ---------------------------------------------------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        query = urllib.parse.parse_qs(parsed.query)
        if not self._authorized(path):
            return self._unauthorized()
        try:
            if path == "/api/health":
                settings = store.get_settings()
                return self._json({
                    "ok": True, "app": APP_NAME, "version": VERSION,
                    "aiConfigured": AIClient(settings.get("ai", {})).configured,
                    "grammar": library_stats(),
                    "languages": {k: v for k, v in LANGUAGES.items() if k not in ("auto", "unknown")},
                    "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                })
            if path == "/api/providers":
                return self._json({"ok": True, "providers": provider_catalog(store.get_settings())})
            if path == "/api/settings":
                return self._json({"ok": True, "settings": store.get_settings()})
            if path == "/api/notebook":
                items = store.notebook_list()
                return self._json({"ok": True, "items": items, "total": len(items)})
            if path == "/api/word":
                word = (query.get("q") or [""])[0].strip()
                lang = (query.get("lang") or ["en"])[0]
                context = (query.get("context") or [""])[0]
                return self._json(lookup_word(word, lang, context))
            if path == "/api/analyze":
                article_id = (query.get("id") or [""])[0]
                if article_id:
                    article = store.get_article(article_id)
                else:
                    items = store.list_articles(1)
                    article = store.get_article(items[0]["id"]) if items else None
                if not article:
                    return self._error("还没有可拆解的文章", 404)
                analysis = analyze_article(article)
                analysis["title"] = article.get("title") or "未命名文章"
                analysis["articleId"] = article.get("id")
                return self._json({"ok": True, "analysis": analysis})
            if path == "/api/library/stats":
                return self._json(lexicon.stats())
            if path == "/api/library/words":
                return self._json(lexicon.words(
                    (query.get("lang") or ["ja"])[0],
                    (query.get("level") or [""])[0],
                    (query.get("q") or [""])[0],
                    int((query.get("page") or ["1"])[0]),
                    int((query.get("size") or ["48"])[0]),
                ))
            if path == "/api/library/grammar":
                return self._json(lexicon.grammar(
                    (query.get("lang") or ["ja"])[0],
                    (query.get("level") or [""])[0],
                    (query.get("q") or [""])[0],
                    int((query.get("page") or ["1"])[0]),
                    int((query.get("size") or ["40"])[0]),
                ))
            if path == "/api/grammar":
                q = (query.get("q") or [""])[0]
                lang = (query.get("lang") or [""])[0]
                category = (query.get("category") or [""])[0]
                items = [public_grammar(e) for e in all_library()]
                if lang:
                    items = [e for e in items if e["language"] == lang]
                if category:
                    items = [e for e in items if e["category"] == category]
                if q:
                    ql = q.lower()
                    items = [e for e in items if ql in json.dumps(e, ensure_ascii=False).lower()]
                return self._json({"ok": True, "items": items, "total": len(items),
                                   "stats": library_stats()})
            m = re.match(r"^/api/grammar/([\w-]+)$", path)
            if m:
                gid = m.group(1)
                entry = grammar_detail(gid) or ai_grammar.detail(gid)
                if not entry:
                    return self._error("语法点不存在", 404)
                return self._json({"ok": True, "grammar": public_entry(entry)})
            if path == "/api/history":
                limit = int((query.get("limit") or ["30"])[0])
                return self._json({"ok": True, "items": store.list_articles(limit)})
            m = re.match(r"^/api/history/([\w-]+)$", path)
            if m:
                article = store.get_article(m.group(1))
                if not article:
                    return self._error("记录不存在", 404)
                return self._json({"ok": True, "article": article})
            m = re.match(r"^/api/history/([\w-]+)/export$", path)
            if m:
                article = store.get_article(m.group(1))
                if not article:
                    return self._error("记录不存在", 404)
                fmt = (query.get("format") or ["md"])[0]
                if fmt == "json":
                    raw = json.dumps(article, ensure_ascii=False, indent=2).encode("utf-8")
                    name = "lingualens-article.json"
                    mime = "application/json"
                elif fmt in ("docx", "word"):
                    raw = build_article_docx(article)
                    name = "lingualens-article.docx"
                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                else:
                    raw = render_article_markdown(article, self._base_url()).encode("utf-8")
                    name = "lingualens-article.md"
                    mime = "application/octet-stream"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Disposition", f'attachment; filename="{name}"')
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            if path == "/api/batch":
                return self._json({"ok": True, "items": store.list_batches()})
            m = re.match(r"^/api/batch/([\w-]+)$", path)
            if m:
                job = batch.get(m.group(1))
                if not job:
                    return self._error("批译任务不存在", 404)
                return self._json({"ok": True, "job": job})
            m = re.match(r"^/api/batch/([\w-]+)/zip$", path)
            if m:
                data, filename = batch.make_zip(m.group(1))
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                ascii_name = f"lingualens-batch-{m.group(1)}.zip"
                self.send_header(
                    "Content-Disposition",
                    f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{urllib.parse.quote(filename)}",
                )
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            # SPA routes
            if path == "/" or path.startswith("/grammar") or path.startswith("/batch") \
                    or path.startswith("/history") or path.startswith("/settings") or path.startswith("/compare") \
                    or path.startswith("/analyze") or path.startswith("/library") or path == "/single":
                page = SINGLE_FILE if SINGLE_FILE.exists() else (WEB_DIR / "index.html")
                return self._send_file(page)
            # static assets
            if path.startswith("/assets/"):
                candidate = (WEB_DIR / path.lstrip("/")).resolve()
                if WEB_DIR.resolve() in candidate.parents:
                    return self._send_file(candidate, cache=False)
            if path == "/favicon.ico" or path == "/favicon.svg":
                candidate = WEB_DIR / "favicon.svg"
                if candidate.exists():
                    return self._send_file(candidate, cache=True)
            if path == "/sw.js":
                return self._send_file(WEB_DIR / "sw.js", cache=False)
            if path == "/manifest.webmanifest":
                return self._send_file(WEB_DIR / "manifest.webmanifest", cache=True)
            return self._error("页面不存在", 404)
        except Exception as exc:
            traceback.print_exc()
            self._error(f"服务器错误：{exc}", 500, exc)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        if not self._authorized(path):
            return self._unauthorized()
        try:
            body = self._body()
            if path == "/api/detect":
                text = str(body.get("text") or "")
                if not text.strip():
                    return self._error("请先输入文字")
                detected = detect_language(text)
                return self._json({"ok": True, "language": detected, "stats": count_stats(text)})
            if path == "/api/settings":
                saved = store.save_settings(body.get("settings") or body)
                return self._json({"ok": True, "settings": saved})
            if path == "/api/notebook":
                action = str(body.get("action") or "add")
                if action == "remove":
                    return self._json(store.notebook_remove(str(body.get("key") or "")))
                if action == "review":
                    return self._json(store.notebook_review(str(body.get("key") or ""), bool(body.get("known"))))
                return self._json(store.notebook_add(body))
            if path == "/api/ai/test":
                config = body.get("ai") or store.get_settings(include_secret=True).get("ai", {})
                if not (config or {}).get("apiKey"):
                    return self._error("请先填写 API Key")
                client = AIClient(config)
                try:
                    content = client.chat(
                        "You are a connection test. Reply with exactly: OK",
                        "Reply with exactly: OK",
                        json_mode=False, max_tokens=8,
                    )
                except Exception as exc:
                    return self._error(f"连接失败：{str(exc)[:240]}", 400)
                return self._json({"ok": True, "reply": content.strip()[:80]})
            if path in ("/api/translate", "/api/analyze"):
                return self._handle_translate(body, analyze_only=path.endswith("analyze"))
            if path == "/api/extract":
                filename = str(body.get("filename") or "upload.txt")
                raw_b64 = str(body.get("data") or "")
                if "," in raw_b64 and raw_b64.strip().startswith("data:"):
                    raw_b64 = raw_b64.split(",", 1)[1]
                try:
                    data = base64.b64decode(raw_b64, validate=False)
                except Exception:
                    return self._error("文件内容解码失败")
                doc = extract_bytes(filename, data)
                return self._json({"ok": True, **doc, "stats": count_stats(doc["text"])})
            if path == "/api/extract-url":
                url = str(body.get("url") or "").strip()
                if not url:
                    return self._error("请输入网页链接")
                doc = fetch_url(url)
                return self._json({"ok": True, **doc, "stats": count_stats(doc["text"])})
            if path == "/api/batch/scan":
                folder = str(body.get("folder") or "").strip().strip('"')
                if not folder:
                    return self._error("请选择或输入文件夹路径")
                result = batch.scan(folder, store.get_settings().get("batchOutput", "语镜译文"))
                return self._json({"ok": True, **result})
            if path == "/api/batch/start":
                folder = str(body.get("folder") or "").strip().strip('"')
                target = str(body.get("target") or "zh-CN")
                provider = str(body.get("provider") or "auto")
                if not Path(folder).expanduser().exists():
                    return self._error("文件夹不存在")
                job = batch.start(folder, target, provider, self._base_url(), store.get_settings(include_secret=True))
                return self._json({"ok": True, "job": job})
            m = re.match(r"^/api/batch/([\w-]+)/cancel$", path)
            if m:
                return self._json({"ok": batch.cancel(m.group(1))})
            m = re.match(r"^/api/history/([\w-]+)/star$", path)
            if m:
                starred = store.toggle_star(m.group(1))
                return self._json({"ok": True, "starred": starred})
            if path == "/api/folder-picker":
                folder = choose_folder()
                if not folder:
                    return self._json({"ok": False, "cancelled": True})
                return self._json({"ok": True, "folder": folder})
            if path == "/api/cache/clear":
                store.cache_clear()
                return self._json({"ok": True})
            if path == "/api/quit":
                if os.environ.get("LINGUALENS_DESKTOP") != "1" or QUIT_EVENT is None:
                    return self._error("当前不是桌面启动模式", 404)
                QUIT_EVENT.set()
                return self._json({"ok": True, "message": "语镜正在退出"})
            if path == "/api/reveal":
                target = body.get("path")
                if target and Path(target).exists():
                    os.startfile(str(Path(target)))  # type: ignore[attr-defined]
                    return self._json({"ok": True})
                return self._error("路径不存在", 404)
            if path == "/api/history" and body.get("action") == "clear":
                return self._error("暂不支持清空全部历史", 400)
            return self._error("接口不存在", 404)
        except (ValueError, TranslationError) as exc:
            self._error(str(exc), 400)
        except Exception as exc:
            traceback.print_exc()
            self._error(f"服务器错误：{exc}", 500, exc)

    def do_DELETE(self):
        path = urllib.parse.unquote(urllib.parse.urlparse(self.path).path)
        try:
            m = re.match(r"^/api/history/([\w-]+)$", path)
            if m:
                store.delete_article(m.group(1))
                return self._json({"ok": True})
            return self._error("接口不存在", 404)
        except Exception as exc:
            self._error("删除失败", 500, exc)

    # ----- translation -----------------------------------------------------
    def _handle_translate(self, body: dict, analyze_only: bool = False):
        text = str(body.get("text") or "").strip()
        if not text:
            return self._error("请先输入或导入一篇文章")
        if len(text) > MAX_TEXT:
            return self._error(f"文章过长（{len(text)} 字符），请控制在 {MAX_TEXT} 字符以内")
        source = str(body.get("source") or "auto")
        target = str(body.get("target") or "zh-CN")
        provider = str(body.get("provider") or store.get_settings().get("provider", "auto"))
        if target not in LANGUAGES or target in ("auto", "unknown"):
            return self._error("目标语言无效")
        settings = store.get_settings(include_secret=True)
        detected = detect_language(text)
        source_lang = detected["code"] if source in ("auto", "", None) else source
        if source_lang in ("unknown",):
            source_lang = "en"
        blocks = split_blocks(text)
        if not blocks:
            return self._error("没有可翻译的正文")
        started = time.time()

        def do_grammar():
            return analyze_full(text, source_lang, settings)

        if analyze_only:
            grammar, warnings = do_grammar()
            return self._json({
                "ok": True,
                "title": title_from_text(text, "语法分析"),
                "source": {"lang": source_lang, "label": LANGUAGES.get(source_lang, {}).get("name", source_lang),
                           "text": text, "stats": count_stats(text), "detected": detected},
                "grammar": grammar,
                "warnings": warnings,
                "elapsed": round(time.time() - started, 2),
            })

        with ThreadPoolExecutor(max_workers=2) as pool:
            grammar_future = pool.submit(do_grammar)
            translation_future = pool.submit(
                translate_blocks, blocks, source_lang, target, provider, settings
            )
            grammar, grammar_warnings = grammar_future.result()
            translation = translation_future.result()

        tr = {str(k): v for k, v in translation["translations"].items()}
        translated_text = blocks_to_text(blocks, tr)
        display_blocks = []
        for block in blocks:
            display_blocks.append({
                "id": block["id"], "type": block.get("type", "paragraph"),
                "level": block.get("level", 0), "prefix": block.get("prefix", ""),
                "source": block["text"], "target": tr.get(str(block["id"]), block["text"]),
                "translated": block.get("translate") is not False,
            })
        warnings = list(dict.fromkeys([*translation.get("warnings", []), *grammar_warnings]))
        payload = {
            "id": f"art-{int(time.time() * 1000)}-{os.urandom(3).hex()}",
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "title": title_from_text(text, "未命名文章"),
            "source": {
                "lang": source_lang, "label": LANGUAGES.get(source_lang, {}).get("name", source_lang),
                "native": LANGUAGES.get(source_lang, {}).get("native", source_lang),
                "text": text, "stats": count_stats(text), "detected": detected,
            },
            "target": {
                "lang": target, "label": LANGUAGES.get(target, {}).get("name", target),
                "native": LANGUAGES.get(target, {}).get("native", target),
                "text": translated_text, "provider": translation.get("provider"),
                "providerLabel": translation.get("providerLabel", translation.get("provider")),
                "cached": translation.get("cached", 0), "blocks": display_blocks,
            },
            "grammar": grammar,
            "warnings": warnings,
            "elapsed": round(time.time() - started, 2),
            "version": VERSION,
        }
        if body.get("save", True):
            store.save_article(payload)
        result = {"ok": True, "article": payload}
        if body.get("analyze"):
            result["analysis"] = analyze_article(payload)
        return self._json(result)

    def log_message(self, fmt, *args):
        if "/api/" in str(args[0] if args else ""):
            return
        log("%s - %s" % (self.address_string(), fmt % args))

    def handle(self):
        # Browser tabs often close while keep-alive is active; that is not an
        # application error and should not dump a traceback into the log.
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass


def choose_folder() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory(title="选择包含文章的文件夹")
        root.destroy()
        return folder or ""
    except Exception as exc:
        log("folder picker unavailable:", exc)
        return ""


def free_port(preferred: int) -> int:
    for port in range(preferred, preferred + 30):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return preferred


def main():
    parser = argparse.ArgumentParser(description="语镜 LinguaLens local translator")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT") or os.environ.get("LINGUALENS_PORT", "8765")))
    parser.add_argument("--host", default=os.environ.get("LINGUALENS_HOST", "127.0.0.1"))
    parser.add_argument("--open", action="store_true", help="open the browser after starting")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    require_auth = os.environ.get("LINGUALENS_REQUIRE_AUTH", "").lower() in ("1", "true", "yes", "on")
    if require_auth and not os.environ.get("LINGUALENS_PASSWORD"):
        log("ERROR: LINGUALENS_PASSWORD is required in public mode.")
        sys.exit(2)

    store.init()
    port = free_port(args.port)
    server = ThreadingHTTPServer((args.host, port), Handler)
    server.daemon_threads = True
    display_host = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host
    url = f"http://{display_host}:{port}"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "runtime.json").write_text(json.dumps({"url": url, "pid": os.getpid(), "host": args.host}, ensure_ascii=False), encoding="utf-8")
    log("=" * 58)
    log(f"  {APP_NAME}  v{VERSION}")
    log(f"  {url}")
    if args.host in ("0.0.0.0", "::"):
        log("  LAN/public mode: listening on all interfaces")
    log(f"  grammar library: {library_stats()['total']} entries")
    log("  Ctrl+C to stop")
    log("=" * 58)
    if args.open and not args.no_open:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("bye")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
