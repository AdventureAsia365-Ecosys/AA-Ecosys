# ADR 0004 — AA-Booking: stack, repo layout, runtime and bootstrap on acc2

- **Status:** Proposed (14/10/2026, S235). Accepted once Nghiệp answers the items marked
  **Open — Nghiệp** below. Until then, only the health-only bootstrap slice (see "Bootstrap scope")
  may be built, and nothing is applied to Dev before the hard preconditions are met.
- **Scope:** AA-Ecosys (new repo AA-Booking; AA-CIS-Infra for the runtime and DB Migrate; AA-CIS-App
  and AA-TripPlanner-Web only later, for the read grants they own).
- **Implements:** ADR 0001 decisions 6–7 (placement on acc2, contracts, one IaC repo) and ADR 0002
  (only CIS writes content). Defers ADR 0003 (one durable job model) for Booking until open decision
  O3 is answered. Answers ecosystem review §11 open question 5 ("Does AAA follow the CIS stack?") as a
  proposal, pending O4.
- **Related Linear:** AA-677 (ERD v2, done), AA-678 (bootstrap), AA-679 (catalog sync), AA-680
  (identity), AA-681 (trip case), AA-682 (operations), AA-683 (UI spec), AA-751 (second repo on
  `shared.job`).

## Context

AA-Booking (AAA) is built in-house from scratch (Nghiệp, 28/09 and S226). The inputs are the
Quanskill PRD (09/06/2026), the v1 ERD, the handover review (10/06/2026), about 110 Figma screens and
ERD v2 (`docs/AAA/erd-v2/`). No vendor code was delivered. ADR 0001 fixes where Booking runs: acc2,
the shared RDS, schema `booking`, provisioned by AA-CIS-Infra, with no new accounts. It does not fix
how Booking is built.

What already exists:

- **DB Migrate** (AA-CIS-Infra) accepts `booking/NNN_*.sql` and registers `bk-NNN` in
  `shared.schema_versions` (`.github/workflows/db-migrate.yml`). It connects with the CIS api task's
  `DATABASE_URL`, which is the RDS master user `aa_cis_admin` (`accounts/aa365/terraform.tfvars`,
  `db_username`; to be confirmed live before `bk-001` is applied). Every object a migration creates
  is therefore owned by `aa_cis_admin`. A file that fails rolls back in its own transaction and is
  not registered (`db/run_migration.py`).
- TripPlanner writes `inquiry.submitted` v1 into `tripplanner.outbox` and exposes
  `tripplanner.v_inquiry_outbox` (tp-008). The contract is in `docs/contracts/inquiry.submitted.v1.json`.
- CIS runs FastAPI + asyncpg on ECS behind API Gateway (REST) → VPC link → NLB → ALB, deploys through
  GitHub OIDC, and defines "done" as merge + CI + rollout COMPLETED + live verify (`aa-ship`).
- The CIS Deploy Dev workflow blocks a deploy while **any** `shared.job` row is queued or running; it
  does not filter by job kind (`apps/AA-CIS-App/.github/workflows/deploy-dev.yml`).
- The OIDC trust on `aa-cis-dev-role` matches every repo in the org
  (`repo:AdventureAsia365-Ecosys*/*:*`, `accounts/aa365/cicd.tf`), and that role has broad IAM write.
  A new repo in the org would inherit it.

Statements this ADR supersedes: the AAA region/accounts in `docs/architecture/ecosystem-review-2026-09.md`
§4 diagram and §7 (`accounts/aaa-{dev,stg,prod}`, ap-southeast-1), and the signed-webhook hand-off in
§6.2. Both were already overridden by ADR 0001 / review §10 (acc2, in-database outbox).

What it costs to differ from CIS: a second CI, deploy, auth and testing toolchain for a solo-run
program.

## Decisions (proposed)

Each item is a proposal until this ADR is Accepted. Items that need an explicit answer are marked
**Open — Nghiệp** and are listed again in "Open decisions".

1. **Stack = the CIS stack.** **Open — Nghiệp (O4: confirm).**
   - Backend: Python 3.12, FastAPI, Pydantic v2, asyncpg with plain SQL repositories (no ORM in
     request paths).
   - Frontend (later, not in the bootstrap): Next.js 16 / React 19 / TypeScript with
     `@tanstack/react-query` and `@tanstack/react-table`, deployed on Vercel. It copies the CIS UI kit
     (`app/_kit`) and brand tokens until the shared design-system package (ADR 0001 decision 7,
     AA-655) is published, then switches to it.
   - Database: PostgreSQL 15 on the shared RDS.

