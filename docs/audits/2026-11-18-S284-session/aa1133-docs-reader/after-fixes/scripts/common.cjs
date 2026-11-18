// AA-1133 live check helpers: sign-in state, a page with console / failed-request capture, safe screenshots.
const fs = require('fs');
const path = require('path');
const { ensureState } = require('/home/nghiep/projects/AA-Ecosys/tools/uat/lib/signin.cjs');
const OUT = '/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-18-S284-session/aa1133-docs-reader/after-fixes';
const PRIV = '/home/nghiep/projects/AA-Ecosys/.tmp-session/S284/private-shots';
const BASE = 'https://aa-cis.lumiguides.it.com/admin/docs';
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/;

async function openPage(browser, { width, height, scheme, mobile = false }) {
  const { file: state } = await ensureState('cis-admin');
  const ctx = await browser.newContext({ storageState: state, viewport: { width, height }, colorScheme: scheme,
    isMobile: mobile, hasTouch: mobile, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  await page.addInitScript((s) => { try { localStorage.setItem('theme', s); } catch (e) {} }, scheme);
  const log = { console: [], failed: [] };
  page.on('console', (m) => { if (m.type() === 'error') log.console.push(m.text().slice(0, 300)); });
  page.on('pageerror', (e) => log.console.push('pageerror: ' + String(e).slice(0, 300)));
  page.on('response', (r) => { if (r.status() >= 400) log.failed.push(`${r.status()} ${r.request().method()} ${r.url().slice(0, 200)}`); });
  page.on('requestfailed', (r) => { const f = r.failure(); if (!(f && /ERR_ABORTED/.test(f.errorText))) log.failed.push(`FAILED ${r.url().slice(0, 200)} ${f && f.errorText}`); });
  return { ctx, page, log };
}

async function goto(page, url) {
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(3000);
  const txt = await page.evaluate(() => document.body.innerText);
  if (/session has ended/i.test(txt) || page.url().includes('/login')) throw new Error('SESSION_EXPIRED ' + page.url());
}

async function shot(page, name, opts = {}) {
  let file = path.join(OUT, name + '.png');
  await page.screenshot({ path: file, ...opts });
  if (fs.statSync(file).size >= 300 * 1024) {
    fs.unlinkSync(file);
    file = path.join(OUT, name + '.jpg');
    await page.screenshot({ path: file, type: 'jpeg', quality: 70, ...opts });
  }
  const txt = await page.evaluate(() => document.body.innerText);
  const m = txt.match(EMAIL);
  if (m) {
    const dest = path.join(PRIV, path.basename(file));
    fs.renameSync(file, dest);
    return { file: dest, kb: Math.round(fs.statSync(dest).size / 1024), private: true };
  }
  return { file: path.basename(file), kb: Math.round(fs.statSync(file).size / 1024), private: false };
}

module.exports = { openPage, goto, shot, BASE, OUT };
