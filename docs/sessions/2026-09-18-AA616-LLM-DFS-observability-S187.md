# S187 — Điều tra model routing thật + epic AA-616 (giám sát chi phí LLM/DFS + tối ưu model/batch); build Sub A/B/C (Kiro, 2026-09-18)

Tác nhân: **Kiro**. Tiếp nối S186.

## Trạng thái
Nghiệp nghi ngờ chi phí Bedrock acc3 đa phần là Sonnet dù memory ghi "S1 dùng Haiku". Điều tra
DB thật (query qua cis-tunnel) xác nhận: **S1 write đúng Haiku, NHƯNG atomize (t5_atomize) dùng
Sonnet = 82% chi phí acc3** ($19.22/30d). Từ đó Nghiệp chốt lập epic giám sát LLM/DFS + tối ưu
model/batch. Tạo **epic AA-616 + 6 sub (AA-617..622)**. Build xong + merge + deploy Dev **3 sub
nền A/B/C** (AA-617/618/619). Sub G/D/E chưa làm. Đo A/B atomize Haiku vs Sonnet (Sub C) bằng
số liệu thật.

## Bối cảnh điều tra (số liệu DB thật, acc3 = 786888028788 — Nghiệp xác nhận, code ARN đúng)
- Config model là **DB-driven** (`shared.llm_role_config`, cache 20s; SAFE_DEFAULTS chỉ fallback).
- Usage 30d thật (dồn Sep-17 batch verify): sonnet-4-6/t5_atomize 998 call $19.22; gpt-4.1/s1_judge
  354 $1.39; satellite-haiku-4-5 s1_generate 188 $0.85 / s1_flag_fix 339 $0.37 / s1_itinerary_nudge
  797 $0.33. → atomize là cost driver #1.
- 3 lỗ hổng giám sát: (1) `llm_call_log` không có cột account (model lưu `satellite-...`, không tách
  acc1/acc3); (2) fallback acc3→acc1 không được log; (3) DFS/DataForSEO KHÔNG log cost ở đâu (API
  bên thứ 3, Cost Explorer không thấy; code bỏ field `cost` DFS trả).
- **RLS lưu ý QUAN TRỌNG:** `aa_app_user` (secret `aa-cis/dev/rds-app-user`) bị RLS lọc → query
  raw_tours/published_tours thấy **0 row**. PHẢI dùng **admin secret `aa-cis/dev/rds`** (user
  `aa_cis_admin`, bypass RLS) cho việc đọc platform-scope. DB thật: raw_tours=793, published_tours
  =116, generated_content=180, tour_atoms=8937 (platform).

## Thay đổi Codebase (repo AA-CIS-App) — 3 PR merged main

### Sub A — AA-617 (PR #395, merged `41774c5`+, migration 153)
- `shared/llm_client/call_log.py`: `_normalize_model_provider()` bỏ prefix `satellite-` + suy
  provider; `record_call`/`_with_pool`/`_sync` +3 param `account`/`fallback_used`/`provider`.
- Thread 14 call site: Mechanism A (resp) → `account=resp.satellite_account`,`fallback_used=
  resp.fallback_used` (graph.py generate/nudge, flag_fix_node ×3, judge_node, t8, t9); Mechanism B
  (invoke_claude) → `account=cfg.account_route or "acc3"`,`provider="bedrock-satellite"`,fallback=
  False (tenant_pipeline t5 ×2, acp_produce adapt/generation/faq/research/repair). Judge gpt-4.1 →
  provider tự suy openai, account NULL.
- `admin_llm_ops._TREE_SQL` +account/provider/fallback_count vào SELECT+GROUP BY; `/llm-usage/calls`
  expose thêm.
- Migration 153: `llm_call_log` +account/fallback_used/provider (nullable) + index partial account.
- Test: `test_aa617_llm_account_instrumentation.py` (5) + sửa `test_aa493_stop_reason.py` (bind order).

### Sub B — AA-618 (PR #396, merged, migration 154)
- Migration 154: bảng mới `shared.dfs_call_log` (id/tenant_id/tour_id/endpoint/keyword/location_code/
  cost_usd/cache_hit/fetched_live/keyword_count/meta + 4 index).
- `shared/dfs_client/call_log.py` (module mới): `extract_cost()` đọc field `cost` top-level DFS trả
  (trước bị bỏ); `record_dfs_call`/`_with_pool`/`_sync` mirror llm_client/call_log (fire-and-forget).
- `dataforseo_client.py`: `DataForSEOClient(tenant_id,tour_id)` + `_log_live()` mỗi HTTP method live
  (search_volume/search_volume_bulk/serp_advanced/keywords_for_keywords) log 1 row fetched_live+cost.
- `handler.py process_seo`: log nhánh cache hit (Redis) cache_hit=True cost 0 + truyền tenant/tour
  vào client khi miss.
- `admin_llm_ops`: endpoint mới `GET /admin/dfs-usage` — rollup cost + cache-hit-rate theo
  endpoint+tenant (cho Sub E dùng).
- Test: `test_aa618_dfs_call_log.py` (6).

### Sub C — AA-619 (PR #397, merged `0e48b6a`+`6a02c3c` lint fix, migration 155)
- Migration 155: UPDATE `llm_role_config` t5_atomize sonnet→haiku (idempotent).
- `role_config.py` SAFE_DEFAULTS t5_atomize → haiku (đồng bộ seed).
- `tenant_pipeline.py`: day-fingerprint key theo model config LIVE (`_t5_cfg.model_id`, resolve 1
  lần đầu `_atomize_per_day`) thay hằng `_T5_MODEL_TIER` (BỎ) → đổi model tự invalidate fingerprint,
  hết drift. Bỏ fetch `_t5_cfg` trùng.
