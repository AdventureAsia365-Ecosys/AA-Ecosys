"""Tests for secrets_register.py (AA-1183 part 1). Run: python3 -m unittest discover -s tools/security -p 'test_*.py'.

Offline, PyYAML only. The fixture rows use invented names and stores; the last class checks the real register files
(the YAML validates, and the Markdown view is rendered from it).
"""
from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import secrets_register as sr  # noqa: E402

BASE = """\
version: 2
updated: "2026-11-27"
secrets:
  - name: demo/dev/db-password
    store: "secretsmanager:acc2"
    status: keep
    rotation:
      class: scheduled
      interval_days: 180
      owner_role: tech-lead
      method: script
      last_rotated: "2026-10-01"
      next_due: "2027-03-30"
      events: [key-ceremony]
  - name: DEMO_DB_PASSWORD
    store: "github:Demo-Repo"
    status: keep
    rotation:
      class: scheduled
      last_rotated: "2026-09-01"
      copy_of: "secretsmanager:acc2 demo/dev/db-password"
  - name: demo/dev/vendor-key
    store: "secretsmanager:acc2"
    status: keep
    rotation:
      class: on-incident
      owner_role: business-owner
      method: vendor-console
      last_rotated: unknown
      events: [suspected-leak]
  - name: DEMO_ROLE_ARN
    store: "github:Demo-Repo"
    status: keep
    rotation:
      class: identifier
  - name: demo.example.test
    store: "acm:us-west-1"
    status: keep
    rotation:
      class: auto
      owner_role: aws
      method: aws
      expires: "2027-01-10"
  - name: DEMO_OLD_TOKEN
    store: "github:Demo-Repo"
    status: orphan-delete
    rotation:
      class: retired
      next_due: "2026-12-01"
  - name: DEMO_GONE
    store: "github:Demo-Repo"
    status: deleted
    rotation:
      class: retired
"""


def load_text(text: str) -> sr.Register:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "register.yaml"
        p.write_text(text, encoding="utf-8")
        return sr.load(p)


def errors_for(text: str) -> list[str]:
    return sr.validate(load_text(text))


def patch(old: str, new: str) -> str:
    assert old in BASE, old
    return BASE.replace(old, new, 1)


