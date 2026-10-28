# S254 (27–28/10/2026): Booking phủ Figma + S4/S5, job nhả/nhận lại khi deploy, Releases Writing memory, audit Figma và geocode

Tác nhân: **Claude Code** (Ultracode; workflow nhiều sóng, tối đa 2 lane nặng, 1 workflow viết code một lúc). Bắt đầu
22:57 27/10 (giờ VN), chạy qua đêm; Nghiệp quay lại khoảng 06:15–06:30 sáng 28/10. Một lần chạm hạn mức phiên
(05:20–06:08). Số liệu cuối phiên lấy từ `docs/audits/2026-10-28-S254-session-close/state-snapshot.md` (chụp 11:40 +07).
Nháp Jira không soạn ở S254: gom sang phiên kế tiếp cùng ngày (Nghiệp, 10:40).

## Trạng thái

- Đầu phiên (khớp snapshot S253): cis api:867 / worker:433, booking:66, crm api:64, web:33, portal:9 — tất cả
  COMPLETED. PR mở: chỉ 4 release PR (CIS #1049, Booking #95, TP #155, Partner #64) + Infra Dependabot #411/#412.
- Cuối phiên: 20 việc đã duyệt xong hoặc ship phần lớn; làm tiếp theo master plan (sóng 7–9: lát sửa từ audit Figma,
  AA-919 R2, AA-990 chặng tự di chuyển, AA-996 lát 2). Ba việc còn chạy lúc soạn nháp log đã xong trước snapshot:
  Booking #128 `b5b2f8f4` + #127 `de3be3c3` merged + deploy; chuỗi `chain_w9.sh` áp bk-032 (DB Migrate check
  40632088145 / apply 40632244244, root bot #294) rồi merge code lát 2 Booking #130 `d78ae200` + deploy (booking:76);
  AA-919 R2 bước C `a720cfac`: informative / completed / tune, $0,375, sạch. **Regression sau #130:**
  `GET /catalog/trip-plans` → 503 `catalog_unavailable` → hotfix Booking #131 đang merge lúc chốt «ORCH: SHA merge #131
  + task def + verify 200».

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

Trạng thái Linear lúc chốt: **AA-682 Done** (S254, S4 + S5 xong); **AA-996** In Progress, đóng sau khi verify hotfix
#131 «ORCH: xác nhận Done»; **AA-997** tạo mới (Backlog, 11:25, Nghiệp đồng ý); các issue còn lại trong bảng
(AA-993, AA-994, AA-979, AA-919, AA-995, AA-990, AA-790) vẫn In Progress «ORCH: xác nhận sau đồng bộ Linear».

| Issue | Kết quả | Bằng chứng |
|---|---|---|
| AA-682 S4 | bk-030 hoá đơn nhà cung cấp + chi trả: Booking #119 → Infra #448 → DB Migrate check 40555987390 / apply 40556423522 (ready=bk-030, root bot #288); code Booking #120 `0c544765` deploy xanh. | Dry-run Dev run 40564671027: 14/14 refusal check, `verdict ok`, rolled back — `docs/audits/2026-10-27-S254-aa682-s4/`. |
| AA-682 S5 | "My Payments": contract root #289, Booking #122 `d654e398`, TripPlanner #167 `23e8b2a4`. | Scope check run-script (Infra #456) + 401 ở cả 3 đường — `docs/audits/2026-10-27-S254-aa682-s5/`. |
| AA-993 G2/G3 | CIS #1077 `74c545dc`: CancelledError trong node LangGraph không còn bị nuốt thành `rewrite_failed`. | G2: job `1ffffb96` nhả 17:31:04Z ở `writer_done`, nhận lại `resumed_from=writer_done`, xong `accounted` (1 version / 1 score / 0 review). G3: a3_atomize `a83fa22d` nhả 17:35:01Z, tiếp tục sau 116 s, 0 fingerprint trùng, $0,0167 — `docs/audits/2026-10-27-S254-aa993-g2-g5/g2-g3-cis-proof.txt`. |
| AA-993 G4 | Booking `bk_noop_sleep` (Booking #121 `5aa2e69a`, Infra #449 TF apply 40564791553 có `JOB_TEST_KINDS`; Infra #454 bật → #455 về dry_run). | Job 300 s nhả đúng 1 lần, tiếp tục từ 215 s, `succeeded` — `g4-booking-proof.txt`. |
| AA-993 G5 + Phase E | Guard deploy mới CIS #1081 `69dc6332`, Partner #99 `826df536`; root #290 `728ce9bd` (docs G5 + ADR 0017). | CIS Deploy Dev run 40577044359: `safe_to_deploy: true`, job đang chạy được nhả và nhận lại — `g5-cis-gate.txt`. |
| AA-993 (log chi phí S1) | CIS #1079 `e22e5fb6`: slug `aa_internal` trong payload làm mất mọi dòng `llm_call_log` (bug cũ, không do G2). | Job `209d9e60` ghi đủ s1_generate / grounding / judge ($0,0514). |
| AA-994 S1c + S2a | S1c eslint-kit CIS #1078 (bằng chứng đỏ run 40554868225 `aa-kit/no-raw-main`, rồi xanh); S2a vendor kit core vào Partner #102 `8af302ee`; kit core `"use client"` cho useMediaQuery CIS #1083 `a38efd49`. | Portal deploy xanh; check "Vendored CIS copies" xanh trên head Partner main `3d338504` (cùng Portal Build, Web Build). |
| AA-979 §4.3 + §4.4 | `/trip`: Infra #451 apply 40573187449 (`CIS_API_URL` cho web), Partner #100 `2fb453f7`, CIS #1082 `0ef0d147` (307 → go-dev). Bỏ bridge EXTERNAL `cis-portal`: Partner #101 `c35ad2d5`, Infra #452 apply 40579274504 + redeploy crm api:69 (0 biến bridge). | Live: aa-cis `/trip` → 307 go-dev (giữ query), go-dev 200, partner-dev 404, robots `Allow /trip/`. |
| AA-919 Releases tab | CIS #1076 `39dc01f0` (tab Releases, API có `evidence` + `summary`); sửa tràn bảng #1080 `1976bf94`; ô chọn tenant theo tên #1086 + `TenantSelect` cho 6 trang admin #1088; WM-19/WM-21 CIS #1084 + Infra #453 (mig 291/292). | Ảnh `docs/audits/2026-10-27-S254-aa919-releases/`. Vòng thử WM-22 qua API (E2E CIS admin): draft #2 (terra-family, t9_social) → evaluated → approved → active → rollback → release 0 active lại. R2 seeded-fault `3a72a697`: verdict fail / hard_stop / tune, $0,046 (đúng như mong đợi với lỗi cài sẵn). |
| AA-784 (6 thẻ xuyên biên giới) | CIS #1074 `ecef8db1`; job `7f554a44` dọn 6/6, giữ country/tên. | $0,0039; comment Linear AA-784. |
| AA-995 | Gộp ảnh trùng CIS #1073 `96eb3932` + TP #165 `1073dbc2` (deploy api:869 / worker:435); trang Golden Hour TP #168 `bb7d259b`; tràn 26 px ở `/destinations/bhutan` 390 → TP #169 `eae69868` + #170 `882f7b5d` (0 px); TP #171 `be5cbc41` (Poppins, giảm chuyển động, content-visibility, mở/đóng tất cả; `/api/health` lúc chốt). | Cover điểm đến lệch id chuẩn = 0 (live); ảnh `docs/audits/2026-10-27-S254-aa995-pages/`. |
| AA-990 (việc nhỏ) | Ảnh portal atom_replaced 4/4 (0 lỗi); `256f07bd` = nguồn chỉ 8 ngày (`source_skips_days`, không sửa); CIS #1089 `8aabaf0a` giữ chặng tự di chuyển (61 / 7.081 atom). | N1: 82/101 tour có route, BELOW_HALF 0; 2 tour transit-skip (Seoul–Busan, Oze–Nikko) cần luật mức tour; 14 tour chờ geocode — `docs/audits/2026-10-27-S254-aa990-close/`. |
| Release PRs | TP #155 `f2024ad4`, Booking #95 `49871054`, Partner #64 `77df9ea2`, CIS #1049 `c3fae2c9` (release-only, không deploy). Dependabot gom vào Infra #446 `3a322860`, đóng #411/#412. | — |
| Vercel | Region sfo1 cho CIS admin, Booking admin, TripPlanner (hiệu lực từ deploy kế). Retention 4 project: preview 2 tuần, production 1 tháng, canceled/errored 1 tuần (06:35). | Retention đặt xong 06:35 cho cả 4 project (checklist phiên; snapshot 11:40 không đọc lại cấu hình Vercel). |
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
    PDF, payment, thông báo, khoá staff bắt lý do, audit-log): #128 `b5b2f8f4` + #127 `de3be3c3` merged, deploy xanh
    (`/booking/health` git_sha `de3be3c3`).
  - Lát 2 (Supplier + ma trận giá + picker): Booking #129 (bk-032) + Infra #458 `82400b9e` → DB Migrate check
    40632088145 / apply 40632244244 (ready=bk-032, root bot #294) → code Booking #130 `d78ae200` deploy (booking:76).
    Regression: `GET /catalog/trip-plans` → 503 `catalog_unavailable` (truy vấn LATERAL đọc view/cột CIS chưa grant cho
    `booking`; stub CI che lỗi) → hotfix #131 (fail-soft + log SQLSTATE + stub khớp live) «ORCH: SHA + verify».
  - Còn: chụp lại 8 frame thiếu bằng chứng + chấm điểm audit cuối.
- **AA-919 Writing memory.** R2 bước C (≤ $2) `a720cfac`: informative / completed / tune, $0,375 (khớp
  `llm_call_log`), sạch. Còn: bước D (lượt R2 ≤ $10 thật) + targeted shadow run — S255.
- **AA-990.** Luật mức tour cho chặng transit (2 tour N1) + kiểm lại sau lượt geocode retry 28–29/10.
- **AA-790 vòng 7 (brand voice).** CIS #1085 merge, đối chứng r6b ($0,894, n=20) rồi r7; panel mù 9 arm (720 điểm):
  ai_tells đạt, brand_voice / reader_value không đạt luật ship → revert CIS #1087, vòng 6 giữ live —
  `docs/audits/2026-10-28-S254-aa790-r7-panel/`. Vòng sau sửa bộ sinh angle T8, không sửa prompt T9.
- **AA-993.** G2–G5 chứng minh live; Phase E mới có ADR 0017 (Proposed). Còn G4b, Phase D, Phase E thực thi.
- **AA-994.** Còn S2b trở đi.
- **AA-979.** Đợt dọn từ 03/11.
- **Audit geocode → AA-997** (tạo 11:25 khi Nghiệp đồng ý: "[Places] Geocode accuracy", Backlog, High): 9.545 tên = 7.924 resolved
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

Xem `docs/audits/2026-10-28-S254-session-close/state-snapshot.md` (chụp 11:40 +07). Tóm tắt:
- ECS: cis api :877 / worker :443 (`dev-8aabaf0a`, #1089; api và worker cùng SHA), booking :76 (`d78ae200`, #130),
  crm api :69 (`c35ad2d5`), web :37 (`3d338504`), portal :10 (`8af302ee`). Cả 6 service 1/1, rollout COMPLETED, revision
  đang chạy = revision mới nhất. Booking sau hotfix #131 «ORCH: task def + SHA».
- Schema: CIS **292** (sau 291/292), Booking **bk-032**, TripPlanner **tp-020** (không đổi), CRM **crm-022** (không đổi).
- Vercel Production: CIS admin `3e5976dc` (#1088), Booking admin `d78ae200` (#130), TripPlanner `be5cbc41` (#171);
  portal chạy Fargate (`aa-crm-dev-portal:10`), Vercel `aa-cis-portal` chỉ là đường rollback tới 03/11.
- Bảng job: `shared.job` 0 queued/running; `booking.job`, `crm.job`, wave mở «ORCH: xác nhận — snapshot chỉ đếm
  `shared.job`».
- PR còn mở: chỉ release (CIS #1075, Booking #116, TP #166, Partner #103) + bot root #291; Infra 0; Booking #131 hotfix
  đang merge «ORCH».
- Cố ý để BẬT cho phiên sau: `JOB_TEST_KINDS=1` trên Dev (CIS api + worker và Booking: `noop_sleep`, `bk_noop_sleep`);
  Vercel retention 4 project; H1/H2 required checks; writer S1 v2 + `s1_generate` = sonnet-5-5; `PLACE_PIPELINE_AUTO=on`;
  Writing memory release 0 active.

## Chi phí

- LLM có log (`shared.llm_call_log`):
  - AA-790: r6b $0,894 + r7 $0,906 = **$1,80** (trần $2,00).
  - AA-919 R2 seeded-fault `3a72a697`: $0,046; R2 bước C `a720cfac`: $0,375.
  - AA-993: G3 a3_atomize $0,0167; job S1 kiểm log `209d9e60` $0,0514.
  - AA-784 6 thẻ địa điểm: $0,0039.
  - Mốc 06:10: tổng có log từ 23:00 = $1,0067 (r6b $0,894). Tổng các khoản đã biết ở trên ≈ $2,29 (AA-790 $1,80 + R2 $0,421 + AA-993 $0,068 + AA-784 $0,004); tổng cả phiên
    theo `llm_call_log` «ORCH: $ từ `llm_call_log` 23:00 27/10 → chốt».
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
2. **Kết AA-996:** nếu hotfix Booking #131 (503 `/catalog/trip-plans`) chưa verify live lúc chốt thì verify rồi đóng
   AA-996 kèm bằng chứng; thêm test chạy truy vấn catalog trên DB thật (stub CI đã che lỗi grant).
3. **AA-997 — sửa độ chính xác geocode** theo kế hoạch `docs/audits/2026-10-28-S254-geocode-audit/` (§8); kiểm lượt
   geocode retry 28–29/10.
4. **AA-919:** lượt R2 ≤ $10 + targeted shadow run.
5. **AA-990:** luật mức tour cho chặng transit (Seoul–Busan, Oze–Nikko) + kiểm lại 14 tour sau lượt geocode retry
   28–29/10.
6. **AA-790:** vòng sau qua bộ sinh angle T8.
7. **Audit Figma Booking (sau AA-996):** chụp lại 8 frame thiếu bằng chứng + điểm audit cuối.
8. **AA-994** S2b trở đi.
9. **AA-993:** G4b, Phase D, Phase E thực thi (ADR 0017).
10. **AA-979** đợt dọn từ 03/11; **rà chi phí AWS** khi phiên ≥ 01/11 (memory `infra-cost-audit-nov-2026`).
