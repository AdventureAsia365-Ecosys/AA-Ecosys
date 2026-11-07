# AA-911 — Vercel retirement of the staff frontends (lane l4-aa911-vercel-retire, S272)

The tech lead approved the retirement on 07/11/2026. Source: root runbook `docs/ops/runbooks/staff-web-ecs-cutover.md`
section 4 steps 2-4, root ADR 0019 d23 (+ S271 amendment), root ADR 0006a A11 / A13. Sections 1-3 and step 4.1 ran
in S271 (Linear AA-911 comments).

## PRs (merge order)

1. AA-CIS-Infra `chore/aa911-apex-on-alb`: `staff_web_apex_on_alb = true`. Plan: one in-place update of
   `aws_route53_record.apex`. Apply, verify the apex 301, then remove the apex domain from the Vercel project.
2. AA-CIS-App `chore/aa911-retire-vercel` and AA-Booking `chore/aa911-retire-vercel` (independent of each other):
   `vercel-deploy.yml` and `frontend/vercel.json` deleted; post-deploy smoke + visual moved to `Deploy Admin Dev`;
   Preview client default ids emptied in both APIs; BFFs keep one client on the production host.
3. AA-CIS-Infra `chore/aa911-retire-preview-hosts` (stacked on 1, rebase after 1 merges): Preview hosts and clients,
   the `aa-booking-admin.vercel.app` callback, the switches with Vercel targets, `staff_web_dns_switch_window = false`.
4. This root PR: register, runbooks, skills, guides, ADR 0006a closing line.

## Decisions

- **Every user of the Preview hosts was moved, none left without a replacement** (the condition for the Infra PR):
  - CIS signed-in UI smoke (`ui-smoke.yml` staff job): production host only, called by `deploy-admin-dev.yml` after
    every verified deploy (it was called by `vercel-deploy.yml`).
  - CIS / Booking visual run on the deployed host (`visual.yml` job `deployed`): production host only, called by
    `deploy-admin-dev.yml`.
  - Booking public smoke: moved from `vercel-deploy.yml` job `smoke` to `deploy-admin-dev.yml` job `smoke`, still in
    the run verdict.
  - CIS Cognito E2E (`e2e-cognito.yml`): the `booking_base_url` input (production or `booking-preview.`) and the
    `BOOKING_PREVIEW_BYPASS` secret are gone; the Booking half runs on `booking.lumiguides.it.com`.
  - Playwright setup (`auth.setup.ts`): the viewer-cap live check on the Preview host is gone with the client; the API
    cap code keeps its unit tests (a client set through the env is still capped).
  - Per-PR previews (`*.vercel.app`, public smoke only): replaced by the required `Visual (next start)` check in both
    repos (ADR 0019 d23 R7), already in place before this lane.
  - Skills `aa-ui-verify` and `aa-ship`: rewritten for "Visual before merge, smoke + visual on ECS after merge".
  - AA-Partner `e2e/smoke-portal/aa911-portal-cross-site.spec.ts` uses `https://booking-preview.lumiguides.it.com` only
    as an Origin header value (a same-site sibling), never as a request target: it keeps working without the host
    (follow-up to rename it, no PR in this lane: one PR per repo per wave and nothing else changes in AA-Partner).
- **Register:** every `vercel:aa-cis-frontend` / `vercel:aa-booking-admin` row, GitHub `VERCEL_TOKEN` (AA-CIS-App,
  AA-Booking), `VERCEL_AUTOMATION_BYPASS_SECRET` (AA-CIS-App) and Secrets Manager `aa-cis/dev/admin-secret-preview`
  (the C9 Preview credential, no holder left) -> **orphan-delete**, dated 07/11/2026. They flip to **deleted** after the
  orchestrator removes them (the Vercel rows go with the project deletion).
- **Runbooks:** `rollback-vercel.md` now covers TripPlanner only; the cut-over runbook marks section 4 done step by
  step and retires the "rollback to Vercel" paths (a CNAME to a deleted Vercel project is a takeover risk);
  `legacy-login-flag.md`, `secret-rotation.md` (the admin service restart, the Cognito client secrets in the ECS task
  secrets), `break-glass.md` (applies_to), the game-day drill D3 (now on `aa-tripplanner`).

## Changed

`docs/security/secrets-register.{yaml,md}`, `docs/ops/runbooks/{staff-web-ecs-cutover,rollback-vercel,legacy-login-flag,
break-glass,secret-rotation}.md`, `docs/ops/{README,feature-flags}.md`, `docs/ops/playbooks/cognito-login.md`,
`docs/ops/drills/rollback-game-day.md`, `docs/adr/0006a-identity-phase1-amendments.md` (A5 update, A11 superseded
note, A13 closing line, consequences), `docs/ecosystem-architecture.md`, `docs/guides/{devops,new-engineer}.md`,
`docs/guides/cis-admin-runbook{,.vi}.md`, `docs/onboarding.md`, `README.md`, `skill/aa-ui-verify/SKILL.md`,
`skill/aa-ship/SKILL.md`, `skill/aa-ecosys-repos/SKILL.md` + `references/booking.md`.

## Tradeoffs

- Not edited: session logs, audits, Linear exports, `docs/generated/*` (the docs bot regenerates them), ADR texts that
  record history (ADR 0004, 0012, 0016), the backlog / tracker (the orchestrator updates them at session end).
- `applies_to: aa-cis-frontend` stays on guides that describe the CIS admin as an app (the id names the frontend, not
  the Vercel project); the break-glass and legacy-flag runbooks now name the ECS service.

## Should know

- `.claude/CLAUDE.md` (root, AA-CIS-App) still says the admins run on Vercel; agents do not edit those files: the tech
  lead updates them (follow-up).
- The AA-CIS-Infra `tools/docs/env_config_vercel.json` snapshot still lists the two projects until it is refreshed
  after their deletion.
