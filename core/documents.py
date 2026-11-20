"""Document extraction for the formats an article usually arrives in.

Pure-stdlib for Office/EPUB containers; PDF uses pypdf when available and
falls back to a conservative stream decoder.
"""
from __future__ import annotations

import csv
import gzip
import io
import ipaddress
import os
import re
import socket
import urllib.parse
import urllib.request
import zipfile
import zlib
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

from .text import extract_html, extract_subtitles, normalize_text, strip_html, title_from_text
from .net import SSL_CONTEXT

MAX_BYTES = 48 * 1024 * 1024
SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".html", ".htm", ".docx", ".pdf", ".epub",
    ".srt", ".vtt", ".pptx", ".xlsx", ".rtf", ".csv",
}
FORMAT_LABELS = {
    ".txt": "纯文本", ".md": "Markdown", ".markdown": "Markdown",
    ".html": "网页", ".htm": "网页", ".docx": "Word", ".pdf": "PDF",
    ".epub": "电子书", ".srt": "字幕", ".vtt": "字幕", ".pptx": "演示文稿",
    ".xlsx": "表格", ".rtf": "富文本", ".csv": "CSV",
}

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _decode(data: bytes, filename: str = "") -> str:
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig", "replace")
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", "replace")
    for enc in ("utf-8", "gb18030", "big5", "shift_jis", "euc-jp", "euc-kr", "latin-1"):
        try:
            text = data.decode(enc)
            if enc == "latin-1" or _plausible(text):
                return text
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


def _plausible(text: str) -> bool:
    if not text:
        return True
    bad = sum(1 for c in text[:5000] if c == "\ufffd")
    return bad / max(1, min(len(text), 5000)) < 0.01


def _docx_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    paragraphs = []
    for p in root.iter(_W + "p"):
        style = p.find(f"./{_W}pPr/{_W}pStyle")
        prefix = ""
        if style is not None:
            val = (style.get(_W + "val") or "").lower()
            m = re.search(r"heading\s*([1-6])", val)
            if m:
                prefix = "#" * int(m.group(1)) + " "
            elif "title" in val:
                prefix = "# "
        chunks = []
        for node in p.iter():
            if node.tag == _W + "t" and node.text:
                chunks.append(node.text)
            elif node.tag == _W + "tab":
                chunks.append("\t")
            elif node.tag in (_W + "br", _W + "cr"):
                chunks.append("\n")
        line = "".join(chunks).strip()
        if line:
            paragraphs.append(prefix + line)
    return "\n\n".join(paragraphs)


def _pptx_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        slides = sorted(
            [n for n in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)],
            key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[-1]).group(1)),
        )
        out = []
        for i, name in enumerate(slides, 1):
            root = ET.fromstring(zf.read(name))
            texts = [node.text.strip() for node in root.iter(_A + "t") if node.text and node.text.strip()]
            if texts:
                # The first text run is usually the slide title; use it as the heading.
                title = texts[0]
                body = "\n\n".join(texts[1:])
                out.append(f"## {title}" + (f"\n\n{body}" if body else ""))
        return "\n\n".join(out)


def _xlsx_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        shared = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.iter(_S + "si"):
                shared.append("".join(t.text or "" for t in si.iter(_S + "t")))
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        names = [s.get("name") or f"Sheet{i}" for i, s in enumerate(workbook.iter(_S + "sheet"), 1)]
        out = []
        sheet_files = sorted(
            [n for n in zf.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n)],
            key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[-1]).group(1)),
        )
        for idx, name in enumerate(sheet_files):
            root = ET.fromstring(zf.read(name))
            rows_out = []
            for row in root.iter(_S + "row"):
                cells = []
                for c in row.iter(_S + "c"):
                    t = c.get("t")
                    val = ""
                    if t == "inlineStr":
                        val = "".join(x.text or "" for x in c.iter(_S + "t"))
                    else:
                        v = c.find(_S + "v")
                        val = v.text or "" if v is not None else ""
                        if t == "s" and val.isdigit():
                            idx_s = int(val)
                            val = shared[idx_s] if idx_s < len(shared) else val
                    if val.strip():
                        cells.append(val.strip())
                if cells:
                    rows_out.append(" ｜ ".join(cells))
            if rows_out:
                label = names[idx] if idx < len(names) else f"Sheet{idx + 1}"
                out.append(f"## {label}\n\n" + "\n\n".join(rows_out))
        return "\n\n".join(out)


