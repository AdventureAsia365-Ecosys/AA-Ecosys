# AA-682 ops-docs bucket — live verify (S256, 29/10/2026)

- Infra #489 (`77185f97`) + CI apply 40788053737; Booking #142 (`5a115023`).
- Bucket: public access block 4/4 true, default encryption AES256; admin role PutObject → AccessDenied (explicit deny in the bucket policy).
- `/booking/health/ready` storage = {supply_media: configured, ops_docs: configured}.
- In-container verify (`aa682_ops_docs_verify.py`, service functions as the E2E staff row):

```
store configured
staff_role admin ops.write True
upload SB-000004 <file-id> active 90
download sha256_match True attachment True sse AES256
remove removed
audit_rows_naming_file 3
RC=0
```
