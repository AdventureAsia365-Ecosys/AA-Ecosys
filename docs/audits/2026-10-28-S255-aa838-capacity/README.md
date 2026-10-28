---
id: OPS-08-2026-10
title: Capacity review 2026-10 (first monthly C8 review)
description: "Rà soát dung lượng lần đầu của RDS dùng chung và 6 service ECS (30 ngày tới 28/10/2026) — headroom, trigger C3, ngân sách kết nối C2.2, SLI C1.2 từ probe, rủi ro, danh sách quyết định chờ Nghiệp duyệt, nhịp tuần/tháng/quý."
type: report
status: active
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-partner, aa-cis-infra]
last_reviewed: 2026-10-28
review_every_days: 30
related: [OPS-08, FIN-02, AA-838, AA-896, AA-824, AA-825, AA-832, AA-859, AA-879]
---

# Rà soát dung lượng 2026-10 (lần đầu, data standards C8)

Ngày: 28/10/2026 (S255). Tác nhân: Claude Code (lane AA-838, chỉ đọc). Chi phí: ≈ 0 USD (vài lệnh CloudWatch
`GetMetricData` + Performance Insights API, trong free tier).
Cửa sổ: **28/09 06:00 → 28/10 06:00 UTC (30 ngày)**. RDS đổi `db.t3.micro` → `db.t4g.small` ngày 15/10, nên mọi trigger
C3 của instance được chấm trên **16–28/10** (301 giờ sau đổi); số trước đó chỉ để so sánh.
Lần sau: phiên đầu tiên của tháng 12/2026 (C8a), hoặc sớm hơn nếu một wave làm một ledger tăng gấp đôi.

Không có account ID, ARN, resource ID hay giá trị dòng nào trong trang này. Số liệu DB lấy từ probe chỉ đọc
`scripts/capacity_probe.py` do phiên điều phối chạy qua ECS exec (login `cis_app`) lúc **28/10 06:53 UTC**; output thô
(332 dòng `PROBE`, không có bí mật, DSN hay giá trị dòng) ở [`data/probe-2026-10-28.txt`](data/probe-2026-10-28.txt).
`pg_stat_statements` tích luỹ từ **07/10 16:35 UTC** (lần reset gần nhất), tức ~3 tuần. Vì `cis_app` không có
`pg_read_all_stats`, câu lệnh của các role khác có số đo nhưng **không có text** — các SLI của TripPlanner / Booking
dưới đây được chấm theo role, không theo câu.

## 1. Kết luận ngắn

- **Instance còn rất rộng.** CPU trung bình 4,7 %, chưa giờ nào vượt baseline 20 %; tải DB (PI, 7 ngày) trung bình
  0,02 phiên hoạt động, đỉnh 0,29 trên 2 vCPU; kết nối đỉnh 30 / 181 (16,6 %), p95 12. Bộ nhớ trống sau đổi:
  thấp nhất 257 MB (1 giờ duy nhất), trung bình 543 MB. **Không trigger resize nào bắn** → giữ `db.t4g.small`.
- **Đĩa:** dùng ≈ 4,5 GB / 20 GB cấp (max autoscale 100 GB); tăng 0,05 GB/ngày (30 ngày), 0,09 GB/ngày (7 ngày gần
  nhất, do wave S1). Alarm `FreeStorageSpace < 50 %` (10 GB trống) sẽ kêu khoảng **cuối tháng 12** nếu giữ nhịp 7 ngày.
- **Retention CIS đã có (AA-825), nhưng chưa xoá gì và lịch nhiều khả năng còn DRY RUN** (chưa xác nhận trực tiếp, D3a). Năm job kind `retention_*` chạy mỗi đêm
  (12–14 lần / 30 ngày, 0 lỗi). Chưa dòng nào quá cửa sổ: `llm_call_log` cũ nhất 17/09 (180 ngày → 16/03/2027),
  `tenant_api_usage` 16/09 (90 ngày → **15/12/2026**), `decision_log` 29/09 (180 ngày → 28/03/2027). Lần chạy thật duy nhất là
  bản chứng minh `manual_override` S239 (200 dòng/bảng), không tính là "live run đã duyệt" theo DM-7.2, nên lịch sẽ chỉ
  đếm (không xoá) cho tới khi Nghiệp duyệt một live run thủ công (D3). Hệ quả: `decision_log` (434k, 444 MB) và `llm_call_log`
  (386k, 203 MB) sẽ **vượt 1 M dòng khoảng 25/11–30/12/2026** và ổn định ở ~2–3,6 M / ~1,7–3,1 M dòng (≈ 3–5 GB cộng
  lại) khi cửa sổ 180 ngày đầy.
- **Đọc catalog của TripPlanner chậm (đo được lần đầu):** câu nặng nhất của role `tripplanner` (4 124 lần gọi, 26 %
  tổng thời gian chạy SQL của cả instance; cả role 33 %) mean **335 ms**, p95 ≈ 2,5 s, max 7,8 s, có ghi temp. SLI browse < 300 ms
  **trượt**; trigger C3 "materialized catalog read model" gần chắc bắn — text câu lệnh cần chạy probe qua `run-script`
  để xác nhận, và theo C3b phải thử sửa query/index trước (D12).
- **Ngân sách kết nối C2.2 trên giấy vẫn vượt:** worst case 168 / trần 135 (`cis_app` 100 / limit 90), đang được chấp
  nhận tới **15/12/2026**. Đo thật đỉnh 30. Cần quyết trước 15/12: thu pool `cis-api` 10 → 5 (đưa tổng về 133).
- **Lỗ hổng giám sát nhỏ:** role `crm_app` (limit 6) **không có alarm `RoleConnectionLimitPct`** dù C4.1 đòi mỗi role
  có limit một alarm; và đã chạm 83 % (5/6) một lần ngày 24/10.

## 2. Chín mục C8b

### (1) CloudWatch RDS `aa-cis-dev-db` — 30 ngày

Instance: `db.t4g.small` (2 vCPU, 2 GiB), PostgreSQL 15.17, gp3 20 GB (3000 IOPS / 125 MB/s), `max_allocated_storage`
100 GB, Single-AZ, backup 7 ngày, Performance Insights bật (giữ 7 ngày, miễn phí).

