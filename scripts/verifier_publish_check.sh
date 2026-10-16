#!/usr/bin/env bash
# ruleset 이 읽는 검사 이름 build-and-check 를 Checks API 로 성공 처리한다.
# workflow_dispatch 잡이 자동으로 만드는 같은 이름 검사는 PR ruleset 에 들어가지 않는다.
# 이 스크립트는 그 잡의 빌드와 게이트가 이미 통과한 뒤에만 호출한다.
#
# 사용: bash scripts/verifier_publish_check.sh <head-sha> <details-url>
set -euo pipefail

SHA="${1:?head sha}"
DETAILS="${2:-}"
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)

PAYLOAD=$(SHA="$SHA" DETAILS="$DETAILS" NOW="$NOW" python3 -c '
import json, os
body = {
    "name": "build-and-check",
    "head_sha": os.environ["SHA"],
    "status": "completed",
    "conclusion": "success",
    "started_at": os.environ["NOW"],
    "completed_at": os.environ["NOW"],
    "external_id": "verifier-ruleset-check",
    "output": {
        "title": "일일 검증 검사 통과",
        "summary": "workflow_dispatch 잡이 만든 검사는 ruleset에 들어가지 않습니다. 이 검사는 그 잡의 빌드와 게이트가 통과한 뒤 Checks API로 남긴 같은 이름의 결과입니다.",
    },
}
url = os.environ.get("DETAILS") or ""
if url.startswith("https://"):
    body["details_url"] = url
print(json.dumps(body))
')

printf '%s' "$PAYLOAD" | gh api --method POST "repos/{owner}/{repo}/check-runs" --input -
echo
echo "ruleset용 build-and-check 성공을 남겼습니다: $SHA"
