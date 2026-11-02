# S264 (02/11/2026): cổng AI phần còn lại (CIS 339–346), đại lý viết bài lại qua OpenAI, thanh bên gom nhóm 4 app, tab Thành viên đối tác, game day quay lui 5/5

Tác nhân: **Claude Code (Ultracode)** (VSCode/WSL; lane code trong worktree qua `tools/workflows/lane.js` → 2 reviewer độc
lập → vòng sửa; điều phối merge/deploy/DB Migrate/kiểm live). 02/11 ~07:05 +07 → ~21:45 +07 (00:05Z → ~14:45Z). Số liệu cuối
phiên lấy từ snapshot `docs/audits/2026-11-02-S264-close/state-snapshot.md` (21:10 +07).
Nguồn diễn biến: checklist sống `.tmp-session/S264-checklist.md`, tab "Phiên" của trang tracker, Linear (đọc lại cuối phiên),
`gh pr list` 6 repo, `docs/audits/2026-11-02-S264-live-verify/`.

Môi trường trong phiên: MFA hết hạn 2 lần (07:55 và giữa game day 12:32Z), Nghiệp nhập lại; **2 cửa sổ tắt auto mode**
(mời Nghiệp làm Owner "Lữ hành Sen Vàng" ~12:00; game day quay lui ~19:00); tạm dừng 13:00–18:10 +07 (Nghiệp họp chị Thư).
Lane chạy song song tối đa 3–4; L1–L15 đều xong, 0 lane đang chạy khi chốt.

## Quyết định của Nghiệp (tech lead)

Chép từ checklist (giờ +07):

- **07:15:** "Ok" — duyệt danh sách việc S264 như đề xuất.
- **07:55:** "Có" cho 2 sửa cấu hình agent (steering role ledger DM-10.4 v1.10; `.claude/CLAUDE.md` portal = ECS
  `aa-crm-dev-portal`) → root #448.
- **Giữa phiên:** cuối phiên cập nhật báo cáo kỳ 3 cho chị Thư nếu có thay đổi (đã làm, bản 5).
- **09:05:** hỏi tiến độ AA-1021 (content series, details private) → bắt đầu lane ngay.
- **09:40:** thanh bên các app: nhóm con phải thu gọn được → lane L9 (kit core `NavGroup`).
- **11:20:** thử luồng tenant → đại lý → Content studio, báo 5 điểm (link vào studio, đại lý không thấy studio, xoá rồi tạo
  lại báo trùng, cùng mail không cấp mật khẩu mới, không thấy social content) → điều tra + lane L10.
- **11:30:** góp ý cho AA-1021 (content series, details private) → đã sửa, chờ tech lead duyệt.
- **~12:00:** muốn vào một đại lý có sẵn để review cho chị Thư → tắt auto mode, mời Owner "Lữ hành Sen Vàng"; sau đó vào
  studio Atlas & Hearth (Sen Vàng không có tenant CIS) bằng một lệnh console, đã vào được.
- **~12:30:** đại lý không viết được bài → **chọn thêm OpenAI làm đường dự phòng cuối** cho 6 stage viết của tenant
  (lane L11, mig 344). Hỏi thêm về model acc2: chen Llama 4 Maverick trước OpenAI cần đổi luật thứ tự 327 / ADR 0009 d5 →
  để tech lead quyết sau khi so 3 bài mẫu.
- **13:00–18:10:** tạm dừng (họp chị Thư), rồi "tiếp tục"; "phiên này còn những gì, làm hết đi".
- **~18:45:** lưu checklist + theo dõi phiên thành tab trong trang tracker; sau đó "làm dạng thống kê, ít chữ" → root #462, #463.
- **Hợp đồng IDS Vietnam (Sunny Cloud):** đọc 3 file, soạn câu hỏi làm rõ (model Claude/GPT trên Bedrock, Marketplace/SCP,
  dịch vụ và bảo mật dữ liệu, điều khoản tạm ngưng / thay đổi đơn phương / gia nhập Org) — tech lead gửi; nội dung hợp đồng
  không vào repo.
