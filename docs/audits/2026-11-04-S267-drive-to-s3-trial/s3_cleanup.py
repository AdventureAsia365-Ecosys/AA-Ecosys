"""S267 AA-1044 cleanup — delete the Drive -> S3 trial prefix, every version. WORKSTATION script (not ecsx).

Why here and not in the container: the CIS task role has no s3:DeleteObject on scripts/* (AA-CIS-Infra
modules/ecs/main.tf), and the bronze bucket is VERSIONED (modules/s3/main.tf), so a plain delete would only add
delete markers and keep the photos billed as noncurrent versions. This deletes each object version and each
delete marker under the exact prefix.

Dry run by default (lists what would go). APPLY=1 deletes. Scope guard: only keys under
scripts/experiments/s267-drive-to-s3/ (optionally one RUN), at most 1,000 versions.

Run (one line, MFA-cached admin credentials passed as env so boto3 does not prompt; pattern from the steering file):
  bash -c 'C=$(aws configure export-credentials --profile aa365-admin --format env-no-export </dev/null) ; grep -q "^AWS_ACCESS_KEY_ID=" <<<"$C" || exit 1 ; env -u AWS_PROFILE $(tr "\n" " " <<<"$C") AWS_REGION=us-west-1 python3 -I .tmp-session/S267/trials/s3_cleanup.py'
  ... same with APPLY=1 before python3 to delete.
Optional env: RUN=<run id> to delete one run only; BUCKET (default aa-cis-bronze-<acc2-account-id>).
"""
import os
import re
import sys

import boto3

PREFIX_ROOT = "scripts/experiments/s267-drive-to-s3/"
CAP = 1000
bucket = os.environ.get("BUCKET", "aa-cis-bronze-<acc2-account-id>")
run = os.environ.get("RUN", "")
if run and not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", run):
    sys.exit("bad RUN")
prefix = PREFIX_ROOT + (run + "/" if run else "")
apply = os.environ.get("APPLY") == "1"

s3 = boto3.client("s3", region_name=os.environ.get("AWS_REGION", "us-west-1"))
print("account", boto3.client("sts").get_caller_identity()["Account"], "bucket", bucket, "prefix", prefix)

items, nbytes = [], 0
for page in s3.get_paginator("list_object_versions").paginate(Bucket=bucket, Prefix=prefix):
    for v in page.get("Versions", []) + page.get("DeleteMarkers", []):
        if not v["Key"].startswith(PREFIX_ROOT):     # belt and braces: never outside the experiment prefix
            sys.exit(f"refusing: key outside the prefix: {v['Key']}")
        items.append({"Key": v["Key"], "VersionId": v["VersionId"]})
        nbytes += v.get("Size", 0)
    if len(items) > CAP:
        sys.exit(f"refusing: more than {CAP} versions under {prefix}")
print(f"versions+markers={len(items)} bytes={nbytes} apply={apply}")
for it in items[:5]:
    print("  e.g.", it["Key"][len(PREFIX_ROOT):])
if not apply or not items:
    sys.exit(0)
errors = 0
for i in range(0, len(items), 1000):
    r = s3.delete_objects(Bucket=bucket, Delete={"Objects": items[i:i + 1000], "Quiet": True})
    for e in r.get("Errors", []):
        errors += 1
        print("ERROR", e.get("Key", "")[len(PREFIX_ROOT):], e.get("Code"))
left = sum(len(p.get("Versions", [])) + len(p.get("DeleteMarkers", []))
           for p in s3.get_paginator("list_object_versions").paginate(Bucket=bucket, Prefix=prefix))
print(f"deleted={len(items) - errors} errors={errors} left_under_prefix={left}")
sys.exit(1 if errors or left else 0)
