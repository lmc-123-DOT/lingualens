"""Recursive folder translation jobs with progress and bilingual exports."""
from __future__ import annotations

import io
import re
import threading
import time
import uuid
import zipfile
from pathlib import Path

from . import store
from .documents import FORMAT_LABELS, extract_bytes, scan_folder
from .grammar import analyze
from .text import LANGUAGES, blocks_to_text, count_stats, detect_language, split_blocks, title_from_text
from .translate import PROVIDER_LABELS, translate_blocks

_jobs: dict[str, dict] = {}
_events: dict[str, threading.Event] = {}
_lock = threading.Lock()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _target_suffix(target: str) -> str:
    return {"zh-CN": "zh", "zh-TW": "zh-TW", "en": "en", "ja": "ja", "ko": "ko",
            "fr": "fr", "de": "de", "es": "es", "ru": "ru"}.get(target, target.replace("-", "_"))


def scan(folder: str, output_name: str = "语镜译文") -> dict:
    folder_path = Path(folder).expanduser()
    output = (folder_path.parent if folder_path.is_file() else folder_path) / output_name
    files = scan_folder(folder_path, exclude=[output])
    total_bytes = sum(f["size"] for f in files)
    return {
        "folder": str(folder_path),
        "outputDir": str(output),
        "files": files,
        "count": len(files),
        "totalBytes": total_bytes,
        "formats": sorted({f["format"] for f in files}),
    }


def start(folder: str, target: str, provider: str, base_url: str = "", settings: dict | None = None) -> dict:
    if target not in LANGUAGES or target in ("auto", "unknown"):
        raise ValueError("目标语言无效")
    settings = settings or store.get_settings(include_secret=True)
    scanned = scan(folder, settings.get("batchOutput", "语镜译文"))
    if not scanned["files"]:
        raise ValueError("这个文件夹里没有找到支持的文档")
    job_id = uuid.uuid4().hex[:10]
    job = {
        "id": job_id, "status": "queued", "createdAt": _now(), "updatedAt": _now(),
        "folder": scanned["folder"], "outputDir": scanned["outputDir"],
        "target": target, "targetLabel": LANGUAGES[target]["name"],
        "provider": provider, "providerLabel": PROVIDER_LABELS.get(provider, provider),
        "baseUrl": base_url, "total": len(scanned["files"]), "done": 0, "failed": 0,
        "bytes": scanned["totalBytes"], "current": "", "files": [
            {**f, "status": "pending", "output": None, "error": None}
            for f in scanned["files"]
        ], "warnings": [],
    }
    store.save_batch(job)
    event = threading.Event()
    with _lock:
        _jobs[job_id] = job
        _events[job_id] = event
    thread = threading.Thread(target=_run, args=(job, event, settings), daemon=True, name=f"batch-{job_id}")
    thread.start()
    return job


def get(job_id: str) -> dict | None:
    with _lock:
        if job_id in _jobs:
            return _jobs[job_id]
    return store.get_batch(job_id)


def cancel(job_id: str) -> bool:
    with _lock:
        event = _events.get(job_id)
        job = _jobs.get(job_id)
    if not event or not job:
        return False
    event.set()
    job["status"] = "cancelling"
    job["updatedAt"] = _now()
    store.save_batch(job)
    return True


