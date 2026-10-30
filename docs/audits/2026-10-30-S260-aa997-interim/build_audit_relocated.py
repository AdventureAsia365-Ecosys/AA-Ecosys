#!/usr/bin/env python3
"""Build audit_relocated.py from audit_relocated.src.py: embed the S254 verified.json (600 rows) exactly as the S257
interim audit builder does (docs/audits/2026-10-29-S257-aa997-interim/build_aa997_interim_audit.py, row())."""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
S257 = ROOT / "docs/audits/2026-10-29-S257-aa997-interim/build_aa997_interim_audit.py"
SRC = ROOT / "docs/audits/2026-10-28-S254-geocode-audit/verified.json"

spec = importlib.util.spec_from_file_location("s257_builder", S257)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

rows = [mod.row(r) for r in json.load(open(SRC))]
blob = json.dumps(rows, ensure_ascii=True, separators=(",", ":"))
src = (HERE / "audit_relocated.src.py").read_text()
assert src.count('"__VERIFIED__"') == 1
out = src.replace('"__VERIFIED__"', repr(blob))
(HERE / "audit_relocated.py").write_text(out)
print(f"rows={len(rows)} blob={len(blob)} B script={len(out)} B")
