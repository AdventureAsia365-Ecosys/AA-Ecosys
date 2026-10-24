"""Tests for check_contracts.py (AA-928). Run: python -m unittest discover -s tools/contracts -p 'test_*.py'."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

import check_contracts as cc

REAL = cc.REPO_ROOT / "docs" / "contracts"


class Policy(unittest.TestCase):
    def test_crm_ops_forbidden_keys(self) -> None:
        p = cc.POLICY["crm.ops.v1"]
        self.assertEqual(cc.key_violation(p, "trip_count"), "trip_count")
        self.assertEqual(cc.key_violation(p, "trips_open"), "trip_count")
        self.assertEqual(cc.key_violation(p, "revenue"), "revenue")
        self.assertEqual(cc.key_violation(p, "monthly_revenue_usd"), "revenue")
        self.assertIsNotNone(cc.key_violation(p, "margin_total"))
        self.assertIsNotNone(cc.key_violation(p, "pipeline_stage_counts"))
        self.assertEqual(cc.key_violation(p, "pii:contact"), "pii:")
        self.assertEqual(cc.key_violation(p, "email"), "pii-name")
        self.assertEqual(cc.key_violation(p, "owner_email"), "pii-name")
        self.assertEqual(cc.key_violation(p, "guest_phone"), "pii-name")
        self.assertIsNone(cc.key_violation(p, "seats_used"))
        self.assertIsNone(cc.key_violation(p, "holds_travellers"))

    def test_booking_supplier_net(self) -> None:
        p = cc.POLICY["booking.b2b.v1"]
        self.assertEqual(cc.key_violation(p, "supplier_net"), "supplier_net")
        self.assertEqual(cc.key_violation(p, "supplier_net_amount"), "supplier_net")
        self.assertIsNone(cc.key_violation(p, "b2b_price"))

    def test_membership_allows_online_id_only(self) -> None:
        p = cc.POLICY["tenant.membership.v1"]
        ok = {"components": {"schemas": {"I": {"properties": {"sub": {"type": "string", "x-pii": "online_id"}}}}}}
        bad = {"components": {"schemas": {"I": {"properties": {"x": {"type": "string", "x-pii": "contact"}}}}}}
        self.assertEqual(cc.scan_schema_doc("tenant.membership.v1", ok, p), [])
        self.assertTrue(cc.scan_schema_doc("tenant.membership.v1", bad, p))
        self.assertEqual(cc.key_violation(p, "crm_role"), "crm_role")
        self.assertEqual(cc.key_violation(p, "email"), "email")

    def test_x_pii_forbidden_in_no_pii_contract(self) -> None:
        doc = {"components": {"schemas": {"T": {"properties": {"note": {"type": "string", "x-pii": "free_text"}}}}}}
        self.assertTrue(cc.scan_schema_doc("crm.ops.v1", doc, cc.POLICY["crm.ops.v1"]))

    def test_payload_scan_is_recursive_and_reads_values(self) -> None:
        p = cc.POLICY["crm.ops.v1"]
        hits = cc.scan_payload(p, {"items": [{"a": {"trip_count": 1}}], "tag": "pii:contact"})
        self.assertEqual({r for r, _ in hits}, {"trip_count", "pii:"})


class Repo(unittest.TestCase):
    def test_this_repo_passes(self) -> None:
        report = cc.run(cc.REPO_ROOT)
        self.assertEqual(report.errors, [])

    def test_every_http_contract_has_a_policy(self) -> None:
        names = {cc.OPENAPI_FILE.match(p.name).group("name") for p in REAL.glob("*.openapi.yaml")}
        self.assertTrue(names)
        self.assertLessEqual(names, set(cc.POLICY))


class Mutations(unittest.TestCase):
    """Copy the real contracts into a temp root, break one thing, expect the named error."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        shutil.copytree(REAL, self.root / "docs" / "contracts")
        self.contracts = self.root / "docs" / "contracts"

    def errors(self) -> list[str]:
        return [msg for _, msg in cc.run(self.root).errors]

    def load(self, name: str) -> dict:
        return yaml.safe_load((self.contracts / f"{name}.openapi.yaml").read_text(encoding="utf-8"))

    def save(self, name: str, doc: dict) -> None:
        (self.contracts / f"{name}.openapi.yaml").write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    def test_deleting_a_required_negative_fails(self) -> None:
        (self.contracts / "samples" / "booking.b2b.v1" / "quote-with-supplier-net-invalid.json").unlink()
        self.assertTrue(any(m.startswith("S4 ") and "supplier_net" in m for m in self.errors()))

    def test_valid_sample_with_trip_count_fails(self) -> None:
        path = self.contracts / "samples" / "crm.ops.v1" / "usage-meters-valid.json"
        sample = json.loads(path.read_text(encoding="utf-8"))
        sample["payload"]["trip_count"] = 3
        path.write_text(json.dumps(sample), encoding="utf-8")
        self.assertTrue(any(m.startswith("S2 expected valid") for m in self.errors()))

    def test_policy_catches_what_a_loosened_schema_lets_through(self) -> None:
        doc = self.load("crm.ops.v1")
        doc["components"]["schemas"]["UsageMeters"]["additionalProperties"] = True
        self.save("crm.ops.v1", doc)
        errs = self.errors()
        self.assertFalse(any("usage-with-trip-count-invalid" in m for m in errs), errs)
        report = cc.run(self.root)
        self.assertTrue(any("usage-with-trip-count-invalid" in n and "schema alone would accept" in n
                            for n in report.notes))

    def test_app_copy_must_be_byte_identical(self) -> None:
        name = "catalog.http.v1.openapi.yaml"
        app = self.root / "apps" / "AA-CIS-App" / "docs" / "contracts"
        app.mkdir(parents=True)
        shutil.copyfile(self.contracts / name, app / name)
        self.assertFalse(any(m.startswith("M1 ") for m in self.errors()))
        (app / name).write_text((self.contracts / name).read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
        self.assertTrue(any(m.startswith("M1 ") for m in self.errors()))

    def test_schema_field_named_supplier_net_fails(self) -> None:
        doc = self.load("booking.b2b.v1")
        doc["components"]["schemas"]["QuoteLine"]["properties"]["supplier_net"] = {"type": "string"}
        self.save("booking.b2b.v1", doc)
        self.assertTrue(any(m.startswith("P1 ") and "supplier_net" in m for m in self.errors()))

    def test_schema_field_revenue_in_crm_ops_fails(self) -> None:
        doc = self.load("crm.ops.v1")
        doc["components"]["schemas"]["UsageMeters"]["properties"]["revenue_usd_month"] = {"type": "string"}
        self.save("crm.ops.v1", doc)
        self.assertTrue(any(m.startswith("P1 ") and "revenue" in m for m in self.errors()))

    def test_broken_ref_fails(self) -> None:
        doc = self.load("catalog.http.v1")
        doc["components"]["schemas"]["Tour"]["properties"]["facets"] = {"$ref": "#/components/schemas/Nope"}
        self.save("catalog.http.v1", doc)
        self.assertTrue(any(m.startswith("O4 ") for m in self.errors()))

    def test_duplicate_operation_id_fails(self) -> None:
        doc = self.load("tenant.membership.v1")
        doc["paths"]["/events"]["get"]["operationId"] = "findMemberships"
        self.save("tenant.membership.v1", doc)
        self.assertTrue(any(m.startswith("O5 ") for m in self.errors()))

    def test_undeclared_scope_fails(self) -> None:
        doc = self.load("booking.b2b.v1")
        doc["paths"]["/quotes"]["post"]["security"] = [{"m2m": ["booking.b2b/everything"]}]
        self.save("booking.b2b.v1", doc)
        self.assertTrue(any(m.startswith("O6 ") for m in self.errors()))

    def test_unlisted_contract_fails(self) -> None:
        readme = self.contracts / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8").replace("crm.ops.v1.openapi.yaml", "x"),
                          encoding="utf-8")
        self.assertTrue(any(m.startswith("R1 ") for m in self.errors()))

    def test_contract_without_policy_fails(self) -> None:
        doc = self.load("catalog.http.v1")
        doc["info"]["x-aa-contract"] = "new.thing.v1"
        (self.contracts / "new.thing.v1.openapi.yaml").write_text(yaml.safe_dump(doc), encoding="utf-8")
        readme = self.contracts / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\n`new.thing.v1.openapi.yaml`\n", encoding="utf-8")
        self.assertTrue(any(m.startswith("P1 no field policy") for m in self.errors()))


