"""Tests for report_registry.py (AA-1003 R1). Run: python -m unittest discover -s tools/docs -p 'test_*.py'."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

import report_registry as rr
from docslib import REPO_ROOT

REFERENCE = """\
# reference

### `shared.job` (table, ~1 rows)
### `gold_aa_internal.v_tour_liveness` (VIEW)
"""


def _catalog(**over) -> dict:
    report = {
        "id": "EX-04", "family": "executive", "name_en": "Scorecard", "name_vi": "Bảng chỉ số",
        "audience": "tech lead", "owner_role": "tech lead", "decision": "Is anything moving the wrong way?",
        "cadence": "daily snapshot", "schedule": "daily", "channel": "/admin/reports", "automation": "auto",
        "status": "partial", "priority": "P0", "template": None, "generator": "cis", "kpis": ["K-JOB-FAIL"],
        "sections": ["1. Tiles"],
    }
    report.update(over)
    return {"version": 1, "reports": [report]}


def _kpis(**over) -> dict:
    kpi = {"id": "K-JOB-FAIL", "version": 1, "name": "Failed jobs", "definition": "failed rows of shared.job",
           "unit": "count", "threshold": "0", "sources": ["shared.job"], "defined_in": "EX-04", "used_by": ["EX-04"]}
    kpi.update(over)
    return {"version": 1, "planned_sources": [], "kpis": [kpi]}


class RegistryCheck(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "docs/reports").mkdir(parents=True)
        (self.root / "docs/architecture").mkdir(parents=True)
        (self.root / rr.SCHEMA_REFERENCE).write_text(REFERENCE, encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.root)

    def write(self, catalog: dict, kpis: dict):
        (self.root / rr.CATALOG).write_text(yaml.safe_dump(catalog, allow_unicode=True), encoding="utf-8")
        (self.root / rr.KPIS).write_text(yaml.safe_dump(kpis, allow_unicode=True), encoding="utf-8")

    def messages(self, catalog: dict, kpis: dict) -> tuple[list[str], list[str]]:
        self.write(catalog, kpis)
        errors, warnings = rr.check(self.root)
        return [e.message for e in errors], [w.message for w in warnings]

    def test_valid_registry_passes(self):
        errors, warnings = self.messages(_catalog(), _kpis())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_unknown_kpi_reference_fails(self):
        errors, _ = self.messages(_catalog(kpis=["K-JOB-FAIL", "K-NOPE"]), _kpis())
        self.assertTrue(any("K-NOPE" in e for e in errors), errors)

    def test_used_by_must_match_the_listing_reports(self):
        errors, _ = self.messages(_catalog(kpis=[]), _kpis())
        self.assertTrue(any("used_by" in e for e in errors), errors)

    def test_bad_enum_values_fail(self):
        errors, _ = self.messages(_catalog(schedule="sometimes", priority="P9", generator="booking"),
                                  _kpis(unit="furlongs"))
        for word in ("schedule", "priority", "generator", "unit"):
            self.assertTrue(any(word in e for e in errors), (word, errors))

    def test_duplicate_report_id_fails(self):
        cat = _catalog()
        cat["reports"].append(dict(cat["reports"][0]))
        errors, _ = self.messages(cat, _kpis())
        self.assertTrue(any("listed twice" in e for e in errors), errors)

    def test_missing_template_fails(self):
        errors, _ = self.messages(_catalog(template="docs/templates/nope.md"), _kpis())
        self.assertTrue(any("template" in e for e in errors), errors)

    def test_unknown_source_fails_unless_planned(self):
        errors, _ = self.messages(_catalog(), _kpis(sources=["shared.kpi_daily"]))
        self.assertTrue(any("shared.kpi_daily" in e for e in errors), errors)
        kp = _kpis(sources=["shared.kpi_daily"])
        kp["planned_sources"] = [{"name": "shared.kpi_daily", "reason": "CIS 305"}]
        errors, _ = self.messages(_catalog(), kp)
        self.assertEqual(errors, [])

    def test_planned_source_now_live_only_warns(self):
        kp = _kpis()
        kp["planned_sources"] = [{"name": "shared.job", "reason": "old"}]
        errors, warnings = self.messages(_catalog(), kp)
        self.assertEqual(errors, [])
        self.assertTrue(any("shared.job" in w for w in warnings), warnings)

    def test_alert_takes_numbers_only(self):
        errors, _ = self.messages(_catalog(), _kpis(alert={"amber_gte": "1"}))
        self.assertTrue(any("alert" in e for e in errors), errors)

    def test_alert_refuses_an_unknown_bound(self):
        # the CIS engine only reads amber_gte / red_gte: a red_lte would silently show "ok"
        errors, _ = self.messages(_catalog(), _kpis(alert={"red_lte": 100}))
        self.assertTrue(any("alert" in e for e in errors), errors)

    def test_copy_must_be_byte_identical(self):
        self.write(_catalog(), _kpis())
        copy = self.root / "copy"
        copy.mkdir()
        shutil.copy(self.root / rr.CATALOG, copy / "catalog.yaml")
        (copy / "kpis.yaml").write_text("version: 1\n", encoding="utf-8")
        errors, _ = rr.check(self.root, copy)
        self.assertTrue(any("byte copy" in e.message for e in errors), errors)


class ImportHelpers(unittest.TestCase):
    def test_schedule_words(self):
        self.assertEqual(rr.schedule_of("daily 01:00 UTC"), "daily")
        self.assertEqual(rr.schedule_of("nightly (02:17 UTC)"), "daily")
        self.assertEqual(rr.schedule_of("on demand"), "on_demand")
        self.assertEqual(rr.schedule_of("every session close (event)"), "event")

    def test_relations_skip_contract_names(self):
        self.assertEqual(rr._sources("shared.llm_call_daily.cost_usd and crm.ops.v1 and booking.job"),
                         ["shared.llm_call_daily", "booking.job"])

    def test_unit_guess_matches_time_words_whole(self):
        self.assertEqual(rr._unit_guess("Oldest queue age", ""), "hours")
        self.assertEqual(rr._unit_guess("Time to first response", ""), "hours")
        for name in ("Cover coverage", "Overage share", "Consent coverage"):
            self.assertEqual(rr._unit_guess(name, ""), "ratio", name)
        self.assertEqual(rr._unit_guess("Average quality score", ""), "score")
        self.assertEqual(rr._unit_guess("Storage growth", ""), "count")

    def test_split_kpi_names(self):
        self.assertEqual(rr._split_kpi("K-TP-TRIPS / K-TP-INQ", "EX-04"),
                         [("K-TP-TRIPS", "TripPlanner trips started"), ("K-TP-INQ", "TripPlanner inquiries sent")])
        self.assertEqual(rr._split_kpi("Win rate", "CRM-01"), [("K-CRM01-WIN-RATE", "Win rate")])


class RepoRegistry(unittest.TestCase):
    def test_committed_registry_passes(self):
        if not (REPO_ROOT / rr.CATALOG).exists():
            self.skipTest("no registry in this checkout")
        errors, _ = rr.check(REPO_ROOT)
        self.assertEqual([e.message for e in errors], [])

    def test_snapshot_kpis_are_in_the_registry_with_their_unit(self):
        if not (REPO_ROOT / rr.KPIS).exists():
            self.skipTest("no registry in this checkout")
        kpis = {k["id"]: k for k in yaml.safe_load((REPO_ROOT / rr.KPIS).read_text(encoding="utf-8"))["kpis"]}
        for kid, spec in rr.SNAPSHOT_KPIS.items():
            self.assertIn(kid, kpis)
            self.assertEqual(kpis[kid]["unit"], spec["unit"])
            self.assertEqual(kpis[kid]["snapshot"]["job"], "kpi_snapshot_daily")
            if "definition" in spec:
                self.assertEqual(kpis[kid]["definition"], spec["definition"])


if __name__ == "__main__":
    unittest.main()
