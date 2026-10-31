// CRM review PREP (data step, never recorded): node tools/uat/record.cjs scenarios/crm/prep.cjs --fast
//   UAT_CRM_NEW_RUN=1 starts a fresh run suffix (rv<yyyymmdd><n>); otherwise a re-run reuses what exists (idempotent).
// Given: identity A (owner of the synthetic agency "Lữ hành Sen Vàng") on Dev.
// When:  it checks /crm/health and keeps the git sha, picks an AA departure with >= 2 free seats, writes the ~10-row
//        import CSV (one possible-duplicate pair) for R02, makes the side trip for R07 (at Proposal, with a builder
//        draft: an agency hotel and an AA tour, balance date set) and the deposit invoice for R10 on a 2-adult trip (the
//        second adult added by name for R11's invite; issued due today:
//        it is overdue from the next agency day, so prep runs >= 1 h and one day boundary before R10).
// Then:  ids in work/crm/state.json (gitignored); the R10 client link in work/crm/.secrets.json (chmod 600). A re-run
//        keeps what is still usable (side trip at Proposal; an open deposit invoice; an accepted proposal's deposit
//        row) and otherwise makes a new trip under a new name (r07b, r10b, ...); the last step asserts both are usable.
// Dev only, invented people on @example.invalid, no Send of real mail, no LLM call. Cost $0.
const fs = require('fs');
const path = require('path');
const { crm, st, base, sha, open, bff, bffOk, waitForCard, prospect, submitInquiryApi, day } = require('./_crm.cjs');

const AA_TOUR = process.env.UAT_CRM_AA_TOUR || '000e3340-d9f5-4b7b-8609-4cdaa9c272dc'; // the Dev seed tour (fixed departures)
const sc = base({ id: 'CRM-REV-PREP', title: 'Prepare the data of the CRM review' });
sc.fastOnly = true;
let s;

const FIRST = ['Linh', 'Oskar', 'Mira', 'Tomas', 'Aiko', 'Priya', 'Lucas', 'Hana', 'Sofia'];
const LAST = ['Nguyen', 'Berg', 'Costa', 'Novak', 'Sato', 'Rao', 'Meyer', 'Kim', 'Rossi'];

function csvFor(tag) {
  const rows = ['client_ref,name,email,phone,marketing_consent'];
  for (let i = 0; i < 9; i++) {
    const name = `${FIRST[i]} ${LAST[i]} ${tag}`;
    rows.push(`RV-${tag}-${String(i + 1).padStart(2, '0')},${name},${FIRST[i].toLowerCase()}.${LAST[i].toLowerCase()}.${tag}@example.invalid,,${i % 2 ? 'no' : 'yes'}`);
  }
  // Row 10: the same name as row 1 with another address -> created with the "possible duplicate" warning, the pair
  // then shows in Clients > Duplicates.
  rows.push(`RV-${tag}-10,${FIRST[0]} ${LAST[0]} ${tag},${FIRST[0].toLowerCase()}.${LAST[0].toLowerCase()}.second.${tag}@example.invalid,,no`);
  return rows.join('\n') + '\n';
}

const OPEN = ['inquiry', 'qualifying', 'proposal'];

/** A trip at Proposal for an invented prospect; `attempt` > 1 gives a new name (an older trip moved on). */
async function newTrip(page, c, key, opts, attempt = 1) {
  const suffix = attempt > 1 ? String.fromCharCode(96 + attempt) : ''; // r07, r07b, r07c ...
  const p = prospect(s, `${key}${suffix}`, opts.first, opts.last, { nights: opts.nights, adults: opts.adults });
  if (suffix) p.name = `${p.name}${suffix}`;
  const existing = (await bff(page, 'GET', 'pipeline')).data;
  let card = null;
  for (const stg of existing.stages || []) for (const x of stg.cards || []) if (x.lead_name === p.name) card = x;
  if (card && !OPEN.includes(card.stage)) throw new Error(`${p.name} is at ${card.stage} already`);
  if (!card) {
    await submitInquiryApi(c, s.form_key, p);
    card = await waitForCard(page, p.name);
  }
  const me = await bffOk(page, 'GET', 'me');
  await bffOk(page, 'POST', `trips/${card.trip_id}/owner`, { member_id: me.member_id });
  await bffOk(page, 'PATCH', `trips/${card.trip_id}`, { start_date: opts.start, end_date: opts.end });
  if (card.stage === 'inquiry') await bffOk(page, 'POST', `trips/${card.trip_id}/stage`, { to: 'qualifying' });
  if (['inquiry', 'qualifying'].includes(card.stage)) {
    await bffOk(page, 'POST', `trips/${card.trip_id}/stage`, { to: 'proposal', override_reason: 'info_by_phone' });
  }
  st.remember(s, 'trips', card.trip_id);
  return { trip_id: card.trip_id, lead_name: p.name, email: p.email, start_date: opts.start, end_date: opts.end, attempt };
}

