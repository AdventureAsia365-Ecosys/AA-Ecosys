#!/usr/bin/env python3
"""Draft the cost sections of the monthly cost and capacity review (FIN-02 / OPS-08, AA-896).

Offline and read-only. It makes NO AWS call: Cost Explorer data comes from what the CIS API already stored
(data standard DM-10.4, S243 reconciliation K-14: no new Cost Explorer script). Two ways to give the inputs:

A. Bundles from tools/finops/collect_month.py (S262; the orchestrator runs it through tools/ecs/ecsx.sh):
  --bundle FILE          PART=cis output: per month the /admin/platform/cost answer, LLM by app/stage/role/account
                         and the published-tour counts. Holds several months (default Aug-Oct style: the three
                         months before the run), which gives the month-over-month section.
  --booking-bundle FILE  PART=booking output: trip cases created and confirmed per month (optional).
  --crm-bundle FILE      PART=crm output: CRM LLM spend per month from crm.llm_usage_daily (optional). Added to the
                         CRM row as spend outside the acc2 bill, as the admin page does with its staff token.
  --month YYYY-MM        the month the report is about (default: the latest month in --bundle).

B. Single exports (S243, still supported):
  --current FILE    JSON body of  GET /admin/platform/cost?month=YYYY-MM&refresh_if_stale=false  (AA-884,
                    api/services/platform_cost.py cost_by_app).
  --previous FILE   the same JSON for the month before (optional; enables the change columns).
  --llm-csv FILE    optional CSV with columns [app,]stage,role,account,calls,cost_usd (one month), from the
                    read-only SQL printed by --print-sql.

Both ways:
  --units FILE      optional JSON with denominators for the report month, e.g. {"published_tours": 1234,
                    "trip_plans": 56, "bookings": 0}; it overrides the bundle counts with the same key.
  --prev-units FILE last month's denominators as counted at last month's end: the CIS bundle saved with last month's
                    report (its units of that month are taken), or a units JSON. Without it the per-tour costs of
                    last month show "n/a": published_at is overwritten on republish, so a past month's tour count
                    read today is too low (collect_month.PUBLISHED_TOURS_SQL).
  --mgmt-usd N      the management account's own spend of the report month (org CloudTrail trail and bucket, KMS
                    key, budgets), from the one-line Cost Explorer read in docs/ops/cost/README.md (profile aa-mgmt;
                    the CIS client reads acc2 and acc3 only). Shown as its own row and added to the grand total.
                    Without it the totals say plainly that the management account is not included.
  --mgmt-prev-usd N the same for the month before (optional; enables the change column and a like-for-like line 2).
  --budget-usd N    the acc2 monthly account budget (docs/ops/finops.md, Budgets) for the budget line.
  --out FILE        write the Markdown there (default: stdout).

The output fills the Vietnamese summary, "Totals", "By app", "Month over month", "Top services", "LLM spend" and
"Unit costs" sections of docs/templates/cost-report.md. Claude Code pastes it into
docs/audits/<date>-S<nnn>-capacity-review/README.md, fills the <điền> / <fill in> reasons and the C8b capacity
checklist, and the tech lead approves (C8a).

How to get the inputs: docs/ops/cost/README.md. Standard library only; Python 3.10+.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

CHANGE_FLAG_PCT = 20.0  # template: "changes over 20 %"
BUNDLE_MARKER = "FINOPS_BUNDLE "
CREDIT_GAP_RATIO = 0.5  # acc3 CE under half the gateway estimate: credits, not savings
ACCOUNT_ID_RE = re.compile(r"(?<![\w-])\d{12}(?![\w-])")  # same as collect_month.ACCOUNT_ID_RE
TOUR_UNITS = ("published_tours", "published_tours_live")
MGMT_LABEL = "Management account (org trail, KMS, budgets)"

LLM_BY_STAGE_SQL = """-- Read-only. $1 = first day of the month, $2 = first day of the next month (dates, UTC).
-- Same sources as platform_cost.AI_SPEND_SQL: rolled-up days from shared.llm_call_daily, other days from
-- shared.llm_call_log. Export the result as CSV with a header row.
-- tools/finops/collect_month.py (PART=cis) runs the same query for every month of a bundle.
SELECT app, stage, role, account, sum(calls)::bigint AS calls, round(sum(cost_usd)::numeric, 4) AS cost_usd
  FROM (
        SELECT d.app, d.stage, d.role, coalesce(d.account, 'acc2') AS account, d.calls, d.cost_usd
          FROM shared.llm_call_daily d
         WHERE d.day >= $1 AND d.day < $2
        UNION ALL
        SELECT coalesce(l.app, l.quality_signal ->> 'app', 'cis'), l.stage, l.role, coalesce(l.account, 'acc2'),
               1, coalesce(l.cost_usd, 0)
          FROM shared.llm_call_log l
         WHERE l.created_at >= ($1::date::timestamp AT TIME ZONE 'UTC')
           AND l.created_at < ($2::date::timestamp AT TIME ZONE 'UTC')
           AND NOT EXISTS (SELECT 1 FROM shared.llm_call_daily d
                            WHERE d.day = (l.created_at AT TIME ZONE 'UTC')::date)
       ) u
 GROUP BY 1, 2, 3, 4
 ORDER BY cost_usd DESC;
