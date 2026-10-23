# S248 — 23/10/2026: lan truyền xoá tour toàn hệ (AA-986), B2B Booking, quét bí mật, drill xoá thật, chọn writer

**Tác nhân:** Claude Code (Ultracode, nhiều workflow + subagent song song; VSCode, WSL2; agent điều phối tự merge/deploy/verify theo luật giai đoạn dev, push/merge bằng GitHub App `aa-agent`).

Nguồn số liệu: `docs/audits/2026-10-23-S248-wrap/state-snapshot.md` (kiểm live ~14:50 UTC), comment Linear của từng issue, checklist sống `.tmp-session/S248-checklist.md`. Phần chưa kiểm ghi rõ "chưa verify".

## Trạng thái

- **ECS:** CIS api **:799** / worker **:358** cùng `dev-5543d1fc`; Booking **:49** `ab5641d1`; rollout COMPLETED, 1/1.
- **Health:** CIS ready schema **274** (yêu cầu 273); Booking ready **bk-021**. TripPlanner 2 Lambda cùng code, cập nhật 23/10 14:22 UTC.
- **Migration mới nhất:** CIS **274** (áp trong phiên: 269–274), Booking **bk-021** (bk-019/020/021), TripPlanner **tp-018** (drop bảng place cũ), schema `crm` có mặt (crm-001/002).
- **Linear Done trong phiên (15):** AA-981, AA-982, AA-983, AA-984, AA-985, AA-933, AA-972, AA-973, AA-974, AA-932, AA-712, AA-839, AA-906, AA-837, AA-986 (đóng sau E2E cuối phiên); AA-762 → Duplicate.
- **Còn In Progress:** AA-645 (đã chốt writer + bước 0; còn rubric brand-fit v2 rồi wave), AA-829 (restore drill S259), AA-910 (chờ Nghiệp xem trang staff 1440 px), AA-896 (báo cáo tháng 10 từ 01/11), AA-703 / AA-816 / AA-911 (epic danh tính, không đổi).
- **Issue mới (Nghiệp yêu cầu/đồng ý):** AA-981, AA-982, AA-983, AA-984, AA-985, AA-986.

## Quyết định của Nghiệp (trong phiên)

