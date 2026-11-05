// CRM review R00 (skill aa-uat-video; plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): the opening cards.
// Given: nobody signed in (cards only); the CRM health endpoint answers.
// When:  the viewer sees what the CRM is, how far the build is, and the order of the working day that follows.
// Then:  each card renders its heading and every line; the CRM version is recorded at the start and the end.
// Slides only (lib/slide.cjs, English): no product screen is drawn, no data written, no LLM call. Cost $0.
// AA-855: the build-progress slide (step 2) is internal: the UAT cut leaves it out (UAT_CUT=internal keeps it), and
// the first card then says it is the acceptance walk-through, not an internal review.
const slide = require('../../lib/slide.cjs');
const { base, sha, uatCut, INTERNAL_CUT } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-00', title: 'CRM review: what the partner CRM is and how far it is built', titleVi: 'Giới thiệu CRM cho đại lý và mức độ hoàn thành', who: null });

sc.steps = uatCut([
  {
    caption: INTERNAL_CUT ? {
      en: 'This is an internal review of the partner CRM: the tool a travel agency uses for inquiries, trips, proposals, bookings, money and its travellers.',
      vi: 'Đây là video review nội bộ của CRM cho đại lý: công cụ đại lý dùng để nhận yêu cầu, quản lý chuyến, gửi đề xuất, đặt dịch vụ, thu tiền và chăm sóc khách.',
    } : {
      en: 'This is the acceptance walk-through of the partner CRM: the tool a travel agency uses for inquiries, trips, proposals, bookings, money and its travellers.',
      vi: 'Đây là video nghiệm thu CRM cho đại lý: công cụ đại lý dùng để nhận yêu cầu, quản lý chuyến, gửi đề xuất, đặt dịch vụ, thu tiền và chăm sóc khách.',
    },
    run: async (page, h) => {
      await sha(page, sc, 'start');
      await slide.show(page, h, {
        kicker: INTERNAL_CUT ? 'CRM review · internal dry run' : 'CRM · acceptance round 1',
        title: 'Adventure Asia Partner CRM',
        lead: 'One working day of a partner agency, from a new inquiry to a booked trip, on the development environment with invented data.',
        bullets: ['Agency: Lữ hành Sen Vàng (invented)', 'Clients: invented people on addresses that never receive mail', 'Interface in English; a Vietnamese voice track is included'],
      });
    },
  },
  {
    internal: true, // the build-progress slide: internal review only, never in the UAT cut
    caption: {
      en: 'About eighty percent of the planned CRM is built. Intake, the pipeline, bookings, suppliers and the traveller portal (its itinerary now also opens offline) are complete; commissions and trip cancel are in. Card payments are not live yet, the AI assistant runs in test mode only, and workflows and WhatsApp or SMS are not started.',
      vi: 'CRM theo kế hoạch đã làm được khoảng tám mươi phần trăm. Phần nhận yêu cầu, pipeline, booking, nhà cung cấp và cổng khách (nay xem được lịch trình cả khi không có mạng) đã xong; hoa hồng và huỷ chuyến cũng đã có. Thanh toán bằng thẻ chưa chạy thật, trợ lý AI mới chạy chế độ thử, còn quy trình tự động và WhatsApp, SMS thì chưa bắt đầu.',
    },
    run: async (page, h) => {
      // Tile values: tools/uat/scenarios/crm/PROGRESS.md (S261 method, recomputed S262 01/11/2026).
      await slide.show(page, h, {
        kicker: 'Where the build stands',
        title: 'About 80% of the planned CRM is built',
        tiles: [
          { value: '100%', label: 'Intake and pipeline' },
          { value: '83-100%', label: 'Proposals (interactive and written)' },
          { value: '95-100%', label: 'Bookings, suppliers and commissions', note: 'one-action trip cancel included' },
          { value: '90%', label: 'Invoices and payments', note: 'card payments not yet' },
          { value: '100%', label: 'Traveller portal', note: 'itinerary works offline' },
          { value: '90-95%', label: 'Email, reports and data export' },
          { value: '90-95%', label: 'Trip hand-over to Adventure Asia, support access', note: 'staff screen not live yet' },
          { value: '0-50%', label: 'Workflows, WhatsApp/SMS, AI', note: 'AI in test mode only; the rest not started' },
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
]);

module.exports = sc;
