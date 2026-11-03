---
id: GUIDE-12-ai-reports
title: Runbook nhà cung cấp AI và báo cáo
description: Cách đọc và dùng các trang CIS admin về nhà cung cấp AI và dữ liệu, chi phí và trần chi phí (AI providers, Cost Operations, Cost per app) và sổ đăng ký báo cáo (Reports), và làm gì khi một nhà cung cấp ngừng trả lời hoặc chi phí tăng vọt.
type: how-to
status: draft
owner: nghiep
audience: [owner, staff, engineer]
applies_to: [aa-cis-frontend, aa-cis-api]
last_reviewed: 2026-11-01
review_every_days: 90
related: [GUIDE-12, GUIDE-12-cis-admin, GUIDE-04, FIN-01, OPS-04, AA-1020]
lang: vi
translation_of: docs/guides/ai-providers-and-reports-runbook.md
---

# Runbook nhà cung cấp AI và báo cáo

Thuộc bộ [truy cập và vận hành các ứng dụng](app-access-and-operations.vi.md). Đây là bản tiếng Việt của
[ai-providers-and-reports-runbook.md](ai-providers-and-reports-runbook.md).

## 1. Ai dùng

Chủ doanh nghiệp và nhân sự admin, để trả lời bốn câu hỏi: mọi nhà cung cấp AI và dữ liệu có trả phí có đang trả lời
không, đã tốn bao nhiêu, còn cách trần chi phí bao xa, và mỗi báo cáo định kỳ đã chạy chưa. Cả bốn trang nằm trong
CIS admin và cần vai trò **admin**. Đăng nhập theo kiểu đăng nhập nhân sự của
[runbook CIS admin](cis-admin-runbook.vi.md), mục 4.

| Trang | Đường đi trong menu | Địa chỉ Dev |
|---|---|---|
| **AI providers** | Platform › AI & spend › AI providers | `https://aa-cis.lumiguides.it.com/admin/ai-gateway` |
| **Cost Operations** | Platform › AI & spend › Cost Operations | `https://aa-cis.lumiguides.it.com/admin/cost-ops` |
| **Cost per app** | Platform › AI & spend › Cost per app | `https://aa-cis.lumiguides.it.com/admin/platform/cost` |
| **Reports** | Platform › Overview › Reports | `https://aa-cis.lumiguides.it.com/admin/reports` |

Mở các trang này không gọi nhà cung cấp nào và không tốn tiền: mọi con số lấy từ log và các lần kiểm đã lưu của chính
chúng ta. Các nút có tốn tiền được nêu rõ bên dưới.

## 2. AI providers

Trang có sáu tab. Mỗi tab có **Guide** bằng lời dễ hiểu (tab **Guide**, hoặc **New here? Read the Guide**).

| Tab | Hiển thị gì | Bạn đổi được gì |
|---|---|---|
| **Providers** | Ba ô số (**Spend this month**, **Spend today**, **Need a look**) và mỗi nguồn trả phí một dòng: **LLM connections**, **Decisions (Jev)**, **Data providers** (DataForSEO, Geoapify). Ba chế độ xem: **Overview**, **Connections**, **Jev credit** | **Connections**: bật hoặc tắt một kết nối, giới hạn và ngân sách tháng của nó, gửi một lời gọi thử nhỏ. **Jev credit**: ghi một lần nạp tiền Jev |
| **Routing** | Mỗi bước của pipeline dùng model nào trước, chuỗi dự phòng và model chạy bóng; thẻ **LLM availability** | **Save** (model chính), **Save route** (dự phòng và chạy bóng) |
| **Models & trials** | Mọi model nền tảng gọi được, chạy ở đâu, giá bao nhiêu, và các so sánh chạy bóng | Bật hoặc tắt một model (giá chỉ đổi qua một thay đổi đã được review) |
| **Budgets** | Mọi trần chi phí: trần ngày của nhà cung cấp, trần của job, ngân sách kết nối, ngân sách AI của tenant | **Add a cap**, sửa một trần. **Stops at the cap** dừng lượt chạy; **Alert only** chỉ cảnh báo |
| **Calls** | Mọi lời gọi đã ghi log, từng cái một, với kết quả và độ trễ | Chỉ có bộ lọc |
| **Guide** | Cách đọc trang | - |

