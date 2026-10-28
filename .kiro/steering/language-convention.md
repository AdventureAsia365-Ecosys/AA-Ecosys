# Language convention (Nghiệp chốt 19/09/2026; bổ sung 19/10/2026, S243 N-7; đổi 28/10/2026, S255)

Bắt buộc mọi phiên trong workspace này:

- **Trao đổi/hội thoại với Nghiệp → tiếng Việt.** Toàn bộ chat, giải thích, tư vấn, câu hỏi,
  báo cáo tiến độ, tổng hợp trạng thái đầu/cuối phiên viết bằng tiếng Việt.
- **Mọi thứ khác → tiếng Anh.** Code, comment trong code, commit message, PR title/description,
  tên branch, Linear issue (title/description/comment), docstring, tên biến/hàm, tài liệu kỹ thuật.

## Ngoại lệ (giữ tiếng Việt)

- **Log session local** (`docs/sessions/*`) — giữ tiếng Việt (khớp lịch sử S181+).
- **Memory Notion** (`Program Brain/memory.md`) — giữ tiếng Việt.
- **Bản tư vấn / audit viết cho Nghiệp trong `docs/audits/`** — được viết tiếng Việt (S243, N-7).

## Tài liệu công ty: tiếng Anh + bản dịch `.vi.md` (S255, thay N-7 của S243)

- **Thân trang tài liệu trong `docs/` (catalog, guide theo vai trò, guide cho chủ doanh nghiệp) → chỉ tiếng Anh.**
  Không còn song ngữ EN–VI cạnh nhau / hai cột (luật N-7 cũ đã bỏ), không đoạn nào trộn hai thứ tiếng.
- **Bản tiếng Việt** (khi cần, ví dụ guide CEO) là file anh em `<cùng tên>.vi.md`: giữ nguyên front-matter của trang
  tiếng Anh (cùng `id`), thêm `lang: vi` và `translation_of: <đường dẫn trang tiếng Anh>`, `title` tiếng Việt, nội dung
  dịch đầy đủ, trung thành. Trang tiếng Anh là bản gốc: sửa nó trước, cập nhật `.vi.md` trong cùng PR.
  Lint `tools/docs/check_frontmatter.py` kiểm cặp này; `/admin/docs` hiện nút chuyển EN/VI. Chi tiết: `docs/STYLE.md` mục Language.
- **Tài liệu công ty gọi theo vai trò, không gọi tên người**: "tech lead", "business owner" (CEO), "engineer on duty".
  Log session, audit và memory giữ nguyên cách viết của chúng.

Mọi thứ khác giữ nguyên như trên.

Nói ngắn gọn: **nói chuyện tiếng Việt, viết ra sản phẩm (code/PR/Linear/docs) tiếng Anh; riêng log session, memory
Notion và audit tư vấn cho Nghiệp được tiếng Việt; bản tiếng Việt của một trang docs nằm ở file `.vi.md` riêng.**
