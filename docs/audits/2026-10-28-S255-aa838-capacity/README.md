---
id: OPS-08-2026-10
title: Capacity review 2026-10 (first monthly C8 review)
description: Rà soát dung lượng lần đầu của RDS dùng chung và 6 service ECS (30 ngày tới 28/10/2026): headroom, trigger C3, ngân sách kết nối C2.2, rủi ro, danh sách quyết định chờ Nghiệp duyệt, và nhịp tuần/tháng/quý.
type: report
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-partner, aa-cis-infra]
last_reviewed: 2026-10-28
review_every_days: 30
related: [OPS-08, FIN-02, AA-838, AA-896, AA-824, AA-832, AA-859, AA-879]
---

# Rà soát dung lượng 2026-10 (lần đầu, data standards C8)

Ngày: 28/10/2026 (S255). Tác nhân: Claude Code (lane AA-838, chỉ đọc). Chi phí: ≈ 0 USD (vài lệnh CloudWatch
`GetMetricData` + Performance Insights API, trong free tier).
Cửa sổ: **28/09 06:00 → 28/10 06:00 UTC (30 ngày)**. RDS đổi `db.t3.micro` → `db.t4g.small` ngày 15/10, nên mọi trigger
C3 của instance được chấm trên **16–28/10** (301 giờ sau đổi); số trước đó chỉ để so sánh.
Lần sau: phiên đầu tiên của tháng 12/2026 (C8a), hoặc sớm hơn nếu một wave làm một ledger tăng gấp đôi.

Không có account ID, ARN, resource ID hay giá trị dòng nào trong trang này. Các mục ghi **[CHỜ PROBE]** điền sau khi
phiên điều phối chạy `scripts/capacity_probe.py` (xem §6).

## 1. Kết luận ngắn

- **Instance còn rất rộng.** CPU trung bình 4,7 %, chưa giờ nào vượt baseline 20 %; tải DB (PI, 7 ngày) trung bình
  0,02 phiên hoạt động, đỉnh 0,29 trên 2 vCPU; kết nối đỉnh 30 / 181 (16,6 %), p95 12. Bộ nhớ trống sau đổi:
  thấp nhất 257 MB (1 giờ duy nhất), trung bình 543 MB. **Không trigger resize nào bắn** → giữ `db.t4g.small`.
- **Đĩa:** dùng ≈ 4,5 GB / 20 GB cấp (max autoscale 100 GB); tăng 0,05 GB/ngày (30 ngày), 0,09 GB/ngày (7 ngày gần
  nhất, do wave S1). Alarm `FreeStorageSpace < 50 %` (10 GB trống) sẽ kêu khoảng **cuối tháng 12** nếu giữ nhịp 7 ngày.
- **Rủi ro thật duy nhất là ledger không có retention:** `shared.decision_log` 428k dòng / 444 MB (bảng lớn nhất) và
  `shared.llm_call_log` 384k / 203 MB tăng ~10k dòng/ngày (wave S1 23–26/10: ~42k/ngày). Ngưỡng dừng C3 "bảng log
  > 1M dòng trước khi retention CIS có" dự kiến chạm **khoảng giữa–cuối tháng 12/2026**, sớm hơn nếu có wave lớn.
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

Extension `pg_stat_statements` 1.10 đã cài (schema `public`, CIS mig 234, 15/10); PI bật. **[CHỜ PROBE]**: bảng top 20
theo `total_exec_time` và `mean_exec_time` mỗi role, số câu có `calls ≥ 20` và mean > 200 ms, và SLI C1.2 xấp xỉ
(`mean + 2 × stddev`):

| SLI C1.2 | Mục tiêu Dev | Đo được |
|---|---|---|
| CIS tenant reads (`acp_shared.*`, `tenant_tour_versions`, `catalog.*`) p95 | < 150 ms | [CHỜ PROBE] |
| CIS admin list / cost pages p95 | < 1 s | [CHỜ PROBE] |
| CIS job claim (advisory lock 650001) mean | < 20 ms | [CHỜ PROBE] |
| TripPlanner browse (`catalog.v_*`) p95 | < 300 ms | [CHỜ PROBE]; tín hiệu phía Lambda: Duration p95 theo giờ TB 1,7 s, max 11,8 s |
| TripPlanner assembly + outbox p95 | < 500 ms | [CHỜ PROBE] |
| Booking API (`trip_cases`, `customers`) p95 | < 100 ms | [CHỜ PROBE] |
| Connection saturation p95 | < 60 % `max_connections`, mỗi role < 80 % limit | **6,6 %**; mỗi role ≤ 33 % trừ `crm_app` 83 % (1 mẫu) |

