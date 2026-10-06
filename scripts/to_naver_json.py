#!/usr/bin/env python3
"""Convert a Morning Crit issue (HTML) into a Naver blog draft (JSON).

Usage:  python3 scripts/to_naver_json.py [source/morning-crit.html]

Writes:
  naver/YYYY-MM-DD.json   the draft for that issue
  naver/latest.json       {"date", "post"} pointer the PC uploader polls

The draft is a list of blocks the PC uploader (morning-crit-naver) types into
the Naver SmartEditor and then saves as a temporary draft. It never publishes.

Block types
  text      {"html": inline HTML (b, i, a only), "text": plain text}
  subtitle  {"text"}                       -> 인용구(소제목) in the editor
  divider   {}
  image     {"card": {"selector", "index"}, "file", "alt"}
            The PC uploader screenshots that element of the published issue
            page (issues/YYYY-MM-DD.html) and uploads the PNG.
  tags      {"tags": [...]}               -> typed as #tags at the end

The text is taken from the issue as written; nothing is rewritten, so the
blog post carries exactly the facts and sources the newspaper checked.
Static sections (읽기 지도, 읽는 법, 번역의 순서) are left out because they
repeat every day and Naver penalises near-duplicate posts.
"""
import datetime as dt
import html
import json
import os
import re
import sys

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_URL = "https://uphillpark.github.io/Morning-Crits/"
BASE_TAGS = ["모닝크릿", "건축뉴스", "런던건축", "AA스쿨", "건축담론", "졸업전시"]
MAX_TAGS = 10
WEEKDAY = "월화수목금토일"


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


def text(node):
    return squash(node.get_text(" ", strip=True)) if node else ""


def inline_html(node, skip=()):
    """Inline HTML for an element, keeping only bold, italic and http links."""
    out = []
    for ch in node.children:
        if isinstance(ch, NavigableString):
            if ch.__class__.__name__ == "Comment":
                continue
            out.append(html.escape(str(ch), quote=False))
        elif isinstance(ch, Tag):
            cls = ch.get("class") or []
            if ch.name in skip or any(k in cls for k in skip):
                continue
            inner = inline_html(ch, skip)
            href = ch.get("href", "")
            if ch.name == "a" and href.startswith(("http://", "https://")):
                out.append('<a href="' + html.escape(href) + '">' + inner.strip() + "</a>")
            elif ch.name in ("b", "strong") and inner.strip():
                out.append("<b>" + inner.strip() + "</b>")
            elif ch.name in ("i", "em") and inner.strip():
                out.append("<i>" + inner.strip() + "</i>")
            elif ch.name == "br":
                out.append(" ")
            elif ch.name == "small" and inner.strip():
                out.append(" · " + inner.strip())
            else:
                out.append(inner)
    return squash("".join(out))


def plain(fragment):
    return squash(BeautifulSoup(fragment, "html.parser").get_text(""))


def t_block(fragment, prefix=""):
    fragment = (html.escape(prefix, quote=False) + fragment) if prefix else fragment
    fragment = squash(fragment)
    return {"type": "text", "html": fragment, "text": plain(fragment)} if fragment else None


def src_block(p):
    if not p:
        return None
    return t_block(inline_html(p), "출처 · ")


def card(selector, index, name, alt):
    return {"type": "image", "card": {"selector": selector, "index": index}, "file": name, "alt": alt}


def headline_core(h):
    core = re.split(r"\s+[—–-]\s+", h, maxsplit=1)[0]
    return squash(re.sub(r"[“”\"'‘’「」『』]", "", core))


def tagify(s):
    return re.sub(r"[^0-9A-Za-z가-힣]", "", s)


class Post:
    def __init__(self):
        self.blocks = []
        self.cards = 0

    def add(self, b):
        if b:
            self.blocks.append(b)

    def sub(self, s):
        self.add({"type": "subtitle", "text": squash(s)})

    def hr(self):
        self.add({"type": "divider"})

    def img(self, selector, index, slug, alt):
        self.cards += 1
        self.add(card(selector, index, "%02d-%s.png" % (self.cards, slug), alt))


