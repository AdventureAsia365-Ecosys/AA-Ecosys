"""Tests for aa1095_acc1_route_order.py (AA-1095, S278). Fakes for the CIS modules and the pool; invented values, no DB.

Run: python3 -m unittest discover -s tools/llm -p 'test_*.py'
"""

from __future__ import annotations

import asyncio
import types
import unittest

import aa1095_acc1_route_order as ro

ENV = {ro.PAYER_ENV: "777788889999"}
CONN_ROW = {"connection_key": "acc1", "kind": "bedrock", "auth_mode": "assume_role",
            "account_id_env": ro.PAYER_ENV, "enabled": False}
DEPLOYMENTS = [{"model_key": "sonnet-5-5", "enabled": True}, {"model_key": "gpt-6-luna", "enabled": True}]
LIVE = {
    "order_mode": "aws_first",
    "routes": {"w_stage": {"model_id": "sonnet-5-5", "fallback_model_ids": ["gpt-6-luna"]}},
    "priorities": {"sonnet-5-5": {"acc3": 10, "acc1": 90, "anthropic-direct": 100},
                   "gpt-6-luna": {"acc3": 10, "acc1": 90}},
}
ORDER = {"sonnet-5-5": ["anthropic-direct", "acc1", "acc3"], "gpt-6-luna": ["acc1", "acc3"]}


class _Db:
    def __init__(self, row):
        self.row = row

    async def fetchrow(self, sql, *args):
        return self.row

    async def fetch(self, sql, *args):
        return DEPLOYMENTS


class _Pool:
    def __init__(self, row=CONN_ROW):
        self.db = _Db(row)

    def acquire(self):
        pool = self

        class _Ctx:
            async def __aenter__(self):
                return pool.db

            async def __aexit__(self, *exc):
                return False
        return _Ctx()


def _world():
    return types.SimpleNamespace(
        live=LIVE,
        models=[types.SimpleNamespace(model_key="sonnet-5-5", family_key="anthropic"),
                types.SimpleNamespace(model_key="gpt-6-luna", family_key="openai")],
        connections={"acc3": {"kind": "bedrock", "data_scope": "aws_only", "enabled": True},
                     "acc1": {"kind": "bedrock", "data_scope": "aws_only", "enabled": False},
                     "anthropic-direct": {"kind": "anthropic", "data_scope": "vendor_direct", "enabled": True}},
        deployments=[{"model_key": m, "connection_key": c, "enabled": True}
                     for m, p in LIVE["priorities"].items() for c in p],
        stages=[{"stage": "w_stage", "role": "writer", "is_active": True, "model_id": "sonnet-5-5"},
                {"stage": "off_stage", "role": "writer", "is_active": False, "model_id": "sonnet-5-5"}])


class _Rc:
    def __init__(self, valid=True, apply_error=None, waves=()):
        self.calls = []
        self.valid, self.apply_error, self.waves = valid, apply_error, list(waves)

    async def read_world(self, pool):
        return _world()

    async def preview(self, pool, **kw):
        self.calls.append(("preview", kw))
        errors = [] if self.valid else [{"rule": "attempt_cap", "message": "too many", "stage": "w_stage"}]
        return {"valid": self.valid, "version": 41, "needs_evidence": True, "errors": errors,
                "warnings": [{"rule": "attempt_cap", "message": "old", "existing": True}],
                "frozen_by_waves": self.waves}

    async def apply(self, pool, **kw):
        self.calls.append(("apply", kw))
        if self.apply_error:
            raise self.apply_error
        return {"version": 42, "diff": [{}, {}, {}], "changed_stages": [], "warnings": []}

    async def serving(self, world):
        return {"w_stage": {"first": "sonnet-5-5@anthropic-direct"}}


class _Fo:
    ORDER_MODE = "model_first"

    @staticmethod
    def family_provider_order(priorities, families, connections, lead):
        assert lead == "acc1" and families["sonnet-5-5"] == "anthropic"
        return ORDER


class _Lc:
    def __init__(self):
        self.calls = []

    async def set_enabled(self, db, key, *, enabled, actor):
        self.calls.append((key, enabled, actor))


