"""S275 AA-741 phase 2: why the blog pieces of the 4 audit tenants are held. Counts only (gate names, codes, F9
classes), no piece text. Read only. Env: P2_SINCE (iso)."""
import asyncio
import collections
import datetime as dt
import json
import os
import sys

import asyncpg

sys.path.insert(0, "/app")
from services.acp_content_writing.gate_eval import failing_gates, hold_reason_codes, f9_class_counts  # noqa: E402

AUDIT = ["audit-atlas-hearth", "audit-terra-family", "audit-trail-pulse", "audit-wildkind-travel"]


async def main():
    since = dt.datetime.fromisoformat(os.environ["P2_SINCE"].replace("Z", "+00:00"))
    c = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    rows = await c.fetch(
        "SELECT cp.status, split_part(coalesce(cp.held_reason, ''), ':', 1) AS hr_head, cp.gate_ledger "
        "FROM acp_shared.content_piece cp JOIN shared.tenants t ON t.tenant_id = cp.tenant_id "
        "WHERE t.slug = ANY($1::text[]) AND cp.channel = 'blog' AND cp.created_at >= $2", AUDIT, since)
    st = collections.Counter(r["status"] for r in rows)
    heads, codes, gates, f9 = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    only = collections.Counter()
    for r in rows:
        if r["status"] != "held":
            continue
        led = r["gate_ledger"]
        led = json.loads(led) if isinstance(led, str) else led
        heads[r["hr_head"][:40]] += 1
        fg = failing_gates(led)
        hold = [g for g in fg if g["may_hold"]]
        for g in hold:
            gates[g["source"]] += 1
        only[",".join(sorted({g["source"] for g in hold})) or "-"] += 1
        for code in hold_reason_codes(led, None):
            codes[code] += 1
        for k, v in f9_class_counts(fg).items():
            f9[k] += v
    print("STATUS", dict(st))
    print("HELD_REASON_HEAD", dict(heads.most_common()))
    print("HOLD_GATES", dict(gates.most_common()))
    print("HOLD_GATE_SETS", dict(only.most_common(12)))
    print("HOLD_CODES", dict(codes.most_common()))
    print("F9_CLASSES", dict(f9.most_common()))
    await c.close()


asyncio.run(main())