| Chỉ số | 30 ngày | Sau đổi (16–28/10) | Ngưỡng / ghi chú |
|---|---|---|---|
| CPU (trung bình theo giờ) | TB 4,7 %, p95 6,5 %, max 12,0 % | TB 4,8 %, p95 6,3 %, max 10,4 % | baseline T 20 %: **0 / 720 giờ** vượt |
| CPU (đỉnh trong giờ) | p95 26 %, max 79,6 % (trước đổi) | p95 28 %, max 54 %; 4 giờ > 50 % | alarm > 80 % / 15′ |
| CPU p95 cả cửa sổ (theo phút) | 7,0 % | — | |
| `CPUSurplusCreditsCharged` | **0** | 0 | trigger > ~10 USD/tháng |
| `CPUCreditBalance` thấp nhất | — | 158 (max 576) | không cạn |
| `FreeableMemory` (min theo giờ) | — | min **257 MB** (17/10, 1 giờ), TB 543, p95 622 MB; 64/301 giờ < 500 MB | alarm < 200 MiB / 10′; trigger < 300 MB > 1 h/ngày × 3 ngày/tuần |
| `FreeableMemory` trước đổi (t3.micro) | < 300 MB gần như cả ngày 28/09–15/10; 359 giờ < 100 MB | — | lý do của việc đổi instance 15/10 |
| `SwapUsage` max | 271 MB (trước đổi) | 48 MB, TB 15 MB | |
| `DatabaseConnections` | max **30** (25/10), p95 cả cửa sổ **12,0**, p99 16,9; max ngày 3–30 | max 30 | `max_connections` 181 → 16,6 % đỉnh, 6,6 % p95; alarm > 108 |
| Đĩa trống (`FreeStorageSpace`) | 16,99 → 15,47 GB (min 15,32) | — | dùng ≈ 4,5 GB (gồm WAL, log, catalog); alarm < 10 GB |
| Tăng đĩa | 0,048 GB/ngày (30 ngày) | 0,091 GB/ngày (7 ngày) | trigger > 1 GB/ngày |
| ReadIOPS | TB 4,7; p95 cả cửa sổ 12,6; đỉnh 1 phút 1171 | đỉnh 277 | baseline gp3 3000 |
| WriteIOPS | TB 4,5; p95 13,6; đỉnh 355 | | |
| ReadLatency | TB 0,5 ms, p95 1,4 ms, max 16 ms | max 10 ms | alarm > 20 ms / 15′ |
| WriteLatency | TB 0,8 ms, p95 3,1 ms, max 62 ms | max 41 ms (1 giờ) | alarm > 20 ms / 15′ (trung bình) |
| `DiskQueueDepth` max | 2,6 | | alarm > 10 |
| `MaximumUsedTransactionIDs` | 2,5 triệu | | alarm 1 tỷ |

Performance Insights (21–28/10, `db.load.avg`): trung bình **0,020** phiên hoạt động, p95 0,10, p99 0,18, đỉnh 0,29
(27/10 03:30 UTC). Theo loại chờ: CPU 64 %, `Client:ClientRead` 12 %, IO 11 %, `Lock:advisory` 2 %. Theo user:
`cis_app` ≈ 60 % tải, rồi `aa_cis_admin` (DB Migrate / run-script), `aa_app_user`, `tripplanner`, `crm_app`,
`booking`. Theo `application_name`: `cis-job` > `cis-worker` > **(trống)** > `db-migrate` > `cis-api` > TP browse >
`cis-tenant` > `crm-api` > `booking-api`. Phiên "(trống)" là `cis_app` (kết nối `asyncpg.connect` ad hoc, script ECS
exec) và `rdsadmin` — lệch C1.1a nhỏ. Phiên "PostgreSQL JDBC Driver" là `rdsadmin` (giám sát nội bộ RDS), không phải
người dùng.

Top SQL theo tải (PI, 7 ngày): `INSERT INTO acp_contract.atom_ranking …`; `SELECT count(*), md5(string_agg(…)) FROM
catalog.v_tour_day` (kiểm độ tươi/nhất quán catalog); tra cache `shared.decision_log` (`DISTINCT ON (question_key)`);
`INSERT INTO shared.llm_call_log`; đọc `catalog.v_tour_day` theo `source_id`; autovacuum `atom_ranking`;
`pg_advisory_xact_lock` (claim job). Không câu nào đáng lo ở mức tải này.

### (2) `pg_stat_statements` / PI top 20 theo role, SLI C1.2

Extension `pg_stat_statements` 1.10 đã cài (schema `public`, CIS mig 234); PI bật. Probe 28/10: 4 928 câu đang lưu
(`pg_stat_statements.max` = 5 000, `track = top`), **1 466 lần bị đẩy ra** (dealloc) từ 07/10 — bảng gần đầy nên câu
hiếm có thể mất lịch sử (D13). p95 dưới đây là xấp xỉ C1.1b `mean + 2 × stddev`; với phân bố lệch (vài lần chờ rất
lâu) nó **phóng đại** p95 thật.

Phân bổ tổng thời gian chạy theo role (07–28/10):

| Role | Số câu | Lần gọi | Tổng | Tỷ lệ | Mean |
|---|---:|---:|---:|---:|---:|
| `cis_app` | 486 | 35,2 M | 2 310 s | 43,8 % | 0,07 ms |
| `tripplanner` | 40 | 231k | 1 749 s | **33,1 %** | 7,6 ms |
| `rdsadmin` | 2 996 | 14,6 M | 557 s | 10,6 % | 0,04 ms |
| `aa_app_user` (tenant pool) | 821 | 297k | 437 s | 8,3 % | 1,5 ms |
| `booking` | 148 | 4,4 M | 102 s | 1,9 % | 0,02 ms |
| `crm_app` | 224 | 2,5 M | 77 s | 1,5 % | 0,03 ms |
| `db_migrator` | 193 | 25k | 42 s | 0,8 % | 1,7 ms |

Top theo tổng thời gian (cả instance): (1) `tripplanner`, text ẩn, 4 124 lần, 1 379 s, mean 335 ms, p95 ≈ 2,5 s, max
7,8 s, ~19 dòng/lần, ghi temp; (2) `cis_app` `INSERT INTO acp_contract.atom_ranking …` 7,7 M lần, 460 s, mean 0,1 ms;
(3) `cis_app` `SELECT pg_advisory_xact_lock($1)` (claim job) 171k lần, 250 s, mean 1,5 ms, **max 45 s**; (4)
`aa_app_user`, text ẩn, 4 119 lần, 236 s, mean 57 ms, p95 ≈ 324 ms, ghi temp; (5) `tripplanner`, text ẩn, 2 515 lần,
mean 75 ms; (6) `cis_app` đọc segment/`atom_ranking` (recompute) 1 135 lần, mean 140 ms. Chi tiết 20 dòng mỗi bảng
(`[pgss_total]`, `[pgss_mean]`, `[pgss_role_*]`) trong file data.

