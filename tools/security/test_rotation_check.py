"""Tests for rotation_check.py (AA-1183 part 2). Run: python3 -m unittest discover -s tools/security -p 'test_*.py'.

Offline: every AWS, GitHub and RDAP answer is a recorded shape with invented names, dates and ids; no network, no AWS
credentials. The forbidden-call class fails when the tool could ever read a secret value.
"""
from __future__ import annotations

import ast
import datetime as dt
import gzip
import json
import re
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rotation_check as rc  # noqa: E402
import secrets_register as sr  # noqa: E402

ROOT = HERE.parents[1]
TODAY = dt.date(2026, 11, 30)

REGISTER = """\
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
      last_rotated: "2026-06-10"
      next_due: "2026-12-07"
  - name: DEMO_DB_PASSWORD
    store: "github:Demo-App/dev"
    status: keep
    rotation:
      class: scheduled
      last_rotated: "2026-06-10"
      copy_of: "secretsmanager:acc2 demo/dev/db-password"
  - name: demo/dev/hmac
    store: "secretsmanager:acc2"
    status: keep
    rotation:
      class: scheduled
      interval_days: 365
      owner_role: tech-lead
      method: manual
      last_rotated: "2026-11-01"
      next_due: "2027-11-01"
  - name: demo/dev/overdue
    store: "secretsmanager:acc2"
    status: keep
    rotation:
      class: scheduled
      interval_days: 180
      owner_role: tech-lead
      method: manual
      last_rotated: "2026-05-01"
      next_due: "2026-10-28"
  - name: demo/dev/unknown
    store: "secretsmanager:acc2"
    status: open-item
    rotation:
      class: scheduled
      interval_days: 365
      owner_role: tech-lead
      method: manual
      last_rotated: unknown
      next_due: unknown
  - name: demo/dev/vendor-key
    store: "secretsmanager:acc2"
    status: keep
    rotation:
      class: on-incident
      owner_role: tech-lead
      method: vendor-console
      last_rotated: "2026-08-01"
  - name: demo/dev/old-thing
    store: "secretsmanager:acc2"
    status: deleted
    rotation:
      class: retired
  - name: demo/dev/to-revoke
    store: "secretsmanager:acc2"
    status: orphan-delete
    rotation:
      class: retired
      next_due: "2026-11-20"
  - name: DEMO_REPO_TOKEN
    store: "github:Demo-App"
    status: keep
    rotation:
      class: scheduled
      interval_days: 90
      owner_role: tech-lead
      method: vendor-console
      last_rotated: "2026-09-10"
      next_due: "2026-12-09"
  - name: DEMO_MISSING
    store: "github:Demo-App"
    status: keep
    rotation:
      class: scheduled
      interval_days: 365
      owner_role: tech-lead
      method: manual
      last_rotated: "2026-10-01"
      next_due: "2027-10-01"
  - name: DEMO_ROLE
    store: "github:Demo-App"
    status: keep
    rotation:
      class: identifier
  - name: demo-client
    store: "cognito:demo-pool"
    status: keep
    rotation:
      class: scheduled
      interval_days: 365
      owner_role: tech-lead
      method: script
      last_rotated: "2026-10-01"
      next_due: "2027-10-01"
  - name: alias/demo-data
    store: "kms:acc2"
    status: keep
    rotation:
      class: auto
      interval_days: 365
      owner_role: aws
      method: aws
      last_rotated: "2026-10-23"
      next_due: "2027-10-23"
  - name: api.demo.example
    store: "acm:us-west-1"
    status: keep
    rotation:
      class: auto
      owner_role: aws
      method: aws
      expires: "2026-12-08"
  - name: img.demo.example
    store: "acm:us-east-1"
    status: keep
    rotation:
      class: auto
      owner_role: aws
      method: aws
      expires: "2027-05-07"
  - name: server certificate rds-ca-demo-g1
    store: "rds:demo-db"
    status: keep
    rotation:
      class: auto
      owner_role: aws
      method: aws
      expires: "2027-07-07"
  - name: human CLI access key
    store: "iam:acc2"
    status: keep
    rotation:
      class: scheduled
      interval_days: 90
      owner_role: tech-lead
      method: manual
      last_rotated: "2026-11-17"
      next_due: "2027-02-15"
  - name: legacy key
    store: "iam:acc9"
    status: orphan-delete
    rotation:
      class: retired
      next_due: "2026-12-20"
  - name: demo.example
    store: "domain:registrar"
    status: keep
    rotation:
      class: auto
      owner_role: registrar
      method: registrar
      expires: "2027-04-04"
  - name: Demo vendor console
    store: "vendor:demo"
    status: keep
    rotation:
      class: on-incident
      owner_role: tech-lead
      method: vendor-console
      last_rotated: unknown
  - name: DEMO_PLANNED
    store: "github:Demo-App"
    status: planned
    rotation:
      class: scheduled
      interval_days: 365
      owner_role: tech-lead
      method: manual
      last_rotated: unknown
      next_due: unknown
"""

POLICY = """\
[windows]
amber_days = 30
amber_days_short_interval = 14
short_interval_max_days = 90
expiry_amber_days = 30
expiry_red_days = 14
date_tolerance_days = 1

[issues]
label = "secret-rotation"
label_color = "b60205"
label_description = "test"
max_writes_per_run = 60

[scope]
github_owner = "Demo-Org"
github_repos = ["Demo-App"]
aws_account_label = "acc2"
aws_region = "us-west-1"

[rdap]
default_base = "https://rdap.example.test/domain/"
timeout_seconds = 5

[rdap.overrides]
"""


def _tmp(text: str, suffix: str) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(textwrap.dedent(text))
    f.close()
    return Path(f.name)


def load_fixture():
    reg = sr.load(_tmp(REGISTER, ".yaml"))
    errors = sr.validate(reg)
    assert not errors, errors
    return reg, rc.load_policy(_tmp(POLICY, ".toml"))