if __name__ == "__main__":
    unittest.main()


class WriteOnlyPiiFieldTest(unittest.TestCase):
    """AA-941: crm.ops.v1 may carry exactly one personal-data field, write-only and tagged, by schema + name."""

    P = cc.POLICY["crm.ops.v1"]

    @staticmethod
    def doc(schema: str, spec: dict) -> dict:
        return {"components": {"schemas": {schema: {"type": "object", "required": ["owner_email"],
                                                    "properties": {"owner_email": spec}}}}}

    def test_the_named_field_tagged_and_write_only_passes(self):
        ok = self.doc("OwnerInviteRequest", {"type": "string", "writeOnly": True, "x-pii": "contact"})
        self.assertEqual(cc.scan_schema_doc("crm.ops.v1", ok, self.P), [])

    def test_untagged_or_readable_or_other_class_fails(self):
        for spec in ({"type": "string", "writeOnly": True}, {"type": "string", "x-pii": "contact"},
                     {"type": "string", "writeOnly": True, "x-pii": "identity"}):
            self.assertTrue(cc.scan_schema_doc("crm.ops.v1", self.doc("OwnerInviteRequest", spec), self.P), spec)

    def test_the_same_field_in_another_schema_fails(self):
        bad = self.doc("TenantSummary", {"type": "string", "writeOnly": True, "x-pii": "contact"})
        self.assertTrue(cc.scan_schema_doc("crm.ops.v1", bad, self.P))

    def test_payload_scan_accepts_it_only_at_the_top_of_that_schema(self):
        self.assertEqual(cc.scan_payload(self.P, {"owner_email": "a@b.example"}, "OwnerInviteRequest"), [])
        self.assertTrue(cc.scan_payload(self.P, {"owner_email": "a@b.example"}, "TenantSummary"))
        self.assertTrue(cc.scan_payload(self.P, {"x": {"owner_email": "a@b.example"}}, "OwnerInviteRequest"))


