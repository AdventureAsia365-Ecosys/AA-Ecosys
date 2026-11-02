"""Public diagram sketches (AA-1021): a small hand-built diagram per episode, drawn here as SVG.

  python -I sketch.py <sketch.json> <out.svg>          # render one sketch on its own (to look at it)

Why not the committed architecture SVGs: a relabelled copy of docs/architecture/diagrams/*.svg keeps every node
position, icon, frame and arrow route of a figure that is public in this repo, so a viewer (or a reverse image search)
can match a frame to the repo whatever the words say. A sketch is authored per episode, kept OUTSIDE git with the
episode file, simplified to what the episode says, and laid out on its own grid; every label in it is authored text
and goes through the whole layer 1 check (deny-list, identifier shapes, n-gram and internal-token check, label set).

Format (the value of one "diagrams" entry of the episode file; an invented example: sketch.example.json):
  {"groups": [{"id": "base", "label": "Shared base", "sub": "one region", "cells": [c0, r0, c1, r1],
               "style": "solid" | "dashed"}],                     a frame around grid cells c0..c1 x r0..r1 (inclusive)
   "nodes":  [{"id": "cat", "label": "Catalogue app", "sub": "api + workers" | ["line", "line"],
               "at": [col, row], "kind": "service" | "store" | "people" | "external"}],
   "edges":  [{"from": "cat", "to": "db", "label": "SQL", "style": "solid" | "dashed", "bend": 0.5}]}
An edge between two rows runs down, across, down; "bend" (0.1-0.9, default 0.5) sets where the cross run sits in the
gap, so two edges that would share a run can be kept apart.
Groups nest by their cells (a group inside another must sit strictly within its cells, or share no cell with it).

The SVG has the structure page.py drives (the same as a Graphviz SVG): g.graph > g.cluster / g.node / g.edge, every
label a direct <text> child, node keys data-k="n<i>" (never the authored ids), edges data-from / data-to. No <title>,
<desc>, link, image or font reference. Stdlib only.
"""
from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path

CELL_W, NODE_W = 264, 216
LINE_H, SUB_H = 22, 17
NODE_PAD_Y = 14
TITLE_BAND = 26
PAD = 18
GROUP_INSET = 10
KINDS = {"service", "store", "people", "external"}
INK, BODY, MUTED, LINE, CARD = "#16202B", "#3B4754", "#66727F", "#8A97A6", "#FFFFFF"
GROUP_STROKE = "#C5CED8"


class SketchError(ValueError):
    pass


def _lines(v) -> list[str]:
    if v is None:
        return []
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


def validate(spec: dict, key: str = "sketch") -> list[str]:
    """Every problem in one sketch (empty list = valid)."""
    if not isinstance(spec, dict):
        return [f"diagram {key}: must be a sketch object (groups / nodes / edges), not {type(spec).__name__}"]
    problems = []
    nodes, groups, edges = spec.get("nodes") or [], spec.get("groups") or [], spec.get("edges") or []
    if not nodes:
        problems.append(f"diagram {key}: no nodes")
    ids, cells = set(), {}
    for n in nodes:
        nid = n.get("id")
        if not nid or nid in ids:
            problems.append(f"diagram {key}: node id {nid!r} missing or repeated")
        ids.add(nid)
        if not str(n.get("label", "")).strip():
            problems.append(f"diagram {key}: node {nid} has no label")
        at = n.get("at")
        if not (isinstance(at, list) and len(at) == 2 and all(isinstance(x, int) and x >= 0 for x in at)):
            problems.append(f"diagram {key}: node {nid} needs at: [col, row] (integers >= 0)")
        elif tuple(at) in cells:
            problems.append(f"diagram {key}: nodes {cells[tuple(at)]} and {nid} share cell {at}")
        else:
            cells[tuple(at)] = nid
        if n.get("kind", "service") not in KINDS:
            problems.append(f"diagram {key}: node {nid} kind must be one of {sorted(KINDS)}")
    gids, framed = set(), []
    for g in groups:
        gid = g.get("id")
        if not gid or gid in gids or gid in ids:
            problems.append(f"diagram {key}: group id {gid!r} missing or repeated")
        gids.add(gid)
        if not str(g.get("label", "")).strip():
            problems.append(f"diagram {key}: group {gid} has no label")
        c = g.get("cells")
        if not (isinstance(c, list) and len(c) == 4 and all(isinstance(x, int) and x >= 0 for x in c)
                and c[0] <= c[2] and c[1] <= c[3]):
            problems.append(f"diagram {key}: group {gid} needs cells: [c0, r0, c1, r1] with c0 <= c1, r0 <= r1")
        else:
            framed.append(g)
    for i, a in enumerate(framed):
        for b in framed[i + 1:]:
            if _overlap(a["cells"], b["cells"]) and not (_within(a["cells"], b["cells"]) or
                                                         _within(b["cells"], a["cells"])):
                problems.append(f"diagram {key}: groups {a['id']} and {b['id']} overlap without nesting")
            elif a["cells"] == b["cells"]:
                problems.append(f"diagram {key}: groups {a['id']} and {b['id']} cover the same cells")
    for e in edges:
        for end in ("from", "to"):
            if e.get(end) not in ids:
                problems.append(f"diagram {key}: edge {end} {e.get(end)!r} is not a node id")
        if e.get("from") == e.get("to"):
            problems.append(f"diagram {key}: edge from {e.get('from')} to itself")
        bend = e.get("bend", 0.5)
        if not (isinstance(bend, (int, float)) and 0.1 <= bend <= 0.9):
            problems.append(f"diagram {key}: edge {e.get('from')} -> {e.get('to')} bend must be 0.1-0.9")
    return problems


