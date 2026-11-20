"""Runtime paths for both source runs and a frozen Windows build.

Development:
    <project>/data
Frozen:
    %LOCALAPPDATA%\\LinguaLens\\data   (writable, survives upgrades)
Resources:
    sys._MEIPASS (one-file) or the executable directory (one-dir)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "LinguaLens"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    if is_frozen():
        bundle = getattr(sys, "_MEIPASS", None)
        if bundle:
            return Path(bundle)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def install_root() -> Path:
    """Return the folder that contains runtime/ and app/ for the embedded build."""
    app = resource_root()
    if (app.parent / "runtime").is_dir():
        return app.parent
    return app


def is_packaged() -> bool:
    return (install_root() / "runtime").is_dir()


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def _portable_flag() -> bool:
    if not is_frozen() and not is_packaged():
        return False
    return (install_root() / "portable.flag").exists()


def data_dir() -> Path:
    override = os.environ.get("LINGUALENS_DATA")
    if override:
        path = Path(override).expanduser()
    elif is_frozen() or is_packaged():
        if _portable_flag():
            path = install_root() / "data"
        else:
            base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
            path = base / APP_NAME / "data"
    else:
        path = resource_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    path = data_dir().parent / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def instance_file() -> Path:
    return data_dir().parent / "server.json"
