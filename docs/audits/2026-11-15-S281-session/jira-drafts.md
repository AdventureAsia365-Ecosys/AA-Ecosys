# S281 — Jira drafts (chờ tech lead duyệt, CHƯA ĐĂNG)

Trạng thái: **nháp**, chưa gọi công cụ ghi Jira nào. Soạn 15/11/2026 theo `skill/aa-jira-update/SKILL.md` +
`docs/guides/working-rules/stakeholder-communication.md`.

Khi đăng:
- `contentFormat: html`; `@thule` đổi thành mention node
  `<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`
  (markdown `@thule` không tạo mention thật). Danh sách / bảng đổi sang HTML.
- Ảnh: `uploadAttachmentToJiraIssue` → curl → `inlineFileId` theo đúng thứ tự ghi ở mỗi nháp. Tên file không dấu.
- Atlassian MCP hay timeout: đăng xong một cái, kiểm `updated >= -10m` trước khi đăng lại.

## Rà Jira trước khi soạn (15/11)

- JQL `project in (PR, KAN, CON) AND statusCategory != Done`: không có yêu cầu mới từ chị Thư sau đợt đăng 14/11
  20:31 (các issue cập nhật gần nhất đều là comment của mình: PR-22/25/26/27 lúc 20:31, PR-20 lúc 09:35). KAN/CON
  không đụng (luật: nháp vào epic app).
- Comment gần nhất đã đọc để không lặp: PR-20 (10652 diễn tập 14/11, 10625 báo cáo kỳ 4), PR-22 (10655, 10649, 10641,
  10640), PR-23 (10647), PR-24 (10648), PR-25 (10653, 10650), PR-26 (10654, 10651, 10646), PR-27 (10656).
- Không nháp PR-23, PR-24, PR-25: phiên này không ship tính năng mới nào ở Content studio, TripPlanner hay Booking ngoài
  các phần đã báo 14/11.
- **Báo cáo tuần kỳ 5 (10–16/11) dưới PR-20 chưa soạn:** kỳ kết thúc 16/11, để phiên sau (S282) soạn đủ tuần.
- Không báo: danh mục tính năng (đã báo Product map 14/11; phần còn lại là quy trình nội bộ), guard CI, các lane công
  cụ, việc chấm claim chưa xong.

---

## 1. PR-22 (CIS — nội dung & pipeline)

**Vì sao:** trang Docs đánh số và chip Settings làm sau đợt đăng 14/11 (nợ từ S280); trang Cài đặt thành nguồn duy
nhất; 3 báo cáo mới trong admin CIS; bước viết bổ sung blog cần đính chính câu "không dùng" của comment 11/11.

**Nội dung:**

> @thule Cập nhật CIS ngày 15/11 (Dev, dữ liệu thử):
>
> 1. **Trang Docs (Platform › Docs):** tài liệu gom theo nhóm có đánh số (1, 1.1, 1.2…), có nút Expand all / Collapse all; hiện có 169 trang trong 23 nhóm. Đã kiểm trên máy tính và điện thoại, nền sáng và tối.
> 2. **Trang Cài đặt (Platform › Settings):**
>    - Khi tìm, kết quả chia thành các chip theo nhóm kèm số lượng (ví dụ tìm "budget": All 3 | Retention 1 | Spend 2); bấm một chip để chỉ xem nhóm đó.
>    - Trang Cài đặt nay là nơi duy nhất quyết định các ngưỡng: không còn giá trị nào bị cấu hình máy chủ ghi đè. Kiểm ngày 15/11: CIS 214 thông số, TripPlanner 17 thông số, 0 bị ghi đè.
> 3. **Ba báo cáo mới trong mục Reports của admin CIS:**
>    - Chi phí AI của từng đại lý so với mức trần của gói, theo tháng. Tháng 10: 0 đại lý vượt ngưỡng cảnh báo, 0 đại lý có chi phí AI mà chưa đặt trần.
>    - Công nợ đại lý theo tuổi nợ, theo tuần. Tuần 02–08/11: 0 đại lý quá hạn, 23 đại lý đều trong hạn.
>    - Tóm tắt booking trong tuần (chỉ số lượng).
>
>    Cả ba đã chạy thật trên Dev ngày 14/11 (3/3 thành công); số liệu là dữ liệu thử, chưa ổn định. Hai báo cáo tuần được đặt lịch tự chạy mỗi thứ Hai, lần đầu 16/11 (chưa tới lần chạy tự động đầu tiên).
> 4. **Bài blog cho đại lý (đính chính cập nhật 11/11):** bước viết bổ sung cho bài ngắn đã được làm lại và nay được dùng. Bước này viết thêm từ dữ kiện của tour và thông tin nền về các địa danh có thật, không thêm hoạt động hay dịch vụ mà tour không có; đoạn nào trình bày một điểm tham quan tuỳ chọn như thể nằm trong lịch trình thì bị loại.
>    - Thử thật ngày 15/11 trên 3 tour của một đại lý thử: tour thứ ba chưa có chủ đề blog nên không có bài (đúng quy tắc); 2 bài còn lại đều đạt độ dài tối thiểu sau bước bổ sung. 1 bài được duyệt, 1 bài bị giữ để kiểm vì một chi tiết lịch trình, không phải vì độ dài. Chi phí AI cả lượt thử: 0,275 USD.
>    - Bước này đang bật cho đại lý thử, chưa bật cho mọi đại lý.
>
> Ảnh theo thứ tự: (1) trang Docs có nhóm đánh số, (2) chip theo nhóm khi tìm trong trang Cài đặt.

