# Audit hệ sinh thái AA (AA-1109, S282)

Ngày 16/11/2026 · Môi trường Dev · Viết cho tech lead. Nhóm 2-3 dev cùng agent AI, chưa có prod, chưa có tenant trả tiền, mô hình chỉ B2B (ADR 0019). Thang 1-5: 1 ad hoc, 2 lặp lại được, 3 được định nghĩa, 4 được đo, 5 được tối ưu.

## 1. Tóm tắt điều hành

- Điểm chung **3,2 / 5** (mức 3 'Defined': quy trình được định nghĩa, nhiều chỗ đã đo). Vượt mức thường thấy ở nhóm 2-3 người; điểm yếu tập trung ở con người, nhà cung cấp và độ lệch tài liệu, không ở kỹ thuật lõi.
- Mạnh nhất: pipeline migration expand/contract có chốt an toàn, AI gateway một cửa với ledger từng lượt gọi, deploy fail closed + auto-rollback, bài học biến thành guard có test.
- Rủi ro số 1 là **bus factor = 1**: một người giữ mọi quyền và duyệt mọi thứ, trong khi giao hàng phụ thuộc gần như hoàn toàn vào agent AI.
- Nhà cung cấp AI mong manh: Bedrock chạy trên acc1 (tài khoản cá nhân, ngoài org), acc3 vẫn bị chặn, Claude dựa vào key tài trợ; Billing Transfer 01/12 đổi payer, role truy cập org phải bật trước 20/11.
- Hai cam kết chưa thành hiện thực: retention (67/137 dòng 'proposed', job TTL chính DRY RUN) và đo chất lượng nội dung AI (instrument v2-v5 no_go, cổng chỉ cảnh báo).
- Trước PII thật / tenant trả tiền còn thiếu: MFA bắt buộc cho staff, DPA ký, scrub PII trước AI cho CIS/tenant, diễn tập sự cố bảo mật, kênh cảnh báo thứ hai. Nên gom thành **một cổng go-live** có ngày.
- Tài liệu lệch thực tế ở nhiều nơi (LLM 'trên acc3', mô hình B2C cũ, 12/25 runbook chưa ghi lần thử): sửa một lượt và thêm lint cụm từ lỗi thời.
- Chi phí: acc2 dự báo 277,6/300 USD tháng 11 dù chưa có khách. Kế hoạch giữ cỡ startup: hầu hết hành động 0 USD, không thêm công cụ doanh nghiệp.

| Lĩnh vực | Điểm | Trước critic |
|---|---|---|
| Kiến trúc & dữ liệu | 3,5 | 3,6 |
| AI & LLMOps | 3,4 | 3,5 |
| Bảo mật & tuân thủ | 3,1 | 3,2 |
| Hạ tầng & FinOps | 3,3 | 3,2 |
| Giao hàng & vận hành | 3,2 | 3,5 |
| Sản phẩm, quy trình & tri thức | 3 | 3 |
| **Chung** | **3,2** | |

## 2. Bảng điểm theo lĩnh vực

### Kiến trúc, ranh giới, nền tảng dữ liệu, mở rộng và độ tin cậy: 3,5/5

Chuẩn so sánh: AWS Well-Architected (REL, PERF, COST); DAMA-DMBOK; Evolutionary Database Design; kế hoạch DM-1..DM-9, C1..C8

Trưởng thành hơn hẳn mức thường thấy ở nhóm 2-3 người: một registry sở hữu schema có CI kiểm, migration expand/contract tự động có chốt an toàn, tham chiếu schema sinh mỗi đêm, đã diễn tập PITR và khôi phục từng tenant. Chỗ yếu: retention chưa thực thi (67/137 dòng DM-7.1 còn 'proposed', job TTL chính vẫn DRY RUN) và cả 4 app dùng chung một RDS single-AZ 2 GB RAM, trong khi DB tăng từ 985 MB lên 2,2 GB trong khoảng 3,5 tuần.

| Mục con | Điểm | Chuẩn | Hiện trạng |
|---|---|---|---|
| Quyền sở hữu app/schema và ranh giới DB | 4 | DAMA-DMBOK Governance; WA REL03 | Mỗi schema có owner NOLOGIN và runtime role riêng; owners.yaml test chéo với runner, guard và isolation probe; CRM cô lập hai chiều; probe nightly xanh. Bằng chứng: `infra/AA-CIS-Infra/db/owners.yaml; docs/database/schema-ownership.md; db-isolation-probe.yml 15/11 success` |
| Contract giữa các app và coupling | 3 | WA REL03/REL05; ADR 0001/0002/0019 | Contract có version (docs/contracts) và contract-copy-guard, nhưng CIS là hub (tenant master, token exchange, AI gateway, catalog views) và cả 4 app chung một DB; chưa có degraded mode đã kiểm. Bằng chứng: `docs/contracts/; contract-copy-guard.yml; 03-scaling.md C3` |
| ADR và nguồn sự thật kiến trúc | 3 | Nygard ADR; ISO/IEC/IEEE 42010 | 22 ADR có CI kiểm đánh số. Trừ điểm (critic, mức chung cho tài liệu lệch): 0011a vẫn 'Proposed' dù đã chạy; 0009 d14 vẫn ghi acc3 là chính; CONTEXT.md CIS 5.194 dòng. Bằng chứng: `docs/adr/0011a dòng 3; docs/adr/0009 dòng 407; wc -l apps/*/CONTEXT.md` |
| Migration expand/contract và pipeline | 4 | Parallel Change (Fowler/Sadalage); DORA CFR | Copy byte-for-byte có guard, expand và contract auto-apply trên Dev khi bảng job rảnh, file destructive dừng để DRY RUN + snapshot, replay trên PG thật. Rủi ro ở tốc độ: 322 file trong 30 ngày. Bằng chứng: `docs/adr/0017a; db/{expand_check,replay_migrations,apply_pending}.py; migration-apply.yml 15-16/11` |
| Schema reference và drift | 4 | DAMA-DMBOK Metadata; DM-3.1 | db-schema-reference.md + ERD sinh từ catalog live mỗi đêm và sau mỗi apply, có drift verdict, PR tự merge khi sạch. 66 cột chưa gắn tag DM-6.1. Bằng chứng: `db-schema-reference.md dòng 3-12 (Verified 2026-11-16)` |
| Retention DM-7.1 và archive | 2,5 | DAMA-DMBOK Lifecycle; GDPR 5(1)(e) | 137 dòng, CI chặn bảng mới thiếu dòng, có DRY RUN và archive Parquet. Nhưng 67 dòng 'proposed'; retention_job vẫn DRY RUN (1.717 dòng quá hạn); TP outbox redact còn dry-run. Bằng chứng: `02-data-management.md §7; audits/2026-11-09-S273-c43-w46 §Retention` |
| Chất lượng dữ liệu và RLS | 3,5 | OWASP ASVS L2 V4/V8; DAMA DQ | 321 RLS policy, 0 vi phạm ngoài allowlist; allowlist còn 131 finding (36 bảng có tenant_id không RLS, 20 entry cũ). Freshness Probe (ENFORCE) đỏ 12-14/11, tự xanh 15/11. Bằng chứng: `db-schema-reference.md §RLS catalogue guard; db-freshness-probe.yml runs` |
| Sizing RDS, review query C4.3, capacity C8 | 4 | WA PERF + COST; C1.2/C2.2/C4.3/C8 | C4.3 chạy đều theo tuần, có ngân sách connection có CI chặn (121/135). Live 7 ngày: CPU TB 6,2%, FreeableMemory thấp nhất ~252 MB. pg_stat_statements bị đẩy ra nhiều (dealloc 9.122/tuần). Bằng chứng: `describe-db-instances + CloudWatch 7 ngày; audits S273 c43-w46; connection-budget.yml` |
| Job runner và deploy an toàn | 3,5 | WA REL05/REL08; ADR 0003/0003a | Một bảng job mỗi owner, guard chặn deploy khi có job/wave, migration chờ job rảnh. Game day rollback đạt S264. Load test chỉ có CRM (p95 264 ms). Bằng chứng: `docs/ops/job-kinds.md; audits/2026-11-05-S269-aa969-loadtest` |
| Backup, PITR, diễn tập khôi phục | 3 | WA REL09/REL13; C7.2b | PITR 14 ngày, 2 diễn tập PITR (~22 phút), khôi phục từng tenant CIS/TP/CRM. Hạ từ 4 xuống 3 (critic, thống nhất với Infra): single-AZ, 0 AWS Backup plan, 0 bản sao khác vùng. Bằng chứng: `describe-db-instances; backup list-backup-plans = 0; ops/drills/README.md; S279 restore-drill.json` |

Điểm mạnh:

- Một registry sở hữu schema, CI kiểm chéo với runner, guard và isolation probe.
- Pipeline migration expand/contract tự động có replay, chờ job rảnh, DRY RUN + snapshot cho file destructive.
- Tham chiếu schema và ERD sinh từ DB live, không phải đoán tên bảng/cột.
- Capacity có số và hành động: ngân sách connection, review query hằng tuần, báo cáo tháng.
- Đã diễn tập khôi phục thật: PITR 2 lần có RTO, khôi phục từng tenant, rollback game day.

### AI platform và LLMOps: 3,4/5

Chuẩn so sánh: AWS WA Generative AI Lens; NIST AI RMF 1.0; OWASP LLM Top 10 2025; EU AI Act Art. 50; FinOps Framework