"""


def money(v: Optional[float]) -> str:
    return "n/a" if v is None else f"{v:,.2f}"


def change(cur: Optional[float], prev: Optional[float]) -> tuple[str, bool]:
    """Return ("+12.3 %" | "new" | "n/a", flagged) where flagged means |change| > CHANGE_FLAG_PCT."""
    if cur is None or prev is None:
        return "n/a", False
    if prev == 0:
        return ("new", cur > 0) if cur else ("0", False)
    pct = (cur - prev) / prev * 100
    return f"{pct:+.1f} %", abs(pct) > CHANGE_FLAG_PCT


def month_vi(month: str) -> str:
    """'2026-10' -> '10/2026' (Vietnamese text uses dd/mm/yyyy, docs/STYLE.md)."""
    y, m = month.split("-")
    return f"{m}/{y}"


def check_platform_cost(data: dict[str, Any], where: str) -> dict[str, Any]:
    for key in ("month", "apps", "totals"):
        if key not in data:
            raise SystemExit(f"{where}: not a /admin/platform/cost response (missing '{key}')")
    return data


def load_json(path: Optional[str]) -> Optional[dict[str, Any]]:
    if not path:
        return None
    return check_platform_cost(json.loads(Path(path).read_text(encoding="utf-8")), path)


def load_bundle(path: Optional[str], part: str) -> Optional[dict[str, Any]]:
    """A collect_month.py bundle: the 'FINOPS_BUNDLE <json>' line of an ecsx.sh output, or the bare JSON."""
    if not path:
        return None
    text = Path(path).read_text(encoding="utf-8")
    line = next((ln for ln in text.splitlines() if ln.startswith(BUNDLE_MARKER)), None)
    try:
        data = json.loads(line[len(BUNDLE_MARKER):] if line is not None else text)
    except json.JSONDecodeError as e:
        raise SystemExit(f"{path}: no FINOPS_BUNDLE line and not JSON ({e.msg})") from None
    if data.get("kind") != "finops_bundle" or data.get("part") != part:
        raise SystemExit(f"{path}: not a collect_month.py bundle with PART={part}")
    if not isinstance(data.get("months"), dict) or not data["months"]:
        raise SystemExit(f"{path}: the bundle has no months")
    if part == "cis":
        for m, v in data["months"].items():
            check_platform_cost(v.get("platform_cost") or {}, f"{path} month {m}")
    return data


def apps_by_key(data: Optional[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {r["app"]: r for r in (data or {}).get("apps", [])}


def services_total(data: Optional[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for r in (data or {}).get("apps", []):
        for s in r.get("services", []):
            out[s["service"]] = out.get(s["service"], 0.0) + float(s["amount_usd"])
    return out


def apply_crm(cost: dict[str, Any], crm_month: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Add the CRM gateway's LLM spend to the CRM row, unless the export already holds it (crm_llm status ok).
    Those calls are not billed on acc2, so they count as LLM outside the AWS bill (platform_cost.cost_by_app)."""
    if not crm_month or (cost.get("crm_llm") or {}).get("status") == "ok":
        return cost
    usage = crm_month.get("crm_llm") or {}
    usd, calls = float(usage.get("cost_usd") or 0.0), int(usage.get("calls") or 0)
    out = copy.deepcopy(cost)
    row = next((r for r in out["apps"] if r["app"] == "crm"), None)
    if row is None:
        row = {"app": "crm", "kind": "app", "label": "CRM", "aws_usd": 0.0, "services": [], "ai_usd": 0.0,
               "ai_in_aws_acc2_usd": 0.0, "ai_calls": 0, "total_usd": 0.0}
        out["apps"].append(row)
    row["ai_usd"] = round(float(row.get("ai_usd") or 0.0) + usd, 4)
    row["ai_outside_aws_usd"] = round(row["ai_usd"] - float(row.get("ai_in_aws_acc2_usd") or 0.0), 4)
    row["ai_calls"] = int(row.get("ai_calls") or 0) + calls
    row["total_usd"] = round(float(row.get("total_usd") or 0.0) + usd, 4)
    totals = out["totals"]
    for k in ("ai_usd", "total_usd") + (("ai_outside_aws_usd",) if "ai_outside_aws_usd" in totals else ()):
        totals[k] = round(float(totals.get(k) or 0.0) + usd, 4)
    out["crm_llm"] = {"status": "ok", "source": "crm.llm_usage_daily (collect_month.py PART=crm)"}
    return out


