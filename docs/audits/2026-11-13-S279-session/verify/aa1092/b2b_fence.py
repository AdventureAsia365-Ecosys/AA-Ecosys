"""S279 AA-1092 live check, part 1 (Booking container, role booking): the bk-049 RLS fence on booking.b2b_partners.

Read-only (every write attempt runs inside a transaction that is rolled back). Prints tenant ids (synthetic tenants),
counts and one hold id / invoice number per partner for part 2. No agency name, no personal data.
"""
import asyncio
import os

import asyncpg


async def main():
    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        parts = await c.fetch(
            "SELECT p.tenant_id::text AS tenant_id, p.status, p.m2m_client_id = min(p.m2m_client_id) OVER () AS same_client, "
            "(SELECT count(*) FROM booking.b2b_holds h WHERE h.partner_id = p.id) AS holds, "
            "(SELECT h.id::text FROM booking.b2b_holds h WHERE h.partner_id = p.id ORDER BY h.created_at DESC LIMIT 1) AS a_hold, "
            "(SELECT count(*) FROM booking.agency_invoice i WHERE i.party_tenant_id = p.tenant_id AND i.number IS NOT NULL) AS invoices, "
            "(SELECT i.number FROM booking.agency_invoice i WHERE i.party_tenant_id = p.tenant_id AND i.number IS NOT NULL "
            " ORDER BY i.number LIMIT 1) AS an_invoice "
            "FROM booking.b2b_partners p ORDER BY holds DESC, p.tenant_id")
        print("PARTNERS (unbound, back office view):", len(parts))
        for p in parts:
            print("  ", dict(p))
        active = [p for p in parts if p["status"] == "active"]
        if len(active) < 2:
            print("fewer than 2 active partners: no pair to test")
            return
        a, b = active[0]["tenant_id"], active[1]["tenant_id"]
        print("PAIR A =", a, " B =", b)
        tx = c.transaction()
        await tx.start()
        try:
            await c.execute("SELECT set_config('app.tenant_id', $1, true)", a)
            seen = await c.fetchval("SELECT count(*) FROM booking.b2b_partners")
            seen_b = await c.fetchval("SELECT count(*) FROM booking.b2b_partners WHERE tenant_id = $1::uuid", b)
            seen_a = await c.fetchval("SELECT count(*) FROM booking.b2b_partners WHERE tenant_id = $1::uuid", a)
            print(f"BOUND A: rows visible={seen} (expect 1), A row={seen_a} (expect 1), B row={seen_b} (expect 0)")
            for label, t in (("A", a), ("B", b)):
                try:
                    async with c.transaction():  # savepoint: a refusal does not abort the outer transaction
                        r = await c.execute(
                            "UPDATE booking.b2b_partners SET updated_at = updated_at WHERE tenant_id = $1::uuid", t)
                    print(f"BOUND A: UPDATE {label} row -> {r} (expect UPDATE 0)")
                except Exception as e:  # a policy refusal is also a pass
                    print(f"BOUND A: UPDATE {label} row -> refused {type(e).__name__}")
        finally:
            await tx.rollback()
        unbound = await c.fetchval("SELECT count(*) FROM booking.b2b_partners")
        print(f"UNBOUND after rollback: rows visible={unbound} (expect {len(parts)})")
    finally:
        await c.close()


asyncio.run(main())
