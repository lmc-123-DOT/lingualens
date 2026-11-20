"""Shared language metadata for translation, detection and the grammar atlas.

The app deliberately separates *translation* languages from *grammar* languages:
Simplified and Traditional Chinese share one grammar library (``zh``), while the
translator still offers both writing systems.
"""
from __future__ import annotations

# Ordered roughly by global reach, then by learning/usage in the app.
LANGUAGE_ORDER = [
    "zh-CN", "zh-TW", "en", "ja", "ko", "es", "fr", "de", "pt", "it",
    "ru", "ar", "hi", "bn", "ur", "fa", "he", "tr", "id", "vi",
    "th", "nl", "pl", "uk", "sv",
]

GRAMMAR_LANGUAGE_ORDER = [
    "en", "zh", "ja", "ko", "es", "fr", "de", "pt", "it", "ru",
    "ar", "hi", "bn", "ur", "fa", "he", "tr", "id", "vi", "th",
    "nl", "pl", "uk", "sv",
]

GRAMMAR_LANGUAGE_NAMES = {
    "en": "英语", "zh": "中文", "ja": "日语", "ko": "韩语", "es": "西班牙语",
    "fr": "法语", "de": "德语", "pt": "葡萄牙语", "it": "意大利语", "ru": "俄语",
    "ar": "阿拉伯语", "hi": "印地语", "bn": "孟加拉语", "ur": "乌尔都语",
    "fa": "波斯语", "he": "希伯来语", "tr": "土耳其语", "id": "印尼语",
    "vi": "越南语", "th": "泰语", "nl": "荷兰语", "pl": "波兰语",
    "uk": "乌克兰语", "sv": "瑞典语",
}

