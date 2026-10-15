# 예시 체험 2건 — K12 Teacher Skills, Presentation Skills

- 날짜: 2026-10-15
- PR: (미정)

머리글: 2026-10-15 — 예시 체험 2건 추가 (anthropics-k12-teacher-skills, pamelafox-presentation-skills). 둘 다 Claude Code CLI로 직접 돌린 결과.

## 기록

- `anthropics-k12-teacher-skills`: k12-lesson-plan-creation 스킬로 중2 과학 '광합성' 45분 수업 자료(수업 계획서·학생 활동지·관찰 기록지)를 만들었다. 결과 그림은 학생 활동지 미리보기 첫 부분. 성취기준은 스킬 기본값인 NGSS(MS-LS1-6) 영어 원문으로 나왔다.
- `pamelafox-presentation-skills`: make-revealjs-presentation 스킬로 광합성 복습 슬라이드 6장을 만들었다. 결과 그림은 6장을 한 장씩 찍어 모은 것.
- `scripts/check_links.py`: 이미지 확장자 목록에 `webp` 를 더했다 (예시 체험 결과 그림 링크가 404로 잡혔다).
- 남은 문제: `check_links.py` 의 '예시 데이터' 공개 금지 검사가 예시 체험 칸의 "예시 데이터" 배지와 부딪쳐 실패한다. 규칙 쪽을 고칠지 배지 문구를 바꿀지 사람이 정해야 한다.
