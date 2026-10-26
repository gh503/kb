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
    """去掉围栏代码块与行内代码：示例里的链接不该被当成真链接。"""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def check_links():
    bad = []
    total = 0
    for f in DOCS.rglob("*.md"):
        txt = strip_code(f.read_text(encoding="utf-8"))
        targets = [m.group(1) for m in re.finditer(r"\]\(([^)]+)\)", txt)]
        # kb-chain 用 HTML 锚点，markdown 正则看不到，单独抓一遍
        targets += [m.group(1) for m in re.finditer(r'<a href="([^"]+)"', txt)]
        for raw in targets:
            target = raw.split("#")[0].strip()
            if not target or target.startswith(("http", "mailto:", "/")):
                continue
            total += 1
            p = f.parent / target
            if not p.exists():
                bad.append((str(f.relative_to(ROOT)), target))
    return total, bad


def check_raw_anchors():
    """原始 HTML 里的 .md 锚点不会被 MkDocs 重写，构建后必 404。"""
    bad = []
    for f in DOCS.rglob("*.md"):
        txt = strip_code(f.read_text(encoding="utf-8"))   # 代码块里的示例不算
        for m in re.finditer(r'<a\s+href="([^"]+\.md)(?:#[^"]*)?"', txt):
            bad.append((str(f.relative_to(ROOT)), m.group(1)))
        # 链表块必须带 markdown 属性，否则里面的链接同样不会被重写
        for m in re.finditer(r'<div class="kb-chain"(?![^>]*markdown)', txt):
            bad.append((str(f.relative_to(ROOT)), "kb-chain 缺少 markdown 属性"))
    return bad


def entries(subject_dir: pathlib.Path):
    return sorted(p for p in subject_dir.glob("*.md") if p.name != "index.md")


def index_rows(index_path: pathlib.Path):
    """只数「## 条目」到下一个同级标题之间的表格行。"""
    txt = index_path.read_text(encoding="utf-8")
    m = re.search(r"^## 条目\n(.*?)(?=^## |\Z)", txt, flags=re.S | re.M)
    if not m:
        return []
    return re.findall(r"^\| \[([^\]]+)\]\(([^)]+\.md)\)", m.group(1), flags=re.M)


def check_nav():
    """每个学科的 index.md 必须出现在 mkdocs.yml 的 nav 里，否则线上没有侧栏入口。"""
    nav = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    nav_paths = set(re.findall(r"-\s+(\S+\.md)", nav))
    missing = []
    for idx in DOCS.rglob("index.md"):
        rel = idx.relative_to(DOCS).as_posix()
        if rel == "index.md":          # 首页在 nav 里写作 index.md
            continue
        if "/" not in rel:             # 域首页（基础/index.md 等）也要求进 nav
            pass
        if rel.startswith("关于/") or rel.startswith("订阅/"):
            continue
        if rel not in nav_paths:
            missing.append(rel)
    return missing


def main():
    problems = []

    total, bad = check_links()
    print(f"内部链接 {total} 条，断链 {len(bad)} 条")
    for f, t in bad:
        problems.append(f"断链: {f} -> {t}")

    for f, t in check_raw_anchors():
        problems.append(f"原始 HTML 锚点指向 .md（构建后 404）: {f} -> {t}")

    missing_nav = check_nav()
    print(f"nav 未收录的 index: {len(missing_nav)} 个")
    for m in missing_nav:
        problems.append(f"nav 缺入口: {m}")

    chains = defaultdict(list)
    for subject in (
        "历史", "政治", "哲学", "文化",
        "运营", "单位经济", "项目管理", "产品的",
        "钱", "健康", "事务", "家", "娱乐",
        "开发", "测试", "运维", "设计", "计算机", "算法与数据结构", "操作系统", "数据库", "概率论", "线性代数", "高等数学",
        "TCP-IP", "网络通信", "安全", "软件安全", "主机安全", "硬件安全",
        "AI", "机器人",
        "通用基础", "数学", "逻辑",
    ):
        if subject in ("运营", "单位经济", "项目管理", "产品的"):
            d = DOCS / "商业" / subject
        elif subject in ("钱", "健康", "事务", "家", "娱乐"):
            d = DOCS / "日常" / subject
        elif subject in ("开发", "测试", "运维", "设计", "计算机", "算法与数据结构", "操作系统", "数据库"):
            d = DOCS / "工程" / subject
        elif subject in ("TCP-IP", "网络通信", "安全", "软件安全", "主机安全", "硬件安全"):
            d = DOCS / "网络" / subject
        elif subject in ("AI", "机器人"):
            d = DOCS / "智能" / subject
        elif subject in ("通用基础", "数学", "逻辑", "概率论", "线性代数", "高等数学"):
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
            "开发", "测试", "运维", "设计", "计算机", "算法与数据结构", "操作系统", "数据库",
            "TCP-IP", "网络通信", "安全", "软件安全", "主机安全", "硬件安全", "AI", "机器人",
            "通用基础", "数学", "逻辑", "概率论", "线性代数", "高等数学",
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
        "开发", "测试", "运维", "设计", "计算机", "算法与数据结构", "操作系统", "数据库", "概率论", "线性代数", "高等数学", "高等数学",
        "TCP-IP", "网络通信", "安全", "软件安全", "主机安全", "硬件安全", "AI", "机器人",
        "通用基础", "数学", "逻辑",
    )
    by_subject = defaultdict(set)
    for (subject, name) in chains:
        by_subject[subject].add(name)
    for subject in TECH_SUBJECTS:
        n = len(by_subject.get(subject, ()))
        if n and not 2 <= n <= 4:
            problems.append(f"{subject}: 链 {n} 条，不在 2–4 条区间")
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
