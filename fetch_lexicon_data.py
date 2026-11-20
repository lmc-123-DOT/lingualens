"""Download the optional learning-station datasets.

The source repository intentionally does not ship third-party dictionaries.
Run this once, then `python build_lexicon.py` to build lexicon/lexicon.db.

Each dataset keeps its upstream license. See THIRD_PARTY_NOTICES.md.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

LEX = Path(__file__).resolve().parent / "lexicon"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LinguaLens/1.0"

FILES = {
    "openjlpt.sqlite": "https://raw.githubusercontent.com/evanclan/OpenJLPT/main/data/openjlpt.sqlite",
    "jlpt_notes.csv": "https://raw.githubusercontent.com/firavoyage/_anki-jlpt-decks/main/NEW-JLPT/notes.csv",
    "word-atlas.json": "https://raw.githubusercontent.com/designfuchen/word-atlas/main/data/word-atlas.json",
    "hsk.json": "https://raw.githubusercontent.com/jelleverheyen/hsk-vocabulary/main/complete.json",
}


def main() -> None:
    LEX.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        target = LEX / name
        if target.exists() and target.stat().st_size > 0:
            print(f"skip {name} ({target.stat().st_size} bytes)")
            continue
        print(f"download {name} ...")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=180) as response:
            target.write_bytes(response.read())
        print(f"  saved {target.stat().st_size} bytes")
    print("done. next: python build_lexicon.py")


if __name__ == "__main__":
    main()