# acc3 is the only LLM satellite (AA-998). The retired fallback account gets a row only while a month's JSON still
# carries it (key "retired" in cost_by_app since AA-998, "acc1" in older exports), so the first report after the
# retirement still compares with the month before.
SATELLITES = (("acc3", "acc3 (LLM satellite)"), ("retired", "Retired account (former LLM fallback)"),
              ("acc1", "acc1 (retired, AA-998)"))


def satellite_rows(cur: dict[str, Any], prev: dict[str, Any]) -> list[tuple[str, str]]:
    return [(n, label) for n, label in SATELLITES if n == "acc3" or n in cur or n in prev]


def grand_total(cost: Optional[dict[str, Any]], mgmt_usd: Optional[float]) -> Optional[float]:
    """The AA-884 total (acc2 + LLM outside acc2) plus the management account when it is given."""
    t = ((cost or {}).get("totals") or {}).get("total_usd")
    return None if t is None else round(float(t) + (mgmt_usd or 0.0), 4)


def section_totals(cur: dict[str, Any], prev: Optional[dict[str, Any]], mgmt_usd: Optional[float] = None,
                   mgmt_prev_usd: Optional[float] = None) -> list[str]:
    lines = ["## Totals by account", "",
             "| Account | This month (USD) | Last month (USD) | Change | Note |",
             "|---|---|---|---|---|"]
    aws_c = (cur.get("aws") or {}).get("total_usd")
    aws_p = ((prev or {}).get("aws") or {}).get("total_usd") if prev else None
    ch, _ = change(aws_c, aws_p)
    cov = cur.get("aws") or {}
    note = f"Cost Explorer, days {cov.get('covered_from')} to {cov.get('covered_to')}, fetched {cov.get('fetched_at')}"
    lines.append(f"| acc2 (infra, all App tags) | {money(aws_c)} | {money(aws_p)} | {ch} | {note} |")
    sat_c = cur.get("llm_satellites") or {}
    sat_p = (prev or {}).get("llm_satellites") or {}
    for name, label in satellite_rows(sat_c, sat_p):
        c = (sat_c.get(name) or {}).get("ce_bedrock_usd")
        p = (sat_p.get(name) or {}).get("ce_bedrock_usd") if prev else None
        est = (sat_c.get(name) or {}).get("llm_log_estimate_usd")
        ch, _ = change(c, p)
        lines.append(f"| {label} | {money(c)} | {money(p)} | {ch} | Bedrock from Cost Explorer; gateway estimate {money(est)} |")
    if mgmt_usd is not None:
        ch, _ = change(mgmt_usd, mgmt_prev_usd)
        lines.append(f"| {MGMT_LABEL} | {money(mgmt_usd)} | {money(mgmt_prev_usd)} | {ch} | "
                     "Cost Explorer of the management account itself (profile aa-mgmt) |")
    else:
        lines.append(f"| {MGMT_LABEL} | not included | | | no --mgmt-usd given: not in any total below |")
    ai = (cur.get("totals") or {}).get("ai_usd")
    total = (cur.get("totals") or {}).get("total_usd")
    lines += ["", f"LLM spend by app (gateway estimates, incl. OpenAI and Jev): {money(ai)} USD. "
              f"Total per the AA-884 rule (AWS acc2 + LLM - acc2 Bedrock counted once): {money(total)} USD."]
    if mgmt_usd is not None:
        lines.append(f"Grand total with the management account: {money(grand_total(cur, mgmt_usd))} USD.")
    else:
        lines.append("Grand total: the management account is not included (no --mgmt-usd).")
    lines.append("")
    return lines


