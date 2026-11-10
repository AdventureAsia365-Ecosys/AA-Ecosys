"""AA-741 phase 3, slice 1 (S276): T9/T10 holds deep-dive + the tour x tenant pairs with no Blog Subject.
READ-ONLY ($0, no LLM, no write; the session is set read-only). Prints counts, 8-char ids, numbers, gate names,
reason codes and fixed problem classes only: never tour or piece text, no e-mail, no secret.

Run by the orchestrator (CIS api container, DATABASE_URL = cis_app), one line:
    tools/ecs/ecsx.sh docs/audits/2026-11-10-S276-aa741-phase3/scripts/p3_1_holds_deep.py P2_SINCE=2026-11-10T05:49:46Z

Env
  P2_SINCE  (required) phase 2 start, ISO; only Blog pieces / requests created at or after it are phase 2.
  TOURS8    (optional) the 12 published_tours.id 8-char prefixes; default = the phase 2 PICK_LIST (status.txt).

Sections (feed the phase 3 report, "T9 write / T10 gates" and "T7 Slate / T8 angle" sections):
  HDR      the bands in force: F4 blog band (chars, quality_gates._length_bounds_for_channel), the writer's word
           target (prompts._BLOG_WORDS / _BLOG_WORDS_MAX), rewrite / trim targets (length_trim), MAX_ATTEMPTS.
  PIECE    one line per phase 2 Blog piece: status, attempts, final hold set, length (chars as F4 reads them =
           tag-stripped text; words; body vs FAQ words; sections), side of the F4 band and by how much, side of the
           writer target, tours of the 12 the Subject sits on, tour days / active atoms.
  ATT      per attempt: hold-capable failing gates (first check = a1, final = fin) with the F4 chars each time.
  REP      repair modes per attempt, length-trim logs (before -> after chars), label reason codes.
  CODES    F17 / F13 / F9 / F4 violation counts and fixed problem classes (no quoted text).
  SEED     what the writer got, as sizes: seed words, facts lines, route moments, walk focus, FAQ pairs before/after,
           writer prompt version (hash 8).
  LLM      t9_* ledger rows of the piece/job: calls, cut replies (max_tokens / length), tokens out, cost, non-ok rows.
  DISC     discarded attempts: chars / words / F4 side.
  FAILED   the failed piece(s): job status, error class (first token only), non-ok ledger rows per stage/error_class.
  SUM_*    aggregates: F4 short vs long (+ deltas), the length-only pieces, words vs the writer target, chars per
           word, first-check vs final-check per gate (fixed / kept / introduced), attempts, repair modes, seed vs
           length correlation, approved pieces for contrast.
  PAIR     all 48 (tenant x tour) pairs: Blog Bar candidates on the tour (via slate.py's own SQL / functions):
           segments, bar cleared / miss reasons, seed ok, held place (one_piece_per_place), thin walk, Debate flags
           (from the cache only, never a paid call), Blog Subjects on the tour by state, T8 angle requests (before /
           since P2_SINCE, status, options, chosen), Blog pieces before / since. NOSUBJ marks the pairs with no
           phase 2 Blog piece and gives the first blocking reason.
  T7JOB    t7_slate job results of the audit tenants since P2_SINCE (counts only).
  JSON     one line with the aggregates.
"""
import ast
import asyncio
import collections
import json
import os
import re
import statistics
import sys
from datetime import datetime

import asyncpg

sys.path.insert(0, "/app")

AUDIT = ["audit-atlas-hearth", "audit-terra-family", "audit-trail-pulse", "audit-wildkind-travel"]
DEFAULT_TOURS8 = ("8602c1d4,2cf487be,84e392c3,caf4bf16,ac574bfe,56b61f58,207e4efa,2d0ee81a,c9716429,a8560125,"
                  "7fe02d1a,b56704c5")
EXCLUDE_PIECES8 = {"d67e3178"}  # synthetic piece (S238 rule), excluded from phase 3 numbers

WORD_RE = re.compile(r"[A-Za-zÀ-ɏ0-9]+(?:['’-][A-Za-zÀ-ɏ0-9]+)*")
FAQ_RE = re.compile(r"^#{2,3}\s*(?:FAQ|Frequently asked)", re.I | re.M)
H2_RE = re.compile(r"^##\s+\S", re.M)
F4_SHORT_RE = re.compile(r"only (\d+) chars")
F4_LONG_RE = re.compile(r"is (\d+) chars")
TRIM_RE = re.compile(r"trimmed (\d+) paragraph\(s\) to fit the blog length band \(([\d,]+) → ([\d,]+) chars")
DAYS_RE = re.compile(r"(\d+)\s*(?:days?|d\b|ngày)", re.I)
CUT_STOPS = ("max_tokens", "length")

# Fixed problem classes (code-generated violation prefixes in trip_facts.py / hygiene.py); never the quoted text.
F17_CLASSES = [
    ("as part of the plan", "optional_as_planned"),
    ("gives a time the source does not", "time_not_in_source"),
    ("places the trip somewhere", "place_not_in_source"),
    ("still holds a role", "role_ended"),
    ("gives the span as", "span_vs_dates"),
    ("closes on a thin moment", "thin_moment_close"),
    ("gives the thin moment", "thin_moment_heading"),
    ("pace or rest promise", "pace_promise"),
    ("service level the source does not", "service_claim"),
    ("to families but never says", "family_caveat_missing"),
    ("plays down a hazard", "hazard_downplayed"),
    ("gateway or base", "gateway_not_on_trip"),
    ("rarity claim", "rarity"),
    ("generalises about", "generalisation"),
    ("where the source says", "quantifier_strengthened"),
]
F13_CLASSES = [
    ("repeats an earlier sentence", "repeat_sentence"),
    ("adds nothing to the sentences around it", "adds_nothing"),
    ("repeats a moment under another moment's heading", "moment_under_other_heading"),
    ("say something new", "dedupe_echo"),
]


