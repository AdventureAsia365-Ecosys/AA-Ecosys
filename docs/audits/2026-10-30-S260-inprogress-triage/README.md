---
id: OPS-08-s260-inprogress-triage
title: "S260 In Progress triage and S261 convergence plan"
description: "Phân loại 31 issue In Progress cuối S260 (đóng / làm nốt / bị chặn / chia lại) và thứ tự xử lý ở đầu S261."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-30
review_every_days: 30
related: [AA-919, AA-920, AA-921, AA-922, AA-923, AA-788, AA-790, AA-1000, AA-1002, AA-1003, AA-1004, AA-642, AA-880, AA-998, AA-896, AA-873, AA-842, AA-900, AA-952, AA-955, AA-961, AA-967, AA-945, AA-703, AA-911, AA-816, AA-994, AA-997, AA-990, AA-855, AA-820]
---

# S260 In Progress triage và kế hoạch dọn ở S261

## 1. Tóm tắt

Cuối S260 có 31 issue ở trạng thái In Progress. Mỗi issue đã được đối chiếu Done-when với bằng chứng: comment Linear, `docs/audits/`, PR và DB live.

| Nhóm | Số issue | Ý nghĩa |
|---|---|---|
| Đóng ngay | 0 | Không issue nào đạt đủ Done-when nguyên văn. AA-1002 là ứng viên duy nhất nhưng bị bác khi kiểm chéo (xem §3). |
| Làm nốt | 9 | Phần còn lại làm được ngay, $0, không cần LLM. Có 3 việc chờ ngày (≥ 01/11, ≥ 02/11, ≥ 03/11). |
| Bị chặn | 13 | Chặn vì LLM path (acc3 Error 002, khoảng 04–06/11), quyết định của tech lead hoặc business owner, hoặc mốc thời gian. Trả về Backlog hoặc Todo, ghi blocker kèm trigger. |
| Chia lại | 9 | Phần chính đã giao và đã verify live. Đóng Done-with-scope, phần còn lại chuyển sang issue có sẵn hoặc follow-up. |

**Quy tắc cho S261.** S261 mở đầu bằng lượt dọn này. Chưa nhận issue mới cho tới khi mỗi issue trong 31 issue đã ở một trong ba trạng thái:
- đã đóng, có comment bằng chứng (kể cả Done-with-scope);
- đã làm xong phần còn lại;
- đã về Backlog hoặc Todo, ghi blocker và trigger.

Mục tiêu cuối S261: số In Progress chỉ còn các issue đang làm dở thật trong phiên.

Mọi câu chữ Done-with-scope và mọi tên follow-up (§6) gom vào **một trang quyết định** cho tech lead bấm duyệt ở đầu phiên. Không hỏi lẻ từng issue.

## 2. Bảng tổng