def full_inventory() -> rc.Inventory:
    """Every source read, every expected row present and in order (all green unless a test changes it)."""
    inv = rc.Inventory()
    inv.sources = {"github:Demo-App": "ok", "aws:secretsmanager": "ok", "aws:cognito": "ok", "aws:kms": "ok",
                   "aws:acm:us-west-1": "ok", "aws:acm:us-east-1": "ok", "aws:rds": "ok", "aws:iam": "ok",
                   "rdap": "ok"}
    inv.sm = {n: {"rotation_enabled": False, "last_rotated": None, "next_rotation": None, "current_created": c}
              for n, c in [("demo/dev/db-password", "2026-06-10"), ("demo/dev/hmac", "2026-11-01"),
                           ("demo/dev/overdue", "2026-05-01"), ("demo/dev/unknown", "2025-01-01"),
                           ("demo/dev/vendor-key", "2026-08-01"), ("demo/dev/to-revoke", "2025-01-01")]}
    inv.github = {"github:Demo-App": {"DEMO_REPO_TOKEN": "2026-09-10", "DEMO_MISSING": "2026-10-01",
                                      "DEMO_ROLE": "2026-01-01"},
                  "github:Demo-App/dev": {"DEMO_DB_PASSWORD": "2026-06-11"}}
    inv.cognito = {"demo-pool": {"demo-client": ["2026-10-01"]}}
    inv.kms = {"alias/demo-data": {"state": "Enabled", "spec": "SYMMETRIC_DEFAULT", "rotation_enabled": True,
                                   "next_rotation": "2027-10-23"}}
    inv.acm = {"us-west-1": {"api.demo.example": {"not_after": "2027-01-21", "status": "ISSUED",
                                                  "renewal_status": "SUCCESS", "eligibility": "ELIGIBLE",
                                                  "in_use": True}},
               "us-east-1": {"img.demo.example": {"not_after": "2027-05-07", "status": "ISSUED",
                                                  "renewal_status": None, "eligibility": "ELIGIBLE",
                                                  "in_use": True}}}
    inv.rds = {"demo-db": {"ca": "rds-ca-demo-g1", "valid_till": "2027-07-07"}}
    inv.iam = {"acc2": ["2026-11-17"]}
    inv.domains = {"demo.example": "2027-04-04"}
    return inv


def by_key(report: rc.Report) -> dict:
    return {i.entry.key: i for i in report.items}


class ForbiddenCallTest(unittest.TestCase):
    """The tool must never be able to read a secret value."""

    # Calls that return a secret value, a private key or a client secret (or create one). Normalised: lower case,
    # without '-', '_' and spaces, so GetSecretValue, get-secret-value and get_secret_value all match.
    FORBIDDEN = ("getsecretvalue", "batchgetsecretvalue", "describeuserpoolclient", "adduserpoolclientsecret",
                 "exportcertificate", "getparameter", "decrypt", "generatedatakey", "createaccesskey",
                 "getcredentialreport", "getsecret(", "secretstring", "secretbinary")

    def test_source_names_no_secret_reading_call(self):
        src = (HERE / "rotation_check.py").read_text(encoding="utf-8").lower()
        flat = re.sub(r"[-_\s]", "", src)
        for token in self.FORBIDDEN:
            if token in ("secretstring", "secretbinary"):
                # Only allowed inside the scrub pattern that DROPS such keys.
                flat_wo_scrub = flat.replace("secret(value|string|binary)", "")
                self.assertNotIn(token, flat_wo_scrub, token)
                continue
            self.assertNotIn(token, flat, f"rotation_check.py names a secret-reading call: {token}")

    def test_no_sdk_or_raw_client(self):
        tree = ast.parse((HERE / "rotation_check.py").read_text(encoding="utf-8"))
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(imported & {"boto3", "botocore"}, "AWS calls go through AwsCli (allowlist) only")

    def test_allowlist_is_metadata_only(self):
        for (service, op), action in rc.AWS_CALLS.items():
            self.assertTrue(op.startswith(("list-", "describe-")) or op == "get-key-rotation-status", op)
            self.assertNotIn("describe-user-pool-client", op.replace("describe-user-pool-clients", ""))
            self.assertNotRegex(action, r"(?i)getsecret|decrypt|export|getparameter|createaccesskey")
            self.assertEqual(action.split(":")[0], {"cognito-idp": "cognito-idp"}.get(service, service))

    def test_cli_refuses_other_calls_without_running(self):
        ran = []
        cli = rc.AwsCli(runner=lambda argv: ran.append(argv) or (0, "{}", ""))
        for service, op in [("secretsmanager", "get-secret-value"), ("cognito-idp", "describe-user-pool-client"),
                            ("acm", "export-certificate"), ("ssm", "get-parameter")]:
            with self.assertRaises(rc.CheckError):
                cli.call(service, op, "us-west-1")
        self.assertEqual(ran, [])

    def test_iam_actions_frozen(self):
        # The same list is the policy statement of the compliance evidence role (AA-CIS-Infra
        # accounts/aa365/compliance_evidence.tf, local.compliance_evidence_rotation_read): change both together.
        self.assertEqual(sorted(set(rc.AWS_CALLS.values())), [
            "acm:DescribeCertificate", "acm:ListCertificates", "cognito-idp:ListUserPoolClientSecrets",
            "cognito-idp:ListUserPoolClients", "cognito-idp:ListUserPools", "iam:ListAccessKeys", "iam:ListUsers",
            "kms:DescribeKey", "kms:GetKeyRotationStatus", "kms:ListAliases", "rds:DescribeDBInstances",
            "secretsmanager:ListSecretVersionIds", "secretsmanager:ListSecrets"])

    def test_scrub_drops_secret_members(self):
        answer = {"ClientSecrets": [{"ClientSecretId": "id-1", "ClientSecretValue": "x",
                                     "ClientSecretCreateDate": "2026-10-01T00:00:00+00:00"}],
                  "SecretString": "x", "Nested": {"PrivateKey": "x", "Ok": 1}}
        self.assertEqual(rc.scrub(answer), {"ClientSecrets": [{"ClientSecretId": "id-1",
                                                               "ClientSecretCreateDate": "2026-10-01T00:00:00+00:00"}],
                                            "Nested": {"Ok": 1}})