def p8(x) -> str:
    return str(x)[:8] if x is not None else "-"


def src_const(rel: str, name: str, default):
    """A module-level literal (`NAME = 3`, `NAME = (900, 1300)  # note`) read from the deployed source under /app,
    without importing the module. `default` (with a WARN) when the line is missing or not a literal."""
    pat = re.compile(rf"^{re.escape(name)}\s*(?::[^=]+)?=\s*(.+?)\s*(?:#.*)?$")
    try:
        with open(os.path.join("/app", rel), encoding="utf-8") as fh:
            for ln in fh:
                m = pat.match(ln.rstrip("\n"))
                if m:
                    return ast.literal_eval(m.group(1))
    except Exception as e:  # noqa: BLE001
        print(f"WARN {name} not read from {rel} ({type(e).__name__}); default {default}")
        return default
    print(f"WARN {name} not found in {rel}; default {default}")
    return default


def quiet_logs() -> None:
    """Drop every structlog event of the imported app modules (slate / walk_focus log Segment id lists): the run
    prints only this script's own lines. Called after the imports."""
    try:
        import structlog

        def _drop(_logger, _name, _event):
            raise structlog.DropEvent

        structlog.configure(processors=[_drop])
    except Exception:  # noqa: BLE001
        pass


def held_head(v) -> str:
    """The code-written head of held_reason (a gate / reason token), never the text after it."""
    if not v:
        return "-"
    m = re.match(r"\s*([A-Za-z0-9_]{1,40})", str(v))
    tok = m.group(1) if m else ""
    # a code token has an underscore (F4_extreme_length) or is one lowercase word (degraded); anything else is prose
    return tok if tok and ("_" in tok or tok.islower()) else "free_text"


def has_test_flag(obj) -> bool:
    """S238 rule: a synthetic piece carries a `*_test` key somewhere in content_piece.flags (list or dict)."""
    if isinstance(obj, dict):
        return any(str(k).endswith("_test") for k in obj) or any(has_test_flag(v) for v in obj.values())
    if isinstance(obj, list):
        return any(has_test_flag(v) for v in obj)
    return False


def jl(v):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            return None
    return v


def classify(v: str, table) -> str:
    s = str(v)
    seo = s.startswith(("title ", "meta "))
    for needle, cls in table:
        if needle in s:
            return ("seo:" if seo else "") + cls
    return ("seo:" if seo else "") + "other"


def generic_head(v: str) -> str:
    """The code-written problem phrase only: cut at the first quote / paren / colon-quote / dash; at most 45 chars."""
    s = str(v).split(": '", 1)[0].split(" — ", 1)[0]
    s = re.split(r"['\"(‘“]", s, 1)[0]
    s = re.sub(r"\d+", "N", s).strip()
    # a capitalised word after the first is a name from the piece (unquoted text): never print it
    if any(w[:1].isupper() for w in s.split()[1:]):
        return "unquoted_text"
    return s[:45] or "other"


def text_measure(text: str, strip) -> dict:
    t = strip(text or "")
    words = WORD_RE.findall(t)
    m = FAQ_RE.search(t)
    body = t[:m.start()] if m else t
    faq = t[m.start():] if m else ""
    return {"chars": len(t), "words": len(words), "body_words": len(WORD_RE.findall(body)),
            "faq_words": len(WORD_RE.findall(faq)), "sections": len(H2_RE.findall(body)), "has_faq": bool(m)}


def f4_chars(entries) -> tuple[str, int | None]:
    """(side, chars) of a failed F4_extreme_length entry in a ledger / snapshot; ('in', None) when it passed."""
    for g in entries or []:
        if not isinstance(g, dict) or g.get("gate") != "F4_extreme_length" or g.get("passed"):
            continue
        for v in g.get("violations") or []:
            m = F4_SHORT_RE.search(str(v))
            if m:
                return "short", int(m.group(1))
            m = F4_LONG_RE.search(str(v))
            if m:
                return "long", int(m.group(1))
        return "fail?", None
    return "in", None


def pearson(xs, ys):
    pts = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pts) < 3:
        return None
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    syy = sum((p[1] - my) ** 2 for p in pts)
    return round(sxy / (sxx * syy) ** 0.5, 3) if sxx and syy else None


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"n": 0}
    return {"n": len(vals), "min": min(vals), "med": round(statistics.median(vals), 1), "max": max(vals),
            "mean": round(sum(vals) / len(vals), 1)}


