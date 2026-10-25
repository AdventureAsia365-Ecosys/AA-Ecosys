**Fixes to the AA-919 plan (WM-17, WM-18, WM-20; WM-19 and WM-22 checked for what the schema must carry now)**

**A. Byte-identical replay can be faked (blocking)**

1. **The Dev replay compares the new builder with itself.** `release0` checks the post-PR-D builder with `memory=None` against the same builder with an empty view. That proves nothing about "today's prompt", which WM-20 scope 2 and ADR 0010 decision 12 require. Add an independent reference:
   - Before PR-D, ship a `prompt_dump` command in PR-B or PR-C, built on the pre-refactor builders.
   - Run it on Dev on that image. Store the full sha256 of (system, user) for each input id under `scripts/out/wm20/pre/`.
   - After PR-D, run release0 on the same input ids and compare three ways: the pre-refactor dump, the new code with `memory=None`, and the new code with release 0.
   - The gate is equality with the pre-refactor dump.
2. **The CI replay test has the same flaw.** `test_aa919_release0_replay` runs `release0.compare` on itself. Instead:
   - The first PR-D commit, green on `main`, commits expected hashes for all 4 × 20 fake inputs, not only a handful of pins.
   - The replay test compares the PR-D output with that committed file.
   - Use the full sha256. `prompt_version_of` is only 8 hex characters (32 bits).
3. **Capture prompts on the live call path, not by calling builders directly.**
   - Use a recorder LLM client that captures (system, user) and then raises.
   - A1: `s1_writer_v2_live.write(state, client=Recorder)`.
   - T2: patch `LLMClient` inside `graph.generate_node`.
   - T9: `generate.write_content` / `rewrite_with_feedback` with the recorder.

   Otherwise "0 diffs" can come from a hook that is never called.
4. **Add a positive control.** A test-only renderer injects a sentinel string. Assert that the sentinel appears at the exact expected byte offset in the captured prompt for each writer. Without it, "a non-empty view also renders `""`" hides missing wiring.
5. **Make the A1 stored-hash check a gate where it applies.** For `generated_content` rows with `metadata->>'writer_version'='v2'` written since the last change to `w_system_prompt` or the forbidden list, the stored `metadata.prompt_version` must equal the replayed `prompt_version_of(system)`. Today the plan reports this as informative only.

**B. Cost: everything must be $0**

