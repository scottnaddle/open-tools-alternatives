#!/usr/bin/env bash
# 배포 직후 공개 URL 검사. deploy.sh 가 source 한다. 직접 실행하지 않는다.
#
# 2026-10-22 (run 39700583674): --max-time 20 에 걸린 curl 이
#   CODE=$(curl -w "%{http_code}" ... || echo "000")
# 에서 헤더의 200 과 echo 의 000 을 이어 붙여 200000 을 찍고,
# 홈 HTML 수신은 set -e 로 URL 없이 curl 28 로 죽었다.
# 전송이 끝나 curl 이 0으로 끝났을 때만 3자리 상태를 받는다.
# 시간 초과·연결 실패와 일시적 HTTP 만 재시도하고, 그 외 4xx/3xx 는 바로 실패다.
# 하나라도 실패하면 호출자가 백업을 복원한다.

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  echo "source scripts/health_check.sh — 직접 실행하지 않습니다." >&2
  exit 1
fi

# 프로덕션 기본값. 테스트만 환경변수로 낮춘다. 워크플로는 덮어쓰지 않는다.
: "${HEALTH_ATTEMPTS:=3}"
: "${HEALTH_CONNECT_TIMEOUT:=10}"
: "${HEALTH_MAX_TIME:=30}"
: "${HEALTH_RETRY_DELAYS:=2 5}"

# stdout: 상태 토큰 하나. HTTP 3자리, timeout, curl<종료코드>, badcode.
# 재시도 안내는 stderr. 실패해도 0을 반환해 호출부의 set -e 를 건드리지 않는다.
http_probe() {
  local url="$1"
  local body="${2:-}"
  local attempts="$HEALTH_ATTEMPTS"
  local connect="$HEALTH_CONNECT_TIMEOUT"
  local maxtime="$HEALTH_MAX_TIME"
  local attempt=1
  local rc=0
  local code=""
  local token=""
  local errf=""
  local out="/dev/null"
  local delay=0
  local idx=0
  local n=0
  local -a delays=()

  read -r -a delays <<< "$HEALTH_RETRY_DELAYS"
  errf=$(mktemp) || {
    printf '%s\n' "badcode"
    return 0
  }
  if [ -n "$body" ]; then
    out="$body"
  fi

  while [ "$attempt" -le "$attempts" ]; do
    if [ "$attempt" -gt 1 ]; then
      idx=$((attempt - 2))
      n=${#delays[@]}
      if [ "$n" -eq 0 ]; then
        delay=0
      elif [ "$idx" -ge "$n" ]; then
        delay="${delays[$((n - 1))]}"
      else
        delay="${delays[$idx]}"
      fi
      sleep "$delay"
    fi

    rc=0
    # -q: curlrc 의 --retry 가 -w 를 여러 번 찍지 않게 한다.
    # 종료코드가 0이 아니면 -w 에 200이 남아 있어도 성공으로 쓰지 않는다.
    code=$(curl -q -sS -o "$out" -w "%{http_code}" \
      --connect-timeout "$connect" \
      --max-time "$maxtime" \
      --retry 0 \
      "$url" 2>"$errf") || rc=$?

    if [ "$rc" -eq 0 ] && [[ "$code" =~ ^[0-9]{3}$ ]]; then
      case "$code" in
        408|429|500|502|503|504)
          token="$code"
          if [ "$attempt" -lt "$attempts" ]; then
            echo "  ↻ ${attempt}/${attempts} HTTP ${code}  ${url}" >&2
            attempt=$((attempt + 1))
            continue
          fi
          ;;
        *)
          token="$code"
          ;;
      esac
      break
    fi

    if [ "$rc" -eq 28 ]; then
      token="timeout"
    elif [ "$rc" -ne 0 ]; then
      token="curl${rc}"
    else
      token="badcode"
    fi
    if [ "$attempt" -lt "$attempts" ]; then
      echo "  ↻ ${attempt}/${attempts} ${token}  ${url}" >&2
      attempt=$((attempt + 1))
      continue
    fi
    break
  done

  rm -f "$errf"
  case "$token" in
    [0-9][0-9][0-9]|timeout|badcode|curl[0-9]|curl[0-9][0-9]|curl[0-9][0-9][0-9]) ;;
    *) token="badcode" ;;
  esac
  printf '%s\n' "$token"
}

