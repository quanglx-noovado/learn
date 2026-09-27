#!/usr/bin/env python3
"""Sinh interview/mindmap.html từ các file markdown trong interview/.

Mindmap toả tròn, đi sâu từng tầng: tất cả → nhóm chủ đề (theo mục lục README) → file → module
(kèm 🟢🟡🔴 của chặng) → nhóm kiến thức (các dòng `*Tên nhóm*` trong phần "Học gì"). Node đang
chọn nằm ở tâm, các con toả xung quanh; bấm một nhánh để đi vào, bấm tâm hoặc Esc để lùi.
Ở một module, panel bên cạnh hiện "Vì sao cần học" và các tiêu chí "Nắm chắc khi" để tick;
trạng thái tick lưu trong localStorage của trình duyệt.

Chỉ dùng standard library. Chạy lại mỗi khi sửa file bài học:
    python3 tools/build_mindmap.py
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "interview"
OUT = ROOT / "mindmap.html"


def inline_md(text: str) -> str:
    """Đổi markdown inline (code, đậm, nghiêng, link) sang HTML an toàn."""
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<em>\1</em>", out)
    out = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2))}" target="_blank" rel="noopener">{m.group(1)}</a>',
        out,
    )
    return out


def plain(text: str) -> str:
    """Bỏ ký hiệu markdown, dùng cho nhãn node."""
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[`*]", "", text).strip()


def parse_readme() -> list[dict]:
    """Đọc các nhóm trong phần Mục lục của README: [{name, files: [(file, prio)]}]."""
    groups, cur, in_toc = [], None, False
    for line in (ROOT / "README.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_toc = line.strip() == "## Mục lục"
            continue
        if not in_toc:
            continue
        if line.startswith("### "):
            cur = {"name": line[4:].strip(), "files": []}
            groups.append(cur)
        m = re.match(r"\|\s*\[([0-9]{2}-[^\]]+\.md)\]\([^)]*\)\s*\|[^|]*\|\s*([^|]*)\|", line)
        if m and cur is not None:
            cur["files"].append((m.group(1), plain(m.group(2))))
    return groups


def parse_file(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    title = plain(re.sub(r"^#\s*\d+\.\s*", "", lines[0]))
    node = {"label": title, "kind": "file", "file": path.name, "children": []}
    stage = module = None
    section = None  # why | learn | check | None
    in_part1 = False
    questions = 0
    for line in lines:
        if line.startswith("## "):
            in_part1 = line.startswith("## Phần 1")
            section = None
            continue
        if re.match(r"^\*\*\d+\.\s", line):
            questions += 1
        if not in_part1:
            continue
        if line.startswith("### "):
            stage = plain(line[4:])
            module = None
            continue
        if line.startswith("#### "):
            level = next((e for e in "🟢🟡🔴" if stage and e in stage), "")
            module = {"label": plain(line[5:]), "kind": "module", "file": path.name,
                      "level": level, "stage": stage or "",
                      "why": "", "checks": [], "children": []}
            node["children"].append(module)
            section = None
            continue
        if module is None:
            continue
        s = line.strip()
        if s.startswith("**Vì sao cần học:**"):
            section = "why"
            module["why"] = s[len("**Vì sao cần học:**"):].strip()
            continue
        if s == "**Học gì**":
            section = "learn"
            continue
        if s == "**Nắm chắc khi**":
            section = "check"
            continue
        if s.startswith("**") and s.endswith("**"):
            section = None
            continue
        if section == "why":
            if s:
                module["why"] += " " + s
            else:
                section = None
        elif section == "learn":
            m = re.match(r"^\*([^*].*?)\*$", s)
            if m:
                module["children"].append({"label": plain(m.group(1)), "kind": "topic", "children": []})
        elif section == "check":
            m = re.match(r"^- \[[ x]\]\s+(.*)", s)
            if m:
                module["checks"].append(inline_md(m.group(1)))
    for mod in node["children"]:
        mod["why"] = inline_md(mod["why"].strip())
    node["questions"] = questions
    kpath = ROOT / "kien-thuc" / path.name
    node["knowledge"] = f"kien-thuc/{path.name}" if kpath.exists() else ""
    for mod in node["children"]:
        mod["knowledge"] = node["knowledge"]
    return node


def build() -> dict:
    root = {"label": "Ôn phỏng vấn Backend (senior, PHP)", "kind": "root", "children": []}
    for g in parse_readme():
        gnode = {"label": g["name"], "kind": "group", "children": []}
        for fname, prio in g["files"]:
            f = parse_file(ROOT / fname)
            f["prio"] = prio
            gnode["children"].append(f)
        root["children"].append(gnode)
    return root


TEMPLATE = r"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mindmap ôn phỏng vấn</title>
<style>
:root {
  --bg: #fbfaf7; --panel: #ffffff; --text: #1f2328; --muted: #6b7078; --line: #d8d4cc;
  --accent: #b4532a; --hl: #fff1b8; --border: #e6e2da; --shadow: 0 6px 24px rgba(0,0,0,.08);
  --b0: #b4532a; --b1: #2f6f9f; --b2: #4d7c3a; --b3: #8a4f9e; --b4: #a8741a; --b5: #2e7d7a; --b6: #9c3d54; --b7: #5b6472;
  --lv1: #3f9a4a; --lv2: #d9a21b; --lv3: #d0493f;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #16181c; --panel: #1f2227; --text: #e6e6e3; --muted: #9aa0a8; --line: #3a3e45;
    --accent: #e0835a; --hl: #5a4a12; --border: #30343b; --shadow: 0 6px 24px rgba(0,0,0,.4);
    --b0: #e0835a; --b1: #6aa8d8; --b2: #8cbf72; --b3: #c08fd4; --b4: #d9a948; --b5: #5fb8b3; --b6: #d77a92; --b7: #9aa3b2;
  }
}
:root[data-theme="dark"] {
  --bg: #16181c; --panel: #1f2227; --text: #e6e6e3; --muted: #9aa0a8; --line: #3a3e45;
  --accent: #e0835a; --hl: #5a4a12; --border: #30343b; --shadow: 0 6px 24px rgba(0,0,0,.4);
  --b0: #e0835a; --b1: #6aa8d8; --b2: #8cbf72; --b3: #c08fd4; --b4: #d9a948; --b5: #5fb8b3; --b6: #d77a92; --b7: #9aa3b2;
}
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; overflow: hidden; background: var(--bg); color: var(--text);
  font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
header { position: fixed; top: 0; left: 0; right: 0; z-index: 3; padding: 10px 16px 8px;
  background: var(--bg); border-bottom: 1px solid var(--border); }
.row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
header h1 { font-size: 15px; margin: 0 8px 0 0; font-weight: 650; }
.stats { color: var(--muted); font-size: 12px; margin-right: auto; }
.search { position: relative; }
input[type=search] { font: inherit; padding: 6px 10px; border: 1px solid var(--border); border-radius: 8px;
  background: var(--panel); color: var(--text); width: 240px; max-width: 100%; }
#results { position: absolute; top: 36px; right: 0; width: min(440px, calc(100vw - 32px)); max-height: 60vh; overflow: auto;
  background: var(--panel); border: 1px solid var(--border); border-radius: 10px; box-shadow: var(--shadow); display: none; z-index: 5; }
#results.open { display: block; }
#results button { display: block; width: 100%; text-align: left; border: 0; border-bottom: 1px solid var(--border);
  border-radius: 0; padding: 8px 12px; background: none; }
#results button:hover, #results button:focus { background: var(--bg); }
#results small { display: block; color: var(--muted); font-size: 11px; }
button { font: inherit; font-size: 13px; padding: 6px 10px; border: 1px solid var(--border); border-radius: 8px;
  background: var(--panel); color: var(--text); cursor: pointer; }
button:hover { border-color: var(--accent); }
#crumbs { margin-top: 8px; font-size: 13px; color: var(--muted); display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
#crumbs button { border: 0; background: none; padding: 2px 4px; color: var(--accent); font-size: 13px; }
#crumbs button:last-child { color: var(--text); font-weight: 600; cursor: default; }
#crumbs .sep { color: var(--muted); }
#crumbs .hint { margin-left: auto; font-size: 12px; }
#stage { position: fixed; left: 0; right: 0; bottom: 0; }
svg { width: 100%; height: 100%; display: block; }
#view.enter { animation: enter .28s ease-out; transform-origin: center; transform-box: fill-box; }
@keyframes enter { from { opacity: 0; transform: scale(.94); } to { opacity: 1; transform: none; } }
@media (prefers-reduced-motion: reduce) { #view.enter { animation: none; } }
.link { fill: none; stroke-width: 1.4; opacity: .5; }
.n { cursor: pointer; }
.n text { fill: var(--text); }
.n .muted { fill: var(--muted); }
.n:hover text, .n:focus text { fill: var(--accent); }
.n:focus { outline: none; }
.n:focus-visible .pill, .n:focus-visible .dot { stroke-width: 3; }
.pill { fill: var(--panel); stroke-width: 1.5; }
.center .pill { stroke-width: 2.5; }
.dot { stroke-width: 2; fill: var(--bg); }
.dot.has { fill: currentColor; }
.leafdot { fill: currentColor; opacity: .7; }
#panel { position: fixed; z-index: 4; right: 16px; bottom: 16px; width: min(420px, calc(100vw - 32px));
  background: var(--panel); border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow);
  padding: 16px 18px; overflow: auto; display: none; }
#panel.open { display: block; }
#panel h2 { font-size: 16px; margin: 0 28px 4px 0; }
#panel .crumb { color: var(--muted); font-size: 12px; margin-bottom: 12px; }
#panel h3 { font-size: 12px; margin: 16px 0 6px; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .03em; }
#panel .close { position: absolute; top: 10px; right: 10px; border: 0; background: none; font-size: 20px; line-height: 1; padding: 4px 8px; }
#panel ul { padding-left: 18px; margin: 0; }
#panel li { margin: 4px 0; }
#panel label { display: flex; gap: 8px; align-items: flex-start; margin: 6px 0; cursor: pointer; }
#panel input[type=checkbox] { margin-top: 3px; accent-color: var(--accent); }
#panel code { font-size: 12px; background: var(--bg); border: 1px solid var(--border); border-radius: 4px; padding: 0 4px; }
#panel a { color: var(--accent); }
.progress { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; margin: 6px 0 2px; }
.progress > div { height: 100%; background: var(--accent); }
@media (max-width: 640px) {
  header h1, .stats { width: 100%; margin: 0; }
  .search, input[type=search] { flex: 1 1 100%; width: 100%; }
  #crumbs .hint { display: none; }
  #panel { left: 16px; right: 16px; width: auto; height: 50vh; }
}
</style>
</head>
<body>
<header>
  <div class="row">
    <h1>Mindmap ôn phỏng vấn Backend</h1>
    <span class="stats" id="stats"></span>
    <div class="search">
      <input type="search" id="q" placeholder="Tìm chủ đề… (gõ không dấu cũng được)" aria-label="Tìm chủ đề" autocomplete="off">
      <div id="results" role="listbox"></div>
    </div>
    <button id="theme" title="Đổi giao diện sáng/tối" aria-label="Đổi giao diện sáng/tối">◐</button>
  </div>
  <nav id="crumbs" aria-label="Vị trí hiện tại"></nav>
</header>
<div id="stage"><svg id="svg" role="img" aria-label="Mindmap"><g id="view"></g></svg></div>
<aside id="panel" aria-live="polite"></aside>
<script>
const DATA = __DATA__;
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
};

// Chuẩn bị cây: cha, màu nhánh (theo nhóm).
(function prep(n, parent, branch) {
  n.parent = parent; n.branch = branch;
  n.children.forEach((c, i) => prep(c, n, n.kind === "root" ? i % 8 : branch));
})(DATA, null, 0);
const all = [];
(function walk(n) { all.push(n); n.children.forEach(walk); })(DATA);
const modules = all.filter(n => n.kind === "module");

function keyOf(m) { return "mm:" + m.file + ":" + m.label; }
function doneCount(m) { const s = store.get(keyOf(m), []); return m.checks.filter((_, i) => s[i]).length; }
function progressOf(n) {
  let done = 0, total = 0;
  (function w(x) { if (x.kind === "module") { done += doneCount(x); total += x.checks.length; } x.children.forEach(w); })(n);
  return [done, total];
}
function stats() {
  const [done, total] = progressOf(DATA);
  document.getElementById("stats").textContent = `${modules.length} module · ${done}/${total} tiêu chí đã nắm chắc`;
}

// Đo và cắt chữ.
const ctx = document.createElement("canvas").getContext("2d");
const FAMILY = " -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif";
function width(s, font) { ctx.font = font + FAMILY; return ctx.measureText(s).width; }
function clip(s, font, max) {
  if (width(s, font) <= max) return s;
  let lo = 0, hi = s.length;
  while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (width(s.slice(0, mid) + "…", font) <= max) lo = mid; else hi = mid - 1; }
  return s.slice(0, lo).trimEnd() + "…";
}
function wrap(s, font, max, lines) {
  const words = s.split(" "), out = [];
  let cur = "";
  for (const w of words) {
    const t = cur ? cur + " " + w : w;
    if (width(t, font) <= max || !cur) cur = t; else { out.push(cur); cur = w; }
  }
  if (cur) out.push(cur);
  if (out.length > lines) { const rest = out.slice(lines - 1).join(" "); out.length = lines - 1; out.push(clip(rest, font, max)); }
  return out.map(l => clip(l, font, max));
}

function labelOf(n) { return n.kind === "module" && n.level ? n.level + " " + n.label : n.label; }
function badgeOf(n) {
  if (n.kind === "module" && n.checks.length) return doneCount(n) + "/" + n.checks.length;
  if (n.kind === "file" || n.kind === "group") { const [d, t] = progressOf(n); return t ? d + "/" + t : ""; }
  return "";
}

const NS = "http://www.w3.org/2000/svg";
function el(tag, attrs, parent, text) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (text !== undefined) e.textContent = text;
  if (parent) parent.appendChild(e);
  return e;
}

const svg = document.getElementById("svg"), view = document.getElementById("view");
const stageEl = document.getElementById("stage"), panel = document.getElementById("panel");
let focus = DATA;

// Chọn bố cục: một vòng (các con) hoặc hai vòng (con + cháu) nếu vừa chỗ.
function plan(n, W) {
  const c = n.children, gc = c.flatMap(x => x.children);
  const two = W >= 900 && c.length <= 10 && gc.length > 0 && gc.length <= 40 && n.kind !== "module";
  return {inner: two ? c : null, outer: two ? gc : c};
}

function render() {
  const header = document.querySelector("header").offsetHeight;
  stageEl.style.top = header + "px";
  const open = panel.classList.contains("open"), wide = innerWidth > 640;
  const side = open && wide ? panel.offsetWidth + 32 : 0, below = open && !wide ? panel.offsetHeight + 16 : 0;
  const W = innerWidth - side, H = innerHeight - header - below;
  panel.style.top = (header + 12) + "px";
  view.textContent = "";
  const {inner, outer} = plan(focus, W);
  const FO = "12.5px", FI = "600 13px", FC = "700 15px";

  // Độ dài nhãn vòng ngoài: hai vòng thì nhãn ngắn hơn để chừa chỗ cho vòng trong.
  const maxL = inner ? 180 : 250;
  const outerText = outer.map(n => clip(n.label, FO, maxL));
  const badges = outer.map(badgeOf);
  const L = Math.max(60, ...outer.map((n, i) => width(outerText[i], FO) + (badges[i] ? width(badges[i], "11px") + 6 : 0))) + 16;

  // Elip vừa màn hình; nếu quá dày thì phóng to hệ toạ độ (chữ nhỏ lại) thay vì chồng chữ.
  let rx = Math.max(120, W / 2 - L - 20), ry = Math.max(90, H / 2 - L - 10);
  const per = Math.PI * (3 * (rx + ry) - Math.sqrt((3 * rx + ry) * (rx + 3 * ry)));
  const need = outer.length * 17;
  let s = 1;
  if (per < need) { s = need / per; rx *= s; ry *= s; }
  const vw = Math.max(W, 2 * (rx + L + 20)), vh = Math.max(H, 2 * (ry + L + 10));
  svg.setAttribute("viewBox", `${-vw / 2} ${-vh / 2} ${vw} ${vh}`);
  stageEl.style.right = side + "px";
  stageEl.style.bottom = below + "px";

  // Góc: mỗi node vòng ngoài một khe; con không có cháu vẫn giữ một khe.
  const slots = inner ? inner.reduce((a, c) => a + Math.max(3, c.children.length), 0) : outer.length;
  const step = 2 * Math.PI / Math.max(slots, 1), start = -Math.PI / 2 + (slots > 1 ? step / 2 : 0);
  const pos = (a, kx, ky) => [kx * Math.cos(a), ky * Math.sin(a)];
  const color = n => `var(--b${n.branch})`;
  const gl = el("g", {}, view), gn = el("g", {}, view);

  const place = [];
  if (inner) {
    let slot = 0;
    inner.forEach(c => {
      const k = Math.max(3, c.children.length), m = c.children.length;
      const a0 = start + slot * step + (k - Math.max(m, 1)) * step / 2;
      c._a = a0 + (Math.max(m, 1) - 1) * step / 2;
      c.children.forEach((g, j) => { g._a = a0 + j * step; });
      slot += k;
    });
  } else outer.forEach((n, i) => { n._a = start + i * step; });

  const r1x = rx * 0.6, r1y = ry * 0.6;
  // Đường nối.
  if (inner) {
    inner.forEach(c => {
      const [x, y] = pos(c._a, r1x, r1y);
      el("path", {class: "link", d: `M0,0 L${x},${y}`, stroke: color(c)}, gl);
      c.children.forEach(g => {
        const [gx, gy] = pos(g._a, rx, ry), [cx, cy] = pos(g._a, (r1x + rx) / 2, (r1y + ry) / 2);
        el("path", {class: "link", d: `M${x},${y} Q${cx},${cy} ${gx},${gy}`, stroke: color(g)}, gl);
      });
    });
  } else outer.forEach(n => {
    const [x, y] = pos(n._a, rx, ry);
    el("path", {class: "link", d: `M0,0 L${x},${y}`, stroke: color(n)}, gl);
  });

  // Vòng ngoài: nhãn xoay theo hướng toả ra, nửa trái lật lại cho dễ đọc.
  outer.forEach((n, i) => {
    const [x, y] = pos(n._a, rx, ry);
    const deg = Math.atan2(ry * Math.sin(n._a), rx * Math.cos(n._a)) * 180 / Math.PI;
    const left = Math.cos(n._a) < 0;
    const g = node(n, gn, `translate(${x},${y})`);
    const lv = {"🟢": "var(--lv1)", "🟡": "var(--lv2)", "🔴": "var(--lv3)"}[n.level];
    el("circle", {class: "dot" + (n.children.length ? " has" : ""), r: n.kind === "module" ? 5.5 : n.children.length ? 5 : 3.5,
      stroke: color(n), style: `color:${lv || color(n)}`}, g);
    const horiz = !inner && outer.length <= 12;
    const t = el("text", {transform: horiz ? "" : `rotate(${left ? deg + 180 : deg})`, x: left ? -10 : 10, "dominant-baseline": "middle",
      "text-anchor": left ? "end" : "start", "font-size": 12.5}, g);
    el("tspan", {}, t, outerText[i]);
    if (badges[i]) el("tspan", {class: "muted", "font-size": 11, dx: 6}, t, badges[i]);
  });

  // Vòng trong: nhãn nằm ngang trong khung bo góc.
  if (inner) inner.forEach(c => {
    const [x, y] = pos(c._a, r1x, r1y);
    const lines = wrap(c.label, FI, 120, 2);
    pill(node(c, gn, `translate(${x},${y})`), lines, FI, 13, color(c), badgeOf(c));
  });

  // Tâm.
  const cg = node(focus, gn, "translate(0,0)", true);
  const cl = wrap(labelOf(focus), FC, 170, 3);
  pill(cg, cl, FC, 15, color(focus), focus.kind === "root" ? "" : badgeOf(focus), true);
  if (focus.parent) el("title", {}, cg, "Bấm để lùi lại: " + focus.parent.label);

  view.classList.remove("enter"); void view.getBBox(); view.classList.add("enter");
  crumbs();
}

function pill(g, lines, font, size, stroke, badge, isCenter) {
  const lh = size * 1.3;
  const btxt = badge ? badge + " tiêu chí" : "";
  const w = Math.max(...lines.map(l => width(l, font)), btxt ? width(btxt, "11px") : 0) + 24;
  const h = lines.length * lh + (badge ? 16 : 0) + 14;
  el("rect", {class: "pill", x: -w / 2, y: -h / 2, width: w, height: h, rx: isCenter ? h / 2.4 : 10, stroke}, g);
  const t = el("text", {"text-anchor": "middle", "font-size": size, "font-weight": isCenter ? 700 : 600}, g);
  const y0 = -h / 2 + 7 + lh * 0.8;
  lines.forEach((l, i) => el("tspan", {x: 0, y: y0 + i * lh}, t, l));
  if (badge) el("tspan", {x: 0, y: y0 + lines.length * lh + 2, class: "muted", "font-size": 11, "font-weight": 400}, t, btxt);
}

function node(n, parent, transform, isCenter) {
  const g = el("g", {class: "n" + (isCenter ? " center" : ""), transform, tabindex: 0, role: "button", "aria-label": n.label}, parent);
  el("title", {}, g, n.label);
  const act = () => isCenter ? up() : open(n);
  g.addEventListener("click", e => { e.stopPropagation(); act(); });
  g.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); act(); } });
  return g;
}

function open(n) {
  if (n.kind === "topic") { setFocus(n.parent); return; }
  setFocus(n);
}
function up() { if (focus.parent) setFocus(focus.parent); }
function setFocus(n) {
  focus = n;
  if (n.kind === "module") showPanel(n); else panel.classList.remove("open");
  render();
  try { history.replaceState(null, "", "#" + encodeURIComponent(pathOf(n).map(x => x.label).slice(1).join("/"))); } catch (e) {}
}
function pathOf(n) { const p = []; for (let x = n; x; x = x.parent) p.unshift(x); return p; }

function crumbs() {
  const nav = document.getElementById("crumbs");
  nav.textContent = "";
  pathOf(focus).forEach((n, i, arr) => {
    if (i) { const s = document.createElement("span"); s.className = "sep"; s.textContent = "›"; nav.appendChild(s); }
    const b = document.createElement("button");
    b.textContent = n.kind === "root" ? "Tất cả" : labelOf(n);
    if (i < arr.length - 1) b.onclick = () => setFocus(n); else b.setAttribute("aria-current", "page");
    nav.appendChild(b);
  });
  const hint = document.createElement("span"); hint.className = "hint";
  hint.textContent = (focus.kind === "file" ? "Chấm: 🟢 nền · 🟡 làm chủ · 🔴 senior · " : "")
    + (focus.parent ? "Bấm vào tâm hoặc Esc để lùi lại" : "Bấm vào một nhánh để đi sâu");
  nav.appendChild(hint);
}

function esc(s) { return s.replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c])); }
function showPanel(m) {
  const saved = store.get(keyOf(m), []);
  const done = doneCount(m), total = m.checks.length;
  panel.innerHTML = `
    <button class="close" aria-label="Đóng">×</button>
    <h2>${esc(labelOf(m))}</h2>
    <div class="crumb">${esc(pathOf(m).slice(1, -1).map(x => x.label).concat(m.stage ? [m.stage] : []).join(" › "))}</div>
    ${m.why ? `<h3>Vì sao cần học</h3><p>${m.why}</p>` : ""}
    ${m.children.length ? `<h3>Nhóm kiến thức</h3><ul>${m.children.map(c => `<li>${esc(c.label)}</li>`).join("")}</ul>` : ""}
    ${total ? `<h3>Nắm chắc khi (${done}/${total})</h3>
      <div class="progress"><div style="width:${done / total * 100}%"></div></div>
      ${m.checks.map((c, i) => `<label><input type="checkbox" data-i="${i}" ${saved[i] ? "checked" : ""}><span>${c}</span></label>`).join("")}` : ""}
    <h3>Học chi tiết</h3>
    <p><a href="${encodeURI(m.file)}" target="_blank" rel="noopener">Mở plan ${esc(m.file)}</a>, tìm module “${esc(m.label)}”.</p>
    ${m.knowledge ? `<p><a href="${encodeURI(m.knowledge)}" target="_blank" rel="noopener">📖 Mở bài đọc kiến thức</a>, mục “${esc(m.label)}”.</p>` : ""}`;
  panel.classList.add("open");
  panel.querySelector(".close").onclick = () => { panel.classList.remove("open"); render(); };
  panel.querySelectorAll("input[type=checkbox]").forEach(cb => cb.onchange = () => {
    const s = store.get(keyOf(m), []); s[+cb.dataset.i] = cb.checked; store.set(keyOf(m), s);
    stats(); showPanel(m); render();
  });
}

// Tìm kiếm: danh sách kết quả, bấm để nhảy tới.
function norm(s) { return s.normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase(); }
const q = document.getElementById("q"), results = document.getElementById("results");
q.addEventListener("input", () => {
  const term = norm(q.value.trim());
  results.textContent = "";
  if (!term) { results.classList.remove("open"); return; }
  const hits = all.filter(n => n.kind !== "root" && norm(n.label).includes(term)).slice(0, 30);
  if (!hits.length) { const d = document.createElement("div"); d.style.padding = "10px 12px"; d.textContent = "Không tìm thấy"; results.appendChild(d); }
  hits.forEach(n => {
    const b = document.createElement("button");
    b.innerHTML = `${esc(labelOf(n))}<small>${esc(pathOf(n).slice(1, -1).map(x => x.label).join(" › "))}</small>`;
    b.onclick = () => { results.classList.remove("open"); q.value = ""; open(n); };
    results.appendChild(b);
  });
  results.classList.add("open");
});
document.addEventListener("click", e => { if (!e.target.closest(".search")) results.classList.remove("open"); });
document.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    if (results.classList.contains("open")) { results.classList.remove("open"); return; }
    if (document.activeElement !== q) up();
  }
});

// Theme sáng/tối, nhớ lựa chọn.
const themeSaved = store.get("mm:theme", null);
if (themeSaved) document.documentElement.dataset.theme = themeSaved;
document.getElementById("theme").onclick = () => {
  const dark = document.documentElement.dataset.theme
    ? document.documentElement.dataset.theme === "dark"
    : matchMedia("(prefers-color-scheme: dark)").matches;
  const next = dark ? "light" : "dark";
  document.documentElement.dataset.theme = next; store.set("mm:theme", next);
};

// Mở lại đúng chỗ đang xem nếu URL có #đường/dẫn.
(function restore() {
  try {
    const parts = decodeURIComponent(location.hash.slice(1)).split("/").filter(Boolean);
    let n = DATA;
    for (const p of parts) { const c = n.children.find(x => x.label === p); if (!c) break; n = c; }
    focus = n; if (n.kind === "module") showPanel(n);
  } catch (e) {}
})();

stats(); render();
let rt; addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(render, 120); });
</script>
</body>
</html>
"""


def main() -> None:
    data = build()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    OUT.write_text(TEMPLATE.replace("__DATA__", payload), encoding="utf-8")
    mods = sum(len(f["children"]) for g in data["children"] for f in g["children"])
    print(f"Đã ghi {OUT.relative_to(ROOT.parent)} ({mods} module)")


if __name__ == "__main__":
    main()
