"""Shared helpers for the AA-Ecosys architecture diagrams (AA-697).

Each ``<name>.py`` next to this file draws one view in the style of the AWS Architecture Icons deck: the official
service icons and group shapes shipped by the Python ``diagrams`` package (mingrammer), drawn by Graphviz. A view
declares its groups (``group``), its services (the ``diagrams`` node classes), where each service sits on a grid
(``place``) and its arrows (``link``); ``_layout.py`` computes the coordinates and routes every arrow orthogonally,
and Graphviz (``neato -n2``) draws the result. ``render.py`` runs them all and writes ``<name>.svg``.

The SVG Graphviz writes points at icon PNGs by absolute path on the machine that rendered it. ``finalize_svg`` turns
every icon into an inline ``data:image/png;base64`` URI (downscaled when Pillow is installed), drops the absolute paths
and the Graphviz comments. ``check_svg_safe`` then refuses anything a reader could run or fetch (scripts,
``foreignObject``, event-handler attributes, ``javascript:``, any reference that is neither a fragment nor an inline
PNG) and any account or resource ID in the text. That check is rule 9 of the docs reader bundle builder
(``tools/docs/build_docs_reader.py``), imported here so render time and publish time apply one rule.

Labels never carry account IDs, ARNs or network IDs (security groups, subnets, VPCs): names and roles only.
"""
from __future__ import annotations

import base64
import html
import io
import re
import sys
from contextlib import contextmanager
from pathlib import Path

import diagrams
from diagrams import Cluster, Diagram, getcluster

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools" / "docs"))
sys.path.insert(0, str(HERE))

import _layout  # noqa: E402
from build_docs_reader import svg_problems  # noqa: E402  (one safety rule for render time and publish time)

GRAPH_ATTR = {"fontname": "Helvetica", "fontsize": "22", "fontcolor": "#232F3E", "labelloc": "t", "labeljust": "l",
              "bgcolor": "white", "pad": "0.2"}
NODE_ATTR = {"fontname": "Helvetica", "fontsize": "12", "fontcolor": "#232F3E"}
EDGE_ATTR = {"fontname": "Helvetica", "fontsize": "10", "color": "#545B64", "fontcolor": "#232F3E",
             "arrowsize": "0.8", "penwidth": "1.3"}

OUTFORMATS = ["svg"]  # render.py --png adds "png" for previews

_RES = Path(diagrams.__file__).resolve().parent.parent / "resources"
_ICONS = HERE / "icons"

# AWS group conventions (AWS Architecture Icons deck, "Groups"): border colour, border style, fill, title colour and the
# group icon drawn at the top-left corner. AWS groups have square corners; groups outside AWS use the neutral grey of
# the deck's "Generic group" / "Corporate data center" (dashed = a logical group, solid = a place with an icon).
GROUPS = {
    "cloud":   {"pencolor": "#232F3E", "style": "solid", "bgcolor": "#FFFFFF", "fontcolor": "#232F3E",
                "icon": _ICONS / "aws-cloud.png"},
    "region":  {"pencolor": "#00A4A6", "style": "dashed", "bgcolor": "#FFFFFF", "fontcolor": "#00A4A6",
                "icon": _ICONS / "region.png"},
    "vpc":     {"pencolor": "#8C4FFF", "style": "solid", "bgcolor": "#FFFFFF", "fontcolor": "#8C4FFF",
                "icon": _RES / "aws" / "network" / "vpc.png"},
    "public":  {"pencolor": "#248814", "style": "filled", "bgcolor": "#E9F3E6", "fontcolor": "#248814",
                "icon": _RES / "aws" / "network" / "public-subnet.png"},
    "private": {"pencolor": "#147EBA", "style": "filled", "bgcolor": "#E6F2F8", "fontcolor": "#147EBA",
                "icon": _RES / "aws" / "network" / "private-subnet.png"},
    "ecs":     {"pencolor": "#D86613", "style": "dashed", "bgcolor": "#FFFFFF", "fontcolor": "#D86613",
                "icon": _RES / "aws" / "compute" / "elastic-container-service.png"},
    "generic": {"pencolor": "#7D8998", "style": "dashed", "bgcolor": "#FFFFFF", "fontcolor": "#5A6B86", "icon": None},
    # outside AWS: a solid grey frame with the owner's icon, like the deck's "Corporate data center" group
    "people":  {"pencolor": "#7D8998", "style": "solid", "bgcolor": "#FFFFFF", "fontcolor": "#5A6B86",
                "icon": _RES / "aws" / "general" / "users.png"},
    "vercel":  {"pencolor": "#7D8998", "style": "solid", "bgcolor": "#FFFFFF", "fontcolor": "#5A6B86",
                "icon": _RES / "programming" / "framework" / "vercel.png"},
    "github":  {"pencolor": "#7D8998", "style": "solid", "bgcolor": "#FFFFFF", "fontcolor": "#5A6B86",
                "icon": _RES / "onprem" / "vcs" / "github.png"},
    "outside": {"pencolor": "#7D8998", "style": "solid", "bgcolor": "#FFFFFF", "fontcolor": "#5A6B86",
                "icon": _RES / "aws" / "general" / "internet-alt1.png"},
}


