---
id: GUIDE-13
title: Các file khoá học của AA Academy
description: Cách viết khoá học AA Academy trong thư mục này - lộ trình, module, bài học, bài kiểm tra và danh sách cho phép, cách một bài học trích nguồn và ghim mã băm của nguồn, các bước kiểm trong docs lint và gói learn mà Docs sync xuất bản.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, pm, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 90
related: [GUIDE-13-lms, GUIDE-13-lms-inventory, GUIDE-15, CAT-00, TPL-02, AA-1104]
lang: vi
translation_of: docs/learn/README.md
---

# Các file khoá học của AA Academy

AA Academy là trang học tập của AA: các lộ trình học theo vai trò với bài học ngắn, bài kiểm tra và bài thực hành.
Người học dùng host academy `academy.<env domain>` (Dev: `academy.lumiguides.it.com`) do ứng dụng web CRM phục vụ;
khoá học, tiến độ, bài kiểm tra và chứng chỉ lấy từ API học tập của CIS (`/learn/v1`, hợp đồng
[`learn.http.v1`](../contracts/learn.http.v1.openapi.yaml)) và schema `learn` của nó. Nhân sự đăng nhập ở đó bằng
đăng nhập nhân viên; đại lý theo sau. CIS admin đặt đường dẫn tới academy và giữ phần xem của nhóm (quyết định D17,
[ADR 0022](../adr/0022-aa-academy-learning-platform.md)). Thiết kế, các lộ trình và các
quyết định nằm trong [bản nghiên cứu](../research/lms/README.vi.md). Thư mục này chứa các khoá học dưới dạng file, và
trang này mô tả định dạng của chúng.

**Một quy tắc trên hết: khoá học không bao giờ chép lại nguồn.** Một bài học gọi tên các mục nó dạy theo tham chiếu, và
ghim mã băm của từng mục. Trình đọc hiện mục nguồn đang sống ngay cạnh bài học. Khi nguồn thay đổi, bước kiểm chuyển đỏ
hoặc bài học được đánh dấu cũ, nên không bài học nào lệch dần khỏi quy tắc nó dạy.

## Bố cục

```text
docs/learn/
  README.md                         trang này
  allowlist.yaml                    các mục skill, steering và CONTEXT.md mà gói được xuất bản; các trang cho đại lý
  schema/*.schema.json              JSON Schema của mọi file bên dưới
  paths/<path id>.yaml              một lộ trình học: các module theo thứ tự, bắt buộc hay tự chọn, các module dự kiến
  modules/<ID>-<slug>/
    module.yaml                     id, tiêu đề, tier, trạng thái, phiên bản, chủ module, mục tiêu, điều kiện trước, bài học
    lessons/<NN>-<slug>.md          thân bài học: không front-matter, dòng đầu là tiêu đề H1
    lessons/<NN>-<slug>.vi.md       bản dịch tiếng Việt của thân bài học, không bắt buộc
    quiz.yaml                       5 đến 10 câu hỏi nhớ lại, mỗi câu trích mục nó kiểm tra
    lab.yaml                        bài thực hành, không bắt buộc (đóng cho tới khi có bộ cấp môi trường thực hành)
```

Module đầu tiên viết theo định dạng này là [F3 How work flows](modules/F3-how-work-flows/module.yaml) trong
[lộ trình Fundamentals](paths/fundamentals.yaml). Chép nó để bắt đầu một module mới.

## Module và bài học

- **ID module** là mã trong các lộ trình của bản nghiên cứu (F1 đến F6, E1 đến E15, L1 đến L9, S, C, B, O, A). Thư mục
  bắt đầu bằng mã đó: `F3-how-work-flows`. ID bài học là `<module>-NN`: `F3-01`.
- **Tier** là ai được đọc module: `staff` (mọi vai trò nhân sự) hoặc `partner` (chủ đại lý và nhân viên đại lý). Một
  lộ trình chỉ chứa module cùng tier với nó. Một module `partner` chỉ trích các trang catalog có trong `partner_pages`
  của danh sách cho phép và các mục trong danh sách cho phép có tier `partner` (quyết định D13).
- **Trạng thái** là `draft` cho tới khi tech lead duyệt module, `active` khi học viên thấy nó, `retired` khi nó bị rút
  lại. Mỗi module được một người thứ hai duyệt (người làm, người kiểm); với câu hỏi do agent soạn, người duyệt là một
  chủ module là người.
