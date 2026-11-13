// UAT scenario REH-04b-takedown (pilot rehearsal Teardown 4; root docs/ops/runbooks/pilot-rehearsal.md): the agency
// owner removes every post the rehearsal left live on the WordPress test site and the Facebook test Page, from the
// studio's Published list (Unpublish -> confirm). Run it at teardown, after X3, or before re-recording REH-04b-*.
// Writes only DELETE /v1/publish-log/<publish id> (the post goes to the WordPress trash / is deleted on the Page), on
// pilot-rehearsal-01 only (pilot guard): allowed for DELETE only, and capped by limitWrites at the number of live posts
// read in step 1 (never more than MAX_POSTS). No model call: cost $0. Nothing live = the scenario passes without a write.
// Given: the rehearsal owner. Then: the publish log of the agency holds no live post; each one reads Unpublished.
const { HOSTS, step, check } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const R = require('./_rehearsal.cjs');
const P = require('./_publish.cjs');

const MAX_POSTS = 6; // the rehearsal publishes two; a few spare for re-takes, never an open-ended loop
let live = [];
let counts = null;
// The DELETE cap: 0 until step 1 has read the live posts, then exactly their number (read when each request arrives).
const cap = [{ name: 'unpublish', path: R.PATHS.unpublish, method: R.methodOf('unpublish'), max: 0 }];

module.exports = rw({
  id: 'REH-04b-takedown',
  app: 'content-studio',
  identity: R.IDENTITY,
  title: 'Pilot rehearsal: take the test posts down',
  titleVi: 'Diễn tập pilot: gỡ các bài đăng thử',
  baseURL: HOSTS.partner,
  allowWrites: R.allow('unpublish'),
  mask: ['[data-testid="publish-fb-summary"]'],
  steps: [
    step('Published lists every post the agency put on its channels, live or taken down.',
      'Mục Đã đăng liệt kê mọi bài đại lý đã đưa lên các kênh, đang hiện hay đã gỡ.',
      async (page, h) => {
        counts = await limitWrites(page, cap);
        await check(page, h, '/portal/content/publish', { heading: 'Publish' });
        live = (await R.publishLog(page)).filter((r) => r.status === 'published');
        cap[0].max = Math.min(live.length, MAX_POSTS);
        if (live.length > MAX_POSTS) throw new Error(`${live.length} live posts: more than a rehearsal leaves, check them by hand`);
        await h.scrollTo(page.getByRole('heading', { name: 'Published' }).first(), 'center');
      }),
    step('The owner unpublishes each live test post. WordPress moves it to the trash; Facebook deletes it.',
      'Chủ đại lý gỡ từng bài đăng thử còn hiện. WordPress chuyển bài vào thùng rác; Facebook xoá bài.',
      async (page, h) => {
        if (!live.length) {
          // Nothing to take down: show that the Published list offers no Unpublish, and write nothing.
          await h.expect(page.locator('[data-testid="kit-datatable-row"]').filter({ has: page.getByRole('button', { name: 'Unpublish' }) }))
            .toHaveCount(0, { timeout: 30_000 });
          return;
        }
        for (const r of live) {
          const row = page.locator('[data-testid="kit-datatable-row"]').filter({ hasText: r.title })
            .filter({ has: page.getByRole('button', { name: 'Unpublish' }) }).first();
          await h.scrollTo(row, 'center');
          await h.click(row.getByRole('button', { name: 'Unpublish' }));
          const removed = page.waitForResponse((x) => R.isCall(x, R.PATHS.unpublish, 'DELETE'), { timeout: 60_000 });
          await h.click(page.getByRole('dialog').getByRole('button', { name: 'Unpublish' }));
          const res = await removed;
          if (res.status() !== 200) throw new Error(`unpublishing a ${P.CH[r.channel === 'blog' ? 'wordpress' : 'facebook'].label} post answered ${res.status()}`);
          await h.expect(page.getByRole('dialog')).toHaveCount(0, { timeout: 30_000 });
        }
      }, { writes: true }),
    step('No test post is live any more. The log keeps each one as Unpublished. This is the end of the scenario.',
      'Không còn bài đăng thử nào hiện. Nhật ký vẫn giữ từng bài với trạng thái Đã gỡ. Kết thúc kịch bản.',
      async (page, h) => {
        const rows = await R.publishLog(page);
        if (rows.some((r) => r.status === 'published')) throw new Error('a post is still live');
        for (const r of live) if (!rows.some((x) => x.publish_id === r.publish_id && x.status === 'unpublished')) throw new Error('a removed post is not logged as unpublished');
        if (live.length) await h.expect(page.getByText('Unpublished').first()).toBeVisible({ timeout: 30_000 });
        if (counts.unpublish !== live.length) throw new Error(`${counts.unpublish} unpublish requests for ${live.length} live posts`);
      }),
  ],
});
