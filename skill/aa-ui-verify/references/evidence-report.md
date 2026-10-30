# Báo cáo bằng chứng live nhiều mục (evidence lane)

Dùng khi một lane kiểm live **nhiều mục đã deploy** (mỗi mục = issue + PR) và gom vào một báo cáo. Cách đăng nhập theo vai:
SKILL §3 (bảng), §3a, §3b. Checklist từng trang (1440/390, light/dark, console, network, dữ liệu): SKILL §3 bước 4.
Comment Done và luật bằng chứng: `aa-ship` §4. Nơi lưu: `aa-session` mục "Audit/báo cáo/artifact". Mẫu đã chạy:
`docs/audits/2026-10-30-S260-evidence/README.md`.

## Luật

- Thư mục `docs/audits/<ngày>-S<nnn>-evidence/`: `README.md` + PNG + `data/`. Tên ảnh bắt đầu bằng số mục (`04c-…png`).
- Mỗi mục có số; mỗi mục con ghi **PASS/FAIL** kèm tên file. Đường bị từ chối (`e2e_read_only`, chỉ empty state, chỉ
  dry run) ghi **not tested + lý do**, không ghi PASS. Câu "chạy được" chỉ cho đúng kênh/vai đã thử.
- Chỉ ghi giá trị đọc thật từ trang hay API. Thiếu dữ liệu → ghi thiếu.
- Hành động phá huỷ (erase, xoá thật) chỉ chạy dry run. Dữ liệu test chỉ ghi qua UI bình thường, trên agency/tenant
  tổng hợp; liệt kê trong mục "Test data written".
- `data/` đã che: id → `<uuid>`, chữ tự do → `<str>`, bỏ phần account trong ARN; giữ tiền, trạng thái, mã lỗi. Tên
  người che trong README và data. Vai ghi theo vai, không ghi mã, secret; không chụp trên host managed login.
- Phát hiện ghi thành F1..Fn; lane bằng chứng **không sửa**, chỉ đề xuất.
- Lane thứ hai/ba cùng ngày → nối thêm mục "Second lane" / "Third lane" vào cùng README (giờ, host + SHA lúc chạy).

## Khung README (tiếng Anh, front-matter theo `docs/STYLE.md`, `type: report`)

```
# S<nnn> live evidence (<dd/mm/yyyy>, <hh:mm>–<hh:mm> +07)

<Browser + version, one browser at a time.> Hosts, after their deploys were green:
<host> (<deployed SHA>; `/health/ready` <git_sha> / schema <key>), ...

Identities (by role; codes and secrets read at run time, never written down; no screenshot on the managed-login host):
- **<app>:** <role / E2E user kind>

Console errors = `console.error` / uncaught page errors on the app origin. Failing requests = responses >= 400 on the
app origin. Raw records in `data/` (ids -> `<uuid>`, free text -> `<str>`; money, status, error codes kept).

## Results
| # | Item (issue + PR) | Result |
|---|---|---|
| 1 | AA-xxx <title> (<Repo> #n) | **PASS** / **FAIL** (<short note, finding Fn>) |

### 1. <item>
- <sub-item>: **PASS** — <what was seen> (`01-<name>-{1440,390}-{light,dark}.png`)
- <sub-item>: not tested — <why>
- Console errors <n>, failing requests <n> (`data/<file>.json`)

## Findings
- **F1 — <symptom>.** `<file>:<line>`. Repro: <steps>. Proposed fix: <...>. Not fixed in this lane.

## Not covered
- <path> — <why>

## Test data written
- <agency/tenant>: <rows created through the UI>

## Second lane (<time>): items <n>–<m>
<hosts + SHA during the lane, then the same sections>
```
