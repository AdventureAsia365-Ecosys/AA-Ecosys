// Shared steps of the pilot rehearsal publish scenarios REH-04b-wordpress and REH-04b-facebook (AA-1086; root
// docs/ops/runbooks/pilot-rehearsal.md step 4b): connect the test channel when the agency has no connection yet (the
// test site / test Page credentials from Secrets Manager, typed into the masked form, never printed), publish the
// piece, take it down, publish it again, and check that one post only is live. Not a scenario (leading underscore).
// The studio takes a pasted WordPress Application Password and a pasted Facebook Page token (no OAuth window), so
// both channels run without a third-party login on camera.
'use strict';
const { step, check } = require('../../lib/dryrun-page.cjs');
const { studioCall, limitWrites, AI_MARK } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');

const CH = {
  wordpress: {
    channel: 'blog', label: 'WordPress', piece: 'blog', summary: 'publish-wp-summary', status: `${R.T}/integrations/wordpress`,
    save: 'wpSave', test: 'wpTest', connected: 'Connected — WordPress verified successfully.',
    fields: (c) => [['e.g. https://yourblog.com', c.site_url], ['e.g. your WordPress username', c.app_user],
      ['xxxx xxxx xxxx xxxx xxxx xxxx', c.app_password]],
    mask: ['input[placeholder="e.g. your WordPress username"]', 'input[type="password"]'],
  },
  facebook: {
    channel: 'facebook', label: 'Facebook', piece: 'facebook', summary: 'publish-fb-summary', status: `${R.T}/integrations/facebook`,
    save: 'fbSave', test: 'fbTest', connected: 'Connected — Facebook Page verified successfully.',
    fields: (c) => [['e.g. 104123456789012', c.page_id], ['e.g. EAAB…', c.page_access_token]],
    // The Page id is the test Page owner's own Page: blurred in the form, the summary card and the post links.
    mask: ['input[inputmode="numeric"]', 'input[type="password"]', '[data-testid="publish-fb-summary"]'],
  },
};

/** The writes a publish scenario of `name` may make (allowWrites sources). */
function allowFor(name) {
  const c = CH[name];
  return R.allow(c.save, c.test, 'publish', 'unpublish');
}

/** The pending card of a piece title (the innermost block holding the title and a Publish button). */
const pendingCard = (page, title) => page.getByText(title, { exact: true }).first()
  .locator('xpath=ancestor::div[.//button[normalize-space()="Publish"]][1]');

