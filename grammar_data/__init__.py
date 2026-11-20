"""Grammar library registry and validation helpers."""
from __future__ import annotations

from .en import EN
from .ja import JA
from .other import OTHER
from .zh import ZH

ALL_ENTRIES = [*EN, *JA, *ZH, *OTHER]
GRAMMAR: dict[str, dict] = {}
for _entry in ALL_ENTRIES:
    if _entry["id"] in GRAMMAR:
        raise RuntimeError(f"Duplicate grammar id: {_entry['id']}")
    GRAMMAR[_entry["id"]] = _entry

LANGUAGE_NAMES = {
    "en": "英语", "ja": "日语", "zh": "中文", "ko": "韩语",
    "fr": "法语", "de": "德语", "es": "西班牙语", "ru": "俄语",
}

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
