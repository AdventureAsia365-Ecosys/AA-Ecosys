// Pilot rehearsal, agency setup before step 6 (runbook docs/ops/runbooks/pilot-rehearsal.md; scenarios/crm/REHEARSAL.md):
// what the owner of the fresh pilot-rehearsal-01 seed does once in the CRM UI so the later CRM steps can pass.
// Given: the CRM seed made the agency and its owner and agent members only (AA-Partner api/app/seed): no payment
//        instructions, no booking terms, no waiver; the owner (crm-rehearsal) is signed in outside the recording.
// When:  the owner saves the bank-transfer instructions on Settings > Payments ("How clients pay you"), then on
//        Settings > Agreements writes and publishes booking terms and a waiver (invented texts).
// Then:  a manual payment method is active with instructions (REH-08b step 3: the client's pay details,
//        payments/claims.py PAY_BY_SQL); a published booking_terms version (REH-08 step 5: the client accepts it with the
//        proposal) and a published waiver (REH-10 step 5: the portal builds its signing envelope only then,
//        portal/public.py WAIVER_SQL). A re-run reuses what is already there and writes nothing new.
// Writes (method and path allowed, each capped): PUT settings/payment-methods/manual (1), POST agreements (2: one draft
// per kind), POST agreements/<id>/publish (2), on the rehearsal agency only (pilot guard pin). No mail, no LLM call.
// Cost $0. Not done here (see REHEARSAL.md): connecting a mailbox (leave it unconnected), the discount limit (the
// agency keeps the registry default and REH-07 reads it live).
const R = require('./_reh.cjs');

const { step } = R;
const TERMS_TEXT = 'Invented booking terms for the pilot rehearsal. Deposit on acceptance as shown in the payment plan; '
  + 'balance by the date in the proposal. Free changes until 30 days before departure. Not a real contract.';
const WAIVER_TEXT = 'Invented waiver for the pilot rehearsal. The traveller confirms they are fit to take part in the '
  + 'activities of the trip and follows the guide\'s safety instructions. Not a real contract.';
const LABEL = 'rehearsal-1';
const BANK = 'Invented bank for the rehearsal. Account name: E2E Pilot Rehearsal Travel. Account number: 000-000-000. '
  + 'Reference: your invoice number.';

const docsOf = async (page, kind) => ((await R.bffOk(page, 'GET', 'agreements')).agreements || []).filter((d) => d.kind === kind);
const manualMethod = async (page) => ((await R.bffOk(page, 'GET', 'settings/payment-methods')).accounts || [])
  .find((a) => a.provider === 'manual' && a.status === 'active' && a.instructions);

/** Publish one agreement of `kind`: reuse a published one, else publish a draft, else write the draft first. */
async function publishKind(page, h, kind, text) {
  if ((await docsOf(page, kind)).some((d) => d.status === 'published')) return R.reuse(h, `the published ${kind}`);
  const rowsOf = () => page.locator(`[data-testid="agreement-row"][data-kind="${kind}"]`);
  if (!(await docsOf(page, kind)).some((d) => d.status === 'draft')) {
    const form = page.getByTestId('agreement-form');
    await h.scrollTo(form);
    await R.choose(h, form.locator('select[name="kind"]'), kind);
    await R.type(page, h, form.locator('input[name="version_label"]'), LABEL);
    await R.type(page, h, form.locator('textarea[name="body_text"]'), text);
    await h.click(form.getByRole('button', { name: /save draft/i }));
    await h.expect(rowsOf().and(page.locator('[data-status="draft"]')).first()).toBeVisible({ timeout: 15_000 });
  }
  const draft = rowsOf().and(page.locator('[data-status="draft"]')).first();
  await h.scrollTo(draft);
  await h.click(draft.getByRole('button', { name: /publish/i }));
  await h.expect(rowsOf().and(page.locator('[data-status="published"]')).first()).toBeVisible({ timeout: 15_000 });
  const published = (await docsOf(page, kind)).filter((d) => d.status === 'published');
  h.expect(published.length, `one published ${kind}`).toBe(1);
}