Một gateway cho mọi lời gọi AI, route theo stage có version và revert, ledger ghi mọi lượt thử kể cả lượt bị từ chối, trần chi theo connection/app/tenant. Kỷ luật đo lường rất cao (pre-registration ghim sha, hold-out), nhưng chưa instrument nào đạt (v2-v5 no_go) nên cổng chất lượng chỉ cảnh báo. Rủi ro lớn nhất là nhà cung cấp: acc3 bị chặn, Bedrock chạy trên acc1 cá nhân, Claude dựa vào key tài trợ, 01/12 đổi payer.

| Mục con | Điểm | Chuẩn | Hiện trạng |
|---|---|---|---|
| AI gateway: routing, fallback, route control | 4 | WA GenAI Lens + REL10/REL12; ADR 0009 d5/d7 | Route theo stage, tối đa 6 lượt thử, route control có preview, kiểm luật, version, revert, audit; probe hằng ngày. Thiếu: diễn tập failover hằng tháng (đã duyệt, chưa lên lịch); TripPlanner chỉ gọi Bedrock. Bằng chứng: `docs/architecture/ai-gateway.md §4, §8; ADR 0009 d5, d7` |
| Cost ledger, phân bổ và trần chi | 4 | FinOps Framework; WA COST; ADR 0009 d6/d8 | Một dòng mỗi lượt thử (app, stage, tenant, route/prompt version); reconcile hằng đêm; báo cáo phiên ra USD. Điểm yếu: hard stop chỉ có trong gateway CIS; crm.llm_call không tính vào trần connection. Bằng chứng: `ai-gateway.md §5-6; ADR 0009 amendment S267 'Keys and caps'; CIS migration 406` |
| Cổng chất lượng, eval, hiệu chuẩn | 3 | NIST AI RMF MEASURE 2.x; ADR 0020 | Golden set đóng băng, pre-registration ghim sha256, hold-out. Kết quả: v2-v5 no_go, judge kappa 0,562 trên 13 cặp, cổng chỉ cảnh báo. eval-regression chỉ chạy tay (quyết định có chủ đích AA-289, cần duyệt chi phí), lần cuối 01/08. Bằng chứng: `CIS docs/calibration/aa1048-two-step-v6-preregistration.md; ai-use-register.md LLM09; eval-regression.yml dòng 1-6` |
| Quản lý prompt và version | 3,5 | NIST AI RMF MANAGE 2; OWASP LLM03 | prompt_versions.json có sha256 và test CI fail khi lệch; ledger ghi prompt_version/hash. Luật 'đổi prompt/route phải có eval run ID' mới là quy ước. Bằng chứng: `CIS docs/llm/prompt-register.md; tests/unit/test_aa900_prompt_registry_gate.py` |
| Rủi ro nhà cung cấp và miền lỗi | 2,5 | WA REL10; NIST AI RMF GOVERN 6 | acc3 bị chặn từ 29/10; Bedrock chat chạy trên acc1 (tài khoản cá nhân, ngoài org). Claude: Anthropic API (key tài trợ) rồi acc1 rồi acc3; GPT: acc1 rồi OpenAI. Writer chỉ còn hai miền lỗi; 01/12 đổi payer; chưa diễn tập failover. Bằng chứng: `docs/sessions/2026-11-12-S278-*.md; dpa-annex-3-subprocessors.md v0.5; ADR 0009 d14` |
| Lọc PII và data scope trước AI | 3 | OWASP LLM02; ASVS L2 V8; DM-6.4 | CRM có scrub F3 chặn khi lỗi; chat TripPlanner có regex email/phone; data scope có test. CIS và nội dung tenant chưa scrub tự động; từ CIS 366 mọi stage text đi ra API vendor; pii_class chưa build. Bằng chứng: `ADR 0009 d5 amendment S267, d10 Proposed; TP backend/shared/scrub.py` |
| AI register và notice (EU AI Act Art. 50) | 4 | EU AI Act Art. 50; NIST AI RMF GOVERN 1/MAP 1 | AI Use Register v1.13 mỗi stage một dòng, bản đồ OWASP LLM Top 10; kit AiNotice và mark máy đọc được theo kênh. Ngày áp dụng Art. 50(2) chưa đối chiếu văn bản chính thức. Bằng chứng: `docs/architecture/ai-use-register.md; ADR 0019 d19` |
| Observability và độ mới tài liệu AI | 3 | WA OPS 8; ITIL-lite CMDB | Tab Guide admin đọc bảng live, trace drawer, bell + e-mail khi circuit mở. Tài liệu tĩnh lệch: ai-gateway.md (05/11) và snapshot route (09/11) trước v10/v11. Hạ xuống 3 (critic, mức chung cho tài liệu lệch). Bằng chứng: `ai-gateway.md header; docs/generated/llm-routes.md; ADR 0009 d14` |

Điểm mạnh:

- Một gateway cho mọi lời gọi AI trả phí, test CI chặn gọi SDK vendor trực tiếp; không thêm service.
- Ledger một dòng mỗi lượt thử, chi phí quy được theo sản phẩm và tenant.
- Route control đổi trong ~20 giây không cần deploy, rollback chỉ là đổi dữ liệu.
- Kết quả no_go được báo đúng, không nới ngưỡng; chi phí lần chạy khớp ledger.
- Không stage nào cho model quyền gọi tool (LLM06).

### Bảo mật, danh tính và tuân thủ: 3,1/5

Chuẩn so sánh: OWASP ASVS 4.0.3 L2 / Top 10; CIS AWS Foundations v3; NIST CSF 2.0; NIST SP 800-61r3; PDPL (Luật 91/2025) + NĐ 356/2025

Cô lập tenant có kiểm tự động, CRM mã hoá PII theo từng đại lý, quét secret toàn lịch sử ở 6 repo public, saga xoá dữ liệu đã chạy thật. Điểm yếu lớn nhất: staff (kể cả admin) đăng nhập một yếu tố (mã e-mail). Bộ pháp lý đầy đủ nhưng vẫn là bản nháp. Chưa có diễn tập bảo mật nào. Theo critic: PII protection hạ còn 3 khi tính cả hệ (retention và scrub trước AI chưa có), access governance hạ còn 2,5 vì một người giữ mọi quyền.

| Mục con | Điểm | Chuẩn | Hiện trạng |
|---|---|---|---|
| Danh tính staff, phiên và MFA | 2 | ASVS L2 V2; CIS AWS 'MFA for privileged users'; ADR 0006 | Pool WORKFORCE MFA=OPTIONAL, không Google IdP, đăng nhập bằng EMAIL_OTP (một yếu tố); 12 user; chỉ break-glass có TOTP. Bằng chứng: `live 16/11: get-user-pool-mfa-config = OPTIONAL; list-identity-providers = 0; ADR 0006 §4` |
| Danh tính tenant / partner / M2M | 4 | ASVS L2 V2/V3; ADR 0006b | Pool partner MFA bắt buộc, admin-only create, deletion protection; pool M2M riêng; đã bỏ đăng nhập bằng API key tenant; assertion TP xoay khoá, khoá cũ bị từ chối live. Bằng chứng: `live: partner pool MFA=ON; ADR 0006b; AA-1092 export` |
| Phân quyền và cô lập tenant | 4 | OWASP A01 / ASVS V4; DM-8.4 | Mỗi app một role, 321 RLS policy, probe cô lập nightly + chặn sau auto-apply, phủ crm_app; xanh 16/11. B2B API Booking đã bind tenant. Bằng chứng: `db-isolation-probe.yml; db/isolation_probe.py; S268 crm-security-review` |
| Quản lý và xoay secret | 3 | WA SEC02/SEC08; DM-8.6/8.9 | 56 secret, đều đổi trong 90 ngày; role CI apply bị Deny đọc secret không cần. Không xoay tự động (theo quyết định); runbook xoay secret và xoay khoá CRM chưa chạy thử. Bằng chứng: `live list-secrets (metadata); accounts/aa365/cicd_split.tf; runbooks secret-rotation.md, crm-keys.md last_tested null` |
| Bảo vệ PII và mã hoá | 3 | ASVS L2 V6/V8; PDPL + NĐ 356 | CRM: DEK theo đại lý qua KMS, blind index, crypto-shred, lint chặn *_enc. Saga xoá đã chạy 2 lần qua 4 app. Hạ từ 4 xuống 3 (critic): retention log/PII chưa thực thi, CIS/tenant chưa scrub trước AI. Bằng chứng: `apps/AA-Partner/CONTEXT.md (vault); S281 AA-1093; 02-data-management.md §7` |
| An toàn repo public và chuỗi cung ứng | 3,5 | OWASP A06/A08; OpenSSF Scorecard; ADR 0021 | gitleaks PR + toàn lịch sử ở 6 repo, push protection, 0 alert secret mở, 5 Dependabot medium. Hở: AA-Partner chưa bật CodeQL; CIS 2 alert high ReDoS trên input domain tenant. Repo gốc public chứa ID ALB/TG trong alarms.md. Bằng chứng: `gh api code-scanning default-setup (Partner = not-configured); docs/generated/alarms.md` |
| Phát hiện, log và audit trail | 3 | CIS AWS v3 §3-4; WA SEC04; NIST CSF DE | CloudTrail đa region, KMS, Object Lock; Access Analyzer 0 finding; cảnh báo root/IAM/SG/phiên admin; bảng audit append-only. GuardDuty và Security Hub tắt theo quyết định chi phí. Bằng chứng: `live: guardduty list-detectors rỗng; accessanalyzer ACTIVE = 0; docs/security/baseline.md` |
| Rà quyền và quản trị bảo mật | 2,5 | ISO 27001 A.5.18; CIS Controls v8 #5-6 | Rà quyền một lần (20/10, 4 user staff); nay 12 user. F-15 (IAM user/access key live) chưa có bản ghi. Baseline lệch thực tế. Hạ xuống 2,5 (critic): một người giữ mọi quyền. Bằng chứng: `audits/2026-10-20-S245-access-review; baseline.md last_reviewed 2026-11-01` |
| Sẵn sàng pháp lý | 3 | PDPL; GDPR Art. 28/33; EU AI Act Art. 50 | DPA v0.4 + 4 phụ lục, hồ sơ chuyển dữ liệu, AI Schedule; saga xoá chứng minh live. 11 file docs/legal vẫn 'draft'; chưa quyết luật sư rà; điều khoản Anthropic/OpenAI '[To confirm]'. Bằng chứng: `grep '^status:' docs/legal/*.md; readiness-packet.md` |
| Ứng phó sự cố và diễn tập bảo mật | 2,5 | NIST SP 800-61r3; ITIL-lite | Runbook có nhánh vi phạm dữ liệu 24h/72h, 5 playbook, 1 postmortem. Chưa tabletop, break-glass qua managed login chưa thử, chưa pentest/DAST. Bằng chứng: `docs/ops/incident-response.md; ops/drills/README.md 'Not drilled yet'` |

