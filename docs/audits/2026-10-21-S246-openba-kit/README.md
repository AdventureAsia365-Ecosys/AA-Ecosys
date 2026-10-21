# OpenBA-Kit: học gì cho cách quản lý tài liệu của AA (S246)

## 0. Tóm tắt

- **OpenBA-Kit là gì:** bộ công cụ BA theo dạng file. Kho của Pham Minh Son, giấy phép MIT, mới 6 ngày tuổi (5 commit, 15–20/10/2026). Kho có 56 skill, 19 rule (296 dòng) và 47 template. Bộ kit đi theo vòng đời BA: discover → PRD → SRS (FR/BR/ERR/NFR) → sơ đồ → use case/story/AC → wireframe → API → test → drift/CR → Jira/Confluence.
- **Điểm mạnh nhất:** quy ước ở mức yêu cầu. Gồm ID ổn định cho FR/BR/ERR, quy tắc viết theo dạng KHI/THÌ/NGOẠI LỆ, tối thiểu 3 kịch bản (thường, lỗi, biên), ma trận trạng thái, và bảng từ mơ hồ cấm dùng. Phần `diagram-design` vendor từ nguồn ngoài cũng làm tốt (giới hạn độ phức tạp, câu hỏi "bảng có thay được không?").
- **Điểm yếu nhất:** không có gì được kiểm bằng công cụ. 54/56 skill là vỏ sinh tự động, 34/47 template là stub rỗng, các rule ID mâu thuẫn nhau, và không có trạng thái duyệt hay người duyệt.
- **Mình đang ở đâu:** về quản lý tài liệu, mình đã mạnh hơn OpenBA. Mình có catalog có ID, front-matter kiểm bằng schema trong CI, docs-lint, trang sinh từ hệ thống thật, ADR có amend, và `Refs AA-` trong commit. Chỗ yếu của mình nằm ở phía yêu cầu nghiệp vụ, ở drift và ở chi phí token.
- **Phát hiện bất ngờ:** đã có khoảng 199 lệnh `COMMENT ON` trong migration, nhưng trình sinh `db-schema-reference.md` không đọc chúng. Vì vậy DM-3.2 và DM-3.5 đang bị vi phạm mà không ai biết.
- **Ba việc nên làm trước:**
  1. **D1:** Done-when phải có ca từ chối và ca biên (XS).
  2. **D2:** cho schema dump đọc `COMMENT ON` (S).
  3. **D3:** sửa xung đột ADR 0009 của CIS và thêm bảng Reserved có kiểm (XS–S).
- **Không học:** cài kit hay symlink 56 skill, SRS IEEE đầy đủ, semver cho mọi trang, bảng tay (data dictionary, RTM, error matrix), và đồng bộ Jira tự động.

## 1. OpenBA-Kit làm thế nào

Nguồn đã đọc: bản clone chỉ đọc tại `/home/nghiep/projects/AA-Ecosys/.tmp-session/openba/src`.

**Vòng đời tài liệu.** Mọi tài liệu ghi vào một cây thư mục theo feature: `docs/{feature}/{srs,usecases,userstories,test,api,ui,cr}/`. Thứ tự các bước:

```text
discover/prd → brainstorm/brd/urd → srs (FR/BR/ERR/NFR) → diagrams → usecase/userstory/ac
→ wireframe/prototype → api-* → test-checklist/test-cases/playwright
→ gap/doc-drift/cr/kg/dashboard → jira/confluence/export/preview/meet
```

**Rules (`rules/01`–`19`):**

