"""Sentence-level article breakdown for English, Chinese and Japanese.

The goal is a transparent, offline-first reading aid: every sentence gets a
lightweight POS / phrase / clause breakdown plus the grammar features that can
be named with rules. It is deliberately not a full dependency parser; results
are labelled as rule-based in the UI.
"""
from __future__ import annotations

import re
from functools import lru_cache

from .text import split_sentences
from .languages import LANGUAGES

# ---------------------------------------------------------------- feature catalog
FEATURES: dict[str, dict[str, dict]] = {
    "en": {
        "article": {"title": "冠词", "category": "限定词", "pattern": "a / an / the + 名词", "summary": "冠词承载可数性和特指性；中文没有冠词，最容易漏用。", "detail": "en-article"},
        "preposition": {"title": "介词短语", "category": "介词", "pattern": "介词 + 名词短语", "summary": "介词短语常作状语或后置定语，决定时间、地点、方式和关系。", "detail": "en-preposition"},
        "present": {"title": "一般现在时", "category": "时态", "pattern": "动词原形 / 第三人称单数 -s", "summary": "表示习惯、事实、真理或当前状态。", "detail": "en-present-simple"},
        "past": {"title": "一般过去时", "category": "时态", "pattern": "动词过去式", "summary": "表示过去某个时间发生并结束的动作或状态。", "detail": "en-past-simple"},
        "future": {"title": "将来表达", "category": "时态", "pattern": "will / be going to + 动词原形", "summary": "will 偏预测或临场决定，be going to 偏计划或眼前证据。", "detail": "en-future-forms"},
        "present_perfect": {"title": "现在完成时", "category": "时态", "pattern": "have / has + 过去分词", "summary": "过去的动作与现在的结果、经验或持续状态相连。", "detail": "en-present-perfect"},
        "past_perfect": {"title": "过去完成时", "category": "时态", "pattern": "had + 过去分词", "summary": "以过去某一时间为锚点，表示“过去的过去”。", "detail": "en-past-perfect"},
        "continuous": {"title": "进行时", "category": "时态", "pattern": "be + 动词 -ing", "summary": "强调某一时刻正在发生或持续的动作。", "detail": "en-present-continuous"},
        "passive": {"title": "被动语态", "category": "语态", "pattern": "be + 过去分词", "summary": "把动作承受者放到主语位置，常用于未知、不重要或想弱化施动者时。", "detail": "en-passive-voice"},
        "modal": {"title": "情态动词", "category": "情态", "pattern": "can / may / must / should + 动词原形", "summary": "表达能力、可能、义务、建议和推测。", "detail": "en-modal-verbs"},
        "negation": {"title": "否定", "category": "句法", "pattern": "助动词 + not；no / never", "summary": "英语否定位置固定在第一个助动词之后。", "detail": "en-negation"},
        "relative": {"title": "定语从句", "category": "从句", "pattern": "名词 + who / which / that / whose", "summary": "用从句修饰前面的名词，补充身份、特征或限定范围。", "detail": "en-relative-clause"},
        "noun_clause": {"title": "名词性从句", "category": "从句", "pattern": "that / whether / if / wh- + 从句", "summary": "整个从句充当主语、宾语、表语或同位语。", "detail": "en-noun-clause"},
        "adverbial_clause": {"title": "状语从句", "category": "从句", "pattern": "because / although / if / when / while + 从句", "summary": "表达原因、让步、条件、时间等逻辑关系。", "detail": "en-adverbial-clause"},
        "infinitive": {"title": "动词不定式", "category": "非谓语", "pattern": "to + 动词原形", "summary": "可作主语、宾语、目的状语或后置定语。", "detail": "en-infinitive"},
        "gerund": {"title": "动名词", "category": "非谓语", "pattern": "动词 -ing 作名词", "summary": "把动作名词化，常作主语或介词宾语。", "detail": "en-gerund"},
        "participle": {"title": "分词结构", "category": "非谓语", "pattern": "现在分词 -ing / 过去分词 -ed", "summary": "分词短语可作定语、状语或补语，压缩从句。", "detail": "en-participle"},
        "conditional": {"title": "条件句", "category": "语气", "pattern": "if / unless + 条件，主句 + 结果", "summary": "真实、非真实和过去虚拟条件有不同时态搭配。", "detail": "en-conditional"},
        "comparative": {"title": "比较结构", "category": "形容词", "pattern": "-er / more + than；as ... as", "summary": "比较级和同级比较用来建立程度、数量或性质的关系。", "detail": "en-comparison"},
        "there_be": {"title": "There be 句型", "category": "句式", "pattern": "There is / are + 名词", "summary": "表示某处存在某物，主语常后置。", "detail": "en-there-be"},
        "imperative": {"title": "祈使句", "category": "句式", "pattern": "动词原形 (+ 宾语)", "summary": "省略主语 you，表达命令、请求、建议或邀请。", "detail": "en-imperative"},
        "question": {"title": "疑问句", "category": "句式", "pattern": "助动词 / wh- 词提前", "summary": "一般疑问句靠助动词倒装，特殊疑问句再加疑问词。", "detail": "en-questions"},
        "inversion": {"title": "倒装", "category": "语序", "pattern": "否定副词 / only 置于句首，助动词提前", "summary": "为了强调或正式语体，把助动词放到主语前。", "detail": "en-inversion"},
        "cleft": {"title": "强调句", "category": "句式", "pattern": "It is / was ... that / who ...", "summary": "把被强调的成分放进 it is ... that 框架。", "detail": "en-cleft"},
        "reporting": {"title": "引语与转述", "category": "句法", "pattern": "say / tell + that 从句", "summary": "转述他人话语时要注意时态后移和代词调整。", "detail": "en-reported-speech"},
    },
    "zh": {
        "shi": {"title": "是字句", "category": "句式", "pattern": "主语 + 是 + 宾语", "summary": "判断、说明或归类；否定用“不是”。", "detail": "zh-shi"},
        "ba": {"title": "把字句", "category": "句式", "pattern": "主语 + 把 + 宾语 + 动词 + 补语", "summary": "强调对宾语的处置结果，动词后通常要带补语或体标记。", "detail": "zh-ba"},
        "bei": {"title": "被字句", "category": "句式", "pattern": "主语 + 被 (+ 施事) + 动词", "summary": "从受事视角叙述，常带不如意或被动结果。", "detail": "zh-bei"},
        "le": {"title": "动态助词“了”", "category": "助词", "pattern": "动词 + 了", "summary": "表示动作完成或状态变化，不等于英语过去时。", "detail": "zh-le"},
        "zhe": {"title": "动态助词“着”", "category": "助词", "pattern": "动词 + 着", "summary": "表示动作或状态的持续。", "detail": "zh-zhe"},
        "guo": {"title": "动态助词“过”", "category": "助词", "pattern": "动词 + 过", "summary": "表示曾经有过的经历。", "detail": "zh-guo"},
        "de": {"title": "结构助词“的 / 地 / 得”", "category": "助词", "pattern": "定语 + 的 + 名词；状语 + 地 + 动词；动词 + 得 + 补语", "summary": "三个 de 分别标记定语、状语和补语。", "detail": "zh-de"},
        "bi": {"title": "比较句", "category": "比较", "pattern": "A + 比 + B + 形容词", "summary": "比较两者程度；否定用“不比”，最高级用“最”。", "detail": "zh-bi"},
        "you": {"title": "存在句", "category": "句式", "pattern": "处所 + 有 + 名词", "summary": "表示某处存在某人或某物。", "detail": "zh-you"},
        "lian": {"title": "“连”字句", "category": "强调", "pattern": "连 + 名词 + 都 / 也 + 动词", "summary": "用极端例子强调，常含“甚至连……都”的意味。", "detail": "zh-lian"},
        "shi_de": {"title": "“是……的”强调句", "category": "强调", "pattern": "是 + 焦点 + 的", "summary": "强调时间、地点、方式或施事者。", "detail": "zh-shi-de"},
        "question": {"title": "疑问句", "category": "句式", "pattern": "吗 / 呢 / 吧 / 正反问 / 疑问词", "summary": "汉语疑问不一定倒装，靠语气词和疑问词表达。", "detail": "zh-question"},
        "compound": {"title": "复句关系", "category": "复句", "pattern": "因为……所以 / 虽然……但是 / 如果……就", "summary": "关联词标记因果、转折、条件、递进等逻辑关系。", "detail": "zh-compound"},
        "pivot": {"title": "兼语句", "category": "句式", "pattern": "主语 + 让 / 叫 / 请 / 使 + 宾语 + 动词", "summary": "第一个动词的宾语同时是第二个动词的主语。", "detail": "zh-pivot"},
        "serial": {"title": "连动句", "category": "句式", "pattern": "主语 + 动词1 + 动词2", "summary": "两个动作共享一个主语，按时间或逻辑顺序排列。", "detail": "zh-serial"},
        "measure": {"title": "量词", "category": "量词", "pattern": "数词 + 量词 + 名词", "summary": "汉语名词通常需要量词，量词也承载形状和类别信息。", "detail": "zh-measure"},
        "aspect": {"title": "体标记", "category": "助词", "pattern": "了 / 着 / 过", "summary": "汉语用体标记表达完成、持续和经历，而不是严格的时间时态。", "detail": "zh-aspect"},
        "complement": {"title": "补语", "category": "句法", "pattern": "动词 + 得 / 结果 / 趋向 / 可能补语", "summary": "补语补充动作的结果、程度、方向或可能性。", "detail": "zh-complement"},
        "topic": {"title": "话题结构", "category": "语序", "pattern": "话题 + 评论", "summary": "汉语常把已知信息放句首作话题，再给评论。", "detail": "zh-topic"},
    },
    "ja": {
        "te": {"title": "て形", "category": "活用", "pattern": "动词て形 / で形", "summary": "用于连接、请求、进行和状态，是日语最核心的连接形式。", "detail": "ja-te"},
        "ta": {"title": "た形", "category": "活用", "pattern": "动词/形容词た形", "summary": "表示过去、完成或确认。", "detail": "ja-ta"},
        "nai": {"title": "ない形", "category": "活用", "pattern": "动词ない形", "summary": "表示否定，也是可能、被动、使役等变形的基础。", "detail": "ja-nai"},
        "potential": {"title": "可能形", "category": "活用", "pattern": "动词可能形 / できる", "summary": "表示能力或可能性。", "detail": "ja-potential"},
        "passive": {"title": "受身形", "category": "语态", "pattern": "动词れる / られる", "summary": "从受事角度叙述，也可表达受害或敬语。", "detail": "ja-passive"},
        "causative": {"title": "使役形", "category": "语态", "pattern": "动词せる / させる", "summary": "表示让某人做某事，或允许、放任。", "detail": "ja-causative"},
        "volitional": {"title": "意向形", "category": "语气", "pattern": "动词う / よう", "summary": "表示意志、提议或“让我们一起……”。", "detail": "ja-volitional"},
        "conditional": {"title": "条件表达", "category": "条件", "pattern": "と / ば / たら / なら", "summary": "四种条件形式在确定性、时间顺序和前提上各有侧重。", "detail": "ja-conditional"},
        "polite": {"title": "敬体", "category": "敬语", "pattern": "です / ます", "summary": "面向听者的礼貌体，说明文和初学者写作常用。", "detail": "ja-polite"},
        "particle_wa": {"title": "助词は", "category": "助词", "pattern": "名词 + は", "summary": "提示主题，常与已知信息或对比有关。", "detail": "ja-wa"},
        "particle_ga": {"title": "助词が", "category": "助词", "pattern": "名词 + が", "summary": "标记主语或新信息，也用于能力、喜好、存在句。", "detail": "ja-ga"},
        "particle_wo": {"title": "助词を", "category": "助词", "pattern": "名词 + を + 动词", "summary": "标记他动词的直接宾语。", "detail": "ja-wo"},
        "particle_ni": {"title": "助词に", "category": "助词", "pattern": "名词 + に", "summary": "标记时间、目的地、对象、存在场所或结果。", "detail": "ja-ni"},
        "particle_de": {"title": "助词で", "category": "助词", "pattern": "名词 + で", "summary": "标记手段、场所、原因或材料。", "detail": "ja-de"},
        "particle_no": {"title": "助词の", "category": "助词", "pattern": "名词 + の + 名词", "summary": "连接名词，表示所属、属性或同位关系。", "detail": "ja-no"},
        "relative": {"title": "连体修饰", "category": "从句", "pattern": "动词/形容词普通形 + 名词", "summary": "日语定语从句直接放在名词前，不需要关系代词。", "detail": "ja-relative"},
        "passive_ni": {"title": "被动对象に", "category": "语态", "pattern": "受事 + に + 受身", "summary": "被动句中常用に标记动作来源或受影响对象。", "detail": "ja-passive"},
        "giving": {"title": "授受表达", "category": "授受", "pattern": "てあげる / てくれる / てもらう", "summary": "根据给予方向和使用者视角选择授受动词。", "detail": "ja-giving"},
        "honorific": {"title": "尊敬语与谦让语", "category": "敬语", "pattern": "お/ご + 动词；いただく / くださる", "summary": "敬语通过词汇替换和句型提升对方、降低自己。", "detail": "ja-honorific"},
    },
}

