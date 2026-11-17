# AA-1112 — DM-7.1 retention windows approved, DM-7.3 archive format (lane docs-dm71)

Lane `l8-docs-dm71`, S283 (2026-11-17), Claude Code. Root repo docs only: no code, no migration, no table.
Input: the tech lead's decision `s283-dm71` = approve the groups as proposed (S283 decision page, record
`docs/audits/2026-11-17-S283-session/decisions/decisions.json`), the AA-1112 issue (S282 audit R02, sections 6.2 and
6.3) and the retention code of AA-CIS-App and AA-Booking on `main`.

## Decisions

- **One marker per row.** Each approved row drops its "proposed" wording and ends with
  "**Approved:** tech lead, S283 decision page, 17/11/2026." (grep-able, one citation format). Windows keep their exact
  numbers; a number that was plain text is now bold, as the table header says bold = approved.
- **What counts as a proposed row.** A row whose window or rule carried "proposed" (a leading "proposed:", "proposed
  (L3 ...):", "proposed for deletion ...", "(proposed TTL kind ...), the window is approved by the tech lead before
  prod"). 64 rows changed: 62 by the helper plus `shared.decision_log` and the S3 archive row. Words like "who proposed
  it" or "one row per proposed value" are not windows and stay.
- **Rows without a window are not invented.** `tripplanner.sessions` and `tripplanner.trip_events` said only "proposed
  in L3": they now say kept, no window proposed, nothing to approve in S283. The Cognito "signed-in account without
  membership" clause had no rule either and says so. `shared.llm_route_config_version` ("a window, e.g. 24 months or
  500 versions, is proposed before prod") is an example, not a proposal, and is unchanged.
- **`shared.decision_log` window = 180 days** for rows with `outcome IS NULL`, rows with a human outcome kept: this is
  what CIS `services/retention/policy.py` (`DECISION_LOG_WINDOW_DAYS = max(180, CACHE_MAX_AGE_DAYS)`) and
  `shared/llm_client/decide.py` (`CACHE_MAX_AGE_DAYS = 180`) run today (DRY RUN), and the decision page fact
  ("decision_log 180 days").
- **Accounting rows** (`booking.invoices` group, `booking.retired_b2c_record`, `booking.agency_invoice` group): approved
  as the working window, the 10-year period marked (est.) until the accountant confirms it before prod.
- **DM-7.3 format from the code:** CIS `services/retention/archive.py` and Booking `backend/app/retention/archive.py`
  write gzipped JSON Lines (`.jsonl.gz`, one `to_jsonb(row)` per line, one object per batch, never two UTC months per
  object); Infra `modules/s3` moves `archive/` to Standard-IA after 90 days, no expiry. Only the CIS archiver checks
  Content-MD5 + HEAD (row count, byte length); the text says so instead of claiming it for Booking.

## Changed

- Part B §7: header of the retention table, 64 rows, a new "S283 approval" note above the dated row notes, DM-7.3
  (format, keys, enforcement), §12 N4 row; Part B version line 1.6 → 1.15 (it was stale since v1.7).
- Part A QRY-9, Part C C3 Retention / Analytics rows, C5.4 intro and C5.4a (format; C5.4a "To build" → exists for the
  CIS and Booking kinds); Part C version line.
- README: version 1.15, changelog row, golden rule 12, open item 8 resolved.
- ADR 0008 decision 7: archive format sentence and an S283 amendment bullet (the README says a retention-window change
  also amends ADR 0008).
- The dfs/geocoder row's rollup cell "daily cost rollup (proposed, N4)" now names the built rollup,
  `shared.ai_usage_hourly` (CIS 372), which already lists both ledgers as its sources.

## Tradeoffs

- The dated notes under the table (S250, S252, S262 ...) still say "waits for the tech lead's approval": they record
  the day each row was added. Rewriting history was rejected; the S283 note says the rows are current.
- Per-row citation is long, but a reader of one row sees its status without reading the notes.

## Should know

- Approval is not deletion. The first live run of each TTL kind per app is still a DRY RUN whose row count the tech
  lead approves (DM-7.2); most approved windows have no TTL kind yet.
- Follow-up: the `decision_log` window is a code constant, not a Platform › Settings value like the other CIS
  retention windows (`cis.retention.*`); making it a setting is a CIS change outside this lane.
- The decision record file lands with the S283 session-close root PR; this PR cites its path.
