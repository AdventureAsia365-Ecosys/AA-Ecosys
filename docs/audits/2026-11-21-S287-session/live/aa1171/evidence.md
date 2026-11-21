# AA-1171 — Alerts catalogue P0: live evidence (21/11/2026)

Checked on Dev after CIS #1636 (`1be86655`) and the follow-up CIS #1637, by the orchestrating agent and a verify
workflow (UI / API lane as the E2E CIS administrator, read-only; infra lane read-only on AWS; an adversarial review).
Account IDs, ARNs and e-mails are masked. Raw files stay in the private session scratch.

| Done-when | Result | Evidence |
|---|---|---|
| 1. Catalogue lists every alarm, rule and in-app check; counts match a live read | **PASS.** 123 rows: CloudWatch 37 (32 metric, 5 metric math), EventBridge 15, budgets 11, cost anomaly 5, in-app 55 (CIS 34, Booking 2, CRM 19). AWS read: 37 metric alarms, 0 composite; 16 rules of which 15 notify SNS (the 16th only logs). Missing: none, extra: none; App and Severity match the AWS tags on all 37 alarms; 0 rows without app, type or severity. | UI lane `catalogue-raw.json` (11:22 UTC), AWS reads |
| 2. Apps health groups by App tag, with a total | **PASS.** `alarms_grouped_by = tag`; CIS 4, TripPlanner 6, Booking 4, CRM 6, shared 17, total 37 = the AWS App tags (CIS was 8 by name prefix; 4 is right after the new worker and 5xx alarms). | `aa1171-01-apps-health-by-tag.png` |
| 3. A threshold changed in Settings changes the check | **PASS.** `cis.ops.xid_age_limit` 1,000,000,000 → 500,000,000 through the settings registry service (propose + approve, maker-checker, self-approved because two-person approval is off on Dev, audited), held 120 s, then restored (v2 = 1,000,000,000). `rds_xid_age` on a synthetic measure of 750,000,000: OK before, **ALARM with threshold 500,000,000** after, OK after the restore; the live measure (4.56 M) stayed OK, so no real alert fired. Read from outside during the hold: the running api's catalogue row showed "500000000 transactions" from 11:34:21 to 11:35:57 UTC and "1000000000" again at 11:36:12; the Settings page showed version 1 with the reason. Limit: the write went through the service functions, not a click on the page (the E2E administrator is read-only); the page and its router call the same functions. | `aa1171-02-settings-xid-during-proof.png`; script output 11:33–11:36 UTC |
| 4. The page topic exists; page alarms notify it | **PASS.** `aa-ecosys-dev-page-alerts` exists; all 11 Severity=page alarms have it in their actions, no ticket alarm does. It has no subscriber yet (D6: no paging tool on Dev; prod adds recipients). | infra lane |
| 5. Delivery-failed alarm and the coverage alarms exist in OK | **PASS.** alerts-delivery-failed, CIS worker no-running-task, Booking worker silent, CIS API 5xx rate, Booking API 5xx rate: all OK at 11:25 UTC. Booking worker-silent showed ALARM for 5 minutes at creation (missing data counts as breaching) and then OK. | infra lane, review |
| 6. `docs/generated/alarms.md` has no resource ID suffix | **PASS** after root #936 (`b81ab55f`): only the generator SHA and fingerprint header lines carry hex runs. | `git show origin/master:docs/generated/alarms.md` |
| 7. No issue IDs in the UI; English by default | **PASS after CIS #1637** (`15814d6e`, re-check 12:11 UTC): the first read found 31 rows (17 alarms, 14 rules) showing 14 tracker IDs copied from the Terraform descriptions; after #1637 the API and the page text show 0 (all 123 rows). English by default (`lang="en"`). The re-check also saw the CRM rows on a cold read (19, 2.6 s) and Apps health saying "CloudWatch alarms". | UI lane; re-check; #1637 tests |

Follow-ups found by the check and fixed in #1637: the CRM registry read used a 2 s timeout (one cold call took 3.8 s and
hid the 19 CRM rows), the peer section was cached 300 s (now 30 s), and Apps health said "automatic checks" while it
counts CloudWatch alarms only.

Left for later (not in the Done-when): a recipient on the page topic before prod; a delivery-failed alarm on the page
topic too; remove the tracker IDs from the Terraform descriptions themselves (the catalogue already hides them); the
condition text of the anomaly-band alarm (CRM KMS decrypt anomaly) renders as "above band None (; over DecryptCalls)".
