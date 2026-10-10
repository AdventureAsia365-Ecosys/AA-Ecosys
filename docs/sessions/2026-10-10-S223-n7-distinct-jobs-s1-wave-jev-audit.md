# S223 — Dọn N7 + distinctiveness, trang Jobs mới, đo wave S1, audit Jev (10/10/2026)

**Tác nhân:** Claude Code (VSCode/WSL), chế độ "dùng kiro-cli" · **ECS cuối phiên:** `aa-cis-dev-api:506` / `worker:61` (cùng SHA `5307549`, rollout COMPLETED, /health 200) · **Migration mới:** 207, 208 (đã áp Dev) · **Job queue:** sạch · **Kiro credit:** còn ~728/2.000 (dùng ~189 trong phiên, reset 01/11) · **Jev:** HẾT CREDIT từ 11:09 (VN) — breaker mở.

## Trạng thái đầu phiên
Khớp memory S222: api `:498` / worker `:53` cùng SHA `f298b05`, queue 0, /health 200, Kiro preflight OK (917 credit). Lệch nhỏ: AA-714 log ghi "In Review", Linear "In Progress" (giữ nguyên).

## Quyết định của Nghiệp (chỉ điều Nghiệp nói)
- Chốt danh sách S223: AA-747 (đo wave) → AA-753 → AA-754 → AA-695 → AA-741 (AA-741 chưa tới).
- Đóng AA-644 (trùng AA-714); AA-708 về Backlog; AAA giữ sau CIS (chưa có mốc).
- Tạo **AA-755**, làm trong phiên; mở rộng thành **thiết kế lại trang Jobs**: header/toolbar dính khi cuộn, lọc + sort mọi cột.
- Duyệt xoá 6 dòng `n7_*` (mig 207) và DROP cột/bảng distinctiveness + Competitors (mig 208).
- AA-747: **trần nudge giữ 3 mỗi version** (không phải mỗi tour); **bật per-day targets mặc định**; đóng AA-747.
- **Kiro được quyền ĐỌC Linear** (`get_issue`, `list_comments`), không ghi.
- AA-695: NO-GO gộp bằng containment/cosine; GO: transit/unnamed không tạo Segment + **dọn Segment kèm snapshot**.
- Tạo **AA-756** (audit Jev toàn hệ thống); áp 7 ngưỡng v2; shadow reject `a1_claim_supported` đo offline.
- **Chính sách writer: A được phép** (kiến thức nền về địa danh), **B cấm** (hứa hoạt động/dịch vụ/giờ/tầm nhìn nguồn không có).
- Giao Kiro ghi `decision_log.outcome` + tối ưu token grounding.
- **Giữ Jev**; chỉ tìm hiểu thêm OpenAI Decisions API làm dự phòng; KHÔNG tự host / không thay bằng Bedrock.

## Kết quả chính
**AA-753 — Done.** **#621** (Kiro 38 credit): xoá `acp_produce/gates.py` + 6 test, bỏ `n7_*` khỏi SAFE_DEFAULTS + UI. DRY RUN 6 dòng, 0 lời gọi từ trước tới nay; restore S3. **Mig 207** áp tay (deploy không tự chạy migration). Verify: 0 dòng `n7_*`, `/admin/llm-config` sạch.

**AA-754 — Done.** **#622** (Kiro 91 credit): gỡ distinctiveness T5/planning (trọng số ÷0,80)/API/portal + Competitors. **#624** mig 208 (merge tay): DROP cột + index, dựng lại `v_active_tour_atoms`, DROP 2 bảng competitor; restore S3. Verify: cột/bảng mất, view 23.933 atom, `/admin/atoms` 200. `db-schema-reference.md` sinh lại (mig 208).

**AA-755 — Done.** **#623** (Kiro 2 vòng ~40 credit) + **#626** (Claude: sort Attempt/By): API phân trang offset + sort whitelist + since/until/created_by/q + total; trang 3 tab, thanh lọc + header dính, pager 50/100/200, trạng thái trên URL. Live: `a3_atomize` total 960, trang cuối tới 29/09; sort cost toàn bộ; smoke production xanh.

**AA-747 — Done.** Wave 50 tour India (3 thử trước), rồi A/B per-day targets 10 tour (ngày lệch 69% → 17%, điểm 7,44 → 7,89, ngày dài quá nguồn 27 → 4, câu grounding sửa 65 → 55), **#625** bật mặc định. Wave đo lại cùng 50 tour: lên Master 80% → 84%, điểm 7,58 → 7,66, flag_fix theo mã 12% → 2%, tour >3 ngày nén 18 → 7, nudge 103 → 80, $1,51 → $1,45. Thiếu mốc S218 1 tour (3 tour Rajasthan FACT_CHECK chờ người) — Nghiệp đồng ý đóng.

**AA-695 — In Progress.** Đo: containment gộp sai ('tokyo' ⊂ 'tokyo tower'), cosine sai cả ở 0,90 → NO-GO. **#628** (Kiro 11 credit, brief sửa giữa chừng): atom chỉ bị loại khỏi Segment khi `unnamed_place` hoặc luật transit VÀ chính atom có loại transit/NULL — giữ 198/199 Segment Jev đã cứu (Nanta, yoga…). **Dọn 5.045 Segment** (2.242 rỗng + 2.803 toàn atom bị loại), 23.958 ranking + 5.502 member + 1.375 alias; snapshot `scripts/restore/s223_aa695_segment_cleanup_apply.json`. Sau: 8.517 Segment thật, tỉ lệ một tour 81,7% (đuôi dài thật).

