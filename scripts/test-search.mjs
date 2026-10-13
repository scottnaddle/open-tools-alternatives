import { chromium } from 'playwright';
import { mkdir } from 'fs/promises';
import { join } from 'path';

const baseURL = process.env.BASE_URL || 'http://localhost:4322';
const outputDir = '/opt/cursor/artifacts/screenshots';

await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  locale: 'ko-KR',
});

console.log(`Testing Pagefind search at ${baseURL}\n`);

const page = await context.newPage();

// Test 1: Search for '포토샵' from search page
console.log('📸 Testing search for "포토샵"...');
await page.goto(`${baseURL}/search/?q=포토샵`, { waitUntil: 'networkidle' });

// Wait for Pagefind to load and search
await page.waitForTimeout(2000);

// Wait for search results to appear
try {
  await page.waitForSelector('.pagefind-ui__results', { timeout: 5000 });
  console.log('   ✓ Search results loaded');
} catch (error) {
  console.log('   ⚠ No results selector found, but continuing...');
}

const outputPath = join(outputDir, 'search-photoshop.png');
await page.screenshot({
  path: outputPath,
  fullPage: true,
});
console.log(`   ✓ Screenshot saved to ${outputPath}`);

// Test 2: Check that synonyms work - search for "사진 편집"
console.log('\n📸 Testing synonym search for "사진 편집"...');
await page.goto(`${baseURL}/search/?q=사진 편집`, { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);

const outputPath2 = join(outputDir, 'search-photo-editing.png');
await page.screenshot({
  path: outputPath2,
  fullPage: true,
});
console.log(`   ✓ Screenshot saved to ${outputPath2}`);

// Test 3: Landing page search
console.log('\n📸 Testing landing page search integration...');
await page.goto(`${baseURL}/`, { waitUntil: 'networkidle' });
await page.waitForTimeout(500);

// Fill in search box
await page.fill('#hq', '압축');
await page.waitForTimeout(300);

const outputPath3 = join(outputDir, 'landing-search-autocomplete.png');
await page.screenshot({
  path: outputPath3,
  fullPage: false,
});
console.log(`   ✓ Screenshot saved to ${outputPath3}`);

await browser.close();
console.log('\n✨ Search testing complete!');
