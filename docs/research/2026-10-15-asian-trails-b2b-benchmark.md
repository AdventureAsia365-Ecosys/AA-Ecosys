# Asian Trails — B2B benchmark (reference note)

Status: reference, first look only. Source: Jira KAN-20 ("look at IT solutions from Asian Trails", Leigh Wilson,
16/03/2026). On 01/10/2026 Leigh replied that it is "a B2B benchmark". Nghiệp's first-look comment is 10444,
from 01/10/2026. Saved in S237 (15/10/2026) so the B2B design work has something to compare against.
The facts below come from that first look. **Re-check them against Asian Trails' current public material
before quoting them in a design or to a partner.**

## What Asian Trails runs (first look, 01/10/2026)

| Area | Asian Trails | Notes |
|---|---|---|
| Agent portal | **eConnect**, launched end of 2022 | B2B agents search and book hotels, transfers, tours, multi-day tours and flights with live rates and availability. Multi-country trips are built in one place. |
| Connectivity | Direct **API** for OTAs and tour operators | Also distributed through aggregators: **TravelgateX** and **Juniper**. |
| Back office | **Lemax** | Cloud reservation system for DMCs, linked to their accounting. |
| Partner rates | Online rate sheets | Published per partner. |

Strength: live inventory and instant booking.

## Where the AA ecosystem stands (15/10/2026)

| Capability | AA today | App |
|---|---|---|
| Tour content | 892 rewritten tours across 14 countries, SEO, and a per-agency (tenant) brand-voice version | AA-CIS |
| Agency self-service | Tenant portal: catalog, brand identity, generated content, publish to WordPress and Facebook Page, API access | AA-CIS |
| Contracts and net rates | Suppliers and contracts, hotels and room types, services (car, guide, ticket, meal) with contracted net rates | AA-Booking (wave 2, Dev) |
| Sellable packages | 892 CIS tours visible in Booking; staff mark what is sellable and use it as the trip-case frame | AA-Booking |
| Pricing control | FX rates and pricing rules with two-person approval (maker cannot approve) | AA-Booking |
| Customer front door | Map-first trip planner that sends trip requests to Booking | AA-TripPlanner-Web |
| Not yet | Live availability, instant confirmation, agent-facing booking portal, OTA/aggregator API, accounting link | — |

AA's edge is content (catalog quality, SEO, per-agency voice). Asian Trails' edge is inventory and transactions.

## What to compare when B2B booking is designed

1. **Agent portal scope:** what an agent can book self-serve (hotel only, tours, multi-day, multi-country) versus
   what still goes through a trip case handled by AA staff.
2. **Rates:** live rates and availability versus contracted net rates plus markup rules; how rate sheets reach partners.
3. **Connectivity:** whether to expose a booking API, and whether to list through aggregators (TravelgateX, Juniper)
   or stay direct.
4. **Back office:** buy (a DMC system like Lemax) or keep building in AA-Booking; the accounting link (invoices and
   payment schedules are Booking wave 3).
5. **Content as a differentiator:** whether rewritten, per-agency content can travel through the same channel as
   rates, which Asian Trails does not appear to offer.

## Next step

Update KAN-20 and this note when the B2B agent pricing and booking design starts (AA-Booking). Until then the
Jira ticket stays open as a benchmark reference.
