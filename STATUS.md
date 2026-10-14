# STATUS.md — 현재 상태 스냅샷

> **에이전트 필독**: 이 파일은 프로젝트의 살아있는 상태입니다. 작업을 마칠 때마다 갱신하세요.
> 마지막 갱신: 2026-10-14 18:30 (Asia/Tashkent) — 워크플로 YAML·daily-verifier PR 실패 대응, 공개 화면 P0(원시값·예시·빈 기능표·폼)

## 한 줄 요약

오픈소스 대안(15개 도구) + 오픈스킬(28개) 2축으로 운영 중. 소스 진실은 `main`, 운영 사이트는 main 빌드 결과물.
**6에이전트 운영 시스템** (발굴/연구/제조/검수/게시/주간) 도입 완료 — 매일 22:00 UTC 자동 슬롯 + 매주 일요일 22:00 UTC 주간 검증.

## 콘텐츠 현황 (2026-10-13 기준)

| 항목 | 수량 | 비고 |
|---|---|---|
| 도구(tools) | 15 | 라이선스 verified 11건 |
| 학교 앱(school-apps) | 9 | 대안 링크 15건 |
| 오픈스킬(skills) | 28 | 자유구성 소개 페이지 3개(PhysicsOS=데모형, Hallmark=이미지형, Huashu Design=영상형) + 레거시 미리보기 4개 — 나머지는 발굴·재구성 루프로 순차 제작 |
| 변경 기록(changes) | 34 | daily-verifier가 매일 추가 |

- 라이선스 제안 대기(pendingLicense): **GIMP, Inkscape, 7-Zip, NanaZip** — 24시간 재확인 통과 시 daily-verifier가 approved 처리. `--apply`는 사용자가 요청할 때만.
- 미검증 필드: OpenCut 5개 필드 등 일부 도구의 v4 필드(학생데이터·계정·연령)는 여전히 확인 중.
- 팩트 나이: 주 1회 `python3 scripts/fact_age.py`로 90일 경과 팩트 확인.

## 배포 상태

