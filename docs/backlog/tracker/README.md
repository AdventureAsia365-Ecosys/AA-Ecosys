# Master plan tracker (HTML)

A one-page view of the living backlog for Nghiệp: milestones M1–M5 with their Done-when criteria, the per-session queue, time-gated checks, items waiting on people, every open Linear issue (filter + sort) and a per-session log.

- Live page (private claude.ai artifact, owner Nghiệp): <https://claude.ai/artifact/Q4LvqJyX5wsqRgZZQ75aoF>
- Files: `index.html` (layout + script, rarely changes) and `plan.json` (all content). The page reads `plan.json` next to it.
- Source of truth stays `docs/backlog/README.md` + Linear. `plan.json` mirrors them; when they disagree, fix `plan.json`.

## Update at the end of every session

Do it in the same root PR that updates `docs/backlog/README.md`.

1. Pull the open issues from Linear (team `AA_Ecosys`, states `started` and `backlog`, fields title/priority/status/project).
2. Edit `plan.json`:
   - `updated`, `session`, `next_session`.
   - `issues[]`: add new issues, remove closed or canceled ones, refresh `status` / `priority`, and keep `milestone`, `session`, `size`, `next`, `needs` in line with backlog §3/§4. `session` uses the labels in `SES_ORDER` in `index.html` (e.g. `S245`, `≥01/11`, `later`, `parked`); the lanes show `S245`…`S253` and `≥01/11`.
   - `milestones[].criteria[].done`: tick what the session proved with live evidence; change `status` (`active` / `next` / `blocked` / `later`).
   - `checks[]` and `waiting[]`: mirror backlog §1 and §2.
   - `log[]`: prepend one entry for the session (`closed`, `canceled`, `created`, `reopened`, short `notes` in Vietnamese).
3. Validate: `python3 -c "import json;json.load(open('docs/backlog/tracker/plan.json'))"`.
4. Republish the artifact to the same URL: Artifact tool, `url` = the link above, `file_path` = `docs/backlog/tracker/index.html`, `files` = `{"plan.json": "docs/backlog/tracker/plan.json"}`. Read the artifact first when the session did not publish it (the tool refuses otherwise).

No secrets, passwords, account IDs or ARNs in `plan.json` (the page can be shared).
