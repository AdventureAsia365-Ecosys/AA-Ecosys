---
id: OPS-08-s261-crm-progress-video-plan
title: "CRM (AA-Partner): tiến độ code và kế hoạch video review toàn app (S261)"
description: "Báo cáo cho tech lead: CRM đã code được bao nhiêu phần trăm (theo số thẻ, theo khối lượng, theo module), quay video review toàn app được chưa, kế hoạch 21 đoạn ngắn ghép thành một video dài, cách quay và ghép ($0), rủi ro và các quyết định cần duyệt trước khi làm."
type: report
status: active
owner: nghiep
audience: [engineer]
applies_to: [aa-partner]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-855, AA-1009]
---

# CRM (AA-Partner): tiến độ code và kế hoạch video review toàn app (S261, 31/10/2026)

Đây mới là **plan để anh duyệt**, chưa quay gì. Số liệu đo bằng cách chỉ đọc repo, Linear và GitHub; chưa ghi gì lên
Linear, GitHub hay AWS. Trang trình bày cùng nội dung: [`page.html`](page.html).

## 1. Trả lời ngắn

**CRM đã code được bao nhiêu.** Khoảng **70 %**, đo theo ba cách cho ra gần như cùng một số:

| Cách đo | Kết quả | Ghi chú |
|---|---|---|
| Theo số thẻ thiết kế (53 thẻ CRM-01a…CRM-38, CRM-B*, CRM-P*) | **69,8 %** (37/53 thẻ đã có code trên `main`) | 32 thẻ Done trên Linear (60,4 %) + 5 thẻ đã merge nhưng chưa đóng. PR #146 merge thì lên 38/53 = 71,7 % |
| Theo khối lượng (S = 0,25, M = 0,5, L = 1 phiên, thang design v3 §6.4; tổng 37,25 phiên) | **71,3 %** tính cả PR #146; 69 % nếu chỉ tính `main` | Cộng thêm W8 Go-real (≈ 2,5 phiên) thì còn ≈ 67 % |
| Trung bình 23 module (F1–F5, M1–M18) | **≈ 70 %** | Nếu tính đều 29 module/thẻ, kể cả Hardening và Go-real đang 0 %, thì ≈ 61 % (cách đếm bi quan nhất) |

- **Phần còn lại:** khoảng 10,7 phiên danh nghĩa; cộng ~15 % cho review và chờ MFA thì ≈ **12 phiên**. W8 Go-real
  thêm 2–3 phiên và phải chờ thủ tục bên ngoài (Stripe live, xác minh vendor, DPA).
- **5 module chưa có code:** M8 ops release, M9 WhatsApp/SMS, M10 workflow + task, M13 commission + huỷ chuyến,
  M14 AI (chỉ có stub, và đang bị chặn vì đường LLM acc3 lỗi Error 002). Ngoài 23 module còn 0 %: Search + library,
  Campaigns, Hardening (security review, SLO, load test, release train), Go-real.

**Quay video review toàn app được chưa.** **Được**, cho khoảng 2/3 app đang chạy live trên Dev với dữ liệu tổng hợp.
Phần chưa có thì cho xem đúng màn trống thật của app (5 mục nav "Coming later") kèm slide "Not ready yet", không dựng
giả màn hình nào. Nếu quay toàn app một lèo thì khoảng 30 % thời lượng là màn trống, nên đề xuất quay **theo luồng
một ngày làm việc của đại lý**.

**Đề xuất.**
1. Quay **21 đoạn ngắn** (R00…R20, 25–120 s mỗi đoạn), ghép thành **một video dài ≈ 25–26 phút** có chương, cắt thêm
   bản highlight ≈ 10 phút từ chính các đoạn đó (không quay lại).
2. Hai bản: `_EN.mp4` (giọng EN, phụ đề EN in cứng, có thêm track VI) và `_VI.mp4` (giọng nữ miền Nam, phụ đề VI in cứng).
3. Quay **sau khi PR #146 (AA-962, crm-030) merge và deploy xong**, vì deploy Partner đang treo ở chỗ trống crm-030.
4. Đây là **bản review nội bộ (dry run)**, chưa phải vòng UAT chính thức (theo quyết định S260), để ở thư mục dry-run
   trên Drive. Chi phí **$0**. Công: ≈ 5–6 giờ, chia 2 phiên.

