"""Tests for vuln_triage.py (AA-1163). Run: python3 -m unittest discover -s tools/security -p 'test_*.py'.

Offline, stdlib only: the KEV/EPSS fetch and the GitHub client are injected fakes. Every package, repo, advisory and
CVE id below is invented.
"""
from __future__ import annotations

import copy
import datetime as dt
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vuln_triage as vt  # noqa: E402

HERE = Path(__file__).resolve().parent
CFG = vt.load_config(vt.DEFAULT_CONFIG)
AS_OF = dt.date(2026, 11, 21)
NOW = dt.datetime(2026, 11, 21, 12, tzinfo=dt.timezone.utc).timestamp()


def dependabot_alert(number=1, *, cve="CVE-2099-0001", ghsa="GHSA-aaaa-bbbb-cccc", severity="medium", v4=6.3,
                     v3=0.0, epss=0.003, pct=0.2, created="2026-11-01T00:00:00Z", scope="runtime",
                     manifest="web/package-lock.json", fixed="2.0.1", package="examplepkg", state="open", **extra):
    a = {
        "number": number, "state": state, "created_at": created, "html_url": f"https://example.invalid/{number}",
        "assignees": [],
        "dependency": {"package": {"ecosystem": "npm", "name": package}, "manifest_path": manifest, "scope": scope},
        "security_advisory": {
            "ghsa_id": ghsa, "cve_id": cve, "severity": severity,
            "identifiers": [{"type": "GHSA", "value": ghsa}] + ([{"type": "CVE", "value": cve}] if cve else []),
            "cvss_severities": {"cvss_v3": {"score": v3}, "cvss_v4": {"score": v4}},
            "epss": {"percentage": epss, "percentile": pct} if epss is not None else None,
        },
        "security_vulnerability": {"first_patched_version": {"identifier": fixed} if fixed else None},
    }
    a.update(extra)
    return a


def code_alert(number=1, *, rule="py/example-rule", level="high", path="app/main.py", created="2026-11-10T00:00:00Z",
               **extra):
    a = {"number": number, "state": "open", "created_at": created, "html_url": "", "assignees": [],
         "rule": {"id": rule, "security_severity_level": level, "severity": "error"},
         "most_recent_instance": {"location": {"path": path}}}
    a.update(extra)
    return a


def finding(**kw) -> vt.Finding:
    base = dict(repo="Repo-A", source="dependabot", ref="#1", package="examplepkg", location="web/package-lock.json",
                ids=["GHSA-aaaa-bbbb-cccc", "CVE-2099-0001"], severity="medium", opened=dt.date(2026, 11, 1))
    base.update(kw)
    return vt.Finding(**base)


def classify(f: vt.Finding, cfg=CFG) -> tuple[str, list[str]]:
    f.exposure = f.exposure or vt.exposure_of(f, cfg)
    return vt.classify(f, cfg)


