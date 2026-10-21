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

TripPlanner slice 6d (AA-847, CIS 256 line places) builds reader SQL from shared constants: `LINE_COLS_SQL` imported
from browse/tiles.py, `{", ".join(LINE_COLS)}` inside an f-string, and `"..." + LINE_COLS_SQL + "..."`. A small static
evaluator renders these (string/tuple constants, `+`, `"sep".join(<tuple or plain generator expression>)`, names
imported `from backend.<module> import NAME`); anything else still fails loudly. A name bound inside the function of
an f-string must come from its substitutions, never from a same-named module constant. The cis search columns are
taken from browse/search.py `CIS_DEST_COLS` (6d adds the line columns) when the module has it.
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
# 6c: the cis search (browse.search CIS_DEST_COLS, no country filter, no keep_where: views hide dead tours, unusable places)
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


def _source_subs(mod: ast.Module, name: str, backend: Path = None):
    """{"source.scan": …, "source.exact": …, "source.destinations": …, "source.dest_id": …} from the module's
    ``NAME = Source(...)`` call (6c), or None when the module has no such call (before 6c)."""
    node = _const_node(mod, name)
    if not (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "Source"):
        return None
    out = {}
    for kw in node.keywords:
        out[f"source.{kw.arg}"] = _render(kw.value, {}, f"{name}.{kw.arg}", mod, backend)
    return out


def _imported(mod: ast.Module, name: str, backend: Path):
    """(module, path) of ``from backend.x.y import NAME`` in ``mod`` when x/y.py exists under ``backend``, else None.
    TripPlanner slice 6d (AA-847) shares LINE_COLS / LINE_COLS_SQL from browse/tiles.py this way."""
    if backend is None:
        return None
    for node in mod.body:
        if isinstance(node, ast.ImportFrom) and node.level == 0 and (node.module or "").startswith("backend."):
            for alias in node.names:
                if (alias.asname or alias.name) == name:
                    path = backend.joinpath(*node.module.split(".")[1:]).with_suffix(".py")
                    if path.exists():
                        return _module(path), alias.name
    return None


def _value(node, subs: dict, where: str, mod: ast.Module = None, backend: Path = None, local=frozenset(),
           env=None):
    """Statically evaluate a str or a tuple of str: a string constant, an f-string, a tuple/list, ``a + b``,
    ``"sep".join(<tuple or generator expression>)``, a Name (a comprehension variable, a module-level constant, or a
    constant imported from another backend module). Nothing is imported or executed. A Name in ``local`` (assigned
    inside the function the f-string is in) must come from ``subs``: a local never falls back to a module constant."""
    env = env or {}
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out = []
        for part in node.values:
            if isinstance(part, ast.Constant):
                out.append(part.value)
                continue
            if part.conversion != -1 or part.format_spec is not None:
                raise SystemExit(f"{where}: conversion / format spec in {{{ast.unparse(part.value)}}}")
            key = ast.unparse(part.value)
            if key in subs:
                out.append(subs[key])
                continue
            val = _value(part.value, subs, f"{where}.{{{key}}}", mod, backend, local, env)
            if not isinstance(val, str):
                raise SystemExit(f"{where}: {{{key}}} is not a string")
            out.append(val)
        return "".join(out)
    if isinstance(node, (ast.Tuple, ast.List)):
        items = tuple(_value(e, subs, where, mod, backend, local, env) for e in node.elts)
        if not all(isinstance(i, str) for i in items):
            raise SystemExit(f"{where}: a tuple of non-strings")
        return items
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a = _value(node.left, subs, where, mod, backend, local, env)
        b = _value(node.right, subs, where, mod, backend, local, env)
        if type(a) is not type(b):
            raise SystemExit(f"{where}: {type(a).__name__} + {type(b).__name__}")
        return a + b
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "join"
            and len(node.args) == 1 and not node.keywords):
        sep = _value(node.func.value, subs, where, mod, backend, local, env)
        arg = node.args[0]
        if isinstance(arg, (ast.GeneratorExp, ast.ListComp)):
            if (len(arg.generators) != 1 or arg.generators[0].ifs or arg.generators[0].is_async
                    or not isinstance(arg.generators[0].target, ast.Name)):
                raise SystemExit(f"{where}: only a plain `for x in <tuple>` comprehension is supported")
            gen = arg.generators[0]
            seq = _value(gen.iter, subs, where, mod, backend, local, env)
            items = tuple(_value(arg.elt, subs, where, mod, backend, local, {**env, gen.target.id: s}) for s in seq)
        else:
            items = _value(arg, subs, where, mod, backend, local, env)
        if not isinstance(sep, str) or not isinstance(items, tuple) or not all(isinstance(i, str) for i in items):
            raise SystemExit(f"{where}: join of non-strings")
        return sep.join(items)
    if isinstance(node, ast.Name):
        name = node.id
        if name in env:
            return env[name]
        if mod is not None and name not in local:
            const = _const_node(mod, name)
            if const is not None:
                return _value(const, subs, f"{where}.{name}", mod, backend)
            imp = _imported(mod, name, backend)
            if imp is not None:
                other, real = imp
                const = _const_node(other, real)
                if const is not None:
                    return _value(const, subs, f"{where}.{name}", other, backend)
        raise SystemExit(f"{where}: no substitution for {{{name}}}")
    raise SystemExit(f"{where}: no substitution for {{{ast.unparse(node)}}} ({type(node).__name__})")


