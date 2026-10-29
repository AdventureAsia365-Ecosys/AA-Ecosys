---
id: PLAT-01-report-catalog-s258
title: Report catalog advisory (AA-1001)
description: "Tư vấn danh mục báo cáo của hệ sinh thái AA: hiện trạng, nguyên tắc, 63 báo cáo theo nhóm (ai đọc, quyết định, tần suất, kênh, mức tự động), lịch, kế hoạch tự động hoá, lộ trình build, báo cáo theo nhu cầu và việc tech lead cần duyệt."
type: report
status: draft
owner: nghiep
audience: [owner, cto, cio, engineer, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-partner, aa-cis-infra]
last_reviewed: 2026-10-29
review_every_days: 90
related: [AA-1001, PLAT-01, FIN-02, OPS-08, SEC-03, SEC-05, APP-07]
---

# Tư vấn danh mục báo cáo của hệ sinh thái (AA-1001)

Ngày: 29/10/2026 (S258). Tác nhân: Claude Code (lane tư vấn, chỉ đọc repo; không chạy gì trả phí, không tạo resource).
Chi phí: 0 USD. Phạm vi: cả 4 app (CIS, TripPlanner, Booking, Partner/CRM) + Infra + repo gốc.

> [!IMPORTANT]
> **Mọi số liệu hôm nay là số giai đoạn Dev.** Chưa có khách thật, tenant trả tiền hay booking thật; ngưỡng ghi
> "trend" hoặc "baseline" chỉ là tín hiệu xu hướng và chỉ thành mục tiêu sau tháng/quý production đầu tiên. Bảng, view,
> job kind và trang ghi "proposed" là đề xuất, **chưa tồn tại**; tên bảng/cột còn lại đã đối chiếu với
> `docs/architecture/db-schema-reference.md`.

Các file trong thư mục này:

| File | Nội dung | Ngôn ngữ |
|---|---|---|
| README.md (trang này) | Tóm tắt, hiện trạng, nguyên tắc, danh mục rút gọn, lịch, lộ trình, việc cần duyệt | Tiếng Việt |
| [catalog.md](catalog.md) | Chi tiết từng báo cáo: mục, KPI có định nghĩa + ngưỡng, nguồn dữ liệu, tần suất, kênh, chủ, lưu trữ, công build, chi phí | Tiếng Anh |
| [catalog.json](catalog.json) | Danh mục dạng máy đọc (63 báo cáo), hạt giống cho registry `docs/reports/catalog.yaml` sau này | Tiếng Anh |
| [automation-plan.md](automation-plan.md) | Một engine cho mọi báo cáo, lịch UTC, mức tự động, luật duyệt, guard, bảng template | Tiếng Anh |
| [on-demand.md](on-demand.md) | Cách yêu cầu báo cáo theo nhu cầu, SLA, luật dữ liệu, trang tự phục vụ | Tiếng Anh |
| [templates/](templates/) | 11 template, mỗi nhóm báo cáo một template | Tiếng Anh |
| [inventory.json](inventory.json) | Kiểm kê thô 145 báo cáo/trang/cảnh báo đang có (3 lane: 61 (docs, pages and process reports), 41 (automation: scheduled workflows, jobs, alerts), 43 (requirements and designed-but-not-built reports)) | Tiếng Anh |

Trang đọc (artifact riêng tư, lọc và xem chi tiết từng báo cáo): <https://claude.ai/artifact/Jiz8KaJiWrpdrvi5eJWWJ4>

## 1. Tóm tắt và khuyến nghị

**Hiện trạng một câu:** hệ thống có nhiều *trang xem trực tiếp* (overview, cost-ops, data coverage, jobs…) và nhiều
*cảnh báo theo sự kiện* (budget, anomaly, alarm, bell), nhưng gần như **không có báo cáo định kỳ nào tự đến tay người
đọc**. Các báo cáo định kỳ hiện có (snapshot cuối phiên, báo cáo tuần Jira PR-20, C4.3 hằng tuần, chi phí + năng lực
tháng, rà soát quyền quý) đều do agent làm tay trong phiên; tuần nào không có phiên là bỏ.

Năm lỗ hổng lớn nhất:

1. **Không có lịch sử số liệu.** `/admin/overview` chỉ là ảnh chụp hiện tại; không so tuần/tháng, không export, không gửi.
2. **Không có sổ đăng ký và lịch báo cáo.** Ngày đến hạn chỉ nằm trong `docs/backlog/README.md` và log phiên.
3. **Kết quả probe đêm chỉ nằm trong `GITHUB_STEP_SUMMARY`** — không ai đọc khi xanh, không có xu hướng.
4. **Trống hẳn mảng kinh doanh:** doanh thu/biên lợi nhuận, công nợ, phễu bán, khách hàng (CSAT/NPS), nguồn khách,
   đối tác (tenant/đại lý), đối soát TripPlanner → Booking (rủi ro mất lead im lặng).
5. **Một số liệu sai đã có sẵn:** Cost Ops đọc ngân sách acc2 = 250 USD (`apps/AA-CIS-App/api/services/cost_ops.py`
   dòng 62) trong khi Terraform đặt 300 USD — mọi trạng thái ngân sách acc2 sẽ lệch tới khi sửa (R0).

**Khuyến nghị:**

- Áp dụng danh mục **63 báo cáo trong 14 nhóm** (mục 4). Ưu tiên — P0: 7, P1: 25, P2: 23, P3: 8. Mức tự động — tự động 38, bán tự động 21, thủ công 3, theo yêu cầu 1.
  Hôm nay — đã có 1, có một phần 37, đã lên kế hoạch 3, chưa có 22.
- **Xây một engine dùng chung, không làm từng báo cáo lẻ:** registry YAML (`docs/reports/catalog.yaml` + `kpis.yaml`),
  bảng snapshot `shared.kpi_daily`, bảng `shared.report_run`, job kind `kpi_snapshot_daily` + `report_generate`, trang hub
  `/admin/reports`. Booking và CRM tự làm báo cáo của schema mình, CIS chỉ nhận số tổng qua contract view / `crm.ops.v1`.
- **Làm trước 7 báo cáo P0:** EX-01, EX-04, EX-06, FI-01, TP-03, OPS-12, OPS-04. Chúng trả lời ba câu mỗi sáng/mỗi tuần: hệ thống có hỏng gì không, tiền có
  trong ngân sách không, có lead nào bị rơi không.
