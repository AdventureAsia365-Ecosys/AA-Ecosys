> Superseded on 2026-10-19 (S243) by docs/engineering-handbook.md — kept for history.

# Đối chiếu bộ handbook S243 với lộ trình S241, data standards v1.0 và ADR

> S243 · 19/10/2026 · Tác nhân: Claude Code (đọc-only, chỉ ghi file này) · Đối tượng: Nghiệp + agent dựng docs
>
> **Đầu vào:**
> - S243: `README.md` (hướng dẫn SDLC/ADLC), `docs-standard-proposal.md` (catalog 34 mục, I1–I15), `docs-pro-practices.md`.
> - S241: `../2026-10-17-S241-sdlc-review/unified-roadmap.md` (U-01…U-61, D-01…D-25), quyết định thật
>   `docs/sessions/2026-10-17-S241-decisions.md`, log S241/S242.
> - Data standards v1.0 (`docs/architecture/data-standards/01–03`), `docs/database/schema-ownership.md`, ADR 0001–0008 (0003a, 0004a,
>   0004b, 0006a).
> - Backlog sống `docs/backlog/README.md` (S242), Linear (đọc 19/10: AA-844…AA-900, project Data Platform 52 issue chưa lưu trữ).
>
> **Thứ tự ưu tiên khi lệch** (theo `unified-roadmap.md` §1.2): ADR accepted > data standards v1.0 > quyết định đã ghi của Nghiệp
> (D-xx, Q-xx, memory) > đề xuất mới (S243). Riêng các chỗ Nghiệp **đã quyết sửa chuẩn** (vd D-13 "sửa DM-11.5") thì chuẩn
> chỉ còn chờ PR v1.1: S243 được viết theo quyết định, nhưng phải ghi "chờ sửa DM-x" cho tới khi PR merge.
> Yêu cầu mới của Nghiệp 19/10 ("đồng ý hết nội dung artifact S243, làm hết theo lộ trình, ưu tiên 0 phí"; "hướng dẫn chị Thư song
> ngữ Anh–Việt; thêm guide theo vai trò") được tính là quyết định mới, mới hơn D-xx, nhưng **không** tự sửa chuẩn hay ADR.

---

## 0. Tóm tắt

1. S243 khớp phần lớn với S241: không đề xuất tách account prod, không Vercel Pro, không pgaudit Dev, giữ ECS exec S3-mediated.
2. Có **6 chỗ lệch thật với data standards** (MUST/SHOULD): `shared.feature_flag` (DM-1.5), nơi lưu bằng chứng drill/access review
   (DM-8.10, C7.2b, C8a), diễn tập quý trên Dev (DM-9.3), DM-11.5 chưa sửa theo D-13, tag `Env` trùng `Environment` (DM-10.1),
   Cost Explorer gọi thêm ngoài ledger (DM-10.4).
3. Có **6 chỗ lệch với quyết định của Nghiệp:** Dev "có PII thật" (D-01), log "14 ngày" (D-09), eval gate tự chạy theo PR (D-23),
   đổi tên env `prod` sớm (D-16), GitHub Team (D-14), agent role riêng "trước prod" (D-15).
4. Trong nội bộ S243 có 3 file lệch nhau về front-matter, đường dẫn và ngôn ngữ. File `docs-standard-proposal.md` §2.1 phải là bản chuẩn.
5. 14 issue mới AA-887…AA-900: trùng hoặc chồng với U-xx ở **AA-889 (U-09), AA-890 (U-11/U-48), AA-891 (U-47), AA-899 (U-44),
   AA-900 (U-29/U-34)**. Ba issue này phải thu hẹp phạm vi, không làm hai lần.
6. Có 6 U-xx còn mở mà **không có issue**: U-04, U-10(c), U-25, U-61, cùng U-09 và U-11 (giờ có chỗ ở AA-889 và AA-890).
7. Catalog thiếu: **guide theo vai trò** (DevOps, CTO/CIO, PM; chị Thư song ngữ), Dead Table Registry, capacity review, access-review
   record, runbook xoá dữ liệu thủ công (D-11), playbook app mới (ADR 0008), runbook break-glass, checklist prod.
8. Các quyết định S241 đã ra nhưng chuẩn chưa sửa theo: DM-11.5 (D-13), C2.3g/DM-8.4 (D-12), bảng DM-7 + C4.2b (D-09), DM-11.2,
   DM-1.2. Gom vào **một PR data standards v1.1** (AA-889 hoặc root PR).
9. Trang `/admin/docs` (AA-898) phải sync **từ CI checkout theo allowlist**, không sync cả `docs/` (`docs/backups/` có dump thật,
   DM-6.10). Ai được đọc tài liệu bảo mật thì Nghiệp quyết.
10. §5 gồm **18 sửa bắt buộc** cho agent dựng docs và **12 điểm Nghiệp quyết**. Phần lớn 0 USD. Chỗ có tiền thì chỉ là cent/tháng
    (S3 docs, Cost Explorer), riêng eval gate theo PR có thể tới ~30 USD/tháng.

---

## 1. Trạng thái U-01…U-61 (đến 19/10/2026)

Nguồn: log S241/S242, backlog §3–§5, Linear (đọc 19/10). "Quyết định" ghi lựa chọn **Nghiệp đã chốt**. Đây không phải mặc định
trong roadmap. ✅ Done · 🔶 đang làm / một phần · ⬜ mở · ⏸ chờ trigger · ✖ không làm (theo quyết định).

### 1.1 Tầng 1 (Ngay)

| U | Việc | Quyết định | Trạng thái | Issue / bằng chứng |
|---|---|---|---|---|
| U-01 | OIDC chỉ `main` | — | ✅ | AA-866 Done (Infra #169/#170, run 39034825070) |
| U-02 | `ADMIN_SECRET` vào env `dev`, xoay 5 nơi | — | ✅ | S241 (xoay đủ 5 nơi) |
| U-03 | Revoke token GitHub lộ | D-02: **xoay khi lên prod** | ⏸ | backlog §1 "before prod"; gộp checklist prod (AA-880) |
| U-04 | Thu hẹp quyền agent (ask/deny, NotResource, identity) | D-15: **giữ aa365-admin** | ⬜ (bước 4 ✖) | **Không có issue.** `.claude/settings.json` vẫn allow `aws iam *`, `terraform apply`, `gh pr merge` |
| U-05 | Tính năng bảo mật GitHub free, 2FA, ruleset | — | ✅ (còn Dependabot BK/TP) | AA-867 Done; phần còn lại ở **AA-895** |
| U-06 | Kiểm role server cho llm-config/budgets/job-runner | — | ✅ (phần chính) | AA-882 Done (`staff_policy`); `hmac.compare_digest` **[cần kiểm]** |
| U-07 | Sentry CIS, alarm 5xx/p95, uptime | Sentry free 1 monitor: CIS; Booking dựa alarm AWS | ✅ | AA-870 Done |
| U-08 | pip-audit chặn, concurrency, guard fail-closed | — | ✅ | AA-868 Done |
| U-09 | Sửa sự thật trong tài liệu | — | 🔶 | Root PR S241 sửa một phần (bảng enforcement, retention). Còn: DM-11.5 "Enforced by", `ecosystem-architecture.md` §5 OIDC, CLAUDE.md "DO NOT merge", C4.2b, DM-11.2 → **AA-889** |
| U-10 | 3 kiểm tra chỉ đọc | D-01 (a), D-25 (b) | 🔶 | (a) ✅ không có PII thật; (b) ✅ root đã private; (c) trust `OrganizationAccountAccessRole` của TrueIDC ⬜, không có issue |
| U-11 | Dọn nhánh, `delete_branch_on_merge`, squash-only, gỡ `/v1/webhooks` khỏi Playground | — | ⬜ | **AA-890** (thiếu phần Playground `/v1/webhooks`) |

### 1.2 Tầng 2 (Trước tenant trả tiền đầu)

| U | Việc | Quyết định | Trạng thái | Issue |
|---|---|---|---|---|
| U-12 | Tenant pool fail-closed theo wave | D-12: **đảo toàn cục ngay** (khác mặc định A của roadmap) | 🔶 | #792 live; AA-859 In Progress (wave 3–4, D5b) |
| U-13 | Redis AUTH/TLS/at-rest + alarm | D-19 báo giá | ⬜ | AA-874 |
| U-14 | `safe_http` chống SSRF | — | ⬜ | AA-875 |
| U-15 | X2 catalogue CI guard | — | ⬜ | AA-848 |
| U-16 | Isolation probe trong CI | — | 🔶 | `db-isolation-probe.yml` (lịch + sau apply), 39/16/0; chưa chạy theo PR chạm RLS |
| U-17 | Xoay master RDS (nếu D-03 = B) | D-03: **xoay khi prod** | ✖ (tới prod) | backlog §1 |
| U-18 | SG riêng mỗi app + ADR 0004b | D-06: **cùng đợt X1** | ✅ | X1 S10–S14 (ADR 0004b, Infra #180–#190) |
| U-19 | Biên API: rate-limit, WAF/throttle, CORS, header | — | ⬜ | AA-876 |
| U-20 | X10: drill PITR, CNAME DSN, restore 1 schema, dump 16/09 | D-10: **làm ngay** | 🔶 | Drill ✅ (~22 phút); CNAME, runbook 1 schema, dump ⬜ → AA-829 (Backlog) |
| U-21 | ECR immutable, rollback, incident page, hạn snapshot | D-09 + AA-869 (30 ngày) | ✅ | AA-869 Done |
| U-22 | Log phiên ECS Exec + `log_connections` | D-07, D-08 | ✅ | Infra #161 (không có issue riêng) |
| U-23 | Gói pháp lý, /privacy, /terms | — | ⬜ | AA-886; AA-820 (≤11/11, chị Thư) |
| U-24 | Thẻ `pii:` cột Booking/TP | — | ⬜ | AA-877 |
| U-60 | Redact outbox TP + `tripplanner.job` | — | ⬜ | AA-861 |

### 1.3 Tầng 3 (90 ngày)

| U | Việc | Quyết định | Trạng thái | Issue |
|---|---|---|---|---|
| U-25 | GitHub App agent, ADR 0010/0011, ruleset, CODEOWNERS | D-13 (theo rủi ro; dev tự merge), D-14 (Free, app public, root private) | ⬜ | **Không có issue.** AA-891 (release-please) cần GitHub App nên phụ thuộc mục này |
| U-26 | Secrets register, dọn mồ côi, E2E chỉ đọc, access review | — | 🔶 | AA-878 In Progress (4 secret mồ côi: DRY RUN xong, Nghiệp vừa trả lời "nếu đã kiểm kỹ thì ok xoá") |
| U-27 | RBAC staff server + JWT, Cognito Phase 1 | Cognito "làm ngay" | 🔶 | AA-882 ✅; AA-816 In Progress (còn cutover); AA-703 |
| U-28 | CI gate parity + TST-1 replay TP | — | ⬜ | AA-879, AA-849 |
| U-29 | Eval gate có trần chi phí | D-23: **đo bằng vòng audit; golden set ~100 mẫu từ dữ liệu có sẵn** | ⬜ | AA-729 (viết lại); AA-900 chồng phạm vi |
| U-30 | Log JSON + request id, Sentry BK/TP | D-20: OK mail (đã bật) | ⬜ | AA-871 |
| U-31 | GuardDuty, Access Analyzer, BPA, CloudTrail | D-19 | ⬜ | AA-873 |
| U-32 | Script xoá + DSAR | D-11: **chưa làm; làm tay theo runbook nếu có yêu cầu** | ✖ (tới Cognito/khách) | AA-839 parked |
| U-33 | Chuỗi X1 | D-05: **làm ngay** | 🔶 | AA-852 (S1–S14 live), AA-860 In Progress (S15–S23); `owners.yaml` ✅; read-only ops role ⬜ |
| U-34 | ADR 0009 AI platform, ledger v2, AI Use Register | — | ⬜ | AA-804 (later) |
| U-35 | X7 contract hash guard + tooling playbook | — | ⬜ | AA-826 |
| U-36 | X4 tách TripPlanner khỏi bảng CIS | — | ⬜ | AA-712 |
| U-37 | N6 Dead Table Registry + L1 | — | ⬜ | AA-850 |
| U-38 | Review định kỳ (capacity tháng, access quý…) | — | ⬜ | AA-838 (Backlog) |
| U-39 | X5 `shared.countries` | — | ⬜ | AA-851 |
| U-61 | N3 còn lại: `idle_session_timeout` TP, script connection budget | — | ⬜ | **Không có issue** (đề xuất #26 S241 chưa tạo) |

### 1.4 Tầng 4 (chờ trigger)

| U | Trigger | Trạng thái | Issue / ghi chú |
|---|---|---|---|
| U-40 L9 + ADR 0012 | ngày go-live (D-16/D-17: chốt khi có ngày, mặc định acc2) | ⏸ | AA-880 (mở rộng S243: SLO, kênh 2, budget prod, PDF break-glass) |
| U-41 managed master secret | X1 xong | ⏸ | — |
| U-42 luồng Terraform | prod / drift | ⏸ (một phần) | AA-846 (plan sạch); `.bak` → AA-890 |
| U-43 build once, SBOM, provenance | first prod | ⏸ | — |
| U-44 ADR 0013 API, OpenAPI | tenant tích hợp API | **kéo sớm** | AA-899 (S243) |
| U-45 public API key | bán gói API | ⏸ | AA-813 |
| U-46 Idempotency-Key | bật thanh toán | ⏸ | AA-682 |
| U-47 release-please, CHANGELOG, DORA | first prod | **kéo sớm một phần** | AA-891 (release-please + tag); DORA và GitHub Deployments vẫn chờ |
| U-48 org `.github`, template PR | contributor 2 | **kéo sớm một phần** | AA-890 (PR template), AA-887 (template docs) |
| U-49 SLO, burn-rate | first prod | ⏸ | mở rộng AA-880; runbook link cho alarm ở AA-893 |
| U-50 bot copy migration, `required_schema_version` | sự cố deploy trước migration | ⏸ | AA-826 |
| U-51 ECS exec thành break-glass | prod (D-07 = A) | ⏸ | — |
| U-52 pentest | deal enterprise | ⏸ | — |
| U-53 không key tĩnh, devcontainer | sau U-04 | ⏸ | AA-517 tham chiếu |
| U-54 `rollback.yml`, Lambda alias `live` | first prod | ⏸ | AA-703 |
| U-55 trailer AI-Agent, tracing | D-21: job chậm không rõ lý do | ⏸ | AA-842 |
| U-56 diễn tập nâng PG major | 05/2027 | ⏸ | AA-881 |
| U-57 L3 còn lại | ADR 0006 Phase 4 / prod | ⏸ | AA-839 |
| U-58 L10 CRM tenant | AA-821 duyệt | ⏸ | AA-821 (PR-19) |
| U-59 reserved concurrency Lambda TP | quota 1000 | ⏸ | — |

### 1.5 D-01…D-25: S243 có giữ đúng quyết định không

| D | Quyết định của Nghiệp | S243 | Xem |
|---|---|---|---|
| D-01 | Dev không có PII thật | **Lệch** (README §5.1) | K-01 |
| D-02, D-03 | Token GitHub, master RDS: xoay khi prod | Khớp (README §6.5, P7) | K-30 cho phần "xoay theo loại" |
| D-04 | Managed master sau X1 | Không nhắc | — |
| D-05, D-06 | X1 + SG làm ngay | Khớp | — |
| D-07 | ECS exec giữ đường chuẩn + log phiên | Khớp (runbook ECS exec S3-mediated) | — |
| D-08 | `log_connections` ngay, pgaudit khi prod | Không nhắc | — |
| D-09 | Log bảo mật 365 ngày, app 30 ngày | **Lệch** (README §6.1 "14 ngày") | K-02 |
| D-10 | Drill ngay (đã đạt) | Đúng sự thật; thêm nhịp quý trên Dev | K-04 |
| D-11 | Chưa làm xoá/xuất; runbook tay nếu có yêu cầu | Catalog thiếu runbook tay | G-13 |
| D-12 | Tenant pool fail-closed toàn cục | Khớp, nhưng chuẩn C2.3g/DM-8.4 chưa sửa | K-22 |
| D-13 | Merge theo rủi ro; dev: agent tự merge cả PR bảo mật/hạ tầng | Khớp hướng, nhưng §5.7 thêm cổng người; DM-11.5 chưa sửa | K-03 |
| D-14, D-25 | App public, root private, gói Free | §5.7 vẫn để ngỏ GitHub Team | K-10 |
| D-15 | Giữ aa365-admin | **Lệch** (README §6.5 "agent role ít quyền trước prod") | K-11 |
| D-16, D-17 | Prod: chốt khi có ngày go-live, mặc định acc2 | §4.7 đổi tên env `prod` sớm | K-09, K-21 |
| D-18 | Vercel Hobby tới tenant trả tiền | Khớp (loại Starlight trên Vercel Pro) | — |
| D-19 | Duyệt chi tiêu từng mục, báo giá trước | Khớp (ghi giá) | K-14, K-15 |
| D-20 | Alarm gửi cả OK | Khớp | — |
| D-21 | Tracing chỉ khi job chậm | Khớp (Later) | — |
| D-22 | Backlog cập nhật tay | Khớp | — |
| D-23 | Golden set ~100 mẫu, đo bằng vòng audit | **Lệch** (eval gate tự chạy theo PR) | K-08 |
| D-24 | Hỏi trước khi tạo issue; tránh CIS Core | Proposal ghi "CIS Core", thực tế tạo ở Data Platform | K-20 |

---

## 2. Mâu thuẫn (CONFLICTS)

Cột "Thắng" theo thứ tự ưu tiên ở đầu file. Cột "Sửa" nói rõ đây là sửa file S243 (agent làm được) hay sửa chuẩn/ADR (cần Nghiệp).

### 2.1 Với data standards và ADR

| # | Chỗ trong S243 | S243 nói | Ngược với | Thắng | Sửa |
|---|---|---|---|---|---|
| K-03 | README §3.3 (root CLAUDE.md), §5.7; pro §5.1, §5.9 | Dev: agent tự merge (đúng D-13). §5.7 thêm: thay đổi rủi ro **bắt buộc** "kiro-reviewer hoặc review của Nghiệp" | **DM-11.5 (MUST)** vẫn ghi "Agents MUST NOT merge", enforced by "Branch protection" (sai sự thật). Phần bổ sung D-13: dev phase **không** có cổng người, kể cả PR bảo mật/hạ tầng | Nội dung: D-13, vì Nghiệp đã quyết sửa DM-11.5. Văn bản chuẩn vẫn đứng cho tới khi PR v1.1 merge | (1) **Chuẩn v1.1 (Nghiệp duyệt câu chữ):** DM-11.5 = "Dev: agent merge sau CI xanh. Từ prod / tenant trả tiền đầu: Nghiệp duyệt PR Terraform/IAM, migration, auth/bảo mật, xoá dữ liệu"; cột enforcement = "hook subagent; review". Sửa cùng PR: `.claude/CLAUDE.md` "DO NOT merge", steering, bảng "Who approves what" (Part B §11, cột "PR reviewer (human merge)"). (2) **S243 §5.7:** đổi thành "rủi ro cao → `kiro-reviewer` (agent) theo `kiro-delegate`; review của Nghiệp chỉ bắt buộc từ prod/tenant trả tiền đầu (D-13)" |
| K-04 | README §6.4 ("nhịp diễn tập theo quý"), proposal OPS-02/03, §2.4, §2.7; pro §5.8 | Diễn tập rollback và restore **mỗi quý**, ngay từ bây giờ | **DM-9.3:** "once now (X10), then before prod and quarterly **in prod**". C7.2b: quý ở prod. Memory `dev-no-waiting` | DM-9.3 | **S243:** "Dev: drill lại khi quy trình restore/rollback đổi và một lần trước prod; theo quý **từ prod**". Bỏ quy tắc "`last_tested` > 180 ngày cảnh báo" cho runbook restore trên Dev, hoặc để ở mức cảnh báo, không bắt chạy. Diễn tập quý trên Dev (~< 1 USD/lần) chỉ làm nếu Nghiệp sửa DM-9.3 (N-2) |
| K-05 | Proposal OPS-03 (`docs/ops/drills/`; AA-829 "Done-when đổi từ docs/audits sang docs/ops/drills"), SEC-04 / AA-878 ext ("access-review log ở `docs/security/`"), FIN-02 `docs/ops/cost/`; pro `docs/cost/reports/` | Bằng chứng drill, access review và chi phí tháng nằm trong `docs/ops/`, `docs/security/` | **DM-8.10:** kết quả access review ở `docs/audits/<date>-S<nnn>-access-review/`. **C7.2b:** drill record ở `docs/audits/`. **C8a:** capacity review ở `docs/audits/<date>-S<nnn>-capacity-review/`. Memory `save-audits-locally` | Chuẩn | **S243:** bằng chứng (output, JSON, ảnh) vẫn ở `docs/audits/<date>-S<nnn>-<slug>/`. `docs/ops/drills/README.md` và `docs/security/README.md` chỉ là **index link**. Bỏ câu đổi Done-when của AA-829. Báo cáo chi phí tháng (FIN-02) **gộp** với capacity review C8 (C8b mục 9 đã có dòng chi phí RDS) và lưu cùng chỗ. Muốn dời thì sửa DM-8.10/C7.2b/C8a (N-10) |
| K-06 | README §5.2 | Bảng `shared.feature_flag(key, owner_app, …)` | **DM-1.5 (MUST):** `shared` chỉ dành cho kernel (tenants, destinations, countries, LLM gateway, `schema_versions`). Bảng mới không thuộc kernel thì vào schema của chủ. Schema mới = quyết định ADR 0008 | DM-1.5 | **S243:** register là tài liệu `docs/ops/feature-flags.md` (0 USD, đủ cho giai đoạn này). Nếu cần bảng: CIS dùng schema của CIS (vd `acp_shared`), mỗi app dùng schema riêng của mình. Cờ dùng chung cho nhiều app thì cần ADR. Cờ tenant pool (`aa544:*`) là **control bảo mật** (C2.3g, DM-8.4, D-12): xếp loại `permission/security`, không có `remove_by`, vẫn ở Redis |
| K-07 | README §4.9, §5.5; proposal I15 → **AA-900** | Thêm cột `prompt_version` (nullable) vào `shared.llm_call_log` ngay | Chuẩn **cho phép** về schema (DM-1.5: ledger gateway nằm trong kernel). Nhưng ledger v2 (`app`, `is_shadow`) thuộc ADR 0009/AA-804, và backlog §4 ghi "Approve the ledger v2 migration" là việc Nghiệp chờ duyệt. Phải theo D8 (DM-11.2, MIG-4) | Quy trình AA-804 | **AA-900:** cột `prompt_version` đi **trong** migration ledger v2 của AA-804 (một lần expand), hoặc Nghiệp duyệt tách riêng (N-5). Migration-only PR → copy Infra → DB Migrate. Regenerate reference. Không cần dòng retention mới (cùng bảng, 180 ngày) |
| K-12 | README §6.6, P12; AA-880 ext | Thêm tag `Env` (dev/prod) qua `default_tags` | **DM-10.1:** key tag đã là `Environment` (cạnh `Project` / `ManagedBy`). Code: `versions.tf:45,62` `Environment = var.environment` trong `default_tags` | DM-10.1 | **S243:** "dùng tag `Environment` đã có; Nghiệp kích hoạt nó làm cost allocation tag trong Billing (thao tác tay, 0 USD)". Không thêm key mới |
| K-13 | Proposal FIN-01, I11 → **AA-896** | "Quy tắc chi tiêu chỉ nằm trong memory Claude" → viết vào `docs/ops/finops.md` | Quy tắc đã có trong **DM-10.1–10.7** (tag, budget, ledger, subset, duyệt chi tiêu) và steering "Script gọi LLM chạy tay — PHẢI ghi cost" | DM-10 (single source) | **S243/AA-896:** `finops.md` chỉ link DM-10 rồi thêm phần quy trình (review tháng, unit cost, anomaly). Rule mới (vd "báo giá trước dịch vụ mới") thì sửa DM-10.7 trong PR v1.1, không chép |
| K-14 | Proposal I11 → **AA-896** | Script mới gọi Cost Explorer API (0,01 USD/request) để làm báo cáo tháng | **DM-10.4:** mọi lệnh gọi trả phí đi qua seam và ghi ledger. CIS đã có `shared/aws_client/cost_explorer.py` (AA-623) và bảng `shared.cost_explorer_snapshot` (~1.428 dòng, chụp hằng ngày theo account + service) | DM-10.4 + tái dùng | **AA-896:** đọc `shared.cost_explorer_snapshot` (và `llm_call_log` cho LLM). Tag `App` lấy bằng cách mở rộng client có sẵn (thêm group-by tag), không viết script gọi CE riêng. Cost Anomaly Detection (0 USD) giữ nguyên |
| K-15 | Proposal §3.2, I13 → **AA-898** | CI `s3 sync` `docs/*` của root/INF lên bucket private; mọi `admin` đọc được; `audience` không phải cơ chế phân quyền | **DM-6.10:** dump dữ liệu thật không được nằm trong cây repo (root có `docs/backups/`, đã gitignore nhưng vẫn ở laptop). D-25: "báo cáo bảo mật chỉ ở repo private". Q2: chỉ owner đổi quyền. DM-10.1: bucket mới phải có tag `App`. D-19: báo giá | DM-6.10 + D-25 | **AA-898:** sync **từ CI checkout** (chỉ file đã track trong git, không bao giờ từ laptop), theo **allowlist** = các mục trong catalog. Mặc định loại `docs/security/**`, `docs/audits/**`, `docs/sessions/**`, `docs/backups/**`, `docs/calib/**`. Nếu muốn hiện thì backend chặn theo role `owner` (N-3). Bucket có `App=cis`, SSE, chặn public; ghi giá ~0,01 USD/tháng vào PR |
| K-16 | README §3.4 mục 7, N5; proposal I3 → **AA-889** | Bỏ ignore `docs/` của CIS, track mọi `.md` sau khi rà | **DM-6.10:** repo public không được chứa secret hay dữ liệu. CIS là repo **public** (D-14). D-25: báo cáo bảo mật chỉ ở repo private | DM-6.10 | **AA-889 Done-when** thêm: gitleaks + regex ID (account, ARN, SG) xanh trên mọi file sắp add. Các file investigations/audits có chi tiết hạ tầng hoặc bảo mật chuyển sang root private, không add vào CIS. Danh sách file add cần Nghiệp xem một lượt |
| K-17 | README §3.3; pro §5.7 | "Coi `owners.yaml` là gốc, md chỉ diễn giải" | Không ngược: **DM-1.2** đã quy định `owners.yaml` là registry duy nhất "khi nó tồn tại". Từ X1 S1 (Infra #163) nó đã tồn tại. Chỗ lệch là phần chữ: DM-1.2 còn ghi "to build", và `schema-ownership.md` vẫn tự nhận là trang xác định owner | DM-1.2 | **Chuẩn v1.1 (sửa sự thật):** DM-1.2 → Exists. `schema-ownership.md` thêm dòng "registry = `owners.yaml`; trang này diễn giải". Làm trong AA-889 |
| K-18 | README §3.4 (bảng trigger: "migration → db-schema-dump.yml tự mở PR"); proposal APP-04 | Schema reference sinh tự động | **DM-11.2** còn ghi "regenerate the schema reference (manual today; D8 step 5 via N1)". Steering `db-schema.md` còn hướng dẫn chạy script `.tmp-session/s209_*` | S243 đúng sự thật (N1 đã xong) | **Chuẩn v1.1 (sửa sự thật):** DM-11.2 = "regenerated by `db-schema-dump.yml` (nightly + sau migrate)". Steering sửa trong **AA-889** |
| K-22 | README §5.2 (nhắc "cờ tenant pool fail-closed (D-12, #792)") | Coi đây là hiện trạng | **C2.3g** và **DM-8.4** vẫn tả "flag off → main pool là ngoại lệ canary". D-12 đã đảo toàn cục, đang chạy live (unreadable flag = tenant pool; `"false"` = admin pool; env khẩn `TENANT_POOL_FORCE_ADMIN_FLAGS`) | D-12 (Nghiệp quyết đảo; roadmap §5 dặn sửa C2.3g khi đổi) | **Chuẩn v1.1:** C2.3g + DM-8.4 + Part A §9 ghi cơ chế mới và đường lùi (cờ `"false"` từng route, env khẩn). Runbook cờ ghi vào `docs/ops/feature-flags.md` (AA-892) |
| K-02b | — | — | **Bảng DM-7** chỉ có dòng `postgresql` 365 ngày. AA-872/D-09 còn áp: flow log, WAF, ECS exec 365 ngày, log app 30 ngày. **C4.2b** vẫn ghi "14-day retention" | D-09 (đã duyệt) | **Chuẩn v1.1:** thêm các dòng log vào bảng DM-7, sửa C4.2b = 365. Không cần quyết lại vì D-09 đã duyệt |

### 2.2 Với quyết định của Nghiệp (D-xx, Q-xx, memory)

| # | Chỗ trong S243 | S243 nói | Ngược với | Thắng | Sửa (file S243) |
|---|---|---|---|---|---|
| K-01 | README §5.1, dòng Dev | "Đang chứa **PII thật** của tenant/khách (S241), thực chất là 'prod mềm'" | **D-01** (đếm chính xác 17/10: `booking.customers` 8, `tripplanner.customers` 6, 100% email test/nội bộ) | D-01 | "Dev chỉ có dữ liệu test (D-01, đếm 17/10). C7.1a cấm đưa PII prod về Dev" |
| K-02 | README §6.1, dòng Logs | "CloudWatch text, giữ **14 ngày** (flow log 7)" | **D-09 / AA-872** (Infra #168): log bảo mật (flow, WAF, ECS exec, postgresql) **365 ngày**, log app **30 ngày** | D-09 | Sửa số liệu theo AA-872. Phần bảng DM-7 xem K-02b |
| K-08 | README P3, §4.9, §5.5; proposal I15 → **AA-900** | `eval-regression.yml` **chạy trên mọi PR** đụng prompt/LLM; DoD bắt có run ID eval | **D-23:** "đo bằng các vòng audit như hiện tại", golden set ~100 mẫu (AA-729). Roadmap U-29 ghi job theo PR là chi tiêu định kỳ mới (~30 USD/tháng), cần duyệt theo DM-10.7/D-19. DM-10.6 (subset) | D-23 + DM-10.7 | **AA-900:** mặc định chạy eval **bằng tay/dispatch** trên golden set của AA-729. Run ID ghi vào PR khi đổi prompt/model/route. Gọi qua `LLMClient`, `stage=adhoc_aa900`, có trần. Chỉ bật trigger theo PR khi Nghiệp duyệt chi tiêu định kỳ có báo giá (N-4) |
| K-09 | README §4.7 | Đổi tên GitHub environment `prod` → `dev-apply` (vì nó apply state dev) | **D-16/D-17:** layout và cổng prod chốt khi có ngày go-live, trong ADR 0012 (U-40/AA-880). **C7.2c/C7.2d** dùng tên env `prod` cho cổng duyệt | D-16 + C7.2d | Chuyển việc đổi tên vào **AA-880** (ADR 0012). README ghi "hiện env tên `prod` nhưng apply Dev; đổi trong ADR 0012" |
| K-10 | README §5.7 (a), P8 | Phương án GitHub Team (~4 USD/người) để có ruleset/required checks trên repo private | **D-14/D-25:** gói Free, 3 app public, root + Infra private. Chi phí 0 là tiêu chí. Roadmap ghi Team ~8 USD (giá không khớp, **[cần kiểm]**) | D-14 | Ghi (b) là **quyết định hiện hành**: bù bằng `if: ref == main` + OIDC `refs/heads/main` (AA-866). Team chỉ xem lại theo trigger của U-25 (contributor thứ 2 / prod) |
| K-11 | README §6.5 dòng "Trước prod", P7 | "Agent dùng role riêng ít quyền" là việc trước prod | **D-15:** giữ `aa365-admin`. **DM-8.7 (MUST)** ghi cứng `--profile aa365-admin`. U-53 là trigger "sau U-04, trong 6 tháng" | D-15 + DM-8.7 | Bỏ khỏi danh sách "trước prod". Ghi "U-04/U-53, chờ Nghiệp mở lại D-15 (N-8)". Phần thu hẹp `ask/deny` không cần sửa chuẩn thì ghi là việc mở **không có issue** (U-04) |
| K-20 | Proposal §4.1 | Mọi issue vào project `CIS Core` | **D-24:** tránh CIS Core (95/100). Thực tế 13 issue nằm ở Data Platform (52/100 chưa lưu trữ), AA-898 ở CIS Portal | D-24 + thực tế | Sửa §4.1 theo project thật |
| K-21 | README §5.1, dòng Prod | "Trên acc2, không tách account — `~/.claude/CLAUDE.md`" | Đúng nội dung nhưng sai nguồn: nguồn là **ADR 0001 (S235), C7.2a, D-17** (mặc định acc2, chốt khi có ngày go-live; AA-864 đang nghiên cứu) | ADR 0001 | Trích ADR 0001 / C7.2a / D-17, nhắc AA-864 |
| K-24 | README §4.5, P2; proposal I14 → **AA-899** | OpenAPI + oasdiff [CẦN NGAY trước prod]; chốt `/booking/v1/...` | **U-44** trigger "tenant đầu tích hợp bằng API", cần **ADR 0013** (dẫn CON-3–5). CON-9 mới là đề xuất | Nghiệp đã duyệt S243 → kéo sớm hợp lệ | **AA-899:** phần export + oasdiff làm được ngay (0 USD). Đổi prefix `/booking/v1` chạm Booking + FE + TP nên cần ADR 0013 ở root (DM-11.1) trước. Ghi U-44 "kéo sớm (S243)" ở backlog |
| K-25 | README §4.2, N2 → **AA-891** | release-please dùng token GitHub App hoặc PAT; release PR không có `Refs AA-xxx` | U-47 trigger "first prod" (Nghiệp đã duyệt kéo sớm qua S243). GitHub App cho agent là **U-25** (chưa có issue). PAT mới = secret mới (U-26/AA-878). Quy tắc commit toàn cục bắt có `Refs` | Nghiệp đã duyệt S243 | **AA-891:** ưu tiên GitHub App (0 USD) tạo trong U-25, hoặc ghi rõ phương án PAT fine-grained vào secrets register AA-878. Ghi ngoại lệ release PR vào `aa-ship` §1. Nghiệp sửa tay `~/.claude/CLAUDE.md` (N-6) |
| K-26 | Proposal §0, I9 | AA-697 "đang Backlog, không parked"; mở rộng thêm network page + access matrix | Backlog §4: AA-697 **parked**, "Needs Nghiệp: Park" | Backlog (chờ Nghiệp) | Nghiệp xác nhận bỏ park trước khi comment mở rộng (N-9) |
| K-27 | Proposal §2.8, GUIDE-04 | Hướng dẫn cho chị Thư chỉ viết tiếng Việt | **Yêu cầu 19/10:** hướng dẫn chị Thư **song ngữ Anh–Việt** + guide theo vai trò. `language-convention.md` chỉ miễn session log + memory | Yêu cầu mới của Nghiệp | GUIDE-04 song ngữ (EN + VI cạnh nhau hoặc hai cột). Thêm guide vai trò (G-01…G-03). Sửa `language-convention.md` (Nghiệp duyệt, N-7) |
| K-30 | Proposal SEC-02, AA-878 ext ("xoay theo loại secret", "rotation procedures per class") | Quy trình xoay theo loại secret | **D-02/D-03:** xoay khi lên prod. **DM-8.9:** master xoay sau khi dùng (prod). Chu kỳ 90 ngày (§5.4 review) **không** được chọn (D-03 = A). DM-8.11 vẫn chỉ là đề xuất | D-03 + DM-8.9 | Runbook xoay chỉ gồm: khi nghi lộ, khi lên prod, sau khi dùng break-glass. Không đặt chu kỳ 90 ngày trên Dev. "Rà tháng" chỉ là kiểm drift register |

### 2.3 Lệch nội bộ giữa 3 file S243 (sửa trước khi dựng docs)

| # | Điểm | README | docs-standard-proposal | docs-pro-practices | Chốt |
|---|---|---|---|---|---|
| K-29a | Key front-matter | `last-reviewed` (gạch nối) | `last_reviewed` (gạch dưới), 6 trường bắt buộc | `last-reviewed`, `review-every: 90d`, bắt `description` | **Proposal §2.1** là chuẩn (nó tự nói thay README). Pro §3.1 sửa theo, thêm `description` làm trường **tuỳ chọn khuyến nghị** |
| K-29b | Giá trị `status` | — | draft/active/deprecated/superseded | draft/stable/deprecated/archived | Theo proposal, thêm `archived` |
| K-29c | Giá trị `audience` | — | owner/staff/engineer/agent | engineer/agent/business | Theo proposal: `owner` = chị Thư. Thêm vai trò mới (G-01…G-03) |
| K-29d | Thư mục template | — | `docs/templates/` | `docs/_templates/` | `docs/templates/` |
| K-29e | Chi phí | — | `docs/ops/finops.md`, `docs/ops/cost/YYYY-MM.md` | `docs/cost/finops.md`, `docs/cost/reports/` | `docs/ops/finops.md`. Bằng chứng tháng theo K-05 |
| K-29f | Onboarding + account map | — | `docs/onboarding.md` (bảng account map duy nhất) | `docs/get-started/README.md`, `docs/reference/aws-accounts.md` | `docs/onboarding.md` (GUIDE-01) |
| K-29g | Cửa chị Thư | — | Google Drive, sau đó `/admin/docs` | `docs/business/` trong root | Nguồn: `docs/business/` (root private, có front-matter `audience: owner`). Drive chỉ là bản xuất PDF |
| K-28 | MkDocs Material | "maintenance mode từ 11/2025" | "maintenance mode từ 11/2025" | "EOL 05/05/2027" | Thống nhất một câu **[cần kiểm]** (không ảnh hưởng quyết định: không chọn MkDocs) |

---

## 3. Trùng lặp (DUPLICATES): AA-887…AA-900 → U-xx

| Issue (S243) | Ánh xạ U-xx / issue có sẵn | Quan hệ | Việc phải làm để không làm hai lần |
|---|---|---|---|
| AA-887 Docs standard | U-48 (template, một phần); DM-11.1 | mới (mở rộng) | Template PR nằm ở AA-890, AA-887 chỉ giữ template docs. Catalog thêm các dòng ở §4 |
| AA-888 Docs lint + ADR index | U-09 (lint trạng thái ADR); U-05 / Infra `secret-scan.yml` (gitleaks) | mới, chồng nhẹ | gitleaks docs: dùng lại cấu hình gitleaks của Infra. Root private không có GitHub secret scanning nên job này cần thật |
| **AA-889** Stale docs + agent drift | **U-09** (sửa sự thật, không có issue) | **trùng** | AA-889 **nhận toàn bộ phần U-09 còn lại**: DM-11.5 cột enforcement, `ecosystem-architecture.md` §5 OIDC, CLAUDE.md (merge, ACP, Booking), C4.2b, DM-11.2, DM-1.2. Đóng U-09 bằng AA-889 |
| **AA-890** PR template, squash-only, `.bak` | **U-11** (squash, dọn nhánh, `delete_branch_on_merge`); U-48 (PR template); U-42 (`.bak`) | **trùng** | Thêm vào AA-890 phần còn lại của U-11: gỡ `/v1/webhooks` khỏi Playground |
| **AA-891** Release traceability | **U-47** (release-please, CHANGELOG); AA-884 (Apps page đọc version) | **trùng một phần (kéo sớm)** | U-47 còn lại: GitHub Deployments + DORA (trigger prod). Token: U-25 hoặc AA-878 (K-25) |
| AA-892 Ops runbooks | U-21 (AA-869 Done: rollback CIS/Vercel); U-20 (AA-829: restore); D-11 (runbook tay) | mở rộng | Restore runbook **ở AA-829**, không làm lại trong AA-892. AA-892 tách rollback từ `aa-ship` §5 và thêm playbook, flag register |
| AA-893 Alarm catalog + TF outputs | U-49 (runbook link, một phần); C4.1/C4.1a; AA-697 (network/IAM); AA-846 (plan sạch) | chồng | Bảng network/IAM: chọn **một** chỗ (AA-893 làm bảng sinh, AA-697 làm văn xuôi + sơ đồ) |
| AA-894 Env-config + ERD | N1 (DM-11.2) mở rộng; AA-878 (tên secret) | chồng với AA-878 | Env-config chỉ ghi **tên biến + tên secret được tham chiếu**. Register secret (owner, xoay) chỉ ở AA-878, env-config link sang |
| AA-895 Security baseline + Dependabot BK/TP | U-05 (còn Dependabot BK/TP); U-31/AA-873; AA-879 (Trivy) | chồng | Bảng control chỉ link tới AA-873/874/875/876/879, không gộp việc |
| AA-896 FinOps | DM-10 / X9; **U-38** (AA-838, C8 capacity review có dòng chi phí); memory `infra-cost-audit-nov-2026`; AA-884 / AA-858 (chi phí theo app) | chồng | Gộp báo cáo tháng với C8 (K-05). Dùng `shared.cost_explorer_snapshot` (K-14). Một nguồn số liệu cho AA-884 và AA-858 |
| AA-897 Onboarding + agents index | U-09 (một phần, phần chỉ dẫn agent) | chồng với AA-889 | AA-889 sửa nội dung lỗi thời. AA-897 chỉ làm mục lục + guide (gồm guide vai trò ở §4) |
| AA-898 `/admin/docs` | Q1 (console 2 khu), AA-884, AA-885 | mới | Làm sau AA-885. Ràng buộc K-15 |
| **AA-899** OpenAPI + oasdiff | **U-44** (kéo sớm) | **trùng** | Ghi U-44 = AA-899 (phần export/diff). ADR 0013 + prefix `/booking/v1` vẫn thuộc U-44 |
| **AA-900** LLM ops, prompt version, eval gate | **U-29** (AA-729), **U-34** (AA-804) | **trùng** | AA-900 thu hẹp còn: prompt register, runbook eval, bảng route sinh tự động. Golden set → AA-729. Cột `prompt_version` → AA-804 (K-07). Eval theo PR theo K-08 |
| Mở rộng AA-697 | Không có U (ARCH-01, C4) | — | Chờ Nghiệp bỏ park (K-26) |
| Mở rộng AA-829 | U-20 | đúng | Không đổi Done-when sang `docs/ops/drills` (K-05) |
| Mở rộng AA-878 | U-26 | đúng | Quy trình xoay theo K-30. Access review lưu ở `docs/audits/` (DM-8.10) |
| Mở rộng AA-880 | U-40 (+ U-49 SLO, U-03/U-17 xoay khi prod, D-16 đổi tên env) | đúng | Thêm việc đổi tên env `prod` (K-09). Dùng tag `Environment` (K-12) |
| Mở rộng AA-886 | U-23 (+ U-24/AA-877, U-34) | đúng | — |
| Mở rộng AA-855 | Không có U (UAT, memory `uat-videos-after-tech`) | đúng | Guide chị Thư song ngữ (K-27) |

**U-xx vẫn không có issue** (hỏi Nghiệp có tạo không; D-24): U-04 (quyền agent, phần không cần sửa chuẩn), U-10(c) (trust TrueIDC, Nghiệp
tự chạy `aws iam`), **U-25** (GitHub App + ADR 0010/0011 + CODEOWNERS; AA-891 phụ thuộc), **U-61** (N3 còn lại; đề xuất #26 S241).

---

## 4. Khoảng trống (GAPS): dòng cần thêm vào catalog (`docs-standard-proposal.md` §1.2)

Ba dòng đầu là yêu cầu mới của Nghiệp ngày 19/10. Các dòng còn lại là rule DM-x hoặc C-x, hay U-xx, có hệ quả tài liệu mà catalog 34 mục
chưa có. Mọi dòng: root private, H trừ khi ghi khác.

| ID mới | Tên | Loại | Đích | Đọc | Nguồn (rule / U / quyết định) | Issue |
|---|---|---|---|---|---|---|
| G-01 → GUIDE-05 | DevOps / vận hành mới vào: on-call, alarm → runbook, deploy, rollback, quyền AWS/MFA, deploy-gate, ECS exec | Tut | `docs/guides/ops-onboarding.md` | E (ops) | DM-8.7/8.8, C6.3, `aa-ship`, incident-response | AA-897 |
| G-02 → GUIDE-06 | Brief cho CTO/CIO: kiến trúc C4 L1, danh mục ADR, rủi ro/bảo mật (baseline), DR (RPO/RTO), chi phí, lộ trình U-xx, quyết định đang chờ | Exp | `docs/guides/cto-cio-brief.md` (song ngữ) | Lãnh đạo kỹ thuật | ADR 0001–0008, DM-9.6, DM-10, roadmap S241 | AA-897 |
| G-03 → GUIDE-07 | Hướng dẫn PM: Linear (DoR/DoD, quota 100, không `Fixes`), backlog sống, nhịp phiên 3–5 issue, release note, Jira chị Thư, ma trận "Who approves what" | How | `docs/guides/pm-guide.md` | PM | DM-11.5, Part B §11, skill `aa-linear-issue`, `aa-jira-update` | AA-897 |
| GUIDE-04 (sửa) | Hướng dẫn chị Thư **song ngữ EN–VI** | Tut/How | `docs/business/` + bản xuất PDF lên Drive | T | Yêu cầu 19/10; K-27 | AA-855 + AA-897 |
| G-05 → PLAT-01 | Trạng thái lộ trình nền tảng U-xx (bảng sống) | Ref | Một mục trong `docs/backlog/README.md` (không phải file trong audits) | E A | Roadmap S241 §1.3: backlog ghi mã U và trỏ về | AA-887 |
| G-06 → ARCH-09 | Dead Table Registry | Ref | `docs/architecture/dead-table-registry.md` | E A | DM-3.8, DM-3.9, N6, U-37 | AA-850 |
| G-07 → ARCH-08 (làm rõ) | Bảng retention DM-7 là **registry duy nhất**. `retention-log.md` (SEC-04) chỉ ghi các lần chạy | Ref | `02-data-management.md` §7 | E A | DM-7.1, DM-7.5, DM-1.2 | AA-886 |
| G-08 → SEC-05 | Bản ghi access review theo quý | Rep | `docs/audits/<date>-S<nnn>-access-review/` + index ở `docs/security/README.md` | E | DM-8.10, U-26/U-38 | AA-878, AA-838 |
| G-09 → OPS-08 | Capacity review hằng tháng (gộp báo cáo chi phí) | Rep | `docs/audits/<date>-S<nnn>-capacity-review/` | E T (tóm tắt) | C8a–c, C4.3, U-38 | AA-838 + AA-896 |
| G-10 → APP-08 | Connection budget (bảng C2.2 + check CI) | Ref (G sau này) | `03-scaling.md` C2.2 + script CI | E A | C2.2, C2.3c, U-61 | (chưa có issue) |
| G-11 → ARCH-07 (mở rộng) | Contract registry: producer → consumer → version → hash đã pin | Ref | `docs/contracts/README.md` | E A | DM-3.6, CON-4, TST-6, U-35 | AA-826 |
| G-12 → SEC-04 (làm rõ) | RoPA / sub-processor sinh từ thẻ `pii:` + AI Use Register | Ref | `docs/legal/register.md` | E T | DM-6.1, DM-6.12 (đề xuất), U-24, U-34 | AA-877, AA-886, AA-804 |
| G-13 → OPS-09 | Runbook xử lý tay yêu cầu xoá/xuất dữ liệu khách (trước khi có nút) | How (draft, dry-run) | `docs/ops/runbooks/data-subject-request.md` | E | **D-11** ("làm tay theo runbook nếu có yêu cầu"), DM-6.7 | AA-839 (tách phần runbook, không cần chờ Phase 4) |
| G-14 → OPS-04 (làm rõ) | Bản ghi sự cố: `docs/incidents/` (U-03) và `docs/ops/postmortems/` gộp làm **một** chỗ | Rep | chọn `docs/ops/postmortems/` và đổi tham chiếu U-03 | E | U-03, incident-response | AA-892 |
| G-15 → GUIDE-08 | Playbook thêm app mới (12 bước ADR 0008) | How | `docs/guides/add-a-new-app.md` (pro-practices có, catalog thiếu) | E A | ADR 0008 d2–d3, DM-1.2, U-35 | AA-897 |
| G-16 → OPS-10 | Break-glass: Cognito `breakglass` (TOTP), master RDS (DM-8.9), `TENANT_POOL_FORCE_ADMIN_FLAGS`, `override_busy_jobs` | How | `docs/ops/runbooks/break-glass.md` | E | DM-8.9, DM-11.4, ADR 0006/0006a, D-12 | AA-892 |
| G-17 → PROD-01 (mở rộng) | Checklist sẵn sàng prod: xoay token + master (D-02/D-03), tiền đề U-33/U-20/U-61, D-16/D-17, C7.2a–f, pgaudit (D-08) | Ref | trong ADR 0012 + `docs/ops/README.md` | E | U-40, C7.2e | AA-880 |
| G-18 → APP-09 | Register job kind + kill switch theo owner (`shared.job`, `booking.job`, `tripplanner.job`) | Ref (G sau này) | `docs/ops/job-kinds.md` | E A | ADR 0003a, C6.x, DM-7.2 | AA-892 (bản tay) |
| G-19 → ARCH-08 (mở rộng) | Changelog data standards + danh sách sửa đổi v1.1 đang chờ (§5) | Ref | `data-standards/README.md` "Changing this standard" | E A | README chuẩn, roadmap §5 | AA-889 |
| G-20 → OPS-11 | Runbook isolation probe (aa817 + X1 probe) | How | `docs/ops/runbooks/isolation-probe.md` | E A | TST-4, DM-8.4, U-16 | AA-892 |
| G-21 → SEC-06 | Quy tắc phân loại docs theo repo (public: không ID/ARN/inventory/báo cáo bảo mật) | Ref | `docs/STYLE.md` §"Where a page may live" | E A | DM-6.10, D-14/D-25, proposal §2.3 | AA-887 |

---

## 5. Những điểm phải áp dụng

### 5.1 Sửa BẮT BUỘC cho agent dựng docs

1. **Dev không có PII thật (D-01).** Sửa README §5.1. Mọi guide (chị Thư, CTO/CIO) ghi "Dev = dữ liệu test".
2. **Retention log đúng D-09/AA-872.** Log bảo mật (flow, WAF, ECS exec, postgresql) 365 ngày, log app 30 ngày. Sửa README §6.1. Thêm các dòng
   này vào bảng DM-7 và sửa C4.2b 14 → 365 trong PR chuẩn v1.1.
3. **Merge rights.** Viết theo D-13 nhưng ghi "chờ DM-11.5 v1.1". README §5.7: thay "review của Nghiệp bắt buộc" bằng "`kiro-reviewer`
   khi rủi ro; người duyệt chỉ từ prod/tenant trả tiền đầu". Sửa DM-11.5 (nội dung + cột enforcement), bảng "Who approves what",
   `.claude/CLAUDE.md` "DO NOT merge" và steering **trong cùng một PR** (AA-889).
4. **Không tạo `shared.feature_flag` (DM-1.5).** Dùng `docs/ops/feature-flags.md`. Cờ tenant pool xếp loại control bảo mật, không có
   `remove_by`.
5. **Bằng chứng drill, access review, capacity/cost review ở `docs/audits/<date>-S<nnn>-<slug>/`** (DM-8.10, C7.2b, C8a).
   `docs/ops/drills/` và `docs/security/` chỉ là index. Không đổi Done-when của AA-829.
6. **Nhịp diễn tập theo DM-9.3:** Dev diễn tập khi quy trình đổi và một lần trước prod; theo quý từ prod. Cảnh báo `last_tested` không
   bắt chạy lại trên Dev.
7. **`prompt_version` đi cùng ledger v2 của AA-804** (hoặc chờ Nghiệp duyệt tách riêng), qua D8. AA-900 thu hẹp còn register + runbook +
   bảng route.
8. **Eval gate:** mặc định dispatch/tay trên golden set AA-729 (D-23). Trigger theo PR chỉ bật khi Nghiệp duyệt chi tiêu định kỳ.
   Mọi lần gọi qua `LLMClient` với `stage=adhoc_aa900`.
9. **Không đổi tên env `prod` bây giờ.** Chuyển vào AA-880 / ADR 0012 (D-16, C7.2d).
10. **Dùng tag `Environment` đã có** (DM-10.1), không thêm `Env`. Nghiệp kích hoạt cost allocation tag bằng tay.
11. **FinOps link DM-10, không chép.** Báo cáo tháng đọc `shared.cost_explorer_snapshot` + `llm_call_log` (DM-10.4). Không viết script
    gọi Cost Explorer mới. Gộp với capacity review C8.
12. **`/admin/docs` (AA-898):** sync từ CI checkout theo allowlist catalog. Loại `docs/backups`, `docs/calib`, `docs/audits`,
    `docs/sessions`, `docs/security` (trừ khi chặn theo role owner). Bucket tag `App=cis`, SSE, chặn public, ghi giá trong PR.
13. **CIS bỏ ignore `docs/` (AA-889):** gitleaks + regex ID xanh trước khi add. Báo cáo bảo mật/hạ tầng chuyển sang root private (DM-6.10,
    D-25). Danh sách file add để Nghiệp xem.
14. **Bỏ phương án GitHub Team và "agent role ít quyền trước prod"** khỏi danh sách việc. Ghi chúng là trigger của U-25 / U-53 (D-14, D-15).
15. **Xoay secret theo D-02/D-03/DM-8.9:** khi nghi lộ, khi lên prod, sau break-glass. Không đặt chu kỳ 90 ngày trên Dev.
16. **Thống nhất front-matter theo proposal §2.1** (`last_reviewed`, status gồm thêm `archived`, `audience` gồm owner/staff/engineer/agent
    và các vai trò mới). Đường dẫn `docs/templates/`, `docs/ops/finops.md`, `docs/onboarding.md`, `docs/business/`. Sửa pro-practices
    §3.1, §3.3 và §7.1 cho khớp.
17. **Không làm hai lần:** AA-889 nhận U-09; AA-890 nhận U-11 (thêm gỡ `/v1/webhooks` khỏi Playground); AA-891 = U-47 phần nhẹ;
    AA-899 = U-44 phần export/diff (ADR 0013 trước khi đổi `/booking/v1`); AA-900 không chạm golden set (AA-729) và ledger (AA-804).
    Ghi mã U-xx vào backlog sống.
18. **Thêm catalog G-01…G-21** (§4): guide DevOps, CTO/CIO, PM, chị Thư song ngữ; Dead Table Registry; access/capacity review; runbook
    yêu cầu dữ liệu tay (D-11); break-glass; checklist prod; playbook app mới; job-kind register; isolation probe; quy tắc phân loại docs
    theo repo. Sửa trích dẫn prod account (ADR 0001/C7.2a/D-17) và project Linear thật (Data Platform).

### 5.2 Cần Nghiệp quyết

| # | Câu hỏi | Mặc định nếu chưa quyết | Chi phí |
|---|---|---|---|
| N-1 | Duyệt câu chữ **PR data standards v1.1**: DM-11.5 (D-13), C2.3g + DM-8.4 + Part A §9 (D-12), dòng DM-7 + C4.2b (D-09), DM-11.2 + DM-1.2 (sự thật), schema-ownership "registry = owners.yaml" | Văn bản v1.0 giữ nguyên; S243 ghi "chờ v1.1" | 0 |
| N-2 | Diễn tập restore/rollback theo quý **trên Dev** (sửa DM-9.3)? | Không: theo DM-9.3 | < 1 USD/lần |
| N-3 | Trên `/admin/docs`, ai đọc tài liệu bảo mật/audit: chỉ owner, hay mọi admin (chị Thư là admin)? | Không sync các thư mục đó | 0 |
| N-4 | Bật eval gate tự chạy theo PR đụng prompt (chi tiêu định kỳ)? | Không: chạy tay (D-23) | ≤ 1 USD/lần, tới ~30 USD/tháng |
| N-5 | Cột `prompt_version`: làm riêng ngay hay đi cùng ledger v2 (AA-804)? | Đi cùng AA-804 | 0 |
| N-6 | Tạo issue **U-25** (GitHub App cho agent/release-please, ADR 0010/0011, CODEOWNERS)? Nghiệp tự sửa `~/.claude/CLAUDE.md` (ngoại lệ release PR không có `Refs`, quy tắc merge theo D-13) | AA-891 dùng PAT fine-grained, ghi vào AA-878 | 0 |
| N-7 | Sửa `language-convention.md`: guide chị Thư và guide vai trò viết song ngữ EN–VI; bản tư vấn trong `docs/audits/` cho Nghiệp viết tiếng Việt | Guide viết song ngữ theo yêu cầu 19/10, chờ sửa convention | 0 |
| N-8 | Mở lại D-15 (agent dùng role ít quyền trước prod, sửa DM-8.7)? | Giữ `aa365-admin` | 0 |
| N-9 | Bỏ park AA-697 để nhận mở rộng (network page, access matrix, C4)? | Giữ park; bảng sinh tự động ở AA-893 | 0 |
| N-10 | Dời nơi lưu bằng chứng drill/access review sang `docs/ops/` + `docs/security/` (sửa DM-8.10, C7.2b, C8a)? | Giữ `docs/audits/` | 0 |
| N-11 | Thời điểm đổi prefix `/booking/v1` và viết ADR 0013 (U-44 kéo sớm) | Chỉ export OpenAPI + oasdiff, chưa đổi URL | 0 |
| N-12 | Tạo issue cho **U-04** (ask/deny commit, NotResource e2e secret) và **U-61** (N3 còn lại), hoặc gộp vào AA-878 / AA-879? | Chưa tạo | 0 |

---

*Phương pháp: đọc toàn văn 3 file S243, `unified-roadmap.md`, `S241-decisions.md`, log S241/S242, backlog S242, data standards Part B §1/§6–§11 và
Part C C2.3/C4/C7/C8, `schema-ownership.md`, ADR index + ADR 0008 §11; kiểm chéo Terraform (`versions.tf` default_tags), code CIS
(`shared/aws_client/cost_explorer.py`), `.claude/settings.json`, Linear (đọc-only). Không sửa repo nào ngoài file này, không đổi AWS/Linear.
Chỗ **[cần kiểm]** chưa xác minh trực tiếp.*
