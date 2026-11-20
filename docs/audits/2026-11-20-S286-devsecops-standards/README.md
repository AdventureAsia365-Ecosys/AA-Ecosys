# Đánh giá mức sẵn sàng bảo mật và compliance — bản tóm tắt

> **Đây là bản tóm tắt an toàn để đặt trong repo public.** Bản chi tiết, có từng control, bằng chứng và cách sửa, là tài liệu **riêng tư** và không công bố. Bản này chỉ gồm điểm số, phương pháp, giải thích các khung, các control đã có và lộ trình theo gói việc.

Phạm vi: 6 repo của hệ sinh thái (root, CIS, Booking, Partner, TripPlanner, Infra), cùng các lệnh đọc cấu hình cloud và GitHub. Ngày kiểm: 20/11/2026. Mỗi khung được đánh giá hai vòng: đánh giá lần đầu, sau đó phản biện kiểm lại.

Thang trạng thái:
- `met`: có bằng chứng và đang chạy.
- `partial`: đã có một phần.
- `gap`: chưa có.
- `org_process`: cần chính sách hoặc quy trình do người thực hiện.
- `N/A`: không áp dụng.

---

## 1. Tóm tắt điều hành

Cách tính:
- **% đáp ứng có trọng số** = (met + 0,5 × partial) / (tổng − N/A).
- **% met chặt** = met / (tổng − N/A).

| Khung | Số mục | Met | Partial | Gap | Org_process | N/A | % met chặt | % đáp ứng có trọng số | Mức sẵn sàng |
|---|---|---|---|---|---|---|---|---|---|
| ISO/IEC 27001:2022 + Amd 1:2024 | 117 | 20 | 58 | 14 | 15 | 10 | 18,7% | 45,8% | Cần 6–12 tháng (thực tế khoảng 4–6 tháng sau khi dựng hệ quản lý) |
| — Điều khoản 4–10 | 24 | 0 | 11 | 11 | 2 | 0 | 0% | 22,9% | |
| — Annex A | 93 | 20 | 47 | 3 | 13 | 10 | 24,1% | 52,4% | |
| SOC 2 (TSC 2017/2022) | 51 | 0 | 44 | 2 | 4 | 1 | 0% | 44,0% | Cần 6–12 tháng (cần môi trường prod và cửa sổ quan sát) |
| ISO/IEC 42001:2023 + EU AI Act | 66 | 8 | 44 | 9 | 3 | 2 | 12,5% | 46,9% | Cần 6–12 tháng (nên làm tích hợp với 27001) |
| OWASP Top 10:2025 | 45 | 17 | 23 | 3 | 1 | 1 | 38,6% | 64,8% | Không có chứng nhận; mục tiêu ASVS L1 trong khoảng 3 tháng |
| OWASP LLM Top 10 2025 + Agentic Top 10 2026 | 27 | 9 | 18 | 0 | 0 | 0 | 33,3% | 66,7% | Không có chứng nhận |
| DevSecOps pipeline + quản lý lỗ hổng | 32 | 7 | 18 | 5 | 2 | 0 | 21,9% | 50,0% | Không có chứng nhận |

Có **49 mục được đánh dấu nhạy cảm**: ISO 27001 16, SOC 2 10, ISO 42001 3, OWASP Top 10 8, OWASP LLM/Agentic 8, DevSecOps 4. Bản này chỉ ghi số lượng của chúng.

**Nhận định chung:**
- Control kỹ thuật đã ở mức khá tốt so với một startup nhỏ.
- Lớp **hệ quản lý** (policy được duyệt, phạm vi, risk register, Statement of Applicability, internal audit, management review) mới ở giai đoạn đầu. Đây là phần cần đầu tư nhiều nhất trước khi tính tới chứng nhận.
- Hiện chưa khung nào chứng nhận được ngay. Hướng đề xuất là dựng hệ quản lý bảo mật và AI tích hợp với chi phí thấp, rồi chỉ đi chứng nhận khi có yêu cầu thật từ khách hàng.

---

## 2. Các khung và cách chúng áp vào hệ thống

