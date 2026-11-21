# Theo dõi tiêu chuẩn bảo mật trên admin: hiện trạng, thị trường và đề xuất

> **Bản tư vấn cho tech lead, đặt trong repo public.** Không có account ID, ARN, tên bucket, giá trị secret hay tên người. Chi tiết từng control vẫn nằm ở bản riêng tư của S286 (D8).

_Read-only advisory, 21/11/2026 (S287). Đầu vào: kiểm kê tài sản hiện có trong 6 repo, khảo sát thị trường (giá thấy ngày 21/11/2026, phần lớn là ước tính của bên thứ ba vì vendor không công bố bảng giá), S286 README §1/§4/§5.4–§5.6/§6, tracker AA-1162…AA-1168, `cicd_split.tf` và `docs_reader.tf` của Infra, workflow `delivery-metrics.yml`, hồ sơ chuyển dữ liệu ra nước ngoài trong `docs/legal/`. Bản nháp đã qua một vòng phản biện; các sửa đổi của vòng đó đã đưa vào đây._

---

## 1. Trả lời ngắn

- **Hiện chưa có** trang Security/Compliance trên admin. Điểm S286 (ISO 27001 45,8 %, SOC 2 44,0 %, ISO 42001 46,9 %, OWASP Top 10 64,8 %, OWASP LLM/Agentic 66,7 %, DevSecOps 50 %) được chấm **một lần**, bằng tay, không tự cập nhật. Tín hiệu bảo mật nằm rải ở 6–8 trang admin (Audit log, Staff/Directory health, Settings, AI gateway, Tenant QA › Compliance, Data erasure, Delivery, Alert recipients) và chưa nơi nào gom thành "đáp ứng bao nhiêu tiêu chí".
- **Thị trường** (Vanta, Drata, Secureframe, Thoropass, và bản open source CISO Assistant) đều làm cùng một mô hình: **một bộ common control** map nhiều-nhiều sang các khung; mỗi control có owner, tần suất, test tự động hoặc bằng chứng tay có **hạn dùng**; điểm tính lại liên tục và **chỉ đếm bằng chứng còn hạn và đạt**; exception có người duyệt và ngày hết hạn; SoA và lịch sử để auditor lấy mẫu.
- **Đề xuất: tự dựng khu "Compliance readiness" gọn trong CIS admin (phương án C) + giữ dữ liệu xuất được (hybrid)**, theo đúng pattern Delivery (AA-1108). Chi phí chạy ~0 USD/tháng khi repo còn public; pha 1 (4 bảng, 2 tab, ~10 check) dùng được sau 1–2 phiên. Chưa mua SaaS: để dành tới khi có trigger chứng nhận (D7).
- Trang hiển thị **điểm sẵn sàng (readiness), không phải chứng nhận**, và hiện **chỉ đo môi trường Dev**.

---

## 2. Hiện trạng

### 2.1 Những gì đã có, dùng lại được làm bằng chứng

| Tài sản đã có | Chứng minh cho | Dùng thế nào trong khu Compliance |
|---|---|---|
| `tools/github/guard_runs.py --json` (các guard chạy theo lịch: gitleaks history, drift, isolation probe, ci-hygiene) | Change/config management, secret hygiene | Check "guard runs xanh trong N ngày" |
| `tools/github/delivery_metrics.py` + workflow `delivery-metrics.yml` + trang Delivery | Change management, DORA | **Mẫu kiến trúc** cho collector (workflow trên master → JSON vào S3 private → CIS API đọc) |
| `register_check.py`, `docs_freshness.py` | Secrets register khớp thực tế, tài liệu được review đúng hạn | Check "register diff = 0", "docs quá hạn = 0" |
| `docs/ops/drills/README.md` | Backup/restore, BCP (RTO) | Check "drill gần nhất ≤ 90 ngày" |
| `pip_audit_gate.sh`, Trivy gate, SBOM trong CI | Vulnerability management, supply chain | Check "exception còn hạn và có lý do"; "% image có SBOM" |
| `/admin/platform/audit/verify` (audit log hash chain) | Logging, integrity | Check "chain verify OK" (cần neo chain head, xem §4.C.5) |
| Settings registry + maker-checker | Change control trên cấu hình runtime | Check "thay đổi tự duyệt = 0"; nơi giữ ngưỡng chấm điểm |
| AI gateway: `shared.llm_call_log`, kill switch, caps, eval gate | ISO 42001, OWASP LLM | Check "% call có log", "số lần break-glass", "vượt cap" |
| AI Use Register + guard | ISO 42001 A.6/A.9, EU AI Act | Check "version + guard pass" |
| EU AI Act Art. 50 marks (AA-1168, Done) | EU AI Act Art. 50(2) | Bằng chứng `met` đầu tiên |
| `docs/legal/register.md` (RoPA, sub-processor list, legal decisions log), DPA + annex, hồ sơ Article 20 | Privacy (PDPL, GDPR), supplier management | Liên kết, không tạo register mới |
| `docs/legal/consent-capture-query.md`, `dsar-erasure-runbook.md`, `docs/ops/incident-response.md` | Consent, DSAR, breach notice 72 h | Check "erasure runs", "runbook review đúng hạn" |
| Nightly `db-schema-dump` | RLS/grant trên mọi schema | Đọc trạng thái RLS cho Booking/CRM (xem §4.C.4) |
| `docs/reports/catalog.yaml` + `/admin/reports` | Nhịp báo cáo định kỳ | Thêm report "Security posture monthly review" |
| `docs/security/baseline.md` ("How to re-check") | Cấu hình AWS nền | Nguồn lệnh cho collector AWS. **Đã cũ** ở mục Trivy (giờ là gate) và CodeQL (đã có trên 4 repo app) |

### 2.2 Lỗ hổng

