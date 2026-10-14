# 배포 SSH 키 설정 (소유자가 한 번만)

자동 배포는 `deploy` 사용자와 SSH 키로만 접속합니다. root 비밀번호와 `sshpass` 는 쓰지 않습니다.
키가 없으면 워크플로는 **배포를 건너뛰고 안내만 남긴 뒤 성공**으로 끝납니다. 그래서 이 설정을 마치기 전에는 사이트가 깨지지 않습니다.

서버 주소는 이 문서에 적지 않습니다. 이미 쓰던 호스트를 `YOUR_SERVER_HOST` 자리에 넣으세요. 비밀값은 채팅이나 저장소에 붙여 넣지 마세요.

## 1. 키 만들기 (내 컴퓨터)

```bash
ssh-keygen -t ed25519 -f "$HOME/.ssh/alternatives_deploy" -C "github-actions-deploy" -N ""
```

- 개인키: `$HOME/.ssh/alternatives_deploy` → GitHub 시크릿 `DEPLOY_SSH_KEY` 본문
- 공개키: `$HOME/.ssh/alternatives_deploy.pub` → 서버 `authorized_keys`

## 2. 서버에서 사용자와 권한

root 로 서버에 들어간 뒤, 아래를 그대로 실행합니다. `/var/www/alternatives` 만 다룹니다. nginx 설정, Ghost, Cloudflare, DNS 는 바꾸지 않습니다.

```bash
sudo adduser --disabled-password --gecos "" deploy
sudo mkdir -p /home/deploy/.ssh
sudo chmod 700 /home/deploy/.ssh
sudo tee /home/deploy/.ssh/authorized_keys >/dev/null << 'EOF'
ssh-ed25519 AAAA...여기에_공개키_한_줄... github-actions-deploy
EOF
sudo chmod 600 /home/deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy /home/deploy/.ssh

# deploy 가 사이트 폴더를 바꾸고, 옆에 백업 폴더를 만들 수 있게 한다.
# /var/www 그룹만 맞춘다. nginx 설정 파일은 건드리지 않는다.
sudo chgrp deploy /var/www
sudo chmod 775 /var/www
sudo chown -R deploy:deploy /var/www/alternatives
sudo find /var/www/alternatives -type d -exec chmod 755 {} +
sudo find /var/www/alternatives -type f -exec chmod 644 {} +
```

파일은 소유자가 `deploy` 이고 모드가 755/644 이라 nginx(`www-data`)가 읽습니다. `chown www-data` 는 하지 않습니다.

nginx reload 는 배포 스크립트가 호출하지 않습니다. 정적 파일 교체만으로 반영됩니다. 나중에 reload 가 꼭 필요할 때만 아래를 추가하세요.

```bash
sudo tee /etc/sudoers.d/deploy-nginx >/dev/null << 'EOF'
deploy ALL=(root) NOPASSWD: /bin/systemctl reload nginx
EOF
sudo chmod 440 /etc/sudoers.d/deploy-nginx
```

## 3. known_hosts 한 줄

내 컴퓨터에서:

```bash
ssh-keyscan -t ed25519 YOUR_SERVER_HOST
```

출력 한 줄을 시크릿 `DEPLOY_KNOWN_HOSTS` 에 넣습니다. 호스트 키를 확인하지 않고 접속하지 않습니다.

접속 시험:

```bash
ssh -i "$HOME/.ssh/alternatives_deploy" -o IdentitiesOnly=yes deploy@YOUR_SERVER_HOST 'ls /var/www/alternatives | head'
```

## 4. GitHub 시크릿

저장소 **Settings → Secrets and variables → Actions** 에 추가합니다.

| 이름 | 값 |
|---|---|
| `DEPLOY_SSH_KEY` | 개인키 파일 전체 (`-----BEGIN OPENSSH PRIVATE KEY-----` 부터) |
| `DEPLOY_HOST` | 서버 주소 |
| `DEPLOY_USER` | `deploy` |
| `DEPLOY_KNOWN_HOSTS` | `ssh-keyscan` 출력 한 줄 |

키가 저장되면 `main` 에 `src/`, `public/`, Astro 설정, `package.json`, `package-lock.json`, `tsconfig.json`, `scripts/deploy.sh` 가 푸시될 때 배포가 실행됩니다. **Settings → Actions → deploy.yml → Run workflow** 로도 같은 키로 수동 실행됩니다.

예전 시크릿 `GHOST_SERVER_ROOT_PASSWORD` 는 더 이상 읽지 않습니다. 키 배포가 한 번 성공한 뒤에 그 시크릿을 지우면 됩니다. `GHOST_SERVER_HOST` 도 코드에서 쓰지 않습니다. 주소는 `DEPLOY_HOST` 만 사용합니다.

## 5. 키가 없을 때

`DEPLOY_SSH_KEY` 가 비어 있으면 배포 잡은 서버에 접속하지 않고 로그에 `배포 키 없음` 안내를 남긴 뒤 성공으로 끝납니다. root 비밀번호로 넘어가지 않습니다.
