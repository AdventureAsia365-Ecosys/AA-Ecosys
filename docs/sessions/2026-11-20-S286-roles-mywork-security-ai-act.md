# S286 — 20/11/2026 — vai trò gọn bước 1, My work (CIS + Booking), nền vai trò tuỳ chỉnh, đánh giá bảo mật, dấu AI EU

**Tác nhân:** Claude Code (VS Code/WSL, Ultracode). 20/11 ~05:20 → ~12:20 +07. Đổi tài khoản claude.ai 1 lần (lane không mất
việc). MFA hết 1 lần (~06:00, nhập lại). Tối đa 5 lane code song song + workflow đánh giá 13 agent, không hết RAM (thấp nhất
~4,5 GB trống).

## Trạng thái

Done có bằng chứng live (Linear): AA-1134, AA-1145, AA-1146 (phần 1; phần 2 → AA-1148), AA-1127, AA-1051 (có giới hạn; T9
→ AA-1169), AA-1150, AA-1168, AA-1156, AA-1159. Còn mở có tiến độ: AA-1155 (nền T1–T4 + T4.1 xong; T5–T11 + T13/T14 sang S287),
AA-1161 (giai đoạn 1 xong; giai đoạn 2 viết lại lịch sử: cuối tuần này). Issue mới: AA-1162…AA-1168 (bảo mật / tuân thủ, từ
quyết định D1–D12), AA-1169 (T9 first-pass yield). Snapshot: [state-snapshot](../audits/2026-11-20-S286-session/state-snapshot.md).

## Thay đổi Codebase (merged)

- **AA-1134 / CI** — root #912 `14f709bd` (làm mới surface snapshot Catalogue + gắn 14 surface vào feature, TP-F004 retired),
  Infra #944 `ac7cac9f` (bỏ diff SES `delivery_options` không hội tụ → Terraform Drift xanh lại).
- **AA-1051** — CIS #1614 `fd79abd6` (`ctx.add_cost` chỉ nhận chi phí không phải LLM; guard AST + test tích hợp; 7 handler bỏ
  cộng đôi).
- **AA-1156** — CIS #1615 `206dab9f` (trang `/admin/my-work`), CIS #1620 `87cbdb2b` (bộ lọc theo URL sau khi bấm ô; spec
  đăng nhập một lần).
- **AA-1150** — Booking #288 `f8c89580` (kế toán đọc, tách quyền kích hoạt / công bố / duyệt dừng bán; maker tạo NCC
  inactive), CIS #1617 `7593f48d` (3 preset, "Show all roles", gỡ `booking-content_creator`; Add staff mặc định quyền thấp nhất).
- **AA-1155 (nền)** — root #914 `11e8d233` (spec `.kiro/specs/AA-1155-custom-staff-roles/` thí điểm AA-1137, ADR 0006a A14
  / A10f / A10g, contract `staff.roles.v1`, INT-083), Infra #946 `ebc8c1db` (nhóm `cis-custom` / `booking-custom`, A10f/A10g),
  CIS #1618 (mig **462**), Booking #289 (**bk-062**), Infra #947 `c5d5f938` (RLS allowlist), Infra #949 `f2f0d948` (PII
  allowlist), Booking #290 `cfc49b5a` (T4.1: `pricing.approve`, `b2b_desk.approve`, kích hoạt hotel/service; maker vẫn rút
  được yêu cầu chờ của chính mình).
- **AA-1159** — Booking #291 `b71fca9c` (dải My work, ô duyệt theo maker-checker, trang xem lại dừng bán), Booking #292
  `a4762dfa` (F4: picker không gọi danh bạ khi thiếu quyền; F5: nhãn ô xuống dòng; Booking admin :49).
- **AA-1161 (giai đoạn 1)** — root #913 `688678c3`, CIS #1616, Booking #287, Partner #368, TP #289, Infra #945 (guard
  `tools/repo/lean_guard.py` ở pre-push + CI; `compress_images.py`; bỏ 9 zip Lambda ~98 MB khỏi cây Infra).
- **AA-1168** — CIS #1619 `daec5413` (dòng công bố + dấu máy đọc WordPress / Facebook / bản xuất text), Partner #369
  `b163d81a` (4 cột AI ở CSV/XLSX My Tours), root #917 `1b2cd959` (AI Use Register v1.15 + test guard register).

