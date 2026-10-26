#!/usr/bin/env python3
"""把一条新链登记进学科索引：链表加一行、条目表加行、清掉表格里的空行。

用法：python3 scripts/register_chain.py <学科目录> <链名> <页1> <页2> <页3> <页4>
每条页写作 "文件名|一句话|深度"，文件名不含 .md。
"""
import pathlib
import sys

def main():
    d = pathlib.Path(sys.argv[1])
    chain = sys.argv[2]
    rows = []
    for spec in sys.argv[3:]:
        f, line, depth = spec.split("|")
        rows.append((f, line, depth))
    idx = d / "index.md"
    s = idx.read_text(encoding="utf-8")

    titles = [r[0] for r in rows]
    chain_row = "| [" + titles[0] + "](" + titles[0] + ".md) | " + \
        " → ".join(f"[{t}]({t}.md)" for t in titles) + " |"
    if chain_row in s:
        print("链表已有该行，跳过")
    else:
        head, rest = s.split("## 条目", 1)
        head = head.rstrip("\n") + "\n" + chain_row + "\n\n"
        s = head + "## 条目" + rest

    entries = "\n".join(f"| [{f}]({f}.md) | {line} | {depth} |" for f, line, depth in rows)
    seg = s.split("## 条目")[1].split("## 链上")[0]
    if f"| [{rows[0][0]}]({rows[0][0]}.md) | " in seg:
        print("条目表已有，跳过")
    else:
        # 直接插到「条目」表的最后一行之后；不能按章节切，
        # 否则中间若有「## 提醒」之类的段落，行会掉进正文里。
        lines = s.splitlines()
        start = next(i for i, l in enumerate(lines) if l.strip() == "## 条目")
        t0 = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("|"))
        t1 = t0
        while t1 + 1 < len(lines) and lines[t1 + 1].startswith("|"):
            t1 += 1
        lines = lines[: t1 + 1] + entries.splitlines() + lines[t1 + 1 :]
        s = "\n".join(lines) + "\n"

    # 清掉表内空行（曾导致表格被截成两张）
    for marker in ("## 链", "## 条目"):
        if marker in s:
            head, rest = s.split(marker, 1)
            body, tail = rest.split("\n## ", 1)
            body = body.replace("\n\n| [", "\n| [")
            s = head + marker + body + "\n## " + tail
    idx.write_text(s, encoding="utf-8")
    print("已登记", chain, "→", idx)

if __name__ == "__main__":
    main()