def _run(pool=None, *, apply=False, env=ENV, rc=None, lc=None):
    rc, lc, lines = rc or _Rc(), lc or _Lc(), []
    code = asyncio.run(ro.run(pool or _Pool(), actor="s278-test", apply=apply, environ=env, rc=rc, fo=_Fo, lc=lc,
                              out=lines.append))
    return code, rc, lc, "\n".join(lines)


class EnvAndConnectionTests(unittest.TestCase):
    def test_the_payer_env_must_be_a_12_digit_id_and_is_never_printed(self):
        self.assertIsNone(ro.env_problem(ENV))
        self.assertIn("not set", ro.env_problem({}))
        self.assertIn("12-digit", ro.env_problem({ro.PAYER_ENV: "12345"}))
        code, rc, lc, text = _run()
        self.assertEqual(code, 0)
        self.assertNotIn("777788889999", text)

    def test_a_missing_env_refuses_before_any_read(self):
        code, rc, lc, text = _run(env={})
        self.assertEqual((code, rc.calls, lc.calls), (2, [], []))

    def test_a_missing_or_wrong_connection_refuses(self):
        self.assertEqual(_run(_Pool(row=None))[0], 2)
        self.assertEqual(_run(_Pool(row={**CONN_ROW, "account_id_env": "OTHER"}))[0], 2)
        self.assertIn("not bedrock/assume_role",
                      " ".join(ro.connection_problems({**CONN_ROW, "auth_mode": "task_role"}, DEPLOYMENTS)))


class DryRunTests(unittest.TestCase):
    def test_dry_run_previews_and_writes_nothing(self):
        code, rc, lc, text = _run()
        self.assertEqual(code, 0)
        self.assertEqual([c[0] for c in rc.calls], ["preview"])
        self.assertEqual(rc.calls[0][1], {"order_mode": "model_first", "provider_order": ORDER})
        self.assertEqual(lc.calls, [])
        self.assertIn("DRY RUN", text)

    def test_the_chain_report_shows_both_families_before_and_after(self):
        code, rc, lc, text = _run()
        self.assertIn("before: sonnet-5-5@acc3 > sonnet-5-5@acc1 (off) > sonnet-5-5@anthropic-direct > "
                      "gpt-6-luna@acc3 > gpt-6-luna@acc1 (off)", text)
        self.assertIn("after:  sonnet-5-5@anthropic-direct > sonnet-5-5@acc1 > sonnet-5-5@acc3 > "
                      "gpt-6-luna@acc1 > gpt-6-luna@acc3", text)
        self.assertNotIn("off_stage", text)

    def test_an_invalid_preview_or_an_open_wave_refuses(self):
        self.assertEqual(_run(apply=True, rc=_Rc(valid=False))[0], 1)
        code, rc, lc, text = _run(apply=True, rc=_Rc(waves=[{"wave": 1}]))
        self.assertEqual((code, lc.calls), (1, []))


class ApplyTests(unittest.TestCase):
    def test_apply_switches_the_connection_on_then_saves_one_break_glass_version(self):
        code, rc, lc, text = _run(apply=True)
        self.assertEqual(code, 0)
        self.assertEqual(lc.calls, [("acc1", True, "s278-test")])
        kind, kw = rc.calls[-1]
        self.assertEqual(kind, "apply")
        self.assertEqual((kw["action"], kw["expected_version"], kw["order_mode"], kw["provider_order"]),
                         ("save", 41, "model_first", ORDER))
        self.assertEqual(kw["break_glass_reason"], ro.REASON)
        self.assertGreaterEqual(len(ro.REASON), 12)
        self.assertIn("saved route-control version 42", text)
        self.assertIn("w_stage: sonnet-5-5@anthropic-direct", text)

    def test_a_refused_save_switches_the_connection_back_off(self):
        code, rc, lc, text = _run(apply=True, rc=_Rc(apply_error=ValueError("conflict")))
        self.assertEqual(code, 1)
        self.assertEqual(lc.calls, [("acc1", True, "s278-test"), ("acc1", False, "s278-test")])
        self.assertIn("switched back off", text)

    def test_an_already_enabled_connection_is_not_toggled(self):
        code, rc, lc, text = _run(_Pool(row={**CONN_ROW, "enabled": True}), apply=True,
                                  rc=_Rc(apply_error=ValueError("x")))
        self.assertEqual((code, lc.calls), (1, []))


if __name__ == "__main__":
    unittest.main()
