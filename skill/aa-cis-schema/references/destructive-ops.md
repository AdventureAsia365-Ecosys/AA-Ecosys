# Xoá bảng hoặc dữ liệu vĩnh viễn

Áp dụng cho: DROP TABLE/COLUMN/SCHEMA, DELETE/TRUNCATE ngoài phạm vi một tour đang test, reset derived của một nước, xoá
file/thư mục code "chết". Luật nền: data standards DM-3.8 (Dead Table Registry) và DM-3.9 (candidate → quarantine
`ALTER … SET SCHEMA retired` → drop sau ≥ 14 ngày; dòng có dữ liệu thật phải archive ra S3 trước). Bỏ bước nào của
DM-3.9 là **ngoại lệ, Nghiệp duyệt**, ghi vào registry (mẫu: 8 bảng tp-018, quyết định d14 S248).

## STEP0 — có thật là chết không

1. Hỏi đúng câu: **"đường mới đã làm được việc này chưa?"**, không chỉ "còn ai dùng không" (AA-473).
2. FK qua `pg_constraint` (không dùng `information_schema`) → cần nhưng chưa đủ.
3. Quét riêng: số dòng, bộ đếm đọc/ghi `pg_stat_user_tables`, caller trong code (`git grep` tên bảng/cột ở mọi repo đọc
   DB dùng chung), cột `*_id` trần không có FK (AA-479).
4. `git ls-files` cho thư mục nghi chết — `__pycache__` không track dễ gây nhầm "còn code".
5. Đọc comment của migration mới nhất liên quan đến bảng; kiểm view phụ thuộc (view tạo bằng `SELECT *` chặn DROP COLUMN).
6. Grep tên bảng trong `tests/integration/` — CI replay toàn bộ migration trên postgres thật.
7. Cùng thư mục ≠ cùng số phận: quyết định từng file.

## Năm bước thực thi

1. **DRY RUN** — đếm đúng số dòng/bảng sẽ bị ảnh hưởng, đưa Nghiệp xem. Ghi số vào Dead Table Registry trước apply.
2. **Snapshot / bản khôi phục** — RDS snapshot hoặc export, nếu có dữ liệu thật. File khôi phục ghi vào key **riêng, cố
   định** (không phải output của lần DRY RUN — chạy lại DRY RUN sẽ ghi đè). Migration có header `-- migrate: destructive`
   thì DB Migrate `apply` tự chụp `db-migrate-<key>-<run id>-<attempt>`, tag `aa:retain-until` = hôm nay + 30 ngày
   (Lambda expiry xoá sau đó). Nếu đó là bản lưu trữ duy nhất → dời `aa:retain-until` (hoặc `aa:retain=keep`) ngay sau
   apply và ghi id + hạn vào registry.
3. **SAVEPOINT** — chạy trong transaction, verify số liệu khớp DRY RUN.
4. **COMMIT** — chỉ khi Nghiệp đồng ý.
5. **Verify độc lập** — kết nối mới (lần chạy workflow khác), re-query catalog / đếm dòng. Không tin lại transaction cũ.

DROP bảng/cột là migration của repo chủ qua DB Migrate (không qua ECS exec). DELETE dữ liệu trên bảng CIS có thể chạy
bằng script ECS exec (`cis_app`); trên schema app khác → DB Migrate `run-script`.

## Sau khi xoá

- Repo gốc AA-Ecosys: merge PR `bot/db-schema-reference` (DB Schema Dump tự mở sau apply); cập nhật dòng của bảng trong
  `docs/architecture/dead-table-registry.md` (run apply, run verify, snapshot); nếu schema có trang ERD thiết kế
  `enforce=true` thì sửa trang đó cùng đợt.
- Ghi vào session block: bảng nào, migration nào, verify ra sao.
