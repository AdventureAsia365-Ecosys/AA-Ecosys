# Nháp Jira S251 (gộp S249 + S250 + S251) — CHƯA ĐĂNG, chờ Nghiệp duyệt

Soạn: 25/10/2026, ~18:50 giờ VN (11:50 UTC), Claude Code (subagent đóng phiên S251). Chỉ đọc Jira/Linear/GitHub,
không đăng, không sửa, không đổi trạng thái gì trên Jira.

Bản này **thay** nháp S249 + S250 (`docs/audits/2026-10-25-S250-wrap/jira-drafts.md`, chưa đăng): mỗi issue Jira chỉ
còn MỘT nháp, số liệu cập nhật tới S251. Không đăng nháp S250 nữa.

**Nguồn số liệu:** comment Linear Done của AA-645 (25/10 10:33Z) và AA-825 (25/10 10:19Z); comment S250 của AA-945;
checklist `.tmp-session/S251-checklist.md`; log wave `.tmp-session/s250/waves.log` + `sum-cw_*.txt`; bằng chứng
`.tmp-session/s251/` (aa945, aa825, ui-cis, dfs-out.json, audit-s1prop); danh sách PR merge + run deploy trên GitHub
(đọc 11:47Z); trạng thái cảnh báo secret/code scanning đọc bằng `gh api` lúc ~11:48Z; bản tóm tắt S251 của phiên điều
phối (cho các số không có file: ngân sách AWS AI). Nháp S249 + S250 gộp từ file S250 nêu trên.

**Đã đọc Jira:** cả 124 issue chưa Done của PR, KAN, CON (JQL `project in (PR, KAN, CON) AND statusCategory != Done`).
Issue cập nhật gần nhất là các epic PR-22…PR-27 lúc 23/10 (trước S249), nên không có gì đã đăng bị lặp lại. Báo cáo
định kỳ gần nhất dưới PR-20 là PR-21 (kỳ 1, 01–19/10).

**Khi đăng** (skill `aa-jira-update`): `contentFormat: html`; thay `@thule` bằng
`<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>`; bảng markdown →
bảng HTML; ảnh đính thẳng qua `uploadAttachmentToJiraIssue` (phase 1) + `inlineFileId`, không dán link GitHub.
Atlassian MCP hay timeout: sau timeout đọc lại comment mới nhất trước khi đăng lại.

**Thứ tự đăng đề xuất:** PR-22 → PR-26 → PR-25 → PR-24 → PR-27 → PR-23 → báo cáo tuần (story mới dưới PR-20, đăng cuối
để link được tới các comment vừa đăng).

## Kiểm trước khi đăng (ô cần chốt)

