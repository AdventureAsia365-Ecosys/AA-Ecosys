# S224 — Đối chiếu chi phí Jev + backfill, AA-748 (không áp dụng), atomize sang GPT-6 Luna, dọn gateway (10–11/10/2026)

**Tác nhân:** Claude Code (VSCode/WSL), chế độ "dùng kiro-cli" · **ECS cuối phiên:** `aa-cis-dev-api:521` / `worker:76` (cùng SHA `d537930`, rollout COMPLETED, /health 200) · **Migration mới (đã áp Dev):** 209, 210, 211, 212, 213, 214 · **Job queue:** sạch · **Kiro credit:** còn ~640/2.000 (dùng ~88 trong phiên: 22,6 + 11,3 + 14,0 + 33,5 + preflight) · **Jev:** có credit lại (canary `credit_ok` đầu phiên).

## Trạng thái đầu phiên
Khớp memory S223: api `:506` / worker `:61` (SHA `5307549`), queue 0. Lệch: memory ghi "Jev hết credit", thực tế canary đầu phiên `credit_ok: true` (chị Thư đã nạp).

## Quyết định của Nghiệp (chỉ điều Nghiệp nói)
- CIS phải khớp số tiền trang Jev → **backfill đúng**.
- **Cảnh báo Jev chỉ khi HẾT credit** (Nghiệp không trực tiếp nạp); làm sẵn **nhập các lần nạp ở Settings**.
- `a1_keyword_about_tour`: **phương án A — enforce 0,80 / 0,30**.
- **Bỏ** tìm hiểu OpenAI Decisions API (không cấp thiết).
- AA-748: làm vòng 2, rồi **đóng (không áp dụng)**; chọn thử temperature writer thay thế.
- **ADR 0008**: stage vai `validate` (trích/kiểm, judge không chấm) được dùng mọi hãng → `s1_source_facts` và atomize sang **GPT-6 Luna (Bedrock acc3)**, Haiku dự phòng.
- Tạo **AA-757** (atomize → Luna), làm ngay trong phiên; mẫu đánh giá phải lớn (≥ 100 cặp đọc tay).
- **Atomize chỉ 1 lần khi tour lên Master (A3 platform); tenant KHÔNG atomize** — dùng atom/Segment/route/hub của platform. Không atomize lại catalog. Ghi note để không nhầm kiến trúc nữa.
- Làm luôn đổi tên atomize sang A3 (bước 5).

