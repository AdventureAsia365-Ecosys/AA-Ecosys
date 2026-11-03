# S265 — trạng thái thật lúc chốt phiên (03/11/2026, ~15:40 +07 / 08:40Z)

Chụp bằng lệnh chỉ đọc (`.tmp-session/S265/snapshot.sh`, ECS exec đọc bảng job, Vercel API). Không ghi account ID, ARN
hay giá trị secret.

| Mục | Giá trị |
|---|---|
| STS | acc2, role `nghiep-admin-8h-session` còn hạn |
| ECS cis-api | `aa-cis-dev-api:983` (mới nhất), image `dev-2f2883ab`, COMPLETED 1/1 |
| ECS cis-worker | `aa-cis-dev-worker:549` (mới nhất), image `dev-2f2883ab` (cùng SHA với api), COMPLETED 1/1 |
| ECS booking | `aa-booking-dev-api:94` (mới nhất), image `dd223181`, COMPLETED 1/1 |
| ECS crm-api | `aa-crm-dev-api:122` (mới nhất), image `3dd029e3`, COMPLETED 1/1 |
| ECS crm-web | `aa-crm-dev-web:94` (mới nhất), image `3dd029e3`, COMPLETED 1/1 |
| ECS crm-portal | `aa-crm-dev-portal:34` (mới nhất), image `0b02c03c`, COMPLETED 1/1 |
| Health CIS | `/health` 200 `2f2883ab` 0.18.0; `/health/ready` 200 schema **352** (336 vẫn giữ có chủ ý tới ≥10/11) |
| Health Booking | 200 `dd223181` 0.14.0; ready schema **bk-036** |
| Health CRM | 200 `3dd029e3` 0.11.0; ready schema **crm-041** |
| TripPlanner web | `/api/health` 200 `537b0fd5` 0.14.0 (Vercel) |
| TripPlanner Lambdas | browse / assembly / jobs cùng CodeSha256 `iHRrpd5N…` (03/11 07:20Z) |
| Migration mới nhất | CIS 352, `tp-024` (drop `tripplanner.llm_spend_daily`), `bk-036`, `crm-041` |
| Vercel Production | CIS admin `66e1c5cb` (READY); Booking admin `dd223181` (READY); TripPlanner `537b0fd5` |
| Bảng job | `shared.job` 0 queued/running, wave mở 0; `crm.job` không có job đang chờ; `booking.job`: `bk_inquiry_pull` lượt cuối 07:36:59Z, 4 dòng chờ đã huỷ 07:40 (B2C tắt) |
| Infra repo variable | `DB_AUTO_APPLY=true`, **`DB_AUTO_APPLY_CONTRACT=false`** (giữ tắt tới khi 336 áp ≥10/11) |
| GitHub env | Infra dùng env **`dev`** (trust `aa-cis-infra-tf-apply` chỉ còn `environment:dev`, secret env `prod` đã xoá) |
| IAM | `bedrock:ListFoundationModels` trên task role CIS (acc2) và `AA3-Bedrock-Invoker` (acc3) — apply local có MFA |
| App profile AI | cis / tripplanner / crm / booking đều **ON** (CRM tắt-bật lại trong kiểm H1c) |
| Heads | root `b7475d03`; CIS `66e1c5cb`; Partner `3dd029e3`; Booking `dd223181`; TripPlanner `537b0fd5`; Infra `e23e74f6` |
| PR còn mở | chỉ PR bot / dependabot / release-please (CIS #1237, #1212, #1179; Partner #200, #133; Booking #161; TP #213, #196; Infra #613, #612) |
| CI nhánh mặc định | xanh ở cả 5 repo con |

**Cố ý để BẬT / giữ:** hop cuối OpenAI cho 6 stage viết tenant (mig 344); `DB_AUTO_APPLY_CONTRACT=false` tới khi áp 336;
`ai_assist` được phép cho đại lý thử "Lữ hành Sen Vàng" (cần cho F4); cờ B2C tắt (`B2C_INTAKE_ENABLED` off,
`ADVISOR_HANDOFF_DEMO` on) theo ADR 0019. Không có cờ wave.

**Lệch đã xử lý trong phiên:** số migration TripPlanner lane đặt tp-025 trong khi main là tp-023 → đổi thành tp-024;
CIS 347–352 áp với `--allow-out-of-order` vì 336 đang giữ có chủ ý.