**RAM.** Đủ. Máy 9,9 GB, đang dùng 4,4 GB, swap đã dùng 2,1 GB vì các lane khác. Lúc nặng nhất quy trình cần ≈ 2 GB
(TTS tiếng Việt), quay ≈ 1 GB, ffmpeg ≈ 0,5 GB, chạy lần lượt. Chỉ cần không quay cùng lúc với `pytest` hay
`next build` của lane khác.

## 2. Tiến độ theo module

Thẻ Done tính 100 %. Thẻ đang dở chấm theo phần đã có trên `main`. Thẻ Backlog tính 0 %, kể cả khi đã có vài khung sẵn.

| Module | % | Trạng thái | Còn thiếu |
|---|---|---|---|
| F1 identity vault | 69 | Đang dở | Hỗ trợ L2 + break-glass L3 (AA-971) |
| F2 hồ sơ ẩn danh | 100 | Xong | — |
| F3 lọc PII | 80 | Đang dở | Scrubber + bộ mẫu xong; chưa có AI gateway dùng tới (LLM bị chặn) |
| F4 tenancy và vai trò | 78 | Đang dở | Truy cập hỗ trợ L2/L3 |
| F5 audit | 85 | Đang dở | Audit cho L2/L3 và ops release |
| M1 intake | 100 | Xong | Import CSV nằm trong PR #146 |
| M2 pipeline | 100 | Xong | Trang Tasks tổng thuộc M10 |
| M3 đề xuất tương tác | 83 | Đang dở | Bản đồ trong builder (AA-948, cần T13 + Mapbox) |
| M4 đề xuất dạng chữ | 100 | Xong | — |
| M5 email | 90 | Xong, còn phần tách | Microsoft 365 send-as (AA-1011) |
| M6 sổ booking | 100 | Xong | — |
| M7 hoá đơn và thanh toán | 90 | Đã merge, chưa đóng | Stripe Connect (test), webhook, link trả thẻ; hiện chỉ có provider `manual` |
| M8 AA ops release | 0 | Backlog | Toàn bộ (phía Booking đã có) |
| M9 WhatsApp/SMS | 0 | Backlog | Toàn bộ (Twilio của đại lý) |
| M10 workflow + task | 0 | Backlog | Toàn bộ; trang Tasks/Automations là màn trống |
| M11 portal khách | 76 | Đã merge, chưa đóng | Offline PWA (AA-954) |
| M12 hợp đồng/waiver | 95 | Xong, còn phần tách | PDF ký PAdES-B-B (AA-1012) |
| M13 commission + huỷ chuyến | 0 | Backlog | Toàn bộ; trang Commissions trống |
| M14 AI | 5 | Bị chặn | Gateway, nháp, giọng; chặn bởi đường LLM (acc3 Error 002) |
| M15 nhà cung cấp | 100 | Xong | — |
| M16 báo cáo đại lý | 90 | Đã merge, chưa đóng | Ô của M8/M13/M14 còn "Coming later"; chưa có rollup `metric_daily` |
| M17 AA insights | 70 | Đã merge, chưa đóng | Trang CIS S-03 và bảng `insight_aggregate` |
| M18 xuất/xoá dữ liệu | 90 | Đã merge, chưa đóng | Re-import, xoá hoãn (khách đang đi), yêu cầu do AA chuyển tới |

**Thẻ ngoài 23 module:**

| Thẻ | % | Ghi chú |
|---|---|---|
| Onboarding + import (AA-962) | 80 | PR #146 đang chờ merge: migration preflight và coverage ≥ 90 % |
| Duty of care + lịch (AA-961) | 95 | Chỉ còn live check banner sự cố; lịch OAuth tách sang AA-1011 |
| Search + library (AA-963) | 0 | Toàn bộ |
| Campaigns (AA-968) | 0 | Toàn bộ |
| Hardening + release (AA-969, AA-970) | 0 | Security review, SLO, load test, release train, trang data. Trang Help có trong #146 |
| Go-real (AA-980) | 0 | Vị trí prod, Stripe live, xác minh vendor, DPA |