Điểm mạnh:

- Cô lập tenant kiểm tự động mỗi đêm, phủ cả 4 app.
- CRM mã hoá PII theo từng đại lý, có crypto-shred.
- Saga xoá dữ liệu chạy thật 2 lần qua 4 app.
- Repo public: gitleaks toàn lịch sử, push protection, lint resource-ID.
- CI chỉ tin main qua OIDC, role apply bị Deny đọc secret, subagent bị hook chặn ghi IAM/push/merge.

### Hạ tầng và FinOps: 3,3/5

Chuẩn so sánh: AWS Well-Architected (OPS05, REL09/10/13, COST01-07); CIS AWS Foundations; FinOps Foundation Framework; ADR 0018

Gần như toàn bộ acc2 nằm trong Terraform (813 tài nguyên), drift nightly xanh 7 đêm, cổng tag trong CI. FinOps bài bản: budget account/app/org, Cost Anomaly, trần AI trong DB, báo cáo tháng có công cụ, chi phí đơn vị. Điểm yếu: acc2 dự báo 277,6/300 USD dù chưa có khách; acc1 cá nhân phục vụ toàn bộ Bedrock; Billing Transfer 01/12 còn bước chưa xong (role truy cập org trước 20/11). DR nâng từ 2,5 lên 3 (critic, thống nhất với Kiến trúc).

| Mục con | Điểm | Chuẩn | Hiện trạng |
|---|---|---|---|
| Độ phủ Terraform và drift | 4 | WA OPS05; ADR 0018 d5 | Plan trên mọi PR, apply chỉ khi dispatch, drift nightly cho aa365 + management xanh 09-15/11. Thiếu: root acc1/acc3 apply tay ngoài drift CI; aa365 và acc3 chưa đặt allowed_account_ids. Bằng chứng: `terraform-drift.yml; audits/2026-10-28-S256-aa697-drift; accounts/aa365/versions.tf` |
| Cấu hình ECS/RDS/S3/Lambda/CloudFront/WAF | 3,5 | WA SEC + REL; CIS AWS Foundations | 8 service ECS (Fargate + Spot), RDS mã hoá + deletion protection + PITR 14 ngày, 15/17 bucket có versioning, WAF trên ALB và Cognito. Bằng chứng: `đọc live 16/11 (describe-*, list-*)` |
| Mạng | 3 | WA REL10/COST07 | Một VPC 2 AZ, NAT instance t4g.nano (rẻ, có auto-recover, nhưng là điểm lỗi đơn), chỉ S3 gateway endpoint. 449 GB traffic liên AZ tháng 10 chưa rõ nguồn. Bằng chứng: `describe-instances; describe-vpc-endpoints; audits/2026-11-03-S265-capacity-review` |
| Mô hình tài khoản và Billing Transfer 01/12 | 3 | AWS multi-account best practice; ADR 0018 | Org acc4 đã có OU, 3 SCP, Identity Center, org trail. Còn mở: role truy cập org trong acc2 vẫn tắt (hạn trước 20/11); xuất lịch sử Cost Explorer 25-28/11. acc1 cá nhân đứng ngoài org. Bằng chứng: `accounts/aa365/terraform.tfvars (org_access_role_enabled = false); plan.json checks AA-1004` |
| Tag và phân bổ chi phí | 3 | FinOps Allocation; WA COST03 | Chuẩn tag FIN-03 + cổng plan; chỉ tag App được kích hoạt; tháng 10 khoảng 50% chi phí acc2 chưa gán app. Bằng chứng: `docs/ops/finops.md §Tags; S265 'Not assigned'` |
| Ngân sách và cảnh báo | 4 | WA COST02/03; FinOps Anomaly | Budget tổng 300 USD, 6 budget theo App, Cost Anomaly ≥ 5 USD, budget org/account ở acc4, trần AI trong DB + đối soát. Budget acc1 chỉ cảnh báo, không có đường đọc Cost Explorer. Bằng chứng: `accounts/aa365/cost_anomaly.tf; accounts/management/budgets.tf; describe-budgets 16/11` |
| Xu hướng chi phí và chi phí đơn vị | 3 | FinOps Unit Economics; WA COST01 | Chi phí đơn vị: 0,34 USD/tour xuất bản, 0,61 USD/booking. acc2 tăng 140 → 135 → 214 → dự báo ~278 USD theo số service luôn bật, không theo người dùng. Bằng chứng: `S265 capacity review; describe-budgets 16/11 (actual 130,89; forecast 277,63)` |
| Chiến lược môi trường | 3 | ADR 0018 d2/d3/d5 | Chỉ có Dev; modules/environment đã nhận Booking/CRM/TP/staff web (plan no-op), lõi CIS vẫn ở root; deploy-prod.yml là khung có guard. Ước tính prod 280-410 USD/tháng. Bằng chứng: `accounts/aa365/environment.tf; deploy-prod.yml header; ADR 0018` |
| Tư thế DR | 3 | WA REL09/REL13; C7.2b (RPO ≤ 15 phút, RTO ≤ 1 giờ) | Mức Dev đủ: PITR 14 ngày, 54 snapshot thủ công tự hết hạn, 3 lần restore thật. Chưa có: Multi-AZ, bản sao us-west-2, AWS Backup plan; state Terraform nằm trong chính acc2. Bằng chứng: `describe-db-snapshots (us-west-2 = 0); backup list-backup-plans rỗng; 03-scaling.md C7.2b` |

Điểm mạnh:

- 813 tài nguyên trong Terraform, drift nightly, CI chỉ đọc qua OIDC.
- Guard chi phí nhiều lớp, đều miễn phí.
- Báo cáo tháng có công cụ, giải thích mọi bước nhảy theo usage type.
- Mô hình tài khoản gọn theo ADR 0018, mở rộng theo trigger chứ không theo ngày.
- Billing Transfer có lịch theo ngày và đường lui (OU Transitional).

### Giao hàng và vận hành (CI/CD, DORA, test, observability, vận hành, guard): 3,2/5

Chuẩn so sánh: DORA four keys (State of DevOps 2024); AWS WA OPS06/07/08/10/11; Google SRE; OpenSSF Scorecard

CI/CD vượt mức thường thấy: merge queue + required checks ở 3 repo app chính, image immutable, cổng schema/job khi deploy, auto-rollback ECS. 30 ngày: ~2.800 PR, trung vị mở → merge 0,04-0,37 giờ, 1 revert. Nhưng chưa đo tỷ lệ thay đổi gây lỗi và thời gian khôi phục; runbook lệch thực tế (12/25 last_tested null); một người trực, một kênh cảnh báo; integration nightly flaky. Điểm area hạ từ 3,5 xuống 3,2 = trung bình các mục con.

