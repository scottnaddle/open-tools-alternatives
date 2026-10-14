# ops/RESEARCH.md — 지속 검색(리서치) 루프 + 6에이전트 명세 보강

이 문서는 **6에이전트 운영 흐름의 작업 단계별 절차**를 상세히 풀어쓴다. 에이전트 정의·라벨·자동 스케줄은 `AGENTS.md`를, 배포 절차는 `ops/RUNBOOK.md`를, 보안·FREEZE는 같은 이름의 파일을 참고한다.

## 1. 흐름 (1줄)

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

상세 표·다이어그램은 `AGENTS.md §2`. 본 문서는 각 단계의 **작업 절차와 결과물 명세**를 다룬다.

## 2. 에이전트 1 — 발굴(Discovery)

**트리거**: 매일 22:00 UTC 자동 슬롯(`.github/workflows/discover.yml`이 빈 본문 이슈 발행) + 수동(이슈 템플릿 직접 사용).

**산출물**: GitHub Issue 1건 + 결론(선정 / 보류).

**리포트(채워야 할 본문)**는 두 가지 템플릿 중 하나를 사용:
- **소프트웨어(도구) 후보** → `.github/ISSUE_TEMPLATE/software-discovery-report.yml` (라이선스 / 분야 / 설치 난이도 / 학교 시나리오 / 기기·플랫폼 / 한국어 UI / 관리자 권한 / 학생 데이터 / 데모 자산 / 위험)
- **AI 스킬 후보** → `.github/ISSUE_TEMPLATE/skill-discovery-report.yml` (라이선스 / 입출력 예시 2개 이상 / 학교 시나리오 / 데모 자산 / 위험)

**선정 기준 (모두 충족)**:
1. 라이선스가 `src/content.config.ts`의 허용목록에 있다 (스킬: `ALLOWED_SKILL_LICENSES` 28종, 도구: 동일). **없음 / AGPL / NOASSERTION / 비OSI는 보류.**
2. 학교에서 실제로 도입 가능 — GitHub 공개 저장소 또는 공식 사이트가 있고, 한국어/영어 가이드·문서·이슈 트래커가 활성.
3. 학교 활용 시나리오가 1개 이상 분명함 (수업용이면 usageScope, 교사 제작용이면 tools).
4. 1차 출처(공식 README/문서)에 위 내용이 명시되어 있음 — 2번 에이전트가 재확인할 사실이지만, 1번에서도 1차 출처를 **링크**해 둔다.

**보류 기준 (1건에 해당하면 보류, 이슈 닫고 `agent/discovery` 제거)**:
- 라이선스 불가
- 학교 활용 시나리오가 불분명(단순 트레이딩 점수용 등)
- 도입 위험 큼(학생 데이터, 유료 전환 소지, 운영 종료)
- 같은 주제·유사 도구가 이미 등록되어 있음(이슈에 "이미 등록됨" 코멘트)

**핸드오프**:
- 보류 시 → 이슈 닫기. `agent/discovery` 제거.
- 선정 시 → `agent/discovery` 라벨은 유지, `queue/research` 라벨 **추가**로 붙여서 2번 에이전트에게 인수인계.

## 3. 에이전트 2 — 연구(Research)

**트리거**: `queue/research` 라벨 이슈.

**산출물**: 이슈 본문 + 코멘트로 (1) 출처 재확인 결과 (2) 라이선스 통과 (3) 학교 활용 시나리오 확정 (4) 적합 컬렉션·라우트 결정.

**절차**:
1. 리포트의 출처를 **공식 저장소/문서에서 직접 재확인** — AGENTS.md 원칙 1(리포트를 그대로 믿지 않음)
2. 라이선스 파일 원문(`LICENSE`/`License.md`)을 GitHub에서 raw로 받아 확인. AGPL·NOASSERTION·상용 등 금지 항목은 **즉시 보류**(이슈에 사유 코멘트 + `queue/research` 제거 + `status/blocked-human` 또는 `priority/urgent` 라벨로)
3. 학교에서 도입 시 운영에 필요한 사실만 추려 **학교 관점 시나리오 1개 이상** 작성
4. 적합 컬렉션 결정:
   - 일반 도구(영상/압축/오피스 등) → `src/content/tools/<id>.json` + `src/content/school-apps/<slug>.json`(기존 학교 앱의 대안일 때)
   - AI 에이전트 스킬 → `src/content/skills/<owner>-<repo>.json` + (선택) `src/content/skill-pages/<slug>.html`
   - 학교 활용 사례·수업 지도안·도입 리뷰 → `src/content/{cases,lessons,reviews}/<id>.json` + 자유구성 페이지