- **AA-1168 follow-up (lane l11, luật giá trị chỉnh được trên admin)** — CIS #1621 `c6154c99` (mig **463** setting
  `cis.content.ai_disclosure` EN + VI + tag, maker-checker; mig **464** `publish_log.sent_message`), CIS #1622 `e29ee061`
  (WordPress / Facebook / export text đọc câu chữ từ setting, retry Facebook tìm theo nội dung đã gửi), Partner #372
  `44daca2e` (export My Content đọc setting qua BFF, bỏ bản chép tay).
- **Rà luật giá trị chỉnh được trên admin** (workflow 8 agent, 75 giá trị của các PR S286): 2 vi phạm. Câu công bố AI →
  l11 ở trên. Preset vai trò staff + CIS chưa có màn sửa vai trò → spec AA-1155 thêm T13 / T14, ADR 0006a bỏ câu "CIS
  không cần editor". Lane workflow luôn có lens review "settings, not hard-coded".

## Thay đổi Hạ tầng

- Terraform Apply Dev run 44643989086 (Infra #946): 2 nhóm WORKFORCE mới. Tài khoản E2E maker A10g tạo bằng
  `crm_dev_identity.py e2e-custom-maker --apply`.
- Migration áp qua chuỗi copy + apply: CIS **462**, **463**, **464**, Booking **bk-062** (đều contract, khi 3 bảng job rảnh).
- Dữ liệu Dev: sửa 9 dòng `shared.job.cost_usd` bị đếm đôi (DRY RUN → fingerprint → apply, 9,65 USD thừa); D1 AA-1127 đổi tên
  2 tenant test + xoá 1 ghi chú add-on (DRY RUN → apply → kiểm lại 0).
- Tạm cấp rồi thu hồi preset Pricing team cho `e2e-cis-cs@` (tech lead bấm, để chạy spec đăng nhập một lần).

## Bằng chứng verify

- AA-1145: proof trong transaction rollback trên DB live — trẻ em 20/40 USD, 24/12 on_request, phí huỷ 0/50/100 %.
- AA-1146: 11/12 bước (S1 batch 503 vì công tắc Batch tắt trên Dev, test CI phủ).
- AA-1127: đối sổ 26/26 PASS (AI tháng 11 tới 20/11: 46,75 USD; Anthropic 35,08), job Cost Explorer hằng ngày chạy (0,03 USD).
- AA-1150: kế toán đọc 200, `booking-content_creator` 0 người; preset do tech lead kiểm trên màn hình; spec đăng nhập một lần
  PASS 19,4 s (`live/05a`, `05b`, `data/05`).
- AA-1156: 4/4 ô khớp (nội dung) + Place cards 4.859 = 4.859 sau #1620. AA-1159: admin 10 ô, kế toán 6 ô, 18 = 18, 3 = 3.
- AA-1168: WordPress / Facebook test đăng → đọc lại → gỡ; bản xuất text; CSV qua UI (`live/aa1168-evidence.md`).
- AA-1161: guard chặn ảnh 620 KiB và `dist/x.zip`, cho qua ảnh 5 KiB.
- l11 (AA-1168 follow-up): setting đọc 200 qua BFF, export text có dòng công bố, bài Facebook test kết thúc bằng câu từ
  setting, `sent_message` lưu 1409 ký tự khớp bài, đã gỡ (`live/l11-ai-disclosure-setting-evidence.md`).
- Ảnh + JSON: [docs/audits/2026-11-20-S286-session/live/](../audits/2026-11-20-S286-session/live/).

## Đánh giá bảo mật DevSecOps

- Workflow 13 agent (6 khung × đánh giá + phản biện + tổng hợp): ISO 27001 45,8 %, SOC 2 44,0 %, ISO 42001 46,9 %, OWASP Top 10
  64,8 %, OWASP LLM/Agentic 66,7 %, DevSecOps 50,0 % (có trọng số). Kỹ thuật khá, hệ quản lý gần như chưa có.
- Bản đầy đủ (riêng tư): trang claude.ai `TcuXQUaCs9AhbLAqQhi8DH` (chia sẻ trong org); bản public:
  [docs/audits/2026-11-20-S286-devsecops-standards/](../audits/2026-11-20-S286-devsecops-standards/README.md).
- 12 quyết định D1–D12 (tech lead bấm trên trang) → issue AA-1162…AA-1168.

## Sự cố / phát hiện

- **Scrub corpus của Partner đỏ 20/11 01:50Z (12 lộ / 260 mẫu)**: code, corpus, dependency, guardrail (version 1) y hệt lượt
  xanh; bộ phát hiện PII của Bedrock Guardrails phía AWS thôi nhận một số tên người Việt trùng địa danh. Dev không có dữ liệu
  thật. Chạy lại tay (run 44661492997) vẫn đỏ → Partner #371 `e70b106d` thêm lớp kiểm tên người cục bộ sau Guardrails (CRM
  api :209); Scrub corpus trên main xanh lại (run 44667781727). GitHub AA-Partner#370 (App không có quyền comment issue).
