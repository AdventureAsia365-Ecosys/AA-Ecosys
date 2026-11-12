# S278 — 12/11/2026 — Công cụ giá Booking, rà bảo mật trước PII, dữ liệu E2E giả lập, Bedrock sang acc1

**Tác nhân:** Claude Code (VSCode/WSL, Ultracode). **Thời gian:** 12/11 ~06:30 → ~18:45 +07; đổi tài khoản Claude 2 lần,
3 cửa sổ tắt auto mode, MFA `aa365-admin` hết 18:27.

## Trạng thái

- **Done (có bằng chứng live):** AA-1049 (Done-with-scope), AA-1084, AA-1080, AA-1069, AA-960, AA-1081.
- **Mở lại:** AA-1088 (PDF M13 ngày đúng; case cũ còn tiêu đề placeholder → backfill đã live, chưa chạy).
- **Còn In Progress / In Review:** AA-1048, 1051, 1070, 1077, 1079, 1087, 1088, 1091, 1092, 1094, 1095 (chi tiết ở
  "Còn lại"). WIP vượt trần 8 (11 issue) vì phiên mở thêm issue từ audit hệ thống; phiên sau mở bằng lượt hội tụ.
- Số liệu live cuối phiên: xem `docs/audits/2026-11-12-S278-session-close/state-snapshot.md`.

## Quyết định của tech lead (trong phiên)

- 06:45 duyệt danh sách hội tụ; AA-1050 về Backlog; AA-1070 làm crm-35 + crm-13 trong phiên; trần trả phí 3,5 USD;
  AA-1048 "gom class trước, tách sau".
- 09:00–09:10 trang quyết định sau R7: 16/16 theo đề xuất; D14: không nhắc go-live với chị Thư, tự đánh giá tính năng
  + pilot tenant giả lập + UAT e2e.
- 11:40 duyệt 13 chính sách giá; luật: mọi giá trị chính sách sửa được trên trang Booking, không viết cứng (memory
  `policy-values-editable-not-hardcoded`).
- "Đo R1 rồi làm tiếp"; R1 trần 4 USD.
- AA-1092: đồng ý 2 chi phí ~1 USD/tháng (WAF REST stage + pool M2M).
- 15:45 acc3 vẫn bị AWS chặn ở cấp tài khoản; acc1 gọi được 13/13 model → **dùng acc1 cho Bedrock**: Claude vẫn ưu tiên
  Anthropic API (đang miễn phí), GPT dùng acc1 trước. Tạo AA-1095 (duyệt).
- acc1 giữ ngoài (độc lập), đầu tháng 12 xem lại việc vào org nào; acc4 chưa liên kết TrueIDC, chỉ acc2 dưới TrueIDC.
- Tạo role vào acc1 dự phòng `AA-BreakGlass-Admin` + profile `acc1-admin` (duyệt, tech lead đã thử OK).

## Thay đổi Codebase (PR đã merge)

- **CIS:** #1447 #1448 #1449 (slate song song + giữ cache) #1450/#1451 (399, độ dài blog vòng 1) #1452/#1453 (400, golden
  split) #1454 (bài held cần chủ xác nhận) #1456 (401, danh tính ghi E2E) #1457/#1458 (402/403 giá tham khảo có cấu trúc)
  #1459/#1460 (404 v_tenant_tour_v1, source_id) #1461 (A10b-4 add-on TripPlanner) #1462/#1463 (405, blog vòng 2: dàn ý
  ngân sách từ, cắt-rồi-mở-rộng, LEAK_RE) #1464 (seeder CIS + sen-vang synthetic) #1465 (406 connection acc1, tắt).
- **Booking:** #231 #232 #233 (workbench giá) #234 (bk-049 RLS) #235/#236 (bk-050/051 chính sách giá + trang Policy)
  #237/#238 (bk-052 + seeder E2E, A10e-1 huỷ departure synthetic, backfill case cũ) #239/#240 (bk-053, bind tenant B2B)
  #241 (bk-054/055 phiên bản giá + lịch mùa).
- **CRM:** #283–#296 (crm-059…062: inclusions, aa_cancel_case, tags, trần Book now; điều hành chuyến, PDF, rooming,
  passport, visa; sửa verify; spec aa-cancel).
