"""AA-847 Problem 2 — prototype of the automatic duplicate-place merge decision (rules only; no I/O, no model call).

Design: README.md in this folder. This file is the executable spec of the deterministic part, run on the labelled
pair set (pairs.json) to measure auto-merge precision / recall. The production port is
AA-CIS-App services/places/dedupe.py (validity.is_same_place and pipeline._in_tour_keepers call it).

    python3 -I dedupe_proto.py pairs.json            # summary + every pair
    python3 -I dedupe_proto.py pairs.json --misses   # only the pairs that are not decided correctly by rules
    python3 -I dedupe_proto.py pairs.json --misses --degrade=all_model_points   # robustness: less metadata

Decision per pair (in order):
  1. hard keeps   — other country; a number / direction qualifier differs; kinds incompatible (town vs landmark,
                    market vs night market, …); farther apart than the kind's radius
  2. id evidence  — same Geoapify place_id (same OSM object) or same place card → auto_merge
  3. score        — name x kind x distance (+ geocoder evidence, + embedding when present):
                    >= HIGH auto_merge, >= LOW llm (one cached adjudication call), else keep.
                    An ambiguous kind relation (bare name vs a built place, local-word-only kind difference) or an
                    ambiguous name relation (extra distinctive word, loose spelling match) is capped at llm.
"""
from __future__ import annotations

import difflib
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

RULE_VERSION = "r1.2"
HIGH, LOW = 0.80, 0.30
AUTO, LLM, KEEP = "auto_merge", "llm", "keep"

# ── vocabulary ────────────────────────────────────────────────────────────────────────────────────────────────────
# whole-token spelling variants, applied first (both sides)
SYN = {"vat": "wat", "phou": "phu", "tad": "tat", "paya": "pagoda", "bazaar": "market", "mt": "mount",
       "centre": "center", "falls": "waterfall", "fall": "waterfall", "waterfalls": "waterfall", "caves": "cave",
       "tunnels": "tunnel", "temples": "temple", "markets": "market", "hills": "hill", "islands": "island",
       "gardens": "garden", "mountains": "mountain", "lakes": "lake", "beaches": "beach"}
# two-word kinds (checked before single words; both words consumed)
PHRASE_KINDS = {("night", "market"): "night_market", ("floating", "market"): "floating_market",
                ("old", "town"): "old_town", ("old", "quarter"): "old_town", ("ancient", "town"): "old_town",
                ("old", "city"): "old_town", ("national", "park"): "national_park",
                ("wildlife", "sanctuary"): "reserve", ("nature", "reserve"): "reserve",
                ("imperial", "city"): "fort", ("forbidden", "city"): "fort", ("city", "palace"): "palace"}
# English kind words (hard kinds)
WORD_KINDS = {
    **dict.fromkeys(("waterfall", "cascade", "cascades"), "waterfall"),
    **dict.fromkeys(("cave", "grotto"), "cave"),
    **dict.fromkeys(("mount", "mountain", "hill", "peak"), "mountain"),
    **dict.fromkeys(("lake", "pond", "lagoon", "reservoir"), "lake"),
    **dict.fromkeys(("river", "stream"), "river"),
    **dict.fromkeys(("island", "isle"), "island"),
    "village": "village", "valley": "valley", "pass": "pass", "beach": "beach", "bay": "bay", "park": "park",
    "market": "market", "bridge": "bridge", "museum": "museum", "palace": "palace", "garden": "garden",
    "square": "square", "tunnel": "tunnel", "airport": "airport", "station": "station", "center": "facility",
    **dict.fromkeys(("temple", "pagoda", "monastery", "shrine", "sanctuary", "gompa"), "temple"),
    **dict.fromkeys(("stupa", "chedi", "zedi"), "stupa"),
    **dict.fromkeys(("street", "road", "trail", "highway"), "street"),
    **dict.fromkeys(("wall", "gate", "fort", "fortress", "citadel", "dzong"), "fort"),
    **dict.fromkeys(("statue", "monument", "memorial", "mausoleum", "tomb"), "monument"),
    **dict.fromkeys(("viewpoint", "lookout"), "viewpoint"),
    **dict.fromkeys(("delta",), "delta"), **dict.fromkeys(("plateau",), "plateau"),
    **dict.fromkeys(("gorge", "canyon"), "gorge"),
}
# local kind words (soft kinds: also start proper names, so a difference that comes only from them is ambiguous)
LOCAL_KINDS = {"wat": "temple", "chua": "temple", "den": "temple", "that": "stupa", "thap": "stupa",
               "tat": "waterfall", "thac": "waterfall", "tham": "cave", "hang": "cave", "doi": "mountain",
               "nui": "mountain", "nam": "river", "song": "river", "huay": "river", "ko": "island", "koh": "island",
               "cho": "market", "cau": "bridge", "muang": "town", "mahal": "palace"}
