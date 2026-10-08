# Session Workflow — AA-Ecosys (quy tắc bắt buộc)

Quy tắc vận hành session do Nghiệp chốt. Áp dụng cho MỌI phiên trong workspace này.

Chi tiết đầy đủ (nghi thức, mẫu, bẫy) nằm trong `skill/` — đây là bản tóm tắt luôn-nạp,
trỏ tới skill là nguồn sự thật. Khi lệch, skill thắng.

## Nguồn trạng thái (3 nơi, phải đồng bộ)
1. **Memory Notion** — `Program Brain / memory.md` (workspace `AA_Ecosys`), đánh số `S<n>`, mới nhất ở ĐẦU.
   Chỉ thao tác trong **Program Brain**; KHÔNG đụng QS-WS / QuanRobotics.
2. **Log session local** — `docs/sessions/YYYY-MM-DD-<chu-de>.md` + index `docs/sessions/README.md` (giữ tiếng Việt).
3. **Linear** — workspace + team `AA_Ecosys`.

Khi nguồn lệch nhau: repo > Notion trang canonical > memory > skill. Báo lệch cho Nghiệp, không tự im lặng.

## Bắt đầu / kết thúc phiên → `skill/aa-session/SKILL.md`
- "bắt đầu session mới": đọc memory HOT + log local + Linear, kiểm trạng thái thật (STS, ECS api/worker cùng SHA,
  `shared.job` queued/running), rồi **đề xuất 5–10 issue** chờ Nghiệp chốt trước khi làm.
- "dừng session này": prepend session block vào memory HOT (chỉ prepend, không rotate tay), log local,
  đồng bộ Linear, đưa **mọi repo (gốc + 3 con) về main/master cây sạch**; root PR chờ thì merge tay
  (`gh pr merge <n> --squash`) hoặc hỏi Nghiệp.

## Nguồn sự thật khi thiết kế — CONTEXT.md (BẮT BUỘC)
Trước khi thiết kế/sửa code một repo, ĐỌC `CONTEXT.md` của repo đó và bám sát (stack, ranh giới, ownership).
`docs/ecosystem-architecture.md` cho cả hệ sinh thái. Thay đổi kiến trúc/ranh giới → cập nhật CONTEXT.md cùng phiên.
Code lệch CONTEXT.md = mâu thuẫn cần làm rõ, không bỏ qua.

## Bài học (lesson log) → `skill/aa-lessons/SKILL.md`
Gặp lỗi do làm/code sai cách hoặc giả định sai → **ghi ngay** 1 nguyên tắc vào `skill/aa-lessons/lessons.md`
(nguyên tắc — triệu chứng → nguyên nhân (phiên, issue). Bắt bằng: …). Trước khi sửa một vùng code, đọc mục của vùng đó.
Bài học kiểm được bằng test/CI → làm guard, rồi xoá dòng.

## ADR đặt ở repo nào → `skill/ai-nghiep/references/adr.md`
Hỏi "đảo ngược quyết định này thì repo nào phải sửa?": ≥2 repo → `AA-Ecosys/docs/adr/`; chỉ hạ tầng →
`infra/AA-CIS-Infra/docs/adr/`; chỉ 1 app → `apps/<repo>/docs/adr/`. ADR con trích dẫn ADR hệ sinh thái nó triển khai.

## Định nghĩa "XONG" + merge/deploy → `skill/aa-ship/SKILL.md`
Merge + CI xanh CHƯA đủ. Issue có code backend chỉ Done khi: merge + CI xanh + deploy Dev **rollout COMPLETED**
+ **verify endpoint live** (curl 200 + shape). Commit/PR dùng `Refs AA-xxx` (KHÔNG `[AA-xxx]`/`Fixes` — tự đóng issue).
Không merge/deploy backend khi `shared.job` còn job hoặc đang có wave (CI tự chặn; override chỉ Nghiệp, ghi lý do).

## Linear → `skill/aa-linear-issue/SKILL.md`
HỎI Nghiệp trước khi tạo issue mới. MỌI issue gắn 1 project; 1 project tối đa 50 issue (gần ngưỡng → hỏi).
Cập nhật trạng thái khi có tiến độ thật + bằng chứng, không Done khống.

## Jira (chị Thư / người ngoài team) → `skill/aa-jira-update/SKILL.md`
Mọi comment Jira: nháp → Nghiệp duyệt → mới đăng. Ngắn gọn, đứng tên Nghiệp (không nhắc tên agent),
không mã Linear nội bộ, tag `@thule` bằng ADF/html mention node. KHÔNG tự tạo issue Jira, KHÔNG tự đổi trạng thái khi báo tiến độ.

## Quyền MCP (Nghiệp đã cấp)
- Notion: đọc + ghi (update memory, comment).
- Linear: đọc + cập nhật trạng thái + tạo issue + comment.

## Ngôn ngữ → `.kiro/steering/language-convention.md`
Trao đổi với Nghiệp tiếng Việt; code/PR/Linear/tài liệu kỹ thuật tiếng Anh; log session + memory Notion giữ tiếng Việt.

## DB → `.kiro/steering/db-schema.md` + `skill/aa-cis-schema/SKILL.md`
Không nhớ/đoán tên bảng-cột — đọc `docs/architecture/db-schema-reference.md` (dump live). Xoá dữ liệu vĩnh viễn
theo quy trình DRY RUN (`skill/aa-cis-schema/references/destructive-ops.md`).

## Script gọi LLM chạy tay — PHẢI ghi cost
Script adhoc gọi Bedrock/OpenAI (A/B, threshold, backfill…) phải qua `LLMClient.generate()` và ghi
`shared.llm_call_log` (`record_call_sync`/`record_call_with_pool`, `stage="adhoc_<issue>"`, `role` chỉ
`writer`/`judge`/`validate`). Không gọi thẳng boto3. Lý do: AWS vẫn tính tiền, không log thì không truy được nguồn (AA-635).

## Chờ CI/deploy — KHÔNG poll liên tục
Chờ 1 khoảng đủ dài (CI ~3–5′, ECS ~2–5′, Vercel ~1–2′) rồi kiểm 1 lần; ưu tiên `gh pr checks <n> --watch`.
Không tạo nhiều lệnh `sleep N; check` chồng chéo hay mở terminal song song để poll dồn dập.

## Lưu ý kỹ thuật (môi trường)
- Chạy git/terraform từ đường dẫn WSL `/home/nghiep/...` (KHÔNG dùng UNC `\\wsl.localhost`).
- terraform/boto3 cần MFA: `export $(aws configure export-credentials --profile aa365-admin --format env | xargs) && unset AWS_PROFILE` rồi chạy.
- AA-CIS-App có branch protection (5 CI job) → merge PR dùng `gh pr merge --auto`. Repo gốc merge tay (lệ root PR).
- MCP config ở `.kiro/settings/mcp.json` (gitignored). Linear endpoint `/mcp` (KHÔNG `/sse`).
- File tạm ghi TRONG workspace tại `/home/nghiep/projects/AA-Ecosys/.tmp-session/` (đã gitignore), KHÔNG ghi ra `~/`. Dọn sau khi dùng.
- Google API key `aa-cis/dev/gdrive-photo-reader` KHÔNG cần đổi (đã bịt rò rỉ từ PR #535 — Nghiệp chốt 02/10/2026).

## Đánh số phiên
Tiếp nối chuỗi trong memory Notion (nguồn chuẩn). Ghi rõ tác nhân (Kiro / Claude Chat / Claude Code) mỗi entry.