const stageOf = async (page, tripId) => {
  const t = await bff(page, 'GET', `trips/${tripId}`);
  return t.status === 200 ? t.data.trip.stage : null;
};

/** R07's builder draft on the side trip: night 1 hotel, day 2 an AA tour (no departure, no seat), balance date. */
async function sideDraft(page, t) {
  if (t.proposal_id) {
    const b = await bff(page, 'GET', `proposals/${t.proposal_id}/builder`);
    if (b.status === 200) return;
  }
  let v = await bffOk(page, 'POST', `trips/${t.trip_id}/builder`, { currency: 'USD' }, 201);
  const pid = v.proposal_id;
  const w = async (method, p2, body) => { v = await bffOk(page, method, p2, { seq: v.edit_seq, ...body }); };
  await w('PATCH', `proposals/${pid}/builder`, { starts_on: t.start_date, balance_due_on: day(12) });
  const night1 = v.days.find((d) => d.day_no === 1).blocks[0].option_block_id;
  await w('POST', `proposals/${pid}/blocks/${night1}/options`, { title: 'Old Quarter heritage hotel', sell_amount: '240.00', net_amount: '150.00' });
  const prod = await bffOk(page, 'GET', `aa/products/${AA_TOUR}?currency=USD`);
  const comp = (prod.components || []).find((x) => x.kind === 'trip_plan');
  if (comp) {
    const day2 = v.days.find((d) => d.day_no === 2);
    await w('POST', `proposals/${pid}/days/${day2.proposal_day_id}/blocks`, { title: 'Island days', type: 'activity' });
    const blk = v.days.find((d) => d.day_no === 2).blocks.find((b) => b.title === 'Island days').option_block_id;
    v = await bffOk(page, 'POST', `proposals/${pid}/blocks/${blk}/aa-options`, {
      seq: v.edit_seq, tour_source_id: AA_TOUR, component_id: comp.component_id, component_kind: comp.kind, sell_amount: '1400.00',
    }, 201);
  }
  t.proposal_id = pid;
  t.with_aa = Boolean(comp);
}

/** The R10 invoice: open (kept), draft (issued now), claimed by a rehearsal (claim rejected), else rebuilt. */
async function invoiceUsable(page, t) {
  if (!t || !t.trip_id || (await stageOf(page, t.trip_id)) !== 'proposal') return false;
  if (t.invoice_id) {
    const inv = await bff(page, 'GET', `invoices/${t.invoice_id}`);
    if (inv.status !== 200) return false;
    if (inv.data.status === 'payment_claimed') await bffOk(page, 'POST', `invoices/${t.invoice_id}/reject-claim`);
    if (inv.data.status === 'draft') await bffOk(page, 'POST', `invoices/${t.invoice_id}/issue`);
    return ['open', 'payment_claimed', 'draft', 'partially_paid'].includes(inv.data.status);
  }
  return false;
}

