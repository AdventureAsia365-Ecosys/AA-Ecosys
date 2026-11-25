# ZAP baseline triage, S294 (25/11/2026)

Run: `zap-baseline.yml` on branch `fix/s294-zap-single-artifact` (run 45618427353, same scan as master after root
#1027), 7 targets, ZAP 2.17.0, passive only. Public repo: alerts, risk and decision only, no reproduction steps.
Compared with the S283 baseline (`docs/audits/2026-11-17-S283-access-review/zap-baseline.md`).

## Counts per target

| Target | High | Medium | Low | Informational |
|---|---:|---:|---:|---:|
| booking-admin | 0 | 4 | 5 | 1 |
| booking-api-health | 0 | 0 | 1 | 3 |
| cis-admin | 0 | 4 | 5 | 1 |
| cis-api-health | 0 | 0 | 1 | 3 |
| crm-portal | 0 | 2 | 3 | 6 |
| tripplanner | 0 | 4 | 4 | 9 |
| tripplanner-plan | 0 | 4 | 5 | 9 |

## Against S283

- **Gone:** X-Content-Type-Options missing (CIS API, Booking API health).
- **New:** none. Every Medium and Low alert is one S283 already triaged.
- **Still open, decision unchanged:**
  - CSP header not set on the CIS / Booking admin static routes. Real.
  - CSP wildcard and `unsafe-inline`. Real, planned nonce hardening with the kit.
  - HSTS not set on the admin hosts. Real.
  - `Server` version leak. Real, cosmetic.
  - Permissions-Policy and COOP/COEP/CORP missing. Accepted for Dev, review at prod.
  - Debug error messages and big redirect on TripPlanner. Check / likely false positive.
  - SRI missing. Accepted for Dev.

## Next

S294 lane: the safe part of the S283 "security headers" slice. It adds the CSP on every admin response including
static routes, HSTS, no `Server` / `X-Powered-By` header and a minimal Permissions-Policy, with no nonce change. The
nonce-based CSP stays with the kit work. Re-run this workflow after it ships and compare the counts.

## Update after the security-headers lane (S294)

A live `curl` of every admin path (`/`, `/login`, `/robots.txt`, `/sitemap.xml`, a 404) shows the full header set the
apps have sent since S284: nonce CSP, HSTS (two years, sub-domains), Permissions-Policy, COOP, nosniff, and no
`X-Powered-By` or `Server` header. The "CSP / HSTS / Permissions-Policy not set" and `Server: awselb/2.0` alerts on
cis-admin and booking-admin come from ZAP's first requests, which carry no User-Agent. The WAF managed rule
`NoUserAgent_HEADER` (CommonRuleSet) blocks them, and the ALB answers with its own plain 403, which has no headers.
The WAF sampled requests of the scan window show this, and `curl -H "User-Agent:"` reproduces it. The apps never saw
those requests.

- **Real gap fixed:** the CRM API (`/crm/*`) now sends HSTS and nosniff on every response (Partner PR of this lane).
- **Left for Infra:** attach a custom block response carrying the security headers to the CommonRuleSet block action.
  The ALB's own `Server: awselb/2.0` on a response it generates cannot be removed: proposed as accepted.
- The counts for cis-admin and booking-admin will not change on a re-run until that Infra change ships.
