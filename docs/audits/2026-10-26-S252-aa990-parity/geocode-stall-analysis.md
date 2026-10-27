# AA-990 / AA-905 — why place geocoding stalled, `unknown_to_model`, dirty countries (read-only)

Run: 27/10/2026 (S252), Claude Code subagent. No DB access, no AWS, no writes, no code change. Code read at
AA-CIS-App `origin/main` **eb1c3f80**. Data: the read-only sweep `.tmp-session/s252/aa990_sweep_db.json`
(`cis_app`, 26/10 23:50Z). Companion report: `f2-f3-investigation.md` (F3 = Pakistan / Philippines missing from the
place guard). That fix is being built on branch `fix/aa-990-country-lists` and is **not repeated here**; this report
only says where it interacts.

## Summary

| # | Root cause | Where (origin/main) | Effect on Dev now | Fix |
|---|---|---|---|---|
| **RC1** | After a credit stop, `place_geocode` does **not** schedule itself again. Nothing else runs it on a timer: there is no cron or recurring slot, and only `place_extract` enqueues it | `services/jobs/place_geocode_job.py:138-141` (no re-enqueue), `:15-18` (doc says "the next place_extract / backfill picks them up"); sole trigger `services/jobs/place_extract_job.py:36-39` | AA-905 lots 1–8 ended about 15:10Z on 26/10. **3,956 pending names, never tried, all due**, plus 180 due `unknown_to_model` retries. The credits reset at 00:00Z on 27/10, but no job is queued, so the backlog waits for the next `place_extract`. Japan 458, Philippines 450, Sri Lanka 473, Thailand 409, South Korea 346, Taiwan 255, Pakistan 266, India 239, Nepal 875 | Fix A: on `stopped_credit_limit` with names still due, enqueue one `place_geocode` with `run_after` = next UTC midnight + 10 min, using a per-day idempotency key. Ops now: enqueue one `place_geocode` from the worker |
| **RC2** | The 12 runs every 20 min that each show "names 400, resolved 0" are **not** retries. Each `place_extract` of the lots queued a debounced geocode; the coalesce cap fired every `MAX_WAIT_S` = 1,200 s. Each run found 0 credits left, deferred all 400 names (no model call, $0), relinked, and stopped | `services/places/enqueue.py:72-96`, `services/places/pipeline.py:312-317` | Harmless ($0), but on the Jobs page they look like successful runs | Covered by Fix A. The `succeeded` status is by design: `result.status = stopped_credit_limit` |
| **RC3** | `unknown_to_model` is a catch-all. `parse_answer` returns `None` for four different cases: (a) the model said `null`; (b) the label is **missing** from the answer (case and whitespace only are tolerated; a `"X (Locality)"` label answered as `"X"`, a wrapped object or a re-spelled key all miss); (c) the model gave a country that `canonical_country` does not know (**Pakistan, Philippines** until F3, Russia, Kazakhstan, North Korea, Tanzania, "Hong Kong", "Tibet Autonomous Region", "Lao People's Democratic Republic"…); (d) a malformed value. Every case costs a try (retry in 1 day, `unknown` after 3) | `services/places/locate.py:141-153` (lookup, canonical country → None), `:202-205` (→ `unknown_to_model`); `services/places/store.py:660-677` (`retry_days=1`, `max_tries=3`) | 803 pending + 217 terminal `unknown` = **1,020** names. 124 are PK/PH (case c, F3). 5 are non-AA countries (case c). About **890** are in AA countries: India 323, Laos 200, China 109, Nepal 64, Bhutan 51, Mongolia 40, Japan 21, Sri Lanka 25, South Korea 25, Thailand 17, Vietnam 12, Taiwan 4. Which case dominates is **unverified**, so run S1–S3 | Fix B: return a reason per label, and do not count a try for "missing from the answer". Non-AA country → terminal `not_aa_country:<country>`. Match keys with `name_norm` and fall back to the plain name |
| **RC4** | `locate: no JSON object` = a whole batch failed to parse. `raw.index("{") … raw.rindex("}")` + `json.loads` fails on an answer cut at `max_tokens` (no closing `}`), on prose after the JSON that contains a `}`, or on an empty or refusal answer. Each name of the batch then **costs a try**: three bad answers turn real places into `unknown`, which contradicts the module doc ("a failed model batch … leaves the names pending") | `services/places/locate.py:136-140`, `:197-201`; `services/places/pipeline.py:332-335` | 9 Laos names. A batch of 9, not 40, fits a chunk cut to the credits left (`pipeline.py:318-322`) or a tail batch | Fix C: parse with `json.JSONDecoder().raw_decode` after stripping fences, unwrap a one-key wrapper, and on failure retry the batch once as two halves before counting a try |
| **RC5** | Dirty `place_name.country` comes from the **place card**. `acp_shared.place_card.country` is the card model's free text ("the one country it is in today", prompt `place_cards.py:97-98`), stored un-normalised (`place_cards.py:735-736`). `build_components` uses it as the component country (`components.py:165,174`). `pipeline.canonical()` returns the raw string when it is not an AA country (`pipeline.py:32-33`, applied at `:110-112`), so `"India and Pakistan"`, `"Nepal and China"`, `"Tanzania"`, `"Russia"` become `geo.tour_place.country` and the `geo.place_name` key. Tour-day anchors use the tour country (`pipeline.py:139`) and are clean | as listed | **46 names** in 13 dirty strings: Tanzania 19, Russia 10, Kazakhstan 4, Nepal and China 4, plus single names. Consequences: (1) the key never matches an existing destination (`store.known_destinations` compares `lower(btrim(d.country))` with the dirty `country_norm`), so a place already on the map is paid for again; (2) a non-AA country (Russia, Tanzania, Kazakhstan, North Korea, Bangladesh) can never pass the guard, so each name pays up to 3 locate tries and ends `unknown` | Fix D: normalise at the card write and in `canonical()`. Use the tour country when it is in the list, else the first AA country. A non-AA-only country → terminal `not_aa_country` with no model call. Then sample with S5 to judge whether those cards are right (Tanzania on an Asia tour is almost certainly a wrong card) |
| **RC6** (to verify) | `due_names` takes **every** pending name, including names that no tour uses any more. The S1 v2 rewrite of 892 tours (25/10) re-extracted places, and old spellings stay `pending` for ever because `place_name` rows are never deleted. Those orphans spend Geoapify credits and model calls with no effect on any tour | `services/places/store.py:292-304` | Unknown share of the 3,956. Run S6 | Fix E: `due_names` / `pending_names_due` pick only names that an unlinked `tour_place` or `tour_day` anchor, or a card without a destination, still references (the partial indexes `tour_place_unlinked_idx` and `tour_day_unlinked_anchor_idx` already exist) |

