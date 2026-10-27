# AA-990 N4: kiểm lại live luật "pin ≥ một nửa số ngày" cho route `tour_graph`

Ngày 27/10/2026 (S253). Tác nhân: Claude Code. Chi phí $0, chỉ đọc API browse công khai.

## Bối cảnh

Sweep catalogue S252 (`2026-10-26-S252-aa990-parity/catalogue-sweep.json`) gắn cờ `PIN_BELOW_HALF` cho 137 tour: route có, nhưng pin chưa tới một nửa số ngày. Trong đó 42 tour vẫn được xếp OK; đó là mục N4. Luật S236 ("route phải pin ≥ 50% số ngày") lúc ấy chỉ áp cho `match: places`.

Bản sửa F2 đã có trên TripPlanner main (`backend/browse/routes.py`, `tour_route`):
- Route `tour_graph` dưới ngưỡng phải nhường cho route `places` nếu route đó pin nhiều ngày hơn.
- Nếu không có route nào đạt, API trả `match: none` và planner hiện danh sách ngày.

## Kết quả (`live.json`, gọi `/api/browse?resource=tour-route` cho cả 137 tour)

| Nhóm S252 | `tour_graph` (≥ 50%) | `places` (≥ 50%) | `none`: hiện danh sách ngày | Còn dưới ngưỡng |
|---|---|---|---|---|
| 42 tour "OK" (N4) | 17 | 12 | 13 | **0** |
| 95 tour khác có cờ | 45 | 24 | 26 | **0** |
| **Tổng 137** | 62 | 36 | 39 | **0** |

Không tour nào còn route pin dưới một nửa số ngày. Cả 137 lời gọi đều trả 200.