1. **Không có register sống**: 338 mục S286 là ảnh chụp một lần, không gắn owner, tần suất, hạn bằng chứng.
2. **Không có lịch sử**: không có snapshot theo ngày, nên không có xu hướng và không có gì cho auditor lấy mẫu trong cửa sổ quan sát.
3. **Không có kho bằng chứng bất biến**: prefix `docs-reader/` trên bucket bronze tự hết hạn bản noncurrent sau 7 ngày và role ghi có quyền Delete.
4. **Phạm vi S286 thiếu luật dữ liệu cá nhân**: S286 không chấm PDPL (Luật 91/2025/QH15 + Nghị định 356/2025/NĐ-CP, hiệu lực từ 01/01/2026) và GDPR. Đừng đọc 45,8 % hay các số khác là "đã phủ privacy".
5. **Phạm vi tài khoản**: acc1 là tài khoản AWS **cá nhân**, ngoài org công ty, nhưng đang phục vụ Bedrock LLM có nội dung tenant/khách (route Claude = Anthropic API → acc1 → acc3). Auditor sẽ nêu việc dữ liệu khách xử lý trong tài khoản cá nhân. acc3 và acc4 (Identity Center, SCP, org CloudTrail) cũng chưa nằm trong phạm vi kiểm.
6. **Thiếu các tài liệu điều khoản 4–10 của ISO**: mục tiêu đo được (6.2), chương trình internal audit (9.2), log nonconformity/corrective action (10.2), hồ sơ năng lực và nhận thức (gồm AI literacy theo EU AI Act Art. 4, áp dụng từ 02/2025).
7. **Thiết bị và con người chưa có collector nào thấy được**: laptop của tech lead (WSL, VPN), máy chạy agent, thiết bị của business owner; không có MDM (A.8.1, A.7.9, A.6.x).
8. **Review PR bởi agent**: AA-1162 tính agent review là PR review; cùng nhóm agent viết code, merge, viết collector và sinh bằng chứng. Auditor nhiều khả năng coi đây là **tự duyệt** (SOC 2 CC8.1, ISO A.8.32).

---

## 3. Thị trường làm thế nào

### 3.1 Các lựa chọn

| Tên | Loại | Giá (nguồn, xem 21/11/2026) | Hợp với mình không |
|---|---|---|---|
| **Vanta** | SaaS GRC, auto-test AWS/GitHub, trust center | ~10–25k USD/năm; tự Vanta ước tính ~25k USD năm đầu cho SOC 2 + ISO 27001 (ước tính bên thứ ba, soc2auditors.org, complyjet.com) | Chưa: đắt hơn bill AWS Dev, thêm sub-processor |
| **Drata** | SaaS GRC | ~15k USD/năm trở lên (bên thứ ba) | Chưa, cùng lý do |
| **Secureframe** | SaaS GRC | ~7,5k USD/năm bản entry (listing AWS Marketplace/Vendr, qua sprinto.com) | Ứng viên rẻ nhất nhóm lớn khi có trigger |
| **Thoropass** | SaaS GRC **kèm audit** | Một reviewer trên G2 dẫn ~8,7k USD/năm platform + ~5,8k USD/năm SOC 2 audit (**chưa kiểm**, chỉ là trích dẫn của người dùng) | Ứng viên khi cần SOC 2 nhanh |
| **Sprinto** | SaaS GRC | Ước tính bên thứ ba, thấp hơn Vanta | Như trên |
| **CISO Assistant Community** (intuitem) | Open source, AGPLv3, self-host | 0 USD license; ~10–25 USD/tháng Fargate (ước tính, chưa đo) | Không chạy service; **dùng thư viện khung làm tham chiếu ID** (kiểm license từng file thư viện trước) |
| **Probo** | Open source, MIT | 0 USD license | Nhẹ hơn, ít nội dung AI/agentic |
| **Prowler** | Open source CSPM, Apache-2.0 | 0 USD, chạy trong Actions | **Có**: mapping `iso27001_2022_aws`, `soc2_aws`, CIS, FSBP, AWS AI security |
| **AWS Security Hub CSPM** | Dịch vụ AWS | Tính theo check × resource × tần suất + finding ingestion; **cần AWS Config** (aws.amazon.com/security-hub/cspm/pricing) | Chưa, xem bẫy chi phí §4.D |
| **AWS Config** (conformance packs) | Dịch vụ AWS | 0,003 USD mỗi configuration item ghi nhận (aws.amazon.com/config/pricing) | Chưa: ENI của Fargate tạo/xoá liên tục làm tăng số item |
| **AWS Audit Manager** | Dịch vụ AWS | Tính theo resource assessment mỗi lần thu bằng chứng | **Không dùng được**: AWS ghi là ở maintenance mode từ 30/04/2026, không bật mới được (docs AWS). Cần một lệnh đọc kiểm rằng acc2 chưa từng bật |

Các con số "Security Hub Essentials" theo từng EC2/image và tin "managed conformance packs công bố 17/11/2026" xuất hiện trong khảo sát nhưng **chưa kiểm được nguồn**, nên không dùng để so sánh.

### 3.2 Thực hành chuẩn của ngành

| Thực hành | Ý nghĩa | Áp dụng cho mình |
|---|---|---|
| **Common control set** | Viết control một lần, map sang nhiều khung (ví dụ SCF làm khoá crosswalk; NIST OLIR/IR 8477 dùng quan hệ equal/subset/intersects) | ~40 control lúc đầu, lớn dần từ ma trận chồng lấn S286 §4. Bỏ qua kiểu quan hệ STRM, chỉ dùng full/partial |
| **Evidence freshness** | Mỗi bằng chứng có `collected_at` + `valid_until`; quá hạn thì không còn tính là đạt | Hạn theo tần suất, chỉnh trong Settings |
| **Continuous control monitoring (CCM)** | Test tự động chạy theo lịch, cảnh báo khi đổi trạng thái (GitLab gọi là automated control testing) | Collector GitHub/AWS/DB + drift alert hằng tuần |
| **Statement of Applicability (SoA)** | Bảng ISO 27001 Annex A (93 control) + ISO 42001 Annex A: áp dụng hay không, lý do, trạng thái | Lúc đầu là một mục trong tài liệu AA-1166, sau mới thành bảng |
| **Exception / risk acceptance** | Ngoại lệ có lý do, control bù, người duyệt, ngày hết hạn; hết hạn thì quay về gap | Lúc đầu nằm trong tài liệu AA-1166, gộp với exception vuln của AA-1163 |
| **IPE (information produced by the entity)** | Auditor kiểm chính công cụ sinh bằng chứng: code, test, version, tính đầy đủ của population | Collector có unit test, version = git SHA, heartbeat, giữ đủ danh sách population |
| **Segregation of duties** | Người làm khác người duyệt; ban lãnh đạo ký review | Business owner là người ký thứ hai |
| **Trust center** | Trang public tóm tắt posture cho khách | Để sau, khi khách pilot gửi questionnaire |
| **Readiness ≠ certification** | Điểm % chỉ là mức sẵn sàng; nghĩa vụ pháp lý là đạt/không đạt | Caption cố định trên trang; luật hiển thị dạng checklist |

