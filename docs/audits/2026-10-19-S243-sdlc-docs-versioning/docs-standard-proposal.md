> Superseded on 2026-10-19 (S243) by docs/engineering-handbook.md — kept for history.

# Đề xuất chuẩn hoá tài liệu hệ thống AA-Ecosys: danh mục, quy chuẩn, nơi lưu, danh sách issue

> S243 · 19/10/2026 · Tác nhân: Claude Code · Đối tượng: Nghiệp
>
> Đi kèm bản hướng dẫn `README.md` cùng thư mục (§3 docs, §7 lộ trình N1–N11, P1–P12). Đầu vào: bộ 21 tài liệu Nghiệp đưa
> (A–E + Database Operations), 2 báo cáo trinh sát đọc-only 19/10 (bản đồ tài liệu hiện có; nơi lưu/hiển thị), `docs/backlog/README.md`.
> Bản này viết tiếng Việt vì là tư vấn cho Nghiệp. Mọi file **mới** nó đề xuất viết **tiếng Anh** (trừ hướng dẫn cho chị Thư, xem §2.8).
> Không có thay đổi nào với repo, AWS, Linear, Notion hay Jira khi viết bản này. Chỗ chưa chắc ghi **[cần kiểm]**.
>
> **Rà soát (critic pass, 19/10):** đã đối chiếu với repo + Linear (đọc-only). Sửa: I16 trùng **AA-880** (đã có issue) → chuyển thành mở rộng;
> AA-697 đang Backlog (không phải parked); rollback CIS/Vercel đã có ở `aa-ship` §5 (AA-869 Done); access review đầu tiên thuộc AA-878;
> SEC-04 khớp phạm vi AA-886; giá Password Protection Vercel; root repo **chưa có workflow nào** và không có role AWS OIDC → generator đọc AWS
> chạy ở INF; title/project Linear theo `skill/aa-linear-issue`; thêm mục ARCH-08 (data standards + schema ownership) bị sót; thêm §4.5 cắt gọn
> cho 1 kỹ sư + agent.

---

## 0. Trả lời ngắn

- **Bộ 21 tài liệu dùng được làm khung**, khoảng 70% trùng với thứ hệ mình cần. Nhưng đừng làm thành 21 file viết tay "có resource ID thật":
  ID chép tay sẽ lỗi thời. `CIS_Runbook_v1.md` là bằng chứng: nó vẫn trỏ acc1, dùng AWS CLI nhiều dòng và mô tả pipeline đã gỡ.
- **Giữ 13 chủ đề, gộp/đổi hình 8, thêm 13 chủ đề còn thiếu**, ra một **danh mục chuẩn 34 mục** (§1.2). Trong đó khoảng **11 mục đã có**
  (chỉ cần front-matter/index), khoảng **9 mục sinh tự động bằng CI** (toàn bộ hoặc phần bảng), khoảng **16 mục phải viết tay mới** (vài mục thuộc 2 nhóm).
- **Không làm hết 34 mục cùng lúc.** Với 1 kỹ sư + agent, làm bản tối thiểu trước (§4.5): chuẩn + lint, dọn rác, ops index + rollback,
  bảng alarm có runbook link, FinOps + báo cáo tháng. Phần sinh tự động còn lại chỉ làm khi bảng tay bắt đầu sai.
- **"Tested"** = runbook có `last_tested` + `tested_where` + link bằng chứng. **"Resource ID thật"** = lấy từ Terraform output hoặc
  bảng sinh tự động, không chép vào văn xuôi (§2.3–§2.4).
- **Nơi lưu: git là nguồn duy nhất** (repo private cho thứ nhạy cảm). **Trang Docs trong admin CIS: nên làm**, nhưng làm **sau**
  khi chuẩn hoá xong nội dung và sau AA-885. Trang này chỉ là chỗ *đọc* (render từ S3, ~0,01 USD/tháng), không phải chỗ *viết* (§3).
- **14 issue mới + mở rộng phạm vi 6 issue có sẵn** (AA-697, AA-829, AA-878, AA-880, AA-886, AA-855). 11 issue mới làm Now, 3 làm Before prod (§4).

---

## 1. Bộ 21 tài liệu — giữ, gộp, bỏ, thêm

### 1.1 Nhận định từng mục

| Mục của Nghiệp | Kết luận | Lý do / đổi thành |
|---|---|---|
| A1 Architecture | **Giữ** | Đã có `docs/ecosystem-architecture.md` (tốt). Thiếu C4 L1–L2 → ARCH-01 |
| A2 Network/VPC | **Giữ, tách 2 lớp** | Văn xuôi + sơ đồ viết tay; bảng SG/subnet **sinh** từ Terraform → ARCH-02 |
| A3 Compute/Data | **Đổi hình** | Thành *service catalog + inventory* sinh tự động (theo tag `App`) + trang Apps của AA-884 → ARCH-03 |
| A4 IAM/Access Control | **Giữ, mở rộng** | Không chỉ AWS IAM: cả người, CI, agent, GitHub/Vercel/Linear/MCP + log access review → ARCH-04 |
| B1 Deployment | **Giữ, gộp** | Nội dung có rồi (skill `aa-ship` + README) → 1 index + 1 trang/app → APP-01 |
| B2 CI/CD Pipeline | **Giữ, sinh tự động** | Parse `.github/workflows/*.yml` + branch protection → APP-02 |
| B3 Environment Config | **Giữ, sinh tự động, chỉ tên** | Nguồn thật là **task def đang chạy** (deploy clone live task def), không phải `.tf` → APP-03 |
| B4 Database Schema | **Giữ (đã xong)** | Đã sinh bởi `db-schema-dump.yml` (workflow ở INF, mở PR vào root); thêm ERD → APP-04. Quy tắc dữ liệu (`data-standards/`, `schema-ownership.md`) → ARCH-08 |
| C1 PROD Runbook | **Đổi hình** | Chưa có prod → *Operations index* cho Dev + mục prod để dành cho go-live → OPS-01 (+ PROD-01 trước prod) |
| C2 Rollback | **Giữ** | 1 runbook/thành phần (CIS, Booking, TP Lambda, Vercel, Terraform) → OPS-02. CIS task-def + Vercel đã có lệnh ở `skill/aa-ship` §5 (AA-869, Done): tách ra file, không viết lại |
| C3 Backup/DR | **Giữ** | Runbook restore PITR + 1 schema + log diễn tập; đã có issue AA-829 → OPS-03 |
| C4 Incident Response | **Giữ (đã có)** | Thêm playbook theo loại alarm + mẫu postmortem → OPS-04 |
| C5 Secret Rotation | **Gộp** | Gộp với secrets register (AA-878) → SEC-02 |
| D1 Security Baseline | **Giữ** | 1 trang checklist có cột trạng thái → SEC-01 |
| D2 Monitoring/Alerting | **Chuyển nhóm + sinh tự động** | Đây là vận hành → OPS-07, bảng alarm sinh từ Terraform, mỗi alarm có link runbook |
| D3 Compliance Log | **Đổi hình** | "Log" chung chung → *register* (hoạt động xử lý dữ liệu, sub-processor, DPA, quyết định, log access review/retention) → SEC-04 |
| D4 Vulnerability Mgmt | **Giữ** | Chính sách (SLA mức độ, ngoại lệ, triage tháng) + bảng alert sinh tự động → SEC-03 |
| E1 Cost Management | **Giữ, tách 2** | Quy tắc + budget (FIN-01) và báo cáo tháng có unit cost (FIN-02) |
| E2 Report Templates | **Gộp** | Không phải 1 tài liệu mà là thư mục mẫu `docs/templates/` → TPL-01 |
| E3 Onboarding Guide | **Giữ, tách 2** | Người (tutorial, GUIDE-01) và agent (thứ tự file chỉ dẫn, GUIDE-02) |
| + Database Operations | **Giữ dạng index** | INF `db/README.md` đã mạnh; chỉ cần trang nối + dọn bản trùng ECS exec → OPS-05. "AWS Database Guide" Nghiệp nhắc **không tìm thấy trong repo** — cần Nghiệp gửi nguồn |

