import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://edtechnewsroom.com',
  base: process.env.ASTRO_BASE || '/',
  trailingSlash: 'always',
});
