"""Tests for linear_export.py: the gitleaks gate on the files just written and the secret-label rewrite (S276,
AA-1024). Offline: no Linear call; gitleaks is a stub unless GITLEAKS_BIN / PATH has the real one (then one extra test
runs it). Run: python3 -m unittest discover -s tools/linear -p 'test_*.py'
"""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import linear_export as le  # noqa: E402

# Invented names only (no secret name copied from the real register). The label and its colon are joined at run
# time: written out in this file they are exactly what the CI secret scan flags (generic-api-key).
SECRETS_COLON = "Secret" + "s:"
S276_SHAPE = f"- {SECRETS_COLON} `orbitquill/dev/zephyr` written (Sentry on)."

STUB = textwrap.dedent("""\
    #!{python}
    import json, os, sys
    a = sys.argv[1:]
    tree = a[1]
    report = a[a.index("--report-path") + 1]
    first = ""
    for d, _, files in os.walk(tree):
        for f in sorted(files):
            first = first or os.path.join(d, f)
    found = [{{"RuleID": "generic-api-key", "File": first, "StartLine": 7, "Secret": "REDACTED"}}]
    mode = os.environ.get("STUB_MODE", "clean")
    if mode == "crash":
        print("boom", file=sys.stderr)
        sys.exit(7)
    with open(report, "w") as fh:
        json.dump(found if mode == "leak" else [], fh)
    with open(os.environ["STUB_ARGS"], "w") as fh:
        json.dump(a, fh)
    sys.exit(1 if mode == "leak" else 0)
""")


def issue(ident: str = "AA-9001", comment: str = "Shipped the lantern filter.", desc: str = "Lantern filter.") -> dict:
    return {
        "id": "uuid-" + ident, "identifier": ident, "title": "Lantern filter chips", "description": desc,
        "url": f"https://linear.app/x/issue/{ident}", "priority": 2, "createdAt": "2026-11-01T10:00:00.000Z",
        "updatedAt": "2026-11-02T10:00:00.000Z", "startedAt": None, "completedAt": "2026-11-02T10:00:00.000Z",
        "canceledAt": None, "archivedAt": None, "trashed": False, "state": {"name": "Done", "type": "completed"},
        "team": {"key": "AA"}, "project": {"name": "Lantern Works"}, "parent": None, "children": {"nodes": []},
        "labels": {"nodes": []}, "assignee": None, "creator": {"name": "Robin"}, "attachments": {"nodes": []},
        "comments": {"nodes": [{"body": comment, "createdAt": "2026-11-02T09:00:00.000Z", "user": {"name": "Robin"}}]},
    }


class SecretLabelTest(unittest.TestCase):
    def test_colon_after_a_secret_label_before_a_backticked_name_is_dropped(self):
        self.assertEqual(le.neutralise_secret_labels(S276_SHAPE),
                         "- Secrets — `orbitquill/dev/zephyr` written (Sentry on).")
        self.assertEqual(le.neutralise_secret_labels("**Secrets:** `orbitquill/dev/a`, `orbitquill/dev/b` rotated"),
                         "**Secrets** — `orbitquill/dev/a`, `orbitquill/dev/b` rotated")
        manager = "Secrets Manager" + ":"
        self.assertEqual(le.neutralise_secret_labels(f"* {manager} `orbitquill/dev/zephyr` stored"),
                         "* Secrets Manager — `orbitquill/dev/zephyr` stored")
        self.assertEqual(le.neutralise_secret_labels("secret:`lanternkey`"), "secret — `lanternkey`")
        two = le.neutralise_secret_labels("Secret: `a-b-c` and later Secrets: `d-e-f`")
        self.assertEqual(two, "Secret — `a-b-c` and later Secrets — `d-e-f`")

    def test_other_text_is_left_as_written(self):
        for text in ("Secrets rotated on 02/11.", "Secret named orbitquill/dev/zephyr written.",
                     "secret_key: `x`", "Secretary: `Robin`", "The key: `lantern`", "Secrets:\n\n`code block`",
                     "**Wrong `X-Lantern-Secret`:** 403", "_(no description)_"):
            self.assertEqual(le.neutralise_secret_labels(text), text, text)

    def test_render_rewrites_comments_and_description(self):
        out = le.render(issue(comment=S276_SHAPE, desc=f"{SECRETS_COLON} `orbitquill/dev/desc` created"))
        self.assertIn("- Secrets — `orbitquill/dev/zephyr` written", out)
        self.assertIn("Secrets — `orbitquill/dev/desc` created", out)
        self.assertNotIn(SECRETS_COLON + " `", out)


class GateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="le-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.out = self.tmp / "docs" / "linear-export"
        (self.out / "lantern-works").mkdir(parents=True)
        self.file = self.out / "lantern-works" / "AA-9001.md"
        self.file.write_text("# AA-9001\n", encoding="utf-8")
        self.stub = self.tmp / "gitleaks-stub"
        self.stub.write_text(STUB.format(python=sys.executable), encoding="utf-8")
        self.stub.chmod(0o755)
        self.args_file = self.tmp / "args.json"
        for p in (mock.patch.object(le, "OUT", self.out), mock.patch.object(le, "ROOT", self.tmp)):
            p.start()
            self.addCleanup(p.stop)

    def gate(self, mode: str | None, skip: bool = False, binary: str | None = None, paths=None):
        env = {"STUB_MODE": mode or "clean", "STUB_ARGS": str(self.args_file), "PATH": str(self.tmp / "empty")}
        env["GITLEAKS_BIN"] = str(self.stub) if binary is None else binary
        err, out = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, env), contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
            rc = le.gitleaks_gate([self.file] if paths is None else paths, skip)
        return rc, out.getvalue(), err.getvalue()

    def test_clean_files_pass_and_the_root_config_is_used(self):
        rc, out, _ = self.gate("clean")
        self.assertEqual(rc, 0)
        self.assertIn("1 exported file(s) clean", out)
        args = __import__("json").loads(self.args_file.read_text())
        self.assertEqual(args[0], "dir")
        self.assertEqual(args[args.index("--config") + 1], str(le.GITLEAKS_CONFIG))
        self.assertIn("--redact", args)
        self.assertTrue(args[1].endswith("tree"))  # a copy of only the files just written, not the whole export

    def test_a_finding_stops_with_file_line_and_rule(self):
        rc, _, err = self.gate("leak")
        self.assertEqual(rc, le.EXIT_LEAKS)
        self.assertIn("docs/linear-export/lantern-works/AA-9001.md:7  generic-api-key", err)
        self.assertIn("Nothing was archived", err)
        self.assertNotIn("REDACTED", err)

    def test_gitleaks_failure_stops(self):
        rc, _, err = self.gate("crash")
        self.assertEqual(rc, le.EXIT_LEAKS)
        self.assertIn("gitleaks exited 7", err)

    def test_missing_gitleaks_stops_loudly_unless_skipped(self):
        rc, _, err = self.gate("clean", binary=str(self.tmp / "no-such-gitleaks"))
        self.assertEqual(rc, le.EXIT_NO_GITLEAKS)
        self.assertIn("gitleaks not found", err)
        self.assertIn("--no-gitleaks", err)
        rc, _, err = self.gate("clean", binary="")  # unset: PATH has none
        self.assertEqual(rc, le.EXIT_NO_GITLEAKS)
        rc, _, err = self.gate("clean", skip=True, binary="")
        self.assertEqual(rc, 0)
        self.assertIn("NOT scanned", err)

    def test_nothing_written_needs_no_scan(self):
        rc, _, _ = self.gate("leak", binary="", paths=[])
        self.assertEqual(rc, 0)


class MainTest(unittest.TestCase):
    """main(): the gate runs after the files are written and before the summary and any archive call."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="le-main-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.out = self.tmp / "docs" / "linear-export"
        self.out.mkdir(parents=True)
        for p in (mock.patch.object(le, "OUT", self.out), mock.patch.object(le, "ROOT", self.tmp),
                  mock.patch.object(le, "api_key", return_value="k"),
                  mock.patch.object(le, "fetch", return_value=[issue(comment=S276_SHAPE)])):
            p.start()
            self.addCleanup(p.stop)

    def run_main(self, argv, gate_rc):
        gql = mock.MagicMock(return_value={"issueArchive": {"success": True}})
        with mock.patch.object(le, "gql", gql), mock.patch.object(le, "gitleaks_gate", return_value=gate_rc) as g, \
                contextlib.redirect_stdout(io.StringIO()) as out:
            rc = le.main(argv)
        return rc, gql, g, out.getvalue()

    def test_a_red_gate_stops_before_the_summary_and_the_archive(self):
        rc, gql, gate, out = self.run_main(["--archive", "--apply"], le.EXIT_LEAKS)
        self.assertEqual(rc, le.EXIT_LEAKS)
        gql.assert_not_called()
        self.assertNotIn("closed issues:", out)
        written = gate.call_args.args[0]
        self.assertEqual(sorted(p.name for p in written), ["AA-9001.md", "README.md"])
        self.assertIn("Secrets — `orbitquill/dev/zephyr`", (self.out / "lantern-works" / "AA-9001.md").read_text())

    def test_a_green_gate_archives(self):
        rc, gql, _, out = self.run_main(["--archive", "--apply"], 0)
        self.assertEqual(rc, 0)
        self.assertIn("closed issues: 1 | files written/updated: 1", out)
        gql.assert_called_once()

    def test_unchanged_files_are_not_rescanned(self):
        self.run_main([], 0)
        _, _, gate, _ = self.run_main(["--only", "AA-9001"], 0)
        self.assertEqual(gate.call_args.args[0], [])
        self.assertFalse(gate.call_args.args[1])


REAL = os.environ.get("GITLEAKS_BIN") or shutil.which("gitleaks")


@unittest.skipUnless(REAL, "gitleaks not installed (set GITLEAKS_BIN to run against the real binary)")
class RealGitleaksTest(unittest.TestCase):
    """With the real gitleaks v8.30.1 and the root config: the S276 shape fires, the rendered export does not."""

    def scan(self, text: str) -> list[dict]:
        tmp = Path(tempfile.mkdtemp(prefix="le-real-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        out = tmp / "linear-export"
        (out / "p").mkdir(parents=True)
        f = out / "p" / "AA-9001.md"
        f.write_text(text, encoding="utf-8")
        with mock.patch.object(le, "OUT", out):
            return le.scan_files([f], REAL)

    def test_s276_shape_fires_and_the_rewrite_clears_it(self):
        self.assertEqual([x["rule"] for x in self.scan(S276_SHAPE + "\n")], ["generic-api-key"])
        self.assertEqual([x["line"] for x in self.scan("a\n" + S276_SHAPE + "\n")], [2])
        self.assertEqual(self.scan(le.render(issue(comment=S276_SHAPE))), [])
        # stripping the backticks alone does not help: the colon is what the rule reads as an assignment
        self.assertEqual(len(self.scan(S276_SHAPE.replace("`", "") + "\n")), 1)


if __name__ == "__main__":
    unittest.main()
