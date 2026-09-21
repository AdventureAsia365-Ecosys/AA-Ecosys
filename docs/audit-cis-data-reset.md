# CIS Data Reset & Pipeline Rerun — Audit plan (S182)

> Linear epic: **AA-594** (project *CIS Data Reset & Pipeline Rerun (Audit)*).
> Sub-issues: G0 AA-595 · G1 AA-596 · G2 AA-597 · G3 AA-598 · G4 AA-599 · G5 AA-600 · G6 AA-601 · cleanup AA-602.
>
> ⚠️ **RDS acc2 `005097885195` dùng CHUNG production** (CIS + TripPlanner). Xóa nhầm = mất data thật của mọi tenant, không hoàn tác trừ khi có backup. Đọc kỹ trước khi chạy bất cứ DELETE nào.

## Mục tiêu (Ms.Thư)
Raw tours (~700+) đã upload từ Excel. Giữ raw thô, reset toàn bộ dữ liệu **dẫn xuất** (master + tenant/social), chạy lại pipeline từ admin (S1 → master content → atomize → segment/score/route → social), verify S1 + social content admin + UI admin (thật/mock).

## Pipeline (verify từ code AA-CIS-App)

- **A0 Upload** → `silver_aa_internal.raw_tours` (`pipeline_status='ingested'`).
- **A1 = S1 rewrite** (`api/routers/admin_pipeline.py::_execute_run_tour`, LLM Bedrock + SEO) → `silver_aa_internal.generated_content` + `quality_scores`; fail → `review_queue` (status hitl).
- **A2 QA gate** → review_queue (HITL).
- **A3 Master pool** (`services/export/handler.py::process_export`, chỉ nhận `generated_content.status='approved'`) → `gold_aa_internal.published_tours`, set `raw_tours.pipeline_status='published'`.
- **A3→Atomize** (fire-and-forget, `_run_a3_atomize_background`, `owner_scope='platform'`) → `acp_contract.tour_atoms`; rồi `recompute_segment_score_route` → `atom_segment`/`atom_ranking`/`route`/`hub` (platform-wide sau AA-545).
- **T-series** (tenant): rewrite → `gold.tenant_tour_versions`; planning T7; angle gate T8 → `angle_gate_request/option`; write T9 → `content_piece`; publish T11 → `publish_log`. State: `tenant_atom_state`, Slate `subject`.
- Master content luôn dùng sentinel tenant `00000000-0000-0000-0000-000000000001`.

## Bảng GIỮ (raw + config + cache — KHÔNG xóa)
- `silver_aa_internal.raw_tours` — **chỉ reset `pipeline_status`→`ingested`**, giữ nguyên row (nhiều FK trỏ về `tour_id`).
- `silver_aa_internal.raw_sources`
- `shared.tenants`, `shared.tenant_brand_rules`, `shared.tenant_config`, `shared.pipeline_lessons`, `shared.tenant_integrations`
- `acp_contract.search_demand`, `acp_contract.segment_research_log` — cache DataForSEO cross-tenant (182 ngày), **giữ để không tốn tiền research lại**
- `acp_shared.facts`
- `shared.destinations` — cache geocode Mapbox (giữ để đỡ tốn API; nhưng embeddings ở `tripplanner.itinerary_components` phải rebuild)
- `shared.pipeline_runs` — batch registry (giữ, chỉ reset status nếu cần)

## Bảng XÓA (dẫn xuất) — THỨ TỰ con → cha
Đa số FK là plain `REFERENCES` (không CASCADE) → phải xóa con trước cha thủ công.

```
1.  acp_shared.publish_log
2.  acp_shared.content_piece
3.  acp_shared.subject
4.  acp_shared.angle_gate_option  →  acp_shared.angle_gate_request
5.  acp_contract.route            →  acp_contract.hub
6.  acp_contract.atom_ranking
7.  acp_contract.atom_segment_member, atom_segment_alias  →  acp_contract.atom_segment
8.  acp_contract.atomize_day_fingerprint,  acp_contract.tour_atoms
9.  acp_shared.tenant_atom_state
10. gold.tenant_tour_versions            (nếu reset cả tenant rewrite)
11. gold_aa_internal.published_tours
12. silver_aa_internal.quality_scores, review_queue, seo_context
13. silver_aa_internal.generated_content
14. UPDATE silver_aa_internal.raw_tours SET pipeline_status='ingested'   (KHÔNG xóa)
```

## TripPlanner (dẫn xuất bậc-2)
`shared.destinations` + `tripplanner.itinerary_components` sinh từ `published_tours` + `tour_atoms` qua `apps/AA-TripPlanner-Web/backend/extraction/run.py`. **Sau khi CIS rerun xong (published_tours + tour_atoms tái tạo, master_status='active'), PHẢI chạy lại** `python -m backend.extraction.run` (hoặc `run_deterministic.py`, có sẵn TRUNCATE) để rebuild — nếu không TripPlanner trỏ tour_id/atom cũ đã xóa (dangling).

## UI admin — real vs mock
Xác nhận: **mọi trang admin fetch dữ liệu THẬT**, không trang nào dùng mock. Điểm dễ nhầm: `master-content` có label `Live/Mock` = cờ `dataforseo_used` thật của từng tour (không phải trang mock). Trang cần verify sau rerun: `s1-rewrite`, `pipeline/s1`, `review`, `master-content`, `atom-curation`, `platform-stats`, `tenant-activity`, `dashboard`.

## Quy trình 8 bước (Linear G0-G6 + cleanup)
1. **G0 (AA-595)** — RDS snapshot + dựng bastion + tunnel + pg_dump theo schema về `docs/backups/YYYY-MM-DD/`. Chặn mọi việc sau.
2. **G1 (AA-596)** — điều tra read-only: đếm row mọi bảng, snapshot "before".
3. **G2 (AA-597)** — viết script DELETE (transaction) + dry-run count, **Nghiệp duyệt**.
4. **G3 (AA-598)** — chạy reset sau backup+duyệt.
5. **G4 (AA-599)** — rerun S1 → master content, verify.
6. **G5 (AA-600)** — atomize + segment/score/route + social admin; rebuild TripPlanner extraction.
7. **G6 (AA-601)** — verify UI admin thật/mock.
8. **cleanup (AA-602)** — ⚠️ **terminate bastion** + revert SG.

## Nguyên tắc an toàn
- Không DELETE nào chạy trước G0 (backup) + G2 (duyệt).
- Mọi DELETE bọc `BEGIN; ... ; -- kiểm tra COUNT rồi COMMIT/ROLLBACK`.
- RDS snapshot là net cuối; pg_dump theo schema là backup thao tác được.
- Terminate bastion sau audit (AA-602) — đừng để chạy tốn phí / mở bề mặt mạng.
