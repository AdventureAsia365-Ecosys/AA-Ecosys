# AI gateway: measure first (S283, 17/11/2026)

Two $0 reads behind ADR 0009 decision 10 (data scopes per maker) and the caller caps.

## Spend by provider, connection and stage, last 30 days

`aa1113-provider-stage-30d.psv`: `shared.llm_call_log`, shadow rows left out, top 60 by cost; `tenants` = number of
distinct tenants (no tenant names). `?` in the connection column = rows written before the gateway stamped
`connection_key`. Reading:

- The writer stages that carry tenant free text are `t9_write`, `t2_generate`, `t8_angle_gen` (7 tenants each, Anthropic
  API first, Bedrock after). These are the stages a free-text PII scrub must cover first.
- Catalogue stages (`s1_*`, `a3_*`, `tp_compose`) carry no tenant text: tenants = 0.
- The largest 30-day line is still `s1_generate` on Bedrock (47.08 USD, the S1 rewrite waves).

## Budgets on the LLM accounts (read-only)

| Budget | Limit (USD / month) | Filter | Cost types |
|---|---|---|---|
| acc1 `aa1-llm-monthly-total` | 100 | its own linked account only | everything included except refunds and credits |
| acc3 `aa3-llm-monthly-total` | 250 | none (whole account) | same |

Neither budget filters by service, so AWS Marketplace lines (Claude models on Bedrock are sold through Marketplace) are
not excluded by a filter. The AWS documentation searched today does not state outright that cost budgets count
Marketplace charges; to close it, compare one month's budget actual with Cost Explorer grouped by service (the Claude
"Amazon Bedrock Edition" lines) after the November bill. The acc3 limit (250) is above its gateway cap (100); align it
with the cap when the tech lead decides d10 (a free budget change, local apply with MFA).


**Update 17/11 (S283):** the tech lead approved 100 USD on the decision page; Infra #895 changed the variable default and the local apply of the acc3 root updated `aa3-llm-monthly-total` in place (plan 0/1/0; read back: 100.0).
