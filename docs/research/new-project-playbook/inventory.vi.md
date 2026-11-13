---
id: CAT-01-research-playbook-inventory
title: Danh mục thực hành cho playbook dự án mới
description: Mọi thực hành AA mà bộ kit dự án mới dùng lại được, kèm nguồn và điều bản chung phải đổi (nghiên cứu AA-1099).
type: reference
status: draft
owner: nghiep
audience: [cto, engineer, pm, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-13
review_every_days: 90
lang: vi
translation_of: docs/research/new-project-playbook/inventory.md
related: [CAT-01-research-playbook, CAT-01, AA-1099, AA-1098]
---

# Danh mục thực hành cho playbook dự án mới

Nghiên cứu cho AA-1099, S279, 13/11/2026. Đi kèm [bản nghiên cứu playbook](README.vi.md). Mỗi dòng được đọc từ
đường dẫn nguồn nó trích. Ngày 13/11/2026 đã kiểm đường dẫn repo gốc có trên `master`, đường dẫn app hoặc Infra có
trên `origin/main` của từng repo.

**Lớp**

- **G**: dùng chung. Dùng nguyên trong bộ kit.
- **P**: mẫu chung nhưng gắn với AA. Bộ kit giữ mẫu, đổi tên, đường dẫn và công cụ thành tham số.
- **A**: riêng AA. Ở lại phần AA; là học liệu LMS (AA-1098), không phải nội dung bộ kit.

Repo app và Infra là repo riêng, nên đường dẫn của chúng ghi dạng code, không phải link.

| Phần | Số dòng | G | P | A |
|---|---|---|---|---|
| Kỹ thuật | 85 | 47 | 33 | 5 |
| Quy trình | 34 | 23 | 11 | 0 |
| Quản trị | 24 | 21 | 3 | 0 |
| Quản lý | 18 | 10 | 8 | 0 |
| **Tổng** | **161** | **101** | **55** | **5** |

**Cách xếp phạm vi.** AA-1099 xếp "DRY RUN" vào quy trình và "chuẩn dữ liệu" vào quản trị. Danh mục này xếp chúng
theo nguồn, mà nguồn là tài liệu kỹ thuật: T43 (DRY RUN cho thao tác xoá) và T35, T36, T38 (chuẩn dữ liệu). Mỗi dòng
chỉ đếm một lần, ở phần Kỹ thuật. Tham chiếu chéo: T43 cũng thuộc Quy trình (nó là một thủ tục thay đổi), còn T35, T36
và T38 cũng thuộc Quản trị (chúng là chuẩn bắt buộc, có phiên bản và người duyệt).

## Kỹ thuật

### Kiến trúc

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T1 | Kiến trúc hệ sinh thái, C4 mức 1-2, dữ kiện đánh dấu [FACT] / [TO CONFIRM] | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) | P | Thành canvas arc42 cùng ba hình C4: ngữ cảnh, container, triển khai. Giữ dấu FACT / TO CONFIRM. |
| T2 | Bố cục nhiều repo: mỗi repo app tự deploy; repo gốc giữ tài liệu, ADR, hợp đồng và công cụ | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §1<br>[`skill/aa-ecosys-repos/SKILL.md`](../../../skill/aa-ecosys-repos/SKILL.md) | P | Câu hỏi Copier: một repo hay repo gốc + repo app. Kèm khung repo gốc (docs/, contracts/, tools/). |
| T3 | App chỉ giao code, Infra tạo mọi tài nguyên cloud (zip giữ chỗ, bỏ qua thay đổi code) | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §4.2<br>`infra/AA-CIS-Infra/CONTEXT.md` | G | Chép nguyên luật. Scaffold kèm thư mục infra dùng mẫu zip giữ chỗ. |
| T4 | Sơ đồ kiến trúc dạng code (Python diagrams kèm bản Mermaid) | [`docs/architecture/diagrams/README.md`](../../../docs/architecture/diagrams/README.md) | G | Mặc định dùng Mermaid; bộ vẽ Python là tuỳ chọn. |
| T5 | CONTEXT.md cho từng repo, đọc trước khi thiết kế và cập nhật khi đổi ranh giới | `apps/AA-CIS-App/CONTEXT.md`<br>[`.kiro/steering/session-workflow.md`](../../../.kiro/steering/session-workflow.md) | P | Mẫu theo các đề mục arc42, có trần dung lượng; file của CIS khoảng 530 KB nên phải tách thành trang theo module. |
| T6 | Hệ ADR: đặt theo phạm vi ảnh hưởng, số do CI kiểm, bản sửa NNNNa | [`docs/adr/README.md`](../../../docs/adr/README.md)<br>[`skill/ai-nghiep/references/adr.md`](../../../skill/ai-nghiep/references/adr.md)<br>[`tools/adr/check_adr_numbers.py`](../../../tools/adr/check_adr_numbers.py) | G | Dùng dạng MADR tối giản. Thêm bước dọn / thay thế để ADR cũ không làm agent hiểu sai. |
| T7 | Mỗi thực thể chỉ một bên ghi; app khác đọc qua hợp đồng (ADR 0002) | [`docs/adr/0002-only-cis-writes-content.md`](../../../docs/adr/0002-only-cis-writes-content.md) | P | Viết thành luật dữ liệu chung; ví dụ nội dung tour giữ ở phần AA. |
| T8 | Cổng quyết định app mới và playbook 12 bước (ADR 0008) | [`docs/adr/0008-new-app-integration-and-data-platform-rules.md`](../../../docs/adr/0008-new-app-integration-and-data-platform-rules.md) | P | Thành checklist của pha Setup; tên schema, role, pool thành chỗ điền. |
| T9 | Ngừng một thực thể bằng một trạng thái, tombstone và view outbox (ADR 0015) | [`docs/adr/0015-tour-liveness-and-retirement-propagation.md`](../../../docs/adr/0015-tour-liveness-and-retirement-propagation.md) | P | Trang mẫu chung trong pha Retire. |
| T10 | Mô hình môi trường và tài khoản gọn: hai môi trường, prod chỉ dựng khi có ngày go-live | [`docs/adr/0012-environment-model.md`](../../../docs/adr/0012-environment-model.md)<br>[`docs/adr/0018-lean-aws-account-model.md`](../../../docs/adr/0018-lean-aws-account-model.md) | G | Mặc định của bộ kit; bảng tài khoản AA giữ ở phần AA. |
| T11 | Thuật ngữ hai thứ tiếng | [`docs/glossary.md`](../../../docs/glossary.md) | P | Kèm thuật ngữ SDLC / ADLC / vận hành; mỗi dự án tự thêm thuật ngữ nghiệp vụ. |

