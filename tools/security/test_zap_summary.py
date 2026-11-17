"""Tests for zap_summary.py (AA-1111). Run: python3 -m unittest discover -s tools/security -p 'test_*.py'.

Offline, stdlib only. testdata/ holds two reports in the shape ZAP 2.17 writes with `zap-baseline.py -J` (the
artifact layout `gh run download` produces: one zap-<id> folder per target), with invented hosts.
"""
from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import zap_summary as z  # noqa: E402

DATA = Path(__file__).resolve().parent / "testdata"


def run(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = z.main([*args])
    return rc, out.getvalue(), err.getvalue()


class Load(unittest.TestCase):
    def test_targets_from_artifact_folders(self):
        reports, versions, errors = z.load(DATA)
        self.assertEqual(sorted(reports), ["demo-api-health", "demo-web"])
        self.assertEqual(versions, {"demo-api-health": "2.17.0", "demo-web": "2.17.0"})
        self.assertEqual(errors, [])

    def test_alerts_flattened_over_sites(self):
        reports, _, _ = z.load(DATA)
        web = reports["demo-web"]
        self.assertEqual(len(web), 5)   # four on the scanned host, one on a third-party script host
        csp = next(a for a in web if a["plugin"] == "10038")
        self.assertEqual((csp["risk"], csp["confidence"], csp["cwe"], csp["count"]), ("Medium", "High", "693", 4))
        self.assertEqual(csp["site"], "https://admin.example.test")
        self.assertEqual({a["site"] for a in web}, {"https://admin.example.test", "https://cdn.example.test"})

    def test_report_at_top_level_and_other_json_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(DATA / "zap-demo-web" / "report_json.json", Path(tmp, "web.json"))
            Path(tmp, "other.json").write_text(json.dumps({"not": "zap"}), encoding="utf-8")
            reports, _, errors = z.load(Path(tmp))
        self.assertEqual(list(reports), ["web"])
        self.assertEqual(errors, [])


class Render(unittest.TestCase):
    def test_counts_per_target(self):
        rc, out, err = run(str(DATA))
        self.assertEqual((rc, err), (0, ""))
        self.assertIn("2 target(s), ZAP 2.17.0", out)
        self.assertIn("| demo-api-health | 0 | 1 | 1 | 0 |", out)
        self.assertIn("| demo-web | 0 | 2 | 2 | 1 |", out)

    def test_same_alert_across_targets_first_in_its_risk(self):
        _, out, _ = run(str(DATA))
        section = out.split("## Alerts across targets", 1)[1].split("\n## ", 1)[0]
        rows = [line for line in section.splitlines() if line.startswith("| Medium")]
        self.assertEqual(rows[0], "| Medium | Content Security Policy (CSP) Header Not Set | 10038 "
                                  "| demo-api-health, demo-web | 5 |")

    def test_per_target_rows_examples_and_escaping(self):
        _, out, _ = run(str(DATA), "--examples", "2")
        web = out.split("## demo-web", 1)[1]
        self.assertIn("| Medium | High | Content Security Policy (CSP) Header Not Set | 10038 | 693 | 4 "
                      "| https://admin.example.test | https://admin.example.test/<br>https://admin.example.test/login"
                      " (+2) |", web)
        self.assertIn("https://cdn.example.test/lib\\|v2.js", web)   # a pipe in a URI does not split the row
        self.assertLess(web.index("| Medium"), web.index("| Low"))
        self.assertLess(web.index("| Low"), web.index("| Informational"))

    def test_min_risk_filters_rows_and_counts(self):
        _, out, _ = run(str(DATA), "--min-risk", "medium")
        self.assertIn("risks shown: Medium and above", out)
        self.assertIn("| demo-web | 0 | 2 | - | - |", out)
        self.assertNotIn("Strict-Transport-Security", out)
        self.assertNotIn("\n| Low |", out)   # no Low row (the count header still names the column)


class Errors(unittest.TestCase):
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, out, err = run(tmp)
        self.assertEqual((rc, out), (2, ""))
        self.assertIn("no ZAP JSON report found", err)

    def test_missing_directory(self):
        rc, _, err = run("/nonexistent/zap-reports")
        self.assertEqual(rc, 2)
        self.assertIn("not a directory", err)

    def test_broken_file_reported_rest_still_summarised(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(DATA / "zap-demo-web", Path(tmp, "zap-demo-web"))
            Path(tmp, "zap-broken").mkdir()
            Path(tmp, "zap-broken", "report_json.json").write_text("{truncated", encoding="utf-8")
            rc, out, err = run(tmp)
        self.assertEqual(rc, 2)
        self.assertIn("unreadable:", err)
        self.assertIn("| demo-web | 0 | 2 | 2 | 1 |", out)

    def test_cell_strips_line_breaks(self):
        self.assertEqual(z.cell("a\n b | c"), "a b \\| c")


if __name__ == "__main__":
    unittest.main()
