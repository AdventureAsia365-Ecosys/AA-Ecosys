# Nháp Jira S249 + S250 (CHƯA ĐĂNG — chờ Nghiệp duyệt)

Soạn: 25/10/2026, ~11:20 giờ VN (04:20 UTC), Claude Code (subagent đóng phiên S250). Chỉ đọc Jira/Linear, không đăng,
không đổi trạng thái.

Nguồn số liệu: log S249 (`docs/sessions/2026-10-24-S249-crm-w1-w2-s1-catalogue-rewrite.md`, gồm nháp Jira S249 chưa
đăng — đã gộp vào đây và cập nhật số), checklist sống `.tmp-session/S250-checklist.md`, log wave
`.tmp-session/s250/waves.log` + `sum-cw_*.txt`, comment Linear S250 của AA-645, 910, 941, 978, 813, 943, 944, 977, 874,
908, 820, 979, 835, 945, 938 (đọc 25/10), bản export Linear S249 (`docs/linear-export/`), bằng chứng trong `docs/audits/`.

Đã đọc: toàn bộ 124 issue chưa Done của PR, KAN, CON (JQL `project in (PR, KAN, CON) AND statusCategory != Done`), và
comment mới nhất của PR-11, 12, 14, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, KAN-20, KAN-86. Comment gần nhất trên các
epic PR-22…PR-27 là ngày 23/10 (trước S249), nên nháp dưới đây không lặp lại nội dung đã đăng.

Khi đăng (theo skill `aa-jira-update`): `contentFormat: html`, thay `@thule` bằng mention node
`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`, bảng markdown →
bảng HTML, ảnh nhúng qua `uploadAttachmentToJiraIssue` (phase 1) + `inlineFileId`. Repo gốc AA-Ecosys là private, nên
**không dán link GitHub tới ảnh** — đính ảnh thẳng vào comment.

Thứ tự đăng đề xuất: PR-22 → PR-26 → PR-25 → PR-24 → PR-27 → PR-23.

---

## PR-22 — CIS — Nội dung & pipeline (Master content, đăng bài, ảnh)

**Vì sao chọn issue này:** comment gần nhất (23/10) báo đã chọn bộ viết mới cho lần viết lại toàn bộ catalogue và kế
hoạch "nhóm nhỏ → 50 tour → từng nước". Đây là phần tiếp theo: kết quả viết lại thật S249 + S250.

**Còn phải điền trước khi đăng:** các ô `[số cuối]` (Sri Lanka đang chạy lúc soạn; còn India 1–4). Lấy từ
`.tmp-session/s250/waves.log` + `sum-cw_sri-lanka_*.txt`, `sum-cw_india_*.txt`. Nếu đăng khi wave chưa xong thì giữ
câu "tới thời điểm soạn" và bỏ các dòng `[số cuối]`.

### Nội dung comment (sẵn để đăng)

@thule Cập nhật viết lại nội dung Master toàn catalogue, số liệu tới [giờ, ngày đăng]:

Bộ viết mới đã chạy thật trên hệ thống: thử 3 tour, rồi 50 tour mẫu ở 13 nước, sau đó chạy từng nước. Tour viết lại vẫn
giữ ngày đăng ban đầu. Mỗi đợt đều được kiểm tự động trước khi lên Master; chưa đợt nào chạm điều kiện phải dừng.

| Nước / đợt | Tour viết lại | Lên Master | Chờ duyệt | Trang có cờ kiểm tự động (trước → sau) | Chi phí (USD) |
|---|---|---|---|---|---|
| Thử 3 tour + mẫu 50 tour (nhiều nước) | 53 | 53 | 0 | 15 → 4 | 4,11 |
| Mongolia | 13 | 13 | 0 | 9 → 0 | 0,84 |
| Pakistan | 14 | 14 | 0 | 5 → 2 | 1,28 |
| Hàn Quốc | 26 | 26 | 0 | 15 → 3 | 2,38 |
| Bhutan | 27 | 27 | 0 | 9 → 0 | 1,75 |
| Đài Loan | 29 | 29 | 0 | 8 → 2 | 1,55 |
| Thái Lan | 34 | 34 | 0 | 13 → 1 | 2,75 |
| Lào | 36 | 36 | 0 | 11 → 1 | 2,87 |
| Philippines | 40 | 40 | 0 | 13 → 2 | 2,46 |
| Nhật Bản | 72 | 72 | 0 | 30 → 3 | 3,66 |
| Nepal | 76 | 76 | 0 | 29 → 7 | 6,91 |
| Trung Quốc | 111 | 111 | 0 | 47 → 5 | 8,17 |
| Sri Lanka | [số cuối] (112 tour, đang chạy lúc soạn) | [số cuối] | [số cuối] | [số cuối] | [số cuối] |
| Ấn Độ | [số cuối] (167 tour, chạy sau Sri Lanka) | [số cuối] | [số cuối] | [số cuối] | [số cuối] |
| **Tổng tới thời điểm soạn** | **531 / 810** | **531** | **0** | **204 → 30** | **38,71** |
| **Tổng cuối** | [số cuối] / 810 | [số cuối] | [số cuối] | [số cuối] | [số cuối] |

