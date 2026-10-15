import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { ogImages } from './integrations/og-images.mjs';

// 운영은 뉴스룸 하위 경로(/alternatives/)에서 서비스된다.
// 기본값을 안전 쪽(/alternatives)으로 반전 — env 누락으로 루트 경로 빌드되는 사고(2026-10-13) 재발 방지.
// 로컬 루트 경로로 개발하고 싶을 때만 ASTRO_BASE=/ 로 덮어쓴다.
const site = 'https://edtechnewsroom.com';
const base = process.env.ASTRO_BASE || '/alternatives';
const feedUrl = new URL('feed.xml', new URL(base.endsWith('/') ? base : `${base}/`, site)).href;

export default defineConfig({
  site,
  base,
  trailingSlash: 'always',
  integrations: [
    sitemap({
      customPages: [feedUrl],
      filter: (page) => !page.includes('/pagefind/'),
    }),
    ogImages(),
  ],
});
