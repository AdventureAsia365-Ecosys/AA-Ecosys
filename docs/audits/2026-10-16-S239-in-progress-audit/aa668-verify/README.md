# AA-668 live verify on CIS Dev (S239, Claude Code)

- **Scope:** Writer panel for Social Content (Done-when a) and for tour rewrite (Done-when b, CIS #756 `b9a9a76f`).
- **Site:** https://aa-cis.lumiguides.it.com. The Vercel Production deploy of `b9a9a76f` is `success` (02:14Z). It is the head of `main`.
- **Tenant:** terra-family (`20d07d32-ed98-405f-81d5-0c2399c9fcdf`, Terra Family Expeditions, growth plan).
- **Credentials:** read from Secrets Manager at run time and never printed or saved.
- **Run window:** 2026-10-16 02:27–02:33 UTC.

## Verdict

| Done-when / check | Verdict |
|---|---|
| (a) Social Content: Slate → segment → goal → angle → streamed text → piece saved, no CTA prompt, no page scroll at 1440x900 | **MET, live** |
| (b) Tour rewrite uses the same panel: header with title, language and channel, live steps and text | **MET, live** |
| (b) Closing mid-write keeps the job; "View progress" reopens the panel | **MET, live** |
| (b) Toast after closing; panel "ready" state; "Open in My Catalog" button | **NOT OBSERVED.** Script defect, not a product defect (see below) |
| Rewrite result saved as a new version in My Catalog | **MET, via API + drawer.** Not reached through the panel button |
| shared.job and content rows visible through the tenant API | **MET** |

## Cost (shared.llm_call_log, via admin `/admin/job-runner/jobs/{id}/llm-calls`)

| Job | Kind | Status | Created → finished (UTC) | LLM calls | Cost |
|---|---|---|---|---|---|
| `a966eb32-93f5-4f4a-bc62-54a45d78403f` | t2_rewrite | succeeded | 02:27:24 → 02:29:04 | 5 (2 sonnet-4-6 generate, haiku nudge, 2 judge) | $0.1254 |
| `7e0d07af-e814-46e6-9da2-086df81067d9` | t8_angles | succeeded | 02:29:43 → 02:30:01 | 1 | $0.0270 |
| `7619f24e-2eb5-4772-8af5-709b3180f5b8` | t9_write | succeeded | 02:30:04 → 02:30:26 | 9 (2 write, judges, embeds) | $0.0241 |
| **Total** | | | | | **$0.1765** |

The run made exactly one paid T2 rewrite and one T8 + T9 write. Route guards counted `pick 1 / goal 1 / write 1 / rewrite 1`. No second paid POST was sent.

## Part 1: Tour rewrite (My Catalog Tours)

IDs:
- published_tour `2cf487be-2a9a-4a64-b1d0-1cceaebd9361` (Laos to Vietnam by Bicycle)
- source version v3 `5c79de77-…`
- new version **v4 `554ab6e8-1047-40cc-8c91-516b81c834a6`**
- job `a966eb32-93f5-4f4a-bc62-54a45d78403f`

Steps:
1. Opened My Catalog Tours and opened the finished v3 (Open →) (`r01`, `r02`).
2. Clicked Request Rewrite. `POST /v1/tours/pool/2cf487be…/rewrite` returned **200** `{version_id 554ab6e8…, version_number 4, status pending, job_id a966eb32…}`.
3. The version drawer was replaced by the Writer panel (1 dialog):
   - Title: "Laos to Vietnam by Bicycle: Nam Ou River to Hanoi — 12 Days".
   - Context line: "**Rewriting in en-US · for Tour catalog**".
   - Layout: dialog x=720 w=720 h=900, fits the viewport, `page_overflow_x 0`, `scrollY 0` (`r03`).
4. Live steps and text streamed (`r04`). After 16 s the progress endpoint `/v1/progress/tour/554ab6e8…` showed `found:true, running`, steps "Reading … done / Writing your version active / …" and 1,518 chars of text. The TITLE, SUBTITLE and SUMMARY appeared in the panel as they were written.
5. Closed the panel mid-write. The job kept running: `my-versions` row v4 `status pending, job_status running`, and progress showed 3,670 chars and still running. The list row showed "WRITING · View progress →" (`r05`).
6. **View progress → reopened the panel** with the same header and live steps (`r06`). Closed it again so the page watcher would toast.
7. The job finished at 02:29:04 (`succeeded`, revision 2, all 6 steps done, 10,905 chars streamed).
   - Tenant API after the run: `GET /v1/tours/versions/554ab6e8…` returned **200** with `version_number 4, status ai_generated, job_status succeeded`, history v1–v4 and 10,735 chars of rewritten_content.
   - My Catalog row: "READY · Open →" (`r12`).
   - Opening it shows the v4 drawer, "Created: 16 Oct, 09:27" (`r13`).

**Not observed (script defect):** the second browser context was meant to keep the panel open until ready. It looked for a `<tr>` row at 390 px, but My Catalog renders cards on a phone, so it timed out and the script exited at about 02:28:20. The job finished about 45 s later, so these were never seen live:
- the success toast,
- the panel's ready state with "Open in My Catalog" and Export DOCX,
- the panel at 390.

A resume run with no new POST found the job already `succeeded`, so the panel could no longer be opened. The fixed script (`logs/aa668_rewrite.mjs`) opens the panel at 1440 and then resizes to 390. Closing these three items needs **one more paid rewrite, about $0.13**. It was not run because the brief allowed only one.

## Part 2: Social Content, LinkedIn (Done-when a)

IDs:
- subject `f886d436-4d2e-4ec1-b413-05d7ee1229e7` (Uran Togoo — walk into the volcanic crater)
- angle-gate request **`72082375-edc4-44f1-a2d8-3317be6eb325`**
- piece **`788f3568-f4d2-4a12-9572-982efb41aa56`**
- t8 job `7e0d07af…`, t9 job `7619f24e…`

Steps:
1. **Prerequisite test edit:** terra-family's brand had no `default_cta`. Through Brand Identity → Default Call to Action, it was set to "Message us to start planning your family trip." and saved with Save as New Version. `POST /admin/brand-identity` returned 200 and the brand moved from v3 to **v4** (`s00`). To revert, restore v3 from the Brand history.
2. Opened Social Content → LinkedIn tab (`s01`). Pick to write: `POST /v1/subjects/f886d436…/pick` returned **200** with request `72082375…`.
3. The panel opened with title "Uran Togoo — walk into the volcanic crater" and context "Writing for **LinkedIn** · Segment". It showed 8 goal cards. Dialog 720x900, fits the viewport, no page scroll (`s02`).
4. Picked the goal "Introduction / Awareness" and clicked Generate 3 angles. `POST …/goal` returned **202** (`generating:true`). Three angles arrived in 20 s, one marked RECOMMENDED (`s03`, `s04`).
5. Clicked "Write with this angle" on angle 0 ("The Volcano That Shaped the Steppe"):
   - `POST /v1/content-writing/requests/72082375…/write` returned **202**.
   - Request body `{}`: no CTA was sent, and the request's `cta` stays null.
   - **No "needs a call to action" prompt** appeared during the write or after it (count 0).
6. Text streamed with steps (Reading done / Writing active / …) and 832 chars after 7 s (`s05` at 1440, `s06` at 390 as a full-screen sheet, 390x844).
7. The finished piece showed "Your post is ready and saved in My Content". The text ends with the brand default CTA "Message us to start planning your family trip." The panel also showed the AI notice and the actions Change angle / Export text / Open in My Content. It fit at 1440x900 with no page scroll (`s07`) and at 390 (`s08`).
8. Open in My Content went to `/portal/t10-review?piece=788f3568…` and showed the piece row "The Volcano That Shaped the Steppe · LINKEDIN · Introduction / Awareness · READY" with its drawer (`s09`).

Tenant API evidence:
- `GET /v1/content-writing/pieces/788f3568…` → **200**: ready_state `ready`, channel `linkedin`, 977 chars.
- `…/requests/72082375…/latest-piece` → 200: same piece, `ready`.
- `GET /v1/angle-gate/requests/72082375…` → 200: status `approved`, goal `introduction_awareness`, 3 angles, chosen "The Volcano That Shaped the Steppe".
- `…/review` → 200.
- `GET /v1/content-writing/reviews` → 200: 7 rows, including this request and piece.
- `/v1/progress/piece/788f3568…`: `done`, revision 2, all 5 steps done.

The shared.job rows (kind, status, payload ids) are in `logs/admin-jobs-llm-cost.json`. The tenant sees the job state through `my-versions.job_status` and `/v1/progress`.

Console errors in the social run: none. HTTP errors: none.

## Defects / notes

1. **Script, not product.** On a 390 viewport My Catalog Tours renders cards, not table rows. Future live scripts must open the panel at 1440 first, or select by card.
2. **Minor, pre-existing.** Opening a My Catalog version drawer calls `GET /v1/tours/pool/2cf487be…`, which returns **404** and logs a console error. The drawer still renders. `POST …/pool/2cf487be…/rewrite` on the same id returned 200, so the pool detail read and the rewrite path disagree on whether this tour is in the tenant's pool.
3. **Minor.** The write response (202) has `channel: null`. The piece read returns `linkedin`.
4. **Minor, stale copy.** The rewrite POST body says "check My Catalog in ~30 seconds". The real job took 100 s. The UI does not show this message.
5. **No Publish button on LinkedIn.** The result actions had no Publish for LinkedIn, only Change angle / Export text / Open in My Content. That is expected if LinkedIn has no publish integration. Publish behind the confirm was not exercised live.
6. **Leftover from attempt 1.** The first social attempt picked "Punakha Dzong — visit" (subject `afdc091e…`, request `aa001cf7-6f04-4493-965b-b0ecf4fdf237`). The script then timed out on a mock-only goal test id, so the request was left in `pending_goal` with no job and no cost.
7. **Market omitted from the header.** As decided in #756, there is no per-Subject market in the Slate API and none on a T2 version.

## Files

- Screenshots `r01–r06, r12, r13` (rewrite) and `s00–s09` (social), plus `s99` (attempt 1 timeout).
- Video:
  - `video/social-linkedin-full-flow-1440.webm`: the full Done-when (a) flow.
  - `video/rewrite-A-request-close-viewprogress-1440.webm`: request → live panel → close → View progress.
  - The other videos are the failed attempts.
- Logs: `logs/*.json` (run logs, admin job/cost read) and the scripts `logs/*.mjs`.
