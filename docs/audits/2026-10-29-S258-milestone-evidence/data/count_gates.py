"""Count the CIS quality gate registry over time (M2a: no new gates during the S246 freeze). Read-only, git only."""
import subprocess, sys, json, re
import yaml

REPO = sys.argv[1]
def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True).stdout

def at_date(d):
    return git("rev-list", "-1", f"--before={d}T23:59:59+07:00", "origin/main").strip()

def registry(rev):
    raw = git("show", f"{rev}:services/quality/taxonomy.yaml")
    if not raw:
        return None
    t = yaml.safe_load(raw)
    g = t.get("gates") or {}
    kinds = {}
    for n, v in g.items():
        k = v.get("kind", "?") + ("/retired" if v.get("retired") else "")
        kinds[k] = kinds.get(k, 0) + 1
    dets = [d for c in t.get("classes", []) for d in (c.get("detectors") or [])]
    enforce = sorted({d["ref"] for d in dets if d.get("mode") == "enforce"})
    return {"gates_total": len(g), "by_kind": kinds,
            "active_gates": sorted(n for n, v in g.items() if v.get("kind") == "gate" and not v.get("retired")),
            "classes": len(t.get("classes", [])), "detectors": len(dets), "enforce_detector_refs": len(enforce),
            "enforce_refs": enforce}

main = git("rev-parse", "origin/main").strip()
main_reg = registry(main)
gate_names = main_reg["active_gates"]

def code_presence(rev):
    present = []
    for n in gate_names:
        out = git("grep", "-l", "-F", f'"{n}"', rev, "--", "services", "api")
        # the YAML registry is left out; registry.py (the Python constants since #982) counts as code
        files = [l for l in out.splitlines() if not l.endswith(".yaml")]
        if files:
            present.append(n)
    return present

points = [("2026-10-01", "4 weeks before today"), ("2026-10-21", "freeze start (S246)"),
          ("2026-10-24", "day before the registry"), ("2026-10-25", "registry created (#982, #992)"),
          ("2026-10-29", "today (origin/main)")]
res = {"main": main, "points": []}
for d, why in points:
    rev = main if d == "2026-10-29" else at_date(d)
    reg = registry(rev)
    pres = code_presence(rev)
    res["points"].append({"date": d, "why": why, "rev": rev[:8],
                          "registry": None if reg is None else {k: v for k, v in reg.items() if k not in ("active_gates", "enforce_refs")},
                          "main_active_gates_used_in_code": len(pres),
                          "main_active_gates_missing_in_code": sorted(set(gate_names) - set(pres))})
# registry history, commit by commit
hist = []
for line in git("log", "--format=%h %ad %s", "--date=short", "origin/main", "--", "services/quality/taxonomy.yaml").splitlines():
    h = line.split()[0]
    reg = registry(h)
    hist.append({"commit": line[:110], "gates_total": reg["gates_total"], "by_kind": reg["by_kind"],
                 "active_gates": len(reg["active_gates"]), "enforce_detector_refs": reg["enforce_detector_refs"]})
res["registry_history"] = hist
res["main_active_gate_names"] = gate_names
print(json.dumps(res, indent=1))
