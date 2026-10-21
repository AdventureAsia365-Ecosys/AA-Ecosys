# adventure.asia làm thước "viết tốt" cho S1 (S246)

## 0. Trả lời ngắn (anh hỏi đúng chỗ nào, và kết luận)

- Anh đúng ở hai điểm. Thứ nhất, khung trang của adventure.asia đáng học: thứ tự mục, tiêu đề ngày, dòng LEVEL, danh sách bao gồm/không bao gồm. Thứ hai, site giờ là chợ B2B cho agent. Vì vậy trang tour phải là bản trắng (white-label) để agent bán lại được ngay.
- Câu chữ trên site thì không làm thước chất lượng được. Site có hai đời trang, và đời nào cũng trượt rubric golden của mình:
  - **Đời cũ (khoảng 650/662 trang):** chữ của nhà cung cấp. Có lỗi chính tả, chữ quảng cáo ("A journey that you will always remember!"), chèn câu "Join Adventure Asia..." giữa ngày, có cả "Book now".
  - **Đời mới (ID 700+):** giọng bình tĩnh, cụ thể. Nhưng vẫn bịa dữ kiện, bỏ bữa ăn/chỗ ngủ/km, gắn LEVEL sai, thêm câu rỗng. Đó cũng chính là lỗi chính của S1.
- Kết luận: học **khung trang và lập trường white-label**. Không học **câu chữ**. Thước "viết tốt" vẫn là: đúng nguồn, giữ đủ dữ kiện vận hành, ngắn khi nguồn mỏng.
- Có hai phát hiện phụ nhưng gấp hơn chuyện giọng văn:
  1. 9 tour S1 đã publish ghi Adventure Asia là đơn vị tổ chức. Trong đó 8 tour không có tên này trong lịch trình nguồn. Nguyên nhân khả dĩ: prompt fixer A1 vẫn ghi "Adventure Asia brand standards".
  2. Site đời mới là một bản viết lại song song của chính các sản phẩm CIS đang có (169/212 tour trùng tên là trang ID 700+). Bản này viết ngoài CIS, nên trái tinh thần ADR 0002.
- Ghi chú quy trình: hai lane cùng lấy trang site bằng curl, cách nhau 2 giây, để giữ nguyên văn. Lane 1 gửi 21 request, lane 2 gửi 9, tổng khoảng 30. Con số này **vượt trần 25 trang** đặt ra. Mọi request đều HTTP 200 và chỉ đọc. Lane phản biện không gửi request nào.

## 1. adventure.asia viết thế nào (cấu trúc, giọng, độ cụ thể; trích ví dụ có link)

