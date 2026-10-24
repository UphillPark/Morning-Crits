# 5면 · Mood Screen 지침

루틴 B(Morning Crit · Seminar)가 `prompts/routine-b.md` 3절에서 이 파일을 읽고 그대로 따른다. 5면은 영어로 쓰고, 본문(이미지·표·프롬프트 제외)은 300~450 words.

목적은 두 가지다. (1) 렌더링과 생성형 AI 프롬프팅에 쓸 시각 어휘를 무의식적으로 쌓는다. (2) 매일 프롬프트로 이미지를 실제로 만들어 보고, 엄격하게 채점하고, 그 피드백으로 다음 호의 프롬프트를 고친다(architecture representation using generative AI 실력 기르기).

형식은 `prompts/seminar-example.html`의 `#page-screen`을 따른다. 견본의 문장은 형식 예시일 뿐이니 베끼지 않는다.

이 파일의 `python3 scripts/…` 명령은 저장소 루트를 작업 디렉터리로 두고 **적힌 형태 그대로** 실행한다. 앞에 `cd …&&`, 환경 변수, 파이프를 붙이지 않는다. 저장소의 `.claude/settings.json` 허용 규칙이 이 형태만 허용한다. 처음 실행할 때 `pip install pillow numpy beautifulsoup4 lxml`.

## 1. 작품 고르기
- 매일 한 작품: 영화, 회화, 다큐멘터리, 사진(사진가·사진집·사진전), 때때로 판화·드로잉. 고전과 교양이 되는 작품을 고르고 지금 열리는 전시나 신작은 고르지 않는다.
- `issues/index.json`의 최근 7일 screen_medium을 보고 한 매체가 한 주에 3번을 넘지 않게 하고, 시대·지역·작가를 고르게 섞는다(아시아·한국 작품, 무성영화, 흑백, 실험영화 포함). 같은 작품(screen_work)은 다시 고르지 않는다. 회화를 고르는 날은 3면의 시대를 느슨하게 따라가도 좋다(억지로 맞추지 않는다).
- data-medium(Film/Painting/Documentary/Photography/Print), data-work("원제 또는 영어 제목 (연도)").
- 결말과 반전을 쓰지 않는다. 스트리밍 제공 여부를 쓰지 않는다. 확인하지 않은 촬영 장비·렌즈·장면을 사실처럼 쓰지 않는다.

## 2. 구성
이미지 1~2장 → 제목(원제 · 영어 · 한국어), 작가·감독, 연도, 국가, 러닝타임(확인된 경우) → Why this one(이 작품에서만 얻을 수 있는 시각 경험, 2~3문장) → Three things to watch for(다음 범주 중 이 작품에서 두드러지는 셋: Composition / Framing, Camera position / Lens / Perspective, Natural and artificial light, Colour palette / Grading, Materiality / Texture, Atmosphere / Weather, Spatial depth, Movement / Duration / Rhythm, Human scale / Occupation, Architecture / Landscape / Urban condition) → **Your frame · generative test**(3절) → 단어 박스 → 푸터.

ONE QUESTION은 더 이상 싣지 않는다.

## 3. Your frame · generative test
`section.gentest` 하나. 4행으로 짠다.

| 행 | 내용 |
|---|---|
| 1 (병합) | YOUR FRAME: example keywords 3개(`·`로 구분) + 그 분위기를 묘사한 프롬프트 한 줄(`pre.prompt`) |
| 2 | `figure.gen` 3칸: A · B1 · B2 이미지(또는 실패 표기) + 점수 한 줄 |
| 3 | `div.gprompt` 3칸: A · B1 · B2 프롬프트 |
| 4 (병합) | 점수표(`table.gscores`) + What worked / What didn't match, and why / Next issue's prompt changes + 채점 방식·Drive 폴더 한 줄 |

### 3.1 세 장의 역할
- **A · Reproduction**: 원본 장면의 구도·요소·색·빛을 유지하면서, 노골적이지 않은 단어로 원본과 최대한 비슷하게 만든다.
- **B1, B2 · Mood transfer**: 원본과 **전혀 다른 장면**(다른 대상·다른 구도)인데, 보는 순간 "그 작품 같다"고 느껴지게 만든다. 가져가는 것은 장르, 테마, 컬러 팔레트, 시대감, 화면 문법(대칭, 미니어처 느낌, 롱테이크의 정적 등). 원본의 장면·대상·구도는 가져가지 않는다. 반드시 건물이나 건축적 공간이 들어간다. 한국식 실무 렌더샷이 아니라 Midjourney · AA School 식 재현을 목표로 한다.
  - 예: 그날 작품이 *The Grand Budapest Hotel*이면, A는 명장면 재현, B는 대칭 정면의 파스텔 산악 요양원 단면 드로잉이나 분홍 케이블카 정거장 컨셉아트처럼 그 장면과 무관한 건축 이미지.

