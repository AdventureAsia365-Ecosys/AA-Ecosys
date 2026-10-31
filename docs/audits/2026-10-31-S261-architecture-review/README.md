---
id: OPS-08-s261-architecture-review
title: "Rà soát kiến trúc, dự án và quy trình SDLC/ADLC theo 8 vai (S261)"
description: "Bản tư vấn cho tech lead: 8 vai chuyên môn và một người rà chuẩn SDLC/ADLC chấm cách tổ chức, làm và quản lý hệ sinh thái AA; lộ trình và các quyết định cần duyệt."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 90
related: [AA-1004, AA-642, AA-1002, AA-855]
---

# Rà soát kiến trúc, dự án và quy trình SDLC/ADLC theo 8 vai (S261, 31/10/2026)

> **Tech lead đã quyết (31/10/2026, sau khi bản này được viết):** giữ repo gốc và Infra public, không chi tiền GitHub
> (E1, N11, BO-11 không áp dụng); TL-7 chưa làm lúc này; TL-9 / F7 đã xong từ 25/10 (mật khẩu DataForSEO đã xoay ở
> S251, secrets register sửa 31/10); bằng chứng quota cho case AWS chờ vài ngày.


Bản tư vấn viết cho tech lead (tiếng Việt, theo luật `docs/audits`). Câu hỏi gốc: với các vai PM, Data Engineer,
AI Engineer (và các vai kiến trúc, vận hành, bảo mật), cách chúng ta tổ chức, thực hiện, quản lý dự án, dữ liệu và
hệ sinh thái còn gì cần tư vấn thêm theo SDLC, ADLC hay các chuẩn.

Cách làm: 9 lượt rà độc lập, chỉ đọc (repo gốc, 5 repo con, `gh`, catalog DB đã dump), không ghi AWS/DB/Linear.
Các vai: CTO, AWS Solutions Architect Professional (viết tắt **SA**), AWS DevOps Engineer Professional (**DevOps**),
AWS Generative AI Developer Professional (**GenAI**), AWS Security Specialty (**Sec**), Project Manager (**PM**),
Data Engineer (**DE**), AI Engineer (**AIE**), và người rà chuẩn SDLC/ADLC (**STD**). Phát hiện trùng nhau giữa các
vai đã được gom lại; cột "Vai nêu" cho biết ai thấy. Đọc cùng:

- `../2026-10-30-S260-go-live-readiness/README.md` (scorecard go-live), `../2026-10-30-S260-legal-readiness/README.md`
- `../2026-10-30-S260-inprogress-triage/README.md` (31 issue In Progress), `../2026-10-17-S241-sdlc-review/README.md`
- `../2026-10-31-S261-aws-bedrock-org-access/README.md`, `../2026-10-31-S261-llm-capacity-plan/README.md`
- `../../ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md`

**Rà phản biện (31/10, cùng ngày):** một lượt độc lập đã mở lại bằng chứng của mọi phát hiện Cao/Trung bình, đối chiếu
các dữ kiện luật và nhà cung cấp với văn bản gốc, hạ mức các mục chỉ ảnh hưởng Dev, chuyển phần kiểu doanh nghiệp lớn
sang "khi có trigger" và chia lại quyết định tech lead / business owner. Danh sách thay đổi ở mục 9.

> **Bản public (repo gốc):** chi tiết F1/F2 (chuỗi leo quyền IAM) đã rút khỏi trang này. Chi tiết trong Linear AA-873; đã vá ở Infra #541.

Quy ước: **Công sức** S ≤ 1 ngày, M 2–5 ngày, L > 1 tuần. **Thời điểm**: "Ngay" = trong 2 tuần tới; "Trước go-live"
= trước khi bắt đầu build prod hoặc trước ngày go-live; "Trigger: …" = khi sự kiện có tên xảy ra. Phát hiện ghi
PLAUSIBLE là kiểm thô, chưa chắc số chính xác.

## 1. Tóm tắt điều hành

1. **Tình trạng chung: 3,2/5.** Kỹ thuật và tài liệu ở mức 3,5 (hiếm thấy ở đội 1–3 người); định hướng sản phẩm và
   quản lý dự án ở mức 2–3. Dev chạy ổn, chưa có prod, 0 người dùng thật, toàn bộ LLM chat/judge đứng từ 29/10.
2. **Mạnh 1:** quyết định truy được (26 ADR, data standards, CONTEXT.md mỗi repo, schema reference sinh tự động) và
   Done phải có bằng chứng live.
3. **Mạnh 2:** đường giao hàng tốt: merge queue, migration expand tự áp (ADR 0017), plan guard + drift đêm, 2 lần
   diễn tập PITR (~22 phút), lead time CIS trung vị 10 phút.
4. **Mạnh 3:** quản trị chi phí và dữ liệu có thật: sổ `shared.llm_call_log`, budget theo app, owner role NOLOGIN,
   RLS + probe cô lập, gateway LLM điều khiển bằng dữ liệu.
5. **Rủi ro 1:** một đường cung cấp LLM duy nhất, đã đứng; judge chưa hiệu chuẩn nên chưa có cổng chất lượng thật.
6. **Rủi ro 2:** không có ngày go-live, khách trả tiền đầu tiên, giá; phạm vi 4 app + CRM "hoàn chỉnh", không giới
   hạn WIP (31 In Progress, số issue đóng mỗi phiên tụt từ ~15–20 xuống 0–3).
7. **Rủi ro 3:** bus factor = 1; **Rủi ro 4:** chuỗi leo quyền IAM (chi tiết trong Linear AA-873; đã vá ở Infra #541) và agent chạy bằng role admin của người.
8. **Rủi ro 5:** đường lên prod chưa tập: ADR 0018 còn Proposed và mâu thuẫn standards, chưa có baseline schema,
   chưa có seed nội dung, mọi bản sao catalog + tfstate chỉ nằm trong acc2 (ở org của đại lý).
9. **Làm trước tiên:** (a) mở đường LLM thứ hai (API Anthropic trực tiếp, trần chi tiêu) + canary hằng ngày;
   (b) một trang chiến lược sản phẩm + cửa sổ go-live + WIP ≤ 8 + đóng băng CRM W6–W8; (c) cắt chuỗi leo quyền,
   xoay mật khẩu DataForSEO lộ trong lịch sử repo public;
10. (d) chấp nhận ADR 0018, sao lưu catalog + tfstate ra ngoài acc2, thêm S3 gateway endpoint; (e) bộ nhãn người 40
    mục + luật thống kê cho judge trước mọi lượt eval trả tiền.

## 2. Bảng điểm theo vai

| Vai | Điểm (1–5) | Nhận xét một câu |
|---|---|---|
| CTO (chiến lược, tổ chức) | 2,5 | Thực thi và tài liệu ~3,5 nhưng định hướng ~2: không ngày go-live, không giá, không khách đầu tiên, nên backlog kỹ thuật dẫn đường; 4 app dựa vào một người và một đường LLM. |
| AWS Solutions Architect | 3,5 | Dev quản trị tốt hơn mức thường của đội 2–3 người; prod phụ thuộc 4 việc chưa làm: dời account, Terraform tái dùng được, egress/backup không dồn vào acc2, DR đã thử. |
| AWS DevOps | 3,5 | Giao hàng mạnh (merge queue, deploy guard hẹp, expand auto-apply, lead time 10′); vận hành chưa theo kịp: cảnh báo chỉ email, 12/17 runbook chưa thử, DORA chưa có nguồn, chuyển private tháng 11 sẽ tắt ngầm vài cổng. |
| AWS GenAI Developer | 3,5 | Gateway, sổ chi phí, data scope ở mức 4; một đường nhà cung cấp đã đứng và cổng phát hành chưa từng qua hiệu chuẩn nên thay prompt/model chưa được chặn bằng bằng chứng. |
| AWS Security | 3,5 | Kiểm soát có văn bản và bằng chứng; rủi ro còn lại là vài quyền quá rộng nối thành chuỗi, cộng hai lựa chọn mức prod còn mở (MFA nhân viên, chính sách vendor_direct). |
| Project Manager | 3 | DoD rất chặt nhưng chưa quản lý bằng số: không WIP limit, milestone đo bằng số phiên, không risk register, trạng thái rải 6–8 nơi. |
| Data Engineer | 3,5 | Nền dữ liệu được quản trị tốt (standards, owner role, schema reference, restore drill, connection budget trong CI); thiếu đường Dev→prod (baseline, seed) và các kiểm tra đêm chỉ báo, không chặn, nên đã trượt lại. |
| AI Engineer | 3 | Thiết kế eval và guardrail mạnh nhưng chưa chứng minh được chất lượng: nhãn chuẩn là LLM chấm LLM, chưa judge nào hiệu chuẩn, mọi sinh nội dung đang dừng. |
| Rà chuẩn SDLC/ADLC | 3 | Cách làm việc được định nghĩa rõ; bước tiếp là giữ hồ sơ đúng và kiểm được: baseline bảo mật cũ, review PR rủi ro không luôn có vết, DORA chưa có nguồn, eval chưa là cổng, nghĩa vụ PDPL chưa vào quy trình sự cố. |
| **Trung bình** | **3,2** | |

## 3. Phát hiện theo lĩnh vực

Mỗi phát hiện: mức (Cao / Trung bình / Thấp), bằng chứng, đề xuất, công sức, thời điểm, vai nêu.

### 3.1 Chiến lược, tổ chức và quản lý dự án

**A1. Không có ngày go-live, khách trả tiền đầu tiên, mô hình giá: ưu tiên đến từ backlog kỹ thuật — Cao**
- Bằng chứng: go-live readiness §7 "No go-live date: the 3-4 week build cannot start"; milestone M5 "Tenant trả tiền /
  prod" 0/3 (`docs/backlog/tracker/plan.json`); CRM spec §11 mục 8 còn mở giá cho đại lý
  (`docs/research/partner-crm-spec.md`); `docs/product/` chỉ có PRD CRM; thuế, % cọc, biên B2B chờ từ S247
  (`docs/backlog/README.md` §2).
- Đề xuất: một trang chiến lược sản phẩm do business owner quyết, tech lead soạn: beachhead (app nào kiếm tiền đầu,
  từ ai), giả thuyết doanh thu và giá, cửa sổ go-live, 3 mục tiêu đo được. Đề xuất mặc định: bán trực tiếp của AA
  trước (TripPlanner + Booking, AA là khách số 0), Content studio cho một đại lý design-partner sau, cửa sổ Q1/2027.
  Sau đó xếp backlog chỉ theo câu hỏi "có nằm trên đường tới lần ra mắt đó không".
- Công sức S · Ngay · Vai: CTO, PM.

**A2. Phạm vi quá rộng và không giới hạn WIP — Cao**
- Bằng chứng: 58 issue trên master plan (23 CRM, 18 CIS core, 10 data); CRM W5–W8 (WhatsApp/SMS, campaign, offline
  PWA, AI gateway) theo hướng "thiết kế sản phẩm hoàn chỉnh, không MVP"; 63 báo cáo (AA-1003, XL); 83 workflow GitHub
  trên 6 repo; 31 In Progress cuối S260; issue đóng mỗi phiên S245–S249 là 19/8/20/15/14, S253–S260 là
  5/2/2/7/3/1/2/0 (`plan.json` log); mỗi phiên agent tự chọn 20 việc "coi như duyệt" (log S258–S260, luật do tech
  lead đặt ở S260). Lưu ý khi đọc số đóng: từ S245 mỗi issue to hơn (luật quota Linear "1 issue = 1 lát giao được"),
  và từ 29/10 mọi việc cần LLM bị chặn, nên số tụt không chỉ do WIP. Dấu hiệu WIP vẫn đứng: 31 In Progress.
- Đề xuất: WIP ≤ 8 In Progress toàn hệ, ≤ 3 mỗi lane, ≤ 2 issue L/XL cùng lúc; issue XL phải tách trước khi vào
  In Progress; bị chặn thì về Todo kèm trigger ngay trong phiên. Bỏ "20 việc mỗi phiên", thay bằng "xong việc dở rồi
  mới lấy việc mới". Đóng băng CRM W6–W8 (AA-958…AA-971) tới khi có đại lý ký thư ý định/pilot; giữ báo cáo ở R0–R4.
  Đo tỷ lệ năng lực dành cho beachhead, mục tiêu ≥ 60%. Ghi luật vào `skill/aa-session` bước 3; thêm "closed/phiên"
  và "In Progress cuối phiên" vào state-snapshot.
- Công sức S · Ngay (áp từ S262) · Vai: CTO, PM, STD; AIE (đóng băng tính năng eval), DE (bảng và báo cáo đi trước
  nhu cầu), DevOps (đóng băng workflow mới).

**A3. Bus factor = 1 — Cao**
- Bằng chứng: 14 ngày commit chỉ có một danh tính người chính, còn lại là bot (`git log`); root MFA, management
  account, case AWS Support, chủ Vercel/GitHub, break-glass TOTP đều ở tech lead (`docs/backlog/README.md` §2); S260
  đổi tài khoản Claude giữa phiên vì chạm giới hạn 5 giờ; không tài liệu nào nêu người kế nhiệm.
- Đề xuất: (a) Ngay: business owner (hoặc người được chỉ định) làm người giữ quyền thứ hai trên GitHub org, AWS
  management account (admin Identity Center), nhà đăng ký tên miền, Vercel, Google Workspace, mỗi tài khoản bắt 2FA
  bằng passkey/app (không SMS); giữ bản break-glass niêm phong và một trang in "giữ hệ thống chạy". Người giữ quyền
  thứ hai chỉ dùng khi tech lead vắng, không vận hành hằng ngày. (b) Trước go-live: thuê một kỹ sư thứ hai bán thời gian; diễn tập
  người đó deploy và rollback một app chỉ bằng `docs/onboarding.md` + runbook, không dùng memory của agent.
  (c) Giữ được 2 nhà cung cấp AI coding (Claude Code, Kiro) và tính phí seat vào ngân sách.
- Công sức M · (a) Ngay, (b) Trước go-live · Vai: CTO, DevOps, PM.

**A4. Milestone đo bằng số phiên, không risk register, không dự báo — Cao**
- Bằng chứng: M1 "S244–S248" còn active ở S260; M2a "S247–S251" mới 3/7 (`plan.json:17`, `:93`); không có risk
  register cấp chương trình (chỉ có một bảng rủi ro cho riêng phương án A trong
  `../2026-10-29-S257-llm-access-options/migration-assessment.md:304`); `plan.json` có size S/M/L/XL nhưng không ngày bắt đầu/kết
  thúc, không cycle time.
- Đề xuất: mỗi milestone thêm `baseline_date`, `forecast_date`, `rag`; forecast tính từ throughput thật (issue Done mỗi
  tuần, từ `docs/linear-export`), dùng trung vị và p85 cycle time theo size, không story point. Thêm `risks[]` 10–15
  dòng vào `plan.json` (xác suất, tác động, owner role, biện pháp, trigger, ngày rà). Dòng nên có ngay: một nhà cung cấp
  LLM; bus factor; quota Linear; hạn AA-820 ngày 11/11; giới hạn usage của agent; chưa có ngày go-live.
- Công sức S (milestone, risk) + M (forecast) · Ngay; forecast trước khi business owner chốt ngày · Vai: PM.

**A5. Quyết định của business owner là nút thắt — Trung bình**
- Bằng chứng: legal readiness 12/12 chủ đề mở, 0/8 DPA ký, điều khoản AI hạn 11/11; thuế/cọc/biên chờ từ S247;
  khoảng 19 mục "Waiting" trong backlog §2 không có tuổi và hạn; báo cáo tuần PR-20 kỳ 3 soạn từ S253 chưa đăng.
- Đề xuất: một khung quyết định 30 phút mỗi tuần, tối đa 5 quyết định trên một trang (đã có mẫu trang quyết định
  bấm duyệt), mỗi quyết định có mặc định nếu 7 ngày không trả lời; AA-820 đi đầu. Thêm cột "mở từ" và "hạn" cho
  mục chờ; mục quá 14 ngày thì làm, giao lại hoặc xoá kèm lý do. Gom bước tay chỉ tech lead làm được (MFA, browser,
  PAT) vào một cửa sổ cố định mỗi tuần. Báo cáo tuần một trang cố định: milestone RAG + baseline/forecast, việc xong
  theo tính năng người dùng thấy, top 3 rủi ro, quyết định cần, chi phí tuần so với ngân sách. Business owner (hoặc
  người được chỉ định) giữ vai product owner cho nghiệm thu UAT và giá.
- Công sức S · Ngay (khung đầu tiên trước 11/11; báo cáo từ tuần 02/11) · Vai: CTO, PM.

**A6. Trạng thái nằm ở 6–8 nơi và đã lệch — Trung bình**
- Bằng chứng: tracker 21 In Progress, Linear 31 (triage S260); `docs/backlog/README.md` 565 dòng, phần lớn là lịch sử
  "Settled in S2xx"; nguồn trạng thái gồm Linear, backlog README, `plan.json`, artifact tracker, Notion memory,
  `docs/sessions` (88 log), checklist `.tmp-session`, state-snapshot, Jira; nghi thức đóng phiên 9 bước ghi ra ~10 nơi.
- Đề xuất: Linear là nguồn duy nhất cho trạng thái issue; `plan.json` sinh từ Linear bằng script (chỉ milestone, risk,
  slot sửa tay); backlog README rút về §1–§3 (~150 dòng), "Settled in Sxxx" chuyển sang `docs/backlog/decisions.md`;
  Notion memory còn 10 dòng con trỏ. Mục tiêu: đóng phiên dưới 20 phút, 3 thao tác tay (duyệt Jira, quyết định,
  merge root PR). Nhẹ đi cũng giúp bàn giao cho kỹ sư thứ hai.
- Công sức M · Ngay (S261–S264) · Vai: CTO, PM.

**A7. Done-when bị đổi giữa chừng, "Done-with-scope" chưa thành luật — Trung bình**
- Bằng chứng: AA-1002 bị nâng mức Done sau khi 4 dòng gốc đã đạt (triage §3); 9/31 issue phải chia lại; issue XL
  dạng ô dù (AA-994, AA-1003) trái luật 1 issue ≈ 1 PR (`skill/aa-linear-issue/SKILL.md:32`).
- Đề xuất: ghi vào `skill/aa-ship`: Done-when đóng băng khi sang In Progress, phạm vi mới thì mở issue mới;
  Done-with-scope hợp lệ khi phần còn lại đã có issue đích được link.
- Công sức S · Ngay · Vai: PM.

**A8. Tổng chi phí sở hữu (TCO) không hiện ra — Trung bình**
- Bằng chứng: `docs/ops/finops.md` và `docs/ops/cost/README.md` chỉ có AWS và LLM; seat AI coding, Vercel, Linear,
  GitHub, DataForSEO, Geoapify, Jev, Google Workspace không ở một sổ; prod ước 280–550 USD/tháng cộng Dev ~260
  (`docs/engineering-handbook.md` §8.4); tín dụng acc3 249,94 USD hết hạn 31/12.
- Đề xuất: thêm bảng TCO mọi nhà cung cấp và seat vào báo cáo chi phí tháng đầu tiên (từ 03/11); một con số "burn
  tháng" và đường hoà vốn (bao nhiêu booking hoặc tenant trả cho nền tảng). Duyệt ngân sách prod cùng lúc với ngày
  go-live.
- Công sức S · Ngay (báo cáo tháng 10) · Vai: CTO.

**A9. Chưa có luật build-vs-buy — Thấp**
- Bằng chứng: tự xây hoặc định xây ký số KMS (AA-955), engine 63 báo cáo, inbox email CRM, campaign, WhatsApp/SMS,
  offline PWA, pipeline video UAT + TTS; điểm khác biệt thật là pipeline nội dung, kho AA, proposal tương tác.
- Đề xuất: một đoạn trong engineering handbook: chỉ tự xây cái dùng nội dung/kho của AA hoặc là lý do khách trả tiền;
  phần còn lại tích hợp hoặc mua sau một adapter mỏng. Áp dụng khi mở lại CRM W6–W8; không viết lại cái đã ship.
- Công sức S · Ngay · Vai: CTO.

### 3.2 LLM và AI (nền tảng, chất lượng, quản trị)

**B1. Một đường cung cấp LLM duy nhất, đã đứng từ 29/10 — Cao**
- Bằng chứng: ADR 0001a (28/10) bỏ fallback chéo account; ngày 29/10 acc3 trả Error 002 mọi model (postmortem §1, §6
  "a single supplier path"); OpenAI trực tiếp 429 (hết credit), `anthropic-direct` chưa có secret; 27/37 stage và
  fallback của chúng cùng nằm trên acc3 (`docs/generated/llm-routes.md`); chặn AA-919, AA-790, AA-1000, AA-900 và phần
  LLM của AA-920/921/922; case AWS dự kiến ~04–06/11.
- Bối cảnh đã có: business owner đang chọn giữa 5 phương án tech lead gửi sau S257 (backlog §2 "LLM access option");
  khoá API Anthropic cũ đã thu hồi (backlog §2 "LLM path"). Mục này không mở câu hỏi mới mà đề xuất câu trả lời cho
  câu hỏi đang chờ.
- Đề xuất: cấp tiền một đường thứ hai không phụ thuộc payer của account AWS nào: API Anthropic trực tiếp, nạp trước,
  trần chi tiêu tự đặt ở cấp tổ chức và workspace (Console có; không đặt được trên workspace mặc định) cộng budget theo
  connection (S10). Theo trang rate limits của Anthropic: chạm trần tự đặt thì API trả HTTP 400 `invalid_request_error`
  ("You have reached your specified ... usage limits"), chạm trần của tier thì 429 không có `retry-after`; gateway
  phải coi cả hai là "đường hết tiền" (không retry, chuyển đường), không phải lỗi request. Tổ chức mới có thể bắt đầu ở
  tier Evaluation với hạn mức thấp hơn, nên mở sớm và chạy ít lưu lượng đều đặn. Adapter đã có (AA-1002 S2), nên phần
  code chủ yếu là cấu hình + xử lý hai mã lỗi trên (~0,5–1 ngày). Phạm vi `vendor_direct` chỉ cho stage A-series nội bộ
  và judge; T-series và `tp_*` giữ `aws_only` tới khi điều khoản tenant ghi "qua AWS hoặc trực tiếp từ nhà cung cấp
  model" và DPA đã đọc. acc3 vẫn là đường chính khi case đóng. Viết một trang "chế độ suy giảm" (stage nào chạy tiếp,
  stage nào dừng, nội dung nào giữ lại). Sửa ADR 0001a: "không fallback chéo ACCOUNT" + "một fallback chéo NHÀ CUNG
  CẤP". Trigger dự phòng: nếu tới 06/11 acc3 chưa mở thì chọn phương án trong 2 ngày làm việc.
