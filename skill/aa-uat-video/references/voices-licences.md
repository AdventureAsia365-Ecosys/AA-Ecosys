# Giọng đọc và giấy phép (aa-uat-video)

Load khi thêm hoặc đổi giọng TTS. Bảng thử nghiệm đầy đủ (RAM, CPU, ASR WER từng giọng, link model card):
`docs/audits/2026-10-30-S260-uat-video-plan/README.md` §2 + §2.1.

## Luật

1. Chỉ TTS **miễn phí, chạy local** trên CPU của máy (không API, không dịch vụ trả tiền).
2. **Dùng thương mại được** ở cả ba lớp: code, trọng số, giọng preset / dữ liệu huấn luyện. Một lớp NC (non-commercial),
   CPML hay "Unknown" → loại, kể cả khi code là Apache/MIT.
3. Engine GPL dùng được như công cụ local (không ship kèm sản phẩm); giọng đi kèm vẫn xét theo giấy phép riêng của nó.
4. Giọng preset phải có tuyên bố người nói đã đồng ý (model card); nhân bản giọng chỉ với người đọc đã đồng ý.
5. Ghi dòng credit trong index / README gói: vd. "Vietnamese voice: VieNeu-TTS v3 Turbo (Apache-2.0)".

Kiểm một model mới: đọc model card + file LICENSE của repo code **và** của trọng số, ghi link nguồn vào bảng §2.1 của
kế hoạch, rồi mới thử nghe.

## Đang dùng

| Ngôn ngữ | Model / giọng | Giấy phép | Ghi chú |
|---|---|---|---|
| EN | Kokoro-82M qua `kokoro-onnx`, giọng `af_heart` (nữ) | trọng số Apache-2.0, runtime MIT | Nghiệp duyệt S260 |
| VI | VieNeu-TTS v3 Turbo, preset **Thục Đoan** (nữ, miền Nam) | code, trọng số, preset Apache-2.0; preset speaker đã đồng ý | chọn S260; dự phòng: `Adam` (nam Nam), Mỹ Duyên, Kim Thanh |
| VI (máy yếu) | VieNeu-TTS v3 Nano | Apache-2.0 | 24 kHz, ngữ điệu phẳng hơn |
| VI (giọng riêng) | VieNeu v3 Turbo clone, mẫu ≤ 8 s | Apache-2.0; người dùng chịu trách nhiệm về đồng ý | `tools/uat/own-voice/` |

## Đã loại

| Model / giọng | Lý do |
|---|---|
| Piper `vi_VN-vais1000-medium` | Nghiệp nghe và loại (giọng Bắc; đọc "Adventure Asia" thành "VA"). Giấy phép thì được (CC BY 4.0) |
| Piper `en_US-ryan` | CC BY-NC-SA (non-commercial) |
| Piper `vi_VN-vivos-x_low` | dữ liệu VIVOS CC BY-NC-SA 4.0 |
| Piper `vi_VN-25hours_single-low` | giấy phép dữ liệu "Unknown" |
| VietTTS (dangvansam) | code Apache-2.0 nhưng trọng số CC BY-NC |
| F5-TTS base + bản fine-tune tiếng Việt (`hynt/F5-TTS-Vietnamese-ViVoice`, EraX-Smile F5) | CC BY-NC / CC BY-NC-SA 4.0 |
| viXTTS / XTTS-v2 | CPML (Coqui Public Model License, non-commercial) |
| Facebook MMS-TTS `vie` | CC BY-NC 4.0 |
| Fish-Speech 1.5 / OpenAudio S1-mini | CC BY-NC-SA 4.0 |
| CosyVoice 2/3, Chatterbox multilingual, MeloTTS | không có tiếng Việt (giấy phép thì được) |
| Zalo AI, VinAI | không công bố trọng số TTS mở (Zalo TTS là API trả tiền) |
| Amazon Polly, OpenAI TTS | trả tiền; Nghiệp chốt S260 chỉ dùng TTS miễn phí local |

Chưa thử (ứng viên nếu cần): Kani-TTS-Vie (Apache-2.0, giọng Nam; cần PyTorch + NeMo, nặng hơn ngân sách 2 GB RAM,
model card chưa nêu đồng ý của người nói); OpenVoice v2 tone-colour converter (MIT, cần PyTorch) đặt trên một preset
miền Nam để đổi âm sắc mà giữ giọng vùng.