class Parse(unittest.TestCase):
    def test_dependabot_prefers_cvss_v4_and_keeps_github_epss(self):
        [f] = vt.parse_dependabot("Repo-A", [dependabot_alert(v4=6.3, v3=7.5)])
        self.assertEqual((f.cvss, f.cvss_version), (6.3, "4.0"))
        self.assertEqual((f.epss, f.epss_percentile, f.epss_source), (0.003, 0.2, "github"))
        self.assertEqual(f.cve, "CVE-2099-0001")
        self.assertEqual(f.ids[0], "GHSA-aaaa-bbbb-cccc")
        self.assertEqual((f.fixed_in, f.opened, f.ref), ("2.0.1", dt.date(2026, 11, 1), "#1"))

    def test_dependabot_falls_back_to_v3_then_nothing(self):
        [f] = vt.parse_dependabot("Repo-A", [dependabot_alert(v4=0.0, v3=7.5)])
        self.assertEqual((f.cvss, f.cvss_version), (7.5, "3.1"))
        [g] = vt.parse_dependabot("Repo-A", [dependabot_alert(v4=0.0, v3=0.0, epss=None)])
        self.assertIsNone(g.cvss)
        self.assertIsNone(g.epss)

    def test_dependabot_skips_closed_alerts(self):
        self.assertEqual(vt.parse_dependabot("Repo-A", [dependabot_alert(state="fixed")]), [])

    def test_code_scanning(self):
        [f] = vt.parse_code_scanning("Repo-A", [code_alert(rule="js/example", level="critical", path="x/y.js")])
        self.assertEqual(f.ids, ["#1"])   # keyed by alert number, never by rule
        self.assertEqual((f.source, f.package, f.severity, f.location), ("code-scanning", "js/example", "critical",
                                                                         "x/y.js"))
        self.assertIsNone(f.cve)

    def test_trivy_prefers_v4_score(self):
        doc = {"CreatedAt": "2026-11-15T03:00:00Z", "Results": [{"Target": "image (debian 13)", "Vulnerabilities": [
            {"VulnerabilityID": "CVE-2099-0002", "PkgName": "libexample", "Severity": "HIGH", "FixedVersion": "1.2",
             "CVSS": {"nvd": {"V3Score": 7.5}, "ghsa": {"V40Score": 8.7}}}]}]}
        [f] = vt.parse_any("Repo-A", doc, AS_OF)
        self.assertEqual((f.source, f.cvss, f.cvss_version, f.severity), ("trivy", 8.7, "4.0", "high"))
        self.assertEqual((f.opened, f.fixed_in), (dt.date(2026, 11, 15), "1.2"))

    def test_sarif_reads_security_severity(self):
        doc = {"runs": [{"tool": {"driver": {"rules": [{"id": "CVE-2099-0003",
                                                         "properties": {"security-severity": "9.1"}}]}},
                         "results": [{"ruleId": "CVE-2099-0003", "locations": [
                             {"physicalLocation": {"artifactLocation": {"uri": "lib/example.so"}}}]}]}]}
        [f] = vt.parse_any("Repo-A", doc, AS_OF)
        self.assertEqual((f.source, f.cvss, f.severity, f.cve, f.opened), ("sarif", 9.1, "critical", "CVE-2099-0003",
                                                                           AS_OF))

    def test_unknown_shape_is_an_error(self):
        with self.assertRaises(ValueError):
            vt.parse_any("Repo-A", {"something": 1}, AS_OF)
        self.assertEqual(vt.parse_any("Repo-A", [], AS_OF), [])


class Rule(unittest.TestCase):
    def test_kev_is_p0(self):
        cls, why = classify(finding(cvss=3.0, kev=True))
        self.assertEqual(cls, "P0")
        self.assertIn("in CISA KEV", why)

    def test_epss_probability_is_p0(self):
        self.assertEqual(classify(finding(cvss=3.0, epss=0.12, epss_percentile=0.95))[0], "P0")
        self.assertEqual(classify(finding(cvss=3.0, epss=0.09, epss_percentile=0.5))[0], "P3")

    def test_critical_score_is_p0_only_on_internet_facing_code(self):
        self.assertEqual(classify(finding(cvss=9.3))[0], "P0")
        self.assertEqual(classify(finding(cvss=9.3, exposure="internal"))[0], "P1")

    def test_bands(self):
        self.assertEqual(classify(finding(cvss=7.0))[0], "P1")
        self.assertEqual(classify(finding(cvss=8.9))[0], "P1")
        self.assertEqual(classify(finding(cvss=6.9))[0], "P2")
        self.assertEqual(classify(finding(cvss=4.0))[0], "P2")
        self.assertEqual(classify(finding(cvss=3.9))[0], "P3")

    def test_epss_percentile_is_p1(self):
        cls, why = classify(finding(cvss=2.0, epss=0.05, epss_percentile=0.93))
        self.assertEqual(cls, "P1")
        self.assertIn("EPSS percentile 0.93", why)

    def test_severity_band_stands_in_for_a_missing_score(self):
        f = finding(severity="high")
        cls, why = classify(f)
        self.assertEqual(cls, "P1")
        self.assertEqual(f.cvss_version, "severity")
        self.assertIn("high band 7.0", why)
        self.assertEqual(classify(finding(severity="unknown"))[0], "P3")

    def test_build_only_moves_one_class_down_but_kev_stays(self):
        cls, why = classify(finding(cvss=7.5, scope="development"))
        self.assertEqual(cls, "P2")
        self.assertIn("build-only: one class down", why)
        self.assertEqual(classify(finding(cvss=2.0, kev=True, scope="development"))[0], "P0")
        self.assertEqual(classify(finding(cvss=2.0, scope="development"))[0], "P3")

    def test_thresholds_come_from_the_config(self):
        cfg = copy.deepcopy(CFG)
        cfg["rule"]["p0_epss"] = 0.01
        self.assertEqual(classify(finding(cvss=2.0, epss=0.02, epss_percentile=0.5), cfg)[0], "P0")
        cfg["rule"]["build_moves_down"] = False
        self.assertEqual(classify(finding(cvss=7.5, scope="development"), cfg)[0], "P1")

    def test_exposure_rules_first_match(self):
        self.assertEqual(vt.exposure_of(finding(location="api/tests/test_x.py", source="code-scanning"), CFG), "build")
        self.assertEqual(vt.exposure_of(finding(location=".github/workflows/ci.yml"), CFG), "internal")
        self.assertEqual(vt.exposure_of(finding(repo="AA-Ecosys", location="tools/x.py"), CFG), "build")
        self.assertEqual(vt.exposure_of(finding(repo="Repo-A", location="tools/x.py"), CFG), "internet")
        self.assertEqual(vt.exposure_of(finding(scope="development"), CFG), "build")


