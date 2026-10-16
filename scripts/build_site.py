#!/usr/bin/env python3
"""Build the GitHub Pages site from today's Morning Crit source.

Usage:  python3 scripts/build_site.py [source/morning-crit.html]

Writes:
  index.html              today's issue (every sheet) + archive tab
  issues/YYYY-MM-DD.html  permanent copy of the issue (YYYY-MM-DD-NNN.html when
                          a second issue shares that date)
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


def thesis_chip(thesis):
    """Short topic tags for sheet 2, from each issue card's region label."""
    tags = []
    for r in thesis.select("article.issue .region") if thesis else []:
        parts = [x.strip() for x in r.get_text(" ", strip=True).split("·")]
        tag = parts[1].split("/")[0].strip() if len(parts) > 1 else parts[0]
        if tag and tag not in tags:
            tags.append(tag)
    return " · ".join(tags[:4])


def read_meta(src):
    soup = BeautifulSoup(src, "html.parser")
    sheets = soup.select("main.sheet[id^=page-]")
    if not sheets:
        sys.exit("Source has no sheets.")
    first = sheets[0]
    by_id = {m["id"][len("page-"):]: m for m in sheets}
    t1 = tblock(first)
    m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", t1.get("date", ""))
    if not m:
        sys.exit("Could not read the issue date from the first sheet's title block.")
    date = "-".join(m.groups())
    num = re.search(r"\d+", t1.get("issue", "") or "0")
    lead = first.find("h2")
    crit_q = first.select_one("aside.crit.big p")
    thesis = by_id.get("thesis")
    issues = [h.get_text(" ", strip=True) for h in thesis.select("article.issue h3")] if thesis else []

    chips = {}
    if thesis:
        chips["thesis"] = thesis_chip(thesis)
    sym = by_id.get("symposium")
    if sym is not None and sym.get("data-day"):
        chips["symposium"] = "DAY " + sym["data-day"].zfill(2) + " · " + sym.get("data-title", "")
    unit = by_id.get("unit")
    if unit is not None and unit.get("data-unit"):
        chips["unit"] = unit.get("data-school", "") + " " + unit["data-unit"] + " · " + unit.get("data-concept", "")
    screen = by_id.get("screen")
    if screen is not None and screen.get("data-work"):
        chips["screen"] = screen.get("data-medium", "") + " · " + screen["data-work"]
    seeds = []
    for li in thesis.select("ul.seeds li") if thesis else []:
        seed = li.find(class_="seed")
        link = li.find(class_="link")
        if seed:
            seeds.append({"seed": seed.get_text(" ", strip=True), "issue": link.get_text(" ", strip=True) if link else ""})
    vocab = []
    for main in sheets:
        if main["id"] == "page-words":
            continue
        for li in main.select("aside.vocab li"):
            term = li.find(class_="term")
            if term:
                vocab.append(term.get_text(" ", strip=True))
    return {
        "date": date,
        "issue": int(num.group()) if num else 0,
        "edition": "sunday" if "review" in by_id else "weekday",
        "headline": lead.get_text(" ", strip=True) if lead else "",
        "crit": crit_q.get_text(" ", strip=True) if crit_q else "",
        "thesis": issues,
        "seeds": seeds,
        "symposium_day": int(sym["data-day"]) if sym is not None and sym.get("data-day", "").isdigit() else None,
        "unit": unit.get("data-unit") if unit is not None else None,
        "unit_concept": unit.get("data-concept") if unit is not None else None,
        "screen_work": screen.get("data-work") if screen is not None else None,
        "screen_medium": screen.get("data-medium") if screen is not None else None,
        "chips": chips,
        "vocab": vocab,
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
    tab = '  <a href="' + prefix + 'archive.html"' + cur + '>ARCHIVE <b>지난 호</b></a>\n'
    if '<button class="print-btn"' in body:
        return body.replace('  <button class="print-btn"', tab + '  <button class="print-btn"', 1)
    return body.replace("</nav>", tab + "</nav>", 1)


CHIP_LABELS = [("thesis", "2"), ("symposium", "3"), ("unit", "4"), ("screen", "5")]
ARCHIVE_CSS = """
<style>
.afilter { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 14px; }
.afilter button { font-family: var(--f-mono); font-size: 12px; background: var(--sheet); color: var(--muted); border: 1px solid var(--ink); padding: 3px 10px; cursor: pointer; }
.afilter button[aria-pressed="true"] { background: var(--ink); color: var(--sheet); }
.afilter input { flex: 1 1 200px; min-width: 0; font: inherit; font-size: 14px; padding: 4px 10px; border: 1px solid var(--ink); background: var(--sheet); color: var(--ink); }
.amonth { font-family: var(--f-mono); font-size: 12px; letter-spacing: 0.12em; color: var(--red); margin: 18px 0 4px; }
.arch { list-style: none; margin: 0; padding: 0; display: grid; }
.arch > li { display: grid; grid-template-columns: 96px 64px minmax(0, 1fr); gap: 6px 14px; padding: 12px 0; border-bottom: 1px solid var(--rule); align-items: baseline; }
.arch > li[hidden] { display: none; }
.arch .d, .arch .n { font-family: var(--f-mono); font-size: 12.5px; color: var(--muted); font-variant-numeric: tabular-nums; }
.arch .h { font-family: var(--f-head); font-weight: 600; font-size: 16px; line-height: 1.45; min-width: 0; }
.arch .sun { font-family: var(--f-mono); font-size: 11px; color: var(--red); border: 1px solid currentColor; padding: 0 5px; margin-right: 6px; }
.arch .chips, .arch .det { grid-column: 3; min-width: 0; }
.arch .chips { display: flex; flex-wrap: wrap; gap: 6px; }
.arch .chips span { font-family: var(--f-mono); font-size: 11.5px; border: 1px solid var(--rule); padding: 0 6px; line-height: 1.7; min-width: 0; overflow-wrap: anywhere; }
.arch .chips b, .arch .det b { color: var(--red); font-weight: 500; margin-right: 4px; }
.arch .det { display: none; font-size: 13.5px; line-height: 1.6; }
.arch .det ul { margin: 2px 0 0; padding-left: 18px; }
.arch .det a { color: var(--ink); }
body.f-1 .arch .det[data-s="1"], body.f-2 .arch .det[data-s="2"], body.f-3 .arch .det[data-s="3"], body.f-4 .arch .det[data-s="4"], body.f-5 .arch .det[data-s="5"] { display: block; }
body[class*="f-"] .arch .chips { display: none; }
@media (max-width: 560px) { .arch > li { grid-template-columns: 78px minmax(0, 1fr); } .arch .n { grid-column: 1; grid-row: 2; } .arch .h, .arch .chips, .arch .det { grid-column: 2; } }
</style>
"""
ARCHIVE_JS = """
<script>
(function () {
  var btns = document.querySelectorAll('.afilter button'), q = document.querySelector('.afilter input');
  function set(n) {
    document.body.className = document.body.className.replace(/\\bf-\\d\\b/g, '').trim();
    if (n) document.body.classList.add('f-' + n);
    btns.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-f') === (n || ''))); });
    filter();
  }
  function filter() {
    var t = (q.value || '').toLowerCase().trim();
    var f = (document.body.className.match(/f-(\\d)/) || [])[1];
    document.querySelectorAll('.arch > li').forEach(function (li) {
      var okText = !t || li.getAttribute('data-text').indexOf(t) >= 0;
      var okSheet = !f || li.querySelector('.det[data-s="' + f + '"]');
      li.hidden = !(okText && okSheet);
    });
    document.querySelectorAll('.amonth').forEach(function (h) {
      var ul = h.nextElementSibling;
      h.hidden = ul && !ul.querySelector(':scope > li:not([hidden])');
    });
  }
  btns.forEach(function (b) { b.addEventListener('click', function () {
    var n = b.getAttribute('data-f');
    try { history.replaceState(null, '', n ? '#sheet-' + n : '#'); } catch (e) {}
    set(n);
  }); });
  q.addEventListener('input', filter);
  var m = location.hash.match(/sheet-(\\d)/);
  set(m ? m[1] : '');
})();
</script>
"""


def chips_for(it):
    chips = dict(it.get("chips") or {})
    if "thesis" not in chips and it.get("thesis"):
        chips["thesis"] = "이슈 " + str(len(it["thesis"])) + "건"
    out = []
    for key, n in CHIP_LABELS:
        if chips.get(key):
            out.append("<span><b>" + n + "</b>" + escape(chips[key]) + "</span>")
    return "".join(out)


def details_for(it, href):
    """Per-sheet detail blocks, shown when the archive is filtered to one sheet."""
    out = []
    if it.get("headline"):
        q = ("<br><small>" + escape(it["crit"]) + "</small>") if it.get("crit") else ""
        out.append('<div class="det" data-s="1"><b>1</b><a href="' + href + '#crit">' + escape(it["headline"]) + "</a>" + q + "</div>")
    if it.get("thesis") or it.get("seeds"):
        lis = "".join("<li>" + escape(t) + "</li>" for t in it.get("thesis", []))
        seeds = "".join("<li>" + escape(x["seed"]) + (" <small>· " + escape(x.get("issue", "")) + "</small>" if x.get("issue") else "") + "</li>" for x in it.get("seeds") or [])
        out.append('<div class="det" data-s="2"><b>2</b><a href="' + href + '#thesis">이슈</a><ul>' + lis + "</ul>"
                   + ("<b>씨앗</b><ul>" + seeds + "</ul>" if seeds else "") + "</div>")
    c = it.get("chips") or {}
    for key, n in (("symposium", "3"), ("unit", "4"), ("screen", "5")):
        if c.get(key):
            out.append('<div class="det" data-s="' + n + '"><b>' + n + '</b><a href="' + href + "#" + key + '">' + escape(c[key]) + "</a></div>")
    return "".join(out)


def build_archive(head, items):
    groups, order = {}, []
    for it in items:
        month = it["date"][:7]
        if month not in groups:
            groups[month] = []
            order.append(month)
        href = "issues/" + it.get("slug", it["date"]) + ".html"
        sun = '<span class="sun">SUNDAY</span>' if it.get("edition") == "sunday" else ""
        text = " ".join([it.get("headline", ""), it.get("crit", "")] + it.get("thesis", []) + [x["seed"] for x in it.get("seeds") or []]
                        + list((it.get("chips") or {}).values()) + (it.get("vocab") or [])).lower()
        groups[month].append(
            '<li data-text="' + escape(text) + '"><span class="d">' + it["date"].replace("-", ".") + "</span>"
            '<span class="n">No. ' + str(it["issue"]).zfill(3) + "</span>"
            '<a class="h" href="' + href + '">' + sun + escape(it["headline"]) + "</a>"
            '<span class="chips">' + chips_for(it) + "</span>" + details_for(it, href) + "</li>"
        )
    lists = "".join('<p class="amonth">' + m.replace("-", ".") + '</p>\n<ul class="arch">' + "\n".join(groups[m]) + "</ul>\n" for m in order)
    filt = ('<div class="afilter" role="group" aria-label="면별 보기">'
            '<button type="button" data-f="">전체</button>'
            + "".join('<button type="button" data-f="' + str(n) + '">' + str(n) + "면</button>" for n in range(1, 6))
            + '<input type="search" placeholder="검색 · 제목, 씨앗, 작품, 단어" aria-label="지난 호 검색"></div>')
    body = (
        '<nav class="tabs" aria-label="Sheets">\n'
        '  <a href="index.html#crit"><span class="n">SHEET 1/5</span> <b>Morning Crit</b></a>\n'
        '  <a href="index.html#thesis"><span class="n">SHEET 2/5</span> <b>Thesis Desk</b></a>\n'
        '  <a href="index.html#symposium"><span class="n">SHEET 3/5</span> <b>Daily Symposium</b></a>\n'
        '  <a href="index.html#unit"><span class="n">SHEET 4/5</span> <b>Unit Brief</b></a>\n'
        '  <a href="index.html#screen"><span class="n">SHEET 5/5</span> <b>Mood Screen</b></a>\n'
        '  <a href="archive.html" aria-current="page">ARCHIVE <b>지난 호</b></a>\n'
        "</nav>\n"
        '<main class="sheet">\n'
        '  <header class="mast"><div><h1>Archive</h1>'
        '<p class="sub">Morning Crit 전체 색인. 면을 고르면 그 면의 지난 기사·씨앗·강의·작품이 펼쳐지고, 검색은 제목·씨앗·단어까지 찾는다.</p></div></header>\n'
        '  <section><div class="label"><span class="tag">지난 호</span> ' + str(len(items)) + "호</div>\n"
        "  " + filt + "\n" + lists + "</section>\n"
        "</main>\n" + ARCHIVE_JS
    )
    head = re.sub(r"<title>.*?</title>", "<title>Morning Crit · Archive</title>", head, flags=re.S)
    return page(head + ARCHIVE_CSS, body, "Morning Crit 지난 호 목록")


def slug_for(meta, items):
    """File name for an issue: its date, or date-NNN when another issue already has that date."""
    for it in items:
        if it["issue"] == meta["issue"]:
            return it.get("slug", it["date"])
    if any(it["date"] == meta["date"] for it in items):
        return meta["date"] + "-" + str(meta["issue"]).zfill(3)
    return meta["date"]


def main():
    src_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "source", "morning-crit.html")
    src = open(src_path, encoding="utf-8").read()
    meta = read_meta(src)
    head, body = split_head(src)
    desc = "Morning Crit No. " + str(meta["issue"]).zfill(3) + " · " + meta["headline"]

    idx_path = os.path.join(ROOT, "issues", "index.json")
    items = []
    if os.path.exists(idx_path):
        items = json.load(open(idx_path, encoding="utf-8"))
    # One entry per issue number; two issues may share a date.
    meta["slug"] = slug_for(meta, items)
    meta["url"] = SITE_URL + "issues/" + meta["slug"] + ".html"
    items = [it for it in items if it["issue"] != meta["issue"]] + [meta]
    items.sort(key=lambda it: (it["date"], it["issue"]), reverse=True)
    newest = items[0]["issue"] == meta["issue"]

    os.makedirs(os.path.join(ROOT, "issues"), exist_ok=True)
    if newest:
        with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
            f.write(page(head, with_archive_tab(body, ""), desc))
    with open(os.path.join(ROOT, "issues", meta["slug"] + ".html"), "w", encoding="utf-8") as f:
        f.write(page(head, with_archive_tab(body, "../"), desc))
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ROOT, "archive.html"), "w", encoding="utf-8") as f:
        f.write(build_archive(head, items))

    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
