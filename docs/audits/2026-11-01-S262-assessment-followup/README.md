---
id: OPS-08-s262-assessment-followup
title: "Follow-up of the S261 architecture review: which actions became issues (S262)"
description: "Maps every action of the S261 architecture review (Now N1–N25, do-first a–e, business-owner asks, go-live G1–G17 and triggers) to Linear issues with live state, lists the gaps with no issue, and designs the Linear-to-plan.json sync."
type: report
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-01
review_every_days: 30
related: [OPS-08-s262-tl-decisions, AA-1004, AA-873, AA-900, AA-820, AA-1003, AA-880, AA-1018, AA-642]
---

# Theo dõi review kiến trúc S261: việc nào đã thành issue (S262, 01/11/2026)

> [!NOTE]
> Trả lời hai câu hỏi của tech lead ngày 01/11:
> 1. **Các việc review đã xác định đã thành issue để hành động chưa?** Mới một phần. Trong 64 mục, 6 mục đã xong,
>    20 mục làm được một phần, 7 mục có issue mở đang mang, 15 mục được quyết "chưa làm" (phần lớn ghi trong file quyết
>    định TL, không có issue), và **16 mục không có issue nào và cũng không có quyết định** (§4).
> 2. **plan.json và Linear có liên kết tự động không?** **Không. Vẫn làm tay** ở bước chốt phiên. Chưa có script đồng
>    bộ; `plan.json` hiện là bản S261 và đã lệch Linear (§5). Thiết kế đồng bộ một chiều ở §6, cỡ S, $0, cần tech lead
>    đồng ý vì TL-5 đang ở danh sách hoãn.

Nguồn: review kiến trúc S261 (`docs/audits/2026-10-31-S261-architecture-review/`), quyết định TL của S262
(`docs/audits/2026-10-31-S262-tl-decisions/README.md`), Linear đọc live 01/11 (gồm cả issue đã archive), repo gốc và
Infra `main` (`1370c7b`). File này chỉ đọc và ghi chép: không tạo issue, không sửa Linear.

## 1. Cách kiểm

- Mỗi mục của review được ánh xạ sang issue Linear, kèm trạng thái và bằng chứng.
- Bước verify (lane này) đã đọc live **26 issue** bằng `get_issue` (status, completedAt, archivedAt, dueDate,
  project): AA-642, AA-1018, AA-1002, AA-900, AA-1017, AA-919, AA-880, AA-873, AA-1004, AA-1003, AA-820, AA-829,
  AA-1015, AA-997, AA-804, AA-896, AA-855, AA-980, AA-816, AA-969, AA-838, AA-1016, AA-1010, AA-958, cộng AA-1020 và
  AA-1021 (tạo mới 01/11). Đã đọc comment của AA-1004, AA-873, AA-900, và tìm Linear theo từ khoá "rollback",
  "passkey", "retention" (gồm archive).
- Bằng chứng trong repo đã kiểm lại: `docs/ops/incident-response.md:57` còn chữ "PDPD"; ADR 0018 dòng 3 là
  "Accepted (2026-10-31, S262)"; `ai-use-register.md:138` có luật ≥ 30 cặp / ≥ 8 mỗi lớp; Infra không có
  `aws_vpc_endpoint`; ba workflow Infra còn `environment: prod`; Infra còn dùng tag action (`@v7`, `@v6`, `@v4`);
  `AWSReservedSSO` chỉ xuất hiện trong archive rule của Access Analyzer; `tools/linear/` chỉ có `linear_export.py`;
  không có `docs/decisions.md`; `index.html:207` có `PRI = {…, None: 4}`.
- Mọi trạng thái Linear trong bảng khớp với lần đọc live, trừ các điểm ở §2.

Ký hiệu trạng thái mục: **xong** · **một phần** · **có issue mở** · **chưa làm (đã quyết)** · **không issue**.

## 2. Đính chính sau khi kiểm

1. **N17 đổi từ "có issue mở" sang "không issue".** AA-873 (Backlog) không ghi gì về sửa SEC-01 hay cảnh báo đăng nhập
   SSO: comment S262 của nó chỉ liệt kê GuardDuty, chi phí tháng đầu, TL-7, TL-9, N7 và allow-list ARN. Không có
   issue nào mang N17.
2. **AA-1004 còn due date 2026-11-07** dù đang Backlog: due này đặt lúc chuyển sang Todo (S261, 04:29Z), rồi issue
   về Backlog (S262) mà due không bỏ. `plan.json` cũng giữ due này.
3. **AA-900 lệch chữ:** Linear là In Progress, nhưng comment S262 cuối cùng ghi "Remains Todo".
4. **AA-1004 comment S262 mục 5** vẫn ghi ADR 0018 "Proposed → Accepted" là việc còn lại (khớp nhận xét ở N8; ADR đã
   Accepted). Cần một comment sửa khi chạm lại AA-1004.
5. Thời điểm đóng (để đọc đúng cột "trước review"): AA-880, AA-919, AA-816 và AA-1002 đóng 31/10 lúc 01:22Z, archive
   31/10 11:24Z; AA-642, AA-1017, AA-1018, AA-804 đóng 31/10 khoảng 17:46–17:49Z, archive 01/11 04:04Z; AA-997 đóng
   01/11 01:49Z.
6. Các mục khác: trạng thái Linear trong bản ánh xạ đúng. "Done-with-scope" là cách đóng ghi trong comment đóng; trên
   Linear các issue đó chỉ hiện "Done".

## 3. Bảng ánh xạ

### 3.1 Việc "Now" (N1–N25)