**Ảnh (đúng thứ tự):**
1. `docs/audits/2026-11-14-S280-session/verify/shots/docs-groups-desktop-light.png` → tên `trang-docs-nhom-danh-so.png`
2. `docs/audits/2026-11-14-S280-session/verify/shots/settings-chips-desktop-light.png` → tên `cai-dat-chip-theo-nhom.png`

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| Docs đánh số, Expand/Collapse, 169 trang 23 nhóm, desktop/phone sáng/tối | Log S280 (`docs/sessions/2026-11-14-S280-…md`, mục Docs + chip): CIS #1509 live, "23 nhóm, số 1.1…; Expand all → 169 trang, Collapse all → 0"; 6 ảnh `docs-groups-*` |
| Chip "All 3 \| Retention 1 \| Spend 2" | Log S280: CIS #1507 live, ảnh `settings-chips-*` (đã xem ảnh desktop-light) |
| 0 giá trị bị ghi đè; CIS 214, TP 17 | Linear AA-1096 comment 14/11 23:10Z (= 15/11 06:10 +07): `GET /admin/settings/registry` CIS 214 / 0 `env_override`, TP 17 / 0. Booking/CRM không đọc được qua registry nên không nêu số |
| 3 báo cáo, số tháng 10 và tuần 02–08/11, 3/3 thành công 14/11 | Linear AA-1003 comment 14/11 21:39Z; output (ảnh trong workspace) (K-TEN-AICAP 0, K-TEN-AINOCAP 0), `BK-03.md` (0 quá hạn, current 23), `FI-07.md`; `*-run.json` |
| Tự chạy thứ Hai, lần đầu 16/11 | `docs/reports/catalog.yaml` FI-07/BK-03 cadence "weekly Monday 01:30 UTC"; AA-1003: `generator: cis` từ 2026-11-16. Chưa quan sát lần tự chạy → ghi rõ |
| Blog: bước bổ sung làm lại, trial 15/11, 2 bài đạt sàn, 1 duyệt 1 giữ vì chi tiết lịch trình, 0,275 USD, chỉ bật cho đại lý thử | Linear AA-1077 comment 14/11 22:45Z (trial 6: extend 4.272→5.081 và 4.503→5.133 ký tự, f4_holds 0, held F17 trip fact, 0,275 USD ledger, `blog_extend_material = with_background` "for the tenant only") + comment đóng 15/11 02:18Z |

Không nêu chi tiết USD chi phí AI theo đại lý trong báo cáo (chi phí nội bộ chi tiết, luật 7).

---

## 2. PR-26 (CRM cho đại lý)

**Vì sao:** 4 tính năng CRM ship trong phiên (AI hỗ trợ nhân viên, mẫu "Booking confirmed", đầu trang chuyến đi, PDF
hợp đồng có chữ ký số) + đính chính dòng "chưa thử trọn vòng" về tour bị ngừng trong comment 14/11 (10651).

