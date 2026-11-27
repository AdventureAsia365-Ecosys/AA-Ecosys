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
# time: written out in this file they are exactly what the CI secret scan flags (generic-api-key). The constant names
# avoid credential words: CodeQL reads a name like "secret" as sensitive data written to the temp file (AA-1111).
LABEL_COLON = "Secret" + "s:"
S276_SHAPE = f"- {LABEL_COLON} `orbitquill/dev/zephyr` written (Sentry on)."
# A random token pasted as a value (invented, not a real key); joined at run time for the same reason.
VALUE_SHAPE = "Secret" + ": `Xk29fJq8LmZp2Rt7`"

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
        self.assertEqual(le.neutralise_secret_labels("secret:`lantern/key`"), "secret — `lantern/key`")
        two = le.neutralise_secret_labels(f"Secret: `a-b/c` and later {LABEL_COLON} `d.e/f-g`")
        self.assertEqual(two, "Secret — `a-b/c` and later Secrets — `d.e/f-g`")

    def test_a_token_that_is_not_a_path_shaped_name_is_left_for_the_gate(self):
        # A pasted value must reach gitleaks as written (colon and all): rewriting it would hide it from the rule.
        label = "Secret" + ":"  # joined at run time, like LABEL_COLON
        tokens = ("lanternkey", "a-b-c", "Orbit/Dev/Zephyr", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYLANTERNKEY",
                  "orbitquill/", "/orbitquill/dev", "orbit quill/dev")
        for text in (VALUE_SHAPE, label.lower() + "`lanternkey`", *(f"{label} `{t}`" for t in tokens)):
            self.assertEqual(le.neutralise_secret_labels(text), text, text)
        mixed = le.neutralise_secret_labels(f"{LABEL_COLON} `orbitquill/dev/zephyr`; {VALUE_SHAPE}")
        self.assertEqual(mixed, f"Secrets — `orbitquill/dev/zephyr`; {VALUE_SHAPE}")

    def test_other_text_is_left_as_written(self):
        for text in ("Secrets rotated on 02/11.", "Secret named orbitquill/dev/zephyr written.",
                     "secret_key: `x`", "Secretary: `Robin`", "The key: `lantern`", "Secrets:\n\n`code block`",
                     "**Wrong `X-Lantern-Secret`:** 403", "_(no description)_"):
            self.assertEqual(le.neutralise_secret_labels(text), text, text)

    def test_render_rewrites_comments_and_description(self):
        out = le.render(issue(comment=S276_SHAPE, desc=f"{LABEL_COLON} `orbitquill/dev/desc` created"))
        self.assertIn("- Secrets — `orbitquill/dev/zephyr` written", out)
        self.assertIn("Secrets — `orbitquill/dev/desc` created", out)
        self.assertNotIn(LABEL_COLON + " `", out)


class PersonalAddressTest(unittest.TestCase):
    """S288: a person's company address never lands in the public export; role and test mailboxes stay."""

    def test_personal_address_is_masked(self):
        self.assertEqual(le.mask_personal_addresses("Invite robin@adventure.asia today"), "Invite r***@adventure.asia today")
        self.assertEqual(le.mask_personal_addresses("Robin.Lee@Adventure.Asia"), "R***@adventure.asia")

    def test_role_and_test_mailboxes_stay(self):
        for text in ("info@adventure.asia", "admin@adventure.asia", "e2e-s235+booking@adventure.asia",
                     "robin@example.com", "adventure.asia", "@adventure.asia"):
            self.assertEqual(le.mask_personal_addresses(text), text, text)

    def test_render_masks_title_description_comments(self):
        it = issue(comment="Sent to robin@adventure.asia", desc="Owner robin@adventure.asia")
        it["title"] = "Account for robin@adventure.asia"
        out = le.render(it)
        self.assertNotIn("robin@", out)
        self.assertEqual(out.count("r***@adventure.asia"), 4)