class HelpersTest(unittest.TestCase):
    def test_to_date(self):
        self.assertEqual(rc.to_date("2026-10-22T06:11:40Z"), dt.date(2026, 10, 22))
        self.assertEqual(rc.to_date("2026-10-22T23:30:00-05:00"), dt.date(2026, 10, 23))
        self.assertEqual(rc.to_date(0), dt.date(1970, 1, 1))
        self.assertEqual(rc.to_date("2026-10-22"), dt.date(2026, 10, 22))
        self.assertIsNone(rc.to_date("unknown"))
        self.assertIsNone(rc.to_date("not a date"))

    def test_redact(self):
        text = "User: arn:aws:sts::123456789012:assumed-role/x/y is not authorized; ask ops@example.test"
        out = rc.redact(text)
        self.assertNotIn("123456789012", out)
        self.assertNotIn("arn:aws", out)
        self.assertNotIn("@example", out)

    def test_publishable_guard(self):
        rc.assert_publishable("plain text 2026-11-30", "x")
        rc.assert_publishable("acp/cms/0a7f87e8-8b4f-4e52-9992-123456789012", "a tenant secret name with a UUID")
        for bad in ("id 123456789012", "arn:aws:iam::role", "s3://bucket", "who@example.test"):
            with self.assertRaises(rc.CheckError):
                rc.assert_publishable(bad, "x")


class PolicyTest(unittest.TestCase):
    def test_real_policy_loads(self):
        p = rc.load_policy()
        self.assertEqual(p.amber_window(90), p.amber_days_short_interval)
        self.assertEqual(p.amber_window(180), p.amber_days)
        self.assertEqual(p.label, "secret-rotation")
        self.assertIn("AA-Ecosys", p.github_repos)

    def test_bad_policy(self):
        for old, new in [("expiry_red_days = 14", "expiry_red_days = 40"),
                         ("amber_days = 30", "amber_days = -1"),
                         ("amber_days_short_interval = 14", "amber_days_short_interval = 31")]:
            with self.assertRaises(rc.CheckError, msg=new):
                rc.load_policy(_tmp(POLICY.replace(old, new, 1), ".toml"))
        with self.assertRaises(rc.CheckError):
            rc.load_policy(_tmp("[windows]\n", ".toml"))


