# S263 — trạng thái live cuối phiên (02/11/2026 ~06:40 +07)

Chụp bằng lệnh chỉ đọc (`.tmp-session/S263/snapshot.sh` + ECS exec đọc bảng job). Không account ID, ARN hay secret.

| Mục | Giá trị |
|---|---|
| STS | acc2, phiên admin 8h |
| aa-cis-dev-api | :973 = mới nhất, image `dev-4f1244a9`, COMPLETED 1/1 |
| aa-cis-dev-worker | :539 = mới nhất, image `dev-4f1244a9` (cùng SHA với api), COMPLETED 1/1 |
| aa-booking-dev-api | :93 = mới nhất, image `967f9b2c`, COMPLETED 1/1 |
| aa-crm-dev-api | :117 = mới nhất, image `f7e8d381`, COMPLETED 1/1 |
| aa-crm-dev-web | :86 = mới nhất, image `e5d5d517`, COMPLETED 1/1 |
| CIS `/health`, `/health/ready` | 200 `4f1244a9` v0.18.0; schema **338** (334, 335, 337, 338 áp; **336 chờ**) |
| Booking | 200 `967f9b2c` v0.14.0; `bk-035` |
| CRM | 200 `f7e8d381` v0.11.0; `crm-039` |
| TripPlanner web | 200 `8e59223a` v0.14.0 |
| Lambda TP browse / assembly | CodeSha256 `uAHKF2/…`, sửa lần cuối 01/11 12:51Z |
| Bảng job | `shared.job` 0 queued/running; wave mở 0 |
| Infra repo variable | `DB_AUTO_APPLY=true`, **`DB_AUTO_APPLY_CONTRACT=false`** (tắt tạm, xem log) |

Heads: root `b14703e8`→ (close PR), CIS `7f713a07`, Partner `0ace0b2e`, Booking `f094e94a`, TripPlanner `8e59223a`,
Infra `7178fb39`.

PR còn mở: root #374 (bot infra docs), #328 (cũ); CIS #1237, #1212 (dependabot), #1179 (release); Partner #133, Booking
#161, TripPlanner #196 (release-please).
