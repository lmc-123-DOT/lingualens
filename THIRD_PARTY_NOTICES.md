# Third-Party Notices

LinguaLens' **source code** is MIT licensed (see `LICENSE`).

The optional learning-station data is **not bundled in the source repository**.
You can download it with `python fetch_lexicon_data.py`, but each dataset keeps
its own license. Building `lexicon/lexicon.db` does not relicense the underlying
content.

| Dataset | Used for | License | Requirements |
|---|---|---|---|
| [OpenJLPT](https://github.com/evanclan/OpenJLPT) | Japanese N5–N1 grammar | **CC BY-SA 4.0** | Attribute OpenJLPT; adapted database must be shared under CC BY-SA 4.0 |
| [firavoyage/_anki-jlpt-decks](https://github.com/firavoyage/_anki-jlpt-decks) | Japanese N5–N1 words + Chinese meanings | **CC BY-NC 4.0** | Attribute the author; **non-commercial use only** |
| [designfuchen/word-atlas](https://github.com/designfuchen/word-atlas) | English CEFR words + Chinese meanings | Code MIT; content governed by its `CONTENT_LICENSE.md` | Check the content license before redistributing |
| [jelleverheyen/hsk-vocabulary](https://github.com/jelleverheyen/hsk-vocabulary) | Chinese HSK words | No explicit license found at time of writing | **Do not redistribute the HSK data until the license is confirmed** |
| LinguaLens grammar library | English/Japanese/Chinese grammar explanations | MIT (original work) | Keep the copyright notice |

## Practical consequences

- **Non-commercial** use is the safe default while the JLPT Anki deck is included.
- If you want a commercial product, remove the CC BY-NC Japanese word list and
  the unclear HSK data, or replace them with datasets that allow commercial use.
- OpenJLPT-derived grammar data must remain CC BY-SA 4.0 and carry attribution.
- The app UI should keep a visible "数据来源" link when the learning station is
  distributed with data.
- This is a project notice, not legal advice. Verify each upstream license before
  publishing a public build.
