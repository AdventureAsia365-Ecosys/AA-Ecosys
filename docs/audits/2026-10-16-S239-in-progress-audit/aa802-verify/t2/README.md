# AA-802 live verify on CIS Dev: T2 silent correction of a tenant tour version (S239, Claude Code)

- **Date:** 2026-10-16, about 09:05–09:16 (UTC+7)
- **Environment:** CIS Dev, https://aa-cis.lumiguides.it.com. Live image dev-1a7d4553 (same as the T9 run in `../README.md`).
- **Approval:** Nghiệp approved Dev writes on test tenants in S239.
- **Scripts (copied here):**
  - `aa802t2_probe.mjs` is read-only. It lists every T2 version of the four test tenants and finds the editable ones.
  - `aa802t2_verify.mjs` runs Playwright at 1440x900 in three steps: `before`, `apply`, `after`.
  - The sources are in `.tmp-session/s239/`.
- **Credentials:** read from Secrets Manager at run time. Nothing was printed or saved.
  - Admin: `aa-cis/dev/e2e-test-admin` (e2e-claude-code).
  - Tenant: `aa-cis/dev/e2e-tenant/wildkind-travel`.
- **Cost:** $0. This was a manual Edit with no LLM call. Rewrite and Suggest were not used.

## How the admin corrects a T2 version (code, AA-CIS-App @ 1a7d4553)

**Backend:** `api/routers/admin_content_quality.py`
- `GET /tour-versions/{id}`
- `POST /tour-versions/{id}/sentences/suggest`, which makes a paid LLM call (not used here)
- `POST /tour-versions/{id}/sentences/apply`, which takes mode `cut`, `rewrite` or `manual`, is deterministic and makes no LLM call

**Rules for a correction:**
- An edit is allowed only when all of these hold (`t2_edit_block`):
  - `status` is `ai_generated` or `needs_review`
  - the version is the tenant's latest version of that tour
  - `edit_source` is not `tenant_edit`
- An `approved` version cannot be edited by design. The tenant has decided on it, so it is theirs.
- The row is updated **in place**, keeping the same id, version_number, status, edit_source and edited_at. No new version row is written, so the tenant's quota and version list do not change.
- History is the audit row (`acp_shared.audit_log`, resource_type `tenant_tour_version`). It carries the sentence before and after, the section before and after, and the **whole** `content_before` and `content_after`.

**Admin UI:** `frontend/app/admin/content-quality/TourVersionDrawer.tsx`
- Reached from Social Content → "08 · Content Quality" → tab "Tour versions (T2)". The deep link is `?tab=versions&version=<id>`.
- Each flagged sentence (T3_grounding or FORBIDDEN_WORD) has **Cut / Rewrite / Edit**. The "Text" section also lets the admin click any sentence to edit it.
- **So the admin UI does have a T2 sentence action. There is no gap against the issue scope.**

## Target

| | |
|---|---|
| Tenant | WildKind Travel (`885d4916-007b-415e-9261-909ad43c6d00`) |
| Version | `b0c7a857-e15c-4ffd-832d-fbf01ecfc5fc`: "Laos to Vietnam by Bicycle: Nam Ou River to Hanoi — 12 Days", **v2 (latest)**, status `ai_generated`, edit_source `ai_generated` |
| published_tour_id | `2cf487be-2a9a-4a64-b1d0-1cceaebd9361` |
| Delivered before the edit? | No. `tenant_copy.exported_at=null`, `published_at=null`, `older_copy=false` |
| Flagged before | 2, both T3_grounding: highlights[4] ("1954") and one itinerary sentence ("1954") |
| Why this one | Of the 48 T2 versions across the 4 test tenants, 12 are editable and 6 of those have flags. This one is on a tenant the T9 run did not touch, and the flag sits in a highlight, which the tenant drawer shows as its own row. |

The task asked for a "held or approved" version. `approved` cannot be edited by design (see above), and T2 has no `held` status. The tenant-safe equivalent is `ai_generated` or `needs_review`, so this run used an `ai_generated` version.

## Steps and results

1. **Tenant view, before (My Catalog Tours, `/portal/t4-pool?tour_id=…`).**
   - `GET /api/tenant/v1/tours/my-versions?page_size=50` returned **200** with total 12.
   - `GET /api/tenant/v1/tours/versions/b0c7a857…` returned **200**.
   - highlights[4] was "Dien Bien Phu in the Muong Thanh Valley — site of the 1954 battle that ended French colonial rule in Indochina".
   - version_history was v1 and v2, both ai_generated. `edited_at` was null.
   - The drawer showed the same highlight.
   - Screenshots: `tenant-before-1440-my-catalog-list.png`, `tenant-before-1440-my-catalog-drawer-top.png` and `tenant-before-1440-my-catalog-drawer-highlight.png`.
2. **Admin action.**
   - As e2e-claude-code I opened `/admin/content-quality?tab=versions&version=b0c7a857…`. The drawer said "Edits change the tenant's copy in place…". The flag row "Highlight 5 · T3 grounding" showed the buttons Cut / Rewrite / Edit.
   - I clicked **Edit**. The textarea was pre-filled with the sentence.
   - I typed "Dien Bien Phu in the Muong Thanh Valley — site of the battle that ended French colonial rule in Indochina" and clicked **Apply**.
   - The UI sent `POST /api/admin/content-quality/tour-versions/b0c7a857…/sentences/apply` with mode=`manual`, field=`highlights`, index=4 and gate=`T3_grounding`.
   - It returned **200** with `warnings=[]`. The stored highlight is "Dien Bien Phu in the Muong Thanh Valley**:** site of the battle that ended French colonial rule in Indochina". `sanitize_replacement` turned the " — " into ": " (see notes).
   - Screenshots: `admin-before-1440-version-drawer.png`, `admin-before-1440-flagged-sentence.png`, `admin-edit-1440-replacement-typed.png` and `admin-after-1440-toast-drawer.png`.
