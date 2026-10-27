# AA-784: spot check mù vòng 3 (luật r3, CIS `43a92134`)

Ngày 27/10/2026 (S253). Tác nhân: Claude Code. Thẻ do GPT-6 Luna viết, Haiku 4.5 kiểm. Luật r3 nằm ở CIS #1065, bản deploy trên Dev là `43a92134`.

## Cách làm

- Chọn 20 thẻ `auto_checked` mới: không lấy lại thẻ của vòng S252 hay vòng 2, và mỗi nước tối đa 2 thẻ.
- Dựng lại 20 thẻ bằng job `place_cards_build` `8da054d1`, tốn $0,045. Kết quả: 14 thẻ `rebuilt` và 6 thẻ `country_changed`.
- 6 thẻ `country_changed` là các đối tượng xuyên biên giới: DMZ (2 thẻ), Gobi, Kanchenjunga Range, Irkutsk, Mahalangur Himal. Guard rebuild từ chối mọi bản nháp đổi nước, nên các thẻ này giữ nguyên giá trị cũ, ví dụ region "Korean Peninsula", locality "Khumbu". Vì không có bản dựng theo luật r3, 6 thẻ này bị loại khỏi packet (xem mục "Còn lại").
- Packet mù gồm 14 thẻ (`packet.json`). Mỗi thẻ có 2 người gán nhãn độc lập (agent tra web, có URL và câu trích). 4 thẻ phải phân xử. Kết quả cuối ở `labels.json`.

## Số liệu

| Chỉ số | S252 | Vòng 2 | **Vòng 3** | Cổng (design §7) |
|---|---|---|---|---|
| FK: fact sai / fact giữ lại | 3/83 = 3,6% | 3/79 = 3,8% | **1/51 = 2,0%** | ≤ 3%: **đạt** |
| UK: fact không kiểm được | 0 | 0 | 1 | — |
| LK: lọt chi tiết tour | 0 | 0 | **0** | ≤ 2%: đạt |
| WI: sai danh tính | 0 | 0 | **0** | ≤ 1 thẻ: đạt |
| Sai nước | 0 | 0 | **0** | 0: đạt |
| Thẻ sai locality hoặc region | 7/20 | 6/20 | **3/14** | chỉ báo cáo |

## Lỗi còn lại

- **Fact sai (1):**
  - E06 Last Water Point: thẻ ghi điểm này nằm "giữa Horombo Hut và Kibo Hut, trên tuyến trên". Theo SummitPost, đoạn này có hai nhánh, và điểm nước cuối (4.130 m) nằm trên nhánh trên. Câu "giữa hai trại" đúng, nhưng chữ "upper route" bị chấm sai.
- **Locality/region (3):**
  - E12, phà Hong Kong–Macau: region "Hong Kong / Macau" là luật r3 cố ý ghi cho tuyến nối hai đơn vị. Người gán nhãn muốn để trống. Đây là khác nhau về quy ước, không phải sai dữ kiện.
  - E15, Gasa Hot Spring: suối nằm dưới thung lũng, cách Gasa Dzong khoảng 2 giờ leo, nên locality "Gasa" là thị trấn gần nhất.
  - E16, Harappa: locality bị xoá vì trùng tên địa điểm (`is_place`), trong khi di chỉ nằm ngay ở làng Harappa.
- **Giá trị cũ trên 6 thẻ xuyên biên giới** (không chấm): luật r3 chỉ áp khi thẻ được dựng lại. Guard đổi nước chặn bản dựng lại nên region/locality cũ vẫn còn. Muốn sửa phải tách việc làm sạch locality/region ra khỏi bản nháp đổi nước; việc này ghi ở backlog.

## Kết luận

Ba cổng chính (FK, LK, WI) cùng chỉ số sai nước đều đạt trên bản dựng theo luật r3. Hai vòng trước trượt cổng FK, vòng này đạt. Locality/region giảm từ 6/20 xuống 3/14, và cả ba ca còn lại đều là ca biên.
