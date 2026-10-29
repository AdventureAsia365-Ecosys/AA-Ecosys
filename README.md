# AA-Ecosys

Root workspace of the Adventure Asia ecosystem. **Multi-repo**: every app keeps its own `.git` and
deploys on its own; this root only gathers them and holds the ecosystem-wide docs, ADRs, data
standards, skills and session logs. All repos live under the GitHub org **`AdventureAsia365-Ecosys`**.
The app repos are public (S241 D-14/D-25), so security reports, inventories and account details
live here or in AA-CIS-Infra, never in an app repo. This root repo and AA-CIS-Infra are public too
since 22/10/2026, until the coding phase ends ([ADR 0014](docs/adr/0014-repo-visibility-and-github-plan.md) amendment).

**Where to start:** [`docs/README.md`](docs/README.md) — "Start here" by role (CEO, new engineer,
DevOps, CTO, CIO, PM, AI agent) and the catalog of every maintained document.

## Layout

```text
AA-Ecosys/                      (this repo, public since 22/10/2026 — ADR 0014 amendment, default branch master)
├── apps/
│   ├── AA-CIS-App/             content system of record: FastAPI api + job worker (ECS), admin console (Vercel)
│   ├── AA-TripPlanner-Web/     B2C map-first trip planner: Next.js (Vercel) + 2 Lambdas
│   ├── AA-Booking/             booking back office: FastAPI api + booking.job worker (ECS), staff admin (Vercel)
│   └── AA-Partner/             partner agencies: CRM api + web (ECS), tenant portal / Content studio (Vercel)
├── infra/
│   └── AA-CIS-Infra/           Terraform (acc2 live stack, acc3 Bedrock root), DB Migrate, schema dump
├── docs/                       ecosystem docs, ADRs, data standards, contracts, ops, sessions, audits
│   └── archive/                retired one-off pages and scripts (kept for history, not current truth)
├── skill/                      runbooks and skills shared by Kiro and Claude Code
└── .kiro/steering/             always-loaded agent rules (session workflow, language, DB schema)
```

Local folder names match the GitHub repo names exactly. On WSL the path is `~/projects/AA-Ecosys/`.

## Repos and deploy

All four apps run on **one AWS account (acc2, us-west-1)** and share one RDS instance, one schema per
owner. Dev only for now; a future prod also lives on acc2 by default (ADR 0001, S241 D-16/D-17).

| Folder | Repo | Deploy |
|---|---|---|
| `apps/AA-CIS-App` | `AdventureAsia365-Ecosys/AA-CIS-App` | ECS Fargate (`aa-cis-dev-api` + `aa-cis-dev-worker`, one image per git SHA) via `Deploy Dev`; Vercel `aa-cis-frontend` (admin). Its `portal/` is a frozen, undeployed copy since AA-979 |
| `apps/AA-TripPlanner-Web` | `AdventureAsia365-Ecosys/AA-TripPlanner-Web` | Vercel (frontend); Lambdas via `deploy-lambdas.yml` |
| `apps/AA-Booking` | `AdventureAsia365-Ecosys/AA-Booking` | ECS Fargate (`aa-booking-dev-api`, same cluster) via `Deploy Dev`; Vercel (staff admin); live `/booking/health` since S235 |
| `apps/AA-Partner` | `AdventureAsia365-Ecosys/AA-Partner` | ECS Fargate ARM64 (`aa-crm-dev-api` via `Deploy Dev`, `aa-crm-dev-web` via `Deploy Web Dev`, `aa-crm-dev-portal` (tenant Content studio) via `Deploy Portal Dev`, same cluster), all on `portal.lumiguides.it.com` since AA-979 P2b |
| `infra/AA-CIS-Infra` | `AdventureAsia365-Ecosys/AA-CIS-Infra` | `Terraform Apply Prod` (acc2 stack, manual dispatch); acc3 by a human with MFA; `DB Migrate` for every app's migrations; `DB Schema Dump` regenerates the schema reference |

Each repo's `CONTEXT.md` is the source of truth for its stack, boundaries and ownership; read it before
designing a change there.

## Ecosystem docs

- [`docs/README.md`](docs/README.md) — start here: role guides and the document catalog.
- [`docs/ecosystem-architecture.md`](docs/ecosystem-architecture.md) — accounts, diagram, schema
  roles, data contracts, identity, OIDC, Bedrock routing.
- [`docs/adr/`](docs/adr/) — ecosystem decisions (0001 target architecture, 0002 only CIS writes
  content, 0003 one durable job model, 0004 AA-Booking, 0006 identity, 0008 data platform rules, …).
- [`docs/architecture/data-standards/`](docs/architecture/data-standards/README.md) — data standards
  (Part A engineering, Part B data management, Part C operations and scaling).
- [`docs/database/schema-ownership.md`](docs/database/schema-ownership.md) — owner repo per schema,
  migration version keys, how migrations reach Dev.
- [`docs/architecture/db-schema-reference.md`](docs/architecture/db-schema-reference.md) — generated
  column-level dump of the shared RDS (do not edit by hand).
- [`docs/contracts/`](docs/contracts/README.md) — versioned JSON contracts between apps.
- [`docs/ops/`](docs/ops/) — incident response and ecosystem runbooks.
- [`docs/backlog/README.md`](docs/backlog/README.md) — the live, ordered backlog.
- [`docs/sessions/`](docs/sessions/) — session logs (Vietnamese, by convention; journals, not current truth).

## Working rules

- Each sub-folder is an independent git repo — run its git and CI from inside it.
- Language: talk to Nghiệp in Vietnamese; code, commits, PRs, Linear and technical docs in English;
  session logs and Notion memory stay Vietnamese (`.kiro/steering/language-convention.md`).
- Session start/end, Done definition, merge rules, Linear and Jira rules:
  `.kiro/steering/session-workflow.md` and the skills it points to.
