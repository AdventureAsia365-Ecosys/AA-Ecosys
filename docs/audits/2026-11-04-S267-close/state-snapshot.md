# S267 — trạng thái thật lúc chốt phiên (04/11/2026, ~20:00 +07 / 13:00Z)

Chụp bằng lệnh chỉ đọc (`.tmp-session/S267/ops/snapshot.sh`, ECS exec đọc bảng job và ledger). Không ghi account ID, ARN
hay giá trị secret.

| Mục | Giá trị |
|---|---|
| STS | acc2, role `nghiep-admin-8h-session` còn hạn |
| ECS cis-api | `aa-cis-dev-api:1000` (mới nhất), image `dev-76cd648a`, COMPLETED 1/1 |
| ECS cis-worker | `aa-cis-dev-worker:566` (mới nhất), image `dev-76cd648a` (cùng SHA với api), COMPLETED 1/1 |
| ECS booking | `aa-booking-dev-api:98` (mới nhất), image `3ef1434b`, COMPLETED 1/1 |
| ECS crm-api | `aa-crm-dev-api:128` (mới nhất), image `90eef674`, COMPLETED 1/1 |
| ECS crm-web | `aa-crm-dev-web:103` (mới nhất), image `6c36fc81`, COMPLETED 1/1 (Content studio chạy trong web từ AA-1036) |
| ECS crm-portal | service 0/0, task definition family đã gỡ (AA-1036 bước B, Infra #659) |
| CIS health | `/health` 200 `76cd648a` 0.18.0; `/health/ready` 200 schema **368** |
| Booking health | `/booking/health` 200 `3ef1434b` 0.14.0; ready 200 **bk-039** |
| CRM health | `/crm/health` 200 `90eef674` 0.11.0; ready 200 **crm-043**; web `portal.lumiguides.it.com/healthz` 200 `6c36fc81` (host cũ `partner-dev` 301 sang `portal`) |
| TripPlanner | web `/api/health` 200 `cf6faf9a` 0.14.0; 3 Lambda cùng CodeSha256 `dsDF/qUp…` (04/11 08:36Z) |
| Migration mới nhất | CIS **368** (362–368 áp trong phiên; 336 vẫn chờ ≥ 10/11), `bk-039`, `crm-043`, `tp-024` (dòng Verified của db-schema-reference 12:35Z) |
| Bảng job | `shared.job` 0 queued/running; `booking.job` 0; `crm.job` chỉ 3 job định kỳ (`crm_booking_sync`, `crm_heartbeat`, `crm_membership_pull`) |
| Infra vars | `DB_AUTO_APPLY=true`, `DB_AUTO_APPLY_CONTRACT=false` (tới khi áp 336) |
| Heads | root `f5398a96` + #524/#514 bot docs (trước PR chốt phiên); CIS `76cd648a`; Partner `6c36fc81`; Booking `3ef1434b`; TripPlanner `cf6faf9a`; Infra `53500588` |
| PR còn mở | chỉ dependabot / release-please (CIS #1237 #1212 #1179, Partner #200 #133, Booking #161, TP #213 #196, Infra #613 #612) |
| CI nhánh mặc định | xanh ở cả 5 repo con (CI, Secret Scan, Deploy, DB Migrate apply 368, Isolation Probe, Tour Liveness Gate) |

**LLM gateway (sau 366–368, probe 04/11 ~12:55Z)**

- Probe mọi deployment đang bật: 13 trả lời, 8 bị từ chối (Claude 5.x + GPT trên acc3, case AWS còn mở), 0,0013 USD.
- Model thật sự phục vụ: 20 stage Sonnet 4.6 / Haiku 4.5 @acc3; 14 stage GPT-6 Luna @openai-direct; 4 embed Cohere @acc2.
  Stage coverage chỉ báo `s1_atom_writer`, `tp_extract` (route chết, 336 tắt).
- Sweep ứng viên acc3 (0,0012 USD): Sonnet 4.5, Opus 4.5, Opus 4.6, Llama 4 Maverick, Kimi K3 trả lời (deployment vẫn tắt);
  GPT-6 Sol / 6.1 Sol / 6.1 Terra `access_denied`. Kết quả: `docs/audits/2026-11-04-S267-llm-routing/live-check/`.
- Trần: acc3 100 USD/tháng, anthropic-direct 150 USD (kết nối tắt, chưa có key), openai-direct 10 USD.

**Chi phí phiên:** LLM ledger 0,0041 USD (probe/sweep/test); Amazon Location 0,32 USD (AA-1043); Drive → S3 ~0,0003 USD
request (AA-1044). Tổng ≈ 0,33 USD.

**Cố ý để BẬT cho phiên sau**

- Route theo họ model (366), model-first mặc định (`LLM_ROUTE_AWS_FIRST` tắt); writer chạy Claude 4.x trên acc3 trong lúc AWS
  chưa mở 5.x; stage GPT chạy GPT-6 Luna qua OpenAI API (trần 10 USD/tháng).
- Probe hằng ngày 05:00Z, cảnh báo stage coverage (bell + email mỗi stage mỗi ngày) — sẽ báo 2 route chết tới khi áp 336.
- Các job CRM/Booking pull, `tenant_account_tick`, fan-out ngừng bán + digest; ngân sách AI tenant theo gói; cờ B2C tắt.
- 4 secret key E2E tenant đang chờ xoá (hết hạn khôi phục 04/12).

**Lệch đã xử lý trong phiên**

- Preflight migration CIS #1297 (368) đỏ vì 367 chưa lên main → rebase sau khi #1295 merge.
- Nhánh code sweep #1296 đọc cột của 367 → giữ lại, merge sau khi áp 367.
- Lệnh `dump` của `tools/docs/gen_llm_routes.py` lỗi khi chạy qua ecsx (file ở `/tmp`) → sửa trong root PR chốt phiên.
- `gpt-4.1` @openai-direct (retired, không route nào dùng) vẫn bật nên probe gọi và lỗi → follow-up AA-1042.