**Câu có `calls ≥ 20` và mean > 200 ms: 3** — `tripplanner` 26 lần mean 410 ms; `tripplanner` 4 124 lần mean 335 ms;
`cis_app` 24 lần mean 253 ms (đọc `atom_ranking` hiện hành, AA-734). Mean cao nhất của `booking` là một câu 9 lần
mean 1,6 s (text ẩn; nhiều khả năng là đọc `catalog.v_tour_day` của sự cố #130 trước hotfix #131 — chưa xác nhận).

| SLI C1.2 | Mục tiêu Dev | Đo được (28/10) | Kết quả |
|---|---|---|---|
| CIS tenant reads (`acp_shared.*`, `tenant_tour_versions`, `catalog.*`) p95 | < 150 ms | Theo text (login `cis_app`): 45 câu, 125k lần, mean 0,7 ms, câu tệ nhất p95 ≈ 254 ms; `tenant_tour_versions` 5 câu, p95 ≈ 2,5 ms. Pool tenant `aa_app_user` (text ẩn): câu nặng nhất p95 ≈ 324 ms, các câu khác ≤ 66 ms | **trượt ở 1–2 câu** (xấp xỉ) |
| CIS admin list / cost pages p95 | < 1 s | Aggregate chi phí LLM: 19 câu, câu tệ nhất p95 ≈ 322 ms; trang usage: p95 ≈ 22 ms | đạt |
| CIS job claim (advisory lock 650001) mean | < 20 ms | mean 1,4 ms (180k lần); max 45 s một lần | đạt |
| TripPlanner browse (`catalog.v_*`) p95 | < 300 ms | Text ẩn; câu nặng nhất role `tripplanner` mean 335 ms, p95 ≈ 2,5 s. Lambda: Duration p95 theo giờ TB 1,7 s, max 11,8 s | **trượt** |
| TripPlanner assembly + outbox p95 | < 500 ms | Text ẩn; các câu khác của `tripplanner` p95 ≈ 97–190 ms, một câu 26 lần p95 ≈ 1,4 s | chưa xác định |
| Booking API (`trip_cases`, `customers`) p95 | < 100 ms | Text ẩn; đường chính mean ≤ 0,4 ms (p95 ≈ 0,4–7 ms); ngoại lệ: 1 câu 9 lần mean 1,6 s, 1 câu 36 lần p95 ≈ 275 ms | đạt trên đường chính |
| Connection saturation p95 | < 60 % `max_connections`, mỗi role < 80 % limit | **6,6 %**; mỗi role ≤ 33 % trừ `crm_app` 83 % (1 mẫu). Lúc probe: 8 phiên client, `cis_app` 4/90, `crm_app` 1/6 | đạt (trừ 1 mẫu `crm_app`) |

Đây là tuần đầu tiên có số; theo C1.2a chỉ báo Nghiệp khi trượt **2 tuần liên tiếp** — tuần W45 cần đo lại hai SLI
trượt (xem §5a).

Lưu ý quyền: `cis_app` **không** là thành viên `pg_read_all_stats`. Chạy probe qua ECS exec thì các dòng
`pg_stat_statements` của role khác vẫn có số đo nhưng **ẩn text và queryid**; `pg_stat_activity` của role khác thấy
role + `application_name` nhưng không thấy `state` (đúng như probe 28/10 cho thấy). Muốn text đầy đủ: chạy cùng file qua DB Migrate `run-script`
(login master; `db_migrator` cũng có `pg_read_all_stats`). **Không đề xuất** cấp `pg_read_all_stats` cho `cis_app`:
role runtime khi đó đọc được text câu lệnh đang chạy của Booking / CRM (có thể chứa literal cá nhân) — trái DM-6.

Tín hiệu đã biết: S254 Booking #130 → 503 ở `/catalog/trip-plans` (đọc `catalog.v_tour_day` theo `source_id` từng dòng
vượt `command_timeout` 5 s; hotfix #131). Probe qua `cis_app` không thấy text của `tripplanner` / `booking` (SLI
`catalog_views` khớp 0 câu), nên trigger "Materialized catalog read model" chấm theo role: role `tripplanner` chỉ đọc view
`catalog.*` và schema `tripplanner`, câu nặng nhất p95 ≈ 2,5 s → gần chắc bắn; xác nhận bằng `run-script` (D6, D12).

### (3) Bảng và index (dump N1 lúc 28/10 04:28 UTC + probe)

Tổng kích thước DB `aa_cis_dev` **1 527 MB** (probe; 274 bảng). Theo schema: `shared` 740 MB, `geo` 361 MB, `acp_contract` 311 MB,
`silver_aa_internal` 29 MB, `acp_shared` 28 MB, `crm` 20 MB, `booking` 8,3 MB, `gold_aa_internal` 7,8 MB,
`tripplanner` 0,9 MB.

Top 10 theo kích thước (tổng = heap + index + toast):

| Bảng | ~dòng | Kích thước | Ghi chú |
|---|---:|---:|---|
| `shared.decision_log` | 434 147 | 443,7 MB | ledger Jev; index 214 MB (5 index > 13 MB); heap cache hit **76,9 %** |
| `geo.tour_place` | 13 356 | 215,5 MB | heap 6,8 MB, index 95 MB (HNSW embedding 93 MB, 7 scan), toast 114 MB (vector embedding): hợp lý, không phải bloat |
| `shared.llm_call_log` | 386 227 | 202,6 MB | ledger LLM, retention 180 ngày (chưa tới hạn) |
| `acp_contract.atom_embedding` | 11 036 | 175,2 MB | vector: toast 87 MB + HNSW 86 MB (14 scan) |
| `acp_contract.atom_ranking` | 97 368 | 66,6 MB | 13,5 M insert / 13,4 M delete: ghi lại toàn bảng mỗi lần recompute; seq scan 37,8k > idx scan 11,8k |
| `geo.tour_leg` | 96 123 | 65,9 MB | seq scan 2 756, idx scan 4 |
| `geo.tour_junction` | 222 234 | 55,1 MB | seq scan 1 252, idx scan 1 |
| `shared.tenant_api_usage` | 156 007 | 37,8 MB | retention 90 ngày (tới hạn 15/12) |
| `acp_contract.tour_atoms` | 54 494 | 31,8 MB | dead 4 816 (8,8 %) |
| `shared.job` | 7 688 | 22,2 MB | toast 12,2 MB (payload/result jsonb) |

Hạng 11–20 theo kích thước: `silver_aa_internal.generated_content` 18,8 MB, `shared.llm_shadow_log` 11,9 MB,
`acp_shared.content_piece` 11,9 MB, `acp_contract.question_embedding` 8,4 MB, `geo.tour_stop` 7,8 MB,
`acp_contract.atom_segment_member` 7,8 MB, `gold_aa_internal.published_tours` 6,8 MB, `acp_contract.route` 6,8 MB,
`silver_aa_internal.raw_tours` 6,5 MB, `crm.aa_catalog_tour` 6,4 MB. Top 30 theo kích thước và theo số dòng:
dòng `[table_size]` / `[table_rows]` trong file data.

- **Dead tuples (C5.2b):** theo dump 28/10 và probe (`[bloat]` = 0), **không bảng nào** có `n_dead_tup / n_live_tup > 20 %` với ≥ 100 dead.
  Cao nhất: `acp_contract.tour_atoms` 4 816 (8,8 %), `atom_segment_member` 1 257 (7,2 %), `atom_matches` 507.
- **Index không dùng (C5.2d):** probe đếm **178** index (không PK/UNIQUE) 0 scan (dump: 181), tổng **33,4 MB**. Lớn nhất `shared.idx_llm_call_log_model_created` 26,8 MB, `acp_shared.idx_content_piece_embedding`
  2,6 MB, `geo.tour_leg_countries_gin` 1,1 MB; còn lại ≤ 16 kB mỗi cái. Giá trị thu hồi thấp.
