"""Text utilities: language detection, block parsing, sentence alignment."""
from __future__ import annotations

import html as html_lib
import re
from html.parser import HTMLParser

LANGUAGES = {
    "zh-CN": {"name": "简体中文", "native": "简体中文", "short": "中"},
    "zh-TW": {"name": "繁体中文", "native": "繁體中文", "short": "繁"},
    "en": {"name": "英语", "native": "English", "short": "EN"},
    "ja": {"name": "日语", "native": "日本語", "short": "日"},
    "ko": {"name": "韩语", "native": "한국어", "short": "한"},
    "fr": {"name": "法语", "native": "Français", "short": "FR"},
    "de": {"name": "德语", "native": "Deutsch", "short": "DE"},
    "es": {"name": "西班牙语", "native": "Español", "short": "ES"},
    "pt": {"name": "葡萄牙语", "native": "Português", "short": "PT"},
    "it": {"name": "意大利语", "native": "Italiano", "short": "IT"},
    "ru": {"name": "俄语", "native": "Русский", "short": "RU"},
    "ar": {"name": "阿拉伯语", "native": "العربية", "short": "AR"},
    "vi": {"name": "越南语", "native": "Tiếng Việt", "short": "VI"},
    "th": {"name": "泰语", "native": "ไทย", "short": "TH"},
    "auto": {"name": "自动检测", "native": "Auto", "short": "A"},
    "unknown": {"name": "未知语言", "native": "Unknown", "short": "?"},
}

STOPWORDS = {
    "en": "the and of to in is that for it with as was on are be this have from or by at not you we they he she his her their an but had has were which will would can could should there what when who how all".split(),
    "fr": "le la les des une est dans pour que qui avec sur pas plus au aux ce cette il elle nous vous ils sont du en et un".split(),
    "de": "der die das und ist nicht mit für auf sich ein eine von zu den dem des im ich wir sie sind auch als aus".split(),
    "es": "el la los las de que y en un una es por con para del se al lo como más pero sus le ha".split(),
    "it": "il la gli le di che e in un una è per con del si al non sono da come anche".split(),
    "pt": "o a os as de que e em um uma é para com do da não se por ao mais como mas".split(),
    "vi": "và của là có không được trong cho một những các với này đó người".split(),
    "nl": "de het een en van is dat op te voor met niet zijn aan er ook als".split(),
}

_ACCENTS = {
    "fr": "àâçéèêëîïôûùüÿœ",
    "de": "äöüß",
    "es": "áéíóúñ¿¡",
    "pt": "ãõáéíóúâêôç",
    "it": "àèéìòù",
    "vi": "ăâđêôơưàảãáạằẳẵắặầẩẫấậèẻẽéẹềểễếệìỉĩíịòỏõóọồổỗốộờởỡớợùủũúụừửữứựỳỷỹýỵ",
}


