# S252 — snapshot trạng thái live lúc chốt phiên (27/10/2026 ~05:10Z)

Tác nhân: Claude Code. Số liệu đọc trực tiếp (AWS CLI, endpoint, GitHub, Vercel MCP, ECS exec role `cis_app`), không chép từ trí nhớ.

## AWS / ECS (acc2, us-west-1, cluster `aa-cis-dev-cluster`)

| Service | Task def đang chạy | Revision mới nhất | Image | Running/desired | Rollout |
|---|---|---|---|---|---|
| aa-cis-dev-api | aa-cis-dev-api:855 | :855 | dev-d1409c6d | 1/1 | COMPLETED |
| aa-cis-dev-worker | aa-cis-dev-worker:421 | :421 | dev-d1409c6d | 1/1 | COMPLETED |
| aa-booking-dev-api | aa-booking-dev-api:62 | :62 | 759732a4 | 1/1 | COMPLETED |
| aa-crm-dev-api | aa-crm-dev-api:61 | :61 | 78d0abf4 | 1/1 | COMPLETED |
| aa-crm-dev-web | aa-crm-dev-web:30 | :30 | 7bd2bb08 | 1/1 | COMPLETED |

- api và worker CIS cùng SHA `d1409c6d`. Revision mới nhất của mỗi family = revision đang chạy (Terraform apply 04:38Z đã được deploy 04:57Z lấy).
- Env mới: `PLACE_PIPELINE_AUTO=on` trên api:855 và worker:421 (Infra #425). `SEGMENT_GC_MODE=apply` (đã có từ trước).
- EventBridge Scheduler nhóm `aa-cis-dev-acp`: còn 5 schedule (booking-uptime, rds-snapshot-expiry-daily, dfs-balance-check-daily, retention-daily, photo-sync-daily). 3 schedule chết (acp daily ingest / weekly export / veto window close) đã xoá.

## Endpoint

| App | Health | Ready |
|---|---|---|
| CIS api | 200, 0.11.0, `d1409c6d` | 200, db ok, **schema 288** (required 287) |
| Booking api | 200, 0.7.0, `759732a4` | 200, schema `bk-026` |
| CRM api (partner-dev) | 200, 0.5.0, `78d0abf4` | 200, schema `crm-021`, membership feed ok, keys kms |
| CRM web (partner-dev /healthz) | 200, 0.5.0, `7bd2bb08` | — |
| TripPlanner web | 200, 0.8.2, `f61a7485` | — |

## Migration mới nhất mỗi owner
CIS 288 (`raw_tours.country` → FK `shared.countries`, áp 04:12Z run 40448250177) · Booking bk-026 · CRM crm-021 · TripPlanner tp-020.
Bản dump `db-schema-reference.md` sau 288: root PR #278 đã merge.

## Vercel production (commit đang phục vụ)
- aa-cis-frontend: `d1409c6d` (#1058, tab Merges).
- aa-booking-admin: `e5d36dbe` (#103).
- aa-tripplanner: `f61a7485` (#161). Main TP đã ở `4b089499` (#162 chỉ đổi hook/CI, không build web).
- aa-cis-portal: không deploy mới trong 12 giờ cuối (lần cuối 26/10).

## Bảng job và wave
- `shared.job`: 0 running, 1 queued nhưng `run_after` > 1 giờ (job hẹn giờ, không chặn deploy).
- `shared.rerun_wave`: 1 dòng chưa ở trạng thái đóng (không có wave chạy; ghi để S253 xem lại trạng thái dòng này).
- Chi phí LLM từ 25/10 00:00Z (`shared.llm_call_log`): **$54.93**.

## Repo (nhánh mặc định, PR còn mở)
| Repo | Head | PR mở |
|---|---|---|
| AA-Ecosys | sau #278/#279 (bot docs) | PR chốt phiên S252 (sắp mở) |
| AA-CIS-App | `d1409c6d` | #1049 release-please 0.12.0 |
| AA-Booking | `e84d8c1a` | #96 dependabot, #95 release-please 0.8.0 |
| AA-TripPlanner-Web | `4b089499` | #157 dependabot, #155 release-please 0.9.0 |
| AA-Partner | `5a6de8b6` | #64 release-please 0.6.0 |
| AA-CIS-Infra | `55147d32` | #412, #411 dependabot |

Chỉ còn PR của bot (release-please, dependabot). Không có PR việc nào của phiên còn mở.

## Probe độ tươi (enforce, sau đợt chữa)
Run Infra `DB Freshness Probe` sau 04:57Z: **đỏ** với 3 chỉ số stale đã quá 24 h:
- `tours_with_place_atoms_but_no_segment` 9: recompute chạy OK vẫn không có segment, cần đọc logic.
- `angle_gate_requests_on_inactive_atoms` 8: 5 trỏ lại được bằng luật đã deploy, 3 không có atom thay thế.
- `dead_member_rows` 10.495: dọn theo quy trình destructive.

Đã khỏi: `orphan_segments` 3 → 0; `place_card_links_missing` 330 → 32 (0 quá 24 h).
`ENFORCE` trong `db/freshness_gate.py` vẫn `False`; bật sau khi 3 chỉ số trên về 0.

## Thứ cố ý để BẬT cho phiên sau
- `PLACE_PIPELINE_AUTO=on` (mới): tour mới hoặc đổi tự có địa điểm, khoảng $0.006–0.019 mỗi nguồn.
- Writing memory release 0 active cho 4 writer, memory on (AA-919).
- Route place card `gpt-6-luna` × Haiku 4.5 (AA-784).
- Writer S1 v2 + `s1_generate` = sonnet-5-5 (mặc định cố định từ S250).
