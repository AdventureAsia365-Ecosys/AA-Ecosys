# S194 — 2026-09-23 — AA-623 (AWS Cost Explorer reconcile) + dọn Linear + cleanup dead route

**Tác nhân:** Kiro.

## Trạng thái

Session bắt đầu bằng review/dọn Linear (Command Center cleanup) rồi tập trung làm 2 issue độc lập
với việc rerun G4 (AA-599 chưa chạy, đợi Nghiệp): **AA-632** (slate cross-channel dedup, xong nhanh)
và **AA-623** (AWS Cost Explorer reconcile — phần lớn thời gian phiên). Cả 2 đã Done, verify live.

## Thay đổi Codebase

### AA-632 (Done) — PR #425, App
- `services/acp_shared/slate.py`: `_choose()` nhận thêm `seen_places: set[str] | None` optional
  (mặc định `None` giữ hành vi cũ — mỗi Channel có set riêng). `propose_slate()` tạo 1 `seen_places`
  set trước loop `for channel in CHANNEL_BARS` và truyền chung cho mọi `_choose()` call trong 1 lần
  propose — dedupe place across Channels cùng tenant (follow-up đã defer từ AA-631).
- 3 test mới trong `tests/unit/test_aa511_slate.py`. Full suite 30/30 pass.
- Deploy Dev COMPLETED, taskDef `aa-cis-dev-api:324`.

### AA-623 (Done) — 6 PR, 2 repo

**Vấn đề gốc:** trang External Spend (`/admin/llm-usage`, AA-622) chỉ tính cost ước tính từ token
(`llm_call_log`/`dfs_call_log`), không phải hóa đơn AWS thật. Cần tích hợp Cost Explorer để đối chiếu.

**Phát hiện quan trọng giữa phiên:** acc2 (005097885195) là **member account**, KHÔNG phải AWS
Organizations payer (`aws organizations describe-organization` → payer thật là `033086823579`,
không liên quan acc1/2/3). Vậy không có 1 lệnh CE consolidated nào gọi được cả 3 account — mỗi
account phải tự có quyền đọc CE riêng. Giải pháp: mirror đúng pattern Bedrock satellite đã chạy
production (`bedrock_satellite_assume.tf`/`bedrock_invoker_import.tf`/`acc3-bedrock/main.tf`).

**Terraform (repo AA-CIS-Infra):**
- PR #68 (App/Infra trước, đã merge/apply trước khi phát hiện gap): acc2 tự có
  `ce:GetCostAndUsage` trực tiếp trên `ecs_task_infra_status_readonly` policy — Resource="*"
  (CE không hỗ trợ resource-level ARN).
- PR #69 (merge + apply): `accounts/acc1-bedrock/cost_explorer_reader.tf` — role mới
  `AA-CostExplorer-Reader`, trust acc2's ECS task role qua ExternalId `aa623-satellite-cost-explorer`.
  `accounts/acc3-bedrock/cost_explorer_reader.tf` — role `AA3-CostExplorer-Reader`, ExternalId
  `aa623-satellite-cost-explorer-acc3`. `accounts/aa365/cost_explorer_satellite_assume.tf` —
  policy mới trên acc2's ECS task role cho `sts:AssumeRole` vào 2 role trên.
- PR #70 (merge, không liên quan trực tiếp AA-623 nhưng phát hiện trong lúc apply PR #69):
  `accounts/acc1-bedrock/versions.tf`'s backend S3 block THIẾU `profile` (khác acc3-bedrock đã có)
  → mọi `terraform init/plan/apply` ở root này rơi về credential chain mặc định
  (`[default]` = acc2 MFA-assume-role) → lỗi `assume role with MFA enabled, but
  AssumeRoleTokenProvider session option not set`. Fix: thêm `profile = "pqnghiep-admin"` vào
  backend block. Verify: `terraform plan` "No changes" sau fix (chỉ là config fix, không đụng state).

