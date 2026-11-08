# S273 — Nháp Jira (CHƯA ĐĂNG, chờ tech lead duyệt một lần)

**Trạng thái 09/11 ~06:20 +07:** chưa đăng. Không gọi công cụ ghi Jira nào (không comment, không đổi trạng thái).

Bộ này gộp 4 nháp S272 chuyển sang (`docs/audits/2026-11-07-S272-close/jira-drafts.md`, đã gộp sẵn nháp S271) với
việc đã ship ở S273. Số liệu cập nhật theo snapshot S273 và bức tranh hệ thống (đo 09/11 00:45 +07).

Luật đã áp dụng (skill `aa-jira-update`, memory `jira-draft-tone`, `jira-report-when-done`,
`jira-claims-need-live-evidence`, `jira-no-tech-decisions`, `batch-drafts-at-session-end`, `platform-report-weekly`,
`tenant-sees-content-only`):

- chỉ báo việc đã ship và đã kiểm live; phần chưa thử thì ghi rõ "chưa thử thật vì …";
- tiếng Việt, đứng tên tech lead, không mã nội bộ (AA-xxx, số PR, tên bảng), không câu hỏi cho chị Thư, không "ạ",
  không "như đã hứa";
- không báo quyết định kỹ thuật/hạ tầng (PR-27 không soạn; việc chuyển TripPlanner khỏi Vercel, vệ sinh CI, tài khoản
  AWS, thiết kế dữ liệu SEO mới không đưa vào như một quyết định);
- kết quả viết cho đại lý báo "đại lý nhận đủ X/X", phần dưới ngưỡng chỉ là tín hiệu trong Writing Lab;
- khi đăng: `contentFormat: html`, mention `<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`,
  bảng markdown đổi sang bảng HTML, ảnh đính theo quy trình upload trong skill.

## Rà Jira (09/11 ~06:10 +07)

JQL `project in (PR, KAN, CON) AND statusCategory != Done ORDER BY updated DESC`: lần cập nhật mới nhất là đợt đăng
06/11 06:24–06:25 (PR-22, PR-25, PR-26, PR-17, PR-18, PR-23). Không có comment mới của chị Thư sau đó. Đã đọc comment
gần nhất của PR-20, PR-22, PR-23, PR-24, PR-25, PR-26, PR-17, KAN-90 để không lặp nội dung.

- PR-20: kỳ 3 (27/10–02/11) đăng dạng comment trên PR-20 ngày 02/11, kèm bảng mô hình B2B ngày 04/11. Kỳ 4 (03–09/11)
  đến hạn thứ Hai 09/11 → nháp #7, cũng dạng comment trên PR-20 như kỳ 3.
- Không soạn: PR-27 (kỹ thuật, tech lead quyết); PR-18 (không có gì mới ship); PR-11/13/15/19 (không đổi); PR-21, PR-28
  (kỳ cũ); KAN-* và CON-* khác (không thuộc việc phiên này). Tài liệu pháp lý (phụ lục bảo mật DPA v0.4) không soạn:
  phần còn lại là việc của luật sư/chủ doanh nghiệp, không đưa câu hỏi cho chị Thư.

## Ô tech lead chốt trước khi đăng

- [ ] #1 PR-22: đã thay bảng số nền S271 ("đạt ngay lần đầu" blog 10 % / catalogue 48 % / đại lý 64 %) bằng bảng
      trạng thái theo kênh đo 09/11 (một nguồn, một cách tính), và bỏ câu mục tiêu "blog đạt ngay lần đầu ≥ 30 %" vì
      mục tiêu đó tính theo chỉ số cũ. Muốn giữ chỉ số cũ thì cần đo lại theo cách S271.
- [ ] #1 PR-22: câu "17/814 tour đánh dấu để xem" là chế độ báo cáo (chưa chặn thật) — giữ hay bỏ.
- [ ] #1 PR-22: không đưa kết quả đợt chạy thử 14 bài blog ngày 08/11 (3 đạt ngưỡng / 11 dưới ngưỡng) vì đây là bộ bài
      dùng để đo, chọn trên tour khó, không so được với số chung. Muốn thêm thì thêm 1 dòng.
