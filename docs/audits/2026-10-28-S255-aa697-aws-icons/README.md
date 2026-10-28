# AA-697 — thử vẽ sơ đồ kiến trúc bằng icon AWS (S255, 28/10/2026)

Tech lead nhắc lại: sơ đồ trên `/admin/docs` nên dùng icon AWS chuẩn, không vẽ ô chữ trơn. Bản thử này kiểm cách làm trước
khi lên lịch AA-697 (đề xuất S257). Chưa đổi gì trong app.

## Đã thử
- Mermaid **12.2.0** (đúng bản CIS dùng), kiểu sơ đồ `architecture-beta`, bộ icon Iconify `@iconify-json/logos` (65 icon
  dịch vụ AWS) đăng ký bằng `mermaid.registerIconPacks`.
- Chạy qua đúng các lớp an toàn của trang Docs: `securityLevel: strict` → DOMPurify hồ sơ SVG (`foreignObject`, `image`,
  `use` bị bỏ) → kiểm không có tham chiếu ra ngoài (`svgIsSelfContained`). Kết quả: 0 `foreignObject`, không tham chiếu
  ngoài, SVG 47 KB.
- File: `prototype-architecture-beta.mmd` (nguồn), `prototype-architecture-beta.png` (ảnh), `render-prototype.mjs`
  (script Playwright; bản thử nạp mermaid/dompurify từ jsDelivr, bản thật phải đóng gói vào app, không gọi CDN).

## Kết quả
- Icon hiện đúng kiểu AWS: CloudFront, API Gateway, Fargate, Lambda, RDS, S3, Cognito, VPC, IAM.
- Hạn chế: Mermaid tự xếp bố cục (mũi tên cắt qua nhóm, chữ đè lên đường), cạnh không có nhãn, bộ `logos` **không có
  icon Bedrock**.
- Trang Docs hiện **không hiện ảnh** (`MarkdownView` đổi `![…]` thành chữ `[image: …]`): SVG vẽ bằng `diagrams` / draw.io
  chưa hiện được cho tới khi reader biết hiện SVG nằm trong bundle docs.

## Đề xuất (chi tiết trong comment AA-697 trên Linear)
1. Sơ đồ AWS chính: Python `diagrams` (mingrammer) qua `awslabs.aws-diagram-mcp-server` — icon AWS chính thức (có
   Bedrock), bố cục Graphviz; nguồn `docs/architecture/diagrams/*.py`, Docs sync render SVG trong CI.
2. Reader: cho hiện ảnh `.svg` tương đối nằm trong bundle docs (qua cùng API docs), cùng lớp lọc DOMPurify +
   `svgIsSelfContained`; ảnh khác vẫn là chữ.
3. Sơ đồ nhỏ trong trang: Mermaid `architecture-beta` + bộ `logos` đóng gói lazy, thêm bộ icon riêng cho Bedrock từ gói
   AWS Architecture Icons chính thức; chờ `document.fonts.ready` trước khi vẽ (sửa chữ bị ngắt giữa từ).
4. Giữ TerraVision để đối chiếu với Terraform; C4 / flowchart cho phần không phải AWS.
