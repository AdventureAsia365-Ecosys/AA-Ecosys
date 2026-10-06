---
name: aa-jira-update
description: Soạn và đăng cập nhật trên Jira của Adventure Asia cho chị Thư (các project PR, KAN, CON) — luôn nháp trước, chờ Nghiệp duyệt rồi mới đăng; tiếng Việt, bảng số liệu theo nước, mention ADF @thule. Dùng khi cần trả lời hoặc báo tiến độ trên Jira, đọc yêu cầu mới từ Jira, hoặc đổi trạng thái issue Jira.
---

# aa-jira-update

Người đọc là phía nghiệp vụ, ngoài nhóm kỹ thuật. Một comment sai đi thẳng tới người ra quyết định, nên đây là chỗ cổng duyệt luôn bắt buộc.

## Luật

1. **Không bao giờ đăng thẳng.** Soạn nháp → đưa Nghiệp xem nguyên văn → chỉ đăng khi Nghiệp nói đăng. Áp dụng cho comment, sửa comment, đổi trạng thái. (PR-11 từng bị đăng trước khi duyệt.)
2. **Tiếng Việt**, câu ngắn, không thuật ngữ nội bộ (không ghi tên bảng, tên hàm, mã AA-xxx trừ khi chị Thư dùng).
3. **Chỉ tag chị Thư**, trừ khi Nghiệp chỉ định thêm người.
4. Số liệu đều phải lấy từ query/endpoint trong phiên này, ghi ngày lấy số.
5. Không đưa vào: chi phí nội bộ chi tiết hay lỗi đã tự xử lý xong, trừ khi Nghiệp muốn. (Ví dụ PR-15 đã bỏ phần Jev.)

## Kết nối

- Atlassian MCP endpoint `/v2/mcp` (v1/sse đã ngừng). Lấy `cloudId` một lần mỗi phiên.
- Mention chị Thư: `contentFormat: html` với `<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>` (markdown `@thule` không tạo mention thật). cloudId site: lấy một lần bằng `getAccessibleAtlassianResources`.
- Bảng HTML render tốt trên Jira.

## Mẫu báo tiến độ rerun

```
@thule Cập nhật <nước> ngày <dd/mm>:

<table> Nước | Tổng tour raw | Lên Master | Đang chờ duyệt (lý do) | Bỏ (raw không đủ) </table>

- Điểm chính: <1–2 câu>
- Cần chị quyết: <câu hỏi cụ thể, nếu có>
- Bước tiếp: <nước kế tiếp, dự kiến>
```

## Quy trình

1. Đọc issue Jira và các comment gần nhất (`getJiraIssue`).
2. Lấy số liệu (query, endpoint báo cáo wave).
3. Soạn nháp trong chat, kèm tên issue và vị trí sẽ đăng.
4. Nghiệp duyệt hoặc sửa → đăng → trả link comment.
5. Ghi vào session block: issue Jira, comment id, nội dung chính.
