# AA-806 — WAF CommonRuleSet pre-flip test (S239, 16/10/2026)

Agent: Claude Code (lane aa806waf). Read-only AWS (STS acc2 005097885195) + HTTP to Dev.

## Setup

- Web ACL `aa-cis-dev-waf`: CommonRuleSet priority 1, group override **Count**, sub-rule overrides
  `SizeRestrictions_BODY`, `CrossSiteScripting_BODY`; then VpcLinkInternalAllow, RateLimit1000,
  GeoBlockNonAllowed. Associated with the ALB `aa-cis-dev-alb` only (no REST stage). The ALB serves
  CIS (default) **and Booking** (`/booking*` listener rule), so one ACL covers both apps.
- Log group `aws-waf-logs-aa-cis-dev` (30 days). ALB body inspection limit: 8,192 bytes.

## Method (no data changed)

No CIS content endpoint is a true no-op when the current value is re-sent: `PATCH /v1/tours/versions/{id}`
`action=edit` inserts a new version, `PATCH /v1/content-writing/pieces/{id}` writes an audit row, and
`PATCH /admin/tours/{id}/raw` runs the UPDATE. WAF inspects the request before the app routes it, so
every write went to a **random non-existent id** (the app answered 404) with **real Dev content** as
the body:
- the raw itinerary of tour `3fa33633` "Ride the Trail" (8.9 KB),
- the `rewritten_content` of the tenant's latest version (atlas-hearth, 13.4 KB),
- editor-style HTML/markdown: `<p>`, `<ul>/<li>`, `<a href>` with `../` links, `<img src="../...">`,
  blockquote, em/strong, entities, quotes, accented names (Hội An, Huế, Đà Nẵng, São Paulo).

Bodies were sent as raw UTF-8 JSON, like a browser. Before and after hashes were identical for all of
these: the tour's raw, generated and published content, the tenant's my-versions and reviews, and
Booking trip cases, suppliers and the latest 20 audit-log rows (`requests.json` → `unchanged`).

## Results (`waf-matches-test.json`)

| id | write | path via | body B | status | CRS rule that would BLOCK | count-override matches |
|---|---|---|---:|---:|---|---|
| A1 | admin raw tour, real fields unchanged (plain text) | CIS BFF | 10,023 | 404 | — | SizeRestrictions_BODY |
| A2 | admin raw tour, HTML description | CIS BFF | 11,232 | 404 | **GenericLFI_BODY** | SizeRestrictions_BODY |
| A3 | admin generated content, HTML | CIS BFF | 19,927 | 404 | **GenericLFI_BODY** | SizeRestrictions_BODY |
| T1 | tenant version edit, real content unchanged | api-cis | 13,430 | 404 | — | SizeRestrictions_BODY |
| T2 | tenant version edit, HTML summary | api-cis | 14,953 | 404 | **GenericLFI_BODY** | SizeRestrictions_BODY |
| T3 | tenant piece edit, markdown blog | api-cis | 9,903 | 404 | **GenericLFI_BODY** | SizeRestrictions_BODY |
| T4 | = T2 through the portal BFF | portal BFF | 14,953 | 404 | **GenericLFI_BODY** | SizeRestrictions_BODY |
| T5 | = T3 through the portal BFF | portal BFF | 9,903 | 404 | **GenericLFI_BODY** | SizeRestrictions_BODY |
| C1 | small HTML intro (< 8 KB) | api-cis | 1,521 | 404 | **GenericLFI_BODY** | — |
| C2 | large plain text, no markup | api-cis | 17,528 | 404 | — | SizeRestrictions_BODY |
| C3 | C1 with every `../` link made absolute | api-cis | 1,590 | 404 | — | — |
| C4 | one markdown link `](../destinations/...)` | api-cis | 75 | 404 | **GenericLFI_BODY** | — |
| C5 | one markdown link `](./destinations/...)` | api-cis | 74 | 404 | — | — |
| C6 | prose with `...`, `/`, `km/h`, `and/or` | api-cis | 119 | 404 | — | — |
| C7 | one `<a href="../...">` | api-cis | 91 | 404 | **GenericLFI_BODY** | — |
| C8 | one `<img src="../...">` | api-cis | 81 | 404 | **GenericLFI_BODY** | — |
| B1 | Booking trip case notes (staff) | api-booking | 9,896 | 404 | **GenericLFI_BODY** | SizeRestrictions_BODY |
| B2 | Booking contract terms (staff) | api-booking | 11,844 | 404 | **GenericLFI_BODY** | SizeRestrictions_BODY |

