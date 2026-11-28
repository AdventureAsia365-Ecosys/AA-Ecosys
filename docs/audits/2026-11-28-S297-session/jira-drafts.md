---
id: OPS-08-s297-jira-drafts
title: "S297 Jira drafts (Vietnamese, for the business owner)"
description: "Drafts of the S297 Jira comments, approved once by the tech lead before posting; posting record."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-28
review_every_days: 30
related: [AA-1191]
---

# S297 Jira drafts

Posting method (S297): Jira REST v2 as the tech lead (API token), not the Atlassian connector, so the comment shows
the tech lead's name only. Mention by account id, images as attachments.

## J1 — PR-31 (Price system): one currency, USD

**Why here:** the USD-only decision of 27/11 belongs to the price system; the last PR-31 comment (10716) is about
agency prices. **Where:** comment on PR-31. **Images:** 3, in this order.

> @thule Từ 28/11 (Dev), toàn hệ thống chỉ dùng một tiền tệ là USD, theo quyết định ngày 27/11:
>
> 1. **Một cài đặt chung "Enabled currencies"** (CIS › Platform › Settings), đang để chỉ USD. Đổi cài đặt này cần
>    người thứ hai duyệt và được ghi lịch sử. Cả ba app (CIS, Booking, CRM cho đại lý) đọc cùng một cài đặt.
> 2. **Không còn VND trên giao diện:** bảng gói và ô giá gói (CIS), Tenant 360, điều khoản thanh toán và hoá đơn phí
>    phần mềm (Booking), trang Billing, dashboard và báo giá của đại lý (CRM) đều chỉ hiện USD; ô chọn tiền tệ được
>    ẩn khi chỉ có một tiền tệ.
> 3. **Hệ thống từ chối lưu số tiền bằng VND** khi VND chưa được bật.
> 4. **Dữ liệu cũ giữ nguyên:** giá VND đã nhập trước đây vẫn được lưu nhưng không hiện; nếu sau này cần hoá đơn VND
>    (ví dụ đại lý Việt Nam theo yêu cầu của kế toán hoặc luật sư) thì chỉ cần bật VND trong cài đặt, không phải làm
>    lại phần mềm.
>
> Đã kiểm trên Dev ngày 28/11: 27 màn hình của 3 app, không còn VND.
>
> Ảnh theo thứ tự: (1) cài đặt "Enabled currencies" đang để USD, (2) ô giá của một gói chỉ còn USD, (3) trang Billing
> của đại lý chỉ hiện USD.

| Claim | Evidence |
|---|---|
| One setting, maker-checker, audited | CIS 497 applied 28/11 (wave, `apply cis/497: applied`); `ui/02e-cis-settings-enabled-currencies-1440-light.png` (value `["USD"]`) |
| No VND on CIS / Booking / CRM screens | `ui/evidence.md` items 2–4, 27 shots, 0 console errors (the Booking billing tiles fix ships with Booking #347 before posting) |
| API refuses VND writes | CI tests of CIS #1731, Booking #345, Partner #411 (422 `currency_not_enabled`); not exercised live (writes) |
| Stored VND kept | DRY RUN 28/11 (DB Migrate run 46125783463): 7 plans keep VND prices, 1 draft invoice, 4 accepted proposals of one test agency; nothing converted |

Images: `ui/02e-cis-settings-enabled-currencies-1440-light.png`, `ui/02b-cis-plan-drawer-1440-light.png`,
`ui/04a-crm-studio-billing-1440-light.png`.

## Posting record

- J1: approved by the tech lead ("đăng", 28/11 ~17:15 +07); posted 28/11 10:16 UTC as PR-31 comment **10717** (author: the tech lead; 3 images attached and embedded; mention rendered as a mention node), through Jira REST v2 with the tech lead's API token.
