# PRD — 열린도구 Alternatives

> **문서 성격**: 제품 요구사항 문서(PRD). *무엇을, 왜, 누구를 위해* 만들었는지와 *현재 어디까지 왔는지*를 한 곳에서 답한다.
> *어떻게* 운영할지는 [`AGENTS.md`](AGENTS.md)(운영 매뉴얼)·[`ops/RESEARCH.md`](ops/RESEARCH.md)(에이전트별 절차)·[`ops/RUNBOOK.md`](ops/RUNBOOK.md)(배포 절차)를 본다.
> 작성: 2026-10-14 · 마지막 갱신: 2026-10-14 · 상태: 4-1 완료 / 4-2 미착수

---

## 1. 개요 (Overview)

**열린도구(Alternatives)** 는 교사를 위한 한국어 정적 정보 사이트다. 학교에서 이미 쓰는 유료·상용 앱(알집, 알캡처, 포토샵, 캐피컷 등) 대신 쓸 수 있는 **오픈소스 대안**, 그리고 수업·업무에 활용할 수 있는 **AI 에이전트 스킬**을 정리한다. 4축 정보 구조(학습SW / 오픈스킬 / 현장사례 / 수업지도안)와 6에이전트 운영 파이프라인(발굴·연구·제조·검수·게시·주간)을 채택해 100% AI 에이전트가 매일 콘텐츠를 발굴·검수·게시·재확인한다.

- **운영 주소**: https://edtechnewsroom.com/alternatives/ (뉴스룸 VPS 정적 호스팅, `/alternatives/` 하위 경로)
- **저장소**: https://github.com/scottnaddle/open-tools-alternatives (비공개)
- **백엔드 없음** — 정적 사이트, 회원제·로그인·개인 콘텐츠 작성 기능 없음
- **AI 운영** — 모든 콘텐츠는 AI 에이전트가 작성하고, 출처·라이선스·사실관계를 CI 게이트로 강제 검증

### 왜 만들었나 (문제 의식)

1. **교사 정보 비대칭** — 학교에서 유료 앱을 구매하지만, 무료 오픈소스 대안의 존재를 모르는 경우가 많다. 알집 → 7-Zip, 알캡처 → ShareX, 포토샵 → GIMP 같은 매핑이 출처와 함께 정리돼 있지 않다.
2. **운영비** — 학교 라이선스 비용 부담(연간 수천만원). 오픈소스 대안은 도입·유지 비용이 거의 0이다.
3. **유료 전환 위험** — 무료로 시작해 유료 전환하는 도구가 많아(Notion, Adobe 등), 정책적으로 검증된 정보가 필요하다.
4. **AI 시대 도구 폭증** — AI 에이전트 스킬(Claude Code·Codex 스킬)이 매일 새로 등장한다. 학교에서 교육적으로 안전한 것만 골라 정리할 자동화된 시스템이 필요하다.

### 핵심 참조(설계에 큰 영향)

