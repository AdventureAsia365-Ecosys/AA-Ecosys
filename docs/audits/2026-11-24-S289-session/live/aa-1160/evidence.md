# AA-1160 planner locale and theme, lead route fallback note: live check on Dev (S289)

- When: 2026-11-23, 22:19–22:31 UTC (2026-11-24 05:19–05:31 +07). Run by an agent, headless Playwright (Node,
  `tools/uat/node_modules`, Chromium), read only.
- Deployed:
  - TripPlanner web `/api/health` `git_sha fee1447a…` (version 0.17.0), checked at 22:19 and 22:30.
  - CIS API `/health/ready`: `f0324a70…` with `schema_version` 474 at 22:19. **The service rolled to `69fb2ce9…` during
    the run**: ECS deployment `aa-cis-dev-api:1261` was created 22:21:55 and COMPLETED 22:24:53 UTC (read with
    `ecs describe-services`, read only). `69fb2ce9` is AA-CIS-App #1656 (CIS 475, migration only) on top of
    `f0324a70` (#1655, AA-1160), so the AA-1160 code is in both. The CIS checks ran 22:24–22:26 UTC.
- Sign-in (check 2): the Dev-only E2E owner (root ADR 0006a A10h), Cognito managed login with an e-mail code, as in
  `2026-11-23-S288-session/live/e2e-owner/evidence.md`. The code was read from the S3 prefix `inbound-admin/` with
  the MFA admin profile (`tools/uat/lib/mailbox.cjs`). It was never printed, logged or screenshotted, and no
  screenshot was taken on the sign-in host. Fresh browser contexts with no saved state file. Both sessions were signed
  out at the end (`/api/admin/session` 401 after).
- **Writes on Dev made by this run: none.** After sign-in every non-GET request from the browser was aborted by a
  route guard. Only Sentry telemetry POSTs were blocked; no app write was attempted. Choosing a country on a public
  planner is a view filter only (nothing is sent or stored).
- Masking: every e-mail address in the page that is not an `e2e-mail` address was masked before each CIS
  screenshot. No lead route on the pages shown has a target address.

## Check 1: public planner of an existing agency (no sign-in)

How the agencies were found: slugs from earlier audits (`pilot-rehearsal-01`, `audit-*`, `aa-tripplanner`), checked
with `GET /{slug}/plan`. Check 2's read-only scan of all 23 tenants showed that six have a planner (TripPlanner
subscription or site): `atlas-hearth`, `audit-atlas-hearth`, `audit-terra-family`, `aa-tripplanner`,
`pilot-rehearsal-01`, `e2e-lead-proof`. Two of them have a theme: `pilot-rehearsal-01` (accent `#1f6f8b`) and
`audit-terra-family` (accent `#14b8a6`).

Computed on `<body>` (`getComputedStyle`). The theme comes from `prefers-color-scheme`, emulated by Playwright. The
page sets `html[data-theme]` to match.

| Time (UTC) | Planner | Width | Scheme | HTTP | `--tp-map-fill` | `--tp-map-line` | `--tp-map-label` | `--tp-band-accent` | `--aa-accent` | `lang` | Screenshot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 22:21:34 | pilot-rehearsal-01 | 1440 | light | 202 | `#1f6f8b` | `#1a5d75` | `#14485a` | `#629aae` | `#1f6f8b` | en | `p1-pilot-rehearsal-01__1440__light.webp` |
| 22:21:49 | pilot-rehearsal-01 | 1440 | dark | 202 | `#1f6f8b` | `#1a5d75` | `#14485a` | `#41859c` | **`#e8a838`** (kit gold, see F1) | en | `p1-pilot-rehearsal-01__1440__dark.webp` |
| 22:22:01 | pilot-rehearsal-01 | 390 | light | 202 | `#1f6f8b` | `#1a5d75` | `#14485a` | `#629aae` | `#1f6f8b` | en | `p1-pilot-rehearsal-01__390__light.png` |
| 22:22:09 | pilot-rehearsal-01 | 390 | dark | 202 | `#1f6f8b` | `#1a5d75` | `#14485a` | `#41859c` | **`#e8a838`** | en | `p1-pilot-rehearsal-01__390__dark.png` |
| 22:22:21 | audit-terra-family | 1440 | light | 202 | `#14b8a6` | `#119b8b` | `#0f5f58` | `#14b8a6` | `#14b8a6` | en | `p1-audit-terra-family__1440__light.webp` |
| 22:22:32 | audit-terra-family | 1440 | dark | 202 | `#14b8a6` | `#119b8b` | `#0f5f58` | `#14b8a6` | `#14b8a6` | en | `p1-audit-terra-family__1440__dark.webp` |
| 22:22:43 | aa-tripplanner (no theme, AA baseline) | 1440 | light | 202 | unset | unset | unset | `#e8b865` | `#db9628` | en | `p1-aa-tripplanner__1440__light.webp` |

No console or page errors in any of the seven loads.

Server-rendered `<style>` of `pilot-rehearsal-01` (excerpt):
`body{--tp-map-fill:#1f6f8b;--tp-map-line:#1a5d75;--tp-map-label:#14485a;}`,
`html[data-theme=dark] body{--aa-accent-deep:#79a9b9;--aa-accent-soft:#1b3747;--aa-accent-tint:#1a2d3a;--aa-accent-border:#1c4c60;}`,
`html[data-theme=dark] body{--tp-band-accent:#41859c;}`. This block has no dark `--aa-accent`.

Map paint with a country chosen (a view filter only), 1440. Pixel counts on the map area (tolerance ±14 per channel):