**T2/T9:** the T2 rewrite and T9 write paths do not read `geo.*` or `shared.destinations`. A grep of
`services/acp_content_writing/`, `services/jobs/t2_rewrite_job.py`, `services/jobs/t9_write_job.py` and
`services/acp_shared/slate.py` finds no `geo.tour_place|place_name|tour_day|tour_stop|shared.destinations|place_geocode`.
T9 reads place **cards** only (`place_cards.py:1-10`). This geocode stall therefore **does not explain a T2/T9
failure**, which needs its own check (job rows and `last_error` for the T2/T9 kinds).

## 1. `place_geocode`: how it works today

### Which names it takes
- `store.due_names` (`store.py:299-304`): `status = 'pending' AND next_retry_at <= now() ORDER BY created_at, name_norm
  LIMIT $limit`. The limit is `MAX_NAMES_PER_RUN = 400` (`place_geocode_job.py:40`). There is no filter for whether
  a tour still uses the name (RC6) and no priority for live tours.
- Names that a known destination or a card destination already answers are resolved with no call
  (`pipeline.py:294-307`). The rest go to `locate.locate_many` in chunks of `locate.BATCH = 40` (`locate.py:37`).

### The Geoapify credit guard
- **2,500** = `geocoder.DEFAULT_DAILY_CREDITS` (`geocoder.py:49`, "stop below the 3,000/day free quota"). The env var
  `GEOAPIFY_DAILY_CREDIT_LIMIT` overrides it (`geocoder.py:385-391`); place_shape shares it (`place_shape_job.py:58`).
- **Per UTC day**: `store.geocoder_requests_today` (`store.py:765-772`) sums `coalesce(credits, requests)` in
  `geo.geocode_call` since `date_trunc('day', now() AT TIME ZONE 'UTC')`. It covers all endpoints, so place_shape
  `place_details` credits count too. That sum is read once at job start (`place_geocode_job.py:95-97`), and
  `credits_left()` = limit − start value − this run's requests (`geocoder.py:234-235`).
