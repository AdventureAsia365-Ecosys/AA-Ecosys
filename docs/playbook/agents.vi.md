---
id: GUIDE-14-agents
title: Vận hành một dự án với agent
description: Cách một người và nhiều agent AI vận hành một dự án - vai trò, dung sai, guardrail, nghi thức phiên, lane, trang quyết định và phân lớp chỉ dẫn.
type: explanation
status: draft
owner: nghiep
audience: [cto, engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-14, GUIDE-14-principles, TPL-01-session, GUIDE-02]
lang: vi
translation_of: docs/playbook/agents.md
---

# Vận hành một dự án với agent

Những gì AA học được khi vận hành một đội gồm một tech lead và nhiều agent AI, viết ra để dự án khác áp dụng được.
**Theo:** AGENTS.md (định dạng chỉ dẫn mở), các kỹ thuật về agent trong Thoughtworks Technology Radar (lộ dần ngữ cảnh,
sandbox, vòng phản hồi; cảnh báo về chỉ dẫn phình to và tài liệu tràn lan), dung sai của PRINCE2.

## Vai trò

| Vai trò | Làm | Không bao giờ |
|---|---|---|
| Tech lead (người) | Duyệt Definition of Ready, ADR và chi tiêu; giữ credential, MFA và các quyết định prod | - |
| Chủ doanh nghiệp (người) | Quyết định kinh doanh, pháp lý và thương mại; xem lại bản phát hành, chi phí và UAT | Duyệt kỹ thuật |
| Agent điều phối (phiên chính) | Chọn việc, viết hoặc giao code, gác cổng, merge và deploy trong giai đoạn dev, kiểm live, cập nhật công cụ theo dõi việc | Đăng cập nhật kinh doanh khi chưa được duyệt; đụng prod khi không có tech lead |
| Subagent và agent code thứ hai (lane) | Code, test và commit trong worktree riêng | Push, merge, áp hạ tầng, ghi secret hay resource cloud |
| Agent review | Review các lớp rủi ro theo góc nhìn của nó | Merge |
| CI | Chạy mọi check; là cổng cuối | - |

Agent có thể là người làm (Responsible) của một pha, không bao giờ là người chịu trách nhiệm cuối (Accountable).

## Dung sai

Agent làm mà không hỏi trong giới hạn của [bảng dung sai](principles.vi.md#dung-sai) và chỉ báo lên khi dự báo vượt.
"Tự quyết, không hỏi" và "không tự đặt cổng chặn" là cùng một luật nhìn từ hai phía: làm trọn một hướng đã duyệt, và
không bao giờ tự đặt ra một lệnh giữ việc mà dung sai không đòi hỏi.

## Trang quyết định

Khi thật sự cần người, mang tới một trang, không phải một chuỗi câu hỏi trong chat:

- Bối cảnh bằng lời thường cho mỗi câu hỏi: nó nói về gì và vì sao quan trọng lúc này.
- Hai tới năm phương án cho mỗi câu hỏi, cộng "Khác" có chỗ để viết.
- Câu trả lời đề xuất được đánh dấu, kèm một dòng lý do.
- Ai trả lời mỗi câu hỏi (tech lead hay chủ doanh nghiệp).
- Câu trả lời được lưu ở nơi agent đọc lại được, để việc tiếp tục mà không phải gõ lại.

## Guardrail

Luật quan trọng được máy thực thi, không dựa vào trí nhớ:

| Guardrail | Chặn cái gì |
|---|---|
| Hook cho subagent | Push, merge, áp hạ tầng, ghi cloud và ghi secret từ một lane |
| Guard ghi qua MCP | Ghi vào công cụ theo dõi việc hay tài liệu từ những công cụ chỉ nên đọc |
| Luật shell guard | Các lệnh từng gây lỗi thật (mỗi luật dẫn bài học của nó) |
| Hook khi dừng | Kết thúc phiên trong khi còn việc không bị chặn |
| Guard dữ liệu cá nhân | Dữ liệu cá nhân trong prompt, log hay commit |

Mỗi hook đi kèm các test red-team chứng minh nó chặn ca xấu và cho ca tốt đi qua.

## Nghi thức phiên

- **Bắt đầu:** đọc log gần nhất, backlog và kế hoạch; kiểm trạng thái live; đề xuất 3 tới 5 issue theo thứ tự kế hoạch.
- **Trong phiên:** giữ một checklist sống; viết bài học ngay lúc tìm ra nguyên nhân gốc, kèm guard sẽ chặn nó lần sau.
- **Đóng phiên:** chụp trạng thái live, thêm bài học, xin duyệt các bản nháp kinh doanh, rồi mới viết log; mọi repo về
  nhánh main sạch.

Mẫu: [checklist phiên và log phiên](../templates/session-checklist.vi.md).

## Lane

- Mỗi lane một worktree, tạo từ main mới nhất; lane không bao giờ sửa checkout chính.
- Mỗi lane đọc `CONTEXT.md` của repo và các bài học của vùng đó trước khi sửa.
- Reviewer theo góc nhìn: đúng đắn cho mọi thay đổi; bảo mật và dữ liệu cho lớp rủi ro; một lượt sửa.
- Một lane trả về một kết quả có cấu trúc: nhánh và commit, test đã chạy, các bước live nó không làm được (kèm script
  sẵn sàng), và phần còn lại.
- Agent điều phối push, mở PR, merge, deploy và chạy các bước live.

## Phân lớp chỉ dẫn

| Lớp | Chứa | Nạp khi |
|---|---|---|
| `AGENTS.md` (nguồn), `CLAUDE.md` import nó | Luật cứng và con trỏ, giữ ngắn | Luôn luôn |
| Skill | Quy trình cho một loại việc | Khi cần |
| Tài liệu (`CONTEXT.md`, playbook, sổ tay) | Sự thật và luật đầy đủ | Được trỏ tới, đọc khi cần |
| Bài học | Các nguyên nhân gốc gần đây, mỗi dòng có trường guard và một tag phạm vi (chỉ dự án này, hoặc chung cho bộ kit) | Theo vùng, trước khi sửa |

Giữ lớp luôn nạp nhỏ và đo nó; chuyển quy trình vào skill; biến bài học kiểm được thành guard rồi xoá dòng; cắt tỉa ở mỗi
đợt rà soát 90 ngày.