| Khung | Cấp | Tóm tắt | Thường được ai yêu cầu |
|---|---|---|---|
| **ISO/IEC 27001:2022 + Amd 1:2024** | Tổ chức | Hệ quản lý an toàn thông tin (ISMS). Gồm điều khoản 4–10 và Annex A với 93 control trong 4 nhóm: Organizational 37, People 8, Physical 14, Technological 34. Amd 1 bổ sung yêu cầu xét biến đổi khí hậu. Tổ chức chứng nhận phải được công nhận theo ISO/IEC 27006-1:2024 | Khách hàng ở Úc và EU |
| **SOC 2** | Tổ chức | Báo cáo attestation do công ty CPA có giấy phép thực hiện, dựa trên Trust Services Criteria 2017 (points of focus sửa năm 2022). Type I đánh giá thiết kế control tại một thời điểm. Type II đánh giá vận hành trong một cửa sổ: AICPA không đặt tối thiểu, lần đầu thường là 3 tháng. AICPA đang lấy ý kiến cho bộ tiêu chí 2027 có thêm nội dung về AI | Khách hàng Mỹ |
| **ISO/IEC 42001:2023** | Tổ chức | Hệ quản lý AI (AIMS), cấu trúc giống 27001. Annex A có 38 control trong 9 mục tiêu. Tổ chức chứng nhận theo ISO/IEC 42006:2025 | Khách hàng EU; hỗ trợ tuân thủ EU AI Act (Art. 4 AI literacy, Art. 50 minh bạch) |
| **OWASP Top 10:2025** | Kỹ thuật | 10 rủi ro web. Hai mục mới là A03 Software Supply Chain Failures và A10 Mishandling of Exceptional Conditions; SSRF được gộp vào A01 Broken Access Control. Đo bằng OWASP ASVS 5.0 | Questionnaire, phạm vi pentest |
| **OWASP LLM Top 10 2025** | Kỹ thuật (AI) | Prompt injection, rò dữ liệu nhạy cảm, xử lý output, quyền hạn quá mức, tiêu thụ không giới hạn, và các rủi ro khác | Phụ lục bảo mật cho khách EU |
| **OWASP Agentic Top 10 2026** | Kỹ thuật (agent) | Goal hijack, tool misuse, lạm dụng danh tính và quyền, chuỗi cung ứng agent, memory poisoning, và các rủi ro khác | Áp dụng vì đội phát triển dùng AI agent |
| **CVE / CVSS v4.0 / EPSS / CISA KEV** | Vận hành | Định danh lỗ hổng, mức nghiêm trọng, xác suất bị khai thác, và danh sách lỗ hổng đã bị khai thác thật | Auditor lấy mẫu để kiểm "đã sửa trong SLA" |

Phân vai theo EU AI Act (đánh giá kỹ thuật, chờ tư vấn pháp lý xác nhận):
- Nền tảng là **provider** của các tính năng AI; agency là **deployer**.
- Không có hệ thống nào thuộc nhóm high-risk theo Annex III.
- Các tính năng AI thuộc nhóm minh bạch theo Art. 50.

---

## 3. Kết quả theo từng khung (số đếm và các control đã có)

### 3.1 ISO/IEC 27001

- **Điều khoản 4–10:** 0 met, 11 partial, 11 gap, 2 org_process. Hệ quản lý (scope, policy, risk assessment, SoA, audit, review) là phần trọng tâm của lộ trình.
- **Annex A:** 20 met, 47 partial, 3 gap, 13 org_process, 10 N/A. Các control vật lý được kế thừa từ nhà cung cấp cloud và có bằng chứng qua AWS Artifact.
- **Control đã có bằng chứng (ví dụ):**
  - Gắn nhãn và phân loại tài nguyên bằng tag guard trong CI.
  - Quy tắc kiểm soát truy cập được ghi trong ADR.
  - Kế hoạch ứng phó sự cố kèm playbook.
  - Postmortem và vòng bài học → guard.
  - Bộ runbook vận hành.
  - Quản lý năng lực có load test.
  - Hạ tầng dưới dạng code, có drift check hằng đêm.
  - Che dữ liệu cá nhân trước khi gửi tới model AI.
  - Audit trail cloud multi-region có log validation.
  - Mã hoá at rest với khoá có rotation.
  - Phân tách mạng.
  - Change management qua PR, required checks và merge queue.

