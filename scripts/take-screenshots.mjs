import { chromium } from 'playwright';
import { mkdir } from 'fs/promises';
import { join } from 'path';

const baseURL = process.env.BASE_URL || 'http://localhost:4321';
const outputDir = '/opt/cursor/artifacts/screenshots';

await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  locale: 'ko-KR',
});

const pages = [
  { name: 'landing', path: '/', title: 'Landing Page' },
  { name: 'app-capcut', path: '/apps/capcut/', title: 'App Page - CapCut' },
  { name: 'tool-7-zip', path: '/tools/7-zip/', title: 'Tool Page - 7-Zip' },
  { name: 'compare', path: '/compare/opencut-vs-shotcut/', title: 'Compare Page' },
  { name: 'changes', path: '/changes/', title: 'Changes Page' },
];

console.log(`Taking screenshots from ${baseURL}`);
console.log(`Output directory: ${outputDir}\n`);

for (const { name, path, title } of pages) {
  const page = await context.newPage();
  const url = `${baseURL}${path}`;
  console.log(`📸 ${title}: ${url}`);
  
  try {
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500); // Extra wait for any animations
    
    const outputPath = join(outputDir, `${name}.png`);
    await page.screenshot({
      path: outputPath,
      fullPage: true,
    });
    console.log(`   ✓ Saved to ${outputPath}`);
  } catch (error) {
    console.error(`   ✗ Error: ${error.message}`);
  }
  
  await page.close();
}

await browser.close();
console.log('\n✨ All screenshots captured!');
