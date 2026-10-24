# Panel chấm mù 50 cặp shadow (S249) + nguyên nhân Rajasthan mất ngày

Bổ sung cho bản go/no-go ([README.md](README.md)): hai điều kiện mở số 1 và 2.

## Panel chấm mù (rubric s1-panel-v1.1, 2 lượt độc lập, $0)

50 cặp (bài mới writer v2 W×Sonnet trong shadow `cfebc266` so với trang đang live), mỗi lượt 10 batch × 5 tour, judge
không biết trang nào là bản nào; lượt b đọc ngược thứ tự để giảm thiên lệch thứ tự. Gói chấm và khóa:
`.tmp-session/s249/aa645/wave50-packet.json`, `wave50-key.json`; kết quả `panel50/pass-a.json`, `pass-b.json` (local).

| Chỉ số | Lượt a | Lượt b |
|---|---|---|
| Lỗi nghiêm trọng / claim kiểm được — bài mới | **0,0015** (4 / 2.599) | **0,0004** (1 / 2.565) |
| Lỗi nghiêm trọng / claim — trang live | 0,0511 (145 / 2.835) | 0,0530 (146 / 2.754) |
| So theo tour: bài mới ít lỗi hơn / nhiều hơn | 42 / 0 (Wilcoxon p ≈ 1,7·10⁻⁸) | 41 / 0 (p ≈ 2,5·10⁻⁸) |
| Trang có lỗi hard-fail: mới / live | 1 / 20 | 1 / 20 |
| Xếp hạng: mới hơn / hoà / live hơn | 49 / 0 / 1 | 48 / 0 / 2 |
| Verdict bài mới | 28 publish nguyên văn, 21 light, 1 heavy | 26 / 23 / 1 |
| Verdict trang live | 20 light, 25 heavy, 5 reject | 20 / 24 / 6 |

Đọc: trên 50 tour chưa từng dùng để chọn writer, bài viết lại có lỗi nghiêm trọng thấp hơn trang đang live khoảng
35–100 lần, hai lượt chấm cho cùng kết luận. Điều kiện d13 cuối cùng ("mỗi wave phân tích chất lượng có cải thiện rõ")
nay có số panel, không chỉ số đo bằng code. Lưu ý: panel chấm khắt hơn nhãn người (AA-783, κ 0,40), nên dùng như so
sánh tương đối mới–cũ, không phải "đạt chuẩn tuyệt đối".

## Rajasthan mất ngày 11–15 — nguyên nhân gốc

- Nguồn có 15 dấu `Day N`; kế hoạch code yêu cầu đủ 15; writer gần như chắc chắn viết đủ 15 (số lần gọi grounding 62 khớp
  15 ngày, trang cuối chỉ 47 đơn vị câu).
- Dòng dữ kiện bữa ăn writer v2 chép từ nguồn ("Meals: dinner") khớp biểu thức dò "giờ ăn bịa" của brand audit →
  **36/50 tour bị gắn `ITINERARY_MEAL_TIME_INVENTED`, 34 tour bị pass sửa Haiku viết lại TOÀN BỘ lịch trình**.
- Ở Rajasthan, pass sửa đó làm rơi ngày 11–15. Không gì hoàn tác: hợp đồng sửa không có điều kiện "giữ số ngày";
  `ITINERARY_DAY_COUNT_MISMATCH` chỉ trừ 0,25 điểm (9,75 vẫn publish); `DAY_COUNT_VS_DURATION` đang ở chế độ shadow.
- Đang sửa (S249): dòng bữa ăn khớp nguồn không còn bị coi là bịa; thêm điều kiện `days_kept` vào hợp đồng sửa (sửa nào
  làm đổi số ngày thì hoàn tác); mất ngày ở writer v2 thành không publish được — không tăng số gate. Rồi replay $0 trên 50
  bản ghi và chạy lại shadow các tour bị ảnh hưởng.