# ---------------------------------------------------------------- token helpers
_EN_DET = {"a", "an", "the", "this", "that", "these", "those", "my", "your", "his", "her", "its", "our", "their", "some", "any", "no", "every", "each", "either", "neither", "both", "all", "few", "many", "much", "more", "most", "several", "another"}
_EN_PRON = {"i", "you", "he", "she", "it", "we", "they", "me", "him", "us", "them", "myself", "yourself", "himself", "herself", "itself", "ourselves", "themselves", "someone", "somebody", "anyone", "anybody", "everyone", "everybody", "nobody", "nothing", "everything"}
_EN_PREP = {"in", "on", "at", "by", "for", "with", "from", "to", "of", "about", "into", "over", "under", "between", "among", "through", "during", "before", "after", "against", "without", "within", "upon", "across", "along", "behind", "beyond", "despite", "except", "inside", "outside", "since", "toward", "towards", "until", "via", "per", "as"}
_EN_CONJ = {"and", "or", "but", "nor", "so", "yet", "because", "although", "though", "while", "whereas", "if", "unless", "when", "whenever", "before", "after", "until", "whether", "that", "who", "which", "whose", "whom", "since", "as"}
_EN_AUX = {"be", "am", "is", "are", "was", "were", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "shall", "should", "can", "could", "may", "might", "must"}
_EN_MODAL = {"can", "could", "may", "might", "must", "shall", "should", "will", "would", "ought"}
_EN_ADV = {"not", "never", "very", "quite", "rather", "too", "also", "just", "only", "even", "still", "already", "yet", "always", "often", "sometimes", "usually", "rarely", "soon", "later", "here", "there", "now", "then", "however", "therefore", "thus", "otherwise", "perhaps", "maybe", "almost", "enough", "well", "fast", "hard", "together", "again", "once", "twice", "rather", "quite"}
_EN_IRREG = {"be": "be", "am": "be", "is": "be", "are": "be", "was": "be", "were": "be", "been": "be", "being": "be", "have": "have", "has": "have", "had": "have", "do": "do", "does": "do", "did": "do", "done": "do", "go": "go", "went": "go", "gone": "go", "see": "see", "saw": "see", "seen": "see", "make": "make", "made": "make", "take": "take", "took": "take", "taken": "take", "write": "write", "wrote": "write", "written": "write", "read": "read", "say": "say", "said": "say", "think": "think", "thought": "think", "know": "know", "knew": "know", "known": "know", "come": "come", "came": "come", "give": "give", "gave": "give", "given": "give", "find": "find", "found": "find", "feel": "feel", "felt": "feel", "leave": "leave", "left": "leave", "keep": "keep", "kept": "keep", "begin": "begin", "began": "begin", "begun": "begin", "run": "run", "ran": "run", "hold": "hold", "held": "hold", "bring": "bring", "brought": "bring", "buy": "buy", "bought": "buy", "pay": "pay", "paid": "pay", "meet": "meet", "met": "meet", "lose": "lose", "lost": "lose", "win": "win", "won": "win", "speak": "speak", "spoke": "speak", "spoken": "speak", "teach": "teach", "taught": "teach", "learn": "learn", "learnt": "learn", "learned": "learn", "build": "build", "built": "build", "send": "send", "sent": "send", "spend": "spend", "spent": "spend", "grow": "grow", "grew": "grow", "grown": "grow", "fall": "fall", "fell": "fall", "fallen": "fall"}
_EN_TOKEN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?|\d+(?:\.\d+)?|[^\sA-Za-z0-9]")

