# Morning Crit

AA Diploma와 졸업전시를 준비하며 매일 아침 읽는 런던·유럽 건축 조간.

- 1면 **Morning Crit** (영어): 런던·유럽 건축계 뉴스와 담론, 오늘의 크릿 질문
- 2면 **Thesis Desk** (한국어): 건축 밖의 국내·해외 이슈를 졸업전시 주제로 번역
- 3면 **Daily Symposium** (한국어): 서양·동아시아 사상사 시대순 강의, 156회 (`curriculum/philosophy.json`)
- 4면 **Unit Brief** (영어): AA → RCA → Bartlett 유닛 브리프 밑의 이론 (`curriculum/units.json`)
- 5면 **Mood Screen** (영어): 영화·회화·다큐·사진 고전 한 편씩, 시각 어휘 쌓기
- **Word Desk**: 다섯 면의 단어 박스를 모은 탭 (IELTS 7.0 / AA Crit). 일요일은 Weekly Review + Word Quiz

웹: https://uphillpark.github.io/Morning-Crits/ · 지난 호: [archive.html](https://uphillpark.github.io/Morning-Crits/archive.html)

## 구조

| 경로 | 내용 |
| --- | --- |
| `source/morning-crit.html` | 그날 호의 원본 (Claude 아티팩트와 같은 HTML) |
| `index.html` | 오늘 호 |
| `issues/YYYY-MM-DD.html` | 날짜별 보관본 |
| `issues/index.json` | 호별 메타데이터 |
| `archive.html` | 지난 호 목록 |
| `source/seminar/YYYY-MM-DD.html` | 세미나 루틴이 만든 3~5면 조각 (일요일은 복습호 조각) |
| `source/sunday.html` | 일요일 복습호 (평일 원본은 그대로 둔다) |
| `curriculum/` | 3면 시간표, 4면 유닛 지도 |
| `prompts/` | 두 루틴의 지침과 조각 형식 견본 |
| `scripts/assemble.py` | 1·2면 원본에 3~5면 조각을 합치고 탭과 Word Desk를 만든다 (`--sunday`: 복습호) |
| `scripts/check_fragment.py` | 세미나 조각의 구조와 링크를 검사한다 |
| `scripts/build_site.py` | 원본으로 index·보관본·아카이브를 만든다 |
| `scripts/to_notion_md.py` | 원본을 Notion 마크다운(`build/notion.md`)과 속성(`build/notion-meta.json`)으로 바꾼다 |
| `scripts/blog_post.py` | 그날 호로 네이버 블로그 붙여넣기 페이지(`blog/YYYY-MM-DD.html`, `blog/index.html`)와 이미지 카드(`blog/img/YYYY-MM-DD/`)를 만든다 |
| `blog/` | 날짜별 블로그 붙여넣기 페이지. 웹: https://uphillpark.github.io/Morning-Crits/blog/ |

## 매일 발행 순서

두 루틴이 나눠 만든다. 05:30 KST 세미나 루틴(`prompts/routine-b.md`)이 3~5면 조각을 `source/seminar/`에 푸시하고, 07:07 KST Morning Crit 루틴(`prompts/routine-a.md`)이 1·2면을 만든 뒤 합쳐서 발행한다.

```bash
python3 scripts/assemble.py        # 1·2면 + 3~5면 조각 + Word Desk (일요일: --sunday → source/sunday.html)
python3 scripts/build_site.py      # 사이트 갱신 (일요일: source/sunday.html)
python3 scripts/blog_post.py       # 네이버 블로그 붙여넣기 페이지 생성
python3 scripts/to_notion_md.py    # Notion용 마크다운 생성
git add -A && git commit -m "Issue YYYY-MM-DD" && git push
```

Notion에는 Supply › Morning Crit_db에 같은 날짜의 페이지가, Supply › Word Bank_db에 그날의 단어가 추가된다.

## 네이버 블로그

매일 https://uphillpark.github.io/Morning-Crits/blog/ 를 열어 검토한 뒤, **제목 복사** → 네이버 제목 칸, **본문 복사** → 본문 칸에 Ctrl+V, **태그 복사** → 발행 설정 태그 칸. 사진이 빠지면 페이지의 "이미지 따로 받기"에서 받아 끌어다 놓는다. 발행은 직접 한다.
