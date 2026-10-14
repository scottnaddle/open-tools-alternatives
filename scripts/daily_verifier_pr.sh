#!/usr/bin/env bash
# daily-verifier가 워킹트리에 남긴 콘텐츠 변경을 브랜치로 푸시하고 draft PR을 연다.
# 같은 날짜 브랜치에 열린 PR이 있으면 그 브랜치를 갱신하고, 없으면 시각 접미사를 붙인다.
# PR 생성에 실패하면 저장소 설정 안내와 함께 종료 코드 1로 끝난다.
set -euo pipefail

DATE=$(date -u +%Y%m%d)
BASE_BRANCH="daily-verifier/${DATE}"
BRANCH="$BASE_BRANCH"
PATHS=(
  src/content/tools
  src/content/skills
  src/content/cases
  src/content/lessons
  src/content/reviews
  src/content/changes
)

git config user.name "Daily Verifier Bot"
git config user.email "bot@yeollin-dogu.dev"

if ! git stash push -u -m "daily-verifier ${DATE}" -- "${PATHS[@]}"; then
  echo "스태시할 변경이 없습니다 — PR 생략"
  exit 0
fi

if git ls-remote --exit-code --heads origin "$BASE_BRANCH" >/dev/null 2>&1; then
  OPEN=$(gh pr list --head "$BASE_BRANCH" --state open --json number --jq 'length')
  if [ "${OPEN:-0}" != "0" ]; then
    echo "같은 날짜 브랜치에 열린 PR이 있어 갱신합니다: $BASE_BRANCH"
    git fetch origin "$BASE_BRANCH"
    git checkout -B "$BASE_BRANCH" "origin/$BASE_BRANCH"
    BRANCH="$BASE_BRANCH"
  else
    BRANCH="${BASE_BRANCH}-$(date -u +%H%M%S)"
    echo "같은 날짜 브랜치는 있으나 열린 PR이 없어 새 브랜치를 만듭니다: $BRANCH"
    git checkout -B "$BRANCH"
  fi
else
  git checkout -B "$BRANCH"
fi

if ! git stash pop; then
  echo "::error::기존 브랜치와 오늘의 검증 결과가 충돌합니다. ${BRANCH} 를 확인하세요."
  exit 1
fi

git add "${PATHS[@]}"
if git diff --cached --quiet; then
  echo "커밋할 변경 없음 — PR 생략"
  exit 0
fi

git commit -m "chore: daily verification update ${DATE}" \
  -m "A-grade changes (stars, releases, health) are ready to merge. C-grade changes (license) need 24h recheck before marking ready."

git push origin "$BRANCH"

if [ "$BRANCH" = "$BASE_BRANCH" ]; then
  EXISTING=$(gh pr list --head "$BRANCH" --state open --json url --jq '.[0].url // empty')
  if [ -n "$EXISTING" ]; then
    echo "기존 PR을 갱신했습니다: $EXISTING"
    exit 0
  fi
fi

set +e
gh pr create \
  --title "Daily Verification — ${DATE}" \
  --body-file .github/workflows/templates/daily-verifier-pr.md \
  --base main \
  --head "$BRANCH" \
  --draft > /tmp/pr-url.txt 2> /tmp/pr-err.txt
CODE=$?
set -e
if [ "$CODE" -ne 0 ]; then
  echo "::error::Pull request 생성에 실패했습니다."
  echo "::error::저장소 소유자가 다음 설정을 켜야 합니다: Settings > Actions > General > Workflow permissions > Allow GitHub Actions to create and approve pull requests"
  echo "::error::gh 오류에 'GitHub Actions is not permitted to create or approve pull requests'가 있으면 그 설정이 꺼져 있는 상태입니다."
  echo "----- gh pr create stderr -----"
  cat /tmp/pr-err.txt
  exit 1
fi
echo "PR 생성: $(cat /tmp/pr-url.txt)"
