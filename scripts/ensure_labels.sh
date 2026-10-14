#!/usr/bin/env bash
# 이슈에 라벨을 붙이기 전에 저장소에 라벨이 있게 한다.
# 목록의 기준은 ops/LABELS.md. 둘을 함께 고친다.
# 사용: bash scripts/ensure_labels.sh
#       bash scripts/ensure_labels.sh --print   # gh를 호출하지 않고 명령만 출력
set -euo pipefail

print_only=0
if [ "${1:-}" = "--print" ]; then
  print_only=1
elif [ -n "${1:-}" ]; then
  echo "알 수 없는 인자: $1 (사용법: --print)" >&2
  exit 2
fi

if [ "$print_only" -eq 0 ] && ! command -v gh >/dev/null 2>&1; then
  echo "gh 가 없습니다. 라벨을 만들 수 없습니다." >&2
  exit 1
fi

ensure() {
  local name="$1" color="$2" desc="$3"
  if [ "$print_only" -eq 1 ]; then
    printf 'gh label create %q --force --color %q --description %q\n' "$name" "$color" "$desc"
    return
  fi
  gh label create "$name" --force --color "$color" --description "$desc"
}

# AGENTS.md 단계 라벨
ensure "agent/discovery" "d93f0b" "1번 에이전트(발굴) 처리 중"
ensure "agent/research" "fbca04" "2번 에이전트(연구) 처리 중"
ensure "agent/build" "0e8a16" "3번 에이전트(제조) 처리 중"
ensure "agent/verify" "5319e7" "4번 에이전트(검수) 처리 중"
ensure "agent/published" "0e8a16" "5번 에이전트(게시) 완료"
ensure "agent/verifier" "0a3069" "일일 검증 PR. CI 통과 후 스쿼시 자동 병합"

# AGENTS.md 큐·상태 라벨
ensure "queue/research" "1d76db" "조사 필요 (새 대안·스킬 후보 또는 정정)"
ensure "queue/verify" "1d76db" "기존 팩트 재확인"
ensure "queue/deploy" "1d76db" "배포 대기"
ensure "status/blocked-human" "e99695" "사람 개입 필요 (로그인·승인)"
ensure "priority/urgent" "b60205" "긴급 (운영 장애, 유료 전환 공식 발표, 데이터 손상)"

# discover.yml 이 gh issue create --label 로 붙이는 종류
ensure "software" "0052cc" "발굴 슬롯 종류: 소프트웨어(도구)"
ensure "skill" "6f42c1" "발굴 슬롯 종류: AI 스킬"
