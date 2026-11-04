"""AA-1043 trial, step 1 — READ-ONLY sample of ~50 places whose stored point Geoapify confirmed.

Runs inside the CIS api container (orchestrator): tools/ecs/ecsx.sh .tmp-session/S267/trials/geo_sample.py
Optional env: SAMPLE_N=50  SEED=aa1043  MAX_COUNTRIES=8  INCLUDE_LINES=0

Reads (cis_app, SELECT only, inside a READ ONLY transaction):
  shared.destinations          id, name, country, country_iso2, lat, lng, located_by, geocoder_provider,
                               geo_precision, geo_status, confidence, geocoder_meta (provider/outcome/query/
                               result_type/confidence/name/tried[].query), duplicate_of
  acp_shared.place_card        display_name, locality, region  (by destination_id, first card)
  geo.place_name               display_name, locality           (by destination_id, first row; tour_name NOT read)
Column names checked against docs/architecture/db-schema-reference.md (Verified 2026-11-04 00:55 UTC).

Output: one JSON document between the marker lines
  ===GEO_SAMPLE_JSON_BEGIN===  /  ===GEO_SAMPLE_JSON_END===
Save it as .tmp-session/S267/trials/geo_sample.json (geo_trial.py also accepts the raw ecsx output file).
No PII: places only (no tour names, no tenant, no person). Writes nothing anywhere.
"""
import asyncio
import hashlib
import json
import os
import re
import sys
import unicodedata

import asyncpg

SAMPLE_N = int(os.environ.get("SAMPLE_N", "50"))
SEED = os.environ.get("SEED", "aa1043")
MAX_COUNTRIES = int(os.environ.get("MAX_COUNTRIES", "8"))
INCLUDE_LINES = os.environ.get("INCLUDE_LINES", "0") == "1"   # rivers / roads: a point compare means little

if not (1 <= SAMPLE_N <= 60):
    sys.exit("SAMPLE_N must be 1..60 (the trial caps Location requests at 120)")

SQL = """
SELECT d.id::text                         AS id,
       d.name, d.country, d.country_iso2::text AS iso2,
       d.lat, d.lng, d.located_by, d.geocoder_provider, d.geo_precision, d.geo_status,
       d.confidence,
       d.geocoder_meta->>'outcome'        AS g_outcome,
       d.geocoder_meta->>'query'          AS g_query,
       d.geocoder_meta->>'name'           AS g_name,
       d.geocoder_meta->>'result_type'    AS g_result_type,
       d.geocoder_meta->>'confidence'     AS g_confidence,
       d.geocoder_meta->>'match_type'     AS g_match_type,
       COALESCE((SELECT array_agg(t->>'query')
                   FROM jsonb_array_elements(
                        CASE WHEN jsonb_typeof(d.geocoder_meta->'tried') = 'array'
                             THEN d.geocoder_meta->'tried' ELSE '[]'::jsonb END) t), '{}') AS g_tried,
       pc.display_name AS card_name, pc.locality AS card_locality, pc.region AS card_region,
       pn.display_name AS pn_name, pn.locality AS pn_locality
  FROM shared.destinations d
  LEFT JOIN LATERAL (SELECT c.display_name, c.locality, c.region
                       FROM acp_shared.place_card c
                      WHERE c.destination_id = d.id AND c.status <> 'rejected'
                      ORDER BY c.updated_at DESC LIMIT 1) pc ON true
  LEFT JOIN LATERAL (SELECT p.display_name, p.locality
                       FROM geo.place_name p
                      WHERE p.destination_id = d.id
                      ORDER BY p.updated_at DESC LIMIT 1) pn ON true
 WHERE d.duplicate_of IS NULL
   AND d.geo_status = 'ok'
   AND d.geocoder_provider = 'geoapify'
   AND d.geocoder_meta->>'outcome' = 'accepted'
   AND d.country_iso2 IS NOT NULL
   AND ($1::bool OR d.geo_precision IS DISTINCT FROM 'line')
"""

# Word lists kept to unambiguous words ("Sa Pa", "Red Dao village" must not count as a temple / an island).
ISLAND_RE = re.compile(r"\b(island|islands|isle|islet|koh|ko|pulau|nusa|gili|atoll|cay|đảo|archipelago)\b", re.I)
TEMPLE_RE = re.compile(r"\b(temple|wat|pagoda|pura|shrine|monastery|gompa|dzong|stupa|chedi|chùa|đền|"
                       r"candi|vihara|lhakhang|mosque|cathedral|basilica|jinja)\b", re.I)


def scripts(text):
    """Non-Latin scripts used in text (THAI, CJK, HANGUL, KHMER, LAO, MYANMAR, DEVANAGARI, ...)."""
    out = set()
    for ch in text or "":
        if ch.isalpha():
            nm = unicodedata.name(ch, "")
            if nm and not nm.startswith("LATIN"):
                out.add(nm.split(" ")[0])
    return out


