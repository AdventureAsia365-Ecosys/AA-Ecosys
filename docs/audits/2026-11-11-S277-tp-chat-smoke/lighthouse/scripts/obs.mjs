import lighthouse from 'lighthouse'; import * as cl from 'chrome-launcher'; import fs from 'node:fs';
for (const url of process.argv.slice(2)) {
  const udd = fs.mkdtempSync(process.cwd()+'/prof-');
  const c = await cl.launch({ userDataDir: udd, chromePath: '/usr/bin/google-chrome', chromeFlags: ['--headless=new','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
  const r = await lighthouse(url, { port: c.port, logLevel: 'error', onlyCategories: ['performance'] });
  await c.kill(); fs.rmSync(udd, { recursive: true, force: true });
  const m = r.lhr.audits.metrics.details.items[0];
  const lt = (r.lhr.audits['long-tasks']?.details?.items ?? []).slice(0,3).map(t => `${Math.round(t.startTime)}+${Math.round(t.duration)} ${String(t.url).slice(-28)}`);
  console.log(url.slice(17), 'simFCP', Math.round(m.firstContentfulPaint), 'obsFCP', m.observedFirstContentfulPaint, 'obsLCP', m.observedLargestContentfulPaint, 'obsLoad', m.observedLoad, '| first long tasks:', lt.join(' ; '));
}