def _epub_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = [n for n in zf.namelist() if re.search(r"\.x?html?$", n, re.I)]
        names.sort(key=lambda n: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", n)])
        chapters = []
        for name in names:
            try:
                html = _decode(zf.read(name), name)
                result = extract_html(html)
                text = result["text"]
                if len(re.sub(r"\s", "", text)) < 30:
                    continue
                if result.get("title") and not text.lstrip().startswith("#"):
                    text = f"## {result['title']}\n\n{text}"
                chapters.append(text)
            except Exception:
                continue
        return "\n\n".join(chapters)


def _pdf_text(data: bytes) -> tuple[str, int]:
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                pages.append("")
        text = "\n\n".join(p.strip() for p in pages if p.strip())
        return _pdf_reflow(text), len(pages)
    except ImportError:
        pass
    except Exception:
        pass
    return _pdf_fallback(data), 0


def _pdf_fallback(data: bytes) -> str:
    """Last-resort text extraction from uncompressed/Flate streams."""
    chunks = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        raw = m.group(1)
        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            continue
        if b"BT" not in raw:
            continue
        strings = re.findall(rb"\((?:\\.|[^\\()])*\)", raw)
        line = []
        for s in strings:
            body = s[1:-1]
            body = re.sub(rb"\\([nrtbf()\\])", lambda x: {b"n": b"\n", b"r": b"\n", b"t": b"\t"}.get(x.group(1), x.group(1)), body)
            try:
                line.append(body.decode("utf-8"))
            except UnicodeDecodeError:
                line.append(body.decode("latin-1", "replace"))
        if line:
            chunks.append(" ".join(line))
    return _pdf_reflow("\n\n".join(chunks))


def _pdf_reflow(text: str) -> str:
    # Join PDF hard-wrapped lines into paragraphs; retain headings and blanks.
    lines = [ln.strip() for ln in text.replace("\r", "\n").split("\n")]
    out, buf = [], []
    for idx, s in enumerate(lines):
        if not s:
            if buf:
                out.append(" ".join(buf))
                buf = []
            continue
        nxt = lines[idx + 1] if idx + 1 < len(lines) else ""
        heading_like = (
            len(s) <= 70 and not buf
            and not re.search(r"[。．.!?！？:：;；,，]$", s)
            and bool(nxt) and (nxt[:1].isupper() or re.match(r"^[一二三四五六七八九十第]", nxt))
        )
        if heading_like:
            out.append(s)
            continue
        if re.search(r"[。．.!?！？:：]$", s) or len(s) < 4:
            buf.append(s)
            out.append(" ".join(buf))
            buf = []
        else:
            buf.append(s)
    if buf:
        out.append(" ".join(buf))
    return normalize_text("\n\n".join(out))


def _csv_text(data: bytes) -> str:
    text = _decode(data)
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except Exception:
        return text
    lines = []
    for row in rows[:5000]:
        cells = [c.strip() for c in row if c.strip()]
        if cells:
            lines.append(" ｜ ".join(cells))
    return "\n\n".join(lines)


def _rtf_text(data: bytes) -> str:
    text = data.decode("latin-1", "replace")
    text = re.sub(r"\\'([0-9a-f]{2})", lambda m: bytes([int(m.group(1), 16)]).decode("cp1252", "replace"), text)
    text = re.sub(r"\\u(-?\d+)\??", lambda m: chr(int(m.group(1)) % 65536), text)
    text = re.sub(r"\\par[d]?\b", "\n\n", text)
    text = re.sub(r"\\[a-z]+-?\d* ?", "", text)
    text = text.replace("{", "").replace("}", "").replace("\\", "")
    return normalize_text(text)


def extract_bytes(filename: str, data: bytes) -> dict:
    if not data:
        raise ValueError("文件是空的")
    if len(data) > MAX_BYTES:
        raise ValueError("文件超过 48MB 限制")
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"暂不支持 {ext or '未知'} 格式，可用格式：{', '.join(sorted(SUPPORTED_EXTENSIONS))}")
    if ext == ".pdf":
        text, pages = _pdf_text(data)
        meta = {"pages": pages}
    elif ext == ".docx":
        text, meta = _docx_text(data), {}
    elif ext == ".pptx":
        text, meta = _pptx_text(data), {}
    elif ext == ".xlsx":
        text, meta = _xlsx_text(data), {}
    elif ext == ".epub":
        text, meta = _epub_text(data), {}
    elif ext in (".html", ".htm"):
        html = _decode(data, filename)
        result = extract_html(html)
        text, meta = result["text"], {"html_title": result.get("title", "")}
    elif ext in (".srt", ".vtt"):
        text, meta = extract_subtitles(_decode(data, filename)), {}
    elif ext == ".csv":
        text, meta = _csv_text(data), {}
    elif ext == ".rtf":
        text, meta = _rtf_text(data), {}
    else:
        text, meta = _decode(data, filename), {}
    text = normalize_text(text)
    if not text:
        raise ValueError("没有从文件中提取到文字（可能是扫描版 PDF，请先 OCR）")
    meta.update({"format": ext.lstrip("."), "formatLabel": FORMAT_LABELS.get(ext, ext), "bytes": len(data)})
    return {"text": text, "title": title_from_text(text, Path(filename).stem), "meta": meta}