---

## 4. Ba phương án

### A) Mua SaaS GRC

| Mục | Ước tính |
|---|---|
| Một lần | 0 USD license; 2–3 phiên nối AWS (IAM role read-only cho vendor), GitHub org, IdP (Cognito không phải IdP chuẩn của các tool này nên phần lớn phải làm tay), nhập policy template |
| Hằng tháng | **~625–2.100 USD** (7,5k–25k USD/năm tuỳ vendor và số khung). Audit tính riêng, theo S286 §5.6: ISO 27001 6–15k USD lần đầu + 3–6k USD/năm; SOC 2 15–35k USD + 10–30k USD/năm; ISO 42001 8–20k USD + 4–8k USD/năm (đều là ước tính, chưa có báo giá) |
| Duy trì | ~0,5 phiên/tháng xử lý task do tool tạo |
| Tự động được | Test cấu hình AWS và GitHub, policy template, nhắc việc theo owner, trust center (thường là add-on), auditor đọc trực tiếp |
| Vẫn làm tay | Policy, risk treatment, access review, management review, internal audit. Phần **đặc thù** tool không thấy: RLS/grant trên DB dùng chung, audit hash chain, `shared.llm_call_log`, kill switch và eval gate của AI gateway, AI Use Register, Art. 50 marks, maker-checker. Thiết bị cá nhân cũng không thấy nếu không có MDM |
| Lock-in | Trung bình: xuất được CSV/PDF nhưng mất lịch sử monitoring khi đổi tool |
| Auditor chấp nhận | Cao nhất (quen giao diện). Tool **không thay** audit |
| Rủi ro | Chi phí vượt bill AWS Dev; thêm một **sub-processor** đọc được AWS + GitHub (phải ghi vào `docs/legal/register.md` và DPA annex 3); mâu thuẫn D7 và luật "dịch vụ trả phí mới cần yes riêng" |

**Kết luận A:** chưa nên. Dành cho lúc có trigger: khách hoặc tender đòi SOC 2/ISO.

### B) Self-host CISO Assistant Community

| Mục | Ước tính |
|---|---|
| Một lần | 2–3 phiên: mirror image vào ECR (tag immutable), Terraform service ECS (Django + SvelteKit), database riêng trên RDS hiện có, ALB rule + host, auth staff (SSO bản Community cần kiểm lại; không có thì đặt sau ALB + Cognito), nhập thư viện khung. Cộng 2 phiên viết collector |
| Hằng tháng | ~10–25 USD Fargate (ước tính, chưa đo) + tải trên RDS dùng chung |
| Tích hợp | Bản Community **không tự thu bằng chứng cloud**: vẫn phải viết collector và đẩy qua REST API, tức phần khó nhất của C vẫn phải làm |
| Duy trì | ~0,5 phiên/tháng: nâng version, vá CVE của chính tool |
| Lock-in | Thấp |
| Auditor chấp nhận | Như C: auditor chấm bằng chứng, không chấm tool |
| Rủi ro | Thêm **một bề mặt tấn công** chứa toàn bộ gap bảo mật; UI không theo kit, không theo RBAC AA-1155, không đọc settings registry; AGPL (chạy nguyên bản thì được, **không** chép code vào repo public); thêm service trên cluster đang tiết kiệm |

**Kết luận B:** không chạy service. Chỉ dùng **ID và mapping** trong thư viện khung làm tham chiếu (sau khi kiểm license của từng file), mô tả tự viết.

### C) Khu "Compliance readiness" gọn trong CIS admin (đề xuất)

#### C.1 Kiến trúc

```
Collectors (chạy trên default branch, output thô KHÔNG BAO GIỜ ra log/artifact)
  root:  compliance-evidence.yml  daily   -> GitHub API, kết luận CI, registers trong repo
  Infra: compliance-aws.yml       nightly -> kiểm AWS read-only; Prowler weekly        (pha 2)
  CIS worker job: compliance_db_checks daily -> catalog DB + bảng app                  (pha 2)
        |
        v  evidence JSON + raw output đủ population (private)
        pha 1: s3://<bronze>/docs-reader/compliance/...  (role Docs sync, như Delivery)
        pha 2: bucket bằng chứng riêng, Object Lock + manifest ký nối chuỗi
        |
CIS API  admin_platform_compliance.py  (ingest -> bảng compliance.*, tính điểm, export)
        |
/admin/platform/compliance  (kit UI, tiếng Anh, permission compliance.read/write)
```

#### C.2 Dữ liệu: bắt đầu nhỏ

Schema CIS-owned mới `compliance`, migration qua DB Migrate, thêm một dòng vào `docs/database/schema-ownership.md`. Tên cụ thể chốt khi viết migration.

**Pha 1: 4 bảng**

| Bảng | Cột chính | Ghi chú |
|---|---|---|
| `control` | `control_id` (ví dụ `AAC-IAM-03`), title/intent **tự viết**, domain, owner_role, frequency, test_type (auto/manual/hybrid), `checks` (JSON list: check_id, collector, `validity_days`), scope (`dev`), active | **~40 control** lúc đầu: các control tự động hoá được + phần cốt lõi của điều khoản 4–10 |
| `requirement_mapping` | control_id, framework (`iso27001:2022`, `soc2:2017r2022`, `iso42001:2023`, `owasp-top10:2025`, `owasp-llm:2025`, `owasp-asi:2026`, `asvs:5.0`, `eu-ai-act`, `vn-pdpl:91/2025`, `gdpr`), ref (`A.5.15`, `CC6.1`, `LLM01`, `Art.50(2)`…), coverage (full/partial), cột SCF ID tuỳ chọn | **Chỉ ID + nhãn tự viết.** Văn bản ISO và AICPA TSC có bản quyền; SCF có điều khoản license riêng (nghi là no-derivatives, cần kiểm trước khi nhúng mô tả); OWASP là CC BY-SA (ghi nguồn, share-alike) |
| `evidence` | id, check_id, collected_at, valid_until, result (`pass`/`fail`/`error`/`manual_pending`/`manual_accepted`), summary (chỉ số tổng hợp, **không** account ID/ARN/dữ liệu khách), s3_key, sha256, **metadata run** (run id, head SHA, conclusion, timestamps, SHA của file workflow), `collector_version` = git SHA | Append-only. `stale` được **tính ra** khi `now > valid_until`. Không dựa vào `run_url`: log/artifact Actions trên repo public chỉ giữ tối đa 90 ngày |
| `score_snapshot` | date, framework, n_total, n_na, n_met, n_partial, n_fail, n_stale, n_manual_pending, strict_pct, weighted_pct, settings_version | Mỗi ngày một dòng: xu hướng + lịch sử cho auditor |