def _run(job: dict, event: threading.Event, settings: dict) -> None:
    job["status"] = "running"
    job["updatedAt"] = _now()
    store.save_batch(job)
    out_root = Path(job["outputDir"])
    out_root.mkdir(parents=True, exist_ok=True)
    used_outputs: set[str] = set()
    for file_info in job["files"]:
        if event.is_set():
            job["status"] = "cancelled"
            job["updatedAt"] = _now()
            store.save_batch(job)
            return
        file_info["status"] = "running"
        job["current"] = file_info["relative"]
        job["updatedAt"] = _now()
        store.save_batch(job)
        try:
            path = Path(file_info["path"])
            data = path.read_bytes()
            doc = extract_bytes(path.name, data)
            text = doc["text"]
            source = detect_language(text)["code"]
            if source == "unknown":
                source = "en"
            blocks = split_blocks(text)
            result = translate_blocks(blocks, source, job["target"], job["provider"], settings)
            translated_text = blocks_to_text(blocks, {str(k): v for k, v in result["translations"].items()})
            grammar = analyze(text, source)
            rel = Path(file_info["relative"])
            out_path = (out_root / rel).with_suffix(f".{_target_suffix(job['target'])}.md")
            if str(out_path.resolve()).lower() in used_outputs:
                # Two source formats can share a stem (essay.docx / essay.pdf).
                out_path = out_path.with_name(f"{rel.stem}.{file_info.get('format', 'file')}.{_target_suffix(job['target'])}.md")
                n = 2
                while str(out_path.resolve()).lower() in used_outputs:
                    out_path = out_path.with_name(f"{rel.stem}.{file_info.get('format', 'file')}-{n}.{_target_suffix(job['target'])}.md")
                    n += 1
            used_outputs.add(str(out_path.resolve()).lower())
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(_render_markdown(
                title=doc.get("title") or title_from_text(text, path.stem),
                source=source, target=job["target"], provider=result.get("provider", job["provider"]),
                source_text=text, translated_text=translated_text, blocks=blocks,
                translations={str(k): v for k, v in result["translations"].items()},
                grammar=grammar, base_url=job.get("baseUrl", ""), meta=doc.get("meta", {}),
            ), encoding="utf-8")
            file_info.update({
                "status": "done", "output": str(out_path), "sourceLang": source,
                "sourceLangLabel": LANGUAGES.get(source, {}).get("name", source),
                "chars": count_stats(text)["chars"], "grammarCount": grammar["summary"]["total"],
                "provider": result.get("provider"), "warnings": result.get("warnings", []),
            })
            if result.get("warnings"):
                for warning in result["warnings"][:2]:
                    if warning not in job["warnings"]:
                        job["warnings"].append(warning)
            job["done"] += 1
        except Exception as exc:
            file_info["status"] = "failed"
            file_info["error"] = str(exc)[:300]
            job["failed"] += 1
        job["updatedAt"] = _now()
        store.save_batch(job)
    job["status"] = "completed" if job["failed"] == 0 else "completed_with_errors"
    job["current"] = ""
    job["finishedAt"] = _now()
    job["updatedAt"] = _now()
    store.save_batch(job)


def _render_markdown(title, source, target, provider, source_text, translated_text,
                     blocks, translations, grammar, base_url, meta) -> str:
    src_name = LANGUAGES.get(source, {}).get("name", source)
    tgt_name = LANGUAGES.get(target, {}).get("name", target)
    stats = count_stats(source_text)
    lines = [
        f"# {title}",
        "",
        f"> 原文：{src_name} ｜ 译文：{tgt_name} ｜ 引擎：{PROVIDER_LABELS.get(provider, provider)} ｜ "
        f"{stats['chars']} 字 ｜ {grammar['summary']['total']} 个语法点",
        "",
        "## 译文",
        "",
        translated_text,
        "",
        "---",
        "",
        "## 原文",
        "",
        source_text,
    ]
    if grammar["points"]:
        lines.extend(["", "---", "", "## 语法索引", ""])
        for p in grammar["points"]:
            url = f"{base_url.rstrip('/')}/grammar/{p['id']}" if base_url else f"/grammar/{p['id']}"
            lines.append(f"- **[{p['title']} · {p['english']}]({url})**（{p['category']}，{p['cefr']}，{p['count']} 处）")
            lines.append(f"  - {p['summary']}")
            if p.get("occurrences"):
                sentence = p["occurrences"][0]["sentence"].replace("\n", " ")
                lines.append(f"  - 文中例句：{sentence}")
    if meta:
        lines.extend(["", "---", "", f"*源文件格式：{meta.get('formatLabel', meta.get('format', ''))}*", ""])
    return "\n".join(lines).strip() + "\n"


def make_zip(job_id: str) -> tuple[bytes, str]:
    job = get(job_id)
    if not job:
        raise ValueError("任务不存在")
    out_root = Path(job["outputDir"])
    if not out_root.exists():
        raise ValueError("输出文件夹还不存在")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        job_outputs = [Path(f["output"]) for f in job.get("files", []) if f.get("output") and Path(f["output"]).is_file()]
        if job_outputs:
            for path in job_outputs:
                try:
                    zf.write(path, path.relative_to(out_root))
                except ValueError:
                    zf.write(path, path.name)
        else:
            for path in out_root.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(out_root))
    filename = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", Path(job["folder"]).name)[:40] or "语镜译文"
    return buffer.getvalue(), f"{filename}-{job_id}.zip"