- Chi phí trung bình khoảng 0,07 USD mỗi tour. Trần chi phí cho cả lần viết lại là 120 USD; tới thời điểm soạn đã dùng
  38,71 USD.
- "Trang có cờ kiểm tự động" là tour bị bộ kiểm theo luật cố định đánh dấu, ví dụ số ngày trong lịch trình lệch thời
  lượng tour, hoặc phần "bao gồm / không bao gồm" mâu thuẫn nhau. Số này giảm từ 204 xuống 30 trên 531 tour. 30 tour còn
  cờ vẫn đã lên Master và sẽ được đọc lại bằng tay.
- Bài mới giữ lại nhiều con số có trong tour gốc hơn (độ cao, khoảng cách, thời gian di chuyển…). Ví dụ: Nepal từ khoảng
  32% lên 84%, Trung Quốc từ khoảng 33% lên 48%, Nhật Bản từ khoảng 46% lên 67%.
- Tên tour mới làm đường dẫn của tour đổi theo. Trên TripPlanner, đường dẫn cũ tự chuyển sang đường dẫn mới, nên link cũ
  không bị hỏng.
- Bước tiếp: chạy xong Sri Lanka và Ấn Độ, rồi gửi bảng tổng cuối.

Chưa kiểm: việc tự chuyển từ đường dẫn cũ sang đường dẫn mới đã kiểm từng tour cho các đợt tới Bhutan (50/50 tour mẫu và
từng nước đầu), các đợt từ Đài Loan trở đi chưa kiểm lại từng tour.

### Bằng chứng (nội bộ, không dán vào comment)

- S249: Linear AA-645 (comment pilot 3, wave ≤50); `docs/audits/2026-10-24-S249-s1-wave50/` (wave-report-d13.json);
  bảng nước S249 trong log S249.
- S250: bảng wave trong `.tmp-session/S250-checklist.md`; `.tmp-session/s250/sum-cw_*.txt` (China 1–3: gate 21→2,
  21→1, 5→2; phủ số liệu 0,326→0,46, 0,33→0,493, 0,302→0,494); `.tmp-session/s250/waves.log` (luỹ kế 478 tour đợt theo
  nước + 53 = 531; $38,71 / $120 sau China 3; Sri Lanka 1 START 03:40:12Z).
- Số gộp theo nước: Nhật = Japan 1 + 2 (20→1, 10→2; $2,508 + $1,155); Nepal = Nepal 1 + 2 (16→3, 13→4; $4,427 +
  $2,482); Trung Quốc = China 1–3 ($3,4945 + $3,7405 + $0,9326). Phủ số liệu gộp theo trọng số số tour.
- Đã bỏ khỏi comment (chi tiết nội bộ, đã tự xử lý): một tour Thái Lan lỗi lúc tách điểm, chạy lại thành công.

---

## PR-26 — CRM cho đại lý — quản lý khách của travel agency (sản phẩm hoàn chỉnh)

**Vì sao chọn issue này:** epic CRM. Comment gần nhất (23/10) báo phần nền đã sẵn và "bước tiếp: màn hình CRM cho
đại lý". S249 + S250 làm đúng phần đó. (PR-19 là yêu cầu gốc của chị Thư; đăng ở epic PR-26 cho gọn, như comment 23/10.)

### Nội dung comment (sẵn để đăng)

@thule Cập nhật CRM cho đại lý ngày [dd/mm]. Các màn hình và luồng dưới đây đã chạy trên Dev, kiểm bằng các đại lý thử
nghiệm và dữ liệu giả:

