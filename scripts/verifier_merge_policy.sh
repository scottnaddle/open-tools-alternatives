# 일일 검증 PR만 자동 병합 대상인지 판별한다.
# 브랜치 접두사 daily-verifier/ 와 라벨 agent/verifier 가 둘 다 있어야 한다.
# 콘텐츠·디자인·발굴 PR은 여기 해당하지 않는다.

verifier_branch_ok() {
  case "$1" in
    daily-verifier/*) return 0 ;;
    *) return 1 ;;
  esac
}

# 인자: 줄바꿈으로 구분된 라벨 이름
verifier_label_ok() {
  printf '%s\n' "$1" | grep -qx 'agent/verifier'
}

# CI가 끝난 뒤 배포 대기를 시작해도 되는지.
# pull_request: 사람이 연 검사. workflow_run 이 이 이벤트를 본다.
# workflow_dispatch: 봇이 gh workflow run 으로 돌린 검사. 검사 이름은 build-and-check.
# push 는 넣지 않는다. 토큰 push 는 CI를 시작하지 않고, 사람 push 와 겹치면 배포가 두 번이다.
verifier_ci_followup_ok() {
  event="$1"
  branch="$2"
  verifier_branch_ok "$branch" || return 1
  case "$event" in
    pull_request|workflow_dispatch) return 0 ;;
    *) return 1 ;;
  esac
}

# workflow_dispatch 잡 검사는 ruleset 에 반영되지 않는다.
# 성공한 workflow_dispatch CI 가 이 커밋·브랜치와 같을 때만 Checks API 결과를 남긴다.
# stdin: gh run list JSON (event, conclusion, headSha, headBranch, url)
# env: SHA, BRANCH. 맞으면 URL 을 출력하고 0, 아니면 1.
verifier_dispatch_success_url() {
  python3 -c '
import json, os, sys
sha = os.environ.get("SHA") or ""
branch = os.environ.get("BRANCH") or ""
if not sha or not branch:
    sys.exit(1)
try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(1)
if not isinstance(data, list):
    sys.exit(1)
for run in data:
    if not isinstance(run, dict):
        continue
    if run.get("event") != "workflow_dispatch":
        continue
    if run.get("conclusion") != "success":
        continue
    if run.get("headSha") != sha or run.get("headBranch") != branch:
        continue
    url = run.get("url") or ""
    if not url:
        sys.exit(1)
    print(url)
    sys.exit(0)
sys.exit(1)
'
}

# 인자: GitHub rules API JSON (브랜치에 적용 중인 규칙 배열).
# required_status_checks 안에 context build-and-check 가 있으면 0.
verifier_rules_require_ci() {
  printf '%s' "$1" | python3 -c '
import json, sys
raw = sys.stdin.read().strip()
if not raw:
    sys.exit(1)
data = json.loads(raw)
if not isinstance(data, list):
    sys.exit(1)
for rule in data:
    if not isinstance(rule, dict) or rule.get("type") != "required_status_checks":
        continue
    params = rule.get("parameters") or {}
    checks = params.get("required_status_checks") or []
    for item in checks:
        context = item.get("context") if isinstance(item, dict) else item
        if context == "build-and-check":
            sys.exit(0)
sys.exit(1)
'
}
