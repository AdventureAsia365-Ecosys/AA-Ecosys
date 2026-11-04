---
id: SEC-08-s268-crm-security-review
title: "AA-Partner CRM security review (AA-969, CRM-37a, S268)"
description: "AA-969 independent review of the AA-Partner API and web: 4 major findings fixed with tests, minor follow-ups, d16 pilot protections still open."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [aa-crm-api, aa-crm-web]
last_reviewed: 2026-11-05
related: [AA-969, AA-1028, ARCH-06-partner]
---

# AA-Partner CRM security review (AA-969, S268)

**Scope.** The AA-Partner API (`api/`, FastAPI on ECS) and the agency web (`web/`, Next.js on ECS, the Content studio
merged into it by AA-1036) at AA-Partner `main` of 04/11/2026, read as an independent reviewer (Claude Code lane
`aa969-crm-hardening`, not the author of the reviewed modules). Design source: `docs/audits/2026-10-21-S246-crm-design-v3/design-v3.md`
§6.3 card CRM-37a and the S265 re-scope comment on AA-969 (the review is a pre-condition of real PII on Dev, root ADR
0019 d16).

**Method.** Read the route classes and their guards, the tenancy contexts, every unauthenticated route, the
upload and import paths, every outbound network call, the job runner, the settings and logging, and the web proxy /
BFF; ran the existing guards (route coverage test, DB access lint, isolation and RLS catalogue tests) on a local
PostgreSQL; wrote failing tests for each finding before fixing it. Synthetic data only. Nothing was run against Dev.

**Result.** No blocking finding. Four **major** findings, all fixed in the AA-969 AA-Partner PR with unit and
integration tests (status: fixed once that PR is merged and deployed). Seven minor items, listed as follow-ups.
The d16 pilot protections are not built yet (section 4): they, not this review, gate the first real PII.

## 1. Findings fixed in code

| # | Severity | Area | Finding | Fix |
|---|---|---|---|---|
| F1 | Major | Input / availability | FastAPI reads and parses a route's JSON body **before** it runs the route's dependencies, the class guard included, and neither CloudFront nor the ALB caps a body. An anonymous request to any write route could make the shared API task buffer a body of any size before the 401: one request could take the task, and every agency with it, down. | `app/bodylimit.py`: a pure ASGI middleware caps every body before any route code (1 MiB; the four upload routes their own cap + 64 KiB). A declared length over the cap is answered 413 at once; a streamed body is counted and cut at the cap. |
| F2 | Major | Tenant isolation (availability) | One agency could hold all 3 pooled connections of the task (shared with the job worker) with a burst of requests, and the wait for a connection was unbounded: every other agency's request queued behind it (card R "a noisy tenant cannot push another tenant past the SLO"). | `app/tenant_gate.py`: every `tenant_tx()` first takes one of its agency's slots (default 2 of 3), keyed by the agency only after this caller's membership was verified (naming another agency's id spends only the caller's own slots); 429 `tenant_busy` after 5 s. The pool wait is bounded (503 `db_busy` after 10 s). A per-member-per-agency ceiling on `/crm/v1` (600 a minute, 429). Proven on a real 3-connection pool: a calm agency's request stays under 0.5 s while another agency runs 12 slow requests at once. |
| F3 | Major | Job runner (availability) | The serial `crm.job` worker claimed strictly oldest first: an agency that queued many jobs (a client import in batches, a mail history import) held every other agency's intake and message jobs behind its whole backlog. | `app/jobs/queue.py`: the claim is fair per agency (rank inside the agency + the agency's jobs served in the last 5 minutes; oldest first inside an agency; platform jobs never wait behind an agency). Every due row is ranked inside its agency, with no global oldest-N window, so the guarantee holds whatever the length of one agency's backlog. Integration tests: 30 queued jobs of one agency, the other agencies' jobs run within the first four claims; 600 older due jobs of one agency, the other agency's job is claimed within the first two. |
| F4 | Major | Secrets in logs | The `request_completed` log line wrote the full path, and several public routes carry a bearer credential in the path (signed client links, calendar feed tokens, webhook ids). Anyone able to read the API logs could open a client's planning form or proposal page. Sentry was already scrubbed; the log line was not. | `app/observability/request_id.py` `redact_path`: path segments of 32+ URL-safe characters that are not a UUID are logged as `[token]`. The rotation of links that were logged before the fix is in the follow-ups (M1). |

Card E "a Spot interruption loses no jobs": checked and covered by tests, no change needed. The API service keeps its
first task on on-demand Fargate (`base = 1`), extra tasks may be Spot. A Spot interruption is a SIGTERM; the lifespan
gives the running job 20 s, then cancels it and **releases** the row (back to the queue, due now, the attempt not
counted). A task that dies without that (SIGKILL) leaves the lease to expire and the reaper re-queues the row. Jobs
are inserted in the same transaction as the data they act on, so nothing is lost between a request and the queue. A
job interrupted three times in a row ends `failed`, visible in the L1 console and the ops checks, never silently
lost. New integration tests: the release-and-resume path and the repeated-interruption path.

## 2. Areas reviewed with no finding