- Credits per name: 1 search, up to 3 for "X to Y" endpoints or the native-script retry (Taiwan / South Korea), 0 for a
  generic phrase (`geocoder.py:287-315`). Every 429/5xx retry also costs a credit (`geocoder.py:245-285`). Rows are
  written once per run in the `finally` (`place_geocode_job.py:111-119`).
- Snapshot, 26/10: geoapify 2,489 requests / **2,500 credits** (limit reached), overpass 216 (free). 25/10: 419 / 423.

### What a credit stop does
1. Before each chunk: `credits_left() <= 0` → all remaining names are `deferred` and the loop stops **before** the
   model call (`pipeline.py:312-317`). If fewer credits are left than names in the chunk, the chunk is cut to
   `left` names (`:318-322`). A mid-chunk `CreditLimitReached` defers the rest of that chunk (`locate.py:217-219, 227-229`).
2. Deferred names are untouched: still `pending`, no try counted, `next_retry_at` unchanged (`pipeline.py:327-331`).
3. The `finally` still relinks and runs the outlier rule. Because `touched` is empty, `apply_outlier_rule(conn, None)`
   re-evaluates **all** sources (`pipeline.py:359-364`). That is cheap but wasted.
4. The job returns normally → `shared.job.status = 'succeeded'` with `result.status = 'stopped_credit_limit'`
   (`place_geocode_job.py:138-141`). It does **not** re-enqueue. The docstring (`:15-18`) relies on "the next
   place_extract / backfill". The same applies to `stopped_geocoder_unavailable` (`:133-137`), which needs an
   operator and is correct to leave.

### What schedules it
- Only `place_extract_job.follow_ups` (`place_extract_job.py:33-41`), when an extract ends `ok|partial|rebased`
  **and** `pending_names_due > 0`. An unchanged build returns `skipped_unchanged` and queues nothing.
- `enqueue_debounced` (`enqueue.py:89-96`): one queued job absorbs every enqueue. `run_after` slides to
  now + 180 s, capped at `created_at + 1,200 s` (`:72-86`). During a lot this gives one run about every 20 min, which
  is the pattern in the snapshot (10:34 … 15:10Z).
- The job re-enqueues itself only on the "continue" branch: names left and this run had names (`place_geocode_job.py:142-144`).
- `PLACE_PIPELINE_AUTO` (`enqueue.py:27-35`) gates only the automatic **place_extract** of never-built tours
  (end of A3 atomize, card relink). AA-989 `maintain_built` (`:38-65`) lets built sources re-extract. It does not
  schedule geocoding. There is **no** recurring slot for any place kind in `shared/jobs/` or in AA-CIS-Infra.

### Retry rules (`store.mark_name`, `store.py:660-677`)
- Any non-deferred failure (`unknown_to_model`, a guard reason such as `outside_country_bbox`, `locate: …`, a geocoder
  error) → `tries + 1`, `next_retry_at = now() + 1 day`, and `status = 'unknown'` once `tries ≥ 3`. `unknown` is
  terminal: `due_names` reads only `pending`, so the snapshot's "due_now" on `unknown` rows means nothing.
- Same model, same prompt shape, temperature 0 (`llm.py:27-30`): a `null` answer usually repeats, so the 2nd and
  3rd tries mostly pay to confirm the first.

### The model `locate` step
- This step is the **primary** proposer, not a fallback. One `a3_place_locate` call per ≤ 40 names
  (`locate.py:8-13, 173-231`) returns `[lat, lng, country, native?]`. Geoapify then confirms it. When Geoapify finds
  no accepted candidate, the model point is kept as `located_by='llm'`, precision `area`, and hard kinds go to the
  `/admin/places` review list (`locate.py:234-249`).
- Cost: the design cap is ≤ $0.015 per call (`llm.py:23-24`, pre-call estimate $0.02). The budget row is
  `bedrock/job:place_geocode` at $3/run (`place_geocode_job.py:12`, mig 226). 3,956 names ≈ 99 calls ≈ **$1.5–2**.
  The 803 pending `unknown_to_model` retries ≈ 20 calls per round. S3 gives the real $/call from `shared.llm_call_log`.
- A full "model only" mode exists: `GEOCODER_PROVIDER=model_only` (`geocoder.py:175-190, 382-384`) makes no Geoapify
  call. It is **not** a credit-stop fallback. Points stored that way stay `llm`/area, because a resolved name is never
  re-queued, so I do not recommend switching to it to drain the backlog.

## 2. `unknown_to_model` and the parse error

`parse_answer` (`locate.py:132-154`):

