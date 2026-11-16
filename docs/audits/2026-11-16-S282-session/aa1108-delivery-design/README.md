# AA-1108 — Thiết kế trang Platform › Delivery (CI/CD + DORA theo app) — tư vấn cho tech lead, S282

## 1. Trang phải trả lời câu hỏi gì

Mỗi chỉ số trên trang gắn với một quyết định, không đo cho đẹp:

| Câu hỏi | Quyết định đi kèm |
|---|---|
| Mỗi app ra bản nhanh tới đâu, có đều không? | Dồn sức vào app nào, có cần chia nhỏ PR hơn không |
| Một thay đổi mất bao lâu từ lúc mở PR tới lúc chạy trên Dev, kẹt ở đoạn nào? | Tối ưu CI, merge queue hay khâu review |
| Bao nhiêu lần deploy gây lỗi, sửa mất bao lâu? | Thêm test/guard ở đâu, có cần làm rollback nhanh hơn |
| CI có ổn định, có tốn thời gian vô ích không? | Sửa test chập chờn, chia shard, cache |
| Các tool ship của agent có làm chậm/hỏng không? | Sửa `ship_*`, train, guard |

## 2. Bộ chỉ số (chuẩn ngành + phần riêng của mình)

### 2.1 DORA — 5 chỉ số (DORA đã mở rộng từ 4 lên 5)

Throughput:
- **Deployment frequency**: số lần deploy thành công mỗi app mỗi tuần.
- **Lead time for changes**: từ commit đầu / lúc mở PR tới khi bản chứa commit đó deploy thành công và qua post-deploy verify.
- **Failed deployment recovery time** (tên mới của MTTR từ 2023): từ lúc deploy hỏng tới khi có deploy xanh kế tiếp.

Instability:
- **Change failure rate**: tỉ lệ deploy gây lỗi (định nghĩa ở §3).
- **Rework rate**: tỉ lệ deploy không theo kế hoạch (hotfix/revert sửa một deploy trước).

### 2.2 Sức khoẻ CI (đây là chỗ mình đang tốn thời gian thật)

- Thời gian p50 / p95 theo workflow và theo job (CI PR, merge queue, main, deploy, post-deploy verify).
- Thời gian chờ merge queue; số lần bị đẩy khỏi hàng.
- Tỉ lệ đỏ trên main; tỉ lệ chạy lại (`run_attempt > 1`); test chập chờn (đỏ rồi xanh trên cùng SHA).
- Phút Actions theo repo (repo public nên miễn phí, nhưng vẫn đo để thấy lãng phí), cache hit.

### 2.3 Phần riêng của hệ sinh thái AA

- Tách PR của agent (GitHub App `aa-agent`), của người và của bot (release-please, schema bot, docs bot): bot không tính vào lead time.
- Migration: thời gian từ merge PR migration tới khi Migration Apply xong (đoạn hay kẹt vì DM-11.4 chờ bảng job rảnh).
- Post-deploy verify: tỉ lệ đạt, lần đỏ gần nhất.

## 3. Định nghĩa chuẩn cho hệ mình (phần quan trọng nhất)

Đo sai định nghĩa thì số đẹp mà vô nghĩa. Đề xuất:

- **Deploy** = một bản ghi GitHub Deployment `environment: dev` của app có trạng thái `success`, và lần post-deploy verify của SHA đó xanh. GitHub đã tự ghi Deployment khi workflow có `environment:`; ở CIS có trên 100 bản ghi.
  Nhiều service chung 1 SHA (CIS api + worker, CRM api + web) gộp thành **1 deploy của app**.
- **Change** = một PR squash-merge vào main. Lead time được tách thành các khúc:
  `mở PR → CI xanh đầu tiên → vào merge queue → merged → deploy xong → verify xanh`.
  Biết khúc nào dài mới biết sửa ở đâu.
- **Deploy hỏng** = một trong các trường hợp:
  - verify đỏ;
  - deploy bị rollback (deploy lại SHA cũ, DEV-03 đã phát hiện được);
  - một PR revert;
  - một PR `fix:` trỏ tới PR của deploy đó trong vòng 48 giờ.
- **Khôi phục** = từ lúc hỏng tới deploy xanh kế tiếp của app đó.
- **Môi trường** là một chiều riêng ngay từ đầu (`dev` bây giờ, `prod` sau go-live). Trang ghi rõ "số trên Dev". DORA chuẩn đo prod, nên không so với benchmark ngành như thể đây là prod.
- **Bộ lọc mặc định:** PR chỉ đổi docs, không gây deploy, thì không tính vào lead time; vẫn đếm ở một mục riêng.

## 4. Kiến trúc dữ liệu — so sánh và đề xuất

| Phương án | Ưu | Nhược | Chi phí |
|---|---|---|---|
| **A. Workflow định kỳ ở repo gốc** đọc API GitHub của 6 repo (`GITHUB_TOKEN`), sinh file sự kiện + file tóm tắt, publish lên S3 như `catalogue.json`; API CIS chỉ đọc | Không thêm secret, không mở endpoint mới, dùng lại đường Docs sync đã chạy | Trễ theo chu kỳ (1 giờ) | 0 USD |
| B. Webhook GitHub → endpoint ingest của CIS → bảng DB | Gần thời gian thực | Thêm secret webhook, endpoint public cần xác thực, thêm bảng và retention | ~0 USD nhưng thêm bề mặt tấn công |
| C. OpenTelemetry Collector (receiver GitHub) + Grafana | Chuẩn mở, dashboard mạnh | Cần máy chạy collector và kho metric: trái quyết định "observability trả phí đang hoãn" | Có phí |
| D. SaaS (Swarmia, LinearB, Datadog DORA) | Có sẵn | Dữ liệu ra ngoài, phí theo người | Có phí |

