# 2026-10-26 주간 후보 반영

머리글: 2026-10-26 — 도구 5개·스킬 2개를 추가하고 Inkscape 최신 안정 태그를 1.4.4로 바꿈

## 기록

- 엔지니어 초안(2026-10-26)의 도구 5개(Xournal++, OpenBoard, PDF Arranger, LosslessCut, PDF4QT)와 스킬 2개(airmang/hwpx-plugins, Steven-A3/HWPX-CLAUDE-SKILL)를 `src/content`에 넣었다. 라이선스만 verified이고, 학교 활용·설치·기기·계정·학생 데이터는 초안과 같이 unverified다. usageScope는 personal, offline-install이다.
- 한국어 후기·영상은 사이드카의 koreanReviews, tutorials를 스키마 필드에 옮겼다. 비어 있는 항목은 필드를 만들지 않았다.
- OpenBoard의 분야는 초안대로 이미지·디자인이다. 제안된 "전자칠판 판서"는 화면 분야 목록(영상·오디오, 이미지·디자인, 문서·오피스, 수업 도구, AI, 유틸리티)에 없어 새 분야로 만들지 않았다.
- Inkscape `github.latestRelease`와 `github.official.latestRelease`를 INKSCAPE_1_4_4(2026-05-05, 태그 페이지)로 바꿨다. GitLab Releases API의 최신 Release 객체는 여전히 INKSCAPE_1_4(2024-10-12)이고, 1.4.4 Release 페이지는 404다. `fromTag`를 붙였다.
- 학교 앱 대안 연결은 대체 정도를 새로 단정하지 않기 위해 만들지 않았다. 도구 상세의 "같은 분야의 프로그램"에서 기존 분야 페이지로 들어간다.
