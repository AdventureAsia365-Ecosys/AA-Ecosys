# AA-818: custom domains, final config and live verify (S239, 16/10/2026)

Agent: Claude Code (orchestrator). The credentials used (TripPlanner API key, e2e admin) were read from Secrets Manager at
run time. They were never printed or saved.

## Config changes made

**Vercel `aa-tripplanner`** (team `pqnghiep1354-5974s-projects`):
- `BROWSE_API_URL` and `TRIP_API_URL` (production, preview and development) now point at
  `https://api-tripplanner.lumiguides.it.com`, a bare host as before.
- New production variable `NEXT_PUBLIC_SITE_URL` = `https://tripplanner.lumiguides.it.com`.
- Before switching: `/browse/search?q=temple` returned the same bytes from the execute-api host and the custom domain
  (8,008 B, md5 `bc35ecae…`).

**Vercel `aa-booking-admin`**: new variable `BOOKING_API_URL` = `https://api-booking.lumiguides.it.com` (all targets).
Before this the project had no env at all and used the code default, the execute-api `/dev` URL.

**Both projects** were redeployed to production with `vercel redeploy --target production`.

**Infra #149**: `booking_staff_admin_url` default changed to `https://booking.lumiguides.it.com`.
- Applied with a targeted plan on `aws_ecs_task_definition.booking`: 1 add / 1 destroy, revision 16 replaced. The service
  was on revision 19, so the replaced revision was not in use.
- AA-Booking `deploy-dev` was then run (run 38856217987, success). The service is now on `aa-booking-dev-api:21`,
  `STAFF_ADMIN_URL=https://booking.lumiguides.it.com`, rollout COMPLETED.

## Live checks (Done-when)

| Check | Result |
|---|---|
| TLS on the 4 hosts | Valid, `ssl_verify_result=0`. tripplanner (Vercel, until 13/01/2027); booking (Vercel, until 14/01/2027); api-booking and api-tripplanner (ACM, one certificate with both SANs, until 30/04/2027) |
| TripPlanner canonical | `rel="canonical" href="https://tripplanner.lumiguides.it.com"` |
| TripPlanner sitemap | `<loc>https://tripplanner.lumiguides.it.com/…` |
| TripPlanner BFF on the new API host | `/api/browse?resource=search&q=temple` 200 (8,008 B); `resource=countries` 200 |
| Booking `/booking/health/ready` | 200 `{"status":"ok","db":"ok","schema_version":"bk-011"}` |
| Booking staff sign-in on booking.lumiguides.it.com | `/api/auth/login` 200, then `/api/booking/trip-cases?limit=5` 200, total 8 (`trip-cases.json`, customer fields removed) |
| Booking Cases page in a browser | `booking-cases-1440.png` and `booking-cases-390.png`: TC-000001..008 visible, no horizontal scroll (`booking_cases.mjs`) |
| Mapbox token from the new host | Style request with `Referer: https://tripplanner.lumiguides.it.com/` returns 200 |

## Not done here

- **Mapbox token URL restriction.** The public token currently has no URL restriction: a request with an unrelated
  Referer also gets 200. Adding the allowed URLs (`tripplanner.lumiguides.it.com`, `aa-tripplanner.vercel.app`,
  preview URLs) is a Mapbox account setting, and this session has no access to that account.
- **Cognito callback URLs (ADR 0006).** No Cognito user pool exists on acc2 yet, so there is nothing to configure.