def sheet1(post, crit):
    lead = crit.select_one("div.lead")
    if lead:
        h2 = lead.find("h2")
        post.sub("1면 · " + headline_core(text(h2)))
        post.add(t_block(inline_html(lead.find(class_="deck"))) if lead.find(class_="deck") else None)
        for p in lead.select(".body > p"):
            post.add(t_block(inline_html(p)))
        if lead.select_one(".stats"):
            post.img("#page-crit div.lead .stats", 0, "lead-stats", "1면 기사 핵심 수치")
        post.add(src_block(lead.select_one("div > p.src")))
        big = lead.select_one("aside.crit.big")
        if big:
            post.img("#page-crit aside.crit.big", 0, "crit-question", "오늘의 크릿 질문")
            # The card already shows the two follow-up tasks; keep the question as searchable text.
            post.add(t_block(inline_html(big.find("p")), "오늘의 질문 · "))
        for aside in lead.select(".side aside.crit:not(.big)"):
            k = text(aside.find(class_="k"))
            post.add(t_block(inline_html(aside, skip=("k", "src")), k + " · " if k else ""))
            post.add(src_block(aside.find(class_="src")))

    for section in crit.find_all("section", recursive=False):
        label = section.find(class_="label")
        name = text(label.find(class_="tag")) if label else ""
        stories = section.select("article.story")
        if stories:
            post.hr()
            for a in stories:
                kicker = text(a.find(class_="kicker"))
                post.sub(text(a.find("h3")))
                paras = [p for p in a.find_all("p", recursive=False)
                         if not set(p.get("class") or []) & {"kicker", "src"}]
                for i, p in enumerate(paras):
                    post.add(t_block(inline_html(p), (kicker + " · ") if (i == 0 and kicker) else ""))
                crit_box = a.find("aside", class_="crit")
                if crit_box:
                    post.add(t_block(inline_html(crit_box, skip=("k",)), "CRIT · "))
                post.add(src_block(a.find("p", class_="src")))
        elif section.select_one("ul.briefs"):
            post.hr()
            post.sub(name or "단신")
            for li in section.select("ul.briefs > li"):
                body = inline_html(li, skip=("src",))
                s = li.find(class_="src")
                if s:
                    body += " (" + inline_html(s) + ")"
                post.add(t_block(body, "✔ "))
        elif section.select_one("ul.cal"):
            post.hr()
            post.sub(name or "일정")
            for li in section.select("ul.cal > li"):
                d = text(li.find(class_="d"))
                t = li.find(class_="t")
                post.add(t_block(inline_html(t) if t else "", "✔ " + d + " — "))


def sheet2(post, thesis):
    post.hr()
    post.sub("2면 · Thesis Desk")
    post.add(t_block(inline_html(thesis.select_one("header.mast p.sub"))))
    for section in thesis.find_all("section", recursive=False):
        issues = section.select("article.issue")
        if not issues:
            continue
        for a in issues:
            idx = thesis.select("article.issue").index(a)
            region = text(a.select_one(".region"))
            h3 = text(a.find("h3"))
            post.sub(h3)
            post.img("#page-thesis article.issue", idx, "issue-%d" % (idx + 1), region + " · " + h3)
            facts = a.find(class_="facts")
            for p in facts.find_all("p", recursive=False) if facts else []:
                if "src" in (p.get("class") or []):
                    continue
                post.add(t_block(inline_html(p), (region + " · ") if region else ""))
            # 장소·개입·재현·참고 are in the card image; repeating them as text would double the post.
            q = a.find("aside", class_="crit")
            if q and q.find(class_="q"):
                line = text(q.find(class_="q"))
                en = text(q.find(class_="en"))
                post.add(t_block(html.escape(line + (" (" + en + ")" if en else ""), quote=False), "THESIS Q · "))
            post.add(src_block(facts.find("p", class_="src") if facts else None))

    pairs = thesis.select("div.pairs > article")
    if pairs:
        post.hr()
        post.sub("겹쳐 읽기 · 두 이슈를 하나의 졸업 주제로")
        for a in pairs:
            post.add(t_block(html.escape(text(a.find("h3")), quote=False), "✔ " + text(a.find(class_="x")) + " → "))
            for p in a.find_all("p", recursive=False):
                if "src" in (p.get("class") or []):
                    continue
                post.add(t_block(inline_html(p)))


