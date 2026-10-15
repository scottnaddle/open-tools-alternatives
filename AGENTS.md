# AGENTS.md — 에이전트 운영 매뉴얼

이 저장소는 **100% AI 에이전트가 운영**하는 사이트(열린도구 Alternatives)의 소스입니다.
새 에이전트가 이 프로젝트에 투입되면 **가장 먼저 이 문서를 읽고**, 다음으로 `STATUS.md`(현재 상태)를 읽으세요.

- 운영 주소: https://edtechnewsroom.com/alternatives/
- 소스 진실: `main` 브랜치 (배포는 main 빌드 결과물)
- 스택: Astro 6 + Node 22 + Zod 콘텐츠 컬렉션 + Pagefind, 하위 경로 `/alternatives/` 빌드

## STATUS.md 는 기능 PR에서 공유 줄을 고치지 않는다

`마지막 갱신` 줄과 공유 절(한 줄 요약, 콘텐츠 현황, 배포 상태, 진행 중 / 보류, 완료된 마일스톤, 다음 담당 안내)은 여러 PR이 같은 줄을 고치면 병합이 깨진다. 기능 PR은 그 줄을 그대로 둔다.

이번 작업의 기록은 새 파일 `ops/status-log/YYYY-MM-DD-<slug>.md` 에만 쓴다. 다른 PR이 만든 로그 파일은 수정하지 않는다. 파일 안에 `머리글:` 한 줄을 둔다.

머리글은 병합된 뒤에만 `python3 scripts/refresh_status_header.py` 로 `마지막 갱신` 한 줄을 고친다. 그 스크립트는 공유 절을 바꾸지 않는다. 기능 PR에서 이 스크립트를 실행하지 않는다.

## 1. 절대 원칙 (예외 없음)