def section_apps(cur: dict[str, Any], prev: Optional[dict[str, Any]]) -> tuple[list[str], list[str]]:
    findings: list[str] = []
    lines = ["## By app (tag `App`)", "",
             "| App | This month (USD) | Last month (USD) | Change | AWS | LLM | Note |",
             "|---|---|---|---|---|---|---|"]
    prev_rows = apps_by_key(prev)
    for r in cur.get("apps", []):
        p = prev_rows.get(r["app"])
        ch, flagged = change(r.get("total_usd"), p.get("total_usd") if p else None)
        note = ""
        if r.get("kind") == "untagged" and (r.get("aws_usd") or 0) > 0:
            top = ", ".join(s["service"] for s in r.get("services", [])[:3])
            note = f"finding: untagged spend ({top})"
            findings.append(f"Untagged acc2 spend {money(r['aws_usd'])} USD (DM-10.1): {top}.")
        if flagged:
            note = (note + "; " if note else "") + "change over 20 %"
        lines.append(f"| {r.get('label', r['app'])} | {money(r.get('total_usd'))} | "
                     f"{money(p.get('total_usd')) if p else 'n/a'} | {ch} | {money(r.get('aws_usd'))} | "
                     f"{money(r.get('ai_usd'))} | {note} |")
    lines.append("")
    return lines, findings


def section_mom(months: list[str], costs: dict[str, dict[str, Any]]) -> list[str]:
    """Every month of the bundle side by side: per app row, the totals, and the top services of the last month."""
    if len(months) < 2:
        return []
    head = "| {} | " + " | ".join(months) + " | Change, last month |"
    sep = "|---|" + "---|" * len(months) + "---|"
    last, before = months[-1], months[-2]

    def row(label: str, values: list[Optional[float]]) -> str:
        ch, flagged = change(values[-1], values[-2])
        return (f"| {label} | " + " | ".join(money(v) for v in values)
                + f" | {ch}{' (over 20 %)' if flagged else ''} |")

    lines = ["## Month over month", "",
             "App tags count only from the day they were set (2026-10-15/16, AA-828); spend before that sits in "
             "\"Not assigned to an app\". Compare earlier months by service. The management account is not in this "
             "table (see Totals by account).", "",
             head.format("App"), sep]
    order: list[str] = []
    labels: dict[str, str] = {}
    for m in months:
        for r in costs[m].get("apps", []):
            if r["app"] not in labels:
                order.append(r["app"])
            labels[r["app"]] = r.get("label", r["app"])
    for key in order:
        vals = [apps_by_key(costs[m]).get(key, {}).get("total_usd") for m in months]
        lines.append(row(labels[key], [None if v is None else float(v) for v in vals]))
    lines.append(row("**Total (AWS acc2 + LLM outside AWS)**",
                     [(costs[m].get("totals") or {}).get("total_usd") for m in months]))
    lines.append(row("AWS acc2", [(costs[m].get("aws") or {}).get("total_usd") for m in months]))
    lines.append(row("LLM, all apps (gateway estimate)", [(costs[m].get("totals") or {}).get("ai_usd") for m in months]))
    lines.append(row("acc3 Bedrock (Cost Explorer, net of credits)",
                     [((costs[m].get("llm_satellites") or {}).get("acc3") or {}).get("ce_bedrock_usd") for m in months]))
    svc = {m: services_total(costs[m]) for m in months}
    top = sorted(svc[last].items(), key=lambda kv: -kv[1])[:10]
    lines += ["", f"Top 10 acc2 services of {last}:", "", head.format("Service"), sep]
    for name, _ in top:
        lines.append(row(name, [svc[m].get(name) for m in months]))
    gone = [s for s in svc[before] if s not in svc[last] and svc[before][s] >= 1.0]
    if gone:
        lines += ["", f"Services billed in {before} but not in {last}: {', '.join(sorted(gone))}."]
    lines.append("")
    return lines


def section_services(cur: dict[str, Any], prev: Optional[dict[str, Any]]) -> list[str]:
    c, p = services_total(cur), services_total(prev)
    top = sorted(c.items(), key=lambda kv: -kv[1])[:5]
    movers = [s for s in c if s not in dict(top) and change(c[s], p.get(s) if prev else None)[1] and c[s] >= 1.0]
    lines = ["## Top 5 services and changes over 20 %", "",
             "| Service | This month (USD) | Last month (USD) | Change | Reason |", "|---|---|---|---|---|"]
    for name, amount in top + [(s, c[s]) for s in movers]:
        ch, _ = change(amount, p.get(name) if prev else None)
        lines.append(f"| {name} | {money(amount)} | {money(p.get(name)) if prev else 'n/a'} | {ch} | <fill in> |")
    lines.append("")
    return lines