POS_ZH = {"n": "名词", "nr": "人名", "ns": "地名", "nt": "机构", "nz": "专名", "v": "动词", "vd": "副动词", "vn": "动名词", "a": "形容词", "ad": "副形词", "an": "名形词", "d": "副词", "p": "介词", "c": "连词", "r": "代词", "m": "数词", "q": "量词", "u": "助词", "t": "时间词", "f": "方位词", "s": "处所词", "e": "叹词", "o": "拟声词", "eng": "英文", "x": "标点"}
POS_JA = {"名詞": "名词", "動詞": "动词", "形容詞": "形容词", "形容動詞": "形容动词", "副詞": "副词", "助詞": "助词", "助動詞": "助动词", "接続詞": "连词", "連体詞": "连体词", "感動詞": "感叹词", "記号": "标点", "接頭詞": "前缀", "フィラー": "填充词"}


def _en_pos(tokens: list[str]) -> list[str]:
    out = []
    for i, token in enumerate(tokens):
        low = token.lower()
        prev = tokens[i - 1].lower() if i else ""
        if not re.search(r"[A-Za-z0-9]", token):
            pos = "标点"
        elif token[0].isdigit():
            pos = "数词"
        elif low in _EN_DET:
            pos = "限定词"
        elif low in _EN_PRON:
            pos = "代词"
        elif low in _EN_PREP:
            pos = "介词"
        elif low in _EN_CONJ:
            pos = "连词"
        elif low in _EN_MODAL:
            pos = "情态动词"
        elif low in _EN_AUX:
            pos = "助动词"
        elif low in _EN_ADV or low.endswith("ly"):
            pos = "副词"
        elif low.endswith("ing") and len(low) > 5:
            nxt = tokens[i + 1].lower() if i + 1 < len(tokens) else ""
            pos = "名词" if i == 0 and nxt in ("is", "are", "was", "were", "has", "have", "had") else "动词"
        elif low.endswith("ed") and len(low) > 4:
            pos = "动词"
        elif low.endswith(("ous", "ful", "less", "able", "ible", "ive", "al", "ic", "ary")):
            pos = "形容词"
        elif prev in _EN_DET:
            pos = "名词"
        elif prev in ("very", "more", "most", "quite", "rather"):
            pos = "形容词"
        elif token[0].isupper() and i > 0:
            pos = "名词"
        else:
            pos = "名词"
        out.append(pos)
    return out


