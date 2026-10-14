#!/usr/bin/env bash
# 열린도구 Alternatives 배포 — 정적 파일 교체만 (nginx·Ghost·Cloudflare·DNS 불문).
# 절차 근거: ops/RUNBOOK.md. 필요한 환경변수:
#   GHOST_SERVER_ROOT_PASSWORD  (필수 — 값 절대 출력 금지)
#   GHOST_SERVER_HOST           (필수 — 서버 주소)
#   SKIP_BUILD=1                (이미 빌드했으면 생략 — CI 워크플로용)
set -euo pipefail

cd "$(dirname "$0")/.."

[ -f ops/FREEZE ] && { echo "⛔ ops/FREEZE 존재 — 배포 중단:"; cat ops/FREEZE; exit 1; }
: "${GHOST_SERVER_ROOT_PASSWORD:?GHOST_SERVER_ROOT_PASSWORD 환경변수 필요}"
: "${GHOST_SERVER_HOST:?GHOST_SERVER_HOST 환경변수 필요}"
command -v sshpass >/dev/null || { echo "sshpass 필요 (brew install hudochenkov/sshpass/sshpass 또는 apt-get install sshpass)"; exit 1; }

REMOTE="root@${GHOST_SERVER_HOST}"
export SSHPASS="${GHOST_SERVER_ROOT_PASSWORD}"
SSH() { sshpass -e ssh -o StrictHostKeyChecking=accept-new "$REMOTE" "$@"; }

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
  chown -R www-data:www-data /tmp/alternatives-new
  rm -rf /var/www/alternatives.new
  mv /tmp/alternatives-new /var/www/alternatives.new"

rollback() {
  echo "✗ 실패 — 백업으로 복원: alternatives.bak-${TS}"
  SSH "set -e
    rm -rf /var/www/alternatives.new
    rm -rf /var/www/alternatives
    cp -a /var/www/alternatives.bak-${TS} /var/www/alternatives
    chown -R www-data:www-data /var/www/alternatives" || echo "⚠️ 자동 복원 실패 — ops/RUNBOOK.md 3절 수동 복원 필요"
}
trap rollback ERR

SSH "set -e
  [ -d /var/www/alternatives ] && rm -rf /var/www/alternatives
  mv /var/www/alternatives.new /var/www/alternatives"

# 4) 헬스체크
echo "▶ 헬스체크"
FAIL=0
for u in \
  "https://edtechnewsroom.com/alternatives/" \
  "https://edtechnewsroom.com/alternatives/skills/" \
  "https://edtechnewsroom.com/alternatives/about/" \
  "https://edtechnewsroom.com/alternatives/pagefind/pagefind.js" \
  "https://edtechnewsroom.com/"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$u" || echo "000")
  echo "  ${CODE}  ${u}"
  [ "$CODE" = "200" ] || FAIL=1
done

# 4-1) HTML이 실제로 참조하는 CSS·JS가 로드되는지 + 하위경로 누락 감지 (2026-10-13 사고 재발 방지)
echo "▶ 에셋 참조 검사 (홈 HTML 기준)"
HTML=$(curl -s --max-time 20 "https://edtechnewsroom.com/alternatives/")
# 캐시 무효화용 쿼리(?v=...)가 붙은 주소도 잡는다
echo "$HTML" | grep -oE '(href|src)="/[^"]+\.(css|js)(\?[^"]*)?"' | sed -E 's/^(href|src)="//; s/"$//' | sort -u | head -8 > /tmp/live-assets.txt
if [ ! -s /tmp/live-assets.txt ]; then
  echo "✗ 홈 HTML에서 에셋 참조를 찾지 못함"; FAIL=1
fi
while IFS= read -r a; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "https://edtechnewsroom.com${a}" || echo "000")
  echo "  ${CODE}  ${a}"
  [ "$CODE" = "200" ] || FAIL=1
done < /tmp/live-assets.txt
# 4-2) CDN이 예전 style.css 를 내보내는지 검사 (2026-10-14 사고: 새 HTML + 캐시된 예전 CSS로 화면 깨짐)
LIVE_CSS=$(echo "$HTML" | grep -oE 'href="/alternatives/style\.css[^"]*"' | head -1 | sed -E 's/^href="//; s/"$//')
if [ -z "$LIVE_CSS" ]; then
  echo "✗ 홈 HTML에서 style.css 참조를 찾지 못함"; FAIL=1
elif ! curl -s --max-time 20 "https://edtechnewsroom.com${LIVE_CSS}" | cmp -s - dist/style.css; then
  echo "✗ 운영 ${LIVE_CSS} 내용이 이번 빌드(dist/style.css)와 다름 — CDN 캐시 의심"; FAIL=1
else
  echo "  ✓ ${LIVE_CSS} = dist/style.css"
fi
if echo "$HTML" | grep -qE 'href="/(apps|tools|skills|compare|_astro)/'; then
  echo "✗ 하위경로(/alternatives) 누락 빌드로 보임 — 루트 절대 링크 발견"; FAIL=1
fi

if [ "$FAIL" != "0" ]; then
  echo "✗ 헬스체크 실패 — 롤백합니다"
  exit 1
fi

trap - ERR
echo "✓ 배포 완료 (백업 남음: /var/www/alternatives.bak-${TS})"
echo "  최근 3개 외 백업 정리는 ops/RUNBOOK.md 6절 — 삭제 전 사용자 확인 필수"
