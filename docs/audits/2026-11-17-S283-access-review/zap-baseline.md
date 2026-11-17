# ZAP baseline triage (S283, 17/11/2026)

Run: root workflow `zap-baseline.yml` (passive baseline, ZAP 2.17.0, 2-minute spider, dispatch only), run 44030478936,
7 Dev entry points. Summary produced with `tools/security/zap_summary.py`. Reports stay in the run artifacts (7 days);
this page names alerts, risk and decision only (public repo: no reproduction steps).

## Counts

| Target | High | Medium | Low |
|---|---:|---:|---:|
| CIS admin | 0 | 5 | 6 |
| CIS API health | 0 | 0 | 3 |
| Booking admin | 0 | 5 | 6 |
| Booking API health | 0 | 0 | 3 |
| CRM web (portal host) | 0 | 2 | 3 |
| TripPlanner (AA site) | 0 | 4 | 6 |
| TripPlanner (agency planner) | 0 | 4 | 6 |

**No High.** No finding needs an emergency fix.

## Triage

| Risk | Alert | Where | Decision | Owner | Proposal |
|---|---|---|---|---|---|
| Medium | CSP header not set | CIS admin (`/sitemap.xml`), Booking admin (page, robots, sitemap) | **Real** | CIS, Booking admin | Send the same CSP on every response of the Next.js admin, including static routes (middleware or `next.config` headers). S |
| Medium | CSP wildcard directive; `script-src` / `style-src` `unsafe-inline` | CIS admin, Booking admin, TripPlanner, CRM web | **Real, planned hardening** | each frontend | Move to nonce-based CSP (Next.js supports it) and drop wildcards; needs a kit-wide check of inline styles. M per app; do with the kit sync |
| Medium | Sub Resource Integrity missing | all frontends | **Accepted for Dev** | — | Scripts are first-party chunks served from the same origin; SRI adds value only for third-party CDNs. Re-check at prod if any third-party script is added |
| Low | HSTS not set | CIS admin, Booking admin, both API health endpoints | **Real** | Infra (API Gateway / CloudFront) + Next.js headers | Add `Strict-Transport-Security` at the edge for every host. S |
| Low | X-Content-Type-Options missing | CIS API, Booking API health | **Real** | CIS, Booking API | Add `nosniff` in the API middleware. XS |
| Low | Server version leak | CIS admin, Booking admin, TripPlanner | **Real, cosmetic** | Infra / Next.js | Strip the `Server` header (`poweredByHeader: false` and edge rule). XS |
| Low | COOP / COEP / CORP missing; Permissions-Policy not set | all | **Accepted for Dev, review at prod** | each frontend | Add COOP `same-origin` and a minimal Permissions-Policy with the CSP work; COEP only if it does not break maps/images |
| Low | Debug error messages / application error disclosure | TripPlanner | **Check** | TripPlanner | Look at the 404/500 bodies the spider hit; make sure no stack or framework detail is returned. S |
| Low | Big redirect detected | TripPlanner agency planner | **Likely false positive** | — | Redirect body carries the page shell; verify nothing sensitive is in it at the next pass |

## Follow-up

A "security headers" slice across the four frontends and the two APIs (CSP everywhere + nonce, HSTS at the edge,
`nosniff`, no `Server` header, Permissions-Policy) is proposed on the S283 close decision page. Re-run this workflow
after it ships and compare counts.