**Định vị 2026.** Trang chủ ghi "THE ADVENTURE TRAVEL MARKETPLACE FOR AGENTS & OPERATORS". Trang about (<https://adventure.asia/about>) hứa "Ready-to-sell trip pages" và "we never sell around you". Giọng thương hiệu ngắn, khẳng định, cụ thể, ví dụ "A named human will contact you within 2 business days."

**Khung trang tour (mọi trang giống nhau).**
- H1 = tên tour. Hộp dữ kiện gồm Duration / Destination (chỉ thành phố đầu) / "From $X".
- Sau đó lần lượt: Summary một đoạn, Highlights 3–8 gạch đầu dòng, Included / Not included, rồi "Day by day Itinerary".
- Mỗi ngày gồm "Day N", tiêu đề lộ trình ("Almaty to Altyn-Emel National Park"), dòng LEVEL, thân bài, và có thể có thẻ khách sạn.
- Site không có mục quy mô đoàn, độ khó tổng hay thông tin thực tế riêng.
- Thời lượng ghi không thống nhất: "12 days 11 nights", "19 DAYS", và có trang chỉ ghi "8" trong khi tóm tắt nói 7 ngày.

**Hai đời trang, hai giọng.**

| | Đời cũ (ID ~1–700) | Đời mới (ID 700+) |
|---|---|---|
| Giọng | trộn "you" (tới 7% số từ) và "we" | ngôi ba, gần như 0 "you"/"we" |
| Từ quảng cáo/trang | tới 39 (Vietnam 136) | 0–2 |
| Dấu chấm than/trang | 0–7 | 0 |
| Số liệu (km, giờ, độ cao)/1.000 từ | trang tốt nhất 24–26 (EBC 39, Laos 119) | 0–7,8 |
| Từ trung vị/ngày | 64–551 | 60–104 |

Để so: S1 có trung vị 56 từ/ngày, 3,2 số liệu/1.000 từ và 0,29 từ quảng cáo/1.000 từ. **S1 đã hơn site về độ "sạch quảng cáo".**

**Mẫu đáng học (trích nguyên văn).**
- Độ cao đi liền giờ đi bộ: "...head north to Chablung (2700m)... to our overnight lodge in Phakding (3 hrs)." ([EBC 39](https://adventure.asia/itinerary/15-day-trek-to-the-everest-base-camp-39/))
- Dòng dữ kiện cuối ngày: "Camp at Jele Dzong. Altitude 3480m / Trekking Today: 8km, 4-5 hours. 1090m ascent." ([Bhutan 35](https://adventure.asia/itinerary/trekking-in-bhutan-through-the-tsaluna-path-35/))
- Ghi km kèm loại mặt đường: "42 km (26 mi) of biking on mixed paved and dirt road, normally taking about 3.5 hours." ([Laos 119](https://adventure.asia/itinerary/laos-bike-and-hike-tour-119/))
- Câu kết đời mới: "A vehicle transfer completes the journey to Chiang Rai. Distance: 48 km. Overnight in Chiang Rai." ([702](https://adventure.asia/itinerary/chiang-mai-to-luang-prabang-private-cycling-702/))
- Chỗ ngủ ghi trung thực: "the Banaue Hotel or a comparable property" ([772](https://adventure.asia/itinerary/philippines-cordillera-trail-hiking-baguio-to-banaue-772/))

**Mẫu cần tránh (trích nguyên văn).**
- Quảng cáo: "as primitive as primitive can be" (Rajasthan 41), "Book now to secure your..." ([324](https://adventure.asia/itinerary/discover-chiang-mai-mae-hong-son-pai-324/)).
- Lộ tên nhà cung cấp: "one of the ITrekNepal staff" (EBC 39).
- Sai kiến thức: "The guide explains the subak irrigation system" trên tour Ifugao (772). Subak là hệ thống của Bali.
- Bịa dữ kiện trên [1010](https://adventure.asia/itinerary/silk-road-traverse-kazakhstan-kyrgyzstan-and-xinjiang-1010/): "largest mosque in China by capacity", "over 3,600 meters", "below zero even in July and August". Nguồn af0ded16 không có câu nào trong số này.
- Câu rỗng: "The pace is deliberate.", "asks something of those who walk it" ([Best of China 1105](https://adventure.asia/itinerary/best-of-china-1105/)).
- Lỗi định dạng lọt ra trang: "Day 16 -- |" (1010).
- Thông tin cũ: trang Vietnam vẫn ghi luật nhập cảnh COVID năm 2022.

## 2. So với nguồn và S1 của mình (bảng 5 tour: nguồn / trang AA / S1 / nhãn)

| Tour (site) | Nguồn DB | Trang AA | S1 published | Nhãn golden |
|---|---|---|---|---|
| af0ded16 ↔ [1010](https://adventure.asia/itinerary/silk-road-traverse-kazakhstan-kyrgyzstan-and-xinjiang-1010/) Silk Road | Chính là chữ site đời cũ: định dạng LEVEL, câu "Join Adventure Asia...". Ghi Lunch/Dinner/Overnight 11 lần mỗi loại | Bịa 3 dữ kiện; bỏ phần lớn bữa ăn và chỗ ngủ; lọt "Day 16 --"; LEVEL lệch 1–2 ngày (không phải san phẳng cả tour) | Chưa chấm | Không có (ngoài golden) |
| dfdb4017 ↔ [324](https://adventure.asia/itinerary/discover-chiang-mai-mae-hong-son-pai-324/) Chiang Mai–MHS–Pai | Có lựa chọn cưỡi voi/xe bò và Chiang Dao | Là bản nhà cung cấp khác, ngắn hơn; bỏ các lựa chọn đó; có "Book now" | Giữ các lựa chọn | Không có (ngoài golden) |
| s1-005 [Ride the Trail 859](https://adventure.asia/itinerary/ride-the-trail-859/) | 12 ngày đạp xe, 45–85 km/ngày | 0 số km, 0 từ chỉ đạp xe; bỏ bữa ăn; cả 12 ngày "Fairly Easy", kể cả ngày site tự gọi là "longest and most demanding" | Giữ 17 số km; nhưng bịa "three countries" và ghi sai cửa khẩu Dak To | fail heavy |
| s1-024 [Sri Lanka 883](https://adventure.asia/itinerary/luxury-family-holiday-in-sri-lanka-883/) | Nhóm ngày: Bentota 1–3, Yala 4–5, Kitulgala 6–7… | Giữ đúng nhóm ngày; bỏ ngày rafting; bịa "kite surfing" | Vỡ cấu trúc: "Departure" ở Day 7 giữa tour | fail reject |
| s1-049 [Cross-Mountain 645](https://adventure.asia/itinerary/cross-mountain-spine-cycling-tour-645/) | Có số km/độ cao theo chặng | Thêm Shei-Pa, cá hồi, cáp treo, chặng phụ 30 km không có trong nguồn; ngày 110 km / 2.081 m ghi "Fairly Easy" | Khớp nguồn, chỉ cần sửa nhẹ | pass light |

Đọc bảng:
- Trên 6 tour golden có trang site, site hơn S1 ở 2 tour, ngang 2, kém 2. Site **không phải chuẩn vàng**.
- So sánh này bị nhiễu. Site có thể viết từ một bản nguồn khác, mới hơn của nhà cung cấp. Vì vậy một "lỗi bịa" của site chưa chắc là bịa. Không nên rút ra luật "site tốt hơn khi nguồn mỏng" từ n = 6.
- Bài học thật nằm ở Sri Lanka. Khi nguồn ghi gộp nhóm ngày, giữ đúng nhóm ngày và viết mỗi ngày một dòng ngắn. Cách này tốt hơn tự dựng lại cấu trúc.

## 3. Vậy việc của S1 là gì (dựa trên ADR/CONTEXT)

- `apps/AA-CIS-App/CONTEXT.md` (mục A1, dòng ~1535) và AA-535 định nghĩa S1: viết `generated_content` bằng giọng **trung tính, không thương hiệu**. Đây là nền chung để mọi tenant viết lại ở T2, và có kiểm tra bám nguồn raw.
- ADR 0001 và 0002: CIS là hệ thống lưu nội dung gốc, và chỉ CIS viết nội dung.
- Nên S1 **không bắt chước giọng adventure.asia**. Việc của S1 gồm:
  1. Tái cấu trúc nguồn nhà cung cấp theo lối dữ kiện trước.
  2. Giữ đủ dữ kiện vận hành (km, giờ, độ cao, bữa ăn, chỗ ngủ, LEVEL nếu nguồn có).
  3. Viết lại để bài là duy nhất. Lý do: một số nguồn chép của hãng lớn (15 lịch trình dùng chữ "CEO" của G Adventures), và 13 nguồn China là chữ site đời cũ.
  4. Là bản trắng: không có tên Adventure Asia, không tên nhà cung cấp, không lời kêu gọi đặt tour.
- Giọng thương hiệu ("The best of Asia is hidden", "Real trips. Checked on the ground") thuộc tầng T-series, không thuộc S1.

## 4. Điều chỉnh kế hoạch S247-S249 (exemplar, rubric, nhánh E, style guide)

Thay đổi nhỏ. Không đổi thứ tự, không thêm chi phí, không thêm cổng vào pipeline.

| Bước | Điều chỉnh |
|---|---|
| S247: bảng dữ kiện + bộ kiểm code | Thêm 2 kiểm tra $0 vào **bộ kiểm offline** (không đưa vào cổng pipeline, giữ lệnh đóng băng). (i) **Giữ dữ kiện nguồn:** số liệu, bữa ăn, chỗ ngủ, LEVEL có trong bảng dữ kiện mà trang thiếu. (ii) **Rò tên:** "Adventure Asia", tên nhà cung cấp, chữ "CEO" kiểu G Adventures xuất hiện mà nguồn không có. Rubric thêm 4 loại lỗi nếu chưa có: bịa chi tiết cụ thể, bỏ bữa ăn/chỗ ngủ, LEVEL sai/san phẳng, câu rỗng trừu tượng. |
| S248: phẫu thuật prompt | Ví dụ mẫu: 3–5 tour **ngoài golden**, đặt trong khung trang AA, **chỉ điền từ bảng dữ kiện CIS**, không dán câu nào của site. Ứng viên đầu: af0ded16, dfdb4017, cộng thêm 1–3 tour. Mượn 3 mẫu tốt: dòng dữ kiện cuối ngày, chỗ ngủ ghi trung thực, bối cảnh địa danh gói trong một mệnh đề. Cùng PR, sửa `FIX_SYSTEM` / "Adventure Asia brand standards" trong `apps/AA-CIS-App/services/content_generation/flag_fix_node.py:194,222` cho trung tính. PR này rủi ro, sẽ có subagent review độc lập như đã định. |
| S248: sàng 12 tour ngoài golden | Đưa af0ded16 và dfdb4017 vào 12 tour sàng nếu không dùng làm ví dụ mẫu. Tour nào đã làm ví dụ mẫu thì loại khỏi bộ sàng và khỏi mẫu mở rộng "+50 tour ngoài golden". |
| Nhánh E (S248) | Củng cố, không đổi hướng. Dùng khung site: hộp dữ kiện, `Day N — A to B` (giữ tiền tố `Day N —` cho `parse_days` của TripPlanner; tiêu đề viết hoa đầu câu, không ALL CAPS), LEVEL nếu nguồn có, dòng Meals/Overnight, Included/Excluded. |
| A/B (S248–S249) | Không đổi. **Không** thêm nhánh "site": đầu vào khác, nên không chấm chung một bảng dữ kiện được. |
| Style guide | Dùng bản nháp ở Phụ lục. Mọi độ dài và số liệu là **trần, hoặc "nếu nguồn có"**, không phải sàn. Bỏ đề xuất "tăng mật độ số liệu lên 11–26/1.000 từ" của lane 1. Đề xuất đó đưa lại đúng áp lực "real number"/"expand" mà S248 đang gỡ. |

## 5. Rủi ro (trùng nội dung SEO, rò rỉ golden, phóng đại)

- **Trùng nội dung SEO: thấp, chỉ tăng nếu mình chép.**
  - Trang site cho index và có canonical tự trỏ.
  - Hiện S1 và site trùng khoảng 0–0,5% chuỗi 6 từ. Với 13 nguồn China là chữ site cũ, S1 giữ 2–15%, chấp nhận được.
  - Rủi ro thật có hai loại. (a) Dán câu site vào ví dụ mẫu: model sẽ lặp câu mở "This N-day private itinerary moves..." trên 900 trang. (b) Site và trang tenant/TripPlanner cùng đăng hai bản viết lại của một sản phẩm. Loại (b) là chuyện kiến trúc (site nên đọc `catalog.v_tour`), không phải luật viết.
- **Rò rỉ golden: cao nếu không chặn.**
  - 14/50 tour golden S1 có trang site: 00f15c2d/1043, 3d359266/1023, efb52e00/157, a54844fe/726, 15b02210/909, 196df8e7/942, 71cacbb0/880, 86f4dc83/883, cb970f00/891, 34164145/644, 7d64faca/657, 913bde35/645, d398ffe0/653, 3fa33633/859.
  - Chữ site của 14 tour này không được dùng làm ví dụ mẫu, mốc rubric, "đáp án tham khảo" cho panel, hay bằng chứng gán nhãn.
  - af0ded16 và dfdb4017 sạch: không thuộc golden.
- **Phóng đại / bịa: rủi ro chính nếu bắt chước giọng site.**
  - Giọng đời mới cùng họ với giọng LLM của S1, mà lỗi chính của giọng này là bịa. Giọng bình tĩnh không có nghĩa là đúng nguồn.
  - Ép "mỗi highlight phải có một số" hay "ngày 50–110 từ" sẽ đẩy model bịa số khi nguồn mỏng. Hiện S1 đã giữ ít số hơn nguồn ở 420/870 tour, và tự thêm số ở 127 tour.
- **Rò thương hiệu:** 9 tour S1 đã publish ghi Adventure Asia là đơn vị tổ chức. Điều này trái lời hứa "Ready-to-sell" với agent. Cần sửa prompt fixer (mục 4) và chạy kiểm rò tên trên toàn catalog ở S247.

## 6. Quyết định cần anh duyệt (mỗi câu có đề xuất)

1. **W1. Dùng adventure.asia thế nào?** Đề xuất: chỉ dùng khung trang, giọng bình tĩnh và lập trường white-label. Không coi chữ site là chuẩn, không dùng làm ví dụ mẫu nguyên văn.
2. **W2. Ví dụ mẫu S248.** Đề xuất: 3–5 tour ngoài golden (af0ded16, dfdb4017 + 1–3), khung AA, điền chỉ từ bảng dữ kiện. Loại hẳn 14 tour golden có trang site. Anh sửa ví dụ mẫu khoảng 1 giờ, như kế hoạch cũ.
3. **W3. Đo số liệu.** Đề xuất: đo **tỷ lệ giữ** dữ kiện nguồn bằng code trong bộ kiểm S247. Không đặt mục tiêu mật độ số.
4. **W4. Rò tên Adventure Asia trong S1.** Đề xuất: thêm kiểm rò tên vào bộ kiểm S247, và sửa prompt fixer cho trung tính trong PR S248 (đã có review độc lập).
5. **W5. Bản viết lại song song trên site.** Đề xuất: anh cho biết ai viết bản đời mới tuần này. Câu hỏi "site có nên đọc catalog CIS không" (ADR 0002) được ghi vào backlog dạng câu hỏi chờ anh. Chưa mở issue Linear nếu anh chưa đồng ý.

---

## Phụ lục: Hướng dẫn giọng văn AA (bản nháp)

```text
AA S1 VOICE GUIDE (draft, S246) — neutral master copy, resellable as-is

Purpose
- Write a neutral, white-label tour page an agent can resell unchanged.
- Facts come only from the source fact sheet. Never write to a length target.

Page shape (in this order)
- Name; facts box (duration as "N days" exactly per the source; start and end city).
- Summary: one paragraph, at most 120 words. Open with duration, private/group
  (if stated), start -> end, main activity. Then 2-3 named stops. No rating, no call to action.
- Highlights: 3-6 bullets, each a concrete noun phrase drawn from the source.
  Include a number only if the source gives one.
- Included / Not included: copy the source lists, normalised. Never upgrade
  ("meals as per plan" is not "all meals").
- Day blocks: "Day N — A to B" in sentence case, never ALL CAPS. If the source groups
  days ("Days 1-3 in Bentota"), keep the grouping and write one short line per day.

Day body
- At most ~110 words; a thin source day may be one or two sentences.
- Third person or a light second person, present tense.
  Order: morning -> main activity -> afternoon -> arrival.
- End with a fact line built only from source fields, omitting what the source lacks:
  "Ride/Trek/Drive: X km, Y h, +Z m. Overnight: <place, lodging type>. Meals: B/L/D."
- Copy LEVEL per day only when the source states it. Never default or average it.
- Lodging: name it as the source does; "or similar" only if the source says so.

Allowed background
- One clause of general background about a named place is fine
  (e.g. "Issyk-Kul, a high mountain lake").
- Anything about what travellers do, see, eat, ride, or where they sleep must be in the source.

Never
- Hype: breathtaking, stunning, unforgettable, once-in-a-lifetime, paradise, exotic.
- Abstract filler: "deliberate", "unhurried", "rewards attention", "a different register",
  "asks something of those who walk it".
- Brand or operator names: Adventure Asia, supplier names, "CEO" as a guide title.
- Calls to action: "Book now", "Join us", "awaits".
- Invented specifics: temperatures, superlatives, altitudes, durations, optional activities.
- Dropping source facts: km, hours, altitude, meals, overnights, sold activities.
- Dated rules (visa or COVID entry) and leaked formatting ("Day 16 -- |").

Meta
- Title: 60 characters or fewer, keyword + route.
- Description: 140-160 characters, factual, with duration and one source number if any.
  No brand suffix, no "seamless support".
```
