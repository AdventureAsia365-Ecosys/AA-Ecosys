# AA-432 STEP0-2 — Per-tenant X-API-Key at FE proxy: feasibility

Status: **investigate-only, no code changed** (per task scope). Read on `main`, live DB check
(structure only, no plaintext/hash values logged), 22/08/2026.

Architecture decision this investigates (already settled, not re-litigated here): API Gateway
`X-API-Key` = infra-layer client identity (per-tenant rate-limit/revoke); JWT = user/session auth
(unchanged). This means: can the FE proxy attach **each tenant's own** `X-API-Key` when it calls
`/v1/*` on their behalf?

**Short answer: not immediately — it requires a storage-architecture change first.** See Q1.

---

## Q1 — Does `shared.tenants` (or anywhere else) hold the raw key, not just a hash?

**No.** Confirmed two ways:

**Schema** (`information_schema.columns`, live):
```
column_name          | data_type
----------------------+-------------------
api_key_hash          | character varying
last_brand_brief_s3_key | text   ← unrelated (S3 pointer for a DOCX upload, not a key)
```
`api_key_hash` is the only key-shaped column on `shared.tenants`. No `api_key_encrypted`, no
`api_key_plaintext`, nothing reversible.

**Code path that provisions the key** — `api/routers/admin.py`:
- `create_tenant()` (`POST /admin/tenants`, L110-199): generates `plaintext = f"cis_{secrets.
  token_urlsafe(32)}"`, computes `key_hash = sha256(plaintext)`, inserts **only `key_hash`** into
  `shared.tenants.api_key_hash`, returns `plaintext` once in the HTTP response body with
  `message="Store this API key securely — it will not be shown again."`
- `generate_api_key()` (`POST /admin/tenants/{id}/generate-key`, L722-749): identical
  pattern for rotation — new plaintext generated, only the new hash persisted, plaintext returned
  once, same "will not be shown again" message.

This is the standard show-once/never-persisted secret pattern (same category as password
hashing) — **by design, not by oversight**. Once the HTTP response is sent, the plaintext is gone
from every system that follows this code path. `lambda_authorizer/handler.py` (re-confirmed)
does the same thing in reverse: hash whatever it receives, compare to `api_key_hash`. There is no
decrypt/reverse step anywhere because none is possible — SHA256 is one-way.

**One misleading comment, worth flagging:** `api/migrations/007_seed_test_tenants.sql:21` says
*"api_key_hash = SHA256 of the raw key (raw keys stored only in Secrets Manager)"* — this does
**not** describe the current system. Grepped every `secretsmanager` call in the app
(`api/main.py:104`, `api/core/sentry.py`): the only Secrets Manager usage is
`aa-cis/dev/api-keys` (external LLM/DataForSEO provider keys for the S2 graph) — a completely
different secret, unrelated to tenant B2B API keys. **Nothing writes a tenant's raw key to
Secrets Manager today.** The migration 007 comment describes an intent that was apparently never
implemented, or was implemented once for those 2 seed rows only and never generalized — either
way, don't trust that comment as a description of current behavior.

**Related finding, separate from the architecture question but time-sensitive:** migration
007's plaintext test keys are committed directly in the SQL file, in cleartext, in git history:
`wl_live_sk_test_wanderlux_2026` (WanderLux Travel) and `ea_live_sk_test_exploreasia_2026`
(ExploreAsia Co.). WanderLux Travel (`slug=wanderlux-travel`) is confirmed **`is_active=true`
right now** (see Q3) with the same `tenant_id` as the migration row — meaning that April test key
may still be a **live, valid credential sitting in cleartext in version control** this instant,
independent of anything else in this report. Recommend rotating that tenant's key (`POST
/admin/tenants/{id}/generate-key`) regardless of which direction is chosen below — this isn't
blocked on any of the open questions.

---

## Q2 — If no plaintext exists, what are the ways forward?

### 2a. Secrets Manager, one secret per tenant

- `create_tenant()` / `generate_api_key()` additionally call
  `secretsmanager.create_secret()` / `put_secret_value()` with `SecretId = f"aa-cis/dev/tenant-
  api-keys/{tenant_id}"`, `SecretString = plaintext` — right after computing the hash, before
  discarding the plaintext.
