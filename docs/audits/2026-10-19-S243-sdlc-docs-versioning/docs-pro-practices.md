> Superseded on 2026-10-19 (S243) by docs/engineering-handbook.md — kept for history.

# Tài liệu hệ thống "chuẩn thương mại": tổ chức, viết, quản trị, trình bày

> S243 · 19/10/2026 · Tác nhân: Claude Code (research, đọc-only) · Đối tượng: Nghiệp
>
> Câu hỏi: làm sao để tài liệu nội bộ của AA_Ecosys được **tổ chức, viết, quản trị và trình bày** chuyên nghiệp,
> dễ đọc, giống các trang docs thương mại (Stripe, Vercel, GitLab…), trong điều kiện 1 kỹ sư + AI agents
> và 1 chủ doanh nghiệp không rành kỹ thuật.
>
> Phạm vi: bản này **không** so sánh nơi host/chi phí host (một agent khác làm). Nó bổ sung cho
> `README.md` cùng thư mục (§3 Documentation: Diátaxis, ma trận nguồn sự thật, docs-as-code, version docs).
> Chỗ nào README đã nói thì ở đây chỉ trỏ lại, không lặp.
>
> Mức áp dụng: **[TUẦN 1]** làm ngay · **[TRƯỚC PROD]** · **[SAU NÀY]** · **[OVERKILL]** = chưa nên làm với quy mô hiện tại.
> Chỗ chưa kiểm được từ nguồn gốc ghi **[cần kiểm]**. Nguồn đầy đủ ở §8.

---

## 0. Tóm tắt một trang

1. **Docs chuyên nghiệp không nhờ công cụ, mà nhờ 4 thứ lặp lại đều:** cấu trúc theo nhu cầu người đọc (Diátaxis),
   khung trang cố định (template), văn phong nhất quán (style guide ngắn), và quản trị (owner + review trong PR + độ tươi).
   Site đẹp chỉ là lớp trình bày; nếu 4 thứ trên chưa có thì site chỉ làm lộ sự lộn xộn rõ hơn.
2. **Information architecture (IA) ≠ cấu trúc thư mục.** Có thể giữ nguyên file hiện có và dựng IA bằng **trang index +
   sidebar config**. Không cần dời file ồ ạt (khớp README §3.2).
3. **Ba "cửa" cho ba loại người đọc:** Engineer (Nghiệp), Agent (Claude Code/Kiro), Business (chị Thư). Mỗi cửa là một trang
   landing chỉ chứa link ("traffic cop" — Google SWE book). Trang cho chị Thư viết tiếng Việt, ngôn ngữ kinh doanh.
4. **Mọi trang có front-matter** (`title`, `description`, `type`, `audience`, `owner`, `status`, `last-reviewed`) và khung
   cố định: TL;DR → điều kiện trước → các bước → kiểm tra → rollback → liên quan. Đây là thứ làm docs "trông thương mại" nhất.
5. **Thứ gì sinh được thì sinh** (OpenAPI, schema dump, contracts, Terraform outputs) và đánh dấu "generated — do not edit".
   Hệ mình đã có mẫu rất tốt: `docs/architecture/db-schema-reference.md`.
6. **Quản trị cho 1 người** = Docs Definition of Done trong `aa-ship` + link check + cảnh báo trang quá hạn review (không chặn
   merge) + 30 phút review docs mỗi quý. Bỏ qua dashboard metrics, CODEOWNERS nhiều người, versioned site.
7. **Agent là người đọc hạng nhất:** index kiểu `llms.txt`, `description` 1 câu ở front-matter để agent chọn đúng file (tiết
   kiệm token), file hướng dẫn agent ngắn và chỉ trỏ link. Quy tắc quan trọng: **agent không được tự bump `last-reviewed`
   nếu chưa đối chiếu với hệ thống thật.**
8. **Nếu dựng site sau này:** Astro Starlight là mặc định hợp lý về tính năng (Pagefind search, sidebar tự sinh, edit link,
   last-updated, plugin OpenAPI/versions/llms.txt/link validator); Docusaurus nếu cần versioning mạnh; **tránh chọn mới
   MkDocs Material** — đã thông báo end of life 05/05/2027 (người kế nhiệm: Zensical).

---

## 1. Học từ ai — mỗi nguồn một bài học

| Nguồn | Bài học chính áp được cho AA_Ecosys |
|---|---|
| **Stripe Docs** (Markdoc) | Tách nội dung khỏi code trình bày; Markdown + một ít custom tag có kiểm soát; **validate docs trong CI** (schema tag, link) và trong editor. Bài học: dùng Markdown thuần + vài quy ước, để CI bắt lỗi, đừng nhúng logic vào docs. |
| **Vercel Docs** | Landing chia theo **việc người đọc muốn làm** (Deploy, Build with AI, Secure, Operate), không theo cấu trúc tổ chức. Mỗi trang có bản `.md` với front-matter `type`, `prerequisites`, `related`, `summary`, `last_updated` — chính là mẫu front-matter cho cả người lẫn agent. Mục "What's new" kéo từ changelog. Có mục riêng "Set up your coding agent" và sitemap đầy đủ. |
| **GitLab Handbook** | "Handbook first": thay đổi quy trình = sửa handbook qua merge request trước, rồi mới thông báo. Content site dùng `.gitlab/CODEOWNERS` để duyệt theo mục; bẫy thực tế: owner đã nghỉ còn trong CODEOWNERS làm MR treo mãi (MR 20577) → owner phải là vai trò còn sống. |
| **GitLab Docs topic types** | Mỗi topic là một trong **Concept / Task / Reference / Troubleshooting**; trang thường mở bằng concept rồi tới task/reference. Không đặt tiêu đề "Overview"/"Introduction"; tiêu đề < 70 ký tự; tránh trang chỉ có link (trừ trang top-level) và topic chỉ 1–2 câu; mục "Related topics" đặt trên Troubleshooting. |
| **Diátaxis** | 4 loại: tutorial, how-to, reference, explanation. **Không dựng khung rỗng trước**; cải thiện từng bước nhỏ, mỗi bước đúng hướng thì publish ngay; "complete, not finished". → Sitemap ở §6 là *đích*, chỉ tạo mục khi đã có nội dung. |
| **Software Engineering at Google, ch.10** | Docs như code: source control, owner, review, issue như bug. **Freshness date + owner**, nhắc khi 3 tháng không đụng; byline "Last reviewed by…" tăng độ tin. 2 đoạn đầu trả lời WHO/WHAT/WHEN/WHERE/WHY. Landing page là "traffic cop" chỉ có link. Docs lỗi thời thì xoá hoặc đánh dấu obsolete + trỏ bản mới. |
| **Google developer documentation style guide** | Second person "you", active voice, điều kiện đặt trước hướng dẫn, sentence case cho heading, numbered list cho bước, code font cho mọi thứ liên quan code, UI element in đậm, link text mô tả, ngày tháng không mơ hồ, alt text cho ảnh. |
| **Microsoft Writing Style Guide** | Ít chữ, đi thẳng vào ý, front-load keyword để quét mắt, câu bắt đầu bằng động từ, bỏ "you can"/"there is", sentence case, không chấm câu cuối heading, Oxford comma. |
| **AWS Well-Architected** | Cấu trúc: pillar → design principles → câu hỏi → best practices; review là "constructive conversation, not an audit"; trang có ngày publish + "Document revisions". → Dùng 6 pillar làm khung cho câu hỏi review quý (§4.8) và cho mục Security/Cost/Reliability. |
| **Write the Docs — Docs as Code** | Issue tracker, version control, plain-text markup, code review, automated tests cho docs; writer và dev cùng sở hữu docs. |
| **Backstage TechDocs** (Spotify gốc) | Docs nằm cạnh code, portal gom lại hiển thị; build trong CI rồi publish lên storage (S3…). Mô hình "docs ở từng repo, một nơi gom" chính là bài toán cross-repo của mình. TechDocs dựa trên MkDocs → để ý tác động của việc MkDocs Material EOL **[cần kiểm]** hướng đi của Backstage. |
| **Atlassian Confluence** | Mỗi space có trang **Overview** làm landing; cây trang **nông**; template cho nội dung lặp lại; một "gardener" dành ~10 phút mỗi tháng/quý tỉa cây; lưu trữ bằng parent "Archived" hoặc archive space thay vì xoá. |
| **The Good Docs Project** | Bộ template mở: quickstart, tutorial, how-to, concept, reference, troubleshooting, glossary, release notes, changelog, README, style guide, user personas… (không có runbook/ADR/postmortem — lấy từ SRE book và ADR hiện có). |
| **Google SRE Book — Example postmortem** | Khung postmortem: Date, Authors, Status, Summary, Impact, Root causes, Trigger, Resolution, Detection, Action items, Lessons learned (went well / went wrong / got lucky), Timeline, Supporting info. |
| **AGENTS.md / llms.txt** | AGENTS.md = "README cho agent", file gần nhất thắng trong monorepo, nay do Agentic AI Foundation (Linux Foundation) quản; llms.txt = index Markdown ở gốc site (H1, blockquote tóm tắt, các H2 danh sách link, mục "Optional"), kèm bản `.md` của từng trang. |
| **Monzo / Spotify** | Không tìm thấy engineering handbook công khai đáng tin. Monzo chỉ có blog "Engineering principles" (2018, "không phải luật, là hướng dẫn"); Spotify đóng góp qua Backstage/TechDocs. Không dùng làm mẫu. |

