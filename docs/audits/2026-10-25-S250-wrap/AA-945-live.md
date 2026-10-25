# AA-945 (CRM-17 agency mail) — live verification, Dev

Session S250, 2026-10-25 (UTC 04:30–04:45). Agent: Claude Code (subagent). Account acc2, us-west-1.
No paid LLM call was made (the ingest path has no LLM step). No push, no merge.

Deployed state checked: AA-Partner `88be0b1` (#47, CRM-17) on ECS `aa-crm-dev-api:41`, rollout COMPLETED, 1 task.
The crm.job worker runs inside the API task (no separate worker service).

## 1. Infra (Infra #375)

| Check | Result |
|---|---|
| MX `crm-in.lumiguides.it.com` (public resolver and authoritative `ns-178.awsdns-22.com`) | `10 inbound-smtp.us-west-1.amazonaws.com.` |
| Active SES receipt rule set | `aa-cis-dev-e2e` |
| Rule order | 0 `e2e-cognito` (e2e-mail recipients -> `aa-cis-dev-e2e-mail-…/inbound/`), 1 `aa-crm-dev-ingest` |
| `aa-crm-dev-ingest` | Enabled, TLS Require, ScanEnabled true, recipients `crm-in.lumiguides.it.com`, single S3Action -> `aa-crm-dev-ingest-<acc2>`, prefix `raw/` |
| Ingest bucket | SSE `aws:kms`, public access block all 4 true, lifecycle `raw-mail-1d` (1 day) Enabled |
| Sending identity `lumiguides.it.com` | DOMAIN, verified for sending, DKIM SUCCESS; account production access on |

## 2. API readiness and job kinds

- `GET https://partner-dev.lumiguides.it.com/crm/health` -> 200, version 0.3.0, git_sha `88be0b1…`.
- `GET /crm/health/ready` -> 200 `{"status":"ok","db":"ok","schema_version":"crm-015","membership_feed":"ok","keys":"kms"}`.
  The ready body has no mail-specific field; crm-015 is the registered schema version.
- Worker start line (log group `/ecs/aa-crm-dev`, stream `api/api/31ca876b…`, 03:23:10Z) lists `crm_mail_health`,
  `crm_mail_history_import`, `crm_mail_ingest` among 15 kinds.
- First `crm_mail_ingest` run at 03:23:12Z: `succeeded: {'setup_notice_count': 1}` (the SES rule-setup notice object
  was consumed).
- `crm_mail_health` has not run yet: it is daily from `JOB_RETENTION_UTC_HOUR` (default 19 UTC); the task started 03:23Z.

## 3. End-to-end forward-in test (no human)

1. Signed in as the seeded e2e owner of agency "Lữ hành Sen Vàng" (tenant `bab16039-a064-517f-a99f-172b729ad3c4`),
   the same user the Partner "E2E Dev" workflow uses: partner pool `aa-partner-dev`, client `partner-web`,
   Cognito `USER_AUTH` with password + TOTP from secret `crm/dev/e2e-test-crm/sen-vang-owner` (values never printed).
2. `GET /crm/v1/mailbox/ingest-address` -> 200, address `lu-hanh-sen-vang-5a04************@crm-in.lumiguides.it.com`
   (redacted: the 64-bit local part is the only secret). `GET /crm/v1/mailbox` -> 200, no mailbox connected,
   providers `google:false, microsoft:false, smtp:true`. Unmatched inbox before the test: empty.
3. Sent ONE plain-text mail with SES v2 from `aa945-ingest-test@lumiguides.it.com` at 04:39:38Z,
   subject `[TEST] AA-945 forward-in ingest live check S250 20261025T043938Z`, SES MessageId
   `011101a1715b7400-646cac6a-ddba-4a7f-bc75-af1658c39e47-000000`. No `[ref:<token>]`: the trip mail token is not
   exposed by any API, so this tests the Unmatched path, not trip-token matching.
4. Raw object landed: `raw/068gr1lim1bnl1bb3ltg7svdlp7t4b5sr42p1bg1`, 4066 bytes, LastModified 04:39:43Z (5 s after send).
5. Job: `crm_mail_ingest 301ca69f-397b-40ea-bf12-37b91375be32` at 04:40:43Z — `mail_ingest stored=1`,
   `succeeded: {'stored_count': 1}`. No ERROR / Traceback / `mail_ingest_dropped` line after the send.
6. Raw object deleted after commit: `raw/` empty at 04:43Z.
7. Read back through the API as the owner: `GET /crm/v1/conversations?unmatched=true` -> 1 conversation
   `781086ce-826b-4fdb-8fce-2805afb5d0da`, channel `email`, `message_count 1`, `held_count 0`, `last_direction in`,
   `unmatched true`; `GET /conversations/{id}/messages` -> 1 message, direction `in`, status `received`,
   `match_method unmatched`, subject and From decrypted correctly, no attachment notes.

Leftover test data: the one Unmatched conversation above stays in the Sen Vàng agency (Dev, synthetic). It can be
purged from the Unmatched inbox trash; it does not touch any trip or client.

## 4. Not tested

- Trip-token threading (card E: a reply with `[ref:<mail_token>]` and no `References` lands on the trip): the token
  is not readable through the API without sending from a trip first, and sending needs a connected mailbox.
- Revoked-token hold (card R `held_reconnect`), send-as and Undo: need a connected mailbox.
- Gmail / Microsoft 365 OAuth send-as: needs a human (Google Cloud OAuth client + Entra app values in
  `crm/dev/mail-oauth`, then `crm_mail_oauth_enabled = true`, then browser consent). Providers show `false` on Dev.
- SMTP send-as and the Settings > Mailbox Test button: need a real mailbox app password (human step).
- Unknown forward-in address drop (`mail_ingest_dropped` + `MailIngestDropped` metric): not exercised live.
- Gmail forwarding-confirmation code capture, attachments, history import (mbox/CSV), nightly `crm_mail_health`.
- The web UI (Messages tab, Unmatched inbox page): checked only through the API, no browser screenshots.
