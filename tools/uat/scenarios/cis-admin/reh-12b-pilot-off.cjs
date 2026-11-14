// Pilot rehearsal step 12b, the staff evidence after an administrator's act (root docs/ops/runbooks/pilot-rehearsal.md,
// step 12b), read only. End pilot is an admin-role write (Tenant 360 > Subscription > End pilot, or POST
// /admin/tenants/<id>/pilot/end with a reason; tenant.write) and is not filmed (catalogue row REH-12b-pilot-end; its
// API answer, the tenant.pilot_ended audit row and the pilot slot query stay JSON evidence). Record this right after
// it ended, before the Teardown offboards the marker.
// Given: the E2E CIS admin (read-only session); env UAT_REH_MARKER_ID = the marker tenant's id. When: they open Tenant
// 360 > Subscription of the marker. Then: no Pilot until badge and no End pilot any more; the Dev pilot slot is free.
// Nothing is written. $0. Not in the dry run.
// Pilot guard: as REH-01b-pilot-on, the tenant is read through the admin API first (no paint) and the run stops with
// pilot_guard unless it carries the marker's invented name and kind.
const { HOSTS, step, ro, check, openTab } = require('../../lib/dryrun-page.cjs');
const { MARKER, markerId, assertMarker } = require('../../lib/rehearsal-admin.cjs');

let id = null;

async function readTenant(page) {
  const res = await page.request.get(`${HOSTS.cisAdmin}/api/admin/tenants/${id}/subscription`, { headers: { Accept: 'application/json' }, timeout: 30_000 });
  if (res.status() !== 200) throw new Error(`the marker tenant read answered ${res.status()}`);
  return ((await res.json()) || {}).tenant;
}

module.exports = ro({
  id: 'REH-12b-pilot-off',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Pilot rehearsal, step 12b: the marker tenant left pilot mode',
  titleVi: 'Diễn tập pilot, bước 12b: tenant đánh dấu đã rời chế độ pilot',
  baseURL: HOSTS.cisAdmin,
  prepare: async () => { id = markerId(); },
  steps: [
    step('At the end of the rehearsal, an administrator ended the marker\'s pilot. We open its Tenant 360 again.',
      'Cuối buổi diễn tập, một quản trị viên đã kết thúc pilot của tenant đánh dấu. Ta mở lại Tenant 360 của nó.',
      async (page, h) => {
        assertMarker(await readTenant(page), { pilot: false }); // before the first paint: pilot_guard otherwise
        await check(page, h, `/admin/tenants/${id}?tab=subscription`, { heading: MARKER.name, ready: '[data-testid="tenant360-ready"]' });
        await openTab(page, h, 'Subscription');
      }),
    step('The pilot badge and End pilot are gone: the pilot slot is free again. This is the end of the scenario.',
      'Nhãn pilot và nút Kết thúc pilot đã biến mất: chỗ pilot lại trống. Kết thúc kịch bản.',
      async (page, h) => {
        const box = page.getByTestId(`tenant-subscription-${id}`);
        await h.expect(box).toBeVisible({ timeout: 30_000 });
        await h.expect(box.getByText(`Kind: ${MARKER.kind}`, { exact: true })).toBeVisible({ timeout: 30_000 });
        await h.expect(box.getByText(/Pilot until/)).toHaveCount(0);
        await h.expect(page.getByTestId('end-pilot')).toHaveCount(0);
      }),
  ],
});