**Đăng nhập và thành viên**
- Đại lý có trang đăng nhập riêng, bắt buộc xác thực 2 lớp (mật khẩu và ứng dụng xác thực trên điện thoại).
- Chủ đại lý mời thành viên và phân vai trò. Kiểm tự động trên Dev: từ lúc mời tới lúc người được mời dùng được mất khoảng
  10 giây.

**Nhận khách và theo dõi chuyến**
- Đại lý có form công khai để khách gửi yêu cầu. Yêu cầu thành một thẻ trên bảng theo dõi và mở được thành hồ sơ chuyến
  (kiểm tự động trên Dev: khoảng 22 giây).
- Bảng theo dõi có 9 bước, từ nhận yêu cầu tới đang đi và huỷ. Muốn chuyển sang bước "Đề xuất" thì phiếu thông tin
  chuyến phải đủ ít nhất 80%, hoặc người có quyền xác nhận bỏ qua. Phiếu thông tin có thể gửi cho khách tự điền, hoặc
  điền từ cuộc gọi; khách tự chọn giờ gọi. Có hoàn tác trong 10 giây, và chuyển nhiều thẻ một lúc có xem trước. Lần kiểm tự
  động trên Dev ngày 25/10 đạt toàn bộ các bước này.

**Dịch vụ, nhà cung cấp, tiền**
- Mỗi đại lý có danh sách nhà cung cấp riêng; AA có sẵn trong danh sách như một nhà cung cấp.
- Mỗi chuyến có tab Bookings ghi từng dịch vụ đã đặt. Khi dịch vụ đã xác nhận, số tiền không sửa được nữa và tỷ giá được
  chốt tại thời điểm đó. Có trang cài đặt thanh toán.
- Tỷ giá cập nhật tự động mỗi ngày. Trên Dev đang dùng tỷ giá giả để thử; lần chạy ngày 25/10 thành công.

**Bảo vệ dữ liệu**
- Mọi lần xem và thao tác trên dữ liệu khách đều được ghi nhật ký. Mỗi giờ nhật ký được xuất sang kho lưu trữ không sửa,
  không xoá được. Đã kiểm trên Dev: kho nhận file đúng giờ.
- Trước khi gửi dữ liệu cho AI, hệ thống che tên, email, số điện thoại… của khách. Thử trên 260 mẫu tiếng Anh và tiếng
  Việt: 0 trường hợp lọt thông tin cá nhân. Tên địa danh bị che nhầm còn 3,98% (mục tiêu dưới 5%). Tính năng AI trong
  CRM hiện vẫn tắt trên Dev.
- Có thùng rác, giữ dữ liệu khi có yêu cầu pháp lý, và xoá dữ liệu theo yêu cầu của khách.

**Kết nối với portal và CIS**
- Khi một người không còn là thành viên của tenant trên portal, CRM tự nhận thông tin đó và cập nhật quyền. Phần kết nối
  đã chạy trên Dev và kiểm mỗi chu kỳ.
- Trong trang admin CIS có chỗ để đội AA soạn nội dung dùng chung cho đại lý (tiếng Anh và tiếng Việt, có lưu phiên bản):
  gói "Trước khi đi" theo nước, mẫu tin nhắn, đoạn nội dung cho chiến dịch. CRM chỉ nhận bản đã đăng, bản nháp không bao
  giờ được gửi sang. Hiện đã có 10 gói "Trước khi đi", 2 mẫu và 2 đoạn chiến dịch, viết tay (không dùng AI) để thử. Đội
  của chị thay bằng nội dung chính thức trong trang soạn đó. Khi đăng bản mới, đại lý đang dùng bản cũ vẫn mở được bản cũ.
- Trang quản lý đại lý cho nhân viên AA: danh sách đại lý, số chỗ đã dùng, chi phí AI, việc bị lỗi, khoá/mở tài khoản, xử
  lý yêu cầu xuất hoặc xoá dữ liệu. Chỉ admin mở được; tài khoản chỉ có quyền duyệt nội dung bị chặn (đã kiểm trên bản
  đang chạy).
- Công cụ nội dung trên portal đã chuyển về cùng ứng dụng với CRM ở phía sau. Tenant không thấy gì thay đổi: địa chỉ portal
  giữ nguyên, trang đăng nhập và trang điều khoản vẫn mở bình thường.

