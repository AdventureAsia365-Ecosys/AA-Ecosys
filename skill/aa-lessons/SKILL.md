---
name: aa-lessons
description: Sổ bài học (lesson log) của AA_Ecosys — ghi ngay một nguyên tắc khi tìm ra nguyên nhân gốc của lỗi do làm/code sai cách hoặc giả định sai, và đọc các bài học của vùng code trước khi sửa để không lặp lại lỗi cũ. Dùng khi Nghiệp nói "lỗi", "sai cách", "lại bị", "note lại bài học", khi review phát hiện lỗi pattern, khi tiền đề của một issue hoá ra sai, và trước khi sửa pipeline/gate/validator, job runner, migration/RLS, Terraform/ECS exec, trang list FE hoặc Playwright.
---

# aa-lessons

Log: [`lessons.md`](lessons.md), chia theo vùng. Mỗi dòng là **một nguyên tắc**, không phải nhật ký sự cố.

| Mục trong `lessons.md` | Đọc trước khi |
|---|---|
| Cách làm việc / Thái độ làm việc | lập kế hoạch, chạy nhiều lane/subagent song song, báo cáo cho Nghiệp |
| Verify và "Done" | báo xong, viết test, chuyển Done, soạn khẳng định cho Jira |
| Vận hành | merge/deploy, Terraform, ECS exec, Vercel, IAM/secret, Linear/GitHub tooling |
| Pipeline và chất lượng | sửa writer/judge/gate/validator, A/B, wave |
| Job runner | sửa `shared.job` / worker / cap / job có vòng lặp LLM |
| Dữ liệu | viết migration, RLS/role, view, script xoá/restore |
| Frontend | sửa trang admin/portal/CRM web, smoke Playwright |

## 1. Trước khi làm — đọc

- Trước khi sửa một vùng, đọc mục tương ứng ở bảng trên.
- Đầu phiên (`aa-session`): lướt các mục liên quan tới issue đã chốt, và file bài học chờ của phiên trước
  (`.tmp-session/S<nnn-1>-lessons-pending.md`) nếu còn.
- Bài học mâu thuẫn với yêu cầu đang làm → nêu với Nghiệp trước, không lặng lẽ bỏ qua.

## 2. Khi nào ghi — ghi ngay

Ghi **ngay lúc tìm ra nguyên nhân gốc**, không đợi cuối phiên. Ghi khi lỗi đến từ:

- làm sai cách hoặc dùng pattern sai (code chạy được nhưng sai thiết kế);
- giả định sai: tiền đề trong issue, trí nhớ, tên bảng/cột, "chắc là do…";
- một bước verify bị bỏ qua mà lẽ ra đã bắt được lỗi;
- thay đổi này phá một quyết định cũ mà không ai đối chiếu.

Không ghi: lỗi gõ đơn thuần, điều đã có guard (test/CI) bắt được, hay nhật ký phiên (thuộc log `docs/sessions/`).

Trong phiên, ghi vào `.tmp-session/S<nnn>-lessons-pending.md` (cùng mẫu dòng); cuối phiên mới chuyển vào
`lessons.md` (mục 5) — tránh nhiều lane cùng sửa một file. Subagent không sửa `lessons.md`: nêu bài học trong kết quả
trả về để điều phối ghi.

## 3. Ghi thế nào

Một dòng, đúng mục, theo mẫu (trường `Guard:` BẮT BUỘC, AA-1024):

```
- **<Nguyên tắc, mệnh lệnh ngắn>** — <triệu chứng → nguyên nhân gốc> (S<nnn>, AA-xxx). Guard: <loại> <đích>.
```

`Guard:` nói cái gì chặn lỗi lần sau (tech lead S271: "viết bài học không cải thiện được gì, lỗi vẫn lặp"):

