# Lane code song song (Ultracode)

Một **lane** = một lát việc (~1 issue, 1 PR hoặc nhóm PR nhỏ) chạy trong một Workflow riêng. Trang này chỉ nói cách
chạy lane; luật hook subagent ở `SKILL.md` mục "Điều phối và subagent", mẫu brief ở
`ai-nghiep/references/handoff-prompt.md`, Definition of Ready ở `aa-linear-issue`, merge ở `aa-ship`.

## Khi nào

- Ultracode bật, phiên 8–10 issue (cỡ phiên: `SKILL.md` bước 3). Issue phải đủ Ready trước khi giao lane.
- Số lane cùng lúc theo RAM: tối đa 3 lane nặng (build/test/Playwright), một `next build` mỗi lúc, chừa ≥ ~2 GB
  (`free -h` trước khi fan-out). Mỗi lane một thư mục scratch riêng.

## Luồng một lane

1. **Gọi Workflow** với script `tools/workflows/lane.js`, `args` là JSON viết inline (không chuỗi giữ chỗ):
   `{"key": "<lane>", "goal": "AA-xxx: <lát việc + đường dẫn plan>", "session": "S<nnn>", "date": "<dd/mm/yyyy>",
   "migStart": {"cis": <N>}, "lenses": [...]}`. `migStart` (gợi ý số migration theo owner) và `lenses` không bắt buộc.
2. **Implement:** agent lane làm trong worktree đường dẫn tuyệt đối của riêng nó, chỉ commit local.
3. **Review:** 2 reviewer độc lập theo lens — mặc định (a) đúng + khớp spec, (b) bảo mật + an toàn dữ liệu. Đổi
   `lenses` khi lane có rủi ro khác (ví dụ UI kit, hiệu năng).
4. **Fix:** một lượt sửa cho finding blocking/major; finding bị bác phải có lý do.
5. **Kết quả:** `prs[]` theo thứ tự merge, mỗi PR có `live_steps`; `notes_vi` 3–6 dòng cho tech lead.
6. **Điều phối** push, mở PR, chạy merge train (`aa-ship`, `references/merge-trains.md`), chạy `live_steps`.

## Luật trong brief

Khối `COMMON` của `lane.js` là dạng workflow của mẫu brief giao việc. Mỗi dòng trong đó là guard cho một bài học
(`aa-lessons`): fixture tên hư cấu, `**billed_fields`, số migration + `git grep '<số cũ>_'`, `openapi.json` theo bản
CI, nhãn model chứa "api" mỗi dòng một nhãn, test integration `cis_app` cấp quyền tạm + đọc theo tên cột, RAM, cấm
push/merge/ECS exec. Thêm luật mới → sửa `COMMON` trong `lane.js` (một nguồn), không chép vào brief từng lane.
Khi một dòng `COMMON` đã là guard, dòng bài học tương ứng trong `lessons.md` có thể rút gọn (`aa-lessons` §4).

## Sau rate limit / usage limit

- Lane chết giữa chừng → chạy lại Workflow với `resumeFromRunId` của run cũ: lane đã xong giữ kết quả, chỉ lane chết
  chạy lại.
- Run không resume được → agent mới tiếp từ trạng thái worktree (`git status`, `git log`, implementation notes), không
  làm lại từ đầu; `lane.js` đã dặn điều này trong `COMMON`.

## Điều phối kiểm trước khi tin review

- Worktree trong `prs[]` có thật và có commit vượt base (`git -C <wt> log --oneline <base>..HEAD`). Review "approve"
  trên nhánh rỗng là review không có gì.
- Lane trả `ready=false` → đọc `blocked_reason`, quyết định làm tiếp bằng tay hay đưa vào checklist là chặn thật.