- **Phiên bản** theo semantic versioning: patch cho sửa câu chữ, minor cho một bài học mới, major khi mục tiêu hay câu
  hỏi kiểm tra thay đổi. Phiên bản major của một module bắt buộc yêu cầu học viên lấy lại chứng nhận.
- **Thân bài học** chỉ chứa những gì không nguồn nào có: mục tiêu, một đoạn dẫn ngắn, chỉ tới các mục nguồn và hai,
  ba câu "tự kiểm tra". Nó không có front-matter; siêu dữ liệu nằm trong `module.yaml`, và H1 của nó trùng tiêu đề bài
  học ở đó.
- **Ngôn ngữ.** Tiếng Anh là bản gốc. Bài học tiếng Việt là file anh em `<NN>-<slug>.vi.md` và module ghi `vi` trong
  `languages` (quyết định D5).
- **Loại bài học** là `reading`, `walkthrough` (một video ngắn) và `worked-example`. Bài kiểm tra và bài thực hành là
  file của module, không phải bài học.
- **Video của bài học** (không bắt buộc, quyết định D8) được khai ở trường `video` của bài: `key` là khoá đối tượng
  dưới tiền tố riêng tư `learn-media/` (`learn-media/<module id>/<NN>-<slug>.mp4` hoặc `.webm`) và `captions` liệt kê
  các ngôn ngữ phụ đề (bắt buộc có `en`), file phụ đề nằm cạnh video dưới tên `<key bỏ phần mở rộng>.<lang>.vtt`. Video
  được dựng tại máy bằng `tools/uat` và tải lên đó, không bao giờ để trong git; API học tập kiểm quyền rồi trả một URL
  ký trước sống trong khoảng của thiết lập `learn.video_url_ttl_seconds`.

## Trích nguồn

Mỗi bài học liệt kê `sources` của nó. Một nguồn là một tham chiếu cộng một mã băm được ghim:

```yaml
sources:
  - ref: doc:CAT-01#22-sources-of-truth-for-process-state
    sha: 9c7ffcfcea34737f
```

| Tham chiếu | Trỏ tới | Được phép khi |
|---|---|---|
| `doc:<catalog id>[#anchor]` (hoặc chỉ ID) | một trang catalog mà trình đọc tài liệu xuất bản | trang không phải loại chỉ chủ nền tảng đọc (SEC-*, ARCH-02/03/04) |
| `adr:<NNNN>[#anchor]` | một ADR ở repo gốc | luôn luôn |
| `skill:<name>#anchor` | một mục của `skill/<name>/SKILL.md` | mục đó có trong danh sách cho phép |
| `steering:<name>#anchor` | một mục của `.kiro/steering/<name>.md` | mục đó có trong danh sách cho phép |
| `context:<repo>#anchor` | một mục trong `CONTEXT.md` của một repo app hoặc Infra | mục đó có trong danh sách cho phép |

- **Anchor** là slug tiêu đề của GitHub. Một mục chạy từ tiêu đề của nó tới tiêu đề kế tiếp cùng cấp hoặc cấp cao hơn.
  Tham chiếu không có anchor là trích cả trang.
- **Ghim** là 16 ký tự hex đầu của SHA-256 của mục. Không bao giờ viết tay: đọc mục đó, rồi chạy
  `python tools/docs/check_learn.py --pin`, lệnh này ghi mã băm hiện tại vào `module.yaml`.
- **Khi một mục được trích thay đổi**, bước kiểm báo lỗi ở pull request kế tiếp. Chủ module đọc mục đã đổi, cập nhật bài
  học và các câu hỏi trích mục đó nếu cần, rồi ghim lại. Một lần ghim lại mà không có bước đọc đó làm mất tác dụng của
  bước kiểm.
- **Câu hỏi kiểm tra** trích một trong các nguồn bài học của module, có anchor. Khi mục đó đổi, câu hỏi bị tạm ngưng
  cho tới khi được xem lại.

## Danh sách cho phép

