#!/usr/bin/env python3
"""给每个条目页加上「本链四页」导航行。

用法：python3 scripts/add_chain_nav.py
幂等：已有该行时原地更新，不重复插入。
范围：只处理工程/网络/智能/基础四域（其余四域按既定约定不动）。
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DOMAINS = ["工程", "网络", "智能", "基础"]
MARK = "> **本链四页**"


def chains_of(idx: pathlib.Path):
    """返回 [(链名, [页面文件名…])]，顺序按链表里的箭头顺序。"""
    text = idx.read_text(encoding="utf-8")
    m = re.search(r"^## 链\n(.*?)(?=\n## |\Z)", text, flags=re.S | re.M)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        if "→" not in line or not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        seen, names = set(), []
        for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+\.md)\)", cells[1]):
            if target not in seen:
                seen.add(target)
                names.append((label, target))
        if names:
            out.append(names)
    return out


def build(names, current: str) -> str:
    parts = []
    for label, target in names:
        if target == current:
            parts.append(f"**{label}**（当前页）")
        else:
            parts.append(f"[{label}]({target})")
    return MARK + "：" + " · ".join(parts)


def main():
    touched = 0
    for dom in DOMAINS:
        for sub in (DOCS / dom).iterdir():
            if not sub.is_dir():
                continue
            idx = sub / "index.md"
            if not idx.exists():
                continue
            for names in chains_of(idx):
                for _, target in names:
                    page = sub / target
                    if not page.exists():
                        continue
                    text = page.read_text(encoding="utf-8")
                    block = build(names, target)
                    if MARK in text:
                        text = re.sub(rf"^{re.escape(MARK)}.*$", block, text, count=1, flags=re.M)
                    else:
                        lines = text.split("\n")
                        hdr = next(
                            (i for i, ln in enumerate(lines) if ln.startswith("> **深度**")),
                            None,
                        )
                        if hdr is None:
                            continue
                        lines.insert(hdr + 1, ">")
                        lines.insert(hdr + 2, block)
                        text = "\n".join(lines)
                    page.write_text(text, encoding="utf-8")
                    touched += 1
    print(f"处理 {touched} 个条目页")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())