5. 게이트 결과(`python3 scripts/check_*.py`) 미리 시뮬레이션 — 라이선스·필수 필드·sourceUrl 형태가 통과 가능한지

**핸드오프**: 이슈에 "연구 완료, 제조 시작" 코멘트 + 라벨 `agent/research` → `agent/build`.

## 4. 에이전트 3 — 제조(Build)

**트리거**: 라벨 `agent/build`.

**산출물**:
- 데이터 JSON 1개(또는 사례/지도안/리뷰 + 자유구성 페이지)
- PR 1개(병합 전 상태)
- `src/content/changes/` 변경기록(아래 §7 참고)

**절차**:
1. 2번의 컬렉션 결정에 따라 JSON 작성 — 스키마: `src/content.config.ts`의 Zod. **모든 fact에 sources·status·lastVerified** — 수동 입력은 `status: "unverified"` + `method: "manual-seed"`
2. 스킬은 `previewMethod`(직접 생성 / 공식 예시) 표기, `dateChecked` ISO 날짜
3. 4축(cases/lessons/reviews)은 `example: true`면 `badges`에 **"예시 데이터"** 필수 — `check_axis_pages.py`가 강제
4. 자유구성 페이지가 필요하면 `src/content/skill-pages/<slug>.html` 또는 4축 상세 페이지. 모든 미디어(iframe·img·video·source·audio)에 **`data-source`** 필수 — `check_skills.py`가 빌드 실패 처리
5. **로컬 게이트**:
   - `python3 scripts/verify.py && python3 scripts/check_usagescope.py && python3 scripts/check_skills.py && python3 scripts/check_axis_pages.py`
6. `npm run build` — 0 errors
7. **PR 생성**:
   - 브랜치 `site/<content-kind>-<slug>`(예: `site/tool-foo`, `site/skill-bar`, `site/case-gr3-physics`)
   - 본문에 이슈 링크 + 체크리스트 + 솔직한 한계
   - `git add` 대상: 새 데이터 + (필요시) 페이지 + 자유구성 페이지. **`src/content/changes/`는 절대 직접 추가하지 않는다** — daily-verifier/weekly-audit가 자동 생성
8. PR 라벨 `agent/build` + 이슈 코멘트 "PR 링크"

**핸드오프**: PR URL + 라벨 `agent/build`로 4번에게.

**기존 회피 원칙 재확인 (4 navLinks 회귀)**:
- 푸터·카드·헤더의 매핑은 4개 이상일 때 직접 명시
- `getStaticPaths`는 `entries.map(...)` 대신 `for` 루프 + `paths: {params, props}[]` 타입 명시
- 새 페이지 작성 시에도 4개 이상 map을 회피 — 컴포넌트 내부 1회 map만 허용

## 5. 에이전트 4 — 검수(Verify)

**트리거**: PR 라벨 `agent/build`.

**산출물**: 라벨 `agent/verify` (승인) 또는 라벨 되돌림(반려).

**절차**:
1. **CI 실제 통과 확인** — `gh pr checks <num>` 직접 확인(AGENTS.md 원칙 10). `build-and-check`가 green이어야 함
2. **운영 원칙 점검**:
   - 모든 fact에 출처가 있는가
   - `예시 데이터` / `확인 중` 표기가 정확한 위치에 있는가
   - 출처 URL은 1차(공식)인가
   - 솔직한 한계 섹션이 있는가(스킬·4축)
   - 학교 적합성·법적 준수 **판정** 문구가 없는가(원칙 3)
   - 회사명(유비온) 노출이 없는가(원칙 5)
3. **기존 검증 규칙 약화 여부** — Zod refine·check 스크립트 임의 변경이 없는가
4. **데이터 정합성** — tools와 school-apps의 alternative 연결, skill의 sourceUrl ↔ github.repo 일치, 4축의 tool.sourceUrl ↔ sourceUrl 일치

**승인**: 라벨 `agent/verify` 부여. 코멘트 "검수 통과, 게시 가능".
**반려**: 라벨 `agent/build`로 되돌림 + 코멘트 "검수 반려 + 사유 + 다음 단계".

## 6. 에이전트 5 — 게시(Publish)

**트리거**: 라벨 `agent/verify`.

**산출물**: 운영 사이트 반영.

