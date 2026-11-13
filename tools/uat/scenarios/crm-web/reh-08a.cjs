// UAT scenario REH-08a (pilot rehearsal, "Book now" books the tour its page shows; root ADR 0019, S278 audit M12): a
// guest opens Adventure Asia's public page of tour X on the client host through the synthetic agency's link
// (/trip/<tour id>?f=<the agency's form key>&p=<a decoy tour key>) and books it with the agency's Book now panel.
// 1440 x 900. $0: no model call. Writes: one price check (POST .../price, stores nothing) and one booking
// (POST .../bookings: a new traveller, a trip at Proposal and its one-option proposal, sent to the invented address).
// The decoy p= key proves the fix: the panel must book the page's own catalogue key (CIS GET /v1/trip/<id>
// source_id), never the key in the link.
// Needs: the agency's Book now switch on and its intake form key (CRM Settings > Online booking; env
// UAT_REH_FORM_KEY, never committed; result.json masks the f= value, lib/dryrun-core.cjs redact), tour X sellable for the agency (a departure inside the window, a retail price) and
// adopted on its planner (the page id is read from the agency's TripPlanner tour list; env UAT_REH_TOUR_X, or
// UAT_REH_TRIP_PAGE = the tour id of the page). The CRM half (the trip's AA line carries the same source id, in the
// agency's pipeline) is the CRM group's read. Record after the CRM read of step 6, so that read sees one lead only.
// Given: a guest with the agency's link. When: they pick a departure and a party, see the price, give a name, an email
// and the consent, and press Book now. Then: the panel asked for the page's key, the booking went out with it, and the
// client's proposal page opens on that tour.
const { HOSTS, step } = require('../../lib/dryrun-page.cjs');
const { rw, limitWrites } = require('../../lib/uat-page.cjs');
const R = require('../tripplanner/_rehearsal.cjs');

const FORM_KEY = /^[A-Za-z0-9_-]{20,64}$/;
const DECOY = 'rehearsal-decoy-tour-key';
const BOOK = /^\/crm\/public\/v1\/book\/[A-Za-z0-9_-]+$/;
const meta = {};
let counts = null;
let page0 = null; // { tourId, sourceId, title }
let widget = null; // the panel's answer