module.exports = R.scenario({
  id: 'REH-02b-agency-setup',
  title: 'Rehearsal: the agency owner sets up payments, booking terms and a waiver',
  titleVi: 'Diễn tập: chủ đại lý thiết lập thanh toán, điều khoản đặt chỗ và bản miễn trừ',
  allowWrites: R.bffWrites(['PUT', 'settings/payment-methods/manual'], ['POST', 'agreements'], ['POST', `agreements/${R.UUID}/publish`]),
  steps: [
    step('The owner of the new agency opens Settings, Payments. Clients pay the agency directly, so it says how.',
      'Chủ của đại lý mới mở Settings, mục Payments. Khách trả tiền thẳng cho đại lý, nên đại lý ghi rõ cách trả.',
      async (page, h) => {
        module.exports.meta.writes = await R.cap(page, [
          ['payment_method', 'PUT', R.bffPath('settings/payment-methods/manual'), 1],
          ['draft', 'POST', R.bffPath('agreements'), 2],
          ['publish', 'POST', R.bffPath(`agreements/${R.UUID}/publish`), 2],
        ]);
        await R.sha(page, module.exports, 'start');
        await R.open(page, h, '/settings/payments', 'crm-payments-settings');
        await R.me(page, 'owner');
        const panel = page.getByTestId('payment-methods');
        await h.expect(panel.locator('form')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
        await h.scrollTo(panel);
        await h.hover(panel);
      }),
    step('She saves the bank-transfer instructions. Every detail here is invented for the rehearsal.',
      'Chị lưu hướng dẫn chuyển khoản. Mọi thông tin ở đây đều là dữ liệu giả lập cho buổi diễn tập.',
      async (page, h) => {
        const panel = page.getByTestId('payment-methods');
        if (await manualMethod(page)) {
          R.reuse(h, 'the bank-transfer instructions');
        } else {
          const saved = page.waitForResponse((r) => /\/settings\/payment-methods\/manual$/.test(new URL(r.url()).pathname) && r.request().method() === 'PUT', { timeout: 30_000 });
          await R.type(page, h, panel.locator('textarea').first(), BANK);
          await h.click(panel.getByRole('button', { name: 'Save instructions' }));
          h.expect((await saved).status()).toBeLessThan(300);
          await h.expect(panel.getByRole('status')).toContainText('Payment instructions saved.', { timeout: 15_000 });
        }
        h.expect(await manualMethod(page), 'an active manual method with instructions').toBeTruthy();
      }, { writes: true }),
    step('Then Settings, Agreements: the documents the agency\'s clients accept and sign.',
      'Tiếp theo là Settings, mục Agreements: các giấy tờ khách của đại lý chấp nhận và ký.',
      async (page, h) => {
        await R.open(page, h, '/settings/agreements', 'agreements-view');
        await h.expect(page.getByTestId('agreements-view')).toHaveAttribute('data-hydrated', 'true', { timeout: 20_000 });
        await h.hover(page.getByTestId('agreement-form'));
      }),
    step('She writes the booking terms and publishes them. Clients accept them together with a proposal.',
      'Chị viết điều khoản đặt chỗ và phát hành. Khách chấp nhận điều khoản cùng với báo giá.',
      async (page, h) => {
        await publishKind(page, h, 'booking_terms', TERMS_TEXT);
      }, { writes: true }),
    step('She does the same for a waiver. Travellers sign it in their portal after the deposit.',
      'Chị làm tương tự với bản miễn trừ. Khách ký bản này trong cổng riêng sau khi đặt cọc.',
      async (page, h) => {
        await publishKind(page, h, 'waiver', WAIVER_TEXT);
      }, { writes: true }),
    step('Both documents are published and the payment instructions are saved: the agency is ready for its first client.',
      'Cả hai giấy tờ đã phát hành và hướng dẫn thanh toán đã lưu: đại lý sẵn sàng đón khách đầu tiên.',
      async (page, h) => {
        for (const kind of ['booking_terms', 'waiver']) {
          await h.expect(page.locator(`[data-testid="agreement-row"][data-kind="${kind}"][data-status="published"]`).first()).toBeVisible({ timeout: 15_000 });
        }
        h.expect(await manualMethod(page), 'the payment instructions').toBeTruthy();
        await h.hover(page.locator('[data-testid="agreement-row"][data-status="published"]').first());
        R.save({ agency_setup_at: new Date().toISOString() });
        await R.sha(page, module.exports, 'end');
      }),
  ],
});