Chưa kiểm trên Dev (mới kiểm trong bộ kiểm thử phần mềm):
- Trang Bookings, Nhà cung cấp, Thanh toán: chưa đi qua bằng một phiên đăng nhập thật.
- Thùng rác, giữ dữ liệu, xoá theo yêu cầu: chưa thao tác trên giao diện bằng phiên đăng nhập thật.
- Đồng bộ thành viên: chưa thử một lần thu hồi thành viên thật (Dev chưa có thay đổi thành viên nào).
- Trang soạn nội dung AA trong admin CIS, và các nút khoá/mở, xử lý yêu cầu trên trang quản lý đại lý: chưa bấm thử bằng
  phiên admin thật.

Đang làm: email trong CRM (gửi và nhận thư với khách).

Ảnh: (1) màn hình chính của đại lý thử nghiệm trên máy tính, (2) trên điện thoại, (3) trang quản lý đại lý cho nhân viên
AA.

### Ảnh đính kèm

1. `docs/audits/2026-10-24-S249-aa935-signin/03-home-1440-light.png` (đổi tên khi đính: `crm-man-hinh-chinh-may-tinh.png`)
2. `docs/audits/2026-10-24-S249-aa935-signin/06-home-390-light.png` (`crm-man-hinh-chinh-dien-thoai.png`)
3. `docs/audits/2026-10-24-S250-aa941-ui/10-admin-agencies-drawer-nghiep.png` (`quan-ly-dai-ly-cho-AA.png`) —
   **Nghiệp xem lại ảnh trước khi đính** (ảnh chụp từ phiên admin của Nghiệp, có thể lộ email/tên).

### Bằng chứng (nội bộ)

- Đăng nhập + mời: AA-939 (export) — E2E Dev run 40076211334, invite → active 10 s; pool partner MFA bắt buộc
  (password + TOTP). AA-935 README 13/13.
- Nhận khách: AA-936 — E2E Dev run 40063125699 (22,4 s).
- 9 bước + phiếu + giờ gọi + hoàn tác + chuyển hàng loạt: AA-943 — Partner E2E Dev run 40133393046 success
  (`slice2-m1m2.spec.ts`).
- Sổ dịch vụ/nhà cung cấp: AA-944 — readiness crm-015; `crm_fx_fetch` synthetic, 21 tỷ giá, 0 lỗi. Không có E2E UI.
- Nhật ký: AA-940 — export hằng giờ, 5 object mỗi tầng (compliance + governance) lúc 07:16 UTC 24/10.
- Che dữ liệu cá nhân: AA-938 phương án B — Scrub corpus run 40102237468: 260 mẫu, 0 rò rỉ, over-scrub 3,98%.
- Vòng đời dữ liệu: AA-942 — 8 hàm quy tắc, trigger trên 11 bảng; UI chưa kiểm live.
- Thành viên: AA-978 — `/tenant/membership/v1/events` 200/401/403 đúng scope; CRM `membership_feed: ok`; 0 sự kiện.
- Nội dung AA: AA-977 — 28 mục (27 đăng, 1 nháp), `/catalog/v1/aa-content` 200/403/401; seed ghi "written by hand for Dev
  (no LLM)".
- Trang quản lý đại lý: AA-941 — reviewer bị chặn (403/redirect), phiên admin Nghiệp thấy 3 đại lý; nút ghi ẩn (chưa ở
  nhóm `crm-platform-admin`).
- Portal chuyển nhà: AA-979 P2a — production deploy run 40156305885, `/tenant-login` + `/terms` 200.
- AA-813 (tài khoản/mời/feed thành viên) đóng qua AA-939 + AA-978 — đã nằm trong các ý trên.

---

## PR-25 — Booking — Hệ thống đặt tour (trip case, báo giá, thanh toán)

**Vì sao chọn issue này:** comment gần nhất (23/10) báo phần bán tour cho đại lý (B2B) và hỏi chị chốt phí huỷ, gia hạn
giữ chỗ, giới hạn giữ lại, khoá kết nối riêng. Chưa có trả lời — nháp này **không hỏi lại**, chỉ báo phần mới.
(Tài khoản kiểm thử chỉ đọc cho Booking là việc nội bộ — không đưa vào.)

### Nội dung comment (sẵn để đăng)

@thule Cập nhật Booking ngày [dd/mm]:

