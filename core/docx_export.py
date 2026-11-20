"""Minimal, dependency-free Word (.docx) writer.

The app already keeps a block model for every article. This module turns that
model into a valid OOXML package without python-docx, so the portable runtime
stays small.
"""
from __future__ import annotations

import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _clean(text: str) -> str:
    return escape(_CONTROL.sub("", str(text or "")))


def _run(text: str) -> str:
    parts = []
    for i, line in enumerate(str(text or "").split("\n")):
        if i:
            parts.append("<w:r><w:br/></w:r>")
        parts.append(f'<w:r><w:t xml:space="preserve">{_clean(line)}</w:t></w:r>')
    return "".join(parts)


def _para(text: str, style: str | None = None, bold: bool = False) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    if bold and not style:
        ppr = '<w:pPr><w:rPr><w:b/></w:rPr></w:pPr>'
    return f"<w:p>{ppr}{_run(text)}</w:p>"


def _page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def build_package(title: str, lines: list[tuple[str, str]]) -> bytes:
    """lines: (kind, text), kind in title/heading/heading2/quote/body/list."""
    body = []
    for kind, text in lines:
        if kind == "title":
            body.append(_para(text, "Title"))
        elif kind == "heading":
            body.append(_para(text, "Heading1"))
        elif kind == "heading2":
            body.append(_para(text, "Heading2"))
        elif kind == "quote":
            body.append(_para(text, "Quote"))
        elif kind == "list":
            body.append(_para(text, "ListParagraph"))
        elif kind == "pagebreak":
            body.append(_page_break())
        else:
            body.append(_para(text))
    sect = (
        "<w:sectPr><w:pgSz w:w=\"11906\" w:h=\"16838\"/>"
        "<w:pgMar w:top=\"1440\" w:right=\"1440\" w:bottom=\"1440\" w:left=\"1440\" "
        "w:header=\"708\" w:footer=\"708\" w:gutter=\"0\"/></w:sectPr>"
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:document {W} {R}><w:body>{''.join(body)}{sect}</w:body></w:document>"
    )

    styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles {W}>
  <w:docDefaults>
    <w:rPrDefault><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos" w:eastAsia="Microsoft YaHei"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:rPrDefault>
    <w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="330" w:lineRule="auto"/></w:pPr></w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
    <w:pPr><w:spacing w:before="0" w:after="240"/><w:jc w:val="left"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Cambria" w:hAnsi="Cambria" w:eastAsia="Microsoft YaHei"/><w:b/><w:color w:val="17211C"/><w:sz w:val="48"/><w:szCs w:val="48"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="360" w:after="140"/><w:outlineLvl w:val="0"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Cambria" w:hAnsi="Cambria" w:eastAsia="Microsoft YaHei"/><w:b/><w:color w:val="146B58"/><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
    <w:pPr><w:keepNext/><w:spacing w:before="240" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr>
    <w:rPr><w:b/><w:color w:val="17211C"/><w:sz w:val="26"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:ind w:left="420" w:right="420"/><w:pBdr><w:left w:val="single" w:sz="18" w:space="12" w:color="D25B41"/></w:pBdr></w:pPr>
    <w:rPr><w:i/><w:color w:val="4E5A52"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:ind w:left="420"/></w:pPr>
  </w:style>
</w:styles>'''

    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''

    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''

    doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    core = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{_clean(title)}</dc:title><dc:creator>语镜 LinguaLens</dc:creator><cp:lastModifiedBy>语镜 LinguaLens</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>
</cp:coreProperties>'''

    app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>语镜 LinguaLens</Application>
</Properties>'''

    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document)
        zf.writestr("word/styles.xml", styles)
        zf.writestr("word/_rels/document.xml.rels", doc_rels)
        zf.writestr("docProps/core.xml", core)
        zf.writestr("docProps/app.xml", app)
    return buf.getvalue()


def article_lines(article: dict) -> list[tuple[str, str]]:
    source = article.get("source") or {}
    target = article.get("target") or {}
    grammar = article.get("grammar") or {}
    lines: list[tuple[str, str]] = [("title", article.get("title") or "未命名文章")]
    stats = source.get("stats") or {}
    lines.append(("quote", f"{source.get('label', '')} → {target.get('label', '')} ｜ {stats.get('chars', 0)} 字 ｜ {grammar.get('summary', {}).get('total', 0)} 个语法点"))
    lines.append(("heading", "译文"))
    for block in target.get("blocks") or []:
        text = block.get("target", "")
        btype = block.get("type", "paragraph")
        if not text:
            continue
        if btype == "heading":
            lines.append(("heading2", text))
        elif btype == "list":
            lines.append(("list", "• " + text))
        elif btype == "quote":
            lines.append(("quote", text))
        else:
            lines.append(("body", text))
    lines.append(("pagebreak", ""))
    lines.append(("heading", "原文"))
    for block in target.get("blocks") or []:
        text = block.get("source", "")
        btype = block.get("type", "paragraph")
        if not text:
            continue
        if btype == "heading":
            lines.append(("heading2", text))
        elif btype == "list":
            lines.append(("list", "• " + text))
        elif btype == "quote":
            lines.append(("quote", text))
        else:
            lines.append(("body", text))
    points = grammar.get("points") or []
    if points:
        lines.append(("pagebreak", ""))
        lines.append(("heading", "语法索引"))
        for point in points:
            lines.append(("heading2", f"{point.get('title')} · {point.get('english')}（{point.get('category')}，{point.get('cefr')}，{point.get('count')} 处）"))
            lines.append(("body", point.get("summary", "")))
            for occ in (point.get("occurrences") or [])[:2]:
                lines.append(("quote", occ.get("sentence", "")))
    return lines


def build_article_docx(article: dict) -> bytes:
    return build_package(article.get("title") or "语镜译文", article_lines(article))


def write_article_docx(article: dict, path: Path) -> Path:
    data = build_article_docx(article)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path
