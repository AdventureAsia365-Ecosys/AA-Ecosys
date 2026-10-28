# ADR 0004 — AA-Booking: stack, repo layout, runtime and bootstrap on acc2

- **Status:** Accepted (14/10/2026, tech lead, S235). Proposed the same day; the open decisions O1–O9
  were answered by the tech lead on 14/10/2026 (see "Open decisions", now "Decisions on the open items").
  The health-only bootstrap is **done** (see "Bootstrap scope").
- **Scope:** AA-Ecosys (new repo AA-Booking; AA-CIS-Infra for the runtime and DB Migrate; AA-CIS-App
  and AA-TripPlanner-Web only later, for the read grants they own).
- **Implements:** ADR 0001 decisions 6–7 (placement on acc2, contracts, one IaC repo) and ADR 0002
  (only CIS writes content). Applies ADR 0003 (one durable job model) to Booking through its own
  `booking.job` table on the same runner library (O3). Answers ecosystem review §11 open question 5
  ("Does AAA follow the CIS stack?"): yes (O4).
- **Related Linear:** AA-677 (ERD v2, done), AA-678 (bootstrap), AA-679 (catalog sync), AA-680
  (identity), AA-681 (trip case), AA-682 (operations), AA-683 (UI spec), AA-751 (second repo on
  `shared.job`).
- **Update 2026-10-28** (checked against AA-Booking `CONTEXT.md`, AA-CIS-Infra and the live schema dump):
  - O1 (staff identity) is replaced by [ADR 0006](0006-ecosystem-identity.md) / [0006a](0006a-identity-phase1-amendments.md):
    Booking verifies Cognito WORKFORCE access tokens of the `booking-staff` and `breakglass` clients and takes the
    role from the `booking-*` groups. It still accepts the CIS bridge token during the transition (AA-911 P6b).
  - Decisions 4 and 8: Booking has jobs (`booking.job`, kinds `bk_*`). The worker loop runs inside the API task as
    one lifespan background task, not as a separate worker service. Deploy Dev calls the Booking deploy gate
    (`GET /booking/ops/deploy-gate`), which since AA-993 G5 blocks only on the retention kinds.
  - Decision 6: since X1 (bk-014) schema `booking` is owned by the NOLOGIN role `bk_owner`. DB Migrate signs in as
    `db_migrator` and runs each Booking file as the schema's live owner, not as `aa_cis_admin`. Latest Booking
    migration on Dev: bk-032 ([DB schema reference](../architecture/db-schema-reference.md)).
  - Decision 2: merges go through the GitHub merge queue; in the dev phase the orchestrating agent merges when CI
    is green (S241 D-13).
  - The staff admin frontend exists: Vercel project `aa-booking-admin` (AA-683).

## Context

AA-Booking (AAA) is built in-house from scratch (tech lead, 28/09 and S226). The inputs are the
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
  A new repo in the org would inherit it. (Fixed before the repo was created: Infra #95 pins the trust
  to AA-CIS-App and AA-CIS-Infra by immutable org/repo ids.)

Statements this ADR supersedes: the AAA region/accounts in `docs/architecture/ecosystem-review-2026-09.md`
§4 diagram and §7 (`accounts/aaa-{dev,stg,prod}`, ap-southeast-1), and the signed-webhook hand-off in
§6.2. Both were already overridden by ADR 0001 / review §10 (acc2, in-database outbox).

What it costs to differ from CIS: a second CI, deploy, auth and testing toolchain for a solo-run
program.

## Decisions

The items that needed an explicit answer (O1–O9) are listed in "Decisions on the open items", with
the answer the tech lead gave on 14/10/2026.

1. **Stack = the CIS stack.** Confirmed (O4).
   - Backend: Python 3.12, FastAPI, Pydantic v2, asyncpg with plain SQL repositories (no ORM in
     request paths).
   - Frontend (later, not in the bootstrap): Next.js 16 / React 19 / TypeScript with
     `@tanstack/react-query` and `@tanstack/react-table`, deployed on Vercel. It copies the CIS UI kit
     (`app/_kit`) and brand tokens until the shared design-system package (ADR 0001 decision 7,
     AA-655) is published, then switches to it.
     **Superseded S252 by [ADR 0016](0016-one-design-system-guarded-kit-copies.md):** no package; Booking vendors
     the canonical CIS kit core into `frontend/ui/core/` (full profile, `frontend/kit.lock.json`), checked byte for
     byte; AA-655 is folded into AA-994.
   - Database: PostgreSQL 15 on the shared RDS.

