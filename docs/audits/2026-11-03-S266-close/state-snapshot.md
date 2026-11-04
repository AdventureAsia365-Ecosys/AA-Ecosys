# S266 — trạng thái thật lúc chốt phiên (04/11/2026, ~08:20 +07 / 01:20Z)

Chụp bằng lệnh chỉ đọc (`.tmp-session/S266/ops/snapshot.sh`, ECS exec đọc bảng job, GitHub deployments API). Không ghi
account ID, ARN hay giá trị secret.

| Mục | Giá trị |
|---|---|
| STS | acc2, role `nghiep-admin-8h-session` còn hạn (MFA nhập lại ~20:15 03/11) |
| ECS cis-api | `aa-cis-dev-api:993` (mới nhất), image `dev-68a5b9d0`, COMPLETED 1/1 |
| ECS cis-worker | `aa-cis-dev-worker:559` (mới nhất), image `dev-68a5b9d0` (cùng SHA với api), COMPLETED 1/1 |
| ECS booking | `aa-booking-dev-api:96` (mới nhất), image `a8d98a1e`, COMPLETED 1/1 |
| ECS crm-api | `aa-crm-dev-api:126` (mới nhất), image `d433581e`, COMPLETED 1/1, `CRM_LLM_PROVIDER=bedrock` (Nova Lite acc2) |
| ECS crm-web | `aa-crm-dev-web:98` (mới nhất), image `d433581e`, COMPLETED 1/1 |
| ECS crm-portal | `aa-crm-dev-portal:37` (mới nhất), image `66367c11`, COMPLETED 1/1 |
| CIS health | `/health` 200 `68a5b9d0` 0.18.0; `/health/ready` 200 schema **361** |
| Booking health | `/booking/health` 200 `a8d98a1e` 0.14.0; ready 200 **bk-037** |
| CRM health | `/crm/health` 200 `d433581e` 0.11.0; ready 200 **crm-043**, `entitlement_feed: ok` |
| TripPlanner | web `/api/health` 200 `ad1fcec3` 0.14.0 (Vercel release); 3 Lambda cùng CodeSha256 `0Oq1G2Xy…` (03/11 17:04Z) |
| Migration mới nhất | CIS **361** (353–361 áp trong phiên, 336 vẫn chờ ≥10/11), `bk-037`, `crm-043`, `tp-024` |
| Vercel / deployments | CIS admin `68a5b9d0` (dev + e2e), Booking admin `a8d98a1e`, TripPlanner `ad1fcec3` (release) |
| Bảng job | `shared.job` 0 queued/running, wave 0; `booking.job` 0; `crm.job` chỉ job định kỳ (`crm_entitlement_pull` 289 lượt thành công) |
| Infra vars | `DB_AUTO_APPLY=true`, `DB_AUTO_APPLY_CONTRACT=false` (tới khi áp 336) |
| GitHub env `prod` (Infra) | required reviewer = tech lead, deployment branch = main (đặt S266) |
| Heads | root `65a163ab` (trước PR chốt phiên); CIS `68a5b9d0`; Partner `d433581e`; Booking `a8d98a1e`; TripPlanner `ad1fcec3`; Infra `86e3b6da` |
| PR còn mở | chỉ dependabot / release-please (CIS #1237 #1212 #1179, Partner #200 #133, Booking #161, TP #213 #196, Infra #613 #612) |
| CI nhánh mặc định | xanh ở cả 5 repo con (CI, Secret Scan, Deploy, DB Migrate apply 361, Isolation Probe) |

**Cố ý để BẬT cho phiên sau**

- CRM gọi model thật cho `crm_draft_reply` (Nova Lite acc2, route crm-042; hai dòng Claude tắt, bật lại khi acc3 hết lỗi).
- Job `crm_entitlement_pull` (2 phút), `bk_tenant_pull` (5 phút), `tenant_account_tick` (mỗi giờ), fan-out ngừng bán tour +
  digest 08:00 UTC; gate chủ đề AA ở bước publish.
- Ngân sách AI tenant từ entitlement (chặn cứng theo gói 15/40/80 USD); mọi tenant Dev đã chi 0 USD tháng 11 trước deploy.
- Hop OpenAI cho 6 stage viết tenant (mig 344), `ai_assist` cho đại lý thử Sen Vàng, cờ B2C tắt (ADR 0019).

**Lệch đã xử lý trong phiên**

- Lane l9/l10/l11 lấy số migration chồng dải → đánh lại theo thứ tự merge (358–359 l10, 360 l11, 361 l9).
- Migration expand 360 không tự áp vì Migration Apply dừng ở 336 → áp bằng DB Migrate `--dispatch-expand`.
- PR copy 354/355/358 đỏ do tranh state lock Terraform → chạy lại lần lượt.
- Đêm 03→04/11 Claude Code lỗi "managed policy settings" ~6 giờ → agent sửa lượt 2 của l9 chết giữa chừng, agent mới làm tiếp.