def read_llm_csv(path: str) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    need = {"stage", "role", "account", "calls", "cost_usd"}
    if rows and not need <= set(rows[0]):
        raise SystemExit(f"{path}: columns must include {sorted(need)}")
    return rows


def crm_llm_rows(crm_month: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"app": "crm", "stage": r.get("stage"), "role": r.get("model") or "-", "account": "crm_gateway",
             "calls": r.get("calls"), "cost_usd": r.get("cost_usd")}
            for r in ((crm_month or {}).get("crm_llm") or {}).get("by_stage_model") or []]


def section_llm(rows: Optional[list[dict[str, Any]]]) -> list[str]:
    lines = ["## LLM spend", ""]
    if rows is None:
        return lines + ["<No --llm-csv or --bundle given: run the SQL from `--print-sql` and add the by-stage table.>",
                        ""]
    with_app = any(r.get("app") for r in rows)
    regular = [r for r in rows if not str(r["stage"]).startswith("adhoc_")]
    adhoc = [r for r in rows if str(r["stage"]).startswith("adhoc_")]
    if with_app:
        by_app: dict[str, float] = {}
        for r in rows:
            by_app[r.get("app") or "cis"] = by_app.get(r.get("app") or "cis", 0.0) + float(r["cost_usd"] or 0)
        lines += ["By app: " + ", ".join(f"{a} {money(v)} USD" for a, v in sorted(by_app.items(), key=lambda kv: -kv[1]))
                  + "." + (" CRM rows come from its own gateway (role column = model)." if "crm" in by_app else ""), ""]
    for title, subset in (("By stage and role", regular), ("Ad-hoc runs (stage adhoc_<issue>)", adhoc)):
        total = sum(float(r["cost_usd"] or 0) for r in subset)
        cols = ("| App | Stage | Role | Account | Calls | USD |", "|---|---|---|---|---|---|") if with_app else \
            ("| Stage | Role | Account | Calls | USD |", "|---|---|---|---|---|")
        lines += [f"### {title} — {money(total)} USD", "", *cols]
        for r in sorted(subset, key=lambda r: -float(r["cost_usd"] or 0))[:20]:
            app = f"{r.get('app') or 'cis'} | " if with_app else ""
            lines.append(f"| {app}{r['stage']} | {r['role']} | {r['account']} | {int(float(r['calls'] or 0)):,} | "
                         f"{money(float(r['cost_usd'] or 0))} |")
        if not subset:
            lines.append("| none | | | | |" + (" |" if with_app else ""))
        lines.append("")
    return lines


NOT_FROZEN = "n/a (published_at is overwritten on republish)"


def unit_values(cost: Optional[dict[str, Any]], units: dict[str, Any]) -> dict[str, Optional[float]]:
    rows = apps_by_key(cost)

    def per(numer: Optional[float], n: Any) -> Optional[float]:
        return numer / n if numer is not None and n else None

    cis, tp, bk = rows.get("cis", {}), rows.get("tripplanner", {}), rows.get("booking", {})
    bookings = units.get("bookings_confirmed", units.get("bookings"))
    return {
        "tour": per(cis.get("total_usd"), units.get("published_tours")),
        "tour_llm": per(cis.get("ai_usd"), units.get("published_tours")),
        "trip_plan": per(tp.get("total_usd"), units.get("trip_plans")),
        "trip_case": per(bk.get("total_usd"), units.get("trip_cases")),
        "booking": per(bk.get("total_usd"), bookings),
    }


