"""S286 AA-1145 live proof (Booking API container, role booking, $0, nothing persists).

Done-when: a test contract with 50 % child price, tiered cancellation and a stop-sale on 24/12 prices correctly: the
child line is 50 % and 24/12 returns 'on request'; contracting can set a stop-sale, sales gets 403.

How: ONE transaction on the live Dev DB, ROLLED BACK at the end. A synthetic supplier / draft contract / per-person
service (prefix S286-PROOF) are inserted like the integration test's fixture
(backend/tests/integration/test_aa1145_supply_model.py); every later step calls the SAME service functions the API
routes call, on this one connection: contract_terms.put_terms (PUT /contracts/{id}/terms), rates.create_rate
(POST /contracts/{id}/rates), restrictions.create_term (POST /contracts/{id}/restrictions),
suppliers.update_contract status=published (PATCH /contracts/{id}, a second person), restrictions.create_stop_sale
(POST /contracts/{id}/stop-sales), restrictions.check (GET /supply/availability), and the B2B quote's pricing path
(quotes._policy, components.price_lines, restrictions.availability_many, quotes.supply_availability). Every function
takes the connection it is given (no own pool / connection), so every write rolls back with the outer transaction.
The 403 for sales is shown from the staff capability map (app.auth.staff) the route guard require() reads; the CI
integration test covers the HTTP 403.

Prints ids, counts, amounts and verdict codes only (no note / reason text). Exit 1 when an expectation fails.
"""
import asyncio
import json
import os
import sys
import traceback
import uuid
from datetime import date
from decimal import Decimal as D

import asyncpg

from app.auth.staff import PERMISSIONS, Staff
from app.b2b import quotes
from app.b2b.components import LineAsk, price_lines
from app.errors import ServiceError
from app.pricing import policy_values
from app.suppliers import service as suppliers
from app.supply import contract_terms, rates, restrictions

TAG = "S286-PROOF"
SUFFIX = uuid.uuid4().hex[:8]
SUPPLIER_NAME = f"{TAG} Lantern Bay Trips {SUFFIX}"
MAKER = Staff(cis_user_id="s286-proof-contracting", email=None, name=None, role="contracting", active=True,
              cis_role=None)
CHECKER = Staff(cis_user_id="s286-proof-admin", email=None, name=None, role="admin", active=True, cis_role=None)
SALES = Staff(cis_user_id="s286-proof-sales", email=None, name=None, role="sales", active=True, cis_role=None)
K_FROM, K_TO = date(2026, 12, 1), date(2026, 12, 31)
D23, D24, D25 = date(2026, 12, 23), date(2026, 12, 24), date(2026, 12, 25)
TIERS = [{"min_days": 30, "fee_pct": "0"}, {"min_days": 15, "fee_pct": "50"}, {"min_days": 0, "fee_pct": "100"}]
ADULT_NET = D("40.00")

failed: list[str] = []


def out(step: str, **kw) -> None:
    print(json.dumps({"step": step, **kw}, default=str), flush=True)


def expect(name: str, ok: bool, **kw) -> None:
    out(name, ok=bool(ok), **kw)
    if not ok:
        failed.append(name)


async def refused(conn, coro) -> str | None:
    """Run a call that should be refused, inside a savepoint; the refusal code (or None if it went through)."""
    try:
        async with conn.transaction():
            await coro
    except ServiceError as exc:
        return exc.code
    return None


