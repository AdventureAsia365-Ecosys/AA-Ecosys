# AA-1173 live check on Dev: sealed compliance evidence (S290, 24/11/2026)

- Infra #1002 (merge 306da64b), Terraform Apply (dev) run 45357390166 success: evidence bucket with Object Lock
  (default retention GOVERNANCE, 365 days) and the role `aa-cis-dev-compliance-evidence`.
- Repo secrets `COMPLIANCE_EVIDENCE_ROLE_ARN` and `COMPLIANCE_EVIDENCE_BUCKET` set in AA-Ecosys and AA-CIS-Infra
  (09:22Z, by the tech lead's session; values never printed).
- Root "Compliance evidence" run 45364700766: success (collector tests, collect and publish, seal into the bucket).
- Infra "Compliance AWS" run 45364721985: success (nightly AWS checks sealed; the weekly Prowler job runs on its
  schedule only).

## Tamper attempts with the AWS admin profile (09:25Z)

Object under test: `evidence/aws_nightly/bundles/2026/11/24/092432Z-45364721985-1.json` (a sealed bundle).

| Attempt | Result |
|---|---|
| Delete the object version | AccessDenied, explicit deny in a resource-based policy |
| Delete without a version (delete marker) | AccessDenied, explicit deny in a resource-based policy |
| Overwrite (put-object on the same key) | AccessDenied, explicit deny in a resource-based policy |
| Delete the version with `--bypass-governance-retention` | AccessDenied, explicit deny in a resource-based policy |
| Head the version afterwards | still there, ObjectLockMode GOVERNANCE, retain until 2027-11-24 |

No bucket name, account ID or ARN is written here (public repo).

## CIS page live check (AA-CIS-App #1667 `5a9f52d0`, CIS 479), 24/11 about 10:30–11:00 UTC

- Identity: the Dev-only E2E owner on the CIS admin (root ADR 0006a A10h). It is the maker only and is never the
  checker.
- Script: `.tmp-session/S290/closeouts/97_aa1173.cjs`.
- Screenshots are compressed. No addresses are shown.

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Sealed sources on Platform › Compliance readiness | **PASS.** The ingest block of `GET /admin/platform/compliance` shows **root_daily `ok`**: 17 rows, chain `first`, object `evidence/root_daily/bundles/2026/11/24/092431Z-45364700766-1.json`, sha256 `936663e3…`. It shows **aws_nightly `ok`**: 11 rows, chain `first`, object `evidence/aws_nightly/bundles/2026/11/24/092432Z-45364721985-1.json`, sha256 `7d065652…`. prowler_weekly is `missing` (weekly schedule). The docs-reader file is in state **`superseded`**, "the sealed root_daily bundle is read instead". On the page, Collectors shows aws_nightly / cis_db / root_daily "Heard from within 36 h" with their last evidence time. It says "Published evidence file: Not read: the sealed daily bundle replaces the published file", and under "Sealed evidence store": root_daily "17 results read from the newest sealed bundle; hash chain starts here" `936663e389f0`, aws_nightly "11 results …" `7d065652cdf3`, prowler_weekly "Nothing sealed yet". The banner reads "the collectors seal each run in a write-once evidence store (Object Lock, a hash-chained manifest)" | `97-sources.json`, `97-overview__{1440,390}__{light,dark}.png`, `97-collectors__{1440,390}__{light,dark}.png` |
| 2 | Exceptions: maker-checker | **PASS for propose and withdraw.** The own-approve refusal is **not demonstrated, because the switch is off**. `cis.settings.two_person_approval` is **off** on Dev. While it is off, the proposer may approve their own proposal (recorded `self_approved`, the S287 Q13 rule), so the own approve was deliberately **not sent**: it would have left an approved SYNTHETIC accepted risk. One SYNTHETIC exception was proposed: subject `vulnerability` `SYNTHETIC-S290-AA1173-PROBE`, risk low, reason starting "SYNTHETIC", expiry tomorrow; longest allowed is 90 days (`exception_max_days`). It became id 1, state `proposed`. The proposer then withdrew it (`POST …/exceptions/1/revoke` 200), and it is now `revoked`, `self_approved false`. The first withdraw call sent no id (a script bug: the propose answer carries no id field) and got 422; the row was found in the list and withdrawn. Nothing else was written | `97-exception.json`, `97-exceptions-open__{1440,390}__{light,dark}.png`, `97-exceptions-withdrawn__1440__light.png` |
| 3 | Reviews tab | **PASS (read only).** 0 reviews. `current_period` 2026-11-01, `current_recorded false`, `max_age_days` 40. The `monthly_review_recent` check fails with "no Security posture monthly review recorded yet". No review was recorded: there is one real record per month and it cannot be withdrawn, so the first real review is the tech lead's | `97-reviews.json`, `97-reviews__{1440,390}__{light,dark}.png` |
| 4 | Settings | **PASS.** The registry lists 23 `cis.compliance.*` keys, among them the five of CIS 479: `exception_max_days` 90, `review_max_age_days` 40, `prowler_critical_high_max` 0, `validity_hours.aws_nightly` 48, `validity_hours.prowler_weekly` 216. Platform › Settings › Content (CIS) › "Compliance readiness 23" | `97-settings.json`, `97-settings__{1440,390}__light.png` |

Not demonstrated, and what it needs:

- **The proposer's own approve refused, then a second person approving.** This needs
  `cis.settings.two_person_approval` on, plus a second real person (the E2E owner may never be the checker).
- **"The first monthly review record exists" (Done-when).** This is the tech lead's first real review.
