#!/usr/bin/env python3
"""Build aa997_interim_audit.py: embed the S254 verified.json (600 rows) as a compact JSON list into the .src.py.

Per row: name_norm, country_norm, locality_norm, tour-name prefix, S254 point + ISO, verdict code, expected points
(every "lat, lng" pair in `expected`; "same point/coords" = the S254 point), expected ISO (HK / MO ISO errors),
random-sample flag, flagged flag, S254 located_by (g/l/m), site-type name (S254 tolerance 4 km instead of 5 km).
"""
import json
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / "docs/audits/2026-10-28-S254-geocode-audit/verified.json"
CODE = {"correct": "C", "too_coarse": "TC", "wrong_place": "WP", "wrong_country": "WC", "not_a_place": "NP",
        "unsure": "U"}
LB = {"geoapify": "g", "llm": "l", "mapbox": "m"}
PAIR = re.compile(r"(-?\d{1,2}\.\d+)\s*°?\s*[NS]?\s*,\s*(-?\d{1,3}\.\d+)")
SITE = set(("temple monastery museum hotel station bridge waterfall falls fort palace pagoda stupa shrine church "
            "mosque cathedral gompa dzong tomb mausoleum tower airport cave caves lodge resort zoo monument memorial "
            "castle observatory gallery statue mandir gurudwara haveli stepwell baori mahal masjid minar chorten "
            "lhakhang goemba dargah kovil brewery winery dam lighthouse pier jetty wat gate hut").split())


def norm(s):
    """services/places/names.name_norm, close enough for ASCII country / locality strings."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().replace("'", "")
    s = " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())
    t = re.sub(r"^((the|a|an) )+", "", s)
    return t or s


def row(r):
    exp_txt = r.get("expected") or ""
    exp = [[float(a), float(b)] for a, b in PAIR.findall(exp_txt) if -90 <= float(a) <= 90 and -180 <= float(b) <= 180]
    if not exp and re.search(r"\bsame (point|coords)", exp_txt, re.I):
        exp = [[r["lat"], r["lng"]]]
    m = re.search(r"\b(HK|MO)\b", exp_txt) if r["verdict"] == "wrong_country" else None
    site = r["verdict"] == "too_coarse" or "precision_area_site" in r["flags"] or bool(
        set(re.findall(r"[a-z]+", r["name_norm"])) & SITE)
    return [r["name_norm"], norm(r["tour_country"]), norm(r.get("locality")), (r["tour_name"] or "")[:30],
            round(r["lat"], 6), round(r["lng"], 6), r["country_iso2"], CODE[r["verdict"]], exp,
            m.group(1) if m else None, int(bool(r["sample"])), int(bool(r["flags"])), LB[r["located_by"]], int(site)]


def main():
    v = json.load(open(SRC))
    rows = [row(r) for r in v]
    blob = json.dumps(rows, ensure_ascii=True, separators=(",", ":"))
    src = (HERE / "aa997_interim_audit.src.py").read_text()
    assert src.count('"__VERIFIED__"') == 1
    out = src.replace('"__VERIFIED__"', repr(blob))
    (HERE / "aa997_interim_audit.py").write_text(out)
    no_ref = sum(1 for r in rows if r[7] in ("TC", "WP", "WC") and not r[8])
    print(f"rows={len(rows)} blob={len(blob)} B script={len(out)} B errors_without_expected_point={no_ref}"
          f" iso_fix_rows={sum(1 for r in rows if r[9])} site={sum(r[13] for r in rows)}")


if __name__ == "__main__":
    main()
