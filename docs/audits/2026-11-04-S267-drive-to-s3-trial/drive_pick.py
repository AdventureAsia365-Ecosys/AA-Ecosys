"""S267 AA-1044 step 1 — pick 2-3 tours with a Drive photo folder for the Drive -> S3 trial. READ-ONLY.

Runs in the CIS api container (orchestrator: tools/ecs/ecsx.sh .tmp-session/S267/trials/drive_pick.py).
  - DB: SELECT only on shared.place_photo (cis_app, DATABASE_URL, ssl=require). No write.
  - Drive: metadata only (files.get parents + files.list of the picked folders). No download. Free
    (Drive API standard use has no charge; quota units only).
  - No S3, no secret value printed (the Drive key is read by services.photos.drive.load_credentials()).

Where the folder ids live (checked S267): shared.place_photo has NO tour-folder id column. It keeps
drive_root_id (the country root, services/photos/sync.py CON_FOLDERS), folder_path (" › "-joined folder
names under the root), tour_folder (the last name) and drive_file_id. The tour folder id is resolved
here from Drive: the parent of one of the tour's files, else by walking folder_path names from the root.

Selection: tours with a matched tour_id, 5..25 photos, from different countries, smallest first, so the
picked set stays under the trial caps (60 files, 300 MB) of drive_to_s3.py.

Env (optional): MAX_TOURS (default 3), MIN_FILES (5), MAX_FILES_PER_TOUR (25).
Output: one PICK line per tour + a ready FOLDERS=... value for drive_to_s3.py.
"""
import asyncio
import os

import asyncpg

from services.photos.drive import API, FOLDER_MIME, DriveClient, load_credentials

MAX_TOURS = int(os.environ.get("MAX_TOURS", "3"))
MIN_FILES = int(os.environ.get("MIN_FILES", "5"))
MAX_FILES_PER_TOUR = int(os.environ.get("MAX_FILES_PER_TOUR", "25"))
CAP_FILES, CAP_BYTES = 60, 300 * 1024 * 1024        # same caps as drive_to_s3.py
LIST_FIELDS = "nextPageToken,files(id,name,mimeType,size,md5Checksum)"
MAX_DRIVE_CALLS = 60                                # metadata calls this script may make


class Calls:
    n = 0


async def drive_get(client: DriveClient, path: str, params: dict) -> dict:
    Calls.n += 1
    if Calls.n > MAX_DRIVE_CALLS:
        raise SystemExit(f"STOP: more than {MAX_DRIVE_CALLS} Drive metadata calls")
    p, h = await client._auth()
    p.update(params)
    return (await client._get(f"{API}/{path}", p, h)).json()


async def list_folder(client: DriveClient, folder_id: str) -> list[dict]:
    out, page = [], None
    while True:
        q = {"q": f"'{folder_id}' in parents and trashed = false", "fields": LIST_FIELDS, "pageSize": 1000,
             "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"}
        if page:
            q["pageToken"] = page
        body = await drive_get(client, "files", q)
        out += body.get("files", [])
        page = body.get("nextPageToken")
        if not page:
            return out


async def tour_folder_id(client: DriveClient, sample_file_id: str, root_id: str, folder_path: str) -> tuple:
    """(folder id, how) — the parent of one file, else the folder reached by name from the root."""
    try:
        body = await drive_get(client, f"files/{sample_file_id}", {"fields": "parents", "supportsAllDrives": "true"})
        parents = body.get("parents") or []
        if parents:
            return parents[0], "parent"
    except Exception as e:  # DriveError carries no URL / key
        print(f"WARN parents lookup failed: {str(e)[:120]}", flush=True)
    cur = root_id
    for name in [s.strip() for s in folder_path.split(" › ") if s.strip()]:
        hit = [f for f in await list_folder(client, cur) if f.get("mimeType") == FOLDER_MIME and f["name"].strip() == name]
        if len(hit) != 1:
            return None, f"walk-failed({len(hit)} folders named like the path step)"
        cur = hit[0]["id"]
    return cur, "walk"


async def main() -> None:
    conn = await asyncpg.connect(os.environ["DATABASE_URL"], ssl="require")
    try:
        rows = await conn.fetch(
            """SELECT tour_id::text AS tour_id, country, drive_root_id, folder_path,
                      count(*) AS n, coalesce(sum(bytes), 0) AS db_bytes, min(drive_file_id) AS sample_file_id
                 FROM shared.place_photo
                WHERE tour_id IS NOT NULL AND status <> 'rejected' AND folder_path <> ''
                GROUP BY tour_id, country, drive_root_id, folder_path
               HAVING count(*) BETWEEN $1 AND $2
                ORDER BY coalesce(sum(bytes), 0), count(*)""", MIN_FILES, MAX_FILES_PER_TOUR)
    finally:
        await conn.close()
    print(f"CANDIDATES {len(rows)} tour folders with {MIN_FILES}..{MAX_FILES_PER_TOUR} photos", flush=True)

    client = DriveClient(load_credentials())
    picks, countries, files_total, bytes_total = [], set(), 0, 0
    try:
        for r in rows:
            if len(picks) >= MAX_TOURS:
                break
            if r["country"] in countries or any(p["tour_id"] == r["tour_id"] for p in picks):
                continue
            fid, how = await tour_folder_id(client, r["sample_file_id"], r["drive_root_id"], r["folder_path"])
            if not fid:
                print(f"SKIP tour={r['tour_id']} country={r['country']} reason={how}", flush=True)
                continue
            children = await list_folder(client, fid)
            images = [f for f in children if f.get("mimeType", "").startswith("image/") and f.get("size")]
            size = sum(int(f["size"]) for f in images)
            if not images or files_total + len(images) > CAP_FILES or bytes_total + size > CAP_BYTES:
                print(f"SKIP tour={r['tour_id']} country={r['country']} images={len(images)} bytes={size} "
                      "reason=empty-or-over-trial-cap", flush=True)
                continue
            countries.add(r["country"])
            files_total += len(images)
            bytes_total += size
            picks.append({"tour_id": r["tour_id"], "folder_id": fid})
            print(f"PICK tour={r['tour_id']} country={r['country']} folder={fid} via={how} "
                  f"drive_images={len(images)} drive_bytes={size} db_rows={r['n']} db_bytes={r['db_bytes']} "
                  f"subfolders={sum(1 for f in children if f.get('mimeType') == FOLDER_MIME)}", flush=True)
    finally:
        await client.aclose()
    print(f"TOTAL picks={len(picks)} images={files_total} bytes={bytes_total} drive_calls={Calls.n}", flush=True)
    print("FOLDERS=" + ",".join(f"{p['tour_id']}:{p['folder_id']}" for p in picks), flush=True)


asyncio.run(main())
