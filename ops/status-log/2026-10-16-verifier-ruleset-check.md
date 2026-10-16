# 일일 검증 ruleset 검사

- 날짜: 2026-10-16
- PR: #45 는 이 수정 전에 열려 있어 자동 병합이 멈춤

머리글: 2026-10-16 — 일일 검증은 통과한 뒤 Checks API로 build-and-check를 남긴다. workflow_dispatch 잡 검사는 ruleset에 들어가지 않는다.

## 기록

- PR #45 (`daily-verifier/20261016`, `1b7a17a`)는 자동 병합이 켜져 있어도 `mergeable_state=blocked` 였다. 디스패치 run 38828235093의 `build-and-check`는 성공이지만 PR 검사 목록에 없다. `pull_request` run 38828219255는 `action_required`이고 잡이 0건이다.
- ruleset 25126613은 `build-and-check`만 요구한다. 승인 리뷰 규칙은 없다.
- 오늘 PR #45는 소유자가 run 38828219255를 승인해야 병합된다. 저장소 설정 변경은 하지 않는다.
