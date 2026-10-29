# S257 — trạng thái kiểm cuối phiên (29/10/2026 14:45 +07)

Nguồn: lệnh một dòng AWS (acc2), `/health` + `/health/ready` các app, `gh`. Không ghi account ID, ARN hay giá trị secret.
STS acc2 OK.

## ECS (cluster aa-cis-dev-cluster)

| Service | Task def đang chạy | Image | Rollout | Revision mới nhất = đang chạy |
|---|---|---|---|---|
| aa-cis-dev-api | :913 | dev-`2e8e10a3` (CIS #1144) | COMPLETED | có |
| aa-cis-dev-worker | :479 | dev-`2e8e10a3` (cùng SHA với api) | COMPLETED | có |
| aa-booking-dev-api | :86 | `216cb5e6` (Booking #145, S4b) | COMPLETED | có |
| aa-crm-dev-api | :77 | `03918c0b` (Partner #121, M4b) | COMPLETED | có |
| aa-crm-dev-web | :49 | `04756799` (release portal 0.9.1) | COMPLETED | có |

Cả 5 service 1/1 task. RDS `aa-cis-dev-db`: không đọc riêng trong snapshot; mọi `/health/ready` trả ok (DB trả lời).
EFS: 0 file system (đã xoá trong phiên, Infra #492).

## Endpoint

| Endpoint | Kết quả |
|---|---|
| CIS `/health/ready` | ok, schema 303, git `2e8e10a3` |
| Booking `/booking/health/ready` | ok, `bk-033` |
| Portal `/healthz` | ok, `04756799` (0.9.1) |
| TripPlanner `/api/health` | ok, `d98ebef7` (báo 0.11.1; commit release 0.12.0 / 0.13.0 không deploy lại) |
| Lambda browse / assembly / jobs | cả ba deploy 07:04 UTC 29/10, cùng CodeSha256 `2W+JYzCH…` |

## Migration mới nhất mỗi owner

CIS 303 (302 và 303 áp hôm nay), Booking bk-033, TripPlanner tp-021 (áp hôm nay), CRM crm-023.
`DB_AUTO_APPLY`: chưa đặt (unset) — chưa có migration nào tự áp.

## Vercel

TripPlanner production trả `d98ebef7` (qua `/api/health`). Commit production của CIS admin và Booking admin không đọc lại trong
snapshot (deploy qua CI, danh sách deployment GitHub của Vercel không còn cập nhật).

## Bảng job / wave

`shared.job`: chỉ 1 job `place_relocate` queued (chuỗi AA-997 `aa997.1`, `run_after` 30/10 00:13 UTC) — có chủ đích; 0 wave mở.
`booking.job`, `crm.job`, `tripplanner.job` không chụp trong snapshot.

## Job đã chạy trong phiên (CIS #1144, theo sau AA-671)

- `photo_destination_match` dry run `6e8b5043`: khớp 1.593 (exact 1.079 / name_in_label 495 / core 19); weak 137; ambiguous 120; no_match 779.
- Apply `69659af9`: ghi 1.593, 283 điểm đến có ảnh, open_after 1.036.
- Pool ảnh bìa phủ 162 → **302 / 892** tour.

## Cố ý để BẬT

- Chuỗi relocate AA-997 (`aa997.1`, job tự nối tiếp theo credit Geoapify mỗi ngày).
- Lambda `aa-tripplanner-dev-jobs` + lịch hằng ngày (tick dry run `tp_retention_outbox_redact`) + 2 alarm `-errors` / `-not-run`.
- Workflow migration-sync / migration-apply (Infra #493) — nhưng `DB_AUTO_APPLY` chưa đặt nên không tự áp.
- `kit-sync.yml` (CIS) mở PR đồng bộ kit core sang Partner / Booking / TripPlanner.
- User E2E studio trả lại role owner sau kiểm viewer.

## Cờ giữ TẮT

Công tắc AA-997 v2 (luật chặt `aa997.2`, strategy v1; P4 FAIL), `T9_READER_CHECKLIST_MODE` (AA-790 r10 FAIL),
`T9_BRIEF_GROUNDING_MODE`, `T8_ANGLE_BRIEF_MODE`, `DB_AUTO_APPLY` (cron migration-sync chưa chạy theo lịch), GuardDuty ("chưa dùng").

## Sự cố còn mở lúc chụp

- **acc3 rời AWS Organization lúc 06:50 UTC** (CloudTrail: `organizations.amazonaws.com` xoá `AWSServiceRoleForOrganizations`;
  `describe-organization` → không còn là thành viên). Ngay sau đó các model OpenAI-on-Bedrock trên acc3 (gpt-5.6-luna,
  gpt-6-luna) trả AccessDenied "not available for this account"; Claude trên acc3 vẫn chạy. Mọi stage judge route sang luna
  (t2_judge, t10_judge, s1_judge, writing_memory_eval, …) có rủi ro; lối cuối OpenAI API hết credit (429).
  Probe nhỏ gpt-6-luna sau đó không ra kết quả (chưa kiểm được).

## PR còn mở lúc chụp (14:45)

| Repo | PR | Trạng thái sau đó |
|---|---|---|
| AA-CIS-App | #1134 release 0.16.0 | merge lúc chốt |
| AA-Booking | #147 release 0.12.0 | merge lúc chốt |
| AA-TripPlanner-Web | #186 release 0.13.0 | merge lúc chốt |
| AA-Partner | #122 release 0.10.0 | merge lúc chốt |
| AA-Ecosys | #327 bot infra docs | merge lúc chốt |
| AA-Ecosys | #328 AA-993 M5 (luật migration cho expand auto-apply) | **cố ý để mở** — chờ proof auto-apply (bk-034, S258) |
| AA-CIS-Infra | — | 0 PR mở |

Head lúc chụp: CIS `2e8e10a3` (#1144; #1142 `652b255f` đã merge trước đó), Booking `216cb5e6` (#145), TripPlanner `84df8e0f` (#187),
Partner `03918c0b` (#121), Infra `621085df` (#498, copy mig 303), root `03071a6b` (#329).
Nhánh CIS `fix/aa-900-adhoc-label-account` (commit `7fbbbc6e`, guard test "nhãn không bao giờ đổi route / account") chưa push lúc chụp.
