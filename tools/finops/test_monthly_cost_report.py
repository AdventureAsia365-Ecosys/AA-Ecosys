"""Run: python3 -m unittest discover -s tools/finops -p 'test_*.py' (from the repo root). Synthetic data only."""
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import monthly_cost_report as m

S = Path(__file__).parent / "samples"


class ReportTest(unittest.TestCase):
    def run_main(self, *args: str) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(m.main(list(args)), 0)
        return buf.getvalue()

    def test_full_report_sections_and_numbers(self):
        out = self.run_main("--current", str(S / "platform-cost-2099-02.json"),
                            "--previous", str(S / "platform-cost-2099-01.json"),
                            "--llm-csv", str(S / "llm-by-stage-2099-02.csv"),
                            "--units", str(S / "units-2099-02.json"))
        for heading in ("## Totals by account", "## By app (tag `App`)", "## Top 5 services", "## LLM spend",
                        "## Unit costs", "## Findings from the data"):
            self.assertIn(heading, out)
        self.assertIn("| acc2 (infra, all App tags) | 186.00 | 158.00 | +17.7 % |", out)
        self.assertIn("| CIS (content + catalog) | 155.00 | 120.00 | +29.2 % | 130.00 | 25.00 | change over 20 % |", out)
        self.assertIn("### Ad-hoc runs (stage adhoc_<issue>) — 0.40 USD", out)
        self.assertIn("| USD per booking | n/a |", out)

    def test_untagged_spend_is_a_finding(self):
        out = self.run_main("--current", str(S / "platform-cost-2099-01.json"))
        self.assertIn("Untagged acc2 spend 3.00 USD (DM-10.1): AWS Data Transfer.", out)
        self.assertIn("| n/a |", out)  # no previous month

    def test_change(self):
        self.assertEqual(m.change(None, 1.0), ("n/a", False))
        self.assertEqual(m.change(5.0, 0.0), ("new", True))
        self.assertEqual(m.change(12.0, 10.0), ("+20.0 %", False))
        self.assertEqual(m.change(12.1, 10.0)[1], True)

    def test_rejects_other_json(self):
        bad = S.parent / "samples" / "units-2099-02.json"
        with self.assertRaises(SystemExit):
            m.load_json(str(bad))


if __name__ == "__main__":
    unittest.main()