Lưu ý quyền: `cis_app` **không** là thành viên `pg_read_all_stats`. Chạy probe qua ECS exec thì các dòng
`pg_stat_statements` của role khác vẫn có số đo nhưng **ẩn text và queryid**; `pg_stat_activity` của role khác thấy
role + `application_name` nhưng không thấy `state`. Muốn text đầy đủ: chạy cùng file qua DB Migrate `run-script`
(login master; `db_migrator` cũng có `pg_read_all_stats`). **Không đề xuất** cấp `pg_read_all_stats` cho `cis_app`:
role runtime khi đó đọc được text câu lệnh đang chạy của Booking / CRM (có thể chứa literal cá nhân) — trái DM-6.

Tín hiệu đã biết: S254 Booking #130 → 503 ở `/catalog/trip-plans` (đọc `catalog.v_tour_day` theo `source_id` từng dòng
vượt `command_timeout` 5 s; hotfix #131). Probe sẽ cho biết view `catalog.*` có còn p95 > 500 ms không (trigger
"Materialized catalog read model").

### (3) Bảng và index (dump N1 lúc 28/10 04:28 UTC + probe)

Tổng kích thước quan hệ ≈ **1,5 GB** (274 bảng). Theo schema: `shared` 740 MB, `geo` 361 MB, `acp_contract` 311 MB,
`silver_aa_internal` 29 MB, `acp_shared` 28 MB, `crm` 20 MB, `booking` 8,3 MB, `gold_aa_internal` 7,8 MB,
`tripplanner` 0,9 MB.

Top 10 theo kích thước (tổng = heap + index + toast):

| Bảng | ~dòng | Kích thước | Ghi chú |
|---|---:|---:|---|
| `shared.decision_log` | 427 684 | 443,7 MB | ledger Jev, chưa có retention |
| `geo.tour_place` | 13 356 | 215,5 MB | ~16 KB/dòng — bất thường; probe tách heap/index/toast **[CHỜ PROBE]** |
| `shared.llm_call_log` | 383 796 | 202,5 MB | ledger LLM, retention 180 ngày chưa chạy |
| `acp_contract.atom_embedding` | 10 674 | 175,2 MB | vector |
| `acp_contract.atom_ranking` | 97 368 | 66,6 MB | 13,5 M insert / 13,4 M delete: ghi lại toàn bảng mỗi lần recompute; seq scan 37,8k > idx scan 11,8k |
| `geo.tour_leg` | 96 123 | 65,9 MB | seq scan 2 756, idx scan 4 |
| `geo.tour_junction` | 222 234 | 55,1 MB | seq scan 1 252, idx scan 1 |
| `shared.tenant_api_usage` | 154 162 | 37,8 MB | retention 90 ngày chưa chạy |
| `acp_contract.tour_atoms` | 54 494 | 31,8 MB | dead 4 816 (8,8 %) |
| `shared.job` | 7 682 | 22,2 MB | ~3 KB/dòng (payload/result jsonb) |

Top 30 đầy đủ (kích thước + số dòng ước lượng): **[CHỜ PROBE]** dòng `[table_size]` / `[table_rows]`.

- **Dead tuples (C5.2b):** theo dump 28/10, **không bảng nào** có `n_dead_tup / n_live_tup > 20 %` với ≥ 100 dead.
  Cao nhất: `acp_contract.tour_atoms` 4 816 (8,8 %), `atom_segment_member` 1 257 (7,2 %), `atom_matches` 507.
- **Index không dùng (C5.2d):** 181 index (không PK/UNIQUE) 0 scan từ khi tạo instance (stats chưa reset, > 30 ngày),
  tổng **33,5 MB**. Lớn nhất `shared.idx_llm_call_log_model_created` 26,8 MB, `acp_shared.idx_content_piece_embedding`
  2,6 MB, `geo.tour_leg_countries_gin` 1,1 MB; còn lại ≤ 16 kB mỗi cái. Giá trị thu hồi thấp.
- **Cache hit** (`blks_hit / (hit + read)`): **[CHỜ PROBE]** dòng `[database]` (trigger r7g cần < 99 % cả tuần).

### (4) Ledger so với retention C5.4 / DM-7

