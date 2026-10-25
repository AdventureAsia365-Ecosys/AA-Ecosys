# AA-835 close-out runbook (S251) — supply content evidence run + paid consumer trial

Goal: produce every Done-when proof of AA-835 (root ADR 0004a) in one job window, then close the issue per aa-ship.
Folder: `/home/nghiep/projects/AA-Ecosys/.tmp-session/s251/aa835/` (scripts in `scripts/`, transcripts in `out/`,
full JSON copies of the CIS scripts in `out/s3/` pulled from `s3://aa-cis-bronze-<acc2>/scripts/s251/aa835/out/`).

Who runs it: the **orchestrator** (the subagent hook blocks `aws ecs execute-command` for subagents).
Every command below is one line. `cd /home/nghiep/projects/AA-Ecosys/.tmp-session/s251/aa835` first.

**Revised after check:aa835 (S251, 7 points, see §8).** What changed for the person running it:
- `scripts/exec.sh` now passes **every** argument after the script (`exec.sh booking scripts/10_booking_act.py rename H`
  works). Arguments must be plain tokens (uuid, `HTL-`/`SVC-` code, `true`/`false`, `hotel`/`service`); anything
  else is refused before any AWS call.
- Every script prints `BEGIN …`, then short `KV KEY=value` lines (ids, versions, statuses, yes/no checks), then the
  full JSON as numbered `J i/n` chunks (≤ 800 bytes per line), then `END tag=…`. `exec.sh` ends with
  `TRANSCRIPT_COMPLETE` or `TRANSCRIPT_INCOMPLETE`. **Read the KV lines; they are the evidence.** The JSON is the
  detail: `python3 scripts/parse.py out/<file>.txt` joins the chunks and says if one is missing.
- `TRANSCRIPT_INCOMPLETE` after a **read** (sizing, `show`, `detail`, `status`): run it again. After a **write**
  (`setup`, `rename`, `upload`, `rights`, `deactivate`, `publish`, `photo409`, `replay`, `pull`): do **not** rerun
  blindly; run `bash scripts/exec.sh booking scripts/10_booking_act.py ids` (read-only: the synthetic supplier's
  hotel / service / media ids, statuses and supply_versions) and the CIS snapshot to see what was written.
  `setup` alone is idempotent and safe to rerun.
- The Booking task role has no `PutObject` on the bronze bucket (Infra grants it only `supply-media/*` on its own
  bucket), so Booking scripts print `NOT_STORED …`: expected; the transcript (`tee out/…`) is the record.

## 0. What is live (checked S251, 25/10/2026 ~06:20 UTC, $0, read-only)