**Sau này, chỉ khi review tháng cho thấy cần:** `exception`, `risk`, `soa_entry`, `review`. Trước đó chúng là các mục trong tài liệu AA-1166 ở prefix private. Corrective action trỏ sang Linear và lessons log, không cần bảng mới.

#### C.3 Cách tính điểm

- Check **đạt** = bằng chứng mới nhất là `pass`/`manual_accepted` và chưa quá `valid_until`.
- Control **met** khi mọi check bắt buộc đạt; **partial** khi đạt một phần; **gap** khi có `fail`, `error` hoặc không có bằng chứng; **stale** khi bằng chứng đạt cuối cùng đã hết hạn (tính như gap). Control có exception còn hạn hiện "accepted risk", không cộng vào met.
- Mỗi khung có **hai số, không trộn**:
  - **Evidenced %** (số chính): strict và weighted (partial × 0,5 như S286).
  - **Assessed % (S286 baseline)**: đường tham chiếu.
- Lúc đầu Evidenced % sẽ **thấp hơn** 45–65 % của S286 vì nhiều control chưa có collector. Đó là đo đúng hơn, không phải tụt hạng.
- **EU AI Act, PDPL, GDPR là nghĩa vụ pháp lý, không phải phần trăm.** Hiện chúng dạng checklist đạt/chưa đạt, mỗi dòng có cờ "cần counsel xem".
- Caption cố định trên Overview: **"Readiness score (Dev environment), not a certification."**

**Giá trị chỉnh trong admin** (settings registry, maker-checker, luật "thresholds editable"):
- `cis.compliance.validity_days.{daily,weekly,monthly,quarterly,annual}`, đề xuất 3/10/40/100/400.
- `cis.compliance.partial_weight` (0,5).
- `cis.compliance.collector_heartbeat_hours` (36).
- `cis.compliance.drift_alert.enabled`, `cis.compliance.drift_alert.min_controls` (1).
- `cis.compliance.exception.max_days` (90), khi có bảng exception.

Đổi các giá trị này **làm đổi điểm**, nên mỗi lần đổi phải qua maker-checker có lý do, và Overview hiện "scoring settings changed on <date>".

#### C.4 Collectors

| Nguồn | Check ví dụ | Dùng lại gì | Pha |
|---|---|---|---|
| GitHub API (root, daily) | Ruleset/required checks trên default branch của 6 repo; CodeQL default setup (hiện thiếu ở root + Infra); secret scanning + push protection; Dependabot alerts quá SLA; code-scanning alerts; guard runs xanh; kết luận CI gần nhất có SBOM + Trivy gate; % PR merged có review **của người** | `guard_runs.py`, `delivery_metrics.py` | 1 (phần cần quyền alert: khi có App đọc, Q5) |
| Registers trong repo (root) | Secrets register diff = 0; docs quá hạn review; drill gần nhất + RTO; access review gần nhất; AI Use Register version + guard; vuln exceptions còn hạn; ngày cập nhật hồ sơ DPIA và hồ sơ Article 20 (PDPL) | `register_check.py`, `docs_freshness.py`, drills index, `pip_audit_gate.sh` | 1 |
| Meta-control | **Heartbeat**: mỗi collector có lần chạy thành công trong 36 h; nếu không, mọi check của nó chuyển `error` thay vì giữ màu xanh cũ | Mới | 1 |
| AWS read-only (Infra, nightly) | CloudTrail logging + log file validation; S3 account BPA; KMS rotation; IAM user không MFA = 0, root MFA; Access Analyzer (bản external-access, miễn phí) findings = 0; EventBridge security rules; log retention; RDS encrypted + backup + deletion protection; ECR immutable + scan; SG mở 0.0.0.0/0 ngoài ALB; WAF rule (AA-1165). Phạm vi gồm **acc2, acc4** (Identity Center MFA, SCP, org CloudTrail) và kiểm đọc **role invoker + logging trên acc1** | `baseline.md`, `sec_alert_check.py`, `iam_trust_inventory.py`, `terraform-drift.yml` | 2 |
| Prowler (weekly) | Số pass/fail theo mapping ISO 27001/SOC 2/CIS/FSBP/AI | Mới, 0 USD. **Không** cấu hình đẩy finding sang Security Hub | 2 |
| DB (CIS worker job, daily) | Audit chain verify OK; RLS bật trên bảng tenant; maker-checker tự duyệt = 0; AI gateway: break-glass, vượt cap, % call có log; directory drift = 0; erasure runs | `/admin/platform/audit/verify`, staff directory reconcile | 2 |
| Manual (quý) | Policy đã ký; biên bản review tháng/quý; training + AI literacy; supplier review; tabletop; **tự khai thiết bị** (mã hoá đĩa, khoá màn hình, cập nhật OS, anti-virus) của tech lead, business owner, máy chạy agent; ngày review permission set của agent (`.claude/settings.json` deny rules) | Upload presigned PUT, có hash, người nộp, hạn | 3 |

RLS của Booking/CRM: system catalog của PostgreSQL (`pg_class.relrowsecurity`, view `pg_policies`) thường đọc được bởi mọi role, nên `cis_app` **có thể** đọc trạng thái RLS của schema `booking`/`crm` mà không cần grant bảng. **Thử bằng một truy vấn read-only trước**; chỉ khi không được mới parse schema dump đêm.

#### C.5 Thiết kế bảo mật bắt buộc

Repo root và Infra đang **public**, nên đây là các bẫy dễ dính:

1. **Log và artifact Actions của repo public ai cũng xem được.**
   - Collector chỉ in số đếm. Output thô (Prowler, AWS describe có account ID/ARN) chỉ ghi file rồi đẩy lên S3 private.
   - Prowler: chuyển **toàn bộ** stdout/stderr vào file (cờ `-q`/`--quiet` vẫn in finding fail ra stdout); che account ID bằng `::add-mask::`; cấm `set -x`; nhớ rằng re-run có debug logging sẽ lộ output của step.
   - Thêm guard test grep các workflow collector tìm những pattern trên (giống `check_resource_ids.py`).