| Ledger | Dòng (28/10) | Tăng 10/10 → 28/10 | Cửa sổ DM-7 | Tình trạng retention |
|---|---:|---|---|---|
| `shared.decision_log` | 427 684 | +199 503 (~11k/ngày; wave 23–26/10 ~42k/ngày) | "quyết trong N4" — chưa có | **chưa có job** |
| `shared.llm_call_log` | 383 796 | +172 984 (~9,6k/ngày) | raw 180 ngày + rollup ngày | **chưa có job** (dòng cũ nhất < 180 ngày? [CHỜ PROBE]) |
| `shared.tenant_api_usage` | 154 162 | +74 107 (~4,1k/ngày) | 90 ngày + rollup tháng | **chưa có job**; dòng quá 90 ngày [CHỜ PROBE] |
| `shared.job` | 7 682 | — | succeeded 30 / failed 90 ngày | prune `job_worker` có; `job` [CHỜ PROBE] |
| `booking.job` | 6 908 | — | như trên | **có** (AA-825, S251) |
| `crm.job` | 7 917 | — | như trên | [CHỜ PROBE] |

Dự báo chạm 1 M dòng (ngưỡng dừng C3 "Retention"): `decision_log` ≈ **19/12/2026** theo nhịp 18 ngày (sớm tới ~10/11 nếu
chạy wave cả catalogue như 23–26/10); `llm_call_log` ≈ **31/12/2026**. Dung lượng hai bảng này cộng lại ~650 MB — chưa
là vấn đề đĩa, nhưng là vấn đề số dòng/autovacuum và chi phí trang admin (aggregate trên `llm_call_log`).

### (5) Lambda (TripPlanner)

| Hàm | Reserved | Invocations 30 ngày | Throttles | Errors | Concurrency max | Duration p95 (theo giờ) |
|---|---:|---:|---:|---:|---:|---|
| `aa-tripplanner-dev-browse` | 15 | 21 067 | 16 157 (gần hết **trước 16/10**, thời quota 10); sau 16/10: **99** (1 giờ ngày 16/10) | 118 | **15** (chạm trần reservation) | TB 1,7 s, max 11,8 s |
| `aa-tripplanner-dev-assembly` | 5 | 969 | 14 (11 ngày 20/10) | 2 | 10 | max 14,6 s |

Quota account đã là 1000; concurrency account đỉnh 15. Lệch tài liệu: bảng C2.2 ghi reserved 10 / 10, Terraform live là
**15 / 5** (`connection_budget.json` đọc đúng Terraform: tổng role `tripplanner` 20 / limit 30, vẫn ổn).

### (6) Job backlog theo owner (CloudWatch `AA/Jobs/*`, tới 16/10 mới có)

- CIS `shared.job`: tuổi job queued tới hạn lâu nhất **1 407 s** (một mẫu 16/10 ~17:00 UTC, > 15′); còn lại p95 2 s.
  `OverdueRunningJobs` = 0 suốt kỳ.
- Booking `booking.job`: **một mẫu 5 phút 38 746 s** (≈ 10,8 giờ) lúc 24/10 ~03:10 UTC, alarm `queue-age` ALARM 10′ rồi OK;
  mọi mẫu khác 0. Nguyên nhân chưa xác nhận (nhiều khả năng một job có `run_after` cũ được thấy đúng lúc worker
  vừa khởi động lại) — xem D8.
- Thời lượng job theo kind 30 ngày (p50/p95, số lỗi): **[CHỜ PROBE]** dòng `[job_cis_kind_30d]`.

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
| t4g.medium → m7g.large | > 5 câu primary-path mean > 200 ms | [CHỜ PROBE] | chưa áp dụng (chưa ở medium) |
| m7g → r7g | cache hit < 99 % một tuần; `FreeableMemory` < 10 % RAM | cache [CHỜ PROBE]; min 257 MB = 12,5 % RAM | không bắn (bộ nhớ) |
| Storage | dùng > 80 % `max_allocated_storage`, hoặc tăng > 1 GB/ngày một tuần | 4,5 %; 0,09 GB/ngày | không bắn |
| Retention (hard stop) | bảng log > 1 M dòng, hoặc `FreeStorageSpace` < 10 GB trước khi retention có | max 428k; 15,3 GB | **chưa bắn — dự kiến giữa–cuối 12/2026** |
| RDS Proxy | Lambda cần > 20; `DatabaseConnections` p95 > 60 % một tuần | 15 + 5 reserved; 6,6 % | không bắn |
| Materialized catalog read model | một view `catalog.*` p95 > 500 ms | [CHỜ PROBE]; sự cố #130 S254 là tín hiệu | chờ probe |
| Read replica | đọc > 30 % CPU primary hoặc CPU > 60 % kéo dài | CPU TB 4,8 % | không bắn |
| Partitioning | bảng > 10 M dòng / > 5 GB; DELETE retention > 5′; dead > 20 % | max 428k / 444 MB; dead max 8,8 % | không bắn |
| App split (Booking riêng) | DB > 200 GB; conn p95 > 70 %; Booking p95 ×2 trong wave ≥ 2 lần/tháng | 1,5 GB; 6,6 %; Booking [CHỜ PROBE] | không bắn |

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

