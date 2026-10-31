# AA-788 — $0 promotion replay, chunked re-run (S261)

Status: **run 31/10/2026 02:47–03:40Z** (orchestrator, ECS exec, 8 chunks of ≤ 50 pieces, $0, no LLM call).

## Why a re-run

S260 ran `apps/AA-CIS-App/scripts/aa788/promotion_replay.py` (DAYS=60, LIMIT=400) once over ECS exec. It printed
nothing back: `ecsx: no result after 900s`, rc=3. The script is CPU-bound (it re-runs the deterministic T10 gates up
to four times per piece through `services.writing_memory.replay.PieceReplay`, with no model call). It also printed its
report only at the very end, so a timeout lost everything.

## Method (S261)

The scripts live in `.tmp-session/S261/aa-788/`:

| File | Runs where | What it does |
|---|---|---|
| `build.sh` | local | Builds `replay_chunk.py` from the pure parts of `promotion_replay.py` on CIS `origin/main` (copied as-is) plus `chunk_tail.py`. `scripts/` is not in the image, and ecsx runs a single file. |
| `replay_chunk.py` | CIS api container (ecsx) | Read-only session (`default_transaction_read_only = on`, asserted). Takes a fixed window (`AS_OF`, `DAYS`, `TOTAL`) and pages through it with a keyset cursor (`AFTER` = created_at,piece_id), so pieces written during the run do not shift the pages. It stops taking new pieces after `BUDGET_S` seconds and gives each piece a `PIECE_TIMEOUT_S` alarm; a timed-out piece counts as a replay error and does not stop the run. Each piece is printed on its own `ROW` line as soon as it is done, so the output survives a timeout. |
| `run_chunks.sh` | orchestrator | Loops `tools/ecs/ecsx.sh replay_chunk.py …` and passes `NEXT` from one chunk to the next. Saves each output to `out/chunk-NN-seenNNNN.txt`, then merges. On a failure it prints the exact resume command. |
| `merge_chunks.py` | local | Checks that every chunk used one window, that no piece appears twice and that the rows cover the whole population. Then it runs the original `summarize()` over all rows and prints `COVERAGE`, `TOTAL` and `GATES`. |

The numbers have the same meaning as the original script:

- `new_holds_by_gate`: pieces that the promoted modes (`T10_F12_SCOPE_MODE=block`, `T10_F9_BRAND_STYLE_MODE=repair`)
  would hold and the default modes would not. This is an upper bound, because a live run first gives the finding its
  sentence repair.
- `attempt1_extra_repairs_by_gate`: attempt-1 texts that pass in the default modes but are blocked first by a promoted
  check. Each one means one extra repair round. For F9_brand_style that is one extra `t9_repair` call plus one F9
  judge call.
- `new_holds_on_panel_light`: new holds on pieces whose majority panel label is `as_is` or `light`. The Done-when line
  asks for this to be empty.

Self-test (local, fake DB built from the unit-test fixtures): 7 pieces were processed in 3 chunks. Results:
`complete=true`, new holds `{"F12_scope": 4}` (expected from the fixtures), one piece after `AS_OF` excluded, the
budget stop moved forward one piece per chunk, a 5 s piece with `PIECE_TIMEOUT_S=1` was recorded as a replay error
and the run went on, and a duplicated chunk was reported as `complete=false`.

## Results

| Item | Value |
|---|---|
| Window | as of 2026-10-31T02:47:48Z, one window for all 8 chunks |
| Image | CIS `1b6e9448` (main, includes AA-788 `484e0924`) |
| Coverage | population 349, unique rows 349, duplicates 0, meta errors 0, complete = true |
| Replayed | 300 (49 had no writer input to replay), errors 0 |
| **New holds, upper bound** | **5 (1.7 % of replayed), all `F12_scope`**; `F14` 0; `F9_brand_style` 0 (style-only, never holds) |
| New holds on panel-light pieces | none (`[]`; 1 labelled light piece replayed) |
| Extra attempt-1 repairs by gate | `F9_brand_style` 1, `F12_scope` 2 (over 177 attempt-1 replays) |
| Stored context | F12 final-body findings 23 (13 not held today); F9 style attempt-1 locatable 16; F14 under-length final 8 |

Reading: promoting F12_scope / F14 / F9_brand_style to blocking would hold at most 5 of 300 replayed pieces (all
F12_scope) and add 3 repair calls on attempt 1. The pilot of 20 pieces with a real writer (paid, LLM path) and the gate
freeze until ~19/11 still apply (triage §5).

Files: `replay-summary.txt` (COVERAGE / TOTAL / GATES lines), `replay-full-run.log` (per-chunk summaries).

No piece text, tenant data or account identifiers are recorded here; the output holds only piece ids, counts and
catalogue place names.