| Time (UTC) | Planner | Scheme | Country | Agency `#1f6f8b` / `#1a5d75` px | AA gold `#b87a1a` / `#db9628` px | Screenshot |
|---|---|---|---|---|---|---|
| 22:29:19 | pilot-rehearsal-01 | light | Philippines | 6150 / 1541 | 0 / 0 | `p4-pilot-rehearsal-01-country__1440__light.webp` |
| 22:29:33 | pilot-rehearsal-01 | dark | Philippines | 6181 / 1559 | 0 / 0 | `p4-pilot-rehearsal-01-country__1440__dark.webp` |
| 22:28:48 | aa-tripplanner (baseline) | light | Vietnam | 0 / 0 | 596 / 10 | `p4-aa-tripplanner-country__1440__light.webp` |

Locale: all six planners render `document.documentElement.lang="en"` (22:30 UTC). **No agency on Dev has locale
`vi`**, so Vietnamese planner chrome could not be shown. The VI catalogue exists in code
(`frontend/lib/planner.messages.ts` `PLANNER = defineMessages(…)` with Vietnamese strings, AA-TripPlanner-Web main).
The implementation note says only `/{slug}/plan` passes the agency's locale (from the CIS site settings). There is
no query or route switch, so no read-only way to show VI exists. Changing an agency's locale is a write and was not
done.

## Check 2: CIS Tenant 360 lead route section (E2E owner, read only)

| Time (UTC) | Step | Result |
|---|---|---|
| 22:24:22 | Sign in as the E2E owner | landed `/admin/overview`; `GET /api/admin/session` 200 `role admin` |
| 22:24:58 | Tenant 360 of "Test Agency - Business Owner" (`c4e6a94f…`), `?tab=subscription` | `GET …/tripplanner-site/lead-route` 200: `crm_agency false`, `lead_channel none`, `has_tripplanner false`, `site false`. **The TripPlanner lead route section does not render.** By design: `Tenant360LeadRoute` returns null when the tenant has neither a TripPlanner subscription nor a site. The tenant has Content Starter and CRM Core (`crm.core` ACTIVE, 3 seats), no TripPlanner. `p3-test-agency-subscription__1440__light.png` (viewport) |
| 22:25:46–22:26:30 | Second sign-in, GET the lead route of all 23 tenants | all 200. `crm_agency` is **false for every tenant**, `lead_channel none` for every tenant |
| 22:26:01 | Tenant 360 › Subscription of `atlas-hearth` (crm.core + TripPlanner site, `crm_agency false`) | note shown (`lead-route-crm-note`): "This agency has the CRM add-on but the CRM has not shown a live agency for it lately (not set up yet, or deleted or locked in the CRM): its planner leads take the route below until the CRM agency is live." Then "Current route · NONE (THE PLANNER REFUSES THE REQUEST) · 4 d ago". `p3-lead-route-atlas-hearth__1440__light.png` |
| 22:26:02 | Same at 390 | same text; no horizontal overflow. `p3-lead-route-atlas-hearth__390__light.png` |
| 22:26 | Same section on `audit-atlas-hearth`, `audit-terra-family`, `pilot-rehearsal-01` | same note; on `aa-tripplanner` and `e2e-lead-proof` (no crm.core) no note, as designed |
| 22:26:34 | Sign out | `/api/admin/session` 401 |

The CIS label is "Current route". The "Now:" wording is the agency app's module badge (Partner). It was not part of
this CIS screen.

## Findings

- **F1 (theme, dark): a dark agency accent leaves the main dark accent on AA gold.** For `pilot-rehearsal-01`
  (accent `#1f6f8b`), the dark theme computes `--aa-accent: #e8a838` (the kit's dark gold). The "Find routes" button
  and the active "Your trip" tab underline are gold in `p1-pilot-rehearsal-01__1440__dark.webp`. The derived dark
  family (deep, soft, tint, border), the band accent and the map colours follow the agency. The cause looks like the
  rule in `lib/tenantBrand.ts`: a token that cannot reach the contrast target is left out, so the kit's gold stays.
  `#1f6f8b` is too dark to read on the dark card, and no lighter dark accent is derived for it.
  `audit-terra-family` (a light accent) is not affected. Proposed follow-up: derive a dark `--aa-accent` by
  lightening the accent until it reads, as is already done for `--tp-band-accent`.
- **F2 (CRM agency marker): `crm_agency` is false for all 23 tenants, `pilot-rehearsal-01` included.** That
  tenant's CRM agency was live in earlier sessions (S285). The CIS note says there can be up to one CRM
  entitlement reconcile pass (1 hour) after the deploy before an existing agency is marked. The deploy was recent
  (#1655), so this may only be timing. Re-read `GET …/lead-route` for `pilot-rehearsal-01` more than 1 hour after
  the `f0324a70` deploy. If it is still false, the `crm_pull` marker write path (CIS `tenant_account` snapshot read
  by the CRM M2M client) is not firing.
- **F3 (test data): the brief's tenant cannot show the section.** "Test Agency - Business Owner" has no TripPlanner
  subscription or site, so CIS hides the lead route section. The API answer is correct (`crm_agency false`). The
  note was shown on `atlas-hearth` instead, which has crm.core, a site and no live CRM agency.

## Files

- `p1-*` public planner 1440/390, light/dark; `p4-*` map with a country chosen; `p3-*` CIS Tenant 360. All PNG,
  compressed with `tools/docs/compress_images.py` (largest 452 KiB, total about 3.7 MiB).
- No browser state file was written (fresh contexts, closed at the end).