class Triage(unittest.TestCase):
    def run_triage(self, f: vt.Finding, register=(), env="dev"):
        vt.triage([f], CFG, list(register), AS_OF, env)
        return f

    def test_due_date_and_status(self):
        f = self.run_triage(finding(cvss=7.5, opened=dt.date(2026, 10, 1)))
        self.assertEqual((f.cls, f.due, f.status), ("P1", dt.date(2026, 10, 31), "past due"))
        f = self.run_triage(finding(cvss=7.5, opened=dt.date(2026, 10, 25)))
        self.assertEqual((f.due, f.status), (dt.date(2026, 11, 24), "due soon"))
        f = self.run_triage(finding(cvss=7.5, opened=dt.date(2026, 11, 20)))
        self.assertEqual(f.status, "open")
        self.assertEqual(f.owner, "tech lead")
        self.assertEqual(f.action, "no fix yet: exception or replace")

    def test_prod_sla(self):
        f = self.run_triage(finding(cvss=9.5, opened=dt.date(2026, 11, 20)), env="prod")
        self.assertEqual((f.cls, f.due), ("P0", dt.date(2026, 11, 23)))

    def test_p3_has_no_clock(self):
        f = self.run_triage(finding(cvss=1.0, opened=dt.date(2025, 1, 1)))
        self.assertEqual((f.cls, f.due, f.status), ("P3", None, "next triage 2026-12-01"))

    def test_active_exception_accepts_the_finding(self):
        row = exc(expires=dt.date(2026, 12, 31))
        f = self.run_triage(finding(cvss=7.5, opened=dt.date(2026, 9, 1)), [row])
        self.assertEqual((f.status, f.action), ("accepted until 2026-12-31", "exception (register)"))
        expired = exc(expires=dt.date(2026, 11, 1))
        f = self.run_triage(finding(cvss=7.5, opened=dt.date(2026, 9, 1)), [expired])
        self.assertEqual(f.status, "past due")

    def test_code_scanning_exception_accepts_one_alert_not_the_rule(self):
        one, two = vt.parse_code_scanning("Repo-A", [code_alert(1, path="app/a.py"), code_alert(2, path="app/b.py")])
        row = exc(id="#1", source="code-scanning", package="py/example-rule")
        vt.triage([one, two], CFG, [row], AS_OF, "dev")
        self.assertEqual(one.status, "accepted until 2026-12-31")
        self.assertFalse(two.status.startswith("accepted"))
        three, = vt.parse_code_scanning("Repo-A", [code_alert(3)])
        vt.triage([three], CFG, [exc(id="py/example-rule", source="code-scanning")], AS_OF, "dev")
        self.assertFalse(three.status.startswith("accepted"))   # a rule-wide row accepts nothing

    def test_alert_numbers_do_not_cross_sources(self):
        cs, = vt.parse_code_scanning("Repo-A", [code_alert(5)])
        dep = finding(ref="#5", ids=["#5"], cvss=5.0)
        vt.triage([cs, dep], CFG, [exc(id="#5", source="dependabot")], AS_OF, "dev")
        self.assertFalse(cs.status.startswith("accepted"))
        self.assertTrue(dep.status.startswith("accepted"))

    def test_actions(self):
        f = self.run_triage(finding(cvss=5.0, fixed_in="2.0.1"))
        self.assertEqual(f.action, "bump to 2.0.1")
        f = self.run_triage(finding(cvss=5.0, fixed_in=None))
        self.assertEqual(f.action, "no fix yet: exception or replace")
        f = self.run_triage(finding(source="code-scanning", location="web/tests/a.test.ts", severity="high", ids=["r"]))
        self.assertEqual(f.action, "fix or dismiss with a reason (build/test code)")

    def test_next_triage_wraps_the_year(self):
        self.assertEqual(vt.next_triage(dt.date(2026, 12, 9)), dt.date(2027, 1, 1))


