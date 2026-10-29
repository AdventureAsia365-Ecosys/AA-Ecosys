"""Draw the two AWS group icons the ``diagrams`` package does not ship (AA-697): run once, commit ``icons/*.png``.

    python _group_icons.py      # needs Pillow and the diagrams package (for the AWS logo)

- ``icons/aws-cloud.png``: the "AWS Cloud" group icon, the AWS logo in white (orange smile) on a squid-ink square.
- ``icons/region.png``: the "Region" group icon, a teal flag outline.

The other group icons (VPC, public subnet, private subnet, ECS, people, Vercel, GitHub, internet) come straight from
the icon set of the ``diagrams`` package at render time (``_common.GROUP_ICONS``).
"""
from __future__ import annotations

from pathlib import Path

import diagrams
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
OUT = HERE / "icons"
RES = Path(diagrams.__file__).resolve().parent.parent / "resources"
SIZE = 128
SQUID_INK = (35, 47, 62, 255)
TEAL = (0, 164, 166, 255)


def aws_cloud() -> Image.Image:
    logo = Image.open(RES / "aws" / "aws.png").convert("RGBA")
    px = logo.load()
    for y in range(logo.height):
        for x in range(logo.width):
            r, g, b, a = px[x, y]
            if a and not (r > 180 and g > 100 and b < 120):  # everything but the orange smile turns white
                px[x, y] = (255, 255, 255, a)
    logo.thumbnail((int(SIZE * 0.78), int(SIZE * 0.78)), Image.LANCZOS)
    im = Image.new("RGBA", (SIZE, SIZE), SQUID_INK)
    im.alpha_composite(logo, ((SIZE - logo.width) // 2, (SIZE - logo.height) // 2))
    return im


def region() -> Image.Image:
    im = Image.new("RGBA", (SIZE, SIZE), (255, 255, 255, 0))
    d = ImageDraw.Draw(im)
    w = SIZE // 14
    d.line([(SIZE * 0.22, SIZE * 0.12), (SIZE * 0.22, SIZE * 0.92)], fill=TEAL, width=w)   # pole
    flag = [(SIZE * 0.22, SIZE * 0.16), (SIZE * 0.82, SIZE * 0.16), (SIZE * 0.66, SIZE * 0.36),
            (SIZE * 0.82, SIZE * 0.56), (SIZE * 0.22, SIZE * 0.56)]
    d.line(flag + [flag[0]], fill=TEAL, width=w, joint="curve")
    return im


def main() -> None:
    OUT.mkdir(exist_ok=True)
    aws_cloud().save(OUT / "aws-cloud.png", optimize=True)
    region().save(OUT / "region.png", optimize=True)
    print("wrote", ", ".join(p.name for p in sorted(OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
