# Nhân viên content chỉnh sửa nội dung tour trong CIS

## 1) Trả lời ngắn

- **Nhân viên content sửa được tour, nhưng CIS chưa có trang sửa tour đúng nghĩa.** Admin, content_lead và content sửa trong drawer của tour, bằng các ô sửa tại chỗ. Ô tự lưu khi click ra ngoài. Không có bản nháp, không có so sánh trước/sau (diff), không có nút "xuất bản" và không ghi ai đã sửa gì.
- **Sửa ở đâu:**
  - Sai **sự thật** (lịch trình từng ngày, bao gồm/không bao gồm, thời lượng, nhà cung cấp): sửa ở **tour gốc** (raw).
  - Chỉ sai **câu chữ**: sửa ở **bản AI viết**, rồi xuất bản lên Master.
  - **Không sửa thẳng Master và không sửa atom**, vì cả hai bị ghi đè ở lần chạy sau.
- **Đề xuất:** làm trang **Tour editor** trong CIS, có 2 làn: "Sự thật" và "Câu chữ". Mỗi lần sửa tạo một phiên bản mới, có lý do và diff, được kiểm lại rồi mới xuất bản. Master đã sửa tay bị khoá để wave không ghi đè. Ước tính 16–20 ngày công. Hạ tầng 0 USD, chỉ tốn tiền LLM khi chạy lại.

## 2) Hiện trạng (đã kiểm trong code)

| Hạng mục | Thực tế |
|---|---|
| Vai trò CIS (9) | admin, content_lead, content (Content Team), tenant_qa, customer_success, support, finance, ai_ops, viewer (`apps/AA-CIS-App/api/core/staff_authz.py:163-210`; nhãn hiển thị ở `frontend/lib/rbac.ts:419-429`) |
| Ai sửa được nội dung tour | admin, content_lead, content, nhờ quyền `content.write` + `review.act` (`staff_authz.py:156,180`). Chỉ admin và content_lead bật/tắt được Master và sửa được atom (`staff_authz.py:164-178, 451-459, 538-539`) |
| Vai trò khác | tenant_qa chấm chất lượng, ai_ops lo AI và chi phí, viewer chỉ đọc. customer_success, support, finance không đọc được nội dung tour (`staff_authz.py:182-208`) |
| Sửa tour gốc | Tab Original gọi `PATCH /admin/tours/{id}/raw`. Lệnh này UPDATE thẳng `raw_tours`, không ghi người sửa, không giữ bản cũ. Sau đó nó xếp một job `source_fanout` 0 USD. Job này chỉ đánh dấu S1/T2/T9 là "nguồn đã đổi", không chạy lại gì (`api/routers/admin_pipeline/tour_detail.py:401-446`; `services/quality/source_fanout.py:1-35`) |
| Sửa bản AI viết | Tab Rewrite và Review Queue ghi đè bản `generated_content` **mới nhất**, có thể không phải bản đang live, và đặt `human_edited=true` (`tour_detail.py:501-577`) |
| Lên Master | Chỉ approve (Review Queue) hoặc promote mới chép text vào `published_tours`. Sau đó hệ thống atomize lại và đánh dấu các bản phụ thuộc (`services/export/handler.py:601-769`) |
| Lỗ hổng | (1) Approve bắt kiểm lại bản sửa tay, promote thì không (`admin_pipeline/versions.py:42-56`, so với `v1_pipeline.py:586-597`). (2) Wave và S1 có thể ghi đè Master đã sửa tay; chỉ recompose bỏ qua bản sửa tay (`s1_recompose_store.py:147,175`). (3) Atom sửa tay mất khi atomize lại. (4) Review Queue không sửa được `aa_itineraries`. (5) Drawer hiện ô sửa cả cho vai trò không có quyền ghi; lưu sẽ bị từ chối (`TourDetailPanelV2.tsx:397`) |
| Tạo tour mới | Chỉ qua upload Excel (`admin_pipeline/uploads.py:20-59`) |
| Mẫu làm tốt đã có | Supply content và AA content: phiên bản bất biến, đi từ nháp tới xuất bản (`apps/AA-CIS-App/CONTEXT.md:2406-2443`) |