All test requests: final action ALLOW (terminating VpcLinkInternalAllow). `CrossSiteScripting_BODY`
never matched the typical HTML. No other sub-rule matched.

**Count window** (`waf-matches-count-window.json`): 70,869 requests from 14/10 00:00Z to 16/10 04:01Z.
138 had CRS labels (132 NoUserAgent_HEADER, 6 UserAgent_BadBots_HEADER). All were scanner GETs
straight to the ALB's public IPs between 14/10 00:33 and 01:56Z, before the ALB SG was narrowed to
10.2.0.0/16. **0 matches since then**, and no real write was over 8 KB: the largest POST body was
2,760 B.

## Go / no-go for `waf_common_rules_count_only = false`

- **NO-GO as the config stands.** `GenericLFI_BODY` would 403 every content save that has a relative
  `../` link in its first 8 KB. That covers CIS admin raw and generated edits, tenant version and
  piece edits (direct and through the BFF), and Booking notes and contract terms.
- **GO with one override:** add `GenericLFI_BODY` to `managed_rule_count_overrides`. `SizeRestrictions_BODY`
  and `CrossSiteScripting_BODY` stay in COUNT. `GenericLFI_QUERYARGUMENTS` and `GenericLFI_URIPATH` still
  block.
- Tighter option for later (not done): keep GenericLFI_BODY in COUNT and add a label-match
  block rule (`awswaf:managed:aws:core-rule-set:GenericLFI_Body`) that skips the content-write
  paths. It would need a priority between CRS (1) and VpcLinkInternalAllow (2), which means
  renumbering the rules.

## Security finding (fixed on the branch)

The WAF log keeps every request header in plain text. Today it holds these:
- `Authorization`: tenant JWTs and Booking staff JWTs.
- `X-Admin-Secret`: the static Vercel BFF → API service secret.

Any principal with logs read in acc2 can read them, including `ReadOnlyAccess` on the PR plan role.
The branch adds `redacted_fields` for authorization, x-admin-secret, x-api-key and cookie. Lines
already written keep the values for up to 30 days, so **rotate ADMIN_SECRET** after the apply.

## Branch (AA-CIS-Infra, local only, not pushed)

`feat/aa806-waf-enforce` (worktree `.tmp-session/wt/aa806waf`, base origin/main 3536789):
- `7eb88cf` fix: redact credential headers in the WAF log
- `1a55664` feat: enforce the WAF CommonRuleSet, keep GenericLFI_BODY in count

Checks: `terraform fmt -check` (modules/waf, accounts/aa365) ok, `terraform validate` ok. Targeted plan
(`-target=module.waf -lock=false`, admin profile, nothing applied): **0 add / 2 change / 0 destroy**.
Both changes are in place: the web ACL (override count → none, plus the GenericLFI_BODY count
override) and the logging configuration (4 redacted headers). The redaction commit alone is 0/1/0.

## Scripts

`scripts/` contains `run.py` (A/T/C1–C2/B writes + hashes), `run2.py` (C3–C8), `logsq.sh` (Logs
Insights) and `analyze.py`. Credentials come from Secrets Manager at run time and are never printed.
The raw log exports that `analyze.py` reads hold header secrets: they were deleted after the
analysis and are not committed.