**Nội dung:**

> @thule Cập nhật CRM đại lý ngày 15/11 (Dev, đại lý thử, dữ liệu thử):
>
> 1. **AI hỗ trợ nhân viên đại lý** (mỗi đại lý tự bật, mặc định tắt):
>    - Soạn nháp trả lời khách theo giọng văn đại lý đã lưu.
>    - Đọc thư xác nhận của nhà cung cấp dịch vụ bổ trợ (ví dụ vé máy bay) mà nhân viên dán vào: lấy mã đặt chỗ và giờ đi, giờ đến cho dòng dịch vụ; thư báo hết chỗ được hiểu là bị từ chối. Dòng tour AA không dùng AI: trạng thái lấy thẳng từ Booking.
>    - Từ ghi chú của nhân viên, gợi ý phương án chỉ trong các tour AA mà đại lý đang được bán; không có tour phù hợp thì báo rõ.
>    - Thử thật trên đại lý thử Sen Vàng ngày 14–15/11: 49 lượt chạy đạt, tổng chi phí AI khoảng 0,007 USD (khoảng 0,00015 USD mỗi lượt). Khi gửi dồn dập, giới hạn số lượt AI của đại lý chặn 33 lượt trước khi gọi AI, không tốn tiền. Thử xong đã tắt AI lại như cũ. Chưa bật cho đại lý thật.
> 2. **Mẫu tin nhắn "Booking confirmed" / "Xác nhận đặt tour"** (tiếng Anh và tiếng Việt) có trong thư viện mẫu của AA; đại lý nhập về thư viện của mình bằng một nút (đã thử: nhập 6 mẫu). Mẫu chỉ dùng các trường tự điền: tên khách, chuyến, ngày khởi hành, điểm đến.
> 3. **Đầu trang chuyến đi** hiện tour AA gốc, ngày khởi hành, nhãn "Booked online" khi khách đặt từ trang tour, và link tới trang tour. Đã kiểm trên 3 chuyến đặt online.
> 4. **Thoả thuận đã ký tải về thành PDF có chữ ký số** (chuẩn PAdES): file gồm điều khoản đặt tour, cam kết của khách và trang ghi vết lúc ký. Đã thử thật: đại lý tải PDF, công cụ kiểm chữ ký PDF báo chữ ký còn nguyên, hợp lệ và phủ toàn bộ file. Khoá ký không bao giờ rời khỏi kho khoá.
>    - Trên Dev, chữ ký dùng chứng thư thử của hệ thống; chưa mở thử bằng Adobe Reader.
>    - Tiếng Việt: đã kiểm in đủ dấu trên bản mẫu; chưa thử với một đại lý dùng tiếng Việt.
>    - Nút tải trên cổng của khách đã có, chưa thử thật.
> 5. **Khi AA ngừng bán một tour** (cập nhật 14/11 ghi "chưa thử trọn vòng"): nay đã thử trọn vòng ngày 14–15/11. CRM gắn cờ 4 dòng (3 phương án đang mở, 1 dòng đã xác nhận) trên 4 chuyến của đại lý; khi tour được bán lại, cờ tự gỡ. Cờ hiện trong CRM chậm nhất khoảng 2 giờ sau thao tác ở CIS. Chi tiết buổi diễn tập ở PR-20.
>
> Ảnh theo thứ tự: (1) đầu trang chuyến đi có tour AA gốc, (2) thư viện mẫu tin nhắn có mẫu "Booking confirmed" và "Xác nhận đặt tour", (3) trang đầu của PDF thoả thuận đã ký (nội dung thử).

**Ảnh (đúng thứ tự):**
1. (ảnh trong workspace) → `crm-dau-trang-chuyen-di.png`
2. (ảnh trong workspace) → `crm-thu-vien-mau-tin-nhan.png`
3. (ảnh trong workspace) → `crm-pdf-thoa-thuan-da-ky.png`

