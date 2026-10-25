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
MARK = '<div class="kb-chain">'
LABEL = '<span class="kb-chain__label">本链四页</span>'


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
            parts.append(f'<span class="kb-chain__now">{label}</span>')
        else:
            parts.append(f'<a href="{target}">{label}</a>')
    return MARK + LABEL + '<span class="kb-chain__sep">/</span>' + '<span class="kb-chain__sep">·</span>'.join(parts) + "</div>"


def clean(text: str) -> str:
    """去掉任意一种旧导航：引用行版本与 div 版本。"""
    text = re.sub(r"(?m)^> \*\*本链四页\*\*.*\n", "", text)
    # 旧格式残留的孤立引用符号
    text = re.sub(r"(?m)^>\s*\n(?=\n?<div class=\"kb-chain\">)", "", text)
    text = re.sub(r"(?m)^>\s*\n(?=\n## )", "", text)
    text = re.sub(r"(?m)^>\s*\n(?=\n*$)", "", text)
    text = re.sub(r"(?ms)^>\s*\n(?=<div class=\"kb-chain\">)", "", text)
    text = re.sub(r"(?s)<div class=\"kb-chain\">.*?</div>\n?", "", text)
    return text


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
                    text = clean(page.read_text(encoding="utf-8"))
                    block = build(names, target)
                    lines = text.split("\n")
                    hdr = next(
                        (i for i, ln in enumerate(lines) if ln.startswith("> **深度**")),
                        None,
                    )
                    if hdr is None:
                        continue
                    lines.insert(hdr + 1, "")
                    lines.insert(hdr + 2, block)
                    page.write_text("\n".join(lines), encoding="utf-8")
                    touched += 1
    print(f"处理 {touched} 个条目页")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())