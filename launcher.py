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
NO_BROWSER = "--no-browser" in sys.argv
LAN = "--lan" in sys.argv or os.environ.get("LINGUALENS_LAN", "").lower() in ("1", "true", "yes", "on")


def _arg_value(name: str, default: int) -> int:
    for index, item in enumerate(sys.argv):
        if item == name and index + 1 < len(sys.argv):
            try:
                return int(sys.argv[index + 1])
            except ValueError:
                return default
        if item.startswith(name + "="):
            try:
                return int(item.split("=", 1)[1])
            except ValueError:
                return default
    return default


PORT = _arg_value("--port", 8765)


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
    instance = _existing_instance()
    return instance[0] if instance else None


def _existing_instance() -> tuple[str, str] | None:
    """Return (url, mode) for a healthy running instance, otherwise None."""
    url = ""
    try:
        info = json.loads(paths.instance_file().read_text(encoding="utf-8"))
        url = str(info.get("url") or "")
    except Exception:
        url = ""
    if not url:
        try:
            url = _url_file().read_text(encoding="utf-8").strip()
        except Exception:
            return None
    if not url:
        return None
    url = url.rstrip("/")
    try:  # Newer builds report their bind mode here.
        with urllib.request.urlopen(url + "/api/net", timeout=1.5) as response:
            data = json.loads(response.read().decode("utf-8"))
        return url, ("lan" if data.get("lan") else "portable")
    except Exception:
        pass
    try:
        with urllib.request.urlopen(url + "/api/health", timeout=1.5) as response:
            if response.status == 200:
                return url, "portable"
    except Exception:
        return None
    return None


def _request_quit(url: str) -> None:
    try:
        request = urllib.request.Request(
            url.rstrip("/") + "/api/quit",
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(request, timeout=3).read()
    except Exception:
        logging.info("Quit request failed or instance already closing")


def _wait_down(url: str, timeout: float = 6.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url.rstrip("/") + "/api/health", timeout=0.8):
                pass
        except Exception:
            return
        time.sleep(0.25)


def _write_url(url: str, mode: str = "portable") -> None:
    _url_file().write_text(url, encoding="utf-8")
    paths.instance_file().write_text(
        json.dumps({"url": url, "pid": os.getpid(), "mode": mode}, ensure_ascii=False),
        encoding="utf-8",
    )


def _write_lan(port: int) -> list[str]:
    """Publish the phone-facing URL so the launcher script can open /mobile."""
    urls = app_server.lan_urls(port)
    mobile = f"http://127.0.0.1:{port}/mobile"
    data = {
        "urls": urls,
        "localUrl": f"http://127.0.0.1:{port}",
        "mobileUrl": mobile,
        "port": port,
        "pid": os.getpid(),
    }
    (paths.data_dir() / "lan.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    (paths.data_dir() / "lan.url").write_text(mobile, encoding="utf-8")
    return urls


def _cleanup_files() -> None:
    for path in (
        _url_file(),
        paths.instance_file(),
        paths.data_dir() / "lan.json",
        paths.data_dir() / "lan.url",
    ):
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass


def _focus_app_window() -> bool:
    """Bring the Edge/Chrome window showing LinguaLens to the foreground."""
    try:
        user32 = ctypes.windll.user32
        found: list[int] = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def callback(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value or ""
            if "语镜" in title or "LinguaLens" in title:
                found.append(int(hwnd))
            return True

        user32.EnumWindows(callback, 0)
        if not found:
            logging.info("Focus: no LinguaLens browser window found")
            return False
        hwnd = found[0]
        logging.info("Focus: found hwnd=%s", hwnd)
        user32.AllowSetForegroundWindow(-1)  # ASFW_ANY
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.BringWindowToTop(hwnd)
        user32.SwitchToThisWindow(hwnd, True)
        # Windows sometimes refuses SetForegroundWindow from a background
        # pythonw process; attach to the foreground thread to unlock it.
        try:
            foreground = user32.GetForegroundWindow()
            foreground_thread = user32.GetWindowThreadProcessId(foreground, None)
            current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
            if foreground_thread and foreground_thread != current_thread:
                user32.AttachThreadInput(current_thread, foreground_thread, True)
                user32.SetForegroundWindow(hwnd)
                user32.AttachThreadInput(current_thread, foreground_thread, False)
            else:
                user32.SetForegroundWindow(hwnd)
        except Exception:
            user32.SetForegroundWindow(hwnd)
        time.sleep(0.15)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        logging.exception("Focus window failed")
        return False


def _open_browser(url: str, size: str = "1440,920") -> bool:
    """Open the app in a real, foreground browser window.

    webbrowser.open() depends on the default-browser association and can fail
    silently on some Windows profiles, so try Edge/Chrome explicitly first.
    --new-window also avoids opening a tab behind an existing minimized window.
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
                subprocess.Popen([str(browser), f"--app={url}", f"--window-size={size}"], close_fds=True)
                logging.info("Opened browser app window: %s", browser)
                for _ in range(140):
                    time.sleep(0.25)
                    if _focus_app_window():
                        break
                return True
            except Exception:
                logging.exception("Browser launch failed: %s", browser)
    try:
        if os.name == "nt":
            os.startfile(url)  # type: ignore[attr-defined]
        else:
            webbrowser.open(url)
        logging.info("Opened browser via shell association")
        for _ in range(60):
            time.sleep(0.25)
            if _focus_app_window():
                break
        return True
    except Exception:
        logging.exception("Shell open failed")
    return False


def main() -> None:
    _log_stream()
    logging.info(
        "Portable launcher starting; lan=%s; packaged=%s; root=%s",
        LAN, paths.is_packaged(), paths.resource_root(),
    )
    existing = _existing_instance()
    if existing:
        url, mode = existing
        logging.info("Existing instance found: %s (mode=%s)", url, mode)
        if LAN and mode != "lan":
            # The phone launcher was used while a local-only instance was running:
            # stop it, then start again bound to the LAN interface.
            logging.info("Restarting local instance in LAN mode")
            _request_quit(url)
            _wait_down(url)
            try:
                _cleanup_files()
            except Exception:
                pass
        elif LAN:
            port = int(url.rsplit(":", 1)[-1])
            _write_lan(port)
            logging.info("LAN instance already running; refreshed connection page")
            return
        else:
            if not NO_BROWSER and not _open_browser(url):
                _message("语镜已经在运行，但没能打开浏览器。\n\n请手动访问：\n" + url, error=True)
            return

    _cleanup_files()
    httpd = None
    try:
        store.init()
        port = app_server.free_port(PORT)
        bind_host = "0.0.0.0" if LAN else "127.0.0.1"
        httpd = ThreadingHTTPServer((bind_host, port), app_server.Handler)
        httpd.daemon_threads = True
        event = threading.Event()
        app_server.QUIT_EVENT = event
        thread = threading.Thread(target=httpd.serve_forever, name="lingualens-http", daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{port}"
        _write_url(url, mode="portable-lan" if LAN else "portable")
        target = url
        if LAN:
            urls = _write_lan(port)
            target = f"{url}/mobile"
            logging.info("LAN ready: %s", ", ".join(urls) or "no LAN address found")
        logging.info("Service ready: %s", url)
        if not NO_BROWSER and not _open_browser(target, "980,880" if LAN else "1440,920"):
            _message("语镜服务已启动，但没能自动打开浏览器。\n\n请手动访问：\n" + target, error=True)
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
