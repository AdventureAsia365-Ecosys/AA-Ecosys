# ADR

## Khi nào phải viết

Đề xuất ADR ngay trong phiên khi: chọn service/lib A thay vì B; đổi kiến trúc hoặc scope dữ liệu (ví dụ atom platform-wide ↔ per-tenant); quyết định schema (JSONB vs relational); đổi pattern bảo mật hoặc auth.

## Nơi lưu và đánh số

ADR sống trong repo, file `docs/adr/NNNN-*.md` (số 4 chữ số, bắt đầu `0001`). Đặt ở repo nào tùy phạm vi — kiểm bằng câu hỏi "nếu đảo quyết định này thì repo nào phải sửa?":

- Ảnh hưởng từ 2 repo trở lên (hợp đồng giữa app, DB/schema dùng chung, account, Model Gateway cấp hệ sinh thái) → `AA-Ecosys/docs/adr/` (root).
- Chỉ hạ tầng (IAM, network, Terraform root) → `AA-CIS-Infra/docs/adr/`.
- Chỉ trong 1 app → `apps/<repo>/docs/adr/`.

Số đếm độc lập theo từng repo, nên có thể trùng số giữa root và app — ADR repo con phải trích dẫn ADR root mà nó triển khai. Chi tiết quy ước ở steering `session-workflow.md`.

## Format

```markdown
# ADR-2026-NNN: <title>
Date: YYYY-MM-DD · Status: Proposed | Accepted | Superseded by ADR-…

## Context
Vì sao cần quyết định; bằng chứng (issue, số liệu).

## Decision
Làm gì, phạm vi.

## Consequences
- (+) …
- (−) … (đánh đổi đã chấp nhận)

## Alternatives considered
- Option — vì sao không chọn
```

Khi một ADR bị thay: sửa `Status: Superseded by …` ở ADR cũ, và thêm banner ở trang Notion cũ trỏ sang trang mới.

## Khung chọn công nghệ

1. Đã có trong stack chưa? Tái dùng thắng viết mới.
2. Chi phí ước tính bằng số thật.
3. Có đảo ngược được không?
4. Hợp quy mô hiện tại không (solo, một môi trường AWS)?

## Đã khoá (không bàn lại nếu không có bằng chứng mới)

| Quyết định | ADR |
|---|---|
| Kiến trúc đích của hệ sinh thái (account, ranh giới app) | root 0001 |
| Chỉ CIS ghi nội dung, app khác chỉ đọc | root 0002 |
| Một durable job model (Postgres queue + worker) cho toàn hệ sinh thái | root 0003 |
| Atom platform-wide (Segment/Score/Route/Hub cũng platform-wide theo CONTEXT.md) | AA-CIS-App 0001 |
| Live writing progress qua Redis poll (không SSE) | AA-CIS-App 0004 |
| Model Catalog + Converse adapter | AA-CIS-App 0005 |
| Stage routes: fallback chain + shadow model | AA-CIS-App 0006 |
| Jev verdict được phép tác động (enforce) | AA-CIS-App 0007 |
| Judge khác vendor với writer | AA-CIS-App 0006 (stage route) |

Danh sách đầy đủ: `AA-Ecosys/docs/adr/` + `apps/AA-CIS-App/docs/adr/`.
