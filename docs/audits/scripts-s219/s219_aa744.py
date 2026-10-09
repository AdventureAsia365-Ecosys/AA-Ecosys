"""AA-744: deterministic backfill — platform atoms with brand forbidden words + active Masters with
seo_meta outside 140-155. MODE=dry (default) -> before/after diff + snapshot JSON to S3, no writes.
MODE=apply -> same computation, writes in ONE transaction, verifies counts match the dry run.
atom_id is kept (FKs from atom_embedding / atom_matches / atom_segment_member)."""
import asyncio, json, os, sys
sys.path.insert(0, "/app")
import boto3, asyncpg
from urllib.parse import urlparse
from collections import Counter
from services.acp_produce.tenant_pipeline import _strip_atom_action, _MASTER_TENANT_ID
from services.acp_shared.atom_extraction import derive_atom_text
from services.content_generation.forbidden_words import all_forbidden, has_word
from services.content_generation.seo_meta_utils import fit_seo_meta_final, SEO_META_MIN, SEO_META_MAX

B = "aa-cis-bronze-005097885195"
MODE = os.environ.get("MODE", "dry")
s3 = boto3.client("s3", region_name="us-west-1")


def hits(text, words):
    return [w for w in words if has_word(text or "", w)]


async def main():
    dsn = boto3.client("secretsmanager", region_name="us-west-1").get_secret_value(SecretId="aa-cis/dev/rds")["SecretString"]
    u = urlparse(dsn)
    c = await asyncpg.connect(host=u.hostname, port=u.port or 5432, user=u.username, password=u.password, database=u.path.lstrip("/"), ssl="require")
    raw = await c.fetchval("SELECT forbidden_words FROM shared.tenant_brand_rules WHERE tenant_id = $1::uuid "
                           "AND is_active ORDER BY (brand_name = 'default') DESC, version DESC LIMIT 1", _MASTER_TENANT_ID)
    brand = json.loads(raw) if isinstance(raw, str) else (raw or [])
    words = all_forbidden(brand)
    print("forbidden words", len(words))

    # ---- atoms
    atoms = await c.fetch("""SELECT atom_id, tour_id::text, place, action, text FROM acp_contract.v_active_tour_atoms
                             WHERE owner_scope = 'platform' AND NOT coalesce(is_empty_marker, false)""")
    a_before = Counter(); a_after = Counter(); a_changes = []; a_left = []
    for a in atoms:
        h = hits(a["text"], words) + [w for w in hits(a["action"], words) if w not in hits(a["text"], words)]
        if not h:
            continue
        a_before.update(h)
        new_action = _strip_atom_action(a["action"] or "", words)
        new_text = derive_atom_text(a["place"] or "", new_action) if a["action"] else a["text"]
        rest = hits(new_text, words)
        a_after.update(rest)
        if rest:
            a_left.append({"atom_id": a["atom_id"], "text": a["text"], "new_text": new_text, "left": rest, "place": a["place"]})
        if new_text != a["text"] or new_action != (a["action"] or ""):
            a_changes.append({"atom_id": a["atom_id"], "tour_id": a["tour_id"], "old_text": a["text"], "old_action": a["action"],
                              "new_text": new_text, "new_action": new_action, "words": h})
    print(f"\nATOMS active platform {len(atoms)} | with forbidden {sum(1 for _ in a_changes) + len([x for x in a_left if x['text']==x['new_text']])} "
          f"| words {dict(a_before)}")
    print(f"  would change {len(a_changes)} | still forbidden after {len(a_left)} {dict(a_after)}")
    for x in a_changes[:12]:
        print(f"   - {x['old_text'][:110]!r}\n     → {x['new_text'][:110]!r}")
    for x in a_left[:15]:
        print(f"   LEFT {x['left']} place={x['place']!r} | {x['new_text'][:120]!r}")

    # ---- masters
    ms = await c.fetch("""SELECT p.tour_id::text, p.generated_content_id::text gc, p.seo_meta, g.seo_meta gseo, rt.duration, rt.country, rt.src_name
                          FROM gold_aa_internal.published_tours p JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = p.tour_id
                          LEFT JOIN silver_aa_internal.generated_content g ON g.id = p.generated_content_id
                          WHERE p.master_status = 'active' AND (length(p.seo_meta) < $1 OR length(p.seo_meta) > $2)""", SEO_META_MIN, SEO_META_MAX)
    m_changes = []; m_left = []
    for m in ms:
        new = fit_seo_meta_final(m["seo_meta"], {"duration": m["duration"], "country": m["country"]}, brand)
        ok = SEO_META_MIN <= len(new) <= SEO_META_MAX
        (m_changes if ok and new != m["seo_meta"] else m_left).append(
            {"tour_id": m["tour_id"], "gc": m["gc"], "name": m["src_name"], "country": m["country"], "old": m["seo_meta"],
             "gc_old": m["gseo"], "new": new})
    print(f"\nMASTERS seo_meta out of band {len(ms)} | fixable {len(m_changes)} | left {len(m_left)} | by country {dict(Counter(m['country'] for m in ms))}")
    for x in m_changes[:8]:
        print(f"   - [{len(x['old'])}] {x['old']!r}\n     [{len(x['new'])}] {x['new']!r}")
    for x in m_left:
        print(f"   LEFT [{len(x['old'])}] {x['country']} {x['name'][:50]} | {x['old']!r}")

    snap = {"atoms": a_changes, "atoms_left": a_left, "masters": m_changes, "masters_left": m_left}
    s3.put_object(Bucket=B, Key=f"scripts/s219_aa744_{MODE}.json", Body=json.dumps(snap, ensure_ascii=False, default=str).encode())
    print(f"\nsnapshot s3://{B}/scripts/s219_aa744_{MODE}.json")

    if MODE == "apply":
        exp = json.loads(s3.get_object(Bucket=B, Key="scripts/s219_aa744_dry.json")["Body"].read())
        assert len(exp["atoms"]) == len(a_changes) and len(exp["masters"]) == len(m_changes), "counts differ from dry run"
        async with c.transaction():
            n1 = 0
            for x in a_changes:
                r = await c.execute("UPDATE acp_contract.tour_atoms SET text=$2, action=$3, updated_at=now() WHERE atom_id=$1 AND text=$4",
                                    x["atom_id"], x["new_text"], x["new_action"] or None, x["old_text"])
                n1 += int(r.split()[-1])
            n2 = n3 = 0
            for x in m_changes:
                r = await c.execute("UPDATE gold_aa_internal.published_tours SET seo_meta=$2 WHERE tour_id=$1::uuid AND master_status='active' AND seo_meta=$3",
                                    x["tour_id"], x["new"], x["old"])
                n2 += int(r.split()[-1])
                if x["gc"] and x["gc_old"] == x["old"]:
                    r = await c.execute("UPDATE silver_aa_internal.generated_content SET seo_meta=$2 WHERE id=$1::uuid AND seo_meta=$3", x["gc"], x["new"], x["old"])
                    n3 += int(r.split()[-1])
            print("APPLIED atoms", n1, "masters", n2, "gc", n3)
            assert n1 == len(a_changes) and n2 == len(m_changes), "row count mismatch — rolling back"

    if MODE == "apply_atoms":
        # Nghiệp approved the atom part only (S219). Apply the dry-run rows whose text is still the
        # same as at dry-run time (A3 may re-atomize some tours meanwhile); report the rest.
        exp = json.loads(s3.get_object(Bucket=B, Key="scripts/s219_aa744_dry.json")["Body"].read())
        now_by_id = {x["atom_id"]: x for x in a_changes}
        todo = [x for x in exp["atoms"]
                if x["atom_id"] in now_by_id and now_by_id[x["atom_id"]]["new_text"] == x["new_text"]]
        print("dry-run atoms", len(exp["atoms"]), "| still identical", len(todo),
              "| new since dry", len(set(now_by_id) - {x["atom_id"] for x in exp["atoms"]}))
        n1 = 0
        async with c.transaction():
            for x in todo:
                r = await c.execute("UPDATE acp_contract.tour_atoms SET text=$2, action=$3, updated_at=now() "
                                    "WHERE atom_id=$1 AND text=$4",
                                    x["atom_id"], x["new_text"], x["new_action"] or None, x["old_text"])
                n1 += int(r.split()[-1])
            print("APPLIED atoms", n1)
            assert n1 == len(todo), "row count mismatch — rolling back"
    await c.close()

asyncio.run(main())
