---
name: aa-lessons
description: Sổ bài học (lesson log) của AA_Ecosys — ghi ngay một nguyên tắc khi phát hiện lỗi do làm/code sai cách, và đọc các bài học của vùng code trước khi sửa để không lặp lại lỗi cũ. Dùng khi tìm ra nguyên nhân gốc của bug, khi Nghiệp nói "lỗi", "sai cách", "lại bị", "note lại bài học", khi review phát hiện lỗi pattern, khi một giả định trong issue hoá ra sai, và trước khi sửa pipeline/gate/validator, job runner, trang list FE, deploy.
---

# aa-lessons

Log: [`lessons.md`](lessons.md), chia theo vùng. Mỗi dòng là **một nguyên tắc**, không phải nhật ký sự cố.

## 1. Trước khi làm — đọc

- Trước khi sửa một vùng (pipeline/gate, job runner, FE list, deploy, dữ liệu…), đọc mục tương ứng trong `lessons.md`.
- Đầu phiên (`aa-session`): lướt các mục liên quan tới issue đã chốt cho phiên.
- Bài học mâu thuẫn với yêu cầu đang làm → nêu với Nghiệp trước, không lặng lẽ bỏ qua.

## 2. Khi nào ghi — ghi ngay

Ghi **ngay lúc tìm ra nguyên nhân gốc**, không đợi cuối phiên. Ghi khi lỗi đến từ:

- làm sai cách hoặc dùng pattern sai (code chạy được nhưng sai thiết kế);
- giả định sai: tiền đề trong issue, trí nhớ, tên bảng/cột, "chắc là do…";
- một bước verify bị bỏ qua mà lẽ ra đã bắt được lỗi;
- thay đổi này phá một quyết định cũ mà không ai đối chiếu.

Không ghi: lỗi gõ đơn thuần, hoặc điều đã có guard (test/CI) bắt được.

## 3. Ghi thế nào

Một dòng, đúng mục, theo mẫu:

```
- **<Nguyên tắc, mệnh lệnh ngắn>** — <triệu chứng → nguyên nhân gốc> (S<nnn>, AA-xxx). Bắt bằng: <test/grep/query/check cụ thể>.
```

- Trùng ý với dòng đã có → sửa dòng đó (thêm bằng chứng), không thêm dòng mới.
- Nguyên tắc chung cho mọi vùng → mục "Cách làm việc".
- Ghi bằng tiếng Việt (log nội bộ), tên code/bảng giữ nguyên.

## 4. Biến bài học thành guard

Bài học kiểm được bằng máy là bài học tốt nhất:

1. Có thể viết unit test, CI check, lint rule hoặc assert → **làm luôn** trong PR đang sửa lỗi, nếu nằm trong scope.
2. Ngoài scope → đề xuất issue (hỏi Nghiệp trước khi tạo, theo `aa-linear-issue`).
3. Guard đã merge → xoá dòng khỏi `lessons.md` (README quy tắc 5), ghi tên guard trong commit message.

## 5. Cuối phiên

Trong `aa-session` kết thúc phiên: rà lại các lỗi đã gặp trong phiên. Lỗi nào chưa có dòng trong `lessons.md` thì ghi bổ sung, rồi nêu số bài học mới trong session block.

## 6. Nơi sửa

`skill/` ở repo gốc là nguồn duy nhất. Sửa xong → PR repo gốc (merge tay), rồi đồng bộ Kiro steering / upload Claude như các skill khác.
