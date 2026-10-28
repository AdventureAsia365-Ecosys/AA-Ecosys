# S254 (27–28/10/2026): Booking phủ Figma + S4/S5, job nhả/nhận lại khi deploy, Releases Writing memory, audit Figma và geocode

Tác nhân: **Claude Code** (Ultracode; workflow nhiều sóng, tối đa 2 lane nặng, 1 workflow viết code một lúc). Bắt đầu
22:57 27/10 (giờ VN), chạy qua đêm; Nghiệp quay lại khoảng 06:15–06:30 sáng 28/10. Một lần chạm hạn mức phiên
(05:20–06:08). Số liệu cuối phiên lấy từ `docs/audits/2026-10-28-S254-session-close/state-snapshot.md` «SNAPSHOT: tên
thư mục snapshot thật».

## Trạng thái

- Đầu phiên (khớp snapshot S253): cis api:867 / worker:433, booking:66, crm api:64, web:33, portal:9 — tất cả
  COMPLETED. PR mở: chỉ 4 release PR (CIS #1049, Booking #95, TP #155, Partner #64) + Infra Dependabot #411/#412.
- Cuối phiên: 20 việc đã duyệt xong hoặc ship phần lớn; làm tiếp theo master plan (sóng 7–9: lát sửa từ audit Figma,
  AA-919 R2, AA-990 chặng tự di chuyển, AA-996 lát 2). Còn chạy lúc soạn log: Booking #127/#128 trong merge queue,
  chuỗi `chain_w9.sh` (bk-032), AA-919 R2 bước C `a720cfac` «SNAPSHOT: trạng thái cuối của 3 việc này».

## Quyết định của Nghiệp (trong phiên)

- Đầu phiên: chọn 20 việc, coi như đã duyệt; việc cần duyệt thì làm luôn theo kế hoạch; chạy liên tục tới 07:00, không
  tự dừng, báo cáo đầy đủ.
- (~23:50) Xong 20 việc trước 7h thì lấy tiếp theo thứ tự master plan và làm tiếp.
- (06:15) "Làm việc bình thường."
- (06:30) Duyệt làm luôn: Vercel deployment retention, vòng thử AA-919 Releases, H1 (AA-Partner bắt buộc Portal Build +
  Web Build), H2 (AA-CIS-App bắt buộc Frontend Lint).
- Ảnh Countries VN/JP/IN và thanh lọc 2 hàng của Booking: "vẫn để bình thường, khi nào có dữ liệu thì load vào" — giữ
  fallback trung tính cho 3 nước chưa có ảnh, giữ thanh lọc 2 hàng theo Figma.
- (10:40) Nháp Jira **gom sang phiên kế tiếp trong cùng ngày** (không soạn/duyệt ở cuối S254); xong các việc đang chạy
  thì chuẩn bị dừng phiên.

## Done (kèm bằng chứng)

Trạng thái Linear từng issue «SNAPSHOT: Done / In Progress theo Linear lúc chốt».

| Issue | Kết quả | Bằng chứng |
|---|---|---|
| AA-682 S4 | bk-030 hoá đơn nhà cung cấp + chi trả: Booking #119 → Infra #448 → DB Migrate check 40555987390 / apply 40556423522 (ready=bk-030, root bot #288); code Booking #120 `0c544765` deploy xanh. | Dry-run Dev run 40564671027: 14/14 refusal check, `verdict ok`, rolled back — `docs/audits/2026-10-27-S254-aa682-s4/`. |
| AA-682 S5 | "My Payments": contract root #289, Booking #122 `d654e398`, TripPlanner #167 `23e8b2a4`. | Scope check run-script (Infra #456) + 401 ở cả 3 đường — `docs/audits/2026-10-27-S254-aa682-s5/`. |
| AA-993 G2/G3 | CIS #1077 `74c545dc`: CancelledError trong node LangGraph không còn bị nuốt thành `rewrite_failed`. | G2: job `1ffffb96` nhả 17:31:04Z ở `writer_done`, nhận lại `resumed_from=writer_done`, xong `accounted` (1 version / 1 score / 0 review). G3: a3_atomize `a83fa22d` nhả 17:35:01Z, tiếp tục sau 116 s, 0 fingerprint trùng, $0,0167 — `docs/audits/2026-10-27-S254-aa993-g2-g5/g2-g3-cis-proof.txt`. |
| AA-993 G4 | Booking `bk_noop_sleep` (Booking #121 `5aa2e69a`, Infra #449 TF apply 40564791553 có `JOB_TEST_KINDS`; Infra #454 bật → #455 về dry_run). | Job 300 s nhả đúng 1 lần, tiếp tục từ 215 s, `succeeded` — `g4-booking-proof.txt`. |
| AA-993 G5 + Phase E | Guard deploy mới CIS #1081 `69dc6332`, Partner #99 `826df536`; root #290 `728ce9bd` (docs G5 + ADR 0017). | CIS Deploy Dev run 40577044359: `safe_to_deploy: true`, job đang chạy được nhả và nhận lại — `g5-cis-gate.txt`. |
| AA-993 (log chi phí S1) | CIS #1079 `e22e5fb6`: slug `aa_internal` trong payload làm mất mọi dòng `llm_call_log` (bug cũ, không do G2). | Job `209d9e60` ghi đủ s1_generate / grounding / judge ($0,0514). |
| AA-994 S1c + S2a | S1c eslint-kit CIS #1078 (bằng chứng đỏ run 40554868225 `aa-kit/no-raw-main`, rồi xanh); S2a vendor kit core vào Partner #102 `8af302ee`; kit core `"use client"` cho useMediaQuery CIS #1083 `a38efd49`. | Portal deploy xanh; check "Vendored CIS copies" «SNAPSHOT: xanh trên main Partner». |
| AA-979 §4.3 + §4.4 | `/trip`: Infra #451 apply 40573187449 (`CIS_API_URL` cho web), Partner #100 `2fb453f7`, CIS #1082 `0ef0d147` (307 → go-dev). Bỏ bridge EXTERNAL `cis-portal`: Partner #101 `c35ad2d5`, Infra #452 apply 40579274504 + redeploy crm api:69 (0 biến bridge). | Live: aa-cis `/trip` → 307 go-dev (giữ query), go-dev 200, partner-dev 404, robots `Allow /trip/`. |
| AA-919 Releases tab | CIS #1076 `39dc01f0` (tab Releases, API có `evidence` + `summary`); sửa tràn bảng #1080 `1976bf94`; ô chọn tenant theo tên #1086 + `TenantSelect` cho 6 trang admin #1088; WM-19/WM-21 CIS #1084 + Infra #453 (mig 291/292). | Ảnh `docs/audits/2026-10-27-S254-aa919-releases/`. Vòng thử WM-22 qua API (E2E CIS admin): draft #2 (terra-family, t9_social) → evaluated → approved → active → rollback → release 0 active lại. R2 seeded-fault `3a72a697`: verdict fail / hard_stop / tune, $0,046 (đúng như mong đợi với lỗi cài sẵn). |
| AA-784 (6 thẻ xuyên biên giới) | CIS #1074 `ecef8db1`; job `7f554a44` dọn 6/6, giữ country/tên. | $0,0039; comment Linear AA-784. |
| AA-995 | Gộp ảnh trùng CIS #1073 `96eb3932` + TP #165 `1073dbc2` (deploy api:869 / worker:435); trang Golden Hour TP #168 `bb7d259b`; tràn 26 px ở `/destinations/bhutan` 390 → TP #169 `eae69868` + #170 `882f7b5d` (0 px); TP #171 (Poppins, giảm chuyển động, content-visibility, mở/đóng tất cả) «SNAPSHOT: SHA merge #171». | Cover điểm đến lệch id chuẩn = 0 (live); ảnh `docs/audits/2026-10-27-S254-aa995-pages/`. |
| AA-990 (việc nhỏ) | Ảnh portal atom_replaced 4/4 (0 lỗi); `256f07bd` = nguồn chỉ 8 ngày (`source_skips_days`, không sửa); CIS #1089 `8aabaf0a` giữ chặng tự di chuyển (61 / 7.081 atom). | N1: 82/101 tour có route, BELOW_HALF 0; 2 tour transit-skip (Seoul–Busan, Oze–Nikko) cần luật mức tour; 14 tour chờ geocode — `docs/audits/2026-10-27-S254-aa990-close/`. |
| Release PRs | TP #155 `f2024ad4`, Booking #95 `49871054`, Partner #64 `77df9ea2`, CIS #1049 `c3fae2c9` (release-only, không deploy). Dependabot gom vào Infra #446 `3a322860`, đóng #411/#412. | — |
| Vercel | Region sfo1 cho CIS admin, Booking admin, TripPlanner (hiệu lực từ deploy kế). Retention 4 project: preview 2 tuần, production 1 tháng, canceled/errored 1 tuần (06:35). | Retention đặt xong 06:35 cho cả 4 project «SNAPSHOT: đọc lại cấu hình». |
| H1 / H2 | AA-Partner main bắt buộc Portal Build + Web Build; AA-CIS-App main bắt buộc Frontend Lint. | Đặt xong 06:35 (checklist phiên). |

## Ship, chưa đóng issue (In Progress, còn slice)

- **AA-996 Booking phủ đủ màn Figma.**
  - bk-029 (Booking #115 → Infra #447 → DB Migrate check 40545909801 / apply 40546186921, root bot #287); code #117
    `c606f60c`; Countries (PK/TW/KG + Images) #118 `71142710`; ảnh `docs/audits/2026-10-27-S254-aa996-figma-coverage/`.
  - bk-031 (Booking #123 → Infra #457 → DB Migrate 40586339735, root bot #292); layout compact cho laptop zoom #124
    `96c1bcf4`.
  - **Audit Figma (việc 20, làm sau cùng):** 7,3/10 (118/120 frame chụp được), 25 lệch thật của sản phẩm, 5 lát sửa —
    `docs/audits/2026-10-28-S254-booking-figma-audit/`.
  - Lát sửa 1 + 3: Booking #125 (ảnh CIS cho Countries: cover / gallery / drawer + fallback trung tính; VN/JP/IN 0 ảnh
    vì CIS chỉ sync Drive "CON" cho 7 nước — việc nội dung CIS) và #126 `7473755c` (DateField en-GB, thanh lọc 2 hàng,
    Export CSV 9 danh sách, bảng hoá đơn / trip-check vừa 1440).
  - Lát 4 + 5: Booking #127 (hồ sơ chuyến / proposals / trip checks; chặn approve version rỗng 422) và #128 (hoá đơn,
    PDF, payment, thông báo, khoá staff bắt lý do, audit-log) — trong merge queue «SNAPSHOT: SHA merge + deploy».
  - Lát 2 (Supplier + ma trận giá + picker): Booking #129 (bk-032) + Infra #458 → apply sau R2 → code PR, qua
    `chain_w9.sh` «SNAPSHOT: bk-032 đã áp chưa».
  - Còn: chụp lại 8 frame thiếu bằng chứng + chấm điểm audit cuối.
- **AA-919 Writing memory.** Còn R2 bước C (≤ $2) `a720cfac` «SNAPSHOT: verdict + chi phí», rồi lượt R2 ≤ $10 thật +
  targeted shadow run.
- **AA-990.** Luật mức tour cho chặng transit (2 tour N1) + kiểm lại sau lượt geocode retry 28–29/10.
- **AA-790 vòng 7 (brand voice).** CIS #1085 merge, đối chứng r6b ($0,894, n=20) rồi r7; panel mù 9 arm (720 điểm):
  ai_tells đạt, brand_voice / reader_value không đạt luật ship → revert CIS #1087, vòng 6 giữ live —
  `docs/audits/2026-10-28-S254-aa790-r7-panel/`. Vòng sau sửa bộ sinh angle T8, không sửa prompt T9.
- **AA-994.** Còn S2b trở đi.
- **AA-979.** Đợt dọn từ 03/11.
- **Audit geocode** (không issue riêng; đề xuất issue mới chờ Nghiệp đồng ý tạo): 9.545 tên = 7.924 resolved
  (7.272 Geoapify, 652 không ghi provider), 1.203 pending, 418 unknown. Độ đúng 7.924 tên ≈ 75% (CI 71–80%); Geoapify
  ≈ 91%, toạ độ LLM đề xuất ≈ 55–60% (3.770 dòng giữ ~1.400 / ~1.700 điểm sai). 1.621 tên chưa resolve chia 14 nhóm
  nguyên nhân; kế hoạch sửa 8 bước — `docs/audits/2026-10-28-S254-geocode-audit/` (§8). Chi phí audit $0.

## Sự cố

1. **Chạm hạn mức phiên 05:20–06:08.** Hai lane sóng 7 dừng giữa chừng; CI CIS #1084 (unit/integration) và #1085
   (golden-set text guard) đỏ, chuỗi r7 dừng. Sau reset: chạy lại sóng 7, sửa CI #1084/#1085.
2. **MFA acc2 hết hạn 07:46.** Vòng chờ migration 291/292 treo im lặng ở dấu nhắc MFA; phát hiện muộn, kill theo PID,
   Nghiệp nhập mã lúc ~08:30 (hạn mới 20:35), chạy lại. Đã ghi bài học.
3. **Build web CRM (AA-Partner) vỡ trên main.** #100 thêm import `@/app/_brand/tokens`, #102 (S2a) xoá file đó; cả hai
   xanh riêng, Web Build không bắt buộc nên merge queue không bắt. Hotfix #104 `3d338504`; H1 bắt buộc Web Build +
   Portal Build.
4. **Mất log chi phí S1.** Hai job S1 lúc 17:18Z / 17:29Z không ghi dòng nào vào `shared.llm_call_log` (slug
   `aa_internal` làm asyncpg từ chối `uuid`, `record_call` nuốt lỗi) — không khôi phục được. Sửa CIS #1079.
5. **`pkill -f` / `kill $(pgrep -f …)` tự giết chính lệnh (exit 144), 2 lần.** Không ảnh hưởng hạ tầng; bài học cũ
   được gộp và nhấn lại.
6. **`shippr.sh` đẩy nhánh khi rebase còn dở** → Booking #120 nhận bản cũ, rebase lại sạch rồi mới queue.

## Trạng thái kiểm cuối phiên

Xem `state-snapshot.md` «SNAPSHOT: đường dẫn». Tóm tắt (mốc giữa phiên 06:10: cis api:874 / worker:440 `0ef0d147`,
schema 290; booking:72; crm api:69, web:37, portal:10; TP `eae69868`; bk-031 — đã cũ, thay bằng số cuối):
- ECS: cis api «SNAPSHOT» / worker «SNAPSHOT» (`«SNAPSHOT SHA»`, api và worker cùng SHA), booking «SNAPSHOT»
  (`«SNAPSHOT SHA»`), crm api «SNAPSHOT», web «SNAPSHOT», portal «SNAPSHOT». Rollout COMPLETED và là revision mới
  nhất «SNAPSHOT».
- Schema: CIS «SNAPSHOT» (292 sau 291/292), Booking «SNAPSHOT» (bk-031 hay bk-032), TripPlanner «SNAPSHOT tp-NNN»,
  CRM «SNAPSHOT crm-NNN».
- Vercel Production: CIS admin «SNAPSHOT», Booking admin «SNAPSHOT», TripPlanner «SNAPSHOT», portal «SNAPSHOT».
- Bảng job: `shared.job` «SNAPSHOT queued/running», `booking.job` «SNAPSHOT», `crm.job` «SNAPSHOT»; wave mở «SNAPSHOT».
- PR còn mở mỗi repo «SNAPSHOT».
- Cố ý để BẬT cho phiên sau: «SNAPSHOT: cờ/route nào còn bật, nếu có».

## Chi phí

- LLM có log (`shared.llm_call_log`):
  - AA-790: r6b $0,894 + r7 $0,906 = **$1,80** (trần $2,00).
  - AA-919 R2 seeded-fault `3a72a697`: $0,046; R2 bước C `a720cfac`: «SNAPSHOT $».
  - AA-993: G3 a3_atomize $0,0167; job S1 kiểm log `209d9e60` $0,0514.
  - AA-784 6 thẻ địa điểm: $0,0039.
  - Mốc 06:10: tổng có log từ 23:00 = $1,0067 (r6b $0,894). Tổng cả phiên «SNAPSHOT $ từ `llm_call_log`».
- **Chi phí không có log:** 2 job S1 (17:18Z / 17:29Z, proof G2) mất dòng `llm_call_log` — đã trả tiền nhưng không đếm
  được; ước theo job `209d9e60` khoảng $0,05 mỗi job (ước, chưa verify).
- Audit geocode và audit Figma Booking: $0 (agent đọc, không gọi geocoder / LLM trả tiền).

## Bài học

Đã chuyển hết vào `skill/aa-lessons/lessons.md`:
- Vận hành: kiểm hạn STS trước vòng chạy nền dài (treo ở dấu nhắc MFA); DB Migrate `apply` chờ chuỗi pipeline địa điểm;
  script push phải từ chối khi rebase còn dở; mọi build deploy từ main phải là required check (Partner #100/#102);
  `gh run view --log` rỗng → đọc job log qua API (gộp dòng S243); `pkill -f` tự giết lệnh (gộp dòng S249/S253, thêm
  S254).
- Job runner: unwrap `NodeCancelledError.__cause__` để lần nhả job lan lên; đếm `llm_call_log` theo `job_id` sau mọi
  lần chạy trả tiền (slug tenant làm mất log).
- Frontend: cha của DataTable có `tableMinWidth` cần `minmax(0, 1fr)`; không bắt người dùng gõ UUID — dùng picker theo
  tên.

## Jira

Chưa soạn — gom sang phiên kế tiếp cùng ngày (Nghiệp, 28/10).

## Việc cần làm đầu phiên sau (S255, theo thứ tự)

1. **Nháp Jira S254** (gom từ phiên này) cùng nháp của S255, đưa Nghiệp duyệt một lần.
2. **Kết các việc đang chạy lúc chốt S254:** Booking #127/#128 merge + deploy; bk-032 + code lát 2 AA-996; kết quả
   AA-919 R2 bước C `a720cfac`.
3. **Sửa độ chính xác geocode** theo kế hoạch `docs/audits/2026-10-28-S254-geocode-audit/` (§8) — tạo issue khi Nghiệp
   đồng ý.
4. **AA-919:** lượt R2 ≤ $10 + targeted shadow run.
5. **AA-990:** luật mức tour cho chặng transit (Seoul–Busan, Oze–Nikko) + kiểm lại 14 tour sau lượt geocode retry
   28–29/10.
6. **AA-790:** vòng sau qua bộ sinh angle T8.
7. **AA-996:** chụp lại 8 frame thiếu bằng chứng + điểm audit Figma cuối.
8. **AA-994** S2b trở đi.
9. **AA-979** đợt dọn từ 03/11; **rà chi phí AWS** khi phiên ≥ 01/11 (memory `infra-cost-audit-nov-2026`).