const sc = rw({
  id: 'REH-08a',
  app: 'crm',
  identity: 'traveller',
  paid: false,
  title: 'Book now on the tour page books that very tour',
  titleVi: 'Đặt ngay trên trang tour đặt đúng tour đó',
  baseURL: R.CLIENT,
  allowWrites: [`^${R.esc(R.CLIENT)}/crm/public/v1/book/[A-Za-z0-9_-]+/(?:price|bookings)$`],
  meta,
  steps: [
    step('A traveller opens an Adventure Asia tour page through the agency\'s link. Its Book now panel is below.',
      'Khách du lịch mở một trang tour của Adventure Asia qua đường dẫn của đại lý. Khung Đặt ngay nằm bên dưới.',
      async (page, h) => {
        counts = await limitWrites(page, [
          { name: 'price', path: /^\/crm\/public\/v1\/book\/[A-Za-z0-9_-]+\/price$/, max: 1, method: '*', accept: (req) => req.method() === 'POST' },
          { name: 'bookings', path: /^\/crm\/public\/v1\/book\/[A-Za-z0-9_-]+\/bookings$/, max: 1, method: '*', accept: (req) => req.method() === 'POST' },
        ]);
        const key = (process.env.UAT_REH_FORM_KEY || '').trim();
        if (!FORM_KEY.test(key)) throw new Error('UAT_REH_FORM_KEY is missing or not a form key (CRM Settings > Online booking of the rehearsal agency)');
        page0 = await tourPage(page);
        meta.tour = { tour_id: page0.tourId, source_id: page0.sourceId };
        const asked = page.waitForResponse((r) => BOOK.test(new URL(r.url()).pathname) && r.request().method() === 'GET', { timeout: 60_000 });
        await h.goto(`/trip/${page0.tourId}?f=${encodeURIComponent(key)}&p=${DECOY}`);
        await h.expect(page.getByTestId('trip-name')).toBeVisible({ timeout: 30_000 });
        const res = await asked;
        const tourParam = new URL(res.url()).searchParams.get('tour');
        if (tourParam !== page0.sourceId) throw new Error(`the panel asked for tour key "${tourParam === DECOY ? 'the decoy p=' : tourParam}", not the page's own key`);
        if (res.status() !== 200) throw new Error(`the Book now panel answered ${res.status()} (404 = Book now off, wrong form key or tour not bookable)`);
        widget = await res.json();
        if (widget.tour !== page0.sourceId) throw new Error('the panel offers another tour than the page shows');
        // The link belongs to the rehearsal agency: nothing is written for any other agency.
        if (widget.agency_name !== R.AGENCY) throw new Error('the form key belongs to another agency than the rehearsal agency');
        if (!Array.isArray(widget.departures) || !widget.departures.length) throw new Error('the panel offers no departure (tour X has none open in the booking window)');
        const panel = page.getByTestId('book-now');
        await h.scrollTo(panel, 'center');
        await h.expect(panel).toHaveAttribute('data-hydrated', 'true', { timeout: 30_000 });
        await h.expect(panel).toContainText('Book this trip');
        await h.expect(panel).toContainText(R.AGENCY);
      }),
    step('The traveller picks a departure and two adults, then asks for the price. The agency\'s live price shows.',
      'Khách chọn một ngày khởi hành và hai người lớn, rồi xem giá. Giá hiện tại của đại lý hiện ra.',
      async (page, h) => {
        const select = page.getByTestId('book-now-departure');
        // A native select: point at it and choose (a click would leave the browser's own list open on a headed take).
        await h.moveTo(select);
        await select.selectOption(widget.departures[0].departure_id);
        const adults = page.getByTestId('book-now-adults');
        await h.click(adults);
        await adults.fill('2');
        const priced = page.waitForResponse((r) => /\/price$/.test(new URL(r.url()).pathname) && r.request().method() === 'POST', { timeout: 60_000 });
        await h.click(page.getByTestId('book-now-check').getByRole('button'));
        const res = await priced;
        if (res.status() !== 200) {
          const err = await page.getByTestId('book-now-error').innerText().catch(() => '');
          throw new Error(`the price check answered ${res.status()}${err ? `: ${err}` : ''}`);
        }
        if (JSON.parse(res.request().postData() || '{}').tour !== page0.sourceId) throw new Error('the price check asked for another tour key');
        await h.expect(page.getByTestId('book-now-price')).toContainText('in total', { timeout: 15_000 });
      }, { writes: true }),
    step('They give a name and an email, and tick the box that lets the agency contact them about this booking.',
      'Khách điền tên và email, rồi đánh dấu ô cho phép đại lý liên hệ về lần đặt này.',
      async (page, h) => {
        const t = R.traveller();
        for (const [id, text] of [['book-now-name', t.name], ['book-now-email', t.email]]) {
          const f = page.getByTestId(id);
          await h.click(f);
          await f.pressSequentially(text, { delay: h.fast ? 0 : 35 });
        }
        const consent = page.getByTestId('book-now-consent');
        await h.click(consent);
        await h.expect(consent).toBeChecked();
      }),
    step('Book now sends the booking for the tour on this page, and opens the traveller\'s proposal to accept and pay.',
      'Nút Đặt ngay gửi lần đặt cho đúng tour trên trang này, rồi mở đề xuất để khách chấp nhận và thanh toán.',
      async (page, h) => {
        const booked = page.waitForResponse((r) => /\/bookings$/.test(new URL(r.url()).pathname) && r.request().method() === 'POST', { timeout: 120_000 });
        await h.click(page.getByTestId('book-now-submit').getByRole('button'));
        const res = await booked;
        const sent = JSON.parse(res.request().postData() || '{}');
        if (sent.tour !== page0.sourceId) throw new Error('the booking went out with another tour key than the page\'s own');
        const body = await res.json().catch(() => ({}));
        meta.booking = { status: res.status(), answer: body.status || body.detail || null };
        if (res.status() !== 200 || body.status !== 'created') throw new Error(`the booking answered ${res.status()} ${body.status || body.detail || ''}`.trim());
        await page.waitForURL((u) => u.pathname === '/c/p', { timeout: 60_000 });
        await h.expect(page.getByTestId('client-proposal')).toBeVisible({ timeout: 60_000 });
      }, { writes: true }),
    step('The proposal names the same tour as the page. This is the end of the scenario.',
      'Đề xuất ghi đúng tour mà trang đã hiển thị. Kết thúc kịch bản.',
      async (page, h) => {
        const proposal = page.getByTestId('client-proposal');
        await h.expect(proposal).toContainText(widget.title, { timeout: 30_000 });
        await h.hover(proposal.getByText(widget.title).first());
        if (counts.bookings !== 1) throw new Error(`${counts.bookings} booking requests in this run (exactly one expected)`);
        if (counts.price_refused || counts.bookings_refused) throw new Error('the page tried a Book now write this take does not make (aborted)');
      }),
  ],
});

/**
 * Tour X's AA page: its tour id (env UAT_REH_TRIP_PAGE, else from the agency's TripPlanner tour list) and its own
 * catalogue key from CIS (GET /v1/trip/<id>, public, the same read the page makes). Read-only GETs.
 */
async function tourPage(page) {
  let tourId = (process.env.UAT_REH_TRIP_PAGE || '').trim().toLowerCase();
  if (!tourId) {
    const r = await page.request.get(`${HOSTS.tripplanner}/api/browse?resource=tenant-tours&tenant=${R.SLUG}&limit=48`, { timeout: 30_000 });
    if (r.status() !== 200) throw new Error(`the agency's tour list answered ${r.status()}`);
    const t = R.pickTour((await r.json()).tours);
    if (!t) throw new Error('tour X is not among the agency\'s tours (set UAT_REH_TOUR_X or UAT_REH_TRIP_PAGE)');
    tourId = String(t.tour_id).toLowerCase();
  }
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(tourId)) throw new Error('the tour page id is not a tour id');
  const c = await page.request.get(`${R.CIS_API}/v1/trip/${tourId}`, { timeout: 30_000, maxRedirects: 0 });
  if (c.status() !== 200) throw new Error(`CIS answered ${c.status()} for the tour page (301 = an older version id)`);
  const trip = await c.json();
  if (!trip.source_id) throw new Error('CIS sends no catalogue key for this page (source_id): the panel would fall back to the link');
  return { tourId, sourceId: String(trip.source_id), title: trip.name };
}

module.exports = sc;
