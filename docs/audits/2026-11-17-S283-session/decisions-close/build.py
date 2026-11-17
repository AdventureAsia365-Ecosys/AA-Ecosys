import json
ROOT = "/home/nghiep/projects/AA-Ecosys/docs/audits"
SRC = ROOT + "/2026-11-12-S278-session-close/decisions/index.html"
OUT = ROOT + "/2026-11-17-S283-session/decisions-close/index.html"
def o(v, t, d="", rec=False):
    x = {"v": v, "t": t, "d": d}
    if rec: x["rec"] = True
    return x
G0, G1, G2, G3, G4, G5 = ("Gấp (Booking)", "Audit giao diện AA-1123", "Audit docs AA-1124", "Docs-as-code + trang /admin/docs",
                          "Chi AI và bảo mật", "Chất lượng nội dung (W5)")
Q = [
 {"grp":G0,"id":"c-b0-test-rule","tag":"B0 · giá Booking","title":"Đóng rule giá B2B 'test' sẽ tự áp ngày 01/01/2027?",
  "ctx":"Audit giao diện: Booking có một rule giá thử nghiệm đã được duyệt, hiệu lực 01/01/2027. Tới ngày đó nó thay rule B2B đang dùng: margin 20 % → 15 %, sàn 12 % → 10 %, mất +25 % RRP. Giao diện không rút được rule đã duyệt nhưng chưa tới ngày.",
  "facts":["Sửa bằng một run-script có DRY RUN (đổi dữ liệu, anh duyệt số dòng) + thêm nút đóng rule chưa hiệu lực và tie-break approved_at"],
  "opts":[o("fix-s284","Làm đầu phiên S284: DRY RUN → anh duyệt → đóng rule + vá code","",True),o("now","Làm ngay trong phiên này"),o("keep","Giữ rule (có chủ đích)")]},
 {"grp":G0,"id":"c-b1-season","tag":"B1 · lịch mùa","title":"Sửa job gán lịch mùa Booking (timeout 405/405 lần nhưng báo succeeded)?",
  "ctx":"Chưa tour nào được gán lịch mùa nên mọi tour đang tính giá mùa thấp. Job báo thành công giả. Sửa: chọn batch từ trip_plans trước, đánh dấu degraded khi bỏ bước, hiện trên trang job; kích thước batch thành setting trên trang admin.",
  "facts":[],
  "opts":[o("s284","Làm ở S284 cùng B0","",True),o("later","Để sau")]},
 {"grp":G1,"id":"c-fe-batches","tag":"FE · 21 batch","title":"Thứ tự làm các batch sửa giao diện?",
  "ctx":"21 batch theo app (README audit). Nhóm đầu: B0/B1 (Booking), S1 tiền + bộ đếm Studio, C1 số liệu CIS lệch, C2 chi phí đúng (Anthropic vào đúng nhóm, Cost Explorer hằng ngày), K1 trợ năng kit (sửa 1 lần cho 4 app). Mọi ngưỡng đụng tới đưa lên trang Settings admin trong cùng PR.",
  "facts":["64 trang chưa mở được (phiên hết hạn) — chạy lại tuần tự ở S284"],
  "opts":[o("top6-s284","S284–S285: B0, B1, S1, C1, C2, K1; các batch còn lại xếp vào master plan","",True),o("all-now","Xếp hết vào S284–S287"),o("pick","Tôi chọn từng batch (ghi chú)")]},
 {"grp":G1,"id":"c-fe-issues","tag":"FE · Linear","title":"Tạo issue Linear cho các batch giao diện thế nào?",
  "ctx":"Gói Free: mỗi issue nên là một lát giao được. Nhiều batch ghi 'new issue needed'.",
  "facts":[],
  "opts":[o("per-app","Gom theo app: 4 issue (CIS, Booking, Agency app, TripPlanner) + 1 issue kit; batch chi tiết trong checklist","",True),o("per-batch","Mỗi batch một issue (~21)"),o("in-1123","Để hết trong AA-1123")]},
 {"grp":G2,"id":"c-docs-batches","tag":"Docs · 11 batch","title":"Làm các batch sửa docs theo thứ tự đề xuất?",
  "ctx":"Batch 1 (XS): dọn thông tin không được nằm trong repo public — e-mail cá nhân, ID tài nguyên, tên người, ghi chú agent trong ADR. Batch 2–3: file chỉ dẫn agent (16/35 lỗi cao). Batch 4: trang pháp lý / bảo vệ dữ liệu. Batch 5: runbook ops sai địa chỉ Terraform. Batch 6–11: guide staff B2B, quét acc1, ADR, docs app, số liệu nhỏ, lưu trữ trang mồ côi.",
  "facts":[],
  "opts":[o("1to5-s284","Batch 1 ngay đầu S284, 2–5 trong S284–S285, 6–11 sau (AA-1118)","",True),o("1-now","Batch 1 làm ngay trong phiên này"),o("later","Để sau")]},
 {"grp":G2,"id":"c-docs-code","tag":"Docs · 19 việc code","title":"19 việc phải sửa code/cấu hình mà audit docs tìm ra (rollback helper, gate cũ, preview ruleset, client Cognito thừa…)?",
  "ctx":"Mỗi việc nhỏ (XS–S). Ví dụ: helper rollback ECS từ chối 2 service admin; bk_inquiry_pull vẫn trong danh sách miễn gate; ruleset preview-signin còn bật; khoá ci-bot là secret cấp repo trên repo public.",
  "facts":[],
  "opts":[o("one-issue","Gom 1 issue 'docs-audit code follow-ups', làm dần theo lát","",True),o("in-1118","Để trong AA-1118")]},
] 
adv = json.load(open(ROOT + "/2026-11-17-S283-docs-advisory/decisions.json"))
for q in adv:
    Q.append({"grp":G3,"id":"c-"+q["id"],"tag":"Docs-as-code","title":q["question_vi"],"ctx":q.get("context_vi") or q.get("ctx") or "","facts":[],
              "opts":[o(x["v"], x["t"], x.get("d",""), bool(x.get("rec"))) for x in q["options"]]})
