> Superseded on 2026-10-19 (S243) by docs/engineering-handbook.md — kept for history.

# S241: Lộ trình nền tảng hợp nhất (SDLC/ADLC review × data standards v1.0)

- **Ngày:** 17/10/2026 (S241). **Tác nhân:** Claude Code.
- **Trạng thái:** **ĐỀ XUẤT, chờ Nghiệp duyệt.** File này không thay đổi ADR, data standards, backlog hay Linear. Nó chỉ gom và xếp thứ tự.
- **Bản sửa 1 (17/10, kiểm nhất quán đối kháng):** sửa trạng thái issue (AA-824 Done S237, AA-830/X3 Done S238, AA-730 Done S227); thêm U-60 (DM-6.6 TripPlanner, AA-861) và U-61 (phần còn lại N3); đổi số rule trùng (TST-7 → TST-8, C2.3h → C2.3i); ghi mặc định cho mọi quyết định §3; thêm tiền đề L9 ← X1 và chi phí eval gate U-29 mà review bỏ sót.
- **Nguồn đã đối chiếu:**
  - SDLC/ADLC review: [`README.md`](README.md) (bản sửa 2) và [`areas/`](areas/);
  - data standards v1.0 (đã duyệt S237): [`README`](../../architecture/data-standards/README.md), [Part A](../../architecture/data-standards/01-engineering.md), [Part B](../../architecture/data-standards/02-data-management.md) (§12 enforcement), [Part C](../../architecture/data-standards/03-scaling.md) (C7 môi trường và prod blueprint). Bản working copy S241 đã chuyển các dòng AA-751/X6 sang Exists;
  - ADR [0001–0008](../../adr/README.md) (kèm 0003a, 0004a; 0009 đang giữ chỗ);
  - [backlog sống](../../backlog/README.md), [`ecosystem-architecture.md`](../../ecosystem-architecture.md);
  - review data architecture gốc [S237](../2026-10-14-S237-lane-backlog/data-architecture/README.md) (roadmap N/X/L).

---

## 1. Mục đích, quy tắc ưu tiên, cách dùng

### 1.1 Mục đích

Hai lộ trình đang chạy song song, chồng nhau và có chỗ ngược nhau:
- roadmap N/X/L của data standards (đã duyệt S237);
- P0-A/P0-B/P1/P2 của SDLC review (S241, chưa duyệt).

File này gộp cả hai thành **một** danh sách việc nền tảng duy nhất, mã **U-xx**, chia 4 tầng. Mỗi mục giữ id gốc (P0-x, Nx/Xx/Lx, rule id) để truy vết.

### 1.2 Quy tắc ưu tiên (bắt buộc)

1. **ADR đã accepted** thắng tất cả.
2. **Data standards v1.0** (Part A/B/C) thắng skill, steering và ghi chú phiên.
3. **Quyết định đã ghi của Nghiệp** cũng ràng buộc. Ví dụ:
   - S240: token GitHub và mật khẩu RDS master xoay khi lên prod;
   - prod nằm trên acc2 (ADR 0001 S235);
   - Vercel Hobby;
   - trunk-based (ADR-2026-023);
   - kỷ luật chi phí (DM-10.7);
   - "Dev không có người dùng thật" (memory dev-no-waiting, S239).
4. **SDLC review là đề xuất mới, chưa duyệt.** Chỗ nào review ngược với ADR, chuẩn hay quyết định đã ghi, file này **không** tự chọn theo review. Mâu thuẫn được đưa lên thành quyết định cho Nghiệp (§3). Cho tới khi Nghiệp quyết, lộ trình xếp theo phương án **giữ nguyên quyết định đã có**.

### 1.3 Cách dùng

- Sau khi Nghiệp duyệt, đây là **nguồn duy nhất cho thứ tự việc nền tảng**: bảo mật, CI/CD, môi trường, dữ liệu, vận hành.
- Backlog sống (`docs/backlog/README.md`) vẫn là hàng việc của phiên. Dòng nào thuộc lộ trình này thì ghi mã U-xx và trỏ về đây, không chép lại nội dung. Phần sửa backlog làm ở root PR cuối phiên, file này không sửa.
- Việc sản phẩm (T-series, portal, Booking wave, place pipeline) không nằm ở đây. Chúng vẫn xếp trong backlog sống.
- Khi một quyết định ở §3 được chốt, sửa mục U tương ứng, ADR/chuẩn (theo §5) và backlog trong cùng một PR.

### 1.4 Cảnh báo trạng thái cũ (đọc trước khi coi việc gì là "còn thiếu")

README và Part B §12 của data standards vẫn ghi "to build" cho nhiều mục đã xong:
- **Đã đóng Done:** AA-807, AA-817, AA-825, AA-827, AA-828 (S239, log S239 mục Linear); AA-824 (S237); AA-830 (S238).
- **Code Infra cho thấy đã có:**
  - N5 (`run_migration.py`: timeout, no-transaction, snapshot trước migration phá huỷ, lint);
  - N3 (`skip_final_snapshot=false`, `copy_tags`, Performance Insights, parameter group riêng có `rds.force_ssl` và `idle_in_transaction`);
  - N1 (`db-schema-dump.yml` chạy hằng đêm; `schema_dump.py` có orphan rate, session theo `application_name`, thống kê bảng/index).
- **Cũng đã xong:** N2 + N7 (mig 229, AA-817), X3 (AA-830, S238: bk-011, `inquiry.submitted` v1.2, backfill, 0 orphan), X8 (AA-827), X9 (AA-828), N4 (AA-825, mig 233), X6 (AA-751, S240–S241).

Hệ quả: một số phần "to build" từng gộp vào AA-807 hoặc AA-824 (đã Done) **vẫn chưa làm**:
- N6 (file `docs/architecture/dead-table-registry.md` không tồn tại);
- `owners.yaml` (không tồn tại);
- X5 `shared.countries`;
- TST-1 (TripPlanner chưa có CI replay migration trên `postgres:15`; `AA-TripPlanner-Web/.github/workflows` chỉ có `ci.yml`, `deploy-lambdas.yml`);
- phần còn lại của N3: C2.3h (`idle_session_timeout` cho role `tripplanner`, không thấy trong code) và script CI tính tổng connection budget của C2.3c (không tồn tại; AA-824 chỉ làm nửa Terraform).

Các phần này cần issue mới hoặc mở lại, xem §6 và §7. Backlog sống §4 vẫn ghi AA-807 là "later" dù S239 đã Done: sửa ở root PR cuối phiên.

---

## 2. Bảng đối chiếu: mục SDLC → data standards → Linear

Quan hệ: **trùng** (cùng việc), **chồng** (phủ một phần), **mở rộng** (review thêm phần chuẩn chưa có), **mâu thuẫn** (ngược ADR, chuẩn hoặc quyết định đã ghi, xem §3), **mới** (chuẩn không đề cập).

