---
id: OPS-08-s261-ai-gateway-design-v2
title: "Cổng AI và dữ liệu (AI gateway) v2: thiết kế đề xuất cho mọi nguồn trả phí, mọi app, mọi stage (S261)"
description: "Thiết kế cho tech lead: một cổng cho mọi nhà cung cấp AI và dữ liệu trả phí (LLM qua Bedrock, Anthropic, OpenAI, Azure OpenAI; Jev, DataForSEO, Geoapify), mọi app và stage; 8 chức năng, thứ tự làm, 3 quyết định."
type: report
status: draft
owner: nghiep
audience: [cto, engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-804, AA-642, AA-900, AA-1002, AA-820, AA-842, AA-1004, AA-1016, AA-1015, AA-964, AA-896]
---

# Cổng AI và dữ liệu (AI gateway) v2: thiết kế đề xuất (S261, 31/10/2026)

Tác nhân: Claude Code. Chỉ là tài liệu: không đổi code, không gọi AWS, DB hay LLM, không đổi route nào.
Quyết định kiến trúc đi kèm: [root ADR 0009](../../adr/0009-ai-platform-and-provider-gateway.md) (đang chờ duyệt).

## Cổng là gì, phạm vi tới đâu

Tech lead định nghĩa (31/10): *"LLM gateway là nơi dùng gọi, quản lý, điều hướng, giám sát, truy vết cho tất cả
nguồn, họ model, và có setup tùy biến cho mỗi loại app, stage, hay nơi nào cần dùng llm trong hệ sinh thái"*, cộng
*"còn cả Jev và DFS nữa"*. Bản này lấy đúng câu đó làm mục tiêu. Phạm vi: **mọi nhà cung cấp AI và dữ liệu mà AA trả
tiền**, gồm LLM ở mọi nguồn (Bedrock trên acc3 và acc2, API trực tiếp của Anthropic và OpenAI, Azure OpenAI) và mọi
họ model (Claude, GPT, Cohere; thêm Nova, Llama, Kimi: chạy được trên Bedrock acc2, hôm nay chưa stage nào dùng),
Jev, DataForSEO, Geoapify, Bedrock Guardrails và Bedrock Batch; cho **mọi app** (CIS, TripPlanner, CRM/Partner,
Booking khi cần) và **mọi stage**. Thiết kế đã duyệt ở S258 phủ LLM của CIS (TripPlanner và CRM sẽ dùng chung lõi ở
một bước sau) và có Jev như một loại nguồn; chưa phủ DataForSEO và Geoapify. Bản v2 mở rộng nó và giữ những gì S258
đã đúng: tách tài khoản / nơi chạy / model; có thứ tự dự phòng; quy định dữ liệu được đi đâu nằm riêng; chi phí lấy
từ sổ ghi.

Hai từ dùng trong cả bài:

- **Miền sự cố**: nhóm nguồn có thể hỏng cùng lúc vì cùng người trả tiền / cùng tổ chức có thể chặn.
- **Đường dự phòng ấm**: đường thứ hai đã có tiền, có khoá, được gọi thử định kỳ, nên khi nguồn chính hỏng thì dùng
  được ngay.

## 8 chức năng

