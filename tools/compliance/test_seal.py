"""AA-1173 — unit tests of tools/compliance/seal.py (the root copy) and of the seal steps of compliance-evidence.yml.

seal.py is the SAME file as AA-CIS-Infra tools/compliance/seal.py; SEAL_SHA256 pins it here and in the Infra tests
(tools/compliance/tests/test_seal.py), updated in both PRs together. No network: a fake AWS CLI runner.
Run: python3 -m unittest discover -s tools/compliance -p 'test_*.py'"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import seal  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SEAL_SHA256 = "bf1087c7b9b6126f6d15716e0a48499948b5baa59bdff87abe126189e6302e27"
NOW = datetime(2026, 3, 4, 5, 6, 7, tzinfo=timezone.utc)


class FakeAws:
    def __init__(self, existing=None, previous=b'{"format": 1}\n'):
        self.calls = []
        self.existing = existing or []
        self.previous = previous
        self.bodies = {}

    def __call__(self, args):
        self.calls.append(args)
        if args[1] == "put-object":
            self.bodies[args[args.index("--key") + 1]] = Path(args[args.index("--body") + 1]).read_bytes()
            return "{}"
        if args[1] == "list-objects-v2":
            return json.dumps({"Contents": [{"Key": k} for k in self.existing]})
        if args[1] == "get-object":
            Path(args[-1]).write_bytes(self.previous)
            return "{}"
        raise AssertionError(args)


class SealTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bundle = Path(self.tmp.name) / "evidence.json"
        self.bundle.write_text(json.dumps({"format": 1, "source": "root_daily", "checks": []}), encoding="utf-8")

    def test_same_file_as_the_infra_copy(self):
        self.assertEqual(hashlib.sha256((ROOT / "tools/compliance/seal.py").read_bytes()).hexdigest(), SEAL_SHA256)

    def test_bundle_then_manifest_each_written_once_and_chained(self):
        prev = b'{"format": 1, "source": "root_daily"}\n'
        newer = "evidence/root_daily/manifest/2026/03/03/024100Z-7-1.json"
        aws = FakeAws(existing=["evidence/root_daily/manifest/2026/03/02/024100Z-6-1.json", newer], previous=prev)
        out = seal.seal("bkt", "root_daily", self.bundle, [], "8-1", "compliance-evidence #8", "abcdef1", NOW, run=aws)
        self.assertEqual(out["chain"], "linked")
        puts = [c for c in aws.calls if c[1] == "put-object"]
        self.assertEqual([c[c.index("--key") + 1] for c in puts], [
            "evidence/root_daily/bundles/2026/03/04/050607Z-8-1.json",
            "evidence/root_daily/manifest/2026/03/04/050607Z-8-1.json"])
        for c in puts:
            self.assertEqual(c[c.index("--if-none-match") + 1], "*")
        manifest = json.loads(aws.bodies["evidence/root_daily/manifest/2026/03/04/050607Z-8-1.json"])
        self.assertEqual(manifest["previous"], {"key": newer, "sha256": hashlib.sha256(prev).hexdigest()})
        self.assertEqual(manifest["objects"][0]["sha256"], hashlib.sha256(self.bundle.read_bytes()).hexdigest())

    def test_a_bundle_of_another_source_is_refused(self):
        with self.assertRaises(ValueError):
            seal.seal("bkt", "aws_nightly", self.bundle, [], "1-1", "r", None, NOW, run=FakeAws())


class SealWorkflowTest(unittest.TestCase):
    """The root workflow seals with the compliance evidence role before the docs-reader copy, and checks the role."""

    def test_seal_steps(self):
        text = (ROOT / ".github/workflows/compliance-evidence.yml").read_text(encoding="utf-8")
        wf = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
        self.assertIn("secrets.COMPLIANCE_EVIDENCE_ROLE_ARN", wf)
        self.assertIn("secrets.COMPLIANCE_EVIDENCE_BUCKET", wf)
        self.assertNotIn("vars.COMPLIANCE", wf)
        self.assertIn("--source root_daily", wf)
        self.assertIn("*:assumed-role/aa-cis-*-compliance-evidence/*", wf)
        self.assertLess(wf.index("tools/compliance/seal.py"), wf.index("secrets.DOCS_SYNC_ROLE_ARN }}\n"))
        self.assertEqual(len(re.findall(r"mask-aws-account-id: true", wf)), 1)

    def test_a_failed_seal_never_blocks_the_docs_reader_upload(self):
        # S290 review: the seal runs before the phase 1 upload, so each seal step is continue-on-error and a last
        # step (after the upload) fails the run when the seal did not succeed.
        text = (ROOT / ".github/workflows/compliance-evidence.yml").read_text(encoding="utf-8")
        steps = re.split(r"\n      - (?=name:|uses:)", text.split("\n    steps:\n", 2)[2])
        by_name = {re.match(r"name: (.*)", s).group(1): s for s in steps if s.startswith("name:")}
        for name in ("AWS credentials (OIDC, compliance evidence role)", "Verify the role",
                     "Seal into the evidence bucket (write-once, hash chain)"):
            self.assertIn("continue-on-error: true", by_name[name], name)
        names = list(by_name)
        outcome = next(n for n in names if n.startswith("Seal outcome"))
        self.assertGreater(names.index(outcome), names.index("Upload the day file, then the latest file"))
        self.assertIn("!cancelled()", by_name[outcome])
        self.assertIn("steps.seal.outcome", by_name[outcome])
        self.assertIn("exit 1", by_name[outcome])


if __name__ == "__main__":
    unittest.main()
