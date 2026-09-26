#!/usr/bin/env python3
"""Sinh interview/references.md: tổng hợp mọi tài liệu tham khảo trong các file interview/NN-*.md.

Nguồn dữ liệu:
- Bảng "Tài liệu nền" ở đầu mỗi file (tài liệu chính của chủ đề).
- Mục "Đọc" của từng module (tài liệu cho từng phần kiến thức).

Chỉ dùng standard library. Chạy lại mỗi khi sửa file bài học:
    python3 tools/build_references.py
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_mindmap import ROOT, parse_readme, plain  # noqa: E402

OUT = ROOT / "references.md"
LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")


def cells(row: str) -> list[str]:
    """Tách một dòng bảng markdown thành các ô (bỏ qua dấu | nằm trong backtick)."""
    parts, cur, code = [], "", False
    for ch in row.strip().strip("|"):
        if ch == "`":
            code = not code
        if ch == "|" and not code:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    parts.append(cur.strip())
    return parts


def parse(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    title = plain(re.sub(r"^#\s*\d+\.\s*", "", lines[0]))
    core, modules = [], []
    section, module = None, None
    for line in lines:
        if line.startswith("## "):
            section = "core" if line.strip() == "## Tài liệu nền" else ("part1" if line.startswith("## Phần 1") else None)
            continue
        if section == "core" and line.startswith("|") and not re.match(r"^\|\s*-", line):
            c = cells(line)
            if len(c) >= 3 and c[0] != "Tài liệu":
                core.append({"name": c[0], "kind": c[1], "use": c[2]})
        if section != "part1":
            continue
        if line.startswith("#### "):
            module = {"label": plain(line[5:]), "links": [], "notes": []}
            modules.append(module)
            reading = False
            continue
        if module is None:
            continue
        s = line.strip()
        if s == "**Đọc**":
            reading = True
            continue
        if s.startswith("**") and s.endswith("**"):
            reading = False
            continue
        if reading and s.startswith("- "):
            found = LINK.findall(s)
            if found:
                module["links"].append(s[2:])
            else:
                module["notes"].append(s[2:])
    return {"file": path.name, "title": title, "core": core, "modules": modules}


def is_book(kind: str) -> bool:
    """Cột "Loại" có chữ "Sách" đứng riêng (không phải "chính sách", "danh sách", "sách online")."""
    k = kind.lower()
    return bool(re.search(r"(^|[+/]\s*)sách", k)) and "online" not in k


def book_title(name: str) -> str:
    m = re.search(r"\*([^*]+)\*", name)
    return plain(m.group(1) if m else name)


def main() -> None:
    groups = parse_readme()
    docs = {f: parse(ROOT / f) for g in groups for f, _ in g["files"]}
    order = [f for g in groups for f, _ in g["files"]]
    short = {f: f"[{f[:2]}]({f})" for f in order}

    # Mỗi URL được những file nào dẫn tới (bỏ phần #anchor để gom trang giống nhau).
    cited = defaultdict(set)
    exact = defaultdict(list)  # base -> [(text, url)] để chọn tên hiển thị
    for f in order:
        d = docs[f]
        texts = [r["name"] for r in d["core"]] + [l for m in d["modules"] for l in m["links"]]
        for t in texts:
            for text, url in LINK.findall(t):
                base = url.split("#")[0].rstrip("/")
                cited[base].add(f)
                exact[base].append((plain(text), url))

    def title_of(base: str) -> tuple[str, str]:
        """Tên hiển thị cho một trang. Nếu trang được dẫn tới qua nhiều anchor khác nhau thì
        dùng tên trang (không anchor) để khỏi mang nhầm tên của một mục con."""
        entries = exact[base]
        plain_hits = [t for t, u in entries if "#" not in u]
        if plain_hits:
            return max(set(plain_hits), key=plain_hits.count), base
        if len({u for _, u in entries}) == 1:
            return entries[0][0], entries[0][1]
        return base.split("://", 1)[1], base

    total_links = sum(len(LINK.findall(l)) for d in docs.values() for m in d["modules"] for l in m["links"])
    out = []
    w = out.append
    w("# Tài liệu tham khảo")
    w("")
    w("> [← Mục lục](README.md) · File này được **sinh tự động** từ các file bài học. Đừng sửa tay;")
    w("> sửa ở file bài học rồi chạy `python3 tools/build_references.py`.")
    w("")
    w(f"Tổng hợp {len(cited)} trang tài liệu từ {len(order)} chủ đề. Dùng file này theo thứ tự:")
    w("")
    w("1. **[Tài liệu nền theo chủ đề](#1-tài-liệu-nền-theo-chủ-đề)**: 4–8 nguồn chính của mỗi chủ đề. Bắt đầu từ đây.")
    w("2. **[Sách](#2-sách)**: danh sách sách, gom từ mọi chủ đề.")
    w("3. **[Được dẫn nhiều nhất](#3-được-dẫn-nhiều-nhất)**: nguồn xuất hiện ở nhiều chủ đề, thường đáng đọc kỹ.")
    w("4. **[Chỉ mục theo module](#4-chỉ-mục-theo-module)**: toàn bộ tài liệu ở mục \"Đọc\" của từng module "
      f"({total_links} link), để tra khi đang học một module cụ thể.")
    w("")
    w("Số trong ngoặc vuông, ví dụ [03], là file bài học dẫn tới tài liệu đó.")
    w("")
    w("---")
    w("")

    # 1. Tài liệu nền.
    w("## 1. Tài liệu nền theo chủ đề")
    w("")
    for g in groups:
        w(f"### {g['name']}")
        w("")
        for f, _ in g["files"]:
            d = docs[f]
            w(f"#### [{f[:2]}. {d['title']}]({f})")
            w("")
            w("| Tài liệu | Loại | Dùng cho |")
            w("|---|---|---|")
            for r in d["core"]:
                w(f"| {r['name']} | {r['kind']} | {r['use']} |")
            w("")

    # 2. Sách.
    w("## 2. Sách")
    w("")
    w("Gom từ bảng tài liệu nền của mọi chủ đề. Sách online miễn phí nằm ở mục 1.")
    w("")
    books = {}
    for f in order:
        for r in docs[f]["core"]:
            if is_book(r["kind"]):
                key = book_title(r["name"]).lower()
                b = books.setdefault(key, {"name": r["name"], "files": [], "use": r["use"]})
                b["files"].append(f)
    w("| Sách | Chủ đề | Dùng cho |")
    w("|---|---|---|")
    for b in sorted(books.values(), key=lambda x: book_title(x["name"]).lower()):
        w(f"| {b['name']} | {' '.join(short[f] for f in sorted(b['files']))} | {b['use']} |")
    w("")

    # 3. Được dẫn nhiều nhất.
    w("## 3. Được dẫn nhiều nhất")
    w("")
    w("Các trang được từ 3 chủ đề trở lên dẫn tới.")
    w("")
    top = sorted(((len(v), k) for k, v in cited.items() if len(v) >= 3), key=lambda x: (-x[0], title_of(x[1])[0].lower()))
    w("| Tài liệu | Số chủ đề | Chủ đề |")
    w("|---|---|---|")
    for n, base in top:
        text, url = title_of(base)
        w(f"| [{text}]({url}) | {n} | {' '.join(short[f] for f in sorted(cited[base]))} |")
    w("")

    # 4. Chỉ mục theo module.
    w("## 4. Chỉ mục theo module")
    w("")
    w("Bấm vào từng chủ đề để mở danh sách.")
    w("")
    for g in groups:
        w(f"### {g['name']}")
        w("")
        for f, _ in g["files"]:
            d = docs[f]
            n = sum(len(LINK.findall(l)) for m in d["modules"] for l in m["links"])
            w("<details>")
            w(f"<summary><strong>{f[:2]}. {d['title']}</strong> ({len(d['modules'])} module, {n} link)</summary>")
            w("")
            w(f"Học chi tiết: [{f}]({f})")
            w("")
            for m in d["modules"]:
                if not m["links"] and not m["notes"]:
                    continue
                w(f"**{m['label']}**")
                w("")
                for l in m["links"] + m["notes"]:
                    w(f"- {l}")
                w("")
            w("</details>")
            w("")

    OUT.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(f"Đã ghi {OUT.relative_to(ROOT.parent)}: {len(cited)} trang, {len(books)} sách, {len(top)} nguồn dẫn nhiều")


if __name__ == "__main__":
    main()