**절차**:
1. **PR merge** — `gh pr merge <num> --merge` (브랜치 보호 없으므로 merge 직전 `gh pr checks`로 CI 최종 확인 — 원칙 10)
2. **배포** — 콘텐츠 PR은 사람이 병합한다. main 푸시와 일일 검증 자동 병합은 `ops/RUNBOOK.md` 대로 `deploy.yml`이 처리한다. SSH 키(`ops/DEPLOY_KEY_SETUP.md`)가 없으면 건너뛴다. 수동 실행은 `gh workflow run deploy.yml --ref main`.
3. 배포 완료 확인 — `gh run watch <run-id>`. 헬스체크(5종) 200 확인
4. **이슈 close** + 라벨 `agent/published` 추가 + 코멘트 "게시 완료, 라이브 URL"
5. `STATUS.md` 갱신 — 콘텐츠 수·검증 현황·다음 할 일

**핸드오프**: 다음 콘텐츠의 1번 에이전트 슬롯이 받아서 처리.

## 7. 에이전트 6 — 주간 검증(Weekly Audit)

**트리거**: 매주 일요일 22:00 UTC(`.github/workflows/weekly-audit.yml` cron). + 일일 검증(daily-verifier)이 매일 부분 수행.

**산출물**:
- `src/content/changes/YYYY-MM-DD-{kind}-{id}-{field}-{hash}.json` 변경기록(누적)
- 각 페이지의 **변경 이력 표시 갱신** (페이지 하단 "변경 이력" 섹션 — 자세한 컴포넌트·표시는 후속 PR)

**대상**:
- `src/content/tools/*.json` — GitHub API로 stars/latestRelease/lastPush/license/health 재확인 (기존 `process_tool`)
- `src/content/skills/*.json` — 동일 (기존 `process_skill`)
- `src/content/{cases,lessons,reviews}/*.json` — 1차 sourceUrl HEAD + dateChecked 갱신 (기존 `process_axis_page`)

**게이트**:
- A등급(stars·latestRelease·lastPush·dateChecked) — 자동 적용
- C등급(license·archived·health) — `pending-24h` 변경기록, 24h 후 재확인 일치 시 `approved` 적용
- 4축의 sourceUrl HEAD 실패 — C등급 alert (수동 조사 필요)

**체인지로그**: 주간 검증 산출물은 사람 검토 후 병합한다. 자동 병합은 일일 검증 PR(`daily-verifier/` + `agent/verifier`)만 해당한다.

## 8. 콘텐츠 추가·수정 절차 (게이트 순서 요약)

1. **발굴** — 이슈 발행 + 리포트
2. **연구** — 공식 저장소·라이선스·문서 재확인
3. **제조** — 데이터 JSON 작성, 게이트 로컬 통과, PR
4. **PR** → **CI 실제 통과 확인** → **병합** (4번 검수와 함께)
5. **게시** — 사람이 병합하면 `deploy.yml` 이 경로에 맞게 배포한다. 키가 없으면 건너뛴다. 수동 실행은 `gh workflow run deploy.yml --ref main`
6. **STATUS.md** 갱신

자세한 절차는 각 에이전트 섹션(§2~§7) 참고.

## 9. 게시 금지·주의

- 사용자 접수(제안·정정)는 **출처 재확인 없이는 반영하지 않는다.** 재확인 결과를 이슈에 남긴다.
- 출처가 명확하지 않은 사실은 **"확인 중"**으로 표시 — verified로 게시하지 않는다.
- 학교 적합성·법적 준수 **판정** 문구 금지 — 정보 제공이 목적이지 보증이 아님.
- 학생 데이터 처리가 있는 도구는 **usageScope = "수업용" 표시 금지** — 학교 AI 도입 절차 안내 후 사용(원칙 4).

## 10. (구) 주간 리서치 체크리스트 — 6번 에이전트로 통합

기존 §5의 체크리스트는 6번 에이전트의 작업으로 흡수:
- [ ] 열린 이슈 목록 → 라벨별 정리, 오래된 `queue/research`부터 처리 (§3)
- [ ] `fact_age.py` 실행 → 90일 경과 팩트 재확인 (§7)
- [ ] 오픈스킬 "준비 중" 카드 중 1개 이상 미리보기 채우기 (§4, 자유구성 페이지)
- [ ] 홈 "이달에 소개하는 도구" — `src/data/featured.json`이 이번 달 항목을 가졌는지 확인
- [ ] 조달 수치 유효기간 확인 (표기: "2026년 1~10월, 확인 중")
- [ ] 처리 결과를 이슈 코멘트로 남기고 닫기 (외부 발송은 초안 → 승인)
