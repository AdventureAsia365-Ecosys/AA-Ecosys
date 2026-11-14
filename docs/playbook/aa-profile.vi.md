---
id: GUIDE-14-aa-profile
title: Bản áp dụng AA của playbook
description: AA-Ecosys ánh xạ vào bộ kit dự án mới chung thế nào - luật, công cụ và ví dụ AA của từng pha nằm ở đâu, và luật nào chỉ riêng AA.
type: reference
status: draft
owner: nghiep
audience: [engineer, cto, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, CAT-01, GUIDE-02, GUIDE-08]
lang: vi
translation_of: docs/playbook/aa-profile.md
---

# Bản áp dụng AA của playbook

AA-Ecosys là ứng dụng tham chiếu của bộ kit (quyết định D12 của bộ kit): repo mới bắt đầu từ repo mẫu, và các repo AA
hiện có được chỉnh tay cho khớp khi đụng tới. Trang này là lớp phủ: nó trỏ từ mỗi trang chung tới nguồn AA chứa luật đó.
Khi hai bên lệch nhau, nguồn AA thắng cho việc của AA và playbook nhận một issue.

## Theo từng pha

| Pha | Nguồn AA |
|---|---|
| 1 Khám phá | Cổng quyết định của [ADR 0008](../adr/0008-new-app-integration-and-data-platform-rules.md) (app mới, module hay API client); các ghi chú nghiên cứu trong [`docs/research/`](../research/new-project-playbook/README.vi.md); [ADR 0019](../adr/0019-b2b-only-ecosystem-model.md) về mô hình kinh doanh |
| 2 Kiến trúc | [Kiến trúc hệ sinh thái](../ecosystem-architecture.md); [mục lục ADR và luật đặt ADR](../adr/README.md); [hợp đồng](../contracts/README.md); [data standards](../architecture/data-standards/README.md); [sở hữu schema](../database/schema-ownership.md); [sổ đăng ký dùng AI](../architecture/ai-use-register.md); [mô hình môi trường](../adr/0012-environment-model.md) |
| 3 Dựng khung | Mục 3 của ADR 0008, playbook mười hai bước cho một app mới (thiết kế, đăng ký chủ sở hữu, role, migration đầu tiên, tenancy, đọc qua hợp đồng, sự kiện, danh tính, dịch vụ nền tảng, dữ liệu cá nhân, vận hành, probe cách ly); [onboarding](../onboarding.md); [chuẩn gắn tag](../architecture/tagging-standard.md); [sổ đăng ký secret](../security/secrets-register.md) |
| 4 Xây dựng | [Definition of Ready](../templates/definition-of-ready.md); skill `aa-linear-issue`; PR template của repo gốc; luật migration MIG-1 tới MIG-14 trong [data standards Part A](../architecture/data-standards/01-engineering.md); lane song song trong skill `aa-session` |
| 5 Kiểm thử | [Chiến lược kiểm thử](../architecture/testing-strategy.md) (ARCH-10, bản AA của mẫu chiến lược kiểm thử); các workflow CI của từng app (UI smoke, eval regression); skill `aa-ui-verify`; [báo cáo UAT](../templates/uat-report.md); [probe cách ly](../ops/runbooks/isolation-probe.md) |
| 6 Phát hành | Skill `aa-ship` (Definition of Done, công cụ merge, cổng deploy, kiểm live); [ghi chú phát hành](../templates/release-note.md); [feature flag](../ops/feature-flags.md); skill `aa-jira-update` cho cập nhật kinh doanh |
| 7 Vận hành | [Mục lục vận hành](../ops/README.md); [xử lý sự cố](../ops/incident-response.md); [postmortem](../ops/postmortems/README.md); [diễn tập](../ops/drills/README.md); [FinOps](../ops/finops.md) |
| 8 Mở rộng | [Chuẩn mở rộng](../architecture/data-standards/03-scaling.md); [mô hình tài khoản gọn](../adr/0018-lean-aws-account-model.md); quyền merge theo giai đoạn (DM-11.5, mục 6.5 của sổ tay) |
| 9 Ngừng | Việc gỡ một tài khoản trong [ADR 0001a](../adr/0001a-retire-acc1-llm-on-acc3-only.md); ngừng tour trong [ADR 0015](../adr/0015-tour-liveness-and-retirement-propagation.md); [sổ bảng chết](../architecture/dead-table-registry.md); quy trình DRY RUN cho việc phá huỷ trong skill `aa-cis-schema` |