### 3.2 B의 종류: 4개 조합 로테이션
B1은 {실사 사진 Photograph, 컨셉아트 Concept art} 중 하나, B2는 {건축 드로잉 Architectural drawing, 오브제·다이어그램 Object / Diagram} 중 하나.

| combo | B1 | B2 |
|---|---|---|
| 1 | Photograph | Architectural drawing |
| 2 | Photograph | Object / Diagram |
| 3 | Concept art | Architectural drawing |
| 4 | Concept art | Object / Diagram |

- 오늘 combo = ((오늘 tblock Issue 번호 − 1) mod 4) + 1. 요일이 아니라 호수로 돌린다(일요일 휴간 때문에).
- 그날 작품과 조합이 정말 맞지 않을 때만 한 칸을 바꾸고, `data-combo`에 실제로 쓴 번호를, screen-log.json의 `combo_swap`에 이유를 적는다.
- `figure.gen`과 `div.gprompt`의 B 칸에 `data-kind`(위 표의 영어 이름)를 단다.

### 3.3 원본 이미지 확보 (채점용)
- 미술관 오픈액세스(Cleveland, Met, Rijksmuseum, Art Institute of Chicago, National Gallery of Art 등)를 먼저 찾고, 없을 때 Wikimedia Commons. 컨테이너에서 Wikimedia가 429로 막히는 일이 잦다.
- 영화·다큐는 라이선스가 확인된 공식 스틸·포스터를 찾는다. 찾지 못하면 그날은 **원본 없음**: A는 생성하되 원본 비교 항목(Style, Composition)은 채점하지 않고, B의 Mood는 참고 점수로만 적는다(4.4).
- 원본은 스크래치 폴더에 받는다. 저장소에 넣지 않는다.

### 3.4 금지어 (`data-ban`)
- `section.gentest`의 `data-ban`에 그날 프롬프트에서 쓰면 안 되는 말을 `|`로 이어 적는다: 작품명(원제·영어·한국어·약칭), 작가·감독·사진가 이름(원어·로마자·한자·성만), 등장인물·배우 이름, 작품 고유의 장소명·건물명·브랜드·소품 이름, 시리즈·유파 이름 중 원작을 곧바로 지목하는 것.
- 공통 금지 표현(in the style of, style of, inspired by, à la, homage to, recreation of, copy of)은 검사 스크립트가 따로 막는다.
- 이 조건은 피드백에 따라 바뀔 수 있다. 바뀌면 이 파일을 고친다.

### 3.5 프롬프트 쓰기
- 먼저 `prompts/screen-log.json`의 최근 7개 항목에서 `next`(다음 호 개선안)와 점수가 낮았던 축을 읽고, 오늘 프롬프트에 반영한다. 반영한 개선안은 로그의 `applied`에 적는다.
- 세 프롬프트 모두 example keywords 3개를 그대로 포함한다.
- 단어 수: A 80 words 이하, B1·B2 각 60 words 이하(`<del>` 안의 말은 세지 않는다). 나열이 아니라 압축하는 연습이다.
- A에서 노골적인 말을 피했다면 그 자리를 `<del>피한 말</del><ins>바꿔 쓴 말</ins>`로 표시하고, 아래에 `<p class="avoid">Avoided N explicit terms</p>`를 단다. `<del>` 안의 말은 실제로 모델에 보내지 않는다.
- B 프롬프트 아래 `dl.carry`에 원본에서 가져온 분위기 요소 → B에서 번역한 방식을 2~4쌍 적는다.
- 감점되는 습관(4.3 Prompt 축): 원본 요소를 화면 위치까지 1:1로 나열하기, 서명·낙관·제목 표식 같은 그 작품만의 표식 지정하기, 제한 길이를 꽉 채운 장황함, 어느 그림에나 붙는 상투어(masterpiece, stunning, 8k, highly detailed).
- 이미지 비율은 원본에 가까운 값(2:3, 3:2, 1:1, 3:4, 4:3, 9:16, 16:9)을 고른다. B는 자유.

### 3.6 생성
각 칸마다 프롬프트(`<del>` 부분을 뺀 글)를 스크래치 파일로 저장하고 실행한다.

```
python3 scripts/gen_image.py <prompt.txt> <scratch>/YYYY-MM-DD-a.png --aspect 2:3
```

