"""Bundle the whole frontend into one self-contained HTML file.

The result is `web/single.html`: CSS, JS, favicon and app icon are inline. It
still talks to the existing Python backend at /api, so functionality is the
same as the split frontend. Serve it at `/` (or the SPA routes) with server.py.
"""
from __future__ import annotations

import base64
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
ASSETS = WEB / "assets"


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> None:
    html = (WEB / "index.html").read_text(encoding="utf-8")
    css = "\n\n".join([
        (ASSETS / "app.css").read_text(encoding="utf-8"),
        (ASSETS / "workbench.css").read_text(encoding="utf-8"),
    ])
    js = (ASSETS / "app.js").read_text(encoding="utf-8")

    # Inline the two stylesheets in their original order.
    html = re.sub(r'\s*<link rel="stylesheet" href="/assets/app\.css[^"]*" />', "", html)
    html = re.sub(r'\s*<link rel="stylesheet" href="/assets/workbench\.css[^"]*" />', "", html)
    html = html.replace("</head>", f"  <style>\n{css}\n  </style>\n</head>")

    # Inline icons; a single static file cannot depend on /assets.
    if (WEB / "favicon.svg").exists():
        html = html.replace('href="/favicon.svg"', f'href="{data_uri(WEB / "favicon.svg", "image/svg+xml")}"')
    if (ASSETS / "icon-192.png").exists():
        html = html.replace('href="/assets/icon-192.png"', f'href="{data_uri(ASSETS / "icon-192.png", "image/png")}"')
    html = re.sub(r'\s*<link rel="manifest" href="/manifest\.webmanifest" />', "", html)

    # A single file has no sibling sw.js; don't let a 404 register noise.
    js = js.replace("navigator.serviceWorker.register('/sw.js').catch(() => {});", "/* single-file build: no external service worker */")

    html = re.sub(r'\s*<script src="/assets/app\.js[^"]*" defer></script>', "", html)
    html = html.replace("</body>", f"  <script>\n{js}\n  </script>\n</body>")
    html = html.replace("<head>", "<head>\n  <!-- Single-file frontend. Requires the LinguaLens Python backend for /api. -->")

    out = WEB / "single.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
