// CRM review R19 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): what is not built yet.
// Given: A (owner) signed in.
// When:  the owner opens the five menu entries that are still empty pages (Tasks, Automations, Commissions,
//        Marketing, Library), each for a moment, then a "Not ready yet" card lists the modules not built.
// Then:  each page is the real empty state (no fake screen); the card names only what is missing, with no date. (Help,
//        an empty page in the plan, is built now and is not shown here.)
// Read only: no write, no LLM call (AI buttons are never clicked). Cost $0.
const slide = require('../../lib/slide.cjs');
const { base, sha, open } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-19', title: 'What is not built yet', titleVi: 'Những phần chưa làm' });

const EMPTY = [
  ['tasks', 'Tasks: one list of every task across trips.', 'Tasks: một danh sách chung mọi việc của các chuyến.'],
  ['automations', 'Automations: follow-ups the CRM would create by itself.', 'Automations: việc nhắc theo dõi CRM tự tạo.'],
  ['commissions', 'Commissions: what the agency earns from each supplier.', 'Commissions: tiền hoa hồng đại lý nhận từ từng nhà cung cấp.'],
  ['marketing', 'Marketing: campaigns to past and future clients.', 'Marketing: chiến dịch gửi khách cũ và khách tiềm năng.'],
  ['library', 'Library: the agency\'s reusable texts, photos and day plans.', 'Library: kho văn bản, ảnh và lịch trình ngày dùng lại của đại lý.'],
];

sc.steps = [
  {
    caption: {
      en: 'Five entries in the menu are still empty pages. They are shown as they really are.',
      vi: 'Năm mục trong menu vẫn còn là trang trống. Video cho xem đúng như hiện tại.',
    },
    run: async (page, h) => {
      await sha(page, sc, 'start');
      await open(page, h, '/', 'crm-home');
      for (const [key] of EMPTY) await h.expect(page.locator(`a[href="/${key}"]`).first()).toBeVisible(); // in the menu
      await h.hover(page.locator(`a[href="/${EMPTY[0][0]}"]`).first());
    },
  },
  ...EMPTY.map(([key, en, vi]) => ({
    caption: { en, vi },
    run: async (page, h) => {
      await open(page, h, `/${key}`, `crm-section-${key}`);
      await h.expect(page.getByTestId('kit-empty-state')).toBeVisible();
      await h.pause(1500);
    },
  })),
  {
    caption: {
      en: 'Not ready yet, besides those pages: Adventure Asia\'s own release of bookings, WhatsApp and text messages, AI help, deeper support access, and the hardening and go-live work.',
      vi: 'Ngoài các trang đó, còn chưa có: bước xác nhận booking phía Adventure Asia, WhatsApp và tin nhắn SMS, trợ giúp bằng AI, quyền hỗ trợ sâu hơn, cùng phần gia cố và đưa vào chạy thật.',
    },
    run: async (page, h) => {
      await slide.notReady(page, h, {
        screen: 'Modules not built yet',
        missing: [
          'Workflows and one task list across trips; commissions; marketing campaigns; search and the library',
          'Adventure Asia\'s operations release of bookings (built on the Booking side, not yet in the CRM)',
          'WhatsApp and SMS through the agency\'s own account',
          'AI help for drafts and replies (waiting for the AI service to be available again)',
          'Deeper support access for Adventure Asia staff, with the client\'s and agency\'s consent',
          'Security review, service targets, load tests, and the steps to run for real (live payments, vendor checks)',
        ],
      });
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
