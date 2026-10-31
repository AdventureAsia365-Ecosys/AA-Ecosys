// CRM review CLEANUP (data step, never recorded): node tools/uat/record.cjs scenarios/crm/cleanup.cjs --fast
//   UAT_CRM_CLEANUP_DRY=1 lists what it would do and writes nothing.
//   UAT_CRM_CLEANUP_KEEP_PREP=1 keeps prep's side trip and invoice trip (clean rehearsal leftovers before recording;
//   the R10 invoice must stay one agency day old to show as overdue) and the R10 client link.
//   UAT_CRM_CLEANUP_TAGS=rv202610311,rv202610312 also trashes the imported clients of those earlier runs.
// Given: identity A (owner of the invented agency) and work/crm/state.json from prep.cjs and the chunks.
// When:  for every trip the review created that is not booked (inquiry, qualifying, proposal, including an accepted
//        proposal waiting for its deposit, and lost / cancelled ones) it voids the invoices still receivable (a claim
//        is answered "not received" first), releases the AA holds on its lines and moves an open trip to Lost (reason
//        "other"; Lost also gives the client's AA hold back); it deletes the saved replies and mail drafts the review
//        made, revokes its ICS feeds, closes its data requests as withdrawn and moves the clients it added (R16) and the
//        run's imported clients (R02: name ends with the run tag, no trip) to the trash; it wipes the run's link tokens
//        (work/crm/.secrets.json) and reports the outbound mail on the run's trips (status counts only, read only).
// Then:  nothing of the run stays open or keeps chasing a client; booked trips are left as they are (the review keeps
//        them as booked examples). Re-running is safe: objects already closed or gone are skipped; any other answer
//        than 200 / 404 is a failure. Left on purpose: R09's booking-terms versions (one per run; an agreement version
//        cannot be deleted, the newest published one stays in force) and the trashed clients (the CRM purges its trash).
// Dev only, invented data, no LLM call. Cost $0.
const { st, base, open, bff, bffOk } = require('./_crm.cjs');

const OPEN = ['inquiry', 'qualifying', 'proposal'];
const NOT_BOOKED = [...OPEN, 'lost', 'cancelled'];
const RECEIVABLE = ['draft', 'open', 'payment_claimed', 'expired'];
const dry = process.env.UAT_CRM_CLEANUP_DRY === '1';
const keepPrep = process.env.UAT_CRM_CLEANUP_KEEP_PREP === '1';
const extraTags = (process.env.UAT_CRM_CLEANUP_TAGS || '').split(',').map((x) => x.trim()).filter((x) => /^rv\d{9,}$/.test(x));
const sc = base({ id: 'CRM-REV-CLEANUP', title: 'Clean up the data of the CRM review' });
sc.fastOnly = true;
let s;
const done = [];
const failed = [];

/** One clean-up write; 200/404 (and any `alsoFine` code, e.g. 409 for "already closed") count as done. */
async function act(page, label, method, p, body, alsoFine = []) {
  if (dry) {
    done.push(`would ${label}`);
    return;
  }
  const r = await bff(page, method, p, body);
  if (r.status < 300 || r.status === 404 || alsoFine.includes(r.status)) done.push(`${label} (${r.status})`);
  else failed.push(`${label}: ${r.status} ${JSON.stringify(r.data && r.data.detail !== undefined ? r.data.detail : '').slice(0, 100)}`);
}

