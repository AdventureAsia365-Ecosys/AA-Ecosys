"""S267 AA-1044 step 2 — copy the photos of the picked Drive folders into an S3 EXPERIMENT prefix.

Runs in the CIS api container (orchestrator):
  tools/ecs/ecsx.sh .tmp-session/S267/trials/drive_to_s3.py MODE=copy FOLDERS=<tour uuid>:<folder id>,... RUN=r1
  tools/ecs/ecsx.sh .tmp-session/S267/trials/drive_to_s3.py MODE=list RUN=r1          (read-only re-check)
(FOLDERS comes from drive_pick.py. VAR=value characters allowed by ecsx: A-Za-z0-9_.:,/@+- — uuids and Drive ids fit.)

What it touches (nothing else):
  - Drive: list the given folders (metadata) and download each image (the app's own DriveClient.download: the
    thumbnail "=s0" original first, alt=media fallback; key from services.photos.drive.load_credentials(), never
    printed).
  - S3: PutObject / GetObject / HeadObject / ListBucket under
        s3://<bronze>/scripts/experiments/s267-drive-to-s3/<RUN>/<tour id>/<drive file id>.<ext>
    only. The CIS task role holds s3:GetObject/PutObject/ListBucket on "*" (AA-CIS-Infra modules/ecs/main.tf
    ecs_task_policy) and no Deny on scripts/*, so the write is allowed. It holds NO s3:DeleteObject there (only
    photos/supply/*), so cleanup runs on the workstation: s3_cleanup.py (aa365-admin; the bucket is versioned,
    every version + delete marker under the prefix must go).
  - No DB access at all. No change to shared.place_photo, photos/ objects or any pipeline setting.
  - Never overwrites: a key that already exists is skipped (HeadObject first).

Integrity: Drive md5Checksum vs md5 of the downloaded bytes (if the "=s0" bytes differ, the file is downloaded
again with alt=media and the mismatch is reported); PutObject with Content-MD5 (S3 rejects a corrupted upload);
then GetObject again and md5 of the stored bytes; image opens with Pillow (verify + size).

Hard caps (in code, not env): 60 files, 300 MB downloaded, 400 S3 requests, 200 Drive calls. Cost of one full run:
~60 PUT + ~120 GET/HEAD + a few LIST = well under 0.01 USD (us-west-1: PUT/LIST 0.0055 USD per 1,000, GET 0.00044
USD per 1,000, Standard 0.026 USD per GB-month; data in from the internet free; S3 via the VPC gateway endpoint).
"""
import asyncio
import base64
import hashlib
import io
import json
import os
import re
import sys
import time

import boto3
from botocore.exceptions import ClientError

from services.photos.drive import API, DriveClient, load_credentials
from shared.aws_client.bronze import bronze_bucket

PREFIX_ROOT = "scripts/experiments/s267-drive-to-s3/"
CAP_FILES, CAP_BYTES, CAP_S3_REQ, CAP_DRIVE_CALLS = 60, 300 * 1024 * 1024, 400, 200
LIST_FIELDS = "nextPageToken,files(id,name,mimeType,size,md5Checksum,modifiedTime,thumbnailLink)"
MODE = os.environ.get("MODE", "list")
RUN = os.environ.get("RUN", "r1")
if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", RUN):
    sys.exit("RUN must be 1-32 chars of A-Za-z0-9_-")
PREFIX = f"{PREFIX_ROOT}{RUN}/"
ID_RE = re.compile(r"[A-Za-z0-9_-]{10,80}")
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


class Budget:
    s3 = 0
    drive = 0

    @classmethod
    def s3_call(cls):
        cls.s3 += 1
        if cls.s3 > CAP_S3_REQ:
            raise RuntimeError(f"S3 request cap {CAP_S3_REQ} reached")

    @classmethod
    def drive_call(cls):
        cls.drive += 1
        if cls.drive > CAP_DRIVE_CALLS:
            raise RuntimeError(f"Drive call cap {CAP_DRIVE_CALLS} reached")


def parse_folders(raw: str) -> list[tuple[str, str]]:
    out = []
    for item in [x for x in raw.split(",") if x]:
        tour, _, folder = item.partition(":")
        if not UUID_RE.fullmatch(tour) or not ID_RE.fullmatch(folder):
            sys.exit(f"bad FOLDERS item (want <tour uuid>:<drive folder id>): {item[:100]}")
        out.append((tour, folder))
    if not 1 <= len(out) <= 3:
        sys.exit("FOLDERS must name 1-3 tour folders")
    return out


