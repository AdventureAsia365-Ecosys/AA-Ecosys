# AA-910 — Booking staff admin on real Dev data, signed in (S250, 25/10/2026)

Agent-run live check of `https://booking.lumiguides.it.com` (Production, real Dev data) as the dedicated E2E Booking staff
user `e2e-booking@e2e-mail.lumiguides.it.com` (WORKFORCE, exactly `booking-admin`, read-only session — Infra #361, Booking #89,
root #241 ADR 0006a A10a). Sign-in through managed login with the email code read from the E2E mailbox; the Booking API
answered `staff/me` 200 role `admin`. Build under test: Booking #88 (layout fix) + #89.

Method: Playwright (Chromium, scrollbars on, Poppins loaded), 25 page entries (the 22 of the S249 layout check plus detail
tabs with real ids) at 1440×900 light and dark, 1280×800 light and 390×844 phone — 100 page loads. Measured: document and
`<main>` horizontal overflow, each kit table's min-content width against its frame, console errors, 4xx/5xx responses.

**Result: 100 / 100 clean** — page overflow 0, `<main>` overflow 0, console errors 0, failed requests 0 on every page and
viewport. At 1440 every table fits its frame with at least 78 px to spare (so ≥ 38 px at 1400).

| Page | Table min-content / frame at 1440 (px) | Slack |
|---|---|---|
| proposals (`/proposals`) | 1006 / 1084 | 78 |
| pricing-rules (`/pricing/rules`) | 983 / 1084 | 101 |
| suppliers (`/suppliers`) | 977 / 1084 | 107 |
| supplier-contracts (`/suppliers/SUP-000001?tab=contracts`) | 977 / 1092 | 115 |
| cases (`/cases`) | 942 / 1084 | 142 |
| services (`/services`) | 942 / 1084 | 142 |
| pricing-fx (`/pricing/rules?tab=fx`) | 941 / 1084 | 143 |
| trip-plans (`/catalog/trip-plans`) | 932 / 1084 | 152 |
| hotels (`/hotels`) | 926 / 1084 | 158 |
| hotel-drawer (`/hotels?hotel=HTL-000001`) | 926 / 1084 | 158 |
| customers (`/customers`) | 915 / 1084 | 169 |
| staff (`/staff`) | 848 / 1084 | 236 |
| b2b-desk-departures (`/b2b-desk?tab=departures`) | 833 / 1084 | 251 |
| dashboard (`/`) | 787 / 1084 | 297 |
| supplier-rates (`/suppliers/SUP-000001?tab=rates`) | 740 / 1092 | 352 |
| staff-cases (`/staff/2d8e5a2f-3722-4571-9327-177d10b74127?tab=cases`) | 669 / 1084 | 415 |
| service-rates (`/services/SVC-000002?tab=rates`) | 652 / 1092 | 440 |
| case-proposals (`/cases/TC-000008?tab=proposals`) | 617 / 1084 | 467 |
| customer-cases (`/customers/CUS-000010?tab=cases`) | 402 / 1092 | 690 |
| trip-plans-orphaned (`/catalog/trip-plans?show=orphaned`) | no kit table | – |
| b2b-desk-on-request (`/b2b-desk`) | no kit table | – |
| audit-log (`/audit-log`) | no kit table | – |
| supplier-activity (`/suppliers/SUP-000001`) | no kit table | – |
| service-activity (`/services/SVC-000002`) | no kit table | – |
| staff-activity (`/staff/2d8e5a2f-3722-4571-9327-177d10b74127?tab=activity`) | no kit table | – |

## Earlier screenshots at "1400 px" (Nghiệp, 24/10)

The screenshots in this folder named `*-1400*.png` were taken with Chrome page zoom at 150 % (zoom icon in the address bar):
the page laid out at about 930 CSS px, so the tables scrolled inside their frames. They do not show a 1400 px layout. A compact
layout for ~930 px (zoomed laptops) is a separate proposal (kit change), not part of AA-910.

Raw numbers: [result.json](result.json).