- [ ] #3 PR-23: ảnh nhãn trong file tải về (thuộc tính file Word) chưa chụp; bằng chứng là bài kiểm tự động trên Dev.
- [ ] #4 PR-24: ảnh khách gửi yêu cầu nằm ở `.tmp-session/` (gitignore, không vào repo); upload thẳng từ đường dẫn đó.
- [ ] #7 PR-20: chưa có số hoá đơn hạ tầng AWS theo tháng (kỳ 3 có ghi sẽ đưa báo cáo chính thức tháng 8–10 vào kỳ 4).
      Phiên này chưa đo. Hoặc tech lead lấy số từ admin Spend › AWS bill rồi điền vào bảng, hoặc giữ câu "đưa vào kỳ 5".
- [ ] #7 PR-20: trang "bức tranh toàn hệ thống" (`system-picture/system-picture.vi.md`) là báo cáo kỹ thuật (tên bảng,
      tên job), chưa publish. Nháp chỉ dùng vài số chung, KHÔNG gắn link. Nếu muốn gửi chị một trang tổng quan thì cần
      một bản rút gọn cho chủ doanh nghiệp rồi mới thêm link vào #7.
- [ ] #8 KAN-90: tuỳ chọn. Đăng thì nên bỏ hoặc giữ câu cuối (kế hoạch cập nhật theo đợt, chưa phải việc đã ship).

---

## 1. PR-22 — CIS: Nội dung & pipeline

**Vì sao:** việc chất lượng viết đã ship ở S271–S273 chưa báo trên Jira (nháp S272 chưa đăng); S273 thêm phiếu dữ kiện
cho bộ viết tour catalogue, bài không còn bị cắt, Writing Lab nhận nhãn chấm, chủ đề Blog tăng sau khi cập nhật dữ liệu
tìm kiếm. Comment gần nhất 06/11 nói về menu admin, không trùng.
**Vị trí:** comment trên epic PR-22.

> @thule Cập nhật chất lượng viết bài và dữ liệu nội dung ngày 06–09/11 (Dev):
>
> - **Rà soát toàn bộ cách hệ thống viết, chấm và kiểm bài** cho blog, bài mạng xã hội, tour catalogue và tour viết
>   cho đại lý. Kết luận: giữ phần viết đang tốt, sắp xếp lại phần kiểm và sửa bài để không còn sửa đi sửa lại.
> - **Một bộ quy tắc viết chung cho mọi bước viết:** được viết bối cảnh về địa danh, nhưng không bao giờ hứa hoạt động,
>   dịch vụ, giờ giấc hay cảnh quan mà tour không có; câu về độ phù hợp với trẻ em, độ an toàn, nhịp độ chỉ viết đúng
>   như nguồn. Bộ 150 ví dụ mẫu được hệ thống xử lý đúng 150/150 theo bộ quy tắc này.
> - **"Phiếu dữ kiện" trước khi viết** (lịch trình, bữa ăn, dịch vụ có trong nguồn), bài chỉ được dựa vào phiếu này.
>   Nay dùng cho cả ba bộ viết: tour catalogue, tour cho đại lý và bài viết. Chạy thử 08/11 trên 3 tour catalogue ở
>   3 nước khác nhau: cả 3 dùng phiếu và xuất bản bình thường, chi phí khoảng 0,07 USD mỗi tour. Chạy thử 07/11 trên
>   tour đại lý, blog và bài mạng xã hội: cả 4 bài dùng phiếu.
> - **Bài không còn bị cắt giữa chừng** vì hết giới hạn độ dài, và lần sửa thứ ba không còn tốn tiền. Lô viết blog ngày
>   08/11: 23 lượt gọi AI, 0 lượt bị cắt, không lượt nào phải gọi lại.
> - **Kiểm lần cuối mỗi khi một bài đi ra** (đăng, duyệt, sửa tay) và ghi lại kết quả. Lượt kiểm trên 814 tour
>   catalogue: 797 đạt, 17 tour được đánh dấu để xem (9 tour có cưỡi voi, 6 tour lệch ngày so với nguồn, 3 tour thiếu
>   một ngày so với thời lượng). Hiện mới ghi nhận, chưa chặn tour nào. Tour có cưỡi voi được giữ nguyên văn và đưa vào
>   hàng duyệt.
> - **Writing Lab nhận 450 nhãn chấm đầu tiên** (150 câu trong bài, mỗi câu chấm theo 3 góc); 84 câu các góc chấm chưa
>   thống nhất được đưa vào hàng chờ AA xem. Bộ nhãn này dùng để đo độ chính xác của bước kiểm trước khi siết hay nới.
> - **Chủ đề Blog gợi ý cho đại lý:** sau khi cập nhật dữ liệu nhu cầu tìm kiếm (thị trường Mỹ) cho các địa điểm trong
>   tour của một đại lý thử, số chủ đề đủ chuẩn Blog của đại lý này tăng từ 4 lên 31 (trên 176 chủ đề). Chi phí 0,55 USD
>   (dữ liệu tìm kiếm 0,51, AI 0,04).
> - **Bài viết cho đại lý thử theo kênh** (đo 09/11). Đại lý luôn nhận đủ bài; cột "dưới ngưỡng" chỉ hiện trong Writing
>   Lab để AA cải thiện:
>
> | Kênh | Đạt ngưỡng | Dưới ngưỡng |
> |---|---|---|
> | Blog | 93 | 113 (55 %) |
> | LinkedIn | 137 | 36 (21 %) |
> | Email | 2 | 2 |
> | Facebook, Instagram, TikTok, quảng cáo, landing page | 22 | 0 |
>
> - Bước tiếp: giảm số bài blog dưới ngưỡng. Lý do hàng đầu là câu kêu gọi hành động nêu dữ kiện mà tour không có
>   (63/151 bài).

