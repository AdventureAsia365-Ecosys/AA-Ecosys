# AA-802 live verify on CIS Dev: T9 silent correction (S239, Claude Code)

- **Date:** 2026-10-16, 08:38–08:42 (UTC+7)
- **Environment:** CIS Dev, https://aa-cis.lumiguides.it.com. Live image dev-1a7d4553.
- **Approval:** Nghiệp approved the Dev write on a test tenant in S239.
- **Script:** `aa802_verify.mjs` (copy here; source at `.tmp-session/s239/aa802_verify.mjs`). It runs Playwright at 1440x900 in three steps: `before`, `apply`, `after`.
- **Credentials:** read from Secrets Manager at run time. Nothing was printed or saved.
  - Admin: `aa-cis/dev/e2e-test-admin` (e2e-claude-code).
  - Tenant: `aa-cis/dev/e2e-tenant/atlas-hearth`.
- **Scope:** T9 only, as the task asked. The T2 tour-version path was not exercised.

## Target

| | |
|---|---|
| Tenant | atlas-hearth (Atlas & Hearth) |
| Piece | `1f02cecb-efd6-4f9c-bf32-1c6efbf3c77b` (blog, status `held`, attempt 3, from the S239 AA-768 re-run) |
| Request (angle_gate_request_id) | `41e41098-ffa7-472a-bdb2-da0922f80c0a`, angle "The Market as Cultural Decoder" |
| Delivered before the edit? | No. `published=false`, `exported=false`, and `tenant_copy.older_copy=false` |
| Flagged sentences before | 4, all F9_cta_fact (blocking) |

## Steps and results

1. **Tenant view, before.**
   - Every tenant call returned 200: `GET /v1/content-writing/pieces/{id}`, `/requests/{rid}/latest-piece`, `/requests/{rid}/review`, `/reviews` and `/v1/publish-log/pending`.
   - Text length was 7083 and contained the target sentence.
   - My Content had 5 items. `/pending` had 3 cards, and exactly 1 of them was for this angle (piece `1f02cecb…`).
   - Screenshots: `tenant-before-1440-my-content-drawer-top.png`, `tenant-before-1440-my-content-drawer-edit-point.png` (the sentence is visible) and `tenant-before-1440-t11-ready-to-publish.png`.
2. **Admin action.** As e2e-claude-code I opened `/admin/content-quality?tab=pieces&piece=1f02cecb…`. In Social Content this is the "08 · Content Quality" tab of the atom-curation group. I chose **Cut** on one flagged sentence (F9_cta_fact):
   > "The shift from museum to market is not a step down in cultural seriousness; if anything, it sharpens the question of what sustains a craft tradition when its original social context is changing."

   I clicked Confirm and **Cut**. The UI then sent `POST /api/admin/content-quality/pieces/{id}/sentences/apply` with mode=cut. It returned **200** with `warnings=[]`, length 7083 → 6888, and the status stayed `held`.
   - No LLM call was made, so the cost is $0.
   - Screenshots: `admin-before-1440-piece-drawer.png`, `admin-before-1440-flagged-sentence.png`, `admin-confirm-1440-cut-modal.png`, `admin-after-1440-toast-drawer.png` and `admin-after-1440-admin-edits-audit-row.png`.
3. **Admin after.**
   - Flagged sentences went from 4 to 3, and the piece shows "ADMIN EDITS · 1".
   - The audit row:
     - action `content_piece.admin_sentence_cut`
     - actor `admin:2d8e5a2f-3722-4571-9327-177d10b74127`
     - created_at 2026-10-16T01:40:00Z
     - mode `cut`, gate `F9_cta_fact`
     - before = the removed sentence, after = ""
     - length_before 7083, length_after 6888, published false
   - `tenant_copy.older_copy` stayed false, which is correct because nothing had been delivered.
