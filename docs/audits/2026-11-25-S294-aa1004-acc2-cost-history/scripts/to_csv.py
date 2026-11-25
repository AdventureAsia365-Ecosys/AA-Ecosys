"""AA-1004 (S294): turn the four Cost Explorer JSON pulls into long-format CSVs.

Usage: python3 scripts/to_csv.py <raw json dir> <csv dir>
Reads service.json, app.json, component.json and rectype.json (output of fetch_ce.sh), writes
acc2-monthly-by-service.csv, acc2-monthly-by-app-tag.csv, acc2-monthly-by-component-tag.csv and
acc2-monthly-by-record-type.csv, plus acc2-monthly-totals.csv. Stdlib only; reads local files only.
A tag group "App$" (empty value) is written as "(untagged)". Refuses to write a cell that looks like an
account number (twelve digits), since the root repo is public.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ACCOUNT_SHAPE = re.compile(r"\b\d{12}\b")
PULLS = {
    "service": ("acc2-monthly-by-service.csv", "service"),
    "app": ("acc2-monthly-by-app-tag.csv", "app_tag"),
    "component": ("acc2-monthly-by-component-tag.csv", "component_tag"),
    "rectype": ("acc2-monthly-by-record-type.csv", "record_type"),
}


def _label(key: str) -> str:
    if "$" in key:
        value = key.split("$", 1)[1]
        return value or "(untagged)"
    return key


def _rows(doc: dict) -> list[tuple[str, str, bool, float, float]]:
    rows = []
    for period in doc["ResultsByTime"]:
        month = period["TimePeriod"]["Start"][:7]
        estimated = bool(period.get("Estimated"))
        for group in period["Groups"]:
            metrics = group["Metrics"]
            rows.append(
                (
                    month,
                    _label(group["Keys"][0]),
                    estimated,
                    float(metrics["UnblendedCost"]["Amount"]),
                    float(metrics["NetUnblendedCost"]["Amount"]),
                )
            )
    return rows


def _write(path: Path, header: list[str], rows: list[list[str]]) -> None:
    for row in rows:
        for cell in row:
            if ACCOUNT_SHAPE.search(cell):
                raise SystemExit(f"refusing to write an account-number-shaped value to {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main(raw_dir: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    totals: dict[str, list[float]] = {}
    months: list[str] = []
    estimated_months: set[str] = set()
    for name, (filename, column) in PULLS.items():
        doc = json.loads((raw_dir / f"{name}.json").read_text(encoding="utf-8"))
        for period in doc["ResultsByTime"]:
            month = period["TimePeriod"]["Start"][:7]
            if month not in months:
                months.append(month)
            if period.get("Estimated"):
                estimated_months.add(month)
        rows = sorted(_rows(doc), key=lambda r: (r[0], -r[3], r[1]))
        _write(
            out_dir / filename,
            ["month", column, "estimated", "unblended_usd", "net_unblended_usd"],
            [[m, k, str(e).lower(), f"{u:.4f}", f"{n:.4f}"] for m, k, e, u, n in rows],
        )
        if name == "service":
            for month, _key, _est, unblended, net in rows:
                cell = totals.setdefault(month, [0.0, 0.0])
                cell[0] += unblended
                cell[1] += net
    total_rows = []
    for month in sorted(months):
        unblended, net = totals.get(month, [0.0, 0.0])
        total_rows.append([month, str(month in estimated_months).lower(), f"{unblended:.2f}", f"{net:.2f}"])
    _write(out_dir / "acc2-monthly-totals.csv", ["month", "estimated", "unblended_usd", "net_unblended_usd"], total_rows)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
