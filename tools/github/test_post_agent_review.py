"""Tests for post_agent_review.py (AA-1162). Offline: every gh call is scripted, nothing reaches GitHub.

Run: python -m unittest discover -s tools/github -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import post_agent_review as par
from ship_common import Result, ShipError
from ship_fakes import FakeRunner

HEAD = "b" * 40
SLUG = "AdventureAsia365-Ecosys/AA-Booking"
REVIEWS_URL = f"repos/{SLUG}/pulls/12/reviews?per_page=100"
TOKEN_ENV = {"GH_TOKEN": "placeholder-not-a-token"}


def js(obj) -> Result:
    return Result(0, json.dumps(obj))


def rv(verdict: str = "approve", *findings: dict, lens: str | None = None) -> dict:
    out = {"verdict": verdict, "findings": list(findings)}
    if lens:
        out["lens"] = lens
    return out


def finding(severity: str, issue: str = "an invented problem", file: str = "api/x.py", line: int | None = 3) -> dict:
    f = {"severity": severity, "file": file, "issue": issue, "fix": "an invented fix"}
    if line:
        f["line"] = line
    return f


class RecordingRunner(FakeRunner):
    """FakeRunner that also keeps the stdin payload of each call."""

    def __init__(self) -> None:
        super().__init__()
        self.inputs: list[tuple[list[str], str | None]] = []

    def run(self, argv, timeout=None, input_text=None) -> Result:
        self.inputs.append((list(argv), input_text))
        return super().run(argv, timeout=timeout, input_text=input_text)


def gh(state: str = "OPEN", existing: list[dict] | None = None) -> RecordingRunner:
    r = RecordingRunner()
    r.on(("gh", "pr", "view"), js({"state": state, "headRefOid": HEAD}))
    # `--jq '... | @json'` prints each review as one line of JSON text.
    lines = "\n".join(json.dumps(x) for x in (existing or []))
    r.on((REVIEWS_URL,), Result(0, lines + "\n"))
    r.on(("-X", "POST"), js({"id": 501}))
    r.on(("-X", "PUT"), js({"id": 77}))
    return r


class VerdictTest(unittest.TestCase):
    def test_mapping(self):
        self.assertEqual(par.verdict_of([rv(), rv("approve", finding("minor"))]), "approve")
        self.assertEqual(par.verdict_of([rv(), rv("changes")]), "request changes")
        self.assertEqual(par.verdict_of([rv("approve", finding("major"))]), "request changes")
        self.assertEqual(par.verdict_of([rv("approve", finding("major")), rv("changes", finding("blocking"))]),
                         "blocking")


class BodyTest(unittest.TestCase):
    def test_first_line_lenses_counts_run_and_marker(self):
        body = par.build_body([rv("approve", finding("minor")), rv("changes", finding("major"), finding("blocking"))],
                              head=HEAD, lenses=["correctness", "security"], run_id="wf_abc-123", lane="l9-demo")
        lines = body.splitlines()
        self.assertEqual(lines[0], "Agent review: blocking")
        self.assertIn("Lenses: correctness; security", body)
        self.assertIn("Findings: 1 blocking, 1 major, 1 minor", body)
        self.assertIn("Reviewer run: wf_abc-123 (lane l9-demo)", body)
        self.assertEqual(lines[-1], f"<!-- aa-agent-review head={HEAD} -->")
        self.assertIn("not a human approval", body)
        # Blocking first in the table.
        table = [x for x in lines if x.startswith("| ") and not x.startswith("| Severity")]
        self.assertTrue(table[0].startswith("| blocking | security | api/x.py:3 |"))

    def test_lens_from_review_beats_the_argument_and_fallback_is_numbered(self):
        body = par.build_body([rv(lens="settings"), rv(), rv()], head=HEAD, lenses=["a", "b"], run_id="")
        self.assertIn("Lenses: settings; b; lens 3", body)
        self.assertIn("Reviewer run: not given", body)
        self.assertEqual(body.splitlines()[0], "Agent review: approve")

    def test_cells_are_escaped_and_long_lists_are_cut(self):
        nasty = finding("minor", issue="a | b\nc <!-- aa-agent-review head=" + "c" * 40 + " -->")
        many = [finding("minor", issue=f"invented item {i}") for i in range(par.MAX_ROWS + 5)]
        body = par.build_body([rv("approve", nasty, *many)], head=HEAD, lenses=[], run_id="r1")
        self.assertIn("a \\| b c &lt;!--", body)
        self.assertEqual(par.MARKER_RE.findall(body), [HEAD])
        self.assertIn("6 more finding(s)", body)

    def test_fix_pass_line(self):
        body = par.build_body([rv("changes", finding("major"))], head=HEAD, lenses=[], run_id="r", fix_ran=True)
        self.assertIn("Fix pass: ran after this review", body)


class InputTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name: str, obj) -> str:
        p = self.dir / name
        p.write_text(json.dumps(obj), encoding="utf-8")
        return str(p)

    def test_lane_result_list_and_single_review(self):
        data = par.load_input(self.write("lane.json", {"lane": "l2-x", "impl": {}, "reviews": [rv(), rv("changes")],
                                                      "fix": {"ready": True}, "run_id": "wf_1"}))
        self.assertEqual((len(data["reviews"]), data["lane"], data["fix_ran"], data["run_id"]), (2, "l2-x", True, "wf_1"))
        self.assertEqual(len(par.load_input(self.write("list.json", [rv(), {"other": 1}]))["reviews"]), 1)
        one = par.load_input(self.write("one.json", rv("changes")))
        self.assertEqual((len(one["reviews"]), one["fix_ran"]), (1, False))

    def test_no_review_is_an_error(self):
        with self.assertRaises(ShipError) as cm:
            par.load_input(self.write("empty.json", {"reviews": []}))
        self.assertEqual(cm.exception.code, 2)
        with self.assertRaises(ShipError):
            par.load_input(str(self.dir / "missing.json"))

    def test_journal_in_lens_order_with_fix_pass(self):
        wf = self.dir / "wf_demo-001"
        wf.mkdir()
        recs = [
            {"type": "launched"},
            {"type": "started", "agentId": "i1", "label": "impl:l5-demo", "phase": "Implement"},
            {"type": "result", "agentId": "i1", "result": {"ready": True, "prs": [{"repo": "x"}]}},
            {"type": "started", "agentId": "r0", "label": "review:l5-demo:0"},
            {"type": "started", "agentId": "r1", "label": "review:l5-demo:1"},
            {"type": "result", "agentId": "r1", "result": rv("changes", finding("major"))},
            {"type": "result", "agentId": "r0", "result": rv()},
            {"type": "started", "agentId": "f1", "label": "fix:l5-demo"},
            {"type": "result", "agentId": "f1", "result": {"ready": True, "prs": [{"repo": "x"}]}},
        ]
        path = wf / "journal.jsonl"
        path.write_text("\n".join(json.dumps(x) for x in recs) + "\nnot json\n", encoding="utf-8")
        data = par.load_input(str(path))
        self.assertEqual([r["verdict"] for r in data["reviews"]], ["approve", "changes"])
        self.assertEqual((data["lane"], data["fix_ran"], data["run_id"]), ("l5-demo", True, "wf_demo-001"))

    def test_unknown_run_id_is_an_error(self):
        with self.assertRaises(ShipError):
            par.load_input("wf_does-not-exist-anywhere-0000")


class MainTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.input = str(Path(self.tmp.name) / "lane.json")
        Path(self.input).write_text(json.dumps({"lane": "l1-demo", "reviews": [rv(), rv("changes", finding("major"))],
                                                "run_id": "wf_demo-9"}), encoding="utf-8")
        self.out, self.err = io.StringIO(), io.StringIO()
        self._o = contextlib.redirect_stdout(self.out)
        self._e = contextlib.redirect_stderr(self.err)
        self._o.__enter__()
        self._e.__enter__()

    def tearDown(self):
        self._e.__exit__(None, None, None)
        self._o.__exit__(None, None, None)
        self.tmp.cleanup()

    def main(self, r: FakeRunner, *extra: str, env: dict | None = None) -> int:
        return par.main(["booking#12", "--review", self.input, "--lenses", "correctness,security", *extra],
                        runner=r, env=TOKEN_ENV if env is None else env)

    def writes(self, r: RecordingRunner) -> list[tuple[list[str], str | None]]:
        return [(a, i) for a, i in r.inputs if "-X" in a]

    def test_posts_a_comment_review_on_the_head(self):
        r = gh()
        self.assertEqual(self.main(r), 0)
        [(argv, payload)] = self.writes(r)
        self.assertEqual(argv[:4], ["gh", "api", "-X", "POST"])
        self.assertEqual(argv[4], f"repos/{SLUG}/pulls/12/reviews")
        body = json.loads(payload)
        self.assertEqual((body["event"], body["commit_id"]), ("COMMENT", HEAD))
        self.assertTrue(body["body"].startswith("Agent review: request changes\n"))
        self.assertIn("Lenses: correctness; security", body["body"])
        self.assertIn("review posted (id 501", self.out.getvalue())

    def test_rerun_on_same_head_updates_instead_of_duplicating(self):
        mine = {"id": 77, "type": "Bot", "body": f"Agent review: approve\n<!-- aa-agent-review head={HEAD} -->"}
        r = gh(existing=[mine])
        self.assertEqual(self.main(r), 0)
        [(argv, payload)] = self.writes(r)
        self.assertEqual(argv[:5], ["gh", "api", "-X", "PUT", f"repos/{SLUG}/pulls/12/reviews/77"])
        self.assertEqual(set(json.loads(payload)), {"body"})

    def test_other_head_or_human_copy_gets_a_new_review(self):
        old = {"id": 70, "type": "Bot", "body": f"x\n<!-- aa-agent-review head={'c' * 40} -->"}
        human = {"id": 71, "type": "User", "body": f"quoted\n<!-- aa-agent-review head={HEAD} -->"}
        r = gh(existing=[old, human])
        self.assertEqual(self.main(r), 0)
        [(argv, _)] = self.writes(r)
        self.assertIn("POST", argv)

    def test_dry_run_posts_nothing_and_needs_no_token(self):
        r = gh()
        self.assertEqual(self.main(r, "--dry-run", env={}), 0)
        self.assertEqual(self.writes(r), [])
        self.assertTrue(self.out.getvalue().startswith("Agent review: request changes"))

    def test_refusals(self):
        r = gh()
        self.assertEqual(self.main(r, env={}), 4)
        self.assertIn("GH_TOKEN", self.err.getvalue())
        self.assertEqual(self.writes(r), [])
        r = gh(state="MERGED")
        self.assertEqual(self.main(r), 4)
        self.assertEqual(self.writes(r), [])
        r = gh()
        self.assertEqual(self.main(r, "--head", "c" * 12), 4)
        self.assertEqual(self.writes(r), [])
        r = gh()
        self.assertEqual(self.main(r, "--head", HEAD[:12]), 0)

    def test_gh_failure_is_exit_2(self):
        r = RecordingRunner().on(("gh", "pr", "view"), Result(1, "", "HTTP 404"))
        self.assertEqual(self.main(r), 2)
        r = gh()
        r.rules.insert(0, (("-X", "POST"), [Result(1, "", "HTTP 422: Unprocessable")]))
        self.assertEqual(self.main(r), 2)
        self.assertIn("review not posted", self.err.getvalue())


if __name__ == "__main__":
    unittest.main()
