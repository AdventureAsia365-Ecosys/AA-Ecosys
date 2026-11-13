// UAT scenario DRILL-01 (catalogue.json): the tenant offboarding erasure saga, DRY RUN drill in the CIS admin.
// Given: the E2E CIS admin (cis-admin, the Dev-only A10b session, signed in unrecorded) and the synthetic audit tenant
//        audit-wildkind-travel (env UAT_DRILL_TENANT, one of the four audit-* slugs), active, with no open request;
//        the saga apply switch is off on Dev.
// When:  they open Data erasure > Tenant offboarding (apply off, the exit windows the settings API reports), offboard the
//        tenant on the
//        Tenants page, start a drill (window 0), Run now, wait for the DRY RUN reports of CIS, Booking and TripPlanner
//        (the CRM is the second stage), then Stop for good and Restore the tenant.
// Then:  each stage-1 app shows its plan hash, the approval stays closed (apply off), the request ends failed with the
//        blocker stopped_by_tech_lead, and the tenant is active again. Nothing is approved or applied: the approve and
//        new-round routes are outside allowWrites (the browser guard aborts them and fails the take) and the API
//        refuses them to the E2E session anyway. The restore cancels the stopped request (phase cancelled).
// Writes (Dev, synthetic tenant only): offboard, drill, advance (Run now), stop, restore; each passes at most once
// (limitWrites) and only for this tenant and this request (pinWrites; any other write method on those paths is aborted
// too). The CIS API accepts them from the E2E session
// only for a synthetic tenant (root ADR 0006a A10b-5). Until that CIS release is live the offboard answers 403
// e2e_read_only: the take fails at that step and nothing changes. after() restores the tenant whenever a step failed
// after the offboard went through (a restore also closes the open erasure request).
// No LLM call; the DRY RUN jobs only read. Cost $0. The wait for the reports polls every 15 s, at most 12 min.
// Session: the CIS access token lives 15 min and the harness aborts the keep-alive POST /api/auth/refresh, so the
// scenario navigates again (proxy.ts refreshes on a page load once the token is within 60 s of expiry) whenever the
// token is that close, and at least every 4 min during the wait; it then re-opens the request's detail pane.
// Logic reused from AA-CIS-App tests/e2e/admin-evidence/erasure-drill.spec.ts. Desktop 1440 x 900.
const { HOSTS, step, check, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');
const { rw, studioCall, limitWrites } = require('../../lib/uat-page.cjs');
const { syntheticRowPatterns } = require('../../lib/pilot-guard.cjs');

const AUDIT = ['audit-atlas-hearth', 'audit-terra-family', 'audit-trail-pulse', 'audit-wildkind-travel'];
const SLUG = (process.env.UAT_DRILL_TENANT || 'audit-wildkind-travel').trim();
if (!AUDIT.includes(SLUG)) throw new Error(`UAT_DRILL_TENANT must be one of ${AUDIT.join(', ')}`);

const TENANTS = '/api/admin/tenants';
const REQS = '/api/admin/job-runner/erasure/requests';
const PAGE = '/admin/tenants/data-erasure?tab=offboarding';
const UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';
const OPEN_PHASES = ['dry_run', 'awaiting_approval', 'apply', 'verify'];
const STAGE_1 = ['booking', 'cis', 'tripplanner'];
const POLL_MS = 15_000;
const WAIT_MS = 12 * 60_000;
// CIS frontend: lib/staffSession.ts STAFF_TOKEN_COOKIE and REFRESH_SKEW_S (a page load refreshes the token this close
// to exp, through GET /api/auth/refresh, which the harness lets through).
const TOKEN_COOKIE = 'cis_admin_token';
const REFRESH_SKEW_S = 60;
const RELOAD_MS = 4 * 60_000;
const REASON = 'UAT drill: erasure saga DRY RUN on a synthetic test agency, restored at the end';

// Path rules of the five writes (URL pathname). allowWrites below is the same list as regex sources on the full URL.
const PATHS = {
  offboard: new RegExp(`^${TENANTS}/${UUID}/offboard$`),
  drill: new RegExp(`^${REQS}/drill$`),
  advance: new RegExp(`^${REQS}/${UUID}/advance$`),
  stop: new RegExp(`^${REQS}/${UUID}/stop$`),
  restore: new RegExp(`^${TENANTS}/${UUID}/restore$`),
};
// RegExp.source keeps the pattern as written (slashes come back escaped): drop ^ and $, end at the path.
const ALLOW = Object.values(PATHS).map((r) => `${r.source.slice(1, -1)}(?:[?#]|$)`);

// Run state (one run per process).
const T = { id: null, name: null };
let rid = null; // the drill request id
let counts = null; // limitWrites counts
const refusedPins = [];
let restored = false;
let lastNav = 0; // last main-frame navigation (ms)
const READ = ['GET', 'HEAD', 'OPTIONS'];

const isPost = (r, re) => r.request().method() === 'POST' && re.test(new URL(r.url()).pathname);
const row = (page) => page.getByTestId('kit-datatable-row').filter({ hasText: SLUG });
const detail = (page) => page.getByTestId('tenant-erasure-detail');
const stepRow = (page, label) => page.getByTestId('tenant-erasure-steps').getByTestId('kit-datatable-row')
  .filter({ hasText: new RegExp(`^\\s*${label}`) });

async function getJson(page, p) {
  const r = await studioCall(page, 'GET', p);
  if (r.status !== 200 || !r.data || typeof r.data !== 'object') throw new Error(`GET ${p.split('?')[0]} answered ${r.status}`);
  return r.data;
}

/** The tenant row of the admin list (include_inactive), or null. */
async function tenantRow(page) {
  const d = await getJson(page, `${TENANTS}?include_inactive=true`);
  const rows = Array.isArray(d) ? d : (d.tenants || []);
  return rows.find((x) => x.slug === SLUG) || null;
}

async function request(page) {
  return (await getJson(page, `${REQS}/${rid}`)).request;
}

const stage1 = (r) => (r.steps || []).filter((s) => s.round === r.round && s.mode === 'dry_run');
const reported = (r) => r.round_apps.length > 0
  && r.round_apps.every((a) => stage1(r).some((s) => s.app === a && (s.plan_hash || s.error_code)));

/**
 * In front of limitWrites: a write reaches the app only for THIS tenant (offboard / restore path, drill body) and THIS
 * drill request (advance / stop). Anything else is aborted before it leaves the browser and fails the step after.
 */
async function pinWrites(page) {
  await page.route((u) => Object.values(PATHS).some((re) => re.test(u.pathname)), (route) => {
    const req = route.request();
    if (READ.includes(req.method())) return route.fallback();
    const p = new URL(req.url()).pathname;
    let ok = false;
    if (req.method() !== 'POST') ok = false; // the five writes are POSTs; limitWrites only counts POSTs
    else if (PATHS.offboard.test(p) || PATHS.restore.test(p)) ok = !!T.id && p.split('/')[4] === T.id;
    else if (PATHS.drill.test(p)) { try { ok = !!T.id && req.postDataJSON().tenant_id === T.id; } catch { ok = false; } }
    else ok = !!rid && p.split('/')[6] === rid;
    if (ok) return route.fallback();
    refusedPins.push(`${req.method()} ${p.replace(new RegExp(UUID, 'g'), '<id>')}`);
    return route.abort('blockedbyclient');
  });
}

function assertPins() {
  if (refusedPins.length) throw new Error(`a write outside this tenant / request was aborted: ${refusedPins.join(', ')}`);
}

/** Seconds left on the staff access token (its JWT exp; the value is never printed), or null when unreadable. */
async function tokenLeftS(page) {
  try {
    const c = (await page.context().cookies(page.url())).find((x) => x.name === TOKEN_COOKIE);
    const exp = c && JSON.parse(Buffer.from(c.value.split('.')[1], 'base64url').toString('utf8')).exp;
    return typeof exp === 'number' ? exp - Date.now() / 1000 : null;
  } catch { return null; }
}

/** Opens this run's request in the detail pane (component state, so a page load closes it). */
async function openRequest(page, h) {
  const rows = page.getByTestId('tenant-erasure-requests').getByTestId('kit-datatable-row')
    .filter({ hasText: T.name }).filter({ hasText: new RegExp(`(${OPEN_PHASES.join('|')})(?![a-z_])`, 'i') });   // cells join with no space: 'drilldry_run1'
  await h.expect(rows).toHaveCount(1, { timeout: 30_000 });
  await h.click(rows.getByRole('button', { name: 'Open', exact: true }));
  await h.expect(detail(page)).toBeVisible({ timeout: 30_000 });
  await h.expect(detail(page)).toContainText(T.name, { timeout: 15_000 });
}

/**
 * Keeps the staff session alive while the scenario stays on one page: loads the offboarding page again (proxy.ts then
 * refreshes the token) when the token is within REFRESH_SKEW_S of its exp, or RELOAD_MS after the last navigation, and
 * re-opens the request. Returns true when it navigated.
 */
async function keepSession(page, h) {
  const left = await tokenLeftS(page);
  if (!((left !== null && left <= REFRESH_SKEW_S) || Date.now() - lastNav >= RELOAD_MS)) return false;
  await check(page, h, PAGE, { heading: 'Data erasure', ready: '[data-testid="tenant-offboarding-ready"]' });
  const after = await tokenLeftS(page);
  if (after !== null && after <= REFRESH_SKEW_S) throw new Error('the staff session could not be refreshed by a page load');
  await openRequest(page, h);
  return true;
}

async function postAnswer(waiting, what) {
  const res = await waiting;
  let body = {};
  try { body = await res.json(); } catch { /* not JSON */ }
  if (res.status() === 403 && body.detail === 'e2e_read_only') {
    throw new Error(`${what} answered 403 e2e_read_only: the CIS release that lets the E2E admin run the drill writes is not live yet`);
  }
  if (res.status() !== 200) throw new Error(`${what} answered ${res.status()}${typeof body.detail === 'string' ? `: ${body.detail.slice(0, 120)}` : ''}`);
  return body;
}

const sc = rw({
  id: 'DRILL-01',
  app: 'cis-admin',
  identity: 'cis-admin',
  paid: false,
  title: 'Tenant offboarding: erasure drill (DRY RUN, stopped, tenant restored)',
  titleVi: 'Offboard tenant: diễn tập xoá dữ liệu (DRY RUN, dừng hẳn, khôi phục tenant)',
  baseURL: HOSTS.cisAdmin,
  allowWrites: ALLOW,
  // Tenant lists (Tenants, Erasure requests) blur every row that is not a synthetic tenant; the per-app steps table of
  // the request names apps only and stays readable.
  allowRows: {
    rows: ':is([data-testid="kit-datatable-row"], table tbody tr):not([data-testid="tenant-erasure-detail"] *)',
    allow: syntheticRowPatterns(),
  },
  steps: [
    step('Data erasure, Tenant offboarding. On Dev the apply switch is off, so nothing can be erased here. The exit windows, editable settings, say how long an agency\'s data waits after it leaves.',
      'Xoá dữ liệu, thẻ Tenant offboarding. Trên Dev công tắc áp dụng đang tắt, nên ở đây không xoá được gì. Thời hạn rời là thiết lập chỉnh được, quy định dữ liệu của đại lý được giữ bao lâu sau khi đại lý rời đi.',
      async (page, h) => {
        counts = await limitWrites(page, Object.entries(PATHS).map(([name, path]) => ({ name, path, max: 1 })));
        await pinWrites(page);
        page.on('framenavigated', (f) => { if (f === page.mainFrame()) lastNav = Date.now(); });
        await check(page, h, PAGE, { heading: 'Data erasure', ready: '[data-testid="tenant-offboarding-ready"]' });
        // The run's tenant: synthetic (the members API offers invites to the E2E admin only on a synthetic tenant),
        // active, and without an open erasure request.
        const t = await tenantRow(page);
        if (!t) throw new Error(`no tenant ${SLUG} on Dev`);
        T.id = String(t.tenant_id);
        T.name = t.name;
        const status = t.status || (t.is_active ? 'active' : 'suspended');
        if (status !== 'active' || t.cancelled_at) throw new Error(`${SLUG} is ${status}, not active: restore it first (an earlier run did not finish)`);
        const access = await getJson(page, `${TENANTS}/${T.id}/members/access`);
        if (!access.actions || access.actions.invite !== true) throw new Error(`${SLUG} is not a synthetic tenant for this session`);
        const list = await getJson(page, REQS);
        if (list.settings.apply_enabled !== false) throw new Error('the saga apply switch is on: a drill runs only with apply off');
        // The windows come from the settings registry (editable in admin): read them, never a literal.
        const w = list.settings.window_days || {};
        for (const app of ['cis', 'crm']) {
          if (!Number.isInteger(w[app]) || w[app] < 0) throw new Error(`the settings report no exit window for ${app} (${w[app]})`);
        }
        sc.meta = { tenant: SLUG, windows: { cis: w.cis, crm: w.crm } };
        const open = list.requests.find((r) => r.tenant_id === T.id && OPEN_PHASES.includes(r.phase));
        if (open) throw new Error(`${SLUG} already has an open erasure request (phase ${open.phase})`);
        const s = page.getByTestId('tenant-erasure-settings');
        await h.scrollTo(s, 'center');
        await h.expect(s).toContainText('off');
        await h.expect(s).toContainText(`${w.cis} days`);
        await h.expect(s).toContainText(`${w.crm} days`);
        await h.hover(s.getByText('off', { exact: true }).first());
        await h.assertRowsFiltered();
      }),
    step('The drill uses an invented test agency. It is still active, so it is offboarded first, on the Tenants page.',
      'Buổi diễn tập dùng một đại lý giả lập dùng để kiểm thử. Đại lý này còn đang hoạt động, nên trước hết phải offboard nó ở trang Tenants.',
      async (page, h) => {
        await check(page, h, '/admin/tenants', { heading: 'Tenants', table: true });
        const r = row(page);
        await h.expect(r).toHaveCount(1, { timeout: 30_000 });
        await h.scrollTo(r, 'center');
        await h.expect(r).toContainText('Active');
        await h.hover(r.getByText(SLUG, { exact: true }));
        await h.assertRowsFiltered();
      }),
    step('Offboard asks for a reason. Access ends and queued jobs stop, but the data stays, so the agency can come back.',
      'Offboard yêu cầu ghi lý do. Quyền truy cập chấm dứt và các việc đang chờ bị huỷ, nhưng dữ liệu vẫn giữ, nên đại lý có thể quay lại.',
      async (page, h) => {
        await h.click(row(page).getByRole('button', { name: /^Offboard$/ }));
        const dialog = page.getByRole('dialog');
        await h.expect(dialog).toContainText(`Offboard ${T.name}?`, { timeout: 15_000 });
        const reason = dialog.getByRole('textbox');
        await h.click(reason);
        if (h.fast) await reason.fill(REASON);
        else await reason.pressSequentially(REASON, { delay: 25 });
        const sent = page.waitForResponse((x) => isPost(x, PATHS.offboard), { timeout: 60_000 });
        await h.click(dialog.getByRole('button', { name: /^Offboard$/ }));
        await postAnswer(sent, 'the offboard');
        await h.expect(dialog).toHaveCount(0, { timeout: 30_000 });
        await h.expect(row(page)).toContainText('Offboarded', { timeout: 30_000 });
        await h.hover(row(page).getByText('Offboarded', { exact: true }));
        assertPins();
      }, { writes: true }),
    step('The offboard recorded an erasure request. A drill sets the waiting time to zero, so the dry run can start now. Only a test agency can be drilled.',
      'Việc offboard đã ghi một yêu cầu xoá dữ liệu. Diễn tập đặt thời gian chờ về không, nên chạy thử bắt đầu được ngay. Chỉ đại lý thử nghiệm mới được diễn tập.',
      async (page, h) => {
        await check(page, h, PAGE, { heading: 'Data erasure', ready: '[data-testid="tenant-offboarding-ready"]' });
        await rowsOrEmpty(page, h);
        await h.assertRowsFiltered();
        const box = page.getByTestId('tenant-erasure-drill');
        await h.scrollTo(box, 'center');
        const pick = box.getByTestId('tenant-erasure-drill-tenant');
        await h.hover(pick);
        await pick.selectOption(T.id);
        const sent = page.waitForResponse((x) => isPost(x, PATHS.drill), { timeout: 60_000 });
        await h.click(box.getByRole('button', { name: 'Start drill' }));
        const body = await postAnswer(sent, 'starting the drill');
        rid = body.request && body.request.request_id;
        if (!rid || !new RegExp(`^${UUID}$`).test(rid)) throw new Error('the drill answer has no request id');
        if (body.request.mode !== 'drill') throw new Error(`the request is in mode ${body.request.mode}, not drill`);
        sc.meta = { ...sc.meta, request_id_prefix: rid.slice(0, 8) };
        await h.expect(box).toContainText('Drill recorded', { timeout: 15_000 });
        const d = detail(page);
        await h.expect(d).toBeVisible({ timeout: 30_000 });
        await h.scrollTo(d);
        await h.expect(d).toContainText('dry_run');
        await h.expect(d).toContainText('drill');
        assertPins();
      }, { writes: true }),
    step('Run now starts the erasure job. CIS, Booking and TripPlanner each compute a dry run plan. Nothing is erased.',
      'Bấm Run now để bắt đầu việc xoá dữ liệu. CIS, Booking và TripPlanner mỗi bên tính một kế hoạch chạy thử. Không có gì bị xoá.',
      async (page, h) => {
        const d = detail(page);
        const sent = page.waitForResponse((x) => isPost(x, PATHS.advance), { timeout: 60_000 });
        await h.click(d.getByRole('button', { name: 'Run now' }));
        const body = await postAnswer(sent, 'Run now');
        if (body.phase !== 'dry_run') throw new Error(`Run now answered phase ${body.phase}, not dry_run`);
        await h.expect(d).toContainText('The saga job will run now', { timeout: 15_000 });
        assertPins();
      }, { writes: true }),
    step('Now we wait for the three reports, usually a few minutes. The page refreshes itself every fifteen seconds.',
      'Giờ chờ ba báo cáo, thường mất vài phút. Trang tự làm mới mỗi mười lăm giây.',
      async (page, h) => {
        await h.scrollTo(page.getByTestId('tenant-erasure-steps'), 'center');
        const t0 = Date.now();
        let r = await request(page);
        let reloads = 0;
        while (r.phase === 'dry_run' && !(reported(r) && !['queued', 'running'].includes((r.job && r.job.status) || ''))) {
          if (Date.now() - t0 > WAIT_MS) throw new Error(`no DRY RUN report after ${WAIT_MS / 60_000} min (job ${(r.job && r.job.status) || 'none'})`);
          await page.waitForTimeout(POLL_MS);
          if (await keepSession(page, h)) {
            reloads += 1;
            await h.scrollTo(page.getByTestId('tenant-erasure-steps'), 'center');
          }
          r = await request(page);
        }
        const apps = [...r.round_apps].sort();
        if (apps.join() !== STAGE_1.join()) throw new Error(`stage 1 apps are ${apps.join(', ') || 'none'}, expected ${STAGE_1.join(', ')}`);
        const bad = stage1(r).filter((s) => STAGE_1.includes(s.app) && (!s.plan_hash || s.error_code));
        if (bad.length) throw new Error(`no DRY RUN plan from ${bad.map((s) => `${s.app} (${s.error_code || s.status})`).join(', ')}`);
        if (r.phase !== 'awaiting_approval') throw new Error(`after the reports the request is in phase ${r.phase}, not awaiting_approval`);
        sc.meta = { ...sc.meta, waited_s: Math.round((Date.now() - t0) / 1000), reloads, phase: r.phase,
          fingerprint_prefix: (r.combined_fingerprint || '').slice(0, 8),
          plans: Object.fromEntries(stage1(r).map((s) => [s.app, (s.plan_hash || '').slice(0, 8)])) };
        await h.expect(detail(page)).toContainText('awaiting_approval', { timeout: 60_000 });
      }),
    step('Each app sent its plan, shown by the first characters of its plan hash. The CRM is the second stage, after its own window, so it has no plan yet.',
      'Mỗi app đã gửi kế hoạch, hiển thị bằng vài ký tự đầu của mã băm kế hoạch. CRM thuộc đợt hai, sau thời hạn riêng, nên chưa có kế hoạch.',
      async (page, h) => {
        await keepSession(page, h);
        const plans = sc.meta.plans;
        for (const [app, label] of [['cis', 'CIS'], ['booking', 'Booking'], ['tripplanner', 'TripPlanner']]) {
          const r = stepRow(page, label);
          await h.expect(r).toHaveCount(1, { timeout: 15_000 });
          await h.expect(r).toContainText(`plan ${plans[app]}`, { timeout: 30_000 });
          await h.hover(r.getByText(`plan ${plans[app]}`));
        }
        const crm = stepRow(page, 'CRM');
        await h.expect(crm).toContainText('waiting');
        await h.expect(crm).not.toContainText('plan ');
        await h.hover(crm);
      }),
    step('The approval stays closed: the apply switch is off on Dev, and a drill is never approved.',
      'Phần duyệt vẫn đóng: công tắc áp dụng đang tắt trên Dev, và buổi diễn tập không bao giờ được duyệt.',
      async (page, h) => {
        await keepSession(page, h);
        const a = page.getByTestId('tenant-erasure-approve');
        await h.scrollTo(a, 'center');
        await h.expect(a).toContainText('Approval is not possible now');
        await h.expect(a).toContainText('the saga apply switch is off on this environment');
        await h.expect(a.getByRole('button', { name: 'Approve' })).toHaveCount(0);
        await h.hover(a.getByText('the saga apply switch is off on this environment'));
      }),
    step('Stop for good ends the drill. The request stays failed, with the blocker stopped by tech lead, and cannot start again.',
      'Bấm Stop for good để kết thúc buổi diễn tập. Yêu cầu chuyển sang thất bại và ghi điểm chặn: trưởng nhóm kỹ thuật đã dừng. Yêu cầu này không chạy lại được.',
      async (page, h) => {
        await keepSession(page, h);
        const d = detail(page);
        await h.scrollTo(d);
        page.once('dialog', (x) => void x.accept());
        const sent = page.waitForResponse((x) => isPost(x, PATHS.stop), { timeout: 60_000 });
        await h.click(page.getByTestId('tenant-erasure-stop'));
        await postAnswer(sent, 'Stop for good');
        const r = await request(page);
        if (r.phase !== 'failed') throw new Error(`after Stop the request is in phase ${r.phase}, not failed`);
        if (!r.blockers.some((b) => b.kind === 'stopped_by_tech_lead')) throw new Error('no stopped_by_tech_lead blocker after Stop');
        if (r.approved_by) throw new Error('the drill request shows an approval');
        await h.expect(d).toContainText('The request is stopped (failed)', { timeout: 15_000 });
        const b = page.getByTestId('tenant-erasure-blockers');
        await h.expect(b).toContainText('stopped_by_tech_lead', { timeout: 30_000 });
        await h.hover(b.getByText(/stopped_by_tech_lead/).first());
        await h.expect(page.getByTestId('tenant-erasure-stop')).toHaveCount(0);
        assertPins();
      }, { writes: true }),
    step('Restore brings the agency back with its plan, brand rules and content. Restoring also closes its erasure request.',
      'Bấm Restore để đưa đại lý trở lại với gói dịch vụ, quy tắc thương hiệu và nội dung như cũ. Việc khôi phục cũng đóng yêu cầu xoá dữ liệu của đại lý.',
      async (page, h) => {
        await check(page, h, '/admin/tenants', { heading: 'Tenants', table: true });
        const r = row(page);
        await h.scrollTo(r, 'center');
        await h.expect(r).toContainText('Offboarded');
        await h.click(r.getByRole('button', { name: /^Restore$/ }));
        const dialog = page.getByRole('dialog');
        await h.expect(dialog).toContainText(`Restore ${T.name}?`, { timeout: 15_000 });
        await h.hover(dialog.getByText(/becomes active again/));
        const sent = page.waitForResponse((x) => isPost(x, PATHS.restore), { timeout: 60_000 });
        await h.click(dialog.getByRole('button', { name: /^Restore$/ }));
        await postAnswer(sent, 'the restore');
        restored = true;
        // The restore hook cancels the open and the failed requests of the tenant: ours ends cancelled.
        const q = await request(page);
        if (q.phase !== 'cancelled' || !q.cancelled_at) throw new Error(`after the restore the drill request is in phase ${q.phase}, not cancelled`);
        const notice = page.getByTestId('tenant-notice-modal');
        await h.expect(notice).toContainText('Tenant Restored', { timeout: 30_000 });
        await h.click(notice.getByRole('button', { name: 'Done' }));
        await h.expect(notice).toHaveCount(0, { timeout: 15_000 });
        assertPins();
      }, { writes: true }),
    step('The agency is active again. Nothing was approved or erased. This is the end of the scenario.',
      'Đại lý đã hoạt động trở lại. Không có gì được duyệt hay bị xoá. Kết thúc kịch bản.',
      async (page, h) => {
        const r = row(page);
        await h.scrollTo(r, 'center');
        await h.expect(r).toContainText('Active', { timeout: 30_000 });
        await h.hover(r.getByText('Active', { exact: true }));
        const t = await tenantRow(page);
        if (!t || t.cancelled_at || (t.status && t.status !== 'active')) throw new Error(`${SLUG} is not active after the restore`);
        const q = await request(page);
        if (q.approved_by) throw new Error('the drill request shows an approval');
        if (q.phase !== 'cancelled' || !q.cancelled_at) throw new Error(`the drill request ends in phase ${q.phase}, not cancelled`);
        sc.meta = { ...sc.meta, final_phase: q.phase };
        for (const [k, n] of Object.entries(counts)) if (n !== 1) throw new Error(`${n} ${k} request(s) in this run, expected 1`);
        await h.assertRowsFiltered();
      }),
  ],
});

// Safety net: a step failed after the offboard was sent (even if its answer never came back) -> restore the tenant when
// it is offboarded (this also closes its open request). It always loads a page first, so an access token that ran out
// during a failed step is refreshed (proxy.ts) before the API calls.
sc.after = async (page, h) => {
  if (restored || !counts || counts.offboard === 0 || !T.id) return;
  await h.goto('/admin/overview');
  const t = await tenantRow(page);
  if (!t || !(t.cancelled_at || t.status === 'offboarded')) return;
  if (counts && counts.restore > 0) throw new Error('the restore was already sent once in this run: restore the tenant by hand');
  const r = await studioCall(page, 'POST', `${TENANTS}/${T.id}/restore`, {});
  if (r.status !== 200) throw new Error(`restoring ${SLUG} answered ${r.status}: restore it by hand on the Tenants page`);
  restored = true;
};

module.exports = sc;