- **The harder part is the read side, not the write side.** The proxy that needs the key is
  `frontend/app/api/tenant/[...path]/route.ts`, running as a **Vercel** serverless function — not
  an AWS-hosted service. It has no IAM role. To call `secretsmanager:GetSecretValue` it would need
  a long-lived AWS access key stored as a Vercel env var — i.e. a *new* durable AWS credential
  living outside AWS's own trust boundary, similar in kind to how `ADMIN_SECRET` already works for
  the staff branch, but now able to read every tenant's gateway key if that Vercel env leaks.
  - Alternative to avoid a Vercel-held AWS key: proxy the lookup through FastAPI (which already
    runs in ECS with a task IAM role) — e.g. an internal endpoint the Next.js proxy calls first to
    fetch the tenant's key, keyed by the `tenant_id` already decoded from the JWT. This avoids
    putting AWS credentials in Vercel, but adds a second network hop per request (or requires a
    cache) and needs its own auth (can't sit behind the very authorizer we're trying to satisfy —
    would need to be a `/admin/*`-shaped route or similar, which is a bit of a semantic stretch
    for a per-tenant self-lookup). Flagging as a real open design question, not solving it here.
  - Either way, a **cache is needed** — calling Secrets Manager (or the FastAPI lookup) on every
    single `/v1/*` request adds latency and cost. Vercel functions are frequently cold-started, so
    an in-process cache has limited hit rate; would likely want a short-TTL edge/KV cache (Vercel
    Edge Config or similar) rather than relying on in-memory caching alone.
- **Migration for existing tenants:** since no plaintext survived for any tenant except (by
  accident) `wanderlux-travel`'s stale April test key, **every currently active tenant needs a
  forced key rotation** (`generate_api_key()`) to backfill Secrets Manager — there's no way to
  recover what was never stored. This is real ops work: each tenant needs to actually receive
  their new key somehow. I didn't find an existing "resend/redeliver key to tenant" flow in this
  codebase — today the only distribution channel is the one-time API response to whoever calls
  the admin endpoint. Worth checking with Nghiep how the 6-7 real active tenants currently *use*
  their key at all today (see Q3 — some of what's in the table looks like leftover test data, not
  live customers), since that determines how disruptive a forced rotation actually is.
- **Complexity: MEDIUM** — bounded, well-understood AWS pattern, but touches 2 endpoints + a new
  cross-cloud credential/routing decision for Vercel + a real (if small) migration/notification
  task for existing tenants. Not a same-day patch.

### 2b. Tenant supplies their own key at setup (instead of system-generated)

- Inverts the current flow — instead of the system minting `cis_...` and hashing it, the tenant
  types in / pastes a key during onboarding, which the proxy would then need to read back from
  "somewhere not hashed" (session storage, a dedicated non-hashed table) to attach per request.
- This doesn't actually avoid the storage question 2a has to answer — it just relocates who
  originates the value. The proxy still needs a durable, reversible read path to *some* store
  holding the raw key, so it inherits the exact same plaintext-at-rest tradeoff as 2a (Q4) without
  2a's benefit of using an established secret-management primitive purpose-built for this.
- Worse on product grounds too: the whole rationale for `X-API-Key` being an infra-layer,
  not-user-facing concern (per the settled architecture decision) argues *against* asking tenants
  to manually manage it — that's exactly the layer they're not supposed to need to touch.
- **Not recommended** — carries 2a's security cost plus extra UX/onboarding cost, no offsetting
  benefit found while reading the code.

### 2c. A third option, found while reading — worth a few minutes before committing to 2a

