"""AA-865 (S245) — $0 counterfactual replay of the F9 sticky-pass carry (CIS fix branch
`fix/f9-sticky-carry-over-repaired-sentences`) over the pooled retry-added cases in pool.json.

No DB, no AWS, no LLM call. It imports the app's own helpers (`_f9_key`, `_f9_deletion_only`, `_f9_antecedent_kept`)
from a CIS checkout that has the fix, so the replay uses the shipped rule, not a copy of it.

    PYTHONPATH=<CIS checkout with the fix> <CIS venv>/bin/python script/s245_f9_counterfactual.py pool.json

For every F9_cta_fact item of every retry-added case it needs four sentences: the flagged sentence at attempt k
(S'), the sentence before it (P'), and the attempt k-1 versions of both (S, P). pool.json has S' and P' for every
item. S and P come from the stored base text when the case has it (S234 k=3 cases: exact comparison). For the k=2
cases the attempt-1 text is not stored, so S and P are set by READING each case (REVIEWED below): a sentence that is
not a repair target is unchanged (a sentence repair edits only its items), and a repaired one is matched to its
repair-target quote. The reading, with its evidence, is in README §5.

Rules replayed, per item (the base verdict must have passed F9, as it did in every F9 case here):
- current: sticky iff the current key is unchanged: S' == S and (no referent opener or P' == P).
- fixed:   current, or the AA-865 carry: S' is a deletion-only edit of S and the referent opener kept its antecedent.
A case is removed when every added gate is removed: all its F9 items sticky and no other gate added (sticky never
touches F17 / F18). Variant `fixed_plus_767`: also removes the two r6 F17 adds that the S239 diagnosis probe showed
the CIS #767 F17 post-check (already on main) removes (a3d82ff1, 263e5a5a).
"""
import json
import math
import sys

from services.acp_content_writing.quality_gates import (_REFERENT_OPEN_RE, _cmp_fold, _f9_antecedent_kept,
                                                        _f9_deletion_only, _fold)

Z95 = 1.959963984540054
TARGET = 0.08
SAME = "same"  # S == S' / P == P'
UNKNOWN = None  # changed, previous version not known: never sticky
POST_767_F17 = {"a3d82ff1", "263e5a5a"}

# (piece id prefix, item index) -> (S at the base attempt, P at the base attempt, class, note). Read from the case
# evidence in pool.json, the repair targets and the S239 r6 diagnosis; see README §5.
REVIEWED = {
    ("bb776a54", 0): (SAME, SAME, "C2", "base text stored: unchanged, previous sentence unchanged"),
    ("71ad6b1f", 0): (UNKNOWN, SAME, "C1", "F17 flags the same sentence at k and is deterministic, so the sentence "
                                           "changed: the repair added 'before the afternoon's next move'"),
    ("9594430b", 0): (SAME, SAME, "C2", "base text stored: unchanged"),
    ("5939df86", 0): (SAME, SAME, "C2", "base text stored: unchanged"),
    ("5939df86", 1): (SAME, SAME, "C2", "base text stored: unchanged"),
    ("5939df86", 2): (SAME, SAME, "C2", "base text stored: unchanged (the F17 target, left as it was)"),
    ("ccb0843c", 0): (SAME, SAME, "C2", "not a repair target, previous sentence not a target: unchanged"),
    ("ccb0843c", 1): ("The journey through this part of northern Mongolia closes with a single further moment: the "
                      "ruins of an ancient monastery, destroyed during the political purges of 1937, which stand as a "
                      "quiet register of what this region has also lost.", SAME, "C2",
                      "the F17 thin-coda target rewritten; the location claim was in the passed sentence, but "
                      "'within' is a new word"),
    ("17125e0c", 0): (SAME, "Swim time at Kuang Si Falls on Day 2 isn't a gap in the schedule. It's the schedule.",
                      "C2", "unchanged; the hook before it was repaired; no referent opener (r6 diagnosis R3)"),
    ("a2133050", 0): ("Before leaving this part of northern Mongolia, the route also passes the ruins of an ancient "
                      "monastery destroyed during the political purges of 1937: a single, spare reminder that the "
                      "region's layers of cultural memory extend well beyond its landscape.", SAME, "C2",
                      "F17 repair cut the added clause: deletion only (r6 diagnosis R4)"),
    ("31b91e79", 0): ("A lake this large, this remote, this ecologically distinct, exerts a gravitational pull on "
                      "everything around it: the climate, the soil, the species, and the human communities who have "
                      "organised their lives around its shores and the forests to its north.", SAME, "C2",
                      "F15 style repair made a figure literal ('shapes', 'sustained'): same claim, new words "
                      "(borderline C1)"),
    ("3aa22704", 0): (SAME, "Guru Rinpoche is said to have flown to this cliff on the back of a tigress in the 8th "
                            "century, and that founding story still shapes why Paro Taktsang matters.", "C2",
                      "unchanged; 'The' opener keyed on the hook, which the F14/F15 repair rewrote"),
    ("4dd0e729", 0): ("It is a practical overnight stop that also gives families time to rest before the longer drive "
                      "north on day four.", SAME, "C1",
                      "the F17 target rewritten into a lunch stop the source does not give (source: overnight)"),
}
NON_F9_CLASS = {
    "71ad6b1f": ("C1", "F17: the repair added 'before the afternoon'"),
    "dde74641": ("C1", "F17: the F9 repair added 'the first evening'"),
    "a3d82ff1": ("C1", "F17: the F9 repair added 'the afternoon' (r6 diagnosis R1)"),
    "263e5a5a": ("C1", "F17: the F15 repair added 'The afternoon' (r6 diagnosis R2)"),
    "ebfff6f3": ("C1", "F18: the full rewrite added 'Most travellers'"),
}
POOLS = {
    "primary_r5_r7": ["S235_r5", "S239_r6", "S239_r7"],
    "extended_with_aa768": ["S235_r5", "S239_r6", "S239_r7", "S239_aa768_pre761", "S239_r6_aa768", "S239_r7_aa768"],
    "current_code_r7": ["S239_r7", "S239_r7_aa768"],
    "extended_plus_natural": ["S235_r5", "S239_r6", "S239_r7", "S239_aa768_pre761", "S239_r6_aa768",
                              "S239_r7_aa768", "natural_post_r7"],
    "reference_S234_r4": ["S234_r4"],
}


