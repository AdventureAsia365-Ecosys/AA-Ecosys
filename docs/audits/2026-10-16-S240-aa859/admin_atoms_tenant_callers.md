# `/admin/atoms*` with a tenant JWT: who called it in the last 30 days

AA-859, S240. Nghiệp's decision: look at 30 days of logs. If **no** request reached `/admin/atoms*` with a
tenant JWT, a later PR removes the tenant branch of `api/routers/admin_atoms.py` outright (no flag).
This file says which logs can answer that, gives the exact read-only commands, and says how to read them.

## 1. What the API itself records per request

| Source | What it has | What it lacks |
|---|---|---|
| `api/routers/admin_atoms.py` | Auth is `_resolve_atom_owner_scope` (`:74-89`): a `Bearer` token is tried **first**, and `X-Admin-Secret` is only checked when no Bearer header is present. The routes log only `atom_delete_recompute_enqueued` / `atom_delete_outcome` (PATCH delete). | Nothing logs which auth branch ran, or the tenant id. |
| uvicorn access log (stdout → ECS `/ecs/aa-cis-dev`, stream `api/api/<task>`) | One line per request: `INFO: <ip>:<port> - "GET /admin/atoms?… HTTP/1.1" 200 OK`, with method, path, query and status. | No headers, so no auth kind or tenant. |
| `rate_limit_middleware` → `_track_admin_call` (`api/middleware/rate_limit.py`) | For `/admin/*`, a row in **`shared.tenant_api_usage`** (`actor_type = 'admin'`, `endpoint` = path, method, status, `called_at`) **only when `X-Admin-Secret` matches**. A Bearer-only request is passed through and not recorded. 90 days of raw rows (retention job, AA-825). | Tenant-JWT calls to `/admin/*` are never recorded. A request carrying both headers is recorded as admin but served by the tenant branch. |
| `sentry_context_middleware` | Sentry tags `route` and `x-tenant-id`. The BFFs never send `x-tenant-id`. | Only errors, and no auth kind. |

**On their own, the API logs cannot tell tenant from admin.** There are two ways around that: count by
header name at the WAF (§2), or compare the access log with the admin-only DB rows (§3).

## 2. Logs that exist (AA-CIS-Infra, read 16/10/2026)