---

## 2. Information architecture (IA)

### 2.1 Các mục cấp 1 điển hình của docs nội bộ/platform tốt

| Mục | Trả lời câu hỏi | Loại Diátaxis | Ví dụ thương mại | Hệ mình hiện có |
|---|---|---|---|---|
| **Start here / Get started** | Tôi mới vào, đọc gì trước, cài gì, chạy thử thế nào? | Tutorial | Vercel "Ship anything", Stripe quickstart | Rải rác trong README từng repo; **chưa có onboarding cấp hệ** |
| **Architecture / Concepts** | Hệ gồm gì, ranh giới ở đâu, tại sao như vậy? | Explanation | AWS Well-Architected, Stripe "How X works" | `docs/ecosystem-architecture.md`, `apps/*/CONTEXT.md`, `docs/architecture/data-standards/` |
| **Guides / How-to** | Làm việc X thế nào (deploy, migrate, thêm app)? | How-to | Vercel KB, GitLab task topics | Skill `skill/aa-ship/`, `skill/aa-wave-rerun/`, `docs/db-access-ssm-tunnel.md` |
| **Reference** | Tên chính xác, tham số, shape, giá trị? | Reference (nên sinh tự động) | Stripe API ref | `db-schema-reference.md` (sinh), `docs/contracts/*.json`, `owners.yaml`; OpenAPI chưa export |
| **Operations / Runbooks** | Có sự cố/alarm thì làm gì, từng bước? | How-to (khẩn) | Google SRE, PagerDuty | `docs/ops/incident-response.md`, CIS `docs/runbooks/clean-rerun.md`, `docs/CIS_Runbook_v1.md` |
| **Security** | Ai truy cập gì, secret ở đâu (chỉ tên), xử lý rò rỉ? | Explanation + Reference + How-to | AWS Security pillar | ADR 0006/0006a, 0004b; secrets register chưa có (AA-878) |
| **Cost** | Tốn bao nhiêu, vì sao tăng, quy tắc chi tiêu? | Reference + Explanation | AWS Cost pillar | Rải trong memory; chưa có `finops.md`, chưa có báo cáo tháng |
| **Decisions (ADR)** | Đã quyết gì, khi nào, đánh đổi gì? | Explanation | GitLab, ThoughtWorks | `docs/adr/` + index (tốt) |
| **Changelog / Release notes** | Bản nào ra gì, ảnh hưởng tôi thế nào? | Reference | Vercel changelog, Stripe changelog | Chưa có (README §4.4) |
| **Glossary** | Thuật ngữ X nghĩa là gì ở hệ này? | Reference | GitLab glossary | README §8 (đề xuất tách `docs/glossary.md`) |
| **Process / Journal** (riêng của mình) | Đã làm gì, theo thứ tự nào? | Không phải docs sản phẩm | GitLab handbook changelog | `docs/sessions/`, `backlog/`, `audits/`, `research/`, `implementation-notes/` |

Ghi chú: mục **Process/Journal** phải tách rõ khỏi docs sản phẩm và gắn nhãn "nhật ký, không phải sự thật hiện hành"
(README §3.1). Lý do: search và agent hay trả về audit cũ như thể đó là quy tắc hiện tại.

### 2.2 Độ sâu điều hướng

- **Tối đa 3 cấp** trong sidebar (Mục → Nhóm → Trang). Sâu hơn thì tách thành mục cấp 1 hoặc dùng "sidebar topics"
  (Starlight có plugin `starlight-sidebar-topics`). Confluence cũng khuyên cây nông.
- **Mỗi nhóm có ≥ 2 trang** mới tạo nhóm; 1 trang thì để ở cấp trên (Diátaxis: không tạo khung rỗng).
- **Trang landing của mỗi mục** chỉ có: 2–3 câu "mục này để làm gì", danh sách link có mô tả 1 dòng, "bắt đầu từ đây".
  Không nhồi nội dung vào landing (Google "traffic cop"; GitLab: trang chỉ-link chỉ hợp lệ ở top-level).
- **Tiêu đề trang = việc người đọc làm** cho how-to ("Roll back an ECS deploy"), = danh từ cho concept/reference
  ("Job runner", "Booking API"). Không "Overview", không "Misc", không tên issue (`AA-816.md` là process doc, không phải trang sản phẩm).

### 2.3 Docs cho từng người đọc

