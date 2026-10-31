---
id: AUD-S262-tl-decisions
title: "Tech lead decisions on the S261 architecture review TL items (S262)"
description: "Rule given by the tech lead on 31/10/2026 for TL-1…TL-25: free and simple items approved and done now; paid or complex items not approved, noted for later."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-804, AA-997, AA-1004, AA-873]
---

# Quyết định TL của review kiến trúc S261 (S262, 31/10/2026)

Nguồn: `docs/audits/2026-10-31-S261-architecture-review/README.md` §7.2.

Luật tech lead (nguyên văn, 31/10 ~19:20 +07): *"các TL: cái nào không tốn tiền thì duyệt làm luôn và kỹ thuật không
quá phức tạp; còn cái nào tốn thêm tiền và phức tạp thì không duyệt, ghi note tính sau."*

Agent phân loại theo đúng luật đó (0 USD và cỡ S / vài giờ = duyệt; tốn tiền định kỳ, lượt trả phí, hoặc cỡ M/L nhiều
ngày = để sau). Tech lead đảo bất kỳ dòng nào thì sửa bảng này.

## Duyệt — làm trong S262

| # | Nội dung | Làm gì trong S262 |
|---|---|---|
| TL-1 | Chấp nhận ADR 0018, giữ us-west-1 | ADR 0018 → Accepted (lý do region ghi trong ADR); C7.2a/c, DM-9.6, Infra CONTEXT.md cùng root/Infra PR |
| TL-3 (một phần) | Trần In Progress | ≤ 8 issue In Progress toàn team (luật trong `aa-session`). Phần đóng băng phạm vi CRM W6–W8 / AA-1003 là quyết định sản phẩm → để sau |
| TL-4 | Mốc theo ngày, sổ rủi ro, Done-when đóng băng, Done-with-scope chính thức | Trường `due` + `risks[]` trong `plan.json`; luật Done-with-scope vào `aa-ship`; rà cùng báo cáo tuần |
| TL-10 (phần luật) | Judge chưa hiệu chuẩn không làm cổng | Ghi luật: judge chỉ làm cổng khi ≥ 30 cặp có nhãn người, ≥ 8 mỗi lớp; kappa 0,562 trên 13 cặp chỉ là ứng viên. Bộ nhãn 40 mục (2 giờ tech lead) để sau |
| TL-11 | Đóng băng tính năng eval / học tới khi T9 blog đi trọn một vòng | Gom AA-919/920/921/922/923, AA-790, AA-1000 vào một track "Writing memory + eval (đóng băng)"; ghi chú Linear; AA-922 rút khỏi S262 |
| TL-13 | Thứ tự lát còn lại của cổng | `prompt_version`, lifecycle, canary (0 USD) → S8 lõi chung → S11 khi cổng chạy; S7 batch hoãn (chỉ giữ phần ghi sổ cho batch) |
| TL-15 | ADR 0009 + AI Use Register v0 | Register v0 (mỗi stage: chủ, nguồn, phạm vi dữ liệu, ngân sách, công tắc tắt) + bảng OWASP LLM 2025; khớp danh sách nhà cung cấp cho AA-820 |
| TL-24 | Site TripPlanner Dev | `noindex` + dòng "bản xem trước" tới go-live; báo business owner một dòng (mất giá trị SEO host Dev) |
| TL-25 | AA-997 | Done-with-scope, bật `hide_flagged` sau audit cuối 01/11; báo business owner con số phủ bản đồ; geocoder trả phí chỉ khi pin ẩn hại sản phẩm |

## Đã xong / giữ quyết định trước

| # | Trạng thái |
|---|---|
| TL-6 | Đã vá (Infra #541, S261) |
| TL-7 | Tech lead đã chốt riêng 31/10 "chưa làm lúc này" → giữ nguyên, không nhắc |
| TL-9 | Mật khẩu DataForSEO đã xoay 25/10 (S251) |

## Không duyệt — ghi để tính sau (tốn tiền hoặc phức tạp)

| # | Nội dung | Lý do để sau | Khi nào xét lại |
|---|---|---|---|
| TL-2 | Tham số hoá Terraform cho prod | Cỡ L | Khi có ngày go-live |
| TL-3 (phần còn lại) | Đóng băng CRM W6–W8, AA-1003; ≥ 60 % năng lực cho beachhead | Quyết định phạm vi sản phẩm | Cùng business owner |
| TL-5 | Gộp nguồn trạng thái (Linear duy nhất, plan.json sinh tự động) | Cỡ M, 1–2 phiên | Khi rảnh giữa các mốc |
| TL-8 | Agent mặc định role hẹp `aa365-agent` | Thiết kế IAM + đổi luồng làm việc | Trước prod |
| TL-12 | Thứ tự + trần các lượt trả phí đầu tiên khi LLM có lại (~13 USD) | Tốn tiền | Khi acc3 hoặc khoá Anthropic có lại |
| TL-14 | Registry không gian embedding + re-embed thử | Tốn tiền (< 1 USD), ~1 ngày | Trước khi đổi billing/org của acc2 (01/12) |
| TL-16 | Baseline schema prod + bánh cóc dump đêm + retention cả lô | 3–5 ngày | Trước prod |
| TL-17 (phần CI) | Check `risk-review` bắt buộc | Cỡ M trên 4 repo; review PR rủi ro vẫn làm như hiện nay | Trước prod |
| TL-18 | Luật agent vào repo + lint chỉ dẫn | Cỡ M | Khi rảnh |
| TL-19 | Tầng eval xác định 0 USD bắt buộc | Cỡ M | Sau khi cổng AI xong |
| TL-20 | Ai sở hữu task def ECS | 1–2 ngày | Trước khi viết Deploy Prod |
| TL-21 | Kênh cảnh báo critical (0–3 USD/tháng) | Tốn tiền | Trước prod |
| TL-22 | Bản sao ngoài acc2 (1–5 USD/tháng) | Tốn tiền | Trước lần dời org 01/12 |
| TL-23 | Topology LLM prod | Tốn tiền + phức tạp | Trước prod |
