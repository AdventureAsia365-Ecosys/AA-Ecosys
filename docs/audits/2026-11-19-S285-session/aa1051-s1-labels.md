# AA-1051 — Nhãn panel cho 22 mẫu S1 (S285, 19/11/2026)

Tác nhân: Claude Code (subagent của workflow). Không gọi LLM trả phí, không AWS, không push/merge. Dữ liệu mẫu (nguồn,
bài viết, lý do chi tiết) chỉ nằm trong `.tmp-session/` (private, không commit); file này chỉ có số đếm.

## Cách gán nhãn

- Mỗi mẫu có 3 phiếu theo lăng kính (facts, voice, reader) + 1 phiếu kiểm chứng đọc toàn bộ nguồn (verifier).
- `agreed` khi verdict của verifier trùng verdict đa số của 3 lăng kính; `disputed` khi verifier lật đa số.
- Nhãn = verdict + grade của verifier khi `agreed`. Mẫu `disputed` KHÔNG được áp (chạy `labels apply` không có
  `--include-disputed`), chờ tech lead quyết.
- `approved_by` ghi "S285 agent panel (pending tech lead review)": nhãn chưa được tech lead duyệt.

## Kết quả

| | Số mẫu |
|---|---|
| Tổng | 22 |
| Agreed (đã áp, fixture addendum lên 1.6.0) | 21 |
| Disputed (chưa áp, vẫn `needs_panel`) | 1 |

Nhãn đã áp (21 mẫu):

| Verdict | Grade | Số mẫu |
|---|---|---|
| pass | light | 14 |
| fail | heavy | 7 |
| pass | as_is | 0 |
| fail | reject | 0 |

Mẫu tranh chấp (1): đa số lăng kính 2–1 cho pass, verifier cho fail/heavy chỉ vì 3 trường trống (description, mobile
card, OG tags). Đề xuất: theo đa số, pass/light — vì chính verifier đã coi 3 trường trống này là lỗ hổng của pipeline
(trống ở cả 22 mẫu) và cho pass/light ở 4 mẫu khác cùng tình huống. Nếu tech lead muốn coi trường trống là
"broken structure" thì phải lật cả 4 mẫu kia, không riêng mẫu này.

## Độ đồng thuận

- 3 lăng kính đồng ý hoàn toàn: 16/22; cả 4 phiếu cùng verdict: 16/22.
- Verifier trùng đa số: 21/22.
- Lăng kính voice lệch đa số ở 5 mẫu, lần nào cũng vì cùng một lý do: chấm fail/heavy do 3 trường trống. Đây là
  điểm rubric cần nói rõ (trường trống do pipeline = light hay broken structure).

## Lý do fail (7 mẫu đã áp)

| Lý do quyết định | Số mẫu |
|---|---|
| Bịa quy mô nhóm (group size) không có trong nguồn | 5 |
| Một ngày bị rút còn 1 dòng, mất nội dung ngày của nguồn (broken structure) | 1 |
| Bỏ điểm nghỉ đêm của nguồn, thay bằng câu mơ hồ tự đặt (fact change) | 1 |

## Lỗi chung đáng theo dõi (không quyết định verdict)

- Description, mobile card, OG tags trống ở cả 22 mẫu → lỗ hổng pipeline, không phải lỗi riêng từng bài.
- Ít nhất 6 mẫu để lọt cách nói nội bộ (nhắc tới "nguồn") vào chữ khách đọc → sửa chữ (light), nên thêm guard ở writer.
