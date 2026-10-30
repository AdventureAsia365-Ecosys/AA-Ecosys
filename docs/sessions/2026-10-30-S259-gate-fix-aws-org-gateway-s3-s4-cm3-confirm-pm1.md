# S259 (30/10/2026): gỡ cổng deploy, tài khoản quản trị AWS mới, LLM gateway S3+S4, C-M3 xác nhận, P-M1 P1, báo cáo R3/R4

Tác nhân: **Claude Code** (Ultracode; workflow nhiều lane, tối đa 2 lane nặng cùng lúc vì RAM/swap). 30/10 08:14 →
~13:50 +07. MFA acc2 làm mới 08:46 (hạn ~16:45). Không chạm hạn mức phiên. Số liệu cuối:
`docs/audits/2026-10-30-S259-session-close/state-snapshot.md`.

## Quyết định của tech lead (trong phiên)

- 08:14: agent tự chọn 20 việc từ master plan + tồn S258, coi như đã duyệt theo kế hoạch; chạy liên tục, không hỏi.
- ~09:10: tech lead tạo **tài khoản AWS quản trị mới** (admin-AA); làm tay: root MFA, bật quyền billing cho role, tạo role
  bootstrap (theo đoạn JSON agent đưa), bật IAM Identity Center ở us-west-1 (chọn **Single-Region** theo đề xuất, tránh
  phí KMS), đăng nhập portal bằng AA-Admin.
- Tech lead: phần nào phát sinh phí trên tài khoản mới thì **báo trước** (đã lưu memory).
- ~10:15: tắt auto mode một lần cho apply IAM/OIDC CI + GitHub environment/secret + xoá role bootstrap.
- Hỏi đường LLM: kiểm lại toàn bộ model (xem dưới); quyết nạp credit OpenAI / khoá Anthropic vẫn chờ tech lead.

## Done / ship

