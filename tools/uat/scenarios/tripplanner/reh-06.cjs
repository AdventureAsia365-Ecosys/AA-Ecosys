// UAT scenario REH-06 (pilot rehearsal step 6, the traveller half; runbook docs/ops/runbooks/pilot-rehearsal.md): a
// guest on the synthetic agency's planner sends the trip to the agency with the contact consent ticked, and presses
// Send twice in a row. 1440 x 900. $0: no model call (search, chat and narration blocked).
// Writes: the guest trip (POST /api/trip: apply tour X's route) and the request (POST /api/trip/send), at most twice:
// the second press may reach the server, which must answer it as the same hand-off (already_sent, the same
// handoff_id; AA-TripPlanner-Web backend/assembly/handler.py). The traveller is invented (env UAT_REH_TRAVELLER_EMAIL,
// default on example.invalid). The web ACL challenges the send without a token: the planner's document load got one.
// Needs: tour X adopted by the agency (step 3), the agency's CRM add-on (its leads go to the CRM); env UAT_REH_TOUR_X.
// The CRM half of step 6 (one lead in /pipeline within about a minute, not visible to other agencies, the
// TripPlanner outbox row redacted) is the CRM group's scenario and a database read.
// Given: a guest with tour X pinned. When: they open the request form, fill it, tick the consent and double-click Send.
// Then: one hand-off: every send answer is 200 with one handoff id, exactly one of them new; the panel says it was
// sent and the button stays disabled.
const { HOSTS, step } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const { PAID_URLS } = require('../../lib/dryrun-core.cjs');
const R = require('./_rehearsal.cjs');

const meta = {};
let counts = null;
const answers = []; // { status, already_sent, handoff_id } per send that reached the server

module.exports = rw({
  id: 'REH-06',
  app: 'tripplanner',
  identity: 'traveller',
  paid: false,
  title: 'Send the trip to the agency: one request, even on a double click',
  titleVi: 'Gửi chuyến đi cho đại lý: một yêu cầu, kể cả khi bấm hai lần',
  baseURL: HOSTS.tripplanner,
  allowWrites: [R.WRITES.trip, R.WRITES.send],
  blockUrls: [...PAID_URLS, '/api/trip/chat(?:[?#]|$)'],
  meta,
  steps: [
    step('A traveller is on the agency\'s planner, under the agency\'s own name.',
      'Khách du lịch đang ở trang lập kế hoạch của đại lý, mang tên riêng của đại lý.',
      async (page, h) => {
        counts = await limitWrites(page, [{ name: 'send', path: R.PATHS.send, max: 2 }]);
        page.on('response', async (r) => {
          if (new URL(r.url()).pathname !== '/api/trip/send' || r.request().method() !== 'POST') return;
          const body = await r.json().catch(() => ({}));
          answers.push({ status: r.status(), already_sent: body.already_sent, handoff_id: body.handoff_id || null, error: body.error });
        });
        await R.openPlanner(page, h);
      }),
    step('They pin the route of the rehearsal tour from the agency\'s list of tours.',
      'Khách thêm lộ trình của tour diễn tập từ danh sách tour của đại lý.',
      async (page, h) => {
        await R.addTourX(page, h, meta);
        await h.click(page.getByRole('button', { name: 'Map', exact: true }));
        meta.stops = (await R.tripStops(page, h, 1)).length;
      }, { writes: true }),
    step('Send to the agency opens a short request form. Their details go only to this agency.',
      'Nút gửi cho đại lý mở một biểu mẫu ngắn. Thông tin của khách chỉ gửi tới đại lý này.',
      async (page, h) => {
        const open = page.getByRole('button', { name: `Send to ${R.AGENCY}`, exact: true });
        await h.scrollTo(open, 'center');
        await h.click(open);
        const form = page.getByTestId('lead-form');
        await h.expect(form).toBeVisible({ timeout: 15_000 });
        await h.expect(form).toContainText(`Your details go only to ${R.AGENCY}`);
      }),
    step('The traveller fills in a name, an email and a short message, and ticks the box that lets the agency contact them.',
      'Khách điền tên, email và một lời nhắn ngắn, rồi đánh dấu ô cho phép đại lý liên hệ.',
      async (page, h) => {
        const t = R.traveller();
        const form = page.getByTestId('lead-form');
        await typeInto(page, h, form.getByRole('textbox', { name: 'Full name' }), t.name);
        await typeInto(page, h, form.getByRole('textbox', { name: 'Email' }), t.email);
        await typeInto(page, h, form.getByRole('textbox', { name: 'Message (optional)' }), t.message);
        const consent = form.getByRole('checkbox', { name: `${R.AGENCY} may contact me about this trip.` });
        await h.click(consent);
        await h.expect(consent).toBeChecked();
        await h.expect(form.getByRole('button', { name: 'Send my request' })).toBeEnabled();
      }),
    step('They press Send twice, quickly. The agency gets one request, not two.',
      'Khách bấm Gửi hai lần liên tiếp. Đại lý chỉ nhận một yêu cầu, không phải hai.',
      async (page, h) => {
        const send = page.getByTestId('lead-form').getByRole('button', { name: 'Send my request' });
        await h.moveTo(send);
        const b = await send.boundingBox();
        if (!b) throw new Error('the Send button has no box');
        const first = page.waitForResponse((r) => new URL(r.url()).pathname === '/api/trip/send' && r.request().method() === 'POST', { timeout: 60_000 });
        await page.mouse.dblclick(b.x + b.width / 2, b.y + b.height / 2);
        await first;
        await h.expect(page.getByText(`Sent to ${R.AGENCY}. They will contact you about this trip.`)).toBeVisible({ timeout: 30_000 });
        await h.pause(1500); // a second send, if the page let one out, answers within this
        meta.send_posts = counts.send;
        meta.send_answers = answers.map((a) => ({ status: a.status, already_sent: a.already_sent }));
        if (!answers.length || answers.length > 2) throw new Error(`${answers.length} send answers (one or two expected)`);
        const bad = answers.find((a) => a.status !== 200);
        if (bad) throw new Error(`a send answered ${bad.status}${bad.error ? ` ${bad.error}` : ''}`);
        const ids = new Set(answers.map((a) => a.handoff_id));
        if (ids.size !== 1 || ids.has(null)) throw new Error(`the sends carried ${ids.size} hand-off ids (one expected)`);
        const fresh = answers.filter((a) => a.already_sent === false).length;
        if (fresh !== 1) throw new Error(`${fresh} new hand-offs (exactly one expected)`);
      }, { writes: true }),
    step('The panel confirms the request was sent, and the send button stays off. This is the end of the scenario.',
      'Bảng chuyến đi xác nhận yêu cầu đã gửi, và nút gửi không bấm được nữa. Kết thúc kịch bản.',
      async (page, h) => {
        const done = page.getByRole('button', { name: /Sent to advisor/ });
        await h.expect(done).toBeDisabled({ timeout: 15_000 });
        await h.hover(done);
        if (counts.send > 2) throw new Error(`${counts.send} send presses left the page (at most two expected)`);
      }),
  ],
});

/** Click a field and type like a person (instant in fast mode). */
async function typeInto(page, h, loc, text) {
  await h.click(loc);
  await loc.pressSequentially(text, { delay: h.fast ? 0 : 35 });
}
