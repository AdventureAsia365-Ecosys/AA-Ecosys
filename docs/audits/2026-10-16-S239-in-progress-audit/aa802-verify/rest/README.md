# AA-802 live verify on CIS Dev: older-copy indicator + /pending vs My Content (S239, Claude Code)

- **Date:** 2026-10-16, 09:24–09:30 (UTC+7)
- **Environment:** CIS Dev, https://aa-cis.lumiguides.it.com (API https://api-cis.lumiguides.it.com). Live image dev-1a7d4553.
- **Approval:** Nghiệp approved test edits on test tenants in S239.
- **Credentials:** read from Secrets Manager at run time (`aa-cis/dev/e2e-test-admin`, `aa-cis/dev/e2e-tenant/terra-family`, `aa-cis/dev/e2e-tenant/atlas-hearth`). Nothing was printed or saved. Password fields in the videos are masked inputs.
- **Scripts (copied here):**
  - `aa802rest_probe.mjs`: read-only probe used to choose the piece.
  - `aa802rest_verify.mjs`: part (a). It runs Playwright at 1440x900 and records video in three steps: export, apply, after.
  - `aa802rest_pending.mjs`: part (b). Read-only.
- **Cost:** $0. The admin action was a manual **Edit**, which makes no LLM call. No paid Rewrite or Suggest was used.
- **Earlier evidence:** the T9 and T2 silent-correction bullets were verified in `../README.md` and `../t2/`.

## (a) Already exported → the admin sees that the tenant has an older copy

### How it works (code)

- **API.** `api/routers/admin_content_quality.py`:
  - `_DELIVERED_SQL` takes `published_at`, the newest `publish_log` row with status `published`, and `exported_at`, the newest `audit_log` row with action `content_piece.exported`.
  - `tenant_copy_state()` sets `delivered_at = max(published_at, exported_at)`.
  - `older_copy` is true when an admin sentence edit (an `admin_sentence_*` audit row) comes after `delivered_at`.
- **Admin UI.**
  - `TenantCopyNotice` (`frontend/app/admin/content-quality/SentenceActions.tsx`, `data-testid="cq-older-copy"`) shows at the top of the drawer.
  - Before any edit, the flagged-sentences section also warns: "The tenant already exported this piece…".
- **Tenant export.** The portal's My Content drawer has an **Export** button. It calls `GET /v1/content-writing/pieces/{id}/export`, which writes the `content_piece.exported` audit row.

### Target

| | |
|---|---|
| Tenant | terra-family (Terra Family Expeditions) |
| Piece | `c54260a5-e154-4f10-b850-fc40676402b7` (linkedin, status `approved`, attempt 2, created 2026-10-16T01:36Z) |
| Request | `9e957fac-596a-4238-8b89-4aa775dab78f`, angle "Sacred Stillness: What Pawangka Teaches Kids That Classrooms Can't" |
| Why this piece | It is the latest piece of its request, so it is the one My Content shows; `26a20425…` is now superseded by it. It has one flagged sentence (F12_scope, warning) that can be edited. LinkedIn is not a publishable channel, so it is never on `/pending`, and part (b) is not affected. |
| State before | `published=false`, `exported=false`, `tenant_copy.older_copy=false`, 0 admin edits, 1113 chars |

### Steps and results

1. **Tenant, before.**
   - All 4 tenant calls returned **200**: piece, latest-piece, `/reviews` and `/pending`.
   - Text length 1113. It contains the sentence "Pawangka Monastery, built in the seventh century by Tibetan King Songtsen Gampo, holds weight…".
   - The key-walk found 0 forbidden keys.
   - Screenshot: `tenant-before-1440-my-content-drawer.png`.
2. **Tenant export.**
   - In the My Content drawer (`/portal/t10-review?piece=c54260a5…`) I clicked **Export**.
   - `GET …/pieces/c54260a5…/export?format=text` returned **200** `text/plain` with 1113 bytes.
   - The browser downloaded `tenant-exported-sacred-stillness-what-pawangka-teaches-kids-that-classrooms-.txt`, which is saved here and still has the old sentence.
   - The admin API then showed `exported=true`, with `exported_at = delivered_at = 2026-10-16T02:25:54.782Z` and `older_copy=false`, which is correct because no edit had been made after the export yet.
