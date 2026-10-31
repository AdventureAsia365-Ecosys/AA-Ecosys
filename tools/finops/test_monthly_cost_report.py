"""Run: python3 -m unittest discover -s tools/finops -p 'test_*.py' (from the repo root). Synthetic data only."""
import io
import json
import tempfile
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

    def test_satellites_acc3_only_after_aa998(self):
        out = self.run_main("--current", str(S / "platform-cost-2099-02.json"),
                            "--previous", str(S / "platform-cost-2099-01.json"))
        self.assertIn("| acc3 (LLM satellite) | 30.00 | 18.00 | +66.7 % |", out)
        self.assertNotIn("acc1", out)

    def test_retired_acc1_row_only_when_a_month_carries_it(self):
        self.assertEqual(m.satellite_rows({}, {}), [("acc3", "acc3 (LLM satellite)")])
        # cost_by_app names the retired account "retired" since AA-998
        self.assertEqual(m.satellite_rows({"retired": {}}, {}),
                         [("acc3", "acc3 (LLM satellite)"), ("retired", "Retired account (former LLM fallback)")])
        self.assertEqual(m.satellite_rows({"acc3": {}}, {"acc1": {"ce_bedrock_usd": 0.76}}),
                         [("acc3", "acc3 (LLM satellite)"), ("acc1", "acc1 (retired, AA-998)")])

    def test_change(self):
        self.assertEqual(m.change(None, 1.0), ("n/a", False))
        self.assertEqual(m.change(5.0, 0.0), ("new", True))
        self.assertEqual(m.change(12.0, 10.0), ("+20.0 %", False))
        self.assertEqual(m.change(12.1, 10.0)[1], True)

    def test_rejects_other_json(self):
        bad = S.parent / "samples" / "units-2099-02.json"
        with self.assertRaises(SystemExit):
            m.load_json(str(bad))


B = {"bundle": str(S / "finops-bundle-cis-2099.json"), "booking": str(S / "finops-bundle-booking-2099.txt"),
     "crm": str(S / "finops-bundle-crm-2099.txt")}


