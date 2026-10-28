---
name: aa-wave-rerun
description: Runbook chạy lại pipeline A1→A3 (S1 rewrite → review/Master → atomize) cho một nước, một nhóm tour hoặc cả catalogue AA-CIS theo từng wave — wave object `/admin/waves` (expected set), thang 3 tour → ≤50 → theo nước, RDS snapshot mỗi wave, điều kiện dừng, khoảng nghỉ cho deploy/DB Migrate, đếm đúng, báo cáo wave kèm chi phí. Dùng khi Nghiệp nói rerun, chạy lại một nước, wave, pilot, viết lại catalogue, hoặc AA-645 / AA-653.
---

# aa-wave-rerun

Wave = một lần chạy trả phí trên một tập tour cố định, có đầu, có cuối, có báo cáo. Mọi bước live (enqueue, ECS exec,
snapshot, merge, DB Migrate) do **phiên điều phối** chạy; subagent chỉ soạn script/runbook (hook chặn ECS exec, merge).

## 1. Chuẩn bị

- [ ] Đầu phiên theo `aa-session`: STS, api/worker cùng SHA, `shared.job` không còn queued/running.
- [ ] **Duyệt chi phí:** thang thử 3 tour → ≤ 50 tour → phần còn lại chỉ khi Nghiệp duyệt rõ, có trần $ (memory
      `paid-runs-subset`). Nêu chi phí ước tính trước khi chạy, từ `llm_call_log` của lần trước, không phỏng đoán.
- [ ] Jev canary `credit_ok`, số dư DFS đủ, cost guard còn budget ngày; quota Bedrock của account chạy writer.
- [ ] Raw của nước đúng nguồn; chỗ nào chưa rõ → hỏi trước. Reset toàn bộ derived chỉ theo runbook AA-CIS-App
      `docs/runbooks/clean-rerun.md` (có RDS snapshot trước, assert sau reset).
- [ ] **Writer/route thật:** đọc env worker (công tắc writer do Terraform quản lý) và route `s1_generate` trong
      `shared.llm_role_config` trước khi enqueue; enqueue kèm model writer mong đợi để lệch là từ chối. Sau mọi Terraform
      apply chạm task def ECS: so tên env revision mới nhất với revision đang chạy (deploy chép revision mới nhất).
- [ ] **Tạo wave object TRƯỚC khi chạy:** `POST /admin/waves` (`tour_ids` hoặc `country` → mọi raw active của nước) — đó là
      `expected_set`. Tour cưỡi voi vẫn nằm trong tập, đếm riêng là "chờ người duyệt" (memory `elephant-riding-policy`).
- [ ] **Snapshot mỗi wave:** RDS manual snapshot (chờ snapshot đang `creating` xong mới tạo) + snapshot dữ liệu tour của
      wave (published + place) để rollback từng wave.

## 2. Thang chạy

