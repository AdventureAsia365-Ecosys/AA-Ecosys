import sys, html
from decimal import Decimal, ROUND_HALF_UP
sys.path.insert(0, sys.argv[1])
from audit_data import AREAS, RISKS, AREA_LABEL, PLAN, NOT_CHECKED, CRITIC_APPLIED, SOURCES

OUT = "/home/nghiep/projects/AA-Ecosys/.tmp-session/S282/audit/ecosystem-audit"
e = html.escape
LV = {3: "Cao", 2: "Trung bình", 1: "Thấp"}

def r1(x):
    return float(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

def vn(x):
    s = f"{x:.1f}" if x != int(x) else f"{int(x)}"
    return s.replace(".", ",")

for a in AREAS:
    raw = sum(s[1] for s in a["subs"]) / len(a["subs"])
    a["raw"] = raw
    a["score"] = r1(raw)
overall_raw = sum(a["raw"] for a in AREAS) / len(AREAS)
OVERALL = r1(overall_raw)

risks = []
for i, (txt, areas, imp, lik, eff, act, ev) in enumerate(RISKS):
    risks.append(dict(txt=txt, areas=areas.split(","), imp=imp, lik=lik, eff=eff, act=act, ev=ev, sev=imp * lik, ord=i))
risks.sort(key=lambda r: (-r["sev"], -r["imp"], r["ord"]))
for i, r in enumerate(risks, 1):
    r["id"] = f"R{i:02d}"

top5 = risks[:5]

# ---------- chart ----------
def chart():
    W, x0, unit, rowh, top = 360, 8, 62, 46, 26
    rows = []
    grid = []
    for t in range(6):
        x = x0 + t * unit
        grid.append(f'<line x1="{x}" y1="{top-6}" x2="{x}" y2="{top + rowh*6 - 8}" class="grid"/>'
                    f'<text x="{x}" y="{top-10}" class="tick" text-anchor="middle">{t}</text>')
    for i, a in enumerate(AREAS):
        y = top + i * rowh
        w = a["score"] * unit
        rows.append(
            f'<g class="bar"><title>{e(a["short"])}: {vn(a["score"])} / 5 (trước critic {vn(a["orig"])})</title>'
            f'<text x="{x0}" y="{y+12}" class="lab">{e(a["short"])}</text>'
            f'<rect x="{x0}" y="{y+18}" width="{w:.1f}" height="14" rx="4" class="fill"/>'
            f'<text x="{x0 + w + 6:.1f}" y="{y+30}" class="val">{vn(a["score"])}</text></g>')
    h = top + rowh * 6
    return (f'<svg viewBox="0 0 {W} {h}" role="img" aria-label="Điểm trưởng thành sáu lĩnh vực, thang 0 đến 5" class="chart">'
            + "".join(grid) + "".join(rows) + "</svg>")

def bar(score):
    return (f'<span class="sbar" aria-hidden="true"><span style="width:{score/5*100:.0f}%"></span></span>'
            f'<span class="snum">{vn(score)}</span>')

def sev_pill(level, kind):
    cls = {3: "hi", 2: "md", 1: "lo"}[level]
    return f'<span class="pill {cls}">{LV[level]}</span>'

# ---------- sections ----------
exec_bullets = [
    f"Điểm chung <b>{vn(OVERALL)} / 5</b> (mức 3 'Defined': quy trình được định nghĩa, nhiều chỗ đã đo). Vượt mức thường thấy ở nhóm 2-3 người; điểm yếu tập trung ở con người, nhà cung cấp và độ lệch tài liệu, không ở kỹ thuật lõi.",
    "Mạnh nhất: pipeline migration expand/contract có chốt an toàn, AI gateway một cửa với ledger từng lượt gọi, deploy fail closed + auto-rollback, bài học biến thành guard có test.",
    "Rủi ro số 1 là <b>bus factor = 1</b>: một người giữ mọi quyền và duyệt mọi thứ, trong khi giao hàng phụ thuộc gần như hoàn toàn vào agent AI.",
    "Nhà cung cấp AI mong manh: Bedrock chạy trên acc1 (tài khoản cá nhân, ngoài org), acc3 vẫn bị chặn, Claude dựa vào key tài trợ; Billing Transfer 01/12 đổi payer, role truy cập org phải bật trước 20/11.",
    "Hai cam kết chưa thành hiện thực: retention (67/137 dòng 'proposed', job TTL chính DRY RUN) và đo chất lượng nội dung AI (instrument v2-v5 no_go, cổng chỉ cảnh báo).",
    "Trước PII thật / tenant trả tiền còn thiếu: MFA bắt buộc cho staff, DPA ký, scrub PII trước AI cho CIS/tenant, diễn tập sự cố bảo mật, kênh cảnh báo thứ hai. Nên gom thành <b>một cổng go-live</b> có ngày.",
    "Tài liệu lệch thực tế ở nhiều nơi (LLM 'trên acc3', mô hình B2C cũ, 12/25 runbook chưa ghi lần thử): sửa một lượt và thêm lint cụm từ lỗi thời.",
    "Chi phí: acc2 dự báo 277,6/300 USD tháng 11 dù chưa có khách. Kế hoạch giữ cỡ startup: hầu hết hành động 0 USD, không thêm công cụ doanh nghiệp.",
]

def area_section(a):
    rows = "".join(
        f'<tr><td class="nm">{e(n)}</td><td class="sc">{bar(s)}</td><td class="bm">{e(b)}</td>'
        f'<td>{e(st)}<div class="ev">{e(ev)}</div></td></tr>' for n, s, b, st, ev in a["subs"])
    arisks = [r for r in risks if a["key"] in r["areas"]]
    rl = "".join(f'<li><a href="#{r["id"]}" class="rid">{r["id"]}</a> {e(r["txt"])}</li>' for r in arisks)
    st = "".join(f"<li>{e(s)}</li>" for s in a["strengths"])
    delta = "" if a["score"] == a["orig"] else f' <span class="muted">(auditor chấm {vn(a["orig"])}, sau critic {vn(a["score"])})</span>'
    return f'''
<article class="area" id="area-{a["key"]}">
  <header class="ahead"><h3>{e(a["name"])}</h3><div class="big">{vn(a["score"])}<small>/5</small></div></header>
  <p class="bench"><span class="eyebrow">Chuẩn so sánh</span> {e(a["bench"])}</p>
  <p>{e(a["summary"])}{delta}</p>
  <div class="tw"><table class="subs"><thead><tr><th>Mục con</th><th>Điểm</th><th>Chuẩn</th><th>Hiện trạng và bằng chứng</th></tr></thead><tbody>{rows}</tbody></table></div>
  <div class="two">
    <div><h4>Điểm mạnh</h4><ul>{st}</ul></div>
    <div><h4>Rủi ro của lĩnh vực</h4><ul class="rl">{rl}</ul></div>
  </div>
</article>'''

def risk_rows():
    out = []
    for r in risks:
        ar = " ".join(r["areas"])
        tags = "".join(f'<span class="tag">{AREA_LABEL[x]}</span>' for x in r["areas"])
        out.append(
            f'<tr id="{r["id"]}" data-areas="{ar}" data-id="{r["id"][1:]}" data-sev="{r["sev"]}" data-imp="{r["imp"]}" data-lik="{r["lik"]}" data-eff="{"SML".index(r["eff"])}">'
            f'<td class="mono">{r["id"]}</td><td class="rt">{e(r["txt"])}<div class="tags">{tags}</div></td>'
            f'<td>{sev_pill(r["imp"],"i")}</td><td>{sev_pill(r["lik"],"l")}</td>'
            f'<td class="mono sevn">{r["sev"]}</td><td class="mono">{r["eff"]}</td>'
            f'<td class="act">{e(r["act"])}</td><td class="ev">{e(r["ev"])}</td></tr>')
    return "".join(out)

def plan_section():
    cols = []
    for k in ("now", "next", "later"):
        title, sub, items = PLAN[k]
        li = "".join(f'<li><span>{e(t)}</span><span class="meta"><b>{ef}</b> · {e(who)}</span></li>' for t, ef, who in items)
        cols.append(f'<div class="pcol {k}"><h3>{e(title)}</h3><p class="muted">{e(sub)}</p><ol>{li}</ol></div>')
    return "".join(cols)

nc = "".join(f'<div><h4>{e(t)}</h4><ul>{"".join(f"<li>{e(x)}</li>" for x in xs)}</ul></div>' for t, xs in NOT_CHECKED)
crit = "".join(f"<li>{e(x)}</li>" for x in CRITIC_APPLIED)
area_opts = "".join(f'<option value="{k}">{v}</option>' for k, v in AREA_LABEL.items())
score_tbl = "".join(
    f'<tr><td><a href="#area-{a["key"]}">{e(a["short"])}</a></td><td class="sc">{bar(a["score"])}</td><td class="mono">{vn(a["orig"])}</td><td class="mono">{len(a["subs"])}</td><td class="mono">{len([r for r in risks if a["key"] in r["areas"]])}</td></tr>'
    for a in AREAS)

CSS = r"""
:root{
/* Layout: one reading column (max 1080px), score chart beside the summary on wide screens, wide tables scroll in place. */
--bg:#f6f7f8;--surface:#ffffff;--ink:#16202a;--ink2:#46525e;--muted:#6b7682;--line:#dde2e7;--accent:#1f6f8b;--accent-soft:#e3eff4;
--hi:#b42318;--hi-bg:#fde8e6;--md:#9a5b00;--md-bg:#fdf0d9;--lo:#2f6b3a;--lo-bg:#e4f2e6;--grid:#e3e7eb;
--f-head:"Space Grotesk","Be Vietnam Pro",system-ui,sans-serif;--f-body:"Be Vietnam Pro",system-ui,-apple-system,"Segoe UI",sans-serif;--f-mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0f1519;--surface:#161e24;--ink:#e6ebef;--ink2:#b5c0c9;--muted:#8a96a1;--line:#2a343c;--accent:#5fb3d0;--accent-soft:#1a2f38;--hi:#ff8a7a;--hi-bg:#3a1c19;--md:#f2b955;--md-bg:#36290f;--lo:#7ccc8a;--lo-bg:#16301c;--grid:#243039;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0f1519;--surface:#161e24;--ink:#e6ebef;--ink2:#b5c0c9;--muted:#8a96a1;--line:#2a343c;--accent:#5fb3d0;--accent-soft:#1a2f38;--hi:#ff8a7a;--hi-bg:#3a1c19;--md:#f2b955;--md-bg:#36290f;--lo:#7ccc8a;--lo-bg:#16301c;--grid:#243039;color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--f-body);font-size:15px;line-height:1.6}
.wrap{max-width:1080px;margin:0 auto;padding-block:28px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
h1,h2,h3,h4{font-family:var(--f-head);line-height:1.25;text-wrap:balance;margin:0}
h1{font-size:2rem;letter-spacing:-.01em}
h2{font-size:1.45rem;margin-bottom:14px;padding-top:8px}
h3{font-size:1.12rem}
h4{font-size:.95rem;margin-bottom:6px}
p{margin:0 0 10px;max-width:72ch}
a{color:var(--accent)}
a:focus-visible,button:focus-visible,select:focus-visible,th:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.eyebrow{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:600}
.muted{color:var(--muted)}
.mono,.ev{font-family:var(--f-mono)}
.ev{font-size:.72rem;color:var(--muted);margin-top:4px;word-break:break-word}
.masthead{display:flex;flex-direction:column;gap:6px;margin-bottom:22px;border-bottom:1px solid var(--line);padding-bottom:18px}
.masthead .meta{color:var(--ink2);font-size:.9rem}
nav.toc{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.88rem;margin-top:6px}
section{margin-top:40px}
.exec{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:28px;align-items:start}
.exec ul{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:8px}
.chartbox{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px}
.overall{display:flex;align-items:baseline;gap:10px;margin-bottom:8px}
.overall .n{font-family:var(--f-head);font-size:2.6rem;font-weight:700;color:var(--accent);line-height:1}
.chart{width:100%;max-width:560px;height:auto;display:block}
.chart .grid{stroke:var(--grid);stroke-width:1}
.chart .tick{fill:var(--muted);font-size:10px;font-family:var(--f-mono)}
.chart .lab{fill:var(--ink2);font-size:12px;font-family:var(--f-body)}
.chart .val{fill:var(--ink);font-size:12px;font-weight:700;font-family:var(--f-mono)}
.chart .fill{fill:var(--accent)}
.chart .bar:hover .fill{opacity:.8}
.tw{overflow-x:auto;margin:12px 0;border:1px solid var(--line);border-radius:8px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:.86rem}
th,td{text-align:left;vertical-align:top;padding:9px 10px;border-bottom:1px solid var(--line)}
tr:last-child td{border-bottom:0}
th{font-size:.74rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600;background:var(--surface);white-space:nowrap}
td.sc{white-space:nowrap}
.sbar{display:inline-block;width:64px;height:8px;border-radius:4px;background:var(--grid);vertical-align:middle;margin-right:8px;overflow:hidden}
.sbar span{display:block;height:100%;background:var(--accent);border-radius:4px}
.snum{font-family:var(--f-mono);font-weight:700;font-variant-numeric:tabular-nums}
table.subs{min-width:820px}
table.subs td.nm{font-weight:600;width:18%}
table.subs td.bm{width:20%;color:var(--ink2);font-size:.8rem}
.area{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px;margin-top:18px}
.area .tw{border-radius:6px}
.ahead{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:6px}
.big{font-family:var(--f-head);font-size:2rem;font-weight:700;color:var(--accent);line-height:1;white-space:nowrap}
.big small{font-size:.9rem;color:var(--muted);font-weight:500}
.bench{font-size:.88rem;color:var(--ink2)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:10px}
.two ul{margin:0;padding-left:18px;font-size:.9rem;display:flex;flex-direction:column;gap:5px}
.rl{list-style:none;padding-left:0!important}
.rid{font-family:var(--f-mono);font-size:.78rem;font-weight:700;text-decoration:none;margin-right:4px}
.controls{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;font-size:.88rem}
select{font:inherit;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--surface);color:var(--ink)}
table.risks{min-width:1100px}
table.risks th[data-k]{cursor:pointer;user-select:none}
table.risks th[data-k]::after{content:" \2195";color:var(--line)}
table.risks th[aria-sort="ascending"]::after{content:" \2191";color:var(--accent)}
table.risks th[aria-sort="descending"]::after{content:" \2193";color:var(--accent)}
table.risks td.rt{width:28%}
table.risks td.act{width:28%;color:var(--ink2)}
table.risks td.ev{width:16%}
table.risks tr:target td{background:var(--accent-soft)}
.sevn{font-weight:700;font-size:1rem}
.pill{display:inline-block;font-size:.72rem;font-weight:600;padding:2px 8px;border-radius:999px;white-space:nowrap}
.pill.hi{color:var(--hi);background:var(--hi-bg)}
.pill.md{color:var(--md);background:var(--md-bg)}
.pill.lo{color:var(--lo);background:var(--lo-bg)}
.tags{margin-top:4px;display:flex;flex-wrap:wrap;gap:4px}
.tag{font-size:.68rem;color:var(--ink2);border:1px solid var(--line);border-radius:4px;padding:0 5px}
.plan{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.pcol{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px;border-top:4px solid var(--accent)}
.pcol.next{border-top-color:var(--md)}
.pcol.later{border-top-color:var(--muted)}
.pcol ol{margin:8px 0 0;padding-left:20px;display:flex;flex-direction:column;gap:9px;font-size:.88rem}
.pcol li span{display:block}
.pcol .meta{font-size:.75rem;color:var(--muted);font-family:var(--f-mono)}
.nc{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 24px}
.nc ul,.method ul{margin:0;padding-left:18px;font-size:.88rem;display:flex;flex-direction:column;gap:4px}
.scale{display:flex;flex-wrap:wrap;gap:8px;font-size:.82rem;margin:8px 0 14px}
.scale span{border:1px solid var(--line);border-radius:6px;padding:3px 8px;background:var(--surface)}
footer{margin-top:40px;font-size:.8rem;color:var(--muted);border-top:1px solid var(--line);padding-top:14px}
@media (max-width:820px){.exec,.two,.plan,.nc{grid-template-columns:1fr}h1{font-size:1.6rem}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = r"""
(function(){
 var tb=document.querySelector('table.risks tbody'); if(!tb) return;
 var ths=document.querySelectorAll('table.risks th[data-k]');
 var sel=document.getElementById('area-filter'); var cnt=document.getElementById('risk-count');
 function apply(){var v=sel.value,n=0;Array.prototype.forEach.call(tb.rows,function(r){var ok=!v||(' '+r.dataset.areas+' ').indexOf(' '+v+' ')>-1;r.hidden=!ok;if(ok)n++;});cnt.textContent=n;}
 function sortBy(th){var k=th.dataset.k;var cur=th.getAttribute('aria-sort');var dir=cur==='descending'?'ascending':'descending';if(k==='id'&&!cur)dir='ascending';
  Array.prototype.forEach.call(ths,function(t){t.removeAttribute('aria-sort');});th.setAttribute('aria-sort',dir);
  var rows=Array.prototype.slice.call(tb.rows);var m=dir==='ascending'?1:-1;
  rows.sort(function(a,b){var d=(parseFloat(a.dataset[k])-parseFloat(b.dataset[k]))*m;return d||(parseFloat(a.dataset.id)-parseFloat(b.dataset.id));});
  rows.forEach(function(r){tb.appendChild(r);});}
 Array.prototype.forEach.call(ths,function(th){th.tabIndex=0;th.addEventListener('click',function(){sortBy(th);});th.addEventListener('keydown',function(ev){if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();sortBy(th);}});});
 sel.addEventListener('change',apply);
 try{var s=localStorage.getItem('aa1109-area');if(s){sel.value=s;}}catch(e){}
 sel.addEventListener('change',function(){try{localStorage.setItem('aa1109-area',sel.value);}catch(e){}});
 apply();
})();
"""

top5_html = "".join(f'<li><a href="#{r["id"]}" class="rid">{r["id"]}</a> {e(r["txt"])}</li>' for r in top5)

page = f'''<title>Audit hệ sinh thái AA</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>{CSS}</style>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&family=Space+Grotesk:wght@500;700&display=swap">
<div class="wrap">
<header class="masthead">
  <span class="eyebrow">AA-1109 · Phiên S282 · 16/11/2026 · Môi trường Dev</span>
  <h1>Audit hệ sinh thái AA</h1>
  <p class="meta">Đánh giá mức trưởng thành của CIS, Booking, TripPlanner, Partner (CRM) và hạ tầng chung, cho tech lead. Nhóm 2-3 dev cùng agent AI, chưa có prod, chưa có tenant trả tiền, mô hình chỉ B2B (ADR 0019). Thang 1-5: 1 ad hoc, 2 lặp lại được, 3 được định nghĩa, 4 được đo, 5 được tối ưu.</p>
  <nav class="toc" aria-label="Mục lục"><a href="#s1">1 Tóm tắt điều hành</a><a href="#s2">2 Bảng điểm theo lĩnh vực</a><a href="#s3">3 Rủi ro xếp hạng</a><a href="#s4">4 Kế hoạch đề xuất</a><a href="#s5">5 Chưa kiểm và phương pháp</a></nav>
</header>

<section id="s1"><h2>1. Tóm tắt điều hành</h2>
<div class="exec">
  <div><ul>{"".join(f"<li>{b}</li>" for b in exec_bullets)}</ul>
  <h4 style="margin-top:18px">Năm rủi ro đầu bảng</h4><ul class="rl">{top5_html}</ul></div>
  <div class="chartbox">
    <div class="overall"><span class="n">{vn(OVERALL)}</span><span class="muted">/ 5 · trung bình sáu lĩnh vực</span></div>
    {chart()}
    <p class="muted" style="font-size:.78rem;margin-top:8px">Mỗi thanh là điểm lĩnh vực sau khi áp critic (trung bình các mục con), cùng thang 0-5. Di chuột lên thanh để xem điểm auditor chấm ban đầu.</p>
    <div class="tw" style="margin-bottom:0"><table><thead><tr><th>Lĩnh vực</th><th>Điểm</th><th>Trước critic</th><th>Mục con</th><th>Rủi ro</th></tr></thead><tbody>{score_tbl}</tbody></table></div>
  </div>
</div>
</section>

<section id="s2"><h2>2. Bảng điểm theo lĩnh vực</h2>
<p>Mỗi mục con chấm theo hai chuẩn: kế hoạch riêng của dự án (ADR, data standards, plan.json) và một chuẩn công khai có tên. Bằng chứng ghi dạng chữ mono nhỏ: đường dẫn file và mục, run/PR, hoặc lệnh đọc live ngày 16/11.</p>
{"".join(area_section(a) for a in AREAS)}
</section>

<section id="s3"><h2>3. Rủi ro xếp hạng</h2>
<p>{len(risks)} rủi ro sau khi gộp các mục trùng giữa lĩnh vực và thêm rủi ro liên lĩnh vực của critic. Điểm = tác động × khả năng (Cao 3, Trung bình 2, Thấp 1). Bấm tiêu đề cột để sắp xếp. Effort: S dưới 1 ngày, M vài ngày, L một sprint trở lên.</p>
<div class="controls"><label for="area-filter">Lọc theo lĩnh vực</label><select id="area-filter"><option value="">Tất cả</option>{area_opts}</select><span class="muted">Đang hiện <b id="risk-count">{len(risks)}</b> rủi ro</span></div>
<div class="tw"><table class="risks"><thead><tr>
<th data-k="id">#</th><th>Rủi ro</th><th data-k="imp">Tác động</th><th data-k="lik">Khả năng</th><th data-k="sev" aria-sort="descending">Điểm</th><th data-k="eff">Effort</th><th>Hành động</th><th>Bằng chứng</th>
</tr></thead><tbody>{risk_rows()}</tbody></table></div>
</section>

<section id="s4"><h2>4. Kế hoạch đề xuất</h2>
<p>Cỡ startup: hầu hết hành động là sửa tài liệu, bật cấu hình có sẵn hoặc diễn tập, chi phí 0 USD. Mục nào tốn tiền (eval định kỳ, rate limit biên, GuardDuty, backup khác vùng) đều cần một lần duyệt chi phí riêng.</p>
<div class="plan">{plan_section()}</div>
</section>

<section id="s5"><h2>5. Những gì chưa kiểm và phương pháp</h2>
<h3 style="margin-bottom:10px">Chưa kiểm (not checked)</h3>
<div class="nc">{nc}</div>
<div class="method" style="margin-top:24px">
<h3 style="margin-bottom:8px">Phương pháp</h3>
<p>Sáu auditor chỉ đọc, mỗi người một lĩnh vực, cộng một critic kiểm lại các khẳng định chính bằng lệnh đọc live và tìm rủi ro liên lĩnh vực bị bỏ sót. Không ghi repo, không push, không ghi AWS, không ECS exec, không Terraform apply, không gọi LLM trả phí. Mọi khẳng định có bằng chứng; chỗ không kiểm được ghi rõ ở trên.</p>
<div class="scale"><span>1 Ad hoc</span><span>2 Lặp lại được</span><span>3 Được định nghĩa</span><span>4 Được đo</span><span>5 Được tối ưu</span></div>
<h4>Chuẩn công khai dùng để so</h4>
<p>AWS Well-Architected (6 trụ + Generative AI Lens, SaaS Lens), DORA four keys, OWASP ASVS 4.0.3 L2 / Top 10 / LLM Top 10 2025, CIS AWS Foundations v3, CIS Controls v8, DAMA-DMBOK, NIST AI RMF 1.0, NIST CSF 2.0, NIST SP 800-61r3, EU AI Act Art. 50, PDPL (Luật 91/2025) + NĐ 356/2025, FinOps Framework, ITIL-lite, ISO 22301, OpenSSF Scorecard.</p>
<h4>Điều chỉnh theo critic</h4>
<ul>{crit}</ul>
<h4 style="margin-top:12px">Nguồn</h4>
<p class="ev" style="font-size:.76rem">{e(SOURCES)}</p>
</div>
</section>
<footer>AA-1109 · S282 · Tác nhân: Claude Code (6 auditor + critic). Báo cáo không chứa ID tài khoản, ARN, e-mail hay giá trị secret.</footer>
</div>
<script>{JS}</script>
'''

with open(f"{OUT}/index.html", "w", encoding="utf-8") as f:
    f.write(page)

# ---------- README ----------
md = []
md.append("# Audit hệ sinh thái AA (AA-1109, S282)\n")
md.append("Ngày 16/11/2026 · Môi trường Dev · Viết cho tech lead. Nhóm 2-3 dev cùng agent AI, chưa có prod, chưa có tenant trả tiền, mô hình chỉ B2B (ADR 0019). Thang 1-5: 1 ad hoc, 2 lặp lại được, 3 được định nghĩa, 4 được đo, 5 được tối ưu.\n")
md.append("## 1. Tóm tắt điều hành\n")
for b in exec_bullets:
    md.append("- " + b.replace("<b>", "**").replace("</b>", "**"))
md.append("")
md.append("| Lĩnh vực | Điểm | Trước critic |\n|---|---|---|")
for a in AREAS:
    md.append(f"| {a['short']} | {vn(a['score'])} | {vn(a['orig'])} |")
md.append(f"| **Chung** | **{vn(OVERALL)}** | |\n")
md.append("## 2. Bảng điểm theo lĩnh vực\n")
for a in AREAS:
    md.append(f"### {a['name']}: {vn(a['score'])}/5\n")
    md.append(f"Chuẩn so sánh: {a['bench']}\n")
    md.append(a["summary"] + "\n")
    md.append("| Mục con | Điểm | Chuẩn | Hiện trạng |\n|---|---|---|---|")
    for n, s, b, st, ev in a["subs"]:
        md.append(f"| {n} | {vn(s)} | {b} | {st} Bằng chứng: `{ev}` |")
    md.append("\nĐiểm mạnh:\n")
    for s in a["strengths"]:
        md.append("- " + s)
    md.append("")
md.append("## 3. Rủi ro xếp hạng\n")
md.append("Điểm = tác động × khả năng (Cao 3, Trung bình 2, Thấp 1). Effort: S dưới 1 ngày, M vài ngày, L một sprint trở lên.\n")
for r in risks:
    ar = ", ".join(AREA_LABEL[x] for x in r["areas"])
    md.append(f"{r['id'][1:]}. **{r['id']}** ({ar}; tác động {LV[r['imp']].lower()}, khả năng {LV[r['lik']].lower()}, điểm {r['sev']}, effort {r['eff']}) {r['txt']}\n   Hành động: {r['act']}\n   Bằng chứng: `{r['ev']}`")
md.append("")
md.append("## 4. Kế hoạch đề xuất\n")
for k in ("now", "next", "later"):
    title, sub, items = PLAN[k]
    md.append(f"### {title}\n\n{sub}\n")
    for t, ef, who in items:
        md.append(f"- [{ef}, {who}] {t}")
    md.append("")
md.append("## 5. Những gì chưa kiểm và phương pháp\n")
md.append("### Chưa kiểm\n")
for t, xs in NOT_CHECKED:
    md.append(f"**{t}**\n")
    for x in xs:
        md.append("- " + x)
    md.append("")
md.append("### Phương pháp\n")
md.append("Sáu auditor chỉ đọc (mỗi người một lĩnh vực) cộng một critic kiểm lại khẳng định chính bằng lệnh đọc live và bổ sung rủi ro liên lĩnh vực. Không ghi repo, không ghi AWS, không ECS exec, không Terraform apply, không gọi LLM trả phí.\n")
md.append("Chuẩn công khai: AWS Well-Architected (6 trụ, Generative AI Lens, SaaS Lens), DORA, OWASP ASVS L2 / Top 10 / LLM Top 10 2025, CIS AWS Foundations v3, CIS Controls v8, DAMA-DMBOK, NIST AI RMF 1.0, NIST CSF 2.0, NIST SP 800-61r3, EU AI Act Art. 50, PDPL + NĐ 356/2025, FinOps Framework, ITIL-lite, ISO 22301, OpenSSF Scorecard.\n")
md.append("Điều chỉnh theo critic:\n")
for c in CRITIC_APPLIED:
    md.append("- " + c)
md.append(f"\nNguồn: {SOURCES}\n")
md.append("Tác nhân: Claude Code. Báo cáo không chứa ID tài khoản, ARN, e-mail hay tên/giá trị secret.\n")
with open(f"{OUT}/README.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print("overall", OVERALL, overall_raw)
for a in AREAS: print(a["key"], a["score"], round(a["raw"],3))
print("risks", len(risks))
for r in top5: print(r["id"], r["sev"], r["txt"][:90])
