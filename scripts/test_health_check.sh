#!/usr/bin/env bash
# 배포 헬스체크: 로컬 서버로 재시도·상태 토큰·실패 로그·롤백 연결을 확인한다.
# 운영 사이트에는 붙지 않는다.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
# shellcheck source=health_check.sh
. "$ROOT/scripts/health_check.sh"

export HEALTH_ATTEMPTS=3
export HEALTH_CONNECT_TIMEOUT=1
export HEALTH_MAX_TIME=1
export HEALTH_RETRY_DELAYS="0 0"

CONTROL=$(mktemp)
HITS=$(mktemp)
DIST=$(mktemp)
PORTFILE=$(mktemp)
spid=""
out=""

cleanup() {
  if [ -n "$spid" ]; then
    kill "$spid" 2>/dev/null || true
    wait "$spid" 2>/dev/null || true
  fi
  rm -f "$CONTROL" "$HITS" "$DIST" "$PORTFILE"
}
trap cleanup EXIT

printf 'body{color:#123}\n' >"$DIST"
GEN=0
set_mode() {
  GEN=$((GEN + 1))
  printf '%s %s\n' "$GEN" "$1" >"$CONTROL"
  : >"$HITS"
}
set_mode ok

export CONTROL HITS DIST
python3 -u - "$CONTROL" "$HITS" "$DIST" >"$PORTFILE" <<'PY' &
import os, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CONTROL, HITS, DIST = sys.argv[1:4]
GOOD = open(DIST, "rb").read()
BAD = b"/*mismatch*/\n" + GOOD
STALL = 15

class H(BaseHTTPRequestHandler):
    gen = None
    counts = {}

    def log_message(self, fmt, *args):
        return

    def _mode(self):
        raw = open(CONTROL, encoding="utf-8").read().split()
        gen = raw[0] if raw else "0"
        mode = raw[1] if len(raw) > 1 else "ok"
        if gen != H.gen:
            H.gen = gen
            H.counts = {}
        return mode

    def _hit(self, path):
        with open(HITS, "a", encoding="utf-8") as fh:
            fh.write(path + "\n")

    def _count(self, path):
        H.counts[path] = H.counts.get(path, 0) + 1
        return H.counts[path]

    def _send(self, status, body, ctype="text/plain; charset=utf-8"):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(data)

    def _stall(self):
        time.sleep(STALL)
        try:
            self._send(200, b"late")
        except Exception:
            return

    def _slow_body(self):
        blob = b"x" * 200000
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(blob)))
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            for i in range(0, len(blob), 20):
                self.wfile.write(blob[i:i + 20])
                self.wfile.flush()
                time.sleep(0.05)
        except Exception:
            return

    def _html(self, mode):
        if mode == "no-assets":
            return "<!doctype html><html><head><title>x</title></head><body>hi</body></html>"
        extra = ""
        if mode == "root-link":
            extra += '<a href="/apps/bad">bad</a>'
        if mode == "asset-404":
            extra += '<script src="/alternatives/gone.js"></script>'
        return (
            "<!doctype html><html><head>"
            '<link rel="stylesheet" href="/alternatives/style.css?v=abc">'
            '<link rel="stylesheet" href="/alternatives/_astro/Base.css">'
            f"</head><body>{extra}</body></html>"
        )

    def do_GET(self):
        mode = self._mode()
        path = self.path.split("?", 1)[0]
        self._hit(path)
        if path == "/slow-body":
            self._slow_body()
            return
        if path == "/always-502":
            self._send(502, b"")
            return
        if path == "/flaky-502":
            if self._count(path) == 1:
                self._send(502, b"")
            else:
                self._send(200, b"ok")
            return
        if path == "/alternatives/" and mode == "home-timeout":
            self._stall()
            return
        if path == "/alternatives/pagefind/pagefind.js" and mode == "pagefind-timeout":
            self._stall()
            return
        if path == "/alternatives/pagefind/pagefind.js" and mode == "pagefind-flaky":
            if self._count(path) < 3:
                self._stall()
                return
        if path == "/alternatives/gone.js":
            self._send(404, b"")
            return
        if path in ("/ping", "/"):
            self._send(200, b"ok")
            return
        if path == "/alternatives/":
            self._send(200, self._html(mode), "text/html; charset=utf-8")
            return
        if path in ("/alternatives/skills/", "/alternatives/about/"):
            self._send(200, b"ok")
            return
        if path == "/alternatives/pagefind/pagefind.js":
            self._send(200, b"ok")
            return
        if path == "/alternatives/_astro/Base.css":
            self._send(200, b"/*base*/\n", "text/css")
            return
        if path == "/alternatives/style.css":
            body = BAD if mode == "css-mismatch" else GOOD
            self._send(200, body, "text/css")
            return
        self._send(404, b"")

httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
print(httpd.server_address[1], flush=True)
httpd.serve_forever()
PY
spid=$!