- Công sức S · Ngay; hai đường độc lập là điều kiện go-live · Vai: CTO, GenAI, AIE, PM, STD.

**B2. Cổng eval chưa hoạt động: nhãn chuẩn là LLM chấm LLM, judge chưa hiệu chuẩn, mẫu quá nhỏ — Cao**
- Bằng chứng: quyết định S245 D7 = "b" (panel agent gán nhãn thay người), trong khi chính thiết kế gọi nhãn của tech
  lead là "nguồn duy nhất không do LLM tạo" (`../2026-10-20-S245-quality-system/decisions.json`); bước verifier đủ
  nguồn `eval_verify` (design §5.4) không có trong code; mọi ngưỡng trong
  `apps/AA-CIS-App/services/quality/thresholds.yaml` là `calibrated: false` (20/20 dòng); kappa tốt nhất 0,562 (gpt-5.6-luna, so
  judge S257) trên **13 cặp**, dưới thanh 0,6 và chính script ghi `counts=False`
  (`../2026-10-29-S257-aa919-judge-compare/judge-compare-s257.txt:215`), riêng t9_social 0,235 trên 13 cặp (S256), a1 lệch 6 pass/44 fail; hạn "chọn một judge
  trước 31/10" đã qua; AA-790 r10: delta +0,688 bằng đúng nhiễu A/A 0,688, cùng bài học lặp 3 lần (AA-346, AA-748,
  AA-790).
- Đề xuất, theo thứ tự: (1) bộ nhãn người 40 mục phân tầng (~15 A1, 10 T9 blog, 10 social, 5 T2), gán mù bằng rubric
  hiện có (tech lead ~2 giờ, hoặc thuê biên tập viên du lịch), đo panel agent so với người; kappa ≥ 0,7 thì giữ panel
  agent kèm con số hợp lệ, dưới thì sửa rubric trước. Verifier dùng họ model khác judge nó kiểm. (2) Luật thống kê:
  judge chỉ "tính" khi ≥ 30 cặp và ≥ 8 mỗi lớp; báo kappa kèm bootstrap CI, PABAK hoặc Gwet's AC1 cho tầng lệch; dưới
  ngưỡng thì chỉ báo cáo. (3) Thử rubric dạng nhị phân theo tiêu chí và so cặp đổi vị trí trên 134 mục sẵn có.
  (4) Mỗi eval có 2 lượt đối chứng để đo nhiễu; chỉ nhận hiệu ứng lớn hơn nhiễu. (5) Khối "đăng ký trước" 5 dòng
  trong eval runbook, chỉ cho lượt eval trả tiền (giả thuyết, mẫu, SD nhiễu, n, thanh); hiệu ứng nhỏ nhất đo được
  lớn hơn thanh thì không chạy. Không thêm vào PR template chung.
  (6) Viết sẵn luật chấp nhận dự phòng nếu kappa vẫn < 0,6 (ví dụ recall lỗi ≥ 0,8, precision ≥ 0,7, kiểm tay 10 mục);
  không hạ thanh 0,6. Chi phí mô hình ~1–5 USD mỗi vòng.
- Công sức M · Nhãn người: Ngay ($0, tận dụng lúc LLM đứng); hiệu chuẩn: phiên đầu có LLM, trước S11 và trước tenant
  trả tiền · Vai: GenAI, AIE, STD.

**B3. Đổi đường hoặc model là đổi model âm thầm; không có canary hằng ngày; không theo dõi vòng đời model — Cao/Trung bình**
- Bằng chứng: adapter Anthropic gửi effort mặc định với `request_defaults '{}'` khác request Converse (mig 306); 3 lần
  request thật khác ý định (S224 temperature, S251 AA-835 json_schema, AA-1002 S10 budget) (`skill/aa-lessons/lessons.md`);
  `llm_provider_health` chỉ cập nhật khi có lưu lượng thật, `test_connection` chỉ chạy từ trang admin; postmortem:
  TTD "Not measured: no alert"; `shared.llm_model_catalog` không có trường lifecycle/EOL; AWS: model ở trạng thái
  Legacy có thể mất quyền sau 15 ngày không dùng.
- Đề xuất: (a) canary đồng nhất trước mọi lần đổi route/ưu tiên/model: 20 mục mỗi judge cổng, 5 mỗi writer, so byte
  request (unit test), số verdict lật ≤ nhiễu, tuân thủ JSON schema; ghi run_id vào audit_log. (b) Job hằng ngày gọi
  `test_connection` cho mỗi connection × model chính (< 0,001 USD/lần, stage `adhoc_conn_test`), báo động sau 2 lần
  lỗi liên tiếp; metric filter $0 trên dòng log `llm_access_denied`. (c) Thêm `lifecycle_status`, `eol_date` vào
  catalog, điền hằng đêm từ trường `modelLifecycle` của ListFoundationModels, cảnh báo 90 ngày trước EOL trong
  digest. (Đã kiểm trang Bedrock model lifecycle: model Legacy "may lose access after 15 days of inactivity"; đợt
  dừng LLM hiện tại đã 2 ngày, nên model Legacy nào đang nằm trong route cần được biết trước ~13/11.)
- Công sức S (mỗi phần) · Ngay · Vai: GenAI, AIE, DevOps, STD.

**B4. Ba gateway LLM riêng: đường mới chỉ tới CIS — Trung bình**
- Bằng chứng: TripPlanner có bản fork 591 dòng `apps/AA-TripPlanner-Web/backend/shared/llm_gateway.py`
  (`SUPPORTED_ACCOUNTS=('acc3','acc2')`, mặc định cứng Sonnet 4.6); CRM có gateway riêng; plug-in không cần deploy chỉ
  đúng cho CIS tới S8.
- Đề xuất: làm S8 (vendor lõi `aa_llm` vào TP và CRM, một bộ contract test cho cả 3 repo) trước S7; giữ thứ tự CRM
  scrub → budget → `ai_enabled` sau giao diện Provider.
- Công sức L · Trước go-live của TripPlanner B2C hoặc AI của CRM · Vai: GenAI.

**B5. Phiên bản prompt và nguồn gốc không nằm trong sổ — Trung bình**
- Bằng chứng: 24–25/34 prompt chỉ ghi version "git", ~11 không có eval baseline
  (`apps/AA-CIS-App/docs/llm/prompt-register.md`); `shared.llm_call_log` không có cột `prompt_version`; DB tiêm lesson,
  brand rule, route vào prompt mà không qua PR.
- Đề xuất: `LLMClient.generate()` tính sha8 của system prompt cuối cùng (kể cả phần DB tiêm) + template id, ghi vào
  `llm_call_log`; kèm model id, route key, release_id. Prompt "none" có ít nhất một fixture Q0 hoặc ghi rõ rủi ro thấp.
- Công sức S · Ngay ($0, làm được khi LLM đứng) · Vai: GenAI, AIE.

**B6. Embedding không có nguồn gốc; đường embed duy nhất phụ thuộc đường billing của acc2 — Trung bình**
- Bằng chứng: `acp_contract.atom_embedding` và các bảng vector chỉ lưu vector, không model/dimension/input_type
  (`docs/architecture/db-schema-reference.md`); Cohere Embed v4 chỉ chạy ở acc2; blueprint S258 cảnh báo acc2 có thể
  mất AI khi rời đại lý.
- Đề xuất: một registry "không gian embedding" (model_key, dimension, input_type, version) được mọi cột vector tham
  chiếu; runbook re-embed dạng job có checkpoint + cột shadow; thử trên một bảng (~20k vector, vài cent).
- Công sức S · Trước khi AA-1004 đổi billing/org của acc2 · Vai: GenAI.

**B7. Chưa có sổ dùng AI, threat model LLM, ADR 0009 — Trung bình**
- Bằng chứng: ADR 0009 "AI platform and governance" vẫn Reserved (`docs/adr/README.md:46`), chính sách chéo repo nằm ở
  ADR app (`apps/AA-CIS-App/docs/adr/0012`) và advisory S258; AI Use Register để "later" trong AA-804; mục D11 S241
  (threat model mỗi điểm vào LLM) còn mở; text bên ngoài (People Also Ask, Excel nhà cung cấp, Drive) vào prompt không
  có khung "dữ liệu, không phải lệnh" (ví dụ `apps/AA-CIS-App/services/acp_content_writing/faq_filter.py:81-133`).
