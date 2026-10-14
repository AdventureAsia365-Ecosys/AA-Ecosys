"""AA-774 kind probe — READ-ONLY (SELECT only, $0). Prepared by lane A-T9 in S235; NOT run by the lane.

Run by the orchestrator inside the api or worker container via the S3-mediated ECS exec pattern
(python3 + asyncpg + boto3, ssl="require"). Prints JSON to stdout; writes nothing (no S3 put, no DB write).

Answers AA-774 Done-when (a): the kind distribution of stored place-card facts (status <> 'rejected'),
facts without a kind / with an unknown kind / that are not objects, and how many cards would drop below
RICH_CARD_FACTS (3) WRITER facts once visiting/practical are filtered (the sibling gate must stay on the
UNFILTERED count — synthesis correction — so this number is the size of the thin-seed effect, not of a
sibling regression). Writer kinds = what_it_is, history, setting, naming; a missing kind counts as
what_it_is (place_cards._clean_facts default).
"""
import asyncio
import json
from urllib.parse import urlparse

import sys
import unicodedata

import asyncpg
import boto3

sys.path.insert(0, "/app")

WRITER_KINDS = {"what_it_is", "history", "setting", "naming"}
CHECKPOINT_REQUESTS = [  # .tmp-session/s234/checkpoint_r4.json
    "1dfbf5e6-bf67-45a3-84c8-7fc37d62868a",  # atlas-hearth blog (Mongolia route)
    "3bf7a5f7-7ddc-45f2-af25-ca1a81b49d21",  # terra-family blog (Mongolia route)
    "f5e6aa33-4113-496b-9567-3591e9cbdef4",  # atlas-hearth linkedin Punakha Dzong
    "ff45fd8a-a9e9-4881-ac8b-25aa25cee014",  # terra-family linkedin Paro
    "d940d26f-a991-4a56-a7a8-aeae63f5c7b4",  # trail-pulse linkedin Kuang Si Falls
    "3524ad2d-76f8-43ae-a84b-a4ecec7978a8",  # wildkind-travel linkedin Punakha Dzong
]