- **Chi phí vận hành ≈ 0 USD/tháng:** báo cáo chỉ đọc dữ liệu đã lưu; không gọi LLM, không eval, không dịch vụ trả phí
  mới; Cost Explorer chỉ 1 lần refresh/tháng (≈ 0,01–0,04 USD). Công build ước tính ~107 ngày công cho toàn bộ, trong đó
  R0–R3 (nền + an toàn hằng ngày + tiền) ~21 ngày công.

## 2. Hiện trạng (kiểm kê)

Kiểm kê đầy đủ ở [inventory.json](inventory.json) (145 mục, 3 lane). Bảng rút gọn các báo cáo/trang chính:

| Báo cáo / trang hiện có | Ở đâu | Tần suất | Tự động | Thiếu gì |
|---|---|---|---|---|
| Snapshot trạng thái cuối phiên | `docs/audits/<date>-S<nnn>-session-close/state-snapshot.md` | mỗi phiên | thủ công | không script, phủ không đều (thiếu `booking.job`/`crm.job`, commit Vercel), không máy đọc được |
| Báo cáo tuần cho business owner (Jira PR-20) | Jira epic PR-20; nháp trong `jira-drafts.md` | tuần | thủ công | không template, không KPI/xu hướng; kỳ 3 nháp chưa đăng; cửa sổ chi phí từng chồng kỳ trước |
| Chi phí + năng lực tháng (FIN-02 = OPS-08) | `docs/templates/cost-report.md`, `capacity-review.md`, `tools/finops/monthly_cost_report.py`; lần đầu [S255](../2026-10-28-S255-aa838-capacity/README.md) | tháng | bán tự động | script chưa chạy trên số thật; export JSON làm tay; mẫu số unit cost làm tay; chưa có kênh gửi tóm tắt cho business owner |
| C4.3 `pg_stat_statements` hằng tuần | đoạn văn trong log phiên + probe thô `docs/audits/2026-10-29-S257-c43-w44/` | tuần | bán tự động | không template, không xu hướng, ngày đến hạn tính tay |
| Rà soát quyền quý (SEC-05) | `docs/templates/access-review.md`; lần đầu `docs/audits/2026-10-20-S245-access-review/` | quý | thủ công | phần IAM live còn chờ (F-15); không script chạy lại |
| Triage lỗ hổng tháng (SEC-03) + drift secrets | `docs/security/vulnerability-management.md`, `secrets-register.md` | tháng | thủ công | kết quả chỉ vào log phiên |
| Wave report | `GET /admin/waves/{id}/report` + Markdown trong `docs/audits/` | mỗi wave | bán tự động | chi phí theo stage và tổng chạy vs trần cộng tay; không có trang `/admin/waves` |
| Trang live CIS (overview, platform apps, cost, cost-ops, data coverage, jobs, content quality, writing memory…) | `/admin/*` | theo nhu cầu | tự động | không lịch sử, không so kỳ, không export, không gửi đi |
| Trang Booking (dashboard, billing KPI + CSV, trip checks, B2B desk, audit log) | AA-Booking `(staff)/*` | theo nhu cầu | tự động | không trang Reports, không tuổi nợ, không phễu bán theo kỳ, nhắc việc chỉ trong app |
| CRM (Home KPI, Reports A-14, access log) | AA-Partner `web/` | theo nhu cầu / kế hoạch | khung | trang Reports trống (AA-966, ≥ S263); KPI Home chưa có số |
| Portal tenant (dashboard, activity CSV, billing) | AA-Partner `portal/` | theo nhu cầu | tự động | không bảng kê sử dụng hằng tháng gửi tenant |
| Cảnh báo: AWS Budgets, Cost Anomaly, ~58 CloudWatch alarm + 15 rule, ops alert e-mail, bell | Terraform Infra, `ops_alert_email`, `shared.notifications` | sự kiện | tự động | chỉ cảnh báo từng sự kiện; không bản tin tổng hợp, không lịch sử MTTA/MTTR |
| Probe đêm (schema dump, isolation, liveness, freshness, connection budget, copy guard, CRM key diff) | workflow Infra | đêm | tự động | chỉ trong run summary; không digest, không xu hướng |
| Release-please CHANGELOG, post-deploy verify | workflow từng repo app | sự kiện | tự động | không ghi chú phát hành ngôn ngữ kinh doanh; không DORA |
| Sentry | CIS, Booking, Partner api/portal | liên tục | tự động | không bản tin lỗi tuần; Booking FE, Partner web, TripPlanner FE chưa có Sentry |
| TripPlanner | chỉ số qua `tripplanner.v_ops_traffic_daily` trên overview CIS | theo nhu cầu | tự động (đếm) | không phễu riêng, không web analytics, không Web Vitals định kỳ, không `/health` |

Dữ liệu nền **đã có sẵn và đủ** cho phần lớn danh mục: sổ LLM (`shared.llm_call_log`, `shared.llm_call_daily`), chi
phí AWS theo account/App tag (`shared.cost_explorer_snapshot`, `shared.cost_explorer_app_snapshot`), sổ nhà cung cấp
(Jev, DataForSEO, Geoapify), bảng job của 4 app, view hợp đồng Booking/TripPlanner (`v_ops_funnel_daily`,
`v_ops_traffic_daily`…), view tài chính Booking (`v_invoice_balance`, `v_payment_schedule_status`,
`v_supplier_bill_balance`), CRM (`crm.metric_event`, `crm.llm_call`, `crm.audit_event`). Dữ liệu **còn thiếu** (cần
migration, đánh dấu proposed): `shared.kpi_daily`, `shared.report_run`, nguồn khách/UTM trên `tripplanner.sessions`
(tp-NNN), khảo sát sau chuyến `booking.trip_feedback` (bk-NNN), endpoint tổng hợp trong `crm.ops.v1`.

## 3. Nguyên tắc báo cáo

1. **Mỗi báo cáo phục vụ một quyết định.** Mỗi mục trong danh mục ghi rõ ai đọc và quyết định gì. Báo cáo 90 ngày không
   ai mở thì bỏ (đếm lượt mở ở EX-06).
2. **Mỗi KPI một định nghĩa.** KPI nằm một chỗ trong `docs/reports/kpis.yaml` có ID và version. Báo cáo khác tham chiếu
   ID, không định nghĩa lại (ví dụ K-LLM-RECON ở FI-01, K-CAT-LIVE ở CIS-01). Đổi định nghĩa thì tăng version và kỳ đó
   không vẽ xu hướng.
3. **Tên lấy từ schema live.** Tên bảng, cột và giá trị trạng thái chỉ lấy từ `db-schema-reference.md` (ví dụ
   `content_piece` status `approved`, không phải `delivered`; stage CRM `booked`, không phải `won`). Bảng đề xuất ghi
   "proposed" tới khi reference có.
