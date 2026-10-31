"""Unit tests of build.py's mux arguments (soft subtitle tracks beside the two voices). No ffmpeg, $0.

  cd tools/uat && ./venv/bin/python -m unittest discover -s tests   (build.py needs numpy + soundfile from the venv;
                                                                     a plain python3 skips these tests)
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    import build  # noqa: E402
except ImportError:  # numpy / soundfile live in tools/uat/venv
    build = None

VOICES = [(0, "en", "English narration", 1), (1, "vi", "Vietnamese narration", 2)]


@unittest.skipIf(build is None, "build.py needs the tools/uat venv (numpy, soundfile)")
class MuxArgs(unittest.TestCase):
    def test_burned_or_no_burn_has_no_subtitle_track(self):
        a = build.mux_args(VOICES, [])
        self.assertEqual(a[:6], ["-map", "0:v", "-map", "1:a", "-map", "2:a"])
        self.assertNotIn("-c:s", a)
        self.assertIn("language=vie", a)
        self.assertEqual(a[a.index("-disposition:a:0") + 1], "default")

    def test_soft_build_maps_both_languages_english_shown_first(self):
        a = build.mux_args(VOICES, [("en", 3), ("vi", 4)])
        self.assertEqual(a[6:10], ["-map", "3:s", "-map", "4:s"])
        self.assertEqual(a[a.index("-c:s") + 1], "mov_text")
        self.assertEqual(a[a.index("-disposition:s:0") + 1], "default")
        self.assertEqual(a[a.index("-disposition:s:1") + 1], "0")
        self.assertEqual(a[a.index("-metadata:s:s:1") + 1], "language=vie")
        self.assertIn("title=Tiếng Việt", a)


if __name__ == "__main__":
    unittest.main()
