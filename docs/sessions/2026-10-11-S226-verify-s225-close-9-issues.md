# S226 — Đồng bộ repo sau cloud session S225 + verify live đóng 9 issue (11/10/2026)

**Tác nhân:** Kiro (WSL/VSCode, có AWS/MFA qua `aa365-admin`)
**Bối cảnh:** S225 là cloud session (Claude Code, không WSL) — mọi thay đổi đẩy lên GitHub, chưa verify live. S226 đồng bộ về local rồi chạy danh sách verify WSL còn tồn.

## Đầu phiên — đồng bộ + nắm trạng thái
- 4 repo đều behind GitHub (ahead=0), fast-forward sạch: AA-Ecosys→`492c80f`, AA-CIS-App→`08e5654`, AA-TripPlanner-Web→`5738a2b`, AA-CIS-Infra→`3195a7a`. 0 PR mở.
- Trạng thái runtime KHỚP memory: ECS api:525/worker:80 cùng SHA `08e5654`; `shared.job` sạch (0 queued/running).
- Lệch phát hiện ngay: `db-schema-reference.md` còn mig 209 trong khi DB đã 218+tp-008.

## Quyết định của Nghiệp
- Làm luôn danh sách verify (không chờ duyệt từng cái); đánh giá toàn bộ In Progress/Backlog xem sao treo nhiều.
- **AA-727**: rerun đã khoá sổ → đóng Done với ghi chú "verified bằng integration test, không chờ wave Laos".
- **AA-677**: **ta tự build AAA Booking, anh Mạnh không còn liên quan** → tự chốt 6 câu nghiệp vụ (theo draft), bỏ "TO CONFIRM", huỷ việc gửi Jira chị Thư/Mạnh.
- **AA-656**: kiểm UI positive-path luôn (không để known-limit).
- **AA-731**: prune 240 orphan cho sạch, đúng logic.
- **AA-756**: làm **phần $0** (inventory + đọc 30 quyết định + báo cáo), KHÔNG recalibrate; audit đầy đủ để phiên riêng.
- Root docs-only: **merge thẳng**, không mở PR lắc nhắc rồi chờ duyệt.

## Kết quả — 9 issue Done (verify live đầy đủ)
- **AA-676**: send-to-advisor e2e trên `aa-tripplanner-dev-assembly` — 2 lần send → `already_sent` false/true, cùng handoff_id 103; `v_inquiry_outbox` đúng **1 dòng**, consent=true, leg chain đúng; payload **validate PASS** với `inquiry.submitted.v1.json`. Dọn data test (outbox về 0).
- **AA-750**: `lambda list-functions` còn 3 (dfs-balance-check + 2 tripplanner); 2 IAM role `lambda-exec`/`sfn-exec` → NoSuchEntity; 0 Step Functions. Invocations 90d: 5/7 = 0; ingestion=26/authorizer=10 là tàn dư trước ngày gỡ.
- **AA-727**: Done theo quyết định Nghiệp (integration test 2/2 real Postgres).
- **AA-677**: chốt 6 câu ERD + bỏ TO CONFIRM → root PR #45 (merged). Mở đường AA-678.
- **AA-656**: content/reviewer login JWT role đúng (backend); **Playwright trên prod** `aa-cis.lumiguides.it.com`: reviewer thật + forge `cis_role=admin` → `/admin/overview` và `/admin/tenants` đều bounce `/admin/review`; xoá 5 env content-login chết trên Vercel; viết lại `scripts/create_staff_user.py` (thiếu do gitignore) → App #651.
- **AA-684**: regenerate `db-schema-reference.md` (mig 215-218+tp-007/008, các object mới) → root PR #46; `schema_versions` có tp-001…tp-008.
- **AA-731**: op `orphans` (240 comp + 51 tour_day) → snapshot ra `s3://.../scripts/restore/s226_aa731_orphan_snapshot.json` → `prune include_components:true` xoá đúng → re-check orphans=0; op `components` đọc 86 atoms qua RLS (`v_active_tour_atoms`, grant mig 216); send idempotent (từ AA-676).
- **AA-726**: `publish_log` có `idempotency_key`/`status`/`requested_at` (mig 215), 0 dòng → không có `requested` treo. (Đã Done từ S225, xác nhận lại.)
- **AA-654**: README TripPlanner khớp env Lambda; sửa note "legacy SQS" lỗi thời (AA-750 gỡ SQS) + cờ `STEP_FUNCTIONS_ARN`/`SF_BATCH_THRESHOLD` còn thừa trên task def api → App #652; đối chiếu CLAUDE.md cũ/mới: quy tắc bền còn, SEO seed rule đã thành `seed_builder.py`.

