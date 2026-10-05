#!/usr/bin/env python3
"""Build the GitHub Pages site from today's Morning Crit source.

Usage:  python3 scripts/build_site.py [source/morning-crit.html]

Writes:
  index.html              today's issue (both sheets) + archive tab
  issues/YYYY-MM-DD.html  permanent copy of the issue
  issues/index.json       issue metadata, newest first
  archive.html            list of every issue
"""
import json
import os
import re
import sys
from html import escape

from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_URL = "https://uphillpark.github.io/Morning-Crits/"


def read_meta(src):
    soup = BeautifulSoup(src, "html.parser")
    crit = soup.find(id="page-crit")
    thesis = soup.find(id="page-thesis")

    def tblock(main):
        out = {}
        tb = main.find(class_="tblock") if main else None
        if tb:
            for cell in tb.find_all("div", recursive=False):
                b = cell.find("b")
                if b:
                    key = b.get_text(strip=True).lower()
                    b.extract()
                    out[key] = cell.get_text(" ", strip=True)
        return out

    t1 = tblock(crit)
    m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", t1.get("date", ""))
    if not m:
        sys.exit("Could not read the issue date from the SHEET 1 title block.")
    date = "-".join(m.groups())
    num = re.search(r"\d+", t1.get("issue", "") or "0")
    lead = crit.find("h2")
    crit_q = crit.select_one("aside.crit.big p")
    issues = [h.get_text(" ", strip=True) for h in thesis.select("article.issue h3")] if thesis else []
    return {
        "date": date,
        "issue": int(num.group()) if num else 0,
        "headline": lead.get_text(" ", strip=True) if lead else "",
        "crit": crit_q.get_text(" ", strip=True) if crit_q else "",
        "thesis": issues,
        "url": SITE_URL + "issues/" + date + ".html",
    }


def split_head(src):
    i = src.find('<nav class="tabs"')
    if i < 0:
        sys.exit("Source has no sheet tabs (<nav class=\"tabs\">).")
    return src[:i], src[i:]


def page(head, body, description):
    return (
        "<!doctype html>\n<html lang=\"ko\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        "<meta name=\"description\" content=\"" + escape(description) + "\">\n"
        + head.strip() + "\n</head>\n<body>\n" + body.strip() + "\n</body>\n</html>\n"
    )


def with_archive_tab(body, prefix, current=False):
    cur = ' aria-current="page"' if current else ""
    tab = '  <a href="' + prefix + 'archive.html"' + cur + '>ARCHIVE <b>지난 호</b></a>\n</nav>'
    return body.replace("</nav>", tab, 1)


def build_archive(head, items):
    rows = []
    for it in items:
        thesis = " · ".join(escape(t) for t in it.get("thesis", [])[:4])
        rows.append(
            "<tr><td class=\"m\">" + it["date"].replace("-", ".") + "</td>"
            "<td class=\"m\">No. " + str(it["issue"]).zfill(3) + "</td>"
            "<td><a href=\"issues/" + it["date"] + ".html\">" + escape(it["headline"]) + "</a></td>"
            "<td>" + thesis + "</td></tr>"
        )
    body = (
        '<nav class="tabs" aria-label="지면">\n'
        '  <a href="index.html#crit">SHEET 1/2 <b>Morning Crit</b></a>\n'
        '  <a href="index.html#thesis">SHEET 2/2 <b>Thesis Desk</b></a>\n'
        '  <a href="archive.html" aria-current="page">ARCHIVE <b>지난 호</b></a>\n'
        "</nav>\n"
        '<main class="sheet">\n'
        '  <header class="mast"><div><h1>Archive</h1>'
        '<p class="sub">지난 Morning Crit 전체. 날짜를 누르면 그날의 1면과 2면이 열린다.</p></div></header>\n'
        '  <section><div class="label"><span class="tag">지난 호</span> ' + str(len(items)) + "호</div>\n"
        '  <div class="tablewrap"><table><thead><tr><th>날짜</th><th>호</th><th>1면</th><th>2면 이슈</th></tr></thead>\n'
        "  <tbody>" + "\n".join(rows) + "</tbody></table></div></section>\n"
        "</main>\n"
    )
    head = re.sub(r"<title>.*?</title>", "<title>Morning Crit · Archive</title>", head, flags=re.S)
    return page(head, body, "Morning Crit 지난 호 목록")


def main():
    src_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "source", "morning-crit.html")
    src = open(src_path, encoding="utf-8").read()
    meta = read_meta(src)
    head, body = split_head(src)
    desc = "Morning Crit No. " + str(meta["issue"]).zfill(3) + " · " + meta["headline"]

    os.makedirs(os.path.join(ROOT, "issues"), exist_ok=True)
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(head, with_archive_tab(body, ""), desc))
    with open(os.path.join(ROOT, "issues", meta["date"] + ".html"), "w", encoding="utf-8") as f:
        f.write(page(head, with_archive_tab(body, "../"), desc))

    idx_path = os.path.join(ROOT, "issues", "index.json")
    items = []
    if os.path.exists(idx_path):
        items = json.load(open(idx_path, encoding="utf-8"))
    items = [it for it in items if it["date"] != meta["date"]] + [meta]
    items.sort(key=lambda it: it["date"], reverse=True)
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ROOT, "archive.html"), "w", encoding="utf-8") as f:
        f.write(build_archive(head, items))

    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