| Dạng | Khi nào |
|---|---|
| `Guard: test\|hook\|tool\|ci\|lane <đường dẫn>` | đã có máy chặn: test, hook (`aa_shell_guard:<RULE>` cho rule của `.claude/hooks/aa_shell_guard.py`), tool, CI check, luật trong `tools/workflows/lane.js`; đường dẫn phải tồn tại |
| `Guard: pending GRD-<n>` (hoặc `AA-<n>`) | guard chưa làm; mã phải có trong `docs/backlog/README.md` hoặc `plan.json` (xếp vào phiên kế) |
| `Guard: none: judgement\|external\|one-off <vì sao>` | không có máy chặn được (phán đoán, sự cố bên ngoài, chỉ một lần); lý do 3+ chữ |

- `tools/docs/check_lessons.py` (Docs lint) đỏ khi một dòng MỚI hoặc SỬA thiếu `Guard:`, đích không tồn tại, mã pending
  chưa lên kế hoạch, hoặc dòng nhắc 2+ phiên mà ghi `none: one-off`. File chờ: `--pending .tmp-session/S<nnn>-lessons-pending.md`.
- **Lặp lại → guard, không gộp dòng** (S271): trùng ý với dòng đã có và lỗi kiểm được bằng máy → làm guard ngay trong
  phiên (hoặc `pending GRD-<n>` xếp vào phiên kế), không chỉ thêm bằng chứng vào dòng cũ. Chỉ dòng `none:` mới gộp.
- Nguyên tắc chung cho mọi vùng → mục "Cách làm việc".
- Ghi bằng tiếng Việt (log nội bộ), tên code/bảng/lệnh giữ nguyên; `Guard:` giữ từ khoá tiếng Anh. Không ghi secret,
  account ID mới hay giá trị token.
- Đích của `Guard:` là thứ còn tồn tại trong repo, không phải helper trong `.tmp-session/` (bị dọn). "Bắt bằng: …" cũ
  chỉ còn là gợi ý cách phát hiện, không thay `Guard:`.

## 4. Biến bài học thành guard

Bài học kiểm được bằng máy là bài học tốt nhất:

1. Có thể viết unit test, CI check, lint rule, hook hoặc assert → **làm luôn** trong PR đang sửa lỗi, nếu nằm trong scope.
2. Ngoài scope → đề xuất issue (hỏi Nghiệp trước khi tạo, theo `aa-linear-issue`).
3. Guard đã merge và chặn được **cả lớp lỗi** (không chỉ đúng một ca) → chuyển dòng sang [`guards.md`](guards.md)
   (cùng mục, kèm đường dẫn guard) trong cùng PR, ghi tên guard trong commit message. Guard chỉ ghim một ca → giữ dòng,
   ghi guard đó ở `Guard:`. `python3 tools/docs/check_lessons.py --sweep` liệt kê các dòng có guard để rà.
4. Luật shell / quy trình (pkill, zsh, export, merge tuần tự, RAM, lane): thêm rule vào `.claude/hooks/aa_shell_guard.py`
   (một bảng rule, mỗi rule có test chặn + test gần-đúng-vẫn-cho-qua, chạy trong root CI), không viết thêm dòng văn xuôi.

## 5. Cuối phiên

Trong `aa-session` kết thúc phiên (bước "Bài học"): `python3 tools/docs/check_lessons.py --pending
.tmp-session/S<nnn>-lessons-pending.md` xanh, rồi chuyển vào `lessons.md` (đúng mục; dòng lặp lại một dòng cũ → guard
hoặc `pending GRD-<n>`, xem mục 3), rà lại các lỗi đã gặp trong phiên còn thiếu dòng, rồi nêu trong session block:
"bài học: X mới, Y thành guard, Z chuyển sang guards.md". Subagent trả bài học dạng `{principle, guard_kind,
guard_target_or_reason}` (`tools/workflows/lane.js`) để điều phối ghi thẳng.

## 6. Nơi sửa và phát hành

`skill/` ở repo gốc là nguồn duy nhất. Sửa xong → PR repo gốc (điều phối merge sau khi Docs lint xanh, luật root PR
trong `aa-ship`), rồi đóng gói lại `tools/skills/package_skills.sh aa-lessons` → Nghiệp upload `skill/dist/aa-lessons.zip`
lên tài khoản claude.ai đang dùng (Settings → Capabilities → Skills, thay bản cùng tên). Kiro đọc trực tiếp từ repo.