| Mục con | Điểm | Chuẩn | Hiện trạng |
|---|---|---|---|
| CI pipeline và kiểm soát merge | 4 | DORA CI; OpenSSF Scorecard | Merge queue (CIS, Booking, Partner), required checks strict, chặn force-push, pre-push ở 6 repo, action ghim SHA. Hở: TripPlanner strict=false, không merge queue; enforce_admins=false. Bằng chứng: `gh api branch protection 16/11; .githooks/pre-push; tools/github/pin_freshness.py` |
| Deploy an toàn | 4 | WA OPS06/REL08 | ECR immutable, schema-gate + job/wave guard fail closed, post-deploy verify git_sha/schema, circuit breaker rollback mọi service; /health/ready CIS và Booking 200 ngày 16/11. Hở: smoke web đỏ vẫn để bản lỗi chạy. Bằng chứng: `deploy-dev.yml; post-deploy-verify.yml; modules/ecs/main.tf deployment_circuit_breaker` |
| Luồng kiểu DORA | 3 | DORA four keys | Throughput mức elite (710 PR CIS, CIS deploy 370/400 thành công, phần đỏ chủ yếu là cổng có chủ đích). Chưa đo CFR và MTTR (hoãn tới prod); commit 'fix:' ~23-28%. Bằng chứng: `gh pr list merged 30 ngày; gh run list deploy-dev.yml; engineering-handbook.md:418,862` |
| Chiến lược test và coverage | 3 | Test pyramid; DORA test automation; NIST AI RMF MEASURE | CIS ratchet coverage 85%, Booking/Partner sàn 90%, contract/visual/smoke test. Hở: TripPlanner không ngưỡng coverage; nightly integration random-order đỏ 5/11 đêm (không liên tiếp, có run xanh 14/11 xen giữa); eval-regression chỉ chạy tay (quyết định AA-289). Bằng chứng: `coverage-ratchet.json; nightly-integration.yml runs; issue nightly-red mở 15/11` |
| Observability | 3 | WA OPS08/REL06; SRE golden signals | 31 alarm + 15 rule EventBridge sinh từ Terraform, 100% có runbook, 0 alarm đang ALARM. Sentry free ở 3 app. Hở: một kênh cảnh báo (SNS e-mail), chưa có tracing xuyên app, SLO chỉ có ở CRM. Bằng chứng: `docs/generated/alarms.md; tools/docs/check_alarm_runbooks.py; describe-alarms 16/11` |
| Vận hành: runbook, drill, sự cố, người trực | 2,5 | ITIL-lite; WA OPS07/OPS10/OPS11 | 25 runbook, 5 playbook, drill thật (PITR, game day D1-D5, restore tenant). Nhưng 12/25 runbook last_tested null kể cả 3 runbook rollback đã qua game day; playbook llm-access-denied không nhắc acc1; ops README ghi LLM chạy trên acc3; một người trực. Bằng chứng: `docs/ops/README.md:17; playbooks/llm-access-denied.md; runbooks/rollback-ecs.md:12; incident-response.md:17` |
| Guard mã hoá bài học | 4 | SRE blameless postmortem actions; S271 | Hook có test (shell guard, subagent guard, lane start, pilot PII, stop-open-work, kit-core), ship tool có test, check_lessons.py. lessons.md: 367 dòng bullet (495 dòng tổng), 128 có 'Guard:', 67 'Guard: none'. Bằng chứng: `/.claude/hooks/test_*; tools/github/test_ship_*.py; docs/audits/2026-11-07-S271-lessons-to-guards` |
| Release và truy vết | 2 | SemVer + Conventional Commits; DORA | release-please cài ở 4 app nhưng PR release mở từ 30/10, /health vẫn 0.18.0. Truy vết dựa vào git_sha (tốt). Bằng chứng: `PR CIS #1179, Booking #161, Partner #133, TP #196; curl /health` |

Điểm mạnh:

- Merge queue + required checks strict, trung vị mở → merge dưới 25 phút, 1 revert / ~2.800 PR.
- Deploy fail closed, verify sau deploy, auto-rollback ECS.
- Health contract giàu thông tin, live khớp commit.
- 46 cảnh báo sinh từ Terraform, 100% có runbook.
- Bài học thành guard có test; bot tự mở issue khi CI đêm đỏ.

### Sản phẩm, quy trình và tri thức: 3/5

Chuẩn so sánh: ADR 0019 + plan.json; AWS SaaS Lens; Kanban/DORA; Diátaxis; ISO 22301; ISTQB/ITIL 4 service validation

Sản phẩm đi xa so với ADR 0019: R0-R3, R6 xong, R4 còn bước xoá bảng B2C, R5 (TripPlanner đa tenant) đã live dù tracker ghi 'later'; CRM bù gần hết khoảng trống so với plugin Odoo. Diễn tập pilot 13 bước PASS có video, báo cáo tuần đều. Điểm yếu lớn nhất: bus factor = 1 (một danh tính người commit ở các repo kiểm được trong 30 ngày). Tracker và trang vào cửa lệch thực tế; chưa có ngày go-live, prod chưa bắt đầu.

| Mục con | Điểm | Chuẩn | Hiện trạng |
|---|---|---|---|
| Độ đầy đủ sản phẩm so với ADR 0019 | 3 | ADR 0019 R0-R8; AWS SaaS Lens | R0-R3, R6 xong; R4 5/6 tiêu chí; R5 live; R7, R8, M5 chưa. 118 tính năng trong catalogue, 115 'live'. Chưa có nhúng iframe/widget (CSP frame-ancestors 'none'). Bằng chứng: `docs/adr/0019; plan.json milestones; apps/AA-TripPlanner-Web/CONTEXT.md; docs/catalogue/features.yaml` |
| Sẵn sàng pilot | 3 | ISTQB acceptance; ITIL 4 transition | Diễn tập 13 bước PASS, diễn tập xoá và khôi phục tenant. Hổng: Laos 45 tour / 0 có giá, tour thiếu ảnh; runbook pilot-rehearsal ghi UNTESTED; chưa có ngày go-live. Bằng chứng: `audits/2026-11-13-S279-session/uat-rehearsal/README.md; plan.json M5` |
| Backlog và kỷ luật WIP | 3 | Kanban WIP; DORA small batches | WIP 8 được giữ, Linear 38/250. Tiêu chí milestone sửa tay nên lệch (M-P2 'later' dù R5 live; M-OD 'next' dù đã xong); milestone không có ngày. Bằng chứng: `Linear list_issues; plan-sync.yml; docs/backlog/README.md L170-171` |
| Vận hành agent | 4 | NIST AI RMF Govern/Manage; DORA CD | Nghi thức phiên + state-snapshot, hook có test, 10 skill, merge qua App + merge queue. Rủi ro: nhịp 27 phiên / 19 ngày dồn lên một người duyệt; agent chạy bằng role admin của người. Bằng chứng: `/.claude/hooks/; skill/; docs/sessions S255-S281` |
| Chất lượng và độ mới tài liệu | 3 | Diátaxis; DORA documentation | Catalog theo vai trò, front-matter, lint xanh, 67 cặp .vi.md. Nhưng trang vào cửa vẫn tả B2C cũ và LLM trên acc3; lint chỉ kiểm hạn, không kiểm nội dung. Bằng chứng: `docs/README.md:17-19; docs/llms.txt:3; docs/guides/new-engineer.md` |
| AA Academy và kit dự án mới | 2 | DORA learning culture; Kirkpatrick 1-2 | Nền tảng đủ theo ADR 0022, nội dung 1 module (F3), 5 module 'planned'; kit phần 2 đang làm. Bằng chứng: `docs/learn/paths/fundamentals.yaml; docs/playbook/` |
| Báo cáo cho bên liên quan | 4 | PRINCE2 highlight report | Báo cáo tuần PR-20 đều 5 kỳ, epic theo app, mọi bản nháp được duyệt trước khi đăng. Chưa có RAG/ngày dự báo. Bằng chứng: `docs/audits/2026-11-15-S281-session/jira-drafts.md` |
| UAT và bằng chứng | 4 | ISTQB acceptance; ITIL 4 validation | Mỗi issue Done có thư mục verify và state-snapshot; video UAT EN/VI. Vòng UAT với người dùng nghiệp vụ (AA-855) chưa bắt đầu. Bằng chứng: `docs/audits/2026-11-15-S281-session/verify/` |
| Bus factor và người chủ chốt | 1 | ISO 22301; CIS Controls v8 #5/#6 | Một danh tính người commit trong 30 ngày (Booking chưa kiểm được); GitHub org, AWS management/root, tên miền, break-glass và mọi phê duyệt ở một người. Đề xuất BO-5 (S261) chưa có issue. Bằng chứng: `git log --since=2026-10-16 theo repo; audits S261 A3/BO-5; plan.json M5 risk` |

Điểm mạnh:

- ADR 0019 thực hiện nhanh, có bằng chứng; TP đa tenant chạy với FORCE RLS.
- CRM đóng khoảng trống chính so với plugin Odoo; add-on bật theo feature key.
- Diễn tập pilot 13 bước có video EN/VI.
- WIP tối đa 8, quota Linear giữ chủ động.
- Báo cáo tuần đều, luôn duyệt trước khi đăng.

## 3. Rủi ro xếp hạng

Điểm = tác động × khả năng (Cao 3, Trung bình 2, Thấp 1). Effort: S dưới 1 ngày, M vài ngày, L một sprint trở lên.

01. **R01** (Sản phẩm, Bảo mật, Giao hàng; tác động cao, khả năng cao, điểm 9, effort M) Bus factor = 1: một người giữ mọi quyền (GitHub org, AWS management/root, tên miền, break-glass) và là người duyệt duy nhất; vắng người này thì hệ đứng.
   Hành động: Chỉ định người giữ quyền thứ hai (GitHub owner, Identity Center acc4, registrar) bằng passkey, niêm phong break-glass, trang in 'giữ hệ thống chạy'; tạo issue BO-5; trước go-live một kỹ sư diễn tập deploy + rollback chỉ bằng runbook.
   Bằng chứng: `git log 30 ngày theo repo; audits S261 A3/BO-5; plan.json M5`
02. **R02** (Kiến trúc, Bảo mật; tác động cao, khả năng cao, điểm 9, effort M) Retention chưa thực thi: 67/137 dòng DM-7.1 'proposed', job TTL chính (shared.job, llm_call_log, tenant_api_usage, TP outbox redact) vẫn DRY RUN; log/PII tích luỹ, trái cam kết xoá trong DPA.
   Hành động: Một buổi duyệt theo nhóm (cấu hình 'kept'; log/ledger theo cửa sổ 30/90/180 ngày), rồi chạy live lần đầu mỗi kind với max_rows lấy từ DRY RUN.
   Bằng chứng: `02-data-management.md §7; audits S273 c43-w46 §Retention; retention_job.py`
