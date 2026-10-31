# AA-945 (CRM-17 Module 5 e-mail): saved reply, internal note and autosaved draft, live check (S261, 31/10/2026)

Lane 2 item 1 of the S260 In Progress triage (`docs/audits/2026-10-30-S260-inprogress-triage/README.md` §5, §6).
Run by the agent at 01:50Z, Dev only, synthetic agency only. Result: **PASS** on every line below.

## How it was run

- Headless Chromium (Playwright, `@playwright/test`), one browser, closed at the end. Egress checked first: VN, not the VPN.
- Host: the CRM web on `https://portal.lumiguides.it.com`. The old `partner-dev.` host now answers 301 to `portal.`
  (AA-979), so the run used `portal.` directly.
- Identity: the e2e **owner** of the synthetic agency "Lữ hành Sen Vàng" (partner pool, password and authenticator).
  The credentials were read at run time from the e2e user's secret (read only) and never written down or printed. No
  screenshot was taken on the managed-login host.
- Trip: the S252 mail probe trip "Việt Nam, 10 đêm" (lead: the synthetic client "E2E MailProbe Client"), conversation
  `b58f6a43…` (the trip's first conversation, 4 messages, no stored draft before the check).
- **Send was never clicked.** No mail left the system. The spec is local only (not committed).
- The proof is the BFF responses and the thread JSON the page reads, not text on the screen alone. The run log
  ([`run-log.txt`](run-log.txt)) holds ids cut to 8 characters, the HTTP status of each call, and nothing else.

## Steps and results

| # | Step | Result |
|---|---|---|
| 1 | Settings › Saved replies: create a saved reply "S261 check reply …" (scope Mine, EN) | `POST /bff/saved-replies` 201, listed. `01-…` |
| 2 | Trip › Messages › New message: type a subject, pick the saved reply in "Insert a saved reply", then type one more line | The body holds the saved reply text followed by the typed line. Three seconds after typing stops, `PUT /bff/messages/drafts/<id>` returns 200 with that exact subject and body, targeting conversation `b58f6a43…`. The composer shows "Draft saved". `02-…` |
| 3 | Trip › Notes: add an internal note ("Add a note for your team" › Save) | `POST /bff/trips/<trip>/notes` 201. Listed as "Note · 31 Oct 2026" with the text. `03-…` |
| 4 | Reload the page | `GET /bff/conversations/b58f6a43…/messages` 200. The draft row is there with `status = draft_autosaved`, `direction = out`. The composer is **filled again** with the same subject and the same body (saved reply + typed line). The draft is **not** listed as a message. The note is still listed. `04-…` (1440), `04b-…` (390) |
| 5 | Mobile 390 px | No horizontal overflow: document 0 px, `main` 0 px. |
| 6 | Clean-up: "Discard draft", then reload | `DELETE /bff/messages/drafts/<id>` 200. After the reload the draft row is gone and the composer is empty. `05-…` |
| 7 | Clean-up: delete the run's saved reply | `DELETE /bff/saved-replies/<id>` 200, no longer listed. |
| – | Console and network across the run | 0 console errors. No BFF response ≥ 400. |

### Done-when lines covered here (CRM-17 checklist)

| Checklist item | Status |
|---|---|
| Saved replies (create, insert into a draft) | **PASS**, live, steps 1–2 |
| Notes (internal note on the trip) | **PASS**, live, step 3 |
| Autosaved drafts, restored after a reload | **PASS**, live, steps 2 and 4; discard also works (step 6) |

The other CRM-17 items were evidenced live in S250–S252; see the Linear comments of 25/10 and 26/10:

- SES forward-in;
- Gmail send-as with Undo;
- token and header threading;
- unknown slug dropped;
- `held_reconnect` and the requeue after reconnect;
- history import.

## Not tested, and why

- **Microsoft 365 (Outlook) and SMTP send-as.** They need an Entra app registration and an SMTP app password, which
  don't exist yet. Per the triage §6 they move to the new follow-up "[CRM] Mail send-as for Microsoft 365 and SMTP".
- **`allow_platform_sender`.** It was dropped by the S247 errata, so there is nothing to test.
- **Sending the draft.** Out of scope for this check. Send + Undo was evidenced in S252. Not sending also kept this run
  from mailing anyone.
- **Agency-scoped saved replies and a second member.** The check used the owner's own ("Mine") reply only. No second
  Sen Vàng member signed in to see an agency reply or someone else's draft. Draft privacy (author only) is enforced
  in `api/app/mail/conversations.py` (`not_a_draft`), but it was not exercised live here.
- **Vietnamese UI and dark mode.** Not part of this item.

## State left on Dev

- One internal note on the probe trip: "S261 internal note check vqurls: client prefers morning calls." The UI has no
  note delete, and the note is harmless synthetic data.
- No draft and no saved reply left behind.

## Screenshots

These are full-page captures. The app shell scrolls inside the page, so its sidebar and top bar show at the place
the page was scrolled to (lower half of the image). That is how the capture works, not a layout bug: the 390 px
overflow check (step 5) is 0.

| File | What it shows |
|---|---|
| `01-saved-reply-created-1440.png` | Settings › Saved replies with the new reply |
| `02-composer-saved-reply-inserted-draft-saved-1440.png` | Trip Messages composer: subject, saved reply inserted plus a typed line, "Draft saved" |
| `03-internal-note-added-1440.png` | Trip Notes panel with the new internal note |
| `04-after-reload-draft-restored-1440.png` | After the reload: composer restored from the stored draft, note still listed |
| `04b-after-reload-draft-restored-390.png` | Same at 390 px |
| `05-after-discard-composer-empty-1440.png` | After Discard draft + reload: empty composer |
| `run-log.txt` | Per-step HTTP status and checks (ids cut to 8 characters) |
