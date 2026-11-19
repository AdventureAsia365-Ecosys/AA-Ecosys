# Tư vấn vòng 3: mọi việc còn chờ tech lead (S285, 19/11/2026)

Chỉ đọc, không sửa repo nào ngoài file này. Không ghi số tài khoản AWS, secret hay e-mail cá nhân.
Ngoài phạm vi: vai trò Booking (T13) đang có bản rà riêng, kể cả ghi chú mới của tech lead lúc 04:38Z
("làm nhóm người dùng và gắn quyền theo app như trang admin") — bản T13 trả lời phần đó.

Nguồn đã đọc: `docs/backlog/README.md` mục 2 "Waiting on Nghiệp"; `.tmp-session/S285-checklist.md`;
`.tmp-session/S285-lessons-pending.md`; các file `advisory-*.md`, `advisory-r2-*.md`, `decisions-gateway-identity.md`
trong thư mục này; `docs/backlog/tracker/plan.json` (`waiting`, `checks`, `milestones`); trang quyết định nguồn cung
(32/32 "Đồng ý", đọc live lúc viết); Linear AA-1110, AA-1111, AA-1126, AA-1127, AA-1128, AA-1144…AA-1153;
`docs/audits/2026-11-17-S283-access-review/README.md` và trang quyết định S283.

Từ viết tắt dùng trong bài (giải thích một lần):

- **KMS** (Key Management Service): dịch vụ khoá mã hoá của AWS. **CMK**: khoá do mình tạo trong KMS, có chính sách riêng.
- **T2**: bước viết lại tour cho từng đại lý (mỗi đại lý một bản lời văn). **T3**: luật chạy lại T2 khi dữ kiện tour đổi.
- **MFA** (multi-factor authentication): đăng nhập hai lớp. **TOTP**: mã 6 số đổi mỗi 30 giây trong app Authenticator.
- **DRY RUN**: chạy thử, chỉ đếm và liệt kê, không ghi gì.
- **SNS**: dịch vụ gửi thông báo (e-mail) của AWS. **WAF**: tường lửa web.
- **Cost Explorer (CE)**: công cụ xem chi phí AWS; mỗi lần gọi API tính 0,01 USD.
- **Done-when**: điều kiện để đóng một issue.

Cách chia:

- **(A)** cần tech lead quyết ngay (kèm đề xuất, chi phí, lý do).
- **(B)** bước tay chỉ tech lead làm được (đăng nhập, MFA, trình duyệt), kèm đường bấm.
- **(C)** đã cũ hoặc đã chốt: nêu bằng chứng, đề xuất gạch khỏi danh sách chờ.
- **(D)** việc của business owner (gửi qua Jira/Zalo, không quyết ở đây).

---

## Tóm tắt

| Nhóm | Số mục | Ghi chú |
|---|---|---|
| A — quyết ngay | 9 | 5 mục có tiền, tổng nếu duyệt hết ≈ 1,7–2,0 USD/tháng cố định + trần T2 10 USD/tháng (trần, không phải tiền chắc chắn tiêu) |
| B — bước tay | 9 | 3 mục có hạn (20/11, 25–30/11, 01/12) |
| C — gạch khỏi danh sách | 18 | Bằng chứng ở từng dòng |
| D — business owner | 8 | Gom vào nháp Jira cuối phiên |

---

## A. Cần tech lead quyết ngay

**A1. Khoá KMS riêng cho số tài khoản ngân hàng nhà cung cấp (AA-1150, lát L7).** Có tiền.
Đề xuất: **Có**, tạo một CMK riêng cho Booking, chỉ role tài chính/admin được giải mã. Chi phí ≈ 1 USD/tháng + 0,03 USD
mỗi 10.000 lần gọi (Dev gần như 0). Lý do: khoá AWS có sẵn (miễn phí) không tách được "ai được giải mã", nên ai đọc được
bảng là đọc được số tài khoản. Không duyệt thì L7 vẫn làm hết, chỉ để phần ngân hàng sau (code đã ghi chờ duyệt riêng).

