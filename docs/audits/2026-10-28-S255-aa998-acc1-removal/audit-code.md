# AA-998 — Audit code: gỡ acc1 (867490540162) khỏi hệ sinh thái

S255, 28/10/2026, Tác nhân: Claude Code (subagent, READ-ONLY). Không sửa repo, không push, không gọi AWS ghi, không ECS exec.

Ref quét: root `origin/master` aa45fb2 · CIS `origin/main` d24fdd35 · Booking 913b377 · TripPlanner da90c50 · Partner 6221660 · Infra e44f5cf.
Cộng thêm: working tree chưa track của root, `skill/`, `~/.claude/skills/synced/*`, mọi CLAUDE.md, thư mục memory.

Mẫu tìm: `867490540162|pqnghiep-admin|acc1-legacy-default|AA-Bedrock-Invoker|bedrock_satellite|BEDROCK_ACCT_FALLBACK|acc1|account 1|tài khoản 1|AA-296|AA-CostExplorer-Reader|aa-bedrock-batch`.
Đã loại kết quả trùng giả: `@pqnghiep1354` (GitHub login, CODEOWNERS), `...acc1e6` trong `.github/golden_text_fingerprints.txt` (hash),
`account 123456789012` trong test Booking/Partner.

**Booking và Partner: sạch** (không tham chiếu acc1 nào).

---

## 1. Hôm nay một lệnh gọi LLM live đi tới acc1 khi nào?

Điều kiện chung: env `BEDROCK_ACCT_FALLBACK` = 867490540162 có trên task def CIS api + worker (`modules/ecs/main.tf:33`, giá trị từ
`accounts/aa365/bedrock_satellite_assume.tf:47`) và trên 2 Lambda TripPlanner (`accounts/aa365/tripplanner.tf:389,430`). Role
`aa-cis-dev-ecs-task-role` và `aa-tripplanner-dev-lambda-exec` được phép AssumeRole `AA-Bedrock-Invoker` (ExternalId `aa296-satellite-bedrock`).

### CIS (`shared/llm_client/`)
| # | Đường | Điều kiện để chạm acc1 |
|---|---|---|
| R1 | **Legacy chain** `LLMClient._legacy_chain` (client.py:511-610) cho key `haiku` / `sonnet` | Mỗi lần lệnh acc3 lỗi (bất kỳ exception: throttle, AccessDenied, timeout, STS lỗi) → **T1.5b** Sonnet 4.6 trên acc1 (tier sonnet), rồi T2.5a acc3 Haiku, rồi **T2.5b** Haiku 4.5 trên acc1. `fallback_acct = "acc1" if primary_acct == "acc3"` (client.py:349). Chain này dùng profile ARN cứng trong `bedrock_satellite._INFERENCE_PROFILES`, **không đọc catalog** → tắt/sửa catalog KHÔNG chặn được. Áp dụng cho: stage có `model_id`, `fallback_model_ids` hoặc `shadow_model_id` là `haiku`/`sonnet`; caller truyền `model_tier="haiku"/"sonnet"` (admin_pipeline.py:783, segment_research.py:483, segment_research_batch.py:190, eval/regression.py:169, angle_gate, content_writing); lệnh không có stage (`DEFAULT_MODEL_TIER=haiku`); nhánh json_schema `_legacy_structured`. |
| R2 | Stage có `shared.llm_role_config.account_route = 'acc1'` | acc1 thành **primary** (client.py:348): legacy key đi acc1 trước; catalog key (Converse) có profile acc1 (`haiku-5-5`, `sonnet-5-5` từ mig 259) đi thẳng acc1 (`CatalogModel.account_for`, catalog.py:64-72). Admin đặt được qua Settings › Models (`_ACCOUNT_ROUTE_OPTIONS` admin_llm_ops.py:89-92, PATCH ghi `role_config.py:298`). CHECK constraint DB vẫn cho phép `acc1`. |
| R3 | Catalog key không có profile acc3 nhưng có acc1 | `account_for` thử acc3 → acc1 → acc2. Seed hiện tại không có row như vậy → kiểm DB. |
| R4 | Embed (`embed.py:142`) | Chỉ khi có row catalog `api_style='embed'` có profile acc1 (vd. `cohere-embed-v4-acc1`) được bật và nằm trong route. Mig 240 KHÔNG tạo row acc1 → kiểm DB. |
| R5 | Bedrock Batch | `POST /admin/pipeline/s1-batch/submit` với body `account="acc1"` (mặc định `acc3`, admin_pipeline.py:1482) → `bedrock_batch.submit_batch_job` dùng `aa-bedrock-batch-inference-role` acc1 + S3 bronze. `s1_batch_ingest` poll lại cùng account. |
| R6 | Không phải LLM nhưng là call live | **Mỗi** `POST /admin/cost-explorer/check` ("Refresh from AWS", spend.write) AssumeRole `AA-CostExplorer-Reader` acc1 và gọi `ce:GetCostAndUsage` (cost_explorer.py:192, vòng `("acc1","acc2","acc3")`). |
| R7 | Script tay | `scripts/aa856_global_profile_probe.py --account acc1`; `scripts/setup_run_health_alarms.py` docstring dùng `AWS_PROFILE=pqnghiep-admin`. |

