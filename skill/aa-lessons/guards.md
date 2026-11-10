# Bài học đã thành guard

Các dòng dưới đây từng nằm trong [`lessons.md`](lessons.md). Mỗi dòng đã có guard máy (test, CI check, hook, tool)
chặn cả lớp lỗi, nên được xoá khỏi sổ bài học (`SKILL.md` mục 4). Giữ ở đây để tra: trước khi gỡ hay nới một guard,
đọc dòng của nó. Nguồn: audit S271 `lessons-guards` (AA-1024), mỗi guard được kiểm là có trên `main` / `master` lúc xoá.

Guard mới thêm: dòng bài học mới ghi `Guard: <loại> <đường dẫn>` (`SKILL.md` mục 3); khi guard đã chặn được cả lớp
lỗi, chuyển dòng đó sang đây trong cùng PR.

## Cách làm việc

- **Prompt cho agent trong workflow phải nói rõ "chỉ làm task này"** (S239) → `tools/workflows/lane.js`
- **Số migration ghi trong plan chưa phải là đã giữ chỗ — lane song song lấy mất trong lúc mình code** (S246) (lỗi thời: đã thay bằng) → `apps/AA-CIS-App/.github/scripts/migration_preflight.py`
- **Nhánh xếp chồng sau khi nhánh dưới squash-merge: `git rebase --onto origin/main <SHA cũ của commit dưới>` — SHA mốc đổi sau mỗi lần rebase** (S243) → `tools/github/ship_train.py`
- **Danh sách trắng theo tên địa danh làm lọt tên người Việt** (S249) → `apps/AA-Partner/api/tests/unit/test_privacy_scrubber.py`
- **Giải xung đột rebase giữa hai khối try/except cùng thêm vào một chỗ thì phải đọc lại kết quả** (S250) → `apps/AA-CIS-App/.github/workflows/ci.yml`
- **Brief lane có lời gọi LLM mới phải nêu các guard toàn cục đã có trên `main` (vd. mọi `record_call` truyền `**billed_fields(resp)`)** (S260) → `apps/AA-CIS-App/tests/unit/test_aa1002_s6_billed_fields.py`
- **Nhiều lane cùng owner migration không được chia dải số trước — điều phối đánh lại số theo thứ tự merge thật (main max + 1)** (S266) → `apps/AA-CIS-App/.github/scripts/migration_preflight.py`
- **Tham số `args` của Workflow phải là JSON thật viết inline, không phải chuỗi giữ chỗ (`"__FROM_FILE__"`)** (S252) → `.claude/hooks/lane_start_guard.py`, `tools/workflows/lane.js` (args check) (guard mới S271, AA-1024)
- **Trước khi báo chi phí "LLM fallback" của một stage, kiểm `provider`/`model` trong `llm_call_log`** (S223) → `tools/llm/spend_by_stage.py` (cột LLM / non-LLM theo role) (guard mới S272, AA-1024)
- **Số chi phí từ `llm_call_log` phải đối chiếu với dashboard nhà cung cấp trước khi báo** (S223, S219, S224) → `tools/llm/spend_by_stage.py` (LOWER BOUND tới khi số `*_log_write_failed` = 0) (guard mới S272, AA-1024)
- **`git -C <repo> worktree add <đường dẫn tương đối>` tính đường dẫn từ `<repo>`, không từ thư mục đang đứng; không có `-C` thì tính từ cwd, mà cwd có thể đang là repo con** (S246, S247) → `.claude/hooks/aa_shell_guard.py` WT-1 (guard mới S272, AA-1024)
- **Usage limit 5 giờ có thể giết nhiều lane cùng lúc giữa chừng — chạy lại workflow bằng resume (`resumeFromRunId`) để giữ kết quả lane đã xong, chỉ chạy lại lane chết** (S257, S260, S269) → `.claude/hooks/lane_start_guard.py` (cho qua `resumeFromRunId`; lane mới trên worktree đã có cần resume: true), `tools/workflows/lane.js` (resumed_state) (guard mới S272, AA-1024)

## Verify và "Done"

