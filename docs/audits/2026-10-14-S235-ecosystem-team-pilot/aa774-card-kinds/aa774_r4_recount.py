"""AA-774 offline recount — $0, no DB, no AWS. Run locally after aa774_kinds_probe.py.

Reads the 20 S234 r4 pieces (.tmp-session/s234/pieces_r4.json — each carries the seed its writer got)
and the probe's JSON (its `r4_bullet_kinds` map), and reports per piece and per seed block how many
"Place background" bullets the AA-774 filter removes and whether the block's thin tag
(moment_fact_count < THIN_FACTS) would change.

    python3 aa774_r4_recount.py probe_out.json            # kinds from the probe (authoritative)
    python3 aa774_r4_recount.py --heuristic               # no probe yet: regex guess of visiting/practical

A bullet whose kind is null in the probe (fact no longer on any card, e.g. merged away after r4) is
reported as `unknown` and counted as kept.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIECES = HERE.parent / "s234" / "pieces_r4.json"
THIN_FACTS = 3
DROP = {"visiting", "practical"}
_SOURCE_RE = re.compile(r"Source itinerary: (.*)$", re.M)
_SENTS_RE = re.compile(r"(?<=[.!?])\s+(?=\S)")
# Heuristic only (no probe): lines that read as visiting/practical.
_PRACTICAL_RE = re.compile(r"^(Visitors|Access|The hike|Trails lead|The road from|Summers are short|The region experiences"
                           r"|Water levels|Winters are severe)|\b(permit|must leave|required to wear|can swim"
                           r"|should be prepared|reached from)\b", re.I)


def fold(s):
    t = unicodedata.normalize("NFKD", s or "")
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).lower().split())


def moment_fact_count(block, drop=frozenset()):
    n = sum(len([x for x in _SENTS_RE.split(m.group(1).strip()) if x.strip()]) for m in _SOURCE_RE.finditer(block))
    in_bg = False
    for line in block.splitlines():
        if line.startswith("Place background"):
            in_bg = True
            continue
        if in_bg and line.startswith("- "):
            n += line[2:].strip() not in drop
        else:
            in_bg = False
    return n


def bullets(block):
    out, in_bg = [], False
    for line in block.splitlines():
        if line.startswith("Place background"):
            in_bg = True
            continue
        if in_bg and line.startswith("- "):
            out.append(line[2:].strip())
        else:
            in_bg = False
    return out


def main():
    heuristic = "--heuristic" in sys.argv
    kinds = {}
    if not heuristic:
        probe = json.loads(Path(sys.argv[1]).read_text())
        kinds = {fold(k)[:72]: v for k, v in probe["r4_bullet_kinds"].items()}

    def kind(b):
        if heuristic:
            return "practical?" if _PRACTICAL_RE.search(b) else "writer?"
        return kinds.get(fold(b)[:72]) or "unknown"

    pieces = json.loads(PIECES.read_text())
    report, seeds_done = [], {}
    for p in pieces:
        if p["seed"] in seeds_done:
            report.append(dict(seeds_done[p["seed"]], piece_id=p["piece_id"], tenant=p["tenant"],
                               channel=p["channel"], status=p["status"]))
            continue
        blocks = []
        for block in re.split(r"\n\s*\n", p["seed"]):
            bs = bullets(block)
            drop = {b for b in bs if kind(b).rstrip("?") in DROP}
            nb, na = moment_fact_count(block), moment_fact_count(block, frozenset(drop))
            blocks.append({"label": block.strip().split("\n", 1)[0][:60], "facts_before": nb, "facts_after": na,
                           "thin_before": nb < THIN_FACTS, "thin_after": na < THIN_FACTS,
                           "removed": sorted(b[:100] for b in drop),
                           "unknown": sum(kind(b) == "unknown" for b in bs)})
        row = {"blocks": blocks, "removed": sum(len(b["removed"]) for b in blocks),
               "thin_changed": sum(b["thin_before"] != b["thin_after"] for b in blocks)}
        seeds_done[p["seed"]] = row
        report.append(dict(row, piece_id=p["piece_id"], tenant=p["tenant"], channel=p["channel"],
                           status=p["status"]))
    summary = {"mode": "heuristic" if heuristic else "probe", "pieces": len(report),
               "distinct_seeds": len(seeds_done),
               "bullets_removed_per_distinct_seed": [r["removed"] for r in seeds_done.values()],
               "pieces_with_thin_change": sum(1 for r in report if r["thin_changed"]),
               "removed_total_over_pieces": sum(r["removed"] for r in report)}
    print(json.dumps({"summary": summary, "pieces": report}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
