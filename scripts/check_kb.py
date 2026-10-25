#!/usr/bin/env python3
"""KB 体检：断链、索引行、学段表头、事实与判断、链完整性。

用法：python3 scripts/check_kb.py
退出码 0 = 全部通过；1 = 有问题。
"""
import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
LEVELS = ["小学–初中", "初中–高中", "高中–大学", "大学–研究生"]


def strip_code(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.S)


def check_links():
    bad = []
    total = 0
    for f in DOCS.rglob("*.md"):
        txt = strip_code(f.read_text(encoding="utf-8"))
        for m in re.finditer(r"\]\(([^)]+)\)", txt):
            target = m.group(1).split("#")[0].strip()
            if not target or target.startswith(("http", "mailto:")):
                continue
            total += 1
            p = DOCS / target.lstrip("/") if target.startswith("/") else f.parent / target
            if not p.exists():
                bad.append((str(f.relative_to(ROOT)), target))
    return total, bad


def entries(subject_dir: pathlib.Path):
    return sorted(p for p in subject_dir.glob("*.md") if p.name != "index.md")


def index_rows(index_path: pathlib.Path):
    """只数「## 条目」到下一个同级标题之间的表格行。"""
    txt = index_path.read_text(encoding="utf-8")
    m = re.search(r"^## 条目\n(.*?)(?=^## |\Z)", txt, flags=re.S | re.M)
    if not m:
        return []
    return re.findall(r"^\| \[([^\]]+)\]\(([^)]+\.md)\)", m.group(1), flags=re.M)


def main():
    problems = []

    total, bad = check_links()
    print(f"内部链接 {total} 条，断链 {len(bad)} 条")
    for f, t in bad:
        problems.append(f"断链: {f} -> {t}")

    chains = defaultdict(list)
    for subject in (
        "历史", "政治", "哲学", "文化",
        "运营", "单位经济", "项目管理", "产品的",
        "钱", "健康", "事务", "家", "娱乐",
        "开发", "测试", "运维", "设计",
        "TCP-IP", "网络通信", "安全",
        "AI", "机器人",
        "通用基础", "数学", "逻辑",
    ):
        if subject in ("运营", "单位经济", "项目管理", "产品的"):
            d = DOCS / "商业" / subject
        elif subject in ("钱", "健康", "事务", "家", "娱乐"):
            d = DOCS / "日常" / subject
        elif subject in ("开发", "测试", "运维", "设计"):
            d = DOCS / "工程" / subject
        elif subject in ("TCP-IP", "网络通信", "安全"):
            d = DOCS / "网络" / subject
        elif subject in ("AI", "机器人"):
            d = DOCS / "智能" / subject
        elif subject in ("通用基础", "数学", "逻辑"):
            d = DOCS / "基础" / subject
        else:
            d = DOCS / "人文" / subject
        if not d.exists():
            continue
        es = entries(d)
        idx = d / "index.md"
        rows = index_rows(idx) if idx.exists() else []
        linked = {name for _, name in rows} if rows else set()
        print(f"{subject}: 条目 {len(es)} 个，索引行 {len(rows)} 条")
        if rows and len(rows) != len(es):
            problems.append(f"{subject}: 索引行 {len(rows)} != 条目 {len(es)}")
        for e in es:
            txt = e.read_text(encoding="utf-8")
            if "> **学段" in txt:
                if "## 事实与判断" not in txt:
                    problems.append(f"{subject}/{e.name}: 缺事实与判断小节")
            elif "> **深度" in txt:
                if "## 证据强度" not in txt:
                    problems.append(f"{subject}/{e.name}: 缺证据强度小节")
                if "## 数字与阈值" not in txt:
                    problems.append(f"{subject}/{e.name}: 缺数字与阈值小节")
                ev = re.search(r"## 证据强度\n(.*?)(?=\n## |\Z)", txt, flags=re.S)
                if ev and not re.search(
                    r"\*\*(实测|公开经验|公开研究|推断|未验证|公式|方法|会计口径|经验区间|经验建议|框架|建议值)\*\*",
                    ev.group(1),
                ):
                    problems.append(f"{subject}/{e.name}: 证据强度没有标签")
            else:
                problems.append(f"{subject}/{e.name}: 缺表头（学段或深度）")
            if rows and e.name not in linked:
                problems.append(f"{subject}/{e.name}: 索引里没有这一行")
            m = re.search(r"> \*\*(?:学段|深度)\*\* ([^｜]+)｜.*?链\*\* (.+)", txt)
            if m:
                chains[(subject, m.group(2).strip())].append((m.group(1).strip(), e.stem))

    # 索引页不得有重复小节（曾出现两个「## 链」）
    for idx in DOCS.rglob("index.md"):
        heads = re.findall(r"^## (.+)$", idx.read_text(encoding="utf-8"), flags=re.M)
        dup = {h for h in heads if heads.count(h) > 1}
        for h in sorted(dup):
            problems.append(f"{idx.relative_to(DOCS)}: 小节「## {h}」重复 {heads.count(h)} 次")

    print(f"\n链 {len(chains)} 条")
    for (subject, name), pages in chains.items():
        levels = [lv for lv, _ in pages]
        if len(pages) < 3:
            problems.append(f"链 {subject}/{name}: 只有 {len(pages)} 页")
        if subject in (
            "运营", "单位经济", "项目管理", "产品的",
            "钱", "健康", "事务", "家", "娱乐",
            "开发", "测试", "运维", "设计",
            "TCP-IP", "网络通信", "安全", "AI", "机器人",
            "通用基础", "数学", "逻辑",
        ):
            # 商业与日常域按深度分层，不按学段；只检查深度是否齐全
            missing_d = [d for d in ("入门", "实操", "取舍") if d not in levels]
            if missing_d:
                print(f"  {subject}/{name}: {len(pages)} 页，缺深度 {', '.join(missing_d)}")
            continue
        missing = [lv for lv in LEVELS if lv not in levels]
        if missing:
            print(f"  {subject}/{name}: {len(pages)} 页，缺 {', '.join(missing)}")

    # 新四域：每学科 2–3 条链，每链恰好 4 页
    TECH_SUBJECTS = (
        "开发", "测试", "运维", "设计",
        "TCP-IP", "网络通信", "安全", "AI", "机器人",
        "通用基础", "数学", "逻辑",
    )
    by_subject = defaultdict(set)
    for (subject, name) in chains:
        by_subject[subject].add(name)
    for subject in TECH_SUBJECTS:
        n = len(by_subject.get(subject, ()))
        if n and not 2 <= n <= 3:
            problems.append(f"{subject}: 链 {n} 条，不在 2–3 条区间")
    for (subject, name), pages in chains.items():
        if subject in TECH_SUBJECTS and len(pages) != 4:
            problems.append(f"链 {subject}/{name}: {len(pages)} 页，应为 4 页")

    if problems:
        print(f"\n发现 {len(problems)} 个问题：")
        for p in problems:
            print("  -", p)
        return 1
    print("\n全部通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