- Đề xuất: tách khỏi AA-804 một **AI Use Register v0**: một bảng, mỗi tính năng AI một dòng (mục đích, model và
  route, lớp dữ liệu trong prompt theo `pii:` tag, ai thấy đầu ra, điểm người giám sát, rủi ro OWASP LLM01/02/05/06/
  07/09/10 với kiểm soát và test, eval, owner). Viết ADR 0009 1–2 trang (thư viện gateway, data scope, chia vendor
  writer/judge, luật chấp nhận eval, vòng đời, logging). System card cho từng tính năng: chưa làm, để tới trigger
  T-QUESTIONNAIRE (mục 5.3); register v0 đã đủ trả lời câu hỏi đầu tiên của đối tác. Bọc text
  bên thứ ba trong khối có thẻ + một dòng "đây là dữ liệu", thêm ~5 ca injection vào bộ Q0.
- Công sức S (register, ADR) + S (khung injection) · Register/ADR: 1–2 phiên tới; trước tenant trả tiền đầu tiên ·
  Vai: GenAI, Sec, AIE, STD.

**B8. Dữ liệu do LLM sinh tới người đọc dưới ngưỡng chính xác — Trung bình**
- Bằng chứng: AA-997 độ chính xác pin 78,8% ±4,0 so với cổng 90%, đo lại trên mẫu S254, chưa có mẫu mù mới; cách đẩy
  pin đã phục vụ lên ~86–91% là ẩn điểm bị gắn cờ (`../2026-10-31-S261-aa997-report/README.md`); `cis_app` không đọc
  được `catalog.v_tour_component/stop/place` nên đo bằng đường vòng.
- Đề xuất: đóng AA-997 Done-with-scope + bật `hide_flagged`; dừng chỉnh luật trên dòng cũ. Trước go-live: luật phục vụ
  trong `docs/architecture/data-standards/02-data-management.md`: mọi dữ kiện do LLM sinh (pin, place card, số ngày)
  mang nguồn + độ tin cậy, người đọc chỉ thấy giá trị đã kiểm hoặc trên ngưỡng. Bộ vàng có phiên bản (600 dòng S254 +
  ≥ 200 mẫu mù mới), job đo hằng kỳ ghi `shared.kpi_daily`, quyền đọc qua view hợp đồng.
- Công sức M · Đóng: Ngay; job DQ + luật: Trước go-live · Vai: AIE, DE.

**B9. Máy móc eval/học đi trước việc dùng thật — Trung bình**
- Bằng chứng: writing memory ~30 module, quality system ~3,9k dòng, golden set 134 mục; chưa rule nào được duyệt qua
  release 0 (AA-920); các tầng Q0/Q2/R0/Q3, shadow, R2, canary, verifier mỗi thứ một issue; ~18 detector ở shadow
  không thể lên enforce trên Dev vì không có tín hiệu người duyệt thật.
- Đề xuất: đóng băng tính năng eval mới; chứng minh trọn một vòng trên T9 blog (nhãn người → judge hiệu chuẩn → một
  rule qua R2 → kích hoạt → hậu kiểm), rồi mới mở rộng A1/T2; gộp AA-919/920/921/922/923, AA-790, AA-1000 vào một
  track. Ghi vào taxonomy README: shadow→enforce chờ tín hiệu tenant đầu tiên; tới lúc đó đo recall bằng lỗi gieo sẵn.
- Công sức S · Ngay (quyết định kế hoạch) · Vai: AIE.

**B10. Batch S7 rủi ro cao, tiết kiệm ít ở khối lượng hiện tại — Thấp**
- Bằng chứng: S7 ước 4 ngày, rủi ro High; tiết kiệm ~25 USD mỗi lần viết lại 810 tour; đang xếp S261 #4.
- Đề xuất: hoãn; khi làm thì dùng Converse invocation type cho batch.
- Công sức L · Trigger: chi phí batch được > ~100 USD/tháng hoặc có lịch chạy lại toàn catalog · Vai: GenAI.

**B11. Cache prompt và parity chi phí chưa kiểm trên call thật — Thấp**
- Đề xuất: wave 3 tour đầu tiên sau khi có LLM: kiểm `cache_read_tokens > 0` cho writer và chi phí log khớp console/
  reconcile trong vài %; xoá `shared/llm_client/prompt_cache.py` nếu không còn import.
- Công sức S · Phiên LLM đầu tiên · Vai: GenAI.

### 3.3 Dữ liệu

