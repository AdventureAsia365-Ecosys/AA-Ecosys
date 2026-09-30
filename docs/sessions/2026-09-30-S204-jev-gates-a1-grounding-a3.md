# S204 — Jev chặn thật: chống bịa master content A1, judge A1, cổng A3 (30/09/2026)

**Tác nhân:** Claude Code (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:394` · **Migration mới nhất:** CIS 188

## Trạng thái
- **5 câu Jev đang enforce trên Dev:** `a3_keyword_belongs` (≤0.30, từ S203), `a3_question_foreign` (accept ≥0.95), `a3_question_about_here` (≤0.20), `a1_claim_supported` (accept ≥0.90, chỉ để xoá cảnh báo số liệu sai), `a3_landing_belongs` (≤0.30).
- **Shadow chờ Nghiệp review:** `a3_demand_belongs` (đề xuất ≤0.40), `a3_atom_in_text` (đề xuất ≤0.30). Còn shadow từ S203: A0 ×3, `a3_idea_traveller`.
- **AA-691 Done** (chống bịa A1), **AA-698 Done** (judge A1). **AA-694 In Progress** (A3-5 xong; A3-6, A3-1 shadow; A3-2 chưa làm). Issue mới **AA-697** (vẽ kiến trúc AWS, Backlog).

## Thay đổi Codebase
**AA-CIS-App (tất cả đã merge, CI xanh, deploy Dev COMPLETED):**
| PR | Nội dung |
|---|---|
| #496 | Hồ sơ hiệu chỉnh phạm vi quốc gia (Nghiệp sửa 1/54) |
| #497 | **AA-691** node `grounding` (A1): số liệu lạ → `UNSUPPORTED_NUMBER`, sửa **từng câu** theo nguồn (1 lời gọi `s1_flag_fix`), revalidate kiểm lại → `manual_check`; Jev `a1_claim_supported` (mig 186); `metadata.grounding` |
| #498 | CONTEXT.md: luồng A1 thêm grounding; notes live verify |
| #499, #500 | **AA-698** judge A1 chỉ chặn theo `brand_fit` (bỏ `cross_brand_distinct` + cap mission cho A1; T2 giữ nguyên) |
| #501 | Sửa câu lần 2 trong revalidate (khi flag_fix nudge chèn lại số liệu); hồ sơ `a1_claim_supported` sau review |
| #502 | **Sửa lỗi:** landing tự tính lại shortlist, bỏ qua lọc Jev → câu bị loại vẫn đếm qua claim-by-name; cổng landing `a3_landing_belongs` (mig 187) |
| #503 | Cổng A3-6 `resolve_demand` + A3-1 `ground_day_atoms` (mig 188, shadow); hồ sơ hiệu chỉnh 3 câu |

**Root repo:** #14 (log S203) merge; #15 ignore `docs/calib/*.xlsx|csv` + README link Drive.

## Thay đổi Hạ tầng / dữ liệu
- Migration 186, 187, 188 apply tay trên Dev **trước** deploy (chỉ thêm dòng `decision_question`).
- Enforce qua script ECS exec: foreign/about_here (lần đầu auto mode chặn, Nghiệp duyệt chạy), `a1_claim_supported`, `a3_landing_belongs`.
- Drive AdventureAsia: Sheet keyword belongs (reviewed), `jev-question-catalog.html`, 4 Sheet hiệu chỉnh mới (grounding, landing, demand A3-6, atom A3-1).

## Bằng chứng verify
- **Master content đang publish:** 337/7.911 câu trong 90/121 tour (74%) có số liệu nguồn không có → 302/87 sau khi code hiểu đổi đơn vị giờ/phút, giờ `12.30`, số dính chữ.
- Hiệu chỉnh `a1_claim_supported` (200 câu): accept ≥0.90 = 50/50; reject câu không số chỉ 19/21 → không bật `UNSUPPORTED_CLAIM`. Nghiệp sửa 5/59 (8,5%, đều theo Jev).
- **Judge Luna:** A1 GPT-4.1 trung bình 8,88 (n=354) vs Luna 3,20; shadow cùng input: distinct Luna 2–6 vs GPT-4.1 8–9.
- Smoke A1 đủ graph 3 tour trên :392: Mongolia 1→fixed (judge 8.0), Sri Lanka 12→pass, Bhutan 10→fixed; 0 câu sót; ~$0,03/tour.
- **Landing:** 11.143 cặp → 7.402 sau lọc quốc gia; chỉ 14% landing đúng; reject ≤0.30 = 125/125; Nghiệp sửa 1/62.
- **A3-6:** chỉ 33/100 keyword hạng 1 đúng; reject ≤0.40 = 88/88.
- **A3-1:** 63% atom platform không nằm trong text ngày của nó (prompt atomize gửi kèm summary/highlights cả tour); reject ≤0.30 = 127/127.
- Unit suite 2165 pass; 3 lỗi cũ (aa324 ×2, aa652) cũng lỗi trên main.
- Chi phí Jev cả phiên < $0,05; LLM smoke ~$0,5.

## Còn lại
1. **Nghiệp review** Sheet A3-6 (70 dòng) + A3-1 (47 dòng) → enforce `a3_demand_belongs` ≤0.40, `a3_atom_in_text` ≤0.30.
2. Sửa prompt atomize: preamble cả tour chỉ làm ngữ cảnh (A3-1 gốc rễ).
3. AA-694 Done-when: chạy lại atom ranking Bhutan, cho Nghiệp xem `questions_count` + demand trước/sau; A3-2 activity type.
4. Sau đó UI v2 (AA-662→) → runbook + chạy lại (AA-653/594). Theo dõi tỉ lệ HITL A1 (Luna brand_fit 7–8, sát ngưỡng 7.0).
5. `FORBIDDEN_WORD` vẫn là mã mềm trên 2/3 tour smoke (AA-641).
6. AA-697 (vẽ kiến trúc AWS) sau lần chạy lại.

## Lưu ý kỹ thuật
- Merge PR có `[AA-xxx]` tự chuyển issue Linear sang Done → mở lại khi còn việc (bị 4 lần trong phiên).
- ECS exec hay EOF giữa chừng: chạy script dài bằng `nohup` trong container (`.tmp-session/s204_run_detached.sh`), đọc kết quả qua S3.
- Ghép atom với text ngày: phải khớp `source_hash` với đúng version `generated_content` đã atomize (bản đang publish có thể khác).
- `git stash` trong lúc có file staged làm mất staged → phải add lại (đã xảy ra ở #502).
- Đọc Google Sheet >40 dòng: `read_file_content` chỉ trả mẫu; dùng `download_file_content` (CSV base64).
- Auto mode chặn ghi DB Dev lần đầu; chạy được khi Nghiệp yêu cầu rõ.