### Đọc trạng thái của một dòng

| Trạng thái | Nghĩa | Làm gì |
|---|---|---|
| **OK** | Đang trả lời, không gần giới hạn nào | Không cần làm gì |
| **Degraded** | Đang trả lời, nhưng các lời gọi gần đây có lỗi | Theo dõi; báo kỹ sư trực nếu kéo dài một ngày |
| **Circuit open** | Nhiều lời gọi liên tiếp lỗi; cổng tạm bỏ qua kết nối này một thời gian và dùng tuyến kế tiếp | Không làm tay; nó tự thử lại |
| **Low** | Số dư dưới ngưỡng cảnh báo, hoặc đã dùng quá 80 % credit hôm nay | Lên kế hoạch nạp tiền với tech lead |
| **Cap reached** | Ngân sách, số dư hoặc credit hôm nay đã hết; lời gọi dừng hoặc chuyển dự phòng | Chỉ nâng trần khi chủ doanh nghiệp duyệt, hoặc chờ sang kỳ sau |
| **Off** | Đã tắt có chủ đích | Không cần làm gì |
| **No recent calls** | Không có lời gọi nào được trả lời trong 24 giờ; không có lỗi nào được biết | Không cần làm gì |
| **Unknown** | Không đọc được nguồn, hoặc chưa biết số dư | Đọc lý do trên dòng |

### Việc thường làm

1. **Kiểm trước một lượt chạy trả phí.** Mở **Providers**. **Need a look** nên bằng không, và kết nối mà bước đó dùng
   (xem **Routing**) nên ở trạng thái OK.
2. **Theo dõi các lời gọi của một job.** Mở **Jobs**, bấm vào job, rồi **Open trace**; hoặc trong **Calls** chọn
   **Only this job** trên một dòng. Trace liệt kê mọi lời gọi trả phí của job đó theo thứ tự thời gian. Cho cả một
   tour: **Master Content** › tour đó › **Open AI trace**.
3. **Ghi một lần nạp tiền Jev.** **Providers › Jev credit**: điền **Date** và **Amount (USD)**, rồi **Add top-up**. Jev
   không có dịch vụ báo số dư, nên credit còn lại là ước tính từ các lần nạp này trừ đi chi phí chúng ta đã ghi log.
4. **Đưa các job bị từ chối trở lại.** Khi một nhà cung cấp từng từ chối lời gọi trả lời lại (dòng của nó OK), dùng
   **Re-queue refused jobs**. Nút này cho xem số liệu trước và chỉ đưa lại vào hàng đợi sau khi bạn xác nhận, mỗi lần
   50 job. Bước kiểm không tốn tiền; sau đó các job chạy và tốn đúng như lần đầu.

> [!WARNING]
> **Save** và **Save route** đổi model cho mọi lời gọi tiếp theo của bước đó. Chạy bóng làm chi phí của các lời gọi
> được lấy mẫu tăng gấp đôi. Đổi tuyến hay đổi trần là quyết định của tech lead; hãy hỏi trước.

## 3. Cost Operations và Cost per app

- **Cost Operations** cho thấy nền tảng chi bao nhiêu cho model AI, DataForSEO, Jev và hoá đơn AWS, so với ngân sách.
  Các tab: **Overview**, **AI & data spend** (theo tenant, model và thị trường), **LLM**, **DataForSEO**, **AWS bill**,
  **Jev**.
- **Cost per app** chia một tháng theo ứng dụng: CIS, Booking, TripPlanner, Partner CRM, cộng phần dùng chung (database
  và mạng) và phần định danh (đăng nhập nhân sự).
- **Refresh from AWS** hỏi Amazon số liệu mới và tốn khoảng 0,04 USD mỗi lần bấm. Các trang tự làm mới khoảng một lần
  mỗi ngày, nên hiếm khi cần nút này.

Cách đọc tiền được giải thích cho chủ doanh nghiệp trong [hướng dẫn cho CEO](ceo.vi.md), mục 5; quy trình chi phí
nằm ở [FinOps](../ops/finops.md).

