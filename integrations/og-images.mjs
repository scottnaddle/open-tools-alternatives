// 빌드가 끝난 HTML의 og:image 주소를 읽고, 같은 제목으로 1200×630 PNG를 dist/og/에 만든다.
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Resvg } from '@resvg/resvg-js';

const FONT_DIR = fileURLToPath(new URL('../node_modules/@fontsource/noto-sans-kr/files/', import.meta.url));
const FONT_FILES = [
  'noto-sans-kr-korean-700-normal.woff',
  'noto-sans-kr-latin-700-normal.woff',
  'noto-sans-kr-korean-400-normal.woff',
  'noto-sans-kr-latin-400-normal.woff',
].map((name) => join(FONT_DIR, name));

function decode(text) {
  return text
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

function escapeXml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function wrap(text, max, lines) {
  const len = (s) => [...s].length;
  const words = text.trim().split(/\s+/);
  const out = [];
  let cur = '';
  let i = 0;
  while (i < words.length && out.length < lines) {
    const word = words[i];
    const next = cur ? `${cur} ${word}` : word;
    if (len(next) <= max) {
      cur = next;
      i += 1;
      continue;
    }
    if (cur) {
      out.push(cur);
      cur = '';
      continue;
    }
    const chars = [...word];
    out.push(chars.slice(0, max).join(''));
    words[i] = chars.slice(max).join('');
  }
  if (cur && out.length < lines) out.push(cur);
  if (i < words.length && out.length) {
    const last = [...out[out.length - 1]];
    out[out.length - 1] = `${last.slice(0, Math.max(0, max - 1)).join('')}…`;
  }
  return out;
}

function renderSvg(title) {
  const lines = wrap(title, 18, 3);
  const startY = 250 - (lines.length - 1) * 28;
  const tspans = lines
    .map((line, i) => `<text x="72" y="${startY + i * 78}" fill="#ffffff" font-size="58" font-weight="700" font-family="Noto Sans KR">${escapeXml(line)}</text>`)
    .join('');
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg width="1200" height="630" viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
  <rect width="1200" height="630" fill="#145C3E"/>
  <rect x="0" y="0" width="16" height="630" fill="#1E6A47"/>
  <text x="72" y="92" fill="#D7EDE3" font-size="26" font-family="Noto Sans KR">열린도구 · 학교 앱의 무료 대안</text>
  ${tspans}
  <text x="72" y="568" fill="#D7EDE3" font-size="24" font-family="Noto Sans KR">edtechnewsroom.com/alternatives</text>
</svg>`;
}

function walk(dir, acc) {
  for (const name of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, name.name);
    if (name.isDirectory()) {
      if (name.name === 'pagefind' || name.name === 'og') continue;
      walk(p, acc);
    } else if (name.name === 'index.html') acc.push(p);
  }
  return acc;
}

export function ogImages() {
  return {
    name: 'og-images',
    hooks: {
      'astro:build:done': async ({ dir }) => {
        const root = fileURLToPath(dir);
        const pages = walk(root, []);
        const jobs = new Map();
        const imageRe = /property="og:image" content="([^"]+)"/;
        const altRe = /property="og:image:alt" content="([^"]+)"/;
        for (const file of pages) {
          const html = readFileSync(file, 'utf8');
          const image = html.match(imageRe);
          const alt = html.match(altRe);
          if (!image || !alt) continue;
          const filename = new URL(image[1]).pathname.split('/').pop();
          if (!filename || !filename.endsWith('.png')) continue;
          jobs.set(filename, decode(alt[1]));
        }
        const outDir = join(root, 'og');
        mkdirSync(outDir, { recursive: true });
        for (const [filename, title] of jobs) {
          const svg = renderSvg(title);
          const png = new Resvg(svg, {
            font: { fontFiles: FONT_FILES, loadSystemFonts: false, defaultFontFamily: 'Noto Sans KR' },
            fitTo: { mode: 'width', value: 1200 },
          }).render().asPng();
          writeFileSync(join(outDir, filename), png);
        }
        console.log(`og-images: ${jobs.size}장`);
      },
    },
  };
}