4. **Tenant view, after.**
   - All 5 tenant calls returned 200.
   - Every surface returned the corrected text at length 6888 with the sentence gone: the piece, latest-piece, the My Content list item and the My Content drawer. latest-piece returned the same piece_id.
   - `/pending` still had 3 cards, with exactly 1 for this angle and the same piece_id.
   - Diffing `tenant-before-content_text.txt` against `tenant-after-content_text.txt` shows exactly one change: that sentence was removed.
   - Screenshots: `tenant-after-1440-my-content-drawer-top.png`, `tenant-after-1440-my-content-drawer-edit-point.png` (the paragraph now ends at "…Bhutanese making and craft.") and `tenant-after-1440-t11-ready-to-publish.png`.

## Verdict per Done-when bullet

| Done-when | Verdict | Evidence |
|---|---|---|
| A repair on an unpublished held piece means the tenant API returns the repaired text | **MET (live)** | Step 4: piece, latest-piece, My Content and the drawer all show 6888 chars with no cut sentence |
| History has both versions | **MET for T9, as a span diff** | The audit row stores `start`, `end`, `before` (the removed text), `after` and both lengths. The old version is the new text with the `before` span put back. Unlike the T2 path, the T9 row does not store the whole old and new texts. The piece row is updated in place, so the piece_id does not change (the #732 design). |
| Tenant responses contain no gate or score keys (AA-796 key-walk) | **MET (live)** | A recursive key-walk of all 5 tenant responses, before and after the edit, for gate, score, held, flag, repair, ledger, violation, quality, blocking and problem found 0 hits. `angle_gate_request_id` is excluded because it is an id. The drawer text has no held, flag, gate, F-code or "needs review" wording. |
| No flags or held wording visible to the tenant | **MET** | The drawer word scan found nothing, before or after. The portal screenshots show no badge or score. |
| `/pending` still shows exactly one card for that angle | **MET** | 1 card before and 1 after, both piece `1f02cecb…`. The total stayed at 3. |
| Admin audit row exists (admin UI) | **MET** | "ADMIN EDITS · 1" with the struck-through removed sentence (`admin-after-1440-admin-edits-audit-row.png`) |
| Scope 2: after a repair, `/pending` returns only the new piece_id | **MET in substance** | A T9 edit updates the piece in place, so the "new" piece is the same piece_id. `/pending` returns only that piece for the request. |
| Already published/exported means the admin sees an older copy | **Not tested** | That needs an export or publish before the edit. This run kept the piece undelivered on purpose. |
| T2 tour-version path | **Not tested** | Out of scope for this task |

## Defects / notes

- **No product defect found.**
- **Script gap: the T11 full-page screenshot shows only the first "Ready to Publish" card.** The cards sit in an inner scroll container. The card count comes from the `/pending` API (3 cards, 1 for this angle).
- **Wording gap between the S239 audit entry and the T9 audit row.** The entry says the audit row stores the whole version (`content_before`/`content_after`). For T9 the row actually stores the span (`before`/`after` plus offsets). Keep this in mind if the Done-when is read as "two full versions stored".
- **Design confirmation still pending in Linear.** Nghiệp has not yet confirmed the in-place UPDATE design (from #732) in Linear, as opposed to writing a new version row.

## Test records created (for later clean-up)

No new records were created. This run made one data change and wrote one audit row. Neither carries a "ZZ S239 test" name, because an admin sentence edit has no name field.

1. **Content change.** `acp_shared.content_piece` `1f02cecb-efd6-4f9c-bf32-1c6efbf3c77b` (atlas-hearth): `content_text` changed in place from 7083 to 6888 chars. To restore it, put back the sentence above at offset 1369; the full old text is in `admin-before-content_text.txt`.
2. **Audit row.** One row in `acp_shared.audit_log`: action `content_piece.admin_sentence_cut`, resource_id `1f02cecb-efd6-4f9c-bf32-1c6efbf3c77b`, created_at 2026-10-16T01:40:00.374Z.
