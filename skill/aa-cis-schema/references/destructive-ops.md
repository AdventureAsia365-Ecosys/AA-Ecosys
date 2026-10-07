# Xoá bảng hoặc dữ liệu vĩnh viễn

Áp dụng cho: DROP TABLE/COLUMN, DELETE/TRUNCATE ngoài phạm vi một tour đang test, reset derived của một nước, xoá file/thư mục code "chết".

## STEP0 — có thật là chết không

1. Hỏi đúng câu: **"đường mới đã làm được việc này chưa?"**, không chỉ "còn ai dùng không" (AA-473).
2. FK qua `pg_constraint` (không dùng `information_schema`) → cần nhưng chưa đủ.
3. Quét riêng: số dòng, caller trong code (`git grep` tên bảng/cột), cột `*_id` trần không có FK (AA-479).
4. `git ls-files` cho thư mục nghi chết — `__pycache__` không track dễ gây nhầm "còn code".
5. Đọc comment của migration mới nhất liên quan đến bảng.
6. Grep tên bảng trong `tests/integration/` — CI replay toàn bộ migration trên postgres thật.
7. Cùng thư mục ≠ cùng số phận: quyết định từng file.

## Năm bước thực thi

1. **DRY RUN** — đếm đúng số dòng/bảng sẽ bị ảnh hưởng, đưa Nghiệp xem.
2. **Snapshot** — RDS snapshot hoặc export bảng, nếu có dữ liệu thật.
3. **SAVEPOINT** — chạy trong transaction, verify số liệu khớp DRY RUN.
4. **COMMIT** — chỉ khi Nghiệp đồng ý.
5. **Verify độc lập** — kết nối mới, re-query `information_schema`/đếm dòng. Không tin lại transaction cũ.

## Sau khi xoá

- Ở repo gốc AA-Ecosys: regenerate `docs/architecture/db-schema-reference.md` và thêm dòng vào `docs/architecture/dead-table-registry.md` (bảng, migration, ngày, lý do). PR riêng, link chéo với PR migration.
- Cập nhật skill **hai lần**: một lần trước apply (audit + go-ahead), một lần sau apply (số liệu thật).
- Ghi vào session block: bảng nào, migration nào, verify ra sao.
