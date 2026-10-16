# 스킬 예시 체험 칸

- 날짜: 2026-10-15
- PR: (미정)

머리글: 2026-10-15 — 스킬 상세 페이지에 "예시 체험" 칸(교사 입력 → 결과 → 3단계)을 추가했다. 데이터는 `src/content/skill-demos/`, 아직 0건.

## 기록

- 새 콘텐츠 컬렉션 `skillDemos` (`src/content/skill-demos/<slug>.json`). 파일이 있는 스킬만 칸을 그린다. 늘 "예시 데이터" 배지를 붙인다.
- `scripts/check_skills.py` 가 슬러그 일치, 결과 파일 존재, 3단계, 공식 예시 출처를 검사한다.
- 형식과 하루 1건 추가 절차는 `ops/SKILL_DEMOS.md`.
