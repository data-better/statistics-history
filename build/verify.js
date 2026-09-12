const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const ROOT = '/home/claude/site';

const PAGES = [
  'index.html', 'timeline.html', 'works.html', 'people.html', 'appendix.html',
  'story/index.html', 'story/00-prehistory.html', 'story/01-probability.html',
  'story/02-errors.html', 'story/03-society.html', 'story/04-three-waves.html',
  'story/05-computation.html', 'story/06-data-science.html', 'story/07-epilogue.html',
];

(async () => {
  const browser = await chromium.launch();
  let fail = 0;
  const external = [];

  for (const p of PAGES) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    page.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
    page.on('request', r => { if (/^https?:/.test(r.url())) external.push(p + ' -> ' + r.url()); });

    await page.goto('file://' + path.join(ROOT, p));
    await page.waitForTimeout(400);

    const text = await page.evaluate(() => document.body.innerText);
    const bad = p === "appendix.html" ? 0 : (text.match(/우도/g) || []).length;  // 부록의 치환 대조표는 원본 표기를 그대로 싣는다
    const navCount = await page.locator('.site-nav a').count();
    const horiz = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);

    const flag = (errs.length || bad || navCount !== 6 || horiz) ? 'FAIL' : 'ok  ';
    if (flag === 'FAIL') fail++;
    console.log(`${flag} ${p.padEnd(30)} nav=${navCount} 우도=${bad} hscroll=${horiz} errs=${errs.length}`);
    errs.slice(0, 3).forEach(e => console.log('      ! ' + e.slice(0, 180)));
    await ctx.close();
  }

  // 타임라인 상세 기능 점검
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  await page.goto('file://' + path.join(ROOT, 'timeline.html'));
  await page.waitForTimeout(500);
  const nodes = await page.locator('.tl-node').count();
  await page.locator('.tl-node').first().click();
  await page.waitForTimeout(350);
  const detailOpen = await page.locator('.tl-detail.open').count();
  const detailTitle = await page.locator('.tl-detail h2').first().textContent().catch(() => '');
  const urlHasId = page.url().includes('id=');
  console.log(`\n타임라인: 노드 ${nodes}개 / 상세패널 ${detailOpen ? '열림' : '안 열림'} "${(detailTitle||'').slice(0,40)}" / URL에 id ${urlHasId}`);
  await page.screenshot({ path: '/home/claude/build/shot-timeline.png' });

  // 분야 필터
  await page.goto('file://' + path.join(ROOT, 'timeline.html') + '?field=베이즈');
  await page.waitForTimeout(500);
  const bayesNodes = await page.locator('.tl-node').count();
  const badge = await page.locator('.field-badge').first().innerText();
  console.log(`분야 필터(베이즈): 노드 ${bayesNodes}개, 헤더 배지 "${badge.trim()}"`);

  // 잘못된 field 값
  await page.goto('file://' + path.join(ROOT, 'timeline.html') + '?field=존재하지않는분야');
  await page.waitForTimeout(400);
  const allNodes = await page.locator('.tl-node').count();
  console.log(`잘못된 field 값 → 노드 ${allNodes}개 (전체 표시되어야 정상)`);

  // 게이트 → 링크 전파
  await page.goto('file://' + path.join(ROOT, 'index.html'));
  await page.waitForTimeout(300);
  await page.locator('.field-card[data-field="응용"]').click();
  await page.waitForTimeout(300);
  const panelVisible = await page.locator('#field-panel').isVisible();
  await page.locator('.site-nav a', { hasText: '이야기' }).click();
  await page.waitForTimeout(500);
  const propagated = page.url().includes('field=');
  const recBadge = await page.locator('[data-rec]:not([hidden])').count();
  console.log(`게이트: 패널 ${panelVisible ? '열림' : '안 열림'} / 링크 전파 ${propagated} / 추천 배지 ${recBadge}개`);
  await page.screenshot({ path: '/home/claude/build/shot-story-index.png' });

  await page.goto('file://' + path.join(ROOT, 'index.html'));
  await page.waitForTimeout(400);
  await page.screenshot({ path: '/home/claude/build/shot-index.png', fullPage: false });

  await page.goto('file://' + path.join(ROOT, 'story/04-three-waves.html'));
  await page.waitForTimeout(400);
  await page.screenshot({ path: '/home/claude/build/shot-chapter.png' });

  // 모바일 375px
  const m = await browser.newContext({ viewport: { width: 375, height: 800 } });
  const mp = await m.newPage();
  for (const p of ['index.html', 'timeline.html', 'story/04-three-waves.html', 'works.html']) {
    await mp.goto('file://' + path.join(ROOT, p));
    await mp.waitForTimeout(350);
    const h = await mp.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
    console.log(`375px ${p.padEnd(30)} 가로스크롤=${h}`);
  }
  await mp.screenshot({ path: '/home/claude/build/shot-mobile.png' });
  await m.close();

  // 다크 모드
  const d = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: 'dark' });
  const dp = await d.newPage();
  await dp.goto('file://' + path.join(ROOT, 'timeline.html'));
  await dp.waitForTimeout(450);
  await dp.screenshot({ path: '/home/claude/build/shot-dark.png' });
  await d.close();

  console.log(`\n외부 네트워크 요청: ${external.length}건`);
  external.slice(0, 5).forEach(e => console.log('  ' + e));
  console.log(`실패 페이지: ${fail}건`);
  if (errs.length) console.log('타임라인 오류:', errs.slice(0, 3));
  await browser.close();
})();
