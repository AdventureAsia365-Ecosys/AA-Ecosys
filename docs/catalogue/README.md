---
id: ARCH-07-catalogue
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
| [`platform.yaml`](platform.yaml) | Platform decisions docs pages show as generated blocks: account roles (labels only), LLM provider order, app tags (AA-1132) |
| [`doc-map.yaml`](doc-map.yaml) | Docs ↔ code map: code globs per repo and the pages that describe them; the Docs impact check reads it (AA-1132) |
| [`doc-owners.yaml`](doc-owners.yaml) | Owners of the docs files without front-matter (agent rules, skills, steering, every repo's `CONTEXT.md`), so the freshness report covers them (AA-1132) |

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
| `name`, `name_vi`, `summary`, `summary_vi` | Plain words for the business owner, in English and Vietnamese (the Product map shows the Vietnamese pair when the viewer picks VI); no internal issue id |
| `roles` | Who uses it (staff roles, agency roles, `traveller`, `public`, `machine`) |
| `status` | `live`, `beta`, `planned` or `retired`, as the code on Dev does it today |
| `proven` | Optional, live or beta rows only: `date` (YYYY-MM-DD) and `evidence`, a pointer to the live proof that the feature works end to end: a repo file (an audit or drill record), `uat:<scenario id>` or a link to a run or pull request of the ecosystem's GitHub repos. Rows without it are live by the code, not yet by evidence; the check prints how many carry it |
| `milestone` | Planned rows only, and required there: the `docs/backlog/tracker/plan.json` milestone that holds the work, or `later`. A planned row owns no surface until it ships |
| `surface` | The pages (`page:/path`) and API route groups (`route:module`) the feature owns; `/**` covers the pages below |
| `conditions` | What must be true for the feature to work: `entitlements` (plan or add-on feature keys), `settings` (settings registry keys), `connections` (AI gateway connection keys), `secrets` (names only), `tenant_kinds` (`demo`, `pilot`, `agency`), `note` |
| `depends_on` | Features of other apps it cannot work without |
| `guide` | A published `docs/` catalog page that explains it (staff tier, so every admin can open it from the map) |
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
- a journey, `depends_on` or integration names a missing id, or a guide is not a published, staff-tier docs reader
  page (a catalog page with a front-matter id that every admin can open);
- either file holds an account ID, an ARN or an e-mail address;
- a `proven` pointer is malformed, points at nothing or sits on a row that is not live or beta; a planned row has no
  milestone of the plan, or owns a surface (AA-1118).

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

## Generated blocks and docs impact (AA-1132)

**Generated blocks.** A fact that many pages repeat (which account serves the chat models, which ECS services run) is
written once and shown as a block that [`tools/docs/gen_sections.py`](../../tools/docs/gen_sections.py) renders into
the page between two comment markers:

```markdown
<!-- gen:ecs-services -->
<!-- /gen -->
```

Blocks today: `accounts` and `llm-route-order` (from [`platform.yaml`](platform.yaml)), `ecs-services` (from the
Terraform-state inventory `docs/generated/inventory.md`), `latest-migrations` (from the live schema dump
`docs/architecture/db-schema-reference.md`), and, read from the other five repos by
[`tools/docs/repo_facts.py`](../../tools/docs/repo_facts.py): `app-versions` (release-please), `job-kinds-cis`,
`job-kinds-booking`, `job-kinds-crm`, `job-kinds-tripplanner` (the kind registries in code), `backup-days` (Infra
Terraform); `required-checks` comes from GitHub (`gh api`, read only). Every block renders from one snapshot,
`docs/generated/facts.snapshot.json`, so the check is deterministic and never calls AWS. Change a decision in
`platform.yaml` (with its ADR), run `python tools/docs/gen_sections.py --write`, commit the snapshot and the pages.
The docs lint fails a PR whose blocks differ from the snapshot or whose snapshot is behind `platform.yaml`; a snapshot
behind a collected source (the inventory, the schema dump; the other repos and GitHub when given) is a warning, fixed
by `--write` in the next docs PR. The repo facts and required checks refresh at session close, from the workspace:

```bash
python tools/docs/gen_sections.py --write --repos-root /home/nghiep/projects/AA-Ecosys --repos-ref origin/main --github
```

The nightly Catalogue run compares the repo facts with the repos' main and warns on drift. Never edit a block by hand;
write the prose around it.

**Docs impact.** [`doc-map.yaml`](doc-map.yaml) maps code globs of each repo to the pages that describe them. The
reusable workflow `.github/workflows/docs-impact.yml`, called from every app repo, runs
[`tools/docs/doc_impact.py`](../../tools/docs/doc_impact.py) on each pull request: when mapped code changed and none
of its pages did, the PR gets one sticky comment and warning annotations listing the pages to check. It never blocks
a merge (tech lead S283: warn only). Answer it with one line in the PR body: `Docs-impact: <root PR link>`,
`Docs-impact: updated-here` or `Docs-impact: none: <reason>`. Run it locally before a push:

```bash
python tools/docs/doc_impact.py check --repo AA-CIS-Infra --repo-dir infra/AA-CIS-Infra --base origin/main
# a range of merged work (session close): --base <first commit> --head origin/main
```

Add an entry when a page starts describing code; keep ids stable (hooks and lane notes cite them).

**Event-based freshness.** A page "needs review" when code its doc-map entries watch changed after the page's own last
commit. [`tools/docs/docs_freshness.py`](../../tools/docs/docs_freshness.py) computes it from git history only: the
docs bundle writes `needs_review` on each published page and a `freshness` summary into the reader manifest (Docs
sync clones the other repos blobless for their history), and the weekly Docs lint run adds the report to its summary.
Files without front-matter are registered in [`doc-owners.yaml`](doc-owners.yaml) so they get the same flag and a
calendar review date. A PR that raises `last_reviewed` should say what it checked on a `Verified:` line of its body
(docs lint warns otherwise). Warn only: nothing here blocks a merge.

**Names in backticks.** [`tools/docs/check_code_refs.py`](../../tools/docs/check_code_refs.py) checks repo paths, service
names, job kinds, settings keys, migration numbers and workflow names inside backticks against the facts (warnings),
and fails on a Terraform address after `-target=` / `-replace=` that the resource inventory does not have.