### Nghiệp vụ (sản phẩm AA)

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T12 | Pipeline nội dung CIS A0-A4 và T0-T11, atom, slate, pipeline địa điểm và ảnh | `apps/AA-CIS-App/CONTEXT.md`<br>[`docs/adr/0019-b2b-only-ecosystem-model.md`](../../../docs/adr/0019-b2b-only-ecosystem-model.md) | A | Không vào bộ kit. Là học liệu cho LMS (AA-1098). |
| T13 | Nghiệp vụ Booking và Partner: giá, giá nhà cung cấp, hồ sơ chuyến, các module CRM | `apps/AA-Booking/CONTEXT.md`<br>`apps/AA-Partner/CONTEXT.md`<br>[`docs/adr/0005b-price-versions.md`](../../../docs/adr/0005b-price-versions.md) | A | Không vào bộ kit. Maker-checker và phiên bản giá chuyển sang phần quản trị thành luật chung. |
| T14 | Vòng viết, kiểm, sửa bằng AI có đối chiếu nguồn (A1, ADR 0020) | `apps/AA-CIS-App/CONTEXT.md` §A1<br>[`docs/adr/0020-content-quality-architecture.md`](../../../docs/adr/0020-content-quality-architecture.md) | P | Trang mẫu chung: một sổ chính sách, một fact sheet, cổng đo được, một hợp đồng đầu ra. |
| T15 | Chạy bóng rồi mới cưỡng chế: kiểm tra tự động mới chỉ có hiệu lực sau khi đo độ chính xác | `apps/AA-CIS-App/CONTEXT.md` §A1 | G | Luật chung cho mọi cổng mới; ngưỡng thành một setting. |
| T16 | Hàng đợi người duyệt cho bản ghi trượt kiểm tra tự động | `apps/AA-CIS-App/CONTEXT.md` §A2 | G | Trang mẫu. |
| T17 | Giám khảo AI đã hiệu chuẩn: phán quyết chỉ có hiệu lực sau khi hiệu chuẩn trên mẫu gán nhãn | `apps/AA-CIS-App/docs/adr/0007-jev-verdicts-may-act.md` | P | Luật chung; nhà cung cấp giữ ở phần AA. |