- **Hàm reset dùng cho test phải đặt lại cả trạng thái thời gian cấp module (đồng hồ flush), không chỉ bộ đếm** (S246) → `apps/AA-CIS-App/tests/unit/test_aa660_decide.py`
- **Booking CI tính coverage ≥ 90% chỉ từ `tests/unit` — module mới chỉ có integration test kéo tổng xuống dưới ngưỡng** (S252) → `apps/AA-Booking/.github/workflows/ci.yml`, `tools/workflows/lane.js`
- **Partner `test_production_schedule_leaves_the_queue_idle...` bấp bênh theo thời điểm (một job định kỳ `crm_*` vừa đến hạn) — main xanh thì rerun, không sửa code PR** (S252) → `apps/AA-Partner/api/tests/integration/test_job_runner.py`
- **Atom hoá không có nghĩa là không bịa. Atom cần grounding riêng** (n/a) → `apps/AA-CIS-App/services/acp_contract/a3_atomize.py`, `apps/AA-CIS-App/tests/unit/test_aa694_demand_atom_gates.py`
- **Atomize chỉ có ở A3 platform (1 lần khi tour lên Master; tenant không bao giờ atomize — họ dùng atom/Segment/route/hub của platform)** (S224) (lỗi thời: đã thay bằng) → `apps/AA-CIS-App/services/acp_contract/a3_atomize.py`
- **"Đã lên gateway" phải kiểm theo đường gọi, không theo việc có ghi cost** (S224) → `apps/AA-CIS-App/tests/unit/test_aa685_no_raw_model_calls.py`
- **Fixture test chỉ dùng tên/địa danh hư cấu, không chép từ DB, audit hay prompt cũ** (S260) → `apps/AA-CIS-App/.github/workflows/ci.yml`
- **Thân PR chỉ ghi mã issue khi PR thật sự làm issue đó — Linear tự nối PR với mọi mã nhắc tới và có thể tự chuyển issue sang Done khi merge** (S243, S244) → `.github/workflows/pr-title.yml` (mọi repo), `tools/github/ship_open_prs.py` (validate) (guard mới S272, AA-1024)
- **Tiêu đề PR không được ghi mã issue ngay sau tiền tố `fix:` — Linear đọc "fix: AA-847 …" là câu đóng issue "fix AA-847" và tự chuyển Done khi merge** (S246) → `.github/workflows/pr-title.yml` (mọi repo), `tools/github/ship_open_prs.py` (validate) (guard mới S272, AA-1024)
- **Linear vẫn tự chuyển Done khi không có câu đóng issue nào** (S246) → `tools/linear/done_audit.py` (cuối phiên, `skill/aa-session`) (guard mới S272, AA-1024)
- **Trước khi chuyển Done, đọc lại "Done when" trong mô tả issue, không dựa vào việc PR đã merge** (S233) → `tools/linear/done_audit.py` (guard mới S272, AA-1024)
- **Tham số / id của `pytest.mark.parametrize` phải tất định — không dùng giá trị sinh lúc import (`uuid4()`, `time`)** (S276) → `apps/AA-CIS-App/tests/unit/test_s276_parametrize_determinism_lint.py` (guard mới S277, AA-1024)

## Vận hành

