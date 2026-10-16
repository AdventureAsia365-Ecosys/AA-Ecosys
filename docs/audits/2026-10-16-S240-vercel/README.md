# Vercel usage, S240 (16/10/2026)

## Actions taken (Nghiệp approved)
- Deleted 5 unused projects: visionserve-bundle-int8, statusboard-ai-frontend, statusboard-ai-backend, aa-acp-portal, cis-agentops.
- Deleted 342 preview deployments older than 7 days (CIS 315, TripPlanner 27; list `.tmp-session/s240/vercel_old_previews.tsv`, `vercel remove --safe`).
- CIS #783: dropped the duplicate deploy-hook job from Deploy Dev (Git integration already deploys main; the hook made a second production deployment per merge).

## Deployment cap (Hobby ~100 / 24 h, team-wide)
- 76 deployments listed in the 24 h before 14:50Z (CIS 46, TripPlanner 22, Booking admin 8; 23 CANCELED by the Ignored Build Step, which still count). Rate-limited at 12:55Z.
- `git.deploymentEnabled` filters by branch, not path, so it cannot skip backend-only PRs. Follow-up: CI-created previews only when `frontend/**` changes, Git-integration previews off.

## Fluid Active CPU (2h05m of 4h in 30 days) — cause and fixes
Source: `vercel api /v2/usage?type=requests` per project + CloudWatch Logs Insights on the backend access log (`/ecs/aa-cis-dev`) for the paths the Vercel proxy routes call. Per-route Vercel metrics and user agents need Observability Plus (not bought).

| Project (16/09–15/10) | Outgoing | Function GB-h | Invocations |
|---|---|---|---|
| aa-cis-frontend | 4.16 GB (96.6 %) | 34.0 (87.6 %) | 180.8k |
| aa-tripplanner | 110 MB | 4.6 | 59.2k |
| aa-booking-admin | 37 MB | 0.13 | 1.7k |

CIS outgoing went from 1–6 MB/day to 93–766 MB/day from 1 Oct (Jobs page, AA-687). Traffic follows VN working hours (open admin tabs, agents, UI smoke), not crawlers.

Top backend paths behind the CIS proxy (3–16 Oct): `POST /auth/verify-admin` 42.2k (20 s verify cache), `GET /admin/notifications/count` 17.8k (Topbar `setInterval` 30 s, runs in hidden tabs), `GET /admin/review-queue` 16.0k (Sidebar + BottomNav, two keys, 60 s each), `GET /admin/job-runner/summary|workers|jobs` ~15k each (Jobs page, 10 s, page size 100 with payload/result).

Fixes, ranked (frontend, need a Vercel deploy):
1. Jobs page: poll only while queued/running, 30 s, page size 25, drop payload/result from the list (load in the drawer). ~25 % of CIS invocations.
2. Shell pollers: Topbar on react-query (pauses hidden tabs) at 120 s; one shared review-queue key, 120–300 s. ~15 %.
3. Admin verify cache 20 s → ~5 min (or local JWT verify).
4. Proxy routes stream the upstream body instead of `arrayBuffer()`.
5. TripPlanner ISR revalidate 1800 s → 6–24 h + tag revalidation on CIS publish (lowest priority, ~12 % GB-h).
