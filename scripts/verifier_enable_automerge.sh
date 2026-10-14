#!/usr/bin/env bash
# 일일 검증 PR에 agent/verifier 를 붙이고, CI 통과 후 스쿼시 자동 병합을 켠다.
# 저장소에 필수 상태 검사·자동 병합 설정이 없으면 경고만 남기고 0으로 끝난다.
# 콘텐츠·디자인·발굴 PR에서는 호출하지 않는다.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck source=verifier_merge_policy.sh
. "$ROOT/scripts/verifier_merge_policy.sh"

PR_REF="${1:?PR URL 또는 번호}"
BRANCH="${2:?브랜치 이름}"

if ! verifier_branch_ok "$BRANCH"; then
  echo "::error::자동 병합은 daily-verifier/ 브랜치만 대상입니다: $BRANCH"
  exit 1
fi

bash "$ROOT/scripts/ensure_labels.sh"
gh pr ready "$PR_REF" >/dev/null 2>&1 || true
gh pr edit "$PR_REF" --add-label "agent/verifier"

# 필수 검사가 없으면 --auto 가 CI를 기다리지 않고 바로 병합될 수 있다.
# 그 경우에는 요청하지 않고 PR을 열어 둔다.
RULES=$(gh api "repos/{owner}/{repo}/rules/branches/main" 2>/tmp/verifier-rules.err || true)
if [ -z "$RULES" ] || ! verifier_rules_require_ci "$RULES"; then
  echo "::warning::main 에 필수 검사 build-and-check 가 없습니다. 자동 병합을 켜지 않습니다. ops/BRANCH_PROTECTION.md"
  if [ -s /tmp/verifier-rules.err ]; then
    echo "----- rules API stderr -----"
    cat /tmp/verifier-rules.err
  fi
  exit 0
fi
ALLOW=$(gh api "repos/{owner}/{repo}" --jq '.allow_auto_merge')
if [ "$ALLOW" != "true" ]; then
  echo "::warning::Allow auto-merge 가 꺼져 있습니다. 자동 병합을 켜지 않습니다. Settings → General → Pull Requests. ops/BRANCH_PROTECTION.md"
  exit 0
fi

echo "자동 병합 요청: $PR_REF (squash, CI build-and-check 통과 후)"
set +e
gh pr merge "$PR_REF" --squash --auto > /tmp/verifier-automerge.out 2> /tmp/verifier-automerge.err
CODE=$?
set -e
if [ "$CODE" -ne 0 ]; then
  echo "::warning::자동 병합을 켜지 못했습니다. PR은 열린 채로 둡니다. 소유자 설정은 ops/BRANCH_PROTECTION.md 를 보세요."
  echo "----- gh pr merge stderr -----"
  cat /tmp/verifier-automerge.err
  exit 0
fi
cat /tmp/verifier-automerge.out
echo "CI(build-and-check)가 통과하면 GitHub가 이 PR을 스쿼시 병합합니다."
