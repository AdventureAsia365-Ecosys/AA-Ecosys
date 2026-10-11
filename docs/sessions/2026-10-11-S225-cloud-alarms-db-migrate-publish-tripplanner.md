# S225 — Cảnh báo log-write-failed, workflow DB Migrate, publish idempotent (AA-726), TripPlanner harness (AA-731) (11/10/2026)

**Tác nhân:** Claude Code (cloud session — KHÔNG có AWS/MFA, KHÔNG local/WSL) · **ECS sau phiên:** `aa-cis-dev-api:522` / `worker:77` (cùng image `dev-eda8fc4`, rollout stable, smoke 5/5) · **Migration mới (đã áp Dev qua workflow):** 215, 216 · **Queue:** sạch (guard Deploy Dev cho qua)

## Trạng thái đầu phiên
Cloud container không có aws CLI, key trong env bị STS từ chối → không kiểm được STS/ECS/`shared.job` trực tiếp. `/health` 200; 4 repo trên main khớp S224 (App `d537930`); 0 PR mở.

## Quyết định của Nghiệp
- Chốt 10 issue làm được từ cloud; làm 1 → 2 → 3 (+ docs).
- **Migration làm qua repo Infra**: Nghiệp duyệt PR, Claude merge, trigger apply prod và theo dõi; **không đụng local/WSL**.
- AA-726: chưa cần publish WordPress thành công — chỉ note lại → **Done**.
- Việc chưa làm được từ cloud: note lại để kiểm từ local/WSL (mục cuối).

## Kết quả chính
- **AA-CIS-Infra #82** (merged `512f31f`):
  - AA-756: 4 metric filter + 4 alarm `*_log_write_failed` (llm_call_log, decision_log, llm_shadow_log, dfs_call_log) → SNS `aa-cis-dev-acp-alerts`. Terraform Apply Prod **8 added / 0 changed / 0 destroyed**.
  - **Workflow `DB Migrate`** (`.github/workflows/db-migrate.yml` + `db/run_migration.py` + `db/README.md`): chỉ chạy từ main, `check`/`apply`, one-off Fargate task từ task def api (cùng subnet/SG, `DATABASE_URL` của task), SQL qua presigned S3, kiểm sha256, fail nếu version không vào `shared.schema_versions`. Chạy thật lần đầu OK (`latest_registered=214`).
  - SQL `db/migrations/cis/215_*`, `216_*` (bản copy y hệt ở `AA-CIS-App/api/migrations/`).
- **AA-726 — Done.** App #646 (merged `eda8fc4`): `publish_log.idempotency_key` + `requested` + unique index (mig 215, áp 05:28Z); `requested` ghi trước khi gọi WordPress/Facebook; cùng revision đã đăng → replay; đang chạy → 409; thử lại sau mất response → tìm bài trên remote trước (WP theo slug revision, FB theo message). Unit 2552 passed, integration Postgres thật 6/6. Credential đã nằm sẵn Secrets Manager.
- **AA-731 — In Progress.** TripPlanner #65 (merged `beb1fed`, Deploy Lambdas xanh): Send-to-advisor idempotent (advisory lock + event `sent` cuối, không migration); narration grounding (số bịa → thay bằng tên component); extraction đọc `v_active_tour_atoms` (grant mig 216, áp 05:31Z); op `orphans`. 152 test pass.
- **AA-756** vẫn In Progress (phần alarm xong).
- **AA-727 — In Progress (chờ wave thật).**
  - App #647 (merged `4a844be`): `shared.rerun_wave` (mig 217, áp 06:10Z) + `/admin/waves`:
    - tạo wave (từ tour_ids hoặc một nước), danh sách, đóng wave;
    - báo cáo 4 cột + trạng thái từng tour + loại lỗi + Jev coverage + chi phí;
    - `/check`: wave thiếu → 1 chuông.
  - Infra #83: Lambda probe gọi `/check` hằng ngày.
  - Deploy Dev xanh; unit 2561 passed, integration 2/2.
  - Done-when: wave Laos phải tạo wave **trước** khi chạy, rồi so với đếm tay.
