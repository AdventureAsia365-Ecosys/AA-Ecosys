"""Unit tests for the backtick name checks (AA-1132 A7): tools/docs/check_code_refs.py.

Run: python -m unittest tools/docs/test_check_code_refs.py
Fixtures are an invented repo (inventory, schema reference, surface and facts snapshots); no network, no git needed.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_code_refs as c  # noqa: E402

INVENTORY = """# Resource inventory

## river

| Type | Name | Address |
|---|---|---|
| `aws_ecs_service` | aa-cis-dev-otter | `module.environment.aws_ecs_service.otter` |
| `aws_kms_key` | river-data | `module.environment.aws_kms_key.river_data` |
| `aws_ecs_service` | aa-crm-dev-heron | `module.environment.aws_ecs_service.staff_web["heron"]` |

Counted only: `aws_route53_record` 3, `random_password` 2.
"""

SCHEMA_REF = """# Ref

### `crm.pond_flag` (table)
- grant `crm_reader`: SELECT
"""

FACTS = {
    "migrations": {"as_of": "2026-01-02", "owners": [{"owner": "CIS", "latest": "120"},
                                                     {"owner": "Booking", "latest": "bk-010"}]},
    "repos": {
        "job_kinds": {"AA-Booking": [{"kind": "bk_reed_sweep"}], "AA-Partner": [{"kind": "crm_reed_pull"}],
                      "AA-TripPlanner-Web": [{"kind": "tp_reed_trim"}]},
        "workflows": {"AA-CIS-App": ["ci.yml", "deploy-dev.yml"]},
    },
}

SURFACE = {"settings": {"cis.river.max_days": {"app": "cis"}}}


class Repo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.put(c.INVENTORY, INVENTORY)
        self.put(c.SCHEMA_REF, SCHEMA_REF)
        self.put(c.SNAPSHOT, json.dumps(FACTS))
        self.put(c.SURFACE, json.dumps(SURFACE))
        self.put("docs/ops/real.md", "# Real\n")
        self.put("tools/docs/x.py", "")
        self.put(".github/workflows/docs-lint.yml", "name: x\n")
        self.src = c.Sources(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def put(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def rules(self, text: str, rules=c.RULES) -> list[tuple[str, int]]:
        return [(f.kind, f.line) for f in c.check_text("docs/x.md", text, self.src, rules)]


class PathRule(Repo):
    def test_missing_root_path_is_found(self):
        self.assertEqual(self.rules("See `docs/ops/real.md` and `docs/ops/gone.md`.\n"), [("path", 1)])

    def test_line_suffix_anchor_and_folder_are_accepted(self):
        self.assertEqual(self.rules("`docs/ops/real.md:12` `docs/ops/real.md#top` `docs/ops/` `tools/docs/x.py:3-9`\n"),
                         [])

    def test_other_repo_context_placeholders_and_foreign_tools_are_skipped(self):
        text = ("AA-Booking `docs/ops/gone.md`\n`docs/<area>/x.md` `docs/*.md` `docs/sessions/YYYY-MM-DD.md`\n"
                "`tools/terraform/plan_guard.py`\n`.github/workflows/deploy-dev.yml`\n")
        self.assertEqual(self.rules(text), [])

    def test_fenced_code_is_not_a_path_and_ignore_marker_skips(self):
        self.assertEqual(self.rules("```bash\ncat docs/ops/gone.md\n```\n`docs/ops/gone.md` docs-lint: ignore\n"), [])


class TerraformRule(Repo):
    def test_addresses(self):
        text = ("```bash\nterraform plan -target=module.environment.aws_kms_key.river_data\n"
                "terraform plan -target=aws_kms_key.river_data\n"
                "terraform apply -target='module.environment.aws_ecs_service.staff_web[\"heron\"]'\n"
                "terraform apply -target=module.environment.aws_ecs_service.staff_web\n"
                "terraform apply -target=module.environment\n"
                "terraform apply -replace=module.environment.random_password.anything\n"
                "terraform apply -target=aws_route53_record.db\n"
                "terraform -chdir=accounts/lake plan -target=aws_kms_key.elsewhere\n```\n")
        self.assertEqual(self.rules(text, ("tf-address",)), [("tf-address", 3)])

    def test_inline_address(self):
        self.assertEqual(self.rules("run `-replace=module.environment.aws_kms_key.gone`\n", ("tf-address",)),
                         [("tf-address", 1)])

    def test_resource_type(self):
        self.assertEqual(c.resource_type('module.a.module.b.aws_s3_bucket.x["k"]'), "aws_s3_bucket")
        self.assertEqual(c.resource_type("data.aws_iam_policy_document.p"), "aws_iam_policy_document")
        self.assertIsNone(c.resource_type("module.environment"))


class NameRules(Repo):
    def test_service(self):
        text = "`aa-cis-dev-otter` `aa-cis-dev-badger`\nThe `aa-crm-dev-portal` service was retired.\n"
        self.assertEqual(self.rules(text, ("service",)), [("service", 1)])

    def test_job_kind_needs_the_word_kind_and_is_not_a_db_name(self):
        text = ("kinds: `bk_reed_sweep`, `bk_reed_gone`, `tp_reed_trim`\n"
                "the stage `tp_compose` runs\nkind of role `crm_reader`\nretired kind `bk_old_pull`\n")
        self.assertEqual(self.rules(text, ("job-kind",)), [("job-kind", 1)])

    def test_setting(self):
        text = ("`cis.river.max_days` `cis.river.min_days` `crm.pond_flag.note` `crm.ops.v1` `booking.b2b.v1.openapi.yaml`"
                " `tripplanner.example.it.com`\n")
        self.assertEqual(self.rules(text, ("setting",)), [("setting", 1)])

    def test_migration(self):
        text = "`bk-010` `bk-011` `120_river.sql` `121_river.sql` `crm-999`\n"
        self.assertEqual(self.rules(text, ("migration",)), [("migration", 1), ("migration", 1)])

    def test_workflow(self):
        text = ("`ci.yml` `docs-lint.yml` `gone.yml` `owners.yaml` `.github/workflows/gone2.yml` `db/x.yml`\n"
                "`vercel-deploy.yml` was deleted\n")
        self.assertEqual(self.rules(text, ("workflow",)), [("workflow", 1), ("workflow", 1)])


class Cli(Repo):
    def test_strict_rules_and_exit_codes(self):
        self.put("docs/page.md", "# P\n\n`docs/ops/gone.md`\n\n```bash\nterraform plan -target=aws_kms_key.gone\n```\n")
        args = ["--root", str(self.root), "docs/page.md"]
        self.assertEqual(c.main(args), 0)                                     # warnings only
        self.assertEqual(c.main(args + ["--strict-rules", "path"]), 1)
        self.assertEqual(c.main(args + ["--strict-rules", "tf-address"]), 1)
        self.assertEqual(c.main(args + ["--only", "path", "--strict-rules", "tf-address"]), 0)
        self.assertEqual(c.main(args + ["--strict"]), 1)

    def test_generated_pages_are_skipped(self):
        self.put("docs/gen.md", "---\ngenerated: true\n---\n`docs/ops/gone.md`\n")
        self.assertEqual(c.run(self.root, ["docs/gen.md"]), [])


if __name__ == "__main__":
    unittest.main()