def group(kind: str, title: str, note: str = ""):
    """A group box in the official AWS look: ``with group("vpc", "Shared VPC"):``.

    The title (and an optional smaller ``note`` line) sits beside the group icon at the top-left corner. Groups nest
    in the AWS order: AWS Cloud (one per account) > Region > VPC > subnet groups > ECS cluster.
    """
    return _group(kind, title, note)


@contextmanager
def _group(kind: str, title: str, note: str):
    g = GROUPS[kind]
    view = _VIEW["view"]
    parent = getattr(getcluster(), "_aa", None)
    key = f"{len(view.groups) + 1} {kind} {title}"
    text = f'<B>{html.escape(title)}</B>'
    if note:
        text += f'<BR ALIGN="LEFT"/><FONT POINT-SIZE="10">{html.escape(note)}</FONT>'
    icon = (f'<TD FIXEDSIZE="TRUE" WIDTH="24" HEIGHT="24" VALIGN="TOP"><IMG SRC="{g["icon"]}" SCALE="TRUE"/></TD>'
            if g["icon"] else "")
    label = (f'<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="2"><TR>{icon}'
             f'<TD ALIGN="LEFT" BALIGN="LEFT"><FONT COLOR="{g["fontcolor"]}" POINT-SIZE="12">{text}</FONT></TD>'
             f'</TR></TABLE>>')
    attrs = {"labeljust": "l", "labelloc": "t", "pencolor": g["pencolor"], "bgcolor": g["bgcolor"],
             "style": g["style"], "penwidth": "1.5", "fontname": "Helvetica"}
    if g["style"] == "filled":
        attrs["fillcolor"] = g["bgcolor"]
    rec = _layout.Group(key=key, kind=kind, title=title, note=note, attrs=attrs, label=label, parent=parent)
    view.groups.append(rec)
    if parent is not None:
        parent.children.append(rec)
    with Cluster(key) as cluster:
        cluster._aa = rec
        yield rec


# --- services ------------------------------------------------------------------------------------------------------

_VIEW: dict = {}


def _patch_node(cls) -> None:
    def node(self, nodeid, label, **attrs):
        view = _VIEW["view"]
        n = _layout.Node(id=f"s{len(view.nodes) + 1}", label=label, attrs={"image": attrs["image"]},
                         group=getattr(self, "_aa", None))
        view.nodes.append(n)
        _VIEW["by_id"][nodeid] = n
        if n.group is not None:
            n.group.nodes.append(n)

    cls.node = node


_patch_node(Diagram)
_patch_node(Cluster)


def _node(x) -> "_layout.Node":
    return _VIEW["by_id"][x.nodeid]


def place(cells: dict) -> None:
    """Put each service on a grid cell: ``place({staff: (0, 1), rest: (2, 1)})`` = (column, row), left to right and
    top to bottom. Columns follow the reading order (people, edge, compute, data); rows keep one request path on one
    line where they can. Groups grow around their members, so the members of one group need adjacent cells."""
    for node, cell in cells.items():
        _node(node).cell = cell


def legend(cell: tuple) -> None:
    """The arrow legend, in a small generic group on ``cell``."""
    with group("generic", "Legend") as g:
        view = _VIEW["view"]
        n = _layout.Node(id=f"s{len(view.nodes) + 1}", label="", attrs={}, group=g, cell=cell, legend=True)
        view.nodes.append(n)
        g.nodes.append(n)


# --- arrows --------------------------------------------------------------------------------------------------------

