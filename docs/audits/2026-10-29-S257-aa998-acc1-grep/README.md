# AA-998 — acc1 grep proof across the six repos (S257, 29/10/2026)

Follow-up to [`../2026-10-28-S255-aa998-acc1-removal/`](../2026-10-28-S255-aa998-acc1-removal/README.md). S255 cut every
runtime path to acc1, destroyed the `accounts/acc1-bedrock` Terraform root (7 resources) and its state bucket, and
re-inventoried acc1 (0 ecosystem resources). AA-CIS-Infra #476 then removed the root folder from `main`. This page
proves what is left in the code and says why each remaining hit is acceptable or what still needs a change.

## Method

Read-only `git grep` on each repo's freshly fetched default branch (no working-tree files, so no local leftovers):

```bash
git -C <repo> grep -nIE '867490540162|pqnghiep-admin|acc1-legacy-default|AA-Bedrock-Invoker|acc1-bedrock' <origin default branch>
```

Repos and commits: root `master` `d011f21`, AA-CIS-App `main` `92934598`, AA-Booking `main` `b2a2124`, AA-TripPlanner-Web
`main` `c961e12`, AA-Partner `main` `1e32e7f`, AA-CIS-Infra `main` `daaa477` (and the S257 branch
`chore/AA-998-acc1-leftover-refs` `a0b3a10`).

