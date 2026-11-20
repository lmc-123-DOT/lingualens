"""Explain a word's in-context form: inflection, particles and before/after.

This is the "word in this article" companion to the dictionary lookup. It is
rule-based and intentionally explains the visible change instead of pretending
to be a full morphological analyzer.
"""
from __future__ import annotations

import re

EN_IRREG = {
    "went": ("go", "过去式"), "gone": ("go", "过去分词"),
    "saw": ("see", "过去式"), "seen": ("see", "过去分词"),
    "made": ("make", "过去式/过去分词"), "took": ("take", "过去式"),
    "taken": ("take", "过去分词"), "wrote": ("write", "过去式"),
    "written": ("write", "过去分词"), "read": ("read", "过去式/过去分词"),
    "said": ("say", "过去式/过去分词"), "thought": ("think", "过去式/过去分词"),
    "knew": ("know", "过去式"), "known": ("know", "过去分词"),
    "came": ("come", "过去式"), "gave": ("give", "过去式"),
    "given": ("give", "过去分词"), "found": ("find", "过去式/过去分词"),
    "felt": ("feel", "过去式/过去分词"), "left": ("leave", "过去式/过去分词"),
    "kept": ("keep", "过去式/过去分词"), "began": ("begin", "过去式"),
    "begun": ("begin", "过去分词"), "ran": ("run", "过去式"),
    "held": ("hold", "过去式/过去分词"), "brought": ("bring", "过去式/过去分词"),
    "bought": ("buy", "过去式/过去分词"), "paid": ("pay", "过去式/过去分词"),
    "met": ("meet", "过去式/过去分词"), "lost": ("lose", "过去式/过去分词"),
    "won": ("win", "过去式/过去分词"), "spoke": ("speak", "过去式"),
    "spoken": ("speak", "过去分词"), "taught": ("teach", "过去式/过去分词"),
    "built": ("build", "过去式/过去分词"), "sent": ("send", "过去式/过去分词"),
    "spent": ("spend", "过去式/过去分词"), "grew": ("grow", "过去式"),
    "grown": ("grow", "过去分词"), "fell": ("fall", "过去式"),
    "fallen": ("fall", "过去分词"), "was": ("be", "过去式"),
    "were": ("be", "过去式"), "been": ("be", "过去分词"),
    "did": ("do", "过去式"), "done": ("do", "过去分词"),
    "has": ("have", "第三人称单数"), "had": ("have", "过去式/过去分词"),
    "is": ("be", "第三人称单数"), "are": ("be", "现在式"),
    "am": ("be", "第一人称单数"),
}

FORM_EXPLAIN = {
    "过去式": "表示过去发生并结束的动作或状态。",
    "过去分词": "常与 have/has/had 构成完成时，或与 be 构成被动语态。",
    "现在分词": "常与 be 构成进行时，也可作动名词或分词状语。",
    "动名词": "把动作当作名词使用，可作主语或介词宾语。",
    "第三人称单数": "一般现在时中，主语为 he/she/it 时动词加 -s/-es。",
    "复数": "名词复数形式，表示多于一个。",
    "比较级": "用于两者比较，常与 than 连用。",
    "最高级": "用于三者及以上比较，通常前面加 the。",
}