def _en_lemma(word: str, pos: str) -> str:
    low = word.lower()
    if low in _EN_IRREG:
        return _EN_IRREG[low]
    if pos == "动词" and low.endswith("ing") and len(low) > 5:
        return low[:-3]
    if pos == "动词" and low.endswith("ed") and len(low) > 4:
        return low[:-2]
    if pos == "名词" and low.endswith("s") and len(low) > 3:
        return low[:-1]
    return low


def _en_tokens(text: str) -> list[dict]:
    raw = _EN_TOKEN.findall(text)
    tags = _en_pos(raw)
    return [{"text": t, "pos": p, "lemma": _en_lemma(t, p)} for t, p in zip(raw, tags)]


def _en_join(tokens: list[dict]) -> str:
    return " ".join(t["text"] for t in tokens if (t.get("text") or "").strip())


def _en_chunks(tokens: list[dict]) -> list[dict]:
    chunks = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        pos = tok["pos"]
        text = tok["text"]
        if pos in ("标点", "连词"):
            if pos == "连词":
                chunks.append({"label": "连接", "role": "连接", "text": text})
            i += 1
            continue
        if pos == "介词":
            j = i + 1
            while j < len(tokens) and tokens[j]["pos"] in ("限定词", "形容词", "名词", "代词", "数词"):
                j += 1
            chunks.append({"label": "介词短语", "role": "状语", "text": _en_join(tokens[i:j])})
            i = j
            continue
        if pos in ("限定词", "形容词") or (pos == "数词" and i + 1 < len(tokens)):
            j = i
            while j < len(tokens) and tokens[j]["pos"] in ("限定词", "形容词", "数词"):
                j += 1
            if j < len(tokens) and tokens[j]["pos"] in ("名词", "代词"):
                j += 1
                while j < len(tokens) and tokens[j]["pos"] == "名词":
                    j += 1
                chunks.append({"label": "名词短语", "role": "", "text": _en_join(tokens[i:j])})
                i = j
                continue
        if pos == "名词" or pos == "代词":
            j = i + 1
            while j < len(tokens) and tokens[j]["pos"] == "名词":
                j += 1
            chunks.append({"label": "名词短语", "role": "", "text": _en_join(tokens[i:j])})
            i = j
            continue
        if pos in ("助动词", "情态动词", "动词"):
            j = i
            while j < len(tokens) and tokens[j]["pos"] in ("助动词", "情态动词", "动词", "副词"):
                j += 1
            chunks.append({"label": "动词短语", "role": "", "text": _en_join(tokens[i:j])})
            i = j
            continue
        if pos == "副词":
            chunks.append({"label": "副词", "role": "状语", "text": text})
            i += 1
            continue
        chunks.append({"label": pos, "role": "", "text": text})
        i += 1
    return chunks


