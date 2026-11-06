# AA-741 phase 1 — chuỗi nội dung đại lý T7→T11 đủ 8 kênh trên 4 thương hiệu (S271, 06/11/2026)

Audit viết cho tech lead (tiếng Việt, theo luật ngôn ngữ cho `docs/audits/`). Số liệu lấy từ Dev: ledger
`shared.llm_call_log` (non-shadow, 4 tenant `audit-*`, từ 2026-11-05 23:44Z), kết quả script chạy chuỗi trong phiên S271.
Không có tên người, email hay nội dung bài viết trong file này. Phase 0: `../2026-11-05-S270-aa741-phase0/README.md`.

## 1. Chạy gì

| Thương hiệu (tenant audit) | Bước | Kết quả |
|---|---|---|
| Atlas & Hearth | T7 → T8 → T9 → T11, 8 kênh | **69/69 PASS** (pilot trước, đo chi phí rồi mới chạy tiếp) |
| WildKind Travel | T7 → T11, 8 kênh | **59/60** — kênh blog không còn chủ đề (§4.1) |
| Terra Family | T2 thêm 2 tour (đủ 3) + T7 → T11, 8 kênh | **75/75 PASS** |
| Trail Pulse | T2 thêm 2 tour (đủ 3) + T7 → T11, 8 kênh | **75/75 PASS** |

8 kênh: blog, linkedin, facebook, instagram, tiktok, email, landing_page, ads. Mỗi kênh: chọn chủ đề tốt nhất của slate,
chọn mục tiêu, sinh 3 góc viết, chọn góc đầu, viết, giao cho đại lý, xuất (text; blog thêm HTML document + fragment).

**Đại lý nhận nội dung:** 31/32 lượt kênh giao bài `ready` cho đại lý (lượt thiếu = blog WildKind, không có chủ đề để
viết). Mọi bản HTML blog mang dấu AI máy đọc được (`data-ai-generated` + meta `ai-*`).

## 2. Chi phí theo stage và vai trò (ledger, 4 tenant, phase 1)

| Stage | Vai trò | Model @ connection | Lượt | Lỗi | USD |
|---|---|---|---|---|---|
| t9_write | writer | sonnet-5-5 @ anthropic-direct | 52 | 4 | 2,1069 |
| t9_write | writer | sonnet-4-6 @ anthropic-direct (dự phòng) | 1 | 0 | 0,0627 |
| t8_angle_gen | writer | sonnet-5-5 @ anthropic-direct | 31 | 0 | 0,8371 |
| t2_generate | writer | sonnet-5-5 @ anthropic-direct | 7 | 0 | 0,5467 |
| t9_repair | writer | haiku-5-5 / haiku-4-5 @ anthropic-direct | 21 | 1 | 0,0217 |
| t2_itinerary_nudge | writer | haiku-5-5 @ anthropic-direct | 3 | 0 | 0,0012 |
| t10_judge | judge | gpt-6-luna @ openai-direct | 63 | 0 | 0,0412 |
| t7_debate_judge | judge | gpt-6-luna @ openai-direct | 146 | 0 | 0,0175 |
| t2_judge | judge | gpt-6-luna @ openai-direct | 21 | 0 | 0,0109 |
| t10_judge | judge | gpt-6-luna / gpt-5.6-luna @ acc3 | 6 | 6 (từ chối, 0 USD) | 0,0000 |
| t9_faq_answer_fit / t9_faq_filter | validate | sonnet-5-5 / haiku-5-5 @ anthropic-direct | 6 | 0 | 0,0187 |
| f10_embed | embed | cohere-embed-v4 @ acc2 | 63 | 0 | 0,0024 |
| **Tổng** | | | | | **3,6671** |

Theo vai trò: **writer 3,5763 USD (97,5 %)**, judge 0,0697, validate 0,0187, embed 0,0024.
Atlas (8 kênh, không T2) = 0,81 USD → **≈ 0,10 USD/bài** trọn T8 + T9 + T10. Phase 0 + phase 1 ≈ 5,7 USD (mức duyệt ≤ 20 USD).

## 3. Lượt eval R2 (AA-900, cùng phiên, trần 2,5 USD tech lead duyệt)

Run `08c34cb4…`, t9_blog, non_inferior: **invalid (budget_cap) sau 15 item; judge kappa 0,137** (cần ≥ 0,6). Chi phí
2,474 USD: **writer** t9_write 20 lượt 2,420 USD, **judge** writing_memory_eval 70 lượt 0,054 USD. Không phải bằng chứng;
judge hiện không khớp nhãn người (route judge đã rời acc3 do acc3 từ chối GPT). Ghi trên CIS #1330.

## 4. Phát hiện theo cơ chế

### 4.1 Kênh blog cạn chủ đề sau 1–2 bài (lỗi thiết kế, đang sửa)
- Slate T7 lấy chủ đề blog theo **route** (chuỗi ngày liên tiếp của một tour, ≈ 1–2 route/tour), các kênh khác theo
  **segment** (từng điểm, hàng chục/tour). Unique index `(tenant, channel, route)` làm route đã dùng không bao giờ được
  đề xuất lại → đại lý 3 tour chỉ viết được 1–2 bài blog, mãi mãi (WildKind phase 1, cả 4 tenant 0 chủ đề blog sau phase 1;
  kịch bản UAT W-02 FAIL vì lý do này).
- Thiết kế gốc của bộ công cụ social: blog là chủ đề theo segment, route đi kèm làm mạch hành trình. Grain route là độ lệch
  của CIS (AA-511), chưa cân nhắc tác dụng phụ.
- Sửa (lane S271): blog về grain segment + gắn route khi chọn; chi phí ≈ +0 (brand-fit đã cache theo segment).

### 4.2 T9 blog sinh quá nhiều token (đang điều tra)
- t9_write blog: trung bình 1.846 token ra, có lượt **11.465**; **4 lượt chạm trần 12.000** (3 truncated + 1
  billed_unusable, **0,58 USD mất**). Một bài blog ≈ 860 chữ ≈ 1.200 token. t9_write = 2,1/3,67 USD của phase.
- Lane S271 tìm nguyên nhân trong prompt/hợp đồng đầu ra của T9 và giới hạn lại.

### 4.3 Dự phòng model hoạt động đúng
- 1 lượt t9_write rơi Sonnet 4.6, 1 lượt repair rơi Haiku 4.5 (model-first fallback, có ledger).
- t10_judge thử acc3 6 lượt bị từ chối (0 USD, circuit), rồi OpenAI trả lời.

### 4.4 Còn từ phase 0
- `system_prompt` không được điền khi nhập brief .docx (§4.3 phase 0) — chưa sửa.

## 5. Việc tiếp
1. Merge + deploy 2 bản sửa §4.1 / §4.2, quay lại UAT W-02 và chạy lại slate blog 1 tenant (≈ 0,2 USD).
2. Phase 2 (48 tour) chỉ sau khi §4.1 + §4.2 live — không thì phase 2 lặp lại hai lỗi trên với chi phí ×4.
3. Trần AI gói Growth (40 USD/tháng): với ≈ 0,10 USD/bài và ≈ 0,19 USD/tour T2, đại lý dùng hết 200 lượt viết lại ≈ 38 USD
   — xem lại sau khi §4.2 giảm token.