| Rule | Nội dung | Ghi chú |
|---|---|---|
| 01, 02, 03, 06 | ID `FR-MOD-FEAT-SEQ`, `BR-DOMAIN-SEQ` (KHI/THÌ/NGOẠI LỆ), `ERR-MOD-HTTP-SEQ`, `UC-MOD-SEQ` | Độ dài SEQ lệch nhau (3 / 2–3 / 2 chữ số). `_templates/08-srs.md:11` dùng `FR-AUTH-001`, trái với rule 01 |
| 04 | NFR theo ISO 25010, có số mặc định (P95 < 500 ms, 1.000 TPS, 99,9 %) | Chỉ 4 nhóm. Các con số không có nguồn |
| 05 | Mục lục SRS theo IEEE 830 / 29148 | Template 08-srs lại là bản rút gọn, nên rule và template không khớp |
| 08 | Ít nhất 3 kịch bản Gherkin mỗi story: thường, lỗi nghiệp vụ, biên | Không có file .feature nào, nên không kịch bản nào được chạy |
| 09 | Data dictionary 8 cột viết tay | Ví dụ tự mâu thuẫn: default `PENDING` không có trong enum |
| 11 | Error matrix 7 cột | Lệch với rule 03 |
| 12 | Ma trận chuyển trạng thái (có role) | Template 19 lại có cột side effect, không có role |
| 13 | Wireframe xám, phải đủ các trạng thái UI | Template 31 không làm đúng chính rule này |
| 14 | RTM FR → US → AC → TC | Dừng ở test case, không nối tới issue, PR hay verify live |
| 15 | Phân tích tác động CR trước khi sửa tài liệu | Template 47 có CR ID nhưng không ghi ai duyệt |
| 16 | Bảng 5 câu mơ hồ kèm cách viết đo được | Chỉ kiểm bằng prompt |
| 17 | Ma trận RBAC | Phạm vi dữ liệu chỉ nằm trong tên dòng |
| 18 | Front-matter `depends_on`, `related_diagrams` | Không có gì kiểm |
| 19 | Semver và bảng Revision History cho mọi tài liệu | 13 template quan trọng (gồm 01-prd, 08-srs) không có bảng này |

**Skills:**
- `skills/srs`, `skills/ac`, `skills/cr`, `skills/doc-drift`, `skills/code-to-srs` (trích `file:dòng`), `skills/reverse-doc` và `reverse-preview` (huy hiệu độ tin cậy H/M/L), `skills/meet`, `skills/api-map` (bảng UI ↔ DB ↔ API đối tác), `skills/preview`.
- Tất cả chỉ là hướng dẫn viết cho LLM, không có script kiểm.
- `skills/kg` và `skills/dashboard` trỏ tới template không tồn tại (45, 46).

**Templates:** 34/47 là stub chung ("Mục 1/2/3"). Các file `.bru`, `.spec.ts`, `.d2`, `.bpmn`, `.puml`, `.dbml` thực chất chứa Markdown.

**Sơ đồ:**
- `skills/diagram-design/SKILL.md` (v2.6, tiếng Anh, vendor từ ngoài) có:
  - câu hỏi "bảng hay đoạn văn có làm được không?" (dòng 264);
  - giới hạn 9 node, 12 mũi tên (dòng 233–241);
  - hợp đồng SVG có thể truy cập (dòng 379–388);
  - quy tắc "extract, don't render" (dòng 347–352).
- `scripts/render_diagrams.py` chỉ vẽ được sequence và state. Flowchart và ER âm thầm rơi về bộ vẽ sequence.

**Cài đặt:** symlink `skills/*` vào `~/.claude/skills`. Khi đó các đường dẫn `rules/` và `_templates/` bị gãy, và tên skill chung chung (`ask`, `export`, `state`) dễ trùng với skill khác.

## 2. Hệ tài liệu của AA hiện nay

**Đang tốt:**
- Catalog Diátaxis có ID ổn định: `docs/README.md` (CAT-00).
- Quy tắc tài liệu nằm trong `docs/engineering-handbook.md` §4, `docs/STYLE.md` (đã có mục Diagrams, dòng 141–158) và `docs/templates/` (12 template cùng `frontmatter.schema.json`).
- Docs-lint ở root (`.github/workflows/docs-lint.yml`) kiểm front-matter, ADR index, AWS CLI một dòng, link (lychee), markdownlint và gitleaks. Mỗi thứ Hai có báo cáo freshness.
- Có trang sinh tự động: `docs/architecture/db-schema-reference.md` và `docs/generated/{alarms,iam-roles,inventory,network}.md`.
- Data standards có ID quy tắc (DM-x.y), cột "Enforced by" và quy trình đổi version (`docs/architecture/data-standards/`).
- Contract có version: `docs/contracts/README.md`.
- Truy vết tốt từ commit xuống: khoảng 192/200 commit CIS có `Refs AA-`, 430/495 file test CIS đặt tên `test_aaNNN`, và mỗi issue có implementation note.