3. **Admin, before the edit.**
   - Logged in as e2e-claude-code, I opened `/admin/content-quality?tab=pieces&piece=c54260a5…`. The `cq-older-copy` notice was not shown yet (count 0).
   - The flagged section shows "The tenant already exported this piece. An edit changes our copy only — the downloaded file keeps the old text."
   - Screenshot: `admin-before-1440-flagged-sentence-exported-note.png`.
4. **Admin Edit.**
   - On the F12_scope row ("names 'King Songtsen Gampo', outside this piece's scope") I chose **Edit**. The draft was pre-filled with the sentence.
   - I replaced the sentence with "Pawangka Monastery holds weight that children sense before they can name it." and clicked **Apply**.
   - `POST /api/admin/content-quality/pieces/c54260a5…/sentences/apply` with `mode=manual` and `gate=F12_scope` returned **200** with `warnings=[]`. Length went from 1113 to 1051, and the status stayed `approved`.
   - Screenshots: `admin-edit-1440-replacement-typed.png`, `admin-after-1440-toast-drawer.png`.
5. **Admin, after the edit.**
   - `tenant_copy` is now `{exported_at: 02:25:54.782Z, delivered_at: same, older_copy: **true**, edits_after_delivery: 1}`.
   - The audit row:
     - action `content_piece.admin_sentence_edited`
     - actor `admin:2d8e5a2f-3722-4571-9327-177d10b74127`
     - created_at 2026-10-16T02:26:14.851Z
     - span 0–138, before = the old sentence, after = the new sentence
     - `exported: true`, `published: false`
   - After a reload the drawer shows the amber notice:
     > **The tenant has an older copy.** They downloaded it on Oct 16, 09:25 AM, before 1 admin edit to this piece. Their copy keeps the old text until they export again.
   - "ADMIN EDITS · 1" appears, with the old sentence struck through.
   - Screenshot: `admin-after-1440-older-copy-notice.png`, which shows both the notice and the audit row.
6. **Tenant, after.**
   - All 4 calls returned **200**. The piece, latest-piece (same piece_id), My Content and the drawer all return the edited text at 1051 chars, and the old sentence is gone.
   - Diffing `tenant-before-content_text.txt` against `tenant-after-content_text.txt` shows exactly one change, in that sentence.
   - The key-walk found 0 hits. The pattern covered gate, score, held, flag, repair, ledger, violation, quality, blocking, problem, older, tenant_copy, exported, admin_edit and audit.
   - The piece's keys are only `piece_id, angle_gate_request_id, channel, ready_state, content_text, seo_title, meta_description, slug, route_hub_name, route_segment_count, created_at`.
   - The drawer word scan found nothing for held, flag, gate, F-codes, "needs review", "older copy", "updated version" or "admin".
   - The tenant sees no notice. This matches the spec, which made the tenant notice optional and deferred.
   - Screenshot: `tenant-after-1440-my-content-drawer.png`.

**Video** (`video/`):
- `1-tenant-export.webm`: login, drawer, Export.
- `2-admin-edit-older-copy.webm`: admin drawer, Edit, Apply, reload, notice.
- `3-tenant-after.webm`: tenant drawer with the edited text.

## (b) Scope addition 1: T11 `/pending` = My Content items with no live publish; no request repeats

