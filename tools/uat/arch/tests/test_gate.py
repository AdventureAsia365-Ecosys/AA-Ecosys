"""Gate tests (AA-1021): a planted brand word, an account-ID-shaped number and a hostname each FAIL the gate, on every
layer that sees text. Invented names only. Stdlib only:

  python3 -m unittest discover -s tools/uat/arch/tests
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gate  # noqa: E402

DENY = """## brand
Zentrova Travel
Zentrova
cs:ZT
## coined
widget_queue
re:\\bno\\s+key\\b
"""
CLEAN = "A small travel company runs four apps on one managed database, with a role per app."


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "deny.txt").write_text(DENY)
        self.pats = gate.load_patterns(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def l1(self, text):
        return gate.check_texts({"narration": text}, self.pats, None, set(), ngram=False)


class Layer1(Base):
    def test_clean_text_passes(self):
        self.assertEqual(self.l1(CLEAN), [])

    def test_planted_brand_word_fails(self):
        hits = self.l1("Today Zentrova moves its catalogue to the cloud.")
        self.assertTrue(hits)
        self.assertEqual(hits[0].category, "deny:brand")
        self.assertTrue(self.l1("Built at ZENTROVA TRAVEL, in two weeks."))

    def test_brand_across_a_line_break_fails(self):
        self.assertTrue(self.l1("built at Zentrova\nTravel"))

    def test_case_sensitive_short_brand(self):
        self.assertTrue(self.l1("the ZT platform"))
        self.assertEqual(self.l1("zt and ZTX are not the brand"), [])

    def test_account_id_shaped_number_fails(self):
        for text in ("the account 123456789012 holds it", "id 1234-5678-9012", "bucket-123456789012"):
            hits = self.l1(text)
            self.assertTrue(hits, text)
            self.assertTrue(all(h.category == "identifier:account-id" for h in hits), text)
        self.assertEqual(self.l1("a 13-digit 1234567890123 is not an account"), [])

    def test_hostname_fails(self):
        for text in ("open trips.zentrova-demo.travel now", "see api.example.com", "https://x", "mail ops@example.org"):
            self.assertTrue(self.l1(text), text)
        self.assertEqual(self.l1("built with Next.js and Node.js"), [])

    def test_other_identifiers_fail(self):
        for text in ("arn:aws:iam::", "in us-west-2 today", "issue XY-1021", "migration crm-035", "ADR 0018",
                     "session S264", "it costs $40", "about 12 USD a day", "10.0.3.7", "AKIA" + "Q" * 16):
            self.assertTrue(self.l1(text), text)

    def test_regex_and_coined_terms(self):
        self.assertTrue(self.l1("the path has no key yet"))
        self.assertTrue(self.l1("the widget_queue drains"))

    def test_missing_deny_list_refuses(self):
        with self.assertRaises(SystemExit):
            gate.load_patterns(self.tmp / "nowhere")


class NgramLayer(Base):
    def setUp(self):
        super().setUp()
        self.ws = self.tmp / "ws"
        (self.ws / "docs").mkdir(parents=True)
        (self.ws / "docs" / "page.md").write_text(
            "Our nightly sweeper drains the parcel ledger before dawn. Uses ParcelLedgerV2 and parcel_ledger.\n")
        subprocess.run(["git", "init", "-q", str(self.ws)], check=True)
        subprocess.run(["git", "-C", str(self.ws), "add", "."], check=True)

    def test_phrase_from_a_public_repo_fails(self):
        hits = gate.ngram_scan({"s1": "Each night the sweeper drains the parcel ledger before dawn."}, self.ws, set())
        self.assertTrue(any(h.category == "ngram:phrase" for h in hits))

    def test_internal_token_from_a_public_repo_fails(self):
        hits = gate.ngram_scan({"s1": "It writes to parcel_ledger and ParcelLedgerV2."}, self.ws, set())
        self.assertEqual({h.category for h in hits}, {"ngram:token"})

    def test_generic_or_allowed_phrase_passes(self):
        self.assertEqual(gate.ngram_scan({"s1": "It is one of the things we do."}, self.ws, set()), [])
        line = "Each night the sweeper drains the parcel ledger before dawn."
        allow = gate.script_shingles(line, set())
        self.assertTrue(allow)
        self.assertEqual(gate.ngram_scan({"s1": line}, self.ws, allow), [])

    def test_public_labels_together_in_one_file_fail(self):
        (self.ws / "docs" / "plan.md").write_text("Labels: river desk, cabin ledger, deck planner and port gateway.\n")
        subprocess.run(["git", "-C", str(self.ws), "add", "."], check=True)
        labels = ["River desk", "Cabin ledger", "Deck planner", "Port gateway", "Region"]
        hits = gate.label_set_scan(labels, self.ws)
        self.assertEqual([h.where for h in hits], ["docs/plan.md"])
        self.assertEqual(gate.label_set_scan(labels[:3], self.ws), [])

    def test_root_repo_override(self):
        other = self.tmp / "other"
        (other / "docs").mkdir(parents=True)
        (other / "docs" / "x.md").write_text("nothing here\n")
        subprocess.run(["git", "init", "-q", str(other)], check=True)
        subprocess.run(["git", "-C", str(other), "add", "."], check=True)
        line = "Each night the sweeper drains the parcel ledger before dawn."
        os.environ["ARCH_VIDEO_ROOT_REPO"] = str(other)
        try:
            self.assertEqual(gate.ngram_scan({"s1": line}, self.ws, set()), [])
        finally:
            del os.environ["ARCH_VIDEO_ROOT_REPO"]


class Layer2(Base):
    def test_dom_dump_with_brand_in_svg_fails(self):
        dump = {"title": "x", "body": "Catalogue", "svg": ["Zentrova admin"], "attrs": [], "refs": []}
        self.assertTrue(gate.scan_text(gate.dom_dump_texts(dump), "kf-01", self.pats, layer="L2"))

    def test_dom_dump_with_account_id_or_host_in_attribute_fails(self):
        for attr in ("data-k=123456789012", "aria-label=portal.zentrova-demo.com"):
            dump = {"title": "", "body": "", "svg": [], "attrs": [attr], "refs": []}
            self.assertTrue(gate.scan_text(gate.dom_dump_texts(dump), "kf-02", self.pats, layer="L2"), attr)

    def test_inline_image_payload_is_not_text(self):
        dump = {"refs": ["data:image/png;base64,AAAA123456789012BBBB"], "svg": [], "attrs": []}
        self.assertEqual(gate.scan_text(gate.dom_dump_texts(dump), "kf-03", self.pats, layer="L2"), [])

    @unittest.skipIf(shutil.which("node") is None, "node not installed")
    def test_patterns_compile_the_same_in_javascript(self):
        src = json.dumps(gate.patterns_json(self.pats))
        js = ("const p=JSON.parse(process.argv[1]);const t=process.argv[2];let n=0;"
              "for(const x of p){if(new RegExp(x.source,'g'+x.flags).test(t))n++;}console.log(n);")
        for text in ("Zentrova at api.example.com, account 123456789012", CLEAN):
            out = subprocess.run(["node", "-e", js, src, text], capture_output=True, text=True, check=True).stdout
            py = sum(1 for p in self.pats if p.regex.search(text))
            self.assertEqual(int(out.strip()), py, text)


class Layer3(Base):
    def test_ocr_text_with_brand_number_or_host_fails(self):
        frames = {"f1.png": "Catalogue\nZentr0va", "f2.png": "id 123456789012",
                  "f3.png": "go to trips.zentrova-demo.travel", "f4.png": CLEAN}
        hits, status = gate.check_ocr([Path(k) for k in frames], self.pats, gate.literal_terms(self.tmp),
                                      ocr=lambda p: frames[p.name])
        self.assertEqual({h.where for h in hits}, {"f1.png", "f2.png", "f3.png"})
        self.assertIn("ran on 4", status)

    def test_without_tesseract_layer_is_skipped_with_a_warning(self):
        orig = gate.tesseract_cmd
        gate.tesseract_cmd = lambda: None
        try:
            hits, status = gate.check_ocr([Path("f.png")], self.pats, [])
        finally:
            gate.tesseract_cmd = orig
        self.assertEqual(hits, [])
        self.assertTrue(status.startswith("SKIPPED"))

    def test_edit_distance_one(self):
        self.assertTrue(gate.edit1("zentrova", "zentr0va"))
        self.assertTrue(gate.edit1("zentrova", "zentrov"))
        self.assertFalse(gate.edit1("zentrova", "zentr0v4"))


class Layer4(Base):
    def probe(self, tags):
        return lambda p: {"format": {"tags": tags}, "streams": [{"index": 0, "tags": {"handler_name": "VideoHandler"}}],
                          "chapters": [{"id": 0, "tags": {"title": "The problem"}}]}

    def test_brand_in_file_name_fails(self):
        (self.tmp / "out").mkdir()
        (self.tmp / "out" / "zentrova-ep1_master.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n")
        hits = gate.check_artifacts(self.tmp / "out", self.pats)
        self.assertTrue(any(h.where.startswith("name:") for h in hits))

    def test_account_id_or_host_in_captions_fails(self):
        (self.tmp / "out").mkdir()
        (self.tmp / "out" / "ep1_x.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\naccount 123456789012\n")
        (self.tmp / "out" / "ep1_x.description.txt").write_text("More at blog.zentrova-demo.com\n")
        hits = gate.check_artifacts(self.tmp / "out", self.pats)
        self.assertEqual({h.where for h in hits}, {"ep1_x.srt", "ep1_x.description.txt"})

    def test_metadata_tags(self):
        mp4 = self.tmp / "ep1_master.mp4"
        self.assertEqual(gate.metadata_hits(self.probe({"title": "Engineering notes", "encoder": "Lavf60.16.100"})(mp4),
                                            "m", self.pats), [])
        bad = gate.metadata_hits(self.probe({"title": "Zentrova notes", "comment": "x"})(mp4), "m", self.pats)
        self.assertEqual({h.category for h in bad}, {"metadata:tag", "deny:brand"})
        enc = gate.metadata_hits(self.probe({"encoder": "ZT Studio"})(mp4), "m", self.pats)
        self.assertIn("metadata:encoder", {h.category for h in enc})


if __name__ == "__main__":
    unittest.main()
