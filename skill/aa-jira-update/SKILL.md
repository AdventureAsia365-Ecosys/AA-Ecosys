---
name: aa-jira-update
description: Soạn và đăng cập nhật trên Jira của Adventure Asia cho chị Thư (các project PR, KAN, CON; epic theo app PR-22…PR-27, báo cáo tuần PR-20) — luôn nháp trước, chờ Nghiệp duyệt rồi mới đăng; tiếng Việt, bảng số liệu, mention @thule bằng mention node, ảnh nhúng. Dùng khi cần trả lời hoặc báo tiến độ trên Jira, soạn báo cáo tuần, đọc yêu cầu mới từ Jira, hoặc đổi trạng thái issue Jira.
---

# aa-jira-update

Người đọc là phía nghiệp vụ, ngoài nhóm kỹ thuật. Một comment sai đi thẳng tới người ra quyết định, nên đây là chỗ cổng
duyệt luôn bắt buộc.

## Luật

1. **Không bao giờ đăng thẳng.** Soạn nháp → đưa Nghiệp xem nguyên văn → chỉ đăng khi Nghiệp nói đăng. Áp dụng cho
   comment, sửa comment, đổi trạng thái. Câu kiểu "chưa vội đăng, làm xong rồi đăng luôn" nghĩa là *chờ làm xong*,
   không phải bỏ bước duyệt (PR-11 từng bị đăng trước khi duyệt).
2. **Không tự tạo issue Jira, không tự đổi trạng thái** khi báo tiến độ (steering `session-workflow.md`). Yêu cầu mới
   đặt dưới đúng epic app chỉ khi Nghiệp bảo.
3. **Chỉ báo khi việc đã ship.** Không comment kiểu "đã ghi nhận, sẽ làm". Mỗi câu "chạy được" chỉ cho đúng kênh đã thử
   thật trọn vòng, có ảnh; chưa thử thì ghi "đã có trong hệ thống, chưa thử thật vì …" (memory
   `jira-claims-need-live-evidence`, bài học trong `skill/aa-lessons/lessons.md` mục Verify và "Done").
4. **Tiếng Việt**, câu ngắn, đứng tên Nghiệp (không nhắc tên agent), không thuật ngữ nội bộ: không tên bảng, tên hàm,
   mã Linear (`AA-xxx`) hay mã quyết định nội bộ. Nói tính năng đã làm và chỗ xem; không "như đã hứa", không rải "ạ"
   (memory `jira-draft-tone`).
5. **Chỉ tag chị Thư**, trừ khi Nghiệp chỉ định thêm người — kể cả khi nội dung có nhắc tên người khác.
6. Số liệu đều phải lấy từ query/endpoint/snapshot trong phiên này, ghi ngày (và giờ) lấy số.
7. Không đưa vào: chi phí nội bộ chi tiết hay lỗi đã tự xử lý xong, trừ khi Nghiệp muốn.
8. Việc pháp lý/kinh doanh/chính sách: trước hết xem có thay đổi hệ thống nào bỏ được câu hỏi không; chỉ câu hỏi thật sự
   của chủ doanh nghiệp (giá, phí, hợp đồng, luật sư) mới đưa chị Thư, dạng đề xuất nhẹ nhàng có phương án + khuyến nghị,
   không hạn chót gây áp lực (memory `tech-focus-business-to-thu`, `improve-system-not-raise`). Trang/bảng hỏi cho chị
   Thư viết như form khảo sát trung tính (memory `thu-questionnaire-style`).

## Cấu trúc Jira (site `adventure-asia.atlassian.net`)

- Project: **PR** (Plans & Reports), **KAN**, **CON**.
- PR có một epic cho mỗi app: PR-22 CIS nội dung & pipeline, PR-23 Portal tenant, PR-24 TripPlanner, PR-25 Booking,
  PR-26 CRM cho đại lý, PR-27 Nền tảng (đăng nhập, bảo mật, hạ tầng). Tính năng là story con của epic tương ứng; comment
  vào story/epic khi tính năng ship.
