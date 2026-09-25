# Session Workflow — AA-Ecosys (quy tắc bắt buộc)

Quy tắc vận hành session do Nghiệp chốt (16/09/2026). Áp dụng cho MỌI phiên Kiro trong workspace này.

## Nguồn trạng thái (3 nơi, phải đồng bộ)
1. **Memory Notion** — `Program Brain / memory.md` (workspace Notion `AA_Ecosys`). Nguồn sự thật theo phiên,
   đánh số `S<n>` (mới nhất ở ĐẦU trang). Chỉ thao tác trong **Program Brain**; KHÔNG đụng QS-WS / QuanRobotics.
2. **Log session local** — `docs/sessions/YYYY-MM-DD-<chu-de>.md` + index `docs/sessions/README.md`.
3. **Linear** — workspace `AA_Ecosys`, team `AA_Ecosys`. Issues/tasks.

## CONTEXT.md — nguồn sự thật khi thiết kế (BẮT BUỘC — Nghiệp chốt 21/09/2026)
- Mỗi repo có file `CONTEXT.md` mô tả chính xác repo đó (stack, layout, deploy, ranh giới, domain):
  `apps/AA-CIS-App/CONTEXT.md`, `apps/AA-TripPlanner-Web/CONTEXT.md`, `infra/AA-CIS-Infra/CONTEXT.md`;
  và `docs/ecosystem-architecture.md` mô tả cả hệ sinh thái.
- **Khi thiết kế / phân tích / sửa code cho một repo, PHẢI đọc `CONTEXT.md` của repo đó trước và bám sát**
  làm nguồn sự thật (design, ranh giới, ownership). Không thiết kế trái với CONTEXT.md; nếu thực tế code
  lệch CONTEXT.md → coi là mâu thuẫn cần làm rõ, cập nhật CONTEXT.md cho đúng, không im lặng bỏ qua.
- Khi thay đổi kiến trúc/chức năng/ranh giới của repo → cập nhật `CONTEXT.md` repo đó (và
  `ecosystem-architecture.md` nếu ảnh hưởng liên-repo) trong cùng phiên, giữ 4 file này luôn khớp thực tế.

## Quyền MCP (Nghiệp đã cấp)
- Notion: đọc + ghi (update memory, comment).
- Linear: đọc + **cập nhật trạng thái + tạo issue + comment**.

## Lệnh "bắt đầu session mới"
Khi Nghiệp nói "bắt đầu session mới", TRƯỚC KHI làm gì khác:
1. Đọc **memory Notion** (`Program Brain/memory.md`) — lấy state phiên mới nhất (S<n>), việc-cần-làm-đầu-phiên.
2. Đọc **log session local** mới nhất trong `docs/sessions/`.
3. Xem **Linear** — list issues (backlog + in-progress + todo) để biết việc đang mở.
4. Tổng hợp ngắn gọn (bảng/gạch đầu dòng) cho Nghiệp: state hiện tại + đề xuất việc làm phiên này. Chờ Nghiệp chốt.

## Trong khi làm
- Khi cần tạo task/lưu việc/plan → **HỎI Nghiệp trước khi tạo issue Linear mới**. Không tự ý tạo.
- Plan công việc, tư vấn, trao đổi để Nghiệp duyệt trước khi thực thi việc lớn/rủi ro.
- Cập nhật trạng thái issue Linear khi có tiến độ thật (kèm bằng chứng), không set Done khống.
- **Định nghĩa "XONG" một issue có code backend (BẮT BUỘC — Nghiệp chốt 19/09/2026):** merge PR + CI xanh CHƯA đủ.
  Phải verify TIẾP: (a) deploy Dev **rollout COMPLETED** (ECS `aa-cis-dev-api` chạy taskDef mới, deployment cũ đã rút),
  (b) **verify endpoint live thật** (curl endpoint mới → HTTP 200 + shape đúng). Chỉ khi cả 4 (merge + CI + deploy
  COMPLETED + endpoint live) mới comment "Done" kèm bằng chứng. FE deploy qua Vercel (check CI Vercel SUCCESS ở PR).

## Quy tắc Linear issue (BẮT BUỘC — Nghiệp nhắc nhiều lần)
- **MỌI issue mới PHẢI gắn vào 1 project** (không để trống project).
- **1 project tối đa 50 issue.** Trước khi tạo issue, kiểm số issue của project đích; nếu tạo sẽ vượt 50 → HỎI Nghiệp + tạo project mới.
- Vẫn giữ quy tắc: HỎI Nghiệp trước khi tạo issue Linear mới.

## Lệnh "dừng session này"
Khi Nghiệp nói "dừng session này":
1. **Ghi log local**: tạo `docs/sessions/YYYY-MM-DD-<chu-de>.md` (mục: Trạng thái, Thay đổi Codebase,
   Thay đổi Hạ tầng, Bằng chứng verify, Còn lại, Lưu ý kỹ thuật). Cập nhật `docs/sessions/README.md` (index).