| Issue | Tên ngắn | Nhóm | Việc còn lại | Quyết định đề xuất | Cỡ |
|---|---|---|---|---|---|
| AA-919 | Writing memory: eval + release gate | Chia lại | Comment trỏ AA-900. Hiệu chuẩn judge kappa ≥ 0.6 cần LLM | Done-with-scope. Hiệu chuẩn gộp vào AA-920 | S |
| AA-920 | Writing memory: rule vào 4 writer | Bị chặn | Release 1 cho A1 và T9 qua R2 + shadow. Chưa có rule nào được duyệt | Backlog. Chờ LLM và judge đã hiệu chuẩn | M |
| AA-921 | Writing memory: exemplar ghim, tóm tắt sở thích | Bị chặn | Kiểm ghim live ($0), review #1186. R2 WM-27/28 cần LLM | Làm phần $0, rồi Backlog | S |
| AA-922 | Writing memory: KPI tuần, soft-stop | Làm nốt | Báo cáo tuần thứ hai (≥ 02/11) và file trend | Done-with-scope sau báo cáo thứ hai | S |
| AA-923 | Writing memory: nhãn T2/A1, xoá khi offboard | Làm nốt | Lưu 2 nhãn. Erasure DRY RUN rồi chạy thật. Đăng output wm34 | Làm nốt ở S261, đóng có bằng chứng | M |
| AA-788 | T10: nâng F12/F14/F9 thành chặn | Bị chặn | Chạy lại replay $0. Pilot 20 bài cần LLM, gate đang đóng băng | Chạy replay, rồi Backlog | S |
| AA-790 | T10: gate giọng tenant, kiểm toàn vẹn | Bị chặn | Gate rubric chưa xây. brand_voice 6.75, chưa tới 7 | Backlog. Comment hai mục đã đạt | L |
| AA-1000 | T10: adjudicator LLM tầng 2 | Bị chặn | Hiệu chuẩn, shadow ≥ 50 finding, báo chi phí. Cả ba cần LLM | Backlog | M |
| AA-1002 | Infra: blueprint AWS org + LLM gateway | Chia lại | Ghi review mig 304. Slice S7/S8/S11 chuyển sang AA-642 | Done-with-scope | XS |
| AA-1003 | Report engine + catalog 63 report | Chia lại | Xuất bằng chứng report_run. FI-01 tháng 10 (≥ 03/11) | Done-with-scope R0–R4. Follow-up R5–R7 | S |
| AA-1004 | Infra: mô hình AWS gọn, Identity Center | Bị chặn | Mời member account, test SCP, đường AI, apply qua CI | Backlog. Tech lead đang tạm dừng | L |
| AA-642 | Epic Model Gateway | Chia lại | S7 batch, S8 lõi aa_llm, S11, chứng minh S9/S10 live | Viết lại thành issue giao được, chuyển Todo | L |
| AA-880 | Blueprint prod + ADR 0012 | Chia lại | Plan Terraform prod và chi phí, chờ ngày go-live | Done-with-scope. Phần prod sang AA-1004 | XS |
| AA-998 | Infra: gỡ acc1 | Bị chặn | Cost Explorer acc1 tháng 11 = 0 USD, kiểm ≥ 01/12 | Backlog, hạn 01/12 | XS |
| AA-896 | FinOps: báo cáo chi phí tháng | Làm nốt | `docs/ops/cost/2026-10.md`, đơn giá, tóm tắt 5 dòng | Làm khi ≥ 01/11, đóng kèm PR | S |
| AA-873 | Bảo mật: baseline phát hiện | Bị chặn | Dòng chi phí tháng đầu. GuardDuty chờ tech lead đồng ý | Ghi chi phí, rồi Backlog | XS |
| AA-842 | Observability: điều tra OTel | Bị chặn | Báo cáo đã xong. Spike tạm dừng theo quyết định tech lead | Backlog, không hỏi lại | XS |
| AA-900 | LLM: docs, version prompt, eval gate | Bị chặn | Một PR đổi prompt có run ID eval và chi phí hợp lệ | Todo. Chạy eval ngay khi có LLM | S |
| AA-952 | CRM-23 hoá đơn, thanh toán | Làm nốt | Slice 4: chuyển khoản, giữ chỗ, nhắc nợ, link hết hạn | Xong slice 4 thì Done-with-scope. Stripe tách riêng | L |
| AA-955 | CRM-25 hợp đồng, waiver | Làm nốt | 3 kiểm live: mã hết hạn, chấp nhận lại điều khoản, waiver | Done-with-scope. PAdES tách riêng | S |
| AA-961 | CRM-30 duty of care + lịch | Làm nốt | Kiểm live sự cố trên departure. Trùng chuyến (tuỳ chọn) | Done-with-scope. OAuth lịch tách riêng | S |
| AA-967 | CRM-35 xuất và xoá dữ liệu | Làm nốt | Xoá thật rồi verify. AA staff tải export phải bị 403 | Done-with-scope. Phần claim period tách riêng | M |
| AA-945 | CRM-17 email | Chia lại | Kiểm nhanh saved reply, note, nháp tự lưu | Done-with-scope. M365 + SMTP tách riêng | S |
| AA-703 | Epic identity (ADR 0006) | Chia lại | Bridge sang AA-911. Google cho traveller. Audit giới hạn lạm dụng | Done-with-scope | S |
| AA-911 | Đăng nhập Preview, bỏ bridge | Bị chặn | P5–P8 chờ hết code dự án | Backlog. Gom việc dọn identity cuối dự án | M |
| AA-816 | UI quản lý staff | Chia lại | Thử user bị khoá đăng nhập (tuỳ chọn). A10 sang AA-911 | Done-with-scope | S |
| AA-994 | Design system chung | Chia lại | Suppression CIS 659, Partner 293. ShellFrame, visual job, close-out | Done-with-scope, chia 3–5 issue | XL |
| AA-997 | Độ chính xác geocode | Làm nốt | Audit lại sau chuỗi 31/10, recheck aa997.1, mẫu mới, đếm trước/sau | Làm phần $0. Vẫn dưới 90% thì Done-with-scope | M |
| AA-990 | S1 v2 tới các reader | Làm nốt | Bằng chứng Booking/CRM/portal. recheck_14 sau AA-997 | Done-with-scope, hoãn parity narrate | M |
| AA-855 | UAT có video | Bị chặn | Vòng 1 chờ 3 gate. Khoảng 58 kịch bản chưa quay | Backlog, ghi 3 gate | L |
| AA-820 | Pháp lý: điều khoản AUP Anthropic | Bị chặn | Business owner chọn A/B/C và quyết có hỏi luật sư không | Todo, hạn 11/11 | S |

## 3. Đóng ngay

