# AA-897 implementation notes (root repo: role guides, onboarding, agent index)

Scope: the guides lane of AA-897 (S243, 19/10/2026), built on the AA-887 foundation branch
(`docs/aa887-docs-standard`, templates and front-matter schema). Pages: `docs/onboarding.md` (GUIDE-01),
`docs/agents.md` (GUIDE-02), `docs/guides/ceo.md` (GUIDE-04), `devops.md` (GUIDE-05), `cto.md` (GUIDE-06),
`pm.md` (GUIDE-07), `cio.md` (GUIDE-09), `new-engineer.md` (GUIDE-10). Refs AA-897, AA-887.

## Decisions

- **`docs/onboarding.md` was written in this lane too**, although the brief put "accounts & access" and the account
  map inside `new-engineer.md`. The foundation catalog (GUIDE-01) and STYLE already point every account-ID reference at
  `onboarding.md#account-map`, so the table lives there (heading "Account map") and the new-engineer guide links to it.
  This also closes the foundation's dangling links to `onboarding.md`.
- **CEO guide format:** each section in English, then a "Tiếng Việt" block with the same content; tables are repeated
  in Vietnamese rather than made four columns wide (readable on a phone and in a PDF export). Vietnamese text uses
  `dd/mm/yyyy`; English text uses ISO dates (STYLE). Issue keys are kept out of both language blocks and collected in
  a final "Sources (for maintainers)" section.
- **Ms. Thư's access is stated as it is today**: CIS role `admin` (S242: created by Nghiệp on Platform → Staff), no
  Booking role (Nghiệp set it to None in S242). Platform pages are admin-only (`PAGE_RULES /admin/platform`), so she
  sees Apps, Audit log and Cost per app; Staff writes are owner-only.
- **Admin menu names copied from code** (`AA-CIS-App` `frontend/app/_kit/adminNav.tsx` on `origin/main`, 2026-10-19),
  including the AA-884 pages merged today (#838). The ops overview redesign (AA-858) is described as "being designed".
- **Facts checked live, read-only (2026-10-19)**: `sts get-caller-identity` (acc2), ECS services and rollout state,
  Lambda names, RDS class / backup retention / single-AZ, CloudWatch log group retention (security 365, app 30), AWS
  Budgets (total 250 USD; CIS 150, shared 50, Booking 25, TripPlanner 25), alarm count (65) and the auto-scaling
  `AlarmLow` alarms that sit in ALARM, `/health` of CIS and Booking, HTTP status of the admin, portal, Booking admin
  and TripPlanner hosts, Linear project names (read through the connector). No secret was read.
- **C4 L1/L2 in the CTO guide** are flowcharts with C4 labels (STYLE: `C4Context` is experimental), at most 15 nodes,
  marked as a summary; the maintained set stays with AA-697 (parked, N-9).
- **Links to pages other S243 lanes create** use the catalog paths: `ops/README.md` (AA-892, linked from the DevOps
  guide as the brief asked). Other planned pages (`docs/security/baseline.md`, `secrets-register.md`,
  `docs/ops/finops.md`, `docs/ops/feature-flags.md`, `docs/legal/register.md`) are named in code spans, not linked,
  so this PR does not add more dangling links.
- **Statuses:** every page `status: draft` (written from scratch by an agent, STYLE) with `last_reviewed: 2026-10-19`
  because the facts were checked against the live system today.
- No `docs/guides/README.md`: the "Start here" table in `docs/README.md` is the index of the role guides; a second
  index would drift.

## Changed (vs. the brief)

- Added `docs/onboarding.md` (see Decisions).
- The CEO guide covers "Booking admin" as "only if you have a Booking role" instead of a step-by-step, because her
  account has none today.
- The CIO vendor table is a working list marked as such; the register of record is AA-886 (`docs/legal/register.md`).
- GUIDE-08 `add-a-new-app.md` (also AA-897 in the catalog) is not written here; it was not in this lane's brief.

## Tradeoffs

- Role guides restate a few one-line facts (Dev = test data, retention 365/30, merge rights per D-13) because the
  role-guide template requires every guide to state them the same way; each carries its decision key so a change is
  found by search. Everything longer is a link.
- `agents.md` records "known stale points" per instruction file so AA-889 has a checklist; the cost is that the table
  must be pruned when AA-889 fixes them (the page says so).
- The CEO guide mentions the Safe Browsing review (AA-816) because she may hit the warning; it is dated and should be
  removed once Google clears the site.

## Should know

- Corrections from the S243 reconciliation applied: D-01 (Dev test data only) in every guide; D-09 retention
  365/30; merge rights per D-13 with "DM-11.5 text update pending v1.1"; no `shared.feature_flag` (flag register is a
  doc, tenant-pool flags are a security control); evidence in `docs/audits/` (DM-8.10, C7.2b, C8a); drill cadence
  DM-9.3; existing `Environment` tag; FinOps links DM-10 and reads the existing ledgers; eval by hand or dispatch
  (D-23); no `prod` environment rename now (AA-880); GitHub Team and least-privilege agent role only as triggers
  (U-25, U-53); rotation on exposure, go-live and break-glass use only; real Linear project names (Data Platform).
- The bilingual CEO guide is an exception to `language-convention.md` pending N-7.
- Merge after the AA-887 foundation PR. Then rerun the link check: the only dangling link left from this lane is
  `ops/README.md` until the AA-892 lane merges.