class ResourceIdMaskTest(unittest.TestCase):
    """AA-1185: docs/linear-export/ is in the scope of the root docs lint `resource-ids --mode error`, so an export of an
    issue that quotes account IDs, ARNs, network ids or an outside mailbox must leave nothing for the lint to fail on.
    Invented values only."""

    ACCT = "4" * 6 + "7" * 6
    OTHER = "1234" * 3
    TEXT = (f"Role arn:aws:iam::{ACCT}:role/lantern-runner in account {ACCT} (also {OTHER}). "
            "Group sg-0a1b2c3d4e5f60718, vpc-0a1b2c3d, lb app/lantern-alb/0123456789abcdef, "
            "pool us-west-1_AbCdEf123, host https://ab12cd34ef.execute-api.us-west-1.amazonaws.com/dev, "
            "mail lantern.keeper@gmail.com and ops@vendor-lantern.vn; keep robin@example.com, info@adventure.asia, "
            f"bucket aa-lantern-bronze-{ACCT}, tenant 0f0e0d0c-0b0a-4909-8807-{OTHER}.")

    def _lint_findings(self, page: str) -> list:
        sys.path.insert(0, str(le.ROOT / "tools" / "docs"))
        import check_docs_text
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "docs" / "linear-export" / "lantern-works" / "AA-9001.md"
            target.parent.mkdir(parents=True)
            target.write_text(page, encoding="utf-8")
            return check_docs_text.check_resource_ids(Path(tmp), ["docs/linear-export/lantern-works/AA-9001.md"])

    def test_raw_text_fails_the_lint(self):
        self.assertTrue(self._lint_findings(self.TEXT))

    def test_masked_text_passes_the_lint_and_keeps_names(self):
        out = le.mask_resource_ids(self.TEXT, {self.ACCT: "acc2"})
        self.assertEqual(self._lint_findings(out), [])
        for kept in ("arn:...:iam::{acc2}:role/lantern-runner", "account {acc2}", "{aws-account}", "sg-{masked}",
                     "vpc-{masked}", "app/lantern-alb/{masked}", "{user-pool-id}", "{apigw-id}.execute-api.",
                     "{outside-mailbox} and {outside-mailbox}", "robin@example.com", "info@adventure.asia",
                     f"aa-lantern-bronze-{self.ACCT}", f"0f0e0d0c-0b0a-4909-8807-{self.OTHER}"):
            self.assertIn(kept, out, kept)

    def test_aliases_come_from_the_environment(self):
        with mock.patch.dict(os.environ, {"AWS_ACCOUNT_ALIASES": f"acc2={self.ACCT}, bad=12"}):
            self.assertEqual(le.account_aliases(), {self.ACCT: "acc2"})
            self.assertEqual(le.mask_resource_ids(f"id {self.ACCT}"), "id {acc2}")
        with mock.patch.dict(os.environ, {"AWS_ACCOUNT_ALIASES": ""}):
            self.assertEqual(le.mask_resource_ids(f"id {self.ACCT}"), "id {aws-account}")

    def test_render_and_index_pass_the_lint(self):
        it = issue(comment=self.TEXT, desc=f"Root mailbox lantern.keeper@gmail.com on {self.ACCT}")
        it["title"] = f"Clean account {self.ACCT}"
        it["attachments"] = {"nodes": [{"title": f"Report {self.ACCT}", "url": "https://example.com/r"}]}
        self.assertEqual(self._lint_findings(le.render(it)), [])
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(le, "OUT", Path(tmp)):
            le.write_index([it])
            index = (Path(tmp) / "README.md").read_text(encoding="utf-8")
        self.assertNotIn(self.ACCT, index)
        self.assertEqual(self._lint_findings(index), [])


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
        self.assertTrue(args[1].endswith("tree"))  # a copy of only the run's files, not the whole export folder

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
        with mock.patch.object(le, "_resolve_gitleaks", lambda: None):
            rc, _, err = self.gate("clean", binary="")  # unset: the resolver finds none
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

    def test_unchanged_files_are_scanned_again_after_a_red_or_unscanned_run(self):
        # Run 1 writes the files and stops on the gate (no gitleaks / a finding); run 2 rewrites nothing. Run 2 must
        # still scan the issue file and the index, and must not archive when that scan is red.
        page = self.out / "lantern-works" / "AA-9001.md"
        for first_rc in (le.EXIT_NO_GITLEAKS, le.EXIT_LEAKS):
            rc, _, _, _ = self.run_main(["--archive", "--apply"], first_rc)
            self.assertEqual(rc, first_rc)
            before = page.stat().st_mtime_ns
            rc, gql, gate, out = self.run_main(["--archive", "--apply"], le.EXIT_LEAKS)
            self.assertEqual(page.stat().st_mtime_ns, before)  # nothing rewritten
            self.assertEqual(sorted(p.name for p in gate.call_args.args[0]), ["AA-9001.md", "README.md"])
            self.assertEqual(rc, le.EXIT_LEAKS)
            gql.assert_not_called()
        rc, gql, gate, out = self.run_main(["--archive", "--apply"], 0)
        self.assertIn("files written/updated: 0", out)
        gql.assert_called_once()

    def test_only_scans_the_named_issue_files_even_when_unchanged(self):
        self.run_main([], 0)
        _, _, gate, _ = self.run_main(["--only", "AA-9001"], 0)
        self.assertEqual([p.name for p in gate.call_args.args[0]], ["AA-9001.md"])
        self.assertFalse(gate.call_args.args[1])


REAL = le.gitleaks_bin()  # S294: the resolver, not shutil.which (a mise shim with no version fails)


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

    def test_a_pasted_value_after_a_secret_label_still_fires_after_render(self):
        self.assertEqual([x["rule"] for x in self.scan(le.render(issue(comment=VALUE_SHAPE)))], ["generic-api-key"])


if __name__ == "__main__":
    unittest.main()



class GitleaksBinTest(unittest.TestCase):
    """S294: without GITLEAKS_BIN the export gate uses the pre-push resolver, so a broken mise shim is skipped."""

    def test_resolver_is_used_without_gitleaks_bin(self):
        with mock.patch.dict(os.environ, {"GITLEAKS_BIN": ""}), \
                mock.patch.object(le, "_resolve_gitleaks", lambda: "/opt/gitleaks-8.30.1/gitleaks"):
            self.assertEqual(le.gitleaks_bin(), "/opt/gitleaks-8.30.1/gitleaks")

    def test_the_resolver_skips_a_shim_that_cannot_answer_its_version(self):
        sys.path.insert(0, str(le.ROOT / "tools" / "github"))
        import gitleaks_resolve

        def run_version(exe):
            return (None, "No version is set for shim: gitleaks") if "shims" in exe else ("8.30.1", "")

        found = gitleaks_resolve.resolve([], run_version=run_version, env={},
                                         on_path=["/home/u/.local/share/mise/shims/gitleaks", "/usr/bin/gitleaks"])
        self.assertEqual(found.path, "/usr/bin/gitleaks")
