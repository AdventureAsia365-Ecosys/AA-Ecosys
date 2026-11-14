"""S279 AA-1092 live check, part 2 (CRM api container): booking.b2b.v1 cross-tenant refusals through the CRM's own
M2M client (app.main.build_booking_client). Read-only GETs. Prints the HTTP outcome per case only, never a body,
a token or a URL. Ids are synthetic tenants / holds found by part 1 (b2b_fence.py).
"""
import asyncio
import sys
import uuid

sys.path.insert(0, "/app")

from app.booking.client import BookingRefusal, BookingUnavailable  # noqa: E402
from app.main import build_booking_client, build_tokens  # noqa: E402
from app.settings import load_settings  # noqa: E402

A = uuid.UUID("bab16039-a064-517f-a99f-172b729ad3c4")
B = uuid.UUID("00000000-0000-4000-8000-00000000c972")
C = uuid.UUID("1d3e25e0-497a-490f-8511-c89d8d7873e4")
SUSPENDED = uuid.UUID("1bae2159-671b-4f35-a782-e96ea4cbdd4a")
HOLD_A = "1d6de7ca-5181-4bd4-9d9e-ee162ce35d45"
HOLD_B = "ddf358f3-685a-449e-8584-b955e53dcbdd"
INV_C = "AAS-2026-000001"


async def case(label, expect, coro):
    try:
        await coro
        got = "200"
    except BookingRefusal as e:
        got = f"{e.status} {e.code}"
    except BookingUnavailable as e:
        got = f"unavailable {e.error_class}"
    ok = got.startswith(expect)
    print(f"{'PASS' if ok else 'FAIL'}  {label}: got {got}, expect {expect}")
    return ok


async def main():
    settings = load_settings()
    client = build_booking_client(settings, build_tokens(settings))
    if client is None:
        print("booking client not configured")
        return
    results = [
        await case("control: A reads its own hold", "200", client.get_hold(A, HOLD_A)),
        await case("control: B reads its own hold", "200", client.get_hold(B, HOLD_B)),
        await case("A reads B's hold", "404", client.get_hold(A, HOLD_B)),
        await case("B reads A's hold", "404", client.get_hold(B, HOLD_A)),
        await case("control: C reads its own invoice", "200", client.invoice(C, INV_C)),
        await case("A reads C's invoice", "404", client.invoice(A, INV_C)),
        await case("unknown tenant", "403 unknown_partner", client.billing_status(uuid.uuid4())),
        await case("suspended tenant", "403 unknown_partner", client.billing_status(SUSPENDED)),
        await case("control: A billing status", "200", client.billing_status(A)),
    ]
    print(f"{sum(results)}/{len(results)} PASS")


asyncio.run(main())
