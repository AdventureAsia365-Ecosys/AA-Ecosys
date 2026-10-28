# S255: rà soát tài liệu công ty trên `/admin/docs` (AA-898)

- Ngày: 2026-10-28 (S255). Tác nhân: Claude Code (một nhóm reviewer song song + một integrator).
- Phạm vi: 98 trang mà `/admin/docs` xuất bản từ repo gốc (trang catalog có front-matter + ADR). Nhánh
  `docs/s255-docs-review`, một commit, chưa push.
- Cách làm: mỗi trang đối chiếu với hệ thống thật (code `apps/*` và `infra/AA-CIS-Infra` trên `origin/main`,
  `docs/architecture/db-schema-reference.md`, và các sự thật S255: acc1 đã rời hệ sinh thái (AA-998, LLM chỉ chạy acc3,
  không fallback chéo account), CIS 294 live, Booking bk-032, TripPlanner tp-020, CRM crm-023, portal chạy Fargate
  (`portal.`) với Vercel `aa-cis-portal` là đường rollback tới 03/11, deploy không còn chờ bảng job rảnh (AA-993 G5),
  `/admin/docs` đã live).
- Luật áp dụng: tài liệu công ty gọi theo **vai trò** (tech lead, business owner), không gọi tên người; **thân trang chỉ
  tiếng Anh**, bản tiếng Việt nằm ở file anh em `<tên>.vi.md` (thay luật song ngữ N-7 của S243); link tương đối phải
  mở được; trang sinh tự động không sửa tay, chỉ báo lỗi thời.

## Kết quả tổng

| Verdict | Số trang |
|---|---|
| fixed | 55 |
| ok | 31 |
| needs_owner_decision | 12 |
| **Tổng** | **98** |

Bản dịch tiếng Việt mới (4 file `.vi.md`): `docs/engineering-handbook.vi.md`, `docs/glossary.vi.md`,
`docs/guides/ceo.vi.md`, `docs/legal/readiness-packet.vi.md`.

Phần integrator làm thêm (ngoài 98 trang):

- Schema front-matter (`docs/templates/frontmatter.schema.json`) có thêm `lang` (`en`|`vi`) và `translation_of`
  (đường dẫn trang tiếng Anh); `lang: vi` bắt buộc đi cùng `translation_of` và ngược lại. Mô tả trường đổi tên người
  thành vai trò.
- `tools/docs/docslib.py`: `translation_lang()`, `source_of_translation()`. `tools/docs/check_frontmatter.py`: trang
  `.vi.md` dùng chung `id` với trang tiếng Anh (không tính trùng id), phải có `lang: vi`, `translation_of` đúng trang
  tiếng Anh cạnh nó, và trang đó phải tồn tại với cùng `id`; trang thường không được đặt `translation_of` hay `lang`
  khác `en`. `tools/docs/check_prd_refs.py` không coi `.vi.md` là một PRD thứ hai.
- `tools/docs/build_docs_reader.py` (manifest của Docs sync): luật 8 về bản dịch, mỗi entry có thêm `lang`,
  `translation_of`, `translations`; `counts.translations`. Bản dịch chỉ được xuất bản khi trang tiếng Anh được xuất
  bản, và luôn lấy access tier của trang tiếng Anh. Thêm unit test cho cả hai công cụ.
- `docs/README.md`, `docs/STYLE.md`, `tools/docs/README.md`, `.kiro/steering/language-convention.md`: luật mới
  (tiếng Anh + `.vi.md`, gọi theo vai trò).
- Thay tên người bằng vai trò ở các trang công ty còn lại ngoài 98 trang: `docs/templates/*`, `docs/security/*`
  (kể cả `secrets-register.yaml`, `TBD-Nghiep` đổi thành `TBD-tech-lead`), `docs/legal/tenant-terms-ai-clause-draft.md`,
  `docs/architecture/ecosystem-review-2026-09.md`, `docs/architecture/t-series-audit-and-plan.md`,
  `docs/contracts/README.md`, `docs/AAA/erd-v2/README.md`, `docs/llms.txt`.
