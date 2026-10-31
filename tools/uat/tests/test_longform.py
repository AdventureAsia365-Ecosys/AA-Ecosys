"""Unit tests of longform.py's pure parts (offset math, chapters, chunk picking). No ffmpeg, $0.

  cd tools/uat && python3 -m unittest discover -s tests
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import longform as lf  # noqa: E402


class Timestamps(unittest.TestCase):
    def test_round_trip(self):
        for sec in (0, 1.5, 59.999, 61.25, 3725.04):
            self.assertAlmostEqual(lf.parse_ts(lf.fmt_ts(sec)), sec, places=3)
        self.assertEqual(lf.fmt_ts(3725.04), "01:02:05,040")
        self.assertEqual(lf.fmt_ts(1.5, "."), "00:00:01.500")
        self.assertEqual(lf.fmt_ts(-2), "00:00:00,000")

    def test_parse_srt(self):
        text = "1\n00:00:00,250 --> 00:00:04,000\nHello\n\n2\n00:00:04,000 --> 00:00:09,500\nTwo\nlines\n"
        self.assertEqual(lf.parse_srt(text), [(0.25, 4.0, "Hello"), (4.0, 9.5, "Two\nlines")])
        self.assertEqual(lf.parse_srt(""), [])


class Offsets(unittest.TestCase):
    def test_cards_and_chunks_shift_cues(self):
        segs = [(2.5, None), (10.0, [(0.0, 4.0, "a"), (4.0, 10.0, "b")]), (2.5, None), (6.0, [(0.5, 6.0, "c")])]
        self.assertEqual(lf.merge_cues(segs), [(2.5, 6.5, "a"), (6.5, 12.5, "b"), (15.5, 21.0, "c")])

    def test_cue_clipped_to_its_chunk(self):
        segs = [(5.0, [(1.0, 8.0, "long")]), (3.0, [(0.0, 1.0, "next")])]
        self.assertEqual(lf.merge_cues(segs), [(1.0, 5.0, "long"), (5.0, 6.0, "next")])

    def test_cue_outside_its_chunk_dropped(self):
        self.assertEqual(lf.merge_cues([(2.0, [(3.0, 4.0, "late")])]), [])


class Chapters(unittest.TestCase):
    def setUp(self):
        self.ch = lf.chapter_starts([("Intro", 2.5, 30.0), ("Home", 2.5, 50.25)])

    def test_starts_at_cards(self):
        self.assertEqual(self.ch, [("Intro", 0.0, 32.5), ("Home", 32.5, 85.25)])

    def test_ffmetadata(self):
        meta = lf.ffmetadata(self.ch, "Review; v1")
        self.assertTrue(meta.startswith(";FFMETADATA1\ntitle=Review\\; v1\n"))
        self.assertIn("[CHAPTER]\nTIMEBASE=1/1000\nSTART=32500\nEND=85250\ntitle=Home", meta)
        self.assertEqual(meta.count("[CHAPTER]"), 2)

    def test_escaping(self):
        self.assertIn("title=a\\=b\\#c", lf.ffmetadata([("a=b#c", 0, 1)]))

    def test_chapters_txt(self):
        self.assertEqual(lf.chapters_txt(self.ch), "00:00 Intro\n00:32 Home\n")
        self.assertEqual(lf.chapters_txt([("A", 0, 10), ("B", 3700, 3800)]), "0:00:00 A\n1:01:40 B\n")


class Picking(unittest.TestCase):
    def test_newest_version_per_id(self):
        files = ["out/CRM-REV-01_20261105_v1.mp4", "out/CRM-REV-01_20261105_v2.mp4", "out/CRM-REV-00_20261104_v3.mp4",
                 "out/CRM-REV-00_20261105_v1.mp4", "out/CRM-REV-01_20261105_v2.en.srt", "out/OTHER-01_20261105_v1.mp4"]
        self.assertEqual(lf.pick_chunks(files, "CRM-REV-"),
                         {"CRM-REV-00": "out/CRM-REV-00_20261105_v1.mp4", "CRM-REV-01": "out/CRM-REV-01_20261105_v2.mp4"})

    def test_highlight_ids(self):
        self.assertEqual(lf.highlight_ids("R01, R03,R15", "CRM-REV-"), ["CRM-REV-01", "CRM-REV-03", "CRM-REV-15"])
        self.assertEqual(lf.highlight_ids("4", "CRM-REV-"), ["CRM-REV-04"])
        with self.assertRaises(ValueError):
            lf.highlight_ids("Rx", "CRM-REV-")


if __name__ == "__main__":
    unittest.main()