- DFS: hoãn xoay mật khẩu (memory `dfs-rotation-deferred`). Bật secret scanning + gitleaks toàn lịch sử: làm.
- Bỏ các cổng do agent tự đặt (≤1 Booking/phiên, chờ slot, chờ 01/11, "cần làm rõ") — memory `no-agent-made-gates`.
- Trang quyết định 18 thẻ (d01–d18, https://claude.ai/artifact/6MTgUdkyb1eVbEzeVWH7gH): duyệt đủ, kèm ghi chú. d06: tour mới lấy ngày publish thật, tour cũ viết lại giữ `published_at` đầu tiên. d07: lỗi hệ thống không đẩy cho chị Thư — tự sửa hệ thống (memory `improve-system-not-raise`). d15: che account ID/ARN/VPC trong doc sinh tự động (repo gốc public). d16: xoá spike CRM hello.
- **AA-645:** writer **W×Sonnet** cho lần viết lại; brand-fit chỉ báo cáo (không chặn) tới khi có rubric v2; pilot + ≤50 shadow trước, toàn catalog cần duyệt riêng.
- **AA-986 (yêu cầu mới của Nghiệp):** tour bị xoá ở S0/A0 phải ẩn mọi dẫn xuất toàn hệ, tenant giữ bản T2 kèm cảnh báo. ADR 0015 + Q1–Q10 đã duyệt: Q2 không badge khi supersede; Q4 giữ booking đã xác nhận + cờ staff + thông báo staff; Q5 trang tour 410/301; Q8 Master Content staff và admin.
- AA-839: Nghiệp cùng làm drill xoá thật ("ok làm") trên tenant tổng hợp.
- AA-829: Nghiệp bỏ chặn classifier cho bước ghi Secrets Manager; chuyển 7 DSN sang `db.dev.internal`.

## Thay đổi Codebase

**AA-CIS-App:** #939 (tương phản admin/portal), #941 (AA-982), #942 (AA-816 401/403 thay 500), #943 + #947 (AA-983), #944 (mig 269 crm keys), #945 + #948 (S1-first bước 1–2), #946 + #960 + #961 (AA-839 job xoá, trang admin, fingerprint gắn subject), #949, #951 + #953 (AA-984), #952 (mig 270, AA-712), #954 + #958 (gitleaks), #955 + #956 (AA-985 F17), **AA-986:** #959 (L1 luật một nguồn, mig 271), #962 (mig 272 lifecycle record), #964 (L2 service lifecycle duy nhất), #966 (mig 274 tombstone + outbox + notifications), #967 (L3 tenant thấy/bị chặn, trang trip 410/301); **AA-645:** #963 (mig 273), #965 (bước 0). Release 0.6.0 (#940).

**AA-Booking:** #62/#65/#70 (bk-019/020/021), #64 (M2M + báo giá B2B), #67 (departure, giữ chỗ, xác nhận), #68 (AA-910 trang staff 1440 px), #69 + #73 (gitleaks), #71 (luật thương mại B2B: VND, huỷ có phí + dry run, gia hạn 1 lần, giới hạn giữ lại), **#75 (AA-986 L5: từ chối bán tour đã rời catalog, cờ + thông báo staff)**, #76 (inquiry v1.3), #74 (dependabot Next 16.4.1). Release 0.3.0 (#63).

**AA-TripPlanner-Web:** #132 (Next 16, AA-906), #134 (AA-837), #135 (chỉ đọc CIS qua view catalog), #136, #138 + #141 (gitleaks), #139 (tp-018), **#142 (AA-986 L6: chuyến đã lưu báo điểm dừng không còn phục vụ, trang tour retired 410)**. Release 0.5.0 (#133).

**AA-CIS-Infra:** #292–#329 (38 PR): gitleaks + canary (#292/#297), M2M pool (#293/#300/#302), CRM owner/KMS/bucket/budget (#294/#303/#304/#325), probe (#295), budget acc3 (#298), bản sao migration (bk-020/021, 270–274, tp-018), `db.dev.internal` (#308), seed tổng hợp B2B (#310/#311/#315/#316), xoá spike CRM (#312), che ID (#313), copy guard (#317), **probe lan truyền xoá tour (#318) + gate hằng đêm (#328/#329)**, cờ xoá (#320/#321/#322), dọn PII allowlist (#326).

**AA-Partner:** #1 skeleton (API, tenant_tx, crm-002, crm.job), #4 + #6 (gitleaks), #2 (actions bump).

**AA-Ecosys (root):** #184–#215: secret scan root (#185/#190/#201), CRM docs (#186/#198/#199), AA-829 (#187/#210), S1 bước 0/1 (#188), báo cáo chi phí (#191/#194), runbook xoá/DSAR (#192/#208), contract B2B (#195/#205/#212), Dead Table Registry (#196), memo hiệu chuẩn (#203), che ID (#204), **ADR 0015 (#206)**, contract catalog.tour v1.3 (#211), inquiry v1.3 (#213), **DM-4.9 luật tour liveness (#215)**; bot doc #193/#197/#200/#202/#207/#209/#214. PR này: log + backlog + tracker + snapshot + audits + lessons.

## Thay đổi Hạ tầng

- **DB Migrate (check → apply, bảng job rảnh):** CIS 269, 270, 271, 272, 273, 274; Booking bk-019, bk-020, bk-021; TripPlanner tp-018 (snapshot `db-migrate-tp-018-…` giữ tới 2027-04-21).
- **Terraform:** acc3 local (budget/spend guard); acc2 CI + local MFA (KMS/Cognito sửa #300/#302; rule/target group của spike theo thứ tự đúng); `db.dev.internal` (Route 53 private zone, $0,50/tháng); CRM KMS + bucket + budget; cờ xoá bật/tắt cho drill.
- **GitHub:** secret scanning + push protection 6 repo; check bắt buộc `gitleaks` ở 4 repo app; nhãn `secret-scan-baseline-reviewed`.
- **Dữ liệu Dev:** seed B2B tổng hợp; tenant drill `aa839-drill-1` đã xoá thật (chỉ giữ audit log); 120 artifact GitHub cũ xoá.

## Bằng chứng verify

- **AA-986 E2E trên Dev (23/10 14:33–15:0x UTC):**
  - Tour Philippines `0c8bdf9e` retire (`source_deleted`): CIS `/v1/trip` 410; Booking ẩn sản phẩm, báo giá 409 `tour_not_served`, staff nhận 1 thông báo `bk_tour_lifecycle_pull`; TripPlanner backend: danh sách retired có `000e3340`, trang tour Lambda trả 410, browse Philippines ẩn tour (43 tour).
  - Tour `7f58d505` retire: `tenants_notified 1`; tenant atlas-hearth thấy `served_status retired / source_deleted`, chuông `tour.discontinued`, viết lại bị 409 `tour_discontinued` với thông điệp dễ hiểu. Restore: `served`, chuông thêm `tour.reinstated` (`tenants_reinstated` đếm riêng).
  - TripPlanner công khai theo kịp khi cache hết hạn: trang tour **410** từ 14:49 UTC, danh sách browse (CDN `max-age=1800`) không còn tour lúc 15:03 UTC.
  - Restore tour Philippines (15:04 UTC): CIS `/v1/trip` 200; Booking có lại sản phẩm, báo giá 201; TripPlanner Lambda: danh sách retired rỗng, tour 200, browse 44 tour.
  - Chạy lại gate sau restore (run 39975242497): **GREEN**, violations 0, errors 0, pending 0; 892 Master = 892 khoá catalog = 892 đang phục vụ. AA-986 → Done.
- **AA-839:** drill xoá thật: DRY RUN `d4fb89f5` → Apply `382ad9b3` → verify `4c01c2f1` tenant GONE; S3/secrets 0; Sentry 0 event `tenant_id` (90 ngày).
- **AA-837/AA-906:** axe trên prod `/plan`: 0 lỗi tương phản (sáng/tối, 1440/390), console sạch (`docs/audits/2026-10-23-S248-aa837-prod-axe/`).
- **AA-972/973/974:** B2B live 24/24 + 36/36 trên seed tổng hợp.
- **AA-981:** canary khoá giả bị bắt ở PR + lịch sử, rồi pin.

## Còn lại

- AA-645: rubric brand-fit v2 + đo lại 125 trang ($ nhỏ) → wave 3 / ≤50 shadow.
- AA-910: Nghiệp mở trang staff Booking ở 1440 px rồi đóng.
- AA-829: restore drill (S259). AA-896: báo cáo tháng 10 từ 01/11.
- Release PR đang mở: CIS #950 (0.7.0), Booking #66 (0.4.0), TP #137 (0.6.0), AA-Partner #3 (0.2.0) — để phiên sau cắt release.
- Jira S248: Nghiệp duyệt cả 7 nháp, đã đăng: PR-13 (10496), PR-25 (10497), PR-26 (10498), PR-27 (10499), PR-22 (10500), PR-24 (10501), PR-23 (10502).

## Lưu ý kỹ thuật cho phiên sau

- Mọi thay đổi trạng thái phục vụ của tour đi qua `services/tour_lifecycle` (CIS), không UPDATE tay. Tombstone `catalog.v_tour_retired`, outbox `catalog.v_tour_lifecycle_outbox`.
- TripPlanner frontend giữ danh sách tour retired tối đa 30 phút mỗi instance (stale-while-revalidate) — trang tour có thể còn 200 trong lúc đó; backend trả 410 ngay.
- Phản hồi restore có `tenants_reinstated` riêng (không phải `tenants_notified`).
- Kiểm STS luôn kèm `</dev/null` + timeout (lệnh chờ MFA treo phiên).
- Bài học S248: 17 mục mới trong `skill/aa-lessons/lessons.md`.

## Duyệt cuối phiên (trang quyết định, nhóm "Cuối S248")

Nghiệp duyệt và dừng phiên; các việc sau làm đầu S249 (backlog §3 dòng 0a–0g):
- e01 AA-645: rubric brand-fit v2 + đo lại, pilot 3 → shadow ≤ 50 tour (~$4,5).
- e02 AA-783: báo cáo đồng thuận người–panel ($0), đóng issue.
- e03 AA-829: restore drill đầy đủ, có lật `db.dev.internal` (~$0,10) + tập dượt khôi phục 1 schema.
- e04 AA-910: agent tự kiểm 1440 px bằng tài khoản E2E rồi đóng.
- e05: cắt release CIS 0.7.0, Booking 0.4.0, TripPlanner 0.6.0, AA-Partner 0.2.0.
- e06: tạo **AA-987** (CIS lifecycle → purge cache TripPlanner, ≤ 2 phút) và làm trong S249.
- e07: AA-934, AA-935, AA-975 để S249.
