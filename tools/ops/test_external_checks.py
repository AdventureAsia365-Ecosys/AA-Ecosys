"""AA-1142 — tools/ops/external_checks.py without the network: the config is valid, a result is built step by step (a
DNS failure stops before TLS, a refused certificate before HTTP, a TLS-only target makes no request), the expected
statuses decide http_ok, the run has the format CIS reads, the summary table. Invented hosts only.

Run: python3 -m unittest discover -s tools/ops -p 'test_external_checks.py'
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import external_checks as ec  # noqa: E402

NOW = datetime(2026, 11, 25, 10, 0, 7, 123, tzinfo=timezone.utc)
HEALTH = {"id": "zz-api", "app": "cis", "host": "api.zz.example", "mode": "health", "path": "/health", "expect": [200]}
TLS_ONLY = {"id": "zz-auth", "app": "shared", "host": "auth.zz.example", "mode": "tls"}


def _dns_ok(host):
    return True, None


def _tls_ok(host):
    return True, "2027-01-20T00:00:00+00:00", None


class ConfigTest(unittest.TestCase):
    def test_committed_config_is_valid_and_public_hosts_only(self):
        targets = ec.load_config()
        self.assertGreaterEqual(len(targets), 5)
        for t in targets:
            self.assertTrue(t["host"].endswith(".lumiguides.it.com"), t["host"])

    def test_bad_configs_are_refused(self):
        bad = [
            {"targets": []},
            {"targets": [{**HEALTH, "id": "Bad Id"}]},
            {"targets": [HEALTH, HEALTH]},
            {"targets": [{**HEALTH, "host": "x/y"}]},
            {"targets": [{**HEALTH, "app": "nowhere"}]},
            {"targets": [{**HEALTH, "mode": "ping"}]},
            {"targets": [{**HEALTH, "path": "health"}]},
            {"targets": [{**HEALTH, "expect": [99]}]},
        ]
        for doc in bad:
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / "c.json"
                p.write_text(json.dumps(doc), encoding="utf-8")
                with self.assertRaises(ec.ConfigError, msg=doc):
                    ec.load_config(p)


class CheckTest(unittest.TestCase):
    def test_healthy_target(self):
        r = ec.check_one(HEALTH, dns=_dns_ok, tls=_tls_ok, get=lambda h, p: (200, 140, None))
        self.assertEqual((r["dns_ok"], r["tls_ok"], r["http_status"], r["http_ok"], r["latency_ms"]),
                         (True, True, 200, True, 140))
        self.assertEqual(r["url"], "https://api.zz.example/health")

    def test_unexpected_status_and_a_failed_request(self):
        r = ec.check_one(HEALTH, dns=_dns_ok, tls=_tls_ok, get=lambda h, p: (502, 90, None))
        self.assertIs(r["http_ok"], False)
        r = ec.check_one(HEALTH, dns=_dns_ok, tls=_tls_ok, get=lambda h, p: (None, 10000, "timeout: zz"))
        self.assertIsNone(r["http_ok"])
        self.assertEqual(r["error"], "timeout: zz")

    def test_dns_failure_stops_before_tls(self):
        def no_tls(host):
            raise AssertionError("TLS must not run")
        r = ec.check_one(HEALTH, dns=lambda h: (False, "gaierror: zz"), tls=no_tls, get=None)
        self.assertEqual((r["dns_ok"], r["tls_ok"], r["error"]), (False, None, "gaierror: zz"))

    def test_refused_certificate_stops_before_http(self):
        def no_get(h, p):
            raise AssertionError("HTTP must not run")
        r = ec.check_one(HEALTH, dns=_dns_ok, tls=lambda h: (False, None, "SSLCertVerificationError: zz"),
                         get=no_get)
        self.assertIs(r["tls_ok"], False)

    def test_tls_only_target_makes_no_request(self):
        def no_get(h, p):
            raise AssertionError("HTTP must not run")
        r = ec.check_one(TLS_ONLY, dns=_dns_ok, tls=_tls_ok, get=no_get)
        self.assertEqual((r["tls_ok"], r["http_status"], r["cert_not_after"]), (True, None,
                                                                                  "2027-01-20T00:00:00+00:00"))

    def test_dns_check_reports_errors(self):
        def boom(*a, **k):
            raise OSError("zz no such host")
        self.assertEqual(ec.check_dns("x.zz.example", resolve=boom), (False, "OSError: zz no such host"))
        self.assertEqual(ec.check_dns("x.zz.example", resolve=lambda *a, **k: [("x",)]), (True, None))

    def test_cert_end(self):
        self.assertEqual(ec.cert_end({"notAfter": "Jan 20 12:00:00 2027 GMT"}), "2027-01-20T12:00:00+00:00")
        self.assertIsNone(ec.cert_end({}))


class RunTest(unittest.TestCase):
    def test_run_has_the_format_cis_reads(self):
        doc = ec.run([HEALTH, TLS_ONLY], now=NOW, dns=_dns_ok, tls=_tls_ok, get=lambda h, p: (200, 120, None))
        self.assertEqual(doc["format"], 1)
        self.assertEqual(doc["checked_at"], "2026-11-25T10:00:07+00:00")
        keys = {"target", "app", "host", "url", "mode", "dns_ok", "tls_ok", "cert_not_after", "http_status", "http_ok",
                "latency_ms", "error"}
        self.assertTrue(all(set(r) == keys for r in doc["results"]))
        table = ec.summary(doc)
        self.assertIn("| api.zz.example | ok | ok | 2027-01-20 | 200 | 120 ms |", table)
        self.assertIn("| auth.zz.example | ok | ok | 2027-01-20 | – | – ms |", table)


if __name__ == "__main__":
    unittest.main()
