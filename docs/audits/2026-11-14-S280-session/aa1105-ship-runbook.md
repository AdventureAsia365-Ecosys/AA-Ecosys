# AA-1105 — ship runbook for S2 (Infra #841) and S3 (CIS #1508, migration 420)

Independent review, S280 (read-only): **#841 ship; #1508 ship after #841 merges.** No code must-fix. The only red check on
#1508 is Migration preflight ("schema learn belongs to no owner in db/owners.yaml"): expected until #841 adds `learn` to
`db/owners.yaml`. Dev plan of #841: 11 add / 4 change / 2 destroy. Cost about 0 USD (one ALB rule, no new distribution).

## Safe order

1. Pre-apply checks (read-only):
   - no Route 53 record `academy.lumiguides.it.com` and no other CloudFront distribution carrying it as an alias;
   - CIS task role inline policies total stays under 10,240 characters (`ecs_task_policy` grows by about 330).
2. Merge Infra #841. **Hold AA-Partner `web/**` merges** until step 4: `deploy-web-dev.yml` copies the latest
   `crm_web` revision, and the new revision maps two `crm/dev/web` keys that do not exist yet (a deploy in that window
   goes red and rolls back by circuit breaker; not an outage).
3. Terraform Apply (dev); confirm the same 11 / 4 / 2.
4. At once: `tools/identity/crm_dev_identity.py academy-web-secret` dry run, then `--apply`; confirm the two key names.
5. Re-run the #1508 Migration preflight, then merge #1508 through the merge queue.
6. Merge the Migration Sync copy PR on Infra (the retention check now scopes the `learn` tables and must pass).
7. Migration Apply 420 once the job tables are idle; check the isolation probe cells `cross.*.learn.learner` and
   `default_acl.cis`; merge the schema dump PR.
8. AA-Partner academy web (S5) only after step 4; if any web deploy ran before the apply, compare revisions and redeploy.
9. `tools/terraform/crm_edge_live_check.py --academy-host academy.lumiguides.it.com`.

## Follow-ups for S4/S5 (not blocking)

- Captions over CORS: the bronze bucket CORS allows only the CIS admin origin; add GET/HEAD for the academy origin or
  proxy `.vtt` through the web before videos ship.
- Child rows: nothing ties a child row's `tenant_id` to its learner's tenant; add a composite FK or trigger before the
  P7 grants to `aa_app_user`.
- `learn.lab_run` has no index on `learner_id` (cascade delete scans).
- Erasure: deleting an `admin_users` row only nulls `learner.admin_user_id`; the AA-1093 saga should cover `learn.*`.
- `learn.retention_purge` guard is a bug catcher, not access control.
- Certificate name: prefer the staff directory name over the `academy-web` `name` write.
- Public verify rate limit must key on the real client IP (API Gateway → NLB → ALB: pick the right `X-Forwarded-For` hop).
- Fixed in #1508 during S280: the seed cites ADR 0022 decision 6 as accepted.