**Ảnh:** không đính (các trang Writing Lab có thông tin nội bộ).

| Câu | Bằng chứng |
|---|---|
| Rà soát + kết luận giữ phần viết tốt | Audit S271 `docs/audits/2026-11-06-S271-writing-quality-audit/` (nháp S271/S272) |
| Bộ quy tắc chung; 150/150 ví dụ | Linear W1 Done 08/11: bộ 150 ví dụ policy v1 quyết đúng như chính sách (block 103 / warn 12 / pass 35), chạy trên main; lint chính sách 0 lỗi (chạy lại S273) |
| Phiếu dữ kiện S1: 3 tour, 3 nước, ~0,07 USD/tour | `aa1047-s1-trial/s1-trial-report.txt`; Linear W1 08/11: mọi tour có `fs_id`, lối ra auto_publish → done, 0 lỗi; 0,213 USD tổng, 0,071/tour từ sổ chi phí |
| Phiếu dữ kiện T2 + T9, 4 bài | Chạy thử trả phí 07/11 (S272): 4 phiếu mới, mọi bài có `fs_id` |
| 23 lượt, 0 bị cắt, 0 gọi lại | Linear (issue một chủ thử lại) 08/11 ~16:20 UTC: 23 request T9, mọi request `stop_reason=end_turn`, 1 dòng sổ/request |
| Lần sửa thứ ba không tốn tiền | Ship S271 (nháp S271/S272), không đo lại ở S273 |
| 814 / 797 / 17 (9 + 6 + 3) | `docs/audits/2026-11-07-S272-close/aa1047-final-contract-report.json` (chế độ báo cáo, chưa chặn) |
| 450 nhãn, 84 vào hàng chờ | Linear W2 08/11: import qua API staff, ghi lần 2 giữ nguyên 450; báo cáo CL-1 `aa1048-w2/cl1-report-aggregate.json` |
| Blog 4 → 31 / 176; 0,51 + 0,04 USD | Checklist S273 mục "Research tenant audit" + `dfs-cost-audit/design.vi.md` mục 1 "Bằng chứng ngày 08/11"; snapshot: DFS 0,508 + LLM 0,039 USD |
| Bảng theo kênh; 63/151 | `system-picture/system-picture.vi.md` mục 1 "T9 theo kênh" (đo 08/11 ~17:45 UTC, role chỉ đọc); 22 = Facebook 6 + 4 kênh × 4 |

---

## 2. PR-17 — Tenant viết lại tour đúng giọng thương hiệu

**Vì sao:** hai thay đổi đã ship ở S271 (cưỡi voi, điểm giọng văn chỉ tham khảo) chưa báo; S273 viết lại 14 tour cho đại
lý thử. Comment gần nhất 06/11 (chuỗi viết lại chạy lại trên 4 thương hiệu thử), không trùng.
**Vị trí:** comment trên story PR-17.

> @thule Cập nhật viết lại tour cho đại lý ngày 06–08/11 (Dev):
>
> - **Tour có hoạt động cưỡi voi:** hệ thống giữ nguyên nội dung gốc, chỉ thêm phần thương hiệu của đại lý, và đưa vào
>   hàng duyệt của AA. Đại lý vẫn nhận bài như bình thường.
> - **Bước chấm giọng văn giờ chỉ để tham khảo,** không còn quyết định số lần viết lại, nên bài ra nhanh hơn và ít tốn
>   hơn.
> - **08/11:** viết lại 14 tour cho một đại lý thử, đại lý nhận đủ 14/14. Chi phí viết khoảng 0,04 USD mỗi tour.