| Người đọc | Cần gì | Cửa vào | Ngôn ngữ | Không cho xem / không cần |
|---|---|---|---|---|
| **Engineer** (Nghiệp, sau này contractor) | Kiến trúc, cách làm, runbook, reference chính xác | `docs/README.md` → Start here | English | — |
| **Agent** (Claude Code, Kiro, agent khác) | Quy tắc bắt buộc, index file, reference máy đọc được (JSON/OpenAPI), lệnh verify | `CLAUDE.md`/steering → `docs/llms.txt` (index) | English | Văn bản dài giải thích lịch sử; nên trỏ thẳng vào reference |
| **Business owner** (chị Thư) | Hệ làm được gì, release mới có gì, tốn bao nhiêu, rủi ro/quyết định cần chị | `docs/business/README.md` | **Tiếng Việt**, không thuật ngữ, có ảnh | Runbook, ARN, tên bảng, mã Linear nội bộ (khớp quy tắc Jira) |
| **Tenant / đối tác B2B** (sau này) | API, contract, quickstart tích hợp | Docs public riêng | English | Mọi thứ nội bộ — **tách site/khu vực**, không chung với docs nội bộ |

Bài học Google SWE book: "luôn chọn **một** người đọc chính cho mỗi trang". Một trang không phục vụ cả chị Thư lẫn agent.
Khi cần cả hai: trang kỹ thuật tiếng Anh + một khối "Tóm tắt cho kinh doanh" tiếng Việt ở đầu, hoặc trang business riêng trỏ sang.

### 2.4 Gom tài liệu nhiều repo (cross-repo aggregation)

Hiện trạng: root `AA-Ecosys` + 4 repo con (CIS, Booking, TripPlanner, Infra), mỗi repo có `CONTEXT.md`, `README.md`, `docs/`.

| Cách | Mô tả | Hợp khi | Mức |
|---|---|---|---|
| **A. Index ở root, docs ở repo con** | `docs/apps/<app>.md` ở root = trang landing mỗi app: 5 dòng mô tả + link GitHub tới `CONTEXT.md`, runbook, ADR của repo đó | Bây giờ (repo-only) | **[TUẦN 1]** |
| **B. Build site kéo nhiều repo** | CI checkout 4 repo, mount `apps/*/docs` vào site dưới `/apps/<app>/` | Khi đã chọn site generator | [TRƯỚC PROD] nếu chọn site |
| **C. Portal kiểu Backstage TechDocs** | Mỗi repo build docs, publish S3, portal gom theo catalog | Nhiều team, hàng chục service | **[OVERKILL]** |

Quy tắc chung dù chọn cách nào: **sự thật cấp app ở repo app; sự thật cấp hệ ở root; root chỉ trỏ link, không chép**
(GitLab "single source of truth"; README §3.3). Lưu ý: CIS `docs/` đang bị gitignore (README §3.4 mục 7) — phải sửa trước
khi gom bất cứ thứ gì của CIS.

---

## 3. Giải phẫu trang và template

### 3.1 Front-matter chuẩn (mọi trang viết tay thuộc docs sản phẩm)

```yaml
---
title: Roll back an ECS deploy            # sentence case, < 70 chars
description: Return aa-cis-dev-api to the previous task definition in under 5 minutes.  # 1 sentence; agents read this first
type: how-to                              # tutorial | how-to | reference | explanation | runbook | adr | postmortem | report
audience: engineer                        # engineer | agent | business
owner: nghiep                             # accountable person (a role that exists, not a departed name)
status: stable                            # draft | stable | deprecated | archived
last-reviewed: 2026-10-19                 # date a human verified it against the live system
review-every: 90d                         # runbook 90d, reference 90d, explanation 180d, adr: never
applies-to: aa-cis-api >= v0.4.0          # optional, once releases are tagged
superseded-by:                            # set when status: deprecated
related: [docs/ops/incident-response.md, skill/aa-ship/SKILL.md]
---
```

- `title` + `description` là tên field **gốc** của Starlight/Docusaurus/Nextra/Mintlify → sau này lên site không phải sửa.
  Các field còn lại là field mở rộng (Starlight cho mở rộng schema front-matter; MkDocs/Docusaurus bỏ qua field lạ) **[cần kiểm]**
  chi tiết từng tool khi chọn.
- Dùng gạch nối (`last-reviewed`) cho khớp đề xuất ở README §3.4. Chọn một kiểu và giữ nguyên.
- File sinh tự động **không** dùng front-matter này; thay bằng dòng đầu `<!-- GENERATED by <workflow> — do not edit -->`
  + dòng "Verified …" như `db-schema-reference.md`.
- GitHub hiển thị front-matter YAML thành bảng nhỏ ở đầu file → đọc trên GitHub vẫn ổn.

### 3.2 Khung trang chung (thứ tự cố định)

1. **Tiêu đề** (H1 = `title`).
2. **TL;DR** — 1–3 câu: trang này giúp làm gì, kết quả là gì (WHO/WHAT/WHY của Google).
3. **Before you begin / Prerequisites** — quyền, profile AWS, công cụ, trạng thái cần có (vd "no queued job in `shared.job`").
4. **Thân trang** theo loại (bên dưới).
5. **Verify** — lệnh/URL chứng minh đã thành công, kèm kết quả mong đợi.
6. **Rollback / Undo** — với mọi trang có thay đổi hệ thống.
7. **Troubleshooting** — lỗi hay gặp → nguyên nhân → cách sửa (link `skill/aa-lessons/lessons.md` khi có).
8. **Related** — 3–6 link có mô tả.
9. **Footer tự động** (khi có site): last updated (git), edit this page, owner.

### 3.3 Template theo loại

Template đặt ở `docs/_templates/` [TUẦN 1], viết tiếng Anh (theo language convention). Bản rút gọn dưới đây.

**How-to**
~~~markdown
# <Verb> <object>            (e.g. "Apply a DB migration on Dev")
<TL;DR: what you achieve, when to use this page.>
## Before you begin
- Access: <profile/role>   - State: <precondition>
## Steps
1. <One action per step. Condition first: "If X, run Y.">
   ```bash
   <single-line command>
   ```
   Expected: <output>
## Verify
## Roll back
## Related
~~~

**Runbook** (how-to khẩn, gắn với alarm)
```markdown
# Runbook: <alarm or symptom>
| Field | Value |
|---|---|
| Alarm | <CloudWatch alarm name> |
| Severity | SEV1/2/3 (see incident-response.md) |
| Owner | nghiep |
| Time to mitigate | <target> |
## Symptoms            — what you see (alarm text, error, page)
## Impact              — who is affected; tell Ms. Thư? (yes/no rule)
## Diagnose            — 3–5 checks, fastest first, each with a command and what "bad" looks like
## Mitigate            — stop the bleeding (rollback, scale, disable flag)
## Fix                 — root-cause fix or link to the issue
## Verify              — live check (curl 200 + shape)
## After               — postmortem needed? lessons.md entry?
```

**Concept / Explanation**
```markdown
# <Noun>                  (e.g. "Job runner")
<TL;DR: what it is, why it exists, in 2 sentences.>
## How it works           — one diagram (Mermaid) + 3–6 paragraphs
## Boundaries             — what it is NOT responsible for; who owns what
## Design choices         — link the ADRs; no decision text copied here
## Limits and gotchas
## Related
```

**Reference** (viết tay — chỉ khi không sinh được)
```markdown
# <Thing> reference
<One line: scope, source of truth, how generated or verified.>
| Name | Type | Default | Description |
|---|---|---|---|
## Examples
```

