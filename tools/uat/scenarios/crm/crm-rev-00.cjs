// CRM review R00 (skill aa-uat-video; plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): the opening cards.
// Given: nobody signed in (cards only); the CRM health endpoint answers.
// When:  the viewer sees what the CRM is, how far the build is, and the order of the working day that follows.
// Then:  each card renders its heading and every line; the CRM version is recorded at the start and the end.
// Slides only (lib/slide.cjs, English): no product screen is drawn, no data written, no LLM call. Cost $0.
const slide = require('../../lib/slide.cjs');
const { base, sha } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-00', title: 'CRM review: what the partner CRM is and how far it is built', titleVi: 'Giới thiệu CRM cho đại lý và mức độ hoàn thành', who: null });

sc.steps = [
  {
    caption: {
      en: 'This is an internal review of the partner CRM: the tool a travel agency uses for inquiries, trips, proposals, bookings, money and its travellers.',
      vi: 'Đây là video review nội bộ của CRM cho đại lý: công cụ đại lý dùng để nhận yêu cầu, quản lý chuyến, gửi đề xuất, đặt dịch vụ, thu tiền và chăm sóc khách.',
    },
    run: async (page, h) => {
      await sha(page, sc, 'start');
      await slide.show(page, h, {
        kicker: 'CRM review · internal dry run',
        title: 'Adventure Asia Partner CRM',
        lead: 'One working day of a partner agency, from a new inquiry to a booked trip, on the development environment with invented data.',
        bullets: ['Agency: Lữ hành Sen Vàng (invented)', 'Clients: invented people on addresses that never receive mail', 'Interface in English; a Vietnamese voice track is included'],
      });
    },
  },
  {
    caption: {
      en: 'About seventy percent of the planned CRM is built. Intake, the pipeline, bookings and suppliers are complete; money, the traveller portal and reports are mostly there.',
      vi: 'Khoảng bảy mươi phần trăm CRM theo kế hoạch đã được làm. Phần nhận yêu cầu, pipeline, sổ booking và nhà cung cấp đã xong; tiền, cổng khách và báo cáo đã có phần lớn.',
    },
    run: async (page, h) => {
      await slide.show(page, h, {
        kicker: 'Where the build stands',
        title: 'About 70% of the planned CRM is built',
        tiles: [
          { value: '100%', label: 'Intake and pipeline' },
          { value: '83-100%', label: 'Proposals (interactive and written)' },
          { value: '100%', label: 'Bookings and suppliers' },
          { value: '90%', label: 'Invoices and payments', note: 'card payments not yet' },
          { value: '76%', label: 'Traveller portal', note: 'offline use not yet' },
          { value: '90%', label: 'Email and reports' },
          { value: '90%', label: 'Data export and erasure' },
          { value: '0%', label: 'Workflows, WhatsApp/SMS, commissions, AI', note: 'not started or blocked' },
        ],
      });
    },
  },
  {
    caption: {
      en: 'The review follows the agency through its day. Screens that are not built yet are shown as they really are, with a short card naming what is missing.',
      vi: 'Video đi theo một ngày làm việc của đại lý. Màn hình nào chưa làm thì cho xem đúng như hiện tại, kèm một thẻ ngắn ghi rõ phần còn thiếu.',
    },
    run: async (page, h) => {
      await slide.show(page, h, {
        kicker: 'What follows',
        title: 'A working day of the agency',
        bullets: [
          'Home, getting started and importing clients',
          'A new inquiry, the pipeline and the client profile',
          'Proposals, acceptance on a phone, contracts and invoices',
          'The traveller portal, duty of care, email, suppliers and reports',
          'Data export, settings, the assistant view and what is not built yet',
        ],
      });
      await h.pause(1200);
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
