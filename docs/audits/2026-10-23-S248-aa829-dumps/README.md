# AA-829 — DRY RUN: the 2026-09-16 real-data dumps (S248, 23/10/2026)

Read-only listing. Nothing was moved, deleted, uploaded or changed. No row values were read or printed:
only file metadata, the dump table of contents, DDL and row counts.

## 1. What and where

| Item | Finding |
| --- | --- |
| Location | One copy only: `docs/backups/2026-09-16/` in the root checkout on Nghiệp's WSL2 laptop (ext4 inside the WSL VHDX). |
| Other copies searched | Whole `/home/nghiep` (all worktrees, `.tmp-session`, home): none. Windows side `C:\Users\*\{Downloads,Desktop,Documents,OneDrive*}` (depth 4): none. S3: not checked live (MFA had expired, see §6, command 1). |
| Origin | AA-595 (G0 of the CIS data reset, S183, 16/09/2026): `pg_dump -Fc --no-owner --no-privileges`, one file per schema, through the G0 bastion SSM tunnel. The bastion and `.g0_pgpass` were cleaned up (AA-602); no `*pgpass*` file is left under `/home/nghiep`. |
| Git | Ignored by `.gitignore:19` (`docs/backups/`) and excluded from markdownlint. No `*.dump`, `*.pgdump`, `*.sql.gz` or `docs/backups/*` path was ever added in any ref of root or AA-CIS-Infra (`git log --all --diff-filter=A`). |
| Encryption | None at file level (PostgreSQL custom format, plain). Only protection is the laptop disk / Windows account. |
| Permissions | `-rw-r--r--` owner `nghiep` (world-readable inside WSL; single-user machine). |
| Related RDS snapshot | `aa-cis-dev-db-g0-audit-20260916` (same point in time) was **deleted** by the AA-869 snapshot-expiry Lambda after Nghiệp's S241 decision (`docs/sessions/2026-10-17-S241-decisions.md`: "xoá `g0-audit-20260916`, bật xoá thật"). The local dumps are now the only copy of the 16/09 pre-reset data. |

### Files (sha256 for the deletion record)

| File | Bytes | Schema | sha256 |
| --- | ---: | --- | --- |
| `shared.dump` | 802,961 | shared | `84c0fcb386ba6cf32adafebccbb55f7e691fac66e32589a5a7926af527529c6e` |
| `silver_aa_internal.dump` | 2,208,663 | silver_aa_internal | `c2e494b823c6240221127b84193754f6369cd55915eab41c0a64fa0098d7dcd5` |
| `gold_aa_internal.dump` | 233,346 | gold_aa_internal | `523bba84a2698758c32b69a7ba1ce39413b0627a72eb1d61f047458126d579a9` |
| `acp_contract.dump` | 614,188 | acp_contract | `42ecc8e433c425691d4f7d2d980a28dff0c2df50bfa5beef8e0e42a4ee30561d` |
| `acp_shared.dump` | 389,506 | acp_shared | `8087a5b6cdfd5aa84f66f07ccc67f17794f5ba9f9ad3f8b98c832509c2e26909` |
| `tripplanner.dump` | 6,414,022 | tripplanner | `6a14e33fb5fd00544c544a75df1c348d2e17a4e4620577437613c7b6bf1bec7c` |
| **Total** | **10,662,686** (~10.2 MiB) | 6 schemas, 70 `TABLE DATA` entries | |

## 2. Why it is sensitive (from DDL + row counts only)

| Table (in dump) | Rows | Sensitive columns |
| --- | ---: | --- |
| `shared.admin_users` | 4 | `password_hash` of the legacy password login (being switched off by AA-816) |
| `shared.tenant_export_config` | 3 | `webhook_url`, `auth_header` (tenant webhook credentials, if set) |
| `shared.tenants` | 4 | `api_key_hash` |
| `shared.tenant_integrations` | 0 | (`secret_key` column, empty) |
| `tripplanner.customers` | 2 | `name`, `phone`, `email` (personal data) |
| `tripplanner.sessions` | 21 | `guest_token` |
| `shared.llm_call_log`, `acp_shared.audit_log`, `shared.notifications` | 741 / 127 / 39 | operational logs |
| `silver_aa_internal.raw_tours` / `raw_sources` | 793 / 37 | partner tour content (commercial, not personal) |

Whether the `auth_header` / phone / email cells are real or test values was **not** checked: reading cell values
was refused by the session's PII guard, which is the right call for a DRY RUN. Treat them as real.

## 3. Public exposure now that root and Infra are public (ADR 0014 amendment, S247)

- **Data: not exposed.** No dump, extract or presigned link is in either repo's tree or history.
- **Metadata: public, low risk.** Root docs name the folder, the six file names, schema list, sizes and the 16/09
  row counts (`docs/linear-export/.../AA-595.md`, `docs/archive/2026/audit-cis-g1-before-snapshot.md`,
  `docs/audits/2026-10-15-S238-backlog-audit/backlog_audit.json` with the absolute laptop path, the S241/S245
  audits, `DM-6.10`, `docs/guides/cio.md`, `docs/ops/database-operations.md`). This tells a reader that a laptop
  holds real data, not how to get it. No action needed beyond removing the files.