**Thiếu hoặc đang lệch:**
1. **Spec của chị Thư không có chỗ chính thức.** `docs/research/partner-crm-spec.md` nằm trong nhóm "journal", tức "lịch sử, không phải sự thật hiện tại". Spec không có front-matter, version hay dấu duyệt. Spec đã có ID module (F1–F5, 1–18) nhưng chưa có ID ở mức từng quy tắc.
2. **Quy tắc nghiệp vụ của chủ không có ID.** Ví dụ: cưỡi voi, độ trung thực nguồn, nguyên tắc CRM §2 và §5. Phần lớn nằm trong auto-memory riêng của Claude, nên Kiro không thấy.
3. **Done-when thường chỉ có đường thường.** Khoảng 70 % (135/192) issue đã xuất không có ca lỗi hay ca biên nào. `docs/templates/definition-of-ready.md` và `skill/aa-linear-issue/SKILL.md` không yêu cầu hai loại ca này.
4. **`COMMENT ON` không hiện ra.** `infra/AA-CIS-Infra/db/schema_dump.py` không đọc `pg_description`, nên `db-schema-reference.md` có 0 thẻ `pii:`.
5. **ID trùng nhau:**
   - `apps/AA-CIS-App/docs/adr/0009-f17-...md` đã có, nhưng `docs/backlog/README.md:48` (AA-915) vẫn định dùng "app ADR 0009".
   - Số 0010 ở root được "giữ chỗ" trong audit, không nằm trong index.
   - Các dãy D1… trùng nhau giữa S241, CRM và Writing Memory.
6. **Drift dù đã có lint:**
   - Handbook §4.6 ghi trang generated là "Planned" dù đã có.
   - `docs/adr/README.md` ghi data standards v1.0, thực tế là v1.2.
   - `docs/audits/README.md` vẫn mang tên "AA-CIS pipeline" và thiếu khoảng 27/38 audit.
   - `skill/README.md` vẫn ghi "nháp 06/10".
   - `skill/aa-cis-schema/SKILL.md:66` trỏ tới file không tồn tại.
7. **AA-CIS-App không có docs-lint.** Backlog ghi AA-888 "Done" nhưng repo lớn nhất lại bị thiếu.
8. **Chi phí token cao.** `apps/AA-CIS-App/CONTEXT.md` nặng 165 KB và phải đọc trước khi thiết kế. Booking CONTEXT 55 KB, handbook 87 KB. Có dòng trong index sessions dài 1.820 ký tự.
9. **Duyệt nằm ngoài git.** Câu trả lời trên trang duyệt nằm trong DB của artifact. `docs/audits/2026-10-20-S245-tenant-crm/v2.1/owner-approvals-r2.md` được chép tay. Trang duyệt của chị Thư chưa có bản ghi trả lời trong repo.

## 3. Tiêu chuẩn quản lý tài liệu