def ext_of(name: str, mime: str) -> str:
    e = (name.rsplit(".", 1)[-1] if "." in name else "").lower()
    if e in ("jpg", "jpeg", "png", "webp", "gif", "heic", "tif", "tiff"):
        return e
    return {"image/png": "png", "image/webp": "webp", "image/gif": "gif"}.get(mime, "jpg")


async def list_images(client: DriveClient, folder_id: str) -> list[dict]:
    out, page = [], None
    while True:
        Budget.drive_call()
        p, h = await client._auth()
        p.update({"q": f"'{folder_id}' in parents and trashed = false", "fields": LIST_FIELDS, "pageSize": 1000,
                  "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"})
        if page:
            p["pageToken"] = page
        body = (await client._get(f"{API}/files", p, h)).json()
        out += [f for f in body.get("files", []) if f.get("mimeType", "").startswith("image/")]
        page = body.get("nextPageToken")
        if not page:
            return sorted(out, key=lambda f: f["name"])


async def download_alt_media(client: DriveClient, file_id: str) -> bytes:
    Budget.drive_call()
    p, h = await client._auth()
    p["alt"] = "media"
    return (await client._get(f"{API}/files/{file_id}", p, h)).content


def image_check(data: bytes) -> dict:
    from PIL import Image
    try:
        with Image.open(io.BytesIO(data)) as im:
            fmt, (w, h) = im.format, im.size
            im.verify()
        return {"opens": True, "format": fmt, "width": w, "height": h}
    except Exception as e:
        return {"opens": False, "error": type(e).__name__}


def exists(s3, bucket: str, key: str) -> bool:
    Budget.s3_call()
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
            return False
        raise


