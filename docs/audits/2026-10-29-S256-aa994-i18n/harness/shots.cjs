const { chromium } = require("/home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App/node_modules/playwright");
const OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-29-S256-aa994-i18n";
const BASE = "http://127.0.0.1:3456";
const PAGES = [["overview", "/admin/overview"], ["review", "/admin/review"], ["content-quality", "/admin/content-quality"], ["jobs", "/admin/jobs"]];
const only = process.argv[2];
(async () => {
  const b = await chromium.launch();
  const report = [];
  for (const lang of ["en", "vi"]) for (const width of [1440, 390]) {
    const ctx = await b.newContext({ viewport: { width, height: width === 390 ? 844 : 900 }, colorScheme: "light",
      isMobile: width === 390, hasTouch: width === 390, locale: lang === "vi" ? "vi-VN" : "en-GB", timezoneId: "Asia/Ho_Chi_Minh" });
    const cookies = [{ name: "cis_admin_token", value: "local.mock.token", url: BASE }, { name: "cis_role", value: "admin", url: BASE }];
    if (lang === "vi") cookies.push({ name: "cis_lang", value: "vi", url: BASE });
    await ctx.addCookies(cookies);
    await ctx.addInitScript(() => { try { localStorage.setItem("cis_theme", "light"); } catch {} });
    for (const [name, path] of PAGES) {
      if (only && name !== only) continue;
      const p = await ctx.newPage();
      const errors = [];
      p.on("console", (m) => m.type() === "error" && errors.push(m.text().slice(0, 160)));
      p.on("pageerror", (e) => errors.push("pageerror " + e.message.slice(0, 160)));
      p.on("response", (r) => r.url().includes("/api/") && r.status() >= 400 && errors.push(`HTTP ${r.status()} ${r.url().replace(BASE, "")}`));
      await p.goto(BASE + path, { waitUntil: "domcontentloaded", timeout: 30000 });
      await p.waitForFunction(() => !document.querySelector('[aria-busy="true"]'), null, { timeout: 15000 }).catch(() => errors.push("still busy after 15s"));
      await p.waitForTimeout(1500);
      const info = await p.evaluate(() => ({ lang: document.documentElement.lang, sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, h1: document.querySelector("h1")?.textContent?.trim() }));
      const file = `${name}-${lang}-${width}-light.png`;
      // The admin shell scrolls inside its main column, not the body: grow the viewport to the content height.
      const tall = await p.evaluate(() => Math.max(document.documentElement.scrollHeight, ...[...document.querySelectorAll("main, main *")]
        .filter((e) => e.scrollHeight > e.clientHeight + 4 && /(auto|scroll)/.test(getComputedStyle(e).overflowY)).map((e) => e.scrollHeight + 80)));
      await p.setViewportSize({ width, height: Math.min(Math.max(tall, 600), 7000) });
      await p.waitForTimeout(500);
      await p.screenshot({ path: `${OUT}/${file}`, fullPage: true });
      report.push({ file, url: p.url().replace(BASE, ""), htmlLang: info.lang, h1: info.h1, overflowX: info.sw > info.cw, errors });
      await p.close();
    }
    await ctx.close();
  }
  await b.close();
  console.log(JSON.stringify(report, null, 1));
})();