function publishSteps(name, state) {
  const c = CH[name];
  const rowsOf = async (page) => (await R.publishLog(page)).filter((r) => r.piece_id === state.piece.piece_id && r.channel === c.channel);

  /** The piece's row of GET /v1/publish-log/pending ({ piece_id, title, channel }), or null. */
  async function pendingRow(page) {
    const d = await R.getJson(page, `${R.T}/publish-log/pending`, 'the pieces ready to publish');
    return (Array.isArray(d.data) ? d.data : []).find((p) => p.piece_id === state.piece.piece_id) || null;
  }

  async function publishOnce(page, h) {
    let row = null;
    for (const until = Date.now() + 30_000; !(row = await pendingRow(page)) && Date.now() < until;) await page.waitForTimeout(2_000);
    if (!row) throw new Error(`the ${c.label} piece is not in Ready to Publish`);
    const card = pendingCard(page, row.title);
    await h.scrollTo(card, 'center');
    const sent = page.waitForResponse((r) => R.isCall(r, R.PATHS.publish), { timeout: 120_000 });
    await h.click(card.getByRole('button', { name: 'Publish', exact: true }));
    const res = await sent;
    const body = await res.json().catch(() => ({}));
    if (res.status() !== 200 || body.success !== true) throw new Error(`publishing to ${c.label} answered ${res.status()} (success ${body.success})`);
    await h.expect(card.getByText('Published.').first()).toBeVisible({ timeout: 30_000 });
    return body;
  }

  /** WordPress only: the live post page carries the planner link and the AI mark on its <article>. */
  async function checkLivePost(page, h, url) {
    if (name !== 'wordpress') return;
    await h.goto(url);
    const html = await page.content();
    if (!html.includes(state.link)) throw new Error('the live post does not carry the planner link of tour X');
    if (!AI_MARK.article.test(html)) throw new Error('the live post has no AI mark on its <article>');
    await h.scrollTo(page.locator(`a[href="${state.link}"]`).first(), 'center');
  }

  return [
    step(`Publish holds the agency's channels and the pieces ready to go out. The owner opens it for ${c.label}.`,
      `Mục Đăng bài chứa các kênh của đại lý và các bài sẵn sàng đăng. Chủ đại lý mở mục này cho ${c.label}.`,
      async (page, h) => {
        state.counts = await limitWrites(page, [
          { name: 'save', path: R.PATHS[c.save], max: 1 }, { name: 'test', path: R.PATHS[c.test], max: 1 },
          { name: 'publish', path: R.PATHS.publish, max: 2 },
        ]);
        await check(page, h, '/portal/content/publish', { heading: 'Publish' });
        state.piece = await R.readyPiece(page, c.piece);
        if (!state.piece) throw new Error(`no ready ${c.label} piece on the rehearsal agency (record the step 4 scenarios first)`);
        state.link = R.reh.plannerLink((await R.findTourX(page)).tour_id);
        if ((await rowsOf(page)).some((r) => r.status === 'published')) {
          throw new Error(`the piece is already live on ${c.label}: take it down first (REH-04b-takedown), then record again`);
        }
        if (name === 'wordpress' && !String(state.piece.content_text || '').includes(state.link)) {
          throw new Error('the article does not carry the planner link yet (record REH-04-edit first)');
        }
      }),
    step(`The agency connects its ${c.label}: the details are pasted once, then tested. They never show again.`,
      `Đại lý kết nối ${c.label}: dán thông tin một lần rồi kiểm tra. Thông tin này không bao giờ hiện lại.`,
      async (page, h) => {
        const st = await studioCall(page, 'GET', c.status);
        if (st.status !== 200) throw new Error(`reading the ${c.label} connection answered ${st.status}`);
        if (st.data && st.data.connected) {
          await h.expect(page.getByTestId(c.summary)).toBeVisible({ timeout: 30_000 });
          await h.hover(page.getByTestId(c.summary));
          return;
        }
        const creds = R.reh.channelCreds(name);
        if (name === 'wordpress') {
          // The free test site expires after about two weeks and then answers HTML (runbook step 0.6).
          const wp = await page.context().request.get(`${creds.site_url.replace(/\/+$/, '')}/wp-json/`, { timeout: 20_000 });
          if (wp.status() !== 200 || !/json/.test(wp.headers()['content-type'] || '')) throw new Error('the WordPress test site does not answer JSON on /wp-json/ (expired?)');
        }
        for (const [ph, value] of c.fields(creds)) {
          const f = page.getByPlaceholder(ph, { exact: true }).first();
          await h.click(f);
          await f.fill(value);
        }
        await h.assertMasked(c.mask.filter((m) => !m.startsWith('[data-testid')));
        await h.click(page.getByRole('button', { name: 'Test & Connect' }).first());
        await h.expect(page.getByText(c.connected).or(page.getByTestId(c.summary)).first()).toBeVisible({ timeout: 60_000 });
      }, { writes: true }),
    step(`Publish sends the piece to ${c.label}. The post goes live with the text the agency approved.`,
      `Bấm Đăng bài để gửi bài lên ${c.label}. Bài lên trực tuyến với đúng nội dung đại lý đã duyệt.`,
      async (page, h) => {
        const body = await publishOnce(page, h);
        state.firstUrl = body.external_url;
        const live = (await rowsOf(page)).filter((r) => r.status === 'published');
        if (live.length !== 1) throw new Error(`${live.length} live ${c.label} posts for the piece after publishing`);
        if (state.firstUrl) await checkLivePost(page, h, state.firstUrl);
      }, { writes: true }),
    step('Unpublish takes the post down. The publish log keeps the record, and the piece is ready to publish again.',
      'Gỡ bài sẽ đưa bài xuống. Nhật ký đăng bài vẫn giữ lại, và bài sẵn sàng để đăng lại.',
      async (page, h) => {
        await check(page, h, '/portal/content/publish', { heading: 'Publish' });
        const live = (await rowsOf(page)).find((r) => r.status === 'published');
        const row = page.locator('[data-testid="kit-datatable-row"]').filter({ hasText: live.title }).first();
        await h.scrollTo(row, 'center');
        await h.click(row.getByRole('button', { name: 'Unpublish' }));
        const removed = page.waitForResponse((r) => R.isCall(r, R.PATHS.unpublish, 'DELETE'), { timeout: 60_000 });
        await h.click(page.getByRole('dialog').getByRole('button', { name: 'Unpublish' }));
        const res = await removed;
        if (res.status() !== 200) throw new Error(`unpublishing answered ${res.status()}`);
        await h.expect(page.getByText(`Removed from ${c.label}.`).first()).toBeVisible({ timeout: 30_000 });
        const rows = await rowsOf(page);
        if (rows.some((r) => r.status === 'published')) throw new Error('the post is still live after Unpublish');
        if (!rows.some((r) => r.publish_id === live.publish_id && r.status === 'unpublished')) throw new Error('the publish log has no unpublished row');
      }, { writes: true }),
    step(`Publishing again puts one post back. ${c.label} never shows the same piece twice. This is the end of the scenario.`,
      `Đăng lại sẽ đưa đúng một bài trở lại. ${c.label} không bao giờ hiện cùng một bài hai lần. Kết thúc kịch bản.`,
      async (page, h) => {
        const body = await publishOnce(page, h);
        const rows = await rowsOf(page);
        const live = rows.filter((r) => r.status === 'published');
        if (live.length !== 1) throw new Error(`${live.length} live ${c.label} posts for the piece after publishing again`);
        if (!rows.some((r) => r.status === 'unpublished')) throw new Error('the first post is not recorded as unpublished');
        if (body.external_url) await checkLivePost(page, h, body.external_url);
        const n = state.counts;
        if (n.publish !== 2 || n.save > 1 || n.test > 1) throw new Error(`unexpected write counts ${JSON.stringify(n)}`);
      }, { writes: true }),
  ];
}

module.exports = { CH, allowFor, publishSteps, pendingCard };