def has_diacritic(text):
    return any(ch.isalpha() and ord(ch) > 127 and unicodedata.name(ch, "").startswith("LATIN") for ch in text or "")


def rank(key):
    return hashlib.sha256(f"{SEED}|{key}".encode()).hexdigest()


def first_local_name(r):
    """A local-script name we already hold for the place (meta query / tried queries / names), if any."""
    for cand in [r["g_query"], *(r["g_tried"] or []), r["name"], r["card_name"], r["pn_name"]]:
        if cand and scripts(cand):
            return cand.strip()
    return None


async def main():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        async with conn.transaction(readonly=True):
            await conn.execute("SET LOCAL statement_timeout = '60s'")
            rows = [dict(r) for r in await conn.fetch(SQL, INCLUDE_LINES)]
    finally:
        await conn.close()

    pool = []
    for r in rows:
        local = first_local_name(r)
        text_all = " ".join(x for x in [r["name"], r["card_name"], r["pn_name"], r["g_name"]] if x)
        tags = []
        if ISLAND_RE.search(text_all):
            tags.append("island")
        if TEMPLE_RE.search(text_all):
            tags.append("temple")
        if local:
            tags.append("non_latin")
        if has_diacritic(text_all):
            tags.append("diacritic")
        if r["geo_precision"] == "area":
            tags.append("area")
        r["local_name"] = local
        r["local_scripts"] = sorted(scripts(local)) if local else []
        r["tags"] = tags
        r["_rank"] = rank(r["id"])
        pool.append(r)

    by_iso = {}
    for r in pool:
        by_iso.setdefault(r["iso2"].strip().upper(), []).append(r)
    # Countries: the MAX_COUNTRIES with most candidates, plus any country holding non-Latin candidates (TW / KR / CN /
    # JP ...) so the hard script cases are present.
    order = sorted(by_iso, key=lambda k: -len(by_iso[k]))
    countries = order[:MAX_COUNTRIES]
    for iso in order[MAX_COUNTRIES:]:
        if any("non_latin" in r["tags"] for r in by_iso[iso]) and len(countries) < MAX_COUNTRIES + 3:
            countries.append(iso)
    for iso in countries:
        by_iso[iso].sort(key=lambda r: r["_rank"])

    picked, seen = [], set()

    def take(pred, quota):
        n, progress = 0, True
        while n < quota and progress:              # round-robin over countries for spread
            progress = False
            for iso in countries:
                if n >= quota or len(picked) >= SAMPLE_N:
                    return
                for r in by_iso[iso]:
                    if r["id"] not in seen and pred(r):
                        picked.append(r); seen.add(r["id"]); n += 1; progress = True
                        break

    hard = max(1, SAMPLE_N // 6)                   # ~8 each at N=50
    take(lambda r: "non_latin" in r["tags"], hard)
    take(lambda r: "island" in r["tags"], hard)
    take(lambda r: "temple" in r["tags"], hard)
    take(lambda r: "diacritic" in r["tags"], max(1, hard // 2))
    take(lambda r: "area" in r["tags"], max(1, hard // 2))
    take(lambda r: True, SAMPLE_N - len(picked))  # the rest: plain points, spread by country

    keep = ("id", "name", "local_name", "local_scripts", "card_name", "card_locality", "card_region", "pn_name",
            "pn_locality", "country", "iso2", "lat", "lng", "located_by", "geocoder_provider", "geo_precision",
            "confidence", "g_query", "g_name", "g_result_type", "g_confidence", "g_match_type", "tags")
    sample = [{k: r.get(k) for k in keep} for r in picked]
    for s in sample:
        s["iso2"] = (s["iso2"] or "").strip().upper()
    out = {
        "issue": "AA-1043", "seed": SEED, "sample_n": len(sample), "candidates": len(pool),
        "countries": {iso: sum(1 for s in sample if s["iso2"] == iso) for iso in countries},
        "tag_counts": {t: sum(1 for s in sample if t in s["tags"])
                       for t in ("non_latin", "island", "temple", "diacritic", "area")},
        "filter": "shared.destinations: duplicate_of IS NULL, geo_status ok, geocoder_provider geoapify, "
                  "geocoder_meta.outcome accepted, country_iso2 set" + ("" if INCLUDE_LINES else ", not line"),
        "places": sample,
    }
    print("===GEO_SAMPLE_JSON_BEGIN===")
    print(json.dumps(out, ensure_ascii=False, default=str))
    print("===GEO_SAMPLE_JSON_END===")
    print(f"geo_sample: {len(sample)} places from {len(pool)} candidates; countries={out['countries']}; "
          f"tags={out['tag_counts']}", file=sys.stderr)


asyncio.run(main())