03. **R03** (AI, Giao hàng; tác động cao, khả năng cao, điểm 9, effort M) Chất lượng nội dung AI chưa đo đạt: instrument v2-v5 no_go, judge chưa hiệu chuẩn, cổng chỉ cảnh báo; eval-regression chạy tay, lần cuối 01/08 (quyết định AA-289). Vòng v2-v6 trên cùng 21 vi phạm TP có nguy cơ overfit.
   Hành động: Time-box AA-1048: v6 là lượt cuối trên pool này; go thì xác nhận trên tập TP mới, no_go thì giữ v1 warn và chuyển sang kiểm bằng code. Xin duyệt chi phí cho golden subset 3-10 mẫu chạy hằng tuần, ghi ledger, có trần.
   Bằng chứng: `aa1048-two-step-v6-preregistration.md; ai-use-register.md LLM09; eval-regression.yml dòng 1-6`
04. **R04** (Kiến trúc, Hạ tầng; tác động cao, khả năng trung bình, điểm 6, effort L) Một RDS single-AZ db.t4g.small (2 GB) cho cả 4 app, DR một vùng: không AWS Backup, không bản sao khác vùng, state Terraform trong acc2. DB tăng 985 MB → 2,2 GB trong ~3,5 tuần, FreeableMemory thấp nhất ~252 MB.
   Hành động: Dev: thêm FreeableMemory + tăng trưởng DB vào C4.3, xử lý theo thứ tự C3b (retention trước, lên t4g.medium sau). Trước tenant trả tiền: dựng prod đúng C7.2 (Multi-AZ, PITR 14 ngày, AWS Backup cross-region, diễn tập có đo RTO). Pilot dữ liệu thật: báo giá backup replication sang us-west-2.
   Bằng chứng: `describe-db-instances; CloudWatch 7 ngày; backup list-backup-plans = 0; 03-scaling.md C7.2`
05. **R05** (AI, Bảo mật, Hạ tầng; tác động cao, khả năng trung bình, điểm 6, effort M) Bedrock LLM chạy trên acc1 (tài khoản cá nhân của tech lead, ngoài org), acc3 vẫn bị chặn, Claude dựa vào key Anthropic tài trợ. Writer gọi Anthropic API trước (acc1 là dự phòng cho writer, là đường đầu cho stage GPT). Rủi ro hợp đồng, hoá đơn, bàn giao và miền lỗi.
   Hành động: Viết 1 trang kế hoạch thoát acc1 (điều kiện chuyển sang tài khoản AI thuộc org công ty, việc gì khi key tài trợ hết); quyết định tại buổi rà đầu tháng 12; ghi ngoại lệ có hạn trong DPA và cho luật sư xác nhận trước PII thật.
   Bằng chứng: `dpa-annex-3-subprocessors.md dòng 39, 80; ADR 0001a Note S278; finops.md 'Where the money is'`
06. **R06** (Hạ tầng, AI; tác động cao, khả năng trung bình, điểm 6, effort M) Billing Transfer 01/12 đổi payer và org: có thể mất lịch sử chi phí, đổi quyền model Bedrock trên acc2 (Cohere Embed, Guardrail, Nova Lite); tag phải bật lại ở acc4.
   Hành động: 25-28/11 xuất Cost Explorer 13 tháng; ngay trước và sau 01/12 chạy probe LLM toàn bộ connection + một lời gọi embed; sau chuyển bật lại tag ở acc4 và so tổng tháng 11.
   Bằng chứng: `plan.json AA-1004; docs/backlog/README.md dòng 53; finops.md §Tags`
07. **R07** (Hạ tầng; tác động cao, khả năng trung bình, điểm 6, effort S) Role truy cập org (OrganizationAccountAccessRole) trong acc2 vẫn tắt, hạn trước 20/11; trễ thì acc4 không có đường quản trị vào acc2 sau khi chuyển.
   Hành động: Tech lead apply targeted có MFA, merge PR một dòng bật biến, thử assume từ acc4 trước 20/11; chỉ gỡ role SSO của reseller sau khi thử thành công.
   Bằng chứng: `accounts/aa365/terraform.tfvars (org_access_role_enabled = false); org_access.tf`
08. **R08** (Bảo mật; tác động cao, khả năng trung bình, điểm 6, effort M) Staff, kể cả admin xem được dữ liệu mọi tenant, đăng nhập một yếu tố (mã e-mail): pool WORKFORCE MFA=OPTIONAL, không Google IdP.
   Hành động: Trước pilot có PII thật: password + TOTP bắt buộc cho nhóm admin (0 USD) hoặc Google IdP + 2SV bắt buộc; ghi amendment ADR 0006.
   Bằng chứng: `live 16/11 get-user-pool-mfa-config = OPTIONAL; ADR 0006 §4`
09. **R09** (Sản phẩm, Liên lĩnh vực; tác động cao, khả năng trung bình, điểm 6, effort M) Không có một cổng go-live duy nhất: điều kiện trước đại lý thật (MFA staff, DPA ký, prod C7.2, kênh cảnh báo 2, scrub PII, rate limit, retention, runbook đã thử) rải ở nhiều nơi; chưa có ngày go-live, M5 chưa bắt đầu, catalog pilot hổng (Laos 45 tour / 0 có giá); pilot Dev giới hạn 8 tuần.
   Hành động: Checklist go-live ~15 dòng gắn bằng chứng + issue làm tiêu chí M5, guard CI báo đỏ khi pilot thật bật mà còn dòng mở; đo độ phủ giá/ảnh cho 1-2 thị trường pilot; xin business owner một ngày go-live dự kiến; làm M5 P0 (0 USD).
   Bằng chứng: `plan.json:236-238, M5; ADR 0019 d16; uat-rehearsal README`
10. **R10** (Bảo mật, AI; tác động cao, khả năng trung bình, điểm 6, effort M) Bộ pháp lý (DPA, privacy, terms, hồ sơ PDPL) vẫn draft, chưa quyết luật sư rà; điều khoản Anthropic/OpenAI '[To confirm]'; ngày áp dụng Art. 50(2) chưa đối chiếu.
   Hành động: Cổng cứng 'không PII thật trước khi DPA ký'; một trang quyết định ngắn cho business owner (rà toàn bộ hay chỉ phụ lục 3-4); điền [To confirm] từ điều khoản công khai; đối chiếu Art. 113 trên EUR-Lex.
   Bằng chứng: `grep '^status:' docs/legal/*.md; readiness-packet.md; ADR 0019 dòng 232`
11. **R11** (AI, Bảo mật; tác động cao, khả năng trung bình, điểm 6, effort M) Từ CIS 366 mọi stage text (gồm tenant, tp_*) đi ra API vendor; CIS và tenant chưa scrub PII tự động, pii_class chưa build, quyết định 10 vẫn Proposed.
   Hành động: Đưa scrub F3 của CRM thành bước tuỳ chọn trong gateway chung cho stage có cờ free_text, chặn khi lỗi; chốt quyết định 10 trước tenant trả tiền.
   Bằng chứng: `ADR 0009 d5 amendment S267, d10; TP backend/shared/scrub.py`
12. **R12** (Giao hàng, Sản phẩm, Kiến trúc; tác động cao, khả năng trung bình, điểm 6, effort M) Runbook và playbook lệch thực tế: 12/25 runbook last_tested null (kể cả 3 rollback đã qua game day S264), playbook llm-access-denied không có acc1, ops README ghi LLM trên acc3, OPS-05 ghi backup 7 ngày (live 14), drill index thiếu S264/S279/S281.
   Hành động: Một root PR sửa playbook theo route v10/v11, ghi last_tested + bằng chứng game day, sửa OPS-05 và drill index; chạy thử 4 runbook quan trọng (rollback-ecs, rollback-terraform, secret-rotation, rollback-booking); guard: PR đổi route/ADR account đòi sửa playbook.
   Bằng chứng: `docs/ops/README.md:17; playbooks/llm-access-denied.md; runbooks/rollback-ecs.md:12; database-operations.md §Facts`
13. **R13** (Bảo mật; tác động cao, khả năng trung bình, điểm 6, effort S) Ứng phó sự cố bảo mật chưa diễn tập: chưa tabletop, break-glass qua managed login chưa thử, chưa xoay secret/khoá CRM lần nào; hạn báo 24h/72h sẽ làm lần đầu dưới áp lực.
   Hành động: Tabletop 60 phút, 2 kịch bản (secret lộ trên repo public; đại lý A đọc được dữ liệu B); xoay thật một secret ít rủi ro, xoay DEK trên đại lý tổng hợp, thử break-glass. 0 USD.
   Bằng chứng: `ops/drills/README.md 'Not drilled yet'; runbooks secret-rotation.md, crm-keys.md last_tested null`
14. **R14** (Giao hàng; tác động cao, khả năng trung bình, điểm 6, effort S) Một người trực, một kênh cảnh báo (SNS e-mail), không người dự phòng; pilot ngoài giờ sẽ không ai phản ứng.
   Hành động: Thêm kênh thứ hai miễn phí (SNS sang chat/webhook hoặc push điện thoại), chỉ định engineer dự phòng, bảng 'engineer on duty' theo tuần.
   Bằng chứng: `incident-response.md:17; docs/generated/alarms.md; ADR 0012:123`