# Edge kinds, the same in every view (README "Conventions" and the legend drawn in each view).
KINDS = {
    "data": {},                        # solid: a request, a read or a write (also an HTTP contract between apps)
    "control": {"style": "dashed"},    # dashed: control or identity (sign-in, OIDC, sts:AssumeRole, deploy)
    "async": {"style": "dotted"},      # dotted: asynchronous or optional (events, logs, a call not live yet)
}
LEGEND = [("data", "request or data"), ("control", "control or identity (sign-in, OIDC, AssumeRole, deploy)"),
          ("async", "asynchronous or optional (events, logs, not provisioned)")]
_layout.LEGEND_TEXTS[:] = [text for _, text in LEGEND]


def link(src, dst, label: str = "", kind: str = "data", into=None, out_of=None) -> None:
    """One arrow from ``src`` to ``dst``, arrowhead on the target only.

    ``into`` / ``out_of`` take a group: the arrow then ends (starts) on that group's border, for a relation whose real
    end is the whole group (one arrow instead of one per member). The label goes beside the arrow.
    """
    a = {"dir": "forward", "arrowhead": "normal", **KINDS[kind]}
    s = out_of if out_of is not None else _node(src)
    d = into if into is not None else _node(dst)
    _VIEW["view"].edges.append(_layout.Edge(src=s, dst=d, label=label, attrs=a))


# --- the view ------------------------------------------------------------------------------------------------------


class _GridDiagram(Diagram):
    problems: list[str] = []

    def render(self) -> None:
        formats = self.outformat if isinstance(self.outformat, list) else [self.outformat]
        legend_rows = [({"dir": "forward", "arrowhead": "normal", **KINDS[k]}, text) for k, text in LEGEND]
        dot = _layout.draw(_VIEW["view"], self.filename, formats, GRAPH_ATTR, NODE_ATTR, EDGE_ATTR, legend_rows)
        _GridDiagram.problems = layout_problems(dot)


@contextmanager
def diagram(title: str, filename: str):
    """The context every view draws in: ``with diagram("AA-Booking ...", filename):``."""
    _VIEW.clear()
    _VIEW.update(view=_layout.View(title=title), by_id={})
    with _GridDiagram(title, filename=filename, outformat=list(OUTFORMATS), show=False) as d:
        yield d


# --- arrow labels and the layout check ------------------------------------------------------------------------------

_STMT = re.compile(r'^(?P<ind>\s*)(?P<head>graph|node|edge|"[^"]*"|[\w.-]+)(?P<arrow>\s*->\s*(?:"[^"]*"|[\w.-]+))?'
                   r'\s*\[(?P<attrs>.*?)\];\s*$', re.M | re.S)
_EDGE_FONT_PT = 10


def _attr(attrs: str, name: str) -> str | None:
    m = re.search(rf'(?<![\w-]){name}=("(?:[^"\\]|\\.)*"|[^,\s\]]+)', attrs)
    return None if m is None else m.group(1).strip('"')


def _points(pos: str) -> list[tuple[float, float]]:
    pts, end = [], None
    for tok in pos.split():
        if tok.startswith(("e,", "s,")):
            x, y = tok[2:].split(",")
            if tok[0] == "e":
                end = (float(x), float(y))
            continue
        x, y = tok.split(",")
        pts.append((float(x), float(y)))
    if end:
        pts.append(end)
    out: list[tuple[float, float]] = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) > 0.5 or abs(p[1] - out[-1][1]) > 0.5:
            out.append(p)
    return out


def _segments(pts):
    return [(a, b) for a, b in zip(pts, pts[1:])]


def _box_hits_segment(box, seg, pad=1.5) -> bool:
    (x1, y1, x2, y2) = box
    (ax, ay), (bx, by) = seg
    sx1, sx2 = sorted((ax, bx))
    sy1, sy2 = sorted((ay, by))
    return not (sx2 < x1 - pad or sx1 > x2 + pad or sy2 < y1 - pad or sy1 > y2 + pad)


def _boxes_overlap(a, b, pad=2.0) -> bool:
    return not (a[2] + pad < b[0] or b[2] + pad < a[0] or a[3] + pad < b[1] or b[3] + pad < a[1])


