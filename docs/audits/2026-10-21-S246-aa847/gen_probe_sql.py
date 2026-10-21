#!/usr/bin/env python3
"""AA-847 — copy the TripPlanner place-reader SQL into the AA-CIS-Infra probe (db/scripts/aa847_places_probe.py).

The probe runs on Dev through DB Migrate `run-script`, which may not import app code. So the exact SQL the browse and
assembly readers send (legacy and cis) is copied into the probe between two markers, with the TripPlanner commit it
came from. This script reads the TripPlanner sources with `ast` (nothing is imported or executed), renders the
module-level string constants and the few f-strings built inside functions, and rewrites the block.

    python3 gen_probe_sql.py --tp ../../../apps/AA-TripPlanner-Web --probe ../../../infra/AA-CIS-Infra/db/scripts/aa847_places_probe.py
    python3 gen_probe_sql.py ... --check      # exit 1 when the probe block differs from a fresh generation

Rendering rules for an f-string (ast.JoinedStr): each `{expr}` is replaced by SUBS[<name>][ast.unparse(expr)], and
a placeholder without a substitution is an error, so a reader change cannot slip through silently.

TripPlanner slice 6c (AA-847) made `vector_topk` source-aware (`Source` LEGACY / CIS): `{source.scan}` etc. are
rendered from the module's own `LEGACY = Source(...)` / `CIS = Source(...)` call (kind "fstring_src"); the cis
search then runs `topk_sql` / `exact_sql` with `source=CIS`, and the old `browse.search.CIS_SEARCH_SQL` (exact
aggregate, before 6c) becomes optional. The generator works on both shapes.
"""
from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path

BEGIN = "# BEGIN GENERATED READERS"
END = "# END GENERATED READERS"

# (key in READERS, file under backend/, how to find it)
#   ("const", NAME)             module-level NAME = "..."
#   ("format", NAME, {k: v})    module-level NAME = "...".format(**{k: v})
#   ("fstring", FUNC, n, subs)  the n-th f-string inside function FUNC, {expr} -> subs[ast.unparse(expr)]
TOPK_SUBS = {"cols": "od.id, od.name, od.lat, od.lng", "scan_where": "c.embedding IS NOT NULL",
             "keep_where": "<ACTIVE_TOUR_SQL>", "k_param": "2", "int(limit)": "60", "key": "od.id"}
EXACT_SUBS = {"cols": "d.id, d.name, d.lat, d.lng", "scan_where": "c.embedding IS NOT NULL",
              "keep_where": "<ACTIVE_TOUR_SQL>", "int(limit)": "60", "key": "d.id", "group": "d.id, d.name, d.lat, d.lng"}
# 6c: the cis search (browse.search CIS_DEST_COLS, no country filter, no keep_where: the views are live-only)
TOPK_CIS_SUBS = {"cols": "od.destination_id AS id, od.name, od.lat, od.lng, od.located_by, od.precision",
                 "scan_where": "c.embedding IS NOT NULL", "keep_where": "", "k_param": "2", "int(limit)": "60",
                 "key": "od.destination_id"}
EXACT_CIS_SUBS = {"cols": "d.destination_id AS id, d.name, d.lat, d.lng, d.located_by, d.precision",
                  "group": "d.destination_id, d.name, d.lat, d.lng, d.located_by, d.precision",
                  "scan_where": "c.embedding IS NOT NULL", "keep_where": "", "int(limit)": "60",
                  "key": "d.destination_id"}