1. **출처 없는 사실은 게시하지 않는다.** 모든 사실(fact)에 원 출처 URL + 확인 시각이 있어야 한다. 지어내지 않는다.
2. **미확인 값은 "확인 중", 가짜 값은 "예시 데이터"로 표시한다.** 확인 전 값을 verified로 넣는 것은 스키마가 막지만, 문구 수준의 과장도 하지 않는다.
3. **점수·인기 순위·"도움이 됐어요"를 만들지 않는다.** 법적 준수 보장 문구도 금지.
4. **usageScope(수업용/교사 개인용)를 유지한다.** 교육부 지침 개념. 학생 직접 사용 판정은 검증된 사실 없이는 불가(CI가 강제).
5. **회사명(유비온/Ubion)을 어디에도 노출하지 않는다.** (뉴스룸 브랜드 규칙)
6. **큰 작업은 계획을 먼저 보여 승인받고 시작한다.**
7. **라이선스 자동 반영(`--apply`)은 사용자가 요청할 때만 실행한다.**
8. **외부 발송(메일·메시지·알림)은 반드시 초안 → 사용자 승인 순서.** 승인 없이 보내지 않는다.
9. **비밀값은 절대 출력·커밋하지 않는다.** 서버 비밀번호 등은 GitHub 시크릿 또는 셸 환경변수로만 다룬다. 서버 IP·접속정보가 적힌 문서를 저장소에 커밋하지 않는다.
10. **"CI 통과"는 반드시 `gh pr checks <번호>`로 직접 확인한다.** 과거에 확인 없이 "통과"라고 보고했다가 실제로는 실패였던 사례가 있다. 실패한 PR을 병합한 실제 사고도 있었다(2026-10-13, PR #10).
    - 참고: 필수 검사 `build-and-check` 는 소유자가 Rulesets에서 설정한다 (`ops/BRANCH_PROTECTION.md`). 에이전트 토큰으로는 걸 수 없다. 저장소가 공개이면 무료 플랜에서 설정할 수 있다. 설정 전까지는 위 확인 절차가 방어선이고, 일일 검증 자동 병합은 이 검사가 필수일 때만 요청한다. `GITHUB_TOKEN` 이 연 PR은 `pull_request` CI를 시작하지 않으므로, 일일 검증은 `ci.yml` 을 `workflow_dispatch` 로 돌린다. PAT 는 쓰지 않는다.

## 2. 6개 에이전트 (사이트 운영 단위)

콘텐츠는 **6개 에이전트**가 순차로 처리하며, 각 단계의 입력/출력/게이트는 아래와 같다. 모든 산출물은 **GitHub Issues + PR + 데이터 파일**이며, 사람(사용자)은 검수 단계 또는 외부 발송 단계에서만 개입한다.

| # | 에이전트 | 트리거 | 입력 | 출력 | 게이트 / 핸드오프 |
|---|---|---|---|---|---|
| 1 | **발굴(Discovery)** | 매일 22:00 UTC 자동 슬롯 + 수동 | GitHub Trending·소셜·이슈 템플릿 | **이슈 1건** (소프트웨어 or 스킬 발굴 리포트) — 선정/보류 결론 포함 | 라벨 `agent/discovery` → 보류 시 close, 선정 시 `queue/research` 부여 후 2로 |
| 2 | **연구(Research)** | 이슈 큐 `queue/research` | 1의 리포트(공식 저장소·문서) | 코멘트로 출처·라이선스·학교 활용 시나리오·적합 컬렉션 결정 | 라이선스 허용목록 통과 → `agent/research` → 3으로 |
| 3 | **제조(Build)** | 라벨 `agent/research` → `agent/build` | 2의 검증 결과 | 데이터 JSON + (필요시) 자유구성 페이지 + `changes/` 변경기록 | 로컬 게이트(`check_*.py`) → PR → `agent/build` → 4로 |
| 4 | **검수(Verify)** | PR 생성·라벨 `agent/build` | 3의 PR | 검수 결과(승인/반려) | CI 실제 통과(`gh pr checks`) + 운영 원칙 점검 → 승인 시 `agent/verify` → 5로 / 반려 시 3으로 |
| 5 | **게시(Publish)** | 라벨 `agent/verify` 승인 | 4의 승인된 PR | main 반영 + 배포 | 사람이 merge → `deploy.yml`(경로 필터 푸시). 일일 검증만 자동 병합. 이슈 close + `agent/published` |
| 6 | **주간 검증(Weekly Audit)** | 매주 일요일 22:00 UTC | 기존 모든 항목의 1차 sourceUrl + GitHub release | 변경 감지 시 `changes/` 기록 + **페이지 아카이빙 표시 업데이트** | 라벨 `priority/urgent` 자동 — **운영 사이트 장애 / 유료 전환 공식 발표 / 데이터 손상** |

**흐름 다이어그램**:

```
[1 발견]  → 이슈 1건
   ↓
[2 연구]  → 코멘트 + 라벨 agent/research
   ↓
[3 제조]  → PR + 라벨 agent/build
   ↓
[4 검수]  → gh pr checks 확인 → 라벨 agent/verify
   ↓
[5 게시]  → merge + deploy + 이슈 close + 라벨 agent/published
   ↓
[6 주간]  → changes + 페이지 아카이빙 갱신
```

**상태/핸드오프 규칙**:
- **이슈 1건 = 콘텐츠 1건의 라이프사이클.** 발굴부터 게시까지 한 이슈에서 진행.
- 각 단계가 끝나면 해당 에이전트 라벨(`agent/discovery` 등)을 다음 라벨로 옮긴다.
- 반려 시 같은 이슈에서 1단계 또는 직전 단계 라벨로 되돌린다.

**에이전트 세션 시작 시**:
1. 이 문서(`AGENTS.md`) 정독
2. `STATUS.md`(현재 상태) 확인
3. GitHub Issues에서 **자신이 처리할 라벨** 이슈 확인:
   - 매일 22:00 UTC 슬롯 직후라면: `agent/discovery` 이슈 1건(자동 발행됨)
   - 2번 에이전트라면: `agent/research` 이슈
   - 등등
4. 해당 이슈의 코멘트·링크된 PR을 따라 진행

## 3. 운영 루프 (자동 스케줄)

| 루프 | 트리거 | 내용 | 담당 |
|---|---|---|---|
| 일일 자동 슬롯 | 매일 22:00 UTC — `.github/workflows/discover.yml` (cron) | **1번 에이전트의 "오늘의 후보 1건" 이슈 자동 발행** — 사람은 본문만 채움. 동시에 `daily-verifier.yml`은 tools/skills/4축 팩트 재확인. | 워크플로 (자동) |
| 주간 검증 | 매주 일요일 22:00 UTC — `.github/workflows/weekly-audit.yml` (cron) | **6번 에이전트가 기존 모든 항목의 1차 sourceUrl HEAD + GitHub releases를 재검사** → 변경 시 `changes/` 기록 + 각 페이지의 변경 이력 표시 갱신 | 워크플로 (자동) + 사람의 PR 검토 |
| 긴급 정지 | `ops/FREEZE` 파일 존재 | 모든 워크플로·검증이 즉시 중단 | (수동) |
| 배포 | `deploy.yml` — main 푸시(경로 필터) · 일일 검증 병합 후 호출 · 수동 | `ops/RUNBOOK.md`. `DEPLOY_SSH_KEY` 가 없으면 건너뜀. 키 설정은 `ops/DEPLOY_KEY_SETUP.md` | 워크플로 (키 설정 후) |

## 4. 작업 큐 = GitHub Issues + 라벨

사람(선생님·사용자)의 요청과 에이전트의 발견은 모두 이슈로 쌓는다. **두 종류의 라벨**을 사용한다:

**큐/상태 라벨** (단계가 아닌 상태):
- `queue/research` — 조사 필요 (새 대안·스킬 후보 또는 정정 접수)
- `queue/verify` — 검증 필요 (기존 팩트 재확인)
- `queue/deploy` — 배포 대기
- `status/blocked-human` — 사용자 로그인·승인 등 사람 개입 필요 (예: Threads 수집 재개)
- `priority/urgent` — 긴급 (운영 사이트 장애, 유료 전환 공식 발표 등)

**에이전트 단계 라벨** (콘텐츠 1건의 라이프사이클 추적):
- `agent/discovery` — 1번 에이전트 처리 중
- `agent/research` — 2번 에이전트 처리 중
- `agent/build` — 3번 에이전트(제조) 처리 중
- `agent/verify` — 4번 에이전트(검수) 처리 중
- `agent/published` — 5번 에이전트(게시) 완료
- `agent/verifier` — 일일 검증 PR 전용. `daily-verifier/` 브랜치와 함께 있을 때만 CI 통과 후 자동 스쿼시 병합

**발굴 슬롯 종류** (`discover.yml`이 `--label`로 붙임): `software`, `skill`.
전체 이름·색·설명은 `ops/LABELS.md`. 워크플로는 붙이기 전에 `scripts/ensure_labels.sh`로 라벨을 만든다 (`issues: write` 필요).

**이슈 템플릿 5종** (`.github/ISSUE_TEMPLATE/`):
1. **대안 요청** — 선생님/사용자가 유료 앱의 대안을 요청
2. **정보 정정** — 사이트의 틀린 정보/오래된 정보 정정
3. **스킬 제안** — 사용자가 아는 AI 스킬을 제안 (사람→에이전트 1로)
4. **스킬 발굴 리포트** — 에이전트 1(발굴)이 스킬 후보 보고
5. **소프트웨어(도구) 발굴 리포트** — 에이전트 1이 도구 후보 보고

## 5. 콘텐츠 추가·수정 절차 (6에이전트 게이트 순서)

1. **발굴** — 이슈 발행 + 리포트 작성
2. **연구** — 공식 저장소·라이선스·문서 재확인, 코멘트
3. **제조** — 데이터 JSON 작성 (스키마: `src/content.config.ts`)
   - 도구 → `src/content/tools/<id>.json` + `src/content/school-apps/<slug>.json` 연결
   - 스킬 → `src/content/skills/<owner>-<repo>.json` + (선택) `src/content/skill-pages/<slug>.html`
   - 사례/지도안/리뷰 → `src/content/{cases,lessons,reviews}/<id>.json` + 자유구성 페이지
4. **로컬 게이트**: `python3 scripts/verify.py && python3 scripts/check_usagescope.py && python3 scripts/check_skills.py && python3 scripts/check_axis_pages.py`
5. **빌드**: `npm run build`
6. **PR** → **`gh pr checks`로 CI 실제 통과 확인** → **병합** (4번 검수가 함께 수행)
7. **게시** — 콘텐츠·디자인·발굴 PR은 사람이 병합한다. main에 사이트 파일이 들어가면 `deploy.yml`이 배포한다(SSH 키가 있을 때). 일일 검증 PR만 자동 병합되며, 그 병합은 `deploy-after-verifier.yml`이 배포를 호출한다. 절차는 `ops/RUNBOOK.md`.
8. **상태 기록** — `STATUS.md` 공유 줄을 고치지 않고 `ops/status-log/` 에 남긴다. 머리글은 병합 뒤에만 고친다. 위 「STATUS.md 는 기능 PR에서 공유 줄을 고치지 않는다」.

## 6. 긴급 정지 (FREEZE)

저장소 루트에 `ops/FREEZE` 파일이 있으면 모든 워크플로(일일/주간/배포)가 즉시 중단된다.
서비스 종료·유료 전환 소식 대응 등 "게시를 멈춰야 하는 상황"에서 이 파일을 커밋하고, 해제 시 삭제한다.
파일 안에 중단 사유와 날짜를 한 줄 적는다.

## 7. 하지 말 것

- `daily-verifier`의 PR을 검토 없이 병합하지 않는다 (C등급 24시간 재확인 규칙 유지)
- nginx · Ghost · Cloudflare · DNS 설정을 변경하지 않는다 (배포는 정적 파일 교체만 — `ops/RUNBOOK.md`)
- 기존 검증 규칙(Zod refine, check 스크립트)을 약화시키지 않는다
- main에 직접 커밋하지 않는다 — PR + CI 필수
- 사용자가 읽는 문구를 영어로 쓰지 않는다 (현장 대상 한국어 유지)
- 4 navLinks 회귀(2026-10-13 회귀) 재발 방지: 푸터·카드·헤더의 매핑은 4개 항목 이상일 때 직접 명시(getStaticPaths는 `for` 루프 + 타입 명시) — 자세한 패턴은 코드 코멘트 참고
- 기능 PR에서 `STATUS.md`의 `마지막 갱신` 줄과 공유 절을 고치지 않는다. 기록은 `ops/status-log/`에만 추가한다.

## Cursor Cloud specific instructions

- 개발 서버는 `npm run dev -- --host 0.0.0.0 --port 4321`. `astro.config.mjs`의 base 기본값이 `/alternatives`라서 로컬 주소는 `http://127.0.0.1:4321/alternatives/` 이다. `/` 는 404다.
- 의존성은 `npm ci`(lockfile). Node.js 22 이상이 `/usr/local/bin`에 있어야 한다. Python 게이트(`check_usagescope.py`, `check_skills.py`, `check_axis_pages.py`, `check_links.py`)는 표준 라이브러리만 쓴다. `check_links.py`는 `npm run build` 이후 `dist/`를 본다.
- `scripts/verify.py`와 `scripts/daily_verifier.py`는 GitHub API를 호출하고 콘텐츠 JSON을 고칠 수 있다. 환경이 뜨는지 확인할 때는 실행하지 않는다.