2. **Role ghi bằng chứng.**
   - **Không** dùng `tf_plan`: role này assume được từ mọi PR branch của Infra, cho nó quyền Put thì một PR có thể làm giả bằng chứng.
   - **Không** dùng ReadOnlyAccess: policy đó gồm `s3:GetObject` mọi bucket (bronze có PII), `logs:GetLogEvents`, `lambda:GetFunction` (biến môi trường), `dynamodb:GetItem`. Dùng **SecurityAudit + ViewOnlyAccess** + phần bổ sung nhỏ Prowler ghi trong tài liệu + Put **chỉ** prefix bằng chứng; deny rõ Delete, DeleteObjectVersion, BypassGovernanceRetention, PutObjectRetention.
   - **Ghim workflow, không chỉ ghim branch**: trust hiện tại của role Docs sync cho **mọi** workflow trên master của root assume. Với role bằng chứng, đổi OIDC subject template của repo để có `job_workflow_ref`, chỉ `compliance-evidence.yml` (và `compliance-aws.yml` ở Infra) assume được. Cấm `pull_request_target` trong các workflow này, gắn vào workflow lint hiện có.
   - Ghi chú phụ: `tf_plan` có cùng độ phơi ReadOnlyAccess từ mọi PR branch. Nêu ở AA-1162/AA-1166, không xử lý trong việc này.
3. **Kho bằng chứng bất biến (pha 2).**
   - Bucket nhỏ riêng, versioning + Object Lock. Governance mode **không chặn admin**: ai có `s3:BypassGovernanceRetention` (AdministratorAccess có) vẫn xoá được. Vì vậy deny BypassGovernanceRetention, PutObjectRetention, DeleteObjectVersion trong bucket policy cho mọi principal trừ break-glass; hoặc dùng compliance mode với thời hạn ngắn.
   - Mỗi ngày ghi **manifest nối chuỗi** (hash manifest hôm trước + hash các object trong ngày), để tính toàn vẹn không chỉ dựa vào lock.
   - Mã hoá SSE-S3 hoặc key có sẵn (key KMS mới tốn 1 USD/tháng + request). **Không** bật CloudTrail S3 data events cho bucket này (tính tiền theo event).
4. **Neo audit hash chain.** Người có role master DB viết lại được cả chuỗi. Mỗi ngày ghi chain head vào bucket Object Lock (~0 USD), lúc đó "audit chain verify OK" mới có nghĩa.
5. **Bằng chứng không chứa dữ liệu cá nhân của khách.** Object Lock không xoá được, sẽ xung đột với DSAR và quyền xoá theo PDPL/GDPR. Chỉ cho phép định danh staff, và ghi điều này vào RoPA trong `docs/legal/register.md`.
6. **Nội dung register không nằm trong repo.** Code ở CIS (public); control, mapping, finding và 49 mục nhạy cảm nằm trong DB + snapshot đêm lên S3 private (D8). Seed bằng DB Migrate `run-script` từ file private S286. Schema dump đêm sẽ công bố DDL lên repo root public: chấp nhận được, nhưng không đặt gì nhạy cảm trong comment bảng/cột. Fixture test dùng dữ liệu tổng hợp. UI không hiện mã issue Linear.

#### C.6 Trang admin

Route `/admin/platform/compliance`, permission mới `compliance.read`/`compliance.write` theo AA-1155, ban đầu chỉ administrator. UI tiếng Anh, dùng kit.

| Tab | Nội dung | Pha |
|---|---|---|
| Overview | Score card mỗi khung (Evidenced strict/weighted + đường S286), xu hướng 90 ngày, đếm stale/fail/manual pending/collector lỗi heartbeat, "changed since last week", caption readiness, ngày đổi settings chấm điểm | 1 |
| Controls | Bảng lọc theo khung/owner/status/stale; drawer: mapping, checks, lịch sử bằng chứng, mở bản thô qua presigned GET | 1 |
| Obligations | PDPL, GDPR, EU AI Act dạng checklist đạt/chưa đạt + cờ counsel | 2 |
| Exceptions & Risks, SoA, Reviews | Khi các bảng tương ứng ra đời | 3 |

Cảnh báo: **drift alert hằng tuần** (control met → fail/stale) qua đường Alert recipients hiện có; report "Security posture monthly review" trong `docs/reports/catalog.yaml` để `/admin/reports` hiện tới hạn/quá hạn.

#### C.7 Chi phí, công sức, rủi ro

| Mục | Ước tính |
|---|---|
| Một lần | 0 USD license; pha 1 = 1–2 phiên; tổng pha 1–3 ~4–5 phiên |
| Hằng tháng | Actions trên repo public 0 USD; S3 vài MB + vài trăm PUT/ngày < 0,10 USD; Prowler trong Actions 0 USD; bucket Object Lock SSE-S3 ~0 USD. **Tổng < 1 USD/tháng** (ước tính, chưa đo). **Điều kiện:** root và Infra còn public. Nếu repo chuyển private, CodeQL + secret scanning cần GitHub Advanced Security (trả phí) và Prowler đêm (~20 phút × 30 ≈ 600 phút/tháng) ăn vào quota Actions của org Free |
| Auditor chấp nhận | Được, nếu bằng chứng có timestamp + nguồn, đủ population, lưu bất biến, collector có version + test + heartbeat, có lịch sử qua cửa sổ quan sát. Auditor ít quen giao diện hơn Vanta, nên phải xuất CSV/SoA |
| Rủi ro | Tự build và tự duy trì collector; collector sai thì điểm sai (giảm bằng unit test + heartbeat + metadata run); register phình nếu không gộp common control; trang "đẹp nhưng không ai đọc" nếu không gắn nhịp review tháng |

### D) Bẫy chi phí cần nói rõ (áp dụng cho mọi phương án)

