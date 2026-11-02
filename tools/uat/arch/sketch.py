"""Public diagram sketches (AA-1021): a small hand-built diagram per episode, drawn here as SVG.

  python -I sketch.py <sketch.json> <out.svg>          # render one sketch on its own (to look at it)
  python -I sketch.py --extract-icons <icon-package.zip> <dir>     # setup.sh: the official icons this file uses

Why not the committed architecture SVGs: a relabelled copy of docs/architecture/diagrams/*.svg keeps every node
position, frame and arrow route of a figure that is public in this repo, so a viewer (or a reverse image search)
can match a frame to the repo whatever the words say. A sketch is authored per episode, kept OUTSIDE git with the
episode file, simplified to what the episode says, and laid out on its own grid; every label in it is authored text
and goes through the whole layer 1 check (deny-list, identifier shapes, n-gram and internal-token check, label set).

Format (the value of one "diagrams" entry of the episode file; an invented example: sketch.example.json):
  {"groups": [{"id": "base", "label": "Common layer", "sub": "one region", "cells": [c0, r0, c1, r1],
               "kind": "cloud" | "account" | "region" | "vpc" | "private-subnet" | "public-subnet" | "generic",
               "icon": "<icon key>", "style": "solid" | "dashed"}],  a frame around grid cells c0..c1 x r0..r1
   "nodes":  [{"id": "cat", "label": "Catalogue app", "sub": "api + workers" | ["line", "line"],
               "at": [col, row], "kind": "service" | "store" | "people" | "external", "icon": "<icon key>" | "none"}],
   "edges":  [{"from": "cat", "to": "db", "label": "SQL", "style": "solid" | "dashed", "bend": 0.5}]}
An edge between two rows runs down, across, down; "bend" (0.1-0.9, default 0.5) sets where the cross run sits in the
gap, so two edges that would share a run can be kept apart.
Groups nest by their cells (a group inside another must sit strictly within its cells, or share no cell with it).

Icons: the official AWS Architecture Icons (the published asset package; AWS permits their use in architecture
diagrams). setup.sh downloads the package (pinned URL + sha256) and extracts the files named in ICONS into the
gitignored cache; nothing of it is committed. A node takes the icon named by "icon", else the one its label names
(a cloud product name, ICON_BY_LABEL), else a general icon for its kind (people: users, external: internet); a
group "kind" draws the official group style (border colour, corner icon), a group "icon" draws a service group in the
service's category colour. Icons are inlined as plain shapes: <title>, <desc>, ids and any text, link, image, style or
url() reference are dropped or refused, so an icon adds nothing a gate layer could read. Without an icon folder
(render(..., icon_dir=None)) the sketch is drawn without icons, with the same frames and colours.

The SVG has the structure page.py drives (the same as a Graphviz SVG): g.graph > g.cluster / g.node / g.edge, every
label a direct <text> child, node keys data-k="n<i>" (never the authored ids), edges data-from / data-to. No <title>,
<desc>, link, image or font reference. Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from html import escape
from pathlib import Path

CELL_W, NODE_W = 284, 240
LINE_H, SUB_H = 24, 19
NODE_PAD_Y = 14
ICON, ICON_GAP = 46, 8
GROUP_ICON = 32
TITLE_BAND = 40
PAD = 18
GROUP_INSET = 12
KINDS = {"service", "store", "people", "external"}
# Strong, readable palette: near-black labels, dark sub-lines, dark edges, mid-grey node strokes on white cards.
INK, BODY, MUTED, LINE, CARD = "#0B1219", "#232F3E", "#3F4B59", "#5A6B7D", "#FFFFFF"
LABEL_PX, SUB_PX, GROUP_PX, EDGE_PX = 16, 13.5, 16, 13.5

# Official AWS group styles (border colour from the group icons of the asset package; dashed where the guide uses it).
GROUP_KINDS = {
    "cloud": {"stroke": "#242F3E", "icon": "group-cloud"},
    "account": {"stroke": "#E7157B", "icon": "group-account"},
    "region": {"stroke": "#00A4A6", "icon": "group-region", "dash": True},
    "vpc": {"stroke": "#8C4FFF", "icon": "group-vpc"},
    "private-subnet": {"stroke": "#00A4A6", "icon": "group-private-subnet", "fill": "#E6F6F7"},
    "public-subnet": {"stroke": "#7AA116", "icon": "group-public-subnet", "fill": "#F2F6E8"},
    "generic": {"stroke": "#7D8998"},
}

ICON_PACKAGE = "Icon-package_07312026"
_SVC, _RES, _GRP = ("Architecture-Service-Icons_07312026/", "Resource-Icons_07312026/",
                    "Architecture-Group-Icons_07312026/")
# key -> (file in the official package, category colour used for a service group's frame)
ICONS = {
    "api-gateway": (_SVC + "Arch_Networking-Content-Delivery/64/Arch_Amazon-API-Gateway_64.svg", "#8C4FFF"),
    "cloudfront": (_SVC + "Arch_Networking-Content-Delivery/64/Arch_Amazon-CloudFront_64.svg", "#8C4FFF"),
    "ecs": (_SVC + "Arch_Containers/64/Arch_Amazon-Elastic-Container-Service_64.svg", "#ED7100"),
    "fargate": (_SVC + "Arch_Containers/64/Arch_AWS-Fargate_64.svg", "#ED7100"),
    "lambda": (_SVC + "Arch_Compute/64/Arch_AWS-Lambda_64.svg", "#ED7100"),
    "rds": (_SVC + "Arch_Databases/64/Arch_Amazon-RDS_64.svg", "#C925D1"),
    "elasticache": (_SVC + "Arch_Databases/64/Arch_Amazon-ElastiCache_64.svg", "#C925D1"),
    "s3": (_SVC + "Arch_Storage/64/Arch_Amazon-Simple-Storage-Service_64.svg", "#7AA116"),
    "cognito": (_SVC + "Arch_Security-Identity/64/Arch_Amazon-Cognito_64.svg", "#DD344C"),
    "waf": (_SVC + "Arch_Security-Identity/64/Arch_AWS-WAF_64.svg", "#DD344C"),
    "secrets-manager": (_SVC + "Arch_Security-Identity/64/Arch_AWS-Secrets-Manager_64.svg", "#DD344C"),
    "bedrock": (_SVC + "Arch_Artificial-Intelligence/64/Arch_Amazon-Bedrock_64.svg", "#01A88D"),
    "eventbridge": (_SVC + "Arch_Application-Integration/64/Arch_Amazon-EventBridge_64.svg", "#E7157B"),
    "eventbridge-scheduler": (_RES + "Res_Application-Integration/Res_Amazon-EventBridge_Scheduler_48.svg",
                              "#E7157B"),
    "ses": (_SVC + "Arch_Business-Applications/64/Arch_Amazon-Simple-Email-Service_64.svg", "#DD344C"),
    "cloudwatch": (_SVC + "Arch_Management-Tools/64/Arch_Amazon-CloudWatch_64.svg", "#E7157B"),
    "ecs-service": (_RES + "Res_Containers/Res_Amazon-Elastic-Container-Service_Service_48.svg", "#ED7100"),
    "users": (_RES + "Res_General-Icons/Res_48_Light/Res_Users_48_Light.svg", "#242F3E"),
    "user": (_RES + "Res_General-Icons/Res_48_Light/Res_User_48_Light.svg", "#242F3E"),
    "client": (_RES + "Res_General-Icons/Res_48_Light/Res_Client_48_Light.svg", "#242F3E"),
    "internet": (_RES + "Res_General-Icons/Res_48_Light/Res_Internet-alt1_48_Light.svg", "#242F3E"),
    "app": (_RES + "Res_General-Icons/Res_48_Light/Res_Generic-Application_48_Light.svg", "#242F3E"),
    "group-cloud": (_GRP + "AWS-Cloud-logo_32.svg", "#242F3E"),
    "group-account": (_GRP + "AWS-Account_32.svg", "#E7157B"),
    "group-region": (_GRP + "Region_32.svg", "#00A4A6"),
    "group-vpc": (_GRP + "Virtual-private-cloud-VPC_32.svg", "#8C4FFF"),
    "group-private-subnet": (_GRP + "Private-subnet_32.svg", "#00A4A6"),
    "group-public-subnet": (_GRP + "Public-subnet_32.svg", "#7AA116"),
}
# A label naming a cloud product picks its icon (first match wins; whole words, case-insensitive).
ICON_BY_LABEL = [
    (r"eventbridge scheduler", "eventbridge-scheduler"), (r"eventbridge", "eventbridge"),
    (r"api gateway", "api-gateway"), (r"cloudfront", "cloudfront"), (r"lambda", "lambda"),
    (r"fargate", "fargate"), (r"ecs|elastic container service", "ecs"), (r"rds|aurora", "rds"),
    (r"elasticache", "elasticache"), (r"s3|simple storage service", "s3"), (r"cognito", "cognito"),
    (r"bedrock", "bedrock"), (r"ses|simple email service", "ses"), (r"waf", "waf"),
    (r"secrets manager", "secrets-manager"), (r"cloudwatch", "cloudwatch"),
]
ICON_BY_KIND = {"people": "users", "external": "internet"}
GROUP_KIND_BY_LABEL = [(r"aws cloud", "cloud"), (r"private subnet", "private-subnet"),
                       (r"public subnet", "public-subnet"), (r"vpc", "vpc"), (r"account", "account"),
                       (r"region", "region")]


class SketchError(ValueError):
    pass


def default_icon_dir() -> Path:
    return Path(os.environ.get("ARCH_VIDEO_CACHE") or Path(__file__).resolve().parent / ".cache") / "aws-icons"


def _lines(v) -> list[str]:
    if v is None:
        return []
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


def _match(label: str, table: list[tuple[str, str]]) -> str | None:
    low = label.lower()
    for pat, key in table:
        if re.search(rf"(?<![a-z0-9])(?:{pat})(?![a-z0-9])", low):
            return key
    return None


def node_icon(n: dict) -> str | None:
    """The icon key a node draws: its "icon" ("none" = no icon), else the product its label names, else its kind's."""
    if "icon" in n:
        return None if n["icon"] in (None, "none") else n["icon"]
    return _match(str(n.get("label", "")), ICON_BY_LABEL) or ICON_BY_KIND.get(n.get("kind", "service"))


