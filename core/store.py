"""SQLite persistence for history, settings, translation memory and batch jobs."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from . import paths

DATA_DIR = paths.data_dir()
DB_PATH = DATA_DIR / "lingualens.db"

DEFAULT_SETTINGS = {
    "provider": "auto",
    "ai": {
        "baseUrl": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "apiKey": "",
        "temperature": 0.2,
    },
    "aiGrammar": True,
    "autoGlossary": True,
    "translationStyle": "natural",
    "glossary": "",
    "batchOutput": "语镜译文",
    "theme": "paper",
}

_lock = threading.RLock()


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init() -> None:
    with _lock, _connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            title TEXT NOT NULL,
            source_lang TEXT,
            target_lang TEXT,
            provider TEXT,
            source_text TEXT,
            target_text TEXT,
            payload TEXT,
            grammar TEXT,
            starred INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_articles_created ON articles(created_at DESC);
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            status TEXT NOT NULL,
            payload TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ai_grammar (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_settings(include_secret: bool = False) -> dict:
    with _lock, _connect() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    stored = {}
    for row in rows:
        try:
            stored[row["key"]] = json.loads(row["value"])
        except Exception:
            stored[row["key"]] = row["value"]
    settings = deep_merge(DEFAULT_SETTINGS, stored)
    env_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
    if env_key and not settings["ai"].get("apiKey"):
        settings["ai"]["apiKey"] = env_key
        settings["ai"]["apiKeySource"] = "env"
    if not settings["ai"].get("apiKey"):
        settings["ai"]["apiKeySource"] = "none"
    elif "apiKeySource" not in settings["ai"]:
        settings["ai"]["apiKeySource"] = "local"
    if include_secret:
        return settings
    public = deep_merge({}, settings)
    key = settings["ai"].get("apiKey", "")
    public["ai"]["apiKey"] = ""
    public["ai"]["apiKeySet"] = bool(key)
    public["ai"]["apiKeyHint"] = (key[:4] + "…" + key[-4:]) if len(key) > 10 else ("已设置" if key else "")
    return public


def save_settings(patch: dict) -> dict:
    current = get_settings(include_secret=True)
    incoming = dict(patch or {})
    if isinstance(incoming.get("ai"), dict):
        incoming["ai"] = dict(incoming["ai"])
        if not incoming["ai"].get("apiKey"):
            incoming["ai"].pop("apiKey", None)
        if incoming["ai"].get("clearKey"):
            incoming["ai"]["apiKey"] = ""
            incoming["ai"].pop("clearKey", None)
    merged = deep_merge(current, incoming)
    # Never persist a key inherited from the environment.
    if current.get("ai", {}).get("apiKeySource") == "env" and not (
        isinstance(incoming.get("ai"), dict) and incoming["ai"].get("apiKey")
    ):
        merged["ai"]["apiKey"] = ""
    # Never persist the env sentinel as a real key.
    merged["ai"].pop("apiKeySet", None)
    merged["ai"].pop("apiKeyHint", None)
    merged["ai"].pop("apiKeySource", None)
    with _lock, _connect() as conn:
        for key in ("provider", "ai", "aiGrammar", "autoGlossary", "translationStyle", "glossary", "batchOutput", "theme"):
            conn.execute(
                "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(merged.get(key), ensure_ascii=False)),
            )
    return get_settings()


def cache_get(key: str, max_age: float = 60 * 60 * 24 * 30) -> str | None:
    with _lock, _connect() as conn:
        row = conn.execute("SELECT value, created_at FROM cache WHERE key=?", (key,)).fetchone()
    if not row:
        return None
    if time.time() - row["created_at"] > max_age:
        return None
    return row["value"]


def cache_set(key: str, value: str) -> None:
    if not value:
        return
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO cache(key,value,created_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, created_at=excluded.created_at",
            (key, value, time.time()),
        )


def cache_clear() -> None:
    with _lock, _connect() as conn:
        conn.execute("DELETE FROM cache")


def save_article(payload: dict) -> str:
    article_id = payload.get("id") or uuid.uuid4().hex[:12]
    payload["id"] = article_id
    grammar = payload.get("grammar") or {}
    grammar_points = grammar.get("points", []) if isinstance(grammar, dict) else grammar
    with _lock, _connect() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO articles
               (id,created_at,title,source_lang,target_lang,provider,source_text,target_text,payload,grammar)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                article_id, payload.get("createdAt") or _now(), payload.get("title", "未命名文章"),
                (payload.get("source") or {}).get("lang"), (payload.get("target") or {}).get("lang"),
                (payload.get("target") or {}).get("provider"), (payload.get("source") or {}).get("text", ""),
                (payload.get("target") or {}).get("text", ""),
                json.dumps(payload, ensure_ascii=False), json.dumps(grammar_points, ensure_ascii=False),
            ),
        )
        conn.execute(
            "DELETE FROM articles WHERE id NOT IN (SELECT id FROM articles ORDER BY created_at DESC LIMIT 200)"
        )
    return article_id


def get_article(article_id: str) -> dict | None:
    with _lock, _connect() as conn:
        row = conn.execute("SELECT payload FROM articles WHERE id=?", (article_id,)).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["payload"])
    except Exception:
        return None


def list_articles(limit: int = 30) -> list[dict]:
    with _lock, _connect() as conn:
        rows = conn.execute(
            """SELECT id,created_at,title,source_lang,target_lang,provider,source_text,target_text,grammar,starred
               FROM articles ORDER BY created_at DESC LIMIT ?""", (max(1, min(200, limit)),)
        ).fetchall()
    out = []
    for row in rows:
        try:
            grammar_count = len(json.loads(row["grammar"] or "[]"))
        except Exception:
            grammar_count = 0
        out.append({
            "id": row["id"], "createdAt": row["created_at"], "title": row["title"],
            "sourceLang": row["source_lang"], "targetLang": row["target_lang"],
            "provider": row["provider"], "grammarCount": grammar_count,
            "excerpt": _plain_excerpt(row["source_text"]),
            "translatedExcerpt": _plain_excerpt(row["target_text"]),
            "starred": bool(row["starred"]),
        })
    return out


def _plain_excerpt(text: str, limit: int = 150) -> str:
    text = (text or "").replace("\r", "")
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"^\s{0,3}(#{1,6}|>|[-*+]\s|\d+[.)]\s)\s*", "", line)
        line = re.sub(r"[`*_]{1,3}", "", line)
        line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
        if sum(len(x) for x in lines) >= limit:
            break
    return " ".join(lines)[:limit]


def delete_article(article_id: str) -> None:
    with _lock, _connect() as conn:
        conn.execute("DELETE FROM articles WHERE id=?", (article_id,))


def toggle_star(article_id: str) -> bool:
    with _lock, _connect() as conn:
        conn.execute("UPDATE articles SET starred=1-starred WHERE id=?", (article_id,))
        row = conn.execute("SELECT starred FROM articles WHERE id=?", (article_id,)).fetchone()
    return bool(row["starred"]) if row else False


def save_batch(job: dict) -> None:
    with _lock, _connect() as conn:
        conn.execute(
            """INSERT INTO batch_jobs(id,created_at,updated_at,status,payload) VALUES(?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at,status=excluded.status,payload=excluded.payload""",
            (job["id"], job.get("createdAt") or _now(), _now(), job.get("status", "queued"),
             json.dumps(job, ensure_ascii=False)),
        )


def get_batch(job_id: str) -> dict | None:
    with _lock, _connect() as conn:
        row = conn.execute("SELECT payload FROM batch_jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["payload"])
    except Exception:
        return None


def list_batches(limit: int = 20) -> list[dict]:
    with _lock, _connect() as conn:
        rows = conn.execute("SELECT payload FROM batch_jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    jobs = []
    for row in rows:
        try:
            job = json.loads(row["payload"])
        except Exception:
            continue
        jobs.append({
            "id": job.get("id"), "status": job.get("status"), "createdAt": job.get("createdAt"),
            "folder": job.get("folder"), "outputDir": job.get("outputDir"),
            "total": job.get("total", 0), "done": job.get("done", 0), "failed": job.get("failed", 0),
            "target": job.get("target"), "provider": job.get("provider"),
        })
    return jobs


def save_ai_grammar(entry: dict) -> None:
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ai_grammar(id,payload,created_at) VALUES(?,?,?)",
            (entry["id"], json.dumps(entry, ensure_ascii=False), _now()),
        )


def get_ai_grammar(grammar_id: str) -> dict | None:
    with _lock, _connect() as conn:
        row = conn.execute("SELECT payload FROM ai_grammar WHERE id=?", (grammar_id,)).fetchone()
    if not row:
        return None
    try:
        return json.loads(row["payload"])
    except Exception:
        return None