R4_BULLET_PREFIXES = [
"A bear rescue centre operated by Free the Bears is located at the entrance to th",
"A fire in 1998 severely damaged much of the complex; it was subsequently restore",
"Access to the eastern and western Taiga camps where Tsaatan live requires a perm",
"According to Bhutanese tradition, Guru Rinpoche (Padmasambhava) flew to this sit",
"It holds an estimated 70 percent of Mongolia's fresh water and about 0.4 percent",
"It is the centerpiece of the Uran Togoo-Tulga Uul Natural Monument, a protected ",
"It lies at the ecological transition zone between Central Asian steppe grassland",
"It remains the winter residence of the Je Khenpo (Chief Abbot of Bhutan) and the",
"It served as the capital and seat of government of Bhutan for 318 years (1637–19",
"It serves as the main hub and gateway town for travellers heading to Khövsgöl La",
"It was built in 1637–1638 by Zhabdrung Ngawang Namgyal, the unifier of Bhutan, w",
"Kuang Si Falls is a multi-tiered limestone waterfall system located approximatel",
"Lake Khövsgöl is a large freshwater lake in northern Mongolia, near the Russian ",
"Mörön developed as an administrative and trade centre during the Soviet era and ",
"Mörön has a small domestic airport with scheduled flights connecting it to Ulaan",
"Mörön is the capital city of Khövsgöl Province, the northernmost aimag (province",
"Paro Taktsang is a sacred Buddhist monastery complex built into a sheer granite ",
"Paro Taktsang is one of Bhutan's most revered pilgrimage sites; Bhutanese Buddhi",
"Punakha Dzong is a large Buddhist monastery-fortress (dzong) located at the conf",
"Punakha Dzong served as the capital and seat of government of Bhutan until 1955,",
"Reindeer in Tsaatan culture are used for riding and as pack animals as well as f",
"Summers are short and cool; sudden storms can arise quickly on the lake, making ",
"The Delgermörön River flows near the town, and the surrounding landscape is char",
"The Tsaatan (Dukha) are a small semi-nomadic indigenous community, numbering onl",
"The Tsaatan (Dukha) people, a small community of reindeer herders, live in the r",
"The Tsaatan are ethnically and linguistically related to Tuvan peoples of southe",
"The Tsaatan community has faced pressures including population decline, restrict",
"The building spans a long peninsula between the two rivers and is connected to t",
"The city sits in a broad valley at an elevation of approximately 1,283 metres ab",
"The complex comprises four main temples, several sacred caves, and a series of s",
"The crater is roughly 600 metres wide and 50–60 metres deep, and its caldera flo",
"The dzong has been damaged and rebuilt multiple times due to fire and floods, mo",
"The dzong houses the sacred relic of Zhabdrung Ngawang Namgyal and important rel",
"The falls cascade over a series of travertine limestone terraces, creating a seq",
"The hike to the monastery from the base-area car park follows a forested trail a",
"The interior courtyards contain a utse (central tower) and several temples adorn",
"The lake freezes solidly in winter, typically from January through April, and wa",
"The lake sits at an elevation of roughly 1,645 metres (5,397 feet) above sea lev",
"The main temple structures were built around the sacred cave in 1692 under the d",
"The main upper fall drops roughly 50 metres into a large pool at the base.",
"The region experiences extremely cold winters and the taiga terrain is marshy in",
"The road from Luang Prabang to the falls is paved and passes through rural villa",
"The site is set within forested hills and is part of a protected area; the surro",
"The surrounding area is protected as Khövsgöl Nuur National Park, established in",
"The surrounding forest is composed largely of blue pine and rhododendron, and pr",
"The surrounding landscape combines open green steppe grasslands with patches of ",
"The town has a typical Mongolian provincial layout with a central square, a mark",
"The vivid turquoise colour of the water is caused by high calcium carbonate cont",
"The volcano last erupted approximately 20,000–24,000 years ago, making it geolog",
"Their settlements are not permanent villages but seasonal camps of teepee-style ",
"Their territory lies deep in the taiga, typically reached from the town of Tsaga",
"Trails lead up alongside the falls to viewpoints at the top, passing through for",
"Uran Togoo is considered the largest of several dormant volcanoes in the surroun",
"Visitors are required to wear traditional Bhutanese dress (gho for men, kira for",
"Visitors can swim in the lower tiered pools; the upper reaches and the main fall",
"Visitors can trek across the volcanic terrain, including walking down into the w",
"Visitors must leave cameras and bags at a checkpoint before entering the inner t",
"Visitors typically arrive via the nearby town of Khatgal at the lake's southern ",
"Visitors typically see the teepee camps, interact with families, observe reindee",
"Water levels and flow are strongest during and just after the rainy season (roug",
"Winters are severe, with temperatures regularly dropping well below −30 °C, refl"
]

FACTS = "CASE WHEN jsonb_typeof(pc.facts) = 'array' THEN pc.facts ELSE '[]'::jsonb END"

Q_KINDS = f"""
SELECT CASE WHEN jsonb_typeof(f) <> 'object' THEN '<not_object>'
            WHEN f->>'kind' IS NULL THEN '<missing>'
            ELSE f->>'kind' END AS kind,
       count(*) AS facts, count(DISTINCT pc.card_id) AS cards
FROM acp_shared.place_card pc
CROSS JOIN LATERAL jsonb_array_elements({FACTS}) AS f
WHERE pc.status <> 'rejected'
GROUP BY 1 ORDER BY 2 DESC
"""

Q_CARDS = f"""
WITH per_card AS (
  SELECT pc.card_id, pc.display_name, pc.country, pc.status,
         count(f) AS total_facts,
         count(f) FILTER (WHERE coalesce(f->>'kind', 'what_it_is')
                          IN ('what_it_is', 'history', 'setting', 'naming')) AS writer_facts,
         count(f) FILTER (WHERE f->>'kind' IN ('visiting', 'practical')) AS dropped_facts
  FROM acp_shared.place_card pc
  LEFT JOIN LATERAL jsonb_array_elements({FACTS}) AS f ON true
  WHERE pc.status <> 'rejected'
  GROUP BY pc.card_id, pc.display_name, pc.country, pc.status
)
SELECT count(*) AS cards,
       count(*) FILTER (WHERE dropped_facts > 0) AS cards_losing_facts,
       count(*) FILTER (WHERE total_facts >= 3 AND writer_facts < 3) AS cards_falling_below_rich,
       count(*) FILTER (WHERE writer_facts = 0) AS cards_left_with_no_writer_fact,
       sum(total_facts) AS total_facts, sum(writer_facts) AS writer_facts, sum(dropped_facts) AS dropped_facts
FROM per_card
"""

