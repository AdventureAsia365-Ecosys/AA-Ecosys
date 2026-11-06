// Dry-run scenario BK-08 (AA-1009, plan §4): operations, the read part: supplier bills, agency billing and trip
// checks. The customer invoices and payments left with the B2C half of Booking (AA-1046, root ADR 0019): agency
// money is Agency billing, AA's own payables are the supplier bills.
// Given: the E2E Booking staff (read-only session). When: they open Supplier bills, Agency billing, then Trip
// checks. Then: each list renders its rows or the empty state; no API call fails; nothing is written. $0.
const { HOSTS, step, ro, check } = require('../../lib/dryrun-page.cjs');

module.exports = ro({
  id: 'BK-08',
  app: 'booking',
  identity: 'booking',
  title: 'Operations: supplier bills, agency billing and trip checks',
  titleVi: 'Vận hành: hoá đơn nhà cung cấp, thanh toán đại lý và kiểm tra chuyến đi',
  baseURL: HOSTS.booking,
  steps: [
    step('Supplier bills lists the bills suppliers sent, matched to confirmed bookings, and what is still to pay.',
      'Trang Hoá đơn nhà cung cấp liệt kê hoá đơn nhà cung cấp gửi, khớp với các đặt chỗ đã xác nhận, và số tiền còn phải trả.',
      async (page, h) => {
        await check(page, h, '/billing', { heading: 'Supplier bills', table: true });
      }),
    step('Agency billing lists every invoice from the company to an agency: the software fee and the tour settlement.',
      'Trang Thanh toán đại lý liệt kê mọi hoá đơn công ty gửi đại lý: phí phần mềm và quyết toán tour.',
      async (page, h) => {
        await check(page, h, '/agency-billing', { heading: 'Agency billing', table: true });
      }),
    step('Trip checks list what must be confirmed before each departure. This is the end of the scenario.',
      'Kiểm tra chuyến đi liệt kê những gì phải xác nhận trước mỗi chuyến khởi hành. Kết thúc kịch bản.',
      async (page, h) => {
        await check(page, h, '/trip-checks', { heading: 'Trip checks', table: true });
      }),
  ],
});
