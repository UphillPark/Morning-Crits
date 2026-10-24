#!/usr/bin/env python3
"""Check a Seminar fragment before it is pushed.

Usage:  python3 scripts/check_fragment.py source/seminar/YYYY-MM-DD.html [--sunday]

Checks that the expected sheets exist with their ids and data-* attributes,
that each sheet has a title block, a headline and a word box, and that no
image or link URL is a placeholder or answers 404/410. URLs the container
cannot reach (proxy refusal, 403, 429, timeouts) are listed as "unverified"
rather than failed: confirm those through WebSearch/WebFetch results instead.
On weekdays it also checks the Mood Screen generative test (section.gentest):
three image cells A, B1, B2 with a status, a prompt for each, the score table,
generated images present in assets/screen/ (they are pushed with the fragment,
so they are checked on disk, not over HTTP), prompt word limits, and that no
prompt uses a banned word (the section's data-ban list plus generic copying
phrases; words struck out with <del> are the avoided ones and do not count).
Prints a JSON report and exits 1 if anything fails.
"""
import json
import os
import re
import sys
import urllib.request

from bs4 import BeautifulSoup

WEEKDAY = {
    "symposium": ["data-day", "data-title"],
    "unit": ["data-unit", "data-school", "data-concept"],
    "screen": ["data-medium", "data-work"],
}
SUNDAY = {"review": [], "quiz": []}
UA = {"User-Agent": "Mozilla/5.0 (MorningCrit fragment check)"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_URL = "https://uphillpark.github.io/Morning-Crits/assets/screen/"
SLOTS = {"a": 80, "b1": 60, "b2": 60}  # prompt word limit per image cell
STATUSES = {"ok", "quota", "refused", "error"}
GENERIC_BAN = ["in the style of", "style of", "inspired by", "à la", "homage to", "recreation of", "copy of"]


def prompt_words(pre):
    """Prompt text as sent to the model: <del> marks the avoided words, so drop them."""
    pre = BeautifulSoup(str(pre), "html.parser")
    for d in pre.find_all("del"):
        d.decompose()
    return pre.get_text(" ", strip=True)


def check_gentest(main_el, problems):
    sec = main_el.select_one("section.gentest")
    if sec is None:
        problems.append("#page-screen has no section.gentest")
        return
    if not sec.select_one(".framebox pre.prompt"):
        problems.append("gentest has no YOUR FRAME prompt")
    kw_el = sec.select_one(".framebox p i")
    keywords = [k.strip().lower() for k in kw_el.get_text().split("·") if k.strip()] if kw_el else []
    if len(keywords) != 3:
        problems.append("gentest YOUR FRAME needs three example keywords separated by ·")
    ban = [b.strip().lower() for b in (sec.get("data-ban") or "").split("|") if b.strip()]
    if not ban:
        problems.append("gentest has no data-ban list (title, artist, names to keep out of prompts)")
    for slot, limit in SLOTS.items():
        fig = sec.select_one('figure.gen[data-slot="' + slot + '"]')
        if fig is None:
            problems.append("gentest missing figure.gen " + slot)
            continue
        st = fig.get("data-status")
        if st not in STATUSES:
            problems.append("gentest " + slot + " data-status must be one of " + ", ".join(sorted(STATUSES)))
        img = fig.find("img")
        if st == "ok":
            src = img.get("src", "") if img else ""
            if not src.startswith(ASSETS_URL):
                problems.append("gentest " + slot + " image must live under " + ASSETS_URL)
            elif not os.path.exists(os.path.join(ROOT, "assets", "screen", src[len(ASSETS_URL):])):
                problems.append("gentest " + slot + " image file missing: assets/screen/" + src[len(ASSETS_URL):])
        elif img is not None:
            problems.append("gentest " + slot + " has status " + str(st) + " but still has an image")
        box = sec.select_one('.gprompt[data-slot="' + slot + '"] pre.prompt')
        if box is None:
            problems.append("gentest missing prompt for " + slot)
            continue
        words = prompt_words(box)
        n = len(words.split())
        if n > limit:
            problems.append("gentest " + slot + " prompt has " + str(n) + " words (limit " + str(limit) + ")")
        low = re.sub(r"\s+", " ", words.lower())
        for b in ban + GENERIC_BAN:
            if re.search(r"(?<!\w)" + re.escape(b) + r"(?!\w)", low):
                problems.append("gentest " + slot + " prompt uses banned words: " + b)
        for k in keywords:
            if k not in low:
                problems.append("gentest " + slot + " prompt is missing the example keyword: " + k)
    if not sec.select_one("table.gscores tbody tr"):
        problems.append("gentest has no score table")


def status(url):
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers=UA)
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if method == "GET":
                return e.code
        except Exception as e:  # network errors: report, do not crash
            if method == "GET":
                return str(e)[:80]
    return None


def main():
    path = sys.argv[1]
    sunday = "--sunday" in sys.argv
    soup = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser")
    problems, urls = [], {}
    for name, attrs in (SUNDAY if sunday else WEEKDAY).items():
        main_el = soup.find("main", id="page-" + name)
        if main_el is None:
            problems.append("missing sheet #page-" + name)
            continue
        for a in attrs:
            if not main_el.get(a):
                problems.append("#page-" + name + " missing " + a)
        if not main_el.select_one(".tblock"):
            problems.append("#page-" + name + " has no .tblock")
        if not main_el.find("h2") and name != "quiz":
            problems.append("#page-" + name + " has no h2")
        if name != "quiz" and not main_el.select("aside.vocab li[data-kind] .term"):
            problems.append("#page-" + name + " has no word box")
        if name == "screen":
            check_gentest(main_el, problems)
        for img in main_el.find_all("img"):
            if img.get("src", "").startswith(ASSETS_URL):
                continue  # generated images: checked on disk by check_gentest
            urls[img.get("src", "")] = "img #page-" + name
        for a in main_el.find_all("a", href=True):
            if a["href"].startswith("http"):
                urls.setdefault(a["href"], "link #page-" + name)
    checked, unverified = {}, []
    for url, where in urls.items():
        if "…" in url or "..." in url or not url.startswith("http"):
            problems.append(where + " has a placeholder URL: " + url)
            continue
        st = status(url)
        checked[url] = st
        if st in (404, 410):
            problems.append(where + " " + str(st) + " " + url)
        elif not isinstance(st, int) or st >= 400:
            unverified.append(where + " " + str(st) + " " + url)
    print(json.dumps({"file": path, "urls_checked": len(checked), "unverified": unverified, "problems": problems}, ensure_ascii=False, indent=2))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