Tenant API only: `GET /v1/content-writing/reviews` (My Content), `GET /v1/publish-log/pending` and `GET /v1/publish-log?limit=200` (the tenant's published and unpublished rows). All returned 200 for both tenants. Data: `b-pending-vs-my-content.json`.

| Tenant | My Content | No live publish | …on a publishable channel (blog/facebook) | `/pending` cards | Equal? | Request ids on `/pending` unique? |
|---|---|---|---|---|---|---|
| atlas-hearth | 5 | 5 | **3** | **3** | yes, same 3 piece_ids | yes (3 of 3) |
| terra-family | 6 | 6 | **4** | **4** | yes, same 4 piece_ids | yes (4 of 4) |

Per item:

- **atlas-hearth.**
  - 3 blog items, never published; all 3 are on `/pending`.
  - 2 LinkedIn items, never published; not on `/pending`.
  - No `publish_log` rows.
- **terra-family.**
  - "The Family Dinner…" (blog) and "What One Ruined Monastery…" (blog) were never published; both are on `/pending`.
  - "The Checkpoint Before the Temple" (facebook) was published and later unpublished (1 row); it is on `/pending`.
  - "Where Two Worlds Meet: Lake Khövsgöl…" (blog) was published and unpublished twice (2 rows); it is on `/pending`.
  - 2 LinkedIn items were never published and are not on `/pending`.

**Why the counts differ: 5 vs 3, and 6 vs 4.**
- The difference is exactly the LinkedIn items.
- `/pending` lists only channels the portal can publish to: `_SUPPORTED_CHANNELS = ("blog", "facebook")` in `v1_publish.py`, matching `PUBLISHABLE_CHANNELS` in the frontend.
- LinkedIn pieces stay in My Content for export, but they never get a Ready to Publish card.
- This explains the S238 gap: "atlas-hearth My Content 5, T11 3". The other 2 are the LinkedIn items, not published pieces.
- An item that was published and then unpublished counts as "no live publish" and comes back on `/pending`, as `list_pending`'s docstring describes.

**Other checks.**
- Every `/pending` piece_id is the latest piece that My Content shows for its request, so there are no superseded pieces.
- All `/pending` titles are present in the rendered T11 page. Screenshots: `b-<slug>-1440-my-content-list.png`, `b-<slug>-1440-t11-publish.png`.

**Verdict.** **MET**, with one reading: "My Content items with no live publish" has to be limited to the publishable channels (blog, facebook). Suggest rewording the Done-when that way.

## Verdict per Done-when bullet (this run)

| Done-when | Verdict | Evidence |
|---|---|---|
| Already published/exported → admin sees that the tenant has an older copy | **MET (live, export path)** | Steps 2–5. `older_copy` went false → true after one edit that came after the export. The notice text is shown in the drawer. The publish path (`published_at`) uses the same `tenant_copy_state()` and was not exercised, because it would need a live WordPress/Facebook post. |
| (optional) neutral tenant notice | **Not built (deferred, allowed by spec)** | The tenant sees the edited text with no notice and no flag keys (step 6). |
| Repair → tenant API returns the repaired text, no gate/score keys | **MET again** on an approved, exported piece | Step 6 |
| History has both versions | **MET (span diff)** | Audit row with `before`/`after` sentence and offsets 0–138, lengths 1113 → 1051 |
| Scope 1: `/pending` = My Content with no live publish; no request repeats | **MET**, limited to publishable channels | Section (b) |

## Defects / notes

- **No product defect found.**
- **Minor UX gap (by design, not a bug): the edited sentence stays flagged in the admin drawer.**
  - After the Edit, "Flagged sentences · 1" still lists the new sentence, and the text still highlights it. The F12 reason, "names 'King Songtsen Gampo'", also stays, although the name is gone.
  - The cause is that the router keeps `gate_ledger`/`flags` as the writer produced them ("they measure the writer, not the admin's edit"), and the highlight still matches the span at offset 0.
  - A Cut removes the span, so its row goes away; that is why the earlier T9 run went from 4 flagged sentences to 3. An Edit keeps a stale row, which could lead an admin to edit the same sentence twice.
  - Possible follow-up: mark a flagged row "edited by admin" when an `admin_sentence_*` audit row covers its span. Not filed; Nghiệp to decide.
- **Script gap (carried over): the T11 full-page screenshot shows only the first Ready to Publish card,** because the cards sit in an inner scroll container. The card count comes from the `/pending` API, and all titles are present in the page DOM.
- terra-family's WordPress connection currently shows as not connected on T11 ("Connect WordPress to publish"). This does not affect the test.

## Test records created (for later clean-up)

1. **Export audit row.** One row in `acp_shared.audit_log`: action `content_piece.exported`, tenant terra-family, resource_id `c54260a5-e154-4f10-b850-fc40676402b7`, created_at 2026-10-16T02:25:54.782Z, details `{channel: linkedin, format: text}`.
2. **Content change.** `acp_shared.content_piece` `c54260a5-e154-4f10-b850-fc40676402b7`: `content_text` was edited in place, 1113 → 1051 chars, changing only the first sentence. The full old text is in `admin-before-content_text.txt`. To restore it, put back the sentence at offset 0.
3. **Edit audit row.** One row in `acp_shared.audit_log`: action `content_piece.admin_sentence_edited`, resource_id as above, created_at 2026-10-16T02:26:14.851Z.
4. **Downloaded file.** A local copy of the exported file, kept here as evidence. It is test content and contains no secret.

Neither audit row carries a "ZZ S239 test" name, because these actions have no name field. Part (b) was read-only.
