#!/usr/bin/env python3
"""把「链上还没写的」里已经写成页面的选题删掉。

判据：选题（去掉括号补充、空格、标点）与同目录下某个页面的文件名互相包含。
写成脚本而不是手删，是因为每补一批链都要重跑一次。
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "docs"


def norm(s: str) -> str:
    s = re.sub(r"[（(].*?[）)]", "", s)
    return re.sub(r"[\s，。、：:；;“”\"'？?！!·\-—]+", "", s)


def main() -> int:
    removed = 0
    for idx in ROOT.rglob("index.md"):
        subj = idx.parent
        stems = [norm(p.stem) for p in subj.glob("*.md") if p.name != "index.md"]
        if not stems:
            continue
        text = idx.read_text(encoding="utf-8")
        m = re.search(r"^## 链上还没写的\n(.*?)(?=\n## |\Z)", text, re.S | re.M)
        if not m:
            continue
        keep = []
        for line in m.group(1).splitlines():
            b = re.match(r"^- (.+)$", line.strip())
            if b:
                t = norm(b.group(1))
                hit = [s for s in stems if t == s or (len(t) >= 4 and (t in s or s in t))]
                if hit:
                    removed += 1
                    continue
            keep.append(line)
        new = "\n".join(keep)
        new = re.sub(r"\n{3,}", "\n\n", new)
        text = text[: m.start(1)] + new + text[m.end(1):]
        idx.write_text(text, encoding="utf-8")
    print(f"移除已写选题 {removed} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
