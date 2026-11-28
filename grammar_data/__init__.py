"""Grammar library registry and validation helpers.

Core entries live in ``en.py`` / ``ja.py`` / ``zh.py`` / ``other.py``.  The
world-language atlas is data-only JSON under ``grammar_data/world/`` so new
languages can be added without touching Python code.  Every entry is validated
at import time: a broken file fails loudly instead of silently producing an
empty detail page.
"""
from __future__ import annotations

import json
from pathlib import Path

from core.languages import GRAMMAR_LANGUAGE_NAMES, GRAMMAR_LANGUAGE_ORDER

from .en import EN
from .english_plus import EN_PLUS
from .extra import EXTRA
from .ja import JA
from .other import OTHER
from .zh import ZH

WORLD_DIR = Path(__file__).resolve().parent / "world"
REQUIRED_FIELDS = (
    "id", "language", "title", "english", "category", "cefr",
    "formula", "summary", "sections", "examples",
)


def _load_world() -> list[dict]:
    entries: list[dict] = []
    if not WORLD_DIR.exists():
        return entries
    for path in sorted(WORLD_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - authoring guard
            raise RuntimeError(f"Cannot read grammar file {path.name}: {exc}") from exc
        raw_entries = payload.get("entries") if isinstance(payload, dict) else payload
        if not isinstance(raw_entries, list):
            raise RuntimeError(f"Grammar file {path.name} must contain a list of entries")
        for index, raw in enumerate(raw_entries):
            if not isinstance(raw, dict):
                raise RuntimeError(f"{path.name}[{index}] is not an object")
            missing = [key for key in REQUIRED_FIELDS if key not in raw]
            if missing:
                raise RuntimeError(f"{path.name}[{index}] missing fields: {', '.join(missing)}")
            lang = raw["language"]
            if lang not in GRAMMAR_LANGUAGE_ORDER:
                raise RuntimeError(f"{path.name}[{index}] unknown language: {lang}")
            entry = dict(raw)
            entry.setdefault("source", "curated")
            entry.setdefault("related", [])
            entry.setdefault("pitfalls", [])
            entry.setdefault("links", [])
            entry.setdefault("patterns", [])
            entry.setdefault("priority", 4)
            entry.setdefault("confidence", 0.76)
            entry["_file"] = path.name
            entries.append(entry)
    return entries


WORLD = _load_world()
ALL_ENTRIES = [*EN, *EN_PLUS, *JA, *ZH, *OTHER, *EXTRA, *WORLD]
GRAMMAR: dict[str, dict] = {}
for _entry in ALL_ENTRIES:
    if _entry["id"] in GRAMMAR:
        where = _entry.get("_file", "built-in")
        raise RuntimeError(f"Duplicate grammar id: {_entry['id']} ({where})")
    GRAMMAR[_entry["id"]] = _entry

LANGUAGE_NAMES = dict(GRAMMAR_LANGUAGE_NAMES)

for _entry in GRAMMAR.values():
    _entry["related"] = [rid for rid in _entry.get("related", []) if rid in GRAMMAR and rid != _entry["id"]]


def get(grammar_id: str) -> dict | None:
    return GRAMMAR.get(grammar_id)


def all_entries() -> list[dict]:
    return list(GRAMMAR.values())


def for_language(language: str) -> list[dict]:
    return [e for e in GRAMMAR.values() if e["language"] == language]


def search(query: str = "", language: str = "", category: str = "") -> list[dict]:
    q = (query or "").strip().lower()
    results = []
    for entry in GRAMMAR.values():
        if language and entry["language"] != language:
            continue
        if category and entry["category"] != category:
            continue
        if q:
            haystack = " ".join([
                entry.get("title", ""), entry.get("english", ""), entry.get("summary", ""),
                entry.get("formula", ""),
                " ".join(s.get("heading", "") + " " + s.get("body", "") for s in entry.get("sections", [])),
            ]).lower()
            if q not in haystack:
                continue
        results.append(entry)
    return results


def stats() -> dict:
    by_lang: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for entry in GRAMMAR.values():
        by_lang[entry["language"]] = by_lang.get(entry["language"], 0) + 1
        by_category[entry["category"]] = by_category.get(entry["category"], 0) + 1
    return {"total": len(GRAMMAR), "byLanguage": by_lang, "byCategory": by_category}


def detection_entries() -> list[dict]:
    """Entries that carry their own regex patterns for article analysis."""
    return [e for e in GRAMMAR.values() if e.get("patterns")]


def public_entry(entry: dict) -> dict:
    """Strip authoring-only fields before sending an entry to the browser."""
    hidden = {"patterns", "priority", "confidence", "_file", "sample"}
    return {key: value for key, value in entry.items() if key not in hidden}
