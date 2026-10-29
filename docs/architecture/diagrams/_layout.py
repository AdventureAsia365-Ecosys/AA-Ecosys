"""Grid layout, orthogonal arrow routing and the Graphviz output of the architecture views (AA-697).

Graphviz ``dot`` decides the order of nodes inside a rank by itself, ignores groups when it routes orthogonal edges
and puts edge labels on the lines. An AWS reference diagram is drawn on a grid instead, so the views place each
service on a grid cell (``place``) and this module does the rest, deterministically:

1. ``layout``: column and row positions from the widest icon-plus-text of each column and row, plus room for every
   group border and group title that falls between two columns or rows; group boxes from their members.
2. ``route``: each arrow is a shortest path on a 6 pt grid (A*) that never enters an icon, a text, a group title or a
   group neither of its ends belongs to (unless no other way exists), avoids running along group borders or other
   arrows, and pays for every bend; it leaves an icon from a side and ends on a side (or on a group border).
3. ``place_edge_labels``: each arrow label goes beside the longest straight run of its own arrow, clear of everything.
4. The result is written as a laid-out Graphviz file that ``neato -n2`` draws as is (icons, HTML group titles, styles).

``layout_problems`` re-checks the drawing (an arrow through a node, a title or a foreign group, along a border, two
arrows on one track); ``render.py`` prints them, and a clean view prints none.
"""
from __future__ import annotations

import heapq
import math
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

S = 6                 # routing grid step, points
ICON = 58.0           # icon edge, points (0.8 in)
FONT = 12             # service text, points
LINE = FONT * 1.2
GAP_TEXT = 3          # icon bottom to its text
GAP_X = 46            # between two columns (plus group margins)
GAP_Y = 30            # between two rows (plus group margins)
GM = 18               # group margin (inside the border, around its members)
TITLE_H = 30          # group title band
TOP = 64              # view title band
PAD = 24
EDGE_FONT = 10
ARROW = 8             # arrowhead length
RUN = 3               # grid cells of straight run before a bend costs no extra
NEAR = 12             # clearance an arrow keeps from an icon that is not one of its ends
LEGEND_TEXTS: list[str] = []   # set by _common (the legend rows)

_DIRS = [(1, 0), (-1, 0), (0, -1), (0, 1)]   # E, W, N, S (y grows downwards)


@dataclass(eq=False)
class Group:
    key: str
    kind: str
    title: str
    note: str
    attrs: dict
    label: str
    parent: "Group | None"
    children: list = field(default_factory=list)
    nodes: list = field(default_factory=list)
    box: tuple = (0, 0, 0, 0)
    title_box: tuple = (0, 0, 0, 0)

    def chain(self) -> list["Group"]:
        out, g = [], self
        while g is not None:
            out.append(g)
            g = g.parent
        return out


@dataclass(eq=False)
class Node:
    id: str
    label: str
    attrs: dict
    group: Group | None
    cell: tuple | None = None
    x: float = 0.0
    y: float = 0.0
    legend: bool = False

    def text_size(self) -> tuple[float, float]:
        lines = self.label.split("\n")
        return max(len(s) for s in lines) * FONT * 0.56 + 8, len(lines) * LINE + 4

    def footprint(self) -> tuple[float, float]:
        if self.legend:
            return 70 + max(len(s) for s in LEGEND_TEXTS) * EDGE_FONT * 0.56 + 20, 104.0
        tw, th = self.text_size()
        return max(ICON, tw), ICON + GAP_TEXT + th

    def icon_box(self) -> tuple:
        if self.legend:
            w, h = self.footprint()
            return (self.x - w / 2, self.y - ICON / 2, self.x + w / 2, self.y - ICON / 2 + h)
        return (self.x - ICON / 2, self.y - ICON / 2, self.x + ICON / 2, self.y + ICON / 2)

    def text_box(self) -> tuple:
        tw, th = self.text_size()
        top = self.y + ICON / 2 + GAP_TEXT
        return (self.x - tw / 2, top, self.x + tw / 2, top + th)

    def full_box(self) -> tuple:
        if self.legend:
            return self.icon_box()
        a, b = self.icon_box(), self.text_box()
        return (min(a[0], b[0]), a[1], max(a[2], b[2]), b[3])

    def chain(self) -> list[Group]:
        return self.group.chain() if self.group else []


