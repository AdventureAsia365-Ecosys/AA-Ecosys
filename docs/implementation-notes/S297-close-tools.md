# S297 close — root tools changed at the session close (AA-1191 DRY RUN fix, Jira posting tool)

Session S297 (28/11/2026), orchestrator. Two small root tools, each with its own test.

## Decisions

- **`tools/ops/aa1191_vnd_dry_run.py`** passes the currency parameter only to a query that uses `$1`. The `shared.plan`
  query has no placeholder; asyncpg raised InterfaceError and the whole CIS section printed `skipped`, which looked like
  a permission gap. The Infra byte copy (`db/scripts/aa1191_vnd_dry_run.py`, Infra #1066) carries the same fix.
- **`tools/jira/post_comment.py`** posts Jira comments as the tech lead (REST v2 + his API token) instead of the
  Atlassian connector, which stamps "Claude with ..." on every write (tech lead decision S297). Dry run by default;
  `--post` uploads the images, then writes one wiki-markup comment. First use: PR-31 comment 10717.

## Changed

- New `tools/jira/post_comment.py` + `tools/jira/test_post_comment.py`; `skill/aa-jira-update` "Kết nối" names it.
- `tools/ops/test_aa1191_vnd_dry_run.py`: the fake connection now refuses an argument count that does not match the
  `$n` placeholders, as asyncpg does (the old script fails 3 tests against it; the fixed one passes).

## Tradeoffs

- The token file lives outside the repo (`secret_manager/Jira/jira-token`, two non-empty lines). The tool reads it at run
  time and never prints it; it does not cache or copy it. A Secrets Manager entry was not used: the token is personal to
  the tech lead, not an ecosystem credential.
- Wiki markup (REST v2) instead of ADF (v3): shorter to write and renders mentions, lists and embedded attachments.

## Should know

- A 401 from `GET /rest/api/2/myself` means the token expired: the tech lead creates a new one.
- Reading Jira through the connector is still fine; only writes move to the tool.