def section_units(cur: dict[str, Any], prev: Optional[dict[str, Any]], units: Optional[dict[str, Any]],
                  prev_units: Optional[dict[str, Any]] = None, prev_tours_frozen: bool = False) -> list[str]:
    """``prev_tours_frozen``: last month's tour counts were taken at last month's end (--prev-units). Otherwise
    they were counted today, after republishes moved published_at, so last month's per-tour costs show n/a."""
    lines = ["## Unit costs", "", "| Unit | Value (USD) | Last month (USD) | Basis |", "|---|---|---|---|"]
    if not units:
        return lines + ["| <no --units file or bundle counts> | | | |", ""]
    v = unit_values(cur, units)
    pv: dict[str, Any] = unit_values(prev, prev_units) if prev is not None and prev_units else {}
    if pv and not prev_tours_frozen:
        pv.update(tour=NOT_FROZEN, tour_llm=NOT_FROZEN)
    def n(key: str) -> str:
        v = units.get(key)
        return "no count" if v is None else f"{v:,}"

    bookings_key = "bookings_confirmed" if "bookings_confirmed" in units else "bookings"
    live = f"; {n('published_tours_live')} live at month end" if "published_tours_live" in units else ""
    rows = [
        ("USD per published tour", "tour", f"cis total / {n('published_tours')} published tours{live}"),
        ("USD LLM per published tour", "tour_llm", f"cis LLM / {n('published_tours')}"),
        ("USD per trip plan", "trip_plan", f"tripplanner total / {n('trip_plans')} trip plans"),
    ]
    if "trip_cases" in units:
        rows.append(("USD per trip case", "trip_case", f"booking total / {n('trip_cases')} trip cases created"))
    rows.append(("USD per booking", "booking", f"booking total / {n(bookings_key)} bookings"
                 + (" (trip cases confirmed or later)" if "bookings_confirmed" in units else "")))
    for label, key, basis in rows:
        last = pv.get(key)
        lines.append(f"| {label} | {money(v[key])} | {last if isinstance(last, str) else money(last)} | {basis} |")
    lines += ["", "Published tours = published or republished in the month (`published_at`), counted when the bundle "
              "was collected: a republish overwrites `published_at`, so a later republish moves a tour out of its "
              "earlier month and a past month counted today is too low. Last month's per-tour cost is shown only "
              "from the counts saved with last month's report (`--prev-units`). Dev numbers: trend only.", ""]
    return lines


def summary_vi(cur: dict[str, Any], prev: Optional[dict[str, Any]], units: Optional[dict[str, Any]],
               budget_usd: Optional[float], mgmt_usd: Optional[float] = None,
               mgmt_prev_usd: Optional[float] = None) -> list[str]:
    """Five lines for the business owner (plain Vietnamese, no issue keys). The reason and the decision stay to fill.
    Line 1 is the grand total with the management account when --mgmt-usd is given, and says so when it is not."""
    t = cur.get("totals") or {}
    total, aws = t.get("total_usd"), (cur.get("aws") or {}).get("total_usd")
    outside = t.get("ai_outside_aws_usd")
    if outside is None and total is not None and aws is not None:
        outside = total - aws
    m = month_vi(cur["month"])
    parts = f"hạ tầng AWS {money(aws)} USD, AI tính ngoài hoá đơn AWS {money(outside)} USD"
    if mgmt_usd is not None:
        line1 = (f"1. Tổng chi phí tháng {m}: {money(grand_total(cur, mgmt_usd))} USD ({parts}, tài khoản quản lý AWS "
                 f"{money(mgmt_usd)} USD).")
    else:
        line1 = f"1. Tổng chi phí tháng {m}: {money(total)} USD ({parts}; chưa gồm tài khoản quản lý AWS)."
    lines = ["## Tóm tắt cho chủ doanh nghiệp (VI)", "",
             "<!-- Bản nháp tự sinh từ số liệu: điền lý do (dòng 3) và việc cần quyết (dòng 5), đọc lại trước khi gửi. -->",
             "", line1]
    if prev:
        both = mgmt_usd is not None and mgmt_prev_usd is not None
        cur_t = grand_total(cur, mgmt_usd if both else None)
        pt = grand_total(prev, mgmt_prev_usd if both else None)
        ch, _ = change(cur_t, pt)
        note = " (so sánh chưa gồm tài khoản quản lý)" if mgmt_usd is not None and not both else ""
        lines.append(f"2. So với tháng {month_vi(prev['month'])} ({money(pt)} USD): "
                     f"{ch.replace('n/a', 'chưa so được')}{note}.")
    else:
        lines.append("2. Chưa có số tháng trước để so sánh.")
    deltas = []
    prev_rows = apps_by_key(prev)
    for r in cur.get("apps", []):
        if prev is not None:
            deltas.append((float(r.get("total_usd") or 0) - float(prev_rows.get(r["app"], {}).get("total_usd") or 0),
                           r.get("label", r["app"])))
    if deltas:
        d, label = max(deltas, key=lambda x: abs(x[0]))
        lines.append(f"3. Thay đổi lớn nhất: {label} {d:+,.2f} USD; lý do: <điền>.")
    else:
        lines.append("3. Phần lớn chi phí: <điền>; lý do: <điền>.")
    if budget_usd and aws is not None:
        used = aws / budget_usd * 100
        lines.append(f"4. Ngân sách AWS tháng: đã dùng {money(aws)} / {money(budget_usd)} USD ({used:.0f} %), "
                     f"còn {money(budget_usd - aws)} USD.")
    else:
        lines.append("4. Ngân sách tháng: <điền>.")
    v = unit_values(cur, units or {})
    unit = (f"Chi phí mỗi tour xuất bản: {money(v['tour'])} USD (riêng AI {money(v['tour_llm'])} USD)"
            if v["tour"] is not None else "Chi phí mỗi tour xuất bản: chưa có số tour")
    lines += [f"5. {unit}; số liệu môi trường Dev, chỉ để xem xu hướng. Cần quyết định: <điền, hoặc \"không có\">.", ""]
    return lines


