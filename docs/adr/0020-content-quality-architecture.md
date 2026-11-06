# ADR 0020 — Content quality architecture: one policy registry, one FactSheet, measured gates, one exit contract for every AI-written tour page, blog and social post

- **Status:** **Accepted** (tech lead, S271, 06/11/2026). The decision page recorded 16 policy and product choices,
  all on the recommended option (D1–D16 below). The wave roadmap (W0–W6) is accepted as the order of work; each paid
  step still needs its own yes (D12).
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
- **d10 data scopes:** exception for the pinned claim instrument (D16): a vendor-direct model may be the first and only
  rung of a check-role route that carries tour text without personal data; `allowed_scopes` records it; the S235
  vendor-last-resort test is updated for that role only.
- **d12 qualification:** an instrument is a base model with calibrated connections; its id hashes the wire model,
  deployment and returned model id; a route change on a gated stage needs an eval run id or a break-glass reason.

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