| Chức năng | Mục tiêu | Hôm nay | Cần làm |
|---|---|---|---|
| **Gọi** | Mọi app gọi mọi nhà cung cấp trả phí qua một cửa, mỗi loại việc một cách gọi (viết chữ, embedding (biến chữ thành số để tìm nội dung giống nhau), quyết định của Jev, tra SEO, tra toạ độ) | Chỉ LLM của CIS đi qua cổng; Jev, DataForSEO, Geoapify mỗi thứ một client riêng; TripPlanner có bản sao cổng riêng; CRM còn giả lập; có vài chỗ code gọi thẳng nhà cung cấp, không qua cổng | Một lõi dùng chung, với phần nối riêng cho từng nhà cung cấp; đóng các chỗ code gọi thẳng nhà cung cấp, không qua cổng; xoá code DataForSEO cũ |
| **Nguồn** | Mỗi đường vào (tài khoản, API, khoá, vùng) là một dòng trong sổ nguồn, có ngân sách, phạm vi dữ liệu và miền sự cố | Sổ nguồn chỉ có cho LLM của CIS (5 nguồn); không ghi miền sự cố; Jev, DataForSEO, Geoapify nằm trong biến môi trường và code | Đưa mọi nhà cung cấp trả phí vào sổ nguồn, thêm miền sự cố |
| **Họ model** | Hãng làm model, nơi chạy model và khả năng của model (suy luận, xuất JSON, cache) là ba thứ riêng, ghi bằng dữ liệu; thêm họ mới không cần sửa code | Muốn thêm một hãng model mới phải sửa code | Thêm hãng / model mới chỉ bằng cấu hình |
| **Điều hướng** | Mỗi stage có model chính, dự phòng theo thứ tự, ít nhất một đường dự phòng ấm ở miền sự cố khác, và giới hạn tổng thời gian chờ, kể cả khi chuyển sang dự phòng | Có route theo stage, nhưng gần hết stage chạy trên acc3; 29/10 acc3 bị chặn thì không stage viết nào chạy; code chọn model ở nhiều chỗ khác nhau; vài chỗ dùng model cố định, không theo cấu hình | Chọn model ở một chỗ duy nhất; luật "luôn có đường dự phòng khác miền sự cố"; giới hạn tổng thời gian chờ |
| **Tuỳ biến theo app / stage** | Mỗi app, mỗi stage có hồ sơ: model, tham số (độ dài tối đa, mức suy nghĩ, nhiệt độ), phạm vi dữ liệu, ngân sách, bật/tắt | Chỉ CIS đổi model theo stage trong admin; tham số rải trong code; TripPlanner chỉ dùng một phần cấu hình của CIS; CRM có cấu hình riêng theo đại lý | Bảng tham số theo stage × model; hồ sơ theo app (CIS, TripPlanner, CRM; Booking khi cần) |
| **Quản lý** (ngân sách, an toàn dữ liệu, kiểm tra sống) | Không lần gọi trả phí nào chạy mà không qua trần tiền; dữ liệu chỉ tới nơi được phép (theo hãng, vùng địa lý, tenant); biết trước khi một nguồn mất quyền hay hết tiền | Trần chi tiêu chỉ có hiệu lực ở những chỗ code nhớ bật nó; Jev không có trần trước khi gọi; một đường DataForSEO không có trần; TripPlanner vẫn gọi tiếp khi không đọc được số đã tiêu; mất quyền chỉ phát hiện khi việc thật hỏng; Jev có danh sách tenant được phép, LLM thì không | Trần bắt buộc ở cổng cho mọi nguồn; chính sách dữ liệu theo nguồn (hãng, vùng, tenant); kiểm tra sống định kỳ (chi phí nằm trong quyết định 2) |
| **Giám sát** | Một trang: nguồn nào sống, còn bao nhiêu tiền, đã chi bao nhiêu theo app / stage / tenant, độ trễ, tỉ lệ lỗi; cảnh báo ngay khi có chuyện | LLM có ô trạng thái trên trang admin, bản tin hằng ngày, đối soát hoá đơn; DataForSEO có số dư hằng ngày; Jev chỉ có số dư ước tính; Geoapify đếm credit; TripPlanner không có gì; không có độ trễ | Trang "Nguồn trả phí" chung, độ trễ theo stage, cảnh báo tức thì qua chuông admin và email vận hành đã có |
| **Truy vết** | Mỗi lần gọi (kể cả bị từ chối) để lại một dòng cùng dạng: app, stage, nguồn, model, tenant, job, độ trễ, kết quả, chi phí; xem được theo job và tour | 5 nơi ghi, mỗi nơi ghi một kiểu, không cộng gộp được; lần gọi bị từ chối ở CIS không để lại dòng; không có độ trễ; không xem được theo job | Một mẫu ghi chung cho mọi nhà cung cấp (sổ CRM cùng mẫu), màn xem theo job / tour |

