# S262 (31/10–01/11/2026): cổng AI v2 hoàn chỉnh (S0–S8, registry v2, độ tin cậy), CRM W5/W7 xong, AA-997 đóng, video review CRM, 17 issue Done

Tác nhân: **Claude Code (Ultracode)** (VSCode/WSL; lane code trong worktree → reviewer độc lập → vòng sửa; điều phối
merge/deploy/live). 31/10 ~18:40 +07 → 01/11 ~11:10 +07 (31/10 11:40Z → 01/11 ~04:10Z). Số liệu cuối phiên:
`docs/audits/2026-11-01-S262-close/state-snapshot.md` (kiểm 03:55–04:07Z; chỗ không kiểm ghi "chưa kiểm").
Nguồn diễn biến: checklist sống `.tmp-session/S262-checklist.md`, các thư mục `docs/audits/2026-10-31-S262-*/` và
`docs/audits/2026-11-01-S262-*/`, Linear (đọc lại cuối phiên), git log 6 repo.

Môi trường trong phiên: chạm hạn mức 5 giờ **hai lần** → đổi tài khoản claude.ai (lần 1 sang `info@adventure.asia`,
lần 2 sang `nghieppham`), lane resume bằng `resumeFromRunId`; MFA làm mới 20:45 (31/10) và 07:34 (01/11), hết hạn
khoảng 07:31 → 07:34 chặn audit AA-997 / cửa sổ AA-1019 vài phút. Lưu ý: các mốc giờ checklist ghi "21:45 → 23:45"
thực tế nằm trong 20:30–21:36 +07 (đã ghi chú trong checklist); mốc chuẩn xem log GitHub (Z).

## Quyết định của Nghiệp (tech lead)

- **Mở phiên:** chọn 20 việc, trọng tâm **dọn In Progress + dựng cổng AI (LLM gateway) cho hoàn chỉnh**; "việc nào cần
  tôi thì duyệt cho làm luôn theo kế hoạch"; chạy liên tục, không hỏi.
- **~19:25 — luật TL** cho các mục TL-1…TL-25 của review kiến trúc S261: *"cái nào không tốn tiền thì duyệt làm luôn
  và kỹ thuật không quá phức tạp; còn cái nào tốn thêm tiền và phức tạp thì không duyệt, ghi note tính sau"* → bảng
  phân loại `docs/audits/2026-10-31-S262-tl-decisions/README.md`. Làm trong phiên: TL-1 (ADR 0018 Accepted, giữ
  us-west-1), TL-3 một phần (≤ 8 In Progress), TL-4, TL-10 (phần luật), TL-11 (đóng băng track Writing memory + eval →
  AA-922 rút khỏi phiên), TL-13, TL-15 (AI Use Register v0), TL-24 (TP Dev `noindex`), TL-25 (AA-997). Để sau: TL-2,
  TL-3 phần còn lại, TL-5, TL-8, TL-12, TL-14, TL-16…TL-19.
- **"làm tiếp đi còn nhiều ram" / "còn nhiều ram thì đẩy tốc độ"** → thêm lane song song (tối đa 6 lane cùng lúc).
- **"dùng gpt api diễn tập gọi nhỏ"** → diễn tập OpenAI API qua cổng (AA-1018).
- **"cứ làm bình thường … khi nào hết tôi switch acc"** → không tự giới hạn theo hạn mức Claude (memory
  `no-throttle-for-usage`).
- **23:06 "ok" → duyệt Infra #568** (2 alarm break-glass CRM, ~0,20 USD/tháng) → merge + Terraform Apply.
- **00:38 "Ok" → duyệt Infra #575** (2 alarm Module 8 ops release ~0,20 USD/tháng + `BOOKING_ADMIN_URL`) → merge + apply.
- **Cửa sổ tắt auto mode** (Nghiệp tắt, agent gom bước): (1) gắn nhãn `secret-scan-baseline-reviewed` cho root #399;
  (2) 21:09 Terraform Apply Infra cho #553 (`TP_DAILY_SPEND_CAP_USD`); (3) Terraform Apply cho #574 (`LLM_DAILY_PROBE`);
  (4) 08:41 AA-1019: ghi 2 key staff vào secret web CRM → Terraform Apply #577 → tạo user Cognito WORKFORCE
  `e2e-crm-staff` (crm-ops + crm-support).
