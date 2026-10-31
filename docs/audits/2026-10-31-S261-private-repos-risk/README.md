---
id: OPS-08-s261-private-repos-risk
title: "Chuyển repo gốc và AA-CIS-Infra về private từ 01/11: rủi ro hết phút CI và mất tính năng GitHub (S261)"
description: "Bản tư vấn cho tech lead: nếu root và Infra về private trên GitHub Free thì phút Actions hết vào ngày nào, tính năng nào tắt và pipeline nào gãy, bốn phương án kèm chi phí và rủi ro, checklist ngày chuyển, và nội dung nhạy cảm đang public trong Infra cần rút gọn."
type: report
status: active
owner: nghiep
audience: [engineer]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-1004]
---

# Chuyển repo gốc và AA-CIS-Infra về private từ 01/11: rủi ro hết phút CI (S261, 31/10/2026)

Bản tư vấn viết cho tech lead (tiếng Việt, theo luật `docs/audits`). Tác nhân: Claude Code. Cả ba phần đo đạc đều
**chỉ đọc**: `gh api`, `gh run list`, GraphQL check runs, API billing của org. Không đổi setting nào, không push gì.
Org `AdventureAsia365-Ecosys` đang ở gói **Free** (2 seat). Cả 6 repo hiện public, root và Infra đều có 0 fork, 0 star.

Câu hỏi gốc: qua ngày 01/11 nên chuyển repo gốc và Infra về private (kế hoạch trong ADR 0014, Amendment S247), nhưng
cần đánh giá rủi ro CI bị chặn vì hết phút free của GitHub.

## 0. Quyết định của tech lead (31/10/2026, S261)

**Giữ cả repo gốc và AA-CIS-Infra ở public, không trả thêm tiền cho GitHub** (không payment method, không gói Team,
không self-hosted runner). Các phương án B/C/D bên dưới và checklist mục 5 **không áp dụng**; báo cáo giữ lại làm
tư liệu. Mật khẩu DataForSEO lộ trong lịch sử Infra **đã được xoay từ S251 (25/10/2026)**: tech lead đổi trên dashboard
nhà cung cấp, agent cập nhật secret (AWS `LastChangedDate` 25/10/2026, đọc lại S261). Các dòng nói "chưa xoay / xoay
ngay" ở mục 1, 4, 5, 6 lấy từ một dòng secrets register chưa được cập nhật sau S251 (đã sửa S261), nên không còn đúng.
Phần rút gọn ghi chú nhạy cảm ở mục 6 đã làm: Infra #543. TL-7: tech lead quyết chưa làm (Chi tiết trong Linear AA-873; đã vá ở Infra #541).

## 1. Trả lời ngắn

- **Có, vượt rất xa.** Ở nhịp hiện tại, root và Infra chạy khoảng **880 phút billable/ngày, tức khoảng 26.300
  phút/tháng**, gấp **13 lần** hạn mức 2.000 phút của Free. Nếu lật cả hai repo ngày 01/11, phút hết vào khoảng
  **03/11** (lên Team với 3.000 phút thì chỉ lùi tới khoảng 04/11). Chuyện này đã xảy ra một lần vào ngày 22/10.
- **Khi hết phút, những thứ sau gãy:** GitHub chặn mọi job của repo private nếu org chưa có payment method. Terraform
  Apply, DB Migrate, Migration Apply, DB Schema Dump, gitleaks và Docs sync đều dừng. DB Migrate trên Infra là đường
  duy nhất để áp migration, nên mọi deploy của 4 app cần schema mới sẽ đứng ở `schema-gate` rồi đỏ.
- **Kể cả khi còn phút, vẫn mất một số tính năng** trên Infra private gói Free: ruleset và 5 check bắt buộc, tự áp
  migration expand, bot tự merge copy PR, secret theo environment (rủi ro), required reviewer của env `org`, secret
  scanning và push protection.
