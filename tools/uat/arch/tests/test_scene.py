"""Scene, timeline, caption and sketch tests (AA-1021). Invented content only. Stdlib only:

  python3 -m unittest discover -s tools/uat/arch/tests
"""
import copy
import html
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scene  # noqa: E402
import sketch  # noqa: E402

SKETCH = {
    "groups": [{"id": "cloud", "label": "Cloud account", "sub": "one region", "cells": [0, 1, 1, 2]},
               {"id": "base", "label": "Common layer", "cells": [0, 2, 1, 2], "style": "dashed"}],
    "nodes": [{"id": "guests", "label": "Guests", "at": [0, 0], "kind": "people"},
              {"id": "cat", "label": "Catalogue", "sub": ["api", "workers"], "at": [0, 1]},
              {"id": "box", "label": "Containers", "at": [1, 1]},
              {"id": "db", "label": "Managed database", "at": [0, 2], "kind": "store"},
              {"id": "ext", "label": "Vendor APIs", "at": [1, 2], "kind": "external"}],
    "edges": [{"from": "guests", "to": "cat", "label": "HTTPS & co"}, {"from": "cat", "to": "db"},
              {"from": "box", "to": "ext", "style": "dashed"}],
}

EPISODE = {
    "slug": "ep1-example", "title": "Three shops, one ledger", "series": "River notes", "episode": 1,
    "diagrams": {"eco": SKETCH},
    "description": "How an invented company splits its platform.", "hashtags": ["#aws", "#architecture"],
    "cuts": {"master": {"aspect": "16:9", "chapters": True, "max_s": 200},
             "short": {"aspect": "9:16", "max_s": 60}},
    "scenes": [
        {"id": "s1", "chapter": "The problem", "cuts": ["master", "short"],
         "visual": {"type": "title", "kicker": "Episode 1", "title": "Three shops, one ledger"},
         "sentences": ["An invented company sells river cruises.", "It runs four small apps."]},
        {"id": "s2", "chapter": "The catalogue",
         "visual": {"type": "diagram", "diagram": "eco", "title": "Catalogue", "reveal": ["Catalogue"]},
         "sentences": ["The catalogue app owns every product page.",
                       {"text": "Its workers run in containers.", "visual": {"highlight": ["Containers"]},
                        "cuts": ["master", "short"]}]},
        {"id": "s3", "chapter": "Recap", "visual": {"type": "end", "title": "Thanks"},
         "sentences": [{"text": "That is the whole picture.", "voice": "F"}]},
    ],
}


class Load(unittest.TestCase):
    def test_voices_alternate_by_scene_starting_female_in_odd_episodes(self):
        _, s = scene.load(EPISODE)
        self.assertEqual([x.voice_key for x in s], ["F", "F", "M", "M", "F"])
        self.assertEqual({x.voice for x in s}, {"af_heart", "am_michael"})
        ep = copy.deepcopy(EPISODE)
        ep["episode"] = 2
        _, s2 = scene.load(ep)
        self.assertEqual(s2[0].voice_key, "M")

    def test_sentence_visual_merges_and_cuts_default_to_master(self):
        _, s = scene.load(EPISODE)
        self.assertEqual(s[3].visual["reveal"], ["Catalogue"])
        self.assertEqual(s[3].visual["highlight"], ["Containers"])
        self.assertEqual(s[2].cuts, {"master"})
        self.assertEqual([x.id for x in scene.cut_sentences(s, "short")], ["s1.1", "s1.2", "s2.2"])

    def test_unapproved_voice_and_bad_references_are_errors(self):
        ep = copy.deepcopy(EPISODE)
        ep["voices"] = {"F": "af_bella"}
        ep["scenes"][1]["visual"]["diagram"] = "nope"
        ep["scenes"][0]["cuts"] = ["tiktok"]
        with self.assertRaises(scene.SceneError) as e:
            scene.load(ep)
        msg = str(e.exception)
        for part in ("af_bella", "diagram 'nope'", "unknown cut tiktok"):
            self.assertIn(part, msg)

    def test_all_texts_has_every_authored_string(self):
        meta, s = scene.load(EPISODE)
        texts = scene.all_texts(EPISODE, s)
        self.assertIn("s1.1:text", texts)
        self.assertEqual(texts["s1.1:visual.kicker"], "Episode 1")
        self.assertEqual(texts["hashtags"], "#aws #architecture")
        self.assertNotIn("s2.1:visual.reveal", texts)   # names of drawn labels; the drawn text is checked itself


