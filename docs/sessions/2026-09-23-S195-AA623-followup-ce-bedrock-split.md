# S195 — 2026-09-23 — AA-623 follow-up: Cost Explorer tách Bedrock vs hạ tầng + filter thời gian

**Tác nhân:** Claude Code.

## Trạng thái
Nghiệp đối chiếu panel AA-623 với CSV Cost Explorer tháng 9 của acc1/2/3, hỏi "acc2 lấy đâu ra
gọi Bedrock nhiều". Kết luận: acc2 KHÔNG gọi Claude — panel cũ gắn nhãn "(Bedrock)" cho TỔNG cả
account acc2 (ELB/ECS/RDS/ElastiCache/VPC/WAF…). Đã sửa + thêm filter thời gian, merge, deploy,
verify live khớp CSV.

## Thay đổi Codebase
- App PR **#429** (squash `55e48c5`): `shared/aws_client/cost_explorer.py` (NextPageToken
  pagination, `read_cost_range()` thay `read_latest_snapshot()`, `is_bedrock_service()`),
  `api/routers/admin_llm_ops.py` (`_resolve_window`: `days` preset hoặc `start`/`end` UTC, end
  inclusive, max 366 ngày, 422 khi đảo ngược — áp cho tree/calls/dfs-usage/by-country/spend-daily/
  cost-explorer/check), FE `/admin/llm-usage` (date picker toàn trang; panel CE: Bedrock actual vs
  Bedrock estimated acc1/2/3 vs infra, bảng per-account, top services, cảnh báo gap). Không migration.
- Notes: `apps/AA-CIS-App/docs/implementation-notes/AA-623.md` (local — `docs/` gitignored ở repo App).

## Thay đổi Hạ tầng
- Không đổi hạ tầng. Deploy Dev → ECS `aa-cis-dev-api:328` COMPLETED.
- MCP: dùng connector **claude.ai Linear / claude.ai Notion** (đã Connected); đã gỡ bản local trùng.

## Bằng chứng verify (live, ECS exec → localhost:8000)
- `POST /admin/cost-explorer/check?start=2026-09-01&end=2026-09-22` → 621 rows, 0 errors.
- 01–22/09: acc2 $98.51 (Bedrock $0.0053) = CSV; acc1 $1.68 (Bedrock $0.894) = CSV; acc3 $36.71 = CSV.
- 16–22/09: acc2 $31.66 (Bedrock $0.0009); acc3 $25.99; acc1 $0.86.
- Các endpoint khác nhận start/end → 200; range đảo ngược → 422. Nghiệp gửi screenshot panel mới OK.

## Đồng bộ Linear / Notion
- AA-623: comment bằng chứng follow-up (PR #429 tự gắn qua GitHub integration), giữ Done.
- **AA-635** tạo mới (Medium, Backlog, parent AA-616, project CIS Data Reset & Pipeline Rerun (Audit), 44/50).
- Memory Notion: đã prepend S195.

## Còn lại
- **AA-635:** log thiếu so với hoá đơn Bedrock 16–22/09 — acc3 thật $25.99 vs `llm_call_log` $20.86
  (~20% thiếu); acc1 thật $0.766 vs log **$0.009** (Haiku $0.73 ngày 17/09 không được log).
- ~~Nhãn FE `CE_ACCOUNT_LABEL` tiếng Việt~~ → ĐÃ SỬA: PR **#430** (squash `e30314e`) đổi sang
  "main infra" / "LLM satellite, primary" / "LLM satellite, fallback"; CI 5 job + Vercel prod SUCCESS,
  Deploy Dev → taskDef **329** COMPLETED.
- acc2 bị tính RDS/ECS MỌI ngày tháng 9 (~$4.5/ngày) → CLAUDE.md ghi "AWS: STOPPED" là sai; nhắc stop.
- `/admin/cost-explorer/check` vẫn chỉ chạy tay (không scheduler).
- AA-599/AA-594 (G4 rerun), AA-605, AA-628 — như S194.

## Lưu ý kỹ thuật cho phiên sau
- Chạy unit test local: cần env giống CI (`ci.yml`) + AWS creds giả (`AWS_ACCESS_KEY_ID=testing`,
  `AWS_CONFIG_FILE=/dev/null`) — không thì import app treo chờ MFA của profile `[default]`.
- Từ PowerShell gọi `wsl` rơi vào zsh login → quote/glob hỏng; viết script `.sh` rồi `wsl -- bash file.sh`.
  `npx` trong WSL trỏ sang npm Windows → dùng `node_modules/.bin/tsc|eslint` trực tiếp.
- `aws ecs execute-command` với stdin null → "Cannot perform start session: EOF"; giữ stdin mở bằng
  `sleep 90 | aws ecs execute-command ...`.
- CLI `claude` không có trên PATH Windows; binary nằm ở
  `%USERPROFILE%\.vscode\extensions\anthropic.claude-code-<ver>-win32-x64\resources\native-binary\claude.exe`.