def exc(**kw) -> vt.Exception_:
    base = dict(repo="Repo-A", id="GHSA-aaaa-bbbb-cccc", source="dependabot", package="examplepkg",
                expires=dt.date(2026, 12, 31), reason="Write-only use.", way_out="Replace the package.",
                approved_by="tech lead", approved_on=dt.date(2026, 11, 20))
    base.update(kw)
    return vt.Exception_(**base)


class Exceptions(unittest.TestCase):
    def test_ignore_files(self):
        pip = vt.parse_ignore_file("Repo-A", ".github/pip-audit-ignore.txt",
                                   "# header\nPYSEC-2099-1 2026-12-31 reason text\n")
        self.assertEqual([(e.source, e.id, e.expires) for e in pip], [("pip-audit", "PYSEC-2099-1",
                                                                       dt.date(2026, 12, 31))])
        trivy = vt.parse_ignore_file("Repo-A", ".trivyignore", "# why\nCVE-2099-0004 exp:2027-01-15\nCVE-2099-0005\n")
        self.assertEqual([(e.source, e.id, e.expires) for e in trivy],
                         [("trivy", "CVE-2099-0004", dt.date(2027, 1, 15)), ("trivy", "CVE-2099-0005", None)])

    def test_dismissals_only_risk_acceptance(self):
        alerts = [dependabot_alert(1, state="dismissed", dismissed_reason="tolerable_risk",
                                   dismissed_comment="exception until 2026-12-31: write-only (SEC-03)"),
                  dependabot_alert(2, ghsa="GHSA-dddd-eeee-ffff", state="dismissed", dismissed_reason="inaccurate")]
        got = vt.dismissals("Repo-A", "dependabot", alerts, CFG["exceptions"]["dependabot_reasons"])
        self.assertEqual([(e.id, e.expires) for e in got], [("GHSA-aaaa-bbbb-cccc", dt.date(2026, 12, 31))])
        cs = [code_alert(7, state="dismissed", dismissed_reason="won't fix",
                         dismissed_comment="exception until 2026-12-31: internal only (SEC-03)")]
        got = vt.dismissals("Repo-A", "code-scanning", cs, CFG["exceptions"]["code_scanning_reasons"])
        self.assertEqual([(e.id, e.expires) for e in got], [("#7", dt.date(2026, 12, 31))])

    def test_cross_check(self):
        entries = [
            vt.SourceEntry("Repo-A", "dependabot", "GHSA-aaaa-bbbb-cccc", dt.date(2026, 12, 30), "GitHub dismissal #1"),
            vt.SourceEntry("Repo-A", "trivy", "CVE-2099-0009", dt.date(2027, 1, 1), ".trivyignore"),
            vt.SourceEntry("Repo-B", "pip-audit", "PYSEC-2099-2", None, "pip-audit-ignore.txt"),
        ]
        register = [exc(), exc(repo="Repo-B", id="PYSEC-2099-2", source="pip-audit"),
                    exc(id="GHSA-old0-old0-old0", expires=dt.date(2026, 11, 1), approved_on=dt.date(2026, 10, 1)),
                    exc(id="GHSA-long-long-long", expires=dt.date(2027, 6, 1))]
        problems = vt.check_exceptions(register, entries, [], AS_OF, 90)
        texts = {(p.repo, p.id): p.text for p in problems}
        self.assertIn("register says 2026-12-31", texts[("Repo-A", "GHSA-aaaa-bbbb-cccc")])
        self.assertIn("not in the exception register", texts[("Repo-A", "CVE-2099-0009")])
        self.assertIn("carries no expiry", texts[("Repo-B", "PYSEC-2099-2")])
        msgs = [p.text for p in problems if p.id == "GHSA-old0-old0-old0"]
        self.assertTrue(any("expired on 2026-11-01" in m for m in msgs))
        self.assertTrue(any("remove the row" in m for m in msgs))
        self.assertTrue(any("more than 90 days" in p.text for p in problems if p.id == "GHSA-long-long-long"))

    def test_code_scanning_rows_name_one_alert(self):
        entries = [vt.SourceEntry("Repo-A", "code-scanning", "#3", dt.date(2026, 12, 31), "GitHub dismissal #3")]
        ok = [exc(id="#3", source="code-scanning")]
        self.assertEqual(vt.check_exceptions(ok, entries, [], AS_OF, 90), [])
        rule_row = exc(id="py/example-rule", source="code-scanning")
        problems = vt.check_exceptions([rule_row], [], [], AS_OF, 90)
        self.assertTrue(all(p.code for p in problems))
        self.assertTrue(any("not a rule" in p.text for p in problems))
        # a Dependabot row "#3" does not register the code scanning dismissal #3
        problems = vt.check_exceptions([exc(id="#3", source="dependabot")], entries, [], AS_OF, 90)
        self.assertTrue(any(p.id == "#3" and p.code and "not in the exception register" in p.text for p in problems))

    def test_clean_register(self):
        entries = [vt.SourceEntry("Repo-A", "dependabot", "GHSA-aaaa-bbbb-cccc", dt.date(2026, 12, 31), "d")]
        self.assertEqual(vt.check_exceptions([exc()], entries, [], AS_OF, 90), [])

    def test_register_file_rows_need_every_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "reg.toml"
            p.write_text('[[exception]]\nrepo = "Repo-A"\nid = "X"\nsource = "trivy"\nexpires = 2026-12-01\n')
            with self.assertRaises(ValueError):
                vt.load_register(p)
            p.write_text('[[exception]]\nrepo = "Repo-A"\nid = "X"\nsource = "trivy"\nexpires = 2026-12-01\n'
                         'reason = "r"\nway_out = "w"\napproved_by = "tech lead"\napproved_on = 2026-11-20\n')
            [row] = vt.load_register(p)
            self.assertEqual(row.expires, dt.date(2026, 12, 1))

    def test_shipped_register_parses(self):
        self.assertIsInstance(vt.load_register(vt.DEFAULT_REGISTER), list)