4. **Số do máy sinh, không gõ tay.** Báo cáo đọc snapshot (`shared.kpi_daily`) và report run. Người/agent chỉ viết các
   dòng nhận định.
5. **Không gọi dịch vụ trả phí để làm báo cáo.** Không LLM, không eval, không Cost Explorer (trừ 1 lần refresh tháng của
   FI-01), không dịch vụ trả phí mới. Công cụ trả phí mới cần báo giá và một câu "đồng ý" riêng cho đúng mục đó.
6. **App nào giữ số của app đó.** Booking, CRM, TripPlanner tự làm báo cáo từ schema mình. CIS chỉ thấy số tổng qua
   contract view hoặc `crm.ops.v1`. Nhân viên AA không thấy PII của đại lý; tenant không thấy QA, gate hay chi phí LLM.
7. **Độ nhạy quyết định kênh.** Báo cáo nền tảng được vào git. Số thương mại, số tenant và dữ liệu cá nhân ở S3 và app
   chủ khi repo gốc còn public. Account ID, ARN, resource ID không bao giờ vào repo app.
8. **Tên dễ hiểu cho người đọc.** Tên báo cáo và chữ người dùng thấy không chứa mã nội bộ (mã Jira, Linear, số luật data
   standards, mã thiết kế) — mã để trong ghi chú. Báo cáo cho tenant/đại lý dùng tên KPI thường, theo ngôn ngữ người
   dùng (mặc định tiếng Anh).
9. **Vai trò, không tên người.** Trang báo cáo công ty ghi tech lead, business owner, engineer on duty. Bản tiếng Việt là
   file `.vi.md` bên cạnh trang tiếng Anh.
10. **Thời gian rõ ràng.** Mỗi báo cáo ghi cửa sổ theo giờ ICT, giờ sinh theo UTC, và độ tươi của từng nguồn (Cost
    Explorer tạm tính 48 giờ; kết quả probe trong bản tin sáng đã cũ khoảng 20 giờ).
11. **Dev ghi là Dev.** Trước production, ngưỡng là tín hiệu xu hướng. Mục tiêu đặt sau tháng hoặc quý production đầu
    và ghi vào `kpis.yaml`.
12. **Duyệt trước khi đăng.** Mọi thứ gửi business owner hoặc người ngoài nhóm: nháp, trình một lần cuối phiên, duyệt,
    rồi mới đăng. Mỗi khẳng định nói rõ kênh nào đã kiểm live.
13. **Bằng chứng hơn trạng thái.** Dòng sẵn sàng/nghiệm thu chỉ tính là xong khi có link run, PR, video hoặc trang.
14. **Tự động phần lặp lại, template phần còn lại.** Câu hỏi hỏi hai lần thành báo cáo trong registry. Báo cáo làm tay
    hai lần thì có generator.
15. **Lỗi phải lộ ra.** Thiếu bản tin hằng ngày tự nó là tín hiệu. Run lỗi hoặc quá hạn hiện ở OPS-12, EX-06 và EX-01.

## 4. Danh mục báo cáo

63 báo cáo. Bấm ID để xem chi tiết (mục, KPI, nguồn dữ liệu, lưu trữ, công build, chi phí) trong
[catalog.md](catalog.md). Cột "Ai đọc", "Quyết định" và "Kênh" giữ tiếng Anh như trong catalog (vai trò theo quy ước
tài liệu công ty); "Kênh" rút gọn — bản đủ ở catalog. Giờ trong cột "Tần suất" là giờ Việt Nam (ICT); BD2 = ngày làm việc
thứ hai của tháng.