**C1. Chưa có cách dựng schema prod từ repo — Cao**
- Bằng chứng: bản copy migration CIS ở Infra chỉ có file 215–317; lịch sử `acp_*` của dòng AA-ACP-Core "is in no repo"
  (`docs/architecture/data-standards/01-engineering.md:298-302`); replay đêm chỉ chạy một phần và lỗi ở tp-021
  (`db-schema-reference.md:11411-11430`); test replay toàn bộ migration gãy nhiều lần (130 lỗi CI S243, CIS #1190 S260).
- Đề xuất: mỗi owner một baseline: dump schema-only tại phiên bản migration đã tag, khôi phục vào instance nháp và có
  drift sạch so với Dev, đăng ký `<owner>-baseline` trong `schema_versions`. Bootstrap prod = roles → baseline →
  migration sau đó, đều qua DB Migrate. Replay CI bắt đầu từ baseline (bỏ phần lớn test giòn). Diễn tập ngay trên
  instance bỏ đi (dùng lại setup restore drill).
- Công sức M (~3–5 ngày, instance nháp vài cent) · Diễn tập: Ngay; đóng băng baseline: tuần 1 build prod · Vai: DE.

**C2. Seed nội dung Dev→prod mới có thiết kế — Cao**
- Bằng chứng: ADR 0012 quyết định 9 (seed có duyệt, idempotent, theo allow-list); mục 8 cổng go-live còn mở; đồ thị
  FK lớn (atom_embedding 175 MB, geo.tour_place 216 MB) kèm nợ chất lượng (B8).
- Đề xuất: seed là một job kind CIS điều khiển bằng allow-list bảng sinh từ PII tag (lỗi nếu bảng có cột `pii:`), thứ
  tự copy theo đồ thị FK từ dump, parity = số dòng mỗi bảng + `content_hash` của `catalog.v_tour`; loại rõ phần thí
  nghiệm (schema retired, shadow log, scratch của wave, ranking cũ). Tập vào instance nháp và ghi thời gian.
- Công sức M · Trước go-live (tuần 1–2 build), tập khi có baseline · Vai: DE.

**C3. Bản sao duy nhất của catalog và tfstate nằm trong acc2 (ở org đại lý) — Cao**
- Bằng chứng: catalog Dev là seed prod (ADR 0012 d9); PITR 7 ngày, snapshot tay, bucket tfstate đều ở acc2
  (`infra/AA-CIS-Infra/modules/rds/main.tf:157`, `accounts/aa365/versions.tf:31`); acc2 thuộc org đại lý và sắp dời
  org; acc3 mất Bedrock vài phút sau khi đổi org; RDS mã hoá bằng khoá AWS-managed (`modules/rds/main.tf:129`) nên
  không chia sẻ snapshot chéo account được.
- Đề xuất: hằng tuần, và ngay trước lần dời org của acc2: `pg_dump` các schema nội dung không PII (silver/gold/acp/
  catalog/geo, cùng allow-list với seed) qua DB Migrate run-script, gửi vào bucket có versioning + Object Lock
  GOVERNANCE ở một account AA kiểm soát (aa-ai hôm nay); copy luôn bucket tfstate. Tuỳ chọn: snapshot copy mã hoá lại
  bằng CMK chia sẻ cho account đó.
- Công sức S (1–5 USD/tháng) · Ngay, trước mọi lần dời org/Billing Transfer · Vai: SA.

**C4. Kiểm tra đêm chỉ báo cáo và đã trượt lại — Trung bình**
- Bằng chứng: drift "clean" khi đóng AA-853 (S251), nay "open" 4 mục + tp-021; RLS guard 1 vi phạm
  (`booking.b2b_partners` tắt RLS) và 18 mục allowlist cũ; 45 cột nghi PII chưa tag (`db-schema-reference.md:10992`,
  `:11324`, `:11338`, `:11415`).
- Đề xuất: "bánh cóc": job dump ghi một dòng sức khoẻ dữ liệu (drift mở, vi phạm RLS, PII chưa tag, allowlist cũ,
  orphan); số nào tăng thì chặn auto-merge PR bot và mở/cập nhật một issue. Dọn tồn đọng hôm nay trước (tp-021,
  `booking.b2b_partners`).
- Công sức S · Ngay · Vai: DE.

**C5. PII tag của `crm` chưa đủ trước CRM Go-real — Trung bình**
- Bằng chứng: chưa tag `crm.member_invitation.email_enc`, `crm.studio_invitation.email_enc`,
  `crm.member.cognito_iss/cognito_sub`, `crm.refund_request.decision_note`, `crm.message.attachment_notes`
  (`db-schema-reference.md:11252-11300`); RoPA và inventory xoá dữ liệu sinh từ tag; lint chỉ kiểm tên lớp, không kiểm
  thiếu tag.
- Đề xuất: tag hoặc allowlist cả 45 cột trong một migration crm; lint Infra `check_migration_files.py` báo lỗi khi cột
  mới của app mới có tên khớp token PII mà không có tag hoặc lý do.
- Công sức S · Trước AA-980 (CRM Go-real) · Vai: DE.

**C6. Retention phần lớn còn trên giấy — Trung bình**
- Bằng chứng: các kind retention CIS mặc định DRY RUN (`apps/AA-CIS-App/services/jobs/retention_job.py:129-143`);
  `shared.decision_log` 443,7 MB, 427k dòng (~30% DB) chưa có cửa sổ; ~20 dòng "proposed"; cửa sổ PII Booking/TP chờ L3.
- Đề xuất: một lượt duyệt theo DM-7.5: duyệt cả lô cửa sổ "proposed", `decision_log` 180 ngày + rollup ngày (như
  `llm_call_log`), chạy live lần đầu mỗi kind trên Dev để chứng minh 2x stop và archive-trước-xoá. Cửa sổ PII
  Booking/TP phải duyệt trước khách thật đầu tiên. Dung lượng (1,5 GB) không phải lý do để vội.
- Công sức S · Trước go-live · Vai: DE.

**C7. Agent thêm schema nhanh hơn tốc độ dùng — Trung bình**
- Bằng chứng: 355 bảng/view, 140 hàm, 1.000 index; ~10 commit migration/ngày ở Infra; 163/294 bảng ~0 dòng hoặc chưa
  analyze (crm 60/90, booking 42/59, shared 36/67); mỗi bảng kéo theo retention, PII tag, RLS, inventory xoá, chi phí
  replay.
- Đề xuất: luật cho agent: bảng ship cùng lát với người ghi và người đọc đầu tiên. Trước khi cắt baseline: rà bảng
  rỗng theo Dead Table Registry, cách ly bảng không có người ghi dự kiến, xoá sau 14 ngày (quy trình DRY RUN).
- Công sức S · Luật: Ngay; dọn: trước khi cắt baseline · Vai: DE.

**C8. Kiểm orphan mới phủ 1 khoá chéo app; recompute xoá-chèn lại nhân số lần ghi — Thấp**
- Bằng chứng: chỉ kiểm `booking.trip_case_legs → catalog.v_tour`; `acp_contract.atom_ranking` 13,5M insert / 13,4M
  delete trên ~97k dòng, `geo.tour_junction` 2,2M/2,0M.
- Đề xuất: thêm 3–4 định nghĩa khoá (CRM → catalog/Booking, Booking supply → `shared.supply_entity`, phiên TP →
  catalog); thêm WAL bytes và CPU credit vào rà năng lực tháng; đổi sang chỉ ghi dòng thay đổi khi một trigger C3 nổ.
- Công sức S · Orphan: trước go-live; recompute: khi có trigger · Vai: DE.

**C9. Chương trình báo cáo quá lớn cho giai đoạn chưa có doanh thu — Thấp**
- Bằng chứng: 63 báo cáo, 229 KPI (`docs/reports/catalog.yaml`, `kpis.yaml`), lộ trình ~107 ngày công; bản copy
  registry giữ bằng luật phiên chứ không phải CI.
- Đề xuất: dừng ở R0–R4 (bộ P0 đã live); báo cáo khác chỉ khi có người đọc có tên yêu cầu; đưa kiểm bản copy registry
  vào CI CIS (`report_registry.py check --copy`).
- Công sức S · Ngay · Vai: DE, CTO.

### 3.4 Hạ tầng AWS, account và DR

**D1. ADR 0018 còn Proposed trong khi standards vẫn bắt prod ở acc2 — Cao**
- Bằng chứng: `03-scaling.md:382` C7.2a "separate RDS instance in acc2 … no new account", `:384` C7.2c,
  `02-data-management.md:360` DM-9.6; ADR 0018 đặt prod ở aa-prod (`docs/adr/0018-lean-aws-account-model.md:69`);
  go-live readiness §7 coi đây là blocker; advisory S261 đã thiết kế quanh aa-prod.
- Đề xuất: chấp nhận ADR 0018 ngay ($0, đảo được trước khi có member), cùng root PR sửa C7.2a/c, DM-9.6, bảng account
  trong Infra CONTEXT.md, mục 3 go-live; thêm một đoạn về region (xem D7).
- Công sức S · Ngay · Vai: SA, DevOps, CTO.

**D2. Toàn bộ egress riêng đi qua một NAT instance t4g.nano ở một AZ, không VPC endpoint — Trung bình** (hạ từ Cao:
chỉ Dev, chưa người dùng; prod sẽ dùng NAT gateway managed nên đây không phải blocker go-live)
- Bằng chứng: `infra/AA-CIS-Infra/modules/vpc/main.tf:151-157` (một t4g.nano ở us-west-1a, mọi route table riêng trỏ
  vào); không có `aws_vpc_endpoint`; băng thông nền t4g.nano 0,032 Gbps; alarm chỉ email, không recover action
  (`accounts/aa365/observability_ecosys.tf:110-125`).
- Đề xuất: Ngay: S3 gateway endpoint (miễn phí, kéo traffic S3 và layer ECR khỏi NAT); thêm EC2 recover/reboot vào
  alarm status-check; theo dõi CPU credit và NetworkOut một tháng, chỉ lên t4g.micro/small khi chạm nền 32 Mbps.
  Prod: NAT gateway managed (một cái lúc đầu; AWS có chế độ Regional NAT Gateway từ 11/2025, một gateway tự trải qua
  các AZ có workload, đáng so giá lúc build prod), interface endpoint chỉ khi
  phí xử lý NAT vượt giá endpoint (~7–8 USD/AZ/endpoint/tháng).
- Công sức S · Ngay (Dev); NAT gateway lúc build prod · Vai: SA.

**D3. Đường build prod đi qua việc biến root Terraform 17k dòng thành thứ tái dùng được — Trung bình**
- Bằng chứng: `accounts/aa365` ~17.449 dòng, 466 resource cấp cao, ~151 chỗ cứng "dev", một state
  (`dev/terraform.tfstate`) trộn tài nguyên cấp account và mọi app; `modules/` chưa có `platform-env`; ADR 0012 d5 định
  refactor bằng moved block vì trước đây prod chung acc2.
- Đề xuất (hai vai khác ý về thời điểm, gộp lại): sau khi chấp nhận ADR 0018, tham số hoá root hiện có (biến
  environment/account/region, `-backend-config` mỗi account, `allowed_account_ids` từ biến, cờ `count/for_each` cho
  file chỉ Dev: agent_session, e2e_mailbox, docs_reader, satellite cost-explorer, CI bootstrap) bằng các PR nhỏ có
  plan Dev "no changes"; cách này tránh moved block cho 466 resource. **Không** tách state hay dựng root prod trước
  khi có ngày go-live. Tech lead chốt cách (D-quyết định ở §7).
- Công sức L (~1–2 tuần của 3–4 tuần build, dời sớm) · PR zero-change: Ngay sau ADR 0018; xong trước khi đặt ngày
  go-live · Vai: SA, DevOps.

**D4. Mục tiêu DR mất region (RTO ≤ 4 giờ, đang ở dạng "proposed") khó đạt với thiết kế hiện có và chưa thử — Trung bình**
- Bằng chứng: ADR 0012 d10, DM-9.6 (ghi rõ "proposed; confirmed in the L9 blueprint") đặt RPO ≤ 24 giờ, RTO ≤ 4 giờ qua copy AWS Backup sang us-west-2; Cognito pool
  (không backup chéo region native), ECR (chưa replicate), Secrets Manager (không replica), ACM, custom domain API GW,
  SES, zip Lambda đều gắn một region; diễn tập hiện có chỉ PITR cùng region (`docs/ops/drills/README.md`).
- Đề xuất: business owner ký mục tiêu thực tế (RPO 24 giờ, RTO 24–48 giờ = dựng lại từ IaC + bản copy DB chéo region)
  thay vì trả tiền warm standby. Bộ hỗ trợ rẻ: ECR cross-region replication, replica Secrets Manager cho vài secret
  quan trọng, export thuộc tính người dùng Cognito hằng đêm, biến region trong root, một buổi tabletop. RDS/S3/Backup
  của prod dùng CMK từ ngày đầu (~1 USD/khoá/tháng).
- Công sức M (5–20 USD/tháng) · Trước go-live · Vai: SA, Sec.

**D5. Đại lý và payer: hai account dưới hai đại lý, cả hai từng gây chặn LLM; Billing Transfer làm mất một phần kiểm soát chi phí — Trung bình**
- Bằng chứng: acc2 ở org TrueIDC, Bedrock LLM bị chặn; acc3 mất quyền khi hết bảo trợ eCloudvalley; Billing Transfer
  chỉ một payer mỗi org, sớm nhất 01/12/2026, chấp nhận trước 29/11 23:59 UTC; dưới Billing Transfer org chỉ thấy chi
  phí pro forma, mất Cost Anomaly Detection, không thấy số dư credit
  (`../2026-10-31-S261-aws-bedrock-org-access/README.md` §1, dòng 40); ADR 0018:88 đặt budget ở management account.
- Đề xuất: quyết trước ~20/11: hoặc Billing Transfer sang một đại lý với trả lời bằng văn bản cho câu 1, 2, 6a/6b, 8
  trong `reseller-questions.md`, hoặc chạy LLM ngoài org (API trực tiếp, B1) và chỉ dùng đại lý cho hạ tầng. Hợp đồng
  nào cũng có: chuyển credit, điều khoản thoát, không SCP/chặn Marketplace. Giữ budget + anomaly monitor trong từng
  account thành viên; tải CUR và hoá đơn trước khi chuyển. Không dời acc2 khỏi org hiện tại trước khi đường LLM thay
  thế đã chạy.
- Công sức M · Trước 29/11 nếu muốn bắt đầu 01/12 · Vai: CTO, SA, Sec.

**D6. Gói Support Basic không đáp ứng mục tiêu sự cố prod — Trung bình**
- Bằng chứng: case acc3 mở nhiều ngày ở Basic, trả lời dự kiến ~04–06/11; mục tiêu K-INC-TTR của chính postmortem
  dưới 1 ngày làm việc.
- Đề xuất: Business support trên aa-prod (và aa-ai nếu LLM prod đi qua đó) từ go-live; Dev giữ Basic. Kiểm giá hiện
  hành trên trang AWS Support (mức tối thiểu ~100 USD/tháng/account theo reviewer, cần xác nhận).
- Công sức S · Trigger: ngày go-live · Vai: SA.

**D7. Region prod thừa hưởng từ Dev, chưa quyết riêng — Thấp**
- Bằng chứng: ADR 0018:69 ghi "in us-west-1" không lý do; us-west-1 chỉ 2 AZ cho account này; theo AWS Price List
  RDS PostgreSQL db.t4g.medium Multi-AZ 0,171 USD/giờ ở us-west-1, 0,129 ở us-west-2; legal readiness dòng 7 đã chấp
  nhận lưu trữ ở Mỹ.
- Đề xuất: thêm đoạn region vào ADR 0018 trước khi chấp nhận. Mặc định: giữ us-west-1 (đồng nhất Dev, quota và lịch
  sử Bedrock, dòng pháp lý đã xong), trừ khi kế hoạch chi phí prod cho thấy chênh ~25% RDS là đáng kể. Account mới là
  thời điểm rẻ duy nhất để đổi region. DE nhắc: dời region DB sau go-live tốn 1–2 tuần.
- Công sức S · Trước khi chấp nhận ADR 0018 · Vai: SA, DE.

**D8. Giới hạn của RDS dùng chung là connection, không phải CPU; đặt LLM prod chung quota với wave Dev — Thấp/Trung bình**
- Bằng chứng: db.t4g.small max_connections 181, trần 75% = 135, budget C2.2 đang 120 (`db/connection_budget.json`);
  ADR 0018 §3 cho Bedrock prod đi qua aa-ai, chung quota với wave Dev trả tiền.
- Đề xuất: giữ trigger hiện tại; trong kế hoạch prod tính lại C2.2 cho t4g.medium Multi-AZ, RDS Proxy chỉ trước
  Lambda TripPlanner. Gateway có trần TPM và USD theo môi trường để wave Dev không làm đói prod; mọi thay đổi payer/org
  xong ít nhất 2 tuần trước go-live.
- Công sức S/M · Lúc build prod · Vai: SA, GenAI.

### 3.5 CI/CD, phát hành và vận hành

**E1. Chuyển repo gốc và Infra về private (tháng 11) sẽ tắt các cổng pipeline đang dựa vào — Cao**
- Bằng chứng: ADR 0017 d8: auto-apply cần ruleset và environment rule ở AA-CIS-Infra, GitHub Free chỉ cho ở repo
  public; ADR 0014 dòng 96–97, 121 (secret scanning dừng trên Free private; ~37 USD/tháng phút Actions); docs GitHub
  (đã kiểm 31/10): required reviewer và wait timer trên Free/Pro/Team chỉ cho repo public (repo private cần
  Enterprise), environment secret và deployment branch ở repo private cần Pro/Team; secret scanning ở repo private
  của org cần bật add-on **GitHub Secret Protection** trên Team (trả phí riêng, không nằm trong 4 USD/user); Infra đang public với `AA_CI_BOT_PRIVATE_KEY` là secret cấp repo; CTO đề xuất cho Infra private ngay vì nó
  mô tả toàn bộ bề mặt tấn công.
- Đề xuất: trước khi lật, viết checklist một trang "cái gì sẽ tắt" vào amendment ADR 0014 (ruleset, environment
  `dev-db-auto`, environment secret, deployment-branch rule, secret scanning). Chọn một: (a) GitHub Team ~4 USD/user/
  tháng (giữ ruleset, environment secret, deployment branch; required reviewer vẫn cần Enterprise); (b) ở Free, đặt
  `DB_AUTO_APPLY=false` và chấp nhận một click tay mỗi migration expand; hoặc thêm một self-hosted runner cho job nặng.
  Điều kiện OIDC trust trong IAM đã có (AA-866: role apply kiểm `environment:prod` + `ref:refs/heads/main`, không dựa
  `if:`); chỉ cần kiểm lại các role OIDC khác (`cicd_db_auto_apply.tf`, `docs_reader.tf`, `e2e_mailbox.tf`,
  `accounts/management/cicd.tf`) có cùng điều kiện `ref`. Gitleaks PR + full-history (ADR 0014 amendment 2) vẫn chạy
  khi private, nên không bắt buộc mua Secret Protection. Hệ quả cho F2: Chi tiết trong Linear AA-873; đã vá ở Infra #541. Thứ tự: checklist → quyết gói → Infra private (sớm) → repo gốc cuối tháng 11.
- Công sức S · Ngay (trước mọi lần lật public→private) · Vai: DevOps, CTO, Sec.

**E2. Cảnh báo chỉ tới một người qua email, không phân mức — Trung bình hôm nay, Cao trước go-live** (hạ vì Dev chưa
có người dùng; vẫn làm phần $0 ngay vì đợt dừng LLM 29/10 được phát hiện tình cờ)
- Bằng chứng: cả 100 dòng trong `docs/generated/alarms.md` gửi về một topic; email cả ALARM và OK; alarm TargetTracking
  AlarmLow "nằm ở ALARM bình thường"; Sentry free với 1 uptime monitor (chỉ CIS `/health`); Booking, CRM, portal, TP
  không có kiểm uptime ngoài; postmortem: TTD không đo.
- Đề xuất: hai SNS topic: `critical` (tỷ lệ 5xx, service unhealthy, connection DB, `llm_access_denied`, quy tắc bảo
  mật) và `info` (email OK, chi phí, autoscaling, chỉ vào digest). `critical` tới kênh điện thoại (AWS Chatbot vào
  Slack/Teams miễn phí, hoặc SNS SMS cho tech lead + một người dự phòng). Route 53 health check trên host API công
  khai (trang giá Route 53: 50 check cơ bản cho endpoint AWS cùng account là miễn phí; HTTPS hoặc so chuỗi là tính năng
  thêm ~1 USD/tính năng/tháng; endpoint ngoài AWS như Vercel 0,75 USD/check/tháng + ~2 USD/tính năng). Trước go-live: tuyến paging
  đã thử, 2 SLO mỗi API công khai (ADR 0012 d11.5).
- Công sức S · Ngay (tách topic, metric filter, health check); trước go-live (paging, SLO) · Vai: DevOps, STD.

**E3. Rollback chỉ chứng minh cho CIS; 12/17 runbook chưa thử — Trung bình**
- Bằng chứng: bảng runbook trong `docs/ops/README.md`: rollback-booking, rollback-vercel, rollback-tp-lambda,
  rollback-terraform, deploy-gate-override là "draft, UNTESTED"; `docs/ops/incident-response.md`: CRM API, CRM web,
  portal chưa có runbook rollback; Lambda TP deploy `--publish` không alias.
- Đề xuất: một runbook tham số "rollback ECS service về revision N" dùng cho CIS, Booking, crm-api, crm-web,
  crm-portal; một game day $0 trên Dev rollback Booking, một service CRM, một project Vercel, Lambda TP, ghi thời gian
  vào drill index; Lambda TP có alias `live` để rollback là đổi trỏ alias. Mọi runbook phải tập một lần trước go-live
  (DM-9.3).
- Công sức M · Ngay ($0); hết runbook trước go-live · Vai: DevOps.

**E4. Terraform apply bằng tay sau merge, không gate job-idle; hai chủ ghi task definition ECS — Trung bình**
- Bằng chứng: `terraform-apply.yml` plan lại khi dispatch, không so digest với plan của PR cho aa365; `skill/aa-ship`
  §2: "Apply không có guard job" và "main của Infra không được có thay đổi đã merge mà chưa apply" là luật tay; từ 15/10:
  60 apply, 5 lỗi; `modules/ecs/main.tf:716, 905` `ignore_changes = [desired_count, task_definition]` trong khi
  `deploy-dev.yml` copy revision ACTIVE mới nhất rồi đổi image, nên cần đối chiếu env tay sau apply.
- Đề xuất: Ngay: thêm job deploy-gate vào `terraform-apply.yml` khi plan chạm `aws_ecs_service`,
  `aws_ecs_task_definition`, `aws_lambda_function`; tự dispatch apply cho aa365 (Dev) khi push main và plan guard qua
  (giữ dispatch tay cho management, acc3, prod sau này); drift job so tên env của revision đang chạy với Terraform.
  Trước go-live: Terraform sở hữu toàn bộ template task def, CI chỉ thay image digest và lỗi nếu trường khác lệch.
- Công sức S (gate, auto-dispatch) + M (task def) · Ngay / Trước go-live · Vai: DevOps.

**E5. Đường promote lên prod đã thiết kế nhưng chưa có gì chạy thử trên Dev — Trung bình**
- Bằng chứng: ADR 0012 d6: environment GitHub tên `prod` vẫn đang apply Dev, đổi tên `dev` còn chờ; d7: deploy bằng
  digest; ops README "Prod": chưa có môi trường prod.
- Đề xuất: đổi tên `prod`→`dev` theo 4 bước của d6; một workflow `deploy-by-digest` triển khai lại một digest đã build
  lên Dev, đồng thời là công cụ rollback chuẩn, để đường promote prod chạy trên Dev mỗi tuần. Thêm
  `actions/attest-build-provenance` vào job build ECR (repo app đang public; nếu repo nào về private thì kiểm gói
  GitHub trước, vì tính năng này ở repo private phụ thuộc gói), SLSA Build L2; Deploy Prod chạy
  `gh attestation verify` trước khi deploy.
- Công sức M · Ngay (rename, deploy-by-digest); provenance trước khi viết Deploy Prod · Vai: DevOps, STD.

**E6. Action dùng tag thay vì SHA trong workflow có quyền AWS; CIS không có Dependabot cho actions — Thấp/Trung bình**
- Bằng chứng: AA-CIS-Infra 99 `uses:` theo tag, 9 theo SHA (`aws-actions/configure-aws-credentials@v6`,
  `hashicorp/setup-terraform@v4`, `actions/checkout@v7`…); app repo dùng `aquasecurity/trivy-action@v0.36.0`;
  `apps/AA-CIS-App/.github/dependabot.yml` chỉ npm và pip; tiền lệ tj-actions (CVE-2025-30066).
- Đề xuất: pin SHA đầy đủ (kèm comment version) trong mọi workflow xin `id-token: write` hoặc đọc khoá App
  (terraform-apply, db-migrate, migration-apply/sync, deploy-dev*, release-please); thêm `github-actions` vào Dependabot
  của CIS. Workflow lint chỉ đọc giữ nguyên.
- Công sức S (agent làm một PR mỗi repo) · Infra: Ngay; app repo trước go-live · Vai: DevOps, Sec, STD.

**E7. DORA đã định nghĩa nhưng chưa đo — Thấp/Trung bình**
- Bằng chứng: `docs/reports/kpis.yaml` K-DORA-DF/LT/CFR/MTTR đều `sources: []`; dữ liệu thô có sẵn: CIS Deploy Dev 100
  lượt 27–31/10 (86 thành công / 8 lỗi / 6 huỷ), Booking 82/3, Partner 66/6 từ 01/10, Infra terraform-apply 55/5,
  migration-apply 33/4 từ 15/10 (`gh run list`).
- Đề xuất: script chỉ đọc qua `gh` API: DF = deploy thành công/app/tuần; LT = merge → deploy chứa SHA; CFR = (deploy
  lỗi + post-deploy-verify lỗi + revert + rollback circuit-breaker) / deploy; MTTR từ bảng postmortem; tách theo tác
  giả agent/người, thêm tỷ lệ làm lại (PR `fix:` cùng path trong 24 giờ). Rule EventBridge cho
  `SERVICE_DEPLOYMENT_FAILED`. Báo dạng xu hướng, không so dải "elite". Kèm: tech lead đọc mẫu 3 PR đã merge/tuần
  thuộc tầng rủi ro (auth, migration, IAM) và ghi lại kết quả.
- Công sức S · Ngay (báo cáo tháng đầu tiên, đầu tháng 11) · Vai: DevOps, STD, CTO.

**E8. Độ phức tạp pipeline vượt số người vận hành được — Trung bình**
- Bằng chứng: AA-CIS-Infra 26 workflow, ~13 lịch (probe đêm, drift, dump, freshness, liveness, copy guard,
  migration-sync 10 phút/lần, migration-apply mỗi giờ), 2 GitHub App; cron GitHub là best effort (29/10 chỉ chạy một
  lần trong ~6 giờ); quy trình nằm chủ yếu trong skill của agent.
- Đề xuất: đóng băng gate/workflow mới trừ khi sự cố hoặc build prod cần; một trang sơ đồ workflow nào kích workflow
  nào, email lỗi của từng cái; bỏ workflow lịch mà tín hiệu đã có trong digest; "bài kiểm kỹ sư thứ hai" (gắn A3).
- Công sức M · Ngay (đóng băng, sơ đồ) · Vai: DevOps.

### 3.6 Bảo mật, quyền riêng tư và kiểm soát agent

**F1. Chuỗi leo quyền IAM qua quyền đọc secret của runtime CIS — Cao (đã vá)**
- Chi tiết trong Linear AA-873; đã vá ở Infra #541.

**F2. Quyền secret của apply role Terraform và bảo vệ environment Infra — Cao (đã vá, phần còn lại là TL-7)**
- Chi tiết trong Linear AA-873; đã vá ở Infra #541.

**F3. Agent chạy bằng role admin MFA của người trong lúc đọc dữ liệu không tin cậy — Trung bình trên Dev, Cao trước aa-prod**
(hạ từ Cao: đây là mở lại quyết định có chủ ý D-15 trong `docs/security/baseline.md:58`, đã có kiểm soát bù: hook
subagent, deny đọc `~/.aws`, deletion protection + PITR trên RDS; nhưng bản sao catalog duy nhất nằm trong acc2, xem C3)
- Bằng chứng: header `agent_session.tf`: agent dùng phiên `aa365-admin` 8 giờ khi đọc file nhà cung cấp, Jira, web;
  role hẹp `aa-cis-dev-agent-session` đã có nhưng tuỳ chọn theo D-15 (`docs/security/baseline.md`); S255 agent bật
  GuardDuty khi chưa được duyệt; OWASP LLM06 Excessive Agency.
- Đề xuất (bản rẻ cho 1 người): Ngay trên Dev: profile `aa365-agent` là mặc định khi agent đọc đầu vào không tin cậy
  (file nhà cung cấp, web, Jira) và cho việc thường ngày mà role hẹp đã phủ (ECS exec, log, S3 scripts); bổ sung ngoại lệ NotResource cho
  secret E2E (access review F-12); `aa365-admin` chỉ dùng trong các "cửa sổ tắt auto-mode" đã gom sẵn; Terraform và DB
  tiếp tục qua CI. aa-prod: agent không có role người, chỉ read-only + CI.
- Công sức M · Ngay trên Dev (xét lại D-15); bắt buộc trước khi có aa-prod · Vai: Sec.

**F4. Nghĩa vụ PDPL chưa vào vận hành; site TripPlanner Dev mời index và có form nhận yêu cầu — Trung bình hôm nay, Cao trước dữ liệu thật đầu tiên**
- Bằng chứng nội bộ: `docs/ops/incident-response.md:57` chỉ ghi "business owner decides with the lawyer (PDPD notice
  duties)", không đồng hồ, không mẫu, không nơi nhận (đây là file duy nhất ngoài `docs/audits` còn dùng "PDPD");
  `docs/legal/readiness-packet.md:129` đã dẫn đúng Luật 91/2025/QH15 + Nghị định 356/2025/NĐ-CP;
  `apps/AA-TripPlanner-Web/frontend/app/robots.ts` cho phép `/` và có sitemap; trang privacy/terms còn "Draft".
