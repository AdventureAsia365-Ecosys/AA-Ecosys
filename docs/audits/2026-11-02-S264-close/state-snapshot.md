# S264 — trạng thái live cuối phiên (02/11/2026 ~21:10 +07)

Chụp bằng lệnh chỉ đọc (`.tmp-session/S264/snapshot.sh` + ECS exec đọc bảng job, Vercel API). Không account ID, ARN hay secret.

| Mục | Giá trị |
|---|---|
| STS | acc2, phiên admin 8h |
| aa-cis-dev-api | :979 = mới nhất, image `dev-a08d7209`, COMPLETED 1/1 |
| aa-cis-dev-worker | :545 = mới nhất, image `dev-a08d7209` (cùng SHA với api), COMPLETED 1/1 |
| aa-booking-dev-api | :93 = mới nhất, image `967f9b2c`, COMPLETED 1/1 (Booking #169 chỉ đổi admin Vercel, api không deploy lại) |
| aa-crm-dev-api | :120 = mới nhất, image `dca5465b`, COMPLETED 1/1 |
| aa-crm-dev-web | :92 = mới nhất, image `ba3eec91`, COMPLETED 1/1 |
| aa-crm-dev-portal | :34 = mới nhất, image `0b02c03c`, COMPLETED 1/1 |
| CIS `/health`, `/health/ready` | 200 `a08d7209` v0.18.0; schema **346** (339–346 áp trong phiên; **336 vẫn chờ**, contract ≥ 10/11) |
| Booking | 200 `967f9b2c` v0.14.0; `bk-035` |
| CRM api | 200 `dca5465b` v0.11.0; `crm-040` |
| CRM web `portal./healthz` | 200 `ba3eec91` v0.11.0 (`partner-dev./healthz` trả 301 sang `portal.` — đúng thiết kế) |
| TripPlanner web | 200 `8e59223a` v0.14.0 (không file frontend nào đổi sau #210 nên Vercel không build lại) |
| Lambda TP browse / assembly | cùng CodeSha256 `gFA2On…`, sửa lần cuối 02/11 12:54Z / 12:21Z (E3 #211 + core sync #212) |
| Vercel Production | CIS admin `a08d7209`; Booking admin `1fceb3c4`; TripPlanner `8e59223a`; portal chạy ECS (không còn Vercel) |
| Bảng job | `shared.job` 0 queued/running, wave mở 0; `booking.job` 0; `crm.job` chỉ 3 job định kỳ hẹn giờ (membership_pull, booking_sync, heartbeat) |
| App profile AI | cả 4 app `ai_enabled=true` (bật lại sau game day H1a, kiểm trong phiên) |
| Infra repo variable | `DB_AUTO_APPLY=true`, **`DB_AUTO_APPLY_CONTRACT=false`** (giữ tắt tới khi 336 áp ≥ 10/11) |
| CI nhánh mặc định | xanh ở cả 5 repo con (Deploy Dev, CI, Release Please, Secret Scan, Terraform Drift, DB Schema Dump) |

Heads: root `0fb8309c` → (close PR), CIS `a08d7209`, Partner `dca5465b`, Booking `1fceb3c4`, TripPlanner `39e7e65b`,
Infra `e4e45160`.

PR còn mở: root #466 (bot infra docs); CIS #1237, #1212 (dependabot), #1179 (release); Partner #133, Booking #161,
TripPlanner #196 (release-please), #213 (dependabot); Infra #613, #612 (dependabot).

Cố ý để BẬT cho phiên sau: không có cờ wave nào. Route `t9_write`/T-series có hop cuối OpenAI (mig 344) — cố ý, tới khi
acc3 hoặc key Anthropic có lại.

Lệch so với điều phiên tưởng: không có.