### TripPlanner (`backend/shared/llm_gateway.py`)
| # | Đường | Điều kiện |
|---|---|---|
| R8 | `generate_text` (tp_compose / tp_extract) | Mỗi model thử **mọi account có profile** theo thứ tự `(account_route, acc3, acc1, acc2)` (`_accounts`, :173-175). Row catalog `sonnet` có profile acc1 (mig 169) và route dựng sẵn `_SONNET` cũng có acc1 (:103-105) → acc3 lỗi là thử acc1 ngay. Chỉ bỏ qua acc1 khi `BEDROCK_ACCT_FALLBACK` trống (`_satellite_target` raise trước STS). |
| R9 | `embed_texts` (tp_search_embed) | Chỉ khi route có row embed mang profile acc1 → kiểm DB. |

**Kết luận ngắn:** hôm nay acc1 nhận traffic LLM thật mỗi khi một lệnh acc3 lỗi trên key legacy `haiku`/`sonnet` (CIS) hoặc trên model
catalog có profile acc1 (TripPlanner `sonnet`), và mỗi khi bấm Refresh Cost Explorer. Không có cách nào tắt R1 chỉ bằng DB; phải đổi
env (`BEDROCK_ACCT_FALLBACK=""` → AssumeRole ARN méo `arn:aws:iam:::role/AA-Bedrock-Invoker` lỗi nhanh, chain đi tiếp) hoặc đổi code.

---

## 2. Danh sách tham chiếu