SPECS = [
    ("browse.countries.COUNTRIES_SQL", "browse/countries.py", ("const", "COUNTRIES_SQL")),
    ("browse.countries.COUNTRIES_SQL_CIS", "browse/countries.py", ("const", "COUNTRIES_SQL_CIS")),
    ("browse.countries.COUNTRY_DESTINATIONS_SQL", "browse/countries.py", ("const", "COUNTRY_DESTINATIONS_SQL")),
    ("browse.countries.COUNTRY_DESTINATIONS_SQL_CIS", "browse/countries.py",
     ("const", "COUNTRY_DESTINATIONS_SQL_CIS")),
    ("browse.destinations.DEST_SQL", "browse/destinations.py", ("const", "DEST_SQL")),
    ("browse.destinations.DEST_SQL_CIS", "browse/destinations.py", ("const", "DEST_SQL_CIS")),
    ("browse.destinations.COMPONENTS_SQL", "browse/destinations.py", ("const", "COMPONENTS_SQL")),
    ("browse.destinations.COMPONENTS_SQL_CIS", "browse/destinations.py", ("const", "COMPONENTS_SQL_CIS")),
    # tiles without filters (the map's default): the cis f-string comes first in build_tile_query
    ("browse.tiles.TILE_SQL_CIS", "browse/tiles.py", ("fstring", "build_tile_query", 0, {"where_frag": ""})),
    ("browse.tiles.TILE_SQL", "browse/tiles.py", ("fstring", "build_tile_query", 1, {"where_frag": ""})),
    ("browse.routes.SINGLE_SQL", "browse/routes.py", ("const", "SINGLE_SQL")),
    ("browse.routes.SINGLE_SQL_CIS", "browse/routes.py", ("const", "SINGLE_SQL_CIS")),
    ("browse.routes.CHAIN_SQL", "browse/routes.py", ("const", "CHAIN_SQL")),
    ("browse.routes.CHAIN_SQL_CIS", "browse/routes.py", ("const", "CHAIN_SQL_CIS")),
    ("browse.routes.DAYS_SQL", "browse/routes.py", ("const", "DAYS_SQL")),
    ("browse.routes.DAYS_SQL_CIS", "browse/routes.py", ("const", "DAYS_SQL_CIS")),
    ("browse.routes.COMPONENTS_SQL", "browse/routes.py", ("const", "COMPONENTS_SQL")),
    ("browse.routes.COMPONENTS_SQL_CIS", "browse/routes.py", ("const", "COMPONENTS_SQL_CIS")),
    ("browse.routes.TOUR_NAMES_SQL", "browse/routes.py", ("const", "TOUR_NAMES_SQL")),
    ("browse.routes.TOURS_BY_SOURCE_SQL", "browse/routes.py", ("const", "TOURS_BY_SOURCE_SQL")),
    ("browse.routes.SOURCE_BY_TOUR_SQL", "browse/routes.py", ("const", "SOURCE_BY_TOUR_SQL")),
    ("browse.routes.TOUR_TITLE_SQL", "browse/routes.py", ("const", "TOUR_TITLE_SQL")),
    ("browse.routes.TOUR_ROUTE_PLACES_SQL", "browse/routes.py", ("const", "TOUR_ROUTE_PLACES_SQL")),
    ("browse.routes.PLACE_COMPONENTS_SQL", "browse/routes.py", ("const", "PLACE_COMPONENTS_SQL")),
    ("browse.routes.PLACE_COMPONENTS_SQL_CIS", "browse/routes.py", ("const", "PLACE_COMPONENTS_SQL_CIS")),
    ("browse.routes.TOUR_DAYS_COUNT_SQL", "browse/routes.py", ("const", "TOUR_DAYS_COUNT_SQL")),
    ("browse.search.ACTIVE_TOUR_SQL", "browse/search.py", ("const", "ACTIVE_TOUR_SQL")),
    ("shared.vector_topk.TOPK_SQL", "shared/vector_topk.py", ("fstring_src", "topk_sql", 0, TOPK_SUBS, "LEGACY")),
    ("shared.vector_topk.EXACT_SQL", "shared/vector_topk.py", ("fstring_src", "exact_sql", 0, EXACT_SUBS, "LEGACY")),
]
# Optional readers: copied when the source has them, skipped (and listed in READERS_ABSENT) otherwise.
#   before 6c: the cis search was the exact aggregate CIS_SEARCH_SQL;
#   from 6c (AA-847): the cis search is vector_topk with source=CIS, and the assembly readers have cis twins.
OPTIONAL_SPECS = [
    ("browse.search.CIS_SEARCH_SQL", "browse/search.py",
     ("format", "CIS_SEARCH_SQL", {"where_frag": "", "limit": "60"})),
    ("shared.vector_topk.TOPK_SQL_CIS", "shared/vector_topk.py", ("fstring_src", "topk_sql", 0, TOPK_CIS_SUBS, "CIS")),
    ("shared.vector_topk.EXACT_SQL_CIS", "shared/vector_topk.py",
     ("fstring_src", "exact_sql", 0, EXACT_CIS_SUBS, "CIS")),
    ("shared.component_ids.MAP_SQL", "shared/component_ids.py", ("const", "MAP_SQL")),
    ("assembly.events.COMPONENTS_SQL", "assembly/events.py", ("const", "COMPONENTS_SQL")),
    ("assembly.events.COMPONENTS_SQL_CIS", "assembly/events.py", ("const", "COMPONENTS_SQL_CIS")),
    ("assembly.coverage.OPTIONS_SQL", "assembly/coverage.py", ("const", "OPTIONS_SQL")),
    ("assembly.coverage.OPTIONS_SQL_CIS", "assembly/coverage.py", ("const", "OPTIONS_SQL_CIS")),
    ("assembly.activities.ACTIVITIES_SQL", "assembly/activities.py", ("const", "ACTIVITIES_SQL")),
    ("assembly.activities.ACTIVITIES_SQL_CIS", "assembly/activities.py", ("const", "ACTIVITIES_SQL_CIS")),
    ("assembly.suggestions.TASTE_SQL", "assembly/suggestions.py", ("const", "TASTE_SQL")),
    ("assembly.suggestions.TASTE_SQL_CIS", "assembly/suggestions.py", ("const", "TASTE_SQL_CIS")),
    ("assembly.suggestions.ROUTE_CANDIDATES_SQL", "assembly/suggestions.py", ("const", "ROUTE_CANDIDATES_SQL")),
    ("assembly.suggestions.ROUTE_CANDIDATES_SQL_CIS", "assembly/suggestions.py",
     ("const", "ROUTE_CANDIDATES_SQL_CIS")),
]


