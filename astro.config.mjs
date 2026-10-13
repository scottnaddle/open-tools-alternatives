import { defineConfig } from 'astro/config';

// 운영은 뉴스룸 하위 경로(/alternatives/)에서 서비스된다.
// 기본값을 안전 쪽(/alternatives)으로 반전 — env 누락으로 루트 경로 빌드되는 사고(2026-10-13) 재발 방지.
// 로컬 루트 경로로 개발하고 싶을 때만 ASTRO_BASE=/ 로 덮어쓴다.
export default defineConfig({
  site: 'https://edtechnewsroom.com',
  base: process.env.ASTRO_BASE || '/alternatives',
  trailingSlash: 'always',
});