def _en(word: str, context: str) -> dict:
    surface = word
    low = word.lower()
    tokens = re.findall(r"[A-Za-z]+(?:['’][A-Za-z]+)?", context or "")
    index = next((i for i, token in enumerate(tokens) if token.lower() == low), -1)
    prev = tokens[index - 1].lower() if index > 0 else ""
    lemma = low
    form = "原形"
    change = "词典形"
    features: list[str] = []

    if low in EN_IRREG:
        lemma, form = EN_IRREG[low]
        change = f"{lemma} → {surface}"
    elif low.endswith("ing") and len(low) > 5:
        stem = low[:-3]
        if len(stem) > 2 and stem[-1] == stem[-2]:
            stem = stem[:-1]
        if low.endswith("ying"):
            stem = low[:-4] + "y"
        elif low.endswith("aking") or low.endswith("oving") or low.endswith("iving"):
            stem = stem + "e"
        lemma = stem
        form = "现在分词/动名词"
        change = f"{lemma} + -ing → {surface}"
        features.append("进行时" if prev in ("is", "are", "was", "were", "be") else "非谓语")
    elif low.endswith("ed") and len(low) > 4:
        stem = low[:-2]
        if low.endswith("ied"):
            stem = low[:-3] + "y"
        elif len(stem) > 2 and stem[-1] == stem[-2]:
            stem = stem[:-1]
        elif low.endswith("ated") or low.endswith("oved") or low.endswith("used"):
            stem = stem
        lemma = stem
        form = "过去式/过去分词"
        change = f"{lemma} + -ed → {surface}"
        if prev in ("have", "has", "had"):
            form = "过去分词"
            features.append("完成时")
        elif prev in ("is", "are", "was", "were", "be", "been"):
            form = "过去分词"
            features.append("被动语态")
        else:
            features.append("过去")
    elif low.endswith("s") and len(low) > 3:
        stem = low[:-1]
        if low.endswith("ies"):
            stem = low[:-3] + "y"
        elif low.endswith("es"):
            stem = low[:-2]
        lemma = stem
        form = "第三人称单数/复数"
        change = f"{lemma} + -s/-es → {surface}"
        features.append("一般现在时" if prev in ("he", "she", "it", "this", "that") else "名词复数")
    elif low.endswith("er") and len(low) > 4:
        lemma = low[:-2]
        form = "比较级"
        change = f"{lemma} + -er → {surface}"
        features.append("比较")
    elif low.endswith("est") and len(low) > 5:
        lemma = low[:-3]
        form = "最高级"
        change = f"{lemma} + -est → {surface}"
        features.append("最高级")

    explain = FORM_EXPLAIN.get(form)
    if not explain:
        if "过去式" in form:
            explain = FORM_EXPLAIN["过去式"]
        elif "过去分词" in form:
            explain = FORM_EXPLAIN["过去分词"]
        elif "现在分词" in form or "动名词" in form:
            explain = FORM_EXPLAIN["现在分词"]
        elif form == "原形":
            explain = "文中就是词典形，没有额外屈折变化。"
        else:
            explain = "这是该词在本文中的形式；词典形可以帮助你定位它的基本含义。"
    return {
        "available": True, "lang": "en", "surface": surface, "lemma": lemma,
        "pos": "动词" if low not in ("is", "are", "am", "was", "were", "has", "had") and (form != "原形" or prev in ("to", "can", "will", "must")) else "词",
        "form": form, "features": features, "change": change,
        "before": {"label": "词典形", "text": lemma},
        "after": {"label": "文中形式", "text": surface},
        "explain": explain, "context": context[:240],
    }


def _ja(word: str, context: str) -> dict:
    from janome.tokenizer import Tokenizer
    tokens = list(Tokenizer().tokenize(context or ""))
    token = None
    auxiliaries: list[str] = []
    for i, candidate in enumerate(tokens):
        for span in (1, 2, 3):
            surface = "".join(t.surface for t in tokens[i:i + span])
            if surface == word:
                token = candidate
                auxiliaries = [t.surface for t in tokens[i + 1:i + span]]
                break
        if token:
            break
    if token is None:
        token = next((t for t in tokens if t.base_form == word), None)
    if not token:
        return {"available": False, "lang": "ja", "surface": word, "explain": "没有在句子里定位到这个形式。"}
    pos_full = token.part_of_speech.split(",")
    pos = pos_full[0]
    infl_type = token.infl_type or ""
    infl_form = token.infl_form or ""
    base = token.base_form or word
    if pos in ("動詞", "形容詞", "形容動詞", "助動詞"):
        form = infl_form if infl_form and infl_form != "*" else "辞书形"
        if auxiliaries:
            form = "＋".join([form] + auxiliaries)
        change = f"{base} → {word}" + (f"（{infl_type}・{form}）" if infl_type else "")
        usage = {
            "未然形": "后续ない、う/よう、れる/られる、せる/させる等。",
            "連用形": "后续ます、て、た，或用于句中连接。",
            "終止形": "放在句末结句。",
            "連体形": "放在名词前作定语。",
            "仮定形": "后续ば，表示条件。",
            "命令形": "表示命令。",
        }.get(infl_form, "这是动词/形容词在句中的活用形式。")
        if auxiliaries:
            usage += f" 这里的「{''.join(auxiliaries)}」进一步标记时态或连接。"
        explain = f"辞书形是「{base}」。{usage}"
    else:
        form = "无活用"
        change = f"{word}（{pos}）"
        explain = f"{pos}没有活形变化，在句中主要靠助词和语序确定成分。"
    return {
        "available": True, "lang": "ja", "surface": word, "lemma": base, "pos": pos,
        "form": form, "features": [x for x in (infl_type, *auxiliaries) if x and x != "*"],
        "change": change, "before": {"label": "辞书形", "text": base},
        "after": {"label": "文中形式", "text": word}, "explain": explain,
        "context": context[:240],
    }