| Mục SDLC | Rule / roadmap data std | Linear | Quan hệ | → U | Ghi chú |
|---|---|---|---|---|---|
| §1 "acc2 Dev = production vì giữ PII thật" | C7.1a, DM-6.10, DM-6.8; L9 | AA-821 | **mâu thuẫn** | U-10 | D-01. Dump live 16/10: `booking.customers` khoảng 1 dòng (ước lượng `reltuples`, không phải đếm chính xác), `shared.tenants` 4, không có schema `crm`. Phần "CRM" trong review sai. Còn mở: dump laptop 16/09, các dòng customer/tenant, và inquiry từ site TripPlanner public trên domain thật (S239) có phải người/doanh nghiệp thật không. |
| P0-1 Nhánh bất kỳ assume được role deploy/tf-apply | C7.2d, DM-11.5; X1, L9 | — | mới | U-01, U-02 | Chuẩn không có rule về trust OIDC. Bước 4 (xoay `ADMIN_SECRET`) trùng việc §1/#4 trong backlog, làm một lần. Required reviewer không dùng được trên repo private Free/Team nên C7.2d phải sửa (D-16). |
| P0-2 Revoke token GitHub đã lộ | DM-8.9 | — | **mâu thuẫn** | U-03 | D-02. Mở lại quyết định S240 (backlog §1). `docs/incidents/` là vị trí mới. |
| P0-3 Agent chạy bằng role admin | DM-8.7, DM-8.8, DM-11.5; X1 | AA-730 (Done S227), AA-517 (tham chiếu) | **mâu thuẫn** | U-04 (b1–b5), U-53 (b6) | D-15. DM-8.7 (MUST) ghi cứng `--profile aa365-admin`. Phải sửa chuẩn v1.1, steering và skill trong cùng một PR. |
| P0-4 Bật tính năng bảo mật GitHub miễn phí, 2FA | DM-6.10 | — | mới | U-05 | Infra đã có `secret-scan.yml`, cần kiểm lại câu "private không quét secret". AA-ACP-App đang archived và public, không phải đã xoá như CLAUDE.md ghi. |
| P0-5 Kiểm role backend cho llm-config/budgets/job-runner | NAM-14 | AA-816, AA-703 | mới | U-06 | Vá tạm trên đường tới ADR 0006 Phase 1. llm-config thuộc contract gateway (ADR 0009, CON-8). |
| P0-6 Sentry, alarm 5xx API GW, uptime | C4.1, C4.1a, C1.2 | AA-832 | mở rộng | U-07 | Alarm cấp app, nằm ngoài baseline RDS/job. Uptime SaaS ngoài Terraform cần chấp nhận rõ. Sentry: `send_default_pii=False` (DM-6.4). |
| P0-7 pip-audit chặn, concurrency, guard fail-closed | C6.3a, DM-11.4; X6 | — | mở rộng | U-08 | Guard CIS fail-open khi thiếu secret, trái MUST của C6.3a. Đưa về ngang guard Booking (X6). |
| P0-8 Cô lập tenant fail-open, Redis không AUTH | DM-8.4, C2.3g, SEC-10, TST-4, TST-5; X2 | AA-859, AA-817, AA-544 | **mâu thuẫn** | U-12, U-13, U-14, U-15 | D-12. Chuẩn đã chấp nhận fallback này cho route còn canary và rollback bằng `DEL` Redis. Review sai ở chỗ `aa_cis_admin` "BYPASSRLS" (§3.2). |
| P0-9 Runtime CIS đọc PII Booking, SG chung, master đã lộ | DM-1.3, DM-8.9, DM-6.8, SEC-1, SEC-12, C2.3b, DM-8.6, TST-4, C7.2c; X1 | AA-860, AA-817 | **mâu thuẫn** | U-16, U-17, U-18, U-33, U-41 | D-03, D-04, D-05, D-06. Ngược S240, ngược ADR 0004 d5 và kéo X1 lên sớm. |
| P0-10 Biên API: rate-limit login, WAF stage, throttle, docs, CORS, header | C2.3a, C2.3g, C2.3e, DM-10.7; N3 | AA-806, AA-577 | mới | U-19, U-59 | Throttle stage bổ sung cho các chặn phía DB. WAF stage là chi phí mới (D-19). C2.3e là phần tương ứng phía Lambda, review không nhắc. |
| P0-11 Khôi phục/rollback: drill PITR, dump, ECR immutable, runbook | DM-9.3, DM-6.10, DM-9.2, DM-9.4, DM-9.5, C7.1; X10 | AA-829 | mở rộng | U-20, U-21 | D-10 (thời điểm). Review bỏ sót DM-9.5 (CNAME) và DM-9.4 (restore một schema). Hạn snapshot thủ công cần một dòng DM-7 (D-09). |
| P0-12 Truy cập dữ liệu không log, management account bên thứ ba | DM-8.8, MIG-5, DM-2.4, C7.2e, C4.2a, C4.2c, DM-7.1; X1, L9 | AA-864 | **mâu thuẫn** | U-22, U-10, U-51 | D-08 (pgaudit hoãn tới prod theo S237/C7.2e). Log phiên ECS Exec là bổ sung, tương thích. |
| P0-13 Hồ sơ pháp lý, /privacy /terms, Vercel Pro | DM-6.7, DM-6.8, DM-6.5, DM-6.2; L3, L10 | AA-820, AA-839, AA-821 | **mâu thuẫn** | U-23, U-24 | D-18 (Vercel Pro ngược quyết định Hobby). Phần còn lại mở rộng DM-6. Gửi chị Thư dưới dạng đề xuất nhẹ nhàng. |
| P1-1 Cổng merge: App "aa-agent", ADR 0010/0011, ruleset, auto-merge | DM-11.5, DM-6.10, DM-11.1, DM-10.7 | — | **mâu thuẫn** | U-25 | D-13, D-14. Auto-merge của agent ngược DM-11.5 MUST. Steering hiện tại cũng đang ngược DM-11.5. |
| P1-2 Vệ sinh secret: register, mồ côi, PAT → App, E2E chỉ đọc | DM-8.6, DM-8.10, SEC-2 | — | mở rộng | U-26 | Chu kỳ 90 ngày (§5.4) là mâu thuẫn riêng (D-03). Biến có gạch dưới thì Nghiệp sửa tay. |
| P1-3 RBAC staff phía server, verify JWT, tách key | NAM-14 | AA-816, AA-703 | chồng | U-27 | Bước tạm trên đường tới ADR 0006 d8/Phase 1. TTL staff 8h là tạm, đích là 15 phút + 12h refresh. |
| P1-4 Cổng CI: tsc/next build, Trivy, Lambda TP sau CI, header | TST-1 | — | mới | U-28 | Thêm TST-1 (replay migration TP trên `postgres:15`), lỗ hổng duy nhất mà chuẩn đã liệt kê. |
| P1-5 Eval gate có trần chi phí cho T2/T9 | DM-10.4, DM-10.6, DM-10.7, DM-4.6, CON-8, DM-6.4 | AA-729, AA-783 (nhãn T9, liên quan), AA-804 | chồng | U-29, U-34 | D-23 (AA-729 viết lại hay huỷ). Gắn eval id vào PATCH llm-config phụ thuộc ADR 0009. Job LLM chạy theo PR là chi tiêu định kỳ mới (DM-10.7, D-19). |
| P1-6 Log JSON + request id, Sentry Booking/TP, OKActions | C1.1d, DM-6.4, C4.2c, C4.1a; N3 | — | **mâu thuẫn** | U-30 | D-20 (OKActions ngược S240 "chỉ email khi ALARM"). Log chỉ chứa id, không PII. |
| P1-7 GuardDuty, Access Analyzer, CloudTrail, giữ log 365 ngày, audit event | DM-2.4, DM-7.1, DM-7.5, C4.2b, DM-10.7 | — | mở rộng | U-31 | D-09, D-19. Audit mở rộng `acp_shared.audit_log`, không tạo bảng audit chung (DM-2.4). |
| P1-8 Xoá dữ liệu (DM-6.7), DSAR export, hạn snapshot | DM-6.7, DM-6.2, DM-9.2, DM-7.5; L3 | AA-839 | mở rộng | U-32 (hạn snapshot: U-21) | D-11 (kéo L3/AA-839 lên). DSAR export là rule mới. |
| P2-1 ADR 0012 mô hình môi trường, layout Terraform | C7.2a, C7.2c, C7.2d, DM-9.6; L9 | AA-864 | **mâu thuẫn** | U-40 | D-16, D-17. Ba layout không tương thích: `envs/prod`, `accounts/<name>`, `stacks/platform`. |
| P2-2 Luồng Terraform: plan comment, apply theo hash, drift | C7.2c, C4.1a | — | mới | U-42 | Bắt drift kiểu AA-832 (#155). |
| P2-3 Build once theo digest, provenance, SBOM, pin SHA | — | — | mới | U-43 | Attestation phụ thuộc lựa chọn ADR 0011. |
| P2-4 OpenAPI /v1, problem+json, access log API GW | CON-3, CON-4, CON-5, DM-3.6; X7 | — | mở rộng | U-44 | ADR 0013 phải dẫn CON-3–5. |
| P2-5 Public API key (`shared.tenant_api_keys`) | DM-1.5, DM-6.9, NAM-13, DM-7.1, MIG-4 | AA-813 | mở rộng | U-45, U-11 | Key lưu hash, cần dòng retention, đi theo D8. |
| P2-6 Idempotency-Key cho POST tốn tiền | CON-7, DM-2.4 | AA-682 | mở rộng | U-46 | Kích hoạt khi bật thanh toán. |
| P2-7 release-please, CHANGELOG, DORA | — | — | mới | U-47 | |
| P2-8 Org `.github`, template PR | DM-11.1 | — | mới | U-48 | Template PR là chỗ đặt checklist SQL §8 Part A. |
| P2-9 SLO người dùng, burn-rate, k6 | C1.2, C1.2a, C4.1, C8b; L9 | — (kết quả đưa vào AA-838) | mở rộng | U-49 | Đưa kết quả vào review dung lượng C8 (U-38). |
| P2-10 Bot copy migration, preflight `required_schema_version` | MIG-4, DM-11.2, DM-1.2; X7, X1 | AA-826 | mở rộng | U-50 | Giữ merge tay và Copy Guard. |
| P2-11 ECS exec thành break-glass, workflow run-script | DM-8.8, MIG-5, DM-8.9, C2.2; X1 | — | **mâu thuẫn** | U-51 | D-07. DM-8.8 và CLAUDE.md toàn cục coi ECS exec là đường chuẩn. A/B LLM phải chạy qua ECS exec (§4.3 ecosystem-architecture). |
| P2-12 Pentest bên thứ ba | — | — | mới | U-52 | Quyết định chi tiêu của Nghiệp và chị Thư. |
| P2-13 Không key tĩnh trên máy dev, agent chạy trong devcontainer | DM-8.7 | AA-517 | mới | U-53 | Đọc lại hồ sơ AA-517 trước khi tắt `acc1-legacy-default`. |
| P2-14 DR prod, mạng prod, Security Hub/Config | DM-9.6, C7.2a, C7.2b, C7.2e, C7.2f, C3; L9, L7 | — | mở rộng | U-40 | Review thiếu C7.2e, C7.2f và trigger RDS Proxy (L7). |
| P2-15 `rollback.yml`, Lambda alias `live` | — | AA-703 | chồng | U-54 | ADR 0006 d5 (trigger Cognito). Áp alias cho Lambda TP là phần mới. |
| P2-16 Provenance code AI, OTel, AA-842 B, SLSA L3 | — | AA-842 | **mâu thuẫn** | U-55 | D-21. S238: chỉ làm AA-842 B khi job chậm hoặc không giải thích được. |
| P2-17 Dọn nhánh, squash-only, tự sinh backlog | — | — | mới | U-11 | D-22 (tự sinh backlog đổi ritual steering). |
| §5.1 Ma trận visibility × gói GitHub (A/B/C) → ADR 0011 | DM-6.10, DM-6.1 | — | mở rộng | U-25, U-10 | D-14. Root public có giá/audit, có thể đang vi phạm DM-6.10 (D-25). |
| §5.2 Môi trường và promote (dev → tag → prod trên acc2) → ADR 0012 | C7.2a, C7.2c, C7.2d, C7.2e, DM-8.9; L9, X1 | — | chồng | U-40 | Khớp ADR 0001. C7.2d cần sửa nếu Infra private (D-16). |
| §5.3 CI/CD chuẩn: Dependabot gom PR hằng tuần **tự merge patch/minor**, audit chặn build, export bằng chứng hằng tháng, CodeQL/gitleaks | DM-11.5, DM-6.10 | — | **mâu thuẫn** (phần tự merge) | U-05, U-08, U-28, U-25 | Bot tự merge ngược DM-11.5 như agent tự merge: thuộc D-13. Phần còn lại là mở rộng (`dependabot.yml` mọi repo ở U-05, audit chặn ở U-08/U-28). |
| §5.4 Đích quản lý secret: xoay 90 ngày, xoay ngay khi nghi lộ | DM-8.6, DM-8.9, SEC-2 | — | **mâu thuẫn** | U-26 | D-03. |
| §5.5 Đích quản lý API | DM-8.4, SEC-10, CON-3, CON-4 | AA-703 | chồng | U-12, U-27, U-44 | Đích fail-closed khớp chuẩn. Chỉ thời điểm và cơ chế khác (D-12). |
| §5.6 Quan sát và SLO: alarm đẩy về điện thoại **kèm OK**, audit trail 365 ngày | C4.1, C4.1a, DM-7.1, DM-7.5 | — | **mâu thuẫn** (phần OK, giữ log) | U-07, U-30, U-31, U-49 | D-20 (OK), D-09 (365 ngày). |
| §5.7 Phát hành và hỗ trợ: quy trình sự cố, SLA, `support@`, **status page miễn phí**; release-please khi có prod | — | — | mở rộng | U-21, U-23, U-47 | Status page (area Q3) chỉ có ở §5.7, đưa vào U-23. |
| §5.8 Ma trận ADLC | DM-11.5, DM-8.7, DM-8.8, DM-11.4 | — | **mâu thuẫn** | U-25, U-04 | D-13, D-15. Giữ "DB Migrate apply" và `override_busy_jobs` chỉ cho người là đúng DM-11.4/C6.3b. |
| §6 Chi phí +35–55 USD/tháng; prod 150–300 | DM-10.7, DM-10.1, C3c; X9, L9 | AA-828 | mở rộng | §4.5 | Mỗi dịch vụ trả phí cần Nghiệp duyệt sau khi tính bằng AWS pricing calculator. Gắn tag `App` từ PR đầu tiên. |
| §7 Những gì KHÔNG làm | C3, C3b, C7.2a, C2.3b, DM-8.9, DM-10.6; L9, X1 | — | **trùng** | §4.6 | Khớp ADR 0001 S235, ADR 0008 d10/C3, thứ tự C2.3b/DM-8.9 và DM-10.6. Giữ nguyên làm guardrail. |

Mục chỉ có trong `areas/` mà README review không đưa vào (README thắng khi lệch, §8.2 review), nên **không** có mục U: A14 (giới hạn kích thước body, `extra='forbid'`), E13 (S3 gateway endpoint miễn phí cho Dev; phần prod của E13 nằm trong U-40). Nghiệp muốn thì thêm vào U-19 / U-40.

---

## 3. Mâu thuẫn cần Nghiệp quyết

Mỗi dòng có **phương án A/B**. Phương án **mặc định** (lộ trình đang xếp theo nó cho tới khi Nghiệp quyết) là phương án giữ quyết định hoặc chuẩn đã duyệt, trừ khi ghi rõ khác.

### 3.1 Quyết định

| # | Chủ đề | Review nói | Chuẩn / quyết định đã ghi nói | Đề xuất xử lý | Phương án |
|---|---|---|---|---|---|
| D-01 | Khung "acc2 Dev = production vì có PII thật" | §1: Dev giữ PII thật (`booking.customers`, CRM, tenant thật). Khung này đẩy P0-9 bước 1, P1-7, P1-8 lên trước và mở lại S240. | C7.1a: PII prod không được lên Dev, seed phải tổng hợp hoặc che. Dev objectives "không phải cam kết paging" (C1). S239: "đang dev, làm gì có người dùng". S237 hoãn pgaudit vì "4 tenant, 1–2 booking row". | Không nhận tiền đề này một cách im lặng. Dump 16/10: `booking.customers` khoảng 1 dòng, `tripplanner.customers` khoảng 0, `shared.tenants` 4, không có schema `crm`. Các số này là ước lượng `reltuples`, không phải đếm; S239 thấy 8 trip case trên Booking, và TripPlanner đã chạy public trên domain thật từ S239 (thu tên, email, điện thoại, chưa có trang privacy), nên PII thật **có thể** đã vào qua form inquiry. Nghiệp xác nhận bằng một lệnh đếm chính xác chỉ đọc (U-10): mấy dòng đó, inquiry kể từ ngày lên domain, và dump laptop 16/09 có phải người/doanh nghiệp thật không. | **A (mặc định):** là dữ liệu test. Sửa §1 của review thành "Dev giữ dữ liệu test; đây là danh sách sẵn sàng trước prod/tenant đầu", xếp tầng theo tenant đầu hoặc prod. **B:** là dữ liệu thật, tức C7.1a đang bị vi phạm. Chọn tiếp: B1 xoá/che dữ liệu thật trên Dev; hoặc B2 tuyên bố Dev là prod trên thực tế, kéo theo đảo dev-no-waiting, S240 và C1/C4.1a. |
| D-02 | Revoke token GitHub ngay | P0-2: token có scope `repo, workflow`, dùng được từ mọi nơi trên Internet. Revoke ngay, XS. | S240 / backlog §1: token + mật khẩu RDS "để nguyên, xoay khi lên prod". | **Khuyến nghị A.** Chi phí 0, XS, lý do không phụ thuộc D-01. Tách khỏi phần RDS. | **A (khuyến nghị):** revoke ngay, backlog §1 chỉ còn mật khẩu RDS chờ prod. **B (mặc định, giữ S240 cho tới khi Nghiệp quyết):** U-03 chưa chạy. |
| D-03 | Xoay mật khẩu RDS master bây giờ và chính sách xoay (90 ngày, xoay ngay khi nghi lộ) | P0-9 b1: xoay tay trước tenant đầu. §5.4: xoay 90 ngày, xoay ngay khi nghi lộ. | S240: xoay khi lên prod. DM-8.9: "rotates after use (prod)". Chuẩn chưa có chính sách xoay định kỳ. | Về kỹ thuật thì an toàn: Terraform `ignore_changes = [password]`. Đây vẫn là đảo quyết định. Nên đi theo D-01: nếu D-01=B thì chọn B. | **A (mặc định):** giữ S240, chuyển bước này vào checklist prod (U-40). **B:** xoay tay ở tầng 2 (U-17), sửa DM-8.9 (xoay khi lộ, không chỉ ở prod) và thêm rule xoay (DM-8.11, §5). |
| D-04 | Bật `manage_master_user_password` | P0-9 b5: bật sau X1 và SG riêng, ở P0-B. | Trước X1, master còn là người chạy DB Migrate và là role duy nhất có CREATEROLE (C2.2, C2.3a/b). DM-8.2 cần `db_migrator` riêng trước. DM-8.6 và CLAUDE.md toàn cục ghi `aa-cis/dev/rds` là DSN thuần, còn secret do RDS quản lý là JSON và tự xoay 7 ngày. Schema dump và aa817 probe cũng nối bằng master. | Đặt sau **toàn bộ** X1 (gồm `db_migrator`), sau consumer schema-dump/probe và sau quy trình break-glass đọc JSON. CLAUDE.md toàn cục và skill aa-cis-schema phải sửa, chỉ Nghiệp sửa được CLAUDE.md. | **A (khuyến nghị, mặc định):** trigger "X1 xong" hoặc L9 (U-41). **B:** giữ ở P0-B như review, kéo theo D-05=B. |
| D-05 | Thời điểm tách role X1 | P0-9 b2: "AA-817 X1" ở P0-B, cỡ M. | ADR 0008 d6 (accepted) và E2: `bk_owner`/`tp_owner` + `db_migrator` trước, rồi CIS chuyển `cis_app` sau AA-817 D2. Backlog #17: AA-860 "sau AA-807/AA-826", cỡ L. | Giữ đúng thứ tự trong ADR. Sửa id trong review: phần CIS là AA-860, không phải AA-817. | **A (mặc định):** X1 ở tầng 90 ngày (U-33), theo đúng thứ tự ADR. **B:** kéo cả chuỗi X1 (owner roles + `db_migrator` → D2 policies → AA-860) lên tầng 2, ước lại là L. |
| D-06 | Security group riêng cho từng app | P0-9 b3: mỗi app một SG trước tenant đầu, SG RDS/Redis liệt kê ingress theo app. | ADR 0004 d5: Booking dùng "existing private subnets and app security group"; plan Booking không được đổi tài nguyên CIS. ADR không ghi rõ chấp nhận rủi ro SG chung; câu "revisit for staging/prod isolation" chỉ nói về ALB/cluster riêng (mục Alternatives). C7.2c chỉ đòi SG riêng theo môi trường (prod). | Rẻ, nhưng sửa ranh giới của một ADR đã accepted, nên cần ADR 0004b. | **A:** viết ADR 0004b, làm trên Dev ở tầng 2 (U-18). **B (mặc định):** chỉ làm ở prod (C7.2c, U-40). |
| D-07 | ECS exec: đường chuẩn hay break-glass | P0-12/P2-11: script ECS exec chạy bằng master và bỏ qua PR/CI. Chuyển thành break-glass, thay bằng workflow run-script. | DM-8.8: người truy cập DB **chỉ** qua S3-mediated ECS exec. MIG-5 cho phép DML một lần qua đường này. ADR 0004 d5 bắt buộc `enable_execute_command`. CLAUDE.md toàn cục gọi đây là "canonical". A/B LLM bắt buộc chạy qua ECS exec. | Nhận phần bổ sung: log phiên exec (U-22) và read-only ops role (X1+, U-33). Biến exec thành break-glass là đề xuất cần sửa DM-8.8, MIG-5, ADR 0004 d5, CLAUDE.md, và phải có đường thay thế cho A/B. | **A (mặc định):** giữ DM-8.8, thêm log và read-only role. **B:** khi có prod, sửa DM-8.8/MIG-5 và chuyển exec thành break-glass (U-51). |
| D-08 | pgaudit trên Dev ngay | P0-12 b2: load pgaudit (`ddl,write`), bật `log_connections`, reboot ngắn. | C7.2e: pgaudit là SHOULD **ở prod**. S237 §7 chuyển pgaudit sang Later (Nghiệp đã duyệt). C4.2c: log không được chứa PII. C6.3b/C5.5a: reboot cần mọi job table idle và maintenance window. Log postgresql giữ 14 ngày. | pgaudit `write` sẽ ghi literal PII từ script ad-hoc. `log_connections` thì không có rủi ro đó, làm được qua parameter group (C4.2a). | **A (mặc định):** chỉ `log_connections` (U-22), pgaudit vào prod (U-40). **B:** bật pgaudit trên Dev với scope không ghi được literal PII, có idle check C6.3b, window, và một dòng DM-7. |
| D-09 | Cửa sổ retention mới | P1-7: log bảo mật ≥ 365 ngày, log app 30–90 ngày. P0-11/P1-8: snapshot thủ công có hạn. | DM-7.1 là registry duy nhất. DM-7.5: mọi thay đổi cửa sổ phải được Nghiệp duyệt và sửa bảng. Log postgresql 14 ngày (C4.2b). Chưa có dòng nào cho snapshot thủ công. DM-9.2 bắt buộc snapshot trước migration phá huỷ. | Chuyển thành các dòng sửa DM-7 (§5, B-7): CloudTrail/log bảo mật, log app, log phiên ECS exec, snapshot thủ công (miễn trừ snapshot DM-9.2 còn trong cửa sổ). | **A:** duyệt các dòng như đề xuất ở §5. **B:** giữ nguyên DM-7, chỉ thêm dòng snapshot thủ công. **Mặc định (cho tới khi quyết):** không đổi dòng DM-7 nào; log mới dùng cửa sổ 14 ngày như log hiện có; hạn snapshot ở U-21 chờ. |
| D-10 | Thời điểm diễn tập restore (X10/AA-829) | P0-11: trước tenant trả tiền đầu tiên, không đặt mục tiêu RTO. | DM-9.3/C7.1: "run it once **now**". C1.2: Dev RTO < 1 h. Backlog: AA-829 "later". Ba nguồn cho ba thời điểm khác nhau. | Chuẩn nói "now", chi phí < 1 USD. Ghi kết quả so với mục tiêu C1.2 (< 1 h). Bỏ chữ "cross-account" ở area E10 vì ngược ADR 0001. | **A (khuyến nghị, mặc định vì chuẩn thắng backlog):** làm ngay khi có slot, giữ U-20 ở đầu tầng 2. **B:** trước tenant đầu, như review. **C:** giữ "later" của backlog, khi đó phải sửa DM-9.3. |
| D-11 | Quyền chủ thể dữ liệu trong 90 ngày | P1-8: script xoá DM-6.7 chạy DRY RUN, endpoint DSAR export. | DM-6.7: "to build (L3); Runbook until then", gắn ADR 0006 Phase 4. AA-839 parked "before prod", chưa được duyệt tạo. Chuẩn không có rule access/export. | Runbook (P0-13) khớp "Runbook until then". Script và DSAR export là kéo L3 lên sớm. DSAR cần rule mới (DM-6.11). | **A:** bỏ park AA-839, thêm DM-6.11, làm U-32 ở tầng 90 ngày. **B (mặc định):** chỉ runbook trước tenant đầu (trong U-23), script theo ADR 0006 Phase 4 (U-57). |
| D-12 | Đảo mặc định tenant pool | P0-8: thiếu cờ nghĩa là dùng tenant pool, áp toàn cục. Rollback qua SSM hoặc deploy, không qua Redis. | C2.3g: fallback "chỉ còn khi route là canary". Route đã promote thì phải 503. DM-8.4: đóng từng route trong AA-817. Backlog §6: rollback = `DEL` key. AA-859 wave 3–4 còn chờ. | Cả 11 cờ đã ON, nên đảo toàn cục thực chất là promote mọi canary cùng lúc và bỏ rollback đã duyệt. Pool tenant 2/task, `aa_app_user` giới hạn 15: nới thì phải sửa C2.2 (C2.3c). | **A (khuyến nghị, mặc định, khớp C2.3g/DM-8.4):** quyết theo từng wave AA-859, mỗi wave promote thì bỏ fallback cho route đó, sửa C2.3g và runbook khi bỏ rollback qua Redis (U-12). **B:** đảo toàn cục và chuyển cờ sang SSM, sửa C2.3g, §9 Part A, DM-8.4 trước. |
| D-13 | Quyền merge: agent tự merge PR rủi ro thấp | P1-1/§5.8: App "aa-agent" mở PR, PR rủi ro thấp tự merge khi xanh, chỉ đường dẫn nhạy cảm cần Nghiệp. | DM-11.5 (MUST): "Agents MUST NOT merge to main", ghi enforced bởi branch protection và hook. `.claude/CLAUDE.md`: "DO NOT merge". Steering lại bảo agent `gh pr merge --auto` và merge tay root PR, tức đã ngược DM-11.5. | Quyết trong ADR 0010 "Change authority". Dù chọn gì, sửa ngay dòng "Enforced by" sai của DM-11.5 (0/951 PR có review, `required_pull_request_reviews=null`), việc này nằm trong U-09. | **A:** sửa DM-11.5 thành mô hình theo tầng rủi ro (gồm cả Dependabot tự merge patch/minor ở review §5.3), sửa steering và CLAUDE.md cho khớp. **B (mặc định, theo DM-11.5 MUST):** giữ chỉ người merge, sửa steering cho đúng DM-11.5 (bỏ `--auto` và việc agent tự merge root PR); không bật Dependabot auto-merge. Việc sửa steering cũng chờ Nghiệp xác nhận. |
| D-14 | Visibility repo và gói GitHub (ADR 0011) | §5.1: phương án A (Team ~8 USD, root + Infra private, app public) là khuyến nghị. B: Enterprise ~42 USD. C: Team, tất cả private. | E10 S237 (đã duyệt, quyết định 10 của review S237): "the 3 app repos stay public". Root public theo S235 (không thuộc E10). DM-6.10 viết cho repo public. Review gọi đây là đảo S235 nhưng không nhắc E10. | Phương án A giữ 3 repo app public nên **không** đảo E10, chỉ đảo lựa chọn S235 cho root. B và C đảo E10 một cách tường minh. Quyết định kinh doanh và IP của Nghiệp và chị Thư. Private hoá root thì sửa lời DM-6.10. | **A:** phương án A của review. **B:** Enterprise. **C:** Team, tất cả private. **D (mặc định):** giữ hiện trạng (app + root public theo E10/S235, Infra private, gói Free), dùng gitleaks và chuyển dữ liệu nhạy cảm khỏi root (xem D-25). Chi phí 0. |
| D-15 | Profile AWS cho agent (`aa365-agent`) | P0-3: agent dùng `--profile aa365-agent`, sửa 8 file gồm `~/.claude/CLAUDE.md`. | DM-8.7 (MUST) ghi cứng `--profile aa365-admin`. CLAUDE.md toàn cục dùng aa365-admin cho ECS exec. Thiết kế AA-730 (`agent_session.tf`) thì nói agent phải dùng aa365-agent. | Sửa DM-8.7 thành trung lập về profile qua PR chuẩn v1.1. Nghiệp tự sửa CLAUDE.md toàn cục. Trước khi chuyển, kiểm aa365-agent làm được S3 upload, presign và ECS exec (DM-8.8). | **A (khuyến nghị):** sửa DM-8.7, chuyển agent sang aa365-agent sau khi kiểm (U-04 bước 4). **B (mặc định, theo DM-8.7 MUST cho tới khi chuẩn được sửa):** giữ aa365-admin, chỉ thêm ask/deny. |
| D-16 | Layout Terraform prod và cổng duyệt prod (ADR 0012) | P2-1: đổi tên env Infra `prod` thành `dev-apply`, tham số hoá `stacks/platform`. §5.1: repo private trên Free/Team không có env reviewer. | C7.2c (MUST): `envs/prod/`. CONTEXT.md của Infra (AA-841, S238): không tạo lại per-env root, môi trường mới thì dùng `accounts/<name>/`. C7.2d: prod apply cần approval của env `prod` trên GitHub. | Ba layout không tương thích. Chốt trong ADR 0012 và sửa C7.2c cùng PR (C7.2c đã cũ sau AA-841). Sửa C7.2d: cổng là IAM `ref`/`job_workflow_ref` + ruleset, trừ khi chọn Enterprise hoặc Infra public. | **A:** `accounts/<name>/` (khớp CONTEXT.md). **B:** `stacks/platform` tham số hoá (review). **C:** `envs/prod/` (C7.2c hiện tại). **Không có mặc định an toàn:** C7.2c (chuẩn, thắng theo precedence) và CONTEXT.md Infra (AA-841 đã xoá `envs/`) mâu thuẫn từ trước review. Không dựng gì cho prod tới khi chốt; U-40 chỉ kích hoạt khi có ngày go-live nên không chặn tầng 1–3. |
| D-17 | Account cho prod | §5.2/§7 #12: giữ prod trên acc2 kèm biện pháp bù. Không áp được cho principal của management account TrueIDC `033086823579`. | ADR 0001 S235, C7.2a, ADR 0008 d1: prod trên acc2, không thêm account. AA-864 đang nghiên cứu gom acc2 về acc3 hoặc một account. | ADR 0012 dẫn AA-864 và chốt account prod một lần, trước L9. Kết quả khác acc2 thì sửa ADR 0001, C7.2a, DM-9.6. | **A (mặc định):** acc2, kèm biện pháp bù và điểm xem xét management account. **B:** chờ AA-864 rồi mới chốt. |
| D-18 | Vercel Pro | P0-13/§6: lên Pro (~20 USD + usage) trước ngày thu tiền. Bật lại Git integration để `VERCEL_TOKEN` chỉ còn ở production. | S240: ở lại Hobby bằng cách giảm usage, Nghiệp đã duyệt. Backlog #2 đi hướng ngược lại (chỉ preview do CI tạo). DM-10.7: chi tiêu cần Nghiệp duyệt. | Quyết định chi tiêu và điều khoản thương mại, gắn với tenant trả tiền đầu tiên. Trong lúc chờ: giữ backlog #2, ghi P0-1 b6 (token ở mức repo) là rủi ro chấp nhận. | **A:** lên Pro trước ngày thu tiền. **B (mặc định):** Hobby, xem lại khi ký tenant. |
| D-19 | Gói chi tiêu AWS mới | WAF stage ~0–2, ECR 30 image ~1–3, log exec ~1–5, GuardDuty ~1–5, CloudTrail/KMS ~1–3, giữ log ~2–8 USD/tháng. | DM-10.7, §11 Part B: dịch vụ trả phí mới cần Nghiệp duyệt, tính bằng AWS pricing calculator (C3c). Tag `App` từ PR đầu tiên (DM-10.1). | Duyệt từng dòng, sau khi tính lại bằng calculator. Lưu ý tổng P1 cộng prod có thể tiến gần budget account $250. Review §6 **bỏ sót** chi phí LLM định kỳ của eval gate U-29 (xem §4.5). | **A:** duyệt cả gói ở tầng 2 và tầng 3. **B (mặc định, đúng DM-10.7):** duyệt từng mục khi tới lượt. |
| D-20 | OKActions trên alarm | P1-6: thêm OKActions. | S240 (backlog §6): alarm chỉ email khi ALARM. Backlog #8 bỏ `ok_actions` khỏi alarm TP. | Mâu thuẫn trực tiếp với quyết định vận hành mới nhất. | **A (mặc định):** giữ "chỉ ALARM". **B:** OK chỉ đẩy về kênh điện thoại/uptime, không qua email. |
| D-21 | Trigger của AA-842 (tracing) | P2-16: làm sau P1-6. | S238: chỉ làm option B khi job chậm hoặc không giải thích được. | — | **A (mặc định):** giữ trigger S238. **B:** "sau U-30". |
| D-22 | Tự sinh trạng thái phiên và backlog | P2-17: tự sinh. | Steering session-workflow: cập nhật tay §3/§5 cuối phiên. | Đổi nghi thức thì phải sửa steering. | **A (mặc định):** giữ cập nhật tay. **B:** thử tự sinh phần §5/§6 của backlog. |
| D-23 | AA-729 golden set: viết lại hay huỷ | P1-5: golden set 20–30 mẫu cho T2/T9 cộng prompt-injection, ≤ 1 USD/lần. | Backlog: AA-729 chờ Nghiệp quyết viết lại thành eval harness theo stage hay huỷ. | P1-5 là phương án "viết lại". Job PR gọi LLM là chi tiêu định kỳ mới, cần duyệt theo DM-10.7 cùng D-19. | **A:** viết lại AA-729 theo P1-5 (U-29). **B:** huỷ, giữ eval chạy tay. **Mặc định:** AA-729 giữ trạng thái chờ, U-29 chưa làm. |
| D-24 | Tạo issue Linear mới | §6 review đề xuất khoảng 20 issue. | Steering/DM-11: hỏi Nghiệp trước khi tạo. Quota ≤ 100 issue chưa lưu trữ mỗi project. | Danh sách đã gộp ở §7. | Duyệt từng dòng ở §7. |
| D-25 | Dữ liệu thương mại trong root public | §5.1: root public chứa giá và audit. | DM-6.10: repo public không được chứa secret hay dữ liệu. Giá và net rate là `conf:commercial` (DM-6.1, ADR 0004a/0005). | Có thể đang vi phạm DM-6.10, bất kể chọn gì ở D-14. Kiểm trước (U-10), rồi quyết. | **A (mặc định nếu U-10 xác nhận vi phạm, vì DM-6.10 là MUST):** chuyển dữ liệu nhạy cảm sang chỗ private, giữ root public. **B:** private hoá root (D-14 = A/C). |

### 3.2 Sửa sự thật, không cần quyết định (gom vào U-09)

| Chủ đề | Sai ở đâu | Đúng là | Sửa |
|---|---|---|---|
| "CRM" giữ PII | Review §1 (dòng 14, 27); P0-9 REVOKE `crm` | Không có schema `crm` (dump 16/10, 15 schema). AA-821 vẫn parked. | Sửa review. Giữ "REVOKE `crm`" làm điều kiện của L10 (ADR 0008 d8). |
| `aa_cis_admin` "có BYPASSRLS" | P0-8 (dòng 248), P0-9 b2; docstring `aa544_tenant_pool.py:26` | `bypassrls = no` (dump roles). Rủi ro vẫn còn, nhưng cơ chế là: role sở hữu bảng + ENABLE không FORCE (D2) + `pg_read_all_data`. | Sửa review. Sửa docstring trong một PR CIS sau. |
| ADR 0006 "Cognito có MFA" | P1-3 | WORKFORCE: MFA tuỳ chọn (TOTP, chỉ break-glass). Staff đăng nhập bằng email code, không có mật khẩu (dòng Status của ADR 0006, S236: "Google dropped"; thân ADR vẫn tả Google, cần dọn). | Ghi lại đích: "ADR 0006 Phase 1 (Cognito WORKFORCE, không mật khẩu staff)". |
| Dòng trạng thái cũ trong chuẩn | DM-9.1 "today true"; C7.1 (class `db.t3.micro`, final snapshot, parameter group `default`); C4.2a/C2.3f "To build (N3)"; README "How enforced" và §12 | `modules/rds/main.tf`: `skip_final_snapshot=false`, parameter group pg15 riêng (`log_min_duration_statement`, `log_parameter_max_length=0`, `idle_in_transaction`, `rds.force_ssl`), `db.t4g.small`. N1/N2/N3 (trừ C2.3h, script C2.3c)/N4/N5/N7/X3/X8/X9 đã Done. | Root PR chuyển các dòng sang Exists, báo Nghiệp (đúng quy tắc README:37-39). Kiểm luôn các dòng "proposed" của DM-7 (README open item 8) đã được chốt trong AA-825 chưa. |
| DM-11.5 "Enforced by: Branch protection" | Part B §11 | Không có review bắt buộc. Root `master` không được bảo vệ. | Sửa cột enforcement thành "hook subagent; review (chưa cưỡng chế)" (D-13 quyết phần nội dung). |
| `ecosystem-architecture.md` §5 | Bảng OIDC vẫn ghi `aa-cis-dev-role` là role hiện tại | Infra CONTEXT.md:218: `aa-cis-dev-role` đã bị xoá; OIDC đã tách theo repo và job. | Cập nhật §5. |
| CLAUDE.md dự án: ACP "ĐÃ ARCHIVE + XOÁ" | `.claude/CLAUDE.md:16` | `AA-ACP-App` archived public, `AA-ACP-Core` archived private, vẫn còn. | Sửa dòng. |
| Comment trust tf-apply | `cicd_split.tf:515-517` | Comment giả định có branch rule và reviewer, nhưng cả hai đều không tồn tại. | Sửa trong U-01. |
| Số chi phí | §6 review và C3 | Không mâu thuẫn, khác phạm vi: review tính cả ECS/NAT/Backup, C3 chỉ tính RDS. | ADR 0012 giữ một con số đã đối chiếu. |
| Sentry và PII | P0-6, P1-6 | DM-6.4 cấm PII trong log ứng dụng. Sentry tính là log ứng dụng. | Tiêu chí nghiệm thu: `send_default_pii=False` và lọc body/header. |
| ID issue trong review | P0-9 "AA-817 X1" | AA-817 đã Done (S239). Phần tách runtime CIS là AA-860. | Sửa review. |
---

## 4. Lộ trình hợp nhất

**Cách đọc:**
- **Nguồn:** id gốc bên SDLC (P0-x, P1-x, P2-x) và bên data standards (roadmap Nx/Xx/Lx kèm rule).
- **Linear:** issue có sẵn, hoặc "**mới**" (chờ Nghiệp duyệt tạo, xem §7).
- **Công sức:** XS dưới nửa ngày; S 1–2 ngày; M 3–5 ngày; L trên 1 tuần (1 người cộng agent).
- **Chi phí:** USD/tháng tăng thêm, toàn là ước tính [SL], phải tính lại bằng AWS pricing calculator trước khi bật (DM-10.7, C3c).
- **"(D-xx)"**: mục này phụ thuộc một quyết định ở §3. Cho tới khi Nghiệp quyết, làm theo phương án mặc định.

⚠️ Một số mục chạm biến có dấu gạch dưới (`ADMIN_SECRET`, `E2E_ADMIN_*`, `TF_VAR_DB_PASSWORD`, `VERCEL_TOKEN`, DSN). Những biến này Nghiệp sửa tay trong VSCode/Console. Agent không sinh script cho các biến đó.

### 4.1 Tầng 1: Ngay (0 USD, tuần này)

Tổng khoảng 3–4 ngày công. Thao tác ghi trên GitHub, AWS hay Vercel settings do Nghiệp chạy (lệnh một dòng ở §8.4 của review).

| U | Tiêu đề | Nguồn | Linear | Công sức | Phụ thuộc | Chi phí |
|---|---|---|---|---|---|---|
| U-01 | Đóng đường "nhánh bất kỳ → quyền admin acc2": env CIS `dev`/`prod` chỉ cho `main`; `if: github.ref == 'refs/heads/main'` trên terraform-apply; điều kiện IAM `token.actions.githubusercontent.com:ref` trên role tf-apply/db-migrate/deploy (thử trên role nháp trước, có phương án dự phòng); sửa comment `cicd_split.tf:515-517`; ghi rủi ro chấp nhận cho `E2E_ADMIN_*`, `VERCEL_AUTOMATION_BYPASS_SECRET`, `VERCEL_TOKEN` ở mức repo (bù bằng U-26, D-18) | P0-1 b1–3, b5, b6; C7.2d (bổ sung), rule mới DM-11.6 (§5) | **mới** | S | — | 0 |
| U-02 | `ADMIN_SECRET`: chuyển vào env `dev` (main-only) của AA-CIS-App, rồi **xoay một lần ở cả 5–6 nơi** (Secrets Manager, ECS api + worker, Vercel prod + preview, GitHub, Lambda dfs-balance). Gộp với việc §1/#4 trong backlog. ⚠️ Biến có gạch dưới: Nghiệp sửa tay. | P0-1 b4; backlog §1/#4; DM-8.6 | chore (backlog #4) | S | U-01; cần slot Vercel; auto mode tắt | 0 |
| U-03 | Revoke token GitHub đã lộ, cấp lại token fine-grained, ghi bản ghi sự cố ngắn (`docs/incidents/`, vị trí mới), xoá transcript chứa giá trị (`redact_leaked_env.sh`) | P0-2; DM-8.9 | chore | XS | **D-02** | 0 |
| U-04 | Thu hẹp quyền agent, phần không cần sửa chuẩn: (1) `.claude/settings.json` bản commit có `ask` cho apply/iam/secret/workflow run/merge/vercel env/scale, `deny` đọc `~/.aws/**` và `~/.config/gh/**`; allow cá nhân để trong `settings.local.json`, xoá 3 rule có mật khẩu literal; Kiro áp tương đương. (2) Terraform PR: thu hẹp Deny ở `agent_session.tf:159` bằng `NotResource` cho `aa-cis/dev/e2e-test-admin`. (3) Kiểm identity đầu phiên. (4) **Sau D-15:** chuyển tài liệu agent sang `--profile aa365-agent`, sửa DM-8.7 cùng PR, Nghiệp sửa CLAUDE.md toàn cục. (5) Ghi các luồng giữ cho Nghiệp (apply cục bộ, ghi/xoay secret, `aws iam`, scale/stop, DB Migrate `apply`, merge PR nhạy cảm). | P0-3 b1–b5 (b6 ở U-53); DM-8.7, DM-8.8, DM-11.5 | **mới** (AA-730 đã Done S227: role agent đã có, chỉ là tham chiếu) | S | Bước 4 chờ D-15; kiểm aa365-agent làm được S3/presign/ECS exec | 0 |
| U-05 | Bật tính năng bảo mật GitHub miễn phí trên 4 repo public (secret scanning, push protection, Dependabot, CodeQL default, PVR); Dependabot + `dependabot.yml` cho Infra; org bắt 2FA, tắt quyền member tạo repo public; ruleset tối thiểu (chặn force-push và xoá nhánh); chạy gitleaks toàn lịch sử `AA-ACP-App` rồi xoá hoặc private; kiểm lại `secret-scan.yml` của Infra | P0-4; DM-6.10 | **mới** | XS | — | 0 |
| U-06 | Kiểm role phía server (`admin`/`owner`) cho `PATCH /admin/llm-config`, `PUT /admin/budgets`, ghi job-runner; một verifier `hmac.compare_digest` thay mọi chỗ so sánh secret | P0-5; NAM-14; bước tạm của ADR 0006 Phase 1 | **mới** (liên quan AA-816, AA-703) | S | — | 0 |
| U-07 | Thấy lỗi CIS: secret Sentry DSN (free tier, `release = git SHA`, **`send_default_pii=False` + lọc body/header**); alarm 5XXError-rate và IntegrationLatency p95 cho API GW `4ylo382khg` bằng Terraform (missing data = not breaching, C4.1a); một uptime check miễn phí cho CIS `/health` và Booking `/booking/health/ready` | P0-6; C4.1, C4.1a, C1.2, DM-6.4 | **mới** (liên quan AA-832) | S | Sentry vào danh sách sub-processor (U-23) | 0 |
| U-08 | CI/deploy CIS: bỏ `\|\| true` ở pip-audit (ignore có hạn như Booking); `concurrency` cho deploy-dev; guard `shared.job` **fail-closed** khi thiếu credential; giữ `--desired-count 1` kèm comment lý do | P0-7; C6.3a, DM-11.4; X6 | **mới** | XS–S | — | 0 |
| U-09 | Sửa sự thật trong tài liệu (root PR): các dòng §3.2; chuyển dòng trạng thái cũ trong chuẩn sang Exists; sửa cột enforcement của DM-11.5; `ecosystem-architecture.md` §5; CLAUDE.md dự án (ACP); sửa review (CRM, BYPASSRLS, MFA, AA-860) | §3.2; README chuẩn "Precedence" | không cần | XS | — | 0 |
| U-10 | Ba kiểm tra **chỉ đọc**: (a) đếm **chính xác** (`count(*)`, không dùng `reltuples` của dump) và xác nhận PII thật trên Dev: `booking.customers`, `booking.inbox_events`, `tripplanner.customers`, `shared.tenants`, inquiry đến từ domain TripPlanner public kể từ S239, dump laptop 16/09 (cho **D-01**); (b) liệt kê dữ liệu `conf:commercial` (giá, net rate) và audit nhạy cảm trong root public (cho **D-25**); (c) `aws iam get-role OrganizationAccountAccessRole` xem trust của `033086823579`, xin TrueIDC chính sách truy cập và SCP bằng văn bản | §1; P0-12 b3; DM-6.10, C7.1a; AA-864 | không cần (ghi vào audit) | XS | (c) Nghiệp chạy, vì hook chặn `aws iam` | 0 |
| U-11 | Việc XS: dọn nhánh đã merge, `delete_branch_on_merge`, squash-only trên 4 repo; gỡ `/v1/webhooks` khỏi Playground | P2-17 (phần XS); P2-5 (phần "ngay khi rảnh") | không cần | XS | Phần tự sinh backlog chờ **D-22** | 0 |

### 4.2 Tầng 2: Trước tenant trả tiền đầu tiên

Khoảng 15–20 ngày công, 4–6 tuần part-time, song song với Booking. Mốc chặn là **ngày ký tenant đầu tiên**, không phải số tuần. Nếu D-01 = B (Dev có PII thật), cả tầng này chuyển lên làm ngay sau tầng 1.

| U | Tiêu đề | Nguồn | Linear | Công sức | Phụ thuộc | Chi phí |
|---|---|---|---|---|---|---|
| U-12 | Cô lập tenant **fail-closed theo từng wave AA-859**: hoàn thành D5b, wave 3, wave 4; route nào được promote thì bỏ đọc cờ Redis cho route đó (cờ tắt hoặc Redis lỗi → không còn về main pool). Phần "thiếu pool → 503" đã có từ AA-817 PR-A (CIS #765, S239); đường còn mở là `_flag_enabled` (`aa544_tenant_pool.py`) trả "off" khi Redis lỗi; test CI route-policy + **test hai tenant** cho mọi route `/v1`; sửa C2.3g và runbook backlog §6 khi bỏ rollback qua Redis | P0-8 b1, b4; C2.3g, DM-8.4, SEC-10, TST-4 (mở rộng sang HTTP) | AA-859 | L | **D-12**; mỗi lần nới pool phải sửa C2.2 (C2.3c) | 0 |
| U-13 | Redis: bật AUTH + TLS (`auth_token` từ Secrets Manager), cluster mới có at-rest, cùng `cache.t3.micro`; alarm trên metric filter `aa817_tenant_flag_read_failed` và `used_tenant_pool=false` **chỉ trên các route có cờ tenant pool** (khoảng 49/63 route `/v1` còn lại chạy main pool theo thiết kế, alarm toàn bộ sẽ báo liên tục) | P0-8 b2, b3; rule mới SEC-13, dòng C4.1 mới (§5) | **mới** | S–M | Cluster mới cần đổi endpoint (deploy lại api, worker, Booking) | ~0 |
| U-14 | Client `safe_http` dùng chung: resolve DNS, chặn IP private, `allow_redirects=False`, giới hạn size và timeout; thay `_validate_wp_url` | P0-8 b5 | **mới** | S | — | 0 |
| U-15 | **X2 catalogue CI guard** (review bỏ sót): bảng tenant không RLS, policy PUBLIC, tên GUC, NULLIF, FK chéo owner, grant allowlist; kèm lint thẻ PII (X2+) và kernel list (DM-1.5) | X2; TST-5; DM-2.1, 2.3, 5.2, 5.4, 8.3, 8.4, (+6.1, 1.5) | **mới** (AA-817 đã Done) | M | Grant allowlist đầy đủ cần `owners.yaml` (U-33); làm trước bằng allowlist tạm. Phần **+** (lint thẻ PII, kernel list) chỉ thêm khi Nghiệp OK (Part B §12) | 0 |
| U-16 | Isolation probe trong CI: chạy probe aa817 (giữa các tenant) trên mỗi PR chạm RLS; thêm probe chéo app "role runtime CIS `SELECT booking.customers` phải lỗi", để ở trạng thái expected-fail đến khi U-33 xong | P0-9 b4; TST-4; DM-8.4 | **mới** (hoặc gộp U-15) | S | Probe chéo app chỉ xanh sau U-33 | 0 |
| U-17 | *(Có điều kiện, D-03 = B)* Xoay tay mật khẩu RDS master qua Console; sửa DSN `aa-cis/dev/rds` qua Console; force-new-deployment api và worker; làm mới Lambda dùng DSN; cập nhật secret GitHub `TF_VAR_DB_PASSWORD` (Terraform có `ignore_changes = [password]` nên không revert, nhưng giá trị cũ đã lộ vẫn nằm ở đó cho tới U-41). Nếu U-20 làm cùng đợt thì gộp sửa DSN (CNAME + mật khẩu) vào một lần sửa Console. ⚠️ Biến có gạch dưới: Nghiệp sửa tay. | P0-9 b1; DM-8.9 | chore | S | **D-03**; mặc định chuyển vào checklist prod U-40. Làm trước X1 (U-33) là an toàn theo đúng thứ tự review: xoay tay → X1 → managed (U-41) | 0 |
| U-18 | *(Có điều kiện, D-06 = A)* SG riêng cho từng app (CIS api, worker, Booking), SG RDS/Redis liệt kê ingress theo app; viết ADR 0004b | P0-9 b3; ADR 0004 d5; C7.2c | **mới** | S–M | **D-06**; Terraform + deploy lại 3 service | ~0 |
| U-19 | Biên API: rate-limit theo IP + backoff theo user cho `/auth/admin-login` và `/auth/tenant-login` (không khoá cứng theo user); cấp `apigateway:SetWebACL`, `waf_protect_rest_api_stages=true`; throttle stage CIS 50 rps / burst 100, `/auth/*` khoảng 5 rps (đo lại theo giây trước khi siết); khoá `/booking/docs` + `openapi.json` trên `api-booking` (pattern AA-577); CORS rỗng ở môi trường đã deploy; security header (CSP `frame-ancestors 'none'`, nosniff, Referrer-Policy) cho CIS và TripPlanner, lấy Booking làm mẫu | P0-10; C2.3a, C2.3g (bổ sung), rule mới C2.3i (§5); DM-10.7 | **mới** (liên quan AA-806, Done S239; AA-577 là pattern CIS đã áp) | M | WAF stage cần duyệt chi phí (**D-19**) | ~0–2 |
| U-20 | **X10 đầy đủ (AA-829):** diễn tập PITR (instance tạm, smoke query từng schema, ghi RTO so với mục tiêu C1.2 < 1 h, xoá bản tạm); dump 16/09 → S3 private SSE-KMS rồi xoá bản local; **private CNAME cho DSN (DM-9.5)**; **runbook restore một schema (DM-9.4)** | P0-11 b1, b2; X10; DM-9.3, 9.4, 9.5, 6.10, C7.1 | AA-829 | M | **D-10** (thời điểm); sửa DSN là việc tay của Nghiệp; xoá dump local cần Nghiệp duyệt (backlog AA-829) | < 1 (mỗi lần drill, một lần) |
| U-21 | Rollback app và sự cố: bỏ push `:latest` trước, rồi ECR CIS IMMUTABLE qua Terraform, lifecycle giữ 30 image `dev-*`, untagged hết hạn 7 ngày; rollback = trỏ về task-def revision trước, ghi vào `aa-ship`; cách dùng Vercel instant rollback; `docs/ops/incident-response.md` (SEV1–3, ai được báo gồm chị Thư và tenant, 15 phút đầu, mẫu thông báo); hạn cho snapshot thủ công theo dòng DM-7 mới | P0-11 b2 (snapshot), b3–6; DM-9.2, DM-7.5 | **mới** | S | Hạn snapshot chờ **D-09**; ECR 30 image chờ D-19 | ~1–3 |
| U-22 | Log phiên ECS Exec: `executeCommandConfiguration` có logging (CloudWatch/S3, KMS) trên cluster bằng Terraform; bật `log_connections` qua parameter group (idle check C6.3b, trong maintenance window). pgaudit **không** làm ở đây (mặc định D-08 = A) | P0-12 b1, b2 (một phần); DM-8.8, C4.2a, C6.3b | **mới** | S | **D-08**; dòng retention log exec (**D-09**) | ~1–5 |
| U-23 | Gói pháp lý (đề xuất nhẹ nhàng gửi chị Thư, chị và luật sư quyết): privacy/cookie, mẫu DPA + danh sách sub-processor (AWS, TrueIDC, Bedrock/Anthropic, OpenAI, Jev, Vercel, Mapbox, SES, Sentry), RoPA, **runbook DSAR/xoá theo DM-6.7 ("Runbook until then")**, đánh giá chuyển dữ liệu ra nước ngoài, SLA gọn, `support@` vào Linear, status page miễn phí (review §5.7); chốt AA-820 trước 11/11; metadata `ai_generated` trong payload gửi tenant. Kỹ thuật: trang `/privacy`, `/terms` trên TripPlanner và portal; kiểm thu consent đúng DM-6.5 (giá trị, thời điểm, nguồn) | P0-13, §5.7; DM-6.5, 6.7, 6.8 | AA-820 + **mới** | M (phần lớn là thời gian duyệt) | RoPA cần U-24; Vercel Pro chờ **D-18** | 0 (Pro ~20 + usage nếu D-18 = A) |
| U-24 | Gắn thẻ `pii:<class>` cho cột hiện có của Booking/TripPlanner (DM-6.1, bước 1 của L3), regenerate schema reference. RoPA lập từ các thẻ này | L3 (bước thẻ PII); DM-6.1, DM-3.2 | **mới** | S | `COMMENT ON COLUMN` đi qua migration của chủ (D8: `bk-NNN`, `tp-NNN`) | 0 |
| U-60 | DM-6.6 phía TripPlanner: `tripplanner.job` từ DDL template (C6.1d, ADR 0003a d4) + worker Lambda theo lịch + kind `tp_outbox_pii_redact` (90 ngày, E3). Đã nằm trong backlog sống #6; mục U này chỉ để truy vết, không làm hai lần | DM-6.6, DM-7.2; README chuẩn open item 3; L3 (phần redact) | AA-861 | M–L | TP merge cần tắt auto mode | ~0 (Lambda theo lịch) |

### 4.3 Tầng 3: Trong 90 ngày

Khoảng 25–35 ngày công, chưa tính X1 nếu D-05 = B.

| U | Tiêu đề | Nguồn | Linear | Công sức | Phụ thuộc | Chi phí |
|---|---|---|---|---|---|---|
| U-25 | Cổng thay đổi: (1) GitHub App "aa-agent" làm danh tính commit/PR của agent (credential helper cho Claude Code và Kiro); (2) ADR 0011 visibility × gói; (3) ADR 0010 Change authority; (4) ruleset theo tầng rủi ro + CODEOWNERS (`.github/workflows/**`, `db/migrations/**`, `accounts/**`, `.claude/**`, `.kiro/**`, `skill/**`, `CLAUDE.md`, module auth); (5) mỗi App chỉ cài vào repo cần dùng; viết lại `autoMode.environment` | P1-1, §5.1, §5.8 (phần quyền); DM-11.5, DM-6.10, DM-11.1 | **mới** | M | **D-13, D-14, D-25** | 0 nếu D-14 = D (mặc định); ~8 (Team, A/C); ~42 (Enterprise, B) |
| U-26 | Vệ sinh secret: `docs/security/secrets-register.md` (tên, owner, consumer, ngày xoay, gồm TrueIDC); xoá secret mồ côi (`ACPCORE_READ_TOKEN`, `VERCEL_DEPLOY_HOOK`); PAT → App token; Lambda đọc secret theo ARN, không để plaintext trong env; tài khoản E2E chỉ đọc, không thấy PII, rồi thay `ADMIN_SECRET` trong Vercel Preview; **chạy DM-8.10 access review quý đầu** | P1-2, §5.4; DM-8.6, DM-8.10, SEC-2 | **mới** | S | U-25 (App token); tài khoản E2E chỉ đọc và việc thay `ADMIN_SECRET` trong Vercel Preview cần backend kiểm role và verify JWT staff (U-06, U-27), vì hôm nay backend tin `x-admin-role` từ bất kỳ ai giữ `ADMIN_SECRET`; chu kỳ 90 ngày chờ **D-03** | 0 |
| U-27 | RBAC staff phía server: `require_staff(roles=…)` cho mọi router `/admin`; test CI duyệt `app.routes`, fail khi route `/admin` không phải GET mà thiếu policy; backend verify JWT staff; tách key staff/tenant; TTL staff 8h (tạm) → **ADR 0006 Phase 1** (Cognito WORKFORCE, bỏ `X-Admin-Secret`) | P1-3, §5.5; NAM-14 (§9 Part A) | AA-703, AA-816 | M | U-06 | 0 |
| U-28 | Cổng CI đồng đều: CIS bắt buộc `tsc --noEmit` + `next build`; Trivy `exit-code: 1` + `.trivyignore` có hạn; TripPlanner deploy Lambda sau CI kèm smoke; check security header trên preview; bỏ `frontend/**` khỏi path filter deploy ECS; ratchet coverage CIS; **TST-1: replay toàn bộ `tp-NNN` trên `postgres:15`** | P1-4; TST-1 (README open item 5) | **mới** | S–M | — | 0 |
| U-29 | Eval gate có trần chi phí: golden set 20–30 mẫu cho T2/T9 cộng bộ prompt-injection, job PR theo path filter, ≤ 1 USD/lần qua `LLMClient` (stage theo DM-10.4, ví dụ `adhoc_aa729`, ghi `llm_call_log`), kèm trần tháng trong `shared.spend_budget` (DM-10.5), fail khi thiếu baseline. PATCH llm-config kèm eval run id thì làm sau U-34 | P1-5; DM-10.4, DM-10.5, DM-10.6, DM-10.7, DM-4.6, CON-8 | AA-729 (viết lại); AA-783 (nhãn T9, có thể làm golden set) | M | **D-23**, **D-19** (chi tiêu định kỳ); U-34 | ≤ 1/lần; tới ~30/tháng (review P1-5: 85 commit chạm prompt trong ~11 tuần), tính trên acc3 Bedrock |
| U-30 | Log JSON (structlog) + middleware request id gắn `tenant_id`, `job_id` (**chỉ id, không PII**, DM-6.4/C4.2c) ở 3 app; Sentry cho Booking và TripPlanner (scrub PII); test guard thiếu DSN khi `ENVIRONMENT != test`; ghi `db_ms` (C1.1d) | P1-6; C1.1d, DM-6.4, C4.2c | **mới** | S–M | U-07; OKActions chờ **D-20** | 0 |
| U-31 | Phát hiện và audit trail: GuardDuty chỉ foundational + RDS login (tắt các feature đắt), xác nhận bằng ước tính trong 30 ngày thử; IAM Access Analyzer; S3 BPA cấp account; CloudTrail multi-region + KMS + CloudWatch metric filter (root login, thay đổi IAM/SG/trail, đọc Secrets Manager); bucket trail versioning + Object Lock; audit event append-only cho ghi `/admin` và `/v1` **bằng cách mở rộng `acp_shared.audit_log`** (DM-2.4, không tạo bảng chung) | P1-7; DM-2.4, DM-7.1, DM-7.5, C4.2b | **mới** | S–M | **D-09, D-19**; tag `App` (DM-10.1). Review đặt ở P1 vì "Dev giữ PII thật": nếu D-01 = A, Nghiệp có thể dời sang trước prod | ~4–16 (GuardDuty 1–5, CloudTrail/KMS 1–3, giữ log 2–8) |
| U-32 | *(Có điều kiện, D-11 = A)* Quyền chủ thể dữ liệu: script xoá DM-6.7 chạy DRY RUN có query xác minh; endpoint export cho staff (DSAR, rule mới DM-6.11). Hạn snapshot thủ công của P1-8 nằm ở U-21; redact outbox TP (DM-6.6) ở U-60, không phụ thuộc D-11 | P1-8; L3 (script xoá, kéo sớm); DM-6.7 | AA-839 (cần duyệt tạo) | M | **D-11**; phần TP của script xoá cần U-60 | 0 |
| U-33 | **Chuỗi X1** theo đúng ADR 0008 d6, theo thứ tự: (1) `owners.yaml` + template role bootstrap (DM-1.2; phạm vi sẵn có của AA-826); (2) `bk_owner`/`tp_owner` NOLOGIN (DM-1.3); `db_migrator` trên task def riêng có input `environment` (DM-8.2, C7.2d); định nghĩa role LOGIN trong git (DM-8.1); (3) AA-817 D2 role-scoped policies; (4) **AA-860** chuyển runtime CIS sang `cis_app`, REVOKE trên `booking`/`tripplanner`, bỏ `pg_read_all_data`; (5) read-only ops role (DM-8.8, X1+, cần Nghiệp OK theo Part B §12) | P0-9 b2; X1; DM-1.2, 1.3, 8.1, 8.2, 8.8, 8.9; SEC-1 | AA-826 (bước 1) + **mới** (bước 2, vì AA-807 đã Done) + AA-860 (bước 3–4) | L | **D-05** (B = kéo lên tầng 2). Backlog #17 ghi AA-860 "sau AA-807/AA-826": chỉ cần bước 1 của AA-826, không cần hash guard (U-35) | 0 |
| U-34 | ADR 0009 AI platform: contract gateway CON-8, cột `app`/`is_shadow` trên ledger, AI Use Register (lấy từ `llm_role_config` + `llm_model_catalog`, công bố như danh sách sub-processor), quyết định kiểm PII tự động DM-6.4 (regex email/phone/passport trên prompt và ghi ledger) | AA-804; DM-6.4, CON-8, DM-10.5; area adlc Q13 | AA-804 | M | — | 0 |
| U-35 | X7 phần còn lại: consumer contract hash guard (CON-4, TST-6, DM-3.6) + công cụ playbook đọc `owners.yaml`. **Kiểm câu §3 review** "bản copy contract đã pin hash trong test" | X7; CON-4, TST-6, DM-3.6 | AA-826 (`owners.yaml` + role bootstrap của AA-826 tính ở U-33 bước 1) | S–M | Hash guard: không phụ thuộc; công cụ playbook: sau U-33 bước 1 | 0 |
| U-36 | X4 tách TripPlanner: bỏ `set_catalog_tenant` (SEC-10), đọc qua `catalog.*`, drop 7 bảng đóng băng và 12 FK chéo owner (DRY RUN), REVOKE grant trực tiếp của TP trên bảng CIS | X4; DM-2.3, 5.2, 8.4; SEC-5, CON-1 | AA-712 | M–L | — | 0 |
| U-37 | N6 Dead Table Registry (`docs/architecture/dead-table-registry.md`) + quarantine wave 1; L1 wave 2–3, gồm archive `shared.pipeline_jobs` | N6, L1; DM-3.8, 3.9 | **mới** (AA-807 đã Done) | M | L1 chỉ sau N6 + chủ bảng xác nhận (trigger S237); DRY RUN theo `destructive-ops.md` | 0 |
| U-38 | Đưa các review định kỳ vào nghi thức phiên: capacity review hằng tháng (C8a–c), check `pg_stat_statements` hằng tuần (C4.3), access review hằng quý (DM-8.10), rà quyền agent hằng quý (§5.8). Lần đầu: capacity review | C8, C4.3, DM-8.10; §5.8 | AA-838 (cần duyệt tạo) | S, định kỳ | — | 0 |
| U-39 | Toàn vẹn dữ liệu (ghi cho đủ, ngoài phạm vi SDLC): X5 `shared.countries` (ISO-3166) + view country trong `catalog` + cột `country_iso2`. (X3 tour key đã Done qua AA-830, S238; orphan rate có trong `schema_dump.py`) | X5; DM-2.4 | **mới** | M | — | 0 |
| U-61 | Phần còn lại của N3: C2.3h `idle_session_timeout` cho role `tripplanner` (thử trên Dev với Lambda vừa thaw trước khi bật; pool TP thử acquire lại một lần); C2.3c script CI đọc giá trị Terraform và fail khi tổng connection budget vượt (C2.2) | N3; C2.3c, C2.3h | **mới** (hoặc mở lại AA-824) | S | C2.3h là `ALTER ROLE`: đi qua migration ngoại lệ N3 hoặc role bootstrap X1 (C2.3a, MIG-6) | 0 |

### 4.4 Tầng 4: Có điều kiện kích hoạt

| U | Tiêu đề | Nguồn | Linear | Kích hoạt khi | Công sức | Chi phí |
|---|---|---|---|---|---|---|
| U-40 | **L9 prod blueprint + ADR 0012 (Environment model):** instance riêng trên acc2 (hoặc theo D-17), Multi-AZ, PITR 14 ngày, AWS Backup cross-region, quarterly drill, RPO/RTO DM-9.6; **C7.2e** role tách từ ngày đầu, `aa_cis_admin` chỉ break-glass, Enhanced Monitoring, pgaudit (D-08); **C7.2f** DSN qua private CNAME; layout Terraform (D-16) và cổng prod (sửa C7.2d); mạng prod (NAT GW mỗi AZ, ALB internal, xoá default VPC); Security Hub FSBP + Config; biện pháp bù cho acc2 (OIDC/KMS/ABAC `env=prod`, agent không có quyền prod); đổi tên env Infra; xoay master/GitHub token theo S240 (D-02/D-03); một con số chi phí đã đối chiếu | P2-1, P2-14, §5.2; L9, L7 (trigger "before prod" của RDS Proxy, C3); C7.2a–f, DM-9.6; area E13 (phần prod) | **mới** (L9, chưa có issue); AA-864 | Có ngày go-live. **Tiền đề:** U-33 xong (C7.2e: "X1 Done is a prerequisite of L9"), U-20 (drill trước prod, DM-9.3), U-61 (budget), D-16 và D-17 đã chốt | L | ~150–300 (C3: RDS ~110–130) |
| U-41 | `manage_master_user_password` + bỏ `TF_VAR_DB_PASSWORD`; sửa DM-8.6, CLAUDE.md toàn cục (Nghiệp), skill aa-cis-schema cho secret JSON | P0-9 b5; C2.3b, DM-8.9, DM-8.6 | — | X1 (U-33) xong, gồm `db_migrator`, schema dump, probe; hoặc L9 (**D-04**) | S | ~0.4 |
| U-42 | Luồng Terraform: plan comment trên PR, apply gắn hash plan, `fmt`/`validate`/tflint/trivy config, drift hằng đêm, state lock cho acc1/acc3, xoá `.bak`/`.tfplan` | P2-2 | — | Trước prod hoặc sự cố drift tiếp theo | M | 0 |
| U-43 | Build once theo digest, `attest-build-provenance`/SBOM, `vercel build --prebuilt`, pin SHA mọi action + allowlist | P2-3 | — | First prod; attestation theo D-14 | M | 0 |
| U-44 | ADR 0013 HTTP API conventions: `response_model` cho `/v1`, commit `openapi.json`, `oasdiff breaking`, problem+json + `request_id` chỉ cho `/v1` ngoài và `docs/contracts`, access log API GW, tắt `execute-api`; inventory API trong `ecosystem-architecture.md`. Dẫn CON-3–5 | P2-4, §5.5 (phần "khi tenant tích hợp API"); CON-3–5, DM-3.6 (X7 là U-35) | — | Tenant đầu tiên tích hợp bằng API | M | ~0–1 (access log) |
| U-45 | Public API v1: `shared.tenant_api_keys` (scope, hết hạn, ≥ 2 key active, **lưu hash**, có dòng retention, đi theo D8), X-API-Key, rate-limit theo key, usage plan | P2-5; DM-1.5, DM-6.9, NAM-13, DM-7.1, MIG-4; ADR 0006 Phase 3 | AA-813 (liên quan) | Quyết định bán gói API | M | ~0 |
| U-46 | `Idempotency-Key` cho POST tốn tiền hoặc không đảo ngược được (mở rộng CON-7 sang HTTP, rule CON-10) | P2-6; CON-7 | AA-682 | Trước khi bật thanh toán | S–M | 0 |
| U-47 | release-please, GitHub Deployments, CHANGELOG, release note cho tenant, DORA | P2-7 | — | First prod | S–M | 0 |
| U-48 | Org `.github`: reusable workflow (Booking làm mẫu), template PR (gồm checklist SQL §8 Part A), template issue, SECURITY.md, CONTRIBUTING | P2-8; DM-11.1 | — | Contributor thứ hai, hoặc lần lệch pipeline thứ ba | S | 0 |
| U-49 | SLO người dùng + alarm burn-rate, dashboard mỗi app, k6; đưa vào C8 | P2-9; C1.2, C1.2a, C4.1, C8b | — (kết quả vào review C8 của AA-838/U-38) | First prod | M | ~0–3 (dashboard) |
| U-50 | Bot mở PR copy migration sang Infra (giữ merge tay và Copy Guard); preflight `required_schema_version` (MIG-4 b5) | P2-10; MIG-4, DM-11.2 | AA-826 | Sự cố "app deploy trước migration" tiếp theo | S–M | 0 |
| U-51 | ECS exec thành break-glass; workflow "run-script" chỉ chạy script đã commit trên main hoặc job kind đã review; đường thay thế cho A/B LLM | P2-11, P0-12 b4; DM-8.8, MIG-5 | — | Sau U-22 + U-33, khi có prod (**D-07**) | M | 0 |
| U-52 | Pentest bên thứ ba một lần | P2-12 | — | Trước deal enterprise đầu tiên | — | một lần (báo giá) |
| U-53 | Không còn key tĩnh trên máy dev (IAM Identity Center/aws-vault); agent chạy trong devcontainer hoặc OS user riêng chỉ có `aa365-agent`; tắt `[acc1-legacy-default]` **sau khi đọc lại hồ sơ AA-517** | P2-13, P0-3 b6; DM-8.7 | AA-517 (tham chiếu) | Sau U-04, trong 6 tháng | M | 0 |
| U-54 | `rollback.yml`; Lambda alias `live` (trigger Cognito theo ADR 0006 d5; mở rộng sang Lambda TP) | P2-15 | AA-703 | First prod | S | 0 |
| U-55 | Trailer `AI-Agent:` trong commit (mở rộng quy tắc commit `Refs AA-xxx`), telemetry agent, tracing AA-842 option B, SLSA L3, harden-runner | P2-16 | AA-842 | Theo **D-21** (mặc định: job chậm hoặc không giải thích được) | M | 0 |
| U-56 | Diễn tập nâng PostgreSQL 15 lên major mới trên snapshot restore (đường X10), smoke 3 app | C5.5b | **mới** | 05/2027 (6 tháng trước EOL 11/2027), capacity review gắn cờ; cần U-20 (đường restore) xong trước | M | < 1 |
| U-57 | Phần còn lại của L3: thu `tripplanner.customers` về guest contact + consent (DM-6.2), dòng retention TP/Booking (DM-7.1), script xoá đầy đủ nếu D-11 = B | L3; DM-6.2, 6.7, 7.1 | AA-839 | ADR 0006 Phase 4 / trước prod | M–L | 0 |
| U-58 | L10 tenant CRM qua playbook (schema `crm`, REVOKE `crm` cho runtime CIS, DPA, isolation probe) | L10; DM-6.8 | AA-821, AA-813 | Nghiên cứu AA-821 được duyệt + X1/X2/X7/AA-813 xong | L | — |
| U-59 | `reserved_concurrent_executions` cho Lambda TP (`tripplanner_browse`/`assembly`) bằng 10 trong lần apply đầu sau khi quota lên 1000, trước mọi load test | C2.3e (E6) | AA-824 (Done; mở lại hoặc **mới**) | Quota Lambda 1000 có hiệu lực | XS | 0 |

Các mục Later khác giữ nguyên trigger theo S237 §7, C3 và C8: L2 hội tụ định danh địa điểm (sau X4), L4 read model, L5 partition, L6 Athena, L7 RDS Proxy (trigger tải; trigger "before prod" đã tính trong U-40), L8 relay. Lộ trình này không đổi chúng.

### 4.5 Tổng chi phí tăng thêm (ước tính, chờ duyệt theo D-19)

| Tầng | USD/tháng | Ghi chú |
|---|---|---|
| 1. Ngay | 0 | Tính năng GitHub miễn phí, Sentry free, uptime free |
| 2. Trước tenant | ~2–10 | WAF stage 0–2, ECR 30 image 1–3, log exec + `log_connections` 1–5, Redis mới cùng loại node ~0. Drill PITR < 1 là phí một lần, không tính tháng. Cộng ~20 + usage nếu D-18 = A (Vercel Pro) |
| 3. 90 ngày | ~4–16 AWS | GuardDuty giới hạn 1–5, CloudTrail/KMS 1–3, giữ log 2–8 (D-09). Cộng ~8 (Team) hoặc ~42 (Enterprise) nếu D-14 ≠ D. Cộng eval gate U-29 tới ~30 LLM (acc3, D-23) |
| **Cộng dồn hết tầng 3, phương án mặc định** (D-14 = D, D-18 = B, U-29 chưa làm) | **~6–26** | Chỉ phí AWS acc2 |
| **Cộng dồn hết tầng 3, theo review** | **~35–55** (A/C) hoặc **~70–90** (B) | Bằng 6–26 + GitHub (8 hoặc 42) + Vercel Pro 20; khớp §6 review. Chưa gồm eval gate U-29 (review bỏ sót) |
| 4. Prod (U-40) | ~150–300 | Ước rất thô. ADR 0012 giữ một con số đã đối chiếu với C3 (RDS ~110–130, RDS Proxy "before prod" ~20–25). Lưu ý budget account $250 tính cả Dev hiện tại |

### 4.6 Guardrail giữ nguyên (§7 review, khớp chuẩn)

Không dựng staging thường trực hay multi-region. Không mua GHAS cho repo private. Không public Infra. Không bật Security Hub/Config trước prod. Không audit SOC 2 thật lúc này. Không bắt duyệt tay mọi PR (chờ D-13). Không canary/CodeDeploy. Không dùng Pact broker. Không viết lại auth trước ADR 0006 Phase 1. Không chạy eval toàn catalog (DM-10.6). Không tách account prod (ADR 0001, trừ khi D-17 = B dẫn tới kết quả khác). Không bật managed master secret trước X1 (C2.3b/DM-8.9). Không khoá cứng tài khoản theo username.

---

## 5. Đề xuất sửa data standards (chỉ đề xuất, chờ Nghiệp duyệt)

Tất cả đi chung **một PR v1.1** vào root repo. Steering và skill nào nhắc lại rule thì sửa cùng PR. Thay đổi đụng quyết định đã accepted thì sửa kèm ADR 0008 hoặc ADR liên quan (mục "Changing this standard"). Rule id mới đánh tiếp số cuối của mỗi nhóm. Kiểm lại số chưa dùng khi viết PR (đã kiểm 17/10: TST-7 và C2.3h **đã có** trong v1.0, nên rule mới là TST-8 và C2.3i; SEC-13, CON-9/10, DM-6.11/12, DM-8.11/12, DM-11.6, C1.3, C6.3c, C7.2g/h còn trống).

### Part A (Engineering)

| Rule đề xuất | Loại | Nội dung ngắn | Nguồn | Phụ thuộc |
|---|---|---|---|---|
| SEC-13 | mới | Kho dữ liệu dùng cho quyết định bảo mật (cờ tenant pool, cache phiên) MUST có AUTH + TLS. Thiếu cờ hoặc lỗi đọc cờ MUST NOT nới quyền: route đã promote fail closed. | P0-8; U-13 | — |
| SEC-10, C2.3g, §9 (dòng tenant pool) | sửa | Ghi cơ chế promote từng route AA-859 và cơ chế rollback sau khi bỏ Redis `DEL` (SSM Parameter hoặc deploy), nếu D-12 = B; với A chỉ cập nhật trạng thái từng wave. | P0-8; D-12 | D-12 |
| TST-8 | mới | Mỗi route `/v1` có test hai tenant (0 dòng chéo). Mỗi route `/admin` không phải GET có policy role, được test liệt kê `app.routes`. | P0-8 b4, P1-3; U-12, U-27 | — |
| TST-4 | sửa | Isolation probe chạy trong CI (không chỉ là runbook trước tenant đầu), kèm probe chéo app sau X1. | P0-9 b4; U-16 | — |
| CON-9 | mới | Contract HTTP `/v1` ngoài: OpenAPI commit trong repo, `oasdiff breaking` trong CI, problem+json + `request_id`, major song song ≥ 30 ngày (như CON-5). Nội dung chi tiết ở ADR 0013. | P2-4; U-44 | Trigger tích hợp API |
| CON-10 | mới | POST tốn tiền hoặc không đảo ngược được MUST nhận `Idempotency-Key` và lưu UNIQUE (mở rộng CON-7). | P2-6; U-46 | Trigger thanh toán |
| §8 checklist | sửa vị trí | Checklist SQL đưa vào template PR của org (P2-8) thay vì chép tay. | P2-8; U-48 | Trigger |

### Part B (Data management)

| Rule đề xuất | Loại | Nội dung ngắn | Nguồn | Phụ thuộc |
|---|---|---|---|---|
| DM-6.4 | sửa | Error tracker bên thứ ba (Sentry) tính là log ứng dụng: MUST `send_default_pii=False` và lọc body/header. Nếu duyệt U-34, thêm enforcement "kiểm PII tự động trong gateway". | P0-6, P1-6; U-07, U-34 | U-34 cho phần CI |
| DM-6.11 | mới | Quyền truy cập/xuất (DSAR): staff xuất được toàn bộ dữ liệu một traveller theo cùng phạm vi DM-6.7, trong thời hạn luật định; mỗi lần xuất ghi audit. | P1-8; D-11 | D-11 |
| DM-6.12 | mới | Danh sách sub-processor và RoPA được lập từ thẻ `pii:` (DM-6.1) và AI Use Register, cập nhật khi thêm vendor. | P0-13; U-23, U-24, U-34 | — |
| DM-7 (bảng) | thêm dòng | CloudTrail/log bảo mật: ≥ 365 ngày (S3/Glacier, Object Lock). Log ứng dụng CloudWatch: 30–90 ngày (thay 14). Log phiên ECS Exec: ≥ 365 ngày. Snapshot RDS thủ công: hạn 90 ngày, trừ snapshot DM-9.2 của migration phá huỷ còn trong cửa sổ expand/contract. Log pgaudit (nếu D-08 = B): như log bảo mật. | P1-7, P0-11, P0-12; D-09 | D-09 (DM-7.5) |
| DM-8.7 | sửa | Trung lập về profile: "xác nhận acc2 bằng `sts get-caller-identity` với profile của phiên; agent dùng `aa365-agent`, `aa365-admin` chỉ cho Nghiệp". | P0-3; D-15 | D-15 |
| DM-8.8 | sửa | Log phiên ECS Exec MUST bật trên cluster (CloudWatch/S3, KMS) trước khi agent được exec. Nếu D-07 = B (khi có prod): exec thành break-glass, script thường chạy qua workflow run-script hoặc job kind đã review. Sửa MIG-5 cùng PR. | P0-12, P2-11; D-07 | D-07 cho phần break-glass |
| DM-8.9 | sửa | Nếu D-03 = B: mật khẩu master xoay ngay khi nghi lộ (cả Dev), không chỉ "after use (prod)". | P0-9, §5.4; D-03 | D-03 |
| DM-8.11 | mới | Register secret (`docs/security/secrets-register.md`): owner, consumer, ngày xoay. Nghi lộ thì xoay và ghi một bản sự cố. Chu kỳ định kỳ (90 ngày) chỉ khi D-03 = B. | P1-2, §5.4 | D-03 |
| DM-8.12 | mới | Mạng: mỗi app một SG; SG RDS/Redis chỉ nhận ingress từ SG app được liệt kê. Kèm ADR 0004b. | P0-9 b3; D-06 | D-06 |
| DM-9.3 | sửa | Ghi thời điểm drill đã chốt (D-10). Drill ghi RTO so với C1.2 (< 1 h). Chu kỳ trên Dev: quý (review) hoặc chỉ trước prod (hiện tại). | P0-11; D-10 | D-10 |
| DM-10.7 | sửa | Thêm dòng "đã duyệt" cho từng chi tiêu mới khi Nghiệp duyệt (WAF stage, ECR, log, GuardDuty, CloudTrail, GitHub Team, Vercel Pro). | §6 review; D-14, D-18, D-19 | Các D tương ứng |
| DM-11.5 | sửa | Sửa ngay cột "Enforced by" cho đúng sự thật. Nội dung rule theo D-13 (ADR 0010). | P1-1; D-13 | D-13 cho nội dung |
| DM-11.6 | mới | Trust OIDC cho role deploy/apply/migrate MUST giới hạn theo `ref` (main hoặc tag) ở IAM, và env GitHub MUST có branch policy. Workflow apply MUST kiểm `github.ref`. | P0-1; U-01 | — |

### Part C (Operations and scaling)

| Rule đề xuất | Loại | Nội dung ngắn | Nguồn | Phụ thuộc |
|---|---|---|---|---|
| C4.1 (bảng) | thêm dòng | API GW 5XXError-rate + IntegrationLatency p95 mỗi API; uptime ngoài cho mỗi health endpoint; `aa817_tenant_flag_read_failed` > 0; route tenant `used_tenant_pool=false`. | P0-6, P0-8; U-07, U-13 | — |
| C4.1a | sửa | Ngoại lệ được chấp nhận: uptime check SaaS nằm ngoài Terraform, được ghi trong register. | P0-6 | — |
| C4.2c | sửa | Nếu D-08 = B: scope pgaudit không được ghi literal PII (ví dụ `ddl` + role-based chỉ cho break-glass). Ghi rõ Sentry thuộc phạm vi rule này. | P0-12; D-08 | D-08 |
| C2.3i | mới | Throttle stage API GW (CIS 50 rps / burst 100, `/auth/*` ~5 rps) là chặn phía HTTP, bổ sung cho C2.3a/C2.3g. Đổi số thì đo lại theo giây và cập nhật C2.2. | P0-10; U-19 | — |
| C6.3c | mới | Deploy guard MUST fail closed khi thiếu credential. Workflow deploy MUST có `concurrency` theo service. | P0-7; U-08 | — |
| C7.1 (bảng) | sửa | Chuyển dòng cũ (class, final snapshot, parameter group) sang "Exists". Thêm dòng: log phiên ECS Exec, ECR immutable. | §3.2; U-09, U-21, U-22 | — |
| C7.2c | sửa | Layout Terraform prod theo ADR 0012 (D-16), thay `envs/prod/` đã cũ sau AA-841. | P2-1; D-16 | D-16 |
| C7.2d | sửa | Cổng prod: IAM `ref`/`job_workflow_ref` + ruleset PR khi Infra private trên Free/Team; env reviewer chỉ khi repo public hoặc Enterprise. | §5.1, §5.2; D-14, D-16 | D-14, D-16 |
| C7.2g | mới | Mạng prod: NAT GW mỗi AZ, ALB internal, xoá default VPC; Security Hub FSBP + Config bật cùng prod (không bật trên Dev). | P2-14; U-40 | Trigger L9 |
| C7.2h | mới | Biện pháp bù cho prod trên acc2: role/trust OIDC riêng, KMS CMK riêng, ABAC `env=prod` chặn role Dev, state key riêng, agent không có quyền trên `env=prod`; điểm xem xét management account (D-17). | §5.2; U-40 | D-17 |
| C1.3 | mới | SLO người dùng (HTTP) và alarm burn-rate từ khi có prod; kết quả đưa vào C8b. | P2-9; U-49 | Trigger prod |

---

## 6. Mục data standards còn "to build" mà review không nhắc → đưa vào lộ trình

Đọc §1.4 trước. Bảng dưới chỉ gồm việc **thật sự còn mở** sau khi đối chiếu với S239–S241 và code.

| Mục chuẩn còn mở | Rule | Vì sao quan trọng | → U / tầng |
|---|---|---|---|
| X2 catalogue CI guard (+ lint thẻ PII, kernel list) | TST-5; DM-2.1, 2.3, 5.2, 5.4, 8.3, 8.4, (+6.1, 1.5) | Lớp chặn ở DB cho cô lập tenant. P0-8 chỉ có test HTTP. | U-15, tầng 2 |
| X4 / AA-712 tách TripPlanner | SEC-5, SEC-10, CON-1, DM-2.3 | TP vẫn tự đặt GUC tenant master, có grant trực tiếp trên bảng CIS và 12 FK chéo owner. | U-36, tầng 3 |
| X1 ngoài phần runtime CIS: `owners.yaml`, `bk_owner`/`tp_owner`, `db_migrator` task def riêng, role trong git, read-only ops role | DM-1.2, 1.3, 8.1, 8.2, 8.8 (X1+), C7.2d | Đây mới là câu trả lời của chuẩn cho "script chạy bằng master" (P0-12). Là tiền đề của L9 (C7.2e). | U-33, tầng 3 (D-05) |
| N3 phần còn lại: `idle_session_timeout` role `tripplanner`, script CI connection budget | C2.3h, C2.3c | AA-824 (Done S237) chỉ làm nửa Terraform; hai mục này không có trong code. | U-61, tầng 3 |
| X7 / AA-826 consumer contract hash guard + tooling | CON-4, TST-6, DM-3.6 | Review cho là đã có. Cần kiểm. | U-35, tầng 3 |
| Phần còn lại của X10: private CNAME, restore một schema | DM-9.5, DM-9.4 | Rút ngắn RTO, tách sự cố một app khỏi hai app còn lại. | U-20, tầng 2 |
| L3: thẻ PII trên cột hiện có, redact outbox, script xoá, thu `tripplanner.customers`, dòng retention TP/Booking | DM-6.1, 6.2, 6.6, 6.7, 7.1 | Không có thẻ thì không lập được RoPA. | Tách theo bước: U-24 thẻ (tầng 2); U-60 redact TP (tầng 2); U-32 script xoá nếu D-11 = A (tầng 3); U-57 phần còn lại (tầng 4) |
| DM-6.6 redact payload outbox phía TripPlanner (+ `tripplanner.job`, README open item 3) | DM-6.6, DM-7.2, C6.1d | Booking đã làm (#23). TP chờ AA-861 (`tripplanner.job`). | U-60, tầng 2 (backlog #6, không phụ thuộc D-11) |
| DM-6.4 kiểm PII tự động trên prompt và log (README open item 6) | DM-6.4 | Có trong area report Q13 nhưng bị bỏ khỏi README review. | U-34, tầng 3 |
| DM-6.5 thu consent (giá trị, thời điểm, nguồn) | DM-6.5 | Liên quan trực tiếp trang privacy/cookie. | U-23, tầng 2 |
| DM-8.10 access review DB hằng quý | DM-8.10 | Review chỉ đề xuất rà quyền agent. | U-26 (lần đầu) + U-38 (định kỳ), tầng 3 |
| C8 capacity review hằng tháng + C4.3 check `pg_stat_statements` hằng tuần | C8a–c, C4.3 | Trigger C3 chỉ chạy khi có người đo. | U-38, tầng 3 |
| C2.3e reserved concurrency Lambda TP | C2.3e (E6) | Phía Lambda của throttle P0-10. | U-59, tầng 4 (trigger quota) |
| C5.5b diễn tập nâng major PG15 | C5.5b | EOL 11/2027. | U-56, tầng 4 |
| N6 Dead Table Registry + L1 (archive `shared.pipeline_jobs`) | DM-3.8, 3.9 | File registry chưa tồn tại dù AA-807 đã Done. | U-37, tầng 3 |
| TST-1 replay migration TP trên `postgres:15` | TST-1 | Lỗ hổng CI duyệt trong chuẩn, gộp vào AA-807 (Done) nhưng chưa làm. | U-28, tầng 3 |
| ADR 0009 AI platform (CON-8, cột `app`/`is_shadow`, AI Use Register) | CON-8, DM-10.5 | Eval id trên PATCH llm-config (P1-5) phụ thuộc vào nó. | U-34, tầng 3 |
| C7.2e, C7.2f, trigger RDS Proxy "trước prod" (L7) | C7.2e, C7.2f, C3 | P2-14 thiếu các mục này. | U-40, tầng 4 |
| X5 `shared.countries` (X3 đã Done qua AA-830, S238; §12 còn ghi "to build" là dòng cũ, sửa ở U-09) | DM-2.4 | Toàn vẹn dữ liệu, ngoài phạm vi SDLC. | U-39, tầng 3 |
| L9 prod blueprint chưa có issue | DM-9.6, C7.2 | P2-1/P2-14 + ADR 0012 nên gộp thành một issue L9. | U-40 (issue mới ở §7) |

---

## 7. Issue Linear đề xuất tạo mới (KHÔNG tạo, chờ Nghiệp duyệt từng dòng, D-24)

Project dùng tên hiện có. Trước khi tạo, kiểm quota (≤ 100 issue chưa lưu trữ mỗi project) và kiểm trùng theo skill `aa-linear-issue`. Nếu project Data Platform gần ngưỡng, có thể tạo project mới "Platform Security & SDLC", việc này cũng cần Nghiệp duyệt.

| # | Tiêu đề (EN) | U | Project | Ưu tiên |
|---|---|---|---|---|
| 1 | Restrict deploy/apply/migrate OIDC trust to main: env branch policy, ref guard, IAM ref condition | U-01 | Data Platform — Schema, Ops & Scale | Urgent |
| 2 | Agent least privilege: committed ask/deny lists, block ~/.aws reads, e2e secret allowlist, aa365-agent switch | U-04 | Data Platform — Schema, Ops & Scale (AA-730 đã Done S227, chỉ tham chiếu) | High |
| 3 | Enable free GitHub security features, org 2FA, Infra Dependabot; scan archived AA-ACP-App history | U-05 | Data Platform — Schema, Ops & Scale | High |
| 4 | Server-side role check on llm-config, budgets and job-runner writes; constant-time secret compare | U-06 | CIS Core — Pipeline, LLM & Platform | High |
| 5 | CIS error visibility: Sentry DSN with PII scrubbing, API Gateway 5xx/latency alarms, external uptime check | U-07 | CIS Core — Pipeline, LLM & Platform | High |
| 6 | CIS CI/deploy hardening: blocking pip-audit, deploy concurrency, fail-closed job guard | U-08 | CIS Core — Pipeline, LLM & Platform | High |
| 7 | Redis AUTH/TLS/at-rest and tenant-flag read-failure alarm | U-13 | Data Platform — Schema, Ops & Scale | High |
| 8 | SSRF-safe outbound HTTP client (safe_http) for tenant-supplied URLs | U-14 | CIS Core — Pipeline, LLM & Platform | High |
| 9 | X2 catalogue CI guard: RLS, PUBLIC policies, NULLIF, cross-owner FKs, grant allowlist, PII-tag lint | U-15 (+ U-16) | Data Platform — Schema, Ops & Scale | High |
| 10 | Per-app security groups for CIS api/worker and Booking (ADR 0004b) | U-18 | Data Platform — Schema, Ops & Scale | Medium (chỉ khi D-06 = A) |
| 11 | API edge hardening: login rate limit, WAF and throttles on the CIS stage, gate Booking docs, CORS, security headers | U-19 | CIS Core — Pipeline, LLM & Platform | High |
| 12 | App rollback readiness: immutable CIS ECR, task-def rollback runbook, Vercel rollback, incident one-pager | U-21 | CIS Core — Pipeline, LLM & Platform | High |
| 13 | ECS Exec session logging and log_connections | U-22 | Data Platform — Schema, Ops & Scale | High |
| 14 | Legal readiness packet proposal for Ms. Thư and /privacy, /terms pages | U-23 | TripPlanner & AA-Booking | Medium |
| 15 | Tag existing Booking and TripPlanner PII columns (DM-6.1) | U-24 | TripPlanner & AA-Booking | Medium |
| 16 | Change authority: agent GitHub App identity, ADR 0010/0011, risk-tiered rulesets and CODEOWNERS | U-25 | Data Platform — Schema, Ops & Scale | Medium |
| 17 | Secrets register, orphaned-secret cleanup, read-only E2E account, first quarterly access review | U-26 | Data Platform — Schema, Ops & Scale | Medium |
| 18 | CI gate parity: CIS typecheck/build, blocking Trivy, TripPlanner Lambda deploy after CI, TripPlanner migration replay on postgres:15 | U-28 | CIS Core — Pipeline, LLM & Platform | Medium |
| 19 | Structured JSON logs with request ids (ids only) and Sentry for Booking and TripPlanner | U-30 | CIS Core — Pipeline, LLM & Platform | Medium |
| 20 | Account detection baseline: GuardDuty (limited features), Access Analyzer, S3 BPA, hardened CloudTrail | U-31 | Data Platform — Schema, Ops & Scale | Medium (cần D-19) |
| 21 | X1 owner roles and db_migrator task definition (Booking/TripPlanner first; owners.yaml comes from AA-826) | U-33 | Data Platform — Schema, Ops & Scale | High (tiền đề của AA-860) |
| 22 | N6 Dead Table Registry and legacy shared.pipeline_jobs archive | U-37 | Data Platform — Schema, Ops & Scale | Low |
| 23 | X5 shared.countries and catalog country view | U-39 | Data Platform — Schema, Ops & Scale | Low |
| 24 | L9 prod blueprint and ADR 0012 environment model | U-40 | Data Platform — Schema, Ops & Scale | Medium (trigger: ngày go-live) |
| 25 | PostgreSQL 15 major-upgrade rehearsal on a restored snapshot | U-56 | Data Platform — Schema, Ops & Scale | Low (trigger 05/2027) |
| 26 | N3 remainder: tripplanner idle_session_timeout and a CI connection-budget check (or reopen AA-824) | U-61 | Data Platform — Schema, Ops & Scale | Low |

**Không cần issue mới** (dùng issue hoặc chore có sẵn):
- U-02, U-03, U-17: chore trong backlog §1;
- U-09, U-10, U-11: root PR hoặc audit;
- U-12: AA-859;
- U-20: AA-829;
- U-27: AA-703, AA-816;
- U-29: AA-729;
- U-33 bước 1, U-35: AA-826; U-33 bước 3–4: AA-860;
- U-34: AA-804;
- U-36: AA-712;
- U-46: AA-682;
- U-55: AA-842;
- U-57: AA-839;
- U-60: AA-861.

**Tầng 4 chưa có issue và chưa cần** (tạo khi trigger cháy, hỏi Nghiệp trước): U-41, U-42, U-43, U-44, U-47, U-48, U-49, U-51, U-52; U-45 (theo AA-813), U-53 (sau U-04), U-54 (theo AA-703), U-58 (AA-821, AA-813).

**Issue đã nằm trong backlog chờ duyệt tạo:** AA-839 (U-32/U-57) và AA-838 (U-38) vẫn là các dòng "Approve creating" trong backlog §4. U-59 cần mở lại AA-824 hoặc tạo một issue XS (có thể gộp với #26).