- **TripPlanner:** #255 #256 #257.
- **Infra:** #783 #787 #789 #790 (WAF) #794 (`--end-cutover`) #797 (root acc1-bedrock + quyền assume).
- **Repo gốc:** #703 #704 #705 #709 #711 #712 #714 #716 #718 #719 #721 #726 #727 #730 #733.

## Thay đổi Hạ tầng

- WAF trên stage REST CIS + Booking và pool M2M (CI apply).
- Khoá ký assertion TripPlanner riêng; `--end-cutover` 10:10Z → khoá cũ bị từ chối (probe 401).
- acc1: bucket state `aa-cis-tfstate-acc1-bedrock-*`, role `AA1-Bedrock-Invoker` (chỉ invoke 13 model, tin task role CIS
  + ExternalId), role `AA-BreakGlass-Admin` (CLI, tag ManagedBy=manual-S278). aa365: quyền assume + env
  `BEDROCK_ACCT_PAYER` (CI apply 2 add / 1 change / 2 destroy task def). GitHub secret `BEDROCK_ACCT_PAYER_ID` (Infra).
- 3 user Booking E2E (staff/maker/checker).

## Jira

- Đã đăng (tech lead duyệt, kèm ảnh live): PR-25 (comment 10645), PR-26 (10646), PR-23 (10647), PR-24 (10648).

## Bằng chứng verify

- `.tmp-session/S278/verify/README.md` (sẽ chép vào `docs/audits/2026-11-12-S278-session-close/verify/`).
- AA-1081: slate 12,3 s / 0 lượt judge (trước 756–894 s / 344–362 lượt).
- AA-1048 R1: GPT-6 Luna extraction precision t2 0,27 (lb 0,21) / t9_blog 0,22 (lb 0,16), recall 40/45; llama4 0,09–0,13;
  chi 0,918/4 USD.
- acc1 vs acc3: acc1 13/13 model gọi được, quota 2M–30M TPM; acc3 7 model "not available for this account", quota 0.

## Còn lại (việc chưa xong)

1. AA-1095: ĐÃ bật connection acc1 + route v10 (theo họ model) + v11 (3 judge GPT-6 Luna trên Bedrock trước); probe 13/13
   ok. Còn: một lượt gọi stage thật ghi sổ với account acc1 (Dev không traffic) rồi đóng.
2. AA-1091: bk-054/055 đã áp; Booking #242 (code) coverage đã đủ 91,38% nhưng đỏ 1 test tích hợp
   `test_migration_of_todays_prices_keeps_every_price` sau khi đổi số → sửa rồi ship.
3. AA-1087 / AA-1088 / AA-1070 crm-13: chạy bước live (seeder Booking, e2e-writers, Partner aa-cancel, backfill case cũ
   DRY RUN → apply) — bị chặn vì ecsx local mode không đọc được kết quả từ container Booking/CRM.
4. AA-1094: mọi tenant giả lập kind=demo → TripPlanner phục vụ catalogue AA; sửa luật DEMO_KIND (dựa aa-tripplanner /
   content.internal), rồi gắn add-on cho audit-atlas-hearth và kiểm.
5. AA-1092: kiểm cross-tenant B2B live; tech lead quyết chi phí rủi ro 2 (CloudFront+WAF TripPlanner ~5 USD/tháng) và 3
   (rule rate theo người xem CRM ~1 USD/tháng/rule).
6. AA-1077: thử 3 bài v7 (đang chạy lại cuối phiên); bài Galle thiếu chất liệu → luật chọn chủ đề (seed tối thiểu).
7. AA-1048: agent panel xét 215 false positive ($0) trước lượt trả phí kế.
8. AA-1079 / AA-1051: theo AA-1048 / AA-1095.

## Lưu ý kỹ thuật cho phiên sau

- Không SendMessage vào agent trong Workflow lane (sinh bản sao) — dừng lane rồi chạy lại.
- Lane cùng app cần dải số migration rời nhau; khi đổi số sửa cả PR body `applies:`/`chain:`.
- `ECSX_SCRIPT_TIMEOUT` là tham số sau đường dẫn (ecsx.sh nay từ chối biến môi trường).
- Role chaining (acc1-admin) bị AWS giới hạn 1 giờ/phiên; CLI tự gia hạn từ phiên `aa365-admin` 12 giờ.
- Apply Terraform root acc1-bedrock: từ checkout Infra chính trên main, `-backend-config` bucket/profile + tfvars không
  commit (hook TF-1 chặn apply từ worktree).
