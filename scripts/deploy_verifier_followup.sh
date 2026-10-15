#!/usr/bin/env bash
# CI가 daily-verifier/* 에서 성공한 뒤 호출한다.
# 라벨 agent/verifier 가 있고 병합이 끝나면 deploy.yml 을 workflow_call 할 수 있도록
# 병합 커밋 SHA 를 출력한다. 대상이 아니면 merged=false.
#
# 사용: bash scripts/deploy_verifier_followup.sh <head-branch> <head-sha> [event]
# event: pull_request | workflow_dispatch. 그 외는 배포하지 않는다.
# 출력(GITHUB_OUTPUT 가 있으면 거기에, 아니면 stdout):
#   merged=true|false
#   sha=<merge commit>
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck source=verifier_merge_policy.sh
. "$ROOT/scripts/verifier_merge_policy.sh"

HEAD="${1:?head branch}"
# head sha 는 로그용. 병합 커밋은 PR에서 읽는다.
HEAD_SHA="${2:-}"
EVENT="${3:-pull_request}"

# 같은 병합 커밋으로 workflow_run 과 CI의 직접 호출이 겹치면 배포는 한 번만.
claim_deploy_lock() {
  local sha="$1"
  local err
  err=$(mktemp)
  if gh api "repos/{owner}/{repo}/git/refs" \
      -f ref="refs/verifier-deploy/${sha}" \
      -f sha="$sha" >"$err" 2>&1; then
    rm -f "$err"
    return 0
  fi
  if grep -qi 'Reference already exists' "$err"; then
    echo "이 병합 커밋의 배포는 이미 잡혀 있습니다: $sha"
    rm -f "$err"
    return 1
  fi
  echo "::warning::배포 잠금 ref 를 만들지 못했습니다. 배포는 계속합니다."
  cat "$err"
  rm -f "$err"
  return 0
}

emit() {
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    printf '%s\n' "$1" >> "$GITHUB_OUTPUT"
  else
    printf '%s\n' "$1"
  fi
}

finish_skip() {
  echo "$1"
  emit "merged=false"
  emit "sha="
  exit 0
}

if ! verifier_ci_followup_ok "$EVENT" "$HEAD"; then
  finish_skip "자동 배포 대상 아님 (이벤트 ${EVENT}, 브랜치 ${HEAD})"
fi

NUM=$(gh pr list --head "$HEAD" --state open --json number --jq '.[0].number // empty')
if [ -z "$NUM" ]; then
  NUM=$(gh pr list --head "$HEAD" --state merged --json number --jq '.[0].number // empty')
fi
if [ -z "$NUM" ]; then
  finish_skip "PR을 찾지 못했습니다: $HEAD"
fi

labels() {
  gh pr view "$NUM" --json labels --jq '.labels[].name'
}

if ! verifier_label_ok "$(labels)"; then
  finish_skip "라벨 agent/verifier 가 없습니다. 자동 병합·배포하지 않습니다: #$NUM"
fi

# 자동 병합은 CI가 녹색이 된 직후 반영된다. 잠시 기다린다.
for _ in $(seq 1 30); do
  STATE=$(gh pr view "$NUM" --json state --jq '.state')
  if [ "$STATE" = "MERGED" ]; then
    SHA=$(gh pr view "$NUM" --json mergeCommit --jq '.mergeCommit.oid // empty')
    if [ -z "$SHA" ]; then
      echo "병합됨 #$NUM 인데 병합 커밋을 아직 읽지 못했습니다. 다시 봅니다."
      sleep 20
      continue
    fi
    echo "병합됨 #$NUM ${SHA} (head ${HEAD_SHA:-unknown}, event ${EVENT})"
    if ! claim_deploy_lock "$SHA"; then
      finish_skip "배포 잠금이 이미 있습니다: #$NUM ${SHA}"
    fi
    emit "merged=true"
    emit "sha=$SHA"
    exit 0
  fi
  if [ "$STATE" = "CLOSED" ]; then
    finish_skip "PR #$NUM 이 병합 없이 닫혔습니다."
  fi
  sleep 20
done

echo "::warning::PR #$NUM 이 아직 열려 있습니다. 필수 검사(build-and-check)와 Allow auto-merge 설정을 ops/BRANCH_PROTECTION.md 에서 확인하세요. 배포는 호출하지 않습니다."
emit "merged=false"
emit "sha="