**A2. Trần tiền tháng cho việc tự chạy lại T2 khi dữ kiện tour đổi (AA-1146, T3).** Có tiền (dạng trần).
Đề xuất: **10 USD/tháng trên Dev**, báo ở 80 %, sửa được trong admin; hết trần thì chỉ đánh dấu "lỗi thời" và báo.
Lý do: một lượt T2 ≈ 0,12–0,27 USD (đo ở AA-800/801), 10 USD ≈ 40–80 lượt, đủ cho Dev. Đây là trần nằm trong ngân sách
connection đã đặt, không phải tiền mới. Agent đọc số thật/tour trong `shared.llm_call_log` trước khi bật và báo lại nếu lệch.

**A3. Tách khoá staff console CRM ra secret riêng (AA-1019 phần còn lại).** Có tiền.
Đề xuất: **Có, làm ngay** (không đợi tenant trả tiền đầu tiên). Chi phí 0,40 USD/tháng (một secret).
Lý do: hôm nay role chạy Content studio đọc được cả khoá staff CRM vì chúng chung một secret; tách ra thì một lỗi ở
studio không lộ khoá staff. Rẻ, làm chung một PR Infra với nhóm A6.

**A4. Đọc Cost Explorer một lần mỗi ngày (AA-1127 C2 "spend truth" + AA-1141 mục 5).** Có tiền.
Đề xuất: **Có, 1 lượt/ngày dùng chung cho hai issue**, có badge "cũ" khi lượt đọc lỗi. Chi phí ≈ 0,30–0,60 USD/tháng
(0,01 USD mỗi lần gọi). Lý do: sổ `llm_call_log` chỉ thấy tiền AI; CE thấy cả ECS, RDS, S3… nên trang chi phí mới khớp
hoá đơn. Nếu muốn rẻ hơn: 1 lượt/tuần (≈ 0,05 USD/tháng) nhưng số trễ tới 7 ngày.

**A5. Kiểm tra từ bên ngoài bằng Route 53 health check (AA-1142 mục 3).** Có tiền.
Đề xuất: **Không**. Dùng cron GitHub Actions (repo public, 0 USD) kiểm DNS, TLS, `/health` mỗi 5–15 phút như issue đã
ghi. Route 53 health check ≈ 0,50–0,75 USD mỗi check mỗi tháng, chỉ đáng khi có prod và cần failover DNS.

**A6. Dọn quyền và secret theo access review S283 (một lô, 0 USD).**
Đề xuất: **Duyệt cả lô**, agent làm theo thứ tự DRY RUN → liệt kê → xoá: F-09 (2 secret E2E cũ không workflow nào đọc),
F-12 (secret không ai đọc từ khi tạo, kiểm người dùng trước), F-13 (môi trường GitHub thời Vercel), F-20 (hash mật khẩu
chết trong `shared.admin_users`), F-24 (9 dòng staff Booking cũ), F-08 (chuyển khoá CI bot + bộ E2E portal vào environment
chỉ `main`), F-04 (đổi Allow `*` của CIS sang danh sách cho phép). Lý do: tất cả là "cửa cũ không ai dùng"; xoá trước pilot.

**A7. Quyền của business owner trong CIS (access review Q-1, hỏi từ S245).**
Đề xuất: **Giữ `cis-admin` và bắt buộc TOTP** cùng đợt MFA admin (AA-1111). Lý do: S283 đã chọn business owner làm người
giữ khoá thứ hai (AA-1110), nên chị cần quyền admin thật; rủi ro nằm ở việc thiếu lớp đăng nhập thứ hai, không ở vai trò.
Phương án khác: `cis-content_lead`, nhưng khi đó diễn tập "chạy không cần agent" thiếu quyền.

**A8. Dọn dữ liệu thử trên Dev (D1 của AA-1127, AA-1128, phần CRM).**
Đề xuất: **Duyệt nguyên tắc ngay**: đổi tên / ngưng (không xoá cứng) các tenant, đại lý, nhà cung cấp, staff thử có mã
issue trong tên; gỡ bán trip plan thử; thay dòng tỷ giá thử; nhập ngày lễ 2026–2027; thêm lint chặn tên `AA-\d+` trong seed.
Phần **xoá cứng** (nếu có) thì agent trình danh sách DRY RUN trên trang duyệt rồi mới chạy. 0 USD. Lý do: dữ liệu thử
đang lẫn vào ảnh chụp và trang Jira cho chị Thư (vd. PR-30 phải ghi rõ "dữ liệu giả lập").

