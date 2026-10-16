# 예시 체험 (스킬 상세 페이지)

IT가 익숙하지 않은 선생님이 스킬을 설치하기 전에 "무엇을 넣으면 무엇이 나오는지" 한눈에 보도록, 미리 만들어 둔 예시 하나를 보여 주는 칸이다.

- 데이터: `src/content/skill-demos/<slug>.json` (한 스킬에 파일 하나)
- 결과 파일: `public/skill-demos/<slug>/` 아래 그림(PNG·JPG·WebP) 또는 짧은 영상(MP4·WebM)
- 스키마: `src/content.config.ts` 의 `skillDemos`
- 검사: `python3 scripts/check_skills.py` (슬러그 일치, 결과 파일 존재, 3단계, 출처)
- 파일이 없는 스킬은 상세 페이지에 이 칸을 그리지 않는다. 폴더가 비어 있어도 빌드된다.

## 원칙

1. 수업 상황은 꾸민 예시다. 화면에 **"꾸민 수업 예시"** 배지가 늘 붙는다. 실제 학교·학생 이름, 학생 개인정보를 쓰지 않는다.
2. 결과는 실제로 스킬을 돌려 나온 것만 쓴다. 손으로 고친 결과를 "생성 결과"라고 하지 않는다.
3. 만든 방식을 표기한다. 에이전트가 직접 돌렸으면 `self-made`, 스킬 저장소가 제공한 예시면 `official-example` + `sourceUrl`.
4. 점수·순위·"효과 보장" 같은 문구를 쓰지 않는다. 문구는 한국어로 쓴다.
5. 회사명은 쓰지 않는다. 결과 그림 안에도 넣지 않는다.

## 파일 형식

```json
{
  "slug": "스킬 slug와 같게 (파일 이름도 같게)",
  "title": "중2 과학 — 광합성 복습 자료 만들기",
  "method": "self-made",
  "madeWith": "Claude Code + 이 스킬",
  "input": {
    "scenario": "어떤 수업 상황인지 한두 문장",
    "prompt": "선생님이 실제로 입력한 문장 그대로"
  },
  "output": {
    "type": "image",
    "path": "/skill-demos/<slug>/result.png",
    "alt": "그림을 못 보는 사람을 위한 설명",
    "excerpt": "결과 글의 일부 (선택)"
  },
  "steps": ["1단계", "2단계", "3단계"],
  "dateChecked": "YYYY-MM-DD",
  "note": "덧붙일 말 (선택)"
}
```

| 칸 | 필수 | 설명 |
|---|---|---|
| `slug` | 예 | `src/content/skills/*.json` 의 `slug` 와 같다. 파일 이름도 `<slug>.json` |
| `title` | 예 | 예시 제목. 학년·과목·할 일을 짧게 |
| `method` | 예 | `self-made`(직접 생성) 또는 `official-example`(공식 예시) |
| `madeWith` | 예 | 어떤 도구로 돌렸는지. 예: `Claude Code + 이 스킬` |
| `sourceUrl` | 공식 예시면 예 | 공식 예시의 원 출처 URL |
| `input.scenario` | 예 | 수업 상황 |
| `input.prompt` | 예 | 선생님이 넣은 문장. 줄바꿈은 `\n` |
| `output.type` | 예 | `image` 또는 `video` |
| `output.path` | 예 | `/skill-demos/`, `/skills-outputs/`, `/skills-assets/` 로 시작. 앞에 `/alternatives` 를 붙이지 않는다 |
| `output.alt` | 예 | 대체 글 |
| `output.poster` | 아니오 | 영상 첫 화면 그림 경로 |
| `output.excerpt` | 아니오 | 결과 글 발췌 (5줄 안팎) |
| `steps` | 예 | 정확히 3개. 선생님이 따라 할 수 있는 말로 |
| `dateChecked` | 예 | 결과를 만든 날 |
| `note` | 아니오 | 한계·주의점 |

결과 파일 기준: 그림은 가로 1200px 안팎·500KB 이하, 영상은 30초 이하·5MB 이하·소리 없이도 이해되게.

## 하루 1건 추가 절차

1. **고르기** — 예시 체험이 없는 스킬 하나를 고른다.
   `ls src/content/skill-demos/` 와 `ls src/content/skills/` 를 비교한다. `수업용` 이고 설치가 쉬운 스킬을 먼저 한다.
2. **상황 쓰기** — 실제 교실에서 있을 법한 상황 하나를 정한다 (학년·과목·단원·할 일). 학생 실명·개인정보는 넣지 않는다.
3. **돌리기** — 스킬 저장소 안내대로 설치하고, 정한 문장을 그대로 넣어 결과를 만든다. 넣은 문장과 결과를 고치지 않고 저장한다.
4. **결과 저장** — 화면을 캡처하거나 짧게 녹화해 `public/skill-demos/<slug>/` 에 둔다. 크기 기준을 지킨다.
5. **JSON 쓰기** — 위 형식으로 `src/content/skill-demos/<slug>.json` 을 만든다. `steps` 3개는 "무엇을 연다 → 무엇을 붙여 넣는다 → 무엇을 확인한다" 순서로 쓴다.
6. **로컬 게이트** — `python3 scripts/check_skills.py && python3 scripts/check_usagescope.py && npm run build`.
   `npm run dev -- --host 0.0.0.0 --port 4321` 로 `http://127.0.0.1:4321/alternatives/skills/<slug>/` 를 열어 칸이 보이는지 확인한다.
7. **PR** — 브랜치에서 커밋하고 PR을 연다. `ops/status-log/YYYY-MM-DD-<slug>.md` 에 한 줄 기록을 남긴다 (`STATUS.md` 공유 줄은 고치지 않는다).
8. **CI 확인** — `gh pr checks <번호>` 로 실제 통과를 확인한다. 병합은 사람이 한다.

막히면(설치 실패, API 키 필요 등) 억지로 채우지 않고 그 스킬은 건너뛴다. 이유를 해당 스킬 이슈에 코멘트로 남긴다.