def place_edge_labels(laid: str) -> str:
    """Move each edge ``xlabel`` of a laid-out dot file (``dot -Tdot``) to a clear spot beside its own arrow."""
    text = laid.replace("\\\n", "")
    stmts = list(_STMT.finditer(text))
    obstacles: list[tuple[float, float, float, float]] = []   # nodes and group titles
    borders: list = []                                        # group borders
    lines: list = []                                          # every visible arrow
    labelled = []
    for m in stmts:
        head, attrs = m.group("head"), m.group("attrs")
        if head == "graph":
            bb = _attr(attrs, "bb")
            if bb and _attr(attrs, "peripheries") != "0" and "label=<" in attrs:
                x1, y1, x2, y2 = map(float, bb.split(","))
                borders += _segments([(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)])
                lp, lw, lh = _attr(attrs, "lp"), _attr(attrs, "lwidth"), _attr(attrs, "lheight")
                if lp and lw and lh:
                    cx, cy = map(float, lp.split(","))
                    w, h = float(lw) * 72, float(lh) * 72
                    obstacles.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
        elif m.group("arrow"):
            if _attr(attrs, "style") == "invis" or not _attr(attrs, "pos"):
                continue
            pts = _points(_attr(attrs, "pos"))
            lines.append(pts)
            if _attr(attrs, "xlabel"):
                labelled.append((m, pts))
        elif head not in ("node", "edge"):
            pos, w, h = _attr(attrs, "pos"), _attr(attrs, "width"), _attr(attrs, "height")
            if pos and w and h and _attr(attrs, "style") != "invis":
                cx, cy = map(float, pos.split(","))
                w, h = float(w) * 72, float(h) * 72
                obstacles.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
    all_segments = [s for pts in lines for s in _segments(pts)] + borders
    placed: list = []
    edits: dict[int, str] = {}
    for m, pts in labelled:
        label = _attr(m.group("attrs"), "xlabel").replace("\\n", "\n")
        rows = label.split("\n")
        w = max(len(r) for r in rows) * _EDGE_FONT_PT * 0.56 + 4
        h = len(rows) * _EDGE_FONT_PT * 1.2 + 2
        own = _segments(pts)
        best, best_cost = None, None
        for seg in sorted(own, key=lambda s: -(abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))):
            (ax, ay), (bx, by) = seg
            horizontal = abs(ay - by) < 0.5
            for t in (0.5, 0.35, 0.65, 0.2, 0.8):
                px, py = ax + (bx - ax) * t, ay + (by - ay) * t
                offsets = ([(0, h / 2 + 3), (0, -h / 2 - 3)] if horizontal
                           else [(w / 2 + 4, 0), (-w / 2 - 4, 0)])
                for dx, dy in offsets:
                    cx, cy = px + dx, py + dy
                    box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
                    cost = (sum(_boxes_overlap(box, o) for o in obstacles) * 10
                            + sum(_boxes_overlap(box, p) for p in placed) * 10
                            + sum(_box_hits_segment(box, s) for s in all_segments) * 3)
                    if best_cost is None or cost < best_cost:
                        best, best_cost = (cx, cy, box), cost
                    if cost == 0:
                        break
                if best_cost == 0:
                    break
            if best_cost == 0:
                break
        cx, cy, box = best
        placed.append(box)
        edits[m.start("attrs")] = re.sub(r'xlp="[^"]*"', f'xlp="{cx:.2f},{cy:.2f}"', m.group("attrs"))
    out, last = [], 0
    for m in stmts:
        if m.start("attrs") in edits:
            out += [text[last:m.start("attrs")], edits[m.start("attrs")]]
            last = m.end("attrs")
    out.append(text[last:])
    return "".join(out)