3. **Admin after.**
   - Flags went from 2 to 1; only the itinerary flag is left, and it was not touched. status, version_number (2), latest (2) and edit_source did not change. `tenant_copy.older_copy=false`.
   - "ADMIN EDITS · 1" is shown with the old sentence struck through and the new sentence under it (`admin-after-1440-admin-edits-audit-row.png`).
   - The audit row:
     - action `tenant_tour_version.admin_sentence_edited`
     - actor `admin:2d8e5a2f-3722-4571-9327-177d10b74127`
     - created_at `2026-10-16T02:14:07.571Z`
     - details: mode `manual`, field `highlights`, index 4, gate `T3_grounding`, `before` and `after`, `section_before` and `section_after`, version_number 2, status `ai_generated`, `exported=false`
     - **`content_before` / `content_after`**: the whole versions. Each matches the admin GET before and after the edit exactly.
4. **Tenant view, after.**
   - `my-versions` and `versions/{id}` returned **200** again.
   - highlights[4] now holds the corrected text, and the old sentence appears nowhere (detail, list item or drawer).
   - Same id, same v2, same status `ai_generated`, same edit_source. `edited_at` is still **null**, so the drawer shows no "Edited:" line. version_history is still v1 and v2, and the list total is still 12.
   - Diffing `tenant-before-rewritten_content.json` against `tenant-after-rewritten_content.json` shows exactly one changed line (highlights[4]). The tenant's after-content is identical to the admin's after-content.
   - Screenshots: `tenant-after-1440-my-catalog-list.png`, `tenant-after-1440-my-catalog-drawer-top.png` and `tenant-after-1440-my-catalog-drawer-highlight.png`.

## Verdict per Done-when bullet (T2 path)

| Done-when / scope | Verdict | Evidence |
|---|---|---|
| A repair on an unpublished flagged version means the tenant API returns the repaired text | **MET (live)** | Step 4: `versions/{id}`, the `my-versions` item and the My Catalog drawer all show the corrected highlight, and the old one is gone |
| History has both versions | **MET (live, as whole versions)** | The audit row stores `content_before` and `content_after`, the whole rewritten_content, equal to the admin GET before and after. The T9 row stores only the span. |
| Tenant responses contain no gate or score keys (AA-796 key-walk) | **MET (live)** | A recursive key-walk of both tenant responses, before and after, for gate, score, held, flag, repair, ledger, violation, quality, blocking, problem, qa_, review, escalat and admin found **0 hits**. A value-walk for `needs_review`, held, flagged and blocked also found 0. |
| No flags or held wording visible to the tenant | **MET** | The drawer text and input values contain no held, flag, gate, T3_ or F-code, score, needs review, admin, grounding, "corrected" or "updated version" wording, before or after |
| Silent: no new version, no notice | **MET** | Same version id and number, `edited_at` null, no "Edited:" label, version_history unchanged, `my-versions` total unchanged (12) |
| Admin audit row exists (admin UI) | **MET** | "ADMIN EDITS · 1" in the drawer, plus the audit row fields above |
| Admin UI has a T2 sentence action | **MET (no gap)** | Cut / Rewrite / Edit on flagged rows, plus click-any-sentence in the Text section |
| Already exported means the admin sees an older copy (T2) | **Not tested** | That needs a tenant DOCX export before an admin edit. This run kept the version undelivered on purpose. |
| AI repair that re-passes the gates writes a new version | **Not tested** | No paid Rewrite or AI repair was run, as the task asked |

## Defects / notes

- **No AA-802 defect found on the T2 path.**
- **Note: the stored sentence is not exactly what the admin typed.**
  - `sanitize_replacement` changed " — " to ": ". The response came back with `warnings=[]`, and nothing in the editor told the admin the text would be normalised.
  - The result reads fine. This is likely the house dash rule rather than a bug, but an admin may notice that the text differs from what they typed.
- **Pre-existing defect, not AA-802: the tenant My Catalog drawer always 404s on `GET /api/tenant/v1/tours/pool/{published_tour_id}`.**
  - `catalogApi.ts::fetchPoolTour` calls a route that `api/routers/v1_tours.py` does not have. The only `/pool/{id}` route is `POST …/rewrite`.
  - Reproduced on WildKind with a second tour (`84e392c3…`). The console shows "Failed to load resource: 404" every time the drawer opens.
  - The drawer falls back to the AA original fields from `versions/{id}`, so the tenant sees no visible break. Only the console error appears.
- **Itinerary flag not touched.** The version still has 1 T3_grounding flag in its itinerary ("1954"). It was left alone on purpose: one edit only.

## Test records changed (for later clean-up)

No new rows were created apart from one audit row.

1. **Content change.** `gold_aa_internal.tenant_tour_versions` `b0c7a857-e15c-4ffd-832d-fbf01ecfc5fc` (WildKind Travel): `rewritten_content.highlights[4]` was changed in place.
   - Old: "Dien Bien Phu in the Muong Thanh Valley — site of the 1954 battle that ended French colonial rule in Indochina".
   - The full old content is in `admin-before-rewritten_content.json` and in the audit row's `content_before`.
2. **Audit row.** One row in `acp_shared.audit_log`: action `tenant_tour_version.admin_sentence_edited`, resource_id `b0c7a857-e15c-4ffd-832d-fbf01ecfc5fc`, created_at 2026-10-16T02:14:07.571Z.
