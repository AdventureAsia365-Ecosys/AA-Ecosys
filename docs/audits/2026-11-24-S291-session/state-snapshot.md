# S291 — snapshot trạng thái thật lúc chốt phiên (25/11/2026 ~03:40 +07)

Tác nhân: Claude Code. Chỉ tên và số; không account ID, ARN hay giá trị secret.

## STS / MFA
- STS acc2 OK (profile aa365-admin). Phiên MFA hết hạn 06:52 +07 (25/11).

## ECS (cluster aa-cis-dev-cluster) — revision đang chạy = revision mới nhất của family
| Service | Running | Rollout | Task def |
|---|---|---|---|
| aa-cis-dev-api | 1/1 | COMPLETED | :1276 |
| aa-cis-dev-worker | 1/1 | COMPLETED | :845 |
| aa-cis-dev-admin | 1/1 | COMPLETED | :101 |
| aa-booking-dev-api | 1/1 | COMPLETED | :175 |
| aa-booking-dev-admin | 1/1 | COMPLETED | :67 |
| aa-crm-dev-api | 1/1 | COMPLETED | :219 |
| aa-crm-dev-web | 1/1 | COMPLETED | :191 |
| aa-tripplanner-dev-web | 1/1 | COMPLETED | :29 |

## Endpoint (git_sha)
- CIS `/health` + `/health/ready`: ok, `df33eb9b`, schema 483 (api và worker cùng SHA).
- CIS admin `/api/healthz`: ok, `64242ba4` (hotfix ToastProvider #1679).
- Booking `/booking/health` + `/ready`: ok, `591d7397`, bk-075. Booking admin `/api/healthz`: `caa80a41`.
- CRM api `/crm/health` + `/ready` (host portal.): ok, `4471854c`, crm-088. CRM web `/healthz`: `4471854c`.
- TripPlanner web `/api/health`: ok, `aa78d945`; Lambda browse `/api/browse?resource=countries` 200.

## Migration mới nhất mỗi owner
- CIS 483 (áp trong phiên: 480, 481, 482, 483), Booking bk-075 (áp trong phiên), CRM crm-088 (áp trong phiên), TripPlanner tp-037 (không đổi).
- Root #991 (bot db-schema-reference) merged `16354ec7`.

## Bảng job / wave
- `shared.job` 0 queued/running; `booking.job` 0; `crm.job` 3 job định kỳ queued (crm_booking_sync, crm_heartbeat, crm_membership_pull — bình thường). Không có wave mở.

## PR còn mở (cố ý)
- **Giữ tới sau buổi thứ Năm 26/11 (draft):** Booking #331, CIS #1676 — đặt tên savepoint theo độ sâu cho mọi pool (chạm luồng duyệt TK ngân hàng / publish hai người lúc runtime).
- Release-please tuần W49: CIS #1645, Booking #302, Partner #380, TripPlanner #295 (merge đầu tuần W49).
- Dependabot actions bump: root #958, CIS #1638, Booking #330, Partner #383, TripPlanner #293, Infra #977; CIS #1586 (frontend-security); bot kit-sync Booking #276, Partner #355; CIS #1467 test durations; Booking #200 (bk-045 destructive, ≥28/11); Infra #935 (AA-1111, chờ TOTP chủ DN).

## Cố ý để BẬT / đã đổi cấu hình
- TripPlanner: ruleset `main: merge queue (AA-1119)` active + strict required checks (bật 24/11 bằng gh của tech lead, đã được cho phép).
- Không cờ wave nào đang bật. Hai công tắc hai người (`cis.content.publish_two_person`, `cis.settings.two_person_approval`) vẫn TẮT, giữ cho buổi thứ Năm.
- Dữ liệu SYNTHETIC close-out S290 giữ nguyên (SUP-000019 TK ngân hàng pending; chi BIL-000002 vẫn 409 `bank_account_pending`, kiểm 24/11 sau deploy Booking).

## Lệch đã xử lý trong phiên
- Catalogue lịch đỏ (5 setting compliance S290 thiếu trong surface snapshot) → root #990.
- TripPlanner deploy job Visual đỏ từ #298 (planner sập khi add-on trả sai dạng) → TP #303, Visual xanh.
- Trang Ecosystem status sập sau deploy AA-1141 (`useToast` ngoài `ToastProvider`) → CIS #1679, trang render lại.
