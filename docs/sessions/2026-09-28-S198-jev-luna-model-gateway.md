# S198: Jev (TypeSafe), GPT-6 Luna, Claude/Bedrock, thiết kế Model Gateway

- **Ngày:** 27–28/09/2026
- **Tác nhân:** Claude Code (cloud session, Nghiệp dùng điện thoại)
- **Người duyệt:** Nghiệp

## Trạng thái

Chỉ nghiên cứu và thiết kế. **Không đổi code app, không đổi hạ tầng.**

- **Jev API:** chưa gọi được thật. Cloud env chặn `*.typesafe.ai` (proxy trả 403).
  - Nghiệp đã chuyển Network access sang **Custom**, allow `api.typesafe.ai` và `docs.typesafe.ai`.
  - Thay đổi này chỉ có hiệu lực ở **session mới**.
- **Linear:**
  - Project mới **P-AA-11 "LLM Model Gateway & Decision Layer"** (Nghiệp duyệt, vì P-AA-10 và P-AA-8 đều đã 50/50).
  - **AA-642** [EPIC] Model Gateway.
  - **AA-643** Jev eval offline.
  - **AA-644** GPT-4.1 → GPT-6 Luna cho judge.
  - **AA-645** Sonnet 5 cho writer.
  - Comment: AA-634 (S198 part 1/2/3), AA-616, AA-518.
- **Notion:** memory S198 đã prepend.

## Thay đổi Codebase

Repo gốc (nhánh `claude/jev-codebase-api-test-u3onvv`):
- `docs/research/jev/jev_smoke.py`: smoke test Jev dùng `typesafe-sdk` 0.7.2. Key đọc từ env `TYPESAFE_API_KEY`, **không commit key**.
- Log này và dòng index trong README.

## Thay đổi Hạ tầng

Không có. Riêng cloud environment của Claude Code (không phải AWS): Network access đổi sang Custom.

## Nội dung chính

### Jev (TypeSafe System One)

- **API**, đọc từ SDK chính thức:
  - `POST https://api.typesafe.ai/v1/systemone`, header `Authorization: Bearer`, model `jev-latest`.
  - Request gồm `state` và `questions`, với 3 loại câu hỏi: Noul (xác suất có/không), Choice (1 nhãn + xác suất từng nhãn), Score (thang bậc).
  - Không trả được chuỗi tự do.
- **Nhánh `add-the-typesafe-skill` của chị Thư** (`thule78/aa-soscial-media`, Nghiệp gửi dạng zip):
  - Dùng Jev làm **cổng Noul chặn dữ liệu rác trước khi mua hoặc đếm**:
    - ticket 03: keyword có thật sự thuộc địa điểm không, hỏi trước khi mua DataForSEO;
    - ticket 04: câu hỏi PAA có đúng quốc gia không;
    - ticket 05: landing có đúng khoảnh khắc không.
  - Seam `Judge` tách riêng khỏi `LLMClient`; mọi xác suất đều được lưu.
  - **Chị tự đo: đồng thuận với người chấm chỉ 51%.** Floor 0.15 chưa hiệu chỉnh.
- **CIS có đủ 3 lỗ hổng này.** Riêng `land_questions_for_segment()` còn lỏng hơn bản gốc.
- **Ứng viên Jev theo từng stage:** xem comment S198 trên AA-634. Nổi bật:
  - T3 grounding: regex bắt nhầm kéo theo viết lại cả tour.
  - F8: đã chuyển sang WARN nhưng vẫn gọi GPT-4.1 mỗi lần.
  - T8 `rank_angles`: chỉ kiểm LLM có chép nguyên văn câu hỏi hay không.
  - `compute_demand`: gán volume chỉ vì trùng một từ.
  - `facts.py`: nhồi toàn bộ facts vào prompt.
  - A0 `column_mapper`.
  - TripPlanner `verify.py`.

### GPT-6 Luna