**Ảnh:** không.

| Câu | Bằng chứng |
|---|---|
| Cưỡi voi giữ nguyên + vào hàng duyệt | Ship S271 (nháp S271/S272); lượt kiểm 814 tour ghi 9 tour cưỡi voi |
| Chấm giọng văn chỉ tham khảo | Ship S271 (nháp S271/S272), không đo lại ở S273 |
| 14/14, ~0,04 USD/tour | `.tmp-session/S273/l18-w2/out/report_latest.txt`: t2 good 14, failed 0, status ai_generated 14; t2_generate 0,5615 + t2_flag_fix 0,0092 + nudge 0,0005 = 0,571 USD / 14 ≈ 0,041 |

---

## 3. PR-23 — Portal tenant / app cho đại lý (nhãn AI trên mọi app)

**Vì sao:** nhãn AI đã kiểm live trọn vòng ngày 08/11, gồm lần đăng WordPress thật (comment 06/11 ghi là chưa thử được vì
site thử hết hạn) và 18/19 màn hình có ảnh; phần tải về đã ship ở S272. Đây là comment chính về nhãn AI; PR-24 và PR-25
chỉ nhắc ngắn và trỏ về đây.
**Vị trí:** comment trên epic PR-23.

> @thule Nhãn "nội dung có AI hỗ trợ" trên các app, ngày 07–08/11 (Dev). Phần này đáp ứng yêu cầu ghi nhãn nội dung AI
> của châu Âu (hạn 02/12/2026).
>
> - **Tải bài về:** mọi bản tải về trong Content studio (bài blog dạng trang web, đoạn chèn, bản chữ, và file Word của
>   tour) đều mang nhãn máy đọc được cho biết nội dung do AI tạo. File Word của tour giờ được lưu đúng tên tour và phiên
>   bản, không còn tất cả cùng tên "tour.docx". Đã kiểm tự động trên Dev: tải bài blog, đoạn chèn, bản chữ và file Word,
>   nhãn và tên file đều đúng.
> - **Đăng lên WordPress:** ngày 08/11 em đăng một bài blog của đại lý thử lên một site WordPress thử, qua đúng nút
>   Publish của Content studio. Bài trên WordPress mang dấu AI máy đọc được trong mã trang (người đọc không thấy khác);
>   trong Content studio, bài hiện ở danh sách Published kèm nhãn "AI-assisted".
> - **Nhãn trên giao diện,** đã kiểm và chụp 18/19 màn hình trên Dev ngày 08/11:
>
> | App | Chỗ có nhãn |
> |---|---|
> | Content studio | My Content (dòng thông báo và nhãn từng bài), ngăn chi tiết bài, trang Publish, danh sách Published, tab Kho tour |
> | Booking (nhân viên AA) | phần nội dung lấy từ CIS trong ngăn khách sạn, chi tiết dịch vụ, form dịch vụ, bộ soạn đề xuất và bản xem trước đề xuất |
> | TripPlanner | nhãn trên trang tour, dòng thông báo dưới lịch trình, dòng thông báo ở lời dẫn chuyến đi |
> | CRM | khung bản nháp AI trên trang chuyến |
> | WordPress | bài đã đăng (dấu trong mã trang) |
>
> - **Chưa thử thật:** dòng thông báo dưới một bản nháp AI vừa viết trong CRM, vì gói của đại lý thử chưa bật trợ lý AI
>   (viết nháp cần gọi AI có trả phí). Phần này đã có trong hệ thống.
>
> Ảnh theo thứ tự: (1) danh sách Published trong Content studio, bài đã đăng lên WordPress có nhãn "AI-assisted";
> (2) bài đó trên site WordPress thử.

**Ảnh (theo thứ tự):**
1. `docs/audits/2026-11-08-S273-session/aa1040-live/shots/s04-studio-published-list.png` (đặt tên khi upload: `content-studio-published-nhan-ai.png`)
2. `docs/audits/2026-11-08-S273-session/aa1040-live/shots/w02-wordpress-post.png` (`bai-wordpress-thu.png`)