15. **R15** (Liên lĩnh vực; tác động cao, khả năng trung bình, điểm 6, effort M) Năng lực giao hàng phụ thuộc gần như hoàn toàn vào agent AI (~2.800 PR/30 ngày, quy trình nằm trong skill/hook); đổi tài khoản, hạn mức hay giá của nhà cung cấp agent là tốc độ sụp.
   Hành động: Trang 'chạy không có agent' (deploy, rollback, migration bằng tay theo runbook), diễn tập cùng người giữ quyền thứ hai (gộp BO-5); đặt WIP theo năng lực review của người.
   Bằng chứng: `.claude/CLAUDE.md; engineering-handbook.md:215`
16. **R16** (Liên lĩnh vực, Hạ tầng, AI; tác động cao, khả năng trung bình, điểm 6, effort S) Hai nguồn tài trợ AI sẽ hết (key Anthropic tài trợ, credit AWS Lift hạn 31/12); Lift không chi Claude trên Bedrock, chi phí sẽ chuyển sang thẻ trên acc1; chưa ước tính kịch bản không tài trợ.
   Hành động: Thêm kịch bản 'không tài trợ' vào báo cáo FinOps tháng 11; ghi ngày hết hạn từng nguồn vào plan.json làm time-gated check.
   Bằng chứng: `ai-gateway.md:85,198; finops.md:43,81`
17. **R17** (AI; tác động cao, khả năng trung bình, điểm 6, effort S) Diễn tập failover LLM hằng tháng đã duyệt (~0,25 USD) nhưng chưa lên lịch; đường dự phòng chỉ được probe bằng lời gọi nhỏ.
   Hành động: Dùng route-trace/test với 3 tour (writer sang acc1, judge sang OpenAI); lên lịch hằng tháng, bắt buộc chạy ngay sau 01/12.
   Bằng chứng: `ai-gateway.md §8 'Not scheduled'; ADR 0009 d7`
18. **R18** (Hạ tầng; tác động trung bình, khả năng cao, điểm 6, effort M) Chi phí acc2 tăng dù chưa có khách: dự báo tháng 11 277,6/300 USD (92,5%) do 8 service luôn bật, 56 secret, 31 alarm, 2 LB, 2 WAF, traffic liên AZ chưa rõ.
   Hành động: Rà chi phí 0 USD: gom secret theo app, hẹn giờ tắt admin/web Dev khi không dùng, truy nguồn traffic liên AZ; mục tiêu acc2 ≤ 250 USD.
   Bằng chứng: `describe-budgets 16/11; S265 capacity review`
19. **R19** (Kiến trúc; tác động trung bình, khả năng cao, điểm 6, effort M) Schema và tốc độ thay đổi quá lớn so với 2-3 dev: 335 → 527 bảng/view trong 19 ngày, 322 file migration/30 ngày, CONTEXT.md CIS 5.194 dòng.
   Hành động: Mỗi bảng mới nêu lý do + dòng retention trong PR; rà Dead Table Registry hằng tháng cùng C8; tách CONTEXT.md thành phần cốt lõi ≤ 300 dòng + trang chi tiết.
   Bằng chứng: `lịch sử git db-schema-reference.md; git log db/migrations; wc -l CONTEXT.md`
20. **R20** (Sản phẩm, AI, Kiến trúc; tác động trung bình, khả năng cao, điểm 6, effort S) Tài liệu kiến trúc và trang vào cửa lệch: README/llms.txt/handbook/guide tả B2C cũ và LLM trên acc3; ai-gateway.md và snapshot route trước v10/v11; ADR 0009 d14 và 0011a chưa cập nhật.
   Hành động: Sửa một lượt (kèm .vi.md), chụp lại snapshot route, thêm Note vào 0009 d14, đổi trạng thái 0011a; thêm danh sách cụm từ lỗi thời vào Docs lint.
   Bằng chứng: `docs/README.md:17-19; docs/llms.txt:3; docs/adr/0009:407; docs/adr/0011a:3`
21. **R21** (Sản phẩm; tác động trung bình, khả năng cao, điểm 6, effort S) Tracker lệch thực tế: M-P2 'later' dù R5 live, M-OD 'next' dù đã xong, backlog còn 'Backlog' cho issue Done; milestone không có ngày dự báo.
   Hành động: Tính trạng thái tiêu chí milestone từ issue Linear trong plan_sync.py, CI báo đỏ khi lệch; thêm baseline/forecast date; rút gọn backlog README.
   Bằng chứng: `plan.json milestones; docs/backlog/README.md L170-171; plan-sync.yml`
22. **R22** (Kiến trúc; tác động trung bình, khả năng cao, điểm 6, effort S) Số liệu review query không đáng tin: pg_stat_statements bị đẩy ra rất nhiều (dealloc 9.122/tuần, max 10.000).
   Hành động: Nâng pg_stat_statements.max lên 20.000 ở lần reboot yên tĩnh kế tiếp, hoặc lưu top-50 rồi reset sau mỗi review tuần.
   Bằng chứng: `audits/2026-11-09-S273-c43-w46 §Finding`
23. **R23** (Giao hàng; tác động trung bình, khả năng cao, điểm 6, effort S) Integration nightly random-order đỏ 5/11 đêm (không liên tiếp; có run xanh 14/11 xen giữa); test phụ thuộc thứ tự có thể làm merge queue đỏ ngẫu nhiên.
   Hành động: Tái hiện bằng seed trong summary, sửa fixture rò state, đóng issue nightly-red; đỏ quá 3 đêm thì đưa vào danh sách việc đầu phiên.
   Bằng chứng: `nightly-integration.yml runs; issue nightly-red 15/11`
24. **R24** (Giao hàng; tác động trung bình, khả năng cao, điểm 6, effort S) Chưa đo DORA (CFR, MTTR), hầu như không postmortem; commit 'fix:' ~23-28%.
   Hành động: Script 0 USD lấy số tháng từ GitHub API (deploy, revert, fix theo nhãn regression, alarm → green); postmortem 1 trang cho sự cố Dev hỏng > 30 phút.
   Bằng chứng: `engineering-handbook.md:418,862,881; docs/ops/postmortems/ (1 bản)`
25. **R25** (Bảo mật; tác động trung bình, khả năng cao, điểm 6, effort S) Rà quyền truy cập cũ (4 user staff, nay 12), F-15 IAM user/access key chưa kiểm; baseline bảo mật lệch (Cognito 'partial', app repo 'chưa scan lịch sử').
   Hành động: Rà baseline bằng lệnh read-only có sẵn; một bản rà quyền bổ sung ngắn trước pilot (12 user + nhóm, IAM user/key, triage lỗ hổng tháng 11).
   Bằng chứng: `audits/2026-10-20-S245-access-review; baseline.md last_reviewed 2026-11-01`
26. **R26** (Liên lĩnh vực, Bảo mật; tác động trung bình, khả năng cao, điểm 6, effort S) Repo gốc public chứa định danh hạ tầng: docs/generated/alarms.md có ID của ALB và target group, trái DM-6.10/D-25.
   Hành động: Sửa generator docs-gen chỉ in tên, che hậu tố ID; thêm pattern ALB/TG vào lint resource-ID của repo gốc. Không cần viết lại lịch sử.
   Bằng chứng: `docs/generated/alarms.md; repo visibility = public`
27. **R27** (Kiến trúc; tác động trung bình, khả năng trung bình, điểm 4, effort S) Gate dữ liệu đỏ không ai xử lý: Freshness Probe (ENFORCE) đỏ 12-14/11, tự xanh 15/11, nguyên nhân chưa rõ.
   Hành động: Thêm dòng 'gate nightly 7 ngày xanh/đỏ' vào khối trạng thái đầu phiên; gate đỏ 2 đêm liền phải ghi nguyên nhân vào log phiên.
   Bằng chứng: `db-freshness-probe.yml runs 12-15/11`
28. **R28** (AI, Hạ tầng; tác động trung bình, khả năng trung bình, điểm 4, effort M) Trần cứng theo connection chỉ gateway CIS thực thi; TripPlanner chỉ có trần app/ngày; CRM không tính vào trần connection; acc1 trả bằng thẻ.
   Hành động: Thêm cờ vượt trần vào catalog.v_llm_gateway_config_v1 để TP chặn khi lỗi; cộng CRM vào tổng connection; AWS Budget miễn phí kèm e-mail trên acc1.
   Bằng chứng: `ADR 0009 amendment S267; CIS migration 406`
29. **R29** (Bảo mật; tác động trung bình, khả năng trung bình, điểm 4, effort S) AA-Partner (app sẽ giữ PII thật) chưa bật CodeQL; CIS có 2 alert high ReDoS trên input domain do tenant nhập (hạn 30 ngày, trước 07/12).
   Hành động: Bật CodeQL default setup cho AA-Partner (miễn phí repo public), triage lượt đầu; sửa 2 regex (giới hạn độ dài trước khi match).
   Bằng chứng: `gh api code-scanning default-setup; vulnerability-management.md`
30. **R30** (Bảo mật; tác động trung bình, khả năng trung bình, điểm 4, effort S) Biên public chưa có rate limit chung: CloudFront CRM không có rule theo IP, HTTP API TripPlanner không gắn WAF, limiter trong bộ nhớ từng task.
   Hành động: Trình tech lead quyết định ~6 USD/tháng trước pilot có PII thật; nếu chưa duyệt thì ghi là rủi ro chấp nhận có điều kiện mở lại.
   Bằng chứng: `AA-1092 export residuals 2-3; S268 review M3`
31. **R31** (Giao hàng; tác động trung bình, khả năng trung bình, điểm 4, effort S) TripPlanner kém chuẩn CI: không merge queue, strict=false, không ngưỡng coverage, visual planner hay đỏ; main đỏ 3 lần/30 ngày.
   Hành động: Bật ruleset merge queue cho TP, --cov-fail-under bằng mức hiện tại rồi ratchet, ổn định planner.spec.ts.
   Bằng chứng: `gh api branch protection TP; TP ci.yml`