Q_BELOW_RICH = f"""
SELECT pc.display_name, pc.country, pc.status,
       count(f) AS total_facts,
       count(f) FILTER (WHERE coalesce(f->>'kind', 'what_it_is')
                        IN ('what_it_is', 'history', 'setting', 'naming')) AS writer_facts
FROM acp_shared.place_card pc
LEFT JOIN LATERAL jsonb_array_elements({FACTS}) AS f ON true
WHERE pc.status <> 'rejected'
GROUP BY pc.card_id, pc.display_name, pc.country, pc.status
HAVING count(f) >= 3
   AND count(f) FILTER (WHERE coalesce(f->>'kind', 'what_it_is')
                        IN ('what_it_is', 'history', 'setting', 'naming')) < 3
ORDER BY pc.country, pc.display_name
"""

# Sample dropped texts so a human can confirm they are visiting/practical lines (permits, dress codes, access).
Q_DROPPED_SAMPLE = f"""
SELECT pc.display_name, pc.country, f->>'kind' AS kind, left(f->>'text', 200) AS text
FROM acp_shared.place_card pc
CROSS JOIN LATERAL jsonb_array_elements({FACTS}) AS f
WHERE pc.status <> 'rejected' AND f->>'kind' IN ('visiting', 'practical')
ORDER BY pc.country, pc.display_name
LIMIT 60
"""


Q_MISSES = """
SELECT prompt_sha, reason, count(*) AS n, count(*) FILTER (WHERE retry_after > now()) AS still_blocking
FROM acp_shared.place_card_miss GROUP BY 1, 2 ORDER BY 1, 2
"""

Q_ALL_FACTS = f"""
SELECT f->>'text' AS text, f->>'kind' AS kind
FROM acp_shared.place_card pc CROSS JOIN LATERAL jsonb_array_elements({FACTS}) AS f
WHERE pc.status <> 'rejected' AND jsonb_typeof(f) = 'object'
"""

Q_REQ = """
SELECT request_id::text, tenant_id::text, atom_id, trip_id::text, channel, route_segment_ids
FROM acp_shared.angle_gate_request WHERE request_id = $1::uuid
"""


def _fold(s):
    t = unicodedata.normalize("NFKD", s or "")
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).lower().split())


def _filtered(card):
    if not card:
        return card
    facts = card.get("facts") or []
    if isinstance(facts, str):
        facts = json.loads(facts or "[]")
    return {**card, "facts": [f for f in facts if isinstance(f, dict) and f.get("text")
                              and (f.get("kind") or "what_it_is") in WRITER_KINDS]}


def _block_report(before, after):
    from services.acp_shared.atom_seed import THIN_FACTS, moment_fact_count

    def bullets(block, head):
        out, on = [], False
        for line in block.splitlines():
            if line.startswith(head):
                on = True
                continue
            if on and line.startswith("- "):
                out.append(line[2:])
            else:
                on = False
        return out
    nb, na = moment_fact_count(before), moment_fact_count(after)
    gone = [b[:140] for b in bullets(before, "Place background") if b not in bullets(after, "Place background")]
    return {"label": before.split("\n", 1)[0][:80], "facts_before": nb, "facts_after": na,
            "thin_before": nb < THIN_FACTS, "thin_after": na < THIN_FACTS,
            "siblings_before": len(bullets(before, "Other trips")), "siblings_after": len(bullets(after, "Other trips")),
            "removed": gone}