### Nền tảng

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T18 | Sổ setting: mọi ngưỡng, giới hạn, trần sửa được trên trang admin, mỗi khoá có hướng dẫn | `apps/AA-CIS-App/api/services/settings_registry.py`<br>`apps/AA-CIS-App/CONTEXT.md` | P | Scaffold kèm bảng, khung trang admin và guard CI chặn hằng số mới. |
| T19 | Vai trò nhân viên lấy từ nhóm định danh; luật trang cưỡng chế ở proxy và API | `apps/AA-CIS-App/CONTEXT.md` | P | Mẫu ma trận vai trò, không phụ thuộc nhà cung cấp. |
| T20 | Control plane tenant, vòng đời, role DB có ngữ cảnh RLS đóng khi lỗi | `apps/AA-CIS-App/CONTEXT.md`<br>[`docs/architecture/data-standards/01-engineering.md`](../../../docs/architecture/data-standards/01-engineering.md) §4 | P | Câu hỏi Copier: đa tenant có hay không. Có thì thêm mẫu RLS bật FORCE từ ngày đầu. |
| T21 | Bảo mật BFF: chặn ghi chéo site, sáu header bảo mật, không cấp CORS | `apps/AA-CIS-App/CONTEXT.md` | G | Có sẵn trong khung web. |
| T22 | Định danh: mỗi đối tượng một pool, định danh = (iss, sub), BFF code + PKCE, token máy theo scope | [`docs/adr/0006-ecosystem-identity.md`](../../../docs/adr/0006-ecosystem-identity.md)<br>[`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §4.6 | P | Checklist định danh không phụ thuộc nhà cung cấp; Cognito là cấu hình AA. |
| T23 | Secret chung ở edge, đóng khi lỗi; mỗi tiền tố route một loại token; link khách hàng băm | `apps/AA-TripPlanner-Web/CONTEXT.md`<br>`apps/AA-Partner/CONTEXT.md` | G | Thành mục mẫu trong security baseline. |
| T24 | Cổng chia phần công bằng giữa tenant (chống hàng xóm ồn) | `apps/AA-Partner/CONTEXT.md` | G | Thuộc tuỳ chọn đa tenant. |

### Bộ chạy job

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T25 | Một mô hình job bền, mỗi chủ một bảng job, nhận việc SKIP LOCKED, xả và nhận lại khi deploy | [`docs/adr/0003-one-durable-job-model.md`](../../../docs/adr/0003-one-durable-job-model.md)<br>[`docs/adr/0003a-per-owner-job-tables.md`](../../../docs/adr/0003a-per-owner-job-tables.md)<br>[`docs/architecture/data-standards/03-scaling.md`](../../../docs/architecture/data-standards/03-scaling.md) C6 | G | Scaffold kèm mẫu DDL và vòng lặp worker. |
| T26 | Sổ loại job có công tắc dừng; cổng deploy chỉ chờ loại job chặn | [`docs/ops/job-kinds.md`](../../../docs/ops/job-kinds.md)<br>[`docs/ops/runbooks/deploy-gate-override.md`](../../../docs/ops/runbooks/deploy-gate-override.md) | P | Mẫu sổ và endpoint cổng deploy trong scaffold. |

### Nền tảng AI

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T27 | Cổng AI: một điểm đi qua cho mọi lệnh gọi AI/dữ liệu trả phí, route có dự phòng, ngân sách, cầu dao | [`docs/adr/0009-ai-platform-and-provider-gateway.md`](../../../docs/adr/0009-ai-platform-and-provider-gateway.md)<br>[`docs/architecture/ai-gateway.md`](../../../docs/architecture/ai-gateway.md) | P | Câu hỏi Copier: có tính năng AI không. Có thì vendor lõi gateway kèm guard đồng bộ. |
| T28 | Mỗi lần gọi một dòng sổ cái, kể cả bị từ chối và lỗi; script tay gắn stage adhoc_<issue> | [`docs/architecture/ai-gateway.md`](../../../docs/architecture/ai-gateway.md) §6<br>[`.kiro/steering/session-workflow.md`](../../../.kiro/steering/session-workflow.md) | G | Luật bắt buộc cho mọi lệnh gọi trả phí. |
| T29 | Phạm vi dữ liệu theo stage, sổ prompt, sổ sử dụng AI | `apps/AA-CIS-App/docs/adr/0012-llm-data-scopes-per-stage.md`<br>`apps/AA-CIS-App/docs/llm/prompt-register.md`<br>[`docs/architecture/ai-use-register.md`](../../../docs/architecture/ai-use-register.md) | G | Ba mẫu. |
| T30 | Đánh giá: bộ chuẩn vàng, chạy bóng, CI chống thoái lui | `apps/AA-CIS-App/docs/llm/eval-runbook.md`<br>`apps/AA-CIS-App/.github/workflows/eval-regression.yml` | G | Mẫu workflow và thư mục bộ chuẩn vàng. |
| T31 | Ranh giới AI với tư vấn rủi ro cao; dấu AI trên nội dung giao đi | `apps/AA-Booking/CONTEXT.md`<br>[`docs/adr/0020-content-quality-architecture.md`](../../../docs/adr/0020-content-quality-architecture.md) | G | Mục trong checklist phát hành (phần AI). |
| T32 | Miền lỗi nhà cung cấp: một lệnh chặn cấp tài khoản làm sập mọi model cùng lúc | [`docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md`](../../../docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md) | P | Luật: có hai đường nhà cung cấp độc lập trước khi dựa vào AI ở prod. |
| T33 | Gọi chéo tài khoản, thứ tự route nhà cung cấp, runbook khoá, công cụ CLI gateway | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §4.3<br>[`docs/ops/runbooks/llm-anthropic-api-key.md`](../../../docs/ops/runbooks/llm-anthropic-api-key.md)<br>[`tools/llm/`](../../../tools/llm/) | A | Chỉ ở phần AA. |

### Nền tảng dữ liệu

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T34 | CSDL dùng chung, mỗi schema một chủ, sổ quyền sở hữu | [`docs/database/schema-ownership.md`](../../../docs/database/schema-ownership.md) | G | Mẫu sổ. |
| T35 | Chuẩn dữ liệu (phiên bản 1.13 tính tới 13/11/2026): 20 luật vàng, Phần A (kỹ thuật), B (quản lý), C (mở rộng) | [`docs/architecture/data-standards/README.md`](../../../docs/architecture/data-standards/README.md) | P | Kèm bản lõi; các con số AA (thời hạn, ngân sách) thành giá trị mặc định dự án tự đặt. |
| T36 | Đặt tên, khoá và kiểu (NAM, KEY), luật truy vấn (QRY), checklist PR có SQL | [`docs/architecture/data-standards/01-engineering.md`](../../../docs/architecture/data-standards/01-engineering.md) | G | Chép nguyên. |
| T37 | Migration: khoá theo chủ, chạy lại an toàn, không file down, expand / contract, expand tự áp trên Dev | [`docs/architecture/data-standards/01-engineering.md`](../../../docs/architecture/data-standards/01-engineering.md) §3<br>[`docs/adr/0017-migrations-in-app-pr-expand-auto-apply.md`](../../../docs/adr/0017-migrations-in-app-pr-expand-auto-apply.md) | P | Mẫu migration và preflight; bước copy sang Infra chỉ cho dự án nhiều repo. |
| T38 | Role, quyền và một mẫu RLS (SEC-1..12) | [`docs/architecture/data-standards/01-engineering.md`](../../../docs/architecture/data-standards/01-engineering.md) §4 | G | Chép nguyên. |
| T39 | View hợp đồng, JSON Schema cho từng hợp đồng, minor chỉ thêm / major chạy song song, lint hợp đồng | [`docs/contracts/README.md`](../../../docs/contracts/README.md)<br>[`tools/contracts/check_contracts.py`](../../../tools/contracts/check_contracts.py) | G | Mẫu hợp đồng và lint trong scaffold. |
| T40 | Outbox, job kéo, inbox chống trùng | [`docs/architecture/data-standards/README.md`](../../../docs/architecture/data-standards/README.md) | G | Trang mẫu. |
| T41 | Gắn thẻ PII cho cột, mỗi bảng log một dòng thời hạn lưu, lưu trữ ra object storage | [`docs/architecture/data-standards/02-data-management.md`](../../../docs/architecture/data-standards/02-data-management.md) §6-7 | G | Mẫu thời hạn lưu; bộ sinh danh mục PII. |
| T42 | Tài liệu schema và ERD sinh tự động; agent không bao giờ đoán tên bảng, cột | [`docs/architecture/db-schema-reference.md`](../../../docs/architecture/db-schema-reference.md)<br>[`.kiro/steering/db-schema.md`](../../../.kiro/steering/db-schema.md) | P | Workflow dump trong scaffold. Đây là năng lực DORA 'dữ liệu nội bộ AI truy cập được'. |
| T43 | Sổ bảng chết; thao tác xoá luôn DRY RUN trước | [`docs/architecture/dead-table-registry.md`](../../../docs/architecture/dead-table-registry.md)<br>[`skill/aa-cis-schema/references/destructive-ops.md`](../../../skill/aa-cis-schema/references/destructive-ops.md) | G | Chép nguyên. |
| T44 | Probe cô lập: 0 dòng chéo tenant khi RLS hoặc role thay đổi | [`docs/ops/runbooks/isolation-probe.md`](../../../docs/ops/runbooks/isolation-probe.md) | G | Mẫu probe CI cho tuỳ chọn đa tenant. |
| T45 | Workflow DB Migrate, exec container qua object storage, các bẫy schema | [`docs/ops/runbooks/db-migrate.md`](../../../docs/ops/runbooks/db-migrate.md)<br>[`docs/ops/runbooks/ecs-exec-s3-mediated.md`](../../../docs/ops/runbooks/ecs-exec-s3-mediated.md) | A | Phần AA. Bộ kit chỉ giữ nguyên tắc: DDL chạy từ CI, không từ máy cá nhân. |

### Mở rộng và độ tin cậy

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T46 | SLO, ngân sách kết nối tối đa 75%, mở rộng theo trigger đo được, bảo trì Postgres, rà soát dung lượng hằng tháng | [`docs/architecture/data-standards/03-scaling.md`](../../../docs/architecture/data-standards/03-scaling.md) | G | Là mặc định; SLO và error budget bật khi có bản prod đầu tiên. |

### Hạ tầng

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T47 | IaC: mỗi tài khoản một root, backend state, plan trên PR, chỉ apply từ main, kiểm drift định kỳ | `infra/AA-CIS-Infra/CONTEXT.md` | P | Khung infra với cùng workflow; tên tài khoản thành tham số. |
| T48 | CI vào cloud bằng OIDC, mỗi repo và job một role | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §5 | G | Chép nguyên. |
| T49 | Chuẩn gắn tag với guard CI; guard trên plan Terraform | [`docs/architecture/tagging-standard.md`](../../../docs/architecture/tagging-standard.md) | G | Giữ tên khoá tag; giá trị theo dự án. |
| T50 | Tài liệu sinh tự động: kiểm kê, role IAM, mạng, cảnh báo, cấu hình env (chỉ tên) | [`docs/generated/alarms.md`](../../../docs/generated/alarms.md)<br>[`docs/generated/env-config.md`](../../../docs/generated/env-config.md) | P | Workflow docs-gen trong khung infra. |
| T51 | Container trên Fargate, tag image bất biến theo commit, /health trả git_sha | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §5.3 | G | Chép nguyên. |
| T52 | Mỗi bên gọi một security group | [`docs/adr/0004b-per-app-security-groups.md`](../../../docs/adr/0004b-per-app-security-groups.md) | G | Chép nguyên. |

### Thực hành kỹ thuật

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T53 | Pipeline CI: lint, test unit và integration chia shard, build image, build frontend | `apps/AA-CIS-App/.github/workflows/ci.yml` | P | Mỗi stack một mẫu (API Python, web Next.js, Lambda). |
| T54 | Hook pre-push với kiểm tra nhanh tại máy | `apps/AA-CIS-App/.githooks/pre-push`<br>`apps/AA-CIS-App/scripts/pre-push.sh` | G | Có sẵn trong scaffold. |
| T55 | Ratchet sức khoẻ code: độ phức tạp tối đa 10, file tối đa 800 dòng, baseline chỉ được giảm (AA-1097) | `apps/AA-CIS-App/.github/scripts/code_health.py`<br>`apps/AA-CIS-App/.github/code-health.json` | G | Có từ ngày đầu với baseline rỗng, nên giới hạn đúng từ commit đầu tiên. |
| T56 | Ratchet độ phủ test: mức sàn chỉ đi lên | `apps/AA-CIS-App/.github/scripts/coverage_ratchet.py` | G | Có sẵn trong scaffold. |
| T57 | Vệ sinh CI/CD: danh sách action cho phép, độ mới của pin, ngân sách cache, lint workflow | [`docs/adr/0021-github-org-security-and-ci-hygiene.md`](../../../docs/adr/0021-github-org-security-and-ci-hygiene.md)<br>[`tools/github/ci_hygiene.py`](../../../tools/github/ci_hygiene.py) | G | Chép nguyên. |
| T58 | Quét secret trên PR và toàn bộ lịch sử | [`.github/workflows/secret-scan.yml`](../../../.github/workflows/secret-scan.yml) | G | Chép nguyên. |
| T59 | Kiểm tiêu đề PR và luật Refs | [`.github/workflows/pr-title.yml`](../../../.github/workflows/pr-title.yml) | P | Mẫu mã issue của tracker thành tham số. |
| T60 | Mẫu PR là hồ sơ thay đổi: rủi ro, rollback, chi phí, ảnh hưởng tài liệu | [`.github/pull_request_template.md`](../../../.github/pull_request_template.md) | G | Chép nguyên. |
| T61 | Release-please, build một lần deploy nhiều nơi, verify sau deploy, hợp đồng /health và /health/ready | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §5.2<br>`apps/AA-CIS-App/.github/workflows/post-deploy-verify.yml` | G | Có sẵn trong scaffold. |
| T62 | Sổ feature flag: deploy không phải phát hành | [`docs/ops/feature-flags.md`](../../../docs/ops/feature-flags.md) | G | Mẫu sổ. |
| T63 | So sánh hợp đồng API (xuất OpenAPI và kiểm thay đổi phá vỡ) | `apps/AA-CIS-App/.github/workflows/api-contract.yml` | G | Có sẵn trong scaffold. |
| T64 | Guard bản sao từng byte cho code dùng chung được vendor (UI kit, lõi AI, bộ kiểm định danh) | [`docs/adr/0016-one-design-system-guarded-kit-copies.md`](../../../docs/adr/0016-one-design-system-guarded-kit-copies.md)<br>[`tools/kit/kit-sync.sh`](../../../tools/kit/kit-sync.sh) | G | Script đồng bộ chung với danh sách nguồn. |
| T65 | Merge queue và bộ công cụ ship (cổng, wave, train, copy và apply) | [`tools/github/README.md`](../../../tools/github/README.md)<br>[`skill/aa-ship/references/merge-trains.md`](../../../skill/aa-ship/references/merge-trains.md) | P | Danh sách repo (apps.env) và tên bot thành tham số. |

### Frontend và kiểm thử

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T66 | Một design system, kit gốc chép từng byte, guard chặn sửa bản sao | [`docs/adr/0016-one-design-system-guarded-kit-copies.md`](../../../docs/adr/0016-one-design-system-guarded-kit-copies.md) | P | Là tuỳ chọn; phải bổ sung chuẩn trợ năng (khoảng trống). |
| T67 | Kiểm UI: build, preview, ảnh sáng / tối / mobile, lỗi console và network, dữ liệu thật | [`skill/aa-ui-verify/SKILL.md`](../../../skill/aa-ui-verify/SKILL.md) | P | Thành skill chung. |
| T68 | Playwright smoke, so sánh hình, E2E có đăng nhập, integration chạy đêm | `apps/AA-CIS-App/.github/workflows/ui-smoke.yml`<br>`apps/AA-CIS-App/.github/workflows/visual.yml` | G | Mẫu workflow. |
| T69 | Bộ UAT: chạy kịch bản thành video có phụ đề và thuyết minh bằng công cụ miễn phí tại máy | [`tools/uat/build.py`](../../../tools/uat/build.py)<br>[`skill/aa-uat-video/SKILL.md`](../../../skill/aa-uat-video/SKILL.md) | G | Kèm thành công cụ. |

### Quan sát và bảo mật

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T70 | Nền quan sát: log JSON có request id, cảnh báo theo triệu chứng, công cụ bắt lỗi, SHA ở health | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §7.1 | G | Chép nguyên. |
| T71 | Danh mục cảnh báo, mỗi cảnh báo trỏ tới runbook (thiếu thì lint báo lỗi) | [`docs/generated/alarms.md`](../../../docs/generated/alarms.md)<br>[`tools/docs/check_alarm_runbooks.py`](../../../tools/docs/check_alarm_runbooks.py) | G | Chép nguyên. |
| T72 | Checklist security baseline có trạng thái thật và lệnh kiểm lại | [`docs/security/baseline.md`](../../../docs/security/baseline.md) | P | Ánh xạ lại theo OWASP ASVS 5.0 mức 1 và tự đánh giá SAMM nhẹ. |
| T73 | Sổ secret (chỉ tên), runbook xoay vòng, quản lý lỗ hổng | [`docs/security/secrets-register.md`](../../../docs/security/secrets-register.md)<br>[`docs/ops/runbooks/secret-rotation.md`](../../../docs/ops/runbooks/secret-rotation.md)<br>[`docs/security/vulnerability-management.md`](../../../docs/security/vulnerability-management.md) | G | Thành mẫu. |
| T74 | Viết an toàn cho repo public: không ID tài khoản, ARN, ID mạng hay điểm yếu | [`docs/STYLE.md`](../../../docs/STYLE.md)<br>[`docs/adr/0014-repo-visibility-and-github-plan.md`](../../../docs/adr/0014-repo-visibility-and-github-plan.md) | G | Chép nguyên. |
| T75 | Hook rào chắn agent: subagent, MCP, shell guard, sửa kit, chặn PII, có test tấn công thử | [`.claude/hooks/subagent-guardrails.sh`](../../../.claude/hooks/subagent-guardrails.sh)<br>[`.claude/hooks/aa_shell_guard.py`](../../../.claude/hooks/aa_shell_guard.py)<br>[`.claude/settings.json`](../../../.claude/settings.json) | P | Tách thành luật chung và luật AA; test đi kèm. |
| T76 | Sổ quyền riêng tư: hồ sơ xử lý, bên xử lý phụ, DPA, yêu cầu của chủ thể dữ liệu | [`docs/legal/register.md`](../../../docs/legal/register.md) | P | Mẫu; nội dung pháp lý theo từng nước. |

### Chi phí và tài liệu

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| T77 | FinOps: tag, ngân sách, trần chi tiêu trong DB, công cụ báo cáo chi phí tháng | [`docs/ops/finops.md`](../../../docs/ops/finops.md)<br>[`tools/finops/monthly_cost_report.py`](../../../tools/finops/monthly_cost_report.py) | P | Mẫu bảng chi phí; công cụ báo cáo đọc cấu hình dự án. |
| T78 | Trang chi tiêu trong admin và đối soát sổ cái hằng đêm | [`docs/ecosystem-architecture.md`](../../../docs/ecosystem-architecture.md) §4.4 | A | Phần AA. |
| T79 | Tài liệu như code: catalog, loại Diátaxis, schema front-matter, lint tài liệu | [`docs/README.md`](../../../docs/README.md)<br>[`docs/STYLE.md`](../../../docs/STYLE.md)<br>[`tools/docs/README.md`](../../../tools/docs/README.md) | G | Kèm khung catalog và lint. |
| T80 | Luật ngôn ngữ: trang tiếng Anh, ngôn ngữ thứ hai là file anh em .vi.md | [`.kiro/steering/language-convention.md`](../../../.kiro/steering/language-convention.md) | P | Tham số: ngôn ngữ chính và ngôn ngữ phụ. |
| T81 | Mẫu tài liệu: ADR, runbook, how-to, reference, explanation, postmortem, release note, các bản rà soát | [`docs/templates/adr.md`](../../../docs/templates/adr.md)<br>[`docs/templates/runbook.md`](../../../docs/templates/runbook.md) | G | Chép nguyên. |
| T82 | Onboarding, hướng dẫn theo vai trò, lộ trình kỹ sư mới | [`docs/onboarding.md`](../../../docs/onboarding.md)<br>[`docs/guides/new-engineer.md`](../../../docs/guides/new-engineer.md) | P | Cấu trúc mẫu; nội dung theo dự án. |
| T83 | PRD như code với tiêu chí chấp nhận AC-n | [`docs/product/README.md`](../../../docs/product/README.md) | G | Chép nguyên. |
| T84 | Ghi chú triển khai theo issue (Decisions, Changed, Tradeoffs, Should know) | [`docs/implementation-notes/`](../../../docs/implementation-notes/) | G | Chép nguyên. |
| T85 | Trình đọc tài liệu trong admin có nút EN / VI và che ID | [`tools/docs/build_docs_reader.py`](../../../tools/docs/build_docs_reader.py) | P | Nền cho LMS (AA-1098). |

## Quy trình

### Quản lý phiên

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| R1 | Đầu phiên: đọc trạng thái, kiểm live, trạng thái cổng AI, đề xuất issue theo slot kế hoạch | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md)<br>[`.kiro/steering/session-workflow.md`](../../../.kiro/steering/session-workflow.md) | P | Thành skill chung; các lệnh kiểm live lấy từ file cấu hình dự án. |
| R2 | Cuối phiên theo đúng thứ tự: chốt việc, snapshot live, bài học, bản nháp được duyệt, rồi mới ghi log | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md) | P | Thành skill chung; giữ luật bằng chứng trước log. |
| R3 | Checklist phiên sống, đăng thành tab Phiên của tracker | [`docs/backlog/tracker/README.md`](../../../docs/backlog/tracker/README.md) | P | File checklist trong repo; đăng lên là tuỳ chọn. |
| R4 | Mỗi phiên 3-5 issue; tối đa 8 In Progress; vượt trần thì mở phiên bằng lượt hội tụ | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md) | G | Đây là giới hạn WIP của Kanban; thêm tuổi việc và cycle time. |
| R5 | Rà soát định kỳ: truy vấn chậm hằng tuần, dung lượng và chi phí hằng tháng, quyền hằng quý | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md)<br>[`docs/templates/capacity-review.md`](../../../docs/templates/capacity-review.md)<br>[`docs/templates/access-review.md`](../../../docs/templates/access-review.md) | G | Chép nhịp; hạn tính từ bản ghi gần nhất. |
| R6 | Log phiên, đánh số và khối memory | [`docs/sessions/README.md`](../../../docs/sessions/README.md) | P | Nơi lưu memory thành tham số (mặc định là file trong repo). |
| R7 | Nguồn sự thật cho trạng thái quy trình và thứ tự khi lệch | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §2.2 | G | Chép nguyên. |
| R8 | Làm xong rồi mới đóng; hook Stop chặn dừng khi còn việc không bị chặn | [`.claude/hooks/stop-open-work.sh`](../../../.claude/hooks/stop-open-work.sh) | G | Đi kèm bộ hook agent. |

### Sẵn sàng và xong

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| R9 | Definition of Ready với lớp rủi ro (auth, migration, IAM/secret, xoá, chi phí, LLM) | [`docs/templates/definition-of-ready.md`](../../../docs/templates/definition-of-ready.md) | G | Chép nguyên; thêm trường appetite. |
| R10 | Definition of Done = đã kiểm live, kèm comment bằng chứng | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) | G | Chép nguyên. |
| R11 | Done-when đóng băng khi sang In Progress; Done-with-scope chỉ khi có issue nối tiếp | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) | G | Chép nguyên. |

### Ship và phát hành

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| R12 | Checklist trước merge; chặn theo mọi check, không chỉ check bắt buộc | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) | P | Thành skill chung; tên công cụ thành tham số. |
| R13 | Chỉ deploy khi không có job chặn hay batch đang mở; phần còn lại xả và nhận lại | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md)<br>[`docs/architecture/data-standards/03-scaling.md`](../../../docs/architecture/data-standards/03-scaling.md) | G | Chép nguyên. |
| R14 | Chỉ apply hạ tầng qua workflow, từ main | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) | G | Chép nguyên. |
| R15 | Các bước kiểm live sau deploy | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md) | G | Thành checklist phát hành. |
| R16 | Release note chỉ từ việc đã kiểm | [`docs/templates/release-note.md`](../../../docs/templates/release-note.md) | G | Chép nguyên. |
| R17 | Rollback: app trước, CSDL chỉ tiến; runbook và buổi diễn tập | [`docs/ops/runbooks/rollback-ecs.md`](../../../docs/ops/runbooks/rollback-ecs.md)<br>[`docs/ops/drills/rollback-game-day.md`](../../../docs/ops/drills/rollback-game-day.md) | G | Thành mẫu; phần lớn runbook rollback của AA vẫn UNTESTED. |
| R18 | Thứ tự flag và migration: tắt flag, deploy, apply, bật flag, kiểm | [`docs/ops/feature-flags.md`](../../../docs/ops/feature-flags.md) | G | Chép nguyên. |
| R19 | Quản lý phiên bản: commit, phiên bản app, tag image, khoá migration, API, phiên bản prompt và model | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §5 | G | Chép nguyên. |

### Chạy lô trả phí

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| R20 | Chạy lô với tập cố định: 3, rồi tối đa 50, rồi tất cả; snapshot; điều kiện dừng bằng số; báo cáo có mã thoát | [`skill/aa-wave-rerun/SKILL.md`](../../../skill/aa-wave-rerun/SKILL.md) | P | Thành skill chạy lô chung. |
| R21 | Ước tính chi phí trước khi chạy trả phí; không có cơ sở thì chạy thử 3 mục trước | [`tools/llm/cost_estimate.py`](../../../tools/llm/cost_estimate.py) | P | Đọc sổ cái của dự án. |

### Sự cố và học hỏi

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| R22 | Ứng phó sự cố: mức độ, 15 phút đầu, báo cho ai, nhánh rò rỉ dữ liệu | [`docs/ops/incident-response.md`](../../../docs/ops/incident-response.md) | G | Chép nguyên. |
| R23 | Playbook theo triệu chứng, thư viện runbook, luật 'đã chạy thử' | [`docs/ops/README.md`](../../../docs/ops/README.md)<br>[`docs/STYLE.md`](../../../docs/STYLE.md) | P | Mẫu mục lục; giữ luật đã chạy thử. |
| R24 | Diễn tập và game day có link bằng chứng | [`docs/ops/drills/README.md`](../../../docs/ops/drills/README.md) | G | Chép nguyên. |
| R25 | Mẫu postmortem không đổ lỗi và mục lục | [`docs/templates/postmortem.md`](../../../docs/templates/postmortem.md)<br>[`docs/ops/postmortems/README.md`](../../../docs/ops/postmortems/README.md) | G | Thêm danh sách điều kiện kích hoạt theo SRE. |
| R26 | Sổ bài học có trường Guard bắt buộc; bài học thành test hoặc hook | [`skill/aa-lessons/SKILL.md`](../../../skill/aa-lessons/SKILL.md)<br>[`tools/docs/check_lessons.py`](../../../tools/docs/check_lessons.py)<br>[`skill/aa-lessons/guards.md`](../../../skill/aa-lessons/guards.md) | G | Kèm sổ rỗng và bộ kiểm. |
| R27 | Luật cứng: kiểm, không đoán; tìm nguyên nhân gốc trước; kiểm live trước khi khẳng định | [`skill/ai-nghiep/SKILL.md`](../../../skill/ai-nghiep/SKILL.md) | G | Chép nguyên. |

### Điều phối agent

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| R28 | Quyền agent điều phối và subagent: subagent viết code và commit tại máy; agent điều phối ship | [`skill/ai-nghiep/SKILL.md`](../../../skill/ai-nghiep/SKILL.md) | G | Chép nguyên; hook cưỡng chế. |
| R29 | Lane song song: mỗi lane một worktree, reviewer theo góc nhìn, một lượt sửa, danh sách PR kèm bước live | [`tools/workflows/lane.js`](../../../tools/workflows/lane.js)<br>[`skill/aa-session/references/parallel-lanes.md`](../../../skill/aa-session/references/parallel-lanes.md) | P | Tách khối luật COMMON thành phần chung và phần AA. |
| R30 | Mẫu giao việc | [`skill/ai-nghiep/references/handoff-prompt.md`](../../../skill/ai-nghiep/references/handoff-prompt.md) | G | Chép nguyên. |
| R31 | Giao cho agent viết code thứ hai (Kiro) có preflight và gác cổng | [`.claude/skills/kiro-delegate/SKILL.md`](../../../.claude/skills/kiro-delegate/SKILL.md)<br>[`.claude/agents/kiro-reviewer.md`](../../../.claude/agents/kiro-reviewer.md) | P | Mẫu 'agent thứ hai' không phụ thuộc nhà cung cấp. |
| R32 | Tầng chỉ dẫn agent và mục lục: CLAUDE.md, steering, skill, llms.txt | [`docs/agents.md`](../../../docs/agents.md)<br>[`docs/llms.txt`](../../../docs/llms.txt) | P | AGENTS.md thành nguồn; CLAUDE.md import nó. |
| R33 | Bảo trì skill: SKILL.md ngắn, có references, dọn luật bị thay, luật đã thành CI thì xoá | [`skill/README.md`](../../../skill/README.md) | G | Chép nguyên. |
| R34 | Giải thích từng issue bằng lời dễ hiểu trước khi làm | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md) | G | Chép nguyên. |

## Quản trị

### Quyết định

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| V1 | Khi nào viết ADR; khung chọn công nghệ | [`skill/ai-nghiep/references/adr.md`](../../../skill/ai-nghiep/references/adr.md) | G | Chép nguyên. |
| V2 | Danh sách quyết định đã khoá, chỉ mở lại khi có bằng chứng mới | [`skill/ai-nghiep/references/adr.md`](../../../skill/ai-nghiep/references/adr.md) | P | Danh sách rỗng cho mỗi dự án. |
| V3 | Thứ tự ưu tiên nguồn: ADR trên chuẩn, trên quyết định, trên handbook, trên skill | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §1.3<br>[`docs/agents.md`](../../../docs/agents.md) | G | Chép nguyên. |
| V4 | Nhật ký quyết định của tech lead, mỗi quyết định ghi nơi cưỡng chế | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §10 | G | Chép nguyên. |
| V5 | Sửa nguồn gốc trước, rồi mới sửa bản tóm tắt | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §1.4 | G | Đây là luật handbook-first của GitLab. |
| V6 | Danh sách 'chưa làm bây giờ' kèm lý do từng mục | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §9.3 | G | Mỗi dự án giữ danh sách riêng. |

### Kiểm soát thay đổi

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| V7 | Quyền merge theo giai đoạn: thời dev agent tự merge khi xanh; từ prod đầu tiên tech lead duyệt lớp rủi ro | [`docs/architecture/data-standards/02-data-management.md`](../../../docs/architecture/data-standards/02-data-management.md)<br>[`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §6.5 | G | Chép nguyên; đây là 'standard change' của ITIL bằng lời thường. |
| V8 | Ai duyệt gì, theo loại thay đổi | [`docs/architecture/data-standards/02-data-management.md`](../../../docs/architecture/data-standards/02-data-management.md) | G | Thành một phần của RACI. |
| V9 | Agent độc lập review PR rủi ro (maker-checker cho agent) | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md)<br>[`.claude/agents/kiro-reviewer.md`](../../../.claude/agents/kiro-reviewer.md) | G | Chép nguyên. |
| V10 | Maker-checker cho dữ liệu nghiệp vụ: người thứ hai công bố giá | [`docs/adr/0005b-price-versions.md`](../../../docs/adr/0005b-price-versions.md) | G | Mở rộng sang thay đổi setting và sửa dữ liệu (khoảng trống). |
| V11 | Kết quả của chính agent không phải bằng chứng; giám khảo khác bên viết | [`skill/ai-nghiep/SKILL.md`](../../../skill/ai-nghiep/SKILL.md) | G | Chép nguyên. |
| V12 | Agent push và merge dưới danh tính GitHub App; bot merge PR sinh tự động | [`docs/adr/0011-github-app-identity-and-merge-rights.md`](../../../docs/adr/0011-github-app-identity-and-merge-rights.md)<br>[`docs/security/github-apps.md`](../../../docs/security/github-apps.md) | G | Chép nguyên; ADR 0011 vẫn Proposed (khoảng trống). |
| V13 | Agent không bao giờ scale, dừng hay bật hạ tầng | [`skill/ai-nghiep/SKILL.md`](../../../skill/ai-nghiep/SKILL.md) | G | Chép nguyên. |
| V14 | Hỏi quyết định gom thành một trang, mỗi câu có đề xuất; tự làm trong giới hạn đã thống nhất | [`skill/aa-session/SKILL.md`](../../../skill/aa-session/SKILL.md) | G | Viết thành dung sai kiểu PRINCE2 (hôm nay một phần chỉ nằm trong memory riêng). |

