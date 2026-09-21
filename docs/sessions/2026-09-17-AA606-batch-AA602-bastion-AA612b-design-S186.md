# S186 — AA-606 Bedrock Batch (merged) + AA-602 terminate bastion + AA-612(b) điều tra/tư vấn/chốt 3 sub (Kiro, 2026-09-17)

Tác nhân: **Kiro**. Tiếp nối S185.

## Trạng thái
Hoàn tất 3 việc: (1) **AA-606** build Bedrock Batch Inference cho S1 rewrite writer — 2 PR merged
(App #394, Infra #62), Terraform applied cả 3 root, issue Done. (2) **AA-602** terminate bastion
EC2 + dọn IAM — Done. (3) **AA-612(b)** điều tra T7-T11 đối chiếu Ms.Thư + tư vấn thiết kế (không
port máy móc) + chốt thiết kế redesign social tenant + tạo 3 sub-issue (AA-613/614/615). AA-612 giữ
In Progress (phần build (b) chờ, đã tách sub).

## Thay đổi Codebase (repo AA-CIS-App) — AA-606, merged main `c95573c` (PR #394)
### File mới
- `services/content_generation/batch_prompt.py`: builder prompt attempt-1 STANDALONE dùng chung
  với generate_node (single source of truth, batch & sync không drift). `build_s1_system_prompt`/
  `build_s1_user_prompt`/`build_brand_diff_block`/`materialize_s1_prompt`/`prompt_version_of`.
- `shared/llm_client/bedrock_batch.py`: `build_model_input` (body y hệt invoke_claude), `build_
  manifest_jsonl` (recordId=tour_id, dedup guard), `upload_manifest`, `submit_batch_job`
  (CreateModelInvocationJob), `get_batch_status`, `poll_batch_job`, `read_batch_output`.
  `_s3_client` dùng boto3 NATIVE acc2 (bucket cùng account; invoker role KHÔNG có S3 perm — chỉ
  Bedrock batch service role mới cross-account). `MIN_BATCH_RECORDS=100` (verified khớp quota live).
  Batch service role arn: acc1=`aa-bedrock-batch-inference-role`, acc3=`aa3-bedrock-batch-inference-role`.
  s3BucketOwner=005097885195.
- `services/content_generation/s1_batch.py`: `_load_prompt_state` (đọc raw_tours+brand+lessons+SEO),
  `submit_s1_batch` (materialize N→JSONL→S3→submit), `ingest_s1_batch` (poll→read→mỗi tour gọi
  `_execute_run_tour(batch_text=...)`).
- `tests/unit/test_aa606_bedrock_batch.py`: 19 test thuần (manifest/dedup, model_input, parse, builder).
### File sửa
- `services/content_generation/graph.py`: thêm `parse_generated_json` (parse+json-repair salvage
  dùng chung), `_apply_seo_keywords_used`, `seed_generated_node`, **`build_graph_from_generated()`**
  (entry seed→validate→judge→gate; retry loop VẪN về generate on-demand attempt-2/3). `ContentState
  += batch_text`. Gỡ import thừa sau refactor: `hashlib` (prompt_version giờ qua prompt_version_of),
  `SYSTEM_PROMPT`+`build_rewrite_prompt` (generate_node dùng builder). generate_node refactor dùng
  builder chung + `_build_brand_diff_block` delegate.
- `api/routers/v1_pipeline.py`: `_rewrite_tour` +batch_text/batch_model_used/batch_account, chọn
  build_graph_from_generated khi có batch_text.
- `api/routers/admin_pipeline.py`: `_execute_run_tour` +batch context (forward xuống _rewrite_tour,
  tái dùng 100% brand-resolve/SEO/persist/export/review-queue). Endpoint **`POST /admin/s1-batch/
  submit`** (202 + background poll+ingest task `_s1_batch_ingest_task`) + **`GET /admin/s1-batch/
  {job_id}`**. Dùng jobs_repo (job_type `s1_batch`).

**Mô hình lai**: batch chạy WRITER attempt-1 (Haiku, acc3 primary); judge (gpt-4.1) + retry loop
generate↔judge giữ on-demand. Tour trượt gate sau batch → build_graph_from_generated route xuống
generate on-demand attempt-2/3 → hành vi sau gate y hệt luồng đồng bộ.

## Thay đổi Hạ tầng (repo AA-CIS-Infra) — merged main `f6b540c` (PR #62), applied live
- `modules/s3/main.tf`: thêm prefix `batch-input/s1-rewrite/*` + `batch-output/s1-rewrite/*` vào
  bucket policy bronze (4 statement acc1+acc3 get/put + list).
- `accounts/acc1-bedrock/main.tf` + `accounts/acc3-bedrock/batch.tf`: thêm 2 prefix vào batch-role
  S3 policy (ReadBatchInput/WriteBatchOutput/ListBucketForBatchPrefixes).
- **Applied cả 3 root (0 destroy mỗi cái)**: aa365 (creds acc2 MFA export), acc3-bedrock (acc2 assume),
  acc1-bedrock (profile `acc1-legacy-default` = IAM user admin_nghiep acc1).
- **AA-602**: terminate bastion `i-006e9b5bc05c6861f` (state=terminated). IAM `aa-cis-g0-bastion-role`
  + `aa-cis-g0-bastion-profile` (tạo tay ở G0, grep Terraform 0 match → xóa tay: detach SSM policy →
  remove from profile → delete profile → delete role, verify NoSuchEntity). SG dùng chung
  `aa-cis-dev-sg-app` (không có rule tạm cần revert). Tunnel SSM đóng theo bastion. RDS snapshot G0
  `aa-cis-dev-db-g0-audit-20260916` GIỮ (rollback G4/G5).

## Bằng chứng verify
- **AA-606**: py_compile 7 file sạch; test_aa606 19/19 pass; **full tests/unit 1993 passed** (2 fail
  duy nhất = test_aa324 do thiếu OPENAI_API_KEY LOCAL — không regression, thêm OPENAI_API_KEY=dummy
  → 4/4 pass; CI có key thật → xanh). CI PR #394 = 5/5 SUCCESS (Lint/Security/Unit/Integration/Docker).
- **Quota Bedrock Batch Claude Haiku 4.5 us-west-1 (service-quotas live)**: min-records=**100** (khớp
  MIN_BATCH_RECORDS), max 100,000/job, input≤1GB, job≤5GB, max 100 job in-progress → 763 tour 1 job.
- **Terraform**: validate 3 root OK; plan aa365 module.s3 = `0 add/1 change/0 destroy`; apply cả 3 =
  0 destroy.
- **Sửa 1 test kỳ vọng sai của chính mình**: JSON hợp lệ không `name` vẫn trả dict (name-guard chỉ áp
  nhánh salvage, khớp generate_node gốc) → tách thành 2 test.

## Còn lại (việc đầu phiên sau S187)
1. **AA-613 (Sub 1 backend)** — nền build redesign social tenant. Chi tiết trong issue: gate `severity`
   (block/warn/note) + metrics table (migration 153) + dọn leak `/pieces` (bỏ held_reason/gate_ledger/
   repair_log/flags khỏi response tenant) + bỏ `held` phía tenant (sau ≤2 retry = approved) + tách F9
   (cta/FACT_CHECK giữ block, brand_fit/GENERIC_AI_WORDING → warn) + F8 → warn + **fix BUG blog publish
   markdown→HTML fragment** (`v1_publish._call_adapter` đẩy content_text markdown thô vào WordPress) +
   export full-HTML(document) VÀ bare-article(fragment) + export/publish ghi audit. Build TRƯỚC.
2. **AA-614 (Sub 2 FE tenant)** — My Content phẳng (ẩn gate/held, bỏ not_ready) + khóa copy màn hình
   (user-select:none vùng hiển thị, CHỪA textarea edit AA-569) + publish/export rõ. Sau Sub 1.
3. **AA-615 (Sub 3 FE admin monitor)** — telemetry gate/severity/retry/publish theo tenant/kênh, MỞ RỘNG
   trang có sẵn (run-health/platform-stats), không tạo trang mới. Priority Medium, sau Sub 1.
4. **AA-599 (G4) rerun S1 763 tour** — CHẶN bởi điều kiện (đã comment vào AA-599): (a) verify luồng nhỏ
   batch vài tour admin+tenant đúng logic + xác nhận CreateModelInvocationJob nhận inference-profile ARN
   cross-account (chưa test job thật), (b) DỌN SẠCH data dẫn xuất (105 tour rác + data verify) bằng
   script G3 `docs/audit-cis-g3-reset.sql` — Nghiệp duyệt trước, (c) rồi mới batch full. Cần dựng lại
   bastion cho verify+dọn.
5. **Verify `atom_ranking.said`** — nếu chưa nạp thật thì 4 kênh attention-led (linkedin/fb/ig/tiktok)
   không bao giờ clear bar 150 → slate rỗng. Verify khi dựng bastion (gộp G4). Điều kiện chặn cho hành
   vi thật của Sub 2/3.
6. **AA-603** (DROP N7/N8 dead + drop column starred) — CHƯA làm, cần gỡ code reader + deploy + DROP qua
   DB (bastion). Để lúc dựng bastion.
7. **AA-610** rank-sum score ranking (điều tra, Medium) — chưa động.

## Lưu ý kỹ thuật (phiên sau — QUAN TRỌNG về shell)
- **ROOT CAUSE shell "chết" (đã xử lý triệt để phiên này)**: truyền tham số `cwd` = WSL path làm
  terminal backend WSL treo (process spawn được nhưng KHÔNG chạy lệnh, file không tạo ra, kể cả `echo`;
  list_processes hiện "running" mãi). **FIX: BỎ tham số `cwd`, dùng `cd /home/nghiep/... &&` TRONG lệnh**
  + luôn ghi output ra file rồi read_file. stdout nhiễu (ký tự lặp `eecho`, prompt zsh theme) + exit -1
  đều GIẢ — lệnh vẫn chạy. Đây là cách chạy shell ổn định trong phiên này.
- Shell vẫn kẹt lại sau các lệnh `sleep` dài (sleep 60/90) → tránh sleep dài trong 1 execute_bash; nếu
  kẹt, Nghiệp reset/khởi động lại IDE Kiro rồi tiếp.
- zsh: glob không match (`*.tf`, `.lsr*.txt`) làm dừng lệnh giữa chừng → quote glob (`"--include=*.tf"`)
  hoặc rm từng file tên đầy đủ.
- Terraform apply cần MFA: creds acc2 đã MFA (`nghiep-admin-8h-session`); export cho TF bằng
  `export $(aws configure export-credentials --format env | xargs) && unset AWS_PROFILE`. acc1 backend
  state ở bucket acc1 → cần profile `acc1-legacy-default` (không phải creds acc2).
- Branch protection AA-CIS-App: 5 CI job required, Vercel KHÔNG required. `strict:true` → branch phải
  up-to-date: khi PR BEHIND, `git fetch origin main && git merge origin/main --no-edit && git push` rồi
  auto-merge tự chạy. `gh pr merge <n> --squash --auto`.
- PR xóa/refactor import: PHẢI chạy full `tests/unit/` (env `JWT_SECRET=x AWS_*=dummy
  AWS_EC2_METADATA_DISABLED=true`, thêm `OPENAI_API_KEY=dummy` nếu chạm client.py) — `.venv/bin/python`.
- grep_search (tool) chập chờn trên path WSL UNC (lúc 0 match cho chuỗi chắc có, lúc chạy được) — dùng
  `grep -rn` qua bash khi cần chắc.

Log local: `docs/sessions/2026-09-17-AA606-batch-AA602-bastion-AA612b-design-S186.md`.