**Kết quả: 0 issue đóng thẳng được.**

AA-1002 là ứng viên CLOSE duy nhất. Bốn dòng Done-when nguyên văn đều có bằng chứng. Kiểm chéo vẫn bác vì ba lý do:
1. Comment mới nhất của chính issue (S260, 30/10 15:51) nâng mức Done lên "một dòng chi phí đã đối soát và budget enforcement". Việc này cần LLM path.
2. Migration 304 (S1) chưa có bản ghi review độc lập.
3. Scope gốc còn mở: plug-and-play, fallback chéo provider, S7/S8/S11, S1-infra.

Vì vậy AA-1002 chuyển sang nhóm Chia lại.

Các issue dưới đây **đóng được trong giờ đầu S261 chỉ bằng một comment**, không cần code. Chúng đóng dạng Done-with-scope nên chờ tech lead duyệt câu chữ trên trang quyết định (§6). Dòng bằng chứng viết tiếng Anh để dán thẳng vào comment Linear.

- **AA-880.** "ADR 0012 Accepted (root #320 daf49f7a, S257). Prod Terraform plan + cost moved to AA-1004 scope item 6 under ADR 0018 (root #360); L9 prod checklist copied to AA-1004 in a comment."
  - Việc kèm theo: comment checklist L9 sang AA-1004. Gồm Multi-AZ, PITR 14 d, cross-region backup, drill hằng quý, tách role, Enhanced Monitoring, pgaudit, private CNAME DSN, NAT mỗi AZ, ALB nội bộ, Security Hub/Config (trả phí, hỏi riêng), báo giá trước khi apply.
- **AA-919.** "WM-17 migration 284 + golden set 1.3.0 (134 items); WM-18 activate-requires-eval in DB + API, rollback drill on terra-family t9_social (ADR 0010); WM-19 seeded-fault R2 3a72a697 fail/hard_stop/tune at $0.046; WM-20 release 0 replay 0 byte diffs for a1/t2/t9_blog/t9_social (docs/audits/2026-10-26-S252-wm20-release0/); WM-21 targeted shadow 575b462c 3/3 pass, $0.057; WM-22 Releases tab CIS #1076/#1080 (docs/audits/2026-10-27-S254-aa919-releases/). Prompt register lives in AA-900 (CIS #1136). Judge calibration (kappa ≥ 0.6) moved to AA-920."
  - Việc kèm theo: một comment trên AA-900 trỏ về đây.
- **AA-1002.** "Blueprint full + lean, report page and decision list (section 14) delivered: docs/audits/2026-10-29-S258-aws-org-blueprint/ (root #346). LLM gateway S1–S6, S9, S10 shipped and live on Dev (CIS #1158/#1159 … #1191, main 041ba9a2), no billed traffic yet. IaC/CLI/org implementation moved to AA-1004; S7, S8, S11, S1-infra and live S9/S10 proof moved to AA-642."
  - Việc kèm theo: trước khi đóng, ghi một note review sau sự việc cho migration 304.
- **AA-816.** "Directory create/role/disable on Cognito (S242); cutover S1 (docs/audits/2026-10-19-S244-aa816-cutover/) and S2 legacy off (CIS #922: login 404, HS256 401); create_staff_user.py retired (CIS #858); Booking role via AA-680; reconcile drift 1 → 0 (CIS #1063). A10/A10a/A10b moved to AA-911."
  - Việc kèm theo (tuỳ chọn, cỡ S): khoá một tài khoản test, thử đăng nhập để thấy bị từ chối, rồi mở lại.
- **AA-703.** "Phases 0–4 delivered: pools + triggers + break-glass; CIS staff (AA-816); Booking staff (AA-680); tenant users (AA-813 via AA-939/AA-978); TripPlanner travellers by email code (AA-908, docs/audits/2026-10-25-S250-aa908-live/). Bridge issuer removal moved to AA-911; traveller Google/Facebook, Booking customer sign-in and abuse-limit audit moved to a follow-up."
  - Việc kèm theo (tuỳ chọn, $0): chạy probe giới hạn lạm dụng trên pool EXTERNAL. Gồm khoá khi sai mã, cooldown gửi lại mã, WAF theo IP. Ghi vào `docs/audits/<date>-S261-identity-abuse-limits/`.

AA-642 không đóng. Issue này được viết lại thành một issue giao được (§6).

## 4. Làm nốt trong S261

### Bước 0: giờ đầu, agent điều phối, $0

1. Kiểm trạng thái thật theo nghi thức `aa-session`. Thêm hai việc:
   - trạng thái job `dac718c6` (place_relocate);
   - một probe LLM.
