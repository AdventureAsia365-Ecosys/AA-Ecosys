# Trả lời ghi chú Q4 và Q8: A/B có hiệu quả không, phương án B là gì (S246)

Bối cảnh: anh đã duyệt Q1–Q8 của bản tư vấn S246. Anh còn hai ghi chú: Q4 "cần tư vấn kỹ, chưa chắc A/B hiệu quả", Q8 "chưa hiểu phương án B chạy thế nào". Bản này trả lời hai ghi chú đó. Toàn bộ chỉ đọc dữ liệu, không gọi LLM trả phí. Số nào là ước tính thì có ghi rõ.

## 0. Trả lời ngắn

- **Q4: anh nghi đúng.** Nếu chạy A/B như đang viết (5 nhánh, 50 tour, chấm "đạt / sửa nhẹ", nhánh thắng phải vượt |A'−A|), nhiều khả năng mình **không thấy** được cải thiện thật, trừ khi cải thiện rất lớn. Lỗi nằm ở **thước đo**, không nằm ở số tour. Ví dụ: nếu người viết mới nâng tỷ lệ "sửa nhẹ" từ 12% lên 25%, A/B 50 tour chỉ có khoảng 1/3 cơ hội nhận ra.
- **Cách sửa A/B.** Thước chính đổi sang **đếm lỗi nghĩa trên mỗi trang** (bịa, hứa không có nguồn, số gắn sai danh từ). Thêm phép **so cặp mù** "trang nào agency dùng được hơn". Lỗi kiểm được bằng code chỉ làm cổng phải đạt, không tính vào phần thắng. Chỉ giữ 3 nhánh chính, chạy 2 lần, mỗi lần ≤ $10.
- **Nói trước kết cục dễ xảy ra nhất:** sau 50 tour vẫn "chưa rõ", phải thêm 50 tour ngoài golden set. Tổng thực tế khoảng **$8–25 qua 3–4 phiên**, không phải $12–15 trong một lượt.
- **Q8: phương án B = "trang ngắn, dữ kiện trước".** Code dựng khung (hộp dữ kiện, các dòng theo ngày, bao gồm / không bao gồm) thẳng từ bảng dữ kiện. LLM chỉ viết một câu cho mỗi ngày. Người sửa nhẹ trên trang `/admin/review` đã có sẵn. Ước tính 10–15 phút/tour, chưa đo.
- **Đề xuất chính:** đừng để B chờ tới khi A/B thua. Cho trang ngắn (nhánh E) **vào A/B ngay**, vì nó gần như $0. Khi đó cùng một lần chạy trả lời được cả Q4 (người viết mới có tốt hơn không) lẫn Q8 (trang ngắn có đủ dùng không).

## 1. A/B 50 tour có đủ không

### 1.1 Vì sao thước "đạt / sửa nhẹ" gần như mù

- Trên 50 bài S1 golden: 0 bài đăng nguyên văn, 6 sửa nhẹ (12%), 42 sửa nặng, 2 bỏ. Thước này đang **nằm sát đáy**.
- Cải thiện thật thường xảy ra **bên trong** nhóm "sửa nặng": từ 4 lỗi xuống 2 lỗi thì vẫn là "sửa nặng". Thước đạt/không đạt không thấy thay đổi đó.
- Mô phỏng: nếu người viết mới **giảm một nửa** số lỗi, tỷ lệ trang 0 lỗi chỉ tăng khoảng 12–17 điểm %.

Khả năng phát hiện (power) với thước đạt/sửa nhẹ, kiểm định McNemar, ngưỡng 0,05:

| Cải thiện thật (sửa nhẹ trở lên) | n = 50, so 1 cặp | n = 50, 3 nhánh mới (đã chia ngưỡng) | Số tour cần cho 80% |
|---|---|---|---|
| 12% → 25% | 0,33 | 0,16 | khoảng 150–200 |
| 12% → 35% | 0,72 | 0,51 | khoảng 70 |
| 12% → 45% | 0,94 | 0,84 | dưới 50 |

- Mục tiêu "lát rải đều 4/18 → 10/18" chỉ có power khoảng 0,42, **kể cả khi** hiệu ứng là thật. Nó chỉ dùng để mô tả được, không làm tiêu chí đạt/trượt được.
- 5 nhánh làm hại hai lần. Một là phải chia nhỏ ngưỡng thống kê, mất 20–35 điểm power. Hai là panel phải chấm 250 trang đọc toàn nguồn.

### 1.2 Nhiễu thật lớn tới đâu (kèm giới hạn của từng số)

| Nguồn nhiễu | Số | Đọc thế nào |
|---|---|---|
| Gate cho kết quả khác nhau trên cùng 50 đầu vào S1 (production so với regenerate S245) | 11/50 (22%) | **Không phải nhiễu A/A sạch.** Hai lần chạy cách nhau rất nhiều commit (`quality_gates.py` sửa 37 lần từ 25/09), lại do judge không thấy nguồn chấm. Nó lẫn ba thứ: nhiễu sinh văn, nhiễu judge và code đã trôi. |
| Judge đọc đoạn trích lệch nhãn đọc toàn nguồn | 8–9/50 mỗi judge; kappa 3 judge = 0,71 | Đây là lệch do thiếu thông tin (judge trích cho đạt 29%, nhãn cuối 12%). Nó **chưa phải** nhiễu khi panel đọc toàn nguồn chấm lại chính nó. Con số này chưa có. |
| AA-748: control lặp tự lệch | 150 → 96 lỗi grounding trên 30 tour (−36%) | Mô phỏng cho thấy chuyện này có thể chỉ là ngẫu nhiên, p = 0,02–0,2 tuỳ độ "đuôi nặng" giả định. Có điểm chưa khớp: với đúng tham số dùng cho bảng power, p chỉ là 0,023. Nên hoặc có hiệu ứng theo lô, hoặc bảng power đang hơi lạc quan. Round 2 của AA-748 cũng chạy sau #639/#640 và migration 212. |

**Kết luận phần nhiễu:** chưa có số đo nhiễu thật của chính thước mình sẽ dùng. Vì vậy bước đầu tiên (S247, $0) là **cho panel chấm lại 10–15 trang A hai lần** để có độ lặp thật. Sau đó mới tin bảng power.

### 1.3 Thước nào nhạy hơn

| Thước | n = 50, giảm lỗi 50% / 30% / 20% | n = 100 |
|---|---|---|
| Đếm lỗi bằng code (không nhiễu đo) | 0,94 / 0,54 / 0,29 | 1,00 / 0,79 / 0,46 |
| Đếm lỗi bằng panel (bắt 80%, 0,3 báo nhầm/trang, **giả định**) | 0,86 / 0,43 / 0,26 | 0,99 / 0,69 / 0,40 |

| So cặp mù (đảo thứ tự, thắng khi nhất quán) | 65% / 70% / 75% người chấm chọn bản mới |
|---|---|
| Power ở n = 50, giả định 25% hoà | 0,53 / 0,76 / 0,92 |
| Số tour cần cho 80% | khoảng 89 / 49 / 31 |

- Lưu ý: judge LLM mạnh chỉ nhất quán khi đảo thứ tự ở khoảng 65% số cặp (Zheng et al. 2023). Tỷ lệ hoà thật có thể 35% trở lên, nên số tour cần tăng thêm khoảng 15%.
- "Mù" chỉ là danh nghĩa. Trang mới ngắn hơn, không có meta cụt, nên judge đoán được nhánh.
- Luật "phải vượt |A'−A|" thô: nó đem hiệu ứng so với **một lần rút ngẫu nhiên** của nhiễu. Ở n = 50, riêng chênh lệch A–A' đã dao động khoảng −23% tới +28%.

**Trả lời thẳng câu "50 tour có đủ không":** đủ để thấy cải thiện **lớn** (giảm ≥ 40–50% lỗi, hoặc ≥ 70% người chấm chọn bản mới). Không đủ để thấy cải thiện **vừa** (giảm 20–30%). Muốn thấy mức vừa thì cần khoảng 100 tour, và phải đổi thước.

## 2. Cách thử tốt hơn

### 2.1 Sửa lỗi gây nhiễu nhân quả trước tiên

"Đường mới" đang gom 4 thay đổi: day-count oracle, meta gọi riêng không cắt chữ, bỏ ép độ dài, và prompt/model mới. Hai thay đổi đầu **chắc chắn** xoá lỗi đếm ngày và meta cụt. Nếu so với A gốc thì W gần như chắc thắng, nhưng điều đó không trả lời câu anh hỏi: người viết mới có **bớt tô vẽ** không. Lỗi tô vẽ mới là lỗi chiếm đa số: 29/50 lý do nhãn nhắc "invented/unsupported", 8/50 meta cụt, khoảng 4/50 đếm ngày.

→ Control là **A+** = người viết hiện tại + day-count oracle + meta gọi riêng. Lỗi kiểm bằng code chỉ là **cổng** (phải về ~0), không tính vào phần thắng.

### 2.2 Thiết kế đề xuất

| Bước | Làm gì | Chi phí | Ghi chú |
|---|---|---|---|
| **0 (S247)** | Bộ kiểm bằng code (đếm ngày, số không có trong nguồn, meta cụt/quá dài, tên ngoài bảng) chạy trên 50 bài S1 cũ, báo TPR/TNR. Panel chấm lại 10–15 trang hai lần để đo độ lặp. Chốt rubric: danh sách loại lỗi nghĩa + câu hỏi so cặp "agency dùng trang nào". | $0 | Có số nhiễu thật để thay giả định. |
| **1 (S248) – sàng model** | Đường mới với Haiku, Luna, Sonnet trên 12 tour **ngoài golden set**. Xếp hạng theo lỗi + panel xếp 3 bản. Chọn một người viết W (hoà thì lấy model rẻ). | khoảng $2,5 | Đây là bước "chọn người thắng", không kết luận thống kê. 12 tour có thể chọn nhầm; ghi rõ trong báo cáo. |
| **2a (S248–S249) – run 1** | 25 tour golden × {A+, A', W, E}. Sinh xen kẽ trong cùng lần chạy. Cả 4 bản chấm chung một lô mù, rubric cố định, đọc toàn nguồn. | khoảng $3 (W là Haiku/Luna); khoảng $6,5 (W là Sonnet) | A' chỉ chạy ở run 1, làm **kiểm tra A/A**. |
| **2b – run 2** | 25 tour golden tiếp theo × {A+, W, E}. | khoảng $2 / $5,5 | |
| **3 – chỉ khi chưa rõ** | +50 tour ngẫu nhiên ngoài golden × {A+, W, E}. Nâng n lên 100. | khoảng $3,5 / $10,5 (chia 2 lần nếu > $10) | Không cần nhãn golden trước, vì đếm lỗi và so cặp không cần. |

**Hai câu hỏi, hai cặp so sánh:**
- **W vs A+** trả lời Q4: người viết mới có bớt lỗi nghĩa không.
- **E vs W** trả lời Q8: trang ngắn có đủ dùng không.

**Thước:**
- Thước chính: **số lỗi nghĩa nghiêm trọng / số khẳng định kiểm được** trên mỗi trang (chuẩn hoá theo độ dài, để trang ngắn không thắng chỉ vì ít chữ), kiểm định Wilcoxon theo cặp.
- Thước kèm: **độ phủ dữ kiện**, tức trang giữ được bao nhiêu trường mà nguồn CÓ (thời lượng, km, giờ, bữa, chỗ ở, bao gồm…). Tính bằng code so với bảng dữ kiện.
- Thước kèm: so cặp mù, đảo thứ tự.
- Chỉ báo cáo, không dùng để quyết: tỷ lệ đạt/sửa nhẹ và lát 18 tour.

### 2.3 Khi nào dừng, khi nào chọn

- **Kiểm tra A/A (run 1):** nếu A+ vs A' lệch có ý nghĩa thì run đó vô hiệu, phải sửa thước trước. Lưu ý: ở n = 25 kiểm tra này chỉ bắt được thiên lệch lớn (power khoảng 0,2), và tự vô hiệu oan khoảng 10% số lần.
- **Sau run 1, dừng vì vô ích:** W/A+ ≥ 0,9 về tỷ lệ lỗi **và** so cặp ≤ 50% → dừng tinh chỉnh người viết, xem kết quả E.
- **Sau run 1, dừng sớm vì thắng rõ:** chỉ khi rất mạnh (z ≥ 2,8, theo O'Brien-Fleming).
- **Chọn W:** tỷ lệ lỗi W/A+ ≤ 0,7, p < 0,025 ở lần nhìn cuối; so cặp **không thua** (≥ 50%); cổng code về ~0; chi phí/tour trong ngân sách. Không đòi cả hai thước cùng có ý nghĩa, vì nếu đòi thì xác suất đạt chỉ còn 0,25–0,35 kể cả khi W tốt thật.
- **Chọn E cho một nhóm tour:** lỗi nghĩa của E ≤ W, độ phủ dữ kiện không thấp hơn, so cặp "agency dùng" không thua quá 10 điểm.
- **Chuyển hẳn sang B:** ở n = 100, cận trên khoảng tin cậy của tỷ lệ lỗi W/A+ ≥ 0,9, hoặc so cặp ≤ 55%.

### 2.4 Chi phí và thời gian thật

- Giá A $0,0296/tour là **mức sàn**: report S245 có 815 call nhưng chỉ 627 có log (23% call không có log). Cần đối chiếu dashboard nhà cung cấp.
- Tổng tiền AWS: khoảng $7–14 nếu dừng sau 50 tour; $8–25 nếu cần bước 3.
- **Thời gian của anh:** panel bất đồng khoảng 16–18% nên anh xem khoảng 25–35 trang mỗi vòng, tức khoảng **1–2,5 giờ/vòng**. Con số 30–45 phút trong bản tư vấn là quá lạc quan. Trang E ngắn nên phần của nó nhanh hơn.

## 3. Phương án B cụ thể

### 3.1 Trang trông thế nào

Vẫn dùng đúng 11 trường `generated_content` hiện có, **không đổi schema**:

| Trường | Nội dung | Ai làm |
|---|---|---|
| `aa_name`, `aa_subtitle` | Tên + loại thời lượng (Half Day / 1 Day / N Days); subtitle là một câu dữ kiện | LLM, code kiểm |
| `aa_summary` | Một câu hút gắn với điểm hút có trong nguồn, rồi hộp "At a glance" dạng `Label: value`: thời lượng, điểm/giờ đi-về, bữa, chỗ ở, phương tiện, độ khó, cỡ đoàn, tuổi. **Trường nào nguồn không có thì ẩn**, và trường đó vào danh sách hỏi nhà cung cấp. | Code dựng từ bảng dữ kiện |
| `aa_highlights` | 3–5 dòng, mỗi dòng một dữ kiện có thật | LLM chọn, code kiểm |
| `aa_itineraries` | **Giữ tiêu đề `Day N — <title>`**, vì TripPlanner tách ngày bằng regex này (`master_content.py:44-47`; không khớp thì `parse_days` trả rỗng). Dưới tiêu đề: 1 câu ≤ 40 từ + các dòng Route / Distance / Time / Meals / Overnight (chỉ khi nguồn có) | Câu: LLM. Dòng: code |
| `aa_description` | Danh sách bao gồm / không bao gồm | Code |
| `seo_title`, `seo_meta` | Một call riêng, code kiểm, cho viết lại 1 lần, không cắt chữ | LLM + code |

Tổng khoảng 150–400 từ, so với trung vị 764 từ hiện nay. Chỗ LLM có thể bịa co lại còn vài câu, đọc soát bằng mắt trong 1–2 phút.

**Điểm yếu cần nói thẳng:**
- **Hộp dữ kiện thường sẽ trống.** Đếm thô trong 50 nguồn golden: cỡ đoàn có ở 9/50, tuổi tối thiểu 7/50, không bao gồm 9/50, giờ xuất phát 15/50, độ khó 17/50. Chỉ bữa ăn (43/50) và chỗ ở (46/50) là phổ biến. Đòn bẩy thật là **danh sách hỏi nhà cung cấp**, tức thời gian của nhóm chị Thư.
- Trang khô hơn, mất giọng AA, ít chữ cho SEO. Tạm thời chưa hại vì TripPlanner mới ở Dev, chưa có traffic.
- Mỗi lần đổi S1 phải chạy lại atomize, T2, T9 và tính lại Segment/Route một lần.
- Các hãng lớn (Intrepid, Exodus, G Adventures) cũng đưa dữ kiện lên trước. Nhưng 2 trong 4 trang mình đọc là trip notes hậu cần, cả 4 đều là hãng bán lẻ, và chưa xem được trang DMC B2B nào. Đây là tín hiệu, không phải bằng chứng.

### 3.2 "Sửa nhẹ bởi người" là gì

Người sửa **không viết lại bài**. Họ làm 4 việc:
1. Đối chiếu từng dòng dữ kiện với câu gốc, sửa hoặc gạch dòng sai.
2. Duyệt câu hút và tiêu đề ngày; chỉ sửa cụm từ, không viết lại câu.
3. Điền danh sách hỏi nhà cung cấp nếu có câu trả lời, không thì để ẩn.
4. Bấm duyệt.

**Công cụ đã có:** `/admin/review` (`ReviewEditor.tsx`) sửa được 11 trường qua `PATCH /admin/tours/{tour_id}/generated/{content_id}`. Sửa xong hệ thống đặt `human_edited`, bắt re-validate rồi mới cho approve. Có sẵn vai trò staff `reviewer` (quyền `review.act`), đăng nhập Cognito workforce.

**Còn thiếu, khoảng 1 phiên Claude:**
- (a) Editor chỉ mở cho dòng nằm trong review queue. Tour đã lên Master phải tạo version mới, promote, atomize lại.
- (b) Lịch trình chỉ sửa được dạng textarea thô.
- (c) Chưa có khung hiện câu gốc cạnh từng dữ kiện; làm cùng bảng dữ kiện S247.
- (d) `edit_diff` chỉ lưu tên trường; AA-916 sẽ lưu nội dung trước/sau.

### 3.3 Ai làm, bao lâu, bao nhiêu (đều là ước tính, chưa đo)

| Việc | Ai | Trang ngắn | Văn dài hiện tại |
|---|---|---|---|
| Đối chiếu nguồn + sửa chữ | Panel Claude + anh phân xử, hoặc biên tập viên tự do (Upwork: copy editor $20–40/giờ, trung vị khoảng $30) | 10–15 phút/tour → 8–13 giờ cho 50 tour (khoảng $250–780 nếu thuê) | 30–60 phút/tour cho bài sửa nặng → 25–45 giờ (khoảng $750–2.700) |
| Chọn 50 tour ưu tiên + trả lời hỏi nhà cung cấp | Chỉ nhóm chị Thư làm được | 5–10 phút/tour + thời gian chờ nhà cung cấp | Như nhau |

- Có ca phản ví dụ: s1-037 bị nhãn "sửa nặng" nhưng lịch trình gần như đúng hết số; lỗi dồn ở subtitle/summary/meta, sửa có thể chỉ mất 10 phút. Nên con số "nhanh gấp 3" chưa chắc.
- Thuê người ngoài kéo theo việc ẩn: cấp tài khoản Cognito, chia sẻ dữ liệu nhà cung cấp, hướng dẫn rubric.
- Chuyện người và nhân sự là quyết định của chị Thư. Mình chỉ gửi đề xuất trung tính. Ý "agency châu Âu có nghĩa vụ đưa main characteristics" (EU PTD 2015/2302 Điều 5–6; UK dùng Package Travel Regulations 2018) cũng để chị Thư cân nhắc, không dùng làm lập luận kỹ thuật, vì chưa biết agency thật ở đâu.

### 3.4 Khi nào nên làm B ngay, không chờ A/B

- **Làm ngay phần rẻ:** dựng E thành một nhánh của A/B từ S248. Gần như $0, vì code dựng khung và LLM chỉ viết vài câu.
- **Áp dụng B làm mặc định trước khi A/B xong**, chỉ khi:
  - (a) có agency thật cần trang của khoảng 50 tour trước khi A/B kết luận; hoặc
  - (b) số đo độ lặp ở S247 cho thấy panel quá nhiễu (ví dụ chấm lại lệch > 25%), tức là A/B không đáng chạy.
  
  Khi đó B an toàn hơn: phần bịa được chỉ còn vài câu, và người soát được.
- **Không quyết trước** chuyện "tour 1 ngày / nguồn mỏng thì dùng trang ngắn". Số liệu gợi ý điều đó (nguồn < 300 từ: 0/13 đạt), nhưng chưa có ý nghĩa thống kê (Fisher p = 0,15), và bị gây nhiễu do golden set được chọn lệch có chủ đích. Mình phân tầng theo độ giàu nguồn **trong** A/B rồi mới chốt.

## 4. Ví dụ thật trên một tour

Mình chọn **s1-008 "1 Day Trishuli River Rafting" (Nepal)**, một ca nguồn mỏng. Nhãn golden: fail, sửa nặng, panel đồng ý. Pipeline lúc đó vẫn cho qua (score 8.00, brand_audit pass).

**Giới hạn của ví dụ:** hai bản mới dưới đây do mình viết tay. Mình đã biết trước danh sách lỗi của panel, và bảng dữ kiện do agent mạnh dựng, không phải Haiku trích. Vì vậy đây chỉ là **minh hoạ hình dạng**, không phải bằng chứng A/B sẽ thắng. Ca nguồn giàu (s1-037 Bhutan) để ở `/home/nghiep/projects/AA-Ecosys/.tmp-session/s246-q48/example-s1-037.md`. Ở ca đó, code chỉ chắc chắn bắt được **3/8 lỗi** (meta so sánh nhất, meta cụt, rơi số km), không phải 4/8. Lỗi "two passes above 4,300 m" chép đúng từ intro của nguồn, nên phải có bước LLM phát hiện mâu thuẫn mới bắt được. Bản Plan B trong file đó cũng cần đổi `1. **Paro**` thành `Day 1 — Paro` để không làm vỡ `parse_days`.

### 4.1 Bản hiện tại (đã ship)

> **Subtitle:** Four-hour run from Fishling to Mugling on Class III–IV rapids
> **Summary (trích):** …delivers a full-day run of intermediate whitewater… across Class III and IV rapids. The river cuts through foothills terrain… sections of open water suitable for swimmers and less experienced paddlers…
> **Itinerary:** …A lunch break takes place partway through on the riverbank…
> **SEO meta:** One-day Trishuli River rafting run from Fishling to Mugling covers Class III–IV rapids with trained guides, safety gear, and riverbank lunch included.

| Lỗi | Nguồn nói gì | Code bắt được không |
|---|---|---|
| "Class III–IV rapids", lặp ở 5 trường | Nguồn không phân cấp thác | Chỉ bắt được nếu viết riêng luật cho cấp thác. Bộ kiểm "số không có trong nguồn" thường không đọc số La Mã. |
| "suitable for swimmers and less experienced paddlers" | Không có. **Lời hứa an toàn sai**, hại nhất cho agency. | Không (lỗi nghĩa) |
| "intermediate whitewater", "one of Nepal's primary rafting corridors" | Không có; model tự thêm kiến thức | Không |
| "lunch… partway through" | Nguồn **tự mâu thuẫn**: lịch trình ghi "short lunch break" giữa chặng, inclusions ghi lunch "after accomplishing the rafting" | Không, trừ khi bảng dữ kiện đánh dấu mâu thuẫn |

→ Ở ca này code gần như **không bắt được gì**. Đó đúng là lý do thước chính của A/B phải là lỗi nghĩa.

### 4.2 Bảng dữ kiện (đầu vào duy nhất của người viết mới)

| Khoá | Giá trị | Nguồn |
|---|---|---|
| duration | 1 day | `duration` |
| route | Kathmandu → Fishling (put-in) → Mugling | itinerary |
| drive | 3–4 h Kathmandu → Fishling, after early breakfast at hotel | itinerary |
| on_river | about 4 h, Fishling → Mugling; safety briefing first | itinerary, summary |
| scenery | boulders, landscapes with lush greenery, river beaches, fewer other rafters | summary |
| meals | lunch on the river bank (included) | inclusions |
| **CONFLICT** | lunch during the run (itinerary) hay after the run (inclusions)? | itinerary vs inclusions |
| included | rafting with experienced guide and crew, camping gear, lunch | inclusions |
| not_included | drinks, camera/phone/laundry, insurance, costs from natural events | exclusions |
| after | return to Kathmandu, or continue to Chitwan or Pokhara | itinerary |
| **MISSING** | cấp thác, tuổi tối thiểu, có cần biết bơi không, xe đi/về có bao gồm không, giá | — |
| **DO NOT USE** | "Temple Tiger", "Venture Travel" (tên nhà cung cấp lọt trong nguồn) | summary, exclusions |

### 4.3 Bản "người viết mới" (W: văn ngắn, chỉ dùng bảng)

> **Name:** Trishuli River Rafting — 1 Day (Nepal)
> **Subtitle:** About 4 hours on the Trishuli from Fishling to Mugling, with lunch on the riverbank
> **Summary:** An early start from Kathmandu and a 3–4 hour drive to the put-in at Fishling. After a safety briefing from your river guide, you spend about 4 hours rafting down the Trishuli to Mugling, past boulders, green hillsides and quiet river beaches. Lunch is served on the riverbank. From Mugling you can head back to Kathmandu or continue to Chitwan or Pokhara.
>
> **Day 1 — Kathmandu to Mugling on the Trishuli**
> After an early breakfast at your hotel in Kathmandu, drive 3–4 hours to Fishling. Your guide gives a full safety briefing, then you raft about 4 hours downstream to Mugling, with lunch on the riverbank. From Mugling, return to Kathmandu or travel on to Chitwan or Pokhara.
>
> **SEO meta (145 ký tự, trọn câu):** 1-day Trishuli River rafting in Nepal: drive from Kathmandu to Fishling, then about 4 hours on the river to Mugling, with lunch on the riverbank.

Không có cấp thác, không có lời hứa an toàn. Bữa trưa không ghi giờ, vì nguồn đang mâu thuẫn. Văn vẫn đọc trôi, nhưng ngắn hơn khoảng một nửa.

### 4.4 Bản "trang ngắn" (E: phương án B)

> **At a glance**
> - 1 day · Kathmandu → Fishling → Mugling
> - Drive: 3–4 h to the put-in at Fishling
> - Rafting: about 4 h, Fishling to Mugling, with a safety briefing first
> - Included: experienced rafting guide and crew, equipment, lunch on the riverbank
> - Not included: drinks, insurance, personal expenses
> - After the trip: back to Kathmandu, or on to Chitwan or Pokhara
>
> **Day 1 — Kathmandu to Mugling on the Trishuli**
> About 4 hours on the Trishuli, past boulders and quiet river beaches.
> Route: Kathmandu – Fishling (drive 3–4 h) – Mugling (raft about 4 h) · Meals: lunch

**Danh sách hỏi nhà cung cấp** (chỉ trong admin, không hiện cho khách):
1. Cấp thác của chặng Fishling–Mugling? Có cần biết bơi không, tuổi tối thiểu bao nhiêu?
2. Bữa trưa ăn giữa chặng hay sau khi xuống thuyền?
3. Xe Kathmandu → Fishling và xe từ Mugling đi tiếp có bao gồm không?

**Ví dụ này cho thấy gì:**
- Cả W và E đều xoá được lỗi nặng nhất (cấp thác bịa, hứa an toàn). Nhưng W làm được là **nhờ bảng dữ kiện ghi rõ chỗ thiếu**, không nhờ model giỏi hơn. A/B phải kiểm điều đó trên model rẻ, khi người viết **không** biết trước đề.
- E an toàn nhất nhưng rất mỏng. Khách muốn biết "thác cỡ nào" thì trang chưa trả lời được, cho tới khi nhà cung cấp trả lời câu 1.

## 5. Đề xuất điều chỉnh kế hoạch S247–S249

| Phiên | Giữ | Đổi / thêm | Chi phí |
|---|---|---|---|
| S247 | Bảng dữ kiện + bộ kiểm code trên 50 bài S1 cũ; báo TPR/TNR | **Thêm:** panel chấm lại 10–15 trang hai lần để đo độ lặp. Rubric chốt danh sách lỗi nghĩa + câu so cặp "agency dùng trang nào". Bảng dữ kiện có thêm mục MISSING, CONFLICT, DO NOT USE. Lưu ý: giá trị kiểu "route" là tóm tắt, sẽ trượt tiêu chí "khớp nguyên văn 100%"; tách hai loại trường "trích nguyên văn" và "tóm tắt có trỏ câu gốc". | $0–1 |
| S248 | Phẫu thuật prompt S1 sau flag; ví dụ mẫu ngoài golden set | **Thêm:** dựng A+ (oracle + meta riêng, người viết cũ) và E (code dựng khung + 1 câu/ngày). Giữ tiêu đề `Day N —`. Sàng 3 model trên 12 tour ngoài golden set. | khoảng $2,5 + thử 3 tour khoảng $0,1 |
| S248–S249 | Hai lần chạy, mỗi lần ≤ $10; panel mù, đọc toàn nguồn; anh phân xử bất đồng | **Thay** 5 nhánh × 50 tour bằng run 1 (25 tour × A+/A'/W/E) → nhìn giữa chừng → run 2 (25 tour × A+/W/E). **Bỏ** luật "vượt \|A'−A\|" và mục tiêu 4/18 → 10/18 làm tiêu chí đạt/trượt (chỉ còn mô tả). Phân tầng kết quả theo độ giàu nguồn. | khoảng $5–12 |
| S250 (nếu cần) | Nối nhánh thắng ở chế độ shadow | **Nếu chưa rõ:** +50 tour ngoài golden (A+/W/E) trước khi nối. **Nếu W thua:** nối E làm mặc định, dọn editor `/admin/review` (1 phiên), gửi chị Thư đề xuất trung tính về 50 tour ưu tiên + hỏi nhà cung cấp. | $3,5–10,5 |

Thời gian của anh: khoảng 1–2,5 giờ cho mỗi vòng phân xử, cộng khoảng 1 giờ sửa ví dụ mẫu ở S248.

## 6. Quyết định cần anh duyệt

1. **Thước chính của A/B.** Đề xuất: lỗi nghĩa / khẳng định kiểm được, cộng so cặp mù. Đạt/sửa nhẹ chỉ báo cáo. Lỗi code chỉ là cổng.
2. **Số nhánh và cách chọn model.** Đề xuất: sàng Haiku/Luna/Sonnet trên 12 tour ngoài golden, rồi xác nhận bằng A+/A'/W/E trên 50 tour golden, chia 2 lần chạy.
3. **Trang ngắn E.** Đề xuất: đưa vào A/B ngay từ S248 như một nhánh, không để làm đường lui.
4. **Luật dừng và chuyển sang B.** Đề xuất: sau run 1, dừng W nếu tỷ lệ lỗi W/A+ ≥ 0,9 và so cặp ≤ 50%. Ở n = 100, chuyển B nếu cận trên ≥ 0,9 hoặc so cặp ≤ 55%. Nói trước: kết cục dễ nhất là phải thêm 50 tour.
5. **Người sửa nhẹ và nhóm chị Thư.** Đề xuất: chưa gửi gì cho chị Thư bây giờ. Sau A/B, gửi một đề xuất trung tính về 50 tour ưu tiên + hỏi nhà cung cấp; ai sửa chữ là chị quyết.



Các file liên quan:
- `/home/nghiep/projects/AA-Ecosys/.tmp-session/s246-q48/power.py`
- `/home/nghiep/projects/AA-Ecosys/.tmp-session/s246-q48/power-out.txt`
- `/home/nghiep/projects/AA-Ecosys/.tmp-session/s246-q48/s1-length-vs-label.json`
- `/home/nghiep/projects/AA-Ecosys/.tmp-session/s246-q48/example-s1-037.md`
- `/home/nghiep/projects/AA-Ecosys/docs/eval/aa729/fixture-1.1.0.json` (s1-008, s1-037)
- `/home/nghiep/projects/AA-Ecosys/docs/audits/2026-10-21-S246-content-quality-advisory/README.md`
