---
name: aa-session
description: Nghi thức bắt đầu và kết thúc một phiên làm việc AA_Ecosys — đọc memory.md HOT, kiểm job/ECS/STS, chốt danh sách việc; cuối phiên prepend session block (không rotate), cập nhật Linear, dừng môi trường. Dùng khi Nghiệp nói bắt đầu phiên, "S2xx", "đầu phiên", "kết thúc phiên", "chốt phiên", "wrap up", hoặc khi một phiên AA bắt đầu mà chưa có bối cảnh.
---

# aa-session

## Bắt đầu phiên

1. **Đọc Notion `memory.md` HOT** (Program Brain). Lấy: phiên gần nhất, "việc cần làm đầu phiên sau", lưu ý kỹ thuật, ECS revision cuối. Không đọc archive trừ khi cần lịch sử cũ.
2. **Kiểm trạng thái thật**, so với memory:
   - STS còn hạn: `aws sts get-caller-identity --profile aa365-admin`
   - Môi trường đang chạy? (`cis-status`). Nếu môi trường đang tắt → **KHÔNG tự `cis-start`**; báo Nghiệp và chờ Nghiệp bật. Agent không bao giờ tự bật/tắt hạ tầng.
   - api và worker cùng image SHA, đúng revision memory ghi
   - `shared.job` có job queued/running không (query không lọc thời gian)
   - Jev canary `credit_ok` và số dư DFS, nếu phiên có chạy pipeline
3. **Đưa danh sách 5–10 issue sẽ làm**, theo thứ tự ưu tiên. Mỗi issue `get_issue` để chắc title đúng.
4. **Báo lệch:** nếu state thật khác memory (revision, job treo, issue đã đóng), nói ngay trước khi làm.

Đầu ra: một khối ngắn gồm trạng thái (3–5 dòng), lệch nếu có, danh sách việc.

## Trong phiên

- Mỗi quyết định kiến trúc → đề xuất ADR (`ai-nghiep/references/adr.md`).
- Mỗi issue xong → theo `aa-ship` (verify live rồi mới Done).
- Wave rerun → theo `aa-wave-rerun`, không merge backend giữa wave.

## Kết thúc phiên

1. **Session block** prepend vào đầu `memory.md` HOT, đúng format:
   ```
   ## S<nnn> (<dd/mm/yyyy>, <Kiro|Claude Code|Claude Chat> — <môi trường>): <tiêu đề ngắn>
   **Quyết định của Nghiệp** — chỉ quyết định Nghiệp nói, không phải đề xuất của agent
   **Kết quả chính** — issue + PR + bằng chứng verify
   **Việc cần làm đầu phiên sau (S<nnn+1>)** — có thứ tự
   **Lưu ý kỹ thuật** — chỉ điều mới, chưa có trong skill
   ```
2. **Chỉ prepend.** Agent không cắt, không di chuyển, không xoá session block cũ. Nghiệp tự chuyển phiên cũ sang `memory_archive_2026H2` bằng tay (rotate tự động từng gây lỗi).
3. **Lưu ý kỹ thuật lặp lại ≥2 phiên** → đưa vào skill phù hợp (thường `ai-nghiep/references/lessons.md`), rồi xoá khỏi memory.
4. **Linear:** issue đã verify → Done kèm comment bằng chứng; đang dở → In Progress kèm ghi chú.
5. **Log local:** `docs/sessions/<yyyy-mm-dd>-S<nnn>-<slug>.md`.
6. **KHÔNG dừng môi trường.** Hệ thống để chạy liên tục, ổn định. Agent TUYỆT ĐỐI không tự `cis-stop`/`cis-start`/scale ECS/stop RDS/stop NAT — mọi bật/tắt hạ tầng chỉ Nghiệp làm, hoặc Nghiệp yêu cầu rõ. Cuối phiên để nguyên môi trường đang chạy.
7. **Tóm tắt 3 dòng** cho Nghiệp: đã làm / còn lại / phiên sau bắt đầu từ đâu.
