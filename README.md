# Morning Crit

AA Diploma와 졸업전시를 준비하며 매일 아침 읽는 런던·유럽 건축 조간.

- 1면 **Morning Crit**: 런던·유럽 건축계 뉴스와 담론, 오늘의 크릿 질문
- 2면 **Thesis Desk**: 건축 밖의 국내·해외 이슈를 졸업전시 주제로 번역

웹: https://uphillpark.github.io/Morning-Crits/ · 지난 호: [archive.html](https://uphillpark.github.io/Morning-Crits/archive.html)

## 구조

| 경로 | 내용 |
| --- | --- |
| `source/morning-crit.html` | 그날 호의 원본 (Claude 아티팩트와 같은 HTML) |
| `index.html` | 오늘 호 |
| `issues/YYYY-MM-DD.html` | 날짜별 보관본 |
| `issues/index.json` | 호별 메타데이터 |
| `archive.html` | 지난 호 목록 |
| `scripts/build_site.py` | 원본으로 index·보관본·아카이브를 만든다 |
| `scripts/to_notion_md.py` | 원본을 Notion 마크다운(`build/notion.md`)과 속성(`build/notion-meta.json`)으로 바꾼다 |
| `scripts/blog_post.py` | 그날 호로 네이버 블로그 붙여넣기 페이지(`blog/YYYY-MM-DD.html`, `blog/index.html`)와 이미지 카드(`blog/img/YYYY-MM-DD/`)를 만든다 |
| `blog/` | 날짜별 블로그 붙여넣기 페이지. 웹: https://uphillpark.github.io/Morning-Crits/blog/ |

## 매일 발행 순서

```bash
python3 scripts/build_site.py      # 사이트 갱신
python3 scripts/blog_post.py       # 네이버 블로그 붙여넣기 페이지 생성
python3 scripts/to_notion_md.py    # Notion용 마크다운 생성
git add -A && git commit -m "Issue YYYY-MM-DD" && git push
```

Notion에는 Supply › Morning Crit_db에 같은 날짜의 페이지가 추가된다.

## 네이버 블로그

매일 https://uphillpark.github.io/Morning-Crits/blog/ 를 열어 검토한 뒤, **제목 복사** → 네이버 제목 칸, **본문 복사** → 본문 칸에 Ctrl+V, **태그 복사** → 발행 설정 태그 칸. 사진이 빠지면 페이지의 "이미지 따로 받기"에서 받아 끌어다 놓는다. 발행은 직접 한다.
