"""Shared helpers for the AA-Ecosys architecture diagrams (AA-697).

Each ``<name>.py`` next to this file draws one view with the Python ``diagrams`` package (mingrammer), which ships the
official AWS Architecture Icons and lays out with Graphviz. ``render.py`` runs them all and writes ``<name>.svg``.

The SVG Graphviz writes points at icon PNGs by absolute path on the machine that rendered it. ``finalize_svg`` turns
every icon into an inline ``data:image/png;base64`` URI (downscaled when Pillow is installed), drops the absolute paths
and the Graphviz comments and numbers the random node ids. ``check_svg_safe`` then refuses anything a reader could run
or fetch (scripts, ``foreignObject``, event-handler attributes, ``javascript:``, any reference that is neither a
fragment nor an inline PNG) and any account or resource ID in the text. That check is rule 9 of the docs reader
bundle builder (``tools/docs/build_docs_reader.py``), imported here so render time and publish time apply one rule.

Labels never carry account IDs, ARNs or network IDs (security groups, subnets, VPCs): names and roles only.
"""
from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools" / "docs"))

from build_docs_reader import svg_problems  # noqa: E402  (one safety rule for render time and publish time)

# One look for every view: white canvas, readable labels. Curved splines, not ortho: Graphviz cannot place edge
# labels on orthogonal edges (they drift away from their line).
GRAPH_ATTR = {
    "fontname": "Helvetica",
    "fontsize": "22",
    "labelloc": "t",
    "pad": "0.4",
    "nodesep": "0.55",
    "ranksep": "0.9",
    "bgcolor": "white",
    "splines": "spline",
    "compound": "true",
}
NODE_ATTR = {"fontname": "Helvetica", "fontsize": "12"}
EDGE_ATTR = {"fontname": "Helvetica", "fontsize": "10", "color": "#545B64"}

# Cluster styles (AWS group conventions: account = dark outline, region = dashed teal, VPC = purple, others light).
ACCOUNT = {"bgcolor": "#FFFFFF", "pencolor": "#232F3E", "penwidth": "2", "fontsize": "15", "style": "rounded"}
REGION = {"bgcolor": "#FFFFFF", "pencolor": "#147EBA", "style": "dashed", "fontsize": "13"}
VPC = {"bgcolor": "#F7F3FC", "pencolor": "#8C4FFF", "penwidth": "1.5", "fontsize": "13"}
GROUP = {"bgcolor": "#F2F3F3", "pencolor": "#AAB7B8", "fontsize": "13", "style": "rounded"}
EXTERNAL = {"bgcolor": "#FFF8EE", "pencolor": "#D86613", "fontsize": "13", "style": "rounded,dashed"}

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


def cluster_ref(cluster, end: str = "lhead") -> dict:
    """Edge attributes that clip an edge at a cluster border (``lhead`` = arrow into it, ``ltail`` = out of it)."""
    return {end: cluster.name}