2. Chuyển 13 issue Bị chặn về Backlog hoặc Todo theo §5. Mỗi issue có một comment ghi blocker và trigger. Riêng AA-921, AA-788 và AA-873 làm phần $0 trước khi chuyển.
3. Đăng trang quyết định duy nhất cho tech lead. Trang gồm:
   - câu chữ Done-with-scope (§6);
   - danh sách follow-up cần tạo (§6);
   - quyết định `hide_flagged` (AA-997);
   - quyết định CRM12 (AA-967).
4. Khi tech lead duyệt: đăng comment và đóng AA-880, AA-919, AA-1002, AA-816, AA-703. Viết lại AA-642.

### Mốc thời gian cần nhớ

| Ngày | Việc |
|---|---|
| 31/10 00:12Z | Chuỗi relocate `dac718c6` (1.005 dòng) chạy. Có thể kéo sang 01/11. |
| ≥ 01/11 | AA-896 và audit chi phí hạ tầng tháng 8–10. Số liệu là tạm tính tới 03/11. |
| ≥ 02/11 | AA-922: báo cáo KPI tuần thứ hai, trigger=schedule. |
| ≥ 03/11 | FI-01 tháng 10 (AA-1003). Số chi phí tháng 10 chốt. |
| khoảng 04–06/11 | AWS dự kiến mở lại LLM path trên acc3. |
| 11/11 | Hạn quyết định cho AA-820. |
| khoảng 13/11 | Được drop bảng quarantine của AA-923, theo quy trình Dead Table Registry. |
| khoảng 19/11 | Hết đóng băng gate (AA-788, AA-790). |
| ≥ 01/12 | Kiểm Cost Explorer acc1 cho AA-998. |

### Lane 1: CIS data/ops (nặng, ECS exec, $0)

Thứ tự trong lane: việc không phụ thuộc làm trước. AA-997 làm khi chuỗi relocate đã xong. AA-990 làm sau AA-997.

1. **AA-923** (M)
   - Chạy `scripts/aa923/wm34_dry_run.py` read-only với role cis_app. Đăng output lên AA-923 và ghi rõ là chạy sau khi đã apply quarantine.
   - Chạy `gh pr checks 1188` để xác nhận staff_authz xanh.
   - WM-32: lưu 1 nhãn trên một bản T2 và 1 nhãn trên một bản viết lại A1. Đi qua đường admin có quyền ghi: tech lead bấm, hoặc gọi API qua ECS exec. Query để chứng minh có 2 dòng và số nhãn T9 không đổi.
   - WM-33: dùng một tenant E2E tổng hợp có 1 dòng ở mỗi store học. Chạy `data_erasure` dạng DRY RUN, rồi chạy thật. Đăng số đếm trước/sau và chứng minh tenant khác giữ đủ dòng. Xác nhận hoặc chạy review độc lập cho #1188, vì đây là việc xoá dữ liệu.
   - Đóng bằng comment bằng chứng. Việc drop bảng sau 13/11 để cho quy trình Dead Table Registry.
2. **AA-921**, phần $0 (S)
   - Exemplars: chạy "Find candidates (dry run)", rồi "Add candidates" cho một tenant E2E.
   - Ghim rồi bỏ ghim, có lý do. Kiểm preview "Next draft" thấy thay đổi. Chụp ảnh.
   - Xác nhận hoặc chạy review độc lập #1186 (migration 313, dữ liệu tenant).
   - Xong thì chuyển Backlog (§5).
3. **AA-788**, phần $0 (S)
   - Chạy lại `scripts/aa788/promotion_replay.py` dạng background job, hoặc với `--limit` nhỏ hơn và chờ lâu hơn.
   - Đăng cận trên số hold mới theo từng gate và `attempt1_extra_repairs_by_gate`.
   - Chuyển Backlog.
4. **AA-997** (M). Làm khi `dac718c6` và mọi job đi kèm đã xong, `left_for_chain` gần 0.
   - Chạy lại `audit_relocated.py` và `recheck_14.py` theo RUNBOOK.md.
   - Đọc 6 dòng "regressed". Chạy dry run relocate recheck trên 1.197 dòng aa997.1 (strategy v2, aa997.3). Apply trong hạn mức credit miễn phí mỗi ngày. Đây là đòn bẩy duy nhất kéo con số gate lên.
   - Lập bảng số tên chưa resolve trước/sau: pending, unknown, non_place, so với 1.621 ở S254.
   - Rút mẫu mù mới ≥ 200 tên đã resolve, chia theo provenance. Gán nhãn bằng agent panel.
   - Đưa `hide_flagged` lên trang quyết định, kèm report mới hơn 6 giờ và 25 mẫu. Chỉ confirm khi tech lead đồng ý.
   - Nếu vẫn dưới 90%: Done-with-scope (§6).