32. **R32** (Giao hàng; tác động trung bình, khả năng trung bình, điểm 4, effort M) Smoke/visual sau deploy web đỏ thì bản lỗi vẫn chạy (Partner deploy-web đỏ 12/151, TP 5/26); circuit breaker chỉ bắt task không khỏe.
   Hành động: Smoke đỏ thì tự gọi ecs_rollback.sh về revision trước, hoặc ít nhất mở issue/bell đỏ như nightly-red.
   Bằng chứng: `Partner runs 43425158176, 43200852058; docs/ops/README.md APP-01`
33. **R33** (Hạ tầng; tác động trung bình, khả năng trung bình, điểm 4, effort S) Phân bổ chi phí chưa đủ: chỉ tag App được kích hoạt, tháng 10 ~50% chi phí acc2 chưa gán app; kích hoạt ở payer cũ hết tác dụng sau 01/12.
   Hành động: Kích hoạt toàn bộ tag ở acc4 ngay ngày chuyển; chạy untagged_report.py trên tháng 12; gắn tag App cho alarm và secret còn thiếu.
   Bằng chứng: `finops.md §Tags; S265 'Not assigned'`
34. **R34** (Liên lĩnh vực, Bảo mật; tác động trung bình, khả năng trung bình, điểm 4, effort M) Agent điều phối chạy bằng role admin của người (phiên STS 12 giờ) trong khi đọc nội dung không tin cậy (tour, tenant, Jira, artifact, web); prompt injection chưa có trong threat model.
   Hành động: Role read-only riêng cho phiên agent mặc định, chỉ assume role ghi khi cần; ghi mối đe doạ vào threat model và AI Use Register (OWASP LLM01 cho agent nội bộ).
   Bằng chứng: `.claude/CLAUDE.md (default profile); .claude/hooks/subagent-guardrails.sh`
35. **R35** (Liên lĩnh vực; tác động trung bình, khả năng trung bình, điểm 4, effort S) Nhiều gói miễn phí có trần cứng: Actions cache > 8/10 GB (issue mở), Linear Free 250, Sentry free; GitHub free buộc repo public.
   Hành động: Bảng 'free-tier limits' trong finops.md có ngưỡng cảnh báo; trước go-live trình chi phí từng mục để quyết.
   Bằng chứng: `issue ci-hygiene cache-over-threshold; session-workflow.md`
36. **R36** (Sản phẩm; tác động trung bình, khả năng trung bình, điểm 4, effort S) Phạm vi nở quá năng lực một người: Academy, kit dự án mới, trang DORA, engine báo cáo chạy song song với việc ra pilot; WIP luôn kịch trần.
   Hành động: Luật 'pilot trước': ≥ 70% slot mỗi phiên cho tiêu chí pilot/prod tới khi có đại lý thật đầu tiên.
   Bằng chứng: `Linear In Progress/In Review = 8; docs/sessions S255-S281`
37. **R37** (Sản phẩm; tác động trung bình, khả năng trung bình, điểm 4, effort S) Catalogue ghi 'live' 115/118 tính năng nhưng không tách 'live trên Dev' với 'đã chứng minh với đại lý'.
   Hành động: Thêm trường proven (none | rehearsal | pilot) lấy từ bằng chứng J-01..J-04, hiện trên trang Product map.
   Bằng chứng: `docs/catalogue/features.yaml`
38. **R38** (Kiến trúc; tác động cao, khả năng thấp, điểm 3, effort M) Coupling về CIS: tenant master, token exchange, AI gateway, catalog views ở CIS; hỏng CIS hoặc contract migration trên DB chung kéo TP/CRM lỗi theo; chưa có degraded mode đã kiểm.
   Hành động: Mỗi add-on ghi 3-5 dòng 'khi CIS/DB không trả lời'; kiểm một lần trong game day 0 USD (scale CIS api về 0 trong 10 phút).
   Bằng chứng: `docs/adr/README.md (0009, 0010a, 0019); owners.yaml consumer_grants`
39. **R39** (Hạ tầng; tác động thấp, khả năng cao, điểm 3, effort S) Service admin/web chỉ chạy Fargate Spot 1 task, gián đoạn ngắn khi Spot bị thay; mang nguyên sang prod sẽ ảnh hưởng người dùng.
   Hành động: Ghi vào module environment: prod_capacity_base = 1 FARGATE và tối thiểu 2 task cho service hướng người dùng ở prod.
   Bằng chứng: `describe-services 16/11`
40. **R40** (Giao hàng; tác động thấp, khả năng cao, điểm 3, effort S) release-please bỏ quên từ 30/10, /health đứng ở 0.18.0; người ngoài kỹ thuật không có release notes.
   Hành động: Merge release PR hằng tuần qua ship_wave cuối phiên, hoặc tắt release-please.
   Bằng chứng: `PR CIS #1179, Booking #161, Partner #133, TP #196`
41. **R41** (Sản phẩm; tác động thấp, khả năng cao, điểm 3, effort S) Academy có nền tảng đủ nhưng 1/6 module nội dung, chưa giúp được onboarding hay bus factor.
   Hành động: Ưu tiên module giúp người thứ hai vận hành (deploy, rollback, sự cố) từ runbook hiện có; nếu chưa thì dừng mở rộng nền tảng.
   Bằng chứng: `docs/learn/paths/fundamentals.yaml`
42. **R42** (Kiến trúc, Bảo mật; tác động trung bình, khả năng thấp, điểm 2, effort S) RLS còn nợ allowlist: 131 finding, 36 bảng có tenant_id không RLS, 20 entry cũ.
   Hành động: Xoá 20 entry cũ, xác nhận lại lý do 36 bảng trong một PR trước khi onboard tenant thật.
   Bằng chứng: `db-schema-reference.md §RLS catalogue guard`
43. **R43** (Bảo mật; tác động trung bình, khả năng thấp, điểm 2, effort S) Chưa có phát hiện mối đe doạ mức tài khoản (GuardDuty, Security Hub tắt) và chưa pentest/DAST.
   Hành động: Giữ quyết định, gắn trigger bật GuardDuty khi pilot nhận PII thật (duyệt chi phí riêng); một lượt OWASP ZAP baseline miễn phí lên CRM và TP trước pilot.
   Bằng chứng: `live: guardduty list-detectors rỗng; baseline.md`
44. **R44** (Hạ tầng; tác động trung bình, khả năng thấp, điểm 2, effort S) Guard chống apply nhầm account còn hở: aa365 và acc3 chưa đặt allowed_account_ids (acc3 hard-code profile); acc1/acc3 ngoài drift CI. AA-517 là tiền lệ.
   Hành động: Thêm allowed_account_ids từ biến (không commit) cho aa365 và acc3, bỏ profile hard-code, ghi lịch plan tay hằng tháng cho acc1/acc3.
   Bằng chứng: `accounts/aa365/versions.tf; accounts/acc3-bedrock/versions.tf; ADR 0018 d5`
45. **R45** (Liên lĩnh vực; tác động trung bình, khả năng thấp, điểm 2, effort S) Tên miền Dev chở staff sign-in, API và tên miền riêng của đại lý; chưa xác minh quyền sở hữu registrar, MFA, gia hạn tự động và tên miền prod.
   Hành động: Ghi quyền sở hữu, gia hạn tự động và người giữ quyền thứ hai của registrar vào access register; chốt tên miền prod trong checklist go-live.
   Bằng chứng: `docs/linear-export AA-246, AA-264`
46. **R46** (Liên lĩnh vực; tác động thấp, khả năng trung bình, điểm 2, effort S) Cây làm việc repo gốc không sạch đầu phiên (.claude/settings.json, plan.json, tracker index.html đã sửa chưa commit; .coverage chưa ignore).
   Hành động: Thêm vào khối trạng thái đầu phiên: repo nào bẩn thì xử lý (PR hoặc bỏ) trước khi nhận việc; cho .coverage vào gitignore.
   Bằng chứng: `git status đầu phiên S282`

## 4. Kế hoạch đề xuất

### Now: 2 tuần (16/11 - 30/11)

Việc rẻ, có hạn cứng hoặc chặn các bước sau.

- [S, tech lead] Bật role truy cập org trong acc2 và thử assume từ acc4 trước 20/11.
- [M, agent + tech lead] Chuẩn bị 01/12: xuất Cost Explorer 13 tháng (25-28/11), probe LLM + embed trước và sau, kế hoạch thoát acc1 một trang, drill failover ngay sau 01/12.
- [S, agent] Một root PR sửa tài liệu lệch: playbook LLM theo v10/v11, ops README, 3 runbook rollback (last_tested từ S264), OPS-05, drill index, ADR 0011a, Note cho 0009 d14, trang vào cửa, snapshot route; thêm lint cụm từ lỗi thời.
- [S, agent] Generator alarms.md che ID ALB/TG; thêm pattern vào lint resource-ID repo gốc.
- [S, agent] Bật CodeQL cho AA-Partner, sửa 2 regex ReDoS ở CIS.
- [S, agent] Sửa integration nightly flaky; thêm dòng 'gate nightly 7 ngày' và 'repo bẩn' vào khối trạng thái đầu phiên.
- [M, tech lead + agent] Buổi duyệt retention theo nhóm cho 67 dòng 'proposed'; chọn cách xử lý pg_stat_statements.
- [S, tech lead] Tạo issue BO-5; chỉ định người giữ quyền thứ hai; nháp checklist go-live ~15 dòng làm tiêu chí M5; sửa milestone plan.json.
- [S, agent] Kịch bản 'không tài trợ' trong báo cáo FinOps tháng 11; rà chi phí acc2 về mục tiêu ≤ 250 USD.

