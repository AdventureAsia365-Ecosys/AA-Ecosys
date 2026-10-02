# S208 — AA-714 (judge Luna + brand audit fail-closed + layer judge), AA-713 (atom theo master_status), chạy lại Mongolia, kết nối Atlassian (02/10/2026)

**Tác nhân:** Kiro (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:431` COMPLETED · **Migration mới nhất:** CIS 203

## Trạng thái
- **AA-714 xong (In Progress → đã deploy hết):** chuyển judge/brand audit sang GPT Luna, dứt điểm vấn đề
  "GPT-4.1 → Luna" chị Thư nêu (Jira PR-16). Không stage judge nào còn dùng GPT-4.1 làm model chính.
- **AA-713 xong (In Review):** atom đi theo `master_status` của tour — tour inactive/trashed không còn feed
  segment/ranking/slate. View + recompute, migration 203 applied Dev.
- **Mongolia chạy lại xong:** 17/17 tour lên Master, 0 HITL, 17/17 atom hoá (335 atom). Master Content ~81 tour.
- **Kết nối Atlassian MCP:** đã setup (v2 Streamable HTTP), test đọc Jira OK — từ phiên sau đọc/đăng Jira trực tiếp qua Kiro.
- Jira PR-15 (tiến độ Mongolia) + PR-16 (judge Luna): **Nghiệp đã tự đăng** (nháp Kiro soạn, có ngày 02/10).

## Thay đổi Codebase (AA-CIS-App #541–#546)
| PR | Nội dung |
|---|---|
| #541 | **brand audit fail-closed:** model/schema lỗi → `manual_check` + `BRAND_AUDIT_UNAVAILABLE` (giữ lại review), không còn tự "pass". **UI LLM Models:** mỗi model hiện nơi chạy (`Bedrock acc3` vs `OpenAI API`); mỗi stage hiện route chỉ-đọc (chính → fallback, shadow + %). |
| #542 | Sửa nhãn chuỗi legacy Claude trên UI: `haiku`/`sonnet` = `Bedrock acc2 → acc3 → acc1` (phát hiện lúc kiểm live). |
| #543 | CONTEXT.md: route judge/brand audit hiện tại, brand audit fail-closed, GPT trên Bedrock acc3 vs OpenAI API. |
| #544 | **Layer judge (AA-714):** `score_brand_fit` thêm lớp 2 — model reasoning (Luna, không seed) + điểm sát ngưỡng [6,8] → chấm thêm 2 lần lấy trung vị; model có seed (gpt-4.1) chấm 1 lần. Lớp 1 = 1 lần; lớp 3 = Jev tie-break `a1_brand_fit` sẵn có trong judge_node (shadow tới khi có calib). |
| #545 | **Luna tin cậy cho brand audit:** (C) bỏ `status` khỏi required schema, tự tính bằng `derive_status(codes, publish_ready, model_status)`; (A) gateway `_call_bedrock_converse` retry 1 lần khi Converse trả thiếu key (áp dụng mọi stage Converse). |
| #546 | **AA-713:** migration 203 view `acp_contract.v_active_tour_atoms` (INNER JOIN published_tours master_status='active' + deleted_at NULL + NOT deleted/empty); 4 read A3 (segment_matching, atom_ranking ×2, route_detection) đọc view; `recompute_rankings_and_routes()` chạy nền từ 5 endpoint admin đổi status → evict atom tour inactive khỏi atom_ranking/route (Slate đọc cache đó). |

## Thay đổi Route LLM (DB `shared.llm_role_config`, không deploy, cache 20s)
Tất cả `updated_by=s208-aa714-*`. Rollback SQL trong `.tmp-session/s208_*.py` header.
- `s1_judge`, `t10_judge`, `n7_judge`: shadow gpt-4.1 → **gpt-6-luna** (chính giữ gpt-5.6-luna).
- `s1_brand_audit`: lần đầu thêm fallback [gpt-5.6-luna, gpt-6-luna]; **cuối phiên đổi chính sang gpt-5.6-luna, fallback gpt-6-luna, shadow gpt-6-luna** (Nghiệp chốt — Luna đã tin cậy sau #545 + Mongolia 0 lỗi).
- `t10_judge`: thử đổi chính sang gpt-6-luna rồi **hoàn lại** gpt-5.6-luna (Nghiệp: chưa A/B T10 trên tenant content thì chưa đổi; giữ gpt-6-luna shadow để gom dữ liệu).

## Thay đổi Hạ tầng / dữ liệu (Dev)
- **Migration 203** apply tay trước deploy (view v_active_tour_atoms).
- **Mongolia:** 17 tour thô active → chạy lại (prefetch SEO 1 job + S1 rewrite CONC 3/4 + atomize nền). 17/17 publish, quality 7–9, brand_audit fixed/pass, 335 atom. Chi phí ~ LLM $0.87 (pilot $0.14 + wave $0.73) + DFS prefetch $0.30.
- **photo_sync:** chạy nền 1 job incremental (29d90896) — 3.232 ảnh unchanged, 0 ảnh mới (7 thư mục CON đã sync hết từ S207).

## Bằng chứng verify
- CI 5/5 + Vercel xanh trên #541/#542/#544/#545/#546. ECS rollout COMPLETED từng bước :427 → :428 → :429 → :430 → :431.
- Live `GET /admin/llm-config`: route brand_audit = GPT-5.6 Luna·Bedrock acc3 → GPT-6 Luna, shadow GPT-6 Luna; judge/t10 tương tự. derive_status + converse retry + repeat-median + v_active_tour_atoms đều present trong image.
- Mongolia pilot 3 tour: brand_fit toàn ≥8 (ngoài band → không lặp), 0 HITL. Wave 14 tour: brand_fit có 8 lần =7.0 (repeat-median kích đúng), 0 HITL. Judge chạy gpt-5.6-luna (primary) + gpt-6-luna (shadow, 0 lỗi). brand_audit 0 lỗi schema.
- v_active_tour_atoms resolve 1513 rows = tổng atom non-deleted (0 bị loại vì chưa tour nào inactive).
- Atlassian MCP v2: `getAccessibleAtlassianResources` trả site adventure-asia (Jira+Confluence read-write); đọc PR-16 OK.
- Unit suite 2.3xx pass mỗi PR; flake8 + next build sạch.

## Còn lại
- **China** — nước chạy lại tiếp theo (rồi Thái Lan, Bhutan [chờ chị Thư 2 NCC], Lào, Nepal, Sri Lanka, Ấn Độ).
- **t10_judge**: cần A/B trên tenant content thật (gpt-6-luna shadow đang gom) rồi mới quyết đổi chính.
- **AA-686** (Backlog): màn hình xem route theo thời gian / lịch sử đổi route / A/B report (phần UI còn mở của AA-714 gộp vào đây).
- **AA-651**: đưa S1 rewrite (`run-tour-async`) từ task in-process API sang job runner → hiện trên trang Jobs + bền qua deploy. Nghiệp: làm khi tới AA-651.
- **AA-713**: chưa chạy cycle inactivate-tour-thật (đụng Master Content thật) — chạy khi Nghiệp cần.
- **Root PR #22** (steering + workspace file): chờ Nghiệp merge tay.
- **Atlassian MCP**: endpoint đã ở v2 (`/v2/mcp`); nhớ dùng ADF mention cho `@thule` khi đăng.

## Lưu ý kỹ thuật cho phiên sau
- **S1 rewrite KHÔNG hiện trên trang Jobs** (nó là task in-process `shared.pipeline_jobs`, không phải `shared.job`). Trang Jobs chỉ có 6 kind job runner. Xem S1 qua trang Rewrite hoặc `GET /admin/jobs/{id}`. Khắc phục gốc = AA-651.
- **Secret `aa-cis/dev/rds` là connection string THẲNG (không JSON)** — dùng trực tiếp làm DSN khi apply migration tay.
- **Judge Luna không nhận temperature/seed** (reasoning model) → ổn định bằng repeat-median (#544), không ép được như gpt-4.1.
- **Luna qua Bedrock Converse không ép schema** → có thể thiếu key; đã xử lý bằng derive_status + gateway retry (#545).
- **GG API key không cần đổi** (steering đã ghi, Nghiệp chốt 02/10).
- Runner phiên: `.tmp-session/s208_run.sh` (chạy script trong container, output qua S3 vì ECS exec hay cắt). Wave: `.tmp-session/s208_wave.mjs` (COUNTRY/CONC/NAMES/PREFETCH).
- Log local: file này.