**ADR** — giữ đúng khuôn đang dùng ở `docs/adr/` (đã chuẩn): header bullet `Status` / `Scope` / `Implements` / `Amends` /
`Design` / `Linear`, rồi `## Context` → `## Decisions` → `## Consequences` (Positive / Negative-cost) → `## Alternatives considered`.
Amendment là file `NNNNa-…` riêng; ADR đã Accepted không sửa nội dung. Chỉ bổ sung: `## Review trigger` (điều kiện để xem lại
quyết định, vd "khi có > 3 tenant thật").

**Postmortem** (theo Google SRE, blameless)
```markdown
# Postmortem: <short title> (<YYYY-MM-DD>)
Status: draft | final · Authors: · SEV:
## Summary            ## Impact (who, how long, data?)
## Timeline (UTC+7)   ## Root causes   ## Trigger
## Detection (how we found out; how long it took)
## Resolution
## Action items       | Action | Type (prevent/detect/mitigate) | Issue | Status |
## Lessons learned    ### Went well  ### Went wrong  ### Where we got lucky
## Business summary (VI) — 3 câu cho chị Thư: chuyện gì, ảnh hưởng gì, đã làm gì để không lặp lại
```

**Monthly cost report** (`docs/cost/reports/YYYY-MM.md`)
```markdown
# Cost report <YYYY-MM>
## Tóm tắt cho kinh doanh (VI)   — tổng tháng, so tháng trước (+/-%), 1 câu lý do, có cần quyết gì không
## Totals by account              | Account | This month | Last month | Δ | Note |   (acc1 / acc2 / acc3)
## By app (tag App)               | CIS | TripPlanner | Booking | Shared | Untagged |
## Top 5 services and changes
## LLM spend                      — from shared.llm_call_log, by stage/role; cost per published tour (unit cost)
## Anomalies and actions          | Finding | Action | Issue |
## Budget status                  — budget vs actual, alerts fired
Source: Cost Explorer export <date>, query <link>. Owner: nghiep.
```

**Release note** (2 bản: kỹ thuật = CHANGELOG sinh tự động; kinh doanh = bản dưới)
```markdown
# <App> <vX.Y.Z> — <YYYY-MM-DD>
## Có gì mới (VI)            — 3–5 gạch đầu dòng theo lợi ích, có ảnh chụp màn hình
## Thay đổi cách dùng (VI)   — người dùng phải làm gì khác (nếu có)
## Đã sửa (VI)
## Technical changes         — link CHANGELOG.md section, PR list, migrations, contract versions
## Known issues
```

**Onboarding** (Start here — tutorial cấp hệ)
```markdown
# Start here
## What AA_Ecosys is (5 lines + C4 context diagram)
## Day 1: access          — GitHub org, AWS profiles (acc map), MFA, Linear, Notion (names only, no secrets)
## Day 1: run one app locally, run its tests
## Day 2: ship a tiny change end to end (branch → PR → CI → deploy Dev → verify live) — the aa-ship path
## How we work            — links: session workflow, language convention, Definition of Done, lessons
## Where things are       — this docs map
```

---

## 4. Quy tắc văn phong (rút từ Google + Microsoft, chỉnh cho hệ mình)

Đặt thành 1 trang `docs/STYLE.md` [TUẦN 1], ≤ 1 màn hình. Agent đọc trang này trước khi viết docs.

**Giọng văn và câu**
1. **Second person, active voice, present tense, imperative cho bước**: "Run the migration", không "The migration should be run".
2. **Một câu một ý, ≤ ~25 từ**; đoạn ≤ 4 câu. Front-load keyword ("Rollback: …").
3. **Điều kiện trước, hành động sau**: "If the deploy gate fails, re-run…". Không "Re-run… if the gate fails".
4. Bỏ "you can", "there is/are", "simply", "just", "obviously" (Microsoft "revise weak writing").
5. Không hứa trước tính năng (Google "don't pre-announce") — chưa ship thì ghi ở roadmap, không ghi ở docs.

**Heading và cấu trúc**
6. **Sentence case**, không chấm cuối, < 70 ký tự, không lặp lại tiêu đề cha (GitLab).
7. **Numbered list** cho trình tự; bullet cho liệt kê; **bảng** cho dữ liệu cặp đôi/so sánh. Mỗi bước 1 hành động.
8. Ngày tháng không mơ hồ: **ISO `2026-10-19`** trong front-matter và docs kỹ thuật; dd/mm/yyyy chỉ trong text tiếng Việt cho chị Thư.

**Code block**
9. Luôn có language tag (`bash`, `python`, `sql`, `hcl`, `json`); 1 lệnh một dòng, không ký tự prompt `$` (để copy được).
10. **Quy tắc nhà:** AWS CLI **một dòng**, luôn ghi rõ `--profile` và `--region` (bẫy WSL2 + bẫy sai account AA-517).
11. Placeholder dạng `<task-arn>` (kebab-case trong ngoặc nhọn), kèm câu giải thích lấy giá trị ở đâu.
    Tên biến môi trường có dấu gạch dưới: để trong code font và **Nghiệp tự sửa tay trong VSCode** (quy tắc toàn cục).
12. Có **output mong đợi** sau lệnh quan trọng. Không dán secret, token, ARN có account khác, dữ liệu khách thật.

**Admonition (callout)**
13. Chỉ 4 mức, dùng tiết kiệm (≤ 2 mỗi màn hình): **Note** (thông tin phụ), **Tip** (cách tốt hơn), **Warning** (có thể hỏng/tốn
    tiền), **Danger/Caution** (mất dữ liệu, ảnh hưởng prod, không đảo ngược). Hiện dùng cú pháp GitHub alert
    (`> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`, `> [!CAUTION]`) vì đọc trên GitHub; khi lên site chuyển sang `:::note` bằng
    script hoặc plugin hỗ trợ GitHub alert **[cần kiểm]** theo tool.

**Hình ảnh và sơ đồ**
14. **Diagram-as-code trước, ảnh sau.** Mermaid (GitHub render trực tiếp) cho flowchart, sequence, state, ER. Mỗi sơ đồ ≤ ~15 node.
15. **C4**: dùng **L1 System Context** (AA_Ecosys + người dùng + hệ ngoài: Bedrock acc3, Cognito, Vercel, Jev, DataForSEO…) và
    **L2 Container** (CIS API/worker, Booking, TP FE + Lambda, RDS, S3, Step Functions) ở `ecosystem-architecture.md`;
    **L3 Component** chỉ cho vùng phức tạp (CIS pipeline A/T-series); **bỏ L4 Code**. Mermaid C4 vẫn là **experimental**
    (cú pháp có thể đổi) → vẽ C4 bằng Mermaid `flowchart` với quy ước màu/nhãn C4, hoặc Structurizr DSL **[SAU NÀY]**.
16. Ảnh chụp màn hình chỉ cho hướng dẫn UI (chủ yếu cho chị Thư/UAT): cắt gọn, có alt text, ghi ngày chụp trong caption,
    PNG/WebP < 300 KB; video UAT để Google Drive (memory `uat-videos-after-tech`), docs chỉ link.