### 3.2 SOC 2

- 0 met, 44 partial, 2 gap, 4 org_process, 1 N/A.
- Chưa có mục nào met, vì SOC 2 cần policy được duyệt và hồ sơ vận hành trong một cửa sổ quan sát.
- Phạm vi đề xuất cho lần đầu: Security + Confidentiality.
- Phần lớn tiêu chí đã có nền kỹ thuật tương ứng.

### 3.3 ISO/IEC 42001 + EU AI Act

- **Điều khoản:** 0 met, 15 partial, 2 gap, 3 org_process.
- **Annex A:** 7 met, 24 partial, 7 gap.
- **EU AI Act và mục bổ sung:** 1 met, 5 partial, 2 N/A.
- **Control đã có bằng chứng:**
  - AI gateway có sổ cái chi phí và hard cap.
  - Tài liệu thiết kế cho từng hệ AI.
  - Log sự kiện của mọi lần gọi model.
  - Không huấn luyện model trên dữ liệu khách hàng.
  - Provenance của dữ liệu đánh giá.
  - Thông báo AI và đánh dấu nội dung do AI tạo.
  - Người duyệt trước khi nội dung được xuất bản.

### 3.4 OWASP Top 10:2025

- 17 met, 23 partial, 3 gap, 1 org_process, 1 N/A.
- **Control đã có:**
  - Cô lập tenant ở tầng database, có probe kiểm trong CI.
  - Chính sách CORS chặt.
  - Bắt buộc pin GitHub Actions theo commit SHA ở cấp org.
  - Dependabot cùng các gate pip-audit.
  - Secret scanning và push protection.
  - Mã hoá dữ liệu và quản lý khoá.
  - Kiểm chữ ký webhook.
  - Các quyết định bảo mật theo nguyên tắc fail-closed.
  - Giới hạn tài nguyên và timeout.

### 3.5 OWASP LLM + Agentic

- 9 met, 18 partial.
- **Control đã có:**
  - Rào chắn prompt cho trường thương hiệu.
  - Tách dữ liệu và chỉ dẫn trong luồng soạn thảo CRM.
  - Rào chắn cho chat lập kế hoạch: che PII, giới hạn lịch sử, test hồi quy trong CI.
  - Phạm vi dữ liệu theo nhà cung cấp.
  - Không cấp tool có quyền ghi cho model ở sản phẩm.
  - Ngân sách và hard stop cho chi phí AI.
  - Circuit breaker cho nhà cung cấp.
- Phần còn lại tập trung vào quy trình làm việc của agent phát triển và vào việc kiểm hành vi model định kỳ.

### 3.6 DevSecOps

- 7 met, 18 partial, 5 gap, 2 org_process.
- **Control đã có:**
  - Dependabot, có lịch sử sửa nhanh.
  - Secret scanning và gitleaks ở cả PR lẫn toàn bộ lịch sử.
  - Allow-list Actions, SHA pinning, token mặc định chỉ đọc.
  - Exception lỗ hổng có hạn dùng.
  - Audit trail cloud và các rule cảnh báo bảo mật.
  - Test hồi quy bảo mật trong CI.

---

## 4. Ma trận chồng lấn (làm một lần, phục vụ nhiều khung)