def _module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _const_node(mod: ast.Module, name: str):
    for node in mod.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return node.value
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            return node.value
    return None


def _source_subs(mod: ast.Module, name: str):
    """{"source.scan": …, "source.exact": …, "source.destinations": …, "source.dest_id": …} from the module's
    ``NAME = Source(...)`` call (6c), or None when the module has no such call (before 6c)."""
    node = _const_node(mod, name)
    if not (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "Source"):
        return None
    out = {}
    for kw in node.keywords:
        out[f"source.{kw.arg}"] = _render(kw.value, {}, f"{name}.{kw.arg}", mod)
    return out


def _render(node, subs: dict, where: str, mod: ast.Module = None) -> str:
    """A string constant or an f-string; `{NAME}` of another module-level string constant (e.g. suggestions.py
    _KM_SQL) is rendered from that constant when `subs` has no entry for it."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = []
        for part in node.values:
            if isinstance(part, ast.Constant):
                out.append(part.value)
            else:
                key = ast.unparse(part.value)
                if key in subs:
                    out.append(subs[key])
                elif mod is not None and isinstance(part.value, ast.Name) and _const_node(mod, key) is not None:
                    out.append(_render(_const_node(mod, key), subs, f"{where}.{key}", mod))
                else:
                    raise SystemExit(f"{where}: no substitution for {{{key}}}")
        return "".join(out)
    raise SystemExit(f"{where}: not a string constant or f-string ({type(node).__name__})")


def extract(backend: Path, key: str, rel: str, how: tuple, optional: bool = False):
    path = backend / rel
    if not path.exists():
        if optional:
            return None
        raise SystemExit(f"{key}: {path} missing")
    mod = _module(path)
    kind = how[0]
    if kind in ("const", "format"):
        node = _const_node(mod, how[1])
        if node is None:
            if optional:
                return None
            raise SystemExit(f"{key}: {how[1]} not found in {rel}")
        text = _render(node, {}, key, mod)
        if kind == "format":
            text = text.format(**how[2])
        return text
    if kind == "fstring_src":
        src = _source_subs(mod, how[4])
        if src is None:
            if how[4] != "LEGACY":
                return None if optional else _fail(f"{key}: no {how[4]} = Source(...) in {rel}")
            src = {}                            # before 6c: the f-string names its tables itself
        how = ("fstring", how[1], how[2], {**how[3], **src})
        kind = "fstring"
    if kind == "fstring":
        func = next((n for n in ast.walk(mod) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and n.name == how[1]), None)
        if func is None:
            if optional:
                return None
            raise SystemExit(f"{key}: function {how[1]} not found in {rel}")
        fstrings = sorted((n for n in ast.walk(func) if isinstance(n, ast.JoinedStr)
                           and any(isinstance(v, ast.Constant) and "SELECT" in v.value for v in n.values)),
                          key=lambda n: (n.lineno, n.col_offset))     # source order, not ast.walk's

        if len(fstrings) <= how[2]:
            raise SystemExit(f"{key}: f-string #{how[2]} not found in {how[1]}")
        return _render(fstrings[how[2]], how[3], key)
    raise SystemExit(f"{key}: unknown spec {kind}")


def _fail(msg: str):
    raise SystemExit(msg)


def _literal(text: str) -> str:
    if '"""' not in text and not text.endswith("\\") and "\\" not in text:
        return '"""' + text + '"""'
    return repr(text)


