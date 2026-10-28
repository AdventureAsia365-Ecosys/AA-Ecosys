---
id: CAT-01
title: Sổ tay kỹ thuật AA-Ecosys
description: Trang duy nhất mô tả cách AA-Ecosys được xây, viết tài liệu, đánh phiên bản, phát hành, vận hành và chi trả - mô hình làm việc, vòng đời, hệ tài liệu, phiên bản, phát hành, vận hành, chi phí, lộ trình nền tảng đã gộp và nhật ký quyết định.
type: explanation
status: draft
owner: nghiep
audience: [owner, engineer, devops, cto, cio, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-19
review_every_days: 90
related: [CAT-00, TPL-02, GUIDE-02, GUIDE-03, ARCH-08, OPS-01, FIN-01, AA-887]
lang: vi
translation_of: docs/engineering-handbook.md
---

# Sổ tay kỹ thuật AA-Ecosys

Trang này là nguồn duy nhất trả lời **chúng ta xây, viết tài liệu, đánh phiên bản, phát hành, vận hành và chi trả cho
AA-Ecosys như thế nào**. Nó thay bản review SDLC và lộ trình nền tảng S241 cùng bốn file tư vấn S243 (liệt kê ở
[§12](#12-lịch-sử-thay-đổi-và-các-tài-liệu-bị-thay-thế)). Trang không chép lại các luật đã có nơi chuẩn: nó nêu tên và
dẫn link tới đó. Khi một luật nằm trong data standard, ADR hay skill, file đó thắng và trang này chỉ trỏ tới.

AA-Ecosys gồm bốn app trên một tài khoản AWS (acc2): **AA-CIS** (nội dung và catalog), **AA-TripPlanner-Web** (cửa
vào cho khách du lịch), **AA-Booking** (khách hàng, hồ sơ chuyến đi, giá, thanh toán) và **AA-Partner** (CRM cho đại
lý đối tác và tenant portal), cộng repo Terraform **AA-CIS-Infra** và repo gốc này (tạm thời public, theo bản sửa đổi
[ADR 0014](adr/0014-repo-visibility-and-github-plan.md)). Hiện chỉ có một môi trường, **Dev**, chỉ chứa dữ liệu test
(D-01). Đội gồm một kỹ sư, tech lead, làm việc cùng các AI agent (Claude Code, Kiro) cho một chủ doanh nghiệp.

> **Dành cho chủ doanh nghiệp (CEO):** Hệ chạy trên một môi trường thử dùng chung (Dev, chỉ dữ liệu test); prod chỉ
> dựng khi đã có ngày go-live. Mọi thay đổi phải qua kiểm tra tự động và được kiểm trên hệ thật mới tính là xong. Chi
> tiêu: ngân sách tài khoản hiện là 300 USD/tháng; mọi chi phí AWS mới đều được báo giá trước và duyệt từng mục. Phần
> chị quyết: kinh doanh, pháp lý và giá. Chị nhận bản tóm tắt tiếng Việt ngắn về chi phí hằng tháng, các bản phát hành
> và mọi sự cố. Hướng dẫn dành cho chị: [CEO guide](guides/ceo.md).

Cách đọc:

| Vai trò | Đọc trước |
|---|---|
| CEO | Khung ở trên, [§8.3](#83-review-hằng-tháng), [§9.3](#93-không-làm-bây-giờ), [CEO guide](guides/ceo.md) |
| CTO / CIO | [§1](#1-mục-đích-phạm-vi-và-thứ-tự-ưu-tiên), [§2](#2-mô-hình-làm-việc), [§5](#5-phiên-bản), [§7](#7-vận-hành), [§9](#9-lộ-trình), [§10](#10-nhật-ký-quyết-định) |
| DevOps | [§6](#6-phát-hành-và-thay-đổi-tính-năng), [§7](#7-vận-hành), [§8](#8-chi-phí-finops), [DevOps guide](guides/devops.md) |
| PM | [§2](#2-mô-hình-làm-việc), [§3](#3-các-giai-đoạn-vòng-đời), [§6.4](#64-definition-of-ready-và-done), [§9](#9-lộ-trình) |
| Kỹ sư mới / agent | [§1](#1-mục-đích-phạm-vi-và-thứ-tự-ưu-tiên)-[§4](#4-hệ-thống-tài-liệu), [onboarding](onboarding.md), [agents.md](agents.md) |

| Nếu bạn muốn | Đọc |
|---|---|
| Luật chơi trong năm phút | [§1](#1-mục-đích-phạm-vi-và-thứ-tự-ưu-tiên) và [§2](#2-mô-hình-làm-việc) |
| Một việc đi từ ý tưởng tới chi phí ra sao | [§3](#3-các-giai-đoạn-vòng-đời) |
| Tài liệu đặt ở đâu và viết thế nào | [§4](#4-hệ-thống-tài-liệu) |
| Phiên bản, phát hành, migration, phiên bản API và prompt | [§5](#5-phiên-bản) và [§6](#6-phát-hành-và-thay-đổi-tính-năng) |
| Alarm, sự cố, backup, secret, quyền truy cập | [§7](#7-vận-hành) |
| Tiền | [§8](#8-chi-phí-finops) |
| Việc tiếp theo, việc đã xong, việc sẽ không làm | [§9](#9-lộ-trình) |
| Vì sao một thứ lại như vậy | [§10](#10-nhật-ký-quyết-định) |
| Một từ bạn chưa biết | [§11](#11-thuật-ngữ) |

---

## 1. Mục đích, phạm vi và thứ tự ưu tiên

### 1.1 Mục đích

- Cho mọi người đọc (chủ doanh nghiệp, kỹ sư, DevOps, CTO, CIO, PM, agent) một nơi giải thích toàn bộ hệ thống giao
  việc và dẫn tới trang giữ từng luật.
- Giữ **một** lộ trình nền tảng ([§9](#9-lộ-trình)) và **một** nhật ký quyết định ([§10](#10-nhật-ký-quyết-định)).
- Chấm dứt tình trạng lệch mà S241 và S243 phát hiện: cùng một sự thật được chép vào năm chỗ, mỗi chỗ hơi khác.

### 1.2 Phạm vi

Trong phạm vi: quy trình, tài liệu, phiên bản, phát hành và deploy, vận hành, vận hành bảo mật, chi phí, và lộ trình
nền tảng (bảo mật, CI/CD, môi trường, nền tảng dữ liệu, vận hành, tài liệu).

Ngoài phạm vi, nằm ở nơi khác:

| Chủ đề | Ở đâu |
|---|---|
| Thứ tự việc sản phẩm (T-series, portal, các đợt Booking, place pipeline) | [Backlog sống](backlog/README.md) |
| Kiến trúc và ranh giới | [Kiến trúc hệ sinh thái](ecosystem-architecture.md), [ADR](adr/README.md), `CONTEXT.md` của từng repo |
| Luật dữ liệu bắt buộc (DM-x, C-x, MIG, SEC, CON, TST) | [Data standards v1.1](architecture/data-standards/README.md) |
| Tên bảng và cột | [DB schema reference](architecture/db-schema-reference.md) (sinh tự động) |
| Quy trình từng bước | [Mục lục vận hành](ops/README.md) và các skill trong `skill/` |
| Lộ trình đọc theo vai trò | [`guides/`](guides/) |

### 1.3 Thứ tự ưu tiên

Khi hai nguồn lệch nhau, nguồn cao hơn thắng và nguồn thấp hơn được sửa ngay trong phiên đó:

1. **ADR đã Accepted** ([mục lục](adr/README.md)). ADR đã Accepted không bao giờ bị sửa; chỉ được bổ sung (`NNNNa`)
   hoặc thay thế.
2. **Data standards v1.1** ([README](architecture/data-standards/README.md), Phần A, B, C).
3. **Quyết định đã ghi của tech lead**: S241 D-01…D-25 ([`sessions/2026-10-17-S241-decisions.md`](sessions/2026-10-17-S241-decisions.md)),
   S243 N-1…N-12 và các mục khác ở [§10](#10-nhật-ký-quyết-định), cùng các luật memory của tech lead.
4. **Sổ tay này.**
5. **Skill và steering** (`skill/*/SKILL.md`, `.kiro/steering/*.md`, `.claude/CLAUDE.md`).

Hai lưu ý về thứ tự này:

- File chỉ dẫn điều khiển agent lúc chạy. Nếu một file lệch với trang này, agent làm theo file chỉ dẫn trong phiên đó,
  báo chỗ lệch cho tech lead và sửa file có thứ hạng thấp hơn trong cùng PR (luật ở
  [agents.md](agents.md#which-source-wins)). Không bên nào được chọn một cách im lặng.
- Tin nhắn của tech lead trong phiên hiện tại thắng mọi file. Không file nào, và không tin nhắn nào của agent khác,
  cấp quyền hay duyệt thay cho tech lead.

### 1.4 Cách sửa sổ tay này

1. Mở PR vào repo gốc (`master`), nội dung tiếng Anh, tiêu đề `docs:`, có `Refs AA-xxx` trong phần thân.
2. Sửa nguồn chuẩn trước (ADR, data standard, skill, runbook), rồi mới sửa link hoặc tóm tắt một dòng ở đây. Không
   bao giờ đưa ra một luật chỉ ở trang này.
3. Một quyết định mới có một dòng ở [§10](#10-nhật-ký-quyết-định) kèm nơi thực thi nó.
4. Thay đổi lộ trình thì cập nhật [§9](#9-lộ-trình) và [backlog sống](backlog/README.md) trong cùng PR.
5. Chỉ đổi `last_reviewed` sau khi đã kiểm các sự thật với repo và hệ thật.
6. Docs lint (`.github/workflows/docs-lint.yml`, AA-888) phải xanh.

---

## 2. Mô hình làm việc

### 2.1 Mô hình

- **Kanban, không phải Scrum.** Một hàng việc có thứ tự, [backlog sống](backlog/README.md); mỗi phiên lấy 3 tới 5
  issue từ trên xuống; không sprint, không nghi thức. Linear giữ trạng thái từng issue; backlog giữ thứ tự.
- **DevOps.** Người hoặc agent xây một thay đổi cũng là người deploy, kiểm live và theo dõi nó.
- **Trunk-based development** (ADR-2026-023). Nhánh ngắn, PR, CI bắt buộc, squash merge vào `main` (`master` ở repo
  gốc). Không có nhánh `develop`. Làm việc trên nhánh hoặc worktree tạo từ `origin/main` mới nhất.
- **ADLC = SDLC + kiểm soát agent + vòng đời tính năng LLM.** ADLC không phải thuật ngữ chuẩn; đây là định nghĩa của
  chúng ta:
  - *Kiểm soát agent*: agent viết phần lớn code. Việc của người chuyển sang viết issue (DoR), cung cấp ngữ cảnh
    (`CONTEXT.md`, steering, skill), gác cổng (CI, review, kiểm live) và giữ các quyền nguy hiểm.
  - *Vòng đời tính năng LLM* (LLMOps): phiên bản prompt và model, eval, sổ cái chi phí và shadow run cho các vai trò
    writer, judge và validate ([§5.7](#57-prompt-và-model-llm)).
- **AI khuếch đại quy trình bạn đang có.** DoR, CI và kiểm live tốt thì lợi gấp đôi khi agent viết phần lớn code;
  yếu thì hỏng gấp đôi.

### 2.2 Nguồn sự thật cho trạng thái quy trình

| Cái gì | Nguồn chuẩn | Nơi khác chỉ dẫn link |
|---|---|---|
| Thứ tự việc | [Backlog sống](backlog/README.md) | Notion memory |
| Trạng thái một issue | Linear (team AA_Ecosys) | backlog, log phiên |
| Điều gì đã xảy ra trong một phiên | `docs/sessions/` (tiếng Việt) | Notion memory HOT (tóm tắt + link) |
| Tiến độ báo cho chủ doanh nghiệp | Jira (soạn nháp, rồi tech lead duyệt) | — |
| Cách làm một việc | `skill/*/SKILL.md` | tóm tắt steering, CLAUDE.md |
| Bài học | [`skill/aa-lessons/lessons.md`](../skill/aa-lessons/lessons.md) | — |

Khi repo, Notion và memory lệch nhau: repo > trang Notion chuẩn > memory > skill
([`session-workflow.md`](../.kiro/steering/session-workflow.md)).

### 2.3 Vai trò

| Vai trò | Làm | Không làm | Hướng dẫn |
|---|---|---|---|
| **Tech lead** (kỹ sư, chủ nền tảng) | Duyệt DoR, ADR, chi tiêu (D-19), quyết định prod; override cổng deploy; tự tay sửa env var có dấu gạch dưới và `~/.claude/CLAUDE.md` | — | [Kỹ sư mới](guides/new-engineer.md), [DevOps](guides/devops.md) |
| **Chủ doanh nghiệp** (CEO) | Quyết việc kinh doanh, pháp lý và thương mại; xem release note, tóm tắt chi phí và UAT | Duyệt kỹ thuật | [CEO guide](guides/ceo.md) |
| **Claude Code, phiên chính** | Chọn việc, viết hoặc giao code, gác cổng, merge và deploy trên Dev trong giai đoạn dev, chạy Terraform và DB Migrate, cập nhật Linear | Đăng lên Jira khi chưa được duyệt; đụng vào prod (khi có) mà không có tech lead | [Mục lục agent](agents.md) |
| **Kiro và subagent** | Code, test và commit trên một nhánh | Push, merge, apply, ghi ECS/RDS/IAM, secret ([`subagent-guardrails.sh`](../.claude/hooks/subagent-guardrails.sh)) | [Mục lục agent](agents.md) |
| **`kiro-reviewer`** (agent) | Review PR rủi ro: auth hoặc phân quyền, migration hoặc schema, CI/workflow/secret, xoá dữ liệu ([`kiro-reviewer.md`](../.claude/agents/kiro-reviewer.md)) | Merge | — |
| **CI** | Check bắt buộc ở mọi repo app; CIS, Booking và Partner merge qua GitHub merge queue (AA-889). Docs lint của repo gốc chạy trên mọi PR gốc nhưng không phải check bắt buộc; agent merge kiểm nó xanh trước khi merge | — | [CTO](guides/cto.md#quality-gates) |
| Người đọc CTO, CIO, PM | Góc nhìn quản trị, bảo mật và tuân thủ, kế hoạch | — | [CTO](guides/cto.md), [CIO](guides/cio.md), [PM](guides/pm.md) |

Quyền merge theo giai đoạn: [§6.5](#65-quyền-merge-theo-giai-đoạn).

---

## 3. Các giai đoạn vòng đời

| # | Giai đoạn | Việc gì xảy ra | Ai | Sản phẩm | Ở đâu |
|---|---|---|---|---|---|
| 1 | Ý tưởng | Một yêu cầu của chủ doanh nghiệp (Jira), một phát hiện từ audit hay alarm, một bài học | Tech lead | Issue Linear | Linear; Jira cho phía kinh doanh |
| 2 | Sắp thứ tự | Xếp hạng trong hàng việc; các kiểm tra theo mốc thời gian | Tech lead + Claude Code | Dòng backlog | [Backlog sống](backlog/README.md) |
| 3 | **Sẵn sàng (DoR)** | Vấn đề, mục tiêu, phạm vi, tiêu chí nghiệm thu, cách kiểm, loại rủi ro, phụ thuộc, ảnh hưởng tài liệu | Claude Code soạn, tech lead xác nhận | Thân issue | [Mẫu DoR](templates/definition-of-ready.md), [`aa-linear-issue`](../skill/aa-linear-issue/SKILL.md) |
| 4 | Thiết kế | Ranh giới, contract hoặc lựa chọn khó đảo ngược | Claude Code đề xuất, tech lead chấp nhận | ADR hoặc bản bổ sung; `CONTEXT.md`; phiên bản contract | [Nơi đặt ADR](../skill/ai-nghiep/references/adr.md), [mẫu ADR](templates/adr.md), [contracts](contracts/README.md) |
| 5 | Xây | Code trên nhánh ngắn hoặc worktree; ghi implementation note trong lúc làm | Kiro / subagent / Claude Code | Conventional commit, `Refs AA-xxx` | `docs/implementation-notes/<ISSUE>.md` (và theo từng repo) |
| 6 | Review và test | CI; agent review cho các loại rủi ro; checklist tài liệu | CI + Claude Code + `kiro-reviewer` | PR = bản ghi thay đổi (rủi ro, rollback, chi phí, tài liệu) | [Mẫu PR](../.github/pull_request_template.md) |
| 7 | Phát hành và deploy | Merge; image `dev-<sha>`; deploy Dev; migration qua DB Migrate | Claude Code (giai đoạn dev) | Revision task definition; deployment Vercel; sau này tag + CHANGELOG | [§5](#5-phiên-bản), [§6](#6-phát-hành-và-thay-đổi-tính-năng), [mục lục vận hành](ops/README.md#how-each-app-is-deployed-app-01) |
| 8 | **Kiểm (Xong)** | Rollout COMPLETED, api và worker cùng SHA, kiểm endpoint live, kiểm UI | Claude Code | Comment "Verified live" kèm bằng chứng | [`aa-ship`](../skill/aa-ship/SKILL.md) |
| 9 | Vận hành | Alarm, Sentry, sự cố, backup, secret, quyền truy cập | Tech lead + Claude Code | Các lần chạy runbook, bản ghi sự cố | [§7](#7-vận-hành) |
| 10 | Rút bài học | Nguyên nhân gốc → luật → CI guard | Claude Code viết, tech lead duyệt | Dòng bài học, test guard, postmortem | [`lessons.md`](../skill/aa-lessons/lessons.md), [mẫu postmortem](templates/postmortem.md) |
| 11 | Chi phí | Báo giá trước khi chi; review hằng tháng; cảnh báo bất thường | Claude Code báo cáo, tech lead quyết | Review chi phí và dung lượng hằng tháng | [§8](#8-chi-phí-finops) |
| 12 | Báo phía kinh doanh | Release note kinh doanh cho việc đã ship và đã kiểm | Claude Code soạn, tech lead duyệt | Comment Jira | [Mẫu release note](templates/release-note.md), skill `aa-jira-update` |

Lưu ý:

- Issue thiếu một mục DoR thì không giao cho Kiro hay subagent.
- Giai đoạn 8 là Definition of Done. Đã merge và xanh chưa phải là xong ([§6.4](#64-definition-of-ready-và-done)).
- Nhật ký (log phiên, audit, implementation note, backlog) ghi lịch sử. Chúng không bao giờ là sự thật hiện hành cho
  một luật.

---

## 4. Hệ thống tài liệu

### 4.1 Diátaxis: bốn loại trang

| Loại | Người đọc cần | Hình dạng | Ví dụ |
|---|---|---|---|
| Tutorial | Học bằng cách làm | Các bước có dẫn dắt, chắc chắn ra kết quả | [Onboarding](onboarding.md), [hướng dẫn kỹ sư mới](guides/new-engineer.md) |
| How-to (gồm runbook) | Làm một việc | Các bước, lệnh một dòng, cách kiểm, rollback | [Runbook](ops/README.md#runbooks), [playbook](ops/README.md#something-is-wrong) |
| Reference | Sự thật chính xác | Bảng khô; sinh tự động khi có thể | [Schema reference](architecture/db-schema-reference.md), [sổ đăng ký secret](security/secrets-register.md) |
| Explanation | Vì sao lại như vậy | Bối cảnh, thiết kế, đánh đổi, link tới ADR | [Kiến trúc](ecosystem-architecture.md), [data standards](architecture/data-standards/README.md), trang này |

Một trang, một loại, một người đọc chính. Nhật ký (`docs/sessions/`, `docs/audits/`, `docs/implementation-notes/`,
`docs/backlog/`, `docs/research/`) nằm ngoài Diátaxis và không phải sự thật hiện hành.

### 4.2 Danh mục là cửa vào duy nhất

[`docs/README.md`](README.md) (CAT-00) liệt kê mọi trang được duy trì kèm ID, loại, đường dẫn, chế độ (viết tay hay
sinh tự động), chủ, nhịp review, người đọc và trạng thái, và mở đầu bằng mục "Start here" theo vai trò. Trang không có
trong danh mục là nhật ký hoặc bản nháp. Agent bắt đầu từ [`agents.md`](agents.md) và [`llms.txt`](llms.txt).

### 4.3 Tài liệu nằm ở đâu

| Nơi | Vai trò | Luật |
|---|---|---|
| **Git** (repo gốc, Infra, repo app) | Nguồn duy nhất | Đổi bằng PR, review cùng code |
| Repo gốc (mặc định private; hiện tạm public, theo bản sửa đổi [ADR 0014](adr/0014-repo-visibility-and-github-plan.md)) | Tài liệu hệ sinh thái, bản đồ tài khoản, tài liệu bảo mật và hạ tầng, audit, các sổ đăng ký theo tên | [Trang được đặt ở đâu](STYLE.md#where-a-page-may-live-sec-06) |
| Repo app (public) | `CONTEXT.md`, ADR của app, how-to an toàn khi public, tài liệu LLM không có dữ liệu tenant | Không account ID, ARN, ID SG/VPC, inventory, danh sách secret, báo cáo bảo mật (DM-6.10, D-14, D-25) |
| Google Drive (thư mục AdventureAsia) | Bản PDF xuất ra và video UAT cho chủ doanh nghiệp | Không bao giờ là nguồn; mỗi bản xuất ghi rõ lấy từ commit nào |
| `/admin/docs` trong CIS admin (AA-898, đã live) | Một **trang đọc**, không phải trình soạn | Đồng bộ từ một checkout CI chỉ gồm file được track, không bao giờ từ laptop ([`docs-sync.yml`](../.github/workflows/docs-sync.yml)); luật xuất bản v1 trong [danh mục](README.md#admin-docs-page-allowlist-aa-898): chỉ trang danh mục và ADR; nhật ký, `docs/security/` và `docs/audits/` không bao giờ được đồng bộ (chặt hơn N-3, vốn cho phép trang bảo mật chỉ owner xem); trang `SEC-*` ở nơi khác và các bản đồ hạ tầng sinh tự động chỉ owner xem qua kiểm tra ở backend (N-3); account ID và ID tài nguyên bị che, có guard lúc build; prefix `docs-reader/` của bucket bronze (`App=cis`, mã hoá, chặn truy cập public), dưới 0,10 USD/tháng |
| Một site tài liệu riêng (Starlight trên S3 + CloudFront + Cognito) | Chỉ ở giai đoạn 3 | Điều kiện kích hoạt: hơn hai kỹ sư, một nhà thầu không có quyền admin, hoặc tài liệu prod phải đọc được khi CIS chết. Không MkDocs, không Backstage, không Vercel Pro cho tài liệu |

Trước prod, một bản PDF break-glass gồm mục lục vận hành, các runbook rollback và quy trình xử lý sự cố được đưa lên
Drive, vì trang admin docs chết cùng CIS (AA-880).

### 4.4 Front-matter, mẫu và văn phong

- Front-matter: [`templates/frontmatter.schema.json`](templates/frontmatter.schema.json). Bắt buộc `id`, `title`,
  `type`, `status`, `owner`, `last_reviewed`; `status` là một trong draft, active, deprecated, superseded, archived;
  `audience` dùng owner, staff, engineer, devops, cto, cio, pm, agent.
- Mẫu: [`templates/`](templates/) (runbook, how-to, reference, explanation, ADR, postmortem, báo cáo chi phí,
  release note, báo cáo UAT, Definition of Ready, hướng dẫn vai trò).
- Văn phong: [`STYLE.md`](STYLE.md): giọng văn, AWS CLI một dòng có `--profile` và `--region`, dùng tên chứ không dùng
  ID tài nguyên, luật "đã test" cho runbook, callout, sơ đồ, đặt tên.
- ADR giữ dòng `Status` riêng và được bổ sung chứ không bị sửa ([luật nơi đặt ADR](../skill/ai-nghiep/references/adr.md)).

### 4.5 Luật docs-as-code

1. **Tài liệu đổi trong cùng PR với code nó mô tả.** [Mẫu PR](../.github/pull_request_template.md) có checklist tài
   liệu; AA-890 thêm mẫu vào mọi repo.
2. **Khi nào phải cập nhật tài liệu:**

   | Khi bạn đổi | Cập nhật |
   |---|---|
   | Ranh giới app, stack, quyền sở hữu dữ liệu | `CONTEXT.md` của repo đó (+ [kiến trúc](ecosystem-architecture.md) nếu ảnh hưởng cả hệ) |
   | Một quyết định mà chỉ sửa repo khác mới đảo ngược được | ADR hoặc bản bổ sung ([nơi đặt](../skill/ai-nghiep/references/adr.md)) |
   | Cấu trúc schema | Không sửa tay: workflow DB Schema Dump mở PR reference; merge nó (DM-11.2) |
   | Một endpoint public hoặc hình dạng response | OpenAPI (sinh tự động, AA-899) và CHANGELOG (AA-891) |
   | Một event hoặc read model giữa các app | Một phiên bản contract mới theo [contracts](contracts/README.md) |
   | Một quy trình vận hành | Runbook và [mục lục vận hành](ops/README.md) |
   | Một tài nguyên AWS tốn tiền | Chi phí hằng tháng trong PR (D-19) |
   | Một prompt, model hoặc route | ID lần chạy eval trong PR ([§5.7](#57-prompt-và-model-llm)) |
   | Một cờ | Một dòng trong [sổ đăng ký cờ](ops/feature-flags.md) |

3. **Trang sinh tự động không bao giờ được sửa tay.** Chúng có `generated: true`, một generator và dòng đầu
   "GENERATED … do not edit"; chỉ PR của generator mới đổi chúng.
4. **`last_reviewed` nghĩa là đã kiểm với hệ thật.** Agent chỉ đổi nó sau khi chạy lệnh kiểm hoặc đọc nguồn, và ghi
   rõ trong PR. Sửa lỗi chính tả không đổi nó.
5. **Trang mới do agent viết bắt đầu ở `draft`** cho tới khi tech lead đã đọc (đọc gộp cuối phiên là được trong giai
   đoạn dev).
6. **Không file nhị phân trong git.** Bảng tính, file nén và video đưa lên Drive hoặc S3; git giữ link.
7. **Không giá trị secret, không dữ liệu khách hàng thật, không bản dump.** Tên secret thì được phép trong repo gốc
   private.
8. **Các PR song song không bao giờ cùng ghi nối vào một file ghi chú.** Mỗi PR ghi mục hoặc file riêng (bài học trong
   [`lessons.md`](../skill/aa-lessons/lessons.md)).
9. **`docs/` của CIS chỉ được track sau khi quét.** AA-889 thay luật bỏ qua toàn bộ bằng "track Markdown, bỏ qua file
   nhị phân", sau khi gitleaks và kiểm ID tài nguyên đạt trên mọi file được thêm. Chi tiết hạ tầng hay bảo mật chuyển
   sang repo gốc private; tech lead review danh sách file được thêm một lần (DM-6.10, D-25).
10. **Deprecate rồi mới archive** ([STYLE](STYLE.md#deprecate-and-archive)). Trang lỗi thời có `status: deprecated`,
    `superseded_by` và một dòng cảnh báo ở đầu; sau một quý không dùng thì chuyển vào `docs/archive/YYYY/` với
    `status: archived`. ADR không bao giờ bị archive (chỉ bị thay thế hoặc bổ sung).

### 4.6 Reference sinh tự động

| Reference | Nguồn | Generator | Trạng thái |
|---|---|---|---|
| DB schema (mọi schema, role, grant, RLS) | Catalog live | Workflow DB Schema Dump của Infra (mỗi đêm + sau mỗi lần DB Migrate apply), PR vào repo gốc | Live ([reference](architecture/db-schema-reference.md)) |
| Quyền sở hữu schema | Infra `db/owners.yaml` (sổ đăng ký, DM-1.2) | Test sổ đăng ký trong Infra; [schema-ownership](database/schema-ownership.md) giải thích nó | Live |
| Contract | JSON Schema theo từng phiên bản | Viết tay, hash được ghim trong test | Live; bảng sổ đăng ký AA-826 |
| OpenAPI theo app | FastAPI | CI export + oasdiff (AA-899) | Booking một phần; CIS đã lên kế hoạch |
| Sổ đăng ký env-config (chỉ tên) + ERD | Task definition live, cấu hình Lambda và Vercel; bản dump schema | Workflow của Infra, PR vào repo gốc (AA-894) | Live ([env-config](generated/env-config.md), [ERD](architecture/erd/README.md)) |
| Bảng alarm, inventory, network và IAM | Terraform | Workflow Docs Gen của Infra (AA-893), mỗi đêm và sau mỗi lần apply | Live ([alarm](generated/alarms.md), [inventory](generated/inventory.md), [network](generated/network.md), [IAM role](generated/iam-roles.md)) |
| Bảng route LLM | `shared.llm_role_config`, `shared.llm_model_catalog` | Export (AA-900) | Đã lên kế hoạch |
| Báo cáo độ mới | Front-matter | Lần chạy docs lint hằng tuần (AA-888) | Đi cùng PR gói tài liệu; chạy hằng tuần sau khi merge (workflow theo lịch chỉ chạy từ nhánh mặc định) |

Generator cần AWS thì chạy trong Infra, nơi có các OIDC role; repo gốc không có quyền AWS.

### 4.7 Độ mới và lint

Docs lint ([workflow](../.github/workflows/docs-lint.yml), [công cụ](../tools/docs/README.md), AA-888) kiểm trên mọi
PR tài liệu: front-matter theo schema và ID không trùng, trạng thái và mục lục ADR, không có AWS CLI ngắt dòng bằng
dấu gạch chéo ngược, link nội bộ (offline), văn phong Markdown (cảnh báo), ID tài nguyên viết thẳng (cảnh báo ở repo
private, lỗi ở repo public khi job của chúng được thêm). Secret được kiểm bằng một workflow riêng trên mọi PR, mọi
đường dẫn ([`secret-scan.yml`](../.github/workflows/secret-scan.yml): gitleaks trên các dòng được thêm; quét toàn bộ
lịch sử mỗi đêm ở [`secret-scan-history.yml`](../.github/workflows/secret-scan-history.yml), AA-981). Một lần chạy
hằng tuần viết báo cáo độ mới: các trang quá `review_every_days` (mặc định 90) và các runbook có `last_tested` cũ. Độ
mới chỉ cảnh báo; không bao giờ chặn merge. Đầu phiên, chọn một hai trang cũ để review cùng việc của phiên.

Mỗi quý một lần (khoảng 30 phút, trong phiên đầu tiên của quý, cùng lần review quyền truy cập ở
[§7.6](#76-quyền-truy-cập)): đi qua báo cáo độ mới, kiểm mục lục từng phần xem có trang mồ côi, hỏi sáu câu hỏi trụ cột
Well-Architected ("nếu X hỏng, trang nào cho biết phải làm gì?"), đọc CEO guide như chủ doanh nghiệp sẽ đọc, và chạy
phần Diagnose của một runbook ngẫu nhiên trên Dev. Nhịp này thuộc U-38 (AA-838).

### 4.8 Ngôn ngữ

Luật nằm ở [`language-convention.md`](../.kiro/steering/language-convention.md):

- Tài liệu kỹ thuật, code, commit, PR, Linear: **tiếng Anh**.
- Trao đổi với tech lead, log phiên, Notion memory, audit tư vấn cho tech lead trong `docs/audits/`: **tiếng Việt**.
- **Trang danh mục chỉ viết tiếng Anh** (S255, [§10.3](#103-s255-2026-10-28)). Không trang nào trộn hai thứ tiếng.
  Bản tiếng Việt là một bản dịch đầy đủ, trung thành, đặt trong file cùng tên `<name>.vi.md`, có cùng front-matter
  cộng `lang: vi` và `translation_of: <đường dẫn trang tiếng Anh>`. Trang tiếng Anh là nguồn; sửa trang đó thì cập
  nhật file `.vi.md` trong cùng PR. Luật này thay các trang song ngữ EN-VI của N-7 (CEO guide, các hướng dẫn vai trò
  và các tóm tắt tiếng Việt từng có trong sổ tay này).
- Tóm tắt kinh doanh cho chủ doanh nghiệp (tóm tắt chi phí, release note kinh doanh, tóm tắt postmortem): tiếng Việt,
  giản dị, không mã Linear nội bộ.

### 4.9 Sự thật nào nằm ở đâu

| Sự thật | Nơi chuẩn | Nơi khác chỉ dẫn link |
|---|---|---|
| Stack, ranh giới, quyền sở hữu của một app | `CONTEXT.md` của repo đó | CLAUDE.md, skill |
| Quyết định kiến trúc | ADR (repo gốc nếu từ hai repo trở lên, nếu không thì repo đó) | trang kiến trúc, `CONTEXT.md` |
| Tên bảng và cột | [Schema reference](architecture/db-schema-reference.md) (sinh tự động) | skill `aa-cis-schema` (chỉ giải thích) |
| Repo nào sở hữu schema nào | Infra `db/owners.yaml` | [schema-ownership](database/schema-ownership.md) |
| Luật dữ liệu, thời hạn lưu giữ, phê duyệt | [Data standards](architecture/data-standards/README.md); DM-7 là sổ đăng ký lưu giữ duy nhất | mọi nơi khác |
| Hình dạng API | OpenAPI sinh từ code | README, frontend |
| Event và read model giữa các app | [Contracts](contracts/README.md) | code app (hash được ghim) |
| Hạ tầng thật | Terraform trong AA-CIS-Infra + state của nó | `CONTEXT.md` của Infra |
| Account ID AWS | Bản đồ tài khoản trong [onboarding](onboarding.md#account-map) | file chỉ dẫn agent giữ một bản khớp |
| Phiên bản đang chạy | `/health` của từng service; sau này GitHub Deployments | log phiên |
| Secret (tên) | [Sổ đăng ký secret](security/secrets-register.md) (YAML trước) | sổ đăng ký env-config dẫn link |
| Cờ và công tắc ngắt khẩn | [Sổ đăng ký cờ](ops/feature-flags.md), [sổ đăng ký job kind](ops/job-kinds.md) | — |
| Quy trình | `skill/*/SKILL.md` | tóm tắt steering |
| Lộ trình nền tảng và quyết định | [§9](#9-lộ-trình), [§10](#10-nhật-ký-quyết-định) | [backlog §3a](backlog/README.md#3a-platform-roadmap-keys-plat-01) sắp thứ tự các mã U-xx |

---

## 5. Phiên bản

### 5.1 Commit

- Định dạng: luật commit chung (`feat|fix|chore|refactor|docs|ci|test|perf: description`, tiêu đề tiếng Anh), phần
  thân `Refs AA-xxx`. Không bao giờ `[AA-xx]` trong tiêu đề; không bao giờ `Fixes` hay `Closes` (Linear sẽ đóng
  issue). Tiêu đề PR trở thành commit squash, nên tiêu đề PR theo cùng luật.
- Đây là Conventional Commits hợp lệ. `Refs AA-xxx` không có dấu hai chấm là văn bản thân, không phải footer; Linear
  đọc nó và release-please bỏ qua nó. Giữ nguyên.
- Với release-please: `feat!:` hoặc footer `BREAKING CHANGE:` đánh dấu thay đổi phá vỡ. CHANGELOG hiển thị `feat`,
  `fix`, `perf`, `revert`; ẩn `docs`, `chore`, `refactor`, `test`, `ci`, `build`.
- Lint tiêu đề PR ở mọi repo: AA-890.

### 5.2 Phiên bản app và phát hành (AA-891)

| Repo | Cách đánh | Tag đầu tiên | `1.0.0` khi |
|---|---|---|---|
| AA-CIS-App | SemVer, release-please | `v0.4.0` (code hiện ghi 0.3.0) | Prod đầu tiên với OpenAPI `/v1` public ổn định |
| AA-Booking | SemVer | `v0.2.0` | Prod và một đối tác B2B dùng API |
| AA-TripPlanner-Web | SemVer | `v0.4.0` | Prod public |
| AA-CIS-Infra | Tuỳ chọn (tag theo ngày khi apply lớn, hoặc release-please) | `v0.1.0` | Một môi trường prod riêng |
| AA-Ecosys (gốc) | Không phát hành; tài liệu có phiên bản theo PR | — | — |

Cách cài release-please (AA-891):

- Chế độ manifest, mỗi repo một package, `bump-minor-pre-major: true` để thay đổi phá vỡ vẫn ở `0.x`.
- PR phát hành phải kích hoạt các check bắt buộc, nên action dùng **token GitHub App của AA-901** (0 USD). PAT
  fine-grained chỉ là phương án dự phòng nếu AA-901 trễ, và khi đó nó có một dòng trong
  [sổ đăng ký secret](security/secrets-register.md) (AA-878).
- CIS giữ một hằng số phiên bản (hiện phiên bản được ghi hai lần trong API), đánh dấu để bot tăng.
- `CHANGELOG.md` và manifest được các workflow deploy bỏ qua theo đường dẫn, hoặc chấp nhận một lần deploy thừa.
- PR phát hành của bot không có `Refs AA-xxx`; ngoại lệ này được AA-891 ghi vào `skill/aa-ship` §1. Tech lead tự tay
  thêm cùng dòng đó vào luật chung (N-6).
- Nhịp trên Dev: cắt một bản phát hành mỗi tuần hoặc ở một mốc cho chủ doanh nghiệp xem, không phải mỗi lần merge.
- CHANGELOG dành cho kỹ sư (các mục theo Keep a Changelog). Release note dành cho kinh doanh: viết tay từ CHANGELOG,
  chỉ cho tính năng đã kiểm live ([mẫu](templates/release-note.md)).
- GitHub Deployments và số liệu DORA ở lại cùng phần còn lại của U-47 tới prod đầu tiên.

### 5.3 Image và cái gì đang chạy

- **Image bất biến và được đặt tên theo commit:** CIS `dev-<sha>`, Booking theo git SHA; ECR IMMUTABLE, CIS giữ 30
  image `dev-*` gần nhất và cho hết hạn image không tag sau 7 ngày (AA-869). Không bao giờ `:latest`.
- Một revision task definition trỏ tới một SHA, nên **rollback = deploy lại revision trước**
  ([§6.3](#63-rollout-và-rollback)).
- **Mọi service tự báo đang chạy gì:** CIS `/health` trả `git_sha` và `/health/ready` kiểm độ sẵn sàng (AA-884, đã
  live trên CIS main); Booking `/booking/health` trả `git_sha` và `/booking/health/ready` kiểm DB và migration bắt
  buộc. Smoke sau deploy khẳng định SHA. Worker cũng báo SHA (api và worker phải khớp).
- Khi đã có tag phát hành, tag được gắn vào cùng digest; không build lại gì (build một lần, deploy nhiều nơi).
- Trang Apps trong admin (AA-884) hiển thị `service | git_sha | version | deployed_at` cho mọi service.
- Frontend: mỗi deployment Vercel mang commit của nó; hiển thị SHA ngắn ở footer admin dùng một biến có dấu gạch dưới
  mà tech lead tự tay đặt.

### 5.4 Migration cơ sở dữ liệu

- **Đánh số, chỉ tiến, chạy lại được, do CI áp**: key `NNN` (CIS), `tp-NNN`, `bk-NNN`, `crm-NNN`, role `rl-NNN`;
  `shared.schema_versions` ghi chúng lại. Không bao giờ sửa migration đã áp; thêm migration mới. Không bao giờ chạy
  DDL từ laptop, ECS exec hay lúc app khởi động.
- **Luồng D8** ([DM-11.2](architecture/data-standards/02-data-management.md#11-change-management), Phần A MIG-4): PR
  chỉ có migration → bản copy y hệt vào Infra → Copy Guard → DB Migrate `check` → `apply` → merge PR schema reference
  được sinh lại → rồi mới tới PR code. Runbook là [DB Migrate](ops/runbooks/db-migrate.md).
- **Expand / contract** cho mọi thay đổi mà hai phiên bản app phải cùng chạy được:
  1. Expand: thêm cột nullable hoặc bảng mới (PR chỉ có migration, áp trước).
  2. Deploy code ghi cả cũ lẫn mới; backfill qua một job.
  3. Chuyển phần đọc sang cấu trúc mới.
  4. Contract ở một bản phát hành sau: xoá cái cũ (`-- migrate: destructive`, có snapshot tự động trước).
  Phiên bản N và N+1 của app đều chạy được trên schema, nên rollback app luôn an toàn.
- DB Migrate `apply` chờ mọi bảng job rảnh (DM-11.4). Deploy app không còn chờ bảng job rảnh: từ AA-993 G5, chúng chỉ
  chờ các job kind chặn deploy.
- Readiness đã kiểm schema: CIS `/health/ready` báo `required_schema` cạnh phiên bản đã áp, và Booking
  `/booking/health/ready` kiểm migration bắt buộc. Sau này (U-50): dừng sớm ngay lúc khởi động.

### 5.5 Terraform

- Ghim phiên bản Terraform và provider, commit file lock; phiên bản engine (PostgreSQL 15, ElastiCache) được ghim
  trong code.
- **Chỉ apply từ `main` qua workflow Terraform Apply.** Trust OIDC của các role deploy và apply chỉ chấp nhận
  `refs/heads/main` (AA-866). Không bao giờ apply từ worktree hay nhánh trước khi merge (từng làm `main` tụt sau hạ
  tầng thật một lần; xem [`lessons.md`](../skill/aa-lessons/lessons.md)).
- Mỗi PR nêu cái gì đổi, chi phí hằng tháng và cách rollback, kèm plan.
- GitHub environment dùng để apply Dev vẫn tên là `prod`. Đổi tên thuộc ADR 0012 (AA-880, D-16, C7.2d); không đổi
  bây giờ.
- Các file `.bak` và `.tfplan` lạc trong Infra đã được xoá (Infra #211, AA-890). Cần xác nhận versioning trên bucket
  state Terraform (chưa kiểm ở S243). Luồng Terraform đầy đủ (comment plan, apply gắn với plan, kiểm drift) là U-42,
  kích hoạt trước prod hoặc khi có sự cố drift tiếp theo.
- Rollback: [runbook rollback Terraform](ops/runbooks/rollback-terraform.md).

### 5.6 Phiên bản API

- API tenant của CIS đã có số phiên bản chính trong URL (`/v1/...`). CIS `/admin/*` và Booking `/booking/*` chưa có.
- Trong một phiên bản chính chỉ có thay đổi bổ sung (field mới, endpoint mới). Xoá hay đổi tên field, đổi kiểu hay đổi
  nghĩa = một phiên bản chính mới hoặc một expand/contract.
- **Bây giờ (AA-899, U-44 kéo lên sớm, 0 USD):** CI export `openapi.json` cho CIS và Booking và chạy oasdiff so với
  `main`; thay đổi phá vỡ sẽ fail trừ khi được gắn nhãn. Việc này cần `response_model` trên các route public.
- **Trước khi có prefix `/booking/v1`:** ADR 0013 về quy ước HTTP ở repo gốc (nó chạm Booking, frontend của Booking và
  TripPlanner, DM-11.1), trích Phần A CON-3 tới CON-5 (N-11).
- Deprecation: thông báo, rồi header `Deprecation` (RFC 9745) và `Sunset` (RFC 8594) cùng một mục CHANGELOG
  "Deprecated", rồi xoá sau thời hạn.
- Event giữa các app theo [contracts](contracts/README.md): bổ sung = minor, phá vỡ = major mới chạy song song ít nhất
  30 ngày.

### 5.7 Prompt và model LLM

- **Model** được ghim theo ID chính xác trong `shared.llm_model_catalog`; route nằm trong `shared.llm_role_config`
  (có audit, với shadow run trong `shared.llm_shadow_log`). ADR của app trong CIS bao phủ catalog và routing.
- **Mọi lần gọi tốn tiền đều đi qua gateway** và vào `shared.llm_call_log` (DM-10.4); script chạy tay dùng
  `stage = adhoc_<issue>` và một role trong writer, judge, validate.
- **Phiên bản prompt:** một cột nullable `prompt_version` đi **cùng migration ledger v2 của AA-804** (một lần expand,
  qua D8; N-5). Tới lúc đó, sổ đăng ký prompt (AA-900) ánh xạ id và phiên bản prompt tới file và stage.
- **Eval:** bộ mẫu chuẩn khoảng 100 mẫu xây từ dữ liệu có sẵn là AA-729. Eval chạy **tay hoặc bằng dispatch** (D-23),
  qua `LLMClient` với `stage = adhoc_aa900` và một trần chi tiêu. PR đổi prompt, model hay route ghi lại ID lần chạy
  eval. Không bật trigger eval theo từng PR (N-4: đó sẽ là chi tiêu định kỳ mới).
- **AA-900 sẽ được thu hẹp** (N-4, N-5) về sổ đăng ký prompt, runbook eval và một bảng route sinh tự động, để nó
  không xây bộ mẫu chuẩn (AA-729) hay đụng tới ledger (AA-804). Issue Linear vẫn liệt kê migration `prompt_version`
  và một workflow eval theo PR; phạm vi và Done-when của nó được cập nhật trước khi bắt đầu làm.
- ADR 0009 về nền tảng AI, các cột `app` và `is_shadow` của ledger và AI Use Register là AA-804 (U-34).

### 5.8 Phiên bản tài liệu

- Tài liệu trong một repo đi theo tag của repo đó: tài liệu ở `v0.4.0` là tài liệu của `v0.4.0`. Không có cơ chế
  riêng.
- Tài liệu repo gốc không có bản phát hành; lịch sử PR là phiên bản của chúng. Các trang mà nơi khác phụ thuộc vào có
  bảng phiên bản riêng: [data standards](architecture/data-standards/README.md#changing-this-standard), contract
  (`vN.M`), `owners.yaml`.
- Không có site tài liệu có phiên bản cho tới khi người dùng bên ngoài chạy cùng lúc hai phiên bản API chính.

---

## 6. Phát hành và thay đổi tính năng

### 6.1 Môi trường

| Môi trường | Mục đích | Hiện nay | Luật |
|---|---|---|---|
| Local | Phát triển, unit test | Có | — |
| PR preview (Vercel) | Xem thay đổi frontend trước khi merge | Có; Playwright UI smoke trên preview của CIS (ba lần chạy `ui-smoke.yml` gần nhất bị bỏ qua: sửa ở AA-879) | Vercel Hobby tới tenant trả tiền đầu tiên (D-18) |
| **Dev** (acc2) | Tích hợp, được phép hỏng, demo | Có | **Chỉ dữ liệu test** (D-01: số đếm chính xác ngày 17/10/2026; Phần C C7.1a cấm PII prod trên Dev). Không có thời gian ân hạn hay theo dõi theo mốc: tạo bằng chứng ngay |
| Staging | — | Không | Không có kế hoạch. Khi có prod, Dev đóng vai pre-prod; PR preview lo phần review UI |
| **Prod** | Người dùng thật | Không | Một instance RDS và các service riêng **trên acc2** (ADR 0001, Phần C C7.2a, D-17); nghiên cứu gộp tài khoản AA-864 làm đầu vào cho ADR 0012. Bố cục, cổng và cách đặt tên trong ADR 0012 khi có ngày go-live (D-16, AA-880, U-40). Mục tiêu prod: DM-9.6, C7.2 |

**Build một lần, deploy nhiều nơi:** cùng một digest image đi từ Dev tới prod; chỉ cấu hình và secret khác nhau.

### 6.2 Deploy không phải là phát hành: feature flag

- *Deploy* = code chạy trong một môi trường. *Phát hành* = người dùng thấy tính năng. Một cờ tách hai việc đó: merge và
  deploy "tối", bật cho một tenant, rồi cho tất cả; khi có chuyện, tắt cờ thay vì rollback.
- **Sổ đăng ký:** [`ops/feature-flags.md`](ops/feature-flags.md) (OPS-06), là một tài liệu, không phải một bảng:
  DM-1.5 giữ `shared` cho phần lõi, nên không có `shared.feature_flag`. Nếu một app cần bảng cờ, nó nằm trong schema
  riêng của app đó; cờ dùng chung cho nhiều app cần một ADR.
- Loại: `release` (tạm thời, có `remove_by` và một issue để gỡ), `ops` (công tắc ngắt khẩn, vĩnh viễn), `security`
  (không bao giờ gỡ theo ngày).
- **Cờ tenant pool là một biện pháp bảo mật** (Phần C C2.3g, DM-8.4, D-12): cờ không đọc được hoặc không có nghĩa là
  tenant pool; chỉ một giá trị `"false"` rõ ràng mới chuyển một route sang admin pool; công tắc khẩn cấp nằm ở
  [break-glass](ops/runbooks/break-glass.md). Chúng không có `remove_by`.
- Thứ tự cho một thay đổi phá vỡ xuyên app: **database trước, bên sản xuất tiếp theo, bên tiêu thụ sau cùng, xoá thứ
  cũ ở cuối cùng**:

  | Bước | Repo | Hành động |
  |---|---|---|
  | 1 | Chủ schema | Migration expand (PR chỉ có migration, D8) |
  | 2 | Gốc | Phiên bản contract minor (field bổ sung) |
  | 3 | Bên sản xuất | Ghi và phục vụ cả cũ lẫn mới; backfill qua một job |
  | 4 | Bên tiêu thụ | Đọc field mới sau một cờ |
  | 5 | — | Bật cờ cho một tenant, kiểm, rồi cho tất cả |
  | 6 | Bên sản xuất | Đánh dấu field cũ là deprecated (CHANGELOG, header cho REST) |
  | 7 | Chủ schema + bên sản xuất | Sau thời hạn: migration contract và một contract major mới nếu có field bị xoá |

### 6.3 Rollout và rollback

Rollback trước, điều tra sau. Chỉ roll forward khi rollback không an toàn (ví dụ sau một migration không đảo ngược
được).

| Thành phần | Rollout | Rollback |
|---|---|---|
| CIS api và worker (ECS) | Rolling, circuit breaker, cổng deploy theo wave đang mở và các job kind chặn deploy (AA-993 G5) | [Rollback CIS](ops/runbooks/rollback-cis.md) (task definition trước, api và worker cùng SHA, rồi revert trên `main`) |
| Booking (ECS) | Rolling, circuit breaker, job guard, smoke SHA | [Rollback Booking](ops/runbooks/rollback-booking.md) |
| Frontend (Vercel) | Deployment do CI tạo khi `frontend/**` đổi | [Rollback Vercel](ops/runbooks/rollback-vercel.md) (rollback tức thì, hoặc deploy lại commit cũ hơn) |
| Lambda TripPlanner | Deploy lọc theo đường dẫn | [Rollback Lambda TP](ops/runbooks/rollback-tp-lambda.md); `needs: ci` + smoke là AA-879, alias `live` là AA-703 (U-54) |
| Database | Chỉ tiến | Không rollback schema; roll forward; PITR là phương án cuối ([khôi phục PITR](ops/runbooks/restore-rds-pitr.md)) |
| Terraform | Plan trong PR, apply từ `main` | [Rollback Terraform](ops/runbooks/rollback-terraform.md) |

Không dùng canary, blue/green và CodeDeploy ([§9.3](#93-không-làm-bây-giờ)).

### 6.4 Definition of Ready và Done

- **Ready:** [mẫu DoR](templates/definition-of-ready.md) (vấn đề, mục tiêu, phạm vi, nghiệm thu, cách kiểm, loại rủi
  ro, phụ thuộc, ảnh hưởng tài liệu) theo định dạng issue của nhà trong
  [`aa-linear-issue`](../skill/aa-linear-issue/SKILL.md). Hỏi tech lead trước khi tạo issue; mọi issue có một
  project; tối đa 100 issue chưa lưu trữ mỗi project.
- **Done:** [`aa-ship`](../skill/aa-ship/SKILL.md): đã merge, CI xanh, rollout deploy COMPLETED, api và worker cùng
  SHA, kiểm endpoint live (200 và đúng hình dạng), kiểm UI khi liên quan, plan Terraform đã review, và một comment
  "Verified live" kèm bằng chứng. Đặt bằng tay, không bao giờ bằng từ khoá trong commit.
- Phần tài liệu của Done: checklist tài liệu trong PR đã tick; một `feat` hay `fix` người dùng thấy được có tiêu đề có
  nghĩa (nó thành dòng CHANGELOG); thay đổi LLM ghi ID lần chạy eval; tài nguyên AWS mới nêu chi phí hằng tháng.

### 6.5 Quyền merge theo giai đoạn

Luật là **DM-11.5** trong [data standards Phần B §11](architecture/data-standards/02-data-management.md#11-change-management)
(v1.1, S241 D-13, duyệt ở S243 N-1), được phản chiếu trong [`.claude/CLAUDE.md`](../.claude/CLAUDE.md) và
[`session-workflow.md`](../.kiro/steering/session-workflow.md). Gói trong một dòng: **trong giai đoạn dev, agent điều
phối tự merge PR của mình sau khi CI xanh, các loại rủi ro thì sau một lần agent review; từ môi trường prod đầu tiên
hoặc tenant trả tiền đầu tiên, tech lead duyệt các PR Terraform/IAM, migration, auth/bảo mật và xoá dữ liệu trước
khi merge.** Subagent không bao giờ merge (hook). Bảng "Who approves what" trong cùng phần đó nói ai quyết từng loại
thay đổi dữ liệu.

Điều sẽ làm cổng prod thành thật về sau: một danh tính agent riêng (GitHub App `aa-agent` và `aa-ci-bot`,
[ADR 0011](adr/0011-github-app-identity-and-merge-rights.md), AA-901), CODEOWNERS trên các đường dẫn rủi ro (có ở cả
năm repo từ AA-901, chưa ép trong giai đoạn dev) và bật code-owner review khi tới điều kiện prod (U-25). Không mua
GitHub Team (D-14, [ADR 0014](adr/0014-repo-visibility-and-github-plan.md)); các repo private dựa vào trust OIDC chỉ
cho `main` và các job guard, và ADR 0014 liệt kê lựa chọn cần quyết cho chúng khi tới điều kiện prod.

---

## 7. Vận hành

Trang bắt đầu: [mục lục vận hành](ops/README.md) (OPS-01). Hướng dẫn hằng ngày: [DevOps guide](guides/devops.md).

### 7.1 Quan sát

| Tín hiệu | Hiện nay | Tiếp theo |
|---|---|---|
| Log | CloudWatch; **log bảo mật và audit 365 ngày, log ứng dụng 30 ngày** (D-09, AA-872; bảng lưu giữ DM-7) | Log JSON chỉ có request id, tenant id và job id, không PII (AA-871, U-30) |
| Metric và alarm | Alarm CloudWatch cho CIS 5xx và độ trễ p95, ECS, Booking, Lambda TripPlanner, RDS, job, SES, Cognito; e-mail khi **ALARM và OK** (D-20); link runbook trong mô tả alarm và một [danh mục alarm](generated/alarms.md) sinh tự động (AA-893) | Kênh thứ hai và SLO ở prod (AA-880, U-49) |
| Lỗi | Sentry cho backend và frontend CIS (AA-870), không gửi PII | Sentry cho Booking và TripPlanner (AA-871) |
| Uptime | Một monitor Sentry miễn phí trên CIS `/health`; Booking dựa vào alarm AWS (AA-870); Lambda ops-probe hằng ngày | — |
| Trace | Không có | Chỉ khi một job chậm mà không giải thích được (D-21, AA-842) |
| LLM | `shared.llm_call_log` (chi phí, tài khoản, fallback, job id) | `prompt_version` cùng AA-804 |
| Cái gì chạy ở đâu | SHA `/health` theo từng service; trang Apps trong admin (AA-884, CIS #838) và trang tổng quan vận hành cho chủ doanh nghiệp (AA-858, CIS #840), cả hai đã deploy trong CIS `dba9b72` | Xong cả hai sau khi kiểm live theo `aa-ship` |

Đặt alarm theo triệu chứng người dùng cảm nhận (5xx, health lỗi, hàng đợi kẹt, vượt ngân sách), không theo nguyên
nhân. Nhớ RED cho service (rate, errors, duration) và USE cho tài nguyên (utilization, saturation, errors). SLO chỉ có
nghĩa khi có traffic thật (prod).

### 7.2 Từ alarm tới runbook

- Mọi alarm trỏ tới một runbook hoặc playbook (AA-893): link là hậu tố `Runbook:` của mô tả alarm, và
  [danh mục alarm](generated/alarms.md) sinh tự động liệt kê mọi alarm kèm runbook. Với alarm không có link, dùng bảng
  triệu chứng trong [mục lục vận hành](ops/README.md#something-is-wrong).
- Playbook: [5xx tăng vọt](ops/playbooks/5xx-spike.md), [hàng đợi kẹt](ops/playbooks/queue-stuck.md),
  [chi phí LLM tăng vọt](ops/playbooks/llm-cost-spike.md), [đăng nhập Cognito](ops/playbooks/cognito-login.md). Trường
  hợp SES bounce là một runbook: [SES bounce](ops/runbooks/ses-bounce.md).
- Công tắc ngắt khẩn theo job kind: [sổ đăng ký job kind](ops/job-kinds.md).
- Runbook theo [mẫu runbook](templates/runbook.md) và luật "đã test" trong [STYLE](STYLE.md#runbooks-and-tested):
  `active` chỉ sau một lần chạy thật (Dev, diễn tập, sự cố, hoặc DRY RUN cho bước phá huỷ); nếu không thì `draft` với
  banner UNTESTED.

### 7.3 Sự cố và postmortem (một nơi)

- Quy trình: [xử lý sự cố](ops/incident-response.md) (SEV1-3, 15 phút đầu, báo cho ai, thông báo tenant). Bốn bước:
  phát hiện, giảm thiểu (rollback hoặc tắt cờ), sửa, review.
- **Một bản ghi cho mỗi sự cố:** bản ghi SEV1-2 bắt đầu trong issue Linear trong vòng 2 ngày làm việc; postmortem được
  viết từ [mẫu postmortem](templates/postmortem.md) và giữ trong thư mục duy nhất mà dòng danh mục OPS-04 nêu tên (thư
  mục được tạo cùng postmortem đầu tiên, AA-892). Điều này thay thư mục sự cố riêng từng được đề xuất ở S241; không có
  nơi thứ hai.
- Không đổ lỗi: dòng thời gian, nguyên nhân gốc, điều gì tốt và chưa tốt, việc cần làm thành issue Linear, và một dòng
  trong [`lessons.md`](../skill/aa-lessons/lessons.md). Bài học mà test kiểm được thì thành CI guard và dòng đó được
  xoá.
- Chủ doanh nghiệp nhận bản tóm tắt tiếng Việt ba câu.

### 7.4 Backup và khôi phục thảm hoạ

- Dev: RDS PITR 7 ngày, chống xoá, snapshot cuối, snapshot tự động trước migration phá huỷ, snapshot thủ công hết hạn
  sau 30 ngày trừ khi cố ý giữ (AA-869).
- **Kết quả diễn tập:** một lần diễn tập PITR đầy đủ đạt ngày 17/10/2026, khoảng 22 phút so với mục tiêu Dev < 1 giờ
  (D-10; bằng chứng [`audits/2026-10-17-S241-restore-drill/`](audits/2026-10-17-S241-restore-drill/)).
- **Nhịp (DM-9.3 + S243 K-04):** trên Dev, diễn tập lại khi quy trình khôi phục hoặc rollback đổi (K-04) và một lần
  trước prod; theo quý từ khi có prod (DM-9.3). `last_tested` cũ trên Dev là cảnh báo, không phải mệnh lệnh (N-2 giữ
  mặc định).
- Runbook: [khôi phục PITR](ops/runbooks/restore-rds-pitr.md), [khôi phục một schema](ops/runbooks/restore-schema.md)
  (nháp); [mục lục diễn tập](ops/drills/README.md). DSN đặt sau một CNAME private, buổi tập khôi phục một schema và
  việc xoá các bản dump cũ trên laptop là AA-829 (U-20); Done-when của nó không đổi.
- **Bằng chứng nằm trong `docs/audits/<date>-S<nnn>-<slug>/`** (C7.2b, DM-8.10, C8a; N-10 giữ mặc định). Mục lục diễn
  tập và bảo mật chỉ dẫn link tới đó.
- Mục tiêu prod (Multi-AZ, PITR 14 ngày, bản sao backup khác vùng, RPO/RTO): DM-9.6 và C7.2b, xác nhận trong ADR 0012.
- Một bản backup chưa từng được khôi phục thì không phải là backup.

### 7.5 Secret

- **Sổ đăng ký:** [sổ đăng ký secret](security/secrets-register.md), YAML trước
  ([`secrets-register.yaml`](security/secrets-register.yaml)), chỉ tên và metadata, có kiểm drift (AA-878, U-26). Sổ
  đăng ký env-config (AA-894) chỉ liệt kê tên mà mỗi service tham chiếu và dẫn link về đây.
- **Khi nào xoay** (D-02, D-03, DM-8.9): khi nghi bị lộ, khi go-live, và sau mỗi lần dùng break-glass. **Không có chu
  kỳ 90 ngày trên Dev.** Lần kiểm hằng tháng là kiểm drift của sổ đăng ký, không phải xoay. Quy trình theo từng loại:
  [runbook xoay secret](ops/runbooks/secret-rotation.md).
- Token GitHub và mật khẩu RDS master bị in ra trong một transcript local ở S240 sẽ được xoay khi go-live (D-02, D-03);
  chúng nằm trong checklist prod (AA-880).
- Secret lúc chạy nằm trong Secrets Manager; CI nhận credential AWS ngắn hạn qua OIDC; không có key tĩnh trong CI.
- Trước mọi lần ghi secret hay tài nguyên: `aws sts get-caller-identity --profile aa365-admin` và xác nhận acc2
  (DM-8.7).
- Tên biến môi trường có dấu gạch dưới do tech lead tự tay sửa trong VSCode hoặc console; agent mô tả thay đổi và
  không bao giờ tự sinh ra nó.
- Secret RDS master được quản lý tự động sẽ làm sau khi tách role X1 (D-04, U-41).

### 7.6 Quyền truy cập

- **Người chỉ vào database qua ECS exec trung gian S3** trên SSM, không bao giờ SSH hay endpoint public (DM-8.8, D-07);
  phiên exec được ghi log và giữ 365 ngày; log kết nối đã bật, pgaudit chờ tới prod (D-08). Cách làm:
  [runbook ECS exec](ops/runbooks/ecs-exec-s3-mediated.md), [vận hành database](ops/database-operations.md).
- **Agent** chạy với profile `aa365-admin` (D-15; N-8 giữ nguyên). Việc thu hẹp danh sách quyền đã commit của agent
  (ask/deny, allowlist secret e2e) được gộp vào AA-878 (N-12). Role agent tối thiểu quyền và bỏ key tĩnh trên laptop
  là mục theo điều kiện (U-53), không phải việc hiện tại.
- **Review quyền truy cập theo quý** (DM-8.10): role, grant, các IAM role đọc từng secret DB, người dùng Cognito
  workforce, collaborator và app GitHub, quyền đã commit của agent, và connector MCP; chạy trong phiên đầu tiên của mỗi
  quý; ghi vào `docs/audits/<date>-S<nnn>-access-review/`; mục lục ở
  [tài liệu bảo mật](security/README.md#access-reviews-sec-05). Lần đầu nằm trong AA-878; nhịp là AA-838 (U-38).
- Đăng nhập nhân sự: Cognito workforce pool với mã e-mail (ADR 0006, 0006a); chỉ owner được đổi quyền của người khác
  (Q2). Đăng nhập mật khẩu cũ đã tắt từ lần chuyển đổi AA-816 ngày 2026-10-22
  ([cờ đăng nhập cũ](ops/runbooks/legacy-login-flag.md)).
- Bản đồ tài khoản và quyền truy cập theo từng người: [onboarding](onboarding.md).

### 7.7 Break-glass

[Runbook break-glass](ops/runbooks/break-glass.md) (OPS-10): tài khoản Cognito `breakglass` với TOTP, RDS master
(DM-8.9: break-glass khi runtime CIS đã có role riêng), và công tắc khẩn cấp của tenant pool. Override cổng deploy có
runbook riêng ([override cổng deploy](ops/runbooks/deploy-gate-override.md)) và do tech lead quyết, kèm lý do viết ra.
Mỗi lần dùng được ghi tên trong log phiên và trên issue Linear, và sau đó phải xoay secret ([§7.5](#75-secret)).

### 7.8 Nền tảng bảo mật và lỗ hổng

- [Nền tảng bảo mật](security/baseline.md) (SEC-01, AA-895): mọi biện pháp kiểm soát kèm trạng thái live, bằng chứng
  và issue còn mở (AA-873, AA-874, AA-875, AA-876, AA-879).
- [Quản lý lỗ hổng](security/vulnerability-management.md) (SEC-03): thời hạn sửa, danh sách ngoại lệ có ngày hết hạn,
  phân loại hằng tháng; Dependabot cho Booking và TripPlanner là một phần của AA-895.

---

## 8. Chi phí (FinOps)

### 8.1 Luật, theo tham chiếu

Luật chi tiêu là **DM-10.1 tới DM-10.7** trong
[data standards Phần B §10](architecture/data-standards/02-data-management.md#10-cost-ownership): tag `App`, ngân sách
theo app, RDS do Infra trả, mọi lần gọi tốn tiền đi qua seam và ledger của nó, ngân sách được kiểm trong database, các
đợt chạy tốn tiền thử khoảng 3 rồi tối đa khoảng 50 tour, và tech lead duyệt mọi thay đổi chi tiêu. Bổ sung theo quyết
định: **báo chi phí hằng tháng trước khi áp bất kỳ dịch vụ hay tài nguyên AWS mới nào và duyệt từng mục** (D-19). Quy
trình quanh các luật là [trang FinOps](ops/finops.md) (FIN-01).

### 8.2 Cái gì đã có

| Rào chắn | Trạng thái |
|---|---|
| Tag `App` | Đã kích hoạt làm tag phân bổ chi phí từ 15/10/2026 |
| Tag `Environment` | Đã có trên mọi tài nguyên Terraform (`default_tags`). acc2 là tài khoản thành viên, nên tech lead nhờ tài khoản trả tiền kích hoạt; 0 USD. Không thêm key `Env` mới (DM-10.1) |
| Ngân sách tài khoản 300 USD/tháng + ngân sách theo app | Live (Infra `observability.tf`; nâng từ 250 kèm cảnh báo dự báo, Infra #460) |
| Cost Anomaly Detection | Miễn phí; live (Infra #213, `cost_anomaly.tf`): cảnh báo tức thì tới e-mail SNS sẵn có cho các bất thường từ 5 USD. AA-896 vẫn mở cho phần còn lại (trang FinOps, công cụ báo cáo hằng tháng). Monitor theo tag chỉ có ở tài khoản quản lý; ngân sách theo app bù phần đó |
| Trần LLM và API bên ngoài | `shared.spend_budget` (DM-10.5) |
| Chi phí theo app | Trang và API chi phí trong admin (AA-884, CIS #838) và trang tổng quan cho chủ doanh nghiệp trên cùng module (AA-858, CIS #840): đã deploy trong CIS `dba9b72`; Xong sau khi kiểm live theo `aa-ship` |
| Ngân sách và cảnh báo bất thường trên acc3 (vệ tinh LLM) | Live (`accounts/acc3-bedrock` `cost_guard.tf`, `cost_anomaly_immediate.tf`). acc1 đã rời hệ sinh thái (AA-998) |

### 8.3 Review hằng tháng

- **Một báo cáo hằng tháng bao gồm chi phí và dung lượng:** FIN-02 = OPS-08 = review dung lượng C8 (C8a, C8b). Claude
  Code soạn từ [mẫu báo cáo chi phí](templates/cost-report.md) cùng [hướng dẫn](ops/cost/README.md); tech lead duyệt;
  lưu ở `docs/audits/<date>-S<nnn>-capacity-review/` kèm một root PR.
- Dữ liệu lấy từ những gì CIS đã lưu: `shared.cost_explorer_snapshot` (và snapshot theo App) cộng
  `shared.llm_call_log` (DM-10.4); script là [`monthly_cost_report.py`](../tools/finops/monthly_cost_report.py).
  **Không viết script mới gọi Cost Explorer**; mở rộng client của CIS nếu cần một cách gom nhóm mới.
- Nội dung: tổng theo `App` so với tháng trước, năm dịch vụ đứng đầu, mọi thay đổi trên 20 % kèm lý do, LLM theo stage
  và tài khoản, chi phí đơn vị, trạng thái ngân sách, việc cần làm, và một bản tóm tắt tiếng Việt năm dòng cho chủ
  doanh nghiệp.
- Chi phí đơn vị: USD mỗi tour được xuất bản, USD LLM mỗi tour được xuất bản, USD mỗi trip plan, USD mỗi booking.
- **Báo cáo đầu tiên:** phiên đầu tiên vào hoặc sau ngày 01/11/2026, cho tháng 10, so sánh tháng 8, 9 và 10 theo app
  và dịch vụ.
- Khi một cảnh báo bật: [FinOps, "When an alert fires"](ops/finops.md#when-an-alert-fires) và
  [playbook chi phí LLM tăng vọt](ops/playbooks/llm-cost-spike.md).

### 8.4 Chi phí của lộ trình

| Khối | USD/tháng | Ghi chú |
|---|---|---|
| Tài liệu, CI, runbook, sổ đăng ký, hướng dẫn, release-please, kiểm OpenAPI, phát hiện bất thường | 0 | Phút GitHub Actions nằm trong gói miễn phí |
| Bucket `/admin/docs` (AA-898) | ~0,01 | Nêu trong PR |
| Trước tenant trả tiền đầu tiên (Redis AUTH/TLS, WAF và throttle, ECR, log) | ~2-10 | Mỗi mục được báo giá và duyệt khi tới lượt (D-19) |
| Bảo mật 90 ngày (GuardDuty giới hạn, gia cố CloudTrail, lưu giữ log) | ~4-16 | AA-873 |
| Alarm Cognito + secret break-glass | ~2,4 | Đã duyệt ở S241 ("Cognito $") |
| WAF Cognito trên pool khách hàng | ~7 | Khi mở đăng ký khách hàng (S241); Apple Developer 99 USD/năm cùng đăng nhập khách hàng AA-680 |
| Vercel Pro | ~20 + mức dùng | Chỉ khi có tenant trả tiền đầu tiên (D-18) |
| Prod (U-40) | ~150-300 (ước lượng) | Một con số thống nhất trong ADR 0012; ngân sách tài khoản 300 USD hiện đã gồm Dev |

---

## 9. Lộ trình

### 9.1 Cách dùng lộ trình

- Bảng này là lộ trình nền tảng **duy nhất**. [Backlog sống](backlog/README.md) sắp thứ tự các phiên tiếp theo;
  [§3a](backlog/README.md#3a-platform-roadmap-keys-plat-01) (PLAT-01) của nó liệt kê các mã U-xx theo thứ tự được chọn
  và không chép nội dung.
- Việc sản phẩm (T-series, portal, các đợt Booking, place pipeline) không nằm ở đây.
- Tầm: **Now** (các phiên tới), **Tenant** (trước tenant trả tiền đầu tiên), **Prod** (trước prod đầu tiên, khi có
  ngày go-live), **Trigger** (khi điều kiện kích hoạt xảy ra), **Later** (khi đội hoặc traffic lớn lên).
- Giá trị trạng thái: Done, In progress, Open, Trigger, Not doing (theo quyết định). Bảng được lập ngày 2026-10-19; các
  dòng ghi "(S255)" được cập nhật ngày 2026-10-28 từ các repo. Linear giữ trạng thái hiện hành của từng issue.
- Chi phí: USD phát sinh thêm mỗi tháng; mục 0 USD đứng trước trong mỗi tầm. Người làm: ai làm việc đó; "Tech lead"
  đánh dấu một bước thủ công hoặc một quyết định.
- Mọi issue nêu ở đây đều có trong Linear; issue chưa là một dòng của backlog sống được liệt kê ở mục "later" của
  backlog §3a.

### 9.2 Bảng lộ trình

| # | Hạng mục | Tầm | Trạng thái | Issue | Chi phí | Người làm |
|---|---|---|---|---|---|---|
| U-01 | Trust OIDC cho deploy/apply/migrate giới hạn ở `main` | Now | Done | AA-866 | 0 | Agent |
| U-02 | Admin secret giới hạn trong environment `dev` và được xoay ở 5 nơi | Now | Done | S241 chore | 0 | Agent + tech lead |
| U-05 | Tính năng bảo mật GitHub miễn phí, 2FA cho org, chặn force-push và xoá nhánh | Now | Done (Dependabot cho Booking và TripPlanner nằm trong AA-895) | AA-867 | 0 | Agent |
| U-06 | Kiểm role phía server cho thao tác ghi llm-config, ngân sách, job-runner | Now | Done (so sánh thời gian hằng định trong `api/core/secret_compare.py`, CIS #791) | AA-882 | 0 | Agent |
| U-07 | Sentry cho CIS, alarm API 5xx và p95, monitor uptime | Now | Done | AA-870 | 0 | Agent |
| U-08 | pip-audit chặn, giới hạn deploy đồng thời, job guard đóng khi lỗi | Now | Done | AA-868 | 0 | Agent |
| U-18 | Mỗi bên gọi một security group, ADR 0004b | Now | Done (X1 S10-S14) | AA-852 | 0 | Agent |
| U-21 | ECR CIS bất biến, runbook rollback, trang sự cố, snapshot hết hạn sau 30 ngày | Now | Done | AA-869 | ~1-3 | Agent |
| U-22 | Log phiên ECS exec, `log_connections` | Now | Done (Infra #161) | — | ~1-5 | Agent |
| — | Lưu giữ log 365 ngày cho bảo mật / 30 ngày cho app, e-mail OK | Now | Done | AA-872 | <1-2 | Agent |
| — | Các khu vực console + trang Staff; tách tenant portal | Now | Done | AA-883, AA-885 | 0 | Agent |
| — | Data standards v1.1 (DM-11.5, C2.3g/DM-8.4, các dòng DM-7, C4.2b, DM-11.2, DM-1.2) | Now | Đã duyệt (N-1); merge cùng PR gói tài liệu | AA-889 | 0 | Agent + tech lead |
| AA-887 | Chuẩn tài liệu: danh mục, mẫu, schema, văn phong, thuật ngữ, DoR, sổ tay này (phần tài liệu của U-48) | Now | Trong PR gói tài liệu (Linear: Backlog) | AA-887 | 0 | Agent |
| AA-888 | Docs lint + mục lục ADR ở mọi repo, báo cáo độ mới | Now | In progress | AA-888 | 0 | Agent |
| U-09 | Tài liệu cũ và chỉ dẫn agent bị lệch; `docs/` của CIS được track sau khi quét | Now | In progress | AA-889 | 0 | Agent |
| U-11 | Chỉ squash, xoá nhánh khi merge, dọn nhánh, mẫu PR và lint tiêu đề, dọn `.bak` của Infra, bỏ `/v1/webhooks` khỏi Playground (phần mẫu PR của U-48) | Now | In progress (mẫu PR Infra và dọn `.bak` đã xong, Infra #211) | AA-890 | 0 | Agent + tech lead (cài đặt) |
| AA-892 | Mục lục vận hành, runbook rollback, playbook, sổ đăng ký cờ và job, break-glass, isolation probe | Now | Bản nháp trong PR gói tài liệu (Linear: Backlog); runbook sẽ được chạy trên Dev | AA-892 | 0 | Agent |
| AA-893 | Link runbook cho alarm (bước 1), rồi các bảng inventory, network và IAM sinh tự động (phần runbook của U-49); output Terraform lõi (VPC, RDS, ECS, ALB, SG) trước, để bảng sinh tự động có nguồn | Now | Bảng alarm, inventory, network và IAM sinh tự động đã live (S255) | AA-893 | 0 | Agent |
| AA-895 | Nền tảng bảo mật, chính sách lỗ hổng, Dependabot cho Booking và TripPlanner | Now | In progress | AA-895 | 0 | Agent |
| AA-896 | Trang FinOps, Cost Anomaly Detection, công cụ báo cáo hằng tháng | Now | In progress (phát hiện bất thường đã live, Infra #213) | AA-896 | 0 | Agent |
| AA-897 | Onboarding, mục lục agent, hướng dẫn vai trò (tiếng Việt là bản dịch `.vi.md` từ S255; trước đó song ngữ theo N-7), playbook thêm app mới | Now | Bản nháp trong PR gói tài liệu (Linear: Backlog) | AA-897 | 0 | Agent |
| U-26 | Sổ đăng ký secret, dọn secret mồ côi, tài khoản E2E chỉ đọc, lần review quyền truy cập đầu tiên | Now | In progress | AA-878 | 0 | Agent + tech lead |
| U-04 | Thu hẹp quyền agent (ask/deny đã commit, allowlist secret e2e), gộp theo N-12 | Now | Open | AA-878 | 0 | Agent + tech lead |
| AA-891 | release-please, CHANGELOG, các tag đầu tiên (phần nhẹ của U-47); SHA trong `/health` của CIS đã ship cùng AA-884 | Now | Open (cần token của AA-901) | AA-891 | 0 | Agent |
| U-25 | Danh tính GitHub App cho agent và release-please; ADR gốc [0011](adr/0011-github-app-identity-and-merge-rights.md) (danh tính, quyền merge) và [0014](adr/0014-repo-visibility-and-github-plan.md) (độ hiển thị, gói GitHub), cả hai Proposed (S247); file CODEOWNERS ở cả năm repo; code-owner review cho prod | Now (App) / Prod (cổng) | Open | AA-901 | 0 | Agent + tech lead |
| U-44 | Export OpenAPI + oasdiff cho CIS và Booking (kéo lên sớm); ADR 0013 trước `/booking/v1` | Now | Open | AA-899 | 0 | Agent |
| AA-894 | Sổ đăng ký env-config sinh tự động (chỉ tên) + ERD | Now | Live (S255): [env-config](generated/env-config.md), [ERD](architecture/erd/README.md) | AA-894 | 0 | Agent |
| — | Trang chi phí theo app và trang tổng quan vận hành cho chủ doanh nghiệp | Now | Đã deploy (CIS #838, #840; SHA live `dba9b72`); Xong sau khi kiểm theo `aa-ship` | AA-884, AA-858 | tối đa ~0,30 | Agent |
| — | Tag phân bổ chi phí `Environment` do tài khoản trả tiền kích hoạt | Now | Open | — | 0 | Tech lead |
| — | Tech lead tự tay sửa `~/.claude/CLAUDE.md`: ngoại lệ `Refs` cho PR phát hành, luật merge theo giai đoạn (N-6); bỏ `handoff.md`, nhắc dừng ECS, số task-def/CI trong CLAUDE.md của repo, cách đánh số `ADR-2026-0xx` (S243 N4) | Now | Open | — | 0 | Tech lead |
| U-10 | Kiểm chỉ đọc: (a) PII thật trên Dev (không có, D-01) và (b) dữ liệu thương mại trong repo gốc (repo gốc chuyển private, D-25) đã xong; (c) trust của tài khoản quản lý và chính sách bằng văn bản từ tài khoản trả tiền còn mở | Now | (a)(b) Done, (c) Open | — | 0 | Tech lead |
| — | Review chi phí và dung lượng hằng tháng đầu tiên (tháng 10) | Now (≥ 01/11) | Open | AA-896, AA-838 | 0 | Agent + tech lead |
| U-12 | Tenant pool đóng khi lỗi (toàn cục từ D-12) và đợt 3-4 | Tenant | In progress | AA-859 | 0 | Agent |
| U-16 | Isolation probe theo lịch và sau khi apply; chạy theo PR khi RLS đổi | Tenant | Probe theo lịch + sau apply đã live (Infra `db-isolation-probe.yml`, X1 S2); phần chạy theo PR khi RLS đổi còn mở | AA-852 (probe); phần theo PR cùng AA-848 | 0 | Agent |
| U-20 | Khôi phục: diễn tập PITR đã xong; DSN qua CNAME private, tập khôi phục một schema, dump trên laptop | Tenant | Open (Linear: Backlog); diễn tập PITR xong ở S241 (D-10) | AA-829 | <1 mỗi lần diễn tập | Agent + tech lead |
| U-14 | Client HTTP gọi ra ngoài an toàn với SSRF | Tenant | Open | AA-875 | 0 | Agent |
| U-15 | CI guard catalog X2 (RLS, PUBLIC, FK xuyên chủ, grant) | Tenant | Open | AA-848 | 0 | Agent |
| U-24 | Tag `pii:` trên các cột Booking và TripPlanner | Tenant | Open | AA-877 | 0 | Agent |
| U-60 | Bảng job TripPlanner + che PII trong outbox | Tenant | Open | AA-861 | ~0 | Agent |
| U-13 | Redis AUTH/TLS/mã hoá lưu trữ + alarm khi đọc cờ lỗi | Tenant | Open (báo giá trước) | AA-874 | ~0 | Agent + tech lead |
| U-19 | Lớp biên API: giới hạn tần suất đăng nhập, WAF và throttle, cổng docs, CORS, header | Tenant | Open | AA-876 | ~0-2 | Agent + tech lead |
| U-23 | Đề xuất bộ pháp lý cho chủ doanh nghiệp, `/privacy`, `/terms`, điều khoản AI | Tenant | Open | AA-886, AA-820 | 0 | Agent + chủ doanh nghiệp |
| U-27 | RBAC nhân sự + chuyển đổi Cognito Phase 1 | Tenant | In progress (S255): CIS đã chuyển (tắt đăng nhập cũ, AA-816 S2); Booking vẫn nhận bridge token của CIS | AA-816, AA-703 | 0 | Agent + tech lead |
| U-33 | Chuỗi tách role X1 (owner role, `db_migrator`, role runtime CIS) | Tenant | Live tới S21 (S255): `cis_owner` sở hữu các schema CIS từ CIS 245, `cis_app` là login runtime của CIS | AA-852, AA-860 | 0 | Agent |
| AA-898 | Trang đọc `/admin/docs` (allowlist, trang bảo mật chỉ owner xem) | Tenant | Live (S255) | AA-898 | ~0,01 | Agent |
| U-28 | Ngang bằng cổng CI, deploy Lambda TripPlanner sau CI, replay migration TripPlanner | Tenant | Open | AA-879; replay migration AA-849 | 0 | Agent |
| U-61 | `idle_session_timeout` của TripPlanner + kiểm ngân sách kết nối trong CI, gộp theo N-12 | Tenant | Open | AA-879 | 0 | Agent |
| U-29 | Bộ mẫu chuẩn khoảng 100 mẫu, eval chạy tay hoặc dispatch (D-23) | Tenant | Open | AA-729 | ≤ 1 mỗi lần chạy | Agent |
| AA-900 | Sổ đăng ký prompt, runbook eval, bảng route sinh tự động (sẽ thu hẹp theo N-4, N-5; phạm vi trên Linear chưa cập nhật) | Tenant | Open | AA-900 | 0 | Agent |
| U-30 | Log JSON có request id; Sentry cho Booking và TripPlanner | Tenant | Open | AA-871 | 0 | Agent |
| U-31 | GuardDuty (giới hạn), Access Analyzer, S3 BPA, gia cố CloudTrail | Tenant | Open (báo giá trước) | AA-873 | ~4-16 | Agent + tech lead |
| U-34 | ADR 0009 về nền tảng AI, ledger v2 có `prompt_version`, AI Use Register | Tenant | Open | AA-804 | 0 | Agent + tech lead |
| U-35 | Guard hash contract + công cụ cho playbook app mới | Tenant | Open | AA-826 | 0 | Agent |
| U-36 | TripPlanner thôi đọc bảng CIS | Tenant | Done (S255): CIS 254 và 270 thu hồi grant, tp-018 xoá các bảng cũ | AA-712 | 0 | Agent |
| U-37 | Dead Table Registry + lưu trữ bảng job cũ | Tenant | In progress (S255): đợt 1 được cách ly bởi CIS 294 | AA-850 | 0 | Agent |
| U-38 | Các lần review định kỳ trong nghi thức phiên (dung lượng hằng tháng, quyền truy cập hằng quý); kiểm `pg_stat_statements` hằng tuần (C4.3); review quyền agent hằng quý | Tenant | Open | AA-838 | 0 | Agent + tech lead |
| U-39 | `shared.countries` và view quốc gia trong catalog | Tenant | Live (S255): CIS 279 | AA-851 | 0 | Agent |
| U-32 | Script xoá dữ liệu và export DSAR | Tenant | Chưa làm (D-11): runbook thủ công khi có yêu cầu | AA-839 | 0 | Agent |
| — | Runbook yêu cầu của chủ thể dữ liệu làm tay (xoá/export khi có yêu cầu, DRY RUN), danh mục OPS-09 | Tenant | Open | AA-839 (phần runbook, không chờ Phase 4) | 0 | Agent |
| — | Chưa đánh số ở S241 (tech lead có thể gộp vào): A14 giới hạn kích thước body + `extra='forbid'` → U-19; E13 S3 gateway endpoint miễn phí trên Dev → U-40 cho phần prod | Tenant | Open (chưa quyết) | AA-876 | 0 | Agent + tech lead |
| U-40 | Bản thiết kế prod, ADR 0012 (tài khoản, bố cục, cổng, đổi tên environment), SLO, kênh cảnh báo thứ hai, ngân sách prod, PDF break-glass, checklist sẵn sàng | Prod | Trigger: ngày go-live | AA-880 | ~150-300 | Agent + tech lead |
| U-03 | Xoay token GitHub bị lộ | Prod | Chưa làm (D-02): khi go-live | AA-880 | 0 | Tech lead |
| U-17 | Xoay mật khẩu RDS master | Prod | Chưa làm (D-03): khi go-live | AA-880 | 0 | Tech lead |
| U-41 | Secret master được quản lý tự động | Prod | Trigger: X1 xong (D-04) | — | ~0,4 | Agent + tech lead |
| U-42 | Luồng Terraform: comment plan, apply gắn với plan, kiểm drift | Prod | Trigger: trước prod hoặc lần drift tiếp theo | AA-846 (plan sạch, ghim phiên bản, guard apply); dọn `.bak` đã xong trong AA-890 | 0 | Agent |
| U-43 | Build một lần theo digest, SBOM khi phát hành, provenance, ghim action | Prod | Trigger: prod đầu tiên | — | 0 | Agent |
| U-47 | GitHub Deployments, số liệu DORA (phần còn lại của U-47) | Prod | Trigger: prod đầu tiên | AA-891 | 0 | Agent |
| U-49 | SLO và alarm burn-rate | Prod | Trigger: prod đầu tiên | AA-880 | ~0-3 | Agent |
| U-54 | `rollback.yml`, alias Lambda `live` | Prod | Trigger: prod đầu tiên | AA-703 | 0 | Agent |
| U-51 | ECS exec trở thành break-glass (D-07 B) | Prod | Trigger: prod | — | 0 | Agent + tech lead |
| — | Vercel Pro | Prod | Trigger: tenant trả tiền đầu tiên (D-18) | — | ~20 + mức dùng | Tech lead |
| U-44 (phần còn lại) | ADR 0013 quy ước HTTP, prefix `/booking/v1` | Trigger | Trigger: tenant đầu tiên tích hợp qua API (N-11) | AA-899 | 0 | Agent + tech lead |
| U-45 | API key public | Trigger | Trigger: bán gói API | AA-813 | ~0 | Agent |
| U-46 | Idempotency-Key trên các POST tốn tiền | Trigger | Trigger: bật thanh toán | AA-682 | 0 | Agent |
| U-48 | `.github` của org, workflow tái sử dụng, mẫu issue, SECURITY.md | Trigger | Trigger: người đóng góp thứ hai | — | 0 | Agent |
| U-50 | Bot copy migration, kiểm phiên bản schema bắt buộc | Trigger | Trigger: sự cố "app chạy trước migration" tiếp theo | AA-826 | 0 | Agent |
| U-52 | Pentest bên thứ ba | Trigger | Trigger: hợp đồng doanh nghiệp đầu tiên | — | báo giá một lần | Chủ doanh nghiệp + tech lead |
| U-53 | Không key tĩnh trên laptop, role agent, devcontainer | Trigger | Trigger: mở lại D-15 | — | 0 | Tech lead |
| U-55 | Trailer commit cho AI agent, tracing phương án B | Trigger | Trigger: job chậm không giải thích được (D-21) | AA-842 | 0 | Agent |
| U-56 | Tập nâng cấp phiên bản chính PostgreSQL 15 | Trigger | Trigger: 05/2027 | AA-881 | <1 | Agent |
| U-57 | Phần còn lại của L3 (dữ liệu khách du lịch, các dòng lưu giữ, xoá dữ liệu) | Trigger | Trigger: ADR 0006 Phase 4 / trước prod | AA-839 | 0 | Agent |
| U-58 | CRM cho tenant theo playbook app mới | Trigger | Đã xây (S255): AA-Partner (ADR 0010), schema `crm` tới crm-023 | AA-821 | — | Agent + chủ doanh nghiệp |
| U-59 | Reserved concurrency cho Lambda TripPlanner | Trigger | Trigger: quota Lambda 1000 | — | 0 | Agent |
| — | Sơ đồ kiến trúc C4 L1-L2, trang network, ma trận quyền truy cập | Later | Tạm gác (N-9 giữ nguyên); bảng lấy từ AA-893 | AA-697 | 0 | Agent |
| — | Video UAT cho mọi app | Later | Sau phần việc kỹ thuật, khi tech lead ra hiệu | AA-855 | 0 | Agent + chủ doanh nghiệp |
| — | Số liệu DORA hằng tháng từ GitHub API; dashboard chi phí đơn vị | Later | Open | — | 0 | Agent |
| — | Tự review Well-Architected hằng năm cho từng app (kèm lăng kính Generative AI); NIST SSDF, NIST AI RMF, OWASP LLM Top 10 làm checklist đọc | Later | Open | — | 0 | Tech lead |
| — | Site tài liệu (giai đoạn 3), lint văn phong Vale (cảnh báo), `terraform-docs`, `AGENTS.md` cho các agent khác; tài liệu đối tác (B2B) public thành site riêng; kiểm trang mồ côi; Structurizr C4 | Later | Theo điều kiện kích hoạt ([§4.3](#43-tài-liệu-nằm-ở-đâu)) | — | 0-1 | Agent |
| — | Tracing OpenTelemetry | Later | Trigger: D-21 | AA-842 | 0 | Agent |

Ánh xạ danh sách riêng của guide S243 (để không xây gì hai lần): N1 SHA trong `/health` của CIS → đã ship cùng AA-884;
N2 release-please → AA-891; N3 mẫu PR và lint tiêu đề → AA-890; N4 chỉ dẫn agent bị lệch → AA-889; N5 luật bỏ qua
`docs/` của CIS → AA-889; N6 mục lục vận hành và rollback → AA-892; N7 phát hiện bất thường → AA-896; N8 cài đặt nhánh
→ AA-890; N9 mục lục ADR → AA-888; N10 thuật ngữ và DoR → AA-887; N11 dọn Infra → AA-890. P1 → AA-880; P2 → AA-899; P3
→ AA-900 + AA-729 + AA-804; P4 → AA-871; P5 → AA-879 + AA-703; P6 → AA-879; P7 → AA-878, AA-873, AA-874, AA-876,
AA-880; P8 → AA-901; P9 → AA-829 + AA-880; P10 → AA-893 + AA-880; P11 → AA-871 + AA-884; P12 → kích hoạt tag ở tài
khoản trả tiền, AA-880, AA-891.

### 9.3 Không làm bây giờ

Mỗi mục là có chủ đích, kèm lý do. Mở lại một mục cần một quyết định mới ở [§10](#10-nhật-ký-quyết-định).

| Không làm | Vì sao / cho tới khi |
|---|---|
| Một môi trường staging cố định, nhiều vùng, active-active | Dev + preview + đẩy cùng một image là đủ cho tới khi có prod với khách hàng lớn |
| Một tài khoản AWS riêng cho prod | ADR 0001, C7.2a, D-17; biện pháp bù đắp nằm trong ADR 0012 |
| Đổi tên GitHub environment `prod` bây giờ | ADR 0012 (D-16, C7.2d) |
| GitHub Team hoặc Enterprise, GHAS cho repo private, chuyển Infra thành public | D-14: gói Free, repo app public, repo gốc và Infra private; thay bằng gitleaks và OIDC chỉ cho `main` |
| Vercel Pro trước tenant trả tiền đầu tiên | D-18 |
| Người duyệt mọi PR trong giai đoạn dev | DM-11.5 / D-13 |
| Chuyển sang role agent tối thiểu quyền trước prod | D-15, N-8 (mục theo điều kiện U-53) |
| Security Hub và AWS Config trước prod | Chi phí và nhiễu; làm cùng prod (C7.2) |
| pgaudit trên Dev | D-08; chỉ prod |
| Xoay secret 90 ngày trên Dev | D-02, D-03, DM-8.9 |
| Diễn tập khôi phục hằng quý trên Dev | DM-9.3, N-2 |
| Trigger eval theo từng PR, hoặc eval trên toàn bộ catalog | D-23, N-4, DM-10.6 |
| Bảng `shared.feature_flag` hoặc dịch vụ cờ trả phí | DM-1.5; sổ đăng ký là một tài liệu |
| Tag `Env` mới hoặc script mới gọi Cost Explorer | DM-10.1, DM-10.4 |
| Secret master được quản lý tự động trước X1 | C2.3b, DM-8.9, D-04 |
| Canary, blue/green, CodeDeploy cho ECS | Circuit breaker + alarm + rollback task definition là đủ |
| Một Pact broker | oasdiff + contract JSON Schema là đủ |
| Site tài liệu, MkDocs, Backstage, tài liệu có phiên bản, site đa ngôn ngữ, cổng tài liệu | Bây giờ là Git + danh mục; tiếp theo `/admin/docs`; site chỉ khi có điều kiện kích hoạt |
| Backlog sinh tự động | D-22: cập nhật tay cuối phiên |
| Tracing trước khi có một job chậm không giải thích được | D-21 |
| Kubernetes, service mesh, cổng developer tự host | Vượt quy mô |
| Audit SOC 2 / ISO 27001 / ISO 42001, SLSA L3, OWASP SAMM đầy đủ, nghi thức Scrum, CAB, lịch trực paging, chính sách error budget chính thức trên Dev | Chỉ chuẩn bị bằng chứng (bản ghi PR, sổ đăng ký, postmortem) |
| Khoá cứng theo username trong giới hạn tần suất đăng nhập | Cho kẻ tấn công khoá được nhân sự |
| Nền tảng DORA/cờ trả phí (ví dụ LaunchDarkly), arc42 đầy đủ, analytics hoặc widget phản hồi cho tài liệu, Vale như một check chặn, CODEOWNERS nhiều người, API playground nội bộ | Quá mức cho một kỹ sư + agent (guide S243 §7, pro-practices §7.2) |

### 9.4 Đề xuất luật không có trong data standards v1.1

Lộ trình S241 §5 đề xuất thêm các luật mà v1.1 (N-1) không nhận. Chúng không phải luật. Mỗi luật chỉ được nêu lại cùng
hạng mục lộ trình cần nó, trong PR của hạng mục đó: SEC-13 Redis AUTH/TLS (U-13), TST-8 test hai tenant và route admin
(U-12, U-27), TST-4 probe trong CI (U-16), CON-9 contract HTTP (U-44, ADR 0013), CON-10 Idempotency-Key (U-46), DM-6.4
Sentry như log ứng dụng (U-30), DM-6.11 export DSAR (U-32, D-11), DM-6.12 danh sách bên xử lý phụ từ tag `pii:` (U-23,
U-24), DM-8.8 ghi log exec (U-22, đã xong; chỉ còn phần chữ), DM-8.11 sổ đăng ký secret (U-26), DM-8.12 SG theo app
(U-18, đã xong; chỉ còn phần chữ), DM-10.7 một dòng "approved" cho mỗi khoản chi mới (D-19), DM-11.6 OIDC chỉ cho
`main` (U-01, đã xong; chỉ còn phần chữ), C2.3i throttle theo stage (U-19), C6.3c deploy guard đóng khi lỗi (U-08, đã
xong; chỉ còn phần chữ), C4.1/C4.1a các dòng alarm (U-07), C7.1 các dòng bảng (U-09), C7.2c/d/g/h và C1.3 (U-40, ADR
0012). Bỏ theo quyết định: DM-8.7 đổi profile (D-15, N-8), DM-8.9 xoay định kỳ (D-03), DM-9.3 diễn tập hằng quý trên
Dev (N-2).

---

## 10. Nhật ký quyết định

Nguồn: [`sessions/2026-10-17-S241-decisions.md`](sessions/2026-10-17-S241-decisions.md) cho D-xx và Q-xx, và bản ghi
phiên S243 cho N-x. Khi một quyết định đã đổi một chuẩn, chuẩn đó là văn bản thực thi.

### 10.1 S241 (17/10/2026)

| # | Quyết định | Thực thi ở |
|---|---|---|
| D-01 | Dev không chứa PII thật (số đếm chính xác: 8 khách hàng Booking và 6 khách hàng TripPlanner, đều là test hoặc nội bộ) | Trang này §6.1; Phần C C7.1a; mọi hướng dẫn ghi "chỉ dữ liệu test" |
| D-02 | Xoay token GitHub bị lộ khi go-live, không phải bây giờ | Checklist AA-880; [§7.5](#75-secret) |
| D-03 | Xoay mật khẩu RDS master khi go-live, không xoay định kỳ trên Dev | DM-8.9; AA-880; [runbook xoay secret](ops/runbooks/secret-rotation.md) |
| D-04 | Mật khẩu master được quản lý tự động sau X1 | Trigger U-41 |
| D-05 | Tách role X1 ngay bây giờ | AA-852, AA-860; [kế hoạch X1](audits/2026-10-17-S241-x1/x1-plan.md) |
| D-06 | Security group theo app trong đợt X1 | [ADR 0004b](adr/0004b-per-app-security-groups.md) |
| D-07 | ECS exec vẫn là đường chuẩn, có ghi log phiên ngay | DM-8.8; ghi log cluster của Infra; [runbook ECS exec](ops/runbooks/ecs-exec-s3-mediated.md) |
| D-08 | `log_connections` ngay, pgaudit ở prod | Parameter group RDS; AA-880 |
| D-09 | Log bảo mật/audit 365 ngày, log app 30 ngày | Bảng lưu giữ DM-7; C4.2b (v1.1); AA-872 |
| D-10 | Diễn tập khôi phục ngay; kết quả: đạt trong khoảng 22 phút | [Bằng chứng diễn tập](audits/2026-10-17-S241-restore-drill/); DM-9.3 |
| D-11 | Chưa có tính năng xoá/export; runbook thủ công khi có yêu cầu; nút bấm sau khi có đăng nhập khách hàng qua Cognito | AA-839 |
| D-12 | Tenant pool đóng khi lỗi trên toàn hệ; giữ rollback theo từng route | C2.3g, DM-8.4, SEC-10 (v1.1); [sổ đăng ký cờ](ops/feature-flags.md) |
| D-13 | Quyền merge theo rủi ro và giai đoạn: giai đoạn dev agent tự merge kể cả bảo mật/hạ tầng; cổng người từ prod hoặc tenant trả tiền đầu tiên | DM-11.5 (v1.1); `.claude/CLAUDE.md`; `session-workflow.md`; hook subagent |
| D-14 | Repo app public, repo gốc private, GitHub Free | [STYLE, trang được đặt ở đâu](STYLE.md#where-a-page-may-live-sec-06); [ADR 0014](adr/0014-repo-visibility-and-github-plan.md); U-25 |
| D-15 | Agent giữ profile `aa365-admin` | DM-8.7; [§7.6](#76-quyền-truy-cập) |
| D-16 | Bố cục và cổng prod chọn cùng ngày go-live | ADR 0012 (AA-880) |
| D-17 | Prod mặc định trên acc2 | ADR 0001; C7.2a; AA-880 |
| D-18 | Vercel Hobby tới tenant trả tiền đầu tiên, sau đó Pro | [§6.1](#61-môi-trường); ghi chú cho chủ doanh nghiệp |
| D-19 | Chi tiêu AWS mới được duyệt từng mục, báo giá trước | Mục chi phí trong mẫu PR; [FinOps](ops/finops.md); DM-10.7 chỉ giữ luật phê duyệt ("thay đổi chi tiêu cần tech lead duyệt") |
| D-20 | E-mail alarm khi ALARM và OK | Alarm của Infra (`ok_actions`); AA-872 |
| D-21 | Chỉ tracing khi một job chậm mà không giải thích được | AA-842 |
| D-22 | Backlog cập nhật tay cuối phiên | `session-workflow.md`; [backlog sống](backlog/README.md) |
| D-23 | Đo chất lượng qua các vòng audit; xây bộ mẫu chuẩn khoảng 100 mẫu từ dữ liệu có sẵn | AA-729; [§5.7](#57-prompt-và-model-llm) |
| D-24 | Cùng tech lead rà các issue Linear trước khi tạo; tránh project CIS Core đã đầy | Skill `aa-linear-issue`; các issue S241 vào Data Platform, CIS Portal và TripPlanner & AA-Booking |
| D-25 | Báo cáo bảo mật và dữ liệu thương mại chỉ ở repo gốc private | STYLE SEC-06; AA-889 quét trước khi track tài liệu CIS |

Các câu trả lời liên quan ở S241: Q1 một console admin với hai khu vực và link tới mọi app; Q2 chỉ owner (tech lead +
một tài khoản khẩn cấp) được đổi quyền của người khác; Q3 một bảng grant (người, app, role); Q4/Q5 role nhân sự Booking
và role nội dung qua group Cognito; Q6 không có UI tạo nhân sự trước Cognito; Q7 gộp ba issue kế hoạch admin; Q8 tách
tenant portal ngay (AA-885, đã xong); Q9 trang tổng quan vận hành do agent làm, rồi cho chủ doanh nghiệp xem (AA-858);
Q10 làm xong khối nền tảng (admin, X1, Cognito, tách portal) trước khi quay lại nội dung CIS. Giai đoạn dev: agent
code, push, merge, kiểm và báo cáo, kể cả các PR bảo mật và hạ tầng.

S241 cũng duyệt chi phí Cognito Phase 0 (14 alarm, 2 metric, secret break-glass, ~2,4 USD/tháng; WAF ~7 USD khi mở
đăng ký khách hàng) và các cách đăng nhập của khách hàng (AA-680); D-18 bổ sung: chỉ xem lại Amplify nếu Vercel vượt
~50 USD/tháng.

### 10.2 S243 (19/10/2026)

| # | Quyết định | Thực thi ở |
|---|---|---|
| S243 | Chấp nhận toàn bộ sổ tay tài liệu và lộ trình; làm hết, việc 0 USD trước; hướng dẫn cho chủ doanh nghiệp song ngữ; thêm các hướng dẫn vai trò (kỹ sư mới, DevOps, CTO, CIO, PM) | Trang này; [danh mục](README.md); [`guides/`](guides/) |
| N-1 | Duyệt data standards v1.1 (DM-11.5, C2.3g + DM-8.4 + SEC-10, các dòng DM-7 + C4.2b, DM-11.2, DM-1.2) | [Changelog của data standards](architecture/data-standards/README.md#changing-this-standard) |
| N-2 | Giữ mặc định: không diễn tập hằng quý trên Dev | DM-9.3; [§7.4](#74-backup-và-khôi-phục-thảm-hoạ) |
| N-3 | Trang bảo mật và audit trên `/admin/docs` chỉ role `owner` xem được | Kiểm role ở backend của AA-898; [§4.3](#43-tài-liệu-nằm-ở-đâu) |
| N-4 | Giữ mặc định: không trigger eval theo PR; eval chạy tay | AA-900; D-23 |
| N-5 | Giữ mặc định: `prompt_version` đi cùng ledger v2 của AA-804 | AA-804; AA-900 |
| N-6 | Tạo issue U-25: AA-901 (GitHub App, hai ADR gốc, CODEOWNERS; hai ADR thành [0011](adr/0011-github-app-identity-and-merge-rights.md) và [0014](adr/0014-repo-visibility-and-github-plan.md) vì số 0010 đã dành cho AA-Partner); tech lead tự tay sửa luật chung (ngoại lệ `Refs` cho PR phát hành, luật merge) | AA-901; AA-891 |
| N-7 | Quy ước ngôn ngữ: hướng dẫn cho chủ doanh nghiệp và các hướng dẫn vai trò song ngữ EN-VI; audit tư vấn cho tech lead được viết tiếng Việt. Phần song ngữ đã được S255 thay thế ([§10.3](#103-s255-2026-10-28)) | [`language-convention.md`](../.kiro/steering/language-convention.md); [§4.8](#48-ngôn-ngữ) |
| N-8 | Giữ mặc định: agent ở lại `aa365-admin` | DM-8.7; D-15 |
| N-9 | Giữ mặc định: AA-697 tiếp tục tạm gác; bảng sinh tự động lấy từ AA-893 | Backlog §4; AA-893 |
| N-10 | Giữ mặc định: bằng chứng diễn tập, quyền truy cập và dung lượng ở lại `docs/audits/` | DM-8.10, C7.2b, C8a |
| N-11 | Giữ mặc định: bây giờ chỉ export OpenAPI + oasdiff; ADR 0013 trước mọi thay đổi `/booking/v1` | AA-899 |
| N-12 | U-04 gộp vào AA-878, U-61 gộp vào AA-879 | AA-878, AA-879 |

Cùng phiên đó cũng quyết các mục sản phẩm và nền tảng ngoài phạm vi sổ tay này (nhân sự Booking định danh theo id
Cognito với một lần backfill, domain portal và link trang pháp lý, xoá secret mồ côi sau khi kiểm, sinh mật khẩu X1
S17); chúng được ghi trong log phiên S243.

### 10.3 S255 (2026-10-28)

| # | Quyết định | Thực thi ở |
|---|---|---|
| S255-L1 | Trang danh mục chỉ viết tiếng Anh. Tiếng Việt nằm trong bản dịch đầy đủ đặt cạnh, `<name>.vi.md` (`lang: vi`, `translation_of`), không bao giờ trộn vào trang tiếng Anh; luật này thay các trang song ngữ của N-7 | [§4.8](#48-ngôn-ngữ); schema front-matter và [STYLE](STYLE.md#language) sẽ cập nhật theo |

---

## 11. Thuật ngữ

Bảng thuật ngữ đầy đủ (theo lĩnh vực, kèm thuật ngữ tiếng Việt): [`glossary.md`](glossary.md). Mười lăm thuật ngữ sổ tay
này dựa vào nhiều nhất:

| Thuật ngữ | Tiếng Việt | Nghĩa trong AA-Ecosys |
|---|---|---|
| ADLC | Vòng đời phát triển có agent | Tên chúng ta đặt cho SDLC + kiểm soát AI agent + vòng đời tính năng LLM ([§2.1](#21-mô-hình)) |
| Trunk-based development | Phát triển trên một nhánh chính | Nhánh ngắn, squash merge vào `main` (ADR-2026-023) |
| Definition of Ready (DoR) | Điều kiện sẵn sàng | Những gì một issue cần trước khi agent xây nó ([mẫu](templates/definition-of-ready.md)) |
| Definition of Done (DoD) | Điều kiện hoàn thành | Đã merge + CI xanh + rollout COMPLETED + đã kiểm live (`aa-ship`) |
| Deploy gate | Cổng chặn deploy | Bước CI chặn deploy backend khi một rerun wave đang mở hoặc một job chặn deploy đang chạy hay sắp tới hạn (DM-11.4, AA-993 G5) |
| Deploy vs release | Triển khai và phát hành | Code đang chạy so với người dùng nhìn thấy; một cờ tách hai việc này |
| Feature flag | Cờ tính năng | Một công tắc không cần deploy; loại release, ops, security ([sổ đăng ký](ops/feature-flags.md)) |
| Expand / contract | Mở rộng / thu hẹp | Đổi schema hay API theo từng bước để cũ và mới cùng chạy |
| SemVer | Đánh phiên bản ngữ nghĩa | `MAJOR.MINOR.PATCH` theo độ tương thích; chúng ta ở `0.x` tới prod |
| release-please | release-please | Bot mở PR phát hành kèm tăng phiên bản và CHANGELOG (AA-891) |
| Immutable image tag | Tag image bất biến | `dev-<sha>`, không bao giờ bị ghi đè, nên rollback chính xác |
| Runbook / playbook | Sổ tay vận hành / kịch bản xử lý | Các bước chính xác cho một việc / chiến lược cho một loại sự cố |
| Break-glass | Lối khẩn cấp | Quyền truy cập khẩn cấp chỉ dùng khi quyền thường không dùng được, sau đó xoay |
| RPO / RTO | Mất dữ liệu tối đa / thời gian dừng tối đa | Mức mất dữ liệu / thời gian dừng chấp nhận được; mục tiêu ở DM-9.6 |
| Cost allocation tag | Tag phân bổ chi phí | `App` và `Environment`, để chi phí tách theo app và môi trường |

---

## 12. Lịch sử thay đổi và các tài liệu bị thay thế

### 12.1 Lịch sử thay đổi

| Ngày | Phiên | Thay đổi |
|---|---|---|
| 2026-10-17 | S241 | Review SDLC/ADLC (sáu lĩnh vực) và lộ trình nền tảng hợp nhất U-01…U-61 cùng các quyết định D-01…D-25 |
| 2026-10-19 | S243 | Guide SDLC/tài liệu/phiên bản, đề xuất chuẩn tài liệu, thực hành tài liệu chuyên nghiệp, và đối chiếu với S241 và data standards (xung đột K-xx, các điểm sửa, quyết định N-1…N-12) |
| 2026-10-19 | S243 | Sổ tay này: một trang cho quy trình, tài liệu, phiên bản, phát hành, vận hành, chi phí, lộ trình và quyết định; áp mọi điểm sửa từ bản đối chiếu; sáu tài liệu được đánh dấu bị thay thế: review và lộ trình S241 và bốn file tư vấn S243 (AA-887) |
| 2026-10-28 | S255 | Review tài liệu: các tóm tắt tiếng Việt chuyển sang bản dịch `engineering-handbook.vi.md`; người được gọi theo vai trò; reference sinh tự động, `/admin/docs`, cổng deploy (AA-993 G5), ngân sách và việc acc1 rời hệ (AA-998) được cập nhật; quyết định ngôn ngữ S255 |

### 12.2 Các tài liệu bị thay thế

Giữ lại làm lịch sử và bằng chứng. Đừng trích chúng như luật hiện hành; hãy trích trang này hoặc nguồn chuẩn mà nó dẫn
link.

| Tài liệu | Bị thay bởi |
|---|---|
| [`audits/2026-10-17-S241-sdlc-review/README.md`](audits/2026-10-17-S241-sdlc-review/README.md) (review SDLC/ADLC S241) | Trang này; bằng chứng theo từng lĩnh vực ở lại [`areas/`](audits/2026-10-17-S241-sdlc-review/areas/) |
| [`audits/2026-10-17-S241-sdlc-review/unified-roadmap.md`](audits/2026-10-17-S241-sdlc-review/unified-roadmap.md) (U-01…U-61, D-01…D-25) | [§9](#9-lộ-trình) và [§10](#10-nhật-ký-quyết-định) |
| [`audits/2026-10-19-S243-sdlc-docs-versioning/README.md`](audits/2026-10-19-S243-sdlc-docs-versioning/README.md) (guide SDLC/ADLC, thuật ngữ) | [§2](#2-mô-hình-làm-việc)-[§8](#8-chi-phí-finops), [thuật ngữ](glossary.md) |
| [`audits/2026-10-19-S243-sdlc-docs-versioning/docs-standard-proposal.md`](audits/2026-10-19-S243-sdlc-docs-versioning/docs-standard-proposal.md) (danh mục, chuẩn, nơi lưu trữ, issue) | [§4](#4-hệ-thống-tài-liệu), [danh mục](README.md), [STYLE](STYLE.md) |
| [`audits/2026-10-19-S243-sdlc-docs-versioning/docs-pro-practices.md`](audits/2026-10-19-S243-sdlc-docs-versioning/docs-pro-practices.md) (thực hành tài liệu chuyên nghiệp) | [§4](#4-hệ-thống-tài-liệu), [STYLE](STYLE.md), [mẫu](templates/) |
| [`audits/2026-10-19-S243-sdlc-docs-versioning/reconciliation-s241-standards.md`](audits/2026-10-19-S243-sdlc-docs-versioning/reconciliation-s241-standards.md) (K-xx, các điểm sửa, N-1…N-12) | Các điểm sửa đã áp khắp trang này; quyết định ở [§10.2](#102-s243-19102026) |

Không bị thay thế: các báo cáo theo lĩnh vực của S241 (bằng chứng), thư mục diễn tập khôi phục và X1, và
[`sessions/2026-10-17-S241-decisions.md`](sessions/2026-10-17-S241-decisions.md) (chính bản ghi quyết định).
