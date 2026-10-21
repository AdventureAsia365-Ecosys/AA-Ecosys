# Request to eCloudvalley: let account 786888028788 use Claude Haiku 5.5 and Sonnet 5.5 on Bedrock

Status: **NOT NEEDED, do not send** (S246, 16:29 UTC). The block cleared on its own. CloudTrail shows the same invoker role succeeding at 14:59 UTC, then denied from 15:56 UTC. The Marketplace subscription that the first call starts in the background had failed: the role has no aws-marketplace permission. After `create-foundation-model-agreement` (15:58 UTC, admin user), access took about 30 minutes to take effect. Smoke at 16:29 UTC: Haiku 5.5 and Sonnet 5.5 are OK on acc3, both plain and schema. The text below is kept only as a record.

---

Chào anh/chị bên eCloudvalley,

Bên mình đang dùng Amazon Bedrock trên tài khoản **786888028788** (region us-west-1). Bên mình cần gọi 2 model mới của Anthropic:

- Claude Haiku 5.5: `global.anthropic.claude-haiku-5-5`
- Claude Sonnet 5.5: `global.anthropic.claude-sonnet-5-5`

Những gì bên mình đã làm:

1. Đã tạo model agreement cho cả 2 model. Trạng thái hiện là **AVAILABLE**.
2. Đã gọi thử, kể cả bằng user admin của tài khoản. Lần nào cũng bị từ chối với lỗi:

   > AccessDeniedException: Model access is denied due to IAM user or service role is not authorized to perform the required AWS Marketplace actions (aws-marketplace:ViewSubscriptions, aws-marketplace:Subscribe) to enable access to this model.

3. Các model Claude cũ hơn (Haiku 4.5, Sonnet 4.6) trên cùng tài khoản vẫn gọi bình thường.

Bên mình nghĩ quyền AWS Marketplace đang bị chặn ở cấp tổ chức (SCP) hoặc ở tài khoản payer. Nhờ anh/chị:

1. Cho phép `aws-marketplace:ViewSubscriptions` và `aws-marketplace:Subscribe` cho tài khoản 786888028788, ít nhất cho 2 model trên. Nếu bên anh/chị subscribe giúp từ phía payer thì cũng được.
2. Báo bên mình biết khi xong, bên mình sẽ gọi thử lại.

Mình cảm ơn.
