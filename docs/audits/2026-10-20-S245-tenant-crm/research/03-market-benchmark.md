# CRM market benchmark for a small/mid B2B travel brand (Asia tour reseller)

> Raw research note from the S245 workflow (research lane 3), kept as returned.

Access date for every web source: 20/10/2026. This was read-only: I edited no files and wrote nothing to Linear, Notion or Jira.

**How reliable the prices are.** Only a few vendor pricing pages could be read directly: Rezdy, Bókun, TravelJoy, Travefy, Zoho (features only, no prices) and HubSpot (partial). Pipedrive returned 403 and Tourwriter returned 404. Every other price comes from third-party directories or blogs, and those often disagree. Each row below says where its price came from. Get vendor quotes before using any figure in a design or proposal.

---

## 1. Travel-specific tools

| Tool | Core CRM features (contacts / leads / pipeline / tasks / email sequences / quotes-itineraries / booking link) | Multi-tenant / white-label / embedded | Public API + webhooks for lead ingestion | Data residency / GDPR tooling | 2026 price |
|---|---|---|---|---|---|
| **Tourwriter** (itinerary-first, tour operators/DMCs) | Built-in CRM holds traveller, supplier and agent contacts. Directories list "sales pipeline management" and a website enquiry form. Itinerary → supplier booking requests → invoices in one lifecycle. Itinerary quotas per tier (25/yr Starter, 50/user Pro, unlimited Premium). Tasks and sequences: unknown. One reviewer says the CRM is basic. | WordPress itinerary plugin. White-label CRM for sub-agents: not found. | REST API that returns JSON. It is set up by Tourwriter support "with your website developer" after implementation. Only documented sync is MailChimp. No HubSpot/Salesforce connector found. Webhooks: unknown. | Unknown | Third-party: $99 / $149 / $249 per user/month (Premium sometimes quote-only or up to $299), plus about $1,199 one-time setup |
| **Travefy** (advisor/agency) | CRM suite launched Jul 2025, with forms and automations, itinerary and proposal builder, invoicing, commission tracking, email integration. Web forms post into the CRM automatically. Branded group landing pages carry an itinerary and a registration form. | Website and landing-page builder; custom domain on Premium. A separate "White Labels" page exists but its contents are not described. Agency tier has shared template and content libraries. | The Agency tier lists "CRM API access". Official API pricing (help page dated Aug 2026): Option 1 costs $250 setup plus $2,500/yr ($208/mo). Option 2, itinerary automation without seats, starts at $1,000/mo for 1,000 itineraries. Webhooks: unknown. | Unknown | Official page: Core $39/user/mo and Premium $59 (annual). Extra seats cost $20 (Core) or $39 (Premium). New-agent programme $25/mo. |
| **TravelJoy** (independent advisors) | CRM, unlimited forms, invoices, payments (card/ACH), itinerary and proposal builder (Pro), automations (Pro), group bookings, client app. Pipeline and tasks are not on the pricing page. Reviewers say team and supplier features are weak. | None found | Zapier only on the Premium tier. Zapier lists the TravelJoy app as Beta, with one confirmed trigger ("task completed") and no new-lead trigger. No public API found. | Unknown | Official page: Starter $19/mo (12 trips/yr, no team). Pro $39/mo or $32 annual. Premium has no listed price. Card fees 5% + 30¢ (Starter) or 3.5% + 30¢ (Pro). Team seats reported at $15 and assistant seats at $10 (third-party). |
| **Lemax** (multi-day operators/DMCs; Asian Trails' back office) | CRM with automatic follow-ups and lead nurturing, plus package and group itinerary costing with profitability. One user review says it lacks full CRM functionality. | Branded B2B portal (partner login, search, price, availability, book) and an "XML Out" feed to partners. That is distribution, not a white-label CRM. | SOAP web service. Lead webhooks: unknown. | Unknown | Not published. Directories repeat "$10,000/user/year" (unverified). |
| **Kaptio** (built on Salesforce) | Leads, opportunities, accounts and cases in Salesforce. No-code itinerary builder, dynamic packaging, automated lead routing, multi-currency payments. | Inherits Salesforce's portal options. Kaptio's own agent portal: not found. | Inherits the Salesforce platform API (not verified for Kaptio). | Inherits Salesforce Hyperforce region choice (not verified for Kaptio) | Capterra lists €200/user/month (Basic). Otherwise custom. A competitor (Softrip) claims a Salesforce licence is needed on top, which is unverified. Aimed at enterprise customers with an in-house Salesforce admin. |
| **Tourplan NX** (DMC/wholesaler back office) | Directories list CRM and client management. The Groups module pulls cost, price and availability from the product database. Nothing found on how the CRM itself works. | Unknown | hostConnect (booking/pax updates) and accountConnect (AR/AP). No full public docs found. Lead webhooks: unknown. | Unknown | Directories disagree: $250/user/mo, $900/user/mo, or from $1,000/mo |
| **Rezdy** (day-tour/activity booking) | No CRM on the official pricing page. Closest items are a guest manifest and automated customer notifications (Accelerate and up). | Unlimited agent, reseller and OTA connections on all plans (distribution) | Developer API and webhooks only on Expansion | Unknown | Official page: Foundation $49, Accelerate $99, Expansion $249 per month, plus a 3% online booking fee and $0.70–$1.00 per offline/agent booking. Prices exclude Australian GST. |
| **Bókun** (activity/tour booking, Tripadvisor-owned) | "Customer management" plus automated reservation emails. No CRM pipeline. | "Custom booking areas for agents" and subvendors on PLUS and up | Developer docs cover webhooks, a REST Booking API and OCTO. Zapier from PLUS. No native CRM connector; a reviewer says webhook replay is thin and integrators add polling. | Unknown | Official page: FREE (Viator-only management), START $49/mo + 1.5%, PLUS $149 + 1.25%, PREMIUM $499 + 1%. |
| **Umapped** (itinerary delivery; owned by Flight Centre) | Itinerary platform: live itinerary, messaging, Sabre and ClientBase integrations. Not a CRM. | Offered as a white-label product and as an API (sources from 2016–17) | API exists; current docs not found | Unknown | Capterra lists about CA$25/month flat. No official 2026 page found. |

**What this shows about travel tools**

- The travel tools are strong on itinerary, quote and invoice, and weak on CRM. None of them publishes lead-ingestion webhooks clearly, apart from Bókun and Rezdy, and those are booking systems rather than CRMs.
- API access is a separate paid product (Travefy) or needs a top tier (Rezdy Expansion, TravelJoy Premium for Zapier).
- None of the travel tools surveyed documents data residency or GDPR tooling publicly.
- The itinerary content itself (day plans, photos, descriptions) is always built by the agency. Tourwriter and Travefy limit or charge per itinerary.

## 2. General SMB CRMs

| Tool | Core CRM features | Multi-tenant / white-label / embedded | API + webhooks for lead ingestion | Data residency / GDPR | 2026 price per seat |
|---|---|---|---|---|---|
| **HubSpot** Free / Starter | Free (up to 2 users): contacts, deal pipelines, email tracking, forms, live chat (third-party summaries). Sequences need Sales Hub Professional; most sources agree Starter does not include them. Quotes on Starter are disputed between sources. No itinerary feature. | No white-label CRM found. Per-account only. | Webhooks API is reported as available from Free up (it is set per app). The "Send a webhook" workflow action needs Operations Hub Pro (vendor page). REST API on every tier. | Official data-centre page lists EU, Canada, Australia, US-West and US-East. New paid customers are assigned by location (third-party). GDPR mode adds lawful basis, consent on forms, GDPR delete and re-add warnings. | Official page shows "$7/mo/seat" and "$20/mo/seat" without saying which billing each applies to. Third parties say $15 annual or $20 monthly, and that $7–10 is a new-customer promotion that reverts to $20. |
| **Zoho CRM / Bigin** | Zoho CRM Free covers 3 users with 5,000 API calls/day (official page). Standard adds web-to-lead forms and cadences (sequences). Professional adds quotes/CPQ. Enterprise adds a sandbox. Bigin is pipeline-first; its web forms create a contact plus a deal in a chosen pipeline stage (third-party). | Not found for white-label. Each data centre holds only accounts registered on that domain. | REST API. Webhooks are outbound workflow actions; an older community thread says they send data out only. Inbound leads come through web forms or the API. Bigin is reached via API, Zapier or Pipedream. | Region is chosen by domain: .eu, .in, .com.au and others (official privacy FAQ). Feature availability can differ by data centre. GDPR: lawful basis plus a Data Subject Requests tab. | Third parties: CRM Standard $14, Pro $23, Enterprise $40, Ultimate $52 per user/month (annual; monthly about $20 and $35). Bigin Express $7, Premier $12, Bigin 360 $18; free for 1 user. |
| **Pipedrive** | Pipelines, leads and deals per seat (2,500 to 20,000), automations from Growth (none on Lite). No free plan, 14-day trial. | None found | Official KB: "regular webhooks are available on all plans"; webhook automation actions on Advanced and up. Webhooks v2 is the default. | Official KB lists AWS EU (Frankfurt, Dublin), Sydney, Montreal, London and US regions. Assignment is by signup location and cannot be picked self-service. Backups may sit in other regions. | Third parties: Lite $14, Growth $39, Premium $59 (some say $49), Ultimate $79 per seat/month (annual). Monthly billing $24, $49, $79, $99. |
| **Salesforce Starter / Pro Suite** | Starter: sales, service and marketing basics, up to 10 users. Pro Suite adds quoting, forecasting and more automation. Web-to-Lead exists on the platform; whether it is in Starter was not verified. | Experience Cloud Partner Community (PRM) is about $25/member/mo or $10/login at list (one source says $50). It reportedly needs Enterprise edition, so Starter and Pro cannot add it (third-party). | Third parties say API access is extra on lower tiers. Starter's API limits were not verified. | Hyperforce lets customers pick a region (US, UK, Germany, India, Japan and others; official). EU Operating Zone is a paid add-on. | Third parties: Starter $25, Pro $100 (annual contract), Enterprise $195, Unlimited $395, Unlimited+ $550 per user/month. |

**What this shows about general CRMs**

- All four have usable inbound APIs and some form of webhooks.
- HubSpot, Zoho and Salesforce have region choice and GDPR tooling. Pipedrive has EU hosting but assigns it rather than letting you choose.
- None of them understands tours, itineraries, pax or travel dates without custom fields.
- None offers a multi-tenant or white-label CRM that a platform like AA could give its tenants, except Salesforce Experience Cloud, which needs Enterprise edition and is costly.

## 3. Table stakes for a travel-agency CRM MVP (8)

Each item is drawn from what the tools above all ship. The aim is a CRM that is "faster than Gmail + WhatsApp + spreadsheet", which is the bar `docs/research/partner-crm-spec.md` §2 sets.

1. **One traveller/contact record.** Dedupe/merge, source, consent flag and timestamp, notes. Every tool has this.
2. **Inquiry capture from many channels.** An embeddable web form, an API/webhook endpoint, and source/UTM attribution. Every inquiry creates a contact and a trip/deal automatically. Travefy, TravelJoy, Bigin, HubSpot and Zoho all do form-to-record.
3. **A trip pipeline with travel stages,** for example Inquiry → Qualifying → Proposal → Booked → Pre-departure → Travelling → Completed / Lost, with a Kanban view. Pipedrive, HubSpot and Bigin are pipeline-first; the travel tools model stages loosely.
4. **Tasks, reminders, an activity timeline and owner assignment,** at least task-on-stage-change.
5. **Itinerary-based quote/proposal.** Day-by-day plan, price per person, versions, a client-facing link with accept. This is the core of Tourwriter, Travefy and TravelJoy; generic CRMs only have line-item quotes (Zoho Professional, Salesforce Pro).
6. **Email templates plus automated follow-ups** (sequences on stage or idle time). Travefy and TravelJoy Pro have automations; Zoho Standard has cadences; HubSpot puts sequences behind Pro.
7. **Deposit/invoice plus a payment link and booking status** (TravelJoy, Travefy, Tourwriter).
8. **Roles and permissions plus basic reports** (conversion by source, pipeline value, revenue), **and privacy tools** (export, delete, consent log). HubSpot and Zoho have GDPR tooling; the travel tools document none.

Can wait until after the MVP: two-way email sync, SMS/WhatsApp inbox, e-sign/waivers, a client portal or app, commission ledger, forecasting.

## 4. What AA could offer by being the content and itinerary source

Across all of the tools above, the agency has to type the itinerary and product data itself. Tourwriter caps itineraries by tier, and Travefy charges $1,000/month for 1,000 API-created itineraries. AA already holds the content and the inquiry path:

- **Leads that arrive already filled in.** Today a TripPlanner inquiry already lands in Booking with its context: `tripplanner.v_inquiry_outbox` (payload jsonb, idempotency_key) flows into `booking.trip_cases` (`inquiry_snapshot` jsonb, `trip_style`, `start_date`/`end_date`, `pax_adults`/`pax_children`, `source_system` ∈ cis/tripplanner/manual). Source: `docs/architecture/db-schema-reference.md`, dump verified 2026-10-19. For a tenant, a lead could arrive carrying:
  - which AA tour or itinerary it came from, and which tenant-published content piece (WordPress or Facebook post published through CIS) the traveller clicked;
  - the day plan, places, dates, pax and trip style.

  Day 1 of the CRM then starts at "Qualifying", not at a blank form.
- **The itinerary is the quote, ready to send.** A draft proposal is built from the CIS master tour in the tenant's own brand voice (CIS already produces per-tenant brand-voice versions; see `docs/research/2026-10-15-asian-trails-b2b-benchmark.md`). No travel CRM benchmarked supplies its own content.
- **An indicative price from real rates.** Booking's contracted net rates plus pricing rules could price that draft instantly. Live availability is "not yet" per the Asian Trails benchmark, so the price would be indicative only.
- **Interest signals for scoring and follow-up.** TripPlanner session and trip events (`tripplanner.trip_events`, `trip_drafts`) and the content the lead engaged with can trigger the next step, for example "viewed day 3 options twice → task: call".
- **Price position.** Free or bundled for tenants, against $19–$249 per seat for the travel tools or $14–$100 per seat plus custom fields for generic CRMs. This matches the "free for partners, pays for itself when they sell AA product" positioning in `docs/research/partner-crm-spec.md` §1.
- **Privacy built in.** Traveller data belongs to the tenant, and AA sees only anonymised demand (`partner-crm-spec.md` §1–2). Every benchmarked travel tool is silent on residency and GDPR, so this is a real selling point.

A cheaper route needs no CRM build: AA becomes a **lead source**. It pushes pre-filled leads (tour, itinerary link, pax, dates, consent) by webhook into the CRM a tenant already uses. HubSpot, Pipedrive and Zoho all accept leads by API, and Pipedrive and HubSpot offer webhooks on low tiers. This could come before, or instead of, a native CRM. The choice is a design decision for Nghiệp.

## 5. Things the design must account for

- **There is no tenant column on today's lead tables.** `booking.trip_cases` and `booking.customers` are AA-owned B2C tables (columns listed in `docs/architecture/db-schema-reference.md`). A tenant CRM needs tenant-scoped data. Keep the AA-817 tenant-isolation and tenant-sees-content-only constraints in mind.
- **Vietnam's Personal Data Protection Law (Law 91/2025/QH15)** took effect 01/01/2026 with cross-border transfer impact-assessment filings. Fines run up to 5% of revenue, and one source reports a five-year grace period for small enterprises. If traveller data collected in Vietnam is stored in us-west-1, this may apply. Whether it does is a question for Ms. Thư and her lawyer; I am not giving a legal conclusion.
- **Existing spec.** `docs/research/partner-crm-spec.md`, added in commit 145cfa9 (PR #97, 18/10/2026), already defines the pipeline, three intake stages, modules and privacy architecture. This benchmark should feed into it, not duplicate it.

## 6. Unknowns

- Data residency for every travel-specific tool.
- Webhook availability for Tourwriter, Travefy, TravelJoy, Lemax and Tourplan.
- Whether Kaptio adds its own portal or API on top of Salesforce.
- Whether HubSpot Starter includes quotes.
- Salesforce Starter's API and Web-to-Lead limits.
- Tourwriter's current official pricing (its pricing page returned 404).
- Pipedrive's official prices (403).
- Umapped's current product status.

## Sources (accessed 20/10/2026)

Repo: `/home/nghiep/projects/AA-Ecosys/docs/research/partner-crm-spec.md`, `/home/nghiep/projects/AA-Ecosys/docs/research/2026-10-15-asian-trails-b2b-benchmark.md`, `/home/nghiep/projects/AA-Ecosys/docs/architecture/db-schema-reference.md`.

Travel tools:
- Tourwriter: [Capterra](https://www.capterra.com/p/39473/TourWriter/), [Software Advice](https://www.softwareadvice.com/travel-agency/tourwriter-profile/), [GetApp](https://www.getapp.com/industries-software/a/tourwriter/), [Zoflowx](https://zoflowx.com/blogs/best-travel-agency-crm-software), [TravelBoost](https://travelboost.app/blog/tour-operator-itinerary-software), [Tourwriter KB CRM](https://kb.tourwriter.com/tag/crm/feed), [Tourwriter CRM page](https://itinerarybuilder.tourwriter.com/?p=2278), [Pipedrive blog](https://www.pipedrive.com/en/blog/crm-for-tourism)
- Travefy: [pricing](https://travefy.com/pricing), [API pricing](https://intercom.help/travefy/en/articles/956803-api-pricing), [CRM launch](https://travefy.com/blog-post/travefy-launches-all-new-crm-suite), [marketing tools](https://go.travefy.com/marketing-website-tools), [NTAP](https://travefy.com/plans/ntap)
- TravelJoy: [pricing](https://traveljoy.com/pricing), [JourneyFuse](https://journeyfuse.com/compare/travel-agent-software-pricing), [Tripkit](https://tripkit.com/traveljoy-reviews), [Zapier](https://zapier.com/apps/traveljoy/integrations)
- Lemax: [Software Advice](https://www.softwareadvice.com/hotel-management/lemax-profile/), [Capterra](https://www.capterra.com/p/117668/iTravel-Software/), [Sembark](https://sembark.com/blog/3-best-ezus-alternatives-for-travel-business/), [Atlas Perk](https://atlasperk.com/lemax-vs-traveltek-vs-tourplan/), [Lemax](https://lemax.net/), [Lemax dev guides](https://support.lemax.net/developer-category/guides/)
- Kaptio: [Capterra](https://www.capterra.com/p/150034/Kaptio-Travel/), [Automate.travel](https://automate.travel/compare/category/travel-crm/), [Softrip](https://www.softrip.com/resources/blog/kaptio-travel-software-alternative-what-enterprise-operators-need-instead/), [FitGap](https://us.fitgap.com/products/024622/kaptio-travel)
- Tourplan: [GetApp](https://www.getapp.com/hospitality-travel-software/a/tourplan/), [NX 2.5](https://www.tourplan.com/nx-version-new/), [Tourplan blog](https://www.tourplan.com/blog/keeping-pace-with-a-changing-travel-industry/), [Tourwriter on Tourplan](https://www.tourwriter.com/tourplan-reviews-alternatives/)
- Rezdy: [pricing](https://www.rezdy.com/pricing/), [Capterra](https://www.capterra.com/p/122690/Rezdy/)
- Bókun: [pricing](https://www.bokun.io/pricing), [developer docs](https://bokun.dev/), [webhooks](https://docs.bokun.io/en/articles/320-webhooks), [Zapier](https://zapier.com/apps/bokun/integrations/webhook)
- Umapped: [Capterra](https://www.capterra.com/p/161577/Umapped/), [Internova](https://internova.com/travel-leaders-elite-division-launches-customized-itinerary-solution-with-umapped/), [Travolution](https://www.travolution.com/news/travel-sectors/tour-operators/umapped-and-sabre-team-create-experiential-itinerary-solution/)

General CRMs:
- HubSpot: [Starter pricing](https://www.hubspot.com/pricing/crm/starter), [data centers](https://www.hubspot.com/data-centers), [GDPR playbook](https://www.hubspot.com/data-privacy/gdpr/hubspot-product-playbook), [TinyCommand](https://tinycommand.com/blogs/hubspot-pricing-explained), [Vedain](https://vedain.com/blog/hubspot-sales-hub-pricing-2026), [Hookdeck](https://hookdeck.com/webhooks/platforms/guide-to-hubspot-webhooks-features-and-best-practices.md)
- Zoho: [pricing](https://www.zoho.com/crm/zohocrm-pricing.html), [privacy FAQ](https://www.zoho.com/privacy/privacy-faq.html), [webhooks](https://help.zoho.com/portal/en/kb/crm-v2/automate-business-processes/actions/articles/crm-v2-webhooks-workflow), [DSR](https://help.zoho.com/portal/en/community/topic/gdpr-contd-introducing-data-subject-requests-and-more-gdpr-compliance-preferences-in-zoho-crm), [Spotsaas](https://www.spotsaas.com/blog/zoho-crm-pricing), [WeekCRM Bigin](https://www.weekcrm.com/pricing/bigin), [Aaxonix Bigin forms](https://aaxonix.com/resources/glossary/web-forms-zoho-bigin/)
- Pipedrive: [webhooks KB](https://support.pipedrive.com/en/article/automations-webhook-requests), [webhooks guide](https://pipedrive.readme.io/docs/guide-for-webhooks), [data security/hosting](https://support.pipedrive.com/hc/en-us/articles/206760639-How-secure-is-my-data-), [SaaSSwitcher](https://www.saasswitcher.com/blog/pipedrive-pricing), [Activepieces](https://www.activepieces.com/blog/pipedrive-pricing-plans-and-total-costs-for-2026)
- Salesforce: [Tech.co](https://tech.co/crm-software/salesforce-pricing-how-much-does-salesforce-cost), [Hyperforce](https://www.salesforce.com/hyperforce), [SaaSCRMReview](https://saascrmreview.com/salesforce-pricing/), [Redress Experience Cloud](https://redresscompliance.com/salesforce-experience-cloud-pricing-2026)

Vietnam PDPL: [EY alert](https://www.ey.com/content/dam/ey-unified-site/ey-com/en-vn/technical/tax/documents/legal-alert-july-2025-personal-data-protection-law-en.pdf), [Digital Policy Alert](https://digitalpolicyalert.org/event/36569-implementing-regulations-of-law-on-personal-data-protection-including-cross-border-data-transfer-regulation-entered-into-force), [Conventus](https://conventuslaw.com/report/vietnams-new-personal-data-protection-law-imposes-administrative-fines-up-to-5-of-annual-revenue-for-non-compliance/)
