# S263 (01–02/11/2026): cổng AI — gia cố lõi + dự phòng acc2 (CIS 325–338), quy trình ship nhanh hơn, CRM WhatsApp/SMS + lời mời đại lý, thông báo AI, giảm cảnh báo

Tác nhân: **Claude Code (Ultracode)** (VSCode/WSL; lane code trong worktree → reviewer độc lập → vòng sửa; điều phối
merge/deploy/live). 01/11 ~11:43 +07 → 02/11 (01/11 04:43Z → ~20:00Z; nháp Jira soạn 02/11). Số liệu cuối phiên: mục
"Trạng thái kiểm cuối phiên" bên dưới (điều phối điền từ snapshot; chỗ không kiểm ghi "chưa kiểm").
Nguồn diễn biến: checklist sống `.tmp-session/S263-checklist.md`, `docs/audits/2026-11-01-S263-gateway-gap-audit/plan.md`
(59 gap / 22 câu hỏi T-1…T-22), `docs/audits/2026-11-01-S263-alerting-cost/`, `docs/audits/2026-11-01-S263-pricing-and-plans/`,
Linear (đọc lại cuối phiên, `list_issues` cập nhật trong 2 ngày), `gh pr list` 6 repo.

Môi trường trong phiên: đổi tài khoản claude.ai một lần (~14:30 +07); MFA hết hạn giữa chuỗi DB Migrate (19:20 +07),
Nghiệp nhập lại; một cửa sổ tắt auto mode (gắn nhãn `secret-scan-baseline-reviewed` cho CIS #1228 — sau đó đóng, gộp
commit #1225 thay cho ghim). RAM ~9 GB: tối đa 3 lane nặng, một `next build` mỗi lúc.

## Quyết định của Nghiệp (tech lead)

Chép nguyên từ checklist (giờ +07):

- **11:50:** duyệt danh sách 9 việc; plan.json ↔ Linear sync làm ngay nếu $0 (có: $0); ưu tiên hoàn thiện cổng AI;
  16 mục review S261 chưa có issue → chờ duyệt theo danh sách giải thích.
- **12:00:** "ok hết" 16 mục → tạo AA-1022 (P3 gia cố $0) + AA-1023 (P4 rollback game day $0); AA-873 thêm N17/G9;
  AA-820 thêm PDPL/Điều 20/3 câu luật sư; AA-1004 checklist trước prod (bỏ due 07/11); AA-900 sửa chữ; bảng trigger
  backlog + trang cho chị Thư (BO) làm ở chốt phiên. SSO aa-mgmt đã đăng nhập.
- **12:00:** LLM tạm thời → OpenAI API hoặc model acc2 qua cổng; khoá Anthropic: làm sẵn code, Nghiệp chỉ nhập key
  (agent lưu Secrets Manager) là dùng ngay.
- **~14:30 (sau đổi tài khoản):** T-1 làm sẵn, key sau; T-2 key OpenAI đã ở Secrets Manager — chỉ còn trần phía cổng;
  T-5/6/19 ok; T-8 tạm, nới, tránh tự chặn khi có traffic; T-9 5 USD Dev + cơ chế gói ở admin (tư vấn); T-11 TP qua cổng
  + AWS, test bằng model rẻ acc2; T-12 test bằng model rẻ acc2; T-15 ok; T-16 hỏi lại (không cần hằng ngày); T-17 ok;
  T-20 ok → AA-1024…1027.
- **Yêu cầu mới (cùng lúc):** thống kê chi phí thật SNS/alarm/SES acc2/acc3/acc4; cảnh báo bảo mật kèm mail "đã vào làm
  gì". Câu hỏi mới: làm giá tour (NCC → AA → đại lý/B2C) → `docs/audits/2026-11-01-S263-pricing-and-plans/`.
- **13:10:** T-3 writer ra API ngoài chỉ khi AWS chặn; T-4 đổi cấu hình 21 stage, test chỉ gọi được; T-10/13/14/15/16/9
  đồng ý; làm giá: xây sẵn → AA-1028 (gói), AA-1029 (chuỗi giá), AA-1030 (hạng đại lý); giảm chi phí cảnh báo: duyệt mọi
  đề xuất, "chỉ giữ cái thật cần" → lane alert-diet (mục tiêu ≤ ~6 USD/tháng).
- **13:15:** T-21 đồng ý (vào AA-1025), giảm tiền cảnh báo đồng ý (lane alert-diet).
- **14:20:** chuẩn bị báo cáo cho chị Thư (họp 02/11 14:00): theo từng app %, tính năng, trang, đã/còn; kiêm báo cáo kỳ 3;
  đánh giá nhà cung cấp AWS; trang artifact → **làm cuối phiên** ("cứ làm hết việc đi"); + runbook vào/chạy từng app →
  lane app-runbooks.
- **~19:00:** "thêm đường dự phòng acc2" → lane gw-acc2-fallback (judge/validate, mig 331, smoke vài cent); tenant stage
  (332): "1 làm luôn" (ghi đè ADR 0009 d14 cho các stage này; amendment ở root #440, kèm luật "AWS first, outside last").
- **AA-1033 (01/11):** duyệt thông báo nội dung AI trên mọi app (viết tiếng Anh).
- Nghiệp hỏi tối ưu cách chạy → agent đề xuất 8 cách (auto-apply contract trên Dev, gom migration theo đợt, lane tự chạy
  đủ CI, merge queue gộp, bớt PR xếp chồng, chia integration test, MFA/SSO 12h, luật auto mode) → thành **AA-1032**.
- **Thử tay CRM:** Nghiệp tự thử lời mời chủ đại lý (không cho agent chạy tự động); yêu cầu dọn tài khoản email mồ côi →
  lane crm-orphan-accounts.
- **16:30Z:** "quay về việc chính (cổng AI), dừng mở rộng CRM".
- **Jira:** 7 nháp S262 + việc S263 gom thành 8 nháp, đưa duyệt một lần cuối phiên (chưa đăng).

## Kết quả theo issue

Trạng thái đọc lại trên Linear cuối phiên (02/11). Done: **AA-1022, AA-958, AA-1031, AA-1032** (4).

| Issue | Trạng thái | Kết quả | PR / bằng chứng |
|---|---|---|---|
| AA-1022 Gia cố miễn phí (S3 gateway endpoint, NAT recover, ghim SHA action, OIDC ref, Dependabot) | **Done** | Terraform Apply 6 add / 4 change; S3 endpoint available, route vpce OK, alarm NAT recover OK, health 200, `sec_alert_check` 0 failed | Infra #579; CIS #1215; root #426 (SEC-01 đúng bộ kiểm soát live) |
| AA-958 CRM-28 WhatsApp + SMS (Twilio của đại lý) | **Done** | crm-036 (contract, apply tay DB Migrate 41291350052); crm-api :109 `0818573e`; live sandbox 7/7 PASS. Follow-up nhỏ: phụ đề Inbox, nút copy hook URL trên mobile | Partner #175, #179, #180; Infra #582; root #428; evidence `.tmp-session/S263/aa958-live/` |
| AA-1031 Trang Staff cấp vai trò CRM + mẫu "Platform owner" | **Done** | mig 330 (expand); tech lead tạo đại lý `test nghiep` bằng quyền mới; nhóm Cognito booking-admin / cis-admin / crm-platform-admin; audit `staff.roles_changed` preset. Follow-up: gợi ý trường ticket bắt buộc | CIS #1230; root #437 |
| AA-1032 Vòng ship nhanh hơn | **Done** | Dev tự áp migration contract khi mọi bảng job rảnh (ADR 0017a) — ca thật đầu tiên crm-039 tự áp (copy #600, `/crm/health/ready` = crm-039); CI Partner 6–10′ → 1–4′, CIS 4–5′ → ~4′ (Docker Build Check giờ dài nhất); ship tools `ship_merge` từ chối mọi check đỏ; DB Migrate có run-name; merge queue CIS/Partner/Booking 4 build / 5 merge / chờ 3′ | Infra #594, #595; root #441, #442; CIS #1236; Partner #184 |
| AA-1033 Thông báo nội dung AI trên mọi app + mục AI trong điều khoản | **In Review** | Kit `AiNotice` (staff / publisher / traveller); CIS admin reviewer, CRM draft + điều khoản, portal, TripPlanner (trang tour, planner, chân trang, `/terms` mục 3 "Use of AI"); kit sync 3 repo. Còn: ảnh live trên Vercel/prod + root #443 (token profile ADR 0016) | CIS #1235; Partner #185, #159; TP #210, #209; Booking #164; root #443 (mở) |
| AA-1024 Lõi CIS + chặn đường vòng | **In Progress** | Live: A1 (tắt `t9_write` → refused 0 USD, `prompt_version` v1), D1 (32 dòng `shared.prompt_version`), G1/G2 (guard 4 repo), A2 phần code (`model_tier` → 422), A4 (luật family judge, lý do tiếng Anh, PATCH 422), A6 (`warnings[]`, đã trả lại). A8 merged, chưa kiểm live. **A9 chưa đủ** (dòng embed ok thiếu `latency_ms`/`attempt_no`) → sửa trong #1245. A3/A5/D8/A2 stage rows: CIS #1244 (mig 334–338) merged; #1245 (gateway giữ retry, lọc theo served role) + #1246 (336 giữ `tp_extract` vì còn traffic 11/10) **đang mở**. Chưa làm: A10, D2 (cần IAM + MFA) | CIS #1214, #1219 (325), #1220 (326), #1221, #1222, #1223, #1243, #1244; Infra #583, #584, #601–#605 |
| AA-1025 Ngân sách, app profile, provider ngoài LLM, trang Providers | **In Progress** | Live: L2 (Batch 503, công tắc Jev/DFS/Geoapify, probe dry-run), B1 (Jev tắt → canary "nothing was sent", đã bật lại), B2 (probe embed + Geoapify, ~0,001 USD), C1 trang Providers (lỗi/độ trễ p50/p95 mỗi dòng, dòng CRM AI, Guardrails, Mapbox; ảnh 1440/390 sáng/tối, 0 lỗi console — ảnh giữ ngoài git vì có account ID). B4 merged, chưa kiểm bật/tắt live. Follow-up: ẩn nút Switch/Re-queue với vai trò chỉ đọc; cột cuối bị cắt 32 px ở 1440. Chưa làm: A7, B3, B5, D3, H1, H2 | CIS #1218, #1242 |
| AA-1026 Warm path + quản trị route | **In Review** | mig 327: bỏ key cũ `haiku`/`sonnet`, writer A-series → GPT trên OpenAI API cuối cùng (T-3), trần OpenAI 10 USD/tháng, báo 80 %, hard stop; smoke < 0,0001 USD. Dự phòng acc2: mig 331 (8 stage nền tảng), 332 (4 stage tenant), 333 (Nova Lite trước bước OpenAI trên 7 route judge); contract smoke live 11/12 rồi 19/20 (~0,0017 + ~0,0025 USD), parser đọc JSON đầu tiên (#1238), smoke đếm lỗi provider là failed (#1241). D7 live (đổi route judge phải có eval hoặc break-glass ≥ 20 ký tự + audit + chuông). Khoá Anthropic: lệnh một dòng cắm key (root #431). **Mở:** `a3_place_dedupe` chưa có bậc acc2 (Llama 4 từ chối forced tool choice; mig 337 thêm prompt mode → smoke Maverick trước) | CIS #1224 (327), #1232, #1233 (331), #1234 (332), #1238, #1239 (333), #1241, #1243; Infra #588, #596–#598; root #431, #440 |
| AA-1027 TripPlanner + CRM trên lõi chung | **In Progress** | E1 (reply `truncated` = lỗi, route deadline) + E2 (`prompt_version`/`prompt_hash`/`request_id` trên ledger TP + gate) merged, Lambda assembly/browse đổi CodeSha256 (06:05Z); kiểm degrade narration live chưa làm (cần guest token). F1/F2: crm-037 stage profile + kill switch, gateway CRM trên lõi chung (live). TP #208: search chỉ embed trong không gian embedding của cột được tìm. Chưa làm: E3–E5, F3 (UI nháp AI), F4 (trả phí, chờ LLM) | TP #206, #207, #208; Partner #176 (crm-037), #177; Infra #587 |
| AA-1020 Làm mới tài liệu kiến trúc | **In Progress** | 6 PR merged (trang AI gateway, sơ đồ, guide, AI Use Register v1, CONTEXT 5 repo + README tài khoản quản lý). Còn: kiểm `/admin/docs`, 2 dòng cấu hình agent (cổng portal trong `.claude/CLAUDE.md`, dòng role ledger trong steering — cần "có" của tech lead), chụp lại snapshot route | root #427; CIS #1217; Booking #166; TP #205; Partner #174; Infra #580 |
| AA-959 CRM-29a Module 10 engine + task | **In Progress** | crm-038 (DB Migrate 41301121077) + code (trang Tasks, Automations) merged; chưa kiểm live | Partner #182, #183; Infra #589 |
| AA-1006 Admin CIS lên kit | **In Progress** | `adminUi.tsx` xoá, suppression kit về 0; kiểm prod 10 trang 0 lỗi console/mạng; F1 tràn mobile Overview + F2–F4 sửa ở #1229; chưa chụp lại sau sửa | CIS #1226, #1229 |
| AA-873 Nền phát hiện tài khoản | **In Progress** | Mail tóm tắt phiên quản trị Identity Center (Lambda mỗi giờ: mỗi phiên admin đã làm gì) — apply 9 add + preview OK | Infra #581; root #429 |

Việc khác trong phiên (không đóng issue):

- **Giảm cảnh báo (alert diet, quyết định 13:10):** chi phí cảnh báo tháng 10 acc2 15,59 USD (acc3 / tài khoản quản lý
  0) → giữ alarm thật cần: Infra #586 apply (1 import, 11 add, 25 change, 99 destroy) → **27 alarm (27 OK), 0 dashboard**;
  kiểm trong app thay alarm CloudWatch: CIS #1227, Booking #167, Partner #181; root #434. Audit:
  `docs/audits/2026-11-01-S263-alerting-cost/`.
- **Lời mời / dọn tài khoản CRM:** lỗi Nghiệp thử tay (POST lần 2 ghi đè cookie claim → mất mật khẩu dùng một lần) sửa ở
  Partner #186 + CIS #1240 (AA rút lời mời, xoá đại lý thử) + root #444 (crm.ops.v1 1.8); lỗi 2 (RESEND dùng `sub` làm
  Username → 500) sửa ở Partner #187. **Nghiệp thử trọn vòng PASS** (mời lại → mật khẩu một lần → đổi mật khẩu → MFA →
  nhận lời mời → CRM Owner → đăng xuất → đăng nhập MFA). Dọn tài khoản chưa từng đăng nhập: crm-039 (tự áp), Partner #188,
  #189 (dry run `would_delete 1` → apply xoá 1 → list-users = 0), Infra #599 (IAM `AdminDeleteUser` trên partner pool),
  root #445 (ADR 0006b A1).
- **Embedding space registry (T-15):** mig 328/329 (Titan V2 dự phòng, tắt; job re-embed), #1231 sửa 329 sau khi #1225
  merge dù Migration preflight đỏ; runbook re-embed qua Infra run-script (root #433, #438; Infra #585). DB Migrate 328
  (41307750581) + 329 (41307898711).
- **Runbook từng app (GUIDE-12):** 7 trang EN + `.vi.md` (root #435, #436).
- **plan.json ↔ Linear:** `tools/linear/plan_sync.py` (root #425), chạy thật đầu phiên (2 issue mới, 21 trường đổi).
- **AA-1003:** FI-01 tháng 10 chạy tay 05:11Z succeeded (AWS 403,28 provisional, LLM 269,35, vendors 281,66 USD); báo cáo
  tuần 02/11 01:30Z chưa đọc.
- **Bảo mật:** kiểm 14 GetSecretValue break-glass 18–19/10 — đều từ phiên admin của Nghiệp. Phát hiện các phiên quản trị
  vào acc2 từ hệ thống của đại lý AWS trong 90 ngày (đã báo tech lead; chi tiết không ghi vào repo public).
- **Báo cáo cho chị Thư** (họp 02/11 14:00): artifact riêng tư v4 (% theo app: CIS 78, Content studio 80, TP 80, Booking
  78, CRM 84, Nền tảng 64; kỳ 3; chi phí theo tháng/thành phần/app; gói dịch vụ prod; đánh giá nhà cung cấp AWS; cần quyết;
  phân quyền; runbook). Link chỉ nằm trong nháp Jira PR-20, không ghi vào repo public.
- **Làm giá tour + gói (câu hỏi mới):** nghiên cứu as-built `docs/audits/2026-11-01-S263-pricing-and-plans/` → AA-1028,
  AA-1029, AA-1030 (Todo).
- **Điều khoản portal** nêu model dự phòng Bedrock (Nova, Llama) của bước kiểm tra/chấm điểm (Partner #190), khớp AI Use
  Register v1.1 (PR chốt phiên này).

## Issue tạo trong phiên

AA-1022 (Done), AA-1023 (Todo, S264), AA-1024, AA-1025, AA-1027 (In Progress), AA-1026 (In Review), AA-1028, AA-1029,
AA-1030 (Todo), AA-1031 (Done), AA-1032 (Done), AA-1033 (In Review). In Progress cuối phiên (Linear): AA-1024, AA-1025,
AA-1027, AA-1020, AA-959, AA-1006, AA-873, AA-896, AA-900, AA-820, AA-1021 (**11** — vượt trần TL-3 ≤ 8; phiên sau gom lại
trước khi mở việc mới).

## Còn mở và vì sao

- **Cổng AI (AA-1024/1025/1026/1027):** không issue nào đạt đủ Done-when. Việc lớn còn lại (cỡ L, phiên sau): A7 ngân sách
  tập trung, B3 circuit chung cho provider ngoài LLM, B5 sổ top-up, D3 hợp đồng ledger, H1 app profile, H2 capacity S12,
  A10 CIS lên `shared/aa_llm`, D2 model lifecycle (cần IAM + MFA), I4 drill failover hằng tháng, I7 harness qualification,
  I8 data scope d10, I9 invoker role riêng TP/CRM (apply có MFA), D6 đối soát hoá đơn (≥01/12), E3–E5 TP, F3 UI nháp AI CRM.
  PR mở: CIS #1245, #1246.
- **`a3_place_dedupe`:** chưa có bậc acc2 — chờ smoke Llama 4 Maverick ở prompt mode (mig 337) rồi migration sau.
- **AA-1033:** chờ ảnh live + root #443.
- **AA-959 / AA-960:** AA-959 chưa kiểm live; AA-960 chưa bắt đầu (dừng mở rộng CRM theo quyết định 16:30Z).
- **AA-896:** bản chính thức chờ Cost Explorer chốt (≥03/11). **AA-820:** luật sư + báo tenant (chị Thư, hạn 11/11).
  **AA-900:** nhãn 40 mẫu + lượt trả phí (chờ LLM).
- **Đường LLM:** acc3 vẫn Error 002 (probe 05:04Z: 16 đường, 6 sống — 5 model acc2 + `gpt-6-luna-openai`; 9 acc3
  `access_denied`); khoá Anthropic chưa có (code + lệnh cắm key làm sẵn).

## Chi phí phiên

| Khoản | Chi phí | Nguồn |
|---|---|---|
| Probe 16 đường (05:04Z) | 0 USD ghi sổ | checklist |
| Smoke sau mig 327 | < 0,0001 USD | checklist |
| Contract smoke acc2 lần 1 (11/12 pass) + lần 2 (19/20 pass) | ~0,0017 + ~0,0025 USD | checklist, AA-1026 |
| Probe B2 embed + Geoapify | ~0,001 USD | AA-1025 |
| Mọi việc còn lại (D7/A4/A6 kiểm live, dọn tài khoản, sandbox Twilio) | 0 USD | checklist |

Tổng LLM/API trả phí trong phiên **< 0,01 USD** (tổng `llm_call_log` của phiên: chưa kiểm). Chi phí định kỳ: giảm cảnh báo
(mục tiêu ≤ ~6 USD/tháng từ 15,59 USD), trần OpenAI 10 USD/tháng (mức tối đa, không phải chi tiêu).

## Jira: chờ duyệt (8 nháp)

8 nháp (PR-26 A/B/C, PR-25, PR-24, PR-23, PR-22, PR-20 kỳ 3) ở `.tmp-session/S263/jira-drafts.md` — **chưa đăng**, chờ
tech lead duyệt một lần. Gồm 7 nháp S262 chuyển sang. Không soạn PR-27 (việc kỹ thuật). Sau khi đăng: ghi link comment vào
bản public `jira-drafts.md` trong thư mục chốt phiên (không account ID, không link Drive riêng, không ảnh evidence-private).

## Trạng thái kiểm cuối phiên

_(Điều phối điền từ `state-snapshot.md` của phiên: STS; ECS task def + image SHA từng service; `/health` + `/health/ready`
mỗi app; migration mới nhất mỗi owner (CIS, `bk-`, `tp-`, `crm-`); Lambda TP CodeSha256; Vercel Production; bảng job;
PR còn mở; CI nhánh mặc định; cái gì cố ý để BẬT.)_

- ECS: _chưa điền_
- Endpoint + migration: _chưa điền_
- Vercel / Lambda: _chưa điền_
- Bảng job + wave: _chưa điền_
- PR còn mở + CI: _chưa điền_
- Cố ý để BẬT: _chưa điền_

## Việc cần làm đầu phiên sau (S264), theo thứ tự

1. **Jira:** 8 nháp → tech lead duyệt một lần → đăng; ghi link vào `jira-drafts.md`.
2. **Cổng AI — phần còn lại** (AA-1024/1025/1026/1027): A7, B3, B5, D3, H1, H2, A10, D2, I4, I7, I8, I9, D6 (D6 ≥01/12);
   merge CIS #1245 + #1246, kiểm A8, A9 live, B4 bật/tắt live.
3. **TripPlanner:** kiểm live E1–E2 (degrade narration, cần guest token) rồi E3–E5.
4. **CRM F3:** UI nháp AI trong trip workspace (`crm.ai_draft`, entitlement `ai_assist`).
5. **Caller `tp_extract`:** tìm ai còn gọi (2 dòng ngày 11/10) trước khi retire route (CIS #1246 giữ nó).
6. **`a3_place_dedupe`:** bậc acc2 sau smoke Llama 4 Maverick ở prompt mode (mig 337).
7. **Content studio:** trang hiện địa chỉ của phiên cũ (`info@…`) thay vì user CRM hiện tại; ẩn "Open Content studio" với
   đại lý không có tenant studio.
8. **Trang Providers:** ẩn/khoá nút Switch/Re-queue với vai trò chỉ đọc; độ rộng cột cuối ở 1440.
9. **AA-959:** kiểm live engine + Tasks/Automations. **AA-960** (tags, coverage, ready-to-travel).
10. **AA-1006:** phần còn lại (chụp lại sau #1229, rồi AA-1007).
11. **AA-1003:** đọc báo cáo tuần 02/11 01:30Z rồi đóng nếu đạt.
12. **AA-896:** báo cáo chi phí tháng 10 chính thức (≥03/11).
13. **C4.3 W45:** rà `pg_stat_statements` tuần (từ 02/11), một đoạn "C4.3 tuần W45" trong log phiên.

Kèm theo: gom In Progress về ≤ 8 (TL-3); AA-1033 ảnh live + root #443; AA-1020 phần còn lại (2 dòng cấu hình agent cần
"có" của tech lead, snapshot route); AA-1023 (game day rollback $0); 8 cách tối ưu ship đã vào AA-1032 — cache layer Docker
Build Check CIS là follow-up đề xuất.

## Bài học (đã vào `skill/aa-lessons/lessons.md`)

- **Vận hành:** lane chạm query provider chạy cả integration test của query; xác định expand/contract trước khi vào merge
  queue; merge queue chỉ chờ check bắt buộc (#1225 → 329 lỗi lên main); test integration đổi dữ liệu dùng chung phải trả
  lại; `gh run view --log-failed` có thể cắt đoạn cuối; Cognito RESEND dùng `Username`=email; số migration giữ chỗ cho lane
  song song phải về liên tiếp (gộp vào dòng apply-pending); zsh `set -- $x` (gộp vào dòng zsh); `pkill -f`/`pgrep -f`
  tự giết shell — lặp 2 lần ở S263, gộp **một** dòng (bỏ dòng trùng S262).
- **Pipeline:** contract smoke phải đếm lỗi provider là failed.
- **Job runner:** thêm job kind định kỳ → cập nhật test lịch production (`test_job_runner`).
- **Dữ liệu:** directive migration (chỉ `expand`, contract = không directive); `CREATE POLICY`/`TRIGGER` kèm `DROP … IF EXISTS`.
- **Frontend:** PR consumer kit mở sau khi Kit Sync vào main; route claim một lần không ghi đè cookie ở mỗi POST.
