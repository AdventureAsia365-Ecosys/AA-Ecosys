# Linear export + archive

Linear stays on the Free plan (250 unarchived issues; archived ones do not count). The UI has no manual
archive and auto-archive waits at least a month, so closed issues are exported here and archived through
the API (S245, 20/10/2026). Never delete issues to free space: deleted issues and their evidence comments
are gone after 30 days.

| Step | Command (from the AA-Ecosys root, MFA profile unlocked) |
|---|---|
| Export every Done / Canceled issue with comments to `docs/linear-export/` | `python3 tools/linear/linear_export.py` |
| See what would be archived (dry run) | `python3 tools/linear/linear_export.py --archive` |
| Archive exported closed issues | `python3 tools/linear/linear_export.py --archive --apply` |
| Move deleted issues from the 30-day trash to the archive (dry run / apply) | `python3 tools/linear/linear_export.py --rescue-trash` / `--rescue-trash --apply` |
| One issue | add `--only AA-913` |

- Only issues in a completed or canceled state are exported or archived; open work is never touched.
- An issue is archived only when its export file matches the issue's current `updatedAt`, so commit the
  export (root PR) in the same session.
- Every archived or trashed issue is exported whatever its state. `--rescue-trash` restores an exported trashed issue and archives it (Linear may report the new state a few seconds late; re-run to confirm).
- The key is read from Secrets Manager `aa-ecosys/ops/linear-api-key` (acc2) into memory only.
  `LINEAR_API_KEY` in the environment overrides it.

Issue size rule (S245): one Linear issue = one deliverable slice (about one PR or a small PR group); the
detailed task list lives in local plans (`docs/backlog/tracker/plan.json`, wave files).

## Tracker sync (`plan_sync.py`, S263)

`python3 tools/linear/plan_sync.py` pulls the Linear-owned fields (open issue set, title, status, priority,
project, due) into `docs/backlog/tracker/plan.json`, one way; dry run by default, `--write` to save, `--check`
exits 1 on drift, `--validate` is offline. Field ownership, conflict rules and when to run it:
`docs/backlog/tracker/README.md`. Tests: `python3 -m unittest discover -s tools/linear -p 'test_*.py'`.

`linear_api.py` holds the shared key lookup and GraphQL call used by both scripts.

`bot_pr_checks.py` is the merge gate of the optional Plan sync bot PR (`.github/workflows/plan-sync.yml`): it reads
the PR head's check runs and says whether the named root checks (Docs lint, gitleaks) passed.