def board_rows(thesis, issue_date):
    today = issue_date.strftime("%m.%d")
    out = []
    for tr in thesis.select("section.board tbody tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) >= 4 and text(tds[0]) == today:
            out.append(t_block(html.escape(text(tds[1]) + " · " + text(tds[2]) + " · " + text(tds[3]), quote=False), "✔ "))
    return out


def build(src):
    soup = BeautifulSoup(src, "html.parser")
    crit = soup.find(id="page-crit")
    thesis = soup.find(id="page-thesis")
    tb = text(crit.select_one(".tblock"))
    m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", tb)
    if not m:
        sys.exit("Could not read the issue date from the SHEET 1 title block.")
    issue_date = dt.date(*map(int, m.groups()))
    num = int(re.search(r"No\.\s*(\d+)", tb).group(1))
    headline = text(crit.find("h2"))
    web = SITE_URL + "issues/" + issue_date.isoformat() + ".html"

    post = Post()
    post.img("#page-crit header.mast", 0, "cover", "Morning Crit No. %03d 마스트헤드" % num)
    n_stories = len(crit.select("article.story")) + (1 if crit.select_one("div.lead") else 0)
    n_issues = len(thesis.select("article.issue")) if thesis else 0
    post.add(t_block(
        "런던 건축계 소식과 AA Diploma를 준비하는 사람의 질문, 그리고 졸업전시 주제가 될 만한 "
        "국내·해외 이슈를 매일 아침 정리합니다. 오늘은 기사 %d개와 이슈 %d개를 골랐습니다." % (n_stories, n_issues)))
    post.add(t_block('디자인 그대로 보기 · <a href="%s">%s</a>' % (web, web)))

    sheet1(post, crit)
    if thesis:
        sheet2(post, thesis)
        seeds = board_rows(thesis, issue_date)
        if seeds:
            post.hr()
            post.sub("오늘의 졸업 주제 씨앗")
            for b in seeds:
                post.add(b)

    post.hr()
    for p in crit.select("footer p")[:1]:
        post.add(t_block(inline_html(p)))
    post.add(t_block('지난 호 전체 · <a href="%sarchive.html">%sarchive.html</a>' % (SITE_URL, SITE_URL)))

    tags = list(BASE_TAGS)
    for a in (thesis.select("article.issue .region") if thesis else []):
        for part in re.split(r"[·/]", text(a))[1:]:
            t = tagify(part)
            if t and t not in tags:
                tags.append(t)
    post.add({"type": "tags", "tags": tags[:MAX_TAGS]})

    title = "Morning Crit %d월 %d일 %s" % (issue_date.month, issue_date.day, headline_core(headline))
    body_chars = sum(len(b.get("text", "")) for b in post.blocks)
    return {
        "schema": 1,
        "date": issue_date.isoformat(),
        "weekday": WEEKDAY[issue_date.weekday()],
        "issue": num,
        "title": title,
        "source_url": web,
        "blocks": post.blocks,
        "stats": {"blocks": len(post.blocks), "images": post.cards, "chars": body_chars},
    }


def main():
    src_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "source", "morning-crit.html")
    draft = build(open(src_path, encoding="utf-8").read())
    out_dir = os.path.join(ROOT, "naver")
    os.makedirs(out_dir, exist_ok=True)
    name = draft["date"] + ".json"
    with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, "latest.json"), "w", encoding="utf-8") as f:
        json.dump({"date": draft["date"], "post": "naver/" + name, "issue_page": "issues/" + draft["date"] + ".html"},
                  f, ensure_ascii=False, indent=2)
    print(json.dumps({"date": draft["date"], "title": draft["title"], **draft["stats"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
