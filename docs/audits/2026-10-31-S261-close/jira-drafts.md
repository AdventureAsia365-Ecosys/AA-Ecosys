---
id: OPS-08-s261-jira-drafts
title: "S261 Jira drafts (rolled over to S262)"
description: "Nháp Jira S261 chưa soạn, chưa đăng: chuyển sang phiên tiếp theo cùng ngày (S262), kèm danh sách việc sản phẩm đã ship mà S262 cần báo."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-953, AA-962, AA-966, AA-945, AA-955, AA-961, AA-967, AA-952, AA-997, AA-1014]
---

# S261 — nháp Jira

**Chưa soạn/đăng: theo lệnh tech lead 31/10, nháp Jira chuyển sang phiên tiếp theo cùng ngày (S262).**
Nguyên văn: "lưu ý nháp jira lưu sang cho phiên tiếp theo ngay sau đây cùng ngày làm việc luôn". S262 soạn một lần,
đưa tech lead duyệt một lần rồi mới đăng (skill `aa-jira-update`; memory `jira-no-tech-decisions`,
`jira-claims-need-live-evidence`). Mọi số liệu lấy từ `state-snapshot.md` và bằng chứng trong
`docs/audits/2026-10-31-S261-evidence/`.

## Việc sản phẩm đã ship S261 cần báo ở S262

CRM (epic CRM trên Jira; chỉ báo phần đã kiểm live, kèm ảnh trong thư mục bằng chứng):

- **AA-953 — portal theo từng người** (Partner #145, crm-029): chọn "bạn là ai", trang riêng mỗi khách, chuyến bay,
  giấy tờ, quét hộ chiếu, mời bạn đồng hành; live 13 mục đạt. Ảnh: `AA-953/`.
- **AA-962 — onboarding + nhập dữ liệu** (Partner #146, crm-030): checklist bắt đầu, nhập khách theo pha có chạy thử,
  gộp trùng, trang Kết nối, mẫu hỏi khách có bên kiểm soát dữ liệu; live đạt + e2e Dev xanh. Ảnh: `AA-962/`.
- **AA-966 — báo cáo + insight** (Partner #144, crm-031; root #391): phễu, tiền, công nợ, đội, chỉ số thành công, CSV;
  AA đọc insight theo quý, chỉ ô đã công bố. Ảnh: `AA-966/`.
- **AA-945 — email trong CRM**: trả lời mẫu, ghi chú nội bộ, nháp tự lưu/khôi phục sau tải lại; Done-with-scope (M365 +
  SMTP + lịch tách sang AA-1011). Ảnh: `AA-945/`.
- **AA-955 — ký điện tử v1**: mã hết hạn bị từ chối, bắt chấp nhận lại điều khoản mới, waiver + từ chối ký được niêm
  phong; Done-with-scope (PDF PAdES tách sang AA-1012). Ảnh: `AA-955/`.
- **AA-961 — banner sự cố** (duty of care): đại lý báo sự cố một chuyến → banner trên trang chuyến + task, gỡ → banner
  hết; chạy live trên Dev. Ảnh: `AA-961/`.
- **AA-967 — xuất / xoá dữ liệu khách**: xuất dữ liệu, chạy thử xoá, xoá thật một khách tổng hợp có biên nhận, chạy
  thử lại trả "không còn"; retention-log ghi dòng. Ảnh: `AA-967/`.
- **AA-952 — hoá đơn và thanh toán (một phần)**: khách báo đã chuyển khoản, gia hạn giữ chỗ một lần, giữ chỗ lại khi cọc
  trễ, nhắc quá hạn; ô thanh toán chờ khách chấp nhận lại điều khoản (Partner #143, #148); live 15 mục đạt. Còn hai mốc
  kiểm theo giờ (nhắc nợ ≥ 18:10Z 31/10, link hết hạn ≥ 04:35Z 02/11) → báo "một phần", chưa báo xong. Ảnh: `AA-952/`.
- **Video review CRM (AA-1014)**: tooling 21 đoạn xong (root #396), mẫu R01 + R03 (EN + VI, phụ đề đổi được) ở
  `.tmp-session/S261/video-samples/`; đã lên Drive: **chưa kiểm**. Chỉ nhắc khi có link Drive; video đầy đủ quay ở
  Session B (trước 10/11).

Địa điểm:

- **AA-997 — độ chính xác toạ độ địa điểm (tiến độ)**: luật mới aa997.4 giữ điểm đúng mà ngày tour xác nhận (CIS #1193);
  chuỗi kiểm lại chạy tiếp ~00:12Z 01/11. Chỉ báo tiến độ, số % chốt sau audit 01/11 (báo cáo
  `docs/audits/2026-10-31-S261-aa997-report/` còn chỗ trống).

## Không đưa lên Jira

- **Quyết định cổng AI v2** (root ADR 0009, root #397; AA-804, AA-1017, AA-1018): hạ tầng / kiến trúc là việc của tech
  lead (memory `jira-no-tech-decisions`) → **không đưa lên Jira**.
- Vá chuỗi quyền IAM (Infra #541), đường Anthropic Dev (Infra #549/#550), case AWS acc3: kỹ thuật, không đưa lên Jira.

## Ứng viên cho một trang báo cáo chủ doanh nghiệp (từ review kiến trúc S261)

Gom các mục BO-1, BO-4, BO-5, BO-6, BO-7, BO-8, BO-9, BO-13 của
`docs/audits/2026-10-31-S261-architecture-review/` vào **một** trang báo cáo cho business owner (memory
`owner-report-one-artifact`, `thu-links-via-jira`): đề xuất bình tĩnh, có phương án và chi phí, số Dev ghi rõ là chưa
ổn định. S262 quyết có làm trang này cùng đợt nháp Jira hay để phiên sau; link (nếu có) đi trong nháp Jira, không gửi
lẻ qua Zalo.

## Kết quả đăng

Chưa đăng (chuyển S262).