5. **AA-990**, phần sau AA-997 (M)
   - Sửa địa điểm cho 16 tour: relocate recheck, mapbox, admin review, tách các chặng "A to B" (35 tên chưa link).
   - Chạy lại `recheck_14`. Đóng N1 cho các tour có route=Y và all_confirmed=Y.

### Lane 2: AA-Partner CRM (nặng)

Việc rẻ đóng trước. Slice 4 của AA-952 làm cuối vì cần migration và review.

1. **AA-945** (S, khoảng 15 phút): chạy Playwright trên Sen Vang. Kiểm chèn saved reply, internal note, khôi phục nháp tự lưu. Chụp ảnh, rồi Done-with-scope.
2. **AA-955** (S), ba kiểm live trên Sen Vang:
   - Xin mã ký, chờ quá TTL rồi submit. Mong đợi 422, signing log ghi `code_refused` với lý do `code_expired`.
   - Publish một bản terms mới trên một trip có proposal đã chấp nhận và deposit chưa trả. Mark paid phải trả 409 `terms_reaccept_required`. Client chấp nhận lại, Mark paid trả 200.
   - Publish một tài liệu từ chối bảo hiểm. Ký một envelope gồm waiver và phần từ chối. Kiểm panel agreements.
   - Xong thì Done-with-scope.
3. **AA-967** (M)
   - Xoá thật một client tổng hợp không có trip live. Kiểm receipt và verify. Dry run lần hai phải trả `subject_not_found`. Chờ đủ DEK cache TTL 300 s.
   - Gọi route tải export bằng token CIS staff (E2E reviewer). Mong đợi 403, ghi vào file bằng chứng.
   - Lệnh DELETE trên `crm.signature_event` với role crm_app phải lỗi. Chấp nhận `test_crm026_schema.py` làm bằng chứng, hoặc chạy DELETE có rollback qua DB Migrate run-script.
   - Đưa CRM12 lên trang quyết định. Đề xuất: coi trip cancelled hoặc completed đã qua mốc claim start là đã đóng, giữ bằng chứng chữ ký.
   - Xong thì Done-with-scope.
4. **AA-961** (S)
   - Bật một sự cố tổng hợp trên departure của một trip Sen Vang có dòng AA, ví dụ booking 963177e5. Làm qua Booking staff admin "Flag incident on departure" (cần phiên staff có quyền ghi) hoặc seed Dev.
   - Kiểm banner và task trên Sen Vang. Atlas & Hearth không được thấy gì. Sau đó gỡ sự cố.
   - Tuỳ chọn: thêm khách lead vào một trip thứ hai trùng ngày. Duty list phải hiện khách một lần, kèm cả hai trip_id.
   - Xong thì Done-with-scope.
5. **AA-952** (L)
   - Trước hết đọc `db-schema-reference.md` (crm-024). Nếu thiếu `invoice.status` enum, `claimed_at` hoặc `hold_extended_at` thì làm PR migration riêng trước.
   - Slice 4 gồm: "I have paid" → `payment_claimed` → một lần `POST /holds/{id}/extend` → task "Verify transfer". Thêm `paid_unfulfillable`, nhắc nợ (schedule + bell), trang link hết hạn không tạo payment session.
   - Đây là PR rủi ro (thanh toán, migration). Cần review độc lập trước khi merge.
   - Live trên Sen Vang:
     - claim → extend → task;
     - nhận tiền sau khi hết hạn đã gia hạn → re-hold, nếu không được thì tạo refund request;
     - trang link hết hạn;
     - void;
     - từ chối refund;
     - duyệt trên ngưỡng.
   - Xác nhận cách hiện tại là đúng ý: hạn của hoá đơn deposit bằng ngày của dòng schedule.
   - Xong thì Done-with-scope, Stripe tách riêng (§6).

### Lane 3: repo gốc, báo cáo, chi phí (nhẹ)

1. **AA-990**, phần $0 không phụ thuộc AA-997 (S):
   - Mở một proposal trip case trên một tour đã viết lại. Chụp text read-back và so với v_tour.
   - Dựng một quote dòng AA trên một tour đã viết lại trong CRM web.
   - Chụp badge master_newer trên portal.lumiguides.it.com (atlas-hearth).
   - Đăng ba comment.
2. **AA-1003** (S):
   - Đọc `/admin/reports` và danh sách report_run. Xác nhận DATA-02/03/04 và lượt chạy theo lịch 31/10 của TP-01, SEC-08, SEC-03, DEV-01, DEV-03, OPS-15 đều thành công.
   - Lưu ảnh chụp 1440 light/dark và file JSON report_run mới nhất của mỗi report vào `docs/audits/<date>-S261-evidence/`.
   - Chạy FI-01 khi ≥ 03/11, rồi Done-with-scope.
