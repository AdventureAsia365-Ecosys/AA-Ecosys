# S266 (03–04/11/2026): R1 control plane tenant (3 lát), điều khoản AI, dấu AI máy đọc được, admin IA + gate chủ đề AA, CRM nháp thật, prod P0/P1

Tác nhân: **Claude Code (Ultracode)** (VSCode/WSL; lane code trong worktree qua `tools/workflows/lane.js` → 2–3 reviewer độc
lập → lượt sửa; với lane migration/quyền thêm **vòng review đối kháng** trên lượt sửa trước khi merge; điều phối
merge/deploy/DB Migrate/Terraform/kiểm live).
03/11 ~16:25 → 04/11 ~08:30 +07 (03/11 09:25Z → 04/11 01:30Z), có quãng dừng ~00:00–06:12 +07 do lỗi Claude Code.
Số liệu cuối phiên lấy từ snapshot `docs/audits/2026-11-03-S266-close/state-snapshot.md` (04/11 ~01:20Z).
Nguồn diễn biến: checklist sống `.tmp-session/S266-checklist.md`, tab "Phiên" của tracker, Linear, `gh pr list` 6 repo.

Môi trường: MFA hết hạn 1 lần (~20:10, Nghiệp nhập lại); **3 cửa sổ tắt auto mode** (Terraform Apply #632/#633 + thử
Deploy Prod; Apply route `/tenant/v1` #635; Apply IAM #646 + moved P1 #643). Lỗi Claude Code "Unable to read managed policy
settings (allowedProviders)" ~6 giờ đêm 03→04/11 làm chết agent sửa lượt 2 của l9 và chặn tin nhắn của Nghiệp lúc 6:11.

## Quyết định của Nghiệp (tech lead)

- **~16:40:** "ok làm hết" — duyệt 5 việc (AA-1028 lát 1, AA-1027 F4 kèm đồng ý ~0,001 USD, AA-1003 R0, AA-820, AA-1004 P0).
- **~17:30:** hỏi bán/kết nối TripPlanner vào CRM từng tenant, tenant tự làm UI → giải thích + artifact; hỏi bản đồ chỉ hiện
  tour đã viết lại hay tất cả → đề xuất tập "tour hiển thị" riêng, mặc định mọi tour AA còn live ở nước được phép (chốt ở R5).
- **~17:50:** "Ok aa1004p0" → bảo vệ env `prod` của Infra (reviewer = tech lead, chỉ `main`).
- **~18:05, ~19:35, 04/11 ~06:40:** "đã tắt" auto mode → 3 lần Terraform Apply.
- **~19:40:** site WordPress test để sau, "chưa quan trọng và gấp".
- **~20:50:** "Làm thêm issue luôn đi, còn nháp jira để sau" → mở thêm l9–l12.
- **04/11 ~06:40:** "Nháp Jira gộp tiếp sang phiên sau".

## Kết quả theo issue

Done: **AA-1027**. Đạt mốc phiên (issue còn mở): AA-1028 (lát 1–3), AA-1003 (R0, về Backlog), AA-820 (phần 1), AA-1004 (P0 +
P1 lát 2), AA-1039 (lát 1–2), AA-1040 (gần xong). Không tạo issue mới.

| Issue | Trạng thái | Kết quả | PR / bằng chứng |
|---|---|---|---|
| AA-1027 TP + CRM lõi chung | **Done** | F4 đường tạm: route CRM `crm_draft_reply` sang Nova Lite acc2 (crm-042), env + IAM CRM; 1 bản nháp thật ok 0,000034 USD, dòng ledger đủ trường | Partner #205, Infra #632, root #494 (ADR 0009 d14 Dev); `docs/audits/2026-11-03-S266-live-verify/f4-draft/` |
| AA-1028 R1 control plane | In Progress | **Lát 1:** CIS 353–355 (gói, subscription, entitlement, event, cột tài khoản) + `/tenant/v1` (account 200, ETag 304, feed, 403 thiếu scope). **Lát 2:** CIS 356–357, saga `tenant_provision`, `crm_entitlement_pull` (crm-043), `bk_tenant_pull` (bk-037) với adoption guard (Sen Vàng không bị đụng). **Lát 3:** CIS 361, Plans & add-ons, Tenant 360 Subscription + override, trial tick, bỏ `PLAN_LIMITS`, ngân sách AI fail-closed **chứng minh live** (24 lượt nova-lite 0,0101 USD rồi `refused/budget`) | root #498/#504/#512, CIS #1275/#1276/#1278/#1279/#1284/#1285, CRM #208/#209, Booking #174/#175, Infra #635 |
| AA-1003 Báo cáo | Backlog | R0: TP-03 retired, KPI B2C "historical"; 5/5 báo cáo chạy live 0 đỏ; R5–R7 sau S280 | root #493, CIS #1272, Booking #172, TP #220 |
| AA-820 Điều khoản AI | In Progress | Phần 1: AI Schedule v1.0, terms portal/CRM/TP, câu thư pilot, dàn ý DPA; live trên portal và TP | root #492, Partner #204, TP #219 |
| AA-1004 Prod nhẹ | Backlog | P0: stack Booking vào `modules/environment`, Deploy Prod skeleton (tự từ chối), DB Migrate prod có khoá, env `prod` có reviewer; P1 lát 2: 70 resource CRM vào module; plan 0/0/0 | Infra #633, #643; Apply 41619369750, 41740813689 |
| AA-1039 R6 Admin | In Progress | Lát 1: admin 7 nhóm + redirect 307. Lát 2: gate chủ đề AA (live PASS 409 `content_needs_change`), fan-out ngừng bán (360, IAM ListUsers); retire→restore chưa kiểm live (chưa có bài E2E đang đăng) | CIS #1277/#1282/#1283, root #503/#510, Infra #646 |
| AA-1040 Dấu AI (hạn 02/12) | In Progress | AiNotice biến thể narration + badge; dấu máy đọc được ở export/WordPress/tenant JSON/trang tour TP/JSON browse (catalog.http.v1 1.3)/supply Booking (CIS 358–359); còn 1 lần publish WP test | CIS #1273/#1274/#1280/#1281, Partner #206/#207, TP #221/#222/#223, Booking #173/#176, root #495/#507/#508 |

Ngoài issue: artifact giải thích TripPlanner cho tenant (bán, nối CRM, 4 mức UI, add-on vào Content, tập tour hiển thị)
`docs/audits/2026-11-03-S266-tripplanner-tenant-addons/` (<https://claude.ai/artifact/HYrjWyt2tSqNoNpAyy5Pn8>).

## Review đối kháng (điểm mới của phiên)

Ba lane rủi ro (l8 lát 2, l11 AA-1039 lát 2, l9 lát 3) đều qua lượt sửa của lane rồi mới chạy thêm vòng "tìm lỗi → agent
khác cố bác". Cả ba lần vòng này bắt thêm lỗi thật mà reviewer đầu bỏ sót: l8 1 blocking (lần pull đầu treo partner Booking
của đại lý không có tenant CIS) + 3 major; l11 6 major (mail khôi phục gửi nhầm, gate lách được, mất sự kiện khi code trước
migration…); l9 7 + 1 major (các đường làm ngân sách AI mở toang). Không lỗi nào bị bác. Đã thành bài học.

## Còn mở và vì sao

- **AA-1028:** ảnh tạo/gán gói trong admin + 403 CRM live (chưa có tài khoản CRM thuộc tenant CIS); 6 follow-up nhỏ.
- **AA-1039:** kiểm retire→restore live cần một bài E2E đang đăng (site WordPress test hết hạn); Writing Lab, gom Spend.
- **AA-1040:** 1 lần publish lên site WordPress test mới (Nghiệp tạo khi rảnh, không gấp).
- **AA-1024 D8:** mig 336 từ 10/11 ~12:00Z, rồi bật lại `DB_AUTO_APPLY_CONTRACT`.
- **Jira:** nháp gộp S265 + S266 chuyển sang S267 (yêu cầu của Nghiệp).
- Follow-up: studio-viewer thấy nút Edit/Export trong drawer bài → kiểm chặn ở API trong R2 (AA-1035).

## Chi phí phiên

F4 1 bản nháp ~0,0001 USD (Guardrail + Nova Lite 0,000034); fail-closed 0,0101 USD (24 lượt nova-lite acc2); kiểm báo cáo,
gate, IAM, pull 0 USD. Tổng ≈ 0,011 USD.

## Trạng thái kiểm cuối phiên (04/11 ~08:20 +07)

- ECS (mỗi family chạy đúng revision mới nhất, COMPLETED 1/1): cis-api :993 + worker :559 `dev-68a5b9d0` (cùng SHA);
  booking :96 `a8d98a1e`; crm-api :126 + web :98 `d433581e`; crm-portal :37 `66367c11`.
- Health 200: CIS 0.18.0 schema **361**; Booking 0.14.0 **bk-037**; CRM 0.11.0 **crm-043** (`entitlement_feed: ok`);
  TripPlanner web `ad1fcec3`; 3 Lambda TP cùng CodeSha256 `0Oq1G2Xy…`. TripPlanner migration **tp-024**.
- Bảng job: `shared.job` 0, wave 0; `booking.job` 0; `crm.job` chỉ job định kỳ.
- Infra: `DB_AUTO_APPLY=true`, `DB_AUTO_APPLY_CONTRACT=false`; env GitHub `prod` có reviewer + chỉ `main`.
- Heads: root (PR chốt phiên), CIS `68a5b9d0`, Partner `d433581e`, Booking `a8d98a1e`, TripPlanner `ad1fcec3`, Infra
  `86e3b6da`. PR còn mở: chỉ dependabot/release-please.
- Cố ý để BẬT: CRM gọi model thật (Nova Lite); các job pull + `tenant_account_tick` + fan-out/digest; ngân sách AI tenant
  chặn theo gói; hop OpenAI 6 stage tenant; `ai_assist` Sen Vàng; cờ B2C tắt.
- PR merge trong phiên (từ 03/11 09:25Z): **68** (root 21, Infra 17, CIS 14, Partner 6, Booking 5, TripPlanner 5).

## Việc cần làm đầu phiên sau (S267), theo thứ tự

1. **Jira:** soạn gộp nháp S265 + S266 (B2B-only, quyết định BO, chi phí tháng 10, cổng AI, R0, R1, điều khoản AI — luật sư
   là quyết định của chị Thư, dấu AI) → Nghiệp duyệt một lần → đăng.
2. **AA-1028:** gắn `crm.core` cho Atlas & Hearth qua saga + user CRM E2E → 403 live; ảnh tạo/gán gói; đóng issue.
3. **AA-1035 R2** (vai trò staff + scope; đã hết chặn nhờ R1) — rủi ro auth → review đối kháng; kèm kiểm Edit/Export của studio-viewer.
4. Lane song song: AA-1039 lát tiếp (Writing Lab / Spend), AA-1036 R3 bắt đầu, AA-1004 lát tiếp (TripPlanner/identity).
5. **≥10/11 ~12:00Z:** áp mig 336, bật lại `DB_AUTO_APPLY_CONTRACT` → đóng AA-1024. C4.3 W46 từ 09/11.

## Bài học (đã vào `skill/aa-lessons/lessons.md`)

- Lane migration/quyền nhiều repo: luôn chạy vòng review đối kháng trên lượt sửa trước khi merge.
- Job chiếu từ master mới phải có adoption guard (dòng chưa từng chiếu mà master chưa có thì để nguyên).
- Ngân sách AI theo entitlement phải fail closed trên mọi đường.
- Nhiều lane cùng owner migration: điều phối đánh lại số theo thứ tự merge thật.
- Migration expand sau một file đang chờ (336) cần `--dispatch-expand`.
- PR copy migration mở cùng lúc tranh state lock → chạy lại lần lượt.
- Nhánh code xếp chồng nhánh migration: rebase sau squash rồi force-with-lease.
- ecsx local mode đôi khi mất output; site WordPress test miễn phí hết hạn ~2 tuần; lỗi "managed policy settings" của Claude Code.