2. **Repo `AdventureAsia365-Ecosys/AA-Booking`, layout:**
   ```
   backend/        FastAPI app (app/main.py, app/routers/, app/db.py, app/settings.py), tests/unit, tests/integration, Dockerfile
   migrations/     NNN_<name>.sql — owner key bk-NNN
   frontend/       placeholder only until O1 (staff identity) and the customer-surface scope are answered
   docs/adr/       repo ADRs; 0001 cites this ADR
   docs/erd/       ERD v2 (moved from AA-Ecosys/docs/AAA/erd-v2)
   CONTEXT.md, README.md, .claude/CLAUDE.md   (English)
   ```
   - Trunk-based (ADR-2026-023): feature branch → PR → required CI → human merge to `main`.
   - Commits follow the program format (`feat|fix|chore|refactor|docs: …` + `Refs AA-xxx`).

3. **CI: five required checks**, mirroring CIS names so branch protection reads the same:
   - **Lint** (ruff).
   - **Security Audit** (pip-audit, failing, unlike CIS's report-only).
   - **Unit Tests**, including a migration guard: each `migrations/*.sql` is wrapped in
     `BEGIN; … COMMIT;`, registers its own `bk-NNN` with `ON CONFLICT DO NOTHING`, and creates or
     alters nothing outside schema `booking` (the `shared.schema_versions` insert is the only
     exception).
   - **Integration Tests**: Postgres 15 service with a stub `shared` schema; apply all migrations in
     order, then call `/booking/health/ready`.
   - **Docker Build Check**, with a Trivy report and an SBOM.
   - Non-required, once a frontend exists: **Frontend Build** (`next build` + eslint), later UI smoke
     on Vercel preview (AA-732 pattern).

4. **Deploy path.**
   - `deploy-dev.yml` on push to `main`.
   - GitHub OIDC → a new least-privilege role `aa-booking-dev-app-deploy`: ECR push to
     `aa-booking-dev-api` only, `ecs:RegisterTaskDefinition`/`DescribeTaskDefinition`,
     `UpdateService`/`DescribeServices` on Booking services only, and `iam:PassRole` on the two
     Booking roles only. AA-Booking never receives the broad `aa-cis-dev-role` ARN.
   - Image tag = git SHA (immutable).
   - Register a new task definition from the current one (only the image swapped), update the
     service, wait `services-stable`, and verify that the running image SHA equals the commit.
   - Smoke: `GET /booking/health` → 200 `{status, service, git_sha}` and `GET /booking/health/ready`
     → 200 `{db:"ok", schema_version:"bk-001"}`.
   - No job guard while Booking has no jobs (decision 8). When it gets jobs, its guard counts only
     Booking kinds.
   - "Done" follows `aa-ship`: merge + CI + rollout COMPLETED + live verify.

5. **Runtime, provisioned by AA-CIS-Infra** in a self-contained `accounts/aa365/booking.tf` (the
   `tripplanner.tf` pattern):
   - ECR `aa-booking-dev-api` (scan on push, keep last 10).
   - Log group `/ecs/aa-booking-dev`.
   - Own execution role (GetSecretValue on `booking/dev/*` only) and own task role. No Bedrock and no
     CIS secrets; add only when a feature needs them.
   - Secret `booking/dev/database-url`: a placeholder in Terraform with `ignore_changes`; the value is
     set out-of-band by Nghiệp.
   - ECS service `aa-booking-dev-api` on the existing `aa-cis-dev-cluster`:
     - 0.25 vCPU / 0.5 GB, FARGATE base 1 + FARGATE_SPOT;
     - circuit breaker with rollback;
     - `ignore_changes = [task_definition, desired_count]`;
     - `enable_execute_command`;
     - existing private subnets and app security group;
     - `desired_count = 0` until the first image exists.
   - **Module and CIS-resource boundary.** The single allowed module edit is one new output,
     `http_listener_arn`, in `modules/alb/outputs.tf`. No other change to `modules/ecs`,
     `modules/api_gateway` or `modules/alb` resources. The Terraform plan for `booking.tf` must show
     no change to any existing CIS resource; the only new object attached to a CIS resource is the
     `/booking/*` listener rule.
   - Routing (the entry point itself is **Open — Nghiệp, O2**):
     - ALB target group (port 8000, health check `/booking/health`);
     - listener rule `path-pattern /booking/*` on the ALB **HTTP** listener (the NLB → ALB hop is
       port 80; the alb module only exports `https_listener_arn` today, hence the new output);
     - proposed entry: a separate REST API `aa-booking-dev` reusing the existing VPC link,
       `ANY /booking/{proxy+}` → `http://<nlb>/booking/{proxy}`, reached on its execute-api URL for
       Dev. A custom domain such as `api-booking.lumiguides.it.com` needs an ACM certificate that
       covers it (unverified; the Terraform `domain_name` differs from the live CIS hostname) and a
       Namecheap DNS record.
   - No worker service until Booking has a job model (decision 8).
   - Rough cost: one 0.25 vCPU / 0.5 GB Fargate task, mostly on Spot, a few USD per month. No new
     ALB, NLB or NAT.

6. **Database role and grants (ADR 0002 decision 4 in the database).**
   - Login role `booking`: rights only on schema `booking`.
   - **Role creation:** `bk-001` creates role `booking` **NOLOGIN** if it is missing, so the file is
     self-contained and idempotent. A one-off approved step then sets `LOGIN PASSWORD` to the value
     Nghiệp stores in `booking/dev/database-url`. No password is ever in Git or in a migration file.
   - **Default privileges must name the owner.** DB Migrate runs as `aa_cis_admin`, so every
     `booking.*` object is owned by `aa_cis_admin`. `bk-001` therefore states
     `ALTER DEFAULT PRIVILEGES FOR ROLE aa_cis_admin IN SCHEMA booking GRANT … TO booking` for tables,
     sequences and functions, plus explicit grants on the objects it creates itself. A default
     privilege without `FOR ROLE` would silently bind to whatever role runs the file.
   - **Cross-owner read grants are not guarded.** Reads outside schema `booking` are granted only by
     the owner repo, in the owner's migration:
     - CIS migration (next free number): `USAGE` on `shared` + `SELECT` on `shared.v_tour_photos`,
       `shared.v_destination_photos` and `shared.destinations` (a view `shared.v_destinations` is
       preferred if CIS adds one), plus the catalog views when AA-679 defines them;
     - TripPlanner `tp-009`: `USAGE` on `tripplanner` + `SELECT` on `tripplanner.v_inquiry_outbox`.

     These migrations are applied **only after** role `booking` exists on Dev, and they do **not**
     wrap the grant in `IF EXISTS (role)`. A guarded no-op still registers its version permanently in
     `shared.schema_versions`, so the grant would never be retried (this is what tp-008 did for role
     `tripplanner`). An unguarded grant fails loudly if the role is missing, and DB Migrate does not
     register a failed file, so it can be re-run once the role exists. None of these grants is needed for the bootstrap.
   - Booking gets no `shared.job` grant (decision 8) and no `shared.llm_call_log` grant before it
     calls an LLM.

7. **Migrations.**
   - Authored in `AA-Booking/migrations/NNN_*.sql`, key `bk-NNN`.
   - A byte-identical copy goes in `AA-CIS-Infra/db/migrations/booking/NNN_*.sql`.
   - Applied to Dev by **DB Migrate** (`check` → `apply`) from `main` of AA-CIS-Infra, before any app
     code that needs it merges.
   - `docs/architecture/db-schema-reference.md` is regenerated after each structural migration.
   - `bk-001` is a **first slice**, not the whole ERD v2 (scope: **Open — Nghiệp, O5**, because
     AA-678's Done-when literally says "schema v2"). Reason: PostgreSQL enum values cannot be removed
     or renamed cheaply, and several FKs depend on contracts and decisions that do not exist yet.
     Proposed split:

     | Part | Contents | Condition |
     |---|---|---|
     | Foundation | `CREATE SCHEMA booking`; role `booking` NOLOGIN if missing; `USAGE` only on the schema (all DDL goes through `bk-NNN` run by DB Migrate; least privilege, matches AA-Booking bk-001); default privileges `FOR ROLE aa_cis_admin`; `INSERT 'bk-001'` into `shared.schema_versions` | Always. This is all `/booking/health/ready` needs |
     | Tier A | `customers`, `customer_otps`, `customer_sessions`, `media_files`, `audit_logs`, `inbox_events` (unique on `(source, contract, idempotency_key)`) | No open decision blocks them |
     | Tier B | `staff_users` + enum `staff_role` | Only if O1 (staff identity) is answered before `bk-001` is authored; otherwise `created_by`/`changed_by` stay plain `uuid` with no FK |
     | Tier B | `trip_cases` (without `trip_plan_id`), `trip_case_countries`, `trip_case_legs`, `trip_case_status_history`, `trip_case_status_transitions` + trigger rejecting illegal jumps (AA-678 harness comment), enums `trip_case_status`, `source_system` | Only if O6 (guest inquiries vs `customer_id NOT NULL`) and the building/proposal-sent status question are answered; otherwise `bk-002` |
     | Tier B | `areas`, `country_profiles` | Only if O7 (content boundary for AAA-authored country text) and the country ISO mapping are answered; otherwise `bk-002` |
     | `bk-002` | `suppliers`, `hotels`, `activities`, `trip_plans*`, `destination_profiles`, `entity_media`; `trip_cases.trip_plan_id` | After the `catalog.tour.v1` contract, the CIS catalog views and the ISO decision (AA-679) |
     | `bk-003` | `trip_case_versions*`, `trip_case_checks`, `staff_assignments`, `supplier_*`, `invoices`, `invoice_items`, `payment_schedule`, `payments`, `notifications` | With AA-681/682 |

8. **Booking has no deferred jobs in the bootstrap.** **Open — Nghiệp (O3: job model).**
   - ADR 0003 makes `shared.job` + a worker the single mechanism for deferred work. Booking does not
     adopt it yet: today the CIS Deploy Dev guard counts every `shared.job` row, so a queued Booking
     job would block CIS deploys (and a CIS wave would block Booking's).
   - Not accepted until the CIS deploy guard filters on CIS kinds: Booking kinds in `shared.job`, a
     Booking-owned worker service (same image, `python -m worker`) claiming only Booking kinds, and the
     AA-751 grant.
   - Alternative to weigh in O3: a Booking-owned `booking.job` table with the same runner library
     (`shared/jobs/`, ADR 0003 decision 4).
   - Either way: no in-process `asyncio.create_task` in request paths, and `inbox_events` stays the
     durable record of what was consumed.

9. **Health and readiness are separate.**
   - `/booking/health` = process liveness, with no DB call. The ALB health check uses it, so a DB
     outage or a missing grant cannot trip the ECS circuit breaker into a rollback loop.
   - `/booking/health/ready` = DB connectivity + `bk-001` present in `shared.schema_versions`. Smoke
     tests and alarms use it.

## Bootstrap scope (first slice)

The first deliverable is a **health-only** service: repo scaffold, 5-check CI, the `bk-001`
foundation, the Infra resources above, and `/booking/health` + `/booking/health/ready` live on Dev.
That is the bootstrap part of AA-678's Done-when.

Explicitly **out of scope** for the bootstrap:

- staff tables and any staff-facing endpoint or UI (O1);
- catalog and `trip_plans` (no `catalog.tour.v1` contract, no CIS catalog views, no country ISO
  mapping);
- guest inquiry intake and the `inbox_events` consumer (O3, O6);
- any use of `shared.job` (decision 8);
- the CIS grant migration and `tp-009`;
- the Vercel frontend and project;
- a custom domain, unless the ACM certificate already covers it (O2).

### Hard preconditions and order

1. Narrow the OIDC trust on `aa-cis-dev-role` (`accounts/aa365/cicd.tf`) to AA-CIS-App and
   AA-CIS-Infra **before** the AA-Booking repo is created, so the new repo never inherits it.
2. Agent sessions working on Booking run with a guardrail that also covers MCP write tools, not only
   Bash.
3. Apply a `BookingRoleTagging` statement (`iam:TagRole`/`UntagRole` on `role/aa-booking-dev-*`) on
   `aa-cis-dev-role` and the alb `http_listener_arn` output **before** `booking.tf` (same IAM
   propagation trap as `TripPlannerRoleTagging`).
4. Create the repo, then scaffold + CI, then branch protection on the five checks.
5. Apply `booking.tf` (`desired_count = 0`); the plan shows no change to CIS resources besides the
   listener rule.
6. `bk-001` PR + byte-identical Infra copy; DB Migrate `check`, then `apply`.
7. Nghiệp sets the role password and the `booking/dev/database-url` value out-of-band.
8. `deploy-dev.yml`, scale to 1, first deploy, live verify.

If O1, O2 and O5 are not answered, stop at "PRs open, nothing applied". Do not apply partially.

## Open decisions

| # | Decision | Options | Recommendation | Owner |
|---|---|---|---|---|
| O1 | **Staff identity** | (a) one store: Booking staff log in through the CIS staff login (`shared.admin_users`, AA-656); `booking.staff_users` becomes a thin profile keyed by `admin_users.id` (Booking role `admin`/`sales`/`content_creator`, no password). (b) Booking keeps its own `staff_users` with its own auth | (a): matches AA-680 "no separate staff user store". Needs a CIS change (email + Booking roles, or a role-mapping table) and a token-verification contract; the Figma password-reset and "Super Admin" screens must be mapped onto it | **Open — Nghiệp** |
| O2 | **API entry** | Separate REST API on the existing VPC link with `/booking/*` path routing, on the execute-api URL for Dev; or a custom domain (ACM certificate + Namecheap DNS) | Execute-api URL for Dev; custom domain once a certificate covers it | **Open — Nghiệp** |
| O3 | **Job model** | `shared.job` with Booking kinds (after the CIS guard filters by CIS kinds and AA-751 grants access); or an own `booking.job` table on the same runner library | Decide before the first Booking job (inquiry intake). Nothing in the bootstrap needs it | **Open — Nghiệp** |
| O4 | **Stack confirmation** | FastAPI + asyncpg backend, Next.js on Vercel (decision 1) | Confirm | **Open — Nghiệp** |
| O5 | **`bk-001` scope** | The first slice (decision 7), amending AA-678's Done-when "schema v2"; or the whole ERD v2 in `bk-001` | First slice | **Open — Nghiệp** |
| O6 | Guest inquiries (`customer: null` in the contract) | Park in `inbox_events` until contact data exists; or nullable `trip_cases.customer_id` | Decide before intake | Open — Nghiệp (not needed for the bootstrap) |
| O7 | Content boundary for AAA-authored activities and country text | Commercial data owned by Booking; or content authored in CIS (ADR 0002 "Revisit") | Decide before `country_profiles`/`activities` | Open — Nghiệp (not needed for the bootstrap) |
| O8 | Customer surface | Booking builds PRD §7.3 Discovery; or TripPlanner stays the discovery/inquiry front and Booking's customer app is sign-in, My Trips, My Payments | Decide before the frontend | Open — Nghiệp (not needed for the bootstrap) |
| O9 | Job kind prefix | `bk_*` vs AA-751's `aab_*` | Pick with O3 | Open — Nghiệp (not needed for the bootstrap) |

ADR 0001 is itself still "Proposed"; whether it moves to Accepted is Nghiệp's call and is not
changed by this ADR.

## Consequences

- **Positive:**
  - one toolchain;
  - CI, deploy and done-rules are copied, not invented;
  - least-privilege DB and IAM from the first commit, and no org-wide OIDC trust reaches the new repo;
  - schema ownership is enforced by the database and the migration guard;
  - cross-owner grants fail loudly instead of registering as silent no-ops;
  - Dev cost is marginal (one small Fargate task on an existing cluster, ALB and NLB).
- **Negative / cost:**
  - Booking shares the CIS ALB, NLB, VPC link and RDS, so an incident or maintenance on those affects
    both apps;
  - path-prefix routing ties Booking's public paths to `/booking/*`;
  - grants depend on CIS and TripPlanner migrations applied after the role exists, so cross-repo
    ordering must be planned;
  - no deferred work until O3 is answered, which blocks inquiry intake;
  - the UI kit is copied until AA-655 ships;
  - the `bk-001` first slice means later `ALTER`s on a young schema.

## Alternatives considered

- **Laravel/PHP**: the handover's "Spatie" permission tables suggest Quanskill's stack. Rejected: no
  code was delivered, and it would mean a second CI/deploy/auth path.
- **Lambda + HTTP API** (TripPlanner pattern). Rejected for the main API: OTP sessions, staff CRUD and
  a long-running consumer fit a container service, and CIS's ECS deploy and DB Migrate tooling already
  target ECS. It can be revisited for a stateless public read API.
- **Own ALB/NLB or own cluster.** Rejected for Dev (cost, more Terraform). Revisit for staging/prod
  isolation.
- **Host header routing on the existing ALB.** Rejected: API Gateway integrations call the NLB by DNS
  name, so the client's Host header does not reach the ALB.
- **Guarded (`IF EXISTS role`) cross-owner grants.** Rejected: a guarded no-op still registers its
  version, so the grant is silently never applied (decision 6).
- **Booking kinds in `shared.job` now.** Rejected until the CIS deploy guard filters by kind
  (decision 8).
- **Whole ERD v2 in `bk-001`.** Rejected as the default (decision 7, O5).
- **Separate database or account.** Rejected by ADR 0001.