3. **AA-896 và AA-873** (S, khi ≥ 01/11):
   - Export `/admin/platform/cost`. Chạy `tools/finops/monthly_cost_report.py` cho 2026-10.
   - Thêm chi phí từng stage từ `shared.llm_call_log` (SQL read-only), đơn giá, phần credit Lift acc3 đã dùng.
   - Cùng lượt này làm audit chi phí hạ tầng tháng 8, 9, 10 theo App tag và service, giải thích các bước nhảy.
   - Ghi chi phí thật từ 28/10 tới 31/10 của KMS, CloudTrail và Access Analyzer cạnh báo giá S255, rồi comment trên AA-873.
   - Viết tóm tắt 5 dòng tiếng Việt cho business owner, đưa vào draft Jira cuối phiên.
   - Đóng AA-896 kèm PR. Nếu chạy trước 03/11 thì ghi là tạm tính.
4. **AA-922** (S, khi ≥ 02/11):
   - Gọi `GET /admin/writing-memory/metrics` để xác nhận có báo cáo thứ hai với trigger=schedule cho tuần 2026-10-26.
   - Chạy script trend, commit vào `docs/audits/<date>-S26x-aa922-trend/`.
   - Done-with-scope cho mục expiry (§6).

Ghi chú: lane 3 dùng chung số liệu chi phí cho ba issue: AA-896, FI-01 của AA-1003 và dòng chi phí của AA-873. Làm một lần.

## 5. Trả về Backlog vì bị chặn

| Issue | Blocker | Việc $0 trước khi trả về | Trigger đưa lại | Trạng thái đích |
|---|---|---|---|---|
| AA-920 | LLM path (acc3 Error 002, case 179326606700328, khoảng 04–06/11). Chưa có judge hiệu chuẩn. Chưa có rule được duyệt | Comment: WM-25/26 xong, code WM-23/24 đã live | LLM mở lại và kappa ≥ 0.6 | Backlog |
| AA-921 | LLM path cho R2 của WM-27 và soạn, chạy R2 tóm tắt sở thích của WM-28 | Kiểm ghim live và review #1186 (§4 lane 1) | LLM mở lại, sau AA-920 | Backlog |
| AA-788 | Tech lead đóng băng gate tới khoảng 19/11. LLM path cho pilot 20 bài | Chạy lại replay (§4 lane 1) | Sau 19/11 và có LLM | Backlog |
| AA-790 | LLM path cho panel và pilot. Gate đóng băng tới khoảng 19/11 cho rubric gate | Comment: integrity check (census S251) và AI-tells (r6 5.95) đã đạt | Sau 19/11 và có LLM. Chạy mẫu cố định S258 cùng hiệu chuẩn judge trước | Backlog |
| AA-1000 | LLM path (case 179326606700328). OpenAI không còn credit | Thêm số case và khoảng 04–06/11 vào mục Blocked by | LLM mở lại: chạy runner hiệu chuẩn (cap $5), rồi shadow | Backlog |
| AA-1004 | Tech lead tạm dừng. Account mới chưa có billing. AI path chờ acc3 | Không | Management account có billing: mời member, test SCP, AI path | Backlog |
| AA-998 | Chỉ còn mốc thời gian: chi phí acc1 tháng 11 chốt đầu tháng 12 | Không | Phiên đầu tiên ≥ 01/12 (đã có dòng time-gated trong backlog) | Backlog, hạn 01/12 |
| AA-873 | GuardDuty trả phí (khoảng 15–20 USD/tháng), tech lead chưa đồng ý | Ghi chi phí tháng đầu (§4 lane 3) | Tech lead đồng ý, dự kiến trước prod hoặc tenant trả tiền đầu tiên. Không hỏi lại | Backlog |
| AA-842 | Tech lead tạm dừng observability trả phí | Không | Có nhu cầu debug cụ thể, hoặc làm ledger AA-804. Không hỏi lại | Backlog |
| AA-900 | LLM path. OpenAI không còn credit, chưa có key Anthropic | Không | Probe LLM đầu phiên thấy có đường: chạy lại R2 t9_blog `--stage adhoc_aa900` (cap $2), gắn run ID và chi phí vào PR đổi prompt | Todo |
| AA-911 | Quyết định S246 của tech lead: bỏ bridge sau khi hết code dự án | Gom vào đây: A10/A10a/A10b từ AA-816 và dòng "bridge issuer removed by config" từ AA-703. Liệt kê các branch đang parked (backlog row 0q) | Hết code dự án: rebase branch, review auth, chạy 4 kiểm Done-when | Backlog |
| AA-855 | Ba gate cho vòng 1: AA-994 migrate xong các trang (nay là follow-up CIS và Partner), có LLM path, quyền ghi UAT chỉ trên Dev cho admin CIS E2E | Ghi 3 gate vào description. Đổi gate AA-994 trỏ sang các follow-up | Đủ 3 gate. Phần làm được ngay là dry-run harness (§6) | Backlog |
| AA-820 | Business owner chọn A/B/C và quyết có hỏi luật sư không | Đặt dueDate 2026-11-11. Kiểm trang legal-readiness (topic 12) đã tới business owner qua draft Jira. Không nhắc thêm | Có quyết định: chốt Schedule, bump LEGAL_VERSION, ghi "không có tenant cần báo" kèm ngày, rồi đóng | Todo |