| Câu | Bằng chứng |
|---|---|
| Nhãn trên mọi bản tải về; tên file Word | Linear 07/11 (S272): BFF chuyển header X-AI + tên file, Deploy Web Dev smoke 69/69 gồm spec tải về (HTML, đoạn chèn, bản chữ, DOCX + tên file); CIS gửi header X-AI cho DOCX từ S272, smoke studio kiểm header (Linear 08/11). Chưa chụp ảnh thuộc tính file |
| Đăng WordPress thật, dấu trong mã trang | `aa1040-live/publish-result.json` (status published, 08/11 10:45 UTC); `aa1040-live/wp-mark-snippet.txt` (`<article data-ai-generated="true" …>`, meta ai-generated, bản lưu REST cũng có dấu); ảnh w01–w03 |
| Published list + nhãn | ảnh `s04`, `w03` |
| 18/19 màn hình, bảng theo app | `aa1040-live/surfaces.json` (18 captured: s01–s05, b01–b05, c01, t01–t04, w01–w03) |
| Chưa thử thông báo dưới nháp CRM | `surfaces.json` c02 `captured: false` ("CRM_DRAFT=1 not set, writing a draft calls a model"); Linear 08/11 |
| Hạn 02/12/2026 | Linear 06/11 (S271): trang Commission "Quick facts" + EUR-Lex index Regulation (EU) 2026/1744 |

---

## 4. PR-24 — TripPlanner

**Vì sao:** S273 thử trọn vòng yêu cầu của khách từ TripPlanner của một đại lý vào đúng CRM của đại lý đó (đúng hướng
"TripPlanner cho đại lý" trong comment PR-20 ngày 04/11); địa chỉ Dev đổi (link aa-tripplanner.vercel.app trong comment
02/11 nay trả 404, chị cần link mới); thêm thông báo AI ở lời dẫn. Comment gần nhất 04/11, không trùng.
**Vị trí:** comment trên epic PR-24.

> @thule Cập nhật TripPlanner ngày 08/11 (Dev):
>
> - **Địa chỉ Dev mới:** <https://tripplanner.lumiguides.it.com>, chạy trên máy chủ của AA. Link cũ
>   aa-tripplanner.vercel.app không còn dùng; điều khoản ở <https://tripplanner.lumiguides.it.com/terms>.
> - **TripPlanner cho đại lý: yêu cầu của khách vào CRM của đại lý.** Khi đại lý có cả gói CRM và gói TripPlanner, yêu
>   cầu khách gửi từ trang TripPlanner của đại lý tự đi vào CRM của đại lý đó. Đã thử trọn vòng 08/11 với một đại lý
>   thử: một khách giả lập lên lịch trình trên trang TripPlanner của đại lý và bấm gửi; trang báo "Sent to Terra Family
>   Expeditions (Audit). They will contact you about this trip."; trong vòng 2 phút yêu cầu vào đúng CRM của đại lý
>   này, không vào CRM của đại lý nào khác (kiểm bằng nhật ký hệ thống).
> - **Còn làm tiếp:** trang TripPlanner của đại lý chưa mang thương hiệu riêng của đại lý (hiện vẫn là giao diện
>   Adventure Asia, như trong ảnh); chưa mở xem yêu cầu này trên giao diện CRM.
> - **Nhãn AI:** phần lời dẫn chuyến đi có thêm dòng thông báo AI. Chi tiết nhãn AI trên các app ở comment cùng ngày
>   trên PR-23.
>
> Ảnh: trang TripPlanner của đại lý thử sau khi khách bấm gửi, có dòng "Sent to Terra Family Expeditions (Audit)".

**Ảnh:** `.tmp-session/S273/l2-r5/shots/lead-sent-audit-terra-family.png` (`tripplanner-dai-ly-gui-yeu-cau.png`;
file nằm trong thư mục gitignore, upload thẳng từ đó). Khách là tên bịa, không hiện trên ảnh.

| Câu | Bằng chứng |
|---|---|
| Địa chỉ mới chạy, link cũ hết dùng | curl 08/11 23:17 UTC: `tripplanner.lumiguides.it.com/api/health` 200, `/terms` 200, `aa-tripplanner.vercel.app/` 404; Linear (lát hosting) 08/11: CNAME → CloudFront, project Vercel đã xoá |
| Tự vào CRM khi có cả hai gói | `.tmp-session/S273/l2-r5/README.md` bước 2 (kênh lead = crm khi tenant có `tp.hosted` + `crm.core`); Linear 08/11: thêm add-on TripPlanner cho tenant audit-terra-family (đã có CRM core), provision job thành công |
| Gửi thành công, câu báo trên trang | Playwright `send status=200`, 13:32:18 UTC; ảnh `lead-sent-audit-terra-family.png` |
| Đúng CRM đại lý A, không vào đại lý khác, trong 2 phút | Linear 08/11: aggregate check CloudWatch lần 2 `audit_tenant_stored=1 other_tenants_with_leads=0`, `rejected_or_foreign_lines=0`, PASS |
| Chưa có thương hiệu riêng; chưa xem trên CRM UI | Ảnh (header Adventure Asia); Linear 08/11 "Still open: two synthetic tenants shown with their own brand"; không có ảnh hộp yêu cầu CRM |
| Thông báo AI ở lời dẫn | `aa1040-live/surfaces.json` t04 captured; ảnh `t04-tp-narration-notice.png` |

