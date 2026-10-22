# AA-871 — bằng chứng live (S247, 22/10/2026, Claude Code)

## Logs Insights theo request_id (lấy từ header `x-request-id` của response thật)

| App | Request | Log group | Kết quả |
|---|---|---|---|
| Booking | `GET /booking/health` → `x-request-id: d7ec72c0d7c0454d972487ded8821f3b` | `/ecs/aa-booking-dev` | 1 dòng JSON `request_completed` (route, status 200, duration_ms, git_sha) |
| TripPlanner | `GET /api/trip?trip_id=0000…` (BFF Vercel) → `x-request-id: fc1c567a-d717-4ffd-8823-5447def0b617` | `/aws/lambda/aa-tripplanner-dev-assembly` | 2 dòng JSON (`guest_auth` no_owner, `request_completed` 404) mang cùng request_id + aws_request_id |
| CIS | — | `/ecs/aa-cis-dev` | Chưa có: CIS chưa cấu hình structlog / request-id → PR CIS riêng (S247) |

Dòng log Booking:
```
{"event": "request_completed", "request_id": "d7ec72c0d7c0454d972487ded8821f3b", "level": "info", "logger": "app.request", "timestamp": "2026-10-22T05:25:27.633195Z", "service": "aa-booking-api", "environment": "dev", "git_sha": "104ef6046bf419a0f36bc0d7cf22e6c416003eb2", "method": "GET", "path": "/booking/health", "route": "/booking/health", "status": 200, "duration_ms": 0.3}
```
Dòng log TripPlanner:
```
{"evt": "guest_auth", "outcome": "no_owner", "route": "get_trip", "request_id": "fc1c567a-d717-4ffd-8823-5447def0b617", "aws_request_id": "6b3aee0c-af3c-4a19-91b9-f2ea8773d5e2"}
{"evt": "request_completed", "method": "GET", "route": "get_trip", "status": 404, "duration_ms": 440.4, "request_id": "fc1c567a-d717-4ffd-8823-5447def0b617", "aws_request_id": "6b3aee0c-af3c-4a19-91b9-f2ea8773d5e2"}
```

## Sentry (org dk-0ql) — lỗi thử, không PII

| Project | Issue | Cách sinh | PII |
|---|---|---|---|
| aa-booking-api | AA-BOOKING-API-1 | ECS exec, `init_sentry(load_settings())` + `capture_exception`, message có email + SĐT | `[email] [phone]`; release = git SHA, environment dev; email cảnh báo tới Nghiệp |
| aa-tripplanner-lambdas | AA-TRIPPLANNER-LAMBDAS-1 | test event browse + assembly | `[email]` |
| aa-tripplanner-web | AA-TRIPPLANNER-WEB-1 | `POST /api/trip` body không phải JSON trên production → `onRequestError` | message bị V8 cắt, không chứa dữ liệu |

Phát hiện phụ: `/api/trip` trả 500 với body không phải JSON → sửa ở TP PR #128 (400 `invalid_json`).
Ghi chú: tag `runtime` Booking hiện `[Filtered] 3.12.15` — scrubber lọc quá tay tên runtime (không lộ gì, chỉnh sau).

## Deploy Booking
Booking #58 (tái dùng image cùng SHA, repo ECR IMMUTABLE) → deploy run 39727086003 success, task def `aa-booking-dev-api:38`,
`SENTRY_DSN` map từ secret, `SENTRY_REQUIRED=true`, `/booking/health` 200.
