"""Public label profile (AA-1021): turns an internal architecture SVG into a public one.

  python -I labels.py <diagram.svg> <out.svg> [--private DIR]     # one diagram through the profile

The profile is a gitignored JSON file (<private>/labels.public.json; template: labels.public.example.json):
  {"map":     {"<exact internal text>": "<public text>" | null},     null drops the text element
   "replace": [["<regex>", "<public text>"], ...],                    substring rewrites after "map"
   "neutral_icons": ["<public label>", ...],                          icon of that node or group -> plain shape
   "drop_titles": true}                                               (default) strip every <title>/<desc>
The internal docs keep their real names; only the copy rendered for a video or post goes through here.

What the anonymizer does to a Graphviz SVG (docs/architecture/diagrams/*.svg):
  - every <text> goes through map then replace; a null mapping removes the element;
  - <title>, <desc>, comments and the XML/DOCTYPE header are dropped (Graphviz writes node and cluster names there);
  - each node <g> gets data-k (its Graphviz node name, only if it is a short neutral key such as s14 / s14-t), each edge
    <g> gets data-from / data-to (the node names it joins), so page.py can reveal a group and its edges by label;
  - a node or group whose public label is in neutral_icons loses its icon <image> (a vendor logo, say) for a plain
    rounded square of the same size, so no logo of a vendor the series does not name reaches a frame;
  - width/height become 100% (the stage sizes it) and the viewBox stays.
Text stays where Graphviz put it (text-anchor middle), so a public label a little longer than the internal one still
reads; keep public labels about as long as the internal ones. Stdlib only.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", XLINK)
NEUTRAL_KEY = re.compile(r"^[a-z]{0,3}\d{1,4}(?:-[a-z0-9]{1,4})*$")


def load_profile(path: Path) -> dict:
    return prepare(json.loads(path.read_text(encoding="utf-8")))


def prepare(data: dict) -> dict:
    data = dict(data)
    data.setdefault("map", {})
    data.setdefault("replace", [])
    data.setdefault("drop_titles", True)
    data.setdefault("neutral_icons", [])
    data["_replace"] = [(re.compile(a), b) for a, b in data["replace"]]
    return data


def public_text(text: str, profile: dict) -> str | None:
    """The public form of one label: exact map first (None = drop), then the regex rewrites."""
    key = " ".join(text.split())
    if key in profile["map"]:
        mapped = profile["map"][key]
        if mapped is None:
            return None
        key = mapped
    for rx, repl in profile["_replace"]:
        key = rx.sub(repl, key)
    return key


def _tag(el) -> str:
    return el.tag.split("}", 1)[-1]


def anonymize_svg(svg_text: str, profile: dict) -> str:
    # Comments and the DOCTYPE never reach the page; ElementTree drops comments on parse by default.
    body = re.sub(r"<!DOCTYPE[^>]*>", "", svg_text)
    body = re.sub(r"<\?xml[^>]*\?>", "", body)
    root = ET.fromstring(body)
    parent = {c: p for p in root.iter() for c in p}
    for g in root.iter(f"{{{SVG}}}g"):
        cls = g.get("class")
        title = g.find(f"{{{SVG}}}title")
        name = (title.text or "").strip() if title is not None else ""
        if cls == "node" and NEUTRAL_KEY.match(name):
            g.set("data-k", name)
        elif cls == "edge" and "->" in name:
            a, b = (s.strip() for s in name.split("->", 1))
            if NEUTRAL_KEY.match(a) and NEUTRAL_KEY.match(b):
                g.set("data-from", a)
                g.set("data-to", b)
    drop = []
    for el in root.iter():
        tag = _tag(el)
        if tag in ("title", "desc") and profile.get("drop_titles", True):
            drop.append(el)
        elif tag == "text":
            new = public_text("".join(el.itertext()), profile)
            if new is None:
                drop.append(el)
            else:
                for child in list(el):
                    el.remove(child)
                el.text = new
        elif tag == "a":
            for attr in ("href", f"{{{XLINK}}}href", f"{{{XLINK}}}title", "title", "target"):
                el.attrib.pop(attr, None)
    for el in drop:
        parent[el].remove(el)
    neutralize_icons(root, {" ".join(x.lower().split()) for x in profile.get("neutral_icons", [])})
    for attr in list(root.attrib):
        if attr in ("width", "height"):
            root.set(attr, "100%")
    root.set("preserveAspectRatio", "xMidYMid meet")
    return ET.tostring(root, encoding="unicode")


def _texts(g) -> set[str]:
    return {" ".join("".join(t.itertext()).lower().split()) for t in g.findall(f"{{{SVG}}}text")}


def neutralize_icons(root, wanted: set[str]) -> None:
    """Swap the <image> of every node / group labelled with a wanted public label for a plain rounded square."""
    if not wanted:
        return
    groups = [g for g in root.iter(f"{{{SVG}}}g") if g.get("class") in ("node", "cluster")]
    keys = set()
    targets = []
    for g in groups:
        if _texts(g) & wanted:
            targets.append(g)
            k = g.get("data-k", "")
            if k:
                keys.add(k[:-2] if k.endswith("-t") else k)
    targets += [g for g in groups if g.get("class") == "node" and g.get("data-k") in keys]
    for g in targets:
        for img in g.findall(f"{{{SVG}}}image"):
            idx = list(g).index(img)
            g.remove(img)
            box = ET.Element(f"{{{SVG}}}rect", {
                "x": img.get("x", "0"), "y": img.get("y", "0"), "width": img.get("width", "0").replace("px", ""),
                "height": img.get("height", "0").replace("px", ""), "rx": "6", "ry": "6", "fill": "#E7ECF1",
                "stroke": "#8A97A6", "stroke-width": "1.5"})
            g.insert(idx, box)


def main(argv: list[str]) -> int:
    from gate import private_dir

    priv_arg = None
    if "--private" in argv:
        i = argv.index("--private")
        priv_arg = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    args = [a for a in argv if not a.startswith("--")]
    priv = private_dir(priv_arg)
    profile = load_profile(priv / "labels.public.json")
    Path(args[1]).write_text(anonymize_svg(Path(args[0]).read_text(encoding="utf-8"), profile), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