**A9. Kênh cảnh báo thứ hai (AA-1110).**
S283 tech lead đã chọn "chưa cần", nhưng Done-when của AA-1110 vẫn ghi "báo động tới kênh thứ hai" nên issue bị kẹt.
Đề xuất: **Giữ "chưa cần" và sửa Done-when**: thêm e-mail SNS thứ hai (hộp thư công ty của business owner) trong buổi
diễn tập người giữ khoá đầu tháng 12 (đã chốt S283). 0 USD. Terraform đã có subscription thứ hai, đang tắt.

---

## B. Bước tay chỉ tech lead làm được

**B1. Tin Zalo cho TrueIDC — hạn 20/11 (AA-1004, nháp `.tmp-session/S275/trueidc-zalo.txt`).** Chưa thấy bằng chứng đã gửi.
Câu 1–2 trong nháp đã có câu trả lời từ kiểm tra S283 (tài khoản tự rời org được, tạo role org được), và việc bật cost
allocation tag nay làm từ org công ty sau 01/12. Đề xuất gửi bản rút gọn: chỉ hỏi câu 3–4 (công cụ của TrueIDC còn lại
trong tài khoản, liên hệ/thanh toán) + tình trạng phụ lục. Agent soạn lại 3–4 dòng nếu anh muốn.

**B2. Đăng ký TOTP cho chính anh trước khi bắt buộc MFA admin (AA-1111).**
Khi lane AA-1111 S2 xong, agent gửi đường đăng ký; anh chỉ: mở trang đăng nhập staff → bước thiết lập Authenticator →
quét QR bằng Google/Microsoft Authenticator → nhập mã 6 số. Lưu ý: sau khi có TOTP, anh đăng nhập bằng **mật khẩu + mã 6
số**; mã e-mail không còn dùng làm lớp đầu (ADR 0006). Business owner làm tương tự sau (A7).

**B3. Tắt VPN để agent chụp ảnh AA-1126.** WAF chặn admin CIS (403) khi máy đi qua VPN.
Bấm: Kaspersky → VPN → Tắt → mở `https://ipinfo.io` kiểm `country` là VN → báo agent "đã tắt VPN". Xong thì bật lại.

**B4. Một cửa sổ tắt auto mode (gom các lệnh bị chặn).**
Gồm: xoá file `~/.aws/*.bak-s283` (anh đã cho agent xoá) và các lệnh xoá của lô A6 nếu duyệt.
Bấm: trong Claude Code nhấn `Shift+Tab` tới khi không còn "auto" → báo agent → agent chạy → bật lại.

**B5. Bật tự nghiên cứu DataForSEO từ 01/12 (AA-1122, duyệt S282, trần 5 USD/tháng).** Hạn: trước 01/12.
Mở `https://aa-cis.lumiguides.it.com/admin/platform/settings` → tìm `cis.seo.research_auto_enabled` → giá trị `true` →
*Effective from* `01/12/2026` → *Reason*: `Enable automatic DFS research from 01/12 per S282 decision, cap 5 USD/month` → Save.

**B6. Billing Transfer — các ngày cố định (AA-1004).**
25–28/11: tải hoá đơn / bảng kê acc2 từ cổng TrueIDC (sau khi rời org sẽ không xem lại được).
01/12: đăng nhập SSO org công ty (`aws sso login --sso-session aa-mgmt-sso --no-browser`) → chấp nhận lời mời cho acc2;
agent kiểm `/health`, ECS, RDS ngay sau đó. 25–30/11: đổi e-mail root acc1 sang hộp thư công ty; ≥ 02/12: thẻ, MST, MFA root.

**B7. Tắt quyền tạo repo của thành viên GitHub (access review F-16, 0 USD).**
`https://github.com/organizations/AdventureAsia365-Ecosys/settings/member_privileges` → *Repository creation* → bỏ chọn
*Public* và *Private* → Save. Kèm F-03: `…/AA-CIS-Infra/settings/environments` → `dev` → *Deployment branches* →
*Selected branches* → thêm `main` → Save.

**B8. Thu hồi 4 PAT (token GitHub cá nhân) không dùng.**
`https://github.com/settings/personal-access-tokens` → xoá `aa-cis-infra-schema-dump`, `ACPCORE_READ_TOKEN`,
`aa-cis-acpcore-read` và token cũ của `ROOT_REPO_DOCS_TOKEN` (cả mục *Tokens (classic)*). Agent không kiểm được trang này.