- **AA-684 — In Progress.**
  - Root #43: `docs/database/schema-ownership.md`, ADR 0001 quyết định 6, steering.
  - Infra #83: xoá `modules/rds/migrations` (9 file cũ); DB Migrate có prefix `tp-`/`bk-`.
  - TripPlanner #66: `tp-007` (áp 06:13Z) đăng ký `tp-001…006` theo đối tượng có thật.
  - Chờ Nghiệp xác nhận `shared.destinations` thuộc CIS.

- **AA-654 — In Progress (docs xong, Nghiệp duyệt + merge).** App #648 (`df89241`: README viết lại, `.claude/CLAUDE.md` 518 → ~90 dòng, bỏ LIVE STATE, CONTEXT thêm bảng contracts); TripPlanner #67 (`8366317`: README, CONTEXT contracts, sửa câu cũ "ghi shared.destinations"); Infra #84 (`a76844e`: README; plan **No changes**, không cần apply); root #43 (README gốc tiếng Anh, `ecosystem-architecture.md` + `tripplanner-to-aaa-handoff.md` dịch + cập nhật: worker, DB Migrate, schema ownership, AA-Booking acc2, alarm, waves; bàn giao theo ADR 0001 outbox, `inquiry.submitted` v1 có legs).

## Việc cần kiểm từ local/WSL (cloud không làm được)
1. **AA-726** — `SELECT status, count(*) FROM acp_shared.publish_log GROUP BY 1;` không có dòng `requested` treo > 2 phút. Khi có site WordPress thật (không anti-bot): publish 1 piece → 1 bài + dòng `published` có `idempotency_key`; publish lại → `replayed: true`, vẫn 1 bài.
2. **AA-731** — invoke `aa-tripplanner-dev-assembly` `{"extraction": {"op": "orphans"}}` → xem `orphan_components` (dọn bằng `prune {"include_components": true}` nếu > 0). Chạy `{"op": "components", "tour_ids": ["<1 tour>"]}` để chắc role `tripplanner` đọc được view `v_active_tour_atoms` qua RLS (lỗi permission/0 atom = báo lại). Gửi thử Send-to-advisor 2 lần trên preview → 1 email (LoggingSender) và 1 event `sent`.
3. **AA-756** — thử alarm: CloudWatch → alarm `aa-cis-dev-*-write-failed` ở trạng thái OK/INSUFFICIENT_DATA; xác nhận email SNS `aa-cis-dev-acp-alerts` đã confirm. Còn lại của issue: kiểm tay ~30 quyết định Jev sau ngưỡng v2; đọc số liệu `a1_promise_unsupported`.
4. **AA-684** — `SELECT version FROM shared.schema_versions WHERE version LIKE 'tp-%' ORDER BY 1;` → mong tp-001…tp-007; thiếu tp-00N = bước đó chưa từng chạy trên Dev.
5. **AA-727** — sau lần chạy probe hằng ngày đầu tiên: log Lambda `aa-cis-dev-dfs-balance-check` có `/admin/waves/check` 200.
6. **Schema reference** — regenerate `docs/architecture/db-schema-reference.md` (mig 215 cột mới `publish_log`, mig 217 bảng `shared.rerun_wave`).
7. **AA-654 (kiểm sâu)** — đối chiếu các README mới với thực tế: danh sách biến môi trường (App/TripPlanner) khớp task def ECS / Lambda config / Vercel; lệnh setup/test chạy được trên máy local. `.claude/CLAUDE.md` của App đã bỏ LIVE STATE — đọc lại bản cũ (git `df89241^`) xem có quy tắc còn hiệu lực nào bị rơi. Chốt chỗ đặt bảng outbox `inquiry.submitted` (đề xuất: schema `tripplanner`, AA-Booking đọc qua view — đang **[TO CONFIRM]** trong spec bàn giao). `docs/contracts/` chưa tạo.

## Lưu ý kỹ thuật
- Mỗi repo chỉ có 1 branch phiên → mỗi repo 1 PR một lúc; gộp nhiều việc Infra vào 1 PR để Nghiệp duyệt một lần.
- `gh` trong cloud: GraphQL bị chặn (dùng `gh api` REST); tải log run bị 403 → đọc log job qua MCP `get_job_logs`.
- Registry Terraform bị chặn trong container → `terraform validate` chỉ chạy ở CI plan.
