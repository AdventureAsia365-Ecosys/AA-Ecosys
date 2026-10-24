# S249 — 23–24/10/2026: CRM W1/W2 + Lane B lên Dev, viết lại S1 toàn catalogue (pilot → ≤50 → theo nước)

**Tác nhân:** Claude Code (Ultracode; workflow + subagent song song; VSCode, WSL2; agent điều phối tự merge/deploy/verify
theo luật giai đoạn dev, push/merge bằng GitHub App `aa-agent`). Phiên dài (23/10 23:20 → 24/10 ~19:00 VN), Nghiệp
chia phiên: phiên sau (S250) chạy tiếp ngay các wave S1 và làm AA-835, AA-910; nháp Jira gom sang S250.

Nguồn số liệu: `docs/audits/2026-10-24-S249-wrap/state-snapshot.md` (kiểm live lúc đóng), comment Linear từng issue,
checklist sống `.tmp-session/S249-checklist.md`, báo cáo wave `docs/audits/2026-10-24-S249-s1-wave50/` +
`.tmp-session/s249/aa645/realpilot/cw-*`. Phần chưa kiểm ghi rõ "chưa verify".

## Trạng thái

- **Linear Done trong phiên (14):** AA-783, AA-829, AA-987, AA-934, AA-935, AA-936, AA-937, AA-940, AA-939, AA-938,
  AA-942, AA-975, AA-976, AA-899. Không tạo issue Linear mới.
- **In Progress:** AA-645 (viết lại S1 — các wave theo nước đang chạy), AA-941 (console L1 đã live, còn kiểm UI bằng
  phiên admin thật), AA-910 (S250 làm luôn). **AA-835** chuyển S250 làm luôn (Nghiệp).
- **PR merged: 93** (CIS 13, Booking 7, TripPlanner 3, Infra 23, AA-Partner 29, root 18).
- **Migration áp Dev (DB Migrate):** Booking **bk-022**; CRM **crm-003 → crm-011** (9 bản). CIS giữ 274.
- **Release:** CIS 0.7.0 + 0.8.0, Booking 0.4.0 + 0.5.0, TripPlanner 0.6.0 + 0.7.0, AA-Partner 0.2.0 + 0.3.0.

## Quyết định của Nghiệp (trong phiên)

- Đầu phiên: tự chọn 20 việc từ master plan + tồn S248, chạy liên tục, không hỏi; việc cần duyệt thì duyệt luôn.
- 24/10 ~12:30 (d04): **duyệt viết lại S1 toàn catalogue**: wave <10 dừng khi ≥2 tour ở lại v1 hoặc lỗi nặng; ≥10
  theo luật 10%; thứ tự pilot 3 thật → ≤50 thật (A3 bật) → theo nước; Nghiệp xem 2 checkpoint; trần **$120**.
- "Khi chạy từng wave thì báo cáo tốn bao nhiêu tiền luôn" (memory `wave-report-cost`).
- "Trang dùng tiếng Anh mặc định" (memory `pages-default-english`) → Partner #17.
- AA-829: "làm luôn" (lật DNS, tắt auto mode).
- ~15:55: **checkpoint 2 duyệt**, chạy từng nước, báo cáo đánh giá; bỏ giới hạn 2h; AA-938 phương án **C**.
- AA-910 / AA-835: "làm luôn đi, đừng nhắc hoài" (memory `do-not-remind-just-do`) → rồi "qua phiên sau làm luôn".
- Đóng phiên: giữ công tắc wave BẬT để phiên sau chạy tiếp ngay; Jira gom sang phiên sau (memory `same-day-session-handover`).

## Thay đổi Codebase