**Đề xuất: A**, nhưng làm đúng 3 điểm để sau này chuyển sang B hoặc C mà không làm lại:

1. **Lưu sự kiện thô, chỉ số tính sau.** Collector ghi các sự kiện chuẩn hoá (workflow run, job, deployment, PR) dạng NDJSON chia theo ngày, rồi mới sinh file tóm tắt. Đổi định nghĩa thì tính lại được trên lịch sử cũ.
2. **Đặt tên trường theo OpenTelemetry semantic conventions cho CI/CD và VCS**, ví dụ `cicd.pipeline.name`, `cicd.pipeline.run.duration`, `cicd.pipeline.result`, `vcs.change.time_to_merge`. Sau này đẩy sang OTel không phải đổi mô hình.
3. **Giữ lịch sử lâu hơn GitHub.** Log Actions chỉ giữ 90 ngày. File sự kiện trên S3 có retention riêng: 400 ngày, đủ so năm.

DEV-01 (DORA tháng) và DEV-03 (dòng chảy tuần) đọc cùng file tóm tắt, nên trang và báo cáo luôn khớp số.

## 5. Giao diện

- **Tổng quan**: mỗi app một thẻ, gồm:
  - 5 chỉ số DORA, mỗi chỉ số có màu theo ngưỡng và sparkline 12 tuần;
  - CI p95 của workflow chậm nhất;
  - trạng thái main (xanh/đỏ và đỏ từ khi nào).
- **Tab từng app**:
  - dòng thời gian deploy (xanh / hỏng / rollback);
  - biểu đồ cột chồng các khúc lead time (thấy ngay khúc kẹt);
  - bảng sức khoẻ CI theo workflow;
  - danh sách deploy hỏng kèm thời gian khôi phục;
  - top test chập chờn;
  - link thẳng tới run trên GitHub.
- Ngưỡng xanh/vàng/đỏ là **setting** trên Platform › Settings, có hướng dẫn EN/VI, ví dụ: lead time p50 ≤ 1 ngày, CFR ≤ 15 %, main đỏ > 2 giờ là đỏ.
- Mỗi chỉ số có tooltip giải thích nó là gì, tăng/giảm nghĩa là gì và nên làm gì.
- Dùng kit UI, đủ EN/VI, light/dark và mobile.

## 6. Cách dùng để có hiệu quả

- Mỗi tuần: DEV-03 đọc trang, chọn 1 điểm nghẽn để sửa; ghi vào log phiên như C4.3.
- Mỗi tháng: DEV-01 so với tháng trước, đặt 1–2 mục tiêu cải thiện.
- Cảnh báo vào Platform › Alerts: main đỏ quá ngưỡng, deploy hỏng, verify đỏ.
- **Không dùng để chấm điểm cá nhân** (Goodhart: đo người thì số sẽ bị "làm đẹp"). Đây là chỉ số của hệ thống và quy trình.
- Số trên Dev biến động mạnh vì ít sự kiện: hiện số mẫu (n) cạnh mỗi chỉ số, và không kết luận khi n quá nhỏ.

## 7. Lộ trình

- **P1 (S282, AA-1108):**
  - collector A, sự kiện thô + tóm tắt;
  - API CIS + trang Tổng quan và tab app;
  - setting ngưỡng;
  - DEV-01 và DEV-03 đọc dữ liệu thật.
- **P2:** cảnh báo; phát hiện test chập chờn từ báo cáo JUnit trong artifact; tách số agent / người / bot; thời gian Migration Apply.
- **P3 (khi có prod / tenant trả tiền):**
  - chiều `prod`, nối sự cố (incident) vào "khôi phục";
  - cân nhắc đẩy sang OpenTelemetry nếu lúc đó mở lại observability trả phí.

## 8. Quyết định của tech lead (S282 ~08:10 +07: "Ok hết các đề xuất")

1. Deploy hỏng gồm cả revert/hotfix trong 48 giờ (rework) — **đề xuất: có**, tách CFR và rework rate như DORA 5 chỉ số.
2. PR của bot không tính vào lead time, nhưng vẫn hiện ở mục riêng — **đề xuất: có**.
3. Tần suất làm mới — **đề xuất: mỗi giờ** (repo public, Actions miễn phí); có thêm nút "làm mới" cho admin.
4. Ngưỡng khởi đầu theo dải "high" của DORA, chỉnh trên Settings — **đề xuất: có**.

Nguồn chuẩn ngành: DORA 5 chỉ số (CD Foundation, 10/2025); OpenTelemetry semantic conventions CI/CD; GitHub Deployments API.

## 9. Xuất kiến thức (tech lead S282)

- AA Academy: inventory thêm mục "Delivery metrics: the five DORA keys and CI health per app" → module L5 (root #820).
  Lane AA-1108 viết thêm trang hướng dẫn `docs/guides/delivery-metrics.md` (+ `.vi.md`, tầng staff) để bài học L5
  trích dẫn được theo hash.
- Kit dự án AA (AA-1103): mẫu `docs/templates/delivery-metrics-report.md` đã có 5 chỉ số DORA; lane AA-1108 chỉnh mẫu
  theo định nghĩa §3 (deploy, change, deploy hỏng, khúc lead time, chiều môi trường) để kit sao chép đúng bản.