def _en_features(text: str, tokens: list[dict]) -> list[dict]:
    low = [t["text"].lower() for t in tokens]
    joined = " ".join(low)
    found = []

    def add(key):
        if key in FEATURES["en"] and key not in {f["key"] for f in found}:
            found.append({"key": key, **FEATURES["en"][key]})

    def next_token(index: int) -> dict | None:
        return tokens[index + 1] if index + 1 < len(tokens) else None

    def is_be(word: str) -> bool:
        return word in ("am", "is", "are", "was", "were", "be", "been", "being")

    def is_participle(token: dict | None) -> bool:
        if not token or token["pos"] != "动词":
            return False
        word = token["text"].lower()
        return word.endswith("ed") or (word in _EN_IRREG and word not in ("be", "am", "is", "are", "was", "were", "been", "being", "have", "has", "had", "do", "does", "did"))

    if any(w in low for w in ("a", "an", "the")):
        add("article")
    if any(t["pos"] == "介词" for t in tokens):
        add("preposition")
    if any(w in low for w in ("will", "shall")) or "going to" in joined:
        add("future")
    for i, token in enumerate(tokens):
        word = token["text"].lower()
        nxt = next_token(i)
        if word in ("have", "has") and is_participle(nxt):
            add("present_perfect")
        if word == "had" and is_participle(nxt):
            add("past_perfect")
        if is_be(word) and nxt and nxt["text"].lower().endswith("ing"):
            add("continuous")
        if is_be(word) and is_participle(nxt):
            add("passive")
        if word in ("to",) and nxt and nxt["pos"] in ("动词", "助动词"):
            add("infinitive")
    if any(w in _EN_MODAL for w in low):
        add("modal")
    if any(w in low for w in ("not", "no", "never", "n't")) or "n't" in text:
        add("negation")
    if any(w in low for w in ("who", "which", "whose", "whom", "that")) and any(t["pos"] == "名词" for t in tokens):
        add("relative")
    if any(w in low for w in ("because", "although", "though", "while", "if", "unless", "when", "before", "after", "since", "whereas")):
        add("adverbial_clause")
    if any(w in low for w in ("that", "whether", "if")):
        add("noun_clause")
    if any(t["text"].lower().endswith("ing") for t in tokens) and not any(is_be(w) for w in low):
        add("gerund")
    if any(t["text"].lower().endswith("ed") for t in tokens) and not any(w in low for w in ("have", "has", "had")) and not any(is_be(w) for w in low):
        add("participle")
    if any(w in low for w in ("if", "unless", "would", "could", "should")):
        add("conditional")
    if any(w in low for w in ("more", "most", "than", "less", "least")) or any(t["text"].lower().endswith("er") for t in tokens):
        add("comparative")
    if "there" in low and any(w in low for w in ("is", "are", "was", "were")):
        add("there_be")
    if tokens and tokens[0]["pos"] == "动词" and not any(t["pos"] == "代词" for t in tokens[:2]):
        add("imperative")
    if "?" in text or (tokens and tokens[0]["text"].lower() in _EN_AUX):
        add("question")
    if any(w in low for w in ("never", "rarely", "seldom", "hardly", "only")) and tokens and tokens[0]["text"].lower() in ("never", "rarely", "seldom", "hardly", "only"):
        add("inversion")
    if "it" in low and any(w in low for w in ("that", "who")) and any(w in low for w in ("is", "was")):
        add("cleft")
    if any(w in low for w in ("said", "says", "told", "asked")):
        add("reporting")

    # Simple tense labels only when no more specific perfect/continuous form won.
    present_keys = {f["key"] for f in found}
    has_finite_verb = any(t["pos"] == "动词" for t in tokens) or any(w in low for w in ("am", "is", "are", "was", "were"))
    if has_finite_verb and not present_keys.intersection({"present_perfect", "past_perfect", "future", "continuous"}):
        aux_forms = {"be", "am", "is", "are", "was", "were", "been", "being", "have", "has", "had", "do", "does", "did"}
        past_form = any(
            t["pos"] == "动词"
            and (t["text"].lower().endswith("ed") or (t["text"].lower() in _EN_IRREG and t["text"].lower() not in aux_forms))
            for t in tokens
        )
        if past_form:
            add("past")
        elif any(t["pos"] == "动词" for t in tokens):
            add("present")
    return found


def _assign_roles_en(chunks: list[dict]) -> dict:
    subject = predicate = obj = ""
    for chunk in chunks:
        if not subject and chunk["label"] == "名词短语":
            subject = chunk["text"]
            chunk["role"] = chunk["role"] or "主语"
        elif not predicate and chunk["label"] == "动词短语":
            predicate = chunk["text"]
            chunk["role"] = chunk["role"] or "谓语"
        elif predicate and not obj and chunk["label"] == "名词短语":
            obj = chunk["text"]
            chunk["role"] = chunk["role"] or "宾语"
        elif chunk["label"] == "介词短语":
            chunk["role"] = chunk["role"] or "状语"
    return {"subject": subject, "predicate": predicate, "object": obj, "adverbial": " ".join(c["text"] for c in chunks if c["role"] == "状语")}