1. **Ledger CIS không có retention** (`decision_log`, `llm_call_log`, `tenant_api_usage`, `shared.job`): chạm ngưỡng
   1 M dòng trong ~7–9 tuần, sớm hơn nếu có wave; cửa sổ của `decision_log` còn chưa quyết (DM-7 "quyết trong N4").
2. **Ngân sách kết nối trên giấy vượt trần** (168 / 135) với hạn chấp nhận 15/12 — một deploy chồng lúc autoscale max có
   thể đẩy `cis_app` tới limit 90 (backstop là lỗi kết nối trên task mới, không sập instance).
3. **`crm_app` không có alarm per-role** và pool thiết kế bằng đúng limit (3 × 2 = 6): mỗi deploy CRM chạm 83–100 %.
4. **Đọc `catalog.*` chậm** (Booking #130 S254; Lambda browse p95 1,7 s): chờ số probe để chấm trigger materialized
   read model.
5. Nhỏ: phiên không `application_name` (C1.1a); `atom_ranking` ghi lại toàn bảng mỗi recompute; `geo.tour_place`
   16 KB/dòng; một mẫu queue-age Booking 10,8 giờ chưa rõ nguyên nhân; alarm đĩa 50 % sẽ kêu ~cuối 12 dù còn
   autoscale tới 100 GB.

## 4. Danh sách quyết định (C8c) — đề xuất, chờ Nghiệp duyệt

| # | Quyết định đề xuất | Loại | Hàng C3 / quy tắc | Ai / chi phí |
|---|---|---|---|---|
| D1 | Giữ `db.t4g.small`, không resize | no action | t4g.small → medium: cả 3 trigger đo được không bắn | — / 0 |
| D2 | Thu pool chính `cis-api` 10 → 5 trước 15/12 (theo baseline `aa859_main_pool_gauge`), cập nhật `connection_budget.json` + bảng C2.2 cùng PR, gỡ 2 `accepted_overages` | tune | t4g.small → medium, dòng "C2.2 total > 75 %"; C3b (pool budget trước resize) | CIS + Infra, S / 0 |
| D3 | Làm retention CIS (N4) cho `llm_call_log` (180 ngày), `tenant_api_usage` (90 ngày), `shared.job` (30/90) và **chốt cửa sổ `decision_log`**; archive Parquet trước khi xoá (C5.4a), DRY RUN lần đầu. Đề xuất cửa sổ `decision_log` = 180 ngày (bằng ledger LLM) | tune | "Retention" (hard stop 1 M dòng) | CIS, M / S3 vài cent. **Cần issue Linear mới — hỏi Nghiệp trước khi tạo** |
| D4 | Thêm alarm `aa-cis-dev-rds-role-connections-crm_app` (RoleConnectionLimitPct > 80 %), cân nhắc nâng limit `crm_app` 6 → 8 bằng file `roles/` nếu alarm kêu mỗi lần deploy | tune | C4.1 "mỗi role có limit một alarm" | Infra, XS / ~0,10 USD/tháng |
| D5 | Sửa bảng C2.2 trong `03-scaling.md`: TP reserved concurrency live 15 / 5 (không phải 10 / 10) | docs | C2.3c | root, XS / 0 |
| D6 | Đưa probe vào AA-CIS-Infra `db/scripts/aa838_capacity_probe.py` (đã qua shape check `--inspect-script`) để mỗi tháng chạy bằng `run-script` có text đầy đủ; tuần dùng PI + probe ECS exec | tune | C4.3, C8b | Infra, XS / 0 |
| D7 | Không chạy `pg_stat_statements_reset()` tháng này: số liệu mới từ 15/10 (~2 tuần), giữ để so tháng sau | no action | C4.3a | — |
| D8 | Tra mẫu queue-age Booking 24/10 bằng run-script chỉ đọc trên `booking.job` (job tạo trước 03:00 UTC, bắt đầu sau 03:05 UTC) | investigate | C4.1 job backlog | Booking/Infra, XS / 0 |
| D9 | Đặt `application_name` cho kết nối ad hoc của CIS (script ECS exec, `asyncpg.connect` lẻ) | tune | C1.1a | CIS, XS / 0 |
| D10 | Theo dõi, chưa làm: `atom_ranking` (ghi đè thay vì xoá + chèn), `geo.tour_place` (xem toast sau probe), 181 index không dùng (33 MB, giá trị thấp; nếu bỏ thì bắt đầu với `idx_llm_call_log_model_created` sau khi kiểm trang cost theo model) | no action | C3b (query/index trước), C5.2d | — |
| D11 | Alarm đĩa `< 50 %` (10 GB trống) sẽ kêu ~cuối 12: giữ nguyên làm cảnh báo sớm, xem lại ở rà soát tháng 12 | no action | C4.1 | — |

## 5. Nhịp rà soát (AA-838)

| Nhịp | Quy tắc | Khi nào | Làm gì | Lưu ở đâu |
|---|---|---|---|---|
| **Tuần** | C4.3, C1.2a | Phiên đầu mỗi tuần ISO, và sau mỗi wave | PI top SQL / wait (7 ngày, miễn phí) + probe ECS exec phần `[pgss_*]` / `[sli]` / `[locks]`; slow log > 500 ms và lock wait trong log group `postgresql`. Một SLI trượt 2 tuần liên tiếp → báo Nghiệp kèm câu lệnh + cách sửa | 1 đoạn "C4.3 tuần W<nn>" trong log phiên |
| **Tháng** | C8a–C8c, FIN-02 = OPS-08 | Phiên đầu mỗi tháng (và sau wave làm ledger ×2) | 9 mục C8b theo trang này: chạy `scripts/gen_cw_queries*.py` + `analyze_cw.py` (đổi START/END), PI, probe qua `run-script`, `check_connection_budget.py`, số chi phí từ báo cáo chi phí tháng; kết bằng danh sách quyết định | `docs/audits/<date>-S<nnn>-capacity-review/` + root PR |
| **Quý** | DM-8.10 | Phiên đầu mỗi quý | Role, grant, default ACL, IAM đọc secret DB, user Cognito `aa-workforce`. Lần đầu đã làm S245 (`docs/audits/2026-10-20-S245-access-review/`); lần sau: phiên đầu 2027-Q1 | `docs/audits/<date>-S<nnn>-access-review/` |

Nhịp đã ghi vào `skill/aa-session/SKILL.md` (bước 6 đầu phiên) và một dòng trỏ trong `.kiro/steering/session-workflow.md`
(cùng PR với trang này).

## 6. Cách tái tạo / việc của phiên điều phối

- `scripts/capacity_probe.py` — chỉ đọc, hai cách chạy, mọi dòng bắt đầu bằng `PROBE`:
  1. ECS exec trong container `api` của `aa-cis-dev-api` (login `cis_app`, `DATABASE_URL` của container), theo pattern
     S3-mediated: tải lên `scripts/aa838_capacity_probe.py` trong bucket bronze, presign, rồi chạy
     `sh -c 'curl -s "$URL" -o /tmp/p.py && PROBE_TOP=50 python3 /tmp/p.py'`. `PROBE_TOP=50` = snapshot top 50 (C4.3a).
  2. DB Migrate `mode=run-script` sau khi copy vào Infra `db/scripts/` (D6) — có text đầy đủ của mọi role.
- `scripts/gen_cw_queries.py`, `scripts/gen_cw_queries2.py` → `aws cloudwatch get-metric-data --cli-input-json
  file://cw_in.json …` (lệnh một dòng), rồi `scripts/analyze_cw.py`. Kết quả lần này: `cloudwatch-summary.txt`
  (giờ hiển thị theo +07).
- PI: `aws pi describe-dimension-keys` (group `db.application`, `db.user`, `db.wait_event`, `db.sql_tokenized`) và
  `aws pi get-resource-metrics` (`db.load.avg`, chu kỳ 300 s), cửa sổ 7 ngày.

## 7. Phụ lục — điền sau khi chạy probe

```text
[CHỜ PROBE] dán các dòng PROBE [header] [setting] [database] [schema] ở đây
[CHỜ PROBE] [table_size] top 30, [table_rows] top 30, [bloat], [index_size], [unused_index]
[CHỜ PROBE] [ledger], [job_cis], [job_cis_kind_30d]
[CHỜ PROBE] [conn], [conn_app], [conn_role], [long_xact], [locks]
[CHỜ PROBE] [pgss], [pgss_role], [pgss_total], [pgss_mean], [pgss_role_total], [pgss_role_mean], [sli]
```