### Next: trước pilot có PII thật / tenant trả tiền đầu tiên

Điều kiện của cổng go-live; mỗi dòng gắn bằng chứng.

- [M, tech lead] MFA bắt buộc cho staff (TOTP hoặc Google IdP + 2SV), amendment ADR 0006.
- [M, business owner] DPA ký (cổng cứng 'không PII thật trước khi ký'), quyết định luật sư rà, điền [To confirm], đối chiếu Art. 50.
- [M, agent] Scrub PII trong gateway chung cho stage free_text; chốt quyết định 10; trần connection chặn được TP/CRM; AWS Budget trên acc1.
- [S, tech lead] Kênh cảnh báo thứ hai, engineer dự phòng, trang 'chạy không có agent' + diễn tập cùng người giữ quyền thứ hai.
- [S, tech lead + agent] Tabletop bảo mật 60 phút, xoay thật 1 secret và 1 DEK, thử break-glass; chạy thử 4 runbook quan trọng.
- [M, agent] Retention chạy live lần đầu mỗi kind; dọn allowlist RLS (20 entry cũ, 36 bảng).
- [L, tech lead + business owner] Prod theo C7.2 (Multi-AZ, AWS Backup cross-region, đo RTO), M5 P0; một ngày go-live dự kiến; độ phủ giá/ảnh cho thị trường pilot.
- [M, agent] TripPlanner lên chuẩn CI (merge queue, coverage); smoke đỏ thì rollback hoặc báo; golden subset eval hằng tuần có trần (duyệt chi phí).
- [S, tech lead] Rate limit biên (~6 USD/tháng) và role read-only cho phiên agent: quyết định có/không, ghi rủi ro chấp nhận nếu không.
- [S, tech lead] Rà quyền bổ sung (12 user staff, IAM user/key), sở hữu registrar và tên miền prod.

### Later: sau go-live hoặc khi trigger đến

Không làm sớm; mỗi mục có điều kiện mở lại.

- [S, tech lead] Bật GuardDuty khi có PII thật (duyệt chi phí riêng); OWASP ZAP baseline định kỳ.
- [S, agent] Đo DORA hằng tháng bằng script 0 USD; postmortem 1 trang cho sự cố > 30 phút.
- [M, tech lead] Đưa Bedrock vào tài khoản AI thuộc org công ty theo ADR 0018.
- [M, agent] Tách CONTEXT.md, rà Dead Table Registry hằng tháng; trường proven cho catalogue; ngày baseline/forecast cho milestone.
- [M, agent] Degraded mode cho add-on khi CIS/DB không trả lời, kiểm trong game day.
- [S, agent] allowed_account_ids cho aa365/acc3; cấu hình prod Spot (base FARGATE, ≥ 2 task); bảng free-tier limits.
- [S, tech lead] Academy: module vận hành cho người thứ hai trước khi mở rộng nền tảng; quyết định giữ hay tắt release-please.

## 5. Những gì chưa kiểm và phương pháp

### Chưa kiểm

**Kiến trúc & dữ liệu**

- Trạng thái live các bảng job (shared.job, booking.job, crm.job): không ECS exec theo luật read-only
- Top SQL trên Performance Insights; nguyên nhân Freshness Probe đỏ 12-14/11 (log run không tải được)
- Prefix archive Parquet trên S3 và số dòng đã archive; số dòng thật của các bảng 'proposed'
- Diễn tập khôi phục tenant cho Booking; load test đường CIS/TP; sao lưu state Terraform

**AI & LLMOps**

- Route live trong DB (v11, connection acc1 bật/tắt); chi tiêu MTD theo connection (số cuối thấy: ~34,32 USD ở S280)
- AWS Budget trên acc1, reconcile có phủ acc1 không; CRM chạy provider thật hay stub trên Dev
- tp_compose có qua scrub_text không; kết quả lượt chạy v6 và mẫu 300 claim
- Ngày áp dụng chính thức Art. 50(2) và thay đổi do Digital Omnibus; hạn của key Anthropic tài trợ

**Bảo mật & tuân thủ**

- IAM user, tuổi access key và root MFA trên acc2 (hook chặn lệnh aws iam); 2SV của Google Workspace
- MFA theo từng user trong pool; kiểm cross-tenant B2B live của AA-1092; WAF association/rules live; scrub log Sentry
- Chính sách Actions và secret cấp org GitHub; thành viên Vercel; retention/redaction có chạy đúng lịch tháng 11
- Văn bản PDPL, NĐ 356 không tải lại, dùng trích dẫn của dự án

**Hạ tầng & FinOps**

- Chi tiêu và budget thực tế trên acc1, acc3; chi tiêu LLM/DFS/geocoder tháng 11 từ ledger
- Trạng thái kích hoạt cost allocation tag (CE API tính phí); OU Transitional và role trong acc4 (chỉ suy ra từ drift xanh)
- SCP của org payer hiện tại; chi phí Vercel, GitHub Actions, Route 53, ACM; nguồn 449 GB traffic liên AZ
- Backup ElastiCache, cấu hình Lambda chi tiết, nội dung hợp đồng Billing Transfer và VAT

**Giao hàng & vận hành**

- Trạng thái Sentry live (connector chưa xác thực); health CRM và TripPlanner (chỉ curl CIS, Booking)
- Required checks và bypass actor trong ruleset Infra; tần suất push --no-verify và override cổng deploy
- MTTR từng sự cố (không có dữ liệu sự cố có cấu trúc); chi phí phút Actions
- Log 13 lần đỏ của DB Migrate và 16 lần đỏ của Terraform Apply

**Sản phẩm, quy trình & tri thức**

- Nội dung comment Jira đã đăng; giao diện live từng tính năng (không mở trình duyệt)
- Tiêu chí M-R7 so với code; độ phủ giá/ảnh theo nước ngoài số Laos
- Số người phát triển thật ngoài danh tính git; repo Booking (origin/HEAD không resolve); Memory Notion
- Người hoàn thành module Academy; chi tiết kit phần 2

### Phương pháp

Sáu auditor chỉ đọc (mỗi người một lĩnh vực) cộng một critic kiểm lại khẳng định chính bằng lệnh đọc live và bổ sung rủi ro liên lĩnh vực. Không ghi repo, không ghi AWS, không ECS exec, không Terraform apply, không gọi LLM trả phí.

Chuẩn công khai: AWS Well-Architected (6 trụ, Generative AI Lens, SaaS Lens), DORA, OWASP ASVS L2 / Top 10 / LLM Top 10 2025, CIS AWS Foundations v3, CIS Controls v8, DAMA-DMBOK, NIST AI RMF 1.0, NIST CSF 2.0, NIST SP 800-61r3, EU AI Act Art. 50, PDPL + NĐ 356/2025, FinOps Framework, ITIL-lite, ISO 22301, OpenSSF Scorecard.

Điều chỉnh theo critic:

- Backup/DR thống nhất ở 3 cho cả Kiến trúc (từ 4) và Hạ tầng (từ 2,5): cùng dữ kiện, tốt cho Dev, thiếu so với C7.2b.
- Tài liệu lệch chấm cùng một mức 3: ADR và nguồn sự thật (từ 3,5), observability/tài liệu AI (từ 3,5).
- Bus factor trừ cả ở Bảo mật: 'Rà quyền và quản trị' từ 3 xuống 2,5.
- 'Bảo vệ PII' từ 4 xuống 3: điểm 4 chỉ đúng cho CRM; tính cả hệ còn retention và scrub trước AI.
- Sửa câu 'Integration đỏ 3 đêm liên tiếp': thực tế có run xanh ngày 14/11 xen giữa.
- Sửa câu 'đường LLM chính (GPT trước) trên acc1': writer chỉ dùng Claude, gọi Anthropic API trước; acc1 là đường đầu cho stage GPT và dự phòng cho writer.
- eval-regression chỉ chạy tay là quyết định có chủ đích (AA-289); khuyến nghị chung: lịch nhỏ có trần, xin duyệt chi phí trước.
- Thống nhất số đếm: 25 file runbook, 12 file last_tested null; lessons.md 367 dòng bullet trên 495 dòng tổng.
- Điểm mỗi lĩnh vực tính lại bằng trung bình các mục con sau điều chỉnh; thêm 8 rủi ro liên lĩnh vực critic chỉ ra (gộp vào bảng xếp hạng, nhãn 'Liên lĩnh vực' hoặc gộp vào rủi ro trùng).

Nguồn: docs/README.md, docs/ecosystem-architecture.md, docs/adr/, docs/architecture/data-standards/, docs/architecture/db-schema-reference.md, CONTEXT.md của từng repo, docs/ops/, docs/security/, docs/legal/, docs/backlog/README.md + tracker/plan.json, docs/audits/ (S255-S281), docs/sessions/ (S279-S281), skill/ (aa-session, aa-ship, aa-lessons), docs/catalogue/, .github/workflows của từng repo, tools/; lệnh AWS chỉ đọc (describe/list/get) và gh api ngày 16/11/2026; curl health công khai.

Tác nhân: Claude Code. Báo cáo không chứa ID tài khoản, ARN, e-mail hay tên/giá trị secret.