def _analyze_en(text: str) -> dict:
    tokens = _en_tokens(text)
    chunks = _en_chunks(tokens)
    return {"tokens": tokens, "chunks": chunks, "skeleton": _assign_roles_en(chunks), "features": _en_features(text, tokens)}


# ---------------------------------------------------------------- Chinese
@lru_cache(maxsize=1)
def _jieba():
    import jieba
    import jieba.posseg as pseg
    jieba.setLogLevel(20)
    return pseg


def _zh_tokens(text: str) -> list[dict]:
    pseg = _jieba()
    out = []
    for word, flag in pseg.cut(text):
        if not word.strip():
            continue
        if word in ("不是", "就是", "还是", "只是", "也是"):
            pos = "动词"
        elif word == "的":
            pos = "助词"
        else:
            pos = POS_ZH.get(flag, flag or "词语")
        out.append({"text": word, "pos": pos, "lemma": word})
    return out


def _zh_chunks(tokens: list[dict]) -> list[dict]:
    chunks = []
    i = 0
    while i < len(tokens):
        pos = tokens[i]["pos"]
        if pos in ("标点", "连词"):
            if pos == "连词":
                chunks.append({"label": "连接", "role": "连接", "text": tokens[i]["text"]})
            i += 1
            continue
        if pos in ("介词",):
            j = i + 1
            while j < len(tokens) and tokens[j]["pos"] in ("代词", "名词", "数词", "量词", "形容词", "人名", "地名", "机构", "专名"):
                j += 1
            chunks.append({"label": "介词短语", "role": "状语", "text": "".join(t["text"] for t in tokens[i:j])})
            i = j
            continue
        if pos in ("数词",):
            j = i + 1
            while j < len(tokens) and tokens[j]["pos"] in ("量词", "形容词", "名词", "动名词"):
                j += 1
            chunks.append({"label": "名词短语", "role": "", "text": "".join(t["text"] for t in tokens[i:j])})
            i = j
            continue
        if pos in ("代词", "名词", "人名", "地名", "机构", "专名", "量词", "时间词", "方位词", "处所词", "动名词"):
            j = i + 1
            while j < len(tokens) and tokens[j]["pos"] in ("名词", "人名", "地名", "机构", "专名", "量词", "时间词", "方位词", "处所词", "动名词", "助词"):
                if tokens[j]["text"] not in ("的", "地", "得"):
                    j += 1
                else:
                    break
            chunks.append({"label": "名词短语", "role": "", "text": "".join(t["text"] for t in tokens[i:j])})
            i = j
            continue
        if pos in ("动词", "副动词", "动名词"):
            j = i + 1
            while j < len(tokens) and tokens[j]["pos"] in ("动词", "助词", "副词", "趋向词"):
                j += 1
            chunks.append({"label": "动词短语", "role": "", "text": "".join(t["text"] for t in tokens[i:j])})
            i = j
            continue
        if pos == "副词":
            chunks.append({"label": "副词", "role": "状语", "text": tokens[i]["text"]})
            i += 1
            continue
        chunks.append({"label": pos, "role": "", "text": tokens[i]["text"]})
        i += 1
    return chunks


def _zh_features(text: str, tokens: list[dict]) -> list[dict]:
    found = []

    def add(key):
        if key in FEATURES["zh"] and key not in {f["key"] for f in found}:
            found.append({"key": key, **FEATURES["zh"][key]})

    if "是" in text or "不是" in text:
        add("shi")
    if "把" in text:
        add("ba")
    if "被" in text:
        add("bei")
    if any(t["text"] == "了" for t in tokens):
        add("le")
    if any(t["text"] == "着" for t in tokens):
        add("zhe")
    if any(t["text"] == "过" for t in tokens):
        add("guo")
    if any(t["text"] in ("的", "地", "得") for t in tokens):
        add("de")
    if "比" in text:
        add("bi")
    if "有" in text:
        add("you")
    if "连" in text and ("都" in text or "也" in text):
        add("lian")
    if re.search(r"是.{1,14}的[。！？!?]?$", text):
        add("shi_de")
    if "?" in text or "？" in text or any(x in text for x in ("吗", "呢", "吧")):
        add("question")
    if any(x in text for x in ("因为", "所以", "虽然", "但是", "如果", "只要", "不但", "而且", "或者", "然后", "而")):
        add("compound")
    if any(x in text for x in ("让", "叫", "请", "使", "令")):
        add("pivot")
    action_verbs = [t for t in tokens if t["pos"] == "动词" and t["text"] not in ("是", "不是", "就是", "还是", "只是", "也是")]
    if len(action_verbs) >= 2:
        add("serial")
    if any(t["pos"] == "量词" for t in tokens):
        add("measure")
    if any(t["text"] in ("了", "着", "过") for t in tokens):
        add("aspect")
    if any(t["text"] == "得" for t in tokens):
        add("complement")
    if tokens and tokens[0]["pos"] in ("名词", "代词", "人名", "地名", "专名"):
        add("topic")
    return found