@dataclass(eq=False)
class Edge:
    src: object               # Node, or a Group with out_of
    dst: object               # Node, or a Group with into
    label: str
    attrs: dict
    pts: list = field(default_factory=list)


@dataclass(eq=False)
class View:
    title: str
    groups: list = field(default_factory=list)
    nodes: list = field(default_factory=list)
    edges: list = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0


# --- 1. layout -----------------------------------------------------------------------------------------------------


def _members(g: Group) -> list[Node]:
    out = list(g.nodes)
    for c in g.children:
        out += _members(c)
    return out


def layout(view: View) -> None:
    placed = [n for n in view.nodes if n.cell is not None]
    missing = [n.label.split("\n")[0] for n in view.nodes if n.cell is None]
    if missing:
        raise SystemExit(f"{view.title}: no grid cell for {missing}")
    seen: dict[tuple, str] = {}
    for n in placed:
        if n.cell in seen:
            raise SystemExit(f"{view.title}: cell {n.cell} holds both {seen[n.cell]!r} and {n.label!r}")
        seen[n.cell] = n.label
    cols = sorted({n.cell[0] for n in placed})
    rows = sorted({n.cell[1] for n in placed})
    colw = {c: max(n.footprint()[0] for n in placed if n.cell[0] == c) for c in cols}
    rowh = {r: max(n.footprint()[1] for n in placed if n.cell[1] == r) for r in rows}
    spans = {}
    for g in view.groups:
        m = _members(g)
        if m:
            spans[g] = (min(n.cell[0] for n in m), max(n.cell[0] for n in m),
                        min(n.cell[1] for n in m), max(n.cell[1] for n in m))
    # room for group borders between two columns (rows): the deepest stack of groups that end on one side or start on
    # the other, taken over the services of that column (row); a group title needs a band above its first row
    def chain_count(n, pred):
        return sum(1 for g in n.chain() if g in spans and pred(spans[g]))

    starts_c = {c: max(chain_count(n, lambda s, c=c: s[0] == c) for n in placed if n.cell[0] == c) for c in cols}
    ends_c = {c: max(chain_count(n, lambda s, c=c: s[1] == c) for n in placed if n.cell[0] == c) for c in cols}
    starts_r = {r: max(chain_count(n, lambda s, r=r: s[2] == r) for n in placed if n.cell[1] == r) for r in rows}
    ends_r = {r: max(chain_count(n, lambda s, r=r: s[3] == r) for n in placed if n.cell[1] == r) for r in rows}
    xs, x = {}, PAD
    for i, c in enumerate(cols):
        if i == 0:
            x += starts_c[c] * GM + colw[c] / 2
        else:
            p = cols[i - 1]
            x += colw[p] / 2 + GAP_X + (ends_c[p] + starts_c[c]) * GM + colw[c] / 2
        xs[c] = x
    ys, y = {}, TOP
    for i, r in enumerate(rows):
        if i == 0:
            y += starts_r[r] * (GM + TITLE_H)
        else:
            p = rows[i - 1]
            y += rowh[p] + GAP_Y + ends_r[p] * GM + starts_r[r] * (GM + TITLE_H)
        ys[r] = y
    for n in placed:
        n.x, n.y = xs[n.cell[0]], ys[n.cell[1]] + ICON / 2

    def box(g: Group) -> tuple:
        parts = [n.full_box() for n in g.nodes] + [box(c) for c in g.children]
        x1 = min(p[0] for p in parts) - GM
        y1 = min(p[1] for p in parts) - GM - TITLE_H
        x2 = max(p[2] for p in parts) + GM
        y2 = max(p[3] for p in parts) + GM
        tw = 24 + 8 + max(len(g.title) * 12 * 0.62, len(g.note) * 10 * 0.56)
        x2 = max(x2, x1 + tw + 16)
        g.box = (x1, y1, x2, y2)
        g.title_box = (x1 + 2, y1 + 2, x1 + 6 + tw, y1 + TITLE_H - 2)
        return g.box

    for g in view.groups:
        if g.parent is None:
            box(g)
    boxes = [n.full_box() for n in placed] + [g.box for g in view.groups if _members(g)]
    view.width = max(b[2] for b in boxes) + PAD
    view.height = max(b[3] for b in boxes) + PAD


