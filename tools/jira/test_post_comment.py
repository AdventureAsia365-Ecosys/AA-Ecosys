"""Run: python3 -m unittest discover -s tools/jira -p 'test_*.py' (from the repo root).

tools/jira/post_comment.py without the network: the token file may hold a blank line between the e-mail and the
token (S297), the token never reaches stdout, a dry run calls only GET /myself, images are appended in order.
Invented values only.
"""
from __future__ import annotations

import base64
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import post_comment as pc  # noqa: E402

FAKE_TOKEN = "TESTTOKEN-not-a-real-value-123456"


class TokenFileTest(unittest.TestCase):
    def _file(self, text: str) -> Path:
        d = tempfile.mkdtemp()
        p = Path(d) / "jira-token"
        p.write_text(text)
        return p

    def test_blank_lines_are_skipped(self):
        header = pc.auth_header(self._file(f"someone@example.invalid\n\n{FAKE_TOKEN}\n"))
        decoded = base64.b64decode(header.split(" ", 1)[1]).decode()
        self.assertEqual(decoded, f"someone@example.invalid:{FAKE_TOKEN}")

    def test_a_file_with_one_line_is_refused(self):
        with self.assertRaises(SystemExit):
            pc.auth_header(self._file("someone@example.invalid\n"))


class DryRunTest(unittest.TestCase):
    def test_dry_run_reads_myself_only_and_never_prints_the_token(self):
        d = Path(tempfile.mkdtemp())
        token = d / "jira-token"
        token.write_text(f"someone@example.invalid\n{FAKE_TOKEN}\n")
        body = d / "body.txt"
        body.write_text("hello")
        img = d / "shot.png"
        img.write_bytes(b"\x89PNG")
        calls = []

        def fake_call(auth, method, path, data=None, headers=None):
            calls.append((method, path))
            return 200, {"displayName": "Test Person"}

        out = io.StringIO()
        with mock.patch.object(pc, "call", fake_call), contextlib.redirect_stdout(out):
            rc = pc.main(["--issue", "PR-1", "--body-file", str(body), "--image", str(img), "--token-file", str(token)])
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [("GET", "/rest/api/2/myself")])
        self.assertNotIn(FAKE_TOKEN, out.getvalue())
        self.assertIn("would attach 1 image(s)", out.getvalue())

    def test_post_appends_images_in_order(self):
        d = Path(tempfile.mkdtemp())
        token = d / "jira-token"
        token.write_text(f"someone@example.invalid\n{FAKE_TOKEN}\n")
        body = d / "body.txt"
        body.write_text("hello")
        imgs = []
        for name in ("b.png", "a.png"):
            (d / name).write_bytes(b"\x89PNG")
            imgs += ["--image", str(d / name)]
        sent = {}

        def fake_call(auth, method, path, data=None, headers=None):
            if path.endswith("/comment"):
                sent["body"] = data.decode()
                return 201, {"id": "1", "author": {"displayName": "Test Person"}}
            return 200, {"displayName": "Test Person"}

        with mock.patch.object(pc, "call", fake_call), contextlib.redirect_stdout(io.StringIO()):
            rc = pc.main(["--issue", "PR-1", "--body-file", str(body), *imgs, "--token-file", str(token), "--post"])
        self.assertEqual(rc, 0)
        self.assertLess(sent["body"].index("!b.png|width=900!"), sent["body"].index("!a.png|width=900!"))


if __name__ == "__main__":
    unittest.main()