6. **The rollback drill writes 1–2 real T9 pieces, which is not $0.** Replace it with a $0 drill:
   - Run the live T9 resolve (`service.start_write`'s resolve step) and `writer_input_snapshot` through the recorder client. The stamp must read `release_no` 1, then 0 after `/rollback`.
   - A paid write is optional and needs Nghiệp's explicit approval (paid-runs rule).
7. **Add a hard guard against LLM calls in `release0` and `golden_import`.** Patch `LLMClient.generate` to raise inside these processes, on top of the `llm_call_log` before/after count.
   - Forbid any context rebuild that calls an LLM: `extract_day_facts` (S1_STRUCTURED_FACTS), the T9 faq_filter / answer-fit, and the search-question fetch. Rebuild only from stored `writer_input` and deterministic `build_fact_table`.

**C. Wrong names and shapes (checked against the schema reference, code and fixture)**

8. **`shared.job` has no status `done`.** The CHECK allows queued, running, succeeded, failed, stopped_budget and cancelled. The T2 source query must use `status='succeeded'`.
9. **There is no `result.diag` in the T2 job result.** `t2_rewrite_job.run` returns `{version_id, version_status, score, qa_status, brand_loaded, **diag}`, so the diag keys sit at the top level. The stamp goes at `shared.job.result.writing_release`. Fix the stamp test and Q11.
10. **The fixture's `output_post_edit` is a boolean** (6 true: 2 t2, 2 blog, 2 LinkedIn), not text.
    - Replace the `output_post_edit jsonb` column with `post_edit bool NN DEFAULT false`. Derive the `post_edit` tier from it.
    - For `post_edit=true` items, `output` is human-edited text. It must not be used as a writer control for WM-19 rejudge. Mark these items, or exclude them from control rows.
11. **Fixture `kind` values are `s1`, `t2`, `t9`, `injection_s1`, `injection_t9`.** Write the mapping to `real` / `synthetic` explicitly.
    - `inj-t9-*` refs hold only `host_sample_id` and `tenant_slug`. The importer must take `tenant_id` from the host sample's `refs.tenant_id`, check it exists in `shared.tenants`, and refuse otherwise.
    - The t9 channel comes from `input.context.channel` (or the stratum), not a top-level field.
12. **3 S1 samples have `days` NULL.** `long_9d` must treat NULL as false. The expected 25/10 holds.
13. **`label` holds reason and evidence text (about 2 KB)**, so tag it `pii:free_text`. Tag `pipeline_verdict` the same way, and the release free-text columns `notes`, `emergency_reason`, `retired_reason`, `rejected_reason` (DM-6.1).
14. **New `prompt_eval_runs` rows must fill the existing NOT NULL columns**: `prompt_version`, `tour_count`, `regression_detected`, `triggered_by`. State what goes in each for `baseline_import`, `r0_replay` and the others.
15. **Pick one `eval_run_id` per writer.** `import_baseline` writes one run per writer per mode, but a release has a single `eval_run_id`. Write one baseline_import run per writer and put the mode on each item result, or name which run is the evidence.
16. **Grant conflict.** `eval_item_result` gets SELECT/INSERT/DELETE only, but `--create-release0` "links `release_id` back onto item results", which is an UPDATE. Guard 2 also forbids column ACLs. Either drop the back-link (the release's `eval_run_id` is enough) or grant UPDATE and drop the "immutable" claim.
17. **281 precondition: the reasoning is backwards.** Readiness uses `max(version) >= REQUIRED`, which would *mask* a missing 281. Guard 1 of 282 must assert that 281 is registered (not only 280). Guard 1 of 283 asserts 282.

**D. Trigger and state-machine gaps**

18. **The guard trigger must allow same-status UPDATEs.** Examples: `reverify` / `reverify_reasons` / `reverify_at`, `notes`, `retired_reason`, and the FK `previous_release_id ON DELETE SET NULL` cascade during erasure. As written, the transition table refuses them, and a tenant erasure would fail on the cascade.
19. **A rolled-back release can be re-activated without re-approval** (retired → active).
    - Add active → rejected for rollback, which matches the AA-918 L0 rollback, or
    - block retired → active when `retired_reason` starts with `rollback:`.
20. **Emergency release (WM-18 scope 4).** Free text is not enough. Require `emergency_reason IN ('hard_stop_1','hard_stop_2','hard_stop_3')` plus a ref to the run or signal that fired. The API must check that a hard stop is open on the currently active release.
21. **Reverify (WM-18 scope 5) cannot be manual only.** Call `reverify_scan`:
    - from the importer when it supersedes a set
    - in the same transaction as `PATCH /admin/llm-config/{stage}/route`, covering writer routes and the judge / `memory_eval` route
    - at worker start for `TAXONOMY_VERSION`

    Name the stage per writer (`s1_generate`, `t2_generate`, and T9's stage). Model "re-run needs approval", for example `reverify_run_id` plus approval fields.
22. **Monthly train scope is ambiguous.** The unique index is per (writer, scope, tenant), while the spec and ADR 0010 decision 6 say one regular release per writer per month. Decide which and write it in the ADR.
23. **The empty class skips shadow evidence**, but ADR 0010 decision 1 and WM-18 scope 2 say activation needs eval *and* shadow (only lexicon is exempt). Amend ADR 0010 (decisions 1 and 12) in the same PR, and record this as a spec deviation in the implementation notes.

**E. WM-19, WM-21 and WM-22 needs to bake in now (avoid another CHECK migration)**

24. **`run_kind`** is missing `r1`, `reverify` and `probe`. WM-19 regenerates only in reverify, and R1 is part of the ladder.
    - Add `phase` (probe / tune / holdout) to `eval_item_result`.
    - Add `scored_result_id uuid REFERENCES eval_item_result`, so a rejudge row points at the stored output it scored. This lets "controls never regenerated outside reverify" be enforced, by a trigger: arm=control AND mode=regenerate needs run_kind IN ('baseline_import','reverify').
25. **Store judge calibration on the run** (WM-19 scope 4): `judge_kappa numeric` and `judge_counts bool`. Add `cost_cap_usd` (scope 6).
26. **`writing_memory_shadow.input_source` allows `golden_item`**, but WM-21 scope 1 says "excluding golden items". Remove it from the CHECK.
27. **WM-22 prompt register.** Store `prompt_sha256` per writer in the r0 run details and the release fingerprint.
28. **WM-22 "close monthly train".** Add state for it now, either a `train_closed_month` column on `writing_memory_writer` or a small table.
29. **The A1 stamp can say memory applied when it was not.** The hook exists only on the v2 path, and v2 needs `S1_WRITER_V2`. With v2 off (the CI default), or on the s1_batch path, the resolver would still stamp.
    - Emit the stamp from the writer that consumed the view, not from the resolver.
    - `release0` must check that the running worker has v2 on, and fail otherwise.

**F. Feasibility of the Dev steps (approval and auth)**

30. **The agent cannot call AI_ADMIN routes on Dev.** The CIS API accepts only Cognito sessions, and the fixed Preview host is capped at viewer. So Dev steps 4–6 (approve, activate, PATCH writers, the scratch-draft 409) cannot run as written. Also, putting Nghiệp's staff id in `approved_by` for a call the agent made breaks ADR 0010 decision 1 ("one human click"). Choose one:
    - bring WM-22's minimal approve / activate / rollback / switch buttons into PR-C, so Nghiệp clicks himself (verify with aa-ui-verify), or
    - run an in-container CLI over the same `releases.*` functions, with `approved_by` set to the agent identity and `approval_ref` set to the decision-page link, documented as an ADR exception.

    The 409 from the API layer is then proven by TestClient in CI plus the CLI calling `evidence_problem`.
31. **Specify the drill scope.** Use a tenant scope on an E2E test tenant, with its own tenant release 0 and release 1, both empty. Do not create a platform "release 1", which would permanently shift platform release numbers. A tenant release 1 rolling back with no tenant release 0 would return 409 `no_previous`.

**G. Conflicts on main and open PRs**

32. **Open CIS PR #1015 (AA-790) collides with PR-D.** It changes T9 `SYSTEM_PROMPT`, `writer_prompt_version` (`662d4aa5` → `3c078692`), `generate.py`, `service.py` (the `write_content` call sites the plan extracts into `writer_kwargs`), `build_user_prompt` (a new "LEAD WITH THIS FACT" line, so line 347 moves) and `writer_input.lead_focus`.
    - Merge or settle #1015 before the PR-D pin commit.
    - The T9 replay must pass the stored `lead_focus` and request write index.
    - The T9 AA-729 baseline becomes stale, so set `reverify=true` with reason `prompt_version_mismatch`, as Q8 does for A1.
33. **Migration numbers.** 282 and 283 are free on CIS and Infra `main` (latest 281; no open PR holds a migration). Keep the reservation branches.

**H. Tenant text in public repos**

34. **The fixture is tracked in the PUBLIC root repo**, not a "private root copy". `docs/eval/aa729/fixture-1.1.0.json` (2.3 MB) is in `AdventureAsia365-Ecosys/AA-Ecosys`, which is PUBLIC. It holds the brand packs `t2:atlas-hearth`, `t2:wildkind-travel`, `t2:terra-family`, `t2:trail-pulse`, full T9 contexts and outputs.
    - Raise it to Nghiệp.
    - Move the fixture to S3 bronze, `git rm` it with a `.gitignore` entry, and decide on history.
    - Run the marker and fingerprint guard in the root repo CI too.
    - Generate fingerprints from the S3 copy.
35. **Keep the bronze bucket name out of CIS code and docs.** It embeds the account ID (DM-6.10). Read it from env; take `--fixture-key` and report paths as keys only.
36. **The fingerprint file in the public CIS repo is a membership oracle** for golden text. Use a keyed HMAC (key in CI secrets), or document that it is acceptable.

**I. Erasure and RLS**

37. **Add the new tenant-text stores to ADR 0010 decision 11**: `eval_golden_item`, `eval_item_result`, plus the DM-7 rows.
    - Make `eval_golden_set.item_count` derived, or document it as an import-time count, since erasure deletes items.
    - The importer must refuse to re-import items for an offboarded or missing tenant.

## Verdict

The plan cannot ship as written. It has four blockers:
- **Self-comparison (1–4):** byte-identical replay compares the new builder with itself.
- **Paid drill (6):** the rollback drill makes paid T9 writes.
- **Public fixture (34):** the AA-729 fixture is tracked in the public root repo.
- **Approval path (30):** the agent cannot make AI_ADMIN API calls on Dev, so the approval steps cannot run as written.

The rest are wrong names or shapes and fields to add now. Fix them before PR-A is written.