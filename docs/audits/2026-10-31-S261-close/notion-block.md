---
id: OPS-08-s261-notion-block
title: "S261 Notion memory block"
description: "Khối phiên S261 để prepend vào đầu Program Brain/memory.md (Notion); agent cuối phiên không ghi Notion, phiên sau hoặc điều phối dán nguyên văn."
type: report
status: active
owner: nghiep
audience: [agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-31
review_every_days: 30
related: [AA-997, AA-952, AA-804, AA-1014, AA-873]
---

# Khối prepend cho Notion memory.md (S261)

Dán nguyên văn phần dưới đường kẻ vào đầu `Program Brain/memory.md` (chỉ prepend, không cắt khối cũ).

---

## S261 (31/10/2026, Claude Code — VSCode/WSL, Ultracode): dọn In Progress, vá IAM, cổng AI v2 duyệt, CRM 7 module chốt, video CRM phiên A
**Quyết định của Nghiệp**
- "Việc nào cần tôi duyệt thì duyệt cho làm luôn theo kế hoạch" → trang quyết định triage S260 coi như duyệt.
- Duyệt kế hoạch video review CRM (Q1–Q8); duyệt tạm 2 giọng (EN Kokoro af_heart, VI VieNeu nữ miền Nam); phụ đề + giọng đổi được.
- Duyệt mô hình tổ chức AWS + kế hoạch quota LLM (phần tech lead T1–T14); acc3 giữ độc lập, chưa vào org AA vội.
- AA-967: diễn tập xoá thật (phương án a).
- Đường Anthropic Dev dựng sẵn, chưa thêm key; bằng chứng quota cho case AWS chờ vài ngày; TL-7 chưa làm; DFS đã xoay S251 — không nhắc nữa.
- GitHub không tốn tiền → repo gốc + Infra giữ public (huỷ kế hoạch private).
- Duyệt cổng AI v2 (3 đề xuất; API ngoài = cả Anthropic và OpenAI; ít issue nhất) → root #397, ADR 0009 phần đã duyệt Accepted.
- Luật mới: không nói trạng thái theo trí nhớ, kiểm live hoặc ghi "chưa kiểm". Artifact dưới tài khoản nghieppham@adventure.asia.
- Dừng phiên; nháp Jira chuyển phiên sau cùng ngày.
**Kết quả chính**
- In Progress 31 → 12. Done: AA-953 (Partner #145), AA-962 (#146), AA-966 (#144, root #391), AA-961 (Infra #544–#546), AA-967 (Infra #547/#548), AA-923, AA-945/AA-955/AA-990/AA-994/AA-1002/AA-880/AA-919/AA-816/AA-703 (Done-with-scope).
- AA-952 lát 4 + F1/F2 (Partner #143, #148; Infra #538 ANALYZE guard) live 15 mục; còn 2 mốc giờ.
- AA-997: luật aa997.4 (CIS #1193, api :940 / worker :506); chuỗi `dc260ef8` chạy lại ~00:12Z 01/11.
- AA-873: vá chuỗi đọc secret IAM (Infra #541, chi tiết trong Linear), rút gọn ghi chú public (Infra #543).
- AA-1002 đường Anthropic Dev không key (Infra #549/#550, budget 150 USD/tháng, connection tắt; runbook root #395).
- E2E CRM xanh lại (Partner #149 limiter portal riêng, #147 spec; run 41177723455). Partner #150 bỏ địa chỉ .invalid.
- AA-1014 phiên A: 21 đoạn + prep/cleanup PASS (root #396); mẫu R01/R03 ở .tmp-session/S261/video-samples/.
- Audit: review kiến trúc 9 vai (3,2/5, F1/F2 rút khỏi bản public), quota LLM, mô hình AWS/Bedrock, repo private (huỷ), cổng AI v2.
- Tạo AA-1005…AA-1018 (follow-up triage, CRM/Booking, video, capacity, cổng AI v2: AA-1017 hạn 28/11, AA-1018 hạn 05/12).
**Trạng thái kiểm cuối phiên** (~11:00Z, `docs/audits/2026-10-31-S261-close/state-snapshot.md`)
- ECS COMPLETED 1/1: cis-api :940 + worker :506 `dev-1b6e9448`; booking :90 `636df62c`; crm-api :94 `bc5f9280`; crm-web :66 `ba225e4b`.
- Migration: CIS 317, bk-035, crm-031 (ready); tp-022 live chưa kiểm. Health 200 hết; crm.lumiguides.it.com 000 (dùng portal.).
- shared.job: 1 queued (place_relocate, cố ý), 0 running, 0 wave; booking.job / crm.job chưa kiểm.
- CI đỏ: root Secret Scan full history (gitleaks aws-access-token ở tools/docs/test_docs_reader.py, #302 — có thể giả, chưa kiểm); Infra DB Freshness Probe 4 đêm (111 link place_card_links_missing).
- Để BẬT: đường Anthropic Dev (không key), CRM LIFECYCLE_DRY_RUN=true (:94), chuỗi AA-997, worktree .tmp-session/wt/s261-video-a.
**Việc cần làm đầu phiên sau (S262, cùng ngày)**
1. Nháp Jira (từ docs/audits/2026-10-31-S261-close/jira-drafts.md) → duyệt một lần → đăng.
2. AA-952: nhắc nợ ≥ 18:10Z 31/10, link hết hạn ≥ 04:35Z 02/11 → Done-with-scope.
3. AA-997: sau chuỗi ~00:12Z 01/11 → audit → điền báo cáo → quyết TL-25 (hide_flagged) → đóng.
4. Một trang quyết định bấm chọn cho các mục TL còn mở của review kiến trúc.
5. AA-642 lát S0 (0 USD).
6. AA-1014 Session B trước 10/11 (prep ≥ 1 giờ trước R10).
7. AA-896 (01/11), AA-922 (02/11).
8. AA-994 follow-up UI kit (AA-1006 → AA-1007 → AA-1008).
**Lưu ý kỹ thuật**
- Expand guard: bảng chưa ANALYZE (reltuples -1) → runner ANALYZE rồi đọc lại (Infra #538). Apply-pending không nhảy khoảng trống số → merge migration theo thứ tự số.
- Lane nặng RAM (TTS + Chromium) cần free -m ≥ 2,5 GB; cloudcode_cli giữ ~3,5 GB.
- gitleaks bắt khoá map HCL đuôi `_key` dù giá trị chỉ là tên secret.
