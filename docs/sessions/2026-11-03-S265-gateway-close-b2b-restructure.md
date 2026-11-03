# S265 (03/11/2026): đóng cổng AI (H1/H2/E4/E5/D2), báo cáo chi phí tháng 10, tái tổ chức hệ sinh thái theo mô hình chỉ B2B (ADR 0019), R0

Tác nhân: **Claude Code (Ultracode)** (VSCode/WSL; lane code trong worktree qua `tools/workflows/lane.js` → 2 reviewer độc
lập → vòng sửa; workflow nhiều agent cho tư vấn/đánh giá; điều phối merge/deploy/DB Migrate/Terraform/kiểm live).
03/11 ~06:25 → ~15:45 +07 (02/11 23:25Z → 03/11 08:45Z). Số liệu cuối phiên lấy từ snapshot
`docs/audits/2026-11-03-S265-close/state-snapshot.md` (15:40 +07).
Nguồn diễn biến: checklist sống `.tmp-session/S265-checklist.md`, tab "Phiên" của tracker, Linear, `gh pr list` 6 repo.

Môi trường: MFA hết hạn 1 lần (~07:30, Nghiệp nhập lại 08:36); **1 cửa sổ tắt auto mode** (~12:10–12:50) cho Terraform
apply local + secret env GitHub. Lane chạy song song tối đa 4–5; 0 lane đang chạy khi chốt.

## Quyết định của Nghiệp (tech lead)

- **06:40:** "ok" — duyệt danh sách S265.
- **08:42:** gửi câu hỏi cho Sunny Cloud / IDS (email + Zalo, 20 câu, đối chiếu hợp đồng Sunny Pay: 4 % là chiết khấu,
  Điều 4/10 = gia nhập Org của IDS, Điều 6.3/10.2 tạm ngưng không báo, Điều 7 tự sửa hợp đồng). Nội dung hợp đồng không vào repo.
- **~10:45:** tp-024 (xoá `tripplanner.llm_spend_daily`) **xoá luôn theo ngoại lệ DM-3.8/3.9** như tp-018; F3 được **bấm
  Draft 1 lần**; cấp `ai_assist` cho "Lữ hành Sen Vàng" trong CIS admin.
- **~10:30:** yêu cầu lớn sau họp tuần 02/11 với chị Thư: tái tổ chức thành mô hình **chỉ B2B** (AA chỉ phục vụ tenant;
  CIS Content là gói nền; CRM và TripPlanner là add-on; Booking chỉ B2B; TripPlanner thành sản phẩm white-label đa tenant;
  vai trò staff rõ ràng; quy định dữ liệu theo vùng) → workflow tư vấn.
- **~12:10:** "đã tắt" auto mode → cửa sổ MFA.
- **~13:15:** tắt rồi bật lại AI cho app Partner CRM trong CIS admin (kiểm H1c).
- **~14:00:** duyệt trang quyết định **44/44** (40 theo đề xuất; TL-6 gộp portal vào web ngay, TL-9 mọi hoá đơn ở
  Booking, TL-16 pilot trên Dev có dữ liệu thật, TL-23 TripPlanner frontend sang ECS); đọc bản giải đáp: "ok hết".
- **~14:20:** `ai_ops` được đọc text tenant trong Writing Lab (có log); đồng ý Fargate + WAF (bật ở R5) + backup RDS 14
  ngày; giữ M2M nội bộ, API cho agency để R8; tạo **AA-1034** (R0) và làm ngay.
- **~14:40–15:00:** frontend rời Vercel: **Dev trước**, CIS admin + Booking admin chung 1 task Spot, TripPlanner 1 task Spot +
  CloudFront + WAF, **~20–22 USD/tháng Dev**; prod tính sau. OpenNext + CloudFront flat-rate chỉ ghi làm lựa chọn sau.
- **~15:05:** tạo 7 issue cho R2–R7 + AI notice; "cần đánh giá luôn toàn bộ plan và các issue" → workflow đánh giá.
- **~15:25:** duyệt hết 52 kết luận + 3 câu hỏi (dựng aa-prod muộn nhất tuần 3 của pilot; SES có; AA-741 trả phí ≤ 20 USD).
  Ghi nhớ: mỗi phiên, danh sách việc phải giải thích từng issue bằng lời thường để Nghiệp hiểu rồi duyệt (memory).