def data_findings(cur: dict[str, Any], crm_given: bool) -> list[str]:
    out: list[str] = []
    refresh = cur.get("refresh") or {}
    if refresh.get("stale"):
        out.append(f"Stored Cost Explorer data was stale when exported ({refresh.get('reason')}); "
                   "refresh with POST /admin/cost-explorer/check (~$0.01) or collect_month.py REFRESH=1 before "
                   "final numbers.")
    acc3 = (cur.get("llm_satellites") or {}).get("acc3") or {}
    ce_usd, est = acc3.get("ce_bedrock_usd"), acc3.get("llm_log_estimate_usd")
    if est is not None and est >= 1.0 and (ce_usd is None or ce_usd < CREDIT_GAP_RATIO * est):
        out.append(f"acc3 Bedrock in Cost Explorer ({money(ce_usd)} USD) is under half of the gateway estimate "
                   f"({money(est)} USD). UnblendedCost is net of credits (acc3 pays with its AWS Lift credit since "
                   "2026-10-29): read the gross Usage amount (RECORD_TYPE) before calling it a saving.")
    if "crm_llm" in cur and (cur.get("crm_llm") or {}).get("status") != "ok" and not crm_given:
        out.append("CRM LLM spend is not in the CRM row (the export had no staff token for the CRM gateway); add "
                   "--crm-bundle from collect_month.py PART=crm.")
    return out


def build(cur: dict[str, Any], prev: Optional[dict[str, Any]], llm_rows: Optional[list[dict[str, Any]]],
          units: Optional[dict[str, Any]], *, prev_units: Optional[dict[str, Any]] = None,
          history: Optional[dict[str, dict[str, Any]]] = None, budget_usd: Optional[float] = None,
          crm_given: bool = False, prev_tours_frozen: bool = False, mgmt_usd: Optional[float] = None,
          mgmt_prev_usd: Optional[float] = None) -> str:
    out = [f"<!-- Drafted by tools/finops/monthly_cost_report.py from /admin/platform/cost {cur['month']}"
           f"{' vs ' + prev['month'] if prev else ''}; numbers are inputs, the reasons are not. -->", ""]
    out += summary_vi(cur, prev, units, budget_usd, mgmt_usd, mgmt_prev_usd)
    out += section_totals(cur, prev, mgmt_usd, mgmt_prev_usd)
    app_lines, findings = section_apps(cur, prev)
    out += app_lines
    if history:
        out += section_mom(sorted(history), history)
    out += section_services(cur, prev)
    out += section_llm(llm_rows)
    out += section_units(cur, prev, units, prev_units, prev_tours_frozen)
    findings += data_findings(cur, crm_given)
    out += ["## Findings from the data", ""]
    out += [f"- {f}" for f in findings] or ["- none"]
    out.append("")
    text = "\n".join(out)
    if ACCOUNT_ID_RE.search(text):  # the draft goes into the public root repo
        raise SystemExit("the drafted report holds a 12-digit account ID; scrub the input (collect_month.scrub)")
    return text


