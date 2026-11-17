#!/usr/bin/env python3
"""Summarise OWASP ZAP baseline reports as Markdown for triage (AA-1111, S283). Stdlib only, offline.

Reads the JSON reports that .github/workflows/zap-baseline.yml uploads (one artifact per target, `zap-<id>`, each
holding `report_json.json`) from a local directory; it downloads nothing itself. Fetch them first:

    gh run download <run id> -R AdventureAsia365-Ecosys/AA-Ecosys -D <dir>
    python3 tools/security/zap_summary.py <dir> [--min-risk low] [--examples 3] > summary.md

Every `*.json` file under <dir> that has ZAP's `site` list is read. The target of a report is the folder it sits in
(the artifact name, `zap-` dropped), or the file name for a report at the top of <dir>. The output has three parts:
  1. counts per target and risk (High / Medium / Low / Informational),
  2. the same alert across targets (one fix, e.g. a header set once at the edge, often clears every row),
  3. per target, every alert with its risk, confidence, plugin id, CWE, instance count and a few example URIs.

Exit: 0 summary printed | 2 no ZAP report found, or a file that is not readable JSON (named on stderr; the summary of
the readable ones is still printed).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RISKS = ("High", "Medium", "Low", "Informational")   # ZAP riskcode 3, 2, 1, 0
RISK_BY_CODE = {"3": "High", "2": "Medium", "1": "Low", "0": "Informational"}
CONFIDENCE_BY_CODE = {"4": "Confirmed", "3": "High", "2": "Medium", "1": "Low", "0": "False positive"}


def cell(value: object) -> str:
    """One Markdown table cell: no line break, no bare pipe."""
    return " ".join(str(value).split()).replace("|", "\\|")


def target_name(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    name = rel.parent.name if len(rel.parts) > 1 else path.stem
    return name[len("zap-"):] if name.startswith("zap-") else name


def is_report(doc: object) -> bool:
    return isinstance(doc, dict) and isinstance(doc.get("site"), list)


def alerts_of(doc: dict) -> list[dict]:
    """The alerts of one report, flattened over its sites: {site, plugin, alert, risk, confidence, cwe, count, uris}."""
    out = []
    for site in doc.get("site") or []:
        if not isinstance(site, dict):
            continue
        for a in site.get("alerts") or []:
            if not isinstance(a, dict):
                continue
            instances = [i for i in a.get("instances") or [] if isinstance(i, dict)]
            try:
                count = int(a.get("count") or len(instances))
            except (TypeError, ValueError):
                count = len(instances)
            out.append({
                "site": str(site.get("@name") or ""),
                "plugin": str(a.get("pluginid") or ""),
                "alert": str(a.get("alert") or a.get("name") or "?"),
                "risk": RISK_BY_CODE.get(str(a.get("riskcode")), "Informational"),
                "confidence": CONFIDENCE_BY_CODE.get(str(a.get("confidence")), str(a.get("confidence") or "?")),
                "cwe": str(a.get("cweid") or ""),
                "count": count,
                "uris": [str(i.get("uri") or "") for i in instances if i.get("uri")],
            })
    return out


def load(root: Path) -> tuple[dict[str, list[dict]], dict[str, str], list[str]]:
    """({target: alerts}, {target: ZAP version}, [unreadable files]) for every ZAP report under root."""
    reports: dict[str, list[dict]] = {}
    versions: dict[str, str] = {}
    errors: list[str] = []
    for path in sorted(root.rglob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue
        if not is_report(doc):
            continue
        target = target_name(path, root)
        reports.setdefault(target, []).extend(alerts_of(doc))
        versions[target] = str(doc.get("@version") or "?")
    return reports, versions, errors


def rank(risk: str) -> int:
    return RISKS.index(risk) if risk in RISKS else len(RISKS)


def render(reports: dict[str, list[dict]], versions: dict[str, str], min_risk: str = "Informational",
           examples: int = 3) -> str:
    keep = rank(min_risk)
    shown = {t: [a for a in alerts if rank(a["risk"]) <= keep] for t, alerts in reports.items()}
    zap = sorted(set(versions.values()))
    lines = ["# ZAP baseline summary", "",
             f"{len(reports)} target(s), ZAP {', '.join(zap) or '?'}, risks shown: {min_risk} and above.", "",
             "## Alerts per target", "",
             "| Target | " + " | ".join(RISKS) + " |", "|---|" + "---:|" * len(RISKS)]
    for target in sorted(shown):
        counts = [sum(1 for a in shown[target] if a["risk"] == r) for r in RISKS]
        lines.append(f"| {cell(target)} | " + " | ".join(str(c) if rank(r) <= keep else "-"
                                                          for c, r in zip(counts, RISKS)) + " |")
    lines.append("")

    across: dict[tuple[str, str, str], dict] = {}
    for target, alerts in shown.items():
        for a in alerts:
            row = across.setdefault((a["risk"], a["plugin"], a["alert"]), {"targets": set(), "count": 0})
            row["targets"].add(target)
            row["count"] += a["count"]
    lines += ["## Alerts across targets", "",
              "| Risk | Alert | Plugin | Targets | Instances |", "|---|---|---|---|---:|"]
    for (risk, plugin, alert), row in sorted(across.items(), key=lambda kv: (rank(kv[0][0]), -len(kv[1]["targets"]),
                                                                              kv[0][2])):
        lines.append(f"| {risk} | {cell(alert)} | {cell(plugin)} | {cell(', '.join(sorted(row['targets'])))} "
                     f"| {row['count']} |")
    if not across:
        lines.append("| - | no alert at this risk level | | | |")
    lines.append("")

    for target in sorted(shown):
        lines += [f"## {target}", ""]
        alerts = sorted(shown[target], key=lambda a: (rank(a["risk"]), a["alert"], a["site"]))
        if not alerts:
            lines += ["No alert at this risk level.", ""]
            continue
        lines += ["| Risk | Confidence | Alert | Plugin | CWE | Instances | Site | Example URIs |",
                  "|---|---|---|---|---|---:|---|---|"]
        for a in alerts:
            uris = a["uris"][:examples]
            more = f" (+{len(a['uris']) - len(uris)})" if len(a["uris"]) > len(uris) else ""
            lines.append(f"| {a['risk']} | {cell(a['confidence'])} | {cell(a['alert'])} | {cell(a['plugin'])} "
                         f"| {cell(a['cwe'])} | {a['count']} | {cell(a['site'])} "
                         f"| {cell('<br>'.join(uris)) if uris else '-'}{more} |")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("directory", type=Path, help="the folder `gh run download` wrote the zap-* artifacts into")
    ap.add_argument("--min-risk", type=str.capitalize, choices=RISKS, default="Informational",
                    help="lowest risk to list (default: Informational, i.e. everything)")
    ap.add_argument("--examples", type=int, default=3, help="example URIs per alert (default 3)")
    a = ap.parse_args(argv)
    if not a.directory.is_dir():
        print(f"{a.directory}: not a directory", file=sys.stderr)
        return 2
    reports, versions, errors = load(a.directory)
    for e in errors:
        print(f"unreadable: {e}", file=sys.stderr)
    if not reports:
        print(f"{a.directory}: no ZAP JSON report found (report_json.json under zap-* folders)", file=sys.stderr)
        return 2
    print(render(reports, versions, a.min_risk, max(a.examples, 0)))
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
