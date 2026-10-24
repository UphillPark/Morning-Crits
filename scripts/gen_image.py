#!/usr/bin/env python3
"""Generate one Mood Screen image with the Gemini image API.

Usage:  python3 scripts/gen_image.py PROMPT_FILE OUT.png [--aspect 2:3]

Reads the prompt from PROMPT_FILE (plain text), asks the first model in MODELS
for one 1K image and writes it to OUT.png. The API key is a network secret
that the proxy adds to requests for generativelanguage.googleapis.com, so this
script never sees it. When a model answers 404 (renamed or retired), the next
model is tried. Prints a JSON report and exits 0 only when an image was saved.

status in the report:
  ok       image saved
  quota    429 / RESOURCE_EXHAUSTED / billing: credit is used up or not enabled
  refused  the safety filter blocked the prompt or the image
  error    anything else (network, 400, no image in the reply)
The caller decides what to print in the image cell for each status.
"""
import base64
import json
import sys
import urllib.error
import urllib.request

API = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"
# Cheapest first. Keep the list short: every extra model is another paid try.
MODELS = ["gemini-3.1-flash-lite-image", "gemini-3.1-flash-image", "gemini-2.5-flash-image"]


def call(model, prompt, aspect=None):
    config = {"responseModalities": ["IMAGE"]}
    if aspect:
        config["imageConfig"] = {"aspectRatio": aspect, "imageSize": "1K"}
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": config}
    req = urllib.request.Request(API.format(model), data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {}
    except Exception as e:  # network or proxy error
        return None, {"error": {"message": type(e).__name__ + ": " + str(e)}}


def classify(code, reply):
    err = (reply.get("error") or {})
    msg = str(err.get("message", ""))[:300]
    if code == 429 or err.get("status") == "RESOURCE_EXHAUSTED" or "billing" in msg.lower() or "credit" in msg.lower():
        return "quota", msg
    if code != 200:
        return "error", (str(code) + " " + msg).strip()
    fb = reply.get("promptFeedback") or {}
    if fb.get("blockReason"):
        return "refused", "prompt blocked: " + str(fb["blockReason"])
    for cand in reply.get("candidates") or []:
        for part in (cand.get("content") or {}).get("parts") or []:
            if (part.get("inlineData") or {}).get("data"):
                return "ok", ""
        if cand.get("finishReason") in ("SAFETY", "IMAGE_SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII"):
            return "refused", "image blocked: " + cand["finishReason"]
    return "error", "no image in reply"


def main(argv):
    aspect = "2:3"
    if "--aspect" in argv:
        i = argv.index("--aspect")
        aspect = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if len(argv) != 2:
        print(__doc__)
        return 1
    prompt = open(argv[0], encoding="utf-8").read().strip()
    out = argv[1]
    report = {"status": "error", "model": None, "detail": "", "words": len(prompt.split())}
    for model in MODELS:
        code, reply = call(model, prompt, aspect)
        if code == 400 and "imageConfig" in json.dumps(reply):
            # Older models reject imageConfig; ask again without it.
            code, reply = call(model, prompt)
        status, detail = classify(code, reply)
        report.update(status=status, model=model, detail=detail, usage=reply.get("usageMetadata"))
        if code == 404:
            continue
        break
    if report["status"] == "ok":
        for cand in reply["candidates"]:
            for part in cand["content"]["parts"]:
                data = (part.get("inlineData") or {}).get("data")
                if data:
                    with open(out, "wb") as f:
                        f.write(base64.b64decode(data))
                    report["file"] = out
                    break
            if "file" in report:
                break
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
