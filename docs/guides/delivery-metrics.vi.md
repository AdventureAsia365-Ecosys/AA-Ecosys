---
id: GUIDE-12-delivery
title: Hướng dẫn chỉ số phát hành
description: Cách đọc trang CIS admin Platform › Delivery và các báo cáo DEV-01 / DEV-03 - năm chỉ số DORA, các khúc lead time và sức khoẻ CI theo app, hàng merge và bản đồ git, mỗi con số được định nghĩa thế nào trong hệ sinh thái này, và làm gì khi một con số thay đổi.
type: how-to
status: draft
owner: nghiep
audience: [engineer, devops, agent, cto]
applies_to: [aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-11-18
review_every_days: 90
related: [GUIDE-12, GUIDE-12-cis-admin, GUIDE-14-metrics, AA-1108, AA-1125, AA-1135]
lang: vi
translation_of: docs/guides/delivery-metrics.md
---

# Hướng dẫn chỉ số phát hành

Thuộc bộ [truy cập và vận hành app](app-access-and-operations.md). Bản tiếng Anh của trang này là
[delivery-metrics.md](delivery-metrics.md). Mẫu báo cáo trong kit dự án dùng cùng định nghĩa là
[báo cáo chỉ số giao hàng](../templates/delivery-metrics-report.md).

## 1. Trang trả lời câu hỏi gì

Mỗi con số trên Platform › Delivery gắn với một quyết định. Con số nào không đổi được quyết định nào thì không có trên
trang.

| Câu hỏi | Quyết định đi kèm |
|---|---|
| Mỗi app ra bản nhanh tới đâu, có đều không? | App nào cần chú ý; có cần chia pull request nhỏ hơn không |
| Một thay đổi mất bao lâu từ pull request tới Dev, và chờ ở đâu? | Tăng tốc CI, hàng merge hay khâu review |
| Bao nhiêu lần deploy hỏng, và sửa mất bao lâu? | Thêm test hay guard ở đâu; rollback có cần nhanh hơn không |
| CI có ổn định không, có tốn thời gian vô ích không? | Sửa test chập chờn, chia job chậm, thêm cache |
| Các tool ship của agent có làm chậm hay làm hỏng việc phát hành không? | Sửa các tool `ship_*`, train hay một guard |

## 2. Số liệu lấy từ đâu

- Workflow **Delivery metrics** ở repo gốc (`.github/workflows/delivery-metrics.yml`) chạy mỗi giờ. Nó đọc sáu repo
  public bằng `GITHUB_TOKEN` của chính nó (không thêm secret nào): các lượt chạy workflow, job của chúng (mọi lần chạy
  lại), các pull request đã merge và các GitHub Deployment của môi trường `dev`; cho tab hàng merge và bản đồ git còn
  đọc timeline của từng pull request đã vào hàng merge và các commit của nhánh mặc định kèm file của chúng.
- Nó **lưu sự kiện thô trước** (mỗi ngày một file NDJSON, giữ 400 ngày) rồi mới tính chỉ số từ đó, nên khi đổi định
  nghĩa thì tính lại được trên lịch sử đã lưu. Tên trường theo OpenTelemetry semantic conventions cho CI/CD và VCS
  (`cicd.pipeline.*`, `vcs.change.*`, `deployment.*`).
- Nó đăng một bản tóm tắt cạnh bộ tài liệu của docs reader. API CIS đọc bản này (cache 5 phút), tô màu từng con số
  bằng các thiết lập của nhóm **delivery** trên Platform › Settings, rồi phục vụ trang. Các báo cáo **DEV-01** (hằng
  tháng) và **DEV-03** (hằng tuần) đọc cùng bản tóm tắt, nên trang và báo cáo luôn cùng số.
- Nút **Làm mới** trên trang đọc lại bản tóm tắt mới nhất đã đăng. Một lượt thu thập mới chạy vào mỗi giờ.
- Mọi con số là **số trên Dev**. Dev có ít sự kiện, nên mỗi chỉ số hiện cỡ mẫu **n** của nó; chỉ số có n dưới thiết
  lập "số sự kiện tối thiểu trước khi tô màu" thì giữ màu xám. Các dải DORA của ngành đo trên production: không so các
  số này với chúng như thể đây là số production.
- Lịch sử của một repo mới được lấp đầy qua vài lượt chạy hằng giờ (hạn mức gọi API dùng chung). Dòng "lịch sử đủ từ"
  trên mỗi app cho biết từ ngày nào số liệu bao phủ đủ.

## 3. Định nghĩa trong hệ sinh thái này

Đây là các định nghĩa đã được duyệt (tech lead, S282). Đây là phần quan trọng nhất: một con số tô màu đẹp mà định
nghĩa sai thì vô nghĩa.

- **Deploy.** Một lượt chạy của một trong các workflow deploy của app trên nhánh mặc định (push hoặc chạy tay) mà job
  deploy đã chạy. Danh sách workflow theo app nằm ở `tools/delivery/apps.json`. Các lượt chạy cùng một commit chồng
  nhau về thời gian là **một lần deploy của app** (CIS api + worker và admin, CRM api và web). Một lần deploy là
  **xanh** khi các job deploy và post-deploy verify đều đạt. Một lượt chạy sau của chính commit đang chạy là **deploy
  lại**: nó có thể là lần khôi phục của một lần deploy hỏng, nhưng không tính là một lần deploy mới.
- **Thay đổi.** Một pull request được squash-merge vào nhánh mặc định.
- **Deploy hỏng.** Một trong các trường hợp:
  - post-deploy verify đỏ;
  - một job deploy lỗi;
  - nó bị **rollback** (một lần deploy sau đưa lên commit cũ hơn);
  - pull request của nó bị **revert**, trong vòng 48 giờ;
  - một pull request có tiêu đề bắt đầu bằng `fix` nhắc tới pull request của nó và được merge trong vòng 48 giờ (một
    **hotfix**).
- **Khôi phục.** Từ lần deploy hỏng tới lần deploy xanh sửa nó: lần deploy xanh kế tiếp với verify đỏ hay job deploy
  lỗi, lần deploy rollback, hoặc lần deploy mang bản revert hay hotfix.
- **Làm lại (rework).** Một lần deploy mà chính nó là sửa chữa ngoài kế hoạch: một rollback, hoặc một lần deploy mang
  pull request revert hay hotfix.
- **Môi trường.** Là một chiều riêng ngay từ đầu: `dev` bây giờ, `prod` sau go-live. Prod sẽ thêm sự cố vào phần
  khôi phục.
- **Không tính vào lead time, đếm riêng.** Pull request của bot (release-please, các bot schema và docs, không phải
  App của agent) và pull request chỉ đổi tài liệu (`docs/**` hoặc Markdown) và không gây deploy.

## 4. Năm chỉ số DORA

DORA đã mở rộng từ bốn lên năm chỉ số: ba về tốc độ, hai về độ ổn định. Ngưỡng khởi đầu là dải "high" của DORA (tech
lead S282); mỗi ngưỡng là một thiết lập trên Platform › Settings › CIS › Chỉ số phát hành, do quản trị viên đổi kèm lý
do.

| Chỉ số | Định nghĩa | Xanh lúc đầu | Vàng lúc đầu | Nếu tệ đi |
|---|---|---|---|---|
| Tần suất deploy | Số lần deploy xanh mỗi tuần trong 4 tuần gần nhất | ít nhất 1 lần mỗi tuần | ít nhất 0,25 lần mỗi tuần | Thay đổi dồn lại: ra pull request nhỏ hơn, xem cái gì chặn deploy |
| Lead time cho thay đổi | Trung vị, từ lúc mở pull request tới post-deploy verify của lần deploy xanh đầu tiên chứa nó | 24 giờ trở xuống | 168 giờ trở xuống | Đọc biểu đồ các khúc (mục 5) và sửa khúc dài nhất |
| Tỉ lệ deploy hỏng | Số lần deploy hỏng / số lần deploy đã lên Dev | 15 % trở xuống | 30 % trở xuống | Xem lý do trong "Deploy hỏng": thêm test hay guard lẽ ra đã bắt được chúng |
| Thời gian khôi phục deploy hỏng | Trung vị, từ lần deploy hỏng tới lần deploy xanh sửa nó | 24 giờ trở xuống | 168 giờ trở xuống | Làm rollback nhanh hơn, hoặc sửa tiếp sớm hơn |
| Tỉ lệ làm lại | Số lần deploy rollback, revert và hotfix / số lần deploy đã lên Dev | 10 % trở xuống | 20 % trở xuống | Thời gian dành cho sửa nhiều hơn cho việc mới: chậm lại và ổn định hoá |

Thêm hai màu trên mỗi app:

- **CI p95 chậm nhất**: thời lượng p95 của workflow CI hay deploy chậm nhất của app; xanh khi 15 phút trở xuống, vàng
  khi 30 phút trở xuống.
- **Nhánh main**: xanh khi lượt CI và deploy mới nhất trên nhánh mặc định đều đạt; vàng khi có một lượt đỏ dưới 2
  giờ; đỏ sau đó. Main đỏ chặn mọi merge: sửa nó trước.

## 5. Các khúc lead time

Lead time được tách ở những điểm mà một thay đổi phải chờ, để biểu đồ cho thấy cần làm gì ở đâu.

| Khúc | Từ → tới | Khúc dài thường có nghĩa là |
|---|---|---|
| Mở tới CI xanh đầu tiên | mở pull request → lượt CI xanh đầu tiên trên nó | CI chậm hoặc chập chờn, hoặc pull request được mở khi chưa sẵn sàng |
| CI xanh tới vào hàng merge | CI xanh đầu tiên → pull request vào hàng merge | đang chờ review hoặc chờ phiên làm việc ship nó |
| Hàng merge tới đã merge | vào hàng → đã merge | hàng chạy lại CI trên main mới nhất; mỗi lần bị đẩy khỏi hàng (một lượt đỏ trong hàng) thêm một vòng CI đầy đủ |
| Đã merge tới đã deploy | đã merge → job deploy của lần deploy xanh đầu tiên chứa nó xong | deploy bị chặn (bảng job còn việc, một migration chờ Migration Apply) hoặc build chậm |
| Đã deploy tới đã verify | job deploy xong → post-deploy verify đạt | verify chậm, hoặc verify đỏ phải deploy lần hai |

Repo không có hàng merge (repo gốc) thì không có điểm hàng merge: khúc "Hàng merge tới đã merge" của nó tính từ CI
xanh tới lúc merge.

## 6. Sức khoẻ CI

| Con số | Cho thấy gì | Làm gì |
|---|---|---|
| p50 / p95 theo workflow | Thời lượng thông thường và chậm của 4 tuần gần nhất (bỏ lượt bị huỷ và bị bỏ qua) | Chia nhỏ hoặc thêm cache cho job chậm nhất; xem danh sách job trong lượt chạy GitHub |
| Tỉ lệ lỗi theo workflow | Số lượt đỏ / số lượt chạy | Tỉ lệ cao trên pull request là bình thường lúc đang code; trên main hay trong hàng merge thì không |
| Tỉ lệ lỗi trên main | Số lượt CI và deploy đỏ trên nhánh mặc định / số lượt chạy | Trên vài phần trăm: có thứ thường làm hỏng main; tìm nguyên nhân chung |
| Chạy lại | Số lượt chạy có nhiều hơn một lần thử | Chạy lại nhiều thường do test chập chờn |
| Job chập chờn | Job đỏ rồi xanh trên cùng một commit | Sửa job đứng đầu trước; không bao giờ chạy lại cho qua |
| Thời gian chờ hàng merge và số lần bị đẩy ra | Thời gian trong hàng, và số lần một pull request bị đẩy ra | Mỗi lần bị đẩy ra tốn một vòng CI đầy đủ |
| Phút Actions | Số phút job theo workflow (repo public chạy miễn phí, nhưng lãng phí vẫn hiện ra) | Bỏ các job chạy khi không có gì chúng kiểm thay đổi |

## 7. Tab hàng merge

AA-CIS-App, AA-Booking và AA-Partner merge qua hàng merge của GitHub. Tab hiện từng **lượt**: một lần pull request nằm
trong hàng, đọc từ timeline của nó (vào / ra khỏi hàng merge, đã merge) và ghép với các lượt chạy merge_group trên nhánh
tạm của hàng.

| Con số | Định nghĩa | Làm gì |
|---|---|---|
| Chờ hàng merge p50 / p95 | Thời gian từ lúc vào hàng tới lúc merge, các lượt được merge trong 4 tuần gần nhất. p95 được tô màu (thiết lập `cis.delivery.queue_wait_*`) | Check merge_group chậm hoặc phải dựng lại nhiều sau các lượt bị loại; tăng tốc hoặc thêm cache cho các check chạy trong hàng |
| Tới merge p50 / p95 | Từ lần đầu pull request vào hàng tới lúc merge, tính mọi lượt của nó | Cao hơn nhiều so với thời gian chờ: các lượt liên tục bị loại |
| Kết quả | **đã merge** (hàng gỡ nó ra và merge), **bị loại** (hàng gỡ ra mà không merge), **bị rút** (người hoặc agent rút ra, hoặc pull request bị đóng), **trong hàng** | - |
| Tỉ lệ bị loại | Số lượt bị loại / số lượt được merge hoặc bị loại (thiết lập `cis.delivery.queue_ejection_*`) | Xem bảng lý do: có thứ chạy được trên pull request nhưng hỏng trên bản đã gộp |
| Lý do bị loại | check lỗi, check quá giờ, check bị huỷ, không có check nào chạy (từ các lượt merge_group của lượt đó), kèm các workflow đỏ | Sửa workflow loại nhiều nhất |
| Tỉ lệ chập chờn | Số lượt có dấu hiệu chập chờn / số lượt được merge hoặc bị loại (thiết lập `cis.delivery.queue_flaky_*`). Dấu hiệu: một lượt merge_group mà lần thử mới nhất đạt sau khi lần thử trước đó lỗi, hoặc bị loại vì check đỏ rồi được merge mà không có commit mới | Cách ly hoặc sửa check; không bao giờ đưa lại vào hàng cho qua |
| CI merge_group | Số phút (theo job, mọi lần thử), số lượt chạy, tỉ lệ lỗi, p95 và số lần chạy lại của các lượt chạy trong hàng | Mỗi lần bị loại tốn trọn một vòng số phút này |
| Lưu lượng | Số lượt rời hàng mỗi ngày, theo kết quả | - |

## 8. Tab bản đồ git

Commit trên nhánh mặc định của từng repo trong 90 ngày, kèm file của chúng (số dòng thêm + xoá từ các squash commit).

| Con số | Định nghĩa |
|---|---|
| Lịch commit | Số commit mỗi ngày; các cột cộng theo tuần |
| Loại tác giả | App agent (`aa-agent`), bot CI (`aa-ecosys-ci-bot`, các bản copy migration của Infra), release-please (commit `chore(...): release`), Dependabot, bot khác, một người. Không bao giờ lưu tên đăng nhập của một người |
| Mức thay đổi | Số dòng thêm + xoá theo thư mục cấp đầu, rồi theo thư mục con hoặc file (đi sâu), và 30 file đứng đầu, trong 30 hoặc 90 ngày. Bỏ qua file lock (`churn_exclude` trong `tools/delivery/apps.json`) |
| Merge theo tiền tố nhánh | Số pull request đã merge theo tiền tố của nhánh (feat, fix, docs, chore, bot, release-please, ...) |
| Commit gần đây | 50 commit mới nhất trên nhánh mặc định kèm pull request của nó (`(#n)` cuối cùng trong tiêu đề) |
| Đã đọc file | Tỉ lệ commit đã đọc danh sách file; lịch sử mới được lấp đầy sau vài lượt chạy hằng giờ, mới nhất trước |

Dùng nó để thấy mã đang thay đổi ở đâu (một điểm nóng đổi mỗi tuần là ứng viên cho một test hoặc tách nhỏ) và ai đang
đổi. Như phần còn lại của trang, nó mô tả hệ thống, không mô tả một người.

## 9. Dùng thế nào

- **Mỗi tuần**: DEV-03 hiện tuần đó theo từng app. Chọn một điểm nghẽn để sửa và ghi vào log phiên.
- **Mỗi tháng**: DEV-01 so với tháng trước. Đặt một hoặc hai mục tiêu cải thiện.
- **Không bao giờ** dùng các số này để chấm điểm một người. Đo người thì số sẽ bị "làm đẹp" (định luật Goodhart).
  Chúng mô tả hệ thống và quy trình.
- **n nhỏ**: khi số sự kiện ít hơn thiết lập, đừng kết luận; chờ thêm dữ liệu.

## 10. Giới hạn hiện tại

- Chỉ có Dev; chưa có chiều prod, và chưa có sự cố trong phần khôi phục.
- Phát hiện hotfix dựa vào một pull request `fix` nhắc tới pull request nó sửa (`#123`); bản sửa không nhắc tới thì
  không được tính.
- Job chập chờn lấy từ các lần chạy lại và các lượt chạy lặp trên một commit; độ chập chờn theo từng test từ báo cáo
  JUnit là bước sau.
- Nút Làm mới đọc lại bản tóm tắt đã đăng; nó không khởi động một lượt thu thập GitHub mới (API CIS không có token
  GitHub).
- Khoảng tự chọn chỉ lùi được tới đầu kho sự kiện (`store_days`, 98 ngày); khoảng dài hơn hoặc cũ hơn bị từ chối,
  không bao giờ ước đoán.
- Cảnh báo (main đỏ quá lâu, deploy hỏng, verify đỏ) và lead time tách theo agent / người / bot là bước sau.

## 11. Khoảng thời gian và biểu đồ

**Bộ chọn khoảng.** Một bộ chọn phía trên các tab đặt khoảng thời gian cho mọi tab (Tổng quan, từng app, Hàng merge,
Bản đồ git); nó nằm trong URL (`?range=7d|28d|90d`, hoặc `?range=custom&from=YYYY-MM-DD&to=YYYY-MM-DD`), nên một
đường link mở đúng góc nhìn đó.

- **Mốc sẵn 7 / 28 / 90 ngày** do bộ thu thập tính mỗi giờ (`ranges.d7`, `d28`, `d90` theo từng app trong cùng bản tóm
  tắt; `range_presets` trong `tools/delivery/apps.json`). Mốc 28 ngày là con số chính trang vẫn luôn hiện.
- **Khoảng tự chọn** (từ, đến, trọn ngày UTC): API CIS tính lại từ các file sự kiện theo ngày của bộ thu thập bằng
  một bản sao y từng byte phần tính toán của bộ thu thập (`tools/delivery/delivery_engine.py`), nên khoảng tự chọn và
  mốc sẵn của cùng một khoảng không thể lệch nhau. Bản tóm tắt mang sha256 của engine; khi bản sao ở CIS khác (một thay
  đổi bộ thu thập chưa đồng bộ bằng `tools/delivery/sync_engine.py`), khoảng tự chọn tạm dừng kèm thông báo, còn mốc
  sẵn vẫn chạy. Khoảng dài nhất là thiết lập `cis.delivery.custom_range_max_days`; khoảng trước đầu kho sự kiện
  (`definitions.store_from`) hoặc sau lượt thu thập mới nhất bị từ chối. Kết quả được lưu đệm theo từng khoảng tới lượt
  thu thập sau (tối đa `cis.delivery.custom_range_cache_entries` khoảng).
- Khoảng bắt đầu trước lịch sử đầy đủ của một app được đo từ ngày lịch sử đầy đủ, như trước ("số ngày được phủ").

**Biểu đồ.**

| Biểu đồ | Cho thấy gì |
|---|---|
| Xu hướng DORA | Số deploy, lead time p50, tỉ lệ deploy hỏng và thời gian khôi phục p50 theo tuần ISO trong 12 tuần, một app hoặc so sánh mọi app |
| Luồng phát hành | Mở pull request → CI xanh → vào hàng merge → merge → deploy → verify: trung vị và p95 của từng bước trong khoảng đã chọn, n mỗi bước; bước có trung vị dài nhất được làm nổi bật. Bảng chữ dưới sơ đồ mang cùng các số |
| Phân bố thời gian chờ trong hàng | Số lượt đã merge theo từng nhóm thời gian chờ (`queue_wait_bins_h` trong `apps.json`) |
| Lý do bị loại | Số lượt bị loại và bị rút ra theo lý do, dạng thanh |
| Tỉ lệ bị loại theo tuần | Bị loại trên (đã merge + bị loại) theo từng tuần ISO của khoảng |
| Treemap churn | Số dòng thay đổi theo thư mục cấp đầu, kích thước theo churn; chọn một thư mục để đi sâu vào thư mục con và file |
| Commit gần đây | Các commit mới nhất trên nhánh mặc định kèm link pull request |

**Sắp xếp.** Các thẻ repo ở Tổng quan và Hàng merge sắp theo màu xấu nhất trước (mặc định), theo tên, hoặc theo chỉ số
đang hiện (cao nhất hoặc chậm nhất trước); lựa chọn nằm trong URL (`?sort=`).