## 3) Thị trường làm thế nào

- **Tourplan, Lemax (hệ thống của DMC/tour operator):** product master có cấu trúc (ngày, dịch vụ, bao gồm, nhà cung cấp), do đội product sửa. Mô tả marketing là một lớp riêng, và mọi thay đổi đều có lịch sử.
- **GetYourGuide, Viator (phía nhà cung cấp):** nhà cung cấp sửa sản phẩm thì bản sửa vào hàng chờ duyệt chất lượng, duyệt xong mới lên kênh bán.
- **Điểm chung:** tách **sự thật vận hành** khỏi **câu chữ bán hàng**. Mỗi lần sửa có phiên bản, tên người sửa, lý do và bước duyệt. Kênh bán được báo ngay khi có thay đổi.

## 4) Phương án

| | A. Vá chỗ đang có | B. Tour editor 2 làn, có phiên bản (**chọn**) | C. Product master có cấu trúc kiểu Tourplan |
|---|---|---|---|
| Làm gì | Bắt promote kiểm lại như approve, ẩn ô sửa theo quyền, ghi audit | Sự thật có lịch sử sửa, câu chữ sửa tay thành phiên bản bất biến; nháp → diff → kiểm lại → xuất bản; khoá Master | Bỏ text tự do; ngày, dịch vụ, bao gồm thành bảng có cấu trúc, gắn nhà cung cấp trong Booking |
| Ngày công | 3 | 16–20 | 40+ |
| Ưu | Nhanh, 0 USD | Đủ chuẩn nghề, dùng lại mẫu supply content | Chuẩn nhất |
| Nhược | Vẫn không có nháp và lịch sử | Sự thật vẫn là text | Phải làm lại A1–A3, chưa cần lúc này |

Chọn **B**, gồm luôn A ở bước đầu. C để sau khi có prod.

## 5) Thiết kế khuyến nghị

**Chủ dữ liệu:** CIS (ADR 0002, 0004a). App khác chỉ đọc view, đại lý không ghi gì vào catalogue.

**Dữ liệu** (migration CIS; thêm cấu trúc mới trước, khoá cách ghi cũ sau):
- Bảng mới `silver_aa_internal.raw_tour_revision`: tour_id, revision_num, source (`excel_import` hoặc `staff_edit`), before/after (jsonb), actor, reason, created_at. Bảng chỉ cho thêm dòng, có trigger chặn sửa và xoá. Mỗi lần import hoặc sửa tay ghi 1 dòng.
- Mở thêm các trường tour gốc hiện chưa sửa được: `src_subtitle`, `best_time_to_go`, `activities`.
- `generated_content`: thêm `origin` (`llm` hoặc `human`) và `parent_version_num`. Sửa câu chữ tạo **phiên bản mới**, không ghi đè. Bước cuối: trigger chặn UPDATE nội dung, giống CIS 278.
- `gold_aa_internal.published_tours`: thêm `human_lock_at`, `human_lock_by`. Wave, S1 rerun và promote tự động không được ghi đè Master đang khoá. Muốn ghi đè phải mở khoá rõ ràng.
- Audit: ghi vào bảng `acp_shared.audit_log` sẵn có. Bảng này chỉ cho thêm dòng và có chuỗi chống sửa (`docs/architecture/db-schema-reference.md:475-503`).

**Màn hình** `/admin/tours/{id}/edit` (mục CIS Content):
1. **Làn Sự thật:** form theo các trường của `raw_tours`, bắt buộc nhập lý do, hiện số bản T2/T9 bị ảnh hưởng. Nút "Chạy lại từ sự thật" báo trước chi phí (USD/tour lấy từ `llm_call_log`). Bản mới đi qua Review Queue.
2. **Làn Câu chữ:** sửa được mọi trường `aa_*`/`seo_*`, kể cả lịch trình, mô tả, thẻ mobile và og. Có diff với Master đang live, có xem trước. Bước kiểm lại tự chạy, rồi mới bấm **Xuất bản**.
3. Banner "Bản nháp: khách chưa thấy" và một tab lịch sử chung cho cả hai làn.
4. Drawer cũ chỉ để xem, có nút "Mở editor".
5. **Tạo tour tay:** form tạo một dòng staging và đi chung luồng import. **Bắt buộc chọn nhà cung cấp của AA** từ view nhà cung cấp của Booking.

