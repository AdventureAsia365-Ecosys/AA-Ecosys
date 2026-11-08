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

- **Review fixes (same lane):** the legal set and the agent skills still said TripPlanner runs on Vercel.
  Vercel left every list with a date (portal 2026-10-28, staff apps 2026-11-07 under the staff-web retirement,
  TripPlanner 2026-11-08), since no AA app is on Vercel any more: DPA Annex 3 (row removed, §4 dates filled), Annex 4,
  the DPA template, the pack outline, the compliance register (vendor row marked left, record rows 1, 2, 8), the VN
  transfer dossier (row 7 removed), the readiness packet EN + VI (live page links on `tripplanner.lumiguides.it.com`,
  question 11 closed) and onboarding (no Vercel team access). Annex A of the readiness packet quotes page text of a
  past commit and stays as quoted; the follow-up paragraph says the live TripPlanner notice now names AWS.
- **Runbook section 4 order:** the Infra PR is now step 3 and is applied before step 4 deletes the Vercel project,
  because the Infra PR also drops the `aa-tripplanner.vercel.app` URLs from the public Cognito `tripplanner` client
  (expected plan: 2 in-place changes, the record TTL and that client).

## Changed

- `docs/security/secrets-register.{yaml,md}` (rows above, a change-log line).
- `docs/ops/runbooks/{tripplanner-web-ecs-cutover,rollback-vercel,rollback-ecs,rollback-tp-lambda,rollback-cis,rollback-booking}.md`,
  `docs/ops/README.md`, `docs/ops/incident-response.md`, `docs/ops/drills/{README,rollback-game-day}.md`.
- `tools/ops/` rollback helper + its test (one service added).
- Current-state docs that still said the TripPlanner frontend runs on Vercel: `README.md`, `docs/ecosystem-architecture.md`
  (table, diagram, contract row, links), `docs/guides/{devops,cto,cio,new-engineer,tripplanner-runbook(.vi)}.md`,
  `docs/engineering-handbook(.vi).md` (rollback row), `docs/README.md` (OPS-02 row), `docs/contracts/catalog.tour.lifecycle.v1.openapi.yaml`
  (secret location), `skill/aa-ship/SKILL.md` (rollback pointer).
- Review fixes: `docs/legal/{dpa-annex-3-subprocessors,dpa-annex-4-transfers,dpa-template,dpa-pack-outline,register,vn-cross-border-transfer-dossier,readiness-packet,readiness-packet.vi}.md`,
  `docs/onboarding.md`; skills `aa-session` (snapshot: 9 ECS services incl. the staff admins and
  `aa-tripplanner-dev-web`, TripPlanner `/api/health` `git_sha` against the ECS image, no Vercel deployment step) and
  `aa-ecosys-repos` (`SKILL.md` repo table, `references/tripplanner.md`).

## Tradeoffs

- The changed skills (`aa-session`, `aa-ecosys-repos`, and `aa-ship` from the first commit) are packaged for claude.ai
  at the session close (`tools/skills/package_skills.sh --changed <session start commit>`), not in this PR.
- Not touched: ADRs (decision records keep their wording), session logs, audits, the backlog history, generated pages
  (`docs/generated/network.md`, `env-config.md`: the Infra docs bot regenerates them after the apply) and the
  architecture diagrams (`docs/architecture/diagrams/{ecosystem,tripplanner}.py` + SVGs need the diagrams toolchain;
  follow-up).

## Should know

- Merge last (after the three app/infra PRs, and after the Infra apply), then the orchestrator deletes the Vercel project `aa-tripplanner` and
  the GitHub secret `VERCEL_TOKEN` of AA-TripPlanner-Web, and flips those register rows to **deleted** at the session
  close.