class ValidateTest(unittest.TestCase):
    def test_base_fixture_is_valid(self):
        self.assertEqual(errors_for(BASE), [])

    def test_version_must_be_2(self):
        errs = errors_for(patch("version: 2", "version: 1"))
        self.assertTrue(any("version" in e for e in errs), errs)

    def test_row_without_rotation_block(self):
        text = BASE + '  - name: DEMO_BARE\n    store: "github:Demo-Repo"\n    status: keep\n    rotation: none\n'
        self.assertTrue(any("rotation must be a mapping" in e for e in errors_for(text)))

    def test_unknown_class_and_key(self):
        errs = errors_for(patch("class: identifier", "class: monthly"))
        self.assertTrue(any("unknown rotation class" in e for e in errs), errs)
        errs = errors_for(patch("      class: identifier", "      class: identifier\n      colour: red"))
        self.assertTrue(any("unknown rotation keys" in e for e in errs), errs)

    def test_next_due_later_than_interval_is_refused(self):
        errs = errors_for(patch('next_due: "2027-03-30"', 'next_due: "2027-04-01"'))
        self.assertTrue(any("later than last_rotated + 180 days" in e for e in errs), errs)

    def test_next_due_earlier_than_interval_is_fine(self):
        self.assertEqual(errors_for(patch('next_due: "2027-03-30"', 'next_due: "2026-12-15"')), [])

    def test_next_due_before_last_rotated_is_refused(self):
        errs = errors_for(patch('next_due: "2027-03-30"', 'next_due: "2026-09-30"'))
        self.assertTrue(any("before last_rotated" in e for e in errs), errs)

    def test_scheduled_needs_interval_dates_and_method(self):
        errs = errors_for(patch("      interval_days: 180\n", ""))
        self.assertTrue(any("needs interval_days" in e for e in errs), errs)
        errs = errors_for(patch('      last_rotated: "2026-10-01"\n', ""))
        self.assertTrue(any("needs last_rotated" in e for e in errs), errs)
        errs = errors_for(patch("      method: script\n", ""))
        self.assertTrue(any("needs method" in e for e in errs), errs)

    def test_unknown_dates_are_allowed_on_scheduled(self):
        text = patch('last_rotated: "2026-10-01"\n      next_due: "2027-03-30"',
                     'last_rotated: unknown\n      next_due: unknown')
        self.assertEqual(errors_for(text), [])

    def test_bad_date(self):
        errs = errors_for(patch('last_rotated: "2026-10-01"', 'last_rotated: "01/10/2026"'))
        self.assertTrue(any("not YYYY-MM-DD" in e for e in errs), errs)

    def test_expires_cannot_be_unknown(self):
        errs = errors_for(patch('expires: "2027-01-10"', "expires: unknown"))
        self.assertTrue(any("expires cannot be unknown" in e for e in errs), errs)

    def test_on_incident_has_no_schedule(self):
        errs = errors_for(patch("      last_rotated: unknown\n", "      last_rotated: unknown\n      interval_days: 90\n"))
        self.assertTrue(any("on-incident has no interval_days" in e for e in errs), errs)

    def test_on_incident_needs_last_rotated(self):
        errs = errors_for(patch("      last_rotated: unknown\n      events: [suspected-leak]",
                                "      events: [suspected-leak]"))
        self.assertTrue(any("on-incident needs last_rotated" in e for e in errs), errs)

    def test_identifier_has_no_rotation_data(self):
        errs = errors_for(patch("      class: identifier", '      class: identifier\n      last_rotated: "2026-01-01"'))
        self.assertTrue(any("an identifier has no last_rotated" in e for e in errs), errs)

    def test_gone_status_needs_retired_and_back(self):
        errs = errors_for(patch("    status: deleted\n    rotation:\n      class: retired",
                                "    status: deleted\n    rotation:\n      class: identifier"))
        self.assertTrue(any("needs class retired" in e for e in errs), errs)
        errs = errors_for(patch("    status: orphan-delete", "    status: keep"))
        self.assertTrue(any("class retired needs" in e for e in errs), errs)

    def test_copy_of_unknown_row(self):
        errs = errors_for(patch('copy_of: "secretsmanager:acc2 demo/dev/db-password"',
                                'copy_of: "secretsmanager:acc2 demo/dev/missing"'))
        self.assertTrue(any("names no register row" in e for e in errs), errs)

    def test_copy_takes_interval_from_primary(self):
        errs = errors_for(patch('      last_rotated: "2026-09-01"\n', '      last_rotated: "2026-09-01"\n      interval_days: 30\n'))
        self.assertTrue(any("takes interval_days from its primary" in e for e in errs), errs)

    def test_copy_has_the_class_of_its_primary(self):
        errs = errors_for(patch('      class: scheduled\n      last_rotated: "2026-09-01"',
                                '      class: on-incident\n      last_rotated: "2026-09-01"'))
        self.assertTrue(any("class of its primary" in e for e in errs), errs)

    def test_copy_needs_its_own_last_rotated(self):
        errs = errors_for(patch('      last_rotated: "2026-09-01"\n      copy_of',
                                '      copy_of'))
        self.assertTrue(any("needs its own last_rotated" in e for e in errs), errs)

    def test_unknown_owner_role_method_event(self):
        errs = errors_for(patch("owner_role: business-owner", "owner_role: intern"))
        self.assertTrue(any("unknown owner_role" in e for e in errs), errs)
        errs = errors_for(patch("method: vendor-console", "method: carrier-pigeon"))
        self.assertTrue(any("unknown method" in e for e in errs), errs)
        errs = errors_for(patch("events: [suspected-leak]", "events: [full-moon]"))
        self.assertTrue(any("unknown event" in e for e in errs), errs)

    def test_duplicate_row(self):
        text = BASE + '  - name: DEMO_ROLE_ARN\n    store: "github:Demo-Repo"\n    status: keep\n    rotation:\n      class: identifier\n'
        self.assertTrue(any("duplicate" in e for e in errors_for(text)))


class ScheduleTest(unittest.TestCase):
    def setUp(self):
        self.reg = load_text(BASE)
        self.keys = self.reg.by_key()

    def test_copy_inherits_interval_and_next_due(self):
        r = sr.effective(self.keys["github:Demo-Repo DEMO_DB_PASSWORD"], self.reg)
        self.assertEqual((r.interval_days, r.next_due, r.last_rotated), (180, "2027-03-30", "2026-09-01"))
        self.assertEqual([e.name for e in sr.copies_of(self.keys["secretsmanager:acc2 demo/dev/db-password"], self.reg)],
                         ["DEMO_DB_PASSWORD"])

    def test_schedule_order_and_scope(self):
        names = [e.name for e in sr.schedule(self.reg)]
        # dated rows first (next due or expiry), then rows without a date; identifiers and gone rows left out
        self.assertEqual(names, ["DEMO_OLD_TOKEN", "demo.example.test", "DEMO_DB_PASSWORD", "demo/dev/db-password",
                                 "demo/dev/vendor-key"])

    def test_labels(self):
        self.assertEqual(sr.label(self.keys["secretsmanager:acc2 demo/dev/db-password"], self.reg), "scheduled 180 d")
        self.assertEqual(sr.label(self.keys["github:Demo-Repo DEMO_DB_PASSWORD"], self.reg),
                         "copy of `demo/dev/db-password`")
        self.assertEqual(sr.label(self.keys["acm:us-west-1 demo.example.test"], self.reg), "auto (AWS)")
        self.assertEqual(sr.label(self.keys["secretsmanager:acc2 demo/dev/vendor-key"], self.reg), "on incident")


