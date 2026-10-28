---
id: GUIDE-03
title: Bảng thuật ngữ
description: Thuật ngữ về phát triển, vận hành, dữ liệu và AA-Ecosys, nghĩa của từng thuật ngữ và nơi nó xuất hiện trong hệ thống.
type: reference
status: active
owner: nghiep
audience: [owner, engineer, devops, cto, cio, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-28
review_every_days: 180
related: [CAT-00, TPL-02]
lang: vi
translation_of: docs/glossary.md
---

# Bảng thuật ngữ

Các thuật ngữ dùng trong tài liệu AA-Ecosys. Bảng được dựng từ mục 8 của hướng dẫn SDLC phiên S243 và bổ sung
thuật ngữ của chương trình. Tài liệu kỹ thuật dùng thuật ngữ tiếng Anh và giữ nguyên ở mọi nơi
([STYLE](STYLE.md#voice-and-structure)). Thêm thuật ngữ mới ngay trong PR đầu tiên dùng nó. Đây là bản tiếng Việt
của [glossary.md](glossary.md); cột thứ hai là tên tiếng Việt của thuật ngữ.

## Quy trình và bàn giao

| Thuật ngữ | Tiếng Việt | Nghĩa | Trong AA-Ecosys |
|---|---|---|---|
| SDLC | Vòng đời phát triển phần mềm | Vòng đời của phần mềm từ ý tưởng tới khi ngừng dùng. | Lập kế hoạch, xây, kiểm tra, phát hành, vận hành, ngừng dùng. |
| ADLC | Vòng đời phát triển có agent | Tên mình dùng cho SDLC cộng thêm việc kiểm soát agent AI và vòng đời của tính năng LLM. | Kiro hoặc subagent viết code, Claude Code gác cổng; prompt writer/judge có eval. |
| Trunk-based development | Phát triển trên một nhánh chính | Nhánh ngắn, gộp thường xuyên vào một nhánh luôn deploy được. | `main` ở repo app và Infra, `master` ở repo gốc (ADR-2026-023). |
| Pull request (PR) | Yêu cầu gộp code | Một thay đổi đề xuất, nơi chạy review và CI. | Squash merge, phần thân ghi `Refs AA-xxx`. |
| CI (continuous integration) | Tích hợp liên tục | Tự động build và test mọi thay đổi. | `ci.yml` ở mọi repo app (CIS: Lint, Security Audit, Unit Tests, Integration Tests, Docker Build Check, Frontend Build, Frontend Lint). |
| CD (continuous delivery / deployment) | Triển khai liên tục | Tự động đưa thay đổi đã qua CI lên một môi trường. | `deploy-dev.yml` (CIS), `deploy-lambdas.yml` (TripPlanner). |
| Required checks / branch protection | Kiểm tra bắt buộc / bảo vệ nhánh | Các kiểm tra phải xanh trước khi merge. | Bảo vệ nhánh trên bốn repo app (CIS 9 kiểm tra, Booking 7, TripPlanner 5, Partner 10, đọc ngày 28/10/2026). Repo gốc và Infra không có. |
| Deploy gate | Cổng chặn deploy | Bước CI chặn deploy backend khi đang mở một wave chạy lại, hoặc khi một job thuộc loại chặn deploy của app đó đang chạy hay sắp tới hạn (C6.3a, AA-993 G5). | CIS: wave đang mở hoặc `data_erasure`, `s1_batch_ingest`, `writing_memory_r2`, `writing_memory_shadow`; Booking: hai loại job lưu trữ (retention); Partner: hiện không có (`crm_dispatch` thôi chặn từ AA-993 G4b). Các job khác đang chờ hoặc đang chạy được nhả ra và task mới nhận lại. Bỏ qua cổng là quyết định của tech lead. |
| Definition of Ready (DoR) | Điều kiện sẵn sàng | Những gì một issue cần có trước khi bắt đầu làm. | [`templates/definition-of-ready.md`](templates/definition-of-ready.md). |
| Definition of Done (DoD) | Điều kiện hoàn thành | Những gì phải đúng thì mới gọi là xong. | `skill/aa-ship`: đã merge, CI xanh, rollout COMPLETED, đã kiểm trên môi trường thật. |
| Kanban | Kanban | Kéo việc từ một hàng đợi có thứ tự, giới hạn số việc đang làm, không chia sprint. | Backlog sống, cộng các phiên làm việc 3 tới 5 issue. |
| Change record | Hồ sơ thay đổi | Dấu vết viết ra của một thay đổi, rủi ro và cách lùi lại. | Chính PR; các loại thay đổi rủi ro được `kiro-reviewer` xem. |
| DORA metrics | Chỉ số DORA | Tần suất deploy, thời gian từ commit tới chạy thật, thời gian khôi phục, tỷ lệ thay đổi lỗi, tỷ lệ làm lại. | Để sau (U-47, khi có prod đầu tiên). |

## Phiên bản và phát hành

| Thuật ngữ | Tiếng Việt | Nghĩa | Trong AA-Ecosys |
|---|---|---|---|
| Conventional Commits | Chuẩn commit quy ước | Dạng tiêu đề commit `type(scope)!: subject`. | `fix: excel price mapping`, phần thân `Refs AA-26`. |
| SemVer | Đánh version ngữ nghĩa | `MAJOR.MINOR.PATCH` theo mức tương thích. | Version app do release-please đặt (AA-891), ví dụ CIS `v0.13.0` (28/10/2026). |
| CalVer | Đánh version theo ngày | Version theo ngày tháng. | Tuỳ chọn cho Infra. |
| Git tag | Nhãn git | Một nhãn cố định gắn vào một commit. | Mỗi bản phát hành của từng repo app có một tag `vX.Y.Z` (AA-891). |
| GitHub Release | Bản phát hành GitHub | Trang cho một tag, có ghi chú và tệp kèm. | Do release-please tạo (AA-891). |
| CHANGELOG | Nhật ký thay đổi | Danh sách thay đổi dễ đọc theo từng version. | `CHANGELOG.md` ở mỗi repo (AA-891). |
| Release note | Ghi chú phát hành | Tóm tắt một bản phát hành cho phía kinh doanh. | Bản nháp Jira cho chủ doanh nghiệp, [mẫu](templates/release-note.md). |
| release-please | release-please | Bot mở PR phát hành kèm số version mới và changelog, rồi gắn tag khi PR được merge. | AA-891 (U-47, làm sớm). |
| Immutable image tag | Tag image bất biến | Tag image không ghi đè được. | ECR `dev-<sha>`, IMMUTABLE, giữ 30 bản gần nhất (CIS). |
| Task definition revision | Bản task definition | Một cấu hình chạy ECS có đánh số. | Rollback trỏ service về bản trước (`skill/aa-ship` §5). |
| Rolling deploy | Triển khai cuốn chiếu | Thay task dần dần. | Mặc định của ECS cho CIS, Booking và Partner. |
| Circuit breaker (ECS) | Cầu dao tự lùi | ECS dừng và lùi một lần deploy khi task mới không khoẻ. | Bật trên các service ECS trong Terraform. |
| Blue/green, canary | Xanh/lục, canary | Chuyển traffic giữa hai bộ chạy / chuyển dần theo phần trăm. | Chưa cần. |
| Rollback / roll-forward | Lùi bản / sửa tiến | Quay về bản trước / đưa lên một bản sửa. | `skill/aa-ship` §5; runbook rollback (OPS-02). |
| Build once, deploy many | Build một lần, chạy nhiều nơi | Một artifact, cùng digest ở mọi môi trường; chỉ cấu hình khác nhau. | Image `dev-<sha>`, sau này đẩy lên prod. |
| Feature flag | Cờ tính năng | Bật tắt tính năng không cần deploy. | Ghi trong `docs/ops/feature-flags.md` (OPS-06); cờ tenant pool là một biện pháp bảo mật. |
| Deploy vs release | Triển khai và phát hành | Code đang chạy, so với người dùng đã thấy. | Bật cờ cho một tenant trước. |
| Expand / contract | Mở rộng / thu hẹp | Đổi schema hay API theo ba bước để bản cũ và bản mới cùng chạy được. | Migration và version của contract. |
| Breaking change | Thay đổi phá tương thích | Thay đổi làm hỏng client đang dùng. | Bỏ một trường trong response; oasdiff bắt được (AA-899). |
| OpenAPI | OpenAPI | Đặc tả REST API mà máy đọc được. | `/booking/openapi.json`; xuất cho CIS và Booking trong AA-899. |
| Deprecation / Sunset header | Header báo ngừng | Header HTTP báo một API sắp bỏ và khi nào bỏ. | RFC 9745 / RFC 8594; đi cùng ADR 0013 (U-44). |

## Tài liệu

| Thuật ngữ | Tiếng Việt | Nghĩa | Trong AA-Ecosys |
|---|---|---|---|
| Docs-as-code | Tài liệu như code | Tài liệu nằm trong repo, sửa cùng PR, CI kiểm tra. | Danh mục này; lint trong AA-888. |
| Diátaxis | Diátaxis | Bốn loại tài liệu: tutorial, how-to, reference, explanation. | Trường `type` của [front-matter](templates/frontmatter.schema.json). |
| Doc catalog | Danh mục tài liệu | Danh sách mọi tài liệu được duy trì, người chịu trách nhiệm và chu kỳ xem lại. | [`docs/README.md`](README.md). |
| Front-matter | Phần đầu trang | Khối YAML ở đầu trang, chứa thông tin về trang. | Bắt buộc: id, title, type, status, owner, last_reviewed. |
| Runbook / playbook | Sổ tay vận hành / kịch bản xử lý | Các bước chính xác cho một việc / cách xử lý một loại sự cố. | `docs/ops/runbooks/`, `docs/ops/playbooks/`. |
| ADR | Bản ghi quyết định kiến trúc | Bối cảnh, quyết định và hệ quả của một lựa chọn kiến trúc. | `docs/adr/` (repo gốc), repo app và Infra. |
| CONTEXT.md | CONTEXT.md | Trang của từng repo về stack, ranh giới và quyền sở hữu; đọc trước khi thiết kế. | CIS, Booking, TripPlanner, Partner, Infra. |
| C4 model | Mô hình C4 | Sơ đồ kiến trúc ở bốn mức phóng to; mình dùng L1 (bối cảnh) và L2 (container). | `ecosystem-architecture.md`. |
| llms.txt | llms.txt | Một mục lục Markdown chỉ cho agent AI nên đọc gì. | [`docs/llms.txt`](llms.txt). |
| Freshness | Độ tươi tài liệu | `last_reviewed` còn nằm trong `review_every_days` hay không. | Báo cáo hằng tuần cùng AA-888. |
| Postmortem (blameless) | Phân tích sau sự cố | Phân tích sự cố không đổ lỗi, kết thúc bằng các việc cần làm. | [`templates/postmortem.md`](templates/postmortem.md); một dòng bài học trong `lessons.md`. |

## Hạ tầng và vận hành

| Thuật ngữ | Tiếng Việt | Nghĩa | Trong AA-Ecosys |
|---|---|---|---|
| acc2 / acc3 | Tài khoản 2 / 3 | Hai tài khoản AWS của hệ sinh thái. | acc2 = toàn bộ hạ tầng; acc3 = tài khoản vệ tinh LLM (Amazon Bedrock). acc1, một tài khoản cá nhân, đã rời hệ sinh thái ở phiên S255 (AA-998): không còn LLM dự phòng qua tài khoản khác. Bảng tài khoản: [onboarding](onboarding.md#account-map). |
| Infrastructure as Code (IaC) | Hạ tầng dạng code | Hạ tầng được khai báo bằng code. | Terraform trong AA-CIS-Infra. |
| Terraform state / lock file | Trạng thái / file khoá Terraform | Bản ghi tài nguyên thật / version provider đã ghim. | State lưu trên S3; `.terraform.lock.hcl`. |
| Terraform drift | Lệch hạ tầng | Hạ tầng thật khác với code hoặc state. | Chỉ apply từ `main` qua `terraform-apply.yml`. |
| OIDC (CI to AWS) | Đăng nhập liên kết OIDC | CI lấy quyền AWS ngắn hạn mà không cần khoá cố định. | Chỉ tin `refs/heads/main` (AA-866). |
| ECS exec, S3-mediated | ECS exec qua S3 | Chạy một script trong container CIS: tải lên S3, tạo link presign, curl vào container, chạy bằng python3. | Cách chuẩn để vào RDS riêng (D-07); mọi phiên đều được ghi log. |
| Break-glass | Lối khẩn cấp | Một thông tin đăng nhập hay công tắc khẩn cấp, chỉ dùng khi lối thường không vào được. | User Cognito `breakglass` có TOTP; RDS master (DM-8.9). Runbook OPS-10. |
| Observability | Khả năng quan sát | Hiểu hệ thống qua log, chỉ số và trace. | CloudWatch, Sentry (CIS, Booking, TripPlanner), các trang admin. |
| Log retention | Thời gian giữ log | Log được giữ bao lâu. | Log bảo mật (flow, WAF, ECS exec, PostgreSQL) 365 ngày, log ứng dụng 30 ngày (D-09, AA-872). |
| SLI / SLO / SLA / error budget | Chỉ số / mục tiêu / cam kết / ngân sách lỗi | Số đo / mục tiêu / hợp đồng / phần lỗi được phép. | SLO có khi có prod đầu tiên (AA-880, U-49). |
| RPO / RTO | Mất dữ liệu tối đa / thời gian dừng tối đa | Lượng dữ liệu mất / thời gian dừng chấp nhận được. | Mục tiêu trong DM-9.6; các lần diễn tập khôi phục trên Dev mất khoảng 22 phút (S241) và 21 phút (S249). |
| PITR | Khôi phục theo thời điểm | Khôi phục cơ sở dữ liệu về bất kỳ thời điểm nào trong khoảng lưu giữ. | RDS Dev giữ 7 ngày; prod sẽ giữ 14 ngày (C7.2b). |
| Restore drill | Diễn tập khôi phục | Tập khôi phục và ghi lại RTO. | Dev: khi quy trình đổi và một lần trước prod; prod: mỗi quý (DM-9.3). |
| FinOps / unit cost | Quản trị chi phí / chi phí đơn vị | Quản lý chi phí cloud / chi phí cho mỗi đơn vị kinh doanh. | USD LLM cho mỗi tour được xuất bản; xem lại hằng tháng (FIN-02). |
| Cost allocation tag | Tag phân bổ chi phí | Tag mà Cost Explorer dùng để chia chi phí. | `App` (bật trong Billing từ 15/10/2026) và `Environment` (DM-10.1). |
| Ledger | Sổ ghi chi phí | Bảng ghi mọi lần gọi trả phí kèm chi phí. | `shared.llm_call_log`, `shared.decision_log`, `shared.dfs_call_log` (DM-10.4). |
| SBOM | Danh mục thành phần phần mềm | Danh sách mọi thư viện và version trong một artifact. | syft trong CI của CIS (AA-177). |
| SLSA / provenance | SLSA / nguồn gốc build | Các mức tin cậy chuỗi cung ứng / bằng chứng ai build gì từ commit nào. | Để sau (U-43, prod đầu tiên). |

## Dữ liệu

| Thuật ngữ | Tiếng Việt | Nghĩa | Trong AA-Ecosys |
|---|---|---|---|
| Migration | Migration (thay đổi cấu trúc DB) | Một file SQL có đánh số, thay đổi schema. | Khoá `NNN` (CIS), `tp-NNN`, `bk-NNN`, `crm-NNN`; áp bằng DB Migrate của Infra. |
| Forward-only | Chỉ tiến | Không bao giờ lùi schema; muốn bỏ thì viết một migration mới. | Quy tắc của DB Migrate; app bản cũ phải chạy được trên schema mới. |
| Idempotent | Chạy lại không đổi kết quả | Chạy hai lần có tác dụng như chạy một lần. | `ON CONFLICT DO NOTHING` trong `schema_versions`. |
| Schema owner | Chủ schema | Repo duy nhất được viết migration và ghi dòng cho một schema. | [`schema-ownership.md`](database/schema-ownership.md); sổ đăng ký `db/owners.yaml` trong Infra. |
| Kernel schema | Schema lõi dùng chung | `shared`: chỉ gồm tenant, điểm đến, quốc gia, cổng LLM và `schema_versions`. | DM-1.5; bảng của app nằm trong schema của chủ app. |
| Contract (event / API / view) | Hợp đồng dữ liệu | Giao diện có version giữa các app. | `docs/contracts/`, view `catalog.*` (ADR 0008). |
| RLS | Bảo mật mức dòng | Bảo mật mức dòng của PostgreSQL, lọc dòng theo tenant. | Tenant pool và isolation probe (AA-817, U-16). |
| Tenant pool | Pool kết nối theo tenant | Pool kết nối DB có role bị RLS ràng buộc. | Đóng an toàn trên toàn hệ thống khi lỗi (fail-closed, D-12). |
| Dead Table Registry | Danh sách bảng chết | Các bảng còn giữ nhưng không còn ghi, kèm kế hoạch xoá. | ARCH-09 (AA-850). |
| PII | Dữ liệu cá nhân | Dữ liệu nhận diện được một người. | Dev chỉ có dữ liệu thử (D-01); nhãn cột `pii:` (DM-6.1, AA-877). |

## Vận hành LLM

| Thuật ngữ | Tiếng Việt | Nghĩa | Trong AA-Ecosys |
|---|---|---|---|
| LLMOps | Vận hành LLM | Quản lý version prompt và model, eval, theo dõi chất lượng và chi phí. | APP-06 (AA-900, đã thu hẹp). |
| Model Gateway | Cổng gọi model | Điểm duy nhất để gọi model trả phí. | `LLMClient.generate()` ghi `shared.llm_call_log`. |
| Writer / judge / validate | Người viết / người chấm / kiểm | Ba vai trò LLM trong pipeline. | Cột `role` trong `shared.llm_call_log`. |
| Eval / golden set | Đánh giá / bộ mẫu chuẩn | Một bộ mẫu cố định để chấm chất lượng LLM trước khi đổi prompt hay model. | Khoảng 100 mẫu (AA-729); chạy tay hoặc dispatch (D-23). |
| Shadow run | Chạy song song | Chạy model hay tuyến mới cạnh tuyến đang dùng mà không trả kết quả của nó ra ngoài. | `shared.llm_shadow_log`. |
| Jev | Jev | Dịch vụ quyết định bên ngoài, đưa ra phán quyết về nội dung. | `decide()` ghi `shared.decision_log`. |
| Atom | Atom | Một mẩu nội dung tour dùng lại được, do pipeline chuỗi A tạo ra. | Đọc qua `acp_contract.v_active_tour_atoms`. |
| A-series / T-series | Chuỗi A / chuỗi T | Các bước pipeline admin A0-A4 / các bước tenant T0-T11. | CONTEXT.md của CIS. |

## Chương trình và quản trị

| Thuật ngữ | Tiếng Việt | Nghĩa | Trong AA-Ecosys |
|---|---|---|---|
| Dev phase | Giai đoạn Dev | Hiện nay: chỉ có môi trường Dev, không có người dùng thật, chỉ có dữ liệu thử. | Agent merge sau khi CI xanh (D-13; DM-11.5 ở v1.1). |
| Prod | Môi trường prod | Môi trường chạy thật sau này. | Một RDS instance riêng trên acc2 (ADR 0001, C7.2a, D-17); chốt ngày khi go-live (AA-880). |
| Data standards | Chuẩn dữ liệu | Các quy tắc bắt buộc MIG-x (Phần A), DM-x (Phần B) và C-x (Phần C) cho RDS dùng chung. | [`docs/architecture/data-standards/`](architecture/data-standards/README.md), version 1.6 (28/10/2026). |
| U-xx / D-xx | Mục lộ trình / quyết định | Các mục lộ trình của S241 / các quyết định tech lead đã ghi lại. | [Handbook §9–§10](engineering-handbook.md#9-roadmap); bản ghi D-xx trong `docs/sessions/2026-10-17-S241-decisions.md`. |
| Session (`S<nnn>`) | Phiên làm việc | Một phiên làm việc có đánh số và có log. | `docs/sessions/`, memory Notion. |
| CODEOWNERS | CODEOWNERS | File GitHub chỉ định người review bắt buộc theo đường dẫn. | Để sau, cần một danh tính agent riêng (U-25). |
| NIST SSDF (SP 800-218) | Khung phát triển an toàn NIST | Các thực hành phát triển phần mềm an toàn, chia bốn nhóm. | Danh sách đọc, để sau. |
| Workforce pool | Pool nhân viên | User pool Cognito cho nhân viên đăng nhập. | Nhân viên CIS đăng nhập bằng mã gửi qua e-mail (ADR 0006a). |
