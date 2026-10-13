// 데모 화면 녹화 — 자체 호스팅 영상 산출물 생성 (ops/RESEARCH.md: 데모 > 영상 > 이미지)
// 사용법: PLAYWRIGHT_BROWSERS_PATH=... node scripts/record-demo.mjs <대상 html> <출력 webm> [초]
import { chromium } from 'playwright';
import { resolve } from 'path';

const [, , input, output, secs = '14'] = process.argv;
if (!input || !output) { console.error('사용법: node scripts/record-demo.mjs <input.html> <output.webm> [seconds]'); process.exit(1); }

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1280, height: 800 },
  recordVideo: { dir: '/tmp/pw-video', size: { width: 1280, height: 800 } },
});
const page = await ctx.newPage();
await page.goto('file://' + resolve(input));
await page.waitForTimeout(2500); // 폰트·애니메이션 초기화 대기
await page.waitForTimeout(parseInt(secs, 10) * 1000);
await ctx.close(); // 녹화 플러시
await page.video().saveAs(output);
await browser.close();
console.log('✓ 녹화 완료:', output);
