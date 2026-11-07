"""Tests for spend_by_stage.py and cost_estimate.py (AA-1024 G18). Invented rows; no DB, no AWS.

Run: python3 -m unittest discover -s tools/llm -p 'test_*.py'
"""

from __future__ import annotations

import contextlib
import io
import unittest
from datetime import datetime, timezone

import cost_estimate as ce
import spend_by_stage as sb

NOW = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)


def row(stage, role, usd, provider="bedrock", model="lantern-model-1", calls=10, shadow=False, unpriced=0, not_ok=0):
    return {"stage": stage, "provider": provider, "model": model, "role": role, "shadow": shadow, "calls": calls,
            "usd": usd, "unpriced": unpriced, "not_ok": not_ok}


ROWS = [row("s1_generate", "writer", 2.5), row("s1_judge", "judge", 0.75, model="lantern-judge"),
        row("a2_decide", "decide", 1.2, provider="typesafe", model="jev"),
        row("seo_keywords", "data", 0.3, provider="dataforseo", model="keywords"),
        row("s1_generate", "writer", 0.25, shadow=True, model="lantern-model-2", unpriced=2)]


def out(fn, *a, **kw):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        code = fn(*a, **kw)
    return code, buf.getvalue()


class SpendTest(unittest.TestCase):
    def test_non_llm_rows_are_never_counted_as_llm(self):
        agg = sb.aggregate(ROWS)
        self.assertAlmostEqual(agg["llm"], 3.5)
        self.assertAlmostEqual(agg["non_llm"]["decide (typesafe / Jev)"], 1.2)
        self.assertAlmostEqual(agg["non_llm"]["data (DataForSEO / Geoapify)"], 0.3)
        self.assertAlmostEqual(agg["total"], 5.0)
        self.assertEqual(sb.kind("guard"), "guard (Guardrails)")
        self.assertTrue(sb.kind("mystery").startswith("other"))  # an unknown role never inflates the LLM total
        self.assertTrue(sb.kind(None).startswith("other"))

    def test_total_is_a_lower_bound_until_write_failures_are_zero(self):
        code, text = out(sb.main, {"SPEND_HOURS": "6"}, NOW, ROWS)
        self.assertEqual(code, 0)
        self.assertIn("LOWER BOUND (log-write failures not checked", text)
        self.assertIn("aws logs start-query --log-group-names /ecs/aa-cis-dev", text)
        self.assertNotIn("\n== TOTAL", text)
        code, text = out(sb.main, {"SPEND_HOURS": "6", "SPEND_WRITE_FAILURES": "3"}, NOW, ROWS)
        self.assertIn("LOWER BOUND (3 ledger writes failed", text)
        code, text = out(sb.main, {"SPEND_HOURS": "6", "SPEND_WRITE_FAILURES": "0"}, NOW, ROWS)
        self.assertIn("== TOTAL: 5.0000 USD over 50 calls", text)
        self.assertNotIn("start-query", text)

    def test_rendering_names_stage_provider_model_shadow_and_unpriced(self):
        _, text = out(sb.main, {"SPEND_FROM": "2026-11-06T00:00Z", "SPEND_TO": "2026-11-07T00:00Z",
                                "SPEND_STAGE": "s1_", "SPEND_WRITE_FAILURES": "0"}, NOW, ROWS)
        self.assertIn("2026-11-06T00:00Z .. 2026-11-07T00:00Z, stages s1_*", text)
        self.assertIn("== LLM: 3.5000 USD", text)
        self.assertIn("== non-LLM decide (typesafe / Jev): 1.2000 USD", text)
        self.assertIn("shadow 2 unpriced", text)
        self.assertIn("2 calls carry no price", text)
        self.assertIn("of which shadow calls", text)

    def test_bad_arguments(self):
        self.assertEqual(out(sb.main, {"SPEND_FROM": "2026-11-07T00:00Z", "SPEND_TO": "2026-11-06T00:00Z"}, NOW,
                             ROWS)[0], 2)
        self.assertEqual(out(sb.main, {"SPEND_WRITE_FAILURES": "-1"}, NOW, ROWS)[0], 2)
        self.assertEqual(out(sb.main, {"SPEND_HOURS": "x"}, NOW, ROWS)[0], 2)

    def test_sql_reads_no_personal_columns(self):
        for sql in (sb.SQL, ce.SQL, ce.TOURS_SQL):
            for col in ("tenant_id", "quality_signal", "request_id", "prompt_hash", "content_piece_id"):
                self.assertNotIn(col, sql)


class EstimateTest(unittest.TestCase):
    ROWS = [{"model": "lantern-model-1", "role": "writer", "calls": 30, "tours": 10, "usd": 1.5, "unpriced": 0},
            {"model": "lantern-judge", "role": "judge", "calls": 20, "tours": 9, "usd": 0.5, "unpriced": 1}]

    def test_per_tour_uses_distinct_tours_over_all_rows(self):
        code, text = out(ce.main, {"COST_STAGE": "s1_", "COST_N": "50"}, self.ROWS, 10)
        self.assertEqual(code, 0)
        self.assertIn("stage LIKE 's1_%'", text)
        self.assertIn("2.0000 USD over 10 tours (50 calls) = 0.20000 USD per tour", text)
        self.assertIn("ESTIMATE for 50 tours: 10.00 USD", text)
        self.assertIn("1 calls without a price", text)
        self.assertIn("source query: SELECT model, role", text)

    def test_per_call(self):
        _, text = out(ce.main, {"COST_STAGE": "s1_judge", "COST_N": "100", "COST_PER": "call"}, self.ROWS, 10)
        self.assertIn("ESTIMATE for 100 calls: 4.00 USD", text)
        self.assertIn("stage LIKE 's1_judge'", text)

    def test_no_basis_refuses_to_guess(self):
        code, text = out(ce.main, {"COST_STAGE": "s9_new", "COST_N": "5"}, [], 0)
        self.assertEqual(code, 3)
        self.assertIn("NO BASIS", text)
        self.assertNotIn("ESTIMATE", text)

    def test_bad_arguments(self):
        for env in ({"COST_N": "5"}, {"COST_STAGE": "s1_"}, {"COST_STAGE": "s1_", "COST_N": "5", "COST_PER": "wave"},
                    {"COST_STAGE": "s1_", "COST_N": "0"}):
            self.assertEqual(out(ce.main, env, self.ROWS, 10)[0], 2, env)


if __name__ == "__main__":
    unittest.main()
