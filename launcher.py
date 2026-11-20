"""Portable desktop launcher for the signed-Python build.

Starts the local service in the background, opens the UI in the default browser,
and waits until the UI asks the service to quit (Settings -> 退出语镜).
No console window is shown when launched with pythonw.exe.
"""
from __future__ import annotations

import ctypes
import json
import logging
import os
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

os.environ["LINGUALENS_DESKTOP"] = "1"

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core import paths, store  # noqa: E402
import server as app_server  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402

APP_TITLE = "语镜 LinguaLens"


def _log_stream():
    log_dir = paths.logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    stream = open(log_dir / "app.log", "a", encoding="utf-8", buffering=1)
    sys.stdout = stream
    sys.stderr = stream
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(stream)],
        force=True,
    )


def _message(text: str, error: bool = False) -> None:
    try:
        flags = 0x10 if error else 0x40
        ctypes.windll.user32.MessageBoxW(0, text, APP_TITLE, flags)
    except Exception:
        pass


def _url_file() -> Path:
    return paths.data_dir() / "server.url"


def _existing_url() -> str | None:
    for candidate in (_url_file(), paths.instance_file()):
        try:
            if candidate.suffix == ".json":
                url = json.loads(candidate.read_text(encoding="utf-8")).get("url")
            else:
                url = candidate.read_text(encoding="utf-8").strip()
        except Exception:
            continue
        if not url:
            continue
        try:
            with urllib.request.urlopen(url.rstrip("/") + "/api/health", timeout=1.5) as response:
                if response.status == 200:
                    return url.rstrip("/")
        except Exception:
            continue
    return None


def _write_url(url: str) -> None:
    _url_file().write_text(url, encoding="utf-8")
    paths.instance_file().write_text(
        json.dumps({"url": url, "pid": os.getpid(), "mode": "portable"}, ensure_ascii=False),
        encoding="utf-8",
    )


def _cleanup_files() -> None:
    for path in (_url_file(), paths.instance_file()):
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass


def _open_browser(url: str) -> bool:
    """Open the app in a real browser window.

    webbrowser.open() depends on the default-browser association and can fail
    silently on some Windows profiles, so try Edge/Chrome explicitly first.
    """
    local = Path(os.environ.get("LOCALAPPDATA", ""))
    candidates = [
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Microsoft/Edge/Application/msedge.exe",
        local / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Google/Chrome/Application/chrome.exe",
        local / "Google/Chrome/Application/chrome.exe",
    ]
    for browser in candidates:
        if browser.exists():
            try:
                subprocess.Popen([str(browser), url], close_fds=True)
                logging.info("Opened browser: %s", browser)
                return True
            except Exception:
                logging.exception("Browser launch failed: %s", browser)
    try:
        if os.name == "nt":
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            webbrowser.open(url)
        logging.info("Opened browser via shell association")
        return True
    except Exception:
        logging.exception("Shell open failed")
    return False


def main() -> None:
    _log_stream()
    logging.info("Portable launcher starting; packaged=%s; root=%s", paths.is_packaged(), paths.resource_root())
    existing = _existing_url()
    if existing:
        logging.info("Existing instance found: %s", existing)
        if not _open_browser(existing):
            _message("语镜已经在运行，但没能打开浏览器。\n\n请手动访问：\n" + existing, error=True)
        return

    _cleanup_files()
    httpd = None
    try:
        store.init()
        port = app_server.free_port(8765)
        httpd = ThreadingHTTPServer(("127.0.0.1", port), app_server.Handler)
        httpd.daemon_threads = True
        event = threading.Event()
        app_server.QUIT_EVENT = event
        thread = threading.Thread(target=httpd.serve_forever, name="lingualens-http", daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{port}"
        _write_url(url)
        logging.info("Service ready: %s", url)
        if not _open_browser(url):
            _message("语镜服务已启动，但没能自动打开浏览器。\n\n请手动访问：\n" + url, error=True)
        event.wait()
        logging.info("Quit requested by UI")
    except Exception:
        logging.exception("Launcher failed")
        _message("语镜启动失败。\n\n请查看：" + str(paths.logs_dir() / "app.log"), error=True)
    finally:
        if httpd is not None:
            try:
                httpd.shutdown()
                httpd.server_close()
            except Exception:
                pass
        _cleanup_files()
        logging.info("Portable launcher stopped")


if __name__ == "__main__":
    main()