class EvaluateTest(unittest.TestCase):
    def setUp(self):
        self.reg, self.policy = load_fixture()

    def run_eval(self, inv: rc.Inventory, today: dt.date = TODAY) -> rc.Report:
        return rc.evaluate(self.reg, inv, self.policy, today)

    def test_baseline_levels(self):
        report = self.run_eval(full_inventory())
        items = by_key(report)
        self.assertEqual(items["secretsmanager:acc2 demo/dev/db-password"].level, rc.AMBER)   # due in 7 days
        self.assertEqual(items["secretsmanager:acc2 demo/dev/hmac"].level, rc.GREEN)
        self.assertEqual(items["secretsmanager:acc2 demo/dev/overdue"].level, rc.RED)
        self.assertIn("overdue since 2026-10-28", " ".join(items["secretsmanager:acc2 demo/dev/overdue"].reasons))
        self.assertEqual(items["secretsmanager:acc2 demo/dev/unknown"].level, rc.RED)
        self.assertIn("unknown", items["secretsmanager:acc2 demo/dev/unknown"].reasons[0])
        self.assertEqual(items["secretsmanager:acc2 demo/dev/vendor-key"].level, rc.GREEN)   # on-incident
        self.assertEqual(items["vendor:demo Demo vendor console"].level, rc.GREEN)            # on-incident unknown
        self.assertEqual(items["secretsmanager:acc2 demo/dev/to-revoke"].level, rc.RED)       # revocation overdue
        self.assertEqual(items["github:Demo-App DEMO_REPO_TOKEN"].level, rc.AMBER)            # 90 d item, 9 days
        self.assertEqual(items["github:Demo-App DEMO_MISSING"].level, rc.GREEN)
        self.assertEqual(items["github:Demo-App/dev DEMO_DB_PASSWORD"].level, rc.GREEN)       # copy, in sync
        self.assertEqual(items["github:Demo-App/dev DEMO_DB_PASSWORD"].due, dt.date(2026, 12, 7))
        self.assertEqual(items["acm:us-west-1 api.demo.example"].level, rc.GREEN)
        self.assertEqual(items["iam:acc2 human CLI access key"].level, rc.GREEN)
        self.assertEqual(items["iam:acc9 legacy key"].level, rc.AMBER)                        # out of reach, due 20 d
        self.assertNotIn("github:Demo-App DEMO_ROLE", items)                                  # identifier
        self.assertNotIn("github:Demo-App DEMO_PLANNED", items)                               # planned
        titles = {f.title for f in report.findings}
        self.assertIn("Secret rotation: secretsmanager:acc2 demo/dev/overdue", titles)
        self.assertNotIn("Secret rotation: secretsmanager:acc2 demo/dev/hmac", titles)

    def test_short_interval_window(self):
        # DEMO_REPO_TOKEN (90 days) due 2026-12-09: 20 days before is green (14-day window), 9 days before amber.
        items = by_key(self.run_eval(full_inventory(), dt.date(2026, 11, 19)))
        self.assertEqual(items["github:Demo-App DEMO_REPO_TOKEN"].level, rc.GREEN)
        # demo/dev/db-password (180 days) due 2026-12-07: 18 days before is amber (30-day window).
        self.assertEqual(items["secretsmanager:acc2 demo/dev/db-password"].level, rc.AMBER)

    def test_missing_from_store(self):
        inv = full_inventory()
        del inv.github["github:Demo-App"]["DEMO_MISSING"]
        del inv.sm["demo/dev/hmac"]
        items = by_key(self.run_eval(inv))
        self.assertEqual(items["github:Demo-App DEMO_MISSING"].level, rc.RED)
        self.assertIn("missing from github:Demo-App", items["github:Demo-App DEMO_MISSING"].reasons[0])
        self.assertEqual(items["secretsmanager:acc2 demo/dev/hmac"].level, rc.RED)

    def test_unreadable_source_is_not_missing(self):
        inv = full_inventory()
        inv.sources["github:Demo-App"] = "error: GET /repos/x/actions/secrets: HTTP 403"
        report = self.run_eval(inv)
        items = by_key(report)
        self.assertEqual(items["github:Demo-App DEMO_MISSING"].level, rc.GREEN)
        coverage = [f for f in report.findings if f.key == "source github:Demo-App"]
        self.assertEqual(len(coverage), 1)
        self.assertEqual(coverage[0].level, rc.RED)
        self.assertEqual(coverage[0].title, "Secret rotation: check could not read github:Demo-App")

    def test_copy_not_updated_after_primary(self):
        inv = full_inventory()
        inv.github["github:Demo-App/dev"]["DEMO_DB_PASSWORD"] = "2026-03-01"
        item = by_key(self.run_eval(inv))["github:Demo-App/dev DEMO_DB_PASSWORD"]
        self.assertEqual(item.level, rc.RED)
        self.assertIn("copy not updated after its primary", " ".join(item.reasons))

    def test_register_claims_rotation_store_does_not_show(self):
        inv = full_inventory()
        inv.sm["demo/dev/hmac"]["current_created"] = "2026-07-07"      # older than last_rotated 2026-11-01
        item = by_key(self.run_eval(inv))["secretsmanager:acc2 demo/dev/hmac"]
        self.assertEqual(item.level, rc.RED)
        self.assertIn("never reached this store", " ".join(item.reasons))

    def test_sm_newer_version_is_not_proof_of_rotation(self):
        inv = full_inventory()
        inv.sm["demo/dev/overdue"]["current_created"] = "2026-11-20"   # a tag/host-only edit, not a rotation
        item = by_key(self.run_eval(inv))["secretsmanager:acc2 demo/dev/overdue"]
        self.assertEqual(item.level, rc.RED)
        self.assertEqual(item.last_source, "register")

    def test_newer_github_date_moves_the_due_date(self):
        inv = full_inventory()
        inv.github["github:Demo-App"]["DEMO_REPO_TOKEN"] = "2026-11-25"
        item = by_key(self.run_eval(inv))["github:Demo-App DEMO_REPO_TOKEN"]
        self.assertEqual(item.level, rc.GREEN)
        self.assertEqual(item.due, dt.date(2027, 2, 23))
        self.assertEqual(item.due_from, "store")
        self.assertTrue(any("record it" in n for n in item.notes))

    def test_retired_still_present(self):
        inv = full_inventory()
        inv.sm["demo/dev/old-thing"] = {"rotation_enabled": False, "current_created": None}
        item = by_key(self.run_eval(inv))["secretsmanager:acc2 demo/dev/old-thing"]
        self.assertEqual(item.level, rc.RED)
        self.assertIn("still exists", item.reasons[0])

    def test_retired_already_gone(self):
        inv = full_inventory()
        del inv.sm["demo/dev/to-revoke"]
        item = by_key(self.run_eval(inv))["secretsmanager:acc2 demo/dev/to-revoke"]
        self.assertEqual(item.level, rc.AMBER)
        self.assertIn("flip the row's status to deleted", item.reasons[0])

    def test_certificate_windows(self):
        inv = full_inventory()
        cert = inv.acm["us-west-1"]["api.demo.example"]
        cert["not_after"] = "2026-12-10"                                 # 10 days: not renewed
        item = by_key(self.run_eval(inv))["acm:us-west-1 api.demo.example"]
        self.assertEqual(item.level, rc.RED)
        self.assertIn("has not been renewed", item.reasons[0])
        cert["not_after"] = "2026-12-25"                                 # 25 days: amber
        self.assertEqual(by_key(self.run_eval(inv))["acm:us-west-1 api.demo.example"].level, rc.AMBER)
        cert["not_after"], cert["renewal_status"] = "2027-03-01", "FAILED"
        item = by_key(self.run_eval(inv))["acm:us-west-1 api.demo.example"]
        self.assertEqual(item.level, rc.RED)
        self.assertIn("FAILED", item.reasons[0])
        self.assertTrue(any("update expires" in n for n in item.notes))

    def test_certificate_register_fallback_and_missing(self):
        inv = full_inventory()
        inv.sources["aws:acm:us-west-1"] = "error: aws acm list-certificates: AccessDenied"
        item = by_key(self.run_eval(inv))["acm:us-west-1 api.demo.example"]
        self.assertEqual(item.expires_source, "register")              # 2026-12-08: 8 days
        self.assertEqual(item.level, rc.RED)
        inv = full_inventory()
        inv.acm["us-east-1"] = {}
        self.assertIn("missing from acm:us-east-1",
                      by_key(self.run_eval(inv))["acm:us-east-1 img.demo.example"].reasons[0])

    def test_kms_rotation_off(self):
        inv = full_inventory()
        inv.kms["alias/demo-data"]["rotation_enabled"] = False
        item = by_key(self.run_eval(inv))["kms:acc2 alias/demo-data"]
        self.assertEqual(item.level, rc.RED)
        self.assertIn("automatic key rotation is off", item.reasons)

    def test_rds_ca_mismatch(self):
        inv = full_inventory()
        inv.rds["demo-db"]["ca"] = "rds-ca-other-g9"
        item = by_key(self.run_eval(inv))["rds:demo-db server certificate rds-ca-demo-g1"]
        self.assertEqual(item.level, rc.AMBER)

    def test_iam_older_active_key(self):
        inv = full_inventory()
        inv.iam["acc2"] = ["2026-05-01", "2026-11-17"]
        item = by_key(self.run_eval(inv))["iam:acc2 human CLI access key"]
        self.assertEqual(item.level, rc.RED)
        self.assertIn("oldest active IAM access key 2026-05-01", " ".join(item.reasons))
        inv.iam["acc2"] = []
        self.assertIn("missing from iam:acc2", by_key(self.run_eval(inv))["iam:acc2 human CLI access key"].reasons[0])

    def test_cognito_two_secrets_and_date(self):
        inv = full_inventory()
        inv.cognito["demo-pool"]["demo-client"] = ["2026-10-01", "2026-11-28"]
        item = by_key(self.run_eval(inv))["cognito:demo-pool demo-client"]
        self.assertEqual(item.level, rc.AMBER)
        self.assertEqual(item.last_rotated, "2026-11-28")
        self.assertEqual(item.due, dt.date(2027, 11, 28))

    def test_domain_rdap(self):
        inv = full_inventory()
        inv.domains["demo.example"] = "2026-12-05"
        self.assertEqual(by_key(self.run_eval(inv))["domain:registrar demo.example"].level, rc.RED)
        inv.domains["demo.example"] = "error: RDAP HTTP 404"
        item = by_key(self.run_eval(inv))["domain:registrar demo.example"]
        self.assertEqual(item.level, rc.GREEN)
        self.assertEqual(item.expires_source, "register")
        self.assertTrue(any("RDAP lookup failed" in n for n in item.notes))

    def test_unregistered_names(self):
        inv = full_inventory()
        inv.sm["demo/dev/stray"] = {"rotation_enabled": False, "current_created": None}
        inv.github["github:Demo-App/dev"]["DEMO_STRAY"] = "2026-01-01"
        report = self.run_eval(inv)
        unreg = {f.key: f for f in report.findings if f.key.startswith("unregistered")}
        self.assertEqual(set(unreg), {"unregistered secretsmanager:acc2", "unregistered github:Demo-App/dev"})
        self.assertTrue(all(f.level == rc.AMBER for f in unreg.values()))
        self.assertIn("`demo/dev/stray`", unreg["unregistered secretsmanager:acc2"].body)

    def test_register_only_run(self):
        """No live source at all: register dates still produce the due findings, plus a coverage finding."""
        inv = rc.Inventory(sources={"github": "error: no GitHub inventory"})
        report = self.run_eval(inv)
        items = by_key(report)
        self.assertEqual(items["secretsmanager:acc2 demo/dev/overdue"].level, rc.RED)
        self.assertEqual(items["github:Demo-App DEMO_MISSING"].level, rc.GREEN)
        self.assertIn("source github", {f.key for f in report.findings})