- **09:00 — nháp Jira (7 đích) KHÔNG đăng ở S262, gom sang S263.**
- **10:22 — yêu cầu mới:** kiểm tài liệu kiến trúc AWS (hệ sinh thái + từng app) và mô hình cổng AI đã cập nhật chưa;
  thêm AA-1021 (content series, details private) → trình plan trước.
- **10:56 — duyệt plan kiến trúc** (`docs/audits/2026-11-01-S262-arch-video-plan/`): TP theo luật dev-phase. **Duyệt tạo
  issue AA-1020** ([Docs] refresh kiến trúc, High, slot S263, lane docs song song CRM W6) và **AA-1021** (content
  series, details private).
- **11:06 — câu hỏi:** việc trong bản đánh giá S261 đã thành issue chưa; `plan.json` ↔ Linear tự động hay tay → trả lời:
  **tay** (tracker README: mirror; N24 chưa làm); workflow đối chiếu N1–N25 / G1–G17 / trigger + thiết kế sync đang chạy
  lúc ghi log.

## Kết quả theo issue

Cả 17 issue dưới đây **Done** trên Linear (đọc lại cuối phiên; đều đã archive qua export 04:04Z).

| Issue | Kết quả | PR / bằng chứng |
|---|---|---|
| AA-964 CRM-33a AI gateway + nháp + guardrail | **Done-with-scope**: crm-032 ledger v2, provider Bedrock Converse, trần theo đại lý, cảnh báo ngân sách, Settings > AI; live stub draft 200 + `llm_call_id`. Còn: model thật (khi có LLM + duyệt chi), Guardrails (báo giá), dòng ADR 0008a | Partner #152, #153; Infra #558; `S262-evidence/AA-964/` |
| AA-1013 Booking đọc lại đề xuất sau rewrite CIS | **Done-with-scope**: báo "CIS đã cập nhật" ở mục cũ, tên mục B2B, preview 390 px không tràn; live F1/F3 PASS, F2 ca cũ PASS (13 ảnh) | Booking #163; `S262-evidence/AA-1013/` |
| AA-971 CRM-13b hỗ trợ AA L2 + break-glass L3 | **Done-with-scope**: crm-033, phía đại lý cấp 1 ngày → banner + thẻ → thu hồi; UI nhân viên S-04 + user E2E chuyển sang AA-1019 | Partner #156, #157; Infra #568 (alarm), #570; `S262-evidence/AA-971/` |
| AA-1015 TripPlanner giới hạn AI + bot check | **Done-with-scope**: burst 35 search/1 phút → 30×200 + 5×429 `rate_limited`; BotID Basic → curl/headless 403 `bot_check_failed`, Chromium headed 200; narration nội dung AA trả trước cache/budget/limit; tp-023 | TP #198, #199, #200, #201; Infra #553, #556 |
| AA-1017 Registry v2 | **Done**: mig 320–322 + code; Q0 LLM-only route hash `d13dd30e…` không đổi; thêm model = 1 PR chứng minh bằng mig 324 (5 model ứng viên acc2 probe OK, chưa route) | CIS #1202, #1203, #1204, #1209; Infra #563, #564, #565, #571, #573 |
| AA-804 ADR 0009 + ledger v2 + UI Providers/Calls + AI Use Register | **Done-with-scope**: mig 319 + writer/reader v2; trang AI providers (Providers, Routing, Models & trials, Budgets, Calls, AI & data spend); ảnh 36 + 43 + 18 PNG (F1–F10, C4, N1–N4 PASS). Còn: đối soát hoá đơn ≤ 5 % (≥ 01/12) | CIS #1195, #1199, #1200, #1201, #1205, #1208, #1211; Infra #559; root #401, #404; `S262-evidence/AA-804*/` |
| AA-642 gateway lát còn lại | **Done-with-scope**: S0 bước 0 + 1 (sửa 0 USD), S7 phần sổ ghi, S8 lõi `aa_llm` dùng chung cho TP + CRM (TP ghi `app=tripplanner`, mig 323), S11 test chuẩn bị; S7 batch hoãn theo TL-13 | CIS #1196, #1197, #1206, #1207; TP #202, #203; Partner #155, #158; root #409; Infra #552, #569; `docs/audits/2026-10-31-S262-ai-gateway-step0/` |
| AA-1018 Độ tin cậy cổng AI | **Done-with-scope**: circuit theo connection, chuông `llm_circuit_open`, re-queue `llm_access_denied`, failure-domain report, deadline route, lớp `truncated`, probe hằng ngày (Infra #574, BẬT); diễn tập OpenAI API qua cổng; trần ngân sách connection chặn live (0 USD). Trigger còn lại: khoá Anthropic | CIS #1198, #1210; Infra #574 |
| AA-1016 Ngân sách AI theo tenant | **Done-with-scope**: live lệnh T-stage của tenant tổng hợp dừng chờ duyệt (0 USD), chuông `spend_budget_alert`; dòng ngân sách tạm đã xoá | CIS #1202 (mig 321), #1208, #1210 |
| AA-952 CRM-23 hoá đơn + thanh toán | **Done-with-scope**: link hết hạn 410 `pay_link_expired` ×2 (đại lý thấy re-quote), tiền đến muộn (reaccept → cọc → reheld → paid), nhắc nợ + task `invoice_overdue` live 18:12Z | Partner (S261) + dữ liệu tổng hợp; `S262-evidence/AA-952/`, ảnh 10/10b/21/22b |
| AA-956 CRM-26 Module 8 ops release | **Done-with-scope**: crm-034, release/refresh/T-21/withdraw/purge, board S-02 qua ECS exec (không lộ tên, watermark), API đại lý 200 + 404 ngẫu nhiên, noauth 401; alarm T-21 bắn thật; sửa lỗi duyệt chỉ 500 đại lý đầu | Partner #160, #162; Infra #575, #576; `S262-evidence/AA-956/` |
| AA-954 CRM-24b PWA ngoại tuyến | **Done**: `sw.js`/manifest/icon OK, CDP installability `[]`, SW active scope `/c/t`; E2E bước 6b offline PASS | Partner #161, #163 (sửa test E2E); `S262-evidence/AA-954/` |
| AA-1009 UAT dry-run harness | **Done**: 27 kịch bản (fast mode, đăng nhập theo danh tính); dry run live 19 PASS + 4 sửa selector → 23/23 PASS chỉ đọc; quay TP-02 headed EN + VI PASS 4/4, $0 | root #415, #416; `docs/audits/2026-10-31-S262-uat-dry-run/` |
| AA-997 geocode | **Done-with-scope (TL-25)**: chuỗi `aa997.4` (dc260ef8 400 + 3625eac5 400 + b1e780e8 224 = 1.024 dòng, 0 lỗi, xong 00:30Z, 0 USD); gate flag-strat 79,6 % FAIL như dự kiến, SERVED 88,0 % ±4,5 (phủ 50,8 %); `hide_flagged` report f54cdf77 → confirm 4919a61f (ẩn 2.517 dòng, 1.187 gắn tour); trả 3 dòng regressed về điểm cũ; báo cáo §7.2 điền | CIS #1213; `docs/audits/2026-10-31-S261-aa997-report/` |
| AA-957 CRM-27 hoa hồng + huỷ chuyến | **Done**: crm-035; 3 vòng kiểm live (hoa hồng A1–A4, huỷ có phí Booking 75 % / 50 %, void hoá đơn + dòng Balance, hoàn cọc, ops release rút trip_cancelled, trợ lý 403) + 3 vòng sửa UI/chức năng | Partner #165, #166, #167, #168, #169, #170; Infra #578; root #420; `S262-evidence/AA-957*/` |
| AA-1019 (mới) staff sign-in CRM web + S-02/S-04 + user E2E | **Done**: đăng nhập staff thật, revoke → 403 `support_session_ended`, break-glass mail + alarm OK→ALARM→OK, tách cookie, chặn cross-site; release live 74c05c77 → view 0→1, manifest có watermark | Partner #164, #171; Infra #577; root #419 (ADR 0006a A10c) |
| AA-1014 video review CRM | **Done**: longform `CRM-REVIEW_20261101_v1` (19:53, 21 chương, 2 tiếng EN/VI + phụ đề mềm) + highlight 8:30; Drive `01 Video/UAT (kiểm thử nghiệm thu)/dry-run/CRM-review-20261101/` 20 file, rclone check 0 khác biệt; $0 | root #422, #423; Partner #172 (lỗi tải CSV khi token hết hạn); `docs/audits/2026-11-01-S262-crm-review-video/` |

Việc khác trong phiên (không đóng issue):

- **AA-900** (In Progress): phần không trả phí xong (prompt register, CI gate, Experiments); còn nhãn 40 mẫu + chạy thử
  trả phí (Nghiệp).
- **AA-820** (In Progress): danh sách nhà cung cấp + nháp điều khoản xong (Partner #151); còn luật sư + báo tenant (chị
  Thư, qua Jira).
- **AA-896** (In Progress): báo cáo chi phí **SƠ BỘ** tháng 10 — tổng ~471,70 USD (AWS acc2 202,85 + AI 268,85), +165 % so
  với tháng 9 → `docs/audits/2026-11-01-S262-capacity-review/` (cũng là rà soát dung lượng tháng C8). Bản chính thức
  ≥ 03/11. Infra #562 (anomaly monitor theo App, tắt tới khi nonprod vào org), root #407.
- **Vệ sinh CI/ops:** root Secret Scan xanh lại (#399, 2 báo nhầm ghim); Infra DB Freshness Probe 111 → 0 (CIS #1194
  ghi `needs_draft`, relink 12 tour 0 USD, Infra #551); `crm.lumiguides.it.com` 000 = host không tồn tại, CRM web đúng là
  `portal.lumiguides.it.com` (sửa skill `aa-session`).
- **Audit kiến trúc** (yêu cầu 10:22): tài liệu kiến trúc **chưa** cập nhật (ecosystem-architecture, sơ đồ, gateway chưa
  có trang as-built, CONTEXT 4 app + Infra) → AA-1020.

## Issue chuyển / tạo

- **In Progress → Backlog** (vẫn mở, có trigger trong comment Linear): **AA-873** (còn GuardDuty — hoãn theo quyết định
  chi phí, mở lại trước prod/tenant trả tiền; chi phí tháng đầu đọc ≥ 01/12), **AA-1004** (còn mời acc3 — TL giữ độc lập,
  mời acc2 sau 01/12, test SCP, đường AI, ADR 0018 phần TL), **AA-922** (track đóng băng TL-11).
- **Tạo mới:** AA-1019 (Done trong phiên), **AA-1020** [Docs] refresh kiến trúc (Backlog, High, slot S263), **AA-1021**
  (content series, details private; Backlog, S264+).
- In Progress cuối phiên: **3** — AA-896, AA-820, AA-900 (trần TL-3 ≤ 8).

## PR theo repo (merge trong phiên, từ 31/10 ~11:40Z)

- **Root (master, head 4a4f32c3):** #399 (gitleaks ghim báo nhầm), #400 (retention tp-023), #401 (ADR 0018 Accepted, AI
  Use Register v0, tracker due/risks, quyết định TL), #403 (crm.ops.v1 1.6), #404, #407 (báo cáo chi phí tháng), #408
  (retention 320/321), #409 (llm-core-sync), #415, #416 (UAT harness), #419 (ADR 0006a A10c), #420 (retention
  crm.trip_cancellation), #422, #423 (video CRM); bot schema-ref #402, #405, #406, #410–#414, #417, #418, #421.
