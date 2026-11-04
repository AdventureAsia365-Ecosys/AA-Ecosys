# AA-1036 R3 slice 1 (Content studio inside the agency web app), live on Dev (S267, 04/11/2026)

Merged: AA-Partner #210 (`93977fff`, merge queue), root #515 (ADR 0010a status line). Deploys: CRM api
`aa-crm-dev-api:127` and web `aa-crm-dev-web:99`, both COMPLETED on `93977fff`.

| Check | Result |
|---|---|
| `portal./healthz` (web) | 200, `service: aa-crm-web`, `git_sha` = merge SHA |
| `/legal/partner-terms`, `/legal/privacy` | 200 (served by the merged web) |
| `/home` without a session | 307 to `/auth/refresh?next=/home` (no 5xx) |
| `/api/healthz`, `/portal/dashboard` | still the studio service `aa-partner-portal` (`66367c11`) until the slice 2 cut-over, as designed |
| E2E CRM owner (Harbour Lights, partner pool + MFA) `/bff/me` | 200, `crm_entitled: true` |
| CRM sidebar "Apps" group | "Trip planner: request add-on"; no Content studio link, because this synthetic agency has no CIS tenant membership (the link shows only with studio access) |

Screenshots: `crm-home-apps-1440-{light,dark}`, `crm-home-390-{light,dark}`, `legal-legal-partner-terms-1440-light`,
`legal-legal-privacy-1440-light`.

Not yet live (slice 2): the ALB host rules move to the web target group, `WEB_CONTENT_HOME`, deletion of the studio
service. Slice 3: tenant API key removal after the 30-day `audit_log` check.
