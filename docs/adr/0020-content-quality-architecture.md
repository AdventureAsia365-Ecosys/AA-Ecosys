# ADR 0020 — Content quality architecture: one policy registry, one FactSheet, measured gates, one exit contract for every AI-written tour page, blog and social post

- **Status:** **Accepted** (tech lead, S271, 06/11/2026). The decision page recorded 16 policy and product choices,
  all on the recommended option (D1–D16 below). The wave roadmap (W0–W6) is accepted as the order of work; each paid
  step still needs its own yes (D12). **Amended S278 (12/11/2026):** pooled claim classes, see
  [Amendment (S278)](#amendment-s278-12112026-pooled-claim-classes--measure-a-pool-first-split-later).
- **Design and evidence:** the S271 writing-quality audit,
  [`docs/audits/2026-11-06-S271-writing-quality-audit/`](../audits/2026-11-06-S271-writing-quality-audit/README.md):
  `README.md` (findings, verdicts, roadmap, targets), `decisions.md` (the choices), `data/` (three pipeline audits,
  the eval-judge root cause and the design review with per-workflow critiques, three redesigns each, judge panels,
  the shared architecture and two adversarial critics).
- **Amends:** [ADR 0009](0009-ai-platform-and-provider-gateway.md) decisions 5 (routing), 8 (ledger), 10 (data
  scopes) and 12 (qualification and family rule): see [Gateway amendments](#gateway-amendments-adr-0009).
- **Respects, unchanged:** ADR 0002 (only CIS writes content), 0009 d1 (one gateway for every model call), 0017
  (migrations in the app PR), 0019 invariant 4 (tenants see content only; QA, held items and flags stay in AA Admin)
  and the standing policies: writer source fidelity, elephant-riding tours kept as-is with human review, tour country
  from the source row, paid runs on small subsets only.
- **Scope:** CIS content writers and checkers (S1 platform tour rewrite, T2 tenant tour rewrite, T9 blog and social
  channels, the Writing Lab evaluation ladder and writing-memory releases) and the gateway core they share. In scope as
  a light profile: the Booking supply-content writer (policy compile + contract check, warn-only, human review kept).
  Out of scope until a later amendment: TripPlanner narration and CRM AI drafts (they keep their own checks; they
  adopt the policy registry when they are next changed).
- **Related Linear:** AA-900 (eval judge, R2), AA-741 (T9 blog quality, thinking budget), AA-1040 (AI marking),
  AA-820 (provider terms).

## Context

Four AI writing workflows produce what agencies use to market and sell tours: S1 rewrites the platform tour catalogue,
T2 rewrites a tour for one agency, T9 writes blogs and social posts, and the Writing Lab measures them. Fixes have
looped for weeks. The S271 audit measured why (0 USD, read-only):

- **T9 blog:** 187 pieces in 60 days, 53% held, 2% passed at the first write. The source-fidelity rule is restated in
  about 10 places with 16 contradictions (three meta-length bands, six widths of place background). The live fact
  judge, which decides 34% of holds, was answered by its third fallback model, uncalibrated. Held pieces still reach the
  tenant as ready, so the paid third attempt buys an admin label only.
- **S1:** the writer is good (0.0015 serious errors per sentence in the S250 blind panel), but the quality score is
  saturated at 9.99/10, the brand judge decides nothing, repairs cannot see the source, and two exits (the hitl exit and
  the server approve of an unedited version) skip grounding and the day guard.
- **T2:** still on the v1 writer prompt; its only score gate is a source-blind brand judge that rewards added detail
  and drives retries, the best-draft choice and the delivered status.
- **Writing Lab:** no valid R2 run for t9_blog. The judge prompt turns every evaluative phrase into an unsupported
  claim, the judge input is cut, 0 of 15 candidates had a paired control, the golden labels disagree with the first-line
  panel at kappa 0.35, and the runner paid the writer after calibration had already failed.

The common root: rules, sources and judges are not owned in one place, gates decide without a measured error rate, and
behaviour changes (route, effort, prompt, writing-memory release) reach live without a measurement.

## Decision

### Principle

The LLM writes prose and makes the few judgements code cannot. Everything else is owned by the system and checked by
code: the facts, the agency's wishes, and the rules. The design borrows the discipline of AI coding: a spec (brief +
FactSheet + agency profile), a compiler (content contracts), a linter (the policy registry), unit tests (claim checks
against FactSheet line ids), small patches (sentence-level repair), CI (replay and eval before any change goes live)
and review (a calibrated, pinned instrument plus human labels). Production runs a fixed, bounded graph, not a
free-roaming agent; agents work in the lab (mine failures, propose rule changes, run replay, open a PR for review).

### Four sources of truth, each with an owner

| Source | Holds | Owner | The LLM may |
|---|---|---|---|
| FactSheet | Per-line ids for days, legs, meals, activities, services, times, stays, price and terms, with provenance (`source_raw`, `human_verified`, `tenant_asserted`, `llm_derived`, `external`) and version | Code (built from the supplier source) + the Master reviewer | cite only |
| Place knowledge | Background on named places (history, geography, culture) with its own source and ISO country | Code + a cross-family checker | use as background within D1 |
| Agency profile | Brand voice, banned words, CTA, target travellers, market and language, channels, SEO keywords, liked exemplars, edit and approve history | The agency (Content studio) | follow, never beyond the facts |
| Policy registry | `writing_policy.yaml`: claim classes and severities, allowed background, bands, channel rules, legal rules | Tech lead + business owner | nothing: prompts, rubrics, rules and route rows are generated from it |

**Precedence:** law > tour facts and AA policy > agency wishes > style. An agency may ask for a lyrical voice; it cannot
ask the writer to promise a dinner, a view or a time the tour does not have. A brief is an instruction, never a source
(D2). Lines that are `llm_derived` (atoms, place cards) never alone clear a claim, and the instrument never verifies
against lines written by its own model family.

### Layers

1. **Infrastructure** (acc2): ECS, RDS, the job runners, storage, monitoring.
2. **AI gateway** (ADR 0009, amended below): routes, pinned instruments, token budget and same-model retry, degraded
   marks, the cost ledger and a cassette of raw replies for replay.
3. **Data:** FactSheet, place knowledge, atoms, lineage and versions; a source change fans out a $0 re-check of the
   objects built on it.
4. **Agency:** profile, per-piece brief, tenant-scoped writing memory (constraint-only rules; exemplars pass a
   contract replay on that tenant's recent objects).
5. **Policy:** the registry and its compiler, with a CI lint that fails on any hand restatement.
6. **Measurement:** golden sets with human-adjudicated claim labels, calibrated instruments with known error rates, the
   replay ladder (free → cents → small paid), a release fingerprint that moves on any route, effort, parameter, prompt,
   policy or memory change, and production watchdogs (cut rate, served-model drift, hold rate per gate, cost per
   delivered object).

### One production graph for every content type

Tour pages (S1, T2), blogs and social posts run the same graph; a **channel profile** sets length, shape, CTA, tags
and platform rules (Facebook, which auto-publishes, gets its own shape asserts).

1. **Plan:** subject and angle from tour data, agency needs and SEO; the brief is checked against the FactSheet and
   cross-tenant duplication is checked before any paid write.
2. **Compose:** the LLM writes prose with inline fact tags (`[F:id]`); code composes the contract fields (meals, day
   count, meta, slug, CTA, FAQ count). Elephant-riding tours in T2 take the Master text verbatim with code-composed
   brand fields and 0 LLM calls (D8).
3. **Verify:** deterministic contract and NLP checks first (numbers, places, banned words, entailment against cited
   lines), then one pinned, calibrated claim instrument; the voice judge reports only.
4. **Repair locally:** only the failing sentence, source-aware, with a contract re-check; a bounded number of
   attempts; the last attempt is "stop and label" at $0 (D6).
5. **Final contract:** one exit for every path (done, hitl, resumed, promote, approve, revalidate); the stored text is
   byte-equal to the gated text.
6. **Deliver and publish:** the agency receives the content with the AI mark (EU AI Act Art. 50); the publish step
   asserts the channel contract on the outgoing payload and records its sha.

A gate may hold content only with a passing measurement record (precision lower bound and recall on enough labelled
fires); until then it warns. NLP and code checks do what they can measure cheaply and precisely; the LLM keeps
generation and the nuanced judgement of hidden promises and voice.

### Policy decisions (decision page, S271)

| # | Decision |
|---|---|
| D1 | Background about places named in the FactSheet is allowed; never this trip's activities, services, times or views; numbers and years in background warn. |
| D2 | The brief is not a source; support comes only from FactSheet line ids. |
| D3 | Reflective sentences are voice, allowed when they state no fact about the trip. |
| D4 | Hypothetical framing warns; naming a concrete trip activity, service, time or view makes it a promise. |
| D13 | Rarity, uniqueness or age attached to the trip is a promise (enforce unless sourced); about a place it follows D1. |
| D14 | Suitability, safety and pace claims only as the source or the audience fields state them; beyond that, enforce. |
| D15 | A staged scene with a concrete trip activity, time or view is a promise (enforce unless sourced); general feeling is voice. |
| D5 | One meta band, 140–155 characters, for every workflow; title per the existing fitter band; code composes and trims. |
| D7 | One claim instrument may hold: R1 calibrates at least two candidates (GPT-6 Luna on the OpenAI API and one acc2 non-Claude model), the winner is pinned to one rung with no fallback (a miss is unverified); GPT-6 leaves every writer route. |
| D16 | The vendor API may be the primary verifier for the check role (tour text only, no personal data); reviewed when acc3 access is granted. |
| D10 | The eval and production share one claim engine; independence comes from human claim labels and a second-vendor vote on unconfirmed blocking claims. |
| D9 | The S1 brand judge leaves the live path; a weekly Writing Lab sample of about 20 tours, pinned; it returns as a gate only at kappa ≥ 0.6 on ≥ 40 labelled pairs. |
| D11 | Tech lead adjudication of about 2–3 hours over 1–2 weeks (agent panel first), then 10 new objects per workflow per month. |
| D6 | Tenant content with a residual promise after the repair budget: the last attempt stops and labels ($0); code cuts only classes with a passing measurement record, clause first; tenant-authored spans are never cut; no publish block. |
| D8 | T2 elephant-riding tours: Master text verbatim, code-composed brand fields, 0 LLM calls, a review row; the agency still receives it. |
| D12 | Paid writer proofs: eval null run ≤ $5, T9 ≤ $15, S1 ≤ $8, T2 ≤ $5 (≤ $33 in total), each after its own yes. |

### Gateway amendments (ADR 0009)

- **d5 routing:** the gateway is the single owner of the same-model truncation retry (an empty or cut reply at the
  ceiling is retried once at 2× on the same model, with the reason recorded) before the route moves on; call-site
  ceilings are computed, never below the model's floor. Writer routes stay within one model family; GPT-6 leaves every
  writer route; nova-lite leaves every judge and validate route.
- **d8 ledger:** every call records the answered model id, rung and effort; a rung > 0 answer, a same-family
  writer/judge pair in one job, or an uncalibrated model on an instrument stage is marked degraded for every role,
  not only writers. A cassette stores the raw reply, request and prompt shas for replay.
  - *Cassette scope (AA-900, S272).* One row per provider attempt that got a reply: answered, cut, or billed but
    unusable. An unusable reply is stored as the provider sent it and marked (`stop_reason` `billed_unusable`, with
    the provider's stop reason after a colon); replay never serves it. A row joins its ledger row on the route trace
    and attempt number, never on the model name (the ledger names the answering label, the cassette the route key
    called). Not recorded, by design: embeddings (the reply is a vector, not text; the caller keeps it and a re-embed
    is deterministic), Jev decisions (their own decision log), and attempts that failed with nothing billed.
- **d10 data scopes:** exception for the pinned claim instrument (D16): a vendor-direct model may be the first and only
  rung of a check-role route that carries tour text without personal data; `allowed_scopes` records it; the S235
  vendor-last-resort test is updated for that role only.
- **d12 qualification:** an instrument is a base model with calibrated connections; its id hashes the wire model,
  deployment and returned model id; a route change on a gated stage needs an eval run id or a break-glass reason.

## Amendment (S278, 12/11/2026): pooled claim classes — measure a pool first, split later

- **Status:** Accepted (tech lead, S278 start: "gom class trước, tách sau"). The rules below make that decision
  operational; they change no bar and no default (every class still warns until a measured flip).
- **Amends:** "A gate may hold content only with a passing measurement record" (One production graph, step 3) and D7
  (the R1 record per class).

### Context

The R1 bar for an LLM claim instrument is per writer surface and per class: precision >= 0.90 with a Wilson-95 lower
bound >= 0.80 over every fire on the writer, and n_pos >= 20 labelled held-out violations of the class. The S275
count on the adjudicated held-out labels (CL-1 1.0.0 + 1.1.0) found at most 9 violations for any (writer, class), so
no class could pass, while the unsupported-trip-claim classes of t9_blog together had 21 (embellish 5, inclusion 6,
misbinding 9, number 1, over 629 held-out t9_blog claims in the decision record). At those rates (0.8-1.4% of claims
per class) reaching 20 per class needs about 1,400-2,500 held-out t9_blog claims for each class, two to four times
what exists, and the adjudication time grows with it, far beyond D11's 2-3 hours of tech-lead work. The claim instrument
does not need the split to work: it calls a sentence "not supported by the source" whatever the class, and its
precision is already measured over every fire on the writer.

### Decision

1. **A pooled claim class (pool)** is a declared union of two or more policy classes on named writer surfaces that
   the R1 record measures as one class. The bar is not lowered; it is applied to the pool, per writer:
   - the writer's precision and lower bound over every fire (unchanged: fires on claims of any class count);
   - the pool's n_pos on that writer (labelled held-out violations of all its members) >= 20, and at least one caught;
   - the held-out split and the instrument conditions (test-retest >= 0.95, ok-cleared >= 0.85, hard subset caught,
     unverified <= 5%) as for a class.
   The record lists a passing pool as `<writer>:<pool id>` and keeps every member's own n_pos, caught and recall.
2. **Who decides a pool.** The tech lead declares a pool in code, in a reviewed PR (CIS
   `services/ground_truth/pools.py`: id, members, writers, who decided and when). Rules of a declaration:
   - it is made **before** the measurement that uses it, never after reading the votes: the record carries the
     declaration's sha (`pools_sha`), and a record made under another declaration does not count for this one;
   - the members are policy classes of every writer the pool names, and they ask the instrument the same question
     (is this claim about the trip stated by the source?); a class is in at most one pool per writer;
   - nothing derives a pool from the data (no automatic grouping by count).
   First pool (S278): `pool.fact_unsupported` = fact.embellish + fact.inclusion + fact.misbinding + fact.number on
   t2, t9_blog and t9_social. fact.name, fact.direction and fact.self_contradiction stay separate classes.
3. **A pool's record gates enforce only for the pool's members.** A passing pool calibrates the `<writer>:<member>`
   keys of that writer and nothing else (`calibrated` = passing classes plus the members of passing pools). The
   enforce map stays per (writer, class): a class holds only when it is calibrated AND the tech lead lists it in the
   enforce overrides (CIS `services/quality/claim_shadow.py` `CALIBRATED` and `ENFORCE_OVERRIDES`). At run time the
   class of a fire is the one the instrument names in extraction mode (the pinned mode of the shadow); a fire
   classed outside the pool's members warns, as does an unclassified fire. An entailment-mode instrument names no
   class, so its pool record stays report-only until the claim it reads carries a class.
4. **Split later.** Each member keeps its own counts in every record. A member that reaches the bar alone
   (`split_ready`) is measured as its own class from then on and leaves the pool in the next declaration; a pool
   with fewer than two members left retires. A changed declaration is a new sha and needs a new measurement before
   a gate reads it. The tech lead may leave a member out of the enforce overrides when its own recall in the pool
   record is weak; the record shows it.

### Consequences

- A gate can leave warn earlier for the commonest failure (an unsupported claim about the trip) on the writers that
  reach 20 pooled violations, without lowering the precision bar that protects agencies from false holds.
- Per-member recall stays less certain than a per-class record would show (fewer positives per member); the record
  states it, and the per-class flip still needs the tech lead's override per member.
- The live R1 run measures only the writers whose pool or class reaches the bar (a writer is taken whole: every
  held-out item of it), which keeps it inside the 2 USD cap.
- Code: CIS `services/ground_truth/pools.py` (declaration, checks, `calibrated_keys`) and `services/ground_truth/r1.py`
  (`pools`, `passing_pools`, `calibrated`, `pools_sha` in the record); evidence: AA-1048.

## Consequences

- Fixes stop being prompt patches: a rule changes once in the registry, the contradiction suite and replay show its
  effect, and only then does it reach live.
- The first writes become right more often (target: T9 first-pass yield from 2% to ≥ 30%, 50% target) and cheaper
  (T9 median ≤ 5 model requests per delivered blog, ≤ $0.25).
- Holds become honest: only measured gates hold, and a held state means something.
- Some current behaviour changes on purpose: the S1 judge leaves the live path, T2's judge becomes report-only, attempt
  3 of T9 no longer pays, and several fallbacks are removed (a stage may queue instead of silently changing model).
- The tech lead's labelling time is on the critical path of W2.

## Roadmap

W0 stop waste and make the truth visible → W1 policy registry, FactSheet, one exit (report mode) → W2 claim labels and
instrument calibration → W3 rewire T9, S1 and T2 in place → W4 promote the calibrated instrument → W5 small paid writer
proofs → W6 cleanup and permanent change control. Proofs, costs and targets per wave: the audit README.

## Alternatives considered

- **Keep patching the current graphs:** rejected; the audit traced the loop to ownership and measurement, which
  patches do not change.
- **Rebuild each workflow as a new graph:** rejected; the writers, repair-with-citations, finalizers, gateway and ledger
  work, and a parallel graph doubles the maintenance surface while it is most needed to shrink.
- **Open agent loops in production:** rejected; cost and variance become unbounded and results cannot be replayed.
  Agents stay in the lab.
- **A different model for the eval than for production checks:** rejected for now (D10); the available non-Claude
  model pool is narrow, and independence comes from human labels.
