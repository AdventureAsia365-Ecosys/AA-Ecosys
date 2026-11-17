# Tóm tắt audit tài liệu S283 (AA-1124)

- Đã đọc và đối chiếu với hệ thống thật (17/11/2026) **361 trang tài liệu sống** trong repo gốc và 5 repo con (thêm 40 bản `.vi.md` có bản ghi riêng → 401 bản ghi). Bỏ qua có chủ đích: log phiên, audit, implementation notes, Linear export, file sinh tự động.
- Kết quả: **24 trang sai** (làm theo sẽ ra kết quả sai hoặc bước không an toàn), **222 trang lệch một phần**, 10 trang mồ côi, 1 trang chỉ hỏng link, 144 trang còn đúng. Mức độ: **35 cao**, 121 trung bình, 108 thấp. Tổng 908 câu lỗi thời, 64 link hỏng, 226 chỗ mâu thuẫn.
- Gốc rễ là 8 thay đổi gần đây chưa lan vào tài liệu: acc1 phục vụ Bedrock trước acc3 (S278), bỏ nửa B2C (AA-1046), bỏ Vercel, Terraform dời vào `modules/environment/`, portal gộp vào CRM web, repo gốc/Infra đã public, backup RDS 14 ngày, luồng migration ADR 0017.
- Đề xuất ưu tiên (đều thuộc AA-1118):
  1. Dọn ngay thông tin không được để trong repo public (e-mail cá nhân, ID tài nguyên, tên người, ghi chú agent lạc trong ADR) — XS.
  2. Sửa file chỉ dẫn agent (CLAUDE.md các repo, steering Kiro của TripPlanner, skill ai-nghiep/aws, aa-ui-verify, aa-ecosys-repos, kiro-delegate, ecs-exec-pattern của CIS) — 16/35 lỗi cao nằm ở đây, có chỗ bảo destroy root acc1 đang chạy — M.
  3. Sửa trang pháp lý / bảo vệ dữ liệu: runbook DSAR (saga đã chạy, bảng `booking.customers` vẫn còn), consent query, ADR 0012 của CIS và AI Use Register (dữ liệu tenant có thể ra API vendor) — M.
  4. Sửa runbook ops có địa chỉ Terraform hoặc bước sai: crm-keys, secret-rotation (`module.environment.*`), pilot-agency-onboarding, 5xx-spike, llm-cost-spike, các runbook rollback — L.
  5. Viết lại runbook cho staff theo mô hình B2B (booking-admin, tripplanner, cis-admin + bản `.vi.md`), rồi quét một lượt "acc1 trước acc3" trên các trang kiến trúc — L.
- 19 việc cần sửa code/cấu hình chứ không phải sửa tài liệu (ví dụ helper rollback ECS từ chối 2 service admin, `bk_inquiry_pull` còn trong danh sách miễn gate, trang `/sign-in` của TripPlanner trái ADR 0019) — liệt kê ở mục 4.1 của README, cần duyệt trước khi tạo issue.