**Backend (repo AA-CIS-App):**
- PR #426: migration 167 (`shared.cost_explorer_snapshot`, 1 dòng/account/service/period/fetch);
  `shared/aws_client/cost_explorer.py` — `fetch_all_accounts_cost()` (acc2 direct call, acc1/acc3
  qua STS AssumeRole session-cache giống `bedrock_satellite.py`, chịu lỗi từng account riêng) +
  `record_snapshot()`/`read_latest_snapshot()`; 2 endpoint mới trong `admin_llm_ops.py`:
  `POST /admin/cost-explorer/check` (secret-gated) + `GET /admin/cost-explorer`. 12 unit test mock.
- PR #427 (bugfix phát hiện khi test LIVE, không phải mock): CE trả `period_start`/`period_end`
  dạng string `'YYYY-MM-DD'`, asyncpg cần `date` object thật (`.toordinal()`), insert thật lỗi
  `asyncpg.exceptions.DataError`. Thêm `_to_date()` helper + regression test. 13/13 pass.
- PR #428: FE panel mới trên Overview tab (`frontend/app/admin/llm-usage/page.tsx`) —
  "AWS actual (Cost Explorer) vs estimated (token)", stat card so sánh, bảng breakdown theo
  account (acc1/acc2/acc3), nút "Refresh from AWS" (POST `/check` on-demand), cập nhật lại
  "Reconcile note" (bỏ câu "tracked separately" cũ). `tsc`/`eslint`/`next build` sạch.

## Thay đổi Hạ tầng

- acc1 (867490540162): role mới `AA-CostExplorer-Reader` + policy `CostExplorerReadOnly`.
- acc3 (786888028788): role mới `AA3-CostExplorer-Reader` + policy `CostExplorerReadOnly`.
- acc2 (005097885195): policy mới `aa-cis-dev-ecs-assume-cost-explorer-reader` trên
  `aa-cis-dev-ecs-task-role` (AssumeRole vào 2 role trên); `ecs_task_infra_status_readonly` đã có
  `ce:GetCostAndUsage` từ PR #68.
- `accounts/acc1-bedrock/versions.tf`: backend S3 config thêm `profile = "pqnghiep-admin"`.
- Migration 167 áp dụng tay vào RDS dev qua ECS exec (container không có `psql`, dùng
  `asyncpg` chạy script Python inline qua `aws ecs execute-command`).

## Bằng chứng verify