| Ô | Hiện trạng lúc soạn (11:50Z) | Làm gì |
|---|---|---|
| `[K1]` cảnh báo "lộ khoá" giả (PR-27, báo cáo tuần) | 80/96 đã đóng (5 repo); AA-CIS-App còn 16 mở, PR sửa (CIS #1010) chưa merge vì CI gitleaks đỏ (thiếu nhãn) | Nếu #1010 đã merge + 16 cảnh báo CIS đã đóng → dùng câu "96/96"; nếu chưa → dùng câu "80/96, phần còn lại …" (cả hai câu đã soạn sẵn) |
| `[K2]` lỗi quét mã (PR-27, báo cáo tuần) | TripPlanner #152 merged (1 lỗi đóng), CIS #1001 merged (1 lỗi đóng); CIS #1011 (5 lỗi ReDoS + 1 trang 404) **chưa merge**, CIS còn 6 cảnh báo mở | Chỉ ghi "7 lỗi đã sửa" khi #1011 đã merge + deploy và cảnh báo CIS về 0; nếu chưa → câu thay thế đã soạn |
| `[K3]` CRM vòng đời chuyến + sản phẩm AA (PR-26) | Partner #49/#50 (CRM-18) và #55/#56 (CRM-19) đã merge, DB Migrate + Deploy Dev xanh. **Không tìm thấy** bằng chứng chạy thử trọn vòng trên Dev (E2E Dev hay ảnh); CRM-18/19 trên Linear vẫn In Progress, không có comment | Nếu phiên điều phối có E2E Dev / ảnh → đổi đoạn "Chưa kiểm" tương ứng; nếu không → giữ nguyên như soạn |
| `[K4]` trang Tài khoản portal (PR-23) | Partner #51 + CIS #1002 merged, Vercel Deploy (portal) xanh 11:43Z. Chưa có ảnh bằng phiên tenant thật | Có ảnh thì đính + bỏ câu "chưa chụp ảnh" |
| `[K5]` báo cáo tuần chốt 26/10 | Số tới 25/10 | Đăng sau 26/10 thì thêm việc của 26/10 (nếu có) |

---

## PR-22 — CIS — Nội dung & pipeline (Master content, đăng bài, ảnh)

**Vì sao chọn:** comment gần nhất (23/10) báo đã chọn bộ viết mới và kế hoạch "thử nhỏ → 50 tour → từng nước". Lần viết
lại toàn catalogue đã xong ở S251, nên đây là báo cáo kết quả cuối (thay nháp S250 còn ô `[số cuối]`).

### Nội dung comment (sẵn để đăng)

@thule Dạ chị, việc viết lại toàn bộ nội dung Master đã xong (số liệu ngày 25/10/2026):

Bộ viết mới đã viết lại **810/810 tour** của đợt này: thử 3 tour, rồi 50 tour mẫu ở 13 nước, sau đó chạy từng nước
(22 đợt). **Tất cả 810 tour đã lên Master, 0 tour phải chờ duyệt, 0 tour phải giữ bản cũ.** Mỗi đợt đều được kiểm tự
động trước khi lên Master và có bản sao lưu cơ sở dữ liệu trước khi chạy; không đợt nào chạm điều kiện phải dừng.

| Nước / đợt | Tour viết lại | Lên Master | Chờ duyệt | Trang có cờ kiểm tự động (trước → sau) | Chi phí (USD) |
|---|---|---|---|---|---|
| Thử 3 tour + mẫu 50 tour (13 nước) | 53 | 53 | 0 | 15 → 4 | 4,11 |
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
| Sri Lanka | 112 | 112 | 0 | 40 → 0 | 8,49 |
| Ấn Độ | 167 | 167 | 0 | 68 → 6 | 12,14 |
| **Tổng** | **810** | **810** | **0** | **312 → 36** | **59,34** |

- **Chi phí:** 59,34 USD cho cả lần viết lại, trong trần 120 USD; trung bình khoảng 0,07 USD mỗi tour. (Các dòng làm
  tròn nên cộng tay lệch vài cent so với tổng.)
- **Trang có cờ kiểm tự động** là tour bị bộ kiểm theo luật cố định đánh dấu, ví dụ số ngày trong lịch trình lệch thời
  lượng tour, hoặc phần "bao gồm / không bao gồm" mâu thuẫn nhau. Trên 757 tour chạy theo nước: 297 → 32; tính cả 53 tour
  thử: 312 → 36. Các tour còn cờ vẫn đã lên Master và sẽ được đọc lại bằng tay.
- **Giữ nhiều số liệu của tour gốc hơn** (độ cao, khoảng cách, thời gian di chuyển…): trung bình từ khoảng 42% lên 67%.
- **Lớp kiểm chứng (Jev)** chạy cho 100% tour ở mọi đợt.
- **Đường dẫn tour:** tên tour mới làm đường dẫn đổi theo. Trên TripPlanner, đường dẫn cũ tự chuyển sang đường dẫn mới.
  Đã kiểm từng tour có đường dẫn đổi ở tất cả các đợt: đều chuyển đúng, trang mới mở bình thường. Tour vẫn giữ ngày đăng
  ban đầu.
- **Giữ nguyên bản cũ có chủ đích:** 39 tour có cưỡi voi giữ nguyên nội dung và chờ người đọc lại, theo hướng chị đã chọn;
  54 tour dùng làm bộ mẫu chuẩn để đo chất lượng cũng giữ nguyên.
- Bộ viết mới là bộ viết mặc định từ nay, kể cả cho tour mới.

**Bước tiếp:** nội dung tour đã mới, nên các phần dùng lại nội dung đó cũng phải đi theo: các đoạn đường và tuyến gợi ý,
thứ tự xếp hạng, địa điểm và tìm kiếm theo nghĩa, lịch trình trên TripPlanner và chuyến khách đã lưu, danh mục tour trong
CRM, đề xuất của Booking và nội dung SEO. Em đã đo hiện trạng từng phần và đang làm tiếp, kèm một phép kiểm tự động để
biết phần nào còn dùng nội dung cũ.

### Câu → bằng chứng (nội bộ, không dán vào comment)

| Câu | Bằng chứng |
|---|---|
| 810/810, 757 + 53, 0 chờ duyệt, 0 giữ v1, 22 đợt, $59,34/$120, ~$0,073/tour | Linear AA-645 comment Done 25/10 10:33Z; `.tmp-session/s250/waves.log` (`ALL_WAVES_DONE` 09:55:57Z, luỹ kế $59,34) |
| Bảng theo nước (S249–S250) | nháp S250 `docs/audits/2026-10-25-S250-wrap/jira-drafts.md` (mục PR-22, bằng chứng) |
| Sri Lanka 112: 40 → 0, $8,49 | `.tmp-session/s250/sum-cw_sri-lanka_1.txt` (12→0, $3,6532), `_2.txt` (25→0, $3,7905), `waves.log` (Sri Lanka 3: $43,0925 − $42,0499 = $1,0426; AA-645: 3→0) |
| Ấn Độ 167: 68 → 6, $12,14 | AA-645 (India 1–4: 13→1, 21→1, 28→2, 6→2); `waves.log` ($55,2322 − $43,0925 = $12,1397) |
| Pilot + ≤50: 15 → 4, $4,11 | AA-645 comment 24/10 (2/3→0/3; 13/50→4/50; $0,2678 + $3,8386); `docs/audits/2026-10-24-S249-s1-wave50/` |
| Số liệu gốc 0,415 → 0,674; giọng thương hiệu 7,69 → 8,00 (không đưa vào comment, chỉ để tham khảo) | AA-645 comment Done |
| Jev 100%, 39 tour cưỡi voi + 54 tour mẫu giữ v1, v2 mặc định | AA-645 comment Done |
| Đường dẫn 308 | AA-645: S249 50/50 + 3/3; S250 tới Lào; S251 389/389 (Philippines → Sri Lanka 2) + 174/174 (Sri Lanka 3 + Ấn Độ) — đếm theo tour có đường dẫn đổi |
| Bước tiếp | Linear AA-988, AA-989, AA-990, AA-991 (Backlog, tạo S251); số đo `.tmp-session/s251/audit-s1prop/coverage2.txt` (chưa chép vào docs/audits) |

Đã bỏ khỏi comment (nội bộ, đã tự xử lý): một tour Thái Lan lỗi lúc tách điểm, chạy lại thành công; điểm giọng thương hiệu
(thang chấm v1 và v2 khác nhau, chỉ để báo cáo).

**Evidence/links:** `docs/audits/2026-10-24-S249-s1-go-no-go/`, `docs/audits/2026-10-24-S249-s1-wave50/`,
`docs/audits/2026-10-24-S250-s251-go-no-go/`, `docs/audits/2026-10-25-S250-wrap/jira-drafts.md`; ngoài docs/audits:
`.tmp-session/s250/waves.log`, `.tmp-session/s250/sum-cw_*.txt`, `.tmp-session/s251/audit-s1prop/coverage2.txt`.
Không có ảnh.

---

## PR-26 — CRM cho đại lý — quản lý khách của travel agency (sản phẩm hoàn chỉnh)

**Vì sao chọn:** epic CRM; comment gần nhất (23/10) báo phần nền đã sẵn, "bước tiếp: màn hình CRM cho đại lý". S249–S251
làm đúng phần đó. (PR-19 là yêu cầu gốc; đăng ở epic cho gọn như 23/10.)

### Nội dung comment (sẵn để đăng)

@thule Dạ chị, cập nhật CRM cho đại lý (số liệu ngày 25/10/2026). Các phần dưới đây đã lên môi trường Dev, kiểm bằng
các đại lý thử nghiệm và dữ liệu giả. Mỗi mục ghi rõ phần nào đã thử thật trên Dev, phần nào mới kiểm trong bộ kiểm thử
phần mềm.

**Đăng nhập và thành viên**
- Đại lý có trang đăng nhập riêng, bắt buộc xác thực 2 lớp (mật khẩu và ứng dụng xác thực trên điện thoại).
- Chủ đại lý mời thành viên và phân vai trò. Thử trên Dev: từ lúc mời tới lúc người được mời dùng được mất khoảng 10 giây.
- Khi một người không còn là thành viên của tenant trên portal, CRM tự nhận thông tin đó và cập nhật quyền. Đã bật cảnh báo
  khi việc đồng bộ này bị kẹt hoặc có sự kiện bị từ chối.

**Nhận khách và theo dõi chuyến**
- Form công khai để khách gửi yêu cầu; yêu cầu thành một thẻ trên bảng theo dõi và mở được thành hồ sơ chuyến (thử trên
  Dev: khoảng 22 giây).
- Bảng theo dõi 9 bước, từ nhận yêu cầu tới đang đi và huỷ. Muốn sang bước "Đề xuất" thì phiếu thông tin chuyến phải đủ ít
  nhất 80%, hoặc người có quyền xác nhận bỏ qua. Phiếu có thể gửi khách tự điền hoặc điền từ cuộc gọi; khách tự chọn giờ
  gọi. Có hoàn tác trong 10 giây, chuyển nhiều thẻ một lúc có xem trước. Lần kiểm tự động trên Dev ngày 25/10 đạt toàn bộ.

**Từ đề xuất tới khi khách đi (mới)**
- Đại lý soạn đề xuất dạng văn bản và gửi link cho khách; khách mở link và bấm chấp nhận.
- Mỗi chuyến có lịch thanh toán. Khi đại lý đánh dấu đã nhận tiền cọc, chuyến tự chuyển sang "Đã đặt" và khách được mời
  vào cổng dành cho khách.
- Khách vào cổng bằng mã 6 số dùng một lần, gửi từ hộp thư của đại lý. Phần khách điền thông tin chuẩn bị chuyến đi chỉ mở
  sau khi đã nhận cọc.
- Ký điện tử bản đầu: khách gõ tên, nhập mã ký mới; hệ thống lưu bằng chứng của lần ký.

**Tour và dịch vụ của AA trong chuyến (mới)**
- Đại lý thêm tour hoặc dịch vụ của AA vào chuyến. Giá, giữ chỗ và tình trạng chỉ lấy từ hệ thống Booking của AA; đại lý
  xem được nhưng không gõ tay hay sửa được các dòng này. Trợ lý AI trong CRM cũng không tự xác nhận được một booking của AA
  (tính năng AI trong CRM hiện vẫn tắt).
- Khi Booking tạm thời không trả lời, yêu cầu được xếp hàng, hiện "AA đang xử lý" và tự gửi lại sau, không tạo trùng giữ chỗ.
- Có cảnh báo khi giá đang là giá "từ" (chỉ nhắc, không chặn).

**Email với khách (mới)**
- Mỗi đại lý có một địa chỉ nhận thư chuyển tiếp riêng. **Đã thử thật trên Dev:** thư khách gửi tới, có mã chuyến trong
  tiêu đề, được gắn đúng vào chuyến đó (kể cả khi thư không phải là thư trả lời); thư có mã không khớp chuyến nào thì vào hộp
  "Chưa gắn chuyến"; thư gửi tới địa chỉ không tồn tại bị bỏ, hệ thống chỉ đếm số, không lưu nội dung; file PDF đính kèm
  được lưu, loại file không cho phép thì bị từ chối.

**Dịch vụ, nhà cung cấp, tiền**
- Mỗi đại lý có danh sách nhà cung cấp riêng; AA có sẵn trong danh sách như một nhà cung cấp.
- Tab Bookings ghi từng dịch vụ đã đặt; dịch vụ đã xác nhận thì số tiền không sửa được nữa và tỷ giá được chốt lúc đó. Có
  trang cài đặt thanh toán. Tỷ giá tự cập nhật mỗi ngày (trên Dev đang dùng tỷ giá giả để thử; lần chạy 25/10 thành công).

**Bảo vệ dữ liệu**
- Mọi lần xem và thao tác trên dữ liệu khách đều ghi nhật ký; mỗi giờ nhật ký được xuất sang kho lưu trữ không sửa, không
  xoá được (đã kiểm trên Dev: kho nhận file đúng giờ).
- Trước khi gửi dữ liệu cho AI, hệ thống che tên, email, số điện thoại… của khách. Thử trên 260 mẫu tiếng Anh và tiếng
  Việt: 0 trường hợp lọt thông tin cá nhân; tên địa danh bị che nhầm còn 3,98% (mục tiêu dưới 5%).
- Có thùng rác, giữ dữ liệu khi có yêu cầu pháp lý, và xoá dữ liệu theo yêu cầu của khách.

**Kết nối với CIS và quản lý cho AA**
- Trong trang admin CIS có chỗ để đội AA soạn nội dung dùng chung cho đại lý (tiếng Anh và tiếng Việt, có lưu phiên bản):
  gói "Trước khi đi" theo nước, mẫu tin nhắn, đoạn nội dung cho chiến dịch. CRM chỉ nhận bản đã đăng. Hiện có 10 gói
  "Trước khi đi", 2 mẫu và 2 đoạn chiến dịch viết tay để thử; đội của chị thay bằng nội dung chính thức trong trang soạn đó.
- Trang quản lý đại lý cho nhân viên AA: danh sách đại lý, số chỗ đã dùng, chi phí AI, việc bị lỗi, khoá/mở tài khoản, xử
  lý yêu cầu xuất hoặc xoá dữ liệu. Chỉ admin mở được (đã kiểm: tài khoản chỉ có quyền duyệt nội dung bị chặn).

**Chưa thử thật trên Dev** (mới kiểm trong bộ kiểm thử phần mềm, hoặc cần một người làm bước đăng nhập):
- Phần "Từ đề xuất tới khi khách đi" và "Tour và dịch vụ của AA trong chuyến": đã lên Dev, chưa đi trọn một chuyến bằng
  phiên đăng nhập thật, chưa có ảnh. `[K3]`
- Email: chưa thử kết nối Gmail hoặc Microsoft 365 để gửi thư bằng địa chỉ của đại lý (cần một người đăng nhập tài khoản
  thật), chưa gửi thật qua SMTP, chưa thử nhập lịch sử thư cũ; màn hình Tin nhắn chưa có ảnh.
- Cảnh báo đồng bộ thành viên: đã bật, chưa thử bằng một lỗi giả; chưa có lần thu hồi thành viên thật nào trên Dev.
- Trang Bookings, Nhà cung cấp, Thanh toán, thùng rác / giữ dữ liệu / xoá theo yêu cầu: chưa thao tác bằng phiên đăng nhập
  thật.
- Trang soạn nội dung AA trong admin CIS, các nút khoá/mở và xử lý yêu cầu trên trang quản lý đại lý: chưa bấm thử bằng
  phiên admin thật.

Ảnh: (1) màn hình chính của đại lý thử nghiệm trên máy tính, (2) trên điện thoại, (3) trang quản lý đại lý cho nhân viên
AA.

### Ảnh đính kèm

1. `docs/audits/2026-10-24-S249-aa935-signin/03-home-1440-light.png` → `crm-man-hinh-chinh-may-tinh.png`
2. `docs/audits/2026-10-24-S249-aa935-signin/06-home-390-light.png` → `crm-man-hinh-chinh-dien-thoai.png`
3. `docs/audits/2026-10-24-S250-aa941-ui/10-admin-agencies-drawer-nghiep.png` → `quan-ly-dai-ly-cho-AA.png` —
   **Nghiệp xem lại trước khi đính** (chụp từ phiên admin của Nghiệp, có thể lộ email/tên).

### Câu → bằng chứng (nội bộ)

| Câu | Bằng chứng |
|---|---|
| Đăng nhập 2 lớp, mời → dùng được ~10 s | AA-939 (export S249) — E2E Dev run 40076211334; `docs/audits/2026-10-24-S249-aa935-signin/README.md` |
| Form → thẻ → hồ sơ ~22 s | AA-936 — E2E Dev run 40063125699 (22,4 s) |
| 9 bước, phiếu 80%, giờ gọi, hoàn tác, chuyển nhiều thẻ | AA-943 — Partner E2E Dev run 40133393046 |
| Sổ dịch vụ / nhà cung cấp / tỷ giá | AA-944 — `crm_fx_fetch` tỷ giá giả, 21 tỷ giá, 0 lỗi; không có E2E UI |
| Nhật ký xuất hằng giờ | AA-940 — 5 object mỗi tầng lúc 07:16 UTC 24/10 |
| Che PII 260 mẫu, 0 lọt, 3,98% | AA-938 phương án B — Scrub corpus run 40102237468 |
| Thùng rác / giữ pháp lý / xoá | AA-942 — chỉ CI, UI chưa kiểm live |
| Đồng bộ thành viên | AA-978 (S250) — `membership_feed: ok`, 0 sự kiện |
| Cảnh báo đồng bộ thành viên | Infra #390 merged 10:34Z + Terraform Apply run 40185381048 xanh; chưa thử alarm |
| Nội dung AA trong admin CIS | AA-977 — 28 mục (27 đăng, 1 nháp); seed viết tay |
| Trang quản lý đại lý | AA-941 — `docs/audits/2026-10-24-S250-aa941-ui/README.md` (reviewer bị chặn; admin thấy 3 đại lý; nút ghi chưa bấm) |
| Đề xuất → chấp nhận, lịch thanh toán, cọc → Đã đặt, cổng khách mã 6 số, Stage 3 sau cọc, ký v0 | AA-946: Partner #49 (crm-016, merged 08:44Z) + #50 (merged 10:36Z), Infra #384/#385; DB Migrate xanh; Deploy Dev run 40185480043 + Deploy Web Dev 40185480039 xanh; review `.tmp-session/s251/r1/review_crm18.json` (unit 1578, integration 389). **Không có E2E Dev / ảnh** → `[K3]` |
| Dòng AA chỉ từ Booking, không sửa tay (403), hàng đợi khi Booking không trả lời, giá "từ" | AA-947: Partner #55 (merged 11:01Z) + #56, Infra #391/#392; Deploy Dev run 40187150782 xanh; PR #55 body (integration 417, unit 1618). **Không có E2E Dev / ảnh** → `[K3]` |
| "Trợ lý AI không tự xác nhận booking AA" | Chỉ từ bản tóm tắt S251 của phiên điều phối (PR #55 ghi: sửa/gõ tay dòng AA → 403 `aa_line_read_only`); không có file riêng |
| Email: mã chuyến gắn đúng chuyến; mã sai → Chưa gắn chuyến; địa chỉ lạ bị bỏ, chỉ đếm; PDF lưu, .txt bị từ chối | `.tmp-session/s251/aa945/EVIDENCE.md` (kiểm (2) PASS, đối chứng âm PASS); `.tmp-session/s251/aa945/card_e-pass-0717Z.log` (`match_method trip_token` 07:17Z; PDF lưu, `type_not_allowed`); `docs/audits/2026-10-25-S250-wrap/AA-945-live.md`; Linear AA-945 comment S250 |
| Chưa thử OAuth / SMTP / nhập lịch sử / ảnh Messages | `.tmp-session/s251/aa945/EVIDENCE.md` (bảng trạng thái) |

**Evidence/links:** `docs/audits/2026-10-24-S249-aa935-signin/` (ảnh 03, 06), `docs/audits/2026-10-24-S250-aa941-ui/`
(ảnh 10), `docs/audits/2026-10-25-S250-wrap/AA-945-live.md`, `docs/audits/2026-10-22-S247-crm-readiness/`; ngoài
docs/audits: `.tmp-session/s251/aa945/EVIDENCE.md` + `card_e-pass-0717Z.log` (có account ID và tenant id — chép vào
docs/audits thì phải che trước, repo gốc public).

---

## PR-25 — Booking — Hệ thống đặt tour (trip case, báo giá, thanh toán)

**Vì sao chọn:** comment gần nhất (23/10) báo phần bán cho đại lý (B2B) và hỏi chị chốt phí huỷ, gia hạn giữ chỗ, giới
hạn giữ lại, khoá kết nối riêng. Chưa có trả lời — nháp này **không hỏi lại**, chỉ báo phần mới.

### Nội dung comment (sẵn để đăng)

@thule Dạ chị, cập nhật Booking (số liệu ngày 25/10/2026):

- **Luồng sự kiện cho đại lý:** hệ thống của đại lý nhận danh sách thay đổi về báo giá, giữ chỗ, gia hạn, huỷ… theo thứ
  tự, đọc lại nhiều lần không bị trùng. Luồng không chứa thông tin cá nhân của khách, và đại lý này không đọc được sự kiện
  của đại lý khác. Đã thử trên Dev với một đại lý thử nghiệm. CRM của đại lý giờ dùng chính luồng này để lấy giá và giữ chỗ
  tour AA (xem cập nhật CRM).
- **Bàn xử lý yêu cầu "on-request"** cho nhân viên: nhận hoặc từ chối yêu cầu của đại lý, có nhãn hạn trả lời.
- **Cờ sự cố cho chuyến khởi hành:** nhân viên đánh dấu một chuyến có sự cố, các đại lý liên quan nhận được thông báo
  (không kèm thông tin khách).
- **Giao diện ở màn hình 1440 px:** các bảng (hồ sơ chuyến, khách hàng, đề xuất, khách sạn, dịch vụ, nhà cung cấp, nhật ký,
  tỷ giá…) vừa khung, không phải kéo ngang. Đã kiểm trên bản đang chạy với dữ liệu của Dev: 25 trang, mỗi trang ở 1440 px
  nền sáng và nền tối, 1280 px và điện thoại; 100/100 lần mở không tràn ngang, không lỗi.
- **Tự dọn dữ liệu cũ đã chạy thật trên Dev:** việc nền cũ được lưu sang kho lưu trữ trước rồi mới xoá; thông tin cá nhân
  (tên, email, số điện thoại) trong các yêu cầu gốc cũ được xoá. Lần chạy ngày 25/10: lưu trữ rồi xoá 17 việc nền cũ, xoá
  thông tin cá nhân của 5 yêu cầu gốc; kiểm lại không còn dòng quá hạn nào sót. Vì dữ liệu Dev còn mới (chưa tới 90 ngày),
  lần chạy này dùng mốc thời gian ngắn hơn, chỉ bật được trên Dev; trên môi trường thật vẫn là 90 ngày.

Chưa thử thật trên Dev: bàn xử lý "on-request" và nút cờ sự cố mới kiểm trong bộ kiểm thử phần mềm, chưa bấm thử bằng phiên
đăng nhập nhân viên.

Đang làm: nội dung khách sạn và dịch vụ của Booking đi qua CIS để viết và duyệt (trang xem nội dung này đã có trong admin
CIS; chưa chạy thử phần viết).

Ảnh: (1) danh sách hồ sơ chuyến ở 1440 px, (2) bảng đề xuất ở 1440 px nền tối, (3) danh sách nhà cung cấp ở 1440 px.

### Ảnh đính kèm

1. `docs/audits/2026-10-24-S250-aa910-live/cases-1440-light.png` → `booking-ho-so-chuyen-1440.png`
2. `docs/audits/2026-10-24-S250-aa910-live/proposals-1440-dark.png` → `booking-de-xuat-1440-nen-toi.png`
3. `docs/audits/2026-10-24-S250-aa910-live/suppliers-1440-light.png` → `booking-nha-cung-cap-1440.png`
   — Nghiệp xem lại ảnh trước khi đính (dữ liệu Dev).

### Câu → bằng chứng (nội bộ)

| Câu | Bằng chứng |
|---|---|
| Luồng sự kiện B2B | AA-975 (export S249): `/b2b/v1/events` 200, không token 401, tenant khác 403; quote → hold → extend → 1 `hold.extended`; không key PII |
| CRM dùng luồng này | Partner #55 (CRM-19, `booking.b2b.v1`) — xem `[K3]` |
| Bàn on-request, cờ sự cố | AA-975 — chỉ CI (348 test xanh) |
| 1440 px, 100/100 | AA-910 — `docs/audits/2026-10-24-S250-aa910-live/` (README, result.json) |
| Dọn dữ liệu: 17 xoá (lưu trữ trước), 5 xoá PII, kiểm 0 sót, mốc ngắn chỉ Dev | Linear AA-825 comment Done 25/10 10:19Z (Booking #91 → `aa-booking-dev-api:58`, Infra #386 apply run 40178214300; DRY RUN 14+3 / 5 → LIVE 17 / 5; 2 object `archive/booking/job/2026/10/…jsonl.gz`); `.tmp-session/s251/aa825/EVIDENCE.md` |
| Nội dung khách sạn/dịch vụ qua CIS | AA-835 In Progress; CIS #991 (consumer) + #1006 (trang admin, Vercel deploy run 40187159038); `.tmp-session/s251/ui-cis/README.md` (trang supply-content chưa mở được bằng phiên đăng nhập) |

**Evidence/links:** `docs/audits/2026-10-24-S250-aa910-live/` (3 ảnh), `docs/audits/2026-10-25-S250-wrap/`; ngoài
docs/audits: `.tmp-session/s251/aa825/EVIDENCE.md`, `.tmp-session/s251/ui-cis/README.md`.

---

## PR-24 — TripPlanner — Lên lịch trình trên bản đồ (khách B2C)

**Vì sao chọn:** comment gần nhất (23/10) nói tour bị gỡ biến khỏi TripPlanner "trong vòng tối đa 30 phút". S249 rút
xuống vài giây; S250 thêm đăng nhập cho khách + "Chuyến đi của tôi"; S251 sửa nút đăng xuất khi trang lỗi.

### Nội dung comment (sẵn để đăng)

@thule Dạ chị, cập nhật TripPlanner (số liệu ngày 25/10/2026):

- **Tour bị gỡ biến mất trong vài giây:** khi AA ngừng phục vụ một tour, TripPlanner được báo ngay. Thử trên Dev: trang tour
  báo "không còn" sau 8 giây (trước đây tới 30 phút). Khi phục vụ lại, tour hiện lại sau 24 giây.
- **Khách đăng nhập bằng mã gửi qua email**, không cần mật khẩu: nhập email, nhập mã nhận được là vào. Lần đầu dùng email
  mới thì tài khoản được tạo luôn.
- **"Chuyến đi của tôi" (My Trips):** chuyến khách lập khi chưa đăng nhập tự gắn vào tài khoản sau khi đăng nhập. Khách
  đăng nhập trên máy khác vẫn thấy và mở được chuyến đó. Khách khác không thấy chuyến của nhau. Nhập sai mã thì báo lỗi và
  không vào được.
- Đã kiểm trên bản đang chạy (tripplanner.lumiguides.it.com) với 2 tài khoản khách thử nghiệm, trên máy tính và điện thoại:
  các bước trên đều đạt, không có lỗi.
- Nút đăng xuất giờ hiện cả khi trang "Chuyến đi của tôi" không tải được (đã lên, chưa chụp ảnh).
- Trang đăng nhập đã bật tường lửa để chặn truy cập bất thường (chưa thử tấn công giả lập).
- Sau lần viết lại nội dung tour (xem cập nhật CIS), đường dẫn cũ của tour tự chuyển sang đường dẫn mới, nên link cũ khách đã
  lưu hay chia sẻ không bị hỏng.

Chưa thử thật: gửi chuyến cho tư vấn viên khi khách đã đăng nhập (email đã xác minh đi kèm sang Booking), mới kiểm trong bộ
kiểm thử phần mềm. Chưa làm: đăng nhập bằng Google/Facebook cho khách.

Ảnh: (1) trang đăng nhập bằng email, (2) "Chuyến đi của tôi" sau khi đăng nhập, (3) mở lại chuyến trên máy khác (điện
thoại), (4) báo lỗi khi nhập sai mã.

### Ảnh đính kèm

1. `docs/audits/2026-10-25-S250-aa908-live/02a-sign-in-email-1440.png` → `tripplanner-dang-nhap-email.png`
2. `docs/audits/2026-10-25-S250-aa908-live/r03-my-trips-after-sign-in-1440.png` → `tripplanner-chuyen-di-cua-toi.png`
3. `docs/audits/2026-10-25-S250-aa908-live/r05b-second-device-opens-trip-390.png` → `tripplanner-mo-tren-may-khac.png`
4. `docs/audits/2026-10-25-S250-aa908-live/06-wrong-code-1440.png` → `tripplanner-sai-ma.png`
   — Nghiệp xem lại email thử nghiệm hiện trên ảnh trước khi đính.

### Câu → bằng chứng (nội bộ)

| Câu | Bằng chứng |
|---|---|
| 8 s / 24 s | AA-987 (S249) — log S249, mục Bằng chứng |
| Đăng nhập mã email, My Trips, máy khác, sai mã | AA-908 — `docs/audits/2026-10-25-S250-aa908-live/README.md` (re-check sau Infra #381 PASS, `results-recheck-381.json`) |
| Nút đăng xuất khi lỗi | TP #149 merged 08:08Z (9443a343); không có ảnh live |
| Tường lửa | Infra #360 / #374 (đã apply); không có kiểm tấn công giả lập |
| Đường dẫn cũ → mới | AA-645 (xem PR-22) |
| email_verified sang Booking | chỉ CI; `.tmp-session/S251-checklist.md` mục 19 (còn thiếu bằng chứng live) |

**Evidence/links:** `docs/audits/2026-10-25-S250-aa908-live/` (4 ảnh + README), log S249
`docs/sessions/2026-10-24-S249-crm-w1-w2-s1-catalogue-rewrite.md`.

---

## PR-27 — Nền tảng — Đăng nhập, bảo mật, hạ tầng (dùng chung các app)

**Vì sao chọn:** epic nền tảng; comment gần nhất (23/10) về quét lộ khoá, xoá dữ liệu theo yêu cầu, tên nội bộ cố định cho
cơ sở dữ liệu ("khi cần khôi phục chỉ đổi một chỗ"). S249 diễn tập đúng việc đó; S250–S251 thêm các phần dưới.

### Nội dung comment (sẵn để đăng)

@thule Dạ chị, cập nhật nền tảng (số liệu ngày 25/10/2026):

- **Diễn tập khôi phục cơ sở dữ liệu:** tạo bản khôi phục về một thời điểm trước khi dữ liệu bị xoá thử. Bản khôi phục sẵn
  sàng sau 21 phút 20 giây (mục tiêu dưới 1 giờ). So sánh đủ 164/164 bảng; phần dữ liệu bị xoá thử được lấy lại đúng. Đã
  chuyển các ứng dụng sang bản khôi phục rồi chuyển về, chỉ đổi một chỗ; mọi dịch vụ chạy lại bình thường. Chi phí diễn tập
  dưới 1 USD.
- **Bộ nhớ đệm được mã hoá:** bộ nhớ đệm dùng chung của CIS chuyển sang bản mới, mã hoá cả khi lưu và khi truyền, có mật
  khẩu truy cập. Dữ liệu chuyển đầy đủ, ứng dụng chạy bình thường, bản cũ chưa mã hoá đã gỡ. Chi phí giảm khoảng
  2,8 USD/tháng.
- **Cảnh báo khi đọc cài đặt của tenant bị lỗi:** đã thử bằng một lỗi giả: email cảnh báo gửi tới, và email "đã ổn" gửi tới
  khi hết lỗi.
- **Báo lỗi tự động không còn gửi kèm thông tin đăng nhập hay email:** báo cáo lỗi gửi lên hệ thống theo dõi lỗi đã được che
  mã đăng nhập của nhân viên và email. Booking, CRM và TripPlanner đã được kiểm, vốn đã an toàn.
- **Đổi mật khẩu DataForSEO** (dịch vụ dữ liệu từ khoá SEO) và kiểm lại: kết nối chạy bình thường.
- **Cảnh báo "lộ khoá" giả:** công cụ quét của GitHub báo 96 khoá Google "bị lộ" (16 ở mỗi kho code trong 6 kho). Đã kiểm:
  đây là các khoá mẫu nằm sẵn trong file cấu hình của chính công cụ quét, không phải khoá thật của AA. Đã sửa cách ghi file
  đó để không bị báo nữa. `[K1]`
  - *Nếu đã đóng hết:* "Cả 96 cảnh báo đã đóng."
  - *Nếu CIS chưa xong:* "80/96 cảnh báo đã đóng; 16 cảnh báo còn lại ở kho CIS sẽ đóng khi bản sửa được đưa lên."
- **Lỗi bảo mật do công cụ quét mã tìm ra:** `[K2]`
  - *Nếu CIS #1011 đã lên:* "Đã sửa 7 lỗi (chủ yếu là các mẫu tìm chữ có thể bị làm chậm cố ý), ở CIS và TripPlanner."
  - *Nếu chưa:* "Đã sửa 2 lỗi ở CIS và TripPlanner; 5 lỗi cùng loại còn lại ở CIS đã có bản sửa, đang chờ đưa lên."
- **Báo cáo đối chiếu cấu trúc cơ sở dữ liệu:** báo cáo hằng đêm so sánh cơ sở dữ liệu thật với các thay đổi đã ghi nhận đã
  được sửa: những phần trước đây được tạo tay nay đã có bản ghi chính thức, nên báo cáo ra được kết luận "không lệch" khi mọi
  thứ khớp, và chỉ báo khi có lệch thật.
- **Tường lửa cho các trang đăng nhập** (nhân viên, khách TripPlanner, đại lý): đã bật.

Chưa thử thật trên Dev: phần che thông tin trong báo lỗi mới kiểm bằng bộ kiểm thử phần mềm, chưa tạo một lỗi thật trên Dev
để xem báo cáo. Tường lửa đăng nhập mới bật cấu hình, chưa thử tấn công giả lập.

### Câu → bằng chứng (nội bộ)

| Câu | Bằng chứng |
|---|---|
| Diễn tập khôi phục | AA-829 (S249) — `docs/audits/2026-10-24-S249-restore-drill/README.md`, `compare-run-39991070753.txt` |
| Bộ nhớ đệm mã hoá, −$2,8/tháng | AA-874 (S250) — comment Linear; Infra #372/#373 |
| Cảnh báo cài đặt tenant | AA-874 — alarm test ALARM 03:59:44Z → OK 04:14:44Z (email cả hai) |
| Che token/email trong Sentry | CIS #979 (S249) — chỉ test, không kiểm live |
| DataForSEO | bản tóm tắt S251; `.tmp-session/s251/dfs-out.json` (`/admin/dfs-balance/check` ok 200) |
| 96 cảnh báo giả | `.tmp-session/S251-lessons-pending.md` (16 khoá mẫu × 6 repo, cấu hình mặc định gitleaks); fix: Partner #57, Booking #93, Infra #393, TP #151, root #260 merged; CIS #1010 **mở** (gitleaks đỏ vì thiếu nhãn). `gh api` 11:48Z: 5 repo 0 mở / 16 đóng hôm nay; CIS 16 mở → `[K1]` |
| Lỗi quét mã | TP #152 merged (1 fixed), CIS #1001 merged (1 fixed); CIS #1011 **mở** (5 ReDoS + 1 trang 404); `gh api` 11:48Z: CIS 6 mở → `[K2]` |
| Báo cáo đối chiếu cấu trúc | AA-853 Done 25/10 10:20Z; Infra #383/#387/#388 + CIS #1003 (mig 281) merged, DB Migrate xanh; `.tmp-session/s251/aa853/final2.json`; `docs/audits/2026-10-25-S250-wrap/AA-853-live.md` |
| Tường lửa | Infra #360 / #374 — không kiểm live |

**Evidence/links:** `docs/audits/2026-10-24-S249-restore-drill/`, `docs/audits/2026-10-25-S250-wrap/AA-853-live.md`;
ngoài docs/audits: `.tmp-session/s251/dfs-out.json`, `.tmp-session/s251/aa853/`, `.tmp-session/S251-lessons-pending.md`.
Không có ảnh.

---

## PR-23 — Portal tenant — Cổng cho đối tác

**Vì sao chọn:** (1) đề xuất điều khoản sử dụng AI cho tenant từ nháp S250 vẫn chưa đăng, chị chưa quyết; (2) S251 có trang
Tài khoản mới trên portal. Đề xuất viết nhẹ nhàng, có phương án; có cần luật sư hay không là chị quyết (memory
`tech-focus-business-to-thu`). Đã bỏ câu "cần chị chọn trước ngày 11/11" của nháp S250 cho đỡ áp lực; chỉ nêu ngày hiệu
lực như một dữ kiện.

### Nội dung comment (sẵn để đăng)

@thule Dạ chị, cập nhật portal tenant (số liệu ngày 25/10/2026):

**Tính năng mới**
- **Trang Tài khoản** trên portal dùng dữ liệu thật: mục Thanh toán có đồng hồ số lần viết lại đã dùng so với hạn mức, ngày
  làm mới và phần vượt hạn mức; mục Hoạt động liệt kê các thao tác của tenant, lọc theo loại và ngày, xuất file CSV; mục Kết
  nối có trạng thái từng kênh đăng bài và thông tin khoá API (khoá được che, ngày cấp, lần dùng gần nhất, nút xin khoá mới
  qua email AA). Đã lên portal ngày 25/10; chưa chụp ảnh bằng phiên đăng nhập tenant thật, em gửi ảnh ở lần cập nhật sau.
  `[K4]`
- Công cụ nội dung trên portal đã chuyển về cùng ứng dụng với CRM ở phía sau. Tenant không thấy gì thay đổi: địa chỉ portal,
  trang đăng nhập và trang điều khoản vẫn mở bình thường.

**Đề xuất về điều khoản sử dụng AI cho tenant**

Bối cảnh: chính sách sử dụng mới của Anthropic (hãng làm ra Claude, mô hình AI viết nội dung cho tenant qua Amazon) có hiệu
lực từ 12/11/2026 và áp dụng cả cho đối tác dùng nội dung viết bằng Claude. Em đã đọc lại bản chính sách đang đăng ngày
24/10: ngày hiệu lực không đổi.

Đã làm:
- Bản nháp điều khoản AI đầy đủ đã cập nhật lên v0.2, khớp chính sách đang đăng, để đính kèm hợp đồng đối tác.
- Trang điều khoản của portal đã có mục 3 "AI-generated content and acceptable use": tóm tắt các việc cấm (đánh giá giả, lời
  chứng thực giả, nhân vật bịa, mạng tài khoản giả, che giấu tài trợ…), nhãn nội dung AI, tenant là người đăng và chịu trách
  nhiệm, AA có quyền giữ, viết lại hoặc từ chối nội dung. Trang vẫn ghi "Draft — pending legal review":
  https://portal.lumiguides.it.com/terms
- Hiện chưa có tenant thật hay tenant trả tiền, nên chưa cần gửi thông báo cho ai. Mỗi tenant chấp nhận điều khoản này khi
  ký hợp đồng lúc bắt đầu dùng.
- CRM cho đại lý hiện chưa gọi Claude. Điều khoản này sẽ được đưa vào điều khoản của đại lý trước khi bật AI cho CRM.

Phương án:
- **A.** Dùng điều khoản như bản nháp: bản tóm tắt trên portal đã có trước 12/11, điều khoản đầy đủ đính kèm hợp đồng mỗi
  tenant lúc bắt đầu. Có nhờ luật sư xem hay không là chị quyết.
- **B.** Nhờ luật sư xem trước; trong lúc chờ, portal vẫn để bản tóm tắt ở dạng nháp.
- **C.** Dùng ngay như A, và nhờ luật sư xem trước khi có tenant trả tiền đầu tiên.

Đề xuất: A hoặc C. Vì chưa có tenant nào, dùng ngay không tốn gì và kịp ngày 12/11; C thêm một lần luật sư xem trước khi
tenant đầu tiên trả tiền.

Khi tiện chị chọn giúp em: A, B hay C; và có nhờ luật sư xem không. Nếu nhờ luật sư, bản nháp đã có sẵn danh sách câu hỏi
cho luật sư (ví dụ: nội dung tenant đăng dưới tên mình không có nhãn AI thì có ổn không; điều khoản ràng buộc tenant bằng
cách nào; luật áp dụng). Em gửi file khi chị cần.

### Câu → bằng chứng (nội bộ)

| Câu | Bằng chứng |
|---|---|
| Trang Tài khoản | AA-761 (In Progress): Partner #51 merged 11:43:52Z, Vercel Deploy (portal) run 40190089738 xanh; CIS #1002 merged 10:50Z, Deploy Dev xanh (run 40188717778 là bản deploy sau đó). Smoke spec mới `e2e/smoke-portal/aa761-account-pages.spec.ts` (dữ liệu mock). **Không có ảnh phiên tenant thật** → `[K4]` |
| Portal chuyển sang AA-Partner | AA-979 (In Progress, P2b còn): Partner #44/#46/#48, CIS #997/#1000, root #253; S250: production deploy run 40156305885, `/tenant-login` + `/terms` 200 |
| Điều khoản AI | AA-820: root #240 (`docs/legal/tenant-terms-ai-clause-draft.md` v0.2), CIS #981 `/terms` §3; phương án A/B/C `docs/legal/readiness-packet.md` §12 |

Không đưa vào (chưa ship): **bảng "My Content"** (Partner #53 còn mở; phần CIS #1007 đã lên nhưng giao diện chưa) và **tab
Thành viên** (Partner #54 còn mở; phần CIS #1008 đã lên). Báo khi giao diện lên và có ảnh.

**Evidence/links:** `docs/legal/tenant-terms-ai-clause-draft.md`, `docs/legal/readiness-packet.md`,
`docs/audits/2026-10-21-S246-legal-packet/`; không có ảnh trang Tài khoản.

---

## PR-20 — Báo cáo nền tảng tuần (STORY MỚI dưới epic PR-20)

**Vì sao:** báo cáo tuần (memory `platform-report-weekly`); kỳ trước là PR-21 (01–19/10, tạo 19/10). Kỳ này 20–26/10
(S245–S251). **Cần tạo một story mới** dưới PR-20 — chỉ tạo khi Nghiệp duyệt (skill: không tự tạo issue Jira).
Tiêu đề đề xuất: **"Báo cáo nền tảng kỳ 2 — tuần 20–26/10/2026"**. Nội dung đặt ở phần mô tả story, theo khung PR-21
(theo app: đã xong / tiếp theo / rủi ro / chi phí). Việc 20–23/10 đã báo chi tiết trên các epic ngày 22–23/10, nên ở đây chỉ
tóm một dòng và trỏ tới epic. Thay "PR-xx" bằng link Jira khi đăng.

### Nội dung story (sẵn để đăng)

@thule Dạ chị, báo cáo nền tảng kỳ 2 (tuần 20–26/10/2026), số liệu lấy ngày 25/10/2026. Chi tiết từng phần nằm ở comment
mới trên các epic theo app.

**1. CIS — Nội dung & pipeline** (PR-22)
- Đã xong:
  - Viết lại toàn bộ nội dung Master bằng bộ viết mới: 810/810 tour, tất cả lên Master, 0 tour chờ duyệt, 0 tour giữ bản cũ;
    tour có cờ kiểm tự động 312 → 36; giữ số liệu của tour gốc nhiều hơn (khoảng 42% → 67%). Đường dẫn cũ tự chuyển sang
    đường dẫn mới. 39 tour cưỡi voi giữ nguyên bản cũ theo hướng chị chọn.
  - 20–23/10 (phần lớn đã báo trên các epic ngày 22–23/10): bộ 100 mẫu chuẩn để đo chất lượng viết; chọn bộ viết mới qua thử nghiệm; tour
    bị xoá ở nguồn tự ẩn ở mọi ứng dụng và hiện lại khi khôi phục, có kiểm tra hằng đêm.
- Tiếp theo: cho các phần dùng lại nội dung tour (tuyến gợi ý, xếp hạng, địa điểm, tìm kiếm, TripPlanner, CRM, Booking, SEO)
  đi theo nội dung mới, kèm phép kiểm tự động độ mới.

**2. Portal tenant** (PR-23)
- Đã xong: trang Tài khoản dùng dữ liệu thật (thanh toán và hạn mức, nhật ký hoạt động + xuất CSV, kết nối và khoá API);
  công cụ nội dung chuyển về cùng ứng dụng với CRM ở phía sau, tenant không thấy thay đổi.
- Tiếp theo: bảng "Nội dung của tôi" dạng bảng có lọc/sắp xếp, tab Thành viên; ảnh các trang mới.
- Cần chị chọn: phương án điều khoản sử dụng AI cho tenant (chi tiết ở PR-23).

**3. TripPlanner** (PR-24)
- Đã xong: tour bị gỡ biến mất sau vài giây (trước đây tới 30 phút); khách đăng nhập bằng mã email và có "Chuyến đi của tôi",
  mở được trên máy khác; đường dẫn tour cũ tự chuyển sang đường dẫn mới.
- Tiếp theo: kiểm thật việc gửi chuyến cho tư vấn viên khi khách đã đăng nhập.

**4. Booking** (PR-25)
- Đã xong: luồng sự kiện cho đại lý (báo giá, giữ chỗ, gia hạn, huỷ); bàn xử lý yêu cầu on-request; cờ sự cố cho chuyến khởi
  hành; giao diện 1440 px không tràn (100/100 lần mở); tự dọn dữ liệu cũ đã chạy thật một lần trên Dev (lưu trữ trước khi
  xoá).
- Tiếp theo: nội dung khách sạn và dịch vụ đi qua CIS để viết và duyệt.
- Đang chờ chị: phí huỷ, gia hạn giữ chỗ, giới hạn giữ lại, khoá kết nối riêng cho đại lý (câu hỏi ở PR-25 ngày 23/10).

**5. CRM cho đại lý** (PR-26)
- Đã xong trên Dev: đăng nhập 2 lớp và mời thành viên; nhận khách → bảng theo dõi 9 bước; sổ dịch vụ, nhà cung cấp, tỷ giá;
  nhật ký không sửa được, che thông tin cá nhân trước khi gửi AI (0 lọt / 260 mẫu); nội dung AA dùng chung; trang quản lý đại
  lý cho AA; đề xuất → khách chấp nhận → nhận cọc → "Đã đặt" → cổng khách bằng mã một lần → ký điện tử bản đầu; tour AA trong
  chuyến lấy giá và giữ chỗ từ Booking, đại lý không sửa tay; email chuyển tiếp gắn đúng chuyến (đã thử thật).
- Tiếp theo: thử trọn một chuyến bằng phiên đăng nhập thật và chụp ảnh; kết nối Gmail/Microsoft 365 để gửi thư bằng địa chỉ
  của đại lý (cần một người đăng nhập tài khoản thật).

**6. Nền tảng — đăng nhập, bảo mật, hạ tầng** (PR-27)
- Đã xong:
  - Diễn tập khôi phục cơ sở dữ liệu: sẵn sàng sau 21 phút 20 giây, 164/164 bảng khớp, chuyển qua lại chỉ đổi một chỗ.
  - Bộ nhớ đệm của CIS được mã hoá, có mật khẩu; bản cũ đã gỡ (rẻ hơn khoảng 2,8 USD/tháng).
  - Đổi mật khẩu DataForSEO; kiểm lại chạy bình thường.
  - Cảnh báo "lộ khoá" giả (khoá mẫu của chính công cụ quét) đã giải thích và xử lý `[K1]`; sửa lỗi do công cụ quét mã tìm
    ra `[K2]`.
  - Báo lỗi tự động không còn kèm mã đăng nhập hay email; cảnh báo khi đọc cài đặt tenant bị lỗi (đã thử bằng lỗi giả);
    tường lửa cho các trang đăng nhập; báo cáo đối chiếu cấu trúc cơ sở dữ liệu hằng đêm đã sửa để ra kết luận đúng.
  - 20–23/10 (đã báo ở PR-27 ngày 23/10): quét lộ khoá tự động trên cả 6 kho code; diễn tập xoá dữ liệu theo yêu cầu; một
    tên nội bộ cố định cho cơ sở dữ liệu để khi khôi phục chỉ đổi một chỗ.
  - Quy trình làm việc của trợ lý AI viết code được cập nhật theo tài khoản Claude mới.
- Tiếp theo: thử tấn công giả lập cho tường lửa đăng nhập; tạo một lỗi thật trên Dev để xem báo cáo lỗi đã che đúng.

**7. Chi phí**
- Viết lại toàn bộ nội dung tour: 59,34 USD cho 810 tour (trần 120 USD), khoảng 0,07 USD mỗi tour.
- Tài khoản AWS dùng cho AI đã báo chạm mốc cảnh báo ngân sách tháng 10: 201,69 / 250 USD, chủ yếu do lần viết lại toàn
  catalogue. Dự kiến cả tháng 10 khoảng 215–225 USD, vẫn dưới 250 USD.
- Bộ nhớ đệm mới rẻ hơn khoảng 2,8 USD/tháng; diễn tập khôi phục dưới 1 USD.
- Số liệu chi phí đầy đủ theo từng ứng dụng sẽ có sau đợt rà soát chi phí tháng (đầu tháng 11), như đã ghi ở kỳ 1.

**8. Rủi ro / sự cố trong kỳ**
- Không có sự cố ảnh hưởng người dùng. Hệ thống vẫn ở môi trường thử nghiệm, chỉ có dữ liệu thử.
- Ngân sách AI tháng 10 đã dùng khoảng 80%; lần viết lại lớn đã xong nên phần còn lại của tháng dự kiến thấp.
- Một số tính năng mới đã lên nhưng chưa thử trọn vòng bằng phiên đăng nhập thật (ghi rõ ở từng epic); em sẽ thử và gửi ảnh
  ở kỳ sau.

### Câu → bằng chứng (nội bộ)

| Câu | Bằng chứng |
|---|---|
| Mục 1–6 | như các nháp PR-22…PR-27 ở trên |
| 20–23/10 (S245–S248) | `docs/sessions/README.md` dòng S245–S248; epic PR-22…PR-27 comment 22–23/10 (đã đăng) |
| Quy trình AI theo tài khoản Claude mới | root #257 ("S251 skill review for the new claude.ai account"), #259 |
| $59,34/$120 | AA-645 comment Done |
| 201,69/250 USD, dự kiến 215–225 USD | **chỉ có trong bản tóm tắt S251 của phiên điều phối**; không tìm thấy file số liệu (`.tmp-session/s251/l1/cost_oct.py` có, không có output) |
| −2,8 USD/tháng, diễn tập < 1 USD | AA-874 (S250), AA-829 (S249) |

**Evidence/links:** các file đã liệt kê ở từng epic; `docs/sessions/README.md`; ngân sách AWS: chưa có file trong
docs/audits (nên lưu ảnh màn hình Budgets hoặc output Cost Explorer vào `docs/audits/2026-10-25-S251-wrap/` trước khi đăng).

---

## Các issue còn lại — không có cập nhật mới (không soạn)

| Issue | Lý do |
|---|---|
| PR-19 (CRM cho travel agencies — yêu cầu gốc) | Gộp vào epic PR-26 như comment 23/10. Nếu muốn chị thấy ở PR-19, đăng 1 dòng trỏ sang PR-26. |
| PR-13 (Jev — lớp kiểm chứng) | Không có thay đổi thiết kế; "Jev chạy cho 100% tour" đã nằm trong PR-22. |
| PR-15 (dữ liệu tour thô trước khi chạy lại) | Không có cập nhật; kết quả viết lại báo ở PR-22. |
| PR-16 (gpt-4.0-mini → gpt-6-luna) | Không có thay đổi tuần này. |
| PR-17 (tenant viết lại đúng giọng thương hiệu) | Các cổng chất lượng viết cho tenant đang làm (mới có phần hiển thị trong admin CIS cho nhân viên AA); chưa có gì tenant thấy → báo khi xong. |
| PR-18 (quản lý tenant) | Tab Thành viên của portal chưa lên (Partner #54 mở) → báo khi xong. |
| PR-14 (đăng nhập không mật khẩu cho Admin + Tenant) | Không có thay đổi đúng phạm vi; đăng nhập bằng mã email cho khách TripPlanner nằm ở PR-24. |
| PR-11 (Visual map planner), PR-12 (Booking system) | Issue cũ; cập nhật chuyển sang PR-24, PR-25 từ 23/10. |
| PR-1, PR-7, PR-9 (đăng bài, mạng xã hội, upload nội dung) | Không có thay đổi tuần này. |
| PR-21 (báo cáo kỳ 1), PR-6, PR-10 (biên bản họp) | Không cập nhật; kỳ 2 là story mới ở trên. |
| KAN-90 (DataForSEO tốn nhiều) | Không có thay đổi về chi phí DataForSEO (lần viết lại dùng 0 USD DataForSEO); việc đổi mật khẩu DataForSEO báo ở PR-27. |
| KAN-86 (B2B Infrastructure), KAN-20 (Asian Trails) | Phần B2B mới báo ở PR-25 / PR-26; không có cập nhật riêng. |
| KAN còn lại (KAN-1…KAN-93: marketing, WTM/ITB, nội dung theo nước, ảnh, nghiên cứu nhà cung cấp, việc của Trang/chị Thư/Leigh) | Việc nghiệp vụ/nội dung của đội AA, không có việc kỹ thuật tương ứng trong S249–S251. |
| CON-1…CON-39 (nội dung theo nước: Raw / Edited / PHOTOS / On web) | Việc biên tập của đội nội dung. Nội dung Master các nước đã viết lại (PR-22) nhưng không đổi trạng thái các thẻ CON; giữ một nơi báo là PR-22. |

## Không đưa vào (nội bộ hoặc chưa ship)

- Chưa ship: bảng My Content (Partner #53), tab Thành viên (Partner #54), đợt sửa lỗi quét mã CIS #1011 và cảnh báo CIS
  #1010 (xem `[K1]`/`[K2]`), dọn hộp sự kiện thành viên CRM (crm-018, Infra #389 mở), thử nghiệm cổng chất lượng viết cho
  tenant có trả phí (AA-926/924/916/790/917/918 — chưa chạy), nội dung khách sạn/dịch vụ Booking → CIS (AA-835 — chưa chạy
  phần viết), phần còn lại của việc chuyển portal (AA-979 P2b).
- Nội bộ / đã tự xử lý: squash Infra #380 xoá ngược một số thay đổi trên main (khôi phục đầu S251, live không ảnh hưởng);
  Sentry báo 401 DataForSEO trong lúc chờ deploy sau khi đổi mật khẩu; các trang admin CIS mới cho nhân viên (huy hiệu mức
  độ lỗi, nút lý do một chạm — chỉ admin, chưa có ảnh); bài học phiên.
