"""The stage page for one aspect ratio (AA-1021): neutral theme, diagram reveal/focus/highlight, title and point slides.

  page.build_html(meta, aspect, svgs, font_path) -> str    (make_episode.py writes it; capture.cjs drives window.show)

capture.cjs opens the page at the frame size (1920x1080, 1080x1080, 1080x1350 or 1080x1920) with deviceScaleFactor 2,
calls window.show(visual) for each keyframe, checks the DOM (gate layer 2) and screenshots. Everything is inline: the
font is a data: URI, the diagrams are the episode's sketches (sketch.py) inside <template> elements, no network request.

Visual types (scene.py):
  title   {kicker, title, lead}                 opening card
  points  {kicker, title, points: [...]}        a short list
  diagram {diagram, kicker, title, reveal: [labels], focus: [labels], highlight: [labels]}
          reveal: groups or nodes (matched by a visible label) shown, the rest faded; a node inside a revealed group
          and an edge between two shown nodes are shown too. focus: the camera frames these (default: the whole
          diagram without reveal; with reveal: the revealed groups and nodes, not their enclosing frames).
          highlight: an accent outline around these.
  end     {kicker, title, lead}                 closing card
Theme: one open-licence sans font, dark ink on a light grey page, one accent colour; no brand colours or fonts.
"""
from __future__ import annotations

import base64
import html
from pathlib import Path

from scene import ASPECTS, LAYOUT

CSS = """
@font-face{font-family:"Plex";src:url(%(font)s) format("truetype");font-weight:100 700;font-display:block}
:root{--bg:#F4F6F8;--card:#FFFFFF;--ink:#16202B;--body:#3B4754;--muted:#66727F;--line:#DCE2E8;--accent:#0E7C7B;
  --accent-soft:#E3F2F1;--W:%(w)spx;--H:%(h)spx}
*{box-sizing:border-box}
html,body{margin:0;width:var(--W);height:var(--H);overflow:hidden;background:var(--bg);color:var(--ink);
  font-family:%(family)s;-webkit-font-smoothing:antialiased}
#frame{position:absolute;inset:0}
#tag{position:absolute;top:%(tag_top)spx;right:%(side_r)spx;font-size:%(tag_px)spx;letter-spacing:.06em;
  text-transform:uppercase;color:var(--muted);font-weight:500}
#hd{position:absolute;left:%(side_l)spx;right:%(side_r)spx;top:%(hd_top)spx;height:%(hd_h)spx;display:flex;
  flex-direction:column;justify-content:flex-end}
#hd .kicker{font-size:%(kick_px)spx;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);
  margin:0 0 6px}
#hd h1{font-size:%(h1_px)spx;line-height:1.12;font-weight:600;margin:0}
#stage{position:absolute;left:%(side_l)spx;right:%(side_r)spx;top:%(st_top)spx;height:%(st_h)spx}
.card{position:absolute;inset:0;background:var(--card);border:1px solid var(--line);border-radius:18px;
  box-shadow:0 14px 40px rgba(22,32,43,.07);overflow:hidden}
.card svg{position:absolute;inset:%(pad)spx;width:calc(100%% - %(pad2)spx);height:calc(100%% - %(pad2)spx)}
.card svg text{font-family:%(family)s}
.card svg .fade{opacity:.07}
.card svg g{transition:none}
.hl{fill:none;stroke:var(--accent);stroke-width:6;rx:14;ry:14}
.cover{position:absolute;left:%(side_l)spx;right:%(side_r)spx;top:%(cov_top)spx;bottom:%(cov_bottom)spx;display:flex;
  flex-direction:column;justify-content:center}
.cover .kicker{display:inline-block;align-self:flex-start;font-size:%(kick_px)spx;font-weight:600;letter-spacing:.08em;
  text-transform:uppercase;color:var(--accent);border:2px solid var(--accent);border-radius:999px;padding:6px 16px;
  margin:0 0 26px}
.cover h1{font-size:%(cover_px)spx;line-height:1.08;font-weight:600;margin:0 0 22px;max-width:18ch}
.cover p{font-size:%(lead_px)spx;line-height:1.45;color:var(--body);margin:0;max-width:34ch}
.cover .rule{width:%(rule_w)spx;height:8px;background:var(--accent);border-radius:4px;margin:0 0 30px}
ul.points{list-style:none;margin:0;padding:%(pts_pad)spx;display:flex;flex-direction:column;justify-content:center;
  gap:%(pts_gap)spx;height:100%%}
ul.points li{font-size:%(pt_px)spx;line-height:1.3;color:var(--ink);padding-left:%(pt_ind)spx;position:relative}
ul.points li::before{content:"";position:absolute;left:0;top:.38em;width:%(dot)spx;height:%(dot)spx;border-radius:6px;
  background:var(--accent)}
"""

