# Nguyên tắc rút ra từ sự cố thật

Mỗi dòng: nguyên tắc — bằng chứng. Khi một nguyên tắc đã thành CI check hoặc code guard, xoá dòng đó.

## Verify và "Done"

- Build pass ≠ chạy đúng. Verify trên domain thật (curl 200 + shape) — S212: SEO 500 tưởng 401, nút Live view không hiện, đếm Thailand sai.
- Có phép kiểm ≠ phép kiểm đúng. Check mang tên "invented/fabricated" phải đối chiếu source thật — 30/07: `ITIN_MEAL_INVENTED` chỉ dò từ khoá output.
- Atom hoá không có nghĩa là không bịa. Atom cần grounding riêng — 30/07, 1/2 mẫu có chi tiết ngoài nguồn.
- Trước khi viết validator mới, tìm cái đã có ở nhánh khác — `find_novel_numeric_claims()` đã tồn tại khi cần quét 58 tour.
- Đọc code thật trước khi đặt giả thuyết — S65 mất nhiều lượt vì giả định có node "finalize" không tồn tại.

## Vận hành

- Không merge/deploy backend khi job đang chạy — S212: deploy giết 16 job S1 của wave Thailand.
- Task chạy trong process API chết khi deploy và không hiện trên trang Jobs — gốc của AA-723.
- Deploy phải cập nhật cả worker — S211: worker kẹt task-def `:1`, chạy code cũ.
- Thêm module top-level phải thêm `COPY` vào Dockerfile và path filter `deploy-dev.yml` — S210.
- Merge PR có `[AA-xxx]` tự đóng issue → dùng `Refs AA-xxx` — S207 phải mở lại AA-653, AA-708.

## Pipeline và chất lượng

- Regenerate không cứu được lỗi nằm ở input (raw nghèo) hay prompt (writer tone) — AA-724.
- Repair step có thể tạo lỗi mới (flag_fix thêm forbidden word) → guard sau repair — AA-641.
- Nhiễu giữa hai lần chạy cùng prompt có thể lớn hơn hiệu ứng của thay đổi prompt — AA-346. Cần đo lặp, không kết luận từ 1 lần.
- Đếm rerun theo distinct tour: master / review-pending / not-run; không đếm superseded; `ingested` trong review ≠ chưa chạy.
- Jev fail-open: `llm_call_log` ghi cả lần lỗi → đọc `decision_log.zone`, không dùng số call làm bằng chứng.

## Dữ liệu

- `pg_constraint` FK-graph là điều kiện cần, không đủ — cột `tenant_id` trần không có FK vẫn liên kết ở tầng app (AA-479).
- Cùng thư mục không cùng số phận — xoá từng file, verify import chain riêng (AA-477).
- 0 row không chứng minh "chưa từng dùng" — kiểm `git ls-files`.
- Trước DROP TABLE: grep tên bảng trong `tests/integration/` (CI replay migration thật).
- STEP0 phải hỏi "đường mới đã làm được việc này chưa", không chỉ "còn ai dùng không" (AA-473).

## Frontend

- FastAPI: không đặt helper giữa `@router.get` và `async def` → decorator bind nhầm, endpoint 422 (S211, #559).
- Next 16 React Compiler: lint lỗi `set-state-in-effect` → dùng lazy init / key-remount / useMemo / react-query.
- Luôn chạy `npm run build` đầy đủ; tsc bắt lỗi prop mà eslint bỏ sót.
- Markdown làm hỏng dấu `_` trong tên env (`NEXT_PUBLIC_...`) → sửa trong editor, không sửa bằng sed/heredoc.
