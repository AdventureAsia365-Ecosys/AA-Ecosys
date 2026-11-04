# S267 (04/11/2026): R1 đóng, R2 vai trò staff, R3 bỏ API key tenant + gộp portal, R4 giá "from", route LLM theo họ model

Tác nhân: **Claude Code (Ultracode)** (VSCode/WSL; lane code trong worktree qua `tools/workflows/lane.js` → reviewer độc
lập → lượt sửa; lane quyền/migration thêm **vòng review đối kháng**; điều phối merge/deploy/DB Migrate/Terraform/kiểm live).
04/11 ~08:30 → ~20:40 +07 (01:30Z → 13:40Z).
Số liệu cuối phiên lấy từ snapshot `docs/audits/2026-11-04-S267-close/state-snapshot.md`.
Nguồn diễn biến: checklist sống `.tmp-session/S267-checklist.md`, tab "Phiên" của tracker, Linear, `gh pr list` 6 repo.

Môi trường: MFA hết hạn 1 lần (Nghiệp nhập lại); **4 cửa sổ tắt auto mode** (Terraform Apply, DB Migrate, gắn label
`secret-scan-baseline-reviewed`, bỏ required check "Portal Build" của AA-Partner); giới hạn dùng 5 giờ làm dừng workflow
2 lần (nối lại bằng `resumeFromRunId`).

## Quyết định của Nghiệp (tech lead)

- **~08:40:** "ok" danh sách việc; Ultracode bật. Sau đó: "còn RAM thì kéo việc về làm tiếp", nháp Jira + quy trình dừng chỉ
  khi Nghiệp nói dừng phiên; checklist cập nhật live lên tab "Phiên" của tracker.
- **acc3 Bedrock:** AWS gỡ chặn tài khoản; Nghiệp gửi lại case (qua Chat) xin bật Claude Sonnet/Haiku 5.5, GPT-6 Luna,
  GPT-5.6 Luna + quota. Kết luận của Nghiệp: trả thẳng AWS, xin model trực tiếp; đại lý chỉ để xuất hoá đơn; account nào
  dùng thì account đó xin.
- **Chính sách LLM (thay T-3):** "ưu tiên AWS, không chỉ AWS"; fallback **cùng model trước** rồi mới sang model khác
  (vd. acc3 Sonnet 5.5 → API Sonnet 5.5 → acc3 Haiku …); chấp nhận chi phí Claude 4.x; trần acc3 100 USD/tháng; **một key
  Anthropic** cho mọi việc, theo dõi chi phí theo sản phẩm trên hệ thống mình; giai đoạn Claude tài trợ → ưu tiên API
  Anthropic cho Claude, nhưng mọi thiết lập phải chỉnh được trên admin, không hard-code; chuỗi judge "GPT-5.6 Luna (acc3) →
  GPT-6 Luna (acc3) → GPT-6 Luna (API OpenAI) → Nova Lite (acc2)"; mỗi lần rơi xuống model sau phải log, trace và báo admin.
- **Tài liệu:** dựng artifact bản đồ route (bảng, sơ đồ, ma trận model, quy tắc, sổ key — tuyệt đối không in key); chốt
  xong thì đồng bộ docs admin + tab Guide trên trang AI gateway.
- **Case study công khai:** bài X/LinkedIn/Facebook + video ngắn + ảnh về kiến trúc LLM, chỉ kỹ thuật + domain, không lộ
  công ty/dữ liệu/tên người; dùng icon AWS chuẩn.
- **Thử dịch vụ AWS thay thế:** Amazon Location (so với Geoapify) và Drive → S3 — tạo issue, dữ liệu nhỏ, không ghi đè,
  đặt trần chi phí.
- **Issue mới:** "[AI gateway] Usage analytics explorer" (chị Thư muốn thống kê chi tiết có lọc/sắp xếp).

## Kết quả theo issue

Done: **AA-1028**, **AA-1043**, **AA-1044**. Issue mới: AA-1042, AA-1043, AA-1044, AA-1045.