| ID | Việc | Issue | Trạng thái Linear (live 01/11) | Mục | Đã làm / còn lại |
|---|---|---|---|---|---|
| N1 | Đường LLM thứ hai: Anthropic API trực tiếp có trần chi, vendor_direct chỉ cho A-series và judge, trang degraded, sửa ADR 0001a | AA-642, AA-1018, AA-1002 | AA-642 Done (archive 01/11); AA-1018 Done (archive 01/11); AA-1002 Done 31/10 01:22Z, đóng trước review | một phần | **Đã:** code live (CIS #1197/#1198/#1201/#1204), test kết nối anthropic-direct trả 1 dòng refused ở 0 USD, đường OpenAI API đã drill qua gateway 31/10, ADR 0001a và 0009 nêu API trực tiếp, TP degrade (TP #198), register đánh dấu s1_judge vendor_direct. **Còn:** chưa có khoá Anthropic và trần chi org (cần BO-2 + tech lead đăng nhập console). Chỉ nằm ở mục 4 comment AA-1004; không issue mở nào sở hữu. |
| N2 | Canary kết nối hằng ngày + alarm llm_access_denied; vòng đời model trong catalog; prompt_version trong llm_call_log | AA-1018, AA-900, AA-1017 | AA-1018 Done; AA-900 In Progress; AA-1017 Done | xong | **Đã:** probe hằng ngày bật (Infra #574 + Terraform Apply), api/worker chạy `LLM_DAILY_PROBE=on`; circuit gửi chuông + e-mail ops khi llm_access_denied (CIS #1198, thấy live 31/10); `prompt_hash` + `prompt_version` trên mọi dòng ledger (mig 321, CIS #1210) có CI gate. **Chưa kiểm:** lần chạy probe đầu tiên (≥ 05:00Z 01/11) có thành công không; hiển thị lifecycle/EOL chưa kiểm live lại. |
| N3 | Bộ 40 nhãn người; luật thống kê judge (≥ 30 cặp, ≥ 8 mỗi lớp, CI); khối pre-registration trong runbook eval | AA-900, AA-919 | AA-900 In Progress; AA-919 Done 31/10 01:22Z (trước review) | một phần | **Đã:** luật ≥ 30 / ≥ 8 trong `ai-use-register.md` (LLM09, s1_judge); kappa 0.562 chỉ là candidate. **Còn:** 40 nhãn (~2 h của tech lead) hoãn theo TL-10; chưa thấy khối pre-registration trong runbook eval. Mang trong comment AA-900. |
| N4 | Trang chiến lược sản phẩm + cửa sổ go-live (business owner); WIP ≤ 8; đóng băng CRM W6–W8 và AA-1003 sau R4; luật build-vs-buy | AA-880 | Done/archive 31/10, trước review; không issue mở | một phần | **Đã:** WIP ≤ 8 In Progress trong `skill/aa-session/SKILL.md` (S262 giữ đúng 8). **Còn:** trang chiến lược và go-live (BO-1) chưa hỏi business owner; trang báo cáo cho owner chưa làm trong S262; đóng băng W6–W8 / AA-1003 và tỷ lệ beachhead ≥ 60 % hoãn (phần còn lại của TL-3); chưa có luật build-vs-buy. |
| N5 | plan.json baseline/forecast/RAG + risks[]; khung quyết định hằng tuần; báo cáo tuần 1 trang từ 02/11 | — | Không issue (theo thiết kế; Jira PR-20) | một phần | **Đã:** root #401 thêm `due` và `risks` cho milestone; luật Done-with-scope trong `skill/aa-ship/SKILL.md`. **Còn:** chưa có trường forecast; báo cáo tuần PR-20 đã nháp nhưng chưa đăng (dời sang S263); khung quyết định tuần (BO-6) chưa tới business owner. |
| N6 | Cắt chuỗi leo thang quyền IAM; rotate DataForSEO | AA-873 | Backlog (chỉ còn mở cho GuardDuty và kiểm chi phí tháng đầu) | xong | Infra #541 đã merge; simulator cho thấy các đường leo thang bị explicit deny (comment AA-873 31/10). DataForSEO đã rotate 25/10 (S251). |
| N7 | Role hẹp mặc định cho agent (xem lại D-15) | AA-873 | Backlog; có trong comment S262 dưới dạng quyết định | chưa làm (đã quyết) | TL-8 không duyệt vì phức tạp. Trigger: trước prod. |
| N8 | Accept ADR 0018 + đoạn region; sửa C7.2a/c, DM-9.6, Infra CONTEXT.md | AA-1004 | Backlog (due 2026-11-07 còn sót) | xong | ADR 0018 Accepted (TL-1, root #401); Infra #554 sửa CONTEXT. **Lệch:** comment S262 của AA-1004 mục 5 vẫn ghi ADR 0018 là việc còn mở. |
| N9 | Bản sao content catalog + tfstate ra ngoài acc2 (Object Lock) trước khi chuyển org | — | Không issue; AA-1004 không nhắc | chưa làm (đã quyết) | TL-22 hoãn vì tốn tiền (1–5 USD/tháng), xem lại trước đợt chuyển org 01/12. Hạn 01/12 chỉ nằm trong file quyết định TL. |
| N10 | S3 gateway endpoint + EC2 recover action cho NAT instance | — | Không issue (AA-880 archive; AA-1004 không nhắc) | không issue | Infra không có `aws_vpc_endpoint` hay recover action. Miễn phí, cỡ S, nhưng chưa có issue lẫn quyết định (không phải mục TL). |
| N11 | Checklist khi repo về private + gói GitHub; điều kiện OIDC ref; pin SHA action Infra; Dependabot cho action CIS | — | Không issue | chưa làm (đã quyết) | Tech lead 31/10: repo giữ public, không trả tiền GitHub. **Còn:** các phần miễn phí không phụ thuộc private bị bỏ theo: Infra còn trộn SHA và tag (`@v7`, `@v6`, `@v4`); kiểm ref OIDC và Dependabot action CIS không ai theo dõi. |
| N12 | Tách SNS critical/info, Route 53 health check, kênh điện thoại | — | Không issue | chưa làm (đã quyết) | TL-21 hoãn vì tốn tiền (0–3 USD/tháng), trước prod. Infra còn một topic alerts. Trigger trước prod không có chỗ trên Linear. |
| N13 | Game day rollback $0 (Booking, CRM, Vercel, TP Lambda) + runbook ECS có tham số + alias "live" | — | Không issue | không issue | Tìm Linear "rollback" (gồm archive) chỉ ra AA-869/AA-892 (Done, cũ) và AA-922 (rollback của writing memory, không liên quan). G11 (mỗi runbook chạy thử một lần) gộp vào đây. |
| N14 | Gate "job rảnh" trong terraform-apply + tự dispatch apply Dev; kiểm drift với env task-def | — | Không issue | không issue | Không thấy gate job-idle trong workflow terraform-apply. TL-20 chỉ phủ một phần và đang hoãn. S262 vẫn dispatch apply tay. |
| N15 | Đổi environment prod → dev; workflow deploy-by-digest | AA-880 | Done/archive, trước review | không issue | Workflow Infra vẫn `environment: prod` (db-freshness-probe, terraform-apply, db-tour-liveness-gate). Deploy-by-digest hoãn theo TL-20. Chỗ duy nhất được nêu tên đã đóng. |
| N16 | Script DORA + rework, báo cáo tháng; check risk-review có marker | AA-1003 | Todo (due 03/11) | một phần | **Đã:** generator DEV-01/DEV-03 live (CIS #1182); DEV-01 chạy tháng đầu 03/11. **Còn:** chưa xác minh chỉ số rework; check risk-review CI (phần CI của TL-17) hoãn tới trước prod. |
| N17 | Sửa SEC-01 cho đúng thực tế (không SoA-lite); cảnh báo khi đăng nhập AWSReservedSSO_* | (AA-873 được gợi ý) | AA-873 Backlog, **không** ghi N17 | không issue (đính chính) | Chỉ có archive rule Access Analyzer nhắc AWSReservedSSO; không có rule cảnh báo đăng nhập. SoA-lite chuyển sang trigger T-QUESTIONNAIRE. |
| N18 | PDPL: nhánh breach hai đường (controller 72 h / CRM báo đại lý), sửa "PDPD"; Dev TP noindex + thông báo form; xong laptop dump | AA-820, AA-829, AA-1015 | AA-820 In Progress (due 11/11); AA-829 Done 24/10; AA-1015 Done | một phần | **Đã:** TP #200 noindex + footer "Preview site" trên Dev (live 31/10); laptop dump xử lý trong AA-829. **Còn:** `incident-response.md:57` vẫn "PDPD"; nhánh breach hai đường chưa viết; AA-820 không mang hai việc này (scope còn lại là luật sư + thông báo tenant). |
| N19 | Ratchet data-health trong dump đêm; dọn tp-021, booking.b2b_partners | — | Không issue (AA-853 Done/archive) | chưa làm (đã quyết) | TL-16 hoãn tới trước prod. Không có trên Linear. |
| N20 | Diễn tập schema baseline trên instance tạm; luật "bảng đi cùng writer/reader" | AA-880 | Done/archive, trước review | chưa làm (đã quyết) | TL-16 hoãn tới trước prod. Chỗ duy nhất được nêu tên đã đóng. |
| N21 | Đóng AA-997 Done-with-scope + hide_flagged | AA-997 | Done 01/11 01:49Z, archive | xong | CIS #1213 merge; hide_flagged ẩn 2.517 dòng; pin phục vụ 88,0 % ±4,5, phủ 50,8 %; báo cáo §7.2 đã điền. **Còn:** business owner chưa được báo số phủ bản đồ (nằm trong nháp PR-22 chưa đăng). |
| N22 | AI Use Register v0 + ADR 0009 (tách từ AA-804) | AA-804 | Done, archive 01/11 | xong | ADR 0009 Accepted cho quyết định 1–9, 13, 14 (root #397); register v0 có bảng OWASP LLM 2025 (root #401); điều khoản portal khớp register (Partner #151). Đối soát hoá đơn ≤ 5 % chờ ≥ 01/12. |
| N23 | Lint chỉ dẫn agent đầu tiên; chuyển luật bền từ memory sang steering/skill | — | Không issue (việc phiên) | chưa làm (đã quyết) | TL-18 hoãn (cỡ M). S262 chuyển 11 bài học vào aa-lessons, nhưng luật trong memory chưa chuyển, chưa có lint. |
| N24 | Gộp nguồn trạng thái: plan.json sinh từ Linear, backlog README gọn, decisions.md | — | Không issue (việc phiên) | chưa làm (đã quyết) | TL-5 hoãn (cỡ M). Đồng bộ vẫn tay (§5). Thiết kế lát S: §6. |
| N25 | Bảng TCO trong báo cáo chi phí tháng 10 (từ 03/11) | AA-896 | In Progress (due 01/11) | có issue mở | Báo cáo sơ bộ tháng 10 đã viết (471,70 USD, +165 %, 0,34 USD/tour), chưa có bảng TCO. Bản chính thức ≥ 03/11; due 01/11 trên Linear sẽ quá hạn. |

### 3.2 Năm việc "làm trước" (a–e)

| ID | Việc | Issue | Trạng thái Linear | Mục | Đã làm / còn lại |
|---|---|---|---|---|---|
| a | Đường LLM thứ hai (Anthropic trực tiếp, trần chi) + canary hằng ngày | AA-1018, AA-642 | Cả hai Done, archive | một phần | Canary bật (Infra #574); đường OpenAI API đã drill live; kết nối Anthropic có code nhưng chưa có khoá. **Còn:** khoá + trần chi (BO-2). AI viết bài trên Dev vẫn chưa chạy. |
| b | Trang chiến lược + go-live + WIP ≤ 8 + đóng băng CRM W6–W8 | — | Không issue | một phần | WIP ≤ 8 live. Trang chiến lược, go-live (BO-1), đóng băng CRM còn mở; trang báo cáo owner chưa làm. |
| c | Cắt chuỗi leo thang + rotate DataForSEO | AA-873 | Backlog | xong | Infra #541 (TL-6); DataForSEO rotate S251 (TL-9). |
| d | Accept ADR 0018, sao lưu catalog + tfstate ra ngoài acc2, thêm S3 gateway endpoint | AA-1004 | Backlog | một phần | ADR 0018 Accepted. Bản sao ngoài acc2 hoãn (TL-22, không issue, hạn 01/12); S3 endpoint không issue, không quyết định. |
| e | Bộ 40 nhãn + luật thống kê judge trước mọi eval trả tiền | AA-900 | In Progress | một phần | Luật đã viết (TL-10). 40 nhãn hoãn; eval trả tiền đằng nào cũng đang bị chặn vì mất LLM. |

### 3.3 Câu hỏi cho business owner (BO)

| ID | Việc | Issue | Trạng thái Linear | Mục | Đã làm / còn lại |
|---|---|---|---|---|---|
| BO-1 | Beachhead, cửa sổ go-live, khách trả tiền đầu tiên, phạm vi Release 1 | — | Chưa đưa lên business owner | không issue | `jira-drafts.md` S262 ghi trang báo cáo owner cho BO-1, 4–9, 13 "chưa làm trong S262". Cần trang + Jira ở S263. |
| BO-2 | Cấp tiền cho Anthropic API trực tiếp (trần 50–100 USD/tháng) | AA-1004, AA-1018 | AA-1004 Backlog (mục 4); AA-1018 Done, khoá là trigger | có issue mở | Code sẵn, kết nối đang tắt. Cần duyệt tiền + tech lead đăng nhập console tạo khoá. |
| BO-3 | Dữ liệu nào được đi vendor_direct | AA-820 | In Progress | một phần | Register: judge vendor_direct, stage tenant aws_only; điều khoản Partner #151 (Draft v0.3) nói API trực tiếp "có thể dùng làm fallback". Chờ business owner / luật sư xác nhận. |
| BO-4..9, BO-13 | Reseller + Billing Transfer (≤ 20/11), người giữ thứ hai, khung quyết định tuần, mục tiêu DR, ngân sách support/bảo mật prod, câu hỏi luật PDPL, bộ báo cáo | AA-1004, AA-820 (một phần trigger) | Chưa đưa lên | không issue | **Rủi ro hạn:** BO-4 cần quyết ~20/11 và chấp nhận Billing Transfer 29/11; nếu S263 không đưa lên thì trễ. |
| BO-11 | Gói GitHub khi repo về private | — | Bỏ | chưa làm (đã quyết) | Tech lead 31/10: repo giữ public, không trả tiền GitHub. |

### 3.4 Go-live (G1–G17)

| ID | Việc | Issue | Trạng thái Linear | Mục | Đã làm / còn lại |
|---|---|---|---|---|---|
| G1 | Tham số hoá root Terraform (PR không đổi gì), dựng aa-prod, apply bằng role prod hẹp | AA-1004, AA-880 | AA-1004 Backlog; AA-880 Done (archive) | có issue mở | AA-1004 scope mục 2 và 6. TL-2 chưa duyệt, chờ có ngày go-live. **Còn:** role apply prod hẹp chưa có trong AA-1004. |
| G2 | Schema baseline đông cứng theo owner; seed nội dung (allow-list theo thẻ PII, parity) có diễn tập | AA-880 | Done (archive) | chưa làm (đã quyết) | TL-16 hoãn "trước prod"; không có trong checklist L9 của AA-1004. Chỉ nằm trong file quyết định TL. |
| G3 | DR: ký RTO 24–48 h; ECR replication, secret replica, export Cognito, tabletop; CMK cho RDS/S3 prod | AA-1004 | Backlog | một phần | Checklist L9 trong AA-1004 có PITR 14 ngày, AWS Backup sang us-west-2, restore drill hằng quý, Multi-AZ. **Còn:** ký RTO, ECR replication, secret replica, export Cognito, tabletop, CMK không có trong checklist hay issue nào. |
| G4 | Hai đường LLM độc lập cho prod; trần TPM/USD theo môi trường; payer/org xong ≥ 2 tuần trước go-live | AA-1018, AA-1004, AA-880 | AA-1018 Done; AA-1004 Backlog; AA-880 Done | chưa làm (đã quyết) | TL-23 hoãn "trước prod". Bảng TPM prod chỉ nằm trong comment của AA-880 đã đóng. Chưa đưa vào checklist prod của AA-1004. |
| G5 | S8: lõi aa_llm chung cho TripPlanner và CRM, contract test chung | AA-642 | Done, archive | một phần | CIS #1206 (lõi + 400 ca parity), TP #202/#203 live, Partner #155/#158. **Còn:** CRM chỉ chứa bản copy lõi, không gọi nó; việc "CRM thay stub bằng adapter lõi" không ai theo dõi. |
| G6 | Luật data-standards về phục vụ dữ kiện do LLM sinh; job DQ địa điểm có golden set | AA-997 | Done, archive | một phần | hide_flagged xong, phục vụ 88,0 %, gate 79,6 % FAIL. **Còn:** không issue cho luật serving và job DQ định kỳ (export AA-997 ghi "follow-up có điều kiện, chưa mở"). |
| G7 | Duyệt retention một lượt, chạy live trên Dev; cửa sổ PII Booking/TP | — | Không issue | chưa làm (đã quyết) | TL-16 hoãn. Root #400/#420 chỉ thêm CI check dòng retention. Tìm "retention" trên Linear chỉ ra issue Done cũ. |
| G8 | Pool WORKFORCE prod bắt MFA/passkey; break-glass TOTP offline; ASVS L1 cho AA-816 | AA-816 | Done, archive | không issue | Tìm "passkey" (gồm archive) chỉ ra issue Done (AA-939, AA-854, AA-703, AA-928, AA-930). Checklist L9 không có dòng identity. |
| G9 | Allow-list ARN cho task role CIS; thu hẹp S3/Bedrock | AA-873 | Backlog | có issue mở | Có trong comment 31/10 (S261, S262) "CIS allow-list ARNs (before go-live)". Chỉ là một dòng comment, chưa vào Done-when. |
| G10 | Terraform sở hữu task def ECS; Deploy Prod theo digest + verify attestation | AA-880 | Done, archive | chưa làm (đã quyết) | TL-20 hoãn "trước khi viết Deploy Prod". Không issue mở, không dòng checklist. |
| G11 | Mỗi runbook chạy thử một lần; thử paging; 2 SLO mỗi API public | AA-969 | Backlog (chỉ CRM) | không issue | Issue "Rollback drill" (N13) chưa tạo; TL-21 hoãn; scope 2 SLO từ AA-880 không chuyển sang AA-1004. Không có gì ở mức hệ sinh thái. |
| G12 | Threat model cho mỗi điểm vào LLM; pin SHA action ở repo app | AA-804 | Done, archive | một phần | Register có bảng OWASP LLM 2025 toàn hệ. **Còn:** threat model theo điểm vào; pin SHA action ở repo app. |
| G13 | Kỹ sư thứ hai bán thời gian + một buổi diễn tập chỉ bằng docs | — | Không issue (review nói không cần issue) | không issue | Chỉ là rủi ro M5 trong `plan.json` (bus factor = 1, BO-5). Diễn tập docs-only chưa lên lịch ở đâu. |
| G14 | Hồ sơ chuyển dữ liệu xuyên biên giới Điều 20 sẵn để nộp; 3 câu hỏi hẹp cho luật sư | AA-820 | In Progress (due 11/11) | không issue | Scope AA-820 là điều khoản AUP Anthropic + ghi nguồn AI. Hồ sơ Điều 20 và 3 câu hỏi (BO-9) không ở issue nào. |
| G15 | AWS Business support trên aa-prod (và aa-ai nếu LLM prod đi qua đó) | AA-1004 | Backlog | không issue | AA-1004 và checklist L9 không nhắc gói support. Cần một dòng trong checklist prod. |
| G16 | Gắn đủ thẻ PII cho crm + lint báo thiếu thẻ | AA-980 | Backlog | một phần | Đã có 81 cột crm có thẻ. **Còn:** `gen_pii_inventory.py --strict` chỉ kiểm booking/tripplanner; không lint crm, không issue. |
| G17 | Vòng UAT chính thức khi UI ổn định và LLM trở lại | AA-855 (+ AA-1006/1007/1008/1010) | AA-855 Backlog; AA-1006/1007 Todo; AA-1008/1010 Backlog | có issue mở | Cổng round 1 ghi trong AA-855; harness dry-run AA-1009 Done S262; `plan.json` M4 có risk + trigger. |

### 3.5 Trigger (T-*)

| ID | Việc | Issue | Trạng thái Linear | Mục | Đã làm / còn lại |
|---|---|---|---|---|---|
| T-LLM-06/11 | Nếu 06/11 acc3 vẫn bị chặn: chọn đường LLM dự phòng trong 2 ngày làm việc | AA-1004, AA-1018 | AA-1004 Backlog; AA-1018 Done; AA-1002 Done | một phần | Ngày được theo dõi (backlog §1, `plan.json` checks). **Còn:** hành động "chọn trong 2 ngày làm việc" chưa ghi ở chỗ sẽ được đọc; issue review nêu (AA-1002) đã đóng. |
| T-PILOT | Mở lại CRM W6–W8 chỉ khi một đại lý ký LOI/pilot | AA-958, 959, 960, 963, 965, 968, 969, 970, 980 | Backlog | chưa làm (đã quyết) | Phần còn lại của TL-3 chưa duyệt, chuyển business owner. Backlog §3b vẫn xếp W6–W8 ở S262–S266, không có cổng pilot; chỉ AA-980 có cổng. |
| T-READER | Chỉ làm báo cáo ngoài R0–R4 khi có người đọc cụ thể | AA-1003 | Todo, due 03/11 | một phần | Cổng trong AA-1003 là mốc kinh doanh, không phải "người đọc cụ thể". Issue follow-up R5–R7 chưa có. |
| T-BATCH | Làm S7 (Converse batch) khi chi batch > ~100 USD/tháng hoặc có lịch rerun toàn catalog | AA-642 | Done, archive | chưa làm (đã quyết) | TL-13 hoãn. Trigger chỉ nằm trong issue đã archive và một audit; không có ở backlog §1/§4 hay `plan.json` checks. |
| T-C3 | Khi một dòng C3 trong 03-scaling.md kích hoạt: resize, RDS Proxy, replica; sửa recompute delete-insert | AA-838 | Done, archive | một phần | Nghi thức hằng tháng có. Rà soát tháng 10 ghi C3 "chưa đo"; một trigger gần như chắc (read model catalog, D12). |
| T-TENANT1 | Tenant trả tiền đầu tiên: nâng detector shadow, cổng người cho PR rủi ro, pentest | AA-873, AA-1016, AA-980 | AA-873 Backlog; AA-1016 Done; AA-980 Backlog | một phần | Cổng merge và GuardDuty đã ghi. **Còn:** nâng detector shadow chưa ghi; pentest chỉ có cho CRM. |
| T-QUESTIONNAIRE | Bảng hỏi bảo mật/AI đầu tiên: SEC-01 cột ISO/SOC 2 (SoA-lite), bằng chứng CC6/7/8, system card, NIST AI RMF lite | AA-873, AA-804 | AA-873 Backlog; AA-804 Done | không issue | Chỉ có trong review S261. |
| T-PAY | Booking nhận tiền thật: pentest ngoài; ASVS L2 cho luồng thanh toán | — | — | không issue | Không thấy issue/backlog Booking nào. |
| T-CONTRACT | Hợp đồng đòi chứng chỉ: SOC 2 Type I / ISO 27001 / ISO 42001 | — | — | không issue | Không có trong backlog, `plan.json`, Linear hay handbook. |
| T-TEAM3 | ≥ 3 người thường xuyên hoặc > 200 issue chưa archive: cân nhắc Linear trả phí + PM | — | — | không issue | Mâu thuẫn với luật đang có (Free, không nâng gói, S245) trừ khi tech lead sửa luật. |
| T-PROD-DATA | aa-prod có dữ liệu thật: bật GuardDuty trên aa-prod; rotate mọi secret một lần | AA-873, AA-1004 | Backlog | có issue mở | Backlog §1 và `plan.json` có GuardDuty + rotate GitHub token / master DB. **Còn:** chỉ hai secret được nêu, không phải "mọi secret". |
| T-ADR0018-§6 | Trigger tăng trưởng ADR 0018 §6: thêm account log-archive/security/backup | AA-1004 | Backlog | có issue mở | Scope AA-1004 ghi rõ "ngoài phạm vi cho tới trigger". Không có gì kiểm trigger theo lịch. |

## 4. Đếm theo trạng thái (sau đính chính N17)

| Trạng thái | Now N1–N25 | a–e | BO | Go-live G1–G17 | Trigger | Tổng |
|---|---|---|---|---|---|---|
| xong | 5 (N2, N6, N8, N21, N22) | 1 (c) | 0 | 0 | 0 | **6** |
| một phần | 6 (N1, N3, N4, N5, N16, N18) | 4 (a, b, d, e) | 1 (BO-3) | 5 (G3, G5, G6, G12, G16) | 4 (T-LLM-06/11, T-READER, T-C3, T-TENANT1) | **20** |
| có issue mở | 1 (N25) | 0 | 1 (BO-2) | 3 (G1, G9, G17) | 2 (T-PROD-DATA, T-ADR0018-§6) | **7** |
| chưa làm (đã quyết) | 8 (N7, N9, N11, N12, N19, N20, N23, N24) | 0 | 1 (BO-11) | 4 (G2, G4, G7, G10) | 2 (T-PILOT, T-BATCH) | **15** |
| không issue | 5 (N10, N13, N14, N15, N17) | 0 | 2 (BO-1, BO-4..9/13) | 5 (G8, G11, G13, G14, G15) | 4 (T-QUESTIONNAIRE, T-PAY, T-CONTRACT, T-TEAM3) | **16** |
| **Tổng** | 25 | 5 | 5 | 17 | 12 | **64** |

Kiểm: 6 + 20 + 7 + 15 + 16 = 64. Trước đính chính (N17 là "có issue mở"): 8 có issue mở, 15 không issue.

Đọc nhanh: ngoài 6 mục đã xong, 58 mục còn việc. Chỉ **7** mục có issue mở sở hữu trọn phần còn lại. Ở 20 mục
"một phần", phần còn lại thường không có chủ trên Linear. 15 mục hoãn có quyết định nhưng phần lớn chỉ nằm trong file
quyết định TL. 16 mục không có issue lẫn quyết định. Mẫu chung: phần còn lại được ghi trong comment của issue đã
đóng/archive (AA-880, AA-642, AA-997) hoặc trong file quyết định TL, nên đầu phiên không thấy.

## 5. Khoảng trống không có issue, đề xuất issue (chưa tạo)

Theo luật quota Linear (1 issue = 1 lát giao được), gom các khoảng trống thành ít issue. **Không tạo**: tech lead duyệt
trước (luật "hỏi trước khi tạo issue").

| # | Đề xuất tiêu đề issue | Project | Gom các mục | Ghi chú |
|---|---|---|---|---|
| P1 | `[AI gateway] Anthropic direct key + org spend cap, and the 06/11 acc3 fallback decision` | CIS Core — Pipeline, LLM & Platform | N1, a, BO-2, T-LLM-06/11 | Phần còn lại hiện chỉ ở AA-1004 mục 4 và issue đã đóng. Cần BO-2 + tech lead đăng nhập console. Hạn thực tế: 06/11 + 2 ngày làm việc. |
| P2 | `[Infra] Off-account copy of the content catalog and tfstate (Object Lock) before the 01/12 org move` | Data Platform — Schema, Ops & Scale | N9, d (phần sao lưu), G3 (một phần) | Có hạn cứng 01/12. Tốn 1–5 USD/tháng: cần tech lead nói "có" riêng cho mục này. |
| P3 | `[Infra] Free hardening: S3 gateway endpoint, NAT recover action, pin Infra action SHAs, OIDC ref condition, Dependabot for CIS actions` | Data Platform — Schema, Ops & Scale | N10, d (S3 endpoint), N11 (phần miễn phí), G12 (pin SHA) | $0, cỡ S. Gợi ý: duyệt ngay theo luật "miễn phí và đơn giản". |
| P4 | `[Ops] $0 rollback game day (Booking, CRM, Vercel, TP Lambda) + parameterised ECS runbook + job-idle gate in terraform-apply` | Data Platform — Schema, Ops & Scale | N13, N14, G11 (phần runbook) | $0. N15 (đổi environment prod → dev) có thể đi chung nếu không đụng TL-20. |
| P5 | `[Security] SEC-01 corrected to the real control set + alert on SSO administrator sign-in` | Data Platform — Schema, Ops & Scale | N17 | $0 (rule EventBridge vào topic sẵn có). Hoặc thêm vào Done-when của AA-873. |
| P6 | `[Legal] PDPL incident branch (72 h controller path / CRM agency path), fix "PDPD", Article 20 transfer dossier + 3 counsel questions` | CIS Core — Pipeline, LLM & Platform | N18 (phần còn), G14, BO-9 | Có thể mở rộng scope AA-820 thay vì issue mới; AA-820 due 11/11. |
| P7 | `[Platform] Pre-prod checklist v2: carry deferred TL items into AA-1004 (DR, identity, support plan, deploy-by-digest, baselines, alert routing, LLM topology)` | Data Platform — Schema, Ops & Scale | G2, G3 (phần còn), G4, G7, G8, G10, G15, N12, N15, N19, N20 | Không phải code: một comment checklist trên AA-1004 là đủ, không cần issue mới. Mục đích: không mục "trước prod" nào chỉ nằm trong file quyết định TL hay issue đã đóng. |
| P8 | `[Places] Data-standards rule for serving LLM-made facts + recurring place DQ job with a golden set` | TripPlanner & AA-Booking | G6 | Theo đề xuất "follow-up có điều kiện" của AA-997. |
| P9 | `[CRM] Replace the CRM LLM stub with the shared aa_llm core adapter + crm missing-PII-tag lint` | Partner CRM — AA-Partner | G5, G16 | Hoặc thêm hai dòng vào checklist AA-980. |
| P10 | `[Tracker] plan_sync.py: one-way Linear → plan.json sync + session-start drift check` | Data Platform — Schema, Ops & Scale | N24 (lát S), N5 (dữ liệu forecast) | Thiết kế ở §6. TL-5 đang hoãn: cần tech lead "có". |
| P11 | `[Reporting] R5–R7 follow-up, gated on a named reader` | Data Platform — Schema, Ops & Scale | T-READER | Tạo khi đóng AA-1003 sau lần chạy 03/11. |

Không đề xuất issue Linear (để đúng chỗ khác):

- **BO-1, BO-4..9, BO-13, N4 (trang chiến lược), N5 (khung quyết định tuần):** đi qua trang báo cáo owner + nháp Jira
  ở S263 (luật Jira: nháp → tech lead duyệt). **BO-4 có hạn ~20/11**, nên làm đầu S263.
- **T-BATCH, T-QUESTIONNAIRE, T-PAY, T-CONTRACT, T-TEAM3, T-TENANT1 (phần nâng detector), G13:** thêm vào một bảng
  trigger trong `docs/backlog/README.md` §1/§4 (và `plan.json` checks) để đầu phiên thấy được. T-TEAM3 mâu thuẫn luật
  "Free, không nâng gói": cần tech lead quyết có sửa luật không.
- **T-PILOT:** gắn cổng "đại lý ký LOI/pilot" vào AA-958…AA-970 và backlog §3b, sau khi business owner quyết (TL-3).
- **N23:** việc phiên (TL-18), không cần issue.
- **Sửa nhỏ trên issue có sẵn (không tạo mới):** AA-1004 bỏ mục 5 (ADR 0018 đã Accepted) và xem lại due 07/11; AA-900
  sửa chữ "Remains Todo"; AA-896 dời due sang ≥ 03/11; AA-873 đưa allow-list ARN (G9) vào Done-when.

## 6. Đồng bộ plan.json ↔ Linear

### 6.1 Hiện trạng: hoàn toàn bằng tay

- `docs/backlog/tracker/README.md` mô tả quy trình tay: bước 1 kéo issue từ Linear, bước 2 sửa `plan.json`. Dòng 7 ghi
  `plan.json` "mirrors" Linear + backlog, nhưng không có script. `tools/linear/` chỉ có `linear_export.py`.
- Kiểm 01/11: `plan.json` trong cây làm việc vẫn là bản chốt S261 (`updated` 2026-10-31, 57 issue). Chốt S262 chưa
  sửa file này (git chỉ thấy `docs/backlog/README.md` đổi).
- Lệch so với Linear live:
  - Issue đã đóng/archive vẫn nằm trong plan: AA-1009, AA-1013, AA-1014, AA-1015, AA-1016, AA-1017, AA-1018, AA-642,
    AA-804, AA-997 (đã kiểm), cùng AA-952, AA-954, AA-956, AA-957, AA-964, AA-971 theo bản ánh xạ (16 issue).
  - Issue mở chưa có trong plan: AA-1020, AA-1021 (tạo 01/11).
  - Trạng thái lệch: AA-873 và AA-1004 là In Progress trong plan nhưng Backlog trên Linear; AA-820, AA-900, AA-896
    là Todo trong plan nhưng In Progress trên Linear; AA-922 Todo trong plan, Backlog trên Linear.
  - Due thiếu trong plan: AA-998 (2026-12-01), AA-1003 (2026-11-03), AA-896 (2026-11-01).
- Lỗi phụ trong `index.html:207`: `PRI` có khoá `None` nhưng dữ liệu ghi "No priority", nên các dòng đó sắp xếp ra NaN.
  Sửa: thêm `"No priority": 4`.

### 6.2 Ai sở hữu trường nào

- **Linear sở hữu** (script luôn ghi đè trong `issues[]`): tập issue mở (state type triage, backlog, unstarted,
  started; gồm cả issue mở bị archive theo cha), `id`, `title`, `status`, `priority` (0 → "No priority", 1 Urgent,
  2 High, 3 Medium, 4 Low), `project` (map tên project sang khoá `data`, `core`, `portal`, `tpbk`, `crm` bằng prefix;
  tên lạ → cảnh báo + `other`), `due` (từ `dueDate`).
- **Không đồng bộ:** labels (gần như không dùng), estimate (chưa bật; sau này bật t-shirt estimate miễn phí thì `size`
  lấy từ Linear).
- **Tay sở hữu** (script không đụng): mỗi issue `milestone`, `session`, `size`, `next`, `needs`; cả các khối
  `milestones`, `checks`, `waiting`, `log`, `projects`, `next_session`.
- Trường tay nằm ngay trong `plan.json`, không có file phụ. Đã loại: label Linear (quá nhiều label phiên/milestone đổi
  liên tục), project milestone Linear (một milestone plan cắt ngang nhiều project), file YAML phụ (thêm phụ thuộc,
  merge hai file).

### 6.3 Script `tools/linear/plan_sync.py` (chỉ thư viện chuẩn)

- Tách `api_key()` và `gql()` từ `linear_export.py` sang `tools/linear/linear_api.py` để dùng chung. Khoá lấy từ
  Secrets Manager như `linear_export.py` hiện làm; biến môi trường ghi đè được.
- Một truy vấn GraphQL phân trang lấy issue team AA, state mở, `includeArchived: true`. Truy vấn thứ hai lấy issue
  đóng/huỷ sau `plan.updated` cho bản nháp log.
- `merge(plan, linear) -> (new_plan, diff)` là hàm thuần, có test fixture (`tools/linear/test_plan_sync.py`).
- Chế độ: mặc định dry run in diff; `--check` thoát 1 khi lệch; `--write` ghi file đúng định dạng hiện tại
  (`indent=1`, `ensure_ascii=False`, xuống dòng cuối) để không churn, đặt `updated` và thêm `synced_at`;
  `--session Sxxx`; `--log-draft` in mảng closed/canceled/created cho `log[0]`.
- Sau khi ghi: kiểm shape JSON + luật due/risks; `session` thuộc `SES_ORDER`, `milestone` thuộc `MS_ORDER` (đọc từ
  `index.html`), lệch thì cảnh báo; **guard public-safety**: fail khi thấy chuỗi 12 chữ số dạng account ID hoặc `arn:`.

### 6.4 Luật xung đột

1. Một chiều Linear → `plan.json`. Script không bao giờ ghi Linear; Linear thắng ở các trường nó sở hữu.
2. Issue đóng (Done, Canceled, Duplicate, xoá) bị bỏ khỏi `issues[]`, liệt kê trong diff và nháp log. Mở lại thì vào
   như issue mới.
3. Issue mở mới nhận giá trị chờ: `milestone:"later"`, `session:"unscheduled"`, `needs:"cần xếp slot"`; diff đánh
   dấu "NEW: slot needed".
4. `due`: Linear có thì Linear thắng; chỉ plan có (ngày chính sách) thì giữ và cảnh báo "đặt vào Linear".
5. Issue mở nhưng archive: giữ, cảnh báo.
6. Giá trị project/session/milestone lạ: cảnh báo, không fail. Chỉ guard public-safety là fail cứng.
7. Xung đột git giữa bot đêm và phiên: phiên chạy `--write` cuối cùng nên thắng; bot dựng lại nhánh từ `master`
   mới nhất mỗi đêm.

### 6.5 Khi nào chạy

- **Đầu phiên:** `plan_sync.py --write` cục bộ (không commit) để danh sách đề xuất dùng trạng thái thật; tóm tắt lệch
  vào khối trạng thái.
- **Chốt phiên:** sau bước 1 (chốt việc + Linear) và snapshot: `--write --session Sxxx` + `--log-draft`, rồi sửa tay
  slot/milestone/checks/waiting/log, validate, republish artifact. Bỏ bước 1 và phần trạng thái của bước 2 khỏi
  README tracker.
- **Tuỳ chọn, bot đêm** `.github/workflows/plan-sync.yml` ở repo gốc: cron ~23:30 UTC + `workflow_dispatch`; Actions
  secret là khoá Linear riêng, phạm vi hẹp nhất Linear cho phép (đặt bằng pipe từ Secrets Manager, không in ra);
  có diff thì đẩy nhánh `bot/plan-sync` và mở/cập nhật PR như mẫu `bot/db-schema-reference`; tự merge chỉ khi
  `--check-scope` xác nhận diff chỉ đụng trường Linear sở hữu. $0 (runner chuẩn miễn phí trên repo public, ~1 phút).
  Lợi phụ: git giữ snapshot trạng thái hằng ngày, là dữ liệu throughput/cycle time cho forecast của N5.

### 6.6 Republish trang tracker

- Chỉ phiên Claude republish được artifact claude.ai (cùng URL tracker); GitHub Action không làm được, và trang không
  đọc raw GitHub (chỉ nạp từ CDN cho phép). Vì vậy trang làm mới ở đầu phiên (tuỳ chọn) và chốt phiên (như hôm nay).
- Hiện độ cũ: `index.html` thêm "Đồng bộ Linear: <synced_at>" cạnh "Cập nhật", cùng sửa `PRI["No priority"]`.

### 6.7 Công sức và duyệt

- Script + tách API + test ~0,5 ngày; sửa `aa-session`, README tracker, `index.html` ~1–2 h; bot đêm tuỳ chọn ~2 h.
  Tổng: một lane cỡ S, khoảng nửa phiên, $0.
- Phần còn lại của N24 (cắt backlog README còn §1–§3, chuyển lịch sử sang `decisions.md`, rút gọn memory Notion thành
  con trỏ) mới là phần cỡ M.
- TL-5 đang ở danh sách hoãn. **Đề xuất:** duyệt riêng lát S này ngay, vì miễn phí và sửa được độ lệch đang có thật
  (16 issue đóng còn trên trang, 6 trạng thái sai).