- CIS admin 503 ~40 giây lúc 09:03: task Fargate **Spot** bị AWS thu hồi (`SpotInterruption`), không phải deploy. Tech lead giữ
  Spot cho 3 service staff web tới prod.

## Jira

Đã đăng sau khi tech lead duyệt (nháp: [jira-drafts.md](../audits/2026-11-20-S286-session/jira-drafts.md)):
PR-22 comment 10681, PR-25 comment 10682, PR-23 comment 10683.

## Quyết định của tech lead

- Duyệt danh sách S286; "tăng tốc" (5 lane); GPU không dùng làm RAM cho lane.
- Bảo mật D1–D12: D1 MFA admin giữ tắt tới prod; D2 dấu AI EU làm song song, không chặn pilot; D3 agent giữ quyền như hiện tại
  tới prod; D4 PR rủi ro cần tech lead duyệt từ khi pilot có dữ liệu thật + chặn xoá / force-push master ngay; D5 thay pentest
  bằng ZAP + tự đánh giá; D6 mở issue, business owner quyết thời điểm luật sư; D7 ISMS/AIMS-lite ngay, chứng nhận khi có
  trigger; D8 tài liệu bảo mật chi tiết lưu S3 riêng tư acc2; D9 GuardDuty khi pilot có dữ liệu thật; D10 rule rate CloudFront
  (~1 USD/tháng); D11 quét image miễn phí; D12 rule KEV/EPSS/CVSS. Tạo 6 issue AA-1162…AA-1167 (+ AA-1168 cho D2).
- AA-1051 Done-with-scope + AA-1169; AA-1161 giai đoạn 2 cuối tuần này (phiên riêng); Fargate Spot staff web giữ tới prod.
- Rotate Notion: S277–S280 sang `memory_archive_2026H9` (đủ 10 phiên).

## Còn lại

- AA-1155 T5–T11 (resolver Booking, vai trò tuỳ chỉnh CIS, trang ma trận quyền) — S287; giải mã token maker E2E cùng T5.
- AA-1161 giai đoạn 2 (cuối tuần), AA-1162…AA-1167, AA-1169 theo slot.
- CIS #1586 (dependabot) vẫn đỏ, Dependabot chưa tạo lại sau lệnh `recreate`.
- Báo cáo tuần PR-20 kỳ 6: Chủ nhật 22/11.

## Lưu ý kỹ thuật cho phiên sau

- Bài học S286 đã vào `skill/aa-lessons/lessons.md` (drift không hội tụ, surface Catalogue, công cụ pre-push thiếu, stamp
  integration, ship bằng `&`, finding authz minor, guardrail AWS đổi hành vi).
- gitleaks đã kiểm checksum ở `.tmp-session/gitleaks-8301/gitleaks` (đặt `AA_GITLEAKS`); shellcheck cho Infra ở scratchpad lane.
- App `aa-agent` không comment được issue GitHub (403 addComment).
- Lane workflow `tools/workflows/lane.js` luôn thêm lens review "settings, not hard-coded" (luật giá trị chỉnh được trên
  trang admin, có từ S278/S279; tech lead nhắc lại S286), kể cả khi lane truyền `lenses` riêng.
