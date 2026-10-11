# AA-Ecosys

Root workspace of the Adventure Asia ecosystem. **Multi-repo**: every app keeps its own `.git` and
deploys on its own; this root only gathers them and holds the ecosystem-wide docs, ADRs, skills and
session logs. All repos live under the GitHub org **`AdventureAsia365-Ecosys`**.

## Layout

```
AA-Ecosys/                      (this repo — default branch master)
├── apps/
│   ├── AA-CIS-App/             content system of record: FastAPI + job worker (ECS), admin + tenant portal (Vercel)
│   └── AA-TripPlanner-Web/     B2C map-first trip planner: Next.js (Vercel) + 2 Lambdas
├── infra/
│   └── AA-CIS-Infra/           Terraform (acc2 live stack, acc1/acc3 Bedrock roots) + DB Migrate workflow
├── docs/                       ecosystem docs, ADRs, database ownership, sessions, audits, research
├── skill/                      runbooks and skills shared by Kiro and Claude Code
└── .kiro/steering/             always-loaded rules (session workflow, language, DB schema)
```

Local folder names match the GitHub repo names exactly. On WSL the path is
`~/projects/AA-Ecosys/`.

## Repos and deploy

| Folder | Repo | Deploy |
|---|---|---|
| `apps/AA-CIS-App` | `AdventureAsia365-Ecosys/AA-CIS-App` | ECS Fargate (api + worker) via `Deploy Dev`; Vercel (frontend) |
| `apps/AA-TripPlanner-Web` | `AdventureAsia365-Ecosys/AA-TripPlanner-Web` | Vercel (frontend); Lambdas via `deploy-lambdas.yml` |
| `infra/AA-CIS-Infra` | `AdventureAsia365-Ecosys/AA-CIS-Infra` | `Terraform Apply Prod` (acc2); acc1/acc3 by a human with MFA; `DB Migrate` for migrations |

Coming: **AA-Booking (AAA)** on acc2, schema `booking` — see
[`docs/tripplanner-to-aaa-handoff.md`](docs/tripplanner-to-aaa-handoff.md) and ADR 0001.

## Ecosystem docs

- [`docs/ecosystem-architecture.md`](docs/ecosystem-architecture.md) — accounts, diagram, schema
  roles, data contracts, OIDC, Bedrock routing.
- [`docs/adr/`](docs/adr/) — ecosystem decisions (0001 target architecture, 0002 only CIS writes
  content, 0003 one durable job model, …).
- [`docs/database/schema-ownership.md`](docs/database/schema-ownership.md) — owner repo per schema,
  migration version keys, how migrations reach Dev.
- [`docs/architecture/db-schema-reference.md`](docs/architecture/db-schema-reference.md) — live
  column-level dump of the shared RDS.
- [`docs/sessions/`](docs/sessions/) — session logs (Vietnamese, by convention).

## Working rules

- Each sub-folder is an independent git repo — `cd` into it to run its git and CI.
- Language: talk to Nghiệp in Vietnamese; code, commits, PRs, Linear and technical docs in English;
  session logs and Notion memory stay Vietnamese (`.kiro/steering/language-convention.md`).
- Session start/end, Done definition, Linear and Jira rules: `.kiro/steering/session-workflow.md`
  and the skills it points to.
