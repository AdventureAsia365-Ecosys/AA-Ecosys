# Hướng dẫn chấm 40 bài T9 (S234) — tiêu chí cho người chấm

**Mục đích:** có nhãn của người thật để (1) kiểm panel AI (4 góc nhìn) có chấm giống người không, (2) đo từng gate bắt
đúng/sai (AA-783, AA-791). Thời gian dự kiến **2–3 giờ** (blog ~5′/bài, LinkedIn ~2′/bài).

**File:** `S234-label-40.xlsx`, sheet **Label**. 40 bài: 16 blog (A&H 8, Terra 8) + 24 LinkedIn (mỗi tenant 6),
lẫn bài gate duyệt và bài gate giữ. **Đừng mở sheet `_key`** trước khi chấm xong (trong đó có kết quả gate — xem trước sẽ
bị dẫn dắt).

Mỗi dòng có: bài viết (TEXT), title/meta (blog), **SOURCE** = toàn bộ những gì writer được phép dùng (moment của tour,
fact địa danh, dòng SCOPE), **BRAND** = tóm tắt brand pack của tenant. Chấm như **chủ một công ty tour (tenant) sắp đăng
bài này dưới thương hiệu của mình**.

## 1. Cột VERDICT — chọn 1 (quan trọng nhất)

| Nhãn | Định nghĩa (dùng đúng ngưỡng này) |
|---|---|
| `as_is` | Đăng **nguyên văn** được: không sai sự thật, đúng giọng brand, đúng chuẩn kênh. Có thể có câu chưa hay nhưng không đáng sửa. |
| `light` | Sửa **≤ 10 phút**, **≤ 3 câu**, **không cần tra cứu** thêm thông tin. |
| `heavy` | Phải sửa nhiều hơn mức `light` (viết lại đoạn, tra cứu fact, đổi cấu trúc) nhưng bài vẫn đáng giữ. |
| `reject` | Bỏ, viết lại từ đầu nhanh hơn sửa (sai nặng, lệch chủ đề, sai brand hoàn toàn). |

Mẹo: nếu phân vân giữa 2 nhãn, chọn nhãn **khắt hơn**.

## 2. Bốn cột lỗi — mỗi cột chọn `không` / `nhẹ` / `nặng`

| Cột | Đánh dấu khi | Ví dụ thật từ S234 |
|---|---|---|
| **LỖI SAI SỰ THẬT / BỊA** | Bài nói điều **không có trong SOURCE** về chuyến đi (lịch trình, giờ giấc, dịch vụ, "đã bao gồm" khi SOURCE ghi optional, hứa nhịp độ/độ dễ), con số không có trong SOURCE, địa danh **ngoài phạm vi** bài, hoặc nói quá ("độc nhất thế giới") khi SOURCE chỉ nói "nhiều". **Kiến thức nền đúng, phổ biến về địa danh thì KHÔNG tính lỗi.** | "boat ride" viết như có sẵn trong khi SOURCE ghi *Optional*; "first night" khi SOURCE không nói đêm nào; "Punakha vẫn là thủ phủ" (đã dời 1955) |
| **LỖI GIỌNG BRAND** | Không giống cách brand này nói (so với BRAND): sai đối tượng (gia đình ↔ dân phượt), sai năng lượng (Trail Pulse phải sôi nổi, Terra phải có góc nhìn của trẻ em/gia đình…), dùng từ cấm, chép nguyên câu trong brand pack/style guide, CTA không đúng câu cấu hình. | Trail Pulse viết như bài thiền tĩnh lặng; Terra "Terra builds journeys so that…" chép từ style guide |
| **LỖI KÊNH / SEO / HÌNH THỨC** | LinkedIn: < 120 hoặc > 250 từ, > 3 hashtag, dòng đầu quá dài/không có hook, hashtag sai chính tả. Blog: title/meta sai phạm vi hoặc cụt, thiếu FAQ (< 3 câu) hoặc FAQ trả lời lạc đề, heading kiểu lệnh cho writer ("A Single Sentence on…"), câu lặp, câu cụt sau khi sửa, CTA lặp 2 lần. | "#PaaTaktsang"; FAQ "Who are the Tsaatan?" không trả lời; câu "That's not filler. That's structure." đứng một mình |
| **VĂN AI / SÁO** | Đọc là biết máy viết: cặp "không phải X, mà là Y" dày đặc, câu sáo ("worth sitting with", "not a monument"), mở bài chung chung, kết bài tóm tắt lại, nhiều gạch ngang dài (—). | "This is not a backdrop. It is the point." |

`nhẹ` = có nhưng sửa trong vài giây; `nặng` = là lý do chính khiến bài không đăng nguyên văn được.

## 3. Các cột còn lại

- **PHÚT SỬA ước tính**: số phút anh nghĩ cần để đưa bài tới mức đăng được (0 nếu `as_is`; để trống nếu `reject`).
- **CÂU CẦN SỬA (trích)**: dán nguyên văn 1–3 câu tệ nhất — giúp đối chiếu với câu gate đã gắn cờ.
- **GHI CHÚ**: bất kỳ điều gì gate/AI nên bắt mà chưa có trong 4 cột trên.

## 4. Không cần chấm

- Ảnh, định dạng HTML, độ dài blog chính xác, điểm SEO kỹ thuật.
- So sánh giữa các bài với nhau — chấm từng bài độc lập.

## 5. Sau khi chấm

Lưu file và báo — Claude sẽ so nhãn của anh với panel AI (độ đồng thuận κ, từng góc nhìn) và với từng gate (gate nào
bắt đúng lỗi anh đánh dấu, gate nào báo nhầm), rồi chỉnh ngưỡng "sửa nhẹ ≥ 60%" và danh sách gate (AA-783, AA-791, AA-787).