**Đặt tên và ngôn ngữ**
17. Tên file **kebab-case tiếng Anh** theo nội dung (`rollback-ecs-deploy.md`), không theo mã issue (mã issue chỉ cho
    `implementation-notes/`). Thuật ngữ thống nhất theo `docs/glossary.md` (vd luôn "tenant", không lúc "khách thuê" lúc "client").
18. **Language policy** (khớp `.kiro/steering/language-convention.md`):
    - Docs kỹ thuật (architecture, how-to, runbook, reference, ADR): **English**.
    - Docs cho kinh doanh (`docs/business/`, release note bản kinh doanh, tóm tắt báo cáo chi phí, tóm tắt postmortem): **tiếng Việt**.
    - Glossary **song ngữ EN ↔ VI** (cột "Giải thích cho người không kỹ thuật").
    - Session log, memory: tiếng Việt (như hiện nay). **Không** dịch toàn bộ docs kỹ thuật sang tiếng Việt / không bật i18n site **[OVERKILL]**.
19. Link text mô tả đích ("see the rollback runbook"), không "click here"; link tương đối trong repo.

**Kiểm bằng máy** (tuỳ chọn): Vale có package Google và Microsoft style để lint văn phong — **[SAU NÀY]**, chạy ở chế độ cảnh báo.
markdownlint (cấu trúc) + lychee/markdown-link-check (link) là đủ cho giai đoạn này.

---

## 5. Quản trị (governance) — bản cho 1 người + agents

### 5.1 Ownership

- Mỗi trang có `owner` trong front-matter. Giai đoạn Dev: gần như tất cả là `nghiep` — vẫn ghi, vì (a) agent biết hỏi ai,
  (b) khi có người thứ 2 chỉ cần đổi owner, (c) bài học GitLab: owner phải là người/vai trò còn tồn tại.
- **CODEOWNERS**: [TRƯỚC PROD], không phải bây giờ. Khi agent còn tự merge (memory `dev-phase-self-merge`) thì CODEOWNERS
  không chặn được gì. Trước prod, dùng nó để **bắt buộc người duyệt** các vùng nhạy cảm:
  `docs/adr/`, `docs/ops/runbooks/`, `docs/security/`, `infra/**`, file generated (chỉ bot được sửa).
- Mapping "lane" agent (CIS backend, portal, Booking, docs — S235) có thể ghi ở field phụ `maintainer` nếu cần, không bắt buộc.

### 5.2 Review trong PR + Docs Definition of Done

README §3.4 đã có PR template ô Docs. Bổ sung **Docs DoD** vào `skill/aa-ship/SKILL.md`:

```
Docs Definition of Done (a PR is not done until):
- [ ] Every page touched has valid front-matter (title, description, type, owner, status, last-reviewed).
- [ ] Behaviour changed → the how-to/runbook that describes it is updated in the same PR.
- [ ] New page is linked from its section index (no orphan pages).
- [ ] Generated references regenerated by CI, never edited by hand.
- [ ] Commands in changed pages were run (or marked "not run: <why>").
- [ ] Link check green.
- [ ] Business-visible change → business release note line (VI) drafted.
```

### 5.3 Độ tươi (freshness)

- **`last-reviewed` nghĩa là "một người đã đối chiếu với hệ thống thật"**, không phải "có ai sửa file". Ngày sửa file đã có
  trong git (và site sẽ hiện "last updated" từ git). Hai ngày khác nhau và đều hữu ích.
- **Script CI nhỏ** [TRƯỚC PROD; bản tay ở TUẦN 1]: đọc front-matter mọi `.md` trong `docs/`, cảnh báo
  (`::warning file=…`) khi `last-reviewed + review-every < hôm nay`, thiếu front-matter, hoặc `status: deprecated` quá 90 ngày.
  **Không chặn merge** (một người không nên bị CI khóa vì docs cũ). Chạy theo lịch hàng tuần, xuất ra job summary.
- Nhịp review gợi ý: runbook/reference **90 ngày**; explanation/architecture **180 ngày**; ADR **không** (bất biến; chỉ amend).
- Gắn vào nghi thức phiên: "bắt đầu session mới" đọc danh sách trang quá hạn cùng lúc với backlog sống.

### 5.4 Deprecation và lưu trữ

1. Trang lỗi thời → `status: deprecated` + `superseded-by:` + một callout Warning đầu trang trỏ bản mới (Google SWE: đánh dấu
   obsolete tốt hơn để một trang "trông có thẩm quyền" nhưng sai).
2. Sau 1 quý không ai cần → chuyển vào `docs/archive/YYYY/` (`status: archived`), bỏ khỏi index và search (site có thể exclude
   thư mục). Không xoá — git giữ lịch sử, giống "Archived parent page" của Confluence.
3. ADR không bao giờ archive; chỉ `Superseded by` / `Amended by`.
4. Ứng viên ngay hiện tại (theo README §3.3): `apps/AA-CIS-App/handoff.md`, các file `docs/*.md` rời (`audit-cis-*`, `g3-*`,
   `g5-*`, `inventory-old-refs.md`) — gắn deprecated hoặc chuyển sang `audits/`.

### 5.5 Version của docs gắn với release

- Docs nằm cùng repo → **tag `vX.Y.Z` chính là version docs** (README §3.5). Không cần cơ chế riêng.
- **Versioned docs site (dropdown chọn version) — [OVERKILL] tới khi** có người dùng bên ngoài chạy đồng thời ≥ 2 major
  version của một API (vd tenant B2B tích hợp Booking API). Ngay cả Docusaurus cũng nói "most of the time, you don't need
  versioning", và khuyên giữ < 10 version.
- Cần ngay bản nhẹ: field `applies-to` + với API public thì OpenAPI export theo tag (file `openapi.v1.json`) và mục
  "Deprecated" trong CHANGELOG có ngày gỡ.

### 5.6 Kỷ luật changelog

- Kỹ thuật: `CHANGELOG.md` mỗi repo theo **Keep a Changelog** (Added / Changed / Deprecated / Removed / Fixed / Security),
  sinh từ Conventional Commits bằng release-please (README §4.4). Không viết tay vào CHANGELOG ngoài phần release-please cho phép.
- Kinh doanh: release note tiếng Việt (template §3.3), gom theo **tháng** hoặc theo mốc chị Thư quan tâm — không theo từng PR.
- Cấp hệ: `docs/changelog.md` chỉ là danh sách link tới release của từng repo + ADR mới trong tháng (giống "What's new" của Vercel).

### 5.7 Single source of truth và reference sinh tự động