- Văn bản gốc (đã đối chiếu 31/10, bản điện tử của Luật 91/2025/QH15 trên hethongphapluat.com; danh mục dữ liệu theo
  NĐ 356/2025 trên cổng PBGDPL Cần Thơ; **luật sư vẫn phải xác nhận** trước khi đưa vào quy trình chính thức):
  - Điều 23 khoản 1: **bên kiểm soát** (hoặc bên kiểm soát và xử lý) thông báo cho cơ quan chuyên trách **chậm nhất 72
    giờ** kể từ khi phát hiện, khi vi phạm có thể gây hại cho quốc phòng, an ninh, trật tự xã hội hoặc xâm phạm tính
    mạng, sức khoẻ, danh dự, nhân phẩm, tài sản của chủ thể; **bên xử lý** thông báo "kịp thời" cho bên kiểm soát.
    Áp vào hệ thống: Booking/TripPlanner (AA là bên kiểm soát) đi đồng hồ 72 giờ tới cơ quan; CRM (AA là bên xử lý cho
    đại lý) phải báo **đại lý** ngay, đại lý mới là bên báo cơ quan.
  - Điều 38 khoản 2: doanh nghiệp nhỏ/khởi nghiệp được chọn không làm **Điều 21, Điều 22 và khoản 2 Điều 33** (hồ sơ
    đánh giá tác động xử lý, cập nhật hồ sơ, lực lượng bảo vệ dữ liệu) trong 5 năm, trừ khi kinh doanh dịch vụ xử lý
    dữ liệu cá nhân, trực tiếp xử lý dữ liệu nhạy cảm hoặc xử lý dữ liệu của số lượng lớn chủ thể. Khoản 3: hộ kinh
    doanh và doanh nghiệp siêu nhỏ được miễn hẳn các điều đó với cùng ngoại lệ. **Miễn trừ không phủ Điều 23 (thông
    báo vi phạm) và không phủ Điều 20 (chuyển dữ liệu xuyên biên giới).**
  - Điều 20: lưu dữ liệu thu ở Việt Nam trên hệ thống ngoài lãnh thổ là chuyển xuyên biên giới; phải lập hồ sơ đánh giá
    tác động chuyển dữ liệu và nộp **trong 60 ngày từ ngày chuyển đầu tiên**. Hệ thống chạy ở AWS us-west-1 và Vercel
    `sfo1`, nên nghĩa vụ này bắt đầu từ dữ liệu khách thật đầu tiên, bất kể miễn trừ.
  - Ngoại lệ "dữ liệu nhạy cảm": bản trước dẫn giới tính và tình trạng hôn nhân trong `booking.customers`; theo NĐ 356
    hai mục này thuộc **dữ liệu cơ bản**, nên bằng chứng đó sai. Bằng chứng đúng: `crm.traveler_health.health_flags_enc`
    (`pii:health`, `docs/legal/register.md:182`; sức khoẻ là dữ liệu nhạy cảm) và AA-Partner là dịch vụ xử lý dữ liệu
    cho đại lý. Nên CRM gần như chắc không hưởng miễn trừ; Booking/TripPlanner có thể hưởng (luật sư xác nhận).
- Đề xuất: (1) Ngay: nhánh "Vi phạm dữ liệu cá nhân" trong đường SEV1, hai ngả: bên kiểm soát (Booking/TP: đồng hồ 72
  giờ, người nộp = business owner, mẫu thông báo, dữ kiện gom từ `register.md`) và bên xử lý (CRM: báo đại lý ngay);
  đánh dấu "chờ luật sư xác nhận". (2) Ngay: sửa "PDPD" trong `incident-response.md` thành "PDPL (Luật 91/2025) + Nghị
  định 356/2025". (3) Ngay: host Dev `noindex` + robots disallow-all + dòng "bản xem trước, đừng nhập dữ liệu thật" trên
  form (~1 giờ) để D-01 "Dev chỉ dữ liệu test" là thật; xong AA-829 (dump trên laptop). (4) Trước dữ liệu khách thật
  đầu tiên: soạn hồ sơ đánh giá chuyển dữ liệu xuyên biên giới (Điều 20) từ `register.md`, sẵn sàng nộp trong 60
  ngày; hỏi luật sư 3 câu hẹp: AA thuộc nhóm nhỏ hay siêu nhỏ, CRM có mất miễn trừ không, mẫu và kênh nộp hiện hành.
- Công sức S · (1)–(3) Ngay; (4) trước AA-980 / go-live · Vai: STD.

**F5. LLM chưa có threat model; luật "không PII vào LLM" chỉ dựa review code; `vendor_direct` sẽ đưa dữ liệu ra ngoài AWS — Trung bình**
- Bằng chứng: `docs/legal/register.md:50` "DM-6.4 is enforced by code review only"; dòng 252–253 chưa liệt kê API
  Anthropic/OpenAI là sub-processor trực tiếp; profile `global.*` có thể xử lý ngoài Mỹ; `prompt_sanitize.py` tự nhận
  không phải phòng chống injection tổng quát.
- Đề xuất: trước khi bất kỳ stage nào được `vendor_direct`: (a) thêm API Anthropic (và OpenAI nếu dùng) vào sổ
  sub-processor kèm điều khoản lưu dữ liệu; (b) chạy pass 1–2 (regex) của scrubber CRM trong gateway chung như tripwire
  chỉ log, rồi chặn với `vendor_direct`; (c) stage tenant và khách du lịch giữ `aws_only`. Trước go-live: threat model
  một trang cho mỗi điểm vào (gộp với AI Use Register ở B7).
- Công sức M · Trước khi bật `vendor_direct` (gắn B1); threat model trước go-live · Vai: Sec, GenAI.

**F6. Baseline bảo mật SEC-01 cũ và mâu thuẫn luật merge — Trung bình** (hạ từ Trung bình/Cao: hồ sơ lỗi thời, không phải lỗ hổng)
- Bằng chứng: `docs/security/baseline.md` (last_reviewed 2026-10-20) vẫn ghi gap: Redis AUTH/TLS (đã sửa S250),
  Access Analyzer, BPA, CloudTrail một region (`baseline.md:34-35, 44, 70, 77-80`), trong khi Infra đã có
  `transit_encryption_enabled = true` (`modules/elasticache/main.tf:104`), `aws_accessanalyzer_analyzer` và
  `aws_s3_account_public_access_block` (`accounts/aa365/security_baseline.tf:66, 74`), `is_multi_region_trail = true`
  (`observability.tf:493`, AA-873 S255); SSRF (AA-875 Done), dump laptop; dòng "Merge
  rights" ghi "agents never merge" trái DM-11.5; go-live readiness mục 8 chép lại các gap cũ; `docs/security/README.md:21`
  vẫn nói trang bảo mật "chỉ ở repo private".
- Đề xuất: kiểm lại mọi dòng bằng lệnh chỉ đọc cuối `baseline.md`; cập nhật danh sách F của access review; (cột mã
  control ISO 27001 Annex A / SOC 2 CC để thành "SoA-lite": **chưa làm**, để tới trigger T-QUESTIONNAIRE); luật đóng phiên: issue gắn SEC-01 sang Done thì
  dòng đổi cùng root PR. Khi repo còn public: phát hiện khai thác được (F-3, F-7) ghi ở chỗ private, công bố sau khi sửa.
- Công sức S · Ngay (trước khi AA-880 hoặc bảng câu hỏi khách đọc); SoA-lite ở trigger · Vai: Sec, STD.

**F7. Mật khẩu DataForSEO lộ trong lịch sử repo Infra public chưa xoay — Trung bình**
- Bằng chứng: amendment ADR 0014 (dòng 84–93) và dòng vendor DataForSEO trong `docs/security/secrets-register.yaml`
  (`rotation: TBD-tech-lead`): tech lead đã chấp nhận rủi ro có ghi lại, chưa xoay; GitGuardian báo trong vài giờ. Đây
  là tài khoản trả trước, lộ khoá thì mất số dư chứ không lộ dữ liệu khách, nên mức Trung bình là đúng; register đã có
  sẵn đường xoay (AA-981) và chính nó ghi "rotate before the repos go back to private".
- Đề xuất: xoay ngay (~15 phút, $0), ghi vào dòng vendor của secrets register. Không cần viết lại lịch sử vì account ID.
- Công sức S · Ngay · Vai: Sec.

**F8. Đường admin của đại lý vào acc2 được archive, không cảnh báo — Trung bình**
- Bằng chứng: `security_access_analyzer_archive.tf:12-13, 81-97` (role `AWSReservedSSO_AdministratorAccess` tin SAML
  của đại lý, đã archive); `security_baseline.tf` cảnh báo root/IAM/SG nhưng không cảnh báo đăng nhập qua
  `AWSReservedSSO_*`; acc2 chứa PII CRM, Booking, nhân viên.
- Đề xuất: rule EventBridge ($0, forward us-east-1 + us-west-1) báo khi có ConsoleLogin, AssumeRoleWithSAML hoặc API call
  với `sessionIssuer` bắt đầu `AWSReservedSSO_`; business owner xin đại lý văn bản ai giữ permission set đó và vì sao;
  dữ liệu khách thật chỉ ở aa-prod trong org của công ty.
- Công sức S · Ngay (cảnh báo); cấu trúc theo ADR 0018 trước go-live · Vai: Sec.

**F9. Đăng nhập nhân viên một yếu tố (mã email); break-glass để cả hai yếu tố trong một secret — Trung bình**
- Bằng chứng: ADR 0006:51-53 (MFA WORKFORCE tuỳ chọn); ADR 0006a A4:126-131 (`aa-identity/dev/breakglass` chứa
  `{password, totp_seed}`); pool partner đã bắt passkey/TOTP (ADR 0006b).
- Đề xuất: pool WORKFORCE prod bắt yếu tố thứ hai (passkey có user verification hoặc TOTP) cho nhóm có quyền ghi tiền
  hoặc người dùng, hoặc liên kết với Google Workspace có 2-Step Verification bắt buộc; TOTP break-glass sang khoá cứng
  offline (~30–50 USD một lần) hoặc seed giấy niêm phong. Dùng OWASP ASVS 5.0 Level 1 làm checklist review cho AA-816.
- Công sức M · Trước go-live (build pool prod) · Vai: Sec, STD.

**F10. Cổng review cho PR rủi ro không luôn có vết — Trung bình (PLAUSIBLE)**
- Bằng chứng: lọc thô 60 PR đã merge gần nhất của AA-CIS-App: 25 PR chạm migrations/workflows/auth/rbac/iam, 2 có
  GitHub review, ~15 có nhắc review trong body/comment, ~10 không có vết; S241: 0/951 PR có review người.
- Đề xuất: check CI bắt buộc, miễn phí "risk-review" ở CIS, Booking, Partner, Infra: PR chạm đường dẫn rủi ro (dùng lại
  danh sách CODEOWNERS) cần comment có marker cố định `Review-Verdict: approve | reviewer: <agent> | model: <id> |
  scope: <files>` do agent khác tác giả đăng. Tới trigger prod, cùng check đó đổi sang cần tech lead duyệt.
- Công sức S · Ngay · Vai: STD, CTO.

**F11. Chỉ dẫn cho agent lớn, một phần ngoài git và mâu thuẫn nhau — Trung bình**
- Bằng chứng: ~45 KB chỉ dẫn luôn nạp (CLAUDE.md toàn cục + dự án, 3 steering, MEMORY.md), thêm 82 file memory,
  11 skill (~1.284 dòng SKILL.md), ~298 dòng lesson; mâu thuẫn: CLAUDE.md toàn cục bảo nhắc tắt ECS/RDS và đọc
  `handoff.md`, memory bảo không nhắc, steering dùng `docs/sessions` + Notion; SEC-01 "agents never merge" vs DM-11.5;
  memory nằm ở `~/.claude/projects/...` ngoài git.
