#!/usr/bin/env python3
"""Write a copy of an issue with the generated Mood Screen images inlined.

Usage:  python3 scripts/inline_images.py [source/morning-crit.html] [build/artifact.html]

The artifact cannot rely on images hosted elsewhere, so every <img> whose src
points at GitHub Pages assets/screen/ is replaced by a data: URI read from the
local assets/screen/ file. Other images are left as they are. The source file
is not changed. Prints a JSON report; a missing file is reported and its img
stays as a link.
"""
import base64
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_URL = "https://uphillpark.github.io/Morning-Crits/assets/screen/"
MIME = {".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
SRC_RE = re.compile(r'src="' + re.escape(ASSETS_URL) + r'([^"]+)"')


def main(argv):
    src = argv[0] if argv else os.path.join(ROOT, "source", "morning-crit.html")
    out = argv[1] if len(argv) > 1 else os.path.join(ROOT, "build", "artifact.html")
    html = open(src, encoding="utf-8").read()
    done, missing = [], []

    def swap(m):
        name = m.group(1)
        path = os.path.join(ROOT, "assets", "screen", name)
        if not os.path.exists(path):
            missing.append(name)
            return m.group(0)
        data = base64.b64encode(open(path, "rb").read()).decode("ascii")
        done.append(name)
        return 'src="data:' + MIME.get(os.path.splitext(name)[1].lower(), "image/webp") + ";base64," + data + '"'

    html = SRC_RE.sub(swap, html)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(json.dumps({"file": os.path.relpath(out, ROOT), "inlined": done, "missing": missing, "bytes": len(html.encode("utf-8"))}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
