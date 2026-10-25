# Template giao việc cho Claude Code / Kiro

Một code block duy nhất để copy. Prompt viết tiếng Anh hoặc tiếng Việt đều được; code, commit, PR viết tiếng Anh.

```
## Task: <tên ngắn> — <AA-xxx>

Only this task. Goal: <làm gì; output là gì>

Repo: <AA-CIS-App | AA-Booking | AA-TripPlanner-Web | AA-Partner | AA-CIS-Infra | AA-Ecosys (root)>
Worktree: /home/nghiep/projects/AA-Ecosys/.tmp-session/wt/<tên> (đường dẫn tuyệt đối), branch
  <feat|fix|chore|docs>/aa-xxx-<mô tả> từ origin/main mới nhất (root: origin/master) → PR → squash vào main

Đọc trước:
- CONTEXT.md của repo; <path>: <vai trò>
- aa-lessons/lessons.md: mục của vùng code sắp sửa

Bối cảnh / ràng buộc:
- <gotcha, quyết định đã chốt, thứ không được đụng>
- Tên bảng/cột: docs/architecture/db-schema-reference.md (không đoán)

Các bước:
1. …
2. …

Verify (bắt buộc, dán kết quả):
- <test / lint / query / curl trên domain thật>

Kết thúc:
- Commit subject "<feat|fix|chore|refactor|docs>: <mô tả>" (không mã issue trong subject);
  body có dòng "Refs AA-xxx". Không "[AA-xxx]", không "Fixes"/"Closes" — Linear tự đóng issue.
- Implementation notes: docs/implementation-notes/AA-xxx.md (Decisions / Changed / Tradeoffs / Should know)
- Subagent: không push, merge, gh workflow run, Terraform apply, DB Migrate, ECS exec. Trả về: branch + commit,
  kết quả verify, và mục "bước live cho điều phối" (push/PR, deploy, migration, kiểm live).
- Linear: comment bằng chứng verify; chỉ chuyển Done khi đã verify live (aa-ship)
```

Trước khi gửi: `get_issue AA-xxx` để chắc số issue đúng với nội dung.
