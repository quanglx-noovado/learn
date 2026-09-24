#!/usr/bin/env python3
"""Tải một trang tutorial dev.java về và lưu thành markdown thô (tiếng Anh).

Dùng để giữ bản gốc tiếng Anh bên cạnh bản dịch tiếng Việt.
Chỉ dùng standard library — không cần cài thêm gì.

Cách dùng:
    python3 tools/fetch_devjava.py <url> <file-dich-ra.md>
    python3 tools/fetch_devjava.py --all java/03-collections/en   # tải cả series collections

Ghi chú kỹ thuật: dev.java bọc code trong custom element <java-playground> và
<readonly-code-editor>, phần code thật nằm trong HTML comment bên trong <snippet>.
Vì HTMLParser bỏ qua comment theo cách khó xử lý, ta rút các block đó ra trước
bằng regex, thay bằng placeholder, rồi ghép lại thành fenced code block ở cuối.
"""

from __future__ import annotations

import html
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://dev.java"

# Series Collections Framework: (số thứ tự khớp bản dịch tiếng Việt, slug trên dev.java)
COLLECTIONS_SERIES = [
    ("01", "intro"),
    ("02", "organization"),
    ("03", "collection-interface"),
    ("04", "iterating"),
    ("05", "lists"),
    ("06", "sets"),
    ("07", "factory-methods"),
    ("08", "stacks-queues"),
]

BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "div"}