| Control dùng chung | ISO 27001 | SOC 2 | ISO 42001 | OWASP | DevSecOps |
|---|---|---|---|---|---|
| Bộ policy, phạm vi và vai trò | Điều khoản 4–5, A.5.1–5.4 | CC1, CC2, CC5.3 | Điều khoản 4–5, A.2, A.3 | — | Policy lỗ hổng |
| Risk register + SoA | 6.1, 8.2, 8.3 | CC3, CC5.1 | 6.1, 8.2–8.3 | A06 | Threat model |
| Xác thực và quyền đặc quyền | A.5.17, A.8.2, A.8.5 | CC6.1–6.3 | A.9.2 | A01, A07, ASI03 | CI identity |
| Change control | A.8.32, A.8.4 | CC8.1 | A.6.2.5 | A03, A08 | Branch protection |
| Quản lý lỗ hổng (CVSS + EPSS + KEV) | A.8.8, A.8.28 | CC7.1 | — | A03 | SAST, SCA, container |
| Chuỗi cung ứng phần mềm (scan, SBOM, provenance) | A.5.21 | CC6.8 | A.4.4 | A03, LLM03 | Build once |
| Logging và giám sát | A.8.15, A.8.16 | CC7.2–7.3 | 9.1, A.6.2.6 | A09 | Alerting |
| Ứng phó sự cố và diễn tập | A.5.24–5.28 | CC7.3–7.5 | A.8.4 | — | — |
| Backup và liên tục kinh doanh | A.5.30, A.8.13 | CC9.1, A1 | — | — | — |
| Quản lý nhà cung cấp | A.5.19–5.23 | CC9.2 | A.10.3 | LLM03 | — |
| Retention và xoá dữ liệu | A.8.10 | CC6.5, C1.2 | A.7 | LLM02 | — |
| Threat model + ASVS | A.8.26–8.27 | CC3.2 | Đánh giá tác động AI | A06 | SAMM |
| Pentest và audit độc lập | 9.2, A.5.35 | CC4.1 | 9.2 | Pentest | — |
| Đào tạo và AI literacy | 7.2–7.3, A.6.3 | CC1.4 | 7.2–7.3, EU Art. 4 | — | — |

---

## 5. Cách đánh giá

### 5.1 Phương pháp

1. Gap assessment (tài liệu này), lặp lại mỗi quý dựa trên code và cấu hình thật.
2. Asset register và risk register: phương pháp 5×5, ngưỡng chấp nhận do lãnh đạo ký.
3. Statement of Applicability chung cho 27001 và 42001.
4. Risk treatment plan: mỗi rủi ro trỏ tới một gói việc.
5. Vận hành 2–3 tháng để tích luỹ hồ sơ: biên bản triage, access review, drill, sổ sự cố, đào tạo.
6. Internal audit do người độc lập thực hiện.
7. Management review có biên bản.

### 5.2 Công cụ

- **Miễn phí:**
  - Prowler (cloud posture).
  - AWS Artifact (bằng chứng kế thừa).
  - CodeQL, Dependabot, pip-audit/npm audit/osv-scanner.
  - Trivy, grype, syft, checkov.
  - GitHub artifact attestations.
  - OWASP ZAP.
  - promptfoo, garak, PyRIT (red-team AI).
  - FIRST EPSS, CISA KEV.
- **Trả phí, tuỳ chọn:**
  - Dịch vụ phát hiện mối đe doạ và posture của cloud: khoảng 15–50 USD/tháng tuỳ dịch vụ (ước tính).
  - Nền tảng compliance như Vanta, Drata, Secureframe, Sprinto: khoảng 7.000–25.000 USD/năm (ước tính thị trường, chưa kiểm giá). Chưa cần ở quy mô hiện tại.

### 5.3 Ưu tiên lỗ hổng

Kết hợp CVSS v4.0, EPSS và CISA KEV:

| Mức | Điều kiện | Hạn sửa (dev) |
|---|---|---|
| P0 | Có trong KEV, hoặc EPSS ≥ 0,10, hoặc CVSS ≥ 9,0 trên code chạy và tiếp xúc internet | 7 ngày |
| P1 | CVSS 7,0–8,9, hoặc EPSS percentile ≥ 0,90 | 30 ngày |
| P2 | CVSS 4,0–6,9 | 90 ngày |
| P3 | CVSS < 4,0 | Chu kỳ sau |

Ở môi trường prod, mọi hạn sửa rút còn một nửa.

### 5.4 Chỉ số đo liên tục

- Số finding đang mở theo mức và số đã quá SLA.
- MTTR theo mức.
- % image đang chạy đã được quét và có SBOM.
- % repo có SAST và có gate SAST.
- % tài khoản admin có MFA bắt buộc.
- % thay đổi có phê duyệt.
- % control có bằng chứng tự động.
- Số tài liệu quá hạn review.
- Tỷ lệ pass bài test adversarial cho AI.
- RTO đo được trong drill.

### 5.5 Nhịp rà soát