def normalize_text(text: str) -> str:
    text = (text or "").replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def detect_language(text: str) -> dict:
    """Fast, deterministic script + stop-word language detection."""
    sample = normalize_text(text)[:30000]
    if not sample:
        return {"code": "unknown", "confidence": 0.0, **_lang("unknown")}
    letters = [c for c in sample if c.isalpha()]
    if not letters:
        return {"code": "unknown", "confidence": 0.0, **_lang("unknown")}

    def count(pred):
        return sum(1 for c in sample if pred(c))

    han = count(lambda c: "\u4e00" <= c <= "\u9fff" or "\u3400" <= c <= "\u4dbf")
    kana = count(lambda c: "\u3040" <= c <= "\u30ff" or "\uff66" <= c <= "\uff9f")
    hangul = count(lambda c: "\uac00" <= c <= "\ud7a3" or "\u1100" <= c <= "\u11ff")
    cyrillic = count(lambda c: "\u0400" <= c <= "\u04ff")
    arabic = count(lambda c: "\u0600" <= c <= "\u06ff")
    thai = count(lambda c: "\u0e00" <= c <= "\u0e7f")
    latin = count(lambda c: ("a" <= c.lower() <= "z"))

    if kana >= 2 and kana / max(han + kana, 1) > 0.015:
        return {"code": "ja", "confidence": min(0.99, 0.9 + kana / max(han + kana, 1) * 0.09), **_lang("ja")}
    if hangul >= 2:
        return {"code": "ko", "confidence": 0.98, **_lang("ko")}
    if thai >= 3:
        return {"code": "th", "confidence": 0.97, **_lang("th")}
    if arabic >= 3:
        return {"code": "ar", "confidence": 0.97, **_lang("ar")}
    if cyrillic >= 3:
        return {"code": "ru", "confidence": 0.96, **_lang("ru")}
    if han >= 3 and han >= latin * 0.4:
        return {"code": "zh-CN", "confidence": 0.95 if han > latin else 0.88, **_lang("zh-CN")}

    lower = sample.lower()
    tokens = re.findall(r"[a-zà-öø-ÿœß]+(?:['’][a-z]+)?", lower)
    if not tokens:
        return {"code": "unknown", "confidence": 0.0, **_lang("unknown")}
    token_set = set(tokens)
    scores = {}
    for code, words in STOPWORDS.items():
        lexicon = set(words)
        hits = sum(1 for w in tokens if w in lexicon)
        uniq = len(token_set & lexicon)
        scores[code] = hits / max(len(tokens), 1) + uniq * 0.012
    for code, chars in _ACCENTS.items():
        hits = sum(lower.count(ch) for ch in chars)
        if hits:
            scores[code] = scores.get(code, 0) + min(0.35, hits / max(len(tokens), 1) * 1.6)
    best = max(scores, key=scores.get)
    top = scores[best]
    second = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0
    if top < 0.018:
        return {"code": "en" if latin > 10 else "unknown", "confidence": 0.45 if latin > 10 else 0.0, **_lang("en" if latin > 10 else "unknown")}
    confidence = min(0.99, 0.55 + top * 2.1 + max(0, top - second) * 1.5)
    return {"code": best, "confidence": round(confidence, 3), **_lang(best)}


def _lang(code: str) -> dict:
    return dict(LANGUAGES.get(code, LANGUAGES["unknown"]))