class BundleReportTest(unittest.TestCase):
    """S262: the collect_month.py bundles (several months, booking and CRM parts)."""

    def run_main(self, *args: str) -> str:
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(m.main(list(args)), 0)
        return buf.getvalue()

    def full(self) -> str:
        return self.run_main("--bundle", B["bundle"], "--booking-bundle", B["booking"], "--crm-bundle", B["crm"],
                             "--budget-usd", "300")

    def test_latest_month_is_the_default_and_compares_with_the_month_before(self):
        out = self.full()
        self.assertIn("from /admin/platform/cost 2099-03 vs 2099-02", out)
        self.assertIn("| acc2 (infra, all App tags) | 200.00 | 186.00 | +7.5 % |", out)

    def test_month_over_month_has_every_month(self):
        out = self.full()
        self.assertIn("## Month over month", out)
        self.assertIn("| App | 2099-01 | 2099-02 | 2099-03 | Change, last month |", out)
        self.assertIn("| CIS (content + catalog) | 120.00 | 155.00 | 180.00 | +16.1 % |", out)
        self.assertIn("| **Total (AWS acc2 + LLM outside AWS)** | 178.00 | 211.00 | 241.50 | +14.5 % |", out)
        self.assertIn("| Amazon ElastiCache | 40.00 | 52.00 | 60.00 | +15.4 % |", out)

    def test_crm_gateway_spend_is_added_once_to_the_crm_row_and_totals(self):
        out = self.full()
        self.assertIn("| CRM | 5.50 | n/a | n/a | 4.00 | 1.50 |", out)
        self.assertIn("Total per the AA-884 rule (AWS acc2 + LLM - acc2 Bedrock counted once): 241.50 USD.", out)
        self.assertIn("| crm | crm_mail_summary | model-small | crm_gateway | 30 | 1.50 |", out)
        self.assertNotIn("CRM LLM spend is not in the CRM row", out)

    def test_apply_crm_skips_an_export_that_already_has_it(self):
        cost = {"apps": [], "totals": {"total_usd": 1.0}, "crm_llm": {"status": "ok"}}
        self.assertIs(m.apply_crm(cost, {"crm_llm": {"cost_usd": 9.0}}), cost)

    def test_without_crm_bundle_the_gap_is_a_finding(self):
        out = self.run_main("--bundle", B["bundle"])
        self.assertIn("CRM LLM spend is not in the CRM row", out)
        self.assertIn("| CRM | 4.00 |", out)

    def test_unit_costs_from_bundle_counts(self):
        out = self.full()
        # Last month's tour count read today is too low (republish moves published_at): no per-tour cost for it.
        self.assertIn("| USD per published tour | 0.30 | n/a (published_at is overwritten on republish) | "
                      "cis total / 600 published tours; 520 live at month end |", out)
        self.assertIn("| USD LLM per published tour | 0.07 | n/a (published_at is overwritten on republish) |", out)
        self.assertIn("| USD per trip case | 1.25 | 2.50 | booking total / 8 trip cases created |", out)
        self.assertIn("| USD per booking | 5.00 | n/a | booking total / 2 bookings (trip cases confirmed or later) |", out)
        self.assertIn("| USD per trip plan | n/a | n/a | tripplanner total / no count trip plans |", out)

    def test_vietnamese_summary_has_five_lines_with_numbers(self):
        out = self.full()
        self.assertIn("## Tóm tắt cho chủ doanh nghiệp (VI)", out)
        section = out.split("## Tóm tắt cho chủ doanh nghiệp (VI)")[1].split("\n## ")[0]
        lines = [ln for ln in section.splitlines() if ln[:2] in {"1.", "2.", "3.", "4.", "5."}]
        self.assertEqual(len(lines), 5)
        self.assertIn("1. Tổng chi phí tháng 03/2099: 241.50 USD", lines[0])
        self.assertIn("So với tháng 02/2099 (211.00 USD): +14.5 %", lines[1])
        self.assertIn("CIS (content + catalog) +25.00 USD; lý do: <điền>", lines[2])
        self.assertIn("đã dùng 200.00 / 300.00 USD (67 %), còn 100.00 USD", lines[3])
        self.assertIn("0.30 USD (riêng AI 0.07 USD)", lines[4])
        self.assertNotRegex(section, r"AA-[0-9]")

    def test_acc3_credit_gap_is_a_finding_not_a_saving(self):
        out = self.full()
        self.assertIn("acc3 Bedrock in Cost Explorer (2.50 USD) is under half of the gateway estimate (38.00 USD)", out)

    def test_earlier_month_and_no_account_ids(self):
        out = self.run_main("--bundle", B["bundle"], "--month", "2099-02")
        self.assertIn("| App | 2099-01 | 2099-02 | Change, last month |", out)
        self.assertNotIn("| 2099-03 |", out)
        self.assertNotIn("CRM rows come from its own gateway", out)
        self.assertNotIn("<acc2>", out)

    def test_ledger_by_app(self):
        out = self.full()
        self.assertIn("By app: cis 39.70 USD, crm 1.50 USD, tripplanner 0.30 USD.", out)
        self.assertIn("### Ad-hoc runs (stage adhoc_<issue>) — 0.20 USD", out)

    def test_prev_units_from_last_months_saved_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            saved = Path(d) / "cis-saved-2099-03-02.txt"  # last month's bundle, counted at that month's end
            saved.write_text("ecsx: run started\nFINOPS_BUNDLE " + json.dumps(
                {"kind": "finops_bundle", "version": 1, "part": "cis", "generated_at": "2099-03-02T00:00:00+00:00",
                 "months": {"2099-02": {"units": {"published_tours": 500, "published_tours_live": 480}}}}) + "\n",
                encoding="utf-8")
            out = self.run_main("--bundle", B["bundle"], "--prev-units", str(saved))
            self.assertIn("| USD per published tour | 0.30 | 0.31 |", out)  # 155.00 / 500
            plain = Path(d) / "units.json"
            plain.write_text(json.dumps({"published_tours": 310}), encoding="utf-8")
            out = self.run_main("--bundle", B["bundle"], "--prev-units", str(plain))
            self.assertIn("| USD per published tour | 0.30 | 0.50 |", out)
            no_month = Path(d) / "other.json"
            no_month.write_text(json.dumps({"kind": "finops_bundle", "months": {"2098-12": {"units": {}}}}),
                                encoding="utf-8")
            with self.assertRaises(SystemExit):
                self.run_main("--bundle", B["bundle"], "--prev-units", str(no_month))

    def test_management_account_row_and_grand_total(self):
        out = self.run_main("--bundle", B["bundle"], "--crm-bundle", B["crm"], "--mgmt-usd", "3.5",
                            "--mgmt-prev-usd", "3")
        self.assertIn("| Management account (org trail, KMS, budgets) | 3.50 | 3.00 | +16.7 % |", out)
        self.assertIn("Grand total with the management account: 245.00 USD.", out)
        self.assertIn("1. Tổng chi phí tháng 03/2099: 245.00 USD (hạ tầng AWS 200.00 USD, AI tính ngoài hoá đơn AWS "
                      "41.50 USD, tài khoản quản lý AWS 3.50 USD).", out)
        self.assertIn("2. So với tháng 02/2099 (214.00 USD): +14.5 %.", out)
        only_cur = self.run_main("--bundle", B["bundle"], "--crm-bundle", B["crm"], "--mgmt-usd", "3.5")
        self.assertIn("(211.00 USD): +14.5 % (so sánh chưa gồm tài khoản quản lý).", only_cur)
        with self.assertRaises(SystemExit):
            self.run_main("--bundle", B["bundle"], "--mgmt-prev-usd", "3")

    def test_without_management_input_the_totals_say_so(self):
        out = self.full()
        self.assertIn("| Management account (org trail, KMS, budgets) | not included |", out)
        self.assertIn("Grand total: the management account is not included (no --mgmt-usd).", out)
        self.assertIn("1. Tổng chi phí tháng 03/2099: 241.50 USD (hạ tầng AWS 200.00 USD, AI tính ngoài hoá đơn AWS "
                      "41.50 USD; chưa gồm tài khoản quản lý AWS).", out)

    def test_sample_bundle_and_report_hold_no_account_id(self):
        self.assertFalse(m.ACCOUNT_ID_RE.search(Path(B["bundle"]).read_text(encoding="utf-8")))
        self.assertFalse(m.ACCOUNT_ID_RE.search(self.full()))

    def test_report_refuses_text_with_an_account_id(self):
        cost = json.loads(Path(B["bundle"]).read_text(encoding="utf-8"))["months"]["2099-03"]["platform_cost"]
        cost["apps"][0]["label"] = "CIS " + "4" * 12  # an unscrubbed export
        with self.assertRaises(SystemExit):
            m.build(cost, None, None, None)

    def test_bad_inputs(self):
        with self.assertRaises(SystemExit):
            m.load_bundle(B["booking"], "cis")  # wrong part
        with self.assertRaises(SystemExit):
            m.load_bundle(str(S / "units-2099-02.json"), "cis")  # not a bundle
        with self.assertRaises(SystemExit):
            self.run_main("--bundle", B["bundle"], "--month", "2099-07")
        with self.assertRaises(SystemExit):
            self.run_main("--bundle", B["bundle"], "--current", str(S / "platform-cost-2099-02.json"))
        with self.assertRaises(SystemExit):
            self.run_main("--current", str(S / "platform-cost-2099-02.json"), "--month", "2099-02")


if __name__ == "__main__":
    unittest.main()