def from_bundles(a: argparse.Namespace) -> dict[str, Any]:
    cis = load_bundle(a.bundle, "cis")
    bk = load_bundle(a.booking_bundle, "booking")
    crm = load_bundle(a.crm_bundle, "crm")
    months = sorted(cis["months"])
    month = a.month or months[-1]
    if month not in cis["months"]:
        raise SystemExit(f"--month {month} is not in the bundle ({', '.join(months)})")
    crm_m = (crm or {}).get("months", {})
    history = {m: apply_crm(cis["months"][m]["platform_cost"], crm_m.get(m)) for m in months if m <= month}

    def units_of(m: str) -> dict[str, Any]:
        u = dict(cis["months"][m].get("units") or {})
        u.update(((bk or {}).get("months", {}).get(m) or {}).get("units") or {})
        return u

    i = months.index(month)
    prev_m = months[i - 1] if i > 0 else None
    units = units_of(month)
    if a.units:
        units.update(json.loads(Path(a.units).read_text(encoding="utf-8")))
    prev_units = units_of(prev_m) if prev_m else None
    frozen = load_prev_units(a.prev_units, prev_m) if prev_m else None
    if prev_units is not None and frozen:
        prev_units.update(frozen)
    llm = list(cis["months"][month].get("llm_by_stage") or []) + crm_llm_rows(crm_m.get(month))
    return {"cur": history[month], "prev": history.get(prev_m) if prev_m else None, "llm_rows": llm,
            "units": units, "prev_units": prev_units, "history": history, "crm_given": crm is not None,
            "prev_tours_frozen": bool(frozen) and any(k in frozen for k in TOUR_UNITS)}


def load_prev_units(path: Optional[str], prev_month: Optional[str]) -> Optional[dict[str, Any]]:
    """--prev-units: last month's CIS bundle (the units of ``prev_month`` it holds) or a plain units JSON."""
    if not path:
        return None
    text = Path(path).read_text(encoding="utf-8")
    line = next((ln for ln in text.splitlines() if ln.startswith(BUNDLE_MARKER)), None)
    try:
        data = json.loads(line[len(BUNDLE_MARKER):] if line is not None else text)
    except json.JSONDecodeError as e:
        raise SystemExit(f"{path}: not JSON ({e.msg})") from None
    if data.get("kind") != "finops_bundle":
        return dict(data)
    got = ((data.get("months") or {}).get(prev_month) or {}).get("units")
    if got is None:
        raise SystemExit(f"{path}: the bundle has no units for {prev_month}")
    return dict(got)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bundle")
    ap.add_argument("--booking-bundle")
    ap.add_argument("--crm-bundle")
    ap.add_argument("--month")
    ap.add_argument("--current")
    ap.add_argument("--previous")
    ap.add_argument("--llm-csv")
    ap.add_argument("--units")
    ap.add_argument("--prev-units")
    ap.add_argument("--mgmt-usd", type=float)
    ap.add_argument("--mgmt-prev-usd", type=float)
    ap.add_argument("--budget-usd", type=float)
    ap.add_argument("--out")
    ap.add_argument("--print-sql", action="store_true", help="print the read-only LLM-by-stage SQL and exit")
    a = ap.parse_args(argv)
    if a.print_sql:
        print(LLM_BY_STAGE_SQL)
        return 0
    if a.mgmt_prev_usd is not None and a.mgmt_usd is None:
        ap.error("--mgmt-prev-usd needs --mgmt-usd")
    if a.bundle:
        if a.current or a.previous or a.llm_csv:
            ap.error("--bundle replaces --current, --previous and --llm-csv")
        kw = from_bundles(a)
        text = build(kw.pop("cur"), kw.pop("prev"), kw.pop("llm_rows"), kw.pop("units"), budget_usd=a.budget_usd,
                     mgmt_usd=a.mgmt_usd, mgmt_prev_usd=a.mgmt_prev_usd, **kw)
    else:
        if not a.current:
            ap.error("--current or --bundle is required (or use --print-sql)")
        if a.booking_bundle or a.crm_bundle or a.month:
            ap.error("--booking-bundle, --crm-bundle and --month need --bundle")
        cur, prev = load_json(a.current), load_json(a.previous)
        units = json.loads(Path(a.units).read_text(encoding="utf-8")) if a.units else None
        llm_rows = read_llm_csv(a.llm_csv) if a.llm_csv else None
        prev_units = load_prev_units(a.prev_units, prev["month"]) if a.prev_units and prev else None
        text = build(cur, prev, llm_rows, units, prev_units=prev_units, budget_usd=a.budget_usd,
                     prev_tours_frozen=bool(prev_units) and any(k in prev_units for k in TOUR_UNITS),
                     mgmt_usd=a.mgmt_usd, mgmt_prev_usd=a.mgmt_prev_usd)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
