#!/usr/bin/env python3
"""Draft the cost sections of the monthly cost and capacity review (FIN-02 / OPS-08, AA-896).

Offline and read-only. It makes NO AWS call: Cost Explorer data comes from what the CIS API already stored
(data standard DM-10.4, S243 reconciliation K-14: no new Cost Explorer script). Inputs:

  --current FILE    JSON body of  GET /admin/platform/cost?month=YYYY-MM&refresh_if_stale=false  (AA-884,
                    api/services/platform_cost.py cost_by_app): acc2 spend by App tag and service, LLM spend
                    by app, acc3 Bedrock from shared.cost_explorer_snapshot (acc1, retired by AA-998,
                    only when a month still carries it).
  --previous FILE   the same JSON for the month before (optional; enables the change columns).
  --llm-csv FILE    optional CSV with columns stage,role,account,calls,cost_usd (one month), from the
                    read-only SQL printed by --print-sql (shared.llm_call_daily + shared.llm_call_log).
  --units FILE      optional JSON with denominators for unit costs, e.g.
                    {"published_tours": 1234, "trip_plans": 56, "bookings": 0}.
  --out FILE        write the Markdown there (default: stdout).

The output fills the "Totals", "By app", "Top services", "LLM spend" and "Unit costs" sections of
docs/templates/cost-report.md. Claude Code pastes it into docs/audits/<date>-S<nnn>-capacity-review/README.md,
adds the C8b capacity checklist and the Vietnamese summary, and Nghiệp approves (C8a).

How to get the inputs: docs/ops/cost/README.md. Standard library only; Python 3.10+.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Optional

CHANGE_FLAG_PCT = 20.0  # template: "changes over 20 %"

LLM_BY_STAGE_SQL = """-- Read-only. $1 = first day of the month, $2 = first day of the next month (dates, UTC).
-- Same sources as platform_cost.AI_SPEND_SQL: rolled-up days from shared.llm_call_daily, other days from
-- shared.llm_call_log. Export the result as CSV with a header row.
SELECT stage, role, coalesce(account, 'acc2') AS account,
       sum(calls)::bigint AS calls, round(sum(cost_usd)::numeric, 4) AS cost_usd
  FROM (
        SELECT d.stage, d.role, d.account, d.calls, d.cost_usd
          FROM shared.llm_call_daily d
         WHERE d.day >= $1 AND d.day < $2
        UNION ALL
        SELECT l.stage, l.role, l.account, 1, coalesce(l.cost_usd, 0)
          FROM shared.llm_call_log l
         WHERE l.created_at >= ($1::date::timestamp AT TIME ZONE 'UTC')
           AND l.created_at < ($2::date::timestamp AT TIME ZONE 'UTC')
           AND NOT EXISTS (SELECT 1 FROM shared.llm_call_daily d
                            WHERE d.day = (l.created_at AT TIME ZONE 'UTC')::date)
       ) u
 GROUP BY 1, 2, 3
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


def load_json(path: Optional[str]) -> Optional[dict[str, Any]]:
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("month", "apps", "totals"):
        if key not in data:
            raise SystemExit(f"{path}: not a /admin/platform/cost response (missing '{key}')")
    return data


