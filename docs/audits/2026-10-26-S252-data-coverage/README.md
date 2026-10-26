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
| `crm.ops.v1` 1.4 | audit: một event platform hoặc không | không ghi event vào audit từng đại lý; log 1 dòng mỗi lần gọi | Không có bảng audit cấp platform; giống `/jobs/summary` |
| `rank.markets` | "Of 6" | mẫu số = số market có search demand | critic mục 4 |
| T0 | mọi tenant active | trừ tenant `is_canary` (dòng `ten.canary` riêng) | critic mục 5 |
| `master.active` | expected = review + never written + failed | expected = review queue | critic mục 1: bản cũ không bao giờ đỏ |
| `tp.pins_served` | must | info; `tp.pins_dangling` là dòng must | critic mục 2 |
| Kiểu "phải bằng" | — | polarity `equal` (missing = abs(mẫu − số)) | `tp.tours`, `crm.cache_served` |
| Pin của TripPlanner (review vòng 2) | `v_ops_pin_components` lấy `payload->>'component_id'` | chỉ id dạng UUID (viết thường); id khác đếm vào `pin_events_invalid_id`, không liệt kê | Lambda ghi `component_id` của request không kiểm; tránh text của khách lọt ra `cis_app`, dòng mới `tp.pins_invalid_id` |
| Lỗi tạm thời (review vòng 2) | `unavailable` cho mọi lỗi catalog / CRM | `unavailable` chỉ khi chắc chắn (`contract_view_missing`, `cognito_session_required`, không có tenant pool); gate bận, rớt kết nối, CRM khác 200 là `error` (cache 60 s, không thành last good); 4 nguồn catalog chạy lần lượt; hết hạn tier chỉ huỷ nguồn còn chạy | Tránh n/a bị cache 10 phút / 24 h vì lỗi thoáng qua (D7) |
| Module định nghĩa chung (Q10) | CIS `defs.py` + bản copy Infra, probe AA-991 import | chỉ có `defs.py` ở CIS | Bản copy Infra + sửa probe là việc riêng, chờ chốt Q10 |

Runbook merge / DB Migrate / deploy / verify: `.tmp-session/s252/datacov/RUNBOOK.md` (agent điều phối).