- **edzip.kr** (건국대 운영, https://edzip.kr) — 교사용 에듀테크 정보·체험 플랫폼. **4축 정보 구조(학습SW·활용사례·수업지도안·심층리뷰)** 와 카드 그리드·카테고리 chip UI를 차용. 단, 회원제·개인 콘텐츠·로그인은 **운영 원칙 위배로 도입하지 않음**.
- **교실 현장의 솔직한 한계** — 정보는 "교사·정보부장·행정" 모두를 위해 정확해야 한다. 추상적 칭찬·점수·순위는 금지.

---

## 2. 목표 / 비목표 (Goals / Non-goals)

### Goals (달성하려는 것)
1. **신뢰 가능한 정보** — 모든 팩트에 1차 출처(공식 저장소·문서)가 있고, 미확인은 "확인 중", 가짜는 "예시 데이터" 배지로 표시.
2. **자동 운영** — 매일 22:00 UTC 자동 검증 + 매주 일요일 22:00 UTC 주간 보정. 사람 개입은 검수·승인·외부 발송 단계에 한정.
3. **6에이전트 파이프라인** — 발견→연구→제조→검수→게시→주간. 한 이슈 = 한 콘텐츠의 라이프사이클.
4. **4축 정보 구조** — 학습SW(오픈소스 도구) / 오픈스킬(AI 스킬) / 현장사례 / 수업지도안(+(예정) 심층리뷰는 PR #17에서 추가됨).
5. **학교 환경 친화** — 오프라인 동작, 자체 호스팅 영상, 한국어 UI, 설치 난이도·관리자 권한·학생 데이터 등 학교 조건 명시.
6. **에이전트 친화 운영** — 새 에이전트가 투입되면 AGENTS.md·STATUS.md 두 개만 읽고 즉시 작업 가능.

### Non-goals (하지 않는 것)
- **회원제 / 로그인 / 개인 콘텐츠** — edzip의 3축은 운영 원칙·정적 정보 원칙에 반하므로 채택하지 않음.
- **점수·인기 순위·"도움이 됐어요"** — 추천 알고리즘은 운영 원칙 3에 반함.
- **광고·스폰서·제휴** — 수익 모델 없음.
- **학교 적합성 / 법적 준수 판정** — 정보 제공이 목적이지 보증이 아님. "확인 중"으로 명시.
- **학생 직접 사용 도구의 자동 승인** — usageScope = "수업용"은 verified 팩트 + 학교 AI 도입 절차 통과 후만 부여(CI 강제).
- **민간 SaaS(Notion, Figma, Adobe 등) 도구 직접 등록** — 오픈소스 대안의 대안군(edzip과 다른 카테고리)으로 운영하지 않음.

---

## 3. 대상 사용자 (Target Users)

| 역할 | 필요 | 이 사이트에서 얻는 것 |
|---|---|---|
| **교사(담임·교과·정보)** | 수업을 위한 도구, 단원 지도안, 시연 예시 | 도구 정보 + 사례 + 지도안, 10분 안에 결정 가능 |
| **정보부장 / 전산** | 학교 PC에 도입할 도구, 라이선스·관리자 권한·일괄 배포 | 심층리뷰 + 도구 컬렉션의 일괄 배포·관리자 권한·학생 데이터 필드 |
| **교무·행정** | 문서·HWP 호환, 학교 행정 도구 | 도구 컬렉션 + 비교 페이지 |
| **뉴스룸 자체** | 콘텐츠 운영 자동화, 운영 원칙 일관성 | AI 에이전트 시스템(6에이전트), CI 게이트, 변경 이력 아카이빙 |
| **AI 에이전트(다음 세션 투입)** | — | AGENTS.md + ops/RESEARCH.md만 읽고 즉시 작업 |

---

## 4. 핵심 운영 원칙 (이미 AGENTS.md §1에 있음 — PRD 차원 요약)

| # | 원칙 | 강제 수단 |
|---|---|---|
| 1 | **출처 없는 사실 금지** — 모든 fact에 URL+시각 | Zod refine + `check_skills`/`check_axis_pages` |
| 2 | **"확인 중" / "예시 데이터" 표기** | 페이지 배지, 스키마 enum |
| 3 | **점수·순위·"도움이 됐어요" 금지** | 운영 원칙 — 코드 강제는 없지만 PR 검수에서 반려 |
| 4 | **usageScope** (수업용/교사 개인용) 유지 | 스키마 + `check_usagescope.py` (student-use-check 시 verified 팩트 강제) |
| 5 | **회사명(유비온) 노출 금지** | 코드/PR 검수 |
| 6 | **큰 작업은 계획 승인 후 시작** | AGENTS.md §1.6 |
| 7 | **`--apply`(라이선스 자동 반영) 사용자 요청 시만** | AGENTS.md §1.7 |
| 8 | **외부 발송 초안 → 사용자 승인** | AGENTS.md §1.8 |
| 9 | **비밀값 출력/커밋 금지** (서버 IP, 비밀번호) | 시크릿/환경변수, PR 검수 |
| 10 | **"CI 통과"는 `gh pr checks`로 직접 확인** | `merge` 직전 매번 |

---

## 5. 정보 구조 — 4축 IA (edzip.kr 차용)

| 축 | 컬렉션 (Zod) | 라우트 | 정적 데이터 | 비고 |
|---|---|---|---|---|
| **학습SW** (오픈소스 대안) | `tools` + `school-apps` | `/`, `/apps/<slug>/`, `/tools/<slug>/`, `/compare/<pair>/` | 15 도구 + 9 학교 앱 + 비교 | 메인 축. 홈 = 학습SW 입구 |
| **오픈스킬** (AI 에이전트 스킬) | `skills` + `skill-pages/<slug>.html` | `/skills/`, `/skills/<slug>/` | 28 스킬 + 3 자유구성 페이지 | 발굴→재구성 2단계 루프 |
| **현장사례** | `cases` | `/cases/`, `/cases/<slug>/` | 예시 1건 (PhysicsOS 중3 2단원 10분 데모) | PR #17·#18 |
| **수업지도안** | `lessons` | `/lessons/`, `/lessons/<slug>/` | 예시 1건 (7-Zip 초5 디지털시민성) | PR #17·#18 |
| **심층리뷰** | `reviews` | `/reviews/`, `/reviews/<slug>/` | 예시 1건 (OBS Studio 도입 검토) | PR #17·#18 — 원래 edzip의 4번째 메뉴를 4-1에서 5번째 축으로 승격 |

**예시 데이터 원칙**: 모든 4축 신규 항목은 `example: true`로 시작하며, "예시 데이터" 배지가 강제되고([check_axis_pages.py](repo/scripts/check_axis_pages.py) 검증) 사용자가 "확인 중"으로 변경하기 전까지는 예시로 표시.

---

## 6. 기능 요구사항 (Functional Requirements)

### 6.1 6에이전트 운영 시스템 (PR #20, 4-1)

| # | 에이전트 | 트리거 | 입력 | 출력 | 게이트 |
|---|---|---|---|---|---|
| 1 | **발굴(Discovery)** | 매일 22:00 UTC 자동 + 수동 (`.github/workflows/discover.yml`) | GitHub Trending·소셜·이슈 템플릿 | 이슈 1건 (소프트웨어/스킬 발굴 리포트) | 라이선스 허용목록 통과, 학교 활용 시나리오 1개 이상 |
| 2 | **연구(Research)** | 이슈 큐 `queue/research` | 1의 리포트(공식 저장소·문서) | 코멘트(출처·라이선스·컬렉션 결정) | 라이선스 1차 재확인 + 학교 관점 시나리오 |
| 3 | **제조(Build)** | 라벨 `agent/research` | 2의 검증 결과 | 데이터 JSON + (선택) 자유구성 페이지 + PR | 로컬 게이트 4종 |
| 4 | **검수(Verify)** | PR 생성·라벨 `agent/build` | 3의 PR | `gh pr checks` + 운영 원칙 점검 | CI 실제 통과 + 원칙 10개 |
| 5 | **게시(Publish)** | 라벨 `agent/verify` | 승인된 PR | merge + deploy + 이슈 close + `agent/published` | `deploy.yml` 수동 실행 |
| 6 | **주간 검증(Weekly Audit)** | 매주 일요일 22:00 UTC (예정) | 기존 모든 항목의 1차 sourceUrl + GitHub release | 변경 시 `changes/` 기록 + 페이지 변경 이력 갱신 | A등급 즉시 / C등급 24h 재확인 |

### 6.2 발견(Discovery) 자동화 — `.github/workflows/discover.yml`

- **cron**: 매일 22:00 UTC
- **동작**: 빈 본문 이슈 1건 자동 발행(라벨 `agent/discovery` + kind=software|skill). GitHub Search API로 참고 후보 1~5개 코멘트 첨부. 홀수일=software, 짝수일=skill.
- **결정론적**: AI 없이도 동작. 사람(또는 다음 에이전트 세션)이 본문 채움.
- **안전**: `ops/FREEZE` 파일 존재 시 즉시 중단.

### 6.3 4축 데이터 모델 (PR #18, content.config.ts)

```ts
cases: { title, grade, unit, schoolContext, tool{sourceUrl}, summary, sourceUrl, sourceMethod, fetchedAt, dateChecked, example, badges }
lessons: { title, grade, unit, duration, schoolContext, tool{sourceUrl}, summary, sourceUrl, sourceMethod, fetchedAt, dateChecked, example, badges }
reviews: { title, tool{slug, sourceUrl, license}, summary, sourceUrl, sourceMethod, fetchedAt, dateChecked, example, badges }
```

**게이트 ([check_axis_pages.py](repo/scripts/check_axis_pages.py))**: sourceUrl http(s) 시작, sourceMethod ∈ 허용 목록, dateChecked YYYY-MM-DD, fetchedAt ISO datetime, example=true면 badges에 "예시 데이터" 필수.

### 6.4 자유구성 쇼케이스(스킬/4축) — PR #13

- `src/content/skill-pages/<slug>.html`(또는 4축 자유구성 페이지): 스킬/사례/지도안/리뷰마다 다른 화면 구성
- 모든 미디어에 `data-source`(원 출처 URL) 필수 — `check_skills.py`가 빌드 실패 처리
- 편집 키트 `.show-*` 클래스(데모/콜아웃/그리드/스탯/스텝/비디오) — 사이트 톤 유지

### 6.5 데이터 거버넌스 (Fact/Source)

`tools`/`skills`의 모든 팩트는 다음 구조:
```ts
fact<T>(v: T) => { value, sources: Source[], status: 'verified'|'unverified'|'conflict'|'stale', lastVerified }
```
- `status === 'verified'`이면 `sources`에 `manual-seed` 외 1개 이상 필수(Zod refine, [content.config.ts](repo/src/content.config.ts) L18-21)
- `daily_verifier`가 매일 stars/latestRelease/lastPush/license 재확인 → 변경 시 `src/content/changes/` JSON 기록 + draft PR
- C등급(license·archived·health)은 `pending-24h` → 24h 후 재확인 일치 시 `approved` → 적용

### 6.6 배포 ([ops/RUNBOOK.md](repo/ops/RUNBOOK.md))

- **수동 트리거**: `gh workflow run deploy.yml --ref main` (사용자 결정)
- **절차**: 산출물 검사(index.html ≥ 60, pagefind 존재) → 서버 백업 → 원자적 교체(임시 폴더 → mv) → 헬스체크 5종(홈/skills/about/pagefind/뉴스룸) → 실패 시 자동 롤백
- **강화된 헬스체크**: 홈 HTML이 참조하는 CSS/JS의 실제 200 확인 + 루트 절대링크 감지(2026-10-13 CSS 404 사고 방지)
- **시크릿**: `GHOST_SERVER_ROOT_PASSWORD`, `GHOST_SERVER_HOST` (GitHub Secrets 1회 설정)
- **금지**: nginx·Ghost·Cloudflare·DNS 설정 변경 금지 (정적 파일 교체만)

### 6.7 GitHub Issues + 라벨

**라벨 10종** (모두 GitHub에 생성됨):
- `agent/{discovery,research,build,verify,published}` (5) — 콘텐츠 1건의 라이프사이클 추적
- `queue/{research,verify,deploy}` (3) — 단계가 아닌 상태
- `status/blocked-human` (1), `priority/urgent` (1)

**이슈 템플릿 5종** (`.github/ISSUE_TEMPLATE/`):
- app-alternative-request · fact-correction · skill-suggestion
- skill-discovery-report · software-discovery-report(이번 PR #20에서 추가)

---

## 7. 비기능 요구사항 (Non-functional)

| 항목 | 기준 | 강제 수단 |
|---|---|---|
| **성능** | 정적 HTML · Pagefind 1MB 이하 · LCP < 2s | Astro 정적 빌드, Pagefind 1.5.x |
| **접근성** | 한국어, 시맨틱 HTML, 키보드 내비, `aria-current` | Base.astro·Lucian 컴포넌트, PR 검수 |
| **검색** | Pagefind 한국어 인덱싱, 동의어(`src/lib/search-synonyms.ts`) | 기존 PR #2에서 완료 |
| **모바일** | `<=768px` 1열·햄버거 메뉴 | Lucian UX/UI Prompt #045 (Base.astro) |
| **보안** | 비밀값 GitHub 시크릿만, AGENTS.md §1.9 | PR 검수, `.gitignore`, 시크릿 등록 |
| **안정성** | 자동 병합 없음, 헬스체크 5종, 자동 롤백 | AGENTS.md §1.10, ops/RUNBOOK.md |
| **i18n** | 한국어 기본, 영문 표기 자제 | AGENTS.md §7, PR 검수 |
| **호스팅** | 뉴스룸 VPS, nginx + Cloudflare, 정적 파일 | 운영 분리·자동화 |

### 7.1 4 navLinks 회귀 (2026-10-13)

Astro 6 + TypeScript frontmatter에서 **navLinks/카드 매핑이 4개 항목 이상일 때 line 276 매칭 오류**로 빌드 실패. 정확한 원인은 미파악(3개는 OK, 4개부터 깨짐). **우회 원칙**:
- 푸터·카드·헤더의 매핑은 4개 이상일 때 **직접 명시**(`<li><a>` 4개)
- `getStaticPaths`는 `entries.map(...)` 대신 `for` 루프 + `paths: {params, props}[]` 타입 명시
- 컴포넌트(`IxCard.astro`) 내부 map은 단일 슬롯으로 처리 → 안전

---

## 8. 기술 스택 & 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                GitHub Issues + 라벨 (10종)                      │
│  [queue/*, status/*, priority/*, agent/*]                     │
│  템플릿 5종: 대안요청·정정·스킬제안·스킬발굴·소프트웨어발굴   │
└─────────────────────────────────────────────────────────────────┘
                              │ 1. 발견
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ .github/workflows/discover.yml — 매일 22:00 UTC cron           │
│  (빈 본문 이슈 발행 + GitHub Search 참고 후보 코멘트)            │
└─────────────────────────────────────────────────────────────────┘
                              │ 2~3. 연구·제조 (에이전트 세션)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  GitHub PR  ─────►  ci.yml (build-and-check)                    │
│                   • npm ci + astro check + build                 │
│                   • check_*.py 4종 (스킬·usage·4축·데이터)       │
│                   • 실제 통과 = gh pr checks (원칙 10)          │
└─────────────────────────────────────────────────────────────────┘
                              │ 4. 검수 → 5. merge
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  main  ─────►  deploy.yml 수동 트리거                            │
│              (백업 → 교체 → 헬스체크 5종 → 자동 롤백)            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                https://edtechnewsroom.com/alternatives/
```

### 8.1 스택
- **프론트엔드**: Astro 6 + Node 22 + TypeScript + Zod 콘텐츠 컬렉션
- **검색**: Pagefind 1.5.x (한국어 동의어)
- **UI**: Lucian UX/UI 컴포넌트 (`#019`, `#045` 등, MIT 헤더 유지) + 자체 토큰 (`public/style.css` `--ground`/`--surface`/`--brand` 등)
- **CI**: GitHub Actions · Python 3.11
- **자동화**: `daily_verifier.py` (도구·스킬·4축 팩트 재검사)
- **호스팅**: 뉴스룸 VPS (167.86.72.98) · nginx + Cloudflare Full(strict)
- **검증 스크립트 4종**: `verify.py` · `check_usagescope.py` · `check_skills.py` · `check_axis_pages.py`

### 8.2 콘텐츠 디렉토리 구조
```
src/
├── content.config.ts          # Zod 스키마 (tools, schoolApps, changes, skills, cases, lessons, reviews)
├── content/
│   ├── tools/                 # 15 도구 JSON
│   ├── school-apps/           # 9 학교 앱 JSON
│   ├── skills/                # 28 스킬 JSON
│   ├── skill-pages/           # 3 자유구성 페이지 (PhysicsOS, Hallmark, Huashu)
│   ├── cases/                 # 1 현장사례 JSON
│   ├── lessons/               # 1 수업지도안 JSON
│   ├── reviews/               # 1 심층리뷰 JSON
│   └── changes/               # 변경 기록 JSON (누적)
├── pages/                     # 라우트 (4축 페이지 6 + 도구·스킬·apps·비교·changes·suggest·search·for/*)
├── layouts/Base.astro         # 헤더(5메뉴 3) + 푸터(3열 4축) + 햄버거 + FREEZE/AGENTS
├── components/                # Icon, Mono, QuickChips, SearchAutocomplete, ToolFacts, ScopeChips, Status, FloatingInput, Toast, IxCard
├── lib/                       # facts.ts (예시 라벨, CAT, mono 등), search-synonyms.ts
└── data/                      # featured.json, scenes.json, ui-examples.json, ui-svgs.json, icons.json

scripts/
├── verify.py                  # GitHub API 팩트 재검사 + 4축 sourceUrl HEAD
├── check_usagescope.py
├── check_skills.py            # 28 OSI 라이선스 게이트
├── check_axis_pages.py        # cases/lessons/reviews 게이트
├── fact_age.py                # 90일 경과 팩트
├── daily_verifier.py          # 위 4종 + 변경기록 통합 (A/C 등급, PR 자동 발행)
├── record-demo.mjs            # 공식 데모 화면 녹화 도구 (자체 호스팅 영상)
└── convert-seed.py, fill_verified_fields.py, take-screenshots.mjs, test-search.mjs (레거시)

.github/
├── ISSUE_TEMPLATE/            # 5종 (app-alternative, fact-correction, skill-suggestion, skill-discovery, software-discovery)
└── workflows/
    ├── ci.yml                 # PR마다 build-and-check
    ├── daily-verifier.yml     # 매일 22:00 UTC (cron)
    ├── deploy.yml             # 수동 (workflow_dispatch)
    └── discover.yml           # 매일 22:00 UTC (cron, PR #20 신규)

ops/
├── RESEARCH.md                # 6에이전트 작업 절차 상세
├── RUNBOOK.md                 # 배포·롤백·헬스체크·긴급정지 절차
├── FREEZE                     # (옵션) 긴급정지 플래그
└── (예정) weekly-audit.yml 등
```

---

## 9. 릴리스 / PR 히스토리 (2026-10-13 ~ 2026-10-14)

| PR | 날짜 | 내용 | 단계 |
|---|---|---|---|
| #11 | 10-13 | skills 상세 페이지 TS 오류 수정 (previewPath undefined) | (사전) |
| #12 | 10-13 | AGENTS.md: 브랜치 보호 제약과 CI 확인 규칙 보강 | 인프라 |
| #13 | 10-13 | 오픈스킬 자유구성 쇼케이스 + 발굴→재구성 2단계 루프 + 3형태 샘플 | 1차 |
| #14 | ❌ 폐기 | (4 navLinks 회귀) | 1a(미머지) |
| #15 | 10-14 | 헤더 학습SW 라벨 | 1a |
| #16 | 10-14 | 푸터 3열 + 4축 (직접 명시, map 회피) | 1a2 |
| #17 | 10-14 | 4축 페이지 6개(현장사례/수업지도안/심층리뷰) + IxCard 컴포넌트 | 2 |
| #18 | 10-14 | 4축 데이터 모델 + Zod 스키마 + CI 게이트 | 3 |
| #19 | 10-14 | daily_verifier 4축 자동 검증 (HEAD + dateChecked + stale) | 3 |
| **#20** | **10-14** | **6에이전트 운영 시스템 + 매일 자동 발굴 슬롯** | **4-1** |

**누적 페이지 수**: 23 → 74 (+51). 도구 15, 스킬 28, 학교 앱 9, 사례 1, 지도안 1, 리뷰 1.

---

## 10. 성공 지표 (KPI) — 정의/측정 필요

운영 사이트는 **정적 정보**가 목적이므로 트래픽 기반 KPI는 부차적. 핵심은 **운영 자동화 사이클이 닫혔는가**:

| 지표 | 목표 | 측정 |
|---|---|---|
| 1번 에이전트 일일 슬롯 발행률 | 100% (FREEZE/실패 제외) | `discover.yml` 워크플로 실행 횟수 vs 하루 |
| 2~5번 에이전트 통과율 | 후보 발행 → 5번(게시) 도착 비율 | 이슈 라벨 흐름 추적 |
| daily_verifier 자동 변경 감지 | 매일 ≥ 1개 변경 (정상 운영 시) | `src/content/changes/` 일일 증가 |
| 4축 페이지 수 | 매주 ≥ 1개 백필 (주 1회) | `src/content/{cases,lessons,reviews}/*.json` 개수 |
| CI 실제 통과율 | 100% (실패 PR 0) | `gh pr checks` 결과 |
| 회귀 0건 | 자동 배포 후 UI 깨짐 0 | 헬스체크 5종 + CSS 404 사고 재발 방지 |
| 메모리: 운영 매뉴얼 완비성 | 새 에이전트가 AGENTS.md + STATUS.md만 읽고 즉시 작업 | (체크리스트) |

---

## 11. 다음 단계 (Backlog)

### 4-2 — 주간 검증 + 페이지 변경 이력 아카이빙 (다음 PR, 다음 세션)
- **`.github/workflows/weekly-audit.yml`**: 매주 일요일 22:00 UTC 자동, 6번 에이전트가 기존 모든 항목 재검사
- **각 페이지 변경 이력 아카이빙 표시**: tools/[slug] / skills/[slug] / cases/[slug] / lessons/[slug] / reviews/[slug] 페이지 하단에 "변경 이력" 섹션. `src/content/changes/` JSON을 모아 표/타임라인으로. `data-pagefind-meta`로 인덱스에서 제외.
- **CI 변경**: weekly-audit의 산출물(변경기록)이 PR로 자동 발행 → 사람이 검토

### (장기) 4-3 — 정밀화
- 에이전트 라벨 자동 전이(다음 에이전트 세션이 이슈를 가져가면 라벨 자동 이동)
- 4축(현장사례·수업지도안·심층리뷰) 백필 — 매주 1건씩 누적
- 오픈스킬 자유구성 페이지 22개(나머지) — 매주 1~2건
- 제안 폼 실동작화(현재 정적) — 서버리스 → 이슈 접수 자동화
- 뉴스레터 초안·승인 흐름(외부 발송은 반드시 초안 → 승인)
- `lucian-uxui` gitlink 경고 정리(.gitmodules 추가 또는 submodule 정식화)
- 라벨 자동 라우팅 — 이슈가 일정 시간 동안 `agent/*` 라벨에서 멈춰 있으면 `priority/urgent` 자동 부여

### (장기) Stage 2a — 학습SW(도구) 인덱스 보강
- 홈(`/`)이 학습SW 입구 + 4축 인덱스 역할 — 카테고리 필터·정렬·검색 강화
- `apps/` (현재 카드) + `tools/` (도구 상세) 통합

### (탐색) 브랜치 보호 (현재 비공개 무료 플랜 한계)
- 공개 전환 또는 GitHub Pro 구독 시 `build-and-check` 필수 검사 설정 (현재는 `gh pr checks` 수동 확인이 유일한 방어선)

---

## 12. 부록

### 12.1 절대 원칙 (AGENTS.md §1과 동일 — 참조)
AGENTS.md §1 참조.

### 12.2 라벨 체계 (GitHub에 10개 생성됨)

| 라벨 | 색상 | 용도 |
|---|---|---|
| `agent/discovery` | d93f0b | 1번 에이전트 처리 중 |
| `agent/research` | fbca04 | 2번 에이전트 처리 중 |
| `agent/build` | 0e8a16 | 3번 에이전트 처리 중 |
| `agent/verify` | 5319e7 | 4번 에이전트 처리 중 |
| `agent/published` | 0e8a16 | 5번 에이전트 완료 |
| `queue/research` | 1d76db | 조사 필요 (후보·정정) |
| `queue/verify` | 1d76db | 팩트 재확인 |
| `queue/deploy` | 1d76db | 배포 대기 |
| `status/blocked-human` | e99695 | 사람 개입 필요 |
| `priority/urgent` | b60205 | 긴급 (장애·유료 전환·손상) |

### 12.3 이슈 템플릿 (`.github/ISSUE_TEMPLATE/`)

1. `app-alternative-request.yml` — 대안 요청 (사람 → 1번)
2. `fact-correction.yml` — 정보 정정 (사람 → 4번 또는 daily-verifier)
3. `skill-suggestion.yml` — 스킬 제안 (사람 → 1번)
4. `skill-discovery-report.yml` — 스킬 발굴 리포트 (1번 → 2번)
5. `software-discovery-report.yml` — 소프트웨어 발굴 리포트 (1번 → 2번, PR #20에서 추가)

### 12.4 핵심 파일 위치

| 영역 | 파일 |
|---|---|
| 운영 매뉴얼 | [AGENTS.md](AGENTS.md), [ops/RESEARCH.md](ops/RESEARCH.md), [ops/RUNBOOK.md](ops/RUNBOOK.md) |
| 상태 | [STATUS.md](STATUS.md) |
| 데이터 스키마 | [src/content.config.ts](src/content.config.ts) |
| 발견 워크플로 | [.github/workflows/discover.yml](.github/workflows/discover.yml) |
| 일일 검증 워크플로 | [.github/workflows/daily-verifier.yml](.github/workflows/daily-verifier.yml) |
| 배포 워크플로 | [.github/workflows/deploy.yml](.github/workflows/deploy.yml) |
| CI 워크플로 | [.github/workflows/ci.yml](.github/workflows/ci.yml) |
| 게이트 스크립트 | [scripts/check_skills.py](scripts/check_skills.py), [scripts/check_usagescope.py](scripts/check_usagescope.py), [scripts/check_axis_pages.py](scripts/check_axis_pages.py), [scripts/verify.py](scripts/verify.py) |
| 자동 검증 본체 | [scripts/daily_verifier.py](scripts/daily_verifier.py) |
| 팩트 TTL | [scripts/fact_age.py](scripts/fact_age.py) |
| 화면 녹화(자체 호스팅 영상) | [scripts/record-demo.mjs](scripts/record-demo.mjs) |

### 12.5 용어집

| 용어 | 정의 |
|---|---|
| **4축** | 학습SW / 오픈스킬 / 현장사례 / 수업지도안(+심층리뷰). edzip.kr 차용 IA. |
| **6에이전트** | 발견·연구·제조·검수·게시·주간. 콘텐츠 1건의 라이프사이클. |
| **Fact** | `{value, sources[], status, lastVerified}` 구조의 출처 강제 데이터 단위. |
| **Source** | `{url, fetchedAt, method, excerpt?}` 구조. method ∈ github-api/release-assets/official-site/readme/procurement-data/manual-seed. |
| **usageScope** | personal / demo / offline-install / student-use-check. `student-use-check`는 verified 팩트 강제. |
| **프리빌드** | `npm run build` 산출물 (정적 HTML). Astro + Pagefind. |
| **4 navLinks 회귀** | 2026-10-13에 발견된 Astro 6 + TypeScript 회귀. 4개 이상 navLinks에서 빌드 실패. 우회: 직접 명시·for 루프. |
| **에이전트** | 본 시스템의 운영 단위(사람 에이전트처럼). 1~6번 각각 책임·입력·출력·게이트가 정의됨. |
| **아카이빙** | 변경 이력의 시각화. `src/content/changes/*.json`을 페이지에 표시. 4-2에서 구현. |

### 12.6 사고 기록 (2026-10-13)

| 시각 | 사고 | 대응 |
|---|---|---|
| 22:31 (Tashkent) | 첫 자동화 배포가 ASTRO_BASE 누락 → CSS 404 → UI 붕괴 | PR #8: base 기본값 `/alternatives`로 반전 + 헬스체크 강화 |
| 22:39 | 재배포 | 운영 복구 |
| 23:00 | PR #10 머지 시 CI 실패를 확인 안 함 (브랜치 보호 없음) | AGENTS.md §1.10 "CI 통과 = `gh pr checks` 직접 확인" 명문화 |
| 이후 | 4 navLinks 회귀 | 우회(직접 명시, for 루프) — 정확한 원인 미파악 |

---

*이 문서는 AGENTS.md(운영 매뉴얼)와 함께 살아 움직입니다. 큰 결정이 바뀌면(예: 4-2 완료, Stage 2a 착수) 갱신하세요.*
