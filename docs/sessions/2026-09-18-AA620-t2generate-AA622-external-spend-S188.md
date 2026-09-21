# S188 — AA-620 tách t2_generate + chốt Sonnet (A/B thật) + AA-622 trang admin "External Spend" (Kiro, 2026-09-18)

Tác nhân: **Kiro**. Tiếp nối S187. Epic AA-616 (giám sát chi phí LLM/DFS) — làm 2 sub G + E.

## Trạng thái
Làm xong **Sub G (AA-620)** và **Sub E (AA-622)** của epic AA-616. Cả hai Done trên Linear, verify
thật trên domain Dev. Tách issue mới **AA-623** (Sub F — Cost Explorer, Low). **Hoãn Sub D (AA-621
batch atomize)** sang phiên sau vì rủi ro IAM/verify chưa đủ. Fix 1 bug Vercel build (MarketplaceTab
JSX hỏng chặn deploy frontend ~21h).

- **AA-620 (Done):** tách stage `t2_generate` riêng cho writer tenant (T2), thread `tenant_id` qua
  S1 graph; chạy A/B thật Haiku vs Sonnet trên brand WanderLux → **chốt t2_generate = Sonnet**
  (A1 admin giữ Haiku). Admin vẫn gạt tay đổi model qua Settings > LLM Models.
- **AA-622 (Done):** trang admin "External Spend" (giữ path `/admin/llm-usage`) — 3 tab (LLM / DFS /
  Trends) + filter tenant + account là 2 chiều lọc/nhóm hạng nhất + fallback drill-down modal +
  Settings có group "t2" cho t2_generate.

## Sub G — AA-620 (tách t2_generate + A/B chốt Sonnet)

### Thiết kế chốt
- Thêm 2 field vào `ContentState`: `tenant_id`, `generate_stage` (thay vì dùng `stage_prefix`).
- CHỈ tách stage `generate` (→ `t2_generate` khi tenant rewrite). KHÔNG tách `s1_flag_fix` /
  `s1_itinerary_nudge` (Haiku đủ cho cả A1 admin lẫn T2 tenant — ghi chú để không quên).
- A1 admin log `tenant_id` = NULL (không dùng sentinel).

### A/B model T2 (đo THẬT trên ECS)
- Viết script `ab_t2_brand_voice.py`, push base64 vào container `api` (task role AA3-Bedrock-Invoker
  chỉ trust ECS → không invoke từ local được). Chạy A/B Haiku vs Sonnet 2 tour (Thailand + Sri Lanka),
  brand WanderLux thật (system_prompt luxury).
- Kết quả: Sonnet đắt ~11-13x Haiku ($0.047-0.054 vs $0.0041-0.0043) NHƯNG bám style_guide luxury rõ
  hơn + seo_meta đúng band. → **Chốt t2_generate = Sonnet** (writer/claude/sonnet/acc3).

### Files sửa (repo AA-CIS-App)
- `services/content_generation/graph.py`: ContentState +`tenant_id`/`generate_stage`; `generate_node`
  dùng `gen_stage` = `generate_stage or "s1_generate"`.
- `services/content_generation/nodes/flag_fix_node.py`: thread `tenant_id`.
- `api/routers/v1_pipeline.py`: `_rewrite_tour` +param tenant_id/generate_stage.
- `api/routers/v1_tours.py`: `trigger_rewrite` truyền `generate_stage="t2_generate"` (nhánh tenant).
- `services/acp_produce/tenant_pipeline.py`: `run_t3_qa_gate` +tenant_id.
- `shared/llm_client/role_config.py`: SAFE_DEFAULTS +`t2_generate`.
- Migration `api/migrations/156_t2_generate_stage.sql`: INSERT `t2_generate` (writer/claude/haiku/acc3)
  vào `shared.llm_role_config`; sau đó UPDATE model_id → sonnet (updated_by=`nghiep-ab-decision-aa620`).

### PR
- **#398** (AA-620) merged.

## Sub E — AA-622 (trang admin "External Spend")

### Thiết kế chốt (theo feedback Nghiệp)
- Giữ path `/admin/llm-usage` (không tạo trang mới → tránh middleware allowlist gotcha). Đổi title
  "External Spend"; sidebar label "LLM Usage" → "External Spend" (icon Gauge → Wallet).
- **tenant + account là 2 chiều lọc/nhóm hạng nhất** (redesign sau feedback): filter bar toàn cục
  (Tenant dropdown + Account chips), toggle group-by (Tenant→Account→Model / Account→Model→Stage),
  bảng "Spend by tenant" mỗi tab.
- 3 tab: LLM / DFS (by country) / Trends (chart theo ngày + tổng token). Model mix + cost/1K.
- **Fallback drill-down:** click ô fallback% (stat card hoặc row tenant) → modal liệt kê call thật
  fell back (acc3→acc1/GPT) cho tenant+range.

### Files sửa
- BE `api/routers/admin_llm_ops.py`: `_TREE_SQL` +tokens_in_total/tokens_out_total; endpoint
  `GET /admin/dfs-usage/by-country` (`_DFS_LOCATION_NAMES` ~20 code); `GET /admin/spend/daily`
  (UNION llm+dfs date_trunc); `_DFS_TREE_SQL` +tenant_id; `/admin/llm-usage/calls`
  +fallback_used(bool)/account/days filter.
- FE `frontend/app/admin/llm-usage/page.tsx`: viết lại (3 tab → redesign tenant/account filter +
  FallbackModal).
- FE `frontend/app/admin/settings/page.tsx`: STAGE_GROUPS +group "t2" "T2 tenant rewrite writer".
- FE `frontend/app/admin/_components/AdminSidebar.tsx`: label + icon.