# --- 2. routing ----------------------------------------------------------------------------------------------------


class _Grid:
    def __init__(self, view: View):
        self.nx = int(math.ceil(view.width / S)) + 2
        self.ny = int(math.ceil(view.height / S)) + 2
        self.blocked = bytearray(self.nx * self.ny)
        self.occ_h = bytearray(self.nx * self.ny)
        self.occ_v = bytearray(self.nx * self.ny)
        self.owner_box: dict[int, Node] = {}
        self.near: dict[int, Node] = {}   # cells just outside an icon: an arrow there looks attached to it
        for n in view.nodes:
            if not n.legend:
                x1, y1, x2, y2 = n.icon_box()
                for j in range(int((y1 - NEAR) // S), int((y2 + NEAR) // S) + 2):
                    for i in range(int((x1 - NEAR) // S), int((x2 + NEAR) // S) + 2):
                        if 0 <= i < self.nx and 0 <= j < self.ny:
                            self.near[j * self.nx + i] = n
        for n in view.nodes:
            self._mark(n.icon_box(), 3, n)
            if not n.legend:
                self._mark(n.text_box(), 2, n)
        for g in view.groups:
            if _members(g):
                self._mark(g.title_box, 3, None)
        self.groups = [g for g in view.groups if _members(g)]
        self.border_v = bytearray(self.nx * self.ny)   # cost of running along (or next to) a vertical group border
        self.border_h = bytearray(self.nx * self.ny)
        for g in self.groups:
            x1, y1, x2, y2 = g.box
            for bx in (x1, x2):
                i = round(bx / S)
                for j in range(int(y1 // S), int(y2 // S) + 1):
                    for di in (-2, -1, 0, 1, 2):
                        self._bump(self.border_v, i + di, j, 14 if abs(di) < 2 else 5)
            for by in (y1, y2):
                j = round(by / S)
                for i in range(int(x1 // S), int(x2 // S) + 1):
                    for dj in (-2, -1, 0, 1, 2):
                        self._bump(self.border_h, i, j + dj, 14 if abs(dj) < 2 else 5)

    def _bump(self, arr, i, j, v):
        if 0 <= i < self.nx and 0 <= j < self.ny:
            arr[j * self.nx + i] = max(arr[j * self.nx + i], v)

    def _set(self, arr, i, j, v=1):
        if 0 <= i < self.nx and 0 <= j < self.ny:
            arr[j * self.nx + i] = v

    def _mark(self, box, inflate, node):
        x1, y1, x2, y2 = box
        for j in range(int(math.floor((y1 - inflate) / S)), int(math.ceil((y2 + inflate) / S)) + 1):
            for i in range(int(math.floor((x1 - inflate) / S)), int(math.ceil((x2 + inflate) / S)) + 1):
                if 0 <= i < self.nx and 0 <= j < self.ny:
                    px, py = i * S, j * S
                    if x1 - inflate <= px <= x2 + inflate and y1 - inflate <= py <= y2 + inflate:
                        self.blocked[j * self.nx + i] = 1


def _ports(end, view_side: str):
    """Grid ports of an arrow end: (cell, direction away from the end, exact point on the end, cost).

    A node offers the middle of each icon side (and two points 12 pt either side); a group (``into`` / ``out_of``)
    offers points all along its border below the title band. ``view_side`` is "src" or "dst": a source prefers its
    right side, a target its left side (left-to-right reading).
    """
    prefer = {"src": {"E": 0, "N": 20, "S": 20, "W": 70}, "dst": {"W": 0, "N": 20, "S": 20, "E": 70}}[view_side]
    k = 2 if view_side == "dst" else 1          # a target leaves room for the arrowhead
    if isinstance(end, Node):
        x1, y1, x2, y2 = end.icon_box()
        if not end.legend:
            y2 = end.text_box()[3] + 2      # an arrow from below leaves (reaches) the service under its text
        along_v = [end.y + o for o in (0, -12, 12, -24, 24)]
        along_h = [end.x + o for o in (0, -12, 12, -24, 24)]
        mid_v, mid_h = end.y, end.x
    else:
        x1, y1, x2, y2 = end.box
        along_v = [y for y in _steps(y1 + TITLE_H + S, y2 - 2 * S)]
        along_h = [x for x in _steps(x1 + 2 * S, x2 - 2 * S)]
        mid_v, mid_h = (y1 + TITLE_H + y2) / 2, (x1 + x2) / 2
    out = []
    for side, d, fixed, along, mid in (("E", (1, 0), x2, along_v, mid_v), ("W", (-1, 0), x1, along_v, mid_v),
                                       ("N", (0, -1), y1, along_h, mid_h), ("S", (0, 1), y2, along_h, mid_h)):
        for a in along:
            if d[1] == 0:
                ci, cj = round((fixed + d[0] * (k * S + 3)) / S), round(a / S)
                exact = (fixed, cj * S)
            else:
                ci, cj = round(a / S), round((fixed + d[1] * (k * S + 3)) / S)
                exact = (ci * S, fixed)
            out.append(((ci, cj), d, exact, prefer[side] + abs(a - mid) / S * (0.8 if isinstance(end, Node) else 0.1)))
    return out


def _steps(a: float, b: float) -> list[float]:
    out, v = [], a
    while v <= b:
        out.append(v)
        v += S
    return out or [(a + b) / 2]


def _chain_of(end) -> list:
    return end.chain() if isinstance(end, Node) else end.chain()


def route(view: View) -> None:
    grid = _Grid(view)
    nx = grid.nx
    for e in view.edges:
        own = set(_chain_of(e.src)) | set(_chain_of(e.dst))
        foreign = [g.box for g in grid.groups if g not in own]
        ends = {e.src, e.dst}
        starts = [p for p in _ports(e.src, "src") if _free(grid, p[0])]
        goals = {}
        for cell, (dx, dy), exact, cost in _ports(e.dst, "dst"):
            if _free(grid, cell):
                goals[(cell, (-dx, -dy))] = (exact, cost)
        if not starts or not goals:
            raise SystemExit(f"{view.title}: no free side for the arrow {e.label or ''!r}")
        gx = [c[0][0] for c in goals]
        gy = [c[0][1] for c in goals]
        bx1, bx2, by1, by2 = min(gx), max(gx), min(gy), max(gy)

        def h(i, j):
            return (max(bx1 - i, 0, i - bx2) + max(by1 - j, 0, j - by2))

        def near_end(k, d):
            # a run that would continue another arrow's run on the same line, a few points short of its end: the
            # two would read as one arrow
            occ, step = (grid.occ_h, 1) if d[1] == 0 else (grid.occ_v, nx)
            if occ[k]:
                return 0
            return 40 if any(occ[k + o * step] for o in (-3, -2, -1, 1, 2, 3) if 0 <= k + o * step < len(occ)) else 0

        def cell_cost(i, j, d):
            k = j * nx + i
            c = 1.0
            horizontal = d[1] == 0
            if horizontal:
                if grid.occ_h[k]:
                    c += 400
                elif grid.occ_v[k]:
                    c += 30
                c += grid.border_h[k]
                c += near_end(k, d)
                for dj, pen in ((-1, 10), (1, 10), (-2, 4), (2, 4)):
                    kk = k + dj * nx
                    if 0 <= kk < len(grid.occ_h) and grid.occ_h[kk]:
                        c += pen
            else:
                if grid.occ_v[k]:
                    c += 400
                elif grid.occ_h[k]:
                    c += 30
                c += grid.border_v[k]
                c += near_end(k, d)
                for di, pen in ((-1, 10), (1, 10), (-2, 4), (2, 4)):
                    kk = k + di
                    if 0 <= kk < len(grid.occ_v) and grid.occ_v[kk]:
                        c += pen
            nb = grid.near.get(k)
            if nb is not None and nb not in ends:
                c += 20
            px, py = i * S, j * S
            for (x1, y1, x2, y2) in foreign:
                if x1 < px < x2 and y1 < py < y2:
                    c += 60
            return c

        heap = []
        tick = 0                              # tie-break: equal costs pop in push order (deterministic)
        best = {}
        for cell, d, exact, cost in starts:
            state = (cell[0], cell[1], d, RUN)   # the port stub counts as a full run: the first bend is free
            cost += near_end(cell[1] * nx + cell[0], d)   # a stub from an icon side can also touch a run
            if cost < best.get(state, 1e18):
                best[state] = cost
                tick += 1
                heapq.heappush(heap, (cost + h(*cell), cost, tick, state, None))
        parent = {}
        found = None
        while heap:
            f, g, _, state, prev = heapq.heappop(heap)
            if state[0] == "done":            # a goal, popped with its port cost included: the cheapest end
                found = state[1]
                break
            if best.get(state, 1e18) < g:
                continue
            if state not in parent:
                parent[state] = prev
            i, j, d, run = state
            if ((i, j), d) in goals:
                done = g + goals[((i, j), d)][1]
                if done < best.get(("done", state), 1e18):
                    best[("done", state)] = done
                    tick += 1
                    heapq.heappush(heap, (done, done, tick, ("done", state), state))
            for nd in _DIRS:
                if nd == (-d[0], -d[1]):
                    continue
                ni, nj = i + nd[0], j + nd[1]
                if not (0 <= ni < nx and 0 <= nj < grid.ny):
                    continue
                if grid.blocked[nj * nx + ni]:
                    continue
                bend = nd != d
                # a bend right after a bend (a run of two cells or less) draws a small kink: pay for it
                ng = g + cell_cost(ni, nj, nd) + ((25 + (60 if run < RUN else 0)) if bend else 0)
                ns = (ni, nj, nd, 1 if bend else min(run + 1, RUN))
                if ng < best.get(ns, 1e18):
                    best[ns] = ng
                    parent.pop(ns, None)
                    tick += 1
                    heapq.heappush(heap, (ng + h(ni, nj), ng, tick, ns, state))
                    parent[ns] = state
        if found is None:
            raise SystemExit(f"{view.title}: no route for the arrow {e.label or ''!r}")
        cells = []
        s = found
        while s is not None:
            cells.append((s[0], s[1]))
            s = parent.get(s)
        cells.reverse()
        start = next(p for p in starts if p[0] == cells[0])
        goal_exact = goals[(cells[-1], found[2])][0]
        pts = [start[2]] + [(i * S, j * S) for i, j in cells] + [goal_exact]
        e.pts = _simplify(pts)
        for (ax, ay), (bx, by) in zip(e.pts, e.pts[1:]):
            if abs(ay - by) < 0.1:
                j = round(ay / S)
                for i in range(round(min(ax, bx) / S), round(max(ax, bx) / S) + 1):
                    grid._set(grid.occ_h, i, j)
            else:
                i = round(ax / S)
                for j in range(round(min(ay, by) / S), round(max(ay, by) / S) + 1):
                    grid._set(grid.occ_v, i, j)


def _free(grid: _Grid, cell) -> bool:
    i, j = cell
    return 0 <= i < grid.nx and 0 <= j < grid.ny and not grid.blocked[j * grid.nx + i]


def _simplify(pts: list) -> list:
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) < 0.01 and abs(p[1] - out[-1][1]) < 0.01:
            continue
        out.append(p)
    # snap the first and last runs to their exact ends (they differ by < 1 grid step)
    if len(out) >= 3:
        a, b = out[0], out[1]
        if abs(a[0] - b[0]) < S and abs(a[1] - b[1]) > 0.01 and abs(a[0] - b[0]) > 0.01:
            out[1] = (a[0], b[1])
    res = [out[0]]
    for p in out[1:]:
        if len(res) >= 2:
            a, b = res[-2], res[-1]
            if (abs(a[0] - b[0]) < 0.01 and abs(b[0] - p[0]) < 0.01) or \
                    (abs(a[1] - b[1]) < 0.01 and abs(b[1] - p[1]) < 0.01):
                res[-1] = p
                continue
        res.append(p)
    return _orthogonalise(res)


def _orthogonalise(pts: list) -> list:
    """Port points sit exactly on an icon side while grid points sit on the grid: join them with right angles."""
    out = [pts[0]]
    for p in pts[1:]:
        q = out[-1]
        if abs(p[0] - q[0]) > 0.01 and abs(p[1] - q[1]) > 0.01:
            # a small jog between an exact port and the grid: move the grid point onto the port line instead
            if len(out) >= 2:
                prev = out[-2]
                if abs(prev[0] - q[0]) < 0.01:      # q ends a vertical run: shift it horizontally? keep vertical
                    out[-1] = (q[0], p[1]) if abs(p[1] - q[1]) < S else q
                    if out[-1] == q:
                        out.append((q[0], p[1]))
                else:
                    out[-1] = (p[0], q[1]) if abs(p[0] - q[0]) < S else q
                    if out[-1] == q:
                        out.append((p[0], q[1]))
            else:
                out.append((q[0], p[1]) if abs(p[0] - q[0]) < abs(p[1] - q[1]) else (p[0], q[1]))
        out.append(p)
    res = [out[0]]
    for p in out[1:]:
        if abs(p[0] - res[-1][0]) < 0.01 and abs(p[1] - res[-1][1]) < 0.01:
            continue
        if len(res) >= 2:
            a, b = res[-2], res[-1]
            if (abs(a[0] - b[0]) < 0.01 and abs(b[0] - p[0]) < 0.01) or \
                    (abs(a[1] - b[1]) < 0.01 and abs(b[1] - p[1]) < 0.01):
                res[-1] = p
                continue
        res.append(p)
    return res


# --- 4. Graphviz output --------------------------------------------------------------------------------------------


def _q(v: str) -> str:
    if v.startswith("<") and v.endswith(">"):
        return v
    # no label holds a backslash of its own, so "\\l" (left-justified line) passes through as Graphviz escape
    return '"' + v.replace('"', '\\"').replace("\n", "\\n") + '"'


def _attrs(d: dict) -> str:
    return ", ".join(f"{k}={_q(str(v))}" for k, v in d.items())


def to_dot(view: View, graph_attr: dict, node_attr: dict, edge_attr: dict, legend_rows: list) -> str:
    H = view.height

    def P(x, y):
        return f"{x:.2f},{H - y:.2f}"

    out = [f"digraph {_q(view.title)} {{",
           f"\tgraph [{_attrs({**graph_attr, 'bb': f'0,0,{view.width:.2f},{H:.2f}', 'label': view.title})}];",
           f"\tnode [{_attrs(node_attr)}];", f"\tedge [{_attrs(edge_attr)}];"]

    def emit_node(n: Node, ind: str):
        if n.legend:
            x1, y1, x2, y2 = n.icon_box()
            for k, (style, text) in enumerate(legend_rows):
                yy = y1 + TITLE_H + 12 + k * 22
                a, b, t = f"{n.id}-l{k}a", f"{n.id}-l{k}b", f"{n.id}-l{k}t"
                out.append(f"{ind}{_q(a)} [{_attrs({'shape': 'point', 'width': '0.01', 'height': '0.01', 'style': 'invis', 'pos': P(x1 + 6, yy)})}];")
                out.append(f"{ind}{_q(b)} [{_attrs({'shape': 'point', 'width': '0.01', 'height': '0.01', 'style': 'invis', 'pos': P(x1 + 60, yy)})}];")
                tw = max(len(s) for s in text.split(chr(10))) * 10 * 0.56 + 6
                out.append(f"{ind}{_q(t)} [{_attrs({'shape': 'plaintext', 'label': text + chr(92) + 'l', 'fontsize': '10', 'fixedsize': 'true', 'width': f'{tw / 72:.3f}', 'height': f'{(text.count(chr(10)) + 1) * 12 / 72:.3f}', 'pos': P(x1 + 70 + tw / 2, yy)})}];")
                legend_edges.append((a, b, style, f"e,{P(x1 + 60, yy)} {P(x1 + 6, yy)} {P(x1 + 6, yy)} {P(x1 + 52, yy)} {P(x1 + 52, yy)}"))
            return
        tw, th = n.text_size()
        icon = {**n.attrs, "label": "", "shape": "none", "fixedsize": "true", "imagescale": "true",
                "width": f"{ICON / 72:.4f}", "height": f"{ICON / 72:.4f}", "pos": P(n.x, n.y)}
        out.append(f"{ind}{_q(n.id)} [{_attrs(icon)}];")
        tb = n.text_box()
        text = {"shape": "plaintext", "label": n.label, "fixedsize": "true", "width": f"{tw / 72:.4f}",
                "height": f"{th / 72:.4f}", "pos": P(n.x, (tb[1] + tb[3]) / 2)}
        out.append(f"{ind}{_q(n.id + '-t')} [{_attrs(text)}];")

    legend_edges: list = []

    def emit_group(g: Group, ind: str):
        if not _members(g):
            return
        x1, y1, x2, y2 = g.box
        tx1, ty1, tx2, ty2 = g.title_box
        a = {**g.attrs, "label": g.label, "bb": f"{x1:.2f},{H - y2:.2f},{x2:.2f},{H - y1:.2f}",
             "lp": P((tx1 + tx2) / 2, (ty1 + ty2) / 2), "lwidth": f"{(tx2 - tx1) / 72:.3f}",
             "lheight": f"{(ty2 - ty1) / 72:.3f}"}
        out.append(f"{ind}subgraph {_q('cluster_' + g.key)} {{")
        out.append(f"{ind}\tgraph [{_attrs(a)}];")
        for n in g.nodes:
            emit_node(n, ind + "\t")
        for c in g.children:
            emit_group(c, ind + "\t")
        out.append(f"{ind}}}")

    for g in view.groups:
        if g.parent is None:
            emit_group(g, "\t")
    for n in view.nodes:
        if n.group is None:
            emit_node(n, "\t")
    for e in view.edges:
        pts = e.pts
        (ax, ay), (bx, by) = pts[-2], pts[-1]
        length = abs(bx - ax) + abs(by - ay)
        ux, uy = ((bx - ax) / length, (by - ay) / length) if length else (0, 0)
        base = (bx - ux * ARROW, by - uy * ARROW)
        body = pts[:-1] + [base]
        spl = [body[0]]
        for p, q in zip(body, body[1:]):
            spl += [p, q, q]
        pos = f"e,{P(*pts[-1])} " + " ".join(P(*p) for p in spl)
        a = {**e.attrs, "pos": pos}
        if e.label:
            a["xlabel"] = e.label
            a["xlp"] = P(*pts[0])
        if isinstance(e.dst, Group):
            a["lhead"] = "cluster_" + e.dst.key
        if isinstance(e.src, Group):
            a["ltail"] = "cluster_" + e.src.key
        src = e.src.nodes_anchor if isinstance(e.src, Group) else e.src.id
        dst = e.dst.nodes_anchor if isinstance(e.dst, Group) else e.dst.id
        out.append(f"\t{_q(src)} -> {_q(dst)} [{_attrs(a)}];")
    for a, b, style, pos in legend_edges:
        out.append(f"\t{_q(a)} -> {_q(b)} [{_attrs({**style, 'pos': pos})}];")
    out.append("}")
    return "\n".join(out) + "\n"


def draw(view: View, filename: str, formats: list, graph_attr, node_attr, edge_attr, legend_rows) -> str:
    """Lay out, route, place labels and write ``<filename>.<fmt>`` with ``neato -n2``; returns the final dot text."""
    from _common import place_edge_labels  # noqa: PLC0415 (shared with the checker)

    layout(view)
    for g in view.groups:      # an arrow that ends on a group border is drawn between two of its members' ids
        m = _members(g)
        g.nodes_anchor = m[0].id if m else ""
    route(view)
    dot = place_edge_labels(to_dot(view, graph_attr, node_attr, edge_attr, legend_rows))
    Path(filename).write_text(dot, encoding="utf-8")
    for fmt in formats:
        subprocess.run(["neato", "-n2", f"-T{fmt}", "-o", f"{filename}.{fmt}"], input=dot, text=True,
                       capture_output=True, check=True)
    return dot