- **Cache hit** (`blks_hit / (hit + read)`, tích luỹ, `stats_reset` chưa từng chạy): `aa_cis_dev` **99,05 %** —
  sát trigger r7g (< 99 % cả tuần) nhưng chưa bắn; số này gồm cả giai đoạn `t3.micro` thiếu RAM. Bảng đọc từ đĩa nhiều
  nhất là `shared.decision_log` (heap hit 76,9 %; câu tra cache Jev `DISTINCT ON (question_key)` đọc 238k block).
  Tuần sau đo lại bằng chênh lệch hai lần probe, không bằng số tích luỹ.
- **Temp:** 4 938 file / **36 GB** ghi temp tích luỹ (`work_mem` 4 MB). Nguồn chính: câu nặng nhất của `aa_app_user`
  (227k block), các câu recompute segment của `cis_app` (149k–287k block), câu nặng nhất của `tripplanner` (50k block).
  Không gây trễ đĩa (WriteLatency TB 0,8 ms) nhưng là dấu hiệu của sort/hash lớn trong các câu đó (D12).
- **Thiết lập liên quan:** `shared_buffers` 516 MB, `effective_cache_size` 1 032 MB, `statement_timeout` 60 s,
  `idle_in_transaction_session_timeout` 60 s, `log_min_duration_statement` 500 ms, `log_lock_waits` on,
  `track_io_timing` on, autovacuum naptime 15 s, scale factor 0,1 / 0,05.

### (4) Ledger so với retention C5.4 / DM-7

Cửa sổ lấy từ code (AA-CIS-App `services/retention/policy.py`, AA-825), không phải từ bản nháp trước của trang này
(bản nháp ghi nhầm "chưa có job" — đã sửa sau khi probe thấy các job kind `retention_*`).

| Ledger | Dòng (28/10) | Dòng 7 ngày / 30 ngày | Cũ nhất | Cửa sổ (code) | Tình trạng retention |
|---|---:|---|---|---|---|
| `shared.decision_log` | 434 147 | 139 431 / 434 147 | 29/09 | 180 ngày, chỉ dòng chưa có `outcome`; archive S3 | `retention_decision_log` 12 lần / 30 ngày, 0 lỗi; tới hạn **28/03/2027** |
| `shared.llm_call_log` | 386 227 | 119 980 / 375 684 | 17/09 | 180 ngày + rollup ngày `llm_call_daily`; archive | `retention_llm_call_log` 14 lần; 0 dòng quá hạn; tới hạn **16/03/2027** |
| `shared.tenant_api_usage` | 156 007 | 14 991 / 148 489 | 16/09 | 90 ngày + rollup tháng; archive | `retention_tenant_api_usage` 14 lần; 0 dòng quá hạn; tới hạn **15/12/2026** |
| `shared.job` | 7 688 | 4 896 / 7 688 | 28/09 | succeeded 30 / failed 90 ngày theo `finished_at` | `retention_job` 12 lần; dòng cũ nhất vừa chạm 30 ngày; `n_tup_del` = 0 từ lần khởi động 15/10 |
| `booking.job` | 6 869 | — (cis_app không đọc được) | — | như trên | **live** (AA-825, S251); 6 999 dòng đã xoá từ 15/10 |
| `crm.job` | 7 985 | — (cis_app không đọc được) | — | như trên | có xoá (15 152 dòng từ 15/10) |

Lịch chạy (DM-7.2, docstring `retention_job.py`): lần chạy theo lịch là **DRY RUN cho tới khi một live run thủ công của
kind đó (cùng cửa sổ) thành công**; lần `manual_override` không tính. Log S239 chỉ có lần override 200 dòng/bảng cho
`llm_call_log` / `tenant_api_usage` (khớp `n_tup_del` = 200 ở hai bảng). Probe này chưa đọc `result ->> 'mode'` của các
job retention, nên chế độ hiện tại của từng kind **chưa xác nhận trực tiếp** — probe đã được bổ sung mục `[retention]`
cho lần sau, và có script một lần cho phiên điều phối (§6).

Dự báo: `decision_log` chạm 1 M dòng ≈ **25/11/2026** theo nhịp 7 ngày (~20k/ngày, có wave S1 23–26/10) hoặc
≈ **18/12** theo nhịp tháng (~11k/ngày); `llm_call_log` ≈ **02/12** (7 ngày) hoặc ≈ **30/12** (tháng). Vì cửa sổ 180 ngày
chưa đầy, retention không chặn được mốc 1 M; trạng thái ổn định khi đầy cửa sổ: `decision_log` ~2,0–3,6 M dòng
(~2–3,7 GB, ~1 KB/dòng gồm index), `llm_call_log` ~1,7–3,1 M dòng (~0,9–1,6 GB). Hàng C3 "Retention" đặt ngưỡng dừng
"> 1 M dòng **trước khi retention có**" — retention đã có, nên ngưỡng không bắn; nhưng con số 1 M không còn là mốc an
toàn thực tế với cửa sổ 180 ngày (D3). Trigger partition (> 10 M dòng / > 5 GB) vẫn xa.

### (5) Lambda (TripPlanner)

| Hàm | Reserved | Invocations 30 ngày | Throttles | Errors | Concurrency max | Duration p95 (theo giờ) |
|---|---:|---:|---:|---:|---:|---|
| `aa-tripplanner-dev-browse` | 15 | 21 067 | 16 157 (gần hết **trước 16/10**, thời quota 10); sau 16/10: **99** (1 giờ ngày 16/10) | 118 | **15** (chạm trần reservation) | TB 1,7 s, max 11,8 s |
| `aa-tripplanner-dev-assembly` | 5 | 969 | 14 (11 ngày 20/10) | 2 | 10 | max 14,6 s |

Quota account đã là 1000; concurrency account đỉnh 15. Lệch tài liệu: bảng C2.2 ghi reserved 10 / 10, Terraform live là
**15 / 5** (`connection_budget.json` đọc đúng Terraform: tổng role `tripplanner` 20 / limit 30, vẫn ổn). Bảng C2.2
đã sửa trong cùng PR (D5).

### (6) Job backlog theo owner (CloudWatch `AA/Jobs/*`, tới 16/10 mới có)

- CIS `shared.job`: tuổi job queued tới hạn lâu nhất **1 407 s** (một mẫu 16/10 ~17:00 UTC, > 15′); còn lại p95 2 s.
  `OverdueRunningJobs` = 0 suốt kỳ.
- Booking `booking.job`: **một mẫu 5 phút 38 746 s** (≈ 10,8 giờ) lúc 24/10 ~03:10 UTC, alarm `queue-age` ALARM 10′ rồi OK;
  mọi mẫu khác 0. Nguyên nhân chưa xác nhận (nhiều khả năng một job có `run_after` cũ được thấy đúng lúc worker
  vừa khởi động lại) — xem D8.
- Lúc probe: `shared.job` không có job `queued` / `running` (6 cancelled, 7 failed, 7 675 succeeded).
- Thời lượng job CIS theo kind, 30 ngày (probe `[job_cis_kind_30d]`; Booking / CRM không đọc được bằng `cis_app`):