### Bug Vercel build (fix trong phiên)
- `frontend/app/(tenant)/portal/_components/MarketplaceTab.tsx:117` — bad merge: dup "Atoms" Metric
  + ref `starred_atom_count` (đã gỡ AA-609) + "Price" Metric mất tag mở → Turbopack parse fail →
  **Vercel build fail ~21h**. Fixed thành 3 Metric Atoms/Price/Runway.
- `frontend/app/admin/llm-usage/page.tsx`: Tooltip formatter `(v)=>fmtUsd(Number(v)||0)` (recharts
  type ValueType|undefined).

### PR
- **#399** (External Spend 3 tab), **#400** (sidebar + settings — LƯU Ý: settings fix bị MẤT khỏi
  squash lần đầu, phải làm lại ở #402), **#401** (fix MarketplaceTab + Tooltip), **#402** (redesign
  tenant/account + settings t2 lại), **#403** (fallback drill-down — merge cuối phiên).

## Thay đổi Hạ tầng
- KHÔNG terraform. Chỉ 1 migration DB `156_t2_generate_stage.sql` applied Dev DB (qua SSM tunnel →
  ECS task, secret `aa-cis/dev/rds` us-west-1 dạng URL string). Sau đó UPDATE model_id=sonnet.
- Bastion đã terminate từ AA-602 (S186) → tunnel dùng SSM port-forward vào ECS task container `api`.

## Bằng chứng verify
- `flake8 api/ services/ shared/` (đúng lệnh CI, max-line=120) EXIT 0 sạch trên PR branch sau fix.
- Full `tests/unit/` **1959 passed** (env JWT_SECRET=x AWS_*=dummy AWS_EC2_METADATA_DISABLED=true
  OPENAI_API_KEY=dummy `.venv/bin/python -m pytest`).
- FE: **`next build` đầy đủ** thành công (bắt type error mà tsc --noEmit + eslint bỏ sót).
- Domain Dev: `/admin/llm-config` trả t2_generate=sonnet/acc3 (17 stages); `/admin/llm-usage/tree`
  trả tenant_id/tenant_label/tokens_in_total/account/fallback_count; `/admin/spend/daily` +
  `/admin/dfs-usage/by-country` HTTP 200.
- Vercel "Deploy Frontend to Vercel" SUCCESS trên f302d75, 88f5476.
- PR #403: CI Lint fail lần đầu do E501 (dòng decorator `/llm-usage/calls` dài 136>120 ở
  `admin_llm_ops.py:173`) — fix wrap decorator (commit `f19f697`), Lint SUCCESS. (Commit `8f0e2c6`
  bỏ import `TrendingUp` KHÔNG phải nguyên nhân — Lint CI chỉ chạy flake8 Python, không lint FE TS.)

## Còn lại (việc chưa xong)
- **Sub D (AA-621) batch atomize** — HOÃN sang phiên sau (S189). Việc lớn, rủi ro cao (IAM acc3 batch
  chưa verify; AA-606 chưa chạy batch job thật lần nào). CHẶN G4/G5.
- **AA-623 (Sub F, Cost Explorer)** — Low, tách riêng (cần IAM ce:GetCostAndUsage + terraform).
- G4/G5 (AA-599/600) rerun 763 tour; AA-613/614/615 (redesign social tenant); AA-610 (rank-sum).

## Lưu ý kỹ thuật (cho phiên sau)
- **CI Lint job chỉ chạy flake8 trên Python** (`api/ services/ shared/`), KHÔNG lint frontend TS.
  Khi Lint fail → chạy flake8 đúng lệnh CI để tìm; F401 (unused import) nằm trong ignore-list nên
  KHÔNG phải nguyên nhân — thường là **E501 line too long** (max 120). PR run CI test trên merge-commit
  SHA (không phải head SHA) → đọc log theo job.
- flake8 local: venv shebang stale + PEP668 chặn pip → `pip install --break-system-packages flake8
  flake8-bugbear` (đã có ở `~/.local/bin/flake8`). Chạy trên **PR branch** (checkout) mới thấy lỗi
  của branch, không phải main.
- **Verify FE PHẢI chạy `next build` đầy đủ** (bắt type error mà tsc --noEmit + eslint bỏ sót) + PHẢI
  kiểm **Vercel deploy status** (GitHub "Deploy Dev" chỉ deploy ECS backend, KHÔNG phải frontend).
  Sau merge PR phải `git show origin/main:<file>` xác nhận commit thật vào main (settings fix từng bị
  mất khỏi squash #400).
- Shell WSL lag/nuốt lệnh: ghi output ra file workspace rồi read_file (path workspace-relative);
  đổi tên file mỗi lần; `control_bash_process` + `tail -f /dev/null` cho lệnh cần giữ output; gh api
  network hay treo. CI merge `gh pr merge <n> --squash --auto`.
- **Sub D (AA-621) BƯỚC 0 BẮT BUỘC** phiên sau: verify batch job THẬT chạy trên acc3 trước khi build
  `atomize_batch.py` (mâu thuẫn IAM: bedrock_batch.py nói acc3 có Batch perm, bedrock_satellite.py nói
  acc3 chỉ InvokeModel; AA-606 chưa chạy batch job thật lần nào). recordId phải đổi scheme
  `<tour_id>#<day>` (per-day collision). Tách phần persist atoms trong `_atomize_per_day` thành hàm
  dùng chung.

Log local này: `docs/sessions/2026-09-18-AA620-t2generate-AA622-external-spend-S188.md`.