결과 JSON의 status에 따라:
- `ok`: 다음 칸으로.
- `refused`: 표현을 순화해(폭력·노출·실존 인물 묘사를 걷어내고) **한 번만** 다시 시도한다. 또 refused면 그 칸은 `data-status="refused"`, 표기 `생성 거부 · refused by the safety filter`.
- `quota`: 크레딧이 떨어졌거나 결제가 꺼졌다. **남은 칸도 시도하지 않고** 모두 `data-status="quota"`, 표기 `크레딧 소진 · credit used up`. 마무리에서 PushNotification을 보낸다.
- `error`: 한 번만 다시 시도한다. 또 error면 `data-status="error"`, 표기 `생성 실패 · generation failed`, 요약에 detail을 적는다.
- 하루 생성 호출은 재시도를 포함해 최대 6번. 이미지가 하나도 안 나와도 신문은 멈추지 않는다. 실패한 칸에는 `<img>`를 넣지 않고 `div.gfail`에 표기를 쓴다(`figure.gen noimg`).
- 결과 JSON의 model과 usage를 로그에 남긴다. 첫 모델이 404면 스크립트가 다음 모델로 넘어간다. 모델이 바뀐 날은 로그의 `model`로 구분된다.

### 3.7 압축 · 보관
성공한 이미지마다:

```
python3 scripts/screen_image.py compress <scratch>/YYYY-MM-DD-a.png assets/screen/YYYY-MM-DD-a.webp
```

- 발행용 압축본은 `assets/screen/YYYY-MM-DD-{a,b1,b2}.webp`(WebP가 안 되면 스크립트가 .jpg로 만든다. 결과 JSON의 file 이름을 그대로 쓴다). img src는 `https://uphillpark.github.io/Morning-Crits/assets/screen/<파일 이름>`.
- 원본 PNG는 Drive `mood screen` 폴더에 올린다(한 번에):

```
python3 scripts/upload_drive.py <scratch>/YYYY-MM-DD-a.png <scratch>/YYYY-MM-DD-b1.png <scratch>/YYYY-MM-DD-b2.png --month YYYY-MM
```

- 결과의 url을 각 figcaption의 `original` 링크로 쓴다. 업로드가 실패하면 링크 없이 두고, 요약에 적고, 마무리에서 PushNotification을 보낸다. 업로드 실패로 신문을 멈추지 않는다.
- figcaption: `<b>A · Reproduction</b>`(B는 `<b>B1 · Photograph</b>` 등) · Generated · YYYY.MM.DD · original 링크.

### 3.8 측정값
원본이 있으면:

```
python3 scripts/screen_image.py compare <원본> <scratch>/YYYY-MM-DD-a.png <scratch>/YYYY-MM-DD-b1.png <scratch>/YYYY-MM-DD-b2.png
```

palette_de(낮을수록 같은 팔레트)와 layout_r(높을수록 같은 구도)을 점수표와 로그에 적는다. 이 숫자는 채점관의 근거이지 점수가 아니다. A는 layout_r이 높을수록, B는 layout_r이 **낮을수록** 목표에 맞다.

## 4. 채점

### 4.1 축
| 이미지 | 축 | 묻는 것 |
|---|---|---|
| A | Style | 원본의 매체감·색·빛·질감이 얼마나 옮겨졌나 |
| A | Composition | 화면 구도와 요소 배치가 원본에서 얼마나 변하지 않았나 |
| A | Prompt | 노골적인 단어 없이, 적은 정보로 닮게 했나 |
| B | Mood | 원본을 모르는 사람도 "그 작품 같다"고 느낄 분위기(장르·팔레트·시대감·화면 문법)가 옮겨졌나 |
| B | Independence | 원본과 다른 장면인가(대상·구도를 가져오지 않았나) |
| B | Architecture | 건축 재현으로서 완성도: 공간이 읽히나, 스케일·재료·빛이 설득력 있나, 그 종류(사진/컨셉아트/드로잉/오브제·다이어그램)의 문법을 지켰나 |
| B | Prompt | A와 같은 기준 |

평균 = 그 이미지에서 확정된 축들의 산술평균(소수 첫째 자리).

### 4.2 채점관 5명과 과반수 규칙
- 축마다 관점이 다른 채점관 5명을 둔다. 매일 같은 다섯을 쓴다.
  - Style · Mood: 판화·회화 보존 전문가, 컬러리스트, 촬영감독, AA 튜터, 생성형 AI 프롬프트 엔지니어
  - Composition · Independence: 사진 편집자, 영화 편집자, 레이아웃 디자이너, AA 튜터, 미술사학자
  - Architecture: AA 다이플로마 튜터, 실무 건축가, 건축 사진가, 컨셉 아티스트, 구조 엔지니어
  - Prompt: 프롬프트 엔지니어, 저작권 검토자, 카피 에디터, AA 튜터, 생성형 AI 연구자
