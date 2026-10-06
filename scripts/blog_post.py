#!/usr/bin/env python3
"""Turn a Morning Crit issue into a ready-to-paste Naver blog post page.

Usage:  python3 scripts/blog_post.py [YYYY-MM-DD]
        (run after build_site.py; reads issues/YYYY-MM-DD.html, default = the
        date in source/morning-crit.html)

Writes:
  blog/YYYY-MM-DD.html          the post, laid out for copy & paste
  blog/index.html               the latest post (same page)
  blog/img/YYYY-MM-DD/*.jpg     image cards cut from the issue page

The page has a toolbar (title / body / tags copy buttons, image downloads)
and below it the post body exactly as it should land in the Naver editor:
paragraphs, ▍ subtitles, • • • dividers, image cards and source links. The
person reviews it, presses "본문 복사" (or drags over the body), and pastes
into the Naver editor. Nothing here logs in to Naver or publishes anything.

The text is taken from the issue as written; nothing is rewritten, so the
post carries exactly the facts and sources the newspaper checked. Static
sections (읽기 지도, 읽는 법, 번역의 순서) are left out because they repeat
every day and Naver penalises near-duplicate posts.
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
        self.add(card(selector, index, "%02d-%s.jpg" % (self.cards, slug), alt))


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


def render_cards(draft, issue_path, out_dir, width=760, scale=1.3):
    """Cut each image card out of the issue page as a JPEG."""
    from playwright.sync_api import sync_playwright

    os.makedirs(out_dir, exist_ok=True)
    done, missing = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1400}, device_scale_factor=scale,
                                color_scheme="light", locale="ko-KR")
        page.goto("file://" + os.path.abspath(issue_path), wait_until="load", timeout=60000)
        page.evaluate("""() => {
            document.querySelectorAll('main.sheet').forEach(m => m.removeAttribute('hidden'));
            document.querySelectorAll('nav.tabs').forEach(n => n.style.display = 'none');
        }""")
        page.evaluate("() => document.fonts && document.fonts.ready")
        for b in draft["blocks"]:
            if b["type"] != "image":
                continue
            loc = page.locator(b["card"]["selector"]).nth(b["card"].get("index", 0))
            try:
                loc.scroll_into_view_if_needed(timeout=5000)
                box = loc.bounding_box()
                sx, sy, sw = page.evaluate("() => [scrollX, scrollY, document.documentElement.scrollWidth]")
                pad = 16
                x = max(0, box["x"] + sx - pad)
                clip = {"x": x, "y": max(0, box["y"] + sy - pad),
                        "width": min(box["width"] + 2 * pad, sw - x), "height": box["height"] + 2 * pad}
                page.screenshot(path=os.path.join(out_dir, b["file"]), clip=clip, full_page=True,
                                type="jpeg", quality=80)
                done.append(b["file"])
            except Exception as e:  # a missing card must not stop the post
                missing.append(b["file"] + ": " + str(e).splitlines()[0])
        browser.close()
    return done, missing


PAGE_CSS = """
:root{--bg:#f4f4f1;--card:#fff;--ink:#1f2328;--muted:#6a7078;--rule:#d9dbd5;--accent:#03c75a;--warn:#c2331d}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#15181b;--card:#1d2125;--ink:#e6e8e3;--muted:#9aa2a9;--rule:#30363b}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 "Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif}
.bar{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--rule);padding:12px 16px}
.bar .in{max-width:760px;margin:0 auto;display:grid;gap:10px}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.meta{color:var(--muted);font-size:13px}
.t{font-weight:700;font-size:17px;flex:1 1 320px}
button{font:inherit;font-size:14px;padding:7px 12px;border-radius:6px;border:1px solid var(--rule);background:var(--card);color:var(--ink);cursor:pointer}
button.main{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:700}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.tags{color:var(--muted);font-size:13px;word-break:keep-all}
.ok{color:var(--accent);font-size:13px;min-height:1em}
details{font-size:13px;color:var(--muted)}
details a{color:inherit;margin-right:8px}
.steps{margin:0;padding-left:18px;font-size:13px;color:var(--muted)}
.paper{max-width:760px;margin:20px auto 80px;padding:0 16px}
.label{font-size:12px;color:var(--muted);margin:0 0 6px}
#post{background:#fff;color:#222;padding:32px 40px;border:1px solid var(--rule);border-radius:6px;font-size:16px;line-height:1.8}
#post p{margin:0}
#post img{max-width:100%;height:auto;display:block;margin:0 auto}
#post a{color:#0a58ca}
@media (max-width:600px){#post{padding:20px 16px}}
"""

PAGE_JS = """
const note = (m) => { const n = document.getElementById('ok'); n.textContent = m; clearTimeout(note.t); note.t = setTimeout(() => n.textContent = '', 4000); };
function copyNode(node) {
  const r = document.createRange(); r.selectNodeContents(node);
  const s = getSelection(); s.removeAllRanges(); s.addRange(r);
  let ok = false; try { ok = document.execCommand('copy'); } catch (e) {}
  s.removeAllRanges(); return ok;
}
async function copyText(t) {
  try { await navigator.clipboard.writeText(t); return true; }
  catch (e) { const a = document.createElement('textarea'); a.value = t; document.body.appendChild(a); a.select();
    let ok = false; try { ok = document.execCommand('copy'); } catch (e2) {} a.remove(); return ok; }
}
document.getElementById('c-title').onclick = async () => note(await copyText(document.getElementById('title').textContent) ? '제목을 복사했어요. 네이버 제목 칸에 붙여 넣으세요.' : '복사가 막혔어요. 제목을 드래그해서 복사해 주세요.');
document.getElementById('c-body').onclick = () => note(copyNode(document.getElementById('post')) ? '본문을 복사했어요. 네이버 본문 칸을 클릭하고 Ctrl+V 하세요.' : '복사가 막혔어요. 본문을 드래그해서 복사해 주세요.');
document.getElementById('c-tags').onclick = async () => note(await copyText(document.getElementById('tags').dataset.tags) ? '태그를 복사했어요. 발행 설정의 태그 칸에 붙여 넣으세요.' : '복사가 막혔어요.');
"""


def body_html(draft, img_base):
    out = []
    for b in draft["blocks"]:
        t = b["type"]
        if t == "text":
            out.append("<p>%s</p>" % b["html"])
            out.append("<p><br></p>")
        elif t == "subtitle":
            out.append('<p><b><span style="font-size:19px">▍ %s</span></b></p>' % html.escape(b["text"], quote=False))
            out.append("<p><br></p>")
        elif t == "divider":
            out.append('<p style="text-align:center"><span style="color:#999999">• • •</span></p>')
            out.append("<p><br></p>")
        elif t == "image" and b.get("rendered", True):
            out.append('<p style="text-align:center"><img src="%s%s" alt="%s" width="760"></p>'
                       % (img_base, b["file"], html.escape(b["alt"])))
            out.append("<p><br></p>")
    while out and out[-1] == "<p><br></p>":
        out.pop()
    return "\n".join(out)


def page_html(draft, img_base):
    tags = next((b["tags"] for b in draft["blocks"] if b["type"] == "tags"), [])
    imgs = [b for b in draft["blocks"] if b["type"] == "image" and b.get("rendered", True)]
    dl = " ".join('<a href="%s%s" download>%s</a>' % (img_base, b["file"], b["file"]) for b in imgs)
    s = draft["stats"]
    return """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Morning Crit 블로그 · %(date)s</title>
<style>%(css)s</style></head>
<body>
<div class="bar"><div class="in">
  <div class="row"><span class="meta">%(date)s (%(wd)s) · No. %(num)03d · 본문 %(chars)s자 · 사진 %(nimg)d장 · <a href="%(src)s">신문 보기</a></span></div>
  <div class="row"><span class="t" id="title">%(title)s</span><button id="c-title">제목 복사</button></div>
  <div class="row"><button class="main" id="c-body">본문 복사</button><button id="c-tags">태그 복사</button>
    <span class="tags" id="tags" data-tags="%(tagcsv)s">%(taghash)s</span></div>
  <div class="ok" id="ok" role="status"></div>
  <details><summary>붙여넣는 순서 · 이미지 따로 받기</summary>
    <ol class="steps"><li>제목 복사 → 네이버 글쓰기 제목 칸에 붙여넣기</li>
    <li>본문 복사 → 본문 칸을 클릭하고 Ctrl+V (사진·링크·굵은 글씨가 함께 들어갑니다)</li>
    <li>사진이 빠지면 아래 파일을 받아 그 자리에 끌어다 놓기</li>
    <li>발행 설정의 태그 칸에 태그 붙여넣기 → 검토 후 발행</li></ol>
    <p>%(dl)s</p></details>
</div></div>
<div class="paper"><p class="label">아래 흰 영역이 네이버 본문에 그대로 들어갑니다. 검토하면서 고칠 곳은 붙여 넣은 뒤 에디터에서 고치세요.</p>
<div id="post">
%(body)s
</div></div>
<script>%(js)s</script>
</body></html>
""" % {
        "date": draft["date"], "wd": draft["weekday"], "num": draft["issue"], "chars": format(s["chars"], ","),
        "nimg": len(imgs), "src": draft["source_url"], "title": html.escape(draft["title"]),
        "tagcsv": html.escape(",".join(tags)), "taghash": html.escape(" ".join("#" + t for t in tags)),
        "dl": dl, "body": body_html(draft, img_base), "css": PAGE_CSS, "js": PAGE_JS,
    }


def issue_date_from_source():
    src = open(os.path.join(ROOT, "source", "morning-crit.html"), encoding="utf-8").read()
    tb = text(BeautifulSoup(src, "html.parser").find(id="page-crit").select_one(".tblock"))
    m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", tb)
    return "-".join(m.groups())


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    date = args[0] if args else issue_date_from_source()
    issue_path = os.path.join(ROOT, "issues", date + ".html")
    if not os.path.exists(issue_path):
        sys.exit("issues/%s.html 이 없습니다. build_site.py 를 먼저 실행하세요." % date)
    draft = build(open(issue_path, encoding="utf-8").read())
    img_dir = os.path.join(ROOT, "blog", "img", date)
    done, missing = render_cards(draft, issue_path, img_dir)
    for b in draft["blocks"]:
        if b["type"] == "image":
            b["rendered"] = b["file"] in done
    local = "--local" in sys.argv
    img_base = ("img/%s/" % date) if local else (SITE_URL + "blog/img/%s/" % date)
    page = page_html(draft, img_base)
    blog_dir = os.path.join(ROOT, "blog")
    for name in (date + ".html", "index.html"):
        with open(os.path.join(blog_dir, name), "w", encoding="utf-8") as f:
            f.write(page)
    print(json.dumps({"date": date, "title": draft["title"], "chars": draft["stats"]["chars"],
                      "images": len(done), "missing_images": missing,
                      "page": SITE_URL + "blog/" + date + ".html"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
