import markdown, re, html
src = open('/home/nghiep/projects/AA-Ecosys/.tmp-session/S278/pricing-advice/report.md', encoding='utf-8').read()
# drop the H1 (the page has its own header)
src = re.sub(r'^# .*\n', '', src, count=1)
body = markdown.markdown(src, extensions=['tables', 'toc', 'sane_lists'], extension_configs={'toc': {'toc_depth': '2-2'}})
md = markdown.Markdown(extensions=['tables', 'toc'], extension_configs={'toc': {'toc_depth': '2-2'}})
md.convert(src)
toc = md.toc
# wrap tables for horizontal scroll
body = body.replace('<table>', '<div class="tw"><table>').replace('</table>', '</table></div>')
body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
page = '''<title>Giá tour B2B</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: a rate-sheet reading room — narrow column, contents rail on wide screens, tariff-style tables. */
:root {
  --bg: #f6f7f5; --surface: #ffffff; --ink: #1b2420; --muted: #5d6a64; --line: #d8dfdb;
  --accent: #1f6f5c; --accent-soft: #dcefe8; --warn: #9a5b00; --warn-soft: #f6ead3;
  --display: "Source Serif 4", Georgia, serif; --body: "Be Vietnam Pro", "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", ui-monospace, Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #111614; --surface: #18201d; --ink: #e4ebe7; --muted: #9aaaa3; --line: #2b3733;
  --accent: #5cc4a6; --accent-soft: #173a31; --warn: #e3ac55; --warn-soft: #3a2c14; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #111614; --surface: #18201d; --ink: #e4ebe7; --muted: #9aaaa3; --line: #2b3733;
  --accent: #5cc4a6; --accent-soft: #173a31; --warn: #e3ac55; --warn-soft: #3a2c14; color-scheme: dark }
* { box-sizing: border-box }
body { background: var(--bg); color: var(--ink); font: 16px/1.65 var(--body); }
.wrap { max-width: 1180px; margin: 0 auto; padding-block: 32px 72px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; grid-template-columns: minmax(0, 1fr); gap: 32px }
@media (min-width: 980px) { .wrap { grid-template-columns: 230px minmax(0, 1fr) } }
header { grid-column: 1 / -1; display: grid; gap: 10px; border-bottom: 1px solid var(--line); padding-bottom: 22px }
.eyebrow { font: 500 12px/1.3 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--muted) }
h1 { font: 700 clamp(30px, 4.4vw, 44px)/1.1 var(--display); margin: 0; text-wrap: balance }
.lede { max-width: 68ch; color: var(--muted); margin: 0 }
.chips { display: flex; flex-wrap: wrap; gap: 8px }
.chip { font: 500 12.5px/1 var(--mono); padding: 6px 9px; border-radius: 6px; background: var(--accent-soft); color: var(--accent) }
nav.toc { position: sticky; top: calc(env(safe-area-inset-top, 0px) + 16px); align-self: start; font-size: 14px; display: none }
@media (min-width: 980px) { nav.toc { display: block } }
nav.toc ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px }
nav.toc a { color: var(--muted); text-decoration: none } nav.toc a:hover { color: var(--accent) }
article { min-width: 0; max-width: 78ch }
article h2 { font: 700 26px/1.2 var(--display); margin: 44px 0 12px; text-wrap: balance; scroll-margin-top: 16px }
article h3 { font: 600 18px/1.3 var(--body); margin: 26px 0 8px }
article p, article li { overflow-wrap: anywhere }
article a { color: var(--accent) }
article code { font: 13.5px var(--mono); background: var(--accent-soft); padding: 1px 5px; border-radius: 4px }
article strong { font-weight: 600 }
article hr { border: 0; border-top: 1px solid var(--line); margin: 32px 0 }
article blockquote { margin: 0; padding: 10px 14px; border-left: 3px solid var(--warn); background: var(--warn-soft); border-radius: 0 6px 6px 0 }
.dg { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); padding: 12px; margin: 14px 0 }
.dg pre { margin: 0; background: transparent }
.tw { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); margin: 14px 0 }
table { border-collapse: collapse; width: 100%; font-size: 14px; min-width: 620px }
th, td { text-align: left; vertical-align: top; padding: 9px 12px; border-bottom: 1px solid var(--line) }
th { font: 600 12px var(--mono); letter-spacing: .04em; text-transform: uppercase; color: var(--muted); background: var(--bg) }
td { font-variant-numeric: tabular-nums }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }
footer { grid-column: 1 / -1; color: var(--muted); font-size: 13px; border-top: 1px solid var(--line); padding-top: 14px }
</style>
<div class="wrap">
  <header>
    <div class="eyebrow">AA-1091 · tư vấn giá · 12/11/2026</div>
    <h1>Giá tour B2B và phiên bản giá</h1>
    <p class="lede">Ngành định giá và bán tour cho đại lý thế nào, hệ thống mình đang ở đâu, thiết kế "phiên bản giá" cho công cụ nhập giá của team CSKH, và 12 câu chính sách cần chủ doanh nghiệp chốt. Mỗi ý có link nguồn.</p>
    <div class="chips"><span class="chip">Giá NET cho đại lý</span><span class="chip">Hợp đồng NCC theo năm</span><span class="chip">Mùa theo ngày đi</span><span class="chip">Không sửa đè giá</span><span class="chip">Báo giá ghim phiên bản</span></div>
  </header>
  <nav class="toc" aria-label="Mục lục">__TOC__</nav>
  <article>__BODY__</article>
  <footer>Nguồn: nghiên cứu web (blog hãng phần mềm được ghi là [ví dụ], không phải chuẩn ngành) và đọc code AA-Booking. ADR 0005b ghi lại thiết kế; chính sách là tham số có mặc định, chủ doanh nghiệp đổi được.</footer>
</div>
'''
extra = open('/home/nghiep/projects/AA-Ecosys/.tmp-session/S278/pricing-advice/page/extra.html', encoding='utf-8').read()
toc = toc.replace('<ul>', '<ul><li><a href="#so-do-gia">Sơ đồ mô hình giá</a></li><li><a href="#tinh-nang-booking">Tính năng Booking</a></li>', 1)
page = page.replace('__TOC__', toc).replace('__BODY__', extra + body)
open('/home/nghiep/projects/AA-Ecosys/.tmp-session/S278/pricing-advice/page/gia-tour-b2b.html', 'w', encoding='utf-8').write(page)
print(len(page))