| Area | What was checked |
|---|---|
| Authentication | One multi-issuer RS256 verifier (byte copy of the CIS verifier, CI-checked): algorithm pinned, `exp` with bounded leeway, `iss`, `token_use = access`, client id per configured pair; issuers and clients only from the environment; a JWKS fetch refuses redirects. The deploy gate checks the GitHub OIDC repository, ids, ref, environment, event and exact workflow ref. |
| Authorisation per route | Every route sits on a class router whose guard runs first (`class_router`; a unit test walks every served path with foreign tokens). The agency class checks membership on every request inside `tenant_tx()` (by token `iss` + `sub`, never e-mail) and the permission matrix (`action=` is mandatory, lint-checked). Ops writes need `crm-platform-admin`; the Dev-only E2E staff identities are read-only / synthetic-only, refused outside Dev. |
| Tenant isolation | FORCE row level security on every tenant table with `tenant_isolation` (catalogue test), `crm_app` NOINHERIT reaching readers only by `SET LOCAL ROLE` from an allow-list, the DB access lint (no query outside a tenancy context), one narrow context per public entry (form key, link hash, feed hash, hook id), each opened by one module only. Cross-schema grants are absent both ways (isolation probe). |
| Input validation | Pydantic models with lengths and enums on every body; uploads typed by magic number, size-capped; the CSV / .xlsx import reads every zip member through a byte budget (no zip bomb) and the XML parser does not resolve entities; CSV exports carry the spreadsheet-formula guard. |
| SSRF | The only host an agency chooses is its SMTP server: resolved once, refused unless the address is global, then pinned for the connection (no DNS rebinding). Every other outbound call goes to fixed hosts (Booking, CIS, the mail providers' APIs, Twilio, the FX sources), https only. |
| Webhooks and public routes | Twilio callbacks are verified with the agency's own token before anything is stored; public writes check Origin, a honeypot and consent, and are rate-limited per address (the viewer address set by CloudFront, IPv6 per /64) and per form; signed links are stored as SHA-256 and answer one 404 for any unusable link. |
| Secrets | Settings mark every secret field out of `repr`; logs and Sentry pass a scrubber (keys, patterns, the F3 detectors); job rows hold ids only (payload guard). |
| Web | Host routing, the BFF allow-list, a cross-site write refusal on every write route (checked), httpOnly sealed session cookies, CSP `frame-ancestors 'none'` (the inquiry form widens it to its own allowed origins), HSTS, `nosniff`, `X-Frame-Options`, no-referrer on the link pages. |

## 3. Minor findings (follow-ups, not fixed here)

| # | Area | Follow-up |
|---|---|---|
| M1 | Secrets in logs | Rotate or expire the client links and calendar feeds issued before F4 is deployed (their tokens may sit in the API log group, 30-day retention); on Dev these are synthetic, so expiry is enough. Before real PII, check that no edge or load balancer access log keeps full URLs of the client host. |
| M2 | Web | The CRM BFF reads a JSON body whole before comparing it with its 256 KiB cap (signed-in users only, and bounded by the proxy's own clone limit). Read it capped, as the raw upload route already does. |
| M3 | Rate limits | Every limiter is per task, in memory: two tasks during a deploy double the ceilings. Accepted on Dev; the WAF of root ADR 0019 (its own cost yes) is the shared ceiling for the pilot. |
| M4 | Job runner | An agency can start any number of client imports and mail history imports (each up to its size cap). F3 keeps the queue fair; a per-agency cap on imports in flight would also bound the storage. |
| M5 | Job runner | A job whose last attempt is cut by a hard kill (no graceful release) ends `failed` ("lease expired, no attempts left"). It is visible and three kinds can be retried from the L1 console; consider not counting an attempt that ended by lease expiry. |
| M6 | Mail | The OAuth mail provider transport follows HTTP redirects (fixed provider hosts, so low risk); refuse redirects as the JWKS fetch does. |
| M7 | Load test | The bounded load test (`AA-Partner loadtest/`) has not run against Dev yet; its result is the live evidence for card R. |

## 4. Root ADR 0019 d16 pilot protections (AA-969 re-scope, S265)

Read in AA-Partner `main` at review time; each must be built and verified live before the first real PII:

| # | Protection | State at review |
|---|---|---|
| 1 | Dev refuses real agencies except the one pilot-marked agency | Not in AA-Partner code yet (no pilot marker); planned in R1 (AA-1028). Synthetic-only rules exist today (seeder, E2E staff identity). |
| 2 | A hook blocks agent and DB Migrate run-script reads of pilot-agency PII (counts only) | Not found in this review's scope (root hooks / Infra); to build. |
| 3 | Clean-up, E2E and wave jobs skip the pilot agency | Not built (needs the marker of 1). |
| 4 | A nightly per-agency export of the pilot agency through the export job | The portability export exists (AA-967); the nightly schedule for one agency is not built. |
| 5 | A one-agency restore drill | Not run. |

Rule for the pilot window (from the same comment): every CRM card that ships while the pilot runs gets a security
review before it is enabled for the pilot agency.

## 5. SLOs and load test (the other half of CRM-37a)

- SLOs: AA-Partner `docs/operations/slo.md` (availability 99.5 %, 5xx < 2 % per 5 minutes, p95 per route group,
  crm.job lag < 120 s at p99 and never > 900 s). Alarms: AA-CIS-Infra `modules/environment/crm_slo.tf` (5xx rate and
  p95 latency on the API target group, 0.30 USD a month) plus four saved Logs Insights queries (free until run).
- Bounded load test: AA-Partner `loadtest/` (k6 + a Python runner with fail-closed guards; 50 synthetic agencies,
  read-only, at most 30 requests a second for at most 10 minutes, hard stop when `shared.job` or `booking.job` is not
  idle or a job-lag check fires). Run by the orchestrator only; its runbook is `loadtest/README.md`.