- Ra mắt 22–23/09/2026. Giá $0.10/$0.50 cho 1M token vào/ra, so với GPT-4.1 là $2/$8, tức rẻ hơn khoảng 16–20 lần.
- Code không dùng GPT-4.1-mini ở đâu cả.
- **Phát hiện:** UI LLM Models chỉ điều khiển được `s1_brand_audit`. Hai chỗ còn lại hardcode GPT-4.1:
  - `brand_fit.py` (dùng cho s1_judge và Debate);
  - `judge_client.py` (dùng cho F8/F9/N7).
- **Rủi ro khi đổi:**
  - Luna là reasoning model, có thể không nhận temperature/seed, làm mất tính lặp lại của judge (AA-209).
  - Có thể phải dùng `max_completion_tokens` thay cho `max_tokens`.
  - Token reasoning tính như output.
  - `pricing.py` chưa có Luna → bị tính theo giá Sonnet.
  - Các ngưỡng chấm cần hiệu chỉnh lại.
- **Khuyến nghị:** A/B trên dữ liệu thật trước. Đổi F8 và Debate trước, F9 `cta_fact` để sau cùng.

### Claude / Bedrock

- **Writer hiện tại:** Sonnet 4.5 (acc2 native), Sonnet 4.6 (satellite), Haiku 4.5.
- **Sonnet 5:** list price $2/$10, rẻ hơn Sonnet 4.6 ($3/$15).
  - Sonnet 5 bỏ temperature, budget_tokens và prefill. CIS gửi Bedrock không kèm temperature và không dùng prefill, nên tương thích.
  - Cần kiểm tra inference profile trên acc3/acc1.

### Model Gateway (AA-642)

- **Vấn đề:** hiện có 6+ cơ chế gọi model khác nhau.
- **Thiết kế đề xuất:**
  - Catalog model là nguồn duy nhất cho dropdown UI và bảng giá.
  - Route theo stage, có fallback và shadow model.
  - 3 seam riêng: `generate` / `decide` / `embed`.
  - Bảng `decision_log` lưu xác suất của Jev.
  - Guard vendor judge ≠ vendor writer.
- **Lộ trình:** 6 phase P0–P5.

## Bằng chứng verify

- Đọc source `typesafe-sdk` trực tiếp.
- `jev_smoke.py` chạy pass với MockTransport (body request đúng định dạng).
- Gọi thật → `TypeSafeAPIConnectionError: 403`.
- Mọi đường dẫn file trong phân tích đều đọc từ code thật: App `c5b8c6f`, TripPlanner `b60d14e`, zip nhánh của chị Thư.

## Còn lại

1. Chạy smoke test Jev bằng key thật, trên session cloud mới hoặc WSL:
   ```
   pip install typesafe-sdk
   TYPESAFE_API_KEY=... python docs/research/jev/jev_smoke.py
   ```
