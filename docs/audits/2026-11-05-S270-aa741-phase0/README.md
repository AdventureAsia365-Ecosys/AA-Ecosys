# AA-741 phase 0 — chạy thử chuỗi nội dung đại lý T0→T11 (S270, 05–06/11/2026)

Audit viết cho tech lead (tiếng Việt, theo luật ngôn ngữ cho `docs/audits/`). Số liệu lấy từ Dev, ledger
`shared.llm_call_log`, và kết quả script trong phiên S270. Không có tên người, email hay nội dung bài viết trong file này.

## 1. Dựng gì

| Bước | Kết quả |
|---|---|
| 4 tenant audit (`audit-atlas-hearth`, `audit-terra-family`, `audit-trail-pulse`, `audit-wildkind-travel`) | Tạo qua saga `tenant_provision` (kind demo, gói growth, ngân sách AI 40 USD/tháng). Tenant cũ S229 giữ nguyên làm fixture E2E. |
| Gắn CRM | Saga `attach` `crm.core` + tạo agency CRM tổng hợp (console `create_agency`) — cần cho lời mời studio E2E (CRM chỉ nhận lời mời E2E cho agency synthetic đã có). |
| Thành viên | Danh tính partner E2E được mời làm **editor** ở cả 4 tenant, nhận lời mời qua mail thật (4/4). |
| T0 brief | 4/4 file .docx tải lên, parse, lưu (version 2). |

## 2. Kết quả từng stage

### Đại lý thấy gì (lớp sản phẩm)
- **T2 viết lại tour: đại lý nhận đủ 8/8** (Atlas 3, WildKind 3, Terra 1, Trail Pulse 1), trạng thái phía đại lý
  `ai_generated`, không điểm, không cờ; **8/8 xuất DOCX** được.
- **T7 gợi ý chủ đề**: 2/2 lần làm mới đề xuất đủ kênh (blog 1–2, LinkedIn 7–8, Facebook 7–8, Instagram 6–7…).
- **T8 góc viết**: 2/4 lượt ra 3 góc; **2/4 lượt hỏng** (xem §4.1, đã sửa).
- **T9 bài viết**: mọi lượt T8 thành công đều ra bài và **giao cho đại lý** (blog 862 chữ, LinkedIn 143 chữ),
  `ready_state=ready`, không cờ hiện cho đại lý.
- **T11 xuất bản**: text + HTML (document / fragment) 200; HTML mang dấu AI máy đọc được (`ai_mark=true`).

### Tín hiệu cho Writing Lab (chỉ nội bộ AA)
- T2: điểm judge 7–8 cho 5/8 bản, 6 cho 3/8 bản (dưới ngưỡng 7 → ghi `needs_review` trong DB, chỉ Lab thấy).
- 0 chữ cấm, 0 lẫn tên thương hiệu khác giữa các tenant cùng tour; nguồn SEO theo thị trường của tenant.

## 3. Chi phí thật (ledger, non-shadow, 4 tenant audit)

| Lượt | Model | Chi phí |
|---|---|---|
| Viết lại 1 tour (T2) | Sonnet 5.5 (Anthropic API) | **≈ 0,19 USD/tour** (8 tour = 1,50) |
| Làm mới đề xuất chủ đề (T7) | GPT-6 Luna (OpenAI, chấm) | ≈ 0,01 USD/lần |
| Góc viết (T8) | Sonnet 5.5 | ≈ 0,05 USD/lượt (gồm lượt bị cắt) |
| Viết + kiểm 1 bài (T9 + T10) | Sonnet 5.5 + Haiku | **≈ 0,11 USD/bài** |
| Trọn chuỗi 1 đại lý (1 tour + 1 slate + 2 góc + 2 bài) | | **≈ 0,50 USD** |
| **Tổng phase 0** | | **1,94 USD** |

Dự báo:
- **Phase 2 (48 tour, 4 thương hiệu)**: T2 ≈ 9 USD + T7–T9 ≈ 2–3 USD ⇒ **≈ 11–12 USD** (trong mức 20 USD đã duyệt).
- **Đại lý gói Growth dùng hết 200 lượt viết lại/tháng**: ≈ 38 USD/tháng chỉ cho T2 — **sát trần ngân sách AI
  40 USD/tháng** của gói (giá gói 799 USD). Đề xuất xem lại trần, hoặc giảm chi phí T2 (tóm tắt nguồn trước khi đưa
  Sonnet).