JS = r"""
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim().toLowerCase();
  const frame = $('#frame');
  const aspect = document.body.dataset.aspect;
  function clear() { $('#hd').style.display = 'none'; $('#stage').innerHTML = ''; frame.querySelectorAll('.cover').forEach((e) => e.remove()); }
  function header(v) {
    const hd = $('#hd');
    hd.style.display = (v.kicker || v.title) ? 'flex' : 'none';
    $('#hd .kicker').textContent = v.kicker || '';
    $('#hd h1').textContent = v.title || '';
  }
  function cover(v, end) {
    const c = document.createElement('section');
    c.className = 'cover';
    if (v.kicker) { const k = document.createElement('div'); k.className = 'kicker'; k.textContent = v.kicker; c.append(k); }
    if (end) { const r = document.createElement('div'); r.className = 'rule'; c.append(r); }
    const h = document.createElement('h1'); h.textContent = v.title || ''; c.append(h);
    if (v.lead) { const p = document.createElement('p'); p.textContent = v.lead; c.append(p); }
    frame.append(c);
  }
  function points(v) {
    header(v);
    const card = document.createElement('div'); card.className = 'card';
    const ul = document.createElement('ul'); ul.className = 'points';
    for (const p of v.points || []) { const li = document.createElement('li'); li.textContent = p; ul.append(li); }
    card.append(ul); $('#stage').append(card);
  }
  function box(el, m) {
    const b = el.getBBox();
    const pts = [[b.x, b.y], [b.x + b.width, b.y], [b.x, b.y + b.height], [b.x + b.width, b.y + b.height]]
      .map(([x, y]) => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f]);
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    return { x: Math.min(...xs), y: Math.min(...ys), w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) };
  }
  const inside = (a, b) => a.x >= b.x - 1 && a.y >= b.y - 1 && a.x + a.w <= b.x + b.w + 1 && a.y + a.h <= b.y + b.h + 1;
  const center = (a, b) => { const cx = a.x + a.w / 2, cy = a.y + a.h / 2; return cx >= b.x && cx <= b.x + b.w && cy >= b.y && cy <= b.y + b.h; };
  const union = (bs) => {
    if (!bs.length) return null;
    const x0 = Math.min(...bs.map((b) => b.x)), y0 = Math.min(...bs.map((b) => b.y));
    const x1 = Math.max(...bs.map((b) => b.x + b.w)), y1 = Math.max(...bs.map((b) => b.y + b.h));
    return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
  };
  function diagram(v) {
    header(v);
    const tpl = document.getElementById('dg-' + v.diagram);
    if (!tpl) throw new Error('diagram not on the page: ' + v.diagram);
    const card = document.createElement('div'); card.className = 'card';
    card.append(tpl.content.cloneNode(true)); $('#stage').append(card);
    const svg = card.querySelector('svg');
    const g0 = svg.querySelector('g.graph') || svg.querySelector('g');
    const m = g0.transform.baseVal.consolidate() ? g0.transform.baseVal.consolidate().matrix : svg.createSVGMatrix();
    const groups = [...svg.querySelectorAll('g.cluster')];
    const nodes = [...svg.querySelectorAll('g.node')];
    const edges = [...svg.querySelectorAll('g.edge')];
    const bb = new Map();
    for (const el of [...groups, ...nodes]) bb.set(el, box(el, m));
    const byKey = new Map(nodes.map((n) => [n.dataset.k, n]));
    const pick = (labels) => {
      const want = new Set((labels || []).map(norm));
      const out = new Set();
      for (const el of [...groups, ...nodes]) {
        const texts = [...el.querySelectorAll(':scope > text')].map((t) => norm(t.textContent));
        if (texts.some((t) => want.has(t))) {
          out.add(el);
          const k = el.dataset.k;
          if (k && k.endsWith('-t') && byKey.get(k.slice(0, -2))) out.add(byKey.get(k.slice(0, -2)));
          if (k && byKey.get(k + '-t')) out.add(byKey.get(k + '-t'));
        }
      }
      const missing = [...want].filter((w) => ![...out].some((el) => [...el.querySelectorAll(':scope > text')].some((t) => norm(t.textContent) === w)));
      if (missing.length) throw new Error('labels not found in diagram ' + v.diagram + ': ' + missing.join(', '));
      return out;
    };
    let shown = null, core = null;
    if (v.reveal && v.reveal.length) {
      const sel = pick(v.reveal);
      const selGroups = groups.filter((g) => sel.has(g));
      shown = new Set(sel);
      for (const n of nodes) if (selGroups.some((g) => center(bb.get(n), bb.get(g)))) shown.add(n);
      for (const n of [...shown]) {
        const k = n.dataset && n.dataset.k;
        if (k && k.endsWith('-t') && byKey.get(k.slice(0, -2))) shown.add(byKey.get(k.slice(0, -2)));
        if (k && byKey.get(k + '-t')) shown.add(byKey.get(k + '-t'));
      }
      core = new Set(shown);
      for (const g of groups) {
        if (shown.has(g)) continue;
        if (selGroups.some((s) => inside(bb.get(g), bb.get(s)))) { shown.add(g); core.add(g); }
        else if (nodes.some((n) => shown.has(n) && inside(bb.get(n), bb.get(g)))) shown.add(g);
      }
      for (const el of [...groups, ...nodes]) if (!shown.has(el)) el.classList.add('fade');
      for (const e of edges) {
        const a = byKey.get(e.dataset.from), b = byKey.get(e.dataset.to);
        if (!(a && b && shown.has(a) && shown.has(b))) e.classList.add('fade');
      }
    }
    if (v.highlight && v.highlight.length) {
      for (const el of pick(v.highlight)) {
        const b = bb.get(el); if (!b || (el.dataset.k && !el.dataset.k.endsWith('-t') && byKey.get(el.dataset.k + '-t'))) continue;
        const r = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        r.setAttribute('class', 'hl');
        r.setAttribute('x', b.x - 10); r.setAttribute('y', b.y - 10);
        r.setAttribute('width', b.w + 20); r.setAttribute('height', b.h + 20);
        svg.append(r);
      }
    }
    let frameBox = null;
    if (v.focus && v.focus.length) frameBox = union([...pick(v.focus)].map((el) => bb.get(el)));
    else if (core) frameBox = union([...core].map((el) => bb.get(el)));
    if (frameBox) {
      const full = svg.viewBox.baseVal;
      const minW = full.width * 0.18, minH = full.height * 0.18;
      const w = Math.max(frameBox.w, minW), h = Math.max(frameBox.h, minH);
      const cx = frameBox.x + frameBox.w / 2, cy = frameBox.y + frameBox.h / 2;
      const pad = 0.06;
      svg.setAttribute('viewBox', `${cx - w / 2 - w * pad} ${cy - h / 2 - h * pad} ${w * (1 + 2 * pad)} ${h * (1 + 2 * pad)}`);
    }
  }
  window.show = (v) => {
    clear();
    if (v.type === 'title') cover(v, false);
    else if (v.type === 'end') cover(v, true);
    else if (v.type === 'points') points(v);
    else if (v.type === 'diagram') diagram(v);
    else throw new Error('unknown visual type ' + v.type);
    return true;
  };
})();
"""