- **Luồng sự kiện cho đại lý:** hệ thống của đại lý nhận được danh sách thay đổi về báo giá, giữ chỗ, gia hạn, huỷ… theo
  thứ tự, đọc lại nhiều lần không bị trùng. Luồng không chứa thông tin cá nhân của khách, và đại lý này không đọc được sự
  kiện của đại lý khác. Đã kiểm trên Dev với một đại lý thử nghiệm.
- **Bàn xử lý yêu cầu "on-request"** cho nhân viên: nhận hoặc từ chối yêu cầu của đại lý, có nhãn hạn trả lời.
- **Cờ sự cố cho chuyến khởi hành:** nhân viên đánh dấu một chuyến có sự cố, các đại lý liên quan nhận được thông báo
  (không kèm thông tin khách).
- **Giao diện ở màn hình 1440 px:** các bảng (hồ sơ chuyến, khách hàng, đề xuất, khách sạn, dịch vụ, nhà cung cấp, nhật ký,
  tỷ giá…) vừa khung, không phải kéo ngang. Đã kiểm trên bản đang chạy với dữ liệu thật của Dev: 25 trang, mỗi trang ở
  1440 px nền sáng và nền tối, 1280 px và điện thoại; 100/100 lần mở không tràn ngang, không lỗi.

Chưa kiểm trên Dev: bàn xử lý "on-request" và nút cờ sự cố mới kiểm trong bộ kiểm thử phần mềm, chưa bấm thử bằng phiên
đăng nhập nhân viên.

Đang làm: nội dung khách sạn và dịch vụ của Booking đi qua CIS để viết và duyệt.

Ảnh: (1) danh sách hồ sơ chuyến ở 1440 px, (2) bảng đề xuất ở 1440 px nền tối, (3) danh sách nhà cung cấp ở 1440 px.

### Ảnh đính kèm

1. `docs/audits/2026-10-24-S250-aa910-live/cases-1440-light.png` (`booking-ho-so-chuyen-1440.png`)
2. `docs/audits/2026-10-24-S250-aa910-live/proposals-1440-dark.png` (`booking-de-xuat-1440-nen-toi.png`)
3. `docs/audits/2026-10-24-S250-aa910-live/suppliers-1440-light.png` (`booking-nha-cung-cap-1440.png`)
   — Nghiệp xem lại ảnh trước khi đính (dữ liệu Dev, kiểm không có thông tin khách thật).

### Bằng chứng (nội bộ)

- AA-975 (S249, export): live CRM M2M, tenant thử c972 — `/b2b/v1/events` 200, no token 401, tenant khác 403; quote →
  hold → extend → 1 `hold.extended`; gọi lại trả y hệt; không có key PII. Desk + incident flag: chỉ CI (348 test xanh).
- AA-910 (S250): Booking #88; live 25 trang × (1440 sáng / 1440 tối / 1280 / 390) = 100 lần mở, 0 tràn trang, 0 lỗi
  console, 0 request lỗi, mọi bảng dư ≥ 78 px ở 1440. `docs/audits/2026-10-24-S250-aa910-live/` (README, result.json).
- AA-835 (đang làm): bk-023/278 áp, chưa chạy thử LLM.

---

## PR-24 — TripPlanner — Lên lịch trình trên bản đồ (khách B2C)

**Vì sao chọn issue này:** comment gần nhất (23/10) nói tour bị gỡ biến khỏi TripPlanner "trong vòng tối đa 30 phút, do
bộ nhớ đệm". S249 rút xuống vài giây; S250 thêm đăng nhập cho khách + "Chuyến đi của tôi".

### Nội dung comment (sẵn để đăng)

@thule Cập nhật TripPlanner ngày [dd/mm]:

- **Tour bị gỡ biến mất trong vài giây:** khi AA ngừng phục vụ một tour, TripPlanner được báo ngay. Thử trên Dev: trang
  tour báo "không còn" sau 8 giây (trước đây tới 30 phút). Khi phục vụ lại, tour hiện lại sau 24 giây.
- **Khách đăng nhập bằng mã gửi qua email**, không cần mật khẩu: nhập email, nhập mã nhận được là vào. Lần đầu dùng email
  mới thì tài khoản được tạo luôn.
- **"Chuyến đi của tôi" (My Trips):** chuyến khách đã lập khi chưa đăng nhập tự gắn vào tài khoản sau khi đăng nhập. Khách
  đăng nhập trên máy khác vẫn thấy và mở được chuyến đó. Khách khác không thấy chuyến của nhau. Nhập sai mã thì báo lỗi và
  không vào được.