## Từng nhà cung cấp: hôm nay và trong cổng

| Nhà cung cấp | Dùng cho | Hôm nay (31/10) | Trong cổng v2 |
|---|---|---|---|
| Bedrock acc3 (Claude, GPT trên Bedrock) | Gần hết stage viết, chấm, kiểm của CIS; soạn lịch trình TripPlanner | Bị chặn từ 29/10 (Error 002); là nguồn chính duy nhất | Một miền sự cố; luôn có đường dự phòng ở miền khác |
| Bedrock acc2 (Cohere Embed; chat: Nova, Llama, Kimi) | Embedding cho CIS và tìm kiếm TripPlanner | Embedding chạy được. Chat: acc2 không gọi được Claude hay GPT (nhà bán lại TrueIDC chặn), chỉ Nova, Llama, Kimi trả lời; chưa stage nào dùng chat trên acc2. Nếu bật, lần gọi chat đó sẽ bị ghi thiếu tài khoản nên không vào ngân sách (sửa ở bước 1) | Ghi đúng tài khoản; có thể làm miền thứ hai cho chấm / kiểm (quyết định 3) |
| Anthropic API trực tiếp | Đường thứ hai cho Claude | Đã chuẩn bị đường Dev, trần 150 USD/tháng; chưa nạp tiền, chưa có khoá | Đường dự phòng ấm, khác miền sự cố (quyết định 2) |
| OpenAI API trực tiếp | Dự phòng cuối cho vài stage chấm | Hết tiền | Giữ là dự phòng cuối, có trần, có kiểm tra sống |
| Azure OpenAI | Một đường GPT ngoài AWS, nếu sau này cần | Đã có code nối (làm ở AA-1002, có kiểm thử) nhưng chưa có tài khoản Azure, chưa bật nguồn nào, không tốn tiền; không phải code chết | Giữ code, không bật; chỉ bật khi cần thêm một đường GPT và anh đã duyệt chi phí |
| Bedrock Batch (acc3) | Viết lại tour hàng loạt (chạy theo lô) | Không ghi sổ (đã kiểm code: ba file chạy theo lô không có dòng ghi chi phí nào) | Đi qua cổng, ghi sổ như lần gọi thường |
| **Jev** | Quyết định có kiểu (chọn, chấm điểm), không ra chữ | Client riêng ngoài cổng; ghi hai sổ; không trần trước khi gọi; số dư chỉ ước tính; có danh sách tenant được phép | Một loại nguồn "quyết định" trong cổng; trần trước khi gọi (hết trần thì coi như Jev lỗi, việc vẫn chạy theo luật cũ); giữ danh sách tenant và các chế độ tắt / thử / áp dụng |
| **DataForSEO** | Khối lượng từ khoá, kết quả tìm kiếm Google, câu hỏi người tìm | Client riêng; sổ riêng; một đường chính không có trần; số dư đọc hằng ngày | Một loại nguồn "dữ liệu" trong cổng; trần bắt buộc ở mọi đường; giữ đọc số dư |
| DataForSEO (code cũ) | Không còn ai dùng | Code chết; nếu sống lại sẽ chạy không sổ, không trần | Xoá |
| **Geoapify** | Xác nhận toạ độ, hình dạng tuyến | Gói miễn phí 3.000 credit/ngày, code tự dừng ở 2.500; sổ riêng | Nguồn "dữ liệu" trong cổng; hạn mức là dữ liệu của nguồn |
| Bedrock Guardrails (CRM) | Lọc thông tin cá nhân trước khi gọi model | Đã có code trong bộ lọc của CRM, nhưng phần gọi model của CRM còn giả lập; không ghi chi phí | Đi qua cổng của CRM, có dòng chi phí |
| CRM (LLM) | Bản nháp AI cho đại lý | Cổng riêng, gọi model còn giả lập | Dùng chung lõi code; giữ cấu hình và sổ riêng trong CRM; sổ cùng mẫu với sổ chung |
| Mapbox | Bản đồ trên trình duyệt khách | Gọi thẳng từ trình duyệt, không ghi gì trong app | Ngoài đường gọi (không thể đi qua máy chủ); chỉ đưa vào trang giám sát và cảnh báo mức dùng |
| AWS Cost Explorer | Đối soát hoá đơn | Bấm tay, khoảng 0,01 USD mỗi lần đọc | Công cụ đối soát của cổng, không phải nguồn để route |
| Nguồn miễn phí (Google Drive, Overpass, tỉ giá) và kênh của tenant (Facebook, WordPress, mail) | — | Không mất tiền, hoặc tenant tự trả | Ngoài phạm vi; ghi trong sổ nguồn là "miễn phí" để biết dữ liệu đi đâu |