- **Residual risk while the repos are public:** a future `git add -f` or a rename out of `docs/backups/` would publish
  the files; gitleaks (AA-981) does not inspect binary dumps. This branch adds repo-wide ignore patterns for dump
  formats as a second fence (§7).
- Side note (not AA-829): `docs/STYLE.md:105` still labels the root repo "private"; ADR 0014's S247 amendment made it
  public. Left for the ADR 0014 owner.

## 4. Options

| | A. Delete (recommended) | B. Keep in a locked S3 location |
| --- | --- | --- |
| What | Shred the six files, remove the folder, keep this record (hashes, table list, counts). | Upload to a dedicated private bucket with SSE-KMS and a deny-all-but-admin policy, lifecycle expiry, then shred locally. |
| Fits | DM-6.10, data minimisation (PII + credential hashes with no current use); same call Nghiệp already made for the 16/09 RDS snapshot in S241. The CIS reset audit (AA-594 project) is closed; 7-day PITR + daily RDS backups cover current recovery. | Only if someone still needs the pre-reset derived rows (~21.6k rows deleted on 16/09) for a forensic question. Nobody has asked since 17/09. |
| Cost | 0 USD | about 1 USD/month (one customer managed KMS key) + < 0.01 USD storage; 0 USD key cost with `aws/s3`, but then the key policy cannot be narrowed. |
| Done-when impact | "S3 objects encrypted" becomes N/A: needs Nghiệp to accept the scope change on AA-829. | Matches the issue text as written. |

**Why not a "locked prefix" in an existing bucket:** the CIS api/worker task role has `s3:GetObject`, `s3:PutObject`
and `s3:ListBucket` on `Resource = "*"` (AA-CIS-Infra `modules/ecs/main.tf`, the S3 statement around line 199), so
any acc2 bucket without an explicit Deny is readable from the containers and from every ECS exec session. Bronze
also allows two cross-account Bedrock roles on some prefixes, is SSE-S3 only and `force_destroy = true` on dev.
A prefix there would need a new Deny statement in the shared bronze policy. A dedicated bucket is simpler to reason
about.

## 5. Proposed commands (single line each; NOT run)

### Option A — delete

```bash
aws rds describe-db-snapshots --db-instance-identifier aa-cis-dev-db --snapshot-type manual --query 'DBSnapshots[].[DBSnapshotIdentifier,SnapshotCreateTime]' --output text --profile aa365-admin --region us-west-1
```

```bash
cd /home/nghiep/projects/AA-Ecosys/docs/backups/2026-09-16 && sha256sum -c /home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-23-S248-aa829-dumps/SHA256SUMS
```

```bash
shred -u -n 1 -z /home/nghiep/projects/AA-Ecosys/docs/backups/2026-09-16/*.dump && rmdir /home/nghiep/projects/AA-Ecosys/docs/backups/2026-09-16 && ls -la /home/nghiep/projects/AA-Ecosys/docs/backups/
```

`shred` on ext4 inside a VHDX is best effort (journal, VHDX block reuse, any Windows backup of the VHDX). Good
enough for 10 MB of Dev data on an encrypted-at-rest laptop; if the laptop disk is not BitLocker-encrypted, say so in
the closing comment.

### Option B — keep in a locked bucket