- **Báo cáo nền tảng hằng tuần** (từ S245): mỗi tuần một story dưới epic PR-20, chia mục theo app (đã xong / tiếp theo /
  rủi ro / chi phí, link tới các story tính năng vừa cập nhật).

## Kết nối

- Atlassian MCP (claude.ai connector, endpoint v2). Lấy `cloudId` một lần mỗi phiên bằng `getAccessibleAtlassianResources`.
  Connector lỗi 404/"not connected" sau khi đổi tài khoản claude.ai → mở lại phiên, không tự debug (memory
  `mcp-after-account-switch`).
- Mention chị Thư: `contentFormat: html` với
  `<span data-type="mention" data-user-id="70121:5793bdd5-44b1-4623-97d4-43c35d440869">@thule</span>` (markdown
  `@thule` không tạo mention thật). Bảng HTML render tốt trên Jira; bảng markdown trong nháp đổi sang HTML khi đăng.
- **Ảnh kèm comment** — đính thẳng vào Jira, không thay bằng link GitHub:
  1. `executeWrite` `uploadAttachmentToJiraIssue` (issueIdOrKey + `filePath`, mỗi file 1 lần) → trả `uploadCommand`
     (curl tới api.media.atlassian.com, token sống ngắn) + `collection`;
  2. chạy curl, lấy `data.id` (fileId);
  3. `addOrEditJiraIssueComment` với `contentFormat: html`, `inlineFileId: [ids…]`, `inlineFileCollection: [collection]`,
     `inlineFileName: [tên…]` → ảnh nhúng ở cuối comment, đúng thứ tự.

  KHÔNG chạy phase 2 (gọi lại với `fileId` để attach riêng) cho cùng file (bị trùng). Đặt tên file tiếng Việt không dấu,
  và thêm 1 dòng chú thích thứ tự ảnh trong comment.
- **Atlassian MCP hay timeout.** Sau một lần đăng bị timeout, kiểm bằng JQL `updated >= -Nm` hoặc đọc comment mới nhất
  trước khi đăng lại, để không đăng trùng.
- Sửa comment đã có ảnh: truyền đủ thân mới ở `contentFormat: html` (markdown làm rơi ảnh).

## Mẫu báo tiến độ rerun

```
@thule Cập nhật <nước> ngày <dd/mm>:

<table> Nước | Tổng tour raw | Lên Master | Đang chờ duyệt (lý do) | Bỏ (raw không đủ) </table>

- Điểm chính: <1–2 câu>
- Cần chị quyết: <câu hỏi cụ thể, nếu có>
- Bước tiếp: <nước kế tiếp, dự kiến>
```

Báo theo bản phát hành (tag `vX.Y.Z` của một app): soạn từ mục CHANGELOG theo mẫu `docs/templates/release-note.md`
(phần "Jira draft (VI)").

## Quy trình

1. Rà issue Jira: các issue khớp việc của phiên và mọi issue chưa Done
   (`project in (PR, KAN, CON) AND statusCategory != Done`); đọc comment gần nhất để không lặp lại nội dung đã đăng.
2. Lấy số liệu (query, endpoint, báo cáo wave, snapshot cuối phiên).
3. Soạn nháp: mỗi issue ghi tên issue, vì sao chọn, vị trí sẽ đăng, nội dung sẵn để đăng, và bảng "câu → bằng chứng".
   Link trang/artifact/file Drive làm cho chị Thư đưa vào đúng nháp của issue đó, không gửi lẻ qua Zalo (memory
   `thu-links-via-jira`; file Excel/review: memory `gdrive-adventureasia-folder`; quyền chia sẻ do Nghiệp mở).
4. **Gom nháp, đưa Nghiệp một lần ở cuối phiên**, dán nguyên văn trong tin nhắn, không chỉ đưa đường dẫn file (memory
   `batch-drafts-at-session-end`). Bản lưu: `docs/audits/<date>-S<nnn>-…/jira-drafts.md` (theo `aa-session`); repo gốc
   đang public nên bản lưu không chứa account ID AWS, secret hay link Drive riêng (DM-6.10).
5. Nghiệp duyệt hoặc sửa → đăng → ghi comment id/link (hoặc "chưa đăng: lý do") vào file nháp và log phiên.