class Feeds(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name)
        self.calls: list[str] = []

    def tearDown(self):
        self.tmp.cleanup()

    def fetch(self, url: str) -> bytes:
        self.calls.append(url)
        if "kev" in url or "known_exploited" in url:
            return json.dumps({"catalogVersion": "2099.01.01", "count": 1,
                               "vulnerabilities": [{"cveID": "CVE-2099-0001"}]}).encode()
        cves = url.split("cve=", 1)[1].split(",")
        return json.dumps({"data": [{"cve": c, "epss": "0.2", "percentile": "0.97", "date": "2099-01-01"}
                                    for c in cves if c != "CVE-2099-0404"]}).encode()

    def test_kev_cached(self):
        ids, state = vt.load_kev(CFG, self.fetch, self.cache, NOW)
        self.assertEqual((ids, state), ({"CVE-2099-0001"}, "catalog 2099.01.01, 1 entries"))
        vt.load_kev(CFG, self.fetch, self.cache, NOW + 60)
        self.assertEqual(len(self.calls), 1)

    def test_epss_batches_and_cache(self):
        cfg = copy.deepcopy(CFG)
        cfg["feeds"]["epss_batch"] = 2
        cves = ["CVE-2099-0001", "CVE-2099-0002", "CVE-2099-0404"]
        scores, state = vt.load_epss(cfg, cves, self.fetch, self.cache, NOW)
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(scores["CVE-2099-0001"], (0.2, 0.97))
        self.assertEqual(scores["CVE-2099-0404"], (None, None))
        self.assertEqual(state, "scores of 2099-01-01")
        vt.load_epss(cfg, cves, self.fetch, self.cache, NOW + 3600)
        self.assertEqual(len(self.calls), 2)            # fresh cache: no new call
        vt.load_epss(cfg, cves, self.fetch, self.cache, NOW + 25 * 3600)
        self.assertEqual(len(self.calls), 4)            # older than cache_hours: asked again

    def test_enrich_prefers_first_over_github(self):
        f = finding(epss=0.001, epss_percentile=0.1, epss_source="github")
        vt.enrich([f], {"CVE-2099-0001"}, {"CVE-2099-0001": (0.2, 0.97)})
        self.assertEqual((f.kev, f.epss, f.epss_source), (True, 0.2, "first"))
        g = finding(source="code-scanning", ids=["py/x"])
        vt.enrich([g], {"CVE-2099-0001"}, {})
        self.assertIsNone(g.kev)


