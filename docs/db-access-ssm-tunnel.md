# Truy cập RDS acc2 từ máy local (Kiro/WSL) qua SSM tunnel + SQLTools

> Mục đích: cho phép query trực tiếp PostgreSQL RDS (acc2) **trong IDE** khi làm data-ops
> (cleanup, upload raw trips, auto-edit) — thay vì chỉ đọc gián tiếp qua ECS exec / S3-mediated query.
>
> **Trạng thái:** hướng dẫn + script chuẩn bị. Chưa dựng gì. Tunnel là kết nối **tạm thời**
> (mở khi cần, đóng là hết) — KHÔNG mở public RDS, KHÔNG đụng SG/network vĩnh viễn.

## 0. Bối cảnh hạ tầng (verify từ Terraform + skill, 16/09/2026)

| Thành phần | Giá trị thật |
|---|---|
| Account | `005097885195` (acc2) |
| Region | `us-west-1` |
| Profile | `aa365-admin` (cần MFA cho một số action) |
| RDS instance id | `aa-cis-dev-db` |
| DB (CIS) | `aa_cis_dev` · user `aa_cis_admin` |
| DB secret | `aa-cis/dev/rds` (Secrets Manager, **plain DSN string**) |
| Schema TripPlanner | `tripplanner.*` + dùng chung `shared.destinations` (cùng instance) |
| ECS cluster / service / container | `aa-cis-dev-cluster` / `aa-cis-dev-api` / `api` |
| SG RDS | `aa-cis-dev-sg-rds` |

RDS nằm trong **DB subnet private, không public-accessible** (đúng chuẩn). Máy WSL không route
thẳng tới được → phải đi qua một điểm trung gian TRONG VPC. Đó là lý do cần tunnel.

## 1. Ràng buộc quan trọng — Fargate vs SSM port forwarding

SSM document `AWS-StartPortForwardingSessionToRemoteHost` map một cổng remote (RDS:5432) về
`localhost` — NHƯNG **chỉ chạy trên target là EC2 instance có SSM agent**. Service `aa-cis-dev-api`
là **ECS Fargate** (ECS Exec dùng SSM channel nhưng KHÔNG expose port-forwarding-to-remote-host).

→ Có 3 đường khả thi. Chọn theo mức tiện/an toàn:

- **A. Bastion EC2 tạm (khuyến nghị cho tunnel “trực tiếp trong IDE”)** — tạo 1 EC2 nhỏ
  (t3.micro) trong private subnet cùng VPC, có SSM agent + IAM `AmazonSSMManagedInstanceCore`,
  SG cho phép egress tới SG RDS:5432. Port-forward RDS về `localhost:5432`. Terminate khi xong.
- **B. socat trong ECS Exec (không tạo hạ tầng mới)** — `aws ecs execute-command` vào container
  `api`, chạy `socat` chuyển tiếp 5432. Vướng: container không có sẵn socat, ECS Exec là
  interactive shell chứ không phải local port map → phức tạp, KHÔNG khuyến nghị.
- **C. Giữ nguyên S3-mediated ECS exec** — an toàn nhất, không mở bề mặt mạng, nhưng không phải
  “query trực tiếp trong IDE” (chạy script Python trong container). Đây là cách hiện tại.

Hướng dẫn dưới đi theo **đường A** (bastion tạm) vì đúng yêu cầu “trực tiếp trong IDE”.
Việc TẠO bastion là **chạm hạ tầng** → cần Nghiệp duyệt trước khi chạy.

## 2. Điều kiện tiên quyết (local)

```bash
# AWS CLI v2 + Session Manager plugin
aws --version                      # v2.x
session-manager-plugin             # phải in ra version; nếu thiếu:
#   Ubuntu/WSL: tải .deb từ AWS docs "Install the Session Manager plugin"
#   curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o smp.deb && sudo dpkg -i smp.deb

# MFA credentials cho profile aa365-admin (một số action RDS/EC2 cần) — nạp vào env:
export $(aws configure export-credentials --profile aa365-admin --format env | xargs) && unset AWS_PROFILE
```

## 3. Lấy DB credentials từ Secrets Manager (chỉ đọc, không in ra chat)

