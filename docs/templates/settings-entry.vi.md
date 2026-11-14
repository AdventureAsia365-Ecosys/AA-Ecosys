---
id: TPL-01-settings-entry
title: Mẫu mục registry settings
description: Cách thêm một ngưỡng, giới hạn hay giá trị chính sách thành một setting sửa được trên trang admin, kèm dòng registry và hướng dẫn vận hành.
type: template
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [TPL-01, CAT-01]
lang: vi
translation_of: docs/templates/settings-entry.md
---

# Mẫu mục registry settings

Mọi giá trị chính sách kinh doanh và mọi ngưỡng hay giới hạn vận hành là một setting: dữ liệu có phiên bản với một trang
admin cho vai trò administrator, gieo sẵn giá trị mặc định đã duyệt (quy tắc làm việc W7 của sổ tay, nguyên tắc "dung
sai, không phải xin duyệt" của playbook). Một biến môi trường hay một hằng số trong code là chưa đủ, vì muốn đổi phải
deploy. Cấu hình deploy (endpoint, tham chiếu secret, công tắc theo môi trường) vẫn nằm trong môi trường (Twelve-Factor
factor III).

## 1. Dòng registry

| Trường | Giá trị |
|---|---|
| Khoá | `<area>.<name>` (ví dụ `quality.min_words`) |
| Kiểu và đơn vị | <số nguyên, số chữ / số thập phân, USD / khoảng thời gian, ngày / enum> |
| Mặc định (đã duyệt) | <giá trị, kèm ai duyệt và khi nào> |
| Khoảng cho phép | <nhỏ nhất tới lớn nhất, hoặc các giá trị enum> |
| Phạm vi | <toàn cục / theo tenant / theo stage / theo nhà cung cấp> |
| Ai được đổi | administrator (maker-checker khi nó làm dịch chuyển tiền hay dữ liệu) |
| Đọc bởi | <module và hàm, qua reader settings duy nhất> |
| Tác dụng của một thay đổi | <ngay lập tức / job tiếp theo / lần deploy cache tiếp theo> |
| Kiểm toán | mỗi thay đổi giữ giá trị cũ, giá trị mới, ai và khi nào |

## 2. Hướng dẫn vận hành

Viết hai tới năm dòng hiện cạnh trường đó trên trang admin:

- **Nó điều khiển gì:** <lời thường>.
- **Tăng khi:** <triệu chứng>. **Giảm khi:** <triệu chứng>.
- **Khoảng an toàn:** <...>. Ra ngoài khoảng đó: <cái gì hỏng>.

## 3. Checklist

- [ ] Được gieo bởi một migration với giá trị mặc định đã duyệt.
- [ ] Đọc qua reader settings duy nhất; không có bản chép cứng của giá trị trong code.
- [ ] Một check CI từ chối ngưỡng viết cứng trong đường code đọc nó.
- [ ] Trang admin hiện trường, đơn vị, khoảng và hướng dẫn vận hành.
- [ ] Một test đổi giá trị và chứng minh hành vi đổi theo mà không cần deploy.