```python
start, end = raw.index("{"), raw.rindex("}") + 1      # :137  first "{" … last "}"
data = json.loads(raw[start:end])                      # :138  → ValueError "no JSON object…" (RC4)
lower = {str(k).strip().lower(): v for k, v in data.items()} if isinstance(data, dict) else {}   # :141
v = lower.get(n.lower())                               # :144  label must match up to case/outer spaces (RC3 b)
lat, lng, country = float(v[0]), float(v[1]), guards.canonical_country(v[2])   # :146
out[n] = Proposal(...) if country else None            # :153  non-AA country → None (RC3 c)
```

and `locate_many` (`locate.py:202-205`) maps every `None` to `reason="unknown_to_model"`. So one label covers:

| Input | Ends as | Correct? |
|---|---|---|
| Model returns `null` (does not know it, or a generic phrase like "local village") | `unknown_to_model` | yes |
| Model answers but re-spells the key (diacritics, "Mt." vs "Mount", drops the `" (Locality)"` part of a generic name's label `locate.py:65-66`), or wraps the map (`{"places": {...}}`) | `unknown_to_model`, try counted | **no**: the model knew it. A wrapped answer fails all 40 names of the batch together |
| Model's country not in `COUNTRY_ISO2` (`guards.py:21-26`): Pakistan / Philippines (F3), Russia, Kazakhstan, North Korea, Tanzania, Bangladesh, "Hong Kong", "Tibet Autonomous Region", "Lao People's Democratic Republic", "Myanmar (Burma)" | `unknown_to_model` | **no**: these are a known place in a country the guard does not take. Snapshot proof: `Kazakhstan` names and `India, Pakistan, China` are already `unknown_to_model` |
| Model answers with the wrong shape (object instead of array) | `unknown_to_model` | should be "malformed" |
| Model gives a point outside the country's bounding box | `outside_country_bbox` (`guards.py:97-107`) | yes |
| Whole answer unparsable | `locate: no JSON object in the locate answer: …` on every name of the batch, try counted | **no**: this is transient, not a fact about the names |

Country in the prompt: `Item.country` is the name row's country (card country or tour country), shown as
"tour country" only (`locate.py:118-129`). The guard and Geoapify's `countrycode` filter use the **model's** country
(`geocoder.py:289`), and destinations are keyed by it (`store.py:410-446`). A dirty input country therefore does not
put a point in the wrong country. It only breaks key reuse (RC5) and wastes tries.

## 3. Dirty country strings

Path: the card model writes `country` → `acp_shared.place_card.country` (`place_cards.py:735-736`, no
normalisation) → `store.ATOMS_SQL` `pc.country AS card_country` (`store.py:78-88`) →
`components.build_components`: `link_country = card_country or tour_country` (`components.py:165`) →
`pipeline.extract_tour_places`: `c.country = canonical(c.country)`, where a non-AA string comes back unchanged
(`pipeline.py:32-33, 110-112`) → `geo.place_name` row (`pipeline.py:134`, `store.insert_names`) and
`geo.tour_place.country/country_norm`. The component **id** uses the tour country (`components.py:172`), so
normalising the link country does not change component ids (no AA-989 impact). It changes the name **key**, though.

What should happen with cross-border places:
- **"A and B" / "A, B, C"** (border features: Everest, K2, Kanchenjunga, Mekong, DMZ): the place has one
  coordinate, and the model's answer decides its country. The key should use the **tour's country when it is in the
  list**, else the first AA country in the list. That way it reuses the destination other tours already resolved.
  The card's country should be normalised the same way at write time.
- **Only a non-AA country** (Russia, Kazakhstan, North Korea, Bangladesh): a real neighbour the route crosses into.
  The guard cannot store it (no ISO entry, no bbox), so today it pays 3 locate tries and ends `unknown`. Minimal
  correct: mark it `unknown` / `not_aa_country:<country>` once, with no model call. The day shows unpinned. A product
  option is to add the neighbours actually on routes to `guards.py` (its docstring already allows "a neighbour it
  crosses into"). That would be a separate decision, and F3's drift test must then accept a superset.
- **Tanzania (19 names), and any other country far from every AA route**: almost certainly a wrong card (identity
  check passed). Run S5. If confirmed, reject those cards (an admin action) and re-extract the affected tours.

## 4. Minimal fixes (code, not applied)

All in AA-CIS-App. They sit on top of F3 (`guards.py` Pakistan / Philippines) and do not repeat it.

**Fix A — reschedule after a credit stop** (`services/jobs/place_geocode_job.py`)

```python
from datetime import datetime, timedelta, timezone
from shared.jobs.registry import enqueue

CREDIT_RESET_DELAY_S = 600          # 00:10 UTC: Geoapify's daily credits have reset


def next_credit_day(now: datetime | None = None) -> datetime:
    now = now or datetime.now(timezone.utc)
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight + timedelta(seconds=CREDIT_RESET_DELAY_S)

# in _run_locked, replacing :138-141
        elif result.get("stopped_credit_limit"):
            result["status"] = "stopped_credit_limit"
            if remaining:
                at = next_credit_day()
                result["next_job"], _ = await enqueue(
                    ctx.pool, KIND, {"reason": f"{KIND}:credit_reset"}, created_by=KIND, run_after=at,
                    idempotency_key=f"{KIND}:credit_reset:{at:%Y-%m-%d}")
                result["next_run_after"] = at.isoformat()
            logger.warning(...)
```

Notes: the per-day key gives one job per reset day. Later `enqueue_debounced` calls coalesce into this queued job
(oldest queued), and `GREATEST(run_after, …)` keeps it at 00:10Z (`enqueue.py:77-86`), which is right: the credits
are spent. If an operator raises `GEOAPIFY_DAILY_CREDIT_LIMIT` mid-day, they enqueue by hand. Update the docstring
`:15-18`. Tests: a credit-stopped run with names left queues one job at the next 00:10Z; a second stop the same day
reuses it; `stopped_geocoder_unavailable` still queues nothing.

Optional, same PR: in `pipeline.geocode_pending`, skip the relink and outlier pass when nothing was resolved
(`touched` empty and `out["resolved"] == 0`), instead of `apply_outlier_rule(conn, None)` over every source (`:359-364`).

**Fix B — honest outcomes from `parse_answer`** (`services/places/locate.py`, `services/places/pipeline.py`, `services/places/store.py`)

```python
# locate.py
REASON_NULL, REASON_MISSING, REASON_MALFORMED = "unknown_to_model", "missing_in_answer", "malformed_answer"

def parse_answer(raw, items) -> dict[str, Proposal | str]:          # label -> Proposal or a reason
    data = _json_object(raw)                                          # Fix C
    keyed = {name_norm(str(k)): v for k, v in data.items()}
    out = {}
    for it in items:
        hit = next((keyed[k] for k in (name_norm(it.label), name_norm(it.name)) if k in keyed), _MISSING)
        if hit is _MISSING:
            out[it.label] = REASON_MISSING; continue
        if hit is None:
            out[it.label] = REASON_NULL; continue
        try:
            lat, lng, raw_country = float(hit[0]), float(hit[1]), str(hit[2])
        except (TypeError, ValueError, IndexError, KeyError):
            out[it.label] = REASON_MALFORMED; continue
        country = guards.canonical_country(raw_country)
        if country is None:
            out[it.label] = f"not_aa_country:{raw_country.strip()[:40]}"; continue
        out[it.label] = Proposal(lat, lng, country, _native(hit, country))
    return out
```

(`name_norm(it.name)` is tried only when no other item in the batch has that plain name. `batches()` already
keeps labels distinct.) In `locate_many`, a string becomes `Outcome(None, reason=…)`. In
`pipeline.geocode_pending` (`:332-335`):

```python
if o.point is None:
    if o.reason in (locate.REASON_MISSING,) or o.reason == "batch_failed":
        await store.defer_name(conn, it.key, error=o.error or o.reason, hours=6)   # no try counted
    elif (o.reason or "").startswith("not_aa_country"):
        await store.mark_name(conn, it.key, error=o.reason, max_tries=1)          # terminal, visible reason
    else:
        st = await store.mark_name(conn, it.key, error=o.error or o.reason)
```

`store.defer_name` = `UPDATE geo.place_name SET last_error = $4, next_retry_at = now() + make_interval(hours => $5),
updated_at = now() WHERE (name_norm, country_norm, locality_norm) = ($1, $2, $3)`. A name that keeps going missing
retries every 6 h; add `missing_in_answer` to the S1 sample to see whether it happens. Tests: wrapped answer,
re-spelled key, label with locality answered by plain name, `"Pakistan"` before and after F3, `"Russia"` →
`not_aa_country:Russia` with tries = 1 and status `unknown`.

**Fix C — tolerant JSON** (`locate.py:136-140`, `:193-201`)

```python
def _json_object(raw: str) -> dict:
    s = (raw or "").strip()
    i = s.find("{")
    if i < 0:
        raise ValueError("no JSON object in the locate answer")
    obj, _ = json.JSONDecoder().raw_decode(s[i:])         # ignores trailing prose / fences
    if isinstance(obj, dict) and len(obj) == 1:            # {"places": {...}} wrapper
        inner = next(iter(obj.values()))
        if isinstance(inner, dict):
            obj = inner
    if not isinstance(obj, dict):
        raise ValueError("locate answer is not a JSON object")
    return obj
```

In `locate_many`, on a parse failure of a batch with more than one name, call `generate` once for each half (at most
2 extra calls, ≈ $0.03). If a half still fails, its names get `Outcome(None, error=…, reason="batch_failed")`, which
Fix B defers without a try. Also log `stop_reason` in the failure warning; `make_generate` already records it in
`shared.llm_call_log`.

**Fix D — country normalisation** (`services/places/guards.py`, `pipeline.py`, `services/acp_shared/place_cards.py`)

```python
# guards.py
_SPLIT = re.compile(r"\s*(?:,|/|;|&|\band\b)\s*", re.I)

def canonical_countries(text: Optional[str]) -> list[str]:
    """'Nepal and China' -> ['Nepal', 'China']; 'Russia' -> []; order kept, AA countries only."""
    seen = []
    for part in _SPLIT.split((text or "").strip()):
        c = canonical_country(re.sub(r"\(.*?\)", "", part).strip())
        if c and c not in seen:
            seen.append(c)
    return seen

# pipeline.py :32-33
def canonical(country: Optional[str], tour_country: Optional[str] = None) -> str:
    c = guards.canonical_country(country)
    if c:
        return c
    many = guards.canonical_countries(country)
    tc = guards.canonical_country(tour_country)
    if many:
        return tc if tc in many else many[0]
    return (country or "").strip()          # non-AA only: kept, then terminal not_aa_country (below)
# :110-112  c.country = canonical(c.country, country)
```

- `place_cards.py:736`: `country = guards.canonical_country(raw_country) or (guards.canonical_countries(raw_country) or [None])[0] or raw_country.strip() or rep.get("country") …`,
  preferring the tour's country when it is in the list, as above. This stops new dirty cards. Existing cards need
  one data step: list them with S5, normalise via an approved write, then force a re-extract of their tours.
- `pipeline.geocode_pending` before `locate_many`: an item whose country has no AA country
  (`not guards.canonical_country(c) and not guards.canonical_countries(c)`) → `mark_name(..., error=f"not_aa_country:{c}", max_tries=1)`,
  with no model call.
- Data effect: re-keyed names leave the old dirty-key rows as orphans. Fix E keeps them from being geocoded.

**Fix E — geocode only names a tour still needs** (`store.py:292-304`)

```sql
-- due_names (and the same WHERE in pending_names_due)
SELECT pn.name_norm, pn.country_norm, pn.locality_norm, pn.display_name, pn.country, pn.locality, pn.tour_name,
       pn.place_card_id::text AS place_card_id, pn.tries
  FROM geo.place_name pn
 WHERE pn.status = 'pending' AND pn.next_retry_at <= now()
   AND (EXISTS (SELECT 1 FROM geo.tour_place tp WHERE tp.destination_id IS NULL
                   AND (tp.name_norm, tp.country_norm, tp.locality_norm) = (pn.name_norm, pn.country_norm, pn.locality_norm))
     OR EXISTS (SELECT 1 FROM geo.tour_day td WHERE td.overnight_destination_id IS NULL AND td.anchor_norm IS NOT NULL
                   AND (td.anchor_norm, td.anchor_country_norm, td.anchor_locality_norm) = (pn.name_norm, pn.country_norm, pn.locality_norm))
     OR EXISTS (SELECT 1 FROM acp_shared.place_card pc WHERE pc.card_id = pn.place_card_id AND pc.destination_id IS NULL))
 ORDER BY pn.created_at, pn.name_norm LIMIT $1
```

Both sub-selects hit the existing partial indexes `tour_place_unlinked_idx` and `tour_day_unlinked_anchor_idx`.

## 5. Ops now (orchestrator, approved step)

1. Check today's credits and queued place jobs with S7.
2. Enqueue **one** `place_geocode` from the worker:
   `shared.jobs.registry.enqueue(pool, 'place_geocode', {'reason': 'aa990_geocode_resume'})`. It continues by itself
   (`:142-144`) until the 2,500 credits are spent. Without Fix A it then stops again, so repeat it after each 00:00Z
   until Fix A ships. At 1–3 credits per name, the 3,956 names take **about 2–4 UTC days** on the Free plan ($0
   Geoapify, about $2 of model calls). Raising `GEOAPIFY_DAILY_CREDIT_LIMIT` to 2,900 adds about 16 % with no
   headroom; not recommended.
3. PK/PH: after F3 deploys, reset those names (F3 report, Data step) **before** this enqueue, or they spend another try.
4. Do not reset the AA-country `unknown_to_model` rows until Fix B ships. Otherwise they are re-asked under the same
   parser and come back the same.

## 6. Read-only SQL for the orchestrator (`cis_app`, container `DATABASE_URL`)

Wrap each block: `BEGIN; SELECT set_config('app.tenant_id','00000000-0000-0000-0000-000000000001',true); … COMMIT;`
(needed only where `published_tours` / `raw_tours` are read; harmless elsewhere). `live` CTE = `store.py:16-26`:

```sql
WITH live AS (
  SELECT pt.tour_id, COALESCE(rt.source_group_id, rt.tour_id)::text AS source_id, rt.country, pt.aa_name
    FROM gold_aa_internal.published_tours pt
    JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = pt.tour_id
   WHERE pt.tenant_id = '00000000-0000-0000-0000-000000000001'::uuid
     AND pt.master_status = 'active' AND pt.deleted_at IS NULL
     AND rt.source_status = 'active' AND rt.deleted_at IS NULL)
```

**S1 — 20 `unknown_to_model` names per country (sample)**
```sql
WITH u AS (
  SELECT pn.country, pn.status, pn.display_name, pn.locality, pn.tour_name, pn.tries, pn.updated_at,
         pc.display_name AS card_name, pc.country AS card_country, pc.locality AS card_locality,
         row_number() OVER (PARTITION BY pn.country ORDER BY pn.updated_at DESC, pn.name_norm) AS rn
    FROM geo.place_name pn
    LEFT JOIN acp_shared.place_card pc ON pc.card_id = pn.place_card_id
   WHERE pn.last_error = 'unknown_to_model')
SELECT country, rn, status, display_name, locality, card_name, card_country, card_locality, left(tour_name, 60) AS tour,
       tries, updated_at
  FROM u WHERE rn <= 20 ORDER BY country, rn;
```

**S2 — shape of `unknown_to_model` per country (which case dominates)**
```sql
SELECT country, count(*) AS n,
       count(*) FILTER (WHERE status = 'unknown') AS terminal,
       count(*) FILTER (WHERE locality IS NOT NULL) AS label_with_locality,     -- case b: "X (Locality)" label
       count(*) FILTER (WHERE display_name LIKE '%(%') AS name_has_paren,
       count(*) FILTER (WHERE place_card_id IS NOT NULL) AS has_card,
       count(DISTINCT date_trunc('minute', updated_at)) AS try_minutes,          -- few minutes, many names → whole-batch misses
       max(tries) AS max_tries
  FROM geo.place_name WHERE last_error = 'unknown_to_model' GROUP BY 1 ORDER BY 2 DESC;
-- baseline: does a locality label resolve worse than a plain one?
SELECT (locality IS NOT NULL) AS with_locality, status, coalesce(left(last_error, 20), '-') AS err, count(*)
  FROM geo.place_name GROUP BY 1, 2, 3 ORDER BY 1, 2, 4 DESC;
```

**S3 — locate calls: cost, truncation, tiny answers**
```sql
SELECT model, stop_reason, count(*) AS calls, round(avg(cost_usd), 5) AS avg_usd, round(sum(cost_usd), 3) AS total_usd,
       max(tokens_out) AS max_out, count(*) FILTER (WHERE (quality_signal->>'output_len_chars')::int < 40) AS tiny_answers
  FROM shared.llm_call_log WHERE stage = 'a3_place_locate' AND created_at > now() - interval '14 days'
 GROUP BY 1, 2 ORDER BY 3 DESC;
```

**S4 — the 9 Laos parse failures and the calls around them**
```sql
SELECT display_name, locality, left(tour_name, 60) AS tour, tries, last_error, updated_at
  FROM geo.place_name WHERE last_error LIKE 'locate:%' ORDER BY updated_at;
SELECT l.created_at, l.job_id, l.model, l.tokens_in, l.tokens_out, l.stop_reason, l.fallback_used, l.account,
       (l.quality_signal->>'output_len_chars')::int AS out_chars
  FROM shared.llm_call_log l
 WHERE l.stage = 'a3_place_locate'
   AND l.created_at BETWEEN (SELECT min(updated_at) - interval '5 minutes' FROM geo.place_name WHERE last_error LIKE 'locate:%')
                        AND (SELECT max(updated_at) + interval '1 minute' FROM geo.place_name WHERE last_error LIKE 'locate:%')
 ORDER BY 1;
```
`stop_reason = max_tokens` → truncation. A tiny `out_chars` → empty or refusal answer.

**S5 — dirty-country names with their cards and source tours**
```sql
WITH live AS (...),
dirty AS (
  SELECT * FROM geo.place_name
   WHERE lower(btrim(country)) NOT IN ('bhutan','cambodia','china','india','indonesia','japan','kyrgyzstan','laos',
         'malaysia','mongolia','myanmar','nepal','south korea','sri lanka','taiwan','thailand','vietnam','tibet',
         'pakistan','philippines'))
SELECT d.country AS name_country, d.status, d.display_name, d.locality, d.tries, left(d.last_error, 40) AS err,
       pc.display_name AS card_name, pc.country AS card_country, pc.region AS card_region, pc.status AS card_status,
       tp.day_index, tp.name AS itinerary_name, l.country AS tour_country, l.source_id, l.tour_id, left(l.aa_name, 60) AS tour
  FROM dirty d
  LEFT JOIN acp_shared.place_card pc ON pc.card_id = d.place_card_id
  LEFT JOIN geo.tour_place tp ON (tp.name_norm, tp.country_norm, tp.locality_norm) = (d.name_norm, d.country_norm, d.locality_norm)
  LEFT JOIN live l ON l.source_id = tp.source_id
 ORDER BY 1, 3, l.source_id, tp.day_index;
-- every dirty card, used or not
SELECT country, count(*) AS cards, (array_agg(display_name ORDER BY display_name))[1:8] AS sample
  FROM acp_shared.place_card
 WHERE status <> 'rejected'
   AND lower(btrim(country)) NOT IN ('bhutan','cambodia','china','india','indonesia','japan','kyrgyzstan','laos',
         'malaysia','mongolia','myanmar','nepal','south korea','sri lanka','taiwan','thailand','vietnam','tibet',
         'pakistan','philippines')
 GROUP BY 1 ORDER BY 2 DESC;
```

**S6 — pending names no tour uses any more (RC6 size)**
```sql
SELECT pn.country, count(*) AS pending,
       count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM geo.tour_place tp WHERE tp.destination_id IS NULL
                                  AND (tp.name_norm, tp.country_norm, tp.locality_norm) = (pn.name_norm, pn.country_norm, pn.locality_norm))
                          AND NOT EXISTS (SELECT 1 FROM geo.tour_day td WHERE td.overnight_destination_id IS NULL AND td.anchor_norm IS NOT NULL
                                  AND (td.anchor_norm, td.anchor_country_norm, td.anchor_locality_norm) = (pn.name_norm, pn.country_norm, pn.locality_norm))
                          AND NOT EXISTS (SELECT 1 FROM acp_shared.place_card pc WHERE pc.card_id = pn.place_card_id AND pc.destination_id IS NULL)
                       ) AS orphan
  FROM geo.place_name pn WHERE pn.status = 'pending' GROUP BY 1 ORDER BY 2 DESC;
```

**S7 — who spent the credits, and what is queued now**
```sql
SELECT date_trunc('hour', g.called_at) AS utc_hour, g.provider, g.endpoint, j.kind,
       sum(g.requests) AS requests, sum(coalesce(g.credits, g.requests)) AS credits
  FROM geo.geocode_call g LEFT JOIN shared.job j ON j.id = g.job_id
 WHERE g.called_at > now() - interval '3 days' GROUP BY 1, 2, 3, 4 ORDER BY 1;
SELECT kind, status, count(*), min(run_after) AS next_run
  FROM shared.job WHERE kind IN ('place_extract','place_geocode','tour_graph_build','place_shape','place_dedupe')
   AND status IN ('queued','running') GROUP BY 1, 2;
```

## Not done here

- No DB read: RC3's split between cases (b) and (c), RC4's cause (truncation or empty answer) and RC6's size are
  inferred from the code and the snapshot. S2/S3/S4/S6 settle them.
- No code changed, so the implementation note for AA-990 is not appended (the CIS main checkout must not be edited).
  The fixes above go into the AA-990 / AA-905 branch notes when they are built.
