"""AA-806 follow-up controls: isolate what triggers GenericLFI_BODY. Small bodies (< 8 KB), random piece ids (404)."""
import datetime as dt
import json
import sys
import time
import uuid

import common as c
import payloads

OUT = sys.argv[1]
TH = {"Authorization": f"Bearer {c.tenant_token('atlas-hearth')}", "User-Agent": c.UA}

no_rel = payloads.RICH_INTRO.replace("../../travel-info/", "https://www.adventure.asia/travel-info/") \
    .replace("../destinations/", "https://www.adventure.asia/destinations/") \
    .replace("../images/", "https://www.adventure.asia/images/")
assert "../" not in no_rel
cases = [
    ("C3", "HTML intro with every ../ link made absolute (otherwise identical to C1)", {"content_text": no_rel}),
    ("C4", "one markdown link with ../ only", {"content_text": "See the [Hue guide](../destinations/vietnam/hue) first."}),
    ("C5", "one markdown link with ./ only", {"content_text": "See the [Hue guide](./destinations/vietnam/hue) first."}),
    ("C6", "prose with ellipsis and slashes, no ../",
     {"content_text": "Then... the pass. Day 3/4: 45 km/h downhill... and/or a boat. Hà Nội – Huế / Đà Nẵng ..."}),
    ("C7", "one HTML link with ../ only", {"content_text": '<p>See <a href="../destinations/vietnam/hue">the Huế guide</a>.</p>'}),
    ("C8", "one HTML img with ../ only", {"content_text": '<p><img src="../images/hai-van.jpg" alt="Hải Vân"></p>'}),
]
res = []
start = dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")
for cid, label, body in cases:
    data = json.dumps(body, ensure_ascii=False).encode()
    path = f"/v1/content-writing/pieces/{uuid.uuid4()}"
    r = c.requests.patch(f"{c.CIS_API}{path}", data=data,
                         headers={**TH, "Content-Type": "application/json; charset=utf-8", "x-aa806-test": cid}, timeout=60)
    res.append({"id": cid, "label": label, "path": path, "body_bytes": len(data), "status": r.status_code,
                "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")})
    print(cid, len(data), r.status_code)
    time.sleep(1)
json.dump({"window_start_utc": start, "requests": res}, open(OUT, "w"), indent=2, ensure_ascii=False)
