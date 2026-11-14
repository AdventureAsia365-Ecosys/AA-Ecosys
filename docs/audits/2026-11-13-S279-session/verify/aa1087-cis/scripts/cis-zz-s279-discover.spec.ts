// S279 verify lane (not committed): read-only discovery as the A10b E2E CIS admin.
import { test } from '@playwright/test';
import fs from 'fs';
import { E2E_CIS_ADMIN_EMAIL, MAILBOX_ADMIN_PREFIX } from '../helpers/mailbox';
import { STAFF_AUTH_HOST, signInByEmailCode } from '../helpers/cognitoSignIn';

const OUT = '/home/nghiep/projects/AA-Ecosys/.tmp-session/S279/verify/aa1087-cis/raw';
const PATHS = (process.env.PATHS ?? '').split(',').filter(Boolean);

test('discover', async ({ page }) => {
  test.skip(process.env.E2EADMIN !== '1', 'opt-in');
  test.setTimeout(240000);
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.getByRole('link', { name: /sign in with company email/i }).click({ timeout: 15000 });
  await page.waitForURL((u) => u.host === STAFF_AUTH_HOST, { timeout: 20000 });
  await signInByEmailCode(page, { email: E2E_CIS_ADMIN_EMAIL, prefix: MAILBOX_ADMIN_PREFIX });
  await page.waitForURL((u) => u.origin === 'https://aa-cis.lumiguides.it.com' && u.pathname.startsWith('/admin'), { timeout: 30000 });
  const out: Record<string, unknown> = { at: new Date().toISOString() };
  for (const p of PATHS) {
    const r = await page.request.get(p, { headers: { Accept: 'application/json' } });
    let body: unknown = null;
    try { body = await r.json(); } catch { body = (await r.text()).slice(0, 1500); }
    out[p] = { status: r.status(), body };
  }
  fs.writeFileSync(`${OUT}/${process.env.OUTNAME ?? 'cis-discover'}.json`, JSON.stringify(out, null, 2));
});
