import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  
  // Screenshot 1: Suggest page with toast
  await page.goto('http://localhost:4321/alternatives/suggest/');
  await page.waitForTimeout(1000);
  
  // Fill form
  await page.fill('#app', '미리캔버스');
  await page.fill('#tool', 'Excalidraw');
  await page.waitForTimeout(500);
  
  // Submit form to trigger toast
  await page.click('button[type="submit"]');
  await page.waitForTimeout(500);
  
  await page.screenshot({ path: '/opt/cursor/artifacts/suggest-toast.png', fullPage: false });
  console.log('✓ Saved suggest-toast.png');
  
  // Screenshot 2: Autocomplete no-results state
  await page.goto('http://localhost:4321/alternatives/');
  await page.waitForTimeout(1000);
  
  // Type a query that won't match
  const input = await page.locator('.u034-in');
  await input.click();
  await input.fill('존재하지않는앱');
  await page.waitForTimeout(800);
  
  await page.screenshot({ path: '/opt/cursor/artifacts/autocomplete-no-results.png', fullPage: false });
  console.log('✓ Saved autocomplete-no-results.png');
  
  // Screenshot 3: Landing desktop
  await page.goto('http://localhost:4321/alternatives/');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/opt/cursor/artifacts/landing-desktop.png', fullPage: true });
  console.log('✓ Saved landing-desktop.png');
  
  // Screenshot 4: Landing mobile (375px)
  await page.setViewportSize({ width: 375, height: 667 });
  await page.goto('http://localhost:4321/alternatives/');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/opt/cursor/artifacts/landing-mobile.png', fullPage: true });
  console.log('✓ Saved landing-mobile.png');
  
  // Screenshot 5: Compare page
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto('http://localhost:4321/alternatives/compare/canva-vs-krita/');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/opt/cursor/artifacts/compare-page.png', fullPage: true });
  console.log('✓ Saved compare-page.png');
  
  await browser.close();
  console.log('\nAll screenshots saved to /opt/cursor/artifacts/');
})();
