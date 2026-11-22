"""Build the offline grammar + vocabulary station database.

Sources (kept outside the runtime; see lexicon/SOURCES.md):
- firavoyage/_anki-jlpt-decks NEW-JLPT/notes.csv (JLPT N5-N1, Chinese meanings)
- evanclan/OpenJLPT openjlpt.sqlite (JLPT grammar, N5-N1, English glosses)
- designfuchen/word-atlas word-atlas.json (English CEFR, Chinese meanings)
- jelleverheyen/hsk-vocabulary complete.json (HSK 2.0/3.0, English glosses)
- LinguaLens' own curated grammar library
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from grammar_data import GRAMMAR  # noqa: E402

LEX = ROOT / "lexicon"
DB = LEX / "lexicon.db"


def clean(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "；".join(str(v) for v in value if v)
    return re.sub(r"<[^>]+>", "", str(value)).strip()


def wid(prefix: str, *parts: str) -> str:
    raw = "\x1f".join(str(p) for p in parts).encode("utf-8")
    return prefix + hashlib.sha1(raw).hexdigest()[:12]


def build() -> None:
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript("""
      PRAGMA journal_mode=DELETE;
      CREATE TABLE words (
        id TEXT PRIMARY KEY, lang TEXT NOT NULL, level TEXT NOT NULL,
        word TEXT NOT NULL, reading TEXT DEFAULT '', romaji TEXT DEFAULT '',
        pos TEXT DEFAULT '', meaning_zh TEXT DEFAULT '', meaning_en TEXT DEFAULT '',
        example TEXT DEFAULT '', example_zh TEXT DEFAULT '', source TEXT DEFAULT ''
      );
      CREATE INDEX idx_words_lang_level ON words(lang, level);
      CREATE INDEX idx_words_word ON words(word);
      CREATE TABLE grammar (
        id TEXT PRIMARY KEY, lang TEXT NOT NULL, level TEXT NOT NULL,
        pattern TEXT NOT NULL, reading TEXT DEFAULT '', meaning TEXT DEFAULT '',
        formation TEXT DEFAULT '', examples_json TEXT DEFAULT '[]',
        tags TEXT DEFAULT '', source TEXT DEFAULT ''
      );
      CREATE INDEX idx_grammar_lang_level ON grammar(lang, level);
      CREATE INDEX idx_grammar_pattern ON grammar(pattern);
      CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
    """)
    words: list[tuple] = []
    grammar: list[tuple] = []

    # ---- Japanese vocabulary (Chinese meanings, readings, examples)
    ja_csv = LEX / "jlpt_notes.csv"
    if ja_csv.exists():
        seen = set()
        with ja_csv.open(encoding="utf-8", newline="") as fh:
            for row in csv.reader(fh):
                if not row or row[0].startswith("#") or len(row) < 9:
                    continue
                match = re.search(r"NEW-(N[1-5])", row[0])
                if not match:
                    continue
                level = match.group(1)
                word = clean(row[2])
                if not word:
                    continue
                key = (word, level)
                if key in seen:
                    continue
                seen.add(key)
                reading = clean(row[5])
                if re.search(r"[A-Za-z\u4e00-\u9fff]", reading):
                    reading = ""
                pos = clean(row[4])
                zh = clean(row[6])
                example = clean(row[11])
                example_zh = clean(row[13])
                words.append((
                    wid("ja-", word, level, pos), "ja", level, word, reading, "",
                    pos, zh, "", example, example_zh, "JLPT 词表（Anki 中文版）",
                ))
    print("Japanese words:", sum(1 for w in words if w[1] == "ja"))

    # ---- English CEFR
    en_json = LEX / "word-atlas.json"
    if en_json.exists():
        for item in json.loads(en_json.read_text(encoding="utf-8")):
            word = clean(item.get("w"))
            level = clean(item.get("cefr")) or "B1"
            if not word:
                continue
            senses = item.get("senses") or []
            zh = "；".join(clean(s.get("zh")) for s in senses if s.get("zh"))
            en = "；".join(clean(s.get("en")) for s in senses if s.get("en"))
            pos = "；".join(dict.fromkeys(clean(s.get("pos")) for s in senses if s.get("pos")))
            ex = item.get("ex") or []
            example = clean(ex[0].get("en")) if ex else ""
            example_zh = clean(ex[0].get("zh")) if ex else ""
            phonetic = clean(item.get("us") or item.get("uk"))
            words.append((wid("en-", word, level), "en", level, word, phonetic, "", pos, zh, en, example, example_zh, "word-atlas（CEFR）"))
    print("English words:", sum(1 for w in words if w[1] == "en"))

    # ---- Chinese HSK
    hsk_json = LEX / "hsk.json"
    if hsk_json.exists():
        for item in json.loads(hsk_json.read_text(encoding="utf-8")):
            word = clean(item.get("simplified"))
            if not word:
                continue
            levels = item.get("level") or []
            level = ""
            for raw in levels:
                m = re.match(r"new-(\d\+?|\d)", str(raw))
                if m:
                    level = "HSK" + m.group(1).replace("+", "")
                    break
            if not level:
                for raw in levels:
                    m = re.match(r"old-(\d)", str(raw))
                    if m:
                        level = "HSK" + m.group(1)
                        break
            level = level or "HSK3"
            forms = item.get("forms") or []
            form = forms[0] if forms else {}
            pinyin = clean(((form.get("transcriptions") or {}).get("pinyin")))
            meaning_en = "；".join(clean(x) for x in (form.get("meanings") or [])[:4])
            pos = "；".join(item.get("pos") or [])
            traditional = clean(form.get("traditional"))
            words.append((wid("zh-", word, level), "zh", level, word, pinyin, "", pos, "", meaning_en, "", traditional, "HSK 词表"))
    print("Chinese words:", sum(1 for w in words if w[1] == "zh"))

    con.executemany("INSERT OR IGNORE INTO words VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", words)

    # ---- Curated LinguaLens grammar (Chinese explanations)
    for entry in GRAMMAR.values():
        pattern = clean(entry.get("formula") or entry.get("title"))
        examples = [{"ja": clean(ex.get("source")), "zh": clean(ex.get("translation"))}
                    for ex in (entry.get("examples") or [])[:2]]
        grammar.append((
            "ll-" + entry["id"], entry["language"], clean(entry.get("cefr")) or "B1",
            clean(entry.get("title")), "", clean(entry.get("summary")), pattern,
            json.dumps(examples, ensure_ascii=False), clean(entry.get("category")),
            "LinguaLens",
        ))
    print("Curated grammar:", len(grammar))

    # ---- OpenJLPT grammar (526 Japanese points, English glosses)
    ojlpt = LEX / "openjlpt.sqlite"
    if ojlpt.exists():
        src = sqlite3.connect(ojlpt)
        src.row_factory = sqlite3.Row
        for row in src.execute("SELECT * FROM grammar"):
            level = clean(row["level"]) or "N3"
            grammar.append((
                "oj-" + clean(row["id"]), "ja", level, clean(row["pattern"]),
                clean(row["reading"]), clean(row["meaning"]), clean(row["formation"]),
                clean(row["examples"]), clean(row["tags"]), "OpenJLPT",
            ))
        src.close()
    print("Total grammar:", len(grammar))
    con.executemany("INSERT OR IGNORE INTO grammar VALUES (?,?,?,?,?,?,?,?,?,?)", grammar)

    con.execute("INSERT INTO meta VALUES ('built_at', datetime('now'))")
    con.commit()
    for row in con.execute("SELECT lang, level, count(*) FROM words GROUP BY lang, level ORDER BY lang, level"):
        print("WORD", row)
    for row in con.execute("SELECT lang, level, count(*) FROM grammar GROUP BY lang, level ORDER BY lang, level"):
        print("GRAMMAR", row)
    con.close()
    print("Wrote", DB, DB.stat().st_size, "bytes")


if __name__ == "__main__":
    build()
