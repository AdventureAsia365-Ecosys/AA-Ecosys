# AA-784: spot check mù 20 thẻ, vòng 2 (thẻ dựng theo luật S253)

Ngày 27/10/2026 (S253). Tác nhân: Claude Code. Thẻ do GPT-6 Luna viết, Haiku 4.5 kiểm. Luật mới ở CIS #1059 (`83dfd114`).

## Cách làm

- Chọn 20 thẻ `auto_checked` theo md5 (seed `s253-spot`), tối đa 2 thẻ một nước, không lấy lại thẻ của vòng S252.
  Cả 20 thẻ được dựng lại bằng luật mới (job `place_cards_build {"card_ids": […]}`, khoảng $0,10) rồi mới xuất packet.
- `packet.json` là bản mù: tên, locality, region, country, naming_note, các fact, câu itinerary. Không có id, model hay route.
- Mỗi thẻ có 2 người gán nhãn độc lập (agent tra web, mỗi fact phải có URL và câu trích). Chỗ hai người lệch nhau thì người thứ ba phân xử; 3 thẻ phải phân xử.
- Kết quả cuối: `labels.json`.

## Số liệu

| Chỉ số | S252 (luật cũ) | S253 (luật mới) | Cổng (design §7) |
|---|---|---|---|
| FK: fact sai / fact giữ lại | 3/83 = 3,6% | **3/79 = 3,8%** | ≤ 3%: **không đạt** |
| UK: fact không kiểm được | 0 | 0 | — |
| LK: lọt chi tiết tour | 0 | **0** | ≤ 2%: đạt |
| WI: sai danh tính | 0 (1 chưa rõ) | **0** (1 chưa rõ: D20) | ≤ 1 thẻ: đạt |
| Sai nước | 0 | **0** | 0: đạt |
| Thẻ sai locality hoặc region | 7/20 | **6/20** | chỉ báo cáo |

## Lỗi

Fact sai (3). Cả ba đều là con số lệch nhẹ, không còn khẳng định "hiện tại" sai:
- D04: Kruba Srivichai mất năm 1939, không phải 1938.
- D17: đèo Ghurchi Lagna cao 3.458 m, không phải "khoảng 3.480 m".
- D20: công viên Panfilov lập năm 1872, không phải 1870.

Locality / region (6). Kiểu lỗi đã đổi: luật S253 không còn ghi vùng địa lý hay thị trấn gần nhất, nhưng **xoá quá tay**:
- Locality bị bỏ trống dù có giá trị đúng:
  - D04: tượng đài trong Chiang Mai;
  - D11: Yongdusan Park, công viên đô thị ở Jung-gu, Busan;
  - D16: hang Ssangyong, Hallim-eup, thành phố Jeju;
  - D13: A Lưới.

  Nguyên nhân: luật "chữ đầu là park / cave… → điểm hẻo lánh" bắt nhầm cả công viên và hang trong đô thị.
- Region bị bỏ trống với thành phố cấp tỉnh:
  - D20: Almaty, thành phố trực thuộc trung ương của Kazakhstan;
  - D13: Huế, thành phố trực thuộc trung ương từ 2025.
- D03 (đường biên Myanmar–Thái Lan): một đối tượng xuyên biên giới không nên có một locality hay region đơn lẻ.

## Sửa hệ thống (vòng 3, S253)

1. Chỉ coi là "hẻo lánh" (bỏ trống locality) khi là vườn quốc gia, khu bảo tồn, đỉnh, đèo, trại, sông băng, hồ ngoài đô thị. Công viên đô thị, hang trong một thành phố hay huyện, tượng đài thì giữ locality.
2. Region được trùng locality khi thành phố là đơn vị cấp 1. Thẻ có thành phố hoặc tỉnh cấp 1 rõ ràng thì phải điền region, không để trống.
3. Đối tượng xuyên biên giới (đường biên, cầu, sông chung) thì locality và region để trống, hoặc ghi "A / B" như cầu ở D19.
4. Con số chính xác (năm sinh, năm mất, năm thành lập, độ cao): checker phải kiểm từng con số và hạ xuống "unsure" khi không chắc. Writer làm tròn hoặc bỏ con số không chắc.