def _parse_layout(laid: str) -> dict:
    """Clusters (box, title box, members), nodes (box, clusters) and visible edges (points) of a laid-out dot file."""
    text = laid.replace("\\\n", "")
    events = [(m.start(), "open", m.group(1).strip('"')) for m in re.finditer(r'subgraph\s+("[^"]*"|[\w.-]+)\s*\{', text)]
    events += [(m.start(), "open", None) for m in re.finditer(r'^\s*\{\s*$', text, re.M)]
    events += [(m.start(), "close", None) for m in re.finditer(r'^\s*\}\s*$', text, re.M)]
    events.sort()
    clusters: dict[str, dict] = {}
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    stack: list = []
    ei = 0
    for m in _STMT.finditer(text):
        while ei < len(events) and events[ei][0] < m.start("head"):
            _, kind, name = events[ei]
            stack.append(name) if kind == "open" else stack.pop()
            ei += 1
        head, attrs = m.group("head").strip('"'), m.group("attrs")
        path = tuple(n for n in stack if n and n.startswith("cluster") and not n.startswith("cluster-"))
        if head == "graph":
            bb = _attr(attrs, "bb")
            if not path or not bb or path[-1] in clusters:
                continue
            x1, y1, x2, y2 = map(float, bb.split(","))
            title = None
            lp, lw, lh = _attr(attrs, "lp"), _attr(attrs, "lwidth"), _attr(attrs, "lheight")
            if lp and lw and lh:
                cx, cy = map(float, lp.split(","))
                w, h = float(lw) * 72, float(lh) * 72
                title = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            clusters[path[-1]] = {"box": (x1, y1, x2, y2), "title": title}
        elif m.group("arrow"):
            if _attr(attrs, "style") == "invis" or not _attr(attrs, "pos"):
                continue
            tail = head
            hd = m.group("arrow").split("->")[1].strip().strip('"')
            edges.append({"tail": tail, "head": hd, "pts": _points(_attr(attrs, "pos")),
                          "lhead": _attr(attrs, "lhead"), "ltail": _attr(attrs, "ltail"),
                          "name": f"{tail}->{hd}", "label": _attr(attrs, "xlabel")})
        elif head not in ("node", "edge"):
            pos, w, h = _attr(attrs, "pos"), _attr(attrs, "width"), _attr(attrs, "height")
            if pos and w and h:
                cx, cy = map(float, pos.split(","))
                w, h = float(w) * 72, float(h) * 72
                nodes[head] = {"box": (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), "path": path,
                               "text": head.endswith("-t") or _attr(attrs, "shape") == "plaintext"}
    # a node's full statement may sit in a root ``{rank=same}`` block; its group is the deepest place it is named
    stack = []
    for line in text.split("\n"):
        s = line.strip()
        m = re.match(r'subgraph\s+("[^"]*"|[\w.-]+)\s*\{', s)
        if m:
            stack.append(m.group(1).strip('"'))
            continue
        if s.endswith("{"):
            stack.append(None)
            continue
        if s == "}":
            stack.pop()
            continue
        m = re.match(r'("[^"]*"|[\w.-]+)\s*(\[|;)', s)
        if m and m.group(1).strip('"') in nodes and "->" not in s:
            path = tuple(n for n in stack if n and n.startswith("cluster") and not n.startswith("cluster-"))
            n = nodes[m.group(1).strip('"')]
            if len(path) > len(n["path"]):
                n["path"] = path
    return {"clusters": clusters, "nodes": nodes, "edges": edges}


def _seg_cross_box(seg, box, pad=0.0) -> bool:
    """Does an axis-parallel segment enter the inside of a box (shrunk by ``pad``)?"""
    x1, y1, x2, y2 = box[0] + pad, box[1] + pad, box[2] - pad, box[3] - pad
    (ax, ay), (bx, by) = seg
    sx1, sx2 = sorted((ax, bx))
    sy1, sy2 = sorted((ay, by))
    return sx2 > x1 and sx1 < x2 and sy2 > y1 and sy1 < y2