Infra (Terraform, preferred over CLI so the bucket is not drift): a new `accounts/aa365/dr_vault.tf` with
`aws_kms_key` + alias `alias/aa-ecosys-dev-dr-vault` (key policy: account root + the admin role only),
`aws_s3_bucket` `aa-ecosys-dev-dr-vault-<account>` (versioning on, `force_destroy = false`), public access block
(all four true), SSE-KMS default with `bucket_key_enabled = true`, lifecycle `expiration { days = 180 }` on
`db-dumps/`, and a bucket policy with `DenyUnencryptedTransport` plus a Deny for every principal whose
`aws:PrincipalArn` is not the admin role (explicit Deny overrides the CIS task role's `Resource = "*"` Allow).
Then:

```bash
aws s3 cp /home/nghiep/projects/AA-Ecosys/docs/backups/2026-09-16/ s3://aa-ecosys-dev-dr-vault-005097885195/db-dumps/2026-09-16/ --recursive --sse aws:kms --sse-kms-key-id alias/aa-ecosys-dev-dr-vault --profile aa365-admin --region us-west-1
```

```bash
aws s3api list-objects-v2 --bucket aa-ecosys-dev-dr-vault-005097885195 --prefix db-dumps/2026-09-16/ --query 'Contents[].[Key,Size]' --output text --profile aa365-admin --region us-west-1
```

```bash
aws s3api head-object --bucket aa-ecosys-dev-dr-vault-005097885195 --key db-dumps/2026-09-16/tripplanner.dump --query '[ServerSideEncryption,SSEKMSKeyId,ContentLength]' --output text --profile aa365-admin --region us-west-1
```

Then the Option A `shred` line. Verify the deny from a CIS container (ECS exec, boto3 `head_object` on one key must
raise `AccessDenied`).

## 6. Read-only checks still to run (needed MFA, expired during this lane)

```bash
for b in $(aws s3api list-buckets --query 'Buckets[].Name' --output text --profile aa365-admin --region us-west-1); do echo "== $b"; aws s3api list-objects-v2 --bucket "$b" --query "Contents[?contains(Key, '.dump') || contains(Key, 'backups/') || contains(Key, 'pg_dump')].[Key,Size,LastModified]" --output text --profile aa365-admin --region us-west-1 2>&1 | head -20; done
```

Expected: no hits (the G0 run wrote only to the laptop). Any hit is a second copy to handle the same way.

## 7. Change in this branch

`.gitignore`: repo-wide `*.dump`, `*.pgdump`, `*.sql.gz`, `*.sql.zst` and `*.backup` patterns next to the existing
`docs/backups/` rule. No tracked file matches them today (checked with `git ls-files`).

## 8. Private DSN CNAME — what the hand edit needs

Nothing for the CNAME exists yet: the only Route 53 zone in Terraform is the public `lumiguides` zone, and
`modules/rds` outputs `db_endpoint` (host:port), not the bare address.

1. **Infra PR first** (Terraform, then apply): add `output "db_address" { value = aws_db_instance.main.address }` to
   `modules/rds/outputs.tf`; a private `aws_route53_zone` (for example `dev.internal`) with a `vpc { vpc_id =
   module.vpc.vpc_id }` block; `aws_route53_record` CNAME `db.dev.internal` → `module.rds.db_address`, TTL 60.
   Cost: 0.50 USD/month for the hosted zone, query cost negligible.
2. **Check resolution inside the VPC** before any secret edit: ECS exec into the api container,
   `python3 -c "import socket; print(socket.getaddrinfo('db.dev.internal', 5432)[0][4])"` must return the RDS
   private IP. TripPlanner Lambdas and the migrator task are in the same VPC; nothing outside the VPC talks to RDS.
3. **Secrets to edit (host part only; user, password, port, database and query stay):**

   | Secret | Read by | Picks up the change |
   | --- | --- | --- |
   | `aa-cis/dev/rds` (master) | migrator task (roles, set-password, run-script), break-glass | next DB Migrate run |
   | `aa-cis/dev/db-migrator` | DB Migrate, DB Schema Dump, isolation probe | next run |
   | `aa-cis/dev/rds-cis-app` | aa-cis-dev-api + aa-cis-dev-worker `DATABASE_URL` | new ECS deployment |
   | `aa-cis/dev/rds-app-user` | CIS tenant pool, isolation probe | new ECS deployment |
   | `booking/dev/database-url` | aa-booking-dev-api `DATABASE_URL` | new ECS deployment |
   | `tripplanner/dev/database-url` | TP browse + assembly Lambdas (by ARN, at cold start) | Lambda cold start (bump a config value to force) |
   | `crm/dev/...` DSN (AA-932, not created yet) | CRM | create it with the CNAME from day one |

4. **Edit all of them in one window, master first.** `db/run_migration.py` `set-password` refuses (exit 11) when a
   role secret's host differs from the master secret's host (`dsn_target` comparison, around line 1501). A partial
   switch leaves set-password broken until the rest follow.
5. **TLS stays fine:** every client uses `ssl="require"` / `sslmode=require`; no repo uses `verify-full`,
   `verify-ca` or `sslrootcert` (grep over all four repos). If one ever moves to `verify-full`, the RDS certificate
   does not cover `db.dev.internal` and that client must keep the RDS hostname.
6. **Rollout:** respect the job-idle guard (DM-11.4) for `shared.job` and `booking.job`, then force a new deployment of
   `aa-cis-dev-api`, `aa-cis-dev-worker`, `aa-booking-dev-api`; `/health/ready` on CIS and `/booking/health` must stay 200.
7. **Underscore names:** the consumers read these as `DATABASE_URL` / `TRIPPLANNER_DATABASE_URL_ARN`. Per the
   standing S245+ rule the orchestrator may do the edit by script (never printing a value): read each secret, replace
   only the host with `urllib.parse`, refuse if the old host is not the RDS address, `put-secret-value` from memory,
   log only `secret name: old host -> new host`. Otherwise Nghiệp edits by hand in the Console.
8. **Done-when "used by at least one app":** after step 6, an ECS exec in the api container shows
   `urlparse(os.environ['DATABASE_URL']).hostname == 'db.dev.internal'` and the API is healthy.