LANGUAGES = {
    "zh-CN": {
        "name": "简体中文", "native": "简体中文", "short": "中",
        "grammar": "zh", "family": "汉藏语系 · 汉语族", "script": "汉字",
        "direction": "ltr", "rank": 1,
        "blurb": "孤立语：少形态变化，靠语序、虚词和语境表达语法关系；量词与话题结构发达。",
    },
    "zh-TW": {
        "name": "繁体中文", "native": "繁體中文", "short": "繁",
        "grammar": "zh", "family": "汉藏语系 · 汉语族", "script": "漢字",
        "direction": "ltr", "rank": 1,
        "blurb": "與簡體中文共享語法系統，使用繁體字形；語序與虛詞用法一致。",
    },
    "en": {
        "name": "英语", "native": "English", "short": "EN",
        "grammar": "en", "family": "印欧语系 · 日耳曼语族", "script": "拉丁字母",
        "direction": "ltr", "rank": 2,
        "blurb": "分析型语言：语序固定为 SVO，时态与体靠助动词，冠词和介词负担重。",
    },
    "ja": {
        "name": "日语", "native": "日本語", "short": "日",
        "grammar": "ja", "family": "日本语系（谱系有争议）", "script": "汉字 + 平假名 + 片假名",
        "direction": "ltr", "rank": 8,
        "blurb": "SOV 语序，助词标记格与话题；动词在后，敬语体系分层细致。",
    },
    "ko": {
        "name": "韩语", "native": "한국어", "short": "한",
        "grammar": "ko", "family": "朝鲜语系（谱系有争议）", "script": "谚文",
        "direction": "ltr", "rank": 15,
        "blurb": "SOV 语序，助词标记主题、主语和宾语；动词词尾承担时态、敬语与连接。",
    },
    "es": {
        "name": "西班牙语", "native": "Español", "short": "ES",
        "grammar": "es", "family": "印欧语系 · 罗曼语族", "script": "拉丁字母",
        "direction": "ltr", "rank": 3,
        "blurb": "屈折语：动词随人称变位，名词有性数，ser/estar 分工是核心难点。",
    },
    "fr": {
        "name": "法语", "native": "Français", "short": "FR",
        "grammar": "fr", "family": "印欧语系 · 罗曼语族", "script": "拉丁字母",
        "direction": "ltr", "rank": 11,
        "blurb": "动词变位丰富，冠词与代词系统繁复；书面语与口语语序差异明显。",
    },
    "de": {
        "name": "德语", "native": "Deutsch", "short": "DE",
        "grammar": "de", "family": "印欧语系 · 日耳曼语族", "script": "拉丁字母",
        "direction": "ltr", "rank": 12,
        "blurb": "四格系统、名词性别与框架结构；从句动词居末，复合词发达。",
    },
    "pt": {
        "name": "葡萄牙语", "native": "Português", "short": "PT",
        "grammar": "pt", "family": "印欧语系 · 罗曼语族", "script": "拉丁字母",
        "direction": "ltr", "rank": 6,
        "blurb": "动词变位与虚拟式发达，冠词、代词缩合多；欧洲与巴西变体有差异。",
    },
    "it": {
        "name": "意大利语", "native": "Italiano", "short": "IT",
        "grammar": "it", "family": "印欧语系 · 罗曼语族", "script": "拉丁字母",
        "direction": "ltr", "rank": 16,
        "blurb": "名词有性数，动词变位规则，复合时态与虚拟式使用频繁。",
    },
    "ru": {
        "name": "俄语", "native": "Русский", "short": "RU",
        "grammar": "ru", "family": "印欧语系 · 斯拉夫语族", "script": "西里尔字母",
        "direction": "ltr", "rank": 7,
        "blurb": "六格体系与动词体（完成/未完成）是骨架；语序灵活，信息结构靠词序。",
    },
    "ar": {
        "name": "阿拉伯语", "native": "العربية", "short": "AR",
        "grammar": "ar", "family": "亚非语系 · 闪米特语族", "script": "阿拉伯字母",
        "direction": "rtl", "rank": 5,
        "blurb": "三辅音词根派生系统；格与性数一致，动词变位随人称变化，书面语保留格尾。",
    },
    "hi": {
        "name": "印地语", "native": "हिन्दी", "short": "HI",
        "grammar": "hi", "family": "印欧语系 · 印度-雅利安语族", "script": "天城文",
        "direction": "ltr", "rank": 4,
        "blurb": "SOV 语序，后置词而非介词；名词有性数，动词随性与敬语层级变化。",
    },
    "bn": {
        "name": "孟加拉语", "native": "বাংলা", "short": "BN",
        "grammar": "bn", "family": "印欧语系 · 印度-雅利安语族", "script": "孟加拉文",
        "direction": "ltr", "rank": 5,
        "blurb": "SOV 语序，名词有格与敬语层级；动词人称词尾丰富，量词使用有特色。",
    },
    "ur": {
        "name": "乌尔都语", "native": "اردو", "short": "UR",
        "grammar": "ur", "family": "印欧语系 · 印度-雅利安语族", "script": "阿拉伯-乌尔都字母",
        "direction": "rtl", "rank": 9,
        "blurb": "SOV 语序，后置词与格标记；名词有性，敬语与波斯语借词层显著。",
    },
    "fa": {
        "name": "波斯语", "native": "فارسی", "short": "FA",
        "grammar": "fa", "family": "印欧语系 · 伊朗语族", "script": "阿拉伯-波斯字母",
        "direction": "rtl", "rank": 21,
        "blurb": "SOV 语序，名词靠 ezafe 连接修饰语；动词人称词尾与虚拟式重要。",
    },
    "he": {
        "name": "希伯来语", "native": "עברית", "short": "HE",
        "grammar": "he", "family": "亚非语系 · 闪米特语族", "script": "希伯来字母",
        "direction": "rtl", "rank": 24,
        "blurb": "三辅音词根与 binyan 动词模板；名词有性数，construct state 表领属。",
    },
    "tr": {
        "name": "土耳其语", "native": "Türkçe", "short": "TR",
        "grammar": "tr", "family": "突厥语系", "script": "拉丁字母",
        "direction": "ltr", "rank": 13,
        "blurb": "黏着语：后缀层层叠加，元音和谐贯穿全词；SOV 语序，格标记丰富。",
    },
    "id": {
        "name": "印尼语", "native": "Bahasa Indonesia", "short": "ID",
        "grammar": "id", "family": "南岛语系 · 马来-波利尼西亚语族", "script": "拉丁字母",
        "direction": "ltr", "rank": 14,
        "blurb": "分析型语言：无时态屈折，靠词缀（meN-、di-、ber-）与时间词表达语法。",
    },
    "vi": {
        "name": "越南语", "native": "Tiếng Việt", "short": "VI",
        "grammar": "vi", "family": "南亚语系 · 越语支", "script": "拉丁字母（国语字）",
        "direction": "ltr", "rank": 14,
        "blurb": "孤立语：靠语序与虚词，量词和语气词丰富；声调区别词义。",
    },
    "th": {
        "name": "泰语", "native": "ไทย", "short": "TH",
        "grammar": "th", "family": "壮侗语系 · 台语支", "script": "泰文",
        "direction": "ltr", "rank": 17,
        "blurb": "孤立语：SVO 语序，量词与语气词发达；时态靠时间词和助动词。",
    },
    "nl": {
        "name": "荷兰语", "native": "Nederlands", "short": "NL",
        "grammar": "nl", "family": "印欧语系 · 日耳曼语族", "script": "拉丁字母",
        "direction": "ltr", "rank": 22,
        "blurb": "V2 语序与从句动词居末；de/het 两类冠词，复合词与小品词丰富。",
    },
    "pl": {
        "name": "波兰语", "native": "Polski", "short": "PL",
        "grammar": "pl", "family": "印欧语系 · 斯拉夫语族", "script": "拉丁字母",
        "direction": "ltr", "rank": 19,
        "blurb": "七格体系与动词体；名词性数格一致，语序灵活但信息结构敏感。",
    },
    "uk": {
        "name": "乌克兰语", "native": "Українська", "short": "UK",
        "grammar": "uk", "family": "印欧语系 · 斯拉夫语族", "script": "西里尔字母",
        "direction": "ltr", "rank": 20,
        "blurb": "七格与动词体，呼格仍活跃；语序灵活，书面语保留丰富的形动词。",
    },
    "sv": {
        "name": "瑞典语", "native": "Svenska", "short": "SV",
        "grammar": "sv", "family": "印欧语系 · 日耳曼语族", "script": "拉丁字母",
        "direction": "ltr", "rank": 23,
        "blurb": "V2 语序，名词通性/中性两类；定指靠后缀，形容词需性数一致。",
    },
    "auto": {"name": "自动检测", "native": "Auto", "short": "A", "grammar": ""},
    "unknown": {"name": "未知语言", "native": "Unknown", "short": "?", "grammar": ""},
}