def group_style(g: dict) -> dict:
    """Border colour, dash, corner icon and fill of a group frame (official AWS group styles)."""
    kind = g.get("kind") or _match(str(g.get("label", "")), GROUP_KIND_BY_LABEL)
    icon = g.get("icon") or (None if kind else _match(str(g.get("label", "")), ICON_BY_LABEL))
    if kind in GROUP_KINDS and kind != "generic":
        st = dict(GROUP_KINDS[kind])
    elif icon:
        st = {"stroke": ICONS[icon][1], "icon": icon} if icon in ICONS else {"stroke": GROUP_KINDS["generic"]["stroke"]}
    else:
        st = dict(GROUP_KINDS["generic"])
    if g.get("style") == "dashed":
        st["dash"] = True
    elif g.get("style") == "solid":
        st["dash"] = False
    return st


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
        if n.get("icon") not in (None, "none") and n.get("icon") not in ICONS:
            problems.append(f"diagram {key}: node {nid} icon must be one of {sorted(ICONS)} or none")
    gids, framed = set(), []
    for g in groups:
        gid = g.get("id")
        if not gid or gid in gids or gid in ids:
            problems.append(f"diagram {key}: group id {gid!r} missing or repeated")
        gids.add(gid)
        if not str(g.get("label", "")).strip():
            problems.append(f"diagram {key}: group {gid} has no label")
        if g.get("kind") is not None and g["kind"] not in GROUP_KINDS:
            problems.append(f"diagram {key}: group {gid} kind must be one of {sorted(GROUP_KINDS)}")
        if g.get("icon") is not None and g["icon"] not in ICONS:
            problems.append(f"diagram {key}: group {gid} icon must be one of {sorted(ICONS)}")
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


