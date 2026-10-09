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
- **Một giá trị được tính ở hai đường code thì phải dùng chung một hàm** — `_audit_from_judge` tự đặt "flagged nếu có mã", bỏ qua `derive_status`, nên FACT_CHECK (cưỡi voi) thành "lỗi brand sửa được" thay vì `manual_check`: flag_fix chạy không có gì để sửa, người duyệt thấy sai lý do (S218 India, 8 tour). Bắt bằng: grep chỗ gán cùng một field trạng thái; test cùng input qua mọi đường.
- **Đo lại sau khi sửa trước khi làm thêm** — định "bỏ seo_meta khỏi flag_fix", đo lại thấy AA-740 đã tự giảm flag_fix 79% → 25% (seo_meta 488/681 → 4/66), không cần code thêm (S218).
- **Một model mạnh hơn không sửa được từ mà prompt/brand list cấm nhưng ngôn ngữ dùng tự nhiên** — Sonnet retry (AA-736) vẫn viết "explore" → thay từ tất định rẻ và chắc hơn (S218).
- Nhiễu giữa hai lần chạy cùng prompt có thể lớn hơn hiệu ứng của thay đổi prompt — AA-346. Cần đo lặp, không kết luận từ 1 lần.
- Đếm rerun theo distinct tour: master / review-pending / not-run; không đếm superseded; `ingested` trong review ≠ chưa chạy.
- Jev fail-open: `llm_call_log` ghi cả lần lỗi → đọc `decision_log.zone`, không dùng số call làm bằng chứng.

## Job runner

- **Cap theo kind phải nhỏ hơn tổng slot của worker** — s1_rewrite cap 4 = `max_parallel` 4 → chiếm hết slot, a3_atomize (cap 1) không chạy được suốt pha rewrite (S217/S218, AA-737). Bắt bằng: test `test_aa737_worker_throughput` (cap s1 + cap a3 < slot).
- **Tăng slot thì tăng cả thread executor và pool DB** — LangGraph chạy node sync trên default executor (6 thread ở 0.5 vCPU); thêm slot mà không thêm thread thì nghẽn âm thầm (AA-737).
- **Job chạy song song bên trong (asyncio.gather / Semaphore) không được dùng chung MỘT connection** — A3/recompute chạy trên `_SingleConnAsPool`, trong khi gate Jev gọi `decide()` 8 luồng → "another operation is in progress" hàng nghìn lần mỗi recompute, decide fail-open → loại transit/demand/landing đổi theo từng lần chạy, route lật version (có identity 14 version) (S219). Bắt bằng: CloudWatch đếm `decide_config_unavailable` = 0 sau mỗi recompute; job mở pool thật (`open_job_pool`).
- **Script theo dõi wave phải chịu được lỗi mạng tạm thời** — 1 lần 502 từ API Gateway làm runner local chết giữa wave (job vẫn chạy). Poll trong try/except, lưu state để resume (S218).

## Dữ liệu