- **~19:00:** "Đã tắt auto mode" → chạy game day quay lui (MFA 991465).
- **21:30:** "ok đăng" — duyệt 4 nháp Jira.

## Kết quả theo issue

Trạng thái đọc lại trên Linear cuối phiên. Done: **AA-1033, AA-1006, AA-959** (3, đã export + archive). In Progress 11 → **8**
(đúng trần TL-3).

| Issue | Trạng thái | Kết quả | PR / bằng chứng |
|---|---|---|---|
| AA-1033 Thông báo nội dung AI mọi app | **Done** | Ảnh live mọi chỗ đặt; lỗi F1 (CRM `/terms` bị rule ALB đưa sang studio) sửa bằng trang `/legal/terms` | Partner #192; root #443, #449 (live-verify §1, §5) |
| AA-1006 CIS admin lên kit | **Done** | F1–F4 của #1229 đạt; phát hiện F2 (Upload tràn ở 390) sửa #1250 | CIS #1250; live-verify §2, §5 |
| AA-959 CRM engine + Tasks | **Done** | Tasks + Automations đạt; engine trên đại lý thử: có ngày / chưa ngày / áp lại không trùng / huỷ chuyến → STOPPED | live-verify §3, §3b |
| AA-1024 Lõi CIS + chặn đường vòng | In Progress | A10 + A5 (CIS lên lõi `aa_llm` 1.1.0, served roles) live; **A8 chưa chứng minh** (trần 0 USD = không trần, numeric(10,2) không đặt < 0,01; Atlas chi 0 USD tháng này) → kiểm lại khi tenant có chi tiêu thật; D2 cần IAM + MFA; **D8 mig 336 chờ ≥10/11 ~12:00Z** | CIS #1261; core sync TP #212, Partner #199 |
| AA-1025 Ngân sách, app profile, provider ngoài LLM | In Review | A7 trần tập trung (mig 340, `llm/app:cis` 51,65 USD/ngày, chỉ cảnh báo) live PASS; B3 circuit Jev/DFS/Geoapify (mig 342) live PASS (chuông + mail, đóng sau 60 s); B5 sổ top-up + cảnh báo credit thấp (mig 343) live PASS; B4 cảnh báo số dư DFS live PASS; D3 federated ledger read + H1a app profile (mig 345/346) live, 4 app `ai_enabled=true` sau kiểm; Providers ẩn nút với vai chỉ xem. Còn: H1b/H1c/H2 | CIS #1248, #1249, #1252, #1253, #1255, #1262, #1263; root #452, #465 |
| AA-1026 Warm paths + route governance | In Review | Mig 339: `a3_place_dedupe` thêm bậc acc2 Llama 4 Maverick, smoke 779 ms 0,00021 USD; mig 344: 6 stage viết tenant = [Claude, gpt-6-luna-openai], live `t9_write` 11:33Z qua OpenAI. Còn D6 đối soát hoá đơn ≥01/12 | CIS #1249, #1259; Partner #198; root #458 |
| AA-1027 TripPlanner + CRM trên lõi chung | In Review | E3 live (dispatch theo deployment, breaker, `pricing.quote`; gỡ `tp_extract` / `tp_component_embed`); mig 341; F3 ô nháp AI CRM (crm-040) ship, chưa kiểm live (cần `ai_assist`). Còn E4, E5, F4 | TP #211; CIS #1251; Partner #194 |
| AA-1023 Game day quay lui $0 | In Review | Runbook ECS có tham số + helper `ecs_rollback.sh`, gate job rảnh trong terraform-apply; **D1–D5 đạt** (Booking, CRM, Vercel, Lambda TP, gate job). Helper báo "IN_PROGRESS" sai 2 lần → sửa (root #469). Còn: đổi tên `environment: prod` 3 workflow Infra (cần MFA) | root #464, #469; Infra #615; `docs/audits/2026-11-02-S264-rollback-game-day/` |
| AA-1020 Tài liệu kiến trúc | In Progress | Bảng route LLM chụp lại (40 route, 20 model) root #461; cấu hình agent root #448; tab tracker | root #448, #461, #462, #463 |
| AA-1007 Portal + CRM web lên kit | In Progress | Thanh bên gom nhóm cả 4 app (kit core `NavGroup` + `useNavGroups`, nhớ trạng thái, rail đủ icon); Members chỉ xem ẩn nút ghi | CIS #1254, #1260; Booking #168, #169; Partner #195, #196 |
| AA-1021 (content series, details private) | In Progress | Tiến độ ghi trong comment Linear; chờ tech lead duyệt | root #456, #459 |
| AA-1031 / tenant ↔ đại lý ↔ studio | (đã Done S263; việc tiếp theo L10) | Tab Thành viên Tenant 360, mời chủ đại lý kèm quyền studio, 409 `tenant_deleted` rõ ràng, picker ẩn tenant đã có đại lý, câu lỗi | CIS #1256, #1257, #1258; Partner #197; root #457 |
| AA-1003 Bộ báo cáo | Todo | Lượt tuần đầu 00:32Z: 11 báo cáo succeeded (FI-02 chi tuần 42,86 USD, −70,2 %; EX-01 LLM 35,23 USD; OPS-13 3/3); 26/63 báo cáo do engine sinh → chưa Done (R4–R7) | comment Linear |

Ngoài issue: Content studio hiện đúng người đăng nhập (`/bff/identity` luôn 200, Partner #191, #193); C4.3 W45 (dưới).

## Issue tạo trong phiên

Không có.

## Còn mở và vì sao

- **Mig 336 (AA-1024 D8):** guard 30 ngày, lượt `tp_extract` cuối 11/10 11:59Z → áp được từ **10/11 ~12:00Z**; tới lúc đó
  `DB_AUTO_APPLY_CONTRACT=false`.
- **A8 (AA-1024):** chưa có tenant chi tiêu thật để chứng minh chặn cứng.
- **D2 (AA-1024), đổi tên env 3 workflow Infra (AA-1023):** cần IAM + MFA.
- **F3 live (AA-1027):** cần cho phép `ai_assist` cho một đại lý thử ở CIS admin và bật AI.
- **AA-1021 (details private):** chờ tech lead duyệt; tài liệu riêng lên Drive trước khi dọn `.tmp-session`.
- **Chen Maverick trước OpenAI cho stage viết:** quyết định của tech lead (đổi luật 327 / ADR 0009 d5), đề xuất làm sau khi so 3 bài mẫu.
- **AWS batch inference acc3:** AWS từ chối (chưa đủ lịch sử dùng on-demand) → xin lại sau.
- **Hợp đồng IDS:** chờ IDS trả lời các câu hỏi tech lead gửi.

## Chi phí phiên

LLM < 0,01 USD: smoke Maverick 0,00021 USD, 2 lượt viết thử qua OpenAI (< 0,001 USD mỗi lượt), lượt A8 qua OpenAI < 0,001 USD.
Game day, kiểm live, C4.3: 0 USD.

## C4.3 tuần W45

Probe `aa838_capacity_probe.py` (DB Migrate run-script, 00:21Z; `docs/audits/2026-11-02-S264-c43-w45/`): 9.735 statement
(cộng dồn từ `stats_reset` 07/10); lock chờ 0, deadlock 0, bloat 0, transaction > 60 s 0, cache hit 99,14 %, kết nối 7/181.
C1.2: tenant reads p95 ~111 ms (< 150), job claim mean 1,1 ms (< 20), Booking p95 < 1 ms (< 100), admin cost aggregate mean
~217 ms (< 1 s); TripPlanner đọc địa điểm lượt mới mean ~82 ms. p95 ~4,9 s ở `catalog_views` là probe của Infra #494, không
phải traffic app. **Không mục tiêu nào trượt** → không có C1.2a.

## Jira: đã đăng (4 comment, 10 ảnh, 02/11 ~21:40)

PR-23 (#10604, 3 ảnh), PR-26 (#10605, 5 ảnh), PR-22 (#10606, 2 ảnh), PR-20 (#10607, link báo cáo kỳ 3 bản 5). Không soạn
PR-24, PR-25, PR-27. Bản lưu: `docs/audits/2026-11-02-S264-close/jira-drafts.md`.
Báo cáo kỳ 3 cho chị Thư cập nhật phần 02/11 sau buổi họp: https://claude.ai/artifact/5QtvFweK4LHaMwF3HfXDok (bản 5).

## Trạng thái kiểm cuối phiên (21:10 +07)

- ECS: cis-api :979 + worker :545 `dev-a08d7209` (cùng SHA); booking :93 `967f9b2c`; crm-api :120 `dca5465b`; crm-web :92
  `ba3eec91`; crm-portal :34 `0b02c03c`. Mỗi family chạy đúng revision mới nhất, rollout COMPLETED 1/1.
- Health 200: CIS 0.18.0 schema **346**; Booking 0.14.0 `bk-035`; CRM 0.11.0 `crm-040`; CRM web `ba3eec91`; TripPlanner
  web `8e59223a` (không file frontend nào đổi sau #210).
- Lambda TP browse / assembly cùng CodeSha256 `gFA2On…` (02/11 12:54Z / 12:21Z).
- Vercel Production: CIS admin `a08d7209`, Booking admin `1fceb3c4`, TripPlanner `8e59223a`.
- Bảng job: `shared.job` 0, wave mở 0; `booking.job` 0; `crm.job` 3 job định kỳ hẹn giờ.
- Infra: `DB_AUTO_APPLY=true`, `DB_AUTO_APPLY_CONTRACT=false`.
- Heads: root `0fb8309c` (+ PR chốt phiên), CIS `a08d7209`, Partner `dca5465b`, Booking `1fceb3c4`, TripPlanner `39e7e65b`,
  Infra `e4e45160`. PR còn mở: bot/dependabot/release-please (root #466; CIS #1237, #1212, #1179; Partner #133; Booking #161;
  TP #213, #196; Infra #613, #612).
- Cố ý để BẬT: hop cuối OpenAI cho 6 stage viết tenant (mig 344) tới khi acc3 hoặc key Anthropic có lại. Không có cờ wave.
- PR merge trong ngày 02/11 (UTC): 62 (root 23, CIS 16, Infra 10, Partner 9, Booking 2, TripPlanner 2), gồm PR bot.

## Việc cần làm đầu phiên sau (S265), theo thứ tự

1. **AA-1021 (details private):** tech lead duyệt → upload Drive → dọn thư mục tạm của phiên.
2. **Cổng AI phần còn lại:** AA-1025 H1b/H1c/H2; AA-1027 E4, E5 (DRY RUN), F3 live (bật `ai_assist` cho đại lý thử);
   AA-1024 D2 + AA-1023 đổi tên env (một cửa sổ MFA); A8 khi có tenant chi tiêu.
3. **≥10/11 ~12:00Z:** áp mig 336 (DB Migrate out-of-order), bật lại `DB_AUTO_APPLY_CONTRACT`.
4. **AA-896:** báo cáo chi phí tháng 10 chính thức (≥03/11); **AA-1003** R4–R7 (hạn bằng chứng 03/11).
5. **CRM:** AA-960 (tags, coverage, ready-to-travel), AA-963, AA-968.
6. **AA-1007:** phần còn lại (suppressions portal/web); Content studio hiện email của chính user (đổi auth ID token).
7. Đề xuất chen Maverick trước OpenAI cho stage viết: so 3 bài mẫu rồi đưa tech lead quyết.
8. Root #466 (bot infra docs): merge khi xanh.

## Bài học (đã vào `skill/aa-lessons/lessons.md`)

- Migration mới đổi CHECK/FK/grant của bảng mà test cũ chạy lại → thêm vào `LATER` + `_undo` của test cũ (lần 3, kèm lỗi thứ
  tự có sẵn 304 → 322).
- Route BFF chỉ để hiển thị trạng thái luôn trả 200 kèm `kind`.
- Kiểm AI TripPlanner qua API Gateway (BotID chặn Playwright).
- ECS exec mất output (lần 6): trả trạng thái trong `finally`, kiểm lại bằng exec riêng, đọc thì `python3 -u`.
- `pkill -f` tự giết shell (thêm 1 lần).
