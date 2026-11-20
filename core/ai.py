"""Optional AI enhancement for grammar analysis.

Rule-based detection remains the source of truth. AI may add advanced points,
but every point must quote a sentence that actually exists in the article, and
its detail page is saved locally so links never rot.
"""
from __future__ import annotations

import hashlib
import re
import time

from . import store
from .translate import AIClient, TranslationError, _parse_json_response

LANG_NAMES = {"en": "英语", "ja": "日语", "zh": "中文", "ko": "韩语",
              "fr": "法语", "de": "德语", "es": "西班牙语", "ru": "俄语"}
ALLOWED_CATEGORIES = {"时态", "时态·体", "语态", "语气", "助词", "助动词", "接续", "条件", "句式", "句法",
                      "从句", "非谓语", "动词", "名词", "代词", "形容词", "副词", "介词", "限定词",
                      "数量词", "比较", "强调", "复句", "补语", "量词", "语序", "敬语", "授受", "格"}
LINKS = {
    "en": [("Cambridge Grammar", "https://dictionary.cambridge.org/grammar/british-grammar/", "Cambridge Dictionary"),
           ("British Council Grammar", "https://learnenglish.britishcouncil.org/grammar", "British Council")],
    "ja": [("Tae Kim's Guide", "https://guidetojapanese.org/learn/grammar", "Tae Kim's Guide"),
           ("日本語NET", "https://nihongokyoshi-net.com/", "日本語NET")],
    "zh": [("Chinese Grammar Wiki", "https://resources.allsetlearning.com/chinese/grammar/", "AllSet Learning"),
           ("汉典", "https://www.zdic.net/", "汉典")],
    "ko": [("How to Study Korean", "https://www.howtostudykorean.com/", "How to Study Korean"),
           ("TTMIK", "https://talktomeinkorean.com/", "Talk To Me In Korean")],
    "fr": [("Lawless French", "https://www.lawlessfrench.com/grammar/", "Lawless French")],
    "de": [("DW Learn German", "https://learngerman.dw.com/en/overview", "DW")],
    "es": [("SpanishDict Grammar", "https://www.spanishdict.com/grammar", "SpanishDict")],
    "ru": [("RussianLessons", "https://www.russianlessons.net/grammar/", "RussianLessons.net")],
}