---

## 5. PR-25 — Booking

**Vì sao:** việc gỡ phần khách lẻ được deploy 06/11 sau đợt đăng 06/11 06:25 nên chưa báo; nhãn AI trong Booking đã kiểm
trên giao diện 08/11 (comment 04/11 ghi là chưa thử được). Comment gần nhất 06/11 (hạng đại lý, hoá đơn), không trùng.
**Vị trí:** comment trên epic PR-25.

> @thule Cập nhật Booking ngày 06–08/11 (Dev):
>
> - **Đã gỡ toàn bộ phần dành cho khách lẻ (B2C)** khỏi hệ thống, đúng mô hình chỉ bán cho đại lý: các trang và chức
>   năng cho khách lẻ, việc nhận yêu cầu khách lẻ, các trang khách lẻ của nhân viên, phần thanh toán của khách trên
>   TripPlanner. Dữ liệu cũ của phần này giữ thêm 30 ngày cho an toàn, xoá hẳn sớm nhất từ 28/11.
> - **Nhãn "AI-assisted" trên nội dung lấy từ CIS:** đã kiểm trên giao diện 08/11 ở 5 chỗ: ngăn khách sạn, chi tiết
>   dịch vụ, form dịch vụ, bộ soạn đề xuất và bản xem trước đề xuất (chi tiết nhãn AI trên các app ở comment cùng ngày
>   trên PR-23).
>
> Ảnh: bộ soạn đề xuất, nhãn "AI-assisted" cạnh phần mô tả lấy từ CIS (dữ liệu thử).

**Ảnh:** `docs/audits/2026-11-08-S273-session/aa1040-live/shots/b04-booking-proposal-builder.png` (`booking-de-xuat-nhan-ai.png`)

| Câu | Bằng chứng |
|---|---|
| Gỡ phần khách lẻ, deploy 06/11 | Linear (R4b) 06/11: Booking task :109 COMPLETED, `/booking/customer/v1/me` và `/trips` → 404; TripPlanner bỏ My Payments; snapshot S273 Booking `/booking/health` 200, schema bk-044 |
| Giữ 30 ngày, xoá sớm nhất 28/11 | Linear 06/11: DRY RUN, lần ghi B2C cuối 28/10 23:50Z → guard 30 ngày qua từ 28/11 23:50Z; migration xoá còn ở bản nháp, tech lead duyệt trước khi áp |
| Nhãn AI 5 chỗ | `aa1040-live/surfaces.json` b01–b05 captured; ảnh b01–b05 |

---

## 6. PR-26 — CRM cho đại lý

**Vì sao:** CRM bắt đầu nhận yêu cầu khách từ TripPlanner của đại lý (đã thử 08/11); lời nhắn của khách được giữ nguyên
(ship S272). Comment gần nhất 06/11, không trùng.
**Vị trí:** comment trên epic PR-26.

> @thule Cập nhật CRM cho đại lý ngày 07–08/11 (Dev):
>
> - **CRM nhận yêu cầu của khách gửi từ TripPlanner của đại lý:** yêu cầu vào đúng CRM của đại lý đó, không vào đại lý
>   khác. Đã thử trọn vòng 08/11 với một đại lý thử có cả gói CRM và TripPlanner (chi tiết và ảnh ở comment cùng ngày
>   trên PR-24). Chưa mở xem yêu cầu trên giao diện CRM.
> - **Lời nhắn của khách được giữ nguyên** và đặt trước phần thông tin tour; khi yêu cầu quá dài, chỉ phần thông tin
>   tour bị rút gọn. Đã kiểm bằng bài kiểm tự động trên 8.000 yêu cầu mẫu: không mất lời nhắn hay số điện thoại nào.
>   Chưa xem trên giao diện CRM.

**Ảnh:** không (ảnh nằm ở PR-24).

| Câu | Bằng chứng |
|---|---|
| Yêu cầu vào đúng CRM đại lý | như #4 (aggregate check PASS, Linear 08/11) |
| Lời nhắn giữ nguyên, 8.000 mẫu | Linear (lát 3) 08/11: CRM api :142 COMPLETED; fuzz 8.000 lead không mất lời nhắn/số điện thoại. Chỉ là bài kiểm tự động, không kiểm trên UI |

