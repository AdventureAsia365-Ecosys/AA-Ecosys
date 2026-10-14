# S236 design review — completing CIS (admin/tenant), TripPlanner (trip.com reference), AA-Booking next steps

Date: 14/10/2026 · Agent: Claude Code (3 read-only inventory agents + orchestrator) · Approved by Nghiệp the same day ("duyệt toàn bộ kế hoạch").

Sources: repo state at CIS `f5f1333`, TripPlanner `6523816` (tp-009), Booking `81af463` (bk-002); ADR 0001/0004/0005; S235 blueprint and audits.

## 1. CIS — admin and tenant

**Today.** Admin A0→A4 plus T-series observability pages are complete on real data. A tenant can run the core loop end to end: T0 brand → pick tour → T2 rewrite → T7 slate → T8 angle → T9 write → My Content → publish (WordPress only). No mock data left in the portal.

**Main gap: self-operation.** Admins still need SQL/scripts; tenants cannot do anything outside the content loop.

| Priority | Admin (no SQL) | Tenant (self-serve) |
|---|---|---|
| Cheap, now | Tenant settings editor — plan, RPM, markets, channels, posts/week. Endpoints exist, UI missing (`admin/tenants/page.tsx:904-921`) → AA-766 | Facebook connect UI (`/v1/integrations/facebook*` exists) → AA-815 |
| | Buttons for segment research run, regenerate angles, stuck-run recovery (endpoints exist) | Self-unpublish (`DELETE /v1/publish-log/{id}` exists) → AA-815 |
| Needs design | Staff user management (script only today), shared with Booking staff (ADR 0004 O1) → AA-816 | Tenant users: invite, roles, key rotation; later passwordless (AA-703) → AA-813 |
| | Facts Entry, platform scope (no API/UI) → AA-814 | Tenant-scope facts: own prices/terms → AA-814 |
| | Editable Pipeline Gates thresholds (read-only today) | AA-802 silent correction, AA-668 writer panel, AA-671 marketplace |
| Later | Membership plan/price editor | Payments + plan change (Stripe), webhooks |

Content quality still decides whether CIS sells (r5: 70% "light edit or better", blog 3/8): AA-792 + AA-801 (T2 judge stability), AA-789/790, AA-787. Run a UI lane and a quality lane in parallel.

## 2. TripPlanner — reference trip.com

**Today.** One page (`/`), map-first. The trip builder is strong (routes from real AA tours, drag days, AI narration, send to advisor). Missing almost everything an OTA needs: product detail page, destination pages, list view, prices, account, SEO.

**Principle.** Do not copy trip.com wholesale — trip.com sells instant inventory, AA sells tailor-made trips via an advisor. Borrow its discovery and trust patterns; keep the map + builder as the differentiator.

| trip.com pattern | For AA | Depends on |
|---|---|---|
| Search-first home with tabs | Hero "Where / how many days / travellers" → map (WIP branch `feat/aa-674-planner-redesign`) | — |
| Results list with filters + sort | List next to pins; filters: days, intensity, month, "from" price | "from" price needs Booking |
| Product detail page (PDP) | `/tours/[slug]` SSR: gallery, highlights, day-by-day, inclusions/exclusions, "from" price, sticky "Customise / Ask an advisor" → AA-812 | `catalog.tour.v1` (AA-679), photo views |
| Destination guides | `/destinations/[country]` from CIS content + place cards — the largest SEO channel → AA-812 | CIS contract |
| Price calendar | Phase 1: "from $X/person by season" from `v_from_prices` | ADR 0005 |
| Wishlist / My Trips / share link | Share link now; My Trips via Booking OTP (O8) | Booking OTP |
| TripGenie assistant | Narration exists; finish AI Phase 0 before opening chat | AA-805 |
| Trust signals | "Designed by AA", "AI-assisted" label, cancellation policy, reviews later | — |

Order: P0 AA-805 (leg order — `sequencing` ignores `source_day_index`; search `input_type`; `/narrate` ownership + spend cap + cache) → P1 catalog contract (stop direct reads of CIS internals, ADR 0001) → PDP + destination pages + search-first home → P2 "from" price, OTP, My Trips.

## 3. AA-Booking — next

**Today.** Intake only: TripPlanner inquiry → TC-000001 + lead + staff notification. No business endpoints, auth, pricing, quotes or frontend.

Smallest slices from "inquiry" to "deposit paid":
1. Staff auth (O1): CIS issues `aud=booking` JWT + JWKS; Booking bk-003 `staff_users`; trip case list/detail API (AA-680 staff half).
2. Status machine: history, assignments, staff fills pax/dates/currency (AA-681).
3. Versions V1..Vn: V1 pre-filled from legs; free-text items until AA-679 (AA-681).
4. Minimal pricing per ADR 0005: `pricing_rules`, `fx_rates`, manual net per item, engine net ÷ (1−m), audited below-floor override (AA-810).
5. Send quote: lock FX + validity, send email — needs SES (AA-811).
6. Customer OTP: merge lead → verified customer; `/me/trips` (AA-680 customer half).
7. Customer approves → version locks → `confirmed`.
8. Deposit: invoice, payment schedule, manual payment record with evidence (AA-682 subset).
9. UI: staff screens + customer pages (needs AA-683 page list, AA-655 design system).

## 4. Cross-cutting
- `catalog.tour.v1` (AA-679) unblocks TripPlanner PDP, Booking items and ADR 0001 compliance.
- SES email (AA-811): Booking quotes + OTP, TripPlanner `notify.py` stub.
- Shared design system (AA-655) before Booking UI and PDP.

## 5. Open business questions (Nghiệp / Ms. Thư)
1. Deposit percentage and payment terms.
2. SES sender domain.
3. ADR 0005 margins confirmed by Ms. Thư?
4. Default quote validity: 7 or 14 days.
5. TripPlanner home: search-first (trip.com) or keep map-first.

## 6. Issues created (S236)
AA-810 pricing engine · AA-811 SES email · AA-812 TripPlanner PDP + destination pages · AA-813 tenant users + key rotation · AA-814 Facts Entry · AA-815 Facebook connect + self-unpublish · AA-816 staff user management.
