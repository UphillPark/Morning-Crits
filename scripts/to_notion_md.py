#!/usr/bin/env python3
"""Convert a Morning Crit issue (HTML) into Notion-flavored Markdown.

Usage:  python3 scripts/to_notion_md.py [source/morning-crit.html]

Writes build/notion.md (page body) and build/notion-meta.json (database
properties). The Markdown follows notion://docs/enhanced-markdown-spec:
headings, callouts, tables, bullet and numbered lists, links.
"""
import datetime as dt
import json
import os
import re
import sys

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_URL = "https://uphillpark.github.io/Morning-Crits/"
SPECIAL = set("\\*~`$[]<>{}|^")


def esc(text):
    return "".join("\\" + c if c in SPECIAL else c for c in text)


def inline(node, skip=()):
    """Rich text for an element, keeping bold, italic and links."""
    out = []
    for ch in node.children:
        if isinstance(ch, NavigableString):
            if ch.__class__.__name__ == "Comment":
                continue
            out.append(esc(str(ch)))
        elif isinstance(ch, Tag):
            if any(ch.get("class") and k in ch.get("class") for k in skip) or ch.name in skip:
                continue
            inner = inline(ch, skip)
            if ch.name == "a" and ch.get("href", "").startswith(("http://", "https://")):
                out.append("[" + inner.strip() + "](" + ch["href"] + ")")
            elif ch.name in ("b", "strong") and inner.strip():
                out.append("**" + inner.strip() + "**")
            elif ch.name in ("i", "em") and inner.strip():
                out.append("*" + inner.strip() + "*")
            elif ch.name == "br":
                out.append("<br>")
            elif ch.name == "small":
                out.append(" — " + inner.strip())
            else:
                out.append(inner)
    return re.sub(r"\s+", " ", "".join(out))


def text(node):
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)) if node else ""


def indent(lines, n=1):
    return ["\t" * n + l for l in lines]


def table(rows, header=True):
    out = ['<table header-row="' + ("true" if header else "false") + '">']
    for row in rows:
        color = ""
        if isinstance(row, tuple):
            row, color = row
        out.append("\t<tr" + (' color="' + color + '"' if color else "") + ">")
        for cell in row:
            out.append("\t\t<td>" + cell + "</td>")
        out.append("\t</tr>")
    out.append("</table>")
    return out


def callout(body_lines, icon, color):
    return ['<callout icon="' + icon + '" color="' + color + '">'] + indent(body_lines) + ["</callout>"]


def src_line(p):
    return ['<span color="gray">출처 · ' + inline(p).strip() + "</span>"] if p else []


def figs_table(div):
    cells = div.find_all("div", recursive=False)
    nums = ["**" + esc(text(c.find("strong"))) + "**" for c in cells]
    labels = [esc(text(c.find("span"))) for c in cells]
    return table([nums, labels], header=True)


def crit_aside(aside, issue_date):
    k = aside.find(class_="k")
    lines = ["**" + esc(text(k)) + "**"] if k else []
    if aside.find(class_="q"):
        lines.append("**" + esc(text(aside.find(class_="q"))) + "**")
        if aside.find(class_="en"):
            lines.append("*" + esc(text(aside.find(class_="en"))) + "*")
        return callout(lines, "🖍️", "red_bg")
    loose = inline(aside, skip=("k", "p", "ol", "src")).strip()
    if loose:
        lines.append(loose)
    for ch in aside.find_all(["p", "ol"], recursive=False):
        if ch.name == "ol":
            lines += ["1. " + inline(li).strip() for li in ch.find_all("li")]
        elif "src" in (ch.get("class") or []):
            lines += src_line(ch)
        else:
            lines.append(inline(ch).strip())
    if k and text(k).upper().startswith("DIPLOMA"):
        return callout(lines, "🎓", "blue_bg")
    return callout(lines, "🖍️", "red_bg")


def dday(date_str, issue_date):
    try:
        d = dt.date.fromisoformat(date_str)
    except ValueError:
        return ""
    n = (d - issue_date).days
    return "D-" + str(n) if n > 0 else ("오늘" if n == 0 else "지남")


