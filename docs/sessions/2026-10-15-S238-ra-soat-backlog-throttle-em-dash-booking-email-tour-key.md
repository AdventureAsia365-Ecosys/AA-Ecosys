# S238 — 15/10/2026 — Rà soát toàn bộ backlog, throttle TripPlanner, em-dash T9/T2, email Booking, tour key v1.2

**Tác nhân:** Claude Code (VS Code, Ultracode). Điều phối + 7 workflow nhiều agent (rà soát backlog 41 agent, 4 đợt
lane build trong worktree + review đối kháng + vòng sửa, điều tra OTel). Agent con chỉ commit; push / PR / merge /
apply / deploy / verify live do phiên chính làm. Tối đa 3 agent song song (WSL 8 GB).
**Audit:** `docs/audits/2026-10-15-S238-backlog-audit/` (README + backlog_audit.json, aa819-429/, aa831/, aa833/,
aa802/, pr17/*.docx, jira-drafts.md). **Backlog sống mới:** `docs/backlog/README.md`.

## Trạng thái cuối phiên
- ECS CIS api :626 / worker :183 (cùng image #754), COMPLETED, `/health` 200. Booking :19, `/booking/health/ready`
  = bk-011. TripPlanner Lambda từ #83.
- Migration áp trong phiên: CIS **235** (v_tour_place day text theo tour), **236** (tenant_config 8 kênh); Booking
  **bk-011** (key tour trên trip_case_legs). Đều qua DB Migrate check → apply.
- Terraform apply (targeted, đọc plan trước): alarm throttle TP (#133), env SES Booking + bỏ env gmail TP (#134),
  budget theo App (#135), tag App 88 resource + budget shared (#136, loại RDS instance / CloudTrail / secret drift),
  env cảnh báo email CIS (#138). RDS + CloudTrail gắn tag `App=shared` bằng API chỉ-thêm-tag.
- `shared.job` + `booking.job` rỗng (chỉ job pull định kỳ). Vercel Hobby **chạm giới hạn build/ngày** 15/10 tối.

## Quyết định của Nghiệp
- Rà soát toàn bộ issue mở + artifact data standards, tạo issue còn thiếu, sắp lại danh sách việc → đã làm
  (69 issue, 14 issue mới AA-830→843, 17 việc gộp vào issue có sẵn).
- Không nhắc nữa: auto-renew Namecheap, lưu trữ issue Linear, `.wslconfig` 12 GB (dùng 8 GB).
- Facebook Live round trip PR-7 đã làm xong (Nghiệp test) → AA-840 Done không cần thêm round trip.
- AA-811: email do **Booking** gửi (đúng ranh giới ADR 0004), hộp thư `nghieppham@adventure.asia`.
- "Làm luôn": gắn tag App cho hạ tầng + email cảnh báo chi phí LLM.
- Lưu thông tin test WP/FB vào Secrets Manager (`aa-cis/dev/e2e-wordpress-test`, `aa-cis/dev/e2e-facebook-test`).
- Nháp Jira: chỉ nói tính năng đã làm, bỏ "như đã hứa", bỏ "ạ"; gom toàn bộ nháp ở cuối phiên để duyệt một lần,
  không hỏi lắt nhắt giữa phiên.
- AA-842 (OTel): đồng ý phân tích — chưa làm, để Backlog; chỉ làm phương án B (span ở cổng chung) khi cần.
- AA-841: Nghiệp hỏi vì sao phải xoay mật khẩu → giải thích: không có gì hỏng; file cũ trong git có mật khẩu dạng
  chữ thường, xoay chỉ là phòng ngừa, tuỳ Nghiệp quyết.
- Dừng phiên; ghi lại toàn bộ rà soát để phiên sau bắt đầu ngay, không audit lại.

## Thay đổi Codebase
- **CIS:** #746 mig 235; #747/#748 hướng dẫn Facebook + sửa mobile; #749 em-dash T9 (autofix, prompt, F2 guard);
  #750 Ready-to-Publish chỉ bản mới nhất; #751 Slate theo kênh tenant + mig 236; #752 em-dash T2; #753 email cảnh báo
  spend budget (`ops_alert_email`); #754 bỏ lượt acc2-native trong chuỗi writer cũ.
- **Booking:** #16 email nhân viên khi có inquiry (`bk_notify_email`, SES) + deploy lấy revision mới nhất; #17 bk-011;
  #18 intake v1.2 + backfill `app.inquiry.leg_keys`.
- **TripPlanner:** #81 bỏ prefetch thẻ + retry 1 lần; #82 notify chỉ log (email chuyển sang Booking); #83 gửi v1.2.
- **Infra:** #132/#137/#140 bản copy migration; #133 alarm throttle; #134 env SES Booking; #135 budget theo App;
  #136 tag App + propagate_tags; #138 env cảnh báo email CIS; #139 bỏ tfvars cũ + xoá `envs/` + gitleaks; #140 kiểm
  orphan DM-4.2 trong dump đêm.
- **Gốc:** #82 contract `inquiry.submitted.v1.2`; PR S238 (log này, backlog sống, audit, steering, lesson).

## Bằng chứng verify
- **Throttle TripPlanner (gốc):** `v_tour_place` lọc `ANY` không đẩy xuống `_tour_day_text` → parse cả 892 tour mỗi
  lần (~0,9 s). Sau 235: 1 tour 872→24 ms, 24 tour 904→81 ms; dội 8 trang điểm đến: Lambda TB 1,25 s (trước 6–13 s).
  Trang chủ prod: 0 request prefetch khi tải/cuộn/hover. Alarm: threshold 5, 2/3 kỳ, không OK action.
- **AA-819:** 429 live trên portal (giới hạn 3/ngày) kèm 6 ảnh; đã trả giới hạn mặc định + ngắt WP.
- **AA-831:** UI verify 1440/390: đủ 3 quyền, Live mode, link hướng dẫn, 0 lỗi console.
- **AA-778:** r6 live 3 bài $0,16 → em-dash 13,6 → 0/1.000 từ; T2 2 tour live $0,25 → 0 em-dash lưu trữ (bản nháp chỉ
  còn 15 dấu "Day N —", đã chuyển "Day N · ").
- **AA-811 Done:** 3 email về hộp thư DreamHost (TC-000004, TC-000005, cảnh báo budget test) — ảnh của Nghiệp.
- **AA-802:** Ready to Publish atlas-hearth 48→3, terra-family 47→4.
- **AA-840 Done:** Slate terra-family facebook/instagram/tiktok 8 mỗi kênh (trước 0), job $0.
- **AA-828:** 4 budget App + tổng; 40 resource `App=cis`, 50 `App=shared`; email cảnh báo LLM gửi thật (SES message id).
- **AA-830 Done:** bk-011, backfill 8/8, TripPlanner gửi v1.2 → TC-000005 key `cis/f9eba2f0…`, 0 orphan.
- **AA-843:** 23 test + mutation; lượt acc2 tốn ~0,1 s/lượt writer (p90 0,4 s) — chờ 24 h log.
- **AA-842:** báo cáo OTel (Notion Program Brain + `apps/AA-CIS-App/docs/investigations/llm-otel-tracing.md`).
- Chi phí LLM phiên ≈ $0,45 (r6 $0,16, T2 $0,25, slate $0, alert test $0).

## Linear
- Done: AA-830, AA-811, AA-840, AA-634, AA-709. Canceled: AA-696, AA-699. AA-708 → In Progress.
- Tạo mới: AA-830→AA-843. Comment bằng chứng / scope addition: 802, 804, 806, 807, 712, 708, 683, 741, 751, 778,
  813, 817, 819, 825, 828, 829, 831, 833, 841, 842, 843.

## Còn lại (phiên sau) → xem `docs/backlog/README.md`
- §1 Time-gated: AA-843 (≥16/10), AA-828 Cost Explorer (≥17/10), AA-801 (≥21/10), AA-833 (≥22/10), AA-714 (31/10),
  AA-820 (≤11/11), AA-819 (12/11).
- Jira S238 đã đăng (Nghiệp duyệt): PR-7 10474, PR-17 10475 (kèm .docx), PR-12 10476, PR-11 10477 — có ảnh/file chèn.
- §2 Chờ Nghiệp: AA-820 luật sư; các
  quyết định đóng/đổi phạm vi; các lượt chạy tốn tiền.
- §3 Hàng đợi: AA-703 Cognito Phase 0, AA-817, AA-806, AA-708 CloudFront, AA-802 silent correction, AA-834, AA-712 L4,
  AA-800/777/780, Booking 822/823/679 → 682, AA-832, AA-827, AA-825, AA-751, AA-836/837 (frontend, gộp PR vì giới hạn
  Vercel)…

## Lưu ý kỹ thuật cho phiên sau
- Lesson mới: lọc `ANY($1)` không đẩy xuống qua join trong view — EXPLAIN đúng dạng lọc của consumer.
- Plan Terraform toàn root còn 16 drift ẩn (AA-806): luôn `-target`, đọc plan, loại RDS instance / secret version /
  random_password / CloudTrail bucket policy. zsh không tách `$T` → chạy `bash -c` với mảng.
- Hai PR backend merge sát nhau → deploy đầu fail ở bước kiểm SHA (benign nếu api/worker cùng SHA mới).
- Vercel Hobby giới hạn build/ngày: gom PR frontend.
- `exec_s3out.sh` + `jobcheck2.py` (S237) vẫn là cách đọc DB / kiểm job an toàn.