GENERIC = frozenset({"the", "of", "and", "a", "an", "in", "at", "to", "s", "scenic", "landscape", "complex", "area",
                     "site", "weekend", "historic", "historical", "famous", "pha"})
QUALIFIERS = frozenset({"old", "new", "upper", "lower", "north", "south", "east", "west", "northern", "southern",
                        "little", "small", "big", "great", "grand", "inner", "outer"})
WEAK = frozenset({"royal", "national", "central", "imperial", "golden", "sacred", "holy", "main"})
COUNTRY_WORDS = frozenset({"laos", "vietnam", "cambodia", "thailand", "myanmar", "nepal", "bhutan", "china", "tibet",
                           "mongolia", "india", "japan", "korea", "taiwan", "indonesia", "sri", "lanka"})

# kinds whose bare name is usually the feature itself ("Hoan Kiem" = the lake)
NATURAL_BARE = frozenset({"waterfall", "cave", "mountain", "lake", "river", "island", "village", "valley", "pass",
                          "beach", "bay", "park", "town"})
# "X Museum" is often the museum inside the heritage building X ("Royal Palace Museum")
HERITAGE = frozenset({"palace", "fort", "temple", "monument"})
# km radius of the distance gate by kind (a pair takes the largest radius of its kinds); x2 when either point is the
# model's (located_by llm) or an area
RADIUS = {"waterfall": 2, "cave": 2, "pass": 3, "beach": 2, "mountain": 3, "island": 3, "village": 3, "town": 5,
          "old_town": 1.5, "lake": 15, "bay": 15, "valley": 10, "park": 10, "national_park": 25, "reserve": 25,
          "delta": 50, "plateau": 25, "gorge": 10, "river": 50, "street": 50}
POI_RADIUS = 0.5
BARE_FAR_KM = 2.0
POI_TYPES = frozenset({"amenity", "building"})
HARD_SETTLEMENT_TYPES = frozenset({"city"})
SOFT_SETTLEMENT_TYPES = frozenset({"suburb", "district"})


def translit(w: str) -> str:
    """Romanisation variants inside a name word (not a kind word): Phousi = Phusi, Luang = Luang."""
    return w.replace("ou", "u") if len(w) > 2 else w


def strip_accents(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))
    return s.replace("đ", "d").replace("Đ", "D")


@dataclass
class Parsed:
    core: list[str]
    kinds: frozenset
    hard_kinds: frozenset
    qualifiers: frozenset
    numbers: frozenset
    run_local: str               # core + local kind words, run together ("phusi" for "Phou Si")


def parse(name: str) -> Parsed:
    s = strip_accents((name or "").lower())
    s = re.sub(r"\([^)]*\)", " ", s)                       # "(Monkey Temple)": an alias, dropped
    s = re.sub(r"'s\b", "", s)
    head, _, tail = s.partition(",")                       # "Old Quarter, Hanoi": the tail is part of the name
    words = [SYN.get(w, w) for w in re.findall(r"[a-z0-9]+", head + " " + tail)]
    kinds, hard, core, local, quals, nums = set(), set(), [], [], set(), set()
    i = 0
    while i < len(words):
        w = words[i]
        nxt = words[i + 1] if i + 1 < len(words) else None
        if nxt and (w, nxt) in PHRASE_KINDS:
            k = PHRASE_KINDS[(w, nxt)]
            kinds.add(k)
            hard.add(k)
            i += 2
            continue
        if w == "ho" and words[i + 1:i + 3] != ["chi", "minh"]:   # Vietnamese ho = lake, not Ho Chi Minh
            kinds.add("lake")
            local.append(w)
        elif w == "city" and i == len(words) - 1:
            kinds.add("town")
            hard.add("town")
        elif w in WORD_KINDS:
            kinds.add(WORD_KINDS[w])
            hard.add(WORD_KINDS[w])
        elif w in LOCAL_KINDS:
            kinds.add(LOCAL_KINDS[w])
            local.append(w)
        elif w.isdigit():
            nums.add(w)
        elif w in QUALIFIERS:
            quals.add(w)
        elif w in GENERIC or w in COUNTRY_WORDS:
            pass
        else:
            w = translit(w)
            core.append(w)
            local.append(w)
        i += 1
    return Parsed(core, frozenset(kinds), frozenset(hard), frozenset(quals), frozenset(nums), "".join(local))