2. **Repo `AdventureAsia365-Ecosys/AA-Booking`, layout:**

   ```text
   backend/        FastAPI app (app/main.py, app/routers/, app/db.py, app/settings.py), tests/unit, tests/integration, Dockerfile
   migrations/     NNN_<name>.sql — owner key bk-NNN
   frontend/       placeholder until the first UI slice (staff identity O1 and customer surface O8 are decided)
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
     set out-of-band by the tech lead.
   - ECS service `aa-booking-dev-api` on the existing `aa-cis-dev-cluster`:
     - 0.25 vCPU / 0.5 GB, FARGATE base 1 + FARGATE_SPOT;
     - circuit breaker with rollback;
     - `ignore_changes = [task_definition, desired_count]`;
     - `enable_execute_command`;
     - existing private subnets and app security group;
       (amended by [ADR 0004b](0004b-per-app-security-groups.md): one security group per caller, S242);
     - `desired_count = 0` until the first image exists.
   - **Module and CIS-resource boundary.** The single allowed module edit is one new output,
     `http_listener_arn`, in `modules/alb/outputs.tf`. No other change to `modules/ecs`,
     `modules/api_gateway` or `modules/alb` resources. The Terraform plan for `booking.tf` must show
     no change to any existing CIS resource; the only new object attached to a CIS resource is the
     `/booking/*` listener rule.
   - Routing (entry point decided in O2):
     - ALB target group (port 8000, health check `/booking/health`);
     - listener rule `path-pattern /booking/*` on the ALB **HTTP** listener (the NLB → ALB hop is
       port 80; the alb module only exports `https_listener_arn` today, hence the new output);
     - entry: a separate REST API `aa-booking-dev-api` reusing the existing VPC
       link, `ANY /booking/{proxy+}` → `http://<nlb>/booking/{proxy}`, reached on its execute-api URL
       for Dev until the custom sub-domain `api-booking.lumiguides.it.com` (O2) has an ACM certificate
       that covers it and a Namecheap DNS record.
   - No worker service until Booking has a job model (decision 8).
   - Rough cost: one 0.25 vCPU / 0.5 GB Fargate task, mostly on Spot, a few USD per month. No new
     ALB, NLB or NAT.

6. **Database role and grants (ADR 0002 decision 4 in the database).**
   - Login role `booking`: rights only on schema `booking`.
   - **Role creation:** `bk-001` creates role `booking` **NOLOGIN** if it is missing, so the file is
     self-contained and idempotent. A one-off approved step then sets `LOGIN PASSWORD` to the value
     the tech lead stores in `booking/dev/database-url`. No password is ever in Git or in a migration file.
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
   - `bk-001` is a **first slice**, not the whole ERD v2 (O5; this amends AA-678's Done-when, which
     literally says "schema v2"). The applied `bk-001` holds the Foundation and Tier A rows below;
     the Tier B rows move to later `bk-NNN` files. Reason: PostgreSQL enum values cannot be removed
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

8. **Booking jobs run on its own `booking.job` table** (O3, kind prefix `bk_*`, O9).
   - ADR 0003 makes a Postgres queue + a worker the single mechanism for deferred work. Booking uses
     the same runner library (`shared/jobs/`, ADR 0003 decision 4) on a Booking-owned `booking.job`
     table, not `shared.job`.
   - Reason: the CIS Deploy Dev guard counts every `shared.job` row, so a queued Booking job would
     block CIS deploys (and a CIS wave would block Booking's). With its own table, the CIS deploy
     guard stays untouched and Booking's own deploy guard counts only `booking.job`.
   - The bootstrap has no jobs. The first Booking job (inquiry intake) brings the `booking.job`
     migration and a Booking-owned worker service (same image, `python -m worker`).
   - No in-process `asyncio.create_task` in request paths, and `inbox_events` stays the durable record
     of what was consumed.

9. **Health and readiness are separate.**
   - `/booking/health` = process liveness, with no DB call. The ALB health check uses it, so a DB
     outage or a missing grant cannot trip the ECS circuit breaker into a rollback loop.
   - `/booking/health/ready` = DB connectivity + `bk-001` present in `shared.schema_versions`. Smoke
     tests and alarms use it.

## Bootstrap scope (first slice) — done 14/10/2026

**Done (AA-678, S235):** Infra #95 (narrowed `aa-cis-dev-role` OIDC trust, Booking IAM prep, ALB
`http_listener_arn` output), Infra #96 (`booking.tf`: ECR, log group, roles, secret, task definition,
target group, `/booking/*` listener rule, ECS service, REST API `aa-booking-dev-api`; plan/apply 24 added,
0 changed) and Infra #97 (deploy-role trust pinned to the AA-Booking repo id `1418188499`). Repo
`AdventureAsia365-Ecosys/AA-Booking` created with the five required checks and branch protection.
`bk-001` applied by DB Migrate at 00:59:38Z on 14/10/2026 (registered, role `booking`, six Tier A
tables). The tech lead set the role password out-of-band; first Deploy Dev succeeded and
`/booking/health` and `/booking/health/ready` return 200 live (`db: ok`, `bk-001`).

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
7. The tech lead sets the role password and the `booking/dev/database-url` value out-of-band.
8. `deploy-dev.yml`, scale to 1, first deploy, live verify.

All eight steps were completed in this order on 14/10/2026.

## Decisions on the open items (tech lead, 14/10/2026)

| # | Decision | Answer |
|---|---|---|
| O1 | **Staff identity** | **(a) one store.** Booking staff log in through the CIS staff login (`shared.admin_users`, AA-656). `booking.staff_users` becomes a thin profile keyed by `admin_users.id` (Booking role, no password). CIS issues the JWT; Booking verifies it, preferably with an asymmetric key published as JWKS, and requires `aud=booking`. |
| O2 | **API entry** | **Custom sub-domains of `lumiguides.it.com`** (e.g. `api-booking.lumiguides.it.com`), as for CIS. The REST API execute-api URL is used until the ACM certificate covers the sub-domain. |
| O3 | **Job model** | **Own `booking.job` table** on the same runner library (decision 8). The CIS deploy guard is untouched. |
| O4 | **Stack confirmation** | **Confirmed:** FastAPI + asyncpg backend, Next.js on Vercel (decision 1). |
| O5 | **`bk-001` scope** | **First slice** (decision 7). Applied 14/10/2026; live `/booking/health/ready`. |
| O6 | Guest inquiries | **Guests must give name + email (phone optional) + consent; no registration.** Contract `inquiry.submitted` v1.1 (`docs/contracts/inquiry.submitted.v1.1.json`). Booking creates a trip case at once with a lead customer (unverified email) and merges it into the customer on OTP sign-in. Contact-less legacy hand-offs are parked in `inbox_events`. |
| O7 | Content boundary | **All customer-facing content (activities, country text) is authored in CIS** (ADR 0002). Booking keeps commercial fields only (see ADR 0005 for prices and suppliers). **Amended S236:** supply data for hotels/services is owned by Booking; CIS writes the customer-facing text and photos from it — see `0004a-supply-content-ownership.md`. |
| O8 | Customer surface | **TripPlanner is the customer front door** (discovery and inquiry). Booking's customer app = sign-in, My Trips, payments. |
| O9 | Job kind prefix | **`bk_*`.** |

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
  - a second job table and worker to operate (`booking.job`, O3), instead of one shared queue;
  - the UI kit is copied until AA-655 ships (superseded S252 by ADR 0016: guarded byte copies of the CIS kit core,
    no package);
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
- **Booking kinds in `shared.job`.** Rejected (O3): it needs the CIS deploy guard to filter by kind
  and couples the two apps' deploys; Booking uses its own `booking.job` table (decision 8).
- **Whole ERD v2 in `bk-001`.** Rejected as the default (decision 7, O5).
- **Separate database or account.** Rejected by ADR 0001.
