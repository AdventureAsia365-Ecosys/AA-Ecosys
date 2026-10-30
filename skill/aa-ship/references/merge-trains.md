# Merge train chạy nền

Một **train** = một chuỗi PR phụ thuộc nhau (migration → copy → DB Migrate → code → deploy, hoặc nhánh xếp chồng)
merge theo thứ tự bằng một script chạy nền. Chỉ agent điều phối chạy train (merge/push/`gh workflow run` bị hook chặn
với subagent, `SKILL.md` §0). Luật gate và cách merge từng repo: `SKILL.md` §1 "Cách merge"; guard job/wave: §2;
verify live: §3.

## Dựng train

- Một script mỗi chuỗi phụ thuộc: `.tmp-session/S<nnn>/<tên>-train.sh`, chạy bằng Bash `run_in_background`, output
  `> .tmp-session/S<nnn>/<tên>-train.txt 2>&1`. Hai chuỗi độc lập = hai train, không gộp.
- Đầu script: `set -u`, `cd /home/nghiep/projects/AA-Ecosys`, `. tools/github/train-lib.sh`. Mỗi bước `|| exit 1`:
  train **dừng ở bước đỏ đầu tiên** và báo; điều phối đọc `.txt`, sửa, viết `<tên>-train2.sh` cho phần còn lại.
- Hàm trong `tools/github/train-lib.sh` (cách gọi ở header file):
  - `gate <Repo> <pr>` — chờ check, chỉ qua khi **mọi** check `pass`/`skipping` và `mergeStateStatus` không `DIRTY`.
  - `merged <Repo> <pr>` — in trạng thái, đặt `MERGED_SHA`.
  - `waitcopy <owner> <NNN>` — chờ file copy trên Infra `main`; PR copy contract/destructive đang mở thì gate + merge.
  - `waitdeploy <cis|booking|crm> <sha>` — chờ health của app báo `git_sha` = SHA merge.
  - `restack <worktree> <old-base-sha> <pr>` — rebase nhánh xếp chồng lên `origin/main` mới, push, `gh pr ready`, gate lại.
- Mọi lệnh chờ có `timeout` (hàm đã có; `gh run watch` trần có thể treo). Train không poll dồn: mỗi vòng ≥ 30 s.

## Thứ tự merge từng repo

- CIS, Booking, Partner: `gate` → `timeout 1500 tools/github/mergeq.sh <Repo> <n>` → `merged`.
- TripPlanner: `gate` → `as-app.sh … gh pr merge <n> --auto --squash`.
- Infra, repo gốc (không required check, không auto-merge): `gate` → `as-app.sh … gh pr merge <n> --squash`.
- Có gì push vào PR sau lần gate trước (bot, restack, release-please) → `gate` lại ngay trước lệnh merge.

## Migration trong train (ADR 0017)

- **Expand:** merge PR app → `waitcopy <owner> <NNN>` (PR copy ci-bot tự merge, Migration Apply tự chạy) →
  `waitdeploy` (job schema gate của Deploy Dev chờ apply).
- **Contract / destructive:** merge PR chỉ migration → `waitcopy` (tìm PR `bot/migration-copy/<owner>-<NNN>` theo
  `headRefName`, gate, merge tay) → `tools/github/dbmig.sh <owner>/<NNN> check && … apply` → mới tới PR code.
  Bước, idle check và output của DB Migrate: `docs/ops/runbooks/db-migrate.md` (không chép vào train).

## Nhánh xếp chồng (stacked)

- PR B dựng trên nhánh PR A: sau khi A squash vào `main`, ghi SHA base cũ của B bằng `git -C <wt> log --oneline`
  **ngay trước** khi restack, rồi `restack <wt> <sha> <prB>` (`git rebase --onto origin/main <sha>` — rebase trần
  kéo lại commit của A đã squash). Xung đột → train dừng, điều phối giải tay (`resolving-merge-conflicts`).

## Deploy và kết thúc

- Chờ deploy bằng `waitdeploy <app> "$MERGED_SHA"` (SHA merge cuối nếu queue gộp nhóm), không bằng "run Deploy Dev
  mới nhất". Sau đó điều phối chạy `live_steps` của lane và verify §3 cho từng PR.
- Train xong → ghi kết quả (PR, SHA, run DB Migrate, deploy) vào checklist phiên.
