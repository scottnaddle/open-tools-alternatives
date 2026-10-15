# main 브랜치 보호 (소유자가 UI에서 설정)

일일 검증 PR의 `gh pr merge --auto --squash` 는 **필수 상태 검사**가 있어야 병합을 기다립니다. 검사가 없으면 스크립트는 자동 병합을 켜지 않습니다. 에이전트 토큰은 브랜치 보호를 바꿀 수 없습니다(2026-10-14 조회 시 403). 아래는 소유자가 UI에서 설정합니다.

2026-10-14에 저장소 visibility 는 `public` 이었습니다. 공개 저장소는 무료 플랜에서도 Rulesets 로 필수 검사를 걸 수 있습니다. 다시 비공개로 두면 GitHub Pro 가 필요합니다.

## 1. 자동 병합 허용

**Settings → General → Pull Requests → Allow auto-merge** 를 켭니다.

## 2. Actions 가 PR을 만들고 병합하게

**Settings → Actions → General → Workflow permissions**

- Read and write permissions
- **Allow GitHub Actions to create and approve pull requests** 켜기

`contents: write` 와 `pull-requests: write` 만으로는 `gh pr create` / `gh pr merge --auto` 가 거절될 수 있습니다.

## 3. main 규칙

**Settings → Rules → Rulesets** (또는 Branches → Add branch ruleset) 에서 대상 브랜치 `main`:

- Restrict updates: pull request 로만 병합 (직접 push 금지). 이미 그렇게 운영 중이면 유지합니다.
- Require status checks to pass: 검사 이름 **`build-and-check`** (`.github/workflows/ci.yml` 의 job 이름)
- 병합 전에 브랜치를 최신으로 유지
- **승인 리뷰는 필수로 두지 않습니다.** 리뷰를 필수로 하면 일일 검증 PR이 CI 이후에도 사람 승인 없이는 병합되지 않습니다.
- 콘텐츠·디자인·발굴 PR에는 라벨 `agent/verifier` 를 붙이지 않습니다. 자동 병합 스크립트는 `daily-verifier/` 브랜치에서만 동작합니다.

## 4. 동작 확인

필수 검사가 켜진 뒤에 일일 검증 PR을 보면:

1. 라벨 `agent/verifier`
2. 상태 검사 `build-and-check` 가 녹색이 된 뒤 스쿼시 병합
3. `GITHUB_TOKEN` 병합은 `main` push 로 `deploy.yml` 을 시작하지 않습니다. `Deploy after verifier merge` 가 CI 성공을 보고, 병합 커밋으로 `deploy.yml` 을 호출합니다. 봇이 `workflow_dispatch` 로 돌린 CI도 대상입니다. `push` 로 돈 CI는 대상이 아닙니다.

## 5. 검사가 0건일 때 (PR #36)

`GITHUB_TOKEN` 으로 연 PR은 `pull_request` / `push` 워크플로를 시작하지 않거나, 승인 대기만 만듭니다. 필수 검사 `build-and-check` 가 없으면 자동 병합이 멈춥니다. PAT 는 쓰지 않습니다.

PR #36 (`daily-verifier/20261015`) 은 2026-10-15 00:24 UTC에 봇이 열었고 그때 검사가 없었습니다. 01:55 UTC에 `build-and-check` 가 통과한 뒤 병합되었습니다. **이미 병합되었으므로 닫았다가 다시 열지 않습니다.**

같은 증상(검사 0건, 자동 병합 대기)이 다시 나오면 소유자가 그 PR 번호로 아래를 실행합니다.

```bash
# 사람이 닫았다가 다시 열면 pull_request 의 reopened 로 CI가 시작됩니다.
gh pr close <번호>
gh pr reopen <번호>
```

이 수정이 `main` 에 반영된 뒤에 만들어진 `daily-verifier/` 브랜치는 봇이 `ci.yml` 을 `workflow_dispatch` 로 시작합니다. 검사 이름은 `build-and-check` 입니다. 그 브랜치에 트리거가 이미 있으면 소유자가 직접 다시 돌릴 수도 있습니다.

```bash
gh workflow run ci.yml --ref daily-verifier/YYYYMMDD
```

검사가 통과하면 자동 병합되고, CI가 `Deploy after verifier merge` 를 호출합니다. 사람 PR의 `pull_request` CI는 기존처럼 `workflow_run` 으로 같은 배포 워크플로에 들어옵니다.

키가 아직 없으면 그 배포는 안내만 남기고 건너뜁니다. `ops/DEPLOY_KEY_SETUP.md`
