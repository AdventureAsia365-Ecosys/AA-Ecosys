# Template giao việc cho Claude Code / Kiro

Một code block duy nhất để copy:

```
## Task: <tên ngắn> — <AA-xxx>

Mục tiêu: <làm gì; output là gì>

Repo: <AA-CIS-App | AA-CIS-Infra | AA-TripPlanner-Web | AA-Booking>
Branch: feature/aa-xxx-<mô tả> từ main → PR → main

Đọc trước:
- <path>: <vai trò>

Bối cảnh / ràng buộc:
- <gotcha, quyết định đã chốt, thứ không được đụng>

Các bước:
1. …
2. …

Verify (bắt buộc, dán kết quả):
- <lệnh test / query / curl trên domain thật>

Kết thúc:
- Commit: "<feat|fix|chore>: <mô tả> (Refs AA-xxx)"
- PR body: "Refs AA-xxx" (không dùng [AA-xxx] — tự đóng issue)
- Linear: comment bằng chứng verify; chỉ chuyển Done khi đã verify live (aa-ship)
```

Trước khi gửi: `get_issue AA-xxx` để chắc số issue đúng với nội dung.