class FakeGh:
    def __init__(self, refuse=(), refuse_files=(), refuse_dismissed=()):
        self.refuse = set(refuse)
        self.refuse_files = set(refuse_files)          # repos whose exception files answer 403
        self.refuse_dismissed = set(refuse_dismissed)  # repos whose dismissed code scanning list answers 500
        self.paths: list[str] = []

    def __call__(self, path: str, raw: bool = False):
        self.paths.append(path)
        repo = path.split("/")[2]
        if repo in self.refuse and "dependabot" in path:
            raise vt.GhError("HTTP 403: Resource not accessible by integration")
        if repo in self.refuse_dismissed and "code-scanning/alerts?state=dismissed" in path:
            raise vt.GhError("gh: Server Error (HTTP 500)")
        if raw and repo in self.refuse_files:
            raise vt.GhError("gh: Resource not accessible by integration (HTTP 403)")
        if raw:
            if repo == "AA-CIS-App" and path.endswith(".trivyignore"):
                return "# why\nCVE-2099-0007 exp:2026-12-31\n"
            raise vt.GhError("HTTP 404: Not Found")
        if repo == "AA-CIS-App" and "dependabot/alerts?state=open" in path:
            return [dependabot_alert(5, v4=9.4, epss=0.5, pct=0.99)]
        if repo == "AA-Partner" and "code-scanning/alerts?state=open" in path:
            return [code_alert(3, path="api/tests/unit/test_x.py")]
        return []


