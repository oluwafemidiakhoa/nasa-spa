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

async function waitForTrainerData() {
  await page.waitForFunction(
    () => document.querySelector('#dataPill')?.textContent?.includes('OFFICIAL NASA XLSX'),
    null,
    { timeout: 15000 },
  );
}

async function gotoTrainer() {
  await page.goto(`${BASE}/trainer`, { waitUntil: 'domcontentloaded' });
  await waitForTrainerData();
}

try {
  console.log('1. Load product-first Mission Trainer on official NASA data');
  await gotoTrainer();
  assert.match(await page.locator('.brand').innerText(), /MOON→MARS.*MISSION TRAINER/i);
  assert.match(await page.locator('.hero .eyebrow').innerText(), /NASA ARCHITECTURE.*INTERACTIVE MISSION TRAINING/i);
  assert.doesNotMatch(await page.locator('.hero').innerText(), /2026 Challenge · Build a Junior Astronaut Mission Trainer/i);
  assert.ok(Number((await page.locator('#gapCount').innerText()).replace(/,/g, '')) >= 16);
  assert.ok(Number((await page.locator('#objectiveCount').innerText()).replace(/,/g, '')) > 1000);

  console.log('2. Switch between Mars and Lunar training scenarios');
  await page.locator('.missionCard[data-mission="mars"]').click();
  assert.match(await page.locator('#consoleTitle').innerText(), /Mars Surface Outpost/i);
  assert.ok((await page.locator('.decision').count()) >= 4, 'Expected Mars engineering decision cards');
  await page.locator('.missionCard[data-mission="lunar"]').click();
  assert.match(await page.locator('#consoleTitle').innerText(), /Lunar South Pole Outpost/i);

  console.log('3. Spend limited training credits on two NASA-backed decisions');
  await page.locator('.decision[data-key="dust"] .choose').click();
  await page.locator('.decision[data-key="shadow"] .choose').click();
  assert.equal((await page.locator('#selectedCount').innerText()).trim(), '2');
  assert.equal((await page.locator('#budgetLeft').innerText()).trim(), '4');
  assert.match(await page.locator('.decision[data-key="dust"]').innerText(), /Lunar Dust/i);
  assert.match(await page.locator('.decision[data-key="shadow"]').innerText(), /lunar shadow/i);

  console.log('4. Run mission debrief and inspect residual architecture evidence');
  await page.locator('#debriefBtn').click();
  await page.waitForSelector('#debrief.show');
  assert.equal((await page.locator('#statInvestments').innerText()).trim(), '2');
  assert.ok(Number(await page.locator('#statSystems').innerText()) > 0, 'Expected mapped architecture nodes');
  assert.ok((await page.locator('#archGrid .archCard').count()) > 0, 'Expected residual architecture cards');
  assert.equal(await page.locator('#evidenceRows .evidenceRow').count(), 2);

  const firstEvidence = page.locator('#evidenceRows .evidenceRow').first();
  const threeDHref = await firstEvidence.locator('a').filter({ hasText: 'OPEN IN 3D' }).getAttribute('href');
  const atlasHref = await firstEvidence.locator('a').filter({ hasText: 'DECISION ATLAS' }).getAttribute('href');
  const sourceHref = await firstEvidence.locator('a').filter({ hasText: 'NASA SOURCE' }).getAttribute('href');
  assert.match(threeDHref || '', /^\/navigator\?gap=\d{4}$/);
  assert.match(atlasHref || '', /^\/atlas\?gap=\d{4}$/);
  assert.match(sourceHref || '', /^https:\/\/www\.nasa\.gov\//);

  console.log('5. Verify Trainer → 3D handoff loads selected NASA gap context');
  await Promise.all([
    page.waitForURL(/\/navigator\?gap=\d{4}/),
    firstEvidence.locator('a').filter({ hasText: 'OPEN IN 3D' }).click(),
  ]);
  await page.waitForFunction(
    () => document.querySelector('#gapTitle')?.textContent?.trim()?.length > 3,
    null,
    { timeout: 15000 },
  );
  assert.match(await page.locator('#phaseBadge').innerText(), /LUNAR|CISLUNAR|MARS|TRANSIT/i);

  console.log('6. Verify 3D → Atlas preserves the same gap');
  const navUrl = new URL(page.url());
  const selectedGap = navUrl.searchParams.get('gap');
  assert.match(selectedGap || '', /^\d{4}$/);
  await Promise.all([
    page.waitForURL(new RegExp(`/atlas\\?gap=${selectedGap}`)),
    page.locator('#backLink').click(),
  ]);
  await page.waitForFunction(
    () => document.querySelector('#dataPill')?.textContent?.includes('OFFICIAL NASA XLSX'),
    null,
    { timeout: 15000 },
  );
  assert.match(page.url(), new RegExp(`gap=${selectedGap}`));

  console.log('7. Verify direct Trainer → Atlas handoff');
  await gotoTrainer();
  const dustAtlas = page.locator('.decision[data-key="dust"] a').filter({ hasText: 'ATLAS' });
  const dustAtlasHref = await dustAtlas.getAttribute('href');
  assert.match(dustAtlasHref || '', /^\/atlas\?gap=\d{4}$/);
  await Promise.all([
    page.waitForURL(/\/atlas\?gap=\d{4}/),
    dustAtlas.click(),
  ]);
  await page.waitForFunction(
    () => document.querySelector('#dataPill')?.textContent?.includes('OFFICIAL NASA XLSX'),
    null,
    { timeout: 15000 },
  );
  assert.ok((await page.locator('.gap.active').count()) === 1, 'Expected selected Atlas gap state');

  console.log('8. Run the real 30-second judge demo to completion');
  await gotoTrainer();
  await page.locator('#demoBtn').click();
  await page.waitForSelector('#demoDock.show');
  assert.match(await page.locator('#demoCopy').innerText(), /Start with a lunar outpost|NASA data/i);
  await page.waitForFunction(
    () => document.querySelector('#demoCopy')?.textContent?.includes('Demo complete:'),
    null,
    { timeout: 36000 },
  );
  assert.match(await page.locator('#demoBtn').innerText(), /REPLAY 30-SECOND DEMO/i);
  assert.ok(await page.locator('#debrief').evaluate(el => el.classList.contains('show')));
  assert.equal((await page.locator('#statInvestments').innerText()).trim(), '3');
  assert.equal((await page.locator('#selectedCount').innerText()).trim(), '3');
  assert.equal((await page.locator('#budgetLeft').innerText()).trim(), '2');

  console.log('9. Verify the demo can be stopped and restarted cleanly');
  await page.locator('#demoBtn').click();
  await page.waitForSelector('#demoDock.show');
  await page.locator('#stopDemo').click();
  await page.waitForFunction(() => !document.querySelector('#demoDock')?.classList.contains('show'));
  assert.match(await page.locator('#demoBtn').innerText(), /30-SECOND DEMO RUN/i);

  if (browserErrors.length) {
    throw new Error(`Browser errors detected:\n${browserErrors.join('\n')}`);
  }

  console.log('MISSION TRAINER E2E: PASS');
} finally {
  await browser.close();
}