class JsonSchemaContractTest(unittest.TestCase):
    """AA-835 / AA-908: JSON Schema contracts get the field policy of their major and samples, like HTTP contracts."""

    SUPPLY = cc.POLICY["supply.hotel.v1"]
    INQUIRY = cc.POLICY["inquiry.submitted.v1"]

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        shutil.copytree(REAL, self.root / "docs" / "contracts")
        self.contracts = self.root / "docs" / "contracts"

    def errors(self) -> list[str]:
        return [msg for _, msg in cc.run(self.root).errors]

    def test_policy_name_is_the_major(self):
        self.assertEqual(cc.policy_name("supply.hotel.v1"), "supply.hotel.v1")
        self.assertEqual(cc.policy_name("supply.hotel.v1.1"), "supply.hotel.v1")
        self.assertEqual(cc.policy_name("inquiry.submitted.v1.4"), "inquiry.submitted.v1")
        self.assertEqual(cc.policy_name("crm.ops.v1"), "crm.ops.v1")

    def test_supply_forbids_commercial_fields_and_urls(self):
        for key, rule in (("supplier_id", "supplier_id"), ("net_amount", "net_amount"),
                          ("internal_notes", "internal_notes"), ("url", "url"), ("links", "links"),
                          ("reservation_email", "pii-name"), ("front_desk_phone", "pii-name")):
            self.assertEqual(cc.key_violation(self.SUPPLY, key), rule, key)
        for key in ("supplier_name", "room_rate", "rate_plan", "margin_pct", "notes", "photo_url", "net",
                    "unit_price", "cost"):
            self.assertIsNotNone(cc.key_violation(self.SUPPLY, key), key)
        for key in ("name", "address", "star_rating", "amenities", "check_in_time", "media_id", "usage_rights",
                    "contract", "supply_version", "working_title", "inclusions"):
            self.assertIsNone(cc.key_violation(self.SUPPLY, key), key)

    def test_inquiry_carries_contact_but_never_a_token(self):
        self.assertEqual(cc.key_violation(self.INQUIRY, "access_token"), "access_token")
        self.assertIsNotNone(cc.key_violation(self.INQUIRY, "session_token"))
        self.assertIsNotNone(cc.key_violation(self.INQUIRY, "password"))
        for key in ("email", "phone", "name", "identity", "iss", "sub", "idempotency_key", "verified"):
            self.assertIsNone(cc.key_violation(self.INQUIRY, key), key)

    def test_every_new_json_contract_has_a_policy_and_the_exempt_list_is_current(self):
        stems = {p.stem for p in REAL.glob("*.json")}
        self.assertLessEqual(cc.JSON_PRE_CHECKER, stems, "JSON_PRE_CHECKER names a file that no longer exists")
        for stem in stems - cc.JSON_PRE_CHECKER:
            self.assertIn(cc.policy_name(stem), cc.POLICY, stem)

    def test_new_json_contract_without_policy_fails(self):
        (self.contracts / "new.thing.v1.json").write_text(
            (self.contracts / "supply.hotel.v1.json").read_text(encoding="utf-8"), encoding="utf-8")
        readme = self.contracts / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\n`new.thing.v1.json`\n", encoding="utf-8")
        errs = self.errors()
        self.assertTrue(any(m.startswith("P1 no field policy for new.thing.v1") for m in errs), errs)
        self.assertTrue(any(m.startswith("S4 new.thing.v1 has no valid sample") for m in errs), errs)

    def test_new_minor_of_an_old_family_needs_samples(self):
        src = self.contracts / "catalog.tour.v1.3.json"
        (self.contracts / "catalog.tour.v1.9.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        readme = self.contracts / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\n`catalog.tour.v1.9.json`\n", encoding="utf-8")
        errs = self.errors()
        self.assertTrue(any(m.startswith("P1 no field policy for catalog.tour.v1") for m in errs), errs)
        self.assertFalse(any("catalog.tour.v1.3" in m for m in errs), errs)

    def test_schema_field_supplier_id_in_supply_fails(self):
        path = self.contracts / "supply.hotel.v1.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        doc["$defs"]["HotelFacts"]["properties"]["supplier_id"] = {"type": "string"}
        path.write_text(json.dumps(doc), encoding="utf-8")
        self.assertTrue(any(m.startswith("P1 ") and "supplier_id" in m for m in self.errors()))

    def test_deleting_a_required_supply_negative_fails(self):
        (self.contracts / "samples" / "supply.service.v1" / "service-with-free-photo-url-invalid.json").unlink()
        self.assertTrue(any(m.startswith("S4 ") and "supply.service.v1" in m and "'url'" in m
                            for m in self.errors()))

    def test_json_sample_must_not_name_a_component_schema(self):
        path = self.contracts / "samples" / "supply.hotel.v1" / "hotel-upsert-valid.json"
        sample = json.loads(path.read_text(encoding="utf-8"))
        sample["schema"] = "HotelFacts"
        path.write_text(json.dumps(sample), encoding="utf-8")
        self.assertTrue(any(m.startswith("S1 supply.hotel.v1 is a JSON Schema contract") for m in self.errors()))

    def test_verified_without_identity_is_rejected_by_the_v1_4_schema(self):
        doc = json.loads((REAL / "inquiry.submitted.v1.4.json").read_text(encoding="utf-8"))
        sample = json.loads((REAL / "samples" / "inquiry.submitted.v1.4" / "signed-in-traveller-valid.json")
                            .read_text(encoding="utf-8"))["payload"]
        validator = cc.Draft202012Validator(doc)
        self.assertEqual(list(validator.iter_errors(sample)), [])
        sample["customer"]["identity"] = None
        self.assertTrue(list(validator.iter_errors(sample)))
        sample["customer"]["verified"] = False
        self.assertEqual(list(validator.iter_errors(sample)), [])
