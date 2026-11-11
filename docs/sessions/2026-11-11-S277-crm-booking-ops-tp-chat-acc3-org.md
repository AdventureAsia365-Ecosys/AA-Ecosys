# S277 — 11/11/2026 (Claude Code — VSCode/WSL, Ultracode)

**Tác nhân:** Claude Code. **Thời gian:** 11/11 ~08:00 → ~21:15 +07. Đổi tài khoản Claude 1 lần (chạm hạn mức 5 giờ), 3 cửa sổ tắt auto mode, MFA còn hạn tới 21:54.

## Trạng thái

- **Done có bằng chứng live:**
  - AA-1041: R7 planner + chat lập kế hoạch; Lighthouse 45 → 62 sau #254.
  - AA-1071, AA-1072: CRM.
  - AA-1073, AA-1074, AA-1075: Booking.
  - AA-1085: crm-058.
  - AA-1076, AA-1078, AA-1083: đã đóng từ đầu phiên.
- **Mở lại AA-1077:** sàn seed 600 từ đã chạy và replay $0 đạt. Extend repair thử 3 bài, 0 bài đạt (0,02 USD), nên để tắt. Chờ một lượt blog audit để đóng.
- **AA-1049:** bỏ hướng A (ghép lại phần cố định của 708 Master bằng code).
  - v1 cắt câu Overnight/Distance mà không thêm gì vào, nên trang mất thông tin.
  - v2 đổi "breakfast, dinner" thành mã "B, D" và sinh dòng bữa ăn mâu thuẫn.
  - Cả 6 tour thử đã khôi phục, 2 wave đã đóng.
  - Con số "708/280" của audit chỉ là khác cách trình bày, trang không lỗi.
- **Còn In Progress / In Review, chuyển sang S278:** AA-1077, AA-1079, AA-1080, AA-1081, AA-1084, AA-1049, AA-1069, AA-1070.

## Thay đổi Codebase (đã merge, deploy, verify)

- **CIS:**
  - #1444, #1445: script recompose. Chỉ dùng DRY RUN; APPLY bị chặn khi `facts_lost > 0`.
  - Infra #772: `T7_BLOG_MIN_SEED_WORDS=600` trên worker.
- **TripPlanner:**
  - #252: chat; tp-029 `ai_spend_month`; Infra #774 thêm WAF Challenge cho `/api/trip/chat`.
  - #253: sửa 4 điểm từ smoke.
  - #254: hiệu năng (Mapbox sau first paint, chat lazy).
- **CRM (AA-Partner):**
  - #274/#276/#278/#279: crm-056/057/058.
  - #281: test chập chờn do `request_id` ngẫu nhiên.
  - #282: 4 lỗi Book now / VNPay.
- **Booking:**
  - #222: smoke Playwright có đăng nhập.
  - #223/#224: bk-047, agency ops.
  - #225: UI finance.
  - #226: admin image bỏ `playwright.config.ts`; Deploy Admin Dev đã hỏng 3 lần từ #222.
  - #227: panel Agency terms.
  - #228/#229: bk-048, bảng ngày khởi hành, phí, điều chỉnh giá.
  - #230: trạng thái đang tải của lịch, nhãn "plan hint", spec chờ dữ liệu.
- **Root:**
  - #694, #696, #700: dòng DM-7.1 và contract 1.7/1.8.
  - #701: ship_wave merge main vào nhánh @after bị tụt sau main.
  - #697/#698: bot.

## Thay đổi Hạ tầng / tài khoản

- **acc3 vào AWS Organization của acc1** (acc1 là payer, không có workload).
  - Identity Center của acc1 ở ap-southeast-1; đã gán AA-Admin cho acc3; profile CLI `acc3-sso`.
  - Credit Lift của hai account được gộp, nhưng không trả cho Claude trên Bedrock (bán qua Marketplace, Cost Explorer tháng 9 và 10).
  - Ticket AWS mở từ acc1: 179438941000223. Đã ghi vào ADR 0001a (Note S277), bảng account trong CLAUDE.md và memory.
- **Migration đã áp:** crm-056/057/058, bk-047/048, tp-029.

## Bằng chứng verify

- Snapshot cuối phiên: `docs/audits/2026-11-11-S277-session/state-snapshot.md`.
  - 7 service COMPLETED, revision đang chạy là revision mới nhất.
  - CIS 398 @318a7982; Booking bk-048 @69c4ffb0, admin d7ea1341; CRM crm-058 @066560e7; TripPlanner 63a2aa2a.
- **Booking:** `docs/audits/2026-11-11-S277-booking-uat/` (`items-evidence.md` bằng chứng từng mục; smoke có đăng nhập 8/8).
- **CRM:** `docs/audits/2026-11-11-S277-crm-live-verify/` (trọn vòng ở chế độ stub, sau bản sửa đạt 7/7).
- **TripPlanner:** `docs/audits/2026-11-11-S277-tp-chat-smoke/` (smoke chat, ledger 0,067 USD, `lighthouse/`).
- **Jira đã đăng** (tech lead duyệt): PR-22 10641, PR-24 10642, PR-25 10643, PR-26 10644. Ảnh của PR-24/25/26 chưa gắn: VPN chặn `api.media.atlassian.com`.

## Còn lại

- Gắn ảnh vào 3 comment Jira khi tắt VPN (10 file trong `.tmp-session/S277/jira_img/`).
- **AA-1084:** trung vị 2 ngày (13/11) và lượt chạy đầu tiên của bot durations.
- **AA-1077:** một lượt blog audit T-series dưới sàn 600 (khoảng 2–4 USD, cần tech lead duyệt).
- **AA-1069, AA-1070** (CRM điều hành): kiểm live từng mục.
- **AA-1079/1080/1081:** ảnh UI và số đo.
- **Điều khoản `departure_fees` (Booking) đang ở dạng nháp:** chủ doanh nghiệp duyệt nội dung thì đại lý mới thấy.

## Lưu ý kỹ thuật cho phiên sau

- Sau khi merge PR Booking có đụng `frontend/`, phải đọc thêm image của `aa-booking-dev-admin`. ship_wave chỉ chờ API, mà PR thuần FE thì làm ship_wave báo "exit 5".
- User E2E staff của Booking chỉ có quyền đọc, mọi POST đều 403 kể cả dry_run, nên phần ghi chỉ kiểm được bằng CI. Agency API chưa có credential thử.
- Model Sonnet 5.5 trên acc3 vẫn bị từ chối, gateway tự chuyển sang Sonnet 4.6 (ledger tp_plan_chat).
- Dùng `aws configure set` được khi tắt auto mode; còn `aws configure get` thì bị luật quyền chặn.