@dataclass
class Place:
    id: str
    name: str
    country: str
    lat: float
    lng: float
    by: Optional[str] = None
    prec: Optional[str] = None
    rt: Optional[str] = None
    pid: Optional[str] = None
    stop: bool = False
    card: Optional[str] = None
    p: Parsed = field(init=False)

    def __post_init__(self):
        self.p = parse(self.name)

    @property
    def settlement(self) -> Optional[str]:
        if self.stop or (self.rt or "") in HARD_SETTLEMENT_TYPES or "town" in self.p.hard_kinds:
            return "hard"
        if (self.rt or "") in SOFT_SETTLEMENT_TYPES:
            return "soft"
        return None

    @property
    def loose(self) -> bool:
        return self.by == "llm" or self.prec == "area"


def km(a: Place, b: Place) -> float:
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp, dl = p2 - p1, math.radians(b.lng - a.lng)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(min(1.0, math.sqrt(h)))


# ── relations ─────────────────────────────────────────────────────────────────────────────────────────────────────
NAME_SCORE = {"exact": 1.0, "fuzzy": 0.85, "contain_locality": 0.9, "contain_extra": 0.55, "fuzzy_low": 0.6,
              "kind_only": 0.6}
AMBIGUOUS_NAME = frozenset({"contain_extra", "fuzzy_low", "kind_only"})
AMBIGUOUS_KIND = frozenset({"bare_vs_built", "soft_kind_diff", "heritage_museum"})


def name_relation(a: Parsed, b: Parsed, localities: frozenset) -> tuple[str, float]:
    ca, cb = set(a.core), set(b.core)
    ja, jb = "".join(a.core), "".join(b.core)
    if not ca and not cb:
        return ("kind_only", NAME_SCORE["kind_only"]) if a.kinds and a.kinds == b.kinds else ("other", 0.0)
    if ca == cb or (ja == jb and len(ja) >= 4) or (a.run_local == b.run_local and len(a.run_local) >= 4):
        return "exact", 1.0
    if min(len(ja), len(jb)) >= 4 and difflib.SequenceMatcher(None, ja, jb).ratio() >= 0.85:
        return "fuzzy", NAME_SCORE["fuzzy"]
    small, big = (ca, cb) if len(ca) <= len(cb) else (cb, ca)
    if small and small < big:
        extra = big - small
        return ("contain_locality", 0.9) if extra <= localities else ("contain_extra", 0.55)
    r = difflib.SequenceMatcher(None, ja, jb).ratio() if ja and jb else 0.0
    if min(len(ja), len(jb)) >= 5 and (r >= 0.7 or ja.startswith(jb) or jb.startswith(ja)):
        return "fuzzy_low", NAME_SCORE["fuzzy_low"]
    jac = len(ca & cb) / len(ca | cb) if ca | cb else 0.0
    return "other", round(0.5 * jac, 3)


def kind_relation(a: Place, b: Place) -> tuple[str, Optional[float]]:
    """(reason, score); score None = incompatible (hard keep)."""
    ka, kb = a.p.kinds, b.p.kinds
    if not ka and not kb:
        return "both_bare", 1.0
    if ka == kb:
        return "same_kind", 1.0
    if a.p.hard_kinds == b.p.hard_kinds and a.p.hard_kinds:
        return "soft_kind_diff", 0.6          # the difference comes only from local words
    for bare, other in ((a, b), (b, a)):
        if bare.p.kinds:
            continue
        k = other.p.kinds
        if bare.settlement == "hard":
            return ("same_kind", 1.0) if k == {"town"} else ("town_vs_place", None)
        if k <= NATURAL_BARE:
            return "bare_natural", 0.9
        if bare.by == "geoapify" and (bare.rt or "") in POI_TYPES:
            return "bare_resolved_poi", 0.85
        return "bare_vs_built", 0.5
    for x, y in ((ka, kb), (kb, ka)):
        if y - x == {"museum"} and x and x <= HERITAGE:
            return "heritage_museum", 0.8
    return "different_kinds", None


