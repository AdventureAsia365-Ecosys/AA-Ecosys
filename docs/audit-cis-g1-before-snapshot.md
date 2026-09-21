# G1 — CIS DB "before" snapshot (S183, 2026-09-16)

Read-only, qua SSM tunnel (localhost:15432) tới aa-cis-dev-db (acc2, postgres 15.17). Linear AA-596.

## Row counts — mọi bảng 6 schema

```
       schema       |               tbl                | rows  
--------------------+----------------------------------+-------
 acp_contract       | atom_decompose_jobs              |    87
 acp_contract       | atom_ranking                     | 11202
 acp_contract       | atom_segment                     |  1485
 acp_contract       | atom_segment_alias               |    35
 acp_contract       | atom_segment_member              |  2999
 acp_contract       | atomize_day_fingerprint          |   324
 acp_contract       | hub                              |     6
 acp_contract       | route                            |   183
 acp_contract       | route_pick                       |     0
 acp_contract       | s1_from_atom_runs                |     2
 acp_contract       | search_demand                    |   480
 acp_contract       | segment_research_log             |   132
 acp_contract       | tour_atoms                       |  3354
 acp_shared         | acp_output_rules                 |     0
 acp_shared         | acp_quota_ledger                 |     1
 acp_shared         | acp_v2_runs                      |    14
 acp_shared         | acp_v2_slots                     |    47
 acp_shared         | angle_gate_option                |    72
 acp_shared         | angle_gate_request               |    42
 acp_shared         | audit_log                        |   127
 acp_shared         | competitor_index_cache           |     4
 acp_shared         | content_metric_snapshot          |     0
 acp_shared         | content_piece                    |    18
 acp_shared         | facts                            |     2
 acp_shared         | marketplace_portfolios           |    11
 acp_shared         | publish_log                      |     0
 acp_shared         | quarter_plan                     |     5
 acp_shared         | quarter_plan_version             |    15
 acp_shared         | subject                          |   435
 acp_shared         | tenant_atom_state                |    18
 acp_shared         | tenant_config                    |     1
 acp_shared         | unknown_ledger                   |    35
 acp_shared         | year_plan                        |     1
 gold_aa_internal   | content_exports                  |     0
 gold_aa_internal   | published_tours                  |    74
 gold_aa_internal   | tenant_tour_versions             |    24
 gold_aa_internal   | webhook_deliveries               |     0
 shared             | acp_runs                         |     0
 shared             | admin_users                      |     4
 shared             | destinations                     |   379
 shared             | llm_call_log                     |   741
 shared             | llm_role_config                  |    16
 shared             | membership_plans                 |     5
 shared             | notifications                    |    39
 shared             | pipeline_jobs                    |    46
 shared             | pipeline_lessons                 |     0
 shared             | pipeline_runs                    |    38
 shared             | prompt_eval_runs                 |     3
 shared             | schema_versions                  |   129
 shared             | tenant_api_usage                 | 18050
 shared             | tenant_brand_rule_versions       |     0
 shared             | tenant_brand_rules               |     5
 shared             | tenant_brand_rules_deleted_aa404 |     6
 shared             | tenant_export_config             |     3
 shared             | tenant_integrations              |     0
 shared             | tenant_rewrite_usage             |     1
 shared             | tenant_seo_config                |     3
 shared             | tenants                          |     4
 silver_aa_internal | generated_content                |   238
 silver_aa_internal | quality_scores                   |   216
 silver_aa_internal | raw_sources                      |    37
 silver_aa_internal | raw_tours                        |   793
 silver_aa_internal | review_queue                     |    52
 silver_aa_internal | seo_context                      |    55
 silver_aa_internal | upload_staging                   |     4
 tripplanner        | customers                        |     2
 tripplanner        | itinerary_components             |  1081
 tripplanner        | sessions                         |    21
 tripplanner        | trip_drafts                      |    21
 tripplanner        | trip_events                      |    52
(70 rows)

EXIT:0
```

## Phân bố trạng thái + tenant

