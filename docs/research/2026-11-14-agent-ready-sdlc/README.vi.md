# SDLC sẵn sàng cho agent: AWS AI-DLC và playbook của Anthropic so với cách làm của AA

Ghi chú nghiên cứu, S280, 14/11/2026. Người viết: Claude Code (lane nghiên cứu). Chỉ đọc: không sửa code, không gọi
AWS, không gọi dịch vụ trả tiền. Thông tin bên ngoài lấy từ ba file ghi chú nguồn trong thư mục này
(`src-aws-aidlc.md`, `src-anthropic-playbook.md`, `src-origin-and-field.md`). Mỗi nguồn được đọc như sau:

- **Rule file và engine của AWS:** đọc từ bản clone `awslabs/aidlc-workflows` (v1.0.1 và `main` tại d8dd27dc).
- **PDF playbook của Anthropic:** trích dẫn và số trang được đối chiếu với một bản trích văn bản của PDF làm trong phiên
  này (53 trang có chữ; trang bìa không có lớp chữ). Số trang in ở chân trang khớp với các chỗ dẫn tr.3, tr.7, tr.9 và
  tr.22. Công cụ tạo bản trích không được ghi lại, và hiện không có công cụ đọc chữ PDF nào được cài, nên không làm lại
  bản trích ở đây được. Ở điểm này, `src-origin-and-field.md` §2 và §6 ("đã tải, chưa đọc") được thay bằng
  `src-anthropic-playbook.md`.
- **Bài phương pháp AI-DLC và PDF đặc tả v2:** trích dẫn lấy từ `src-aws-aidlc.md`, file này ghi là đã đọc từ chính các
  file. `src-origin-and-field.md` §6 lại ghi hai tài liệu này chưa mở. Chữ trong hai PDF được mã hoá theo font nên không
  kiểm lại được ở đây; coi các trích dẫn đó là **chưa kiểm lại**.
- **Trang web:** các trang của Böckeler, DORA, NN/g, Scrum.org, Kiro, Thoughtworks, Endor Labs, Clinton và blog ra mắt
  của AWS được một reviewer mở lại ngày 14/11/2026, và các dòng bị tranh cãi được mở lại lần nữa khi áp dụng review.

