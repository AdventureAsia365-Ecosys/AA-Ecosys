"""AA-896 (S248): Bedrock unit costs per model and month, from local files only (no AWS call).

Joins CloudWatch usage (data/<acc>-bedrock-metrics.json, from fetch_cw_bedrock.sh) with the Cost Explorer
service lines (data/<acc>-service.json, from fetch_ce.sh). Prints a Markdown table.

    python3 -I scripts/bedrock_units.py data            # 23/10 run, October = 01-22
    python3 -I scripts/bedrock_units.py data-final      # after the refresh
"""
import collections
import json
import sys
from pathlib import Path

# Cost Explorer SERVICE name -> CloudWatch ModelId prefixes that bill under it.
SERVICE_MODELS = {
    "Claude Haiku 4.5 (Amazon Bedrock Edition)": ("claude-haiku-4-5",),
    "Claude Sonnet 4.6 (Amazon Bedrock Edition)": ("claude-sonnet-4-6",),
    "Claude Sonnet 5 (Amazon Bedrock Edition)": ("claude-sonnet-5",),
    "OpenAI GPT-5.6 Luna (Amazon Bedrock Edition)": ("gpt-5.6-luna",),
    "OpenAI GPT-6 Luna (Amazon Bedrock Edition)": ("gpt-6-luna",),
}


def family(model_id: str) -> str | None:
    for service, keys in SERVICE_MODELS.items():
        for k in keys:
            # "claude-sonnet-5" must not swallow "claude-sonnet-5-5"
            if model_id.endswith(k) or (k + "-" in model_id and not model_id.endswith(k + "-5")):
                return service
    return None


def usage(path: Path, last_day: str) -> dict:
    agg = collections.defaultdict(float)
    for r in json.loads(path.read_text())["MetricDataResults"]:
        model_id, metric = r["Label"].split("|")
        svc = family(model_id)
        for ts, v in zip(r["Timestamps"], r["Values"]):
            if ts[:10] < last_day:
                agg[(svc or model_id, ts[:7], metric)] += v
    return agg


def ce_cost(path: Path) -> dict:
    out = {}
    for r in json.loads(path.read_text())["ResultsByTime"]:
        for g in r["Groups"]:
            out[(g["Keys"][0], r["TimePeriod"]["Start"][:7])] = float(g["Metrics"]["UnblendedCost"]["Amount"])
    return out


def main(data_dir: str) -> None:
    d = Path(data_dir)
    end = json.loads((d / "acc3-service.json").read_text())["ResultsByTime"][-1]["TimePeriod"]["End"]
    print("| Account | Model | Month | Calls OK | Client errors | Tokens in / call | Tokens out / call "
          "| USD (CE) | USD / 1,000 calls | USD / 1M tokens (in+out) |")
    print("|---|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for acc in ("acc3", "acc1"):
        agg, cost = usage(d / f"{acc}-bedrock-metrics.json", end), ce_cost(d / f"{acc}-service.json")
        for svc, month in sorted({(s, m) for (s, m, _) in agg}):
            inv = agg[(svc, month, "Invocations")]
            err = agg[(svc, month, "InvocationClientErrors")]
            tin, tout = agg[(svc, month, "InputTokenCount")], agg[(svc, month, "OutputTokenCount")]
            usd = cost.get((svc, month))
            if inv < 50 and not usd:
                continue
            name = svc.replace(" (Amazon Bedrock Edition)", "")
            per_k = f"{1000 * usd / inv:.2f}" if usd and inv else "—"
            per_m = f"{1e6 * usd / (tin + tout):.2f}" if usd and tin + tout else "—"
            print(f"| {acc} | {name} | {month} | {inv:,.0f} | {err:,.0f} | {tin / inv if inv else 0:,.0f} "
                  f"| {tout / inv if inv else 0:,.0f} | {usd if usd else 0:.2f} | {per_k} | {per_m} |")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")
