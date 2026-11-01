---
id: OPS-08-s262-crm-review-video
title: "CRM review video, recording results (S262)"
description: "Per-chunk verdicts, app versions and Drive location of the CRM review long video recorded on Dev on 1 Nov 2026."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [partner]
last_reviewed: 2026-11-01
review_every_days: 90
related: [AA-1014]
---

# CRM review video, recording results (S262, 01/11/2026)

- **Output:** `CRM-REVIEW_20261101_v1`.
  - Long video: 19 min 53 s, 21 chapters. Two audio tracks (EN Kokoro, VI VieNeu) and soft EN/VI subtitles. `_EN` / `_VI` copies.
  - Highlight: 8 min 30 s, chunks R01, R03, R04, R06, R08, R10, R11, R15.
  - Sync check: 131 subtitle cues, 0 without speech in their first second. Cost $0 (local TTS and ffmpeg).
- **Drive:** `01 Video/UAT (kiểm thử nghiệm thu)/dry-run/CRM-review-20261101/`, 20 files. `rclone check --one-way` reports 0 differences.
- **App versions:**
  - Chunks R10–R12 come from the morning take on AA-Partner `9ca6997`. R10 needs an invoice that went overdue on an earlier agency day, so it cannot run on a fresh run.
  - Every other chunk comes from a fresh run on `2787b45`. The long video was built with `--allow-sha-drift`, and its README says so.
- **Passes:**
  1. Morning record pass: 15/21.
  2. Scenario fixes (root #422).
  3. Fast pass on `eeccc98`: 22/22.
  4. Record pass on a fresh run: 17/20 + R10–R12 from the morning. R15 failed twice on the CSV export, then passed on retry.
- **Product bug found through R15:** an expired 30-minute access token is not renewed on raw-fetch downloads. The BFF answers 401 and the download fails. The fix is the AA-Partner `bffDownload` helper (lane w14).

Files: `run-all-record2.tsv` (the record-pass table), `CRM-REVIEW_20261101_v1.chapters.txt`, `CRM-REVIEW_20261101_v1.README.txt`.
