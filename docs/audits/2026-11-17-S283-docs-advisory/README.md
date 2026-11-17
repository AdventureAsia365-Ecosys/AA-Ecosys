---
id: CAT-00-docs-advisory-s283
title: Docs-as-code and /admin/docs advisory (S283)
description: Advisory for the tech lead after the S283 docs audit - how to keep docs in sync with code across six repos, how to version docs, where DVC fits, and how to make /admin/docs read like a market docs site.
type: report
status: draft
owner: tech-lead
audience: [cto, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-17
related: [CAT-00, CAT-00-docs-audit-s283, AA-1118, AA-1124]
---

# Tư vấn: docs-as-code và trang /admin/docs (S283)

Ngày 17/11/2026 (S283). Tác nhân: Claude Code (3 lane nghiên cứu, chỉ đọc). Viết cho tech lead.
Chi phí lập báo cáo: 0 USD. Không có account ID, ARN, ID tài nguyên, e-mail hay tên người trong file này.

Bằng chứng gốc: audit tài liệu cùng ngày `docs/audits/2026-11-17-S283-docs-audit/README.md` (+ `rows.json`,
`tom-tat.vi.md`). Câu hỏi cần quyết ở mục 5 có bản máy đọc `decisions.json` (gộp vào trang duyệt cuối phiên).

Giới hạn: chưa chụp ảnh /admin/docs (không có phiên đăng nhập E2E trong lane), nên phần giao diện được đánh giá từ code.
Ảnh chụp sẽ làm trong đợt audit giao diện cuối phiên.

---

## 1. Tóm tắt 5 dòng

1. **Giữ docs-as-code (Git là nguồn duy nhất), nhưng đổi cách đo "cũ":** đo theo *thay đổi code*, không theo lịch. Hôm nay báo cáo freshness nói "0 trang quá hạn" trong khi audit thấy 24 trang sai, 222 trang lệch.
2. **Bốn cơ chế chính, đều 0 USD/tháng:** (a) lint cụm từ đã bỏ, quét cả file chỉ dẫn agent; (b) khối sinh tự động từ code cho các sự thật hay lặp (account/route LLM, service ECS, migration, job kind, required checks); (c) cổng "docs impact" trên PR của cả 6 repo, dựa vào bản đồ docs↔code; (d) cờ "code đổi sau lần review" hiện thẳng trên trang đọc.
3. **"Kiểm soát phiên bản docs" = Git, đã đủ.** Thiếu là *hiện* lịch sử ra cho người đọc: "Cập nhật ngày …", lịch sử commit từng trang, trang "Docs đã đổi gì". **Công cụ DVC (Data Version Control) không dùng cho docs**, và chưa cần cho dữ liệu: chỉ bật khi bộ eval/golden xuất ra file vượt ~50 MB hoặc chứa văn bản tenant.
4. **/admin/docs: nâng cấp reader hiện có, không nhúng Fumadocs, không dựng site riêng, không mua SaaS** ($250–540+/tháng). Reader đã có sẵn phân quyền Cognito, tầng owner, guard che ID: chỉ thiếu trang chủ, sidebar theo chủ đề, tìm toàn văn, bố cục 3 cột + mục lục dính, nút copy code, banner độ tin cậy, lịch sử, phản hồi.
5. **Lộ trình ~15–20 ngày-agent chia lát PR:** làm ngay trong AA-1118 phần lint cụm từ đã bỏ + docs-lint cho CIS + sửa lỗi badge ADR; mở 2 issue mới ("Docs sync engine" và "Docs reader v2") nếu tech lead đồng ý (mục 5).

---

## 2. Docs-as-code

### 2.1 Vì sao 24 trang sai lọt qua quy trình hiện tại

Quy trình hiện có không tệ: front-matter + schema, `docs-lint.yml` với ~12 kiểm tra, publish tự động lên S3, vài trang
sinh tự động (`db-schema-reference.md`, `docs/generated/*`). Nhưng audit cho thấy 7 lỗ hổng:

| # | Lỗ hổng | Bằng chứng |
|---|---|---|
| 1 | **Độ tươi đo theo lịch, còn sai lệch đến từ thay đổi.** Kiểm tra chỉ là `last_reviewed + review_every_days` (mặc định 90 ngày), chạy tuần một lần, chỉ cảnh báo, kết quả nằm trong run summary nên không ai đọc. | `check_frontmatter.py --freshness-report`: 319 trang, **0 quá hạn**. 8 thay đổi gây sai lệch đều < 4 tuần tuổi. `docs/README.md` (CAT-00) vẫn ghi "Model calls run on Bedrock in acc3; acc1 is no longer part of the ecosystem", chưa quá hạn nên không bị báo. |
| 2 | **Ngày review không chứng minh trang đúng.** | 120 trang sai/lệch có `last_reviewed` trong 30 ngày gần nhất. |
| 3 | **Docs và code ở khác repo.** Trang ở repo gốc mô tả hành vi của CIS, Booking, Infra; PR code ở repo con không sửa được trang gốc trong cùng PR, và không có gì báo cho repo gốc. | 314/401 bản ghi audit nằm ở repo gốc. PR template của CIS/Booking/Partner có checklist docs nhưng chỉ cho docs cùng repo và không ai kiểm. |
| 4 | **Một sự thật bị chép ra nhiều trang.** Một quyết định đổi → N trang phải sửa, không ai thấy hết N. | Route acc1/acc3 ~100 câu trên 70 trang; tên/số service ECS ~98 câu/68 trang; số migration ~150 câu/88 trang; job kind 49 câu. |
| 5 | **File chỉ dẫn agent không được coi là docs.** `CLAUDE.md`, `.kiro/steering`, `skill/**`, `.claude/agents`, `CONTEXT.md` không có front-matter nên không vào kiểm tra độ tươi. | 126 file sai/lệch không có front-matter; **16/35 lỗi cao** nằm ở đây, mà chúng được nạp vào mọi phiên. |
| 6 | **Cụm từ đã bỏ quay lại.** Lint "retired phrase" đề xuất từ S282 chưa làm. | Audit §4.1. |
| 7 | **Người đọc không có tín hiệu nào.** Reader hiển thị mọi trang như nhau; 134/205 trang mang `draft` nên chữ "draft" mất nghĩa. | Manifest không có trường cờ cũ; ADR 0001a vẫn hiện "accepted" dù Note S278 đã đảo ngược. |

Hai lỗ hổng phụ kiểm được hôm nay:

- **AA-CIS-App không có `docs-lint.yml`** (Booking, Partner, TripPlanner, Infra đều có bản vendored). CIS có 31 trang được audit, 5 trang sai.
- **PR template CIS tự lỗi thời:** vẫn ghi "`docs/` is gitignored" (đã track từ AA-889; `.gitignore` hiện không còn dòng đó) và liệt kê 7 check thay vì 10.

**Kết luận:** docs-as-code không thất bại; vòng lặp chưa khép. Nguyên tắc sửa: **mỗi sự thật có đúng một nguồn; mọi chỗ
khác hoặc được sinh ra, hoặc được kiểm với nguồn, hoặc chỉ link tới nguồn.** Văn xuôi giải thích "vì sao", không chép số
và tên.

### 2.2 Cơ chế đề xuất theo lớp

Mọi lớp dùng stack sẵn có (tool Python trong `tools/docs/`, GitHub Actions trên repo public nên phút chạy miễn phí,
bundle S3 hiện tại). Chi phí AWS thêm: dưới 0,1 USD/tháng.

| Lớp | Làm gì | Chặn được lỗi nào trong audit hôm nay | Công sức | Chi phí/tháng |
|---|---|---|---|---|
| **L1. Lint cụm từ đã bỏ** | File `docs/catalogue/retired.yaml`: mỗi dòng = cụm từ, thay bằng gì, bỏ từ ADR/issue nào, chỗ được phép giữ (ADR giữ lịch sử, log phiên bỏ qua). Lệnh mới `check_docs_text.py retired` quét `docs/`, `skill/`, `.claude/`, `.kiro/steering/`, và `CONTEXT.md`/`.claude/` của các repo con. **Lỗi trên dòng mới (theo diff), cảnh báo trên dòng cũ** để không chặn mọi PR ngay. **Quy tắc đi kèm:** PR nào ghi quyết định bỏ một thứ (ADR amendment, dời Terraform) phải thêm cụm từ vào `retired.yaml` trong cùng PR. | Cả 8 nhóm thay đổi của audit: "acc3 only"/"acc1 retired", B2C, "Vercel preview", `portal/`, `aa-crm-dev-portal`, `bk_inquiry_pull`, "7-day PITR", "private repo", `accounts/aa365/booking.tf`. | S (~0,5 ngày + vendor sang 5 repo) | 0 |
| **L2. Khối sinh tự động từ code** | `docs/generated/facts.snapshot.json` do job đêm có sẵn làm mới (catalogue job đã checkout 4 repo app; `docs-gen.yml` của Infra đọc Terraform; `gh api` cho visibility và required checks). Quyết định do người chốt (vai trò account, thứ tự route LLM) ở `docs/catalogue/platform.yaml`, chỉ dùng nhãn, không ID. Trong trang viết tay đặt khối đánh dấu `<!-- gen:ecs-services -->…<!-- /gen -->`; tool `gen_sections.py` render khối thành Markdown thường (đọc trên GitHub vẫn đẹp). `--check` chạy trong docs-lint (khối lệch → PR đỏ); `--write` chạy trong bot PR đêm, tự merge khi chỉ đổi snapshot + khối (giống `bot/db-schema-reference`). Không dùng token kiểu `{{fact:x}}` vì GitHub sẽ hiện nguyên token. | Nhóm câu lớn nhất: số migration ~150, route account ~100, service ECS ~98, job kind 49 (biến `docs/ops/job-kinds.md` thành bảng sinh), required checks 16, phiên bản app 11, số ngày backup 16. | M–L (2–3 ngày: engine + 6 khối đầu) | 0 |
| **L3. Cổng "docs impact" trên PR** | `docs/catalogue/doc-map.yaml` ở repo gốc (public): `<repo>:<glob>` → các trang mô tả nó. Seed từ cột bằng chứng trong `rows.json` (mỗi câu lỗi thời đã chỉ ra file code gốc). Tool `doc_impact.py --base <ref>` + workflow tái sử dụng `AA-Ecosys/.github/workflows/docs-impact.yml@<sha>` gọi từ cả 6 repo (đọc map qua raw GitHub, không cần secret). PR chạm file được theo dõi → 1 comment cố định "Docs impact: …" và thân PR phải có dòng `Docs-impact: <link root PR> \| updated-here \| none: <lý do>`. **2 tuần chỉ cảnh báo, sau đó thành check bắt buộc** trong merge queue CIS/Booking/Partner và ruleset Infra. Job đêm liệt kê các lời hứa `Docs-impact` mà root PR chưa merge sau 3 ngày vào `docs/generated/docs-debt.md` (không tạo Linear, giữ quota). | Sai lệch xuyên repo: Terraform dời sang `modules/environment/` (69 câu, gồm địa chỉ sai trong runbook `crm-keys`, `secret-rotation`), portal gộp vào CRM web (30), job kind đổi ở `kinds.py`. | M (1,5–2 ngày + duy trì map) | 0 |
| **L4. Độ tươi theo sự kiện** | Trang/khối khai báo phụ thuộc (glob trong doc-map hoặc khoá fact). Khi phụ thuộc đổi sau `last_reviewed` → manifest đánh dấu `needs_review` kèm danh sách commit; reader hiện banner (mục 3). File không có front-matter (agent files, `CONTEXT.md`) đăng ký trong sổ phụ `docs/catalogue/doc-owners.yaml` (đường dẫn, vai trò chủ, `last_reviewed`, chu kỳ) để vào báo cáo độ tươi. Lịch vẫn giữ làm lưới an toàn nhưng rút ngắn theo loại: agent files/steering 30 ngày, runbook 60, explanation 180. Chỉ được tăng `last_reviewed` khi thân PR có dòng `Verified:` hoặc trang không còn thay đổi chờ. | 126 file "vô hình" không front-matter; khoảng trống "0 quá hạn" so với 24 sai; 120 trang review gần đây nhưng vẫn lệch. | M (~1 ngày) | 0 |
| **L5. Kiểm tra danh tính trong backtick** | Đường dẫn repo phải tồn tại; địa chỉ `-target=`/`-replace=` phải có trong danh sách địa chỉ Terraform đã che; tên service, job kind, settings key phải có trong facts; số migration không được mới hơn migration mới nhất; tên workflow/check phải tồn tại. | Lệnh Terraform sai trong runbook (`crm-keys`, `secret-rotation` báo "No changes" giả); 22 câu trạng thái ADR; tên service cũ. | M (~1 ngày) | 0 |
| **L6. Luật cho agent** | `skill/aa-ship` dòng Docs → "check docs-impact xanh; `none:` chỉ khi đúng". Brief lane (`kiro-delegate/brief-template.md`, `aa-session`) có mục "Docs impact" điền sẵn từ `doc_impact.py`. Hook `pre-push` chạy `doc_impact.py` ở chế độ cảnh báo. Cuối phiên: chạy lint cụm từ đã bỏ + danh sách docs-debt, ghi vào state snapshot. File `~/.claude/CLAUDE.md` toàn cục nằm ngoài repo nên CI không kiểm được: thêm bước đầu phiên so khối account/service với facts và báo lệch. | Thói quen "sửa code quên docs" của chính agent; 16 lỗi cao ở file agent. | S (~0,5 ngày) | 0 |
| **L7. Vá nhanh** | Thêm `docs-lint.yml` vendored vào AA-CIS-App; sửa PR template CIS (bỏ câu gitignored, đúng số check); sửa `_adr_meta` để badge ADR không còn `accepted**`; đưa báo cáo độ tươi hằng tuần vào manifest thay vì chỉ run summary. | 5 trang sai của CIS; badge xám `accepted**` ở ADR 0009, 0019, 0020, 0021, 0022. | XS | 0 |

**Thứ tự giá trị/công sức:** L7 → L1 → L2 → L3 + L6 → L4 → L5. Các đợt sửa 6–7 của AA-1118 (viết lại trang lớn) nên
chạy **sau** L2, để trang viết lại dùng khối `gen:` thay vì chép tay, nếu không sai lệch sẽ quay lại.

**Còn một việc về nội dung:** `CONTEXT.md` quá dài (CIS 5.242 dòng, Partner 3.429, Booking 2.428) là "nam châm" hút sai lệch.
Tách lõi ≤ ~400 dòng (ranh giới, ownership, stack) + file theo vùng dưới `docs/context/`; danh sách dài (endpoint,
migration, kind) thay bằng khối sinh. Việc tách CIS `CONTEXT.md` đã có trong AA-1118.

**Không dùng Vale:** Vale (MIT, miễn phí) làm được lint cụm từ, nhưng `check_docs_text.py` đã vendored ở mọi repo; thêm một
công cụ nữa không lời.

### 2.3 Kiểm soát phiên bản docs

Hiểu "kiểm soát DVC" là **kiểm soát phiên bản tài liệu**: Git đã giữ mọi phiên bản, PR review là kiểm soát thay đổi, và S3
chỉ là bản dẫn xuất (mất S3 thì publish lại từ Git). Không cần thêm hệ thống lưu trữ. Việc còn thiếu là **cho người đọc
thấy lịch sử**:

1. **Lịch sử từng trang trong manifest.** `docs-sync.yml` đổi checkout sang `fetch-depth: 0` + `filter: blob:none`
   (clone không blob, vẫn nhanh). `build_docs_reader.py` thêm `last_changed {sha, date, pr}` và `history` (10 commit
   gần nhất: ngày, tiêu đề, số PR). Reader hiện "Cập nhật 3 ngày trước · PR #843 · Lịch sử (8)".
2. **Link "Xem nguồn / Lịch sử / Sửa trên GitHub"** cho trang tầng staff, trong lúc repo gốc còn public (ADR 0014 nói là
   tạm thời). Build đọc visibility qua `gh api` và tự ẩn link nếu repo chuyển private.
3. **Trang "Docs đã đổi gì"** sinh hằng tuần từ `git log -- docs/` (định dạng commit `docs: … / Refs AA-xxx` đã đủ dễ
   đọc), cộng dấu chấm "đổi từ lần bạn xem trước" (mốc lưu trong localStorage, chỉ là tiện ích riêng người xem).
4. **Gắn docs với bản phát hành:** manifest ghi phiên bản app lúc build (từ `.release-please-manifest.json`); reader có
   mục "Release notes" lấy `CHANGELOG.md` của từng app.
5. **Quay lui một lần publish lỗi:** giữ `manifest.previous.json` trên S3 (giống mẫu `previous.json` của ERD). Dưới 0,01 USD/tháng.
6. **Không làm bộ chọn phiên bản kiểu Docusaurus (v1/v2):** chỉ có một môi trường Dev, không khách nào bị ghim vào bản cũ;
   chính Docusaurus khuyên chỉ dùng khi có nhiều bản phát hành cùng được hỗ trợ. Xem lại khi có prod chạy khác bản với
   Dev, hoặc khi đối tác ngoài dùng API/SDK có phiên bản (hợp đồng API đã có phiên bản trong `docs/contracts/`).

### 2.4 Công cụ DVC (Data Version Control): dùng ở đâu, không dùng ở đâu

DVC (dvc.org, Apache-2.0, miễn phí) để file con trỏ `.dvc` trong Git, dữ liệu thật trên S3. Nó dành cho dữ liệu lớn,
không phải Markdown.

- **Docs: không dùng.** Markdown trong Git đã có phiên bản, diff, review; DVC chỉ thêm bước `dvc pull` cần credential + MFA.
- **Dữ liệu hiện tại: chưa cần.**
  - Golden set eval đã có phiên bản trong DB (migration CIS `284_eval_golden_set.sql`, `400_eval_golden_split.sql`, CLI bump golden).
  - File dữ liệu nhỏ: `docs/eval` 4,5 MB, `docs/calibration` của CIS 1,1 MB, case Q0 72 KB.
  - Ảnh bằng chứng audit được track: ~39 MB (3.140 PNG), đã kiểm hôm nay; phần lớn 592 MB trên đĩa là file chưa track.
    Bước rẻ hơn DVC: mở rộng cổng ảnh hiện có (`check_images.py`, 300 KB, WebP) sang file mới dưới `docs/audits/`.
- **Khi nào bật DVC** (S3 remote ở prefix private trên acc2, vài cent/tháng): (1) một bộ eval/calibration xuất ra file
  vượt ~50–100 MB hoặc là nhị phân (embedding, media); (2) chạy calibration cần tái lập như pipeline (`dvc.yaml` + params);
  (3) bộ dữ liệu chứa văn bản tour/tenant, vì repo public nên không được vào Git.
- **Tạm thời ("DVC-lite"):** khi cần xuất một bộ dữ liệu, ghi lên S3 kèm manifest sha256 commit vào Git, theo mẫu
  `latest.json`/`previous.json` của ERD. Không thêm công cụ.

---

## 3. Trang /admin/docs

### 3.1 Hiện trạng

Code: `apps/AA-CIS-App/frontend/app/admin/docs/page.tsx`, `DocsList.tsx`, `lib/docsReader.ts`, `lib/docsGroups.ts`,
`app/_kit/MarkdownView.tsx`; API `api/routers/admin_docs.py`, `api/services/docs_reader.py`. Nội dung: 205 mục
(171 EN, 34 VI) chỉ từ repo gốc, ~3,3 MB văn bản.

**Điểm mạnh (giữ nguyên):**

- Kiến trúc đúng chuẩn Backstage TechDocs: CI build → S3 → backend phục vụ có phân quyền. Docs merge là lên trang trong
  vài phút, không cần deploy admin.
- Bảo mật: phiên Cognito, tầng owner kiểm ở server, guard che ID khi build, CSP cho ảnh, Markdown an toàn (bỏ HTML thô),
  Mermaid chế độ strict đã sanitize.
- Có sẵn: callout kiểu GitHub, Mermaid (38 khối), ảnh SVG/PNG/WebP, chuyển EN/VI nhớ theo trình duyệt, lọc theo loại
  Diátaxis và đối tượng, URL `?path=` chia sẻ được, dark mode theo kit, điện thoại dùng được (danh sách ↔ trang).

**Điểm yếu (theo mức ảnh hưởng tới người dùng):**

1. **Không có trang chủ.** Vào trang là ô trống "Select a page"; bảng "Start here by role" của CAT-00 và 6 guide theo vai
   trò không được dùng.
2. **Điều hướng theo thư mục, không theo chủ đề.** 24 nhóm tên thư mục viết hoa (`ADR`, `OPS/RUNBOOKS`,
   `ARCHITECTURE/ERD/DESIGN`) đánh số 1, 1.1…; không breadcrumb, không trước/sau, không trang liên quan.
3. **Tìm kiếm yếu.** Chỉ khớp chuỗi con trên tiêu đề/id/đường dẫn/mô tả; không tìm thân trang, không chịu gõ sai, không
   snippet, không nhảy tới heading; ⌘K của admin không có nhóm Docs.
4. **Bố cục chật.** Menu admin + danh sách 260–320 px + nội dung = 3 cột, không còn chỗ cho mục lục; mục lục là hộp
   `<details>` đóng sẵn phía trên, không dính, không scroll-spy; danh sách cuộn trong hộp `calc(100vh - 330px)`.
5. **Code block trơn.** Không nút copy, không nhãn ngôn ngữ, không tô màu; runbook toàn lệnh AWS CLI một dòng nên đây là
   chỗ mất thời gian nhất.
6. **27% link nội bộ dẫn vào ngõ cụt** (616/2.314), nhiều nhất `docs/templates` (149), `docs/audits` (110), `skill/` (54);
   heading không có link neo.
7. **Đầu trang thiên về kỹ sư.** Dòng mono `id · path · last reviewed · for <audience>` đứng đầu; `description` có trong
   manifest nhưng không hiện; `owner`, `related`, `superseded_by`, `last_tested` không hiện.
8. **Không có tín hiệu tin cậy.** Không "cập nhật lúc", không lịch sử, không cờ "code đã đổi", không phản hồi. Lỗi:
   badge `accepted**` (ADR 0009, 0019–0022); ADR 0001a không có dấu "đã bị Note S278 đảo ngược".
9. **Chỉ vai trò `admin` mở được** (`frontend/lib/rbac.ts:127`), nên guide viết cho content lead / customer success
   (`audience: staff`) không tới được người đọc của nó.
10. **Chỉ có docs repo gốc;** `CONTEXT.md`, ADR, runbook của app/Infra không có trong reader dù manifest đã có trường `repo`.

### 3.2 Mẫu từ các trang docs trên thị trường

Đã đối chiếu HTML thật (17/11/2026) của Stripe, Vercel, Supabase, Docusaurus, Starlight, Nextra, Mintlify, Fumadocs,
cộng Backstage TechDocs và khung Diátaxis. Những gì gần như trang nào cũng có:

| Mẫu | Ai có | Reader AA hiện có? |
|---|---|---|
| Trang chủ theo vai trò / nhiệm vụ | Stripe, Supabase, Mintlify, Diátaxis | Không |
| Ô tìm ⌘K toàn văn, chịu gõ sai, nhảy tới mục | Tất cả | Chỉ tiêu đề |
| Bố cục 3 cột: sidebar · nội dung · "On this page" dính có scroll-spy | Tất cả | Không |
| Breadcrumb + Trước/Tiếp | Docusaurus, Starlight, Vercel, Mintlify, Fumadocs | Không |
| "Cập nhật lúc …" + "Sửa trang này" + lịch sử | Docusaurus, Starlight, Nextra, Supabase | Chỉ sha bundle |
| Nút copy code + tô màu cú pháp | Tất cả | Không |
| "Trang này có ích?" + báo lỗi | Stripe, Vercel, Supabase, Nextra, Backstage | Không |
| "Copy page as Markdown" cho agent / LLM | Vercel, Supabase, Mintlify, Stripe (`.md`) | Không (đã có `docs/llms.txt`) |
| Callout, Mermaid, dark mode, chọn ngôn ngữ | Tất cả | **Có** |
| Ask AI | Stripe, Vercel, Supabase | Không (để sau, tốn tiền theo lượt) |
| Bộ chọn phiên bản | Docusaurus | Không cần (mục 2.3) |

### 3.3 Ba phương án

- **A. Nâng cấp reader hiện có** (react-markdown + remark-gfm + Mermaid + kit `_kit`), vay mẫu từ Fumadocs/Docusaurus.
- **B. Nhúng framework mã nguồn mở vào admin** (Fumadocs 16, MIT; tương thích Next 16 / React 19.2 / Tailwind v4 của CIS).
- **C. Site docs riêng tự host** (Starlight hoặc Docusaurus build tĩnh, đặt sau ALB + Cognito hoặc CloudFront + Lambda@Edge).
- (Để so sánh: **D. SaaS** Mintlify / GitBook / ReadMe.)

| Tiêu chí | A. Nâng reader | B. Fumadocs trong admin | C. Site riêng | D. SaaS |
|---|---|---|---|---|
| Trải nghiệm đọc sau khi làm xong | Ngang thị trường cho các mẫu ở 3.2 | Rất tốt ngay từ đầu | Rất tốt ngay từ đầu (Pagefind, edit, prev/next) | Rất tốt |
| Công sức | ~8–12 ngày-agent, chia 4 đợt | ~6–10 ngày di chuyển + nâng cấp theo mỗi major Next | ~3–5 ngày + hạ tầng auth | ~2–3 ngày + nhập nội dung |
| Chi phí/tháng | **0 USD** | 0 USD license | ~5–10 USD (ECS Fargate ARM nhỏ, hoặc CloudFront + Lambda@Edge; ước tính, cần kiểm bằng pricing CLI) | $250–540+ (Mintlify Pro $450–540; GitBook Ultimate $249 + $12/người; ReadMe Pro $250; SSO chỉ ở gói Enterprise) |
| Phân quyền / tầng owner | Có sẵn, kiểm ở server | Loader cache một cây trang chung → trang owner cần cây theo request hoặc 2 nguồn, dễ sai | Đăng nhập thứ hai; tầng owner cần build/site riêng | Mật khẩu chung hoặc SSO đắt; docs pháp lý nằm ở vendor |
| Nội dung runtime từ S3 (không deploy) | Giữ | Được (dynamic source) nhưng mất thế mạnh MDX; MDX runtime chạy code nên vẫn phải giữ Markdown thuần | Mất: mỗi lần đổi docs là một lần build site | Đồng bộ qua Git của vendor |
| Hợp kit UI (ADR 0016, "consistent, not one-off") | Hợp hoàn toàn | **Không:** Fumadocs UI mang design system riêng cạnh `_kit` | Giao diện riêng, ngoài admin | Giao diện vendor |
| Rủi ro | Phải tự làm từng mẫu; giữ phạm vi | Hai hệ giao diện, lỗi phân quyền theo tầng, churn nâng cấp | Thêm dịch vụ + bề mặt tấn công, lặp guard che ID | Chi phí, dữ liệu ra ngoài, khoá vendor |

**Khuyến nghị: phương án A.** Lý do ngắn: 0 USD, giữ một chỗ đăng nhập và một guard bảo mật, docs vẫn lên trang trong vài
phút không cần deploy, đúng luật kit. Chỉ vay ý tưởng của Fumadocs (mục lục kiểu "clerk", popover mục lục trên màn hẹp,
footer trước/sau, popover "View options"). Xem lại C chỉ khi phải cho người **không có tài khoản admin** đọc docs.

**Danh sách nâng cấp (theo thứ tự ưu tiên):**

| # | Thay đổi | Ghi chú kỹ thuật | Cỡ |
|---|---|---|---|
| 1 | **Đầu trang thân thiện:** breadcrumb, H1, `description` làm đoạn dẫn, hàng meta (loại, trạng thái, vai trò chủ, Reviewed, Updated theo Git, thời gian đọc, "Có bản VI"); `id`/`path` dời vào popover "Thông tin trang"; sửa badge `accepted**`; `draft` chỉ hiện là ghi chú nhỏ "Chưa được duyệt" | Root: `_adr_meta`, thêm `description`/`owner`/`related`/`superseded_by` vào `_entry()` | S |
| 2 | **Code block:** nút Copy, nhãn ngôn ngữ, tô màu cho ~8 ngôn ngữ (bash, python, sql, hcl, yaml, json, ts, diff); **link neo `#`** trên h2/h3 copy `?path=…#doc-slug` | Shiki (MIT) nạp lười, theme lấy từ token kit | S |
| 3 | **Banner tin cậy:** "Code trang này mô tả đã đổi ngày … (n commit) sau lần review" (từ L4); "Quá hạn review n ngày"; "Đã bị thay bởi …"; tạm thời: "Có lỗi đã biết, đang sửa trong AA-1118" lấy từ `rows.json` | Trường mới trong manifest; UI dùng callout kit | S |
| 4 | **Trang chủ Docs:** thẻ theo vai trò (business owner, tech lead/CTO, CIO, DevOps, PM, kỹ sư mới, staff), thẻ theo nhiệm vụ ("Có sự cố", "Ship một thay đổi", "Onboard", "Yêu cầu dữ liệu/pháp lý" – tầng owner), "Mới cập nhật", "Cần review" | Kit cards; ngày từ lịch sử Git | S |
| 5 | **Link:** publish `docs/templates` (149 link chết); đích public khác (`skill/`, `.github/`, `tools/`, repo app) mở GitHub tab mới có icon ngoài; audit/security/log giữ là chữ | Root: luật publish + resolver | S |
| 6 | **Sidebar theo chủ đề:** Bắt đầu · Guide theo vai trò · Vận hành (runbook/playbook/drill) · Kiến trúc & quyết định · Tham chiếu (sinh tự động, ERD, API) · Pháp lý & bảo mật · Mẫu; tên đọc được thay slug thư mục; bỏ đánh số 1.1; sidebar dính, cuộn riêng | `docs/sidebar.yaml` + lint "mỗi trang publish xuất hiện đúng một lần" (mục 5, câu 4) | M |
| 7 | **Bố cục 3 cột ≥1280 px:** menu admin tự thu về icon ở /admin/docs; sidebar docs · nội dung rộng 680–760 px (~72–80 ký tự/dòng, chữ 15–16 px) · "Trên trang này" dính có scroll-spy. Dưới 1280 px mục lục là popover | IntersectionObserver, không thêm thư viện | S–M |
| 8 | **Tìm kiếm toàn văn + nhóm Docs trong ⌘K**, phím `/` để focus; kết quả "Trang › Mục" có đoạn trích tô đậm, bỏ dấu để gõ tiếng Việt không dấu vẫn ra | Đề xuất: SQLite FTS5 trong bộ nhớ ở CIS API (thư viện chuẩn Python, `unicode61 remove_diacritics` + bảng trigram, `bm25()`, `snippet()`), dựng từ bundle đã cache, lọc tầng ở server. Phương án khác: index tách theo tầng + MiniSearch ở trình duyệt (mục 5, câu 5) | M |
| 9 | **Cuối trang:** Trước/Tiếp theo sidebar; "Liên quan" (từ `related`) + "Trang link tới đây"; "Xem nguồn · Lịch sử · Sửa trên GitHub" (tầng staff); **"Trang này có ích? Có / Không + Báo lỗi"** lưu vào một bảng nhỏ của CIS, trang admin liệt kê trang bị "Không" nhiều nhất | Một migration CIS (ship trong PR app theo ADR 0017), cần review vì là migration | S–M |
| 10 | **Sơ đồ/ảnh:** bấm để phóng to toàn màn hình, kéo/zoom cho Mermaid, SVG, ERD | | S |
| 11 | **Điện thoại:** thanh trên dính (Quay lại, tiêu đề, nút Mục lục, nút Tìm); mục lục dạng bottom sheet; tìm kiếm toàn màn hình; Trước/Tiếp cuối trang | | S |
| 12 | **Mở reader cho mọi vai trò staff** (tầng owner/staff vẫn kiểm ở server); trang chủ mở đúng thẻ theo vai trò | `rbac.ts:127` + quyền backend; quyết định trước (mục 5, câu 1) | XS |
| 13 | **Docs của app/Infra + "Luật cho agent":** công tắc trên đầu "Ecosystem · CIS · Booking · Partner · TripPlanner · Infra · Agent rules"; publish `CONTEXT.md`, ADR app, runbook app, `CHANGELOG.md` với cùng guard che ID | Dùng lại checkout `_ext/<repo>` của learn bundle | M |
| 14 | Thêm sau: "Copy trang dạng Markdown" (cùng tầng, không lộ thêm), thẻ hover thuật ngữ từ `docs/glossary.md` (A0–A4, T0–T11, atom…), stylesheet in / lưu PDF | | S mỗi mục |
| — | Không làm bây giờ: Ask AI (tốn tiền theo lượt qua gateway; chỉ làm khi có đồng ý riêng kèm chi phí tháng), bộ chọn phiên bản | | — |

### 3.4 Phác thảo bố cục

**Desktop ≥1280 px, trang đọc** (menu admin thu về icon ở cột trái ngoài cùng):

```
+----+------------------+---------------------------------------------+------------------+
| ## | Docs  [Ecosystem v]   [ Tìm trong tài liệu...          / ]      EN | VI    (o) Tôi|
|    +------------------+---------------------------------------------+------------------+
| ic | Bắt đầu          | Docs > Vận hành > Runbook                   | TRÊN TRANG NÀY   |
| on | Guide theo vai trò                                             |  Khi nào dùng    |
| s  | v Vận hành       | Rollback một service ECS                    |  Chuẩn bị        |
|    |   Runbook        | Đưa service về task definition trước        | > Các bước       |
|    |   > Rollback ECS | trong 5 phút.                               |  Kiểm tra sau    |
|    |     5xx spike    | How-to . Active . Tech lead . Reviewed 10/11|                  |
|    |     DB restore   | . Cập nhật 3 ngày trước . 6 phút . Có VI (i)| ---------------- |
|    |   Playbook       | +-----------------------------------------+ | Sửa trên GitHub  |
|    |   Drill          | | (!) Code trang này mô tả đã đổi 12/11   | | Lịch sử (8)      |
|    | > Kiến trúc & QĐ | |     (3 commit) sau lần review cuối.     | | Báo lỗi trang    |
|    | > Tham chiếu     | |     [Xem thay đổi]                      | | Copy Markdown    |
|    | > Pháp lý & BM   | +-----------------------------------------+ |                  |
|    | > Mẫu            | ## Các bước                                 |                  |
|    |                  | +-- bash ------------------------- [Copy] + |                  |
|    |                  | | aws ecs update-service --cluster ...    | |                  |
|    |                  | +-----------------------------------------+ |                  |
|    |                  | ...                                         |                  |
|    |                  | < Trước: 5xx spike      Tiếp: DB restore >  |                  |
|    |                  | Liên quan: [Deploy guard] [ECS exec]        |                  |
|    |                  | Trang này có ích?  [Có] [Không]             |                  |
|    |                  | Nguồn AA-Ecosys@a1b2c3d . publish 10:42     |                  |
+----+------------------+---------------------------------------------+------------------+
```

**Desktop, trang chủ Docs** (`/admin/docs` không có `path`):

```
+----+-----------------------------------------------------------------------------------+
|    |  Tài liệu Adventure Asia             [ Tìm trong tài liệu...              / ]     |
|    |                                                                                   |
|    |  BẮT ĐẦU THEO VAI TRÒ                                                             |
|    |  [Business owner] [Tech lead/CTO] [CIO] [DevOps] [PM] [Kỹ sư mới] [Staff]         |
|    |                                                                                   |
|    |  TÔI CẦN...                                                                       |
|    |  [Có sự cố -> playbook] [Ship một thay đổi] [Onboard] [Yêu cầu dữ liệu/pháp lý]   |
|    |                                                                                   |
|    |  MỚI CẬP NHẬT                         | CẦN REVIEW (code đã đổi / quá hạn)        |
|    |  . Secret rotation      2 ngày trước  | (!) crm-keys          3 commit chưa xem   |
|    |  . AI gateway           3 ngày trước  | (!) job-kinds         quá hạn 12 ngày     |
|    |  . Docs đã đổi gì (tuần này) ->       | ...                                       |
+----+-----------------------------------------------------------------------------------+
```

**Điện thoại (~390 px):**

```
+------------------------------+     +------------------------------+
| <  Rollback ECS   [Mục] [Tìm]|     |  TRÊN TRANG NÀY          [x] |
+------------------------------+     |  Khi nào dùng                |
| Docs > Vận hành > Runbook    |     |  Chuẩn bị                    |
| Rollback một service ECS     |     | > Các bước                   |
| Đưa service về task def      |     |  Kiểm tra sau                |
| trước trong 5 phút.          |     +------------------------------+
| How-to . Reviewed 10/11 (i)  |     (bottom sheet mở từ nút [Mục])
| +--------------------------+ |
| |(!) Code đã đổi 12/11 ... | |
| +--------------------------+ |
| ## Các bước                  |
| +-- bash ----------- [Copy]+ |
| | aws ecs update-servi... >| |
| +--------------------------+ |
| [ Sơ đồ - chạm để phóng to ] |
| < Trước          Tiếp >      |
| Có ích?  [Có] [Không]        |
+------------------------------+
```

Danh sách trang trên điện thoại thành ngăn kéo mở từ nút "Docs" ở thanh trên, không còn là màn hình riêng.

---

## 4. Lộ trình theo lát PR

Cỡ: XS < 0,5 ngày · S ~0,5–1 · M ~1–2 · L ~2–3 ngày-agent. Mọi lát 0 USD/tháng trừ khi ghi khác.

### 4.1 Làm ngay trong AA-1118 (đúng phạm vi hiện có)

| # | Lát PR | Repo | Cỡ |
|---|---|---|---|
| 1 | Lint cụm từ đã bỏ (`retired.yaml` + `check_docs_text.py retired`), quét cả file agent; seed các cụm từ của 8 nhóm thay đổi; luật "ADR bỏ gì thì thêm dòng" vào template ADR | root (+ vendor sang 5 repo) | S |
| 2 | Thêm `docs-lint.yml` vendored vào CIS; sửa PR template CIS (câu gitignored, số check) | AA-CIS-App | XS |
| 3 | Sửa `_adr_meta` (`accepted**`); ADR 0001a hiện ghi chú bị Note S278 đảo ngược; đưa `description`, `owner`, `related`, `superseded_by` vào manifest | root | XS |
| 4 | `plan_sync` báo đỏ khi lệch (đã có trong AA-1118) | root | XS |
| 5 | Tách CIS `CONTEXT.md` (đã có trong AA-1118), dùng khối `gen:` khi lớp L2 xong | AA-CIS-App | M |

Lát 1 làm trước các đợt sửa nội dung của AA-1118: nó vừa chặn tái phạm, vừa là danh sách kiểm cho đợt sửa.

### 4.2 Issue mới A: "Docs sync engine" (generated facts, docs-impact, page history)

| # | Lát PR | Repo | Cỡ | Phụ thuộc |
|---|---|---|---|---|
| A1 | Lịch sử từng trang trong manifest (`fetch-depth: 0` blobless, `last_changed`, `history`), trang "Docs đã đổi gì", `manifest.previous.json` | root | S | — |
| A2 | `facts.snapshot.json` + `platform.yaml` + `gen_sections.py` (`--check`/`--write`) + 2 khối đầu: account/route LLM, service ECS | root (+ catalogue job, Infra `docs-gen`) | M | — |
| A3 | Khối tiếp: migration mới nhất mỗi owner + phiên bản app, job kind (biến `job-kinds.md` thành bảng sinh), required checks mỗi repo, số ngày backup | root | M | A2 |
| A4 | `doc-map.yaml` (seed từ `rows.json`) + `doc_impact.py` + workflow tái sử dụng; gọi từ 5 repo con, **chỉ cảnh báo** | root + 5 PR nhỏ ở repo con | M | — |
| A5 | Độ tươi theo sự kiện + `doc-owners.yaml` cho file agent/`CONTEXT.md` + báo cáo độ tươi vào manifest; luật `Verified:` khi tăng `last_reviewed` | root | M | A4 |
| A6 | Luật agent: `aa-ship`, brief `kiro-delegate`/`aa-session`, `pre-push` cảnh báo, bước cuối phiên, bước đầu phiên so `~/.claude/CLAUDE.md` với facts | root | S | A4 |
| A7 | Kiểm tra trong backtick: đường dẫn, địa chỉ Terraform đã che, tên service/kind/key, số migration, tên workflow | root (+ vendor) | M | A2 |
| A8 | Sau 2 tuần cảnh báo: docs-impact thành check bắt buộc (CIS/Booking/Partner merge queue, ruleset Infra) | 4 repo | XS | A4 + quyết định câu 3 |
| A9 | (tuỳ chọn) Cổng ảnh WebP/300 KB cho file mới dưới `docs/audits/` | root | XS | — |

Tổng ~8–10 ngày-agent.

### 4.3 Issue mới B: "Docs reader v2" (/admin/docs)

| # | Lát PR | Mục ở 3.3 | Repo | Cỡ |
|---|---|---|---|---|
| B1 | Đầu trang thân thiện + code block (copy, nhãn, tô màu) + link neo heading | 1, 2 | AA-CIS-App (+ root lát 4.1#3) | S |
| B2 | Banner tin cậy (audit `rows.json` trước, sau đó "code đã đổi" từ A5) + trang chủ Docs + sửa link (publish templates, link GitHub ngoài) | 3, 4, 5 | root + AA-CIS-App | M |
| B3 | Sidebar theo chủ đề (`sidebar.yaml` + lint) + bố cục 3 cột + mục lục dính scroll-spy + breadcrumb + Trước/Tiếp | 6, 7, 9 (phần điều hướng) | root + AA-CIS-App | M |
| B4 | Tìm toàn văn (FTS5 ở CIS API) + nhóm Docs trong ⌘K + phím `/` | 8 | AA-CIS-App | M |
| B5 | "Cập nhật lúc / Lịch sử / Sửa trên GitHub" (dùng A1) + Liên quan/backlink + widget phản hồi (migration CIS, review trước merge) + trang admin xem phản hồi | 9 | AA-CIS-App (+ root) | M |
| B6 | Phóng to sơ đồ + điện thoại (thanh dính, bottom sheet, ngăn kéo) + Copy Markdown | 10, 11, 14 | AA-CIS-App | S–M |
| B7 | Mở cho mọi vai trò staff (sau quyết định) | 12 | AA-CIS-App | XS |
| B8 | Docs app/Infra + "Agent rules" + Release notes trong reader, công tắc repo | 13 | root + AA-CIS-App + CIS API allowlist | M |

Tổng ~8–12 ngày-agent. Mỗi lát UI đi kèm kiểm giao diện theo `aa-ui-verify` (ảnh desktop/mobile/light/dark).

### 4.4 Thứ tự chạy gợi ý

1. Phiên kế tiếp: 4.1#1–3, B1, A1 (nhanh, thấy ngay; ~2 ngày).
2. Song song với các đợt sửa nội dung 1–5 của AA-1118: A2, A4, B2.
3. Trước đợt sửa 6–7 (viết lại trang lớn): A3 xong, để trang viết lại dùng khối `gen:`.
4. Sau đó: B3, B4, A5, A6, B5; cuối cùng A7, A8, B6–B8.

---

## 5. Câu hỏi cần tech lead quyết

Mỗi câu có đề xuất chọn sẵn (**in đậm**). Bản máy đọc: `decisions.json` cùng thư mục.

1. **Ai đọc được /admin/docs?** **Mở cho mọi vai trò staff, tầng owner/staff vẫn kiểm ở server** / giữ chỉ admin.
   Lý do: guide `audience: staff` hiện không tới được người đọc; nội dung tầng staff vốn đã có trong repo public.
2. **Bản đồ docs ↔ code đặt ở đâu?** **Một file trung tâm `docs/catalogue/doc-map.yaml`** / trường `watches:` trong
   front-matter từng trang / cả hai. Lý do: phủ được cả file không có front-matter (agent files, `CONTEXT.md`), một chỗ để
   xem và seed từ `rows.json`.
3. **Cổng docs-impact chặn tới đâu?** **Cảnh báo 2 tuần, sau đó bắt buộc** / chỉ cảnh báo mãi / bắt buộc ngay.
4. **Sidebar theo chủ đề lấy từ đâu?** **File `docs/sidebar.yaml` + lint "mỗi trang xuất hiện đúng một lần"** / suy từ
   heading của CAT-00 / giữ nhóm theo thư mục. Lý do: kiểm soát rõ, lint chặn trang mồ côi; CAT-00 là bảng Markdown, đọc
   máy dễ vỡ.
5. **Tìm kiếm toàn văn chạy ở đâu?** **Server: SQLite FTS5 trong CIS API** / trình duyệt: index tách theo tầng + MiniSearch.
   Lý do: nội dung tầng owner không rời server, không thêm thư viện, không tải index; ⌘K đã gọi API có debounce.
6. **Widget "Trang này có ích?"** **Có, lưu bảng nhỏ của CIS + trang admin xem** / tạo GitHub issue điền sẵn / không làm.
   Lý do: repo public, góp ý có thể chứa chi tiết nội bộ.
7. **Link "Sửa / Lịch sử trên GitHub".** **Hiện khi repo còn public, build tự ẩn khi repo chuyển private** / không hiện.
8. **Ý nghĩa `draft`.** **Sau khi AA-1118 sửa xong trang nào thì chuyển trang đó sang `active`; reader hiện `draft` là
   ghi chú nhỏ "Chưa duyệt"** / giữ như hiện tại (134/205 trang là draft).
9. **Slug chủ trang.** **`tech-lead`** (đổi các slug `nghiep` trong một đợt) / `nghiep`.
10. **Phương án giao diện.** **A: nâng cấp reader hiện có** / B: Fumadocs trong admin / C: site docs riêng.
11. **Công cụ DVC.** **Chưa dùng; bật khi bộ dữ liệu eval/calibration > ~50 MB, nhị phân, hoặc chứa văn bản tenant** /
    thử ngay cho bộ eval.
12. **Phạm vi Linear.** **AA-1118 giữ lint + vá nhanh + sửa nội dung; mở 2 issue mới "Docs sync engine" và "Docs reader
    v2"** / gộp hết vào AA-1118 / một issue mới duy nhất. (Theo luật Linear: chưa tạo issue nào, chờ tech lead đồng ý.)

---

## Tham chiếu

- Audit: `docs/audits/2026-11-17-S283-docs-audit/README.md`, `rows.json`, `tom-tat.vi.md`
- Reader: `apps/AA-CIS-App/frontend/app/admin/docs/page.tsx`, `DocsList.tsx`, `messages.ts`;
  `frontend/lib/docsReader.ts` (`matchesFilter`, `sectionOf`), `lib/docsGroups.ts`, `lib/rbac.ts:127`, `lib/adminIa.ts:150`;
  `app/_kit/MarkdownView.tsx`, `MermaidDiagram.tsx`, `CommandPalette.tsx`
- API: `apps/AA-CIS-App/api/routers/admin_docs.py`, `api/services/docs_reader.py`, `api/routers/learn.py`
- Tool/workflow: `tools/docs/build_docs_reader.py` (`_adr_meta`, `_entry()`), `check_frontmatter.py`,
  `check_docs_text.py`, `tools/catalogue/surface.py`; `.github/workflows/docs-sync.yml`, `docs-lint.yml`, `catalogue.yml`,
  `plan-sync.yml`; Infra `.github/workflows/docs-gen.yml`, `db-schema-dump.yml`
- Schema/luật: `docs/templates/frontmatter.schema.json`, `docs/STYLE.md`, `docs/README.md` (CAT-00)
- PR template: `apps/AA-CIS-App/.github/pull_request_template.md`
- Nguồn thị trường: docs.gitlab.com/development/documentation/workflow, backstage.io/docs/features/techdocs,
  docusaurus.io/docs/versioning, markdoc.dev, vale.sh, fumadocs.dev, nextra.site, pagefind.app, sqlite.org/fts5.html,
  doc.dvc.org; giá: mintlify.com/pricing, gitbook.com/pricing, readme.com/pricing (kiểm 17/11/2026, cần kiểm lại trước khi quyết)

---

## 6. Phản biện và điều chỉnh

Phản biện độc lập cùng ngày (S283), góc nhìn kỹ sư senior với ngân sách startup: một tech lead + agent, chưa có tenant
thật, người đọc docs chủ yếu là agent (qua file) và tech lead. Chỉ đọc repo, 0 USD. Mục này **thay thế** các khuyến nghị
tương ứng ở mục 1, 2.2, 3.3, 4 và 5 khi hai bên khác nhau. `decisions.json` chưa được sửa theo mục này: cần cập nhật
các câu 1, 2, 3, 4, 6, 7 trước khi gộp vào trang duyệt cuối phiên.

**Kết luận ngắn:** hướng đi đúng (Git là nguồn, nâng reader hiện có, không SaaS, không DVC cho docs). Nhưng bản tư vấn
hứa quá mức ở phần lint, đặt cổng PR nặng hơn mức cần, thêm 6 sổ đăng ký YAML tự nó sẽ lệch, và bỏ sót hai cách rẻ nhất:
**xoá/gộp trang** và **để agent soát lại docs theo phạm vi code vừa đổi** (đúng cách đã bắt được 24 trang sai hôm nay).
Tổng công sức nên giảm từ ~16–22 xuống ~7–8 ngày-agent.

### 6.1 Các mối lo và điều chỉnh

| # | Mối lo | Bằng chứng (kiểm hôm nay) | Điều chỉnh |
|---|---|---|---|
| 1 | **Lint cụm từ đã bỏ (L1) tạo cảm giác an toàn giả.** Nó chỉ bắt *tái phạm* của cụm từ đã được ghi vào `retired.yaml`; lần sai đầu tiên sau một quyết định mới vẫn lọt. Phần lớn câu sai là sai về nghĩa ("saga còn planned", menu/vai trò cũ, "chưa có nút mời"), không có cụm từ nào để bắt. | Chạy thử một danh sách ~20 cụm từ (chọn *sau khi* đã biết đáp án, nên là trần trên) trên `rows.json`: 19/24 trang sai có ≥1 câu khớp, nhưng chỉ 5/24 trang khớp *mọi* câu sai; 48/117 câu sai (41%). Với trang lệch một phần: 183/767 câu (24%). | **Giữ L1** (rẻ, có ích) nhưng ghi rõ vai trò: *cờ "đọc lại trang này"*, không phải bằng chứng trang đúng. Không viết ở đâu rằng L1 "chặn được cả 8 nhóm lỗi". Chỉ báo lỗi trên dòng mới, cảnh báo trên dòng cũ, như đề xuất. |
| 2 | **Thiếu cơ chế duy nhất bắt được sai về nghĩa:** đọc lại trang so với code. Không lint, khối sinh hay cổng PR nào thay được. | Audit hôm nay (agent đọc trang + đối chiếu code/live) là thứ duy nhất tìm ra 24 trang sai; báo cáo độ tươi cùng lúc nói "0 quá hạn". | **Thêm bước "soát docs theo phạm vi" vào nghi thức cuối phiên** (`aa-session`): lấy các trang mà `doc-map.yaml` nối với code đã merge trong phiên, cho một subagent đọc từng trang so với code, ghi lệch vào `docs-debt.md` hoặc sửa luôn. Chạy bằng Claude Code (năng lực gói hiện có, 0 USD phát sinh); **không** chạy qua AI gateway (tính tiền theo lượt). Một audit toàn bộ như hôm nay: mỗi quý hoặc sau một đợt đổi kiến trúc lớn. Đây là lớp chính; L1–L5 là lớp phụ. |
| 3 | **Khối sinh tự động (L2) không tự động đúng.** Sự thật nằm ở dữ liệu runtime (thứ tự route LLM trong DB) cần một lần chụp; chụp tay thì cũ đi như văn xuôi. | Trang sinh có sẵn `docs/generated/llm-routes.md`: snapshot chụp 09/11, **0 lần nhắc acc1**, trong khi S278 (12/11) đã đưa acc1 lên đầu route. Trang "sinh tự động" cũng đang sai. | **(a) Vá nhanh:** chụp lại snapshot llm-routes ngay (đường ECS exec có sẵn). **(b)** L2 chỉ làm cho sự thật lấy được từ Git (Terraform: service ECS; file migration: số mới nhất mỗi owner; `kinds.py`: job kind; `gh api`: required checks). Sự thật runtime: hoặc chụp theo lịch bằng mẫu ECS task tạm của DB Schema Dump, hoặc trang hiện to `captured_at` + banner khi quá N ngày. **(c)** Không cắm khối `gen:` vào ~70 trang: sinh ~5 trang sự thật, thay các bản chép trong văn xuôi bằng **link** tới trang đó; chỉ nhúng khối vào ≤10 file agent (nạp mỗi phiên). Bot PR đêm chạm vài chục file sẽ xung đột với PR người đang mở. |
| 4 | **Cổng PR quá nặng (L3, A8).** Check bắt buộc trong merge queue của 4 repo + dòng `Docs-impact:` bắt buộc trong thân mọi PR. Agent sẽ điền `none: …` cho qua; người thật thì thêm một lý do để PR đỏ. Workflow tái sử dụng đọc map từ repo gốc làm 5 repo phụ thuộc repo gốc. | Repo con đã có 9–10 required checks; phần lớn PR là của agent; checklist docs trong PR template CIS hiện có mà không ai kiểm (chính PR template còn câu "`docs/` is gitignored" sai). | **Chỉ cảnh báo, không có hạn chuyển sang bắt buộc:** comment cố định "Docs impact" + danh sách `docs-debt.md`; bỏ dòng bắt buộc trong thân PR. Thực thi bằng bước cuối phiên (mục 2 trên) đọc `docs-debt.md`. Chỉ xem lại "bắt buộc" nếu sau 1 tháng nợ docs vẫn tăng. **Câu 3 mục 5 đổi đề xuất** (xem 6.3). A8 bỏ khỏi lộ trình. |
| 5 | **Bỏ sót cách sửa gốc cho lỗ hổng #3 (docs khác repo với code):** đặt trang đúng repo. | Runbook chỉ về một app (`booking-admin-runbook`, `cis-admin-runbook`, `tripplanner-runbook`, 3 trang **sai**) nằm ở repo gốc; 314/401 bản ghi ở repo gốc. | **Luật đặt trang giống luật đặt ADR:** trang chỉ mô tả một app nằm trong `docs/` của app đó, sửa cùng PR với code (checklist PR template có sẵn đủ dùng). Repo gốc giữ trang xuyên app. Reader publish thêm `docs/` của repo app (phần docs của B8, đưa lên sớm; **chưa** publish file luật agent). L3 khi đó chỉ còn lo trang xuyên app. Chuyển trang theo từng đợt sửa của AA-1118, giữ redirect `?path=` cũ. |
| 6 | **Bỏ sót cách rẻ nhất: xoá/gộp trang.** Mỗi trang là một chỗ có thể lệch; 361 trang cho một tech lead là nhiều. | 10 trang orphan; TripPlanner 15/22 trang sai hoặc orphan; 134/205 trang reader mang `draft`; nhiều trang chép lại `CONTEXT.md` (bản tư vấn tự nêu ở mục 2.2). | Mỗi đợt AA-1118: trang không có người đọc rõ → lưu trữ (`docs/archive/` + banner) hoặc thay bằng link tới nguồn; trang sai mà viết lại tốn hơn giá trị (vd `architecture-overview.md` TripPlanner) → thay bằng 3 dòng trỏ `CONTEXT.md`. Đo kết quả bằng số trang publish giảm, không chỉ số trang sửa. |
| 7 | **Sáu sổ đăng ký mới tự chúng sẽ lệch:** `retired.yaml`, `platform.yaml`, `facts.snapshot.json`, `doc-map.yaml`, `doc-owners.yaml`, `sidebar.yaml`. | Mỗi file là một sự thật chép tay mới, đúng loại lỗ hổng #4 của mục 2.1. | Gộp `doc-owners.yaml` vào `doc-map.yaml` (một file: đường dẫn → code theo dõi + vai trò chủ). Sidebar lấy từ trường front-matter (`nav: <nhóm>`, tuỳ chọn `nav_order`) thay vì `sidebar.yaml`: dời file không vỡ, lint "mỗi trang publish có `nav`" đơn giản hơn. `platform.yaml` chỉ cho quyết định không có nguồn code (vai trò account). Còn 3 file thay vì 6. |
| 8 | **L4 rút chu kỳ review (agent files 30 ngày, runbook 60) gây báo động giả.** 126 file agent × 30 ngày = banner "quá hạn" thường trực; người đọc học cách bỏ qua banner. Dòng `Verified:` cũng là tự khai, agent sẽ ghi cho qua. | Hôm nay 120 trang có `last_reviewed` trong 30 ngày vẫn lệch: ngày review tự khai không có giá trị chứng minh. | Bỏ phần rút chu kỳ; giữ 90 ngày làm lưới an toàn. Chỉ giữ cờ **theo sự kiện** ("code trang này theo dõi đã đổi sau lần review"), vì nó có căn cứ máy. Bỏ luật `Verified:`; thay bằng bước soát cuối phiên (mục 2). |
| 9 | **L5 (kiểm danh tính trong backtick) đắt và giòn:** nhiều loại danh tính, nhiều ngoại lệ, false positive trên trang lịch sử/ADR. | Đọc lướt 117 câu sai của 24 trang: lỗi kiểu "đường dẫn/địa chỉ không tồn tại" là thiểu số (chưa đếm chính xác); hại thật nằm ở địa chỉ Terraform (`crm-keys`, `secret-rotation` báo "No changes" giả). | Chỉ giữ 2 kiểm: đường dẫn repo trong backtick phải tồn tại; địa chỉ `-target=`/`-replace=` phải có trong địa chỉ tài nguyên đọc tĩnh từ HCL (kể cả khối `moved`), không cần AWS credential. Bỏ phần còn lại của L5 và A7. |
| 10 | **Tổng công sức bị nói nhẹ và cạnh tranh với việc sản phẩm.** | Mục 1 ghi ~15–20 ngày-agent; cộng mục 4 được ~2 (4.1) + 8–10 (A) + 8–12 (B) ≈ 18–24. Ngày-agent không tốn USD phát sinh nhưng tiêu năng lực gói Claude và lượt gác cổng của tech lead. | Lộ trình gọn ở 6.2: ~7–8 ngày-agent. Mọi thứ khác để "khi có ≥5 người đọc thường xuyên ngoài tech lead" hoặc khi có tenant/prod. |
| 11 | **Reader v2 làm nhiều thứ cho ít người đọc; một số món trái luật kit.** Widget "Trang này có ích?" cần migration CIS + trang admin + review; điện thoại nâng cao, copy Markdown, docs luật agent trong reader đều chưa có người dùng. Menu admin tự thu ở riêng `/admin/docs` là biến thể một trang, trái ADR 0016 / "consistent, not one-off". | Hiện reader chỉ vai trò `admin` mở được (`rbac.ts:127`); chưa có tenant; reader đã dùng được trên điện thoại (danh sách ↔ trang). | Giữ B1, B3 (sidebar từ front-matter, 3 cột, mục lục dính), B4 (tìm toàn văn). **Hoãn** B5 phần phản hồi (câu 6 đổi đề xuất), B6 trừ "chạm sơ đồ để phóng to", B8 phần luật agent, mục 14. Chế độ "nội dung rộng / thu menu" làm ở **kit** (`_kit/core` bản CIS, rồi sync) để trang dài khác dùng chung, không làm riêng cho Docs. |
| 12 | **Phân quyền theo tầng phải phủ mọi bề mặt mới, không chỉ trang.** Snippet tìm kiếm, ⌘K, "Trang link tới đây", "Mới cập nhật", "Docs đã đổi gì" (tiêu đề commit), "Copy Markdown" đều có thể lộ tiêu đề/đoạn trang tầng owner cho người không có cờ owner. | Tầng owner hiện = họ id SEC (bảo mật, pháp lý) + bản đồ hạ tầng sinh tự động (`build_docs_reader.py` rule 5); API lọc ở `_visible()`, fail-closed. | Mọi endpoint mới đi qua cùng `_visible()`; mỗi bề mặt có test "người không owner không thấy tiêu đề/snippet trang owner". Trang "Docs đã đổi gì" lọc theo tầng trang chứ không in `git log` thô. Ghi rõ: các trang này vẫn nằm trong repo public, nên tầng owner là **phân luồng đọc**, không phải bảo mật; không đầu tư thêm cơ chế bí mật cho nó. |
| 13 | **Mở reader cho mọi staff (câu 1) khi runbook cho staff đang sai.** | 3 runbook dành cho staff (`booking-admin-runbook`, `cis-admin-runbook`, `tripplanner-runbook` + bản `.vi.md`) có verdict `wrong`. | Mở cho mọi staff **sau khi** 3 trang đó được sửa hoặc mang banner "Có lỗi đã biết" (câu 1 thêm điều kiện). |
| 14 | **"Sửa trên GitHub" vô ích với staff không phải kỹ sư** và mở đường sửa ngoài luồng agent/PR. | Người đọc staff ngoài kỹ thuật không làm việc trên GitHub (chưa kiểm danh sách thành viên org). | "Nguồn · Lịch sử" cho mọi người đọc; "Sửa trên GitHub" chỉ hiện cho vai trò admin (câu 7 điều chỉnh). |
| 15 | **Một số số liệu chi phí/kỹ thuật chưa có bằng chứng trong thư mục.** | Giá SaaS (Mintlify, GitBook, ReadMe) lấy từ trang giá ngày 17/11 nhưng không lưu bản chụp; phương án C "~5–10 USD" tự ghi là ước tính; "AWS thêm < 0,1 USD/tháng" không có phép tính; bộ nhớ index FTS5 trên mỗi task API chưa ước; FTS5 + tokenizer trigram chạy được trên Python local (SQLite 3.45) nhưng **chưa kiểm trong image CIS**. | Coi giá C/D là tham khảo: quyết định chọn A không phụ thuộc chúng, không cần kiểm thêm. Trước B4: kiểm FTS5 trigram trong image API (một lệnh `python3 -c` qua ECS exec hoặc CI) và đo RAM index (~3,3 MB văn bản); nếu không có FTS5 thì dùng MiniSearch phía trình duyệt với index chỉ tầng staff. |
| 16 | **DVC.** | Golden set đã có phiên bản trong DB; file dữ liệu trong repo vài MB. | Đồng ý mục 2.4, không đổi. Lưu ý: trang duyệt nên hỏi lại tech lead "DVC" là *kiểm soát phiên bản docs* hay *công cụ DVC*; bản tư vấn đã trả lời cả hai. |

### 6.2 Lộ trình sau điều chỉnh (~7–8 ngày-agent, 0 USD/tháng)

| Đợt | Nội dung | Thuộc | Cỡ |
|---|---|---|---|
| 0. Vá nhanh (làm ngay) | L7 (docs-lint cho CIS, sửa PR template, badge `accepted**`, ADR 0001a ghi chú Note S278); **chụp lại snapshot llm-routes**; L1 chế độ cảnh báo; reader: trang chủ tạm = render CAT-00 thay ô trống "Select a page", mục lục `<details>` mở sẵn, hiện `description`; banner "Có lỗi đã biết" từ `rows.json` **tự tắt khi trang có commit sau 17/11** (không thì chính banner cũng cũ); lưu trữ 10 trang orphan | AA-1118 | ~1 ngày |
| 1. Đồng bộ | A1 (lịch sử từng trang, "Docs đã đổi gì" lọc theo tầng); L2 bản gọn (~5 trang sự thật lấy từ Git, thay bản chép trong file agent bằng link/khối); `doc-map.yaml` (gộp chủ trang) + L3 chỉ cảnh báo; bước "soát docs theo phạm vi" cuối phiên; luật đặt trang theo repo + reader publish `docs/` của repo app; kiểm địa chỉ Terraform tĩnh | issue mới "Docs sync" | ~3 ngày |
| 2. Reader v2 gọn | B1 (đầu trang, code block copy/nhãn/tô màu, neo heading); B3 (sidebar từ front-matter `nav`, 3 cột qua chế độ rộng của kit, mục lục dính, breadcrumb, Trước/Tiếp); B4 (tìm toàn văn sau khi kiểm FTS5 trong image); phóng to sơ đồ; mở cho mọi staff khi đủ điều kiện ở mục 13 | issue mới "Docs reader v2" | ~3–4 ngày |
| Hoãn | L4 rút chu kỳ, L5 (trừ kiểm địa chỉ TF + đường dẫn), A7, A8 (cổng bắt buộc), widget phản hồi + migration, điện thoại nâng cao, copy Markdown, luật agent trong reader, thuật ngữ hover, Ask AI, bộ chọn phiên bản | — | — |

Đợt 0 và bước soát cuối phiên đem lại phần lớn giá trị; nếu phải cắt tiếp, cắt từ cuối Đợt 2 lên.

### 6.3 Câu hỏi ở mục 5 đổi đề xuất

| Câu | Đề xuất cũ | Đề xuất mới |
|---|---|---|
| 1. Ai đọc /admin/docs | Mở cho mọi staff | **Mở cho mọi staff sau khi 3 runbook staff sai được sửa hoặc gắn banner** |
| 2. Bản đồ docs ↔ code | `doc-map.yaml` trung tâm | Giữ, **gộp luôn `doc-owners.yaml` vào** (một file) |
| 3. Cổng docs-impact | Cảnh báo 2 tuần rồi bắt buộc | **Chỉ cảnh báo + `docs-debt.md` + soát cuối phiên; xem lại sau 1 tháng nếu nợ tăng** |
| 4. Nguồn sidebar | `docs/sidebar.yaml` + lint | **Trường front-matter `nav` (+ `nav_order`) + lint "mỗi trang publish có `nav`"** |
| 6. Widget "có ích?" | Bảng CIS + trang admin | **Không làm bây giờ**; làm khi có ≥5 người đọc thường xuyên ngoài tech lead |
| 7. Link GitHub | Hiện khi repo public | **"Nguồn · Lịch sử" cho mọi người đọc; "Sửa" chỉ cho admin** |
| 12. Phạm vi Linear | AA-1118 + 2 issue mới | Giữ cấu trúc, nhưng 2 issue mới nhỏ hơn (~3 ngày mỗi issue); Đợt 0 nằm trong AA-1118 |

Các câu 5, 8, 9, 10, 11 giữ nguyên đề xuất.