- **15:45:** "Dừng phiên, nháp jira gom qua phiên tiếp theo".

## Kết quả theo issue

Done: **AA-1020, AA-896, AA-1023, AA-1025, AA-1034**; gộp (Duplicate): AA-1005 → AA-1038, AA-1007 → AA-1036, AA-1010 →
AA-1035; huỷ: AA-628, AA-864. Tạo mới: **AA-1034 … AA-1041**.

| Issue | Trạng thái | Kết quả | PR / bằng chứng |
|---|---|---|---|
| AA-1020 Tài liệu kiến trúc | **Done** | 13 mục audit S262 xong; trang hệ sinh thái + ai-gateway theo CIS 325–346; `/admin/docs` live (AA-Ecosys@34c6822f) | root #472, TP #214; `docs/audits/2026-11-03-S265-aa1020-verify/` |
| AA-896 Báo cáo chi phí tháng 10 | **Done** | 482,77 USD **mức dùng** (+171,6 %), ~246,70 USD **thực trả** (acc3 01–28/10 do bên trả tiền cũ trả); anomaly monitor live; `collect_month` REFRESH sửa | root #471, #473; `docs/audits/2026-11-03-S265-capacity-review/` |
| AA-1023 Game day + đổi env | **Done** | Env `prod` → `dev` (expand/contract), 7 workflow xanh trên `dev`, trust chỉ còn `environment:dev`, secret env prod xoá | Infra #620, #621, #622; root #475 |
| AA-1025 Ngân sách, app profile, capacity | **Done-with-scope** | H1b live (TP AI tắt → keyword + refused 0 USD), H1c live (CRM `app_disabled` 0 USD), H2 drill $0 (chờ 60 s không lỗi); chuông chi tiêu TP chờ có chi tiêu thật | CIS #1269/#1270/#1267/#1268, TP #217, Partner #202/#203, root #476/#477 |
| AA-1034 R0 B2B-only | **Done** | ADR 0019 Accepted; TP 410 `b2b_only`; bk-036 INSERT 42501; `bk_inquiry_pull` tắt; Overview hết thẻ B2C; backlog/plan mới | root #486/#487/#488/#490; TP #218; Booking #170/#171; CIS #1271 |
| AA-1027 TP + CRM trên lõi chung | In Review | E4 + E5 live (TP chỉ đọc view, CIS 350/351 REVOKE, tp-024 drop đã kiểm); F3 live (Draft 1 lần 0,0001 USD; chữ phí Partner #201); **F4 đổi sang đường tạm** (acc2/OpenAI ~0,001 USD) | TP #215/#216, CIS #1264/#1265, Infra #618, Partner #201, root #474 |
| AA-1024 Lõi CIS | In Progress | **D2 live** (job lifecycle 20 dòng, 0 NULL, acc2+acc3 42 model; IAM apply local); A8 chuyển sang R1 (AA-1028); còn **D8 mig 336 ≥10/11 ~12:00Z** | CIS #1266 (mig 352), Infra #619 |
| AA-1028 | Todo → R1 | Đổi phạm vi thành control plane tenant (S266–S268) | comment Linear |
| AA-1035…AA-1041 | Backlog | R2 vai trò, R3 một app agency, R4 Booking B2B, R5 TripPlanner đa tenant, R6 admin IA + Writing Lab, AI notice (hạn 02/12), R7 UX | Linear |

Ngoài issue: tư vấn tái tổ chức (16 agent) + giải đáp (9 agent) + đánh giá plan (7 agent) + áp dụng (5 agent);
trả lời và đối chiếu hợp đồng Sunny Cloud / eCloudvalley cho Nghiệp (không vào repo).

## Còn mở và vì sao

- **Mig 336 (AA-1024 D8):** guard 30 ngày, áp được từ **10/11 ~12:00Z**; tới lúc đó `DB_AUTO_APPLY_CONTRACT=false`.
- **AA-1027 F4:** chạy 1 bản nháp CRM thật trên đường tạm acc2/OpenAI (~0,001 USD) cần một "đồng ý" riêng; xong thì đóng.
- **Chuông chi tiêu TripPlanner (AA-1025):** chờ ngày TripPlanner có chi tiêu thật.
- **AA-1021 (details private):** vẫn chờ tech lead duyệt.
- **IDS / eCloudvalley:** chờ hai bên trả lời bằng văn bản (giấy phép bán lại Claude/OpenAI cho khách VN theo Billing Transfer).
- **Jira:** chưa soạn, gom sang S266 (yêu cầu của Nghiệp).

## Chi phí phiên

Cost Explorer ~0,07 USD (refresh tháng 10 + 3 lượt đọc + 1 lượt acc2 tháng 11); F3 Draft 0,0001 USD (Guardrail); kiểm
H1b/H1c/H2/D2/R0 0 USD. Tổng < 0,10 USD.

## Trạng thái kiểm cuối phiên (15:40 +07)

- ECS: cis-api :983 + worker :549 `dev-2f2883ab` (cùng SHA); booking :94 `dd223181`; crm-api :122 + web :94 `3dd029e3`;
  crm-portal :34 `0b02c03c`. Mỗi family chạy đúng revision mới nhất, rollout COMPLETED 1/1.
- Health 200: CIS 0.18.0 schema **352**; Booking 0.14.0 **bk-036**; CRM 0.11.0 **crm-041**; TripPlanner web `537b0fd5`;
  3 Lambda TP cùng CodeSha256 `iHRrpd5N…`. Migration TripPlanner mới nhất **tp-024**.
- Vercel Production: CIS admin `66e1c5cb`, Booking admin `dd223181`, TripPlanner `537b0fd5`.
- Bảng job: `shared.job` 0, wave 0; `crm.job` không chờ; `booking.job` B2C tắt.
- Infra: `DB_AUTO_APPLY=true`, `DB_AUTO_APPLY_CONTRACT=false`; env GitHub `dev`.
- Heads: root (PR chốt phiên), CIS `66e1c5cb`, Partner `3dd029e3`, Booking `dd223181`, TripPlanner `537b0fd5`, Infra
  `e23e74f6`. PR còn mở: chỉ bot/dependabot/release-please.
- Cố ý để BẬT: hop OpenAI cho 6 stage viết tenant (mig 344); `ai_assist` cho đại lý thử; cờ B2C tắt theo ADR 0019.
- PR merge trong ngày 03/11 (UTC): **53** (root 21, Infra 14, CIS 8, TripPlanner 5, Partner 3, Booking 2).

## Việc cần làm đầu phiên sau (S266), theo thứ tự

1. **Jira:** soạn gộp nháp (tái tổ chức B2B-only + trang quyết định cho chị Thư phần BO, chi phí tháng 10, cổng AI, R0) →
   Nghiệp duyệt → đăng.
2. **R1 (AA-1028):** control plane tenant ở CIS `shared` (bản ghi gốc, gói/add-on, entitlement, `tenant.entitlements.v1`,
   job pull CRM/Booking, `data_region`, guard pilot), S266–S268.
3. **AA-1027 F4** trên đường tạm (xin "đồng ý" ~0,001 USD) → đóng AA-1027.
4. Lane song song R6 phần gom AI & spend; P0 của prod (AA-1004).
5. **≥10/11 ~12:00Z:** áp mig 336, bật lại `DB_AUTO_APPLY_CONTRACT` → đóng AA-1024.
6. Danh sách việc phiên phải kèm 1–3 dòng giải thích bằng lời thường cho mỗi issue (memory `explain-each-issue`).

## Bài học (đã vào `skill/aa-lessons/lessons.md`)

- Migration mới có FK tới bảng mà test 304 drop → `LATER` + `_undo` (lần 4; đề xuất guard tự quét).
- Lane không tự chừa số migration; điều phối giao số trong `migStart` cho mọi owner.
- PR migration mở trước khi số trước lên main phải rebase rồi mới gate.
- Hai Terraform plan cùng lúc tranh state lock (lặp; đề xuất `concurrency` / `-lock-timeout`).
- Tài khoản đổi bên trả tiền: Cost Explorer chỉ thấy phần từ ngày đổi → báo cáo ghi riêng "mức dùng" và "thực trả".