def _assign_roles_zh(chunks: list[dict]) -> dict:
    subject = predicate = obj = ""
    for chunk in chunks:
        if not subject and chunk["label"] == "名词短语":
            subject = chunk["text"]
            chunk["role"] = chunk["role"] or "主语"
        elif not predicate and chunk["label"] == "动词短语":
            predicate = chunk["text"]
            chunk["role"] = chunk["role"] or "谓语"
        elif predicate and not obj and chunk["label"] == "名词短语":
            obj = chunk["text"]
            chunk["role"] = chunk["role"] or "宾语"
        elif chunk["label"] == "介词短语":
            chunk["role"] = chunk["role"] or "状语"
    return {"subject": subject, "predicate": predicate, "object": obj, "adverbial": " ".join(c["text"] for c in chunks if c["role"] == "状语")}


def _analyze_zh(text: str) -> dict:
    tokens = _zh_tokens(text)
    chunks = _zh_chunks(tokens)
    return {"tokens": tokens, "chunks": chunks, "skeleton": _assign_roles_zh(chunks), "features": _zh_features(text, tokens)}


# ---------------------------------------------------------------- Japanese
@lru_cache(maxsize=1)
def _janome():
    from janome.tokenizer import Tokenizer
    return Tokenizer()


def _ja_tokens(text: str) -> list[dict]:
    tokenizer = _janome()
    out = []
    for token in tokenizer.tokenize(text):
        pos = POS_JA.get(token.part_of_speech.split(",")[0], token.part_of_speech.split(",")[0])
        out.append({"text": token.surface, "pos": pos, "lemma": token.base_form, "reading": token.reading})
    return out


def _ja_chunks(tokens: list[dict]) -> list[dict]:
    chunks = []
    i = 0
    while i < len(tokens):
        pos = tokens[i]["pos"]
        if pos in ("标点", "连词"):
            if pos == "连词":
                chunks.append({"label": "连接", "role": "连接", "text": tokens[i]["text"]})
            i += 1
            continue
        if pos in ("名词", "代词", "数词"):
            j = i + 1
            while j < len(tokens) and tokens[j]["pos"] in ("名词", "助词", "数词"):
                if tokens[j]["text"] in ("は", "が", "を", "に", "で", "と", "へ", "から", "まで", "より", "の"):
                    j += 1
                else:
                    break
            chunks.append({"label": "名词短语", "role": "", "text": "".join(t["text"] for t in tokens[i:j])})
            i = j
            continue
        if pos in ("动词", "形容词", "形容动词", "助动词"):
            j = i + 1
            while j < len(tokens) and tokens[j]["pos"] in ("动词", "形容词", "形容动词", "助动词", "助词"):
                j += 1
            chunks.append({"label": "谓语", "role": "", "text": "".join(t["text"] for t in tokens[i:j])})
            i = j
            continue
        chunks.append({"label": pos, "role": "", "text": tokens[i]["text"]})
        i += 1
    return chunks


def _ja_features(text: str, tokens: list[dict]) -> list[dict]:
    found = []

    def add(key):
        if key in FEATURES["ja"] and key not in {f["key"] for f in found}:
            found.append({"key": key, **FEATURES["ja"][key]})

    for i, token in enumerate(tokens):
        surface = token["text"]
        prev = tokens[i - 1] if i else None
        if surface in ("て", "で") and prev and prev["pos"] in ("动词", "形容词", "形容动词"):
            add("te")
        if surface in ("た", "だ") and token["pos"] == "助动词" and prev and prev["pos"] in ("动词", "形容词", "形容动词"):
            add("ta")
        if surface in ("ない", "ません"):
            add("nai")
        if surface in ("れる", "られる"):
            add("passive")
        if surface in ("せる", "させる"):
            add("causative")
        if surface in ("う", "よう") and token["pos"] == "助动词":
            add("volitional")
        if surface in ("ば", "たら", "なら"):
            add("conditional")
        if surface == "と" and prev and prev["pos"] in ("动词", "形容词"):
            add("conditional")
        if surface in ("です", "ます"):
            add("polite")
        if surface == "は":
            add("particle_wa")
        if surface == "が":
            add("particle_ga")
        if surface == "を":
            add("particle_wo")
        if surface == "に":
            add("particle_ni")
        if surface == "で":
            add("particle_de")
        if surface == "の":
            add("particle_no")
    if any(x in text for x in ("できる", "れる", "られる")):
        add("potential")
    if any(x in text for x in ("あげる", "くれる", "もらう")):
        add("giving")
    if any(x in text for x in ("いただ", "くださ", "ござい")):
        add("polite")
    # Relative clause: noun + の + noun, or a verb directly before a noun.
    for i, token in enumerate(tokens[:-1]):
        if token["pos"] == "名词" and tokens[i + 1]["text"] == "の" and i + 2 < len(tokens) and tokens[i + 2]["pos"] == "名词":
            add("relative")
            break
    return found


def _assign_roles_ja(chunks: list[dict]) -> dict:
    subject = predicate = obj = topic = ""
    for chunk in chunks:
        if "は" in chunk["text"] and not topic:
            topic = chunk["text"]
            chunk["role"] = chunk["role"] or "主题"
        if "が" in chunk["text"] and not subject:
            subject = chunk["text"]
            chunk["role"] = chunk["role"] or "主语"
        if "を" in chunk["text"] and not obj:
            obj = chunk["text"]
            chunk["role"] = chunk["role"] or "宾语"
        if not predicate and chunk["label"] in ("谓语", "动词短语"):
            predicate = chunk["text"]
            chunk["role"] = chunk["role"] or "谓语"
    if not predicate:
        # Japanese often ends with a verbal noun or a noun predicate; use the
        # final content chunk as the predicate so the skeleton is still useful.
        for chunk in reversed(chunks):
            text = chunk["text"].strip("。！？!?、 ")
            if text and chunk["label"] not in ("连接", "标点"):
                predicate = text
                chunk["role"] = chunk["role"] or "谓语"
                break
    return {"subject": subject, "topic": topic, "predicate": predicate, "object": obj, "adverbial": ""}