class OutputTest(unittest.TestCase):
    def setUp(self):
        self.reg, self.policy = load_fixture()
        self.report = rc.evaluate(self.reg, full_inventory(), self.policy, TODAY)

    def test_due_json(self):
        doc = rc.due_json(self.report, self.policy)
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual(doc["as_of"], "2026-11-30")
        names = [r["name"] for r in doc["items"]]
        self.assertIn("demo/dev/db-password", names)
        row = next(r for r in doc["items"] if r["name"] == "DEMO_DB_PASSWORD")
        self.assertEqual((row["next_due"], row["next_due_source"]),
                         ("2026-12-07", "secretsmanager:acc2 demo/dev/db-password"))
        dues = [r["next_due"] for r in doc["items"] if r["next_due"]]
        self.assertEqual(dues, sorted(dues))
        rc.assert_publishable(json.dumps(doc), "due json")

    def test_summary(self):
        text = rc.summary_md(self.report)
        self.assertIn("### Secret rotation check (2026-11-30)", text)
        self.assertIn("| red | secretsmanager:acc2 demo/dev/overdue |", text)

    def test_issue_body_marker_and_normalisation(self):
        f = next(f for f in self.report.findings if f.key == "secretsmanager:acc2 demo/dev/overdue")
        a = rc.issue_body(f, TODAY, "https://github.example.test/run/1")
        b = rc.issue_body(f, TODAY + dt.timedelta(days=7), "https://github.example.test/run/2")
        self.assertIn(f"{rc.KEY_MARKER}secretsmanager:acc2 demo/dev/overdue -->", a)
        self.assertNotEqual(a, b)
        self.assertEqual(rc._normal(a), rc._normal(b))


class FakeGitHub:
    """A recorded-shape GitHub REST API: issues, labels, Actions secrets and environments."""

    def __init__(self, issues=None, label=True, secrets=None, envs=None, env_secrets=None, fail=None):
        self.issues = list(issues or [])
        self.label = label
        self.secrets = secrets or {}
        self.envs = envs or {}
        self.env_secrets = env_secrets or {}
        self.fail = fail or {}
        self.calls = []

    def __call__(self, method, url, body, headers):
        self.calls.append((method, url, body))
        path = url.split("api.github.com", 1)[1]
        bare = path.split("?")[0]
        for prefix, status in self.fail.items():
            if bare.startswith(prefix):
                return status, {"message": "Resource not accessible by integration"}, {}
        m = re.search(r"[?&]page=(\d+)", path)
        page = int(m.group(1)) if m else 1
        m = re.match(r"/repos/[^/]+/([^/]+)/actions/secrets$", bare)
        if m:
            return 200, {"secrets": self.secrets.get(m.group(1), []) if page == 1 else []}, {}
        m = re.match(r"/repos/[^/]+/([^/]+)/environments$", bare)
        if m:
            return 200, {"environments": [{"name": n} for n in self.envs.get(m.group(1), [])]}, {}
        m = re.match(r"/repos/[^/]+/([^/]+)/environments/([^/]+)/secrets$", bare)
        if m:
            key = (m.group(1), m.group(2))
            if key not in self.env_secrets:
                return 404, {"message": "Not Found"}, {}
            return 200, {"secrets": self.env_secrets[key] if page == 1 else []}, {}
        if bare.endswith("/labels/secret-rotation"):
            return (200 if self.label else 404), {}, {}
        if bare.endswith("/labels") and method == "POST":
            self.label = True
            return 201, {}, {}
        if bare.endswith("/issues") and method == "GET":
            return 200, (self.issues if page == 1 else []), {}
        if bare.endswith("/issues") and method == "POST":
            n = 100 + len(self.issues)
            self.issues.append({"number": n, "title": body["title"], "body": body["body"]})
            return 201, {"number": n}, {}
        m = re.match(r".*/issues/(\d+)(/comments)?$", bare)
        if m:
            return (201 if m.group(2) else 200), {}, {}
        return 404, {"message": "unexpected " + bare}, {}