def tai_trang(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8 (personal study archive)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def cat_div_can_bang(h: str, start: int) -> str:
    """Cắt đúng một thẻ <div> kể cả khi bên trong có div lồng nhau."""
    i = h.index(">", start) + 1
    depth, pos = 1, i
    for m in re.finditer(r"</?div\b", h[i:]):
        depth += 1 if m.group(0) == "<div" else -1
        if depth == 0:
            pos = i + m.start()
            break
    return h[i:pos]


def dedent_snippet(code: str) -> str:
    """Bỏ phần thụt lề do template HTML chèn vào, giữ nguyên thụt lề thật của code."""
    lines = code.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""

    def indent(l: str) -> int:
        return len(l) - len(l.lstrip())

    ne = [l for l in lines if l.strip()]
    # readonly-code-editor thường thụt dòng ĐẦU theo template (32 space) trong khi
    # các dòng sau không thụt -> kéo dòng đầu về ngang mức các dòng sau.
    if len(ne) > 1:
        con_lai = min(indent(l) for l in ne[1:])
        if indent(ne[0]) > con_lai:
            k = lines.index(ne[0])
            lines[k] = " " * con_lai + lines[k].lstrip()
    chung = min(indent(l) for l in lines if l.strip())
    return "\n".join(l[chung:] if l.strip() else "" for l in lines)


def rut_code_blocks(h: str):
    """Thay mỗi code block bằng placeholder @@CODE_n@@, trả về (html_mới, danh_sách_code)."""
    blocks = []

    def thay(m: re.Match) -> str:
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        lang_attr = re.search(r'lang-type="([^"]*)"', attrs)
        lang = lang_attr.group(1) if lang_attr else "java"
        if lang == "text":
            lang = ""  # output của chương trình, không phải code
        cmt = re.search(r"<!--(.*?)-->", inner, re.S)
        code = dedent_snippet(cmt.group(1)) if cmt else ""
        if "&lt;" in code or "&amp;" in code:
            code = html.unescape(code)
        blocks.append((lang, code))
        return f"@@CODE_{len(blocks) - 1}@@"

    h = re.sub(
        r"<(java-playground|readonly-code-editor|code-editor)([^>]*)>(.*?)</\1>",
        thay, h, flags=re.S,
    )
    return h, blocks


class SangMarkdown(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self.buf: list[str] = []
        self.list_stack: list[list] = []   # mỗi phần tử: ["ul"|"ol", số_đếm]
        self.heading = None
        self.link_stack: list[tuple] = []   # (href, vị_trí_trong_buf) — hỗ trợ <a><code>X</code></a>
        self.trong_blockquote = False
        self.bang = None                   # (rows, hàng_hiện_tại) khi đang ở trong <table>
        self.o_cell = False

    # --- helper ---
    def _xuong_block(self, text: str | None = None):
        noi_dung = text if text is not None else "".join(self.buf)
        self.buf = []
        noi_dung = re.sub(r"[ \t]*\n[ \t]*", "\n", noi_dung)
        noi_dung = re.sub(r"[^\S\n]+", " ", noi_dung).strip()
        if noi_dung:
            self.blocks.append(noi_dung)

    def _inline(self, s: str):
        if self.o_cell or not self.bang:
            self.buf.append(s)

    def _phat_li(self):
        """Đẩy nội dung <li> đang gom trong buf ra thành một list item."""
        noi_dung = re.sub(r"\s+", " ", "".join(self.buf)).strip()
        self.buf = []
        if not noi_dung or not self.list_stack:
            return
        muc = self.list_stack[-1]
        muc[1] += 1
        dau = "- " if muc[0] == "ul" else f"{muc[1]}. "
        self.blocks.append("  " * (len(self.list_stack) - 1) + dau + noi_dung)

    # --- tag mở ---
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._xuong_block()
            self.heading = int(tag[1])
        elif tag == "p":
            self._xuong_block()
        elif tag in ("ul", "ol"):
            # list con nằm trong <li>: phát <li> cha ra trước để nó không mất dấu "-"
            if self.list_stack:
                self._phat_li()
            else:
                self._xuong_block()
            self.list_stack.append([tag, 0])
        elif tag == "li":
            self._xuong_block()
        elif tag == "a":
            self.link_stack.append((a.get("href", ""), len(self.buf)))
        elif tag in ("code", "tt"):
            self._inline("`")
        elif tag in ("strong", "b"):
            self._inline("**")
        elif tag in ("em", "i"):
            self._inline("*")
        elif tag == "br":
            self._inline("  \n")
        elif tag == "img":
            src = a.get("src", "")
            if src.startswith("/"):
                src = BASE + src
            self._xuong_block()
            self.blocks.append(f"![{a.get('alt', '')}]({src})")
        elif tag == "blockquote":
            self._xuong_block()
            self.trong_blockquote = True
        elif tag == "table":
            self._xuong_block()
            self.bang = ([], None)
        elif tag == "tr" and self.bang:
            self.bang = (self.bang[0], [])
        elif tag in ("td", "th") and self.bang:
            self.o_cell = True
            self.buf = []
        elif tag == "hr":
            self._xuong_block()
            self.blocks.append("---")

    # --- tag đóng ---
    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            noi_dung = "".join(self.buf).strip()
            self.buf = []
            if noi_dung:
                self.blocks.append("#" * self.heading + " " + re.sub(r"\s+", " ", noi_dung))
            self.heading = None
        elif tag == "p":
            self._xuong_block()
        elif tag in ("ul", "ol"):
            self._xuong_block()
            if self.list_stack:
                self.list_stack.pop()
        elif tag == "li":
            self._phat_li()   # buf rỗng nếu đã phát ở lúc mở list con -> tự bỏ qua
        elif tag == "a":
            if self.link_stack:
                href, vi_tri = self.link_stack.pop()
                text = "".join(self.buf[vi_tri:]).strip()
                del self.buf[vi_tri:]
                if text:
                    url = href if href.startswith(("http", "#")) else BASE + href
                    self._inline(f"[{text}]({url})")
        elif tag in ("code", "tt"):
            self._inline("`")
        elif tag in ("strong", "b"):
            self._inline("**")
        elif tag in ("em", "i"):
            self._inline("*")
        elif tag == "blockquote":
            noi_dung = "".join(self.buf).strip()
            self.buf = []
            if noi_dung:
                self.blocks.append("> " + re.sub(r"\s+", " ", noi_dung))
            self.trong_blockquote = False
        elif tag in ("td", "th") and self.bang:
            rows, cur = self.bang
            if cur is not None:
                cur.append(re.sub(r"\s+", " ", "".join(self.buf)).strip())
            self.buf = []
            self.o_cell = False
        elif tag == "tr" and self.bang:
            rows, cur = self.bang
            if cur:
                rows.append(cur)
            self.bang = (rows, None)
        elif tag == "table" and self.bang:
            rows = self.bang[0]
            self.bang = None
            if rows:
                w = max(len(r) for r in rows)
                rows = [r + [""] * (w - len(r)) for r in rows]
                dong = ["| " + " | ".join(rows[0]) + " |",
                        "|" + "|".join([" --- "] * w) + "|"]
                dong += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                self.blocks.append("\n".join(dong))

    def handle_data(self, data):
        self._inline(data)


def chuyen_doi(url: str) -> str:
    h = tai_trang(url)

    tieu_de = "Untitled"
    i = h.find('<div id="content" class="col-9"')
    if i < 0:
        raise SystemExit(f"không tìm thấy vùng nội dung trong {url}")
    m = list(re.finditer(r"<h1>(.*?)</h1>", h[:i], re.S))
    if m:
        tieu_de = html.unescape(re.sub(r"\s+", " ", m[-1].group(1))).strip()

    ngay = re.search(r'<span class="date">([^<]+)</span>', h)

    than = cat_div_can_bang(h, i)
    than, code_blocks = rut_code_blocks(than)

    p = SangMarkdown()
    p.feed(than)
    p._xuong_block()

    ra = [f"# {tieu_de}", ""]
    ra.append(f"> Source: <{url}> — dev.java" + (f" (last update: {ngay.group(1)})" if ngay else ""))
    ra.append("> Raw English content, kept for reference alongside the Vietnamese translation.")
    ra.append("")

    for b in p.blocks:
        km = re.fullmatch(r"@@CODE_(\d+)@@", b)
        if km:
            lang, code = code_blocks[int(km.group(1))]
            ra += [f"```{lang}", code, "```", ""]
        else:
            ra += [b, ""]

    # gộp các item của cùng một list thành khối liền nhau (bỏ dòng trống giữa chúng)
    text = "\n".join(ra)
    text = re.sub(r"(?m)^((?:  )*(?:- |\d+\. ).*)\n\n(?=(?:  )*(?:- |\d+\. ))", r"\1\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n"


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "--all":
        thu_muc = Path(argv[2])
        thu_muc.mkdir(parents=True, exist_ok=True)
        for so, slug in COLLECTIONS_SERIES:
            url = f"{BASE}/learn/api/collections-framework/{slug}/"
            dich = thu_muc / f"{so}-{slug}.md"
            dich.write_text(chuyen_doi(url), encoding="utf-8")
            print(f"{dich}  ({dich.stat().st_size:,} bytes)")
        return 0
    if len(argv) == 3:
        Path(argv[2]).write_text(chuyen_doi(argv[1]), encoding="utf-8")
        print(f"{argv[2]} xong")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
