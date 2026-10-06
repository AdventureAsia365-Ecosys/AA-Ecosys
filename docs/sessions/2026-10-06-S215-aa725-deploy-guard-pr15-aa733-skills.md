# S215 — AA-725 deploy guard (phần 1-4) + báo cáo PR-15 + AA-733 skill restructure (06/10/2026)

**Tác nhân:** Kiro (VSCode/WSL) · **ECS cuối phiên:** `aa-cis-dev-api:459` (rollout COMPLETED) · **Migration mới:** không · **Branch cuối:** AA-CIS-App về `main` sạch; repo gốc còn `chore/aa-733-skill-restructure` (PR #28 chờ Nghiệp review phiên sau — có chủ ý).

## Trạng thái
Nghiệp chốt làm AA-725 trước (giải thích đơn giản 2 lượt mới OK), rồi xen báo cáo PR-15, cuối cùng AA-733. AA-725 phần 1-4 Done trọn (verify live); phần 5 (digest pin) để phiên sau cho an toàn. PR-15 đã đăng. AA-733 xong phần Kiro resolve marker, PR #28 để Nghiệp review+merge phiên sau.

## Đối chiếu list việc đầu phiên S215
| Việc | Kết quả |
|---|---|
| AA-725 deploy guard (Nghiệp chọn làm trước) | ✅ phần 1-4 Done live; phần 5 (PR3) phiên sau |
| Báo cáo PR-15 Jira (rerun theo nước) | ✅ đăng comment 10459 |
| AA-733 skill restructure | ✅ PR #28 (chờ review); zip cho Claude Chat |
| Wave Nepal / AA-724 / AA-641 / AA-714 | ❌ chưa (phiên dồn vào 3 việc trên) |

## AA-725 — CI deploy guards (phần 1-4 Done, phần 5 phiên sau)
3 PR theo rủi ro tăng dần. Nghiệp duyệt hướng + chọn cách A (pre-deploy guard hỏi qua HTTP endpoint, vì CI không vào được RDS private).

- **PR #573 (phần 3+4, merged, CI xanh):** `tests/unit/test_aa725_route_sanity.py` (AST: không @router/@app decorator bind vào `_helper` — đúng lỗi S211 PR #559; + import app gọi mọi GET route không-param, cấm 422). `tests/unit/test_aa725_dockerfile_copy.py` (mọi module top-level api/shared/services/worker có `COPY` + path filter `deploy-dev.yml` — lỗi S210). Thuần test, verify bắt bug thật (tái hiện S211 → đỏ).
- **PR #574 (phần 1+2, merged + deployed + verify live):**
  - Part 1: `GET /admin/job-runner/deploy-gate` (gate admin-secret) + `queue.active_count()` (status IN queued/running, KHÔNG lọc thời gian). `deploy-dev.yml` thêm job `preflight` curl gate trước ECS roll; `deploy` needs `[build-and-push, preflight]`. `workflow_dispatch` thêm input `override_running_jobs` (lý do, log). Disabled gracefully khi chưa có secret → safe to merge.
  - Part 2: smoke mở rộng — health + job-runner summary + deploy-gate + overview (200 + shape), thay vì chỉ /health.
- **Kích hoạt guard:** set GitHub repo secret `ADMIN_SECRET` pipe thẳng từ Secrets Manager `aa-cis/dev/admin-secret` (chuỗi thuần 44 ký tự) → `gh secret set`, KHÔNG lộ giá trị.
- **Verify LIVE:** ECS api rollout COMPLETED `:459`; `deploy-gate` + secret → 200 `{active:0,by_status:{},safe_to_deploy:true}`; không secret → 403 (không 404). Deploy Dev run sau merge: 5 job xanh (gồm "Pre-deploy job guard" + smoke mới); trước khi set secret guard warn+pass (inert an toàn), sau khi set thì active.
- **Phần 5 (PR3) phiên sau:** pin image digest để api==worker cùng SHA (sửa `deploy_family.sh` đang dùng `:latest` cho cả hai). Rủi ro cao nhất, tách riêng.

**Phát hiện quan trọng:** merge PR vào main CÓ trigger `Deploy Dev` qua GitHub Actions (lúc đầu Kiro tưởng không — do `gh run list` sort lạ). Guard hiệu lực cho mọi deploy qua đường này.

## PR-15 Jira (comment 10459) — tiến độ rerun theo nước
- Số liệu **verify LIVE từ DB** (ECS exec script count master_status='active', v_active_tour_atoms, review_queue) — KHÔNG gom tay từ log.
- Bảng 7 nước + cột thứ tự (theo thứ tự chị Thư chốt): Korea 30/30, Taiwan 36/36, Mongolia 17/17, China 121/121, Thailand 43→41 (2 review), Bhutan 32/32, Laos 46→45 (1 review). **Tổng: raw 325 / master 322 / atom 322 / review 3.**
- **Sửa so với draft v1:** Thailand raw thật = **43** (không phải 41 như gom tay). Verify live cứu lỗi.
- Giọng văn khớp comment Nghiệp trước (đọc 10448-10456), tag @thule bằng mention node HTML, không nhắc Jev/mã nội bộ, không tự đổi trạng thái issue.

## AA-733 — skill restructure (PR #28 repo gốc, chờ review)
- Thay 3 skill nguyên khối (114 KB, 83 marker lỗi thời) → **9 skill** trong `skill/`, mỗi SKILL.md ≤90 dòng + `references/`. Tổng **56.1 KB** (Nghiệp chấp nhận chênh ~1KB).
- Skill mới: aa-session, aa-ship, aa-ui-verify, aa-linear-issue, aa-jira-update, aa-wave-rerun. Giữ ai-nghiep, aa-cis-schema, aa-ecosys-repos (slim).
- **Resolve 43 marker** VERIFY/SINH LẠI bằng code/AWS/DB thật → log `skill/VERIFY-LOG.md`. Sinh lại cis-app.md (router/page/10 job kind) + pipeline.md (stage→code) từ repo.
- **Tạo `docs/architecture/dead-table-registry.md`** (21 bảng DROP 27/08, migration 121+122) ở **root AA-Ecosys** (cạnh db-schema-reference — Nghiệp xác nhận đúng).
- **Sửa 3 lỗi draft Claude Chat:** db-schema-reference ở root (không phải AA-CIS-App); ADR số `NNNN` 2 cấp repo (không `ADR-2026-NNN`); AA-723 đã Done (không "đang chuyển").
- Nghiệp chốt: Mr.Manh/QuanSolution bỏ (giữ 3 người); 56KB OK; dead-table ở root OK.
- **Zip review:** `.tmp-session/aa-733-skills-review.zip` (44 KB) cho Nghiệp upload Claude Chat review theo REVIEW-CHECKLIST.md.
- **Chưa làm (theo quy trình issue):** sync Kiro steering + upload Claude — SAU khi Claude Chat review. **PR #28 để phiên sau Nghiệp review + merge** (Nghiệp yêu cầu).

## Bằng chứng verify
- AA-725: xem phần trên (deploy-gate 200/403, ECS :459, Deploy Dev 5 job xanh).
- PR-15: số live DB (325/322/322/3).
- AA-733: 0 marker trong skill/, mỗi SKILL.md ≤150 dòng, frontmatter name khớp 9/9, references không mồ côi.

## Còn lại (chuyển phiên sau)
1. **AA-733: review + merge PR #28** (Nghiệp review phiên sau) → rồi sync steering + upload Claude.
2. **AA-725 phần 5 (PR3):** pin image digest api==worker. Rủi ro cao, tách riêng.
3. **Wave Nepal (86)** → Sri Lanka (126) → India (236) — lọc `source_status='active'`, prefetch trước.
4. AA-724 (gom mẫu hype-tone: 2 Thailand + 1 Laos Wellbeing-and-Yoga), AA-641, AA-714 (In Review), AA-732.

## Lưu ý kỹ thuật / BÀI HỌC
- **CI không vào được RDS private** → pre-deploy guard phải hỏi qua HTTP endpoint của app (deploy-gate), không query DB thẳng.
- **Set GitHub secret không lộ giá trị:** pipe thẳng `aws secretsmanager get-secret-value ... | gh secret set`. Kiểm shape (JSON vs plain) trước.
- **Import `api.main` trong test local prompt MFA** nếu có AWS_PROFILE — CI không có profile nên không prompt. Mô phỏng CI: unset AWS_PROFILE + set dummy static keys (`AWS_ACCESS_KEY_ID=testing...`) + `AWS_EC2_METADATA_DISABLED=true`.
- **ECS exec script import app code:** cần `cd /app && PYTHONPATH=/app` (không thì `ModuleNotFoundError: shared`).
- **Verify live cứu số sai:** Thailand raw gom tay 41, DB thật 43. Luôn verify DB trước khi báo chị Thư.
- **`gh run list` sort gây hiểu nhầm** "không có deploy run" — kiểm kỹ bằng run id cụ thể / `gh run watch`.
- **Repo gốc là lệ root PR** (merge tay, không CI gate) nhưng phiên này để PR #28 treo theo yêu cầu Nghiệp — repo gốc KHÔNG về master, đứng ở branch AA-733.
- Log local: file này. Memory Notion: prepend S216 (phiên sau là S216).
