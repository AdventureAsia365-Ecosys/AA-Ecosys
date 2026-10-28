#!/usr/bin/env python3
"""AA-850: static code-reference scan for every table/view in db-schema-reference.md.

Reads the generated reference (objects, ~rows, size, owner, activity counters), then every
tracked text file of origin/main of the 5 repos (+ root origin/master for docs only), tokenises
identifiers and records where each object name appears, split by file category.
Output: scan.json next to this script. Read-only, local only.
"""
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("/home/nghiep/projects/AA-Ecosys")
REF = ROOT / "docs/architecture/db-schema-reference.md"
OUT = Path(__file__).with_name("scan.json")

REPOS = {
    "CIS": ("apps/AA-CIS-App", "origin/main"),
    "Booking": ("apps/AA-Booking", "origin/main"),
    "TripPlanner": ("apps/AA-TripPlanner-Web", "origin/main"),
    "Partner": ("apps/AA-Partner", "origin/main"),
    "Infra": ("infra/AA-CIS-Infra", "origin/main"),
}

SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".zip", ".gz", ".pdf", ".woff",
            ".woff2", ".ttf", ".lock", ".xlsx", ".xls", ".docx", ".pptx", ".mp4", ".pyc", ".bin", ".tfstate"}
SKIP_NAMES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock", "poetry.lock"}


def category(repo: str, path: str) -> str:
    p = path.lower()
    if re.search(r"(^|/)(migrations|replay_baseline)/", p) and p.endswith(".sql"):
        return "migration"
    if p.endswith(".md") or p.startswith("docs/") or "/docs/" in p:
        return "docs"
    if re.search(r"(^|/)(tests?|e2e|__tests__)/", p) or re.search(r"(^|/)test_[^/]+\.py$", p) or ".test." in p or ".spec." in p:
        return "test"
    if repo == "CIS" and p.startswith("portal/"):
        return "frozen"  # AA-979: frozen copy, not deployed
    if re.search(r"(^|/)(scripts|tools)/", p) or p.startswith("db/scripts/"):
        return "script"
    if repo == "Infra" and p.startswith("db/") and p.endswith(".py"):
        return "infra-tool"  # schema dump, drift, gates
    if p.startswith(".github/") or p.startswith(".claude/") or p.startswith(".kiro/") or p.startswith(".agents/"):
        return "ci-agent"
    return "runtime"


def parse_reference():
    objs = {}
    cur_schema = None
    text = REF.read_text()
    head = re.compile(r"^### `([a-z0-9_]+)\.([a-z0-9_]+)` \(([^)]*)\)")
    for line in text.splitlines():
        m = head.match(line)
        if m:
            schema, name, meta = m.groups()
            kind = meta.split(",")[0].strip()
            rows = None
            rm = re.search(r"~(\d+) rows", meta)
            if rm:
                rows = int(rm.group(1))
            size = meta.split(",")[-1].strip() if "," in meta else ""
            cur = objs[f"{schema}.{name}"] = {"schema": schema, "name": name, "kind": kind, "rows": rows,
                                              "size": size, "owner": None, "rls": False}
            continue
        if line.startswith("- owner `") and objs:
            last = list(objs.values())[-1]
            if last["owner"] is None:
                last["owner"] = line.split("`")[1]
                last["rls"] = "RLS on" in line
    # activity
    sec = text.split("## Table activity", 1)[1].split("\n## ", 1)[0]
    for line in sec.splitlines():
        m = re.match(r"^\| `([a-z0-9_]+\.[a-z0-9_]+)` \| ([^|]*)\| ([^|]*)\| ([^|]*)\| ([^|]*)\| ([^|]*)\| ([^|]*)\| ([^|]*)\|", line)
        if m and m.group(1) in objs:
            fq, rows, size, seq, idx, iud, dead, vac = [g.strip() for g in m.groups()]
            ins, upd, dele = [int(x.strip()) for x in iud.split("/")]
            objs[fq].update({"seq_scans": int(seq or 0), "idx_scans": int(idx or 0) if idx else 0,
                             "ins": ins, "upd": upd, "del": dele, "last_autovacuum": vac})
    # unused indexes / fk not needed here
    return objs


def git_files(repo_dir: Path, ref: str):
    out = subprocess.run(["git", "-C", str(repo_dir), "ls-tree", "-r", "-l", ref], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        _, typ, sha, size = meta.split()
        if typ != "blob" or size == "-" or int(size) > 2_000_000:
            continue
        name = path.rsplit("/", 1)[-1]
        ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
        if ext in SKIP_EXT or name in SKIP_NAMES or "/dist/" in f"/{path}" or path.startswith("dist/"):
            continue
        yield path, sha


def cat_blobs(repo_dir: Path, items):
    proc = subprocess.Popen(["git", "-C", str(repo_dir), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for path, sha in items:
        proc.stdin.write((sha + "\n").encode())
        proc.stdin.flush()
        header = proc.stdout.readline().split()
        size = int(header[2])
        data = proc.stdout.read(size)
        proc.stdout.read(1)
        if b"\x00" in data[:8000]:
            continue
        yield path, data.decode("utf-8", errors="replace")
    proc.stdin.close()
    proc.wait()


WRITE_RE = r"(?:insert\s+into|update|delete\s+from|truncate(?:\s+table)?|copy|merge\s+into|upsert)\s+(?:only\s+)?"


def main():
    objs = parse_reference()
    names = {o["name"] for o in objs.values()}
    fq_names = set(objs)
    by_name = defaultdict(list)
    for fq, o in objs.items():
        by_name[o["name"]].append(fq)
    hits = {fq: {"qualified": defaultdict(list), "bare": defaultdict(list), "writes": []} for fq in objs}
    tok = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\"?\.\"?[A-Za-z_][A-Za-z0-9_]*)?")
    for repo, (rel, ref) in REPOS.items():
        rdir = ROOT / rel
        files = list(git_files(rdir, ref))
        for path, text in cat_blobs(rdir, files):
            cat = category(repo, path)
            low = text.lower()
            toks = set(t.replace('"', "") for t in tok.findall(low))
            found_fq = toks & fq_names
            bare = set()
            for t in toks:
                if "." in t:
                    a, b = t.split(".", 1)
                    if b in names:
                        bare.add(b)
                    if a in names:
                        bare.add(a)
                elif t in names:
                    bare.add(t)
            for fq in found_fq:
                hits[fq]["qualified"][f"{repo}:{cat}"].append(path)
                if cat in ("runtime", "script", "frozen", "infra-tool") and re.search(WRITE_RE + re.escape(fq) + r"\b", low):
                    hits[fq]["writes"].append(f"{repo}:{path}")
            for b in bare:
                for fq in by_name[b]:
                    if fq not in found_fq:
                        hits[fq]["bare"][f"{repo}:{cat}"].append(path)
        print(repo, len(files), file=sys.stderr)
    for fq in objs:
        objs[fq]["hits"] = {k: {kk: sorted(set(vv)) for kk, vv in v.items()} if isinstance(v, dict) else sorted(set(v))
                            for k, v in hits[fq].items()}
    OUT.write_text(json.dumps(objs, indent=1, sort_keys=True))
    print("wrote", OUT, len(objs), file=sys.stderr)


if __name__ == "__main__":
    main()