- Trang đăng nhập đã bật tường lửa để chặn truy cập bất thường (chưa thử tấn công giả lập).
- Đã kiểm trên bản đang chạy (tripplanner.lumiguides.it.com) với 2 tài khoản khách thử nghiệm, trên máy tính và điện
  thoại: toàn bộ các bước trên đạt, không có lỗi.

Chưa kiểm: gửi chuyến cho tư vấn viên khi khách đã đăng nhập (email đã xác minh đi kèm sang Booking), mới kiểm trong bộ
kiểm thử phần mềm. Chưa làm: đăng nhập bằng Google/Facebook cho khách. Việc cần làm thêm: hiện nút đăng xuất cả khi trang
"Chuyến đi của tôi" không tải được.

Ảnh: (1) trang đăng nhập bằng email, (2) "Chuyến đi của tôi" sau khi đăng nhập, (3) mở lại chuyến trên máy khác (điện
thoại), (4) báo lỗi khi nhập sai mã.

### Ảnh đính kèm

1. `docs/audits/2026-10-25-S250-aa908-live/02a-sign-in-email-1440.png` (`tripplanner-dang-nhap-email.png`)
2. `docs/audits/2026-10-25-S250-aa908-live/r03-my-trips-after-sign-in-1440.png` (`tripplanner-chuyen-di-cua-toi.png`)
3. `docs/audits/2026-10-25-S250-aa908-live/r05b-second-device-opens-trip-390.png` (`tripplanner-mo-tren-may-khac.png`)
4. `docs/audits/2026-10-25-S250-aa908-live/06-wrong-code-1440.png` (`tripplanner-sai-ma.png`)
   — Ảnh chụp không có mã thật trong ô (theo README); Nghiệp xem lại email thử nghiệm hiện trên ảnh trước khi đính.

### Bằng chứng (nội bộ)

- AA-987 (S249): retire → 410 sau 8 s, restore 24 s (log S249, mục Bằng chứng).
- AA-908 (S250): comment Linear 25/10 04:00Z + `docs/audits/2026-10-25-S250-aa908-live/README.md` — lần chạy đầu
  FAIL (thiếu route `/me/*`), re-check sau Infra #381 PASS (`results-recheck-381.json`); sai mã → 400 `code_invalid`;
  0 lỗi console, 0 5xx sau #381. WAF: Infra #360 (đã apply; chưa thử tấn công giả lập — comment đã ghi rõ).
- Đưa riêng: chuyển `/tours/<cũ>` → 308 thuộc PR-22.

---

## PR-27 — Nền tảng — Đăng nhập, bảo mật, hạ tầng (dùng chung các app)

**Vì sao chọn issue này:** epic nền tảng; comment gần nhất (23/10) về quét lộ khoá, xoá dữ liệu theo yêu cầu, tên nội bộ
cố định cho cơ sở dữ liệu ("khi cần khôi phục chỉ đổi một chỗ"). S249 đã diễn tập đúng việc đó.

### Nội dung comment (sẵn để đăng)

@thule Cập nhật nền tảng ngày [dd/mm]:

- **Diễn tập khôi phục cơ sở dữ liệu:** tạo một bản khôi phục về một thời điểm trước khi dữ liệu bị xoá thử. Bản khôi phục
  sẵn sàng sau 21 phút 20 giây (mục tiêu dưới 1 giờ). So sánh đủ 164/164 bảng; phần dữ liệu bị xoá thử được lấy lại đúng.
  Đã chuyển các ứng dụng sang bản khôi phục rồi chuyển về, chỉ đổi một chỗ; mọi dịch vụ chạy lại bình thường. Chi phí diễn
  tập dưới 1 USD.
- **Báo lỗi tự động không còn gửi kèm thông tin đăng nhập hay email:** khi có lỗi, báo cáo gửi lên hệ thống theo dõi lỗi
  đã được che mã đăng nhập của nhân viên và email. Booking, CRM và TripPlanner đã được kiểm, vốn đã an toàn.
- **Bộ nhớ đệm được mã hoá:** bộ nhớ đệm dùng chung của CIS chuyển sang bản mới, mã hoá cả khi lưu và khi truyền, có mật
  khẩu truy cập. Dữ liệu chuyển sang đầy đủ, ứng dụng chạy bình thường sau khi chuyển, bản cũ chưa mã hoá đã gỡ. Chi phí
  giảm khoảng 2,8 USD/tháng.