**Lệch dữ liệu cần chú ý** (sẽ sửa ở bước đồng bộ cuối phiên, không thuộc plan này):
- AA-967: Linear vẫn In Progress dù plan.json ghi Done-candidate (đã verify live S260).
- AA-945, AA-955: Linear đã Done, plan.json (30/10) còn ghi In Progress/Backlog.
- AA-953, AA-966: Linear In Progress, code đã merge hôm nay.
- Linear có 55 issue trong project vì có thêm AA-1011, AA-1012 (tách từ thẻ đã Done); hai issue này không vào mẫu số.
  Nếu tính mỗi issue là M thì % theo khối lượng giảm ≈ 1,8 điểm.

## 3. Kế hoạch video

Thứ tự xem theo **một ngày làm việc của đại lý**. Viewport 1440×900; đoạn của khách quay 390×844 rồi đặt giữa khung
1440×900. UI tiếng Anh (mặc định của sản phẩm). Danh tính:

- **A** = owner của đại lý tổng hợp "Lữ hành Sen Vàng" (đăng nhập ngoài khung quay, lưu `storageState`).
- **B** = assistant của Sen Vàng.
- **C** = khách tổng hợp tạo mới mỗi lượt, địa chỉ `@example.invalid`; mã OTP bị che.
- **D** = staff E2E của Booking, chỉ đọc.

| # | Đoạn | Danh tính | Dữ liệu (Dev, tổng hợp) | Độ dài | Sẵn sàng | Phần chưa có (slide "Not ready yet") |
|---|---|---|---|---|---|---|
| R00 | Mở đầu: CRM là gì, bản đồ module và % | – | – | 30 s | Sẵn | – |
| R01 | Đăng nhập xong, Home (KPI, checklist onboarding, chuông) | A | – | 50 s | Sẵn | – |
| R02 | Onboarding + import CSV (preview, chạy, gộp trùng, Connections) | A | CSV ≈ 10 dòng sinh local, 1 cặp trùng | 100 s | **Chờ #146** | Cả đoạn là slide nếu #146 chưa deploy |
| R03 | Inquiry: khách gửi form công khai, card mới ở cột Inquiry | C → A | Prospect mới, hậu tố `rv<ngày>` | 75 s | Sẵn | – |
| R04 | Pipeline: theo một chuyến qua các stage | A | Chuyến của R03 | 75 s | Một phần | Trang Tasks tổng (M10) |
| R05 | Client 360: hồ sơ ẩn danh, reveal có ghi log | A | Client của R03 | 60 s | Sẵn | – |
| R06 | Builder day-by-day + tour AA (departure thật, giá live) | A | Departure còn ≥ 2 chỗ (prep chọn) | 110 s | Một phần | Bản đồ trong builder (M3) |
| R07 | Đề xuất dạng chữ + "Before you go" | A | Chuyến phụ do prep tạo | 45 s | Sẵn | – |
| R08 | Khách chấp nhận trên điện thoại (hold, terms, accept) | C | Link của R06 (token bị che) | 75 s | Sẵn | – |
| R09 | Hợp đồng và e-sign: terms mới → ký lại, waiver | A ↔ C | Version `rv-<ngày>` | 105 s | Một phần | PDF ký PAdES-B-B |
| R10 | Hoá đơn + thanh toán: claim, xác nhận, Booked, nhắc nợ | A ↔ C (+D) | Hoá đơn quá hạn tạo ≥ 1 giờ trước | 120 s | Một phần | Trả thẻ / Stripe Connect |
| R11 | Portal theo từng người: chuyến bay, scan hộ chiếu SPECIMEN, mời bạn đi | C | Chuyến Booked của R10, 2 người | 100 s | Một phần | Offline PWA |
| R12 | Duty of care + lịch: ai đang đi đâu, ICS feed | A | Chuyến 12–15/11 | 75 s | Một phần | Banner sự cố AA (Q3), đồng bộ lịch OAuth |
| R13 | Email: thread, saved reply, lưu nháp (không bấm Send) | A | Thread mail probe | 75 s | Một phần | Microsoft 365 send-as |
| R14 | Nhà cung cấp + sổ booking | A | Có sẵn | 45 s | Sẵn | – |
| R15 | Báo cáo: funnel, tiền, công nợ, team, xuất CSV | A | Có sẵn | 60 s | Một phần | Ô M8/M13/M14, trang AA insights trong CIS |
| R16 | Xuất / xoá dữ liệu client (dry run → 409 an toàn) | A | Client mới, chưa có chuyến | 75 s | Một phần | Xoá theo yêu cầu do AA chuyển tới |
| R17 | Settings: team, agreements, forms, mailbox, payments, EN↔VI, dark mode | A | – | 70 s | Sẵn | – |
| R18 | Góc nhìn assistant: mục bị chặn theo vai trò | B | – | 35 s | Sẵn | – |
| R19 | Phần chưa có: 6 màn trống + slide các module chưa làm | A | – | 75 s | Chưa có (cả đoạn) | Tasks, Automations, Commissions, Marketing, Library, Help; M8, M9, M14, L2/L3, Hardening, Go-real |
| R20 | Kết: bảng % và việc tiếp theo | – | – | 25 s | Sẵn | – |

