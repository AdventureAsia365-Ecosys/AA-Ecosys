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
| One issue | add `--only AA-913` |

- Only issues in a completed or canceled state are exported or archived; open work is never touched.
- An issue is archived only when its export file matches the issue's current `updatedAt`, so commit the
  export (root PR) in the same session.
- Issues deleted in the last 30 days still come back from the API (`trashed: true`) and are exported too.
- The key is read from Secrets Manager `aa-ecosys/ops/linear-api-key` (acc2) into memory only.
  `LINEAR_API_KEY` in the environment overrides it.

Issue size rule (S245): one Linear issue = one deliverable slice (about one PR or a small PR group); the
detailed task list lives in local plans (`docs/backlog/tracker/plan.json`, wave files).
