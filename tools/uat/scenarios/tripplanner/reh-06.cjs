// UAT scenario REH-06 (pilot rehearsal step 6, the traveller half; runbook docs/ops/runbooks/pilot-rehearsal.md): a
// guest on the synthetic agency's planner sends the trip to the agency with the contact consent ticked, and presses
// Send twice in a row. 1440 x 900. $0: no model call (search, chat and narration blocked).
// Writes, capped by limitWrites: the guest trip (POST /api/trip, op apply_route only) and the request (POST
// /api/trip/send), exactly twice. The form's busy state usually stops the second click inside the page; then the take
// sends the same request once more from the page (same body, same tenant header), so the server's double-click answer
// is proven on every take: already_sent with the same handoff_id (AA-TripPlanner-Web backend/assembly/handler.py
// _send_lead). meta.second_send says which way it went. The traveller is invented (env UAT_REH_TRAVELLER_EMAIL, an
// address on .invalid; any other address stops the take). The web ACL challenges the send without a token: the
// planner's document load got one. The send limits are TripPlanner settings of the CIS registry (a 429 names them).
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
let firstSend = null; // the first send request that left the page: { body, headers }
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
        counts = await limitWrites(page, [
          { name: 'send', path: R.PATHS.send, max: 2, method: '*', accept: (req) => req.method() === 'POST' },
          { name: 'trip', path: R.PATHS.trip, max: 2, method: '*', accept: R.tripOps('apply_route') },
        ]);
        page.on('response', async (r) => {
          if (new URL(r.url()).pathname !== '/api/trip/send' || r.request().method() !== 'POST') return;
          // The take's own repeat (replaySend) records its answer itself, from inside the page.
          if (r.request().headers()[R.REPLAY_HEADER]) return;
          if (!firstSend) firstSend = { body: r.request().postData(), headers: r.request().headers() };
          answers.push(R.sendAnswer(r.status(), await r.text().catch(() => '')));
        });
        await R.openPlanner(page, h, meta);
      }),
    step('They pin the route of the rehearsal tour from the agency\'s list of tours.',
      'Khách thêm lộ trình của tour diễn tập từ danh sách tour của đại lý.',
      async (page, h) => {
        await R.addTourX(page, h, meta);
        await h.click(page.getByRole('button', { name: 'Map', exact: true }));
        meta.days = (await R.tripDays(page, h, 1)).length;
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
    step('They give a name, an email and a short message, and allow the agency to contact them.',
      'Khách điền tên, email và một lời nhắn ngắn, rồi cho phép đại lý liên hệ.',
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
        // counts.send = the send requests that left the page (an answer may still be on its way).
        meta.second_send = counts.send > 1 ? 'double_click' : 'replay';
        if (counts.send === 1 && answers.length === 1 && answers[0].status === 200) await replaySend(page);
        await h.expect.poll(() => answers.length, { timeout: 15_000 }).toBeGreaterThanOrEqual(Math.min(counts.send, 2));
        meta.send_posts = counts.send;
        meta.send_answers = answers.map((a) => ({ status: a.status, already_sent: a.already_sent }));
        const bad = answers.find((a) => a.status !== 200);
        if (bad) throw new Error(`a send answered ${bad.status}${bad.error ? ` ${bad.error}` : ''}${R.registryHint('send', bad.status, bad.error)}`);
        if (answers.length !== 2) throw new Error(`${answers.length} send answers (two expected: the first and the repeat)`);
        const ids = new Set(answers.map((a) => a.handoff_id));
        if (ids.size !== 1 || ids.has(null)) throw new Error(`the sends carried ${ids.size} hand-off ids (one expected)`);
        const fresh = answers.filter((a) => a.already_sent === false).length;
        if (fresh !== 1) throw new Error(`${fresh} new hand-offs (exactly one expected)`);
        if (counts.send_refused || counts.trip_refused) throw new Error('the page tried a trip write this take does not make (aborted)');
      }, { writes: true }),
    step('The panel confirms the request was sent, and the send button stays off. This is the end of the scenario.',
      'Bảng chuyến đi xác nhận yêu cầu đã gửi, và nút gửi không bấm được nữa. Kết thúc kịch bản.',
      async (page, h) => {
        const done = page.getByRole('button', { name: /Sent to advisor/ });
        await h.expect(done).toBeDisabled({ timeout: 15_000 });
        await h.hover(done);
        if (counts.send !== 2) throw new Error(`${counts.send} send requests left the page (exactly two expected)`);
      }),
  ],
});

/**
 * Send the first request once more from the page (same body; the content type and the planner's tenant headers): the
 * double click the form's busy state kept inside the page. The page reads the answer itself and the take records it
 * here: the response listener skips this request (R.REPLAY_HEADER), so the repeat is counted exactly once (S279: the
 * listener missed the repeat's answer when the page never read its body, and the take failed with one answer).
 */
async function replaySend(page) {
  if (!firstSend || !firstSend.body) throw new Error('no first send request to repeat');
  const headers = R.replayHeaders(firstSend.headers);
  const res = await page.evaluate(async ({ body, headers }) => {
    const r = await fetch('/api/trip/send', { method: 'POST', headers, body, credentials: 'same-origin' });
    return { status: r.status, text: await r.text().catch(() => '') };
  }, { body: firstSend.body, headers });
  answers.push(R.sendAnswer(res.status, res.text));
  meta.replay_status = res.status;
}

/** Click a field and type like a person (instant in fast mode). */
async function typeInto(page, h, loc, text) {
  await h.click(loc);
  await loc.pressSequentially(text, { delay: h.fast ? 0 : 35 });
}
