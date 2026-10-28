# AA-790 vòng 8 — bộ sinh angle T8 (S255, 28/10/2026)

**Kết luận: FAIL → cờ `T8_ANGLE_BRIEF_MODE` giữ tắt; vòng 6 vẫn là bản live.** Code vòng 8 (CIS #1095 `646c2bdd`) đã merge
nhưng trơ khi cờ tắt, nên không có gì phải revert.

## Đã làm
- Theo quyết định S254: vòng sau sửa **bộ sinh angle T8**, không sửa prompt T9. CIS #1095 thêm "brief contract" cho T8 sau cờ.
- A/B trên đúng 20 bài pilot S251 (4 tenant, blog + LinkedIn): arm r8 = angle sinh lại bằng brief r8, rồi T9 viết như vòng 6.
  Lượt trả phí 1 dừng ở trần $1,40 với 17/20 bài; 3 blog bị `skipped_cost_cap` được chạy lại riêng (không phải lỗi).
- Panel mù A: 160 item (before, r1–r6, r8), 4 lens, 64 lượt chấm, rubric S251, cùng lens với S252/S254.

## Kết quả (thang 10)
| Lens | r6 | r8 | Ngưỡng (đặt trước) | |
|---|---|---|---|---|
| ai_tells | — | 5,8 | ≥ 5,5 | đạt |
| brand_voice | 6,80 | 6,83 | ≥ 7 tổng, ≥ 7 ở 3/4 tenant, r8 − r6 > 0,15 | trượt |
| reader_value | 7,10 | 6,83 | r8 − r6 ≥ −0,15 | trượt (−0,27) |
| source_fidelity | 7,72 | 7,42 | r8 − r6 ≥ −0,17 | trượt (−0,30) |

W/T/L r8 so với r6: ai_tells 8/3/9, brand_voice 9/3/8, source_fidelity 5/1/14, reader_value 5/5/10. Bảng đủ theo tenant /
kênh: `aggregate.txt`.

## Đọc kết quả
- Đổi angle không nâng brand_voice (+0,03, trong nhiễu) mà làm tụt source_fidelity và reader_value: angle mới kéo bài ra xa
  dữ kiện nguồn (WildKind tăng, Terra Family giảm mạnh).
- Hai vòng liên tiếp (r7 sửa T9, r8 sửa T8) đều không qua luật ship. Đề xuất: dừng tinh chỉnh prompt; vòng sau (nếu có) đo
  lại brand pack và nhãn của panel theo từng tenant trước, vì Trail Pulse / WildKind thấp ở mọi arm.

## Chi phí (`shared.llm_call_log`, stage `adhoc_aa790`)
- r8: T8 sinh angle $0,770 (26 lệnh) + T9 viết $0,859 (20 lệnh) = **$1,629** (trần vòng $2). Panel mù: $0 AWS (agent).
- So sánh: angle T8 live trung bình $0,027/lệnh (60 ngày).