**Sau khi xuất bản:** vẫn chạy `process_export` như hôm nay (atomize lại, segment, đánh dấu bản phụ thuộc), rồi đặt khoá. Thêm 3 việc:
- Báo TripPlanner ở **mọi** lần xuất bản. Hiện chỉ sự kiện lifecycle (vd. khôi phục tour) mới được báo ngay; còn lại TripPlanner chờ cache 30 phút.
- CRM báo đại lý "Tour gốc đã cập nhật". Đổi sự thật thì bản T2 tự làm mới (có trần chi phí). Chỉ đổi câu chữ thì giữ nguyên T2.
- Booking đọc view mới. Trip case đã báo giá giữ bản chụp cũ (**chưa kiểm**).

**Quyền:**

| Việc | Vai trò |
|---|---|
| Sửa nháp (cả hai làn) | content, content_lead, admin |
| Xuất bản câu chữ | có `review.act` và bản đã qua kiểm lại; promote cũng phải qua cùng cổng này |
| Mở khoá Master, tạo tour tay, chạy lại có trả phí | content_lead, admin |
| Đọc | mọi vai trò có `content.read` |

## 6) Lộ trình (mỗi bước là 1 PR giao được)

| Phiên | Bước | Ngày công | Chi phí |
|---|---|---|---|
| 1 | Phương án A: promote phải qua cổng kiểm lại, ô sửa trong drawer hiện theo quyền (`can()`), ghi audit khi sửa tour gốc, Review Queue sửa được lịch trình | 3 | 0 USD |
| 1–2 | Migration thêm: bảng lịch sử sửa, cột `origin`, cột khoá; wave/S1 tôn trọng khoá | 3–4 | 0 USD |
| 2–3 | Trang Tour editor, làn Câu chữ: phiên bản mới, diff, xuất bản | 4–5 | 0 USD |
| 3 | Làn Sự thật + chạy lại có báo giá trước | 3–4 | LLM theo lượt chạy, trong trần Dev |
| 4 | Báo TripPlanner, thông báo trong CRM, làm mới T2 có trần | 3 | LLM T2 nếu bật |
| 4 | Tạo tour tay gắn nhà cung cấp AA; bật trigger chặn sửa phiên bản | 2–3 | 0 USD |

## 7) Cần chốt

1. **Nhà cung cấp gửi lại Excel sau khi nhân viên đã sửa: bên nào thắng?** Đề xuất: bản sửa tay thắng. Lần import sau hiện diff từng trường để nhân viên chọn.
2. **Có cần hai người (người sửa không tự xuất bản)?** Đề xuất: ở Dev cho tự xuất bản. Từ prod, content sửa thì content_lead xuất bản.
3. **Đại lý hiện sửa được câu chữ bản T2 của mình và có "Facts Entries" (giá, điều khoản riêng). Như vậy có trái quy tắc "đại lý không có dữ liệu" không?** Đề xuất: giữ quyền sửa giọng văn T2 nhưng chặn đổi sự thật. Facts Entries chỉ còn markup và điều khoản bán, không có dữ liệu sản phẩm.
4. **Đổi sự thật thì có tự chạy lại T2 cho đại lý (trả phí) không?** Đề xuất: có, với trần chi phí tháng chỉnh được trong admin.
5. **Có cho tạo tour tay không qua Excel?** Đề xuất: có, nhưng bắt buộc gắn nhà cung cấp AA và content_lead duyệt.
6. **Có đổi trường `provider` từ text sang ID nhà cung cấp của Booking không?** Đề xuất: có, làm cùng bước tạo tour tay.