- 운영: https://edtechnewsroom.com/alternatives/ (뉴스룸 VPS 정적 호스팅)
- **2026-10-14 14:08 (Asia/Tashkent): main 8337fe1 배포 완료** — 디자인 개선안 v2(PR #24) + CSS 캐시 무효화(PR #25). deploy.yml 수동 실행(run 38539994031), 헬스체크에 "운영 style.css = dist/style.css" 통과, 서버 백업 `alternatives.bak-20261014-090744`
- 2026-10-13 22:31 (Asia/Tashkent): main 기준 배포 완료 — deploy.yml 수동 실행(run 38439208024), 헬스체크 5종 200, 서버 백업 `alternatives.bak-20261013-173103`
- 시크릿 설정 완료: `GHOST_SERVER_HOST`, `GHOST_SERVER_ROOT_PASSWORD` → 이제 `gh workflow run deploy.yml --ref main` 한 줄로 배포 가능
- 배포 후 외부 확인됨: 이달의 도구 문구 교정·장면 카드 힌트 수정이 운영에 반영
- (소소한 이슈) 워크플로 checkout 정리 단계에서 `lucian-uxui`가 .gitmodules 없는 gitlink라는 경고 출력 — 배포에는 영향 없음, 추후 정리
- **사고 기록(2026-10-13)**: 첫 자동화 배포(22:31)가 ASTRO_BASE 누락으로 루트 절대경로 빌드 → CSS 전면 404, UI 붕괴. PR #8으로 base 기본값 '/alternatives' 반전 + 헬스체크에 "HTML 참조 CSS 실제 로드"·"루트 절대링크 감지" 추가, 22:39 재배포로 완치. 교훈: URL 200만 있는 헬스체크는 콘텐츠 깨짐을 못 잡는다
- **사고 기록(2026-10-14)**: 디자인 v2 배포(13:50, run 38538033688) 직후 Cloudflare가 `/alternatives/style.css`를 이전 판으로 캐시(`max-age=14400`, `cf-cache-status: HIT`)해 새 HTML + 예전 CSS 조합으로 홈 표·아이콘이 깨짐(약 17분). 헬스체크는 CSS 200만 확인해 통과. PR #25로 ① `Base.astro`가 `style.css?v=<내용 해시>`를 참조(CSS가 바뀌면 주소도 바뀜) ② `deploy.sh`가 쿼리 붙은 에셋도 검사하고 운영 style.css 내용을 `dist/style.css`와 비교(다르면 실패·롤백)하도록 고쳐 14:08 재배포로 복구. 교훈: `public/`의 해시 없는 고정 파일은 CDN 캐시에 갇힌다 — 바꿀 일이 있으면 해시 쿼리를 붙이거나 Astro 번들(`_astro/`)로 옮길 것

## 진행 중 / 보류

- [ ] Threads 좋아요 기반 스킬 수집 — 인스타그램 SMS 2단계 인증 문제로 보류. **사용자가 로그인 가능할 때 재개** (`status/blocked-human`)
- [ ] 오픈스킬 자유구성 페이지 25개 중 3개 완료 — 발굴 리포트 이슈 → 재구성 루프로 순차 제작
- [ ] 선생님 페이지 장면 카드 / 앱 페이지 "어디서 쓰나요?" 데이터 — `src/data/scenes.json` 분리 완료, 데이터 고도화는 진행 중
- [ ] 제안 폼 실동작화 (현재 정적) — 4단계 과제: 서버리스 → 이슈 접수 연결
- [x] GitHub 시크릿 설정 완료 (2026-10-13) — 배포 자동화 가동
- [ ] 뉴스레터 초안·승인 흐름 (외부 발송은 반드시 초안 → 승인)
- [x] **6에이전트 시스템 도입 (2026-10-14)** — AGENTS.md + ops/RESEARCH.md 6에이전트 명세, 라벨 10종(agent/* 5 + queue/* 3 + status/* 1 + priority/* 1), 이슈 템플릿 5종, `.github/workflows/discover.yml` 매일 22:00 UTC 자동 슬롯 — **PR A(이번)**
- [x] **워크플로 YAML·P0 공개 화면 (2026-10-14)** — discover/weekly-audit 파싱 복구(schedule+수동만), daily-verifier는 같은 날 브랜치 충돌을 처리하고 PR 생성 실패 시 설정 안내와 함께 실패. 도구·비교·변경 이력의 원시값(active, github-api 등)을 교사 문구로. 확인된 칸이 없는 기능표는 한 줄. 제안 폼은 GitHub 이슈, 뉴스레터는 준비 중. example 현장사례는 공개 빌드에 없음. **소유자가 Settings > Actions > General > Workflow permissions > Allow GitHub Actions to create and approve pull requests 를 켜야 daily-verifier PR이 만들어진다.**
- [ ] `.github/workflows/weekly-audit.yml` (6번 에이전트 자동) + 페이지 변경 이력 아카이빙 표시 — 워크플로 파일은 파싱되게 고쳤고, summary 브랜치 push는 `contents: write`가 필요. 페이지 아카이빙 표시는 도구 페이지 하단에 이미 있음
- [ ] 오픈스킬 자유구성 페이지 22개(나머지) + 4축 사례/지도안/리뷰 백필
- [x] **디자인 개선안 v2 (2026-10-14, PR #24)** — 홈 표형 목록(기기별 가능 여부 열), 학교 앱 상세 재구성, 색 토큰 통일(강조색 `#17694A`), 메뉴 "학습SW" → "대안 찾기", 대안 `can`/`cannot` 스키마(CapCut만 미검증 조사값). 화면 캡처 `design/v2-*.png`
- [ ] 디자인 v2 남은 일(PR #24 체크리스트): `can`/`cannot` 나머지 8개 앱 채우기(출처와 함께), 도구 상세·비교·오픈스킬·소개 레이아웃 v2화, 홈 표 앱 순서 기준을 데이터로, 화면 캡처 비교 CI, 히어로 "매일 다시 확인" 문구와 실제 주기 대조
- [ ] Cloudflare에서 `/alternatives/` 정적 파일 캐시 규칙 점검(HTML·CSS 캐시 기간) — Cloudflare 접근 권한 필요 (`status/blocked-human`)

## 완료된 마일스톤

- PR #1 (2026-10-13): 기반 구축 — Astro 6, Zod 팩트 스키마, 씨앗 데이터
- PR #2 (2026-10-13): 페이지 + Pagefind 검색
- PR #3 (2026-10-13): daily-verifier, usageScope 검사, 검증 필드 93개
- PR #4 (2026-10-13): 하위경로 설정, 리디자인(Lucian), 오픈스킬·소개 페이지, 3개 메뉴
- PR #24 (2026-10-14): 디자인 개선안 v2
- PR #25 (2026-10-14): style.css 캐시 무효화 + 배포 헬스체크 CDN 예전 CSS 검사
- 에이전트 운영 인프라 (2026-10-13): AGENTS.md, 이 파일, ops/, 스킬 라이선스 게이트, 이슈 큐, 배포 자동화, 팩트 TTL, 오픈스킬 발굴→재구성 2단계 루프(자유구성 쇼케이스)

## 다음 담당 에이전트를 위한 안내

1. `AGENTS.md`(6에이전트 운영 매뉴얼) 정독 — 6에이전트 흐름 + 라벨 + 게이트
2. `ops/RESEARCH.md` 정독 — 각 에이전트의 작업 절차·산출물·게이트 상세
3. `STATUS.md`(이 파일) 확인
4. GitHub Issues에서 **자신이 처리할 라벨** 이슈 확인:
   - 매일 22:00 UTC 슬롯 직후라면: `agent/discovery` 이슈 1건(자동 발행됨)
   - 2번 에이전트라면: `agent/research` 이슈
   - 등등
5. 작업 후 이 파일(`STATUS.md`) 갱신.

질문이 생기면 저장소 밖 인수인계 문서(2026-10-13자, 워크스페이스 루트)를 참고하되, **그 문서의 서버 정보는 절대 커밋하지 말 것.**

## 6에이전트 — 운영 노트

| # | 에이전트 | 자동 트리거 | 산출물 |
|---|---|---|---|
| 1 | 발굴(Discovery) | 매일 22:00 UTC (`discover.yml` cron) | 이슈 1건(소프트웨어/스킬 발굴 리포트) |
| 2 | 연구(Research) | 이슈 큐 `queue/research` | 코멘트(출처·라이선스·컬렉션 결정) |
| 3 | 제조(Build) | `agent/build` 라벨 | 데이터 JSON + 자유구성 페이지 + PR |
| 4 | 검수(Verify) | PR `agent/build` | `gh pr checks` + 운영 원칙 → `agent/verify` |
| 5 | 게시(Publish) | `agent/verify` | PR merge + `deploy.yml` + 이슈 close + `agent/published` |
| 6 | 주간 검증(Weekly Audit) | 매주 일요일 22:00 UTC | 기존 모든 항목 팩트 재검사 + 변경 이력 갱신 |

**라벨 10종** (모두 GitHub에 생성됨): `agent/{discovery,research,build,verify,published}` (5) + `queue/{research,verify,deploy}` (3) + `status/blocked-human` (1) + `priority/urgent` (1).