---

## 7. PR-20 — Báo cáo nền tảng kỳ 4 (03–09/11/2026)

**Vì sao:** báo cáo tuần; kỳ 3 đăng 02/11, đã qua một tuần, hôm nay thứ Hai 09/11.
**Vị trí:** comment trên epic PR-20 (như kỳ 3). Không tạo story mới trừ khi tech lead bảo.

> @thule Báo cáo nền tảng kỳ 4 (03–09/11/2026). Mọi số đo trên Dev với dữ liệu thử, còn thay đổi. Chi tiết ở comment
> trên từng epic (ngày 04/11, 06/11 và hôm nay).
>
> | App | Đã xong trong kỳ | Tiếp theo |
> |---|---|---|
> | CIS (PR-22) | Menu admin 7 nhóm; 6 vai trò nhân viên AA, người chăm sóc chỉ thấy đối tác được giao; trang chi phí AI theo app và đối tác; Writing Lab theo từng bước viết; AI viết nội dung chạy lại (05/11). Chất lượng viết: một bộ quy tắc chung, phiếu dữ kiện cho cả ba bộ viết, bài không còn bị cắt, kiểm lần cuối mọi bài đi ra; chủ đề Blog của một đại lý thử tăng 4 → 31 sau khi cập nhật dữ liệu tìm kiếm | Giảm số bài blog dưới ngưỡng; dữ liệu tìm kiếm mới tự đi vào gợi ý chủ đề |
> | App cho đại lý, Content studio (PR-23) | Tiếng Việt; giá "From" trong Marketplace; đại lý tự xin thêm CRM / TripPlanner; người được mời vào thẳng Content; nhãn AI trên mọi bản tải về và trên bài đăng WordPress (08/11) | Đại lý thí điểm |
> | TripPlanner (PR-24) | Giá "from" trên trang tour; địa chỉ Dev mới tripplanner.lumiguides.it.com; yêu cầu của khách từ TripPlanner của đại lý vào đúng CRM của đại lý (08/11) | Trang TripPlanner mang thương hiệu của từng đại lý |
> | Booking (PR-25) | Giá tour tự tính từ bảng giá nhà cung cấp; hạng đại lý và giá hợp đồng; bảng giá theo từng đại lý; hoá đơn và công nợ đại lý; nhập bảng giá nhà cung cấp từ Excel; gỡ phần khách lẻ (06/11); nhãn AI trên nội dung lấy từ CIS (08/11) | Nhập bảng giá thật (ngày 05/11: 2/892 tour có giá) |
> | CRM (PR-26) | Rà soát bảo mật ba vòng; thử tải 50 đại lý mô phỏng, 0 lỗi; sao lưu riêng cho đại lý thí điểm; số chỗ và tính năng theo gói; trang "AA prices"; giá bán gợi ý theo % cộng thêm của đại lý; nhận yêu cầu khách từ TripPlanner của đại lý (08/11) | Thẻ khách, tìm kiếm, chiến dịch trên app chung |
>
> **Nội dung tour** (đo 09/11):
>
> | Bước | Số |
> |---|---|
> | Tour thô đang bán (14 nước) | 917 |
> | Tour Master đang phục vụ | 892 (97 %) |
> | Có tuyến để gợi ý trên bản đồ | 699 |
> | Tour đã viết lại cho đại lý thử | 28 tour, 93 bản, 9 đại lý thử |
> | Bài viết cho đại lý thử | 405 bài; 6 bài từng đăng lên kênh của đại lý (chưa có đại lý thật) |
>
> **Chi phí AI và dữ liệu tìm kiếm** (theo sổ ghi từng lượt gọi; số Dev, chưa ổn định):
>
> | Tháng | AI (USD) | DataForSEO (USD) |
> |---|---|---|
> | 9 | 41,69 | 51,68 |
> | 10 | 269,35 | 19,30 |
> | 11 (tới 08/11) | 15,44 | 0,51 |
>
> Hoá đơn hạ tầng AWS theo tháng sẽ có ở kỳ 5.
>
> **Rủi ro:**
>
> - Tài khoản AI chính trên AWS vẫn chờ AWS mở quyền (đã trả lời các câu hỏi của AWS ngày 08/11). AI viết nội dung vẫn
>   chạy qua đường dự phòng, không gián đoạn.
> - Dữ liệu nhu cầu tìm kiếm còn mỏng: tuỳ thị trường chỉ 4–19 % dòng xếp hạng có số lượt tìm, nên chủ đề Blog gợi ý cho
>   đại lý còn ít. Dữ liệu được cập nhật theo từng đợt có trần chi phí.
> - Hệ thống vẫn ở môi trường thử nghiệm với dữ liệu thử; chưa có ngày go-live.