- **Tổng:** ≈ 24,7 phút nội dung + 21 thẻ chương × 2,5 s ≈ **25–26 phút**.
- **Bản highlight ≈ 10 phút:** R01, R03, R04, R06, R08, R10, R11, R15, cắt từ cùng bộ đoạn.
- **Slide "Not ready yet":** HTML theo kit, tiếng Anh, có lời đọc; không ghi mã AA-xxx; chỉ nói phần còn thiếu,
  không hứa ngày xong.
- **Prep và cleanup** (không quay, chạy `--fast`): prep kiểm `/crm/health` + ghi `git_sha`, chọn departure, tạo chuyến
  phụ, tạo hoá đơn quá hạn, sinh CSV, lưu id vào `state.json`; cleanup chuyển chuyến dở sang Lost và nhả hold, xoá
  saved reply/draft, revoke ICS; chạy lại không tạo trùng.

## 4. Cách quay và ghép

Theo skill `aa-uat-video`, thêm một bước ghép bản dài.

| Bước | Việc | Công cụ |
|---|---|---|
| 1 | Kịch bản `tools/uat/scenarios/crm/crm-rev-00…20.cjs`: mỗi bước có caption EN/VI, vừa thao tác vừa assert; `mask` che OTP, token link, URL ICS, link export | Playwright |
| 2 | Đăng nhập ngoài khung quay: đọc secret lúc chạy, `storageState` riêng cho A và B (chmod 600), không in ra | `tools/uat/lib/crm-signin.cjs` |
| 3 | TTS, mỗi lúc một model: EN Kokoro `af_heart`, VI VieNeu v3 Turbo giọng nữ miền Nam; ra `durations.json` | Local, miễn phí |
| 4 | Quay: `recordVideo`, slowMo 60, lớp phủ con trỏ; mỗi đoạn một Chromium; kiểm `git_sha` đầu và cuối đoạn | Playwright |
| 5 | Build từng đoạn: H.264 CRF 26, 25 fps, 2 track audio EN + VI, sidecar `.srt/.vtt` | `build.py` |
| 6 | Normalise: 1440×900 yuv420p 25 fps, đoạn 390 pad vào giữa rồi mới burn phụ đề; audio 48 kHz, loudnorm −16 LUFS; thẻ chương 2,5 s | `tools/uat/longform.py` (mới) |
| 7 | Ghép: concat `-c copy`, chương nhúng qua ffmetadata, `chapters.txt`, SRT/VTT gộp lệch mốc cho EN và VI | ffmpeg |
| 8 | Kiểm: ≈ 80 khung hình (1 ảnh / 20 s), `check_sync.py` cho 2 track, `result.json` PASS từng bước | Agent tự kiểm |
| 9 | Đóng gói: zip mỗi đoạn + gói `CRM-REVIEW_<yyyymmdd>_v1/` (MP4, SRT/VTT, chapters, README VI + EN); không mã AA-xxx, không log | `package.py` |
| 10 | Upload Drive: `rclone about`, `rclone copy` vào `01 Video/UAT (kiểm thử nghiệm thu)/dry-run/CRM-review-<yyyymmdd>/`, `rclone check --one-way` = 0 khác biệt | rclone |
| 11 | Index `docs/audits/<date>-S<nnn>-uat/crm.md` trong root PR: verdict từng đoạn, link Drive, SHA AA-Partner lúc quay | Root PR |