# ---- official icons: extraction (setup.sh) and inlining as plain shapes -------------------------------------------

_SHAPES = {"g", "path", "rect", "circle", "ellipse", "polygon", "polyline", "line"}
_DROPPED = {"title", "desc", "metadata"}
_ATTRS = {"d", "fill", "fill-rule", "clip-rule", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
          "stroke-miterlimit", "stroke-dasharray", "opacity", "fill-opacity", "stroke-opacity", "x", "y", "width",
          "height", "rx", "ry", "cx", "cy", "r", "points", "x1", "y1", "x2", "y2", "transform"}
_ROOT_ATTRS = {"fill", "fill-rule", "clip-rule", "stroke", "stroke-width"}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _shape_markup(el, name: str) -> str:
    tag = _local(el.tag)
    if tag not in _SHAPES:
        raise SketchError(f"icon {name}: element <{tag}> is not allowed (shapes only: no text, image, link, style)")
    attrs = []
    for k, v in el.attrib.items():
        k = _local(k)
        if k not in _ATTRS:
            continue                      # ids, classes, xlink and anything else that could carry words
        if "url(" in v or "<" in v or '"' in v:
            raise SketchError(f"icon {name}: attribute {k} holds a reference or markup")
        attrs.append(f' {k}="{escape(v)}"')
    kids = "".join(_shape_markup(c, name) for c in el if _local(c.tag) not in _DROPPED)
    if (el.text or "").strip():
        raise SketchError(f"icon {name}: element <{tag}> holds text")
    return f"<{tag}{''.join(attrs)}>{kids}</{tag}>" if kids else f"<{tag}{''.join(attrs)}/>"


