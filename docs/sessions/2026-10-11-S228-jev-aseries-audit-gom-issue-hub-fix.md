# S228 — Khoá audit Jev A-series → gom issue → sửa bug hub (11/10/2026)

**Tác nhân:** Kiro (WSL/VSCode, AWS/MFA qua `aa365-admin` + `aa365-agent`)
**Bối cảnh:** tiếp sau S227. Nghiệp làm việc kiểu "giải thích/phản biện từng bước cho tới khi hiểu rõ rồi mới làm", đẩy mình đào sâu nhiều lần (đọc dữ liệu thật thay vì đoán).

## Đầu phiên — KHỚP memory (lệch nhẹ do commit sau S227)
- 4 repo sạch: root `675ba03`, App `2c84fe8`, TP `5738a2b`, Infra `14a816c`. ECS api:525/worker:80 SHA `08e5654`. `shared.job` sạch, 0 wave. STS cả 2 profile còn hạn.

## Quyết định của Nghiệp
- Khoá nốt audit Jev A-series; đọc kỹ từng issue; gom ý trùng; làm luôn.
- **Giữ HẾT câu hỏi Jev, không retire câu nào** — chỉ calib cho đúng/tốt hơn.
- Gom issue theo **Cách 1**: đóng 4 issue con đã đạt done-when, dồn calib về AA-756.
- Phủ phân tích **toàn bộ 16 câu A-series** (gồm 2 câu shadow), không chỉ 3 câu grey cao.
- Đọc **dữ liệu thật từng tầng** (tour/atom/segment/route/hub), tự đánh giá chất lượng + cross-ref Jev.
- Mở bug issue cho hub + làm luôn tới verify dứt điểm.
- **TREO audit/calib Jev**: ngưỡng vô nghĩa nếu chưa model hệ thống phản ứng gì + ảnh hưởng chất lượng sản phẩm; không đi thí nghiệm chỉnh số.
- Bỏ ý tưởng "điểm độ giàu lịch trình".
- Ghi lesson về cách Kiro/Claude Code làm việc (nghỉ giữa chừng, lòng vòng).

## Kết quả chính
- **Gom issue (Cách 1)**: live-verify gate enforce → đóng Done **AA-690/692/694/695** (build scope xong, có comment bằng chứng), dồn calib về **AA-756** (In Progress, mục Consolidated scope + 5 việc).
- **Phân tích Jev đầy đủ** → `docs/audits/2026-10-11-S228-jev-aseries-closeout.md` (Part 1–7, root `4e22889`):
  - 25 câu config: 3 choice + 22 noul, **không có kind=score** (scoring = s1_judge riêng, không qua Jev).
  - Funnel: 892 tour → 24.302 atom (+8.033 deleted) → 11.306 segment → 108.198 ranking (Score) → 1.331 route → 419 hub.
  - a3_activity_type loại 20% ranking rows thành transit (dấu chân lớn nhất). a3_demand/landing lọc chọn lọc. a3_atom_in_text guard bắt rò hiếm (124 reject/30d thật).
  - a1_claim_supported 58,6% grey, phân phối bimodal, knee ở p~0.15 → reject ≤ 0.15 (nhưng chưa áp được).
  - 2 câu shadow: a1_brand_fit n=0 (tie-break chưa chạm band) → hold; a1_promise_unsupported p-high=bad → accept_floor 0.70 shadow (sửa hướng ngược của chính mình ở Part 2).
- **Chất lượng dữ liệu (đọc tay)**: Atom CAO; Segment tốt-đỉnh/under-merge-đuôi (80% single-tour, nhưng merge thật chỉ 148/11.306, đa số logistics; Segment = place+VERB nên khác verb là khác segment ĐÚNG thiết kế); Route lành mạnh; **Hub BUG**; tour ~20% mỏng (≤10 atom).
- **AA-758 (bug hub) — Done, verified live**:
  - Root cause 2 tầng cùng lỗi `min()` mẫu số: `best_hub_match` (PR #653) + `families()` (PR #654, tầng collapse thật: 1 segment chung → ratio 1.0 → union-find bắc cầu **455 tour thành 1 family → 862 route 1 hub**).
  - Fix = Jaccard/union + tie-break xác định; 40 test route/hub xanh.
  - Verify: #653 deploy xong recompute (ef24cbca, $0, 232s) VẪN 862 → chứng minh collapse ở families(); #654 deploy (api:527 SHA `773d591`) recompute (7f747ea5, $0, 227s) → **862→84 route, 455→55 tours/hub**; hub 84 giờ là journey Delhi thật.
  - Orphan hub 405→425 (dọn sau, không gấp).
- **AA-756 TREO**: blocker rõ — cần (1) model hành động downstream per-question, (2) ground-truth cấp câu (Review-approve=0 vì Nghiệp regenerate; reject/soft-delete/flag_fix đều mislabel).
- **Lesson**: thêm section "Thái độ làm việc (Nghiệp chốt S228)" vào `skill/aa-lessons/lessons.md` — làm trọn việc không nghỉ giữa chừng; ngắn gọn kết luận trước; số thật không đoán; calib phải gắn hành động downstream + chất lượng sản phẩm.

## PR
- App #653 (hub reuse Jaccard) — merged+deployed.
- App #654 (families Jaccard, fix thật) — merged+deployed.
- Root: `540f651`/`6ff9be4`/`d647cda`/`eeda4e8`/`4ee26ce`/`a455abb`/`4e22889` (audit docs + lesson, push thẳng master theo lệ root).

## Lệch đã xử trong phiên
- Hiểu nhầm "a1_keyword_about_tour chưa calibrate" → thực ra đã có PR #634 (0.80/0.30), chỉ chưa chạy enforce.
- Đọc nhầm cột ERROR thành REJECT trên UI → xác nhận lại DB: a1 reject = 0.
- Query bỏ sót cache hit (AA-742 chuyển cache sang bảng riêng) → đối chiếu lại khớp UI.
- Fix hub lần 1 (#653) chưa đủ → đào ra tầng families() mới là gốc (#654).

## Việc cần làm đầu phiên sau (S229)
1. (Tuỳ chọn) Dọn orphan hub (425) — prune hub không được route sống tham chiếu, tidy-up $0.
2. AA-756 vẫn treo: nếu làm tiếp phải bắt đầu bằng **map hành động downstream per-question** rồi mới bàn ground-truth; KHÔNG chỉnh số trước.
3. Trục T-series (portal B2B) — mảng việc chính chưa đụng: AA-741 audit + AA-668/670/671/672 redesign.

## Lưu ý kỹ thuật
- Cache hit KHÔNG ở `decision_log` (từ AA-742) — đếm riêng ở `shared.decision_cache_hits_daily`, UI cộng vào. Query decision_log một mình bỏ sót cache. Số calib đúng = tập `NOT cached` (verdict gốc). UI Jev Decisions = Last 7 days + gồm cached; a1 UI "743" là cột ERROR không phải reject.
- Segment định danh = `(canonical_place, canonical_action→verb quy chuẩn)`; cùng place khác verb = khác segment (đúng).
- Route/hub tính toán thuần, không gọi Jev/LLM → recompute $0. ECS exec timeout 120s < recompute ~230s → enqueue job rồi poll `shared.job`, đừng chờ trong exec.
- Jev kind chỉ choice + noul, KHÔNG có score. "Score" của A3 = bảng tính `atom_ranking`.