1. **Pilot 3 tour** — gồm ít nhất 1 tour dài và 1 tour khó (cycle/bike, raw ngắn). Báo cáo → **chờ Nghiệp duyệt**.
2. **≤ 50 tour** phân tầng theo nước → báo cáo → Nghiệp duyệt phần còn lại (một lần, kèm trần $ và luật "đi tiếp giữa các
   wave khi không có điều kiện dừng").
3. **Theo nước**, ~50 tour/wave, chạy nối tiếp bằng driver (mục 5).

Wave nhỏ (< ~10 tour): ngưỡng phần trăm dễ bắn vì 1 tour → chốt với Nghiệp ngưỡng theo số tour trước khi chạy.

## 3. Trong wave

- **Không merge PR backend/pipeline** khi wave mở. Từ AA-993 G5, Deploy Dev CIS tự chặn khi có wave `open` (và khi job kind
  `deploy_blocking` đang chạy / sắp chạy), không còn chặn theo số job trong `shared.job`; DB Migrate `apply` cũng từ chối
  khi có wave `open`. PR thuần FE thì được.
- Deploy / DB Migrate chỉ trong **khoảng nghỉ giữa wave**: wave trước đã đóng, driver đang tạm dừng. Deploy không cần
  chờ `shared.job` rảnh (job còn chạy được release và task mới claim lại); DB Migrate `apply` thì vẫn chờ `shared.job`
  rảnh (cả `recompute` tự sinh sau `a3_atomize`, C6.3b).
- `a3_atomize` chạy 1 job một lúc toàn hệ → hàng đợi dài là bình thường.
- Theo dõi bằng `GET /admin/waves/{id}/report` khoảng 10 phút một lần, không poll dồn. Script theo dõi phải chịu lỗi mạng
  (502) và lưu state để resume.

## 4. Đếm đúng

`GET /admin/waves/{id}/report` suy trạng thái từng tour từ dữ liệu pipeline (AA-CIS-App `services/waves/report.py`):

| Trạng thái | Nghĩa |
|---|---|
| `master` | Master active, publish/promote trong cửa sổ wave |
| `review_pending` | dòng `review_queue` mới nhất trong cửa sổ còn pending |
| `trashed` | raw bị trash / soft-delete |
| `failed` / `interrupted` | S1 cuối cùng lỗi, hết budget, bị huỷ |
| `running` | còn job của wave queued/running — wave chưa xong |
| `unclassified` / `not_started` | S1 xong mà không Master/không review; chưa chạy — **phải bằng 0** khi đóng |

- Đếm theo **distinct tour** trong `expected_set`; tổng các nhóm = số tour của tập. Không đếm bản superseded;
  `ingested` trong review ≠ chưa chạy.
- Jev coverage = tour có dòng `decision_log` không lỗi / tổng; không dùng số call (Jev fail-open).
- Đếm cả sản phẩm đầu ra (atom, segment theo tour), không chỉ trạng thái job — bước "best-effort" có thể lỗi im lặng.
- Tên bảng/cột: `docs/architecture/db-schema-reference.md` (skill `aa-cis-schema`).

## 5. Báo cáo, điều kiện dừng, đóng wave

**Báo cáo mỗi wave** (chat + comment Linear + session log):

```
Wave <nước/tên> <dd/mm> — expected <n>
| S1 ok | Lên Master | Chờ duyệt (tên + lý do + loại lỗi) | Atomized |
- Chất lượng trước→sau (AA-CIS-App scripts/aa645/wave_report.py, $0): trang có gate code, phủ số liệu nguồn,
  tour ở lại bản cũ, atom live ở ngày vượt số ngày mới (phải 0), "đã publish chưa atomize"; brand-fit chỉ báo cáo
- Jev coverage: <tour có verdict thật>/<n>
- Chi phí: theo stage (writer, judge, Jev, flag_fix, atomize, place), DFS, tổng wave, $/tour, luỹ kế so với trần
- Slug: tour đổi slug → slug cũ 308 sang slug mới, slug mới 200 (kiểm sau ≥ 30′)
- Bất thường: job interrupted, tour kẹt
```

**Điều kiện dừng** chốt bằng số trước khi chạy (mẫu AA-645: `docs/audits/2026-10-23-S248-aa645-writer-decision/
platform-impact-memo.md` §6 — tỉ lệ ở lại bản cũ, đường itinerary legacy, atom ở ngày vượt, chi phí/tour vượt mô hình,
throttle Bedrock, atomize fail không chạy lại được). Cờ nào phụ thuộc job còn queued/running thì đọc lại sau khi hàng đợi
hết, trước khi gọi là dừng.

**Đóng:** không có điều kiện dừng → `POST /admin/waves/{id}/close`. Có → để wave mở, dừng driver, báo Nghiệp.
`POST /admin/waves/check` (ops probe gọi hằng ngày) bật chuông khi wave thiếu tour ở trạng thái cuối.

**Driver nhiều wave:** một script chạy các wave nối tiếp: mỗi wave = kiểm dữ liệu trước → RDS snapshot → enqueue (thử
lại khi `shared.job` bận) → kiểm 10 phút một lần tới khi complete → báo cáo → đóng nếu không dừng. Driver bỏ qua wave đã
đóng, resume wave đang mở, **tạm dừng khi có file cờ GAP** (khoảng nghỉ deploy/DB Migrate), **dừng trước wave kế khi có
file cờ STOP**, dừng khi wave thoát lỗi hoặc STS hết hạn; mỗi bước ghi một dòng log. Driver và log nằm trong
`.tmp-session/` (không vào git) — bản phiên cũ có thể đã bị dọn, viết lại theo khung này.

## 6. Sau wave và hết loạt

- Khi `shared.job` rảnh: các bước hậu kỳ của plan (segment research dry-run, place backfill, map component, place card…).
- Tour `transient` → regenerate. `writer_tone` / `forbidden_word` → không regenerate (regenerate không sửa được lỗi ở input
  hay prompt), gom vào issue chất lượng. `raw_insufficient` → trash. Tour cưỡi voi → người duyệt, không regenerate.
- Hết loạt hoặc có điều kiện dừng: khôi phục công tắc theo plan. Tách phiên trong cùng ngày thì giữ công tắc bật, ghi rõ
  trong handoff cái gì đang bật và wave kế (memory `same-day-session-handover`).
- Báo cho chị Thư → `aa-jira-update`. Bài học vùng wave/job runner: `skill/aa-lessons/lessons.md`.
