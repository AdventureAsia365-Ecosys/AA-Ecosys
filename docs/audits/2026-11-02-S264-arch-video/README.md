---
id: OPS-08-s264-arch-video-gate
title: "Architecture video series: gate log (S264)"
description: "Gate results per architecture video (layers 1-4 automated, layer 5 human): layer, status and hit count only, no script text."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-02
review_every_days: 30
related: [AA-1021]
---

# Architecture video series: gate log (S264)

One section per built episode. This page holds the gate result only: layer, status and hit count, copied from the
build's `gate-summary.md`. Cut lengths, build dates, counts, tool versions, the scripts, the sketches, the deny-list and
the videos stay outside the public repos (Drive, 01 Video), because they would let anyone match this repo to the
videos. Gate and pipeline: `tools/uat/arch/README.md`.

## Ep1 pilot

Layers 1-4 passed on the rebuild after the S264 review fixes (per-episode diagram sketch, drawn labels through the full
text check, hyphenated-token and identity checks). Layer 5 (independent review agent, then the tech lead watching all
four cuts) is pending, so nothing is uploaded or published yet.

| Layer | Status | Hits |
|---|---|---|
| 1 text + n-gram | PASS | 0 |
| 2 DOM before capture | PASS | 0 |
| 3 OCR on frames | PASS | 0 |
| 4 artifacts + metadata | PASS | 0 |
| 5 human review | PENDING | - |