| Reference | Nguồn | Sinh thế nào | Trạng thái |
|---|---|---|---|
| DB schema | live catalog | `db-schema-dump.yml` (Infra) mở PR root | **Có — mẫu chuẩn** |
| Contracts giữa app | `docs/contracts/*.vN.M.json` | viết tay có version + test pin hash | Có |
| Schema ownership | `infra/AA-CIS-Infra/db/owners.yaml` | test registry; `schema-ownership.md` chỉ diễn giải | Có (nên coi yaml là gốc) |
| API mỗi app | FastAPI `/openapi.json` | CI export ra `docs/reference/api/<app>.openapi.json`, render bằng plugin site hoặc Redoc/Scalar | **Thiếu** — [TRƯỚC PROD]; giá trị phụ thuộc việc thêm `response_model` (S241: ~11/258 route CIS) |
| Terraform module | `.tf` | `terraform-docs` → README module | [SAU NÀY] |
| Endpoint/ARN đang chạy | `terraform output -json` (lọc, không secret) | CI ghi bảng reference | [SAU NÀY] |
| Job kinds, LLM routes | `shared.job`, `shared.llm_role_config` | export định kỳ như schema dump | [SAU NÀY] |
| Secrets register | Secrets Manager (chỉ **tên** + owner + rotation) | script list tên | AA-878 |

Quy tắc: file sinh có header "GENERATED … do not edit", CI là người duy nhất sửa, diff hiện trong PR để review.

### 5.8 Metrics và review định kỳ

Chỉ đo những thứ rẻ, tự động:

| Metric | Cách đo | Mục tiêu | Mức |
|---|---|---|---|
| Broken links | lychee trong CI | 0 | [TUẦN 1] |
| Trang thiếu front-matter | script freshness | 0 ở `docs/` sản phẩm | [TRƯỚC PROD] |
| Trang quá hạn review | script freshness | < 10% | [TRƯỚC PROD] |
| Trang mồ côi (không index nào trỏ tới) | script so link | 0 | [SAU NÀY] |
| Search misses / trang được đọc nhiều | analytics của site | — | **[OVERKILL]** (chỉ khi có site + người đọc thật) |

**Review docs hàng quý — 30 phút** (gộp với diễn tập restore theo quý ở README §6.4):
1. Xem danh sách trang quá hạn → review hoặc deprecate.
2. Mở landing của từng mục: còn đúng không, có trang mới nào chưa vào index?
3. Hỏi 6 câu Well-Architected (Operational excellence, Security, Reliability, Performance, Cost, Sustainability): docs có trả lời
   được câu "nếu X hỏng thì làm gì" cho mỗi pillar không? Thiếu → tạo issue.
4. Đọc `business/README.md` như chị Thư: có hiểu không? Có số liệu cũ không?
5. Chọn 1 runbook ngẫu nhiên, chạy thử phần Diagnose trên Dev.

### 5.9 Agent đọc và viết docs

**Đọc**
- **Điểm vào cho agent**: giữ mô hình hiện tại — `.kiro/steering/*.md` là nguồn, `.claude/CLAUDE.md` import bằng `@`.
  Có thể thêm `AGENTS.md` ở root (chuẩn mở, file gần nhất thắng, được Codex/Copilot/Cursor/Gemini CLI… đọc) với nội dung
  chỉ là trỏ sang steering — **[SAU NÀY]**, chỉ khi dùng thêm agent ngoài Claude Code/Kiro. Kiro có đọc `AGENTS.md` không: **[cần kiểm]**.
- **Index cho agent**: `docs/llms.txt` theo định dạng llms.txt (H1 tên dự án, blockquote 2 câu, các H2 "Start here",
  "Architecture", "Reference (generated)", "Operations", "Decisions", mục "Optional" cho audits/sessions). Rẻ, làm được ngay
  trong repo, và nếu lên site thì plugin (`starlight-llms-txt`, Mintlify tự sinh) thay thế. [TUẦN 1]
- **`description` 1 câu** ở front-matter = agent quyết định có mở file hay không mà không phải đọc cả file (giảm token — vấn đề S238).
- Agent ưu tiên **reference máy đọc được** (JSON schema dump, OpenAPI, contracts) hơn văn xuôi; steering đã làm đúng với schema.

**Viết**
- Agent được tạo/sửa docs **trong cùng PR với code**, theo template và `STYLE.md`; skill `writing-for-agents` cho file dành cho agent.
- Agent **không** sửa file GENERATED, **không** sửa nội dung ADR đã Accepted (chỉ đề xuất amendment), **không** đăng docs
  business (tiếng Việt cho chị Thư) mà không qua Nghiệp duyệt — cùng tinh thần quy tắc Jira.
- **Agent chỉ được đặt `last-reviewed` = hôm nay khi đã kiểm nội dung với hệ thống thật** (chạy lệnh verify, đọc file nguồn) và
  ghi bằng chứng trong PR. Nếu không, giữ nguyên ngày cũ. Đây là bẫy lớn nhất của freshness khi có agent: agent sửa một dấu
  phẩy rồi bump ngày → mọi trang "tươi" giả.
- Trang agent viết mới: `status: draft` cho tới khi Nghiệp đọc một lần (giai đoạn Dev có thể duyệt gộp cuối phiên).
- Giữ file hướng dẫn agent **ngắn, chỉ quy tắc + link**; nội dung dài để ở docs/skill (đúng như steering đang làm "sửa steering, không chép").

---

## 6. Trình bày / UX — cái gì làm docs "dễ đọc"

### 6.1 Các yếu tố UX quan trọng (theo thứ tự giá trị)

1. **Search tốt** (full-text, gõ là ra) — quan trọng nhất khi docs > 50 trang.
2. **Sidebar nhất quán + breadcrumb + "On this page" (TOC phải)** — người đọc biết mình ở đâu.
3. **Khung trang cố định** (§3.2) — người đọc biết phần nào ở đâu mà không cần đọc hết.
4. **Code block có nút copy, title file, highlight dòng, diff** — giảm lỗi copy lệnh.
5. **Callout** cho cảnh báo tiền/dữ liệu; **Steps** component cho how-to; **Tabs / code groups** cho biến thể (vd "CLI" vs
   "Console", "acc2" vs "acc3").
6. **Mermaid render tại chỗ**, sơ đồ có thể zoom.
7. **Footer "Last updated" (git) + "Edit this page" + owner** — tăng độ tin (Google SWE: byline review tăng adoption).
8. **Dark mode**, line length ~70–80 ký tự, bảng không quá 6 cột (bảng rộng → tách).
9. **"Copy page as Markdown" / bản `.md` + llms.txt** cho agent (Vercel, Mintlify làm).
10. Feedback "Was this helpful?" — [OVERKILL] với ≤ 2 người đọc.

### 6.2 So sánh tính năng các công cụ

Ghi chú: "built-in" = có sẵn; "plugin" = plugin chính thức hoặc cộng đồng phổ biến; chỉ ghi tính năng, **không** so chi phí host.

