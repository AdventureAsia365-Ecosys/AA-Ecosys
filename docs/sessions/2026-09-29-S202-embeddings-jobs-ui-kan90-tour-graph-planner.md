# S202 — Batch embedding PAA, UI giám sát job, đóng KAN-90, Tour Graph + planner PR-11 (29/09/2026)

**Tác nhân:** Claude Code (VSCode, WSL). **Người duyệt:** Nghiệp.

## Trạng thái

| Việc | Kết quả |
|---|---|
| **AA-688** gộp embedding Cohere cho PAA landing | Done. ~16 giờ → ~4.5 phút, kết quả khớp 77/77 rồi 2506/2506 (#467) |
| **AA-687** UI giám sát job runner | Done. Trạng thái worker lưu Postgres (mig 178); trang Jobs có worker health, progress/ETA, drawer chi tiết, deep link; link từ các trang domain; ETA verify live (job 5142e76b) (#468–#470, #473, #474) |
| **KAN-90** (chị Thư) | Đủ 3 việc đã hứa. T2 tenant không gọi DFS (#471); trần DFS theo ngày chỉ cảnh báo, không dừng (#472); màn hình Budgets (#475, verify prod: 3 dòng). Đã trả lời 3 câu hỏi (comment 10428) và báo cáo xong (comment 10429) |
| **AA-675** trích ngày tour (`tour_day`) | Done. Lambda op `tour_days` / `relink`; vị trí xác định bằng model + Mapbox xác nhận |
| **AA-673** Tour Graph | Done. 56 tour, 299 điểm đến, 379 cạnh, 3.871 leg, 1.748 cặp điểm nối; truy vấn "hàng xóm Paro" 8.5 ms |
| **AA-674** ghép nhiều tour + gợi ý theo tuyến | In Progress. Backend đủ (gợi ý theo tuyến, coverage, `/browse/routes`, activity theo điểm dừng, thêm/bớt ngày, bộ lọc); UI v1 đã lên prod; Nghiệp review "chưa mượt, chưa giống Trip.com" |
| **AA-689** (epic mới) planner kiểu Trip.com trên dữ liệu AA | In Progress. Kế hoạch 4 giai đoạn A–D; Giai đoạn A đang dở trên nhánh WIP |

## Thay đổi Codebase

**AA-CIS-App** (đều đã merge; Dev chạy taskDef :374)
- #467 `perf`: batch embedding Cohere 96 text/lần, giãn 3.5 s mỗi lần (quota 20 req/phút).
- #468 / #469 / #470 / #473 / #474: backend quan sát job (`shared.job_worker`, llm-calls, links); trang Jobs; deep link; notes; bước `ranking_markets` / `route_detection` của a3.
- #471: T2 tenant chỉ đọc `seo_context` cache, thiếu cache thì log `t2_seo_context_missing`.
- #472: `RunBudget.hard_stop_day`. Trần theo lượt và trần theo ngày, mỗi cái theo cờ `hard_stop` của dòng riêng.
- #475: tab Budgets trong External Spend.
- #476 (mig 179): role `tripplanner` được đọc `raw_tours.tour_id` / `country`.
- #477 (mig 180): role `tripplanner` được đọc các cột địa danh/activity của `tour_atoms`, không đọc cột biên tập.

**AA-TripPlanner-Web** (#52–#63, đều đã merge; migration 003–006 đã chạy trên Dev)

| PR | Nội dung |
|---|---|
| #52 | `tour_day` (mig 003), trích bằng quy tắc + `tp_extract`, chạy qua Lambda direct invoke |
| #53 | Tour Graph (mig 004); sửa đọc catalog dưới tenant RLS (`fetch_catalog`); prune/rebuild từ chối khi tập tour active rỗng |
| #54 / #55 | Geocode giới hạn trong các nước AA; op `regeocode` (sau này bị thay thế) |
| #56 | `locate.py`: model đề xuất tọa độ, Mapbox xác nhận ≤ 25 km; neo đêm ngủ (lodging → `end_place`, transit → none); op `relink`; `located_by` (mig 005) |
| #57 | op `components`: dựng lại `itinerary_components` từ atom (tất định), kèm embedding |
| #58 | Gợi ý tiếp theo theo tuyến tour (`ROUTE_CANDIDATES_SQL`); sửa `_current_components` thiếu `destination_id` |
| #59 | `GET /trip/{id}/coverage`; `GET /browse/routes?country&days` |
| #60 | Bộ lọc gợi ý; `/trip/{id}/stops/{dest}/activities`; sự kiện `add_day` / `remove_day` (mig 006) |
| #61 / #62 | UI planner v1; coverage giữ pin đúng ngày tour của nó |
| #63 | Ngày trip theo ngày tour AA; thêm sân bay cho mọi nước AA bán; đường núi < 150 km được vòng tới 3.5 lần |

- Nhánh WIP `feat/aa-674-planner-redesign` (8b76e87, chưa có PR): StartScreen, icons SVG, màu theo ngày, state `intent` / `selectedDay`.

**AA-Ecosys (root):** log này + cập nhật số phiên trong steering.

## Thay đổi Hạ tầng
- Infra #78: secret `tripplanner/dev/mapbox-geocoding-token` và quyền đọc cho assembly Lambda; Terraform Apply chạy qua workflow. Token thật lấy từ `backend/.env`, `put-secret-value` trên acc2.
- Migration DB đã chạy trên Dev: CIS 178, 179, 180; TripPlanner 003, 004, 005, 006.
- Không tạo resource AWS mới nào khác.

## Bằng chứng verify
- AA-688: landing PAA ~4.5 phút; kết quả khớp 2506/2506.
- AA-687: Jobs page trên prod (Playwright); ETA chạy đúng với job a3 thật.
- KAN-90: tab Budgets trên prod hiện 3 dòng (DFS global chỉ cảnh báo, do nghiep:kan90).
- Tour Graph: điểm dừng lệch > 500 km so với cả hai điểm kề trong tour giảm từ 115/517 xuống 3/578 (còn Hong Kong, Bangkok, sân bay Delhi, đều là chặng dài thật).
- API Dev TripPlanner:
  - gợi ý từ Kathmandu (mode route): Pokhara, Namche, Lukla, EBC;
  - `routes` Bhutan 7 ngày: đứng đầu là tour nguyên "Valley Hikes & Mountain Passes";
  - coverage, activity, thêm/bớt ngày đều HTTP 200.
- Playwright trên `aa-tripplanner.vercel.app`: chọn tuyến → coverage → activity → thêm ngày → reload vẫn giữ → bỏ ngày.
- **Chi phí LLM chạy dữ liệu TripPlanner:** `tour_days` 56 tour $0.89; relink $0.15; components 51 tour $0.39 + embedding $0.006. Tổng ≈ **$1.44**.

## Jira / Linear / tài liệu
- Jira KAN-90: comment 10428 (trả lời 3 câu hỏi) và 10429 (báo xong). Jira PR-11: comment 10430 nhờ team marketing điền ảnh vào Google Sheet.
- Linear:
  - Done: AA-688, AA-687, AA-673, AA-675;
  - In Progress: AA-674 (con của AA-689), AA-689 (epic mới);
  - có comment tiến độ trên AA-665 / AA-673 / AA-674 / AA-675 / AA-689.
- Tài liệu cho marketing:
  - [photo request](https://claude.ai/artifact/KjJJetZqq53KgJVNkSHmJm);
  - Google Sheet "AA Trip Planner — photos by place (batch 1)", 163 điểm ưu tiên, trên Drive của Nghiệp;
  - file Excel đủ 786 điểm ở `.tmp-session/deliverables/AA_TripPlanner_photos_by_place.xlsx`.

## Còn lại
- **Nghiệp:** mở quyền Google Sheet ảnh (Share → Anyone with the link → Editor). Chưa mở thì team marketing không vào được.
- **CIS App (ưu tiên, theo yêu cầu Nghiệp quay về App):**
  1. `segment_research_ideas_task` ra 0 ý tưởng;
  2. text Debate bị hỏng;
  3. AA-685 đối soát chi phí (từ 30/09);
  4. AA-663 / AA-662 (UI v2);
  5. AA-651 (worker ECS riêng);
  6. `judge_client` còn ở backend cũ;
  7. 71 địa điểm Bhutan;
  8. opt-in prune 1.081 component cũ của tour không còn publish (Nghiệp quyết).
- **TripPlanner (AA-689, làm theo phần đã thống nhất):**
  1. Giai đoạn A từ nhánh WIP;
  2. lỗi tile 503 ở zoom thế giới;
  3. property test 20 bộ pin;
  4. báo cáo PR-11 sau khi xong Giai đoạn A (nháp cho Nghiệp duyệt);
  5. nạp ảnh khi marketing gửi về;
  6. trích nốt khoảng 65 tour sau đợt dọn dữ liệu.

## Lưu ý kỹ thuật cho phiên sau
- **Tenant RLS:** `published_tours` / `raw_tours` bật RLS bắt buộc theo `app.tenant_id`. Role `tripplanner` phải `set_config('app.tenant_id', '00000000-…0001', true)` trong transaction; thiếu thì thấy 0 dòng. Nếu không có guard, một lệnh prune kiểu "không còn active" sẽ xóa sạch bảng.
- **asyncpg:** không suy được kiểu của `$2 - $3` (phải thêm `::int`); `$1::date` không nhận chuỗi (dùng `$1::text::date`).
- **Mapbox:** tìm theo tên không tin được với địa danh châu Á, kể cả đã lọc country ("Chiang Mai" ra một làng ở Roi Et). Dùng `locate.py`: model đề xuất, Mapbox xác nhận.
- **Linear tự đóng issue** khi PR có `[AA-xxx]` được merge. Issue còn việc phải chuyển lại In Progress.
- **boto3 không dùng lại cache MFA của CLI:** trước khi chạy script operator phải `export $(aws configure export-credentials --profile aa365-admin --format env | xargs)` rồi chạy với `--profile ""`. STS hết hạn sau 8 giờ; phiên này Nghiệp gửi mã MFA qua chat.
- **Auto mode classifier:** có lúc lỗi hàng loạt ("no verdict", khóa turn sau 10 lần), và chặn merge PR khi chưa có review. Nghiệp duyệt hoặc tắt auto mode thì mới merge được.
- `pkill -f` trong một script nền có thể tự giết chính script đó nếu pattern khớp dòng lệnh của nó.
- Memory mới: `decide-dont-ask`, `paid-runs-subset` (chạy tốn phí thì thử ~3 rồi tối đa ~50 tour), `cis-app-first`, `jira-report-when-done`.