## 4. Reports

**Reports** là sổ đăng ký mọi báo cáo định kỳ của nền tảng: ai đọc, bao lâu một lần, và đã chạy chưa.

1. Đọc các ô số: **Reports in the register**, **Generated here**, **Overdue**, **Failed runs (7 days)**, **Latest KPI
   day** (ảnh chụp KPI hằng ngày được lấy mỗi sáng lúc 07:30 giờ Việt Nam cho ngày hôm trước).
2. Lọc theo nhóm hoặc độ ưu tiên, hoặc đánh dấu **Generated here only**.
3. Mở một dòng báo cáo. Ngăn chi tiết cho thấy quyết định mà báo cáo hỗ trợ, người đọc, tần suất, nơi gửi tới, các
   KPI và các lần chạy. Mở một lần chạy để đọc kết quả.
4. **Generate now** (admin) đưa một báo cáo theo sự kiện hoặc một lần chạy mới vào hàng đợi. Sau khoảng một phút là
   xong; bấm **Refresh**.

| Trạng thái hôm nay | Nghĩa |
|---|---|
| **Up to date** | Lần chạy gần nhất phủ kỳ mới nhất |
| **Due** / **Overdue** | Đã tới hạn chạy, hoặc đã trễ |
| **On request** | Chỉ chạy khi có người bấm **Generate now** |
| **First run pending** | Đã lên lịch, chưa chạy lần nào |
| **Not generated here** | Viết tay từ mẫu của nó |

Báo cáo ngày, tuần và tháng tự chạy. Các gói báo cáo kinh doanh cho chủ doanh nghiệp được soạn nháp ở đây, tech lead
review rồi mới đăng lên Jira.

## 5. Khi có gì đó sai

| Bạn thấy | Sau đó |
|---|---|
| **Need a look** lớn hơn không | Mở dòng đó; dòng lý do cho biết vì sao. Báo kỹ sư trực nếu là **Cap reached**, **Unknown** hoặc **Circuit open** quá một ngày |
| Một e-mail cảnh báo ngân sách | Mở **Cost Operations** và **Budgets**; so với số đã chi từ đầu tháng; báo tech lead |
| Một dòng nhà cung cấp báo bị từ chối truy cập hoặc hết credit | Không đổi tuyến. Kỹ sư trực làm theo [playbook LLM bị từ chối truy cập](../ops/playbooks/llm-access-denied.md) hoặc [playbook chi phí LLM tăng vọt](../ops/playbooks/llm-cost-spike.md) |
| Một báo cáo **Overdue** hoặc một lần chạy **Failed** | Mở lần chạy để xem lỗi; báo kỹ sư trực |

Trong giai đoạn dev, tech lead là kỹ sư trực.

## 6. Lưu ý giai đoạn Dev

- Tài khoản model chat chính từ chối mọi lời gọi từ 29/10/2026: các dòng của nó hiện **Circuit open** hoặc bị từ chối
  truy cập, và các bước AI phải chờ hoặc lỗi
  ([postmortem](../ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md)). Embedding cho tìm kiếm vẫn chạy.
- Đường gọi thẳng Anthropic API chưa được bật. OpenAI API là lựa chọn dự phòng cuối cùng của các bước chấm điểm và
  các bước viết bài (nền tảng và tenant), chỉ dùng khi mọi đường AWS đều bị chặn, với trần 10 USD mỗi tháng.
- Số liệu Dev nhỏ và không ổn định: là các lượt chạy thử, không phải khối lượng kinh doanh. Đừng đọc xu hướng từ đó.

## Nguồn (cho người bảo trì)

Đọc từ AA-CIS-App `main` ngày 01/11/2026: `frontend/app/admin/ai-gateway/messages.ts` và `guide.ts`,
`frontend/app/admin/cost-ops/messages.ts`, `frontend/app/admin/reports/messages.ts`, `frontend/lib/rbac.ts`. Sổ đăng
ký báo cáo: [`reports/catalog.yaml`](../reports/catalog.yaml). Quyết định: ADR gốc 0009. Giữ trang này khớp với
[ai-providers-and-reports-runbook.md](ai-providers-and-reports-runbook.md).