## Hình tổng thể

```mermaid
flowchart LR
  subgraph Apps["Các app"]
    CIS["CIS (viết tour, admin, trang viết nội dung cho đại lý)"]
    TP["TripPlanner"]
    CRM["CRM / Partner"]
    BK["Booking (khi cần)"]
  end
  subgraph GW["Cổng AI và dữ liệu (một bộ code dùng chung cho mọi app)"]
    CFG["Tuỳ biến theo app / stage: model, tham số, bật tắt"]
    REG["Nguồn + Họ model: nhà cung cấp, đường vào, miền sự cố, giá"]
    RT["Điều hướng: chính, dự phòng, giới hạn thời gian chờ"]
    POL["Quản lý: ngân sách, an toàn dữ liệu, kiểm tra sống"]
    CALL["Gọi: phần nối riêng cho từng nhà cung cấp"]
    LOG["Truy vết: sổ ghi chung"]
  end
  subgraph P["Nhà cung cấp"]
    B3["Bedrock acc3"]
    B2["Bedrock acc2"]
    BB["Bedrock Batch"]
    GR["Bedrock Guardrails"]
    AN["Anthropic API"]
    OA["OpenAI API"]
    AZ["Azure OpenAI (có code, chưa bật)"]
    JEV["Jev"]
    DFS["DataForSEO"]
    GEO["Geoapify"]
  end
  MON["Giám sát: nguồn trả phí, chi phí, độ trễ, cảnh báo"]
  MB["Mapbox (chỉ giám sát)"]
  CIS --> CFG
  TP --> CFG
  CRM -->|"lõi chung, cấu hình và sổ riêng"| CFG
  BK -.-> CFG
  CFG --> RT --> POL --> CALL
  REG -.-> RT
  CALL --> B3 & B2 & BB & GR & AN & OA & JEV & DFS & GEO
  CALL -.-> AZ
  CALL -->|"kết quả, chi phí, độ trễ"| LOG
  POL -->|"lần bị từ chối"| LOG
  LOG --> MON
  MB -.-> MON
  classDef dashed stroke-dasharray: 5 5
  class AZ,MB dashed
```

## Thứ tự làm

Luật chung: **không lần chạy trả phí nào khi anh chưa đồng ý; không đổi route nào khi anh chưa duyệt bản thiết kế
này.** Mỗi bước là một lát việc nhỏ, có bằng chứng. Cỡ việc tính theo phiên làm việc của agent (một phiên khoảng
nửa ngày).

