// UAT scenario PORTAL-PUB-01 (skill aa-uat-video): a partner agency reads the public legal pages.
// Given: a visitor with no account on the agency host (the AA-Partner web app; /terms answers 308 to /legal/partner-terms).
// When:  they open the partner terms, read the AI clause, follow the link to the privacy notice.
// Then:  each page shows its heading and the expected numbered sections.
// Public pages only: no sign-in, no form submit, no LLM call. Cost $0.
module.exports = {
  id: 'PORTAL-PUB-01',
  app: 'partner-portal',
  title: 'Read the partner terms and the privacy notice',
  baseURL: process.env.UAT_BASE_URL || 'https://portal.lumiguides.it.com',
  viewport: { width: 1440, height: 900 },
  steps: [
    {
      caption: {
        en: 'A partner agency opens the public terms page on the agency portal. No sign-in is needed.',
        vi: 'Một đại lý đối tác mở trang điều khoản công khai trên cổng đại lý. Không cần đăng nhập.',
      },
      run: async (page, h) => {
        await h.goto('/terms');
        await h.expect(page.locator('h1')).toHaveText('Partner terms');
      },
    },
    {
      caption: {
        en: 'Section three explains the rules for AI-generated content and acceptable use.',
        vi: 'Mục ba nêu quy định về nội dung do AI tạo và việc sử dụng được chấp nhận.',
      },
      run: async (page, h) => {
        const s3 = page.getByRole('heading', { name: /3\. AI-generated content/ });
        await h.scrollTo(s3);
        await h.expect(s3).toBeVisible();
        await h.hover(page.getByRole('link', { name: 'Anthropic Usage Policy' }));
      },
    },
    {
      caption: {
        en: 'Plans, availability and liability follow, then the contact address.',
        vi: 'Tiếp theo là gói dịch vụ, mức độ sẵn sàng, trách nhiệm pháp lý và địa chỉ liên hệ.',
      },
      run: async (page, h) => {
        await h.scrollTo(page.getByRole('heading', { name: /7\. Plans and fees/ }));
        await h.expect(page.getByRole('heading', { name: /10\. Contact/ })).toBeVisible();
      },
    },
    {
      caption: {
        en: 'The agency follows the link to the privacy notice.',
        vi: 'Đại lý bấm vào liên kết sang trang thông báo quyền riêng tư.',
      },
      run: async (page, h) => {
        // The studio's legal pages moved to /legal/* in the agency web app (AA-Partner web/lib/studio/legal.ts); /terms
        // and /privacy only answer 308, so no link on the page points at /privacy any more. The body link in "10. Contact".
        await h.click(page.locator('main a[href="/legal/privacy"]').first());
        await page.waitForURL('**/legal/privacy');
        await h.expect(page.locator('h1')).toHaveText('Privacy notice');
      },
    },
    {
      caption: {
        en: 'The notice explains how AI processing works and where the data is stored.',
        vi: 'Thông báo giải thích cách AI xử lý dữ liệu và dữ liệu được lưu ở đâu.',
      },
      run: async (page, h) => {
        await h.scrollTo(page.getByRole('heading', { name: /5\. AI processing/ }));
        await h.pause(1500);
        await h.scrollTo(page.getByRole('heading', { name: /7\. Where your data is stored/ }));
        await h.expect(page.getByRole('heading', { name: /7\. Where your data is stored/ })).toBeVisible();
      },
    },
    {
      caption: {
        en: 'Both pages loaded with every section in place. This is the end of the scenario.',
        vi: 'Cả hai trang đều hiển thị đủ các mục. Kết thúc kịch bản.',
      },
      run: async (page, h) => {
        await h.expect(page.getByRole('heading', { name: /11\. Changes to this notice/ })).toHaveCount(1);
        await h.smoothScrollBy(-400);
      },
    },
  ],
};