ORIGIN=""
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if [ -s "$PORTFILE" ]; then
    PORT=$(tr -d '[:space:]' <"$PORTFILE")
    ORIGIN="http://127.0.0.1:${PORT}"
    if curl -q -sf -o /dev/null --connect-timeout 1 --max-time 2 "${ORIGIN}/ping"; then
      break
    fi
  fi
  sleep 0.1
done
if [ -z "$ORIGIN" ] || ! curl -q -sf -o /dev/null --connect-timeout 1 --max-time 2 "${ORIGIN}/ping"; then
  echo "로컬 헬스체크 서버가 뜨지 않음" >&2
  exit 1
fi

fail() {
  echo "✗ $1" >&2
  if [ -n "$out" ]; then
    printf '%s\n' "----- output -----" "$out" >&2
  fi
  exit 1
}

hits_of() {
  local n
  n=$(grep -c "^${1}$" "$HITS" || true)
  printf '%s\n' "$n"
}

health_rc=0
run_check() {
  health_rc=0
  out=$(check_deploy_health "$DIST" "$ORIGIN" 2>&1) || health_rc=$?
}

assert_has() {
  printf '%s\n' "$out" | grep -F "$1" >/dev/null || fail "$2"
}

assert_lacks() {
  if printf '%s\n' "$out" | grep -F "$1" >/dev/null; then
    fail "$2"
  fi
}

# 1) 빠른 200 은 토큰이 정확히 200
token=$(http_probe "${ORIGIN}/ping")
[ "$token" = "200" ] || fail "ping token=${token}"

# 2) 헤더 200 뒤 본문이 max-time 을 넘기면 예전 한 줄은 200000, 새 검사는 timeout
legacy=$(curl -q -s -o /dev/null -w "%{http_code}" --max-time 1 "${ORIGIN}/slow-body" || echo "000")
token=$(
  HEALTH_ATTEMPTS=1 http_probe "${ORIGIN}/slow-body"
)
[ "$legacy" = "200000" ] || fail "회귀 재현 실패 legacy=${legacy}"
[ "$token" = "timeout" ] || fail "slow-body token=${token}"
case "$token" in
  *000*) fail "timeout 토큰에 000 이 붙음: ${token}" ;;
esac

# 3) 전송이 끝난 404 는 재시도하지 않는다
set_mode ok
token=$(http_probe "${ORIGIN}/missing")
[ "$token" = "404" ] || fail "404 token=${token}"
[ "$(hits_of /missing)" = "1" ] || fail "404 를 재시도함 hits=$(hits_of /missing)"

# 4) 502 한 번은 재시도 후 200. 성공하면 남은 횟수를 쓰지 않는다
set_mode ok
errf=$(mktemp)
token=$(http_probe "${ORIGIN}/flaky-502" 2>"$errf")
[ "$token" = "200" ] || fail "flaky-502 token=${token}"
[ "$(hits_of /flaky-502)" = "2" ] || fail "502 재시도 횟수=$(hits_of /flaky-502)"
grep -q "↻ 1/3 HTTP 502  ${ORIGIN}/flaky-502" "$errf" || fail "502 재시도 로그 없음: $(cat "$errf")"
rm -f "$errf"

# 5) 계속 502 면 3회 뒤에도 502 로 실패
token=$(http_probe "${ORIGIN}/always-502" 2>/dev/null)
[ "$token" = "502" ] || fail "always-502 token=${token}"
[ "$(hits_of /always-502)" = "3" ] || fail "502 한도=$(hits_of /always-502)"

# 6) 정상 사이트는 통과하고 상태 줄이 3자리를 넘지 않는다
set_mode ok
run_check
[ "$health_rc" = "0" ] || fail "정상 검사가 실패 rc=${health_rc}"
assert_lacks "✗" "정상 검사에 실패 표시"
assert_lacks "CDN 캐시" "정상 CSS 를 불일치로 봄"
assert_has "✓ /alternatives/style.css?v=abc = ${DIST}" "CSS 일치 로그 없음"
if printf '%s\n' "$out" | grep -E '^  [0-9]{4,}'; then
  fail "상태 코드가 3자리를 넘음"
fi

# 6b) 이번 빌드 CSS 가 없으면 CDN 불일치로 위장하지 않고 실패
missing="${DIST}.missing"
rm -f "$missing"
real_dist="$DIST"
DIST="$missing"
run_check
DIST="$real_dist"
[ "$health_rc" = "1" ] || fail "없는 CSS 가 통과"
assert_has "이번 빌드 CSS가 없음: ${missing}" "없는 CSS 문구 없음"
assert_lacks "CDN 캐시" "없는 CSS 를 CDN 불일치로 적음"