| Bước | Làm gì | Chức năng nào trong 8 | Cỡ việc | Chi phí | Anh thấy gì khi xong |
|---|---|---|---|---|---|
| 0. Đo trước | Đếm trong sổ ghi: stage nào còn gọi qua đường cũ, chỗ nào còn dùng model cố định, để biết bỏ gì trước (chỉ đọc) | Điều hướng, Truy vết | Nửa phiên | 0 USD | Bảng số đếm; bước 4 bỏ đường nào là dựa vào số này |
| 1. Sửa lỗi không tốn tiền | Ghi đúng tài khoản cho lần gọi chat trên acc2; nhận đúng câu "hết tiền" của Anthropic để không gọi lại mãi; thêm trần cho đường DataForSEO đang không có trần; thêm trần trước khi gọi cho Jev; TripPlanner dừng gọi khi không biết đã tiêu bao nhiêu; xoá code DataForSEO cũ | Quản lý, Truy vết, Gọi | 1 phiên | 0 USD | Mỗi lỗi có bài kiểm thử xanh; bảng kiểm: mọi chỗ gọi trả phí đều có trần; không route nào đổi |
| 2. Anh duyệt (không phải việc code) | Anh đọc bản này, trả lời 3 câu ở dưới; phần ADR 0009 mà 3 câu phủ chuyển sang Accepted | — | Khoảng 1 giờ của anh | 0 USD | ADR 0009 được merge với trạng thái Accepted |
| 3. Sổ ghi chung và trang giám sát | Mỗi lần gọi (cả bị từ chối) có một dòng cùng dạng, có độ trễ; Jev, DataForSEO, Geoapify nối vào cùng dạng; màn xem theo job / tour; trang "Nguồn trả phí" với số dư, chi tiêu, lỗi, độ trễ | Truy vết, Giám sát | 2–3 phiên | 0 USD | Một trang trong admin cho thấy mọi nguồn trả phí với số thật của Dev; mở một job thấy từng lần gọi theo thời gian |
| 4. Sổ nguồn mở rộng, họ model, tham số | Jev, DataForSEO, Geoapify thành dòng trong sổ nguồn; miền sự cố; họ model và khả năng là dữ liệu; tham số theo stage × model; chọn model ở một chỗ duy nhất | Nguồn, Họ model, Tuỳ biến, Điều hướng | 3–4 phiên | 0 USD | Thêm nhà cung cấp hay model mới = một thay đổi cấu hình nhỏ, không sửa code; trong admin chỉ việc bật / tắt; vẫn chưa route nào đổi |
| 5. Độ tin cậy | Đường dự phòng ấm khác miền sự cố; kiểm tra sống định kỳ; giới hạn tổng thời gian chờ; tự tạm ngừng một nguồn đang lỗi liên tục; việc bị từ chối tự chạy lại sau; diễn tập chuyển dự phòng hằng tháng trên Dev | Điều hướng, Quản lý, Giám sát | 2–3 phiên | Theo quyết định 2: nạp 50 USD một lần, rồi khoảng 1–2 USD/tháng | Ô trạng thái trên trang admin hiện xanh cho hai miền sự cố; báo cáo diễn tập: tắt nguồn chính, stage chuyển sang dự phòng trong giới hạn thời gian, kèm chi phí |
| 6. Dùng chung cho các app, thử model mới | TripPlanner và CRM dùng lõi chung (CRM giữ cấu hình và sổ riêng). Model mới được thử từng bước nhỏ, so với model đang dùng, chạy song song không ảnh hưởng thật, rồi mới chuyển; lỗi thì quay lại. Trước lần đổi đầu tiên: đo mức hiện tại của model viết, kiểm model chấm với 40 mẫu anh gán nhãn (khoảng 2 giờ của anh) | Gọi, Họ model | 3–5 phiên | Mỗi model mới vài USD (thử nhanh dưới 0,10 USD; so sánh tối đa 50 tour khoảng 4 USD); mỗi lần chạy trả phí xin anh riêng | TripPlanner và CRM hiện cùng trang giám sát. Đổi model ở stage viết chính: chờ anh duyệt, kèm báo cáo so sánh, chi phí mỗi tour và độ trễ. Đổi ở stage chấm / kiểm: làm khi thử đạt, báo anh sau với cùng báo cáo đó |

**Vì sao đường dự phòng ấm ở bước 5, và không phải chờ tới đó.** Bước 5 làm cho việc dự phòng tự động (tự kiểm tra,
tự chuyển, diễn tập). Nhưng bài học 29/10 không cần chờ: khi anh chọn Có ở quyết định 2, đường Anthropic bật tay được
ngay sau bước 2 (hướng dẫn đã có: nạp tiền, tạo khoá, bật trong admin, rồi thử khoảng 5 tour, dưới 0,50 USD), trong lúc
bước 3–4 vẫn tiếp tục.

