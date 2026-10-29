# S257 — LLM access options (Claude / OpenAI) and AWS account setup

Written for the tech lead to discuss with the business owner after acc3 lost Bedrock access (29/10/2026).

- Options page for the business owner: private artifact only (not kept in the repo).
- `migration-assessment.md` / `migration-summary.vi.md` — options A/B/C2/D/E1 with time, effort, risk
- `anthropic-api-evaluation.md` — direct Anthropic API (batch, cost, billing, data, integration design, ~7.5 dev-days)
- `llm-vendor-recommendation.vi.md`, `angle1-aws-partners-vn.md`, `angle2-alternatives.md` — Vietnamese resellers and alternatives, with sources

Recommendation: D (direct APIs) now, C2 (own AWS Organization + Billing Transfer to an Anthropic-authorized reseller) in parallel, not A.
