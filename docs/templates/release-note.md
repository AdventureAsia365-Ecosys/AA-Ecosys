---
id: APP-07-app-vx-y-z
title: <App> <vX.Y.Z> — <YYYY-MM-DD>
description: <One sentence - the main user-visible change in this release.>
type: report
status: draft
owner: nghiep
audience: [owner, pm, engineer]
applies_to: [replace-me]
last_reviewed: 2026-10-19
related: [APP-07, AA-891]
---

# <App> <vX.Y.Z> — <YYYY-MM-DD>

<!-- Release note = the business view of a release. CHANGELOG.md (written by release-please, AA-891) is the
technical view; link it, do not copy it. One note per app release (tag vX.Y.Z). It is the source of the Jira draft
for the business owner (skill/aa-jira-update): Claude drafts, the tech lead approves, then the Vietnamese lines are posted.

How to fill it from the CHANGELOG section `## [X.Y.Z]` of the app:

1. `### Features` lines -> one "Feature" block each, only for features verified live on Dev (skill/aa-ship
   section 3). Merge lines that are one feature for the user. Skip features with no user-visible change.
2. `### Bug Fixes` lines that a user could notice -> "Fixed / Đã sửa". Internal fixes stay technical.
3. `### ⚠ BREAKING CHANGES` lines that change what a user does -> "Changes in how to use it / Thay đổi cách dùng".
4. Everything else in the section (`### Performance Improvements`, `### Dependencies`, `### Reverts`) ->
   "Technical changes" only, as the CHANGELOG link. `refactor`, `docs`, `chore`, `ci`, `test`, `build` and `style`
   commits are hidden by release-please's default changelog sections, so they never appear there.
5. Rewrite every line in business words: no Linear keys, no commit scopes or hashes, no table or function names.
6. 3 to 6 feature blocks at most; split a larger release over two Jira comments.
7. Each section: English line, then the Vietnamese line with the same content (bilingual EN-VI, guide for the owner,
   .kiro/steering/language-convention.md). Vietnamese dates are dd/mm/yyyy. No "ạ", no "như đã hứa".

Delete this comment and every unused block before saving the note. -->

## Summary / Tóm tắt

- EN: <One or two sentences: what this release gives the business, and when it went live on Dev.>
- VI: <Một hoặc hai câu: bản phát hành này mang lại gì cho công việc, lên Dev ngày dd/mm/yyyy.>

## Feature: <short name> / Tính năng: <tên ngắn>

<!-- One block per "Features" entry kept from the CHANGELOG. Copy this whole block for the next feature. -->

### Feature built / Tính năng đã làm

- EN: <What now exists, written from the user's side: who uses it and what it does for them.>
- VI: <Điều đã có, viết từ phía người dùng: ai dùng và nó giúp gì.>

### What you can try / Chị có thể thử

1. EN: <Open page X, signed in as Y.> — VI: <Mở trang X, đăng nhập bằng Y.>
2. EN: <Do Z; you should see W.> — VI: <Làm Z; sẽ thấy W.>

### Links / Liên kết

- <Page or screen URL on Dev> — <EN label> / <nhãn VI>
- <Screenshot or UAT video on Google Drive, if any> — <EN label> / <nhãn VI>

## Changes in how to use it / Thay đổi cách dùng

- EN: <What a user must now do differently, or "None".>
- VI: <Người dùng phải làm gì khác, hoặc "Không có".>

## Fixed / Đã sửa

- EN: <A fixed problem, described as the user saw it, or "None".>
- VI: <Lỗi đã sửa, viết theo điều người dùng thấy, hoặc "Không có".>

## Technical changes

- CHANGELOG: <link to the `## [X.Y.Z]` section of CHANGELOG.md or to the GitHub Release vX.Y.Z>.
- Deployed SHA: <short sha> (`git_sha` from the app's health endpoint: CIS `/health`, Booking `/booking/health`,
  TripPlanner `/api/health`), migrations: <owner key list or none>, contract versions: <none / name vN>.

## Known issues / Vấn đề còn lại

- EN: <Issue and workaround, or "None known".>
- VI: <Vấn đề và cách xử lý tạm, hoặc "Chưa thấy vấn đề nào".>

## Jira draft (VI)

<!-- The Vietnamese lines above, assembled for the Jira comment. Post only after the tech lead approves the exact text
(skill/aa-jira-update rule 1); the mention is the ADF/HTML node from that skill, not plain "@thule". -->

```text
@thule <App> bản <X.Y.Z> đã lên Dev ngày <dd/mm/yyyy>:

Tính năng mới:
- <Tính năng: một dòng VI>. Chị thử: <bước ngắn>. Link: <url>
- ...

Đã sửa:
- <dòng VI, hoặc bỏ mục này>

Thay đổi cách dùng: <dòng VI hoặc "Không có">
```
