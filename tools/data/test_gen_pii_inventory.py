"""Tests for gen_pii_inventory.py (AA-877). Run: python3 -m unittest discover -s tools/data -p 'test_*.py'"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_pii_inventory as g  # noqa: E402

REFERENCE = """# AA-Ecosys DB Schema Reference (live dump)

**Verified:** 2026-10-22 05:28 UTC — live catalog dump.

## Relations

### `booking.customers` (table, ~1 rows)
```
id uuid NN
name text · pii:name
email text · pii:contact
contact_consent boolean NN
gender text · pii:profile
```

### `booking.trip_plans` (table)
```
id uuid NN
commercial_notes text · conf:commercial
```

### `shared.admin_users` (table)
```
id uuid NN
email text · pii:contact
```

## Personal and confidential data tags (DM-6.1)

Column comments that start with `pii:<class>`.

| schema | tag | columns | named as also |
|---|---|---|---|
| `booking` | `pii:name` | 1 | 0 |

### Tagged columns

| schema | relation | column | tag | also |
|---|---|---|---|---|
| `booking` | `customers` | `email` | `pii:contact` |  |
| `booking` | `customers` | `gender` | `pii:profile` |  |
| `booking` | `customers` | `name` | `pii:name` |  |
| `booking` | `inbox_events` | `payload` | `pii:contact` | `pii:name`, `pii:free_text` |
| `booking` | `trip_plans` | `commercial_notes` | `conf:commercial` |  |
| `shared` | `admin_users` | `email` | `pii:contact` |  |

### Tag findings

- none

## RLS catalogue guard (X2)

| schema | relation | column | tag | also |
|---|---|---|---|---|
| `booking` | `not` | `parsed` | `pii:name` |  |
"""

REGISTER = """---
id: SEC-04
---

# Compliance and privacy register

## (a) Records of processing (RoPA)

> [!IMPORTANT]
> **Provisional.**

| # | Purpose | Data subjects | Data classes | Tables and columns (dump 2026-10-20) | Retention |
|---|---|---|---|---|---|
| 1 | Booking customers | Travellers | `name` | `booking.customers` (`name`, `email`, `contact_consent`, `missing_col`; CHECK `customers_chk`); `booking.inbox_events.payload` (copy, `redacted_at` column) | none |
| 2 | Staff | Staff | `contact` | `shared.admin_users` (`email`) | none |

### How to regenerate this table

1. Steps.

## (b) Sub-processors