| Kind | Số job | p50 | p95 | Lỗi |
|---|---:|---:|---:|---:|
| `a3_atomize` | 2 071 | 42 s | 152 s | 0 |
| `place_extract` | 1 914 | 1,5 s | 34 s | 0 |
| `s1_rewrite` | 1 708 | 149 s | 259 s | 1 |
| `place_cards_build` | 918 | 20 s | 85 s | 0 |
| `t9_write` | 344 | 72 s | 182 s | 0 |
| `recompute` | 127 | 145 s | 296 s | 2 |
| `tour_graph_build` | 70 | 25 s | 57 s | 0 |
| `t2_rewrite` | 62 | 89 s | 331 s | 0 |
| `place_geocode` | 60 | 60 s | 396 s | 0 |
| `photo_sync` | 55 | 12 s | 629 s | 1 |
| `s1_seo_prefetch` | 45 | 51 s | **1 002 s** | 0 |
| `place_dedupe` | 30 | 163 s | 643 s | 0 |
| `place_shape` | 24 | 284 s | **2 675 s** | 0 |
| `supply_content_draft` | 10 | 2,7 s | 3,3 s | **3** |

  Các kind `retention_*`, `ops_rds_role_connections`, `staff_directory_reconcile` đều < 2 s, 0 lỗi. Hai kind có đuôi dài
  (`place_shape` p95 45′, `s1_seo_prefetch` p95 17′) vượt `expected_seconds` mặc định 600 s nếu kind không đặt riêng —
  chỉ là quan sát, không phải trigger C3. `supply_content_draft` 3/10 lỗi thuộc tính năng (S251), không phải dung lượng.

### (7) Ngân sách C2.2 tính lại từ Terraform live

`python3 db/check_connection_budget.py` (AA-CIS-Infra `main` 82400b9, 28/10):

| Pool | Role | max_size × tiến trình | Worst case |
|---|---|---|---:|
| cis-api | cis_app | 10 × 7 | 70 |
| cis-tenant | aa_app_user | 2 × 7 | 14 |
| cis-worker | cis_app | 10 × 3 | 30 |
| tp-browse | tripplanner | 1 × 15 | 15 |
| tp-assembly | tripplanner | 1 × 5 | 5 |
| booking-api | booking | 5 × 2 | 10 |
| crm-api | crm_app | 3 × 2 | 6 |
| db-migrate / dump / probe | db_migrator | 1 × 3 | 3 |
| dự phòng master + rdsadmin | — | — | 15 |
| **Tổng** | | | **168 / trần 135** (75 % của 181) |

Theo role: `cis_app` **100 / 90**, `aa_app_user` 14/15, `booking` 10/15, `crm_app` 6/6, `db_migrator` 3/5,
`tripplanner` 20/30. Hai vượt (`cis_app`, tổng) đang nằm trong `accepted_overages` tới **15/12/2026**. Đo thật: đỉnh
instance 30, đỉnh `cis_app` 23 (25,6 % limit). Với `cis-api` = 5 (mục tiêu C2.2) tổng = 133 < 135.

### (8) Trigger C3 — đo được, bắn hay không

| Hàng C3 | Trigger | Giá trị đo | Kết quả |
|---|---|---|---|
| t4g.small → t4g.medium | CPU > 20 % quá 50 % số giờ trong tuần | 0 giờ / mọi tuần ISO 40–44 | không bắn |
| | `CPUSurplusCreditsCharged` > ~10 USD/tháng | 0 | không bắn |
| | `FreeableMemory` < 300 MB > 1 h/ngày × 3 ngày/tuần | 1 giờ (17/10) sau đổi | không bắn |
| | Tổng C2.2 > 75 % `max_connections` | **168 / 135 trên giấy**; đo thật 30 | **bắn trên giấy** (đã có overage chấp nhận tới 15/12) → đòn bẩy rẻ hơn trước (C3b: pool budget), xem D2 |
| t4g.medium → m7g.large | > 5 câu primary-path mean > 200 ms | 3 câu (`calls ≥ 20`) | không bắn (và chưa ở medium) |
| m7g → r7g | cache hit < 99 % một tuần; `FreeableMemory` < 10 % RAM | cache 99,05 % (tích luỹ); min 257 MB = 12,5 % RAM | không bắn (cache sát ngưỡng, đo lại theo tuần) |
| Storage | dùng > 80 % `max_allocated_storage`, hoặc tăng > 1 GB/ngày một tuần | 4,5 %; 0,09 GB/ngày | không bắn |
| Retention (hard stop) | bảng log > 1 M dòng, hoặc `FreeStorageSpace` < 10 GB trước khi retention có | retention đã có (AA-825); max 434k dòng; 15,3 GB | không bắn; 1 M dòng sẽ vượt 25/11–30/12 do cửa sổ 180 ngày chưa đầy (D3) |
| RDS Proxy | Lambda cần > 20; `DatabaseConnections` p95 > 60 % một tuần | 15 + 5 reserved; 6,6 % | không bắn |
| Materialized catalog read model | một view `catalog.*` p95 > 500 ms | câu nặng nhất role `tripplanner` p95 ≈ 2,5 s (text ẩn); Booking 1 câu mean 1,6 s; sự cố #130 S254 | **gần chắc bắn** — xác nhận text, rồi query/index trước (C3b, D12) |
| Read replica | đọc > 30 % CPU primary hoặc CPU > 60 % kéo dài | CPU TB 4,8 % | không bắn |
| Partitioning | bảng > 10 M dòng / > 5 GB; DELETE retention > 5′; dead > 20 % | max 428k / 444 MB; dead max 8,8 % | không bắn |
| App split (Booking riêng) | DB > 200 GB; conn p95 > 70 %; Booking p95 ×2 trong wave ≥ 2 lần/tháng | 1,5 GB; 6,6 %; Booking 1,9 % tải SQL, đường chính mean ≤ 0,4 ms | không bắn |

### (9) Chi phí RDS so với ngân sách

Theo báo cáo chi phí S248 (`docs/audits/2026-10-23-S248-cost-report/`): RDS tháng 9 = 20,39 USD; sau khi đổi sang
t4g.small ≈ 0,88 USD/ngày + backup → **≈ 30 USD/tháng** (trước ≈ 20). Nằm trong ngân sách app `shared` 100 USD/tháng
(run-rate tháng 10 ~84 USD cho cả nhóm shared). Không có surplus credit. Số tháng 10 đầy đủ thuộc AA-896 (audit chi phí
tháng 11).

### ECS — 6 service (cùng cluster, CPU/bộ nhớ theo % reservation của task)

| Service | Task | Desired / autoscale | CPU TB | CPU TB/giờ max | Mem TB | Mem max | Dữ liệu từ |
|---|---|---|---:|---:|---:|---:|---|
| `aa-cis-dev-api` | 0,5 vCPU / 1 GB, x86 | 1 / 1–7 | 2,9 % | 50 % (đỉnh phút chạm 100 % ở p95 giờ) | 20,7 % | 63 % | 28/09 |
| `aa-cis-dev-worker` | 0,5 / 1 GB, x86 | 1 / 1–3 | 2,9 % | 55 % | 18,3 % | 62 % | 05/10 |
| `aa-booking-dev-api` | 0,25 / 0,5 GB, x86 | 1 | 5,9 % | 38 % | 18,3 % | 57 % | 14/10 |
| `aa-crm-dev-api` | 0,25 / 0,5 GB, ARM64 | 1 | 4,4 % | 8,5 % | 22,6 % | 33 % | 23/10 |
| `aa-crm-dev-web` | 0,25 / 0,5 GB, ARM64 | 1 | 2,7 % | 4,6 % | 14,1 % | 26 % | 24/10 |
| `aa-crm-dev-portal` | 0,25 / 0,5 GB, ARM64 | 1 | 2,9 % | 10,2 % | 16,1 % | 29 % | 26/10 |