# 7) pagefind 두 번 시간 초과 후 세 번째는 200 이면 배포는 통과
set_mode pagefind-flaky
run_check
[ "$health_rc" = "0" ] || fail "일시 시간 초과를 실패로 봄 rc=${health_rc}"
assert_has "↻ 1/3 timeout  ${ORIGIN}/alternatives/pagefind/pagefind.js" "pagefind 재시도 로그 없음"
assert_has "  200  ${ORIGIN}/alternatives/pagefind/pagefind.js" "pagefind 최종 200 없음"
assert_lacks "200000" "재시도 로그에 200000"

# 8) pagefind 가 계속 느리면 URL 을 남기고 실패. 200 으로 위장하지 않는다
set_mode pagefind-timeout
run_check
[ "$health_rc" = "1" ] || fail "지속 시간 초과가 통과 rc=${health_rc}"
assert_has "✗ 상태 확인 실패: ${ORIGIN}/alternatives/pagefind/pagefind.js (timeout)" "실패한 URL 로그 없음"
assert_lacks "200000" "실패 로그에 200000"

# 9) CSS 바이트가 다르면 CDN 메시지로 실패. 시간 초과로 바꾸지 않는다
set_mode css-mismatch
run_check
[ "$health_rc" = "1" ] || fail "CSS 불일치가 통과"
assert_has "CDN 캐시 의심" "CDN 불일치 문구 없음"
assert_lacks "✗ 상태 확인 실패: ${ORIGIN}/alternatives/style.css?v=abc" "CSS 불일치를 수신 실패로 적음"

# 10) 에셋 참조가 없으면 실패
set_mode no-assets
run_check
[ "$health_rc" = "1" ] || fail "에셋 없음이 통과"
assert_has "홈 HTML에서 에셋 참조를 찾지 못함" "에셋 없음 문구 없음"

# 11) 루트 절대 링크는 실패
set_mode root-link
run_check
[ "$health_rc" = "1" ] || fail "루트 절대 링크가 통과"
assert_has "하위경로(/alternatives) 누락" "루트 링크 문구 없음"

# 12) 에셋 404 는 URL 을 남기고 한 번만 요청
set_mode asset-404
run_check
[ "$health_rc" = "1" ] || fail "에셋 404 가 통과"
assert_has "✗ 상태 확인 실패: ${ORIGIN}/alternatives/gone.js (404)" "에셋 404 URL 없음"
[ "$(hits_of /alternatives/gone.js)" = "1" ] || fail "에셋 404 를 재시도함"

# 13) 홈 HTML 시간 초과는 URL 을 남기고, 빈 본문을 에셋 없음으로 오진하지 않는다
set_mode home-timeout
run_check
[ "$health_rc" = "1" ] || fail "홈 시간 초과가 통과"
assert_has "✗ 상태 확인 실패: ${ORIGIN}/alternatives/ (timeout)" "홈 URL 실패 로그 없음"
assert_has "홈 HTML을 받지 못해 에셋 참조 검사를 건너뜀: ${ORIGIN}/alternatives/" "에셋 검사 건너뜀 로그 없음"
assert_lacks "에셋 참조를 찾지 못함" "홈 시간 초과를 에셋 없음으로 적음"

# 14) deploy.sh 는 실패 시 rollback 을 직접 호출한다.
# if 안의 exit 1 은 ERR 트랩을 돌리지 않는다.
python3 - "$ROOT/scripts/deploy.sh" <<'PY'
import sys
from pathlib import Path
text = Path(sys.argv[1]).read_text()
if 'echo "000"' in text or "echo '000'" in text:
    sys.exit("deploy.sh 가 상태 코드 뒤에 000 을 붙인다")
start = text.find("check_deploy_health")
if start < 0:
    sys.exit("check_deploy_health 호출이 없다")
before = text[max(0, start - 600):start]
if "trap - ERR" not in before:
    sys.exit("헬스체크 전에 ERR 트랩을 끄지 않는다")
end = text.find("배포 완료", start)
if end < 0:
    sys.exit("배포 완료 로그를 찾지 못함")
chunk = text[start:end]
if "rollback" not in chunk or "exit 1" not in chunk:
    sys.exit("헬스체크 실패 경로가 rollback 후 종료하지 않는다")
if "health_rc" not in chunk and "health_rc" not in before:
    sys.exit("헬스체크 종료코드를 보존하지 않는다")
print("deploy.sh wiring ok")
PY

# 15) 런북이 재시도·타임아웃·토큰 규칙을 적는다
rb="$ROOT/ops/RUNBOOK.md"
grep -q "30초" "$rb" || fail "런북에 전송 제한 시간이 없다"
grep -q "3회" "$rb" || fail "런북에 재시도 횟수가 없다"
grep -q "200000" "$rb" || fail "런북에 상태 토큰 사고가 없다"
grep -q "408" "$rb" || fail "런북에 일시적 HTTP 상태가 없다"
grep -F -q "상태 확인 실패" "$rb" || fail "런북에 실패 URL 로그가 없다"

echo "✓ health check"