**Tài nguyên và thời gian:**

| Hạng mục | Ước tính |
|---|---|
| RAM đỉnh | ≈ 2 GB (TTS tiếng Việt); quay ≈ 1 GB; ffmpeg ≈ 0,5 GB; chạy lần lượt |
| Đĩa lúc đỉnh | ≈ 2 GB (đĩa còn 851 GB); dọn `work/` sau upload |
| Upload Drive | ≈ 0,9–1 GB |
| Phiên A: viết 21 kịch bản + prep/cleanup + `longform.py`, chạy thử `--fast` trên Dev | ≈ 2,5–3,5 giờ |
| Phiên B: TTS ≈ 35 phút, quay ≈ 40 phút (+20 nếu quay lại), build/ghép ≈ 30–40 phút, kiểm + đóng gói + upload ≈ 40 phút | ≈ 2,5 giờ |
| **Tổng** | **≈ 5–6 giờ, 2 phiên** |
| **Chi phí** | **$0**: không gọi LLM, TTS local, Drive trong dung lượng sẵn có, AWS chỉ đọc vài secret, ECS vốn đang chạy |

## 5. Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Deploy giữa lúc quay (#146 chưa merge; sau deploy portal mọi phiên phải đăng nhập lại) | Quay sau khi #146 merge + deploy xong; đóng băng merge AA-Partner trong lúc quay; mỗi đoạn ghi `git_sha` đầu/cuối, lệch thì quay lại đoạn đó |
| Dữ liệu trôi (số báo cáo, ghế departure, giá Booking) | Prep chọn departure lúc chạy; hậu tố tên mỗi lượt; báo cáo chỉ assert cấu trúc; id lấy từ `state.json` |
| Ràng buộc thời gian (OTP 10 phút, hold có hạn, job nhắc nợ mỗi giờ, chuyến 12–15/11 phải trong cửa sổ 14 ngày) | Quay R08 → R11 liền nhau; prep ≥ 1 giờ trước; quay trước ≈ 10/11, nếu không thì tạo chuyến mới trong cửa sổ |
| Host khách giới hạn 5 lần ghi / phút / địa chỉ | Nhịp lời đọc giãn ≥ 14 s giữa các lần ghi; assert không gặp 429 |
| Banner sự cố AA: E2E Booking bị 403 `e2e_read_only` | Quyết định Q3 ở mục 6 |
| Ghế departure: mỗi lượt chốt 1 ghế, chưa có huỷ chuyến để nhả | 1 người lớn; chọn departure nhiều ghế nhất; chấp nhận vì là Dev tổng hợp |
| Erasure: Dev bật `LIFECYCLE_DRY_RUN=true` | Quay đúng phản hồi 409 và giải thích; không đổi task definition để quay |
| AI của CRM mới là stub (LLM acc3 lỗi) | Không bấm nút AI; nói rõ bằng slide ở R19 |
| Lộ bí mật trên hình (OTP, token, URL ICS, link export) | `mask` + kiểm từng khung hình trước khi đóng gói |
| Mail thật đi ra ngoài | Không bấm Send; form mời member chỉ mở; mời portal chỉ tới `@example.invalid`, tối đa 2 lời mời mỗi lượt. **Sửa sau phiên A (31/10):** gửi proposal, mời portal, mã đăng nhập portal… vẫn xếp mail qua hộp Gmail đang nối với đại lý tổng hợp, khoảng 6–8 mail mỗi lượt tới `@example.invalid` (không tới ai, bị trả về hộp đó). Cách chặn: AA-Partner không bao giờ gửi tới đuôi `.invalid` (lane l12, AA-1014) |
| Tranh RAM với lane khác (swap 2,1 GB) | Không quay song song pytest/build; mỗi lúc một Chromium và một model TTS |
| rclone dùng client_id chung bị chặn | Tạo OAuth client riêng (miễn phí) theo skill §7 |
| Agent không tự nghe được giọng | Anh nghe R01 + R03 (≈ 3 phút) trước khi build cả bộ |

