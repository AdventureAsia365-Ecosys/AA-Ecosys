"""Render every architecture diagram in this folder to a self-contained SVG (AA-697).

    python render.py              # all views
    python render.py ecosystem    # one view
    python render.py --check      # only re-run the safety check on the committed SVGs (stdlib, no Graphviz)

Needs the ``diagrams`` package (and optionally Pillow) plus Graphviz ``dot`` on the PATH; see README.md.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from _common import check_svg_safe, finalize_svg  # noqa: E402

VIEWS = ["ecosystem", "infra", "cis", "booking", "tripplanner", "partner"]


def main(argv: list[str]) -> int:
    if "--check" in argv:
        bad = 0
        for name in VIEWS:
            svg = HERE / f"{name}.svg"
            problems = check_svg_safe(svg.read_text(encoding="utf-8")) if svg.exists() else ["missing"]
            print(f"{name}.svg: {'ok' if not problems else problems}")
            bad += bool(problems)
        return 1 if bad else 0
    names = [a for a in argv if not a.startswith("-")] or VIEWS
    os.chdir(HERE)  # diagrams writes <filename>.svg into the working directory
    for name in names:
        importlib.import_module(name).draw(name)
        size = finalize_svg(HERE / f"{name}.svg")
        print(f"{name}.svg: {size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
