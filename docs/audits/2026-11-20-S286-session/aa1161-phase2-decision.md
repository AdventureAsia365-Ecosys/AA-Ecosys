# AA-1161 phase 2: viết lại lịch sử git để thu nhỏ repo (bản nháp trang quyết định)

Bản nháp cho tech lead (S286, 20/11/2026, tác nhân: Claude Code, lane l5). Phase 1 (guard pre-push + CI ở 6 repo,
`tools/docs/compress_images.py`, bỏ zip Lambda khỏi cây Infra) chặn repo phình thêm, nhưng **không** làm nhỏ lịch sử đã
có: mọi blob đã commit vẫn nằm trong history. Thu nhỏ thật cần `git filter-repo` + force push repo public. Trang này
nêu lựa chọn, con số, rủi ro và checklist để tech lead chốt. Chưa làm gì ở phase 2.

## Kích thước hiện tại (đo 20/11/2026)

`gh api repos/AdventureAsia365-Ecosys/<repo> --jq .size` (KB, GitHub tự tính, có độ trễ):

| Repo | GitHub size | Ghi chú |
|---|---|---|
| AA-Ecosys (gốc) | 847,362 KB (~827 MB) | S285 đo 826 MB; GitHub khuyên < 1 GB |
| AA-CIS-Infra | 90,610 KB (~88 MB) | |
| AA-CIS-App | 39,483 KB (~39 MB) | binary Kiro 664 MB chỉ nằm ở 1 nhánh local, chưa push |
| AA-Partner | 11,436 KB | ổn |
| AA-Booking | 7,337 KB | ổn |
| AA-TripPlanner-Web | 4,712 KB | ổn |

Phân tích blob trong lịch sử (`git rev-list --objects` + `git cat-file --batch-check`, dung lượng nén trên đĩa):

| Repo | Tổng blob | Phần có thể bỏ khỏi lịch sử |
|---|---|---|
| Gốc (`origin/master`) | ~847 MB | ảnh / video / PDF: ~799 MB trong 3,602 blob; trong đó `docs/audits/` ~460 MB, `docs/AAA/figma_AAA/` ~351 MB |
| Infra (`origin/main`) | ~90 MB | `dist/lambdas/*.zip`: ~80 MB trong 18 blob (zip Lambda ACP/CIS đã retire, không file `.tf` nào tham chiếu) |

## Kích thước dự kiến sau phase 2

| Repo | Sau filter-repo (ước tính) | Cách tính |
|---|---|---|
| Gốc, lựa chọn B | ~50-80 MB | ~847 MB trừ ~799 MB media, cộng lại các ảnh chính đã nén giữ ở HEAD (vài chục MB) |
| Gốc, lựa chọn C | ~100-150 MB | chỉ bỏ ảnh > 500 KiB và `figma_AAA`, giữ ảnh nhỏ (khớp mục tiêu trong issue) |
| Infra | ~10 MB | ~90 MB trừ ~80 MB zip |

Số GitHub báo chỉ giảm sau khi GitHub chạy GC phía server; với ref ẩn `refs/pull/*` của PR cũ có thể phải nhờ GitHub
Support (xem Rủi ro).

## Lựa chọn

| # | Lựa chọn | Được | Mất / rủi ro | Đề xuất |
|---|---|---|---|---|
| A | Không viết lại; chỉ giữ guard phase 1 | Không rủi ro force push | Gốc vẫn ~827 MB mãi mãi; clone mới chậm; vượt 1 GB nếu guard bị bypass | Không |
| B | filter-repo gốc: bỏ mọi ảnh/video/PDF khỏi lịch sử trừ file còn ở HEAD (sau khi HEAD đã nén + chuyển Figma ra Drive); Infra: bỏ `dist/lambdas/*.zip` | Nhỏ nhất (~50-80 MB) | Ảnh cũ trong audit chỉ còn link ngoài (Drive/S3 `audit-assets/`, S3 hết hạn 60 ngày) | **Có**, nếu tech lead chấp nhận ảnh cũ chỉ còn ở Drive |
| C | filter-repo gốc chỉ bỏ blob > 500 KiB và `docs/AAA/figma_AAA/`; Infra như B | Giữ ảnh nhỏ cũ trong lịch sử | ~100-150 MB | Phương án dự phòng |
| D | Repo gốc mới (snapshot HEAD), repo cũ archive | Không force push | Mất lịch sử blame/PR, phải đổi mọi pin `AA-Ecosys@<sha>` và URL | Không |

## Rủi ro cần biết trước

1. **SHA đổi toàn bộ.** Mọi commit sau điểm có ảnh đổi SHA. Thứ đang ghim SHA của repo gốc sẽ trỏ vào commit không còn:
   - 5 repo con: `change-guard.yml` và `spec-trace.yml` checkout `AdventureAsia365-Ecosys/AA-Ecosys` ở một SHA cố định;
     workflow gọi lại (`docs-impact.yml`, `spec-trace.yml` dạng `workflow_call`) nếu ghim SHA. Phải re-pin cả 5 repo
     cùng lúc ngay sau force push (một PR mỗi repo), nếu không các job đó báo "checkout failed" (change guard là warn).
   - `.gitleaksignore` (gốc và Infra): fingerprint chứa SHA commit → mọi dòng baseline mất hiệu lực; Secret Scan History
     có thể đỏ cho tới khi tạo lại baseline.
   - Link SHA trong Linear, Jira, docs/sessions, docs/audits, release notes → 404 (link PR `#n` vẫn sống).