- **`UnblendedCost` của Cost Explorer đã trừ credit/refund vào từng service — tài khoản trả bằng credit (acc3 từ 29/10) hiện ~$0 hoặc âm cho ngày dùng thật** (S260) → `apps/AA-CIS-App/shared/aws_client/cost_explorer.py`, `apps/AA-CIS-App/tests/unit/test_aa1002_s10_budget_reconcile.py`
- **`gh run watch` có thể treo trên run đã xong (21 phút, S252 window11) và `mergeq.sh` đợi mãi khi PR thành DIRTY** (S252) → `tools/github/ship_merge.py`
- **WAF CommonRuleSet: link tương đối `../` trong nội dung (HTML href/src hoặc markdown) khớp `GenericLFI_BODY`, không phải XSS** (S235, S239) → `infra/AA-CIS-Infra/modules/waf/main.tf`
- **Script ECS exec tải về `/tmp` phải tự thêm `/app` vào `sys.path`** (S252) → `tools/ecs/ecsx_runner.py`
- **Task chạy trong process API chết khi deploy và không hiện trên trang Jobs** (n/a) → `apps/AA-CIS-App/tests/unit/test_aa650_job_runner.py`
- **Deploy phải cập nhật cả worker** (S211) → `apps/AA-CIS-App/.github/workflows/post-deploy-verify.yml`
- **Repo có branch protection strict (CIS, Booking, AA-Partner): nhiều PR thì merge nối tiếp — PR còn lại thành BEHIND và auto-merge đứng im** (S222, S248, S250, S251) (lỗi thời: đã thay bằng) → `tools/github/ship_merge.py`
- **Input `migration` của DB Migrate là đường dẫn có owner (`cis/250_x.sql`), không chỉ tên file** (S243) → `tools/github/dbmig.sh`
- **Repo gốc không có required check: chờ Docs lint xanh rồi mới `gh pr merge`** (S245) → `tools/github/ship_merge.py`
- **Booking/AA-Partner deploy ở mọi push vào main chạm đường backend, nên PR code cần migration mới không được merge trước khi migration apply** (S249, S256) → `infra/AA-CIS-Infra/tools/github/infra-main-ruleset.json`, `apps/AA-CIS-App/.github/scripts/schema_gate.py`
- **PR repo gốc không có check bắt buộc: đọc `gh pr checks` trước khi merge** (S249) → `tools/github/ship_merge.py`, `tools/docs/check_frontmatter.py`
- **Script helper `source .tmp-session/s247/common.sh` không được dùng lại tên biến của nó (`R`, `RI`, `O`, `H`, `P`, `B`)** (S249) (lỗi thời: đã thay bằng) → `tools/github/ship_merge.py`, `tools/github/ship_train.py`, `tools/github/ship_copy_apply.py`
- **Không đưa account ID thật vào test/code của repo app public** (S252) → `apps/AA-CIS-App/.github/scripts/check_resource_ids.py`
- **Auto mode chặn `git push --force-with-lease` sau rebase — đưa bản rebase lên nhánh PR bằng merge, không force-push** (S252) → `tools/github/ship_train.py`
- **`aws ecs execute-command` có thể treo không giới hạn (phiên SSM không đóng)** (S253) → `tools/ecs/ecsx.sh`
- **DB Migrate `apply` từ chối khi chuỗi pipeline địa điểm (geocode → dedupe → shape → graph) còn job queued/running — xếp migration vào khoảng rảnh giữa các chuỗi, hoặc xin Nghiệp override (ghi lý do)** (S254) → `infra/AA-CIS-Infra/.github/scripts/job-idle-gate.sh`, `infra/AA-CIS-Infra/db/run_migration.py`
- **Script ship/push phải từ chối khi `git rebase` còn dở** (S254) → `tools/github/ship_train.py`
- **GitHub: `mergeq.sh` có thể báo "not merged" đúng lúc queue vừa merge (state còn OPEN, timeline đã ghi RemovedFromMergeQueue reason=merged)** (S255) → `tools/github/ship_merge.py`
- **Repo không có merge queue (TripPlanner, repo gốc): PR đã xanh hết thì merge thẳng `--squash`, không bật `--auto`** (S256) → `tools/github/ship_merge.py`
- **Không đặt alias output trùng tên cột rồi ORDER BY theo tên trần — ORDER BY ưu tiên cột output, nên `txid::text AS txid` + `ORDER BY txid` sắp theo chuỗi ('10' < '9') trong khi WHERE keyset so cột xid8** (S256, S257) → `apps/AA-CIS-App/tests/unit/test_aa978_tenant_membership_contract.py`
- **Test trên index xấp xỉ (HNSW) không so thứ tự top-k tuyệt đối với kết quả chính xác — so khoảng cách / recall@k ≥ ngưỡng** (S257) → `apps/AA-TripPlanner-Web/backend/tests/test_vector_topk_pg.py`
- **Workflow gọi workflow (reusable) không tự nhận secret của environment ở job được gọi** (S258) → `infra/AA-CIS-Infra/.github/workflows/db-isolation-probe.yml`
- **`tools/github/mergeq.sh` có thể báo exit 4 "not merged and not in the queue (OPEN, CLEAN)" đúng lúc queue vừa merge** (n/a) → `tools/github/ship_merge.py`
- **Chuỗi merge nền (train) phải tự gate từng PR ngay trước `gh pr merge`, không tin trạng thái đã đọc lúc đầu** (n/a) → `tools/github/ship_merge.py`
- **Apply-pending KHÔNG nhảy qua khoảng trống số migration: nhiều lane cùng owner → merge theo đúng thứ tự số, hoặc lane merge trước lấy số nhỏ nhất còn trống** (S261, S263) → `tools/github/ship_copy_apply.py`, `tools/workflows/lane.js`
- ****PR code xếp chồng trên PR migration-only (MIG-4): sau khi PR migration squash-merge, PR code vẫn mang commit migration**** (S262) → `tools/github/ship_train.py`
- **Migration tạo bảng mới phải kèm dòng retention DM-7.1 ở repo gốc TRƯỚC khi bot copy sang Infra** (S262) → `infra/AA-CIS-Infra/db/tests/test_check_retention_rows.py`, `tools/workflows/lane.js`
- **Lane AA-Partner phải chạy unit suite đúng như CI (kèm cổng coverage unit 90% của AA-Partner), không chỉ integration** (S262) → `tools/workflows/lane.js`
- **Merge queue / `mergeq.sh` chỉ chờ check BẮT BUỘC** (S263) → `tools/github/ship_merge.py`
- **Nhánh code xếp chồng trên nhánh migration: sau khi PR migration squash-merge phải rebase (commit migration thành rỗng tự bỏ, hoặc `--skip` khi conflict) rồi force-with-lease** (S266) → `tools/github/ship_train.py`
- **Key schema đòi riêng ngoài prefix (`REQUIRED_*_ABOVE_GAP`) phải được cả `/health/ready`, Deploy Dev schema-gate và migration preflight đọc** (S267) → `apps/AA-CIS-App/.github/scripts/schema_gate.py`, `apps/AA-CIS-App/tests/unit/test_schema_gate_script.py`
- **Migration Apply tự động đi theo tiền tố liên tục: một file CIS cố ý treo (336) chặn MỌI file CIS sau nó, kể cả expand; contract cần DB Migrate tay vì `DB_AUTO_APPLY_CONTRACT=false`** (S268, S269) → `tools/github/ship_copy_apply.py`
- **Hook PII của pilot (`.claude/hooks/pilot_pii_guard.py`, AA-969, root #548) chặn lệnh vừa ghi script vừa chạy/upload trong cùng một lệnh, và lệnh `cd` + đường dẫn tương đối** (S269) → `.claude/hooks/pilot_pii_guard.py`
- **PR đang xung đột với main thì GitHub không chạy workflow `pull_request` (không có merge ref) — chỉ còn `pull_request_target` (Secret Scan); đóng/mở lại PR cũng không giúp** (S270) → `tools/github/ship_merge.py`
- **Kịch bản UAT có đăng nhập phải quay qua `node tools/uat/dryrun.cjs --record <ID>`, không gọi thẳng `run.sh`** (S270) → `tools/uat/run.sh`
- **Không `pkill -f <mẫu>` / vòng `pgrep -f` / `ps | grep <mẫu>` + kill từ lệnh Bash mà chính dòng lệnh chứa mẫu đó** (S249, S250, S252, S253, S254, S262, S263, S264) → `.claude/hooks/aa_shell_guard.py` PKILL-1 (guard mới S271, AA-1024)
- **`pkill -f "<mẫu>"` giết luôn chính lệnh chứa mẫu đó** (S268) → `.claude/hooks/aa_shell_guard.py` PKILL-1 (guard mới S271, AA-1024)
- **Không bao giờ `export $(lệnh)` mà không kiểm đầu ra trước — lệnh lỗi/rỗng thì `export` trần in TOÀN BỘ biến môi trường (token, mật khẩu) ra transcript** (S244) → `.claude/hooks/aa_shell_guard.py` ENV-1 (guard mới S271, AA-1024)
- **Merge queue nhiều PR: enqueue song song (mỗi PR một tiến trình nền), không chạy `mergeq.sh` tuần tự** (S257) → `.claude/hooks/aa_shell_guard.py` SHIP-1, `tools/github/ship_wave.py` (guard mới S271, AA-1024)
- **Output dài của ECS exec bị cắt im lặng — không đọc kết quả lớn qua terminal SSM** (S237, S248, S251, S253, S256, S257) → `.claude/hooks/aa_shell_guard.py` ECS-1, `tools/ecs/ecsx.sh` (chạy lại lượt mất, bản output local) (guard mới S272, AA-1024)
- **Không chạy chuỗi verify dài ở nền với output đổ vào `/dev/null`** (S247) → `.claude/hooks/aa_shell_guard.py` BG-1 (guard mới S272, AA-1024)
- **Terraform apply cục bộ phải chạy từ `main` đã merge, không từ nhánh PR / worktree** (S240) → `.claude/hooks/aa_shell_guard.py` TF-1 (guard mới S272, AA-1024)
- **WSL 8 GB OOM khi chạy song song 2 `next build` + pytest + gitleaks mirror + VS Code → VM khởi động lại, mất tác vụ nền** (S248, S261) → `.claude/hooks/aa_shell_guard.py` RAM-1, `.claude/hooks/lane_start_guard.py` (RAM gate) (guard mới S272, AA-1024)
- **gitleaks quét TỪNG commit của PR, sửa ở commit sau không cứu được** (S249, S252, S256) → `tools/github/ship_open_prs.py` (gitleaks v8.30.1 trước mọi push), `apps/AA-CIS-App/scripts/pre-push.sh` (gitleaks trên mỗi push CIS, kể cả push sửa sau khi đã mở PR), `tools/workflows/lane.js` (lane chạy gitleaks) (guard mới S272, AA-1024)
- **Giá trị dạng hash đặt cạnh tên có chữ `token`/`key` trong file JSON sẽ bị gitleaks `generic-api-key` bắt, và job quét TỪNG commit của PR nên sửa ở commit sau vẫn đỏ** (S253, S260) → `tools/github/ship_open_prs.py` (gitleaks v8.30.1 trước mọi push), `apps/AA-CIS-App/scripts/pre-push.sh` (gitleaks trên mỗi push CIS) (guard mới S272, AA-1024)
- **Secret Scan (full history) đỏ trên main không ai thấy vì không phải required check** (S255) → `tools/github/guard_runs.py` (đầu phiên, run lịch đỏ lên trước) (guard mới S272, AA-1024)
- **ecsx local mode (CRM/Booking) đôi khi mất output dù script đã chạy** (S266, S269, S268) → `tools/ecs/ecsx_local.py` (nostart → chạy lại một lần, bản output local) (guard mới S272, AA-1024)
- **`tools/ecs/ecsx.sh` local mode (CRM) đôi khi báo "no result after Ns" dù script đã chạy xong — script ghi output ra file riêng, đọc lại bằng `--resume <run id> 0`; không pipe ecsx qua grep trong lệnh dài** (S267) → `tools/ecs/ecsx_local.py` (bản output `.tmp-session/ecsx/<run id>.out`) (guard mới S272, AA-1024)
- **Script live dài qua `tools/ecs/ecsx.sh` phải ghi `> file 2>&1`, không pipe qua `tail`** (S268) → `tools/ecs/ecsx.sh` (luôn giữ bản output local) (guard mới S272, AA-1024)
- **Điều phối tự chạy Playwright/ecsx cũng tính vào tải RAM của lane — 3 lane code + Playwright của điều phối làm WSL 10 GB khởi động lại** (S270) → `.claude/hooks/aa_shell_guard.py` RAM-1 (cả push / pre-push) (guard mới S272, AA-1024)
- **Push qua `ship_open_prs.py` phải đủ giờ cho hook pre-push của repo** (S272) → `tools/github/test_ship_open_prs.py` PushTimeoutTest (mặc định 900 s, `AA_PUSH_TIMEOUT`) + `tools/github/safe-hooks/pre-push` (push bỏ `GIT_DIR`) (guard mới S272, AA-1024)
- **Test chạy git trong thư mục tạm phải bỏ `GIT_DIR` / `GIT_WORK_TREE` / `GIT_INDEX_FILE` thừa hưởng từ hook** (S272) → `.githooks/pre-push`, `scripts/pre-push.sh`, `tools/github/test_git_env_isolation.py` (guard mới S272, AA-1024)
- **Không push / chạy pre-push đầy đủ của CIS (~5.000 unit test) khi máy đang tải nặng** (S272) → `.claude/hooks/aa_shell_guard.py` RAM-1 (push, PR opener, ship_wave, `scripts/pre-push.sh`) (guard mới S272, AA-1024)
- **Script adhoc chạy lâu (>5′) không chạy trong task api/worker khi còn PR backend chờ merge — deploy thay task giết script** (S234) → `.claude/hooks/aa_shell_guard.py` ECS-1 (không exec trần), `apps/AA-CIS-App/shared/jobs/exec_heartbeat.py` (deploy gate CIS chặn khi heartbeat ecsx còn mới) (guard mới S272, AA-1024)
- **Chuỗi ship nối `&&` với `| tail` / `| head` phải bật `set -o pipefail` — exit code của pipeline là của `tail`, bước sau vẫn chạy** (S272, S273) → `.claude/hooks/aa_shell_guard.py` PIPE-1 (guard mới S274, AA-1024)
- **Wrapper merge queue không kết luận PR "rời queue" khi `isInMergeQueue` đọc false — còn entry trong `mergeQueue.entries` hoặc run `merge_group` của nhánh nhóm `pr-<n>-` chưa xong thì chờ tiếp** (S273) → `tools/github/mergeq.sh` held(), `tools/github/ship_merge.py` queue_hold, `tools/github/test_ship_merge.py` QueueExitTest + MergeqScriptTest (guard mới S274, AA-1024)
- **Allow-list Actions cấp org phải tính action lồng trong composite action bên thứ ba (trivy-action → setup-trivy)** (S273, ADR 0021) → `tools/github/ci_hygiene.py` WL8 + `tools/github/actions-allowlist.txt` (guard mới S274, AA-1024)
- **File sinh tự động từ nguồn ngoài (Linear export) cũng phải qua gitleaks trước khi commit** (S276) → `tools/linear/linear_export.py` (gitleaks trên mọi file xuất của lượt chạy, kể cả file không đổi; chỉ bỏ dấu hai chấm sau nhãn secret khi token là tên dạng đường dẫn, giá trị lạ giữ nguyên cho gitleaks bắt), `tools/linear/test_linear_export.py` (guard mới S277, AA-1024)

## Pipeline và chất lượng

- **Keyword DFS là chuỗi truy vấn thô, không được ép nguyên văn vào title/meta** (S233) → `apps/AA-CIS-App/tests/unit/test_aa768_s233_completeness.py`
- **Tham số gửi cho model phải kiểm ở request thật, không chỉ ở LLMRequest** (S224) → `apps/AA-CIS-App/tests/unit/test_s224_claude_temperature.py`
- **Repair step có thể tạo lỗi mới (flag_fix thêm forbidden word)** (n/a) → `apps/AA-CIS-App/tests/unit/test_aa738_forbidden_strip.py`
- **Bước sửa tất định phải chạy sau lần sửa LLM cuối cùng, không chỉ lúc viết** (S218) → `apps/AA-CIS-App/tests/unit/test_aa738_forbidden_strip.py`, `apps/AA-CIS-App/tests/unit/test_aa768_s234_round4.py`
- **Validator chỉ quét nội dung do writer viết, không quét cả dict** (S218) → `apps/AA-CIS-App/tests/unit/test_aa738_forbidden_strip.py`
- **Đếm rerun theo distinct tour: master / review-pending / not-run; không đếm superseded; `ingested` trong review ≠ chưa chạy.** (n/a) → `apps/AA-CIS-App/services/waves/report.py`, `apps/AA-CIS-App/tests/unit/test_aa727_waves.py`, `apps/AA-CIS-App/tests/integration/test_aa727_waves.py`
- **Jev fail-open: `llm_call_log` ghi cả lần lỗi** (n/a) → `apps/AA-CIS-App/services/waves/report.py`
- **Loại trừ theo luật ở một bước mới phải khớp quyết định CUỐI của bước sau, không chỉ luật gốc** (S223) → `apps/AA-CIS-App/tests/unit/test_aa695_no_transit_segments.py`
- **Luật "dòng đầu" phải đọc dòng đầu SAU khi bỏ khoảng trắng đầu bài; bước sửa cuối không được miễn trừ CTA** (S234) → `apps/AA-CIS-App/tests/unit/test_aa768_s234_round4.py`
- **Test "chép" phải đo cả hai chiều và theo câu, không theo tỉ lệ cả cặp** (S234) → `apps/AA-CIS-App/tests/unit/test_aa768_faq_droppers.py`
- **Bộ lọc phạm vi dựng chỉ từ cách viết của seed sẽ bỏ sót câu hỏi tìm kiếm thật** (S245) → `apps/AA-CIS-App/tests/unit/test_aa779_real_first.py`
- **Nới một bộ lọc liên quan để hết "loại nhầm" thì phải kiểm lại "giữ nhầm" trước khi merge** (S245) → `apps/AA-CIS-App/tests/unit/test_aa779_real_questions.py`
- **Vòng "học" phải ghi và đọc cùng một khoá, và phải có cổng trước khi chạm prompt dùng chung** (S245) → `apps/AA-CIS-App/tests/unit/test_aa923_retired_lesson_paths.py`, `apps/AA-CIS-App/tests/unit/test_aa920_injection.py`
- **Sửa gate chặn nhầm: chạy census trên MỌI hit thật đã lưu (old/new matcher) + bộ câu đối kháng nơi khác trước khi đóng; dùng cấu trúc câu, không dùng danh sách từ** (S248) → `apps/AA-CIS-App/tests/unit/test_aa985_f17_entity_binding.py`
- **Kiểm "lỗi mới" bằng so khớp theo nội dung câu thì một bước sửa chữ trong câu vốn đã lỗi bị coi là gây lỗi mới — so với lỗi của câu CŨ** (S251) → `apps/AA-CIS-App/tests/unit/test_aa768_s234_round2.py`, `apps/AA-CIS-App/tests/unit/test_aa790_post_repair_integrity.py`
- **Bước viết lại xoá chữ giữa hệ từ và liên từ ("X is not A but B") phải kiểm A và B còn song song** (S251) → `apps/AA-CIS-App/tests/unit/test_aa790_writer_ai_tells.py`
- **Stage truyền `json_schema` phải route tới key trong catalog (Converse ép schema tool) — key legacy (`haiku`/`sonnet`/`gpt-4.1`) đi qua `invoke_claude`, bỏ qua `json_schema`, trả text tự do** (S251) → `apps/AA-CIS-App/tests/unit/test_s251_legacy_structured_output.py`
- **Bộ viết lại câu theo luật (`ai_tells`) cần một bất biến chung "không xoá token sự thật", không vá từng mẫu** (S252) → `apps/AA-CIS-App/tests/unit/test_aa790_fact_invariant.py`
- **Một con số mọi bước đều đồng ý vẫn có thể sai nếu cùng đọc từ một parser sai — duration lệch số marker ngày thì replay dòng nguồn thô trước khi đổ lỗi bước sau** (S252) → `apps/AA-CIS-App/tests/unit/test_aa990_n3_day_guard.py`
- **Probe "đi theo nguồn" phải dùng đúng điều kiện đủ tư cách của stage nó đo** (S253) → `apps/AA-CIS-App/tests/unit/test_aa992_data_coverage.py`
- **Recall tune cho gate T10 đang chặn/hold: mỗi pattern mở rộng phải qua verifier tự viết câu sạch mới; còn FP thì bỏ pattern, không nới tiếp** (S257) → `apps/AA-CIS-App/tests/unit/test_aa789_t10_recall.py`
- **Smoke hợp đồng model phải đếm lỗi provider là `failed`** (S263) → `apps/AA-CIS-App/tests/unit/test_aa1026_contract_smoke.py`
- **Cờ dừng của wave phải đọc lại sau khi hàng đợi chạy hết, trước khi gọi là "dừng"** (S249) → `apps/AA-CIS-App/scripts/aa645/wave_report.py` (cờ `pending` khi tour còn job queued/running, exit 5) (guard mới S272, AA-1024)

## Job runner

- **CancelledError (worker nhả job khi deploy) trong node LangGraph sync bị bọc thành `NodeCancelledError` (là `Exception`, CancelledError ở `__cause__`) — unwrap `__cause__` trước nhánh lỗi, không theo `__context__`** (S254) → `apps/AA-CIS-App/api/routers/v1_pipeline.py`, `apps/AA-CIS-App/tests/unit/jobs/test_aa993_g2_s1_resume.py`, `apps/AA-CIS-App/.github/workflows/ci.yml`, `apps/AA-CIS-App/services/content_generation/graph.py`
- **Sau mọi lần chạy trả tiền, đếm dòng `shared.llm_call_log` theo `job_id` — 0 dòng là mất log, không phải $0** (S254) → `apps/AA-CIS-App/shared/jobs/worker.py`, `apps/AA-CIS-App/tests/unit/jobs/test_aa993_s1_llm_call_log.py`, `apps/AA-CIS-App/shared/ops_checks.py`, `apps/AA-CIS-App/api/core/ops_metrics_sampler.py`
- **Thêm job kind định kỳ mới (`crm.job`, `shared.job`) thì cập nhật cả test liệt kê lịch production** (S263) → `apps/AA-Partner/api/tests/integration/test_job_runner.py`, `apps/AA-Partner/.github/workflows/ci.yml`, `tools/workflows/lane.js`
- **Guard "hệ thống rảnh" của load test không được dựa trên một mẫu duy nhất** (S268, S269) → `apps/AA-Partner/loadtest/crm_loadtest.py`, `apps/AA-Partner/api/tests/unit/test_aa969_loadtest_runner.py`, `apps/AA-Partner/.github/workflows/ci.yml`

## Dữ liệu

- **Các cột của một funnel phải đếm cùng một tập (cùng bộ lọc gốc), nếu không cột sau có thể lớn hơn cột trước** (S244) → `apps/AA-CIS-App/tests/unit/test_overview_funnel_active_raw.py`
- **Một UPDATE đổi khoá con (`SET segment_id = …`) trên bảng có PK ghép dễ đụng PK khi dòng đích đã có** (S218) → `apps/AA-CIS-App/tests/integration/test_s218_segment_alias_repoint.py`, `apps/AA-CIS-App/services/acp_contract/segment_matching.py`
- **Trên RDS, kiểm RLS bằng hành vi (đếm dòng dưới tenant lạ), không bằng thuộc tính role** (S236) → `infra/AA-CIS-Infra/db/isolation_probe.py`
- **Luật "không được gộp" trong union-find phải giữ ở cấp NHÓM, không chỉ cấp cặp** (S239) → `apps/AA-CIS-App/tests/unit/test_aa857_subject_seed_country.py`
- **Luật đọc thành viên của một nhóm không được chặt hơn luật đã tạo ra nhóm đó** (S239) → `apps/AA-CIS-App/tests/unit/test_aa857_subject_seed_country.py`
- **Id băm theo (nhãn, nước) mà nhãn còn đổi được thì phải chống trùng id khi ghi** (S239) → `apps/AA-CIS-App/tests/unit/test_aa857_segment_id_collision.py`
- **Khẳng định của plan về hành vi RLS phải đối chiếu số đếm probe live, không suy luận** (S243) → `infra/AA-CIS-Infra/db/isolation_probe.py`
- **Policy `TO r` áp cho cả thành viên của r — đo "trước/sau" phải đo trước khi tạo policy** (S243) → `apps/AA-CIS-App/tests/integration/test_aa860_migration_244.py`
- **Migration thêm policy lên bảng mà migration cũ có guard "đúng tập policy" sẽ làm test re-apply migration cũ đỏ** (S243) → `apps/AA-CIS-App/tests/integration/conftest.py`
- **`Subquery Scan` trong EXPLAIN của view `security_barrier` KHÔNG có nghĩa là bộ lọc bị chặn trên barrier** (S246) → `apps/AA-CIS-App/tests/integration/test_aa847_migration_256.py`
- **Gitleaks mặc định bắt `generic-api-key` khi một hằng có tên kết thúc bằng KEY được gán một chuỗi tên setting/cột (không phải secret)** (S248, S261) → `.github/workflows/secret-scan.yml`, `infra/AA-CIS-Infra/.gitleaks.toml`, `tools/workflows/lane.js`
- **Ảnh catalog trùng nội dung nhưng khác id (mỗi thư mục tour trên Drive một bản; Dev: 2.629 dòng matched, 1.120 sha256)** (S253) → `apps/AA-TripPlanner-Web/backend/tests/test_catalog.py`, `apps/AA-CIS-App/tests/integration/test_aa995_photo_path_by_content.py`
- **Repo public: chuỗi mẫu trong test cũng không được có 12 chữ số dạng account** (S258) → `apps/AA-CIS-App/.github/workflows/ci.yml`, `apps/AA-CIS-App/.github/scripts/check_resource_ids.py`, `apps/AA-CIS-App/tests/unit/test_aa902_resource_id_check.py`
- ****PR migration mở trước khi số liền trước lên main thì CI đỏ preflight ("not the next one"), và vẫn đỏ sau khi số trước** (n/a) → `tools/github/ship_train.py`
- **Luồng erase/withdraw chỉ xoá object S3 sau câu lệnh cuối cùng còn có thể từ chối** (n/a) → `apps/AA-Partner/api/tests/unit/test_portability.py`
- **Mã hoá cột: tên AAD phải trùng tên cột DB** (n/a) → `apps/AA-Partner/api/tests/unit/test_portability.py`
- **Header migration: chỉ file thật sự expand mới có `-- migrate: expand`; file contract là file KHÔNG có directive (không có `-- migrate: contract`)** (S263) → `tools/workflows/lane.js`
- **Migration có `CREATE POLICY` / `CREATE TRIGGER` phải kèm `DROP … IF EXISTS` trước đó** (S263) → `apps/AA-Partner/api/tests/integration/test_crm_migrations.py`
- **Job chiếu (projection pull) từ một master mới phải có adoption guard: dòng chưa từng chiếu (projected_at NULL) mà master chưa có thì để nguyên — không suspend, không xoá quyền, không đóng dấu projected_at** (S266) → `apps/AA-Booking/backend/tests/integration/test_aa1028_tenant_pull.py`, `apps/AA-Partner/api/tests/integration/test_crm043_entitlement_feed.py`
- **Bảng mới có cột `tenant_id` mà RLS tắt có chủ đích không thể là expand: classify đòi ENABLE + FORCE RLS cho bảng tenant_id mới** (S268) → `infra/AA-CIS-Infra/db/rls_catalogue_rules.py`
- **DRY RUN qua ECS exec không băm cả dòng (`md5(t::text)`)** (S271) → `.claude/hooks/pilot_pii_guard.py` (`--check`), `skill/aa-cis-schema/references/destructive-ops.md` (mẫu pin) (guard mới S272, AA-1024)

## Frontend

- **Tràn ngang mobile: đo phần tử gây tràn rồi mới sửa, không đoán** (S221) → `apps/AA-CIS-App/tests/e2e/visual/visual.spec.ts`, `apps/AA-CIS-App/tests/e2e/smoke/smoke-helpers.ts`
- **Next 16 React Compiler: lint lỗi `set-state-in-effect`** (n/a) → `apps/AA-CIS-App/.github/workflows/ci.yml`
- **Playwright `fill` trước khi React hydrate một input controlled bị reset im lặng** (S247) (lỗi thời: đã thay bằng) → `apps/AA-Partner/e2e/smoke-portal/auth.setup.ts`
- **Next sau CloudFront → ALB: kiểm same-origin phải so Origin với origin công khai, không với `request.nextUrl.origin`** (S249) → `apps/AA-CIS-App/frontend/lib/sameOrigin.test.mjs`, `apps/AA-Partner/web/tests/writeGuard.test.ts`
- **Playwright `fullPage: true` trên trang admin chỉ chụp đúng viewport (1440x900)** (S251) → `apps/AA-CIS-App/tests/e2e/smoke/smoke-helpers.ts`, `apps/AA-CIS-App/tests/e2e/visual/visual.spec.ts`
- **Trang not-found mà API của chính nó trả 404 sẽ làm đỏ smoke cấm mọi 4xx và mọi lỗi console (Chromium log "Failed to load resource" cho 404) — ở đó 404 là câu trả lời đúng, khai báo đích danh thay vì nới luật** (S251) → `apps/AA-CIS-App/tests/e2e/smoke/smoke-helpers.ts`
- **Lần đầu kit sync chép một file kit core mới sang một consumer, đối chiếu file mới với lint override + guard riêng của consumer đó trước** (S256) → `apps/AA-CIS-App/.github/workflows/kit-consumers.yml`
- **Ảnh `fullPage` của trang có `content-visibility: auto` ra dải trống ở các section đó; nghi dải trống thì cuộn tới và chụp theo viewport trước khi kết luận (S255** (S255) → `apps/AA-TripPlanner-Web/e2e/visual/visual.spec.ts`
- **Route nhận form một lần (claim lời mời) không được ghi đè cookie trạng thái ở mỗi POST** (S263) → `apps/AA-Partner/web/tests/team.test.ts`, `apps/AA-Partner/web/tests/joinInvitePage.test.ts`
- **Corpus n-gram của gate video phải ngang origin** (S268) → `tools/uat/arch/make_episode.py`
