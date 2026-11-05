# AA-820 part 2 — Implementation notes (root repo, lane l4-aa820-dpa, S269)

Source: Linear AA-820 (S265 re-scope comment: agency = controller, AA = processor, Art. 28 DPA with the AA-970 technical
annex, SCC Module 2 + TIA template, sub-processors after d23, joint-controller clause, tenant-as-controller privacy
text; S263 scope add: PDPL branch, Article 20 dossier), `docs/legal/dpa-pack-outline.md` (P1-P9), ADR 0019.
Part 1 notes: `AA-820.md`.

## Decisions

- **Six pages, not one.** `dpa.md` (body), four annexes, `pilot-contract-set.md` (P7-P9). The annexes double as SCC
  Annexes I-III, so they must stand alone; one page would be too long to review in pieces.
- **Draft v0.2, `status: draft`.** The template was v0.1. The tech lead reads it first (STYLE: agent-written pages start
  as draft); it does not take the AI Schedule's "v1.0 adopted" label.
- **Template superseded, not deleted.** `dpa-template.md` → `status: superseded`, `superseded_by: SEC-04-dpa-agreement`,
  with a banner; many audits and the readiness packet link it.
- **Live vs Planned, never promised.** Every Annex 2 measure is marked Live with evidence (repo file, Terraform line,
  dump, audit folder) or Planned with its gate. Read on `main` on 2026-11-05: RDS encryption, `publicly_accessible =
  false`, `rds.force_ssl = 1`, 7-day backups (INF `modules/rds/main.tf`); partner pool MFA ON / 14 chars
  (`identity_partner.tf`); WORKFORCE MFA OPTIONAL (`identity.tf`); CloudTrail multi-region with validation and KMS;
  CRM vault, scrubber, audit export, support levels (AA-Partner CONTEXT); CIS 373 `pii_class`.
- **The d16 pilot safeguards are a stated gap.** S268 CRM security review §4: none of the five is built; the pilot
  marker columns exist (`shared.tenants.is_pilot`, `pilot_ends_at`). DPA clause 15.3 and pilot-letter clause [●].4
  make "no real data before the safeguards" a contractual promise.
- **Deletion wording follows the code, not the retention table's single-client exceptions.** Offboarding
  (`erase_subject('tenant')`) keeps only the audit and the receipts (`offboarding.py` keep list), so invoices and
  signed agreements go with it; the accounting and claim-period exceptions apply to a single-client erasure. The DPA
  says so and tells the agency to keep what its law requires from the offboarding export.
- **Breach timeline:** contractual 24 h proposed (counsel), operational target 2 h from the incident runbook (SEV1).
- **Booking B2B:** AA as supplier and controller of its commercial records; no traveller identity reaches Booking
  (DM-6.8, contract `booking.b2b.v1`); ops details stay in the CRM ops release.
- **Trip Planner:** written as Annex 1 §5 but attached only when an agency takes it (milestone 2).
- **Sub-processors from live sources:** AI Use Register v1.8 (CIS 366/373) for the AI paths; Sentry region read from
  the Sentry organisation (`us.sentry.io`); Vercel kept until each d23 move, with a dated exit table.
- **Anthropic Usage Policy re-read 2026-11-05** (effective "Nov 12, 2026", scope and enforcement quoted). OpenAI
  policies page: HTTP 403 again.
- **AUP wiring:** pilot-letter clause [●].2 (incorporation + the Anthropic policy by name and date), DPA 3.3 (AA may
  refuse an instruction that breaches a Model Provider Policy), precedence clause [●].3; app pages already live (part 1).

### Review fix pass (S269)

- **CRM model on Dev = Amazon Nova Lite, not a stub.** Verified on AA-CIS-Infra `main` (`crm_llm_bedrock_enabled =
  true`, `modules/environment/crm_llm.tf`: `CRM_LLM_PROVIDER=bedrock`, `us.amazon.nova-lite-v1:0`) and read-only on
  the live CRM task definition (revision 130, the same `CRM_LLM_*` values) on 2026-11-05. Annex 1 §2, Annex 2 M-18,
  Annex 3 §1.2 (Nova Lite = CRM writer; location = US regions through a `us.` profile) and a new Annex 4 §1 row
  (us-east-1, us-east-2, us-west-2) now say so. The source of the error was the AI Use Register CRM row, which still
  said "stub provider": corrected there too (register v1.9, no route change).
