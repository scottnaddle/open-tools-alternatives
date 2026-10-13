# ops/RUNBOOK.md — 배포·복구 절차

대상: 이 사이트를 배포하거나 복구해야 하는 에이전트. 원칙은 `AGENTS.md` 참고.
**이 절차는 정적 파일 교체만 다룬다. nginx · Ghost · Cloudflare · DNS는 절대 건드리지 않는다.**

## 0. 사전 조건 (최초 1회)

1. GitHub 시크릿 등록 (저장소 Settings → Secrets and variables → Actions):
   - `GHOST_SERVER_ROOT_PASSWORD` — 서버 root 비밀번호 (값은 절대 채팅·문서에 출력하지 않는다)
   - `GHOST_SERVER_HOST` — 서버 주소 (IP)
2. 권한 확인: 워크플로를 실행할 수 있는 계정(`gh auth status`로 확인).

## 1. 표준 배포 (권장 — GitHub Actions 수동 트리거)

```bash
gh workflow run deploy.yml --ref main
gh run watch   # 또는 gh run list --workflow=deploy.yml로 확인
```

워크플로가 하는 일 (scripts/deploy.sh와 동일 로직):

1. `ops/FREEZE` 존재 확인 → 있으면 즉시 중단
2. `npm ci && npm run build` → 빌드 산출물 검사 (index.html 60개 이상, `dist/pagefind/` 존재)
3. 서버에서 기존 폴더 백업: `/var/www/alternatives.bak-<시각>`
4. 임시 폴더에 업로드 → 권한 설정(폴더 755, 파일 644, 소유 www-data) → 원자적 교체(swap)
5. 헬스체크: `/alternatives/`, `/alternatives/skills/`, `/alternatives/about/`, pagefind 자산이 200인지
6. 헬스체크 실패 시 자동으로 백업 복원 후 실패 보고

## 2. 로컬에서 직접 배포 (Actions를 못 쓸 때)

```bash
export GHOST_SERVER_ROOT_PASSWORD='...'   # 값 출력 금지
export GHOST_SERVER_HOST='...'
bash scripts/deploy.sh
```

- 내부적으로 `sshpass -e`를 쓴다 (macOS: `brew install sshpass` 또는 `hudochenkov/sshpass/sshpass`)
- `ops/FREEZE`가 있으면 배포하지 않는다

## 3. 롤백

```bash
# 서버에서 최근 백업 확인 후 (백업명: /var/www/alternatives.bak-YYYYmmdd-HHMMSS)
ssh root@"$GHOST_SERVER_HOST" 'ls -1t /var/www/ | grep alternatives.bak | head -3'
# 문제가 생긴 배포 직후라면:
ssh root@"$GHOST_SERVER_HOST" 'rm -rf /var/www/alternatives && cp -a /var/www/alternatives.bak-<시각> /var/www/alternatives && chown -R www-data:www-data /var/www/alternatives'
```

롤백 후 운영 URL 200 확인 + 뉴스룸 홈(https://edtechnewsroom.com) 정상 확인.

## 4. 헬스체크 목록

| URL | 기대 |
|---|---|
| `/alternatives/` | 200, 홈 타이틀 포함 |
| `/alternatives/skills/` | 200 |
| `/alternatives/about/` | 200 |
| `/alternatives/pagefind/pagefind.js` | 200 (검색 동작의 전제) |
| `https://edtechnewsroom.com/` | 200 (뉴스룸 본체 무사 확인) |

## 5. 긴급 정지

- 게시 중단이 필요하면: `ops/FREEZE` 파일 커밋 (한 줄 사유 + 날짜) → 배포·일일 검증 자동 중단
- 이미 배포된 콘텐츠를 내려야 하는 특수 상황은 사용자와 상의 후 진행 (사이트 전체 대신 해당 페이지 데이터 제거를 우선)

## 6. 서버 백업 정리

- 배포할 때마다 `alternatives.bak-<시각>`이 쌓인다. 최근 3개만 남기고 월 1회 정리(삭제 전 사용자 확인).
- nginx 설정 원본 백업은 서버에 있으나, nginx 자체는 건드리지 않는다.

## 7. 알려진 제약

- 배포 자동화는 **수동 트리거만** 허용된다 (사용자 승인 설계). push 자동 배포는 켜지 않는다.
- 서버가 Docker로 Ghost를 돌리고 nginx가 앞단인 구조다. Ghost 컨테이너(`ghost-production`)와는 무관하게 `/var/www/alternatives/`만 교체한다.
