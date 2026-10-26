# S252 — Trang "Data coverage" (AA-992): thiết kế, critic và chỗ bản build khác thiết kế

Yêu cầu (Nghiệp, S252): một trang admin, chỉ số liệu, cho cả hệ thống, để soát chỗ thiếu dữ liệu từ input (Excel tour,
file brand) tới raw, S1, Master, atom, segment, …, T-series, tenant, TripPlanner, Booking, CRM.

- [design.md](design.md) — thiết kế đã sửa theo critic (tiếng Anh, kỹ thuật).
- [critic.md](critic.md) — 12 lỗi chặn (đã sửa trong design) + 7 mục nhỏ.

## Bản build khác thiết kế ở đâu

| Chỗ | Thiết kế | Bản build | Vì sao |
|---|---|---|---|
| tp-020 | 2 view, `v_ops_pin_components (component_id, mapped_id, trips)` | 3 view: `v_ops_pin_components (component_id, trips)` + `v_ops_component_id_map (old_id, new_id)` | Từ AA-990 TripPlanner đi chuỗi map → redirect → map tới 5 bước; một bước `mapped_id` không tái tạo được chuỗi đó. Grant cho `cis_app` thành 5 (không phải 4) |
| Lý do drop "insert failure" | một dòng / lý do | gộp thành `in.drop.insert_failed` | Lý do insert failure là text exception (có thể chứa tên tour): chỉ đếm |
| `crm.ops.v1` 1.3 | audit: một event platform hoặc không | không ghi event vào audit từng đại lý; log 1 dòng mỗi lần gọi | Không có bảng audit cấp platform; giống `/jobs/summary` |
| `rank.markets` | "Of 6" | mẫu số = số market có search demand | critic mục 4 |
| T0 | mọi tenant active | trừ tenant `is_canary` (dòng `ten.canary` riêng) | critic mục 5 |
| `master.active` | expected = review + never written + failed | expected = review queue | critic mục 1: bản cũ không bao giờ đỏ |
| `tp.pins_served` | must | info; `tp.pins_dangling` là dòng must | critic mục 2 |
| Kiểu "phải bằng" | — | polarity `equal` (missing = abs(mẫu − số)) | `tp.tours`, `crm.cache_served` |
| Module định nghĩa chung (Q10) | CIS `defs.py` + bản copy Infra, probe AA-991 import | chỉ có `defs.py` ở CIS | Bản copy Infra + sửa probe là việc riêng, chờ chốt Q10 |

Runbook merge / DB Migrate / deploy / verify: `.tmp-session/s252/datacov/RUNBOOK.md` (agent điều phối).