**AA-756 — In Progress.** Audit Jev: `docs/audits/2026-10-10-S223-jev-audit.html` · artifact https://claude.ai/artifact/8A5XBeeUU5n7B8potPMt5q. Jev $8,44 từ 29/09 (6,5% chi LLM), 80% ở `a1_claim_supported` (gửi cả nguồn cho từng câu, TB 2.408 token). **Áp 7 ngưỡng v2** qua API (restore S3, hồ sơ **#627**). Shadow reject 0,30 `a1_claim_supported`: 24,6% câu, 49/50 tour → không bật; mẫu câu cho thấy 2 loại A/B → **#629** đổi luật writer. **#630** (Kiro 17 credit, chưa merge): ghi `outcome` khi duyệt Review Queue + xoá atom, API `/admin/decisions/outcomes/summary`. **#631** (Kiro 2 vòng ~24 credit, xếp chồng lên #630): grounding gửi mỗi câu nguồn của đúng ngày đó (+ ngày trước/sau + inclusions/exclusions) — đo trên 50 tour thật: nguồn gửi Jev 20,3M → 8,75M ký tự (−57%). Vòng 1 có luật bỏ qua câu "mô tả" theo từ khoá → đo thấy bỏ sót đúng loại B ("wildlife cruise… sightings", "full-day excursion") → đã bỏ hẳn.

**Kiro đọc Linear:** `aa-worker` thêm MCP `linear` chỉ `get_issue` + `list_comments` (test headless: đọc được, không có tool ghi); `kiro-run.sh` trust-tools + brief-template cập nhật.

## Sự cố trong phiên
- **Jev hết credit 04:09 UTC (11:09 VN).** Ảnh hưởng: thử 10 tour cho #629 vô hiệu (730 quyết định lỗi; 10 tour lên Master chỉ qua luật con số); recompute sau dọn Segment chạy khi Jev lỗi (2.878 demand, 113 landing, 134 type lỗi; cache vẫn đúng). Đã soạn tin Zalo cho chị Thư: xác nhận số đã nạp 04/10 (theo log tiêu $1,96 trước 04/10, $6,48 sau) và nhờ nạp thêm ~10 USD.

## Thay đổi hạ tầng / dữ liệu
- Migration 207 (xoá 6 dòng `n7_*`), 208 (DROP distinctiveness + Competitors) — áp tay qua ECS exec.
- Ngưỡng Jev v2 (7 câu) qua `PUT /admin/decisions/questions/{key}`.
- Xoá 5.045 Segment + dòng liên quan (snapshot S3). 2 lần recompute toàn hệ (lần sau trùng lúc Jev hết credit).
- Không Terraform.

## Kế hoạch phiên sau (S224)
1. **Sau khi chị Thư nạp Jev:** chạy canary (`POST /admin/jev-canary/check`) → recompute toàn hệ → chạy lại thử 10 tour cho #629 (`.tmp-session/s223/s223_promise_cmp.py`) → merge **#630**.
2. **#631** (giảm token grounding): sau khi có credit, chạy lại 200 câu calibration với nguồn theo ngày, kiểm độ chính xác accept ≥ 0,85 vẫn ≥ 97% → merge sau #630.
3. AA-756: kiểm tay 30 quyết định/câu sau ngưỡng v2; cảnh báo credit thấp; tìm hiểu OpenAI Decisions API; `a1_keyword_about_tour` gán nhãn hoặc tắt; câu Jev mới chỉ nhắm loại B.
4. **AA-748** (writer đọc dữ kiện có cấu trúc) — ưu tiên cao, gắn với chính sách A/B.
5. AA-695: `a3_same_moment` shadow + Sheet 150 cặp. Rồi AA-741.

## Lưu ý kỹ thuật / BÀI HỌC (đã ghi `skill/aa-lessons/lessons.md`)
- Mâu thuẫn Done-when ↔ implementation notes → hỏi Nghiệp, không tự sửa code (trần nudge).
- Trước khi gọi tên khoản "LLM dự phòng", `GROUP BY stage, provider, model` — Jev ghi song song vào `llm_call_log` (provider `typesafe`).
- Loại trừ theo luật ở bước mới phải khớp quyết định cuối của bước sau (`atom_ranking.excluded_reason`), không chỉ luật gốc.
- Deploy KHÔNG tự chạy migration — áp tay qua ECS exec (`.tmp-session/s223/s223_apply_mig.py`).
- `git add docs/...` trong App repo báo "ignored" và dừng chuỗi `&&` → dùng `git add -u` cho file đã track.
- PR backend xanh nhưng `BEHIND` → auto-merge đứng im; `update-branch` trước.
- `run_script.sh` dùng chung `/tmp/s.py` trong container → không chạy song song 2 script (output lẫn).
- Mode Jev đặt theo cả câu hỏi — muốn "shadow một phía" thì đo offline từ xác suất đã log.
- Không đóng phiên khi Kiro còn chạy: chờ xong, gác cổng, mở PR rồi mới ghi log (Nghiệp nhắc S223).
