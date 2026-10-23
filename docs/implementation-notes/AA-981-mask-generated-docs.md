# AA-981 / AA-889 — Masked generated docs (AA-Ecosys root part)

Linear: AA-981, AA-889 (S248, decision d15: this repo and AA-CIS-Infra stay public until the code is done).
Generator part: AA-CIS-Infra `docs/implementation-notes/AA-981-mask-generated-docs.md` (masking rules, guard tests,
alias table).

## Decisions

- **One-off regeneration by masking, not by re-running the generators.** The Docs Gen pages need the Terraform
  state and the schema reference needs a live catalog dump (both AWS). This PR applies the generators' own masking
  function (AA-CIS-Infra `tools/docs/aws_mask.py rewrite`) to the files as they are on master: same content, ids
  masked, and each `docs-fingerprint` recomputed over the masked body, exactly what `gen_docs.page()` now writes.
  The schema reference Verified line is edited to the generator's new wording (`acc2, us-west-1`).
- **Labels:** account id -> `{acc2}`; ARN -> `arn:{partition}:<service>:<region>:{acc2}:<resource>` (Secrets Manager
  random suffix dropped); EC2/VPC ids -> `<prefix>-{masked}`. UUIDs untouched.

## Changed

- `docs/generated/{alarms,iam-roles,inventory,network}.md`, `docs/architecture/db-schema-reference.md`.
  `env-config.md` had nothing to mask.
- The open bot PR on `bot/generated-infra-docs` was rendered by the old generator and is not merged as is: the
  first Docs Gen run after the AA-CIS-Infra change force-pushes that branch with masked pages.

## Tradeoffs

- Masking the files on master instead of the newer bot-PR copy: the bot PR's content changes (new resources) come
  back through the next Docs Gen run, masked, so nothing is lost and no unmasked line is copied by hand.

## Should know

- **Git history keeps the old values.** Every account id, ARN and VPC id committed before this PR stays in this
  repo's history (and in the bot PR branch until it is force-pushed). AWS account ids are not secrets; the risk is
  reconnaissance only, no credential is exposed. Rewriting history is not planned.
- Hand-written pages (audits, Linear exports, session logs, a few architecture/ops pages) still name account ids;
  this change covers only the generated pages.
- Not masked yet (decision open): API Gateway ids / execute-api hosts, Cognito pool ids, CloudFront ids and
  domains, ALB/NLB DNS names, the RDS endpoint host, the NAT Elastic IP.