1. **Security Hub CSPM** tính theo check × resource × tần suất + finding ingestion vượt free tier, và **bắt buộc AWS Config**. Config là nơi bill phình: mỗi Fargate task tạo/xoá ENI, mỗi thay đổi là một configuration item 0,003 USD. Nếu có ngày bật: periodic recording hoặc loại trừ `AWS::EC2::NetworkInterface`.
2. **Giá theo image**: tag ECR `dev-<sha>` immutable tích luỹ theo mỗi commit, giá theo image sẽ tăng dần; kiểm ECR lifecycle trước khi báo giá (giá chưa kiểm).
3. **Audit Manager** tính theo resource assessment mỗi lần thu bằng chứng (ngày × resource × control). Không còn bật mới được, nhưng ghi lại để không ai thử "free tier".
4. **IAM Access Analyzer**: external-access miễn phí; **unused-access và internal-access trả phí** theo role/user mỗi tháng. Prowler và gợi ý của AWS có thể đẩy sang hai loại này: cần yes riêng.
5. **KMS key mới** cho bucket bằng chứng: 1 USD/tháng + request, phá mốc "< 1 USD". Dùng SSE-S3.
6. **CloudTrail S3 data events** trên bucket bằng chứng: tính theo event, không bật.

### E) Hybrid: C bây giờ, vendor/auditor khi có trigger

- Giữ requirement ID theo định danh chuẩn (ISO 27001:2022 Annex A, SOC 2 TSC, ISO 42001 Annex A, ASVS 5.0, OWASP LLM/ASI, điều EU AI Act, điều PDPL/GDPR) + cột SCF ID làm khoá crosswalk.
- Export có sẵn: **SoA CSV** cho tổ chức chứng nhận ISO; **control matrix CSV** (control, owner, frequency, evidence refs) để import vào Vanta/Drata/Secureframe/Thoropass hoặc CISO Assistant; sau này **OSCAL assessment-results JSON**.
- Khi có trigger: SOC 2 cho khách Mỹ → Thoropass (platform + audit một gói) hoặc Secureframe + auditor riêng; ISO 27001/42001 cho khách Úc/EU → có thể **không cần SaaS**, đi thẳng với tổ chức chứng nhận được công nhận bằng register + SoA của mình. Nếu đã chứng nhận ISO 27001 thì **ISO 27701** là phần mở rộng privacy rẻ, map được sang PDPL và GDPR.
- **PCI DSS v4.0.1** đưa vào register dạng "inactive until trigger": Booking hiện chỉ ghi thanh toán tay (`apps/AA-Booking/docs/ui-spec.md`, Q22). Khi bật Stripe/PayPal, điều kiện SAQ A (hosted checkout, script integrity trên trang thanh toán) thành một bộ control.
- **Cửa sổ quan sát**: mọi bằng chứng hiện là của Dev, không chứng minh control của prod. Scope statement và SoA phải ghi rõ; cửa sổ SOC 2 Type II hoặc đồng hồ ISO surveillance chỉ bắt đầu khi có prod.

### Bảng so sánh

| | A. SaaS | B. CISO Assistant self-host | **C. Tự dựng trong CIS admin** |
|---|---|---|---|
| Một lần | 2–3 phiên nối tích hợp | 2–3 phiên deploy + 2 phiên collector | 1–2 phiên cho pha 1; 4–5 phiên cho pha 1–3 |
| Hằng tháng | ~625–2.100 USD + audit riêng | ~10–25 USD + upkeep | < 1 USD (khi repo còn public) |
| Thấy dữ liệu đặc thù (RLS, AI gateway, audit chain) | Không (custom/upload tay) | Có nếu tự đẩy vào | Có, trực tiếp |
| Thu bằng chứng tự động | AWS/GitHub tốt | Không (tự viết) | Tự viết, dùng lại guard sẵn có |
| Auditor quen | Rất quen | Trung bình | Trung bình (bù bằng export) |
| Lock-in | Trung bình | Thấp | Thấp |
| Hợp D7/D8/luật nhà | Không (chi phí, sub-processor) | Một phần | Có |

---

## 5. Đề xuất và lộ trình

**Đề xuất:** phương án C + hybrid export. B chỉ dùng thư viện khung làm tham chiếu ID. Prowler thay Security Hub/Config. Không mua SaaS trước trigger.

### Pha 1: dùng được ngay (1–2 phiên)

Pha 1 **chưa có kho bất biến**: bằng chứng là "readiness tracking", chưa đủ cho cửa sổ audit. Lý do: kho bất biến cần role mới, bucket mới và GitHub App mới, mà App chỉ tech lead (owner org) tạo được.

1. **Migration** schema `compliance` với 4 bảng (`control`, `requirement_mapping`, `evidence`, `score_snapshot`), grant cho `cis_app`, dòng mới trong `schema-ownership.md`.
2. **Seed ~40 control** + mapping từ file private S286 qua DB Migrate `run-script` (dữ liệu không vào repo). Gồm cả các control điều khoản 4–10, PDPL/GDPR (dạng obligation), acc1/acc3 trong scope.
3. **Collector root `compliance-evidence.yml`** (daily), ~10 check không cần quyền đặc biệt: ruleset/required checks, CodeQL setup, guard runs xanh, CI có SBOM + Trivy, secrets register diff, docs overdue, drill gần nhất, access review gần nhất, vuln exceptions còn hạn, ngày cập nhật hồ sơ PDPL, heartbeat. Ghi vào `docs-reader/compliance/` bằng **role Docs sync hiện có, đúng như Delivery** (prefix này nằm ngoài các lệnh `sync --delete` của Docs sync, chỉ `pages/`, `assets/`, `learn/` bị xoá đồng bộ). Guard test chặn output thô ra log.
4. **API + trang** `/admin/platform/compliance`: Overview + Controls (drawer bằng chứng). Settings `cis.compliance.validity_days.*`, `partial_weight`, `collector_heartbeat_hours`. Permission `compliance.read`.
5. Sửa `baseline.md` (Trivy là gate; CodeQL trên 4 repo app) và bật CodeQL default setup cho root + Infra (gộp vào AA-1162).

### Pha 2: kho bất biến + cloud + DB (2 phiên)

6. GitHub App chỉ đọc (Q5) do tech lead tạo → bật các check Dependabot, secret scanning, code scanning.
7. Terraform Infra (đổi IAM, cần review trước merge): bucket bằng chứng Object Lock + bucket policy deny bypass; role `compliance-evidence` (SecurityAudit + ViewOnlyAccess + Put prefix, trust ghim `job_workflow_ref`). Chuyển collector root sang bucket mới; manifest nối chuỗi hằng ngày; neo audit chain head.
8. `compliance-aws.yml` nightly + Prowler weekly (acc2, acc4; đọc role invoker trên acc1). Một lệnh đọc kiểm acc2 chưa bật Audit Manager.
9. CIS worker job `compliance_db_checks` (thử đọc `pg_policies` cho Booking/CRM trước). Tab Obligations. Drift alert hằng tuần. Check "% image chạy có scan + SBOM" (AA-1164), WAF rule (AA-1165).