def _zh(word: str, context: str) -> dict:
    import jieba.posseg as pseg
    tokens = [(w, flag) for w, flag in pseg.cut(context or "") if w.strip()]
    index = next((i for i, (w, _) in enumerate(tokens) if w == word), -1)
    base_word = word
    particle = ""
    if index < 0:
        for suffix in ("了", "着", "过"):
            if word.endswith(suffix) and len(word) > 1:
                base_word, particle = word[:-1], suffix
                index = next((i for i, (w, _) in enumerate(tokens) if w == base_word), -1)
                break
    pos = tokens[index][1] if index >= 0 else ""
    prev = tokens[index - 1][0] if index > 0 else ""
    nxt = tokens[index + 1][0] if 0 <= index < len(tokens) - 1 else ""
    particles = {"了": "完成/变化", "着": "持续", "过": "经历"}
    form = "原形"
    change = f"{base_word}（词形不变）"
    explain = "汉语动词本身不随人称、时态变形，靠助词和语序表达体貌。"
    after = word
    if particle:
        form = particles[particle]
        change = f"{base_word} + {particle} → {word}"
        explain = f"“{particle}”表示{particles[particle]}；词干不变，附加助词后意义发生变化。"
    elif nxt in particles:
        form = particles[nxt]
        after = base_word + nxt
        change = f"{base_word} + {nxt}"
        explain = f"“{nxt}”表示{particles[nxt]}；词干不变，附加助词后意义发生变化。"
    elif prev == "被":
        form = "被动"
        after = "被" + base_word
        change = f"被 + {base_word}"
        explain = "“被”字句从受事角度叙述，常带不如意或结果义。"
    elif prev == "把":
        form = "处置"
        after = "把" + base_word
        change = f"把 + {base_word}"
        explain = "“把”字句强调对确定对象的处置结果，动词后通常要带补语或“了”。"
    elif word in ("是", "不是", "就是", "还是"):
        form = "判断/焦点"
    return {
        "available": True, "lang": "zh", "surface": word, "lemma": base_word,
        "pos": {"v": "动词", "n": "名词", "a": "形容词", "d": "副词", "r": "代词"}.get(pos, pos or "词"),
        "form": form, "features": [form] if form != "原形" else [],
        "change": change, "before": {"label": "词干", "text": base_word},
        "after": {"label": "文中形式", "text": after}, "explain": explain,
        "context": context[:240],
    }


def explain_in_context(word: str, lang: str = "en", context: str = "") -> dict:
    word = (word or "").strip()
    if not word:
        return {"available": False}
    lang = (lang or "en").lower()
    if lang in ("zh-cn", "zh-tw"):
        lang = "zh"
    try:
        if lang == "en":
            return _en(word, context)
        if lang == "ja":
            return _ja(word, context)
        if lang == "zh":
            return _zh(word, context)
        return {"available": False, "explain": "暂时只支持英/日/中的词形分析。"}
    except Exception as exc:
        return {"available": False, "lang": lang, "surface": word, "explain": f"词形分析失败：{exc}"[:120]}
