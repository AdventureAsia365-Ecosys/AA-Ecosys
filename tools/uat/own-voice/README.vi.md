# Thu giọng của chính mình để làm giọng đọc tiếng Việt cho video UAT

Hướng dẫn đi kèm skill `aa-uat-video` (công cụ `tools/uat/own-voice/clone.py`).

Mô hình dùng: **VieNeu-TTS v3 Turbo** (Apache-2.0, cả code lẫn trọng số; chạy trên CPU của máy này, không
GPU, không gọi API, $0). Nguồn giấy phép: <https://huggingface.co/pnnbao-ump/VieNeu-TTS-v3-Turbo> (mục
"Usage Rights & Licensing FAQ") và <https://github.com/pnnbao97/VieNeu-TTS/blob/main/LICENSE>.
Model card yêu cầu chỉ nhân bản giọng của người đã đồng ý: chỉ dùng bản thu của chính người đọc, và ghi rõ
người đó đã đồng ý trong báo cáo của phiên.

Mô hình chỉ dùng **tối đa 8 giây** giọng mẫu cho mỗi lần nhân bản. Bản thu dài 1–2 phút để script tự cắt ra
vài đoạn 5–8 giây, thử từng đoạn và giữ đoạn nghe hay nhất. Bản dài cũng dùng được sau này nếu muốn
fine-tune (LoRA) cho giống hơn.

## 1. Chuẩn bị

- **Phòng yên tĩnh**: tắt quạt, điều hoà, đóng cửa sổ. Phòng nhiều rèm, chăn, tủ quần áo thì ít vang hơn phòng trống.
- **Mic**: điện thoại hoặc laptop đều được. Điện thoại cách miệng khoảng **20–30 cm**, hơi lệch sang một bên
  để không bị bật hơi ở các âm "p", "b". Không dùng tai nghe Bluetooth (chất lượng mic rất thấp).
- **Ngồi thẳng, uống chút nước**, đọc bằng giọng tự nhiên như khi giới thiệu sản phẩm cho khách, **giọng miền Nam
  bình thường của người đọc**, tốc độ vừa phải, không cố đọc như phát thanh viên.
- **Ngắt khoảng 1 giây giữa các câu.** Script dựa vào các khoảng lặng này để cắt đoạn.
- Đọc nhầm thì dừng 2 giây rồi đọc lại cả câu, không cần thu lại từ đầu.

## 2. Định dạng file

| Mục | Tốt nhất | Vẫn chấp nhận |
|---|---|---|
| Định dạng | WAV (PCM 16-bit), mono | M4A / MP3 / OGG từ app ghi âm điện thoại (script tự chuyển) |
| Tần số lấy mẫu | 44.1 kHz hoặc 48 kHz | ≥ 22.05 kHz |
| Độ dài | 1–2 phút | tối thiểu 30 giây |
| Nhiễu | im lặng nền, không nhạc, không tiếng người khác | tiếng ồn nhẹ (script có bước khử nhiễu) |
| Âm lượng | to rõ, không bị rè/vỡ ở chỗ to nhất | |

Trên điện thoại: iPhone "Ghi âm" (Voice Memos) → Cài đặt → Ghi âm → Chất lượng âm thanh = **Không nén (Lossless)**.
Android: app ghi âm mặc định, chọn chất lượng cao nhất. Laptop: Audacity (miễn phí), Project Rate 48000, Mono,
File → Export → WAV.

## 3. Đặt file ở đâu

Thả file vào:

```
tools/uat/own-voice/input/
```

Đặt tên ví dụ `giong-01.wav`. Script lấy file mới nhất trong thư mục này. `input/`, `work/`, `out/` nằm
trong `.gitignore`: bản thu giọng không bao giờ vào git.

## 4. Đoạn cần đọc (khoảng 1 phút 30 giây)

Phần A, tiếng Việt (bao đủ sáu thanh: ngang, huyền, sắc, hỏi, ngã, nặng, và các vần hay khác nhau giữa
Nam và Bắc như "v/d/gi", "r", "tr/ch", "s/x", vần "-an/-ang", "-ưu/-iu"):

1. Xin chào, tôi là kỹ sư phụ trách nền tảng du lịch của Adventure Asia.
2. Hôm nay mình sẽ cùng xem nhanh cách khách du lịch tìm và mở một tour trên trang web.
3. Trang chủ hiển thị những tour thật trong danh mục, mỗi tour ghi rõ quốc gia và số ngày.
4. Khách có thể chọn điểm đến như Việt Nam, Thái Lan, Lào, Campuchia hay Bhutan.
5. Ở mỗi điểm đến, trang cho biết có bao nhiêu tour và mỗi tour kéo dài mấy ngày.
6. Lịch trình được chia theo từng ngày: buổi sáng tham quan, buổi trưa nghỉ ngơi, buổi chiều đi dạo phố.
7. Nếu thấy chỗ nào chưa đúng, anh chị cứ ghi chú lại, đội kỹ thuật sẽ sửa ngay trong tuần.
8. Sài Gòn mùa này trời hơi oi, chiều tối thường có mưa rào, nhưng chỉ chừng nửa tiếng là tạnh.
9. Mình ghé quán cà phê nhỏ đầu hẻm, gọi một ly sữa đá, ngồi nghe tiếng xe chạy ngoài đường.
10. Rau răm, rau thơm, giá đỗ và chanh ớt là những thứ không thể thiếu trong tô phở hay hủ tiếu.
11. Chuyến xe khởi hành lúc bảy giờ rưỡi sáng, dự kiến tới Cần Thơ khoảng mười một giờ trưa.
12. Cảm ơn anh chị đã xem, hẹn gặp lại trong video tiếp theo.

Phần B, tiếng Anh (mô hình đọc được cả câu song ngữ; mấy câu này giúp giọng nhân bản đọc tên tiếng Anh
như "Adventure Asia" tự nhiên hơn). Đọc bằng giọng tiếng Anh bình thường của người đọc:

13. Welcome to the Adventure Asia trip planner.
14. A traveller opens a destination page and reads the day by day itinerary.
15. Each tour shows its country, its length and the places it visits.

## 5. Sau khi thả file (agent hoặc người đọc tự chạy)

```bash
cd tools/uat/own-voice
../venv-vi/bin/python -I clone.py
```

- Ra tối đa 3 mẫu `out/clone_w1.mp3`, `clone_w2.mp3`, `clone_w3.mp3`, mỗi mẫu đọc 4 câu phụ đề đầu của TP-PUB-01
  bằng giọng nhân bản từ một đoạn 5–8 giây khác nhau. Người đọc nghe và chọn đoạn giống nhất.
- Đoạn đã chọn được lưu ở `work/voice_w<k>.npz`. Dựng video bằng giọng đó:
  `UAT_VI_VOICE=$PWD/work/voice_w<k>.npz bash ../run.sh scenarios/tripplanner/tp-pub-01.cjs`.
- Thời gian trên máy này: khoảng 25 giây để ghi danh giọng, rồi khoảng **2,5 phút CPU cho mỗi phút giọng đọc**.
  RAM đỉnh khoảng 1,9 GB (hai bước chạy hai tiến trình riêng, không cộng dồn).
- Nếu bản nhân bản nghe rè hay lẫn tiếng vang: thu lại ở phòng yên hơn, hoặc chạy lại với
  `UAT_CLONE_DENOISE=0` khi file gốc đã sạch (khử nhiễu đôi khi làm giọng mỏng đi).

Đường chạy đã được kiểm thử bằng một giọng mẫu có sẵn của VieNeu (Apache-2.0, không phải giọng người thật bên ngoài).
