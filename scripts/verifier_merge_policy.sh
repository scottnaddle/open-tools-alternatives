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