## 4. Phát hiện theo cơ chế

### 4.1 Trần token quá thấp cho model 5.x (lỗi thật, đã sửa)
- Ledger 7 ngày: `t8_angle_gen` Sonnet 5.5 chạm `max_tokens=2048` **7/9 lượt** (5 `billed_unusable`, 2 cắt nhưng
  parse được) ⇒ 2/4 yêu cầu T8 kết thúc `pending_goal` 0 góc; mất 0,20 USD. Cùng lỗi ở `t9_write` (1/9 tại 8000),
  `t9_repair` (1/1 tại 2048), `t9_faq_filter` (1/1 tại 3000).
- Sửa: CIS #1330 — trần mỗi stage (T8 4096, T9 blog 12000 / kênh ngắn 4096, repair 4096, faq_filter 6000) + gọi lại
  **đúng 1 lần** với trần gấp đôi khi bị cắt; cả hai lượt đều có dòng ledger (`budget_cut`, `truncation_retry`).
- Chạy lại T8 sau deploy: xem §6.

### 4.2 Judge vẫn thử model acc3 đang bị chặn trước OpenAI
- `t2_judge`, `t7_debate_judge`, `t10_*`: ≈ 560 dòng `refused` trong 1 tối (circuit chặn trước khi gọi, $0) nhưng
  làm bẩn log và chậm. Sửa: CIS #1332 dời nấc đang mở circuit xuống cuối chuỗi (AA-1042).

### 4.3 Nhập brief .docx không bao giờ điền `system_prompt`
- 4/4 tenant `system_prompt=0` sau khi lưu brief. Writer vẫn dùng style guide, chữ cấm, ví dụ — nhưng nếu thiết kế
  mong có `system_prompt` từ brief thì đây là lỗ hổng. Đề xuất: map trường này trong parser T0 hoặc bỏ khỏi form.

### 4.4 Vận hành
- Mời E2E vào tenant chỉ có Content bị CRM từ chối (`tenant_not_synthetic`) vì CRM chưa có agency ⇒ quy trình tạo
  tenant thử nên luôn tạo agency CRM tổng hợp (hoặc lời mời studio không phụ thuộc agency CRM).
- Exec SSM vào task CRM (512 MB) chập chờn khi nạp cả app ⇒ script CRM giữ nhỏ, đọc kết quả bằng `--resume`.

## 5. Việc tiếp (phase 1–2)
1. Sau §6 xanh: phase 1 trên 4 tenant với 3 tour mỗi thương hiệu + đủ kênh (≈ 3–4 USD).
2. Phase 2 (48 tour) theo dự báo §3, báo cáo theo cơ chế + Writing Lab.
3. Đưa các tín hiệu T2 dưới ngưỡng vào Lab (mẫu nhãn) — không chặn đại lý.

## 6. Chạy lại T8 sau CIS #1330 (06/11, ~01:50 +07)
- CIS #1330 deploy `40979fd4` (api + worker COMPLETED).
- Atlas audit, kênh LinkedIn (lượt hỏng ở §4.1): **8/8 PASS**: T8 ra 3 góc sau 52 s, chọn góc, T9 viết 178 chữ, giao cho
  đại lý `ready`.
- Ledger sau deploy: `t8_angle_gen` 1 lượt `end_turn`, **2.574 token ra** (vượt trần cũ 2048 → trước đây sẽ bị cắt),
  0,033 USD, không cần gọi lại; `t9_write` / `t9_repair` `end_turn`. Không còn dòng `max_tokens` thiếu dòng gọi lại.
- WildKind blog không chạy lại được vì slate chỉ có 1 chủ đề blog và đã dùng (giới hạn dữ liệu, không phải lỗi).
- Chi phí chạy lại ≈ 0,08 USD (T7 + T8 + T9). **Tổng phase 0 ≈ 2,0 USD.**