- `pg_constraint` FK-graph là điều kiện cần, không đủ — cột `tenant_id` trần không có FK vẫn liên kết ở tầng app (AA-479).
- Cùng thư mục không cùng số phận — xoá từng file, verify import chain riêng (AA-477).
- 0 row không chứng minh "chưa từng dùng" — kiểm `git ls-files`.
- Trước DROP TABLE: grep tên bảng trong `tests/integration/` (CI replay migration thật).
- **File khôi phục (restore) phải nằm ở key riêng, cố định — không phải output của lần DRY RUN** — script AA-744 ghi snapshot ra `s219_aa744_{MODE}.json`; chạy lại DRY RUN sau khi apply đã ghi đè file "dry" đang là file khôi phục của 924 atom (S219). Cứu được nhờ bản `apply_atoms` + S3 versioning. Bắt bằng: bước apply copy snapshot sang `scripts/restore/<issue>_<ngày>.json` trước khi ghi DB.
- STEP0 phải hỏi "đường mới đã làm được việc này chưa", không chỉ "còn ai dùng không" (AA-473).
- Bước "best-effort" nuốt lỗi bằng `logger.warning` thì phải để lại dấu vết trong kết quả job — không thì lỗi chạy âm thầm hàng ngày: segment không được dựng cho 566 tour từ 05/10 trong khi mọi job `a3_atomize` báo thành công (S218, AA-695). Báo cáo wave phải đếm sản phẩm đầu ra (segment/ranking/route theo tour), không chỉ trạng thái job. Bắt bằng: wave report đếm `tours_with_segment` theo nước.
- Một UPDATE đổi khoá con (`SET segment_id = …`) trên bảng có PK ghép dễ đụng PK khi dòng đích đã có — dùng INSERT … ON CONFLICT DO NOTHING + DELETE (S218, AA-695).
- Index phủ (`INCLUDE`) chỉ có tác dụng khi truy vấn KHÔNG chạm cột nào ngoài index — kể cả `count(l.id)`. Thêm index xong phải EXPLAIN lại, thấy `Index Only Scan` + `Heap Fetches: 0` mới tính là xong — summary Jev vẫn 22 s sau migration 205 vì `count(l.id)` (S218, AA-660). Bắt bằng: EXPLAIN (ANALYZE, BUFFERS) trước/sau.

## Frontend

- **Trang list phải phân trang và lấy option filter ở server** — Review Queue gọi API không kèm `page_size` (mặc định 20) rồi phân trang client trên 20 dòng → luôn 1/1, chọn 100/page vô tác dụng, dropdown nước chỉ có nước của 20 dòng; Master Content cũng vậy (S218, AA-739). Bắt bằng: aa-ui-verify với dữ liệu > 1 trang: chọn page size lớn, sang trang 2, đếm option filter.
- **Mọi bước chờ trong Playwright phải có trần riêng** — `waitForFunction(fn, { timeout })` đặt options sai vị trí (là tham số thứ 3, sau `arg`) nên chờ vô hạn; `networkidle` không bao giờ tới trên trang có polling; cả hai đốt hết 60 s test timeout ở Master Content, trong khi trang hiển thị bình thường (S220, AA-732). Bắt bằng: chạy smoke thật trên Dev trước khi merge (`BASE_URL=… --project=smoke`), đo thời gian từng bước khi timeout.
- **Selector smoke không giả định layout mới** — trang legacy không có `<main>`, nên `main table tbody tr` không bao giờ khớp dù bảng có 20 dòng (S220, AA-732).
- **Workflow CI phải chạy thật một lần trước khi báo xong** — `npm ci` ở root fail vì `package-lock.json` root bị gitignore; review + test local không lộ ra được. `workflow_dispatch --ref <branch>` chạy được bản workflow trên branch, miễn workflow đã có trên main (S220, AA-732).
- **Tràn ngang mobile: đo phần tử gây tràn rồi mới sửa, không đoán** — vòng 1 Kiro sửa split + KPI grid nhưng smoke vẫn y nguyên `scrollWidth 1136`; thủ phạm thật là `<select>` lọc tour tự rộng theo option dài nhất (~1000px). `<select>` có option là tên tour phải có `maxWidth: 100%` + `minWidth: 0` (S221, AA-601). Bắt bằng: smoke 390px assert `scrollWidth <= innerWidth`; khi đỏ, liệt kê phần tử ngoài cùng có `getBoundingClientRect().right > innerWidth` rồi mới sửa.
- FastAPI: không đặt helper giữa `@router.get` và `async def` → decorator bind nhầm, endpoint 422 (S211, #559).
- Next 16 React Compiler: lint lỗi `set-state-in-effect` → dùng lazy init / key-remount / useMemo / react-query.
- Luôn chạy `npm run build` đầy đủ; tsc bắt lỗi prop mà eslint bỏ sót.
- Markdown làm hỏng dấu `_` trong tên env (`NEXT_PUBLIC_...`) → sửa trong editor, không sửa bằng sed/heredoc.