### 4.1 Điều hành và kinh doanh (7)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [EX-01](catalog.md#ex-01) | Gói báo cáo kinh doanh hằng tuần | business owner (primary reader), tech lead (approver) | Is the program on track this week, is spend inside budget, and which decisions must the business owner make now? | tuần (T2 08:30) | Jira comment under the weekly platform report epic PR-20 | bán tự động | có một phần | P0 |
| [EX-02](catalog.md#ex-02) | Báo cáo kinh doanh hằng tháng cho chủ doanh nghiệp | business owner (reader, decisions), tech lead (author, approver) | Where did the money go and what did it buy, is demand and commercial traction moving, and what must the business owner decide next month (pricing, tenants, go-live, paid runs)? | tháng (BD2) | S3 and /admin/reports | bán tự động | chưa có | P1 |
| [EX-03](catalog.md#ex-03) | Tăng trưởng và rời bỏ của đối tác (tenant Content studio, đại lý CRM, đối tác B2B) | business owner, tech lead, AA staff managing partners | Which partners to upsell, rescue or offboard; is the partner business growing; which plan and price work? | tháng + live | New Summary tab on /admin/platform/agencies + CSV | tự động | chưa có | P2 |
| [EX-04](catalog.md#ex-04) | Bảng chỉ số điều hành có lịch sử theo ngày (xương sống số liệu) | business owner, tech lead; feeds every periodic report | Is any headline number moving the wrong way vs last week/month, without waiting for a written report? | ngày 07:30 + live | /admin/overview new Trend tab + CSV export | tự động | có một phần | P0 |
| [EX-05](catalog.md#ex-05) | Báo cáo kinh doanh hằng quý và kế hoạch năm | business owner (approves budget), tech lead (author) | Strategy and budget for the next quarter or year: which apps to invest in, go-live timing, pricing, vendor changes. | quý | S3 + /admin/reports | bán tự động | chưa có | P2 |
| [EX-06](catalog.md#ex-06) | Sổ đăng ký và lịch báo cáo (trung tâm báo cáo) | tech lead, business owner, agents | Which recurring report is due or overdue, where is the latest copy, who approved it? | live + kiểm ngày | /admin/reports + bell | tự động | chưa có | P0 |
| [EX-07](catalog.md#ex-07) | Phễu kích hoạt đối tác mới (tenant Content studio và đại lý CRM) | business owner, AA staff managing partners, tech lead | Where do new tenants and agencies stall between invitation and first value, and who needs a hand-hold call this week? | tuần + tháng | /admin/platform/agencies Onboarding tab + section of EX-03 | tự động | chưa có | P2 |

### 4.2 Chi phí, FinOps và tài chính (9)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [FI-01](catalog.md#fi-01) | Báo cáo chi phí hằng tháng (nửa chi phí của rà soát năng lực OPS-08) | tech lead (approves), business owner (five-line Vietnamese summary) | Was the month's spend justified, which items to cut or scale, are we within budget? | tháng (BD2) | docs/audits/<date>-S<nnn>-capacity-review/cost.md via root PR next to the OPS-08 README | bán tự động | có một phần | P0 |
| [FI-02](catalog.md#fi-02) | Bản tin chi tiêu và số dư nhà cung cấp hằng tuần (e-mail tự động) | tech lead, business owner (opt-in) | Slow a paid run, top up a vendor credit, or investigate a spend jump before the month closes? | tuần (T2 08:30) | SES e-mail to report subscribers + Weekly panel on /admin/cost-ops | tự động | chưa có | P1 |
| [FI-03](catalog.md#fi-03) | Phân bổ chi phí LLM theo bước, vai trò, model, tenant và app | tech lead, engineer, business owner (tenant margin) | Which stage or model to optimise or reroute, which tenant is unprofitable, how much shadow/eval spend to keep? | tháng + live | /admin/cost-ops LLM tab with CSV export + FI-01 section | tự động | có một phần | P1 |
| [FI-04](catalog.md#fi-04) | Sổ nhà cung cấp nền tảng: chi phí, số dư, hạn mức, hợp đồng | tech lead, business owner | Renew, downgrade, top up or replace a platform vendor; which contracts/DPAs are missing before prod? | tháng + quý + sự kiện | Sections of FI-01 / EX-05 | bán tự động | có một phần | P1 |
| [FI-05](catalog.md#fi-05) | Chi phí đơn vị (mỗi tour, kế hoạch chuyến đi, booking, đại lý) | business owner, tech lead | Is the platform getting cheaper per unit of output; what price floor do tenant plans and bookings need? | tháng + live | /admin/platform/cost Unit costs card + FI-01 section | tự động | có một phần | P1 |
| [FI-06](catalog.md#fi-06) | Ngân sách so với thực chi và thời gian còn dùng credit | business owner (approves budget), tech lead (proposes) | Raise, cut or reallocate budgets per app; spend or save credits; approve next year's budget. | tháng + quý + năm | /admin/cost-ops Budgets tab + FI-01 / EX-05 sections | bán tự động | có một phần | P1 |
| [FI-07](catalog.md#fi-07) | Doanh thu, booking và biên lợi nhuận (bản nhanh tuần + đóng sổ tháng) | business owner, Booking admin (finance), sales lead | Is the travel business profitable per booking, channel and destination; are pricing rules and supplier contracts right? | tuần + tháng (chốt BD5) | New Booking staff page Finance reports stored under the booking/ prefix of the reports bucket | tự động | có một phần | P2 |
| [FI-09](catalog.md#fi-09) | Kỳ tính phí tenant và đại lý hằng tháng | business owner (approves charges), AA staff (billing) | What each partner owes this month (plan + overage) and whether plans and quotas are priced right. | tháng (BD2) | CIS admin billing-run view in /admin/reports | bán tự động | chưa có | P3 |
| [BK-03](catalog.md#bk-03) | Tuổi nợ phải thu, phải trả và thu hồi công nợ | Booking admin (finance), sales, contracting staff, business owner | Whom to chase today, which supplier bills to pay this week, is cash enough to pay suppliers before customers pay? | tuần + tháng | Booking billing page Aging tab with CSV | tự động | chưa có | P1 |

### 4.3 Vận hành sản phẩm theo app (10)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [CIS-01](catalog.md#cis-01) | Sức khoẻ catalog hằng tuần | tech lead, content ops, business owner (headline) | Is the sellable catalog complete and current; which countries or tours need rewrite, photos, republish or retirement this week? | tuần + live | /admin/data-coverage Weekly tab + SES digest to subscribers | tự động | có một phần | P1 |
| [CIS-03](catalog.md#cis-03) | Phân phối nội dung cho tenant (nội bộ AA) | AA admin, tech lead, business owner | Which tenants get value; where does the T-series hold or regenerate too much; who is near quota or overage? | tháng + live | /admin/tenant-activity Monthly tab | tự động | có một phần | P2 |
| [TP-01](catalog.md#tp-01) | Phễu TripPlanner hằng tuần | business owner, tech lead | Is the B2C planner turning visitors into advisor inquiries; where does the funnel leak? | tuần + live | /admin/overview TripPlanner card with week/month comparison | tự động | có một phần | P1 |
| [BK-01](catalog.md#bk-01) | Bản tin vận hành Booking mỗi sáng | ops staff, sales, Booking admin | What must staff do today: overdue checks, unconfirmed suppliers, expiring quotes and holds, unpaid deposits for near departures? | ngày T2-T6 08:00 | One e-mail per staff member via bk_notify_email + Booking dashboard Today panel | tự động | có một phần | P1 |
| [BK-02](catalog.md#bk-02) | Phễu bán hàng Booking (tuần/tháng) | business owner, sales lead | How fast and how often do inquiries become confirmed trips; which source and channel convert; where do cases stall? | tuần + tháng | Booking dashboard Reports tab with CSV | tự động | có một phần | P2 |
| [BK-04](catalog.md#bk-04) | Hiệu suất và hợp đồng nhà cung cấp du lịch | contracting staff, Booking admin | Which suppliers confirm slowly, decline often or cause incidents; which contracts to renew or renegotiate before they expire? | tháng + tuần (hợp đồng) | Booking suppliers page Performance tab + CSV | tự động | có một phần | P3 |
| [BK-05](catalog.md#bk-05) | Kênh B2B: báo giá và giữ chỗ | sales lead, business owner | Are partner agencies converting holds into bookings; are hold rules right? | tháng | Booking b2b-desk Report tab + CSV | tự động | có một phần | P3 |
| [BK-06](catalog.md#bk-06) | Lấp đầy chuyến khởi hành và sự cố trên tuyến | ops staff, sales lead, business owner | Which fixed departures will run, need a push or should be cancelled; are on-trip incidents cleared fast? | tuần | Booking departures page Report tab + CSV | tự động | chưa có | P3 |
| [OPS-14](catalog.md#ops-14) | Sức khoẻ bộ chạy job của cả bốn app | engineer, tech lead | Which job kinds fail, retry, run late or never run; tune concurrency or fix code? | tuần + ngày | /admin/jobs new All apps tab | tự động | có một phần | P1 |
| [OPS-15](catalog.md#ops-15) | Ảnh chụp trạng thái cuối phiên (máy đọc được) | tech lead, next agent session | What exactly is live now (images, migrations, jobs, PRs) so the next session starts from facts? | sự kiện (cuối phiên) | docs/audits/<date>-S<nnn>-session-close/state-snapshot.md + state-snapshot.json via root PR | bán tự động | có một phần | P1 |

### 4.4 Chất lượng nội dung AI (3)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [CIS-05](catalog.md#cis-05) | KPI chất lượng nội dung AI hằng tuần (Writing Memory) | tech lead, reviewer | Is writing quality stable or drifting; keep or roll back the active writing-memory release; is the judge reliable enough to gate? | tuần | /admin/writing-memory KPIs tab + SES digest | tự động | đã lên kế hoạch | P1 |
| [CIS-06](catalog.md#cis-06) | Báo cáo đánh giá / phát hành prompt (theo sự kiện) | tech lead, reviewer | Approve, reject or roll back a writing-memory release or prompt version. | sự kiện (eval/release) | /admin/writing-memory release drawer with a printable summary | tự động | có một phần | P2 |
| [CIS-07](catalog.md#cis-07) | Báo cáo wave chạy lại và đợt chạy trả tiền (kèm chi phí) | tech lead, business owner (large runs) | Was the wave complete and within budget; start, scale or stop the next wave? | sự kiện (mỗi wave) | Small /admin/waves page + Markdown in docs/audits/<date>-S<nnn>-<wave>/ | tự động | có một phần | P1 |

### 4.5 Chất lượng dữ liệu và đối soát (6)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [CIS-02](catalog.md#cis-02) | Chất lượng địa điểm và geocode | tech lead, content ops | Is place data accurate enough for TripPlanner maps and Booking itineraries; continue, change or stop the geocode chain (AA-997)? | tháng + sau mỗi đợt geocode | /admin/places summary card | bán tự động | có một phần | P2 |
| [TP-03](catalog.md#tp-03) | Đối soát yêu cầu tư vấn TripPlanner sang Booking (mỗi giờ + tổng hợp ngày) | ops staff, tech lead | Did every customer inquiry reach Booking and become a trip case; which ones are parked or failed? | mỗi giờ + ngày 08:00 | Line in OPS-12 and BK-01 | tự động | chưa có | P0 |
| [DATA-01](catalog.md#data-01) | Bản tin toàn vẹn dữ liệu hằng đêm (tổng hợp các probe) | tech lead, engineer | Did any nightly integrity probe fail; which layer is stale or drifting? | đêm | Each workflow uploads a summary JSON to the reports bucket | tự động | có một phần | P1 |
| [DATA-02](catalog.md#data-02) | Đối soát liên ứng dụng hằng tuần | tech lead, engineer | Are events flowing between apps without loss or lag; does the LLM ledger match the bill? | tuần | Section of OPS-13 weekly | tự động | chưa có | P2 |
| [DATA-03](catalog.md#data-03) | Báo cáo thay đổi schema và hợp đồng dữ liệu | engineer, tech lead, agents | Which migrations and contract changes landed; did any break a consumer? | sự kiện + tuần | PR body of the schema-reference bot PR | tự động | có một phần | P3 |
| [DATA-04](catalog.md#data-04) | Tăng trưởng sổ ghi và tuân thủ thời hạn lưu trữ | tech lead | Are ledgers inside their retention windows and is growth sustainable? | tháng | Section of OPS-08 | tự động | có một phần | P2 |

### 4.6 Độ tin cậy, năng lực và SLO (6)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [TP-02](catalog.md#tp-02) | Hiệu năng web và độ ổn định Lambda TripPlanner hằng tháng | tech lead, engineer | Do the map pages meet Core Web Vitals and are Browse/Assembly Lambdas healthy; what to optimise next? | tháng + mỗi release FE | GitHub Actions summary JSON to S3 | bán tự động | có một phần | P2 |
| [OPS-12](catalog.md#ops-12) | Bản tin sức khoẻ nền tảng mỗi sáng | tech lead, engineer on duty | Is anything broken or drifting that needs work today? | ngày 08:00 | SES e-mail to subscribers + Daily tile on /admin/reports | tự động | chưa có | P0 |
| [OPS-13](catalog.md#ops-13) | Kiểm tra SLO và hiệu năng DB hằng tuần | tech lead, engineer | Did any DB SLI miss its objective two weeks running; which query or index to fix? | tuần (T2) | S3 + /admin/reports | bán tự động | có một phần | P1 |
| [OPS-08](catalog.md#ops-08) | Rà soát năng lực, SLO và độ sẵn sàng hằng tháng | tech lead (approves), CTO/CIO guides | Is capacity enough for next month; resize, tune or accept; which C3 triggers fired? | tháng (BD2) | docs/audits/<date>-S<nnn>-capacity-review/README.md via root PR | bán tự động | có một phần | P1 |
| [OPS-16](catalog.md#ops-16) | Dự báo năng lực và tăng trưởng (6-12 tháng) | tech lead, business owner (budget) | When will storage, connections, CPU, LLM spend or free-plan limits run out under the planned waves and go-live, and what to provision or change ahead of time? | quý | docs/audits/<date>-S<nnn>-capacity-forecast/README.md via root PR | bán tự động | chưa có | P2 |
| [OPS-03](catalog.md#ops-03) | Biên bản diễn tập sao lưu, khôi phục và rollback | tech lead, CTO | Can we restore and roll back within target; which runbook step failed? | sự kiện; quý từ prod | docs/audits/<date>-S<nnn>-<drill>/ via root PR | thủ công | có một phần | P2 |

### 4.7 Sự cố (1)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [OPS-04](catalog.md#ops-04) | Báo cáo sự cố và postmortem (gồm sự cố chi phí) | tech lead, engineer, business owner (SEV1-2 summary) | What broke or overspent, is it stopped, which guard prevents a repeat? | sự kiện (SEV1-2) | docs/ops/postmortems/<YYYY-MM-DD>-<slug>.md (folder does not exist yet | thủ công | có một phần | P0 |

### 4.8 Bảo mật, quyền riêng tư và pháp lý (6)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [CRM-06](catalog.md#crm-06) | Truy cập và quyền dữ liệu của đại lý | agency owner (controller); AA staff counts only | Who accessed traveller data, which exports and erasures ran, is the agency meeting its controller duties? | tháng + theo nhu cầu | CRM settings access-log and data pages | tự động | có một phần | P3 |
| [SEC-03](catalog.md#sec-03) | Báo cáo vệ sinh bảo mật hằng tháng (lỗ hổng, secret, probe cách ly) | tech lead, CIO guide | Which vulnerabilities, secret drifts or isolation failures must be fixed this month; which ignores expire? | tháng (BD2) | docs/audits/<date>-S<nnn>-security-review/README.md via root PR + generated docs/generated/security-alerts.md | bán tự động | có một phần | P1 |
| [SEC-05](catalog.md#sec-05) | Rà soát quyền truy cập hằng quý | tech lead, CIO/CTO guides | Who can reach each app and system, and which access to remove? | quý | docs/audits/<date>-S<nnn>-access-review/README.md via root PR | bán tự động | đã có | P1 |
| [SEC-08](catalog.md#sec-08) | Rà soát thao tác đặc quyền và nhật ký kiểm toán | tech lead | Were privileged actions expected and recorded; is the audit chain intact? | tháng | Section of SEC-03 | bán tự động | có một phần | P2 |
| [SEC-09](catalog.md#sec-09) | Báo cáo quyền riêng tư và yêu cầu của chủ thể dữ liệu | tech lead, business owner (legal calls) | Are data-subject requests, erasures, retention and consent handled on time? | quý + đếm tháng | docs/audits/<date>-S<nnn>-privacy-review/ via root PR | bán tự động | có một phần | P2 |
| [SEC-10](catalog.md#sec-10) | Theo dõi sẵn sàng pháp lý, chính sách và điều khoản AI | business owner (decisions, lawyer is their call), tech lead | Which privacy, terms, DPA, sub-processor and AI-clause items are still open before go-live, and which need a business or legal answer this month? | tháng + quý | docs/audits/<date>-S<nnn>-legal-readiness/README.md via root PR | bán tự động | có một phần | P1 |

### 4.9 Phân phối phần mềm (3)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [DEV-01](catalog.md#dev-01) | Báo cáo phân phối phần mềm và DORA hằng tháng | tech lead, CTO guide | Is delivery fast and safe enough; where to invest in CI, tests or review? | tháng | S3 + /admin/reports | tự động | chưa có | P1 |
| [DEV-02](catalog.md#dev-02) | Ghi chú phát hành theo app | business owner (Vietnamese summary), staff, engineers | What changed for users in this release; is any action needed from staff or tenants? | sự kiện (release) | CHANGELOG.md + Jira epic comment for user-visible releases | bán tự động | có một phần | P2 |
| [DEV-03](catalog.md#dev-03) | Dòng chảy công việc kỹ thuật hằng tuần | tech lead | Is work converging (In Progress closing, PRs merging) and are master-plan slots on track? | tuần | /admin/reports + section of EX-01 | tự động | có một phần | P1 |

### 4.10 Sẵn sàng go-live và nghiệm thu (2)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [OPS-17](catalog.md#ops-17) | Bảng điểm sẵn sàng go-live theo app | business owner (go/no-go), tech lead | Is each app ready to go to production, and what blocks the go-live date? | sự kiện, rồi tuần | docs/audits/<date>-S<nnn>-go-live-readiness/README.md via root PR + a clickable decision page for the busines… | bán tự động | chưa có | P1 |
| [DEV-04](catalog.md#dev-04) | Biên bản nghiệm thu UAT theo app | business owner (accepts), tech lead, staff testers | Does each app do what the business needs, recorded on video, and is it accepted for go-live? | sự kiện (UAT) | docs/audits/<date>-S<nnn>-uat/README.md via root PR + a clickable sign-off page for the business owner | thủ công | đã lên kế hoạch | P2 |

### 4.11 Khách hàng (1)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [CX-01](catalog.md#cx-01) | Mức hài lòng của khách và đánh giá sau chuyến đi | business owner, sales lead, contracting staff; agency owner for CRM agencies (own data only) | Are travellers happy, which suppliers, guides or itineraries cause complaints, and which reviews can be used in marketing (with consent)? | tháng + mỗi phản hồi xấu | Booking Reports tab | tự động | chưa có | P2 |

### 4.12 Tăng trưởng và marketing (2)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [MKT-01](catalog.md#mkt-01) | Nguồn khách và phễu marketing | business owner, sales lead | Which channels bring travellers and partners that convert, and where to spend marketing effort? | tháng + dòng tuần | /admin/overview Acquisition card + EX-02 section | tự động | chưa có | P2 |
| [MKT-02](catalog.md#mkt-02) | Hiệu quả SEO và nội dung | business owner, content ops, tenant owner (own sites, later) | Is published content reaching search demand; which tours or tenant posts to refresh; is DataForSEO spend paying off? | tháng | /admin/content-quality SEO tab | bán tự động | chưa có | P3 |

### 4.13 Báo cáo gửi tenant và đại lý (6)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [CIS-04](catalog.md#cis-04) | Bảng kê sử dụng hằng tháng gửi tenant Content studio | tenant owner/admin (Content studio) | Tenant checks what it used and pays for, and whether to change plan. | tháng (BD2) | Tenant portal account/billing page + e-mail to the tenant owner | tự động | có một phần | P3 |
| [CRM-01](catalog.md#crm-01) | Pipeline và chuyển đổi của đại lý | agency owner/admin, agency agents | Which leads and sources convert, where trips stall, why trips are lost. | live + tháng | CRM web Reports page + Home KPI tiles | tự động | đã lên kế hoạch | P1 |
| [CRM-02](catalog.md#crm-02) | Thời gian phản hồi và khối lượng việc của đại lý | agency owner/admin | Are travellers answered fast enough; is any agent overloaded or late on tasks? | tuần + live | CRM Reports page section + weekly in-app digest for the agency owner | tự động | chưa có | P2 |
| [CRM-03](catalog.md#crm-03) | Sức khoẻ kênh e-mail của đại lý | agency owner/admin; AA staff (counts only) | Are connected mailboxes working; must the agency reconnect? | ngày + tuần | CRM settings health card | tự động | có một phần | P2 |
| [CRM-04](catalog.md#crm-04) | Sử dụng trợ lý AI trong CRM | agency owner/admin, AA staff (counts), tech lead | Is the assistant used and useful per agency; is cost within entitlement; are refusals or errors rising? | tháng + live | CRM Reports page AI section | tự động | chưa có | P2 |
| [CRM-05](catalog.md#crm-05) | Báo cáo tháng gửi chủ đại lý | agency owner | How did the agency do this month and what to fix next month? | tháng (BD2) | CRM Reports page + e-mail to the agency owner | tự động | chưa có | P2 |

### 4.14 Theo nhu cầu (1)

| ID | Tên | Ai đọc | Quyết định | Tần suất | Kênh | Tự động | Trạng thái | Ưu tiên |
|---|---|---|---|---|---|---|---|---|
| [DATA-05](catalog.md#data-05) | Yêu cầu báo cáo hoặc trích xuất số liệu theo nhu cầu | business owner, tech lead, Booking admin, AA staff | Answer a specific question not covered by a scheduled report, or rerun a report for another period. | theo nhu cầu | /admin/reports Request form or a Jira/Linear comment | theo yêu cầu | chưa có | P1 |

## 5. Lịch báo cáo

Giờ Việt Nam (ICT = UTC+7); lịch UTC chi tiết ở [automation-plan.md](automation-plan.md#2-schedule-utc-ict--utc7).

| Nhịp | Khi nào (ICT) | Báo cáo | Ai nhận |
|---|---|---|---|
| Mỗi giờ | liên tục | TP-03 kiểm lead TripPlanner → Booking (chỉ báo khi có lệch) | ops staff (bell + e-mail khi lệch) |
| Hằng đêm | 09:17–12:13 (02:17–05:13 UTC) | DATA-01 các probe toàn vẹn dữ liệu (đã chạy; thêm bước lưu JSON) | vào bản tin sáng hôm sau |
| Hằng ngày | 07:30 | EX-04 chụp KPI ngày hôm trước vào `shared.kpi_daily` | (nguồn cho mọi báo cáo) |
| Hằng ngày | 08:00 | OPS-12 bản tin sức khoẻ nền tảng (mọi ngày); TP-03 tổng hợp ngày; BK-01 bản tin vận hành Booking (T2–T6) | tech lead; nhân viên Booking |
| Hằng ngày | 09:00 | EX-06 kiểm báo cáo đến hạn/quá hạn | tech lead (bell) |
| Hằng tuần, thứ Hai | 07:43 | OPS-13 chạy probe `pg_stat_statements` | — |
| Hằng tuần, thứ Hai | 08:30 | EX-01 nháp gói tuần; FI-02 bản tin chi tiêu; CIS-01, CIS-05, TP-01, BK-02, BK-03, BK-06, OPS-13/14, DATA-02, DEV-03, EX-07, FI-07 bản nhanh, BK-04 hạn hợp đồng | business owner (EX-01 qua Jira sau khi duyệt, đăng trước thứ Ba); tech lead; nhân viên |
| Hằng tháng, BD2 | 09:00 | EX-02, FI-01 (+FI-03/05/06), FI-07, FI-09, OPS-08, SEC-03 (+SEC-08/09/10), DEV-01, CIS-02/03/04, BK-04, BK-05, CRM-05, MKT-01, MKT-02, CX-01 | business owner (tóm tắt 5 dòng), tech lead, tenant/đại lý (bảng kê) |
| Hằng tháng, BD3 | — | làm mới phần chi phí từ tạm tính sang chốt | — |
| Hằng tháng, BD5 | — | hạn duyệt EX-02, FI-01, OPS-08; FI-07 chốt sổ | tech lead, business owner |
| Hằng quý, BD2 tháng 1/4/7/10 | 09:00 | EX-05, SEC-05 (nhắc), SEC-09, SEC-10 đủ, OPS-16 | business owner (duyệt ngân sách), tech lead |
| Hằng năm | tháng 12 hoặc trước go-live | kế hoạch năm + ngân sách theo app (EX-05, FI-06) | business owner |
| Theo sự kiện | khi xảy ra | CIS-06 (eval/release), CIS-07 (wave), OPS-04 (sự cố SEV1-2, chi phí bất thường), OPS-15 (cuối phiên), OPS-03 (diễn tập), DATA-03 (migration), DEV-02 (release), DEV-04 (UAT), OPS-17 (khi có ngày go-live, sau đó hằng tuần) | tuỳ báo cáo |
| Theo nhu cầu | khi có yêu cầu | DATA-05 (xem mục 8) | người yêu cầu |

Lần chạy thật gần nhất cần làm: **FI-01 + OPS-08 cho tháng 10/2026, từ 03/11/2026** (sau khi Cost Explorer chốt số);
làm tay theo template mới được, không cần chờ engine.

## 6. Tự động hoá

Tóm tắt (chi tiết: [automation-plan.md](automation-plan.md)):

- **Một engine cho mọi báo cáo** trong CIS: registry YAML → snapshot `shared.kpi_daily` (00:30 UTC) → job
  `report_generate` sinh JSON + Markdown (+ PDF cho bảng kê) lên bucket báo cáo theo `<app>/<report_id>/<period>/` →
  ghi `shared.report_run` → gửi qua SES (đường `ops_alert_email` có sẵn), bell, trang `/admin/reports`. Booking và CRM
  dùng bảng job và bảng run của mình.
- **Ba mức:** tự động hoàn toàn (máy sinh và gửi), bán tự động (máy sinh số, người viết nhận định và duyệt), thủ công
  (người viết theo template). Báo cáo cho business owner và Jira luôn qua duyệt; nháp gom trình một lần cuối phiên.
- **Guard:** chỉ đọc dữ liệu đã lưu; mỗi app chỉ đọc schema mình; số thương mại không vào git khi repo gốc public;
  mỗi generator có test đối chiếu tên cột với schema reference và snapshot Markdown mẫu.
- **Template:** 11 template trong [templates/](templates/) phủ mọi nhóm; khi áp dụng thì chuyển vào `docs/templates/`
  (thay `cost-report.md` và `postmortem.md`) và đăng ký ID mới trong `docs/README.md`.

## 7. Lộ trình build

| Lát | Báo cáo | Công | Chi phí | Khi nào | Phụ thuộc |
|---|---|---|---|---|---|
| R0 Sửa số trước khi xây | FI-02, FI-06, EX-04, EX-01 | XS (0,5 ngày công): đặt `COST_OPS_AWS_BUDGETS_USD` acc2=300, acc3=250 cho task def CIS api/worker hoặc làm xong AA-665 C5 đọc AWS Budgets live; đăng ký ID mới (PLAT-03, PLAT-04, APP-11..APP-15, OPS-12..OPS-17, SEC-08..SEC-10) trong `docs/README.md` | 0 USD | phiên tới (S258) | — |
| R1 Lõi báo cáo: registry, snapshot, run, hub | EX-06, EX-04, DATA-05 | M (6–7 ngày công): YAML catalog + kpis có lint, migration CIS `shared.kpi_daily` + `shared.report_run`, job kind `kpi_snapshot_daily` + `report_generate`, trang `/admin/reports`, prefix bucket | 0 USD | S258–S259 | R0 |
| R2 Lưới an toàn hằng ngày | OPS-12, TP-03, DATA-01, OPS-04 | S-M (5 ngày công): digest, kiểm lead mỗi giờ + grant `booking.inbox_events`, bước upload JSON probe + OIDC role, thư mục postmortem + postmortem sự cố acc3 S257 | ~0 USD (SES) | S259–S260 | R1 |
| R3 Tiền: chi phí tuần và tháng | EX-01, FI-01, FI-02, FI-03, FI-05, FI-06, FI-04, OPS-08 | M (9 ngày công) | 0–0,04 USD/tháng | S260–S261; FI-01 tháng 10 làm tay từ 03/11 trước khi lát này xong | R0, R1 |
| R4 Chất lượng, độ tin cậy, phân phối | CIS-01, CIS-05, CIS-06, CIS-07, OPS-13, OPS-14, DATA-02, DATA-03, DATA-04, SEC-03, SEC-08, DEV-01, DEV-03, OPS-15, TP-01 | L (22 ngày công; CIS-05 là AA-922 slot S262) | ~0 USD; workflow root dùng phút Actions miễn phí sau khi repo private (11/2026) | S261–S265 | R1, R2 |
| R5 Trước go-live và vận hành Booking | OPS-17, SEC-10, SEC-09, DEV-04, OPS-03, BK-01, BK-03, FI-07, EX-02 | L (17 ngày công) | ~0 USD (SES); < 1 USD mỗi lần diễn tập restore | khi có ngày go-live, chậm nhất 4 tuần trước; file checklist OPS-17, SEC-10 làm được ngay | R1, R3 |
| R6 Đối tác và đại lý | EX-03, EX-07, CIS-03, CIS-04, FI-09, CRM-01..CRM-06 | L (25 ngày công; CRM-01/02 nằm trong AA-966 ≥ S263; cần endpoint tổng hợp `crm.ops.v1`) | ~0 USD | S263+; gấp khi mời tenant/đại lý ngoài đầu tiên | R1; đổi hợp đồng `crm.ops.v1` |
| R7 Tăng trưởng, khách hàng, dự báo | MKT-01, MKT-02, CX-01, BK-02, BK-04, BK-05, BK-06, CIS-02, TP-02, OPS-16, EX-05 | L (22 ngày công; gồm migration tp-NNN nguồn khách và bk-NNN bảng khảo sát) | 0 USD (Search Console miễn phí sau khi xác minh — hỏi trước; Vercel Speed Insights/Web Analytics chỉ khi có báo giá và đồng ý) | trước marketing go-live; OPS-16 và EX-05 vào đầu quý tới (01/2027) | R1, R3; cần chuyến đi thật đầu tiên cho CX-01 |

Tổng ~107 ngày công cho toàn bộ danh mục; nhịp đề xuất: R0–R3 trong 3–4 phiên tới, R4 theo slot master plan,
R5–R7 theo mốc kinh doanh (ngày go-live, tenant/đại lý đầu tiên, chuyến đi thật đầu tiên).

## 8. Báo cáo theo nhu cầu

Tóm tắt (chi tiết: [on-demand.md](on-demand.md)):

- Dùng khi câu hỏi chưa có báo cáo định kỳ nào trả lời, cần chạy lại báo cáo cho kỳ khác, hoặc cần trích xuất một lần.
  Yêu cầu qua form trên `/admin/reports` hoặc comment Jira/Linear, ghi: câu hỏi, quyết định cần hỗ trợ, kỳ, người đọc,
  định dạng, độ nhạy, hạn, có được gọi dịch vụ trả phí không (mặc định: không).
- SLA: chạy lại báo cáo registry — trong ngày làm việc; đếm/xuất từ view có sẵn — 1 ngày; phân tích mới trên dữ liệu có
  sẵn — 3 ngày; cần thu thập dữ liệu mới/migration — thành việc backlog; cần gọi API/LLM trả phí — chỉ sau báo giá và
  một câu "đồng ý".
- Kết quả theo độ nhạy của dữ liệu đầu vào nhạy nhất: số thương mại/cá nhân vào S3 của app chủ, không vào git/Jira; phân
  tích kỹ thuật vào `docs/audits/`. Câu hỏi lặp lại 2 lần trong 90 ngày thì đưa vào registry thành báo cáo định kỳ.

## 9. Việc tech lead cần duyệt

| # | Việc | Bối cảnh | Đề xuất |
|---|---|---|---|
| 1 | Chấp nhận danh mục và thứ tự ưu tiên | 63 báo cáo; P0: EX-01, EX-04, EX-06, FI-01, TP-03, OPS-12, OPS-04 | Duyệt danh mục làm nguồn cho registry; build theo R0 → R7 |
| 2 | Sửa ngân sách acc2 trong Cost Ops (R0) | Code dùng 250 USD, Terraform 300 USD | Đặt `COST_OPS_AWS_BUDGETS_USD` ngay (5 phút, không đổi code), sau đó làm AA-665 C5 đọc AWS Budgets live |
| 3 | Bảng mới và job kind mới trong CIS | `shared.kpi_daily`, `shared.report_run`, `kpi_snapshot_daily`, `report_generate` (migration CIS, review theo luật PR rủi ro) | Đồng ý cho R1 |
| 4 | Đăng ký ID mới và chuyển template | PLAT-03, PLAT-04, APP-11..APP-15, OPS-12..OPS-17, SEC-08..SEC-10 trùng không gian ID với catalog docs | Đăng ký trong `docs/README.md` cùng PR chuyển template vào `docs/templates/` (thay `cost-report.md`, `postmortem.md`) |
| 5 | Người nhận e-mail tự động | OPS-12, FI-02, CIS-01, CIS-05, BK-01 gửi qua SES | Tech lead nhận OPS-12 + FI-02; business owner chỉ nhận khi muốn (opt-in); BK-01 cho từng nhân viên Booking |
| 6 | Báo cáo tuần Jira PR-20 theo mẫu mới | Kỳ 3 (27/10–02/11) đã nháp, chưa đăng; cửa sổ chi phí cũ chồng kỳ | Dùng template `business-review.md` từ kỳ 3; cửa sổ ISO tuần theo ICT |
| 7 | Postmortem đầu tiên | Sự cố quyền truy cập acc3 (S257) chưa có biên bản | Viết theo `incident-postmortem.md` trong R2 |
| 8 | Dữ liệu mới ở app khác (để sau) | tp-NNN nguồn khách/UTM, bk-NNN `booking.trip_feedback`, endpoint tổng hợp `crm.ops.v1` | Chưa cần quyết bây giờ; làm ở R6/R7 theo mốc |
| 9 | Google Search Console (MKT-02) | Miễn phí, nhưng cần business owner xác minh quyền sở hữu từng site | Hỏi khi có site tenant công khai đầu tiên |
| 10 | Không thêm dịch vụ trả phí | Vercel Speed Insights / Web Analytics, GuardDuty, công cụ khảo sát | Giữ tắt; dùng Lighthouse CI, thu nguồn khách first-party, khảo sát qua SES |
| 11 | Mục tiêu kinh doanh | Tỉ lệ chuyển đổi, NPS, giá gói CRM, sàn lấp đầy chuyến khởi hành | Business owner đặt sau tháng/quý production đầu; Dev chỉ theo dõi xu hướng |