def apps_by_key(data: Optional[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {r["app"]: r for r in (data or {}).get("apps", [])}


def services_total(data: Optional[dict[str, Any]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for r in (data or {}).get("apps", []):
        for s in r.get("services", []):
            out[s["service"]] = out.get(s["service"], 0.0) + float(s["amount_usd"])
    return out


# acc3 is the only LLM satellite (AA-998). acc1 (the old fallback) gets a row only while a month's JSON still
# carries it, so the first report after the retirement still compares with the month before.
SATELLITES = (("acc3", "acc3 (LLM satellite)"), ("acc1", "acc1 (retired, AA-998)"))


def satellite_rows(cur: dict[str, Any], prev: dict[str, Any]) -> list[tuple[str, str]]:
    return [(n, label) for n, label in SATELLITES if n == "acc3" or n in cur or n in prev]


def section_totals(cur: dict[str, Any], prev: Optional[dict[str, Any]]) -> list[str]:
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
    ai = (cur.get("totals") or {}).get("ai_usd")
    lines += ["", f"LLM spend by app (gateway estimates, incl. OpenAI and Jev): {money(ai)} USD. "
              f"Grand total per the AA-884 rule (AWS acc2 + LLM - acc2 Bedrock counted once): "
              f"{money((cur.get('totals') or {}).get('total_usd'))} USD.", ""]
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


def section_llm(path: Optional[str]) -> list[str]:
    lines = ["## LLM spend", ""]
    if not path:
        return lines + ["<No --llm-csv given: run the SQL from `--print-sql` and add the by-stage table.>", ""]
    rows = list(csv.DictReader(Path(path).open(encoding="utf-8")))
    need = {"stage", "role", "account", "calls", "cost_usd"}
    if rows and not need <= set(rows[0]):
        raise SystemExit(f"{path}: columns must include {sorted(need)}")
    regular = [r for r in rows if not r["stage"].startswith("adhoc_")]
    adhoc = [r for r in rows if r["stage"].startswith("adhoc_")]
    for title, subset in (("By stage and role", regular), ("Ad-hoc runs (stage adhoc_<issue>)", adhoc)):
        total = sum(float(r["cost_usd"] or 0) for r in subset)
        lines += [f"### {title} — {money(total)} USD", "",
                  "| Stage | Role | Account | Calls | USD |", "|---|---|---|---|---|"]
        for r in sorted(subset, key=lambda r: -float(r["cost_usd"] or 0))[:20]:
            lines.append(f"| {r['stage']} | {r['role']} | {r['account']} | {int(float(r['calls'] or 0)):,} | "
                         f"{money(float(r['cost_usd'] or 0))} |")
        if not subset:
            lines.append("| none | | | | |")
        lines.append("")
    return lines


def section_units(cur: dict[str, Any], prev: Optional[dict[str, Any]], units_path: Optional[str]) -> list[str]:
    lines = ["## Unit costs", "", "| Unit | Value (USD) | Basis |", "|---|---|---|"]
    if not units_path:
        return lines + ["| <no --units file> | | |", ""]
    units = json.loads(Path(units_path).read_text(encoding="utf-8"))
    rows = apps_by_key(cur)

    def per(numer: Optional[float], key: str) -> str:
        n = units.get(key)
        return money(numer / n) if numer is not None and n else "n/a"

    cis = rows.get("cis", {})
    tp = rows.get("tripplanner", {})
    bk = rows.get("booking", {})
    lines += [
        f"| USD per published tour | {per(cis.get('total_usd'), 'published_tours')} | cis total / {units.get('published_tours')} published tours |",
        f"| USD LLM per published tour | {per(cis.get('ai_usd'), 'published_tours')} | cis LLM / {units.get('published_tours')} |",
        f"| USD per trip plan | {per(tp.get('total_usd'), 'trip_plans')} | tripplanner total / {units.get('trip_plans')} trip plans |",
        f"| USD per booking | {per(bk.get('total_usd'), 'bookings')} | booking total / {units.get('bookings')} bookings |",
        "",
    ]
    return lines


def build(cur: dict[str, Any], prev: Optional[dict[str, Any]], llm_csv: Optional[str], units: Optional[str]) -> str:
    out = [f"<!-- Drafted by tools/finops/monthly_cost_report.py from /admin/platform/cost {cur['month']}"
           f"{' vs ' + prev['month'] if prev else ''}; numbers are inputs, the reasons are not. -->", ""]
    out += section_totals(cur, prev)
    app_lines, findings = section_apps(cur, prev)
    out += app_lines
    out += section_services(cur, prev)
    out += section_llm(llm_csv)
    out += section_units(cur, prev, units)
    refresh = cur.get("refresh") or {}
    if refresh.get("stale"):
        findings.append(f"Stored Cost Explorer data was stale when exported ({refresh.get('reason')}); "
                        "refresh with POST /admin/cost-explorer/check (~$0.01) before final numbers.")
    out += ["## Findings from the data", ""]
    out += [f"- {f}" for f in findings] or ["- none"]
    out.append("")
    return "\n".join(out)


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--current")
    ap.add_argument("--previous")
    ap.add_argument("--llm-csv")
    ap.add_argument("--units")
    ap.add_argument("--out")
    ap.add_argument("--print-sql", action="store_true", help="print the read-only LLM-by-stage SQL and exit")
    a = ap.parse_args(argv)
    if a.print_sql:
        print(LLM_BY_STAGE_SQL)
        return 0
    if not a.current:
        ap.error("--current is required (or use --print-sql)")
    cur, prev = load_json(a.current), load_json(a.previous)
    text = build(cur, prev, a.llm_csv, a.units)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