## Cần anh quyết định (3 câu)

1. **Phạm vi: một cổng cho mọi nhà cung cấp AI và dữ liệu trả phí** (LLM, Jev, DataForSEO, Geoapify, Guardrails).
   CRM dùng chung code của cổng nhưng giữ cấu hình và sổ riêng; đó là quy định đã có, giữ nguyên.
   - Đề xuất: **Có**, duyệt bản này và ADR 0009 như đang viết.
   - Nếu chọn Có: làm bước 3, 4 và 6; chi phí hạ tầng 0 USD, chỉ tốn thời gian code.
   - Nếu chọn Không thì: chỉ làm bước 1 (0 USD); Jev, DataForSEO, Geoapify giữ client và sổ riêng; vẫn 5 nơi ghi
     không cộng gộp được; không có trang chung. Chi phí 0 USD.
2. **Đường dự phòng ấm, khác miền sự cố, là bắt buộc**: nạp **50 USD** cho đường Anthropic API (đủ khoảng 800 tour
   viết lại, bước viết tốn khoảng 0,06 USD/tour), giữ trần chi **150 USD/tháng** đã đặt; kiểm tra sống hằng ngày mọi
   nguồn trên Dev (dưới 1 USD/tháng, riêng Anthropic dưới 0,03 USD/tháng); diễn tập chuyển dự phòng mỗi tháng (khoảng
   0,25 USD một lần). Cảnh báo đi qua chuông admin và email vận hành đã có, 0 USD.
   - Đề xuất: **Có**; sự cố 29/10 cho thấy chỉ một nguồn là dừng toàn bộ việc viết.
   - Nếu chọn Có: 50 USD trả trước một lần, dùng dần; chi đều khoảng 1–2 USD/tháng, cộng tiền gọi thật nếu phải
     chuyển sang Anthropic.
   - Nếu chọn Không thì: lần acc3 bị chặn tới, mọi stage viết lại dừng như 29/10 cho tới khi acc3 mở lại. Chi phí
     0 USD.
3. **acc2 được chạy model chat cho chấm và kiểm** (không cho stage viết chính, không cho stage của tenant). acc2 chỉ
   chạy được **Nova (Amazon), Llama 4 (Meta) và Kimi K3 (Moonshot)**, không phải Claude hay GPT (TrueIDC chặn). Tour
   viết bằng tiếng Anh, nên chỉ cần model viết tốt tiếng Anh. Mỗi model trên acc2 phải qua bước thử, so với model chấm
   hiện tại, trước khi chạy thật. Việc này thay quy định cũ "chat chỉ chạy trên acc3".
   - Vì sao cần khi đã có quyết định 2: Anthropic chỉ có Claude, mà model chấm phải khác hãng với model viết (Claude).
     Khi acc3 hỏng, model chấm GPT hôm nay không còn chỗ chạy (OpenAI API hết tiền). acc2 giúp phần chấm / kiểm vẫn
     chạy khi acc3 gặp sự cố, kể cả khi Anthropic cũng lỗi.
   - Lưu ý: acc2 "khác người trả tiền" với acc3 là sự thật hôm nay. Khi đổi cách thanh toán (dự kiến 01/12) hay acc2
     rời TrueIDC thì phải kiểm lại, vì rời TrueIDC có thể làm acc2 mất quyền AI.
   - Đề xuất: **Có**, chỉ cho chấm / kiểm; stage viết vẫn giữ Claude (Sonnet 5.5) cho tới khi bước thử chứng minh
     model khác không kém hơn.
   - Nếu chọn Có: thử 1–2 model, dưới 2 USD mỗi model; mỗi lần chạy trả phí vẫn xin anh riêng.
   - Nếu chọn Không thì: acc2 chỉ chạy embedding; khi acc3 hỏng, phần chấm / kiểm dừng (trừ khi nạp tiền OpenAI API).
     Chi phí 0 USD.

