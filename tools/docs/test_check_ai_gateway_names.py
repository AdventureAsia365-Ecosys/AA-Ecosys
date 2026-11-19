"""Tests of check_ai_gateway_names.py (AA-1042). Root only: the AI gateway guide and the routes snapshot live in this
repo, so the test is not part of the vendored test_docs_tools.py (AA-1134: the vendored file must stay byte-identical in
AA-Booking, AA-Partner, AA-TripPlanner-Web and AA-CIS-Infra, which have no check_ai_gateway_names.py).
Run: python -m unittest discover -s tools/docs -p 'test_*.py'."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

import check_ai_gateway_names


class TempRepo(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)

    def write(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(text), encoding="utf-8")

    def run_quiet(self, fn, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return fn(*args)


class AiGatewayNamesTest(TempRepo):
    """AA-1042: the AI gateway guide's drift guard (check_ai_gateway_names.py). Invented stage, model, connection and
    secret names only."""

    SNAP = {
        "schema": "aa900-llm-routes/2",
        "routes": [{"stage": "q7_write"}, {"stage": "q7_judge"}, {"stage": "zp_compose"}],
        "models": [{"model_key": "zeta-5-5"}, {"model_key": "zeta-4-1"}, {"model_key": "omni-embed-v9"}],
        "connections": [{"connection_key": "acc8"}, {"connection_key": "zeta-direct"}],
        "deployments": [],
    }
    REGISTER = "# Secrets register\n\n| Name | App |\n|---|---|\n| `zz-llm/dev/zeta-direct` | cis |\n"

    def setUp(self) -> None:
        super().setUp()
        self.write("docs/generated/llm-routes.snapshot.json", json.dumps(self.SNAP))
        self.write("docs/security/secrets-register.md", self.REGISTER)

    def page(self, body: str, vi: str | None = None) -> None:
        self.write("docs/architecture/ai-gateway.md", body)
        self.write("docs/architecture/ai-gateway.vi.md", body if vi is None else vi)

    def messages(self) -> list[str]:
        findings, _ = check_ai_gateway_names.check(self.root)
        return [f"{f.path}:{f.line} {f.message}" for f in findings]

    def test_known_names_pass(self) -> None:
        self.page("Stage `q7_write` runs `zeta-5-5` on `zeta-direct`, then `acc8`; key `zz-llm/dev/zeta-direct`.\n"
                  "Not keys: `aws_only`, `model_first`, `shared.llm_role_config`, `zz-llm/<env>/`, `aa-x-dev-y`,\n"
                  "`/admin/ai-gateway`, `tools/x/shared/y.py`, `LLM_ROUTE_AWS_FIRST`.\n")
        findings, checked = check_ai_gateway_names.check(self.root)
        self.assertEqual(findings, [])
        self.assertEqual(checked, 10)    # 5 names per page, both pages

    def test_gone_stage_model_connection_and_secret_fail(self) -> None:
        self.page("Fine: `q7_judge`.\n", vi="Gone: `q7_atom_writer`, `zeta-9-9`, `zeta-indirect`, `acc1`,\n"
                  "`zz-llm/dev/missing-key`.\n")
        msgs = self.messages()
        self.assertEqual(len(msgs), 5, msgs)
        self.assertTrue(all(m.startswith("docs/architecture/ai-gateway.vi.md:") for m in msgs))
        self.assertIn("`q7_atom_writer` is not a stage", msgs[0])
        self.assertIn("`zeta-9-9` is neither a model nor a connection", msgs[1])
        self.assertIn("`acc1` is neither", msgs[3])
        self.assertIn("`zz-llm/dev/missing-key` has no row in docs/security/secrets-register.md", msgs[4])

    def test_code_fences_are_skipped(self) -> None:
        self.page("```text\n`q7_gone`\n```\nSee `q7_write`.\n")
        self.assertEqual(self.messages(), [])

    def test_snapshot_without_connections_fails_closed(self) -> None:
        self.write("docs/generated/llm-routes.snapshot.json",
                   json.dumps({k: v for k, v in self.SNAP.items() if k != "connections"}))
        self.page("`zeta-direct` and `q7_write`.\n")
        msgs = self.messages()
        self.assertEqual(len(msgs), 1, msgs)
        self.assertIn("no connection list", msgs[0])

    def test_missing_translation_fails(self) -> None:
        self.write("docs/architecture/ai-gateway.md", "`q7_write`\n")
        self.assertIn("the Vietnamese copy is missing", " ".join(self.messages()))

    def test_main_exit_codes(self) -> None:
        self.page("`q7_write`\n")
        self.assertEqual(self.run_quiet(check_ai_gateway_names.main, ["--root", str(self.root)]), 0)
        self.page("`q7_gone`\n")
        self.assertEqual(self.run_quiet(check_ai_gateway_names.main, ["--root", str(self.root)]), 1)


if __name__ == "__main__":
    unittest.main()
