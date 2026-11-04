"""S267 AA-1044 step 3 — size of the full Drive -> S3 move. READ-ONLY.

Runs in the CIS api container (orchestrator: tools/ecs/ecsx.sh .tmp-session/S267/trials/drive_estimate.py).
  - DB: SELECT only on shared.place_photo (what the AA-708 photo sync already stored in S3: originals under
    photos/<country slug>/<file id>-orig.<ext> + WebP renditions; `bytes` = the original's size).
  - Drive: metadata only (files.list) of every CON country root in services/photos/sync.py CON_FOLDERS, walked
    to the same depth as the sync (3). No download. Free (Drive API standard use has no charge).
  - No S3, no write, no secret value printed.

Caps: 400 Drive list calls, 50,000 files (prints CAPPED=true when hit, so the totals are a lower bound).
Price used: S3 Standard us-west-1 0.026 USD per GB-month, first 50 TB (AWS Price List API, AmazonS3 us-west-1,
publication 2026-10-15; https://aws.amazon.com/s3/pricing/). PUT 0.0055 USD per 1,000.
"""
import asyncio
import os

import asyncpg

from services.photos.drive import API, FOLDER_MIME, DriveClient, load_credentials
from services.photos.sync import CON_FOLDERS

MAX_LIST_CALLS, MAX_FILES, MAX_DEPTH = 400, 50_000, 3
FIELDS = "nextPageToken,files(id,mimeType,size,md5Checksum)"
USD_GB_MONTH, USD_PUT_1K = 0.026, 0.0055
GB = 1024 ** 3


class Calls:
    n = 0
    capped = False


async def list_children(client: DriveClient, folder_id: str) -> list[dict]:
    out, page = [], None
    while True:
        if Calls.n >= MAX_LIST_CALLS:
            Calls.capped = True
            return out
        Calls.n += 1
        p, h = await client._auth()
        p.update({"q": f"'{folder_id}' in parents and trashed = false", "fields": FIELDS, "pageSize": 1000,
                  "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"})
        if page:
            p["pageToken"] = page
        body = (await client._get(f"{API}/files", p, h)).json()
        out += body.get("files", [])
        page = body.get("nextPageToken")
        if not page:
            return out
        await asyncio.sleep(0.1)


async def walk_root(client: DriveClient, root_id: str) -> dict:
    s = {"folders": 0, "image_folders": 0, "images": 0, "bytes": 0, "non_image_files": 0, "ids": set(), "md5": {}}
    stack = [(root_id, 0)]
    while stack and not Calls.capped:
        fid, depth = stack.pop()
        kids = await list_children(client, fid)
        has_img = False
        for f in kids:
            if f.get("mimeType") == FOLDER_MIME:
                s["folders"] += 1
                if depth < MAX_DEPTH:
                    stack.append((f["id"], depth + 1))
            elif f.get("mimeType", "").startswith("image/"):
                has_img = True
                s["images"] += 1
                s["bytes"] += int(f.get("size") or 0)
                s["ids"].add(f["id"])
                if f.get("md5Checksum"):
                    s["md5"][f["md5Checksum"]] = s["md5"].get(f["md5Checksum"], 0) + 1
                if len(s["ids"]) >= MAX_FILES:
                    Calls.capped = True
            else:
                s["non_image_files"] += 1
        s["image_folders"] += has_img
        await asyncio.sleep(0.05)
    return s


async def main() -> None:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        db = {r["country"]: dict(r) for r in await conn.fetch(
            """SELECT country, count(*) AS rows, count(*) FILTER (WHERE s3_key_original IS NOT NULL) AS with_original,
                      coalesce(sum(bytes) FILTER (WHERE s3_key_original IS NOT NULL), 0) AS original_bytes,
                      count(*) FILTER (WHERE status = 'matched') AS matched,
                      count(*) FILTER (WHERE status = 'error') AS errors,
                      count(DISTINCT tour_folder) AS tour_folders, count(DISTINCT tour_id) AS tours,
                      count(DISTINCT sha256) FILTER (WHERE sha256 IS NOT NULL) AS distinct_sha256
                 FROM shared.place_photo GROUP BY country ORDER BY country""")}
        db_ids = {r["drive_file_id"] for r in await conn.fetch("SELECT drive_file_id FROM shared.place_photo")}
    finally:
        await conn.close()

    client = DriveClient(load_credentials())
    tot = {"images": 0, "bytes": 0, "folders": 0, "image_folders": 0, "not_in_db": 0, "dup_files": 0}
    try:
        for c in CON_FOLDERS:
            if Calls.capped:
                print(f"COUNTRY {c['country']} not walked (cap reached)", flush=True)
                continue
            s = await walk_root(client, c["folder_id"])
            dups = sum(n - 1 for n in s["md5"].values() if n > 1)
            not_in_db = len(s["ids"] - db_ids)
            d = db.get(c["country"], {})
            print(f"COUNTRY {c['country']}: drive images={s['images']} bytes={s['bytes']} "
                  f"({s['bytes'] / GB:.2f} GB) folders={s['folders']} image_folders={s['image_folders']} "
                  f"non_image={s['non_image_files']} same_md5_extra_copies={dups} not_in_db={not_in_db} | "
                  f"db rows={d.get('rows', 0)} with_original_in_s3={d.get('with_original', 0)} "
                  f"original_bytes={d.get('original_bytes', 0)} matched={d.get('matched', 0)} "
                  f"errors={d.get('errors', 0)} tours={d.get('tours', 0)}", flush=True)
            for k in ("images", "bytes", "folders", "image_folders"):
                tot[k] += s[k]
            tot["not_in_db"] += not_in_db
            tot["dup_files"] += dups
    finally:
        await client.aclose()

    db_rows = sum(d["rows"] for d in db.values())
    db_orig = sum(d["with_original"] for d in db.values())
    db_bytes = sum(d["original_bytes"] for d in db.values())
    gb = tot["bytes"] / GB
    print(f"TOTAL drive images={tot['images']} bytes={tot['bytes']} ({gb:.2f} GB) folders={tot['folders']} "
          f"image_folders={tot['image_folders']} same_md5_extra_copies={tot['dup_files']} "
          f"not_yet_in_db={tot['not_in_db']} drive_list_calls={Calls.n} CAPPED={Calls.capped}", flush=True)
    print(f"TOTAL db rows={db_rows} with_original_in_s3={db_orig} original_bytes={db_bytes} "
          f"({db_bytes / GB:.2f} GB) countries_in_db={sorted(db)}", flush=True)
    print(f"COST originals_only: {gb:.2f} GB x {USD_GB_MONTH} = {gb * USD_GB_MONTH:.3f} USD/month; "
          f"one-off PUTs {tot['images']} x {USD_PUT_1K}/1000 = {tot['images'] * USD_PUT_1K / 1000:.4f} USD; "
          f"data in from the internet 0 USD", flush=True)
    print(f"COST already_in_s3 (AA-708 originals): {db_bytes / GB:.2f} GB x {USD_GB_MONTH} = "
          f"{float(db_bytes) / GB * USD_GB_MONTH:.3f} USD/month (already billed today)", flush=True)


asyncio.run(main())