def _analyze_ja(text: str) -> dict:
    tokens = _ja_tokens(text)
    chunks = _ja_chunks(tokens)
    return {"tokens": tokens, "chunks": chunks, "skeleton": _assign_roles_ja(chunks), "features": _ja_features(text, tokens)}


# ---------------------------------------------------------------- article level
def _sentences_for_block(block: dict) -> list[dict]:
    source_sents = split_sentences(block.get("source") or "")
    target_sents = split_sentences(block.get("target") or "")
    out = []
    for index, sentence in enumerate(source_sents):
        translation = target_sents[index] if len(target_sents) == len(source_sents) else (block.get("target") or "")
        out.append({"text": sentence, "translation": translation})
    return out


def _analyze_grammar_only(article: dict, lang: str) -> dict:
    """Fallback for the other 21 atlas languages.

    Token/POS breakdown is only implemented for English, Chinese and Japanese.
    For every other language we still return the rule-based grammar radar from
    ``core.grammar`` so the article page is never mislabelled as English.
    """
    from .grammar import analyze as grammar_analyze

    blocks = (article.get("target") or {}).get("blocks") or []
    source_text = "\n".join((block.get("source") or "") for block in blocks).strip()
    if not source_text:
        source_text = (article.get("source") or {}).get("text", "")
    sentences = []
    for block in blocks:
        if block.get("type") == "code" or not (block.get("source") or "").strip():
            continue
        for item in _sentences_for_block(block):
            sentences.append({
                "id": f"s{len(sentences) + 1}",
                "blockId": block.get("id"),
                "text": item["text"],
                "translation": item["translation"],
                "tokens": [], "chunks": [], "skeleton": {}, "features": [],
            })
    points = grammar_analyze(source_text, lang).get("points", []) if source_text else []
    by_sentence: dict[str, list[dict]] = {}
    for point in points:
        feature = {
            "key": point["id"], "title": point["title"], "category": point["category"],
            "summary": point.get("summary", ""), "detail": point["id"],
            "count": point.get("count", 0),
        }
        for occurrence in point.get("occurrences", []):
            by_sentence.setdefault(occurrence.get("sentence", "").strip(), []).append(feature)
    for sentence in sentences:
        sentence["features"] = by_sentence.get(sentence["text"].strip(), [])
    features = sorted(
        ({
            "key": point["id"], "title": point["title"], "category": point["category"],
            "summary": point.get("summary", ""), "detail": point["id"],
            "count": point.get("count", 0),
        } for point in points),
        key=lambda item: (-item["count"], item["title"]),
    )
    return {
        "language": lang,
        "languageLabel": LANGUAGES.get(lang, {}).get("name", lang),
        "mode": "grammar",
        "note": "逐句词性拆解目前支持英语、中文和日语；这门语言先展示本地语法雷达定位。",
        "sentences": sentences,
        "features": features,
        "summary": {
            "sentences": len(sentences),
            "tokens": 0,
            "featureTypes": len(features),
            "featureCount": sum(point.get("count", 0) for point in points),
            "catalogSize": 0,
        },
    }


def analyze_article(article: dict) -> dict:
    lang = (article.get("source") or {}).get("lang", "en")
    if lang in ("zh-CN", "zh-TW", "zh-cn", "zh-tw"):
        lang = "zh"
    if lang not in ("en", "zh", "ja"):
        return _analyze_grammar_only(article, lang)
    analyzer = {"en": _analyze_en, "zh": _analyze_zh, "ja": _analyze_ja}[lang]
    blocks = (article.get("target") or {}).get("blocks") or []
    sentences = []
    feature_counts: dict[str, int] = {}
    for block_index, block in enumerate(blocks):
        if block.get("type") == "code" or not (block.get("source") or "").strip():
            continue
        for item in _sentences_for_block(block):
            detail = analyzer(item["text"])
            for feature in detail["features"]:
                feature_counts[feature["key"]] = feature_counts.get(feature["key"], 0) + 1
            sentences.append({
                "id": f"s{len(sentences) + 1}",
                "blockId": block.get("id"),
                "text": item["text"],
                "translation": item["translation"],
                "tokens": detail["tokens"],
                "chunks": detail["chunks"],
                "skeleton": detail["skeleton"],
                "features": detail["features"],
            })
    catalog = FEATURES.get(lang, {})
    features = []
    for key, count in sorted(feature_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        info = catalog.get(key)
        if info:
            features.append({"key": key, "count": count, **info})
    return {
        "language": lang,
        "languageLabel": {"en": "英语", "zh": "中文", "ja": "日语"}[lang],
        "mode": "rule",
        "sentences": sentences,
        "features": features,
        "summary": {
            "sentences": len(sentences),
            "tokens": sum(len(s["tokens"]) for s in sentences),
            "featureTypes": len(features),
            "featureCount": sum(feature_counts.values()),
            "catalogSize": len(catalog),
        },
    }