- 이미지 축(Style, Composition, Mood, Independence, Architecture)의 채점관은 **이미지와 원본만 보고 프롬프트를 보지 않는다**(프롬프트를 알면 후해진다). Prompt 축의 채점관은 프롬프트, data-ban, 원본 설명을 본다.
- 각 채점관은 4.3의 기준점에 맞춰 0~100 정수로 독립 채점하고, 근거를 한 줄씩 남긴다(로그에만).
- 판정: 5개 점수의 중앙값을 구하고, **3명 이상이 중앙값 ±5 안에 있으면** 중앙값을 확정 점수로 쓴다. 아니면 그 축은 **Held**로 두고 지면에 `Held (최저–최고)`를 적으며 평균에서 뺀다.
- 측정값(palette_de, layout_r)과 크게 어긋나는 점수(예: palette_de 15 이상인데 Style 85 이상)는 그 채점관이 근거를 다시 쓴다.

### 4.3 기준점 (엄격하게)
- **90**: 나란히 놓고도 차이를 찾기 어렵다(Prompt: 짧고 정확하며 고유명사 없이 원작을 떠올리게 한다).
- **75**: 핵심은 맞고 두세 군데가 분명히 다르다(Prompt: 위치 나열이 일부 있거나 상투어가 하나 있다).
- **60**: 같은 계열이지만 다른 그림으로 읽힌다(Prompt: 요소를 1:1로 늘어놓았거나 작품 고유 표식을 지정했다).
- **40 이하**: 목표와 다른 방향이다.
- 첫 시험(2026-10-20) 점수 80점대는 후했다. 70점대 중반을 "좋은 날"의 기준으로 삼는다.

### 4.4 원본이 없는 날
A의 Style·Composition은 `Not scored · no reference image`, B의 Mood는 `(78) reference only`처럼 괄호로 적고 평균에서 뺀다. Prompt, Independence(원본 설명 기준), Architecture는 채점한다.

### 4.5 피드백
- What worked: 2~3개. 어떤 단어·구조가 어떤 결과를 냈는지.
- What didn't match, and why: 2~4개. 무엇이 달랐고 어떤 단어(또는 빠진 단어) 때문인지.
- Next issue's prompt changes: 2~4개. 다음 호에 바로 쓸 수 있는 구체적인 단어 교체·추가·삭제.

## 5. 기록장 `prompts/screen-log.json`
배열 맨 끝에 오늘 항목 하나를 붙인다(지난 항목은 고치지 않는다).

```json
{
  "date": "YYYY-MM-DD", "issue": 16, "work": "data-work 값", "medium": "Painting",
  "combo": 2, "combo_swap": null, "model": "gemini-3.1-flash-lite-image",
  "reference": true, "ban": ["…"], "keywords": ["…", "…", "…"], "applied": ["지난 개선안 중 반영한 것"],
  "images": [
    {"slot": "a", "kind": "Reproduction", "status": "ok", "words": 72,
     "prompt": "모델에 보낸 글 그대로", "avoided": [["피한 말", "바꿔 쓴 말"]],
     "metrics": {"palette_de": 7.9, "layout_r": 0.61},
     "scores": {"style": {"judges": [80, 82, 81, 70, 84], "final": 81, "held": false}, "composition": {}, "prompt": {}},
     "avg": 75.0, "drive_url": "…", "usage": {}}
  ],
  "worked": ["…"], "mismatch": ["…"], "next": ["…"]
}
```

## 6. 확인
- `python3 scripts/check_fragment.py source/seminar/YYYY-MM-DD.html`이 5면의 생성형 테스트도 검사한다: 세 칸과 status, ok 칸의 이미지 파일이 assets/screen/에 있는지, 프롬프트 단어 수, data-ban과 공통 금지 표현, example keywords 포함 여부, 점수표. problems가 있으면 고치고 다시 실행한다. 금지어에 걸린 프롬프트는 고쳐서 **다시 생성**한다(하루 6번 한도 안에서). 한도를 넘으면 그 칸 프롬프트만 고치고 이미지는 그대로 둔 채 요약에 적는다.
- 5면의 시트당 링크 3개 제한은 본문 링크에만 적용한다. 생성 이미지의 original 링크와 Drive 폴더 링크는 세지 않는다.

## 7. 커밋에 넣을 것
조각 `source/seminar/YYYY-MM-DD.html`, `assets/screen/YYYY-MM-DD-*.webp`(또는 .jpg), `prompts/screen-log.json`. 원본 PNG와 원본 작품 이미지는 커밋하지 않는다.

## 8. 요약과 알림
- 요약에 적는다: 오늘 combo, 세 칸의 status와 평균 점수, Held가 된 축, 금지어·단어 수 검사 결과, Drive 업로드 결과, 사용 모델과 usage.
- PushNotification: `quota`가 나온 날("Mood Screen: Gemini 크레딧 소진 — AI Studio에서 충전 필요"), Drive 업로드가 실패한 날, 세 칸 모두 실패한 날.