Không service nào thiếu tài nguyên; ba service CRM đã ở cỡ Fargate nhỏ nhất. CIS api/worker có đỉnh CPU ngắn chạm
100 % của 0,5 vCPU trong các wave (autoscaling lo), bộ nhớ đỉnh ≤ 63 %. Không đề xuất đổi cỡ.

## 3. Rủi ro (xếp theo mức)

1. **Đọc catalog của TripPlanner chậm** — 33 % thời gian SQL của cả instance đến từ role `tripplanner`; câu nặng nhất
   p95 ≈ 2,5 s, ghi temp; SLI browse trượt; cộng với sự cố Booking #130 cùng họ view `catalog.v_tour_day`. Đây là rủi
   ro người dùng thấy đầu tiên khi có traffic thật.
2. **Ngân sách kết nối trên giấy vượt trần** (168 / 135) với hạn chấp nhận 15/12 — một deploy chồng lúc autoscale max có
   thể đẩy `cis_app` tới limit 90 (backstop là lỗi kết nối trên task mới, không sập instance).
3. **Retention có nhưng chưa live:** ledger sẽ qua 1 M dòng trong 4–9 tuần và chỉ ngừng tăng sau 15/12 (tenant usage) /
   giữa–cuối 03/2027 (LLM, Jev); nếu không ai duyệt live run khi dòng đầu tiên quá hạn thì lịch chỉ đếm mãi.
4. **`crm_app` không có alarm per-role** và pool thiết kế bằng đúng limit (3 × 2 = 6): mỗi deploy CRM chạm 83–100 %.
5. Nhỏ: tenant pool có 1 câu p95 ≈ 324 ms (text ẩn) — trượt SLI tenant lần 1; cache hit 99,05 % sát ngưỡng r7g, kéo
   xuống bởi tra cache Jev trên `decision_log`; 36 GB ghi temp tích luỹ; `pg_stat_statements` đầy (1 466 dealloc); phiên
   không `application_name` (C1.1a); `atom_ranking` ghi lại toàn bảng mỗi recompute (13,5 M insert / 13,4 M delete); một
   lần chờ advisory lock 45 s; một mẫu queue-age Booking 10,8 giờ chưa rõ nguyên nhân; alarm đĩa 50 % sẽ kêu khi ledger
   đầy cửa sổ dù còn autoscale tới 100 GB.

## 4. Danh sách quyết định (C8c) — đề xuất (đã duyệt S256, xem §4a)

