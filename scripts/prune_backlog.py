#!/usr/bin/env python3
"""把「链上还没写的」里已经写成页面的选题删掉。

判据：选题（去掉括号补充、空格、标点）与同目录下某个页面的文件名互相包含。
写成脚本而不是手删，是因为每补一批链都要重跑一次。
"""
from __future__ import annotations

import difflib
import pathlib
import re
import sys

# 换了说法、或者已经被别的学科写掉的选题，显式登记在这里，
# 免得模糊匹配把「看起来像」的条目误删。
ALIASES = {
    ("事务", "租房到期押金不退怎么办"): "租房押金不退怎么办",
    ("事务", "身份证丢了要马上做什么"): "身份证丢了先做什么",
    ("家", "空调外机与晾衣架的固定"): "空调外机与晾衣架怎么固定",
    ("机器人", "多机协同时的冲突处理"): "多机协同的冲突处理",
    ("数学", "指数增长与复利"): "增长率与复利",
    ("逻辑", "量词与范围（所有/有些/没有）"): "量词的顺序",
    ("逻辑", "论证的强度分级"): "论证强度怎么比",
    ("高等数学", "约束优化的 KKT 条件"): "约束优化与KKT条件",
    ("软件安全", "密钥与凭据怎么管"): "见 ../安全/密钥管理 与 ../主机安全/密钥与凭据放在哪",
}

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
                raw = b.group(1)
                t = norm(raw)
                if (subj.name, raw) in ALIASES:
                    removed += 1
                    continue
                hit = [s for s in stems if t == s or (len(t) >= 4 and (t in s or s in t))]
                if not hit and len(t) >= 5:
                    hit = difflib.get_close_matches(t, stems, n=1, cutoff=0.75)
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