### Pha 3: lớp hệ quản lý (1–2 phiên, cùng AA-1166)

10. Bảng `exception` (maker-checker, **hai người khác nhau**: tech lead đề xuất, business owner duyệt), gộp exception vuln của AA-1163. Bảng `risk`, `soa_entry`, `review` khi review tháng cho thấy cần.
11. Upload bằng chứng tay (presigned PUT, hash, hạn) vào bucket Object Lock, gồm tự khai thiết bị hằng quý.
12. Export SoA CSV + control matrix CSV; report "Security posture monthly review"; biên bản review tháng đầu tiên, business owner ký thứ hai.

### Pha 4: theo trigger

13. OSCAL export; AI adversarial pass rate (promptfoo/garak, nối trap set AA-1167); ASVS L1 checklist; control PCI DSS khi bật thanh toán online.
14. Trust center public, chỉ khi khách pilot gửi security questionnaire, chỉ ghi điều đã kiểm.
15. Chọn vendor/auditor (D7); bắt đầu cửa sổ quan sát khi có prod.

### Liên hệ AA-1162…AA-1168

| Issue | Chỗ chồng lấn |
|---|---|
| AA-1162 Repo change control | Check ruleset + required checks + % PR có **review của người** (pha 1). Đề xuất thêm vào scope: bật CodeQL root + Infra; ghi chú độ phơi ReadOnlyAccess của `tf_plan`; control bù cho "agent review" (tech lead lấy mẫu + ký tháng) |
| AA-1163 Vuln management v2 | Check quá SLA + exception hợp nhất + biên bản triage tháng (pha 2–3) |
| AA-1164 Nightly scan image đang chạy | Check "% image chạy có scan + SBOM" (pha 2) |
| AA-1165 WAF rate rule | Một check AWS (pha 2) |
| AA-1166 ISMS-lite/AIMS-lite | **Gắn chặt nhất**: pha 3 là "chỗ chứa" của AA-1166; scope statement phải nêu acc1, acc3, Dev-only; risk register có mục acc1 (review đầu tháng 12 thành risk treatment); dùng chung prefix private |
| AA-1167 AI output & prompt hardening | Check sanitizer trên mọi publish path + trap set pass rate (pha 2/4) |
| AA-1168 EU AI Act Art. 50 marks (Done) | Bằng chứng `met` đầu tiên cho `eu-ai-act Art.50(2)` (seed pha 1) |

Chưa có issue cho trang + register + collector. Theo luật phải **hỏi trước khi tạo** (Q9).

### Nhịp giám sát, cải tiến, nâng cấp (PDCA)

- **Mỗi PR:** gate CI như hiện tại.
- **Hằng ngày/tuần:** collector tự chạy; heartbeat; drift alert tuần.
- **Hằng tháng:** tech lead review control đỏ/stale, triage vuln, lấy mẫu PR do agent review; business owner ký thứ hai. Việc sửa gom thành **gói việc** (1 issue Linear ≈ 1 PR), không mở 1 issue mỗi finding (Linear Free 250 issue).
- **Hằng quý:** access review, tự khai thiết bị, review permission set của agent, management review lite, đặt mục tiêu quý (ví dụ Evidenced weighted ISO Annex A ≥ 60 %).
- **Hằng năm hoặc khi có sự kiện lớn** (prod, khách trả tiền đầu tiên, thanh toán online, đổi tài khoản AWS): risk assessment, review SoA, internal audit, pentest, quyết định chứng nhận.

---

## 6. Quyết định cần tech lead

| # | Câu hỏi (bối cảnh một dòng) | Đề xuất |
|---|---|---|
| Q1 | Chọn phương án nào: SaaS đắt và mù dữ liệu đặc thù, self-host thêm bề mặt tấn công, tự dựng rẻ nhưng tự duy trì | **C + hybrid export**; B chỉ dùng làm tham chiếu ID |
| Q2 | Register để đâu khi repo public | **DB schema `compliance` + snapshot đêm lên S3 private**; repo chỉ chứa code |
| Q3 | Số chính trên trang | **Evidenced % (chỉ bằng chứng còn hạn + đạt), strict và weighted**, S286 làm đường tham chiếu; chấp nhận số ban đầu thấp hơn |
| Q4 | Cỡ register lúc đầu | **~40 common control, map full/partial**, lớn dần từ ma trận S286; không giữ 338 mục theo từng khung |
| Q5 | Collector cần đọc Dependabot/secret/code scanning của 6 repo, GITHUB_TOKEN không đủ | **GitHub App mới chỉ đọc** (administration, security events, Dependabot + secret scanning alerts, actions: read), tách khỏi App merge `aa-agent`; tech lead tạo (pha 2); ghi vào SEC-07 |
| Q6 | Role AWS ghi bằng chứng | **Role mới `compliance-evidence`**: SecurityAudit + ViewOnlyAccess + Put prefix, trust ghim `job_workflow_ref`, deny delete/bypass; không dùng `tf_plan`, không ReadOnlyAccess |
| Q7 | Pha 1 ghi bằng chứng ở đâu khi chưa có kho bất biến | **Dùng role Docs sync + `docs-reader/compliance/` như Delivery**, ghi rõ "readiness, chưa bất biến"; kho Object Lock ở pha 2 |
| Q8 | Kho bất biến | **Bucket nhỏ mới, versioning + Object Lock, bucket policy deny bypass, manifest nối chuỗi, SSE-S3**; ~0 USD/tháng; không bật Object Lock trên bronze (không đảo ngược được) |
| Q9 | Linear: nhét vào AA-1166 hay tạo issue mới | **Tạo 1 issue "Compliance register + evidence page (phase 1–2)" cùng project với AA-1166**; AA-1166 là tài liệu, trang là code |
| Q10 | Ai xem trang | **Permission mới `compliance.read`/`write`, ban đầu chỉ administrator** |
| Q11 | Security Hub CSPM / AWS Config / Access Analyzer trả phí | **Không bây giờ**, dùng Prowler free; xem lại khi có prod (Audit Manager không còn bật được) |
| Q12 | "Agent review" có tính là review không | **Không tính là met**; thêm control bù: tech lead lấy mẫu PR + ký tháng; human approval cho PR rủi ro khi có prod |
| Q13 | Ai ký thứ hai cho review/exception | **Business owner**, để có tách nhiệm (SOC 2 CC1, ISO 9.3) |
| Q14 | Thêm PDPL/GDPR vào phạm vi chấm | **Có**, dạng obligation checklist có cờ counsel; câu hỏi Luật Dữ liệu 60/2024 và quy định lưu trữ trong nước của luật an ninh mạng (dữ liệu ở us-west-1) chuyển cho counsel, không tự kết luận |
| Q15 | Phạm vi tài khoản | **Đưa acc1, acc3, acc4 vào scope**; acc1 (tài khoản cá nhân phục vụ Bedrock) thành mục risk register, gắn với buổi review đầu tháng 12 |
| Q16 | Trigger chứng nhận và shortlist | **Chốt shortlist, mua khi có trigger thật**: Thoropass (SOC 2 nhanh, kèm audit), Secureframe (rẻ nhất nhóm lớn); ISO 27001/42001 đi thẳng với tổ chức chứng nhận bằng SoA của mình |
| Q17 | Trust center public | **Để sau**, khi khách pilot gửi security questionnaire |

