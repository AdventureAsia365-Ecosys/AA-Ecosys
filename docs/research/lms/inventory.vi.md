---
id: GUIDE-13-lms-inventory
title: Danh mục tri thức AA Academy
description: Every domain, method, standard, process and tool the AA ecosystem runs on, with its source of truth, its audience and the AA Academy module that teaches it.
type: report
status: draft
owner: nghiep
audience: [owner, engineer, devops, cto, cio, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-13
review_every_days: 90
related: [GUIDE-13-lms, CAT-00, AA-1098, AA-1099]
lang: vi
translation_of: docs/research/lms/inventory.md
---

# Danh mục tri thức AA Academy

Ghi chú nghiên cứu, phiên S279, 13/11/2026 (AA-1098). Người viết: Claude Code (lane nghiên cứu). Chỉ đọc: không sửa
code, không gọi AWS, không chạy lượt trả phí. Thiết kế dùng danh mục này nằm ở
[trang nghiên cứu AA Academy](README.vi.md). Bản gốc tiếng Anh là [inventory.md](inventory.md).

**Cách lập.** Một lượt kiểm kê đã đọc repo gốc, bốn repo app và Infra trên nhánh main: catalog tài liệu, ADR, data
standards, runbook, playbook, template, skill, file steering, hook, tool, workflow và `CONTEXT.md` của từng repo.
Mỗi dòng là một điều một người cần biết, nơi điều đó được viết ra, ai cần nó và module nào dạy nó. Các dòng chỉ lặp
lại dòng khác đã được gộp. Khoảng trống (tri thức chưa có trang nào) nằm ở
[README §2.3](README.vi.md#23-khoảng-trống-chặn-khoá-học), không nằm ở đây.

**241 mục trong 24 lĩnh vực.** [§25](#25-nguồn-bổ-sung-không-tính-vào-241-mục) liệt kê thêm các ADR và nguồn lịch sử làm rõ các mục này nhưng không được tính là mục.

Tên mục trong bảng giữ nguyên tiếng Anh vì đó là tên kỹ thuật dùng thống nhất trong mọi tài liệu (xem bảng thuật
ngữ `docs/glossary.vi.md`).

**Các cột.**

- **Loại**: khái niệm, quyết định, tiêu chuẩn, kỹ thuật, quy trình, quy tắc, runbook, công cụ, sổ đăng ký, mẫu,
  checklist, hướng dẫn, hook, báo cáo, tra cứu, kế hoạch.
- **Nguồn**: nguồn sự thật. Bài học trỏ tới đường dẫn này và không bao giờ chép lại. Khi một đường dẫn có ở nhiều repo, dòng đó
  nêu tên các repo chứa nó ("bốn repo app" là AA-CIS-App, AA-Booking, AA-Partner và AA-TripPlanner-Web).
- **Đối tượng**: E kỹ sư, D kỹ sư trực, T tech lead, S vận hành và hỗ trợ, C người vận hành nội dung, B nhân viên
  booking và tài chính, A chủ đại lý và nhân viên đại lý, O chủ doanh nghiệp, X agent AI (đọc cùng nguồn qua skill),
  "tất cả" cho mọi vai trò.
- **Module**: module dạy mục đó (F nền tảng, E kỹ thuật, L tech lead, S vận hành và hỗ trợ, C nội dung, B booking
  và tài chính, A đại lý, O chủ doanh nghiệp). Danh sách module ở
  [README §3](README.vi.md#3-đối-tượng-và-lộ-trình-học).

## 1. Kiến trúc (12)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Ecosystem architecture (C4 levels 1–2) | khái niệm | `docs/ecosystem-architecture.md` | tất cả | F2 |
| Multi-repo layout and repo roles | khái niệm | `docs/ecosystem-architecture.md` §1; `skill/aa-ecosys-repos/SKILL.md` | E T X | F2 |
| ADR 0001 target architecture | quyết định | `docs/adr/0001-ecosystem-target-architecture.md` | E T | F2 |
| ADR 0019 B2B-only ecosystem model | quyết định | `docs/adr/0019-b2b-only-ecosystem-model.md` | tất cả | F1 |
| ADR 0002 only CIS writes content | quyết định | `docs/adr/0002-only-cis-writes-content.md` | E T | E3 |
| Apps own code, Infra owns resources | tiêu chuẩn | `docs/ecosystem-architecture.md` §4.2; `infra/AA-CIS-Infra/CONTEXT.md` | E D | E10 |
| CONTEXT.md per repo | tiêu chuẩn | `apps/AA-CIS-App/CONTEXT.md` (và mỗi repo); `.kiro/steering/session-workflow.md` | E X | E1 |
| Architecture diagrams as code | kỹ thuật | `docs/architecture/diagrams/README.md` | E T | E1 |
| ADR system, placement and numbering | tiêu chuẩn | `docs/adr/README.md`; `skill/ai-nghiep/references/adr.md`; `tools/adr/check_adr_numbers.py` | E T X | L1 |
| ADR 0008 new-app integration rules and 12-step playbook | quyết định | `docs/adr/0008-new-app-integration-and-data-platform-rules.md`; `docs/adr/0008a-crm-separate-app-exceptions.md` | E T | L8 |
| Tour liveness and retirement propagation (ADR 0015) | quyết định | `docs/adr/0015-tour-liveness-and-retirement-propagation.md` | E | E11 |
| Glossary | tra cứu | `docs/glossary.md`; `docs/glossary.vi.md` | tất cả | F6 |

## 2. Pipeline nội dung CIS (22)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| A-series and T-series model | khái niệm | `apps/AA-CIS-App/CONTEXT.md` (Pipeline stages) | E T C X | C2 |
| A0 upload and raw tours | khái niệm | `apps/AA-CIS-App/CONTEXT.md` §A-series | E C | C2 |
| A1 generic rewrite graph (S1 writer v2) | kỹ thuật | `apps/AA-CIS-App/CONTEXT.md` §A1 | E C | C2 |
| Grounding against the source | kỹ thuật | `apps/AA-CIS-App/CONTEXT.md` §A1 grounding | E C | C3 |
| Day oracle and shadow-then-enforce gates | kỹ thuật | `apps/AA-CIS-App/CONTEXT.md` §A1 day oracle | E C | C3 |
| A2 Review Queue (human in the loop) | khái niệm | `apps/AA-CIS-App/CONTEXT.md` §A2 | E C | C4 |
| A3 Master Content Pool and atomize | khái niệm | `apps/AA-CIS-App/CONTEXT.md` §A3 | E C X | C2 |
| A4 cross-tenant oversight | khái niệm | `apps/AA-CIS-App/CONTEXT.md` §A4 | T C | C2 |
| Segment, score, route and hub rows | khái niệm | `apps/AA-CIS-App/CONTEXT.md` (platform-wide rows) | E | E11 |
| T0 brand identity and brand pack | khái niệm | `apps/AA-CIS-App/CONTEXT.md` §T0 | E A | A2 |
| T1–T4 tenant tour rewrite | khái niệm | `apps/AA-CIS-App/CONTEXT.md` (T-series) | E A | A2 |
| T7 Slate and Debate layer | khái niệm | `apps/AA-CIS-App/CONTEXT.md` §T7 | E A | A2 |
| T8 angle gate, T9 streamed write, place cards | khái niệm | `apps/AA-CIS-App/CONTEXT.md` §T8–T9; `apps/AA-CIS-App/docs/adr/0004-live-writing-progress-via-redis-poll.md` | E A | A2 |
| T10 quality gates (F-codes, F10 near-duplicate check) | khái niệm | `apps/AA-CIS-App/CONTEXT.md` §T10 | E C | C3 |
| T11 publish to WordPress and Facebook | khái niệm | `apps/AA-CIS-App/CONTEXT.md` §T11 | E A | A2 |
| Content quality architecture (ADR 0020) | quyết định | `docs/adr/0020-content-quality-architecture.md` | E T C O | C3 |
| Governed writing memory | quyết định | `apps/AA-CIS-App/docs/adr/0010-governed-writing-memory.md` | E T C | C8 |
| Facts entries (platform and tenant scope) | khái niệm | `apps/AA-CIS-App/CONTEXT.md` (ownership table) | E C | C8 |
| Jev decisions and calibration | kỹ thuật | `apps/AA-CIS-App/docs/adr/0007-jev-verdicts-may-act.md` | E T C | C8 |
| Rerun waves | runbook | `skill/aa-wave-rerun/SKILL.md`; `apps/AA-CIS-App/docs/runbooks/clean-rerun.md` | E T C | C5 |
| Place pipeline in CIS | quyết định | `docs/adr/0007-place-pipeline-in-cis.md` | E C | C6 |
| Photo pipeline | khái niệm | `docs/ecosystem-architecture.md` §4.5 | E C | C6 |

## 3. Nền tảng CIS (6)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Settings registry with operator guides | tiêu chuẩn | `apps/AA-CIS-App/CONTEXT.md` §Settings registry | E T C | C7 |
| Staff roles and permissions | khái niệm | `apps/AA-CIS-App/CONTEXT.md` §Staff roles and permissions | E T S | S2 |
| Tenant control plane and lifecycle | khái niệm | `apps/AA-CIS-App/CONTEXT.md` §Tenant control plane; `docs/contracts/README.md` | E T S | S3 |
| Tenant DB role and RLS context | kỹ thuật | `apps/AA-CIS-App/CONTEXT.md` §Tenant DB role | E | E3 |
| Admin BFF security (write guard, headers, no CORS) | kỹ thuật | `apps/AA-CIS-App/CONTEXT.md` (Architecture at a glance) | E | E5 |
| Admin docs reader `/admin/docs` | công cụ | `docs/README.md` (Admin docs page allowlist); `tools/docs/build_docs_reader.py` | tất cả | F6 |

## 4. Job runner (5)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| One durable job model, one job table per owner | quyết định | `docs/adr/0003-one-durable-job-model.md`; `docs/adr/0003a-per-owner-job-tables.md` | E D | E4 |
| SKIP LOCKED claim, drain and re-claim | kỹ thuật | `docs/architecture/data-standards/03-scaling.md` C6 | E | E4 |
| Job-kind register and kill switches | sổ đăng ký | `docs/ops/job-kinds.md` | D S | E4 |
| Deploy gate and its override | kỹ thuật | `docs/ops/runbooks/deploy-gate-override.md` | E D | E4 |
| No backend merge during an open wave | quy tắc | `skill/aa-wave-rerun/SKILL.md` §3; `skill/aa-ship/SKILL.md` §2 | E X | E4 |

## 5. Nền tảng AI (17)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| AI gateway (ADR 0009) | quyết định | `docs/adr/0009-ai-platform-and-provider-gateway.md`; `docs/architecture/ai-gateway.md` | E T | E6 |
| Registry, stage routes and route control | kỹ thuật | `docs/architecture/ai-gateway.md` §3–4; `docs/generated/llm-routes.md` | E T | E6 |
| Gateway guards and budgets | kỹ thuật | `docs/architecture/ai-gateway.md` §5 | E T | E6 |
| Ledger v2 (`shared.llm_call_log`) | tiêu chuẩn | `docs/architecture/ai-gateway.md` §6 | E T X | E6 |
| Shared core `aa_llm`, vendored and checked | kỹ thuật | `docs/architecture/ai-gateway.md` §7; `tools/llm-core/llm-core-sync.sh` | E | E6 |
| Data scopes per LLM stage | tiêu chuẩn | `apps/AA-CIS-App/docs/adr/0012-llm-data-scopes-per-stage.md` | E T | E6 |
| Writer, judge and validate roles | khái niệm | `docs/glossary.md`; `apps/AA-CIS-App/docs/adr/0008-validate-stages-any-vendor.md` | E | E6 |
| Shadow runs, golden sets and eval regression | kỹ thuật | `apps/AA-CIS-App/docs/llm/eval-runbook.md` | E T | E6 |
| Prompt register | tiêu chuẩn | `apps/AA-CIS-App/docs/llm/prompt-register.md` | E | E6 |
| Provider route order and cross-account invoke | khái niệm | `docs/ecosystem-architecture.md` §4.3; `docs/adr/0001a-retire-acc1-llm-on-acc3-only.md` | E D T | E6 |
| Embeddings and re-embed | runbook | `docs/ops/runbooks/embedding-re-embed.md` | E | E6 |
| Gateway CLI tools | công cụ | `tools/llm/` | E D | E6 |
| AI Use Register | sổ đăng ký | `docs/architecture/ai-use-register.md` | E T | L1 |
| AI boundary for high-risk advice | tiêu chuẩn | `apps/AA-Partner/CONTEXT.md` (AI boundary for high-risk advice) | E A | A6 |
| AI mark on delivered content | tiêu chuẩn | `docs/adr/0020-content-quality-architecture.md` | E A O | A6 |
| LLM access-denied and cost-spike playbooks | runbook | `docs/ops/playbooks/llm-access-denied.md`; `docs/ops/playbooks/llm-cost-spike.md` | D S | E9 |
| Postmortem: LLM account access refusal | báo cáo | `docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md` | D T | E15 |

## 6. TripPlanner (7)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Browse and assembly Lambda split | kỹ thuật | `apps/AA-TripPlanner-Web/CONTEXT.md` §Backend | E | E14 |
| Event-sourced trips | khái niệm | `apps/AA-TripPlanner-Web/CONTEXT.md` §Data model | E | E14 |
| Jobs Lambda and `tripplanner.job` | khái niệm | `apps/AA-TripPlanner-Web/CONTEXT.md` §Jobs Lambda | E D | E14 |
| Guest identity and traveller sign-in | khái niệm | `apps/AA-TripPlanner-Web/CONTEXT.md` §Guest identity | E | E14 |
| Edge shared secret, fail closed | kỹ thuật | `apps/AA-TripPlanner-Web/CONTEXT.md` §Backend | E | E14 |
| Per-visitor AI rate limits | kỹ thuật | `docs/ecosystem-architecture.md` §3.3 | E | E14 |
| TripPlanner runbook | hướng dẫn | `docs/guides/tripplanner-runbook.md` | S O | S2 |

## 7. Booking (12)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Booking stack and bootstrap (ADR 0004) | quyết định | `docs/adr/0004-aa-booking-stack-and-bootstrap.md` | E | E12 |
| Supply content ownership (ADR 0004a) | quyết định | `docs/adr/0004a-supply-content-ownership.md` | E | E12 |
| B2B API `booking.b2b.v1` | khái niệm | `docs/contracts/booking.b2b.v1.openapi.yaml` | E | E12 |
| Booking admin runbook | hướng dẫn | `docs/guides/booking-admin-runbook.md` | B S | B1 |
| Pricing and supplier rates (ADR 0005) | quyết định | `docs/adr/0005-pricing-and-supplier-rates.md` | E B | B2 |
| Price versions and maker-checker | tiêu chuẩn | `docs/adr/0005b-price-versions.md`; `docs/guides/booking-price-setup.md` | E B T | B2 |
| Tour price chain and agency price tiers | khái niệm | `apps/AA-Booking/CONTEXT.md` (Tour price chain, Agency price tiers) | E B | B2 |
| Trip case lifecycle and trip checks | khái niệm | `apps/AA-Booking/CONTEXT.md` §Trip checks | E B | B3 |
| Departures, allotments and booking operations | khái niệm | `apps/AA-Booking/CONTEXT.md` (Agency booking operations) | E B | B3 |
| Supplier bookings, bills and payouts | khái niệm | `apps/AA-Booking/CONTEXT.md` (Supplier bookings, Supplier bills) | E B | B4 |
| Finance: FX-normalised cost, purchase orders, profit | khái niệm | `apps/AA-Booking/CONTEXT.md` §Finance | E B | B5 |
| B2B resale rules (warning below from price, VND quotes) | quyết định | `docs/adr/0005a-b2b-resale-warn-and-vnd.md` | E B | B6 |

## 8. CRM đối tác (13)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| AA-Partner app (ADR 0010) | quyết định | `docs/adr/0010-aa-partner-app.md`; `apps/AA-Partner/CONTEXT.md` | E T | E13 |
| Tenant fair-share gate | kỹ thuật | `apps/AA-Partner/CONTEXT.md` (Tenancy and data rules) | E | E13 |
| Signed client links | kỹ thuật | `apps/AA-Partner/CONTEXT.md` (Route classes) | E | E13 |
| PII scrubber before AI calls | kỹ thuật | `apps/AA-Partner/CONTEXT.md` (F3 PII scrubber) | E | E13 |
| Route classes and identity verifier | kỹ thuật | `apps/AA-Partner/CONTEXT.md` (Route classes) | E | E5 |
| Content studio sign-in by token exchange | quyết định | `docs/adr/0010a-content-studio-partner-sign-in.md` | E | E5 |
| Content studio runbook | hướng dẫn | `docs/guides/content-studio-runbook.md` | A S | A2 |
| CRM modules (pipeline, proposals, invoices, mail, SMS, workflows, reports) | khái niệm | `docs/guides/crm-runbook.md`; `docs/product/partner-crm/prd.md` | E A | A3 |
| Agency users, roles and settings | hướng dẫn | `docs/guides/crm-runbook.md` | A | A7 |
| AA support access windows (L2) and break-glass (L3) | tiêu chuẩn | `apps/AA-Partner/CONTEXT.md` (AA support access) | E S A | S5 |
| Data portability and deletion | khái niệm | `apps/AA-Partner/CONTEXT.md` (Data lifecycle) | E A | A5 |
| Bring-your-own vendor accounts, shared responsibility | quyết định | `docs/research/partner-crm-spec.md` | T A | A5 |
| CRM keys runbook | runbook | `docs/ops/runbooks/crm-keys.md` | D | E9 |

## 9. Định danh (5)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Ecosystem identity on Cognito (ADR 0006) | quyết định | `docs/adr/0006-ecosystem-identity.md` | E D | E5 |
| BFF code flow with PKCE and token checks | kỹ thuật | `docs/ecosystem-architecture.md` §4.6 | E | E5 |
| M2M client credentials with per-receiver scopes | kỹ thuật | `docs/ecosystem-architecture.md` §4.6 | E | E5 |
| Staff directory in CIS (database first, then Cognito) | kỹ thuật | `docs/ecosystem-architecture.md` §4.6 | E S | S2 |
| Cognito login playbook | runbook | `docs/ops/playbooks/cognito-login.md` | D S | S4 |

## 10. Nền tảng dữ liệu (19)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Shared RDS, one owner per schema | tiêu chuẩn | `docs/database/schema-ownership.md` | E D X | E3 |
| Data standards: the 20 golden rules | tiêu chuẩn | `docs/architecture/data-standards/README.md` | E T | E3 |
| Naming, types and keys | tiêu chuẩn | `docs/architecture/data-standards/01-engineering.md` §1–2 | E | E3 |
| Migration mechanics and the MIG-4 flow | tiêu chuẩn | `docs/architecture/data-standards/01-engineering.md` §3 | E X | E3 |
| Expand/contract migrations with auto-apply (ADR 0017) | quyết định | `docs/adr/0017-migrations-in-app-pr-expand-auto-apply.md` | E D | E3 |
| DB Migrate workflow | runbook | `docs/ops/runbooks/db-migrate.md` | E D | E3 |
| Roles, grants and the RLS template | tiêu chuẩn | `docs/architecture/data-standards/01-engineering.md` §4 | E | E3 |
| Contract views, versioning and the contracts registry | tiêu chuẩn | `docs/architecture/data-standards/01-engineering.md` §5; `docs/contracts/README.md`; `tools/contracts/check_contracts.py` | E | E3 |
| Outbox, pull job, inbox | kỹ thuật | `docs/architecture/data-standards/01-engineering.md` (CON-7) | E | E3 |
| Query rules and the SQL PR checklist | tiêu chuẩn | `docs/architecture/data-standards/01-engineering.md` §6–8 | E | E3 |
| Generated schema reference and ERD | công cụ | `docs/architecture/db-schema-reference.md`; `docs/architecture/erd/` | E X | E3 |
| Schema gotchas | khái niệm | `.kiro/steering/db-schema.md`; `skill/aa-cis-schema/SKILL.md` | E X | E3 |
| Retention and archival | tiêu chuẩn | `docs/architecture/data-standards/02-data-management.md` §7; `docs/legal/retention-log.md` | E T | E3 |
| Dead Table Registry | sổ đăng ký | `docs/architecture/dead-table-registry.md` | E | E3 |
| Isolation probe | runbook | `docs/ops/runbooks/isolation-probe.md` | E T | E3 |
| Data management: ownership, catalog, quality, lineage | tiêu chuẩn | `docs/architecture/data-standards/02-data-management.md` §1–5 | E T | L1 |
| PII classes and privacy rules | tiêu chuẩn | `docs/architecture/data-standards/02-data-management.md` §6 | tất cả | F4 |
| Destructive operations: DRY RUN first | runbook | `skill/aa-cis-schema/references/destructive-ops.md` | E D T | E9 |
| ECS exec through S3 | runbook | `docs/ops/runbooks/ecs-exec-s3-mediated.md`; `tools/ecs/ecsx.sh` | E D | E9 |

## 11. Mở rộng và độ tin cậy (6)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| SLOs and SLIs | tiêu chuẩn | `docs/architecture/data-standards/03-scaling.md` C1 | D T | E9 |
| Connection budget | tiêu chuẩn | `docs/architecture/data-standards/03-scaling.md` C2 | E D | E10 |
| Postgres maintenance | tiêu chuẩn | `docs/architecture/data-standards/03-scaling.md` C5 | D | E10 |
| Scale on a measured trigger, cheapest lever first | kỹ thuật | `docs/architecture/data-standards/03-scaling.md` C3, C9 | E T | L7 |
| Environment and account model (ADR 0012, ADR 0018) | quyết định | `docs/adr/0012-environment-model.md`; `docs/adr/0018-lean-aws-account-model.md` | T O | L7 |
| Monthly capacity review | runbook | `docs/templates/capacity-review.md` | D T | L5 |

## 12. Hạ tầng (11)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Terraform roots, state and drift check | khái niệm | `infra/AA-CIS-Infra/CONTEXT.md` | E D | E10 |
| Terraform apply only through the workflow | quy tắc | `skill/aa-ship/SKILL.md` §2 | E D X | E10 |
| Edge path: API Gateway, VPC link, load balancers, CloudFront, WAF | khái niệm | `docs/ecosystem-architecture.md` §2, §4.1 | E D | E10 |
| ECS Fargate services and immutable image tags | khái niệm | `docs/ecosystem-architecture.md` §4.2 | E D | E10 |
| Per-app security groups (ADR 0004b) | quyết định | `docs/adr/0004b-per-app-security-groups.md` | D | E10 |
| GitHub OIDC, one role per repo and job | kỹ thuật | `docs/ecosystem-architecture.md` §5 | D T | E10 |
| Generated infra references | công cụ | `docs/generated/` | E D | E10 |
| Environment config register (names only) | tiêu chuẩn | `docs/generated/env-config.md` | E D | E10 |
| Tagging standard | tiêu chuẩn | `docs/architecture/tagging-standard.md` | E D | F5 |
| Onboarding: accounts and access | hướng dẫn | `docs/onboarding.md` | E D S | E1 |
| SES mail and bounces | runbook | `docs/ops/runbooks/ses-bounce.md` | D S | S4 |

## 13. Thực hành kỹ thuật (19)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Operating model: Kanban, trunk-based, ADLC | khái niệm | `docs/engineering-handbook.md` §2.1 | tất cả | F3 |
| The 12-stage lifecycle | tiêu chuẩn | `docs/engineering-handbook.md` §3 | tất cả | F3 |
| Roles and agent control | tiêu chuẩn | `docs/engineering-handbook.md` §2.3; `docs/agents.md` | E T X | F3 |
| Definition of Ready and Definition of Done | tiêu chuẩn | `docs/templates/definition-of-ready.md`; `skill/aa-ship/SKILL.md` | E T X | F3 |
| Engineering handbook | hướng dẫn | `docs/engineering-handbook.md` | E T | F3 |
| Ship process from PR to Done | runbook | `skill/aa-ship/SKILL.md` | E X | E2 |
| Merge queue and ship tools | công cụ | `tools/github/README.md` | E X | E2 |
| Conventional commits with a Refs line | tiêu chuẩn | `docs/engineering-handbook.md` §5.1 | E X | E2 |
| PR template as change record | tiêu chuẩn | `.github/pull_request_template.md` | E | E2 |
| Pre-push hook | công cụ | `scripts/pre-push.sh` (bốn repo app) | E X | E2 |
| Code-health and coverage ratchets | kỹ thuật | `.github/scripts/code_health.py` (bốn repo app); `.github/scripts/coverage_ratchet.py` (chỉ AA-CIS-App) | E T | E2 |
| CI pipeline per repo | công cụ | `.github/workflows/ci.yml` (bốn repo app); repo gốc: `docs-lint.yml`, `contracts.yml`, `workflow-lint.yml`, `pr-title.yml` (không có `ci.yml`); Infra: `terraform-plan.yml`, `docs-lint.yml`, các guard migration | E D | E2 |
| Release-please and immutable images | kỹ thuật | `docs/engineering-handbook.md` §5.2–5.3 | E D | E2 |
| Post-deploy verify and the health contract | kỹ thuật | `.github/workflows/post-deploy-verify.yml` (bốn repo app) | E D | E2 |
| Feature flags register | tiêu chuẩn | `docs/ops/feature-flags.md` | E D | E2 |
| API contract diff | công cụ | `.github/workflows/api-contract.yml` (AA-CIS-App và AA-Booking) | E | E2 |
| Implementation notes per issue | mẫu | `docs/implementation-notes/` | E X | E2 |
| Secret scanning | công cụ | `.github/workflows/secret-scan.yml` (repo gốc, Infra và bốn repo app) | E X | E2 |
| Cost line in every PR | quy tắc | `skill/aa-ship/SKILL.md` §1 | E X | E2 |

## 14. Frontend (4)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| One design system, guarded kit copies (ADR 0016) | quyết định | `docs/adr/0016-one-design-system-guarded-kit-copies.md`; `tools/kit/kit-sync.sh` | E X | E7 |
| Next.js BFF pattern | kỹ thuật | `docs/ecosystem-architecture.md` §4.1 | E | E7 |
| Vendored copy guards (identity verifier, `aa_llm`, kit) | kỹ thuật | `tools/kit/`; `tools/llm-core/` | E | E7 |
| UI verification before Done | runbook | `skill/aa-ui-verify/SKILL.md` | E X | E7 |

## 15. Kiểm thử (3)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| UI smoke, visual regression and signed-in E2E | công cụ | `.github/workflows/visual.yml` (bốn repo app); `ui-smoke.yml` và `e2e-cognito.yml` (AA-CIS-App); `ui-smoke-portal.yml` (AA-Partner) | E | E8 |
| Nightly integration tests | công cụ | `apps/AA-CIS-App/.github/workflows/nightly-integration.yml` | E | E8 |
| UAT harness and videos | công cụ | `tools/uat/build.py`; `skill/aa-uat-video/SKILL.md`; `docs/templates/uat-report.md` | E T O | E8 |

## 16. Quan sát và vận hành (12)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Observability baseline and alarm on symptoms | tiêu chuẩn | `docs/engineering-handbook.md` §7.1 | E D | E9 |
| Structured logs with request ids | tiêu chuẩn | `apps/AA-Booking/CONTEXT.md`; `apps/AA-TripPlanner-Web/CONTEXT.md` | E | E9 |
| Alarm catalog with runbook links | sổ đăng ký | `docs/generated/alarms.md`; `tools/docs/check_alarm_runbooks.py` | D | E9 |
| Operations index and symptom table | hướng dẫn | `docs/ops/README.md` | D S | S1 |
| Incident response and postmortems | quy trình | `docs/ops/incident-response.md`; `docs/ops/postmortems/README.md`; `docs/templates/postmortem.md` | D S T | S1 |
| Playbooks by symptom (5xx spike, queue stuck) | runbook | `docs/ops/playbooks/5xx-spike.md`; `docs/ops/playbooks/queue-stuck.md` | D S | E9 |
| Rollback runbooks and the rollback game day | runbook | `docs/ops/runbooks/rollback-ecs.md` (và các trang rollback khác); `docs/ops/drills/rollback-game-day.md` | D | E9 |
| Backup, point-in-time restore and restore drills | runbook | `docs/ops/runbooks/restore-rds-pitr.md`; `docs/ops/drills/README.md` | D | E9 |
| Break-glass | runbook | `docs/ops/runbooks/break-glass.md` | D T | E9 |
| Runbook "tested" rule | tiêu chuẩn | `docs/STYLE.md` (Runbooks and tested) | E D | E9 |
| Pilot agency onboarding and rehearsal | runbook | `docs/ops/runbooks/pilot-agency-onboarding.md`; `docs/ops/runbooks/pilot-rehearsal.md` | T S | S3 |
| App access and operations index | hướng dẫn | `docs/guides/app-access-and-operations.md` | S C B O | S2 |

## 17. Bảo mật (8)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Security baseline | checklist | `docs/security/baseline.md` | D T | L9 |
| Secrets register and rotation | sổ đăng ký | `docs/security/secrets-register.md`; `docs/ops/runbooks/secret-rotation.md` | D T | E5 |
| Vulnerability management | quy trình | `docs/security/vulnerability-management.md` | E T | L9 |
| Quarterly access review | mẫu | `docs/templates/access-review.md` | T S | L9 |
| CI/CD hygiene and org security (ADR 0021) | quyết định | `docs/adr/0021-github-org-security-and-ci-hygiene.md`; `tools/github/ci_hygiene.py` | D T | L9 |
| Public-repo safe writing | tiêu chuẩn | `docs/STYLE.md` (Where a page may live); `docs/adr/0014-repo-visibility-and-github-plan.md` | tất cả | F4 |
| Compliance and privacy register (DPA, sub-processors, DSAR) | sổ đăng ký | `docs/legal/register.md`; `docs/legal/readiness-packet.md` | T O | O5 |
| Tenant AI schedule and DPA pack | mẫu | `docs/legal/tenant-ai-schedule.md`; `docs/legal/dpa.md` | A O | A5 |

## 18. Chi phí và FinOps (8)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| FinOps process | tiêu chuẩn | `docs/ops/finops.md` | T O | F5 |
| Cost ledgers for every paid call | tiêu chuẩn | `docs/architecture/data-standards/02-data-management.md` §10 | E | F5 |
| Quote the cost and get a yes per paid item | quy tắc | `docs/ops/finops.md`; `docs/architecture/data-standards/02-data-management.md` DM-10.7 | E T X | F5 |
| Paid-run ladder (trial, then a small batch) | quy tắc | `docs/architecture/data-standards/02-data-management.md` DM-10.6 | E T C | F5 |
| Cost estimate before a paid run | công cụ | `tools/llm/cost_estimate.py`; `tools/llm/spend_by_stage.py` | E T C | C5 |
| Cost Operations page and nightly reconcile | công cụ | `docs/ecosystem-architecture.md` §4.4 | T B O | O3 |
| Monthly cost report | công cụ | `docs/ops/cost/README.md`; `tools/finops/monthly_cost_report.py`; `docs/templates/cost-report.md` | T O | L5 |
| AI providers and reports runbook | hướng dẫn | `docs/guides/ai-providers-and-reports-runbook.md` | T O | L5 |

## 19. Tài liệu (8)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Docs-as-code and the role catalog | tiêu chuẩn | `docs/README.md`; `docs/engineering-handbook.md` §4 | tất cả | F6 |
| Style guide, front matter and docs lint | tiêu chuẩn | `docs/STYLE.md`; `tools/docs/check_frontmatter.py` | E X | F6 |
| Language rule and `.vi.md` translations | quy tắc | `.kiro/steering/language-convention.md`; `docs/STYLE.md` (Language) | tất cả | F6 |
| What fact lives where | tiêu chuẩn | `docs/engineering-handbook.md` §4.9 | E X | F6 |
| Templates | mẫu | `docs/templates/` | E T | F6 |
| Role guides | hướng dẫn | `docs/guides/cto.md`, `cio.md`, `pm.md`, `devops.md` | T O | F1 |
| PRD as code | tiêu chuẩn | `docs/product/README.md`; `tools/docs/check_prd_refs.py` | E T | L4 |
| Audits folder and artifact registry | tiêu chuẩn | `docs/audits/`; `docs/artifacts/README.md` | T X | L3 |

## 20. Vận hành agent (11)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Agent instruction stack | khái niệm | `docs/agents.md`; `docs/llms.txt`; `.kiro/steering/` | T X | L3 |
| Session ritual and live checklist | runbook | `skill/aa-session/SKILL.md`; `.kiro/steering/session-workflow.md` | T X | L3 |
| State snapshot before any log | checklist | `skill/aa-session/SKILL.md` (cuối phiên, bước 2) | T X | L3 |
| Parallel code lanes | công cụ | `tools/workflows/lane.js`; `skill/aa-session/references/parallel-lanes.md` | T X | L3 |
| Orchestrator and subagent rights | quy tắc | `skill/ai-nghiep/SKILL.md` §3 | T X | L3 |
| Task handoff template | mẫu | `skill/ai-nghiep/references/handoff-prompt.md` | T X | L3 |
| Kiro delegation mode | quy trình | `.claude/skills/kiro-delegate/SKILL.md` | T X | L3 |
| Skill set maintenance | quy trình | `skill/README.md`; `skill/REVIEW-CHECKLIST.md` | T | L3 |
| Subagent and shell guard hooks | hook | `.claude/hooks/`; `.claude/settings.json` | T X | L3 |
| Agents never toggle infrastructure | quy tắc | `skill/ai-nghiep/SKILL.md` §2 | T X | L3 |
| Scheduled guard watch | công cụ | `tools/github/guard_runs.py` | D T | L9 |

## 21. Kế hoạch và issue (9)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Living backlog | sổ đăng ký | `docs/backlog/README.md` | T X | L4 |
| Master plan tracker and plan sync | công cụ | `docs/backlog/tracker/README.md`; `tools/linear/plan_sync.py` | T | L4 |
| Session size, pick order and WIP cap | quy tắc | `skill/aa-session/SKILL.md` (đầu phiên, bước 3) | T X | L4 |
| Platform roadmap and the "do not do now" list | sổ đăng ký | `docs/engineering-handbook.md` §9 | T O | L4 |
| Linear issue standard and template | runbook | `skill/aa-linear-issue/SKILL.md` | T X | L4 |
| Linear Free-plan quota, export and archive | quy tắc | `skill/aa-linear-issue/SKILL.md`; `tools/linear/linear_export.py` | T X | L4 |
| Done audit at session end | công cụ | `tools/linear/done_audit.py` | T X | L4 |
| Frozen Done-when and Done-with-scope | quy tắc | `skill/aa-ship/SKILL.md` §4 | T X | L4 |
| Milestones from the ADR 0019 phases | kế hoạch | `docs/backlog/tracker/plan.json` | T O | O6 |

## 22. Quản trị và kiểm soát thay đổi (13)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Source precedence | quy tắc | `docs/engineering-handbook.md` §1.3; `docs/agents.md` | tất cả | F3 |
| Hard rules: verify, root cause first | quy tắc | `skill/ai-nghiep/SKILL.md` §2 | tất cả | F3 |
| Technology selection frame | tiêu chuẩn | `skill/ai-nghiep/references/adr.md` | T | L1 |
| Locked decisions | sổ đăng ký | `docs/adr/README.md` | T X | L1 |
| Tech-lead decision log | sổ đăng ký | `docs/engineering-handbook.md` §10 | T | L1 |
| Changing the handbook and the standards | quy trình | `docs/engineering-handbook.md` §1.4 | T | L1 |
| Merge rights by phase | quyết định | `docs/architecture/data-standards/02-data-management.md` DM-11.5 | E T | L2 |
| Who approves what | sổ đăng ký | `docs/architecture/data-standards/02-data-management.md` §11 | E T | L2 |
| Risk classes and independent agent review | quy trình | `docs/templates/definition-of-ready.md`; `.claude/agents/kiro-reviewer.md` | E T X | L2 |
| GitHub App identity for agents (ADR 0011) | quyết định | `docs/adr/0011-github-app-identity-and-merge-rights.md`; `docs/security/github-apps.md` | D T | L2 |
| Maker-checker in business data | quy tắc | `docs/adr/0005b-price-versions.md`; `docs/guides/booking-admin-runbook.md` | B T | B2 |
| No self-evaluation as evidence | quy tắc | `skill/ai-nghiep/SKILL.md` §2 | E C X | C3 |
| Decision pages with proposed answers | quy tắc | `skill/aa-session/SKILL.md` | T X | L6 |

## 23. Bên liên quan và nhà cung cấp (7)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Jira: draft, approve, post | quy tắc | `skill/aa-jira-update/SKILL.md` | T X | L6 |
| Jira structure: app epics and the weekly report | tiêu chuẩn | `skill/aa-jira-update/SKILL.md` | T O | O2 |
| Business or technical decision split | quy tắc | `skill/aa-jira-update/SKILL.md` | T O | L6 |
| Stakeholder voice guide and vendor handling | hướng dẫn | `skill/ai-nghiep/references/stakeholders-english.md` | T | L6 |
| Report and KPI registries | sổ đăng ký | `docs/reports/catalog.yaml`; `docs/reports/kpis.yaml` | T O | O2 |
| Release notes | mẫu | `docs/templates/release-note.md` | T O | O2 |
| CEO guide | hướng dẫn | `docs/guides/ceo.md`; `docs/guides/ceo.vi.md` | O | O1 |

## 24. Bài học (4)

| Mục | Loại | Nguồn | Đối tượng | Module |
|---|---|---|---|---|
| Lesson log with a guard field | quy trình | `skill/aa-lessons/SKILL.md`; `tools/docs/check_lessons.py` | E T X | E15 |
| Lessons become guard tests | quy trình | `skill/aa-lessons/guards.md` | E X | E15 |
| New engineer learning path | hướng dẫn | `docs/guides/new-engineer.md` | E | E1 |
| CIS admin runbook | hướng dẫn | `docs/guides/cis-admin-runbook.md` | C S | C1 |

## 25. Nguồn bổ sung (không tính vào 241 mục)

Các nguồn này được nêu tên để người phụ trách module tìm ra. Chúng không phải là mục kiến thức mới: mỗi nguồn làm rõ
một mục ở trên, hoặc là nguồn cho ví dụ thực tế.

### 25.1 ADR chưa được nêu tên ở các dòng trên

| ADR | Nguồn | Làm rõ | Module |
|---|---|---|---|
| Root 0006a identity phase 1 amendments | `docs/adr/0006a-identity-phase1-amendments.md` | Định danh (§9) | E5, S2 |
| Root 0006b partner pool and MFA | `docs/adr/0006b-partner-pool-and-mfa.md` | Định danh (§9); đại lý đăng nhập có MFA | E5, S4, A1 |
| Root 0011a CI bot merges copy and dump PRs | `docs/adr/0011a-ci-bot-merges-copy-and-dump-prs.md` | Quyền merge (§22); luồng migration (§10) | E3, L2 |
| Root 0017a Dev auto-applies contract migrations | `docs/adr/0017a-dev-auto-applies-contract-migrations.md` | Luồng migration (§10) | E3 |
| CIS 0001 atoms platform-wide, segments per tenant | `apps/AA-CIS-App/docs/adr/0001-atoms-platform-wide-segments-per-tenant.md` | Pipeline nội dung CIS (§2) | E11 |
| CIS 0002 search demand shared across tenants | `apps/AA-CIS-App/docs/adr/0002-search-demand-shared-across-tenants.md` | Pipeline nội dung CIS (§2) | E11 |
| CIS 0003 segment, score, route and hub become platform-wide | `apps/AA-CIS-App/docs/adr/0003-segment-score-route-hub-will-become-platform-wide.md` | Pipeline nội dung CIS (§2) | E11 |
| CIS 0005 model catalog and Converse adapter | `apps/AA-CIS-App/docs/adr/0005-model-catalog-and-converse-adapter.md` | Nền tảng AI (§5) | E6 |
| CIS 0006 stage routes, fallback and shadow | `apps/AA-CIS-App/docs/adr/0006-stage-routes-fallback-and-shadow.md` | Nền tảng AI (§5) | E6 |
| CIS 0009 F17 owns offered moments | `apps/AA-CIS-App/docs/adr/0009-f17-owns-offered-moments-promises-gate-dropped.md` | Cổng chất lượng (§2) | C3 |
| CIS 0011 T9 FAQ question filter step | `apps/AA-CIS-App/docs/adr/0011-t9-faq-question-filter-llm-step.md` | T-series (§2) | E11 |
| Booking 0001 implements root ADR 0004 | `apps/AA-Booking/docs/adr/0001-implements-root-0004.md` | Booking (§7) | E12 |
| Partner 0001 implements root ADR 0010 | `apps/AA-Partner/docs/adr/0001-implements-root-0010.md` | Partner CRM (§8) | E13 |

### 25.2 Nguồn lịch sử cho ví dụ thực tế

| Nguồn | Ở đâu | Bài học lấy được gì | Module | Quy tắc dùng |
|---|---|---|---|---|
| Log phiên làm việc | `docs/sessions/` (tiếng Việt, có mục lục) | Một quyết định hay sự cố đã diễn ra thế nào trong một phiên thật | E15, L3, L4 | Trích làm ví dụ thực tế, kèm tóm tắt tiếng Anh trong bài; không bao giờ là nguồn của một quy tắc |
| Bản xuất Linear các issue đã đóng | `docs/linear-export/` | Issue đạt chuẩn Ready và bằng chứng đã dùng để đóng | E2, L4 | Chọn ví dụ thể hiện DoR và "Done = đã kiểm live" |
| Lịch sử Jira (epic theo app, báo cáo tuần) | Ngoài repo, đọc qua connector Jira | Cách báo tiến độ cho chủ doanh nghiệp | L6, O2 | Chỉ lộ trình nhân viên; tóm tắt, không chép nội dung Jira vào repo công khai |
| Audit | `docs/audits/` | Cách chạy và báo cáo một audit | L3, L9 | Đã là một mục ở §19; liệt kê lại ở đây như nguồn ví dụ |
| Postmortem | `docs/ops/postmortems/` | Vấn đề, nguyên nhân, cách sửa | E15, S1 | Đã là mục ở §5 và §16 |
