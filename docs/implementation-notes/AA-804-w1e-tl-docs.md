# S262 lane w1e-tl-docs — tech lead decisions TL-1, TL-3 (part), TL-4, TL-15 and the AA-820 provider list (root repo)

Source: `docs/audits/2026-10-31-S262-tl-decisions/README.md` (the tech lead's rule of 31/10/2026: free and simple TL
items approved and done now), the S261 architecture review §7.2. Sibling PRs: AA-Partner (portal terms and privacy
provider list, notes `docs/implementation-notes/AA-820.md` there), AA-TripPlanner-Web (TL-24 noindex and preview line,
notes `docs/implementation-notes/TL-24.md` there), AA-CIS-Infra (`CONTEXT.md` account table).

## Decisions

- **ADR 0018 Accepted, region written down as decision 7.** The reasons are the ones the S261 review D7 gives
  (residency already settled in the readiness packet, Bedrock access proven in us-west-1, same module and no data move)
  plus latency stated honestly: from Asia neither US West region is faster, and an Asian region was not assessed. The
  costs of staying (two AZs, about 25 % dearer RDS than us-west-2) are recorded with the rule to bring a cost plan back
  before `aa-prod` is created. Second region: us-west-2 for backup copies and, only if needed, eval connections.
- **ADR 0009 and ADR 0018 amend each other**: the `aa-ai` row now reads "main Bedrock chat account" (the condition the
  S261 note set: both accepted). The root pointer lines that ADR 0009's follow-ups asked for are added to ADRs 0001,
  0001a, 0008 (decision 5) and 0008a (§6). The CIS ADR pointers stay open (CIS repo, not this lane). The S258 blueprint
  pointer waits: it belongs to ADR 0009 decision 11, still Proposed.
- **Stale "prod on acc2" text fixed everywhere it was stated as a fact**: onboarding, docs README, glossary (EN/VI),
  CIO/CTO/new-engineer/DevOps/CEO guides, engineering handbook (EN/VI: the Prod environment row, the "Do not do now" row
  and decision D-17). Leaving them would have kept the contradiction the S261 review flagged.
- **Data standards v1.9** (rule change by an accepted ADR): C7.2a (prod RDS in `aa-prod`, us-west-1), C7.2c (root
  `accounts/prod/` in `aa-prod`, `allowed_account_ids`, own state bucket and OIDC), DM-9.6, the index *Where* line and
  the Part B purpose. `last_reviewed` dates not moved (no live check was run).
- **AI Use Register v0** at `docs/architecture/ai-use-register.md`, catalog ID `APP-06-ai-register` (APP-06 = LLM
  operations), `status: draft`. Stage list: the 37 stages of the 29/10 route snapshot (`docs/generated/llm-routes.md`)
  plus `t10_adjudicate` (CIS migration 309, after the snapshot), Jev, DataForSEO, the geocoder and the CRM stub.
  Facts per column were read from CIS `shared/llm_client/role_config.py` (`SAFE_DEFAULTS`, `_VENDOR_DIRECT_STAGES`),
  `shared/cost_guard.py` and the jobs that call `load_run_budget`, TripPlanner `backend/shared/llm_gateway.py` and
  `backend/config.py`, AA-Partner `api/app/llm/gateway.py`, and the CIS eval runbook.
- **Kill switch column says the truth:** the gateway has no per-stage switch; `is_active = false` falls back to
  `SAFE_DEFAULTS` instead of stopping calls. Existing switches (connection `enabled`, hard-stop budget rows, named
  feature flags) are listed per row.
- **Stages with a route but no caller** (`s1_atom_writer`, `t10_claims`, `tp_extract`, `tp_component_embed`) are kept in
  the register and marked, so a cleanup can find them.
- **OWASP table cites only code that exists**; every gap names the ADR 0009 decision or TL item that closes it, or
  "none planned".
- **TL-4 fields are optional and real-date only.** `due` added only where a real date exists (AA-820 11/11, AA-804
  14/11, AA-1004 07/11, all already in the issue `next` text); no milestone got a `due` (none has a fixed date).
  `risks[]` on M1b, M2a, M4, M5 from the risk list the S261 review A4 names (one LLM provider, judge calibration, bus
  factor, Linear quota, AA-820 date, agent usage limits, no go-live date). Text in Vietnamese like the rest of
  `plan.json`; `owner_role` in English role names.
- **Skills in Vietnamese** like the surrounding skill text. The WIP rule says plainly that only the team-wide cap of 8
  was approved; the per-lane and per-size caps of TL-3 were not, and the existing "no agent-made per-lane cap" line
  stays.

## Changed

- `docs/backlog/tracker/index.html` renders the new fields (milestone risks and due, issue due). The artifact
  republish is the orchestrator's session-end step (tracker README).
- AA-820 in this repo: readiness packet Annex A (EN/VI) copies the new portal text (A.3 §5–§6, A.4 §3, version line,
  A.0 row "Full list of AI providers" removed); the clause draft records the update in §0 (a), Q11 and §5. The Schedule
  text and its v0.2 number are unchanged.

## Tradeoffs

- One root PR for TL-1, TL-4, TL-15 and the AA-820 root side: all docs, all from one decision record; splitting would
  only add merge order between pages that link each other.
- The register is hand-written (v0). Generating it from `llm-routes.snapshot.json` would keep the route columns fresh
  but not the purpose, gate and kill-switch columns; v1 can generate the route part once ADR 0009 stage profiles exist.

## Should know

- No code, no migration, no AWS change. The only page whose behaviour changes is the tracker artifact (after
  republish).
- `skill/aa-session/SKILL.md` has three older markdownlint findings (fenced blocks near line 127); skills are outside
  the docs lint scope, and they were not touched here.