| Tính năng | **Astro Starlight** | **Docusaurus 3.10** | **MkDocs Material** | **Mintlify** (SaaS) | **Nextra 4** |
|---|---|---|---|---|---|
| Stack | Astro, Markdown/MDX/Markdoc | React, MDX | Python, Markdown | SaaS, MDX + `docs.json` | Next.js **App Router**, MDX |
| Search | Built-in **Pagefind** (mặc định bật, chạy trong browser, không server) | Algolia DocSearch (chuẩn) hoặc plugin local search | Built-in, chạy trong browser, offline được | Built-in + AI assistant (gói Pro) | Built-in **Pagefind** (chạy ở `postbuild`) |
| Dark mode | Built-in | Built-in | Built-in (palette toggle) | Built-in | Built-in |
| Sidebar tự sinh | `autogenerate: { directory }` (sắp theo tên file) | Autogenerated sidebar | Nav từ thư mục (hoặc khai báo) | Khai báo trong `docs.json` | Từ file system + `_meta.js` |
| Versioning | Plugin `starlight-versions` | **Built-in mạnh nhất** (`docs:version`, `versions.json`, `onlyIncludeVersions`) | `mike` (deploy mỗi version một thư mục) | Có trong navigation config **[cần kiểm]** | Không built-in (deploy riêng mỗi version) |
| OpenAPI → reference | Plugin `starlight-openapi` | Plugin cộng đồng `docusaurus-plugin-openapi-docs` | Plugin cộng đồng (Swagger UI / Neoteroi) | **Mạnh nhất: API playground tương tác** | Không built-in (nhúng Scalar/Redoc) |
| Mermaid | Cộng đồng `astro-mermaid` (render client) | Chính thức `@docusaurus/theme-mermaid` | Built-in qua SuperFences | Built-in | Built-in |
| Callout / Tabs / Steps | Asides (note/tip/caution/danger), Tabs, Steps, Cards built-in | Admonitions, Tabs (đồng bộ `groupId`) built-in | Admonitions, content tabs, **code annotations** (tốt nhất) | Callouts, Tabs, CodeGroup, Steps | Callout, Tabs, Steps, Cards |
| Code block | Expressive Code (title, frame terminal, diff, highlight) built-in | Prism, title, highlight | Pygments, annotations, copy | Copy, CodeGroup | Shiki, copy |
| Edit this page | `editLink.baseUrl` | `editUrl` | `edit_uri` | Có (gợi ý sửa qua git) **[cần kiểm]** | Built-in |
| Last updated (git) | `lastUpdated: true` (mặc định tắt) | `showLastUpdateTime` / `Author` | Plugin `git-revision-date-localized` | **[cần kiểm]** | Built-in |
| i18n | Built-in (`locales`, `defaultLocale`) | Built-in | Built-in UI 60+ ngôn ngữ; nội dung qua plugin | Có | Qua Next.js i18n |
| llms.txt | Plugin `starlight-llms-txt` | Plugin cộng đồng **[cần kiểm]** | Plugin cộng đồng **[cần kiểm]** | Tự sinh + MCP server | Không thấy built-in |
| Link validation | Plugin `starlight-links-validator` | Built-in (`onBrokenLinks`) | Built-in cảnh báo khi build (`validation`) | Có kiểm link CLI **[cần kiểm]** | Không built-in |
| Tình trạng dự án | Hoạt động, nhiều plugin | Hoạt động (3.10.2, 07/2026) | **End of life 05/05/2027**, chỉ bảo trì lỗi nghiêm trọng; kế nhiệm **Zensical** (tương thích dự án MkDocs) | Thương mại | Hoạt động (v4 chỉ App Router) |
| Private/nội bộ | Static → cần lớp auth phía trước host | Static → như trên | Static → như trên | Auth/private docs **tuỳ gói** (Pro ~$450/tháng trả năm) — **cờ chi phí** | Next.js trên Vercel → Deployment Protection **[cần kiểm]** gói |

Nhận xét theo tính năng (không phải quyết định host):
- **Starlight**: cân bằng nhất cho docs nội bộ — đủ tính năng "trông thương mại" sẵn có, plugin phủ đúng các nhu cầu của mình
  (OpenAPI, versions, llms.txt, link validator, sidebar topics), front-matter có schema nên CI bắt lỗi được.
- **Docusaurus**: chọn khi versioning nhiều bản là yêu cầu thật (API public cho tenant) — hiện chưa phải.
- **MkDocs Material**: tính năng viết (admonition, annotation) tốt nhất, hợp team Python, **nhưng EOL 2027** → không chọn mới;
  nếu thích hệ Python thì theo dõi Zensical **[cần kiểm]** độ chín.
- **Mintlify**: đẹp nhất cho API docs public + AI search, nhưng là SaaS trả phí cho private → hợp với docs **đối tác B2B** sau này
  hơn là docs nội bộ.
- **Nextra**: hợp nếu muốn cùng stack Next.js với TripPlanner FE; thiếu versioning/OpenAPI built-in.

---

## 7. Đề xuất cụ thể cho AA_Ecosys

### 7.1 Sitemap đích (IA) — ánh xạ vào file hiện có, không dời ồ ạt

`[có]` = file/thư mục đã tồn tại · `[mới]` = tạo khi có nội dung · `(VI)` = tiếng Việt.

```
docs/README.md                              [mới] Landing: 3 cửa (Engineer · Agent · Business) + "What's new"
docs/llms.txt                               [mới] Index cho agent (định dạng llms.txt)
docs/STYLE.md                               [mới] Style guide 1 màn hình (§4)
docs/_templates/                            [mới] how-to, runbook, concept, reference, postmortem, cost-report, release-note

1. Start here
   docs/get-started/README.md               [mới] Onboarding (template §3.3): access, run, ship 1 change
   docs/get-started/how-we-work.md          [mới] Trỏ: session-workflow, language, aa-ship DoD, lessons
2. Business (VI)  — cho chị Thư
   docs/business/README.md                  [mới] Hệ làm được gì (3 app), trạng thái, ai liên hệ
   docs/business/release-notes/YYYY-MM.md   [mới] Release note tháng (VI)
   docs/business/cost/YYYY-MM.md            → trỏ docs/cost/reports (khối VI ở đầu)
   docs/business/roadmap.md                 [mới] Lấy từ backlog sống, ngôn ngữ kinh doanh
3. Architecture
   docs/ecosystem-architecture.md           [có]  + C4 L1/L2 Mermaid
   docs/architecture/data-standards/        [có]
   docs/apps/{cis,booking,tripplanner,infra}.md  [mới] Landing mỗi app → CONTEXT.md, README, docs/ của repo con
4. Guides (how-to)
   skill/aa-ship/, skill/aa-wave-rerun/      [có]  (skill là how-to cho agent; trang guide chỉ trỏ link)
   docs/db-access-ssm-tunnel.md             [có]  → sau dời docs/guides/
   docs/guides/add-a-new-app.md             [mới] Theo ADR 0008
5. Reference (phần lớn GENERATED)
   docs/architecture/db-schema-reference.md [có, generated]
   docs/contracts/                          [có]
   docs/database/schema-ownership.md        [có]  (gốc: infra db/owners.yaml)
   docs/reference/api/<app>.openapi.json    [mới, generated] trước prod
   docs/reference/aws-accounts.md           [mới] Bản đồ acc1/2/3, profile, region (chuyển từ CLAUDE.md)
   docs/glossary.md                         [mới] Song ngữ EN↔VI
6. Operations
   docs/ops/README.md                       [mới] Index runbook toàn hệ + bảng alarm → runbook
   docs/ops/incident-response.md            [có]
   docs/ops/runbooks/                       [mới] Rollback ECS, restore RDS, rotate secret, queue stuck, LLM cost spike
   docs/ops/postmortems/                    [mới] Theo template SRE
   (repo con) docs/runbooks/                [có ở CIS]
7. Security
   docs/security/README.md                  [mới] IAM/identity tóm tắt → ADR 0004b, 0006/0006a
   docs/security/secrets-register.md        [mới] Chỉ TÊN secret + owner + rotation (AA-878)
8. Cost
   docs/cost/finops.md                      [mới] Quy tắc chi tiêu (gom từ memory: acc3 cho LLM, cost before new service, paid runs subset)
   docs/cost/reports/YYYY-MM.md             [mới] Báo cáo tháng (template §3.3)
9. Decisions
   docs/adr/ (+ README index)               [có]  infra/AA-CIS-Infra/docs/adr/ [mới], apps/*/docs/adr/ [có]
10. Changelog
   docs/changelog.md                        [mới] Link tới CHANGELOG/Release từng repo + ADR mới trong tháng
11. Journal (không phải sự thật hiện hành — gắn nhãn rõ)
   docs/sessions/ backlog/ audits/ research/ implementation-notes/   [có]
   docs/archive/YYYY/                       [mới] Nơi trang deprecated về hưu
```

