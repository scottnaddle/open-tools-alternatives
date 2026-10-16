# ops/RUNBOOK.md — 배포·복구 절차

대상: 이 사이트를 배포하거나 복구해야 하는 에이전트. 원칙은 `AGENTS.md` 참고.
**이 절차는 정적 파일 교체만 다룬다. nginx · Ghost · Cloudflare · DNS는 절대 건드리지 않는다.**

## 0. 사전 조건 (최초 1회)

1. SSH 배포 사용자와 키: `ops/DEPLOY_KEY_SETUP.md` 를 그대로 따른다.
   - 시크릿 `DEPLOY_SSH_KEY`, `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_KNOWN_HOSTS`
   - root 비밀번호와 `sshpass` 는 쓰지 않는다. 키가 없으면 워크플로는 배포를 건너뛴다.
2. 일일 검증 자동 병합을 쓰려면 `ops/BRANCH_PROTECTION.md` (Allow auto-merge, 필수 검사 `build-and-check`). 무료 비공개 플랜에서는 UI로만 걸 수 있다.
3. 권한 확인: 워크플로를 실행할 수 있는 계정(`gh auth status`로 확인).

## 1. 배포가 도는 때

1. `main` 에 사이트 파일이 푸시될 때 (`src/`, `public/`, `astro.config.mjs`, `package.json`, `package-lock.json`, `tsconfig.json`, `scripts/deploy.sh`). 문서만 바뀌면 배포하지 않는다.
2. 일일 검증 PR이 CI 후 자동 병합되면 `deploy-after-verifier.yml` 이 병합 커밋으로 `deploy.yml` 을 호출한다. `GITHUB_TOKEN` 병합은 push 워크플로를 시작하지 않기 때문이다. 봇은 `ci.yml` 을 `workflow_dispatch` 로 돌린 뒤, ruleset용 `build-and-check` 를 Checks API로 남기고 병합을 시도한다. 거절 이유와 승인 대기 실행은 `ops/BRANCH_PROTECTION.md` 5절.
3. 수동: `gh workflow run deploy.yml --ref main`

같은 시각에 두 번 들어와도 `production-deploy` 동시성 그룹이 겹치지 않게 순서대로 실행한다.

`DEPLOY_SSH_KEY` 가 없으면 1~3 모두 서버에 접속하지 않고 안내만 남긴 뒤 성공으로 끝난다.

워크플로가 하는 일 (`scripts/deploy.sh`):

1. `ops/FREEZE` 존재 확인 → 있으면 즉시 중단
2. `npm ci && npm run build` → 빌드 산출물 검사 (index.html 60개 이상, `dist/pagefind/` 존재)
3. 서버에서 기존 폴더 백업: `/var/www/alternatives.bak-<시각>`
4. 임시 폴더에 업로드 → 권한 755/644 → 원자적 교체(swap)
5. 헬스체크: `/alternatives/`, `/alternatives/skills/`, `/alternatives/about/`, pagefind 자산이 200인지, 운영 CSS가 이번 빌드와 같은지
6. 헬스체크 실패 시 자동으로 백업 복원 후 실패 보고

## 2. 로컬에서 직접 배포 (Actions를 못 쓸 때)

```bash
export DEPLOY_HOST='YOUR_SERVER_HOST'          # 값은 출력·커밋 금지
export DEPLOY_USER='deploy'
export DEPLOY_SSH_KEY_FILE="$HOME/.ssh/alternatives_deploy"
export DEPLOY_KNOWN_HOSTS="$(ssh-keyscan -t ed25519 "$DEPLOY_HOST")"
bash scripts/deploy.sh
```

- 키가 없으면 실패한다. 비밀번호로 대체하지 않는다.
- `ops/FREEZE`가 있으면 배포하지 않는다.

## 3. 롤백

```bash
# deploy 사용자로 최근 백업 확인 (백업명: /var/www/alternatives.bak-YYYYmmdd-HHMMSS)
ssh -i "$HOME/.ssh/alternatives_deploy" deploy@YOUR_SERVER_HOST 'ls -1t /var/www/ | grep alternatives.bak | head -3'
# 문제가 생긴 배포 직후라면:
ssh -i "$HOME/.ssh/alternatives_deploy" deploy@YOUR_SERVER_HOST 'rm -rf /var/www/alternatives && cp -a /var/www/alternatives.bak-<시각> /var/www/alternatives && find /var/www/alternatives -type d -exec chmod 755 {} + && find /var/www/alternatives -type f -exec chmod 644 {} +'
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

- 배포는 `main` 푸시(경로 필터)와 일일 검증 병합 후 호출, 그리고 수동 실행이다. `DEPLOY_SSH_KEY` 가 없으면 건너뛴다. 콘텐츠·디자인·발굴 PR은 사람이 병합한다.
- 서버가 Docker로 Ghost를 돌리고 nginx가 앞단인 구조다. Ghost 컨테이너(`ghost-production`)와는 무관하게 `/var/www/alternatives/`만 교체한다.

## 8. Actions가 pull request를 만들게 허용

daily-verifier(매일 22:00 UTC)는 검증 결과를 **main에 직접 커밋하지 않고** 열린 PR로 올린다. draft 로 두면 `gh pr merge --auto` 가 거절되므로 draft 를 쓰지 않는다. 이 PR을 만들려면 저장소 소유자가 아래 설정을 켜 두어야 한다.

**Settings > Actions > General > Workflow permissions > Allow GitHub Actions to create and approve pull requests**

- 워크플로 파일의 `permissions: contents: write`, `pull-requests: write`만으로는 부족하다. 위 체크가 꺼져 있으면 `gh pr create`가 `GitHub Actions is not permitted to create or approve pull requests`로 실패한다.
- 같은 날 브랜치(`daily-verifier/YYYYMMDD`)에 열린 PR이 있으면 그 브랜치를 갱신하고, 브랜치만 있고 열린 PR이 없으면 `daily-verifier/YYYYMMDD-HHMMSS`로 새로 만든다.
- 주간 검증(`weekly-audit.yml`)은 PR을 만들지 않는다. summary 브랜치만 push하므로 위 체크와는 별개로 `contents: write`가 필요하다.
- 발굴 슬롯(`discover.yml`)과 주간 검증은 **schedule과 workflow_dispatch만** 사용한다. push 트리거를 넣지 않는다.
- 두 워크플로는 이슈를 만들기 전에 `scripts/ensure_labels.sh`로 라벨을 만든다. `issues: write`가 필요하다. 목록은 `ops/LABELS.md`.
- 일일 검증 PR만 라벨 `agent/verifier` 와 브랜치 `daily-verifier/` 로 자동 스쿼시 병합을 요청한다. 설정은 `ops/BRANCH_PROTECTION.md`. `actions: write` 로 `ci.yml` 을 `workflow_dispatch` 한다. 그 잡 검사는 ruleset에 안 들어가므로, 통과 뒤에 Checks API로 `build-and-check` 를 남긴다. 토큰의 `pull_request` 는 승인 대기입니다.