class GitHub(unittest.TestCase):
    def test_reads_every_repo_and_records_refusals(self):
        gh = FakeGh(refuse={"AA-Booking"})
        findings, entries, reads = vt.read_github(CFG, gh, AS_OF)
        self.assertEqual(len(reads), 6)
        by = {r.repo: r for r in reads}
        self.assertEqual(by["AA-CIS-App"].dependabot, "1 open")
        self.assertTrue(by["AA-Booking"].dependabot.startswith("not readable: HTTP 403"))
        self.assertEqual(by["AA-Booking"].code_scanning, "0 open")
        self.assertEqual(sorted(f.repo for f in findings), ["AA-CIS-App", "AA-Partner"])
        self.assertEqual([(e.repo, e.id) for e in entries], [("AA-CIS-App", "CVE-2099-0007")])
        self.assertTrue(all("/contents/" in p or "alerts?state=" in p for p in gh.paths))
        self.assertEqual(by["AA-CIS-App"].exception_files,
                         [".github/pip-audit-ignore.txt: absent", ".trivyignore: 1 entries"])
        self.assertEqual(by["AA-CIS-App"].unreadable, [])
        self.assertEqual([n for n, _ in by["AA-Booking"].unreadable], ["dependabot alerts and dismissals"])

    def test_only_404_means_absent(self):
        self.assertEqual(vt.GhError("gh: Not Found (HTTP 404)").status, 404)
        self.assertEqual(vt.GhError("refused", 403).status, 403)
        self.assertIsNone(vt.GhError("connection reset").status)
        gh = FakeGh(refuse_files={"AA-Partner"}, refuse_dismissed={"AA-Booking"})
        _, _, reads = vt.read_github(CFG, gh, AS_OF)
        by = {r.repo: r for r in reads}
        self.assertEqual(by["AA-Partner"].exception_files[0],
                         ".github/pip-audit-ignore.txt: not readable: gh: Resource not accessible by integration "
                         "(HTTP 403)")
        self.assertEqual([n for n, _ in by["AA-Partner"].unreadable], [".github/pip-audit-ignore.txt", ".trivyignore"])
        self.assertEqual(by["AA-Booking"].code_scanning, "0 open; dismissals not readable: gh: Server Error (HTTP 500)")
        self.assertEqual([n for n, _ in by["AA-Booking"].unreadable], ["code-scanning dismissals"])
        problems = vt.unreadable_problems(reads)
        self.assertEqual(len(problems), 3)
        self.assertTrue(all("cross-check did not run" in p.text for p in problems))


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.register = self.dir / "reg.toml"
        self.register.write_text("# empty\n")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, doc) -> Path:
        p = self.dir / name
        p.write_text(json.dumps(doc))
        return p

    def run_cli(self, *args, gh=None, fetch=None):
        out = io.StringIO()
        rc = vt.run(["--register", str(self.register), "--cache-dir", str(self.dir / "cache"), "--as-of", "2026-11-21",
                     *args], gh=gh, fetch=fetch, now=NOW, stdout=out)
        return rc, out.getvalue()

    def test_offline_record_public(self):
        dep = self.write("dep.json", [dependabot_alert(1, v4=7.1, created="2026-10-01T00:00:00Z")])
        cs = self.write("cs.json", [code_alert(2, path="api/secret/handler.py", level="medium")])
        rc, text = self.run_cli("--offline", "--public", "--input", f"Repo-A={dep}", "--input", f"Repo-A={cs}")
        self.assertEqual(rc, 0)
        self.assertIn("# Vulnerability triage record 2026-11", text)
        self.assertIn("| CISA KEV | not checked (--offline) |", text)
        self.assertIn("| P1 | 30 days | 1 | 1 | 0 | 0 |", text)
        self.assertNotIn("api/secret", text)
        self.assertNotIn("py/example-rule", text)
        self.assertIn("## Code scanning (public summary)", text)
        self.assertIn("| Repo-A | P2 | internet | 1 | #2 | 2027-02-08 | 0 |", text)
        self.assertIn("Code scanning only: 1", text.split("## P2")[1].split("##")[0])
        self.assertIn("| Repo-A | dependabot | #1 | examplepkg | web/package-lock.json |", text)

    def test_record_has_front_matter_and_signoff(self):
        dep = self.write("dep.json", [dependabot_alert(1, v4=7.1, created="2026-10-01T00:00:00Z"),
                                      dependabot_alert(2, v4=5.0, ghsa="GHSA-zzzz-zzzz-zzzz", cve=None)])
        rc, text = self.run_cli("--offline", "--record", "--month", "2026-11", "--input", f"Repo-A={dep}")
        self.assertEqual(rc, 0)
        self.assertTrue(text.startswith("---\nid: SEC-03-triage-2026-11\n"))
        self.assertIn("type: report", text)
        front = text.split("---\n")[1]
        for line in front.splitlines():   # plain YAML scalars: one ": " per line, after the key
            self.assertEqual(line.count(": "), 1, line)
        self.assertIn("## Decisions and sign-off", text)
        self.assertIn("| Repo-A dependabot #1 examplepkg | P1 | 2026-10-31 | tech lead | bump to 2.0.1 | pending |", text)
        self.assertNotIn("dependabot #2 examplepkg | P2", text)
        self.assertIn("Sign-off: tech lead, date: pending.", text)

    def test_private_record_keeps_rule_and_path(self):
        cs = self.write("cs.json", [code_alert(2, path="api/secret/handler.py", level="high")])
        rc, text = self.run_cli("--offline", "--record", "--input", f"Repo-A={cs}")
        self.assertIn("| Repo-A | code-scanning | #2 | py/example-rule | api/secret/handler.py |", text)
        self.assertIn("| Repo-A code-scanning #2 py/example-rule | P1 |", text)
        rc, text = self.run_cli("--offline", "--record", "--public", "--input", f"Repo-A={cs}")
        self.assertIn("| Repo-A code scanning #2 | P1 |", text)
        self.assertNotIn("py/example-rule", text)

    def test_strict_fails_on_past_due_p1(self):
        dep = self.write("dep.json", [dependabot_alert(1, v4=7.1, created="2026-10-01T00:00:00Z")])
        rc, _ = self.run_cli("--offline", "--strict", "--input", f"Repo-A={dep}")
        self.assertEqual(rc, 1)

    def test_feeds_through_injected_fetch(self):
        dep = self.write("dep.json", [dependabot_alert(1, v4=2.0, epss=0.0001, pct=0.01)])
        calls = []

        def fetch(url):
            calls.append(url)
            if urlparse(url).hostname == "api.first.org":
                return json.dumps({"data": [{"cve": "CVE-2099-0001", "epss": "0.3", "percentile": "0.99",
                                             "date": "2026-11-20"}]}).encode()
            return json.dumps({"catalogVersion": "2026.11.20", "count": 0, "vulnerabilities": []}).encode()
        rc, text = self.run_cli("--input", f"Repo-A={dep}", fetch=fetch)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 2)
        self.assertIn("| P0 | 7 days | 1 |", text)
        self.assertIn("EPSS 0.30 >= 0.1", text)
        self.assertIn("| FIRST EPSS | scores of 2026-11-20 |", text)

    def test_feed_failure_is_recorded_not_fatal(self):
        dep = self.write("dep.json", [dependabot_alert(1)])

        def fetch(url):
            raise OSError("network down")
        rc, text = self.run_cli("--input", f"Repo-A={dep}", fetch=fetch)
        self.assertEqual(rc, 0)
        self.assertIn("not readable (OSError): KEV not checked", text)
        self.assertIn("GitHub alert values used", text)

    def test_github_mode_and_json(self):
        rc, text = self.run_cli("--github", "--offline", "--format", "json", gh=FakeGh())
        self.assertEqual(rc, 0)
        doc = json.loads(text)
        self.assertEqual(len(doc["reads"]), 6)
        cis = [f for f in doc["findings"] if f["repo"] == "AA-CIS-App"]
        self.assertEqual((cis[0]["cls"], cis[0]["kev"]), ("P0", None))
        self.assertEqual([p["id"] for p in doc["problems"]], ["CVE-2099-0007"])   # trivy ignore without a row

    def test_refused_exception_file_fails_strict(self):
        rc, text = self.run_cli("--github", "--offline", "--public", "--strict", gh=FakeGh(refuse_files={"AA-Partner"}))
        self.assertEqual(rc, 1)
        self.assertIn("| AA-Partner exception files | .github/pip-audit-ignore.txt: not readable", text)
        self.assertIn("- AA-Partner `.trivyignore`: not readable (gh: Resource not accessible by integration "
                      "(HTTP 403)): the register cross-check did not run for it", text)
        self.assertNotIn("has a matching row", text)

    def test_public_register_and_problems_hide_code_scanning_rules(self):
        cs = self.write("cs.json", [code_alert(1, path="api/secret/handler.py"), code_alert(2, path="api/other.py")])
        self.register.write_text(
            '[[exception]]\nrepo = "Repo-A"\nid = "#1"\nsource = "code-scanning"\npackage = "py/example-rule"\n'
            'expires = 2026-12-31\nreason = "Only py/example-rule in api/secret, internal."\n'
            'way_out = "Fix the handler."\n'
            'approved_by = "tech lead"\napproved_on = 2026-11-20\n'
            '[[exception]]\nrepo = "Repo-A"\nid = "py/example-rule"\nsource = "code-scanning"\n'
            'expires = 2026-12-31\nreason = "r"\nway_out = "w"\napproved_by = "tech lead"\napproved_on = 2026-11-20\n')
        rc, text = self.run_cli("--offline", "--public", "--record", "--input", f"Repo-A={cs}")
        self.assertNotIn("py/example-rule", text)
        self.assertNotIn("api/secret", text)
        self.assertIn("| Repo-A | #1 | code-scanning | 2026-12-31 | withheld (code scanning, repo members only) |",
                      text)
        self.assertIn("| Repo-A | (rule withheld) | code-scanning |", text)
        self.assertIn("- Repo-A code scanning (rule withheld): a code scanning row names one alert number", text)
        self.assertIn("- Exception Repo-A code scanning (rule withheld):", text)
        self.assertIn("| Repo-A | P1 | internet | 2 | #1, #2 |", text)   # both still counted open
        rc, text = self.run_cli("--offline", "--record", "--input", f"Repo-A={cs}")
        self.assertIn("- Repo-A `py/example-rule`: a code scanning row names one alert number", text)

    def test_bad_input_exit_2(self):
        bad = self.write("bad.json", {"nope": 1})
        rc, _ = self.run_cli("--offline", "--input", f"Repo-A={bad}")
        self.assertEqual(rc, 2)
        rc, _ = self.run_cli("--offline", "--input", "no-equals-sign")
        self.assertEqual(rc, 2)

    def test_out_file(self):
        out = self.dir / "triage" / "2026-11.md"
        rc, text = self.run_cli("--offline", "--out", str(out))
        self.assertEqual((rc, text), (0, ""))
        self.assertTrue(out.read_text().startswith("# Vulnerability triage record 2026-11"))


