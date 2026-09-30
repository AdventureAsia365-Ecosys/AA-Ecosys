# S205 — Hoàn thiện Jev A0/A1/A3: prompt atomize theo ngày, 13 câu Jev chặn thật, chặn gộp Segment khác nước (30/09/2026)

**Tác nhân:** Claude Code (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:399` · **Migration mới nhất:** CIS 192

## Trạng thái
- **13 câu Jev enforce trên Dev:** a1_claim_supported, a3_keyword_belongs, a3_idea_traveller, a3_question_foreign,
  a3_question_about_here, a3_landing_belongs, a3_demand_belongs, a3_atom_in_text, a3_activity_type, a3_same_place,
  a0_row_kind, a0_itinerary_usable, a0_country.
- **Shadow:** `a1_brand_fit` (A1-4 tie-break — hiệu chỉnh từ lần chạy lại).
- Nghiệp đổi hướng giữa phiên: **hoàn thiện Jev ở mọi stage trước khi chạy lại toàn platform** (không nhảy sang UI v2).
- Issue: AA-694 In Progress (chờ Nghiệp xem Score trên trang Social Content — đã xác nhận bằng Playwright), AA-692 /
  AA-695 In Progress (bị merge tự đóng, đã mở lại), AA-690 In Progress (còn A0-2), AA-693 In Progress (còn research
  run ≤ 10 place), AA-653 nhận input runbook.

## Thay đổi Codebase
**AA-CIS-App:**
| PR | Nội dung |
|---|---|
| #504 | **A3-1 gốc rễ:** `build_day_user_prompt()` rào SUMMARY/HIGHLIGHTS thành TOUR CONTEXT, chỉ trích atom từ phần ngày; SYSTEM_PROMPT thêm luật (fingerprint đổi → atomize lại mọi ngày ở lần chạy lại) |
| #505 | **A3-2:** `resolve_exclusions()` — luật transit vs activity_type atom, chỉ hỏi Jev khi mâu thuẫn (mig 189) |
| #506 | Sửa câu chữ `a3_activity_type` theo nghĩa của luật (transit = không đáng viết, gồm ăn/ngủ thường, briefing) (mig 190) + hồ sơ hiệu chỉnh |
| #507 | Ghi kết quả review A3-2 (0/160) |
| #508 | **AA-692:** A1-4 judge tie-break `a1_brand_fit` (mig 191, shadow); A1-3 mã meal/time chỉ bật khi nguồn không nói (giờ: tất định; bữa ăn: qua `a1_claim_supported`) |
| #509 | Hồ sơ hiệu chỉnh A0 ingest + A3-4 (auto-merge) |
| #510 | **AA-695:** Segment không gộp atom khác nước (id mới băm thêm quốc gia) + Jev `a3_same_place` (mig 192) |
| #511 | Hồ sơ hiệu chỉnh `a3_same_place` (auto-merge) |

**Root repo:** #16 (log S204) merge.

## Thay đổi Hạ tầng / dữ liệu (Dev)
- Migration 189, 190, 191, 192 apply tay trước merge.
- Enforce (script ECS exec): a3_demand_belongs ≤0.40, a3_atom_in_text ≤0.30, a3_activity_type ≥0.95,
  a0_row_kind ≥0.95, a0_itinerary_usable ≤0.20, a0_country ≥0.95, a3_idea_traveller ≤0.20, a3_same_place ≤0.10.
- **Dữ liệu (Nghiệp duyệt):** sửa quốc gia 7 raw_tours (Annapurna/Everest/Mustang India→Nepal; 3 tour Chiang Mai
  Laos→Thailand; Ride the Trail Laos→Vietnam); trash master+source 2 tour rác đã publish (Trip 3 – Meiji-no-Yakata,
  Yaksa Trek BEST DEAL) + soft-delete 7 atom.
- Atomize lại 3 tour Bhutan (fe697018, 5a6201bb, 22174c35) + 1 lần tính lại Score sau A3-2.
- Drive AdventureAsia: 5 Sheet hiệu chỉnh mới (activity type A3-2, A0 ingest, idea filter A3-4, same place A3-7) —
  Nghiệp chấm hết, **0 nhãn bị sửa** ở cả 7 Sheet của phiên (A3-6 70, A3-1 47, A3-2 160, A0 55, A3-4 132, A3-7 150).

## Bằng chứng verify
- **Prompt atomize:** tour ẩm thực 224→36 atom, Buddhist 78→25, Valley Hikes 33→16; đối chiếu từng ngày: atom khớp
  text ngày, không thiếu; `a3_atom_in_text` reject 0/51 atom mới.
- **Bhutan trước/sau:** questions_count 1.716→1.593; demand US 426.490→241.870 (Chari Monastery 90.500→0 "monastery").
- **A3-2 enforce:** US ranked 2.486→2.510, transit 707→679 (79 vào lại: nghi lễ/workshop/safari; 51 hậu cần bị loại).
- **Playwright** trang admin Social Content → Score: tour Buddhist có "attend the fourth teaching", "evening puja"
  được xếp hạng (trước bị loại vì opener `attend`); tour ẩm thực chỉ còn moment đúng ngày. 0 console error.
- **A0 trên 793 tour:** non-tour ≥0.95 9/9; itinerary ≤0.20 33/33; country ≥0.95 738/745 (7 lệch = dữ liệu sai).
- **A1-3 đo:** regex meal/time bắn 41/125 tour; 14/17 giờ có sẵn trong nguồn; 26/34 nguồn cũng ghi bữa ăn.
- **A1-2 bỏ:** s1_brand_audit 36 lời gọi / $0.18 trong 30 ngày.
- **A3-7:** 384/3.337 Segment trộn tên, 65 xuyên quốc gia; 1.020 cặp, Jev 663 cặp ≤0.3; mẫu 150 cặp ≤0.10 = 30/30.
- Unit suite 2.189 pass; 3 lỗi cũ (aa324 ×2, aa652) cũng lỗi trên main. `/health` 200 trên :399.
- Chi phí phiên: LLM atomize ≈ $0.10; Jev ≈ $0.2 (demand/landing/type/A0 793 dòng/same-place 1.020 cặp).

## Còn lại
1. **AA-696 T-series** (tenant test, 9 điểm Jev) — việc Jev lớn cuối cùng trước lần chạy lại.
2. **A0-2 phát hiện trùng gần giống** (AA-690) — chưa làm.
3. AA-693: 1 lượt research ≤ 10 place để thấy keyword bị loại trong decision_log (tốn DFS nhỏ).
4. AA-692: hiệu chỉnh `a1_brand_fit` từ lần chạy lại.
5. AA-694: Nghiệp xác nhận Score trên trang Social Content → Done.
6. Rồi UI v2 (AA-662→) → runbook + chạy lại (AA-653): **dựng lại Segment từ đầu**, atomize lại mọi tour, bỏ dòng A0 mỏng.
7. Luật transit (opener `attend`/`board`/`ride`/`receive`) còn loại nhầm nghi lễ khi atom không mâu thuẫn — quyết định riêng.
8. `a0_country` chỉ hỏi khi resolver không ra nước; resolver tự nó đã sai 7 tour — chưa làm nhánh "itinerary nêu nước khác".

## Lưu ý kỹ thuật
- Merge PR có `[AA-xxx]` tự chuyển issue sang Done — bị liên tục; mở lại sau mỗi merge.
- Auto mode chặn ghi DB Dev / tạo script ghi DB nhiều lần trong phiên → Nghiệp tắt auto mode để chạy.
- STS hết hạn: `echo <mã MFA> | aws sts get-caller-identity --profile aa365-admin`.
- Deploy đang chạy: task mới chưa có exec agent → chọn task đang RUNNING; `taskArns[0]` có thể là task mới.
- Script import hằng số từ code chưa deploy sẽ lỗi trong container → khai báo trực tiếp trong script.
- ECS exec EOF giữa chừng: dùng `.tmp-session/s204_run_detached.sh` (nohup) + đọc kết quả qua S3; runner chung
  `.tmp-session/s205_run.sh <script.py>`.
- Sheet Drive: đọc bằng `download_file_content` (CSV base64). Playwright admin: script `.tmp-session/s205_score_ui.mjs`
  (chromium-1217), tên tour trong dropdown là `src_name` viết hoa.
- PR docs bị BEHIND chặn auto-merge → `gh api -X PUT .../pulls/N/update-branch`.