Mọi khẳng định về AWS hay Anthropic dưới đây đều kèm URL, và cùng các URL đó được liệt kê ở [Nguồn](#8-nguồn). Thông tin
về AA lấy từ repo gốc (`master`) ngày 14/11/2026 và có ghi đường dẫn file. Đây là bản dịch tiếng Việt của
[README.md](README.md); bản tiếng Anh là bản gốc.

Điểm khởi đầu là một infographic tên "Agent-Ready SDLC" (được cho là của Rakesh Gohel). Tech lead muốn đọc tài liệu gốc
đằng sau nó, xem có gì đáng học, và cách đưa cách làm hay vào bộ kit dự án mới và trang học. **Phạm vi:** trong ghi chú
này, "kit" và "Academy" là bộ kit dự án mới và AA Academy của chính AA (thiết kế AA-1098 và AA-1099, issue build AA-1102
tới AA-1105). Không nội dung nào trong ghi chú này dành cho sản phẩm ngoài AA.

## 1. Tóm tắt

- **AI-DLC (AWS):** một phương pháp kèm bộ rule MIT-0. AI dẫn dắt, hỏi trong file và dừng ở cổng duyệt của người sau mỗi
  giai đoạn, bỏ qua giai đoạn khi việc nhỏ. v1 khoảng 30 file rule; v2 là một engine lớn (33 giai đoạn, 14 agent).
- **Playbook Anthropic:** hướng dẫn 54 trang (không có giấy phép mở). Sáu giai đoạn, mỗi giai đoạn commit một artifact cho
  giai đoạn sau đọc (`intent.md`, `spec.md`, `plan.md`, diff, kết quả review PR, sự cố). Người có tên ký duyệt; agent không
  được vượt cổng production.
- **Bài học chung:** quy tắc văn xuôi chỉ khuyến nghị, hook mới ép được. Không model nào tự chấm bài mình. Sức review là giới hạn.
- **Kết luận cho AA:** ta đã làm phần lớn, có chỗ tốt hơn (bài học phải có guard, review lane độc lập, quyền merge theo
  giai đoạn). Không cài engine AI-DLC, không thêm `intent.md`/`spec.md` cho mỗi thay đổi. Áp dụng bảy ý nhỏ (mục 7) qua
  các issue build kit và Academy của AA, AA-1102 tới AA-1105, chi phí 0 USD. Năm ý có phép kiểm tất định đi kèm (đề xuất
  2 tới 6). Đề xuất 1 là một trường định tuyến, còn đề xuất 7 vẫn là quy tắc khuyến nghị cho tới khi có template và lint.

## 2. Infographic so với nguồn gốc

Không tìm thấy bài gốc "Agent-Ready SDLC". Tìm kiếm web, kho lưu trữ Substack của tác giả và hai bài mới nhất đều không
có, còn LinkedIn không đọc được nếu không đăng nhập, nên ngày đăng và các nguồn nó trích là **CHƯA KIỂM ĐƯỢC
(UNVERIFIED)**. Nội dung của nó (mỗi giai đoạn commit một artifact, người có tên ký duyệt, agent dừng ở cổng production,
mỗi giai đoạn đọc commit trước) khớp với một tài liệu: playbook của Anthropic
([trang web](https://claude.com/blog/the-ai-native-sdlc-playbook),
[PDF](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)). Tiêu đề đặt nó cạnh AWS AI-DLC
([blog](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)). Một bảng thuật ngữ của nhà cung cấp cũng
ghép hai thuật ngữ này theo cùng cách ([Endor Labs](https://www.endorlabs.com/learn/what-is-the-ai-native-sdlc), nguồn thứ
cấp).

**Chỗ đúng**

- Mỗi giai đoạn ghi một artifact vào version control, và giai đoạn sau bắt đầu bằng việc đọc nó. Playbook nói đúng như
  vậy, và thêm "the chain of commits is also the audit trail" (chuỗi commit cũng là dấu vết kiểm toán)
  ([PDF tr.7](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).
- Người có tên ký duyệt: product owner cho intent và spec, engineer (hoặc tech lead khi rủi ro cao) cho plan, code owner
  cho PR, release manager cho production (cùng PDF, chương 2 tới 5).
- Agent dừng ở cổng production: "The agent may act up to the production gate, and cannot pass it" (cùng PDF, chương
  Deploy).
- AI-DLC cũng đặt một bước duyệt của người ở cuối mỗi giai đoạn
  ([repo v1.0.1](https://github.com/awslabs/aidlc-workflows/tree/v1.0.1), `core-workflow.md`: "Wait for Explicit
  Approval ... DO NOT PROCEED").

**Chỗ sai hoặc giản lược**

- **Eval không phải một file cho từng giai đoạn.** Trong playbook, eval là một bộ 20 tới 50 việc thật ở giai đoạn 4. Bộ
  này chạy trong CI theo lịch và mỗi khi CLAUDE.md, skill hoặc hook thay đổi, và tỷ lệ đạt chặn merge
  ([PDF chương Test](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).
- **Review không phải một giai đoạn riêng.** Các giai đoạn là Plan, Design, Build, Test, Deploy và Maintain. Review PR và
  `REVIEW.md` nằm trong Deploy (cùng PDF). Playbook gọi giai đoạn 6 lúc là "Maintain", lúc là "Maintenance".
- **Một chuỗi cố định là gây hiểu lầm.** Cả hai nguồn nhấn mạnh việc co giãn theo độ lớn việc. AI-DLC đánh dấu mỗi giai
  đoạn EXECUTE hoặc SKIP và chọn độ sâu ([v1.0.1](https://github.com/awslabs/aidlc-workflows/tree/v1.0.1),
  `common/depth-levels.md`). Bản v2 có 11 workflow profile, và profile Bugfix chạy 6 trên 30 giai đoạn
  ([repo](https://github.com/awslabs/aidlc-workflows), `docs/guide/workflow-profiles.md`). Các "play" của playbook là các
  mô-đun độc lập, và bắt đầu bằng những play không cần gì trước
  ([PDF tr.9](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).
- **Tự động hoá là trạng thái đích, không phải điểm bắt đầu.** Playbook nói "First, you prompt each step by hand" (đầu
  tiên, prompt từng bước bằng tay) (PDF tr.9). Nó dựng cổng trước rồi mới tự động hoá bất cứ thứ gì đi qua cổng (chương
  Deploy, điều kiện tiên quyết cho CI/CD).
- **Hai nguồn là hai thứ khác nhau.** AI-DLC là một cuộc hội thoại do AI dẫn dắt, chạy bằng bộ rule hoặc engine, có file
  câu hỏi và nhật ký kiểm toán, dùng trên nhiều công cụ lập trình. Playbook là một chuỗi artifact trong git, dựa trên tính
  năng của Claude Code và vai trò của doanh nghiệp. Gộp chúng thành một "Agent-Ready SDLC" che mất khác biệt đó. AI-DLC là
  tên phương pháp riêng của AWS, không phải thuật ngữ chung
  ([Endor Labs](https://www.endorlabs.com/learn/what-is-the-ai-native-sdlc), nguồn thứ cấp).
- **Không nguồn nào công bố kết quả đo được.** Playbook không có số liệu nào
  ([PDF](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)). Các tuyên bố về tốc độ của AWS không có
  số đo ([blog](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)). Mọi con số trong hình nên coi là
  không có căn cứ.

## 3. AI-DLC chi tiết

### 3.1 Phương pháp (2025)

- **Nguồn:** bài phương pháp 8 trang của Raja SP ([PDF](https://prod.d13rzhkk8cj2z0.amplifyapp.com/aidlc.pdf); repo ghi
  chú URL này không cố định) và bài blog ra mắt ngày 31/07/2025
  ([AWS](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)). Trích dẫn từ bài phương pháp trong mục
  này chưa được kiểm lại (xem phần đầu).
- **Ý chính:** "AI creates plans, seeks clarification, & implements plans, while humans make critical decisions" (AI lập
  kế hoạch, hỏi làm rõ và thực hiện, con người ra các quyết định quan trọng). Dòng này là alt text của một hình trên blog,
  không phải chú thích hay thân bài ([blog](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/)). Bài phương pháp đảo chiều cuộc hội
  thoại: AI khởi xướng và dẫn dắt, con người duyệt. Việc con người kiểm duyệt hoạt động như một "loss function", cắt lãng
  phí trước khi nó lan xuống các bước sau ([bài phương pháp](https://prod.d13rzhkk8cj2z0.amplifyapp.com/aidlc.pdf),
  nguyên tắc 2 và 9).
- **Phạm vi:** hệ thống đơn giản nằm ngoài phạm vi ([bài phương pháp](https://prod.d13rzhkk8cj2z0.amplifyapp.com/aidlc.pdf),
  nguyên tắc 5).
- **Artifact:** Intent → Unit (liên kết lỏng, giống epic hoặc subdomain trong DDD) → Bolt (vài giờ tới vài ngày, thay cho
  sprint) → Domain Design → Logical Design (AI viết ADR để developer kiểm) → Deployment Unit (cùng bài, mục III).
- **Các pha:** Inception qua "Mob Elaboration" (một phòng, một màn hình chung, một người điều phối; AI đề xuất story và
  Unit, nhóm sửa chỗ thiết kế thừa hoặc thiếu). Construction qua "Mob Construction". Operations, nơi AI chạy bản sửa theo
  runbook khi developer đã duyệt (cùng bài).
- **Các prompt trong bài đặt ra khuôn mẫu** mà sau này thành rule file: lập kế hoạch trong file md có checkbox, "Do not
  make critical decisions on your own" (không tự ra quyết định quan trọng), chờ duyệt, rồi đánh dấu từng bước (bài phương
  pháp, Phụ lục A).

### 3.2 Rule file v1 (tag v1.0.1, MIT-0)

Đọc trực tiếp từ file ở [v1.0.1](https://github.com/awslabs/aidlc-workflows/tree/v1.0.1).

| Chủ đề | Rule nói gì |
|---|---|
| Đóng gói | Một file `core-workflow.md` luôn được nạp (539 dòng) cộng khoảng 30 file chi tiết nạp khi cần. Với Claude Code, chép file core thành `CLAUDE.md` và các file chi tiết vào `.aidlc-rule-details/`. Cùng bộ file dùng cho Kiro steering, Amazon Q rules, Cursor, Copilot và `AGENTS.md` |
| Bắt đầu | Mở chat bằng "Using AI-DLC, ..." |
| Giai đoạn Inception | Workspace Detection (luôn chạy), Reverse Engineering (chỉ khi có code cũ), Requirements (luôn chạy, độ sâu thay đổi), User Stories, Workflow Planning (luôn chạy), Application Design, Units Generation |
| Giai đoạn Construction | Theo từng Unit: Functional Design, NFR Requirements, NFR Design, Infrastructure Design (đều có điều kiện), rồi Code Generation hai phần (lập kế hoạch, rồi sinh code). Build and Test chạy một lần ở cuối. Operations chỉ là chỗ giữ chỗ |
| Co giãn theo việc | Kế hoạch đánh dấu mỗi giai đoạn EXECUTE hoặc SKIP. Độ sâu là Minimal, Standard hoặc Comprehensive. Mỗi giai đoạn có điều kiện liệt kê "Execute IF" và "Skip IF", nên một bản sửa lỗi đơn giản bỏ qua story và thiết kế |
| Câu hỏi | "You must NEVER ask questions directly in the chat." (không bao giờ hỏi thẳng trong chat). Câu hỏi nằm trong file `*-questions.md` với lựa chọn A/B/C, một lựa chọn cuối bắt buộc "X) Other" và một dòng `[Answer]:`. Câu trả lời mơ hồ sinh ra file hỏi tiếp. Có hẳn một rule riêng vì model "was exhibiting overconfidence by not asking enough clarifying questions" (tự tin quá mức, hỏi làm rõ quá ít) |
| Cổng duyệt | Mỗi giai đoạn kết thúc bằng "Wait for Explicit Approval ... DO NOT PROCEED". Construction chỉ cho hai lựa chọn "Request Changes" hoặc "Continue"; "DO NOT create 3-option menus" |
| Hồ sơ | `audit.md` chỉ ghi thêm, có timestamp ISO và "COMPLETE RAW INPUT ... (never summarize)" của người dùng (nguyên văn, không tóm tắt). `aidlc-state.md` giữ checkbox các giai đoạn |
| Thư mục | `aidlc-docs/{inception,construction/<unit>,operations}`; code ứng dụng không bao giờ nằm trong `aidlc-docs` |
| Phần mở rộng | Cặp `X.opt-in.md` và `X.md` (bảo mật, kiểm thử theo thuộc tính, khả năng chịu lỗi). Rule có mã `PREFIX-NN` và mục Verification, mặc định chặn. Các rule bảo mật chỉ là "a directional reference" (tham khảo định hướng) |

Hướng dẫn thực địa `docs/WORKING-WITH-AIDLC.md` trong cùng tag thêm các bài học thực hành:

- Xoá context ở mỗi điểm quyết định, và từ chối nén context giữa chừng.
- Xin phản biện trong một context mới, vì AI "will defend its own prior decisions" (sẽ bảo vệ các quyết định trước của
  chính nó).
- "Never Vibe Code": sửa thiết kế trước, rồi sinh lại code.
- Cập nhật ngược thay đổi vào tài liệu thiết kế.
- Để báo cáo cho người đọc ra ngoài `aidlc-docs`, để chúng không làm bẩn context về sau.

### 3.3 Đặc tả và engine v2 (v2.11.4, 13/11/2026, MIT-0)

Trích dẫn từ PDF đặc tả v2 trong mục này chưa được kiểm lại (xem phần đầu). Trích dẫn từ file trong repo được đọc từ bản
clone.

- **Vì sao có v2:** "our prescriptive stage definitions proved too opinionated, and that is where adoption friction arose"
  (định nghĩa giai đoạn quá áp đặt, gây khó khi áp dụng)
  ([PDF đặc tả v2](https://github.com/awslabs/aidlc-workflows/blob/main/assets/AI-DLC-Workflows-2.0-Specification.pdf), P6).
  Mục tiêu là tiến dần tới tự động "as machine-checkable verification expands" (khi phần kiểm được bằng máy tăng lên)
  (cùng PDF, mục 1).
- **Các nguyên tắc nên biết** (cùng PDF, mục 2):
  - Mọi intent ban đầu đều mơ hồ.
  - Một vòng tự sửa cần hậu điều kiện "checkable by a program the AI cannot modify" (kiểm bởi một chương trình AI không sửa
    được), cộng một điều kiện dừng (giới hạn số vòng hoặc ngân sách token) rồi chuyển cho người.
  - Mỗi giai đoạn có ba ngăn: What (đầu vào và đầu ra), How we know it's right (hậu điều kiện), What we learned (điều đã
    học).
  - Chia nhỏ theo giai đoạn thay vì làm một lần.
  - Áp dụng tự động hoá theo từng bước an toàn.
  - Mỗi lần người sửa là một ứng viên rule, chỉ được nhận sau khi người duyệt.
- **Một giới hạn nói thẳng:** khi cùng một model vừa sinh vừa chấm, nó có thể "satisfy the letter of the check without
  satisfying its intent" (thoả câu chữ của phép kiểm mà không thoả ý định). Vì vậy một giai đoạn chỉ do LLM chấm "will not
  self-halt" (sẽ không tự dừng) (cùng PDF, mục 3). Những rule không bao giờ được vi phạm, như một endpoint không có xác
  thực, cần một linter tất định.
- **Bản đã phát hành** ([repo](https://github.com/awslabs/aidlc-workflows), README và `docs/guide/`):
  - Quy mô và profile: 5 pha (Initialization, Ideation, Inception, Construction, Operation), 33 giai đoạn, 14 agent và 11
    profile. Agent đề xuất profile, người xác nhận.
  - Cài đặt: một binary `aidlc`, rồi `aidlc config --harness claude`, rồi `/aidlc ...`.
  - Gắn vào Claude Code: khoảng 17 hook (record-human-turn, guard duyệt plan, write-audit-log, sensor, validate-state khi
    PreCompact).
  - Hồ sơ: trạng thái nằm ở `aidlc/spaces/<space>/intents/<YYMMDD>-<label>/`, với checkbox sáu trạng thái (`[?]` nghĩa là
    "đang chờ bạn duyệt").
  - Vòng học: sau một lần sửa, nó hỏi "Keep that for next time?" (giữ cho lần sau?) với các lựa chọn dự án, nhóm hoặc
    không.
  - Bằng chứng xong: muốn duyệt Construction cần một lệnh kiểm do người cho phép và một biên nhận do công cụ ghi. "a
    hand-written proof file cannot verify a Unit" (file bằng chứng viết tay không xác nhận được một Unit).
  - Lỗi luôn làm dừng Construction.
  - Mặc định cấp tổ chức là trunk-based, mỗi Bolt squash-merge vào `main`.
- **Vì sao văn xuôi thành hook:** phần đầu file guard duyệt plan nói thẳng: "A field report showed prose losing that
  contest: a conductor generated the code first and backfilled the plan" (một báo cáo thực địa cho thấy văn xuôi thua: agent
  sinh code trước rồi viết bù plan). Quy tắc của họ: "determinism belongs in tools and hooks" (tính tất định thuộc về công
  cụ và hook) ([repo](https://github.com/awslabs/aidlc-workflows), `core/hooks/aidlc-plan-approval-guard.ts`).
- **Nhận xét của chúng tôi (không phải của AWS):** ở commit d8dd27dc, repo có 2.357 file và một bộ phân loại kiểm toán 134
  sự kiện. CHANGELOG có các mục gần đây ghi "breaking for scripts". Nguyên tắc của v1 là người dùng không cần cài gì, nay
  đã nhường chỗ cho một binary.

### 3.4 Công cụ và giấy phép

- **Công cụ:** v1 hỗ trợ Claude Code, Kiro, Amazon Q, Cursor, Cline, Copilot và các công cụ đọc `AGENTS.md`. v2 hỗ trợ
  Claude Code, Kiro, Codex, Cursor, opencode và Copilot; Amazon Q không còn trong danh sách
  ([repo](https://github.com/awslabs/aidlc-workflows)).
- **Giấy phép:** rule, engine và đặc tả v2 là **MIT-0**, nên được sửa và dùng lại mà không cần ghi công. Bài phương pháp và
  các blog AWS không có giấy phép mở: trích dẫn và diễn đạt lại, không sao chép.
- **CHƯA KIỂM ĐƯỢC:** phiên re:Invent DVT214 và chương trình thực địa "AI-DLC Unicorn Gym". Không điều gì trong ghi chú này
  dựa vào chúng.

## 4. Phía Anthropic chi tiết

### 4.1 Những tài liệu đang có

| Tài liệu | Là gì | Giấy phép |
|---|---|---|
| "The AI-Native SDLC Playbook", Louis Claxton, Anthropic Applied AI ([web](https://claude.com/blog/the-ai-native-sdlc-playbook), [PDF](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)) | Hướng dẫn 54 trang. Trang web 21/08/2026; metadata PDF 23/09/2026. "inspired by working with our customers" (rút từ làm việc với khách hàng) (tr.3) | Không ghi; © 2026 Anthropic PBC |
| Cùng playbook dưới dạng khoá học ([Claude Academy](https://academy.claude.com/courses/ai-native-sdlc-playbook)) | 14 bài, khoảng 1 giờ, không có quiz hay huy hiệu | Điều khoản Anthropic |
| "How Anthropic secures its AI-native software development lifecycle", Jason Clinton (Deputy CISO), 21/07/2026 ([bài viết](https://claude.com/resources/articles/how-anthropic-secures-its-ai-native-software-development-lifecycle)) | Một bài liên quan của Anthropic về cách làm nội bộ của chính họ, đăng trước playbook một tháng. Bài không nhắc tới playbook; bài nói nó "is intended to be combined with the Zero Trust for Agents framework" (được dùng kèm khung Zero Trust for Agents). Ngược lại, playbook là hướng dẫn cho khách hàng | Không ghi |
| [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action), [anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review) | GitHub Action để review PR và sửa qua `@claude` | MIT |
| [anthropics/claude-code](https://github.com/anthropics/claude-code) | Bản CLI | Độc quyền |
| [anthropics/skills](https://github.com/anthropics/skills) | Repo skill công khai | Không thấy giấy phép cấp repo |

### 4.2 Playbook quy định gì

**Luận điểm.** "Code is no longer the bottleneck." (code không còn là điểm nghẽn). Các bước chậm giờ chạy theo tốc độ
người: lập kế hoạch, review và test, deploy. Quy trình thành một vòng lặp: "Each stage ends by writing one to version
control ... and the next stage begins by reading it" (mỗi giai đoạn kết thúc bằng việc ghi một artifact vào version
control, giai đoạn sau bắt đầu bằng việc đọc nó). Các trigger nối các giai đoạn: `intent.md` được chấp nhận mở pha thiết
kế, `spec.md` được duyệt mở plan mode, PR được merge chạy pipeline, và một dải kiểm soát bị vượt sẽ viết ra `intent.md`
tiếp theo ([PDF tr.3-8](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).

| Giai đoạn | Artifact | Ai quyết | Quy tắc chính (đều từ [PDF](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)) |
|---|---|---|---|
| 1 Plan | `intent.md` (Problem, Proposed outcome, Affected users and systems, Constraints, Open questions) trong thư mục `intent/` | Product owner, bằng cách merge hoặc đóng | Một "proto-spec in the originator's own terms" (bản spec sơ khởi bằng lời của người đề xuất). Người không dùng git commit qua connector GitHub |
| 2 Design | `spec.md`, do Claude viết theo skill của tổ chức về thương hiệu, bảo mật, tuân thủ và UX, có đánh dấu điểm đáng lo | Product owner; người phụ trách chính sách cho các điểm đáng lo; technical lead khi rủi ro cao | "The product owner reviews that spec, but doesn't write it." (product owner review spec chứ không viết). Spec, prompt sinh ra nó và phiên bản skill đều được lưu trong git |
| 3 Build | `plan.md` (Files that change, Order of work, Risks, Proof); code | Engineer; tech lead hoặc architect khi rủi ro cao | "Nothing is implemented without an accepted plan." (không làm gì khi chưa có plan được chấp nhận). "update plan.md in the same commit" (cập nhật plan.md trong cùng commit), tốt nhất có hook. CLAUDE.md "under a page" (dưới một trang); "When Claude makes a mistake twice" (khi Claude sai lần thứ hai), cách sửa được ghi vào đó. Bắt đầu với 2 hoặc 3 worktree song song; trần là "how many streams one person can review properly" (số luồng một người review cẩn thận được) |
| 4 Test | Kết quả test, log build, so sánh ảnh chụp; bộ eval | Code owner; tỷ lệ đạt eval là điều kiện merge | "Always give Claude a way to verify its own work" (luôn cho Claude cách tự kiểm việc của mình). Với sửa lỗi, commit một test đang fail trước, rồi sửa "without editing the test" (không sửa test), có hook chặn sửa file test. Bằng chứng là output nguyên văn của công cụ. Eval: 20 tới 50 việc thật, và mỗi sự cố thành một eval |
| 5 Deploy | Các lượt review trong `REVIEW.md` (lỗi, bảo mật, tuân thủ so với spec và plan), định nghĩa "Important", giới hạn số góp ý vặt; lịch sử PR | Code owner qua branch protection; release manager cho production | "Findings do not approve or block a PR on their own." (kết quả review tự nó không duyệt hay chặn PR). "the agent that wrote the code has no way to approve it." (agent viết code không có cách nào tự duyệt). Cổng duyệt là hook (ví dụ: `production-gate.sh` thoát mã 2 trừ khi có `RELEASE_APPROVAL`). CI: các bước `claude -p` chỉ đọc chạy trước, rồi bước ghi chỉ đi vào dưới dạng PR, chạy trong sandbox, không giữ sẵn credential production. Tự động hoá chia theo môi trường: dev deploy tự do, production chờ release manager. "Rollback should be the most rehearsed path" (rollback phải là đường được tập nhiều nhất) |
| 6 Maintain | Chẩn đoán được viết thành một `intent.md` mới; post-mortem ghi vào file bài học có version control | Chủ dịch vụ hoặc người trực; product owner cho việc liên quan sản phẩm | Phát hiện luôn tất định (`bands.yaml`: 1σ ghi log, 2σ Claude chẩn đoán chỉ đọc, 3σ Claude được mở PR hoặc chạy runbook đã duyệt trước). Chạy không người dùng "an independent confidence gate between stages" (một cổng tin cậy độc lập giữa các giai đoạn) |

**Kiểm soát.** "A skill is a control, though an advisory one" (skill là một kiểm soát, nhưng chỉ mang tính khuyến nghị):
không gì buộc phiên làm việc tuân theo nó, nên rule phải luôn đúng cần hook, managed settings, branch protection hoặc một
lượt review. "The skill makes violations rare and the hook makes them close to impossible." (skill làm vi phạm hiếm đi,
hook làm vi phạm gần như không thể). Hook đòi duyệt nên đặt ở Deploy, không ở Build, nếu không người lại nằm trên đường
găng. Mỗi artifact chỉ có một nguồn sự thật; tối thiểu là liên kết giữa mã bản ghi của hệ thống cũ và SHA của commit
([PDF, chương Build và khung bên tr.22](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).

**Áp dụng.** Đi theo đồ thị phụ thuộc và bắt đầu với các play không cần gì trước: ghi intent, CLAUDE.md, skill, vòng phản
hồi, và hook làm cổng. Làm mỗi bước bằng tay, rồi biến thành slash command, rồi thành job chạy khi artifact trước được
merge. Dựng cổng trước khi tự động hoá bất cứ thứ gì đi qua cổng. Mỗi play nêu một chỉ số dẫn và một chỉ số trễ (mốc thời
gian git và PR, CI, OpenTelemetry, DORA)
([PDF tr.9 và từng play](https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf)).

**Giới hạn tự nêu.** Skill và CLAUDE.md chỉ mang tính khuyến nghị. Ví dụ managed settings là "a starting point to tailor,
rather than a recommendation to copy" (điểm khởi đầu để chỉnh, không phải để chép). Eval mất giá trị khi model tốt lên.
Việc song song bị giới hạn bởi sức review. Nhiều sản phẩm được nêu đang ở dạng beta hoặc research preview (managed Code
Review, Claude Design, Claude Tag, Claude Security). Không có kết quả đo được nào được công bố (cùng PDF).

**Một bài liên quan: Anthropic bảo mật SDLC của chính họ thế nào.** Đây là Anthropic mô tả cách làm nội bộ, không thuộc
playbook. Hướng dẫn bảo mật nằm trong CLAUDE.md và skill của tổ chức. "New agents post comments for human approval until
trust is earned." (agent mới đăng góp ý để người duyệt tới khi có được lòng tin). Sau một lần nâng model, một agent xử lý
sự cố nhờ một phiên Claude khác push bản sửa, và yêu cầu đó "was caught at a human review gate as designed" (bị một cổng
review của người chặn lại, đúng như thiết kế). Bài học bài rút ra: đặt ranh giới quanh hành động và quyền truy cập, không
đặt vào chỉ dẫn cho model. Các con số là tự báo cáo: kỹ sư ship lượng code mỗi quý gấp 8 lần giai đoạn 2021 tới 2025,
Claude viết khoảng 80% code được merge, khoảng một phần ba số lỗi gây ra các sự cố claude.ai trước đây giờ sẽ bị bắt, và
tỷ lệ PR có góp ý review thực chất tăng từ 16% lên 54%
([bài viết](https://claude.com/resources/articles/how-anthropic-secures-its-ai-native-software-development-lifecycle)).

## 5. Góc nhìn của giới chuyên môn và các phê bình

**Cùng một khung ở mọi nơi.** Intent, rồi spec, thiết kế, plan hoặc task, build, kiểm, deploy và học. Mỗi bước để lại một
artifact markdown và một cổng của người. GitHub Spec Kit chạy constitution → specify → plan → tasks → implement →
converge, và coi "specifications as the source of truth" (spec là nguồn sự thật)
([repo, MIT](https://github.com/github/spec-kit)). Kiro dùng `requirements.md` (hoặc `bugfix.md`), `design.md` và
`tasks.md` ([docs](https://kiro.dev/docs/specs/)).

**Công cụ nào giờ cũng có đường nhẹ.** AI-DLC có Express và Bugfix ([repo](https://github.com/awslabs/aidlc-workflows)).
Kiro có "Quick Spec", sinh cả ba file "without approval gates" (không có cổng duyệt) ([docs](https://kiro.dev/docs/specs/)).
Luồng sửa lỗi và đánh giá ý tưởng của Spec Kit là "independent entry points, not mandatory phases" (điểm vào độc lập,
không phải pha bắt buộc) ([repo](https://github.com/github/spec-kit)).

**Các phê bình**

1. **Chi phí review và tài liệu quá nhiều.**
   - Birgitta Böckeler, nói về đống file dài dòng của **spec-kit**: "I'd rather review code than all these markdown
     files" (thà review code còn hơn đống file markdown này). Nói về **Kiro** với một lỗi nhỏ (bốn user story, 16 tiêu
     chí chấp nhận): "the workflow was like using a sledgehammer to crack a nut" (quy trình như dùng búa tạ đập hạt dẻ)
     ([martinfowler.com](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)). Bà không thử AI-DLC hay
     playbook của Anthropic. Áp các nhận xét này cho chúng là suy luận của chúng tôi.
   - Thoughtworks Radar: các quy trình "elaborate and opinionated" (rườm rà và áp đặt), file spec dài và khó review
     ([Radar, 11/2025](https://www.thoughtworks.com/radar/techniques/spec-driven-development)).
   - Thoughtworks Radar: một nhóm dùng Spec Kit gặp tình trạng chỉ dẫn phình to và context bị "mục", và sửa bằng cách
     chuyển hướng dẫn vào skill nạp khi cần
     ([Radar, 04/2026](https://www.thoughtworks.com/radar/languages-and-frameworks/github-spec-kit)).
2. **Kiểm soát giả.** "I frequently saw the agent ultimately not follow all the instructions" (tôi thường thấy agent rốt
   cuộc không làm theo mọi chỉ dẫn; một nhận xét chung, ví dụ minh hoạ là spec-kit)
   ([Böckeler](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)). AWS
   và Anthropic đồng ý bằng chính lời của họ (mục 3.3 và 4.2): câu trả lời là hook và phép kiểm tất định, không phải thêm
   văn xuôi.
3. **Lặp lại phát triển hướng mô hình (MDD).** Coi spec là nguồn có nguy cơ mang "the downsides of both MDD and LLMs"
   (nhược điểm của cả MDD lẫn LLM): cứng nhắc cộng với không tất định. Nó "Probably not for large features that are still
   very unclear" (có lẽ không hợp với tính năng lớn còn rất mơ hồ)
   ([Böckeler](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)).
4. **Chỉ nhìn vào bên trong.** Dave West (Scrum.org, tự nhận là người ủng hộ Scrum): "AI-DLC's events are internal" (các
   sự kiện của AI-DLC chỉ diễn ra trong nhóm), nên một nhóm có thể "ship the wrong thing, faster" (giao sai thứ, nhanh
   hơn), và retrospective bị bỏ
   ([Scrum.org, 04/08/2026](https://www.scrum.org/resources/blog/aws-ai-dlc-why-ai-coding-still-needs-human-accountability)).
   Will Mitchell: "I believe the bottleneck is further upstream" (tôi cho rằng điểm nghẽn nằm xa hơn về phía đầu nguồn),
   ở khâu khám phá ([blog](https://wakamoleguy.com/p/ai-dlc-solves-wrong-bottleneck)). Bài gọi rõ đây là phương pháp của
   AWS ("introduced by a solutions architect at AWS"), nhưng trang ghi ngày 11/02/2025, trước bài blog ra mắt 31/07/2025,
   nên ngày đăng không đáng tin và bài có thể viết về một bản trước của phương pháp.
5. **AI khuếch đại hệ thống sẵn có.** DORA 2025: "AI doesn't fix a team; it amplifies what's already there" (AI không sửa
   được một đội, nó khuếch đại những gì đã có). 90% dùng AI trong công việc, và 30% ít hoặc không tin code do AI viết. Về
   độ ổn định, bài viết có hai câu riêng: "AI adoption does continue to have a negative relationship with software
   delivery stability" (việc dùng AI vẫn có quan hệ nghịch với độ ổn định khi giao hàng), và "Without robust control
   systems, like strong automated testing, mature version control practices, and fast feedback loops, an increase in
   change volume leads to instability" (thiếu hệ thống kiểm soát vững như kiểm thử tự động mạnh, version control trưởng
   thành và vòng phản hồi nhanh, lượng thay đổi tăng sẽ dẫn tới mất ổn định). Bài không nói các kiểm soát đó xoá được quan
   hệ nghịch ([Google Cloud blog, 24/09/2025](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)).
   Mô hình năng lực AI của DORA liệt kê bảy năng lực, trong đó có làm theo lô nhỏ và version control mạnh
   ([Google Cloud blog](https://cloud.google.com/blog/products/ai-machine-learning/introducing-doras-inaugural-ai-capabilities-model)).
6. **Không có chỗ cho UX (nhắm vào playbook của Anthropic).** Tanner Kohler, "The Role of UX in Agentic Software
   Factories" (NN/g, 30/10/2026): "UX does not own a stage or approval gate in Anthropic's playbook" (UX không giữ giai
   đoạn hay cổng duyệt nào trong playbook của Anthropic), và "it does not define space for UX professionals to get directly
   involved" (playbook không chừa chỗ cho người làm UX tham gia trực tiếp). Bài còn nói playbook "makes no mention of user
   research whatsoever" (không hề nhắc tới nghiên cứu người dùng). Bài bàn về tài liệu của Anthropic, Google và OpenAI,
   không nhắc tới AI-DLC ([NN/g](https://www.nngroup.com/articles/ux-agentic-software-factories/)).

Ý nghĩa với chúng ta: phần có ích là **các kiểm soát** (cổng, hook, review độc lập, biên nhận, co giãn theo việc). Phần
rủi ro là **khối lượng tài liệu** và **các engine nặng**. Handbook của AA đã nói giống DORA: "AI amplifies the process you
already have" ([`docs/engineering-handbook.md`](../../engineering-handbook.md) §2.1).

## 6. Đối chiếu: giai đoạn vòng đời theo từng cách làm

Đường dẫn ở cột "AA hôm nay" tính từ repo gốc. "Áp dụng?" trỏ tới danh sách xếp hạng ở mục 7.

| Giai đoạn | AI-DLC | Playbook Anthropic | AA hôm nay | Khoảng trống | Áp dụng? |
|---|---|---|---|---|---|
| Intent | Intent; pha Ideation của v2; file câu hỏi | `intent.md` trong `intent/`, product owner merge | Issue Linear do agent soạn, tech lead xác nhận (`skill/aa-linear-issue/SKILL.md`, handbook §3 giai đoạn 1); yêu cầu kinh doanh đến từ Jira | Intent nằm ở Linear, không ở git; issue đã đóng được xuất ra `docs/linear-export/` (`tools/linear/linear_export.py`) | **Không.** Linear là nguồn sự thật duy nhất cho một issue (handbook §2.2), điều mà khung bên của playbook chấp nhận. Một bản thứ hai trong git sẽ lệch |
| Yêu cầu và spec | `requirements.md`, story, NFR, độ sâu thay đổi | `spec.md` do Claude viết theo skill tổ chức | Các mục DoR trong issue (`docs/templates/definition-of-ready.md`); lớp rủi ro; ADR khi lựa chọn khó đảo ngược | Chưa có "đường" (path) có tên quyết định một thay đổi cần giai đoạn và artifact nào | **Có**, đề xuất 1 (trường path) |
| Thiết kế | Domain và logical design; AI viết ADR | Một phần của spec; technical lead khi rủi ro cao | Quy tắc đặt ADR (`skill/ai-nghiep/references/adr.md`), `CONTEXT.md` mỗi repo, contract (`docs/contracts/`) | Không thấy | Không đổi |
| Plan | Plan sinh code có checkbox; hook duyệt plan ở v2 | `plan.md` (file, thứ tự, rủi ro, bằng chứng), giữ khớp trong cùng commit | Implementation note mỗi issue: Decisions, Changed, Tradeoffs, Should know (`docs/implementation-notes/`); mục tiêu lane trong `tools/workflows/lane.js` | Chưa có phần "file, thứ tự, bằng chứng" viết trước khi code, và chưa có phép kiểm diff có khớp với nó không | **Có**, đề xuất 2 (mục Plan cộng phép kiểm khớp plan cứng trước khi push) |
| Build | Theo Unit, theo Bolt; walking skeleton | 2-3 worktree; subagent; CLAUDE.md dưới một trang; skill khuyến nghị, hook tất định | Lane trong worktree (`tools/workflows/lane.js`); hook `subagent-guardrails.sh`, `aa_shell_guard.py` (10 rule), `kit-core-edit-guard.sh`, `lane_start_guard.py` (có kiểm RAM), `pilot_pii_guard.py` | Phần chỉ dẫn luôn được nạp khoảng 53 KB: trong repo, `.claude/CLAUDE.md` gốc 10,3 KB cộng ba file steering 17,0 KB; ngoài repo, CLAUDE.md toàn cục 8,6 KB và file chỉ mục auto-memory `MEMORY.md` 17,2 KB (file lớn nhất). Đếm dòng không chuẩn vì nhiều dòng rất dài | **Có**, đề xuất 5 (ngân sách chỉ dẫn) |
| Test | Giai đoạn Build and Test; độ sâu Minimal = một test mỗi yêu cầu; rule mở rộng có mục Verification | Vòng phản hồi; test fail trước cộng hook; eval trong CI | CI mỗi repo, `scripts/pre-push.sh`, lane chạy các phép kiểm của CI trước khi trả; eval golden set cho LLM chạy tay (handbook §5.7); test hook trong CI gốc (`.claude/hooks/test_*.py`) | Chưa có quy tắc test fail trước cho sửa lỗi; chưa có eval hành vi agent sau khi đổi skill hay hook | **Có** (test fail trước, đề xuất 3). Eval agent: **để sau**, đề xuất 8 |
| Review | Agent reviewer, READY hoặc NOT-READY, tối đa 2 vòng, không bao giờ chặn; phản biện trong context mới | `REVIEW.md`, giới hạn góp ý vặt; kết quả review không tự duyệt; code owner duyệt | Reviewer độc lập theo góc nhìn cộng một lượt sửa (`tools/workflows/lane.js`); `kiro-reviewer` cho lớp rủi ro (`.claude/agents/kiro-reviewer.md`); CODEOWNERS ở mọi repo, chưa ép trong giai đoạn dev (handbook §6.5) | Không có trong giai đoạn dev; quy tắc mức độ đã nằm trong `lane.js` | Không đổi |
| Kiểm (Done) | Lệnh kiểm do người cho phép cộng biên nhận do công cụ ghi | Bằng chứng là output nguyên văn của công cụ | Comment "Verified live" do agent gõ theo mẫu (`skill/aa-ship/SKILL.md` §4) | Bằng chứng được gõ lại, không do công cụ sinh ra | **Có**, đề xuất 4 (biên nhận do CI ghi, không do agent) |
| Cổng deploy | Lỗi luôn dừng; trunk cộng squash merge | Agent làm tới cổng production, không vượt qua; một hook; release manager; tự động hoá theo môi trường | Giai đoạn dev tự merge sau CI, merge queue, `tools/github/ship_merge.py`, rule shell SHIP-1; quyền merge đổi khi có prod đầu tiên (handbook §6.5) | Chưa có prod, nên chưa có hook cổng production | **Để sau**, đề xuất 9 (viết khi chạm điều kiện prod) |
| Vận hành | Pha Operation của v2: runbook, SLO, sự cố | Dải tất định; chẩn đoán thành `intent.md` kế tiếp; phân loại | Alarm tới runbook (handbook §7.2), quy trình sự cố (§7.3), Sentry | Chưa có tự động "vượt ngưỡng → issue nháp" | **Để sau**, đề xuất 10 (cần traffic thật) |
| Học | "Keep that for next time?" (dự án, nhóm hoặc không), có người duyệt | Sai "lần thứ hai" thì ghi vào CLAUDE.md; sự cố thành eval; file bài học | Dòng bài học phải nêu guard (`skill/aa-lessons/SKILL.md`, `tools/docs/check_lessons.py`); `guards.md`; rule shell thay văn xuôi | Chưa hỏi phạm vi khi tech lead sửa agent | **Có**, đề xuất 6 (trường phạm vi, do `check_lessons.py` kiểm) |
| Câu hỏi và quyết định | File câu hỏi: A/B/C, "Other" bắt buộc, `[Answer]:`; trả lời mơ hồ thì hỏi lại | Không đề cập | Trang quyết định: duyệt bằng cách bấm chọn, lưu vào database (quy tắc trong `skill/aa-session/SKILL.md`; danh sách trang trong `docs/artifacts/registry.json`) | Quy tắc định dạng chưa được viết ra | **Có**, đề xuất 7 (quy tắc định dạng; chỉ khuyến nghị cho tới khi có template và lint) |
| Dấu vết kiểm toán | `audit.md`, chỉ ghi thêm, nguyên văn lời người dùng | Chuỗi commit | Git, PR, comment Linear, bản ghi trang quyết định, log phiên (`docs/sessions/`) | Không giữ nguyên văn chat, do chủ ý | **Không.** Commit và bản ghi quyết định là đủ; log chat nguyên văn tăng rủi ro dữ liệu riêng tư |
| Co giãn theo việc | EXECUTE hoặc SKIP mỗi giai đoạn; độ sâu; 11 profile | Play mô-đun; auto mode cho việc thường lệ | Lớp rủi ro trong DoR; 3-5 issue mỗi phiên (`skill/aa-session/SKILL.md`) | Chưa có path có tên | Đã gồm trong đề xuất 1 |
| Vệ sinh context | Xoá context ở cổng; từ chối nén; báo cáo để ngoài thư mục của agent | CLAUDE.md dưới một trang | Lane bắt đầu với context mới; checklist phiên và file bàn giao | Phiên chính dài bị nén | Không thêm quy tắc; đề xuất 5 có ích |

## 7. Đề xuất cho AA

Các đề xuất theo luật của AA: không thêm dịch vụ trả tiền, guard hơn quy tắc trên wiki, artifact nằm trong git, tiếng Anh
đơn giản. Công sức tính bằng phiên như thiết kế kit đang đếm
([`docs/research/new-project-playbook/README.md`](../../research/new-project-playbook/README.md) §6). Mọi mục đều
**0 USD**: không dịch vụ mới, không gọi model trong CI.

| # | Làm gì | Ở đâu | Công sức | Rủi ro tài liệu quá nhiều |
|---|---|---|---|---|
| 1 | **Trường "path" trong Definition of Ready**: `fix`, `small`, `feature` hoặc `risky`. Path quyết định thay đổi cần những gì (xem bảng dưới). Đây là EXECUTE/SKIP và profile của AI-DLC, và Quick Spec của Kiro, gói trong bốn từ | AA-1102 R2a (template DoR vốn sẽ thêm trường appetite); `skill/aa-linear-issue/SKILL.md`; `lane.js` nhận `path` làm tham số và chọn góc nhìn review theo nó | 0,25 | **Thấp.** Nó bớt việc cho thay đổi nhỏ |
| 2 | **Một mục Plan ngắn ở đầu implementation note**, có phép kiểm cứng: file thay đổi, thứ tự, rủi ro, bằng chứng, tối đa khoảng 10 dòng. Lane viết nó trong commit đầu và cập nhật trong cùng commit khi code đi lệch ("update plan.md in the same commit" của playbook). **Guard:** bước kiểm trước khi push của điều phối trong `tools/github/ship_open_prs.py`, vốn đã kiểm mọi PR trước khi push bất cứ gì, báo lỗi khi diff đụng vào file mà Plan không nêu, trừ khi commit thêm file đó cũng cập nhật Plan. Đưa cùng danh sách đó cho reviewer góc spec chỉ là gợi ý, vì một phép kiểm do LLM chấm "will not self-halt" (đặc tả v2) | `tools/github/ship_open_prs.py`; `tools/workflows/lane.js`; template implementation note (AA-1102 R2a); skill `project-ship` của kit AA (AA-1103 R4) | 0,5 | **Trung bình.** Giữ trong note sẵn có, không bao giờ tạo `plan.md` mới, và giới hạn khoảng 10 dòng |
| 3 | **Test fail trước cho path `fix`.** Hai commit: test (phải fail trên base), rồi bản sửa. Một phép kiểm git trong `lane.js` từ chối commit sửa nào đụng vào test của commit đầu. Đây là quy tắc "without editing the test" của playbook, ở dạng phép kiểm thay vì một câu văn | `tools/workflows/lane.js`; tài liệu template Copier (AA-1103 R3) | 0,5 | Không |
| 4 | **Biên nhận "Verified live" do CI ghi, không do agent.** Một job sau deploy trong workflow deploy của mỗi app chạy các phép kiểm `live_steps` của lane (trạng thái rollout và SHA image đang chạy, `git_sha` trên `/health`, mã HTTP và shape của từng endpoint đã đổi, tức là bước 1, 2 và 4 của `aa-ship` §3) và đăng biên nhận (lệnh, kết quả, thời điểm, link run) thành comment trên PR dưới danh tính của chính workflow. Một script agent chạy trên máy sẽ in ra khối mà agent vẫn sửa hoặc gõ lại được, nên không phải guard. `aa-ship` §4 khi đó trỏ tới comment này thay cho bằng chứng gõ lại. Bước 5 (ảnh UI), 7 (DB Isolation Probe) và 8 (eval LLM) vẫn làm tay hoặc trỏ tới run workflow riêng của chúng. Dùng App `aa-ci-bot` để comment sẽ nới phạm vi ADR 0011a cho phép, nên cần một bản sửa đổi; token của workflow thì không cần. Theo ý AI-DLC: "a hand-written proof file cannot verify a Unit", nhưng chỉ cho một phần của §3 | Workflow deploy của các app (CIS, Booking, Partner); `skill/aa-ship/SKILL.md` §3 và §4; `project-ship` (AA-1103 R4) | 1,5 | **Thấp.** Thay việc gõ bằng output |
| 5 | **Ngân sách chỉ dẫn, đo bằng byte.** Phần luôn được nạp hôm nay khoảng 53 KB (dòng Build ở mục 6). "Under a page" của playbook nói về một CLAUDE.md của dự án, nên chỉ là hướng đi, không phải chỉ tiêu cho cả bộ. Chuyển các quy trình vào skill nạp khi cần; giữ luật cứng cộng con trỏ. **Guard, hai phần:** một phép kiểm docs lint trong CI gốc báo đỏ khi các file trong repo (`.claude/CLAUDE.md` gốc cộng ba file steering) vượt ngân sách byte lưu trong cấu hình lint. CI gốc không thấy CLAUDE.md toàn cục hay `MEMORY.md`, nên một hook SessionStart trên máy cảnh báo khi chúng vượt ngân sách riêng. Tech lead tự sửa CLAUDE.md toàn cục bằng tay (handbook §2.3); agent đề xuất chỗ cắt | AA-1102 R1 (dọn dẹp, vốn đã 1 phiên); lint trong `tools/docs/` và `docs-lint.yml`; một hook SessionStart trong `.claude/hooks/` | 0,25 thêm vào R1 | **Âm.** Nó cắt bớt chữ. Rủi ro: bỏ mất một quy tắc quan trọng, nên mỗi dòng bị bỏ phải chuyển sang skill, hook hoặc `guards.md`, không xoá trắng |
| 6 | **Trường phạm vi trong vòng học.** Khi tech lead sửa agent, agent đề xuất dòng bài học (kèm Guard) và hỏi một điều: "chỉ AA, kit của AA, hay không?". "Kit của AA" là các skill của bộ kit dự án mới của AA (AA-1103), không có gì ngoài AA. **Guard:** `tools/docs/check_lessons.py` vốn đã đòi trường `Guard:` đúng dạng trên mỗi dòng bài học mới; nay đòi thêm `Scope: aa` hoặc `Scope: aa-kit`. Phép kiểm chứng minh trường có mặt, không chứng minh câu trả lời đúng | `skill/aa-lessons/SKILL.md` §2 và §3; `tools/docs/check_lessons.py`; AA-1103 R4 | 0,1 | **Thấp.** Quy tắc Guard đã chặn việc dòng văn xuôi chồng chất |
| 7 | **Quy tắc định dạng cho trang quyết định**, lấy từ file câu hỏi của AI-DLC: 2 tới 5 lựa chọn thật, không thêm lựa chọn độn, lựa chọn cuối là "Other", đánh dấu câu trả lời đề xuất, ghi ai thường trả lời (tech lead hay business owner), và hỏi lại khi câu trả lời mơ hồ. Ở dạng quy tắc trong skill, nó chỉ **mang tính khuyến nghị**. Nó chỉ thành guard khi có một template trang quyết định dùng chung, với dữ liệu câu hỏi được một lint kiểm (có lựa chọn "Other", đúng một câu trả lời đề xuất được đánh dấu) | `skill/aa-session/SKILL.md` (quy tắc "câu hỏi cho tech lead", vốn đã đòi một trang quyết định bấm chọn); template trang quyết định và lint của nó (AA-1102 R2a) | 0,1 cho quy tắc; 0,5 khi có template và lint | **Thấp** |
| 8 | **Để sau: eval hành vi agent.** 10 tới 20 việc chạy lại bằng tay trong phiên khi một skill hay hook thay đổi, chấm bằng phép kiểm tất định khi được. AA đã chạy lại shell guard trên các lệnh cũ (`.claude/hooks/replay_shell_guard.py`). Một bộ `claude -p` trong CI sẽ cần API key, tức là chi tiêu mới, nên chưa làm | Sau pilot của kit (AA-1103 R5) | 1 | Trung bình. Giữ bộ nhỏ và bỏ các ca không còn phân biệt được (playbook cảnh báo eval mất giá trị dần) |
| 9 | **Để sau: hook cổng production** từ chối lệnh deploy production khi không có phê duyệt release, cộng các công cụ deploy, status và rollback giới hạn theo môi trường. Viết khi chạm điều kiện prod, cùng lúc bật ép code owner | Công tắc prod ở handbook §6.5; nguyên tắc kit "công tắc theo pha" (AA-1102) | 0,5 | Thấp |
| 10 | **Để sau: vòng Maintain**: dải tất định trên các alarm sẵn có; khi vượt ngưỡng thì viết một issue Linear nháp theo dạng DoR. Chỉ làm khi có traffic thật (Dev chưa có) | Handbook §7.2; runbook vận hành | 1 | Thấp |
| 11 | **Dạy trong Academy**: một trang giải thích, "Vòng đời agent của chúng ta so với AI-DLC và playbook của Anthropic", dựng từ mục 2 tới 6 của ghi chú này. Nó lấp một phần gap G11 (chưa có trang giải thích điều phối agent) và cấp nội dung cho mô-đun L3. Trang trỏ tới khoá học miễn phí của Anthropic và trích rule MIT-0 khi cần | AA-1104 (các trang lấp gap); AA-1105 (mô-đun L3 và quiz) | 0,5 | **Trung bình.** Một trang, trỏ link thay vì chép. Phép kiểm lệch của Academy (`docs/research/lms/README.md` §6.4) báo khi nguồn thay đổi |

**Mỗi path đòi gì** (đề xuất 1):

| Path | Khi nào | Cần |
|---|---|---|
| `fix` | Lỗi có phạm vi rõ, khoanh được | Test fail trước (đề xuất 3), một góc nhìn review, không ADR, Plan ngắn |
| `small` | Thay đổi nhỏ, không tạo ranh giới mới | Plan ngắn, một hoặc hai góc nhìn, không ADR |
| `feature` | Hành vi mới hoặc contract mới | DoR đầy đủ, Plan, hai góc nhìn, ADR nếu lựa chọn khó đảo ngược |
| `risky` | Auth, migration, IAM hoặc secret, xoá dữ liệu (các lớp rủi ro trong DoR) | Như `feature`, cộng `kiro-reviewer`, cộng DRY RUN khi xoá |

**Không áp dụng**

- **Engine AI-DLC v2** (binary, khoảng 17 hook, 2.357 file, thay đổi phá vỡ tương thích). Hook riêng của AA và `lane.js`
  đã phủ cùng phần việc, và hợp với repo của chúng ta.
- **Nghi thức Mob Elaboration và Mob Construction.** AA là một tech lead cộng các agent; không có phòng đông người để chạy.
- **File `intent.md`/`spec.md`/`plan.md` cho mọi thay đổi.** Linear cộng DoR, ADR và `CONTEXT.md` đã giữ intent và thiết
  kế. Plan nằm trong implementation note (đề xuất 2). Thêm file sẽ mang tới gánh nặng review mà Böckeler (về spec-kit và
  Kiro) và Thoughtworks cảnh báo.
- **`audit.md` ghi nguyên văn.** Commit và bản ghi trang quyết định là đủ, còn log chat nguyên văn chứa dữ liệu riêng tư.
- **Managed Code Review, Claude Tag và Claude Design.** Chúng đang ở dạng beta hoặc research preview, có thể phát sinh chi
  phí mới, và AA không dùng Slack. Managed settings cho doanh nghiệp không hợp với cách làm một developer hiện nay.

**Cách các mục được áp dụng đi vào kit và Academy của AA.** Cả hai là của chính AA (AA-1098, AA-1099); đoạn này không
nói về sản phẩm nào ngoài AA. Thiết kế kit vốn đã "handbook-first": một quy tắc đổi trong handbook
hoặc skill trước, rồi mới tới kit và các bản sao ([kit §5.1](../../research/new-project-playbook/README.md),
nguyên tắc 3). Academy dựng từ cùng các trang và báo lệch khi một mục nguồn thay đổi
([Academy §6.4](../../research/lms/README.md)). Vì vậy mỗi mục ở trên chỉ được làm một lần, trong handbook, skill
hoặc công cụ của AA, qua PR bình thường. Kit (AA-1102, AA-1103) và Academy (AA-1104, AA-1105) sau đó nhận nó qua các đường
sẵn có. Đề xuất 6 thêm mắt xích duy nhất còn thiếu: bài học dành cho kit của AA được gắn nhãn ngay lúc viết, để các skill
của kit không cần một đợt rà lại về sau.

## 8. Nguồn

| Tiêu đề | URL | Đơn vị phát hành | Ngày | Giấy phép | Dùng để |
|---|---|---|---|---|---|
| AI-DLC Method Definition paper | https://prod.d13rzhkk8cj2z0.amplifyapp.com/aidlc.pdf | AWS (Raja SP) | Không ghi ngày (được dẫn từ 07/2025); URL không cố định | Không ghi (bản quyền AWS) | Nguyên tắc, artifact, nghi thức, prompt Phụ lục A (trích dẫn chưa kiểm lại) |
| AI-Driven Development Life Cycle: Reimagining Software Engineering | https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/ | AWS DevOps blog | 31/07/2025 | Điều khoản trang AWS | Ý chính (alt text của hình), các pha, Bolt |
| Open-Sourcing Adaptive Workflows for AI-DLC | https://aws.amazon.com/blogs/devops/open-sourcing-adaptive-workflows-for-ai-driven-development-life-cycle-ai-dlc/ | AWS DevOps blog | 29/11/2025 | Điều khoản trang AWS | Quy trình thích ứng, cổng ở mọi quyết định |
| Building with AI-DLC using Amazon Q Developer | https://aws.amazon.com/blogs/devops/building-with-ai-dlc-using-amazon-q-developer/ | AWS DevOps blog | 29/11/2025 | Điều khoản trang AWS | Kết quả khác nhau giữa các lần chạy (chỉ đọc tới bước 6) |
| AI-driven development lifecycle using Amazon Bedrock AgentCore | https://aws.amazon.com/blogs/machine-learning/ai-driven-development-lifecycle-using-amazon-bedrock-agentcore/ | AWS ML blog | 03/09/2026 | Điều khoản trang AWS | Chỉ bối cảnh Construction |
| awslabs/aidlc-workflows, tag v1.0.1 | https://github.com/awslabs/aidlc-workflows/tree/v1.0.1 | AWS Labs | 30/06/2026 | MIT-0 | Rule v1: giai đoạn, độ sâu, file câu hỏi, cổng, audit, phần mở rộng, hướng dẫn thực địa |
| awslabs/aidlc-workflows, main tại d8dd27dc (v2.11.4) | https://github.com/awslabs/aidlc-workflows | AWS Labs | 13/11/2026 | MIT-0 | Engine v2: pha, profile, hook, biên nhận, vòng học, guard duyệt plan |
| AI-DLC Workflows 2.0 Specification | https://github.com/awslabs/aidlc-workflows/blob/main/assets/AI-DLC-Workflows-2.0-Specification.pdf | AWS Labs | Không ghi ngày (sửa 12/11/2026) | MIT-0 | Nguyên tắc v2, giới hạn của việc kiểm (trích dẫn chưa kiểm lại) |
| Trang tài liệu AI-DLC | https://awslabs.github.io/aidlc-workflows/ | AWS Labs | Đang chạy | MIT-0 | Đối chiếu hướng dẫn |
| The AI-Native SDLC Playbook (web) | https://claude.com/blog/the-ai-native-sdlc-playbook | Anthropic (Louis Claxton) | 21/08/2026 | Không ghi; © Anthropic | Luận điểm, giai đoạn, vai trò |
| The AI-Native SDLC Playbook (PDF, 54 trang) | https://assets.claude.com/5f640b0ae71b855ddd9989d43952da707f62866f.pdf | Anthropic | Metadata PDF 23/09/2026 | Không ghi; © Anthropic | Mọi quy tắc và trích dẫn theo giai đoạn (đối chiếu với bản trích văn bản; số trang khớp chân trang in) |
| Khoá học AI-Native SDLC Playbook | https://academy.claude.com/courses/ai-native-sdlc-playbook | Anthropic | 2026 | Điều khoản Anthropic | Định dạng khoá học (link cho Academy) |
| How Anthropic secures its AI-native SDLC | https://claude.com/resources/articles/how-anthropic-secures-its-ai-native-software-development-lifecycle | Anthropic (Jason Clinton, Deputy CISO) | 21/07/2026 | Không ghi | Bài liên quan về cách làm nội bộ của Anthropic: reviewer thử việc, ranh giới hành động, số liệu tự báo cáo (câu chữ kiểm lại 14/11/2026) |
| anthropics/claude-code-action | https://github.com/anthropics/claude-code-action | Anthropic | Đang chạy | MIT | Kiểm giấy phép |
| anthropics/claude-code-security-review | https://github.com/anthropics/claude-code-security-review | Anthropic | Đang chạy | MIT | Kiểm giấy phép |
| anthropics/claude-code | https://github.com/anthropics/claude-code | Anthropic | Đang chạy | Độc quyền | Kiểm giấy phép |
| anthropics/skills | https://github.com/anthropics/skills | Anthropic | Đang chạy | Không thấy giấy phép cấp repo | Kiểm giấy phép |
| What is the AI-Native SDLC? | https://www.endorlabs.com/learn/what-is-the-ai-native-sdlc | Endor Labs (thứ cấp) | 22/10/2026 | Điều khoản trang | Cách ghép hai thuật ngữ |
| github/spec-kit | https://github.com/github/spec-kit | GitHub | v1.4.0, 10/11/2026 | MIT | So sánh, đường nhẹ |
| Kiro specs | https://kiro.dev/docs/specs/ | Kiro | Cập nhật 12/11/2026 | Tài liệu độc quyền | Quick Spec, spec sửa lỗi |
| Spec-driven development (Radar) | https://www.thoughtworks.com/radar/techniques/spec-driven-development | Thoughtworks | 05/11/2025 | © Thoughtworks | Phê bình: áp đặt, spec dài |
| GitHub Spec Kit (Radar) | https://www.thoughtworks.com/radar/languages-and-frameworks/github-spec-kit | Thoughtworks | 15/04/2026 | © Thoughtworks | Phê bình: context mục, skill nạp khi cần |
| Understanding Spec-Driven Development: Kiro, spec-kit, and Tessl | https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html | martinfowler.com (Birgitta Böckeler) | 15/10/2025 | © Martin Fowler | Ba mức; phê bình chi phí review và kiểm soát |
| Announcing the 2025 DORA report | https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report | Google Cloud | 24/09/2025 | Điều khoản blog (nội dung dora.dev CC BY 4.0) | Phát hiện khuếch đại, lòng tin, độ ổn định |
| DORA AI Capabilities Model | https://cloud.google.com/blog/products/ai-machine-learning/introducing-doras-inaugural-ai-capabilities-model | Google Cloud | 24/09/2025 | Điều khoản blog (dora.dev CC BY 4.0) | Bảy năng lực |
| AWS AI-DLC: why AI coding still needs human accountability | https://www.scrum.org/resources/blog/aws-ai-dlc-why-ai-coding-still-needs-human-accountability | Scrum.org (Dave West) | 04/08/2026 | Điều khoản trang | Phê bình: chỉ nhìn vào bên trong |
| AI-DLC Solves the Wrong Bottleneck | https://wakamoleguy.com/p/ai-dlc-solves-wrong-bottleneck | Will Mitchell | Trang ghi 11/02/2025, trước bài ra mắt 07/2025, nên không đáng tin | Điều khoản trang | Phê bình: khâu khám phá ở đầu nguồn |
| The Role of UX in Agentic Software Factories | https://www.nngroup.com/articles/ux-agentic-software-factories/ | NN/g (Tanner Kohler) | 30/10/2026 | Điều khoản trang | Phê bình playbook của Anthropic: không có giai đoạn hay cổng cho UX |
| Infographic "Agent-Ready SDLC" | Không tìm thấy | Rakesh Gohel | CHƯA KIỂM ĐƯỢC | CHƯA KIỂM ĐƯỢC | Chỉ là điểm khởi đầu |

## 9. Ghi chú review

Một lượt review phản biện (14/11/2026) nêu 10 phát hiện. Mỗi phát hiện được kiểm lại trước khi áp dụng.

| # | Phát hiện | Kết luận | Đã đổi gì hoặc vì sao không đổi |
|---|---|---|---|
| 1 | Ghi chú dồn mọi thứ vào AA-1102…1105 | Chấp nhận, chỉ phần phạm vi | Phần đầu, mục 7 và đề xuất 6 nay ghi rõ "kit" và "Academy" là của chính AA (AA-1098, AA-1099). Sản phẩm ngoài AA nằm ngoài phạm vi ghi chú này và không được mô tả ở đây |
| 2 | Câu DORA "trừ khi" nói quá | Chấp nhận | Mục 5 ý 5 trích cả hai câu và bỏ "trừ khi" |
| 3 | Bài của Clinton không phải "bài đi kèm" | Chấp nhận | Mục 4.1 và 4.2 gọi đó là bài liên quan về cách làm của chính Anthropic; trích dẫn và cả bốn con số được kiểm lại trên trang |
| 4 | Trích dẫn Böckeler gán sai công cụ | Chấp nhận | Mục 5 ý 1 nêu rõ spec-kit và Kiro, và ghi việc áp sang AI-DLC và playbook là suy luận của chúng tôi |
| 5 | NN/g bị ghi CHƯA KIỂM ĐƯỢC | Chấp nhận | Thêm tác giả, ngày và trích dẫn; phê bình được giới hạn vào playbook của Anthropic |
| 6 | Bài của Mitchell có thể không nói về AWS AI-DLC | Bác một phần | Bài gọi rõ là phương pháp của AWS ("introduced by a solutions architect at AWS"), nên giữ lại. Ngày hiển thị (11/02/2025) sớm hơn bài blog ra mắt, và mục 5 nay ghi rõ điều đó |
| 7 | Nguồn gốc trích dẫn mâu thuẫn | Chấp nhận, đã giải quyết một phần | Phần đầu ghi rõ cách đọc từng nguồn. Số trang của playbook đã được kiểm lại: bản trích văn bản làm trong phiên này đặt mỗi trích dẫn đúng trang có số in ở chân trang là tr.3, tr.7, tr.9 hoặc tr.22. Trích dẫn từ bài phương pháp và đặc tả v2 được ghi là chưa kiểm lại. Dòng ý chính của AWS được ghi là alt text của hình (đã xác nhận trong HTML của trang) |
| 8 | Đo ngân sách chỉ dẫn sai | Chấp nhận | Mục 6 và đề xuất 5 đo bằng byte và tính cả `MEMORY.md` (17.239 byte; cả bộ 53.114 byte); lint CI chỉ phủ file trong repo, một hook SessionStart phủ phần còn lại |
| 9 | Không phải cả bảy ý đều là guard | Chấp nhận | Đề xuất 2 có phép kiểm cứng trước khi push, đề xuất 6 có trường trong `check_lessons.py`, đề xuất 7 ghi là khuyến nghị cho tới khi có template và lint; mục 1 đã cập nhật |
| 10 | Script biên nhận chạy trên máy giả mạo được | Chấp nhận, có điều chỉnh | Đề xuất 4 chuyển biên nhận vào workflow deploy và giới hạn ở bước 1, 2 và 4 của `aa-ship` §3. Token của workflow là đủ; dùng `aa-ci-bot` sẽ cần sửa đổi ADR 0011a. Nội dung phát hiện bị cắt sau "Reuse lane `li…"; được hiểu là "dùng lại `live_steps` của lane" |
