# S275 — snapshot trạng thái (10/11/2026 ~16:00 +07, đọc live)

STS: acc2, role `nghiep-admin-12h` (MFA hết hạn 21:49 +07).

## ECS (cluster aa-cis-dev-cluster), mọi service 1/1 COMPLETED, revision mới nhất = revision đang chạy
| Service | Task def | Image / SHA |
|---|---|---|
| aa-cis-dev-api | :1081 | `dev-5cc016cd` (#1419) |
| aa-cis-dev-worker | :648 | `dev-5cc016cd`, có `T2_ORCHESTRATOR=linear` + `T9_SEO_BUILDER=on` (Infra #752) |
| aa-cis-dev-admin | :17 | `dev-5cc016cd` |
| aa-booking-dev-api | :112 | `76140cdf` |
| aa-booking-dev-admin | :11 | `0cb1569b` + container phụ WordPress test (AA-1060) |
| aa-crm-dev-api | :147 | `451e5011` (#259) |
| aa-crm-dev-web | :122 | `451e5011` |
| aa-tripplanner-dev-web | :6 | `245595cb` |

## Endpoint
- CIS `/health` 200, git_sha `5cc016cd`. `/health/ready` ok, schema 394.
- Booking `/booking/health` 200 `76140cdf`. `/booking/health/ready` ok, bk-044.
- CRM `/crm/health` 200 `451e5011`. `/crm/health/ready` ok, crm-048. Web `/healthz` 200 `451e5011`.
- TripPlanner Lambda `browse` / `assembly`: CodeSha256 `QBfRElxj…`, cập nhật lần cuối 08/11 14:48Z (không đổi trong phiên).

## Migration mới nhất mỗi owner
- CIS **394** (áp tay bằng `ship_copy_apply.py --dispatch-expand --allow-out-of-order`, run 42769339515). CIS 336 vẫn chờ
  AA-1024 D8 (sau 12:00Z 10/11, chưa làm).
- Booking bk-044 (bk-045 = Booking #200 draft, từ 28/11).
- CRM **crm-048** (contract, Partner #258 → Infra #753 → apply qua `ship_wave`).
- TripPlanner: không đổi.
- Schema dump: root #664 tự merge sau apply.

## Bảng job và wave
- `shared.job`: 0 queued/running. Wave mở: 0 (đọc cuối AA-741 phase 2).
- `booking.job` / `crm.job`: guard deploy của Booking và CRM cho qua trong phiên (deploy CRM `451e5011` không bị chặn).
  Container CIS không đọc được hai bảng này.

## AI gateway (24 h, đọc cuối phiên)
- Connection bật: acc2, acc3, anthropic-direct, openai-direct, typesafe, dataforseo, geoapify. Route control v7.
- acc3: 7 model vẫn bị từ chối (ticket đang mở); route chuyển sang model khác, không tính là lỗi.
- Chi tiêu tháng (không tính shadow): 26,18 USD. anthropic-direct 22,38 / 150; openai-direct 0,74 / 10; acc3 0,97 / 100;
  typesafe 2,00.
- Lỗi 24 h:
  - a3_demand 5.017: đợt burst 18:07Z ngày 09/11, trước khi #1416 lên.
  - t7_debate_judge `access_denied` 119: route acc3 bị từ chối rồi chuyển model, cần xem có nên tính là refusal (S276).

## Repo (nhánh mặc định, PR mở)
- Root `9fa97b0e` (#664). PR mở: 0. Thay đổi phiên chưa commit nằm trong root PR cuối phiên.
- CIS `5cc016cd`. PR mở: chỉ PR release #1179.
- Booking `ca4952b1`. PR mở: #200 (draft bk-045, từ 28/11), PR release #161.
- Partner `451e5011`. PR mở: chỉ PR release #133.
- TripPlanner `c3e10fd9`. PR mở: chỉ PR release #196.
- Infra `788addbf` (#753). PR mở: 0.

## Cố ý để BẬT cho phiên sau
- Worker CIS: `T2_ORCHESTRATOR=linear`, `T9_SEO_BUILDER=on` (tech lead chốt; bằng chứng AA-741 phase 2).
  `T9_REGRESSION_GUARD_MODE` vẫn unset. `T9_FAQ_LLM_FILTER=on` giữ nguyên.
- Jev allowlist: 2 tenant demo đã thêm cho việc lọc W2. Gỡ khi xong việc W2 / AA-1063.

## Chi phí phiên (Dev, trả tiền)
- AA-741 phase 2: 6,77 USD (trần 13,44).
- AA-1049, thử nghiệm: T2 0,166 + SEO ~0,21 USD.
- AA-1058: 0,125 USD.
- Jev (AA-1063): shadow 0,085 + lọc 0,038 USD.
- Panel W2/W4 bằng agent: 0 USD.

## Lệch so với điều phiên tưởng
- t2@2: 341 câu tranh chấp **chưa có queue item** (2.166 dòng nhãn panel, 0 mục trong `writing_memory_disagreement`), nên
  chưa duyệt được trong Writing Lab. Cần bước đưa vào hàng duyệt (S276, AA-1063).
- Partner #258 trượt merge queue một lần vì test flaky (hash ngẫu nhiên chứa "900"). Test đã sửa trong #259.
