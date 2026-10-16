# AA-668 live re-verify after CIS #759 (S239, Claude Code)

- **Build under test:** CIS #759 `2090bb22` ("live writing view shows piece text only; writer panel labels and reopen").
  - Backend: api `aa-cis-dev-api:631` and worker `aa-cis-dev-worker:188`, image `dev-2090bb2206fb…`. Both rollouts were COMPLETED at 03:25Z.
  - Frontend: the Vercel Production deploy of `2090bb22` reported success at 03:21Z.
- **Site:** https://aa-cis.lumiguides.it.com. Tenant: terra-family (`20d07d32-ed98-405f-81d5-0c2399c9fcdf`).
- **Credentials:** read from Secrets Manager at run time and never printed or saved. A grep of `logs/` for secrets found none.
- **Run windows (UTC):**
  - Social: 03:31:18–03:34:04.
  - Tour rewrite: 04:02:50–04:05:00.
- **Linear AA-668** was read only. Its Done-when text comes from the S239 in-progress audit.
- **Earlier evidence** (before #759) is one level up, in `../README.md`.

## Verdict

| Done-when / check | Verdict |
|---|---|
| **(a)** Social Content on Dev: pick → goal → angle → streamed text → piece saved, no page scroll at 1440x900 | **MET, live** (2 runs) |
| #759 blocker: no `"replacements"` JSON in the tenant's live view, including a run where sentence repair ran | **MET, live.** Run 2 repaired sentences twice. 0 of 69 progress responses had `replacements`, and none had a section starting with `{` |
| Final live text equals the saved piece | **MET.** Both runs `equal_exact: true` |
| Write card reads "Goal: \<name\> · Channel: LinkedIn" | **MET** ("Goal: Introduction / Awareness · Channel: LinkedIn"). There is a ~0.3 s flash on reopen, see defect D3 |
| Social: close mid-write → Continue shows the text at once, no "Starting…" | **MET by video frame.** The script's own check was taken too early, see "Notes on the social check" |
| **(b)** Tour rewrite uses the same panel: header with title, language and channel, live steps and text | **MET, live** |
| (b) Close mid-write → "View progress" reopens with the text so far at once | **MET, live** (first text 56 ms after the click, with progress answers held, 0× "Starting…") |
| (b) Panel kept open to the end: ready state + "Open in My Catalog" opens the new version | **MET, live** (v5 drawer, "Created: 16 Oct, 11:03") |
| (b) Success toast | **MET, live at 390.** The toast fires for a panel closed mid-write. No toast fires while the panel stays open (by design, see D5) |
| (b) Final live sections equal the saved `rewritten_content` | **MET.** 7/7 sections are equal, 10,233 chars |
| My Catalog at 390 renders cards, at 1440 a table; both reach the panel | **MET.** At 390 a card's "View progress →" opens a full-screen sheet 390x844 |
| Panel fits at 1440x900 (x=720 w=720 h=900) and at 390x844, `page_overflow_x 0`, `scrollY 0` | **MET** in every state measured |

**Overall:** both AA-668 Done-when bullets are met live on Dev after #759, and the #759 blocker no longer reproduces. The open items are the defects below. **D1 is a serious content bug outside AA-668's scope.**

## Cost (shared.llm_call_log via admin `/admin/job-runner/jobs/{id}/llm-calls`, `logs/admin-jobs-llm-cost.json`)

| Job | Kind | Status | Created → finished (UTC) | LLM calls | Cost |
|---|---|---|---|---|---|
| `55ea7b37-4bf2-4694-bea2-fbc931b51561` | t8_angles (social run 1) | succeeded | 03:31:42 → 03:32:01 | 1 | $0.0295 |
| `a94a884a-25cd-4f3c-aac7-f8946a40a79f` | t9_write (social run 1) | succeeded | 03:32:06 → 03:32:24 | 5 | $0.0189 |
| `550a3b34-8926-4cec-a58e-bdce42708865` | t8_angles (social run 2) | succeeded | 03:32:50 → 03:33:12 | 3 | $0.0225 |
| `28ab6260-ee48-4654-9c5a-bfbb62593095` | t9_write (social run 2) | succeeded | 03:33:17 → 03:33:50 | 14 | $0.0253 |
| `e360282e-690f-40fd-906b-e5c75fe225da` | t2_rewrite | succeeded | 04:03:15 → 04:04:46 | 7 | $0.1239 |
| **Total** | | | | | **$0.2202** |

Paid POSTs:
- Social: two writes. The brief allows a second write only if run 1 shows no sentence repair, and run 1 showed none.
- Rewrite: one. The route guard counted `rewrite_posts 1` and blocked nothing.
- Tenant quota went from 13 to 14 rewrites used (186 left).

## Part 1: Social Content, LinkedIn (`logs/social.json`, script `logs/aa668r_social.mjs`)

### Run 1: close mid-write → Continue

IDs:
- subject `b54e9058-b057-4690-bb28-2976ac9fe363` (card "National Library — visit")
- request `b353d044-060b-4c65-84c2-44f64f30a0d1`
- piece `4ebda814-b6f1-4a3b-80e3-727f866220fb`

Steps:
1. Slate → LinkedIn tab (`s01`).
2. Pick to write: `POST /v1/subjects/{id}/pick` returned **200**.
3. The panel header read "National Library — visit" / "Writing for LinkedIn · Segment".
4. Picked the goal "Introduction / Awareness" and clicked Generate 3 angles: `POST …/goal` returned **202**, and the angles arrived (`s02`).
5. Clicked "Write with this angle": `POST /v1/content-writing/requests/{id}/write` returned **202** `in_progress`.
6. The Write card read "Angle: What the Institute Teaches Families About Bhutan · **Goal: Introduction / Awareness · Channel: LinkedIn**". The keys `introduction_awareness` and `linkedin` are no longer shown.
7. Text streamed (`s03`). The panel was closed mid-write and the row showed Continue (`s04`).
8. Continue reopened the panel (`s05`, `s05b`, `s05c`, see the notes below).
9. Polling:
   - The script polled `GET /api/tenant/v1/progress/piece/{piece}` every ~0.5 s: **23 responses** (3 not_found, 17 running, 3 done).
   - The panel's own polls: 16 responses.
   - **0 contain "replacements", and 0 have a section starting with `{`.**
10. Final:
    - progress `done`, revision 1, steps `prepare/write/check done, revise skipped, save done`
    - 1,149 chars, **equal to the piece `content_text`** (`GET /v1/content-writing/pieces/{id}` returned **200**, `ready`, `linkedin`)
11. Panel result: 1440 (`s06`) and 390 full-screen sheet (`s07`). Actions: Change angle / Export text / Open in My Content.
12. Repair log (admin read): `repair_log [{attempt 1}]`, no `repair_mode: sentences`. So run 2 was made.
    - Note: `cost_by_stage` lists one `t9_repair` call ($0.0013) for run 1 that did not change any sentence.

### Run 2: sentence repair ran

IDs:
- subject `766e9956-4d29-4d0a-8fdf-187f4158ad5b` (card "Gyeongju — visit archaeological remains…")
- request `3fa8495d-64c0-4948-8910-c9f599691389`
- piece `269682ec-ddff-4249-bd7e-af8a42bf6a28`

Steps:
1. `pick` returned 200, `goal` returned 202 and `write` returned 202. The Write card read "Goal: Introduction / Awareness · Channel: LinkedIn".
2. **Repair log:** attempt 1 `repair_mode sentences, sentences_repaired 1`, attempt 2 `sentences, 2`. The piece status is `approved`, `attempt_number 3`.
3. Polling:
   - Script: **40 responses** (2 not_found, 35 running, 3 done).
   - Panel: 29.
   - **0 contain "replacements", and 0 have a section starting with `{`.** Revisions [0, 1].
4. Final: progress `done`, steps `… revise done`, 773 chars, **equal to the piece `content_text`**.
5. Screenshots at 1440 (`s08`) and 390 (`s09`).

This is the case #759 fixed: a sentence repair ran and nothing from its JSON reached the tenant's live view.

### Notes on the social check

The script measured `text_shown_at_once` 545 ms after the click, and it recorded `false` with `progress_requests_held 0`. That measurement came too early.

On a reopen the wizard first reads `GET angle-gate/requests/{id}`, then `…/latest-piece`, and only then mounts LiveWriter. So no progress request had been sent yet, and the hold never applied.

The recorded video shows what the tenant actually sees:
- `s05b` (~0.3 s after opening): the Write card only, with no "Starting…".
- `s05c` (~0.3 s later): the full text written so far, at once, with no retype from empty.

So the requirement is met as the tenant sees it. The tour reopen check below holds the progress answers properly and shows the remembered text after 56 ms.

## Part 2: Tour rewrite (`logs/rewrite.json`, script `logs/aa668rr_rewrite.mjs`)

IDs:
- published_tour `2cf487be-2a9a-4a64-b1d0-1cceaebd9361` (Laos to Vietnam by Bicycle). Source: finished v4 `554ab6e8-…`.
- **new version v5 `5bf13cc9-b5e8-42a2-98d5-8cce720ce2e2`**
- job `e360282e-690f-40fd-906b-e5c75fe225da`

### Context A at 1440 (table rows)

1. My Catalog Tours rendered as a **table** at 1440 (`r01`). Clicked Open → on the READY row, and the version drawer opened (`r02`).
2. Request Rewrite: `POST /v1/tours/pool/2cf487be…/rewrite` returned **200** `{version_id 5bf13cc9…, version_number 5, status pending, job_id e360282e…}`.
3. The drawer was replaced by the Writer panel (1 dialog):
   - Title: "Laos to Vietnam by Bicycle: Nam Ou River to Hanoi — 12 Days".
   - Context: "**Rewriting in en-US · for Tour catalog**".
   - Layout: 720x900, fits the viewport (`r03`).
4. Live steps and text streamed (`r04`: research done, write active; 1,621 chars of name/subtitle/summary/highlights).
5. Closed the panel mid-write. The row showed "WRITING · View progress →" (`r05`).
6. **Clicked "View progress →" with every panel progress answer held for 3 s:**
   - the panel appeared after 53 ms,
   - **the remembered text was there after 56 ms** (start and end of the 1,780-char snapshot both visible),
   - it was still there at every sample to 2.6 s,
   - **"Starting…" was seen 0 times** (`r06` was captured during the hold, while the drawer was still sliding in; `r06b` was taken after the hold).
7. **Kept the panel open to the end:**
   - At 04:04:48 the panel showed `tour-rewrite-ready`: "Your new version is ready and saved in My Catalog Tours…", all 6 steps checked, footer AI notice + **Export DOCX + Open in My Catalog** (`r09` at 1440; `r09b` as a full-screen sheet at 390, which fits).
   - No toast appeared while the panel was open (`toast_while_open 0`, see D5).
8. **Open in My Catalog** closed the panel and opened the v5 version drawer: 1 dialog, "Created: 16 Oct, 11:03", new summary text (`r11`).

### Context B at 390 (cards)

1. My Catalog rendered as **cards** at 390. The Laos card read "STATUS WRITING · ACTIONS View progress →" (`r07`).
2. "View progress →" opened the panel as a 390x844 sheet with live text, itineraries streaming at 7,783 chars (`r08`).
3. Closed it mid-write.
4. At 04:04:49 the **toast** appeared: *"Laos to Vietnam by Bicycle: Nam Ou River to Hanoi — 12 Days" is ready — find it in My Catalog Tours.* (`r10`).
5. 6 s later the card read READY · Open → (`r10b`).

### Progress stream vs the saved version

| | |
|---|---|
| Script poller (~0.5 s, APIRequestContext, not held) | **105 responses**: 2 not_found, 99 running, 4 done; revisions [0, 1, 2]; max 10,233 chars |
| Panel polls | A 76, B 3 |
| Bad responses | **0** with `replacements`, **0** sections starting with `{`, **0** sections with a JSON `"key":` |
| Final progress | `done`, revision 2, steps research/write/check/revise/polish/save all done |
| `GET /v1/tours/versions/5bf13cc9…` | **200**: v5, `ai_generated`, job `succeeded` |
| Compare | **All 7 sections equal** the sections built from `rewritten_content` (name 69, subtitle 174, summary 1,544, highlights 977, itineraries 6,727, seo_title 44, seo_meta 150 chars). No extra or missing keys |

Before #759 the final T2 snapshot was the last streamed draft. Now it is the saved version.

Other checks:
- `my-versions` row v5: `ai_generated / succeeded`.
- Console / HTTP errors: B had none. A had 2× **404 `GET /v1/tours/pool/2cf487be…`** (D2).

## Defects / notes

1. **D1 (major, NOT AA-668, pre-existing, needs its own issue):** the Slate Subject the tenant picks is not the place the post is written about.
   - Evidence:
     - Run 1: the card and panel say "National Library — visit", but the angles and post are about the National Institute for Zorig Chusum (Thimphu). The writer seed is `atom 00480b6b9d0bfedd`, "Traditional Arts & Craft School".
     - Run 2: the card says "Gyeongju — visit archaeological remains… Silla period" (Korea), but the post is about the **Lok Virsa Museum, Islamabad (Pakistan)**. The seed is `atom 021bfcdfd62b82c1`.
     - The earlier pre-#759 Uran Togoo run matched.
   - Likely cause: `services/acp_shared/slate.py::_resolve_representative_atom` hands T8/T9 `ORDER BY m.atom_id LIMIT 1` from `acp_contract.atom_segment_member` for the Subject's segment. If a segment's members mix places, which run 2 suggests across countries, the request gets an unrelated atom. The card title comes from the segment's place and action.
   - Not proven: the DB read (subject → segment → member atoms with place and country) was blocked for subagents (`ecs execute-command`), so the orchestrator has to run it. The ready read-only script is `logs/d1_subject_atoms_NOT_RUN.py` (S3-mediated ECS exec). Admin piece evidence: `logs/admin-pieces-social.json`.
   - Breaks the tenant-facing promise "pick this Subject → write about it".
2. **D2 (minor, pre-existing, seen again):** opening a My Catalog version drawer calls `GET /v1/tours/pool/{published_tour_id}`, which returns 404 and logs a console error. The drawer still renders, and `POST …/pool/{id}/rewrite` on the same id returns 200.
3. **D3 (minor, #759 follow-up):** on a social reopen via Continue, for ~0.3 s before `latest-piece` answers:
   - the Write card shows **"Goal: Introduction awareness"** (the `humanizeKey` fallback, because the goal list has not loaded yet),
   - a **"Change angle"** button appears even though the job is still writing (`writing` is still false),
   - no live view shows (`s05b`).
   Then the text appears. Fix ideas: hide the button and the goal label until the `latest-piece` decision is known, or seed `writing` from the known in-flight piece.
4. **D4 (minor):** the rewrite POST response still says "check My Catalog in ~30 seconds"; the real job took 91 s. The UI does not show this message.
5. **D5 (design note):** with the panel kept open to the end, no toast fires, only the ready state. The toast is for a panel closed mid-write. That is consistent with `TourRewritePanel`/`useWriteWatcher`, and it was verified on that path (B).
6. **D6 (cosmetic):** on the toast at 390 (`r10`), the card still read WRITING / View progress for up to 5 s, until the list's 5 s refetch. The toast and the list briefly disagree.
7. **Not run:** Publish behind the confirm (LinkedIn has no publish action). Export DOCX was not clicked.

## Files

- Screenshots:
  - social `s01–s09`, plus video frames `s05b` and `s05c`
  - rewrite `r01–r11` (`r06`/`r06b` held reopen, `r07`/`r08`/`r10`/`r10b` at 390, `r09b` ready at 390)
- Video (Playwright `recordVideo`):
  - `video/social/social-linkedin-run1-close-continue-run2-repair-1440.webm`
  - `video/rewrite-A-1440/rewrite-A-request-close-reopen-held-ready-open-1440.webm`
  - `video/rewrite-B-390/rewrite-B-cards-view-progress-close-toast-390.webm`
- Logs:
  - `logs/social.json`, `logs/social-run{1,2}-progress-polls.json` (every response), `logs/social-run{1,2}-piece.json`
  - `logs/rewrite.json`, `logs/rewrite-progress-polls.json` (every response), `logs/rewrite-version-and-final-progress.json`
  - `logs/admin-jobs-llm-cost.json`, `logs/admin-pieces-social.json`
- Scripts: `logs/aa668r_social.mjs`, `logs/aa668rr_rewrite.mjs`, `logs/aa668rr_jobs.mjs`, `logs/aa668rr_admin_piece.mjs`.