async def main() -> None:
    if not os.environ.get("P2_SINCE"):
        print("STOP P2_SINCE is required (ISO, phase 2 start)")
        return
    since = datetime.fromisoformat(os.environ["P2_SINCE"].replace("Z", "+00:00"))
    tours8 = [t.strip().lower()[:8] for t in os.environ.get("TOURS8", DEFAULT_TOURS8).split(",") if t.strip()]

    from services.acp_content_writing import gate_eval
    from services.acp_content_writing.quality_gates import _length_bounds_for_channel
    from services.acp_shared.citation_tags import strip_citation_tags
    # S276 review (OOM / speed): the writer / trim / service constants are read from the deployed source, not
    # imported. service.py pulls in FastAPI + every writer module and prompts.py the angle-gate stack: hundreds of MB
    # in the api container for four numbers.
    writer_words = src_const("services/acp_content_writing/prompts.py", "_BLOG_WORDS", (900, 1300))
    writer_max = src_const("services/acp_content_writing/prompts.py", "_BLOG_WORDS_MAX", 1600)
    rewrite_target = src_const("services/acp_content_writing/length_trim.py", "REWRITE_TARGET_CHARS", None)
    trim_target = src_const("services/acp_content_writing/length_trim.py", "BLOG_TRIM_TARGET_CHARS", None)
    MAX_ATTEMPTS = src_const("services/acp_content_writing/service.py", "MAX_ATTEMPTS", 3)
    STOP_AND_LABEL = src_const("services/acp_content_writing/service.py", "STOP_AND_LABEL", "stop_and_label")
    _mode = (os.environ.get("T9_LAST_ATTEMPT_MODE") or "").strip().lower()  # service.last_attempt_mode(), api env
    attempt_mode = _mode if _mode in (STOP_AND_LABEL, "legacy") else STOP_AND_LABEL
    band_lo, band_hi = _length_bounds_for_channel("blog")
    quiet_logs()
    print(f"HDR since={since.isoformat()} f4_blog_band_chars={band_lo}-{band_hi} (fixed config, channel only: "
          f"not tour length, not angle) writer_target_words={writer_words[0]}-{writer_words[1]} "
          f"writer_max_words={writer_max} rewrite_target_chars={rewrite_target} trim_target_chars={trim_target} "
          f"max_attempts={MAX_ATTEMPTS} last_attempt_mode={attempt_mode}")

    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        await c.execute("SET default_transaction_read_only = on")
        await c.execute("SET statement_timeout = '120s'")
        ten = await c.fetch("SELECT tenant_id, slug FROM shared.tenants WHERE slug = ANY($1::text[]) ORDER BY slug",
                            AUDIT)
        slug = {t["tenant_id"]: t["slug"] for t in ten}
        tids = [t["tenant_id"] for t in ten]
        pts = await c.fetch(
            "SELECT pt.id, pt.tour_id, rt.duration, rt.country_iso2 FROM gold_aa_internal.published_tours pt "
            "JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = pt.tour_id WHERE left(pt.id::text, 8) = ANY($1::text[])",
            tours8)
        byp = collections.defaultdict(list)
        for r in pts:
            byp[str(r["id"])[:8]].append(r)
        tour_of_p8 = {}
        for t8 in tours8:
            if len(byp.get(t8, [])) != 1:
                print(f"WARN tour={t8} matches={len(byp.get(t8, []))} (need exactly 1): skipped")
                continue
            tour_of_p8[t8] = byp[t8][0]
        p8_of_tour = {r["tour_id"]: k for k, r in tour_of_p8.items()}
        atoms = {r["tour_id"]: r["n"] for r in await c.fetch(
            "SELECT tour_id, count(*) AS n FROM acp_contract.v_active_tour_atoms WHERE tour_id = ANY($1::uuid[]) "
            "GROUP BY 1", list(p8_of_tour))}
        days = {}
        for k, r in tour_of_p8.items():
            m = DAYS_RE.search(r["duration"] or "")
            days[k] = int(m.group(1)) if m else None
        print("TOURS " + " ".join(f"{k}:{tour_of_p8[k]['country_iso2'] or '-'}/d{days[k]}/a{atoms.get(tour_of_p8[k]['tour_id'], 0)}"
                                  for k in tour_of_p8))

        # ------------------------------------------------------------ pieces
        rows = await c.fetch(
            "SELECT cp.piece_id, cp.tenant_id, cp.status, cp.attempt_number, cp.held_reason, cp.content_text, "
            "cp.gate_ledger, cp.repair_log, cp.flags, cp.discarded_attempts, cp.writer_input, cp.job_id, cp.created_at, "
            "cp.angle_gate_request_id, r.subject_id, r.route_segment_ids, s.segment_id, s.state AS subject_state "
            "FROM acp_shared.content_piece cp "
            "JOIN acp_shared.angle_gate_request r ON r.request_id = cp.angle_gate_request_id "
            "LEFT JOIN acp_shared.subject s ON s.subject_id = r.subject_id "
            "WHERE cp.tenant_id = ANY($1::uuid[]) AND cp.channel = 'blog' AND cp.created_at >= $2 "
            "ORDER BY cp.tenant_id, cp.created_at", tids, since)
        n_all = len(rows)
        rows = [r for r in rows if p8(r["piece_id"]) not in EXCLUDE_PIECES8 and not has_test_flag(jl(r["flags"]))]
        if len(rows) != n_all:
            print(f"EXCLUDED test_or_synthetic_pieces={n_all - len(rows)}")

        def piece_segs(r) -> list:
            """The piece's Segment ids: its Subject's Segment, else (route-grain Subject) the request's walk."""
            if r["segment_id"]:
                return [r["segment_id"]]
            return [str(x) for x in (jl(r["route_segment_ids"]) or []) if x]

        # every current ranked (tour, segment) of the 12 tours, read ONCE (atom_ranking has no tour-leading index:
        # one scan here instead of one per piece / pair)
        tour_segs = collections.defaultdict(set)
        seg_tours = collections.defaultdict(set)
        for r in await c.fetch(
                "SELECT DISTINCT segment_id, tour_id FROM acp_contract.atom_ranking WHERE tour_id = ANY($1::uuid[]) "
                "AND excluded_reason IS NULL AND superseded_at IS NULL", list(p8_of_tour)):
            tour_segs[r["tour_id"]].add(r["segment_id"])
            seg_tours[r["segment_id"]].add(p8_of_tour[r["tour_id"]])

        print(f"PIECES n={len(rows)} status={dict(collections.Counter(r['status'] for r in rows))}")
        recs = []
        for r in rows:
            led = jl(r["gate_ledger"]) or []
            rlog = jl(r["repair_log"]) or []
            flags = jl(r["flags"]) or []
            disc = jl(r["discarded_attempts"]) or []
            wi = jl(r["writer_input"]) or {}
            meas = text_measure(r["content_text"], strip_citation_tags)
            final_fail = gate_eval.failing_gates(led)
            final_hold = sorted({g["source"] for g in final_fail if g["may_hold"]})
            codes = gate_eval.hold_reason_codes(led, r["held_reason"])
            f4side, f4n = f4_chars(led)
            side = "short" if meas["chars"] < band_lo else ("long" if meas["chars"] > band_hi else "in")
            delta = meas["chars"] - band_lo if side == "short" else (meas["chars"] - band_hi if side == "long" else 0)
            wside = ("under" if meas["words"] < writer_words[0] else "in" if meas["words"] <= writer_words[1]
                     else "over" if meas["words"] <= writer_max else "over_max")
            tours = sorted({t for s in piece_segs(r) for t in seg_tours.get(s, ())})
            t0 = tours[0] if tours else None

            # per attempt (repair_log attempt-failure entries carry the attempt's trimmed ledger + failing rows)
            att = {}
            modes = []
            for e in rlog:
                if not isinstance(e, dict):
                    continue
                if e.get("gate_targeted") == STOP_AND_LABEL or e.get("repair_mode") in (STOP_AND_LABEL, "label"):
                    continue
                a = e.get("attempt")
                if "gate_ledger" in e or "failing" in e:
                    if a in att:
                        continue
                    fl = e.get("failing")
                    if fl is None:
                        try:
                            fl = gate_eval.failing_gates(e.get("gate_ledger"))
                        except Exception:  # noqa: BLE001
                            fl = []
                    hs = sorted({g.get("source") for g in fl if g.get("may_hold")})
                    s4, n4 = f4_chars(e.get("gate_ledger"))
                    att[a] = {"hold": hs, "f4": s4, "f4_chars": n4,
                              "mode": e.get("repair_mode") or ("full_rewrite" if a and a < r["attempt_number"] else "-")}
                    modes.append(f"a{a}:{att[a]['mode']}")
                elif e.get("repair_mode"):
                    modes.append(f"a{a}:{e.get('repair_mode')}")
            label = next((e for e in rlog if isinstance(e, dict) and e.get("repair_mode") in (STOP_AND_LABEL, "label")),
                         None)
            if 1 in att:
                first_hold, first_f4 = att[1]["hold"], (att[1]["f4"], att[1]["f4_chars"])
            elif r["attempt_number"] == 1:
                first_hold, first_f4 = final_hold, (f4side, f4n)
            else:
                first_hold, first_f4 = None, None  # attempt 1 not recorded
            trims = []
            for fg in flags:
                if isinstance(fg, dict):
                    for v in fg.get("violations") or []:
                        m = TRIM_RE.search(str(v))
                        if m:
                            trims.append((int(m.group(1)), int(m.group(2).replace(",", "")),
                                          int(m.group(3).replace(",", ""))))

            # violation classes on the final ledger (fixed classes / code phrase heads only)
            cls = {"F17_trip_fact": collections.Counter(), "F13_repeat": collections.Counter(),
                   "F9_cta_fact": collections.Counter()}
            nviol = collections.Counter()
            for g in final_fail:
                nviol[g["source"]] += g.get("n") or 0
                if g["source"] == "F9_cta_fact":
                    for k, v in (g.get("classes") or {}).items():
                        cls["F9_cta_fact"][k] += v
            for g in led:
                if not isinstance(g, dict) or g.get("passed"):
                    continue
                gname = g.get("gate")
                vs = g.get("violations") or []
                if gname == "F17_trip_fact":
                    for v in vs:
                        cls["F17_trip_fact"][classify(v, F17_CLASSES)] += 1
                elif gname == "F13_repeat":
                    for v in vs:
                        c13 = classify(v, F13_CLASSES)
                        cls["F13_repeat"][c13 if not c13.endswith("other") else "other:" + generic_head(v)] += 1

            seed_words = len(WORD_RE.findall(wi.get("seed") or ""))
            facts_lines = len([x for x in (wi.get("facts") or "").splitlines() if x.strip()])
            moments = len(wi.get("route_moments") or [])
            moment_words = sum(len(WORD_RE.findall((m or {}).get("seed") or "")) for m in (wi.get("route_moments") or []))

            llm = await c.fetch(
                "SELECT stage, count(*) AS n, sum(coalesce(tokens_out,0)) AS tout, "
                "count(*) FILTER (WHERE stop_reason = ANY($3::text[])) AS cut, "
                "count(*) FILTER (WHERE coalesce(status,'ok') <> 'ok') AS bad, sum(coalesce(cost_usd,0)) AS usd, "
                "array_agg(DISTINCT model) AS models "
                "FROM shared.llm_call_log WHERE (content_piece_id = $1 OR ($2::uuid IS NOT NULL AND job_id = $2)) "
                "AND stage LIKE 't9%' AND is_shadow IS NOT TRUE GROUP BY 1 ORDER BY 1",
                r["piece_id"], r["job_id"], list(CUT_STOPS))
            dlen = []
            for d in disc:
                if isinstance(d, dict):
                    dm = text_measure(d.get("content_text") or "", strip_citation_tags)
                    ds, _ = f4_chars(d.get("gate_ledger"))
                    dlen.append({"attempt": d.get("attempt_number"), "chars": dm["chars"], "words": dm["words"],
                                 "f4": ds})

            rec = {
                "piece": p8(r["piece_id"]), "tenant": slug[r["tenant_id"]], "status": r["status"],
                "attempts": r["attempt_number"], "held_head": held_head(r["held_reason"]),
                "grain": "segment" if r["segment_id"] else ("route" if r["route_segment_ids"] else "none"),
                "final_hold": final_hold, "codes": codes, "first_hold": first_hold,
                "first_f4": first_f4, "final_f4": (f4side, f4n), **meas, "side": side, "delta": delta,
                "wside": wside, "tours": tours, "days": days.get(t0) if t0 else None,
                "atoms": atoms.get(tour_of_p8[t0]["tour_id"]) if t0 else None,
                "att": att, "modes": modes, "trims": trims,
                "label_codes": (label or {}).get("reason_codes"),
                "nviol": dict(nviol), "cls": {k: dict(v) for k, v in cls.items() if v},
                "seed_words": seed_words, "facts_lines": facts_lines, "moments": moments,
                "moment_words": moment_words, "walk_focus": bool(wi.get("walk_focus")),
                "faq_before": wi.get("faq_pairs_before"), "faq_after": wi.get("faq_pairs_after"),
                "wpv": p8(wi.get("writer_prompt_version")), "subject": p8(r["subject_id"]),
                "route_ids": len(jl(r["route_segment_ids"]) or []), "job": r["job_id"],
                "llm": {x["stage"]: {"n": x["n"], "tout": int(x["tout"] or 0), "cut": x["cut"], "bad": x["bad"],
                                     "usd": round(float(x["usd"] or 0), 4), "models": sorted(m for m in x["models"] if m)}
                        for x in llm},
                "disc": dlen,
            }
            recs.append(rec)
            hs = ",".join(final_hold) or "-"
            print(f"PIECE {rec['piece']} tenant={rec['tenant']} status={rec['status']} attempts={rec['attempts']} "
                  f"held_head={rec['held_head']} final_hold={hs} codes={','.join(codes) or '-'} subject={rec['subject']} "
                  f"grain={rec['grain']} tours={','.join(tours) or '-'} days={rec['days']} atoms={rec['atoms']} "
                  f"walk_ids={rec['route_ids']}")
            print(f"  LEN chars={meas['chars']} words={meas['words']} body_words={meas['body_words']} "
                  f"faq_words={meas['faq_words']} sections={meas['sections']} faq={int(meas['has_faq'])} "
                  f"cpw={round(meas['chars'] / meas['words'], 2) if meas['words'] else '-'} f4_side={side} "
                  f"delta_chars={delta:+d} f4_ledger={f4side}:{f4n} writer={wside} "
                  f"vs_floor_words={meas['words'] - writer_words[0]:+d}")
            atxt = " ".join(f"a{a}={','.join(v['hold']) or 'pass'}(F4 {v['f4']}:{v['f4_chars']})"
                            for a, v in sorted(att.items(), key=lambda kv: kv[0] or 0))
            print(f"  ATT {atxt or 'a1=pass'} fin={hs}(F4 {f4side}:{f4n})")
            print(f"  REP modes={' '.join(modes) or '-'} trims={trims or '-'} label_codes={rec['label_codes']}")
            print(f"  CODES nviol={dict(nviol)} classes={rec['cls']}")
            print(f"  SEED seed_words={seed_words} facts_lines={facts_lines} route_moments={moments} "
                  f"moment_seed_words={moment_words} walk_focus={int(rec['walk_focus'])} "
                  f"faq_pairs={rec['faq_before']}->{rec['faq_after']} writer_prompt={rec['wpv']}")
            print("  LLM " + (" ".join(f"{k}:n{v['n']}/cut{v['cut']}/bad{v['bad']}/out{v['tout']}/${v['usd']}/"
                                      f"{'+'.join(v['models'])}" for k, v in rec["llm"].items()) or "-"))
            if dlen:
                print("  DISC " + " ".join(f"a{d['attempt']}:{d['chars']}c/{d['words']}w/F4 {d['f4']}" for d in dlen))

        # ------------------------------------------------------------ failed piece(s)
        for rec in [x for x in recs if x["status"] == "failed"]:
            j = await c.fetchrow("SELECT kind, status, attempt, max_attempts, error, result FROM shared.job WHERE id = $1",
                                 rec["job"]) if rec["job"] else None
            err = (j["error"] or "") if j else ""
            m = re.match(r"\s*([A-Za-z_][\w.]*)", err)
            res = jl(j["result"]) if j else None
            print(f"FAILED piece={rec['piece']} tenant={rec['tenant']} held_head={rec['held_head']} "
                  f"job={p8(rec['job'])} job_kind={j['kind'] if j else '-'} job_status={j['status'] if j else '-'} "
                  f"job_attempt={j['attempt'] if j else '-'}/{j['max_attempts'] if j else '-'} "
                  f"error_class={m.group(1)[:60] if m else '-'} error_len={len(err)} "
                  f"result_keys={sorted(res)[:15] if isinstance(res, dict) else '-'}")
            for x in await c.fetch(
                    "SELECT stage, coalesce(status,'ok') AS st, coalesce(error_class,'-') AS ec, stop_reason, count(*) AS n "
                    "FROM shared.llm_call_log WHERE (content_piece_id = $1 OR job_id = $2) AND is_shadow IS NOT TRUE "
                    "GROUP BY 1,2,3,4 ORDER BY 1", next(r["piece_id"] for r in rows if p8(r["piece_id"]) == rec["piece"]),
                    rec["job"]):
                print(f"  FAILED_LLM stage={x['stage']} status={x['st']} error_class={x['ec']} stop={x['stop_reason']} n={x['n']}")

        # ------------------------------------------------------------ aggregates
        held = [x for x in recs if x["status"] == "held"]
        appr = [x for x in recs if x["status"] == "approved"]
        f4h = [x for x in held if "F4_extreme_length" in x["final_hold"]]
        f4only = [x for x in held if x["final_hold"] == ["F4_extreme_length"]]
        summ = {
            "n": len(recs), "held": len(held), "approved": len(appr), "failed": sum(x["status"] == "failed" for x in recs),
            "band_chars": [band_lo, band_hi], "writer_words": [*writer_words, writer_max],
            "f4_held": {"n": len(f4h), "short": sum(x["side"] == "short" for x in f4h),
                        "long": sum(x["side"] == "long" for x in f4h), "in_now": sum(x["side"] == "in" for x in f4h),
                        "delta_short": stats([x["delta"] for x in f4h if x["side"] == "short"]),
                        "delta_long": stats([x["delta"] for x in f4h if x["side"] == "long"]),
                        "words": stats([x["words"] for x in f4h])},
            "f4_only": {"n": len(f4only), "short": sum(x["side"] == "short" for x in f4only),
                        "long": sum(x["side"] == "long" for x in f4only),
                        "delta": stats([x["delta"] for x in f4only]), "words": stats([x["words"] for x in f4only]),
                        "pieces": [x["piece"] for x in f4only]},
            "words_by_status": {s: stats([x["words"] for x in recs if x["status"] == s])
                                for s in ("held", "approved", "failed")},
            "chars_by_status": {s: stats([x["chars"] for x in recs if x["status"] == s])
                                for s in ("held", "approved", "failed")},
            "writer_side": dict(collections.Counter(x["wside"] for x in recs)),
            "f4_side_all": dict(collections.Counter(x["side"] for x in recs)),
            "cpw": stats([round(x["chars"] / x["words"], 2) for x in recs if x["words"]]),
            "chars_at_writer_floor": round(writer_words[0] * statistics.median(
                [x["chars"] / x["words"] for x in recs if x["words"]]), 0) if any(x["words"] for x in recs) else None,
            "attempts": dict(collections.Counter(x["attempts"] for x in recs)),
            "attempts_held": dict(collections.Counter(x["attempts"] for x in held)),
            "repair_modes": dict(collections.Counter(m.split(":", 1)[1] for x in recs for m in x["modes"])),
            "trimmed_pieces": sum(1 for x in recs if x["trims"]),
            "final_gate_sets": dict(collections.Counter(",".join(x["final_hold"]) or "-" for x in held)),
            "first_gate_sets": dict(collections.Counter(
                (",".join(x["first_hold"]) or "pass") if x["first_hold"] is not None else "unrecorded" for x in recs)),
            "first_f4_side": dict(collections.Counter((x["first_f4"] or ("unrecorded",))[0] for x in recs)),
            "seed_vs_words_r": pearson([x["seed_words"] + x["moment_words"] for x in recs], [x["words"] for x in recs]),
            "days_vs_words_r": pearson([x["days"] for x in recs], [x["words"] for x in recs]),
            "atoms_vs_words_r": pearson([x["atoms"] for x in recs], [x["words"] for x in recs]),
            "f17_classes": dict(sum((collections.Counter(x["cls"].get("F17_trip_fact", {})) for x in held),
                                    collections.Counter())),
            "f13_classes": dict(sum((collections.Counter(x["cls"].get("F13_repeat", {})) for x in held),
                                    collections.Counter())),
            "f9_classes": dict(sum((collections.Counter(x["cls"].get("F9_cta_fact", {})) for x in held),
                                   collections.Counter())),
            "t9_write_cut_pieces": sum(1 for x in recs if (x["llm"].get("t9_write") or {}).get("cut")),
            "t9_write_calls": stats([(x["llm"].get("t9_write") or {}).get("n") for x in recs]),
            "pieces_per_subject": dict(collections.Counter(collections.Counter(
                (x["tenant"], x["subject"]) for x in recs).values())),
            "pairs_per_piece": dict(collections.Counter(len(x["tours"]) for x in recs)),
            "writer_prompt_versions": dict(collections.Counter(x["wpv"] for x in recs)),
        }
        trans = collections.defaultdict(collections.Counter)
        for x in recs:
            if x["first_hold"] is None:
                continue
            fs, ls = set(x["first_hold"]), set(x["final_hold"])
            for g in fs | ls:
                trans[g]["kept" if g in fs and g in ls else "fixed" if g in fs else "introduced"] += 1
        summ["first_vs_final"] = {g: dict(v) for g, v in trans.items()}
        print("SUM_F4 " + json.dumps(summ["f4_held"]))
        print("SUM_F4_ONLY " + json.dumps(summ["f4_only"]))
        print("SUM_LEN words_by_status=" + json.dumps(summ["words_by_status"]) + " chars_by_status="
              + json.dumps(summ["chars_by_status"]) + f" writer_side={summ['writer_side']} f4_side_all={summ['f4_side_all']}"
              f" cpw={summ['cpw']} chars_at_writer_floor~{summ['chars_at_writer_floor']}")
        print(f"SUM_FIRST_FINAL first_sets={summ['first_gate_sets']} final_sets={summ['final_gate_sets']} "
              f"first_f4_side={summ['first_f4_side']} per_gate={summ['first_vs_final']}")
        print(f"SUM_ATTEMPTS all={summ['attempts']} held={summ['attempts_held']} modes={summ['repair_modes']} "
              f"trimmed_pieces={summ['trimmed_pieces']} t9_write_calls={summ['t9_write_calls']} "
              f"t9_write_cut_pieces={summ['t9_write_cut_pieces']}")
        print(f"SUM_CLASSES F17={summ['f17_classes']} F13={summ['f13_classes']} F9={summ['f9_classes']}")
        print(f"SUM_DRIVERS r(seed+moment words, words)={summ['seed_vs_words_r']} r(days, words)={summ['days_vs_words_r']}"
              f" r(atoms, words)={summ['atoms_vs_words_r']} pieces_per_subject={summ['pieces_per_subject']} "
              f"tours_per_piece={summ['pairs_per_piece']} writer_prompt_versions={summ['writer_prompt_versions']}")

        # ------------------------------------------------------------ pairs: Slate / angle per (tenant, tour)
        pairs_out = []
        try:
            from services.acp_shared import slate as sl
            from services.quality.registry import threshold as _thr
            BRAND_FIT_CUT_THRESHOLD = _thr("t7.brand_fit_cut")  # = debate.BRAND_FIT_CUT_THRESHOLD, no LLM import
            CONTESTED_CUT_THRESHOLD = src_const("services/acp_contract/atom_ranking.py", "CONTESTED_CUT_THRESHOLD", 0.5)
        except Exception as e:  # noqa: BLE001
            print(f"STOP_PAIRS slate import failed: {type(e).__name__}")
            sl = None
        quiet_logs()
        try:
            from services.seo_intelligence.seed_builder import LOCATION_CODE_TO_MARKET, resolve_buyer_markets
        except Exception:  # noqa: BLE001
            LOCATION_CODE_TO_MARKET, resolve_buyer_markets = None, None
        if sl is not None:
            for t in ten:
                tid = t["tenant_id"]
                tm = jl(await c.fetchval("SELECT target_market FROM shared.tenant_seo_config WHERE tenant_id = $1 "
                                         "LIMIT 1", tid)) or {}
                try:
                    markets = [LOCATION_CODE_TO_MARKET[loc] for loc, _n, _l in resolve_buyer_markets(tm)]
                except Exception:  # noqa: BLE001
                    known = ("US", "UK", "AU", "DE", "FR", "NL")
                    markets = [x for x in known if x in ((tm or {}).get("countries") or [])] or ["US"]
                markets = markets or ["US"]
                tenant_tours = await sl._tenant_tour_ids(tid, c)
                cand_rows = await c.fetch(sl._SEGMENT_CANDIDATES_SQL, tenant_tours, markets) if tenant_tours else []
                try:
                    seeded = await sl._segments_with_seed(tid, c, cand_rows, {str(x) for x in tenant_tours})
                    seeded_ids = {r["segment_id"] for r in seeded}
                except Exception as e:  # noqa: BLE001
                    print(f"WARN seed check failed tenant={t['slug']}: {type(e).__name__}")
                    seeded_ids = None
                cands = {r["segment_id"]: sl.Candidate(
                    segment_id=r["segment_id"], route_id=None, score=r["total_rank"], demand=r["demand_volume"],
                    questions=r["questions"] or 0, said=r["said"] or 0, place=r["canonical_place"],
                    action=r["canonical_action"]) for r in cand_rows}
                held_map = await sl._fetch_held_subjects(tid, c, ["blog"])
                held_blog = held_map.get("blog")
                try:
                    pool_for_thin = [cands[s] for s in cands if seeded_ids is None or s in seeded_ids]
                    thin = (await sl._fetch_thin_walk_segments(tid, c, pool_for_thin, ["blog"])).get("blog") or frozenset()
                except Exception as e:  # noqa: BLE001
                    print(f"WARN thin check failed tenant={t['slug']}: {type(e).__name__}")
                    thin = None
                dcache = {r["segment_id"]: r for r in await c.fetch(
                    "SELECT DISTINCT ON (segment_id) segment_id, judge_score FROM acp_shared.debate_brand_fit_cache "
                    "WHERE tenant_id = $1 AND segment_id IS NOT NULL ORDER BY segment_id, computed_at DESC", tid)}
                contested = {r["segment_id"]: r["contested"] for r in await c.fetch(
                    "SELECT segment_id, contested FROM acp_contract.atom_segment WHERE segment_id = ANY($1::text[])",
                    list(cands))}
                print(f"PAIR_TENANT {t['slug']} markets={'/'.join(markets)} tenant_tours={len(tenant_tours)} "
                      f"candidates={len(cand_rows)} seeded={len(seeded_ids) if seeded_ids is not None else '?'} "
                      f"held_blog_segments={len(held_blog.segment_ids) if held_blog else 0} "
                      f"held_blog_places={len(held_blog.places) if held_blog else 0} "
                      f"thin={len(thin) if thin is not None else '?'}")
                for t8, pr in tour_of_p8.items():
                    on_tour = sorted(tour_segs.get(pr["tour_id"], ()))
                    in_mk = [s for s in on_tour if s in cands]
                    miss = collections.Counter(sl.bar_status("blog", cands[s]) for s in in_mk)
                    cleared = [s for s in in_mk if sl.bar_status("blog", cands[s]) == sl.BAR_CLEARED]
                    no_seed = [s for s in cleared if seeded_ids is not None and s not in seeded_ids]
                    seeded_c = [s for s in cleared if s not in no_seed]
                    held_c = [s for s in seeded_c if held_blog and held_blog.holds(cands[s])]
                    thin_c = [s for s in seeded_c if thin and s in thin and s not in held_c]
                    free = [s for s in seeded_c if s not in held_c and s not in (thin or ())]
                    deb = [s for s in free if (contested.get(s) is not None and contested[s] >= CONTESTED_CUT_THRESHOLD)
                           or (s in dcache and dcache[s]["judge_score"] < BRAND_FIT_CUT_THRESHOLD)]
                    places_free = len({sl._place_key(cands[s].place) for s in free})
                    subj = await c.fetch(
                        "SELECT subject_id, segment_id, state FROM acp_shared.subject WHERE tenant_id = $1 "
                        "AND channel = 'blog' AND segment_id = ANY($2::text[])", tid, on_tour)
                    sstate = dict(collections.Counter(s["state"] for s in subj))
                    other_ch = await c.fetchval(
                        "SELECT count(DISTINCT channel) FROM acp_shared.subject WHERE tenant_id = $1 AND channel <> 'blog' "
                        "AND segment_id = ANY($2::text[])", tid, free) if free else 0
                    sids = [s["subject_id"] for s in subj]
                    reqs = await c.fetch(
                        "SELECT r.request_id, r.status, r.created_at >= $2 AS p2, "
                        "(SELECT count(*) FROM acp_shared.angle_gate_option o WHERE o.request_id = r.request_id) AS opts, "
                        "(SELECT count(*) FROM acp_shared.angle_gate_option o WHERE o.request_id = r.request_id "
                        "  AND o.chosen) AS chosen "
                        "FROM acp_shared.angle_gate_request r WHERE r.subject_id = ANY($1::uuid[])", sids, since) \
                        if sids else []
                    rq_p2 = [x for x in reqs if x["p2"]]
                    pcs = await c.fetch(
                        "SELECT cp.status, cp.created_at >= $2 AS p2 FROM acp_shared.content_piece cp "
                        "JOIN acp_shared.angle_gate_request r ON r.request_id = cp.angle_gate_request_id "
                        "WHERE r.subject_id = ANY($1::uuid[]) AND cp.channel = 'blog'", sids, since) if sids else []
                    pc_p2 = collections.Counter(x["status"] for x in pcs if x["p2"])
                    pc_old = collections.Counter(x["status"] for x in pcs if not x["p2"])
                    nosubj = not pc_p2
                    reason = "-"
                    if nosubj:
                        reason = ("no_ranked_segment" if not on_tour else
                                  "no_segment_in_markets" if not in_mk else
                                  "bar_miss" if not cleared else
                                  "no_seed_atom" if not seeded_c else
                                  "place_held_one_piece_per_place" if not free and held_c and not thin_c else
                                  "thin_walk" if not free and thin_c and not held_c else
                                  "held_or_thin" if not free else
                                  "no_proposed_subject" if not sstate.get("proposed") and not sstate.get("picked") else
                                  "no_angle_request_p2" if not rq_p2 else
                                  "angle_no_options" if not any(x["opts"] for x in rq_p2) else
                                  "no_piece_written")
                    pr_out = {"tenant": t["slug"], "tour": t8, "segments": len(on_tour), "in_markets": len(in_mk),
                              "bar": dict(miss), "cleared": len(cleared), "no_seed": len(no_seed),
                              "held": len(held_c), "thin": len(thin_c), "free": len(free), "free_places": places_free,
                              "debate_flag": len(deb), "other_channels_on_free": other_ch, "subjects": sstate,
                              "req_all": len(reqs), "req_p2": len(rq_p2),
                              "req_p2_status": dict(collections.Counter(x["status"] for x in rq_p2)),
                              "opts_p2": sum(x["opts"] for x in rq_p2), "chosen_p2": sum(x["chosen"] for x in rq_p2),
                              "pieces_p2": dict(pc_p2), "pieces_before": dict(pc_old), "nosubj": nosubj,
                              "reason": reason}
                    pairs_out.append(pr_out)
                    print(f"PAIR tenant={t['slug']} tour={t8} seg={len(on_tour)} in_mk={len(in_mk)} bar={dict(miss)} "
                          f"cleared={len(cleared)} no_seed={len(no_seed)} held={len(held_c)} thin={len(thin_c)} "
                          f"free={len(free)}/{places_free}pl debate_flag={len(deb)} subj={sstate} "
                          f"req={len(reqs)}(p2 {len(rq_p2)} {pr_out['req_p2_status']} opts={pr_out['opts_p2']} "
                          f"chosen={pr_out['chosen_p2']}) pieces_p2={dict(pc_p2)} pieces_before={dict(pc_old)}"
                          + (f" NOSUBJ reason={reason}" if nosubj else ""))
            ns = [p for p in pairs_out if p["nosubj"]]
            print(f"SUM_PAIRS pairs={len(pairs_out)} nosubj={len(ns)} reasons={dict(collections.Counter(p['reason'] for p in ns))} "
                  f"nosubj_with_pieces_before={sum(1 for p in ns if p['pieces_before'])}")
            summ["pairs_nosubj"] = [{k: p[k] for k in ("tenant", "tour", "reason", "cleared", "held", "thin", "free",
                                                       "subjects", "req_all", "req_p2", "pieces_before")} for p in ns]

        # ------------------------------------------------------------ T7 slate jobs (counts only)
        for j in await c.fetch(
                "SELECT id, status, created_at, payload->>'tenant_id' AS tid, result FROM shared.job WHERE kind = 't7_slate' "
                "AND created_at >= $1 AND payload->>'tenant_id' = ANY($2::text[]) ORDER BY created_at",
                since, [str(x) for x in tids]):
            res = jl(j["result"]) or {}
            slug_j = next((s for k, s in slug.items() if str(k) == j["tid"]), "?")
            print(f"T7JOB {p8(j['id'])} tenant={slug_j} status={j['status']} at={j['created_at']:%H:%M} "
                  f"segments_seen={res.get('segments_seen')} routes_seen={res.get('routes_seen')} "
                  f"blog_proposed={(res.get('proposed_per_channel') or {}).get('blog')} "
                  f"blog_bar={(res.get('bar_status') or {}).get('blog')} "
                  f"unmatched_markets={len(res.get('unmatched_markets') or [])}")

        print("JSON " + json.dumps(summ, default=str))
    finally:
        await c.close()


asyncio.run(main())
