# Option B pricing — decisions for the open questions (S282, 16/11/2026)

Tech lead chose option B and asked that every pricing value be editable in admin (never hard-coded).
Defaults applied by the orchestrator (tech lead may override):

1. Custom domain add-on: ONE addon.custom_domain grants both tp.custom_domain and crm.custom_domain; still included in TripPlanner Pro and CRM Pro.
2. Seats minimum: provision raises seats to seats_min and bills seats_min (no refusal).
3. Add-on trials: every attach / approved request starts trialing for cis.billing.trial_days_default (14) days, once per tenant and product; no second trial after a cancel.
4. Trial AI share: the 50 % applies to each trialing subscription's own share (content cap, TripPlanner +10/+25), never to an override or an AA-1016 row.
5. AA-1016 row with monthly_usd empty: means "follow the plan" (unlimited only for tenant kind internal).
6. Discounts: founding 30 % and combo 10 % do not stack (better one applies); founding covers add-ons attached inside its 12-month window.
7. Booking SaaS draft: flags annual and discounted subscriptions for a manual invoice; no discount lines yet.
8. Pilot "free until go-live": pilot_ends_at may be NULL (until go-live, ended by End pilot); the max-weeks bound is a registry key.
9. TripPlanner planning-chat per-tenant cap: derived from the tenant's TripPlanner add-on AI increment (registry key stays as the platform default when no add-on increment).
10. TripPlanner AI session = a tripplanner.sessions row with at least one AI call in a UTC month, counted once per month.
11. Enterprise / internal quotas after membership_plans prices retire: NULL = no quota; contract numbers set per tenant as overrides.
12. Price PATCH stays admin-only, versioned and audited (no maker-checker until the first paying tenant, DM-11.5).
13. Price lock backfill for existing Dev subscriptions: left empty.

## Tech lead, 16/11/2026 (after the TripPlanner review) — overrides item 1 and the design's add-on items
14. NO retail (à la carte) items. TripPlanner is sold only as the two plans Hosted 49 / Pro 99 USD; the custom domain
    is a Pro feature only (no 15 USD custom-domain add-on), and there is no separately sold AI pack. Do not create
    addon.custom_domain or addon.ai_pack plans and do not build a retail add-on catalogue for them; keep the AI top-up
    as a per-tenant override only. The TripPlanner +10/+25 AI increments stay (they belong to the plans).
15. tripplanner.pro no longer carries tp.embed or tp.api (done live: Plans API, plan version 2). Embed, an open API
    and an AA sub-domain per agency are not sold and are off the roadmap: record this in the ADR 0019 amendment (S10).