| Log | Where defined | Retention | Shows the auth header? |
|---|---|---|---|
| **WAF `aws-waf-logs-aa-cis-dev`** | `modules/waf/main.tf:214-238`, web ACL on the **ALB** (`:197`). The REST-stage association is off: `waf_protect_rest_api_stages` is false by default and not set in `terraform.tfvars`. The ALB is public (`modules/alb/main.tf`, `internal = false`). | **30 days** | **Yes, by name.** Every request header is logged. Since AA-806 (#145, 16/10/2026) the *values* of `authorization`, `x-admin-secret`, `x-api-key` and `cookie` show as `REDACTED`, but the header *names* are still there. |
| ECS `/ecs/aa-cis-dev`, prefix `api/` | `modules/ecs/main.tf:250-252, :333-335` | **14 days** | No (access line only) |
| API Gateway execution logs `API-Gateway-Execution-Logs_<api-id>/dev` | `modules/api_gateway/main.tf:433-445` (INFO, `data_trace_enabled = false`), `accounts/aa365/observability_ecosys.tf:86-88` | 14 days | No: request headers are logged only with data trace on. No API GW access log is configured. |
| ALB access logs, S3 diag bucket | `accounts/aa365/main.tf:151`, `diagnostics.tf:129-139` | 7 days | No (request line and user agent only) |
| Vercel runtime logs of the CIS frontend | tenant BFF `frontend/app/api/tenant/[...path]/route.ts` | short; depends on the Vercel plan (around 1 day on Pro without Observability Plus; check the plan) | Only the path `/api/tenant/admin/atoms`. That route has a staff branch too (a `cis_admin_token` session sends `X-Admin-Secret`), so the path alone is not proof. |

**The 30-day window is only fully covered by WAF.** ECS covers the last 14 days and can confirm what
WAF finds.

Code context: since AA-526 (#309, 05/09/2026) the portal has no `/admin/atoms` caller
(`(tenant)/portal/layout.tsx:31`, `_components/Sidebar.tsx:32`), so the whole 30-day window falls after
that change. The tenant BFF still forwards **any** path with the tenant's Bearer, so a tenant session (or
anyone holding a tenant JWT and calling `api-cis` directly) can still reach `/admin/atoms`. That is
why this check is needed. The portal does call `/api/tenant/admin/brand-identity` with a tenant JWT
(`BrandTab.tsx:126`) by design, so the filters below match `/admin/atoms` only, never all of `/admin/*`.

## 3. Commands (read-only; profile `aa365-admin`, `us-west-1`, single line each)

⚠️ The WAF log rows written **before the #145 redaction was applied** contain plaintext tenant JWTs and
the BFF `X-Admin-Secret`. Every query below returns **only aggregates** (`stats`). Never add
`fields @message`, never `display` a header and never export raw WAF events.

Set the time window first (seconds since the epoch):

```bash
NOW=$(date +%s); S30=$(date -d '30 days ago' +%s); S14=$(date -d '14 days ago' +%s)
```

Each `start-query` prints a query id. Wait 30–90 s, then fetch the result once
(`aws logs get-query-results --query-id <id> --profile aa365-admin --region us-west-1 --output json > qN.json`)
and check `"status": "Complete"`. Logs Insights costs about $0.005–0.006 per GB scanned. Q0 shows the
stored size first.

**Q0: the log groups, their retention and size; WAF logging config and redaction**
```bash
aws logs describe-log-groups --log-group-name-prefix aws-waf-logs-aa-cis-dev --profile aa365-admin --region us-west-1 --query 'logGroups[].{name:logGroupName,retentionDays:retentionInDays,storedBytes:storedBytes}' --output table
aws logs describe-log-groups --log-group-name-prefix /ecs/aa-cis-dev --profile aa365-admin --region us-west-1 --query 'logGroups[].{name:logGroupName,retentionDays:retentionInDays,storedBytes:storedBytes}' --output table
aws wafv2 list-web-acls --scope REGIONAL --profile aa365-admin --region us-west-1 --query 'WebACLs[].{name:Name,arn:ARN}' --output table
aws wafv2 get-logging-configuration --resource-arn <ARN of aa-cis-dev-waf from the line above> --profile aa365-admin --region us-west-1 --query 'LoggingConfiguration.{dest:LogDestinationConfigs,redacted:RedactedFields,filter:LoggingFilter}' --output json
```
Expected: WAF retention 30, ECS retention 14. The logging destination is `aws-waf-logs-aa-cis-dev`, and
there is **no `LoggingFilter`** (a filter that drops ALLOW requests would make every count below 0).

**Q1: WAF coverage per day (no day without events)**
```bash
aws logs start-query --log-group-name aws-waf-logs-aa-cis-dev --start-time $S30 --end-time $NOW --query-string 'stats count(*) as events by bin(1d) as day, httpSourceName | sort day asc' --profile aa365-admin --region us-west-1 --query queryId --output text
```

**Q2: every `/admin/atoms*` request in 30 days, by auth header present (the main answer)**
```bash
aws logs start-query --log-group-name aws-waf-logs-aa-cis-dev --start-time $S30 --end-time $NOW --query-string 'fields httpRequest.uri as uri, httpRequest.httpMethod as method, httpSourceName as src, action | filter uri like /^\/admin\/atoms/ | parse @message /(?i)"name":"(?<h_bearer>authorization)"/ | parse @message /(?i)"name":"(?<h_admin>x-admin-secret)"/ | fields ispresent(h_bearer) as has_bearer, ispresent(h_admin) as has_admin_secret | stats count(*) as n, min(@timestamp) as first_seen, max(@timestamp) as last_seen by src, action, method, has_bearer, has_admin_secret' --profile aa365-admin --region us-west-1 --query queryId --output text
```

**Q3: detail of the tenant-JWT candidates only (Bearer present, no admin secret), per day**
```bash
aws logs start-query --log-group-name aws-waf-logs-aa-cis-dev --start-time $S30 --end-time $NOW --query-string 'fields httpRequest.uri as uri, httpRequest.httpMethod as method, httpRequest.clientIp as ip, action | filter uri like /^\/admin\/atoms/ | filter @message like /(?i)"name":"authorization"/ | filter @message not like /(?i)"name":"x-admin-secret"/ | stats count(*) as n by bin(1d) as day, action, method, uri, ip | sort day asc' --profile aa365-admin --region us-west-1 --query queryId --output text
```

**Q4: positive control. The same classification on `/admin/brand-identity`, which the portal calls with a tenant JWT**
```bash
aws logs start-query --log-group-name aws-waf-logs-aa-cis-dev --start-time $S30 --end-time $NOW --query-string 'fields httpRequest.uri as uri, action | filter uri like /^\/admin\/brand-identity/ | parse @message /(?i)"name":"(?<h_bearer>authorization)"/ | parse @message /(?i)"name":"(?<h_admin>x-admin-secret)"/ | fields ispresent(h_bearer) as has_bearer, ispresent(h_admin) as has_admin_secret | stats count(*) as n, min(@timestamp) as first_seen, max(@timestamp) as last_seen by action, has_bearer, has_admin_secret' --profile aa365-admin --region us-west-1 --query queryId --output text
```

**Q5: ECS access log, `/admin/atoms*` per day, method and status (last 14 days)**
```bash
aws logs start-query --log-group-name /ecs/aa-cis-dev --start-time $S14 --end-time $NOW --query-string 'fields @message | filter @logStream like /^api\// | filter @message like /"[A-Z]+ \/admin\/atoms/ | parse @message /"(?<method>[A-Z]+) (?<path>\/admin\/atoms[^ ?"]*)[^"]* HTTP\/[0-9.]+" (?<status>\d{3})/ | stats count(*) as n by bin(1d) as day, method, status | sort day asc' --profile aa365-admin --region us-west-1 --query queryId --output text
```

**Q6: ECS, `tenant_api_usage` write failures that would skew the §3 comparison (last 14 days)**
```bash
aws logs start-query --log-group-name /ecs/aa-cis-dev --start-time $S14 --end-time $NOW --query-string 'fields @message | filter @logStream like /^api\// | filter @message like /Billing track error/ | stats count(*) as n by bin(1d) as day' --profile aa365-admin --region us-west-1 --query queryId --output text
```

**Q7: DB, admin-authenticated `/admin/atoms*` calls per UTC day, method and status (30 days; the table
keeps 90 days of raw rows).** Read-only. RDS is private, so it runs through the S3-mediated ECS exec
pattern; **`p0_preflight.py` carries it as item 6** (same READ ONLY transaction, rolled back), so the P0
run answers it: read `item6_admin_atoms_usage` in the P0 JSON. It is not part of `gate_241_ready`. The
query, for reference:
```sql
SELECT (called_at AT TIME ZONE 'UTC')::date AS day, method, status_code, count(*) AS n
  FROM shared.tenant_api_usage
 WHERE actor_type = 'admin' AND endpoint LIKE '/admin/atoms%' AND called_at >= now() - interval '30 days'
 GROUP BY 1, 2, 3
 ORDER BY 1, 2, 3;
```
The day is taken in UTC so it lines up with the Logs Insights `bin(1d)` of Q5.

## 4. How to read the results

Q2 rows, using the `action = ALLOW` rows only (BLOCK rows never reached the API):

| has_bearer | has_admin_secret | Meaning |
|---|---|---|
| 1 | 0 | **Tenant-JWT caller.** Or a staff JWT sent as Bearer, which `verify_tenant_jwt` answers with 403 "Tenant token required"; Q5's status separates the two for the last 14 days. |
| 1 | 1 | **Also counts as a tenant caller.** The Bearer branch wins in `_resolve_atom_owner_scope`. No BFF sends both today, so investigate any row here. |
| 0 | 1 | Staff (admin BFF `frontend/app/api/admin/[...path]/route.ts`, or the staff branch of the tenant BFF). Expected. |
| 0 | 0 | No credentials → 401. Scanners. Ignore, but note the count. |

`httpSourceName` should read `ALB` only. If an `APIGW` source also appears, the REST-stage association has
been switched on and each request is logged twice: read one source.

**Verdict "zero tenant callers in 30 days"** holds only when all of these are true:
1. Q2 has no ALLOW row with `has_bearer = 1`;
2. Q4 has ALLOW rows with `has_bearer = 1, has_admin_secret = 0`. This proves the header detection works:
   a zero in Q2 is then a real zero, not a broken regex;
3. Q1 shows WAF events on every day of the window, and Q0 shows no `LoggingFilter`;
4. cross-check for the last 14 days: Q5's `status = 200` count per day and method equals the sum of Q7's
   `n` over the rows with `status_code = 200` for the same day and method (± the Q6 failures). Compare
   200 with 200 only: Q7 also holds admin 4xx/5xx rows, which Q5 counts under their own status. If Q5's
   200 is higher than Q7's 200 on a day, that day had successful non-admin calls; look at Q3 for that day.

If (2) fails because there was no brand-identity traffic in the window, open the portal Brand tab once as
tenant A (a normal tenant action) and re-run Q4 for the last hour. Do **not** create a control by calling
`/admin/atoms` with a tenant JWT: that would put a tenant caller into the very window being checked.

If any tenant caller shows up: Q3 gives the day, method, URI and source IP. An IP in the VPC CIDR means the
call came through API Gateway / VPC link (BFF or a direct `api-cis` call). A public IP means a direct call
to the public ALB. Then the tenant branch is not dead, and PR-J's flagged 403 (plan D3) stays the route.

## 5. Limits (say these in the report)
- The look-back is capped by retention: WAF 30 days, so exactly the window asked for and nothing older.
  ECS 14 days, ALB 7 days.
- WAF logs no response status, and the ECS access line has no headers. Only Q2 + Q5 + Q7 together tie
  "who" to "what status", and only for the 14 days ECS keeps.
- Tenant identity is not recoverable from any log: the Bearer value is redacted, and must stay so. The
  question answered is "did any tenant-JWT request reach the route", not "which tenant".
