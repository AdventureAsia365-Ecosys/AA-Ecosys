---
id: ARCH-03-catalogue
title: Product catalogue
description: What every AA app can do, how the apps link, what each link needs to work, and the guard that keeps the catalogue in step with the code.
type: reference
status: draft
owner: nghiep
audience: [owner, staff, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 30
---

# Product catalogue

One machine-readable place for what each app can do and how the apps link, including the conditions a link needs.
The admin page **Platform › Product map** in CIS (`/admin/platform/catalogue`) renders it; the Academy and the in-app
assistant read the same files.

| File | Holds |
|---|---|
| [`features.yaml`](features.yaml) | The apps, every feature (`<APP>-F<nnn>`) and the business journeys |
| [`integrations.yaml`](integrations.yaml) | Every link between two apps or to an outside provider (`INT-<nnn>`) |
| [`surface.snapshot.json`](surface.snapshot.json) | Generated: every page and API route group of each app, the settings registry keys and the plan feature keys |

The model follows the Backstage catalog format without a Backstage server: an app is a *System*, a feature is a
*Component* with the pages and API route groups it owns, an integration is an *API* with one producer
(`providesApis`) and its consumers (`consumesApis`). The integration `kind` names the DDD context-map relation:
`db_view` (published language over a read view), `http_api` (open host service), `event_outbox` (outbox, pull
consumer, inbox), `webhook` (push), `m2m` (one app drives another), `provider` (an outside vendor). Apps and links are
the C4 context and container levels of the [ecosystem architecture](../ecosystem-architecture.md).

## Feature fields

| Field | Meaning |
|---|---|
| `id` | `<APP>-F<nnn>`: `CIS`, `BK` (Booking), `CRM` (AA-Partner: CRM and Content studio), `TP` (TripPlanner), `INF` (shared platform). Never reused |
| `app`, `module` | The app and a short module name |
| `name`, `name_vi`, `summary` | Plain words for the business owner; no internal issue id |
| `roles` | Who uses it (staff roles, agency roles, `traveller`, `public`, `machine`) |
| `status` | `live`, `beta`, `planned` or `retired`, as the code on Dev does it today |
| `surface` | The pages (`page:/path`) and API route groups (`route:module`) the feature owns; `/**` covers the pages below |
| `conditions` | What must be true for the feature to work: `entitlements` (plan or add-on feature keys), `settings` (settings registry keys), `connections` (AI gateway connection keys), `secrets` (names only), `tenant_kinds` (`demo`, `pilot`, `agency`), `note` |
| `depends_on` | Features of other apps it cannot work without |
| `guide` | A `docs/` page that explains it |
| `owner` | The accountable role: `tech_lead`, `business_owner`, `content_lead`, `customer_success`, `finance`, `ai_ops` |

Evidence comes from the other direction: each UAT scenario in `tools/uat/catalogue.json` names the features it shows
(`features`), and the bundle lists those scenarios under each feature.

## Integration fields

`producer`, `consumers` (app ids or `external`), `kind`, `contracts` (files in [`docs/contracts/`](../contracts/README.md)
with the version in use), `auth`, `conditions` (same keys as a feature), `cadence`, `failure` (what users see when the
link fails), `kill_switch`, `personal_data`, `features` (the features on both sides), `owner`, `status`.

## Journeys

A journey is a business story told as steps; each step names its features and integrations, and the journey names its
UAT scenarios (`uat`, or `uat_prefix` for a whole series such as the pilot rehearsal `REH-`). That gives the trace
journey → features → integrations → contracts → UAT scenarios and recorded videos.

## The guard

`python tools/catalogue/catalogue.py check` (workflow `Catalogue`, on every pull request that touches the catalogue,
the contracts, the UAT catalogue or the tool) fails when:

- a contract file in `docs/contracts/` belongs to no integration, or an integration names a missing contract;
- a UAT scenario that is not retired names no feature, or a feature id that does not exist;
- a setting, plan feature key, AI gateway connection or secret named in a condition does not exist;
- a page or API route group in the surface snapshot maps to no feature, or a feature's surface pattern matches nothing;
- a journey, `depends_on` or integration names a missing id, or a guide page is missing;
- either file holds an account ID, an ARN or an e-mail address.

The surface snapshot is refreshed from the app repos:

```bash
python tools/catalogue/surface.py refresh --apps-root ~/projects/AA-Ecosys
python tools/catalogue/catalogue.py check
```

The workflow's nightly job checks the four public app repos out side by side and runs
`surface.py check`: a new page or router in any app that is not in the snapshot fails that run, so the snapshot (and
with it the feature mapping) cannot fall behind the code for more than a day.

## Publishing

The `Docs sync` workflow builds `catalogue.json` (`python tools/catalogue/catalogue.py bundle --out <dir>`) next to the
docs reader manifest and uploads it with the docs bundle on every merge to `master`. The CIS API serves it to the admin
page (read only, cached five minutes), so a merged catalogue change shows up within minutes with no deploy.

## Changing the catalogue

1. Add or change the rows in the YAML files (a new page or router: refresh the snapshot first, the guard lists what is
   unmapped).
2. Give every new UAT scenario its `features`.
3. Run the check locally; open a root pull request.
