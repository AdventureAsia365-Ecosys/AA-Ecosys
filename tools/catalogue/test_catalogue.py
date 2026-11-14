"""AA-1106 — tests of the product catalogue guard (catalogue.py) and the surface snapshot (surface.py).

Each rule is proven on a small invented repo in a temp folder: the clean fixture passes, and one missing row makes the
check fail with the line that names it. The last test runs the guard on the committed catalogue.
Run: python -m unittest discover -s tools/catalogue -p 'test_*.py'
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogue as cat_mod  # noqa: E402
import surface as surface_mod  # noqa: E402

FEATURES = {
    "format": 1,
    "apps": [
        {"id": "cis", "name": "CIS", "name_vi": "CIS", "repo": "AA-CIS-App", "kind": "system", "summary": "Content.",
         "summary_vi": "Noi dung.", "owner": "tech_lead"},
        {"id": "crm", "name": "CRM", "name_vi": "CRM", "repo": "AA-Partner", "kind": "system", "summary": "Agency.",
         "summary_vi": "Dai ly.", "owner": "tech_lead"},
    ],
    "features": [
        {"id": "CIS-F001", "app": "cis", "module": "tours", "name": "Tours", "name_vi": "Tour",
         "summary": "Tour pages.", "summary_vi": "Trang tour.", "roles": ["admin"], "status": "live", "owner": "content_lead",
         "surface": ["page:/admin/tours/**", "route:tours"],
         "conditions": {"settings": ["cis.a"], "entitlements": ["content.rewrite"], "connections": ["openai-direct"],
                        "secrets": ["aa-cis/dev/openai-key"], "tenant_kinds": ["agency"]}},
        {"id": "CRM-F001", "app": "crm", "module": "home", "name": "Home", "name_vi": "Trang chu",
         "summary": "Home page.", "summary_vi": "Trang chu.", "roles": ["owner"], "status": "live", "owner": "tech_lead",
         "surface": ["page:/home", "route:agency"], "depends_on": ["CIS-F001"], "guide": "docs/catalogue/README.md"},
    ],
    "journeys": [
        {"id": "J-01", "name": "Story", "name_vi": "Cau chuyen", "summary": "A story.", "summary_vi": "Mot cau chuyen.",
         "steps": [{"name": "One", "name_vi": "Mot", "features": ["CIS-F001", "CRM-F001"],
                    "integrations": ["INT-001"]}],
         "uat": ["CIS-01"]},
    ],
}
INTEGRATIONS = {
    "format": 1,
    "integrations": [
        {"id": "INT-001", "name": "Catalogue over HTTP", "producer": "cis", "consumers": ["crm"], "kind": "http_api",
         "contracts": [{"file": "catalog.http.v1.openapi.yaml", "version": "1"}], "auth": "M2M token",
         "cadence": "On demand", "failure": "Cached copy", "kill_switch": "Remove the scope", "personal_data": False,
         "features": ["CIS-F001", "CRM-F001"], "owner": "tech_lead", "status": "live"},
    ],
}
SURFACE = {
    "schema": 1,
    "apps": {"cis": ["route:tours", "page:/admin/tours", "page:/admin/tours/[id]"],
             "crm": ["route:agency", "page:/home"]},
    "settings": {"cis.a": {"app": "cis", "area": "content"}},
    "entitlements": {"content.rewrite": {"product": "content", "kind": "limit"}},
}
UAT = {"version": 1, "scenarios": [
    {"id": "CIS-01", "status": "live", "features": ["CIS-F001"], "story": "Tours", "app": "cis-admin"},
    {"id": "CIS-02", "status": "retired", "story": "Old", "app": "cis-admin"},
]}
LLM = {"connections": [{"connection_key": "openai-direct", "enabled": True, "kind": "openai"}]}


class Fixture:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.features = copy.deepcopy(FEATURES)
        self.integrations = copy.deepcopy(INTEGRATIONS)
        self.surface = copy.deepcopy(SURFACE)
        self.uat = copy.deepcopy(UAT)
        (self.root / "docs/contracts/samples").mkdir(parents=True)
        (self.root / "docs/contracts/catalog.http.v1.openapi.yaml").write_text("openapi: 3.1.0\n")
        (self.root / "docs/contracts/README.md").write_text("# Contracts\n")
        (self.root / "docs/contracts/samples/x.json").write_text("{}\n")
        (self.root / "docs/catalogue").mkdir(parents=True)
        (self.root / "docs/catalogue/README.md").write_text(
            "---\nid: ARCH-07-catalogue\ntitle: Catalogue\n---\n\n# C\n")
        (self.root / "docs/security").mkdir(parents=True)
        (self.root / "docs/security/secrets-register.md").write_text("| `aa-cis/dev/openai-key` | keep |\n")
        (self.root / "docs/generated").mkdir(parents=True)
        (self.root / "docs/generated/llm-routes.snapshot.json").write_text(json.dumps(LLM))
        (self.root / "tools/uat").mkdir(parents=True)

    def write(self):
        (self.root / "docs/catalogue/features.yaml").write_text(yaml.safe_dump(self.features, sort_keys=False))
        (self.root / "docs/catalogue/integrations.yaml").write_text(yaml.safe_dump(self.integrations, sort_keys=False))
        (self.root / "docs/catalogue/surface.snapshot.json").write_text(json.dumps(self.surface))
        (self.root / "tools/uat/catalogue.json").write_text(json.dumps(self.uat))
        return cat_mod.Catalogue(self.root)

    def problems(self):
        return cat_mod.check(self.write())


class CatalogueCheckTest(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.addCleanup(self.fx.tmp.cleanup)

    def assertProblem(self, needle: str):
        problems = self.fx.problems()
        self.assertTrue(any(needle in p for p in problems), f"{needle!r} not in {problems}")

    def test_clean_fixture_passes(self):
        self.assertEqual(self.fx.problems(), [])

    def test_contract_without_integration_fails(self):
        (self.fx.root / "docs/contracts/new.event.v1.json").write_text("{}\n")
        self.assertProblem("contract new.event.v1.json: no integration names it")

    def test_contract_in_rules_folder_is_covered_too(self):
        (self.fx.root / "docs/contracts/rules").mkdir()
        (self.fx.root / "docs/contracts/rules/x.rules.json").write_text("{}\n")
        self.assertProblem("contract rules/x.rules.json: no integration names it")

    def test_missing_contract_file_fails(self):
        self.fx.integrations["integrations"][0]["contracts"].append({"file": "gone.v1.json", "version": "1"})
        self.assertProblem("contract gone.v1.json does not exist")

    def test_uat_scenario_without_feature_fails(self):
        self.fx.uat["scenarios"].append({"id": "CIS-03", "status": "live", "story": "New"})
        self.assertProblem("UAT CIS-03: names no feature id")

    def test_retired_uat_scenario_needs_no_feature(self):
        self.assertFalse(any("CIS-02" in p for p in self.fx.problems()))

    def test_uat_scenario_with_unknown_feature_fails(self):
        self.fx.uat["scenarios"][0]["features"] = ["CIS-F999"]
        self.assertProblem("UAT CIS-01: feature CIS-F999 does not exist")

    def test_unknown_setting_entitlement_connection_secret_fail(self):
        cond = self.fx.features["features"][0]["conditions"]
        cond["settings"].append("cis.nope")
        cond["entitlements"].append("nope.flag")
        cond["connections"].append("nope-direct")
        cond["secrets"].append("aa-cis/dev/nope")
        problems = self.fx.problems()
        for needle in ("setting cis.nope", "entitlement nope.flag", "connection nope-direct", "secret aa-cis/dev/nope"):
            self.assertTrue(any(needle in p for p in problems), needle)

    def test_unmapped_page_fails(self):
        self.fx.surface["apps"]["crm"].append("page:/reports")
        self.assertProblem("surface crm page:/reports: maps to no feature")

    def test_unmapped_router_fails(self):
        self.fx.surface["apps"]["cis"].append("route:new_router")
        self.assertProblem("surface cis route:new_router: maps to no feature")

    def test_stale_surface_pattern_fails(self):
        self.fx.features["features"][1]["surface"].append("page:/gone")
        self.assertProblem("feature CRM-F001: surface page:/gone matches nothing")

    def test_pattern_of_another_app_does_not_count(self):
        self.fx.surface["apps"]["crm"].append("route:tours")
        self.assertProblem("surface crm route:tours: maps to no feature")

    def test_broken_references_fail(self):
        self.fx.features["features"][1]["depends_on"] = ["CIS-F404"]
        self.fx.features["journeys"][0]["steps"][0]["integrations"] = ["INT-404"]
        self.fx.integrations["integrations"][0]["features"].append("TP-F001")
        problems = self.fx.problems()
        for needle in ("depends_on CIS-F404", "integration INT-404", "feature TP-F001 does not exist"):
            self.assertTrue(any(needle in p for p in problems), needle)

    def test_shape_rules(self):
        f = self.fx.features["features"][0]
        f["id"] = "CRM-F002"
        f["status"] = "done"
        f["summary"] = "Built in AA-123."
        del self.fx.features["features"][1]["summary_vi"]
        self.fx.integrations["integrations"][0]["failure"] = "See AA-1106"
        problems = self.fx.problems()
        for needle in ("id prefix does not match app cis", "status must be one of", "feature CRM-F002: a text value",
                       "integration INT-001: a text value", "feature CRM-F001: summary_vi missing"):
            self.assertTrue(any(needle in p for p in problems), needle)

    def test_guide_must_be_a_published_staff_page(self):
        (self.fx.root / "docs/ops").mkdir()
        (self.fx.root / "docs/ops/plain.md").write_text("# No front-matter\n")
        (self.fx.root / "docs/ops/owner.md").write_text("---\nid: SEC-01\ntitle: Owner page\n---\n\n# O\n")
        guides = {"docs/ops/plain.md": "no front-matter id", "docs/ops/owner.md": "owner-only page",
                  "docs/ops/gone.md": "does not exist", "README.md": "not a docs/*.md path"}
        for guide, needle in guides.items():
            self.fx.features["features"][1]["guide"] = guide
            self.assertProblem(needle)

    def test_account_id_arn_email_fail(self):
        self.fx.features["features"][0]["summary"] = "Account 123456789012 at a@b.co arn:aws:iam::x"
        problems = " ".join(self.fx.problems())
        for needle in ("12-digit", "ARN", "e-mail"):
            self.assertIn(needle, problems)

    def test_bundle_lists_uat_and_links(self):
        bundle = cat_mod.build_bundle(self.fx.write(), sha="abc", ref="master")
        feat = {f["id"]: f for f in bundle["features"]}
        self.assertEqual(feat["CIS-F001"]["uat"], ["CIS-01"])
        self.assertEqual(feat["CIS-F001"]["summary_vi"], "Trang tour.")
        self.assertEqual(feat["CRM-F001"]["integrations"], ["INT-001"])
        self.assertEqual(bundle["settings"], {"cis.a": {"app": "cis", "area": "content"}})
        self.assertEqual(bundle["journeys"][0]["uat"], ["CIS-01"])
        self.assertEqual(bundle["source"], {"repo": "AA-Ecosys", "sha": "abc", "ref": "master"})
        self.assertEqual(cat_mod.public_problems(json.dumps(bundle)), [])

    def test_public_problems_ignores_digits_inside_a_commit_sha(self):
        self.assertEqual(cat_mod.public_problems('{"sha": "40087e38b950257287406f6463f6a91f144e1ee5"}'), [])
        self.assertTrue(cat_mod.public_problems('{"note": "account 123456789012 here"}'))

    def test_bundle_command_writes_file(self):
        self.fx.write()
        out = self.fx.root / "out"
        self.assertEqual(cat_mod.main(["bundle", "--out", str(out), "--root", str(self.fx.root)]), 0)
        self.assertEqual(json.loads((out / "catalogue.json").read_text())["format"], 1)

    def test_check_command_fails_on_problem(self):
        self.fx.uat["scenarios"].append({"id": "CIS-04", "status": "live"})
        self.fx.write()
        self.assertEqual(cat_mod.main(["check", "--root", str(self.fx.root)]), 1)


class SurfaceTest(unittest.TestCase):
    def test_page_route_drops_groups(self):
        self.assertEqual(surface_mod.page_route("."), "/")
        self.assertEqual(surface_mod.page_route("(staff)/cases/[code]"), "/cases/[code]")
        self.assertEqual(surface_mod.page_route("staff/(console)/ops"), "/staff/ops")

    def test_matches(self):
        m = cat_mod.surface_matches
        self.assertTrue(m("page:/a/**", "page:/a"))
        self.assertTrue(m("page:/a/**", "page:/a/b/c"))
        self.assertFalse(m("page:/a/**", "page:/ab"))
        self.assertTrue(m("page:/c/*", "page:/c/p"))
        self.assertFalse(m("page:/c/*", "page:/c/p/q"))

    def test_collect_and_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "apps"
            for folder in ("AA-CIS-App", "AA-Booking", "AA-Partner", "AA-TripPlanner-Web"):
                (root / folder).mkdir(parents=True)
            cis = root / "AA-CIS-App"
            (cis / "frontend/app/admin/docs").mkdir(parents=True)
            (cis / "frontend/app/admin/docs/page.tsx").write_text("export default 1")
            (cis / "api/routers").mkdir(parents=True)
            (cis / "api/routers/admin_docs.py").write_text("@router.get(\"/x\")\nasync def x(): ...\n")
            (cis / "api/routers/_helpers.py").write_text("@router.get(\"/x\")\n")
            (cis / "api/routers/jobs_repo.py").write_text("def f(): ...\n")
            (cis / "shared/settings").mkdir(parents=True)
            (cis / "shared/settings/compiled_defaults.json").write_text(json.dumps(
                {"definitions": [{"key": "cis.a", "app": "cis", "area": "content"}]}))
            (cis / "api/migrations").mkdir(parents=True)
            (cis / "api/migrations/355_x.sql").write_text(
                "INSERT INTO shared.entitlement_feature (feature_key, product, value_kind) VALUES\n"
                "    ('crm.core',  'crm', 'flag', NULL, 'The CRM');\n")
            tp = root / "AA-TripPlanner-Web"
            (tp / "frontend/app/api/trip/chat").mkdir(parents=True)
            (tp / "frontend/app/api/trip/chat/route.ts").write_text("")
            (tp / "backend/browse").mkdir(parents=True)
            (tp / "backend/browse/handler.py").write_text("")
            bk = root / "AA-Booking/backend/app/pricing"
            bk.mkdir(parents=True)
            (bk / "policy_params.py").write_text('Param(\n    "quote_validity_days",\n')
            snap = surface_mod.collect(Path(tmp))
            self.assertEqual(snap["apps"]["cis"], ["page:/admin/docs", "route:admin_docs"])
            self.assertEqual(snap["apps"]["tripplanner"], ["route:bff/trip", "route:lambda/browse"])
            self.assertIn("booking.policy.quote_validity_days", snap["settings"])
            self.assertEqual(snap["entitlements"], {"crm.core": {"product": "crm", "kind": "flag"}})
            newer = copy.deepcopy(snap)
            newer["apps"]["cis"].append("page:/admin/new")
            self.assertEqual(surface_mod.diff(snap, newer), ["cis: new page:/admin/new"])


class CommittedCatalogueTest(unittest.TestCase):
    def test_committed_catalogue_passes(self):
        problems = cat_mod.check(cat_mod.Catalogue())
        self.assertEqual(problems, [], "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