**Khi LLM mở lại, làm theo thứ tự này:**
1. Eval AA-900 (≤ $2), để chứng minh đường gọi chạy.
2. Hiệu chuẩn judge (follow-up của AA-919 đã gộp vào AA-920).
3. Hiệu chuẩn AA-1000.
4. Release 1 của AA-920, rồi WM-27/28 của AA-921.
5. Parity narrate/compose của AA-990.
6. AA-788 và AA-790, chỉ sau 19/11.

Mọi lượt trả phí làm theo luật chạy mẫu nhỏ và ghi chi phí từng stage.

## 6. Chia lại và Done-with-scope

Mỗi dòng dưới đây có câu chữ đóng đề xuất và nơi nhận phần còn lại. Ưu tiên chuyển phần còn lại vào issue có sẵn để giữ quota Linear Free. **Chưa tạo issue nào.** Tất cả lên trang quyết định để tech lead duyệt.

| Issue | Câu chữ Done-with-scope (tiếng Anh, dán vào Linear) | Phần còn lại đi đâu |
|---|---|---|
| AA-919 | "WM-17..WM-22 eval/release machinery shipped and verified live; judge calibration (kappa ≥ 0.6 per stratum, judge_counts=true) moved to AA-920." | Gộp vào Done-when của AA-920. Không tạo issue mới |
| AA-1002 | "Blueprint (full + lean), report page and decision list delivered; LLM gateway S1–S6, S9, S10 live on Dev with no billed traffic; IaC/CLI/org moved to AA-1004; remaining gateway slices moved to AA-642." | AA-1004 và AA-642. Không tạo issue mới |
| AA-642 | Không đóng. Đổi tên: "[LLM] Gateway remaining slices: S7 batch, S8 aa_llm core for TripPlanner + CRM, S11 legacy stages to 5.5, live proof of S9/S10". Done-when viết theo từng slice. Comment: P0–P4 đã giao qua AA-518, AA-1002 và lớp Jev decide | Chính AA-642, chuyển Todo. Code S8 làm được không cần LLM. Live smoke chờ LLM |
| AA-880 | "ADR 0012 accepted (root #320); prod blueprint moved to AA-1004 item 6 under ADR 0018." | AA-1004. Không tạo issue mới |
| AA-1003 | "R0–R4 built and generated live on Dev (CIS-05 under AA-922); FI-01 October run done on or after 03/11." | Mới: "[Reporting] Catalog slices R5–R7: go-live and Booking ops, partners and agencies, growth". Backlog, trigger là các mốc kinh doanh |
| AA-945 | "Gmail send-as + SES forward-in + history import delivered; allow_platform_sender dropped by errata S247." | Mới: "[CRM] Mail send-as for Microsoft 365 and SMTP". Blocker: đăng ký app Entra và app password SMTP |
| AA-703 | "Identity phases 0–4 delivered (pools, staff CIS + Booking, tenant users, TripPlanner travellers by email code, legacy login off)." | Bridge sang AA-911. Mới: "[Identity] Traveller Google/Facebook sign-in, Booking customer app sign-in and live abuse-limit audit". Backlog, trigger là app khách Booking hoặc app Facebook |
| AA-816 | "Restated S243 Done-when met: directory create/role/disable on Cognito, sign-in, cutover S1/S2." | A10/A10a/A10b sang AA-911. Không tạo issue mới |
| AA-994 | "Phases 1–5 shipped: ADR 0016, canonical kit core + tokens in all 5 apps, kit lint at error in 4 repos, kit sync bot, KitGallery everywhere, Booking fully migrated (S6d), CIS S6a + S6b PR1/PR2." | Mới, xem bản rút gọn bên dưới |
| AA-922 | "Rule expiry proven by test_aa922_kpi_weekly; first live expiry tracked in AA-920." | AA-920. Không tạo issue mới |
| AA-952 | "Manual and bank-transfer payments, invoices, refunds with approval matrix delivered and verified live." | Mới: "[CRM W5] CRM-23b Stripe Connect Standard (test mode) + idempotent webhooks". Blocker: tài khoản Stripe test-mode platform của tech lead |
| AA-955 | "E-sign v1 = KMS-sealed text envelope, verified live (per-traveller, guardian, expired code, re-accept, waiver)." | Mới: "[CRM] CRM-25b PAdES-B-B signed PDF (pyHanko external signer over kms:Sign, embedded EN/VI font, X.509 for seal key)" |
| AA-961 | "R37 delivered; R15 sync delivered as the revocable ICS feed." | Mới: "[CRM] Calendar OAuth sync (Google calendar.events / Microsoft Graph, BYO)". Phần Graph chờ app M365 |
| AA-967 | "Export, erasure DRY RUN → run → verify and the signed-agreement exception delivered and verified live." | Mới: "[CRM] CRM-35b claim-period erasure, deferred erasure on Travelling trips, re-import into a fresh agency". Cần quyết định CRM12 |
| AA-997 | Chỉ dùng nếu sau recheck vẫn dưới 90%: "System fixes 1–6 shipped; served-pin accuracy measured at <x>% (fresh sample, with hide_flagged + non_place)." | Mới, có điều kiện: "[Places] Reach 90%: LLM-assisted adjudication of llm_point rows + alias table + hand pins". Backlog, chờ LLM |
| AA-990 | "Parity, saved-trip mapping, tenant, CRM, Booking and SEO checks met with live evidence; narrate/compose parity deferred until an LLM path exists." | Đưa vào danh sách regression sau khi có LLM, hoặc vào dry run của AA-855. Không tạo issue mới |
| AA-855 | (Không đóng, về Backlog) | Mới: "[UAT] Dry-run scenario harness: fast mode, sign-in setup per identity, ~20 public/read-only scenarios as regression". Mới: "[Auth] Dev-only UAT write permission for the E2E CIS admin" (PR auth, cần review) |

