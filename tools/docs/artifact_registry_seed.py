"""One-off seed (S271) for docs/artifacts/registry.json: every claude.ai artifact link cited in the root repo, with the
files that cite it and the link text / line context, merged with titles from an `Artifact list` export (JSON lines
{"url","title"} in the file given as argv[1]). Prints JSON; the curated registry is edited by hand afterwards.

Usage: python3 tools/docs/artifact_registry_seed.py titles.jsonl > /tmp/seed.json
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
URL = re.compile(r"https://claude\.ai/artifact/([A-Za-z0-9]{20,24})")
MDLINK = re.compile(r"\[([^\]]{3,120})\]\(https://claude\.ai/artifact/([A-Za-z0-9]{20,24})")


def main():
    titles = {}
    if len(sys.argv) > 1:
        for line in open(sys.argv[1], encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                titles[URL.search(r["url"]).group(1)] = r["title"]
    found = {}
    for p in sorted(ROOT.glob("docs/**/*.md")) + sorted(ROOT.glob("skill/**/*.md")):
        if "/data/" in str(p):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            for m in URL.finditer(line):
                aid = m.group(1)
                e = found.setdefault(aid, {"id": aid, "cited_in": [], "context": None})
                rel = f"{p.relative_to(ROOT)}:{i}"
                if len(e["cited_in"]) < 4:
                    e["cited_in"].append(rel)
                ml = [x for x in MDLINK.finditer(line) if x.group(2) == aid]
                if ml and not e["context"]:
                    e["context"] = ml[0].group(1)
                elif not e["context"]:
                    e["context"] = re.sub(r"\s+", " ", line.strip())[:140]
    for aid, t in titles.items():
        found.setdefault(aid, {"id": aid, "cited_in": [], "context": None})["title"] = t
    out = sorted(found.values(), key=lambda e: (-len(e["cited_in"]), e["id"]))
    for e in out:
        e["url"] = f"https://claude.ai/artifact/{e['id']}"
        e.setdefault("title", None)
    print(json.dumps(out, ensure_ascii=False, indent=1))


main()