| Chuẩn | Yêu cầu cốt lõi | Áp dụng thực tế cho mình | Nguồn |
|---|---|---|---|
| ISO/IEC/IEEE 15289:2019 (trả phí) | 7 loại tài liệu chung: description, plan, policy, procedure, report, request, specification. Được gộp hoặc tách | Chỉ dùng làm checklist. Thêm loại `specification` khi có spec thật | iso.org/standard/74909 |
| ISO/IEC/IEEE 29148:2018 (thay IEEE 830) | Yêu cầu phải rõ, kiểm được, đơn nhất, có nguồn | Done-when kiểm được, có ca lỗi và ca biên (D1). Không viết SRS đầy đủ | iso.org/standard/72089 |
| ISO/IEC/IEEE 26514 / 26515 | Tài liệu cho người dùng viết trong cùng vòng agile | Guide vai trò song ngữ đã khớp. Thêm "user doc impact" khi cần | iso.org/standard/77451, 70880 |
| ISO/IEC/IEEE 29119-3:2021 | Test plan, báo cáo hoàn tất test | Mẫu UAT đã có. Không làm thêm | iso.org/standard/79429 |
| ISO 9001:2015 §7.5 | Nhận diện, duyệt, version, truy cập, lưu giữ. Bằng chứng không bị sửa | Git, PR và front-matter đã đủ phần lớn. Thiếu bản ghi duyệt trong git (D10) | Hướng dẫn công khai của ISO/TC176 |
| IIBA BABOK v3 | Truy vết, duyệt = baseline, verify khác validate | Gắn version và dấu "approved by" cho spec chủ (D14) | iiba.org |
| NASA SWE-052 | Truy vết hai chiều, truy theo giá trị | Để sau. Chỉ làm khi đã có rule có ID và miền đã build | swehb.nasa.gov/x/x4AIAw |
| IEEE 828 / ISO 9001 §8.3.6 | Kiểm soát thay đổi, baseline | Issue là CR, PR là bản ghi thay đổi. Đã có | standards.ieee.org/standard/828-2012 |
| Diátaxis | Mỗi trang một loại. Không tạo khung rỗng | Đã dùng. Là lý do không chép 34 stub của OpenBA | diataxis.fr |
| Write the Docs / Google docguide | Docs-as-code, sửa tài liệu cùng PR, xoá trang chết | Đã có. Thêm lint cho CIS (D4) | writethedocs.org, google.github.io/styleguide/docguide |
| Nygard ADR / MADR 4.0 | Đánh số không dùng lại. Có mục Confirmation và decision-makers | Bảng Reserved có kiểm (D3) | adr.github.io/madr |
| arc42 / C4 | Chỉ dùng phần có ích. C4 mức L1–L2 là đủ | Đã có trong STYLE.md. Không làm thêm | arc42.org, c4model.com |
| GitLab handbook-first | Ghi vào repo trước, rồi mới báo ở kênh khác | Đưa câu trả lời duyệt về git (D10) | handbook.gitlab.com |
| SemVer / Keep a Changelog | Version chỉ dùng khi có giao diện công khai | Dùng cho contract và spec đã ký. Không dùng cho trang văn xuôi | semver.org, keepachangelog.com |
| GOV.UK tech-docs-gem | `last_reviewed_on`, `review_in`, owner. Review theo trigger | Đã có lịch review. Thêm `watch_paths` (D12) | github.com/alphagov/tech-docs-gem |

## 4. Đề xuất áp dụng, xếp hạng

Thang công: XS < 1 giờ, S khoảng nửa ngày đến 1 ngày, M khoảng 1–3 ngày. "Adopt" là lấy gần nguyên ý tưởng. "Adapt" là lấy ý tưởng nhưng đổi cách làm.

