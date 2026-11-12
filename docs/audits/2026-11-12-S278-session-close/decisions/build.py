import json
SRC = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-10-S275-session/decisions/index.html"
OUT = "/home/nghiep/projects/AA-Ecosys/.tmp-session/S278/decisions/index.html"
def o(v, t, d="", rec=False):
    x = {"v": v, "t": t, "d": d}
    if rec: x["rec"] = True
    return x
Q = [
 {"grp":"Nội dung (M2a / ADR 0020)","id":"d1-content-share","tag":"D1 · luật 60 %","title":"Giữ luật ≥ 60 % sức làm cho chất lượng nội dung (S279–S292)?",
  "ctx":"Luật từ S262/S265 để CRM không lấn R4/R5/R7. R4, R5, R7 nay đã xong. S276 giữ (5/8 issue), S277 tụt (~5/12). Bảng slot nháp giữ được 35/58 slot = 60 %.",
  "facts":["Đếm theo slot issue mỗi phiên, không tính các mục kiểm theo ngày"],
  "opts":[o("keep60","Giữ ≥ 60 % nội dung","",True),o("50","Hạ xuống 50 %"),o("drop","Bỏ luật, xếp theo giá trị")]},
 {"grp":"Nội dung (M2a / ADR 0020)","id":"d2-m2b","tag":"D2 · mốc mới","title":"Tách mốc mới M2b “Chất lượng nội dung đã chứng minh”?",
  "ctx":"Tiêu chí M2a hiện chỉ là luật chi phí, AA-741 (xong), AA-788, Writing Lab — không đo bài có tốt lên không. ADR 0020 có mục tiêu: tỉ lệ bài blog T9 đạt ngay lần đầu từ 2 % lên ≥ 30 % (đích 50 %), trung vị ≤ 5 lượt gọi model và ≤ 0,25 USD mỗi bài.",
  "facts":[],
  "opts":[o("m2b","Tạo M2b: W2–W5 đóng (AA-1048, 1050, 1051) + 3 mục tiêu ADR 0020 đo trong một báo cáo","",True),o("keep","Giữ M2a, chỉ tick cái đã xong")]},
 {"grp":"Nội dung (M2a / ADR 0020)","id":"d3-w2-fallback","tag":"D3 · AA-1048","title":"Nếu gom class rồi vẫn không đủ 20 vi phạm thì làm gì?",
  "ctx":"Đầu phiên anh đã chọn đo class gộp trước (vd. fact.* của t9_blog ≈ 21). Câu này chỉ dùng khi lượt đếm lại hôm nay vẫn dưới 20.",
  "facts":["Lane AA-1048 đang dựng script đếm lại (thêm bộ nhãn t2@2) — kết quả trong phiên này"],
  "opts":[o("seed-paid","Sinh thêm vi phạm thật bằng một lượt nhỏ trả phí, nằm trong trần 2 USD của R1","",True),o("n10","Sửa ADR 0020 cho phép n_pos ≥ 10 cho class đầu (hiệu chuẩn yếu hơn)"),o("wait","Chờ nhãn tích luỹ hằng tháng (chậm, nhiều tuần)")]},
 {"grp":"Nội dung (M2a / ADR 0020)","id":"d4-tl11","tag":"D4 · TL-11","title":"Khi nào gỡ băng TL-11 (writing memory + eval: AA-790, 920, 921, 922, 1000)?",
  "ctx":"TL-11 (S262) đóng băng tới khi blog T9 chạy trọn một vòng. Chặn thứ hai (không có đường LLM) đã hết: key Anthropic direct chạy từ S269, OpenAI có trần 10 USD.",
  "facts":[],
  "opts":[o("1077-and-1050","Gỡ khi AA-1077 đóng với một vòng T9 sạch VÀ AA-1050 bật enforce cho ít nhất một class đã đo","",True),o("1077","Gỡ ngay khi AA-1077 đóng"),o("m2b","Giữ băng tới báo cáo M2b")]},
 {"grp":"Nội dung (M2a / ADR 0020)","id":"d5-w5-yes","tag":"D5 · AA-1051","title":"Duyệt trước 4 lượt chứng minh trả phí W5 (mỗi lượt chạy khi cổng của nó xanh)?",
  "ctx":"Trần ADR 0020 D12: eval null ≤ 5 USD, T9 ≤ 15, S1 ≤ 8, T2 ≤ 5 (tổng ≤ 33 USD), tiền thẻ Anthropic/OpenAI. Mỗi lượt chỉ chạy sau W2 R1 + W4 (quyết định S275).",
  "facts":[],
  "opts":[o("all-now","Đồng ý cả 4 ngay, mỗi lượt chạy khi cổng xanh, báo chi phí từng stage","",True),o("one-by-one","Duyệt từng lượt khi sẵn sàng"),o("not-now","Chưa trong đợt này")]},
 {"grp":"Nội dung (M2a / ADR 0020)","id":"d6-openai-cap","tag":"D6 · trần OpenAI","title":"Trần cứng OpenAI 10 USD/tháng trong lúc chạy W4/W5: giữ hay nâng?",
  "ctx":"Nếu thước đo claim được ghim là GPT-6 Luna (OpenAI), W4/W5 có thể chạm trần 10 USD giữa chừng; gateway từ chối và lượt chạy dừng (không tự đổi model). Đầu phiên hôm nay OpenAI tháng 11 mới tiêu 0,96 USD.",
  "facts":["Số kiểm live 12/11: openai-direct 0,96 / 10 USD"],
  "opts":[o("keep10","Giữ 10 USD; kiểm số đầu mỗi phiên, chỉ hỏi lại khi một lượt sắp vượt","",True),o("raise20","Nâng 20 USD tới 31/12, cảnh báo ở 80 %")]},
 {"grp":"Nội dung (M2a / ADR 0020)","id":"d7-aa788","tag":"D7 · AA-788","title":"Duyệt pilot AA-788 (20 bài) từ 19/11, ước 2–5 USD?",
  "ctx":"AA-788 đưa F12_scope, F14 thiếu độ dài và F9_brand_style thành chặn. Replay $0 đã xong; pilot 20 bài là bước cuối.",
  "facts":[],
  "opts":[o("yes5","Đồng ý, trần 5 USD, thử 3 bài trước","",True),o("wait","Chờ báo cáo M2b")]},
 {"grp":"Mốc và phạm vi","id":"d8-r7-visual","tag":"D8 · M-R7","title":"Tiêu chí R7 “test giao diện chạy với next start trong CI” — đóng thế nào?",
  "ctx":"TripPlanner chụp 1440/390 sáng/tối sau mỗi deploy (chỉ báo cáo), chưa phải check mỗi PR, nên lỗi bố cục chỉ thấy sau merge. Job theo PR không tốn tiền (Actions repo public). Tiêu chí “chat chuyển R8” không còn đúng: AA-1041 đã làm chat.",
  "facts":[],
  "opts":[o("A","Chấp nhận bản chạy sau deploy (đạt theo phạm vi), bỏ tiêu chí chat, đóng M-R7","",True),o("B","Tạo issue mới cho job test giao diện mỗi PR (check bắt buộc), rồi đóng")]},
 {"grp":"Mốc và phạm vi","id":"d9-mp2-video","tag":"D9 · M-P2","title":"Bỏ tiêu chí “video AA-855 vòng 2 (TripPlanner)” của M-P2?",
  "ctx":"Từ S271 ngừng quay video UAT định kỳ; bằng chứng là Playwright + CI + curl. Mọi tiêu chí khác của M-P2 đã có qua AA-1038 (Done 10/11).",
  "facts":[],
  "opts":[o("drop","Đánh M-P2 xong theo phạm vi; AA-855 để Backlog cho video ký duyệt của chủ doanh nghiệp","",True),o("record","Quay một video TripPlanner bây giờ")]},
 {"grp":"R8 và CRM","id":"d10-r8","tag":"D10 · R8","title":"Mở lát R8 nào trong đợt này?",
  "ctx":"R8 có 4 phần: gộp màn Booking staff vào AA Admin (chỉ sau khi xoá bảng B2C, AA-1061 ≥ 28/11), tên miền riêng của tenant (CloudFront + ACM), thêm ngôn ngữ ngoài en/vi (cần duyệt tiền dịch máy), API máy cho đại lý (chỉ khi tenant trả tiền yêu cầu).",
  "facts":[],
  "opts":[o("domain-only","Chỉ tên miền riêng của tenant (≈ 0 USD, ước tính); gộp màn Booking xét ở lần cắt S292","",True),o("plus-booking","Làm cả gộp màn Booking"),o("none","Không R8 trong đợt này")]},
 {"grp":"R8 và CRM","id":"d11-crm-order","tag":"D11 · CRM sau R3","title":"Thứ tự lane CRM, và AA-965 (AI cho dịch vụ phụ) bắt đầu luôn?",
  "ctx":"7 card tạm dừng được xếp “sau S280”. AA-965 từng chờ đường LLM, nay đã có qua gateway (pii_class us, trần AI R1). AA-1011 cần anh đăng ký app Entra; AA-1012 cần quyết định chứng chỉ prod lúc go-live. Mỗi card qua review bảo mật trước khi bật cho tenant pilot.",
  "facts":[],
  "opts":[o("with-965","AA-960 → 963 → 968 → 970 → 965 (thử dev ≤ 1 USD) → add-on Odoo nhỏ; AA-1011 khi có Entra; AA-1012 tới go-live","",True),o("no-965","Cùng thứ tự, bỏ AA-965"),o("pause","Dừng lane CRM, chỉ làm nội dung")]},
 {"grp":"R8 và CRM","id":"d12-unpark","tag":"D12 · AA-948 / AA-704","title":"AA-948 (fork bản đồ builder) và AA-704 (trợ lý AI trong app): mở lại?",
  "ctx":"AA-948 chờ R7 (“một engine, hai bề mặt”), cần anh quyết engine TripPlanner dùng chung + duyệt riêng tiền Mapbox. AA-704 chờ pilot mốc 2, control plane, AI notice, trần AI theo tenant — đều đã xong; nó thêm chi phí LLM mỗi câu hỏi (chưa báo giá).",
  "facts":[],
  "opts":[o("keep-parked","Giữ cả hai ở parked; xét lại ở lần cắt S292 khi có đại lý pilot dùng app","",True),o("948","Mở AA-948, báo giá Mapbox trước"),o("704","Mở AA-704, báo giá chi phí trước")]},
 {"grp":"R8 và CRM","id":"d13-new-issues","tag":"D13 · Linear","title":"Tạo issue mới trên Linear?",
  "ctx":"Đang mở 39 issue (gói Free tối đa 250). NEW-A: runbook đón đại lý pilot + chạy thử trên tenant giả (0 USD). NEW-C: add-on Odoo nhỏ hạng 45–53 (0 USD). NEW-D: tên miền riêng R8 (≈ 0 USD). NEW-B chỉ khi D8 = B.",
  "facts":[],
  "opts":[o("acd","Tạo NEW-A, NEW-C, NEW-D (+ NEW-B nếu D8 = B)","",True),o("a-only","Chỉ NEW-A"),o("none","Không tạo, gộp vào issue có sẵn")]},
 {"grp":"Chủ doanh nghiệp và prod","id":"d14-owner","tag":"D14 · Jira","title":"Gửi các mục cho chủ doanh nghiệp dạng đề xuất nhẹ trong nháp Jira cuối phiên?",
  "ctx":"Không chặn kế hoạch. Chưa có ngày go-live và đại lý pilot đầu tiên thì mốc “P2 trễ nhất tuần 3 của pilot” không bao giờ bắt đầu. Còn chờ: 10 giá trị mặc định M-OD (PR-26 comment 10636, hệ thống đang dùng đề xuất), điều khoản phí ngày khởi hành Booking (nháp S277), ký phụ lục Billing Transfer của TrueIDC.",
  "facts":[],
  "opts":[o("draft","Một nháp Jira trên epic liên quan: đề xuất khung thời gian pilot + các mặc định còn mở, anh duyệt cuối phiên","",True),o("hold","Giữ lại tới báo cáo M2b")]},
 {"grp":"Chủ doanh nghiệp và prod","id":"d15-p0","tag":"D15 · AA-1004","title":"Chạy AA-1004 P0 lát 2–4 (chuyển stack CIS, CRM, TripPlanner vào modules/environment) ngay?",
  "ctx":"Mới xong lát 1 (stack Booking, khung Deploy Prod, DB Migrate prod có guard, Infra #633). P0 tốn 0 USD và plan Dev phải ra “no change”. Làm trước giúp P2–P3 nhanh khi có ngày go-live.",
  "facts":[],
  "opts":[o("now","Làm, lane B S280–S284, mỗi lát một cửa sổ Terraform apply","",True),o("wait","Chờ ngày go-live")]},
 {"grp":"Chủ doanh nghiệp và prod","id":"d16-bk045","tag":"D16 · AA-1061","title":"AA-1061 (xoá bảng B2C) đổi sang key migration mới?",
  "ctx":"AA-1061 ghi “dựng lại Booking #200 (bk-045)”, nhưng key 045 nay đã thuộc migration finance của AA-1074. Dùng lại sẽ đụng. Guard đóng băng 30 ngày (áp từ 28/11 23:50Z) giữ nguyên.",
  "facts":[],
  "opts":[o("rekey","Dựng lại trên key trống kế tiếp (bk-049 trở đi), cùng guard; ghi comment Linear","",True),o("later","Để nguyên, xử lý lúc làm")]},
]
lines = open(SRC, encoding="utf-8").read().split("\n")
head = lines[:73]   # up to the line before "  var Q = ["
tail = lines[167:]  # from the line after "  ];"
head = [l.replace("Chốt việc S275", "Kế hoạch sau R7 · S278") for l in head]
for i, l in enumerate(head):
    if 'class="status">S275' in l:
        head[i] = '    <div class="status">S278 · 12/11/2026 · kế hoạch S279–S292 · 16 quyết định</div>'
    if 'class="lede"' in l:
        head[i] = ('    <p class="lede">R0–R7 và hai mốc pilot đã xong trên thực tế; slot S279/S280 gần hết. Đây là 16 câu để chốt kế hoạch '
                   'S279–S292 (4 lane song song: chất lượng nội dung W2→W5, chuẩn bị pilot + prod, card CRM sau R3, mở R8 bằng tên miền riêng). '
                   'Mỗi câu có bối cảnh bằng lời thường và một đề xuất đã chọn sẵn. Bấm <b>Chốt</b> từng câu, hoặc <b>Chốt tất cả theo đề xuất</b>; '
                   'agent đọc lựa chọn đã lưu và cập nhật plan.json / backlog.</p>')
    if l.strip().startswith("<footer>"):
        head[i] = ('  <footer>Bản kế hoạch đầy đủ (tiếng Anh): <code>docs/audits/2026-11-12-S278-session/plan-after-r7/plan.md</code> (root PR cuối phiên). '
                   'Chi trả phí ước cho cả đợt ≈ 45–52 USD, chủ yếu W5 (≤ 33 USD). Phát hiện phụ: plan.json chưa tick M-P2, M-R7, M-OD và mục D8 của M1b — sửa trong root PR.</footer>')
js = "  var Q = " + json.dumps(Q, ensure_ascii=False, indent=1).replace("\n", "\n  ") + ";"
open(OUT, "w", encoding="utf-8").write("\n".join(head + [js] + tail))
print("ok", len(Q))
