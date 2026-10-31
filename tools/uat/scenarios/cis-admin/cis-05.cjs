// Dry-run scenario CIS-05 (AA-1009, plan §4): Social content (atom curation), read only.
// Given: the E2E CIS admin (read-only session). When: they open Social Content.
// Then: the title and the content tiles render; no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'CIS-05',
  app: 'cis-admin',
  identity: 'cis-admin',
  title: 'Social content: the atoms behind social posts',
  titleVi: 'Nội dung mạng xã hội: các mẩu nội dung dùng cho bài đăng',
  baseURL: HOSTS.cisAdmin,
  steps: [
    step('Social Content shows the short content pieces the platform cuts from each tour for social posts.',
      'Trang Social Content hiển thị các mẩu nội dung ngắn mà nền tảng tách từ mỗi tour cho bài đăng mạng xã hội.',
      async (page, h) => {
        await check(page, h, '/admin/atom-curation', { heading: 'Social Content', ready: '[data-testid="admin-content-ready"]' });
      }),
    step('The counters and the list loaded. Nothing is changed. This is the end of the scenario.',
      'Các số đếm và danh sách đã tải. Không thay đổi gì. Kết thúc kịch bản.',
      async (page, h) => {
        await h.scrollTo(page.getByTestId('admin-content-ready'));
        await h.smoothScrollBy(400);
      }),
  ],
});