| Việc | Kết quả |
|---|---|
| AA-993 **Done** | Cổng schema-gate: chấp nhận probe độc lập mới nhất xanh sau một run chỉ đỏ probe (CIS #1167, Booking #153, Partner #126; review độc lập bắt 1 fail-open, đã sửa). Deploy CIS khi job relocate đang chạy (job nhả về hàng đợi rồi chạy tiếp, không mất/không trùng). Mig 307 đi trọn chuỗi bot không bước tay. Lead time CIS (trung vị) **59 → 10 phút**. ADR 0017 **Accepted** (root #364) |
| AA-789 **Done** (with scope) | Duyệt theo kế hoạch; phần LLM chuyển AA-1000 |
| AA-1002 gateway **S3** | CIS #1168 `b7cd4cfa` live: route trải theo deployment, alias key cũ (tắt), account từ registry, mig 307 tự áp; snapshot 37 route không đổi |
| AA-1002 gateway **S4** | CIS #1176 `1878349b` live: circuit breaker + limiter + bảng health (mig 309 tự áp) + tab Connections, grant sửa connection (mig 310, DB Migrate). Live: test connection openai-direct → `quota_exhausted` $0 |
| Phân loại lỗi | CIS #1173: OpenAI 429 "no credits remaining" = `quota_exhausted` |
| AA-1003 R1/R2 live | Qua cổng mới cùng #1167; 63 báo cáo; lịch 02:03Z sinh EX-04/EX-06/TP-03/OPS-12 |
| AA-1003 **R3** | CIS #1169 `6372fbed` + root #361: 8 báo cáo tiền chạy live (EX-01 tuần 144,05 USD, FI-03 LLM T9 42,79 USD) |
| AA-1003 **R4** phần 1 | CIS #1174 `02b1f4f3` + root #366: sửa 2 lỗ R3 (số tour = 892, probe CloudWatch); CIS-01/06/07, OPS-13/14 live |
| AA-1000 | CIS #1172 `a38b3dc5` live, chế độ off; mig 308 (Infra #517 + DB Migrate). Hiệu chuẩn/shadow chờ LLM |
| AA-919 | Census FB = 1; chọn 38 → đóng băng 34 mẫu; panel 3 góc nhìn + verifier (33/34 đồng thuận, 1 quyết theo chính sách nguồn); golden set **1.3.0 apply** (134 mục; t9_social 32 cặp hiệu chuẩn, đo được); vân tay CIS #1171 |
| **C-M3** (AA-952 lát 1) | Booking #155 (b2b 1.2) + root #363 + Partner #128: dòng AA từ bộ giữ chỗ được chấp nhận, Booking xác nhận sau cọc. Proof live **16/16 PASS** |
| **P-M1 P1** | Agency tổng hợp Atlas & Hearth: mời studio editor (phase 2 5/5) → đổi vai trò → CRM nhận **4,7 s / 37,9 s**; CIS không cấp vai trò CRM 3/3 |
| AA-994 | S6d Booking #156 `45de036` (+ 2 gap Figma: lưới ảnh Hotels, menu dòng hoá đơn/thanh toán; layout 281/281); S6b PR1 CIS #1175 `5f162b5c` |
| AA-1004 ngày 1 | Infra #513/#514/#515 + root #360 (ADR 0018 Proposed): org, 3 OU, 3 SCP, org trail, budgets, Identity Center, CI OIDC; drift management exit 0; role bootstrap đã xoá. ~1–1,5 USD/tháng |
| AA-997 | 33 mẫu aa997.3 đọc từng dòng (6 đúng, 21 sai do tuyến ngày bay, 6 nửa); chuỗi relocate aa997.3 + v2 dòng `llm`: ngày 1 830 dòng, 220 xác nhận, 0 lỗi, $0; còn 1.005 dòng (31/10) |
| Release | CIS 0.17.0 (#1150); 0.18.0 / Booking 0.14.0 / Partner 0.11.0 đang merge lúc chốt |

## LLM (kiểm 30/10 11:20)

Mọi model sinh văn bản FAIL: Bedrock acc3 Error 002 (Claude Haiku/Sonnet/Opus 5.x, GPT-5.6/6 Luna, GPT-6 Astra, key cũ
haiku/sonnet); OpenAI trực tiếp 429 hết credit. Chỉ Cohere Embed v4 (acc2) chạy. GPT-5.6 Luna không có đường OpenAI
(thêm được bằng 1 dòng deployment).

## Sự cố / bài học (đã chuyển vào `skill/aa-lessons/lessons.md`)

1. File test chép sang Booking/Partner đỏ `ruff format` (CIS không chạy format).
2. `mergeq.sh` báo exit 4 đúng lúc queue vừa merge (#128, #156 thật ra đã MERGED).
3. **boto3 qua hook `sitecustomize` rơi về khoá tĩnh acc3** — dry run Cognito tra nhầm tài khoản (không ghi gì); sửa bằng
   botocore session + JSONFileCache + kiểm account = acc2.
4. Auto mode chặn apply IAM/OIDC → gom cửa sổ.
5. FK mới (307 alias, 309 health) làm đỏ test integration cũ (259, 304, 306) → grep `DELETE/DROP` + Postgres local.
6. Số migration theo `main` lúc merge (đổi 309→308, 310/311→309/310).
7. Layout-mock Booking đo bản `.next` cũ nếu không build lại.

## Jira

Nháp PR-22, PR-24, PR-25, PR-26 ở `docs/audits/2026-10-30-S259-session-close/jira-drafts.md` (gộp nháp S258),
**chưa đăng**: tech lead bảo gom tiếp sang phiên sau (S260); bỏ PR-27 (hạ tầng là việc kỹ thuật).

## Chi phí

LLM: ~$0 (mọi lệnh sinh văn bản bị từ chối; 1 lệnh embedding ~0,00001 USD). Geoapify: 1.019 request, $0 (gói Free).
AWS mới: tài khoản quản trị ~1–1,5 USD/tháng (KMS + S3 trail); acc2 không thêm dịch vụ.

## Việc cần làm đầu phiên sau (S260)

1. AA-997: chuỗi relocate xong (~31/10) → audit lại độ chính xác → AA-990 recheck_14.
2. AA-1002: ảnh tab Connections + S5 (chính sách thành dữ liệu); bật một đường LLM khi tech lead nạp credit OpenAI hoặc
   đưa khoá Anthropic.
3. AA-994: thêm biến thể nút (link/icon/segmented) trong kit core CIS → xong 66 nút Booking (S6d) + S6b PR2.
4. AA-1003 R4 phần 2; AA-952 lát tiếp.
5. Đến hạn: AA-896 báo cáo chi phí tháng + C8 capacity review (phiên đầu ≥ 01/11); C4.3 W45 (từ 02/11).
6. Có LLM: AA-919 kappa, AA-790, AA-1000 hiệu chuẩn, AA-900 eval.