- **AA-CIS-App (main, head 0982cbd9):** #1194, #1195, #1196 (mig 318), #1197, #1198, #1199, #1200 (mig 319), #1201,
  #1202 (mig 320/321), #1203 (mig 322), #1204, #1205, #1206, #1207 (mig 323), #1208, #1209 (mig 324), #1210, #1211, #1213.
- **AA-Booking (main, head 16fbed68):** #162 (kit-sync), #163 (AA-1013).
- **AA-TripPlanner-Web (main, head c845b623):** #198, #199 (tp-023), #200 (noindex), #201 (BotID), #202 (core sync), #203.
- **AA-Partner (main, head d395b7ac):** #151, #152 (crm-032), #153, #154, #155, #156 (crm-033), #157, #158, #160
  (crm-034), #161, #162, #163, #164, #165 (crm-035), #166, #167, #168, #169, #170, #171, #172.
- **AA-CIS-Infra (main, head 1370c7b5):** #551, #552, #553, #554, #556, #558, #559, #562, #563, #564, #565, #568, #569,
  #570, #571, #573, #574, #575, #576, #577, #578 (đóng không merge: #555, #557 trùng bot).
- DB Migrate: CIS 318 → 324, tp-023, crm-032 → crm-035 (check + apply xanh từng chuỗi MIG-4).
- Terraform Apply (workflow Infra): #553, #568, #574, #575, #577.