| Mã | Đề xuất | Học từ | Hiện trạng AA | Công | Giá trị |
|---|---|---|---|---|---|
| D1 | **Adapt.** Issue có quy tắc hoặc hướng tới người dùng phải có ít nhất 1 ca từ chối và 1 ca biên trong Done-when, nêu mã lỗi nếu có. Nếu không áp dụng thì ghi "N/A – lý do". Sửa DoR, `aa-linear-issue` và brief cho reviewer. Không dùng Gherkin | `rules/08-gherkin-acceptance-criteria.md`, ISO 29148 | DoR chỉ yêu cầu "3–6 tiêu chí". Khoảng 70 % issue không có ca lỗi | XS | Cao |
| D2 | **Adopt (sửa lỗi).** `schema_dump.py` đọc `obj_description`/`col_description`, `gen_schema_reference.py` hiện cột ý nghĩa. Bổ sung DM-3.5: cột status phải giải thích từng giá trị | `rules/09` (làm ngược lại: không viết bảng tay) | Có 199 COMMENT nhưng không hiện ra. DM-3.2 và DM-3.5 đang sai | S | Cao |
| D3 | **Adopt.** Sửa AA-915 thành CIS ADR 0010 trong backlog và `plan.json`. Thêm bảng Reserved vào mọi `docs/adr/README.md`. `check_adr_index.py` báo lỗi khi số đã giữ chỗ trùng với file có thật | MADR, Nygard | CIS 0009 đang bị trùng. 0010 ở root giữ chỗ trong audit | XS–S | Cao |
| D4 | **Adopt.** Đưa `docs-lint.yml` sang AA-CIS-App. Chạy chế độ warn hoặc dùng baseline link lúc đầu. Không lặp lại check resource-ids vì CI đã có. Sửa trạng thái AA-888 cho đúng | Write the Docs | CIS không có docs-lint dù AA-888 ghi Done | S–M | Cao |
| D5 | **Adopt.** Tách `apps/AA-CIS-App/CONTEXT.md` theo domain: Staff roles khoảng 43 KB, Architecture, Glossary, Pipeline. Giữ một trang gốc ngắn có link | (OpenBA không có; rút từ đo token) | 165 KB, phải đọc trước mỗi thiết kế | M | Cao |
| D6 | **Adapt.** Đưa spec CRM vào catalog: front-matter, `status: draft`, giữ nguyên ID F1–F5/1–18 (không đánh số lại), để stub ở đường dẫn cũ. Không dùng prefix PROD vì PROD-01 đã có; dùng APP-xx hoặc thêm prefix mới. Owner ghi "thu" sau khi chị xác nhận | `rules/01`, `05`; 29148 | Spec đang nằm trong research/journal | XS–S | TB–Cao |
| D7 | **Adapt.** Check theo kiểu ADR index: audit mới nào chưa có link trong `docs/audits/README.md` thì báo. Dòng index vẫn viết tay. Sửa tiêu đề index | (ngược với `/kg` của OpenBA) | Thiếu khoảng 27/38 audit | XS–S | TB |
| D8 | **Adapt.** Thêm vào `aa-ui-verify` và Done-when cho issue UI các trạng thái loading, error (API lỗi), 403 và modal/drawer. Empty state đã có | `rules/13` | Chưa ai kiểm error và loading | XS | TB |
| D9 | **Adapt.** Thêm vào `docs/STYLE.md` nhãn `[verified-live <ngày>]`, `[from-code path:dòng]`, `[inference]`, `[unverified]`. Dùng lại từ đã có. Không dùng phần trăm | `skills/code-to-srs`, `reverse-doc` | Chỉ một trang research dùng nhãn kiểu này | XS | TB |
| D10 | **Adapt.** Khi đóng phiên, xuất câu trả lời artifact ra `approvals.json` (gồm choice, người duyệt, ngày) trong thư mục audit. Thêm bước này vào `skill/aa-session`. Khi trích chéo tài liệu thì gắn prefix (CRM-D12). Bỏ lint "14 ngày" | ISO 9001 §7.5.3, GitLab | Đang chép tay. Duyệt của chị Thư chưa có bản ghi | S | TB |
| D11 | **Adapt.** Script `check_skills.py` tự động hoá `skill/REVIEW-CHECKLIST.md`: đường dẫn phải tồn tại, description có trigger (cả "Dùng khi/cho/mỗi khi"), tên khớp thư mục. Sửa link chết ở `aa-cis-schema:66` và tiêu đề "nháp" | (lỗi của OpenBA: 14 file có `\n`) | Checklist hiện chỉ làm tay | S | TB |
| D12 | **Adapt (giai đoạn 1).** Thêm `watch_paths` (chỉ trong cùng repo) vào schema. Báo cáo tuần có mục "Nguồn đổi sau review". Gắn trước cho khoảng 5 trang: handbook, ADR README, runbook | `skills/doc-drift`, GOV.UK, Ergo | Chỉ review theo lịch, drift vẫn lọt | S | TB |
| D13 | **Adapt (hẹp).** Trang quy tắc chủ theo mẫu DM: ID, Rule, Why, Enforced by, Steward. Chỉ cho khoảng 10–15 rule chưa có ID. Rule nào đã có (DM-4.5, ADR 0005) thì trỏ tới, không chép lại. Không bắt buộc KHI/THÌ/NGOẠI LỆ | `rules/02` | Rule chủ nằm trong auto-memory riêng | S | TB |
| D14 | Để sau. Thêm dòng "Version X · approved by · ngày" và bảng thay đổi vào spec chủ, giống data-standards. Không gắn git tag nếu Nghiệp chưa chốt | `rules/19`, BABOK | Chưa có dấu chị Thư duyệt | XS | TB |
| D15 | Để sau. Lint cho ID DM-x.y và Cx.y: mỗi ID định nghĩa đúng một lần, mọi trích dẫn phải trỏ được | `rules/01–03` (không có công cụ) | 161 lần trích dẫn, không có gì kiểm | S | TB |
| D16 | Để sau. Template trang duyệt chung có 2 chế độ: Nghiệp (có mã, có approve-all) và chị Thư (không mã, không approve-all) | `skills/preview` | Mỗi phiên viết tay lại, tốn token | M | TB |
| D17 | Để sau, chờ AA-682. Trang ma trận chuyển trạng thái trip case sinh từ seed migration và hằng số Python | `rules/12` | 12 cạnh đang viết tay trong CONTEXT | S | Thấp–TB |
| D18 | Để sau, khi có miền sản phẩm mới. Template spec gọn: phạm vi, actor × quyền × phạm vi dữ liệu (own/tenant/all), non-goals, câu hỏi mở kèm đề xuất | `_templates/08-srs.md` | Chưa có template spec | XS–S | TB |
| D19 | Để sau, khi bắt đầu Stripe hoặc đối tác. Mở rộng bảng "Data mapping" của booking-ui-spec: thêm field đối tác, transform, required. Cột PII lấy từ thẻ DM-6.1 | `skills/api-map` | Đã có bảng 2 lớp | XS | TB |
| D20 | Để sau. `docs/templates/implementation-note.md`, thêm 4 heading vào CLAUDE.md của Booking, TP, Infra | (OpenBA: mỗi output một template) | Quy tắc đã có, chưa có file mẫu | XS | Thấp |
| D21 | Để sau. Sinh trang quyền đọc được từ `PERMISSIONS` của Booking, và test "mọi route đều có permission" | `rules/17` | Ma trận nằm trong code, CIS đã có test | S | Thấp–TB |

