# AA-1038 — R5 hosting, final step: TripPlanner Vercel retirement (root docs)

Runbook `docs/ops/runbooks/tripplanner-web-ecs-cutover.md` section 4 step 5. Companion PRs of the same step:
AA-CIS-Infra (record always on the distribution), AA-CIS-App (purge default), AA-TripPlanner-Web (Vercel deploy and
Vercel-only code removed). Merge order: Infra, CIS, TripPlanner, root.

## Decisions

- **Secrets register:** every `vercel:aa-tripplanner` row and GitHub AA-TripPlanner-Web `VERCEL_TOKEN` ->
  **orphan-delete** (no consumer; the orchestrator deletes the project and the GitHub secret, then flips them to
  **deleted**). `tripplanner/dev/web` and `TP_MAPBOX_PUBLIC_TOKEN` -> **keep** (created 08/11/2026). The
  Secrets Manager rows lose their "copy: Vercel aa-tripplanner ..." consumers; their rotation says "a new deployment of
  aa-tripplanner-dev-web" instead of "update the Vercel env". The `vendor:vercel` account-token row -> **orphan-delete**:
  no ecosystem Vercel project is left, so the tokens only need revoking (tech lead).
- **`rollback-vercel.md` superseded, not deleted:** many pages link it (ops index, handbook, drills, guides). It now
  says where each former Vercel frontend rolls back (all ECS) and carries `status: superseded`,
  `superseded_by: OPS-02-ecs`. The links that named it as the TripPlanner frontend's rollback now point at
  `rollback-ecs.md`.
- **The ECS rollback helper gains `aa-tripplanner-dev-web`** (health `https://tripplanner.lumiguides.it.com/api/health`,
  field `git_sha`) with a test, so the frontend has a rollback procedure after Vercel. The game day D3 drill moves from
  Vercel Instant Rollback to this service.
- **Cut-over runbook section 4** records what each step did; section 3's DNS rollback is replaced by the ECS rollback
  (the switch and the Vercel CNAME target are gone: a Vercel CNAME with no project is a takeover risk).

## Changed

- `docs/security/secrets-register.{yaml,md}` (rows above, a change-log line).
- `docs/ops/runbooks/{tripplanner-web-ecs-cutover,rollback-vercel,rollback-ecs,rollback-tp-lambda,rollback-cis,rollback-booking}.md`,
  `docs/ops/README.md`, `docs/ops/incident-response.md`, `docs/ops/drills/{README,rollback-game-day}.md`.
- `tools/ops/` rollback helper + its test (one service added).
- Current-state docs that still said the TripPlanner frontend runs on Vercel: `README.md`, `docs/ecosystem-architecture.md`
  (table, diagram, contract row, links), `docs/guides/{devops,cto,cio,new-engineer,tripplanner-runbook(.vi)}.md`,
  `docs/engineering-handbook(.vi).md` (rollback row), `docs/README.md` (OPS-02 row), `docs/contracts/catalog.tour.lifecycle.v1.openapi.yaml`
  (secret location), `skill/aa-ship/SKILL.md` (rollback pointer).

## Tradeoffs

- Not touched: ADRs (decision records keep their wording), session logs, audits, the backlog history, generated pages
  (`docs/generated/network.md`, `env-config.md`: the Infra docs bot regenerates them after the apply) and the
  architecture diagrams (`docs/architecture/diagrams/{ecosystem,tripplanner}.py` + SVGs need the diagrams toolchain;
  follow-up).

## Should know

- Merge last (after the three app/infra PRs), then the orchestrator deletes the Vercel project `aa-tripplanner` and
  the GitHub secret `VERCEL_TOKEN` of AA-TripPlanner-Web, and flips those register rows to **deleted** at the session
  close.