Q += [
 {"grp":G4,"id":"c-adr0009-caps","tag":"ADR 0009","title":"Ghi nguyên tắc chi AI (dev trần cứng; prod dùng nhiêu tính nhiêu, quota theo gói, cầu dao bất thường) thành sửa đổi ADR 0009?",
  "ctx":"Anh đã nêu nguyên tắc hôm nay; AA-1126 đang code (migration 446 + code gateway đang ship, UX quota đang làm). ADR giữ quyết định cho lúc dựng prod.",
  "facts":[],
  "opts":[o("yes","Đồng ý, agent viết amendment trong root PR cuối phiên","",True),o("later","Để khi dựng prod")]},
 {"grp":G4,"id":"c-sec-headers","tag":"ZAP","title":"Làm lát 'security headers' cho 4 frontend + 2 API (ZAP: 0 High)?",
  "ctx":"Medium: CSP thiếu ở vài route, CSP có wildcard / unsafe-inline; Low: thiếu HSTS, nosniff, lộ header Server, Permissions-Policy. SRI và COEP chấp nhận cho Dev.",
  "facts":["Bản triage: docs/audits/2026-11-17-S283-access-review/zap-baseline.md"],
  "opts":[o("s284","Một issue, làm S284–S285 (CSP nonce theo từng app, HSTS ở edge)","",True),o("headers-only","Chỉ HSTS + nosniff + Server (nhỏ), CSP để sau"),o("prod","Để lúc dựng prod")]},
 {"grp":G4,"id":"c-access-findings","tag":"Rà quyền Q4","title":"Dọn các phát hiện rà quyền F-20…F-24 (hash mật khẩu cũ, user staff_users thời bridge, token khách TripPlanner lưu rõ)?",
  "ctx":"Đều là xoá/sửa dữ liệu nhỏ, theo quy trình DRY RUN và anh duyệt số dòng. Không phát hiện quyền chéo app nào.",
  "facts":[],
  "opts":[o("s284","Làm ở S284 theo DRY RUN","",True),o("later","Để sau")]},
 {"grp":G5,"id":"c-w5-gate","tag":"W5 · mẫu","title":"Null run W5 thiếu mục GATE (6/12). Làm gì?",
  "ctx":"Golden set aa729@1.4.0 chỉ có 6 mục GATE; cần 12 để đủ power.",
  "facts":[],
  "opts":[o("label6","Agent panel gắn nhãn thêm 6 mục GATE (0 USD), tạo phiên bản golden mới","",True),o("lower","Hạ tối thiểu xuống 6 (power yếu, chỉ tư vấn)"),o("wait","Chưa")]},
 {"grp":G5,"id":"c-w5-reverify","tag":"W5 · reverify","title":"Cho chạy reverify writer t9_blog trên golden mới (trả phí) trước null run?",
  "ctx":"Control hiện không ghi cấu hình writer nên null run không hợp lệ. Reverify viết lại bộ control bằng cấu hình hiện tại.",
  "facts":["Agent báo giá bằng DRY plan trước khi chạy"],
  "opts":[o("yes-cap5","Đồng ý, trần 5 USD, DRY plan báo giá trước","",True),o("no","Chưa")]},
 {"grp":G5,"id":"c-w5-margin","tag":"W5 · margin","title":"Chấp nhận margin 4,0 claim/blog (thay 2,5) cho null run?",
  "ctx":"Review của lane nâng margin để phản ánh độ dao động thật của writer (writer_sd 4,6); power 0,81.",
  "facts":[],
  "opts":[o("accept","Chấp nhận 4,0","",True),o("keep25","Giữ 2,5 (cần mẫu lớn hơn)")]},
]
lines = open(SRC, encoding="utf-8").read().split("\n")
start = next(i for i, l in enumerate(lines) if l.strip() == "var Q = [")
end = next(i for i in range(start, len(lines)) if lines[i].strip() == "];")
head, tail = lines[:start], lines[end + 1:]
out = []
for l in head:
    l = l.replace("Kế hoạch sau R7 · S278", "Duyệt cuối phiên S283")
    if 'class="status">S278' in l:
        l = '    <div class="status">S283 · 17/11/2026 · ' + str(len(Q)) + ' quyết định</div>'
    if 'class="lede"' in l:
        l = ('    <p class="lede">Gom đề xuất của audit giao diện, audit docs, bản tư vấn docs-as-code, ZAP, rà quyền và W5 để anh duyệt một lần. '
             'Mỗi câu có đề xuất chọn sẵn; bấm <b>Chốt</b> từng câu hoặc <b>Chốt tất cả theo đề xuất</b>. Báo cáo đầy đủ ở docs/audits/2026-11-17-S283-*.</p>')
    if l.strip().startswith("<footer>"):
        l = ('  <footer>Nguồn: docs/audits/2026-11-17-S283-fe-audit, -docs-audit, -docs-advisory, -access-review, -session (root PR cuối phiên). '
             'Chi trả phí nếu chốt theo đề xuất: tối đa ~5 USD (reverify W5).</footer>')
    out.append(l)
js = "  var Q = " + json.dumps(Q, ensure_ascii=False, indent=1).replace("\n", "\n  ") + ";"
open(OUT, "w", encoding="utf-8").write("\n".join(out + [js] + tail))
print("ok", len(Q))