| Check | Result |
|---|---|
| STS | acc2 `<acc2>` |
| ECS | `aa-cis-dev-api:819`, `aa-cis-dev-worker:385` (image `dev-4ce6a3aa…` = CIS #998, includes consumer #991), `aa-booking-dev-api:56` (image `174a194…` = Booking #90, includes #84/#86); exec enabled on all three; container name `api` on both api services |
| Health | Booking `/booking/health/ready` 200 `schema_version bk-024`; CIS `/health/ready` 200 `280`, git_sha 4ce6a3aa |
| Env (task defs) | CIS api/worker: no `SUPPLY_FEED_PULL`, no `SUPPLY_CONTENT_LLM`, no `SUPPLY_CONTENT_MAX_DRAFTS_PER_DAY` → pull **on**, LLM **on** (paid default), cap 20/day. Worker `:385` env has `BRONZE_BUCKET` and `PHOTO_CDN_DISTRIBUTION_ID`, no `PHOTO_BUCKET` (→ `photo_bucket()` = bronze) and no `PHOTO_CDN_BASE` (→ default `https://img.lumiguides.it.com`, so the photo copy is not "CDN off"); task role `aa-cis-dev-ecs-task-role`. Booking: `SUPPLY_MEDIA_BUCKET=aa-booking-dev-supply-media-<acc2>` |
| Consumer cursor | `cis_supply_content` last_feed_seq **0**, last_pull_at 06:21:43 UTC, last_error **null** (the sampler pulls every 300 s, no error) |
| Booking supply feed | `booking.v_supply_outbox` **0 events**; `booking.outbox` holds 1 row, stream `b2b` |
| Booking facts | `v_supply_hotels` 2 active (v1, no media), `v_supply_services` 2 active (v1, no media): `ZZ S239 test …` (SUP-000001, AA-822) and `SYNTHETIC S248 …` (SUP-000002, AA-973 seed). `entity_media` 0 rows |
| CIS tables | `supply_entity` 0, `supply_content_version` 0, `supply_event_inbox` 0, `supply_media` 0 |
| Cost so far | `shared.job` supply kinds: 0 ever; `llm_call_log` stage `supply_content_writer`: 0 calls, $0 |
| Stage config | `supply_content_writer` = writer / claude / sonnet / acc3 / active (read only, not changed) |
| Read-back | `catalog.v_supply_content` readable by role `booking` (0 rows, no error) → Booking read-back on |
| Booking staff | 5 active `admin`, 2 inactive `contracting`; `booking.job` queue empty |
| CIS job queue at 06:23 UTC | `a3_atomize` 3 queued + 1 running, `recompute` 1 queued (AA-645 wave live) |
| Booking bucket policy (live, `aws s3api get-bucket-policy`, S251 fix pass) | `aa-booking-dev-supply-media-<acc2>` has `AllowCisTaskReadSupplyMedia` = Allow `s3:GetObject` on `…/supply-media/*` for `<arn>` (the worker's task role), plus `DenyCisTaskWrites` and the TLS / SSE-AES256 denies. Same account, so the bucket policy grant alone allows the read unless the role carries an explicit Deny |
| Terraform (Infra `main` 581b6c4, after #382) | CIS task role: delete on `photos/supply/*` + `cloudfront:CreateInvalidation` present in `modules/ecs/main.tf` |

Not verified (IAM reads are blocked for subagents; checked in S0 by the KV lines or by the step's stop condition):
- **CIS task role, live IAM**: (a) the S10 purge grant (delete on `photos/supply/*`, `cloudfront:CreateInvalidation`);
  (b) no explicit Deny on `s3:GetObject` of the Booking bucket that would cancel the bucket-policy read used by the S8
  photo copy (`photos.copy_rights_cleared` → `s3.get_object`). S8 and S10 each have a stop condition for AccessDenied.
- `shared.spend_budget` and `shared.schema_versions` rows: the first transcript was cut before them. S0 now prints
  them as `KV SPEND_BUDGET=…` / `KV SCHEMA_VERSIONS=…` (expected: bedrock `job:supply_content_draft` run $0.10, day
  $1.00, hard_stop true; `278`, `bk-023`, `bk-024` present).

## 1. How the writes are made (and why this path)

| Path | Verdict |
|---|---|
| **ECS exec into `aa-booking-dev-api` (container `api`) calling Booking's own service functions** (`app.supply.records.create_record / update_record / set_status`, `app.supply.media.upload_media / update_media`, `app.suppliers.service.create_supplier`) with a synthetic `Staff` actor `system:aa835-evidence` | **Use this.** Same code the staff API routes call: bk-023 triggers, outbox rows, audit rows and the S3 put (task role) behave exactly as for a staff request; role `booking` via the container's `DATABASE_URL`; $0; no secrets read. Only the HTTP + Cognito layer is skipped. `supply_version` is read straight from `booking.hotels` / `booking.services` (`records.resolve` / `get_record` at 174a194 do not select it). |
| Booking API over HTTP | No write-capable session: the E2E Booking staff user is read-only (AA-910, Booking #89); the 5 admins are humans. |
| DB Migrate `mode=run-script` as master | Possible for hotel/service rows (triggers fire the same), but cannot upload a photo to S3, bypasses the app's audit/validation, needs a workflow run per step. Fallback only. |
| CIS review | ECS exec into `aa-cis-dev-api` calling `services/supply_content/review.py` (the functions behind `/admin/supply-content`) as `cis_app`, reviewer `system:aa835-evidence` (plan "Evidence approval"). |
| CIS consumer trigger | Automatic: the api's ops sampler runs `pull.pull_once` every **300 s** (`OPS_METRICS_INTERVAL_S`). There is no feed-pull job kind: the pull itself queues `supply_content_draft` jobs (background, concurrency 1, 2 attempts) on `shared.job`, which the **worker** runs (one Sonnet call each). `20_cis_review.py pull` runs the same `pull_once` at once (optional, saves the wait). |

Synthetic supply only: `setup` creates its own supplier `SYNTHETIC S251 AA-835 Evidence Supplier` (hotel + activity,
VN) with one hotel and one service. The AA-822 (`ZZ S239`) and AA-973 (`SYNTHETIC S248`, SUP-000002) records are
never touched (the AA-973 cleanup branch and AA-947 rely on SUP-000002).

## 2. Preconditions (stop if one fails)

1. **Job window.** The run makes the pull queue `supply_content_draft` / `supply_media_purge` rows in `shared.job`.
   Start only when the orchestrator allows writes to `shared.job` (AA-645 wave finished or paused). The draft kind is
   background + concurrency 1, so it cannot starve a wave, but S251's rule says no new `shared.job` rows during the
   wave. Check: `bash scripts/exec.sh cis scripts/00_cis_sizing.py | tee out/p0_cis.txt` → `KV JOB_QUEUE_NOW=…`.
2. **No CIS / Booking deploy from S1 to S11** (draft jobs run on the worker; DM-11.4 also blocks a backend deploy
   while `shared.job` holds jobs). **CIS code round 2 (the `/admin/supply-content/<id>` page) should be deployed
   before S0**: then S3 runs complete at its place. If it is not live by S0, run S0–S12 anyway and do S3b after S12,
   once round 2 is deployed (§4, S3b).
3. `00_cis_sizing` shows `KV CURSOR=… error:None`, `KV WRITER_CALLS=… today_utc:N` with N ≤ 15 (cap 20/day leaves
   room for the 5 calls below), `KV ROLE_CONFIG=writer/claude/sonnet/acc3/active=True`,
   `KV SPEND_BUDGET=bedrock job:supply_content_draft run:$0.10 day:$1.00 hard_stop:True`.
4. Pricing is unchanged: stage `supply_content_writer` = Sonnet on acc3.

## 3. Cost (paid-runs rule: trial ~3, then ≤ ~50)

5 writer calls in total, all Sonnet on acc3 through `LLMClient` (logged in `shared.llm_call_log`, stage
`supply_content_writer`, with the job id): hotel v1, service v1, hotel v3 (rename), hotel v4 (photo without rights),
hotel v5 (photo with rights). ~3k in / ≤1.2k out each ≈ **$0.02 per call, ≈ $0.10 total** (upper bound used by the job's
check: $0.05/call → $0.25). Hard limits already live: 20 calls/day count cap, cost guard `bedrock /
job:supply_content_draft` $0.10/run, $1.00/day, hard stop. Steps S1-read-back, S2, S3, S5, S7, S9, S10, S11 cost $0
(S5 queues no draft: replayed events are duplicates).

**Trial = the first 3 calls (S1 + S4).** Gate after S4: each draft is usable, follows the facts (no invented
activities / services / times / views, writer source-fidelity policy), cost per call ≤ $0.05. Only then S6–S8.

## 4. Run order

`H` = hotel uuid, `S` = service uuid (S1 `KV HOTEL_ID=` / `KV SERVICE_ID=`), `E_H` = CIS entity id of H
(`KV FOCUS_ENTITY=<E_H> …`), `M` = Booking media uuid (S6 `KV MEDIA_ID=`).
"Tick" = wait one sampler pass (≤ 300 s) **or** run `bash scripts/exec.sh cis scripts/20_cis_review.py pull`.
After a tick that queued a draft, wait for the worker (~30–90 s) before reading the result.
Snapshot commands used throughout (all read-only, rerun freely):
- CIS: `bash scripts/exec.sh cis scripts/00_cis_sizing.py H | tee out/<step>_cis.txt` (`KV FOCUS_ENTITY / VERSIONS /
  INBOX / MEDIA / JOBS / LLM` of H)
- Booking: `bash scripts/exec.sh booking scripts/10_booking_act.py show H S | tee out/<step>_bk.txt`
  (`KV HOTEL_CONTENT` / `SERVICE_CONTENT` = `get_record().content`, what `GET /booking/hotels/{id}` returns;
  `KV PROPOSAL_TEXT_KEYS` = `content.published_texts`; `KV PROPOSAL_ITEM_HOTEL` / `_SERVICE` = the same items run
  through `content.attach_to_items`, see §5 point 2; `KV OUTBOX`, `KV MEDIA`)
- Read-back view: `bash scripts/exec.sh booking scripts/01_booking_sizing.py H | tee out/<step>_view.txt`
  (`KV FOCUS_READBACK` = the `catalog.v_supply_content` row)

| Step | Command | Expected | Stop if |
|---|---|---|---|
| S0 preflight | `bash scripts/exec.sh cis scripts/00_cis_sizing.py \| tee out/s0_cis.txt` + `bash scripts/exec.sh booking scripts/01_booking_sizing.py \| tee out/s0_bk.txt` | as §0; §2 KV lines; job window open | §2 fails |
| S1 create (paid ×2) | `bash scripts/exec.sh booking scripts/10_booking_act.py setup \| tee out/s1_setup.txt` | `KV HOTEL_ID`, `HOTEL_CODE HTL-…`, `HOTEL_SUPPLY_VERSION=1`, same for `SERVICE_…`; `HOTEL_CONTENT=status:none …` (read-back on, CIS holds no row yet). Cut transcript → `10_booking_act.py ids` | any error / `HOTEL_CONTENT=null(read-back off)` |
| S1 tick (natural, proves the sampler path) | wait ≥ 300 s, then CIS snapshot for H and for S | `FOCUS_INBOX`: 1× `supply.upsert:v1:facts1:applied` each; `FOCUS_ENTITY … status:draft`→`in_review` after the job; `FOCUS_JOBS`: 1 `supply_content_draft:succeeded` each with cost; `FOCUS_LLM`: 1 row each with cost | cursor error, job `failed` / `stopped_budget`, cost > $0.05/call |
| **S1 read-back while draft** ($0, check #5) | `bash scripts/exec.sh booking scripts/10_booking_act.py show H S \| tee out/s1_bk.txt` | `HOTEL_CONTENT=status:in_review … description:no highlights:0 photos:0 edit_url:/admin/supply-content/<E_H>` (or `status:draft` if the job has not finished), same for the service; `PROPOSAL_TEXT_KEYS=none`; `PROPOSAL_ITEM_HOTEL=description:no highlights:0`, `PROPOSAL_ITEM_SERVICE=description:no …` | any `description:yes` before publish |
| S2 publish | `bash scripts/exec.sh cis scripts/20_cis_review.py publish H` then the same for `S`; `20_cis_review.py detail H` | `KV PUBLISHED=version:… status:published` | `KV REFUSED=…` |
| S2 read-back | Booking `show H S` + view snapshot H | `HOTEL_CONTENT=status:published … description:yes highlights:≥1 photos:0 edit_url:/admin/supply-content/<E_H>`; `PROPOSAL_TEXT_KEYS=hotel:…,service:…`; `PROPOSAL_ITEM_HOTEL=description:yes`, `PROPOSAL_ITEM_SERVICE=description:yes`; view `FOCUS_READBACK=status:published … description:yes` | `HOTEL_CONTENT=null` (read-back off) |
| **S3a UI, Booking ($0, required)** | aa-ui-verify on the fixed Booking Preview host (E2E read-only user has `supply.read`): hotel drawer of H and service page of S at 1440 px and mobile (390 px), light | "Customer content" panel shows the **published** text read-only (status pill "Published", description, highlights) and the "Edit in CIS" link `https://aa-cis.lumiguides.it.com/admin/supply-content/<E_H>`; screenshots into `out/ui/` | panel missing (read-back off) |
| **S3b UI, Edit in CIS ($0, required; only after CIS round 2 is deployed)** | Done here when round 2 was live at S0; otherwise **after S12** (no deploy during S1–S11, §2.2). Check `curl -s https://api-cis.lumiguides.it.com/health/ready` git_sha = the round-2 merge, then from the Booking drawer click "Edit in CIS" for H (and S) | the CIS page `/admin/supply-content/<E_H>` renders the entity after Cognito sign-in (title, status, versions with the published one), desktop + mobile screenshots; no 404. After S12 the entity shows `unpublished` (inactive): still valid, since Booking shows the link for every status (`SupplyContent.tsx` `cisEditUrl`) and `catalog.v_supply_content` keeps `edit_url` for inactive rows (CIS 278, no `WHERE` on the view) | 404 / error page → AA-835 is **not** Done (§6) |
| S4 rename (paid ×1) | `bash scripts/exec.sh booking scripts/10_booking_act.py rename H \| tee out/s4_rename.txt` | `KV BEFORE=1`, `AFTER_SUPPLY_VERSION=3`, `AFTER_NAME=…Riverside Lodge`, `AFTER_STYLE=riverside boutique` (2 outbox rows, v2 + v3, one transaction) | — |
| S4 tick | tick, then CIS snapshot H, Booking `show H S`, view H | `FOCUS_INBOX`: `…:v2:facts3:applied`, `…:v3:facts3:skipped_older`; `FOCUS_ENTITY … applied:3 … status:stale`; 1 new draft job `succeeded`; view `FOCUS_READBACK=status:stale … description:NULL highlights:NULL`; Booking `HOTEL_CONTENT=status:stale … description:no`; `PROPOSAL_TEXT_KEYS` **without** `hotel:`; `PROPOSAL_ITEM_HOTEL=description:no`, `PROPOSAL_ITEM_SERVICE=description:yes` | text still served while stale |
| **Trial gate** | `bash scripts/exec.sh cis scripts/20_cis_review.py detail H` and `… detail S` (+ JSON via `parse.py`) | 3 drafts usable + faithful; `FOCUS_LLM` ≤ $0.05 each | any unfaithful draft → stop, report to Nghiệp before more paid calls |
| S5 replay ($0) | right after a tick: `bash scripts/exec.sh cis scripts/20_cis_review.py replay H \| tee out/s5_replay.txt` | Rewinds to the **first** inbox event of H minus 1 and pulls once, rewind + pull in **one transaction holding the cursor row** (the sampler cannot tick in between). `KV PENDING_BEFORE=0`, `EXPECTED_DUPLICATES=4` (H v1, S v1, H v2, H v3), `PULL=… applied:0 … duplicate:4 drafts_queued:0 …`, `UNCHANGED=True`, `REPLAY_OK=True` | `UNCHANGED=False` with `PENDING_BEFORE=0`. `PENDING_BEFORE>0` means new events were waiting (they get applied, not a fault): tick, then run the replay once more |
| S6 photo, no rights (paid ×1) | `bash scripts/exec.sh booking scripts/10_booking_act.py upload H false \| tee out/s6_upload.txt` | `KV MEDIA_ID=<M>`, `USAGE_RIGHTS=False`, `SIZE=1200x800 ~122000 bytes image/png`, `HOTEL_VERSION=3 -> 4` | `media_storage_unavailable` (bucket/task role) |
| S6 tick | tick, CIS snapshot H | `FOCUS_MEDIA=<M>:rights=False:…:url_1600=None`; draft job v4 `succeeded`, `photos=copied0/failed[]`; `FOCUS_VERSIONS` newest `photos0`; still `stale` | — |
| S7 409 ($0) | `bash scripts/exec.sh cis scripts/20_cis_review.py photo409 H M \| tee out/s7_409.txt` | `KV REFUSED=409 photo_rights media_ids:[M]`, `REJECT_PROBE=rejected`, `UNEXPECTED=none` | `UNEXPECTED=publish succeeded…` |
| S8 rights on (paid ×1) | `bash scripts/exec.sh booking scripts/10_booking_act.py rights M true` → tick → wait for the job → CIS snapshot H | `KV HOTEL_SUPPLY_VERSION=5`; draft job v5 `photos=copied1/failed[]`; `FOCUS_MEDIA=<M>:rights=True:active=True:url_1600=https://img.lumiguides.it.com/supply/hotel/<M>-1600.webp?v=…`; newest version `photos1` | **`FOCUS_JOBS … failed[<M>:…AccessDenied…]`** (bucket-policy read cancelled by an IAM Deny, or the bronze write refused) or any other `failed[…]` → record the job id + error, **stop before publish**, report (S9–S12 can still run: they do not need the photo) |
| S8 publish + CDN | `20_cis_review.py publish H` → view H → `curl -sI "<url_1600>"` | `KV PUBLISHED=… status:published`; view `FOCUS_READBACK … photos:['<url_1600>']`; curl `HTTP 200`, `content-type: image/webp` | 403/404 |
| S9 deactivate ($0) | `bash scripts/exec.sh booking scripts/10_booking_act.py deactivate H hotel` → tick → CIS snapshot H + view H | `KV HOTEL_STATUS=inactive`, `HOTEL_SUPPLY_VERSION=6`; `FOCUS_INBOX` newest `supply.deactivate:v6:facts6:applied`; `FOCUS_ENTITY … active:False status:unpublished published:<kept>`; versions unchanged; **no new draft job**; view `status:unpublished description:NULL photos:None` | a draft job queued for v6 |
| S10 withdraw rights ($0) | `bash scripts/exec.sh booking scripts/10_booking_act.py rights M false` → tick → wait ~60 s → CIS snapshot H | `HOTEL_SUPPLY_VERSION=7` (`supply.deactivate`, still inactive); `FOCUS_JOBS` 1 `supply_media_purge:succeeded`; `FOCUS_MEDIA … url_1600=None`; after the CloudFront invalidation (1–5 min) `curl -sI "<url_1600>"` → 403/404 | purge `failed` with AccessDenied → the Infra grant is not live (record; the view already hides the photo) |
| S11 service off ($0) | `bash scripts/exec.sh booking scripts/10_booking_act.py deactivate S service` → tick → view S | `KV SERVICE_STATUS=inactive`; view `FOCUS_READBACK=status:unpublished description:NULL` | — |
| S12 close snapshot | `00_cis_sizing.py H`, `00_cis_sizing.py S`, `01_booking_sizing.py H`, `20_cis_review.py status` | totals for the Linear comment; `KV WRITER_CALLS=calls:5 … cost:$≈0.10` | — |
| S3b (if not done at S3) | see S3b row above, after the CIS round-2 deploy | | |

Optional HTTP proofs ($0): `GET /booking/hotels/H` with a staff token (E2E read-only user is enough: `supply.read`);
the S3 object checks `aws s3api head-object --bucket aa-cis-bronze-<acc2> --key photos/supply/hotel/<M>-1600.webp
--profile aa365-admin --region us-west-1` (200 after S8, 404 after S10; worker has no `PHOTO_BUCKET`, so the photo
bucket is bronze).

## 5. Evidence for the Linear close comment (AA-835)

From the transcripts (`out/*.txt`: KV lines + `parse.py`) and the CIS JSON copies (`out/s3/*.json`):
1. Health: Booking ready bk-024, CIS ready 280, api = worker image.
2. Create → draft → publish → read-back: S1/S2 rows (outbox v1, inbox applied, job ids + cost, version ids, view row,
   `get_record().content`). Draft state shows no text (S1 read-back: `description:no`, no proposal text). **Proposal
   proof level, say it in the comment:** the proof runs `content.published_texts` and `content.attach_to_items` on
   version items shaped exactly like `trip_cases.versions.ITEM_SUPPLY_JSON` (a room-type item carries its hotel as
   `entity_type/entity_id`, a service item its service), which is the call `_items(content=True)` makes on every
   proposal version read. No trip case version was built: the synthetic hotel has no room type, and adding one bumps
   the hotel's supply_version (bk-023 trigger) = one more paid draft and shifted version numbers. Booking #86's unit
   test `test_proposal_items_carry_only_published_text` covers `versions.get_items` → `_items(content=True)` →
   `attach_to_items` with a fake connection; no live proposal read was made.
3. Rename → stale: S4 (v2 applied with facts 3, v3 skipped_older, stale, NULL text, proposal text and item text gone,
   new draft).
4. Replay → no change: S5 (all 4 events re-read as duplicates, `applied 0`, `UNCHANGED True`).
5. Deactivate → unpublish: S9 (rows kept, no draft job).
6. Media rights: S6/S7 (409 `photo_rights`), S8 (CDN 200 image/webp in `photo_urls`), S10 (purge job, copies gone).
7. UI: S3a Booking screenshots (published panel, desktop + mobile) and S3b "Edit in CIS" → CIS page screenshots.
8. Cost: `KV FOCUS_LLM` rows of H and S — calls, tokens, `cost_usd`, account acc3; total vs the $1/day guard.
9. Wave impact: the draft jobs were background kind; `KV JOB_QUEUE_NOW` before/after.

## 6. Gaps found while preparing (decide before marking Done)

- **CIS admin page `/admin/supply-content/<id>`**: absent at the deployed SHA 4ce6a3aa (cut from CIS #991, notes
  "Should know"; not on any CIS branch at this fix pass). `catalog.v_supply_content.edit_url` and Booking's "Edit in
  CIS" link point at it, so today the link 404s after sign-in. It is being built in **CIS code round 2** (list,
  detail with diff, publish / reject / unpublish / regenerate; the API `api/routers/admin_supply_content.py` exists).
  Done-when requires "a working 'Edit in CIS' link" with desktop and mobile screenshots, so **AA-835 is Done only
  after S3b passes on the round-2 deploy.** A new backlog row does **not** meet Done-when; the only other way to close
  is a scoped Done-when exception that Nghiệp approves explicitly (record it in the close comment).
- Evidence records stay on Dev (inactive hotel + service, active synthetic supplier, the Booking photo object; CIS
  copies are purged by S10). Labelled SYNTHETIC; add them to the next supply cleanup run.
- Writer cost guard: a stopped job (cap / budget) is not re-queued. If a step hits the cap, the regenerate is
  `review.request_draft` (`POST /admin/supply-content/{id}/draft`); it is not in `20_cis_review.py` on purpose (one
  more paid call must be a decision, not a script default).

## 7. Cleanup

`aws s3 rm s3://aa-cis-bronze-<acc2>/scripts/s251/aa835/ --recursive --profile aa365-admin --region us-west-1`
after the evidence is copied into `docs/audits/<date>-S251-aa835/` (the `scripts/` prefix has no lifecycle rule).
Remove `out/.last_exec.txt` (scratch copy of the last transcript).

## 8. Fixes after check:aa835 (S251) and how each was verified locally

Verified against the deployed code (CIS `4ce6a3aa`, Booking `174a194`, extracted with `git archive`), $0, no exec:

| # | Problem | Fix | Verified |
|---|---|---|---|
| 1 | `exec.sh` passed only `$3` | passes all args (`ARGS="$*"` after `shift 2`), refuses non-token args, prints `TRANSCRIPT_COMPLETE/INCOMPLETE` | `bash -n`; run with a stubbed `aws` on PATH: the remote command carries `rename <uuid>` and `photo409 <uuid> <uuid>`; `a;rm -rf` refused, exit 2 |
| 2 | `supply_version` not in `records.resolve/get_record` | `supply_version()` reads `booking.hotels|services.supply_version` by id; `version_of`, `brief` (now async) use it | grep of `records.py` at 174a194 (no `supply_version` in `COMMON_COLUMNS` / `HOTEL.columns` / `SERVICE.columns`); fake-conn test: `brief` issues `SELECT supply_version FROM booking.hotels WHERE id = $1::uuid` and returns it |
| 3 | transcript cut at ~1 kB, Booking `NOT_STORED` | `emit()` in all 4 scripts: BEGIN, KV lines, JSON in ≤ 800-byte `J i/n` chunks, END; new read-only `ids` action; `parse.py` joins chunks and flags missing / cut chunks | self-test: every action's output round-trips through `parse.py` (CRLF + trailing `Cannot perform start session: EOF`), longest line 806 bytes, a half-cut transcript keeps all KV lines and reports incomplete; the 4 helper copies are byte-identical; the S251 legacy transcript still parses |
| 4 | UI Done-when marked optional | S3a (Booking screenshots) and S3b (Edit in CIS → CIS page, after the round-2 deploy) required; §6 no backlog-row close | code: `SupplyContent.tsx` shows the link for every status; CIS 278 view keeps `edit_url` for inactive entities |
| 5 | proposal check indirect, no draft-state read | `show` now also runs `content.attach_to_items` on `ITEM_SUPPLY_JSON`-shaped items; new S1 read-back row; §5 states the proof level | test with Booking's real `attach_to_items` (view stubbed published for the hotel only): hotel item gets the text, service item `None`/[] |
| 6 | replay re-read only one event; sampler race | rewind to H's **first** event − 1, rewind + `pull._pull_batch` in one transaction holding the cursor row (`FOR UPDATE NOWAIT`, retry ×3); `pending_before`, `expected_duplicates`, `replay_ok` | signatures of `pull._pull_batch(conn, limit, enqueue_jobs)` and review functions checked at 4ce6a3aa; fake-pool test: one lock-busy retry, rewound_to 0, duplicate 4 = expected, `UNCHANGED/REPLAY_OK True` |
| 7 | S8 photo copy depends on an unchecked grant | live bucket policy read (`AllowCisTaskReadSupplyMedia` → `aa-cis-dev-ecs-task-role`, the worker's role); IAM-side Deny listed as not verified; S8 stop condition on `photos.failed`; worker env (`BRONZE_BUCKET`, no `PHOTO_BUCKET`/`PHOTO_CDN_BASE`) recorded | `aws s3api get-bucket-policy` + `aws ecs describe-task-definition aa-cis-dev-worker` (read-only); `photos.py` / `supply_content_draft_job.py` at 4ce6a3aa: result `photos = {copied, failed[{media_id, error}]}`; `00_cis_sizing` prints it as `photos=copiedN/failed[…]` (tested) |