- Docs lint chạy như `docs-lint.yml`: unit test 47/47, front-matter 109 trang 0 lỗi, PRD refs 0 lỗi, ADR index 0 lỗi,
  AWS CLI một dòng 0 lỗi, alarm runbook link đủ, resource-ids chỉ cảnh báo (ở archive, security, linear-export),
  markdownlint 0 lỗi. Bundle reader: 102 trang (98 trang tiếng Anh + 4 bản dịch), 11 trang chỉ owner xem.
  Lychee không tải được trên máy (bị chặn tải binary), nên link tương đối được kiểm bằng script offline tương đương:
  0 link hỏng.

## Từng trang

| Trang | Verdict | Ghi chú |
|---|---|---|
| `docs/README.md` | fixed | Catalog: `/admin/docs` đã live, bỏ câu placeholder của AA-897, thêm acc3/AA-998, đổi tên người thành vai trò, luật ngôn ngữ `.vi.md` thay N-7. |
| `docs/STYLE.md` | fixed | Viết lại mục Language (trang tiếng Anh, bản Việt ở `.vi.md` cùng front-matter + `lang`/`translation_of`), sửa bảng public/private (root + Infra đang public, thêm AA-Partner), bỏ acc1, đổi tên người thành vai trò. |
| `docs/adr/0001-ecosystem-target-architecture.md` | fixed | Thêm Update 2026-10-28: acc1 rời hệ sinh thái (AA-998), LLM chỉ acc3; quyết định 8 cho phép bản dịch `.vi.md`. Bỏ account ID, đổi tên người thành vai trò. |
| `docs/adr/0002-only-cis-writes-content.md` | fixed | Dịch câu trích tiếng Việt sang tiếng Anh; Update: hệ quả 1 đã xong (ADR 0007, tp-018 xoá bảng place cũ). |
| `docs/adr/0003-one-durable-job-model.md` | fixed | Dịch câu tiếng Việt trong Status; "Nac" đổi thành "Step" (ghi chú tên cũ); Update: bước 5 xong (AA-735), bước 6 thay bằng 0003a. |
| `docs/adr/0003a-per-owner-job-tables.md` | fixed | Update: template + `owners.yaml` đã có, thêm `crm.job`, deploy không chờ bảng job rảnh từ AA-993 G5, DB Migrate apply vẫn chờ; Booking có deploy gate. |
| `docs/adr/0004-aa-booking-stack-and-bootstrap.md` | fixed | Update: O1 thay bằng Cognito (0006/0006a), worker Booking chạy trong task API, deploy gate, `bk_owner`/`db_migrator`, bk-032, merge queue. Bỏ REST API id. |
| `docs/adr/0004a-supply-content-ownership.md` | fixed | Ghi lỗ hổng "CIS chạy bằng aa_cis_admin" đã đóng 19/10 (X1, AA-860); sửa ý "Google redirect" (staff chỉ đăng nhập bằng mã email). |
| `docs/adr/0004b-per-app-security-groups.md` | fixed | Bỏ SG ID; Update: rollout xong, AA-Partner có group riêng. |
| `docs/adr/0005-pricing-and-supplier-rates.md` | fixed | Update: bảng giá đã có (bk-032) và phần chưa làm (`v_from_prices`, `price.from.v1`, `tax_rules`); "Tết" thành "Lunar New Year". |
| `docs/adr/0005a-b2b-resale-warn-and-vnd.md` | fixed | Sửa tên bảng `b2b_partner` thành `booking.b2b_partners`; ghi `price.from.v1` chưa có. |
| `docs/adr/0006-ecosystem-identity.md` | fixed | Đổi tên người thành vai trò, bỏ account ID. Mâu thuẫn nội bộ có sẵn (xem dưới). |
| `docs/adr/0006a-identity-phase1-amendments.md` | fixed | Bỏ user-pool ID (lệnh tra một dòng), bỏ email cá nhân; Update: Booking Phase 2 một phần, alarm A8, email mời staff, reconcile hằng ngày. |
| `docs/adr/0006b-partner-pool-and-mfa.md` | fixed | Đổi tên người thành vai trò, ngày ISO. |
| `docs/adr/0007-place-pipeline-in-cis.md` | fixed | Ghi tp-018 đã xoá 8 bảng cũ; thêm ghi chú G5 cho deploy gate. |
| `docs/adr/0008-new-app-integration-and-data-platform-rules.md` | fixed | Bỏ câu trích tiếng Việt, đổi tên người, thay account ID bằng link account map. |
| `docs/adr/0008a-crm-separate-app-exceptions.md` | fixed | Đổi tên người; DM-11.4 ghi là luật cũ, đã thu hẹp từ AA-993 G5. |
| `docs/adr/0010-aa-partner-app.md` | fixed | Cutover P2b đã chạy 2026-10-27, portal chạy Fargate, Vercel chỉ còn là đường rollback tới 2026-11-03. |
| `docs/adr/0010a-content-studio-partner-sign-in.md` | needs_owner_decision | Thêm Implementation status (cutover xong). ADR vẫn Proposed dù đã chạy thật. |
| `docs/adr/0011-github-app-identity-and-merge-rights.md` | needs_owner_decision | Ghi trạng thái thật (2 App, `aa-ecosys-ci-bot`, CODEOWNERS 6 repo). Vẫn Proposed; "all five repos" chưa rõ có AA-Partner. |
| `docs/adr/0014-repo-visibility-and-github-plan.md` | needs_owner_decision | Sửa mục "Not yet covered": 6 repo đều có secret-scan, public, bật secret scanning + push protection. Vẫn Proposed. |
| `docs/adr/0015-tour-liveness-and-retirement-propagation.md` | fixed | Đổi tên người; bọc `<date>` vào code để reader không nuốt chữ. |
| `docs/adr/0016-one-design-system-guarded-kit-copies.md` | fixed | Đổi tên người; thêm ghi chú G5 cho guard job-busy. |
| `docs/adr/0017-migrations-in-app-pr-expand-auto-apply.md` | ok | Nội dung đúng; chỉ đổi tên người, ngày, bọc `<object>`. |
| `docs/agents.md` | fixed | Kiểm từng file với git log; thêm hook `kit-core-edit-guard`, dòng AA-Partner; root/Infra public; liệt kê điểm cũ trong file chỉ dẫn agent. |
| `docs/architecture/data-standards/01-engineering.md` | fixed | Thêm AA-Partner, `crm-NNN`, `crm.job`; KEY-6 theo ADR 0008a; MIG-4 tách luật DB Migrate khỏi luật G5. Chưa nâng `last_reviewed`. |
| `docs/architecture/data-standards/02-data-management.md` | fixed | Sửa nhiều chỗ lỗi thời (X1, N1, N3, N4, N6, N7, X10 xong; CRM live); DM-3.3 drift gate vẫn mở. |
| `docs/architecture/data-standards/03-scaling.md` | fixed | Cập nhật Part C; phát hiện `crm-api` chưa đặt `statement_timeout` và chưa role nào có backstop cấp role. |
| `docs/architecture/data-standards/README.md` | fixed | Dịch câu tiếng Việt, đổi tên người, cập nhật bảng enforcement và open item. |
| `docs/architecture/dead-table-registry.md` | fixed | 10 object wave 1 đã quarantine bằng CIS 294; còn thiếu run id apply/verify. |
| `docs/architecture/erd/README.md` | ok | Trang sinh tự động; lệch nhẹ: CIS 292 (live 294), thiếu CRM. |
| `docs/architecture/erd/acp_contract.md` | ok | Sinh tự động; lỗi thời sau CIS 294 (3 bảng đã sang `retired`). |
| `docs/architecture/erd/acp_deliver.md` | ok | Sinh tự động, vẫn đúng. |
| `docs/architecture/erd/acp_shared.md` | ok | Sinh tự động; lỗi thời sau CIS 294 (2 bảng đã sang `retired`). |
| `docs/architecture/erd/booking.md` | ok | Sinh tự động, khớp bk-032. |
| `docs/architecture/erd/catalog.md` | ok | Sinh tự động, CIS 293/294 không đổi catalog. |
| `docs/architecture/erd/crm.md` | ok | Sinh tự động; header thiếu key `crm-023`, owner hiện `crm` thay vì AA-Partner (lỗi generator). |
| `docs/architecture/erd/design/README.md` | fixed | crm đã live (chưa đồng bộ trang thiết kế), thêm dòng tripplanner bị thiếu. |
| `docs/architecture/erd/design/crm.md` | needs_owner_decision | Trang thiết kế lệch: 31 bảng thiết kế chưa live, 16 bảng live chưa có trên trang; cần vẽ lại theo dump và bật enforce. |
| `docs/architecture/erd/design/tripplanner.md` | fixed | Đối chiếu dump tp-020: bảng, khoá, FK khớp; tp-020 chỉ thêm 3 view. |
| `docs/architecture/erd/geo.md` | ok | Sinh tự động; header CIS 292 nhưng nội dung đúng. |
| `docs/architecture/erd/gold_aa_internal.md` | ok | Sinh tự động; chỉ lệch số migration ở header. |
| `docs/architecture/erd/public.md` | ok | Sinh tự động, vẫn đúng. |
| `docs/architecture/erd/shared.md` | needs_owner_decision | Sinh tự động bị cũ: còn vẽ 5 object CIS 294 đã chuyển sang `retired`, thiếu `dfs_call_log.job_id` (CIS 293); cần chạy lại DB Schema Dump. |
| `docs/architecture/erd/silver_aa_internal.md` | ok | Sinh tự động; chỉ lệch số migration ở header. |
| `docs/architecture/erd/tripplanner.md` | ok | Sinh tự động ở tp-020, khớp. |
| `docs/database/schema-ownership.md` | fixed | Bỏ chữ "planned" cho migration đã áp, sửa bk-029 thành bk-030, thêm schema `retired`, sửa luật idle/deploy gate theo G5, đóng mục gaps AA-684. |
| `docs/ecosystem-architecture.md` | fixed | acc1 rời hệ, portal Fargate, TripPlanner bỏ bảng cũ (tp-018), Booking tới bk-032, identity cập nhật, ADR 0015 Accepted, bỏ ID khỏi prose. |
| `docs/engineering-handbook.md` | fixed | Chuyển tóm tắt tiếng Việt sang `engineering-handbook.vi.md` (mới); đổi tên người; luật ngôn ngữ mới, `/admin/docs` live, G5, ngân sách 300 USD, acc1 rời hệ. |
| `docs/generated/alarms.md` | needs_owner_decision | Sinh từ Infra@dc75f51, cũ hơn PR #460–#466; cần chạy lại Docs Gen sau Terraform Apply. |
| `docs/generated/env-config.md` | needs_owner_decision | Vẫn liệt kê biến `BEDROCK_*_FALLBACK` của acc1 mà Infra #466 đã gỡ; cần chạy lại Docs Gen. |
| `docs/generated/iam-roles.md` | needs_owner_decision | Thiếu role `aa-cis-dev-docs-sync`, còn quyền assume sang acc1, câu mở đầu trong template generator còn nhắc acc1. |
| `docs/generated/inventory.md` | needs_owner_decision | Sinh từ Infra@56e36d1, chưa có GuardDuty (#471), CloudTrail KMS (#468), role docs-reader (#465). |
| `docs/generated/network.md` | needs_owner_decision | Cùng nguồn cũ 56e36d1, có thể thiếu thay đổi NAT (#467). |
| `docs/glossary.md` | fixed | acc1 rời hệ, deploy gate G5, số required checks, data standards 1.6; cột tiếng Việt chuyển sang `glossary.vi.md` (mới). |
| `docs/guides/ceo.md` | fixed | Bỏ song ngữ, trang tiếng Anh thuần; bản dịch đầy đủ ở `guides/ceo.vi.md` (mới). |
| `docs/guides/cio.md` | fixed | acc1 rời hệ, Redis/Access Analyzer/BPA xong, GuardDuty đã bật (Infra #471, kiểm live), Sentry Booking/TP, budget 300. |
| `docs/guides/cto.md` | fixed | Sơ đồ C4 (Partner, portal Fargate, pool PARTNER, Bedrock chỉ acc3), danh sách ADR, data standards 1.6, required checks. |
| `docs/guides/devops.md` | fixed | Thêm service CRM và portal Fargate, deploy gate G5, Deploy Portal Dev, 94 alarm, runbook rollback. |
| `docs/guides/new-engineer.md` | fixed | acc3 cho AI, portal Fargate, AA-Partner trong bảng repo/local setup, required checks, merge queue. |
| `docs/guides/pm.md` | fixed | Project Partner CRM, quota Linear Free + export/archive, nhịp phiên, release-please đã chạy. |
| `docs/legal/consent-capture-query.md` | fixed | CHECK `source` của `booking.customers` có thêm `traveller_signin`; ngày dump mới. |
| `docs/legal/dpa-template.md` | fixed | Drill xoá tenant 23/10, Vercel sfo1 + portal trên AWS, Sentry không gửi frame locals, bỏ số dòng code dễ lệch. |
| `docs/legal/dsar-erasure-runbook.md` | needs_owner_decision | Sửa nhiều điểm cũ; cần tech lead quyết: Infra đang public nên PR lookup chứa hash e-mail sẽ lộ việc một người gửi yêu cầu. |
| `docs/legal/readiness-packet.md` | fixed | Tách song ngữ: trang tiếng Anh + `readiness-packet.vi.md` (mới, kể cả Phụ lục A); sửa điểm cũ. |
| `docs/legal/register.md` | needs_owner_decision | `gen_pii_inventory --check` báo 93 cột PII mới chưa có dòng RoPA (CRM, Booking invoices/payments, `shared.tenant_members`, `tripplanner.traveller_accounts`); cần quyết RoPA cho CRM và cơ sở pháp lý. |
| `docs/legal/retention-log.md` | ok | Code khớp; chưa kiểm trong DB có lượt chạy thật nào sau 2026-10-21. |
| `docs/onboarding.md` | fixed | Account map đúng S255; acc3 giữ budget/anomaly alert, tên role Cost Explorer đã kiểm. |
| `docs/ops/README.md` | fixed | Bảng CI/CD sửa theo workflow trên main và required checks đọc qua `gh api`. |
| `docs/ops/cost/README.md` | fixed | Bỏ câu "private root repo" (repo gốc đang public). |
| `docs/ops/database-operations.md` | fixed | Thêm storage autoscaling 100 GB, ngày ISO. |
| `docs/ops/drills/README.md` | ok | Không có drill mới sau 24/10; link mở được. |
| `docs/ops/feature-flags.md` | fixed | Cột Owner đổi thành vai trò; thiếu flag của CRM (báo). |
| `docs/ops/finops.md` | ok | Ngân sách 300 USD và từng app, budget/anomaly acc3 khớp Terraform. |
| `docs/ops/incident-response.md` | ok | Log group khớp Terraform; link mở được. |
| `docs/ops/job-kinds.md` | ok | Bảng kind CIS/Booking/CRM khớp code. |
| `docs/ops/playbooks/5xx-spike.md` | ok | Tên alarm có trong catalog; curl health trả đúng như trang ghi. |
| `docs/ops/playbooks/cognito-login.md` | ok | Pool, alarm, địa chỉ gửi mail khớp Terraform. |
| `docs/ops/playbooks/llm-cost-spike.md` | ok | Ngân sách, ngưỡng anomaly, cột `llm_call_daily`, trần TP khớp; chỉ còn acc3. |
| `docs/ops/playbooks/queue-stuck.md` | ok | Tên 3 alarm, ngưỡng, route ops CRM, G5 khớp. |
| `docs/ops/runbooks/break-glass.md` | ok | Nhóm, alarm, `breakglass-init/verify` khớp Infra. |
| `docs/ops/runbooks/crm-keys.md` | ok | Rule/alarm KMS, workflow diff hằng đêm khớp; role break-glass của CRM đúng là chưa tạo. |
| `docs/ops/runbooks/db-migrate.md` | ok | Mã exit, timeout, `override_busy_jobs`, `password_roles` khớp; vẫn draft dù đã chạy thật. |
| `docs/ops/runbooks/deploy-gate-override.md` | fixed | Một lần apply `data_erasure` bị nhận lại sẽ từ chối và cần DRY RUN + duyệt mới. |
| `docs/ops/runbooks/ecs-exec-s3-mediated.md` | fixed | Tham chiếu "bastion note" thành link thật tới ghi chú đã lưu trữ. |
| `docs/ops/runbooks/isolation-probe.md` | ok | Lịch và key đăng nhập `crm_app` khớp. |
| `docs/ops/runbooks/legacy-login-flag.md` | fixed | Callout `[!IMPORTANT]` đổi thành `[!NOTE]`; còn lệch AA-680 / AA-911 P6b (báo). |
| `docs/ops/runbooks/restore-rds-pitr.md` | fixed | Bước 4 lỗi thời: so sánh bằng run-script (drill S249), đường ECS exec bằng master không còn chạy. |
| `docs/ops/runbooks/restore-schema.md` | ok | Đúng; option A đã diễn tập S249; vẫn draft. |
| `docs/ops/runbooks/rollback-booking.md` | ok | ECR giữ 10 image, gate retention khớp. |
| `docs/ops/runbooks/rollback-cis.md` | ok | ECR giữ 30 image, gate G5 khớp. |
| `docs/ops/runbooks/rollback-terraform.md` | fixed | Khoá state là S3 lockfile (AA-846), acc1-bedrock chỉ chờ destroy, lệnh MFA theo mẫu an toàn. |
| `docs/ops/runbooks/rollback-tp-lambda.md` | fixed | Ghi rõ `post-deploy-verify.yml` fail ngay sau Path B bước 3 cho tới khi revert được deploy. |
| `docs/ops/runbooks/rollback-vercel.md` | fixed | Portal chạy Fargate; `aa-cis-portal` chỉ là đường rollback DNS tới 03/11. |
| `docs/ops/runbooks/secret-rotation.md` | fixed | Bổ sung Cognito client `-preview` và `cis-portal`; tên secret khớp. |
| `docs/ops/runbooks/ses-bounce.md` | fixed | PARTNER pool không gửi mã đăng nhập qua email, chỉ mail xác minh đổi email. |
| `docs/product/README.md` | ok | Quy tắc PRD khớp `check_prd_refs.py` (nay bỏ qua `.vi.md`). |
| `docs/product/partner-crm/prd.md` | ok | Migrations crm 001–023 khớp Infra; link resolve. |

## Cần owner quyết (needs_owner_decision)

1. ADR 0010a, 0011, 0014 còn **Proposed** dù đã chạy thật: tech lead chuyển sang Accepted hay không. ADR 0011: danh
   sách cài App ghi "all five repos" / "5 selected repos" trong khi có 6 repo (AA-Partner).
2. `docs/architecture/erd/design/crm.md`: vẽ lại theo dump live crm-023, bật `enforce=true`, quyết `status` (luật 1:
   draft chỉ tới migration đầu tiên).
3. `docs/legal/register.md`: 93 cột PII mới chưa có dòng RoPA; RoPA cho CRM và cơ sở pháp lý (tech lead + business
   owner, có thể cần luật sư).
4. `docs/legal/dsar-erasure-runbook.md`: Infra đang public, PR lookup chứa hash e-mail sẽ lộ việc có người gửi yêu cầu;
   cần cách chạy lookup khác trong lúc Infra public.
5. Trang sinh tự động cần chạy lại generator (không sửa tay): `docs/architecture/erd/shared.md` (và cả bộ ERD +
   `db-schema-reference.md`): chạy DB Schema Dump `publish=true`, merge PR `bot/db-schema-reference`;
   `docs/generated/alarms.md`, `env-config.md`, `iam-roles.md`, `inventory.md`, `network.md`: chạy AA-CIS-Infra Docs Gen
   sau Terraform Apply của #460–#471. Câu "satellite roles in acc1 / acc3" nằm trong template
   `tools/docs/gen_docs.py` của Infra, phải sửa ở đó.
6. Không thuộc 12 trang nhưng cần quyết: `status: draft` của `db-migrate.md` và `restore-schema.md` dù đã chạy trên
   Dev; luật STYLE "agent không sinh/sửa env var có dấu gạch dưới" mâu thuẫn memory "do hand steps myself".

## Trùng lặp và mâu thuẫn (chỉ báo, chưa sửa)

- ADR 0006 quyết định 4 vẫn ghi Google là cách đăng nhập chính của staff, trong khi Status và 0006a A9 nói chỉ mã email.
- ADR 0007: quyết định 7 ghi "GPT-5.6 Luna", amendment S246 ghi "GPT-6 Luna".
- ADR 0004 quyết định 4/8 còn mô tả service worker Booking riêng và "human merge" (đã có Update chỉ ra).
- ADR 0008a quyết định 5 (CRM gọi Bedrock qua role riêng trên acc3, AA-930): chưa kiểm được trong code AA-Partner sau
  AA-998; owner xác nhận.
- `docs/ops/runbooks/legacy-login-flag.md`: đầu trang ghi Booking còn dùng route cũ "tới AA-680", cuối trang ghi "tới
  AA-911 P6b".
- `docs/architecture/data-standards/README.md` open item 10 (ngoại lệ NAM-14) đã xong ở Part A; CON-8 và §9 còn ghi
  `shared.llm_call_daily` "to build" dù bảng đã có; DM-7 còn liệt kê `crm.outbox` (chưa live).
- `docs/legal/retention-log.md` tóm tắt "chưa có lần xoá tenant nào" trong khi drill xoá tenant đã chạy 23/10 (theo
  readiness packet, DPA). `docs/legal/register.md` trước đây ghi vùng Vercel "not pinned", các trang legal khác ghi sfo1
  từ 28/10.
- `docs/STYLE.md`: "business-facing summaries ... are Vietnamese" (tóm tắt cho business owner trong cost report,
  release note, postmortem) đi ngược luật "thân trang chỉ tiếng Anh"; các template `cost-report.md`, `postmortem.md`,
  `uat-report.md`, `release-note.md` vẫn có khối tiếng Việt, `access-review.md` / `capacity-review.md` còn nhắc N-7.
  Đề xuất: giữ các khối này vì chúng là bản nháp tin nhắn gửi business owner (Jira), không phải trang catalog, và ghi
  rõ ngoại lệ đó trong STYLE.
- `docs/templates/runbook.md` còn luật "shared.job không có job queued/running" cho deploy (cũ trước G5).
- `docs/ops/feature-flags.md` chưa có mục cho CRM (AA-Partner).
- `docs/security/github-apps.md` còn khối "Tóm tắt (VI)" (trang security, không xuất bản lên reader).
- File chỉ dẫn agent (không phải trang catalog, integrator không sửa): `.claude/CLAUDE.md` vẫn ghi acc1 là LLM fallback,
  portal trên Vercel, luật "không merge/deploy khi bảng job còn job" (đã đổi bởi G5); `.kiro/steering/session-workflow.md`
  cùng luật bảng job; `~/.claude/CLAUDE.md` vẫn có acc1. AA-Partner `CONTEXT.md` vẫn ghi portal "Still on Vercel".
- `docs/contracts/inquiry.submitted.v1.1.json` còn tên người trong `description`; không sửa để tránh đổi nội dung một
  contract đã phát hành (hash guard sau này).
- Journal (`docs/implementation-notes/`, `docs/backlog/`, `docs/research/`, `docs/calib/`, `docs/eval/`) giữ tên người
  như khi viết (STYLE mục Voice, điểm 11). Trường front-matter `owner: nghiep` là slug, giữ nguyên; schema ghi rõ slug này
  là vai trò tech lead.

## Trang sinh tự động lỗi thời

| Trang | Lỗi thời | Cách sửa |
|---|---|---|
| `docs/architecture/db-schema-reference.md` | Header CIS 292 (live 294, main đã có 296), thiếu dòng CRM ở "latest migration per owner", chưa có schema `retired` | DB Schema Dump `publish=true`, merge PR bot |
| ERD `acp_contract`, `acp_shared`, `shared` | Còn object CIS 294 đã chuyển sang `retired`; `shared.dfs_call_log` thiếu `job_id` (293); chưa có trang ERD cho `retired` | Cùng lần dump trên |
| ERD `README.md`, `crm.md` | Thiếu key `crm-NNN`, owner hiện `crm` thay vì AA-Partner, `applies_to` sai | Sửa `gen_erd.py` (AA-CIS-Infra) |
| ERD `geo`, `gold_aa_internal`, `silver_aa_internal`, `catalog`, `acp_deliver` | Chỉ header (CIS 292) | Lần dump tới |
| `docs/generated/alarms.md`, `iam-roles.md` | Infra@dc75f51, thiếu #460–#466 | Docs Gen sau Terraform Apply |
| `docs/generated/env-config.md` | Infra@459b94f, còn biến fallback acc1 | Docs Gen sau Apply + deploy |
| `docs/generated/inventory.md`, `network.md` | Infra@56e36d1, thiếu #462–#471 | Docs Gen sau Apply |

## Lỗi hiển thị trên `/admin/docs`

- Mermaid hiện mã nguồn, chưa vẽ sơ đồ (MarkdownView chưa có plugin mermaid).
- Callout kiểu GitHub (`> [!NOTE]`, `> [!WARNING]`) hiện như blockquote thường, còn nguyên chữ `[!NOTE]` (chưa có
  plugin GitHub alert).
- HTML comment (marker generator, markdownlint) bị bỏ nhờ `skipHtml`, không cần sửa trang. Chữ dạng `<date>` /
  `<object>` không bọc code sẽ bị nuốt; các chỗ tìm thấy đã bọc vào code.
- **Chưa có nút EN/VI.** Bundle mới đã có trường cho nút này (dưới đây). Cho tới khi CIS reader dùng các trường đó,
  4 trang `.vi.md` hiện thành 4 dòng riêng trong danh sách (cùng ID với trang tiếng Anh, tiêu đề tiếng Việt), vì API hiện
  bỏ qua trường lạ (`_ENTRY_FIELDS`).

## Trường manifest cho nút EN/VI (CIS reader cần dùng)

Manifest vẫn `format: 1`, `rule: "v1"`; các trường mới là thêm vào, không phá API hiện tại.

- Mỗi entry trong `pages[]`:
  - `lang`: `"en"` (trang gốc) hoặc `"vi"` (bản dịch).
  - `translation_of`: bản dịch thì là `path` của entry tiếng Anh (cùng `repo`); trang tiếng Anh là `null`.
  - `translations`: trang tiếng Anh thì là danh sách `{"lang", "path", "key", "title"}` của các bản dịch đã xuất bản
    (sắp theo `lang`), không có thì `[]`; bản dịch luôn `[]`.
- `counts.translations`: số entry là bản dịch.
- Bản dịch là một entry đầy đủ trong `pages[]` (có `key`, `sha256`, `access`, ...), cùng `id` và cùng `access` với
  trang tiếng Anh, nên `load_page(repo, path)` hiện có đọc được nó mà không đổi gì.

Việc phía CIS (`api/services/docs_reader.py` + trang `/admin/docs`): thêm `lang`, `translation_of`, `translations` vào
`_ENTRY_FIELDS`, kiểm `path`/`key` của từng phần tử `translations` bằng `_PATH` / `_valid_key`, chỉ liệt kê entry có
`lang == "en"` (hoặc `translation_of` null) trong danh sách, và hiện nút EN/VI khi entry có `translations` không rỗng
(hoặc đang mở một bản dịch thì quay về `translation_of`). Mặc định mở tiếng Anh (luật "pages default to English").

## Việc còn lại cho integrator / phiên điều phối

- Các file vendored phải giống hệt ở 4 repo (`tools/docs/README.md`): `docslib.py`, `check_frontmatter.py`,
  `test_docs_tools.py` đã đổi ở đây, và `docs/templates/frontmatter.schema.json` mà các repo app + Infra cũng copy.
  Cần copy sang AA-Booking, AA-TripPlanner-Web, AA-CIS-Infra trong cùng phiên (subagent không sửa repo khác).
- Chạy lychee thật trong CI của PR (máy này không tải được binary).
- PR CIS cho nút EN/VI (mục trên).
