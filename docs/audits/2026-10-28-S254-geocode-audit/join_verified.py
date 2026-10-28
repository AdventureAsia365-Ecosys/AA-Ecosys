#!/usr/bin/env python3
"""Join agent verdicts (verified_raw.psv) to shard rows; write verified.json + stats."""
import json, re, unicodedata, math, random
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
CODES = {"C":"correct","TC":"too_coarse","WP":"wrong_place","WC":"wrong_country","NP":"not_a_place","U":"unsure"}
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+"," ",s).strip()
rows=[]
for i in range(10):
    for r in json.load(open(HERE/f"shard-{i}.json")):
        r["_shard"]=i; rows.append(r)
used=set(); out=[]; unmatched=[]
for line in open(HERE/"verified_raw.psv"):
    line=line.rstrip("\n")
    if not line: continue
    nm,tp,code,exp,note=line.split("|",4)
    cands=[k for k,r in enumerate(rows) if k not in used and r["name_norm"]==nm and norm(r["tour_name"]).startswith(norm(tp))]
    if not cands:
        cands=[k for k,r in enumerate(rows) if k not in used and r["name_norm"]==nm]
    if not cands: unmatched.append((nm,tp)); continue
    k=cands[0]; used.add(k); r=rows[k]
    out.append({"name_norm":nm,"display_name":r.get("display_name"),"tour_name":r["tour_name"],"tour_country":r.get("country"),
        "country_iso2":r.get("country_iso2"),"lat":r.get("lat"),"lng":r.get("lng"),"geo_precision":r.get("geo_precision"),
        "geocoder_provider":r.get("geocoder_provider"),"located_by":r.get("located_by"),"locality":r.get("locality"),
        "flags":r.get("flags",[]),"detail":r.get("detail",{}),"sample":bool(r.get("sample")),"shard":r["_shard"],
        "verdict":CODES[code],"expected":exp or None,"note":note})
missing=[ (r["name_norm"],r["tour_name"]) for k,r in enumerate(rows) if k not in used]
json.dump(out,open(HERE/"verified.json","w"),ensure_ascii=False,indent=1)
print("verified",len(out),"unmatched",len(unmatched),unmatched[:10],"shard rows not verified",len(missing))
for m in missing: print("  MISSING",m)
