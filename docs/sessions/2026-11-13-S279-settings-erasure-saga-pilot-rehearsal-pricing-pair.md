# S279 — 13–14/11/2026 — Settings cho mọi ngưỡng, saga xoá dữ liệu khi offboard, diễn tập pilot có video, cặp E2E định giá

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). **Thời gian:** 13/11 ~06:30 → 14/11 ~09:50 +07 (đêm có khoảng nghỉ);
chạm trần 5 giờ 1 lần (23:10, các lane chạy lại), MFA `aa365-admin` hết 06:14 sáng 14/11 và làm mới lúc ~09:15.

## Trạng thái

- **Done (có bằng chứng live):** AA-1087, AA-1088, AA-1070, AA-1092, AA-1094 (đầu phiên); AA-1097 (ratchet 4 repo + tách
  `admin_pipeline`); AA-1098 + AA-1099 (thiết kế Academy + kit dự án mới, 31 quyết định đã duyệt, tạo AA-1102…1105).
- **Còn In Progress / In Review:**
  - AA-1096 (L1–L6 live; còn: đổi thử 1 giá trị mỗi app, `settings-lint` bắt buộc ở 3 repo, trang Platform › Infra).
  - AA-1093 (saga live, drill DRY RUN có video; lần xoá thật B–F phiên sau, chuẩn bị A1–A6 xong).
  - AA-1091 (cặp E2E định giá live; chạy giá giả lập phiên sau, cần owner cấp preset).
  - AA-1086 (34 video, 32 PASS; còn REH-06 quay lại, REH-08a Book now, bước giá, X1/marker).
  - AA-1048 (prompt v2 = no_go; bước kế v3 cho câu diễn đạt lại).
  - AA-1077 (l27 live; nguyên nhân giữ bài chính là độ dài F4).
- **Issue mới:** AA-1102, 1103 (kit dự án R1–R2b / R3–R6), AA-1104, 1105 (Academy P1–P2 / P3–P4), AA-1106 (catalogue tính
  năng + liên kết, UI ở CIS admin › Product map).
- Số liệu live cuối phiên: `docs/audits/2026-11-13-S279-session/state-snapshot.md`.

## Quyết định của tech lead (trong phiên)

- 06:50 duyệt 10 việc (hội tụ WIP trước, rồi AA-1086 + AA-1093); trần trả phí LLM phiên 5 USD.
- 07:35 AA-1093 D1–D11 theo đề xuất, riêng D2 = 90 ngày (CRM tự xoá sau 90 ngày); AA-1048 đổi 5 nhãn ok → violation.
- AA-1092: hoãn rủi ro 2 (CloudFront + WAF trước TripPlanner API) và 3 (rate CRM theo IP) tới trước pilot thật.
- Mọi ngưỡng/giới hạn/trần chỉnh được trên trang admin, có giải thích từng thông số (memory `policy-values-editable…`).
- 13:53 duyệt `cis.t7.blog_chars_per_seed_word` = 3.364.
- 17:20 "Chạy, diễn tập thì quay video lại" (memory: mọi drill/diễn tập đều quay video).
- ~19:40 tour X diễn tập = Philippines (Dev chưa có tour Laos có giá/bán cho đại lý).
- ~20:45 làm theo đề xuất: dòng tour AA đã xác nhận hiện cho khách mặc định; chép ngày/điểm đến tour AA vào đề xuất;
  chuỗi blog dùng tour mô tả dày; sửa kịch bản REH-06.
- Duyệt cả 31 quyết định AA-1098/1099 (trang quyết định).
- ~22:50 "làm luôn, giá giả lập thôi": AA-1093 xoá thật trên tenant tổng hợp + AA-1091 giá giả lập với danh tính E2E.
- ~00:20 AA-1093 phần xoá thật để phiên sau (cần 3 lần bấm Cognito trong một cửa sổ trước 07:00).
- Tham chiếu AWS AgentCore: ghi vào AA-704 làm nguồn nghiên cứu.
- Tạo AA-1106 (catalogue tính năng + liên kết), UI đặt ở CIS admin.
- 14/11 duyệt "Đăng" 4 comment Jira.

## Thay đổi Codebase (PR đã merge, chính)

