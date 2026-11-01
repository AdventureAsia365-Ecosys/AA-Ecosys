# Merge train chạy nền

Một **train** = một chuỗi PR phụ thuộc nhau (migration → copy → DB Migrate → code → deploy, hoặc nhánh xếp chồng)
merge theo thứ tự bằng lệnh chạy nền. Chỉ agent điều phối chạy train (merge/push/`gh workflow run` bị hook chặn với
subagent, `SKILL.md` §0). Luật gate và cách merge từng repo: `SKILL.md` §1 "Cách merge"; guard job/wave: §2; verify
live: §3. Công cụ và mã thoát: `tools/github/README.md` (AA-1032).

## Dựng train

- Mỗi chuỗi phụ thuộc một lệnh (hoặc một script ngắn nối các lệnh bằng `&&`) chạy bằng Bash `run_in_background`,
  output `> .tmp-session/S<nnn>/<tên>-train.txt 2>&1`. Hai chuỗi độc lập = hai train, không gộp. Không tự viết lại
  gate/merge/copy trong `.tmp-session/`: dùng các tool dưới đây (S263: script tự viết merge PR có check đỏ không bắt
  buộc và đọc nhầm run DB Migrate của file khác).
- Công cụ (Python stdlib, `python3 tools/github/<tool>.py --help`):
  - `ship_merge.py '<Repo> <n>' …` — chờ check, **mọi** check phải xanh (không chỉ required), từ chối draft / base
    không phải nhánh mặc định / DIRTY / PR xoá file; repo queue qua `mergeq.sh`, repo khác squash
    `--match-head-commit`. Nhiều PR: queue chạy song song, cùng repo không queue thì lần lượt; `--serial` giữ thứ tự.
  - `ship_train.py <Repo> <worktree> <branch>:<pr>[:<own>] …` — nhánh xếp chồng (mục dưới).
  - `ship_copy_apply.py <owner> <NNN>` — PR copy Infra + DB Migrate + readiness (mục Migration).
  - `train-lib.sh` (source): còn dùng `waitdeploy <cis|booking|crm> <sha>` (chờ health báo `git_sha`) và `merged`;
    `gate`/`waitcopy`/`restack` cũ đã có bản tool ở trên.
- Train **dừng ở bước đỏ đầu tiên** (mã thoát khác 0) và báo; điều phối đọc `.txt`, sửa, chạy lại phần còn lại (tool
  bỏ qua PR đã merge). Mọi lần chờ có timeout; tool tự poll (≥ 30 s mỗi vòng), không `gh run watch` trần.
- Phiên MFA 8 h: tool cảnh báo khi còn < 30 phút (train: < 60 phút) vì `as-app.sh` cần MFA ở mỗi lần push/merge.

## Thứ tự merge từng repo

- CIS, Booking, Partner: `ship_merge.py` (gate mọi check → `mergeq.sh` → đọc lại state, kể cả khi `mergeq.sh` báo
  "not merged" mà queue vừa merge).
- TripPlanner, Infra, repo gốc: `ship_merge.py` (squash thẳng khi mọi check xanh, đúng head đã gate).
- Có gì push vào PR sau lần gate trước (bot, restack, release-please) → chạy lại `ship_merge.py` ngay trước khi merge.

## Migration trong train (ADR 0017)

- **Expand:** `ship_merge.py` PR app → `ship_copy_apply.py <owner> <NNN>` (chờ PR copy ci-bot tự merge — hoặc gate +
  merge nếu còn mở — không dispatch, đợi key có trong `/health/ready`) → `waitdeploy` (job schema gate của Deploy Dev
  chờ apply).
- **Contract / destructive:** `ship_merge.py` PR chỉ migration → `ship_copy_apply.py <owner> <NNN> --mode check` →
  `ship_copy_apply.py <owner> <NNN>` (apply) → mới tới PR code. Tool:
  - tìm `bot/migration-copy/<owner>-<NNN>` ở **mọi** trạng thái (mở → gate + merge; đã merge → dùng luôn; đóng → bỏ);
  - đọc loại file từ header trên Infra main; file destructive cần `--allow-destructive` sau quy trình DRY RUN;
  - theo **đúng run của mình**: khoá cục bộ, ghi các run có sẵn, dispatch, lấy run mới có tiêu đề
    `DB Migrate <mode> <owner>/<file>` (run-name của Infra); không bao giờ đọc "run mới nhất";
  - in conclusion + dòng log chính (`ran as`, busy/idle, applied), rồi `/health/ready` (`schema_version`, key trong
    `registered_keys`).
  Bước, idle check và output của DB Migrate: `docs/ops/runbooks/db-migrate.md` (không chép vào train).

## Nhánh xếp chồng (stacked)

- `ship_train.py <Repo> <worktree> <A>:<prA> <B>:<prB>` (dưới cùng trước). Số commit riêng của mỗi nhánh đếm **một
  lần trước khi đụng gì** (`<nhánh dưới>..<nhánh>`; ghi `:<n>` để ép), rồi mỗi nhánh:
  `git rebase --onto origin/main <nhánh>~<n> <nhánh>` — chỉ commit riêng di chuyển, commit của nhánh dưới đã squash
  không bị replay (lesson S243) → đổi base PR về `main` + `gh pr ready` nếu cần → push
  `--force-with-lease=<nhánh>:<SHA remote>` qua `as-app.sh` → gate + merge như `ship_merge.py`.
- Tool từ chối khi đang rebase dở, có file tracked bị sửa, hoặc `origin/<nhánh>` có commit mà nhánh local thiếu
  (bot/người khác đã push). Xung đột → abort rebase, train dừng, điều phối giải tay (`resolving-merge-conflicts`).
- `--dry-run` in kế hoạch rebase, không đụng gì.

## Deploy và kết thúc

- Chờ deploy bằng `waitdeploy <app> "$MERGED_SHA"` (SHA merge cuối nếu queue gộp nhóm), không bằng "run Deploy Dev
  mới nhất". Sau đó điều phối chạy `live_steps` của lane và verify §3 cho từng PR.
- Train xong → ghi kết quả (PR, SHA, run DB Migrate, deploy) vào checklist phiên.