## Dở dang
- **AA-756 (In Progress)**: $0 inventory → `docs/audits/2026-10-11-S226-jev-inventory.md` (root PR #47). 23 câu Jev, 274,961 quyết định/30d, **$9.68**; `a1_claim_supported` = 72% chi phí. **Phát hiện: tất cả 23 câu giờ là `shadow`** (kể cả a1_claim_supported) — không câu nào enforce; `decision_log.outcome` fill 0%. `a1_promise_unsupported` 100% grey, tv0 (chưa cho tín hiệu). Audit đầy đủ + recalibrate để phiên riêng.
- **AA-730 (In Progress)**: thêm profile `aa365-agent` vào `~/.aws/config`; role tồn tại nhưng **assume từ `user/nghiep-admin` → AccessDenied**. Trust = `:root`+MFA, nhưng trust kiểu `:root` còn đòi identity policy của caller cấp `sts:AssumeRole` lên ARN đó — user chưa có. **Cần 1 thay đổi Terraform (Nghiệp apply tay)**: thêm `sts:AssumeRole` cho `nghiep-admin`, HOẶC đổi trust principal sang ARN đích danh. Đã ghi cách sửa trong Linear.

## PR
- Root (merge thẳng): #45 (AA-677), #46 (AA-684 schema-ref), #47 (AA-756 inventory).
- AA-CIS-App (auto-merge, CI xanh): #651 (create_staff_user.py), #652 (README env note).

## Lệch đã xử trong phiên
- `scripts/create_staff_user.py` thiếu — `scripts/` bị gitignore, các script giữ lại phải `git add -f`.
- `db-schema-reference.md` lỗi thời (mig 209) → regenerate S226.
- 5 env content-login chết trên Vercel Production (CONTENT_PASSWORD, CONTENT2_PASSWORD, CONTENT2_USERNAME, CONTENT_DISPLAY_NAME, CONTENT_USERNAME) → xoá.
- README AA-CIS-App note "legacy SQS" lỗi thời → sửa.

## Bài học ghi vào `skill/aa-lessons/lessons.md`
- "Role đã apply" ≠ "role dùng được" — phải thử assume thật (trust `:root` còn đòi identity policy caller). (AA-730)
- Script/artifact tả trong implementation-note có thể chưa commit (thư mục gitignore) — `git ls-files` để chắc. (AA-656)

## Việc cần làm đầu phiên sau (S227)
1. **AA-730**: sau khi Nghiệp apply Terraform (thêm sts:AssumeRole / đổi trust), chạy test negative/positive của profile agent rồi đóng.
2. **AA-756** (phiên riêng, audit đầy đủ): xác nhận ý đồ enforce/shadow (vì sao tất cả thành shadow); chọn 2–3 câu giữ enforce; retire các câu ~100% grey (a3_atom_in_text, a1_keyword_about_tour, a3_keyword_belongs, T-series nhỏ); human-label ~100/câu; recalibrate + đo trên wave (~<$1 Jev); backfill `decision_log.outcome`.
3. Dọn các branch local cũ đã merge (nhiều branch tồn ở AA-TripPlanner-Web/AA-Ecosys/AA-CIS-Infra).

## Lưu ý kỹ thuật
- ECS exec execute-command hay timeout ~120s → chạy nền, đọc kết quả qua S3 (`scripts/out/*.json`).
- Profile `aa365-agent` assume hỏi MFA riêng, cache khác với `aa365-admin` role đã export; env Nghiệp export ở shell khác không sang shell của agent.
- Playwright CIS: `testDir=tests/e2e`, project `chromium` quét mọi file trừ `smoke/`; chạy UI test trên prod `aa-cis.lumiguides.it.com` (public, không cần bypass secret), `BASE_URL`+creds qua env.
