#!/usr/bin/env python3
"""生成两个导航页：全站索引、待写清单。

用法：python3 scripts/gen_nav_pages.py
幂等：重复运行只会重写这两个文件，其余内容不动。
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DOMAINS = ["自然", "人文", "商业", "日常", "工程", "网络", "智能", "基础"]

ROW_LINK = re.compile(r"^\| \[([^\]]+)\]\(([^)]+\.md)\) \| (.+?) \| (.+?) \| (.+?) \|$")


def section(text: str, name: str) -> str:
    m = re.search(rf"^## {name}\n(.*?)(?=\n## |\Z)", text, flags=re.S | re.M)
    return m.group(1) if m else ""


def parse_subject(idx: pathlib.Path):
    """返回 (entries, chains, backlog)。entries: [(title, file, one_line, depth)]"""
    text = idx.read_text(encoding="utf-8")
    entries, chains = [], []
    for line in section(text, "条目").splitlines():
        m = ROW_LINK.match(line.strip())
        if m:
            entries.append((m.group(1), m.group(2), m.group(3).strip(), m.group(4).strip()))
    for line in section(text, "链").splitlines():
        if "→" in line and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                chains.append(cells[1])
    backlog = [
        ln[2:].strip()
        for ln in section(text, "链上还没写的").splitlines()
        if ln.strip().startswith("- ")
    ]
    return entries, chains, backlog


def collect():
    data = {}
    for dom in DOMAINS:
        d = DOCS / dom
        if not d.is_dir():
            continue
        subjects = []
        for sub in sorted(p for p in d.iterdir() if p.is_dir()):
            idx = sub / "index.md"
            if not idx.exists():
                continue
            entries, chains, backlog = parse_subject(idx)
            if not entries:
                continue
            subjects.append((sub.name, entries, chains, backlog))
        if subjects:
            data[dom] = subjects
    return data


def gen_index(data) -> str:
    total = sum(len(e) for subs in data.values() for _, e, _, _ in subs)
    nchain = sum(len(c) for subs in data.values() for _, _, c, _ in subs)
    out = [
        "# 全站索引",
        "",
        f"> **{total} 条**，按域 → 学科分组。**这一页由 `scripts/gen_nav_pages.py` 生成，不要手改。**",
        ">",
        f"> 共 {len(data)} 个域、{sum(len(s) for s in data.values())} 个学科、{nchain} 条链。",
        "> 想按问题链路读，去各学科页；想按关键词找，用右上角搜索。",
        "",
        "## 按域看",
        "",
        "| 域 | 学科 | 条目 |",
        "| --- | --- | --- |",
    ]
    for dom, subs in data.items():
        names = " · ".join(f"[{n}](../{dom}/{n}/index.md)" for n, _, _, _ in subs)
        n = sum(len(e) for _, e, _, _ in subs)
        out.append(f"| [{dom}](../{dom}/index.md) | {names} | {n} |")
    out.append("")
    for dom, subs in data.items():
        out.append(f"## {dom}")
        out.append("")
        for name, entries, chains, _ in subs:
            out.append(f"### [{name}](../{dom}/{name}/index.md)")
            out.append("")
            if chains:
                out.append("链（4 页一链）：")
                out.append("")
                for c in chains:
                    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", c)
                    out.append(f"- {plain}")
                out.append("")
            out.append("| 条目 | 一句话 | 深度 |")
            out.append("| --- | --- | --- |")
            for title, file, one, depth in entries:
                out.append(f"| [{title}](../{dom}/{name}/{file}) | {one} | {depth} |")
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def gen_backlog(data) -> str:
    rows = []
    for dom, subs in data.items():
        for name, entries, chains, backlog in subs:
            for item in backlog:
                rows.append((dom, name, item))
    out = [
        "# 待写清单",
        "",
        f"> 各学科页「链上还没写的」汇总，共 **{len(rows)} 条**。**由 `scripts/gen_nav_pages.py` 生成，不要手改。**",
        ">",
        "> 这些是候选选题，不是承诺。开写前先判断：有没有可写的数字或判据？",
        "> 没有的话，先补素材，不要先建页。",
        "",
    ]
    cur = None
    for dom, name, item in rows:
        if dom != cur:
            out.append(f"## {dom}")
            out.append("")
            cur = dom
        out.append(f"- **{name}**：{item}")
    out.append("")
    out.append("## 怎么用这一页")
    out.append("")
    out.append("```text")
    out.append("1. 按域挑一批（同一域连着写，体例与数字风格更容易一致）")
    out.append("2. 每条先确认：能不能给出至少 3 个可代入的数字/判据")
    out.append("3. 能 → 按 4 页一链写；不能 → 回去补素材，别硬写")
    out.append("4. 写完后从学科页删掉对应条目，这一页下次生成会自动少一条")
    out.append("```")
    return "\n".join(out).rstrip() + "\n"


def main():
    data = collect()
    (DOCS / "关于" / "全站索引.md").write_text(gen_index(data), encoding="utf-8")
    (DOCS / "关于" / "待写清单.md").write_text(gen_backlog(data), encoding="utf-8")
    total = sum(len(e) for subs in data.values() for _, e, _, _ in subs)
    backlog = sum(len(b) for subs in data.values() for _, _, _, b in subs)
    print(f"全站索引: {total} 条")
    print(f"待写清单: {backlog} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())