- `test_aa508` fingerprint ref dùng `SAFE_DEFAULTS["t5_atomize"].model_id`.

## Thay đổi Hạ tầng
- KHÔNG đụng Terraform/AWS resource. 3 migration (153/154/155) applied lên **Dev DB** qua tunnel
  (admin secret), verified từng cái. Deploy Dev tự chạy sau mỗi merge — cả 3 SUCCESS.

## Bằng chứng verify
- **Sub C A/B đo THẬT** (invoke_claude 2 model trong ECS container `api`, role acc3 trusted,
  read-only KHÔNG ghi tour_atoms): Bhutan H=27/28,S=28/29,32/32 — atom count gần y hệt, parse sạch,
  Haiku place/action grounded không bịa, Sonnet ~4x cost. → chốt hạ Haiku.
- Full `tests/unit/` **1955 passed** (1946 base + 5 AA-617 + 6 AA-618; sửa test_aa493/aa508).
- 3 PR CI 5/5 required pass (Docker/Integration/Lint/Security/Unit); Vercel fail non-required.
  #397 Lint fail lần đầu (1 comment >120 cols) → fix `6a02c3c` → xanh.
- 3 migration verified trên Dev DB (cột/bảng/config đúng + schema_versions).
- Deploy Dev #395/#396/#397 đều success.

## Còn lại (việc đầu phiên sau S188)
1. **Sub G (AA-620)** — tách stage `t2_generate` (config đổi ở admin Settings/LLM Models) + cân
   nhắc Sonnet cho T2 tenant (A1 admin GIỮ Haiku) + thread `tenant_id` qua S1 graph. A/B brand-voice
   trước khi chốt. **Migration 156+**. LƯU Ý: KHÔNG mở PR song song AA-614 (cùng đụng v1_pipeline/
   v1_tours).
2. **Sub D (AA-621)** — batch atomize (mở rộng AA-606 bedrock_batch.py sang t5). Sau khi model chốt
   Haiku (Sub C done rồi). CHẶN G4/G5 cùng.
3. **Sub E (AA-622)** — UI admin "External Spend" (FE) đọc `/admin/llm-usage/tree` (đã có account/
   provider/fallback_count) + `/admin/dfs-usage`. Đây là phần **FE đồng bộ** cho A/B/G. Cross-ref
   AA-615 (khác trọng tâm: AA-615=content gate/severity, Sub E=cost).
4. **G4/G5 (AA-599/600)** rerun 763 tour — chặn bởi Sub C(done)+Sub D. Giờ atomize đã Haiku → rẻ.
5. **AA-613** (redesign social tenant Sub1 BE) — hoãn sau nền; migration **156+**.

## Lưu ý kỹ thuật (phiên sau)
- **RLS: đọc platform-scope PHẢI dùng admin secret `aa-cis/dev/rds` (aa_cis_admin)**, KHÔNG dùng
  `aa-cis/dev/rds-app-user` (RLS lọc → 0 row). Rewrite host → `127.0.0.1:15432` (tunnel).
- **Migration order:** Sub A=153, B=154, C=155. Kế tiếp 156+ (Sub G, AA-613).
- **Chạy Bedrock từ LOCAL KHÔNG được** — `AA3-Bedrock-Invoker` chỉ trust ECS task role
  `aa-cis-dev-ecs-task-role`, KHÔNG trust admin session. → muốn gọi Bedrock thật (A/B đo) phải qua
  `aws ecs execute-command` vào task (container `api`, cluster `aa-cis-dev-cluster`, task id đọc từ
  `list-tasks`). Push script vào /tmp qua base64 rồi chạy foreground trong 1 exec session (detached
  nohup CHẾT khi session exit — SIGHUP). Foreground + flush per-item để thấy tiến độ.
- **Satellite invoke đồng bộ stall nhiều phút với itinerary lớn (13-18k chars)** — latency luồng
  1-request tuần tự, KHÔNG phải model. → củng cố Sub D (batch atomize) cho rerun 763.
- **Shell WSL:** BỎ tham số `cwd`; dùng script file + `cd ... &&` + ghi output ra file rồi read_file.
  execute_bash exit -1 GIẢ. read_file path WSL UNC hay cache stale → đọc lại với offset khác / đổi
  tên file output. Terminal reused hay chạy script CŨ → đổi tên file mỗi lần cho chắc.
- **CI AA-CIS-App:** 5 required (Lint/Security/Unit/Integration/Docker), Vercel KHÔNG required. Lint
  `--max-line-length=120`. `gh pr merge <n> --squash --auto`. Migration apply THỦ CÔNG qua psql
  (không auto trên deploy).
- **Quy tắc Linear (Nghiệp nhắc):** mọi issue mới PHẢI gắn 1 project; tối đa 50 issue/project. Đã
  ghi vào steering session-workflow. Project "CIS Data Reset & Pipeline Rerun (Audit)" hiện ~31
  issue (đủ chỗ). AA-616..622 đã gắn (Nghiệp gắn tay AA-616..622 lúc chưa gắn tự động).

Log local: `docs/sessions/2026-09-18-AA616-LLM-DFS-observability-S187.md`.