**B9. Không gấp, chỉ khi cần:** (a) mở lại phiên Claude Code để connector Sentry nạp lại (đọc issue Sentry);
(b) site WordPress test mới + Application Password cho một lượt publish thật (AA-1040, AA-1039);
(c) app Microsoft 365 cho đại lý dùng M365 (AA-1011) — chỉ khi có đại lý thật dùng M365.

---

## C. Đã cũ hoặc đã chốt — đề xuất gạch khỏi danh sách chờ

| # | Mục | Bằng chứng |
|---|---|---|
| C1 | 32 quyết định nguồn cung (T1–T19, B1–B13) | Trang quyết định đọc live: 32/32 "yes"; B2 bấm lại lúc 04:22Z sau tư vấn vòng 2 → phương án C chốt, đã vào AA-1152 |
| C2 | 13 quyết định gateway + tên (G1–G6, I1–I7, I4 sửa) | `decisions-gateway-identity.md`; G6, I3 còn nợ phần tư vấn → trả lời ở mục E dưới |
| C3 | AA-1138 trần CRM + chuyển `crm_draft_reply` sang Haiku | Infra #921 merged; `crm/078` applied, `/crm/health/ready` báo `crm-078`; còn lại là việc agent: Partner #354 đỏ "Vendored CIS copies" |
| C4 | AA-1051 chạy trả phí | Đã duyệt (T9 ≤ 15, S1 ≤ 8, T2 ≤ 5 USD); gán nhãn thêm mẫu là việc agent (memory "claude audits quality") |
| C5 | Liên hệ BILLING thay thế acc2 | Tech lead thêm 17/11; kiểm 1.7 đạt (`aa1004-org-move-checks.md`) |
| C6 | Cost allocation tag qua TrueIDC | Thay bằng bật từ org công ty ≥ 02/12 (check trong `plan.json`) |
| C7 | Chen Llama 4 Maverick trước OpenAI (AA-1026) | Đường LLM đổi S278: Claude/GPT chạy Bedrock acc1; câu hỏi không còn nghĩa |
| C8 | Câu hỏi Sunny Cloud / IDS Vietnam; đoạn "LLM path S260/S262" | Đường LLM đã giải quyết bằng acc1 (S278); không còn cần reseller thứ ba |
| C9 | Nháp Jira S262, S265, S266, S281 | Đã đăng (02/11; S281: 10657–10661) |
| C10 | Trần OpenAI (AA-1018), khoá Anthropic | Đặt S263; khoá Anthropic cắm S269 |
| C11 | AA-1008 H3 required checks | Issue Done |
| C12 | AA-1021 chuỗi video/bài viết | Issue Canceled |
| C13 | AA-948 engine bản đồ dùng chung | Chốt S283 "shared-quote": agent báo giá Mapbox trước khi làm |
| C14 | AA-1059 25 tour thô chờ duyệt S1 | Thuộc Review Queue; memory "review-queue-no-reminders": không đưa vào danh sách hỏi |
| C15 | AA-1049 `T9_FAQ_LLM_FILTER` giữ hay tắt | Đang bật từ S247, không lỗi; đề xuất giữ nguyên, bỏ câu hỏi (anh muốn tắt thì báo) |
| C16 | Phân xử A/B S1 30 bài (S251); AA-900 40 nhãn | Writer v2 là mặc định vĩnh viễn (S250); nhãn do agent làm |
| C17 | Mật khẩu ứng dụng TasteWP | Site TasteWP cũ đã hết hạn (S266) |
| C18 | Gói video TripPlanner-intro lên Drive | Agent tự đưa lên bằng rclone (memory GDrive), không cần tech lead |

Cũng đã chốt, chỉ nhắc để khỏi hỏi lại: MFA admin = TOTP (S283), role agent chỉ đọc = có (S283), bỏ luật WAF geo cho
host staff sau MFA (S285), fork-PR approval đã bật, go-live = "chưa hỏi" (S283).

---

## D. Việc của business owner (gom vào nháp Jira cuối phiên, không quyết ở đây)

1. **Ký phụ lục TrueIDC cho Billing Transfer** (AA-1004); role tổ chức trên acc2 chờ tới khi ký.
2. **Người giữ khoá thứ hai + buổi 60 phút đầu tháng 12** (thử quyền, diễn tập deploy/rollback, tabletop) — S283 đã chọn
   business owner; cần chị xác nhận lịch.
