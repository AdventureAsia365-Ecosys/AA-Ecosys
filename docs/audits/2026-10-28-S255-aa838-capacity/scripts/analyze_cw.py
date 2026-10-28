"""Summarise the AA-838 CloudWatch pulls (cw_out.json, cw_out2.json) into report numbers."""
import collections
import json
import statistics

d1 = {r["Id"]: r for r in json.load(open("cw_out.json"))["MetricDataResults"]}
d2 = {r["Id"]: r for r in json.load(open("cw_out2.json"))["MetricDataResults"]}
d = {**d1, **d2}
MB = 1024 * 1024
GB = 1024 ** 3


def vals(i):
    return d[i]["Values"]


def series(i):
    return list(zip(d[i]["Timestamps"], d[i]["Values"]))


def pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def summ(i, scale=1, nd=1):
    v = [x / scale for x in vals(i)]
    if not v:
        return "no data"
    return f"min {min(v):.{nd}f} / avg {statistics.mean(v):.{nd}f} / p95 {pct(v,95):.{nd}f} / max {max(v):.{nd}f} (n={len(v)})"


print("== RDS hourly ==")
print("CPU avg (hourly avg)", summ("cpu_avg"))
print("CPU max (hourly max)", summ("cpu_max"))
cpu = vals("cpu_avg")
print("hours CPU avg >20%:", sum(1 for x in cpu if x > 20), "of", len(cpu))
# per ISO week share of hours > 20
wk = collections.defaultdict(lambda: [0, 0])
for ts, v in series("cpu_avg"):
    w = ts[:10]
    import datetime
    iso = datetime.date.fromisoformat(w).isocalendar()[1]
    wk[iso][1] += 1
    if v > 20:
        wk[iso][0] += 1
print("per ISO week hours >20%:", dict(wk))
print("FreeableMemory min (MB)", summ("mem_min", MB, 0))
print("FreeableMemory avg (MB)", summ("mem_avg", MB, 0))
low = collections.Counter(ts[:10] for ts, v in series("mem_min") if v < 300 * MB)
print("days with hourly min <300MB (hours):", dict(low))
st = series("stor_min")
print("FreeStorage GB first/last/min:", st[0][1] / GB, st[-1][1] / GB, min(v for _, v in st) / GB)
days = (len(st) - 1) / 24
print("storage growth GB/day (first->last):", (st[0][1] - st[-1][1]) / GB / days)
# 7-day growth
last7 = [v for ts, v in st[-24 * 7:]]
print("storage growth GB/day last 7d:", (last7[0] - last7[-1]) / GB / 7)
# daily min storage
dmin = collections.OrderedDict()
for ts, v in st:
    dmin[ts[:10]] = min(dmin.get(ts[:10], 1e18), v)
print("daily min free GB:", {k: round(v / GB, 2) for k, v in dmin.items()})
print("Conn hourly max", summ("conn_max", 1, 0))
print("Conn hourly avg", summ("conn_avg", 1, 1))
print("Conn hourly p95", summ("conn_p95", 1, 1))
cmax = collections.OrderedDict()
for ts, v in series("conn_max"):
    cmax[ts[:10]] = max(cmax.get(ts[:10], 0), v)
print("daily conn max:", dict(cmax))
for k in ["riops_avg", "riops_max", "wiops_avg", "wiops_max", "dqd_max", "swap_max"]:
    print(k, summ(k, 1, 2))
for k in ["rlat_avg", "rlat_max", "wlat_avg", "wlat_max"]:
    print(k, "(ms)", summ(k, 0.001, 2))
print("rthr avg KB/s", summ("rthr_avg", 1024, 1), "wthr avg KB/s", summ("wthr_avg", 1024, 1))
print("credit balance min", summ("credit_bal_min", 1, 1))
print("surplus charged sum 30d", sum(vals("surplus_charged")), "surplus bal max", max(vals("surplus_bal_max") or [0]))
print("txid max", max(vals("txid_max")))
print("== whole window ==")
for k in [k for k in d if k.startswith("w_")]:
    print(k, d[k]["Values"])

print("== ECS ==")
names = ["aa-cis-dev-api", "aa-cis-dev-worker", "aa-booking-dev-api", "aa-crm-dev-api", "aa-crm-dev-web", "aa-crm-dev-portal"]
for i, n in enumerate(names):
    ts = d[f"ecs{i}_cpu_avg"]["Timestamps"]
    first = min(ts) if ts else None
    print(n, "first", first, "hours", len(ts))
    print("  cpu avg", summ(f"ecs{i}_cpu_avg"), "| cpu max", summ(f"ecs{i}_cpu_max"))
    print("  mem avg", summ(f"ecs{i}_mem_avg"), "| mem max", summ(f"ecs{i}_mem_max"))

print("== roles ==")
for i, r in enumerate(["cis_app", "aa_app_user", "tripplanner", "booking", "crm_app", "db_migrator"]):
    print(r, "conn", summ(f"role{i}_max", 1, 0), "| pct", summ(f"role{i}_pctmax", 1, 1))
print("== lambda ==")
for i, n in enumerate(["browse", "assembly"]):
    print(n, "conc max", max(vals(f"lam{i}_conc") or [0]), "throttles", sum(vals(f"lam{i}_thr")),
          "invocations", sum(vals(f"lam{i}_inv")), "errors", sum(vals(f"lam{i}_err")),
          "dur p95 hourly max ms", max(vals(f"lam{i}_dur_p95") or [0]))
    thr = [(ts, v) for ts, v in series(f"lam{i}_thr") if v > 0]
    print("  throttle hours", thr[:10])
print("acct conc max", max(vals("lamacct_conc")))
print("== jobs ==")
for i, n in enumerate(["CIS", "Booking"]):
    print(n, "oldest queued age max s", max(vals(f"job{i}_age") or [0]), "p95", pct(vals(f"job{i}_age"), 95),
          "overdue running max", max(vals(f"job{i}_over") or [0]))
    hi = [(ts, v) for ts, v in series(f"job{i}_age") if v > 900]
    print("  hours with age >15min:", len(hi), hi[:5])