- **Cảnh báo khi đọc cài đặt của tenant bị lỗi:** đã thử bằng một lỗi giả: email cảnh báo gửi tới, và email "đã ổn" gửi
  tới khi hết lỗi.
- **Tường lửa cho các trang đăng nhập** (nhân viên, khách TripPlanner, đại lý): đã bật.

Chưa kiểm trên Dev: phần che thông tin trong báo lỗi mới kiểm bằng bộ kiểm thử phần mềm, chưa tạo một lỗi thật trên Dev
để xem báo cáo. Tường lửa đăng nhập mới bật cấu hình, chưa thử tấn công giả lập.

### Bằng chứng (nội bộ)

- AA-829 (S249): `docs/audits/2026-10-24-S249-restore-drill/README.md` — RTO 21′20″, 164/164 bảng, restore 1 schema 40
  dòng (`equals_copy=true`), repoint `db.dev.internal` qua lại, 4 service stable; copy xoá. Chi phí < $1.
- CIS #979 (S249, trong AA-941): Sentry bỏ frame locals + che JWT/Bearer/email; test 16 (sentry); Booking/Partner/TP đã
  an toàn. Không có kiểm live.
- AA-874 (S250): comment Linear — Valkey 8 TLS + AUTH + at-rest; gate PASS; 23 key copy, 21 cờ tenant giống nhau; api :818
  / worker :384 `/health/ready` 200, không lỗi Redis; node cũ đã destroy; −$2,8/tháng; alarm test ALARM 03:59:44Z → OK
  04:14:44Z (email cả hai).
- WAF: Infra #360 (AA-908) — ba pool. Không có kiểm live.

---

## PR-23 — Portal tenant — Cổng cho đối tác

**Vì sao chọn issue này:** điều khoản sử dụng AI là điều khoản cho tenant, nằm ở trang `/terms` của portal. Bộ hồ sơ pháp
lý (gồm bản nháp điều khoản AI) đã gửi chị ở PR-27 ngày 22/10; việc cần chị quyết trước 11/11 đặt ở đây cho gọn.
Đề xuất bình tĩnh, có phương án, việc có cần luật sư hay không là chị quyết (memory `tech-focus-business-to-thu`).

### Nội dung comment (sẵn để đăng)

@thule Đề xuất về điều khoản sử dụng AI cho tenant, cần chị chọn trước ngày 11/11/2026:

**Bối cảnh:** chính sách sử dụng mới của Anthropic (hãng làm ra Claude, mô hình AI viết nội dung cho tenant qua Amazon)
có hiệu lực từ 12/11/2026 và áp dụng cả cho đối tác dùng nội dung viết bằng Claude. Em đã đọc lại bản chính sách đang
đăng ngày 24/10: ngày hiệu lực không đổi.

**Đã làm:**
- Bản nháp điều khoản AI đầy đủ đã cập nhật lên v0.2, khớp với chính sách đang đăng, để đính kèm hợp đồng đối tác.
- Trang điều khoản của portal đã có mục 3 "AI-generated content and acceptable use": tóm tắt ngắn các việc cấm (đánh giá
  giả, lời chứng thực giả, nhân vật bịa, mạng tài khoản giả độc lập, che giấu tài trợ…), nhãn nội dung AI, tenant là người
  đăng và chịu trách nhiệm, AA có quyền giữ, viết lại hoặc từ chối nội dung. Trang vẫn ghi "Draft — pending legal review":
  https://portal.lumiguides.it.com/terms
- Hiện chưa có tenant thật hay tenant trả tiền, nên không cần gửi thông báo cho ai. Mỗi tenant sẽ chấp nhận điều khoản này
  khi ký hợp đồng lúc bắt đầu dùng.
- CRM cho đại lý hiện chưa gọi Claude. Điều khoản này sẽ được đưa vào điều khoản của đại lý trước khi bật AI cho CRM.

**Phương án:**
- **A.** Dùng điều khoản như bản nháp: bản tóm tắt trên portal đã có trước 11/11, điều khoản đầy đủ đính kèm hợp đồng mỗi
  tenant lúc bắt đầu. Có nhờ luật sư xem hay không là chị quyết.