3. **Câu điều khoản đối tác về bảo hiểm (B10):** đại lý tự đảm bảo được phép bán bảo hiểm ở nước mình — lời văn pháp lý,
   luật sư hay không là việc của chị.
4. **Danh sách giấy tờ nhà cung cấp theo nước** (MST, giấy phép lữ hành…) cho hồ sơ nhà cung cấp AA-1150.
5. **Hiện giá "từ X/khách" trên trang đại lý (B2 phương án C):** báo chị khi tính năng chạy (AA-1152), vì nó đổi điều ADR
   0019 b5 "không hiện giá AA"; chỉ báo khi xong, không hỏi trước.
6. **10 giá trị mặc định M-OD** (AA-1066, Jira PR-26 comment 10636) — hệ thống dùng đề xuất tới khi có trả lời.
7. **Thuế, % đặt cọc, đánh dấu thanh toán** (AA-682); **điều khoản AI, /privacy, /terms, luật sư** (AA-820).
8. **Tháng go-live mục tiêu**: S283 tech lead chọn "chưa hỏi" — giữ nguyên, chỉ ghi để không mất.

---

## E. Trả lời nốt hai phần tư vấn còn nợ (G6, I3)

**G6 — "mỗi app một key" khi dùng Bedrock.** Bedrock không cần key như API Anthropic: app gọi bằng IAM role. Cách chuẩn để
tách theo app, 0 USD thêm:
(1) mỗi app một role gọi riêng (hoặc cùng role `AA1-Bedrock-Invoker` nhưng ExternalId/tên phiên khác nhau) — chặn/thu hồi
được từng app; (2) mỗi app một **application inference profile** gắn tag `App=cis|crm|tripplanner` — AWS ghi chi phí theo
profile, Cost Explorer tách được theo app, giá token không đổi (tài liệu AWS: "no additional charges for cost attribution").
Đề xuất: làm (2) trước khi TripPlanner chuyển sang acc1 (G5), (1) làm khi tách prod.

**I3 — thị trường cho người dùng tự sửa tên thế nào.** Slack, Google Workspace, Microsoft 365, HubSpot đều cho người dùng
tự sửa tên hiển thị; admin có công tắc khoá việc này (Workspace/M365 khi tên lấy từ danh bạ công ty). Mẫu chung: **tên hiển
thị** tự sửa, **tên pháp lý / e-mail** do admin giữ, mọi lần đổi ghi log. Khớp I3 + I7: đại lý tự sửa tên trong CRM; staff
AA đổi qua thủ tục có log vì Cognito `name` là gốc. Mức chắc chắn: cao với Slack/Workspace, chưa kiểm lại hôm nay.

---

## F. Bảng tiền (mọi mục có chi phí)

| Mục | Chi phí | Đề xuất | Trạng thái |
|---|---|---|---|
| A1 KMS khoá ngân hàng | ≈ 1 USD/tháng | Có | chờ duyệt |
| A2 Trần T2 tự chạy lại | trần 10 USD/tháng (trong ngân sách sẵn) | Có | chờ duyệt |
| A3 Tách secret staff CRM | 0,40 USD/tháng | Có | chờ duyệt |
| A4 Cost Explorer hằng ngày | 0,30–0,60 USD/tháng | Có | chờ duyệt |
| A5 Route 53 health check | 0,50–0,75 USD/check/tháng | Không (dùng GitHub Actions 0 USD) | chờ duyệt |
| Ảnh tour trên S3 (AA-1148) | < 0,10 USD/tháng (vài GB, bucket sẵn có) | coi như gồm trong T4 | đã duyệt cùng T4 |
| AA-1051 chạy trả phí | T9 ≤ 15, S1 ≤ 8, T2 ≤ 5 USD | — | đã duyệt S285 |
| DFS tự nghiên cứu | ≤ 5 USD/tháng từ 01/12 | — | đã duyệt S282, chờ bước tay B5 |
| GuardDuty | 15–20 USD/tháng | giữ tắt | đã hoãn, không hỏi lại tới trước prod |
| VPC interface endpoint | 75–90 USD/tháng | chỉ prod | hỏi khi dựng prod |
| Mapbox cho bản đồ CRM | chưa báo giá | agent báo giá trước | parked (S283) |
| OTel spike | — | giữ tắt | đã hoãn |
