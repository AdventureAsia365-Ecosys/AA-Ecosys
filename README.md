# AA-Ecosys

Thư mục gốc gom các repo của hệ sinh thái Adventure Asia. **Multi-repo**: mỗi app có `.git` riêng,
deploy độc lập; thư mục này chỉ để gom lại cho dễ làm việc. Tất cả nằm dưới org GitHub
**`AdventureAsia365-Ecosys`** (đổi tên từ `AdventureAsia365-CIS`).

## Cấu trúc

```
AA-Ecosys/
├── apps/
│   ├── AA-CIS-App/          # repo AA-CIS-App — FastAPI backend (CIS + ACPv2) + Admin FE + Tenant Portal
│   └── AA-TripPlanner-Web/  # repo AA-TripPlanner-Web — B2C map-first trip planner (Next.js FE + 2 Lambda)
├── infra/
│   └── AA-CIS-Infra/        # repo AA-CIS-Infra — Terraform: VPC, RDS, ECS, Lambda, API GW, OIDC, Bedrock
├── docs/                    # tài liệu cấp hệ sinh thái (không thuộc repo con)
└── skill/                   # ghi chú/skill nội bộ
```

> Tên thư mục local khớp **chính xác** tên repo GitHub để nhìn là biết map sang repo nào.

## Repo & deploy

| Thư mục | Repo | Deploy |
|---------|------|--------|
| `apps/AA-CIS-App` | `AdventureAsia365-Ecosys/AA-CIS-App` | ECS Fargate (api) + Vercel (frontend) |
| `apps/AA-TripPlanner-Web` | `AdventureAsia365-Ecosys/AA-TripPlanner-Web` | Vercel (FE) + Lambda (BE) |
| `infra/AA-CIS-Infra` | `AdventureAsia365-Ecosys/AA-CIS-Infra` | GitHub Actions (aa365) + human/MFA (acc1/acc3) |

Sắp có: `AA-Booking` (AAA) — xem `docs/tripplanner-to-aaa-handoff.md`.

## Tài liệu cấp hệ

- [`docs/ecosystem-architecture.md`](docs/ecosystem-architecture.md) — kiến trúc toàn hệ (sơ đồ, phân vai schema, data contracts, OIDC).
- [`docs/tripplanner-to-aaa-handoff.md`](docs/tripplanner-to-aaa-handoff.md) — spec bàn giao TripPlanner → AA-Booking (nháp, chờ AAA).
- [`docs/inventory-old-refs.md`](docs/inventory-old-refs.md) — kiểm kê tham chiếu tên org/repo/path cũ (phục vụ đổi tên org).

## Lưu ý vận hành

- Mỗi thư mục con là một git repo độc lập — `cd` vào đó để chạy git/CI của riêng nó.
- Đổi tên org đang theo nguyên tắc **OIDC trust mở rộng (chấp nhận cả tên cũ + mới) TRƯỚC, đổi tên SAU,
  gỡ trust cũ sau cùng**. Chi tiết trong `docs/`.
- Trên WSL, đường dẫn thật là `~/projects/AA-Ecosys/` (không phải `~/projects/aa-cis/` như một số ghi chú cũ).
