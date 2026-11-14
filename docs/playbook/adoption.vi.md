---
id: GUIDE-14-adoption
title: Áp dụng playbook
description: Checklist ngày đầu, kế hoạch 30 / 60 / 90 ngày, chi phí chạy của một dự án mới và cách chính bộ kit được nghiệm thu.
type: how-to
status: draft
owner: nghiep
audience: [owner, cto, pm, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-discovery, GUIDE-14-setup, GUIDE-14-metrics]
lang: vi
translation_of: docs/playbook/adoption.md
---

# Áp dụng playbook

Checklist là một danh sách issue được theo dõi, có người phụ trách và ngày, không phải văn xuôi. Tạo mỗi dòng một issue.

## Ngày đầu (hai phiên đầu tiên)

| # | Bước | Người phụ trách |
|---|---|---|
| 1 | Điền [bản tóm tắt khám phá](../templates/discovery-brief.vi.md) và [điều lệ](../templates/project-charter.vi.md); quyết định G1 | Chủ doanh nghiệp |
| 2 | Sinh một hoặc nhiều repo từ repo mẫu; push; bật branch protection và merge queue | Tech lead |
| 3 | Tạo project trong công cụ theo dõi việc, file kế hoạch và backlog đầu tiên | Agent điều phối |
| 4 | Điền `CONTEXT.md` trên canvas arc42 và view C4 context | Agent điều phối; tech lead chấp nhận |
| 5 | Viết các ADR đầu tiên: stack, quyền sở hữu dữ liệu, danh tính, môi trường | Agent điều phối; tech lead chấp nhận |
| 6 | Báo giá chi phí hằng tháng của khung trên Dev và xin chủ doanh nghiệp đồng ý; rồi tạo tài khoản cloud và role CI qua IaC, có tag và cảnh báo ngân sách ở đúng con số đó | Tech lead |
| 7 | Áp migration `<prefix>-001` (schema, role) từ CI | Agent điều phối |
| 8 | Deploy khung lên Dev; `/health` trả về SHA của commit | Agent điều phối |
| 9 | Điền sổ RAID, bảng chi phí và sổ đăng ký secret (chỉ tên) | Agent điều phối |
| 10 | Chạy lần đóng phiên đầu tiên: snapshot, log, tạo file bài học | Agent điều phối |

## 30 / 60 / 90 ngày

| Tới ngày | Kết quả | Kiểm bằng |
|---|---|---|
| 30 | Tính năng đầu tiên đi qua Definition of Ready và Done; ratchet và docs lint xanh; bài học đầu tiên thành guard | Comment đã kiểm live; lịch sử CI |
| 60 | Chiến lược kiểm thử được dùng; checklist ASVS mức 1 xong cho các vùng bị đụng tới; runbook đầu tiên được thử trong một lần diễn tập; lấy baseline DORA | Bằng chứng diễn tập; báo cáo chỉ số đầu tiên |
| 90 | Lần rà soát chi phí và dung lượng hằng tháng đầu tiên; retro đầu tiên về chính playbook; một lượt cắt tỉa chỉ dẫn và ADR; viết kế hoạch G7 (cái gì bật khi có prod đầu tiên) | Các file rà soát; các issue về playbook được nêu |

## Chi phí chạy của một dự án mới

Xây bộ kit thì miễn phí; chạy thứ nó sinh ra thì không. Bước 6 tới 8 deploy một khung có cơ sở dữ liệu, bảng job và
`/health` lên Dev, và thứ đó bị tính tiền hằng tháng. Báo giá ở G1 bằng công cụ tính giá của nhà cung cấp cho đúng
region. Số ước lượng thô từ bảng giá niêm yết (tháng 11/2026):

| Hình dạng | Chạy gì trên Dev | Chi phí hằng tháng thô |
|---|---|---|
| Nền tảng dùng chung: app gia nhập một cluster container, instance cơ sở dữ liệu, private link và API gateway đã có, với schema và role riêng | Hai container nhỏ (api, worker), log, vài secret | khoảng 10 tới 35 USD |
| Độc lập: tài khoản, cơ sở dữ liệu và load balancer riêng | Hai container nhỏ, instance PostgreSQL nhỏ nhất ở một zone, một load balancer, một NAT gateway, IPv4 công khai, log, secret, kho image | khoảng 80 tới 120 USD; load balancer và NAT gateway chiếm khoảng một nửa |

Ưu tiên hình dạng dùng chung khi dự án nằm trong cùng tổ chức; dùng độc lập khi nó phải được cách ly (chủ khác, pháp
nhân khác).

## Chính bộ kit được nghiệm thu thế nào

| Thước đo | Mục tiêu |
|---|---|
| Sinh tới xanh: từ lúc chép mẫu tới mọi check xanh trên một PR rỗng | tối đa 1 phiên |
| Các mục ngày đầu cần sửa tay mà playbook không mô tả | 0 mục chặn, tối đa 3 mục nhỏ, mỗi mục được sửa trong bộ kit |
| Cập nhật mẫu từ tag trước lên tag mới nhất trên một dự án chưa đụng tới | áp vào không xung đột |
| Quét rò rỉ trên repo mẫu | 0 phát hiện |
| Một agent mới không có ngữ cảnh dự án chạy checklist ngày đầu chỉ bằng tài liệu | không có câu hỏi nào mà tài liệu lẽ ra phải trả lời |
| Sinh tới live: từ lúc chép mẫu tới `/health` trả về SHA của commit trên Dev | tối đa 2 phiên |
| Ngừng một service thử bằng checklist pha 9 | 0 resource và 0 USD còn lại sau một ngày tính tiền |
| Baseline DORA trước ngày 60, retro playbook trước ngày 90 | cả hai đã làm |