**Bỏ:** không bỏ chủ đề nào. Chỉ bỏ 2 *cách làm*: (1) dán resource ID thật vào văn xuôi; (2) coi 21 mục là 21 file viết tay độc lập.

**Thêm (thiếu trong 21):** ADR index mỗi repo, CONTEXT.md mỗi repo, contracts, API reference (OpenAPI), LLM/AI ops (prompt register,
route, eval), CHANGELOG + release note, feature-flag register, glossary, agent onboarding, hướng dẫn cho chị Thư, prod blueprint
(ADR 0012), mẫu tài liệu/PR template, và chuẩn kỹ thuật/dữ liệu (`docs/architecture/data-standards/` + `docs/database/schema-ownership.md`,
đã có, nguồn của các luật DM-x — bản trước bỏ sót).

### 1.2 Danh mục chuẩn cuối cùng (doc catalog)

Ký hiệu: **Loại** theo Diátaxis (Tut = tutorial, How = how-to, Ref = reference, Exp = explanation; Rep = report, quá trình).
**Mode**: H = viết tay, G = sinh tự động, H+G = văn xuôi tay + bảng sinh. **Đọc**: E = engineer, A = agent, T = chị Thư.
**Owner mặc định**: Nghiệp duyệt, Claude viết/cập nhật; ghi riêng nếu khác. Repo: **root** = AA-Ecosys (private), **INF** = AA-CIS-Infra
(private), **CIS/BK/TP** = app repo (**public**, chỉ nội dung an toàn để công khai).