class SyncIssuesTest(unittest.TestCase):
    def setUp(self):
        self.reg, self.policy = load_fixture()
        self.report = rc.evaluate(self.reg, full_inventory(), self.policy, TODAY)
        self.titles = {f.title for f in self.report.findings}

    def gh(self, fake):
        return rc.GitHub("t", transport=fake)

    def test_dry_run_writes_nothing(self):
        fake = FakeGitHub()
        log = rc.sync_issues(self.report, self.policy, self.gh(fake), "Demo-Org/Demo-Root", apply=False)
        self.assertTrue(all(m == "GET" for m, _, _ in fake.calls))
        self.assertEqual(sum(1 for line in log if line.startswith("would create")), len(self.titles))

    def test_apply_creates_edits_keeps_and_closes(self):
        overdue = next(f for f in self.report.findings if f.key == "secretsmanager:acc2 demo/dev/overdue")
        unchanged_body = rc.issue_body(overdue, TODAY - dt.timedelta(days=7), "old run")
        issues = [
            {"number": 1, "title": overdue.title, "body": unchanged_body},
            {"number": 2, "title": "Secret rotation: secretsmanager:acc2 demo/dev/db-password", "body": "old text"},
            {"number": 3, "title": "Secret rotation: secretsmanager:acc2 demo/dev/hmac", "body": "was red"},
            {"number": 4, "title": "Someone else's issue with the label", "body": ""},
            {"number": 5, "title": "Secret rotation: a pull request", "body": "", "pull_request": {}},
        ]
        fake = FakeGitHub(issues=issues, label=False)
        log = rc.sync_issues(self.report, self.policy, self.gh(fake), "Demo-Org/Demo-Root", apply=True,
                             run_url="https://github.example.test/run/9")
        writes = [(m, u.split("Demo-Root", 1)[1]) for m, u, _ in fake.calls if m != "GET"]
        self.assertIn(("POST", "/labels"), writes)
        self.assertIn("unchanged #1 [red] " + overdue.title, log)
        self.assertIn(("PATCH", "/issues/2"), writes)
        self.assertIn(("POST", "/issues/3/comments"), writes)
        close = next(b for m, u, b in fake.calls if m == "PATCH" and u.endswith("/issues/3"))
        self.assertEqual(close, {"state": "closed", "state_reason": "completed"})
        self.assertFalse(any(u.endswith(("/issues/4", "/issues/5")) for _, u, _ in fake.calls))
        created = {b["title"] for m, u, b in fake.calls if m == "POST" and u.endswith("/issues")}
        self.assertEqual(created, self.titles - {overdue.title, issues[1]["title"]})
        for m, u, b in fake.calls:
            if m == "POST" and u.endswith("/issues"):
                self.assertEqual(b["labels"], ["secret-rotation"])

    def test_write_cap(self):
        policy = rc.load_policy(_tmp(POLICY.replace("max_writes_per_run = 60", "max_writes_per_run = 2"), ".toml"))
        fake = FakeGitHub()
        log = rc.sync_issues(self.report, policy, self.gh(fake), "Demo-Org/Demo-Root", apply=True)
        self.assertEqual(sum(1 for m, u, _ in fake.calls if m == "POST" and u.endswith("/issues")), 2)
        self.assertTrue(any(line.startswith("cap: max_writes_per_run=2") for line in log))

    def test_refuses_unpublishable_body(self):
        f = self.report.findings[0]
        f.body += "\naccount 123456789012"
        with self.assertRaises(rc.CheckError):
            rc.sync_issues(self.report, self.policy, self.gh(FakeGitHub()), "Demo-Org/Demo-Root", apply=True)


class CollectGitHubTest(unittest.TestCase):
    def test_names_and_dates_only(self):
        reg, policy = load_fixture()
        fake = FakeGitHub(
            secrets={"Demo-App": [{"name": "DEMO_REPO_TOKEN", "created_at": "2026-01-01T00:00:00Z",
                                   "updated_at": "2026-09-10T08:00:00Z"}]},
            envs={"Demo-App": ["dev", "Preview"]},
            env_secrets={("Demo-App", "dev"): [{"name": "DEMO_DB_PASSWORD", "updated_at": "2026-06-11T01:00:00Z"}],
                         ("Demo-App", "Preview"): []})
        inv = rc.collect_github(reg, policy, rc.GitHub("t", transport=fake))
        self.assertEqual(inv.sources, {"github:Demo-App": "ok"})
        self.assertEqual(inv.github, {"github:Demo-App": {"DEMO_REPO_TOKEN": "2026-09-10"},
                                      "github:Demo-App/dev": {"DEMO_DB_PASSWORD": "2026-06-11"},
                                      "github:Demo-App/Preview": {}})
        self.assertTrue(all(m == "GET" for m, _, _ in fake.calls))

    def test_forbidden_is_a_source_error(self):
        reg, policy = load_fixture()
        fake = FakeGitHub(fail={"/repos/Demo-Org/Demo-App/actions/secrets": 403})
        inv = rc.collect_github(reg, policy, rc.GitHub("t", transport=fake))
        self.assertTrue(inv.sources["github:Demo-App"].startswith("error: GET /repos/Demo-Org/Demo-App/actions"))
        self.assertIn("HTTP 403", inv.sources["github:Demo-App"])

    def test_deleted_environment(self):
        reg, policy = load_fixture()
        fake = FakeGitHub(secrets={"Demo-App": []}, envs={"Demo-App": []})
        inv = rc.collect_github(reg, policy, rc.GitHub("t", transport=fake))
        self.assertEqual(inv.github["github:Demo-App/dev"], {})                  # register env, gone live
        self.assertEqual(inv.sources["github:Demo-App"], "ok")


