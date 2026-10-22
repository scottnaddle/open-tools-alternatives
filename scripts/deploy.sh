#!/usr/bin/env bash
# 열린도구 Alternatives 배포 — 정적 파일 교체만 (nginx·Ghost·Cloudflare·DNS 불문).
# SSH 키로 비-root 사용자 deploy 에 접속한다. 비밀번호·root 는 쓰지 않는다.
# 필요한 환경변수 (ops/DEPLOY_KEY_SETUP.md):
#   DEPLOY_HOST            서버 주소. 값은 저장소에 적지 않는다.
#   DEPLOY_USER            기본 deploy
#   DEPLOY_SSH_KEY         개인키 본문. 또는 DEPLOY_SSH_KEY_FILE 경로
#   DEPLOY_KNOWN_HOSTS     ssh-keyscan 한 줄. StrictHostKeyChecking=yes
#   SKIP_BUILD=1           이미 빌드했으면 생략
set -euo pipefail

cd "$(dirname "$0")/.."
# shellcheck source=health_check.sh
. "$(dirname "$0")/health_check.sh"

[ -f ops/FREEZE ] && { echo "⛔ ops/FREEZE 존재 — 배포 중단:"; cat ops/FREEZE; exit 1; }
: "${DEPLOY_HOST:?DEPLOY_HOST 환경변수 필요. ops/DEPLOY_KEY_SETUP.md}"
DEPLOY_USER="${DEPLOY_USER:-deploy}"
: "${DEPLOY_KNOWN_HOSTS:?DEPLOY_KNOWN_HOSTS 환경변수 필요. ops/DEPLOY_KEY_SETUP.md}"
if [ -z "${DEPLOY_SSH_KEY:-}" ] && [ -z "${DEPLOY_SSH_KEY_FILE:-}" ]; then
  echo "DEPLOY_SSH_KEY 가 없습니다. 비밀번호로 대체하지 않습니다. ops/DEPLOY_KEY_SETUP.md" >&2
  exit 1
fi

KEY_TMP=""
if [ -n "${DEPLOY_SSH_KEY_FILE:-}" ]; then
  KEY_PATH="$DEPLOY_SSH_KEY_FILE"
else
  KEY_TMP=$(mktemp)
  printf '%s\n' "$DEPLOY_SSH_KEY" > "$KEY_TMP"
  chmod 600 "$KEY_TMP"
  KEY_PATH="$KEY_TMP"
fi
KNOWN_TMP=$(mktemp)
printf '%s\n' "$DEPLOY_KNOWN_HOSTS" > "$KNOWN_TMP"
chmod 600 "$KNOWN_TMP"
cleanup_ssh() {
  [ -n "$KEY_TMP" ] && rm -f "$KEY_TMP"
  rm -f "$KNOWN_TMP"
}
trap cleanup_ssh EXIT

REMOTE="${DEPLOY_USER}@${DEPLOY_HOST}"
SSH() {
  ssh -i "$KEY_PATH" \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=yes \
    -o UserKnownHostsFile="$KNOWN_TMP" \
    "$REMOTE" "$@"
}

# 1) 빌드
if [ "${SKIP_BUILD:-0}" != "1" ]; then
  echo "▶ 빌드"
  npm ci
  npm run build
fi

# 2) 빌드 산출물 검사
N_HTML=$(find dist -name index.html | wc -l | tr -d ' ')
[ "$N_HTML" -ge 60 ] || { echo "✗ index.html이 ${N_HTML}개뿐 — 빌드 불완전, 중단"; exit 1; }
[ -f dist/pagefind/pagefind.js ] || { echo "✗ dist/pagefind 없음 — 중단"; exit 1; }
echo "✓ 산출물 검사 통과 (index.html ${N_HTML}개, pagefind 있음)"

# 3) 업로드 → 권한 → 원자적 교체
TS=$(date +%Y%m%d-%H%M%S)
echo "▶ 업로드 (백업: alternatives.bak-${TS})"
tar -C dist -cf - . | SSH "rm -rf /tmp/alternatives-new && mkdir -p /tmp/alternatives-new && tar -C /tmp/alternatives-new -xf -"
SSH "set -e
  cp -a /var/www/alternatives /var/www/alternatives.bak-${TS}
  find /tmp/alternatives-new -type d -exec chmod 755 {} +
  find /tmp/alternatives-new -type f -exec chmod 644 {} +
  rm -rf /var/www/alternatives.new
  mv /tmp/alternatives-new /var/www/alternatives.new"

rollback() {
  echo "✗ 실패 — 백업으로 복원: alternatives.bak-${TS}"
  SSH "set -e
    rm -rf /var/www/alternatives.new
    rm -rf /var/www/alternatives
    cp -a /var/www/alternatives.bak-${TS} /var/www/alternatives
    find /var/www/alternatives -type d -exec chmod 755 {} +
    find /var/www/alternatives -type f -exec chmod 644 {} +" || echo "⚠️ 자동 복원 실패 — ops/RUNBOOK.md 3절 수동 복원 필요"
}
trap rollback ERR

SSH "set -e
  [ -d /var/www/alternatives ] && rm -rf /var/www/alternatives
  mv /var/www/alternatives.new /var/www/alternatives"

# 4) 헬스체크. 일시적 지연은 scripts/health_check.sh 가 재시도한다.
# if 안의 exit 은 ERR 트랩을 돌리지 않으므로, 실패하면 rollback 을 직접 호출한다.
# 검사 도중 ERR 이 돌면 return 코드가 트랩에 먹히고 롤백이 두 번 날 수 있어 잠시 끈다.
trap - ERR
set +e
check_deploy_health "dist/style.css"
health_rc=$?
set -e
trap rollback ERR
if [ "$health_rc" -ne 0 ]; then
  echo "✗ 헬스체크 실패 — 롤백합니다"
  rollback
  exit 1
fi

trap - ERR
echo "✓ 배포 완료 (백업 남음: /var/www/alternatives.bak-${TS})"
echo "  최근 3개 외 백업 정리는 ops/RUNBOOK.md 6절 — 삭제 전 사용자 확인 필수"
