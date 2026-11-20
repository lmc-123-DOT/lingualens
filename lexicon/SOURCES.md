# 学习站台数据来源

本目录的 `lexicon.db` 由 `build_lexicon.py` 从公开数据整理。**原始数据不随源码仓库分发**；先运行 `python fetch_lexicon_data.py` 下载。

| 数据 | 用途 | 来源 | 许可证 |
|---|---|---|---|
| OpenJLPT | 日语 N5–N1 语法 526 条 | https://github.com/evanclan/OpenJLPT | CC BY-SA 4.0 |
| `_anki-jlpt-decks` / `NEW-JLPT/notes.csv` | 日语 N5–N1 词汇、读音、中文释义、例句 | https://github.com/firavoyage/_anki-jlpt-decks | CC BY-NC 4.0（**仅限非商业**） |
| word-atlas | 英语 CEFR A1–C2 词汇、中文释义、例句 | https://github.com/designfuchen/word-atlas | 代码 MIT；词条内容另见其 `CONTENT_LICENSE.md` |
| hsk-vocabulary | 中文 HSK 1–7 词汇、拼音、词性 | https://github.com/jelleverheyen/hsk-vocabulary | 未找到明确许可证；**确认前不要再分发** |
| 语镜自有语法库 | 英/日/中语法条目 231 条（中文讲解） | 本项目 `grammar_data/` | MIT |

## 分发注意

- 代码是 MIT；**词库不是**。
- 当前词库包含 CC BY-NC 的日语词表，因此默认只能**非商业**使用。
- 商业版本必须移除 CC BY-NC 词表和许可证不明的 HSK 数据，或替换为可商用的数据源。
- OpenJLPT 数据要求署名，改编后的数据库需按 CC BY-SA 4.0 共享。
- 公开发布时保留本文件和 `THIRD_PARTY_NOTICES.md`。