## Dung sai: giá trị của AA

| Dung sai | Giá trị của AA | Nguồn |
|---|---|---|
| Thời gian | 3 tới 5 issue mỗi phiên (8 tới 10 trong một phiên dài); tối đa 8 In Progress | Skill `aa-session` |
| Chi phí | Mỗi mục trả phí mới được báo giá và duyệt riêng; lượt chạy tốn tiền: khoảng 3, rồi tối đa khoảng 50 | Quy tắc làm việc W3 và W4 trong [sổ tay](../engineering-handbook.vi.md); [FinOps](../ops/finops.md); DM-10.6 |
| Phạm vi | Done-when đóng băng khi In Progress; một issue là một lát việc bàn giao được | Skill `aa-linear-issue` |
| Chất lượng | Mọi check xanh; Done = đã kiểm live | Skill `aa-ship` |
| Rủi ro | Lớp rủi ro được một agent độc lập review; bước phá huỷ sau DRY RUN và lời đồng ý của tech lead | DM-11.5; skill `aa-cis-schema` |
| Lợi ích | Câu hỏi kinh doanh tới chủ doanh nghiệp dưới dạng phương án bình tĩnh kèm khuyến nghị | Skill `ai-nghiep` |

Các quy tắc làm việc W1 tới W7 (tự quyết, không hỏi; không tự đặt cổng chặn; lượt chạy tốn tiền chỉ một tập nhỏ; báo
giá trước mọi mục trả phí; kiểm live trước khi khẳng định; một trang báo cáo cho chủ doanh nghiệp; mọi ngưỡng là setting
sửa được trên trang admin) nằm ở các mục [2.4](../engineering-handbook.vi.md#24-hai-luật-làm-việc-tự-quyết-không-hỏi-không-tự-đặt-cổng-chặn) (W1,
W2) và [2.5](../engineering-handbook.vi.md#25-thêm-các-quy-tắc-làm-việc-cho-agent) (W3 tới W7) của sổ tay.

## Hôm nay AA làm khác bộ kit chung ở đâu

| Bộ kit chung | AA hôm nay | Vì sao |
|---|---|---|
| `AGENTS.md` là nguồn chỉ dẫn | `.kiro/steering/` cùng `.claude/CLAUDE.md` | Tạm giữ (quyết định D7 của bộ kit); chỉnh cho khớp khi đụng tới |
| Skill chung bằng tiếng Anh | Skill AA bằng tiếng Việt với đường dẫn AA | Lớp phủ AA có thể giữ tiếng Việt (quyết định D8 của bộ kit); skill chung tới cùng AA-1103 |
| Một repo từ mẫu | Một repo gốc cộng năm repo app và Infra, dựng tay | Dựng trước khi có bộ kit; chỉnh tay cho khớp (D12) |
| Linear hoặc công cụ theo dõi việc khác | Linear gói Free, xuất và archive cuối phiên | Luật hạn mức, skill `aa-linear-issue` |
| Kênh cập nhật kinh doanh | Comment Jira soạn nháp, rồi tech lead duyệt | Skill `aa-jira-update` |

## Luật chỉ riêng AA (không có trong bộ kit)

Các phần riêng về sản phẩm và vận hành mà trang học liệu dạy nhưng bộ kit không mang: pipeline nội dung CIS, các domain
Booking và Partner, định tuyến tài khoản LLM, runbook migrate và exec cơ sở dữ liệu, và trang chi tiêu trong admin.