def language_catalog() -> list[dict]:
    """Return the ordered translation/grammar language catalog for the UI."""
    out = []
    for code in LANGUAGE_ORDER:
        meta = LANGUAGES[code]
        out.append({"code": code, **meta})
    return out


def grammar_catalog(counts: dict[str, int] | None = None) -> list[dict]:
    """Return the 24 grammar languages with display metadata and entry counts."""
    counts = counts or {}
    by_code = {}
    for code, meta in LANGUAGES.items():
        grammar_code = meta.get("grammar")
        if not grammar_code:
            continue
        # Simplified Chinese is the canonical display for the shared zh library.
        if grammar_code == "zh" and code != "zh-CN":
            continue
        by_code[grammar_code] = meta
    out = []
    for code in GRAMMAR_LANGUAGE_ORDER:
        meta = dict(by_code.get(code, {}))
        out.append({
            "code": code,
            "name": GRAMMAR_LANGUAGE_NAMES.get(code, code),
            "native": meta.get("native", code),
            "short": meta.get("short", code.upper()),
            "family": meta.get("family", ""),
            "script": meta.get("script", ""),
            "direction": meta.get("direction", "ltr"),
            "rank": meta.get("rank", 99),
            "blurb": meta.get("blurb", ""),
            "count": counts.get(code, 0),
        })
    return out
