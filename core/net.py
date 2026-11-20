"""Shared HTTPS context.

Python installs on Windows often lack a CA bundle. Prefer certifi when it is
present (it is bundled in the recommended venv), otherwise use the platform
store. Never silently disable certificate verification.
"""
from __future__ import annotations

import ssl

try:
    import certifi  # type: ignore
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:  # pragma: no cover - platform dependent
    SSL_CONTEXT = ssl.create_default_context()
