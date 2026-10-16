# S239 — 16/10/2026 — Dọn In Progress: RLS tenant, retention, Segment lẫn nước, search chịu tải qua acc3, domain riêng

**Tác nhân:** Claude Code (VS Code, Ultracode). Phiên chính điều phối, thêm khoảng 15 workflow nhiều agent:
- build trong worktree;
- review đối kháng, rồi một vòng sửa;
- verify live;
- dry-run dữ liệu.

Agent con chỉ commit. Push, PR, merge, Terraform apply, DB Migrate, ECS exec và ghi Linear đều do phiên chính làm.
**Audit / bằng chứng:** `docs/audits/2026-10-16-S239-in-progress-audit/`. Mỗi issue một thư mục; video nằm trên S3, danh sách trong `VIDEOS.md`.

## Trạng thái cuối phiên
- **ECS CIS:** api :642 / worker :199, cùng image `b478a18b` (#770), COMPLETED, `/health` 200.
- **Booking:** :21 (`git_sha` a35792c), `/booking/health/ready` = bk-012.
- **TripPlanner:** Lambda từ #92.
- **Migration áp trong phiên** (đều qua DB Migrate check → apply, `shared.job` rỗng):
  - CIS **237** (RLS `tenant_integrations`), **238** (Cohere global profile), **239** (aa_app_user đọc master + NULLIF + REVOKE), **240** (fallback Cohere acc3);
  - TP **tp-011 / tp-012** (guest token băm);
  - Booking **bk-012** (retention).
- **Terraform apply có target** (đọc plan trước khi apply):
  - #142: gỡ `aa-cis-dev-role`.
  - #144: CNAME booking.
  - #145: WAF enforce + che header trong log.
  - #147: IAM Lambda TP cho Cohere global.
  - #149: Booking `STAFF_ADMIN_URL`.
  - #150: lịch retention 20:30 UTC + lifecycle `archive/`.
  - #153: IAM invoker **acc3** cho Cohere.
- **acc3:** đã chấp nhận thoả thuận Marketplace Cohere Embed v4 (Nghiệp duyệt), trạng thái AVAILABLE 08:57Z.
- **Vercel:**
  - env domain mới (TP: site URL + 2 API URL; Booking: `BOOKING_API_URL`), redeploy production;
  - **Ignored Build Step** cho 3 project (`git diff HEAD^ HEAD --quiet -- .`): PR chỉ sửa backend → CANCELED, không build;
  - team chạm trần **~100 deployment/24h** (93 thấy được).
- **GitHub:** bật Allow auto-merge cho AA-Booking (5 check bắt buộc giữ nguyên).
- **Mapbox:** Nghiệp đặt URL restriction cho token TP; tiles/geocoding từ domain lạ → 403, bản đồ trên domain thật vẫn 200.
- **`shared.job`:** rỗng lúc dừng.

## Quyết định của Nghiệp
- Dọn issue In Progress: xong thì đóng có bằng chứng, chưa xong thì làm cho xong. Dev không có người dùng thật → không chờ mốc ngày hay grace window.
- Tập trung kỹ thuật và tính năng. Việc pháp lý/kinh doanh (AA-820) chỉ là đề xuất nhẹ cho chị Thư; có cần luật sư hay không do chị quyết.
- UAT quay video, làm một lần sau khi xong phần kỹ thuật, cho cả 3 app (AA-855).
- Nhãn AI trên TripPlanner: **"Adventure Asia AI"** (rút gọn "AA AI").
- Duyệt hết đề xuất đầu phiên: 237 + flag; retention chạy thật cho các kind CIS; domain booking; AA-678 đóng qua root PR; DataForSEO giữ mật khẩu; WAF không chặn theo địa lý; AA-833 đóng.
- **Ops overview:** tạo issue cho admin CIS (AA-858, mở rộng `/admin/overview`). Ưu tiên chờ chị Thư.
- **Tắt auto mode và "làm luôn các việc cần tôi làm tay, kiểm tra đầy đủ":** mình tự sửa env Vercel và biến Terraform Booking, đọc lại từng giá trị.
- **AA-857:** chọn "chờ PR CIS sửa gốc trước", sau đó duyệt apply dry-run v4 (danh sách 10 Segment khai tử; 3 request test để nguyên).
- **AA-777 r7:** chạy dù cộng dồn ~$2.6 (vượt nhẹ $2.5).
- **Cohere (AA-856 → AA-862):** chuỗi cache → acc2 → acc3 → tìm theo từ khoá. **Bỏ acc1.** Xin lại quota acc2 sau vài tuần. Chưa tạo case quota Claude/GPT cho acc2.
- **Payer:** acc2 = **TrueIDC** (không dùng được LLM Bedrock), acc3 = **eCloudvalley** (dùng được LLM, đang trong chương trình **AWS Lift**, $250 tier 1), acc1 = tài khoản cá nhân Nghiệp (xin quota dễ nhất).
- Gom về 1 tài khoản là mục tiêu dài hạn. Tạo issue nghiên cứu **AA-864**, chưa đào sâu.
- Thêm service AWS nào cũng phải báo chi phí trước; không để chi phí hạ tầng tăng đột biến.
- **Đầu tháng 11:** audit chi phí tháng 8/9/10.
- Dừng phiên: cập nhật Jira (nháp chờ duyệt), lập danh sách việc phiên sau.

## Thay đổi Codebase
- **CIS:**
  - #755 AA-791; #756/#759 AA-668; #757 AA-701; #758 AA-831; #760 mig 237; #761 F9 sticky pass + cắt câu attempt 3;
  - #762 seed Slate theo địa danh của Subject + guard nước theo component;
  - #763 mig 238; #764 nút override retention; #765 fail-closed toàn bộ route tenant pool + pool đúng CONNECTION LIMIT;
  - #766 mig 239; #767 sentence repair không thêm số/giờ/nhịp + gộp finding chồng nhau + giữ câu cảnh báo nguy hiểm;
  - #768 chống trùng id Segment giữa các nước + chỉ đổi nhãn id được claim + Subject theo alias;
  - #769 sàn override 21 ngày + tháng đã đóng; #770 mig 240 + client acc2 chỉ thử 1 lần.
- **TripPlanner:**
  - #84 tp-011; #85 guest token; #86 nhãn AI + guard narration; #87 "Adventure Asia AI"; #88 popover;
  - #89 đóng grace; #90 tp-012; #91 cache embed + fallback từ khoá; #92 client satellite embed.
- **Booking:** #19 CONTEXT ranh giới AI; #20 bảng; #21 modal footer; #22 bk-012; #23 retention kinds (redact theo allowlist).
- **Infra:**
  - bản copy migration #141/#143/#146/#148/#151/#152/#154;
  - IAM/IaC #142/#144/#145/#147/#149/#150/#153.
- **Gốc:** #86 (audit S239, `ecosystem-architecture.md` cho Booking, 5 bài học, `.gitignore` video); PR cuối phiên (log này, backlog, nháp Jira).

## Linear
- **Done** (có bằng chứng trong comment):
  - AA-792, 778, 771, 772, 681, 708, 756, 763, 807, 843, 701, 791, 683, 822, 823, 679, 802, 668, 831, 768, 801, 828, 833, 827, 806, 841, 714;
  - **AA-856, 818, 819, 817, 825, 857, 862, 678**.
- **Còn In Progress:** **AA-777**. r7 đạt 20/20 bài duyệt, 0 F9 hold, AA-768 5/5; chỉ "retry thêm lỗi mới" 13% > 8%. Chờ Nghiệp chốt đóng.
- **Issue mới:**
  - AA-844 → 855 (đầu phiên);
  - AA-856, 857, 858 (Ops overview);
  - AA-859 (tenant pool đợt 2), AA-860 (X1 tách role), AA-861 (xoá PII outbox TP, chờ AA-751);
  - AA-862 (Cohere acc3, Done), AA-863 (admin xem seed place), AA-864 (nghiên cứu gom về 1 tài khoản).

## Bằng chứng verify (tóm tắt)
- **AA-856/862:** burst 15 luồng × 60 giây, truy vấn khác nhau.
  - Truy vấn mới semantic: 32 → **429**; từ khoá 456 → 66; **0 lỗi 5xx**.
  - acc3: 396 embed OK/phút. Probe acc3 cosine = 1.0 so với acc2.
- **AA-857:**
  - Segment lẫn nước 96 → **0**, kể cả khi đếm mọi trạng thái. Verify **PASS**.
  - Đã tách 2.870 dòng; chạy lại 652/652 tour, 0 lỗi. Snapshot `scripts/restore/aa857_20261016T080718Z.json`.
  - Bài T9 viết thật trên Subject đã sửa đúng địa danh (Zorig Chusum, Thimphu).
- **AA-817:**
  - Probe từng bảng với GUC giả, chạy với role aa_app_user: trước 239 là 63 pass / 12 khoảng hở đã biết; **sau 239 là 75/75, 0 FAIL**.
  - Kiểm API 29/29; 24 request đều `used_tenant_pool=True`.
- **AA-825:**
  - Chạy thật 200 dòng/bảng: rollup bằng đúng số gốc trước khi xoá ($26.794948). File S3 `rows=200`, mã hoá AES256.
  - EXPLAIN đạt. Lịch chạy invoke OK.
  - Booking DRY RUN 2 kind (0 dòng ứng viên).
- **AA-818:**
  - TLS đạt trên 4 host; canonical/sitemap theo domain mới; `/booking/health/ready` 200;
  - đăng nhập Booking và trang Cases có 8 trip case (có ảnh chụp).
- **AA-777 r7:** 20/20 duyệt, $1.27.
- **Chi phí LLM của phiên:** khoảng **$3.6**:
  - AA-768 $0.28; AA-668 $0.40; A/B judge $0.12; r6 $1.23; r7 $1.27; T9 live $0.06; F19 + probe ≈ $0.01;
  - trước đó có smoke/narration ~$0.2.

## Còn lại (chưa xong)
- **Rotate admin secret.** Lý do: log WAF cũ (giữ 30 ngày) còn giá trị cũ dạng chữ thường. Cần làm đồng bộ 5 chỗ: Secrets Manager, ECS api/worker force-new-deployment, Vercel `aa-cis-frontend` `ADMIN_SECRET`, GitHub secret `ADMIN_SECRET` của CIS, Lambda DFS (Terraform data source). Đã soạn sẵn kế hoạch; hoãn vì trần build Vercel (frontend phải redeploy mới nhận secret mới). Auto mode cũng chặn bước ghi secret.
- **AA-777:** Nghiệp chốt đóng hay mở follow-up cho tỉ lệ re-flag F9_cta_fact.
- **TripPlanner `.claude/CLAUDE.md`:** vẫn ghi chuỗi Cohere "acc2 → acc3 → acc1" và Mapbox "DEFERRED". Cần sửa: bỏ acc1, Mapbox đã đặt restriction.
- **Vercel:** kiểm deployment CANCELED (bị Ignored Build Step bỏ qua) có bị tính vào trần 100/ngày không.

## Lưu ý kỹ thuật cho phiên sau
- **Id Segment có thể trùng giữa các nước:** id được băm theo (địa danh, động từ, nước) lúc tạo, nhưng nhãn có thể đổi sau đó. Đã chặn ở #768.
- **Dry-run dữ liệu phải có cổng chặn đổi nhãn:** bản v3 đổi tên 43 Segment, v4 mới đúng.
- **Phân tích output ECS exec:** stdout lẫn log structlog có dấu ngoặc nhọn, nên đọc JSON đầy đủ từ S3, đừng cắt `{…}` từ stdout.
- **Đừng chạy hai vòng job xen kẽ trên `shared.job`:** r7 và apply AA-857 chen nhau lúc 08:07. Phải tách hẳn: chờ hàng job trống thật sự trước khi chạy cái thứ hai.
- **Marketplace model (Cohere) tính theo từng tài khoản:** acc3 phải `create-foundation-model-agreement` thì role satellite mới gọi được. Quota cũng tính theo tài khoản.
- **Test integration chạy theo tên file:** test sau có thể thấy dữ liệu do module trước để lại (aa712 tạo lại route `a3_place_embed`), nên test migration nên tự chạy lại migration (vốn idempotent) trước khi kiểm.
- **Agent trong workflow có thể bị lạc đề** khi Nghiệp nhắn giữa lượt. Thêm dòng "YOUR ONLY JOB…" vào prompt, và kiểm worktree/commit tồn tại trước khi tin kết quả review.
