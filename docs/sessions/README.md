# Session Logs — AA-Ecosys

Nhật ký từng phiên làm việc (Kiro / Claude Code / phiên khác) để bàn giao ngữ cảnh:
đã làm task gì, thay đổi gì về **codebase** và **hạ tầng**, còn gì chưa xong.

## Quy ước
- Mỗi phiên = 1 file `YYYY-MM-DD-<chu-de-ngan>.md`.
- Bắt buộc có các mục: Trạng thái, Thay đổi Codebase, Thay đổi Hạ tầng, Bằng chứng verify,
  Còn lại (việc chưa xong), Lưu ý kỹ thuật cho phiên sau.
- Ghi FACT đã verify; đánh dấu rõ phần suy đoán / chưa verify.
- Số liệu vận hành hay đổi (task def, migration số, PROD state) → không hard-code ở đây, tham chiếu nguồn thật.

## Index
| Ngày | Chủ đề | File |
|------|--------|------|
| 2026-09-17 | S185 — AA-608 follow-up (regex meal precision + flag_fix json salvage, PR #390) verify 27/27 approved MEAL 87%→33%; 3 sub AA-607: gỡ s1-from-atom (PR #391), gỡ star no-op (PR #392), fix bug T2 brand fetch (PR #393); note nợ cleanup batch data vào AA-600, drop column vào AA-603 | [2026-09-17-AA608-followup-AA607-subs-S185.md](2026-09-17-AA608-followup-AA607-subs-S185.md) |
| 2026-09-16 | S184 — Reset residual DB + cost=0, fix bug S0/S1 tours-ready (PR #387) + trash 30 POI, dịch i18n admin (PR #388), điều tra 2 luồng viết → epic AA-607 + AA-606 Bedrock Batch, cancel AA-495 | [2026-09-16-CIS-reset-residual-writeflows-S184.md](2026-09-16-CIS-reset-residual-writeflows-S184.md) |
| 2026-09-16 | S183 — CIS Data Reset G0-G3 (backup+bastion+tunnel, điều tra, script DELETE, reset commit), phát hiện N7/N8 dead, AA-603 tạo, audit UI residual | [2026-09-16-CIS-audit-G0-G3-S183.md](2026-09-16-CIS-audit-G0-G3-S183.md) |
| 2026-09-16 | S182 — TripPlanner MAP/UI deploy (Ms.Thư #4/#5 + nợ UI) + khung audit CIS data reset + DB tunnel guide | [2026-09-16-AA-ECOSYS-dev-S182.md](2026-09-16-AA-ECOSYS-dev-S182.md) |
| 2026-09-15 | AA-Ecosys restructure (đổi tên org, gom multi-repo, OIDC transitional) | [2026-09-15-aa-ecosys-restructure.md](2026-09-15-aa-ecosys-restructure.md) |

<!-- Thêm dòng mới lên đầu bảng cho mỗi phiên. -->
