#!/usr/bin/env python3
"""Upload Mood Screen images to the 'mood screen' Google Drive folder.

Usage:  python3 scripts/upload_drive.py IMAGE [IMAGE ...] [--month YYYY-MM]

Sends each image to the Apps Script upload endpoint in MOOD_UPLOAD_URL, with
the token in MOOD_UPLOAD_TOKEN (both set in the cloud environment). The
endpoint saves only png/jpeg/webp files, into a month subfolder when --month
is given. Prints a JSON report (never the token or the endpoint URL) and exits
1 if any upload fails. An upload failure must not stop the issue: write the
report into the summary and carry on.
"""
import base64
import json
import os
import sys
import urllib.request

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
MAX_BYTES = 20 * 1024 * 1024


def upload(url, token, path, month):
    ext = os.path.splitext(path)[1].lower()
    if ext not in MIME:
        return {"file": path, "ok": False, "error": "not a png/jpeg/webp image"}
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        return {"file": path, "ok": False, "error": f"too large ({size} bytes)"}
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    body = {"token": token, "name": os.path.basename(path), "mime": MIME[ext], "data": data}
    if month:
        body["month"] = month
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        # Apps Script answers with a 302 to script.googleusercontent.com; urllib follows it as a GET.
        with urllib.request.urlopen(req, timeout=90) as resp:
            reply = json.loads(resp.read().decode("utf-8"))
    except Exception as e:  # network, proxy refusal, non-JSON reply
        return {"file": path, "ok": False, "error": f"{type(e).__name__}: {e}"}
    reply.pop("token", None)
    return {"file": path, **reply}


def main(argv):
    month = None
    if "--month" in argv:
        i = argv.index("--month")
        month = argv[i + 1] if i + 1 < len(argv) else None
        argv = argv[:i] + argv[i + 2:]
    files = argv
    url = os.environ.get("MOOD_UPLOAD_URL")
    token = os.environ.get("MOOD_UPLOAD_TOKEN")
    if not files:
        print(__doc__)
        return 1
    if not url or not token:
        print(json.dumps({"ok": False, "error": "MOOD_UPLOAD_URL or MOOD_UPLOAD_TOKEN is not set"}))
        return 1
    results = [upload(url, token, p, month) for p in files]
    ok = all(r.get("ok") for r in results)
    print(json.dumps({"ok": ok, "results": results}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
