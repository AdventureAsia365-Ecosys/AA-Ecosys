"""Scene, timeline, caption and label-profile tests (AA-1021). Invented content only. Stdlib only:

  python3 -m unittest discover -s tools/uat/arch/tests
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import labels  # noqa: E402
import scene  # noqa: E402

EPISODE = {
    "slug": "ep1-example", "title": "Four apps, one picture", "series": "Engineering notes", "episode": 1,
    "diagrams": {"eco": "ecosystem"},
    "description": "How an invented company splits its platform.", "hashtags": ["#aws", "#architecture"],
    "cuts": {"master": {"aspect": "16:9", "chapters": True, "max_s": 200},
             "short": {"aspect": "9:16", "max_s": 60}},
    "scenes": [
        {"id": "s1", "chapter": "The problem", "cuts": ["master", "short"],
         "visual": {"type": "title", "kicker": "Episode 1", "title": "Four apps, one picture"},
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
        self.assertNotIn("s2.1:visual.reveal", texts)   # labels are checked through the profile instead


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


SVG = """<?xml version="1.0"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "x">
<svg width="200pt" height="100pt" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg"
 xmlns:xlink="http://www.w3.org/1999/xlink"><!-- secret comment -->
<g id="graph0" class="graph"><title>Orbit platform</title><text>Orbit platform: ecosystem architecture (Dev)</text>
<g id="clust1" class="cluster"><title>cluster_1 orbit Orbit-Trips</title><text>Orbit-Trips</text></g>
<g id="node1" class="node"><title>s1</title><a xlink:href="https://x.example.com" xlink:title="t">
<text>OrbitTrips web</text></a></g>
<g id="node3" class="node"><title>s7</title><image xlink:href="data:image/png;base64,AAAA"
 width="20px" height="20px" x="5" y="6"/></g>
<g id="node4" class="node"><title>s7&#45;t</title><text>Hosting box</text></g>
<g id="node2" class="node"><title>orbit_api</title><text>VendorOne · VendorTwo (no key)</text></g>
<g id="edge1" class="edge"><title>s1&#45;&gt;s2</title><text>calls</text></g>
</g></svg>"""
PROFILE = {"map": {"Orbit-Trips": "Route app", "Orbit platform: ecosystem architecture (Dev)": None,
                   "VendorOne · VendorTwo (no key)": "model vendor APIs"},
           "replace": [["Orbit-?Trips", "Route app"]], "drop_titles": True, "neutral_icons": ["Hosting box"]}


class LabelProfile(unittest.TestCase):
    def setUp(self):
        self.out = labels.anonymize_svg(SVG, labels.prepare(PROFILE))

    def test_texts_are_mapped_dropped_or_rewritten(self):
        self.assertIn(">Route app<", self.out)
        self.assertIn(">Route app web<", self.out)
        self.assertIn(">model vendor APIs<", self.out)
        self.assertNotIn("Orbit", self.out)
        self.assertNotIn("VendorOne", self.out)

    def test_titles_comments_links_and_doctype_are_gone(self):
        for gone in ("<title", "secret comment", "DOCTYPE", "example.com", "orbit_api"):
            self.assertNotIn(gone, self.out)

    def test_vendor_icon_becomes_a_plain_shape(self):
        self.assertNotIn("<image", self.out)
        self.assertIn('rx="6"', self.out)
        self.assertIn('x="5"', self.out)

    def test_neutral_keys_kept_for_reveal(self):
        self.assertIn('data-k="s1"', self.out)
        self.assertIn('data-from="s1"', self.out)
        self.assertIn('data-to="s2"', self.out)
        self.assertNotIn('data-k="orbit_api"', self.out)
        self.assertIn('width="100%"', self.out)


if __name__ == "__main__":
    unittest.main()