- **Đề xuất (tech lead quyết): phương án D.**
  - **01/11:** chỉ lật **repo gốc** sang private, sau khi đã giảm phút cho root và org owner đã thêm payment method
    kèm budget nhỏ (khoảng 10 USD/tháng).
  - **Infra giữ public** tới khi hết giai đoạn code, hoặc muộn nhất là trước prod đầu tiên (AA-880). Trong lúc chờ:
    xoay mật khẩu DataForSEO ngay, rút gọn các dòng nhạy cảm ở mục 6 (TL-7: chi tiết trong Linear AA-873; đã vá ở Infra #541).
  - Khi lật Infra thì chọn B (Team cộng phút trả thêm, khoảng 80–150 USD/tháng) hoặc self-hosted runner (cần duyệt
    chi phí AWS riêng).
  - Nếu tech lead muốn Infra private ngay vì bề mặt tấn công, chọn **B** từ 01/11. Chi phí khoảng 150 USD/tháng
    (khoảng 80–105 USD nếu đã giảm phút), và chấp nhận một click tay cho mỗi migration expand cho tới khi sửa guard.

## 2. Số phút đo được

### Cách đo

- Liệt kê mọi workflow run tạo trong tháng 10 của cả 6 repo (REST, tách theo ngày để không chạm trần 1.000 kết quả):
  root 1.223 run, Infra 3.951 run.
- Lấy mọi job attempt của từng run (GraphQL `checkSuite.checkRuns`), bỏ job skipped (0 giây). Mỗi job được **làm
  tròn lên** phút nguyên, đúng luật tính tiền của GitHub.
- **Đối chiếu với billing thật của GitHub** (`/organizations/AdventureAsia365-Ecosys/settings/billing/usage`): lệch
  khoảng 1–2% ở mọi repo (root 2.393 so với 2.390; Infra 7.002 so với 6.917). Dữ liệu billing cũng cho thấy đúng lúc
  bị chặn ngày 22/10: root và Infra cộng lại vượt 2.000 phút đúng ngày đó.
- Một lần đo thứ hai, độc lập (lấy mẫu thời gian job của tuần 24–30/10), ra khoảng **26.600 phút/30 ngày**, khớp con
  số trên.
- Mọi job chạy trên `ubuntu-*` (Linux x64, 0,006 USD/phút). Không có Windows hay macOS.

### Tổng hợp

| | Root (AA-Ecosys) | Infra (AA-CIS-Infra) | Root + Infra |
|---|---|---|---|
| Phút billable, 30 ngày gần nhất (tháng 10) | **2.393** | **7.002** | **9.395** |
| Phút thô (trước khi làm tròn) | 1.763 | 3.702 | 5.465 |
| Phần do làm tròn lên từng job | 26% | **47%** | 42% |
| Nhịp hiện tại, phút/ngày (trung bình 24–30/10) | 275 | 603 | **878** |
| Dự phóng một tháng ở nhịp đó | ~8.240 | ~18.080 | **~26.300** (khoảng 25.300–26.600) |
| Lật riêng repo này thì hết 2.000 phút sau | ~7 ngày | ~3 ngày | **~2,3 ngày (khoảng 03/11)** |

Phút theo tuần (tăng theo nhịp PR của giai đoạn dev; Infra nhận khoảng 20–35 PR/ngày, phần lớn là copy PR của agent
và bot):

| Tuần | Root | Infra |
|---|---|---|
| 01–07/10 | 0 | 7 |
| 08–14/10 | 0 | 164 |
| 15–21/10 | 78 | 1.350 |
| 22–28/10 | 1.408 | 4.191 |
| 29–31/10 (khoảng 2,5 ngày) | 907 | 1.290 |

### Root theo workflow (tháng 10)

| Workflow | Trigger | Run | Phút billable | 7 ngày gần nhất |
|---|---|---|---|---|
| **Secret Scan (full history)** | **push lên master** + hằng đêm | 196 (188 do push) | **1.316 (55%)** | 1.179 |
| Docs lint | PR, cron thứ Hai | 490 | 508 | 306 |
| Secret Scan (PR) | `pull_request(_target)`, push | 381 | 405 | 305 |
| Docs sync (đẩy docs cho `/admin/docs`) | PR, push | 96 | 99 | 95 |
| Contracts | PR | 56 | 57 | 36 |

### Infra theo workflow (tháng 10)

| Workflow | Trigger | Run | Phút billable | 7 ngày gần nhất |
|---|---|---|---|---|
| Migration Copy Guard | PR + hằng đêm (3 job/PR) | 315 | **1.077** | 705 |
| DB Migrate | dispatch | 421 | **883** | 363 |
| Terraform Plan | PR | 525 | **785** | 388 |
| DB Schema Dump | hằng đêm + 227 dispatch (sau mỗi apply) | 242 | **753** | 474 |
| Secret Scan (full history) | **push lên main** + hằng đêm | 229 | 560 | 493 |
| Secret Scan (PR) | PR | 489 | 487 | 227 |
| DB Isolation Probe | hằng đêm + dispatch | 218 | 432 | 215 |
| Terraform Apply Prod | dispatch | 133 | 375 | 183 |
| Connection Budget | PR, push, hằng đêm | 295 | 314 | 234 |
| Docs Gen Tests, ALB Rule Order, Docs lint, Managed Login Branding, Identity Trigger Tests | PR, push | 750 | 808 | 561 |
| Migration Apply (tự áp expand), mới từ 29/10 | push, **cron mỗi giờ**, dispatch | 38 | 142 | 110 |
| Docs Gen (nightly) | cron | 80 | 136 | 97 |
| Migration Sync, mới từ 29/10 | **cron mỗi 10 phút**, issue_comment, workflow_run | 95 | 94 | 81 |
| Drift, Freshness, Liveness, CRM key diff, Contract Copy Guard, test khác, Dependabot | | | ~120 | |

Hai rủi ro ẩn trong bảng:

- **Cron dày:** `migration-sync.yml` chạy cron `4-59/10 * * * *`, `migration-apply.yml` chạy mỗi giờ (2 job/run).
  Hiện GitHub đang bỏ phần lớn các lần chạy theo lịch: từ 29/10 chỉ 8 trong khoảng 360 lần Migration Sync theo lịch
  thực sự chạy. Nếu GitHub chạy đủ lịch, riêng hai cron này đã thêm **tối đa khoảng 5.700 phút/tháng**.
- **Làm tròn:** 2.869 trong 5.126 job của Infra chạy không quá 30 giây nhưng vẫn bị tính tròn 1 phút.
- **Mức nền khi không ai làm gì** (chỉ còn cron) khoảng **1.000 phút/tháng**, đã bằng nửa hạn mức Free.

### So với hạn mức và giá

| Gói | Phút có sẵn/tháng | Root + Infra ở nhịp hiện tại | Sau khi giảm phút (ước tính 15.000–19.000) |
|---|---|---|---|
| Free, chưa có payment method | 2.000 | **Bị chặn từ khoảng 03/11** | Bị chặn sau khoảng 3–4 ngày |
| Free + payment method + budget | 2.000 + trả phần vượt | ~146 USD/tháng | ~78–102 USD/tháng |
| Team (2 seat × 4 USD) | 3.000 + trả phần vượt | ~140 + 8 ≈ **148 USD/tháng** | ~80–104 USD/tháng |
| **Chỉ root private (phương án D), đã giảm phút** | 2.000 | ~3.400 phút → vượt ~1.400 ≈ **8 USD/tháng** | ~2.000–2.500 nếu gộp thêm các check PR của root (ước tính) |

- Giá vượt: Linux x64 0,006 USD/phút, arm64 0,005 USD/phút, làm tròn lên phút theo từng job.
- Con số **37 USD/tháng trong ADR 0014 đã lỗi thời.** Nó tính từ phút của các app repo tháng 9 theo giá cũ.
- Dung lượng không phải rủi ro: artifact của Infra 88 MB (Free cho 500 MB), root gần 0; cache 154 MB / 8 MB (10 GB
  mỗi repo, miễn phí).
- Bốn app repo **không nên** về private: tổng 6 repo dự phóng khoảng 204.000 phút/tháng (khoảng 1.200 USD/tháng).
  Ngoài ra merge queue trên repo private chỉ có ở Enterprise Cloud, và artifact của CIS-App (3,5 GB) vượt cả mức Team.

## 3. Tính năng mất khi private trên Free và ảnh hưởng tới pipeline

| Tính năng | Đang dùng ở đâu | Gãy gì khi private Free | Cách xử lý |
|---|---|---|---|
| **Phút Actions** | Mọi workflow của root và Infra | Hết sau khoảng 2–3 ngày. Infra kéo theo migration của cả 4 app; root kéo theo Docs sync (`/admin/docs` không cập nhật) và bot merge PR `bot/db-schema-reference` (cần check `Docs lint`, `gitleaks` chạy xong) | Giảm phút (mục 4) cộng payment method và budget, hoặc giữ repo public |
| **Ruleset + 5 check bắt buộc** | Infra: ruleset "main: PR and required checks (AA-993 I1)": bắt PR, chỉ squash, cấm force-push và xoá, 5 check (`Terraform Plan (dev)`, `gitleaks`, `Copies match owner main`, `Migration lint and unique numbers`, `Expand classify`). Đây là hàng rào giữ ci-bot chỉ merge copy PR xanh. Root: không có ruleset | Ruleset vẫn còn nhưng **không được thực thi**: push thẳng `main`, force-push, merge khi check đỏ đều làm được. Gác cổng quay về kỷ luật agent (aa-ship) | Team lấy lại ruleset. Root không đổi gì |
| **Tự áp migration expand** (ADR 0017 d8) | `migration-apply.yml`, biến `DB_AUTO_APPLY=true`, guard kiểm `private == false` và có ruleset | Tự tắt an toàn (`allowed=false`, chỉ liệt kê). Mỗi migration expand lại cần một người chạy DB Migrate `apply` | Chấp nhận một click tay mỗi migration; hoặc lên Team **và** sửa guard `private == false`, amend ADR 0017 d8 |
| **Bot merge copy PR** | `migration-sync.yml` (merge pass), guard giống trên | Tự tắt: agent điều phối phải merge tay từng copy PR | Như dòng trên |
| **Secret theo environment** | Infra: `AWS_ROLE_ARN` trên env `prod` (role apply) và `dev-db-auto` (role db-auto-apply). Cấp repo, `AWS_ROLE_ARN` là role plan | Docs của GitHub nói không có trên private Free. Thực tế 14–22/10 Infra private mà Terraform Apply (env `prod`) vẫn chạy được khoảng 15 lần, tức env secret vẫn được đọc. Nếu GitHub làm đúng docs: Terraform Apply, DB Migrate, Schema Dump, các Probe nhận ARN role plan và bị AccessDenied | Kiểm ngay sau khi lật (`db-auto-apply-role-check`, DB Migrate `check`). Dự phòng: đổi sang secret cấp repo tên riêng (ví dụ `AWS_APPLY_ROLE_ARN`). ARN không phải bí mật; hàng rào thật là trust IAM (`environment:prod` + `ref` main, AA-866). Team có env secret trên private |
| **Deployment branch policy** | `dev-db-auto` và `org`: chỉ `main` | Mất trên Free | Không thành lỗ hổng: trust IAM của `aa-cis-infra-db-auto-apply` và `tf-apply` đã đòi `ref=refs/heads/main`. Team lấy lại được |
| **Required reviewer trên environment** | Env `org`: reviewer bắt buộc là tech lead | Mất, và **Team cũng không có** (chỉ Enterprise). Job `terraform-apply-management` đọc `environments/org` và từ chối apply khi không thấy reviewer, nên root `management` khả năng cao **không apply được qua CI**. Nếu API vẫn trả reviewer mà GitHub không thực thi thì job chạy không ai duyệt | Đổi guard sang phương án B của ADR 0014 (dispatch tay, kiểm `github.actor` là tech lead, giữ digest của plan); hoặc apply `management` từ máy với profile `aa-mgmt` có MFA |
| **Secret scanning + push protection** | Bật trên cả hai repo | Tắt (cần GitHub Secret Protection, khoảng 19 USD/committer/tháng) | Không mua (ADR 0014 Amendment 2): gitleaks PR và full-history là máy quét duy nhất. Nếu hết phút thì gitleaks cũng dừng |
| **App repo đọc Infra không cần token** | (a) `Migration preflight` trong `ci.yml` của CIS, Booking, Partner clone Infra ẩn danh; (b) `schema_gate.py` đọc Actions API của Infra | (a) Chỉ cảnh báo "not readable (private?)", bỏ bước classify, không phải check bắt buộc. (b) Đã thiết kế sẵn: 404 thì chỉ kiểm `registered_keys` | Chấp nhận; `Expand classify` của Infra vẫn là nơi quyết định |
| **Link runbook trong alarm** | `alarm_runbooks.tf`: `runbook_base_url` trỏ tới `github.com/.../AA-Ecosys/blob/master/docs/ops` | Ai chưa đăng nhập GitHub (hoặc không phải member org) mở link sẽ thấy 404 | Chấp nhận (người trực là member). Sau này có thể trỏ sang `/admin/docs` |
| **CODEOWNERS** | Có file, không thực thi (`require_code_owner_review: false`) | Không đổi gì so với hiện tại | Quyết lúc có prod (AA-880) |
| **Merge queue** | Root và Infra không dùng | Không ảnh hưởng (app repo vẫn public) | — |
| Dependabot alerts / security updates, dependency graph | Bật | Vẫn chạy | — |
| OIDC sang AWS, GitHub App `aa-agent` / ci-bot | Mọi workflow AWS; `as-app.sh`; `migration-sync-wake` ghi Issues vào Infra | Vẫn chạy (đã chứng minh qua các lần apply 14–22/10) | Sau khi lật, thử một lần đọc bằng token App |

## 4. Phương án

| Phương án | Chi phí/tháng (ước tính) | Giữ được | Rủi ro / mất gì |
|---|---|---|---|
| **A. Giữ cả hai public** tới khi hết giai đoạn code hoặc trước prod đầu tiên (AA-880) | 0 USD | Toàn bộ: phút, ruleset, auto-apply, env reviewer, secret scanning | Nội dung DM-6.10 tiếp tục public, kể cả commit mới. Lưu ý: lịch sử đã public từ 22/10 và đã bị GitGuardian quét, nên lật private **không thu hồi** được gì đã lộ. Phải rút gọn nội dung (mục 6) và giữ luật "commit mới như repo public" |
| **B. Cả hai private + GitHub Team** (2 seat × 4 USD) + payment method trả phần vượt | ~148 USD; ~80–104 USD nếu giảm phút | Ruleset, check bắt buộc, env secret, deployment branch | Required reviewer của `org` (chỉ Enterprise), secret scanning (+19 USD/committer). Auto-apply và bot merge vẫn tắt cho tới khi sửa guard `private == false` |
| **C. Cả hai private trên Free**, chấp nhận thao tác tay và dời check | Không có payment method: 0 USD nhưng **bị chặn từ khoảng 03/11**. Có payment method: ~146 USD, hoặc ~78–102 USD nếu giảm phút | Phút (nếu trả tiền), OIDC, App | Mất ruleset, auto-apply, bot merge, env reviewer, branch policy; env secret có thể gãy bất cứ lúc nào (hành vi ngoài docs). Mỗi migration thêm việc tay. Dời check sang máy local thì mất bằng chứng CI |
| **D. Chỉ root private, Infra giữ public** tới khi hết giai đoạn code hoặc trước prod đầu tiên | Root đã giảm phút ~3.400 phút → **~8 USD** (cần payment method + budget); 0 USD nếu gộp check PR xuống dưới 2.000 | Mọi gác cổng của Infra, auto-apply, env reviewer `org`, secret scanning của Infra | Root mất secret scanning (gitleaks thay). Infra vẫn public nên phải làm mục 6 và đặt rule cho env `prod`. Root mà hết phút thì `/admin/docs` và PR schema-reference đứng (không chặn deploy app) |
| Biến thể của B/C: **self-hosted runner** cho Infra (EC2 nhỏ ở acc2) | Phút self-hosted miễn phí; EC2 khoảng 15–30 USD + công vận hành. **Cần tech lead đồng ý riêng khoản AWS mới** | Phút | Đổi `runs-on` ở 27 workflow; runner phải ephemeral và được hardening vì giữ quyền Terraform/OIDC; tính năng gói Free vẫn mất như C |

**Vì sao đề xuất D:**

- Root dùng ít phút. Sau khi bỏ trigger `push` của Secret Scan full history, root chỉ còn khoảng 115 phút/ngày.
  Root cũng không có ruleset hay environment nào để mất.
- Lật Infra là lật đúng chỗ đắt nhất (603 phút/ngày) và là chỗ gác cổng tự động của migration toàn hệ.
- Lật Infra sớm không xoá được phần đã lộ: lịch sử đã public 9 ngày và đã bị quét. Rủi ro thật sự giảm được nhờ xoay
  DataForSEO, rút gọn HEAD (mục 6) và đặt rule cho `prod`.
- Thời điểm lật Infra: khi nhịp PR Infra giảm (hết giai đoạn code) hoặc trước prod đầu tiên, tuỳ cái nào tới trước.
  Lúc đó amend ADR 0014 lần 3: chọn B hoặc self-hosted runner, sửa guard `terraform-apply-management`, tách secret
  role apply ra cấp repo.

## 5. Checklist ngày chuyển

Thứ tự bên dưới áp cho D. Nếu chọn B hoặc C thì làm thêm các dòng có ghi "(Infra)".

| # | Khi nào | Việc | Ai làm |
|---|---|---|---|
| 1 | 31/10–01/11 | Chốt phương án và duyệt rõ khoản chi: payment method, budget Actions (D: khoảng 10 USD; B: khoảng 150 USD); ghi vào ADR 0014 Amendment 3 | Tech lead |
| 2 | Trước khi lật | Xoay mật khẩu DataForSEO theo đường AA-981; kiểm RDS master có trùng giá trị cũ không | Agent + tech lead (đăng nhập dashboard nhà cung cấp) |
| 3 | Trước khi lật | PR giảm phút cho root: `secret-scan-history.yml` chỉ chạy hằng đêm (bỏ trigger push); gộp Docs lint, Contracts và check của Docs sync vào ít job nhất. (Infra) cùng việc đó, cộng bỏ cron `*/10` của Migration Sync và cron mỗi giờ của Migration Apply, chỉ giữ trigger theo sự kiện | Agent; PR sửa workflow là thay đổi rủi ro nên cần agent review trước khi merge |
| 4 | Trước khi lật | (Infra) Sửa guard `terraform-apply-management` (phương án B của ADR 0014); đổi `AWS_ROLE_ARN` của env sang secret cấp repo tên riêng; sửa guard `private == false` nếu đã lên Team | Agent |
| 5 | Trước khi lật | Chụp lại setting hiện tại vào thư mục audit: ruleset, `environments`, `security_and_analysis`, danh sách secret/biến (chỉ tên) | Agent (`gh api`, chỉ đọc) |
| 6 | Trước khi lật | Không có job trong `shared.job` / `booking.job` / `crm.job`, không có wave, không có DB Migrate hay Terraform Apply đang chạy, không còn copy PR Infra đang chờ | Agent |
| 7 | Ngay trước khi lật | Org owner thêm payment method, đặt budget cho Actions và bật dừng khi chạm budget (không bị chặn cứng như 22/10, cũng không trả quá tay). (B) Nâng gói Team | Tech lead (**chỉ owner org làm được**; token agent không có scope `admin:org`) |
| 8 | 01/11 | Đổi visibility: Settings → General → Danger Zone → Change visibility → Private, hoặc `gh repo edit AdventureAsia365-Ecosys/AA-Ecosys --visibility private --accept-visibility-change-consequences`. Repo có 0 fork nên không có fork public bị tách ra | Tech lead (owner org; App `aa-agent` không có quyền admin repo) |
| 9 | Ngay sau khi lật | Đọc lại: `visibility`, ruleset, `environments`, `security_and_analysis`. Chạy thử Docs sync, Secret Scan (PR) trên một PR nhỏ, và token App đọc repo. (Infra) `db-auto-apply-role-check`, DB Migrate `check`, Terraform Plan; kiểm `environments/org` còn trả reviewer không | Agent |
| 10 | Tuần đầu (01–07/11) | Mỗi ngày đọc phút đã dùng (API billing của org hoặc trang Billing) so với dự phóng; nếu vượt nhịp dự kiến 20% thì tìm workflow gây ra và cắt | Agent đọc số; tech lead xem trang billing nếu token thiếu quyền |
| 11 | Cuối tuần đầu | Ghi kết quả thật vào ADR 0014 Amendment 3 và log phiên; cập nhật `docs/security/secrets-register.md` (DataForSEO đã xoay) | Agent |

## 6. Nội dung nhạy cảm đang public trong Infra và đề xuất rút gọn ngay

Rà trên `main` d0ac9dd ngày 31/10, chỉ đọc. Account ID không tính vào đây (đã chấp nhận để lộ). Kết quả: 2 mục
cao, 6 mục trung bình, 6 mục thấp/thông tin, trong 14 file (ghi chú triển khai, comment Terraform, workflow).

Bản public này không liệt kê từng dòng, đường đi hay quyền cụ thể. Chi tiết trong Linear AA-873; đã vá ở Infra #541. Phần rút gọn các ghi chú nhạy cảm ở HEAD của
Infra đã làm ở Infra #543. Sửa ở HEAD không xoá được bản cũ trong lịch sử git; mật khẩu DataForSEO đã xoay từ S251
(xem mục 0). Phần còn lại (TL-7): tech lead quyết chưa làm.

## 7. Nguồn

- [Billing for GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions): Free cho
  org 12 USD compute (khoảng 2.000 phút Linux) và 500 MB artifact; Team 18 USD (3.000 phút) và 2 GB; runner chuẩn
  trên repo public và self-hosted runner miễn phí; chặn khi hết hạn mức nếu chưa có payment method.
- [Actions runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing): Linux x64
  0,006 USD/phút, arm64 0,005 USD/phút, làm tròn lên theo job.
- [GitHub pricing](https://github.com/pricing) và [GitHub's plans](https://docs.github.com/en/get-started/learning-about-github/githubs-plans):
  Team 4 USD/user/tháng; repository rules, code owners, environment secrets và deployment branches trên private cần Team.
- [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments):
  required reviewer và wait timer trên Free/Pro/Team chỉ cho repo public.
- [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets),
  [Creating rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository).
- [Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue),
  [Merge queue GA](https://github.blog/changelog/2023-07-12-pull-request-merge-queue-is-now-generally-available/).
- [About secret scanning](https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning),
  [Secret Protection changelog](https://github.blog/changelog/2025-03-04-introducing-github-secret-protection-and-github-code-security/),
  [GHAS billing](https://docs.github.com/en/billing/concepts/product-billing/github-advanced-security).
- [About Dependabot alerts](https://docs.github.com/en/code-security/dependabot/dependabot-alerts/about-dependabot-alerts).
- Trong repo: [ADR 0014](../../adr/0014-repo-visibility-and-github-plan.md) và các amendment;
  [rà soát kiến trúc S261](../2026-10-31-S261-architecture-review/README.md) (E1, BO-11);
  `infra/AA-CIS-Infra/.github/workflows/` (`migration-apply.yml`, `migration-sync.yml`, `terraform-apply.yml`,
  `db-schema-dump.yml`); `infra/AA-CIS-Infra/accounts/aa365/alarm_runbooks.tf`, `docs_reader.tf`;
  `apps/AA-CIS-App/.github/workflows/ci.yml` và `.github/scripts/schema_gate.py`.
- Dữ liệu đo và script (scratchpad phiên S261, không commit):
  `/tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/cad059ca-b2c4-41de-9344-dda6ca944497/scratchpad/gh/` và
  `/tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/cad059ca-b2c4-41de-9344-dda6ca944497/scratchpad/ghs/`.

**Chưa kiểm được:** org đã có payment method hoặc budget chưa (token thiếu scope `admin:org`; việc bị chặn ngày 22/10
cho thấy là chưa); API `environments/org` còn trả reviewer sau khi lật hay không; hành vi env secret trên private Free
(mâu thuẫn với docs). Tuần 24–30/10 là tuần dev rất dày, tuần thưa hơn sẽ thấp hơn, nhưng mức nền chỉ riêng cron đã
khoảng 1.000 phút/tháng.