- ECS deploy App PR #426/#427/#428: `rolloutState: COMPLETED`, taskDef cuối `aa-cis-dev-api:326`
  (sau #427; #428 là FE nên deploy qua Vercel riêng, không đụng taskDef ECS).
- `aws iam get-role --role-name AA-CostExplorer-Reader` (acc1) và `AA3-CostExplorer-Reader` (acc3)
  → cả 2 tồn tại thật sau khi Nghiệp apply PR #69.
- **Test full-flow thật trên AWS (không mock):** `POST /admin/cost-explorer/check` →
  `{"row_count":194,"errors":{},"period_start":"2026-09-16","period_end":"2026-09-23"}` — cả 3
  account fetch thành công, 0 lỗi. `GET /admin/cost-explorer` sau đó trả 194 dòng, có đủ cả 3
  account_id (005097885195, 867490540162, 786888028788), nhiều service AWS thật (EC2, RDS, ECS,
  ElastiCache, Bedrock/Cohere Embed, WAF...).
- FE: Nghiệp gửi 3 screenshot xác nhận panel "AWS actual (Cost Explorer) vs estimated (token)"
  render đúng trên `aa-cis.lumiguides.it.com/admin/llm-usage` — AWS actual $57.95 vs LLM estimated
  $22.29, breakdown theo account (acc2 $31.09, acc3 $25.99, acc1 $0.86), Reconcile note đã update.
- Linear AA-623 cập nhật đủ evidence từng bước, đóng Done cuối phiên với 6 PR attachment.

## Còn lại

- AA-599/AA-594 (G4 rerun) — vẫn chờ Nghiệp go-ahead, cần G1 (row count)/G2 (FK graph) mới trước
  khi chạy script reset-v2 đã soạn ở S193.
- AA-605 (admin UI style sync với adventure.asia) — Backlog, chưa đụng.
- AA-628 (engagement feedback loop) — Backlog, cần STEP0 design (chưa có nguồn data engagement).

## Lưu ý kỹ thuật cho phiên sau

- **Terraform backend S3 thiếu `profile` là bug âm thầm nguy hiểm:** `provider "aws" { profile }`
  KHÔNG áp dụng cho backend init/state — chỉ áp dụng cho resource. Nếu backend block thiếu
  `profile`, Terraform rơi về credential chain mặc định (`AWS_PROFILE` env, hoặc `[default]` trong
  `~/.aws/config`). Trong workspace này `[default]` là acc2's MFA-assume-role — khi chạy Terraform
  cho acc1/acc3 mà thiếu `profile` trong backend, sẽ lỗi MFA khó hiểu (tưởng lỗi credential, thật
  ra là thiếu 1 dòng config). Đã fix `acc1-bedrock` (PR #70); nếu tạo root Terraform mới cho
  acc1/acc3 sau này, LUÔN copy backend block đầy đủ từ `acc3-bedrock/versions.tf` (đã đúng), không
  copy thiếu từ acc1-bedrock cũ.
- **Migration DB không tự động apply** — không có bước CI/CD nào chạy migration khi deploy (chỉ
  build+push Docker+update ECS task def). Phải apply tay. Container không có `psql` binary — dùng
  `aws ecs execute-command --interactive --command "python3 -c '...'"` với `asyncpg` (đã có sẵn
  trong image vì app dùng) để chạy raw SQL từ migration file. Pattern:
  ```
  aws ecs execute-command --cluster aa-cis-dev-cluster --task <task-arn> --container api \
    --interactive --command "python3 -c \"import asyncio,asyncpg,os
  async def m():
      sql=open('api/migrations/NNN_xxx.sql').read()
      conn=await asyncpg.connect(os.environ['DATABASE_URL'])
      try: await conn.execute(sql); print('OK')
      finally: await conn.close()
  asyncio.run(m())\""
  ```
- **asyncpg date binding:** không bao giờ pass string `'YYYY-MM-DD'` trực tiếp vào asyncpg cho
  cột `DATE`/`TIMESTAMP` — nó không tự parse, cần `datetime.strptime(...).date()` trước khi bind.
  AWS APIs (Cost Explorer, và có thể nhiều SDK khác) trả date dạng string theo convention riêng.
- **Terminal WSL trong phiên này bị treo dài (silent, không garble) nhiều lần** — nguyên nhân xác
  nhận 2 lần là do lệnh `aws` (profile có MFA-assume-role, ví dụ `aa365-admin`) chờ nhập MFA code
  mà agent không thấy prompt (agent chỉ thấy exit code -1, không thấy text "Enter MFA code"). Khi
  gặp treo dài không lý do rõ, nghi ngờ đầu tiên nên là "có lệnh aws đang chờ MFA" — hỏi Nghiệp
  chạy `aws sts get-caller-identity --profile <profile>` trong terminal thật của họ để giải phóng
  session cache, agent sẽ tự phục hồi sau đó (không cần agent tự nhập gì, chỉ cần Nghiệp tương tác
  1 lần cho MFA prompt). `control_bash_process`/`get_process_output` (kênh terminal riêng) là cách
  hiệu quả để chẩn đoán process nào thực sự "running" (treo) vs terminal chính chỉ delay tạm.
- **Terraform provider profile khác nhau giữa `pqnghiep-admin` (SSO, cần `aws sso login`) và
  `aa365-admin`/`nghiep_aa365` (MFA-assume-role hoặc static key)** — không nhầm 2 loại auth này,
  chúng cần quy trình unlock khác nhau khi hết hạn.
