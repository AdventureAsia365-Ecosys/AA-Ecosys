#!/usr/bin/env python3
"""Build flags-summary.json + tables for the S254 geocode audit README (stdlib, read-only)."""
import json, math
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
OUT = Path("/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-28-S254-geocode-audit")
P = json.load(open(HERE/"place_names.json")); res=[r for r in P if r.get("status")=="resolved"]
F = json.load(open(HERE/"flags.json")); v = json.load(open(HERE/"verified.json"))
T=len(res); NF=sum(1 for f in F if f["flags"]); NU=T-NF
def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)); return [round((c-h)/d,3),round((c+h)/d,3)]
ERR={"too_coarse","wrong_place","wrong_country","not_a_place"}
S=[r for r in v if r["sample"]]; FL=[r for r in v if r["flags"]]
def vc(g): return dict(Counter(r["verdict"] for r in g))
def rate(g):
    n=len(g); c=sum(r["verdict"]=="correct" for r in g); e=sum(r["verdict"] in ERR for r in g)
    return {"n":n,"correct":c,"errors":e,"unsure":n-c-e,"correct_rate":round(c/n,3),"correct_95ci":wilson(c,n),"error_rate":round(e/n,3),"error_95ci":wilson(e,n)}
# stratified estimates
def strat(keyf):
    N=Counter(keyf(r,f) for r,f in zip(res,F)); est={"c":0,"e":0}; var={"c":0,"e":0}; cells={}
    for k,Nk in N.items():
        g=[r for r in v if keyf_v(keyf,r)==k]; t=len(g); W=Nk/T
        for m,pred in (("c",lambda r:r["verdict"]=="correct"),("e",lambda r:r["verdict"] in ERR)):
            p=sum(map(pred,g))/t; est[m]+=W*p; var[m]+=W*W*p*(1-p)/t*(1-t/Nk)
        cells[str(k)]={"population":Nk,"verified":t}
    ci=lambda m:[round(est[m]-1.96*math.sqrt(var[m]),3),round(est[m]+1.96*math.sqrt(var[m]),3)]
    return {"correct":round(est["c"],3),"correct_95ci":ci("c"),"error":round(est["e"],3),"error_95ci":ci("e"),"cells":cells}
def keyf_v(keyf,r): return keyf(r,r)
by_flag=lambda r,f: bool(f["flags"])
by_prov=lambda r,f: (r["located_by"], bool(f["flags"]))
est_flag=strat(by_flag); est_prov=strat(by_prov)
cs=Counter(r["verdict"] for r in S); cf=Counter(r["verdict"] for r in FL)
projected={k: round(NU*cs[k]/len(S)+NF*cf[k]/len(FL)) for k in ["correct","wrong_place","too_coarse","not_a_place","wrong_country","unsure"]}
HOMONYM={"bell and drum tower","ancient city wall","city wall","400 year old residence of the gao family","grand canal","grand canal of china",
 "national gandhi museum","princess street","san agustin church","immaculate conception cathedral","mt shibaoshan","dharma cave","pingan",
 "pakxang","buddha park","victory square","himalayas","shennv valley the goddess stream"}
HKISO={"yuen po street bird market","hong kong","central hong kong","shum shui po"}
def cause(r):
    if r["verdict"]=="wrong_country" and r["name_norm"] in HKISO: return "hk_iso_as_cn"
    if r["verdict"] in("wrong_place","wrong_country") and r["name_norm"] in HOMONYM: return "homonym_wrong_city"
    if r["verdict"] in("wrong_place","wrong_country"): return "off_target_same_region"
    if r["verdict"]=="too_coarse": return "centroid_instead_of_site"
    if r["verdict"]=="not_a_place": return "not_a_place"
    return None
for r in v: r["cause"]=cause(r)
causes=Counter(r["cause"] for r in v if r["cause"])
prov_tbl={}
for k in ["geoapify","llm","mapbox"]:
    g=[r for r in v if r["located_by"]==k]; gs=[r for r in g if r["sample"]]
    prov_tbl[k]={"population":sum(1 for r in res if r.get("located_by")==k),"verified_all":rate(g),"verified_random_sample":rate(gs) if gs else None}
