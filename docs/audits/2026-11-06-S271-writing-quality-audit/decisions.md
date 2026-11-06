# S271 — Quyết định của tech lead (06/11/2026)

Nguồn: trang quyết định https://claude.ai/artifact/YZzbttV86QkzHssvsfkAbd (bản chuyển sang tài khoản Claude mới; bản gốc lúc chọn: 6y5NHZ2rx1Yb7euNifHYeY), lựa chọn lưu trong `decisions` của trang, đọc lại lúc 11:31Z. Cả 16 câu chọn **A** (đề xuất), không ghi chú. Đây là đầu vào khoá `writing_policy.yaml` v1 (W1) và ADR 0020.

| # | Câu | Chọn | Nội dung chốt |
|---|---|---|---|
| D1 | Bối cảnh địa danh | A | Cho phép bối cảnh (lịch sử, địa lý, văn hoá) về địa danh có trong FactSheet; không bao giờ hứa hoạt động / dịch vụ / giờ / cảnh quan của chuyến; con số và năm trong bối cảnh = warn. |
| D2 | Brief là nguồn? | A | Không. Brief chỉ là chỉ dẫn; căn cứ chỉ từ dòng FactSheet có ID. |
| D3 | Câu suy ngẫm | A | Giọng văn, được phép nếu không nêu dữ kiện về chuyến. |
| D4 | Câu giả định | A | Warn; nêu hoạt động / dịch vụ / giờ / cảnh quan cụ thể thì là lời hứa. |
| D13 | Hiếm / độc nhất / lâu đời | A | Gắn với chuyến = lời hứa (enforce nếu nguồn không có); về địa danh theo D1 (bối cảnh, số và năm = warn). |
| D14 | Phù hợp / an toàn / nhịp độ | A | Chỉ điều nguồn hoặc trường đối tượng khách nói; vượt quá = lời hứa, enforce. |
| D15 | Dựng cảnh | A | Cảnh có hoạt động / giờ / cảnh quan cụ thể = lời hứa (enforce nếu nguồn không có); cảm giác chung = giọng văn. |
| D5 | Dải meta / title | A | Meta 140–155 ký tự cho mọi workflow; title theo dải của bộ chỉnh title hiện có; code tự ghép / cắt, không bắt LLM đếm. |
| D7 | Judge duy nhất được giữ bài | A | R1 hiệu chuẩn ≥ 2 ứng viên (GPT-6 Luna qua OpenAI API + một model acc2 không phải Claude), chọn model đạt, ghim 1 rung không fallback (miss = unverified); gỡ GPT-6 khỏi mọi route writer. |
| D16 | Luật dữ liệu cho judge trên OpenAI API | A | Cho phép vendor API làm judge chính cho vai trò kiểm (chỉ văn bản tour, không dữ liệu cá nhân); sửa ADR 0009; xem lại khi acc3 được cấp quyền. |
| D10 | Judge eval = judge sản xuất | A | Dùng chung một engine; độc lập đến từ nhãn người theo từng câu + phiếu thứ hai khác hãng cho câu chặn chưa chắc. |
| D9 | Bỏ s1_judge khỏi luồng thật | A | Bỏ; chuyển sang lấy mẫu ~20 tour/tuần trong Writing Lab, ghim; chỉ quay lại làm cổng khi kappa ≥ 0,6 trên ≥ 40 cặp. |
| D11 | Thời gian duyệt nhãn | A | ~2–3 giờ trong 1–2 tuần (agent làm lượt đầu), sau đó 10 mẫu / workflow / tháng. |
| D6 | Nội dung đại lý còn lời hứa sai | A | Lượt 3 = "dừng và gắn nhãn" (0 USD); code chỉ cắt câu cho loại lỗi đã đo precision đạt; còn lại giao kèm nhãn admin; không chặn publish. |
| D8 | Tour cưỡi voi ở T2 | A | Giữ nguyên văn Master + ô thương hiệu do code ghép, 0 lần gọi LLM, tạo dòng duyệt, đại lý vẫn nhận. |
| D12 | Trần trả phí W5 | A | Eval null run ≤ $5, T9 ≤ $15, S1 ≤ $8, T2 ≤ $5 (tổng ≤ $33); mỗi lần chạy cần đồng ý riêng. |

Lưu ý thực thi (từ phản biện, đã gộp vào D6 / D7 trước khi tech lead chọn): truth_cut chỉ cho class có measurement record đạt, ưu tiên cắt mệnh đề; span do đại lý viết không bao giờ bị cắt. Instrument ghi model id thật trả về mỗi lần gọi; `max_completion_tokens` ≥ 8192 (migration 382).
