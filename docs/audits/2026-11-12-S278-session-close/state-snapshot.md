# S278 — trạng thái kiểm cuối phiên (12/11/2026 ~18:45 +07)

Lấy live lúc chốt phiên (STS `aa365-admin`, ECS, endpoint health, DB qua ECS exec chỉ đọc, GitHub). Không ghi account ID,
ARN hay giá trị secret.

## ECS (cluster aa-cis-dev-cluster) — mọi service running = desired = 1, rollout COMPLETED

| Service | Task definition |
|---|---|
| aa-cis-dev-api | aa-cis-dev-api:1109 |
| aa-cis-dev-worker | aa-cis-dev-worker:678 |
| aa-booking-dev-api | aa-booking-dev-api:123 |
| aa-crm-dev-api | aa-crm-dev-api:162 |
| aa-crm-dev-web | aa-crm-dev-web:144 |

## Endpoint và migration

| App | Health | git_sha | Migration mới nhất |
|---|---|---|---|
| CIS | `/health/ready` ok | 995241bc (= main) | 406 |
| Booking | `/booking/health` + `/ready` ok | 8c98da54 | bk-055 (bk-054/055 áp; code #242 chưa merge) |
| CRM api | `/crm/health` + `/ready` ok | 5d302757 (= main) | crm-062 |
| CRM web | `/healthz` ok | 5d302757 | — |

Booking main = a73b031c (#241, chỉ migration); live 8c98da54 có đủ code đến #240.

## Bảng job / wave

- `shared.job` queued/running: 0. Không wave mở. Không cờ wave nào cố ý để bật.
- Worker vẫn bật như đầu phiên: `S1_CONTROL=contract`, `T2_ORCHESTRATOR=linear`, `T9_SEO_BUILDER=on`,
  `T7_BLOG_MIN_SEED_WORDS=600`.

## AI gateway (AA-1095)

- Connection `acc1` BẬT; 13 deployment (9 bật: 4 tắt theo catalog/acc3). Probe 13/13 model ok trên acc1 (0,0027 USD).
- Route-control v10 (provider order theo họ: Claude anthropic-direct > acc1 > acc3; GPT acc1 > acc3) và v11 (3 judge:
  gpt-6-luna trên Bedrock trước gpt-6-luna-openai).
- Sổ cái acc1 tới 18:45: chỉ `adhoc_conn_test` (14 dòng). Chưa có lượt gọi stage thật (Dev không traffic) → kiểm phiên sau.

## Chi tiêu trả phí của phiên (ledger)

- R1 `adhoc_aa1048`: 0,9182 USD (1.645 dòng) / trần 4 USD.
- Thử T7 + blog (cửa sổ P3 từ 11/11 23:58Z): ~1,63 USD trước lượt thử blog 2 + ~0,47 USD lượt 2 ≈ 2,1 / 3,3 USD.
- Probe kết nối `adhoc_conn_test`: 0,0088 USD.

## Hạ tầng thay đổi trong phiên

- acc1: bucket state + role `AA1-Bedrock-Invoker` (Terraform root `accounts/acc1-bedrock`, apply từ Infra main), role
  `AA-BreakGlass-Admin` (CLI, tag ManagedBy=manual-S278).
- aa365: quyền assume acc1 + env `BEDROCK_ACCT_PAYER` (CI apply). WAF stage REST CIS/Booking + pool M2M.
- Secret khoá assertion TripPlanner: bỏ `edge_derived_until` (10:10Z); probe khoá cũ 401.
- GitHub secret Infra `BEDROCK_ACCT_PAYER_ID`.

## PR còn mở

- AA-Booking #242 (code phiên bản giá + lịch mùa): coverage đã đủ (91,38%); đỏ 1 test tích hợp
  `test_migration_of_todays_prices_keeps_every_price` sau khi đổi số bk-053 → bk-054 → phiên sau.
- AA-Booking #200 (bk-045 xoá bảng B2C, hẹn ≥ 28/11, AA-1061). Còn lại chỉ PR bot (release, docs regen, CI durations).

## Lệch / lưu ý

- l18 bước live (seeder Booking, e2e-writers, Partner aa-cancel, backfill case cũ) chưa chạy: ecsx local mode không đọc
  được kết quả từ container Booking/CRM.
- Mọi tenant giả lập kind=demo → AA-1094 chưa chứng minh được danh sách tour riêng của đại lý.
