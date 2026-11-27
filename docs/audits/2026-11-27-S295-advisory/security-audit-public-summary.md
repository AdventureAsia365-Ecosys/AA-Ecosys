# Security and compliance review, November 2026 (public summary)

**Date:** 27 November 2026
**Scope:** the whole platform: content and catalogue service, booking back office, agency CRM and Content studio, trip planner, shared infrastructure, delivery pipeline, AI features, and the governance and legal pack.
**Method:** read-only review. Eight independent review lanes, each checked by a second, adversarial reviewer. Evidence came from code, infrastructure-as-code, configuration, and read-only queries against the hosting account. No penetration testing, data access or secret values were involved.
**Reference standards:** OWASP ASVS 5 (L1/L2), CIS AWS Foundations Benchmark, AWS Security Reference Architecture, ISO/IEC 27001:2022 Annex A, ISO/IEC 42001, Vietnam's Personal Data Protection Law 91/2025 and Decree 356/2025, Cybersecurity Law 116/2025, AI Law 134/2025, and the EU AI Act transparency duties.

## Overall view

For a small team, the technical base is stronger than usual. The main gaps before the first paying pilot are in governance, legal paperwork and operational resilience, not in core engineering. Most of the planned improvements cost nothing and are small in effort.

| Area | Rating (A = production-ready … E = urgent) |
|---|---|
| Identity and access | C |
| Network and edge | B |
| Application security | B− |
| Data protection and privacy | C |
| Secrets, supply chain and CI/CD | C |
| Detection and resilience | C |
| AI security | C+ |
| Governance and compliance | D |

## Strengths confirmed by the review

- **Edge.** Private origins reached only through the CDN or the API layer. Modern TLS only on public domains. A consistent set of strict security headers.
- **Tenant isolation.** In the agency CRM, row-level security is enforced in the database. Each agency's data has its own encryption key, held under a managed key service.
- **CI/CD.** Keyless pipeline credentials scoped to exact repositories. Pinned third-party actions. Secret scanning on every change and across full history. Dependency alerts at zero. Nightly scans of running images.
- **Encrypted, recoverable storage.** Point-in-time recovery, deletion protection and tested restore drills.
- **AI behind one gateway.** Spending caps, fail-closed behaviour, personal-data scrubbing before model calls, output sanitising, and human review before anything is published.
- **Tamper-resistant audit trail.** Locked storage, security event rules, alarms, and automated daily compliance evidence.
- **An honest management system draft.** Scope, risk register, statement of applicability, AI impact assessments and an incident response plan that includes the 72-hour personal-data breach duty.

## Improvement themes

1. **Contracts and legal basis before any paid pilot.** Confirm the contracting entity. Have counsel review the pilot agreement, data processing agreement, AI terms and privacy notices. Complete the Vietnamese filings: cross-border transfer assessment, processing impact assessment, AI system classification, and information-system security classification.
2. **Approve the management system.** Formally sign the security and AI policies and the risk acceptances. Name a second key-holder. Run a tabletop exercise. Add people controls: NDAs, acceptable use, onboarding and offboarding, and security and AI-literacy training.
3. **Stronger administrator authentication and least privilege.** Apply this to staff, automation and AI coding agents. Enforce change approval on the code-hosting side.
4. **Secret hygiene.** Rotate credentials before real customer data arrives, and keep infrastructure state tightly restricted.
5. **Resilience.** Immutable, cross-region backups. A second alert channel and responder. Written recovery targets for the pilot.
6. **Detection.** Managed threat detection once real data arrives. Request-level access logs for breach scoping. Security alerting for the management account.
7. **Supplier assurance.** Dated evidence of each provider's data terms, a supplier register, and moving every processing path into company-owned accounts.
8. **AI governance.** Complete the AI use register. Run adversarial testing on every AI surface that faces users or agencies. Enforce retention on model-output records. Extend incident response to AI incidents.

## Roadmap

- **This week (no cost):** quick hardening of access and automation, documentation corrections, and alerting fixes.
- **Before the first paying pilot:** the legal pack, policy approval, administrator authentication, credential rotation, locked backups and threat detection. The added running cost is estimated at USD 25–35 per month.
- **Before production:** high-availability database and network egress, a wider web application firewall, internal encryption in transit, and a dedicated backup account.
- **Later:** an ASVS Level 2 self-assessment, build provenance, and certification readiness if a customer requires it.

Detailed findings are kept in the private engineering records and are tracked to closure.