`accounts/acc1-bedrock/` on AA-CIS-Infra `main`: `git ls-tree -r origin/main` lists **no path** under it (removed by #476).

## Result

| Repo | Lines | Files | `867490540162` | `pqnghiep-admin` | `acc1-legacy-default` | `AA-Bedrock-Invoker` | `acc1-bedrock` | Live code / config |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| root (AA-Ecosys) | 182 | 57 | 69 | 63 | 15 | 25 | 50 | none (2 stale living lines, see below) |
| AA-CIS-App | 31 | 17 | 0 | 22 | 0 | 9 | 0 | none (1 guard test that names the patterns) |
| AA-Booking | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| AA-TripPlanner-Web | 5 | 5 | 0 | 0 | 0 | 1 | 4 | none (1 stale status report) |
| AA-Partner | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| AA-CIS-Infra `main` | 64 | 29 | 23 | 9 | 0 | 8 | 34 | comments only (fixed on the S257 branch) |
| AA-CIS-Infra S257 branch | 60 | 25 | 23 | 9 | 0 | 7 | 30 | none (history comments + retired-account table) |

**No live code or configuration on any default branch reads, assumes, deploys to or routes to acc1.** Every hit is a
history record, a retired-account entry, a guard that forbids the pattern, or a stale sentence in a living doc.
Supplementary check: `BEDROCK_ACCT_FALLBACK` appears only in the CIS guard test, a TripPlanner test that asserts the
env vars are absent (`backend/tests/test_llm_gateway.py`), and an Infra comment saying it is gone.

## Hits by repo

### AA-CIS-Infra

| Where | Kind | Verdict |
|---|---|---|
| `accounts/acc3-bedrock/{main,batch,cost_explorer_reader,versions}.tf` (13 lines on `main`) | comments pointing at deleted acc1 files, "acc3-primary / acc1-fallback" design | **stale → fixed** on `chore/AA-998-acc1-leftover-refs` (comment-only, `terraform validate` green, no plan diff) |
| `CONTEXT.md` §State backend (2 lines) | how-to still named "acc1/acc3 roots" and profile `pqnghiep-admin` | **stale → fixed** on the same branch |
| `tools/docs/gen_docs.py` (1 line) | IAM page text "satellite roles in acc1 / acc3" | **stale → fixed** on the same branch; next Docs Gen run updates root `docs/generated/iam-roles.md` |
| `CONTEXT.md:42,51`, `.claude/CLAUDE.md:27` | retired-account table rows / history line | OK (record) |
| `.claude/CLAUDE.md:20-21` | says the acc1 root's "only remaining step is a human destroy" | **stale** — left for the orchestrator (lane agents do not edit CLAUDE.md) |
| `accounts/aa365/{bedrock_satellite_assume,observability,versions}.tf` | past-tense comments ("removed", "decommissioned", "does NOT touch") | OK (history) |
| `docs/implementation-notes/*` (20 files) | point-in-time notes (AA-246, AA-272, AA-397, AA-587, AA-862 …) | OK (history) |
| `db/migrations/cis/*` | mention `acc1` (not the patterns above) | OK — byte-identical copies of CIS migrations, must not diverge |

Local only (not in git): the main checkout still has `infra/AA-CIS-Infra/accounts/acc1-bedrock/.terraform/` (provider
cache from the S255 destroy, no state). Safe to delete by hand.

### AA-CIS-App

| Where | Kind | Verdict |
|---|---|---|
| `tests/unit/test_aa998_no_acc1_runtime.py` | the AA-998 guard: fails CI if runtime code names the acc1 role, profile or env var | OK (guard, keep) |
| `docs/archive/2026-05-23-handoff-session31.md`, `docs/archive/2026-08-23-handoff-aa441.md` | old handoffs with `--profile pqnghiep-admin` commands | OK (archive; account IDs already masked) |
| `docs/claude_audit/AA-351*`, `AA-418*`, `AA-510*`, `docs/claude_tasks/AA-351-01*` | past audits / briefs | OK (history) |
| `docs/implementation-notes/` AA-176, 305, 308, 345, 352, 404, 432, 441, 751, 889 | past notes | OK (history) |

### AA-TripPlanner-Web

| Where | Kind | Verdict |
|---|---|---|
| `.kiro/steering/tech.md:89`, `docs/architecture-overview.md:186` | say "the former `accounts/acc1-bedrock`" | OK (already worded as retired) |
| `.kiro/specs/tripplanner-mvp/tasks.md:119`, `docs/implementation-notes/AA-862.md:80` | MVP task list, past note | OK (history) |
| `docs/bao-cao-hien-trang-vi.md:137` | status report: "Trust cross-account Bedrock ở `accounts/acc3-bedrock` + `acc1-bedrock`" | **stale** — one-line TripPlanner docs fix (acc3 only); not in this lane |

### Root (AA-Ecosys)

| Where | Files | Verdict |
|---|---:|---|
| `docs/audits/**` (S235, S241, S243, S246, S248, S255, S256 folders) | 25 | OK (frozen audit evidence). Note: `2026-10-23-S248-cost-report/scripts/fetch_ce.sh` and `fetch_cw_bedrock.sh` call `--profile pqnghiep-admin`; they are the S248 evidence scripts, not a runbook — do not re-run them (acc1 is out of the ecosystem). |
| `docs/linear-export/**` | 21 | OK (exported closed issues) |
| `docs/sessions/**` | 3 | OK (session logs) |
| `docs/adr/0001a-retire-acc1-llm-on-acc3-only.md` | 1 | OK (the decision record) |
| `docs/onboarding.md:39`, `skill/ai-nghiep/references/aws.md` | 2 | OK — one history line / retired-account entry (source of the public-repo leak pattern, see AA-998 notes) |
| `docs/implementation-notes/AA-998.md`, `AA-896-cost-report.md` | 2 | OK (history). AA-998's "still open: folder still in Infra `main`" is updated on this branch. |
| `skill/aa-ecosys-repos/references/infra.md:7` | 1 | **stale ("thư mục còn chờ xoá") → fixed** on this branch |
| `.claude/CLAUDE.md:44` | 1 | **stale** ("thư mục root còn trong Infra, chờ xoá") — left for the orchestrator (lane agents do not edit CLAUDE.md) |

## Still to do (outside this page)

1. Orchestrator: update the two CLAUDE.md lines (root `.claude/CLAUDE.md:44`, Infra `.claude/CLAUDE.md:20-21`) to
   "root destroyed and removed (#476)".
2. TripPlanner: one-line fix in `docs/bao-cao-hien-trang-vi.md:137` (acc3 only).
3. Infra repo secret `AWS_ACCOUNT_ALIASES`: drop the acc1 entry after the next Docs Gen run no longer prints acc1.
4. Cost Explorer acc1 for 11/2026 = 0 USD on ecosystem services: check in the first session of 12/2026 (from S255).
