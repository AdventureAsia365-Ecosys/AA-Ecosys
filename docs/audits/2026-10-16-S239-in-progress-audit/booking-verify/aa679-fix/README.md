# AA-679 fix: "Use for trip case" dialog footer at 390 px (S239)

Done-when bullet covered: *The 390 px "Use for trip case" dialog footer is fully visible (S237 UI verify defect).*

- Repo: AA-Booking, worktree `.tmp-session/wt/aa679`, branch `fix/aa679-modal-footer-390` from `origin/main` `cd4b962`.
- Commit (local, not pushed): `4642358 fix: kit modal body scrolls and keeps its footer above the phone bottom nav`
  (body `Refs AA-679`).
- Files: `frontend/ui/Modal.tsx` (kit, documented local deviation from the CIS copy), `frontend/ui/shell.css`
  (`--aa-modal-inset-bottom: 76px` in the phone media query under `:root:has(.aa-bottom-nav)`),
  `docs/implementation-notes/AA-679.md` (new section "Fix branch").

## Cause

The kit Modal scrolled as one box (`max-height: 90vh; overflow: auto` on the dialog), so the footer was the last
thing in the scroll content. At 390x844 the form is 808 px in a 758 px box: on open the footer was outside the
dialog box; at 390x667 outside the viewport. Even scrolled to the end, the dialog bottom (802 / 634) overlapped the
60 px bottom nav (top 784 / 607).

## Fix

Dialog = flex column, header + footer `flex-shrink: 0`, body `flex: 1 1 auto; min-height: 0; overflow-y: auto;
overscroll-behavior: contain`; `max-height: 100%` of the overlay; overlay bottom padding
`var(--aa-modal-inset-bottom, 24px)` = 76 px on phones when the bottom nav exists. Applies to every kit modal.

## Steps

1. `npm ci` in `frontend/`, `npm run dev` (http://localhost:3100), default server config = Dev Booking API + CIS
   login. Login with `aa-cis/dev/e2e-test-admin` read from Secrets Manager at run time (never printed).
2. Script `.tmp-session/s239/bkv/s679fix.mjs <before|after>` (Chromium, scrollbars on): for light and dark, at
   390x844, 390x667, 1440x900: open `/catalog/trip-plans/4a2411b2-6966-4ec0-a27e-84f9fad186ea` (HTTP 200), click
   "Use for trip case", measure; scroll the dialog body to the end, measure; switch to "Add to an existing case",
   measure; click Cancel (dialog must close). **Read-only: nothing submitted, no Dev writes.**
3. Per footer button: inside viewport, inside the dialog rect, bottom <= bottom-nav top, and
   `document.elementFromPoint(centre)` is the button (or inside it).
4. Run once on `cd4b962` (before) and once with the fix (after). Raw numbers: `before-measure.json`,
   `after-measure.json`.

## Results

| Viewport | Phase | Dialog (y..bottom) | Scroll box | Cancel / Create on open | At scroll end | Above nav |
|---|---|---|---|---|---|---|
| 390x844 | before | 42..802 | dialog 808/758 | outside dialog, hit = no | hit = yes | no (802 > 784) |
| 390x844 | after | 24..768 | body 683/617 | inside, hit = yes | hit = yes | yes (768 < 784) |
| 390x667 | before | 33..634 | dialog 808/598 | outside viewport, hit = no | hit = yes | no (634 > 607) |
| 390x667 | after | 24..591 | body 683/440 | inside, hit = yes | hit = yes | yes (591 < 607) |
| 1440x900 | before / after | 167..733 (620 wide) | none | hit = yes | hit = yes | n/a (no nav) |

Same numbers in light and dark. "Add to an existing case" mode (Cancel / Add version): pass in both phases. Cancel
closed the dialog in every run. Body scroll box `scrollWidth == clientWidth` (334): no sideways scroll. Console
errors: 0. Network: only `ERR_ABORTED` on dashboard prefetches cancelled by the navigation (not failures).

Screenshots: `before-*` / `after-*-{390x844,390x667,1440x900}-{light,dark}-new-case.png`, `…-new-case-scrolled.png`,
`…-390x667-*-existing-case.png`. The round "N" badge bottom-left in the after shots is the Next dev indicator
(local dev only).

## Checks

- `npm run lint` exit 0, `npm run typecheck` exit 0, `npm run build` exit 0.

## Verdict

Done-when "390 px dialog footer fully visible": **PASS locally** (light + dark, 390x844 and 390x667, 1440 unchanged).
Still needed for Done per aa-ship: push + PR + CI green, merge by Nghiệp, then re-run the script against the
Vercel preview / `aa-booking-admin.vercel.app` (`BASE` change only).

## Defects / follow-ups

- None new in the dialog. Follow-up: `ui/Modal.tsx` now deviates from the CIS kit copy; upstream the same layout to
  CIS `frontend/app/_kit/Modal.tsx` (same whole-dialog scroll there), then re-copy.
- Other AA-679 bullet still open (not in this task): evidence that a tour unpublished in CIS leaves the list.