class Sec03MatchesConfig(unittest.TestCase):
    """The SLA table on the SEC-03 page and the config the tool reads stay the same numbers."""

    def test_sla_days(self):
        page = (vt.ROOT / "docs" / "security" / "vulnerability-management.md").read_text(encoding="utf-8")
        for cls in ("P0", "P1", "P2"):
            m = re.search(rf"^\| \*\*{cls}\*\* \|[^\n]*\| (\d+) days \| (\d+) days \|", page, re.M)
            self.assertIsNotNone(m, f"no {cls} row in SEC-03")
            self.assertEqual((int(m.group(1)), int(m.group(2))), (CFG["sla"]["dev"][cls], CFG["sla"]["prod"][cls]),
                             f"{cls}: SEC-03 and vuln_triage.toml differ")

    def test_thresholds_named_on_the_page(self):
        page = (vt.ROOT / "docs" / "security" / "vulnerability-management.md").read_text(encoding="utf-8")
        r = CFG["rule"]
        for text in (f"EPSS ≥ {r['p0_epss']:.2f}", f"CVSS ≥ {r['p0_cvss']:.1f}",
                     f"EPSS percentile ≥ {r['p1_epss_percentile']:.2f}", f"CVSS {r['p1_cvss']:.1f}",
                     f"CVSS {r['p2_cvss']:.1f}"):
            self.assertTrue(text in page, f"SEC-03 does not name {text!r} (vuln_triage.toml [rule])")


if __name__ == "__main__":
    unittest.main()
