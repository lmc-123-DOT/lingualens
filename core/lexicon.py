"""Read-only access to the offline grammar / vocabulary station."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from . import paths

DB_PATH = paths.resource_path("lexicon", "lexicon.db")
LANGS = {"en": "英语", "ja": "日语", "zh": "中文"}
LEVEL_ORDER = {
    "en": ["A1", "A2", "B1", "B2", "C1", "C2"],
    "ja": ["N5", "N4", "N3", "N2", "N1", "N1-补充"],
    "zh": ["HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6", "HSK7"],
}


def available() -> bool:
    return DB_PATH.exists()


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def stats() -> dict:
    if not available():
        return {"ok": False, "error": "词库还没有安装", "languages": {}, "words": 0, "grammar": 0}
    con = _conn()
    words = {}
    grammar = {}
    for row in con.execute("SELECT lang, level, count(*) AS n FROM words GROUP BY lang, level"):
        words.setdefault(row["lang"], {})[row["level"]] = row["n"]
    for row in con.execute("SELECT lang, level, count(*) AS n FROM grammar GROUP BY lang, level"):
        grammar.setdefault(row["lang"], {})[row["level"]] = row["n"]
    total_words = sum(sum(v.values()) for v in words.values())
    total_grammar = sum(sum(v.values()) for v in grammar.values())
    con.close()
    languages = []
    for code, label in LANGS.items():
        levels = sorted(set(words.get(code, {})) | set(grammar.get(code, {})),
                        key=lambda x: LEVEL_ORDER.get(code, []).index(x) if x in LEVEL_ORDER.get(code, []) else 99)
        languages.append({
            "code": code, "label": label, "levels": levels,
            "words": sum(words.get(code, {}).values()),
            "grammar": sum(grammar.get(code, {}).values()),
            "wordsByLevel": words.get(code, {}),
            "grammarByLevel": grammar.get(code, {}),
        })
    return {"ok": True, "words": total_words, "grammar": total_grammar, "languages": languages}


def _level_order(lang: str) -> str:
    levels = LEVEL_ORDER.get(lang, [])
    if not levels:
        return "level"
    cases = " ".join(f"WHEN '{level}' THEN {index}" for index, level in enumerate(levels))
    return f"CASE level {cases} ELSE 99 END"


def words(lang: str, level: str = "", query: str = "", page: int = 1, size: int = 48) -> dict:
    if not available():
        return {"ok": False, "error": "词库还没有安装", "items": [], "total": 0}
    lang = lang if lang in LANGS else "ja"
    page = max(1, int(page or 1))
    size = max(1, min(100, int(size or 48)))
    where = ["lang = ?"]
    params: list = [lang]
    if level:
        where.append("level = ?")
        params.append(level)
    q = (query or "").strip()
    if q:
        where.append("(word LIKE ? OR reading LIKE ? OR meaning_zh LIKE ? OR meaning_en LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like, like])
    clause = " AND ".join(where)
    con = _conn()
    total = con.execute(f"SELECT count(*) FROM words WHERE {clause}", params).fetchone()[0]
    rows = con.execute(
        f"SELECT * FROM words WHERE {clause} ORDER BY {_level_order(lang)}, word LIMIT ? OFFSET ?",
        [*params, size, (page - 1) * size],
    ).fetchall()
    con.close()
    return {
        "ok": True, "lang": lang, "level": level, "query": q,
        "page": page, "size": size, "total": total,
        "pages": max(1, (total + size - 1) // size),
        "items": [dict(row) for row in rows],
    }


def grammar(lang: str, level: str = "", query: str = "", page: int = 1, size: int = 40) -> dict:
    if not available():
        return {"ok": False, "error": "词库还没有安装", "items": [], "total": 0}
    lang = lang if lang in LANGS else "ja"
    page = max(1, int(page or 1))
    size = max(1, min(100, int(size or 40)))
    where = ["lang = ?"]
    params: list = [lang]
    if level:
        where.append("level = ?")
        params.append(level)
    q = (query or "").strip()
    if q:
        where.append("(pattern LIKE ? OR meaning LIKE ? OR formation LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like])
    clause = " AND ".join(where)
    con = _conn()
    total = con.execute(f"SELECT count(*) FROM grammar WHERE {clause}", params).fetchone()[0]
    rows = con.execute(
        f"SELECT * FROM grammar WHERE {clause} ORDER BY {_level_order(lang)}, "
        "CASE source WHEN 'LinguaLens' THEN 0 ELSE 1 END, pattern LIMIT ? OFFSET ?",
        [*params, size, (page - 1) * size],
    ).fetchall()
    con.close()
    items = []
    for row in rows:
        item = dict(row)
        try:
            item["examples"] = json.loads(item.get("examples_json") or "[]")
        except Exception:
            item["examples"] = []
        item.pop("examples_json", None)
        items.append(item)
    return {
        "ok": True, "lang": lang, "level": level, "query": q,
        "page": page, "size": size, "total": total,
        "pages": max(1, (total + size - 1) // size),
        "items": items,
    }
