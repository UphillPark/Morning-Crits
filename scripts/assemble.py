#!/usr/bin/env python3
"""Merge the Seminar desk's sheets 3-5 into today's issue and build the Word Desk.

Usage:
  python3 scripts/assemble.py            weekday: source/morning-crit.html (in place)
  python3 scripts/assemble.py --sunday   Sunday review: writes source/sunday.html
  python3 scripts/assemble.py --date YYYY-MM-DD   use another date's fragment

Weekday: sheets 1-2 come from source/morning-crit.html (written by the Morning
Crit routine). Sheets 3-5 come from source/seminar/YYYY-MM-DD.html (written by
the Seminar routine). A missing fragment or sheet becomes a "closed today"
notice. The Word Desk sheet is rebuilt from every sheet's aside.vocab, the tab
bar is rebuilt from the sheets present, and sheets 3-5 take the issue number
of sheet 1.

Sunday: the fragment holds the review sheets (page-review, page-quiz). They are
wrapped in the head of source/morning-crit.html and written to
source/sunday.html, so the weekday base stays untouched for Monday.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from html import escape

from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "source", "morning-crit.html")
KST = dt.timezone(dt.timedelta(hours=9))

# id suffix -> (tab number label, tab title)
SHEETS = [
    ("crit", "Morning Crit"),
    ("thesis", "Thesis Desk"),
    ("symposium", "Daily Symposium"),
    ("unit", "Unit Brief"),
    ("screen", "Mood Screen"),
]
SUNDAY_SHEETS = [("review", "Weekly Review"), ("quiz", "Word Quiz")]
SEMINAR = ["symposium", "unit", "screen"]
SUBS = {
    "symposium": "역사·사상사 시대순 강의 — 서양과 동아시아를 한 시대 안에서 나란히 읽는다",
    "unit": "AA · RCA · Bartlett unit briefs, read for the theory underneath them",
    "screen": "One classic a day — film, painting, documentary, photography — to build a visual vocabulary",
}
KIND = {"ielts": "IELTS 7.0", "crit": "AA CRIT"}


def main_re(name):
    return re.compile(r'<main\b[^>]*\bid="page-' + name + r'"[^>]*>.*?</main>', re.S)


def find_main(html, name):
    m = main_re(name).search(html)
    return m.group(0) if m else None


def set_hidden(block, hidden):
    open_tag = re.match(r"<main\b[^>]*>", block).group(0)
    tag = re.sub(r"\s+hidden(?=[\s>])", "", open_tag)
    if hidden:
        tag = tag[:-1] + " hidden>"
    return tag + block[len(open_tag):]


def tblock_value(block, key):
    m = re.search(r"<b>" + key + r"</b>\s*([^<]*)</div>", block or "")
    return m.group(1).strip() if m else ""


def set_tblock(block, key, value):
    return re.sub(r"(<b>" + key + r"</b>)\s*[^<]*(</div>)", lambda m: m.group(1) + value + m.group(2), block, count=1)


def closed_sheet(name, title, date_label, issue):
    return (
        '<main class="sheet" id="page-' + name + '">\n'
        '  <header class="mast">\n'
        "    <div>\n"
        "      <h1>" + title + "</h1>\n"
        '      <p class="sub">' + SUBS[name] + "</p>\n"
        "    </div>\n"
        '    <div class="tblock" aria-label="Issue information">\n'
        "      <div><b>Issue</b>" + issue + "</div>\n"
        "      <div><b>Date</b>" + date_label + "</div>\n"
        "      <div><b>Desk</b>Closed</div>\n"
        "      <div><b>Rev</b>A</div>\n"
        "    </div>\n"
        "  </header>\n"
        '  <section class="closed"><p>Seminar desk closed today · 오늘 3~5면 휴간</p></section>\n'
        "</main>"
    )


def vocab_rows(html):
    """(term, pos, ko, ex, kind, sheet title) for every word box, in sheet order."""
    soup = BeautifulSoup(html, "html.parser")
    titles = dict(SHEETS + SUNDAY_SHEETS)
    rows = []
    for main in soup.select("main.sheet"):
        name = (main.get("id") or "")[len("page-"):]
        if name == "words":
            continue
        for li in main.select("aside.vocab li"):
            def part(cls):
                el = li.find(class_=cls)
                return el.get_text(" ", strip=True) if el else ""
            rows.append((part("term"), part("pos"), part("ko"), part("ex"), li.get("data-kind", ""), titles.get(name, name)))
    return rows


def words_sheet(html, date_label, issue):
    rows = vocab_rows(html)
    body = []
    for term, pos, ko, ex, kind, sheet in rows:
        body.append(
            "<tr><td>" + escape(term) + "</td><td class=\"m\">" + escape(pos) + "</td><td>" + escape(ko)
            + "<br><small>" + escape(ex) + "</small></td><td class=\"kind " + escape(kind) + "\">" + KIND.get(kind, kind)
            + "</td><td class=\"m\">" + escape(sheet) + "</td></tr>"
        )
    n_ielts = sum(1 for r in rows if r[4] == "ielts")
    n_crit = sum(1 for r in rows if r[4] == "crit")
    table = (
        '    <div class="tablewrap words"><table>\n'
        "      <thead><tr><th>Term</th><th>POS</th><th>뜻 · 예문</th><th>Kind</th><th>Sheet</th></tr></thead>\n"
        "      <tbody>" + "\n".join(body) + "</tbody>\n"
        "    </table></div>\n"
    ) if rows else '    <section class="closed"><p>No words today · 오늘 단어 없음</p></section>\n'
    return (
        '<main class="sheet" id="page-words">\n'
        '  <header class="mast">\n'
        "    <div>\n"
        "      <h1>Word Desk</h1>\n"
        '      <p class="sub">오늘 다섯 면에서 모은 단어 — IELTS 7.0 학술 어휘와 AA 크리틱 용어. 매주 일요일 퀴즈로 다시 본다.</p>\n'
        "    </div>\n"
        '    <div class="tblock" aria-label="Issue information">\n'
        "      <div><b>Issue</b>" + issue + "</div>\n"
        "      <div><b>Date</b>" + date_label + "</div>\n"
        "      <div><b>IELTS</b>" + str(n_ielts) + "</div>\n"
        "      <div><b>AA Crit</b>" + str(n_crit) + "</div>\n"
        "    </div>\n"
        "  </header>\n"
        '  <section aria-labelledby="words-h">\n'
        '    <div class="label"><span class="tag" id="words-h">Today’s words</span> ' + str(len(rows)) + " terms</div>\n"
        + table +
        "  </section>\n"
        "</main>"
    )


def nav(sheets):
    total = len(sheets)
    links = []
    for i, (name, title) in enumerate(sheets):
        cur = ' aria-current="page"' if i == 0 else ""
        links.append('  <a href="#' + name + '" data-page="' + name + '"' + cur + '><span class="n">SHEET ' + str(i + 1) + "/" + str(total) + "</span> <b>" + title + "</b></a>")
    links.append('  <a href="#words" data-page="words"><span class="n">WORDS</span> <b>Word Desk</b></a>')
    return '<nav class="tabs" aria-label="Sheets">\n' + "\n".join(links) + "\n</nav>"


def split_doc(html):
    """head (up to the tab bar), tail (the closing script and after)."""
    i = html.find('<nav class="tabs"')
    j = html.rfind("<script>")
    if i < 0 or j < 0:
        sys.exit("Source has no tab bar or closing script.")
    return html[:i], html[j:]


def latest_issue():
    idx = os.path.join(ROOT, "issues", "index.json")
    if not os.path.exists(idx):
        return 0
    return max((it.get("issue", 0) for it in json.load(open(idx, encoding="utf-8"))), default=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sunday", action="store_true")
    ap.add_argument("--date")
    args = ap.parse_args()

    html = open(SRC, encoding="utf-8").read()
    head, tail = split_doc(html)
    crit = find_main(html, "crit")

    if args.date:
        day = dt.date.fromisoformat(args.date)
    elif not args.sunday and crit:
        m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", tblock_value(crit, "Date"))
        day = dt.date(*map(int, m.groups())) if m else dt.datetime.now(KST).date()
    else:
        day = dt.datetime.now(KST).date()
    frag_path = os.path.join(ROOT, "source", "seminar", day.isoformat() + ".html")
    frag = open(frag_path, encoding="utf-8").read() if os.path.exists(frag_path) else ""
    date_label = day.strftime("%Y.%m.%d ") + day.strftime("%a").upper()

    if args.sunday:
        if not frag:
            sys.exit("No Sunday fragment: " + frag_path)
        issue = "No. " + str(latest_issue() + 1).zfill(3)
        sheets, blocks = [], []
        for name, title in SUNDAY_SHEETS:
            b = find_main(frag, name)
            if b:
                b = set_tblock(b, "Issue", issue)
                blocks.append(set_hidden(b, hidden=bool(blocks)))
                sheets.append((name, title))
        if not blocks:
            sys.exit("Sunday fragment has no page-review / page-quiz sheet.")
        body = "\n\n".join(blocks)
        doc = head + nav(sheets) + "\n\n" + body + "\n\n" + set_hidden(words_sheet(body, date_label, issue), True) + "\n\n" + tail
        out = os.path.join(ROOT, "source", "sunday.html")
        open(out, "w", encoding="utf-8").write(doc)
        print(json.dumps({"edition": "sunday", "date": day.isoformat(), "issue": issue, "sheets": [s for s, _ in sheets], "out": out}, ensure_ascii=False))
        return

    if not crit:
        sys.exit("Source has no #page-crit sheet.")
    issue = tblock_value(crit, "Issue") or "No. ---"
    blocks, status = [crit], {}
    thesis = find_main(html, "thesis")
    if thesis:
        blocks.append(thesis)
    titles = dict(SHEETS)
    for name in SEMINAR:
        b = find_main(frag, name) if frag else None
        status[name] = "fragment" if b else "closed"
        if b:
            b = set_tblock(b, "Issue", issue)
        else:
            b = closed_sheet(name, titles[name], date_label, issue)
        blocks.append(b)
    blocks = [set_hidden(b, hidden=(i > 0)) for i, b in enumerate(blocks)]
    body = "\n\n".join(blocks)
    sheets = [(n, t) for n, t in SHEETS if n != "thesis" or thesis]
    doc = head + nav(sheets) + "\n\n" + body + "\n\n" + set_hidden(words_sheet(body, date_label, issue), True) + "\n\n" + tail
    open(SRC, "w", encoding="utf-8").write(doc)
    print(json.dumps({"edition": "weekday", "date": day.isoformat(), "issue": issue, "fragment": os.path.relpath(frag_path, ROOT) if frag else None, "sheets": status, "words": len(vocab_rows(body))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