`api/routers/v1_tours.py`'s `get_tenant()` already decodes the JWT itself and does not consult
the gateway authorizer's per-tenant context at all (confirmed in STEP0). That means the *actual*
reason `X-API-Key` exists per tenant — independent rate-limit/revoke per AA-13 — could be
satisfied **without ever storing a recoverable secret**, by moving per-tenant rate-limit/revoke to
the application layer: a REQUEST-type API Gateway authorizer (or no gateway-level per-tenant auth
at all, just a shared edge check) plus Redis-backed per-tenant throttling keyed on the JWT's
`tenant_id` — `app.state.redis` is already wired up in `api/main.py`, so the primitive exists.
Revoke becomes "flip `is_active=false`" (already how it works) instead of "the specific key value
must be invalidatable."

This doesn't produce a per-tenant `X-API-Key` at all — it's a genuine alternative to the
"per-tenant key at the gateway" premise, not a variant of it, so it may not match what was
"chốt"'d if the decision specifically wants the API-Gateway usage-plan/key mechanism itself
preserved for its built-in throttling. Surfacing it because it sidesteps Q4's tradeoff entirely,
not because it's clearly better — worth 5 minutes of Nghiep/Claude Chat's attention before ruling
it out, since 2a's cross-cloud-credential wrinkle (above) is a real complication 2c doesn't have.

---

## Q3 — Current tenants: structure only, no hash values logged

Live query, `shared.tenants`, 14 rows total (checked `is_active`, whether `api_key_hash` is
non-null, and its length — never the value):

| slug | name | is_active | has_hash | hash_len | created_at |
|---|---|---|---|---|---|
| aa_internal | Adventure Asia Internal | true | true | 64 | 2026-04-20 (internal sentinel, not a real tenant) |
| exploreasia-co | ExploreAsia Co. | **false** | true | 64 | 2026-04-20 (migration 007 seed) |
| wanderlux-travel | WanderLux Travel | **true** | true | 64 | 2026-04-20 (migration 007 seed — see Q1 cleartext-key finding) |
| peakadventures | PeakAdventures | true | true | 64 | 2026-04-21 |
| test-agency | Test Agency | false | true | 64 | 2026-04-30 |
| lumitest | lumitest | false | true | 64 | 2026-05-06 |
| atlas-hearth | Atlas & Hearth | true | true | 64 | 2026-05-19 |
| terra-family-expeditions | Terra Family Expeditions | true | true | 64 | 2026-05-19 |
| trail-pulse | Trail Pulse | true | true | 64 | 2026-05-19 |
| wildkind-travel | WildKind Travel | true | true | 64 | 2026-05-19 |
| sri-landka | Sri Lanka UAT | false | true | 64 | 2026-05-22 |
| aa309-verify-c5316bd4 | AA-309 Live Verify Tenant | true | true | 64 | 2026-08-08 |
| aa-384-live-verify | AA-384 Live Verify | true | true | 64 | 2026-08-08 |
| test-n1-flow | TEST-N1-flow | true | true | 64 | 2026-08-12 |

**Every single row has `has_hash=true`, `hash_len=64`** (valid SHA256 hex) — zero exceptions.
Confirms Q1 at the data level, not just the code level: no tenant, old or new, has a recoverable
key sitting anywhere.

The 3 named in the task: `test-agency` (inactive), `wanderlux-travel` (active — the cleartext-in-
git one), `wildkind-travel` (active) — all present, all hash-only, matches expectations.

**Noticed in passing, not core to this report:** 3 rows (`aa309-verify-c5316bd4`,
`aa-384-live-verify`, `test-n1-flow`) look like leftover live-verify tenants from prior sessions'
"Verify LIVE" steps (AA-309, AA-384) that are still `is_active=true` — AA-430's own notes describe
deleting its equivalent verify tenant afterward. Flagging so it isn't lost, not fixing it here
(out of scope).

