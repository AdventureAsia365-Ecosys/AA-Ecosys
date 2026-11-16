---
name: project-batch-run
description: Run a paid or long batch (an AI rewrite, a backfill, an import) as a recorded batch object in a ladder - a trial of about 3 items, then at most 50, then the rest - with a snapshot before each step, stop conditions, deploy freeze while it runs, correct counting and a cost report per stage. Use when re-running a pipeline over many items, starting a paid run, or reporting a run's result.
---

# project-batch-run

Parameters (in `AGENTS.md`): the batch object (where a run's expected set is recorded), the cost ledger, the snapshot
command, the job table.

## 1. Before the run

- **Quote the cost** from the measured cost per item in the ledger (never a guess) and get an explicit yes for this
  run. A blanket approval does not cover a new paid run.
- **Record the batch object**: the expected set of items, the stages, the stop conditions, the cost cap.
- **Snapshot** the data the run changes (a database snapshot or an export), so a bad run can be undone.
- Tell the deploy gate a run is open: no backend deploy or migration while it runs.

## 2. The ladder

| Step | Size | Go on when |
|---|---|---|
| Trial | about 3 items | every item passes the checks by hand and the cost per item matches the quote |
| Pilot | at most 50 items | failure rate and cost within the stop conditions |
| Full | the rest, in groups | each group within the stop conditions |

Never run the whole catalogue unasked; the ladder is the default.

## 3. Stop conditions (examples; set them in the batch object)

- Failure rate of a stage above its limit.
- Cost per item above the quote by more than the agreed margin, or the run total near the cap.
- A quality check of a sample fails.
- Any error that repeats on the same item more than the retry limit.

Limits are settings of the batch object, not literals in a script.

## 4. Counting

Count from the batch object's expected set and the stored results, never from log lines: done, failed (with reason),
skipped (with reason), not started. The four add up to the expected set.

## 5. Report per step

| Stage | Items | Done | Failed | Cost | Cost per item |
|---|---|---|---|---|---|

Add the run total, the running total against the cap, and the next step. Cost comes from the ledger rows of the run
(one row per call, failed calls included).

## 6. After the run

Close the batch object, lift the deploy freeze, keep the snapshot until the result is accepted, and write lessons.