async def _request_report(pool, request_id):
    from services.acp_angle_gate.route_digest import route_moments
    from services.acp_content_writing.service import _fetch_route_segments
    from services.acp_shared import atom_seed as s

    # "before" = pre-AA-774 rendering even when this runs on AA-774 code (then the module filters by
    # itself): widen its kind set to every kind; the "after" side passes pre-filtered cards anyway.
    if hasattr(s, "WRITER_FACT_KINDS"):
        s.WRITER_FACT_KINDS = frozenset(s.WRITER_FACT_KINDS) | {"visiting", "practical"}

    async with pool.acquire() as conn:
        req = await conn.fetchrow(Q_REQ, request_id)
    if req is None:
        return {"request_id": request_id, "error": "not found"}
    req = dict(req)
    seg_ids = req["route_segment_ids"]
    if isinstance(seg_ids, str):
        seg_ids = json.loads(seg_ids)
    out = {"request_id": request_id, "channel": req["channel"], "route": bool(seg_ids)}
    async with pool.acquire() as conn:
        if seg_ids:
            atoms = []
            await _fetch_route_segments(req["tenant_id"], req["trip_id"], seg_ids, pool, atoms_out=atoms)
            parts = []
            for atom_id, label in atoms:
                p = await s.atom_seed_parts(conn, atom_id, req["tenant_id"], siblings=False)
                parts.append(p if p is not None else {"atom_id": atom_id, "text": label or "", "card": None,
                                                      "label_only": True})
            parts, _ = s.canonicalize_route_cards(parts)
            pairs = []
            for group in s.group_route_moments(parts):
                if group[0].get("label_only"):
                    before = after = group[0]["text"]
                else:
                    before = s.compose_route_moment(group)
                    after = s.compose_route_moment([{**p, "card": _filtered(p.get("card"))} for p in group])
                pairs.append((group[0]["atom_id"], before, after))
            out["moments"] = [dict(_block_report(b, a), atom_id=i) for i, b, a in pairs]
            for tag, idx in (("digest_before", 1), ("digest_after", 2)):
                ms = route_moments([(p[0], p[idx]) for p in pairs])
                out[tag] = {"anchors": [m["label"][:60] for m in ms if not m["thin"]],
                            "thin": [m["label"][:60] for m in ms if m["thin"]]}
        else:
            p = await s.atom_seed_parts(conn, req["atom_id"], req["tenant_id"])
            if p is None:
                return dict(out, error="atom not live")
            args = (p["text"], p["evidence"], p["hook"], p["season"], p["siblings"])
            kw = dict(place=p["place"], country=p["country"], day=p["day"])
            before = s.compose_seed(*args, card=p["card"], **kw)
            after = s.compose_seed(*args, card=_filtered(p["card"]), **kw)
            out["moments"] = [dict(_block_report(before, after), atom_id=req["atom_id"])]
    out["thin_changed"] = sum(m["thin_before"] != m["thin_after"] for m in out["moments"])
    out["facts_removed"] = sum(len(m["removed"]) for m in out["moments"])
    return out


async def main():
    sm = boto3.client("secretsmanager", region_name="us-west-1")
    p = urlparse(sm.get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"].strip())
    ro = {"default_transaction_read_only": "on"}
    cargs = dict(host=p.hostname, port=p.port or 5432, database=p.path.lstrip("/"),
                 user=p.username, password=p.password, ssl="require", server_settings=ro)
    conn = await asyncpg.connect(**cargs)
    try:
        async with conn.transaction(readonly=True):
            out = {name: [dict(r) for r in await conn.fetch(q)]
                   for name, q in (("kinds", Q_KINDS), ("cards", Q_CARDS), ("below_rich", Q_BELOW_RICH),
                                   ("dropped_sample", Q_DROPPED_SAMPLE), ("misses", Q_MISSES))}
            kind_of = {}
            for r in await conn.fetch(Q_ALL_FACTS):
                kind_of.setdefault(_fold(r["text"])[:72], r["kind"])
    finally:
        await conn.close()
    out["r4_bullet_kinds"] = {b: kind_of.get(_fold(b)[:72]) for b in R4_BULLET_PREFIXES}
    pool = await asyncpg.create_pool(min_size=1, max_size=2, **cargs)
    try:
        out["requests"] = []
        for rid in CHECKPOINT_REQUESTS:
            try:
                out["requests"].append(await _request_report(pool, rid))
            except Exception as e:  # noqa: BLE001 — report and go on
                out["requests"].append({"request_id": rid, "error": str(e)[:300]})
    finally:
        await pool.close()
    out["summary"] = {"requests_with_thin_change": sum(1 for r in out["requests"] if r.get("thin_changed")),
                      "facts_removed_per_request": {r["request_id"][:8]: r.get("facts_removed")
                                                    for r in out["requests"]}}
    print(json.dumps(out, indent=1, default=str, ensure_ascii=False))


asyncio.run(main())
