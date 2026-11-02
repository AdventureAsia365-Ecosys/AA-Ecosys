---
id: OPS-08-s264-arch-video-gate
title: "Architecture video series: gate log (S264)"
description: "Gate results per architecture video (layers 1-4 automated, layer 5 human); counts and tool versions only, no script text."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-02
review_every_days: 30
related: [AA-1021]
---

# Architecture video series: gate log (S264, 02/11/2026)

One section per built episode. This page holds the gate result only (layer, status, hits, tool versions, date); the
scripts, the label profile, the deny-list and the videos stay outside the public repos (Drive, 01 Video). Gate and
pipeline: `tools/uat/arch/README.md`.

## Ep1 pilot

Built on 2026-11-02 from the ecosystem view. Layers 1-4 passed; layer 5 (independent review agent, then the tech lead
watching all four cuts) is pending, so nothing is uploaded or published yet.

| Layer | Status | Hits | Notes |
|---|---|---|---|
| 1 text + n-gram | PASS | 0 | strings: 140; ngram: 5-word phrases + internal-looking tokens vs public repos |
| 2 DOM before capture | PASS | 0 | frames_checked_before_capture: 21 |
| 3 OCR on frames | PASS | 0 | images: 230; note: ran on 230 images |
| 4 artifacts + metadata | PASS | 0 | files: 19 |
| 5 human review | PENDING | - | note: review agent + tech lead, checklist REVIEW.md |

| Cut | Aspect | Seconds | Keyframes | Cues | Chapters |
|---|---|---|---|---|---|
| master | 16:9 | 180.5 | 8 | 44 | 8 |
| short | 9:16 | 48.3 | 5 | 20 | 0 |
| x | 16:9 | 114.8 | 8 | 28 | 0 |
| linkedin | 4:5 | 76.8 | 5 | 26 | 0 |

Tools: ffmpeg ffmpeg version 6.1.1-3ubuntu5 Copyright (c) 2000-2023 the FFmpeg developers; tesseract tesseract 5.3.4; node v22.22.3; kokoro-onnx 0.6.1; playwright 1.59.1