2. **Cập nhật memory Notion**: prepend phiên mới `S<n+1>` vào ĐẦU `Program Brain/memory.md`
   (format bảng/gạch đầu dòng; việc đã làm + việc cần làm đầu phiên sau + lưu ý). KHÔNG tự rotate HOT→Archive
   (Nghiệp tự làm tay; nếu trang quá dài thì HỎI trước).
3. **Đồng bộ Linear**: cập nhật trạng thái issue đã đụng, comment tiến độ, tạo issue cho việc còn treo (sau khi hỏi).
4. Đảm bảo 3 nguồn (Notion memory, log local, Linear) + trạng thái repo nhất quán với nhau.

## Đánh số phiên
- Tiếp nối chuỗi trong memory Notion (nguồn chuẩn — số dưới đây chỉ để tham khảo nhanh).
  Phiên gần nhất: **S197** (25/09/2026, Claude Code). Phiên tiếp theo là S198...
- Ghi rõ tác nhân (Kiro / Claude Chat / Claude Code) trong mỗi entry vì memory dùng chung nhiều agent.

## Lưu ý kỹ thuật (môi trường)
- Chạy git/terraform từ đường dẫn WSL `/home/nghiep/...` (KHÔNG dùng path UNC `\\wsl.localhost`).
- terraform apply cần MFA: `export $(aws configure export-credentials --profile aa365-admin --format env | xargs) && unset AWS_PROFILE` rồi chạy (TF không tự prompt MFA).
- AA-CIS-App có branch protection (5 CI job) → merge PR dùng `gh pr merge --auto`.
- MCP config ở `.kiro/settings/mcp.json` (gitignored, chứa token). Linear endpoint dùng `/mcp` (KHÔNG `/sse`).
- **File tạm (scratch) ghi TRONG workspace, KHÔNG ghi ra `~/` (Nghiệp chốt 19/09/2026):** đặt ở
  `/home/nghiep/projects/AA-Ecosys/.tmp-session/` (đã thêm vào `.gitignore` repo gốc). Lý do: Kiro LUÔN hỏi allow khi
  đọc file NGOÀI workspace, kể cả khi autopilot bật (autopilot chỉ bỏ xác nhận cho hành động TRONG workspace) — ghi ra
  `~/` làm phiền vì mỗi `read_file` bị hỏi. Ưu tiên đọc output ngắn thẳng qua `get_process_output`; chỉ ghi-file-rồi-đọc
  khi output dài. Dọn `.tmp-session/` sau khi dùng.

## Script gọi LLM chạy tay — PHẢI ghi log chi phí (Nghiệp chốt 24/09/2026, từ AA-635)

Mọi script chạy tay có gọi Bedrock/OpenAI (A/B so model, đo threshold, thử prompt, backfill…),
dù chạy local hay qua ECS exec:

- **Gọi qua `LLMClient.generate()`** (`shared/llm_client/client.py`), KHÔNG gọi thẳng
  `boto3 bedrock-runtime` / `invoke_model` / `invoke_claude()`.
- **Ghi `shared.llm_call_log`** cho từng lời gọi bằng `record_call_sync()` /
  `record_call_with_pool()` (`shared/llm_client/call_log.py`), `stage="adhoc_<issue>"`
  (vd `adhoc_aa619`), `role` chỉ được `writer`/`judge`/`validate` (CHECK constraint — tên khác bị
  từ chối âm thầm, mất log).
- Lý do: AWS vẫn tính tiền, nhưng nếu không log thì trang External Spend thấp hơn hoá đơn và
  không truy được nguồn. Bằng chứng: 18/09 script A/B (AA-619/620) gọi thẳng Bedrock → $0.83 trên
  bill acc3 không có dòng log nào (AA-635).

## Chờ CI/deploy — KHÔNG poll liên tục (Nghiệp chốt 23/09/2026)

Khi chờ CI (`gh pr checks`), deploy (ECS rollout, Vercel), hay bất kỳ job chạy nền dài:

- **KHÔNG** tạo nhiều lệnh `sleep N; check` chồng chéo nhau, không tạo terminal mới liên tục để poll dồn dập.
- Chờ **1 khoảng đủ dài** dựa trên thời gian trung bình đã biết (CI full ~3-5 phút, ECS deploy ~2-5 phút,
  Vercel ~1-2 phút) rồi kiểm **1 lần**. Nếu chưa xong, chờ thêm 1 khoảng dài nữa — không rút ngắn dần
  xuống kiểu 30s/60s/90s liên tiếp.
- Dùng `control_bash_process` với `sleep <thời gian dài>` MỘT LẦN, không mở thêm terminal song song
  để "kiểm nhanh hơn" trong lúc cái cũ vẫn đang chờ.
- Nếu cần theo dõi tiến trình dài (nhiều job), ưu tiên `gh pr checks <n> --watch` (tự poll đúng nhịp)
  thay vì tự viết loop sleep/check thủ công.
- Mục tiêu: để CI/deploy chạy đúng nhịp tự nhiên của nó, không tạo cảm giác dồn dập/rối cho Nghiệp
  theo dõi qua tool call log.