sc.steps = [
  {
    caption: { en: 'Open the CRM and read the run state.', vi: 'Mở CRM và đọc trạng thái lượt chạy.' },
    run: async (page, h) => {
      s = st.load();
      if (!s.run) throw new Error('no review run in work/crm/state.json');
      await open(page, h, '/pipeline', 'crm-pipeline');
      sc.meta.run = s.run;
      sc.meta.dry_run = dry;
    },
  },
  {
    caption: { en: 'Void open invoices, release AA holds and move the unfinished trips to Lost.', vi: 'Huỷ hoá đơn còn mở, nhả giữ chỗ AA và chuyển các chuyến dở dang sang Lost.' },
    run: async (page) => {
      const ids = [...new Set([...((s.created && s.created.trips) || []), ...(s.r03 ? [s.r03.trip_id] : [])])];
      const kept = keepPrep ? [s.side_trip && s.side_trip.trip_id, s.invoice_trip && s.invoice_trip.trip_id] : [];
      for (const id of ids) {
        if (kept.includes(id)) {
          done.push(`trip ${id.slice(0, 8)} kept (prep)`);
          continue;
        }
        const t = await bff(page, 'GET', `trips/${id}`);
        if (t.status === 404) {
          done.push(`trip ${id.slice(0, 8)} gone (404)`);
          continue;
        }
        if (t.status !== 200) {
          failed.push(`read trip ${id.slice(0, 8)}: ${t.status}`);
          continue;
        }
        const stage = t.data.trip.stage;
        if (!NOT_BOOKED.includes(stage)) {
          done.push(`trip ${id.slice(0, 8)} left at ${stage} (booked example)`);
          continue;
        }
        const invs = await bff(page, 'GET', `trips/${id}/invoices`);
        if (invs.status !== 200) failed.push(`read invoices of trip ${id.slice(0, 8)}: ${invs.status}`);
        for (const inv of ((invs.data && invs.data.invoices) || []).filter((x) => RECEIVABLE.includes(x.status))) {
          const iid = inv.invoice_id.slice(0, 8);
          if (inv.status === 'payment_claimed') await act(page, `invoice ${iid} claim -> not received`, 'POST', `invoices/${inv.invoice_id}/reject-claim`);
          await act(page, `void invoice ${iid} (${inv.status})`, 'POST', `invoices/${inv.invoice_id}/void`, { reason: 'CRM review clean-up (invented data)' });
        }
        const lines = ((await bff(page, 'GET', `trips/${id}/lines`)).data || {}).lines || [];
        for (const l of lines.filter((x) => x.supplier_kind === 'aa' && x.aa && x.aa.hold_id && !['released', 'cancelled'].includes(x.status))) {
          const lid = l.booking_line_id || l.line_id;
          await act(page, `release AA hold on line ${lid.slice(0, 8)}`, 'POST', `lines/${lid}/aa/release`, {});
        }
        if (OPEN.includes(stage)) await act(page, `trip ${id.slice(0, 8)} ${stage} -> lost`, 'POST', `trips/${id}/stage`, { to: 'lost', lost_reason: 'other' });
        else done.push(`trip ${id.slice(0, 8)} already ${stage}`);
      }
    },
  },
  {
    caption: { en: 'Delete the saved replies and drafts, revoke the calendar feeds, close the data requests, trash the added clients.', vi: 'Xoá câu trả lời mẫu và bản nháp, thu hồi lịch ICS, đóng các yêu cầu dữ liệu, chuyển khách đã thêm vào thùng rác.' },
    run: async (page) => {
      const c = s.created || {};
      for (const id of c.saved_replies || []) await act(page, `delete saved reply ${id.slice(0, 8)}`, 'DELETE', `saved-replies/${id}`);
      for (const id of c.drafts || []) await act(page, `delete draft ${id.slice(0, 8)}`, 'DELETE', `messages/drafts/${id}`);
      for (const id of c.ics_feeds || []) await act(page, `revoke ICS feed ${id.slice(0, 8)}`, 'POST', `calendar/feeds/${id}/revoke`, {});
      for (const id of c.data_requests || []) {
        const r = await act(page, `close data request ${id.slice(0, 8)}`, 'POST', `data/requests/${id}/close`, { status: 'withdrawn', outcome: 'withdrawn_by_subject' }, [409]);
        void r;
      }
      for (const id of c.clients || []) await act(page, `client ${id.slice(0, 8)} -> trash`, 'DELETE', `travelers/${id}`);
      // R02's imported clients: found by the run tag in their names (exact token search), only those with no trip.
      for (const tag of [s.run, ...extraTags]) {
        for (let pg = 1; pg <= 5; pg++) {
          const r = await bff(page, 'POST', 'travelers/search', { q: tag, page: pg });
          if (r.status !== 200) {
            failed.push(`search clients of ${tag}: ${r.status}`);
            break;
          }
          const mine = (r.data.items || []).filter((x) => x.display_name.endsWith(` ${tag}`) && !x.trips && !(c.clients || []).includes(x.traveler_id));
          for (const x of mine) await act(page, `imported client ${x.traveler_id.slice(0, 8)} (${tag}) -> trash`, 'DELETE', `travelers/${x.traveler_id}`);
          if (!r.data.has_more || dry) break;
        }
      }
      if (!dry) st.clearSecrets(keepPrep ? ['r10_link_path'] : []);
    },
  },
  {
    caption: { en: 'Count the outbound mail of the run\'s trips.', vi: 'Đếm thư gửi đi trên các chuyến của lượt chạy.' },
    run: async (page) => {
      // Read only. Proposal sends, portal invites and code mails go out through the agency's connected mailbox to the
      // invented *.invalid addresses; this shows what left (status counts, never an address or a subject).
      const ids = [...new Set([...((s.created && s.created.trips) || []), ...(s.r03 ? [s.r03.trip_id] : [])])];
      const tally = {};
      for (const id of ids) {
        const cv = await bff(page, 'GET', `conversations?trip_id=${id}`);
        for (const c of (cv.status === 200 && cv.data.conversations) || []) {
          const m = await bff(page, 'GET', `conversations/${c.conversation_id}/messages`);
          for (const x of ((m.status === 200 && m.data.messages) || []).filter((y) => y.direction === 'out')) {
            const k = `${x.status}${x.failure_code ? `:${x.failure_code}` : ''}`;
            tally[k] = (tally[k] || 0) + 1;
          }
        }
      }
      sc.meta.outbound_mail = tally;
      console.log(`cleanup: outbound mail on the run's trips ${JSON.stringify(tally)}`);
    },
  },
  {
    caption: { en: 'Report what was cleaned.', vi: 'Báo cáo những gì đã dọn.' },
    run: async (page, h) => {
      for (const d of done) console.log(`cleanup: ${d}`);
      sc.meta.done = done;
      if (!dry) {
        const fresh = st.load();
        // Kept prep trips are still open: only a full clean-up lets newRun() drop this run's ids.
        fresh[keepPrep ? 'partly_cleaned_at' : 'cleaned_at'] = new Date().toISOString();
        st.save(fresh);
      }
      if (failed.length) throw new Error(`cleanup failed for: ${failed.join('; ')}`);
      h.expect(failed).toEqual([]);
      await bffOk(page, 'GET', 'pipeline');
    },
  },
];

module.exports = sc;