Đã cân nhắc nhưng bỏ (chi tiết ở §5): RTM generator, lint từ mơ hồ, khối CR impact riêng, error-code catalog dạng tài liệu, `depends_on` có kiểu, template biên bản họp, chuẩn sơ đồ mới, checklist NFR ISO 25010.

## 5. Không nên học theo, và điểm yếu của OpenBA

| Không học | Lý do |
|---|---|
| Cài kit hoặc symlink 56 skill | Tên chung chung trùng với skill khác, đường dẫn gãy, phần lớn là vỏ sinh tự động |
| SRS IEEE 830 đầy đủ cho mỗi module | Quá nặng cho 1 kỹ sư. IEEE 830 đã bị thay thế |
| Semver và Revision History trên mọi trang | Trùng với git, dễ lệch, đẩy nội dung xuống dưới |
| Data dictionary, error matrix, RTM, RBAC viết tay | Bảng tay lệch khỏi code. Chính ví dụ của OpenBA đã tự mâu thuẫn |
| RTM generator bằng marker (L104/L204) | Chưa có rule nào có ID để truy. Phần issue → test → evidence thì grep đã trả lời được |
| Lint từ mơ hồ (L106/L210) | Không có trang spec nào để quét. Sẽ báo nhầm nhiều. D1 xử lý đúng gốc hơn |
| Khối CR impact riêng (L107/L209) | DoR đã có "Docs impact", Risk, Cost |
| Error-code catalog dạng tài liệu (L108/L205) | `errors.py` đã tách code và status. Chỗ lệch thật là các map `FRIENDLY` lặp ở frontend; nên gộp bằng một issue code |
| `depends_on` có kiểu (L110/L208) | Trùng với `related`. Đích BR/FR chưa tồn tại |
| Template biên bản họp (L114) | Gần như không có cuộc họp nào cần ghi. Quyết định đã đi qua trang duyệt |
| Chuẩn sơ đồ mới (L116/L218) | STYLE.md đã có Mermaid, giới hạn 15 node và C4 |
| Checklist NFR ISO 25010 (L117) | `03-scaling.md`, DM-9.6 và `finops.md` đã có số và cột "measured by" |
| Mã `ERR-[MODULE]-[HTTP]-[SEQ]` | Gắn ID với HTTP status. Mã snake_case của Booking tốt hơn |
| Con số NFR mặc định của OpenBA | Là số mặc định kiểu e-commerce, không có nguồn |
| `/jira`, `/confluence` đẩy thẳng | Trái quy tắc: Jira phải qua nháp và Nghiệp duyệt |
| `render_diagrams.py` và bộ D2/PlantUML/BPMN | Chỉ vẽ được 2 loại sơ đồ, lỗi thì im lặng |
| Dashboard và drift do LLM chấm | Không lặp lại được kết quả, không ghi SHA |
| Dịch skill sang tiếng Anh để tiết kiệm token | Chi phí nằm ở cấu trúc (CONTEXT 165 KB), không nằm ở ngôn ngữ |