2. Họp chị Thư về P-AA-11, ADR 0007 (verdict không kèm trích dẫn), DPA/ZDR khi gửi nội dung tenant sang TypeSafe.
3. AA-644: kéo khối lượng gọi GPT theo stage từ `llm_call_log` trước khi hứa con số tiết kiệm.
4. Việc tồn: AA-599/600/601, AA-641. (PR #6 của S197 đã merge.)

## Phần 2 — Đồng bộ git local ↔ GitHub (28/09/2026, Claude Code trên VSCode/WSL)

Nghiệp yêu cầu kiểm tra codebase local so với GitHub ở 4 repo, rồi dọn sạch.

### Đã làm
- **Repo gốc:** local đang đứng trên nhánh `docs/s197-session-log` (đã merge), `master` thiếu 5 commit (PR #6, PR #7).
  - Checkout `master`, fast-forward lên `41a5752` (kéo về log S197/S198 + `docs/research/jev/jev_smoke.py`).
  - Xoá 2 nhánh local đã merge (`docs/s197-session-log`, `docs/s191-context-and-session-logs`).
  - `git remote set-head origin -a` (local chưa có `origin/HEAD`).
  - Grep `apikey_` trong `docs/`: không có key Jev nào trong repo.
- **TripPlanner:** `origin/HEAD` local còn trỏ `spec/v0.3-map-first` → set về `main`.
- **App — stash 09/09 (để lại trước AA-573):** notes verify sau merge AA-535/545/553/562/572 + 5 e2e spec live-verify (AA-561/565/567). Chưa có trong main.
  - **PR #450** (merged): áp đúng patch của stash lên main. Lần đầu chép đè cả file làm mất 37 dòng mới của `AA-572.md` → đã sửa bằng `git apply`, diff PR khớp stash từng dòng (+363/−2).
  - Không đưa lại mục LIVE STATE cũ (AA-551/554) trong `.claude/CLAUDE.md` của stash.
- **Infra PR #73** (merged): `.gitignore` thêm `accounts/*/lambda_src/*.zip` (output `archive_file.dfs_balance_check`). Không ignore `*.zip` toàn cục vì `dist/lambdas/*.zip` và `artifacts/placeholder.zip` đang được track.
- **Dọn nhánh local** (script do Nghiệp tự chạy vì auto mode chặn `git branch -D`/`git stash drop`):
  - Xoá nhánh đã merge/squash-equivalent với `origin/main`, hoặc còn nguyên trên origin mà local không đi trước. App còn ~440 nhánh → 10.
  - `git worktree prune`: 7 worktree cũ trỏ `projects/aa-cis/...`.
  - Drop stash sau khi PR #450 merge.
- **11 nhánh chỉ có ở local** (App 9: aa-103-e2e-ui, aa-156, aa-170-ui-v3, aa-437/438/439/440 audit, aa-477, aa-515; Infra 2: nat-instance, fix-account1-decommission) → Nghiệp chọn **push lên GitHub dạng `archive/<tên>`**, đối chiếu SHA remote = local rồi mới xoá local.

### Trạng thái cuối (verify)
| Repo | Nhánh | HEAD | vs origin | Nhánh local | Stash |
|---|---|---|---|---|---|
| AA-Ecosys | master | `41a5752` | 0/0 | 1 | 0 |
| AA-CIS-App | main | `fa062bc` | 0/0 | 1 | 0 |
| AA-TripPlanner-Web | main | `b60d14e` | 0/0 | 1 | 0 |
| AA-CIS-Infra | main | `594f8d6` | 0/0 | 1 | 0 |

Working tree sạch cả 4 repo, 1 worktree/repo, `.tmp-session/` trống.

## Lưu ý kỹ thuật

- **Auto mode chặn `git branch -D` và `git stash drop`** (Irreversible Local Destruction), kể cả trong script lớn → agent viết script, Nghiệp tự chạy. Riêng "push archive rồi xoá local sau khi đối chiếu SHA" thì chạy được khi Nghiệp yêu cầu rõ.
- Khôi phục stash lên main mới hơn: dùng `git diff stash^1 stash | git apply`, **không** `git checkout stash -- file` (ghi đè cả file, mất thay đổi mới của main).
- Terminal VSCode của Nghiệp là zsh trong Ubuntu → chạy thẳng `bash <file>`; tiền tố `wsl -d Ubuntu --` chỉ dùng từ PowerShell.
- Nhánh lưu trữ: `git checkout archive/<tên>` trên App/Infra.
- **Network access của cloud env:** menu environment → Edit.
  - Ô Environment variables chỉ nhận dạng `KEY=value`; domain phải nhập vào ô **Allowed domains** (mode Custom).
  - Sau khi chuyển sang Custom, kiểm tra GitHub/PyPI vẫn truy cập được.
- **Repo private của người khác (thule78):** chủ repo phải cài Claude GitHub App. Hai repo cùng tên không gắn chung một session được.
- **AA-351** (trial GPT-5.6) không có trong workspace Linear này, chỉ còn trong `docs/implementation-notes/` của App.