```bash
# DSN đầy đủ (host RDS, user, password, dbname) — dùng để cấu hình SQLTools.
aws secretsmanager get-secret-value \
  --secret-id aa-cis/dev/rds \
  --region us-west-1 \
  --query SecretString --output text
```

Tách các phần từ DSN `postgresql://<user>:<pass>@<rds-host>:5432/<db>`:
- `<rds-host>` = endpoint RDS thật (dùng làm remote host cho port-forward).
- `<user>` / `<pass>` / `<db>` = điền vào SQLTools.

> ⚠️ Không paste password vào file commit. SQLTools có thể đọc password từ biến môi trường
> hoặc hỏi lúc connect (xem §6).

Lấy nhanh RDS endpoint (nếu cần tách riêng):
```bash
aws rds describe-db-instances --db-instance-identifier aa-cis-dev-db \
  --region us-west-1 --query 'DBInstances[0].Endpoint.Address' --output text
```

## 4. (Đường A) Dựng bastion tạm — CẦN NGHIỆP DUYỆT

Ý tưởng: 1 EC2 t3.micro trong **private subnet** cùng VPC RDS, quản lý qua SSM (không cần SSH key,
không cần public IP). Sau khi xong việc → **terminate**.

Các bước (tóm tắt, chưa chạy):
1. Lấy VPC/subnet/SG hiện có từ Terraform outputs (`envs/dev`) — private DB subnet + SG cho phép
   egress 5432 tới SG RDS. RDS SG phải cho phép ingress 5432 từ SG bastion (một sửa đổi SG tạm,
   hoặc dùng SG sẵn có mà RDS đã trust).
2. Launch EC2 Amazon Linux 2023 (SSM agent có sẵn), instance profile có
   `AmazonSSMManagedInstanceCore`, đặt trong private subnet.
3. Chờ instance `online` trong SSM: `aws ssm describe-instance-information`.

> Đây là phần chạm hạ tầng (EC2 + có thể sửa SG). KHÔNG tự chạy. Khi Nghiệp duyệt, mình soạn
> lệnh cụ thể/Terraform-ephemeral tương ứng.

## 5. Mở tunnel (script)

Xem `docs/db-tunnel.sh`. Cách dùng:
```bash
./docs/db-tunnel.sh <bastion-instance-id> <rds-host>
# ví dụ: ./docs/db-tunnel.sh i-0abc123 aa-cis-dev-db.xxxx.us-west-1.rds.amazonaws.com
# → giữ terminal này mở; RDS giờ ở localhost:5432
```

## 6. Cấu hình SQLTools trong Kiro

1. Cài extension: **SQLTools** (`mtxr.sqltools`) + driver **SQLTools PostgreSQL/Cockroach**
   (`mtxr.sqltools-driver-pg`). (Kiro là VS Code-based → cài như extension bình thường.)
2. Đã có sẵn file workspace `.vscode/settings.json` với connection `AA RDS (tunnel)` trỏ
   `localhost:5432` (xem §7). Mở panel SQLTools → Connect → nhập password (từ §3) khi được hỏi.
3. Chọn database: `aa_cis_dev`. Query thử an toàn:
   ```sql
   SELECT current_database(), current_user;
   SELECT count(*) FROM shared.destinations;      -- bảng dùng chung TripPlanner
   SELECT table_name FROM information_schema.tables WHERE table_schema='tripplanner';
   ```

## 7. File cấu hình đi kèm

- `docs/db-tunnel.sh` — script mở SSM port-forward (đường A).
- `.vscode/settings.json` — connection SQLTools mẫu (`localhost:5432`, password rỗng → SQLTools hỏi lúc connect).

## 8. An toàn / dọn dẹp

- Tunnel là session tạm: `Ctrl+C` để đóng. Không để mở khi không dùng.
- Bastion (đường A): `aws ec2 terminate-instances --instance-ids <id>` sau khi xong. Revert
  sửa đổi SG tạm nếu có.
- KHÔNG bật `publicly_accessible` cho RDS. KHÔNG mở 5432 ra 0.0.0.0/0.
- Query data-ops đụng PROD: luôn `BEGIN; ... ; -- kiểm tra rồi COMMIT/ROLLBACK`, backup trước
  khi UPDATE/DELETE hàng loạt.