Lưu ý: theo Diátaxis, **không tạo trước cả cây rỗng**. Chỉ tạo `README.md` của một mục khi mục đó có ≥ 2 trang thật.

### 7.2 Lộ trình

**Tuần 1 — "nền", khoảng 1 ngày công, chỉ Markdown trong repo** [TUẦN 1]
- [ ] `docs/README.md` landing 3 cửa + `docs/llms.txt` + `docs/STYLE.md` + `docs/_templates/` (how-to, runbook, concept, postmortem).
- [ ] Front-matter cho ~10 trang quan trọng nhất: `ecosystem-architecture.md`, 4 `CONTEXT.md`, `incident-response.md`,
      `clean-rerun.md`, `db-access-ssm-tunnel.md`, `schema-ownership.md`, `data-standards/README`.
- [ ] `docs/apps/<app>.md` × 4 (landing trỏ sang repo con) và `docs/ops/README.md` (index runbook).
- [ ] `docs/glossary.md` song ngữ (tách từ README §8) và `docs/business/README.md` (VI, 1 trang).
- [ ] CI root: markdownlint + lychee ở chế độ cảnh báo.
- [ ] Thêm Docs DoD (§5.2) vào `skill/aa-ship/SKILL.md`; gỡ gitignore `docs/` của CIS (README §3.4).
- [ ] Gắn `status: deprecated` cho các file rời đã lỗi thời (§5.4).

**Trước prod** [TRƯỚC PROD]
- [ ] OpenAPI export trong CI cho Booking + CIS, đưa vào `docs/reference/api/`.
- [ ] CHANGELOG (release-please) + template release note VI + `docs/changelog.md`.
- [ ] Runbook cho mỗi alarm (bảng alarm → runbook), template postmortem, ít nhất 1 lần diễn tập restore có ghi lại.
- [ ] `docs/security/` + secrets register (tên only); `docs/cost/finops.md` + báo cáo tháng đầu tiên (gộp việc audit chi phí đầu tháng 11).
- [ ] Script freshness theo lịch tuần (cảnh báo, không chặn); review docs quý đầu tiên.
- [ ] CODEOWNERS cho `docs/adr/`, `docs/ops/`, `docs/security/`, `infra/**` khi bỏ chế độ agent tự merge.
- [ ] Nếu chọn site (theo kết quả agent so sánh host): dựng site từ cấu trúc trên — front-matter đã tương thích, sidebar autogenerate,
      Mermaid, edit link, last-updated, llms.txt plugin.

**Sau này** [SAU NÀY]
- [ ] C4 bằng Structurizr; Vale lint văn phong (cảnh báo); `terraform-docs`; export job kinds/LLM routes như schema dump.
- [ ] Trang orphan check; `AGENTS.md` nếu dùng thêm agent khác.
- [ ] Docs public cho tenant/đối tác B2B (site riêng, có thể Mintlify/Starlight) — tách hẳn docs nội bộ.

**Overkill bây giờ** [OVERKILL] — không làm tới khi có team/người đọc ngoài
- Versioned docs site (dropdown version); i18n toàn site; Backstage/portal; analytics search misses và feedback widget;
  CODEOWNERS nhiều người; API playground tương tác cho docs nội bộ; Vale ở chế độ chặn merge; dashboard docs metrics;
  quy trình docs review riêng ngoài PR.

---

## 8. Nguồn

- Stripe — Markdoc: https://stripe.dev/blog/markdoc
- Vercel Docs (landing + bản Markdown có front-matter): https://vercel.com/docs
- GitLab Handbook — handbook-first: https://handbook.gitlab.com/handbook/company/culture/all-remote/handbook-first/
- GitLab handbook CODEOWNERS (MR gỡ owner cũ): https://gitlab.com/gitlab-com/content-sites/handbook/-/merge_requests/20577
- GitLab Code Owners: https://docs.gitlab.com/17.6/user/project/codeowners
- GitLab Docs topic types: https://docs.gitlab.com/development/documentation/topic_types/
- Diátaxis: https://diataxis.fr/ · How to use: https://diataxis.fr/how-to-use-diataxis/
- Software Engineering at Google, ch.10 Documentation: https://abseil.io/resources/swe-book/html/ch10.html
- Google developer documentation style guide — highlights: https://developers.google.com/style/highlights
- Microsoft Writing Style Guide — top 10 tips: https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice
- AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html
- Write the Docs — Docs as Code: https://www.writethedocs.org/guide/docs-as-code/
- Backstage TechDocs: https://backstage.io/docs/features/techdocs/
- Atlassian — Confluence knowledge management best practices: https://www.atlassian.com/software/confluence/resources/guides/best-practices/knowledge-management
- Atlassian Community — page tree best practices: https://community.atlassian.com/forums/Confluence-articles/Best-practices-for-a-great-page-tree-experience/ba-p/2486271
- The Good Docs Project templates: https://www.thegooddocsproject.dev/template
- Google SRE — example postmortem: https://sre.google/sre-book/example-postmortem/
- C4 model: https://c4model.com/ · Mermaid C4 (experimental): https://mermaid.js.org/syntax/c4.html
- llms.txt: https://llmstxt.org/ · AGENTS.md: https://agents.md/
- Astro Starlight: https://starlight.astro.build/ · config: https://starlight.astro.build/reference/configuration/ · plugins: https://starlight.astro.build/resources/plugins/
- Docusaurus: https://docusaurus.io/docs · versioning: https://docusaurus.io/docs/versioning
- Material for MkDocs (EOL 05/05/2027, Zensical): https://squidfunk.github.io/mkdocs-material/ · https://zensical.org/
- Mintlify: https://www.mintlify.com/docs · pricing: https://www.mintlify.com/pricing
- Nextra: https://nextra.site/docs · search (Pagefind): https://nextra.site/docs/guide/search
- Monzo engineering principles (không phải handbook): https://monzo.com/blog/2018/06/29/engineering-principles