def radius_km(a: Place, b: Place, krel: str) -> float:
    kinds = a.p.kinds | b.p.kinds
    if not kinds:
        r = 5.0 if "hard" in (a.settlement, b.settlement) else 2.0
    else:
        r = max([RADIUS.get(k, POI_RADIUS) for k in kinds])
    if krel == "bare_vs_built":
        r = max(r, 2.0 if "soft" in (a.settlement, b.settlement) else 1.0)
    return r * (2 if (a.loose or b.loose) else 1)


@dataclass
class Decision:
    decision: str
    score: float
    why: str
    km: float


def decide(a: Place, b: Place, localities: frozenset = frozenset(), embedding_cos: Optional[float] = None) -> Decision:
    d = round(km(a, b), 2)
    if a.country.strip().lower() != b.country.strip().lower():
        return Decision(KEEP, 0.0, "other_country", d)
    if a.p.numbers != b.p.numbers:
        return Decision(KEEP, 0.0, "number_differs", d)
    if a.p.qualifiers != b.p.qualifiers:
        return Decision(KEEP, 0.0, "qualifier_differs", d)
    krel, ks = kind_relation(a, b)
    if ks is None:
        return Decision(KEEP, 0.0, krel + (" (same provider object: geocode defect)" if a.pid and a.pid == b.pid
                                           else ""), d)
    r = radius_km(a, b, krel)
    if d > r:
        return Decision(KEEP, 0.0, f"farther_than_{r:g}km", d)
    if a.pid and a.pid == b.pid:
        return Decision(AUTO, 1.0, "same_provider_object", d)
    if a.card and a.card == b.card:
        return Decision(AUTO, 1.0, "same_place_card", d)
    nrel, ns = name_relation(a.p, b.p, localities)
    weak = all(t in WEAK for t in a.p.core) and all(t in WEAK for t in b.p.core)
    if weak and d > 0.3:
        ns *= 0.85
    ds = 1 - d / r
    ev = 0.0
    if (a.by == b.by == "geoapify" and a.pid and b.pid and a.pid != b.pid
            and (a.rt or "") in POI_TYPES and (b.rt or "") in POI_TYPES):
        ev -= 0.15                             # the geocoder found two different objects
    if embedding_cos is not None:
        ev += max(-0.1, min(0.1, (embedding_cos - 0.8) / 2))
    score = round(ns * ks * (0.6 + 0.4 * ds) + ev, 3)
    why = f"{nrel}/{krel}"
    capped = nrel in AMBIGUOUS_NAME or krel in AMBIGUOUS_KIND
    if krel == "bare_natural" and d > BARE_FAR_KM:
        bare = a if not a.p.kinds else b
        # a bare name a few km from the feature may be the town named after it ("Ha Long" / "Ha Long Bay");
        # only a geocoder POI result for the bare name says it is not a settlement
        if not (bare.by == "geoapify" and (bare.rt or "") in POI_TYPES):
            capped = True
    if score >= HIGH and not capped:
        return Decision(AUTO, score, why, d)
    if score >= LOW and ns >= 0.5:
        return Decision(LLM, score, why, d)
    return Decision(KEEP, score, why, d)


# ── evaluation ────────────────────────────────────────────────────────────────────────────────────────────────────

DEGRADE = {
    # robustness: the same pairs with less metadata than the live rows will have
    "no_ids_no_stops": lambda p: {k: v for k, v in p.items() if k not in ("pid", "stop", "card")},
    "all_model_points": lambda p: {**{k: v for k, v in p.items() if k not in ("pid", "stop", "card", "rt")},
                                   "by": "llm", "prec": "area"},
}