| Issue | Trạng thái | Kết quả | PR / bằng chứng |
|---|---|---|---|
| AA-1028 R1 control plane | **Done** | Saga gắn `crm.core` cho Atlas & Hearth → CRM chiếu core/10 chỗ/`ai_assist`; gate `whatsapp_sms` 403 `feature_not_allowed` live; vòng tạo/gán/trả/retire gói thử; 11 ảnh | `docs/audits/2026-11-04-S267-live-verify/aa1028/` |
| AA-1035 R2 vai trò staff | In Progress | Lát 1 live: CIS 362–364 (vai trò, scope tenant, gán staff), Booking bk-038 (nhóm finance), Cognito groups; kiểm cô lập 200/403; vòng đối kháng 2 bắt thêm 6 major, sửa xong | CIS #1289/#1290, Booking #177/#178, Infra #651/#653, root #516 |
| AA-1036 R3 tenant | In Progress | Lát 1: studio gộp vào CRM web; cut-over; service portal cũ đã xoá (INACTIVE); lát 3: bỏ API key tenant (tenant-login 410), 4 secret E2E hẹn xoá 04/12; 368 (NULL hash) áp xong 04/11 (CIS #1297); 369 DROP chờ DRY RUN + duyệt | Partner #210–#213, Infra #650/#659/#662, CIS #1292/#1297, root #515/#525/#526 |
| AA-1039 R6 Admin | In Progress | Lát 3: Writing Lab API + UI, ô KPI Lab | CIS #1286/#1287/#1288 |
| AA-1029 R4 giá | In Progress | Chuỗi giá hợp đồng → view `booking.v_from_prices` → TripPlanner hiện "from 235 USD"; seed Dev | root #521, CIS #1291 (365), Booking #179/#180, Infra #660/#661, TP #224 |
| AA-1004 Prod nhẹ | Backlog | Lát 3: stack TripPlanner vào `modules/environment` (42 moved, apply 0/0/0) | Infra #649 |
| AA-1026 Bảng khả dụng model | In Progress | IAM acc3 cho 8 model ứng viên (Infra #663); CIS 367 model ứng viên (tắt) + trạng thái probe; sweep ứng viên + cảnh báo stage live (CIS #1295 áp 367, #1296 `76cd648a`); sweep ứng viên 0,0012 USD: Sonnet 4.5, Opus 4.5/4.6, Llama 4 Maverick, Kimi K3 trả lời; GPT-6 Sol/6.1 Sol/6.1 Terra bị từ chối | CIS #1295/#1296 |
| AA-1042 Route control center | In Progress | Route theo họ model + chuỗi fallback model-first (CIS #1293 code, #1294 migration 366 áp 04/11); ADR 0009 d5 S267 + AI Use Register v1.8 (root #527); artifact bản đồ route | `docs/audits/2026-11-04-S267-llm-routing/` |
| AA-1043 Amazon Location | **Done** | Giữ Geoapify: Amazon Location 0,32 USD, sai ở châu Á, 0/6 điểm Hàn Quốc | `docs/audits/2026-11-04-S267-geo-location-trial/` |
| AA-1044 Drive → S3 | **Done** | 3.232/3.232 ảnh đã có trong S3; đề xuất cut-over đọc thẳng S3 | `docs/audits/2026-11-04-S267-drive-to-s3-trial/` |
| AA-1045 Usage analytics explorer | Backlog | Tạo issue (lọc/sắp xếp theo provider, account, app, stage, thời gian, token) | — |

Artifact: bản đồ route model AI <https://claude.ai/artifact/AgTQX7AwiRYAPj2SSYGjsX>.

## Còn mở và vì sao

- **AA-1042:** phần chỉnh trên admin (thứ tự nhà cung cấp theo model, chế độ thứ tự là cài đặt DB, preset "Prefer Anthropic API
  for Claude", xem trước, hoàn tác), Route trace, cảnh báo rơi model, tab Guide + đồng bộ docs, tắt deployment `gpt-4.1` cũ.
- **AA-1036:** 369 DROP `api_key_hash` (DRY RUN + tech lead duyệt), kiểm người dùng mới được mời vào Content, studio tiếng Việt.
- **AA-1035 R2:** lát 2 (trang giao đối tác cho nhân viên, chế độ "xem như đối tác").
- **AA-1029:** portal marketplace đọc giá "from"; nhập bảng giá thật.
- **AA-1039:** retire→restore cần site WordPress test mới.
- **AA-1045** (Usage analytics explorer) Backlog; bài đăng X/LinkedIn/Facebook + video kiến trúc LLM (AA-1021, icon AWS chính thức,
  không lộ công ty/dữ liệu/tên người) chưa làm.
- **acc3:** Claude 5.x / GPT trên Bedrock vẫn chờ AWS mở (case đã gửi lại); key Anthropic chờ chị Thư gửi → cắm key + đặt
  limit 150 USD trong Console.
- **AA-1024 D8:** áp 336 từ 10/11 ~12:00Z (tắt luôn 2 route chết), bật lại `DB_AUTO_APPLY_CONTRACT`.

## Chi phí phiên

LLM ledger từ 01:30Z: 0,0041 USD (probe/sweep/test kết nối; 0 lượt pipeline trả phí). Amazon Location (AA-1043) 0,32 USD.
Drive → S3 (AA-1044) ~0,0003 USD request. Tổng ≈ **0,33 USD**.

## Trạng thái kiểm cuối phiên

Chi tiết: `docs/audits/2026-11-04-S267-close/state-snapshot.md` (04/11 ~13:00Z).

- ECS (mỗi family chạy đúng revision mới nhất, COMPLETED 1/1): cis-api :1000 + worker :566 `dev-76cd648a` (cùng SHA);
  booking :98 `3ef1434b`; crm-api :128 `90eef674`; crm-web :103 `6c36fc81`; crm-portal 0/0 (đã gỡ).
- Health 200: CIS 0.18.0 schema **368**; Booking **bk-039**; CRM **crm-043**; TripPlanner web `cf6faf9a`, 3 Lambda cùng
  CodeSha256 `dsDF/qUp…`; `tp-024`.
- Bảng job: `shared.job` 0, `booking.job` 0, `crm.job` chỉ job định kỳ. `DB_AUTO_APPLY=true`, `DB_AUTO_APPLY_CONTRACT=false`.
- LLM: 20 stage Sonnet 4.6/Haiku 4.5 @acc3, 14 stage GPT-6 Luna @openai-direct, 4 embed Cohere @acc2; coverage chỉ báo 2 route chết.
- PR merge trong phiên: **55** (root 14 trước PR chốt, Infra 18, CIS 12, Partner 4, Booking 4, TripPlanner 1). PR còn mở: chỉ
  dependabot/release-please.

## Jira

Đã đăng 04/11 ~20:30 sau khi tech lead duyệt và sửa (bỏ 2 câu ở PR-20, xưng "em", đoạn luật sư viết nhẹ lại, "dữ liệu mô
phỏng"): PR-20 #10608, PR-23 #10611 (A, 3 ảnh) + #10612 (B), PR-24 #10614 (1 ảnh), PR-25 #10610, PR-26 #10613 (3 ảnh), PR-22
#10615 (4 ảnh). Bản lưu + link: `docs/audits/2026-11-04-S267-close/jira-drafts.md`.

## Việc cần làm đầu phiên sau (S268), theo thứ tự

1. **AA-1042 admin controls** (provider order theo model, preset Anthropic-first, chế độ thứ tự trong DB, Route trace, cảnh báo rơi
   model, tab Guide + `docs/architecture/ai-gateway.md`), tắt `gpt-4.1`.
2. Cắm key Anthropic khi chị Thư gửi (runbook một lệnh) + limit 150 USD trong Console; theo dõi case AWS acc3.
3. AA-1036: DRY RUN 369 → tech lead duyệt → áp; kiểm user mới mời; studio tiếng Việt.
4. AA-1035 R2 lát 2; AA-1029 portal marketplace; AA-1045 Usage analytics explorer (thiết kế).
5. Case study công khai (AA-1021): bài X/LinkedIn/Facebook + video ngắn + ảnh về kiến trúc LLM (icon AWS chính thức, ẩn danh).
6. **≥ 10/11 ~12:00Z:** áp 336, bật lại `DB_AUTO_APPLY_CONTRACT` → đóng AA-1024. C4.3 W46 từ 09/11.

## Bài học (đã vào `skill/aa-lessons/lessons.md`)

- Test integration không dựa vào dòng seed của bảng dùng chung; mỗi file tự đặt repo root vào `sys.path`.
- Review đối kháng vòng 2 trên bản đã sửa vẫn bắt lỗi leo quyền mới → test ma trận role × route ghi.
- Key schema đòi riêng ngoài prefix phải được readiness, schema-gate và preflight cùng đọc.
- ecsx local mode mất output → ghi file + `--resume`.
- Auto mode chặn Terraform Apply/DB Migrate/label kể cả khi đã duyệt → gom một cửa sổ.
- Lane bị dừng giữa chừng: vòng sau kiểm cây git trước.
- Jira HTML: bảng trong gạch đầu dòng → 400; upload ảnh Jira timeout khi VPN bật.