| # | Quyết định đề xuất | Loại | Hàng C3 / quy tắc | Ai / chi phí |
|---|---|---|---|---|
| D1 | Giữ `db.t4g.small`, không resize | no action | t4g.small → medium: cả 3 trigger đo được không bắn | — / 0 |
| D2 | Thu pool chính `cis-api` 10 → 5 trước 15/12 (theo baseline `aa859_main_pool_gauge`), cập nhật `connection_budget.json` + bảng C2.2 cùng PR, gỡ 2 `accepted_overages` | tune | t4g.small → medium, dòng "C2.2 total > 75 %"; C3b (pool budget trước resize) | CIS + Infra, S / 0 |
| D3 | Retention đã có (AA-825), không cần làm mới. (a) Phiên điều phối chạy `retention_check.py` (§6) để xác nhận chế độ từng kind. (b) Trước **15/12/2026** (dòng `tenant_api_usage` đầu tiên quá 90 ngày): DRY RUN thủ công → Nghiệp duyệt `max_rows` → live run, để lịch chuyển sang live (DM-7.2); làm lại như vậy cho `llm_call_log` / `decision_log` giữa tháng 3/2027 và cho `retention_job` khi có ứng viên. (c) Giữ cửa sổ 180 ngày (đề xuất); sửa câu chữ hàng C3 "Retention": ngưỡng 1 M dòng chỉ áp dụng cho ledger **chưa có** job retention, ledger đã có job thì theo dõi bằng trigger partition (> 10 M / > 5 GB) | tune + docs | "Retention" | CIS (vận hành) + root, XS / S3 vài cent |
| D4 | Thêm alarm `aa-cis-dev-rds-role-connections-crm_app` (RoleConnectionLimitPct > 80 %), cân nhắc nâng limit `crm_app` 6 → 8 bằng file `roles/` nếu alarm kêu mỗi lần deploy | tune | C4.1 "mỗi role có limit một alarm" | Infra, XS / ~0,10 USD/tháng |
| D5 | Sửa bảng C2.2 trong `03-scaling.md`: TP reserved concurrency live 15 / 5 (không phải 10 / 10), tổng mục tiêu tính lại = 133 — **đã làm trong cùng PR** (data standards v1.6, facts only) | docs | C2.3c | root, XS / 0 |
| D6 | Đưa probe vào AA-CIS-Infra `db/scripts/aa838_capacity_probe.py` (đã qua shape check `--inspect-script`) để mỗi tháng chạy bằng `run-script` có text đầy đủ; tuần dùng PI + probe ECS exec | tune | C4.3, C8b | Infra, XS / 0 |
| D7 | Không chạy `pg_stat_statements_reset()` tháng này: số liệu từ 07/10 (~3 tuần), giữ để so tháng sau; lần probe này chạy `PROBE_TOP` mặc định 20, nên chưa có snapshot top 50 mà C4.3a đòi trước khi reset | no action | C4.3a | — |
| D8 | Tra mẫu queue-age Booking 24/10 bằng run-script chỉ đọc trên `booking.job` (job tạo trước 03:00 UTC, bắt đầu sau 03:05 UTC) | investigate | C4.1 job backlog | Booking/Infra, XS / 0 |
| D9 | Đặt `application_name` cho kết nối ad hoc của CIS (script ECS exec, `asyncpg.connect` lẻ) | tune | C1.1a | CIS, XS / 0 |
| D10 | Theo dõi, chưa làm: `atom_ranking` (ghi đè thay vì xoá + chèn), `geo.tour_place` (đã giải thích: embedding + HNSW, không phải bloat), 178 index không dùng (33 MB, giá trị thấp; nếu bỏ thì bắt đầu với `idx_llm_call_log_model_created` sau khi kiểm trang cost theo model) | no action | C3b (query/index trước), C5.2d | — |
| D11 | Alarm đĩa `< 50 %` (10 GB trống) sẽ kêu khi ledger đầy cửa sổ (~3–5 GB thêm) hoặc sớm hơn theo nhịp 7 ngày: giữ nguyên làm cảnh báo sớm, xem lại ở rà soát tháng 12 | no action | C4.1 | — |
| D12 | Lấy text câu nặng nhất của `tripplanner` (và câu 9 lần của `booking`, câu nặng nhất của `aa_app_user`) bằng probe qua `run-script` (D6), `EXPLAIN (ANALYZE, BUFFERS)` trên Dev, rồi sửa theo thứ tự C3b: query/index (đọc theo `source_id` một lần thay vì từng dòng như hotfix #131, index khớp bộ lọc browse), sau đó mới tính materialized read model | investigate → tune | "Materialized catalog read model"; C3b | TripPlanner + CIS (chủ view `catalog.*`), S / 0 |
| D13 | Nâng `pg_stat_statements.max` 5 000 → 10 000 trong parameter group (tham số static: áp vào lần reboot có kế hoạch kế tiếp, vài MB shared memory) | tune | C4.3 | Infra, XS / 0 |

## 4a. Kết quả duyệt và thực hiện (S256, 28/10/2026)

Tech lead duyệt cả danh sách D1–D13 trong S256 (trừ việc thêm dịch vụ AWS trả phí mới — danh sách này không có mục
nào như vậy). Lane AA-838 của S256 (Claude Code) thực hiện; bước live (Terraform Apply, reboot RDS, run-script, deploy)
là của phiên điều phối.

| # | Kết quả | Ở đâu |
|---|---|---|
| D1 | Quyết định, không làm gì: giữ `db.t4g.small` | — |
| D2 | **Đổi đòn bẩy, cùng mục tiêu:** pool chính `cis-api` **giữ 10**; thay vào đó `max_capacity` của api **7 → 3**. Lý do: baseline `aa859_main_pool_gauge` (16–28/10, log `/ecs/aa-cis-dev`, đọc S256): dòng gauge 60 s gần như luôn `in_use=0` (đo thưa, báo thấp), nhưng các dòng `aa859_main_pool_wait` (chờ ≥ 50 ms) cho thấy một task dùng 5–7 kết nối 55 lần và 8–10 kết nối 8 lần trong 23–28/10 với traffic admin thường, và đầy 10 trong burst AA-859 (22/10, chờ tối đa 3,9 s) — pool 5 sẽ xếp hàng các lần đó và làm burst quá `acquire timeout` 5 s (503). Autoscaling api chưa từng lên quá **3** task từ cuối tháng 9. Ngân sách C2.2: **120 / 135**, `cis_app` 60 / 90, `aa_app_user` 6 / 15; bỏ cả hai `accepted_overages`. Muốn quay về phương án pool 5: đảo PR Infra + đổi `api/main.py` | AA-CIS-Infra (`modules/ecs/main.tf`, `db/connection_budget.json`); data standards v1.7 C2.2 |
| D3 | (a) Bằng probe mới qua `run-script` (mục `[retention]`: chế độ và trigger của từng kind, kind nào đã có live run được duyệt) — thay cho `retention_check.py`. (b) Mốc **trước 15/12/2026**: DRY RUN thủ công `retention_tenant_api_usage` → duyệt `max_rows` → live run; giữa tháng 3/2027 cho `llm_call_log` / `decision_log` (phiên điều phối ghi mốc vào backlog "Time-gated checks"). (c) Câu chữ hàng C3 "Retention" đã sửa (v1.7): ngưỡng 1 M dòng chỉ cho ledger **chưa có** job retention | root (data standards v1.7, template `capacity-review.md`); bước (a)(b) của điều phối |
| D4 | Đã xong S255 (Infra #461): alarm `…-rds-role-connections-crm_app` tồn tại, trạng thái OK (đọc S256). Chưa nâng limit `crm_app` (chưa có lần kêu nào khi deploy) | — |
| D5 | Đã xong S255 (data standards v1.6) | — |
| D6 | Probe trong Infra `db/scripts/aa838_capacity_probe.py` đồng bộ bản đã sửa (cửa sổ `decision_log` 180 ngày, `shared.job` theo `finished_at`, mục `[retention]`); `PROBE_TOP` mặc định **50** vì `run-script` không truyền biến môi trường | AA-CIS-Infra `db/scripts/` (+ bản copy `scripts/capacity_probe.py` ở đây) |
| D7 | Quyết định, không reset. Từ nay mỗi lần chạy probe qua `run-script` đã có snapshot top 50 (C4.3a) | — |
| D8 | Đã khoanh nguyên nhân từ log task Booking: mẫu 38 746 s đến từ sampler của **task mới** 0,5 s sau khi deploy cuốn chiếu khởi động nó (24/10 03:14:46 UTC); sampler task cũ gửi 0 lúc 03:11:23, mẫu kế tiếp lại 0 → một dòng `run_after` ≈ 23/10 16:29 UTC chỉ "đến hạn mà chưa ai nhận" trong vài phút quanh deploy (nhiều khả năng kind mà worker cũ chưa có, hoặc job được tạo với `run_after` cũ). Script chỉ đọc `db/scripts/aa838_booking_queue_age_check.py` gọi tên dòng đó (kind, `run_after` so với `created_at`, lúc được nhận) | AA-CIS-Infra `db/scripts/`; chạy bởi điều phối |
| D9 | CIS: `get_database_url()` gắn mặc định `application_name=cis-direct` (pool có tên riêng vẫn thắng), 8 chỗ `asyncpg.connect(os.environ["DATABASE_URL"])` chuyển sang `get_database_url()`; mẫu script ECS exec (runbook + skill `aa-cis-schema`) truyền `server_settings={"application_name": "cis-exec"}` | AA-CIS-App `shared/secrets.py`; root runbook + skill; data standards v1.7 C1.1a |
| D10 | Quyết định, theo dõi, chưa làm | — |
| D11 | Quyết định, giữ alarm đĩa 50 %, xem lại ở rà soát tháng 12 | — |
| D12 | Bước 1 (lấy text câu nặng nhất của `tripplanner` / `booking` / `aa_app_user`) = cùng lần chạy probe qua `run-script` (D6). Bước 2 (`EXPLAIN (ANALYZE, BUFFERS)` + sửa query/index, rồi mới tính read model) là lát việc sau cho TripPlanner + CIS khi có text; phần Booking đã sửa ở S255 (#134, 15/16 đường đọc ≤ 152 ms) | điều phối (run-script), rồi lát việc sau |
| D13 | `pg_stat_statements.max` = 10 000 trong parameter group, `apply_method = pending-reboot` (tham số static). Có hiệu lực sau lần reboot có kế hoạch kế tiếp (vài MB shared memory, 0 USD); chạy probe **trước** reboot | AA-CIS-Infra `modules/rds/main.tf`; reboot = bước của điều phối |

Chi phí cả danh sách: **0 USD/tháng** thêm (D4 0,10 USD/tháng đã tính ở S255). Không mục nào cần một dịch vụ AWS trả phí mới.

## 5. Nhịp rà soát (AA-838)

| Nhịp | Quy tắc | Khi nào | Làm gì | Lưu ở đâu |
|---|---|---|---|---|
| **Tuần** | C4.3, C1.2a | Phiên đầu mỗi tuần ISO, và sau mỗi wave | PI top SQL / wait (7 ngày, miễn phí) + probe ECS exec phần `[pgss_*]` / `[sli]` / `[locks]`; slow log > 500 ms và lock wait trong log group `postgresql`. Một SLI trượt 2 tuần liên tiếp → báo Nghiệp kèm câu lệnh + cách sửa | 1 đoạn "C4.3 tuần W<nn>" trong log phiên (mẫu §5a) |
| **Tháng** | C8a–C8c, FIN-02 = OPS-08 | Phiên đầu mỗi tháng (và sau wave làm ledger ×2) | 9 mục C8b theo trang này: chạy `scripts/gen_cw_queries*.py` + `analyze_cw.py` (đổi START/END), PI, probe qua `run-script`, `check_connection_budget.py`, số chi phí từ báo cáo chi phí tháng; kết bằng danh sách quyết định | `docs/audits/<date>-S<nnn>-capacity-review/` + root PR; mẫu [`docs/templates/capacity-review.md`](../../templates/capacity-review.md) |
| **Quý** | DM-8.10 | Phiên đầu mỗi quý | Role, grant, default ACL, IAM đọc secret DB, user Cognito `aa-workforce`. Lần đầu đã làm S245 (`docs/audits/2026-10-20-S245-access-review/`); lần sau: phiên đầu 2027-Q1 | `docs/audits/<date>-S<nnn>-access-review/`; mẫu [`docs/templates/access-review.md`](../../templates/access-review.md) |

Nhịp đã ghi vào `skill/aa-session/SKILL.md` (bước 6 đầu phiên) và một dòng trỏ trong `.kiro/steering/session-workflow.md`
(cùng PR với trang này).

### 5a. C4.3 tuần W44 (lần kiểm tuần đầu tiên, 28/10/2026)

Nguồn: probe 28/10 06:53 UTC (`pg_stat_statements` tích luỹ 07–28/10, login `cis_app`), PI 21–28/10, CloudWatch.
Top theo tổng thời gian: role `tripplanner` (1 câu, 1 379 s, mean 335 ms) > `cis_app` `INSERT atom_ranking` (460 s, mean
0,1 ms) > `pg_advisory_xact_lock` (250 s, mean 1,5 ms) > `aa_app_user` (1 câu, 236 s, mean 57 ms). Câu `calls ≥ 20` mean
> 200 ms: 3 (2 của `tripplanner`, 1 recompute của `cis_app`). SLI C1.2: job claim, admin/cost, Booking đường chính, kết
nối **đạt**; TripPlanner browse **trượt** (p95 ≈ 2,5 s), CIS tenant reads **trượt ở 1–2 câu** (p95 ≈ 254–324 ms, xấp
xỉ), TP assembly chưa xác định (text ẩn). Lock: 0 phiên chờ lúc probe, 0 transaction mở > 60 s, 0 deadlock tích luỹ.
Slow log > 500 ms: chưa đọc tuần này (log group `postgresql`; thêm vào lần W45). Đây là lần trượt **thứ nhất** — W45
(phiên đầu tuần 02/11) đo lại hai SLI trượt; nếu vẫn trượt thì báo Nghiệp theo C1.2a kèm text câu lệnh (từ D12) và
cách sửa. W45 so sánh bằng chênh lệch giữa hai lần probe (số tích luỹ không cho biết riêng một tuần).

## 6. Cách tái tạo / việc của phiên điều phối

- `scripts/capacity_probe.py` — chỉ đọc, hai cách chạy, mọi dòng bắt đầu bằng `PROBE`. Sau lần chạy 28/10 đã sửa hai
  chỗ: cửa sổ `decision_log` 180 ngày (bản cũ in "none yet") và `shared.job` tính theo `finished_at`; thêm mục
  `[retention]` (lần chạy gần nhất và chế độ của từng kind `retention_*`). Output lần này: `data/probe-2026-10-28.txt`
  (chạy bằng bản trước khi sửa).
  1. ECS exec trong container `api` của `aa-cis-dev-api` (login `cis_app`, `DATABASE_URL` của container), theo pattern
     S3-mediated: tải lên `scripts/aa838_capacity_probe.py` trong bucket bronze, presign, rồi chạy
     `sh -c 'curl -s "$URL" -o /tmp/p.py && PROBE_TOP=50 python3 /tmp/p.py'`. `PROBE_TOP=50` = snapshot top 50 (C4.3a).
  2. DB Migrate `mode=run-script` sau khi copy vào Infra `db/scripts/` (D6) — có text đầy đủ của mọi role.
- `scripts/gen_cw_queries.py`, `scripts/gen_cw_queries2.py` → `aws cloudwatch get-metric-data --cli-input-json
  file://cw_in.json …` (lệnh một dòng), rồi `scripts/analyze_cw.py`. Kết quả lần này: `cloudwatch-summary.txt`
  (giờ hiển thị theo +07).
- PI: `aws pi describe-dimension-keys` (group `db.application`, `db.user`, `db.wait_event`, `db.sql_tokenized`) và
  `aws pi get-resource-metrics` (`db.load.avg`, chu kỳ 300 s), cửa sổ 7 ngày.

- Việc còn của phiên điều phối (chỉ đọc): chạy `.tmp-session/S255/aa838/retention_check.py` theo pattern ECS exec
  S3-mediated để xác nhận chế độ (dry_run / live) của từng kind retention trước khi chốt D3.

## 7. Phụ lục — output probe

Output thô đầy đủ: [`data/probe-2026-10-28.txt`](data/probe-2026-10-28.txt) (332 dòng `PROBE` + 2 dòng của wrapper ECS
exec). Đã soát trước khi commit: không có DSN, mật khẩu, token, account ID, ARN, UUID hay literal chuỗi; text câu lệnh
đã chuẩn hoá (`$n`) và cắt ở 160 ký tự. Các mục: `[header]`, `[setting]`, `[database]`, `[schema]`, `[table_size]`,
`[table_rows]`, `[bloat]`, `[index_size]`, `[unused_index]`, `[ledger]`, `[job_cis]`, `[job_cis_kind_30d]`, `[conn]`,
`[conn_app]`, `[conn_role]`, `[long_xact]`, `[locks]`, `[pgss]`, `[pgss_role]`, `[pgss_total]`, `[pgss_mean]`,
`[pgss_role_total]`, `[pgss_role_mean]`, `[sli]`.

Dòng mở đầu của probe (để đối chiếu nhanh):

```text
PROBE [header] login=cis_app at=2026-10-28T06:53:47Z postmaster_start=2026-10-15 07:46:28.456331+00:00 read_all_stats=False
PROBE [database] aa_cis_dev size=1527.4MB backends=6 commit=14582773 rollback=3097 cache_hit=99.05% temp_files=4938 temp=36275.8MB deadlocks=0 conflicts=0 xid_age=2516409 stats_reset=None
PROBE [pgss] schema=public statements=4928 dealloc=1466 stats_reset=2026-10-07 16:35:01.069635+00:00
PROBE [pgss] statements with calls>=20 and mean>200ms: 3
PROBE [bloat] tables with dead/live > 20% and >= 1000 dead rows: 0
PROBE [unused_index] count=178 total=33.4MB (C5.2d: drop candidate only after 30 days at 0)
```