class FakeAws:
    """Recorded AWS CLI v2 JSON answers (invented ids and dates)."""

    def __init__(self, fail=None):
        self.calls = []
        self.fail = fail or set()

    def __call__(self, argv):
        self.calls.append(argv)
        self.test_argv(argv)
        service, op = argv[1], argv[2]
        if (service, op) in self.fail:
            return 254, "", ("An error occurred (AccessDeniedException): User: arn:aws:sts::123456789012:assumed-"
                             "role/demo/x is not authorized")
        data = {
            ("secretsmanager", "list-secrets"): {"SecretList": [
                {"Name": "demo/dev/db-password", "LastChangedDate": "2026-11-20T00:00:00+00:00"},
                {"Name": "demo/dev/hmac"}, {"Name": "demo/dev/overdue"}, {"Name": "demo/dev/unknown"},
                {"Name": "demo/dev/vendor-key"}, {"Name": "demo/dev/to-revoke"}]},
            ("secretsmanager", "list-secret-version-ids"): {"Versions": [
                {"VersionId": "v-old", "VersionStages": ["AWSPREVIOUS"], "CreatedDate": "2026-01-01T00:00:00+00:00"},
                {"VersionId": "v-new", "VersionStages": ["AWSCURRENT"], "CreatedDate": 1781049600.0}]},
            ("cognito-idp", "list-user-pools"): {"UserPools": [{"Id": "us-west-1_demo", "Name": "demo-pool"}]},
            ("cognito-idp", "list-user-pool-clients"): {"UserPoolClients": [
                {"ClientId": "client-1", "ClientName": "demo-client"}, {"ClientId": "c2", "ClientName": "other"}]},
            ("cognito-idp", "list-user-pool-client-secrets"): {"ClientSecrets": [
                {"ClientSecretId": "s1", "ClientSecretValue": "leaked?", "ClientSecretCreateDate": "2026-10-01T00:00:00Z"}]},
            ("kms", "list-aliases"): {"Aliases": [{"AliasName": "alias/demo-data", "TargetKeyId": "key-1"}]},
            ("kms", "describe-key"): {"KeyMetadata": {"KeyState": "Enabled", "KeySpec": "SYMMETRIC_DEFAULT",
                                                      "KeyManager": "CUSTOMER"}},
            ("kms", "get-key-rotation-status"): {"KeyRotationEnabled": True, "NextRotationDate": "2027-10-23T00:00:00Z"},
            ("acm", "list-certificates"): {"CertificateSummaryList": [
                {"CertificateArn": "cert-old", "DomainName": "api.demo.example"},
                {"CertificateArn": "cert-new", "DomainName": "api.demo.example"},
                {"CertificateArn": "cert-x", "DomainName": "unrelated.example"},
                {"CertificateArn": "cert-img", "DomainName": "img.demo.example"}]},
            ("rds", "describe-db-instances"): {"DBInstances": [{"CACertificateIdentifier": "rds-ca-demo-g1",
                                                                "CertificateDetails": {"CAIdentifier": "rds-ca-demo-g1",
                                                                                       "ValidTill": "2027-07-07T00:00:00Z"}}]},
            ("iam", "list-users"): {"Users": [{"UserName": "person-a"}, {"UserName": "person-b"}]},
        }
        if (service, op) == ("acm", "describe-certificate"):
            arn = argv[argv.index("--certificate-arn") + 1]
            na = {"cert-old": "2026-12-01T00:00:00Z", "cert-new": "2027-01-21T00:00:00Z",
                  "cert-img": "2027-05-07T00:00:00Z"}[arn]
            return 0, json.dumps({"Certificate": {"NotAfter": na, "Status": "ISSUED", "RenewalEligibility": "ELIGIBLE",
                                                  "InUseBy": ["lb"], "RenewalSummary": {"RenewalStatus": "SUCCESS"}}}), ""
        if (service, op) == ("iam", "list-access-keys"):
            user = argv[argv.index("--user-name") + 1]
            keys = {"person-a": [{"Status": "Active", "CreateDate": "2026-11-17T00:00:00Z"},
                                 {"Status": "Inactive", "CreateDate": "2025-01-01T00:00:00Z"}], "person-b": []}[user]
            return 0, json.dumps({"AccessKeyMetadata": keys}), ""
        return 0, json.dumps(data[(service, op)]), ""

    def test_argv(self, argv):
        assert argv[0] == "aws" and (argv[1], argv[2]) in rc.AWS_CALLS, argv
        assert "--output" in argv and argv[argv.index("--output") + 1] == "json", argv


class CollectAwsTest(unittest.TestCase):
    def test_shapes(self):
        reg, policy = load_fixture()
        fake = FakeAws()
        inv = rc.collect_aws(reg, policy, rc.AwsCli(runner=fake))
        self.assertTrue(all(v == "ok" for v in inv.sources.values()), inv.sources)
        self.assertEqual(set(inv.sources), {"aws:secretsmanager", "aws:cognito", "aws:kms", "aws:acm:us-east-1",
                                            "aws:acm:us-west-1", "aws:rds", "aws:iam"})
        self.assertEqual(inv.sm["demo/dev/db-password"]["current_created"], "2026-06-10")
        self.assertIsNone(inv.sm["demo/dev/to-revoke"]["current_created"])      # retired: no version call
        self.assertEqual(inv.cognito, {"demo-pool": {"demo-client": ["2026-10-01"]}})
        self.assertNotIn("leaked?", json.dumps(inv.to_json()))
        self.assertEqual(inv.kms["alias/demo-data"]["next_rotation"], "2027-10-23")
        self.assertEqual(inv.acm["us-west-1"], {"api.demo.example": {
            "not_after": "2027-01-21", "status": "ISSUED", "renewal_status": "SUCCESS", "eligibility": "ELIGIBLE",
            "in_use": True}})
        self.assertNotIn("unrelated.example", json.dumps(inv.acm))
        self.assertEqual(inv.rds["demo-db"], {"ca": "rds-ca-demo-g1", "valid_till": "2027-07-07"})
        self.assertEqual(inv.iam, {"acc2": ["2026-11-17"]})
        self.assertNotIn("person-a", json.dumps(inv.to_json()))
        includes = next(a for a in fake.calls if a[2] == "list-certificates")
        self.assertIn("RSA_2048", includes[includes.index("--includes") + 1])
        report = rc.evaluate(reg, inv, policy, TODAY)
        self.assertEqual(by_key(report)["acm:us-west-1 api.demo.example"].level, rc.GREEN)

    def test_denied_source_is_redacted(self):
        reg, policy = load_fixture()
        inv = rc.collect_aws(reg, policy, rc.AwsCli(runner=FakeAws(fail={("kms", "list-aliases")})))
        self.assertTrue(inv.sources["aws:kms"].startswith("error: aws kms list-aliases"))
        self.assertNotIn("123456789012", inv.sources["aws:kms"])
        self.assertEqual(inv.sources["aws:cognito"], "ok")
        report = rc.evaluate(reg, inv, policy, TODAY)
        f = next(f for f in report.findings if f.key == "source aws:kms")
        rc.assert_publishable(f.title + f.body, "coverage")


class CollectRdapTest(unittest.TestCase):
    def test_expiration_event(self):
        reg, policy = load_fixture()
        seen = []

        def fetch(url, timeout):
            seen.append(url)
            return 200, {"events": [{"eventAction": "registration", "eventDate": "2020-04-04T00:00:00Z"},
                                    {"eventAction": "expiration", "eventDate": "2027-04-04T10:00:00Z"}]}
        inv = rc.collect_rdap(reg, policy, fetch)
        self.assertEqual(seen, ["https://rdap.example.test/domain/demo.example"])
        self.assertEqual(inv.domains, {"demo.example": "2027-04-04"})
        inv = rc.collect_rdap(reg, policy, lambda url, t: (404, None))
        self.assertEqual(inv.domains, {"demo.example": "error: RDAP HTTP 404"})