**Điểm yếu của OpenBA:**
- Không có schema, linter hay CI. 19 rule chỉ là văn xuôi viết cho LLM.
- ID tự mâu thuẫn. Rule 03 và rule 11 lệch cột. Template phá rule.
- Không có vòng đời duyệt: thiếu status, người duyệt, ngày duyệt.
- README hứa nhiều hơn nội dung khoảng 3 lần. 34/47 template là stub. 3 template được tham chiếu nhưng không có. 14 skill có `\n` sai.
- Cách cài theo tài liệu làm gãy đường dẫn rules. Không có adapter cho Cursor hay Windsurf như đã quảng cáo.
- Truy vết dừng ở test case, không nối tới issue, PR hay verify live.
- Ngôn ngữ "tiếng Việt chuyên nghiệp" bị cố định trong 54 skill.
- Phần `diagram-design` vendor về thiếu file license MIT gốc.
- Kho rất non: một tác giả, 5 commit, không có test hay release.

## 6. Phương pháp

- **Đọc nguồn:** clone OpenBA-Kit vào `/home/nghiep/projects/AA-Ecosys/.tmp-session/openba/src`, chỉ đọc như dữ liệu. Không chạy script, installer hay `render_diagrams.py`.
- **Năm nhóm đọc:** rules, skills/templates, sơ đồ/handoff, hệ tài liệu AA, và tiêu chuẩn. Tiêu chuẩn đọc từ nguồn gốc công khai. ISO/IEEE trả phí nên chỉ đọc abstract; BABOK một phần cần đăng nhập.
- **Ứng viên:** 47 đề xuất (L101–L121 và L201–L226). Mỗi đề xuất qua 2 vòng kiểm:
  - **Kiểm sự thật:** đối chiếu cả file OpenBA lẫn file AA. 9/47 đúng hoàn toàn, 38 cần sửa; nhiều chỗ sai ở phía "AA thiếu", thực ra mình đã có.
  - **Kiểm độ hợp:** 3 hợp mạnh (L105, L118, L224). Phần lớn còn lại ở mức trung bình hoặc yếu, và nhiều cặp trùng nhau.
- **Sau kiểm:** 2 ứng viên giữ nguyên (L105, L215). Gộp trùng và sửa phạm vi thì còn 21 đề xuất (D1–D21): 13 nên áp dụng, 8 để sau. Ngoài ra có 8 nhóm bỏ.
- **Giới hạn:** số dòng và số byte lấy từ lúc đọc ngày 21/10/2026. Trạng thái của ISO 9001:2026 chưa xác nhận.
