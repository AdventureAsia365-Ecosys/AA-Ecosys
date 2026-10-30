---
name: aa-uat-video
description: Quay video UAT và video giới thiệu sản phẩm AA_Ecosys (Playwright + phụ đề + giọng đọc TTS miễn phí chạy local) — kịch bản có assert từng bước, kiểm khung hình và khớp tiếng, đóng gói zip mỗi video, upload Google Drive bằng rclone, index + báo cáo. Dùng khi Nghiệp nói UAT, quay video, video giới thiệu, giọng đọc / lồng tiếng, nhân bản giọng, hoặc AA-855. Screenshot và kiểm một trang sau khi sửa UI thuộc aa-ui-verify.
---

# aa-uat-video

Mục tiêu: **một kịch bản = một user story = một video = một regression test.** Video là bằng chứng cho người đọc
nghiệp vụ; kịch bản đồng thời là bài test chạy lại được.

Công cụ: `tools/uat/` ở repo gốc (mỗi file có header ghi cách gọi). Cài một lần: `bash tools/uat/setup.sh`.
Kế hoạch đầy đủ (danh mục kịch bản theo app, bảng giọng đã thử, nơi lưu, audit thiết kế tổng thể):
`docs/audits/2026-10-30-S260-uat-video-plan/README.md` (§2.1, §3, §4).

## 1. Khi nào quay

- Quyết định S260: từ S261 kịch bản chạy như **dry run nội bộ** và regression; video giữ nội bộ.
- **Vòng chính thức** (Drive `UAT (kiểm thử nghiệm thu)/<round>/` + trang cho chủ doanh nghiệp) chỉ quay khi đủ tiêu
  chí vào vòng trong kế hoạch §6 (UI ổn định sau AA-994, có lại đường LLM, quyền ghi UAT Dev cho E2E CIS admin đã merge).
- Vòng sau chỉ **quay lại tính năng mới hoặc đã đổi**; bản cũ giữ nguyên, tăng `v<n>`.
- Check theo từng issue vẫn là `aa-ship` (verify live) + `aa-ui-verify` (ảnh); không biến mỗi issue thành một UAT.

## 2. Trước khi quay

1. **Egress = VN.** `curl -s ipinfo.io/country` phải ra `VN`; khác thì DỪNG và nhờ Nghiệp tắt VPN (Vercel chặn IP
   VPN/datacenter). `run.sh` tự kiểm và thoát mã 3. Triệu chứng + nguyên nhân: `aa-lessons` mục Vận hành (dòng
   Vercel 403 Code 21).
2. **RAM:** một Chromium và một model TTS trong RAM tại một thời điểm (`tts.py` giải phóng Kokoro rồi mới nạp VieNeu).
3. **Dữ liệu:** chỉ dữ liệu tổng hợp trên Dev (tenant, đại lý, khách, staff E2E). Mọi form thật để nguyên chưa gửi,
   mọi tin nhắn thật để nguyên chưa gửi; luồng cần gửi chạy trên đối tượng E2E. Không gọi LLM trả tiền khi quay.
4. **Che bí mật:** `scenario.mask = [selector]` làm mờ API key, webhook secret… trước khi quay.
5. **Đăng nhập không lên hình:** đăng nhập một lần trong context không quay, lưu `storageState`, truyền qua
   `UAT_STORAGE_STATE`. Danh tính và cách đăng nhập E2E: `aa-ui-verify` §3 (bảng) + §3a — dùng đúng bảng đó.
   Luồng cần UI bên thứ ba thật (Meta, hộp thư) → Nghiệp quay bằng Claude trên trình duyệt desktop.

## 3. Viết kịch bản

File `tools/uat/scenarios/<app>/<id>.cjs` (mẫu: `tripplanner/tp-pub-01.cjs`, `partner-portal/portal-pub-01.cjs`):
`id`, `title`, `baseURL` (ghi đè bằng `UAT_BASE_URL`), `viewport` (1440 × 900; 390 × 844 cho trang dùng trên điện
thoại), header Given/When/Then, danh sách `steps`.

- Mỗi step có `caption: { en, vi }` (vừa là phụ đề vừa là lời đọc) và `run()` **làm hành động và assert** kết quả
  (heading, URL, số dòng, badge trạng thái).
- Assert sai → step FAIL, dừng chạy, **video vẫn giữ** làm bằng chứng lỗi; phụ đề step đó có `[FAIL]`.
- **Fast mode** cho CI / regression: `node tools/uat/record.cjs <scenario> --fast` (không video, không giữ nhịp,
  chỉ `result.json`).
- Id theo danh mục kế hoạch §4 (`TP-03`, `BK-04`, `CRM-06`…); kịch bản mới thêm vào danh mục đó.

## 4. Giọng đọc

- **Tiếng Anh:** Kokoro `af_heart` (nữ) — Nghiệp đã duyệt.
- **Tiếng Việt:** VieNeu-TTS v3 Turbo, giọng miền Nam **"Thục Đoan"** (đã chọn). Đổi bằng `UAT_VI_VOICE`
  (vd. `Adam` = nam miền Nam, hoặc file giọng clone `own-voice/work/voice_w<k>.npz`).
