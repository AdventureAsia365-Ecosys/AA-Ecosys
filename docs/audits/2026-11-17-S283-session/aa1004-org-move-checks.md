# Org-move readiness checks, nonprod account (S283, 17/11/2026)

Runbook: `infra/AA-CIS-Infra/docs/runbooks/org-move-readiness-checks.md`, checks 1.2–1.5 and 1.7. Read-only, run from the
admin role of the nonprod account. Script: one `bash` file with the runbook's commands; account numbers masked.

| Check | Result | Reading |
|---|---|---|
| 1.2 Pending invitations | none | Expected before 01/12 (the AA organization has not invited the account yet). |
| 1.3 `LeaveOrganization` / `CloseAccount` | `allowed`, `AllowedByOrganizations = True` for both | No reseller SCP denies leaving, as far as the simulator sees (it skips SCP conditions on context keys it is not given). Strong evidence, not proof. |
| 1.4 Create `OrganizationAccountAccessRole` (`CreateRole`, `AttachRolePolicy`, `PutRolePolicy`, `TagRole`) | all `allowed`, `True` | Technically the local apply of README §6 step 2 could run before the move. It stays on hold anyway: the tech lead holds it until the business owner signs the reseller contract appendix (S282). This is evidence for the hold decision, not a trigger. |
| 1.5 Role exists already | `NoSuchEntity` | Keep `org_access_adopt_existing_role = false`. |
| 1.7 Contact details | primary contact present (country VN); **no BILLING alternate contact** | AWS needs full contact details to let an account stand alone. Add a BILLING alternate contact (role mailbox) before the move; question R4 not needed (no `AccessDenied`). Payment method: root-user console check, not done here. |

Next: the BILLING alternate contact is a hand step for the tech lead (console or `aws account put-alternate-contact`, a
write: not run by the agent). The other checks are unchanged until the invitation arrives (1.2 again after step 5).

## Cost data kept before the move

`aa1004-finops-bundle-2025-10..2026-10.json`: the cost data CIS has stored per month (read through
`tools/finops/collect_month.py`, `PART=cis`, no new Cost Explorer request, account numbers scrubbed). Real AWS totals
start in August 2026 (140.22 USD), September 134.96 + 42.79 AI, October 213.87 + 269.35 AI = 482.73 USD; months before
August read 0 because the platform ran elsewhere then. The dated 25–28/11 export (13 months, by service and App tag,
straight from the account) stays on the AA-1004 plan; this file is the fallback if that date slips.


**Update 17/11 (S283):** the tech lead added the BILLING alternate contact on the console (role mailbox of the company); `get-alternate-contact --alternate-contact-type BILLING` now returns it. Check 1.7 passes.