def layout_problems(laid: str) -> list[str]:
    """Readability problems of a laid-out view: an arrow through a node, a label, a group title or a group neither of
    its ends belongs to, an arrow running along a group border, two arrows sharing one track."""
    lay = _parse_layout(laid)
    nodes, clusters = lay["nodes"], lay["clusters"]
    problems: list[str] = []
    tracks = []
    for e in lay["edges"]:
        ends = {e["tail"], e["head"], f"{e['tail']}-t", f"{e['head']}-t"}
        end_paths = set()
        for n in (e["tail"], e["head"]):
            end_paths.update(nodes.get(n, {}).get("path", ()))
        for c in (e["lhead"], e["ltail"]):
            if c:
                end_paths.add(c)
        segs = _segments(e["pts"])
        for seg in segs:
            for name, n in nodes.items():
                if name in ends or name.startswith("legend_"):
                    continue
                if _seg_cross_box(seg, n["box"], pad=1):
                    problems.append(f"{e['name']}: through node {name}")
            for name, c in clusters.items():
                if c["title"] and _seg_cross_box(seg, c["title"], pad=-2):
                    problems.append(f"{e['name']}: over the title of {name}")
                if name not in end_paths and _seg_cross_box(seg, c["box"], pad=2):
                    problems.append(f"{e['name']}: through group {name}")
                x1, y1, x2, y2 = c["box"]
                (ax, ay), (bx, by) = seg
                if abs(ay - by) < 0.5 and abs(ax - bx) > 12 and min(abs(ay - y1), abs(ay - y2)) < 6 \
                        and min(ax, bx) < x2 and max(ax, bx) > x1:
                    problems.append(f"{e['name']}: along the border of {name}")
                if abs(ax - bx) < 0.5 and abs(ay - by) > 12 and min(abs(ax - x1), abs(ax - x2)) < 6 \
                        and min(ay, by) < y2 and max(ay, by) > y1:
                    problems.append(f"{e['name']}: along the border of {name}")
            tracks.append((e["name"], e["tail"], seg))
    for i, (n1, t1, s1) in enumerate(tracks):
        for n2, t2, s2 in tracks[i + 1:]:
            if n1 == n2 or t1 == t2:
                continue
            (a1, b1), (a2, b2) = s1, s2
            if abs(a1[1] - b1[1]) < 0.5 and abs(a2[1] - b2[1]) < 0.5 and abs(a1[1] - a2[1]) < 3:
                lo, hi = max(min(a1[0], b1[0]), min(a2[0], b2[0])), min(max(a1[0], b1[0]), max(a2[0], b2[0]))
                if hi - lo > 6:
                    problems.append(f"{n1} and {n2}: share a track")
            if abs(a1[0] - b1[0]) < 0.5 and abs(a2[0] - b2[0]) < 0.5 and abs(a1[0] - a2[0]) < 3:
                lo, hi = max(min(a1[1], b1[1]), min(a2[1], b2[1])), min(max(a1[1], b1[1]), max(a2[1], b2[1]))
                if hi - lo > 6:
                    problems.append(f"{n1} and {n2}: share a track")
    return sorted(set(problems))



# --- SVG clean-up and safety -----------------------------------------------------------------------------------

ICON_PX = 96  # icons are drawn at about 1.4 in; 96 px keeps them sharp and the SVG small

_IMG_HREF = re.compile(r'(?P<attr>xlink:href|href)="(?P<path>[^"#][^"]*\.png)"')


def _png_data_uri(path: str) -> str:
    raw = Path(path).read_bytes()
    try:  # optional: shrink the 256 px icons; without Pillow the original bytes are inlined
        from PIL import Image  # type: ignore

        with Image.open(io.BytesIO(raw)) as im:
            im = im.convert("RGBA")
            im.thumbnail((ICON_PX, ICON_PX), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="PNG", optimize=True)
            raw = buf.getvalue()
    except ImportError:
        pass
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def finalize_svg(svg_path: Path) -> int:
    """Inline icons, strip machine-specific bits, check safety; returns the final size in bytes."""
    text = svg_path.read_text(encoding="utf-8")
    cache: dict[str, str] = {}

    def repl(m: re.Match[str]) -> str:
        p = m.group("path")
        if p not in cache:
            cache[p] = _png_data_uri(p)
        return f'xlink:href="{cache[p]}"'

    text = _IMG_HREF.sub(repl, text)
    # Graphviz comments (generator, one per node and edge) carry nothing a reader needs.
    text = re.sub(r"<!--.*?-->\n?", "", text, flags=re.S)
    # diagrams names every node with a random uuid4 hex. Number them in order of appearance instead, so a re-render of
    # an unchanged view gives the same file and no random digit run looks like an account ID to the docs guard.
    ids: dict[str, str] = {}
    text = re.sub(r"\b[0-9a-f]{32}\b", lambda m: ids.setdefault(m.group(0), f"n{len(ids) + 1}"), text)
    problems = check_svg_safe(text)
    if problems:
        raise SystemExit(f"{svg_path.name}: unsafe SVG: {problems}")
    svg_path.write_text(text, encoding="utf-8")
    return len(text.encode("utf-8"))


def check_svg_safe(text: str) -> list[str]:
    """Problems that keep an SVG out of the docs reader (empty list = safe): the bundle builder's own rule 9 check."""
    return svg_problems(text)


