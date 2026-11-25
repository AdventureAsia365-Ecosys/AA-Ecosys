# S292 — trạng thái thật lúc chốt phiên (25/11/2026, ~12:00 +07)

Tác nhân: Claude Code. Số liệu lấy từ lệnh kiểm live trong phiên (ECS, health, ECS exec chỉ đọc), không chép từ trí nhớ.

## AWS / MFA

- STS acc2 OK. MFA aa365-admin hết hạn 18:44 +07 (nhập lại lúc ~06:55 sáng nay).
- Máy local OOM một lần ~11:50 (WSL khởi động lại): không mất dữ liệu; các lệnh chạy nền bị ngắt đã chạy lại.

## ECS (revision đang chạy = revision mới nhất của family, rollout COMPLETED, 1/1)

| Service | Task def | Image |
|---|---|---|
| aa-cis-dev-api | :1288 | dev-794eea54 |
| aa-cis-dev-worker | :857 | dev-794eea54 (cùng SHA api) |
| aa-cis-dev-admin | :103 | dev-ed236b6d |
| aa-booking-dev-api | :175 | 591d7397 (không đổi trong phiên) |
| aa-booking-dev-admin | :69 | caa80a41 (deploy lại cho sidecar WordPress test digest mới, app không đổi) |
| aa-crm-dev-api | :220 | 1f7c0136 |
| aa-crm-dev-web | :191 | 4471854c (không đổi) |
| aa-tripplanner-dev-web | :29 | aa78d945 (không đổi) |

## Health

- CIS `/health/ready` 200, schema 489, git 794eea54.
- Booking `/booking/health/ready` 200, bk-075. CRM `/crm/health/ready` 200, crm-088. TripPlanner `/api/health` 200, aa78d945.

## Migration áp Dev trong phiên

CIS 484 (AA-1169), 485–486 (AA-1142), 487 (AA-1154 A1), 488 (status noise), 489 (AA-1178). Không migration Booking / CRM / TP.

## Bảng job

- `shared.job`: 0 queued/running lúc chốt. `booking.job` / `crm.job`: không đọc được bằng role `cis_app`; không có deploy hay job mới trên Booking/CRM sau S291.
- Không wave, không cờ wave đang bật.

## Repo (head nhánh mặc định, PR còn mở)

| Repo | Head | PR mở |
|---|---|---|
| root | b7fb009e (+ root PR chốt phiên) | — |
| AA-CIS-App | 794eea54 | #1676 (draft, savepoint, giữ tới sau thứ Năm), #1645 (release W49), #1638 (dependabot), #1586 (frontend-security, sau thứ Năm), #1467 (bot durations) |
| AA-Booking | caa80a41 | #331 (draft, savepoint), #330 (dependabot), #302 (release W49), #276 (kit sync, sau thứ Năm), #200 (draft, destructive) |
| AA-Partner | 1f7c0136 | #380 (release W49), #355 (kit sync) |
| AA-TripPlanner-Web | 9bcbb88d | #295 (release W49) |
| AA-CIS-Infra | 377d51f6 | #977 (dependabot, chờ rebase), #935 (WAF geo / MFA, sau thứ Năm) |

## AI gateway (tháng 11)

- anthropic-direct 40,40 / 150 USD; openai-direct 8,25 / 25 USD; acc1 0,29 / 95; acc3 1,07 / 100 (7 model vẫn bị AWS từ chối).
- LLM trả phí trong phiên: ~1,42 USD (lượt đo AA-1169 w5-t9-r2) + 0,00085 USD (một lần Analyse AA-1154).
- Catalog: `opus-4-5` Off (tech lead bấm 09:10, sau email AWS deprecation).

## Cố ý để BẬT cho phiên sau

- Setting `cis.t9.blog_claim_rule` = On (đo lại tốt hơn: yield 0,417).
- Hook agent `AA_SYNC_HOOKS=warn` (`.claude/settings.json`), SubagentStop vẫn im lặng.
- External checks chạy theo lịch 7/22/37/52 mỗi giờ (root #1007).

## RDS snapshot thủ công

- Đã xoá `db-migrate-tp-018-…` (tech lead duyệt) và `aa-cis-dev-db-pre-s253-aa991-cleanup` (tech lead duyệt); Lambda expiry xoá `db-migrate-281-…` theo hạn. Bản cũ nhất còn lại `db-migrate-296-…` (28/10) → alarm copy-age hết đỏ, đủ 30 ngày chiều 27/11.
