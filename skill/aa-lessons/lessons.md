# Nguyên tắc rút ra từ sự cố thật

Cách ghi/đọc: xem `SKILL.md` (aa-lessons). Mỗi dòng: **nguyên tắc** — triệu chứng → nguyên nhân (phiên, issue). Bắt bằng: … .
Khi một nguyên tắc đã thành CI check hoặc code guard, xoá dòng đó.

## Cách làm việc

- **Kiểm tiền đề của issue bằng dữ liệu thật trước khi thiết kế** — AA-738 ghi "writer phát forbidden word lõi"; query 9 tour thật cho thấy 0 từ lõi, 100% là từ của brand list (explore/package/nestled) → thiết kế khác hẳn (S218). Bắt bằng: 1 query mẫu trên dữ liệu thật trước khi code.
- **Đo trước khi chỉnh hiệu năng** — AA-737 định tăng cap s1_rewrite; đo `shared.job` cho thấy nút thắt là slot worker dùng chung (`max_parallel=4`) làm a3_atomize đói 59 phút (S218). Bắt bằng: timeline running/queued theo kind từ `shared.job`.
- **Siết một gate thì phải đối chiếu quyết định cũ và đường sửa hiện có** — AA-736 biến mã độ dài meta thành chặn Master, nhưng AA-608 từng chủ ý để chúng "soft" vì flag_fix không đảm bảo sửa được → S218 Sri Lanka 11 tour điểm ≥7 kẹt review. Bắt bằng: với mỗi code chuyển sang hard-block, chỉ ra bước nào sửa được nó một cách tất định.

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
- **Bước sửa tất định phải chạy sau lần sửa LLM cuối cùng, không chỉ lúc viết** — strip forbidden lúc viết vẫn để lọt vì flag_fix/re-repair seo_meta viết lại "Explore …" (S218, 8 tour). Bắt bằng: test gọi `revalidate_node` với nội dung vừa bị repair đưa từ cấm vào.
- **Validator chỉ quét nội dung do writer viết, không quét cả dict** — `json.dumps(generated)` quét luôn `seo_keywords_used` (từ khoá DFS "cheap summer getaways") → FORBIDDEN_WORD không sửa được, chặn Master vĩnh viễn, 13/538 bản (S218, AA-738). Bắt bằng: liệt kê field metadata và loại khỏi mọi scan nội dung.
- **Dữ liệu lưu phải là dữ liệu đã được validate** — seo_meta bị cắt lúc ghi DB nên bản lưu 153 ký tự mà mã vẫn là SEO_META_TOO_LONG, chẩn đoán dễ sai (S218). Bắt bằng: khi điều tra mã độ dài, so `issues` của validate, đừng đo field đã lưu.
- **Một model mạnh hơn không sửa được từ mà prompt/brand list cấm nhưng ngôn ngữ dùng tự nhiên** — Sonnet retry (AA-736) vẫn viết "explore" → thay từ tất định rẻ và chắc hơn (S218).
- Nhiễu giữa hai lần chạy cùng prompt có thể lớn hơn hiệu ứng của thay đổi prompt — AA-346. Cần đo lặp, không kết luận từ 1 lần.
- Đếm rerun theo distinct tour: master / review-pending / not-run; không đếm superseded; `ingested` trong review ≠ chưa chạy.
- Jev fail-open: `llm_call_log` ghi cả lần lỗi → đọc `decision_log.zone`, không dùng số call làm bằng chứng.

## Job runner

- **Cap theo kind phải nhỏ hơn tổng slot của worker** — s1_rewrite cap 4 = `max_parallel` 4 → chiếm hết slot, a3_atomize (cap 1) không chạy được suốt pha rewrite (S217/S218, AA-737). Bắt bằng: test `test_aa737_worker_throughput` (cap s1 + cap a3 < slot).
- **Tăng slot thì tăng cả thread executor và pool DB** — LangGraph chạy node sync trên default executor (6 thread ở 0.5 vCPU); thêm slot mà không thêm thread thì nghẽn âm thầm (AA-737).
- **Script theo dõi wave phải chịu được lỗi mạng tạm thời** — 1 lần 502 từ API Gateway làm runner local chết giữa wave (job vẫn chạy). Poll trong try/except, lưu state để resume (S218).

## Dữ liệu

- `pg_constraint` FK-graph là điều kiện cần, không đủ — cột `tenant_id` trần không có FK vẫn liên kết ở tầng app (AA-479).
- Cùng thư mục không cùng số phận — xoá từng file, verify import chain riêng (AA-477).
- 0 row không chứng minh "chưa từng dùng" — kiểm `git ls-files`.
- Trước DROP TABLE: grep tên bảng trong `tests/integration/` (CI replay migration thật).
- STEP0 phải hỏi "đường mới đã làm được việc này chưa", không chỉ "còn ai dùng không" (AA-473).

## Frontend

- **Trang list phải phân trang và lấy option filter ở server** — Review Queue gọi API không kèm `page_size` (mặc định 20) rồi phân trang client trên 20 dòng → luôn 1/1, chọn 100/page vô tác dụng, dropdown nước chỉ có nước của 20 dòng; Master Content cũng vậy (S218, AA-739). Bắt bằng: aa-ui-verify với dữ liệu > 1 trang: chọn page size lớn, sang trang 2, đếm option filter.
- FastAPI: không đặt helper giữa `@router.get` và `async def` → decorator bind nhầm, endpoint 422 (S211, #559).
- Next 16 React Compiler: lint lỗi `set-state-in-effect` → dùng lazy init / key-remount / useMemo / react-query.
- Luôn chạy `npm run build` đầy đủ; tsc bắt lỗi prop mà eslint bỏ sót.
- Markdown làm hỏng dấu `_` trong tên env (`NEXT_PUBLIC_...`) → sửa trong editor, không sửa bằng sed/heredoc.
