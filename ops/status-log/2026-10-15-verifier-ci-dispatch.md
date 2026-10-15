# 일일 검증 CI 디스패치

- 날짜: 2026-10-15
- PR: #40

머리글: 2026-10-15 — 일일 검증 PR은 workflow_dispatch로 build-and-check를 붙인다. 토큰이 연 pull_request는 검사를 시작하지 않는다.

## 기록

- `GITHUB_TOKEN`의 push/`pull_request`는 `build-and-check`를 시작하지 않는다. daily-verifier가 `ci.yml`을 `workflow_dispatch`로 돌리고, 그 성공이 `deploy-after-verifier`를 부른다. PAT는 쓰지 않는다.
- PR #36은 2026-10-15 00:24 UTC에 검사가 없다가 01:55 UTC에 통과한 뒤 병합되었다. 이미 병합되었으므로 닫았다가 다시 열지 않는다.
- 검사가 0건인 다음 검증 PR은 소유자가 닫았다가 다시 연다. 절차는 `ops/BRANCH_PROTECTION.md` 5절.