**Ảnh:** không.

| Câu | Bằng chứng |
|---|---|
| Các mục 03–05/11 (menu, vai trò, chi phí AI, Writing Lab, tiếng Việt, giá From, add-on, lời mời, giá Booking, hạng, hoá đơn, nhập Excel, CRM bảo mật/tải/sao lưu/AA prices/% cộng thêm) | Đã đăng có bằng chứng trên PR-22/23/24/25/26 ngày 04/11 và 06/11 (đọc lại 09/11) |
| AI viết nội dung chạy lại 05/11 | Comment PR-17 ngày 06/11 |
| Các mục 06–08/11 | Bằng chứng ở nháp #1–#6 |
| 2/892 tour có giá | Comment PR-25 ngày 06/11 (đo 05/11), chưa đo lại |
| Bảng nội dung tour | `system-picture/system-picture.vi.md` mục 1 (917, 892 = 97,3 %, 699, 28 tour / 93 bản / 9 tenant, 405 bài, 6 bài trong publish_log) |
| Chi phí theo tháng | `system-picture.vi.md` mục 4 (LLM tháng 9/10/11; DFS tháng 9/10/11) |
| Tài khoản AI chính chờ AWS | Checklist S273 mục 0 (thư trả lời AWS gửi 17:09 08/11); đầu phiên acc3 5 ok / 7 denied; AI chạy qua route tạm (OpenAI / Anthropic trực tiếp) |
| 4–19 % dòng có số lượt tìm | `system-picture.vi.md` mục 1 bảng demand (DE/FR/NL 4,4 % … US 19,1 %) |

---

## 8. KAN-90 — DataforSEO search spent high (TUỲ CHỌN)

**Vì sao:** issue của chị Thư về chi phí DataForSEO, comment cuối 03/10. Phiên S273 đo lại chi phí theo tháng và có một
lượt nghiên cứu có kiểm soát; số cho thấy bản sửa tháng 9–10 giữ được chi phí thấp. Tuỳ tech lead: số này cũng đã nằm
trong bảng chi phí của #7.
**Vị trí:** comment trên KAN-90.

> @thule Cập nhật chi phí DataForSEO (09/11/2026):
>
> | Tháng | DataForSEO (USD) |
> |---|---|
> | 9 | 51,68 |
> | 10 | 19,30 |
> | 11 (tới 08/11) | 0,51 |
>
> - Từ đợt sửa cuối tháng 9, nghiên cứu từ khoá chỉ chạy khi admin bấm, theo đợt có trần chi phí; phía đại lý không gọi
>   DataForSEO.
> - Lượt nghiên cứu ngày 08/11 cho các địa điểm trong tour của một đại lý thử (thị trường Mỹ) tốn 0,51 USD dữ liệu và
>   0,04 USD AI; số chủ đề đủ chuẩn Blog của đại lý này tăng từ 4 lên 31.
> - Hiện dữ liệu nhu cầu tìm kiếm mới phủ 4–19 % dòng xếp hạng tuỳ thị trường. Phần còn lại được cập nhật theo từng đợt,
>   mỗi đợt có trần chi phí và được duyệt trước khi chạy.

**Ảnh:** không.

| Câu | Bằng chứng |
|---|---|
| Chi phí theo tháng | `system-picture.vi.md` mục 4 (DFS tháng 9 51,68 / 10 19,30 / 11 0,51) |
| Chỉ admin bấm, đại lý không gọi DFS | `dfs-cost-audit/design.vi.md` mục 1 (S1 và nghiên cứu: "Admin bấm"; T2: "Không. Có test chặn"); comment KAN-90 ngày 29/09 |
| 0,51 + 0,04 USD; 4 → 31 | Snapshot S273 (DFS 0,508 + LLM 0,039); `design.vi.md` mục 1 "Bằng chứng ngày 08/11" |
| 4–19 % | `system-picture.vi.md` mục 1 bảng demand |
| Câu cuối (theo đợt, duyệt trước) | Kế hoạch, chưa phải việc đã ship → ô chốt ở đầu file |

---

## Ghi chép sau khi đăng

(điền comment id / link hoặc "chưa đăng: lý do" cho từng nháp)
