#!/usr/bin/env python3
"""Compress screenshots in place before they are committed (AA-1161; tools/repo/lean_guard.py suggests it).

  PNG   quantized to 256 colours (palette PNG, optimize on); a screenshot usually shrinks 50-80 % and stays legible;
  JPEG  re-saved at quality 75 (optimize, progressive);
  --webp  also converts PNG / JPEG to WebP (quality 75) next to the source and removes the source: the format
        tools/docs/check_images.py wants for new audit images (a JPEG is refused there).

File names are kept (except with --webp), metadata (EXIF, text chunks) is dropped, and a file is only rewritten when
the result is smaller. Prints one line per file (before -> after) and a total. Folders are walked recursively.

Needs Pillow, which tools/docs/requirements.txt does not carry (the lint tools do not need it). Any venv with Pillow
works, e.g. the AA-CIS-App one:
  apps/AA-CIS-App/.venv/bin/python tools/docs/compress_images.py docs/audits/2026-11-20-S286-session/
  python3 tools/docs/compress_images.py --dry-run shot.png      # sizes only, nothing written

Exit codes: 0 done, 1 a file could not be read or written, 2 Pillow missing or bad arguments.
"""

from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

PNG = {".png"}
JPEG = {".jpg", ".jpeg"}
JPEG_QUALITY = 75
WEBP_QUALITY = 75
PALETTE_COLOURS = 256


def human(n: int) -> str:
    return f"{n / (1024 * 1024):.1f} MiB" if n >= 1024 * 1024 else f"{n / 1024:.0f} KiB"


def encode(img, suffix: str, webp: bool) -> tuple[bytes, str]:
    """The compressed bytes and the suffix to write them under."""
    from PIL import Image

    buf = io.BytesIO()
    if webp:
        mode = "RGBA" if img.mode in ("RGBA", "LA") or "transparency" in img.info else "RGB"
        img.convert(mode).save(buf, "WEBP", quality=WEBP_QUALITY, method=6)
        return buf.getvalue(), ".webp"
    if suffix in PNG:
        if img.mode == "P":
            pal = img
        elif img.mode in ("RGBA", "LA") or "transparency" in img.info:
            pal = img.convert("RGBA").quantize(colors=PALETTE_COLOURS, method=Image.Quantize.FASTOCTREE)
        else:
            pal = img.convert("RGB").quantize(colors=PALETTE_COLOURS, method=Image.Quantize.MEDIANCUT)
        pal.save(buf, "PNG", optimize=True)
        return buf.getvalue(), suffix
    img.convert("RGB").save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return buf.getvalue(), suffix


def compress_file(path: Path, dry_run: bool = False, webp: bool = False) -> tuple[int, int, Path]:
    """(bytes before, bytes after, written path). After == before when the file was kept as it was."""
    from PIL import Image

    before = path.stat().st_size
    with Image.open(path) as img:
        img.load()
        data, suffix = encode(img, path.suffix.lower(), webp)
    target = path.with_suffix(suffix) if webp else path
    if len(data) >= before and not webp:
        return before, before, path
    if not dry_run:
        tmp = target.with_name(target.name + ".tmp-compress")
        tmp.write_bytes(data)
        os.replace(tmp, target)
        if webp and target != path:
            path.unlink()
    return before, len(data), target


def iter_images(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for p in map(Path, paths):
        if p.is_dir():
            out.extend(sorted(f for f in p.rglob("*") if f.is_file() and f.suffix.lower() in PNG | JPEG))
        elif p.is_file():
            out.append(p)
        else:
            print(f"skip  {p}: not found", file=sys.stderr)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("paths", nargs="+", help="image files or folders")
    ap.add_argument("--dry-run", action="store_true", help="print the sizes, write nothing")
    ap.add_argument("--webp", action="store_true", help="convert to WebP (quality 75) and remove the source")
    args = ap.parse_args(argv)
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("compress_images: Pillow is missing; run it with a venv that has it "
              "(apps/AA-CIS-App/.venv/bin/python) or pip install Pillow", file=sys.stderr)
        return 2
    total_before = total_after = 0
    errors = 0
    for f in iter_images(args.paths):
        if f.suffix.lower() not in PNG | JPEG:
            print(f"skip  {f}: not a PNG or JPEG")
            continue
        try:
            before, after, target = compress_file(f, dry_run=args.dry_run, webp=args.webp)
        except Exception as e:  # a broken image must not stop the others
            print(f"FAIL  {f}: {type(e).__name__}: {e}")
            errors += 1
            continue
        total_before += before
        total_after += after
        if after == before and target == f:
            print(f"keep  {f}: {human(before)} (already small)")
        else:
            pct = 100 * (before - after) / before if before else 0
            name = f if target == f else f"{f} -> {target.name}"
            print(f"{'would' if args.dry_run else 'done '} {name}: {human(before)} -> {human(after)} (-{pct:.0f} %)")
    print(f"total: {human(total_before)} -> {human(total_after)}{' (dry run)' if args.dry_run else ''}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