- **B.** Nhờ luật sư xem trước; trong lúc chờ, portal vẫn để bản tóm tắt ở dạng nháp.
- **C.** Dùng ngay như A, và nhờ luật sư xem trước khi có tenant trả tiền đầu tiên.

**Đề xuất:** A hoặc C. Vì chưa có tenant nào, dùng ngay không tốn gì và kịp ngày 12/11; C thêm một lần luật sư xem trước
khi tenant đầu tiên trả tiền.

**Cần chị quyết:**
1. Chọn A, B hay C.
2. Có nhờ luật sư xem không, và nếu có thì trước thời điểm nào.

Nếu nhờ luật sư, bản nháp đã có sẵn danh sách câu hỏi cho luật sư (ví dụ: nội dung tenant đăng dưới tên mình không có
nhãn AI thì có ổn không; điều khoản ràng buộc tenant bằng cách nào; luật áp dụng). Em gửi file khi chị cần.

Ngoài ra: công cụ nội dung trên portal đã chuyển về cùng ứng dụng với CRM ở phía sau. Tenant không thấy gì thay đổi; địa chỉ
portal, trang đăng nhập và trang điều khoản vẫn mở bình thường.

### Bằng chứng (nội bộ)

- AA-820: root #240 (Draft v0.2 `docs/legal/tenant-terms-ai-clause-draft.md`, §0 nơi đặt, §4 chấp nhận lúc onboarding,
  §6 14 câu hỏi cho luật sư); CIS #981 portal `/terms` §3 — live 200, "Draft v0.2", link AUP.
- Phương án A/B/C + đề xuất: `docs/legal/readiness-packet.md` §12 (bản trên origin/master; checkout local đang cũ).
- Portal chuyển: AA-979 P2a — production deploy run 40156305885; `/tenant-login` + `/terms` 200.
- Câu "Em gửi file khi chị cần": file nằm trong repo private; nếu Nghiệp muốn gửi luôn thì đưa bản v0.2 lên thư mục
  Google Drive "Legal readiness packet (2026-10-22)" (link đã có ở PR-27) và thay câu này bằng link.

---

## Không soạn (ghi lý do để Nghiệp xem)

| Issue | Lý do không soạn lần này |
|---|---|
| PR-14 (đăng nhập không mật khẩu Admin + Tenant) | Không có gì mới đúng phạm vi: đăng nhập đại lý trong CRM dùng mật khẩu + ứng dụng xác thực (không phải không mật khẩu); tenant portal vẫn đăng nhập như cũ; Google/Facebook chưa làm. Đăng nhập bằng mã email cho khách TripPlanner đã đưa vào PR-24. |
| PR-19 (CRM cho travel agencies — yêu cầu gốc) | Gộp vào epic PR-26 như comment 23/10. Nếu Nghiệp muốn chị Thư thấy ở PR-19, đăng 1 dòng trỏ sang PR-26. |
| PR-15 (dữ liệu tour thô trước khi chạy lại toàn bộ) | Liên quan việc viết lại S1, nhưng tiến độ đã đăng ở PR-22 từ 23/10; giữ một nơi. |
| PR-11 (Visual map planner), PR-12 (Booking system) | Issue cũ; cập nhật mới đã chuyển sang epic PR-24, PR-25 từ 23/10. |
| PR-20 / PR-21 (báo cáo nền tảng định kỳ) | Không thuộc phạm vi task này; báo cáo tuần là việc riêng (memory `platform-report-weekly`). |
| KAN-20 (Asian Trails benchmark), KAN-86 (B2B Infrastructure), KAN-90 (DataForSEO) | Không có thay đổi S249/S250 đáng báo; KAN-90: các wave viết lại dùng DataForSEO $0. |
| Việc chưa xong (báo khi xong, memory `jira-report-when-done`) | AA-945 email CRM (chưa kiểm nhận mail live); AA-835 nội dung khách sạn/dịch vụ Booking → CIS (chưa chạy thử trả phí); AA-926/924/790/916 cổng chất lượng nội dung tenant (pilot trả phí chưa chạy); AA-979 P2b. |
| Nội bộ | Tài khoản kiểm thử chỉ đọc cho Booking (AA-910), ảnh zoom 150% của Nghiệp, OpenAPI/kiểm thay đổi API (AA-899), lỗi tách điểm 1 tour Thái Lan đã tự xử lý. |
