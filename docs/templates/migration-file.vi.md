---
id: TPL-01-migration
title: Mẫu file migration
description: Header, transaction, tự đăng ký và hình dạng expand / contract mà mọi file migration cơ sở dữ liệu bắt đầu từ đó.
type: template
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem]
last_reviewed: 2026-11-14
review_every_days: 180
related: [TPL-01, docs/architecture/data-standards/01-engineering.md]
lang: vi
translation_of: docs/templates/migration-file.md
---

# Mẫu file migration

Chép khối dưới vào `db/migrations/<prefix>-<NNN>_<slug>.sql`. Nó theo các luật migration MIG-1 tới MIG-14 của AA
([data standards Part A](../architecture/data-standards/01-engineering.md)) ở dạng chung: mỗi schema một chủ sở hữu và
một dải số, chỉ đi tới, idempotent, expand / contract cho mọi thay đổi hình dạng, chỉ áp từ CI.

```sql
-- Migration <prefix>-<NNN>: <ISSUE-KEY> — <what changes and why, one line>
-- Phase: expand | contract | data | destructive
-- Touches (lock-sensitive): <schema.table, ...> | none
-- migrate: <no-transaction | destructive>   (only when needed; delete otherwise)
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '15min';

-- Expand: add, never rename or drop in the same release.
CREATE TABLE IF NOT EXISTS <schema>.<table> (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id   uuid NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE <schema>.<table> ADD COLUMN IF NOT EXISTS <column> text;
-- A NOT NULL on an existing table: add CHECK (...) NOT VALID here, VALIDATE in a later file.

-- Grants for the runtime role (least privilege).
GRANT SELECT, INSERT, UPDATE ON <schema>.<table> TO <app_runtime_role>;

-- Self-registration: how the runner knows this file ran.
INSERT INTO <schema>.schema_versions (version, description)
VALUES ('<prefix>-<NNN>', '<slug>')
ON CONFLICT (version) DO NOTHING;
COMMIT;
```

## Luật người review kiểm

- [ ] File chỉ đụng tới schema của chủ sở hữu nó và dòng đăng ký của chính nó.
- [ ] Chạy lại không làm gì thêm (`IF NOT EXISTS`, `ON CONFLICT DO NOTHING`, `CREATE OR REPLACE` cho view).
- [ ] Đổi tên hay xoá được tách ra: expand, ship bên đọc và bên ghi chạy trên cả hai hình dạng, rồi contract ở một file
  sau.
- [ ] Không backfill lớn trong migration (quá khoảng 10.000 dòng thì chuyển sang một job).
- [ ] Một file phá huỷ theo quy trình chạy thử: đưa số đếm chính xác, chụp snapshot, ghi lại lời duyệt.
- [ ] Không có down migration; hoàn tác là một file đi tới mới.
- [ ] Được áp bởi workflow migrate của CI, không bao giờ từ máy cá nhân hay lúc app khởi động.
