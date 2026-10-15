# 검색 노출

- 날짜: 2026-10-15
- PR: #39

머리글: 2026-10-15 — 검색 노출(사이트맵, canonical, 페이지별 제목·설명, OG, JSON-LD, 피드 new/update). 피드는 커밋된 변경만 검사한다.

## 기록

- sitemap-index, canonical, 페이지별 title/description, OG PNG, JSON-LD, RSS `feed.xml`. category는 `new` 또는 `update`. 별 수·버전·최근 커밋·확인 시각처럼 숫자나 날짜만 바뀐 기록은 넣지 않는다. 같은 값의 중복 기록은 한 번만 넣는다.
- 피드 검사는 `git ls-files`로 커밋된 변경 기록만 본다. `verify.py`가 빌드 뒤에 작업 트리에 쓰는 기록은 피드에 없으므로 실패로 보지 않는다.
- 소유자 절차는 `ops/SEO.md` (루트 robots.txt, Google·Naver·Daum 확인 변수).