def count_stats(text: str) -> dict:
    text = text or ""
    latin_words = len(re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['’\-][A-Za-zÀ-ÖØ-öø-ÿ]+)*", text))
    cjk_chars = len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7a3]", text))
    words = latin_words + cjk_chars
    sentences = len(split_sentences(text)) if text.strip() else 0
    paragraphs = len([p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()])
    chars = len(re.sub(r"\s", "", text))
    minutes = max(1, round(words / 260)) if words else 0
    return {"chars": chars, "words": words, "sentences": sentences, "paragraphs": paragraphs, "minutes": minutes}


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST = re.compile(r"^(\s*)([-*+•]|\d{1,3}[.)])\s+(.*)$")
_QUOTE = re.compile(r"^\s*>\s?(.*)$")
_FENCE = re.compile(r"^\s*(```|~~~)")


def split_blocks(text: str) -> list[dict]:
    """Split an article into translatable, renderable blocks."""
    text = normalize_text(text)
    if not text:
        return []
    lines = text.split("\n")
    blocks: list[dict] = []
    buf: list[str] = []
    buf_type = "paragraph"
    prefix = ""
    level = 0
    in_fence = False
    fence_buf: list[str] = []

    def flush():
        nonlocal buf, buf_type, prefix, level
        if buf:
            raw = "\n".join(buf).strip("\n")
            joined = _join_soft_lines(raw)
            if joined.strip():
                blocks.append({
                    "id": len(blocks) + 1,
                    "type": buf_type,
                    "text": joined,
                    "prefix": prefix,
                    "level": level,
                })
        buf = []
        buf_type = "paragraph"
        prefix = ""
        level = 0

    for line in lines:
        fence = _FENCE.match(line)
        if fence:
            if in_fence:
                fence_buf.append(line)
                blocks.append({
                    "id": len(blocks) + 1,
                    "type": "code",
                    "text": "\n".join(fence_buf),
                    "prefix": "",
                    "level": 0,
                    "translate": False,
                })
                fence_buf = []
                in_fence = False
            else:
                flush()
                in_fence = True
                fence_buf = [line]
            continue
        if in_fence:
            fence_buf.append(line)
            continue
        if not line.strip():
            flush()
            continue
        h = _HEADING.match(line)
        if h:
            flush()
            blocks.append({
                "id": len(blocks) + 1,
                "type": "heading",
                "text": h.group(2).strip(),
                "prefix": h.group(1),
                "level": len(h.group(1)),
            })
            continue
        q = _QUOTE.match(line)
        if q:
            flush()
            blocks.append({
                "id": len(blocks) + 1,
                "type": "quote",
                "text": q.group(1).strip(),
                "prefix": "> ",
                "level": 0,
            })
            continue
        li = _LIST.match(line)
        if li:
            flush()
            blocks.append({
                "id": len(blocks) + 1,
                "type": "list",
                "text": li.group(3).strip(),
                "prefix": li.group(1) + li.group(2) + " ",
                "level": 0,
            })
            continue
        # A table row is kept as a render-only block: translating cells as prose
        # damages alignment, so it is preserved in the bilingual export.
        if line.count("|") >= 2 and line.strip().startswith("|"):
            flush()
            blocks.append({
                "id": len(blocks) + 1,
                "type": "table",
                "text": line.strip(),
                "prefix": "",
                "level": 0,
                "translate": False,
            })
            continue
        if buf_type == "paragraph" and buf and _looks_like_heading_break(buf[-1], line):
            flush()
        buf.append(line)

    if in_fence and fence_buf:
        blocks.append({
            "id": len(blocks) + 1, "type": "code", "text": "\n".join(fence_buf),
            "prefix": "", "level": 0, "translate": False,
        })
    flush()
    return blocks


def _join_soft_lines(raw: str) -> str:
    lines = [ln.strip() for ln in raw.split("\n")]
    out = ""
    for ln in lines:
        if not out:
            out = ln
        elif re.search(r"[A-Za-z0-9,;:)\]]$", out) and re.match(r"[A-Za-z0-9(\[]", ln):
            out += " " + ln
        elif re.search(r"[。！？、，；：）」』】]$", out):
            out += ln
        else:
            out += " " + ln
    return re.sub(r"\s+", " ", out).strip()


def _looks_like_heading_break(prev: str, line: str) -> bool:
    if len(prev) > 90 or len(line) > 110:
        return False
    return bool(re.match(r"^(第[一二三四五六七八九十百0-9]+[章节篇]|[A-Z][A-Za-z .,'\-]{2,50}$)", line.strip()))


def render_block(block: dict, translated: str | None = None) -> str:
    text = block.get("text", "") if translated is None else translated
    btype = block.get("type", "paragraph")
    if btype == "heading":
        return ("#" * max(1, block.get("level", 2))) + " " + text
    if btype == "list":
        return block.get("prefix", "- ") + text
    if btype == "quote":
        return "> " + text.replace("\n", "\n> ")
    return text


def blocks_to_text(blocks: list[dict], translated: dict | None = None) -> str:
    parts = []
    for b in blocks:
        value = translated.get(str(b["id"]), b["text"]) if translated else b["text"]
        parts.append(render_block(b, value))
    return "\n\n".join(parts)


def split_sentences(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    # Protect common abbreviations and decimal points.
    protected = text
    replacements = {
        r"\bMr\.": "Mr<dot>", r"\bMrs\.": "Mrs<dot>", r"\bMs\.": "Ms<dot>",
        r"\bDr\.": "Dr<dot>", r"\bProf\.": "Prof<dot>", r"\bSt\.": "St<dot>",
        r"\be\.g\.": "e<dot>g<dot>", r"\bi\.e\.": "i<dot>e<dot>",
        r"\bU\.S\.": "U<dot>S<dot>", r"\bNo\.": "No<dot>", r"\bvs\.": "vs<dot>",
    }
    for pattern, repl in replacements.items():
        protected = re.sub(pattern, repl, protected, flags=re.I)
    protected = re.sub(r"(?<=\d)\.(?=\d)", "<dot>", protected)
    pieces = re.split(r"(?<=[。！？!?])\s*|(?<=[.])\s+(?=[A-Z「『\"'“”])", protected)
    out = []
    for piece in pieces:
        piece = piece.replace("<dot>", ".").strip()
        if piece:
            out.append(piece)
    return out or [text]


def chunk_text(text: str, max_chars: int = 450) -> list[str]:
    """Split text into sentence-safe chunks under max_chars."""
    text = text.strip()
    if len(text) <= max_chars:
        return [text] if text else []
    sentences = split_sentences(text)
    chunks, current = [], ""
    for sentence in sentences:
        while len(sentence) > max_chars:
            cut = sentence.rfind(" ", 0, max_chars)
            if cut < max_chars * 0.55:
                cut = max_chars
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if not sentence:
            continue
        if current and len(current) + 1 + len(sentence) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def group_blocks(blocks: list[dict], max_chars: int = 7000, max_blocks: int = 24) -> list[list[dict]]:
    groups, current, size = [], [], 0
    for block in blocks:
        if block.get("translate") is False:
            continue
        length = len(block.get("text", ""))
        if current and (size + length > max_chars or len(current) >= max_blocks):
            groups.append(current)
            current, size = [], 0
        current.append(block)
        size += length
    if current:
        groups.append(current)
    return groups


# ---------------------------------------------------------------------------
# HTML extraction
# ---------------------------------------------------------------------------

class _ArticleParser(HTMLParser):
    BLOCK_TAGS = {"p", "div", "section", "article", "main", "header", "footer", "li", "blockquote", "pre", "tr"}
    HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
    SKIP = {"script", "style", "nav", "aside", "form", "button", "svg", "noscript", "iframe", "select"}
    VOID = {"br", "img", "hr", "input", "meta", "link", "source", "area", "embed"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.pre_depth = 0
        self.title = ""
        self._in_title = False
        self._href = ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "title":
            self._in_title = True
        if tag in self.SKIP:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "br":
            self.parts.append("\n")
        elif tag == "hr":
            self.parts.append("\n\n---\n\n")
        elif tag == "pre":
            self.pre_depth += 1
            self.parts.append("\n\n```\n")
        elif tag in self.HEADINGS:
            self.parts.append("\n\n" + "#" * self.HEADINGS[tag] + " ")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag == "blockquote":
            self.parts.append("\n\n> ")
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        if tag in self.SKIP:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag == "pre":
            self.pre_depth = max(0, self.pre_depth - 1)
            self.parts.append("\n```\n\n")
        elif tag in self.HEADINGS or tag in self.BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
            return
        if self.skip_depth:
            return
        if self.pre_depth:
            self.parts.append(data)
        else:
            text = re.sub(r"\s+", " ", data)
            if text.strip():
                self.parts.append(text)


def extract_html(html_text: str) -> dict:
    parser = _ArticleParser()
    try:
        parser.feed(html_text)
    except Exception:
        pass
    raw = "".join(parser.parts)
    raw = re.sub(r"[ \t]+\n", "\n", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    text = normalize_text(raw)
    title = html_lib.unescape(parser.title).strip()
    if title:
        lines = text.split("\n", 1)
        if len(title) > 3 and (not lines or title[:18].lower() not in lines[0].lower()):
            text = f"# {title}\n\n{text}"
    return {"title": title, "text": text}


def strip_html(html_text: str) -> str:
    text = re.sub(r"(?is)<(script|style|nav|footer|svg).*?</\1>", " ", html_text or "")
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p>", "\n\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_text(html_lib.unescape(text))


# ---------------------------------------------------------------------------
# SRT / VTT
# ---------------------------------------------------------------------------

def extract_subtitles(text: str) -> str:
    text = normalize_text(text)
    lines = []
    for line in text.split("\n"):
        s = line.strip()
        if not s or s.isdigit() or "-->" in s or s.upper() == "WEBVTT":
            continue
        lines.append(s)
    return "\n\n".join(lines)


def title_from_text(text: str, fallback: str = "未命名文章") -> str:
    for block in split_blocks(text):
        if block.get("type") == "heading":
            return block["text"][:80]
    first = next((ln.strip() for ln in text.split("\n") if ln.strip()), "")
    first = re.sub(r"^[#>*\-\d.\s]+", "", first)
    if not first:
        return fallback
    # Prefer a whole first sentence over a hard character cut.
    sentence = re.match(r"^(.{4,80}?[。．.!?！？])(?:\s|$)", first)
    if sentence:
        candidate = sentence.group(1).strip()
        return candidate
    if len(first) > 64:
        cut = first[:64]
        if " " in cut[36:]:
            cut = cut[:cut.rfind(" ")]
        return cut.rstrip(" ,.;:，。；：") + "…"
    return first
