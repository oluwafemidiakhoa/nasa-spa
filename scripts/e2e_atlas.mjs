import { chromium } from 'playwright';
import assert from 'node:assert/strict';

const BASE = process.env.E2E_BASE_URL || 'http://127.0.0.1:4173';
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
const browserErrors = [];

page.on('pageerror', err => browserErrors.push(`pageerror: ${err.message}`));
page.on('console', msg => {
  if (msg.type() === 'error') browserErrors.push(`console.error: ${msg.text()}`);
});

async function waitForAtlasData() {
  await page.waitForFunction(() => document.querySelector('#dataPill')?.textContent?.includes('OFFICIAL NASA XLSX'), null, { timeout: 15000 });
}

async function gotoAtlas(gap = '0801') {
  await page.goto(`${BASE}/atlas?gap=${gap}`, { waitUntil: 'domcontentloaded' });
  await waitForAtlasData();
}

try {
  console.log('1. Load Atlas with a selected NASA gap');
  await gotoAtlas('0801');
  assert.match(await page.locator('#mapTitle').innerText(), /Gap → architecture/i);
  assert.match(await page.locator('#detailTitle').innerText(), /Lunar Dust/i);
  assert.match(await page.locator('.gap.active .gapId').innerText(), /0801/);
  assert.match(await page.locator('#open3D').getAttribute('href'), /\/navigator\?gap=0801$/);
  assert.ok((await page.locator('[data-hit="true"]').count()) > 0, 'Expected mapped architecture nodes for 0801');

  console.log('2. Select a different gap and verify state + URL + 3D handoff update');
  const targetGap = page.locator('.gap').filter({ hasText: 'Mars Transportation Propulsion' }).first();
  await targetGap.click();
  await page.waitForURL(/gap=1104/);
  assert.match(await page.locator('#detailTitle').innerText(), /Mars Transportation Propulsion/i);
  assert.match(await page.locator('#open3D').getAttribute('href'), /\/navigator\?gap=1104$/);

  console.log('3. Exercise GAP ADDRESSED residual-dependency mode');
  await page.locator('[data-state="resolved"]').click();
  await page.waitForSelector('.residualPanel');
  assert.match(await page.locator('.residualPanel').innerText(), /Residual dependency check/i);

  console.log('4. Exercise reverse architecture lookup');
  await page.locator('.modeBtn[data-view="reverse"]').click();
  assert.match(await page.locator('#mapTitle').innerText(), /Architecture → gaps/i);
  assert.ok((await page.locator('.archChoice').count()) > 0, 'Expected architecture choices');
  await page.locator('.archChoice').first().click();
  assert.ok((await page.locator('.reverseGap').count()) > 0, 'Expected at least one reverse-linked gap');

  console.log('5. Exercise gap comparison mode');
  await page.locator('.modeBtn[data-view="compare"]').click();
  assert.match(await page.locator('#mapTitle').innerText(), /Gap comparison/i);
  assert.equal(await page.locator('.compareCard').count(), 2);
  assert.ok((await page.locator('[data-slot="a"]').count()) > 10, 'Expected comparison selectors for loaded gaps');

  console.log('6. Return to gap mode and verify 3D Navigator connection');
  await page.locator('.modeBtn[data-view="gap"]').click();
  const dustGap = page.locator('.gap').filter({ hasText: 'Lunar Dust-Tolerant Systems and Dust Mitigation' }).first();
  await dustGap.click();
  await page.waitForURL(/gap=0801/);
  await Promise.all([
    page.waitForURL(/\/navigator\?gap=0801/),
    page.locator('#open3D').click(),
  ]);
  await page.waitForFunction(() => document.querySelector('#gapTitle')?.textContent?.includes('Lunar Dust'), null, { timeout: 15000 });
  assert.match(await page.locator('#gapTitle').innerText(), /Lunar Dust/i);
  assert.match(await page.locator('#phaseBadge').innerText(), /LUNAR|CISLUNAR/i);

  console.log('7. Verify 3D → Atlas round trip preserves gap');
  await Promise.all([
    page.waitForURL(/\/atlas\?gap=0801/),
    page.locator('#backLink').click(),
  ]);
  await waitForAtlasData();
  assert.match(await page.locator('#detailTitle').innerText(), /Lunar Dust/i);

  console.log('8. Exercise Atlas judge mode start/stop');
  await page.locator('#judgeBtn').click();
  await page.waitForSelector('#judgeDock.show');
  assert.match(await page.locator('#judgeText').innerText(), /NASA|gap|architecture/i);
  await page.locator('#stopJudge').click();

  if (browserErrors.length) {
    throw new Error(`Browser errors detected:\n${browserErrors.join('\n')}`);
  }

  console.log('ATLAS E2E: PASS');
} finally {
  await browser.close();
}
