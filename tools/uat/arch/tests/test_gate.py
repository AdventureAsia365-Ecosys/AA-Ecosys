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

# S272: a git hook (pre-push) exports GIT_DIR and friends; a git command run in a temporary repo below would then act
# on the real repo (a hook-run test once set core.bare, a fake identity and refs in an app clone). Drop git's
# repo-local variables for this whole test process (the list is `git rev-parse --local-env-vars`; test_git_env_isolation).
for _git_var in ("GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG", "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT",
                 "GIT_OBJECT_DIRECTORY", "GIT_DIR", "GIT_WORK_TREE", "GIT_IMPLICIT_WORK_TREE", "GIT_GRAFT_FILE",
                 "GIT_INDEX_FILE", "GIT_NO_REPLACE_OBJECTS", "GIT_REPLACE_REF_BASE", "GIT_PREFIX", "GIT_SHALLOW_FILE",
                 "GIT_COMMON_DIR"):
    os.environ.pop(_git_var, None)

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


class HyphenAndIdentity(Base):
    """Hyphenated coined names, the series identity and drawn diagram labels (review findings of the S264 pilot)."""

    def setUp(self):
        super().setUp()
        self.ws = self.tmp / "ws"
        (self.ws / "src").mkdir(parents=True)
        (self.ws / "src" / "notes.md").write_text(
            "We run xx-thing2 and orbit-core-v3 nightly; see crate.parcel_log and the Harbour digest series.\n"
            "Read-only replicas are event-driven.\n")
        (self.ws / "src" / "plan.md").write_text("Amazon Aurora, Amazon SQS, AWS Lambda and Amazon S3 Glacier.\n")
        subprocess.run(["git", "init", "-q", str(self.ws)], check=True)
        subprocess.run(["git", "-C", str(self.ws), "add", "."], check=True)

    def test_hyphenated_tokens_are_internal_looking(self):
        for tok in ("xx-thing2", "orbit-core", "Orbit-Core", "aa-bb", "geo-v2's"):
            self.assertTrue(gate.internal_looking(tok), tok)
        for tok in ("read-only", "event-driven", "Multi-tenant", "well-known"):
            self.assertFalse(gate.internal_looking(tok), tok)
        self.assertFalse(gate.internal_looking("orbit-core", {"orbit-core"}))

    def test_hyphenated_token_found_in_a_public_repo_fails(self):
        hits = gate.ngram_scan({"s1": "Our xx-thing2 is fast and orbit-core keeps up."}, self.ws, set())
        self.assertEqual(sorted(h.match.split()[0] for h in hits), ["orbit-core", "xx-thing2"])
        self.assertEqual({h.category for h in hits}, {"ngram:token"})

    def test_prefix_of_a_public_identifier_fails(self):
        hits = gate.ngram_scan({"s1": "Rows land in crate.parcel and then drain."}, self.ws, set())
        self.assertEqual([h.category for h in hits], ["ngram:token"])

    def test_ordinary_compounds_pass(self):
        self.assertEqual(gate.ngram_scan({"s1": "Our read-only copies stay event-driven."}, self.ws, set()), [])

    def test_series_identity_found_anywhere_fails(self):
        hits = gate.identity_scan({"series_tag": gate.strip_episode_marker("Harbour digest · Ep 2")}, self.ws)
        self.assertEqual([h.category for h in hits], ["ngram:identity"])
        self.assertEqual(gate.identity_scan({"series": "Lantern letters"}, self.ws), [])
        self.assertEqual(gate.strip_episode_marker("Harbour digest · Episode 12"), "Harbour digest")

    def test_cloud_product_names_do_not_count_in_the_label_set(self):
        cloud = ["Amazon Aurora", "Amazon SQS", "AWS Lambda", "Amazon S3 Glacier", "Partner desk"]
        self.assertEqual(gate.label_set_scan(cloud, self.ws), [])
        self.assertEqual(gate.label_set_candidates(cloud), ["partner desk"])

    def test_coined_label_drawn_in_a_sketch_fails_layer1(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import make_episode  # noqa: E402
        import scene  # noqa: E402

        sk = {"nodes": [{"id": "a", "label": "Catalogue", "sub": "crate.parcel_log", "at": [0, 0]},
                        {"id": "b", "label": "Workers", "sub": "orbit-core", "at": [1, 0]}],
              "edges": [{"from": "a", "to": "b"}]}
        ep = {"slug": "ep9-test", "title": "A calm title", "series": "Lantern letters", "series_tag": "Lantern · Ep 9",
              "cuts": {"master": {"aspect": "16:9"}}, "diagrams": {"d": sk},
              "scenes": [{"id": "s1", "visual": {"type": "diagram", "diagram": "d"}, "sentences": ["Hello there."]}]}
        meta, sents = scene.load(ep)
        hits, texts, svgs, n = make_episode.layer1(ep, meta, sents, None, self.pats, self.ws, set())
        self.assertEqual(n, 4)
        self.assertIn("d", svgs)
        drawn = {h.match.split()[0] for h in hits if h.where.startswith("diagram:d:")}
        self.assertEqual(drawn, {"crate.parcel_log", "orbit-core"})
        sk["nodes"][0]["sub"], sk["nodes"][1]["sub"] = "api", "workers"
        meta, sents = scene.load(ep)
        self.assertEqual(make_episode.layer1(ep, meta, sents, None, self.pats, self.ws, set())[0], [])
        ep["series_tag"] = "Harbour digest · Ep 9"
        meta, sents = scene.load(ep)
        hits = make_episode.layer1(ep, meta, sents, None, self.pats, self.ws, set())[0]
        self.assertEqual([h.category for h in hits], ["ngram:identity"])


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

    def test_tsv_drops_line_noise_but_keeps_text(self):
        head = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"
        rows = ["5\t1\t1\t1\t1\t1\t10\t10\t60\t14\t95\tZentrova",
                "5\t1\t1\t1\t1\t2\t80\t10\t40\t14\t93\tadmin",
                "5\t1\t2\t1\t1\t1\t10\t300\t13\t2\t18\t\u00a36",
                "5\t1\t2\t1\t1\t2\t30\t300\t70\t2\t20\teee",
                "4\t1\t3\t1\t1\t0\t0\t0\t9\t9\t-1\t"]
        text = gate.tsv_text("\n".join([head] + rows))
        self.assertEqual(text, "Zentrova admin")
        self.assertTrue(gate.scan_text(text, "f", self.pats, layer="L3"))
        self.assertEqual(gate.scan_text(text.replace("Zentrova ", ""), "f", self.pats, layer="L3"), [])

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
        self.assertEqual(gate.metadata_hits(self.probe({"title": "River notes", "encoder": "Lavf60.16.100"})(mp4),
                                            "m", self.pats), [])
        bad = gate.metadata_hits(self.probe({"title": "Zentrova notes", "comment": "x"})(mp4), "m", self.pats)
        self.assertEqual({h.category for h in bad}, {"metadata:tag", "deny:brand"})
        enc = gate.metadata_hits(self.probe({"encoder": "ZT Studio"})(mp4), "m", self.pats)
        self.assertIn("metadata:encoder", {h.category for h in enc})


if __name__ == "__main__":
    unittest.main()
