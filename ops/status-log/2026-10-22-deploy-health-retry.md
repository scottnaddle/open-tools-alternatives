# 배포 헬스체크 일시 지연

- 날짜: 2026-10-22
- 실패한 실행: https://github.com/scottnaddle/open-tools-alternatives/actions/runs/39700583674

머리글: 2026-10-22 — 배포 헬스체크가 느린 연결을 재시도하고, 상태 코드가 200000처럼 붙지 않게 한다.

## 기록

- 20261022 일일 검증(PR #60, main `4ce4263`) 병합 뒤 Deploy after verifier merge 가 헬스체크에서 롤백했다. pagefind.js 줄이 `200000`이었고, 이어서 홈 HTML curl 이 28로 끊기며 실패 URL 없이 백업으로 돌아갔다.
- 직후 같은 주소의 pagefind.js 는 200, 약 45KB였다. 빌드 산출물 검사(index.html 81)는 통과한 뒤였다. 러너에서 서버로 가는 연결이 20초 한도에 걸린 것으로 본다.
- 검증 데이터는 main에만 있다. 운영 파일은 직전 백업이다. 이 수정 병합 뒤 Deploy 를 main으로 수동 실행해야 운영에 올라간다.
