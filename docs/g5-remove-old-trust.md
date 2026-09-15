# G5 — Gỡ trust tên org cũ khỏi OIDC (bản chuẩn bị, CHƯA apply)

> **CHỈ áp dụng sau khi:** org đã đổi tên sang `AdventureAsia365-Ecosys`, remote đã cập nhật,
> và đã có **vài ngày** deploy xanh ổn định **chỉ với org mới** (không còn workflow nào chạy dưới tên cũ).
> Gỡ sớm sẽ làm hỏng deploy nếu còn ref/redirect nào dùng tên cũ.
>
> **Tiền đề (Task 4) — ĐÃ XÁC MINH 15/09/2026:** OIDC "Subject claim template" ở cấp **org**
> (Settings → Actions → OIDC) đang **TRỐNG** và "Use immutable subject claim" **KHÔNG** bật.
> → Customization là **repo-level** (chỉ `AA-TripPlanner-Web` tự bật dạng `@<id>`), **KHÔNG** org-level.
> → Ở `cicd.tf` **BỎ** dòng wildcard dư `repo:AdventureAsia365-Ecosys*/*:*`, chỉ giữ dạng phẳng
>   `repo:AdventureAsia365-Ecosys/*:*` (giống pattern org cũ đã chạy được).

## 1. `accounts/aa365/cicd.tf` — role `aa-cis-dev-role`

**Hiện tại (transitional, sau G2):**
```hcl
StringLike = {
  "token.actions.githubusercontent.com:sub" = [
    "repo:AdventureAsia365-CIS/*:*",
    "repo:AdventureAsia365-Ecosys/*:*",
    "repo:AdventureAsia365-Ecosys*/*:*",
  ]
}
```

**Mục tiêu G5 (Task 4 = repo-level → giữ dạng phẳng, quay lại string đơn):**
```hcl
StringLike = {
  "token.actions.githubusercontent.com:sub" = "repo:AdventureAsia365-Ecosys/*:*"
}
```
Đồng thời **xoá** block comment `# TRANSITIONAL (...)`.

## 2. `accounts/aa365/tripplanner.tf` — role `aa-tripplanner-dev-app-deploy`

**Hiện tại (transitional, sau G2):**
```hcl
StringLike = {
  "token.actions.githubusercontent.com:sub" = [
    "repo:AdventureAsia365-CIS*/AA-TripPlanner-Web*:*",
    "repo:AdventureAsia365-Ecosys*/AA-TripPlanner-Web*:*",
  ]
}
```

**Mục tiêu G5 (giữ dạng `@id` wildcard, chỉ còn org mới, quay lại string đơn):**
```hcl
StringLike = {
  "token.actions.githubusercontent.com:sub" = "repo:AdventureAsia365-Ecosys*/AA-TripPlanner-Web*:*"
}
```
Cập nhật comment: bỏ đoạn TRANSITIONAL, giữ lại giải thích về "@<id>" customization.

## 3. Quy trình apply (BẠN/người, MFA)

```bash
cd infra/AA-CIS-Infra/accounts/aa365
terraform fmt cicd.tf tripplanner.tf
terraform validate                    # kỳ vọng: Success
terraform plan                        # đọc FULL log — kỳ vọng chỉ đụng 2 assume-role policy
# xác nhận không resource nào khác thay đổi
terraform apply                       # MFA
```

## 4. Verify sau apply

- Chạy 1 deploy trên **org mới**: TripPlanner `deploy-lambdas`, CIS `deploy-dev`, infra `terraform-plan`.
- `aws sts get-caller-identity` trong workflow phải OK; deploy xanh.
- Xác nhận **không** còn workflow nào chạy dưới tên org cũ (Actions history sạch tên cũ).

## 5. Dọn docs sau G5

- Cập nhật `docs/ecosystem-architecture.md` §5: bỏ phần "[CẦN XÁC NHẬN] org vs repo level" (đã chốt ở Task 4)
  và bỏ mô tả trạng thái transitional (chỉ còn org mới).
- Đóng checklist G5 trong kế hoạch restructure.

## 6. Nguồn

- `docs/inventory-old-refs.md` mục #1, #2 (Loại A).
- Diff transitional đã apply ở G2 (commit sửa `cicd.tf` + `tripplanner.tf`).
