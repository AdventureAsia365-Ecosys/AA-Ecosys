# AA-919 WM-20 — release 0 replay on Dev (S252, 26/10/2026)

Cost: **$0** (no model call; `llm_guard` installed in every step). Image: CIS `dddb7cff` (#1039, WM-18 + WM-20),
migration 287 applied before the deploy.

## Steps run

| Step | When (UTC) | Result |
|---|---|---|
| PRE replay on the old image (`b7da3d1a`) | 12:27 | `scripts/out/wm20/pre/s252.json` (bronze) |
| DB Migrate `cis/287_writing_memory_release.sql` check + apply | 13:14 / 13:16 | success |
| Deploy Dev `dddb7cff`, `/health/ready` schema 287 | 13:24 | success |
| POST replay on the new image | 13:30 | `scripts/out/wm20/post/s252.json` (bronze) |
| `release0` dry run, then `--apply --a1-v2-on-worker` | 13:40 | 4 `r0_replay` runs, A1 release 0 drafted (`evaluated`) |

`S1_WRITER_V2=on` was read from the worker task definition (the api task does not carry it; A1 rewrites run on the worker).

## Byte-for-byte gate (pre image = memory off = release-0 view)

| Writer | Inputs | Compared with pre | Byte diffs vs pre | Diffs off vs r0 | Stored hashes reproduced | Verdict |
|---|---|---|---|---|---|---|
| A1 | 25 | 25 | 0 | 0 | 25 / 25 | **pass** → release 0 `evaluated` |
| T2 | 15 | 15 | 0 | 0 | — (T2 stores none) | fail: 15 < 20 inputs |
| T9 blog | 25 | 25 | 0 | 0 | 0 / 14 | fail: no stored production hash reproduced |
| T9 social | 25 | 25 | 0 | 0 | 0 / 8 | fail: no stored production hash reproduced |

The refactor changed no prompt byte for any writer (0 diffs everywhere, 0 errors). The three fails are evidence gaps,
not prompt drift:

- **T2**: Dev has only 15 succeeded T2 rewrite jobs to replay; the gate needs 20.
- **T9**: every stored T9 piece was written before the AA-790 r6 prompt (#1035, deployed today), so none of their
  stored `writer_prompt_version` hashes can match the current prompt. One fresh piece per platform on the current
  image would give a reproducible stored hash.

## Not done in S252 and why

- **A1 release 0 approve + activate + memory on**: ADR 0010 decision 1 requires one human click (Releases panel
  `/admin/writing-memory/releases/{id}/approve`, `/activate`). Left for Nghiệp.
- **T2 / T9 release 0 and the WM-18 rollback drill** (the drill runs on a tenant writer, `t9_social`): both need
  new model output (≥ 5 more T2 rewrites, 1 T9 blog + 1 T9 social on the current prompt). The acc3 LLM budget is
  frozen for new paid runs until 01/11, so this moves to the first November session: write those pieces, re-run
  POST + `release0 --apply`, then the drill.

## Ids (Dev)

- r0 runs: A1 `72539555-147d-4740-b876-80bb8d1e6c15`, T2 `64747c0a-dc51-4a1b-b8b0-9ae58b52aac9`,
  T9 blog `a06d1f7c-d251-4bb1-9229-24860670a74c`, T9 social `1585d068-5524-4864-8752-b2ecac26089c`
- A1 platform release 0: `715d7251-6df5-4416-bd11-a4d86ebb3dd1` (status `evaluated`, `reverify = true`)

## Update 27/10/2026 — T2 / T9 completed, all four writers live, WM-18 drill passed

Nghiệp approved release 0 ("duyệt release 0", Linear AA-919 comment 33719beb) and lifted the acc3 budget hold.

1. Fresh inputs on the current image (E2E tenants only): 6 T2 rewrites (2 per tenant, all succeeded) + 1 T9 blog +
   1 T9 LinkedIn piece (both ready). Measured model cost **$0.53** (`t2t9_cost_check` post).
2. New PRE replay on the pre-refactor image `b7da3d1a` (one-off Fargate task on task definition `aa-cis-dev-api:845`,
   ADR 0010 decision 12), key `scripts/out/wm20/pre/aa919-t2t9.json`.
3. POST replay on the current image (`scripts/out/wm20/post/aa919-t2t9.json`):

| Writer | Inputs | Byte diffs vs pre | Off vs r0 | Stored hashes reproduced | Verdict |
|---|---|---|---|---|---|
| A1 | 25 | 0 | 0 | 25 / 25 | pass |
| T2 | 21 | 0 | 0 | — | pass |
| T9 blog | 25 | 0 | 0 | 1 / 15 (the fresh piece) | pass |
| T9 social | 25 | 0 | 0 | 1 / 9 (the fresh piece) | pass |

4. `release0 --approve --activate --memory-on` with `--approval-ref` = Nghiệp's decision: platform release 0 **active**
   for a1, t2, t9_blog, t9_social; `memory_enabled = true` for all four (empty releases: prompts byte-identical).
5. WM-18 rollback drill (tenant terra-family, writer t9_social, apply): tenant release 0 **active**, release 1
   **retired** by the rollback (`previous_release_id` = release 0). Drill dry run first, then apply.
