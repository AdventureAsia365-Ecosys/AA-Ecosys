// CRM review R20 (plan docs/audits/2026-10-31-S261-crm-progress-video-plan §3): the closing card.
// Given: nobody signed in (cards only); the CRM health endpoint answers.
// When:  the viewer sees the build status per area and what comes next.
// Then:  each card renders its heading and every line; no date is promised; the CRM version is recorded at both ends.
// Slides only (lib/slide.cjs, English): no data written, no LLM call. Cost $0.
const slide = require('../../lib/slide.cjs');
const { base, sha } = require('./_crm.cjs');

const sc = base({ id: 'CRM-REV-20', title: 'Where the CRM stands and what comes next', titleVi: 'CRM đang ở đâu và bước tiếp theo', who: null });

sc.steps = [
  {
    caption: {
      en: 'To sum up: about seventy percent of the planned CRM is built and runs end to end, from the first inquiry to a booked trip and a signed traveller.',
      vi: 'Tóm lại: khoảng bảy mươi phần trăm CRM theo kế hoạch đã được làm và chạy trọn vẹn, từ yêu cầu đầu tiên tới chuyến đã đặt và khách đã ký.',
    },
    run: async (page, h) => {
      await sha(page, sc, 'start');
      await slide.show(page, h, {
        kicker: 'Where the build stands',
        title: 'About 70% built, working end to end',
        tiles: [
          { value: '100%', label: 'Intake, pipeline, bookings, suppliers' },
          { value: '83-100%', label: 'Proposals', note: 'map in the builder not yet' },
          { value: '90%', label: 'Invoices and payments', note: 'card payments not yet' },
          { value: '95%', label: 'Contracts and e-sign', note: 'signed PDF not yet' },
          { value: '76%', label: 'Traveller portal', note: 'offline use not yet' },
          { value: '90%', label: 'Email, reports, data requests' },
          { value: '0-5%', label: 'Workflows, WhatsApp/SMS, commissions, AI' },
        ],
      });
    },
  },
  {
    caption: {
      en: 'Next come the missing pieces of the modules shown today, then the modules not started, then the hardening needed to run for real.',
      vi: 'Tiếp theo là các phần còn thiếu của những module vừa xem, rồi tới các module chưa bắt đầu, sau đó là phần gia cố để chạy thật.',
    },
    run: async (page, h) => {
      await slide.show(page, h, {
        kicker: 'What comes next',
        title: 'Next steps',
        bullets: [
          'Finish the parts marked "Not ready yet" in this review',
          'Build the modules not started: workflows and tasks, commissions, WhatsApp and SMS, campaigns, the library',
          'AI help once the AI service is available again',
          'Harden and prepare to run for real: security review, service targets, load tests, live payments',
        ],
        foot: 'Internal review on the development environment with invented data. Thank you for watching.',
      });
      await h.pause(1200);
      await sha(page, sc, 'end');
    },
  },
];

module.exports = sc;