**Không cần trả lời bây giờ.** ADR 0009 còn 3 đề xuất được duyệt riêng (luật model viết / model chấm theo hãng, kèm 2
giờ anh gán nhãn ở bước 6; cấu hình nguồn chỉ đổi qua migration; vùng dữ liệu được phép cho tenant) và 4 việc hoãn
(vùng AWS thứ hai, lọc thông tin cá nhân cho TripPlanner, lưu nội dung prompt, luật chất lượng mới cho bước viết
tour). Mỗi điểm sẽ được trình kèm đề xuất khi tới bước cần nó.

## Phụ lục: tên kỹ thuật

Phần này dành cho engineer và agent. Nguồn: các audit S261 trong `docs/audits/2026-10-31-S261-llm-gateway-design-gap/`,
`docs/audits/2026-10-31-S261-llm-gateway-readiness/`, `docs/audits/2026-10-31-S261-llm-capacity-plan/`, bảng kiểm kê
nhà cung cấp trả phí S261 [`inventory.md`](inventory.md) (đọc code, không gọi live), và thiết kế đã duyệt
[S258 blueprint](../2026-10-29-S258-aws-org-blueprint/README.md) mục "AI / LLM Gateway".

**ADR liên quan** (tiền tố bắt buộc: CIS ADR khác root ADR cùng số):
root ADR 0001 quyết định 2 (Single Model Gateway, sẽ được sửa) và 4 (cost guard); root ADR 0001a (LLM chat chỉ trên
acc3, sẽ được sửa); root ADR 0008 quyết định 5 (ngoại lệ SELECT cấu hình gateway, sẽ đóng); root ADR 0008a §5–6 (CRM
có gateway và sổ riêng, giữ nguyên); root ADR 0018 (`aa-ai`, sẽ được sửa, có ghi chú trong cùng PR); CIS ADR 0005
quyết định 4 và 9 (catalog), CIS ADR 0006 §4–5 (luật writer/judge theo vendor), CIS ADR 0007 (Jev verdict, giữ
nguyên), CIS ADR 0008 (validate mọi vendor), CIS ADR 0012 (data scope theo stage); data standards DM-10.4 (bản sau).

**Sổ ghi hôm nay:** `shared.llm_call_log` (LLM CIS + TripPlanner, Jev cost), `shared.decision_log` (Jev verdict),
`shared.dfs_call_log` (DataForSEO), `geo.geocode_call` (Geoapify), `crm.llm_call` (CRM), `shared.cost_explorer_snapshot`;
không có sổ: Mapbox, Guardrails, Bedrock Batch (đã kiểm bằng grep: `s1_batch.py`, `s1_batch_ingest_job.py`,
`bedrock_batch.py` không có `record_call`, `llm_call_log` hay `cost_usd`).

**Registry hôm nay:** `shared.llm_provider_connection` (kind có `azure_openai`, chưa dòng nào), `llm_model_deployment`,
`llm_model_catalog`, `llm_role_config` (`allowed_scopes`, mig 311), `llm_model_alias`, `llm_provider_health`; Jev:
`shared.decision_question`, `shared.jev_tenant_allowlist`, `shared.jev_credit_topup`; ngân sách: `CIS
shared/cost_guard.py` (`PROVIDERS` = dfs, bedrock, openai, jev, geocoder, anthropic, azure_openai),
`connection_budget.py`.

**acc2 chat (ma trận truy cập 31/10):** Claude bị từ chối ("not available for channel program accounts"),
`openai.gpt-5.5` bị từ chối; Nova Lite / Pro / 2 Lite, Llama 4 Maverick / Scout (`us.`) và Kimi K3 trả lời.

**Bước 1 (0 USD), vị trí lỗi:**
- acc2 `account=NULL`: `CIS shared/llm_client/client.py:1375-1380` (chưa stage nào route chat sang acc2; lỗi sẽ lộ
  khi thêm Nova / Llama / Kimi).
