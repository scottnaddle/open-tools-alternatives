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
3. `GITHUB_TOKEN` 병합은 `main` push 로 `deploy.yml` 을 시작하지 않습니다. `Deploy after verifier merge` 가 CI 성공을 보고, 병합 커밋으로 `deploy.yml` 을 호출합니다. 봇이 `workflow_dispatch` 로 돌린 CI도 대상입니다. 그 잡 검사만으로는 자동 병합이 안 되므로, 통과 뒤에 Checks API 결과를 남깁니다. `push` 로 돈 CI는 대상이 아닙니다.

## 5. 봇 PR은 승인 대기이고, workflow_dispatch 검사는 ruleset에 안 들어간다

두 가지가 겹치면 자동 병합이 `blocked` 로 남습니다. 저장소 설정을 더 켤 필요는 없습니다. PAT 도 쓰지 않습니다.

1. `GITHUB_TOKEN` 으로 연 PR의 `pull_request` (`opened` / `synchronize` / `reopened`) 는 실행이 만들어지지만 **승인 대기**(`action_required`)입니다. 잡은 0건이고, 쓰기 권한이 있는 사람이 "Approve and run" 을 눌러야 시작합니다. 토큰은 자기 실행을 승인할 수 없습니다. 닫았다가 다시 열어도 `reopened` 가 또 승인 대기를 만듭니다.
2. `workflow_dispatch` 로 돌린 잡 검사 `build-and-check` 는 커밋에는 성공으로 남지만, **PR ruleset 의 필수 검사로 세지지 않습니다.** 필수 검사로 인정되는 이벤트는 `push`, `pull_request`, `pull_request_review`, `pull_request_target`, `deployment`, `deployment_status` 입니다. 그래서 자동 병합은 디스패치 성공만으로는 실행되지 않습니다.

통과한 디스패치 뒤에 Checks API 로 같은 이름 `build-and-check` 성공을 남깁니다. 이 결과는 워크플로 잡 검사가 아니라서 ruleset 에 들어갑니다. 앱은 GitHub Actions(15368)입니다. 이어서 스쿼시 병합을 시도하고, GitHub 가 거절하면 그 응답을 로그에 남깁니다. 사람 PR의 `pull_request` CI는 그대로입니다.

PR #36 은 2026-10-15 01:55 UTC에 소유자가 승인 대기 실행을 승인한 뒤에야 병합되었습니다. **이미 병합되었으므로 닫았다가 다시 열지 않습니다.**

### 오늘 PR #45 (2026-10-16)

`daily-verifier/20261016`, head `1b7a17a`. 디스패치 run `38828235093` 은 성공했지만 ruleset 에 안 들어갔고, `pull_request` run `38828219255` 는 `action_required` 입니다. 자동 병합은 켜져 있고 `mergeable_state` 는 `blocked` 입니다. 이 수정이 main 에 들어가기 전의 브랜치라, 아래 승인 없이는 병합되지 않습니다.

쓰기 권한이 있는 소유자가 PR에서 **Approve and run workflows** 를 누르거나, 실행 페이지에서 승인합니다.

https://github.com/scottnaddle/open-tools-alternatives/actions/runs/38828219255

승인되면 `pull_request` 잡이 `build-and-check` 를 남기고, 이미 켜 둔 스쿼시 자동 병합이 진행됩니다. 설정 변경은 필요 없습니다.

승인 없이 봇 PR의 `pull_request` 워크플로를 돌리려면 GitHub 가 안내하는 대로 GitHub App 설치 토큰이나 PAT 로 PR을 만들어야 합니다. 그 비밀은 이 저장소에 넣지 않습니다.