2. **Ref ẩn và fork.** GitHub giữ `refs/pull/<n>/head` của mọi PR cũ; các object đó vẫn được giữ và vẫn tính dung lượng
   cho tới khi GitHub Support xoá cache/ref (quy trình "removing sensitive data"). Fork/clone của người khác vẫn còn
   lịch sử cũ (repo public). Phase 2 thu nhỏ repo, không "xoá" được thứ đã public.
3. **Nhánh và PR đang mở** bị lệch hoàn toàn sau force push: phải merge/đóng hết trước.
4. **release-please** (repo con, không phải gốc/Infra) không bị ảnh hưởng trực tiếp; nhưng tag ở gốc/Infra (nếu có) phải
   được filter-repo viết lại cùng. Nhánh bot (`bot/db-schema-reference`, PR copy ci-bot của Infra) phải được tạo lại từ
   master/main mới.
5. **Worktree và checkout local** (máy dev, lane `.tmp-session/wt/*`, Kiro): phải clone lại; pull vào checkout cũ sẽ
   trộn lại lịch sử cũ và đẩy ngược lên nếu ai đó push.
6. **Branch protection / ruleset** của Infra và gốc phải tạm cho phép force push trên nhánh mặc định trong cửa sổ, rồi
   khoá lại. Đây là thay đổi cài đặt repo (tech lead).
7. **Cache CI** gắn với ref cũ vô dụng: xoá (workflow Cache cleanup hoặc `gh cache delete --all`).

## Checklist cửa sổ phase 2 (khi tech lead duyệt)

Chuẩn bị (trước cửa sổ):

- [ ] Phase 1 đã merge ở cả 6 repo và guard xanh (không còn đường thêm ảnh/zip mới).
- [ ] Gốc: nén ảnh còn ở HEAD (`tools/docs/compress_images.py`), chuyển `docs/AAA/figma_AAA/` lên Drive (thư mục
      AdventureAsia) + để link; ảnh audit đầy đủ của các phiên cũ lên Drive hoặc S3 `audit-assets/` (nếu cần giữ).
- [ ] Liệt kê đường dẫn bỏ khỏi lịch sử (`--paths-from-file` hoặc `--strip-blobs-bigger-than 500K` cho lựa chọn C) và
      chạy thử filter-repo trên bản `git clone --mirror` tạm; đo kích thước trước/sau (`git count-objects -vH`).
- [ ] Liệt kê mọi chỗ ghim SHA repo gốc ở 5 repo con (`git grep -n 'AA-Ecosys' -- .github/`), soạn sẵn PR re-pin.
- [ ] Thông báo cửa sổ (thời gian, repo, việc phải làm sau: clone lại).

Trong cửa sổ:

- [ ] Merge hoặc đóng **mọi** PR mở của repo đó (hôm nay: gốc 1 PR mở, Infra 1 PR mở); dừng lane/agent đang chạy.
- [ ] Sao lưu đầy đủ: `git clone --mirror` lên chỗ riêng tư (S3 private của acc2 hoặc Drive), ghi checksum.
- [ ] Chạy `git filter-repo` trên mirror mới clone; kiểm `git log --stat` vài commit và HEAD tree giống hệt trước.
- [ ] Tạm mở force push trên nhánh mặc định (ruleset), `git push --force --mirror` (hoặc `--all` + `--tags`), khoá lại.
- [ ] Merge các PR re-pin SHA ở 5 repo con; tạo lại baseline `.gitleaksignore` nếu Secret Scan History đỏ.
- [ ] Xoá cache CI của repo; mở ticket GitHub Support để dọn `refs/pull/*` và chạy GC (nếu số size chưa giảm).

Sau cửa sổ:

- [ ] Clone lại mọi checkout local và worktree (`rm -rf` + clone; không `pull` vào checkout cũ).
- [ ] Kiểm release-please và nhánh bot chạy lại bình thường (PR schema dump, PR copy ci-bot Infra).
- [ ] Ghi kích thước sau (`gh api repos/AdventureAsia365-Ecosys/<repo> --jq .size`) vào issue; cập nhật link SHA quan
      trọng trong docs nếu cần.

## Việc cần tech lead quyết

1. Chọn B (khuyến nghị) hay C cho repo gốc; Infra làm cùng cửa sổ hay riêng.
2. Đồng ý ảnh audit cũ chỉ còn ở Drive (S3 `audit-assets/` hết hạn sau 60 ngày nên không thay được Drive).
3. Ngày giờ cửa sổ (đề xuất: cuối một phiên, sau khi mọi PR đã merge; ~1-2 giờ cho cả hai repo).
4. Ai mở ticket GitHub Support nếu size không giảm sau force push.
