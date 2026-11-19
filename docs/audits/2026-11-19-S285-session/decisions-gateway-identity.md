# S285 — Quyết định của tech lead: gateway AI và tên người dùng

Nguồn: trang quyết định https://claude.ai/artifact/NHsW9EY4jj4ptc3DdJq81P (19/11/2026, 13/13 "Đồng ý").
Bản tư vấn: [advisory-gateway.md](advisory-gateway.md), [advisory-identity.md](advisory-identity.md).

| Mã | Quyết định | Ghi chú của tech lead |
|---|---|---|
| G1 | Chưa dựng service gateway trung tâm | |
| G2 | CRM dùng đúng tên connection của registry chung | |
| G3 | Ngân sách theo dòng (app, connection) | |
| G4 | aa_llm 1.3 phạm vi hẹp (cap, anomaly, scrub, route plan) | |
| G5 | TripPlanner gọi Claude qua acc1 | Làm luôn, không đợi đầu tháng 12 |
| G6 | Key Anthropic riêng mỗi app | Để sau; giữ 1 key chung; hướng chính là Bedrock, không phải API direct; tư vấn thêm "mỗi app một key" khi dùng Bedrock |
| I1 | Mỗi app lưu tên hiển thị của người thuộc app đó | |
| I2 | Tên thành viên đại lý lưu chữ thường (pii:name) | |
| I3 | Thành viên tự sửa tên của mình | Tư vấn thêm thị trường làm thế nào |
| I4 | Ghi tên vào tài khoản Cognito một lần lúc tạo | Giải thích rõ hơn |
| I5 | Component PersonLabel dùng chung | |
| I6 | Giữ bản tạm S285 tới khi có cột tên | |
| I7 | Đổi tên staff AA qua thủ tục có ghi log | |

| I4 (sửa 19/11) | Đại lý: tên người mời gõ lưu trong lời mời của CRM để điền sẵn, Cognito không giữ tên; staff AA: Cognito `name` là gốc (token mang tên sang Booking), CIS chép theo, đổi qua thủ tục I7 | Tech lead chọn để I3 và I4 không mâu thuẫn |
