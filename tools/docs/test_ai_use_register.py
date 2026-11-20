"""AA-1168 register guard: every LLM route has a row in the AI Use Register (docs/architecture/ai-use-register.md).

Run: python -m unittest discover -s tools/docs -p 'test_*.py' (the docs-lint "Unit tests of the lint tools" step).

The routes are the stages of the committed route snapshot docs/generated/llm-routes.snapshot.json (every row of
`shared.llm_role_config`, active or not; recaptured with tools/docs/gen_llm_routes.py) plus GATEWAY_STAGES_WITHOUT_ROUTE:
stages an app's gateway runs without a route row of its own, which the snapshot cannot show. A register row names
its stages in backticks in the first cell of a table row of the "## Register" section; a name with `*` covers every
stage it matches (`crm_*`). The first tests use invented names only; the last one checks the committed files.
"""

from __future__ import annotations

import fnmatch
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTER = REPO_ROOT / "docs" / "architecture" / "ai-use-register.md"
SNAPSHOT = REPO_ROOT / "docs" / "generated" / "llm-routes.snapshot.json"

# Stage -> where its gateway runs it with no `shared.llm_role_config` row (so no snapshot row). Remove an entry once
# CIS seeds the stage's own route row: the snapshot then carries it.
GATEWAY_STAGES_WITHOUT_ROUTE = {
    "tp_plan_chat": "AA-TripPlanner-Web backend/shared/llm_gateway.py (borrows the tp_compose route)",
}

_STAGE_NAME = re.compile(r"`([a-z0-9_*]+)`")


def register_section(page: str) -> str:
    """The text of the "## Register" section (up to the next level-2 heading)."""
    match = re.search(r"^## Register\s*$(.*?)(?=^## )", page, flags=re.M | re.S)
    if not match:
        raise ValueError("the register page has no '## Register' section")
    return match.group(1)


def register_stage_names(page: str) -> set[str]:
    """Every backticked stage name in the first cell of a table row of the Register section (header and rule rows
    excluded)."""
    names: set[str] = set()
    for line in register_section(page).splitlines():
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        first = line.split("|")[1]
        names.update(_STAGE_NAME.findall(first))
    return names


def snapshot_stages(snapshot: dict) -> set[str]:
    return {r["stage"] for r in snapshot.get("routes", []) if r.get("stage")}


def missing_rows(stages: set[str], names: set[str]) -> list[str]:
    """Stages with no register row: no exact name and no `*` pattern that matches."""
    patterns = [n for n in names if "*" in n]
    return sorted(s for s in stages if s not in names and not any(fnmatch.fnmatchcase(s, p) for p in patterns))


_PAGE = """# Register page

## Register

| Stage | App | Purpose |
|---|---|---|
| `zz_write` | CIS | Writes |
| `zz_judge`, `zz_audit` | CIS | Judges `zz_not_a_row_name` in a later cell |
| `crm_*` (gateway v2) | CRM | Drafts |
| None | Booking | No AI |

## Machine-readable marking

| Surface | What |
|---|---|
| `zz_marking_only` | not a register row |
"""


class ParseTest(unittest.TestCase):
    def test_first_cell_names_only_in_the_register_section(self) -> None:
        self.assertEqual(register_stage_names(_PAGE), {"zz_write", "zz_judge", "zz_audit", "crm_*"})

    def test_missing_rows_honour_patterns(self) -> None:
        names = register_stage_names(_PAGE)
        self.assertEqual(missing_rows({"zz_write", "crm_draft_reply", "zz_new_stage"}, names), ["zz_new_stage"])
        self.assertEqual(missing_rows({"zz_marking_only", "zz_not_a_row_name"}, names),
                         ["zz_marking_only", "zz_not_a_row_name"])

    def test_page_without_register_section_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            register_section("# Page\n\n## Other\n\ntext\n")

    def test_snapshot_stages(self) -> None:
        snap = {"routes": [{"stage": "zz_write", "is_active": True}, {"stage": "zz_off", "is_active": False}]}
        self.assertEqual(snapshot_stages(snap), {"zz_write", "zz_off"})


class CommittedRegisterTest(unittest.TestCase):
    def test_every_route_and_gateway_stage_has_a_register_row(self) -> None:
        names = register_stage_names(REGISTER.read_text(encoding="utf-8"))
        stages = snapshot_stages(json.loads(SNAPSHOT.read_text(encoding="utf-8"))) | set(GATEWAY_STAGES_WITHOUT_ROUTE)
        self.assertGreater(len(stages), 30, "the route snapshot looks empty")
        missing = missing_rows(stages, names)
        self.assertEqual(missing, [], "LLM stages with no row in docs/architecture/ai-use-register.md (Register "
                                      "section): add a row per stage (AA-1168, EU AI Act Art. 50)")

    def test_gateway_stages_without_route_are_not_in_the_snapshot(self) -> None:
        """Once CIS seeds a stage's own route row, the snapshot carries it: drop the hand entry."""
        stages = snapshot_stages(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
        self.assertEqual(sorted(set(GATEWAY_STAGES_WITHOUT_ROUTE) & stages), [])


if __name__ == "__main__":
    unittest.main()
