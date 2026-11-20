"""Desktop entry point for the packaged LinguaLens application.

It starts the existing local HTTP service, then hosts the UI in a native
WebView2 window through pywebview. If WebView2 is missing, it falls back to a
small control window and the system browser.
"""
from __future__ import annotations

import ctypes
import json
import logging
import os
import sys
import tempfile
import threading
import time
import traceback
import webbrowser
from pathlib import Path

# pywebview's WinForms backend goes through pythonnet. On a packaged build the
# launcher supplies a WindowsDesktop runtimeconfig for .NET 8, which avoids the
# .NET Framework assembly-resolution path entirely.
os.environ.setdefault("PYTHONNET_RUNTIME", "netfx")

_STARTUP_LOG = Path(tempfile.gettempdir()) / "lingualens-startup.log"


def _boot(message: str) -> None:
    try:
        with open(_STARTUP_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except Exception:
        pass


_boot("desktop entry imported")
_boot(f"exe={sys.executable} frozen={getattr(sys, 'frozen', False)} localappdata={os.environ.get('LOCALAPPDATA')}")


def _excepthook(exc_type, exc, tb):
    _boot("UNHANDLED\n" + "".join(traceback.format_exception(exc_type, exc, tb)))


sys.excepthook = _excepthook

# Make imports work in source mode before core.paths is imported below.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from core import paths, store  # noqa: E402
    import server as app_server  # noqa: E402
    from http.server import ThreadingHTTPServer  # noqa: E402
except Exception:
    _boot("IMPORT FAILURE\n" + traceback.format_exc())
    raise

APP_TITLE = "语镜 LinguaLens"
MUTEX_NAME = "Local\\LinguaLens.Desktop.1"
_instances: list = []


def setup_logging() -> Path:
    """Windowed builds have no console; keep a useful local log."""
    log_path = paths.logs_dir() / "app.log"
    stream = open(log_path, "a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = stream
    if sys.stderr is None:
        sys.stderr = stream
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(stream)],
        force=True,
    )
    return log_path


def acquire_mutex():
    try:
        handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
        already = ctypes.windll.kernel32.GetLastError() == 183
        return handle, already
    except Exception:
        return None, False


def focus_existing() -> bool:
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, APP_TITLE)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            return True
    except Exception:
        pass
    # If the window title lookup fails, at least open the last known URL.
    try:
        info = json.loads(paths.instance_file().read_text(encoding="utf-8"))
        url = info.get("url")
        if url:
            webbrowser.open(url)
            return True
    except Exception:
        return False
    return False


def start_http_server():
    store.init()
    port = app_server.free_port(8765)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), app_server.Handler)
    httpd.daemon_threads = True
    thread = threading.Thread(target=httpd.serve_forever, name="lingualens-http", daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}"
    paths.instance_file().write_text(
        json.dumps({"url": url, "pid": os.getpid(), "startedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z")}, ensure_ascii=False),
        encoding="utf-8",
    )
    return httpd, url


def stop_http_server(httpd) -> None:
    try:
        httpd.shutdown()
        httpd.server_close()
    except Exception:
        pass
    try:
        paths.instance_file().unlink(missing_ok=True)
    except Exception:
        pass


def fallback_browser(url: str, httpd) -> None:
    """Used only when WebView2/pywebview cannot start."""
    import tkinter as tk
    from tkinter import messagebox

    webbrowser.open(url)
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("460x230")
    root.configure(bg="#f4efe4")
    root.resizable(False, False)
    frame = tk.Frame(root, bg="#f4efe4", padx=24, pady=20)
    frame.pack(fill="both", expand=True)
    tk.Label(frame, text="语镜 LinguaLens", bg="#f4efe4", fg="#17211c",
             font=("Microsoft YaHei", 18, "bold")).pack(anchor="w")
    tk.Label(frame, text="已在浏览器中打开。关闭此窗口即可退出语镜。", bg="#f4efe4",
             fg="#4e5a52", font=("Microsoft YaHei", 10)).pack(anchor="w", pady=(8, 14))
    tk.Label(frame, text=url, bg="#f4efe4", fg="#146b58",
             font=("Consolas", 10)).pack(anchor="w")
    row = tk.Frame(frame, bg="#f4efe4")
    row.pack(fill="x", pady=(18, 0))
    tk.Button(row, text="打开界面", command=lambda: webbrowser.open(url),
              bg="#146b58", fg="white", relief="flat", padx=14, pady=6).pack(side="left")
    tk.Button(row, text="打开数据文件夹", command=lambda: os.startfile(str(paths.data_dir())),
              relief="flat", padx=14, pady=6).pack(side="left", padx=8)

    def close():
        stop_http_server(httpd)
        root.destroy()

    tk.Button(row, text="退出", command=close, relief="flat", padx=14, pady=6).pack(side="right")
    root.protocol("WM_DELETE_WINDOW", close)
    root.mainloop()


def run() -> None:
    log_path = setup_logging()
    logging.info("LinguaLens desktop starting; frozen=%s; log=%s", paths.is_frozen(), log_path)
    mutex, already = acquire_mutex()
    if already:
        logging.info("Another instance is running")
        if not focus_existing():
            try:
                messagebox = __import__("tkinter.messagebox", fromlist=["messagebox"])
                messagebox.showinfo(APP_TITLE, "语镜已经在运行。")
            except Exception:
                pass
        return
    _instances.append(mutex)
    httpd = None
    try:
        httpd, url = start_http_server()
        logging.info("HTTP server ready: %s", url)
        try:
            runtime_config = paths.install_root() / "runtime" / "lingualens.runtimeconfig.json"
            if runtime_config.exists():
                os.environ["PYTHONNET_RUNTIME"] = "coreclr"
                os.environ["PYTHONNET_CORECLR_RUNTIME_CONFIG"] = str(runtime_config)
            import webview

            icon = paths.resource_path("web", "assets", "语镜.ico")
            window = webview.create_window(
                APP_TITLE,
                url,
                width=1440,
                height=920,
                min_size=(980, 680),
                background_color="#f4efe4",
                text_select=True,
                zoomable=True,
                confirm_close=False,
            )
            webview.start(
                debug=False,
                private_mode=False,
                storage_path=str(paths.data_dir().parent / "browser"),
                icon=str(icon) if icon.exists() else None,
            )
            logging.info("WebView window closed")
        except Exception as exc:
            logging.exception("WebView failed, falling back to browser: %s", exc)
            fallback_browser(url, httpd)
    except Exception:
        logging.exception("Fatal startup error")
        try:
            from tkinter import messagebox
            messagebox.showerror(APP_TITLE, "语镜启动失败。\n\n" + traceback.format_exc(limit=2))
        except Exception:
            pass
    finally:
        if httpd is not None:
            stop_http_server(httpd)
        try:
            if mutex:
                ctypes.windll.kernel32.CloseHandle(mutex)
        except Exception:
            pass
        logging.info("LinguaLens desktop stopped")


if __name__ == "__main__":
    run()