## Trạng thái live cuối phiên (từ snapshot 03:55–04:07Z)

- ECS (đều COMPLETED, 1/1, revision mới nhất = đang chạy ở cả 6 family, không còn revision mẫu treo):
  cis-api :956 + cis-worker :522 cùng `dev-0982cbd9`; booking-api :91 `16fbed68`; crm-api :107 `f2f72e92`; crm-web :81
  `d395b7ac` (có `STAFF_*`); crm-portal :25 `7e452205`.
- Endpoint: tất cả 200 — CIS v0.18.0 schema **324** (required 322); Booking v0.14.0 **bk-035**; CRM api v0.11.0
  **crm-035**; CRM web `staff_auth_configured=true`; TripPlanner web `4fd7dcab`, browse 200, search không BotID → 403
  `bot_check_failed`. Lambda TP browse/assembly/jobs cùng CodeSha256 (31/10 16:30Z, TP c845b623). tp-023 theo dòng Verified.
- Vercel Production: CIS admin `67668f85` (#1213 chỉ backend), Booking admin `16fbed68`, TripPlanner `4fd7dcab`
  (#202/#203 chỉ backend); portal chạy ECS `aa-crm-dev-portal` (không còn project Vercel).
- Bảng job: snapshot (subagent) **chưa kiểm**; điều phối kiểm 11:04 +07 qua ECS exec: `shared.job` idle, `booking.job`
  idle, `crm.job` 2 queued (job định kỳ). Không có wave mở; alarm job CRM OK.
- CI nhánh mặc định 6 repo xanh (chỉ Dependabot Updates của CIS/TP đỏ). Soát xoá file: 3 commit có xoá, đều cố ý.
- PR còn mở: root #374 (bot infra docs), #328 (AA-993 M5, cũ); CIS #1212 (dependabot), #1179 (release); Booking #164
  (kit-sync), #161 (release); TP #196 (release); Partner #159 (kit-sync), #133 (release); Infra 0.
- Cố ý để BẬT: `LLM_DAILY_PROBE=on` (CIS api + worker); `hide_flagged` đã confirm; CRM staff console + user
  `e2e-crm-staff`; TP BotID Basic + `TP_DAILY_SPEND_CAP_USD=5.0`; 22 alarm `aa-crm-dev-*` OK (4 mới); 5 model ứng viên
  acc2 đã probe, **chưa route**; lượt dữ liệu video `rv202610317` giữ lại.
- LLM sinh văn bản: acc3 vẫn bị chặn (Error 002, chuông `llm_circuit_open`); khoá Anthropic chưa có.

## Chi phí phiên

| Khoản | Chi phí | Nguồn |
|---|---|---|
| Probe 5 model ứng viên acc2 qua cổng (nova-lite, nova-2-lite, llama4-maverick, llama4-scout, kimi-k3) | ≈ 0,0016 USD | checklist 00:20 |
| Diễn tập OpenAI API qua cổng (Test 0,000015 + 2 lượt judge 0,000013/lượt có sổ + 2 lượt không vào sổ < 0,001) | < 0,01 USD | checklist 22:10 (AA-1018) |
| Mọi việc còn lại: relink 12 tour, chuỗi geocode AA-997, test anthropic-direct (refused), trần connection, ngân sách tenant, video CRM + UAT (TTS local), báo cáo FinOps (dữ liệu đã lưu) | 0 USD | checklist |
| Search TP (Cohere embed acc2) trong burst kiểm giới hạn | không đáng kể, chưa cộng từ `llm_call_log` | checklist 21:25, 23:40 |

Tổng LLM/API trả phí trong phiên **< 0,02 USD**. Chi phí định kỳ mới duyệt: 4 alarm (~0,40 USD/tháng, #568 + #575), probe
hằng ngày (~0,05–0,20 USD/tháng, trong mức duyệt S261). Bản nháp place-card trả phí (~0,17 USD) không chạy (acc3 chặn).

## Jira — chưa đăng, dời S263

Theo quyết định Nghiệp 09:00 +07: **không đăng gì trong S262**. Nháp 7 đích (PR-26 A + B, PR-25, PR-24, PR-23 kèm câu
hỏi điều khoản AI/AA-820, PR-20 kỳ 3 — chỉ đăng từ thứ Hai 02/11, PR-22 định vị) ở
`docs/audits/2026-11-01-S262-close/jira-drafts.md` (gồm cả nháp S261 chuyển sang). Ảnh đã cắt/che ở
`.tmp-session/S262/jira-img/` (không đưa vào repo public) — **giữ thư mục này cho S263**. PR-27 không soạn (việc kỹ thuật
của tech lead).

## Việc cần làm đầu phiên sau (S263)

1. **Jira:** đưa 7 nháp cho Nghiệp duyệt một lần → đăng (ảnh từ `.tmp-session/S262/jira-img/`; PR-20 từ 02/11) → ghi
   link comment vào `jira-drafts.md`. Bổ sung link Drive video CRM (đã kiểm) vào PR-26/PR-20 nếu Nghiệp đồng ý.
2. **AA-896:** báo cáo chi phí tháng 10 **chính thức** từ 03/11 (Cost Explorer chốt số), thay bản sơ bộ.
3. **AA-820:** hạn **11/11** (điều khoản hiệu lực 12/11) — luật sư + báo tenant thuộc chị Thư, qua Jira PR-23.
4. **AA-1020** refresh tài liệu kiến trúc (slot S263, lane docs song song) — cần `aws sso login --sso-session aa-mgmt-sso`
   (profile `aa-mgmt`) để đọc tài khoản quản lý.
5. **CRM W6:** AA-959, AA-960.
6. **Theo dõi đường LLM:** case acc3 (Error 002) và khoá Anthropic — có lại thì làm TL-12 (thứ tự + trần lượt trả phí);
   kiểm kết quả probe hằng ngày đầu tiên (≥ 05:00Z 01/11).
7. **Giữ `.tmp-session/S262/jira-img/`** tới khi Jira đăng xong.

Kèm theo: C4.3 tuần W45 (từ 02/11); quyết PR bot còn mở (Booking #164 / Partner #159 kit-sync, root #374, #328 cũ);
kết quả workflow đối chiếu việc review S261 ↔ issue + thiết kế sync `plan.json` ↔ Linear (câu hỏi 11:06); dọn worktree
(72) + nhánh lane đã merge + 12 script S3 từ 31/10 nếu bước chốt phiên chưa làm.

## Bài học (đã vào `skill/aa-lessons/lessons.md`, 14 dòng)

- **Vận hành:** `pgrep -f`/`pkill -f` khớp chính shell đang chờ (dùng PID); PR code xếp chồng trên PR migration-only phải
  `rebase --onto` ngay sau khi migration merge; `ecsx` "no readable ECSX_CHUNK line" → `--resume` trước khi chạy lại;
  migration tạo bảng mới cần dòng retention DM-7.1 ở root trước khi bot copy; lane AA-Partner chạy unit suite + cổng
  coverage 90 % như CI; script ECS exec viết nhanh cũng phải tra db-schema-reference (`shared.job.attempt`).
- **Pipeline:** script adhoc gọi API trả phí ghi sổ bằng helper có sẵn, chạy thử với stub trước.
- **Dữ liệu:** vòng lặp xuyên đại lý phải phân trang, không cắt `[:500]`; test integration CIS chạm `geo.*` phải apply
  lại 255 + 319 trong fixture.
- **Frontend:** BotID Basic chặn Playwright headless (chạy headed); E2E dọn dữ liệu sau hành động có job nền là race;
  không merge repo khi E2E Dev của repo đó đang chạy (deployment skew); bộ đếm lượt video không để trong state local của
  worktree; panel dùng lại nhãn access log phải có tân ngữ.
- Skill `aa-session`: CRM web + api health trên host `portal.` (không phải `crm.`). Skill zip đóng gói: aa-lessons,
  aa-session, aa-ship, aa-uat-video.
