# S288 evidence images: where they live

Only 16 key screenshots stay in this folder. The full set of 65 screenshots is stored outside git, in the private S3
prefix `audit-assets/2026-11-23-S288-session/` of the CIS bronze bucket on acc2. The relative paths are the same as
the links in the `.md` files of this folder (`live/<check>/<file>.png`). The rule comes from the tech lead's decision of
S285 (AA-1161): GitHub holds code and the text that runs or documents the system; images live in their own storage. A
bucket lifecycle rule (`audit-assets-expire-60d`) deletes these copies 60 days after upload (about 22/01/2027):
download anything worth keeping before then.

Read one (single line, AWS admin profile):

```
aws s3 cp s3://<cis-bronze-bucket>/audit-assets/2026-11-23-S288-session/live/<path> . --profile aa365-admin --region us-west-1
```

Personal data: every staff address except the role mailbox `info@` is masked in the images (`t***@adventure.asia`), and
the username of the business owner's row is blacked out.

Kept in git (shown in the S288 Jira drafts or the main checks):

- `live/aa-1149/aa1149-readiness-blocked__1440__light.png`: Price readiness filtered on "Can operate = Blocked"
- `live/aa-1149/aa1149-sell-exception-drawer__1440__light.png`: the "Allow sale…" dialog
- `live/aa-1149/aa1149-case-sold-before-split__1440__light.png`: a trip case sold before tours were split
- `live/aa-1158/suppliers-pending-1440-light.png`: suppliers filtered on "Pending approval"
- `live/aa-1158/home-my-work-1440-light.png`: Booking home with the new approval tiles
- `live/aa-1158/audit-log-self-approvals-1440-light.png`: the "Business-owner self-approvals" audit tab
- `live/aa-1174/r2-compliance-obligations-desktop-light.png`: Compliance readiness › Obligations
- `live/e2e-owner/03b-new-tenant-outcome.png`: test tenant created, CRM agency "Needs a look (crm_unavailable)"
- `live/e2e-owner/06b-compliance-after-refresh.png`: evidence refreshed, `cis_db` and `crm_ops` last seen 22:01
- `live/e2e-owner/07a-cis-view-as-content-no-banner.png`: CIS view-as before the display-cookie fix (no banner)
- `live/e2e-owner/07c-booking-view-as-product-ops-accounting.png`: Booking view-as banner
- `live/e2e-owner/final-1-pricing-policy-group-size-bands.png`: Group size bands in force (v2), final run
- `live/e2e-owner/final-2-pricing-policy-group-size-bands-history.png`: bands version history
- `live/e2e-owner/final-3-cis-view-as-content-banner.png`: CIS view-as banner after the fix (CIS #1651)
- `live/e2e-owner/final-4-cis-view-as-back.png`: after the banner's Back
- `live/e2e-owner/final-5-price-readiness-no-synthetic-tour.png`: no synthetic tour on Dev (sale exception not tried)