def enhance(text: str, language: str, existing: list[dict], settings: dict) -> dict:
    if not settings.get("aiGrammar", True):
        return {"points": [], "warning": ""}
    client = AIClient(settings.get("ai", {}))
    if not client.configured:
        return {"points": [], "warning": ""}
    sample = (text or "")[:18000]
    if len(sample) < 20:
        return {"points": [], "warning": ""}
    lang_name = LANG_NAMES.get(language, language)
    existing_titles = "、".join(p.get("title", "") for p in existing[:18])
    system = (
        "You are a meticulous grammar teacher and corpus linguist. Analyze the supplied article in its "
        "original language. Identify 2-5 grammar points that are actually present and pedagogically useful "
        "to a Chinese-speaking learner. Do not invent sentences. Each point must quote one exact sentence "
        "from the article. Explain in clear Simplified Chinese. Return ONLY valid JSON."
    )
    user = (
        f"文章语言：{lang_name}（{language}）。\n"
        f"已有基础语法点（不要重复）：{existing_titles or '无'}。\n"
        "请补充文章中出现、但上面没有覆盖的进阶语法/句式。要求：\n"
        "1. 每个点必须有 context_sentence，且必须是文章原文中的完整句子（逐字复制）。\n"
        "2. 至少 2 个 sections，包含「结构」「语感/用法」；至少 1 组例句和 1 个易错点。\n"
        "3. 分类只能从：时态、语态、语气、助词、接续、条件、句式、句法、从句、非谓语、动词、名词、代词、形容词、副词、介词、限定词、比较、强调、复句、补语、量词、语序、敬语、授受、格 中选择。\n"
        "4. CEFR 使用 A1/A2/B1/B2/C1/C2（日语可用 N5-N1，中文可用 HSK1-HSK6）。\n"
        "5. 不要输出文章以外的例句作为 context_sentence。\n"
        '返回 JSON：{"points":[{"title":"中文名","english":"English name","category":"分类",'
        '"cefr":"B2","formula":"结构公式","summary":"一句话解释","context_sentence":"原文句子",'
        '"sections":[{"heading":"结构","body":"..."},{"heading":"语感/用法","body":"..."}],'
        '"examples":[{"source":"原文例句","translation":"中文释义"}],'
        '"pitfalls":[{"wrong":"错误句","right":"正确句","why":"原因"}]}]}\n\n'
        "文章：\n" + sample
    )
    try:
        content = client.chat(system, user, json_mode=True, max_tokens=3200)
        parsed = _parse_json_response(content)
    except (TranslationError, Exception) as exc:
        return {"points": [], "warning": f"AI 语法增强失败：{str(exc)[:160]}"}
    raw_points = parsed.get("points") if isinstance(parsed, dict) else None
    if not isinstance(raw_points, list):
        return {"points": [], "warning": "AI 语法增强返回格式异常"}

    normalized_text = re.sub(r"\s+", "", text)
    titles = {p.get("title", "").strip().lower() for p in existing}
    points = []
    for raw in raw_points:
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title") or "").strip()[:40]
        context = str(raw.get("context_sentence") or "").strip()
        if not title or len(context) < 4:
            continue
        if re.sub(r"\s+", "", context) not in normalized_text:
            continue
        if title.lower() in titles:
            continue
        category = str(raw.get("category") or "").strip()
        if category not in ALLOWED_CATEGORIES:
            category = "句式"
        sections = []
        for sec in (raw.get("sections") or [])[:5]:
            if isinstance(sec, dict) and str(sec.get("body") or "").strip():
                sections.append({
                    "heading": str(sec.get("heading") or "用法")[:24],
                    "body": str(sec.get("body") or "")[:1200],
                    **({"bullets": [str(x)[:160] for x in sec.get("bullets", [])][:5]} if sec.get("bullets") else {}),
                })
        if not sections:
            continue
        examples = []
        for ex in (raw.get("examples") or [])[:4]:
            if isinstance(ex, dict) and ex.get("source"):
                examples.append({"source": str(ex.get("source"))[:300],
                                 "translation": str(ex.get("translation") or "")[:300]})
        pitfalls = []
        for pit in (raw.get("pitfalls") or [])[:4]:
            if isinstance(pit, dict) and pit.get("wrong") and pit.get("right"):
                pitfalls.append({"wrong": str(pit["wrong"])[:240], "right": str(pit["right"])[:240],
                                 "why": str(pit.get("why") or "")[:300]})
        digest = hashlib.sha1(f"{language}|{title}|{context}".encode("utf-8")).hexdigest()[:10]
        gid = f"ai-{digest}"
        entry = {
            "id": gid, "language": language, "title": title,
            "english": str(raw.get("english") or "AI grammar note")[:60],
            "category": category, "cefr": str(raw.get("cefr") or "B1")[:6],
            "formula": str(raw.get("formula") or "")[:200],
            "summary": str(raw.get("summary") or "")[:400],
            "sections": sections, "examples": examples, "pitfalls": pitfalls,
            "related": [], "source": "ai",
            "links": [{"label": label, "url": url, "site": site}
                      for label, url, site in LINKS.get(language, LINKS["en"])],
        }
        store.save_ai_grammar(entry)
        points.append({
            "id": gid, "language": language, "title": title, "english": entry["english"],
            "category": category, "cefr": entry["cefr"], "formula": entry["formula"],
            "summary": entry["summary"], "count": 1, "confidence": 0.8,
            "occurrences": [{"blockId": 0, "sentence": context[:320], "match": context[:80]}],
            "source": "ai",
        })
        titles.add(title.lower())
        if len(points) >= 5:
            break
    return {"points": points, "warning": ""}


def detail(grammar_id: str) -> dict | None:
    return store.get_ai_grammar(grammar_id)
