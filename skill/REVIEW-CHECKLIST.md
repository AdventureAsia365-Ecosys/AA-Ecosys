# Checklist review khi bộ skill được upload lại

Claude Chat dùng checklist này khi Nghiệp upload bản đã qua Claude Code/Kiro.

## Cấu trúc

- [ ] Đủ 9 skill. Mỗi `SKILL.md` có frontmatter `name` + `description`. `name` khớp tên thư mục.
- [ ] Mỗi `SKILL.md` ≤ ~150 dòng; tổng bộ ≤ ~55 KB (bản cũ 114 KB).
- [ ] Mọi file trong `references/` được trỏ tới từ `SKILL.md` của skill đó. Không có file mồ côi.
- [ ] Không còn `VERIFY`, `SINH LẠI`, "lỗi thời", "SAI", "cũ", "ADDITIONS".

## Nội dung

- [ ] Không có số đang đổi: revision ECS, số tour, migration mới nhất, issue đang làm.
- [ ] Không chép bảng schema; `aa-cis-schema` trỏ `db-schema-reference.md`.
- [ ] Nhất quán giữa các skill: atom scope, tên service ECS, profile AWS, tên project Linear, quy ước `Refs AA-xxx`.
- [ ] Nhất quán với repo: đối chiếu ngẫu nhiên 5 path/route/bảng với VERIFY-LOG.
- [ ] Không còn rule mâu thuẫn với cách dùng công cụ hiện tại (ví dụ "Chat không viết code").
- [ ] Luật đã thành CI check (AA-725, AA-732 khi xong) đã được xoá khỏi skill.

## Trigger

- [ ] Description của 9 skill không chồng nhau. Đặc biệt: `aa-ship` với `aa-ui-verify`; `aa-session` với `ai-nghiep`.
- [ ] Thử 6 câu: "bắt đầu phiên S213", "merge PR này được chưa", "sửa trang Tenants", "tạo issue cho bug X", "báo chị Thư tiến độ Laos", "chạy lại Nepal". Mỗi câu kích đúng một skill chính.

## An toàn

- [ ] Không có secret, password, token, DSN, account number nhạy cảm (ngoài account ID AWS đã dùng công khai trong skill cũ).
- [ ] Các cổng duyệt còn nguyên: Jira nháp trước khi đăng; DRY RUN khi xoá; Terraform qua workflow.
- [ ] Không có chỉ dẫn cho agent tự thực hiện payment, xoá dữ liệu prod, hay đổi IAM mà không qua Nghiệp.

## VERIFY-LOG

- [ ] Mỗi mốc có kết luận và bằng chứng.
- [ ] Phần "đã thêm từ bản hiện tại" hợp lý: là nguyên tắc lâu dài, không phải nhật ký phiên.
- [ ] Câu hỏi mở được liệt kê để Nghiệp quyết.