| ID | Tên | Loại | Đích (repo:đường dẫn) | Mode (cơ chế sinh) | Owner | Nhịp cập nhật / review | Đọc | Hiện có | Việc cần làm (issue §4) |
|---|---|---|---|---|---|---|---|---|---|
| ARCH-01 | Ecosystem architecture (C4 L1–L2) | Exp | root:`docs/ecosystem-architecture.md` | H (Mermaid) | mặc định | Khi đổi ranh giới; review 90 ngày | E A T(L1) | Có, 388 dòng, 1 flowchart | Thêm C4 L1/L2, link từ CONTEXT → I9 |
| ARCH-02 | Network & edge | Exp + Ref | INF:`docs/network.md` + `docs/generated/network.md` | H+G (`terraform show -json` → bảng subnet, SG matrix, endpoint) | mặc định / bot | Sau mỗi apply đụng mạng; review 90 ngày | E A | Rải rác: INF CONTEXT "Edge", ADR 0004b, `waf-count-review.md` | I7 (bảng) + I9 (văn xuôi, sơ đồ) |
| ARCH-03 | Service catalog & resource inventory | Ref | INF:`docs/generated/inventory.md` + trang Apps (AA-884) | G (Resource Groups Tagging API theo tag `App` + Terraform state) | bot | Nightly + sau apply | E A T(trang Apps) | INF CONTEXT "Main stack modules", `03-scaling.md` | I7; trang live AA-884 |
| ARCH-04 | Access & IAM matrix | Ref + Exp | INF:`docs/iam.md` + `docs/generated/iam-roles.md`; root:`docs/security/access-matrix.md` | H+G (role, trust, policy từ `aws_iam_role*`) | mặc định | Access review mỗi quý | E A | `ci-role-split.md`, `agent-session-role.md`, `tools/identity/README.md`, ADR 0006/0006a | I7 (bảng) + I9 (ma trận người/CI/agent/connector). Access review đầu tiên + log: **AA-878** mục 5 (đã có) |
| ARCH-05 | ADR index mỗi repo | Exp | `docs/adr/README.md` ở cả 5 repo | H + lint | mặc định | Mỗi ADR mới | E A | root có; CIS 8 ADR không README; BK 1; TP/INF chưa có thư mục | I2 |
| ARCH-06 | CONTEXT.md mỗi repo | Exp | `CONTEXT.md` mỗi repo | H | mặc định | Khi đổi stack/ranh giới; review 90 ngày | E A | Có cả 5 (CIS 1438 dòng) | Thêm front-matter `applies_to` → I1 |
| ARCH-07 | Contracts catalog | Ref | root:`docs/contracts/` | H (+G bảng producer → consumer → version → test pin) | mặc định | Mỗi version contract | E A | Tốt nhất hệ | Bảng sinh: Later, chỉ khi > ~10 contract (§4.5) |
| ARCH-08 | Engineering & data standards (DM rules) + schema ownership | Ref + Exp | root:`docs/architecture/data-standards/{01-engineering,02-data-management,03-scaling}.md`, `docs/database/schema-ownership.md` | H | mặc định | Khi đổi luật DM; review 90 ngày | E A | **Có, đầy đủ** | Chỉ front-matter + link từ catalog → I1 |
| APP-01 | Deployment (index + 1 trang/app) | How | root:`docs/ops/README.md` (index); app:`docs/runbooks/deploy.md` | H | mặc định | Khi đổi workflow deploy | E A | `skill/aa-ship`, README các app | I6 |
| APP-02 | CI/CD matrix | Ref | root:`docs/generated/cicd-matrix.md` | H trước (1 bảng trong `docs/ops/README.md`); G (parse workflow YAML + branch protection) chỉ khi bảng tay sai | mặc định | Khi workflow đổi | E A | Không (chỉ snapshot S241) | I6 (bảng tay); generator: Later (§4.5) |
| APP-03 | Environment config register (chỉ tên) | Ref | root:`docs/generated/env-config.md` | G (`describe-task-definition`, `get-function-configuration`, Vercel env API; bỏ giá trị, secret chỉ giữ tên). Chạy ở **INF** (root không có workflow/role AWS), mở PR vào root như `db-schema-dump.yml` | bot | Nightly + sau deploy | E A | Bảng tay ở README CIS/TP; Booking chưa có | I8. ⚠️ tên biến có gạch dưới: generator giữ nguyên, dòng viết tay thì Nghiệp sửa trong VSCode |
| APP-04 | DB schema reference + ERD | Ref | root:`docs/architecture/db-schema-reference.md` (+ `db-erd.md`) | G (INF `db-schema-dump.yml`, đã có) | bot | Sau mỗi migration + nightly | E A | **Có, đầy đủ** | Thêm ERD Mermaid → I8; sửa steering `db-schema.md` → I3 |
| APP-05 | API reference (OpenAPI) | Ref | app:`openapi.json` (CI artifact/commit); CIS `/admin/api-docs` | G (FastAPI export + oasdiff) | bot | Mỗi PR | E A (đối tác sau) | 1 phần (`/booking/openapi.json`, trang admin CIS) | I14 (Before prod) |
| APP-06 | LLM/AI operations | Ref + How | CIS:`docs/llm/` (an toàn công khai); root:`docs/generated/llm-routes.md` | H+G (export `shared.llm_role_config`, `shared.llm_model_catalog`) | mặc định | Khi đổi prompt/route/model | E A | ADR CIS 0005–0008, CONTEXT "Model operations", `/admin/settings` | I15 (Before prod) |
| APP-07 | CHANGELOG + release note | Ref / Rep | app + INF:`CHANGELOG.md`; release note qua Jira | G (release-please) + H (release note) | bot / Nghiệp duyệt note | Mỗi release | E A T | Không có | I5 |
| OPS-01 | Operations index (thay "PROD Runbook") | How (index) | root:`docs/ops/README.md` | H | mặc định | Review 90 ngày | E A | Không (chỉ có incident doc) | I6 |
| OPS-02 | Rollback runbooks | How | root:`docs/ops/runbooks/rollback-{cis,booking,tp-lambda,vercel,terraform}.md` | H, **tested** | mặc định | Diễn tập mỗi quý | E A | CIS task-def + Vercel: `aa-ship` §5 (AA-869 Done, ECR immutable); S243 §5.4 | I6: tách CIS/Vercel từ `aa-ship` §5 (aa-ship chỉ còn link), viết mới Booking/Terraform; TP Lambda alias `live` thuộc **AA-703** (U-54) |
| OPS-03 | Backup, restore & DR (+ drill log) | How + Rep | root:`docs/ops/runbooks/restore-rds-pitr.md`, `restore-schema.md`, `docs/ops/dr.md`, `docs/ops/drills/` | H (+ output drill) | mặc định | Diễn tập mỗi quý | E A | Drill S241 (chỉ script + JSON, **không có write-up**), `data-standards/02` §9 | **AA-829** (mở rộng) |
| OPS-04 | Incident response, playbooks, postmortem | How + Exp | root:`docs/ops/incident-response.md`, `docs/ops/playbooks/*.md` | H | mặc định | Sau mỗi SEV1–2; review 90 ngày | E A T(tóm tắt) | `incident-response.md` có, tốt | Playbook theo loại alarm → I6 |
| OPS-05 | Database operations (bổ sung) | How (index) | root:`docs/ops/database-operations.md` → INF `db/README.md`, skill `aa-cis-schema` | H | mặc định | Review 90 ngày | E A | INF `db/README.md` mạnh; bản ECS exec trùng ở 3 chỗ; root `docs/db-access-ssm-tunnel.md` + `db-tunnel.sh` nằm lạc ở gốc `docs/` | I6 (index) + I3 (dọn bản trùng, chuyển file lạc) |
| OPS-06 | Feature-flag register | Ref | root:`docs/ops/feature-flags.md` | H (sau này G từ bảng) | mặc định | Khi thêm/gỡ cờ | E A | Cờ ad hoc | I6 |
| OPS-07 | Monitoring & alarm catalog | Ref | INF:`docs/generated/alarms.md` | G (`terraform show -json` / `describe-alarms`); description alarm chứa link runbook | bot | Sau apply | E A | ~36–53 alarm (S243 README đếm ~36 khối Terraform; AA-872 báo 53/53 có OKActions), **không alarm nào có runbook link** | I7 |
| PROD-01 | Prod blueprint + prod runbook section | Exp + How | root:`docs/adr/0012-*.md` (số 0009–0011 đã giữ chỗ: AA-804, U-25) + mục prod trong `docs/ops/README.md` | H | Nghiệp | Khi có ngày go-live | E A | Không; **AA-880** đã có (U-40) | Mở rộng **AA-880** (Before prod) |
| SEC-01 | Security baseline | Ref (checklist) | root:`docs/security/baseline.md` | H (cột trạng thái sau này G) | mặc định | Mỗi quý | E A | Rải rác ADR/INF/S241 | I10 |
| SEC-02 | Secrets register + rotation | Ref + How | root:`docs/security/secrets-register.{yaml,md}`, `docs/security/rotation/*.md`; checker ở INF | H+G (drift checker) | mặc định | Kiểm tháng; xoay theo loại secret | E A | Đã lên kế hoạch AA-878 | **AA-878** (mở rộng: quy trình xoay) |
| SEC-03 | Vulnerability management | Exp + Ref | root:`docs/security/vulnerability-management.md` + `docs/generated/security-alerts.md` | H+G (`gh api` code-scanning/dependabot) | mặc định | Triage tháng | E A | Công cụ CI có; `pip-audit-ignore.txt` là register ngoại lệ thực tế | I10 |
| SEC-04 | Compliance & privacy register | Ref + Rep | root:`docs/legal/` (thư mục đã có: `tenant-terms-ai-clause-draft.md`) → `register.md` (RoPA, sub-processor, DPA, quyết định) + `retention-log.md`; access-review log ở `docs/security/` (AA-878) | H (+G retention log từ lịch sử job) | Nghiệp; quyết định nghiệp vụ = chị Thư | Mỗi quý; khi thêm vendor | E T (luật sư) | Nháp điều khoản AI, `data-standards/02` §6–7 | **AA-886** (đã gồm sub-processor, DPA, RoPA từ PII tag): register là bản trong repo của gói đó. Liên quan AA-877 (PII tag), AA-804 (AI Use Register), AA-839 (erasure) |
| FIN-01 | FinOps rules, budgets, tags | Exp + Ref | root:`docs/ops/finops.md` | H | mặc định | Mỗi quý | E A T | Quy tắc chỉ nằm trong memory Claude; budget trong `observability.tf` | I11 |
| FIN-02 | Monthly cost report (unit cost) | Rep | root:`docs/ops/cost/YYYY-MM.md` | G (Cost Explorer theo `App` + service; `llm_call_log` theo stage) + H (giải thích) | Claude soạn, Nghiệp duyệt | Hằng tháng | E T | Chưa có (lần đầu ≥01/11) | I11. Số liệu chi phí/app cũng là nguồn cho AA-884 (Apps page) và AA-858 (overview chị Thư): 1 script, 3 nơi đọc |
| GUIDE-01 | Engineer onboarding | Tut | root:`docs/onboarding.md` (chứa **bảng account map duy nhất**) | H | mặc định | Review 90 ngày; khi đổi quyền | E | README root lỗi thời | I12 |
| GUIDE-02 | Agent onboarding & thứ tự file chỉ dẫn | Ref | root:`docs/agents.md` | H, **chỉ là mục lục** (link + thứ tự ưu tiên), không chép lại luật, để không thành lớp chỉ dẫn thứ 6 bị lệch | mặc định | Review 90 ngày | A E | Rải rác 5 CLAUDE.md, steering, skill | I12 |
| GUIDE-03 | Glossary | Ref | root:`docs/glossary.md` | H | mặc định | Khi có thuật ngữ mới | E A T | S243 §8 (tiếng Việt) | I1 |
| GUIDE-04 | Hướng dẫn cho chị Thư (admin, portal, chi phí, release note) | Tut/How | Google Drive AdventureAsia (tiếng Việt, ảnh/video); sau này trang Docs `audience: owner` | H | Nghiệp; chị Thư duyệt | Mỗi release lớn | T | Chưa có | **AA-855** (mở rộng) + I13 |
| TPL-01 | Bộ mẫu tài liệu + PR template | — | root:`docs/templates/*`; mỗi repo `.github/pull_request_template.md` | H | mặc định | Khi đổi quy chuẩn | E A | 1 phần (skill Jira, session) | I1 + I4 |

**Ngoài danh mục, giữ nguyên vai trò "nhật ký"** (không phải sự thật hiện hành, không cần front-matter): `docs/sessions/`, `docs/audits/`,
`docs/implementation-notes/`, `docs/backlog/`, `skill/aa-lessons/lessons.md`. Erasure/retention runbook đã có AA-839 (parked tới trước prod).

---

## 2. Quy chuẩn chung

### 2.1 Front-matter bắt buộc (mọi mục trong danh mục §1.2)

Thay dạng `last-reviewed` (gạch nối) ở bản hướng dẫn §3.4 bằng dạng gạch dưới dưới đây, cho thống nhất với schema JSON:

```yaml
---
id: OPS-02                        # ID trong doc catalog
title: Rollback - AA-CIS-App
type: how-to                      # tutorial | how-to | reference | explanation | adr | report | template
status: active                    # draft | active | deprecated | superseded
superseded_by: null               # ID hoặc đường dẫn khi status = superseded
owner: nghiep
audience: [engineer, agent]       # owner (Thư) | staff | engineer | agent
applies_to: [aa-cis-api, aa-cis-worker]   # service/app/version mà tài liệu đúng
last_reviewed: 2026-10-19
review_every_days: 90
# chỉ runbook / how-to:
last_tested: 2026-10-19
tested_where: dev-acc2            # dev-acc2 | drill | incident | dry-run
tested_evidence: <link Linear comment / docs/audits/... / docs/ops/drills/...>
# chỉ tài liệu sinh tự động:
generated: false
generator: null                   # vd infra/AA-CIS-Infra/.github/workflows/docs-gen.yml
---
```