- **CIS:** saga xoá 408–411 (#1476/#1477), settings registry + Platform › Settings (#1471/#1472, 407), ngưỡng chất lượng
  (#1479/#1480, 412–413), settings TripPlanner (#1482/#1483, 414–415), hướng dẫn từng setting (#1485/#1486, 416), tab CRM
  (#1487), ratchet (#1473), tách `admin_pipeline` (#1478), A10b-5 drill (#1484), instrument v2 (#1481 417 + #1488),
  repeat drop đọc F13_hygiene (#1489), preset định giá cho E2E CS (#1490).
- **Booking:** bk-056 + Pricing › Policy đọc ngưỡng (#243/#244), bk-057 xoá tenant (#246/#247), hướng dẫn chính sách
  (#248), cặp E2E định giá (#249), ratchet (#245).
- **CRM (AA-Partner):** crm-063 cờ tour ngừng (#298/#299), ratchet (#300), G1/G2/G9 (#301), crm-064 settings (#302–#304),
  smoke giá (#305), crm-065 + hiện dòng AA / chép ngày tour (#306/#307).
- **TripPlanner:** tp-030/031 + jobs xoá/backup (#259/#260/#262/#263), settings (#264), feed xoá 5 phút (#265), ratchet (#261).
- **Repo gốc:** hợp đồng xoá + DPA + runbook (#747), retention rows, runbook onboarding pilot (#740), nghiên cứu Academy +
  kit (#757), harness UAT diễn tập (#760, #761), ADR 0006a A10e-2 (#762), giải thích Settings (#755).

## Thay đổi Hạ tầng

- Infra #804 (budget acc1 chỉ cảnh báo), #807/#809/#811/#812/#814 (saga), #820 (bỏ env CRM), #821 (migration-sync
  `--input`), #827 (probe owner-only), #829 (lịch erasure_feed 5 phút), #832 (L6: bỏ env settings khỏi Terraform, literal →
  biến, xoá 4 usage plan, output `platform_limits`), #833 (trigger WORKFORCE + mailbox cho cặp định giá), #834 (công tắc xoá
  Booking + script đọc lại). Mọi apply qua `terraform-apply.yml`, plan khớp từng lần.
- Danh tính E2E mới `e2e-booking-pricing-checker@` (booking-contracting). Tenant tổng hợp `aa1093-erase-01` (giữ cho AA-1093).

## Bằng chứng verify (chọn lọc)

- Diễn tập pilot: 34 video (EN + VI) trên Drive, trang tóm tắt https://claude.ai/artifact/9KCRRJ1cuGULqBHZeVeAmC;
  index `docs/audits/2026-11-13-S279-session/uat-rehearsal/` (+ `videos.html`, không link Drive). DRILL-01 v5 PASS 11/11.
- AA-1048: dry run, trial 3 (0,0015 USD), full 50 (0,0316 USD, ledger 150/150) → no_go (FP dropped 48 % < 60 %, TP kept 90 %).
- AA-1077: replay $0 48 bài, 0 drop, không gate nào khác đổi.
- AA-1096 L6: apply 3/2/7, CIS + CRM + Booking chạy revision mới, env cũ đã bỏ, Lambda TP sạch, usage plan 0.
- AA-1093 A6: CIS 39 dòng/8 bảng (digest `319239b2…`), Booking 1 audit, re-read master: TP PASS (137 phiên thấy được),
  Booking FAIL (đúng trước apply), CRM 0/126.
- Chi phí LLM trả phí cả phiên: ~1,7 USD (diễn tập 0,49 USD; AA-1048 0,033 USD; AA-1077 thử 4 ~0,3 USD; còn lại trial/probe).

## Jira

Đã đăng 4 comment (tech lead duyệt 14/11): PR-22 #10649, PR-25 #10650, PR-26 #10651, PR-20 #10652
(`docs/audits/2026-11-13-S279-session/jira-drafts.md`). Trang video là artifact riêng tư: tech lead mở chia sẻ cho chị Thư.

## Còn lại (việc chưa xong)

1. AA-1093 B–F (xoá thật tenant `aa1093-erase-01`): tech lead bấm bật setting, duyệt fingerprint, tắt setting; 2 PR Infra
   bật/tắt công tắc; runbook `.tmp-session/S279/aa1093-apply/RUNBOOK.md`. Rủi ro R1: `APPLIED_SQL` của Booking chưa theo round.
2. AA-1091: owner cấp preset Pricing team cho `e2e-cis-cs@`, chạy runbook bước 2–10 (giá giả lập), rồi gỡ preset.
3. AA-1096: đổi thử 1 giá trị mỗi app, `settings-lint` bắt buộc ở Booking/Partner/TripPlanner, trang Platform › Infra.
4. AA-1086: REH-06 quay lại, REH-08a (bật Book now + form key), REH-01 giá (sau AA-1091), X1/marker.
5. AA-1048 v3 (câu diễn đạt lại), AA-1077 đường độ dài F4.
6. AA-1106 catalogue (Ultracode), AA-1102…1105 theo slot.

## Lưu ý kỹ thuật cho phiên sau

- Bài học mới đã vào `skill/aa-lessons/lessons.md` (ship_open_prs dừng cả lô; `gh pr edit` lỗi GraphQL → REST; boto3
  `--profile ""`; mã MFA qua stdin; hook PII > 2 MB; ecsx timeout; link Drive trực tiếp; deploy trước apply chép mẫu cũ).
- Repo gốc còn 4 file đổi ở checkout chính trước phiên: `.claude/settings.json` (quyền cục bộ, không commit).