**Follow-up của AA-994, đề xuất bản rút gọn 3 issue thay cho 5:**
1. "[UI] CIS admin pages on the kit (S6b rest): suppressions 659 → 0, delete adminUi.tsx"
2. "[UI] Partner portal + CRM web on the kit (S6c): delete portal ui.tsx, suppressions 182 + 111 → 0"
3. "[UI] Kit shell, visual job and close-out (S6e + S1d/S2c + S6f/H3): shared ShellFrame, visual job 1440/390 light/dark for CIS/portal/CRM web, empty suppressions, required checks"

Issue 3 chứa PR workflow rủi ro. Bước H3 cần tech lead đăng nhập. Nếu tech lead muốn tách nhỏ hơn thì dùng bản 5 issue: tách ShellFrame, visual job và close-out thành ba issue.

**Quota Linear:**
- Bản rút gọn tạo tối đa khoảng 11 issue mới: 1 R5–R7, 1 M365/SMTP, 1 identity, 3 UI, Stripe, PAdES, calendar OAuth, CRM-35b, Places có điều kiện. Thêm 2 issue UAT nếu không làm thẳng dưới AA-855.
- Có thể gộp thêm "M365/SMTP mail" và "calendar OAuth" thành một issue "[CRM] Microsoft 365 + BYO calendar connect", vì cả hai cùng cần app Entra.
- Đổi lại, S261 đóng khoảng 18 issue. Cuối phiên export và archive các issue này, nên số issue chưa lưu trữ giảm thực.

## 7. Quy tắc giữ In Progress gọn từ S261

1. Chỉ chuyển một issue sang In Progress khi bắt đầu làm nó trong chính phiên đó. Không chuyển trước để "đánh dấu sẽ làm".
2. Cuối phiên, mỗi issue còn In Progress phải có một comment "Next: <bước cụ thể> (<ngày>)". Không có bước tiếp có ngày thì trả về Backlog hoặc Todo, ghi blocker và trigger.
3. Issue bị chặn bởi LLM, quyết định của người, hoặc mốc thời gian thì không ở In Progress. Mốc thời gian nằm ở mục "Time-gated checks" của `docs/backlog/README.md`.
4. Epic và issue ôm cả cụm việc không để In Progress. Done-when phải kiểm được trong 1–2 phiên. Việc lớn hơn thì chia theo lát giao được.
5. Khi phần chính đã giao và verify live, đóng Done-with-scope ngay. Comment ghi phần đã đạt kèm bằng chứng và nơi nhận phần còn lại. Không giữ issue mở chỉ vì một dòng bị chặn.
6. Follow-up mới phải hỏi tech lead trước, gom vào một trang quyết định ở đầu hoặc cuối phiên. Ưu tiên gộp vào issue có sẵn.
7. Snapshot cuối phiên (`state-snapshot.md`) liệt kê số In Progress và bước tiếp của từng issue. Nghi thức kết thúc của `aa-session` thêm bước kiểm này.
8. Đầu mỗi phiên chạy một probe LLM chung. Khi có đường gọi, làm theo thứ tự ở cuối §5, không mở lại từng issue riêng lẻ.