**AA-Partner (CRM):** crm-003 vault (#7/#9 KeyProvider KMS, AES-GCM + blind index); crm-004 + web skeleton + seeder
(#10/#11); sửa đăng nhập live (#14 write guard origin, #15 Next HOSTNAME trên Fargate, #17 tiếng Anh mặc định);
crm-005 + slice 1 intake → board + E2E (#13/#16); crm-006 + F1/F2 (#18/#19); crm-007 + audit export (#20/#23);
crm-008 + quyền/thành viên/mời + pool partner MFA (#21/#24, E2E #28/#30); crm-009 + scrubber F3 (#22/#25/#26/#29,
phương án C #33); crm-010 + vòng đời dữ liệu/giữ pháp lý (#31/#32); crm-011 + console L1 `/crm/ops/v1` (#34/#35);
release 0.2.0/0.3.0 (#3/#8), actions bump (#12).

**AA-CIS-App:** #969 brand-fit v2 + harness; #971 purge TripPlanner theo sự kiện lifecycle (AA-987); #972 portal link
CRM; #973 catalog.http.v1 cho CRM qua M2M (AA-976); #974 OpenAPI export + oasdiff (AA-899); #975 Platform Apps + chi
phí CRM; #976 vá mất ngày khi flag_fix (AA-645); #978 trang S-01 console agency (AA-941); **#979 Sentry bỏ frame
locals + che token/email** (review bảo mật AA-941 phát hiện token nhân viên lọt lên Sentry khi lỗi 500); release
0.7.0/0.8.0 (#950/#970); dependabot (#968/#977).

**AA-Booking:** bk-022 outbox chung + feed B2B + desk on-request + cờ sự cố (#77/#80, AA-975); AA-679 re-land (#78);
kiểm layout 1440 lặp lại được (#81, AA-910); OpenAPI (#82); release 0.4.0/0.5.0 (#66/#79).

**AA-TripPlanner-Web:** #143 purge cache theo thông báo lifecycle có ký (AA-987); release 0.6.0/0.7.0.

**AA-CIS-Infra:** #330 script drill AA-829; bản copy migration bk-022, crm-003…011; #332 KMS CRM; #333 scope M2M
catalog; #335 web CRM trên ECS; #336 managed login branding mọi client external (+ guard CI); #338 client host go-dev;
#340/#342 bucket tài liệu/audit; #345 pool partner MFA + client crm-staff + nhóm staff; #347 bật đăng nhập partner;
#346/#348 guardrail Bedrock dò PII; #349 cảnh báo tuổi bản sao backup + dry run lifecycle; **#350 role Terraform Plan
đọc được guardrail** (sau #348 mọi plan đỏ).

**AA-Ecosys (root):** #218–#235: báo cáo AA-783, hợp đồng (b2b 1.1, lifecycle purge, catalog.http 1.1, crm.ops 1.1 +
luật trường PII write-only), drill AA-829, go/no-go S1 + panel 50, bằng chứng AA-910/AA-935, DM-7 (audit, LLM,
invitation, crm-010), DPA annex 4, schema dump + infra docs regen.

## Thay đổi Hạ tầng

- **DB Migrate:** bk-022; crm-003…crm-011 (mỗi lần qua check → apply; crm-010/011 áp trong khoảng nghỉ giữa wave vì
  DB Migrate bị chặn khi wave mở).
- **Terraform (CI apply):** CRM KMS/bucket/web/client host/pool partner/guardrail/alarm. **Local MFA:** bootstrap
  `tf_apply_crm` (Bedrock guardrail) và role `tf_plan` (đọc guardrail) — lần sau Nghiệp tắt auto mode cho bước này.
- **Cognito:** pool `aa-partner-dev` (MFA bắt buộc), 6 user E2E partner + secret `crm/dev/e2e-test-crm/*`, client
  secret web CRM chuyển sang `partner-web`. GitHub env: `e2e` (secrets/variables), `scrub-corpus` (main only).
- **S1 waves:** worker CIS có `S1_WRITER_V2=on` (hiện :371, kế thừa qua deploy), route `s1_generate` = sonnet-5-5 —
  **cố ý để BẬT** cho S250. RDS snapshot thủ công `aa-cis-dev-db-pre-s1-*` một bản mỗi wave (hết hạn theo luật 30 ngày
  AA-869).
- **Chi phí thêm/tháng (Dev):** guardrail ~$0,75, alarm backup ~$0,70, Cognito pool partner $0 (dưới 10k MAU).

## Bằng chứng verify (chính)

- **AA-645 / S1:** pilot thật 3/3 ($0,27); wave ≤50: 50/50 publish + atomize, 0 review, gate 13→4, phủ số liệu
  0,415→0,672, slug 308 50/50, $3,84 (`docs/audits/2026-10-24-S249-s1-wave50/`). Theo nước (mỗi wave: 0 điều kiện
  dừng, 0 review, slug 308 đúng 100%):

  | Wave | Tour | Gate trước→sau | Phủ số liệu | Chi phí |
  |---|---|---|---|---|
  | Mongolia | 13 | 9→0 | 0,724→0,781 | $0,836 |
  | Pakistan | 14 | 5→2 | 0,477→0,606 | $1,277 |
  | South Korea | 26 | 15→3 | 0,48→0,698 | $2,377 |
  | Bhutan | 27 | 9→0 | 0,446→0,843 | $1,753 |
  | Taiwan | 29 | (đang chạy lúc đóng — xem `cw-progress.log`) | | |

  Luỹ kế trước Taiwan **$10,35 / $120**; 133/810 tour đã v2 (162 khi xong Taiwan).
- **CRM:** readiness `crm-011`; E2E Dev (slice 1 + mời → active **10 giây**); xuất audit có object ở cả 2 bucket;
  Scrub corpus live 242 mẫu **0 rò rỉ** (che quá tay 9,1% sau phương án C, còn đỏ so với 5%); DB có 8 hàm quy tắc giữ +
  11 trigger bảo vệ; `/crm/ops/v1/console` không token → 401.
- **AA-987:** retire → 410 sau 8 s, restore 24 s; **AA-829:** PITR 21′20″, 164/164 bảng; **AA-975/976:** live 200/304/404/401/403/410.

## Còn lại (S250 làm ngay, theo thứ tự)

1. **Wave S1 tiếp** (công tắc vẫn bật): đọc `cw-progress.log` (Taiwan), rồi lần lượt Thailand 34, Laos 36,
   Philippines 40, Japan 50+22, Nepal 50+26, China 50+50+11, Sri Lanka 50+50+12, India 50+50+50+17:
   `bash .tmp-session/s249/aa645/cw_wave2.sh <cw_name>` rồi `cw_summary.py <cw_name>` + `cw_ledger.py`; báo cáo
   từng wave kèm chi phí; slug 308 sau ≥30′ bằng `cw_slugs.sh`. Hết loạt: khôi phục công tắc (worker revision sạch,
   route haiku), báo cáo tổng + Linear AA-645.
2. **AA-835** (5 phần, comment Linear S249) — chạy thử trả phí theo luật subset.
3. **AA-910** — tự kiểm live bằng user staff E2E (Cognito, mã qua hộp thư E2E), không hỏi.
4. **AA-941** — kiểm UI `/admin/platform/agencies` (aa-ui-verify).
5. **Jira S249** (nháp bên dưới) → Nghiệp duyệt → đăng.
6. AA-938: phương án B chỉ khi Nghiệp muốn đưa over-scrub < 5% (Scrub corpus đêm còn đỏ, issue AA-Partner #27).

## Nháp Jira chuyển S250 (chưa đăng; cập nhật số wave trước khi đưa duyệt)

- **PR-22 (CIS nội dung):** viết lại nội dung Master toàn catalogue bằng bộ viết mới — pilot + 50 tour + Mongolia,
  Pakistan, Hàn Quốc, Bhutan, Đài Loan đã xong; trang bị chặn ở cổng chất lượng giảm mạnh, phủ số liệu từ nguồn tăng;
  đường dẫn cũ tự chuyển sang tên mới trên TripPlanner; chi phí trung bình ~$0,07/tour; các nước còn lại chạy tiếp.
- **PR-26 (CRM đại lý):** trên Dev đã có: đăng nhập riêng cho đại lý bắt buộc xác thực 2 lớp, mời thành viên (mời → dùng
  được trong khoảng 10 giây), nhật ký truy cập + xuất hằng giờ, lọc dữ liệu cá nhân trước khi gửi AI (0 rò rỉ trên 242
  mẫu thử), thùng rác / giữ dữ liệu theo yêu cầu pháp lý / yêu cầu xoá, trang quản trị agency cho AA.
- **PR-24 (TripPlanner):** tour bị gỡ ở hệ thống nội dung biến mất khỏi TripPlanner trong vài giây (trước đây tới 30 phút).
- **PR-25 (Booking):** luồng sự kiện cho đại lý B2B, bàn xử lý yêu cầu on-request, cờ sự cố chuyến đi.
- **PR-27 (Nền tảng):** diễn tập khôi phục cơ sở dữ liệu (21 phút, đủ dữ liệu); siết bảo mật báo lỗi (không gửi thông
  tin đăng nhập/email lên hệ thống theo dõi lỗi).

## Lưu ý kỹ thuật cho phiên sau

- Bài học mới: `skill/aa-lessons/lessons.md` (S249: scratch theo lane, cờ dừng khi hàng đợi chưa xong, quy tắc bảo vệ
  dữ liệu một chỗ ở DB, danh sách trắng địa danh lọt tên người, gitleaks quét từng commit, ARN không để trong vars
  GitHub repo public, HOSTNAME Fargate, origin sau CloudFront…).
- Trong lúc wave mở: không deploy backend CIS, không DB Migrate — chèn vào khoảng nghỉ giữa wave (script `gap1.sh` mẫu).
- `cw_wave2.sh` tự chờ job `recompute` debounce trước khi enqueue; đặt tên wave không có dấu cách/ngoặc.
- Auto mode chặn apply IAM role CI và `terraform-apply` qua script gộp: tách bước, hoặc nhờ Nghiệp tắt auto mode.