def wilson(k: int, n: int) -> dict:
    p = k / n
    d = 1 + Z95 * Z95 / n
    c = (p + Z95 * Z95 / (2 * n)) / d
    h = Z95 * math.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / d
    return {"num": k, "den": n, "rate": round(p, 4), "ci95": [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)],
            "le_target": p <= TARGET}


def referent(sentence: str) -> bool:
    return bool(_REFERENT_OPEN_RE.match(" ".join(_fold(sentence).split())))


def replay_item(case: dict, idx: int, item: dict) -> dict:
    s_new = (item.get("in_attempt_k") or {}).get("sentences") or [item.get("sentence")]
    if len(s_new) != 1:
        return {"current": False, "fixed": False, "why": "two-sentence quote (C3): not replayed"}
    s_new, p_new = s_new[0], (item.get("in_attempt_k") or {}).get("prev_sentence")
    s_old, p_old, cls, note = REVIEWED[(case["piece_id"][:8], idx)]
    s_old = s_new if s_old == SAME else s_old
    p_old = p_new if p_old == SAME else p_old
    if not case.get("f9_passed_at_base") or item.get("flagged_by_f9_at_base"):
        return {"class": cls, "note": note, "current": False, "fixed": False, "why": "never passed at the base"}
    if s_old is UNKNOWN:
        return {"class": cls, "note": note, "current": False, "fixed": False, "why": "changed; old version unknown"}
    unchanged = _cmp_fold(s_old) == _cmp_fold(s_new)
    current = unchanged and (not referent(s_new) or _cmp_fold(p_old) == _cmp_fold(p_new))
    carry = _f9_deletion_only(s_old, s_new) and _f9_antecedent_kept(s_new, p_old, p_new)
    return {"class": cls, "note": note, "current": current, "fixed": current or carry,
            "deletion_only": _f9_deletion_only(s_old, s_new), "antecedent_kept": _f9_antecedent_kept(s_new, p_old, p_new)}


def main(path: str) -> None:
    pool = json.load(open(path))
    rows = []
    for case in pool["cases"]:
        pid = case["piece_id"][:8]
        items = case["added"].get("F9_cta_fact") or []
        replays = [replay_item(case, i, it) for i, it in enumerate(items)]
        others = [g for g in case["added_gates"] if g != "F9_cta_fact"]
        row = {"set": case["set"], "piece": pid, "k": case["k"], "mode": case["mode"], "added": case["added_gates"],
               "f9_items": replays, "other_gates": others,
               "class": sorted({r["class"] for r in replays} | ({NON_F9_CLASS[pid][0]} if others else set())),
               "removed": {}}
        for rule in ("current", "fixed"):
            row["removed"][rule] = not others and bool(replays) and all(r[rule] for r in replays)
        row["removed"]["fixed_plus_767"] = row["removed"]["fixed"] or (
            pid in POST_767_F17 and others == ["F17_trip_fact"] and not replays)
        rows.append(row)
    out = {"cases": rows, "pools": {}}
    for name, sets in POOLS.items():
        den = pool["pools"][name]["retries"]
        in_pool = [r for r in rows if r["set"] in sets]
        assert len(in_pool) == pool["pools"][name]["any_blocking_added"]["num"], name
        res = {"observed": wilson(len(in_pool), den)}
        for rule in ("current", "fixed", "fixed_plus_767"):
            left = [r for r in in_pool if not r["removed"][rule]]
            res[rule] = wilson(len(left), den)
            res[rule + "_f9"] = wilson(sum("F9_cta_fact" in r["added"] and not r["removed"][rule] for r in in_pool), den)
            res[rule + "_left"] = [r["piece"] for r in left]
        out["pools"][name] = res
    classes = {}
    for r in rows:
        for c in r["class"]:
            classes.setdefault(c, []).append(r["piece"])
    out["classes"] = classes
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "pool.json")