[`allowlist.yaml`](allowlist.yaml) là đường duy nhất để một mục của skill, file steering hay `CONTEXT.md` vào được gói
learn: mỗi mục một dòng, kèm tier và lý do; thứ gì không có trong danh sách thì không bao giờ được xuất bản (mặc định
từ chối). Danh sách thứ hai, `partner_pages`, nêu các trang catalog mà module cho đại lý được trích. Lớp chặn che giấu
thông tin của trình đọc tài liệu chạy trên mọi mục có trong danh sách. Sửa danh sách cho phép là mở rộng ai được đọc
gì, nên được review như một thay đổi rủi ro (xác thực và quyền truy cập) trước khi merge.

## Các bước kiểm

| Ở đâu | Chạy gì | Báo lỗi khi |
|---|---|---|
| Docs lint, mọi pull request ở repo gốc có chạm `docs/**` hoặc `tools/docs/**` | `python tools/docs/check_learn.py`, và các unit test `tools/docs/test_check_learn.py` và `tools/docs/test_learn_bundle.py` | một file sai schema, ID trùng, tham chiếu không tìm thấy, ghim thiếu hoặc đã đổi, module đại lý trích trang dành cho nhân sự, mục được trích nằm ngoài danh sách cho phép, vòng lặp điều kiện trước, account ID hay resource ID trong nội dung khoá học |
| Docs sync, trên master | `python tools/docs/build_learn_bundle.py`, với các file `CONTEXT.md` của các repo app được checkout | mọi lỗi khoá học trừ lệch nguồn; lệch nguồn được xuất bản ở dạng cũ (bên dưới) |

Chạy chúng ở máy trước khi push:

```bash
python3 tools/docs/check_learn.py
python3 tools/docs/check_learn.py --ext-root <workspace-root> --strict-external
python3 -m unittest discover -s tools/docs -p 'test_*learn*.py'
python3 tools/docs/build_learn_bundle.py --check --ext-root <workspace-root>
```

Dòng thứ hai kiểm thêm các mục `context:` với các repo app: `<workspace-root>` là thư mục chứa `apps/<repo>` và
`infra/AA-CIS-Infra`.

## Gói learn

Workflow Docs sync dựng gói learn sau khi đã tải các trang tài liệu lên, vào một thư mục riêng, và tải nó lên dưới tiền
tố của trình đọc tài liệu ở `learn/`. Lỗi khoá học không bao giờ chặn các trang: các bước learn chạy sau cùng, một lần
dựng lỗi không tải gì lên cho learn (gói trước đó vẫn giữ), và chỉ lượt chạy chuyển đỏ.

| Đối tượng | Chứa gì |
|---|---|
| `learn/manifest.json` | lộ trình, module và bài học kèm siêu dữ liệu, mọi mục được trích kèm mã băm hiện tại và tier, với mỗi bài học, nguồn nào đã cũ, và khoá video cùng phụ đề của bài (dưới `learn-media/`, không dưới `learn/`). Nó không bao giờ chứa đáp án |
| `learn/lessons/<module folder>/<NN>-<slug>.md` | thân bài học và bản dịch, đã che thông tin |
| `learn/sections/<kind>/<name>/<anchor>.md` | nội dung đã che thông tin của từng mục được trích |
| `learn/quizzes/<module id>.json` | các câu hỏi kèm đáp án và cờ `suspended`. Chỉ API học tập đọc ở phía máy chủ; đáp án không bao giờ tới trình duyệt trước khi nộp bài |

**Cũ.** Trên master, một mục nguồn ở repo gốc đã đổi không giữ khoá học lại: bài học được đánh dấu cũ, các câu hỏi
trích mục đó bị tạm ngưng, và API học tập mở một mục xem lại nội dung cho chủ module (nghiên cứu GUIDE-13 §6.4). Một
file `CONTEXT.md` của repo app không đọc được, hoặc mất mục được trích, cũng đánh dấu cũ các bài học của nó như vậy.
Định dạng đầy đủ nằm ở phần đầu file `tools/docs/build_learn_bundle.py`.

## Liên quan

- [Nghiên cứu và quyết định của AA Academy](../research/lms/README.vi.md) và [bản kiểm kê tri thức](../research/lms/inventory.vi.md)
- [Quy tắc làm việc](../guides/working-rules/README.vi.md), các trang quy tắc mà bài học trích
- [Hướng dẫn văn phong tài liệu](../STYLE.md)