def _overlap(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _within(inner, outer) -> bool:
    return outer[0] <= inner[0] and outer[1] <= inner[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def labels(spec: dict) -> list[str]:
    """Every text a sketch shows (layer 1 input; make_episode also re-reads the rendered SVG)."""
    out = []
    for item in (spec.get("groups") or []) + (spec.get("nodes") or []):
        out += [str(item.get("label", ""))] + _lines(item.get("sub"))
    for e in spec.get("edges") or []:
        out += _lines(e.get("label"))
    return [x for x in out if x.strip()]


STORE_TOP = 10          # extra room under a store's lid


def _node_h(n: dict) -> float:
    lid = STORE_TOP if n.get("kind") == "store" else 0
    return 2 * NODE_PAD_Y + LINE_H + SUB_H * len(_lines(n.get("sub"))) + lid


def _layout(spec: dict):
    nodes, groups = spec.get("nodes") or [], spec.get("groups") or []
    cols = 1 + max([n["at"][0] for n in nodes] + [g["cells"][2] for g in groups])
    rows = 1 + max([n["at"][1] for n in nodes] + [g["cells"][3] for g in groups])
    depth = {g["id"]: sum(1 for o in groups if o is not g and _within(g["cells"], o["cells"])) for g in groups}
    starts = {r: sorted((g for g in groups if g["cells"][1] == r), key=lambda g: depth[g["id"]]) for r in range(rows)}
    ends = {r: [g for g in groups if g["cells"][3] == r] for r in range(rows)}
    body = {r: max([_node_h(n) for n in nodes if n["at"][1] == r] + [LINE_H + 2 * NODE_PAD_Y]) for r in range(rows)}
    head = {r: TITLE_BAND * len(starts[r]) + sum(SUB_H for g in starts[r] if _lines(g.get("sub"))) for r in range(rows)}
    tail = {r: GROUP_INSET * (1 + max([depth[g["id"]] for g in ends[r]], default=0)) for r in range(rows)}
    y, row_y = PAD, {}
    for r in range(rows):
        row_y[r] = y
        y += head[r] + 22 + body[r] + 22 + tail[r]
    height = y + PAD
    width = 2 * PAD + cols * CELL_W
    box = {}
    for r in range(rows):
        top = row_y[r]
        for k, g in enumerate(starts[r]):
            box[g["id"]] = {"top": top}
            top += TITLE_BAND + (SUB_H if _lines(g.get("sub")) else 0)
    for g in groups:
        d = depth[g["id"]]
        c0, r0, c1, r1 = g["cells"]
        x0 = PAD + c0 * CELL_W + 4 + GROUP_INSET * d
        x1 = PAD + (c1 + 1) * CELL_W - 4 - GROUP_INSET * d
        y0 = box[g["id"]]["top"]
        y1 = row_y[r1] + head[r1] + 22 + body[r1] + 22 + tail[r1] - GROUP_INSET * (1 + d) + 4
        box[g["id"]] = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0, "depth": d}
    nbox = {}
    for n in nodes:
        c, r = n["at"]
        h = _node_h(n)
        x = PAD + c * CELL_W + (CELL_W - NODE_W) / 2
        y = row_y[r] + head[r] + 22 + (body[r] - h) / 2
        nbox[n["id"]] = {"x": x, "y": y, "w": NODE_W, "h": h}
    return width, height, box, nbox


def _t(x, y, text, size, weight=400, fill=INK, anchor="middle", halo=False) -> str:
    ring = f' paint-order="stroke" stroke="{CARD}" stroke-width="5" stroke-linejoin="round"' if halo else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}"{ring}>{escape(text, quote=False)}</text>')


def _shape(n: dict, b: dict) -> str:
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    kind = n.get("kind", "service")
    if kind == "store":
        ry = 9
        return (f'<path d="M{x:.1f},{y + ry:.1f} a{w / 2:.1f},{ry} 0 0,1 {w:.1f},0 v{h - 2 * ry:.1f} '
                f'a{w / 2:.1f},{ry} 0 0,1 {-w:.1f},0 z" fill="{CARD}" stroke="{LINE}" stroke-width="1.6"/>'
                f'<path d="M{x:.1f},{y + ry:.1f} a{w / 2:.1f},{ry} 0 0,0 {w:.1f},0" fill="none" stroke="{LINE}" '
                f'stroke-width="1.6"/>')
    rx = h / 2 if kind == "people" else 12
    dash = ' stroke-dasharray="6 5"' if kind == "external" else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" ry="{rx:.1f}" '
            f'fill="{CARD}" stroke="{LINE}" stroke-width="1.6"{dash}/>')