```
=== pipeline_status ===
 pipeline_status | count 
-----------------+-------
 ingested        |   717
 published       |    75
 hitl_rejected   |     1
(3 rows)

=== tenants ===
              tenant_id               |          name           
--------------------------------------+-------------------------
 00000000-0000-0000-0000-000000000001 | Adventure Asia Internal
 1bae2159-671b-4f35-a782-e96ea4cbdd4a | test 1
 a1b2c3d4-0001-4000-8000-000000000001 | WanderLux Travel
 a1b2c3d4-0002-4000-8000-000000000002 | ExploreAsia Co.
(4 rows)

=== content_piece by tenant ===
              tenant_id               | count 
--------------------------------------+-------
 a1b2c3d4-0001-4000-8000-000000000001 |    18
(1 row)

=== subject by tenant ===
              tenant_id               | count 
--------------------------------------+-------
 a1b2c3d4-0001-4000-8000-000000000001 |   435
(1 row)

=== generated_content status ===
  status  | count 
----------+-------
 approved |   194
 hitl     |    42
 rejected |     2
(3 rows)

=== published_tours master_status ===
 master_status | count 
---------------+-------
 inactive      |    39
 active        |    31
 trashed       |     4
(3 rows)

EXIT:0
```

## Nhận xét ranh giới (cho G2)

**Khớp bản đồ (docs/audit-cis-data-reset.md):** mọi bảng GIỮ + XÓA trong bản đồ đều tồn tại và có row count ở trên.

**Chênh lệch cần lưu:**
- `pipeline_status='published'` = **75** nhưng `gold_aa_internal.published_tours` = **74**. Lệch 1. Khả năng: 1 raw_tour có pipeline_status='published' nhưng bản published tương ứng đã bị trash/xoá, hoặc 1 published_tours bị trashed (master_status='trashed'=4). G2 cần soi kỹ khi viết UPDATE reset pipeline_status.
- `published_tours.master_status`: active=31, inactive=39, trashed=4 (tổng 74).

**Tenant: KHÔNG có tenant B2B thật.** 4 tenant = sentinel Internal + `test 1` (rỗng) + WanderLux Travel + ExploreAsia Co. CHỈ WanderLux (`a1b2c3d4-0001...`) có dữ liệu dẫn xuất tenant thật (18 content_piece + 435 subject). ExploreAsia + test1 rỗng. → G3 reset dẫn xuất tenant an toàn, không cần chừa tenant nào (khớp ghi chú S182).

**Bảng NGOÀI bản đồ — G2 phải phân loại GIỮ/XÓA trước khi viết script:**
- `acp_shared`: `acp_v2_runs`(14), `acp_v2_slots`(47), `quarter_plan`(5), `quarter_plan_version`(15), `year_plan`(1), `marketplace_portfolios`(11), `content_metric_snapshot`(0), `acp_output_rules`(0), `acp_quota_ledger`(1), `unknown_ledger`(35), `competitor_index_cache`(4) — nhiều bảng ACPv2/plan cũ (tham chiếu S177/S179 chuỗi dọn route cũ), cần xác nhận sống/chết + có phải dẫn xuất không.
- `acp_contract`: `atom_decompose_jobs`(87), `s1_from_atom_runs`(2), `route_pick`(0) — job/run log của atomize, khả năng dẫn xuất (xóa) nhưng cần xác nhận.
- `silver_aa_internal`: `upload_staging`(4) — staging upload Excel, khả năng giữ (nguồn) hay dọn.
- `shared`: `tenant_brand_rules_deleted_aa404`(6) — bảng backup cũ (AA-404), giữ nguyên/bỏ qua. `pipeline_jobs`(46), `pipeline_runs`(38), `prompt_eval_runs`(3), `llm_call_log`(741), `tenant_api_usage`(18050), `notifications`(39) — log/registry, cân nhắc giữ (lịch sử vận hành) hay reset.
- `gold_aa_internal`: `content_exports`(0), `webhook_deliveries`(0) — rỗng, dẫn xuất publish.

→ **G2 (AA-597)**: chốt danh sách + thứ tự con→cha cho các bảng ngoài bản đồ này, rồi viết script DELETE để Nghiệp duyệt.