MD = textwrap.dedent(f"""\
    # Demo register

    ## Rotation

    {sr.MD_BEGIN}
    stale
    {sr.MD_END}

    ## Register

    ### Secrets Manager

    | Name | Owner app | Rotation | Status | Notes |
    |---|---|---|---|---|
    | `demo/dev/db-password` | demo | old text | **planned** | n |
    | `demo/dev/vendor-key` | demo | old | **keep** | n |

    ### Other stores

    | Name | Store | Rotation | Status | Notes |
    |---|---|---|---|---|
    | `DEMO_DB_PASSWORD` | `github:Demo-Repo` | x | **keep** | n |
    | `DEMO_ROLE_ARN` | `github:Demo-Repo` | x | **keep** | n |
    | `demo.example.test` | `acm:us-west-1` | x | **keep** | n |
    | `DEMO_OLD_TOKEN` | `github:Demo-Repo` | x | **orphan-delete** | n |
    | `DEMO_GONE` | `github:Demo-Repo` | x | **deleted** | n |
    """)


class MarkdownTest(unittest.TestCase):
    def setUp(self):
        self.reg = load_text(BASE)

    def test_render_sets_cells_and_schedule(self):
        new, problems = sr.render_md(MD, self.reg)
        self.assertEqual(problems, [])
        self.assertIn("| `demo/dev/db-password` | demo | scheduled 180 d | **keep** | n |", new)
        self.assertIn("| `DEMO_DB_PASSWORD` | `github:Demo-Repo` | copy of `demo/dev/db-password` | **keep** | n |", new)
        self.assertIn("| `DEMO_ROLE_ARN` | `github:Demo-Repo` | identifier | **keep** | n |", new)
        self.assertNotIn("stale", new)
        self.assertIn("| `demo/dev/db-password` | `secretsmanager:acc2` | scheduled | 180 d | tech-lead | 2026-10-01 | "
                      "2027-03-30 |", new)
        # idempotent
        again, problems = sr.render_md(new, self.reg)
        self.assertEqual((again, problems), (new, []))

    def test_missing_and_extra_rows_are_problems(self):
        md = MD.replace("| `DEMO_GONE` | `github:Demo-Repo` | x | **deleted** | n |\n",
                        "| `DEMO_STRAY` | `github:Demo-Repo` | x | **keep** | n |\n")
        _, problems = sr.render_md(md, self.reg)
        self.assertIn("secrets-register.md: no table row for github:Demo-Repo DEMO_GONE", problems)
        self.assertTrue(any("DEMO_STRAY has no row in the YAML" in p for p in problems), problems)

    def test_markers_required(self):
        _, problems = sr.render_md(MD.replace(sr.MD_END, ""), self.reg)
        self.assertEqual(problems, ["the rotation schedule markers are missing or unbalanced"])


class RealRegisterTest(unittest.TestCase):
    """Guards on the committed register: v2 valid, the Markdown view rendered from it, decisions kept."""

    @classmethod
    def setUpClass(cls):
        cls.reg = sr.load(sr.REGISTER)

    def test_register_validates(self):
        self.assertEqual(sr.validate(self.reg), [])

    def test_markdown_view_is_current(self):
        md = sr.REGISTER_MD.read_text(encoding="utf-8")
        new, problems = sr.render_md(md, self.reg)
        self.assertEqual(problems, [])
        self.assertEqual(new, md, "run: python3 tools/security/secrets_register.py md --write")

    def test_llm_vendor_keys_rotate_only_on_incident(self):
        # tech lead decision S295 N1: no scheduled rotation for LLM vendor keys, a vendor-side spend limit instead
        keys = self.reg.by_key()
        for name in ("aa-cis/dev/openai-key", "aa-llm/dev/anthropic-direct"):
            self.assertEqual(keys[f"secretsmanager:acc2 {name}"].rotation.cls, "on-incident", name)

    def test_every_live_credential_has_last_rotated(self):
        for e in self.reg.entries:
            r = sr.effective(e, self.reg)
            if r.cls in ("scheduled", "on-incident"):
                self.assertIsNotNone(r.last_rotated, e.key)

    def test_no_account_id_in_the_register(self):
        import re
        for path in (sr.REGISTER, sr.REGISTER_MD):
            self.assertIsNone(re.search(r"(?<![\w-])\d{12}(?![\w-])", path.read_text(encoding="utf-8")), path.name)


if __name__ == "__main__":
    unittest.main()
