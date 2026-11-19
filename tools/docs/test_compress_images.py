"""Unit tests for compress_images.py (AA-1161). Skipped where Pillow is not installed (the docs-lint venv has no
Pillow; run them with a venv that has it, e.g. apps/AA-CIS-App/.venv/bin/python -m unittest ...).

Fixture images are drawn in code (gradients and noise that look like a busy screenshot); no real screenshot is used.
"""

from __future__ import annotations

import contextlib
import io
import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compress_images as ci  # noqa: E402

try:
    from PIL import Image
except ImportError:  # pragma: no cover - depends on the venv
    Image = None


def busy_image(mode: str = "RGB", size: tuple[int, int] = (480, 320)):
    rng = random.Random(1161)
    img = Image.new(mode, size)
    px = img.load()
    for y in range(size[1]):
        for x in range(size[0]):
            base = ((x * 255) // size[0], (y * 255) // size[1], rng.randrange(256))
            px[x, y] = base + (255,) if mode == "RGBA" else base
    return img


@unittest.skipIf(Image is None, "Pillow not installed")
class CompressImages(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def run_main(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            rc = ci.main(list(args))
        return rc, out.getvalue()

    def test_png_is_quantized_in_place_and_smaller(self):
        p = self.dir / "screen.png"
        busy_image().save(p, "PNG")
        before = p.stat().st_size
        rc, out = self.run_main(str(self.dir))
        self.assertEqual(rc, 0, out)
        self.assertLess(p.stat().st_size, before)
        with Image.open(p) as img:
            self.assertEqual(img.mode, "P")
            self.assertEqual(img.size, (480, 320))
        self.assertIn("screen.png", out)
        self.assertIn("total:", out)

    def test_rgba_png_keeps_its_name(self):
        p = self.dir / "overlay.png"
        busy_image("RGBA").save(p, "PNG")
        rc, out = self.run_main(str(p))
        self.assertEqual(rc, 0, out)
        self.assertTrue(p.exists())

    def test_jpeg_quality_75(self):
        p = self.dir / "photo.jpg"
        busy_image().save(p, "JPEG", quality=98)
        before = p.stat().st_size
        rc, out = self.run_main(str(p))
        self.assertEqual(rc, 0, out)
        self.assertLess(p.stat().st_size, before)

    def test_dry_run_writes_nothing(self):
        p = self.dir / "screen.png"
        busy_image().save(p, "PNG")
        before = p.read_bytes()
        rc, out = self.run_main("--dry-run", str(p))
        self.assertEqual(rc, 0, out)
        self.assertEqual(p.read_bytes(), before)
        self.assertIn("would", out)

    def test_small_file_is_kept(self):
        p = self.dir / "tiny.png"
        Image.new("P", (4, 4)).save(p, "PNG", optimize=True)
        before = p.read_bytes()
        rc, out = self.run_main(str(p))
        self.assertEqual(rc, 0, out)
        self.assertEqual(p.read_bytes(), before)
        self.assertIn("keep", out)

    def test_webp_conversion_replaces_the_source(self):
        p = self.dir / "audit.jpg"
        busy_image().save(p, "JPEG", quality=95)
        rc, out = self.run_main("--webp", str(p))
        self.assertEqual(rc, 0, out)
        self.assertFalse(p.exists())
        self.assertTrue((self.dir / "audit.webp").exists())

    def test_broken_file_is_reported(self):
        p = self.dir / "broken.png"
        p.write_bytes(b"not an image")
        rc, out = self.run_main(str(p))
        self.assertEqual(rc, 1)
        self.assertIn("FAIL", out)


if __name__ == "__main__":
    unittest.main()