- **Measure references.** DPA 3.4 → M-18 (scrub) and M-20 (placeholder map); clause 4 → M-9 to M-15; clause 14 →
  M-7 (audited database sessions) and M-13 to M-15 (the reviewer proposed M-13 to M-15; M-7 added because the
  "Database" bullet of clause 14 is that measure).
- **Anonymous statistics.** New DPA clause 1.6 (Agency instruction, the release rule of the CRM insights code, the
  opt-out set by AA on the Agency's written request = `crm.tenant_entitlement.insights_opt_out`, which is a platform
  field), clause 1.3 now says "Except as clause 1.6 allows"; counsel point C13 (instruction vs AA purpose, Art. 28(10);
  opt-in for EU agencies).
- **Roles of users' data.** DPA 1.2 excludes "the data in clause 1.4"; pilot clause [●].1 now refers to Agency
  Personal Data as the DPA defines it and points to DPA 1.4 for AA's own role.
- **Defined terms.** Pilot clause [●].0 defines Adventure Asia/AA, Agency, Agreement, Services, Portal, and maps the AI
  Schedule's "Tenant" to the Agency and "Personal Data" to the DPA's meaning; DPA §2 also defines Services and the
  Tenant mapping, so the DPA reads the same when it later attaches to the partner agreement. "Confidential
  Information" stays a [COUNSEL] pointer to the pilot letter's own confidentiality clause.

## Changed

- New: `docs/legal/dpa.md` (SEC-04-dpa-agreement), `dpa-annex-1-processing.md` (SEC-04-dpa-annex1),
  `dpa-annex-2-security.md` (SEC-04-dpa-annex2), `dpa-annex-3-subprocessors.md` (SEC-04-dpa-annex3),
  `dpa-annex-4-transfers.md` (SEC-04-dpa-annex4, type template), `pilot-contract-set.md` (SEC-04-pilot-set).
- Edited: `dpa-pack-outline.md` (drafted-in table), `dpa-template.md` (superseded), `register.md` (pointer to Annex 3;
  Sentry region US), `docs/architecture/ai-use-register.md` (S269 line under the follow-up for the business owner; v1.9: CRM row
  corrected to Nova Lite on Dev),
  `docs/README.md` (SEC-04 row links), `docs/guides/cio.md` (DPA row).

## Tradeoffs

- No `.vi.md`: the issue does not ask for one; counsel works on the English. The business owner gets the Vietnamese
  summary in the session-end Jira draft.
- The PDPL incident branch (`docs/ops/incident-response.md`) and the filled Vietnamese Article 20 dossier are **not** in
  this lane: the DPA names them as open (clause 8.3 note, Annex 4 §2); the TIA template is written so both share facts.
- The Content studio has no self-serve whole-account export; the DPA states a manual export on request rather than
  inventing a tool.
- Legal content (SCC option choices, US surveillance law names in the TIA) is marked [COUNSEL]; engineering states
  only where data goes and what protects it.

## Should know

- Nothing here is approved: the tech lead reads the pack (then `status` may move), and counsel is the business owner's
  call (b10, b20).
- Before the pilot letter is signed: `pilot-contract-set.md` §5 readiness checks (pilot safeguards, 14-day backups,
  vendor terms, market and transfer mechanism, Jev allowlist, AI allowance).
- If backups move to 14 days, update DPA 11.3 and Annex 2 M-29/M-30. When a frontend leaves Vercel, update Annex 3 §4
  and §1.3. When the CRM gateway gets the vendor APIs, or its Dev route leaves Nova Lite (acc3 back: crm-037 Claude entries
  switched on), update Annex 3 §1.2, Annex 4 §1, Annex 2 M-18 and Annex 1 §2.