def icon_shapes(path: Path) -> tuple[str, float]:
    """(inner markup, viewBox size) of one official icon, reduced to plain shapes; refuses anything else."""
    root = ET.fromstring(path.read_bytes())
    if _local(root.tag) != "svg":
        raise SketchError(f"icon {path.name}: not an SVG")
    vb = [float(x) for x in re.split(r"[ ,]+", (root.get("viewBox") or "").strip()) if x]
    if len(vb) != 4 or vb[0] or vb[1] or vb[2] != vb[3]:
        raise SketchError(f"icon {path.name}: needs a square viewBox at 0 0")
    outer = "".join(f' {k}="{escape(v)}"' for k, v in root.attrib.items() if _local(k) in _ROOT_ATTRS
                    and "url(" not in v)
    body = "".join(_shape_markup(c, path.name) for c in root if _local(c.tag) not in _DROPPED)
    return f"<g{outer}>{body}</g>", vb[2]


class _Icons:
    def __init__(self, icon_dir: Path | None):
        self.dir = Path(icon_dir) if icon_dir else None
        self.cache: dict[str, tuple[str, float]] = {}

    def has(self, key: str | None) -> bool:
        return bool(key and self.dir and key in ICONS)

    def draw(self, key: str, x: float, y: float, size: float) -> str:
        if key not in self.cache:
            f = self.dir / f"{key}.svg"
            if not f.exists():
                raise SketchError(f"icon {key} missing in {self.dir} (run tools/uat/arch/setup.sh)")
            self.cache[key] = icon_shapes(f)
        inner, vb = self.cache[key]
        return (f'<g class="icon" transform="translate({x:.1f} {y:.1f}) scale({size / vb:.4f})">' + inner + "</g>")


def extract_icons(package: Path, out_dir: Path) -> list[str]:
    """setup.sh: copy the ICONS files out of the official package zip as <key>.svg, checking each one inlines."""
    out_dir.mkdir(parents=True, exist_ok=True)
    done = []
    with zipfile.ZipFile(package) as z:
        for key, (member, _colour) in sorted(ICONS.items()):
            data = z.read(member)
            (out_dir / f"{key}.svg").write_bytes(data)
            icon_shapes(out_dir / f"{key}.svg")
            done.append(key)
    (out_dir / "VERSION").write_text(ICON_PACKAGE + "\n", encoding="utf-8")
    return done


# ---- layout and drawing -------------------------------------------------------------------------------------------

