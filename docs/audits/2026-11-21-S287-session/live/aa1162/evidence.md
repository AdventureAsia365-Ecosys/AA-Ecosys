# AA-1162 — root master refuses force-push and deletion (21/11/2026, ~18:20 +07)

Run by the orchestrating agent as the `aa-agent` GitHub App, with the tech lead's approval of the command (auto mode off).

| Test | Command | GitHub answer | Remote `master` after |
|---|---|---|---|
| Force-push one commit back | `git push --force-with-lease=master:<head> origin <head~1>:master` | `! [remote rejected] ... -> master (push declined due to repository rule violations)` | unchanged (`b3632949`) |
| Delete the branch | `git push origin :master` | `! [remote rejected] master (refusing to delete the current branch: refs/heads/master)` | unchanged (`b3632949`) |

Rules on `master` (`GET /repos/.../rules/branches/master`): `deletion`, `non_fast_forward` (ruleset 27781683, no bypass
actors) and `required_status_checks` (ruleset 27270886). The five child repos' `main` return `deletion` and
`non_fast_forward` as well.
