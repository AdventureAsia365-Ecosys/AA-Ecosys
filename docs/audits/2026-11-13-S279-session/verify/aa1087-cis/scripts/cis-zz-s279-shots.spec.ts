// S279 verify lane (not committed): A10b admin, Compliance page shots (MODE=before|after) + reads of flag and audit.
import { test, type Page } from '@playwright/test';
import fs from 'fs';
import { E2E_CIS_ADMIN_EMAIL, MAILBOX_ADMIN_PREFIX } from '../helpers/mailbox';
import { STAFF_AUTH_HOST, signInByEmailCode } from '../helpers/cognitoSignIn';

const D = '/home/nghiep/projects/AA-Ecosys/.tmp-session/S279/verify/aa1087-cis';
const FLAG = 'ad4d4fc5-7db6-4d96-88f7-31a472cfc4ff';
const TENANT = '9149d3c6-fcaf-4400-8e7a-4ed5e557e146';
const MODE = process.env.MODE ?? 'before';

async function getJson(page: Page, p: string) {
  const r = await page.request.get(p, { headers: { Accept: 'application/json' } });
  let body: unknown = null; try { body = await r.json(); } catch { body = (await r.text()).slice(0, 800); }
  return { status: r.status(), body };
}

test('shots', async ({ page }) => {
  test.skip(process.env.E2EADMIN !== '1', 'opt-in');
  test.setTimeout(300000);
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await page.getByRole('link', { name: /sign in with company email/i }).click({ timeout: 15000 });
  await page.waitForURL((u) => u.host === STAFF_AUTH_HOST, { timeout: 20000 });
  await signInByEmailCode(page, { email: E2E_CIS_ADMIN_EMAIL, prefix: MAILBOX_ADMIN_PREFIX });
  await page.waitForURL((u) => u.origin === 'https://aa-cis.lumiguides.it.com' && u.pathname.startsWith('/admin'), { timeout: 30000 });
  const out: Record<string, unknown> = { at: new Date().toISOString(), mode: MODE };
  const all = await getJson(page, '/api/admin/tenant-qa/compliance?state=all&kind=subject_gate&limit=200');
  const f = ((all.body as { data?: Record<string, unknown>[] }).data ?? []).find((x) => x.flag_id === FLAG);
  out.flag = f ? { state: f.state, resolution: f.resolution, resolved_by: f.resolved_by, resolved_at: f.resolved_at,
    release_reason: (f.detail as Record<string, unknown>)?.release_reason, tenant_id: f.tenant_id, piece_id: f.piece_id } : null;
  out.total_flags = (all.body as { total?: number }).total;
  for (const [w, h] of [[1440, 900], [390, 844]] as const) {
    await page.setViewportSize({ width: w, height: h });
    await page.goto('/admin/tenant-qa/compliance', { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${D}/shots/aa1087-compliance-${MODE}-open-${w}-light.png`, fullPage: true });
    out[`open_tab_has_piece_${w}`] = await page.evaluate(() => /E2E fixture \(synthetic\) s279/.test(document.body.innerText));
    out[`sideways_${w}`] = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    if (MODE === 'after') {
      await page.getByRole('tab', { name: /^Resolved/ }).first().click({ timeout: 10000 }).catch(async () => {
        await page.getByText('Resolved', { exact: true }).first().click({ timeout: 10000 });
      });
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
      await page.waitForTimeout(2500);
      await page.screenshot({ path: `${D}/shots/aa1087-compliance-after-resolved-${w}-light.png`, fullPage: true });
      out[`resolved_tab_has_piece_${w}`] = await page.evaluate(() => /E2E fixture \(synthetic\) s279/.test(document.body.innerText));
    }
  }
  if (MODE === 'after') {
    out.audit_released = await getJson(page, '/api/admin/platform/audit?scope=all&action=content_compliance.released&limit=10');
    out.audit_staff_request = await getJson(page, `/api/admin/platform/audit?scope=staff&route=${encodeURIComponent(`/admin/tenant-qa/compliance/${FLAG}/release`)}&limit=10`);
    out.audit_staff_request_prefix = await getJson(page, '/api/admin/platform/audit?scope=staff&action=staff.request&limit=15');
    out.tenant_audit = await getJson(page, `/api/admin/tenants/${TENANT}/audit?limit=10`);
    for (const [w, h] of [[1440, 900], [390, 844]] as const) {
      await page.setViewportSize({ width: w, height: h });
      await page.goto('/admin/platform/audit', { waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
      await page.waitForTimeout(3000);
      await page.screenshot({ path: `${D}/shots/aa1087-audit-log-after-${w}-light.png`, fullPage: false });
      out[`audit_page_has_release_${w}`] = await page.evaluate(() => /content_compliance\.released/.test(document.body.innerText));
    }
  }
  fs.writeFileSync(`${D}/raw/aa1087-${MODE}.json`, JSON.stringify(out, null, 2));
});