async def copy(s3, bucket: str) -> dict:
    folders = parse_folders(os.environ.get("FOLDERS", ""))
    client = DriveClient(load_credentials())
    m = {"mode": "copy", "bucket": bucket, "prefix": PREFIX, "tours": [], "files": 0, "copied": 0,
         "skipped_existing": 0, "skipped_cap": 0, "failures": [], "bytes": 0, "md5_drive_match": 0,
         "md5_s3_match": 0, "thumb_s0_md5_mismatch": 0, "opens": 0, "dup_md5_groups": 0, "seconds_total": 0.0}
    seen_md5: dict[str, list[str]] = {}
    per_photo: list[float] = []
    t_all = time.monotonic()
    try:
        for tour_id, folder_id in folders:
            images = await list_images(client, folder_id)
            t = {"tour_id": tour_id, "folder_id": folder_id, "images": len(images), "copied": 0, "bytes": 0}
            m["tours"].append(t)
            for f in images:
                fid, size, drive_md5 = f["id"], int(f.get("size") or 0), f.get("md5Checksum")
                m["files"] += 1
                if m["copied"] + m["skipped_existing"] >= CAP_FILES or m["bytes"] + size > CAP_BYTES or not size:
                    m["skipped_cap"] += 1
                    continue
                key = f"{PREFIX}{tour_id}/{fid}.{ext_of(f['name'], f.get('mimeType', ''))}"
                t0 = time.monotonic()
                try:
                    if exists(s3, bucket, key):
                        m["skipped_existing"] += 1
                        continue
                    Budget.drive_call()
                    data = await client.download(fid, f.get("thumbnailLink"))
                    got_md5 = hashlib.md5(data).hexdigest()
                    source = "app_download" if f.get("thumbnailLink") else "alt_media"   # thumb "=s0" first, alt=media fallback
                    if drive_md5 and got_md5 != drive_md5 and source == "app_download":
                        m["thumb_s0_md5_mismatch"] += 1
                        data = await download_alt_media(client, fid)
                        got_md5, source = hashlib.md5(data).hexdigest(), "alt_media_after_mismatch"
                    m["md5_drive_match"] += bool(drive_md5 and got_md5 == drive_md5)
                    chk = image_check(data)
                    m["opens"] += chk["opens"]
                    Budget.s3_call()
                    s3.put_object(
                        Bucket=bucket, Key=key, Body=data, ContentType=f.get("mimeType") or "image/jpeg",
                        ContentMD5=base64.b64encode(hashlib.md5(data).digest()).decode(),
                        Metadata={"drive-file-id": fid, "drive-md5": drive_md5 or "", "md5": got_md5,
                                  "size": str(len(data)), "tour-id": tour_id, "drive-folder-id": folder_id,
                                  "drive-modified": f.get("modifiedTime", ""), "source": source,
                                  "experiment": "AA-1044-S267"})
                    Budget.s3_call()
                    back = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
                    s3_ok = hashlib.md5(back).hexdigest() == got_md5
                    m["md5_s3_match"] += s3_ok
                    seen_md5.setdefault(got_md5, []).append(fid)
                    m["copied"] += 1
                    m["bytes"] += len(data)
                    t["copied"] += 1
                    t["bytes"] += len(data)
                    dt = time.monotonic() - t0
                    per_photo.append(dt)
                    print(f"OK {fid} bytes={len(data)} drive_md5_ok={bool(drive_md5 and got_md5 == drive_md5)} "
                          f"s3_md5_ok={s3_ok} opens={chk['opens']} fmt={chk.get('format')} "
                          f"{chk.get('width')}x{chk.get('height')} src={source} sec={dt:.2f}", flush=True)
                    del data, back
                except RuntimeError as e:   # a hard cap: stop the run
                    m["failures"].append({"file": fid, "error": str(e)})
                    raise
                except Exception as e:      # one bad file must not stop the run; no URL / key in the message
                    err = re.sub(r"key=[^&\s'\"]+", "key=***", f"{type(e).__name__}: {e}")[:200]
                    m["failures"].append({"file": fid, "error": err})
                    print(f"FAIL {fid} {err}", flush=True)
    except RuntimeError:
        pass
    finally:
        await client.aclose()
    m["seconds_total"] = round(time.monotonic() - t_all, 1)
    m["dup_md5_groups"] = sum(1 for v in seen_md5.values() if len(v) > 1)
    if per_photo:
        s = sorted(per_photo)
        m["sec_per_photo"] = {"mean": round(sum(s) / len(s), 2), "p50": round(s[len(s) // 2], 2),
                              "max": round(s[-1], 2)}
    m["requests"] = {"s3": Budget.s3, "drive": Budget.drive}
    # Request cost only (storage is prorated per hour and the prefix is deleted after the report).
    m["est_request_cost_usd"] = round(Budget.s3 * 0.0055 / 1000, 6)
    return m


def list_prefix(s3, bucket: str) -> dict:
    """Read-only: the objects under this RUN's prefix and their metadata (cleanup preview, verify after copy)."""
    out = {"mode": "list", "bucket": bucket, "prefix": PREFIX, "objects": 0, "bytes": 0, "md5_meta_vs_etag_ok": 0,
           "keys_sample": []}
    token = None
    while True:
        Budget.s3_call()
        kw = {"Bucket": bucket, "Prefix": PREFIX, "MaxKeys": 1000}
        if token:
            kw["ContinuationToken"] = token
        r = s3.list_objects_v2(**kw)
        for o in r.get("Contents", []):
            out["objects"] += 1
            out["bytes"] += o["Size"]
            if len(out["keys_sample"]) < 5:
                out["keys_sample"].append(o["Key"][len(PREFIX_ROOT):])
            if out["objects"] <= 60:
                Budget.s3_call()
                meta = s3.head_object(Bucket=bucket, Key=o["Key"]).get("Metadata", {})
                out["md5_meta_vs_etag_ok"] += meta.get("md5") == o["ETag"].strip('"')
        token = r.get("NextContinuationToken")
        if not token:
            break
    out["requests"] = {"s3": Budget.s3}
    return out


async def main() -> None:
    bucket = bronze_bucket()
    s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-west-1"))
    if MODE == "copy":
        result = await copy(s3, bucket)
    elif MODE == "list":
        result = list_prefix(s3, bucket)
    elif MODE == "cleanup":
        result = {"mode": "cleanup", "done": False,
                  "why": "the CIS task role has no s3:DeleteObject / DeleteObjectVersion on scripts/* and the bucket "
                         "is versioned; run .tmp-session/S267/trials/s3_cleanup.py on the workstation (aa365-admin)",
                  "preview": list_prefix(s3, bucket)}
    else:
        sys.exit("MODE must be copy | list | cleanup")
    print("MANIFEST " + json.dumps(result, default=str), flush=True)


asyncio.run(main())