- **Giọng của chính người đọc:** chỉ khi người đó đồng ý (ghi rõ trong báo cáo phiên), mẫu ≤ 8 s; hướng dẫn thu và
  script: `tools/uat/own-voice/README.vi.md` + `clone.py`.
- **Chỉ TTS miễn phí chạy local.** Giọng chưa đủ hay → thử model mã nguồn mở khác. Piper `vi_VN-vais1000` (giọng Bắc)
  đã bị loại. Dịch vụ TTS trả tiền nằm ngoài phạm vi (luật dịch vụ trả tiền: `aa-lessons/lessons.md` mục Cách làm việc).
- **Luật giấy phép:** code, trọng số và giọng preset đều phải cho phép dùng thương mại. Danh sách đã loại (NC / CPML /
  không rõ) và cách kiểm một model mới: `references/voices-licences.md` — đọc trước khi thêm giọng.

## 5. Chạy, build và kiểm

```bash
bash tools/uat/run.sh scenarios/<app>/<id>.cjs
# captions -> tts.py (EN + VI, durations.json) -> record (mỗi step giữ >= độ dài lời đọc) -> build.py -> check_sync.py
# exit 0 PASS | 2 có step FAIL (video vẫn giữ) | 3 egress không phải VN
```

`build.py`: ffmpeg H.264, phụ đề tiếng Anh burn vào hình, hai track audio EN (mặc định) + VI, sidecar
`.en/.vi.srt` + `.vtt`, `.result.json`. Video giới thiệu TripPlanner: `bash tools/uat/intro/run_intro.sh en|vi`
(một MP4 mỗi ngôn ngữ, kịch bản cảnh ở `intro/narration.json`).

Kiểm xong khi cả ba đạt:

1. **Khung hình:** mở từng ảnh `work/<id>/frames/*.png` (một ảnh mỗi 20 s) — thấy con trỏ, phụ đề đọc được, không có
   trang Security Checkpoint / trang lỗi.
2. **Khớp tiếng:** `check_sync.py` báo có tiếng ở mọi điểm bắt đầu cue, cho cả hai track. `run.sh` kiểm track EN;
   track VI chạy thêm: `tools/uat/venv/bin/python -I tools/uat/check_sync.py <mp4> <stem>.vi.srt --track 1`.
3. **Kết quả:** `result.json` có PASS/FAIL từng step; báo cáo ghi đúng step FAIL + mốc thời gian.

Agent không tự nghe được: độ tự nhiên của giọng là Nghiệp quyết.

## 6. Đóng gói

```bash
python3 -I tools/uat/package.py uat <ID>_<yyyymmdd>_v<n> "<tiêu đề>"
python3 -I tools/uat/package.py intro TripPlanner-intro <yyyymmdd> "<tiêu đề>"
```

Một zip mỗi video trong `out/packages/`: MP4 mỗi ngôn ngữ, MP3 lời đọc, SRT/VTT, kịch bản lời đọc, README VI + EN.
Zip là bản gửi đi được nguyên trạng: không id nội bộ (AA-xxx), không log chạy, không `result.json`.
Tên: `<ID>_<yyyymmdd>_v<n>` (vd. `TP-PUB-01_20261030_v2`); quay lại sau khi sửa → tăng `v<n>`.

## 7. Upload Google Drive

Connector Drive chỉ mang được text; video đi bằng **rclone**, remote `aadrive:` (gốc = thư mục AdventureAsia, Nghiệp
đã cấp quyền). Chọn thư mục theo **tên**, theo loại video:

```bash
rclone copy <thư mục local> "aadrive:01 Video/Giới thiệu sản phẩm/<tên video>"
rclone copy <thư mục local> "aadrive:01 Video/UAT (kiểm thử nghiệm thu)/<round>/<app>"
rclone check <thư mục local> "<remote vừa copy>" --one-way     # phải ra 0 differences
```

Upload xong khi `rclone check` báo 0 differences. Di chuyển trên Drive bằng `rclone moveto` (link giữ nguyên).
Nghiệp tự mở quyền chia sẻ. rclone đang dùng client_id chung sắp bị khai tử trong 2026: khi rclone cảnh báo/ngừng,
tạo OAuth client riêng (Google Cloud project miễn phí) rồi `rclone config update aadrive client_id=… client_secret=…`
— giá trị không ghi vào repo hay skill.

## 8. Index và báo cáo

- Index mỗi app: `docs/audits/<date>-S<nnn>-uat/<app>.md` trong root PR — kịch bản, story, verdict, độ dài, step FAIL +
  mốc thời gian, link Drive, commit SHA của app lúc quay.
- Một trang artifact cho chủ doanh nghiệp (một tab mỗi app), lưu local theo `aa-session` (save audits locally); link
  đưa vào draft Jira cuối phiên, lời văn theo `aa-jira-update`.
- Lỗi tìm thấy → issue có sẵn hoặc issue mới (hỏi trước, `aa-linear-issue`).

## Bảo trì

- Script mới cho `tools/uat/`: header ngắn (làm gì, cách gọi, chi phí), đường dẫn tương đối theo thư mục script,
  không secret, không đường dẫn `/home/...`. `venv/`, `models/`, `work/`, `out/` đã gitignore.
- Đổi giọng, đổi luật giấy phép → sửa §4 + `references/voices-licences.md` cùng lúc.
