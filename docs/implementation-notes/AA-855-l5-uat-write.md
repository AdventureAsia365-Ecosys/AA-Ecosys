# AA-855 — UAT round 1: the write scenarios W-01..W-04 (lane l5-uat-write, S271)

Lane l5-uat-write (S271, Claude Code). Root repo, branch `feat/aa-855-uat-write-scenarios`. Builds on the round-1
harness (`AA-855-r1-harness.md`).

## Decisions

- **Four scenarios, one chain.** W-01 rewrites one Adventure Asia tour for the agency brand (Marketplace → Rewrite this
  tour → follow it in My Tours → Export DOCX → open the version). W-02 picks an article topic on Articles, chooses a
  goal, shows the three angles and presses Write with this angle. W-03 opens the writer on that request
  (`/portal/create/write?resume_request_id=`), waits until the article is delivered and opens it in My Content. W-04
  exports the article (Export HTML file, AI mark checked) and a social post (text). Every step is a visible click; the
  BFF is only read (GET) to choose the subject.
- **"Choose an angle" starts the write.** The studio has no separate choose step: Write with this angle chooses and
  writes in one click (AngleGateWizard). So W-02 ends with the write started (its caption says so) and W-03 follows the
  same article to delivery. W-03 pays only when W-02 chose the angle but its write never started.
- **One identity, one audit tenant per run.** New identity `studio-audit` (lib/studio-audit.cjs): the partner E2E
  person who is an editor in the four synthetic audit tenants (secret `crm/dev/e2e-test-crm/harbour-lights-owner`,
  read with the aws CLI in memory). `UAT_STUDIO_TENANT` picks the tenant (default `audit-atlas-hearth`); any other
  value throws. The pilot guard pins every studio-audit scenario to that slug (`scopesFor` → `only: [slug]`), and a
  scenario's own `pilotGuard` cannot widen it (throws). The four audit tenants join the built-in allow-list by their
  invented display names ("… (Audit)"), like the E2E tenants.
- **Tenant choice by name.** A person with several studios lands on `/portal-access/select`; sign-in clicks the option
  whose name is exactly the audit tenant's (exactly one must match), then checks `GET /api/tenant/me`. A saved session
  on another tenant is moved through the chooser. One state file per audit tenant (`.state-studio-audit-<slug>.json`).
- **Write set apart from the dry-run set.** `scenarios/write-set.cjs` (W-01..W-03, PRT-02, PRT-06) is loaded by
  dryrun.cjs through `describeWrite()` (writable identity, guard on, non-empty allowWrites, `paid` stated, writing steps
  marked). A write-set id is never in the whole set nor reached by `--app` / `--identity`; a paid one needs
  `--allow-paid` (which implies `--include-writable`), else `select` throws. W-04 is read only and sits in the dry-run
  manifest (writable identity → `--include-writable`).
- **Preview = the read-only part.** `--preview --only W-01,W-02` runs the steps before the first step marked
  `{ writes: true }` with `allowWrites` emptied (record.cjs `UAT_PREVIEW=1`, fast only), $0. W-03 has none.
- **Every paid call is capped in the page.** `limitWrites()` (page route in front of the guard) lets each write through
  at most once (the article write twice only when the first answers 422 for a missing call to action; then the editor
  types an invented one in the field the studio shows) and aborts any extra before it leaves the browser.
- **Re-runnable without deleting.** W-01 takes the first catalog tour not in My Tours and still sold; W-02 the first
  proposed topic (Update topics first when none is left, then a clear FAIL naming the tenant); W-03 / W-04 re-show the
  same piece. Nothing is deleted.
- **Hand-over file + Dev fallback.** W-02 / W-03 write `work/uat-write-chain.json` (gitignored, uuids only, mode 600,
  6 h validity). W-03 falls back to the tenant's newest article of the last 6 h, W-04 to its newest ready article and
  social post (lesson S262: local run state goes stale).
- **AI mark checked on the files.** HTML: `data-ai-generated="true"` on `<article>` and `<meta name="ai-generated">`
  (CIS `ai_marking.py`). DOCX: `ai-generated` in `docProps/core.xml` keywords, read with a small stdlib ZIP reader
  (`zipEntry`), no new dependency.

## Changed

- `lib/pilot-guard.cjs`: four audit tenants in SYNTHETIC; `studio-audit` scope + pin.
- `lib/signin.cjs`: identity `studio-audit`, studio chooser by name, `ensureStudioTenant`.
- `lib/dryrun-core.cjs`: identity, `--allow-paid`, `--preview`, `describeWrite`, write-set rules in `select`, report
  line for a paid run / a preview. `dryrun.cjs`: loads the write set, passes `UAT_ALLOW_PAID` only for a paid write-set
  entry with `--allow-paid`, 40 min child timeout for a full write-set run.
- `record.cjs`: preview mode. `lib/dryrun-page.cjs` `step(..., { writes })`. `lib/uat-page.cjs`: `rw()` keeps `paid`,
  `limitWrites`, `downloadBytes`, `zipEntry`, `AI_MARK`. New `lib/studio-audit.cjs`, `lib/write-chain.cjs`.
- PRT-02 / PRT-06: their writing steps are marked (they are in the write set now, recordable with `--record`).
- `catalogue.json`: W-01..W-04 (round R1-2026-11; W-01..W-03 writes + paid; W-04 neither). `lib/catalogue.cjs`:
  identity `studio-audit`, `checkWriteSet`.
- Tests: `tests/write-scenarios.test.cjs` (new) and the write-set cases in `tests/dryrun.test.cjs`.

## Tradeoffs

- W-03 deep-links the resume URL instead of clicking through the Slate: the Slate's Continue button only exists for a
  topic picked in the same visit, and a separate video is a new visit.
- W-02 asks for new topics when none is left (about 0.01 USD) rather than failing at once; on 06/11 no audit tenant
  had a proposed article topic.
- The pilot guard matches the audit tenants by name (their ids stay out of the public repo), the same rule as the E2E
  tenants; a tenant renamed to an audit name would pass, which the local id pin (`work/uat-allowlist.json`) closes.

## Should know

- Live checks run here (06/11, $0): `--only W-04 --include-writable` PASS 3/3 on audit-atlas-hearth (the HTML
  export carries both AI marks; the DOCX check first runs in W-01); `--only W-01,W-02 --preview` PASS 2/2 and 1/1.
  No paid step was run in this lane.
- Read on 06/11: proposed article topics = 0 on all four audit tenants (W-02 will press Update topics); ready
  articles: Atlas 2, Terra 1, WildKind 0, Trail Pulse 0.
- Record from the main checkout after merge, one tenant per sequence, after the AA-741 phase-1 chain on that tenant is
  done (it uses the same slate).