STORE_TOP = 10          # extra room under a store's lid (stores drawn without an icon)


def _node_h(n: dict, icons: _Icons) -> float:
    if icons.has(node_icon(n)):
        return 2 * NODE_PAD_Y + ICON + ICON_GAP + LINE_H + SUB_H * len(_lines(n.get("sub")))
    lid = STORE_TOP if n.get("kind") == "store" else 0
    return 2 * NODE_PAD_Y + LINE_H + SUB_H * len(_lines(n.get("sub"))) + lid


def _layout(spec: dict, icons: _Icons):
    nodes, groups = spec.get("nodes") or [], spec.get("groups") or []
    cols = 1 + max([n["at"][0] for n in nodes] + [g["cells"][2] for g in groups])
    rows = 1 + max([n["at"][1] for n in nodes] + [g["cells"][3] for g in groups])
    depth = {g["id"]: sum(1 for o in groups if o is not g and _within(g["cells"], o["cells"])) for g in groups}
    starts = {r: sorted((g for g in groups if g["cells"][1] == r), key=lambda g: depth[g["id"]]) for r in range(rows)}
    ends = {r: [g for g in groups if g["cells"][3] == r] for r in range(rows)}
    body = {r: max([_node_h(n, icons) for n in nodes if n["at"][1] == r] + [LINE_H + 2 * NODE_PAD_Y])
            for r in range(rows)}
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
        for g in starts[r]:
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
        h = _node_h(n, icons)
        x = PAD + c * CELL_W + (CELL_W - NODE_W) / 2
        y = row_y[r] + head[r] + 22 + (body[r] - h) / 2
        nbox[n["id"]] = {"x": x, "y": y, "w": NODE_W, "h": h}
    return width, height, box, nbox


def _t(x, y, text, size, weight=400, fill=INK, anchor="middle", halo=False) -> str:
    ring = f' paint-order="stroke" stroke="{CARD}" stroke-width="6" stroke-linejoin="round"' if halo else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}"{ring}>{escape(text, quote=False)}</text>')


def _shape(n: dict, b: dict, with_icon: bool) -> str:
    x, y, w, h = b["x"], b["y"], b["w"], b["h"]
    kind = n.get("kind", "service")
    if kind == "store" and not with_icon:
        ry = 9
        return (f'<path d="M{x:.1f},{y + ry:.1f} a{w / 2:.1f},{ry} 0 0,1 {w:.1f},0 v{h - 2 * ry:.1f} '
                f'a{w / 2:.1f},{ry} 0 0,1 {-w:.1f},0 z" fill="{CARD}" stroke="{LINE}" stroke-width="2"/>'
                f'<path d="M{x:.1f},{y + ry:.1f} a{w / 2:.1f},{ry} 0 0,0 {w:.1f},0" fill="none" stroke="{LINE}" '
                f'stroke-width="2"/>')
    rx = (min(h / 2, 24) if kind == "people" else 10)
    dash = ' stroke-dasharray="7 5"' if kind == "external" else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" ry="{rx:.1f}" '
            f'fill="{CARD}" stroke="{LINE}" stroke-width="2"{dash}/>')


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
    L, W = 11, 5.5
    if abs(x1 - x0) > abs(y1 - y0):
        s = 1 if x1 > x0 else -1
        pts = [(x1, y1), (x1 - s * L, y1 - W), (x1 - s * L, y1 + W)]
    else:
        s = 1 if y1 > y0 else -1
        pts = [(x1, y1), (x1 - W, y1 - s * L), (x1 + W, y1 - s * L)]
    return '<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + f'" fill="{BODY}"/>'


