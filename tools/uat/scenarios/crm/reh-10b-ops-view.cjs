// Pilot rehearsal step 10, the AA side (runbook docs/ops/runbooks/pilot-rehearsal.md, "A10c reads the ops view"): AA
// ground operations read the trip's release in the staff console (S-02).
// Given: REH-08c-aa-confirmed: Adventure Asia confirmed tour X on the rehearsal trip, so the CRM released the
//        travellers' details to AA ops (crm_ops_release_sync, hourly or nudged at the confirm); REH-10-portal filled the
//        lead's details. The AA staff console E2E user (crm-staff, root ADR 0006a A10c: groups crm-ops + crm-support,
//        synthetic agencies only) is signed in outside the recording (e-mail code from the MFA-only mailbox prefix).
// When:  the staff user opens the S-02 board on the CRM web /staff/ops and then the rehearsal trip's release.
// Then:  the board lists the trip under the rehearsal agency, its row naming tour X's departure (rows of any other
//        agency are blurred; the CRM lists only synthetic agencies to this user anyway); the release page shows that
//        departure and the lead traveller's name (the minimal details of the travellers panel). Each view is written to the agency's audit ("AA ops viewed trip X"): the agency side of that is a
//        read the orchestrator makes on the CRM audit, not on this screen.
// Read only in the browser (the API records the S-02 view itself). No manifest download, no support session, no
// break-glass. No LLM call. Cost $0.
const { step, ro } = require('../../lib/dryrun-page.cjs');
const { syntheticRowPatterns } = require('../../lib/pilot-guard.cjs');
const R = require('./_reh.cjs');

const flat = (t) => String(t || '').replace(/[\s\u00ad\u200b-\u200d\u2060]+/g, '');

let s;

const sc = ro({
  id: 'REH-10b-ops-view',
  app: 'crm',
  identity: 'crm-staff',
  title: 'Rehearsal: Adventure Asia ground operations read the trip\'s release',
  titleVi: 'Diễn tập: bộ phận điều hành của Adventure Asia xem thông tin chuyến được chuyển giao',
  baseURL: R.crm.PARTNER,
  allowRows: { rows: '[data-testid="staff-ops-board"] [data-testid="kit-datatable-row"], [data-testid="staff-ops-board"] table tbody tr', allow: syntheticRowPatterns() },
  blurText: ['\\bAA-?\\d{3,4}\\b'],
  scrollBlock: 'center',
  meta: { agency: R.REHEARSAL_AGENCY },
  steps: [
    step('An Adventure Asia operations user opens the staff console. The board lists the trips agencies have released to AA ground operations.',
      'Một nhân viên điều hành của Adventure Asia mở bảng điều khiển nội bộ. Bảng liệt kê các chuyến đại lý đã chuyển cho bộ phận điều hành của AA.',
      async (page, h) => {
        s = R.need(R.load(), ['trip_id', 'lead_name', 'departure', 'r08c_done_at'], 'REH-08c-aa-confirmed');
        await R.sha(page, sc, 'start');
        await h.goto('/staff/ops');
        await h.expect(page.getByTestId('staff-ops-board')).toBeVisible({ timeout: 30_000 });
        await h.assertRowsFiltered();
      }),
    step('The rehearsal agency\'s trip is on the board, with the Adventure Asia departure it travels on.',
      'Chuyến của đại lý diễn tập có trên bảng, kèm chuyến khởi hành của Adventure Asia mà khách đi.',
      async (page, h) => {
        const link = page.locator(`[data-testid="staff-ops-board"] a[href*="${s.trip_id}"]`).first();
        await h.expect(link).toBeVisible({ timeout: 20_000 });
        await h.expect(link).toHaveAttribute('href', new RegExp(`/staff/ops/${R.AGENCY_ID}/${s.trip_id}`));
        const row = page.locator('[data-testid="staff-ops-board"] tr, [data-testid="staff-ops-board"] [data-testid="kit-datatable-row"]')
          .filter({ has: page.locator(`a[href*="${s.trip_id}"]`) }).last(); // `has` is relative to the row
        // The departure id wraps in its cell (break opportunities inside it): compare without whitespace / zero-width.
        await h.expect.poll(async () => flat(await row.innerText()), { timeout: 20_000 }).toContain(flat(s.departure.departure_id));
        await h.scrollTo(link);
        await h.hover(row);
      }),
    step('Opening it shows the release: the departure and the travellers\' minimal details, such as the lead traveller\'s name.',
      'Mở chuyến sẽ thấy phần chuyển giao: chuyến khởi hành và thông tin tối thiểu của khách, như tên khách đứng tên.',
      async (page, h) => {
        await h.click(page.locator(`[data-testid="staff-ops-board"] a[href*="${s.trip_id}"]`).first());
        await page.waitForURL(`**/staff/ops/${R.AGENCY_ID}/${s.trip_id}`, { timeout: 20_000 });
        const rel = page.getByTestId('staff-release');
        await h.expect(rel).toBeVisible({ timeout: 30_000 });
        await h.expect.poll(async () => flat(await rel.innerText()), { timeout: 20_000 }).toContain(flat(s.departure.departure_id));
        await h.expect(rel).toContainText(s.lead_name.split(' ')[0]);
        await h.hover(rel);
        await R.sha(page, sc, 'end');
      }),
  ],
});

sc.prepare = async () => {
  if (process.env.UAT_STORAGE_STATE) return;
  const { ensureState } = require('../../lib/signin.cjs');
  sc.storageState = (await ensureState('crm-staff')).file;
};

module.exports = sc;