async def main() -> int:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    outer = conn.transaction()
    await outer.start()
    contract_id = None
    try:
        # ── Synthetic staff rows (FK target of created_by / published_by), rolled back with everything else ──
        for st in (MAKER, CHECKER, SALES):
            await conn.execute(
                "INSERT INTO booking.staff_users (cis_user_id, role, active, created_at, updated_at, preferences)"
                " VALUES ($1, $2, true, now(), now(), '{}'::jsonb) ON CONFLICT (cis_user_id) DO NOTHING",
                st.cis_user_id, st.role)
        # ── Fixture (as the integration test's `draft`): invented supplier, draft USD contract, per-person service ──
        sid = await conn.fetchval(
            "INSERT INTO booking.suppliers (company_name, categories, country_code, created_by)"
            " VALUES ($1, $2, 'VN', $3) RETURNING id::text",
            SUPPLIER_NAME, ["activity"], MAKER.cis_user_id)
        contract_id = await conn.fetchval(
            "INSERT INTO booking.supplier_contracts (supplier_id, title, valid_from, valid_to, currency, created_by)"
            " VALUES ($1::uuid, $2, $3, $4, 'USD', $5) RETURNING id::text",
            sid, f"{TAG} December activities", K_FROM, K_TO, MAKER.cis_user_id)
        service_id = await conn.fetchval(
            "INSERT INTO booking.services (supplier_id, service_type, unit, title, created_by)"
            " VALUES ($1::uuid, 'activity', 'person', $2, $3) RETURNING id::text",
            sid, f"{TAG} Lantern boat trip {SUFFIX}", MAKER.cis_user_id)
        sv = f"sv:{service_id}"
        out("fixture", supplier_id=sid, contract_id=contract_id, service_id=service_id, rolled_back_at_end=True)

        # ── Contract terms on the draft (contracting): tiered cancellation, deposit + balance, child 50 % ──
        terms_in = {"cancellation_tiers": TIERS, "deposit_pct": D("30"), "deposit_due_days": 7,
                    "balance_due_days_before": 21, "credit_days_after": None, "child_pct": D("50")}
        saved = await contract_terms.put_terms(conn, MAKER, contract_id, terms_in)
        t = saved["terms"]
        expect("terms_saved", t["child_pct"] == "50.00" and [x["min_days"] for x in t["cancellation_tiers"]] ==
               [30, 15, 0], child_pct=t["child_pct"], tiers=t["cancellation_tiers"], deposit_pct=t["deposit_pct"],
               balance_due_days_before=t["balance_due_days_before"])
        terms = (await contract_terms.terms_many(conn, [contract_id]))[contract_id]
        fees = {days: format(terms.fee_pct(days), "f") for days in (45, 30, 20, 15, 7, 0)}
        expect("cancellation_tiers_fee_pct", fees == {45: "0.00", 30: "0.00", 20: "50.00", 15: "50.00", 7: "100.00",
                                                       0: "100.00"}, fee_pct_by_days_before=fees)

        # ── Adult rate 40 USD a person, a free-sale term for the whole contract (max 8 a booking) ──
        rate = await rates.create_rate(conn, MAKER, contract_id, {"service_id": service_id, "net_amount": ADULT_NET})
        out("adult_rate", rate_id=rate["id"], net_amount=rate["net_amount"], pax_type=rate.get("pax_type"),
            unit=rate["unit"])
        term = await restrictions.create_term(conn, MAKER, contract_id, {
            "component_id": sv, "inventory_kind": "free_sale", "date_from": K_FROM, "date_to": K_TO,
            "units": None, "release_days": None, "max_pax": 8, "note": None})
        out("free_sale_term", restriction_id=term["id"], status=term["status"], max_pax=term["max_pax"])

        # A stop-sale needs a published contract (409 contract_not_published while draft).
        early = await refused(conn, restrictions.create_stop_sale(conn, MAKER, contract_id, {
            "component_id": sv, "date_from": D24, "date_to": D24, "note": f"{TAG} supplier closed"}))
        expect("stop_sale_on_draft_refused", early == "contract_not_published", code=early)

        # ── Publish: the maker may not publish its own terms; a second person does ──
        mine = await refused(conn, suppliers.update_contract(conn, MAKER, contract_id, {"status": "published"}))
        expect("maker_cannot_publish", mine == "maker_checker", code=mine)
        published = await suppliers.update_contract(conn, CHECKER, contract_id, {"status": "published"})
        expect("contract_published_by_checker", published["status"] == "published", status=published["status"])
        locked = await refused(conn, contract_terms.put_terms(conn, MAKER, contract_id, terms_in))
        expect("terms_fixed_after_publish", locked == "contract_locked", code=locked)

        # ── Permission: stop_sale.write = contracting + admin, never sales (route guard require("stop_sale.write")) ──
        holders = sorted(PERMISSIONS["stop_sale.write"])
        expect("permission_map_stop_sale_write",
               "contracting" in holders and "sales" not in holders and MAKER.can("stop_sale.write")
               and not SALES.can("stop_sale.write"),
               holders=holders, contracting_can=MAKER.can("stop_sale.write"), sales_can=SALES.can("stop_sale.write"),
               sales_http="403 (require dependency; HTTP covered by tests/integration/test_aa1145_supply_model.py)")

        # ── Stop-sale on 24/12 by contracting: in effect at once (pending) ──
        ss = await restrictions.create_stop_sale(conn, MAKER, contract_id, {
            "component_id": sv, "date_from": D24, "date_to": D24, "note": f"{TAG} supplier closed"})
        expect("stop_sale_set_by_contracting", ss["status"] == "pending" and ss["in_effect"] is True,
               restriction_id=ss["id"], status=ss["status"], in_effect=ss["in_effect"],
               date_from=ss["date_from"], date_to=ss["date_to"])

        # ── Staff availability check (GET /supply/availability): 23 and 25 free-sale, 24 on request ──
        today = await policy_values.today_utc(conn)
        check = await restrictions.check(conn, component_id=sv, date_from=D23, date_to=D25, pax=3, units=1,
                                         today=today)
        days = [(d["date"], d["status"], d["reason"]) for d in check["days"]]
        expect("availability_check", days == [("2026-12-23", "available", "free_sale"),
                                              ("2026-12-24", "on_request", "stop_sale"),
                                              ("2026-12-25", "available", "free_sale")], days=days)

        # ── B2B quote pricing path: policy, price_lines (B4 child), engine verdicts, line availability ──
        try:
            policy = await quotes._policy(conn, today)
            by_type, age_max = policy.child_price_pct_by_service_type, quotes._child_age_max(policy)
            out("pricing_policy", loaded=True, child_pct_activity=format(by_type.get("activity"), "f")
                if by_type.get("activity") is not None else None, child_age_max=age_max)
        except Exception as exc:  # noqa: BLE001 — the contract % wins over the policy %, so pricing still proves B4
            by_type, age_max = None, None
            out("pricing_policy", loaded=False, error=type(exc).__name__)
        asks = [
            LineAsk("adult_only_24", sv, D24, None, 1, 0, 0),
            LineAsk("child_only_24", sv, D24, None, 0, 1, 0),
            LineAsk("family_23", sv, D23, None, 2, 1, 0),
            LineAsk("family_24", sv, D24, None, 2, 1, 0),
        ]
        costs = await price_lines(conn, asks, child_pct_by_type=by_type, child_age_max=age_max)
        nets = {a.line_ref: sum((amt for amt, _ in lc.costs), D("0")) for a, lc in zip(asks, costs)}
        notes = {a.line_ref: lc.child for a, lc in zip(asks, costs)}
        adult, child = nets["adult_only_24"], nets["child_only_24"]
        ratio = (child / adult) if adult else None
        expect("child_line_is_50_pct", adult == D("40.00") and child == D("20.00") and ratio == D("0.5"),
               adult_line_net=adult, child_line_net=child, child_to_adult=ratio,
               child_basis=notes["child_only_24"])
        expect("family_line_2a_1c", nets["family_23"] == D("100.00") == nets["family_24"]
               and notes["family_24"] == {"basis": "contract_pct", "pct": "50"},
               family_23_net=nets["family_23"], family_24_net=nets["family_24"], child_basis=notes["family_24"],
               currency=sorted({cur for lc in costs for _, cur in lc.costs}))
        supply_asks = [s for lc in costs for s in lc.supply]
        verdicts = iter(await restrictions.availability_many(conn, supply_asks, today=today))
        per_line = {}
        for a, lc in zip(asks, costs):
            vs = [next(verdicts) for _ in lc.supply]
            avail, note = quotes.supply_availability("available", vs, [s.on for s in lc.supply])
            per_line[a.line_ref] = {"engine": [v.reason for v in vs], "line_availability": avail, "supply_note": note}
        expect("quote_line_24_12_on_request",
               per_line["family_24"]["line_availability"] == "on_request"
               and per_line["family_24"]["supply_note"] == {"stop_sale": ["2026-12-24"]}
               and per_line["family_23"]["line_availability"] == "available"
               and per_line["family_23"]["supply_note"] is None,
               lines=per_line,
               note_on_contrast="quote_in keeps an sv: line without a departure on_request anyway; the engine verdict "
                                "and supply_availability are what change on 24/12")
    except Exception as exc:  # noqa: BLE001 — print the class and app code only, never a DB message (may echo data)
        failed.append("unexpected_error")
        tb = traceback.extract_tb(exc.__traceback__)
        out("unexpected_error", error=type(exc).__name__, code=getattr(exc, "code", None),
            where=[f"{os.path.basename(f.filename)}:{f.lineno}:{f.name}" for f in tb[-4:]])
    finally:
        await outer.rollback()
    try:
        left = await conn.fetchval("SELECT count(*) FROM booking.suppliers WHERE company_name = $1", SUPPLIER_NAME)
        left_r = await conn.fetchval(
            "SELECT count(*) FROM booking.supply_restrictions WHERE supplier_contract_id = $1::uuid",
            contract_id) if contract_id else 0
        expect("rolled_back_nothing_persists", left == 0 and left_r == 0, suppliers_left=left,
               restrictions_left=left_r)
    finally:
        await conn.close()
    print(json.dumps({"summary": "AA-1145 live proof", "ok": not failed, "failed": failed}), flush=True)
    return 0 if not failed else 1


sys.exit(asyncio.run(main()))