- Anthropic 429 `enforced_spend_limit_reached` bị coi là throttled: `adapters/anthropic_messages.py:303`. Nguồn: tài
  liệu rate limits của Anthropic, trích ở S257 `docs/audits/2026-10-29-S257-llm-access-options/anthropic-api-evaluation.md:164-169`
  (429 khi chạm trần tier; 400 khi chạm trần workspace do mình đặt). Fixture dựng từ thân lỗi trong tài liệu, không
  nạp tiền chỉ để gây lỗi.
- DataForSEO không trần: `CIS services/seo_intelligence/handler.py:186` (`process_seo`).
- Jev không có `load_run_budget(..., "jev")`: `CIS shared/llm_client/decide.py`.
- TripPlanner fail-open: `TP backend/shared/llm_gateway.py:580-590`.
- Code chết: `CIS services/acp_produce/dataforseo.py` (chỉ test `test_aa298_dataforseo.py` import).
- Ngưỡng cứng cần thành dữ liệu: Jev low-credit 3 USD (`shared/jev_credit.py`), DFS
  `DFS_BALANCE_ALERT_THRESHOLD_USD` 10 USD (`admin_llm_ops.py:62`).

**Bước 3–6, ánh xạ sang thiết kế** (mã D lấy từ audit design-gap §3): D1 họ model (`llm_model_family`, bỏ CHECK vendor
đóng), D2 `api_style` xuống deployment, D3 capabilities hiệu lực + `stage_model_params`, D4 một dispatch pipeline (bỏ
`_legacy_chain`, vendor path, direct OpenAI sau khi đo ở bước 0; `model_tier` chỉ trong eval/probe), D5
`failure_domain` + bất biến dự phòng + route deadline + canary + circuit cấp connection + re-queue, D6 lớp lỗi
`truncated`, D7 thang thẩm định, D8 `model_maker` / `inference_geo` trong data scope, D9 cấu hình bằng migration, D10
bỏ `account_route` (sau khi đo ở bước 0), thay bằng cột role theo connection, D11 eval spend có scope. Điều kiện trước
mọi lần đổi route / họ model (gap §6): baseline Sonnet 5.5, judge calibration 40 mẫu, canary chéo đường
`s1_generate` trên anthropic-direct, contract smoke mỗi ứng viên.

**Chi phí, cách tính:** probe dưới 0,001 USD mỗi lần (blueprint checklist A4); probe mọi deployment Dev hằng ngày
dưới 1 USD/tháng khi tối đa 30 deployment bật; diễn tập ≈ 3 tour × 0,0768 USD (wave S249); 50 USD / 0,06 USD mỗi tour
cho `s1_generate` ≈ 800 tour.

**Issue:** AA-804 (ADR 0009, ledger v2, AI Use Register), AA-642 (dispatch, S3-rest, S8 lõi dùng chung, S7 batch, S12
dung lượng), AA-900 (thang thẩm định, judge calibration, R2 candidate arm), AA-1002 (đã Done-with-scope; S12 chuyển
đi), AA-820 (điều khoản tenant: hãng và vùng được phép), AA-842 (OTel / Langfuse tự host, đang hoãn vì chi phí),
AA-1004 (SCP cho us-west-2), AA-1016 (ngân sách AI theo tenant Content studio), AA-1015 (giới hạn TripPlanner), AA-964
(gateway CRM), AA-896 (alarm). N1 (độ tin cậy) và N2 (họ model) được tạo nếu anh chọn Có ở quyết định 1.

**Langfuse:** Cloud bị loại (dữ liệu ra ngoài AWS, trái CIS ADR 0012 và root ADR 0008a); tự host hoãn (ước 60–150
USD/tháng hạ tầng, chưa kiểm, theo audit AA-842 `docs/audits/2026-10-29-S257-aa842-otel/README.md:487`; ClickHouse
trên Fargate, thêm kết nối vào RDS chung). Sổ ghi chung + màn truy vết tự làm, 0 USD hạ tầng.
