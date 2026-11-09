# Restore → republish WordPress pages: follow-up of the AA-1060 rehearsal (S274)

## Gap
A `restored` event only resolves `tour_retired` flags that are still open. A tenant WordPress page that the
retirement already moved to draft stays in draft, while the "back on sale" mail goes out. During the AA-1060
rehearsal, post 6 was republished by hand.

## Work done
Branch `fix/aa-1039-restore-republish` in AA-CIS-App, pushed with **no PR and not merged**. Commits: dd7c14fb,
c92f84bc, edef9e26.
- New job kind `restored_page_republish`.
- New WordPress adapter calls `post_status`, `draft_post`, `set_published`.
- Claim-first publish under the key lock.
- The notice mail lists the pages put back and the pages kept.
- Tests: 85 unit; 29 integration passed locally.

## Reviews
Three independent reviews:

| Review | Verdict | Findings | Status |
|---|---|---|---|
| 1 | BLOCK | 1 blocker, 4 majors | fixed in c92f84bc |
| 2 | BLOCK | 1 major (interrupted claim), 4 minors | fixed in edef9e26 |
| 3 | BLOCK | 2 majors, 6 minors | open |

Review 3 in detail:
- **Major:** the "lost WordPress answer" rule can publish a draft that the tenant made on purpose.
- **Major:** a restore that lands between a lost draft answer and its retry leaves the page in draft, and no one is told.
- **Minors:**
  - resume runs without the key lock;
  - deferral runs without the lock;
  - orphaned claims are never cleaned up;
  - the claim is released while the WordPress state is unknown;
  - "stays in draft" can be mailed while the page goes back online;
  - the M4 revert does not check whether the page was modified.

## Assessment and options (tech lead decides)
Each round closes holes and opens new ones. The system writes to a site that the tenant also edits, and every
network failure leaves the remote state unknown.

- **A (recommended):** no automatic republish. The restore notice (bell and mail) lists each drafted page with a
  one-click "Put back online" in the portal. The click runs one publish call through the existing publish path,
  which already handles idempotency and the content gate, so nothing is published without the tenant. The branch's
  adapter calls and notice changes can be reused; the claim, resume and race machinery is dropped.
- **B:** keep automatic republish. Finish review 3's list (about 8 more fixes and a sweep for orphaned claims), then
  rehearse on test-wp, including a page set to private before the draft date.

Until a direction is chosen, today's behaviour stands: pages stay in draft after a restore, and the tenant
republishes them from WordPress.