## 6. Cần anh duyệt

Mỗi mục có sẵn đề xuất; anh chỉ cần đồng ý hoặc chọn phương án khác.

| # | Quyết định | Đề xuất | Phương án khác |
|---|---|---|---|
| Q1 | Ngôn ngữ | UI tiếng Anh; 2 bản dài `_EN.mp4` (giọng + phụ đề EN, có track VI) và `_VI.mp4` (giọng nữ miền Nam, phụ đề VI in cứng). Lý do: trình phát Drive chỉ phát track mặc định, không tự hiện phụ đề mềm | Chỉ 1 bản EN có 2 track (tiết kiệm ≈ 15–20 phút encode) |
| Q2 | Độ dài | Bản đầy đủ ≈ 25–26 phút có chương + bản highlight ≈ 10 phút | Chỉ bản highlight; hoặc chỉ các đoạn rời |
| Q3 | Banner sự cố AA (R12) | Slide "chưa quay được" + ảnh baseline | Anh tự bấm "Flag incident" bằng tài khoản staff Booking trong cửa sổ ngắn để agent quay; hoặc seed bằng DB Migrate run-script (nặng hơn, cần review) |
| Q4 | Thời điểm quay | Sau khi PR #146 merge + deploy xong; phiên A (tooling) làm ngay, phiên B (quay) ngay sau deploy, trước ≈ 10/11 | Quay ngay bây giờ, R02 thành slide |
| Q5 | Ghế departure | Chấp nhận mỗi lượt chốt 1 ghế trên Dev (1 người lớn, departure nhiều ghế nhất) | Bỏ tour AA khỏi R06 |
| Q6 | Đoạn erasure (R16) | Quay đúng 409 `deletion_dry_run` và giải thích là công tắc an toàn của Dev | Bỏ phần Erase, chỉ quay export |
| Q7 | Có quay phần chưa xong không | Có, nhưng ngắn: màn trống thật ≈ 5 s mỗi trang + slide "Not ready yet" gom ở R19, cộng slide nhỏ trong từng đoạn; không dựng giả màn hình | Bỏ hẳn phần chưa xong, chỉ quay phần đã chạy |
| Q8 | Nơi lưu và quyền | Drive thư mục dry-run nội bộ; anh tự mở quyền chia sẻ | – |

**Lúc quay anh cần:** tắt VPN (`run.sh` dừng nếu egress không phải VN); nhập mã MFA nếu phiên `aa365-admin` 8 giờ hết
hạn. Không cần cấp quyền ghi mới nào.

**Nguồn đã đọc:** skill `skill/aa-uat-video/SKILL.md`; kế hoạch S260 `docs/audits/2026-10-30-S260-uat-video-plan/`;
bằng chứng S261 `docs/audits/2026-10-31-S261-evidence/` (AA-945, AA-955, AA-961, AA-967); bộ quay `tools/uat/record.cjs`;
nav CRM `apps/AA-Partner/web/lib/nav.ts`; mô tả PR AA-Partner #143–#146; Linear project "Partner CRM — AA-Partner";
`linear-issue-map.json` và design v3 §6.3–6.4.

## Artifact

- `page.html`: <https://claude.ai/artifact/Rgw1AnJotY3iLtyqnUcw97> (private, claude.ai account nghieppham@adventure.asia since S261)
