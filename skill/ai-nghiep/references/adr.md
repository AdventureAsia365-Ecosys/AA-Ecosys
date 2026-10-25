# ADR

## Khi nào phải viết

Đề xuất ADR ngay trong phiên khi: chọn service/lib A thay vì B; đổi kiến trúc, ranh giới app hoặc scope dữ liệu (ví dụ
atom platform-wide ↔ per-tenant); quyết định schema (JSONB vs relational); đổi pattern bảo mật, auth hoặc quyền merge.
Đổi kiến trúc/ranh giới thì cập nhật `CONTEXT.md` của repo liên quan trong cùng thay đổi.

## Nơi lưu và đánh số

ADR sống trong repo, file `docs/adr/NNNN-<slug>.md` (4 chữ số). Đặt ở repo nào — hỏi "nếu đảo quyết định này thì repo
nào phải sửa?":

- Từ 2 repo trở lên (hợp đồng giữa app, DB/schema dùng chung, account, identity, quy tắc cấp hệ sinh thái) →
  `AA-Ecosys/docs/adr/` (root).
- Chỉ hạ tầng (IAM, network, Terraform root) → `AA-CIS-Infra/docs/adr/`.
- Chỉ trong 1 app → `apps/<repo>/docs/adr/`. ADR app triển khai một ADR root thì trích dẫn nó (ví dụ Booking
  `0001-implements-root-0004`, Partner `0001-implements-root-0010`).

Số đếm độc lập theo từng repo. Root: lấy số ở dòng "Next free root numbers" trong `docs/adr/README.md` và thêm dòng vào
bảng của README; số giữ chỗ (Reserved) chỉ dùng khi ADR trích dẫn issue giữ chỗ. CI root kiểm việc này
(`tools/adr/check_adr_numbers.py`). Sửa đổi một ADR đã có = file riêng `<NNNN>a-<slug>.md` (chữ cái kế tiếp), ADR gốc
thêm dòng trỏ sang và cột Status ghi "amended by …".

## Format

```markdown
# ADR NNNN — <title>

- **Status:** Proposed (<dd/mm/yyyy>, S<nnn>) | Accepted (<ngày>, ai duyệt) | Superseded by ADR …
- **Scope:** <repo / app / phần hệ thống chịu ảnh hưởng>
- **Amends / Implements:** <ADR liên quan, nếu có>

## Context
Vì sao cần quyết định; bằng chứng (issue, số liệu).

## Decision
Làm gì, phạm vi (đánh số từng quyết định nếu nhiều).

## Consequences
- (+) …
- (−) … (đánh đổi đã chấp nhận)

## Alternatives considered
- Option — vì sao không chọn
```

ADR viết bằng tiếng Anh. Khi một ADR bị thay: sửa Status của ADR cũ thành `Superseded by …` và cập nhật bảng README.

## Khung chọn công nghệ

1. Đã có trong stack chưa? Tái dùng thắng viết mới.
2. Chi phí ước tính bằng số thật (dịch vụ AWS mới: nêu chi phí/tháng trước khi apply).
3. Có đảo ngược được không?
4. Hợp quy mô hiện tại không (solo, một môi trường AWS)?

## Đã khoá (không bàn lại nếu không có bằng chứng mới)

| Quyết định | ADR |
|---|---|
| Kiến trúc đích của hệ sinh thái (account, ranh giới app, dịch vụ dùng chung) | root 0001 (siết bởi 0008) |
| Chỉ CIS ghi nội dung, app khác đọc qua view | root 0002 |
| Một durable job model cho toàn hệ; mỗi owner một bảng job theo template chung | root 0003 + 0003a |
| AA-Booking: stack, runtime trên acc2; supply data ở Booking, nội dung supply cho khách ở CIS | root 0004 + 0004a |
| Identity hệ sinh thái trên Cognito (staff, tenant, traveller; pool partner có MFA) | root 0006 + 0006a/b |
| Quy tắc tích hợp app mới và nền tảng dữ liệu | root 0008 (+ 0008a cho CRM) |
| AA-Partner: một app cho đại lý (CRM + tenant portal) | root 0010 |
| Tour liveness: một trạng thái served do CIS sở hữu, tombstone/outbox cho app khác | root 0015 |
| Atom platform-wide (Segment/Score/Route/Hub cũng platform-wide theo CONTEXT.md) | AA-CIS-App 0001, 0003 |
| Model Catalog + Converse adapter; stage route có fallback chain + shadow | AA-CIS-App 0005, 0006 |
| Writer Anthropic, judge khác vendor; stage validate dùng vendor nào cũng được | AA-CIS-App 0006 §5 + 0008 |
| Jev verdict được phép tác động (enforce) | AA-CIS-App 0007 |
| Writing memory có cổng release, không fine-tune | AA-CIS-App 0010 |

Danh sách đầy đủ và trạng thái (Proposed/Accepted): bảng trong `docs/adr/README.md` của từng repo.
