// Pilot rehearsal step 1b, the staff evidence after an administrator's act (root docs/ops/runbooks/pilot-rehearsal.md,
// step 1b), read only. Entering pilot mode is an admin-role write (POST /admin/tenants/provision, kind agency,
// pilot_weeks 1; the orchestrator through the admin route or the tech lead; never the E2E admin, root ADR 0006a A10b-4),
// and so is the second-pilot refusal (pilot_taken, kept as
// API JSON): neither is filmed (catalogue row REH-01b-pilot-start). Record this right after the marker was provisioned.
// Given: the E2E CIS admin (read-only session); env UAT_REH_MARKER_ID = the marker tenant's id. When: they open Tenant
// 360 > Subscription of the marker. Then: it is kind agency, in pilot mode with an end date ("Pilot until ..."), and
// this session is offered no End pilot (administrators only). Nothing is written. $0. Not in the dry run.
// Pilot guard: the marker is the Dev pilot during this step, so it is not on the synthetic allow-list. Before anything
// is shown, the first step reads the tenant through the admin API (no paint) and stops with pilot_guard unless it
// carries the marker's invented name and kind (lib/rehearsal-admin.cjs MARKER): a real agency is never opened.
const { HOSTS, step, ro, check, openTab } = require('../../lib/dryrun-page.cjs');
const { MARKER, markerId, assertMarker } = require('../../lib/rehearsal-admin.cjs');

let id = null;

async function readTenant(page) {
  const res = await page.request.get(`${HOSTS.cisAdmin}/api/admin/tenants/${id}/subscription`, { headers: { Accept: 'application/json' }, timeout: 30_000 });
  if (res.status() !== 200) throw new Error(`the marker tenant read answered ${res.status()}`);
  return ((await res.json()) || {}).tenant;
}

module.exports = ro({
  id: 'REH-01b-pilot-on',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Pilot rehearsal, step 1b: the marker tenant is in pilot mode',
  titleVi: 'Diễn tập pilot, bước 1b: tenant đánh dấu đang ở chế độ pilot',
  baseURL: HOSTS.cisAdmin,
  prepare: async () => { id = markerId(); },
  steps: [
    step('An administrator put a second invented agency, the marker, into pilot mode. We open its Tenant 360.',
      'Một quản trị viên đã đưa một đại lý giả lập thứ hai, tenant đánh dấu, vào chế độ pilot. Ta mở Tenant 360 của nó.',
      async (page, h) => {
        assertMarker(await readTenant(page), { pilot: true }); // before the first paint: pilot_guard otherwise
        await check(page, h, `/admin/tenants/${id}?tab=subscription`, { heading: MARKER.name, ready: '[data-testid="tenant360-ready"]' });
        await openTab(page, h, 'Subscription');
      }),
    step('The Subscription tab: kind agency, and a Pilot until badge with the pilot\'s end date.',
      'Thẻ Gói dịch vụ: loại agency, và nhãn pilot ghi ngày kết thúc pilot.',
      async (page, h) => {
        const box = page.getByTestId(`tenant-subscription-${id}`);
        await h.expect(box).toBeVisible({ timeout: 30_000 });
        await h.expect(box.getByText(`Kind: ${MARKER.kind}`, { exact: true })).toBeVisible({ timeout: 30_000 });
        await h.expect(box.getByText(/^Pilot until \d{4}-\d{2}-\d{2}$/)).toBeVisible({ timeout: 30_000 });
      }),
    step('Only an administrator may end a pilot: the test admin sees no End pilot button. This is the end of the scenario.',
      'Chỉ quản trị viên được kết thúc pilot: tài khoản quản trị thử nghiệm không thấy nút Kết thúc pilot. Kết thúc kịch bản.',
      async (page, h) => {
        await h.expect(page.getByTestId('end-pilot')).toHaveCount(0);
      }),
  ],
});