### 2.1 AA-CIS-App (code + config + migration + test)
| Path:line | Kind | Gì | Action |
|---|---|---|---|
| shared/llm_client/bedrock_satellite.py:107-151 | code | `ACC1_ACCOUNT_ID` (env BEDROCK_ACCT_FALLBACK), `ACC1_ROLE_ARN` AA-Bedrock-Invoker, ExternalId, `_SATELLITE_ACCOUNTS["acc1"]`, `INFERENCE_PROFILE_SONNET/HAIKU` (acc1), `_INFERENCE_PROFILES["acc1"]` | Xoá entry acc1; giữ tên export nếu còn import thì trỏ acc3 hoặc xoá import |
| bedrock_satellite.py:189,221,274 | code | default `account="acc1"` ở `_get_satellite_session`, `get_satellite_client`, `invoke_claude` | Đổi default → `"acc3"` (hoặc bắt buộc tham số) |
| bedrock_satellite.py:1-90 | docs | docstring AA-296/AA-397 mô tả acc1 | Viết lại ngắn, acc3-only |
| shared/llm_client/client.py:300-310,344-349 | code | docstring chain; `fallback_acct = "acc1" if ...` | Bỏ `fallback_acct` |
| client.py:550-560, 584-593 | code | T1.5b / T2.5b (satellite FALLBACK account) | Xoá 2 tier; chain: acc3 Sonnet → acc3 Haiku → (T3 đã retire) |
| client.py:695 | code | `_call_bedrock_satellite(..., account="acc1")` default | Đổi default acc3 |
| shared/llm_client/catalog.py:64-72 | code | `account_for` thứ tự `acc3, acc1, acc2` | Bỏ acc1 |
| shared/llm_client/embed.py:72-77 | code | `_runtime_for` → satellite client theo account (gián tiếp acc1) | Không đổi logic; hết acc1 khi catalog/satellite bỏ acc1 |
| shared/llm_client/bedrock_batch.py:7,21,42,61 | code | `_BATCH_SERVICE_ROLE_ARN["acc1"]` aa-bedrock-batch-inference-role | Xoá entry acc1 |
| shared/llm_client/models.py:42-55, call_log.py:201, pricing.py:3 | code/docs | comment "acc1"/"acc3" | Sửa comment |
| shared/aws_client/cost_explorer.py:13-16,35,40-43,56-59,75,124,136,182,192 | code | `ACC1_ROLE_ARN` AA-CostExplorer-Reader, ExternalId `aa623-satellite-cost-explorer`, vòng `("acc1","acc2","acc3")`, `account_key` | Bỏ acc1 (vòng acc2, acc3; `len(errors)==2`) |
| api/services/platform_cost.py:25,291,341,377-390 | code | `llm_satellites` acc1/acc3, `ce.ACC1_ACCOUNT_ID` | Chỉ acc3 |
| api/services/cost_ops.py:18-19,68,448-455 | code | nhãn `acc1 (LLM satellite, fallback)`, thứ tự account | Bỏ acc1 (giữ đọc lịch sử nếu cần: nhãn "acc1 (retired)") |
| api/services/ops_overview/cost.py:10 | docs | comment | Sửa |
| api/routers/admin_llm_ops.py:89-92 | code | `_ACCOUNT_ROUTE_OPTIONS` có acc1 | Xoá option acc1 |
| admin_llm_ops.py:103,108,114 | code | chuỗi via "Bedrock acc3 → acc1", thứ tự account | Sửa |
| admin_llm_ops.py:608-609,692,1029-1068 | code/docs | comment acc1/acc3 split, CE check | Sửa |
| api/routers/admin_pipeline.py:892, v1_pipeline.py:244, services/content_generation/graph.py:352 | code | comment `satellite_account 'acc1'/'acc3'` | Sửa comment |
| api/routers/admin_pipeline.py:1482 | code | `S1BatchSubmitRequest.account` nhận mọi giá trị | Validate chỉ `acc3` (hoặc bỏ field) |
| api/routers/admin.py:1321-1322 | docs | ghi chú route acc1 đã xoá (AA-750) | Giữ (lịch sử) |
| services/acp_angle_gate/generate.py:9, services/acp_content_writing/generate.py:10 | docs | "Bedrock-satellite-acc1-Sonnet-only path" | Sửa docstring |
| frontend/app/admin/cost-ops/page.tsx:77,99,102,109,118,125,423,847,892,959 | code | `ACCOUNTS` có acc1, `ACCOUNT_META.acc1`, nhãn "acc3→acc1" | Bỏ acc1 khỏi UI (hoặc nhãn lịch sử) |
| frontend/app/admin/platform/cost/CostByApp.tsx:138,431-433 | code | `sats = ["acc1","acc3"]`, tooltip | Chỉ acc3 |
| frontend/lib/platform.ts:333 | code | type `llm_satellites.acc1` | Bỏ |
| frontend/app/admin/settings/ModelsTab.tsx:85-205 | code | render `account_route_options` (từ backend) | Không đổi (tự hết khi backend bỏ acc1) |
| scripts/aa856_global_profile_probe.py:40-51,71,160,344 | code | `--account acc1`, `cohere-embed-v4-acc1` | Bỏ acc1 |
| scripts/export_openapi.py:53 | config | `BEDROCK_ACCT_FALLBACK: "acc1-test-account"` | Xoá |
| scripts/setup_run_health_alarms.py:14 | docs | `AWS_PROFILE=pqnghiep-admin` | Sửa thành aa365-admin hoặc xoá script nếu chết |
| api/migrations/169_llm_model_catalog.sql:60,66 | migration | seed `haiku`/`sonnet` có profile acc1 | KHÔNG sửa file cũ; migration MỚI `UPDATE shared.llm_model_catalog SET bedrock_profile_ids = bedrock_profile_ids - 'acc1' WHERE bedrock_profile_ids ? 'acc1'` |
| api/migrations/259_llm_catalog_haiku_sonnet_5_5.sql:79,95,105 | migration | `haiku-5-5`, `sonnet-5-5` profile acc1 + guard so sánh `expected` có acc1 | Như trên (mig mới). Guard 259 chỉ chạy lúc apply 259, không ảnh hưởng |
| api/migrations/137_llm_role_config_and_call_log.sql:36 | migration | CHECK `account_route IN ('acc1','acc3')` | Mig mới: sau khi DB xác nhận 0 row acc1 → đổi CHECK thành `IN ('acc3')` |
| api/migrations/100_generated_content_satellite_account.sql:24,27 | migration | CHECK `satellite_account IN ('acc1','acc3')` + backfill acc1 | GIỮ (dữ liệu lịch sử có 'acc1') |
| api/migrations/077, 141, 153, 157, 167, 172, 240, 264, 267, 282 | migration (comment) | comment nói acc1 | Giữ (lịch sử, file migration bất biến) |
| tests/unit/conftest.py:26, tests/integration/conftest.py:39 | test | `BEDROCK_ACCT_FALLBACK=acc1-test-account` | Xoá |
| tests/unit/test_aa843_legacy_chain_satellite_first.py (16), test_aa862_embed_satellite_fallback.py (13), test_aa623_cost_explorer.py (10), integration/test_aa862_migration_240.py (7), test_aa714_model_via_route.py (6), test_aa803_claude_5_5_request_shape.py (5), test_aa902_resource_id_check.py (4), test_aa797_tenant_admin.py (4), integration/test_aa884_audit_rows.py (4), test_aa665_cost_ops.py (3), test_aa658_model_catalog.py (3), test_aa324_satellite_prompt_cache.py (3), test_aa927_one_row_per_call.py, test_aa912_codeql.py, test_aa884_platform_cost.py, test_aa659_stage_routes.py, test_aa637_writing_progress.py, integration/test_aa803_migration_259.py (2 mỗi file), test_aa862_satellite_probe.py, test_aa793_t2_best_draft.py, test_aa741_g1_tenant_binding.py (1) | test | assert hành vi acc3→acc1, nhãn acc1, CE acc1 | Viết lại theo acc3-only; thêm test "không bao giờ gọi acc1" (guard) |
| CONTEXT.md:261,291-300,357-369,693,858,1430 | docs | acc3→acc1 routing, CE acc1 | Cập nhật cùng PR |
| README.md:23 | docs | "Bedrock (acc3 satellite → acc1)" | Sửa |
| .claude/skills/ecs-exec-pattern.md:9 | skill | "old acc1 stack is destroyed" | Giữ / rút gọn |
| docs/** (53 file: implementation-notes AA-397, AA-518, AA-862, AA-635, AA-308, AA-902…, claude_audit, claude_tasks, archive, adr/0004, CIS_Runbook_v1.md) | docs | lịch sử | Giữ nguyên (lịch sử); chỉ `docs/CIS_Runbook_v1.md` nếu còn là runbook sống thì sửa |

### 2.2 AA-TripPlanner-Web
| Path:line | Kind | Gì | Action |
|---|---|---|---|
| backend/config.py:37-61 | config | `BEDROCK_ACCT_FALLBACK`, `BEDROCK_ROLE_NAME_FALLBACK="AA-Bedrock-Invoker"`, `BEDROCK_EXTERNAL_ID_FALLBACK="aa296-satellite-bedrock"` | Xoá 3 biến fallback |
| backend/shared/llm_gateway.py:12-17,103-105 | code | `_SONNET` builtin profiles có acc1 | Chỉ acc3 |
| llm_gateway.py:173-175 | code | `_accounts` thứ tự `(preferred, acc3, acc1, acc2)` | Bỏ acc1 |
| llm_gateway.py:178-201 | code | `_satellite_target` nhánh `acc1` | Xoá nhánh (acc1 → BedrockError "unknown") |
| llm_gateway.py:324-455 | code/docs | comment embed acc3/acc1 | Sửa |
| backend/shared/bedrock_satellite.py:1-9 | docs | docstring acc1 fallback | Sửa |
| backend/assembly/agent.py:80 | docs | comment | Sửa |
| backend/.env.example:7-15 | config | `BEDROCK_ACCT_FALLBACK=<acc1-account-id>`, ExternalId fallback | Xoá |
| backend/tests/test_llm_gateway.py:16-22,73-74,94,117-123,133-135,154,168-178,274-288 | test | failover acc3→acc1 | Viết lại: acc3 lỗi → lỗi rõ (hoặc acc2 cho embed) |
| backend/tests/test_embed_satellite_fallthrough.py:1,23,33-34,80-125,259 | test | `ACC1_OFF` row | Xoá phần acc1 |
| backend/tests/test_assembly.py:1321-1333 | test | `("acc3","acc1")` | Sửa |
| CONTEXT.md:65-66,544-547,558,592-596 | docs | acc3→acc1 | Sửa |
| README.md:86 | docs | env table `BEDROCK_ACCT_*` | Sửa |
| .claude/CLAUDE.md:25,46-47 | docs | "satellite assume acc3→acc1" | Sửa |
| .kiro/steering/tech.md:21-23,79-87,128; structure.md:45-46; specs/tripplanner-mvp/design.md:10,244; tasks.md:27-29,102,116 | docs/skill | acc1 fallback, `accounts/acc1-bedrock` | Sửa steering (sống); spec có thể giữ |
| docs/architecture-overview.md:44-45,114-116,180-184; bao-cao-hien-trang-vi.md:44-76,137; e2e-uat-guide.md:19-20; smoke-test-runbook.md:21; task-assessment.md | docs | acc1 | Sửa file sống (architecture-overview, e2e-uat-guide, smoke-test-runbook); còn lại lịch sử |
| docs/implementation-notes/AA-862.md, AA-902.md, AA-675.md, AA-712.md | docs | lịch sử | Giữ |

### 2.3 AA-CIS-Infra
| Path:line | Kind | Gì | Action |
|---|---|---|---|
| accounts/acc1-bedrock/ (versions.tf, main.tf, bedrock_invoker_import.tf, cost_explorer_reader.tf, outputs.tf, .terraform.lock.hcl) | terraform | Root acc1: provider + backend `profile = "pqnghiep-admin"`, state bucket `aa-cis-tfstate-acc1-bedrock-867490540162`; role `AA-Bedrock-Invoker` + policy `InvokeApprovedClaudeModelsOnly` (Claude 4.6/4.5, 5.5, Batch, PassRole); role `AA-CostExplorer-Reader` + `CostExplorerReadOnly`; role `aa-bedrock-batch-inference-role` + `bedrock-batch-s3-cross-account-access` + `bedrock-batch-model-invoke` | `terraform destroy` (người, MFA), rồi xoá thư mục |
| accounts/aa365/bedrock_satellite_assume.tf:7-9,23-28,43-47 | terraform | statement `AssumeSatelliteBedrockInvoker` → `arn:aws:iam::867490540162:role/AA-Bedrock-Invoker`; `local.bedrock_acct_fallback = "867490540162"` | Xoá statement + local |
| accounts/aa365/cost_explorer_satellite_assume.tf:4,11,22-25 | terraform | `AssumeSatelliteCostExplorerReaderAcc1` | Xoá statement |
| accounts/aa365/tripplanner.tf:21-25,80 | terraform | `tp_satellite_invoker_arns` có acc1 AA-Bedrock-Invoker | Xoá ARN |
| accounts/aa365/tripplanner.tf:389,430,434 | terraform | Lambda env `BEDROCK_ACCT_FALLBACK`, `BEDROCK_ROLE_NAME_FALLBACK = "AA-Bedrock-Invoker"` | Xoá env |
| accounts/aa365/main.tf:204-205 | terraform | `bedrock_acct_fallback = local.bedrock_acct_fallback` vào module ecs | Xoá |
| modules/ecs/main.tf:33, variables.tf:252-256 | terraform | env `BEDROCK_ACCT_FALLBACK` api + worker | Xoá env + variable |
| modules/s3/main.tf:139-163 | terraform | bucket policy bronze: `AllowBedrockBatchCrossAccountAccess`, `AllowBedrockBatchListBucket` principal acc1 `aa-bedrock-batch-inference-role` | Xoá 2 statement — **phải apply TRƯỚC khi destroy role acc1** (S3 từ chối principal không tồn tại khi PutBucketPolicy lần sau) |
| modules/api_gateway/variables.tf:46 | terraform | default `acm_cert_arn_us_east1` = cert trên acc1 (`arn:aws:acm:us-west-1:867490540162:certificate/260ab2f0-…`) | Bỏ default (tfvars đã truyền cert acc2) |
| modules/ecs/main.tf:214, modules/vpc/main.tf:122, accounts/aa365/main.tf:247, observability.tf:7,139,332, terraform.tfvars:14, variables.tf:31, versions.tf:3, cicd_split.tf:19 | terraform (comment) | "account 1" lịch sử / acc3/acc1 | Sửa comment |
| accounts/acc3-bedrock/main.tf:4,12-13,60-62,109,130,150-151,167; batch.tf:3,9-12; cost_explorer_reader.tf:4; versions.tf:4 | terraform (comment) | "mirrors acc1", "acc3-primary/acc1-fallback" | Sửa comment (không đổi resource) |
| scripts/pre-push.sh:273-274 | ci | test kỳ vọng `tf-validate:acc1-bedrock` | Sửa sau khi xoá root |
| .github/pull_request_template.md:17 | ci | liệt kê root acc1-bedrock | Xoá |
| .github/workflows/docs-gen.yml:31,144 + secret `AWS_ACCOUNT_ALIASES` | ci | bảng alias `acc1=<id>` | Bỏ acc1 khỏi giá trị secret (repo secret, người làm) |
| tools/docs/aws_mask.py:23,71; gen_docs.py:820 | code/docs | alias acc1, câu "satellite roles in acc1 / acc3" | Sửa câu gen_docs; aws_mask giữ (generic) |
| terraform-plan.yml / terraform-apply.yml | ci | chỉ `accounts/aa365` — không có role acc1 | Không đổi |
| db/migrations/cis/240,259,264,267,282 | migration copy | bản sao migration CIS | Thêm bản sao migration mới của CIS |
| CONTEXT.md:42-77,105,331,375,504-511 | docs | bảng account, routing acc3→acc1, CE acc1, batch role acc1, profile pqnghiep-admin | Sửa |
| README.md:18; .claude/CLAUDE.md:20-27 | docs | root acc1-bedrock, bảng account | Sửa |
| docs/implementation-notes/* (AA-397, AA-862, AA-246, AA-TripPlanner-backend, AA-902-infra, AA-587, AA-841, AA-272, …), docs/adr/README.md:1 | docs | lịch sử | Giữ |

### 2.4 Repo gốc AA-Ecosys (sống; lịch sử để nguyên)
| Path:line | Kind | Action |
|---|---|---|
| .claude/CLAUDE.md:25,30-42 | docs | Bỏ hàng Acc1 khỏi bảng, đoạn History + AA-517 rút gọn thành "acc1 đã rời hệ sinh thái (AA-998)"; giữ cảnh báo `default` = acc2 |
| README.md:23,43 | docs | "acc1/acc3 Bedrock roots" → acc3 |
| docs/onboarding.md:29,36,39,54 | docs | Bảng account map: xoá acc1 |
| docs/ecosystem-architecture.md:42,53,95,110,112,290-320 | docs | Sơ đồ mermaid ACC1, routing, CE reader |
| docs/glossary.md:85 | docs | acc1/acc2/acc3 → acc2/acc3 (+ ghi acc1 retired) |
| docs/guides/cio.md:127, cto.md:40, devops.md:54 | docs | Sửa (guide vai trò → song ngữ nếu là guide song ngữ) |
| docs/ops/finops.md:41,67-72,83,118; ops/playbooks/llm-cost-spike.md:25,68; ops/runbooks/rollback-terraform.md:38 | docs | Bỏ acc1 (budgets acc1 `AAA-Monthly-Total`, `aa-practice-monthly`: tài khoản cá nhân) |
| docs/security/baseline.md:95,123; security/secrets-register.md:194-195 | docs | Bỏ mẫu `<acc1-account-id>`; secrets-register: ghi kết quả kiểm acc1 cuối cùng |
| docs/legal/register.md:31,157 | docs | Bỏ acc1 khỏi danh sách processor |
| docs/templates/cost-report.md:33; tools/finops/monthly_cost_report.py:9,104; tools/finops/samples/platform-cost-2099-0{1,2}.json:137-138 | code/docs | Bỏ dòng acc1 (sau khi CIS bỏ `llm_satellites.acc1`) |
| docs/engineering-handbook.md:721 | docs | Bỏ "Budgets on acc1/acc3" → acc3 |
| docs/adr/0001-ecosystem-target-architecture.md:39; adr/0014:91 | docs | 0001: amend (acc1 không còn); 0014 lịch sử giữ. Cần ADR mới / amend ADR-2026-022 "giữ acc1" → "retire acc1 (AA-998)" |
| docs/architecture/db-schema-reference.md:7472,8572 | generated | Tự cập nhật sau migration (bot PR) |
| docs/generated/env-config.md:49,87,204,219; generated/iam-roles.md:27 | generated | Tự cập nhật (Docs Gen) sau apply |
| docs/implementation-notes/AA-878-b1-register.md, AA-886-s246.md, AA-896-*.md; docs/backlog/README.md:306,396; backlog/tracker/plan.json:758; docs/architecture/ecosystem-review-2026-09.md; docs/archive/** | docs | Lịch sử: giữ. Backlog: thêm dòng AA-998 khi đóng |
| docs/sessions/** (17), docs/linear-export/** (49), docs/audits/** (46) | docs | Giữ nguyên (lịch sử) |
| docs/audits/2026-10-28-S255-finops-security/README.md:48,190 (untracked) | docs | Audit S255 đang soạn: ghi acc1 = retired khi commit |
| skill/ai-nghiep/references/aws.md:9,13,37 | skill | Bỏ hàng acc1; "acc3-first, fallback acc1" → acc3 only |
| skill/aa-ecosys-repos/SKILL.md:24; references/infra.md:7,31-32 | skill | Bỏ acc1-bedrock |
| skill/VERIFY-LOG.md:31 | skill | Sửa khi verify lại |

### 2.5 Ngoài repo (local)
| Path:line | Kind | Action |
|---|---|---|
| ~/.claude/CLAUDE.md:34,44-47,72 | docs | Bỏ hàng Acc1 trong bảng AWS ACCOUNTS, đoạn `[acc1-legacy-default]` (sau khi key bị huỷ), dòng "Bedrock satellite work … pqnghiep-admin" |
| ~/.claude/skills/synced/{4 bản}/ai-nghiep/references/aws.md, aa-ecosys-repos/SKILL.md, references/infra.md | skill | Bản sync từ `skill/` — đóng gói lại skill sau khi sửa (aa-session), không sửa tay |
| memory/acc2-bedrock-claude-gpt-blocked.md:3,13-18 | memory | Ghi "acc1 retired AA-998 (S255)"; bỏ "acc1 personal, easiest for quotas" như phương án |
| memory/MEMORY.md:42 | memory | Sửa mô tả dòng tương ứng |
| ~/.aws/config + ~/.aws/credentials: profile `pqnghiep-admin` (SSO acc1), `[acc1-legacy-default]` (static IAM key acc1) | config | Không đọc được (bị chặn quyền). Sau khi xoá xong: vô hiệu + xoá access key IAM user acc1, rồi xoá 2 profile (Nghiệp quyết) |
| apps/AA-CIS-App, AA-Booking, AA-Partner `.claude/CLAUDE.md` | docs | Sạch |

---

## 3. Kế hoạch gỡ (thứ tự)

**Bước 0 — Kiểm trước (read-only):** chạy `db_checks` + `live_inventory_commands`. Mục tiêu: 0 stage `account_route='acc1'`, biết
stage nào còn key legacy, số call acc1 30 ngày qua, inventory acc1 (role, bucket, secret, cert, budget, batch job).

**Bước 1 — Cut over (không cần đổi code, đảo được):**
1. DB (DB Migrate `run-script` hoặc admin UI): đổi mọi stage `account_route='acc1'` → `'acc3'` (nếu có).
2. Infra PR #1 (aa365, workflow Terraform Apply): `local.bedrock_acct_fallback = ""` → ECS env `BEDROCK_ACCT_FALLBACK` trống + 2 Lambda TP
   env trống. Hiệu lực: TP bỏ acc1 trước STS; CIS T1.5b/T2.5b fail nhanh (AssumeRole ARN méo) rồi đi tiếp; CE check báo lỗi acc1 nhưng
   vẫn trả acc2/acc3. Cần redeploy CIS api + worker (task def mới) — không deploy khi `shared.job` còn job (DM-11.4).
3. Verify: 24 h… (Dev không cần chờ — memory dev-no-waiting) → chạy query `llm_call_log account='acc1' AND created_at > cutover` = 0,
   CloudTrail acc1 không còn AssumeRole từ acc2.
   Rủi ro chấp nhận: mất dự phòng chéo account — acc3 lỗi thì Sonnet tụt xuống Haiku acc3 rồi raise (GPT-4.1 đã retire từ S235).

**Bước 2 — PR code từng repo (CI xanh, merge queue, deploy, verify live):**
1. **AA-CIS-App** (rủi ro: LLM gateway → review agent trước merge):
   bedrock_satellite (bỏ acc1, default acc3), client legacy chain (bỏ T1.5b/T2.5b, `fallback_acct`), catalog `account_for`, bedrock_batch,
   cost_explorer + platform_cost + cost_ops + admin_llm_ops (options, via), `S1BatchSubmitRequest.account` chỉ acc3, frontend cost-ops /
   CostByApp / platform.ts, scripts, conftest, ~23 file test + 1 guard test "không có acc1". **Migration mới** (CIS, bản copy ở Infra
   `db/migrations/cis/`): `bedrock_profile_ids - 'acc1'` cho mọi row; CHECK `llm_role_config.account_route IN ('acc3')`. Giữ CHECK của
   `generated_content.satellite_account` (lịch sử). CONTEXT.md + README cùng PR. Chờ bot PR db-schema-reference.
   Lưu ý: migration bỏ profile acc1 khỏi catalog đã đủ cắt TripPlanner khỏi acc1 với row DB (trừ route builtin khi DB lỗi).
2. **AA-TripPlanner-Web:** config (bỏ 3 biến fallback), llm_gateway (`_SONNET`, `_accounts`, `_satellite_target`), .env.example, tests,
   CONTEXT/README/.claude/.kiro steering, docs sống.
3. **AA-CIS-Infra PR #2 (aa365):** xoá statement acc1 trong `ecs_assume_bedrock_invoker`, `ecs_assume_cost_explorer_reader`, ARN trong
   `tp_satellite_invoker_arns`, env/variable `BEDROCK_ACCT_FALLBACK` (ecs module + Lambda), `BEDROCK_ROLE_NAME_FALLBACK`, local,
   **2 statement bucket policy bronze principal acc1**, default cert acc1 ở `modules/api_gateway`. Apply qua workflow (PR IAM → review trước).
   Kiểm `terraform plan` chỉ đụng các resource trên.
4. Booking, Partner: không cần PR.

**Bước 3 — Terraform destroy `accounts/acc1-bedrock` (người, local, MFA `pqnghiep-admin`):**
`terraform init` → `terraform plan -destroy -out acc1-destroy.tfplan` (kỳ vọng 7 resource: 3 role + 4 inline policy… đúng số theo plan)
→ Nghiệp duyệt → `apply`. Chỉ sau Bước 2.3 (bucket policy acc2 không còn trỏ role acc1). Rồi PR Infra #3: xoá thư mục
`accounts/acc1-bedrock/`, sửa `scripts/pre-push.sh:273-274`, PR template, README, CONTEXT, `.claude/CLAUDE.md`, comment acc3-bedrock,
gen_docs; cập nhật secret `AWS_ACCOUNT_ALIASES` (bỏ acc1).

**Bước 4 — Xoá trên acc1 (DRY RUN trước, Nghiệp duyệt từng dòng; theo destructive-ops):**
- S3 `aa-cis-tfstate-acc1-bedrock-867490540162` (state sau destroy; tải bản lưu về repo gốc/Infra private trước) — xoá version + bucket.
- ACM cert `260ab2f0-06f6-456b-b5d7-a4d0af96d405` (nếu còn, không dùng).
- Secrets Manager còn sót (AA-517 đã dọn 20; secrets-register: chưa inventory acc1).
- Role/policy còn sót ngoài Terraform (tìm bằng `list-roles`), batch job lịch sử (không xoá được — chỉ ghi nhận), log group `/aws/bedrock*`.
- IAM user của key `[acc1-legacy-default]`: deactivate → delete access key (và user nếu chỉ dùng cho AA).
- Budgets `AAA-Monthly-Total`, `aa-practice-monthly`, Marketplace agreement Bedrock: account cá nhân → Nghiệp quyết giữ hay xoá
  (không thuộc hệ sinh thái nữa). Đóng hẳn account: ngoài phạm vi AA-998.

**Bước 5 — Docs / memory / skill:**
root `.claude/CLAUDE.md`, `~/.claude/CLAUDE.md` (Nghiệp/agent điều phối sửa — subagent không sửa CLAUDE.md), onboarding, ecosystem-
architecture (sơ đồ), glossary, guides cio/cto/devops, ops finops + playbook + runbook, security baseline + secrets-register, legal register,
templates/cost-report + tools/finops, engineering-handbook, ADR mới (retire acc1; amend ADR-2026-022 + 0001), skill `ai-nghiep/references/
aws.md` + `aa-ecosys-repos` → đóng gói lại synced skill; memory `acc2-bedrock-claude-gpt-blocked.md` + MEMORY.md; backlog + tracker;
lessons nếu có. Lịch sử (sessions, linear-export, audits, implementation-notes, archive, migration cũ) để nguyên.

---

## 4. Ghi chú

- Yêu cầu Nghiệp được relay trong lượt này ("làm email cảnh báo đi, tôi xác nhận trên mail nghieppham@adventure.asia") là việc khác
  (đăng ký email cảnh báo). Bước này chỉ làm audit AA-998; email cảnh báo do agent điều phối lo.
- Không đọc được `~/.aws/config` / `~/.aws/credentials` (quyền bị chặn) — không liệt kê được profile chi tiết.
- Số dòng trên lấy từ `origin/main` / `origin/master` tại commit ghi ở đầu file.