def _route(a: dict, b: dict, bend: float = 0.5) -> list[tuple[float, float]]:
    """An orthogonal path from box a to box b: straight when they share a row or a column, else one elbow pair."""
    acx, acy = a["x"] + a["w"] / 2, a["y"] + a["h"] / 2
    bcx, bcy = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
    if abs(acy - bcy) < 1:
        sx = a["x"] + a["w"] if bcx > acx else a["x"]
        ex = b["x"] if bcx > acx else b["x"] + b["w"]
        return [(sx, acy), (ex, bcy)]
    down = bcy > acy
    sy = a["y"] + a["h"] if down else a["y"]
    ey = b["y"] if down else b["y"] + b["h"]
    if abs(acx - bcx) < 1:
        return [(acx, sy), (bcx, ey)]
    mid = sy + (ey - sy) * bend
    return [(acx, sy), (acx, mid), (bcx, mid), (bcx, ey)]


def _arrow(p: tuple, q: tuple) -> str:
    (x0, y0), (x1, y1) = p, q
    L, W = 9, 4.5
    if abs(x1 - x0) > abs(y1 - y0):
        s = 1 if x1 > x0 else -1
        pts = [(x1, y1), (x1 - s * L, y1 - W), (x1 - s * L, y1 + W)]
    else:
        s = 1 if y1 > y0 else -1
        pts = [(x1, y1), (x1 - W, y1 - s * L), (x1 + W, y1 - s * L)]
    return '<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + f'" fill="{BODY}"/>'


def render(spec: dict, key: str = "sketch") -> str:
    problems = validate(spec, key)
    if problems:
        raise SketchError("; ".join(problems))
    width, height, gbox, nbox = _layout(spec)
    keys = {n["id"]: f"n{i}" for i, n in enumerate(spec["nodes"], 1)}
    # Paint order: edges, then the group frames (no fill; their titles keep a halo so an arrow passes behind a title,
    # never through it), then the nodes.
    parts, frames = [], []
    for g in sorted(spec.get("groups") or [], key=lambda g: gbox[g["id"]]["depth"]):
        b = gbox[g["id"]]
        dash = ' stroke-dasharray="7 6"' if g.get("style") == "dashed" else ""
        body = [f'<rect x="{b["x"]:.1f}" y="{b["y"]:.1f}" width="{b["w"]:.1f}" height="{b["h"]:.1f}" rx="14" ry="14" '
                f'fill="none" stroke="{GROUP_STROKE}" stroke-width="1.4"{dash}/>',
                _t(b["x"] + 16, b["y"] + 21, str(g["label"]), 14, 600, BODY, "start", halo=True)]
        for sub in _lines(g.get("sub"))[:1]:
            body.append(_t(b["x"] + 16, b["y"] + 21 + SUB_H, sub, 12, 400, MUTED, "start", halo=True))
        frames.append('<g class="cluster">' + "".join(body) + "</g>")
    for e in spec.get("edges") or []:
        pts = _route(nbox[e["from"]], nbox[e["to"]], float(e.get("bend", 0.5)))
        dash = ' stroke-dasharray="6 5"' if e.get("style") == "dashed" else ""
        path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        body = [f'<path d="{path}" fill="none" stroke="{BODY}" stroke-width="1.6"{dash}/>', _arrow(pts[-2], pts[-1])]
        lab = _lines(e.get("label"))
        if lab:
            i = max(range(len(pts) - 1), key=lambda k: abs(pts[k + 1][0] - pts[k][0]) + abs(pts[k + 1][1] - pts[k][1]))
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            for j, line in enumerate(lab):
                body.append(_t(mx + (8 if x0 == x1 else 0), my - 6 + j * 14, line, 12, 400, MUTED,
                               "start" if x0 == x1 else "middle", halo=True))
        ends = f'data-from="{keys[e["from"]]}" data-to="{keys[e["to"]]}"'
        parts.append(f'<g class="edge" {ends}>' + "".join(body) + "</g>")
    parts += frames
    for n in spec["nodes"]:
        b = nbox[n["id"]]
        cx = b["x"] + b["w"] / 2
        y = b["y"] + NODE_PAD_Y + 16 + (STORE_TOP if n.get("kind") == "store" else 0)
        body = [_shape(n, b), _t(cx, y, str(n["label"]), 14.5, 600)]
        for j, sub in enumerate(_lines(n.get("sub")), 1):
            body.append(_t(cx, y + 4 + j * SUB_H, sub, 12, 400, MUTED))
        parts.append(f'<g class="node" data-k="{keys[n["id"]]}">' + "".join(body) + "</g>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" '
            f'viewBox="0 0 {width:.0f} {height:.0f}" preserveAspectRatio="xMidYMid meet">'
            f'<g class="graph">' + "".join(parts) + "</g></svg>")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    Path(argv[1]).write_text(render(json.loads(Path(argv[0]).read_text(encoding="utf-8")), Path(argv[0]).stem),
                             encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