(Đã xem cả 3 ảnh: dữ liệu đều là đại lý thử "E2E Pilot Rehearsal Travel"; PDF ghi rõ "Invented … Not a real contract".)

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| 3 tính năng AI, mặc định tắt, dòng tour AA không dùng AI, chỉ chọn tour AA | Linear AA-965 comment 15/11 01:40Z (Partner #321/#322, crm-069/070 applied) + comment kế hoạch 03/11 (R10 chỉ nhà cung cấp bổ trợ; R40 chỉ tour AA) |
| Đọc thư: mã VNX417Q, giờ 09:15/11:25; thư "flight full" → declined | AA-965 comment 15/11 (round 1–3) |
| 49 lượt đạt, 33 bị chặn ($0), 0,007169 USD, ~0,00015/lượt, đã tắt lại | AA-965 comment 15/11, bảng chi phí từ `crm.llm_call`; "Restored: … AI back off" |
| Chưa bật cho đại lý thật | AA-965: cổng review bảo mật trước pilot tenant |
| Mẫu EN/VI, nhập 6 mẫu | Linear AA-1089 comment 14/11 20:39Z (`import-aa` 200, added 6); ảnh templates |
| Đầu trang chuyến, 3 chuyến | AA-1089 comment: `aa_source` live, 3 trips `web_booking`; ảnh trip header |
| PDF PAdES hợp lệ, phủ toàn file, khoá không rời KMS | Linear AA-1012 comment 14/11 21:01Z: POST …/pdf 200, pyHanko intact/valid/trusted, ENTIRE_FILE, kms:Sign DIGEST |
| Chứng thư thử; chưa thử Adobe; VI chỉ bản mẫu; cổng khách chưa thử | AA-1012: Dev CA tự cấp; "A live Vietnamese screenshot would need a synthetic agency with locale vi"; live chỉ ở vai owner đại lý |
| Tour ngừng bán → 4 cờ, gỡ khi bán lại, ~2 giờ | Linear AA-1086 comment 15/11 01:20Z (X2) + AA-1093 comment đóng; root #806; `docs/audits/2026-11-15-S281-session/verify/aa1086/` |

---

## 3. PR-27 (Nền tảng)

**Vì sao:** xoá dữ liệu khi offboard nay gồm CRM (14/11 mới báo 3 app); diễn tập khôi phục TripPlanner; AA Academy lên
host `academy.lumiguides.it.com` (nợ "host academy" từ S280) và chạy trọn vòng tới chứng chỉ.

**Nội dung:**

> @thule Cập nhật nền tảng ngày 15/11 (Dev):
>
> 1. **Xoá dữ liệu khi đại lý ngừng hợp tác nay gồm cả CRM** (cập nhật 14/11 mới có CIS, Booking và TripPlanner). Chạy thật lần thứ hai trên một đại lý giả lập, hai lượt; mỗi lượt đều chạy thử trước và có người duyệt, có bản sao lưu trước khi xoá.
>    - CIS xoá 55 dòng; Booking xoá hoặc ẩn danh thông tin ở 3 dòng; CRM xoá 36 dòng, ẩn danh 1 dòng và huỷ khoá mã hoá giấy tờ của đại lý; TripPlanner không có dữ liệu của đại lý này.
>    - Kiểm lại độc lập ở cả 4 app: không còn dữ liệu cá nhân của đại lý.
> 2. **Diễn tập khôi phục dữ liệu TripPlanner của một đại lý** ngày 15/11: sao lưu 42 dòng, khôi phục thử, 42/42 dòng khớp.
> 3. **AA Academy** (<https://academy.lumiguides.it.com>, đăng nhập bằng tài khoản nhân viên): trang học cho đội ngũ AA, gồm bài học, lưu tiến độ, bài kiểm tra chấm trên máy chủ, chứng chỉ khi đạt và trang kiểm chứng chỉ công khai (ai có link đều kiểm được chứng chỉ còn hiệu lực hay không).
>    - Khoá Fundamentals hiện có module đầu tiên: 2 bài học và 1 bài kiểm tra.
>    - Đã thử trọn vòng ngày 15/11 bằng tài khoản nhân viên thử: học 2 bài, đạt bài kiểm tra module 6/6 và bài kiểm tra cuối khoá 100 %, nhận chứng chỉ; trang kiểm chứng chỉ báo VALID khi mở không đăng nhập.
>    - Các trang chạy trên máy tính và điện thoại, nền sáng và tối, không lỗi. Kết quả của tài khoản thử không tính vào số liệu của đội.
>
> 4. **TripPlanner trên tên miền riêng của đại lý:** đại lý có thể chạy trang lập kế hoạch trên tên miền của mình (ví dụ `trip.<tên miền đại lý>`) thay cho đường dẫn chung. Nhân viên AA thêm tên miền ở Tenant 360; hệ thống hiện 2 bản ghi DNS để đại lý tạo, tự xin chứng chỉ HTTPS và gắn tên miền. Tên miền thuộc nền tảng AA bị từ chối.
>    - Đã thử thật ngày 15/11 với một tên miền thử nghiệm và đại lý thử: trang chạy HTTPS trên tên miền riêng, mang tên đại lý; các lớp bảo vệ của trang vẫn áp dụng. Gỡ tên miền thì đại lý quay về đường dẫn chung.
>
> Ảnh: (1) trang kiểm chứng chỉ của AA Academy (chứng chỉ của tài khoản thử), (2) TripPlanner của đại lý thử trên tên miền riêng.

**Ảnh:**
1. (ảnh trong workspace) → `academy-kiem-chung-chi.png`

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| Lượt 2 gồm CRM, 2 lượt, chạy thử + duyệt, sao lưu trước | Linear AA-1093 comment đóng 15/11 05:08Z: R1 fingerprint bce15fdf (03:52Z), R2 32c1185e (04:46Z), snapshot `tenant-erase-20261115-erase02` |
| CIS 55, Booking 2 redact + 1 anonymise, CRM 36 + 1 + shred 1 khoá, TP 0 | AA-1093 comment đóng; checklist S281 "r1 … CIS 55 / BK 3 / TP 0, r2 … CRM 36+1+shred 1" |
| Kiểm lại độc lập 4 app, 0 dữ liệu cá nhân | AA-1093: E1–E4 PASS, verify 0/96, 0/22, 0/8, 0/83 pii |
| TP restore 42/42 | AA-1093 mục 3: `tp_tenant_backup` 42 dòng 4 bảng, `restore_drill` passed, 5/5, 5/5, 29/29, 3/3 |
| Academy: host, sign-in nhân viên, bài học, tiến độ, quiz chấm máy chủ, chứng chỉ, verify công khai | Linear AA-1105 comment 14/11 23:51Z (6 trang 200, 0 lỗi console, 1440/390 sáng/tối) + comment đóng 15/11 03:54Z (F3 6/6, final 100 %, chứng chỉ f9de22c4, verify 200 VALID trên trình duyệt ẩn danh); Partner #317, Infra #847/#858 |
| Khoá Fundamentals có 1 module (2 bài + quiz) | AA-1105 comment 23:51Z ("Fundamentals has one built module, F3") + `docs/learn/modules/F3-how-work-flows/module.yaml` |
| Tài khoản thử không tính số liệu | AA-1105 comment 23:51Z "its results stay out of the team's numbers" |

Ghi chú cho người duyệt: comment PR-22 ngày 14/11 (10649) đã viết "đã khôi phục thử thành công" cho cả CIS và
TripPlanner; Linear ghi lần diễn tập TripPlanner đạt trọn vẹn là 15/11. Mục 2 nêu trung tính con số 15/11; bỏ mục 2 nếu
muốn tránh trùng.

---

## 4. PR-20 (Báo cáo nền tảng — tiếp nối comment diễn tập pilot 14/11)

**Vì sao:** comment 10652 (14/11) kết bằng "Còn lại cho buổi sau: Đặt tour online, nhập giá, và các bước ngân sách của
pilot thật". Các phần đó đã báo trên PR-25/PR-26 tối 14/11; phiên này chạy nốt bước bật/tắt thí điểm và diễn tập
ngừng bán tour qua 4 app → đóng lại đầu việc diễn tập ngay trên thread đã mở.

**Nội dung:**

> @thule Diễn tập pilot (tiếp theo cập nhật 14/11): các bước còn lại đã chạy xong trên Dev với đại lý thử nghiệm.
>
> - **Đặt tour online, nhập giá, ngân sách AI:** đạt ngày 14/11 (xem comment 14/11 trên PR-25 và PR-26).
> - **Bật và tắt chế độ thí điểm cho một đại lý:** hệ thống chỉ cho một đại lý thí điểm cùng lúc, yêu cầu thứ hai bị từ chối; kết thúc thí điểm thì chỗ được giải phóng. Video: đạt 3/3 và 2/2 bước.
> - **Diễn tập AA ngừng bán một tour, qua 4 app (14–15/11):**
>   - Tour rút khỏi danh sách bán, đại lý đang dùng tour nhận thông báo, trang tour công khai báo tour không còn, Booking nhận tin, CRM gắn cờ 4 dòng trên 4 chuyến của đại lý.
>   - Khi khôi phục tour: trang tour mở lại, đại lý được thông báo lại, cờ trong CRM tự gỡ.
>   - Từ thao tác ở CIS tới cờ trong CRM mất tối đa khoảng 2 giờ.
> - **Kết thúc:** đại lý thử nghiệm đã ngừng hợp tác theo đúng quy trình; dữ liệu của đại lý hẹn xoá không sớm hơn 14/12/2026 (CRM không sớm hơn 12/02/2027), tài khoản Booking của đại lý đã tạm ngưng.
> - 6 video mới (bật/tắt thí điểm, đặt tour online quay lại, các bước ngân sách) đã lên thư mục video diễn tập.
> - Chưa có kịch bản diễn tập cho hai tình huống: Content studio và TripPlanner từ chối khi đại lý hết ngân sách AI.

**Ảnh:** không.

**Link:** không thêm. Trang video diễn tập (`https://claude.ai/artifact/9KCRRJ1cuGULqBHZeVeAmC`) chưa được cập nhật các
take S281 trong phiên này (registry ghi nó chỉ có 37 video S279) → chỉ thêm link nếu điều phối đã đăng lại trang đó với
các video mới.

**Câu → bằng chứng:**

| Câu | Bằng chứng |
|---|---|
| Book now, nhập giá, ngân sách đạt 14/11 | Jira PR-25 10653, PR-26 10654 (đã đăng 14/11 20:31); Linear AA-1086 comment S280 (REH-08a, REH-12-budget-on/off PASS) |
| Chỉ một đại lý thí điểm, yêu cầu 2 bị từ chối, End pilot giải phóng; 3/3, 2/2 | Linear AA-1086 comment 14/11 17:57Z: `pilot_taken`, REH-01b PASS 3/3, REH-12b PASS 2/2, "Dev pilot slot is free" |
| Diễn tập ngừng bán: 1 đại lý được báo, trang 410, Booking nhận, 4 cờ; khôi phục 200, đại lý được báo lại, cờ gỡ; ~2 giờ | AA-1086 comment đóng 15/11 01:20Z (X2): trash 18:15Z, 4 flags 20:00Z, restore 23:02Z, cleared 01:00:27Z, "up to about two hours"; evidence `docs/audits/2026-11-15-S281-session/verify/aa1086/x2-*.json`; root #806 |
| Offboard: xoá không trước 14/12, CRM 12/02/2027, Booking suspended | AA-1086 comment 17:57Z (Teardown) |
| 6 video lên Drive | AA-1086 comment 17:57Z (REH-01b, REH-12b, REH-06 v2, REH-12-budget-on, REH-12-budget-off, REH-08a v4) |
| Chưa có kịch bản studio/planner hết ngân sách | AA-1086 "Follow-up kept: gap G8" |

---

## Kết quả đăng

Đã đăng 15/11/2026 (~15:50 +07) sau khi tech lead duyệt "Đăng": PR-22 comment 10657 (2 ảnh), PR-26 comment 10658 (3 ảnh), PR-27 comment 10659 (2 ảnh, thêm mục 4 tên miền riêng TripPlanner), PR-20 comment 10660. Mention @thule bằng mention node.


Chưa đăng — chờ tech lead duyệt. Sau khi đăng: ghi comment id từng issue vào đây và vào log phiên; bản lưu chuyển sang
`docs/audits/2026-11-15-S281-session/jira-drafts.md` (không chứa account ID, secret hay link Drive riêng).
