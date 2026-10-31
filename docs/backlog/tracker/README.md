# Master plan tracker (HTML)

A one-page view of the living backlog for Nghiệp: milestones (M1–M5 plus the CRM and portal-move milestones C-M1, P-M1, C-M2, C-M3) with their Done-when criteria, the per-session queue, time-gated checks, items waiting on people, every open Linear issue (filter + sort) and a per-session log.

- Live page (private claude.ai artifact, owner Nghiệp): <https://claude.ai/artifact/Q4LvqJyX5wsqRgZZQ75aoF>
- Files: `index.html` (layout + script, rarely changes) and `plan.json` (all content). The page reads `plan.json` next to it.
- Source of truth stays `docs/backlog/README.md` + Linear. `plan.json` mirrors them; when they disagree, fix `plan.json`.

## Update at the end of every session

Do it in the same root PR that updates `docs/backlog/README.md`.

1. Pull the open issues from Linear (team `AA_Ecosys`, states `started` and `backlog`, fields title/priority/status/project).
2. Edit `plan.json`:
   - `updated`, `session`, `next_session`.
   - `issues[]`: add new issues, remove closed or canceled ones, refresh `status` / `priority`, and keep `milestone`, `session`, `size`, `next`, `needs` in line with backlog §3/§4. `session` uses the labels in `SES_ORDER` in `index.html` (e.g. `S247`, `≥S263`, `later`, `parked`); the lanes show `S249`…`S262` (S246 master plan, re-slotted at the end of S248: S252+ moved two sessions earlier). `next` starts with the work lane (`L0`…`L7`, `LP`) of the plan in `docs/audits/2026-10-21-S246-master-plan/plan-and-status.json`; `≥S263` holds CRM W5–W8 until the S262 re-plan. When the window moves, update `SES_ORDER`, `LANES` and `MS_ORDER` in `index.html`.
   - `milestones[].criteria[].done`: tick what the session proved with live evidence; change `status` (`active` / `next` / `blocked` / `later`).
   - `milestones[].risks[]` and `due` (optional, below): review them with the weekly report (PR-20); add a risk when a session finds one, drop it when its trigger can no longer fire.
   - `checks[]` and `waiting[]`: mirror backlog §1 and §2.
   - `log[]`: prepend one entry for the session (`closed`, `canceled`, `created`, `reopened`, short `notes` in Vietnamese).
3. Validate: `python3 -c "import json;json.load(open('docs/backlog/tracker/plan.json'))"`.
4. Republish the artifact to the same URL: Artifact tool, `url` = the link above, `file_path` = `docs/backlog/tracker/index.html`, `files` = `{"plan.json": "docs/backlog/tracker/plan.json"}`. Read the artifact first when the session did not publish it (the tool refuses otherwise).

## Optional fields (TL-4, S262)

The tech lead approved dated milestones and a risk register (S261 architecture review TL-4, record
`docs/audits/2026-10-31-S262-tl-decisions/README.md`). Both fields are optional; the page shows them when present.

| Field | On | Shape | Meaning |
|---|---|---|---|
| `due` | a milestone or an issue | ISO date `YYYY-MM-DD` | A real date the work is due (a Linear due date, a policy date, a vendor deadline). Not a guess: no date known → no field. `checks[].due` keeps its free-text meaning ("hằng đêm"). |
| `risks` | a milestone | array of `{ "text", "owner_role", "trigger" }` | `text`: what can go wrong (Vietnamese, like the rest of the file). `owner_role`: `tech lead`, `business owner` or `engineer on duty`, never a name. `trigger`: the observable condition or date at which the owner acts. |

Validate the new fields with:

```bash
python3 -c "import json,re;d=json.load(open('docs/backlog/tracker/plan.json'));[re.fullmatch(r'\d{4}-\d{2}-\d{2}',x['due']) or exit('bad due '+x.get('id','')) for x in d['milestones']+d['issues'] if 'due' in x];[set(r)=={'text','owner_role','trigger'} or exit('bad risk') for m in d['milestones'] for r in m.get('risks',[])];print('ok')"
```

No secrets, passwords, account IDs or ARNs in `plan.json` (the page can be shared).