### Dữ liệu, bảo mật và AI

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| V15 | Quyền sở hữu schema và thứ tự migration (PR migration, copy, apply, dump schema, code) | [`docs/database/schema-ownership.md`](../../../docs/database/schema-ownership.md)<br>[`docs/ops/runbooks/db-migrate.md`](../../../docs/ops/runbooks/db-migrate.md) | P | Dự án một repo bỏ bước copy. |
| V16 | Luật PII và hook không cho agent đọc dòng dữ liệu cá nhân | [`docs/architecture/data-standards/02-data-management.md`](../../../docs/architecture/data-standards/02-data-management.md) §6<br>[`.claude/hooks/pilot-pii-guard.sh`](../../../.claude/hooks/pilot-pii-guard.sh) | G | Chép nguyên. |
| V17 | Rà soát quyền hằng quý, break-glass có rà soát sau khi dùng | [`docs/templates/access-review.md`](../../../docs/templates/access-review.md)<br>[`docs/ops/runbooks/break-glass.md`](../../../docs/ops/runbooks/break-glass.md) | G | Chép nguyên. |
| V18 | Sổ sử dụng AI ánh xạ OWASP LLM Top 10 và đánh dấu đầu ra | [`docs/architecture/ai-use-register.md`](../../../docs/architecture/ai-use-register.md) | G | Chép nguyên. |
| V19 | Quản trị thay đổi LLM: mã sổ prompt, lần chạy eval và chi phí trong PR, revert khi kết quả trượt | [`skill/aa-ship/SKILL.md`](../../../skill/aa-ship/SKILL.md)<br>[`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §5.7 | G | Chép nguyên. |
| V20 | Mọi ngưỡng do quản trị viên sửa được; chỉ hằng số hay biến môi trường thì không tính | `apps/AA-CIS-App/CONTEXT.md` ("Settings registry: every key ships its guide")<br>Linear AA-1096 | G | Ghi luật vào bộ chuẩn của hệ sinh thái cho mọi app; hôm nay nó là luật của CIS và một issue đang mở (khoảng trống 7). |
| V21 | Quyền xem repo và gói trả phí quyết bằng ADR | [`docs/adr/0014-repo-visibility-and-github-plan.md`](../../../docs/adr/0014-repo-visibility-and-github-plan.md) | P | Mẫu quyết định. |

### Chi phí

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| V22 | Báo chi phí tháng và xin đồng ý rõ cho từng hạng mục trả phí | [`docs/ops/finops.md`](../../../docs/ops/finops.md) | G | Chép nguyên; đây là dung sai chi phí kiểu PRINCE2. |
| V23 | Thang chạy trả phí: khoảng 3, rồi tối đa 50, không chạy toàn bộ khi chưa duyệt | [`docs/architecture/data-standards/02-data-management.md`](../../../docs/architecture/data-standards/02-data-management.md) §10 | G | Chép nguyên. |
| V24 | Dòng chi phí trong mọi PR; chỉ mở rộng theo trigger đo được, đòn bẩy rẻ nhất trước | [`.github/pull_request_template.md`](../../../.github/pull_request_template.md)<br>[`docs/architecture/data-standards/03-scaling.md`](../../../docs/architecture/data-standards/03-scaling.md) | G | Chép nguyên. |

## Quản lý

### Lập kế hoạch

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| M1 | Mô hình vận hành: hàng đợi Kanban, DevOps, trunk-based, ADLC | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §2.1 | G | Chép nguyên. |
| M2 | Vòng đời 12 bước từ ý tưởng tới báo cho bên kinh doanh | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §3 | G | Mở rộng hai đầu: discovery trước bước 1, retirement sau bước 9. |
| M3 | Backlog sống: hàng đợi có thứ tự, việc kiểm theo hạn, việc chờ tech lead | [`docs/backlog/README.md`](../../../docs/backlog/README.md) | G | Thành mẫu. |
| M4 | Tracker kế hoạch tổng (plan.json và trang HTML) có mốc, Done-when và rủi ro | [`docs/backlog/tracker/README.md`](../../../docs/backlog/tracker/README.md)<br>[`docs/backlog/tracker/plan.json`](../../../docs/backlog/tracker/plan.json) | P | Dùng lại schema và trang; công cụ đồng bộ đọc tracker ghi trong cấu hình. |
| M5 | Đồng bộ một chiều từ tracker issue sang kế hoạch | [`tools/linear/plan_sync.py`](../../../tools/linear/plan_sync.py) | P | Mỗi tracker một adapter. |
| M6 | Lộ trình nền tảng có mã và nhật ký quyết định | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) §9 | P | Bảng rỗng cho mỗi dự án. |

### Theo dõi issue

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| M7 | Hỏi trước khi tạo; kiểm trùng; mẫu Problem / Scope / Done-when; một project; thang ưu tiên | [`skill/aa-linear-issue/SKILL.md`](../../../skill/aa-linear-issue/SKILL.md) | P | Thành skill chung; tên project thành tham số. |
| M8 | Hạn mức gói Free: mỗi issue một lát giao được, xuất issue đã đóng vào repo rồi lưu trữ | [`tools/linear/linear_export.py`](../../../tools/linear/linear_export.py) | P | Module tuỳ chọn, chỉ cho Linear Free. |
| M9 | Kiểm đúng issue trước khi ghi; dùng Refs, không dùng Fixes / Closes | [`skill/aa-linear-issue/SKILL.md`](../../../skill/aa-linear-issue/SKILL.md)<br>[`.github/workflows/pr-title.yml`](../../../.github/workflows/pr-title.yml) | G | Chép nguyên. |
| M10 | Kiểm Done: issue sang Done mà không có bằng chứng thì mở lại | [`tools/linear/done_audit.py`](../../../tools/linear/done_audit.py) | P | Mỗi tracker một adapter. |
| M11 | Phạm vi phát sinh giữa chừng thành issue mới có liên kết | [`skill/aa-linear-issue/SKILL.md`](../../../skill/aa-linear-issue/SKILL.md) | G | Chép nguyên. |

### Báo cáo và các bên liên quan

| # | Thực hành | Nguồn AA | Lớp | Bản chung phải đổi gì |
|---|---|---|---|---|
| M12 | Cập nhật cho kinh doanh: nháp, tech lead duyệt, rồi đăng; chỉ tiến độ sản phẩm; gom vào cuối phiên | [`skill/aa-jira-update/SKILL.md`](../../../skill/aa-jira-update/SKILL.md) | P | Thành skill 'cập nhật kinh doanh' chung; kênh là tham số. |
| M13 | Tách quyết định kinh doanh và kỹ thuật; trước hết xem thay đổi hệ thống có xoá được câu hỏi không | [`skill/aa-jira-update/SKILL.md`](../../../skill/aa-jira-update/SKILL.md) | G | Chép nguyên. |
| M14 | Hướng dẫn giọng văn theo bên liên quan và cách làm việc với nhà cung cấp | [`skill/ai-nghiep/references/stakeholders-english.md`](../../../skill/ai-nghiep/references/stakeholders-english.md) | P | Dùng lại cấu trúc; bỏ tên người. Thêm checklist chọn nhà cung cấp (khoảng trống). |
| M15 | Sổ báo cáo và KPI, có lint | [`docs/reports/catalog.yaml`](../../../docs/reports/catalog.yaml)<br>[`docs/reports/kpis.yaml`](../../../docs/reports/kpis.yaml) | G | Chép nguyên. |
| M16 | Rà soát dung lượng và chi phí hằng tháng | [`docs/templates/capacity-review.md`](../../../docs/templates/capacity-review.md)<br>[`docs/templates/cost-report.md`](../../../docs/templates/cost-report.md) | G | Chép nguyên. |
| M17 | Thư mục audit theo phiên và sổ artifact | [`docs/artifacts/README.md`](../../../docs/artifacts/README.md) | G | Chép nguyên. |
| M18 | Engineering handbook trỏ tới mọi nguồn gốc | [`docs/engineering-handbook.md`](../../../docs/engineering-handbook.md) | G | Thành trang đầu của playbook. |
