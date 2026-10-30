---
id: OPS-08-s260-state-snapshot
title: "S260 state snapshot (30/10/2026)"
description: "Trạng thái live cuối phiên S260: ECS, health, migration, Vercel, bảng job, repo, việc cố ý để bật."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-30
review_every_days: 30
related: [AA-1002, AA-1003, AA-994, AA-952, AA-955, AA-967, AA-961, AA-921, AA-922, AA-923, AA-788, AA-997]
---

# S260 — state snapshot (chụp 30/10/2026 22:29 +07, 15:29Z)

STS acc2 OK (MFA làm mới 20:47 bằng mã tech lead gửi; phiên 12 h, hạn 31/10 ~08:47 +07).

## ECS (cluster aa-cis-dev-cluster), tất cả COMPLETED 1/1; revision mới nhất mỗi family = revision đang chạy

| Service | Task definition | Image |
|---|---|---|
| aa-cis-dev-api | :939 | `dev-041ba9a2` (CIS #1191, gateway S9) |
| aa-cis-dev-worker | :505 | `dev-041ba9a2` (cùng SHA) |
| aa-booking-dev-api | :90 | `636df62c` (Booking #160) |
| aa-crm-dev-api | :85 | `3718242a` (Partner #140) — có `KMS_SEAL_KEY_ID` từ Infra #525 |
| aa-crm-dev-web | :61 | `3a116512` (Partner #142) |
| aa-crm-dev-portal | :22 | không đổi trong phiên |

## Health

- CIS `/health/ready`: ok, schema **317**, git `041ba9a2`, version 0.18.0.
- Booking `/booking/health/ready`: ok, **bk-035** (không đổi).
- CRM `/crm/health/ready` (host portal.): ok, **crm-027**; CRM api git `3718242a`; CRM web `/healthz` ok `3a116512` 0.11.0.
- TripPlanner `/api/health`: ok `02dd9f1c` 0.14.0 (TP #197); `/api/browse?resource=countries` 200.

## Migration mới nhất mỗi owner

| Owner | Mới nhất | Cách áp trong phiên |
|---|---|---|
| CIS | 317 | 311 contract (DB Migrate 41041084214 / 41041321869); 312 contract (41044219001 / 41044432518); 313–315 expand tự áp (bot); 316 contract (Infra #532, 41070447288 / 41070702600); 317 expand tự áp (bot) |
| Booking | bk-035 | không đổi |
| TripPlanner | tp-022 | không đổi |
| CRM | crm-027 | crm-024 (41038833355 / 41039061497), crm-025 (41052674848 / 41052902908), crm-026 (41061724723 / 41061975356), crm-027 (41073608653 / 41073903296) |

## Vercel production

- CIS admin: Vercel Deploy xanh tại `041ba9a2`.
- Booking admin: Vercel Deploy xanh tại `636df62c`.
- TripPlanner: `02dd9f1c` (đọc từ `/api/health`).
- Content studio (portal) chạy trên ECS `aa-crm-dev-portal`, không đổi.

## Bảng job / wave

- `shared.job`: 1 `place_relocate` queued, `run_after` 31/10 00:12Z (chuỗi AA-997 aa997.3 + v2, 17 job đã xong; còn khoảng 1.005 dòng `llm`).
- DB Migrate `check` 41081388562 success (không bảng job nào chặn). `booking.job` / `crm.job`: chỉ job định kỳ. Không wave mở.

## Repo (head nhánh mặc định lúc chụp)

| Repo | Head | PR mở |
|---|---|---|
| AA-CIS-App | `041ba9a2` gateway S9 | #1179 release 0.19.0 (bot release-please) |
| AA-Booking | `636df62c` điểm ẩn với khách | #161 release (bot) |
| AA-TripPlanner-Web | `02dd9f1c` sửa bản đồ planner | #196 release (bot) |
| AA-Partner | `3a116512` giờ của lịch | #133 release 0.12.0 (bot) |
| AA-CIS-Infra | `6d7470e4` copy 317 | — |
| AA-Ecosys | `a292d27c` docs S10 | #328 (AA-993 M5, cố ý), #374 bot generated infra docs, + PR chốt phiên |

## LLM (probe 30/10 15:14 + kiểm acc3 15:30)

Mọi model sinh văn bản vẫn bị từ chối: acc3 Bedrock Error 002 (chặn cấp tài khoản từ 29/10 ~07:11Z sau khi rời org đại lý;
case AWS Support đang mở, live chat 16:28: service team xử lý 3–5 ngày làm việc); acc2 Bedrock "channel program
accounts"; OpenAI 429 hết credit; `anthropic-direct` chưa có secret. Đối chứng acc1 (tài khoản cá nhân, độc lập): Bedrock
gọi được (Nova Pro, Claude Haiku 4.5) → khoá là riêng acc3. Chỉ Cohere Embed v4 (acc2) chạy.

## Cố ý để BẬT / lưu ý cho phiên sau

- `DB_AUTO_APPLY=true` trên AA-CIS-Infra (từ S258).
- Chuỗi relocate AA-997 tự chạy lượt 31/10 00:12Z. Sau đó: chạy lại `hide_flagged` report + audit (`docs/audits/2026-10-30-S260-aa997-interim/`), rồi mới confirm ẩn (endpoint từ chối 409 khi còn job relocate queued).
- Công tắc mặc định TẮT: AA-788 `T10_F12_SCOPE_MODE` / `T10_F9_BRAND_STYLE_MODE` (chưa đặt), AA-1002 S10 `LLM_CONNECTION_BUDGETS` (không connection nào có budget), `WRITING_MEMORY_PREF_SUMMARY` (tắt), T10 tier-2 `T10_ADJ_MODE` tắt.
- Dữ liệu test trên Dev (agency tổng hợp Sen Vàng): INV-000001 (đã trả, hoàn 50), 2 phong bì ký đã niêm phong, 1 export khách, 1 data request portability + 3 erasure (chỉ dry run), 1 feed ICS đã thu hồi, 1 lần reveal tên khách; vài chuyến khách vãng lai trong `tripplanner.*` từ lúc quay video.
- rclone `aadrive:` (thư mục Drive AdventureAsia) đã cấu hình trên máy tech lead; shared client_id của rclone sẽ ngừng trong 2026 → tạo client id riêng.
- Terminal: `AWS_PROFILE=aa365-admin` mặc định, vùng theo profile, lệnh `awsp`; khoá Anthropic chữ thường đã xoá khỏi `~/.zshrc` (tech lead revoke trên Console).
