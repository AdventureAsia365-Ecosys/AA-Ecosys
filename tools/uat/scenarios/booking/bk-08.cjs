// Dry-run scenario BK-08 (AA-1009, plan §4): operations, the read part: invoices, payments and trip checks.
// Given: the E2E Booking staff (read-only session). When: they open Payments & invoices (both tabs), then Trip
// checks. Then: each list renders its rows or the empty state; no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check, openTab, rowsOrEmpty } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'BK-08',
  app: 'booking',
  identity: 'booking',
  title: 'Operations: invoices, payments and trip checks',
  titleVi: 'Vận hành: hoá đơn, thanh toán và kiểm tra chuyến đi',
  baseURL: HOSTS.booking,
  steps: [
    step('Payments and invoices opens on the customer invoices and what is still due.',
      'Trang Thanh toán và hoá đơn mở ra với hoá đơn khách hàng và số tiền còn phải thu.',
      async (page, h) => {
        await check(page, h, '/billing', { heading: 'Payments & invoices', table: true });
      }),
    step('The payments tab lists the money received and how it was matched.',
      'Thẻ thanh toán liệt kê tiền đã nhận và cách đối chiếu.',
      async (page, h) => {
        await openTab(page, h, 'Payments');
        await rowsOrEmpty(page, h);
      }),
    step('Trip checks list what must be confirmed before each departure. This is the end of the scenario.',
      'Kiểm tra chuyến đi liệt kê những gì phải xác nhận trước mỗi chuyến khởi hành. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/trip-checks', { heading: 'Trip checks', table: true });
      }),
  ],
});
