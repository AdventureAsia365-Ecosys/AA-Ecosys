# Specs

One folder per issue, `AA-<n>-<slug>/`, in Kiro's spec format: `requirements.md` (or `bugfix.md`), `design.md`
(feature specs) and `tasks.md`. This repo holds the specs of root-repo work and of work across repos; an application
repo holds the specs of its own work in its own `.kiro/specs/`.

- Rules and approval: `docs/guides/working-rules/planning-and-issues.md` (Specs) and `skill/aa-linear-issue/SKILL.md`.
- Templates: `skill/aa-linear-issue/templates/spec/` (feature, bugfix, quick).
- Check: `python3 tools/spec/trace_check.py check .kiro/specs/AA-<n>-<slug>`; the Spec trace workflow
  (`.github/workflows/spec-trace.yml`) runs it on every PR whose issue has a spec.
- Archived specs (implemented, closed at a session end) move to `_archive/`. Specs ship in public repos: no account
  ID, resource ID or secret (the docs lint checks this folder).