async function depositInvoice(page, t, proposalId) {
  const life = await bffOk(page, 'GET', `trips/${t.trip_id}/lifecycle`);
  const dep = (life.schedule || []).find((x) => x.kind === 'deposit' && (!proposalId || x.proposal_id === proposalId));
  if (!dep) return false;
  const inv = await bffOk(page, 'POST', `trips/${t.trip_id}/invoices`, { schedule_id: dep.schedule_id }, 201);
  await bffOk(page, 'PATCH', `invoices/${inv.invoice_id}`, { due_on: st.today().replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3') });
  const issued = await bffOk(page, 'POST', `invoices/${inv.invoice_id}/issue`);
  Object.assign(t, {
    proposal_id: dep.proposal_id, invoice_id: inv.invoice_id, number: issued.number, due_on: issued.due_on,
    issued_at: new Date().toISOString(), overdue_from: day(1, new Date(`${issued.due_on}T12:00:00Z`)),
  });
  st.remember(s, 'invoices', inv.invoice_id);
  return true;
}

sc.steps = [
  {
    caption: { en: 'Check the CRM is up and keep its version.', vi: 'Kiểm tra CRM đang chạy và ghi lại phiên bản.' },
    run: async (page, h) => {
      s = process.env.UAT_CRM_NEW_RUN === '1' || !st.load().run ? st.newRun() : st.load();
      await open(page, h, '/pipeline', 'crm-pipeline');
      s.git_sha = await sha(page, sc, 'start');
      const me = await bffOk(page, 'GET', 'me');
      if (me.member_role !== 'owner') throw new Error(`identity A is ${me.member_role}, not owner`);
      const form = ((await bffOk(page, 'GET', 'intake-forms')).forms || []).find((f) => f.status === 'active');
      if (!form) throw new Error('the agency has no active inquiry form');
      s.form_key = form.public_key;
      s.agency = me.display_name;
      st.save(s);
      sc.meta.run = s.run;
    },
  },
  {
    caption: { en: 'Pick an Adventure Asia departure with at least two free seats.', vi: 'Chọn một chuyến khởi hành của Adventure Asia còn ít nhất hai chỗ.' },
    run: async (page) => {
      const prod = await bffOk(page, 'GET', `aa/products/${AA_TOUR}?currency=USD`);
      const deps = (prod.departures || []).filter((d) => d.status === 'scheduled' && d.available >= 2 && d.auto_confirm);
      if (!deps.length) throw new Error(`no departure of the seed tour has 2 free seats (${(prod.departures || []).map((d) => `${d.start_date}:${d.available}`).join(', ')})`);
      const kept = s.departure && deps.find((d) => d.departure_id === s.departure.departure_id);
      const dep = kept || deps.sort((a, b) => b.available - a.available || a.start_date.localeCompare(b.start_date))[0];
      s.departure = { tour_source_id: AA_TOUR, tour_title: prod.tour && prod.tour.title, departure_id: dep.departure_id, start_date: dep.start_date, available: dep.available };
      st.save(s);
    },
  },
  {
    caption: { en: 'Write the import file: ten invented clients, one possible duplicate.', vi: 'Tạo file nhập: mười khách giả lập, trong đó có một cặp có thể trùng.' },
    run: async () => {
      const file = path.join(st.DIR, `import-${s.run}.csv`);
      if (!fs.existsSync(file)) fs.writeFileSync(file, csvFor(s.run));
      const lines = fs.readFileSync(file, 'utf8').trim().split('\n');
      if (lines.length !== 11) throw new Error(`the import file has ${lines.length - 1} rows, expected 10`);
      s.csv = { file: path.relative(path.join(__dirname, '..', '..'), file), rows: 10, duplicate_name: `${FIRST[0]} ${LAST[0]} ${s.run}` };
      st.save(s);
    },
  },
  {
    caption: { en: 'Make the side trip for the written proposal.', vi: 'Tạo chuyến phụ cho phần đề xuất dạng chữ.' },
    run: async (page) => {
      const kept = s.side_trip && (await stageOf(page, s.side_trip.trip_id)) === 'proposal';
      if (!kept) {
        const attempt = s.side_trip ? (s.side_trip.attempt || 1) + 1 : 1;
        const c = await page.context().newPage();
        try {
          s.side_trip = await newTrip(page, c, 'r07', { first: 'Minh', last: 'Tran', nights: 5, adults: 2, start: day(30), end: day(35) }, attempt);
        } finally {
          await c.close();
        }
        st.save(s);
      }
      await sideDraft(page, s.side_trip);
      st.save(s);
    },
  },
  {
    caption: { en: 'Make the trip with an issued deposit invoice, due today.', vi: 'Tạo chuyến có hoá đơn đặt cọc đã phát hành, hạn hôm nay.' },
    run: async (page) => {
      if (await invoiceUsable(page, s.invoice_trip)) return st.save(s);
      // An accepted proposal whose deposit was never invoiced (a crash between accept and issue): invoice it.
      if (s.invoice_trip && s.invoice_trip.proposal_id && !s.invoice_trip.invoice_id
          && (await stageOf(page, s.invoice_trip.trip_id)) === 'proposal' && (await depositInvoice(page, s.invoice_trip, s.invoice_trip.proposal_id))) {
        return st.save(s);
      }
      const attempt = s.invoice_trip ? (s.invoice_trip.attempt || 1) + 1 : 1;
      const c = await page.context().newPage();
      try {
        const t = await newTrip(page, c, 'r10', { first: 'Sara', last: 'Lindqvist', nights: 3, adults: 2, start: day(12), end: day(15) }, attempt);
        s.invoice_trip = t;
        st.save(s);
        // The second adult, by name only: R11 shows the lead inviting him to his own portal.
        const trip = await bffOk(page, 'GET', `trips/${t.trip_id}`);
        if ((trip.party || []).length < 2) await bffOk(page, 'POST', `trips/${t.trip_id}/travelers`, { new: { display_name: `Erik Lindqvist ${s.run}` } }, 201);
        const docs = (await bffOk(page, 'GET', 'agreements')).agreements || [];
        const terms = docs.find((d) => d.kind === 'booking_terms' && d.status === 'published');
        const draft = await bffOk(page, 'POST', `trips/${t.trip_id}/proposals`, {
          body: 'Three nights in Hoi An and the Hai Van pass with a private guide. Invented trip for the CRM review.',
          currency: 'USD', total_amount: '1800.00', deposit_amount: '540.00', balance_due_on: day(5),
          ...(terms ? { terms_doc_id: terms.doc_id } : {}),
        });
        t.proposal_id = draft.proposal_id;
        st.save(s);
        const sent = await bffOk(page, 'POST', `proposals/${draft.proposal_id}/send`);
        const secrets = st.loadSecrets();
        secrets.r10_link_path = sent.link_path;
        st.saveSecrets(secrets);
        await c.goto(`${crm.CLIENT}${sent.link_path}`, { waitUntil: 'domcontentloaded' });
        await c.waitForLoadState('networkidle').catch(() => {});
        const pg = await c.evaluate(async () => (await (await fetch('/crm/public/v1/proposal', { headers: { Accept: 'application/json' } })).json()));
        const view = pg.page || pg;
        await crm.paceClientWrite();
        const acc = await c.evaluate(async (body) => {
          const r = await fetch('/crm/public/v1/proposal/accept', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
          return { status: r.status, text: (await r.text()).slice(0, 200) };
        }, {
          full_name: t.lead_name, accept_terms: true, rooms_confirmed: true, price_hash: view.price_hash, selection_hash: view.selection_hash,
          terms_doc_id: view.terms && typeof view.terms === 'object' ? view.terms.doc_id : view.terms_doc_id,
        });
        if (acc.status !== 200) throw new Error(`the client accept answered ${acc.status} ${acc.text.replace(/[A-Za-z0-9_-]{40,}/g, '<token>')}`);
        if (!(await depositInvoice(page, t, draft.proposal_id))) throw new Error('no deposit row after the accept');
      } finally {
        await c.close();
      }
      st.save(s);
    },
  },
  {
    caption: { en: 'Everything is ready; the CRM version did not change.', vi: 'Dữ liệu đã sẵn sàng; phiên bản CRM không đổi.' },
    run: async (page, h) => {
      await sha(page, sc, 'end');
      const fresh = st.load();
      for (const k of ['form_key', 'departure', 'csv', 'side_trip', 'invoice_trip']) if (!fresh[k]) throw new Error(`state.json lacks ${k}`);
      h.expect(await stageOf(page, fresh.side_trip.trip_id), 'side trip stage').toBe('proposal');
      h.expect(fresh.side_trip.proposal_id, 'side trip builder draft').toBeTruthy();
      h.expect(await stageOf(page, fresh.invoice_trip.trip_id), 'invoice trip stage').toBe('proposal');
      const inv = await bffOk(page, 'GET', `invoices/${fresh.invoice_trip.invoice_id}`);
      h.expect(inv.status, 'R10 invoice status').toBe('open');
      console.log(`prep: run ${fresh.run}; departure ${fresh.departure.start_date} (${fresh.departure.available} seats); invoice ${fresh.invoice_trip.number} due ${fresh.invoice_trip.due_on}, overdue from ${fresh.invoice_trip.overdue_from}`);
    },
  },
];

module.exports = sc;
