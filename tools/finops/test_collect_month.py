"""Run: python3 -m unittest discover -s tools/finops -p 'test_*.py' (from the repo root). Fake DB, no AWS call."""
import asyncio
import io
import json
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest import mock

import collect_month as c
import monthly_cost_report as m

REPO = Path(__file__).resolve().parents[2]


class FakeDB:
    """Answers fetch() by the SQL constant it gets; records every call."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    async def fetch(self, sql, *args):
        self.calls.append((sql, args))
        for key, value in self.answers.items():
            if sql is key:
                return value(*args) if callable(value) else value
        raise AssertionError("unexpected SQL")


class MonthTest(unittest.TestCase):
    def test_default_is_the_three_whole_months_before(self):
        self.assertEqual(c.default_months(date(2099, 11, 1)), ["2099-08", "2099-09", "2099-10"])
        self.assertEqual(c.default_months(date(2099, 2, 14)), ["2098-11", "2098-12", "2099-01"])

    def test_parse_months(self):
        self.assertEqual(c.parse_months(" 2099-09, 2099-08 ,2099-09", date(2099, 11, 1)), ["2099-08", "2099-09"])
        self.assertEqual(c.parse_months("", date(2099, 11, 1)), ["2099-08", "2099-09", "2099-10"])
        with self.assertRaises(SystemExit):
            c.parse_months("2099-12", date(2099, 11, 1))
        with self.assertRaises(SystemExit):
            c.parse_months("2099-13", date(2099, 11, 1))

    def test_window_ends_tomorrow_for_the_current_month(self):
        self.assertEqual(c.window("2099-10", date(2099, 11, 3)), (date(2099, 10, 1), date(2099, 11, 1)))
        self.assertEqual(c.window("2099-12", date(2099, 12, 9)), (date(2099, 12, 1), date(2099, 12, 10)))
        self.assertEqual(c.next_month(date(2099, 12, 1)), date(2100, 1, 1))

    def test_scrub_drops_account_ids_at_any_depth(self):
        got = c.scrub({"aws": {"account_id": "x", "total_usd": 1}, "l": [{"account_id": "y", "k": 2}]})
        self.assertEqual(got, {"aws": {"total_usd": 1}, "l": [{"k": 2}]})


class CollectTest(unittest.TestCase):
    def test_cis_reads_cost_ledger_and_units_per_month(self):
        db = FakeDB({
            c.PUBLISHED_TOURS_SQL: [{"published_tours": 7, "published_tours_live": Decimal(30)}],
            c.LLM_BY_STAGE_SQL: [{"app": "cis", "stage": "s1_rewrite", "role": "writer", "account": "acc3",
                                  "calls": 3, "cost_usd": Decimal("1.2500")}],
        })
        seen = []

        async def cost_fn(pool, month, *, refresh_if_stale):
            seen.append((month, refresh_if_stale))
            return {"month": month, "apps": [], "totals": {}, "refresh": {"stale": False}}

        out = asyncio.run(c.collect_cis(db, ["2099-09", "2099-10"], date(2099, 11, 2), cost_fn=cost_fn))
        self.assertEqual(seen, [("2099-09", False), ("2099-10", False)])
        self.assertEqual(out["2099-10"]["units"], {"published_tours": 7, "published_tours_live": 30})
        self.assertEqual(out["2099-10"]["llm_by_stage"][0]["cost_usd"], 1.25)
        self.assertEqual(out["2099-10"]["period_end_exclusive"], "2099-11-01")
        self.assertEqual(db.calls[0][1], (date(2099, 9, 1), date(2099, 10, 1)))

    def test_refresh_only_for_a_stale_month_and_only_when_asked(self):
        db = FakeDB({c.PUBLISHED_TOURS_SQL: [{"published_tours": 0, "published_tours_live": 0}],
                     c.LLM_BY_STAGE_SQL: []})
        state = {"stale": True}

        async def cost_fn(pool, month, *, refresh_if_stale):
            return {"month": month, "apps": [], "totals": {}, "refresh": {"stale": state["stale"]}}

        refreshed = []

        async def refresh_fn(pool, start, end):
            refreshed.append((start, end))
            state["stale"] = False
            return {"row_count": 4}

        out = asyncio.run(c.collect_cis(db, ["2099-10"], date(2099, 11, 3), cost_fn=cost_fn, refresh_fn=refresh_fn))
        self.assertEqual(refreshed, [(date(2099, 10, 1), date(2099, 11, 1))])
        self.assertEqual(out["2099-10"]["refreshed"], {"row_count": 4})
        self.assertFalse(out["2099-10"]["platform_cost"]["refresh"]["stale"])
        state["stale"] = True
        out = asyncio.run(c.collect_cis(db, ["2099-10"], date(2099, 11, 3), cost_fn=cost_fn))
        self.assertIsNone(out["2099-10"]["refreshed"])

    def test_booking_counts_confirmed_statuses(self):
        db = FakeDB({c.TRIP_CASES_SQL: [{"trip_cases": 5, "bookings_confirmed": 2}]})
        out = asyncio.run(c.collect_booking(db, ["2099-10"], date(2099, 11, 3)))
        self.assertEqual(out, {"2099-10": {"units": {"trip_cases": 5, "bookings_confirmed": 2}}})
        self.assertIn("paid", db.calls[0][1][2])
        self.assertNotIn("cancelled", db.calls[0][1][2])

    def test_crm_sums_its_gateway_rollup(self):
        db = FakeDB({c.CRM_LLM_SQL: [{"stage": "crm_a", "model": "m1", "calls": 2, "cost_usd": Decimal("0.5")},
                                     {"stage": "crm_b", "model": "m2", "calls": 1, "cost_usd": Decimal("0.25")}]})
        out = asyncio.run(c.collect_crm(db, ["2099-10"], date(2099, 11, 3)))
        self.assertEqual(out["2099-10"]["crm_llm"]["calls"], 3)
        self.assertEqual(out["2099-10"]["crm_llm"]["cost_usd"], 0.75)

    def test_main_prints_one_bundle_line_the_report_reads(self):
        fake = {"kind": "finops_bundle", "version": 1, "part": "booking", "generated_at": "x",
                "months": {"2099-10": {"units": {"trip_cases": 1, "bookings_confirmed": 0}}}}

        async def fake_run(part, months, refresh, now):
            self.assertEqual((part, months, refresh), ("booking", ["2020-10"], False))
            return fake

        buf = io.StringIO()
        env = {"PART": "booking", "MONTHS": "2020-10", "REFRESH": "0"}
        with mock.patch.dict(os.environ, env), mock.patch.object(c, "run", fake_run), redirect_stdout(buf):
            self.assertEqual(c.main(), 0)
        line = buf.getvalue()
        self.assertTrue(line.startswith(c.MARKER) and line.endswith("\n") and line.count("\n") == 1)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "out.txt"
            p.write_text("noise\n" + line, encoding="utf-8")
            self.assertEqual(m.load_bundle(str(p), "booking"), fake)

    def test_bundle_is_scrubbed(self):
        b = c.bundle("cis", {"2099-10": {"platform_cost": {"aws": {"account_id": "x"}}}},
                     datetime(2099, 11, 3, tzinfo=timezone.utc))
        self.assertNotIn("account_id", json.dumps(b))
        self.assertEqual(b["part"], "cis")

    def test_a_cost_by_app_answer_leaves_no_account_id_in_the_bundle(self):
        """The live cost_by_app shape carries IDs under account_id, ai_by_source[].account_name and
        llm_satellites.lines[].label (shared/aws_client/accounts.py); none may reach the public repo."""
        acc2, acc3 = "1" * 12, "2" * 12  # invented IDs

        async def cost_fn(pool, month, *, refresh_if_stale):
            return {
                "month": month, "totals": {"total_usd": 1.5},
                "aws": {"account_id": acc2, "total_usd": 1.0},
                "apps": [{"app": "cis", "ai_by_source": [
                    {"provider": "bedrock", "account": "acc3", "account_name": acc3, "cost_usd": 0.5},
                    {"provider": "bedrock", "account": "acc2", "account_name": acc2, "cost_usd": 0.1},
                    {"provider": "openai", "account": "openai-direct", "account_name": "OpenAI API", "cost_usd": 0.1},
                    {"provider": "crm_gateway:m1", "account": None, "account_name": None, "cost_usd": 0.1}]}],
                "llm_satellites": {"acc3": {"account_id": acc3, "ce_bedrock_usd": 0.4},
                                   "lines": [{"key": "acc3", "label": f"{acc3} (LLM)", "account_id": acc3}]},
                "refresh": {"stale": False,
                            "reason": f"AccessDenied: arn:aws:sts::{acc2}:assumed-role/x is not authorized"},
            }

        db = FakeDB({c.PUBLISHED_TOURS_SQL: [{"published_tours": 1, "published_tours_live": 1}],
                     c.LLM_BY_STAGE_SQL: []})
        data = asyncio.run(c.collect_cis(db, ["2099-10"], date(2099, 11, 3), cost_fn=cost_fn))
        b = c.bundle("cis", data, datetime(2099, 11, 3, tzinfo=timezone.utc))
        text = json.dumps(b)
        self.assertIsNone(re.search(r"\b\d{12}\b", text), text)
        self.assertEqual(c.find_account_ids(b), [])
        pc = b["months"]["2099-10"]["platform_cost"]
        self.assertEqual([s["account_name"] for s in pc["apps"][0]["ai_by_source"]],
                         ["acc3", "acc2", "OpenAI API", None])
        self.assertEqual(pc["llm_satellites"]["lines"][0]["label"], "acc3 (LLM)")
        self.assertIn("arn:aws:sts::<account-id>:assumed-role", pc["refresh"]["reason"])
        self.assertEqual(pc["llm_satellites"]["acc3"], {"ce_bedrock_usd": 0.4})

    def test_scrub_keeps_uuids_and_amounts(self):
        uid = "0f0e0d0c-0000-4000-8000-" + "3" * 12
        self.assertEqual(c.scrub({"id": uid, "usd": 0.123456789012}), {"id": uid, "usd": 0.123456789012})

    def test_main_refuses_to_print_a_bundle_with_an_account_id(self):
        async def fake_run(part, months, refresh, now):
            return {"kind": "finops_bundle", "part": "crm", "months": {"2099-10": {"n": int("5" * 12)}}}

        buf, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"PART": "crm", "MONTHS": "2020-10"}), \
                mock.patch.object(c, "run", fake_run), redirect_stdout(buf), mock.patch.object(c.sys, "stderr", err):
            self.assertEqual(c.main(), 3)
        self.assertEqual(buf.getvalue(), "")
        self.assertIn("$.months.2099-10.n", err.getvalue())


class SchemaNamesTest(unittest.TestCase):
    """Every table the collector reads exists in the live dump (never guess names, db-schema.md)."""

    def test_tables_exist_in_the_schema_reference(self):
        ref = (REPO / "docs/architecture/db-schema-reference.md").read_text(encoding="utf-8")
        sql = "\n".join([c.LLM_BY_STAGE_SQL, c.PUBLISHED_TOURS_SQL, c.TRIP_CASES_SQL, c.CRM_LLM_SQL])
        tables = set(re.findall(r"\b(?:FROM|JOIN)\s+([a-z_]+\.[a-z_]+)", sql))
        self.assertEqual(tables, {"shared.llm_call_daily", "shared.llm_call_log", "gold_aa_internal.published_tours",
                                  "booking.trip_cases", "crm.llm_usage_daily"})
        for t in tables:
            self.assertIn(f"### `{t}` (", ref, t)

    def test_confirmed_statuses_are_allowed_by_the_check(self):
        ref = (REPO / "docs/architecture/db-schema-reference.md").read_text(encoding="utf-8")
        check = next(ln for ln in ref.splitlines() if "trip_cases_status_chk" in ln)
        for s in c.CONFIRMED_STATUSES:
            self.assertIn(f"'{s}'", check)


if __name__ == "__main__":
    unittest.main()
