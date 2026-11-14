---
id: GUIDE-14-scale
title: "Pha 8: Mở rộng"
description: Chỉ mở rộng khi một điều kiện đo được yêu cầu, đòn bẩy rẻ nhất trước, và bật các biện pháp prod ở cổng G7.
type: how-to
status: draft
owner: nghiep
audience: [owner, cto, engineer, devops]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-operate, GUIDE-14-principles]
lang: vi
translation_of: docs/playbook/08-scale.md
---

# Pha 8: Mở rộng

**Mục tiêu:** chỉ mở rộng khi một điều kiện đo được yêu cầu, đòn bẩy rẻ nhất trước. **Người chịu trách nhiệm cuối:** chủ
doanh nghiệp, vì pha này tồn tại để duyệt chi tiêu mới; tech lead thiết kế thay đổi. **Theo:** Google SRE (SLO và chính
sách error budget), thói quen "đòn bẩy rẻ nhất trước" của FinOps, các mô hình môi trường cỡ startup (hai môi trường cho
tới khi có điều kiện kích hoạt).

## Điều kiện kích hoạt

Viết bảng điều kiện từ sớm; chỉ hành động khi một dòng xảy ra.

| Điều kiện (đo được) | Ngưỡng ví dụ | Đòn bẩy đầu tiên (rẻ nhất) | Đòn bẩy tiếp theo |
|---|---|---|---|
| CPU hay số kết nối cơ sở dữ liệu | liên tục trên 70 % trong một tuần | sửa các query nặng nhất; một connection pooler | instance lớn hơn |
| Hàng đợi hay job tồn đọng | job cũ nhất quá cửa sổ của nó, hằng ngày | chỉnh độ song song của worker | thêm một task worker |
| SLO độ trễ có nguy cơ | error budget dưới 25 % | cache, index, kích thước payload | scale out |
| Chi phí trên một đơn vị tăng | chi phí đơn vị tăng 30 % so với tháng trước | bỏ phần lãng phí tìm được khi rà soát | đổi kiến trúc |
| Bản phát hành prod đầu tiên hoặc tenant trả tiền đầu tiên | đã có ngày | bật các biện pháp prod bên dưới | - |

## Cổng G7: bật các biện pháp prod

Viết trong giai đoạn dev, bật cùng lúc khi bản phát hành prod đầu tiên hoặc tenant trả tiền đầu tiên có ngày (quyết định
D10 của bộ kit):

- [ ] Chính sách SLO và error budget có hiệu lực ([mẫu](../templates/slo-error-budget.vi.md)).
- [ ] Đặt trực sự cố và liên hệ khi có sự cố; alarm tới một người, không chỉ tới e-mail.
- [ ] Code owner được ép trên các đường dẫn rủi ro; tech lead duyệt merge rủi ro trước khi chúng vào.
- [ ] Agent chạy với một role quyền tối thiểu, không phải profile admin.
- [ ] Một môi trường prod ở tài khoản riêng, dựng từ bản thiết kế prod, có ngân sách riêng.
- [ ] Xoay các secret đã bị lộ hoặc dùng chung trong giai đoạn dev.

## Sản phẩm bàn giao

- Bảng điều kiện kích hoạt và rà soát dung lượng ([rà soát chi phí và dung lượng](../templates/cost-report.md)).
- Bản thiết kế prod (môi trường, tài khoản, nơi lưu dữ liệu, backup và mục tiêu khôi phục).
- Công tắc quản trị ở trên, được ghi thành một quyết định có ngày.

## Lỗi hay gặp

- Mở rộng theo cảm giác hay một đỉnh đơn lẻ.
- Mua instance lớn hơn trước khi sửa query nặng nhất.
- Bật các biện pháp prod từng cái một, nên đội không bao giờ biết luật nào đang áp dụng.
- Dựng prod trước khi có ngày go-live.