| Nhịp | Việc |
|---|---|
| Mỗi PR | Các gate bảo mật trong CI |
| Hằng tuần | Dependabot |
| Hằng tháng | Triage lỗ hổng, DAST, quét lại image, red-team AI, Prowler |
| Hằng quý | Access review, scorecard, management review, ASVS |
| Hằng năm | Risk assessment, review policy, internal audit, pentest, đào tạo |

### 5.6 Lộ trình chứng nhận và chi phí tham khảo (ước tính, chưa có báo giá)

| Khung | Đường đi | Thời gian | Năm đầu | Duy trì |
|---|---|---|---|---|
| ISO 27001 | ISMS → vận hành → internal audit → Stage 1/Stage 2 với tổ chức chứng nhận được công nhận | 4–6 tháng | 6.000–15.000 USD (chi phí audit) | 3.000–6.000 USD/năm |
| SOC 2 | Readiness → Type I → cửa sổ Type II | 6–9 tháng | 15.000–35.000 USD | 10.000–30.000 USD/năm |
| ISO 42001 | Sau 27001 hoặc tích hợp cùng | 4–9 tháng | 8.000–20.000 USD | 4.000–8.000 USD/năm |

Trình tự đề xuất:
1. Dựng hệ quản lý tích hợp với chi phí thấp.
2. Pentest trước khách hàng trả tiền đầu tiên.
3. ISO 27001 khi khách hàng Úc/EU yêu cầu.
4. ISO 42001 tích hợp.
5. SOC 2 khi khách hàng Mỹ yêu cầu.

---

## 6. Lộ trình theo gói việc

| Pha | Gói việc |
|---|---|
| **0–30 ngày** | Staff authentication hardening; AI output and prompt hardening; EU AI Act transparency launch gate và AI register integrity; agent least privilege; repo change-control hardening; bắt đầu vulnerability management v2 |
| **30–90 ngày** | Build-once image pipeline với quét định kỳ; vulnerability management v2 hoàn chỉnh; bộ tài liệu ISMS + AIMS được lãnh đạo ký; edge and runtime protection; diễn tập ứng phó sự cố và kiểm key-holder thứ hai; threat model và ASVS; tư vấn pháp lý cho hồ sơ DPA |
| **90–180 ngày** | Pentest bên ngoài; internal audit độc lập lần đầu; management review; môi trường prod theo blueprint; quyết định có đi chứng nhận hay không |

Phân việc:
- Phần kỹ thuật do kỹ sư và agent thực hiện.
- Các quyết định về chính sách, ngân sách, pháp lý và chứng nhận do business owner đưa ra.

---

## 7. Phụ lục: nguồn chuẩn đã kiểm (20/11/2026)

| Chuẩn | Phiên bản | Nguồn |
|---|---|---|
| ISO/IEC 27001 | 2022 + Amd 1:2024; 93 control; ISO/IEC 27006-1:2024 | iso.org, IAF, ANAB, UKAS |
| SOC 2 | TSC 2017 (points of focus 2022); exposure draft 2027 TSC | aicpa-cima.com |
| ISO/IEC 42001 | 2023; 38 control; ISO/IEC 42006:2025; ISO/IEC 42005:2025 | iso.org và catalog thứ cấp |
| EU AI Act | Reg. 2024/1689; Art. 4 (từ 2/2/2025); Art. 50 (từ 2/8/2026); Digital Omnibus (chưa kiểm EUR-Lex) | Các nguồn pháp lý thứ cấp |
| OWASP Top 10 | 2025 | top10.owasp.org/2025 |
| OWASP ASVS | 5.0.0 (30/5/2025) | asvs.owasp.org |
| OWASP LLM Top 10 | 2025 | genai.owasp.org/llm-top-10 |
| OWASP Agentic Top 10 | 2026 (9/12/2025) | genai.owasp.org |
| CVSS | v4.0, tài liệu bản 1.2 | first.org |
| EPSS | Model v2026.06.15 | api.first.org; epss.empiricalsecurity.com |
| CISA KEV | Catalog 2026.11.18 (1786 mục) | cisagov/kev-data |
| OWASP SAMM / SLSA | SAMM 2.0; SLSA v1.2 | owaspsamm.org; slsa.dev |
