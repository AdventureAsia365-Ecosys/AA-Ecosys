
# S276 — trạng thái live cuối phiên

Lấy lúc 15:01Z ngày 10/11/2026 (22:01 +07), acc2, us-west-1. Chỉ tên và số, không account ID, ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster)

Mọi service 1/1, rollout COMPLETED. Revision mới nhất của mỗi family = revision đang chạy.

| Service | Task def | Ghi chú |
|---|---|---|
| aa-cis-dev-api | :1086 | image `987dccdc` (CIS #1426) |
| aa-cis-dev-worker | :654 | cùng SHA với api; env `S1_CONTROL=contract`, `T2_ORCHESTRATOR=linear`, `T9_SEO_BUILDER=on` |
| aa-cis-dev-admin | :19 | |
| aa-booking-dev-api | :112 | không đổi trong phiên |
| aa-booking-dev-admin | :11 | |
| aa-crm-dev-api | :149 | |
| aa-crm-dev-web | :127 | web `f166946f` (Partner #265) |
| aa-tripplanner-dev-web | :6 | web `245595cb` (không đổi) |

## Health và migration

| Endpoint | Kết quả |
|---|---|
| CIS `/health/ready` | ok, schema 395, git `987dccdc`; key 336 đã đăng ký (D8) |
| Booking `/booking/health/ready` | ok, bk-044 |
| CRM `/crm/health/ready` | ok, crm-051 |
| CRM web `/healthz` | ok, `f166946f` |
| TripPlanner `/api/health` | ok, `245595cb` |
| TripPlanner DB | tp-028 (FORCE RLS) đã áp, run 42803155123 |

- `DB_AUTO_APPLY_CONTRACT` (AA-CIS-Infra) = `true` từ 12:11Z.
- DB Isolation Probe run 42803939499: 99/99 ô đạt.

## Bảng job và wave

- `shared.job`: không còn job queued; lúc 13:18Z chỉ có `recompute` và `place_dedupe` đang chạy (việc nền).
- Wave: 0 đang mở. Wave smoke S1 `80102e97` đã đóng 13:52Z.
- `booking.job` 0; `crm.job` chỉ job định kỳ (đầu phiên).

## AI gateway (21:28 +07)

- Chi tiêu tháng 11 (không tính shadow): 26,45 USD.
- anthropic-direct 22,63 / 150 USD; openai-direct 0,75 / 10; acc3 0,97 / 100 (7 model vẫn bị từ chối, tính là refusal dự kiến); acc2 0,09.
- Route control v7. Không có connection mới báo lỗi.

## Cố ý để BẬT

- Worker: `S1_CONTROL=contract` (AA-1049, bật sau replay + smoke), `T2_ORCHESTRATOR=linear`, `T9_SEO_BUILDER=on`.
- CIS: luật tour ngừng bán mặc định chỉ báo; `auto_draft` tắt cho mọi đại lý.
- Allowlist Jev: rỗng.

## Dữ liệu thử để lại trên Dev

- Bài drill AA-1039 `804a822e` trên site WordPress thử: đã đăng lại (online) sau drill; tour key `66a568bd` đang bán bình thường.
- Bài drill thứ nhất (piece `05384b74`, publish `37498801`) vẫn online trên site thử.
- CRM đại lý thử Sen Vàng: một phiên bản đề xuất nháp v2 (chưa gửi); các lần huỷ chỉ chạy thử (dry run).
- TripPlanner: 2 chuyến khách thử (không có dữ liệu cá nhân).
- Writing Lab: 417 câu t2@2 trong hàng duyệt, có đề xuất của panel.

## PR còn mở lúc snapshot

- AA-Partner #266 (bảng phí huỷ mặc định khớp 3A): trong merge queue.
- Release Please: CIS #1179, Booking #161, TripPlanner #196, Partner #133 (để nguyên).
- Booking #200 (bk-045, draft, hạn từ 28/11).
- Repo gốc: PR chốt phiên này.