- Đề xuất: "lint chỉ dẫn" mỗi 10 phiên (script + một lượt agent liệt kê xung đột từ khoá giữa CLAUDE.md, steering,
  skill, memory); chuyển luật bền (quyền merge, duyệt chi phí, ngôn ngữ UI, giọng Jira) từ memory vào steering/skill
  qua PR để được review và có phiên bản; cập nhật `~/.claude/CLAUDE.md`.
- Công sức M (một lần) rồi S mỗi lượt · Ngay · Vai: STD.

**F12. Danh tính E2E nhận mã qua mailbox CI đọc được không bao giờ được vào pool prod — Thấp**
- Bằng chứng: ADR 0006a A10/A10a/A10b; OTP vào mailbox S3 mà role OIDC `e2e-mail-reader` đọc được.
- Đề xuất: test trong root Terraform prod làm plan lỗi nếu trigger pool prod mang allow-map E2E hoặc CHECK email nhân
  viên nhận domain ngoài công ty; khôi phục CHECK chặt trong seed schema prod.
- Công sức S · Lúc build pool prod · Vai: Sec.

## 4. SDLC / ADLC và các chuẩn

### 4.1 Bảng chuẩn: áp dụng khi nào

Câu trả lời chuẩn cho đối tác hỏi "có ISO/SOC 2 không": **"Chưa chứng nhận. Kiểm soát của chúng tôi bám theo ISO 27001
và SOC 2 và có tài liệu; sẽ chứng nhận khi hợp đồng khách hàng yêu cầu."**

| Chuẩn / khung | Cần ngay (≤ 2 tuần) | Trước go-live | Sau / khi có trigger | Bằng chứng nằm ở đâu |
|---|---|---|---|---|
| Luật Bảo vệ DLCN 91/2025/QH15 + NĐ 356/2025 (PDPL) | Sửa chữ "PDPD" ở incident-response; nhánh vi phạm hai ngả (bên kiểm soát 72 giờ, Điều 23; bên xử lý CRM báo đại lý) chờ luật sư; Dev noindex | Hồ sơ đánh giá chuyển dữ liệu xuyên biên giới (Điều 20, nộp trong 60 ngày từ dữ liệu thật đầu tiên, miễn trừ Điều 38 không phủ); 3 câu hỏi hẹp cho luật sư; cửa sổ retention PII Booking/TP | Hồ sơ đánh giá tác động xử lý (Điều 21) nếu luật sư xác nhận không được miễn | `docs/legal/*`, `docs/ops/incident-response.md` |
| OWASP Top 10 for LLM Applications 2025 | Bảng ánh xạ trong AI Use Register v0 | Threat model mỗi điểm vào; ca injection trong Q0 | — | AI Use Register (B7) |
| NIST AI RMF 1.0 + Generative AI Profile (AI 600-1) | — | — (AI Use Register v0 ở B7 đã đủ làm phần MAP thô) | Bản "lite" (system card, MEASURE) ở T-QUESTIONNAIRE; đầy đủ khi khách doanh nghiệp đòi | AI Use Register, ADR 0009 |
| ISO/IEC 42001 | — | — | "Bám theo" qua register + ADR 0009 khi T-QUESTIONNAIRE; chứng nhận khi hợp đồng yêu cầu | — |
| ISO/IEC 27001:2022 | SEC-01 sửa cho đúng thực tế (không thêm cột Annex A) | Rà quý SEC-01 | SoA-lite (cột Annex A) ở T-QUESTIONNAIRE; chứng nhận khi hợp đồng yêu cầu | `docs/security/baseline.md` |
| SOC 2 (CC6/CC7/CC8) | Check risk-review có vết (vừa là kiểm soát thật, vừa là bằng chứng CC8.1) | — | Gom bằng chứng CC6/7/8 ở T-QUESTIONNAIRE; Type I khi hợp đồng yêu cầu | PR record, registers, postmortem |
| OWASP ASVS 5.0 | — | Level 1 làm checklist cho auth/session (AA-816, pool prod) | L2/L3 khi Booking nhận thanh toán thật | review AA-816 |
| SLSA / supply chain | Pin SHA action có quyền AWS/App | Build provenance L2 cho image ECR + verify khi deploy prod | L3 / hardened runner: không | workflow từng repo |
| DORA | Script DF/LT/CFR/MTTR + rework, báo tháng | Dùng để dự báo ngày | Không so dải "elite" | `docs/reports/kpis.yaml` |
| Kanban (SDLC quản lý) | WIP limit, Done-when đóng băng, risk register, milestone theo ngày | Forecast theo throughput | Scrum/PM chuyên trách: khi ≥ 3 người và > 1 khách | `plan.json`, `skill/aa-session` |
| Pentest bên ngoài | — | — | Trigger: trước khi Booking nhận tiền thật hoặc tenant trả tiền đầu tiên | — |

### 4.2 Khoảng trống chính

1. **Hồ sơ không còn đúng thực tế**: SEC-01 cũ, standards mâu thuẫn ADR 0018, memory mâu thuẫn steering. Bằng chứng
   cho khách/kiểm toán đọc đầu tiên đang sai.
2. **Đo lường chưa có nguồn**: DORA `sources: []`, throughput/cycle time không đo, eval không qua hiệu chuẩn, chất
   lượng dữ liệu đo bằng script tạm. Có định nghĩa, thiếu dữ liệu.
3. **Kiểm soát chỉ báo, không chặn**: drift/RLS/PII trong dump đêm, quality-paths CI non-blocking, review PR rủi ro.
4. **Quyền rộng của workload và agent**: task role CIS, apply role, agent dùng role người (OWASP LLM06).
5. **Vòng đời AI chưa khép**: chưa có ground truth của người, chưa có canary/parity khi đổi đường, chưa có sổ dùng AI.
6. **Quản lý dự án chưa có số và giới hạn**: WIP, ngày, rủi ro, quyết định có tuổi.

### 4.3 Làm việc với AI agent: nên giữ và nên sửa

**Nên giữ:**
- Định nghĩa Done bằng bằng chứng live (`skill/aa-ship`), DoR template, vòng lesson → guard → xoá.
- Danh tính riêng cho agent (GitHub App `aa-agent`, ADR 0011), trailer Co-Authored-By (572/638 commit CIS từ 01/10),
  hook chặn subagent merge/push/IAM, chặn đọc `~/.aws` và token `gh`.
- Merge queue + CI bắt buộc, agent tự merge trong giai đoạn dev (DM-11.5), cổng người bật lúc **bắt đầu build prod**
  (sớm hơn ngày go-live, theo CTO).
- Mọi call LLM qua gateway và có sổ chi phí, kể cả script tạm; "chạy thử ~3 rồi ≤ 50" cho lượt trả tiền.
- Song song lane code + lane tư vấn khi RAM cho phép; agent tự chụp bằng chứng.

**Nên sửa:**
- Bỏ "agent tự chọn 20 việc coi như duyệt" → WIP limit + business owner/tech lead chốt danh sách theo beachhead.
- Agent dùng role hẹp `aa365-agent` mặc định; role admin chỉ trong cửa sổ đã gom (F3).
- Review PR rủi ro bằng agent khác phải để lại marker kiểm được (F10); tech lead đọc mẫu 3 PR rủi ro/tuần.
- Luật bền của agent vào repo (steering/skill) qua PR; lint chỉ dẫn mỗi 10 phiên (F11).
- Agent không tự tạo bảng, workflow, gate, báo cáo đi trước người dùng (C7, E8, C9); "build only if on the path".
- Giảm nghi thức phiên: tự động snapshot, `plan.json` sinh từ Linear, Notion còn con trỏ (A6).
- Kiểm tra "kỹ sư thứ hai": quy trình phải chạy được mà không cần memory của agent (A3).

## 5. Lộ trình

Linear đang ở gói Free: ưu tiên tái dùng issue có sẵn, việc nhỏ làm thành lát/checklist trong issue cha. Issue mới
chỉ là đề xuất; tạo sau khi tech lead đồng ý (luật `aa-linear-issue`).

### 5.1 Ngay (≤ 2 tuần, tới ~14/11)

