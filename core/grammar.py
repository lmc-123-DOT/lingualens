"""Deterministic grammar detection over article sentences.

Detection is deliberately rule-based: it never invents a grammar point, gives
the exact sentence where it occurs, and can run without an API key. AI can add
depth later, but the spine stays inspectable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from grammar_data import GRAMMAR, detection_entries, get as get_grammar
from .languages import GRAMMAR_LANGUAGE_NAMES, GRAMMAR_LANGUAGE_ORDER, grammar_catalog
from .text import detect_language, split_blocks, split_sentences


@dataclass
class Rule:
    gid: str
    patterns: list[str]
    confidence: float = 0.82
    priority: int = 5
    flags: int = re.I
    allow: str | None = None
    deny: str | None = None
    compiled: list[re.Pattern] = field(default_factory=list)

    def __post_init__(self):
        self.compiled = [re.compile(p, self.flags) for p in self.patterns]


PP = (
    "been|done|gone|seen|made|taken|given|known|shown|written|spoken|eaten|drunk|"
    "begun|broken|chosen|driven|fallen|felt|found|got|gotten|heard|held|kept|left|lost|"
    "met|paid|put|read|run|said|sold|sent|set|shown|sat|slept|spent|stood|taught|told|"
    "thought|understood|won|worn|built|caught|come|become|brought|bought|fought|sought|"
    "grown|thrown|flown|drawn|worn|torn|born|born|risen|arisen|forgotten|hidden|hit|cut|"
    "let|shut|spread|cost|hurt|quit|burst|cast|deal|meant|learnt|learned|worked|changed|"
    "created|developed|increased|reduced|used|produced|published|reported|announced"
)
PRESENT_PART = r"[A-Za-z]+ing"

EN_RULES = [
    Rule("en-present-perfect", [rf"\b(?:have|has)\s+(?:not\s+)?(?:\w+\s+){{0,2}}(?:{PP})\b"], 0.9, 10),
    Rule("en-past-perfect", [rf"\bhad\s+(?:not\s+)?(?:\w+\s+){{0,1}}(?:{PP})\b"], 0.9, 9),
    Rule("en-passive-voice", [rf"\b(?:am|is|are|was|were|be|been|being|get|got|gets)\s+(?:not\s+)?(?:\w+\s+){{0,1}}(?:{PP})\b"], 0.85, 9),
    Rule("en-present-continuous", [rf"\b(?:am|is|are)\s+(?:not\s+)?(?:\w+\s+){{0,1}}{PRESENT_PART}\b"], 0.86, 8),
    Rule("en-past-continuous", [rf"\b(?:was|were)\s+(?:not\s+)?(?:\w+\s+){{0,1}}{PRESENT_PART}\b"], 0.88, 8),
    Rule("en-future-forms", [r"\b(?:will|shall)\s+(?:not\s+)?\w+", r"\b(?:am|is|are|was|were)\s+going\s+to\s+\w+"], 0.8, 7),
    Rule("en-conditional", [r"\bif\b[^.!?]{0,90}\b(?:will|would|were|had|should|could)\b", r"\b(?:unless|provided that|as long as)\b"], 0.83, 9),
    Rule("en-modal-verbs", [r"\b(?:can|could|may|might|must|should|shall|will|would|ought to|had better)\b"], 0.72, 4),
    Rule("en-gerund", [r"\b(?:enjoy|avoid|mind|finish|suggest|recommend|consider|imagine|practi[cs]e|keep|risk|delay|deny|look forward to|be used to|instead of)\s+\w+ing\b"], 0.9, 8),
    Rule("en-infinitive", [r"\b(?:want|need|decide|hope|plan|promise|refuse|manage|afford|choose|expect|learn|try|agree|offer|fail)\s+to\s+\w+"], 0.85, 6),
    Rule("en-relative-clause", [r"\b(?:who|whom|whose|which)\b", r"\b(?:the|a|an)\s+\w+(?:\s+\w+)?\s+that\s+\w+"], 0.75, 7),
    Rule("en-article", [r"\b(?:a|an|the)\b"], 0.55, 1),
    Rule("en-comparative", [r"\b\w{3,}er\s+than\b", r"\bmore\s+\w+\s+than\b", r"\bthe\s+(?:\w{3,}est|most\s+\w+)\b", r"\bas\s+\w+\s+as\b"], 0.84, 5),
    Rule("en-phrasal-verb", [r"\b(?:give up|figure out|turn on|turn off|look after|look forward to|come across|carry out|bring about|set up|point out|find out|go through|take off|put off|break down|work out|run into|get over|deal with|come up with|put up with)\b"], 0.88, 7),
    Rule("en-reported-speech", [r"\b(?:said|told|asked|explained|mentioned|reported|claimed)\s+(?:that\b|me\b|him\b|her\b|us\b|them\b|the\s+\w+)"], 0.8, 7),
    Rule("en-subjunctive", [r"\b(?:suggest|recommend|demand|insist|require|propose|request)\s+that\s+\w+\s+\w+", r"\bif\s+I\s+were\b", r"\bit\s+is\s+(?:important|necessary|essential|vital)\s+that\b"], 0.88, 9),
    Rule("en-inversion", [r"\b(?:never|rarely|seldom|hardly|not only|not until|no sooner)\b[^.!?]{0,55}\b(?:have|has|had|do|does|did|is|are|was|were|can|could|will|would)\b"], 0.86, 9),
    Rule("en-causative", [r"\b(?:have|has|had|get|got|gets)\s+(?:\w+\s+){0,2}(?:done|made|repaired|cut|built|cleaned|painted|translated|checked|fixed)\b", r"\b(?:make|made|let|help|helps|helped)\s+\w+\s+\w+"], 0.83, 8),
    Rule("en-participle-clause", [r"^\s*(?:[A-Z][a-z]+ing|[A-Z][a-z]+ed|Having\s+\w+)\b[^.!?]{0,60},", r"\b(?:having|being)\s+\w+ed\b"], 0.8, 8),
    Rule("en-preposition", [r"\b(?:interested in|depend on|consist of|good at|afraid of|look forward to|in order to|because of|instead of|according to|on behalf of|in spite of)\b"], 0.86, 5),
    Rule("en-quantifier", [r"\b(?:some|any|many|much|few|little|a lot of|several|both|either|neither|each|every|all|none)\b"], 0.6, 2),
    Rule("en-countable", [r"\b(?:information|advice|furniture|equipment|news|research|luggage|baggage|progress|knowledge)\b", r"\b(?:piece|pieces|item|items)\s+of\b"], 0.85, 6),
    Rule("en-questions", [r"^[^.!?]{0,90}\?$", r"^(?:what|who|where|when|why|how|which|whose|whom|do|does|did|is|are|was|were|can|could|will|would|should|may|might|have|has|had)\b[^.!?]*\?"], 0.86, 6),
    Rule("en-negation", [r"\b(?:not|never|no|nobody|nothing|nowhere|neither|nor)\b", r"\b(?:don't|doesn't|didn't|isn't|aren't|wasn't|weren't|can't|couldn't|won't|wouldn't|shouldn't|haven't|hasn't|hadn't)\b"], 0.66, 3),
    Rule("en-adverb", [r"\b(?:always|usually|often|sometimes|rarely|seldom|never|quickly|slowly|carefully|quietly|suddenly|however|therefore|interestingly|fortunately|unfortunately)\b"], 0.68, 3),
    Rule("en-conjunction", [r"\b(?:although|though|because|unless|whereas|while|since|even though|so that|in order that)\b"], 0.78, 5),
    Rule("en-pronoun", [r"\b(?:I|you|he|she|it|we|they|me|him|her|us|them|my|your|his|its|our|their|myself|yourself|himself|herself|itself|ourselves|themselves)\b"], 0.5, 1),
    Rule("en-appositive", [r",\s*(?:a|an|the)\s+[^,.]{3,40},", r"\bthe\s+\w+\s*,\s*(?:a|an|the)\s+\w+"], 0.75, 5),
    Rule("en-purpose", [r"\b(?:in order to|so as to|so that|in order that)\b"], 0.86, 6),
]

JA_RULES = [
    Rule("ja-teiru", [r"て(?:いる|います|いた|いました|いない|いません)", r"で(?:いる|います|いた)"], 0.9, 10),
    Rule("ja-teoku", [r"て(?:おく|おきます|おいた|おいて|おこう|おかない)", r"(?:とく|ときます|といた|といて)"], 0.88, 9),
    Rule("ja-teshimau", [r"て(?:しまう|しまった|しまいます|しまい|しまおう)", r"(?:ちゃう|ちゃった|じゃう|じゃった)"], 0.88, 9),
    Rule("ja-temiru", [r"て(?:みる|みた|みます|みて|みよう|みたい)"], 0.88, 8),
    Rule("ja-tearu", [r"て(?:ある|あります|あった|あって|あらない)"], 0.88, 8),
    Rule("ja-tekuru-iku", [r"て(?:くる|きた|きます|こない|いった|いく|いきます|いこう)"], 0.82, 7),
    Rule("ja-passive", [r"(?:される|られる|された|られた|されています|されています|せられる|させられる)"], 0.85, 9),
    Rule("ja-causative", [r"(?:させる|せる|させた|せた|させます|せます)"], 0.85, 9),
    Rule("ja-potential", [r"(?:ことができる|ことができます|られる|れる|ける|める|てる|せる)"], 0.62, 4),
    Rule("ja-keigo", [r"(?:いらっしゃ|おっしゃ|召し上が|ご覧|なさい|ください|いただ|申し上げ|伺|拝見|存じ|ござい|でござい)"], 0.86, 8),
    Rule("ja-teiru", [r"ています", r"でいます"], 0.9, 9),
    Rule("ja-tai", [r"(?:たい|たく|たかった|たくなかった)(?:です|と思う|と思っています)?"], 0.75, 6),
    Rule("ja-nagara", [r"ながら"], 0.9, 8),
    Rule("ja-tari", [r"たり[^。]{0,40}たり", r"だり[^。]{0,40}だり"], 0.9, 8),
    Rule("ja-node", [r"ので(?:、|,|\s|$)", r"なので"], 0.86, 7),
    Rule("ja-noni", [r"のに(?:、|,|\s|$)"], 0.88, 8),
    Rule("ja-kara", [r"から(?:、|,|\s|$)"], 0.72, 5),
    Rule("ja-ba", [r"(?:れば|けば|せば|たば|なれば|すれば|行けば|見れば)"], 0.86, 8),
    Rule("ja-tara", [r"(?:たら|だったら)"], 0.86, 8),
    Rule("ja-nara", [r"なら(?:、|,|\s|$)", r"のなら"], 0.84, 7),
    Rule("ja-to-conditional", [r"と(?:、|,)?[^。]{0,28}(?:なる|咲く|開く|出る|降る|始まる|終わる|見える)"], 0.72, 6),
    Rule("ja-quotation", [r"(?:と言う|と言った|と思います|と思った|と聞いた|と書いて|って言|って思)"], 0.86, 7),
    Rule("ja-giving", [r"(?:てあげる|てくれる|てもらう|あげる|くれる|もらう)"], 0.8, 6),
    Rule("ja-comparison", [r"(?:より|ほど|くらい|ぐらい)"], 0.76, 5),
    Rule("ja-volitional", [r"(?:しよう|しましょう|しようと思|ようとする|ようと思)"], 0.84, 7),
    Rule("ja-koto", [r"こと(?:が|を|は|に|で|だ|です)", r"ことができる", r"ことがある"], 0.8, 5),
    Rule("ja-wa", [r"(?<=[\u4e00-\u9fff\u3040-\u30ff])は(?=[\u4e00-\u9fff\u3040-\u30ff、。！？\s])"], 0.72, 3,
         deny=r"こんにちは"),
    Rule("ja-ga", [r"(?<=[\u4e00-\u9fff\u3040-\u30ff])が(?=[\u4e00-\u9fff\u3040-\u30ff、。！？\s])"], 0.72, 3),
    Rule("ja-wo", [r"(?<=[\u4e00-\u9fff\u3040-\u30ff])を(?=[\u4e00-\u9fff\u3040-\u30ff、。！？\s])"], 0.72, 3),
    Rule("ja-ni", [r"(?<=[\u4e00-\u9fff\u3040-\u30ff])に(?=[\u4e00-\u9fff\u3040-\u30ff、。！？\s])"], 0.68, 2),
    Rule("ja-de", [r"(?<=[\u4e00-\u9fff\u3040-\u30ff])で(?=[\u4e00-\u9fff\u3040-\u30ff、。！？\s])"], 0.68, 2),
    Rule("ja-to", [r"(?<=[\u4e00-\u9fff\u3040-\u30ff])と(?=[\u4e00-\u9fff\u3040-\u30ff、。！？\s])"], 0.66, 2),
    Rule("ja-no", [r"(?<=[\u4e00-\u9fff\u3040-\u30ff])の(?=[\u4e00-\u9fff\u3040-\u30ff、。！？\s])"], 0.66, 2),
]

ZH_RULES = [
    Rule("zh-shi-de", [r"是[^。！？]{0,36}的(?:[。！？]|$)"], 0.8, 8),
    Rule("zh-ba", [r"把[^。！？]{0,40}"], 0.92, 10),
    Rule("zh-bei", [r"被[^。！？]{0,35}"], 0.92, 10),
    Rule("zh-lian-dou", [r"连[^。！？]{0,20}(?:都|也)"], 0.92, 9),
    Rule("zh-yi-jiu", [r"一[^。！？]{0,20}就", r"一[^。！？]{0,12}(?:便|即)"], 0.9, 9),
    Rule("zh-yuelaiyue", [r"越来越[^。！？]{0,20}"], 0.93, 9),
    Rule("zh-yue-yue", [r"越[^。！？]{0,18}越[^。！？]{0,18}"], 0.92, 9),
    Rule("zh-suiran-danshi", [r"虽然[^。！？]{0,50}(?:但是|可是|却|不过|仍然|还是)"], 0.94, 9),
    Rule("zh-yinwei-suoyi", [r"因为[^。！？]{0,50}(?:所以|因此|因而|故而)", r"由于[^。！？]{0,50}(?:所以|因此|因而)"], 0.93, 9),
    Rule("zh-ruguo-jiu", [r"(?:如果|要是|假如|倘若)[^。！？]{0,50}(?:就|便|那么)"], 0.93, 9),
    Rule("zh-budan-erqie", [r"(?:不但|不仅|不只)[^。！？]{0,50}(?:而且|还|也|甚至)"], 0.93, 9),
    Rule("zh-zhiyou-cai", [r"只有[^。！？]{0,45}(?:才|方能)"], 0.93, 9),
    Rule("zh-wulun-dou", [r"(?:无论|不管|不论)[^。！？]{0,50}(?:都|也|总)"], 0.93, 9),
    Rule("zh-qushi-buyu", [r"[\u4e00-\u9fff](?:起来|下去|出来|过来|过去|上来|下来|进来|进去|回来|回去|开来|起)"], 0.7, 6),
    Rule("zh-jieguo-buyu", [r"(?:做|写|吃|看|听|走|跑|说|洗|打扫|学|读|买|卖|用|开|关|放|拿|找|想|记|修|改|弄|喝|睡|站|坐|长|变|见|遇|打|擦|收|考|讲|谈|忙)(?:完|好|到|见|懂|错|光|干净|清楚|成|住|掉)(?:了|过|的|得)?"], 0.72, 5),
    Rule("zh-keneng-buyu", [r"[\u4e00-\u9fff](?:得|不)(?:了|起|下|动|住|完|懂|见|开|上|着)"], 0.72, 6),
    Rule("zh-cunxian", [r"^(?:桌上|墙上|门口|远处|窗前|房间里|教室里|街上|天上|空中|树上|床上|地上|水里|书上|画上|心中|心里|窗外|台上|门前|屋外|山脚下|路边)[^。！？]{0,22}(?:有|是|出现|站着|坐着|放着|挂着|躺着|来了|走了)"], 0.78, 5),
    Rule("zh-jianyu", [r"(?:让|叫|请|使|派|命令|要求|允许)[^。！？]{0,16}(?:去|来|做|交|参加|帮|写|说|看|完成|处理)"], 0.85, 8),
    Rule("zh-shuangbin", [r"(?:给|送|教|告诉|借|问|还|赔)[^。！？]{0,10}(?:我|你|他|她|我们|他们|老师|朋友|大家)[^。！？]{0,12}"], 0.78, 6),
    Rule("zh-liangci-overlap", [r"(个|本|条|张|件|只|位|次|回|遍|家|辆|座|间|双|对)\1"], 0.86, 6),
    Rule("zh-yiwen-rendai", [r"(?:谁|什么|怎么|哪里|哪儿|哪个|多少)[^。！？]{0,18}(?:都|也)"], 0.9, 8),
    Rule("zh-gei", [r"(?:给|送给|寄给|发给|交给)[^。！？]{0,20}"], 0.65, 4),
    Rule("zh-bi", [r"比[^。！？]{0,18}(?:更|还|得多|一些|一点儿|大|小|高|低|快|慢|多|少|好|差|强|弱)"], 0.85, 6),
    Rule("zh-meiyou", [r"(?:没有|没)[^。！？]{0,18}(?:那么|这么|那样|这样)[^。！？]{0,8}"], 0.82, 6),
    Rule("zh-le", [r"了"], 0.6, 2),
    Rule("zh-zhe", [r"着"], 0.62, 2),
    Rule("zh-guo", [r"过"], 0.58, 2),
    Rule("zh-de", [r"[的地得]"], 0.5, 1),
    Rule("zh-dou", [r"都"], 0.55, 2),
    Rule("zh-jiu", [r"就"], 0.55, 2),
    Rule("zh-cai", [r"才"], 0.6, 2),
    Rule("zh-you", [r"有"], 0.4, 1),
    Rule("zh-shi", [r"是"], 0.4, 1),
]

KO_RULES = [
    Rule("ko-topic", [r"(?<=[\uac00-\ud7a3])(?:은|는)(?=\s)"], 0.8, 6),
    Rule("ko-object", [r"(?<=[\uac00-\ud7a3])(?:을|를)(?=\s)"], 0.8, 6),
    Rule("ko-connective", [r"(?:고|아서|어서)(?=\s)"], 0.7, 5),
]
FR_RULES = [
    Rule("fr-passe-compose", [r"\b(?:ai|as|a|avons|avez|ont|suis|es|est|sommes|êtes|sont)\s+(?:pas\s+)?\w+(?:é|i|u|s|t)\b"], 0.78, 7),
    Rule("fr-articles", [r"\b(?:le|la|les|un|une|des|du|de la)\b"], 0.55, 2),
]
DE_RULES = [
    Rule("de-cases", [r"\b(?:der|die|das|den|dem|des|einen|einem|einer)\b"], 0.55, 3),
    Rule("de-word-order", [r"\b(?:weil|dass|wenn|obwohl|da)\b[^.!?]{0,80}\b\w+(?:e|st|t|en)\b"], 0.62, 4),
]
ES_RULES = [
    Rule("es-ser-estar", [r"\b(?:soy|eres|es|somos|sois|son|estoy|estás|está|estamos|estáis|están)\b"], 0.6, 3),
    Rule("es-subjunctive", [r"\b(?:que|ojalá)\b[^.!?]{0,60}\b\w+(?:e|es|emos|éis|en)\b"], 0.55, 4),
]
RU_RULES = [Rule("ru-cases", [r"\b(?:в|на|с|к|о|об|для|без|из|от|до|по)\b"], 0.45, 2)]

RULES = {
    "en": EN_RULES, "ja": JA_RULES, "zh": ZH_RULES, "zh-CN": ZH_RULES, "zh-TW": ZH_RULES,
    "ko": KO_RULES, "fr": FR_RULES, "de": DE_RULES, "es": ES_RULES, "ru": RU_RULES,
}


def _install_data_rules() -> None:
    """Turn ``patterns`` in the grammar atlas into detector rules.

    Entries can ship their own regex so adding a language is a data change, not
    a second code change.  Invalid patterns fail at startup with the grammar id
    attached, which is far easier to fix than a silent false negative.
    """
    installed: dict[str, set[str]] = {lang: {r.gid for r in rules} for lang, rules in RULES.items()}
    for entry in detection_entries():
        lang = entry["language"]
        patterns = [p for p in entry.get("patterns", []) if isinstance(p, str) and p.strip()]
        if not patterns or entry["id"] in installed.setdefault(lang, set()):
            continue
        try:
            rule = Rule(
                entry["id"], patterns,
                confidence=float(entry.get("confidence", 0.76)),
                priority=int(entry.get("priority", 4)),
            )
        except re.error as exc:  # pragma: no cover - authoring guard
            raise RuntimeError(f"Invalid regex in grammar {entry['id']}: {exc}") from exc
        RULES.setdefault(lang, []).append(rule)
        installed[lang].add(entry["id"])


_install_data_rules()

MAX_POINTS = 24
MAX_OCCURRENCES = 4
LANG_SHORT = {code: code for code in GRAMMAR_LANGUAGE_ORDER}
LANG_SHORT.update({"zh-CN": "zh", "zh-TW": "zh"})


def _sentence_rows(text: str) -> list[dict]:
    rows = []
    for block in split_blocks(text):
        if block.get("type") in {"code", "table"}:
            continue
        for sentence in split_sentences(block.get("text", "")):
            s = sentence.strip()
            if len(s) < 3:
                continue
            rows.append({"blockId": block["id"], "sentence": s})
    return rows


def analyze(text: str, language: str = "auto") -> dict:
    text = (text or "").strip()
    detected = detect_language(text) if language in ("auto", "", None) else {
        "code": language, "confidence": 0.99
    }
    lang = LANG_SHORT.get(detected["code"], detected["code"])
    rules = RULES.get(lang, [])
    rows = _sentence_rows(text)
    hits: dict[str, list[dict]] = {}
    for row in rows:
        sentence = row["sentence"]
        for rule in rules:
            if rule.deny and re.search(rule.deny, sentence, re.I):
                continue
            if rule.allow and not re.search(rule.allow, sentence):
                continue
            matched = None
            for pattern in rule.compiled:
                m = pattern.search(sentence)
                if m:
                    matched = m.group(0).strip()
                    break
            if not matched:
                continue
            bucket = hits.setdefault(rule.gid, [])
            if len(bucket) < MAX_OCCURRENCES and not any(x["sentence"] == sentence for x in bucket):
                bucket.append({
                    "blockId": row["blockId"],
                    "sentence": sentence[:320],
                    "match": matched[:80],
                })
    points = []
    for gid, occurrences in hits.items():
        entry = get_grammar(gid)
        if not entry:
            continue
        rule = next((r for r in rules if r.gid == gid), None)
        confidence = min(0.99, (rule.confidence if rule else 0.7) + 0.012 * max(0, len(occurrences) - 1))
        points.append({
            "id": gid, "language": entry["language"], "title": entry["title"],
            "english": entry["english"], "category": entry["category"], "cefr": entry["cefr"],
            "formula": entry["formula"], "summary": entry["summary"],
            "count": len(occurrences), "confidence": round(confidence, 2),
            "occurrences": occurrences,
            "source": "rule",
        })
    priority = {}
    for lang_rules in RULES.values():
        for r in lang_rules:
            priority[r.gid] = max(priority.get(r.gid, 0), r.priority)
    points.sort(key=lambda p: (-p["count"], -priority.get(p["id"], 0), p["cefr"]))
    points = points[:MAX_POINTS]
    groups: dict[str, int] = {}
    for p in points:
        groups[p["category"]] = groups.get(p["category"], 0) + 1
    cefr: dict[str, int] = {}
    for p in points:
        cefr[p["cefr"]] = cefr.get(p["cefr"], 0) + 1
    return {
        "language": lang,
        "detected": detected,
        "points": points,
        "summary": {"total": len(points), "categories": groups, "cefr": cefr},
    }


def detail(grammar_id: str) -> dict | None:
    return get_grammar(grammar_id)


def all_library() -> list[dict]:
    language_order = {code: index for index, code in enumerate(GRAMMAR_LANGUAGE_ORDER)}
    category_order = {
        "时态": 0, "时态·体": 1, "体": 2, "语态": 3, "语气": 4, "从句": 5,
        "句法": 6, "句式": 7, "非谓语": 8, "助词": 9, "助动词": 10, "接续": 11,
        "条件": 12, "动词": 13, "名词": 14, "代词": 15, "形容词": 16, "副词": 17,
        "介词": 18, "后置词": 19, "限定词": 20, "数量词": 21, "比较": 22,
        "强调": 23, "复句": 24, "补语": 25, "量词": 26, "语序": 27, "敬语": 28,
        "授受": 29, "格": 30, "名词化": 31, "构词": 32, "否定": 33, "疑问": 34,
    }
    return sorted(GRAMMAR.values(), key=lambda e: (
        language_order.get(e["language"], 99),
        category_order.get(e["category"], 50),
        e["cefr"],
        e["id"],
    ))


def library_stats() -> dict:
    by_language, by_category = {}, {}
    for e in GRAMMAR.values():
        by_language[e["language"]] = by_language.get(e["language"], 0) + 1
        by_category[e["category"]] = by_category.get(e["category"], 0) + 1
    return {
        "total": len(GRAMMAR),
        "byLanguage": by_language,
        "byCategory": by_category,
        "languageNames": dict(GRAMMAR_LANGUAGE_NAMES),
        "languages": grammar_catalog(by_language),
    }