def load(path: str, degrade: Optional[str] = None) -> tuple[dict[str, Place], list[tuple]]:
    data = json.load(open(path, encoding="utf-8"))
    fix = DEGRADE[degrade] if degrade else (lambda p: p)
    places = {pid: Place(pid, **fix(dict(p))) for pid, p in data["places"].items()}
    return places, [tuple(x) for x in data["pairs"]]


def localities_of(places: dict[str, Place]) -> dict[str, frozenset]:
    """Tokens of hard-settlement names per country (production: names of overnight stops / city results)."""
    out: dict[str, set] = {}
    for p in places.values():
        if p.settlement == "hard":
            out.setdefault(p.country.lower(), set()).update(p.p.core)
    return {c: frozenset(s) for c, s in out.items()}


def evaluate(path: str, degrade: Optional[str] = None) -> dict:
    places, pairs = load(path, degrade)
    locs = localities_of(places)
    rows = []
    for a_id, b_id, label, src, note in pairs:
        a, b = places[a_id], places[b_id]
        dec = decide(a, b, locs.get(a.country.lower(), frozenset()))
        rows.append({"a": a.name, "b": b.name, "country": a.country, "label": label, "src": src, "note": note,
                     **dec.__dict__})
    n_merge = sum(r["label"] == "merge" for r in rows)
    n_keep = len(rows) - n_merge
    by = {(lab, dec): sum(1 for r in rows if r["label"] == lab and r["decision"] == dec)
          for lab in ("merge", "keep") for dec in (AUTO, LLM, KEEP)}
    auto_tp, auto_fp = by[("merge", AUTO)], by[("keep", AUTO)]
    llm_m, llm_k = by[("merge", LLM)], by[("keep", LLM)]
    summary = {
        "rule_version": RULE_VERSION, "degrade": degrade, "pairs": len(rows), "merge": n_merge, "keep": n_keep,
        "matrix": {f"{lab}->{dec}": n for (lab, dec), n in by.items()},
        "rules_only": {"precision": round(auto_tp / (auto_tp + auto_fp), 3) if auto_tp + auto_fp else None,
                       "recall": round(auto_tp / n_merge, 3), "false_merges": auto_fp},
        "with_llm_if_llm_is_right": {"recall": round((auto_tp + llm_m) / n_merge, 3), "false_merges": auto_fp,
                                     "llm_calls": llm_m + llm_k},
        "with_llm_worst_case": {"recall": round(auto_tp / n_merge, 3), "false_merges": auto_fp + llm_k,
                                "precision": round((auto_tp + llm_m) / (auto_tp + llm_m + auto_fp + llm_k), 3)},
        "keep_correct_by_rules": round(by[("keep", KEEP)] / n_keep, 3),
        "by_src": {s: {"pairs": sum(r["src"] == s for r in rows),
                       "merge_auto": sum(r["src"] == s and r["label"] == "merge" and r["decision"] == AUTO
                                         for r in rows),
                       "merge": sum(r["src"] == s and r["label"] == "merge" for r in rows),
                       "false_merge": sum(r["src"] == s and r["label"] == "keep" and r["decision"] == AUTO
                                          for r in rows)}
                   for s in sorted({r["src"] for r in rows})},
    }
    return {"summary": summary, "rows": rows}


def main(argv: list[str]) -> int:
    degrade = next((a.split("=", 1)[1] for a in argv if a.startswith("--degrade=")), None)
    paths = [a for a in argv[1:] if not a.startswith("--")]
    out = evaluate(paths[0] if paths else "pairs.json", degrade)
    print(json.dumps(out["summary"], indent=2))
    only_misses = "--misses" in argv
    print()
    print(f"{'label':5} {'decision':10} {'score':>5} {'km':>6}  pair  [why]")
    for r in sorted(out["rows"], key=lambda r: (r["label"], r["decision"], -r["score"])):
        right = (r["label"] == "merge") == (r["decision"] == AUTO)
        if only_misses and right:
            continue
        print(f"{r['label']:5} {r['decision']:10} {r['score']:5.2f} {r['km']:6.2f}  {r['a']} | {r['b']} "
              f"({r['country']})  [{r['why']}]  {r['src']}")
    return 0 if out["summary"]["rules_only"]["false_merges"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