def block(el, issue_date):
    """Markdown lines for one element, dispatched on tag and class."""
    cls = el.get("class") or []
    name = el.name
    if name in ("nav", "script", "style") or "tblock" in cls:
        return []
    if "label" in cls:
        tag = el.find(class_="tag")
        rest = text(el).replace(text(tag), "", 1).strip() if tag else ""
        return ["## " + esc(text(tag) + (" · " + rest if rest else "") if tag else text(el))]
    if name == "header" and "mast" in cls:
        return []  # handled by sheet()
    if name == "aside" and "crit" in cls:
        return crit_aside(el, issue_date)
    if "kicker" in cls:
        return ['<span color="red">**' + esc(text(el)) + "**</span>"]
    if "src" in cls:
        return src_line(el)
    if "stats" in cls or "figs" in cls:
        return figs_table(el)
    if name in ("h2", "h3"):
        return ["### " + inline(el).strip()]
    if name == "p":
        t = inline(el).strip()
        return [t] if t else []
    if name == "ul" and "briefs" in cls:
        out = []
        for li in el.find_all("li", recursive=False):
            line = "- " + inline(li, skip=("src",)).strip()
            s = li.find(class_="src")
            if s:
                line += ' <span color="gray">(' + inline(s).strip() + ")</span>"
            out.append(line)
        return out
    if name == "ul" and "cal" in cls:
        rows = [["날짜", "D-day (발행일 기준)", "일정"]]
        for li in el.find_all("li", recursive=False):
            dd = li.find(class_="dd")
            rows.append([
                esc(text(li.find(class_="d"))),
                dday(dd.get("data-date", ""), issue_date) if dd else "",
                inline(li.find(class_="t")).strip(),
            ])
        return table(rows)
    if name == "table":
        rows = []
        head = el.find("thead")
        if head:
            rows.append([esc(text(th)) for th in head.find_all("th")])
        width = len(rows[0]) if rows else 0
        for tr in el.find("tbody").find_all("tr", recursive=False):
            cells = [inline(td).strip() for td in tr.find_all("td", recursive=False)]
            if "group" in (tr.get("class") or []):
                rows.append((["**" + cells[0] + "**"] + [""] * (width - 1), "gray_bg"))
            else:
                rows.append(cells + [""] * (width - len(cells)))
        return table(rows, header=bool(head))
    if "routine" in cls or "method" in cls:
        out = []
        for d in el.find_all("div", recursive=False):
            label = text(d.find(class_="mono"))
            strong = d.find("strong")
            title = (label + " · " + text(strong)) if strong else label
            out.append("- **" + esc(title) + "** " + inline(d.find("p")).strip())
        return out
    if "pairs" in cls:
        out = []
        for a in el.find_all("article", recursive=False):
            out.append("### " + inline(a.find("h3")).strip())
            out.append('<span color="red">' + esc(text(a.find(class_="x"))) + "</span>")
            for p in a.find_all("p", recursive=False):
                out += block(p, issue_date)
        return out
    if name == "article" and "issue" in cls:
        out = []
        hd = el.find("header")
        region = text(hd.find(class_="region"))
        scales = [text(s) for s in hd.select(".scale span.on")]
        out.append("### " + inline(hd.find("h3")).strip())
        out.append('<span color="red">**' + esc(region) + "**</span> · 스케일: " + esc(" → ".join([scales[0], scales[-1]]) if len(scales) > 1 else "".join(scales)))
        for ch in el.find(class_="facts").children:
            if isinstance(ch, Tag):
                out += block(ch, issue_date)
        dl = el.find("dl")
        if dl:
            for dt_, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
                out.append("- **" + esc(text(dt_)) + "** " + inline(dd).strip())
        q = el.find("aside", class_="crit")
        if q:
            out += crit_aside(q, issue_date)
        return out
    if name == "footer":
        return ['<span color="gray">' + inline(p).strip() + "</span>" for p in el.find_all("p")]
    # containers: walk children
    out = []
    for ch in el.children:
        if isinstance(ch, Tag):
            out += block(ch, issue_date)
    return out


def sheet(main, title, icon, issue_date):
    mast = main.find("header", class_="mast")
    cells = {}
    for c in mast.select(".tblock > div"):
        b = c.find("b")
        k = text(b)
        b.extract()
        cells[k] = text(c)
    info = " · ".join(esc(k + " " + v) for k, v in cells.items())
    out = ["# " + title, ""]
    out += callout([esc(text(mast.find(class_="sub"))), '<span color="gray">' + info + "</span>"], icon, "gray_bg")
    for ch in main.children:
        if isinstance(ch, Tag) and ch is not mast:
            lines = block(ch, issue_date)
            if lines:
                out += lines
    return out


def issue_slug(num, date):
    """Page name build_site.py gave this issue (date, or date-NNN on a shared date)."""
    idx = os.path.join(ROOT, "issues", "index.json")
    if os.path.exists(idx):
        for it in json.load(open(idx, encoding="utf-8")):
            if it.get("issue") == num:
                return it.get("slug", it["date"])
    return date


def main():
    src_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "source", "morning-crit.html")
    soup = BeautifulSoup(open(src_path, encoding="utf-8").read(), "html.parser")
    crit = soup.find(id="page-crit")
    thesis = soup.find(id="page-thesis")

    date_txt = text(crit.select_one(".tblock"))
    m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", date_txt)
    issue_date = dt.date(*map(int, m.groups()))
    num = int(re.search(r"No\.\s*(\d+)", date_txt).group(1))
    headline = text(crit.find("h2"))
    crit_q = text(crit.select_one("aside.crit.big p"))
    thesis_titles = [text(h) for h in thesis.select("article.issue h3")] if thesis else []
    web = SITE_URL + "issues/" + issue_slug(num, issue_date.isoformat()) + ".html"

    lines = [
        '<callout icon="🌐" color="blue_bg">',
        "\t디자인 그대로 보기: [" + web + "](" + web + ") · [지난 호 전체](" + SITE_URL + "archive.html)",
        "</callout>",
        "<table_of_contents/>",
    ]
    lines += sheet(crit, "1면 · Morning Crit", "📰", issue_date)
    lines += ["---"]
    if thesis:
        lines += sheet(thesis, "2면 · Thesis Desk", "🧭", issue_date)

    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    md = "\n".join(lines) + "\n"
    open(os.path.join(ROOT, "build", "notion.md"), "w", encoding="utf-8").write(md)
    meta = {
        "Name": "Morning Crit No. " + str(num).zfill(3) + " · " + issue_date.strftime("%Y.%m.%d"),
        "date:발행일:start": issue_date.isoformat(),
        "date:발행일:is_datetime": 0,
        "호수": num,
        "1면 헤드라인": headline,
        "크릿 질문": crit_q,
        "2면 이슈": " / ".join(thesis_titles),
        "웹 신문": web,
    }
    json.dump(meta, open(os.path.join(ROOT, "build", "notion-meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({"lines": len(lines), "chars": len(md), **meta}, ensure_ascii=False))


if __name__ == "__main__":
    main()
