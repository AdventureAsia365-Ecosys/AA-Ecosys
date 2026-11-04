# AA-1044 — tour photos from Google Drive into S3, small trial (S267, 04/11/2026)

Tech lead request: test on a small sample, no change to current data, capped cost.

## What we found first

The copy already exists. The AA-708 photo sync (`services/photos/sync.py`) downloads every image under the CON
country roots with the Drive API key and stores the original plus WebP renditions in the bronze bucket
(`photos/<country>/…`), one `shared.place_photo` row each. So the question is the cut-over, not a second copy.

## Trial (copy of 3 tours into an experiment prefix, then deleted)

| Measure | Value |
|---|---|
| Tours / files / bytes | 3 tours (China, Mongolia, South Korea), 16 photos, 5.5 MB |
| Byte fidelity | 16/16 md5 equal to Drive, 16/16 equal after re-read from S3, 16/16 open as images; 0 thumbnail mismatches |
| Speed | 0.54 s per photo (p50), 9.4 s total |
| Cost | ~0.0003 USD in requests |
| Cleanup | experiment prefix deleted (16 objects, 0 left) |

No `shared.*` row, no `photos/` object and no pipeline setting changed (`copy_manifest.json`).

## Full picture (`estimate.txt`, Drive metadata vs the database)

- Drive: 3,232 images in 211 folders, 2.95 GB, 7 countries.
- Already in S3 with a database row: 3,232 of 3,232 (0 missing, 0 errors), 2.96 GB.
- 1,919 images are the same file reused across several tour folders (same md5).
- S3 Standard us-west-1: 0.026 USD per GB-month, so about 0.08 USD a month, already billed today.

## Recommendation

1. Read photos only from S3 everywhere (pipeline, apps): it is already complete and byte-exact.
2. Drive stays the content team's working folder for new photos; the sync only adds new or changed files.
3. Drop the Google API key only when the team uploads new photos straight to S3 (an admin upload page that writes
   the same `photos/` layout and `place_photo` row). Until then the key is needed to discover new photos.
4. Optional: deduplicate the 1,919 reused files by md5 in the storage layout (saves about 1 GB, ~0.03 USD a month).