- **Bắt buộc tối thiểu** (schema `required`): `id`, `title`, `type`, `status`, `owner`, `last_reviewed`. Các trường còn lại tuỳ chọn, chỉ bắt
  buộc theo loại (`last_tested`/`tested_where`/`tested_evidence` cho runbook `active`; `generator` khi `generated: true`). Mặc định
  `review_every_days: 90` nếu bỏ trống. Lý do: 1 kỹ sư + agent, front-matter dài thì sẽ bị điền cho có.
- `CONTEXT.md` và ADR không dùng front-matter đầy đủ: CONTEXT.md chỉ thêm `last_reviewed` + `applies_to`; ADR giữ dòng `Date · Status` theo
  `skill/ai-nghiep/references/adr.md`.
- File sinh tự động có thêm dòng đầu `<!-- GENERATED by <workflow> from <repo>@<sha> - do not edit -->` (mẫu đã có ở `db-schema-reference.md`).
- Schema đặt ở root `docs/templates/frontmatter.schema.json`; CI kiểm (§2.6).
- `audience` dùng để lọc điều hướng trên trang Docs sau này (§3). Đây **không** phải cơ chế phân quyền.

### 2.2 Mẫu theo loại tài liệu (đặt ở `docs/templates/`)

| Mẫu | Các mục bắt buộc |
|---|---|
| `runbook.md` (how-to vận hành) | When to use (trigger/alarm) · Preconditions (quyền, profile, trạng thái `shared.job`) · Steps (mỗi bước 1 lệnh 1 dòng + kết quả mong đợi) · Verify · Rollback / abort · Escalation (ai được báo) · Tested log (ngày, nơi, bằng chứng) |
| `how-to.md` (việc kỹ sư thường làm) | Goal · Before you start · Steps · Verify · Troubleshooting |
| `reference.md` | Scope · Source of truth (file/bảng/Terraform output) · Table · How to regenerate (nếu G) |
| `explanation.md` | Context · Design (sơ đồ) · Why (đánh đổi, link ADR) · Boundaries · Open questions |
| `adr.md` | Giữ mẫu đang dùng ở `docs/adr/` (Status · Context · Decision · Consequences · Alternatives); thêm `Amends/Supersedes`. Đã Accepted thì chỉ amend `NNNNa` |
| `report-cost-monthly.md` | Totals theo `App` + so tháng trước · Top 5 service · Chênh > 20% và lý do · LLM theo stage/account · Unit cost (USD/tour published, USD LLM/tour, USD/trip plan, USD/booking) · Actions · Tóm tắt 5 dòng tiếng Việt cho chị Thư |
| `release-note.md` | 3–6 dòng nghiệp vụ, chỉ tính năng đã verify live, không mã Linear (khớp `skill/aa-jira-update`) |
| `postmortem.md` | Summary · Impact · Timeline · Root cause · What went well/badly · Actions (issue Linear) · Lesson (dòng `lessons.md`) |
| `uat-report.md` | App · Build (`version`/`git_sha`) · Kịch bản · Video link (Drive) · Kết quả · Lỗi mở |
| `issue-dor.md` | Mẫu DoR ở bản hướng dẫn §5.6 (Goal · Scope · Acceptance · Verify · Risk class · Dependencies · Docs impact) |
| `.github/pull_request_template.md` | What/Why + `Refs AA-xxx` · Risk & rollback · Cost (nếu thêm AWS resource) · Docs checklist (bản hướng dẫn §3.4) |

### 2.3 Quy tắc resource ID

1. **Văn xuôi không chứa ID dễ đổi**: `sg-…`, `subnet-…`, `vpc-…`, ARN, số task-def revision, snapshot ID, ID API Gateway.
   Viết bằng **tên** (`aa-cis-dev-db`, `aa-cis/dev/rds`, `aa-cis-dev-api`) và kèm **lệnh tra 1 dòng**, hoặc **tên Terraform output**
   (`tf_apply_role_arn`), hoặc **link tới bảng sinh** (`docs/generated/network.md`).
2. **Account ID chỉ ở 1 chỗ**: bảng account map trong `docs/onboarding.md` (GUIDE-01). Nơi khác link tới đó. Ngoại lệ: tên tài nguyên
   đã chứa account ID theo quy ước đặt tên (vd bucket `aa-cis-bronze-005097885195`).
3. **Repo public (CIS, BK, TP)**: không account ID, không ARN, không SG/VPC ID, không inventory, không danh sách secret. Những thứ đó ở root/INF.
4. **Tiền đề kỹ thuật**: root `accounts/aa365` của INF hiện **không có output** cho VPC/RDS/ECS/ALB/SG. Cần thêm `outputs.tf` cho ID lõi
   trước khi bảng sinh có ý nghĩa (I8).
5. **Ngoại lệ hợp lệ**: tài liệu nhật ký (sessions, audits, implementation notes), file sinh tự động, và **file chỉ dẫn agent**
   (`CLAUDE.md`, `.kiro/steering/*`, `skill/**`): agent cần bảng account map ngay trong ngữ cảnh, không theo link được lúc khởi động.
   Bảng trong các file này phải khớp GUIDE-01 (lint so sánh, không xoá).
6. **CI chặn** (§2.6): regex `sg-[0-9a-f]{8,}`, `subnet-[0-9a-f]{8,}`, `vpc-[0-9a-f]{8,}`, số 12 chữ số đứng riêng, ngoài các đường dẫn
   được miễn. `arn:aws:` là **lỗi ở repo public** (CIS, BK, TP) nhưng chỉ **cảnh báo ở root/INF**: tài liệu IAM (ARCH-04, `agent-session-role.md`)
   cần ARN mẫu/pattern trong policy, chặn cứng sẽ đẻ ra danh sách miễn dài.

### 2.4 Quy tắc "tested"

- Runbook chỉ `status: active` khi đã chạy thật ít nhất 1 lần trên **Dev acc2** (`--profile aa365-admin`), trong **diễn tập**, hoặc trong
  **sự cố thật**. Ghi `last_tested`, `tested_where`, `tested_evidence`.
- Bước phá huỷ (xoá dữ liệu, restore đè) chỉ thử bằng **DRY RUN** theo `skill/aa-cis-schema/references/destructive-ops.md`, hoặc trên tài nguyên
  tạm (instance restore riêng như drill S241). Ghi `tested_where: dry-run` hoặc `drill`.
- Chưa thử → `status: draft` + banner đầu file `> UNTESTED - do not follow in an incident without checking each step.`
- Thử lại: rollback và restore **mỗi quý**; mọi runbook khi quy trình đổi; runbook có `last_tested` > 180 ngày thì CI cảnh báo.
- Bằng chứng: comment Linear "Tested on Dev" hoặc file trong `docs/ops/drills/YYYY-MM-DD-<slug>.md` (output lệnh, thời gian, kết quả).

### 2.5 Quy tắc lệnh AWS CLI trong tài liệu