def _render(node, subs: dict, where: str, mod: ast.Module = None, backend: Path = None, local=frozenset()) -> str:
    """A string constant or an f-string (also ``"..." + NAME + "..."``); `{NAME}` of another module-level string
    constant (e.g. suggestions.py _KM_SQL), or one imported from another backend module (6d: tiles.py
    LINE_COLS_SQL), is rendered from that constant when `subs` has no entry for it."""
    text = _value(node, subs, where, mod, backend, local)
    if not isinstance(text, str):
        raise SystemExit(f"{where}: not a string constant or f-string ({type(node).__name__})")
    return text


def _locals(func) -> frozenset:
    """Names bound inside a function (arguments and assignment targets)."""
    names = {a.arg for a in ast.walk(func.args) if isinstance(a, ast.arg)}
    names |= {n.id for n in ast.walk(func) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    return frozenset(names)


def _dest_select(alias: str, cols, dest_id: str) -> tuple[str, str]:
    """TripPlanner vector_topk._dest_select: (select list, group-by list); ``id`` is the destination key."""
    sel, grp = [], []
    for c in cols:
        expr = f"{alias}.{dest_id}" if c == "id" else f"{alias}.{c}"
        sel.append(f"{expr} AS {c}" if c == "id" and dest_id != "id" else expr)
        grp.append(expr)
    return ", ".join(sel), ", ".join(grp)


def cis_search_subs(backend: Path) -> dict:
    """The cis search's destination columns as browse.search passes them (``CIS_DEST_COLS``; 6d adds the line
    columns of CIS 256). Before 6d the module has no such constant and the hard-coded 6c columns stay."""
    path = backend / "browse" / "search.py"
    if not path.exists():
        return {}
    mod = _module(path)
    node = _const_node(mod, "CIS_DEST_COLS")
    if node is None:
        return {}
    cols = _value(node, {}, "browse.search.CIS_DEST_COLS", mod, backend)
    if not isinstance(cols, tuple):
        raise SystemExit("browse.search.CIS_DEST_COLS: not a tuple of strings")
    od, _ = _dest_select("od", cols, "destination_id")
    d, group = _dest_select("d", cols, "destination_id")
    return {"shared.vector_topk.TOPK_SQL_CIS": {"cols": od},
            "shared.vector_topk.EXACT_SQL_CIS": {"cols": d, "group": group}}


def extract(backend: Path, key: str, rel: str, how: tuple, optional: bool = False, extra: dict = None):
    """``extra`` overrides the spec's f-string substitutions (cis_search_subs: the 6d cis search columns)."""
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
        text = _render(node, {}, key, mod, backend)
        if kind == "format":
            text = text.format(**how[2])
        return text
    if kind == "fstring_src":
        src = _source_subs(mod, how[4], backend)
        if src is None:
            if how[4] != "LEGACY":
                return None if optional else _fail(f"{key}: no {how[4]} = Source(...) in {rel}")
            src = {}                            # before 6c: the f-string names its tables itself
        how = ("fstring", how[1], how[2], {**how[3], **src, **(extra or {})})
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
        return _render(fstrings[how[2]], how[3], key, mod, backend, _locals(func))
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
    cis_subs = cis_search_subs(backend)
    for key, rel, how in SPECS:
        readers[key] = extract(backend, key, rel, how)
    for key, rel, how in OPTIONAL_SPECS:
        text = extract(backend, key, rel, how, optional=True, extra=cis_subs.get(key))
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
