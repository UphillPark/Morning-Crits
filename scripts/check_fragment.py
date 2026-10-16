#!/usr/bin/env python3
"""Check a Seminar fragment before it is pushed.

Usage:  python3 scripts/check_fragment.py source/seminar/YYYY-MM-DD.html [--sunday]

Checks that the expected sheets exist with their ids and data-* attributes,
that each sheet has a title block, a headline and a word box, and that no
image or link URL is a placeholder or answers 404/410. URLs the container
cannot reach (proxy refusal, 403, 429, timeouts) are listed as "unverified"
rather than failed: confirm those through WebSearch/WebFetch results instead.
Prints a JSON report and exits 1 if anything fails.
"""
import json
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
        for img in main_el.find_all("img"):
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