---

## 7. Nguồn

Giá và tình trạng dịch vụ thấy ngày 21/11/2026; số của vendor SaaS là ước tính bên thứ ba.

- Thị trường và giá:
  - <https://soc2auditors.org> (tổng hợp giá Vanta/Drata/Sprinto/Thoropass)
  - <https://www.complyjet.com>
  - <https://sprinto.com/blog/secureframe-pricing/>
  - <https://www.g2.com/products/thoropass/pricing> (trích dẫn reviewer, chưa kiểm)
  - <https://aws.amazon.com/security-hub/cspm/pricing/>
  - <https://aws.amazon.com/config/pricing/>
  - <https://docs.aws.amazon.com/audit-manager/latest/userguide/audit-manager-availability-change.html>
  - <https://aws.amazon.com/iam/access-analyzer/pricing/>
- Open source:
  - <https://github.com/intuitem/ciso-assistant-community> (AGPLv3; license từng file thư viện cần kiểm)
  - <https://github.com/prowler-cloud/prowler> (Apache-2.0)
  - <https://github.com/getprobo/probo> (MIT)
- Thực hành:
  - <https://securecontrolsframework.com/free-content/> (SCF, STRM; kiểm điều khoản license)
  - <https://www.nist.gov/cyberframework/csf-20-informative-references> (OLIR)
  - <https://csrc.nist.gov/pubs/ir/8477/final> (NIST IR 8477, set theory relationship mapping)
  - <https://handbook.gitlab.com/handbook/security/security-assurance/security-compliance/automated-control-testing/>
  - <https://pages.nist.gov/OSCAL/> (OSCAL)
  - <https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect> (OIDC subject, `job_workflow_ref`)
- Nội bộ (đường dẫn trong repo):
  - `docs/audits/2026-11-20-S286-devsecops-standards/README.md` (§1, §4, §5.4–§5.6, §6)
  - `docs/legal/vn-cross-border-transfer-dossier.md` (Luật 91/2025/QH15, Nghị định 356/2025/NĐ-CP; chưa qua counsel)
  - `docs/legal/register.md`, `docs/ops/incident-response.md`, `apps/AA-Booking/docs/ui-spec.md` (Q22)
  - `.github/workflows/delivery-metrics.yml`, `.github/workflows/docs-sync.yml` (pattern collector, phạm vi `sync --delete`)
  - `apps/AA-CIS-App/api/routers/admin_platform_delivery.py`
  - `infra/AA-CIS-Infra/accounts/aa365/cicd_split.tf` (role `tf_plan`: ReadOnlyAccess, trust PR + main)
  - `infra/AA-CIS-Infra/accounts/aa365/docs_reader.tf` (role Docs sync: trust mọi workflow trên master, Put/Delete `docs-reader/*`, noncurrent hết hạn 7 ngày)
  - `docs/security/baseline.md` (cũ ở mục Trivy/CodeQL)
  - `docs/backlog/tracker/plan.json` (AA-1162…AA-1168)

---

## 8. Kết quả quyết định (tech lead, 21/11/2026, trang quyết định S287)

15/17 câu theo đề xuất. Hai câu khác đề xuất:

- **Q13:** chưa cần người ký thứ hai cho review / exception lúc này (một tech lead).
- **Q14:** PDPL và GDPR **chưa** vào phạm vi chấm cho tới khi có pilot. Lý do của tech lead: dữ liệu đặt ở Mỹ và thị trường chính không phải Việt Nam.

Q4 (ghi chú "sao không làm full"): register liệt kê **đủ mọi yêu cầu** của từng khung trong phạm vi và map mỗi yêu cầu vào một
control chung. Con số ~40 là số control (việc mình làm và chứng minh), không phải cắt bớt phạm vi. Một control (ví dụ "MFA cho admin")
thoả nhiều yêu cầu ở nhiều khung cùng lúc, nên % đáp ứng vẫn tính trên toàn bộ yêu cầu của khung.

Issue triển khai: AA-1170 (pha 1–2), cùng project với AA-1166. Trang quyết định: https://claude.ai/artifact/MxZVVsNbcmjo31DBz8n2fQ.

**Cập nhật cuối phiên S287 (21/11, tech lead):**

- **Q14 đổi:** luật dữ liệu cá nhân VN (Luật 91/2025/QH15 + Nghị định 356/2025/NĐ-CP) và GDPR vào trang **ngay ở S288**, dạng checklist
  nghĩa vụ có cờ "cần luật sư xem". Các luật quốc tế khác (UK GDPR, Privacy Act của Úc, luật bang Mỹ theo ngưỡng, luật chống
  spam cho chiến dịch e-mail, Luật Dữ liệu 60/2024 và quy định lưu trữ trong nước, PCI DSS khi có thanh toán thẻ) chỉ vào sau
  bước bản đồ áp dụng theo thị trường, mỗi kết luận có nguồn chính thức → AA-1174.
- Pha 2–3 (kho bằng chứng khoá ghi, GitHub App chỉ đọc, Prowler, DB checks, exception / risk / SoA, rà soát tháng) chưa có issue
  sau khi AA-1170 đóng → tạo AA-1173, xếp S289 sau bộ chính sách AA-1166 (S288).

