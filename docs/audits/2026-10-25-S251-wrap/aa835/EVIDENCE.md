# AA-835 — live proof on Dev (S251, 25/10/2026)

Synthetic Booking hotel HTL-000003 ("SYNTHETIC S251 AA-835 Evidence Riverside Lodge") and one activity service, supplier
"SYNTHETIC S251 AA-835 Evidence Supplier". Runbook: `RUNBOOK.md` (account ids / ARNs masked).

| Step | Result |
|---|---|
| S1 first run | 3/3 drafts failed "reply is not JSON" ($0.011): route `sonnet` (legacy key) ignored `json_schema` |
| Fix | CIS #1016 (55e24026) gateway + migration 282 (route → `sonnet-5-5`), Infra #395, DB Migrate apply; schema 282 |
| Redraft | hotel + service drafts `succeeded` on sonnet-5-5 (~$0.005 each), faithful to the facts (trial gate passed) |
| S2 publish + read-back | Booking content `published`, description yes, highlights 5; proposal texts hotel + service; proposal items carry the text |
| S4 rename (first run) | v2 applied (facts 3), v3 skipped_older, entity stale, new draft queued |
| S5 replay | rewind + pull: duplicate 4, applied 0, UNCHANGED True, REPLAY_OK True |
| S6–S8 photo | rights off → no copy; rights on → draft v5 with 1 photo → published |
| S7 409 | not run cleanly (probe before CIS pulled the photo event: `unknown_media` 422) — covered by unit tests only |
| S9/S11 deactivate | hotel and service `active False`, `unpublished`, read-back description NULL, no draft job |
| S10 rights withdrawn | `supply_media_purge` succeeded; CDN 403, bronze object 404 |
| UI (Nghiệp's screenshots, `ui/`) | Booking hotel drawer "Customer content · FROM CIS · Published · Version 3" + "Edit in CIS" (desktop, 390 px); CIS `/admin/supply-content/<entity>` PUBLISHED v3, history v1–v3, no-rights photo not copied |
| Cost | 6 writer calls today, $0.025 |

The hotel was re-activated and published (v3) for the screenshots and left that way (synthetic, Dev).