Text.
"""


class ParseTest(unittest.TestCase):
    def test_reference_reads_only_the_tagged_columns_table(self):
        ref = g.parse_reference(REFERENCE)
        self.assertEqual(ref["verified"], "2026-10-22 05:28 UTC")
        keys = [(t["schema"], t["relation"], t["column"], t["tag"]) for t in ref["tagged"]]
        self.assertEqual(len(keys), 6)                                     # not the RLS section's table
        self.assertIn(("shared", "admin_users", "email", "pii:contact"), keys)
        payload = next(t for t in ref["tagged"] if t["column"] == "payload")
        self.assertEqual(payload["also"], ["pii:name", "pii:free_text"])
        self.assertEqual(ref["columns"][("booking", "customers")],
                         {"id", "name", "email", "contact_consent", "gender"})

    def test_named_columns_of_a_cell(self):
        cell = ("`booking.customers` (`name`, `email`, `contact_consent`, `missing_col`; CHECK `customers_chk`); "
                "`booking.inbox_events.payload` (copy, `redacted_at` column)")
        self.assertEqual(g.named_columns(cell), {
            ("booking", "customers", "name"), ("booking", "customers", "email"),
            ("booking", "customers", "contact_consent"), ("booking", "customers", "missing_col"),
            ("booking", "customers", "customers_chk"), ("booking", "inbox_events", "payload"),
        })

    def test_nested_parentheses(self):
        cell = "`tripplanner.sessions` (`guest_token_hash`, `customer_id`; plaintext (`guest_token`) retired)"
        self.assertEqual({c for _, _, c in g.named_columns(cell)}, {"guest_token_hash", "customer_id", "guest_token"})

    def test_ropa_rows(self):
        rows = g.parse_ropa(REGISTER)
        self.assertEqual(sorted(rows), [1, 2])
        self.assertIn(("shared", "admin_users", "email"), rows[2])

    def test_missing_ropa_table_is_an_error(self):
        with self.assertRaises(g.InventoryError):
            g.parse_ropa("## (a) Records of processing (RoPA)\n\nNo table.\n\n## (b) x\n")


class InventoryTest(unittest.TestCase):
    def setUp(self):
        self.ref = g.parse_reference(REFERENCE)
        self.inv = g.inventory(self.ref, g.parse_ropa(REGISTER))

    def test_commercial_left_out_and_rows_mapped(self):
        by_col = {(r["relation"], r["column"]): r["ropa"] for r in self.inv["rows"]}
        self.assertNotIn(("trip_plans", "commercial_notes"), by_col)
        self.assertEqual(by_col[("customers", "email")], [1])
        self.assertEqual(by_col[("admin_users", "email")], [2])

    def test_new_processing_line_and_tagging_gap(self):
        self.assertEqual(self.inv["new_lines"], ["booking.customers.gender"])
        # contact_consent exists and is untagged; missing_col and customers_chk are not columns of the reference.
        self.assertEqual(self.inv["gaps"], ["booking.customers.contact_consent"])

    def test_block_render(self):
        block = g.render_block(self.ref, self.inv)
        self.assertTrue(block.startswith(g.START + "\n\n### Column inventory (from pii tags)\n"))
        self.assertTrue(block.endswith("\n\n" + g.END))
        self.assertIn("(Verified 2026-10-22 05:28 UTC): 5 personal-data column(s) and 0 credential column(s)", block)
        self.assertIn("| `booking` | `customers` | `gender` | `pii:profile` |  | **none** |", block)
        self.assertIn("| `booking` | `inbox_events` | `payload` | `pii:contact` | `pii:name`, `pii:free_text` | 1 |",
                      block)


class WriteTest(unittest.TestCase):
    def test_insert_then_replace_in_place(self):
        ref = g.parse_reference(REFERENCE)
        block = g.render_block(ref, g.inventory(ref, g.parse_ropa(REGISTER)))
        once = g.write_block(REGISTER, block)
        self.assertLess(once.index(g.START), once.index("### How to regenerate this table"))
        self.assertGreater(once.index(g.START), once.index("| 2 | Staff |"))
        self.assertEqual(g.write_block(once, block), once)                 # idempotent
        changed = g.write_block(once, block.replace("**none**", "9"))
        self.assertEqual(changed.count(g.START), 1)
        self.assertIn("| 9 |", changed)

    def test_falls_back_to_section_b(self):
        reg = REGISTER.replace("### How to regenerate this table\n\n1. Steps.\n\n", "")
        out = g.write_block(reg, "BLOCK")
        self.assertIn("BLOCK\n\n## (b) Sub-processors", out)


class MainTest(unittest.TestCase):
    def _files(self, register: str = REGISTER):
        d = Path(tempfile.mkdtemp())
        (d / "ref.md").write_text(REFERENCE, encoding="utf-8")
        (d / "reg.md").write_text(register, encoding="utf-8")
        return d

    def test_write_then_check(self):
        d = self._files()
        args = ["--reference", str(d / "ref.md"), "--register", str(d / "reg.md")]
        self.assertEqual(g.main(args + ["--check"]), 1)                    # stale block + a new line
        self.assertEqual(g.main(args), 0)
        self.assertIn(g.START, (d / "reg.md").read_text(encoding="utf-8"))
        self.assertEqual(g.main(args + ["--check"]), 1)                    # still a new processing line

    def test_check_passes_when_every_tag_has_a_row(self):
        reg = REGISTER.replace("`missing_col`;", "`missing_col`, `gender`;")
        d = self._files(reg)
        args = ["--reference", str(d / "ref.md"), "--register", str(d / "reg.md")]
        self.assertEqual(g.main(args), 0)
        self.assertEqual(g.main(args + ["--check"]), 0)
        self.assertEqual(g.main(args + ["--check", "--strict"]), 1)        # contact_consent: gap

    def test_missing_section_exits_2(self):
        d = self._files()
        (d / "ref.md").write_text("# empty\n", encoding="utf-8")
        self.assertEqual(g.main(["--reference", str(d / "ref.md"), "--register", str(d / "reg.md")]), 2)


if __name__ == "__main__":
    unittest.main()
