# S285 evidence images: where they live

Only 9 key screenshots stay in this folder. The full set of 300 screenshots (22.6 MB) is stored outside git, in
the private S3 prefix `audit-assets/2026-11-19-S285-session/` of the CIS bronze bucket on acc2. The relative paths
are the same as the links in the `.md` files of this folder. The rule comes from the tech lead's decision of S285
(AA-1161): GitHub holds code and the text that runs or documents the system; images, videos and build files live in
their own storage. A bucket lifecycle rule (`audit-assets-expire-60d`, Infra #943) deletes these copies 60 days after
upload (about 18/01/2027 for this session): download anything worth keeping before then.

Read one (single line, AWS admin profile):

```
aws s3 cp s3://<cis-bronze-bucket>/audit-assets/2026-11-19-S285-session/<path> . --profile aa365-admin --region us-west-1
```

Kept in git (shown in the S285 Jira posts or the main checks):

- `aa1144/recheck-step5-saved-1440.png`: a studio save keeps the agency's own fields
- `aa1126/quota-studio-rewrite-refused-vi-1440-light.png`: AI writing allowance used up (studio)
- `aa1126/quota-crm-settings-ai-vi-1440-light.png`: AI budget used up (CRM)
- `aa1126/quota-tripplanner-bell-1440-light.png`: Trip planner AI allowance notice in the studio bell
- `aa1139/live-crm-owner-rehearsal-after-scope-1440.png`: Trip planner module in the CRM web
- `aa1139/live-studio-key-after-reload-after-scope-1440.png`: signing key after rotation, version and date only
- `aa1127/live-390-settings-cis-spend-light.png`: admin page at 390 px
- `aa1128/recheck-dashboard.png`: Booking staff admin in Vietnamese
- `aa1129-l18/studio-billing-card-vi-1440.png`: the studio's monthly bill card