flag_rates={fl:{**rate([r for r in FL if fl in r["flags"]]),"verdicts":vc([r for r in FL if fl in r["flags"]])} for fl in ["country","tour_spread","dup_coords","precision_area_site","provenance_null"]}
hk=[r for r in res if r.get("lat") is not None and 22.15<=r["lat"]<=22.57 and 113.83<=r["lng"]<=114.45]
mo=[r for r in res if r.get("lat") is not None and 22.10<=r["lat"]<=22.22 and 113.52<=r["lng"]<=113.60]
summary={
 "audit":"S254 geocode audit, CIS geo.place_name","date":"2026-10-28",
 "scope":{"total":len(P),"resolved":T,"pending":sum(r["status"]=="pending" for r in P),"unknown":sum(r["status"]=="unknown" for r in P)},
 "rule_flags":{"dup_coords":{"rows":927,"coordinate_groups":243},"precision_area_site":755,"provenance_null":652,"tour_spread":260,"country":38,"bbox":0,
   "null_island_zero_swapped":0,"rows_with_any_flag":NF},
 "flag_combinations":{"dup_coords only":679,"precision_area_site only":619,"provenance_null only":522,"tour_spread only":168,"dup+precision":110,"dup+provenance":94,
   "country only":35,"dup+spread":31,"provenance+spread":25,"precision+spread":22,"dup+provenance+spread":10,"dup+precision+spread":3,"country+provenance":1,"country+precision":1,"country+spread":1},
 "pairwise":{"dup&precision":113,"dup&provenance":104,"dup&spread":44,"provenance&spread":35,"precision&spread":25},
 "country_flag_groups":{"TZ in Kilimanjaro tours stored as India (source country wrong)":24,"VN in Bangkok-HCMC cycling tours stored as Thailand (true cross-border, TH-VN not in neighbour map)":13,"NP point in a Pakistan tour ('himalayas')":1},
 "cross_border_accepted_as_neighbour":{"rows":443,"top":{"CN in NP tours":116,"VN in LA tours":72,"KH in TH tours":51}},
 "provenance_null":{"rows":652,"located_by":{"llm":442,"mapbox":210},"geo_precision":{"null":649,"line":3},"confidence_null":652,"review_reason_null":652,
   "top_countries":{"KR":104,"NP":103,"CN":87,"BT":64,"IN":64,"LA":51,"TH":49,"MN":48,"LK":45,"JP":25},"other_flags":{"dup_coords":104,"tour_spread":35,"country":1}},
 "verification":{"design":"top-400 flagged by risk score (all 297 country/spread rows + 103 dup/precision/provenance) + 200 random unflagged (seed 254); 10 shards x 60",
   "verifier":"LLM agent judgement only; no geocoder or paid call. Tolerance: site ~2-4 km, village/town ~5 km, area/line = point inside the feature.",
   "random_unflagged_sample":{**rate(S),"verdicts":vc(S)},"flagged_top400":{**rate(FL),"verdicts":vc(FL)},
   "per_flag":flag_rates,"by_located_by":prov_tbl,
   "overall_estimate_flag_stratified":est_flag,"overall_estimate_provenance_stratified":est_prov,
   "projected_counts_over_resolved":projected,
   "error_causes_in_verified":dict(causes)},
 "hong_kong_macau_iso":{"rows_in_HK_box":len(hk),"iso":dict(Counter(r["country_iso2"] for r in hk)),"rows_in_Macau_box":len(mo),"iso_macau":dict(Counter(r["country_iso2"] for r in mo))},
 "name_norm_article_strip":{"rows_with_leading_An_dropped":sum(1 for r in P if (r.get("display_name") or "").lower().startswith("an ") and not r["name_norm"].startswith("an ")),
   "proper_noun_examples":["An Binh Island -> binh island","An Ping Old Street -> ping old street"]},
}
json.dump(summary,open(OUT/"flags-summary.json","w"),ensure_ascii=False,indent=1)
# verified.json for docs: add cause
json.dump(v,open(OUT/"verified.json","w"),ensure_ascii=False,indent=1)
def short(t,n=46): return t if len(t)<=n else t[:n-1]+"…"
def pt(r): return f"{r['lat']:.4f}, {r['lng']:.4f} {r['country_iso2']} ({r['located_by']}/{r['geo_precision'] or 'null'})"
order={"wrong_country":0,"wrong_place":1,"too_coarse":2}
W=sorted([r for r in v if r["verdict"] in order],key=lambda r:(order[r["verdict"]],r["name_norm"]))
lines=["| # | verdict | name | tour | current point | expected |","|---|---|---|---|---|---|"]
for i,r in enumerate(W,1):
    exp=(r["expected"] or "—").replace("|","/"); lines.append(f"| {i} | {r['verdict']} | {r['name_norm']} | {short(r['tour_name'])} | {pt(r)} | {exp} |")
np_=sorted([r for r in v if r["verdict"]=="not_a_place"],key=lambda r:r["name_norm"])
lines2=["| name | tour | kind |","|---|---|---|"]
def kind(n):
    if " to " in f" {n} " or n.startswith("border to"): return "route segment"
    if "hotel" in n or "or similar" in n or "lodge" in n or "lobby" in n: return "lodging"
    if " and " in n: return "compound"
    return "activity / people / description"
for r in np_: lines2.append(f"| {r['name_norm']} | {short(r['tour_name'])} | {kind(r['name_norm'])} |")
un=sorted([r for r in v if r["verdict"]=="unsure"],key=lambda r:r["name_norm"])
lines3=["| name | tour | current point | note |","|---|---|---|---|"]
for r in un: lines3.append(f"| {r['name_norm']} | {short(r['tour_name'])} | {pt(r)} | {short(r['note'],90)} |")
Path(HERE/"tbl_wrong.md").write_text("\n".join(lines)+"\n"); Path(HERE/"tbl_np.md").write_text("\n".join(lines2)+"\n"); Path(HERE/"tbl_unsure.md").write_text("\n".join(lines3)+"\n")
print(json.dumps({k:summary["verification"][k] for k in ["overall_estimate_flag_stratified","overall_estimate_provenance_stratified","projected_counts_over_resolved","error_causes_in_verified"]},indent=1))
print(json.dumps({k:{"pop":x["population"],"all":(x["verified_all"]["n"],x["verified_all"]["correct_rate"]),"samp":(x["verified_random_sample"] or {}).get("correct_rate")} for k,x in prov_tbl.items()}))
print({k:(x["n"],x["error_rate"]) for k,x in flag_rates.items()}, summary["hong_kong_macau_iso"], summary["name_norm_article_strip"]["rows_with_leading_An_dropped"], len(W), len(np_), len(un))
