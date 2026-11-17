import json
SRC = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-12-S278-session-close/decisions/index.html"
OUT = "/home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-17-S283-session/decisions/index.html"
def o(v, t, d="", rec=False):
    x = {"v": v, "t": t, "d": d}
    if rec: x["rec"] = True
    return x
G1, G2, G3, G4 = "Bảo mật trước pilot (AA-1111)", "Vận hành liên tục (AA-1110)", "Dữ liệu và AI (AA-1112, AA-1113)", "Chất lượng nội dung, prod, khác"
Q = [
 {"grp":G1,"id":"s283-mfa-admin","tag":"AA-1111 · MFA admin","title":"Bắt admin đăng nhập bằng yếu tố thứ hai thế nào?",
  "ctx":"Pool đăng nhập nhân viên (WORKFORCE) đang để MFA OPTIONAL, cho đăng nhập bằng mật khẩu hoặc mã gửi e-mail. Không dùng được Google 2SV vì hộp thư công ty nằm ở DreamHost. MFA của Cognito áp cho cả pool và không áp cho đăng nhập bằng mã e-mail, nên muốn chỉ bắt admin thì phải thiết kế riêng.",
  "facts":["Đã kiểm live 16/11: get-user-pool-mfa-config = OPTIONAL","Chưa kiểm token của pool có claim amr hay không: agent kiểm trước khi code; không có thì dùng Lambda pre-token đóng dấu claim"],
  "opts":[o("totp-admin","Nhóm admin đăng nhập mật khẩu + TOTP; API CIS/Booking/Partner từ chối phiên admin không có dấu MFA; người khác vẫn dùng mã e-mail","",True),o("separate-pool","Tách pool riêng cho admin, bắt MFA cả pool"),o("prod","Để tới lúc dựng prod")]},
 {"grp":G1,"id":"s283-ro-role","tag":"AA-1111 · R34","title":"Phiên agent mặc định dùng role AWS chỉ đọc, chỉ nâng quyền ghi khi apply/deploy?",
  "ctx":"Audit S282 (R34): agent đang dùng role admin 12 h cho mọi việc. Role chỉ đọc làm mặc định giảm thiệt hại khi lệnh sai; bước ghi ghi rõ trong checklist phiên.",
  "facts":[],
  "opts":[o("yes","Đồng ý: chỉ đọc mặc định, role ghi chỉ cho bước apply/deploy, ghi log","",True),o("no","Giữ role admin như hiện nay")]},
 {"grp":G1,"id":"s283-dreamhost","tag":"Chủ doanh nghiệp · e-mail","title":"Đề xuất với chủ doanh nghiệp bật MFA trên DreamHost và đặt mật khẩu mạnh, riêng cho mỗi hộp thư?",
  "ctx":"Hộp thư công ty là kênh khôi phục của nhiều tài khoản (AWS, GitHub, Linear). Không tốn tiền.",
  "facts":[],
  "opts":[o("jira","Đưa vào nháp Jira cuối phiên như một đề xuất nhẹ, anh duyệt","",True),o("skip","Chưa gửi")]},
 {"grp":G2,"id":"s283-keyholder","tag":"AA-1110 · người giữ khoá","title":"Ai là người giữ khoá thứ hai, và khi nào diễn tập?",
  "ctx":"Hôm nay chỉ anh có quyền chủ org GitHub, Identity Center acc4, tên miền và break-glass. Agent đã viết trang “chạy không cần agent” và kịch bản tabletop (lane L3 hôm nay).",
  "facts":["Các runbook rollback ECS/Booking/TP Lambda chưa diễn tập lần nào"],
  "opts":[o("owner-dec","Chủ doanh nghiệp; một buổi 60 phút tuần đầu tháng 12 (sau khi acc2 vào org 01/12): thử quyền + diễn tập + tabletop","",True),o("other","Người khác (anh ghi chú)"),o("later","Để sau go-live")]},
 {"grp":G2,"id":"s283-alert2","tag":"AA-1110 · cảnh báo","title":"Kênh cảnh báo thứ hai (miễn phí) là gì?",
  "ctx":"Báo động hiện chỉ gửi một e-mail SNS. Lane hôm nay thêm subscription thứ hai trong Terraform, mặc định tắt.",
  "facts":[],
  "opts":[o("email-owner","E-mail SNS thứ hai tới hộp thư công ty của chủ doanh nghiệp; bật khi xác nhận","",True),o("webhook","Webhook push miễn phí (agent đề xuất dịch vụ)"),o("none","Chưa cần")]},
 {"grp":G2,"id":"s283-billing-contact","tag":"AA-1004 · acc2","title":"Thêm liên hệ BILLING thay thế cho acc2 trước khi chuyển org?",
  "ctx":"Kiểm 1.7 sáng nay: acc2 có liên hệ chính nhưng chưa có liên hệ BILLING thay thế. AWS cần đủ thông tin liên hệ để tài khoản đứng riêng. Các kiểm khác: tự rời org được (1.3), tạo được role org (1.4), role chưa tồn tại (1.5). Apply role vẫn giữ tới khi ký phụ lục TrueIDC.",
  "facts":[],
  "opts":[o("hand","Anh thêm trên console (hộp thư vai trò), khoảng 2 phút","",True),o("agent","Agent chạy put-alternate-contact (lệnh ghi, cần anh cho phép)"),o("later","Để tới 01/12")]},
 {"grp":G3,"id":"s283-retention-job","tag":"AA-1112 · retention","title":"Cho chạy live lần đầu retention_job: xoá 2.392 job đã xong hơn 30 ngày?",
  "ctx":"DRY RUN đêm 16/11: shared.job có 2.392 job trạng thái succeeded cũ hơn 30 ngày (28/09–16/10), không archive theo chính sách đã duyệt. Các loại retention khác có 0 dòng vì dữ liệu chưa đủ tuổi. Sau một lượt live, lượt theo lịch tự chạy live trong giới hạn tăng 2x.",
  "facts":["Job failed/cancelled (90 ngày, có archive): 0 dòng","llm_call_log 180 ngày, tenant_api_usage 90 ngày, decision_log 180 ngày: 0 dòng"],
  "opts":[o("yes-2392","Đồng ý, max_rows = 2.392 (job succeeded), chạy một lượt và báo số","",True),o("no","Chưa xoá")]},
 {"grp":G3,"id":"s283-dm71","tag":"AA-1112 · DM-7.1","title":"Duyệt khoảng 57 dòng retention đang ở trạng thái “proposed” trong DM-7.1?",
  "ctx":"Các nhóm: log CIS, cấu hình nền tảng CRM, bản ghi xoá dữ liệu CRM, TripPlanner, vận hành Booking, thời hạn decision_log. Danh sách đầy đủ ở bảng DM-7.1 trong data standards. Mỗi app chạy live lần đầu vẫn theo DRY RUN rồi anh duyệt số dòng.",
  "facts":[],
  "opts":[o("approve-groups","Duyệt theo nhóm như đề xuất; lượt live đầu mỗi app vẫn DRY RUN + anh duyệt số","",True),o("page","Agent làm trang duyệt từng dòng"),o("later","Để sau")]},
 {"grp":G3,"id":"s283-d10","tag":"AA-1113 · ADR 0009 d10","title":"Chấp nhận ADR 0009 quyết định 10 (phạm vi dữ liệu theo nơi xử lý) để bật che PII trước lượt gọi AI?",
  "ctx":"Đo $0 hôm nay (30 ngày): chỉ ba stage viết cho đại lý mang chữ của tenant: t9_write, t2_generate, t8_angle_gen (7 tenant mỗi stage). Các stage catalogue (s1_*, a3_*, tp_compose) không có dữ liệu tenant.",
  "facts":["File: docs/audits/2026-11-17-S283-session/aa1113-provider-stage-30d.psv"],
  "opts":[o("accept","Chấp nhận; che PII fail-closed cho các stage free-text (t9/t2/t8), tp_compose không cần","",True),o("wait","Chờ thêm số liệu")]},
 {"grp":G3,"id":"s283-acc3-budget","tag":"AA-1113 · budget","title":"Hạ budget acc3 từ 250 xuống 100 USD/tháng cho khớp trần gateway?",
  "ctx":"Budget acc1 = 100 USD (khớp trần gateway 100). Budget acc3 = 250 USD trong khi trần gateway của acc3 là 100. Cả hai không lọc theo dịch vụ nên nhiều khả năng đã tính tiền Marketplace (Claude); kiểm lại khi có hoá đơn tháng 11. Đổi budget miễn phí.",
  "facts":[],
  "opts":[o("100","Hạ xuống 100 USD, agent apply local khi có MFA","",True),o("keep","Giữ 250")]},
 {"grp":G4,"id":"s283-nullrun","tag":"AA-1051 · null run","title":"Cho chạy null run W5 bằng thước đo v7 (tư vấn), trần 5 USD?",
  "ctx":"AA-1048 v7 đã ghim (FP 68 %, TP 88 %), chưa đủ 80 % để chặn nên chỉ dùng làm tư vấn. Null run cần để biết mức nhiễu của thước đo trước các lượt chứng minh trả phí.",
  "facts":[],
  "opts":[o("yes5","Đồng ý, trần 5 USD, sau khi PR nối v7 (0 USD) đã merge","",True),o("wait","Chưa")]},
 {"grp":G4,"id":"s283-aa788","tag":"AA-788 · pilot","title":"Pilot 20 bài AA-788 (F12_scope, F14, F9) từ 19/11, ước 2–5 USD?",
  "ctx":"Replay $0 đã xong. Pilot là bước cuối trước khi đưa ba cổng thành chặn (sửa một lần, không giữ bài). Đăng ký trước mẫu + chỉ số rồi mới chạy.",
  "facts":[],
  "opts":[o("yes5","Đồng ý, trần 5 USD, thử 3 bài trước, đăng ký trước merge trước","",True),o("wait","Chưa")]},
 {"grp":G4,"id":"s283-tl11","tag":"D4 · TL-11","title":"Gỡ băng TL-11 thế nào khi AA-1050 chưa thể enforce class nào trước pilot?",
  "ctx":"S278 D4: gỡ TL-11 khi AA-1077 đóng và AA-1050 enforce ít nhất một class. Điều kiện thứ hai chưa thể đạt trước pilot, nên AA-790/920/921/1000 đứng yên.",
  "facts":[],
  "opts":[o("lift-0usd","Gỡ cho code $0 và replay; lượt shadow trả phí, pilot và đổi prompt writer chờ pilot","",True),o("keep","Giữ băng như cũ")]},
 {"grp":G4,"id":"s283-waf","tag":"AA-1117 · WAF","title":"Giới hạn tốc độ ở biên (CloudFront WAF, ~5–6 USD/tháng): bật bây giờ hay lúc prod?",
  "ctx":"Dev không có người dùng thật. Ghi rủi ro chấp nhận có điều kiện vào checklist go-live.",
  "facts":[],
  "opts":[o("prod","Lúc dựng prod","",True),o("now","Bật bây giờ trên Dev")]},
 {"grp":G4,"id":"s283-golive","tag":"Chủ doanh nghiệp · go-live","title":"Đề xuất chủ doanh nghiệp đặt tháng go-live mục tiêu?",
  "ctx":"Chưa có ngày go-live thì prod P2–P6, AA-980, AA-1054 và checklist AA-1117 không bắt đầu được. Luật dự phòng S265: P2 trễ nhất tuần 3 của pilot.",
  "facts":[],
  "opts":[o("jira","Nháp Jira đề xuất một tháng mục tiêu sau khi chuyển org (01/12), anh duyệt","",True),o("hold","Chưa hỏi")]},
 {"grp":G4,"id":"s283-map-engine","tag":"AA-948 · bản đồ","title":"Builder CRM dùng chung engine bản đồ/tuyến của TripPlanner (không fork)?",
  "ctx":"AA-948 đang parked. Dùng chung engine tránh lệch hai bản. Mapbox có thể tốn tiền: agent báo giá trước khi làm.",
  "facts":[],
  "opts":[o("shared-quote","Đồng ý engine dùng chung; agent báo giá Mapbox trước, vẫn parked tới khi duyệt giá","",True),o("no","Giữ nguyên parked, không bàn")]},
 {"grp":G4,"id":"s283-template-app","tag":"AA-1103 · template","title":"Cài App aa-agent lên repo project-template và duyệt kích hoạt module Academy L8 sau PR?",
  "ctx":"Cài App là một cú bấm của owner org. L8 (playbook dự án mới) đang làm bản nháp ở lane L4 hôm nay.",
  "facts":[],
  "opts":[o("yes","Đồng ý cả hai","",True),o("module-only","Chỉ duyệt L8, chưa cài App")]},
 {"grp":G4,"id":"s283-tp-ruleset","tag":"AA-1119 · TripPlanner","title":"Bật merge queue + check bắt buộc cho repo TripPlanner (anh áp ruleset JSON, ~1 phút)?",
  "ctx":"Ba repo app khác đã có merge queue. App aa-agent không có quyền admin repo nên không tự áp được.",
  "facts":[],
  "opts":[o("yes","Đồng ý; agent chuẩn bị JSON","",True),o("later","Để sau")]},
]
lines = open(SRC, encoding="utf-8").read().split("\n")
start = next(i for i, l in enumerate(lines) if l.strip() == "var Q = [")
end = next(i for i in range(start, len(lines)) if lines[i].strip() == "];")
head, tail = lines[:start], lines[end + 1:]
out = []
for l in head:
    l = l.replace("Kế hoạch sau R7 · S278", "Quyết định S283")
    if 'class="status">S278' in l:
        l = '    <div class="status">S283 · 17/11/2026 · ' + str(len(Q)) + ' quyết định</div>'
    if 'class="lede"' in l:
        l = ('    <p class="lede">Các câu cần anh hoặc chủ doanh nghiệp quyết, gom từ lượt đánh giá 35 issue Linear sáng nay và các lane đang chạy. '
             'Mỗi câu có bối cảnh bằng lời thường và một đề xuất chọn sẵn. Bấm <b>Chốt</b> từng câu hoặc <b>Chốt tất cả theo đề xuất</b>; '
             'agent đọc lựa chọn đã lưu rồi làm tiếp. Câu nào không chốt thì agent làm theo đề xuất và báo lại.</p>')
    if l.strip().startswith("<footer>"):
        l = ('  <footer>Nguồn: <code>docs/audits/2026-11-17-S283-session/</code> (root PR cuối phiên). Chi trả phí nếu chốt hết theo đề xuất: '
             'tối đa ~10 USD (null run ≤ 5, pilot AA-788 ≤ 5); các mục khác 0 USD.</footer>')
    out.append(l)
js = "  var Q = " + json.dumps(Q, ensure_ascii=False, indent=1).replace("\n", "\n  ") + ";"
open(OUT, "w", encoding="utf-8").write("\n".join(out + [js] + tail))
print("ok", len(Q))