- **Một lệnh = một dòng**, không `\` xuống dòng (treo WSL2). Biến shell đặt ở dòng riêng trước đó (`TASK_ARN=$(aws ecs list-tasks … )`).
- Luôn ghi đủ `--profile aa365-admin --region us-west-1` (hoặc profile satellite đúng của acc1/acc3). Bước đầu mọi runbook:
  `aws sts get-caller-identity --profile aa365-admin`.
- Dùng tên, không ID (§2.3). Lệnh ghi (write) đánh dấu rõ `# WRITE` ở cuối dòng.
- Tên biến môi trường có gạch dưới trong tài liệu viết tay: Nghiệp sửa tay trong VSCode, agent không tự sinh/sửa.
- CI kiểm (§2.6): trong code fence, dòng bắt đầu bằng `aws ` mà kết thúc bằng `\` thì lỗi.

### 2.6 Review tài liệu trong PR và kiểm tra trong CI

**Trong PR** (docs-as-code): docs đổi cùng PR với code. PR template có Docs checklist. Claude gác cổng kiểm "Docs impact" trong DoR khớp với
file đã đổi. File `generated: true` chỉ đổi qua PR của bot (như `db-schema-dump.yml` đang làm).

**Workflow `docs-lint.yml`** ở root (và bản nhỏ ở INF; app repo chỉ link check + regex ID). Lưu ý: root repo **hiện chưa có `.github/` nào**
(không workflow, không role AWS OIDC), nên đây là workflow đầu tiên của root, chỉ chạy lint không cần AWS. Mọi generator cần đọc AWS
(I7, I8) chạy ở INF và mở PR vào root bằng token đã có của `db-schema-dump.yml`.

| Kiểm tra | Mức | Ghi chú |
|---|---|---|
| Front-matter hợp lệ theo schema (catalog docs) | Lỗi | Chỉ áp cho file trong danh mục, không áp nhật ký |
| Link nội bộ (relative) | Lỗi | lychee chế độ offline, nhanh |
| Link ngoài | Cảnh báo, chạy hằng tuần | Tránh PR đỏ vì site ngoài chập chờn |
| `last_reviewed` > `review_every_days` (mặc định 90) | Cảnh báo (annotation) | Hằng tuần sinh `docs/generated/freshness.md`: danh sách file quá hạn |
| `last_tested` > 180 ngày ở runbook active | Cảnh báo | |
| Regex resource ID (§2.3) | Lỗi (`arn:aws:` chỉ cảnh báo ở root/INF) | Có danh sách đường dẫn miễn |
| AWS CLI nhiều dòng (§2.5) | Lỗi | |
| ADR có `Status:` hợp lệ và có trong `docs/adr/README.md` | Lỗi | |
| gitleaks trên `docs/**` | Lỗi | Tài liệu được có **tên** secret, không bao giờ có **giá trị** |

Chi phí: Actions trên repo private dùng quota miễn phí của GitHub Free (2.000 phút/tháng); job lint < 1 phút.

### 2.7 Nhịp review

| Nhịp | Việc |
|---|---|
| Mỗi PR | Docs checklist; docs-lint |
| Hằng tuần | Link ngoài + báo cáo freshness (tự động) |
| Hằng tháng | Báo cáo chi phí (FIN-02); triage lỗ hổng (SEC-03); kiểm drift secrets register (SEC-02) |
| Mỗi quý | Access review (ARCH-04); diễn tập rollback + restore (OPS-02/03); review baseline bảo mật (SEC-01), compliance register (SEC-04), FinOps rules (FIN-01) |
| Đầu phiên (ritual) | Mở `docs/generated/freshness.md` nếu có mục quá hạn; chọn 1–2 file để review cùng việc của phiên |

### 2.8 Ngôn ngữ

- Tài liệu kỹ thuật (mọi mục §1.2 trừ GUIDE-04): **tiếng Anh**, theo `.kiro/steering/language-convention.md`.
- Giữ tiếng Việt theo convention: session log, Notion memory. Bản tư vấn cho Nghiệp trong `docs/audits/` (S241, S243, file này) đang viết
  tiếng Việt **theo lệ**, convention chưa ghi; audit kỹ thuật dành cho agent đọc (vd S234 `t-series-rounds`) vẫn tiếng Anh.
- **Đề xuất ngoại lệ mới, Nghiệp chốt:** (1) GUIDE-04 (hướng dẫn cho chị Thư) và phần tóm tắt cho chị Thư trong FIN-02 viết **tiếng Việt**, văn
  phong không kỹ thuật; (2) ghi rõ lệ "bản tư vấn trong `docs/audits/` cho Nghiệp = tiếng Việt". Nếu đồng ý thì thêm 2 dòng vào
  `language-convention.md` (I1).

---

## 3. Lưu ở đâu, đọc ở đâu

### 3.1 So sánh ngắn

| Phương án | Chi phí/tháng | Chị Thư đọc được? | Độ tươi | Kết luận |
|---|---|---|---|---|
| Chỉ markdown trong repo GitHub | 0 | Không (không có tài khoản GitHub) | Tốt nhất (cùng PR với code) | **Nguồn chuẩn, luôn giữ** |
| **Trang Docs trong admin CIS**, CI đồng bộ markdown lên S3 private, backend CIS phục vụ qua admin API | ~0,01 USD (S3) | **Có, bằng đăng nhập staff Cognito** (email-code live từ S242, chị Thư đã được mời; cutover legacy ở AA-703) | Vài phút sau merge, không tốn deploy Vercel | **Làm, ở giai đoạn 2** |
| Như trên nhưng fetch GitHub lúc build Vercel | 0 | Có | Chỉ khi redeploy (tốn quota 100 deploy/ngày Hobby) | Không: cần PAT đọc repo private trong env build của project gắn repo public, và nội dung bị nhúng vào bundle |
| Site riêng Astro Starlight trên Vercel Hobby | 0 nếu công khai. Chặn người lạ: Password Protection chỉ có ở Enterprise hoặc Pro (20 USD/người/tháng) **+ add-on Advanced Deployment Protection ~150 USD/tháng** [cần kiểm giá hiện hành] | Không: Vercel Authentication trên Hobby chỉ cho thành viên account (chỉ Nghiệp) và Standard Protection không che domain production | Mỗi lần push = 1 deploy | Không |
| Starlight trên S3 + CloudFront + Lambda@Edge Cognito | ~0–1 USD (CloudFront free tier 1 TB/tháng; Lambda@Edge phải ở us-east-1, ngoài region chuẩn us-west-1) | Có | Tốt | Giai đoạn 3, chỉ khi có trigger |
| MkDocs Material | — | — | — | Không: đã vào maintenance mode từ 11/2025 |
| Backstage TechDocs | ~20–40 USD + công vận hành | — | — | Quá tầm cho 1 kỹ sư |
| Notion / Google Drive làm nguồn | Có sẵn | Drive: có | Kém: bản sao lệch dần | Không làm nguồn; Drive chỉ chứa bản xuất cho chị Thư |
| GitHub Wiki | Repo private cần Team 4 USD/người | Không | Repo wiki riêng, không review | Không |

### 3.2 Khuyến nghị theo giai đoạn

**Giai đoạn 1 — Now (2–3 phiên tới): chỉ git.**
- Làm các issue nội dung I1–I12 (§4). Kỹ sư đọc trên GitHub (Mermaid render sẵn), agent đọc repo như hiện tại.
- Chị Thư chưa cần trang nào. Khi cần gửi gì (báo cáo chi phí tháng, hướng dẫn admin) thì xuất PDF lên Drive AdventureAsia, có dòng
  "generated from <repo>@<sha>". Drive không bao giờ là nguồn.

**Giai đoạn 2 — trước prod (kéo sớm được): trang `/admin/docs` trong CIS (I13).**
- **Trả lời câu "có nên làm trang Docs trong admin không": có.** Lý do: chị Thư đọc được bằng đăng nhập sẵn có, chi phí gần 0, nội dung không
  lọt vào repo/bundle public, không tốn quota deploy Hobby, và đúng hướng "quan sát mọi thứ trong admin" đang theo
  (`/admin/api-docs`, `/admin/llm-usage`, Apps page AA-884).
- **Nhưng không làm ngay.** Trang chỉ có giá trị khi nội dung đã chuẩn (front-matter, `audience`) và khi đã có ≥ 5 tài liệu cho chị Thư.
  Nó cũng chạm `frontend/` đang bị AA-885 (tách portal) động tới, nên làm sau khi AA-885 merge để tránh xung đột.
  Trigger kéo sớm: AA-855 (UAT) bắt đầu, hoặc chị Thư hỏi tài liệu.
- Trang là **chỗ đọc, không phải chỗ viết**: không có nút sửa; mỗi trang có footer "source: repo@sha · last reviewed". Kèm vài widget
  live: alarm đang ALARM, drift secrets register, danh sách tài liệu quá hạn.
- **Quyết định cần chốt khi làm:** chị Thư có role `admin`, nên tag `audience` chỉ ẩn khỏi menu chứ không chặn. Đề xuất mặc định:
  chấp nhận chị Thư xem được mọi thứ (tài liệu không chứa giá trị secret). Khi có thêm staff `admin` không phải chủ thì thêm cờ `engineer`.

**Giai đoạn 3 — sau, chỉ khi có trigger:** > 2 kỹ sư, có contractor không được vào admin CIS, hoặc prod cần tài liệu đọc được khi CIS sập.
- Khi đó dựng Starlight trên S3 + CloudFront + Cognito edge, build từ **cùng markdown, front-matter và manifest**, không phải viết lại.
- Ngay khi có prod (không chờ trigger): giữ 1 bản **break-glass** (OPS-01 index, OPS-02 rollback, OPS-04 incident) dạng PDF trên Drive.
  Trang Docs sập cùng CIS, đúng lúc cần runbook nhất.

---

## 4. Danh sách issue để "làm hết"

### 4.1 Bảng issue

Project Linear: **dùng project có sẵn** theo `skill/aa-linear-issue` (gom 3 project từ S231, không mở project mới): mọi issue docs/CI/bảo mật/ops
vào `CIS Core — Pipeline, LLM & Platform`; I13 vào `CIS Portal — Admin & Tenant UI`. **[cần kiểm]** số issue chưa lưu trữ của CIS Core trước
khi tạo 14 issue (ngưỡng 100/project; workspace Free trần 250). Phải hỏi Nghiệp trước khi tạo (steering). Issue mở rộng phạm vi thì chỉ thêm
comment vào issue cũ (`get_issue` kiểm title trước khi ghi), không tạo mới. Title theo mẫu `[Area] <việc> — <chi tiết>`; mô tả theo mẫu
Problem / Scope / Done when / Related.

| # | Title (EN) | Repo | Cỡ | Giai đoạn | Phụ thuộc | Gộp N/P | Issue có sẵn |
|---|---|---|---|---|---|---|---|
| I1 | [Docs] Adopt the documentation standard — catalog, front-matter schema, templates, glossary, DoR | root | S | Now | — | N10 | — |
| I2 | [CI] Docs lint and ADR indexes in every repo — front-matter, links, resource-ID and multi-line CLI checks | root, INF, CIS, BK, TP | S | Now | I1 | N9 | — |
| I3 | [Docs] Remove stale docs and agent-instruction drift — CIS runbook v1, root README, steering, stray root files | root, INF, CIS | M | Now | — | N4, N5 | — |
| I4 | [CI] PR template, PR title lint and squash-only settings in all repos — plus Infra .bak cleanup | 5 repo | S | Now | I1 | N3, N8, N11 | — |
| I5 | [Release] Version traceability — CIS /health git_sha, release-please, CHANGELOG per app | CIS, BK, TP (+INF tuỳ chọn) | M | Now | I4 | N1, N2, một phần P12 | Tiền đề cho AA-884 (Apps page đọc version) |
| I6 | [Ops] Operations index and runbooks — rollback per component, DB ops index, flag register, incident playbooks | root (+ app repo cho deploy.md) | M | Now | I1 | N6 | Tách từ `aa-ship` §5 (AA-869 Done); TP Lambda alias thuộc AA-703 |
| I7 | [Infra] Alarm catalog with runbook links and core Terraform outputs — generated inventory, network, IAM tables | INF (PR vào root nếu cần) | M | Now | I1, I6 | một phần P10 | — |
| I8 | [Docs] Generated env-config register (names only) and DB ERD | INF (generator) → root (output) | S–M | Now | I1 | — | Mở rộng workflow INF `db-schema-dump.yml` (AA-807) |
| I9 | (không tạo) mở rộng AA-697: thêm network page + access matrix | root, INF | M | Now | I7 | — | **AA-697** (Backlog; điều kiện "sau AA-653" đã đạt) |
| I10 | [Security] Security baseline and vulnerability management policy — Dependabot for Booking and TripPlanner | root, BK, TP | S | Now | I1 | một phần P6 | Bảng control link tới AA-873/874/875/876 |
| I11 | [FinOps] FinOps doc, Cost Anomaly Detection and the monthly cost report with unit costs | root, INF | S–M | Now | I1 | N7, một phần P12 | Số liệu dùng chung với AA-884, AA-858 |
| I12 | [Docs] Engineer onboarding guide and agent instruction index | root | S | Now | I3 | — | — |
| I13 | [Admin] Docs reader page in the CIS admin — S3 sync, manifest, /admin/docs | INF, root, CIS | M–L | Before prod (kéo sớm được) | I1, I2, AA-885 | — | — |
| I14 | [API] OpenAPI export and breaking-change check for CIS and Booking | CIS, BK | M | Before prod | I5 | P2 | — |
| I15 | [LLM] LLM operations docs, prompt versioning and eval gate | CIS, root | M | Before prod | I1 | P3 | liên quan **AA-729** (golden set), **AA-804** (ADR 0009, AI Use Register) |
| — | Mở rộng: prod runbook section, break-glass PDF, 2 SLO/API, kênh cảnh báo 2, tag `Env` + budget prod | root, INF | — | Before prod | I6, I9, AA-829 | P1, phần SLO của P10 | **AA-880** (đã có, U-40) — bản trước gọi nhầm là issue mới I16 |
| — | Mở rộng: restore runbook (PITR + 1 schema) + `docs/ops/drills/` (Done-when đổi từ `docs/audits` sang `docs/ops/drills`) | root | M | Now | I1 | P9 | **AA-829** |
| — | Mở rộng: secret rotation procedures per class + nơi đặt access-review log | root, INF | M | Now | I1 | một phần P7 | **AA-878** (đang In Progress; mục 5 đã có access review đầu tiên) |
| — | Mở rộng: register trong `docs/legal/` là bản repo của gói RoPA/sub-processor/DPA | root | S | Before prod | I1 | — | **AA-886** |
| — | Mở rộng: owner-facing guides (Vietnamese) cùng UAT | Drive (+ I13) | M | Before prod | I1 | — | **AA-855** |

Số issue **mới** = 14 (I1–I15 trừ I9). Mở rộng 6 issue có sẵn: AA-697, AA-880, AA-829, AA-878, AA-886, AA-855.
Chưa có issue và **không** gộp vào đây: U-25 (GitHub App "aa-agent", ADR 0010/0011, CODEOWNERS, ruleset) — hỏi Nghiệp có tạo không.

### 4.2 Đối chiếu N1–N11, P1–P12 (không tạo trùng)

| Mục guide §7 | Nằm ở |
|---|---|
| N1 CIS `/health` git_sha | I5 |
| N2 release-please + CHANGELOG + tag | I5 |
| N3 PR template + semantic PR lint | I4 |
| N4 dọn lớp chỉ dẫn agent | I3 |
| N5 CIS `.gitignore` docs | I3 (CIS `.gitignore` có `docs/`, nhưng 517 file đã được add cưỡng bức: sửa ignore cho `docs/**/*.md`) |
| N6 `docs/ops/README.md` + rollback | I6 (nội dung CIS/Vercel đã có từ AA-869) |
| N7 Cost Anomaly Detection | I11 |
| N8 delete branch on merge, squash-only, dọn nhánh | I4 (TP đã bật delete-branch; 4 repo còn lại chưa; cả 5 repo còn cho merge commit + rebase) |
| N9 ADR README ở INF/TP | I2 (mở rộng cho cả 5 repo) |
| N10 glossary + mẫu DoR | I1 |
| N11 xoá `main.tf.bak*`, `envs/dev` | I4 (đã kiểm: `main.tf.bak`, `main.tf.bak2`, `envs/dev` rỗng còn ở INF) |
| P1 ADR 0012 môi trường | **AA-880** (U-40) |
| P2 OpenAPI + oasdiff | I14 |
| P3 eval gate + `prompt_version` | I15 (+ AA-729 golden set) |
| P4 Sentry Booking/TP | **AA-871** (giữ nguyên, không tạo mới) |
| P5 TP Lambda `needs: ci` + smoke + alias | `needs: ci`: **AA-879** (CI gate parity, "TripPlanner Lambda deploy after CI"); alias `live` + `rollback.yml`: **AA-703** (U-54) |
| P6 Trivy chặn CRITICAL, coverage, `tsc` gate | **AA-879** (CI gate parity); phần Dependabot ở I10 |
| P7 rotate token + RDS master, secrets register, AA-873/874/876, agent role | **AA-878**, **AA-873**, **AA-874**, **AA-876**; xoay master/GitHub token khi prod: **AA-880** |
| P8 CODEOWNERS / required review / GitHub Team | **U-25** (ADR 0010/0011), **chưa có issue Linear**; không gộp vào AA-880 |
| P9 DR | **AA-829** |
| P10 SLO, alarm runbook link, kênh cảnh báo 2 | Runbook link: I7. SLO + kênh 2: **AA-880** (mở rộng) |
| P11 JSON logs + request ID; "what runs where" | **AA-871** (logs), **AA-884** (Apps page) |
| P12 tag `Env`, budget prod, release note tenant | I11 (tag/budget Dev), **AA-880** (budget prod), I5 (release note) |

### 4.3 Thứ tự đề xuất cho 2–3 phiên tới (3–5 issue/phiên)

1. Phiên A: I1 → I2 → I3 → I4 (nền: chuẩn + lint + dọn rác).
2. Phiên B: I6 → I7 (phần alarm + runbook link trước) → I11 (khớp mốc audit chi phí ≥01/11) → AA-829 phần runbook.
3. Phiên C: I5 → I10 → I12 → AA-697 (mở rộng) → I8.
4. Sau AA-885 và trước UAT: I13, rồi AA-855 + hướng dẫn chị Thư.
5. Khi có ngày go-live: I14, I15, AA-880 (mở rộng), AA-886.

### 4.4 Mô tả issue (dán vào Linear, tiếng Anh; theo mẫu Problem / Scope / Done when / Related của `skill/aa-linear-issue`)

Dưới đây là phần Scope + Done when. Khi tạo, thêm Problem (dẫn S243 proposal + bằng chứng) và Related.

**I1 — [Docs] Adopt the documentation standard — catalog, front-matter schema, templates, glossary, DoR**
Scope: `docs/README.md` with the doc catalog (IDs ARCH/APP/OPS/SEC/FIN/GUIDE/TPL from the S243 proposal), `docs/templates/` (runbook, how-to,
reference, explanation, ADR, cost report, release note, postmortem, UAT report, DoR) and `docs/templates/frontmatter.schema.json`
(required: id, title, type, status, owner, last_reviewed). `docs/glossary.md` (English, from S243 §8). DoR template into
`skill/aa-linear-issue/SKILL.md`; docs/cost lines in the `skill/aa-ship` DoD. If Nghiệp approves, two lines in `language-convention.md`
(owner-facing guides and advisory audits stay Vietnamese).
Done when: the catalog lists every entry with target path, mode, owner and cadence; the schema validates a sample file; existing catalog docs
get front-matter (ecosystem-architecture, incident-response, data-standards, schema-ownership; CONTEXT.md x5 get `last_reviewed` + `applies_to`).

**I2 — [CI] Docs lint and ADR indexes in every repo — front-matter, links, resource-ID and multi-line CLI checks**
Scope: root `.github/workflows/docs-lint.yml` (the root repo's first workflow, no AWS access): front-matter schema, internal link check
(lychee offline), weekly external links, freshness report (`docs/generated/freshness.md`, warn > review_every_days, runbook last_tested
> 180 d), resource-ID regex (`arn:aws:` warn-only in private repos), multi-line AWS CLI check, ADR status lint, gitleaks on docs. Smaller
job in INF and the app repos (links + ID regex). `docs/adr/README.md` in CIS, BK, TP, INF.
Done when: a test PR adding an `sg-` ID or a `\`-continued `aws` command fails; the freshness report is generated on schedule.

**I3 — [Docs] Remove stale docs and agent-instruction drift — CIS runbook v1, root README, steering, stray root files**
Scope: mark CIS `docs/CIS_Runbook_v1.md` SUPERSEDED (or delete) and point to `docs/ops/`; refresh root `README.md` (Booking live, layout);
fix root `.claude/CLAUDE.md`, `.kiro/steering/db-schema.md` (CI regeneration, Booking), INF CLAUDE.md banner; archive CIS `handoff.md`
and `.claude/HANDOFF.md`; dedupe ECS-exec copies into one canonical how-to; move stray files at the root of `docs/` (`*.sql`, `*.sh`,
`db-access-ssm-tunnel.md`, `inventory-old-refs.md`, `tripplanner-to-aaa-handoff.md`) into `docs/ops/` or an archive folder. CIS `.gitignore`:
replace the blanket `docs/` ignore with `docs/**/*.md` tracked and binaries ignored; review local files for real data, account IDs and ARNs
**before** adding (public repo). List the edits Nghiệp makes by hand in `~/.claude/CLAUDE.md`.
Done when: no doc in any repo tells the reader to use acc1 for infra; a new CIS doc can be added without `git add -f`; scan shows no
account ID/ARN in CIS docs.

**I4 — [CI] PR template, PR title lint and squash-only settings in all repos — plus Infra .bak cleanup**
Scope: `.github/pull_request_template.md` (What/Why + Refs, Risk & rollback, Cost, Docs checklist) in all 5 repos; semantic PR title check in
BK and TP; `delete_branch_on_merge=true` and squash-only (merge commit + rebase off) on all repos; prune merged remote branches; delete INF
`main.tf.bak`, `main.tf.bak2`, empty `envs/dev`.
Done when: `gh api repos/<org>/<repo>` shows the settings on all 5 repos; a new PR shows the template.

**I5 — [Release] Version traceability — CIS /health git_sha, release-please, CHANGELOG per app**
Scope: CIS `/health` returns `version` + `git_sha` from the image build arg; Deploy Dev smoke compares the SHA (copy Booking). release-please in
manifest mode (`bump-minor-pre-major`, GitHub App token so checks run, `paths-ignore` for CHANGELOG on deploy) for CIS, BK, TP; first tags;
document the release-PR exception to `Refs AA-xxx` in aa-ship. Release-note template used for Jira drafts.
Note: env var names with underscores are edited by hand by Nghiệp in VSCode.
Done when: `curl /health` on Dev shows the deployed SHA; each repo has `CHANGELOG.md` and a first GitHub Release.
Related: AA-884 reads this version on the Apps page.

**I6 — [Ops] Operations index and runbooks — rollback per component, DB ops index, flag register, incident playbooks**
Scope: `docs/ops/README.md` (index of every runbook in all repos + a hand-written CI/CD table), `docs/ops/runbooks/rollback-{cis,booking,
tp-lambda,vercel,terraform}.md` (CIS and Vercel moved out of `skill/aa-ship` §5 from AA-869, aa-ship keeps a link; TP Lambda documents the
current revert-and-redeploy path until AA-703 adds the `live` alias), core how-tos (ECS exec S3-mediated, deploy-gate override, scale, logs,
job kill switch, legacy login flag, SES bounce), `docs/ops/database-operations.md`, `docs/ops/feature-flags.md`, `docs/ops/playbooks/`
(5xx spike, queue stuck, LLM cost spike, Cognito login, SES), per-app `docs/runbooks/deploy.md` (public-safe).
Done when: every runbook follows the template, uses single-line CLI with names only, and has `last_tested` + evidence from a Dev run (or
`status: draft` with the UNTESTED banner).

**I7 — [Infra] Alarm catalog with runbook links and core Terraform outputs — generated inventory, network, IAM tables**
Scope: step 1: a runbook link in every `aws_cloudwatch_metric_alarm` description + generated `docs/generated/alarms.md`. Step 2: root outputs
for VPC, subnets, SGs, RDS, ECS, ALB, NLB, API GW (today only Booking/TP/identity/CI-role outputs exist); `docs-gen.yml` in INF (after apply +
nightly, read-only OIDC role [cần kiểm role name, likely `tf_plan_role`]) writes `docs/generated/{network,inventory,iam-roles}.md` via a bot PR.
Done when: tables regenerate without manual edits; each alarm in `alarms.md` links to an existing runbook; zero cost stated in the PR.

**I8 — [Docs] Generated env-config register (names only) and DB ERD**
Scope: extend the INF `db-schema-dump.yml` pattern (INF has the AWS role; it opens a PR into root with its existing token): env names (no
values; secrets by name only) from the live ECS task defs, Lambda configs and Vercel projects → root `docs/generated/env-config.md`; a Mermaid
ERD per schema added to the schema dump. Out of scope (Later, §4.5): generated CI/CD matrix and contracts table.
Done when: env-config covers CIS api/worker, Booking, TP Lambdas and the Vercel projects; a secret value never appears (gitleaks green).

**AA-697 extension (comment, no new issue)**
Add to scope: INF `docs/network.md` (ingress path, tiers, NAT, endpoints, egress to Bedrock/OpenAI/DFS, diagram); root
`docs/security/access-matrix.md` (humans, CI roles, agent role, runtime roles, GitHub/Vercel/Linear/Notion/MCP). C4 L1/L2 in
`ecosystem-architecture.md` is already in its scope. The access-review log itself stays in AA-878. No literal IDs (links to generated tables).

**I10 — [Security] Security baseline and vulnerability management policy — Dependabot for Booking and TripPlanner**
Scope: `docs/security/baseline.md` (controls with status: WAF, MFA, OIDC main-only, CI least privilege, SG per caller, RLS, Redis AUTH/TLS
AA-874, GuardDuty/CloudTrail/Access Analyzer/S3 BPA AA-873, branch protection, secret scanning, agent guardrails); `vulnerability-management.md`
(severity SLA, exception process = `pip-audit-ignore.txt` with expiry, monthly triage); generated open-alerts table; `dependabot.yml` in BK and
TP (CIS and INF already have one).
Done when: each control links to its evidence or open issue; Dependabot PRs appear in BK and TP.

**I11 — [FinOps] FinOps doc, Cost Anomaly Detection and the monthly cost report with unit costs**
Scope: `docs/ops/finops.md` (rules now only in Claude memory: cost quote before new services, paid-run subsets, LLM logging; budgets; tags;
acc1/acc3 LLM budgets [cần kiểm]); Cost Anomaly Detection monitors (service + `App` tag) to the existing SNS e-mail (the service is free);
script for `docs/ops/cost/YYYY-MM.md` (Cost Explorer by App/service, `llm_call_log` by stage, unit costs; Cost Explorer API is 0.01 USD per
request, a monthly run is a few cents) + first report for October at ≥01/11.
Done when: anomaly monitor live; `2026-10.md` report with a 5-line Vietnamese summary for Ms. Thư.
Related: AA-884 and AA-858 show cost per app from the same script output.

**I12 — [Docs] Engineer onboarding guide and agent instruction index**
Scope: `docs/onboarding.md` (accounts and access: AWS profiles/MFA, `default` = acc2, GitHub org, Vercel, Linear, Notion, Jira; first local run;
first PR to Dev; where truth lives; the single account-map table). `docs/agents.md`: an index only — every CLAUDE.md, steering file and skill,
which wins, freshness date; no rules restated.
Done when: a fresh reader can open a PR to Dev following only the guide (dry walkthrough by an agent).

**I13 — [Admin] Docs reader page in the CIS admin — S3 sync, manifest, /admin/docs**
Scope: INF: private docs bucket, OIDC write role for root/INF `docs/*`, ECS task read (state cost < 0.05 USD/month). Root/INF workflow: build
`manifest.json` (path, repo, sha, title, audience, last_reviewed, headings) + optional search index, `s3 sync`. CIS backend
`GET /admin/docs/manifest`, `GET /admin/docs/file?path=` (path must be in the manifest). CIS frontend `/admin/docs` under Platform →
Developer: tree, audience toggle, react-markdown + remark-gfm + rehype-slug, lazy mermaid, no raw HTML, source footer. After AA-885 merges.
Done when: Ms. Thư can open an `audience: owner` page with her staff Cognito login; content updates within minutes of a merge with no Vercel deploy.

**I14 — [API] OpenAPI export and breaking-change check for CIS and Booking**
Scope: CI exports `openapi.json` for CIS and Booking; oasdiff on PRs against `main`; `response_model` for public routes; publish to the release.
Done when: a test PR removing a public field fails unless labelled breaking.

**I15 — [LLM] LLM operations docs, prompt versioning and eval gate**
Scope: prompt register (id, version, file, stage, eval baseline), eval runbook, generated route/catalog table; nullable `prompt_version` on
`shared.llm_call_log` (expand migration); `eval-regression.yml` on PRs touching prompts. Uses the golden set from **AA-729**; ADR 0009 and the
AI Use Register stay in **AA-804**. Public repo: no secrets or tenant data in examples.
Done when: a prompt change PR shows an eval run ID and the version lands in `llm_call_log` on Dev.

**AA-880 extension (comment, no new issue)**
Add to scope: prod section in `docs/ops/README.md`; 2 SLOs per public API; second alert channel; `Env` tag + prod budget; break-glass PDF
copy of OPS-01/02/04 on Drive. CODEOWNERS and the GitHub Team decision stay with U-25 (ADR 0010/0011), not here.

### 4.5 Cắt gọn cho 1 kỹ sư + agent (chống overkill)

| Mục | Đánh giá | Đề xuất |
|---|---|---|
| 34 mục catalog cùng lúc | Quá nhiều cho 1 người duyệt | **Bản tối thiểu** (Now): I1, I2, I3, I4, I6, I7 bước 1, I11, AA-829. Còn lại theo nhịp §4.3 |
| Generator CI/CD matrix (APP-02) | 5 repo, ~20 workflow, ít đổi | Bảng tay trong `docs/ops/README.md`; generator chỉ khi bảng tay sai 2 lần |
| Generator bảng contracts (ARCH-07) | 6 file contract, README đã tốt | Later, khi > ~10 contract |
| Generator network/IAM (I7 bước 2) | Cần thêm output Terraform lõi trước | Làm sau bảng alarm; network/IAM giữ văn xuôi + lệnh tra 1 dòng nếu thiếu thời gian |
| Front-matter 15 trường | Sẽ bị điền cho có | 6 trường bắt buộc, còn lại theo loại (§2.1) |
| SEC-04 4 file | Dư cho giai đoạn Dev | 1 `register.md` + 1 `retention-log.md` trong `docs/legal/`; access-review log ở AA-878 |
| release-please 3–4 repo | ~16 PR/ngày, release PR mở liên tục | Chấp nhận được; nếu vướng thì chỉ tag theo deploy + CHANGELOG sinh từ commit |
| Diễn tập rollback + restore mỗi quý | Hợp lý | Gộp vào 1 phiên/quý, ghi `docs/ops/drills/` |
| Trang `/admin/docs` (I13) | Có ích cho chị Thư, M–L | Giữ ở giai đoạn 2, chỉ khi có ≥ 5 tài liệu `audience: owner` |

---

*Phương pháp: tổng hợp 2 báo cáo trinh sát đọc-only 19/10/2026 (bản đồ tài liệu theo 21 mục; đánh giá nơi lưu/hiển thị kèm tài liệu Vercel,
GitHub, AWS), bản hướng dẫn S243 `README.md` và `docs/backlog/README.md`. Không thay đổi repo, AWS, Linear, Notion hay Jira.*