class Timeline(unittest.TestCase):
    def setUp(self):
        self.meta, self.s = scene.load(EPISODE)
        self.dur = {x.id: 3.0 for x in self.s}

    def test_timeline_gaps_and_total(self):
        tl, total = scene.timeline(scene.cut_sentences(self.s, "master"), self.dur)
        self.assertEqual(tl[0]["start"], scene.INTRO_S)
        self.assertAlmostEqual(tl[1]["start"], tl[0]["end"] + scene.SENT_GAP_S)
        self.assertAlmostEqual(tl[2]["start"], tl[1]["end"] + scene.SENT_GAP_S + scene.SCENE_GAP_S)
        self.assertAlmostEqual(total, tl[-1]["end"] + scene.OUTRO_S, places=3)

    def test_keyframes_one_per_visual_run(self):
        tl, total = scene.timeline(scene.cut_sentences(self.s, "master"), self.dur)
        kf = scene.keyframes(tl, total)
        self.assertEqual(len(kf), 4)   # title, diagram, diagram + highlight, end
        self.assertEqual(kf[0]["at"], 0.0)
        self.assertEqual(kf[-1]["until"], total)
        for a, b in zip(kf, kf[1:]):
            self.assertEqual(a["until"], b["at"])
            self.assertLess(b["at"], [e for e in tl if scene.visual_key(e["visual"]) == b["key"]][0]["start"])

    def test_cues_fit_the_aspect_and_never_overlap(self):
        long = {"text": "The catalogue app owns every product page, every price note and every photo caption, "
                        "and it hands them to the other apps through one contract."}
        tl = [{"id": "x", "scene": "s", "chapter": "c", "start": 1.0, "end": 9.0, "text": long["text"],
               "voice": "af_heart", "visual": {}}]
        for aspect, limit in scene.CUE_CHARS.items():
            cs = scene.cues(tl, aspect, 12.0)
            self.assertTrue(all(len(c[2]) <= limit for c in cs), aspect)
            self.assertTrue(all(a[1] <= b[0] for a, b in zip(cs, cs[1:])), aspect)
            self.assertEqual(" ".join(c[2] for c in cs), long["text"])

    def test_chapters_and_length_rules(self):
        tl, total = scene.timeline(scene.cut_sentences(self.s, "master"), self.dur)
        ch = scene.chapters(tl)
        self.assertEqual([c[1] for c in ch], ["The problem", "The catalogue", "Recap"])
        self.assertEqual(ch[0][0], 0.0)
        problems = scene.check_cut("master", {"max_s": 10}, total, ch)
        self.assertTrue(any("longer than max_s" in p for p in problems))
        self.assertTrue(any("YouTube needs 10s" in p for p in problems))   # Recap is one 3 s sentence
        self.assertEqual(scene.check_cut("short", {"max_s": 60}, 40.0, None), [])

    def test_sidecars(self):
        cs = [[0.5, 2.0, "First line"], [2.1, 3.0, "Second-line"]]
        self.assertIn("00:00:00,500 --> 00:00:02,000", scene.srt(cs))
        self.assertTrue(scene.vtt(cs).startswith("WEBVTT"))
        a = scene.ass(cs, "9:16")
        self.assertIn("PlayResY: 1920", a)
        self.assertIn("Second‑line", a)   # no break inside a hyphenated word
        self.assertIn(f",{int(scene.LAYOUT['9:16']['cap_margin'] * 1920)},1", a)


class Sketch(unittest.TestCase):
    def setUp(self):
        self.svg = sketch.render(copy.deepcopy(SKETCH), "eco")

    def test_structure_page_py_drives(self):
        root = ET.fromstring(self.svg)
        ns = "{http://www.w3.org/2000/svg}"
        graph = root.find(f"{ns}g")
        self.assertEqual(graph.get("class"), "graph")
        kinds = [g.get("class") for g in graph.findall(f"{ns}g")]
        self.assertEqual(kinds.count("cluster"), 2)
        self.assertEqual(kinds.count("node"), 5)
        self.assertEqual(kinds.count("edge"), 3)
        for g in graph.findall(f"{ns}g"):
            if g.get("class") in ("node", "cluster"):
                self.assertTrue(g.findall(f"{ns}text"), g.get("class"))   # labels are direct children (pick())
        self.assertEqual(root.get("width"), "100%")

    def test_keys_are_neutral_never_the_authored_ids(self):
        self.assertIn('data-k="n1"', self.svg)
        self.assertIn('data-from="n1" data-to="n2"', self.svg)
        for authored in ("guests", "data-k=\"cat\"", "\"ext\""):
            self.assertNotIn(authored, self.svg)
        for gone in ("<title", "<desc", "<image", "href", "<a "):
            self.assertNotIn(gone, self.svg)

    def test_drawn_text_is_exactly_the_labels(self):
        drawn = re.findall(r"<text[^>]*>([^<]*)</text>", self.svg)
        self.assertEqual(sorted(html.unescape(t) for t in drawn), sorted(sketch.labels(SKETCH)))

    def test_nested_groups_and_nodes_inside_their_frames(self):
        root = ET.fromstring(self.svg)
        ns = "{http://www.w3.org/2000/svg}"
        rects = [g.find(f"{ns}rect") for g in root.iter(f"{ns}g") if g.get("class") == "cluster"]
        (outer, inner) = sorted(rects, key=lambda r: float(r.get("width")), reverse=True)
        f = lambda r, k: float(r.get(k))  # noqa: E731
        self.assertLess(f(outer, "x"), f(inner, "x"))
        self.assertLess(f(outer, "y"), f(inner, "y"))
        self.assertGreater(f(outer, "y") + f(outer, "height"), f(inner, "y") + f(inner, "height"))

    def test_invalid_sketches_are_errors(self):
        bad = copy.deepcopy(SKETCH)
        bad["nodes"][1]["at"] = [0, 0]
        bad["edges"].append({"from": "cat", "to": "nowhere"})
        bad["groups"].append({"id": "x", "label": "Cross", "cells": [1, 0, 2, 1]})
        msg = "; ".join(sketch.validate(bad, "eco"))
        for part in ("share cell", "'nowhere'", "overlap without nesting"):
            self.assertIn(part, msg)
        with self.assertRaises(sketch.SketchError):
            sketch.render(bad, "eco")

    def test_committed_diagram_name_is_refused(self):
        ep = copy.deepcopy(EPISODE)
        ep["diagrams"] = {"eco": "ecosystem"}
        with self.assertRaises(scene.SceneError) as e:
            scene.load(ep)
        self.assertIn("visual fingerprint", str(e.exception))


if __name__ == "__main__":
    unittest.main()