## Kết quả chính
**Đối chiếu chi phí Jev (AA-756).** Dashboard Jev 03–10/10: $11,80 / 408k request; `llm_call_log` chỉ $7,05 / 139k. Nguyên nhân: lỗi một-connection (sửa ở #600 lúc 09/10 01:00 UTC) làm **ghi log thất bại** (`*_log_write_failed` khớp phần thiếu từng ngày) — Jev vẫn tính tiền, và mất `decision_log` = mất cache nên recompute hỏi lại Jev. **Backfill** 53 dòng tổng hợp (`quality_signal.source='reconcile_s224'`, 347.242 call, $6,11): tổng Jev CIS $8,44 → $14,54; 03–10/10 ra $11,78 so với $11,80. **#632**: ghi log lỗi thì thử lại trên connection riêng (+ transaction cho decision_log). Giá đúng ($0,042/Mtok).

**#630 / #631 / #633 (AA-756).** #630 ghi outcome (deploy bị guard chặn do recompute tự động sau wave → chạy lại). #631 nguồn theo ngày cho grounding: cổng đo đồng thuận 200 câu (−72% ký tự, 1 accept sai không có con số) → merge; pilot live tour dài −51% token. #633 thêm SUMMARY nguồn vào nguồn theo ngày (2/25 câu bị chấm thấp sai vì chi tiết ở summary).

**Jev credit trong Settings (#635, Kiro, mig 209).** Tab "Jev Credit": nhập lần nạp, ước số dư (nạp $20 − chi $10,14 = ~$9,86); cảnh báo hết credit dùng advisory lock (trước đây 3 thông báo trùng). Verify live + ảnh desktop/mobile; **#636** sửa TabBar tràn ngang mobile (lỗi có sẵn, 7 tab).

**`a1_keyword_about_tour` → enforce 0,80 / 0,30** (gán nhãn 100 mẫu, precision 1,0 cả hai ngưỡng; 54% từ khoá ≤ 0,30). Calibration doc **#634**. Mô phỏng: loại đúng từ khoá rác (bald eagle cho tour Sri Lanka…).

**Câu hỏi Jev loại B `a1_promise_unsupported` (#637, mig 211, shadow)** — hỏi chung lời gọi với `a1_claim_supported`, để đo riêng "hứa điều nguồn không có".

**AA-748 — Done (không áp dụng).** Kiro #638 (cờ `S1_STRUCTURED_FACTS`, mặc định TẮT, mig 210) + vòng 2 #639/#640 (luật chỉ con số, trích chỉ con số, `s1_source_facts` → Luna $0,0004/tour). A/B: vòng 1 −45% câu sai nguồn nhưng điểm −0,23; **arm đối chứng lặp lại tự chênh −36%** → hiệu ứng nằm trong dao động; output cuối đã 0 câu sai sau sửa. Đóng.

**Temperature writer.** #641 (`S1_WRITER_TEMPERATURE`) — lượt đầu vô hiệu vì **temperature không hề tới Claude** (cả 2 đường native bỏ tham số) → **#643** sửa. Lượt thật 0,4: câu sai nguồn 3,73 vs 3 đối chứng 3,47/4,23/4,73, điểm bằng → **giữ mặc định**.

**AA-757 — Done.** A/B offline 60 tour / 14 nước / 477 ngày: Luna 0 lỗi, 0 lỗi JSON, 0 bịa (120 mục đọc tay), Jev p<0,5 0,5% vs Haiku 1,5%, rẻ ~6 lần. Phát hiện **atomize gọi thẳng `invoke_claude` (không qua gateway)** → **#642** (Kiro: atomize qua gateway; Claude: xoá judge legacy, guard chặn `invoke_claude`/`get_satellite_client` ngoài `shared/llm_client`). **#644** lọc atom hậu cần + làm sạch evidence + prompt động từ cụ thể; **mig 213** atomize → validate / gpt-6-luna / Haiku dự phòng. Verify live 3 job `a3_atomize`: 43 call đều Luna, 0 fallback, $0,029, 0 atom hậu cần. **#645** (Kiro) đổi tên: `services/acp_contract/a3_atomize.py`, `run_a3_atomize`, stage `a3_atomize` (**mig 214**). Không atomize lại catalog.

**ADR 0008** (AA-CIS-App `docs/adr/0008-validate-stages-any-vendor.md`).

## Linear
- AA-748 **Done** (không áp dụng, báo cáo 2 vòng). AA-757 **Done**. AA-756 **In Progress** (comment: backfill, #630/#631 gate, temperature, keyword enforce, sub-task credit Settings).

## Việc cần làm phiên sau (S225)
1. AA-756 còn: kiểm tay ~30 quyết định Jev sau ngưỡng v2; cảnh báo CloudWatch khi `*_log_write_failed` > 0; đọc số liệu `a1_promise_unsupported` (loại B) sau vài ngày → quyết luật writer.
2. AA-695: shadow `a3_same_moment` + Sheet 150 cặp → rồi AA-741.
3. Theo dõi chi phí atomize trên Luna (lần publish tour mới) và `a1_keyword_about_tour` enforce (bộ từ khoá S1 có hụt không).

## Lưu ý kỹ thuật / BÀI HỌC (đã ghi `skill/aa-lessons/lessons.md`)
- Chi phí từ `llm_call_log` phải đối chiếu dashboard nhà cung cấp; ghi log lỗi = mất cache = trả tiền lại.
- Wave S1 xong chưa phải queue sạch: recompute tự động chạy sau vài phút → guard chặn deploy.
- A/B S1 ~30 tour phải có arm đối chứng lặp lại (dao động giữa 2 lần chạy ~±35%).
- Tham số model (temperature) phải kiểm ở request thật — đường Claude native từng bỏ ngầm.
- "Đã qua gateway" kiểm theo đường gọi, không theo việc có ghi cost (atomize từng gọi thẳng `invoke_claude`).
- **Atomize chỉ ở A3 platform** — tenant không atomize; tên `t5_`/`tenant_pipeline` là di tích (đã đổi ở #645). Note ở CONTEXT.md + skill `aa-ecosys-repos`.
- Deploy thay task api → giết script chạy trong container (A/B `run_detached`); không merge backend khi đang đo.
- Phiên AWS 8h hết giữa phiên 2 lần → cần Nghiệp nhập MFA.