def render(spec: dict, key: str = "sketch", icon_dir: Path | None = None) -> str:
    problems = validate(spec, key)
    if problems:
        raise SketchError("; ".join(problems))
    icons = _Icons(icon_dir)
    width, height, gbox, nbox = _layout(spec, icons)
    keys = {n["id"]: f"n{i}" for i, n in enumerate(spec["nodes"], 1)}
    # Paint order: edges, then the group frames (a faint tint at most; their titles keep a halo so an arrow passes
    # behind a title, never through it), then the nodes.
    parts, frames = [], []
    for g in sorted(spec.get("groups") or [], key=lambda g: gbox[g["id"]]["depth"]):
        b = gbox[g["id"]]
        st = group_style(g)
        dash = ' stroke-dasharray="8 6"' if st.get("dash") else ""
        fill = f'fill="{st["fill"]}" fill-opacity="0.55"' if st.get("fill") else 'fill="none"'
        body = [f'<rect x="{b["x"]:.1f}" y="{b["y"]:.1f}" width="{b["w"]:.1f}" height="{b["h"]:.1f}" rx="2" ry="2" '
                f'{fill} stroke="{st["stroke"]}" stroke-width="2.4"{dash}/>']
        tx = b["x"] + 14
        if icons.has(st.get("icon")):
            body.append(icons.draw(st["icon"], b["x"], b["y"], GROUP_ICON))
            tx = b["x"] + GROUP_ICON + 10
        body.append(_t(tx, b["y"] + 22, str(g["label"]), GROUP_PX, 600, INK, "start", halo=True))
        for sub in _lines(g.get("sub"))[:1]:
            body.append(_t(tx, b["y"] + 22 + SUB_H, sub, SUB_PX, 500, MUTED, "start", halo=True))
        frames.append('<g class="cluster">' + "".join(body) + "</g>")
    for e in spec.get("edges") or []:
        pts = _route(nbox[e["from"]], nbox[e["to"]], float(e.get("bend", 0.5)))
        dash = ' stroke-dasharray="7 5"' if e.get("style") == "dashed" else ""
        path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        body = [f'<path d="{path}" fill="none" stroke="{BODY}" stroke-width="2.2"{dash}/>', _arrow(pts[-2], pts[-1])]
        lab = _lines(e.get("label"))
        if lab:
            i = max(range(len(pts) - 1), key=lambda k: abs(pts[k + 1][0] - pts[k][0]) + abs(pts[k + 1][1] - pts[k][1]))
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            for j, line in enumerate(lab):
                body.append(_t(mx + (8 if x0 == x1 else 0), my - 6 + j * 16, line, EDGE_PX, 500, MUTED,
                               "start" if x0 == x1 else "middle", halo=True))
        ends = f'data-from="{keys[e["from"]]}" data-to="{keys[e["to"]]}"'
        parts.append(f'<g class="edge" {ends}>' + "".join(body) + "</g>")
    parts += frames
    for n in spec["nodes"]:
        b = nbox[n["id"]]
        cx = b["x"] + b["w"] / 2
        ik = node_icon(n)
        with_icon = icons.has(ik)
        body = [_shape(n, b, with_icon)]
        top = b["y"] + NODE_PAD_Y
        if with_icon:
            body.append(icons.draw(ik, cx - ICON / 2, top, ICON))
            top += ICON + ICON_GAP
        elif n.get("kind") == "store":
            top += STORE_TOP
        y = top + 17
        body.append(_t(cx, y, str(n["label"]), LABEL_PX, 600))
        for j, sub in enumerate(_lines(n.get("sub")), 1):
            body.append(_t(cx, y + 3 + j * SUB_H, sub, SUB_PX, 500, MUTED))
        parts.append(f'<g class="node" data-k="{keys[n["id"]]}">' + "".join(body) + "</g>")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" '
            f'viewBox="0 0 {width:.0f} {height:.0f}" preserveAspectRatio="xMidYMid meet">'
            f'<g class="graph">' + "".join(parts) + "</g></svg>")


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[0] == "--extract-icons":
        done = extract_icons(Path(argv[1]), Path(argv[2]))
        print(f"icons: {len(done)} in {argv[2]}")
        return 0
    if len(argv) != 2:
        print(__doc__)
        return 2
    icon_dir = default_icon_dir()
    Path(argv[1]).write_text(render(json.loads(Path(argv[0]).read_text(encoding="utf-8")), Path(argv[0]).stem,
                                    icon_dir if (icon_dir / "VERSION").exists() else None), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
