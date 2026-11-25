# S294 — trạng thái live cuối phiên (26/11/2026 ~03:15 +07)

Nguồn: lệnh một dòng chạy lúc chốt phiên (ECS describe-services, curl health, ECS exec đếm job, gh). Không ghi account ID, ARN hay secret.

## ECS (cluster aa-cis-dev-cluster) — 8/8 running = desired, rollout COMPLETED; revision đang chạy = revision mới nhất của family

| Service | Task def | Image / git sha (health) |
|---|---|---|
| aa-cis-dev-api | :1299 | ba5d2ffc (CIS #1715) |
| aa-cis-dev-worker | :868 | cùng image api |
| aa-cis-dev-admin | :109 | 9fba482f (CIS #1714) |
| aa-booking-dev-api | :176 | 8844fd00 (Booking #332, build lại --pull) |
| aa-booking-dev-admin | :70 | b89f18f4 (Booking #334) |
| aa-crm-dev-api | :225 | 10d1f134 (Partner #402) |
| aa-crm-dev-web | :195 | 10d1f134 |
| aa-tripplanner-dev-web | :32 | 4d6919e7 (TripPlanner #306) |

## Endpoint
- CIS `/health` + `/health/ready` 200 (schema 494); Booking `/booking/health` + `/ready` 200 (bk-075); CRM `/crm/health` + `/ready` 200 (crm-090), CRM web `/healthz` 200; TripPlanner `/api/health` 200 (`application/json; charset=utf-8`); CIS admin `/api/healthz` 200.
- Migration mới nhất: CIS 494, bk-075, crm-090 (crm-089 + crm-090 áp trong phiên), tp không đổi.

## Bảng job, wave, cờ
- `shared.job` 0 queued/running (03:10). Không có wave. Job CRM `crm_calendar_push` chạy ok (error_count 0).
- Cố ý để BẬT: `cis.llm.fact_instruction_guard` = On (tech lead 19:44, D1). `cis.content.publish_two_person` vẫn tắt (bật trong buổi họp 26/11).
- Dữ liệu demo: tour tay SYNTHETIC 3 ngày (draft, SUP-000019) cho buổi họp.
- Ngoại lệ ảnh WordPress test-wp (libzstd1) hết hạn 02/12: phải đổi digest khi upstream có bản vá.

## Guard + CI
- Guard theo lịch: 0 đỏ / 43 (Catalogue, Image Scan được đánh dấu superseded bởi lượt chạy tay xanh).
- CI trên main: CIS, Booking, Partner, TripPlanner xanh. Image Scan chạy tay 25/11 gate passed; ZAP chạy lại 00:19 (0 High).
- WAF: request không User-Agent → 403 kèm 4 header bảo mật, 1 dòng HSTS (Infra #1038, #1040 đã apply).

## PR còn mở (cố ý)
- Nháp ship sau buổi họp 26/11: CIS #1713 (AA-1181 a), #1709/#1710 (gỡ t10_claims, chờ AA-1169), #1676 + Booking #331 (savepoint), Partner #403 (cookie __Secure-), Infra #1041 (luật mật khẩu pool partner), Booking #200 (≥28/11).
- Giữ tới tuần W49 / sau họp: release PR (CIS #1645, Booking #302, Partner #380, TripPlanner #295), kit sync (Booking #276, Partner #355), Dependabot actions (CIS #1638, Booking #330), CIS #1467 (test durations), Infra #935 (chờ MFA admin).
- Nháp AA-1061 (≥ 28/11, sau khi tech lead duyệt pins DRY RUN): Booking #336 (bk-076), Infra #1042, CIS #1717, Infra #1043.
- Đã đóng: CIS #1586 (thay bằng #1705), Booking #200 (thay bằng #336).
- Sau snapshot: CIS #1716 merged `bd910ac3` (chỉ test, không deploy).
