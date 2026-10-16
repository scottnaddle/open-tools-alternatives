#!/usr/bin/env bash
# 네트워크 없이 자동 병합 대상 판별만 확인한다.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck source=verifier_merge_policy.sh
. "$ROOT/scripts/verifier_merge_policy.sh"

verifier_branch_ok "daily-verifier/20261014"
verifier_branch_ok "daily-verifier/20261014-142209"
if verifier_branch_ok "daily-verifier"; then echo "접두사만 있는 이름은 거부해야 함"; exit 1; fi
if verifier_branch_ok "cursor/skill-detail-template-c12f"; then echo "콘텐츠 브랜치는 거부해야 함"; exit 1; fi
if verifier_branch_ok "main"; then echo "main 은 거부해야 함"; exit 1; fi

verifier_label_ok $'queue/research\nagent/verifier'
if verifier_label_ok "agent/verify"; then echo "agent/verify 는 자동 병합 라벨이 아님"; exit 1; fi
if verifier_label_ok "agent/discovery"; then echo "발굴 라벨은 거부해야 함"; exit 1; fi

if grep -q sshpass "$ROOT/scripts/deploy.sh"; then echo "deploy.sh 에 sshpass 가 남아 있음"; exit 1; fi
if grep -q GHOST_SERVER_ROOT_PASSWORD "$ROOT/scripts/deploy.sh"; then echo "deploy.sh 에 root 비밀번호가 남아 있음"; exit 1; fi
if grep -q sshpass "$ROOT/.github/workflows/deploy.yml"; then echo "deploy.yml 에 sshpass 가 남아 있음"; exit 1; fi
if grep -q GHOST_SERVER "$ROOT/.github/workflows/deploy.yml"; then echo "deploy.yml 이 예전 서버 시크릿을 읽음"; exit 1; fi

if verifier_rules_require_ci '[]'; then echo "빈 규칙은 거부해야 함"; exit 1; fi
if verifier_rules_require_ci '[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"other"}]}}]'; then
  echo "다른 검사 이름은 거부해야 함"; exit 1
fi
verifier_rules_require_ci '[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"build-and-check"}]}}]'

verifier_ci_followup_ok pull_request daily-verifier/20261015
verifier_ci_followup_ok workflow_dispatch daily-verifier/20261015
verifier_ci_followup_ok workflow_dispatch daily-verifier/20261015-142209
if verifier_ci_followup_ok push daily-verifier/20261015; then echo "push CI 는 배포 대상이 아님"; exit 1; fi
if verifier_ci_followup_ok pull_request cursor/skill-detail-template-c12f; then echo "콘텐츠 브랜치 CI 는 배포 대상이 아님"; exit 1; fi
if verifier_ci_followup_ok workflow_dispatch main; then echo "main 디스패치는 배포 대상이 아님"; exit 1; fi
if verifier_ci_followup_ok pull_request daily-verifier; then echo "접두사만 있는 브랜치는 거부해야 함"; exit 1; fi

if ! grep -q 'workflow_dispatch' "$ROOT/.github/workflows/ci.yml"; then echo "ci.yml 에 workflow_dispatch 가 없음"; exit 1; fi
if ! grep -q 'gh workflow run ci.yml' "$ROOT/scripts/daily_verifier_pr.sh"; then echo "일일 검증이 ci.yml 을 디스패치하지 않음"; exit 1; fi
if ! grep -q "workflow_run.event == 'workflow_dispatch'" "$ROOT/.github/workflows/deploy-after-verifier.yml"; then
  echo "배포 대기가 workflow_dispatch CI 를 보지 않음"; exit 1
fi
if ! grep -q 'id: build-and-check' "$ROOT/.github/workflows/ci.yml" && ! grep -q '^  build-and-check:' "$ROOT/.github/workflows/ci.yml"; then
  echo "검사 이름이 build-and-check 가 아님"; exit 1
fi

printf '%s' '[{"event":"pull_request","conclusion":"action_required","headSha":"abc","headBranch":"daily-verifier/20261016","url":"https://example.test/pending"},{"event":"workflow_dispatch","conclusion":"success","headSha":"abc","headBranch":"daily-verifier/20261016","url":"https://example.test/ok"}]' \
  | SHA=abc BRANCH=daily-verifier/20261016 verifier_dispatch_success_url | grep -qx 'https://example.test/ok'
if printf '%s' '[{"event":"workflow_dispatch","conclusion":"success","headSha":"other","headBranch":"daily-verifier/20261016","url":"https://example.test/ok"}]' \
  | SHA=abc BRANCH=daily-verifier/20261016 verifier_dispatch_success_url; then
  echo "다른 커밋의 성공은 검사 결과로 쓰면 안 됨"; exit 1
fi
if printf '%s' '[{"event":"pull_request","conclusion":"success","headSha":"abc","headBranch":"daily-verifier/20261016","url":"https://example.test/pr"}]' \
  | SHA=abc BRANCH=daily-verifier/20261016 verifier_dispatch_success_url; then
  echo "pull_request 성공만으로 Checks API 를 부르면 안 됨"; exit 1
fi

if ! grep -q 'checks: write' "$ROOT/.github/workflows/ci.yml"; then echo "ci.yml 에 checks: write 가 없음"; exit 1; fi
if ! grep -q 'checks: write' "$ROOT/.github/workflows/deploy-after-verifier.yml"; then echo "배포 대기에 checks: write 가 없음"; exit 1; fi
if ! grep -q 'pull-requests: write' "$ROOT/.github/workflows/deploy-after-verifier.yml"; then echo "배포 대기가 병합 권한이 없음"; exit 1; fi
if ! grep -q 'verifier_publish_check.sh' "$ROOT/.github/workflows/ci.yml"; then echo "CI가 ruleset 검사를 남기지 않음"; exit 1; fi
if ! grep -q 'gh pr merge' "$ROOT/scripts/deploy_verifier_followup.sh"; then echo "병합 거절 이유를 묻지 않음"; exit 1; fi
if ! grep -q 'name.: .build-and-check' "$ROOT/scripts/verifier_publish_check.sh"; then echo "Checks API 이름이 build-and-check 가 아님"; exit 1; fi

echo "✓ verifier merge policy"