def read_document(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"文件不存在：{path}")
    data = path.read_bytes()
    result = extract_bytes(path.name, data)
    result["meta"]["filename"] = path.name
    return result


def scan_folder(folder: str | Path, exclude: list[Path] | None = None) -> list[dict]:
    folder = Path(folder).expanduser()
    if not folder.exists():
        raise ValueError(f"文件夹不存在：{folder}")
    if folder.is_file():
        if folder.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError("这个文件格式暂不支持")
        return [{"path": str(folder), "relative": folder.name, "size": folder.stat().st_size,
                 "format": folder.suffix.lower().lstrip(".")}]
    excluded = {p.resolve() for p in (exclude or [])}
    found = []
    for root, dirs, files in os.walk(folder):
        root_path = Path(root)
        dirs[:] = sorted(
            d for d in dirs
            if not d.startswith(".") and d not in {"node_modules", "__pycache__", "语镜译文"}
            and (root_path / d).resolve() not in excluded
        )
        for name in sorted(files):
            p = root_path / name
            if p.suffix.lower() not in SUPPORTED_EXTENSIONS or name.startswith("~$"):
                continue
            try:
                if any(part.startswith(".") for part in p.relative_to(folder).parts):
                    continue
                found.append({
                    "path": str(p),
                    "relative": str(p.relative_to(folder)).replace("\\", "/"),
                    "size": p.stat().st_size,
                    "format": p.suffix.lower().lstrip("."),
                    "label": FORMAT_LABELS.get(p.suffix.lower(), p.suffix),
                })
            except OSError:
                continue
    return found


# ---------------------------------------------------------------------------
# URL import
# ---------------------------------------------------------------------------

def _assert_public_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("只支持 http/https 网页链接")
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        raise ValueError("无法解析该网址")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("出于安全考虑，不能抓取内网地址")


def fetch_url(url: str, timeout: int = 25) -> dict:
    _assert_public_url(url)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/138.0 Safari/537.36 LinguaLens/1.0",
        "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7",
        "Accept-Encoding": "gzip",
    })
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as response:
        data = response.read(6 * 1024 * 1024)
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            data = gzip.decompress(data)
        content_type = response.headers.get("Content-Type", "")
        charset = response.headers.get_content_charset() or ""
        final_url = response.geturl()
    if "application/pdf" in content_type or final_url.lower().endswith(".pdf"):
        text, pages = _pdf_text(data)
        if not text:
            raise ValueError("这个 PDF 没有可提取文字，可能是扫描件")
        return {"text": text, "title": title_from_text(text, "PDF 文章"), "meta": {"format": "pdf", "pages": pages, "url": final_url}}
    if "text/plain" in content_type:
        text = _decode(data)
        return {"text": normalize_text(text), "title": title_from_text(text, "网页文章"), "meta": {"format": "txt", "url": final_url}}
    if not charset:
        m = re.search(rb"<meta[^>]+charset=[\"']?([\w-]+)", data[:4096], re.I)
        charset = m.group(1).decode("ascii", "ignore") if m else "utf-8"
    try:
        html = data.decode(charset, "replace")
    except LookupError:
        html = _decode(data)
    result = extract_html(html)
    if not result["text"].strip():
        result["text"] = strip_html(html)
    return {
        "text": result["text"],
        "title": result.get("title") or title_from_text(result["text"], "网页文章"),
        "meta": {"format": "html", "url": final_url},
    }