**If pursuing 2a:** of the 10 `is_active=true` rows, up to 3 are probably test artifacts rather
than real customers (worth confirming with Nghiep) — so the real forced-rotation count is likely
closer to 6-7 tenants (aa_internal + wanderlux-travel, peakadventures, atlas-hearth,
terra-family-expeditions, trail-pulse, wildkind-travel), not all 10.

---

## Q4 — Security tradeoff: hash-only vs. plaintext-somewhere

This is a real, structural security posture change, not an implementation detail — flagging
plainly per the task's ask, not picking a "least bad" option silently.

**Today:** a full DB compromise (SQL injection, backup leak, insider access, a misconfigured
snapshot) yields only SHA256 hashes. Because the underlying keys are 32 bytes of
`secrets.token_urlsafe` randomness (not human-chosen passwords), a plain unsalted SHA256 is
actually fine here — there is no dictionary/rainbow-table risk against 256 bits of real entropy,
so this isn't "weak hashing," it's the correct tradeoff for random-token secrets. **The keys are
structurally unrecoverable even if the database itself is fully compromised.**

**Under 2a (Secrets Manager):** this changes to "the keys are recoverable if [IAM policy on
`aa-cis/dev/tenant-api-keys/*`] is misconfigured, OR [whatever new credential lets Vercel reach
Secrets Manager] leaks, OR [the internal FastAPI lookup route, if that's the chosen path] is
reachable by something it shouldn't be." AWS Secrets Manager is a legitimate, well-controlled
place to hold secrets (KMS encryption at rest, IAM-scoped access, CloudTrail-audited) — this is
not "write plaintext to a log file." But it is unambiguously a downgrade from *structurally
impossible to leak* to *leak is possible if a specific, real new access path is compromised*.
The Vercel-side wrinkle in 2a above (a long-lived AWS credential living in a non-AWS platform, or
a new internal lookup endpoint) is exactly the kind of new access path this concern is about —
it's not hypothetical, it's the actual thing that would need to exist for 2a to work.

2b carries the identical tradeoff (still needs a durable, reversible store somewhere), so this
applies to it equally.

**Recommendation on Q4 specifically:** don't decide this as a side effect of picking 2a for
convenience — it deserves an explicit sign-off from Nghiep as its own decision, separate from
"which option is less code to write."

---

## Bottom line

1. **Per-tenant `X-API-Key` at the FE proxy is not deployable as-is.** No plaintext exists
   anywhere for any of the 14 tenants (confirmed at both code and live-data level) — this isn't a
   quick wiring change, it requires a genuine storage-architecture addition first.
2. **If proceeding, 2a (Secrets Manager) is the sounder of the two named options** — 2b inherits
   the same security tradeoff with worse UX and no offsetting benefit. But 2a has a real open
   design question (how a Vercel-hosted proxy reaches an AWS secret without holding a long-lived
   AWS credential itself) that needs an answer before implementation, not during.
3. **Worth 5 minutes of consideration: 2c (move per-tenant rate-limit/revoke to the app layer,
   keyed on the JWT's `tenant_id`, using the Redis connection that already exists)** — it fulfills
   the underlying AA-13 goal without ever needing a recoverable secret, sidestepping Q4 entirely.
   It does mean API Gateway stops doing per-tenant differentiation, which may or may not fit
   what was already decided — flagging as an option, not a counter-proposal.
4. **Forced key rotation is required for existing tenants either way** (2a or 2b) — roughly 6-7
   real active tenants, pending confirmation of which of the 10 `is_active=true` rows are real
   customers vs. leftover verify artifacts.
5. **Independent, time-sensitive finding:** `wanderlux-travel` is active today and its original
   plaintext key is sitting in cleartext in a git-tracked migration file — recommend rotating that
   one regardless of which direction this task resolves to.

No code changed. Awaiting Nghiep + Claude Chat to pick a direction (2a / 2c / other) before any
implementation work starts.