class CliTest(unittest.TestCase):
    def test_iam_actions(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(rc.main(["iam-actions"]), 0)
        self.assertEqual(json.loads(buf.getvalue()), sorted(set(rc.AWS_CALLS.values())))

    def test_run_register_only_dry(self):
        import contextlib
        import io
        out = Path(tempfile.mkdtemp())
        buf = io.StringIO()
        reg = _tmp(REGISTER, ".yaml")
        pol = _tmp(POLICY, ".toml")
        inv = out / "gh.json"
        inv.write_text(json.dumps({"sources": {"github:Demo-App": "ok"},
                                   "github": full_inventory().github}), encoding="utf-8")
        rc_github = rc.GitHub
        try:
            rc.GitHub = lambda token, **kw: rc_github(token, transport=FakeGitHub())
            with contextlib.redirect_stdout(buf):
                code = rc.main(["--register", str(reg), "--policy", str(pol), "run", "--github-inventory", str(inv),
                                "--json-out", str(out / "due.json"), "--summary", str(out / "s.md"),
                                "--as-of", "2026-11-30", "--repo", "Demo-Org/Demo-Root"])
        finally:
            rc.GitHub = rc_github
        self.assertEqual(code, 0)
        doc = json.loads((out / "due.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["coverage"], {"github:Demo-App": "ok"})
        self.assertIn("would create [red] Secret rotation: secretsmanager:acc2 demo/dev/overdue", buf.getvalue())

    def test_aws_unavailable_is_one_coverage_finding(self):
        import contextlib
        import io
        out = Path(tempfile.mkdtemp())
        rc_github = rc.GitHub
        try:
            rc.GitHub = lambda token, **kw: rc_github(token, transport=FakeGitHub())
            with contextlib.redirect_stdout(io.StringIO()):
                code = rc.main(["--register", str(_tmp(REGISTER, ".yaml")), "--policy", str(_tmp(POLICY, ".toml")),
                                "run", "--aws-unavailable", "role arn:aws:iam::123456789012:role/x not assumed",
                                "--json-out", str(out / "due.json"), "--as-of", "2026-11-30"])
        finally:
            rc.GitHub = rc_github
        self.assertEqual(code, 0)
        doc = json.loads((out / "due.json").read_text(encoding="utf-8"))
        self.assertTrue(doc["coverage"]["aws"].startswith("error: role <arn> not assumed"))
        self.assertIn("source aws", {f["key"] for f in doc["findings"]})

    def test_inventory_round_trip_through_gzip_base64(self):
        inv = full_inventory()
        blob = gzip.compress(json.dumps({"sources": inv.sources, "github": inv.github}).encode())
        back = rc.Inventory.from_json(json.loads(gzip.decompress(blob)))
        self.assertEqual(back.github, inv.github)


class RealRegisterTest(unittest.TestCase):
    """The real register and policy: every row evaluates, and every possible issue body is publishable."""

    def test_every_body_publishable(self):
        reg = sr.load()
        self.assertEqual(sr.validate(reg), [])
        policy = rc.load_policy()
        report = rc.evaluate(reg, rc.Inventory(), policy, dt.date(2026, 11, 30))
        self.assertGreater(len(report.items), 100)
        for item in report.items:
            item.flag(rc.RED, "forced for the publishability test")
            finding = rc._row_finding(item, policy, report.as_of)
            rc.assert_publishable(finding.title + "\n" + rc.issue_body(finding, report.as_of, ""), finding.title)
        rc.assert_publishable(json.dumps(rc.due_json(report, policy)), "due json")

    def test_known_overdue_items_show_up(self):
        """The S295 calendar's overdue items (register dates only) are red."""
        report = rc.evaluate(sr.load(), rc.Inventory(), rc.load_policy(), dt.date(2026, 11, 30))
        red = {i.entry.key for i in report.items if i.level == rc.RED}
        self.assertIn("vendor:github GitHub personal access tokens (pqnghiep1354)", red)
        self.assertIn("iam:acc1 legacy static key (acc1-legacy-default)", red)


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        import yaml
        self.text = (ROOT / ".github/workflows/secret-rotation.yml").read_text(encoding="utf-8")
        self.doc = yaml.safe_load(self.text)
        self.on = self.doc.get("on", self.doc.get(True))

    def test_weekly_never_more_than_daily(self):
        crons = [c["cron"] for c in self.on["schedule"]]
        self.assertEqual(len(crons), 1)
        minute, hour, dom, month, dow = crons[0].split()
        self.assertTrue(minute.isdigit() and hour.isdigit(), "one run per day at most")
        self.assertEqual((dom, month, dow), ("*", "*", "1"), "weekly on Monday")

    def test_shape(self):
        self.assertNotIn("pull_request_target", self.on)
        self.assertNotIn("set -x", self.text)
        self.assertEqual(self.doc["permissions"], {"contents": "read"})
        jobs = self.doc["jobs"]
        self.assertEqual(jobs["github"]["environment"], "ci-bot")
        self.assertNotIn("id-token", jobs["github"]["permissions"])
        self.assertNotIn("environment", jobs["check"], "the check job keeps the ref:refs/heads/master OIDC subject")
        self.assertEqual(jobs["check"]["permissions"], {"contents": "read", "issues": "write", "id-token": "write"})
        for job in ("github", "check"):
            self.assertIn("refs/heads/master", jobs[job]["if"])
            self.assertIn("pull_request", jobs[job]["if"])
        mint = next(s for s in jobs["github"]["steps"] if "create-github-app-token" in str(s.get("uses")))
        self.assertEqual(mint["with"]["permission-secrets"], "read")
        self.assertEqual(mint["with"]["permission-environments"], "read")
        self.assertEqual({k for k in mint["with"] if k.startswith("permission-")},
                         {"permission-secrets", "permission-environments"})
        run = next(s for s in jobs["check"]["steps"] if s.get("name") == "Check and sync the issues")["run"]
        self.assertIn("rotation_check.py run", run)
        self.assertIn("--aws-unavailable", run)
        creds = next(s for s in jobs["check"]["steps"] if s.get("id") == "aws")
        self.assertTrue(creds["continue-on-error"])
        self.assertIn("--apply", run)
        self.assertIn("inputs.apply", jobs["check"]["env"]["APPLY"])


if __name__ == "__main__":
    unittest.main()