def generate(tp: Path) -> str:
    backend = tp / "backend"
    sha = subprocess.run(["git", "-C", str(tp), "rev-parse", "--short=12", "HEAD"], capture_output=True,
                         text=True, check=True).stdout.strip()
    readers, missing = {}, []
    for key, rel, how in SPECS:
        readers[key] = extract(backend, key, rel, how)
    for key, rel, how in OPTIONAL_SPECS:
        text = extract(backend, key, rel, how, optional=True)
        if text is None:
            missing.append(key)
        else:
            readers[key] = text
    lines = [f"{BEGIN} (root docs/audits/2026-10-21-S246-aa847/gen_probe_sql.py; do not edit by hand)",
             f'READERS_FROM = "AA-TripPlanner-Web@{sha}"',
             f"READERS_ABSENT = {sorted(missing)!r}",
             "READERS = {"]
    for key in sorted(readers):
        lines.append(f"    {key!r}: {_literal(readers[key])},")
    lines += ["}", END]
    return "\n".join(lines)


def splice(probe_text: str, block: str) -> str:
    start = probe_text.index(BEGIN)
    end = probe_text.index(END) + len(END)
    return probe_text[:start] + block + probe_text[end:]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tp", required=True, type=Path, help="AA-TripPlanner-Web checkout")
    ap.add_argument("--probe", required=True, type=Path, help="AA-CIS-Infra db/scripts/aa847_places_probe.py")
    ap.add_argument("--check", action="store_true", help="exit 1 when the probe block is out of date")
    a = ap.parse_args(argv)
    block = generate(a.tp)
    text = a.probe.read_text(encoding="utf-8")
    new = splice(text, block)
    if a.check:
        if new != text:
            print("probe reader block is out of date: re-run without --check", file=sys.stderr)
            return 1
        print("probe reader block is up to date")
        return 0
    a.probe.write_text(new, encoding="utf-8")
    print(f"wrote {len(block.splitlines())} lines into {a.probe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