def font_url(font_path: Path | None) -> tuple[str, str]:
    if font_path and font_path.exists():
        data = base64.b64encode(font_path.read_bytes()).decode("ascii")
        return f"data:font/ttf;base64,{data}", '"Plex","Liberation Sans",sans-serif'
    return "data:,", '"Liberation Sans","DejaVu Sans",sans-serif'


def build_html(meta: dict, aspect: str, svgs: dict[str, str], font_path: Path | None) -> str:
    w, h = ASPECTS[aspect]
    lay = LAYOUT[aspect]
    url, family = font_url(font_path)
    base = min(w, h)
    sl, sr = int(lay["side"][0] * w), int(lay["side"][1] * w)
    hd_top, hd_bot = int(lay["header"][0] * h), int(lay["header"][1] * h)
    st_top, st_bot = int(lay["stage"][0] * h), int(lay["stage"][1] * h)
    tall = aspect == "9:16"
    vals = {
        "font": url, "family": family, "w": w, "h": h, "side_l": sl, "side_r": sr,
        "tag_top": int(h * (0.035 if tall else 0.03)) if tall else max(18, int(h * 0.025)),
        "tag_px": int(base * 0.022), "hd_top": hd_top, "hd_h": hd_bot - hd_top,
        "kick_px": int(base * (0.026 if not tall else 0.03)), "h1_px": int(base * (0.05 if not tall else 0.058)),
        "st_top": st_top, "st_h": st_bot - st_top, "pad": int(base * 0.018), "pad2": 2 * int(base * 0.018),
        "cov_top": int(h * (0.12 if not tall else 0.15)), "cov_bottom": int(h * (0.24 if not tall else 0.45)),
        "cover_px": int(base * (0.075 if not tall else 0.088)), "lead_px": int(base * (0.034 if not tall else 0.042)),
        "rule_w": int(base * 0.09), "pts_pad": int(base * 0.045), "pts_gap": int(base * 0.028),
        "pt_px": int(base * (0.04 if not tall else 0.047)), "pt_ind": int(base * 0.045), "dot": int(base * 0.016),
    }
    if tall:   # the tag sits under the platform's top bar
        vals["tag_top"] = int(h * 0.04)
    css = CSS % vals
    tag = ""
    if meta.get("series_tag"):
        tag = f'<div id="tag">{html.escape(meta["series_tag"])}</div>'
    templates = "".join(f'<template id="dg-{html.escape(k)}">{svg}</template>' for k, svg in svgs.items())
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(meta.get("title", ""))}'
            f'</title><style>{css}</style></head><body data-aspect="{aspect}"><div id="frame">{tag}'
            f'<header id="hd"><div class="kicker"></div><h1></h1></header><main id="stage"></main></div>'
            f'{templates}<script>{JS}</script></body></html>')


def write(path: Path, meta: dict, aspect: str, svgs: dict[str, str], font_path: Path | None) -> Path:
    path.write_text(build_html(meta, aspect, svgs, font_path), encoding="utf-8")
    return path

