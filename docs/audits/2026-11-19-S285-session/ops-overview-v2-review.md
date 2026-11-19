## Kết quả critic pass: ops-overview-mockup.html

File: /home/nghiep/projects/AA-Ecosys/docs/audits/2026-11-19-S285-session/ops-overview-mockup.html (sửa trực tiếp, diff +20/−8 dòng). Bản gốc trước khi sửa: /tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/0cb0d264-8ea0-40d3-a9d8-5d17034f0ae0/scratchpad/crit/orig.html. Mình kiểm logic bằng Playwright (Chromium) ở 1440 px light và 390 px dark, script: /tmp/claude-1000/-home-nghiep-projects-AA-Ecosys/0cb0d264-8ea0-40d3-a9d8-5d17034f0ae0/scratchpad/crit/t.js.

### Checklist (done / fixed / missing)

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| (2) Time range 1h/6h/24h/7d/custom dựng lại mọi chart và list | done | Khi đổi 24h → 1h, các phần sau dựng lại: 4 golden chart, spend, lanes, app tiles, resource tiles, queue bars, events, resolved, AI, connections, jobs, failing kinds. Custom range ghi `#range=custom&from=…&to=…` và tự chọn bước 5 phút. Phần cố định có badge riêng: Cost (tính từ đầu tháng), Delivery. Bullet AI theo app vẫn tính "24 h gần nhất" vì cap tính theo ngày. |
| (1) App chips lọc mọi section | **fixed** | Lỗi: meter Cost vẫn ghi "Spent $268 / Forecast $396 / Budget $450" khi đã lọc, dù hero đã đổi thành $222.77. Đã sửa: meter và aria-label giờ tính lại theo share của app đang chọn. Các section còn lại lọc đúng. Platform dùng chung luôn hiện. |
| (1) Double-click chip trên toolbar = chỉ app đó | done | `#apps=bk` hiện 1 tile |
| (1) Filter severity/status (Needs attention), severity + search (Events), status (Services) | done | Mỗi list có dòng "Showing x of y · n hidden by filters" |
| (1) Sort và aria-sort | done | Header 3 trạng thái, `aria-sort` ascending/descending/none, ghi vào hash `sort=svc.up.desc`. Ở ≤900 px có dropdown Sort. Đã thử sort trên svc, q, conn và ev. |
| (3) Legend: tick ẩn/hiện, nút "only", phím O, Reset | done | Headroom và đường ngưỡng của series bị ẩn cũng ẩn theo. Khi ẩn hết, chart báo "All series are hidden…". |
| (3) Double-click legend = "only this" | **fixed** | Lỗi: click đầu dựng lại legend nên event `dblclick` không tới, double-click chỉ bật/tắt 2 lần. Đã sửa: dùng `e.detail === 2` trong click handler và bỏ listener dblclick. Kiểm lại: double-click bk thì chỉ còn bk. |
| (4) Ngưỡng + headroom trên mọi chart | done (2 chỗ có chủ ý) | Đã có ngưỡng và headroom ở: tile requests (đường capacity hoặc nhãn "off scale"), traffic (cap theo màu app), 5xx (warn/crit), p95 (warn/crit, Lambda TP 6 s), queue wait (15/60 min), spend/h (anomaly guard, breaker, cap pace theo connection), queue bars (capacity + "% headroom"), 6 sparkline tài nguyên (warn/crit, ngưỡng ngoài thang ghi "↑"), daily cost (budget share), bullet theo app và theo connection (80 % + cap), meter cost (80 % + budget), uptime (SLO + "budget % left"). **Còn thiếu:** failing job kinds có vạch warn nhưng headroom chỉ nằm trong tooltip. **Có chủ ý:** event lanes và share bar không phải chart đo giới hạn. |
| Compare previous period | **fixed** | Lúc đầu chỉ 4 golden chart có đường kỳ trước. Đã thêm đường kỳ trước vào 4 tile chart requests cho khớp "deltas in app tiles". Chart spend không có dữ liệu kỳ trước (đã ghi rõ trong What's new). |
| URL hash state | done | Lưu range, apps, cmp, hide, filter, q, sort, ack, theme. Reload giữ nguyên legend. replaceState không bắn hashchange. Copy link có fallback khi bị chặn. Riêng preview "All green" không vào hash (chỉ dùng cho mock). |
| Layout 390 px | done + **fixed** | Ở 390 px: scrollWidth = 390, 0 phần tử tràn, kể cả khi mở custom popover và What's new. Lỗi: hàng app của toolbar cuộn ngang với scrollbar ẩn, đẩy "Copy link" và "Reset view" ra x≈926, ngoài màn hình. Đã sửa: chỉ dải chip cuộn ngang, hai nút xuống dòng. `filtered-note` ẩn trên phone. scroll-padding-top tăng 150 → 196 px cho khớp toolbar sticky cao 186 px. |
| Dark mode tokens | done | Token có ở `:root`, khối `prefers-color-scheme` có guard `:not([data-theme=light])` và `[data-theme=dark]`. Body nền #0d0d0d ở dark, #f9f9f7 ở light. Nút Theme xoay vòng auto/light/dark. |
| Không tải gì từ ngoài | done | 0 request ngoài `file:`, 0 lỗi console/pageerror |
| Không tên thật / ID thật | done | Không có account ID, ARN, e-mail hay tên người. Chỉ có "tech lead" và tên alarm theo mẫu đặt tên. |
| Còn lại (không sửa) | note | Zoom bằng kéo chỉ chạy với chuột, chưa có trên cảm ứng. Danh sách Needs attention là trạng thái hiện tại, không theo range (danh sách Resolved thì theo range). |

### Ghi chú ngắn
1. Hướng (1)–(4) đã chạy được thật bằng logic, không chỉ là markup. Mình sửa 4 lỗi: meter Cost không theo bộ lọc app, double-click legend không ra "only", tile chart thiếu đường kỳ trước, nút toolbar bị đẩy ra ngoài màn hình ở 390 px.
2. Chỉ còn 1 thiếu nhỏ: failing job kinds chưa có dòng headroom hiện sẵn, chỉ có trong tooltip. Event lanes và share bar không có ngưỡng là có chủ ý.
3. Trang không tải gì từ ngoài, không có ID thật, dark/light đủ token, không cuộn ngang ở 390 px. Mockup sẵn sàng đưa tech lead xem.

### (5) 12 ý tưởng nên làm cho trang Ecosystem status

| # | Tính năng (học từ) | Giải quyết gì | Trên trang | Nguồn dữ liệu | Effort | USD/tháng | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 1 | Annotations + "What changed" (Grafana, Datadog Change Tracking) | Không biết đỉnh lỗi đến từ deploy, đổi setting, migration, wave hay đổi route control | Vạch dọc trên mọi chart, màu theo loại, tick để ẩn từng loại; panel "What changed" lọc theo app/loại, có link PR/run | `shared.ops_event`, ghi từ ECS deploy, summary.json, audit settings, DB Migrate, `/admin/waves`, đổi route control | S–M | 0 | P1 |
| 2 | Ack / snooze / mute có người phụ trách (PagerDuty, Opsgenie) | Alert lặp lại mỗi tick, không rõ ai đang xử lý | Ack · Snooze 1h/4h/đến mai · Mute có hạn, lý do ≥ 20 ký tự, tự hết hạn; ghi "Acked by tech lead 08:12" | `ops_event` + `shared.notifications` (thêm ack/snooze/owner) | S–M | 0 | P1 |
| 3 | Data freshness từng nguồn (Grafana, Better Stack) | Sampler chết mà trang vẫn xanh | Chip "as of 08:51" ở mỗi section, quá TTL thì chuyển xám "stale"; footer liệt kê sampler, schema dump, guards, digest | `as_of` của `/admin/overview/status` | S | 0 | P1 |
| 4 | Capacity forecast (New Relic, Railway) | Thấy % hiện tại nhưng không biết còn bao lâu chạm trần | "RDS còn ~41 ngày tới 15 GiB free · AI spend chạm cap ngày 27 · Actions cache 7.8/10 GB" | CloudWatch RDS, `spend_budget`, `llm_call_log`, GitHub API | S–M | 0 | P1 |
| 5 | Cost anomaly theo app × provider × route (AWS Cost Anomaly Detection) | Batch trả phí chạy quá tay, cuối ngày mới thấy | Banner "AI spend CIS 14–15h gấp 4.2× median 7 ngày". Chart nhóm theo app × provider × route: hôm nay ưu tiên API direct (1 key), khi chuyển sang Bedrock vẫn theo dõi được từng app mà không phải sửa trang (G6) | `llm_call_log` theo giờ; Cost Explorer 1 lần/ngày (tuỳ chọn) | S | 0 (~0.30 nếu dùng CE API) | P1 |
| 6 | Daily digest + push (Better Stack, Opsgenie) | Tech lead không ngồi trước trang cả ngày | Digest OPS-12 dùng chung hàm verdict, có link tới đúng view; push SEV1/2 chưa ack sau 10 phút | SNS email; web push PWA | S | 0 | P1 digest, P2 push |
| 7 | Saved views có tên + tạm dừng auto-refresh (Grafana) | URL state đã có nhưng chưa lưu được góc nhìn hay dùng; refresh làm mất zoom khi đang soi | View có tên ("Wave watch", "AI spend"); chip "Auto 60s · Pause", tự dừng khi tab ẩn, khi zoom hoặc khi chọn range custom | URL hash (đã có) + user prefs | S | 0 | P1 |
| 8 | Accessibility WCAG 2.2 AA | Màu đang là tín hiệu chính; tech lead hay xem trên điện thoại | Trạng thái luôn có icon + chữ, "View as table" cho mọi chart, focus bàn phím, aria-live cho verdict | Kit primitives | S–M | 0 | P1 |
| 9 | SLO + error budget burn (SRE Workbook) | Ngưỡng tức thời không cho biết tháng này còn chịu được bao nhiêu lỗi | "99.6 % / SLO 99.5 % · budget còn 38 % · burn 1h 2.1×"; báo khi burn 1h > 14.4× hoặc 6h > 6× | ALB/API GW (GetMetricData), `ops_sample` | M | 0 | P2 (chạy thử trên Dev) |
| 10 | Incident record + timeline (PagerDuty, incident.io) | Sự cố hiện chỉ nằm trong log phiên | "Declare incident" từ alert: SEV, người phụ trách, trạng thái, timeline tự ghép từ `ops_event`, nút "Tạo lesson" | Bảng incident mới + `ops_event` | M | 0 | P2 |
| 11 | Synthetic checks từ bên ngoài (Better Stack) | Sampler chạy trong VPC nên không thấy lỗi DNS/TLS như khách gặp | Dải "external" đặt cạnh "internal", cảnh báo cert sắp hết hạn | GitHub Actions cron 5–15 phút (repo public nên miễn phí, cron có thể trễ) | S | 0 (Route 53 0.50–0.75/check nếu cần) | P2 |
| 12 | Drill-down theo tenant (Honeycomb) | Lỗi hay spend đang dồn vào đại lý nào? | Filter "tenant"; top tenant theo spend, job lỗi, 5xx | `llm_call_log.tenant_id`, `crm.job`, CRM M2M | M | 0 | P3 (khi có tenant thật) |

Mình bỏ khỏi danh sách: dependency map, anomaly bands, view theo vai trò, "Explain this", DORA, export CSV/PNG, keyboard shortcuts, status page cho đại lý. Lý do: hoặc chưa cần ở giai đoạn Dev, hoặc phần lõi đã có (URL state, table view), hoặc sẽ tự có khi xong mục 1 và 10 (DORA, incident timeline). Hướng chung giữ nguyên: dùng một bảng `shared.ops_event` cho annotations, change log, ack, incident và DORA về sau. Chỉ mục 5 (CE API, tuỳ chọn) là tốn tiền.
