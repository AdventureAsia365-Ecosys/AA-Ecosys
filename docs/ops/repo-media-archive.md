---
id: OPS-08-repo-media-archive
title: Repository media archive (screenshots, design exports, binaries)
description: Where the full-size screenshots, Figma exports and other binary files that left the root repository in the AA-1161 history rewrite are kept, and how to fetch one.
type: reference
status: active
owner: nghiep
audience: [engineer, devops, agent]
last_reviewed: 2026-11-21
review_every_days: 180
---

# Repository media archive

The root repository keeps code, tests, config, text docs and a few key screenshots, compressed (AA-1161, root
`tools/repo/lean_guard.py`). Full image sets, Figma exports and other binaries live in the **private archive bucket of
the Dev infrastructure account** (the "bronze" bucket, server-side encrypted, all public access blocked), never on a
personal drive.

| What | Where in the bucket | Since |
|---|---|---|
| Every media file that was in the root repository on 21/11/2026 (3,909 files, 922 MB: PNG, JPEG, SVG, PDF, DOCX, XLSX), at its original size | `archive/repo-media/AA-Ecosys/<the same path as in the repository>` | S287, 21/11/2026 |
| The Booking Figma screen exports, formerly `docs/AAA/figma_AAA/` (120 PNG files, 387 MB) | `archive/repo-media/AA-Ecosys/docs/AAA/figma_AAA/` | S287 |
| A full backup of the root and Infra repositories before the history rewrite (git bundles of every ref, with SHA-256 checksums) | `archive/repo-backups/2026-11-21-aa1161/` | S287 |

The `archive/` prefix has no expiry rule (objects move to Infrequent Access over time). The short-lived
`audit-assets/` prefix (60 days) is for evidence sets that do not need to outlive a review.

## What changed in the repository

- `docs/AAA/figma_AAA/` left the repository. Pages that cite it (for example the S236 Booking UI spec) now point here.
- Screenshots that no page linked to were removed from `docs/audits/`; the ones that a page links to stay, compressed
  (`tools/docs/compress_images.py`, PNG quantized to 256 colours). The original full-size file of each one is in the
  archive at the same path.
- The history of the root repository was rewritten so that only the media still in the tree remains, and the retired
  Lambda zips (`dist/lambdas/*.zip`) left the history of the Infra repository. Commit SHAs changed on both; links to a PR
  number still work.

## Fetch a file

With the Dev infrastructure profile (MFA), copy one file or a whole folder; replace `<bucket>` with the bronze archive
bucket name (`terraform output` in `accounts/aa365` of the Infra repository, or the S3 console):

```bash
aws s3 cp s3://<bucket>/archive/repo-media/AA-Ecosys/docs/audits/<folder>/<file>.png . --profile aa365-admin --region us-west-1
aws s3 sync s3://<bucket>/archive/repo-media/AA-Ecosys/docs/AAA/figma_AAA/ ./figma_AAA --profile aa365-admin --region us-west-1
```

## New evidence

New screenshots follow `docs/STYLE.md`: key shots only, compressed, under 300 KB each in the repository; a full set
goes to this archive (or to `audit-assets/` when it only matters for a short review) and the audit page says where.