# 0이면 통과, 그 외는 실패. 롤백은 호출자(deploy.sh)가 한다.
check_deploy_health() {
  local dist_css="${1:-dist/style.css}"
  local origin="${2:-https://edtechnewsroom.com}"
  local FAIL=0
  local work=""
  local home_body=""
  local asset_file=""
  local css_body=""
  local home_url=""
  local code=""
  local home_code=""
  local live_css=""
  local css_url=""
  local a=""
  local full=""
  local u=""

  origin="${origin%/}"
  home_url="${origin}/alternatives/"
  work=$(mktemp -d) || return 1
  home_body="$work/home.html"
  asset_file="$work/assets.txt"
  css_body="$work/live.css"
  : >"$home_body"

  echo "▶ 헬스체크"
  for u in \
    "$home_url" \
    "${origin}/alternatives/skills/" \
    "${origin}/alternatives/about/" \
    "${origin}/alternatives/pagefind/pagefind.js" \
    "${origin}/"
  do
    if [ "$u" = "$home_url" ]; then
      code=$(http_probe "$u" "$home_body") || code="badcode"
      home_code="$code"
    else
      code=$(http_probe "$u") || code="badcode"
    fi
    echo "  ${code}  ${u}"
    if [ "$code" != "200" ]; then
      echo "✗ 상태 확인 실패: ${u} (${code})"
      FAIL=1
    fi
  done

  echo "▶ 에셋 참조 검사 (홈 HTML 기준)"
  if [ "$home_code" != "200" ]; then
    echo "✗ 홈 HTML을 받지 못해 에셋 참조 검사를 건너뜀: ${home_url}"
    rm -rf "$work"
    return 1
  fi

  # 참조된 CSS·JS 를 모두 본다. 예전 head -8 은 뒤쪽 깨진 참조를 놓칠 수 있다.
  {
    grep -oE '(href|src)="/[^"]+\.(css|js)(\?[^"]*)?"' "$home_body" || true
  } | sed -E 's/^(href|src)="//; s/"$//' | sort -u >"$asset_file" || true

  if [ ! -s "$asset_file" ]; then
    echo "✗ 홈 HTML에서 에셋 참조를 찾지 못함"
    FAIL=1
  fi
  while IFS= read -r a; do
    [ -n "$a" ] || continue
    case "$a" in
      /*) ;;
      *)
        echo "✗ 에셋 경로가 절대경로가 아님: ${a}"
        FAIL=1
        continue
        ;;
    esac
    full="${origin}${a}"
    code=$(http_probe "$full") || code="badcode"
    echo "  ${code}  ${full}"
    if [ "$code" != "200" ]; then
      echo "✗ 상태 확인 실패: ${full} (${code})"
      FAIL=1
    fi
  done <"$asset_file"

  live_css=$(grep -oE 'href="/alternatives/style\.css[^"]*"' "$home_body" || true)
  live_css=$(printf '%s\n' "$live_css" | sed -E 's/^href="//; s/"$//')
  live_css=${live_css%%$'\n'*}
  if [ -z "$live_css" ]; then
    echo "✗ 홈 HTML에서 style.css 참조를 찾지 못함"
    FAIL=1
  else
    css_url="${origin}${live_css}"
    code=$(http_probe "$css_url" "$css_body") || code="badcode"
    echo "  ${code}  ${css_url}"
    if [ "$code" != "200" ]; then
      echo "✗ 상태 확인 실패: ${css_url} (${code})"
      FAIL=1
    elif [ ! -f "$dist_css" ]; then
      echo "✗ 이번 빌드 CSS가 없음: ${dist_css}"
      FAIL=1
    elif ! cmp -s "$css_body" "$dist_css"; then
      echo "✗ 운영 ${live_css} 내용이 이번 빌드(${dist_css})와 다름 — CDN 캐시 의심"
      FAIL=1
    else
      echo "  ✓ ${live_css} = ${dist_css}"
    fi
  fi

  if grep -qE 'href="/(apps|tools|skills|compare|_astro)/' "$home_body"; then
    echo "✗ 하위경로(/alternatives) 누락 빌드로 보임 — 루트 절대 링크 발견"
    FAIL=1
  fi

  rm -rf "$work"
  return "$FAIL"
}
