# AA-1046 lane l2-r4b-b2c-drop: B2C drop, part 1 (S271)

Lane of S271 (Claude Code, orchestrated). Part 1 of AA-1046 only: the DRY RUN fix, the readers, the Booking
destructive migration. Part 2 (VAT e-invoice provider API) is another lane. Plan and draft:
`docs/audits/2026-11-05-S270-aa1037-b2c-drop-dryrun/` (README sections 1-9).

## Decisions

- **Pins hash non-personal columns only (part A).** The S270 DRY RUN pinned each dropped table with
  `md5(string_agg(t::text …))`, a whole-row read the pilot PII guard (`.claude/hooks/pilot_pii_guard.py`, AA-969)
  refuses for an ECS exec script. Each table now has a fixed column list (`PIN_COLUMNS` in the script,
  `-- pin-columns:begin` in the migration, byte-equal, harness-checked): the key, the write times and the status-like
  codes, one `jsonb_build_array(...)::text` per row, sorted, newline-joined, md5. The nine pin statements are written
  out in full in the script (`PIN_SQL`), with no run-time hole, so the guard reads each column list against its own
  table; a test checks each equals `PIN_SQL_TEMPLATE` over `PIN_COLUMNS` and that the migration's `EXECUTE format` is
  the same template.
- **jsonb array, not `concat_ws` / `format`.** `concat_ws` drops NULLs (two different rows can join to the same text);
  `format('%s|…')` is read by the guard as a run-time hole in the select list. A jsonb array keeps NULLs and types.
- **Column choice.** customers: id, code, source, verified, is_blocked, write times. identities (no id): customer_id,
  created_at. OTPs / sessions: id, customer_id, channel / attempts, created / expires / used / revoked. media: id,
  content_type, created / deleted. Money tables: ids, numbers (invoice_number, ref), kinds, status, currency, amounts,
  dates and write times. Amounts and codes are not tagged `pii:` (test `test_pins_read_no_personal_column` reads the
  schema reference).

## Changed

- Harness: 13 tests (was 11). The "same-count UPDATE" case now flips a pinned code (`verified`) with the triggers off,
  a new case moves an id (delete-plus-insert), and a known-limit case shows a hand edit of `name` alone keeps the pin.
  New: no pinned column is `pii:`-tagged; the guard itself (run as a subprocess with a fake PreToolUse input) passes the
  script and refuses a `md5(t::text)` probe.

## Tradeoffs

- A hand UPDATE of a personal column alone with the triggers off is no longer seen by the pin. Only `bk_owner` can do
  that, every app write moves `updated_at` (seen by the pin and by the 30-day guard), and the rows are dropped anyway.
  Reading personal columns into the hash would put them through an agent-run exec, which ADR 0019 d16 forbids.

## Should know

- Verified locally on PostgreSQL 16 against Booking `origin/main` `5066f75` (bk-044): 13 passed. Guard check:
  `python3 .claude/hooks/pilot_pii_guard.py` with `{"tool_name":"Bash","tool_input":{"command":"ECSX_SERVICE=aa-booking-dev-api tools/ecs/<ecsx> <script>"}}` on stdin exits 0.

## Review fixes (S271)

- **Draft holds its tables.** The draft mirrors bk-045: `SHARE ROW EXCLUSIVE` on the nine dropped tables and
  `trip_cases` right after `BEGIN`, so no write lands between the pin / archive checks and the drops. Harness: 14
  tests (new `test_draft_holds_writes_from_the_guards_to_the_drops`), passed on PostgreSQL 16 from the Booking code
  branch checkout.
- **README section 4** lists the readers the review found: the Infra owner-only exemption for
  `booking.retired_b2c_record` and the DM-6.5 consent script, the root DSAR runbook, the consent query page and the
  UAT scenarios BK-08 / BK-10 (fixed in the rootdocs PR of this lane).