| # | Việc | Công sức | Issue Linear gợi ý |
|---|---|---|---|
| N1 | Đường LLM thứ hai: API Anthropic trực tiếp, trần chi tiêu, `vendor_direct` chỉ cho A-series + judge; trang "chế độ suy giảm"; sửa ADR 0001a | S | AA-1002 (lát mới) + AA-642 |
| N2 | Canary connection hằng ngày + alarm `llm_access_denied`; lifecycle model trong catalog; `prompt_version` sha8 trong `llm_call_log` | S×3 | AA-1002 (S-slices), AA-900 |
| N3 | Bộ nhãn người 40 mục; luật thống kê judge (≥ 30 cặp, ≥ 8/lớp, CI); khối đăng ký trước trong eval runbook | S+S | AA-919 |
| N4 | Trang chiến lược sản phẩm + cửa sổ go-live (business owner); WIP ≤ 8; đóng băng CRM W6–W8 và AA-1003 sau R4; luật build-vs-buy | S | AA-880 (đầu vào), không cần issue mới |
| N5 | `plan.json`: baseline/forecast/RAG + `risks[]`; khung quyết định tuần; báo cáo tuần một trang từ 02/11 | S | PR-20 (Jira); không cần issue Linear |
| N6 | Cắt chuỗi leo quyền IAM (chi tiết trong Linear AA-873; đã vá ở Infra #541); xoay DataForSEO (đã xong S251) | S+M | AA-873 |
| N7 | Agent mặc định `aa365-agent` (xét lại D-15) | M | gộp vào N6 |
| N8 | Chấp nhận ADR 0018 + đoạn region; sửa C7.2a/c, DM-9.6, Infra CONTEXT.md | S | AA-1004 |
| N9 | Bản sao catalog nội dung + tfstate ra ngoài acc2 (Object Lock), trước mọi lần dời org | S | AA-1004 |
| N10 | S3 gateway endpoint + recover action cho NAT | S | AA-1004 hoặc AA-880 |
| N11 | Checklist "cái gì tắt khi về private" + chọn gói GitHub; kiểm điều kiện `ref` ở các role OIDC còn lại (role apply đã có, AA-866); pin SHA action Infra; Dependabot actions cho CIS | S | issue mới "Repos back to private" (đang là mục chờ ở backlog §2) |
| N12 | Tách SNS critical/info, Route 53 health check, kênh điện thoại | S | issue mới "Alert routing" hoặc gộp AA-880 (mục 11.5) |
| N13 | Game day rollback $0 (Booking, CRM, Vercel, Lambda TP) + runbook ECS tham số + alias `live` | M | issue mới "Rollback drill" |
| N14 | Gate job-idle trong terraform-apply + tự dispatch apply Dev; drift so env task def | S | gộp N13 hoặc AA-880 |
| N15 | Đổi tên environment `prod`→`dev`, workflow deploy-by-digest | M | AA-880 |
| N16 | Script DORA + rework, báo tháng; check `risk-review` có marker | S+S | AA-1003 (DEV-01, R0–R4) |
| N17 | Sửa SEC-01 cho đúng thực tế (không SoA-lite); cảnh báo đăng nhập `AWSReservedSSO_*` | S | AA-873 |
| N18 | PDPL: nhánh vi phạm hai ngả (72 giờ bên kiểm soát / CRM báo đại lý), sửa "PDPD" ở incident-response; Dev TP noindex + cảnh báo form; xong dump laptop | S | AA-820 (mục pháp lý) + AA-829 |
| N19 | Bánh cóc sức khoẻ dữ liệu trong dump đêm; dọn tp-021, `booking.b2b_partners` | S | issue mới "Data health ratchet" hoặc gộp AA-853 |
| N20 | Diễn tập baseline schema trên instance nháp; luật "bảng ship cùng người ghi/đọc" | M | AA-880 |
| N21 | Đóng AA-997 Done-with-scope + `hide_flagged` | S | AA-997 |
| N22 | AI Use Register v0 + ADR 0009 (tách khỏi AA-804) | S | AA-804 |
| N23 | Lint chỉ dẫn agent lần đầu; chuyển luật bền từ memory vào steering/skill | M | không cần issue (việc phiên) |
| N24 | Gộp nguồn trạng thái: `plan.json` sinh từ Linear, backlog README rút gọn, `decisions.md` | M | không cần issue (việc phiên) |
| N25 | Bảng TCO trong báo cáo chi phí tháng 10 (từ 03/11) | S | báo cáo FIN-02 hiện có |

### 5.2 Trước go-live (bắt đầu khi business owner đặt ngày; một số làm sớm được)

| # | Việc | Công sức | Issue Linear gợi ý |
|---|---|---|---|
| G1 | Tham số hoá root Terraform (PR zero-change) rồi dựng aa-prod; apply role prod hẹp | L | AA-1004, AA-880 |
| G2 | Baseline schema mỗi owner đóng băng; seed nội dung (allow-list từ PII tag, parity) đã tập | M+M | AA-880 |
| G3 | DR: ký RTO 24–48 giờ; ECR replication, replica secret, export Cognito, tabletop; CMK cho RDS/S3 prod | M | AA-880 |
| G4 | Hai đường LLM độc lập cho prod; trần TPM/USD theo môi trường; payer/org xong ≥ 2 tuần trước | M | AA-1002 |
| G5 | S8: lõi `aa_llm` cho TripPlanner và CRM, contract test chung | L | AA-1002 (S8) |
| G6 | Luật phục vụ dữ kiện do LLM sinh trong data standards; job DQ địa điểm có bộ vàng | M | AA-997 (tiếp) hoặc issue mới |
| G7 | Duyệt retention cả lô, chạy live trên Dev; cửa sổ PII Booking/TP | S | issue mới "Retention approval pass" |
| G8 | Pool WORKFORCE prod bắt MFA/passkey; TOTP break-glass offline; ASVS L1 cho AA-816 | M | AA-816 |
| G9 | Allow-list ARN cho task role CIS; S3/Bedrock hẹp | S | gộp N6 |
| G10 | Task def do Terraform sở hữu; Deploy Prod theo digest + verify attestation | M | AA-880 |
| G11 | Mọi runbook đã tập một lần; paging đã thử; 2 SLO/API công khai | M | gộp N13 |
| G12 | Threat model mỗi điểm vào LLM (gộp vào AI Use Register); pin SHA app repo | S | AA-804 |
| G13 | Kỹ sư thứ hai bán thời gian + diễn tập chỉ bằng tài liệu | M | không cần issue (quyết định nhân sự) |
| G14 | Hồ sơ đánh giá chuyển dữ liệu xuyên biên giới (Điều 20) sẵn sàng nộp; 3 câu hỏi hẹp cho luật sư (nhỏ hay siêu nhỏ, CRM có mất miễn trừ, mẫu/kênh nộp) | S | AA-820 / legal readiness |
| G15 | Business support trên aa-prod (và aa-ai nếu LLM prod đi qua) | S | AA-1004 |
| G16 | PII tag đủ cho `crm` + lint thiếu tag | S | trước AA-980 |
| G17 | UAT vòng chính thức khi UI ổn định + LLM có lại | M | AA-855 |

### 5.3 Khi có trigger

| Trigger (tên) | Việc | Issue |
|---|---|---|
| T-LLM-06/11: acc3 vẫn khoá tới 06/11 | Chọn phương án LLM dự phòng trong 2 ngày làm việc (bản options S257) | AA-1002 |
| T-PILOT: một đại lý ký thư ý định / pilot | Mở lại CRM W6–W8 sau luật build-vs-buy | AA-958…AA-971 |
| T-READER: có người đọc có tên cho báo cáo | Làm thêm báo cáo ngoài R0–R4 | AA-1003 |
| T-BATCH: chi phí batch được > ~100 USD/tháng hoặc lịch chạy lại toàn catalog | Làm AA-1002 S7 (Converse batch) | AA-1002 |
| T-C3: một dòng C3 trong `03-scaling.md` nổ | Resize, RDS Proxy, replica; sửa recompute xoá-chèn lại | AA-838 |
| T-TENANT1: tenant trả tiền đầu tiên | Promote detector shadow theo tín hiệu thật; cổng người cho PR rủi ro; pentest | — |
| T-QUESTIONNAIRE: đối tác/khách gửi bảng câu hỏi bảo mật hoặc AI đầu tiên | SEC-01 thêm cột ISO 27001 Annex A / SOC 2 CC (SoA-lite); gom bằng chứng CC6/7/8; system card A1/T2/T9/TP; bản NIST AI RMF "lite" | AA-873, AA-804 |
| T-PAY: Booking nhận tiền thật | Pentest bên ngoài; ASVS L2 cho luồng thanh toán | — |
| T-CONTRACT: hợp đồng đòi chứng chỉ | SOC 2 Type I / ISO 27001 / ISO 42001 | — |
| T-TEAM3: ≥ 3 người làm thường xuyên hoặc > 200 issue chưa archive | Xét Linear trả phí; xét PM chuyên trách khi có > 1 khách | — |
| T-PROD-DATA: aa-prod nhận dữ liệu thật | Bật GuardDuty (~15–20 USD/tháng) trong aa-prod; xoay mọi secret một lần | AA-873 |
| T-ADR0018-§6: một trigger tăng trưởng của ADR 0018 | Thêm account log-archive/security/backup | AA-1004 |

## 6. Những việc KHÔNG nên làm lúc này

| Không làm | Vì sao |
|---|---|
| Dựng đủ blueprint 9 account / 7 OU, Control Tower, account log-archive/security | ADR 0018 bản lean đủ cho 2–3 người; chỉ thêm khi trigger §6 nổ. |
| Staging chạy thường trực, multi-region active/active, warm standby, per-tenant DB, Kubernetes/EKS, Aurora, Transit Gateway, tách service | Không giải quyết vấn đề đang có; nhân việc vận hành cho một người. Backup chéo region + dựng lại từ IaC là đủ. |
| Read replica, tách Booking ra RDS riêng, RDS Proxy trên Dev, đổi instance class Dev | Chưa trigger C3 nào nổ (đỉnh connection 30/181, DB 1,5 GB). |
| Interface VPC endpoint trên Dev | ~7–8 USD/AZ/endpoint/tháng, đắt hơn traffic NAT tiết kiệm; S3 gateway endpoint là ngoại lệ vì miễn phí. |
| Savings Plans / RDS reservation | Chờ prod chạy 4–8 tuần ở kích thước ổn định. |
| Thay chuỗi API Gateway → NLB → ALB | WAF trên REST API là lý do của thiết kế; chỉ đổi khi đo thấy độ trễ/chi phí. |
| Data warehouse (Redshift, Snowflake, BigQuery), dbt, CDC/Kafka/EventBridge relay, data catalog (DataHub), Macie | DB 1,5 GB; `kpi_daily` + archive Parquet đủ; Glue/Athena chờ yêu cầu BI chéo app đầu tiên. |
| Partition `llm_call_log`/`decision_log` | Bảng lớn nhất 443 MB, xa ngưỡng 10M dòng / 5 GB; retention trước. |
| GuardDuty, Security Hub, Inspector, Detective, OTel/X-Ray (AA-842), Langfuse/LangSmith/Arize, PagerDuty/Opsgenie, Sentry trả phí | Chi phí không có giá trị khi chưa có prod; đã xếp vào cổng go-live. SNS + Chatbot/SMS đủ cho một người trực. |
| Bedrock Knowledge Bases / OpenSearch Serverless, Agents/AgentCore/Flows, Prompt Management, managed Model Evaluation, Provisioned Throughput, fine-tune/distill, tự host model, thay Jev | pgvector đủ ở ~20k vector; pipeline là job xác định; đổi công cụ làm reset hiệu chuẩn; khối lượng quá nhỏ. |
| Gateway LLM dạng service HTTP / proxy kiểu LiteLLM | Giữ thư viện vendored tới khi ≥ 3 app có call prod thật hoặc khoá phải giữ tập trung. |
| Batch S7, eval trả tiền mỗi PR, chạy lại toàn catalog để "thử" đường LLM mới | Tiết kiệm ít, rủi ro cao; canary 20 mục trước, hiệu chuẩn có trần ~5 USD. |
| Thêm vòng prompt AA-790, S11 đổi model, mở rộng golden set, chuyển gate shadow → enforce, đổi mốc 7.0, hạ thanh kappa 0,6 | Chưa có judge hiệu chuẩn và nhãn người; thêm nhãn LLM không sửa lỗ hổng hợp lệ. |
| Mở lại CRM W6–W8, làm báo cáo quá R4 (lộ trình ~107 ngày công) | Chưa có pilot, chưa có người đọc. |
| Tách state Terraform / dựng `accounts/aa365-prod` trước ngày go-live | Làm một lần cùng build prod để cổng "plan không đổi" chỉ chạy một lần. |
| Mở rộng expand auto-apply sang prod hoặc file contract | ADR 0017 và ADR 0012 d7 giữ migration prod thủ công. |
| Chạy theo DORA "elite" trên Dev | Chỉ dùng làm đường xu hướng. |
| Chứng nhận SOC 2 / ISO 27001 / ISO 42001, ISMS đầy đủ (ủy ban rủi ro, CAB, audit nội bộ) | Hàng chục nghìn USD + nhiều tháng; chỉ khi hợp đồng yêu cầu. "Bám theo, chưa chứng nhận". |
| SLSA L3, hardened runner, ký Sigstore mọi artifact, pipeline SBOM đầy đủ | L2 provenance cho image là trần hợp lý tới prod. |
| ASVS L2/L3, SAMM | ASVS L1 cho auth là đủ lúc này. |
| Scrum đủ nghi thức, story point, burndown, EVM, PMBOK/PRINCE2/SAFe, ISO 9001/21502, thuê PM chuyên trách | Kanban + WIP + nhịp tuần đủ cho 1–2 người + agent. |
| Linear trả phí, đồng bộ hai chiều Linear ↔ Jira, chuyển việc kỹ thuật sang Jira | Jira chỉ cho business owner; xét Linear trả phí ở trigger T-TEAM3. |
| Thêm tài liệu/nghi thức mới | Mọi thay đổi ở đây theo hướng gộp và tự động hoá cái đang có. |
| Bổ nhiệm DPO, nộp hồ sơ cho cơ quan quản lý trước khi luật sư xác nhận miễn trừ | Chỉ chuẩn bị bản nháp. |
| Xây theo Nghị định 13/2023 | Đã bị NĐ 356/2025 thay từ 01/01/2026. |
| Viết lại lịch sử git vì account ID | Không phải credential; xoay credential thật thay vào đó. |
| Dời acc2 khỏi org đại lý trước khi đường LLM thay thế chạy được; gộp mọi thứ vào một account; chuyển Dev sang acc3 hay region mới | Một sự cố thành hai; không giải quyết rủi ro payer. |
| Thuê đội toàn thời gian trước khi chọn beachhead | Một kỹ sư thứ hai bán thời gian là đủ trước go-live. |
| Thêm app thứ năm | Phạm vi đã vượt sức đội. |
| Định tuyến bất cứ gì sang acc1 | AA-998. |

## 7. Cần duyệt

### 7.1 Business owner

| # | Quyết định | Bối cảnh | Đề xuất | Chi phí |
|---|---|---|---|---|
| BO-1 | Beachhead, cửa sổ go-live, ai trả tiền đầu tiên, phạm vi Release 1 | Không có ngày thì build prod 3–4 tuần không bắt đầu được, không dự báo được (A1, A4) | Bán trực tiếp của AA trước (TripPlanner + Booking), Content studio với một đại lý design-partner sau, cửa sổ Q1/2027; CRM ở dạng pilot; giá cho đại lý chọn trong free / theo seat / theo hoa hồng | 2–3 giờ họp; prod ~280–550 USD/tháng (giá niêm yết) chỉ khi bắt đầu build |
| BO-2 | Cấp tiền đường LLM thứ hai (API Anthropic trực tiếp) — là câu trả lời đề xuất cho câu hỏi 5 phương án đang chờ từ S257, không phải câu hỏi mới | Mọi LLM đứng từ 29/10; adapter đã có (B1) | Thẻ công ty, trần chi tiêu tổ chức 50–100 USD/tháng, chỉ dùng khi Bedrock lỗi hoặc cho A-series/judge; acc3 vẫn là chính | 0–100 USD/tháng, thường gần 0; hạn dùng của tín dụng nạp trước: đọc điều khoản Anthropic lúc nạp (bản này chưa kiểm); thuế nhà thầu (FCT) hỏi kế toán |
| BO-3 | Dữ liệu nào được gửi thẳng tới nhà cung cấp model (`vendor_direct`) | Ra ngoài AWS là quyết định quản trị dữ liệu (F5) | Cho phép nội dung A-series của AA và call judge; tenant và khách du lịch giữ `aws_only` tới khi sửa điều khoản tenant và đọc DPA vendor; đưa vào hồ sơ chuyển dữ liệu ra nước ngoài | $0; thời gian rà pháp lý |
| BO-4 | Đại lý AWS + Billing Transfer | Hạn chấp nhận 29/11 cho bắt đầu 01/12; cả hai đại lý từng gây chặn LLM (D5) | Chỉ ký khi có văn bản trả lời câu 1, 2, 6a/6b, 8 (chuyển credit, điều khoản thoát, không SCP/chặn Marketplace, quyền bán lại Claude); quyết trước ~20/11, không thì dời tháng sau và giữ LLM trên API trực tiếp; xin đại lý văn bản về đường AdministratorAccess vào acc2 | Billing Conductor 0 hoặc 50 USD/org/tháng tuỳ gói đại lý; biên đại lý chưa biết |
| BO-5 | Liên tục: người giữ quyền dự phòng ngay, kỹ sư thứ hai trước go-live | Bus factor 1 (A3) | Business owner (hoặc người được chỉ định) là chủ thứ hai trên GitHub org, AWS management, nhà đăng ký tên miền, Vercel; giữ bản break-glass niêm phong; ngân sách kỹ sư bán thời gian từ đầu build prod | $0 bây giờ; ~0,3–0,5 kỹ sư từ khi build |
| BO-6 | Khung quyết định tuần + báo cáo tuần một trang; AA-820 trước 11/11 | Quyết định đọng nhiều tuần (A5) | 30 phút/tuần, ≤ 5 quyết định, mặc định nếu 7 ngày không trả lời; báo cáo thứ Hai dưới PR-20; giữ vai product owner cho UAT và giá | 30 phút/tuần |
| BO-7 | Mục tiêu DR mất region | RTO 4 giờ hiện tại cần warm standby (D4) | RPO 24 giờ, RTO 24–48 giờ (dựng lại từ IaC + bản copy chéo region) | ~5–20 USD/tháng, so với vài trăm USD/tháng cho warm standby |
| BO-8 | Ngân sách prod gồm support và bảo mật | Basic support không đáp ứng sự cố prod (D6); GuardDuty đã hẹn cho prod | Business support trên aa-prod (và aa-ai nếu LLM prod qua đó); GuardDuty ~15–20 USD/tháng + KMS 1–3 USD/tháng bật ngày có dữ liệu thật; duyệt cùng ngày go-live | Support từ ~100 USD/tháng/account (cần kiểm giá AWS hiện hành) + ~20 USD/tháng |
| BO-9 | Câu hỏi cụ thể cho luật sư về PDPL | Miễn trừ Điều 38 chỉ phủ Điều 21, 22, 33.2, không phủ thông báo vi phạm (Điều 23) và hồ sơ chuyển dữ liệu ra nước ngoài (Điều 20); CRM xử lý dữ liệu sức khoẻ và là dịch vụ xử lý cho đại lý (F4) | Hỏi trước đại lý thật đầu tiên (AA-980): AA là doanh nghiệp nhỏ hay siêu nhỏ; CRM có mất miễn trừ không; mẫu và kênh nộp hồ sơ Điều 20 và thông báo 72 giờ; tech lead soạn sẵn nháp hồ sơ | Thời gian luật sư; nháp $0 |
| BO-11 | Gói GitHub khi repo về private (tech lead chọn phương án, business owner duyệt khoản chi tháng) | Free private tắt ruleset/environment rule; secret scanning private cần add-on Secret Protection kể cả trên Team; required reviewer private cần Enterprise (E1) | GitHub Team 1–2 seat nếu muốn giữ auto-apply migration expand; không mua Secret Protection (gitleaks đã thay); nếu không, ở Free và chấp nhận một click tay mỗi migration | ~4 USD/user/tháng + ~37 USD/tháng phút Actions private (ước tính ADR 0014), hoặc self-hosted runner |
| BO-13 | Báo cáo nào doanh nghiệp thật sự đọc | 63 báo cáo, ~107 ngày công (C9) | Xác nhận 5–7 báo cáo P0 đã live là bộ duy nhất tới go-live | Tiết kiệm phần lớn lộ trình báo cáo |

### 7.2 Tech lead

| # | Quyết định | Đề xuất | Chi phí |
|---|---|---|---|
| TL-1 | Chấp nhận ADR 0018 + region | Chấp nhận ngay, giữ us-west-1 kèm lý do viết ra, cùng root PR sửa C7.2a/c, DM-9.6, Infra CONTEXT.md | $0, S |
| TL-2 | Cách làm Terraform cho prod | Tham số hoá root hiện có (backend + tfvars mỗi account, cờ cho file chỉ Dev) bằng PR zero-change sau ADR 0018; không tách state hay dựng root prod trước ngày go-live | $0 AWS; L |
| TL-3 | WIP limit + đóng băng phạm vi | ≤ 8 In Progress, ≤ 3 mỗi lane, ≤ 2 L/XL; XL tách trước; đóng băng CRM W6–W8 và AA-1003 sau R4; ≥ 60% năng lực cho beachhead; bỏ "20 việc mỗi phiên" | $0; giải phóng ~1/3 năng lực phiên |
| TL-4 | Milestone theo ngày + risk register + Done-when đóng băng + Done-with-scope chính thức | Thêm trường vào `plan.json`, luật vào `aa-ship`/`aa-session`, rà tuần cùng PR-20 | $0, ~2 giờ |
| TL-5 | Gộp nguồn trạng thái | Linear là nguồn duy nhất; `plan.json` sinh tự động; backlog README §1–§3; `decisions.md`; Notion còn con trỏ | $0, M (1–2 phiên) |
| TL-6 | Cắt chuỗi leo quyền | Chi tiết trong Linear AA-873; đã vá ở Infra #541. | $0 |
| TL-7 | Bảo vệ environment apply của Infra | Chi tiết trong Linear AA-873; đã vá ở Infra #541 (phần còn lại); tech lead 31/10: chưa làm lúc này | $0 |
| TL-8 | Agent mặc định role hẹp (xét lại D-15) | Có: `aa365-agent` mặc định, admin trong cửa sổ đã gom | $0; thêm chút ma sát |
| TL-9 | Xoay mật khẩu DataForSEO | Xoay ngay, ghi vào secrets register | $0, ~15 phút |
| TL-10 | Judge và luật chấp nhận | Chưa judge nào "tính": 0,562 của gpt-5.6-luna là trên 13 cặp, script tự ghi `counts=False`. Dùng nó chỉ làm ứng viên cho vòng hiệu chuẩn, không làm cổng; bộ nhãn người 40 mục; luật ≥ 30 cặp/≥ 8 mỗi lớp + CI; luật dự phòng viết trước nếu kappa < 0,6; xét lại S245 D7 (b→a) | ~2 giờ người + 1–5 USD/vòng |
| TL-11 | Đóng băng tính năng eval/học tới khi T9 blog đi trọn một vòng | Gộp AA-919/920/921/922/923, AA-790, AA-1000 vào một track | Lùi A1/T2 ~2–3 phiên |
| TL-12 | Thứ tự và trần các lượt trả tiền đầu tiên khi LLM có lại | (1) canary 20 mục < 1 USD; (2) hiệu chuẩn 2 judge cổng ≤ 5 USD; (3) AA-900 R2 ≤ 2 USD; (4) AA-1000 ≤ 5 USD; (5) AA-790 sau 19/11 trên mẫu cố định; dừng ở lỗi đầu tiên | ~13 USD |
| TL-13 | Thứ tự lát AA-1002 còn lại | `prompt_version`, lifecycle, canary (S, $0) → S8 → S11 khi cổng chạy; hoãn S7 | Giải phóng ~4 ngày (S7) |
| TL-14 | Registry không gian embedding + re-embed thử | Trước khi AA-1004 đụng billing/org của acc2 | < 1 USD, ~1 ngày |
| TL-15 | ADR 0009 + AI Use Register v0 (tách khỏi AA-804) | 1–2 phiên tới, kèm bảng OWASP LLM 2025 | $0, S |
| TL-16 | Baseline schema prod + bánh cóc dump đêm + duyệt retention cả lô | Baseline mỗi owner; số xấu đi thì chặn auto-merge PR bot; `decision_log` 180 ngày + rollup | ~3–5 ngày + ~1 ngày + 1 phiên; vài cent |
| TL-17 | Check `risk-review` bắt buộc + đọc mẫu 3 PR rủi ro/tuần | Có; đổi sang tech lead duyệt ở trigger prod | ~1 lượt agent reviewer mỗi PR rủi ro |
| TL-18 | Luật bền của agent vào repo + lint chỉ dẫn mỗi 10 phiên | Có | M một lần |
| TL-19 | Tầng eval xác định $0 bắt buộc trên path filter | Cassette, schema, fixture injection/thiếu nguồn/PII; eval trả tiền vẫn tay | M, $0 định kỳ |
| TL-20 | Ai sở hữu task def ECS | Terraform sở hữu template; CI chỉ thay digest, lỗi khi trường khác lệch; quyết trước khi viết Deploy Prod | $0, ~1–2 ngày |
| TL-21 | Kênh cảnh báo critical | Hai SNS topic; critical vào Chatbot/Slack miễn phí hoặc SMS cho tech lead + một người dự phòng | ~0–3 USD/tháng |
| TL-22 | Bản sao ngoài acc2 | `pg_dump` hằng tuần schema nội dung + tfstate vào bucket Object Lock ở aa-ai, chạy trước lần dời org | ~1–5 USD/tháng |
| TL-23 | Topology LLM prod | Role chỉ-prod ở aa-ai + API vendor trực tiếp làm đường độc lập, trần theo môi trường; Bedrock native trong aa-prod chỉ sau khi warm-up (cần sửa ADR 0001a) | Trả theo dùng; M |
| TL-24 | Site TripPlanner Dev có nhận yêu cầu thật và được tìm kiếm không (chuyển từ BO-10: thuần kỹ thuật, D-01 đã quyết) | Không: noindex + dòng "bản xem trước" tới go-live; báo business owner một dòng vì mất giá trị SEO của host Dev | $0, ~1 giờ |
| TL-25 | AA-997 độ chính xác địa điểm (chuyển từ BO-12: báo cáo AA-997 viết cho tech lead; luật S248 d07 "tự giải trong hệ thống") | Chấp nhận Done-with-scope, bật `hide_flagged` (phủ bản đồ ~65% → ~48% pin, độ chính xác pin hiển thị ~88–91%); báo business owner con số phủ bản đồ; geocoder trả phí chỉ khi pin ẩn làm hại sản phẩm, lúc đó mới mang báo giá cho business owner duyệt chi | $0 bây giờ |

## 8. Nguồn

**Nội bộ (repo gốc và repo con):**
- `docs/README.md`, `docs/ecosystem-architecture.md`, `docs/engineering-handbook.md` (§2.1, §3, §6.5, §8.4, §9.2–9.3),
  `docs/onboarding.md`
- `docs/adr/0001a-retire-acc1-llm-on-acc3-only.md`, `0006*`, `0011`, `0012-environment-model.md`, `0014*`,
  `0017-migrations-in-app-pr-expand-auto-apply.md`, `0018-lean-aws-account-model.md`, `docs/adr/README.md`
- `docs/architecture/data-standards/` (`01-engineering.md`, `02-data-management.md`, `03-scaling.md`, README),
  `docs/architecture/db-schema-reference.md`, `db/connection_budget.json`
- `docs/backlog/README.md`, `docs/backlog/tracker/plan.json`, `docs/linear-export/`
- `docs/ops/README.md`, `docs/ops/incident-response.md`, `docs/ops/drills/README.md`, `docs/ops/finops.md`,
  `docs/ops/cost/README.md`, `docs/ops/runbooks/restore-rds-pitr.md`, `docs/ops/playbooks/llm-access-denied.md`,
  `docs/ops/postmortems/2026-10-29-acc3-bedrock-access-refusal.md`, `docs/generated/alarms.md`,
  `docs/generated/llm-routes.md`
- `docs/security/baseline.md`, `docs/security/README.md`, `docs/security/secrets-register.md` (+ `.yaml`),
  `docs/security/github-apps.md`
- `docs/legal/register.md`, `docs/legal/readiness-packet.md`, `docs/legal/dpa-template.md`
- `docs/reports/catalog.yaml`, `docs/reports/kpis.yaml`, `docs/templates/definition-of-ready.md`,
  `docs/research/partner-crm-spec.md`
- Audit: `docs/audits/2026-10-17-S241-sdlc-review/`, `2026-10-17-S241-restore-drill/`, `2026-10-20-S245-access-review/`,
  `2026-10-20-S245-quality-system/`, `2026-10-23-S248-aa645-writer-decision/`, `2026-10-28-S256-aa919-calibration/`,
  `2026-10-29-S257-aa790-r10-panel/`, `2026-10-29-S257-aa919-judge-compare/`, `2026-10-29-S257-llm-access-options/`,
  `2026-10-29-S258-aa790-fixed-sample/`, `2026-10-29-S258-aa919-calibration-round/`, `2026-10-29-S258-aws-org-blueprint/`,
  `2026-10-30-S260-go-live-readiness/`, `2026-10-30-S260-legal-readiness/`, `2026-10-30-S260-inprogress-triage/`,
  `2026-10-31-S261-aa997-report/`, `2026-10-31-S261-aws-bedrock-org-access/`, `2026-10-31-S261-llm-capacity-plan/`
- Log phiên `docs/sessions/` S250, S255–S260
- `.kiro/steering/*.md`, `skill/aa-session`, `skill/aa-ship`, `skill/aa-linear-issue`, `skill/aa-lessons/lessons.md`,
  `.claude/hooks/subagent-guardrails.sh`, `.claude/settings.json`
- Infra: `infra/AA-CIS-Infra/modules/{ecs,rds,vpc}/main.tf`, `accounts/aa365/{cicd,cicd_split,agent_session,
  crm_data,crm_scrub,security_cloudtrail,security_access_analyzer_archive,security_baseline,observability_ecosys,
  versions}.tf`, `.github/workflows/{terraform-plan,terraform-apply,terraform-drift}.yml`
- CIS: `apps/AA-CIS-App/services/quality/{taxonomy,thresholds,paths}.yaml`, `shared/llm_client/breaker.py`,
  `api/services/llm_connections.py`, `api/routers/admin_llm_ops.py`, `api/migrations/306_llm_anthropic_deployments.sql`,
  `services/jobs/retention_job.py`, `services/acp_content_writing/faq_filter.py`, `docs/llm/{prompt-register,
  eval-runbook}.md`, `docs/adr/0010*`, `docs/adr/0012*`, `.github/workflows/{ci,deploy-dev,eval-regression}.yml`,
  `.github/dependabot.yml`
- TripPlanner: `backend/shared/llm_gateway.py`, `frontend/app/robots.ts`; Partner: `api/app/llm/gateway.py`, `CONTEXT.md`
- Dữ liệu sống chỉ đọc: `git log --since=2026-10-17`, `gh run list`, `gh api .../environments`, `gh pr list`

**Bên ngoài (nguồn chính do các vai dẫn):**
- Anthropic, rate limits và spend limits: https://platform.claude.com/docs/en/api/rate-limits
- AWS Bedrock model lifecycle: https://docs.aws.amazon.com/bedrock/latest/userguide/model-lifecycle.html
- AWS Bedrock batch inference data: https://docs.aws.amazon.com/bedrock/latest/userguide/batch-inference-data.html
- AWS RDS chia sẻ snapshot mã hoá: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/share-encrypted-snapshot.html
- AWS IAM Access Analyzer policy generation: https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-generation.html
- Amazon Cognito MFA: https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-mfa.html
- Route 53 pricing: https://aws.amazon.com/route53/pricing/ ; AWS Price List (RDS, NAT gateway, us-west-1/us-west-2)
- GitHub pricing: https://github.com/pricing ; environments: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- GitHub Actions secure use: https://docs.github.com/en/actions/reference/security/secure-use
- CVE-2025-30066 (tj-actions/changed-files): https://nvd.nist.gov/vuln/detail/CVE-2025-30066
- OWASP Top 10 for LLM Applications 2025: https://genai.owasp.org/llm-top-10/
- NIST AI 600-1 (Generative AI Profile): https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
- Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15, đọc 31/10 trên bản điện tử: Điều 20
  https://hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-20 , Điều 21
  https://hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-21 , Điều 23
  https://hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-23 , Điều 38
  https://hethongphapluat.com/luat-bao-ve-du-lieu-ca-nhan-2025/dieu-38 . Danh mục dữ liệu cơ bản / nhạy cảm theo Nghị định
  356/2025/NĐ-CP: https://pbgdpl.cantho.gov.vn/quy-dinh-ve-danh-muc-du-lieu-ca-nhan-co-ban-va-danh-muc-du-lieu-ca-nhan-nhay-cam .
  Đây là bản sao điện tử, không phải Công báo; **luật sư vẫn phải xác nhận** trước khi đưa vào quy trình chính thức.
- GitHub secret scanning (repo private cần Secret Protection):
  https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning
- AWS Regional NAT Gateway (11/2025): https://aws.amazon.com/about-aws/whats-new/2025/11/aws-nat-gateway-regional-availability/
- Giá AWS Business Support: kiểm trên trang AWS Support pricing trước khi duyệt (BO-8).

## 9. Rà phản biện (31/10/2026)

Một lượt độc lập mở lại bằng chứng của mọi phát hiện Cao/Trung bình (file, dòng, `gh api` chỉ đọc) và đối chiếu dữ
kiện bên ngoài với nguồn gốc. Kết quả:

- **Giữ nguyên, đã xác nhận:** A1, A2, A3, A4, B1, B2, B4, C1, C3, D1, D5, E1, E3, E4, E6, F1, F2, F7, F8 (số liệu,
  dòng code và trạng thái environment GitHub khớp; vài số dòng lệch 1–2 dòng, không đổi ý).
- **Hạ mức:** D2 Cao → Trung bình (chỉ Dev); E2 Cao → Trung bình hôm nay / Cao trước go-live; F3 Cao → Trung bình
  trên Dev / Cao trước aa-prod (mở lại quyết định D-15, có kiểm soát bù); F4 Cao/Trung bình → Trung bình hôm nay / Cao
  trước dữ liệu thật; F6 Trung bình/Cao → Trung bình (hồ sơ cũ, không phải lỗ hổng).
- **Sửa dữ kiện sai hoặc thiếu:** F4 dẫn giới tính/tình trạng hôn nhân là dữ liệu nhạy cảm: sai (NĐ 356 xếp vào dữ liệu
  cơ bản), thay bằng `crm.traveler_health` + CRM là dịch vụ xử lý; miễn trừ Điều 38 chỉ phủ Điều 21, 22, 33.2, không
  phủ thông báo 72 giờ (Điều 23) và hồ sơ chuyển dữ liệu ra nước ngoài 60 ngày (Điều 20), nên hồ sơ Điều 20 thành việc
  trước go-live; bên xử lý (CRM) báo bên kiểm soát "kịp thời", không phải 72 giờ. E1 đề xuất "đặt điều kiện OIDC trong
  IAM": đã có từ AA-866, đổi thành kiểm các role còn lại. E1/BO-11: secret scanning private cần add-on Secret
  Protection kể cả trên Team. B2/TL-10: kappa 0,562 chỉ trên 13 cặp, `counts=False`, không được dùng làm cổng. B1: bổ sung
  mã lỗi khi chạm trần chi tiêu (400 trần tự đặt, 429 trần tier), tier Evaluation cho tổ chức mới, và ghi rằng BO-2 là
  câu trả lời cho câu hỏi 5 phương án đang chờ. A2: số issue đóng mỗi phiên bị nhiễu bởi issue to hơn từ S245 và đợt
  dừng LLM. A4: có một bảng rủi ro riêng cho phương án A (S257), nhưng không có register cấp chương trình. E2: giá
  Route 53 health check (HTTPS là tính năng thêm). B3: dẫn trường `modelLifecycle` và mốc 15 ngày của AWS. D2: Regional
  NAT Gateway đã có từ 11/2025. BO-2: hạn tín dụng 1 năm chưa kiểm, bỏ khẳng định.
- **Chuyển sang "khi có trigger" (T-QUESTIONNAIRE mới):** SoA-lite (cột ISO 27001 Annex A / SOC 2 CC) ở F6/N17,
  bằng chứng SOC 2 trước go-live, NIST AI RMF "lite" trước go-live, ISO 42001 "bám theo" trước go-live, system card
  từng tính năng ở B7/G12; khối "đăng ký trước" chỉ ở eval runbook, không vào PR template chung.
- **Chia lại quyết định:** BO-10 (noindex Dev) → TL-24 và BO-12 (AA-997 `hide_flagged`) → TL-25, vì đều là quyết định
  kỹ thuật, business owner chỉ cần được báo; BO-11 ghi rõ tech lead chọn phương án, business owner duyệt khoản chi.
  Số BO-10 và BO-12 để trống, không đánh lại số.
- **Bản public:** F1/F2 đã rút gọn trước khi commit vào repo gốc (public). Chi tiết trong Linear AA-873; đã vá ở Infra #541.

## Artifact

- `review.html`: <https://claude.ai/artifact/WZyv9k6EHG559tCBm3DZZz> (private, claude.ai account nghieppham@adventure.asia since S261)
