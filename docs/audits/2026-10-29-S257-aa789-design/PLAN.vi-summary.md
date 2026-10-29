# AA-789: tóm tắt kế hoạch cho tech lead (bản đầy đủ: PLAN.md)

**Sẽ làm gì:** ba tầng, và chỉ tầng tất định (không dùng LLM) mới được hold bài.
- **Tầng 0, phòng từ gốc ($0):** seed chỉ ghi "Dùng tên Mörön (không viết Moron)", bỏ phần giải thích. Brief bỏ mẫu "one X, one Y, one Z" mà writer hay chép. Hai lỗi rò rỉ (ghi chú tên, công thức brief) không còn chỗ để sinh ra.
- **Tầng 1, khớp với seed ($0 LLM):** spaCy phân tích câu, đối chiếu SeedGraph và một từ kích hoạt. Chỉ báo lỗi khi cả ba khớp, thiếu một là bỏ qua. Lỗi ghi dưới gate cũ F17/F18/F13 kèm tiền tố `sa:`, không thêm gate mới (luật freeze S246). Mỗi lớp có mode riêng: off/shadow/repair/hold.
- **Tầng 2, LLM cho phần còn sót (trả phí nhỏ, làm sau):** chỉ xét các câu tầng 1 kích hoạt nhưng bỏ qua (ghi chú tên bị diễn đạt lại, câu lặp không chủ ngữ, FAQ hỏi WHAT/WHY/HOW, "hard to overstate"). Trích dẫn phải khớp nguyên văn hai phía, lỗi gọi model thì bỏ qua. **Không bao giờ hold**, mạnh nhất là sửa hoặc cắt 1 câu.

**Mỗi lớp xử lý thế nào:**
- Được phép hold: 1 'by boat' (lúc đầu chỉ repair), 2 tùy chọn bị lật ngược, 3 near→at, 5 tỷ lệ "của thế giới".
- Chỉ repair rồi warn: 4 hứa độ khó, 6 so sánh nhất không phạm vi, 10 câu mở đầu mồ côi (thêm luật danh từ trần cho "Access requires…"). 7 công thức brief và 8 ghi chú tên: tầng 0 + cắt câu.
- 9 câu lặp diễn đạt lại: ghép cặp theo cùng dòng seed + bge cục bộ, tự xóa câu sau hoặc warn. 11 FAQ: tầng 1 bắt câu hỏi đo được (có/không, bao lâu, khi nào, ở đâu, ai); câu hỏi mở chuyển cho `faq_answer_fit`, đổi route khỏi Sonnet.

**Luật an toàn trước khi hold:**
- Offline: 0 FP trên 246 câu sạch (cận trên Wilson 1,54%), 0 FP trên các ca khó của lớp, qua kiểm tra cố tình làm hỏng input (error injection).
- Shadow: ≥ 50 lần kích hoạt có nhãn, sai ≤ 1, có người chấm thứ hai. Phải sửa 1 câu thất bại mới hold, và chỉ sau khi freeze hết (~18/11).
- Có 1 hold sai là tự hạ mode; nâng mode phải qua PR kèm bằng chứng.
**Chi phí:** $0 bây giờ. Chạy đủ trên Dev ≈ $5–7/tháng: RAM worker 2 GiB ≈ $3,6 (nếu đo thấy cần), repair ≈ $0,2–0,8, tầng 2 ≈ $1–2. Hiệu chuẩn tầng 2 một lần ≈ $2,5 (trần $5). Khi có tenant (~3.000 bài/tháng) ≈ $20–35/tháng.

**Các bước và cổng:**
- P0 offline ($0): baseline main, chấm từng lớp bằng score.py, đo RSS. P1 shadow ($0): replay mọi bài đã lưu trên Dev, agent panel gắn nhãn.
- P2 repair: cần route t9_repair, đang bị chặn trên acc3. P3/P4 tầng 2: cần credit OpenAI hoặc acc3 được gỡ chặn. P5 hold sau 18/11, theo thứ tự lớp 2 → 3 → 5 → 1.

**$0 làm ngay:** S1 nền tảng, S2 harness eval, S3 lớp 1–5, S4 lớp 6/7/8/10, S5 tầng 0, S6 lớp 9, S7 FAQ, S8 vòng phản hồi, phần $0 của module tầng 2.
**Trả phí sau:** đo tỷ lệ repair thành công, hiệu chuẩn và shadow tầng 2, chạy T-round để đo hiệu quả tầng 0.
**Cần anh quyết** (đã kèm đề xuất): D1 nâng RAM worker, chỉ khi đo thấy cần · D2 route tầng 2 dùng OpenAI credit, trần $5 · D3 freeze hiểu là cho repair trước, hold sau 18/11 · D4 mở thêm 1 issue Linear cho tầng 2 · D5 bằng chứng để hold là agent 2 người chấm + anh kiểm 20 mẫu · D6 tầng 0 đổi input của writer.
