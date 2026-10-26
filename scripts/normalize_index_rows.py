#!/usr/bin/env python3
"""把游离在「条目」表之外的表格行收回到条目表末尾。

register_chain 早期版本会把新行追加到「## 链上还没写的」之前，
如果索引里中间还有「## 提醒」之类的段落，行就落到了正文里。
这个脚本做一次规范化，可重复运行。
"""
from __future__ import annotations

import pathlib
import re
import sys

ROW = re.compile(r"^\| \[[^\]]+\]\([^)]+\.md\) \| .+ \| .+ \|$")
HEAD = re.compile(r"^## ")


def fix(path: pathlib.Path) -> int:
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "## 条目")
    except StopIteration:
        return 0
    # 条目表：从 start 之后第一条以 | 开头的行开始，连续行都算表内
    t0 = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("|")), None)
    if t0 is None:
        return 0
    t1 = t0
    while t1 + 1 < len(lines) and lines[t1 + 1].startswith("|"):
        t1 += 1
    table = lines[t0 : t1 + 1]
    keep = lines[: t0] + table + lines[t1 + 1 :]
    stray = [(i, l) for i, l in enumerate(keep) if ROW.match(l) and not (t0 <= i <= t1)]
    if not stray:
        return 0
    rows = [l for _, l in stray]
    stray_idx = {i for i, _ in stray}
    out = [l for i, l in enumerate(keep) if i not in stray_idx]
    # 找到表尾（表可能因移除而位移，重新定位）
    start = next(i for i, l in enumerate(out) if l.strip() == "## 条目")
    t0 = next(i for i in range(start + 1, len(out)) if out[i].startswith("|"))
    t1 = t0
    while t1 + 1 < len(out) and out[t1 + 1].startswith("|"):
        t1 += 1
    out = out[: t1 + 1] + rows + out[t1 + 1 :]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(rows)


def main() -> int:
    n = 0
    for idx in pathlib.Path("docs").rglob("index.md"):
        k = fix(idx)
        if k:
            print(f"{idx}: 收回 {k} 行")
            n += k
    print("合计", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
