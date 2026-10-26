#!/usr/bin/env python3
"""生成内联 SVG 图并插进页面。

用法：
  python3 scripts/gen_charts.py            # 把图写进页面的 <!-- kb-chart:名字 --> 标记处
  python3 scripts/gen_charts.py --list     # 只列出可用的图

设计约束：
  - 图是内联 SVG，用 currentColor 与 CSS 变量取色 → 深色模式自动跟着变
  - 不依赖 JS，不额外下载文件
  - 所有数据都来自本机实测或可直接计算的公式，图上标明数值
"""
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

INK = "currentColor"
ACCENT = "var(--kb-accent)"
WARN = "var(--kb-warn)"
GRID = "var(--kb-line)"
MUTED = "var(--kb-ink-mute)"

W, H = 720, 340
PAD_L, PAD_R, PAD_T, PAD_B = 62, 96, 34, 46


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=12, anchor="start", color=INK, weight="400", opacity=1):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
        f'fill="{color}" font-weight="{weight}" opacity="{opacity}" '
        f'font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">{esc(s)}</text>'
    )


def frame(title, xlab, ylab):
    out = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="none"/>']
    out.append(text(0, 14, title, size=13, weight="700"))
    out.append(text(W - 4, H - 8, xlab, size=11, anchor="end", color=MUTED))
    out.append(text(10, PAD_T - 12, ylab, size=11, color=MUTED))
    return out


def axes(xmin, xmax, ymin, ymax, xticks, yticks, xfmt=str, yfmt=str, logy=False):
    """画坐标轴、网格与刻度。logy=True 时 ymin/ymax 是原值，内部取 log10。"""
    out = []
    def sy(v):
        if logy:
            lo, hi = math.log10(ymin), math.log10(ymax)
            return PAD_T + (hi - math.log10(v)) / (hi - lo) * (H - PAD_T - PAD_B)
        return PAD_T + (ymax - v) / (ymax - ymin) * (H - PAD_T - PAD_B)
    def sx(v):
        return PAD_L + (v - xmin) / (xmax - xmin) * (W - PAD_L - PAD_R)

    for yv in yticks:
        y = sy(yv)
        out.append(f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{W-PAD_R}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        out.append(text(PAD_L - 8, y + 4, yfmt(yv), size=11, anchor="end", color=MUTED))
    out.append(f'<line x1="{PAD_L}" y1="{PAD_T}" x2="{PAD_L}" y2="{H-PAD_B}" stroke="{GRID}" stroke-width="1"/>')
    for xv in xticks:
        x = sx(xv)
        out.append(text(x, H - PAD_B + 18, xfmt(xv), size=11, anchor="middle", color=MUTED))
    return out, sx, sy


def polyline(points, color, width=2.2, dash=None, dots=True):
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out = [f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}"{d} stroke-linejoin="round" stroke-linecap="round"/>']
    if dots:
        for x, y in points:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{color}"/>')
    return out


def legend(items, x=None, y=None):
    x = PAD_L + 8 if x is None else x
    y = PAD_T + 8 if y is None else y
    # 右对齐放不下就把整块图例往左推，避免文字被画布裁掉
    need = max((30 + len(lbl) * 7.4 for lbl, _, _ in items), default=0)
    if x + need > W - 2:
        x = max(PAD_L + 4, W - 2 - need)
    out = []
    for i, (label, color, dash) in enumerate(items):
        yy = y + i * 18
        d = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<line x1="{x}" y1="{yy}" x2="{x+22}" y2="{yy}" stroke="{color}" stroke-width="2.4"{d}/>')
        out.append(text(x + 30, yy + 4, label, size=11, color=INK))
    return out


def note_text(x, y, note, size=11, color=None):
    """注释太长会超出画布，按宽度折成两行。"""
    color = MUTED if color is None else color
    limit = int((W - x - 8) / (size * 0.98))
    if len(note) <= limit:
        return [text(x, y, note, size=size, color=color)]
    mid = len(note) // 2
    # 在中间附近找一个标点断开
    cut = min(range(max(1, mid - 12), min(len(note) - 1, mid + 12)),
              key=lambda i: (0 if note[i] in "，。；：" else 1, abs(i - mid)))
    return [text(x, y - 13, note[:cut + 1], size=size, color=color),
            text(x, y, note[cut + 1:], size=size, color=color)]


def wrap(inner, caption):
    return (
        '<figure class="kb-figure">\n'
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(caption)}" '
        'xmlns="http://www.w3.org/2000/svg">\n' + "\n".join(inner) + "\n</svg>\n"
        f'<figcaption>{caption}</figcaption>\n</figure>'
    )


# ---------------------------------------------------------------- 通用构建器

def _fmt_default(v):
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    if abs(v) >= 1:
        return f"{v:g}"
    return f"{v:g}"


def col_chart(title, labels, series, unit, note="", logy=False, yticks=None, ymax=None,
              rotate=False):
    """竖向分组柱状图。series = [(名字, [值...], 颜色)]。"""
    inner = frame(title, "", unit)
    vals = [v for _, vs, _ in series for v in vs if v > 0]
    lo, hi = (min(vals), max(vals)) if vals else (1, 10)
    if ymax:
        hi = ymax
    if logy:
        lo = lo / 2
        hi = hi * 2
    else:
        lo = 0
        hi = hi * 1.15
    ticks = yticks or ([lo * 2 ** i for i in range(0, 8) if lo * 2 ** i <= hi][:5] if logy
                       else [hi * i / 4 for i in range(0, 5)])
    ax, sx, sy = axes(0, len(labels), lo, hi, [], ticks, yfmt=_fmt_default, logy=logy)
    inner += ax
    n = len(series)
    slot = (W - PAD_L - PAD_R) / max(1, len(labels))
    bw = min(46, slot * 0.62 / n)
    for si, (name, vs, color) in enumerate(series):
        for i, v in enumerate(vs):
            cx = PAD_L + slot * (i + 0.5) - (n * bw) / 2 + si * bw
            vv = v if (v > 0 or not logy) else lo
            y = sy(vv)
            h = max(1.0, (H - PAD_B) - y)
            inner.append(f'<rect x="{cx:.1f}" y="{y:.1f}" width="{bw-3:.1f}" height="{h:.1f}" rx="3" fill="{color}" opacity="0.85"/>')
            if v > 0:
                inner.append(text(cx + (bw - 3) / 2, y - 6, _fmt_default(v), size=10,
                                  anchor="middle", color=color, weight="700"))
    for i, lab in enumerate(labels):
        cx = PAD_L + slot * (i + 0.5)
        if rotate:
            inner.append(f'<text x="{cx:.1f}" y="{H-PAD_B+14}" font-size="10" text-anchor="end" fill="{MUTED}" transform="rotate(-28 {cx:.1f} {H-PAD_B+14})">{esc(lab)}</text>')
        else:
            inner.append(text(cx, H - PAD_B + 16, lab, size=11, anchor="middle", color=MUTED))
    if n > 1:
        inner += legend([(nm, c, None) for nm, _, c in series], x=W - PAD_R + 14, y=PAD_T + 10)
    if note:
        inner += note_text(PAD_L, H - 8, note)
    return wrap(inner, note or title)


def line_chart(title, xlab, ylab, xs, series, note="", logx=False, logy=False,
               xticks=None, yticks=None, xfmt=None, yfmt=None):
    """折线图。series = [(名字, [值...], 颜色, dash 或 None)]"""
    inner = frame(title, xlab, ylab)
    xmin, xmax = min(xs), max(xs)
    vals = [v for _, vs, _, _ in series for v in vs if v > 0]
    ymin, ymax = min(vals), max(vals)
    if logx:
        xmin, xmax = xmin / 1.5, xmax * 1.5
    if logy:
        ymin, ymax = ymin / 2, ymax * 2
    else:
        ymin, ymax = 0, ymax * 1.15
    xt = xticks or xs
    yt = yticks or ([ymin, ymax])
    xf = xfmt or (lambda v: f"{v:g}")
    yf = yfmt or _fmt_default
    ax, sx, sy = axes(xmin, xmax, ymin, ymax, xt, yt, xfmt=xf, yfmt=yf, logy=logy)
    inner += ax
    for name, vs, color, dash in series:
        pts = [(sx(x), sy(v)) for x, v in zip(xs, vs)]
        inner += polyline(pts, color, dash=dash)
    if len(series) > 1:
        inner += legend([(nm, c, d) for nm, _, c, d in series], x=W - PAD_R + 14, y=PAD_T + 10)
    if note:
        inner += note_text(PAD_L, H - 8, note)
    return wrap(inner, note or title)


def strip_chart(title, cols, rows, note=""):
    """状态条：每行一个对象，按列打分（0–3），用色块表示。适合「选型/状态」这类非数值比较。"""
    inner = frame(title, "", "")
    x0 = 150
    cw = (W - PAD_R - x0) / len(cols)
    y = PAD_T + 16
    for i, c in enumerate(cols):
        inner.append(text(x0 + cw * (i + 0.5), y - 4, c, size=11, anchor="middle", color=MUTED))
    y += 10
    for label, marks, comment in rows:
        inner.append(text(x0 - 10, y + 16, label, size=12, anchor="end", color=INK, weight="600"))
        for i, m in enumerate(marks):
            cx = x0 + cw * i + 6
            color = {3: ACCENT, 2: ACCENT, 1: GRID, 0: GRID}[m]
            op = {3: 0.9, 2: 0.5, 1: 0.6, 0: 0.25}[m]
            inner.append(f'<rect x="{cx:.1f}" y="{y}" width="{cw-12:.1f}" height="22" rx="4" fill="{color}" opacity="{op}"/>')
            if m == 3:
                inner.append(text(cx + (cw - 12) / 2, y + 15, "好", size=10, anchor="middle", color="var(--kb-paper)", weight="700"))
            elif m == 2:
                inner.append(text(cx + (cw - 12) / 2, y + 15, "中", size=10, anchor="middle", color=INK))
            elif m == 1:
                inner.append(text(cx + (cw - 12) / 2, y + 15, "差", size=10, anchor="middle", color=MUTED))
        if comment:
            inner.append(text(W - PAD_R + 4, y + 15, comment, size=10, color=MUTED))
        y += 30
    if note:
        inner += note_text(PAD_L, H - 8, note)
    return wrap(inner, note or title)


def hbar_chart(title, labels, values, unit, note="", logbar=True):
    """横向条形图（对数长度可选）。"""
    inner = frame(title, unit, "")
    x0, x1 = 200, W - 44
    y = PAD_T + 18
    usable = [v for v in values if v > 0]
    vmax = max(usable) if usable else 1
    floor = (min(usable) * 0.8) if (logbar and usable) else 0
    for label, v in zip(labels, values):
        if logbar:
            vv = v if v > 0 else floor
            frac = (math.log10(vv) - math.log10(floor)) / (math.log10(vmax) - math.log10(floor)) if vmax > floor else 0.5
        else:
            frac = v / vmax
        w = max(1.0, frac * (x1 - x0))
        inner.append(text(x0 - 10, y + 15, label, size=12, anchor="end", color=INK))
        inner.append(f'<rect x="{x0}" y="{y}" width="{w:.1f}" height="22" rx="4" fill="{ACCENT if v == max(usable) else WARN}" opacity="0.85"/>')
        val = f"{_fmt_default(v)} {unit}"
        if x0 + w + 8 + len(val) * 7.2 > W - 4:      # 右侧放不下就写进条里
            inner.append(text(x0 + w - 8, y + 15, val, size=12, anchor="end", color="var(--kb-paper)", weight="700"))
        else:
            inner.append(text(x0 + w + 8, y + 15, val, size=12, color=INK, weight="700"))
        y += 42
    if note:
        inner += note_text(x0, y + 6, note)
    return wrap(inner, note or title)


# ---------------------------------------------------------------- 图定义

def chart_growth():
    """复杂度增长曲线：log-log"""
    n_max, n_min = 1000, 1
    def curves():
        return {
            "O(1)": [1] * 6,
            "O(log n)": [math.log2(n) for n in (1, 4, 16, 64, 256, 1000)],
            "O(n)": [1, 4, 16, 64, 256, 1000],
            "O(n log n)": [max(1, n * math.log2(n)) for n in (1, 4, 16, 64, 256, 1000)],
            "O(n²)": [max(1, n * n) for n in (1, 4, 16, 64, 256, 1000)],
        }
    xs = [1, 4, 16, 64, 256, 1000]
    inner = frame("同样从 n=1 到 n=1000，五种复杂度各涨多少", "n（对数）", "操作次数（对数）")
    ax, sx, sy = axes(1, 1000, 1, 1e6, [1, 4, 16, 64, 256, 1000],
                      [1, 10, 100, 1e3, 1e4, 1e5, 1e6], xfmt=lambda v: str(int(v)),
                      yfmt=lambda v: f"{int(v):,}", logy=True)
    inner += ax
    colors = {"O(1)": MUTED, "O(log n)": ACCENT, "O(n)": ACCENT, "O(n log n)": WARN, "O(n²)": WARN}
    dashes = {"O(1)": "4 4", "O(log n)": None, "O(n)": None, "O(n log n)": None, "O(n²)": "6 4"}
    for name, ys in curves().items():
        pts = [(sx(x), sy(max(1, y))) for x, y in zip(xs, ys)]
        inner += polyline(pts, colors[name], dash=dashes[name], dots=name in ("O(n log n)", "O(n²)"))
    inner += legend([("O(1)", MUTED, "4 4"), ("O(log n)", ACCENT, None), ("O(n)", ACCENT, None),
                     ("O(n log n)", WARN, None), ("O(n²)", WARN, "6 4")], x=W - PAD_R + 14, y=PAD_T + 14)
    inner.append(text(sx(1000) - 6, sy(1e6) + 14, "n=1000 时差 100 万倍", size=11, anchor="end", color=WARN, weight="700"))
    return wrap(inner, "五种复杂度的增长曲线（纵轴为对数刻度）")


def chart_sort():
    ns = [500, 1000, 2000, 4000]
    builtin = [0.047, 0.111, 0.258, 0.544]
    bubble = [40.472, 99.551, 488.455, 1977.715]
    inner = frame("同一个排序任务：内置排序 vs 冒泡（本机实测）", "元素个数 n", "耗时 ms（对数）")
    ax, sx, sy = axes(400, 4200, 0.01, 3000, ns, [0.01, 0.1, 1, 10, 100, 1000, 3000],
                      xfmt=lambda v: str(int(v)), yfmt=lambda v: (f"{v:g}"), logy=True)
    inner += ax
    inner += polyline([(sx(n), sy(t)) for n, t in zip(ns, builtin)], ACCENT)
    inner += polyline([(sx(n), sy(t)) for n, t in zip(ns, bubble)], WARN)
    inner += legend([("内置 sorted（≈ ×2.2/翻倍）", ACCENT, None), ("冒泡（≈ ×4/翻倍）", WARN, None)],
                    x=W - PAD_R + 14, y=PAD_T + 14)
    inner.append(text(sx(4000) - 8, sy(1977.715) - 12, "1,977.7 ms", size=11, anchor="end", color=WARN, weight="700"))
    inner.append(text(sx(4000) - 8, sy(0.544) - 12, "0.544 ms", size=11, anchor="end", color=ACCENT, weight="700"))
    inner.append(text(sx(500) + 4, sy(40.472) - 12, "870×", size=11, color=MUTED))
    inner.append(text(sx(4000) - 60, sy(1977.715) + 26, "3,635×", size=11, color=WARN, weight="700"))
    return wrap(inner, "n 从 500 到 4000，倍数从 870 涨到 3635（Python 3.10.12，3 次中位数）")


def chart_quicksort():
    ns = [1000, 2000, 4000]
    naive = [77.8, 299.4, 928.4]
    good = [0.013, 0.020, 0.036]
    inner = frame("朴素快排遇到「本来就有序」的输入会退化", "元素个数 n", "耗时 ms（对数）")
    ax, sx, sy = axes(800, 4400, 0.008, 2000, ns, [0.01, 0.1, 1, 10, 100, 1000],
                      xfmt=lambda v: str(int(v)), yfmt=lambda v: f"{v:g}", logy=True)
    inner += ax
    inner += polyline([(sx(n), sy(t)) for n, t in zip(ns, naive)], WARN)
    inner += polyline([(sx(n), sy(t)) for n, t in zip(ns, good)], ACCENT)
    inner += legend([("朴素快排（取首元素为枢轴）", WARN, None), ("内置 sorted（Timsort）", ACCENT, None)],
                    x=W - PAD_R + 14, y=PAD_T + 14)
    inner.append(text(sx(4000) + 6, sy(928.4) + 4, "928 ms", size=11, color=WARN, weight="700"))
    inner.append(text(sx(4000) + 6, sy(0.036) + 4, "0.036 ms", size=11, color=ACCENT, weight="700"))
    inner.append(text(sx(1000), sy(77.8) - 14, "翻倍 ×3.8 → 接近二次增长", size=11, color=WARN))
    return wrap(inner, "有序输入下，朴素快排 4000 个元素要 0.93 秒，内置排序只要 0.036 毫秒")


def chart_search():
    ns = [10000, 100000, 1000000]
    lin = [7.679, 98.891, 1159.659]
    bin_ = [0.082, 0.151, 0.198]
    inner = frame("200 次查询：线性扫描 vs 二分查找", "元素个数 n（对数）", "耗时 ms（对数）")
    ax, sx, sy = axes(8000, 1_300_000, 0.05, 3000, ns, [0.05, 0.5, 5, 50, 500],
                      xfmt=lambda v: f"{int(v/1000)}k" if v < 1_000_000 else "1M", yfmt=lambda v: f"{v:g}", logy=True)
    inner += ax
    inner += polyline([(sx(n), sy(t)) for n, t in zip(ns, lin)], WARN)
    inner += polyline([(sx(n), sy(t)) for n, t in zip(ns, bin_)], ACCENT)
    inner += legend([("线性扫描 O(n)", WARN, None), ("二分查找 O(log n)", ACCENT, None)],
                    x=W - PAD_R + 14, y=PAD_T + 14)
    inner.append(text(sx(1_000_000) - 10, sy(1159.659) - 12, "1,159.7 ms", size=11, anchor="end", color=WARN, weight="700"))
    inner.append(text(sx(1_000_000) - 10, sy(0.198) - 12, "0.198 ms", size=11, anchor="end", color=ACCENT, weight="700"))
    inner.append(text(sx(1_000_000) - 10, sy(0.198) + 22, "5,866×", size=12, anchor="end", color=ACCENT, weight="700"))
    return wrap(inner, "n 每涨 10 倍，线性那一列也涨 10 倍，二分几乎不动")


def _bar_chart(title, labels, values, unit, logbar=True, note=""):
    """横向条形图，对数长度，适合展示「差两个数量级」的对比。"""
    inner = frame(title, unit, "")
    x0, x1 = 190, W - 40
    y = PAD_T + 20
    vmax = max(values)
    positives = [v for v in values if v > 0]
    floor = min(positives) * 0.8 if positives else 1.0
    for label, v in zip(labels, values):
        # 零值只用几何占位（画成 0 宽），文字仍显示真实值
        vv = v if v > 0 else floor
        frac = (math.log10(vv) - math.log10(floor)) / (math.log10(vmax) - math.log10(floor))
        w = frac * (x1 - x0)
        inner.append(text(x0 - 10, y + 15, label, size=12, anchor="end", color=INK))
        inner.append(f'<rect x="{x0}" y="{y}" width="{w:.1f}" height="22" rx="4" fill="{ACCENT if v == min(values) else WARN}" opacity="0.85"/>')
        val = f"{v:g} {unit}"
        if x0 + w + 8 + len(val) * 7.2 > W - 4:
            inner.append(text(x0 + w - 8, y + 15, val, size=12, anchor="end", color="var(--kb-paper)", weight="700"))
        else:
            inner.append(text(x0 + w + 8, y + 15, val, size=12, color=INK, weight="700"))
        y += 46
    if note:
        inner += note_text(x0, y + 8, note)
    return wrap(inner, title)


def chart_syscall():
    return _bar_chart("一次系统调用 ≈ 222 次函数调用（本机实测）",
                      ["C 函数调用", "getpid 系统调用"], [3.50, 778.12], "ns",
                      note="横向为对数刻度：两者差 222 倍。这台机器开了 KPTI，绝对值偏高。")


def chart_sqlite():
    return _bar_chart("100 万行查询：全表扫描 vs 走索引（本机 SQLite）",
                      ["全表扫描", "走索引"], [132.6, 0.2], "ms",
                      note="同一查询、同一数据，差约 660 倍。索引的代价是写入变慢、占磁盘。")


def chart_array():
    return hbar_chart("同一份数据，换个访问方式就差几倍（本机实测）",
                      ["数组顺序遍历", "链表遍历（顺序 malloc）", "数组随机跳访问"],
                      [10.72, 20.36, 41.78], "ms",
                      note="随机跳访问最慢：每次都要等一次缓存未命中。线性刻度，不是对数。")


def chart_memory():
    """进程内存分区示意"""
    inner = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="none"/>']
    inner.append(text(0, 14, "一个进程的内存里有什么", size=13, weight="700"))
    blocks = [
        ("栈 stack", "局部变量、调用帧 · 自动回收 · 常见 8 MB", ACCENT),
        ("堆 heap", "malloc/new · 手动管理 · 泄漏与碎片都在这里", WARN),
        ("bss", "未初始化全局变量（清零）", MUTED),
        ("data", "已初始化全局变量", MUTED),
        ("text", "机器码 · 只读", MUTED),
    ]
    y = 40
    for name, desc, color in blocks:
        h = 46
        inner.append(f'<rect x="90" y="{y}" width="300" height="{h}" rx="6" fill="{color}" opacity="0.12" stroke="{color}" stroke-width="1"/>')
        inner.append(text(104, y + 20, name, size=13, weight="700"))
        inner.append(text(104, y + 36, desc, size=11, color=MUTED))
        y += h + 8
    inner.append(text(410, 66, "高地址 ↑", size=11, color=MUTED))
    inner.append(text(410, 262, "低地址 ↓", size=11, color=MUTED))
    inner.append(f'<line x1="405" y1="76" x2="405" y2="252" stroke="{GRID}" stroke-width="1" stroke-dasharray="4 4"/>')
    inner.append(text(470, 130, "栈往低地址长", size=11, color=MUTED))
    inner.append(text(470, 150, "堆往高地址长", size=11, color=MUTED))
    inner.append(text(470, 190, "两者相向生长，", size=11, color=MUTED))
    inner.append(text(470, 208, "中间夹着空闲区", size=11, color=MUTED))
    return wrap(inner, "进程内存五块：栈自动回收但小，堆大但要自己管")


def chart_pipeline():
    """编译链路示意"""
    inner = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="none"/>']
    inner.append(text(0, 14, "从 .c 到能跑的进程：五道手", size=13, weight="700"))
    steps = [
        ("预处理", "gcc -E", "hi.i", "17,933 B"),
        ("编译", "gcc -S", "hi.s", "654 B"),
        ("汇编", "gcc -c", "hi.o", "1,480 B"),
        ("链接", "gcc", "hi", "15,960 B"),
        ("加载", "运行", "进程", "—"),
    ]
    x = 24
    y = 96
    bw, bh, gap = 122, 76, 14
    for i, (name, cmd, out, size) in enumerate(steps):
        inner.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="8" fill="{ACCENT}" opacity="0.10" stroke="{ACCENT}" stroke-width="1.2"/>')
        inner.append(text(x + bw / 2, y + 24, name, size=13, anchor="middle", weight="700"))
        inner.append(text(x + bw / 2, y + 44, cmd, size=11, anchor="middle", color=MUTED))
        inner.append(text(x + bw / 2, y + 62, f"{out} · {size}", size=11, anchor="middle", color=MUTED))
        if i < len(steps) - 1:
            inner.append(f'<path d="M{x+bw+2} {y+bh/2} L{x+bw+gap-4} {y+bh/2}" stroke="{MUTED}" stroke-width="1.6"/>')
            inner.append(f'<path d="M{x+bw+gap-8} {y+bh/2-4} L{x+bw+gap-2} {y+bh/2} L{x+bw+gap-8} {y+bh/2+4}" fill="{MUTED}"/>')
        x += bw + gap
    inner.append(text(24, 210, "报错出在哪一步，决定你该改什么：", size=12, weight="700"))
    inner.append(text(24, 232, "「undefined reference」是链接错误，不是语法错误——少 -l、少文件、extern 没实现", size=12, color=MUTED))
    inner.append(text(24, 254, "「cannot open shared object」是动态库缺失——容器里最常见", size=12, color=MUTED))
    inner.append(text(24, 276, "「段错误」是运行期——越界、空指针、栈溢出", size=12, color=MUTED))
    return wrap(inner, "五步链路与每步的真实产物大小（本机 x86_64）")


def chart_tcp_timeline():
    """一次请求的四个往返：DNS → TCP → TLS → HTTP"""
    inner = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="none"/>']
    inner.append(text(0, 14, "第一次访问一个网站，要等几个往返", size=13, weight="700"))
    cx, sx_ = 150, 560
    top, bottom = 56, 300
    inner.append(text(cx, top - 8, "客户端", size=12, anchor="middle", weight="700"))
    inner.append(text(sx_, top - 8, "服务器", size=12, anchor="middle", weight="700"))
    inner.append(f'<line x1="{cx}" y1="{top}" x2="{cx}" y2="{bottom}" stroke="{GRID}" stroke-width="1.4"/>')
    inner.append(f'<line x1="{sx_}" y1="{top}" x2="{sx_}" y2="{bottom}" stroke="{GRID}" stroke-width="1.4"/>')

    steps = [
        ("DNS 解析", "查域名 → 拿 IP", 1),
        ("TCP 握手", "SYN → SYN-ACK → ACK", 1),
        ("TLS 握手", "TLS 1.3 一个往返；1.2 两个", 1),
        ("HTTP 请求", "请求 → 响应", 1),
    ]
    y = top + 26
    for i, (name, detail, rtt) in enumerate(steps):
        color = ACCENT if i < 3 else WARN
        inner.append(text(16, y + 4, f"{i+1}. {name}", size=12, weight="700", color=color))
        inner.append(text(16, y + 20, detail, size=10.5, color=MUTED))
        inner.append(f'<line x1="{cx}" y1="{y}" x2="{sx_}" y2="{y}" stroke="{color}" stroke-width="1.8"/>')
        inner.append(f'<path d="M{sx_-8} {y-4} L{sx_} {y} L{sx_-8} {y+4}" fill="{color}"/>')
        inner.append(text((cx + sx_) / 2, y - 8, "1 RTT", size=10.5, anchor="middle", color=MUTED))
        y += 62
    inner.append(text(16, 318, "TLS 1.3 之后，前三次往返总共 3 RTT；首次访问常见 4 RTT 起（含 DNS 与连接建立）。", size=11, color=MUTED))
    inner.append(text(16, 334, "连接复用起来之后，后续请求只剩 HTTP 那一个往返。", size=11, color=MUTED))
    return wrap(inner, "首屏之前的四个往返：DNS、TCP、TLS、HTTP 各一次")


def chart_cert_chain():
    """证书链：从站点证书走到信任锚"""
    inner = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="none"/>']
    inner.append(text(0, 14, "证书链：验证的不是「这张证书」，而是「能不能走到我信任的根」", size=13, weight="700"))
    boxes = [
        ("站点证书", "example.com", "签名者：中间 CA", WARN),
        ("中间 CA", "Intermediate CA", "签名者：根 CA", ACCENT),
        ("根 CA", "Root CA", "在系统/浏览器信任库里", ACCENT),
    ]
    y = 62
    for i, (name, sub, note, color) in enumerate(boxes):
        inner.append(f'<rect x="60" y="{y}" width="300" height="62" rx="8" fill="{color}" opacity="0.10" stroke="{color}" stroke-width="1.2"/>')
        inner.append(text(76, y + 24, name, size=13, weight="700"))
        inner.append(text(76, y + 42, sub, size=11, color=MUTED))
        inner.append(text(76, y + 56, note, size=10.5, color=MUTED))
        if i < len(boxes) - 1:
            inner.append(f'<line x1="210" y1="{y+62}" x2="210" y2="{y+78}" stroke="{MUTED}" stroke-width="1.4"/>')
            inner.append(f'<path d="M206 {y+74} L210 {y+80} L214 {y+74}" fill="{MUTED}"/>')
        y += 80
    inner.append(text(400, 96, "验证要做三件事：", size=12, weight="700"))
    inner.append(text(400, 118, "① 签名能不能逐级验到根", size=11, color=MUTED))
    inner.append(text(400, 138, "② 域名是否匹配（SAN / 通配符）", size=11, color=MUTED))
    inner.append(text(400, 158, "③ 时间是否在有效期内", size=11, color=MUTED))
    inner.append(text(400, 196, "缺一环就失败：", size=12, weight="700"))
    inner.append(text(400, 218, "根不在信任库 → unknown CA", size=11, color=MUTED))
    inner.append(text(400, 238, "中间证书没下发 → incomplete chain", size=11, color=MUTED))
    inner.append(text(400, 258, "域名不匹配 → hostname mismatch", size=11, color=MUTED))
    inner.append(text(400, 278, "过期 → certificate has expired", size=11, color=MUTED))
    return wrap(inner, "证书链三段：站点证书 → 中间 CA → 根 CA（信任锚）")


def chart_fork():
    return _bar_chart("造一个执行单元要多少时间（本机实测）",
                      ["同进程 pipe 往返", "创建线程", "fork 复制进程", "fork + exec 换程序"],
                      [7.40, 131.12, 357.63, 1599.85], "µs",
                      note="横向为对数刻度；fork 只复制页表，exec 还要读 ELF 与加载动态库。")


def chart_fsync():
    return _bar_chart("同一份 8 MB 数据，三种写法差三个数量级（本机实测）",
                      ["O_DIRECT 写入", "buffered 写入", "每条 write 后 fdatasync"],
                      [117.57, 8.91, 14820.18], "ms",
                      note="对数刻度。中间那条最快，是因为它只写了内存；最慢那条每次都在等磁盘确认。")


def chart_pagecache():
    inner = frame("一次 write 之后，数据在哪", "时间", "")
    inner.append(text(0, 44, "write() 返回成功", size=12, weight="700", color=ACCENT))
    inner.append(text(0, 62, "数据在 page cache（内核内存），此时进程崩溃不丢", size=11, color=MUTED))
    inner.append(f'<line x1="0" y1="78" x2="{W-20}" y2="78" stroke="{GRID}" stroke-width="1"/>')
    inner.append(text(0, 104, "↓  脏页积累到 dirty_ratio（本机 20%）或被回收", size=11, color=MUTED))
    inner.append(text(0, 140, "内核 writeback 线程回写磁盘", size=12, weight="700", color=WARN))
    inner.append(text(0, 158, "此时断电才会丢；fsync 强行把这一步提前并等它完成", size=11, color=MUTED))
    inner.append(f'<line x1="0" y1="174" x2="{W-20}" y2="174" stroke="{GRID}" stroke-width="1"/>')
    inner.append(text(0, 200, "↓  块设备确认", size=11, color=MUTED))
    inner.append(text(0, 236, "数据真正在盘上", size=12, weight="700", color=ACCENT))
    inner.append(text(0, 254, "本机 O_DIRECT 直写只有 69.7 MB/s，这才是这块盘的速度", size=11, color=MUTED))
    inner.append(text(0, 290, "同一个 8 MB：buffered 8.91 ms ｜ fsync 14,820 ms ｜ 差 1,663 倍", size=12, weight="700", color=WARN))
    return wrap(inner, "write 的三个落点：页缓存 → 回写 → 磁盘确认")

def chart_db_index():
    return _bar_chart("同一张 20 万行的表，三种读法（本机 SQLite）",
                      ["全表扫描 SCAN", "走索引 + 回表（命中 2168 行）", "覆盖索引（只读索引）"],
                      [16.337, 5.373, 0.127], "ms",
                      note="对数刻度。中间那条虽然用了索引，但命中行太多，回表把收益吃掉了。")


def chart_db_txn():
    return _bar_chart("插 5000 行：逐条提交 vs 一个事务（本机 SQLite）",
                      ["一个事务", "逐条自动提交"],
                      [30.1, 33570.4], "ms",
                      note="对数刻度。差别不在 SQL，在于 5000 次 fsync 与 1 次 fsync。")

def chart_mc_error():
    ns = [10**3, 10**4, 10**5, 10**6]
    err = [0.04060, 0.01004, 0.00333, 0.00109]
    inner = frame("蒙特卡洛估 π：误差随样本量怎么降（本机实测）", "样本量 n（对数）", "绝对误差（对数）")
    ax, sx, sy = axes(500, 2_000_000, 0.0005, 0.2, ns, [0.001, 0.003, 0.01, 0.03, 0.1],
                      xfmt=lambda v: f"{int(v/1000)}k" if v < 1_000_000 else "1M",
                      yfmt=lambda v: f"{v:g}", logy=True)
    inner += ax
    inner += polyline([(sx(n), sy(e)) for n, e in zip(ns, err)], ACCENT)
    # 1/√n 参考线
    ref = [(sx(n), sy(1.0 / math.sqrt(n))) for n in (10**3, 10**6)]
    inner += polyline(ref, MUTED, width=1.6, dash="5 4", dots=False)
    inner += legend([("实测误差", ACCENT, None), ("1/√n 参考", MUTED, "5 4")],
                    x=W - PAD_R + 14, y=PAD_T + 14)
    inner.append(text(sx(1000) + 6, sy(0.0406) - 12, "0.041", size=11, color=ACCENT, weight="700"))
    inner.append(text(sx(1_000_000) - 8, sy(0.00109) - 12, "0.0011", size=11, anchor="end", color=ACCENT, weight="700"))
    inner.append(text(sx(1000) + 4, sy(0.0406) + 24, "样本 ×1000，误差只降 37 倍", size=11, color=MUTED))
    return wrap(inner, "误差与 1/√n 几乎平行：算力换精度是平方关系")


def chart_clt():
    ns = [10, 100, 1000, 10000]
    sd = [0.31035, 0.10028, 0.03135, 0.00994]
    inner = frame("样本均值的标准差 ≈ σ/√n（总体是指数分布，偏态）", "样本量 n（对数）", "均值标准差（对数）")
    ax, sx, sy = axes(8, 15000, 0.008, 0.4, ns, [0.01, 0.03, 0.1, 0.3],
                      xfmt=lambda v: f"{int(v)}", yfmt=lambda v: f"{v:g}", logy=True)
    inner += ax
    inner += polyline([(sx(n), sy(x)) for n, x in zip(ns, sd)], ACCENT)
    inner += polyline([(sx(n), sy(1/math.sqrt(n))) for n in (10, 10000)], MUTED, width=1.6, dash="5 4", dots=False)
    inner += legend([("模拟值", ACCENT, None), ("1/√n", MUTED, "5 4")], x=W - PAD_R + 14, y=PAD_T + 14)
    inner.append(text(sx(10) + 4, sy(0.31035) - 12, "0.310", size=11, color=ACCENT, weight="700"))
    inner.append(text(sx(10000) - 6, sy(0.00994) - 12, "0.0099", size=11, anchor="end", color=ACCENT, weight="700"))
    return wrap(inner, "n 涨 1000 倍，均值波动缩小约 31 倍（√1000 ≈ 31.6）")


def chart_ci_coverage():
    inner = frame("标称 95% 的置信区间，实际覆盖多少（3000 次重复）", "样本量 n", "覆盖率 %")
    ax, sx, sy = axes(0, 230, 80, 100, [5, 30, 200], [80, 85, 90, 95, 100], xfmt=lambda v: str(int(v)), yfmt=lambda v: f"{v}%")
    inner += ax
    # 95% 目标线
    inner.append(f'<line x1="{PAD_L}" y1="{sy(95):.1f}" x2="{W-PAD_R}" y2="{sy(95):.1f}" stroke="{WARN}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    inner.append(text(W - PAD_R - 4, sy(95) - 8, "标称 95%", size=11, anchor="end", color=WARN))
    for n, cov in ((5, 88.7), (30, 93.2), (200, 94.5)):
        x = sx(n)
        inner.append(f'<rect x="{x-26}" y="{sy(cov):.1f}" width="52" height="{sy(80)-sy(cov):.1f}" rx="4" fill="{ACCENT}" opacity="0.8"/>')
        inner.append(text(x, sy(cov) - 8, f"{cov}%", size=12, anchor="middle", weight="700"))
    inner += note_text(PAD_L, H - 10, "n=5 时只有 88.7%：偏态数据下 t 区间太窄，会让人误以为结论很确定")
    return wrap(inner, "小样本 + 偏态：置信区间系统性低估不确定性")

def chart_matmul():
    return _bar_chart("同一对 512×512 矩阵，三种写法（本机 C，-O2）",
                      ["朴素 ijk", "换序 ikj", "分块 64"], [331.3, 115.7, 95.5], "ms",
                      note="横向为对数刻度。数学完全等价，差别只在最内层循环是否连续访问内存。")


def chart_cond():
    conds = [1e2, 1e8, 1e12]
    ne = [8.68e-13, 4.62e-1, 4.68e-1]
    qr = [2.16e-15, 3.05e-10, 4.52e-5]
    inner = frame("条件数变大时，两种解法的误差（本机 numpy）", "矩阵条件数（对数）", "系数相对误差（对数）")
    ax, sx, sy = axes(50, 2e12, 1e-16, 1.0, [1e2, 1e8, 1e12], [1e-15, 1e-10, 1e-5, 1e-1],
                      xfmt=lambda v: f"{v:.0e}", yfmt=lambda v: f"{v:.0e}", logy=True)
    inner += ax
    inner += polyline([(sx(c), sy(e)) for c, e in zip(conds, ne)], WARN)
    inner += polyline([(sx(c), sy(e)) for c, e in zip(conds, qr)], ACCENT)
    inner += legend([("正规方程 XᵀXβ=Xᵀy", WARN, None), ("QR / lstsq", ACCENT, None)],
                    x=W - PAD_R + 14, y=PAD_T + 14)
    inner.append(text(sx(1e8) - 6, sy(4.62e-1) - 12, "46% 误差", size=11, anchor="end", color=WARN, weight="700"))
    inner.append(text(sx(1e8) + 8, sy(3.05e-10) + 16, "3e-10", size=11, color=ACCENT, weight="700"))
    inner += note_text(PAD_L, H - 10, "正规方程的误差按 κ² 放大，条件数 1e8 时系数已经错了近一半")
    return wrap(inner, "条件数 1e8：正规方程误差 46%，QR 仍有 1e-10 精度")

def chart_numdiff():
    hs = [1e-1, 1e-2, 1e-3, 1e-4, 1e-6, 1e-8, 1e-10, 1e-12, 1e-15]
    fwd = [4.294e-02, 4.216e-03, 4.208e-04, 4.207e-05, 4.207e-07, 2.970e-09, 5.848e-08, 4.324e-05, 1.481e-02]
    ctr = [9.001e-04, 9.005e-06, 9.005e-08, 9.004e-10, 2.772e-11, 2.581e-09, 5.848e-08, 1.227e-05, 1.481e-02]
    inner = frame("数值微分的误差是 U 形：h 太小反而更差", "步长 h（对数，向左更小）", "绝对误差（对数）")
    ax, sx, sy = axes(1e-16, 1.0, 1e-12, 1e-1, [1e-15, 1e-12, 1e-9, 1e-6, 1e-3, 1e-1],
                      [1e-11, 1e-8, 1e-5, 1e-2], xfmt=lambda v: f"{v:.0e}", yfmt=lambda v: f"{v:.0e}", logy=True)
    inner += ax
    inner += polyline([(sx(h), sy(e)) for h, e in zip(hs, fwd)], WARN)
    inner += polyline([(sx(h), sy(e)) for h, e in zip(hs, ctr)], ACCENT)
    inner += legend([("前向差分 ∝ h", WARN, None), ("中心差分 ∝ h²", ACCENT, None)],
                    x=W - PAD_R + 14, y=PAD_T + 14)
    inner.append(text(sx(1e-6), sy(2.772e-11) - 12, "中心差分最优 2.8e-11", size=11, anchor="middle", color=ACCENT, weight="700"))
    inner.append(text(sx(1e-15) + 6, sy(1.481e-02) - 10, "h=1e-15 全是噪声", size=11, color=WARN, weight="700"))
    return wrap(inner, "截断误差与舍入误差的平衡点：中心差分约在 h=1e-6")


def chart_integration():
    ns = [10, 20, 40, 80, 160]
    trap = [1.648e-02, 4.114e-03, 1.028e-03, 2.570e-04, 6.426e-05]
    simp = [1.095e-04, 6.784e-06, 4.231e-07, 2.643e-08, 1.652e-09]
    inner = frame("n 翻倍时误差怎么降：梯形 /4，辛普森 /16", "分段数 n（对数）", "绝对误差（对数）")
    ax, sx, sy = axes(8, 200, 1e-10, 1e-1, ns, [1e-9, 1e-7, 1e-5, 1e-3, 1e-1],
                      xfmt=lambda v: str(int(v)), yfmt=lambda v: f"{v:.0e}", logy=True)
    inner += ax
    inner += polyline([(sx(n), sy(e)) for n, e in zip(ns, trap)], WARN)
    inner += polyline([(sx(n), sy(e)) for n, e in zip(ns, simp)], ACCENT)
    inner += legend([("梯形 O(h²)，倍率 4.00", WARN, None), ("辛普森 O(h⁴)，倍率 16.00", ACCENT, None)],
                    x=W - PAD_R + 14, y=PAD_T + 14)
    inner.append(text(sx(160) - 6, sy(6.426e-05) - 12, "6.4e-5", size=11, anchor="end", color=WARN, weight="700"))
    inner.append(text(sx(160) - 6, sy(1.652e-09) - 12, "1.7e-9", size=11, anchor="end", color=ACCENT, weight="700"))
    return wrap(inner, "同样 160 段：梯形误差 6.4e-5，辛普森 1.7e-9（差 39,000 倍）")


def chart_gd():
    inner = frame("步长从 0.19 到 0.3：收敛、振荡、发散（本机实测）", "迭代步数", "‖x‖（对数）")
    ax, sx, sy = axes(0, 20, 1e-3, 1e6, [0, 5, 10, 15, 20], [1e-2, 1, 100, 1e4, 1e6],
                      xfmt=lambda v: str(int(v)), yfmt=lambda v: f"{v:g}", logy=True)
    inner += ax
    curves = {
        "lr=0.19": ([9.69e-01, 3.69e-01, 1.15e-01, 3.4e-02, 8e-03], ACCENT),
        "lr=0.2": ([1.0, 1.0, 1.0, 1.0, 1.0], MUTED),
        "lr=0.21": ([1.35, 2.6, 5.0, 9.6, 1.17e2], WARN),
        "lr=0.3": ([2.12, 1.02e3, 1.05e6, 1.05e6, 1.05e6], WARN),
    }
    for label, (vals, color) in curves.items():
        pts = [(sx(i * 5), sy(v)) for i, v in enumerate(vals)]
        inner += polyline(pts, color, dash="5 4" if label == "lr=0.2" else None)
    inner += legend([(k, c, "5 4" if k == "lr=0.2" else None) for k, (v, c) in curves.items()],
                    x=W - PAD_R + 14, y=PAD_T + 14)
    inner += note_text(PAD_L, H - 10, "特征值 1 与 10 → 收敛上界 2/10 = 0.2；边界值正好振荡不下降")
    return wrap(inner, "步长 0.19 收敛、0.2 振荡、0.21 发散、0.3 五步爆到 1e6")

def chart_deps():
    return _bar_chart("你审过的代码 vs 实际运行的代码（本机 pip list）",
                      ["直接依赖（requirements.txt）", "虚拟环境实际安装"], [2, 187], "个",
                      note="94 倍。攻击面按「实际装进来的包」算，不按你写了几个 import 算。")


def chart_strings():
    return _bar_chart("同一个程序：调试信息会留下多少可读字符串（本机 strings）",
                      ["-O2 无调试信息", "-O0 -g 带调试信息"], [59, 112], "条",
                      note="带 -g 时几乎翻倍，源码路径、变量名、断言文本全部留在产物里。")

def chart_host_surface():
    return _bar_chart("一台笔记本的暴露面（本机盘点）",
                      ["运行服务", "监听 socket", "其中对外", "SUID/SGID 文件"],
                      [40, 24, 9, 23], "个",
                      note="对外 9 个里包含 mDNS、DHCP 与两个应用自起的高位端口。")


def chart_hw_status():
    return _bar_chart("本机 17 项 CPU 漏洞的缓解状态（/sys 实测）",
                      ["Mitigation（有缓解）", "Not affected（不受影响）", "Vulnerable（无缓解）"],
                      [12, 5, 0], "项",
                      note="12 项有缓解，其中 4 项以关闭超线程为代价；没有裸露的 Vulnerable。")

def chart_hash_load():
    alphas = [0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
    return line_chart("链地址法：装载因子越高，平均查找越长", "装载因子 α", "平均比较次数",
                      alphas, [("1 + α/2", [1 + a / 2 for a in alphas], ACCENT, None)],
                      note="α=0.75 时约 1.38 次比较；再高就该扩容（2 倍，摊还 O(1)）")


def chart_cache_hit():
    hs = [0.0, 0.5, 0.8, 0.9, 0.95, 0.99]
    return line_chart("命中率决定平均耗时（缓存按后端的 1/10 计）", "缓存命中率",
                      "平均耗时（后端=1）", hs,
                      [("0.1h + (1−h)", [0.1 * h + (1 - h) for h in hs], ACCENT, None)],
                      note="80% 命中率已经把平均耗时压到 0.28；这是按公式示意，不是本机实测")


def chart_proc_thread():
    return col_chart("同一台机器上三种「造执行单元」的成本（本机实测）",
                     ["线程创建", "fork+wait", "fork+exec"],
                     [("微秒", [131.12, 357.63, 1599.85], ACCENT)], "µs",
                     note="线程最便宜，fork 要复制页表，exec 还要换整个地址空间",
                     yticks=[0, 500, 1000, 1500, 2000])


def chart_list_set():
    return hbar_chart("2 万元素 / 2000 次查询：list vs set（本机实测）",
                      ["list 线性扫描", "set 哈希查找"], [574.73, 0.225], "ms",
                      note="2554 倍。查询次数超过 10 次，建集合就回本。")


def chart_const_factor():
    return hbar_chart("常数因子能有多大：一次系统调用顶 222 次函数调用（本机实测）",
                      ["C 函数调用", "getpid 系统调用"], [3.50, 778.12], "ns",
                      note="缓存未命中还要再差约 100 倍（量级，未在本页实测）")


def chart_struct_choose():
    return strip_chart("四种结构怎么选（按场景打分，不是性能排名）",
                       ["查找", "插入", "有序遍历", "内存紧凑"],
                       [("数组", [1, 3, 1, 3], ""),
                        ("哈希表", [3, 3, 1, 1], ""),
                        ("平衡树", [2, 2, 3, 1], ""),
                        ("跳表", [2, 2, 3, 1], "")],
                       note="3=好 2=中 1=差。数组插入只有尾部快，中间插入是 O(n)。")


def chart_fib_growth():
    ns = [30, 40, 50]
    return line_chart("朴素递归斐波那契：每加 10 就乘 100", "n", "调用次数（对数）",
                      ns, [("朴素递归 2^n", [1e6, 1e8, 1e10], WARN, None),
                           ("迭代 O(n)", [30, 40, 50], ACCENT, "5 4")],
                      note="n=50 时朴素版要 1e10 次调用，迭代版只有 50 次",
                      logy=True, xticks=ns, yticks=[10, 1e3, 1e5, 1e7, 1e9, 1e11],
                      yfmt=lambda v: f"{v:.0e}")


def chart_pid_limit():
    return col_chart("僵尸只占 PID，但 PID 会被耗尽（本机与容器常见值）",
                     ["本机 ulimit -u", "容器常见上限", "更紧的容器"],
                     [("上限", [95090, 512, 256], ACCENT)], "个",
                     note="每个僵尸占 1 个 PID 与约几 KB 内存；容器里几十个就能让服务起不来",
                     logy=True)


def chart_mem_pressure():
    return strip_chart("内存紧张时系统会做什么（按代价排序）",
                       ["延迟影响", "数据风险", "好观测"],
                       [("回收页缓存", [2, 1, 3], ""),
                        ("换出到 swap", [3, 2, 2], ""),
                        ("触发 OOM killer", [3, 3, 3], ""),
                        ("分配失败返回", [1, 1, 3], "")],
                       note="3=高。OOM killer 排最后：它直接杀进程，不是「慢一点」。")


def chart_small_file():
    return col_chart("1 字节的内容，在磁盘上要占多少（本机实测）",
                     ["内容本身", "块对齐后", "实测占用"],
                     [("字节", [1, 4096, 4121], WARN)], "B",
                     note="块最小 4096 B；实测 4121 B 含元数据。2 万个这样的小文件要 1580 ms 建完",
                     logy=True)


def chart_file_free():
    return col_chart("删了文件，空间什么时候才回来（本机实测）",
                     ["写入数据", "unlink 后释放", "close 后释放"],
                     [("MB", [200, 0, 210], ACCENT)], "MB",
                     note="只要还有进程开着这个文件，unlink 就只是删了个目录项")


def chart_switch_cost():
    return col_chart("一次切换要多少时间（本机 C 程序实测）",
                     ["线程 → 线程", "进程 → 进程"],
                     [("微秒", [9.5, 13.7], ACCENT)], "µs",
                     note="1.45 倍。单核每秒上限：线程约 10.5 万次，进程约 7.3 万次")


def chart_wal_vs_delete():
    return col_chart("同一个事务 2 万行：DELETE 日志 vs WAL（本机实测）",
                     ["DELETE 模式", "WAL 模式"],
                     [("毫秒", [65.4, 55.1], ACCENT)], "ms",
                     note="只快 1.2 倍。WAL 的收益在「读写不打架」，不在这点写入时间")


def chart_write_lock():
    return col_chart("第二个写者等了多久才放弃（本机实测）",
                     ["第一个写者", "第二个写者（timeout=0.2）"],
                     [("毫秒", [0.0, 201.8], WARN)], "ms",
                     note="0 表示没等。SQLite 同时只允许一个写者，这是设计不是 bug")


def chart_txn_batch():
    return col_chart("插 5000 行：逐条提交 vs 一个事务（本机实测）",
                     ["一个事务", "逐条自动提交"],
                     [("毫秒", [30.1, 33570.4], WARN)], "ms",
                     note="1,115 倍。差别不在 SQL，在 5000 次 fsync 与 1 次",
                     logy=True)


def chart_crash_rows():
    return hbar_chart("kill -9 前后，那 10 万行去哪了（本机实测）",
                      ["崩溃前已插入（未提交）", "重启后可见"], [100000, 0], "行",
                      note="0 行且 integrity_check=ok：事务没提交，回滚是干净的")


def chart_index_selectivity():
    return hbar_chart("同一张表四种读法（本机 SQLite，20 万行）",
                      ["全表扫描", "低选择性索引（2168 行回表）", "覆盖索引", "高选择性索引（1 行）"],
                      [16.337, 5.373, 0.127, 0.0131], "ms",
                      note="「走了索引」不等于快：回表的随机读把收益吃掉，差 410 倍")


def chart_index_cost():
    return col_chart("多一个索引，写入贵多少（20 万行，本机实测）",
                     ["无索引", "加 1 个索引"],
                     [("毫秒", [367, 663], WARN)], "ms",
                     note="1.8 倍。索引在写入路径上一直收税，读得少就别建")


def chart_p_false():
    return col_chart("p<0.05 到底有多容易碰巧出现（本机模拟）",
                     ["单次检验「显著」", "20 次检验至少一次"],
                     [("比例 %", [5.5, 62.9], WARN)], "%",
                     note="单次名义 5%、实测 5.5%；20 次检验时理论 64.2%、模拟 62.9%",
                     yticks=[0, 20, 40, 60, 80])


def chart_variance_add():
    return col_chart("方差可加，但要独立（本机 20 万次模拟）",
                     ["单个骰子", "两个独立之和", "同一个加两次"],
                     [("方差", [2.917, 5.833, 11.667], ACCENT)], "",
                     note="独立时 2 倍，完全相关时 4 倍：把同一个随机量加两次是在放大风险",
                     yticks=[0, 3, 6, 9, 12])


def chart_coin_dev():
    ns = [10, 100, 1000, 10000]
    return line_chart("抛硬币：频率偏离 0.5 有多快（本机 1000 次重复）", "n（对数）",
                      "平均绝对偏差（对数）", ns,
                      [("实测", [0.1240, 0.0406, 0.0127, 0.0038], ACCENT, None),
                       ("1/(2√n)", [0.1581, 0.0500, 0.0158, 0.0050], MUTED, "5 4")],
                      note="n 涨 10 倍，偏差只降到约 1/3.2；这是所有采样精度的天花板",
                      logx=True)


def chart_birthday():
    ks = [10, 23, 40, 60]
    return col_chart("生日悖论：模拟与公式几乎重合（本机 2 万次模拟）",
                     ["10 人", "23 人", "40 人", "60 人"],
                     [("模拟 %", [12.08, 51.62, 89.28, 99.38], ACCENT),
                      ("公式 %", [11.69, 50.73, 89.12, 99.41], MUTED)], "%",
                     note="23 人过半，是因为比的是 253 对，不是 23 次",
                     yticks=[0, 25, 50, 75, 100])


def chart_simpson():
    return col_chart("每一组都赢，合并却输（本机构造数据集）",
                     ["轻症", "重症", "合并"],
                     [("A 组 %", [90.0, 50.0, 54.4], ACCENT),
                      ("B 组 %", [80.0, 40.0, 75.6], WARN)], "%",
                     note="A 的病人 89% 是重症，B 只有 11%：合并率是加权平均，权重变了结论就翻转",
                     yticks=[0, 25, 50, 75, 100])


def chart_lib_choice():
    return hbar_chart("同一个矩阵乘法，四种写法（n=256，本机实测）",
                      ["Python 三层循环", "C 朴素 ijk", "BLAS / numpy", "C 分块 256"],
                      [7716.7, 36.6, 12.77, 10.9], "ms",
                      note="Python 比 BLAS 慢 604 倍；分块 C 能追平 BLAS，但大矩阵会被反超")


def chart_similarity():
    return strip_chart("三种相似度各看什么（选错指标比不会算更糟）",
                       ["看方向", "看长度", "对量纲敏感", "适合文本"],
                       [("余弦", [3, 1, 1, 3], ""),
                        ("欧氏距离", [1, 3, 3, 1], ""),
                        ("点积", [2, 3, 3, 2], "")],
                       note="3=强相关。文本长短不一时，长度是噪声，所以用余弦。")


def chart_block_tile():
    ns = [256, 512]
    return line_chart("块不是越大越好：最优块取决于缓存容量（本机实测）", "矩阵规模 n",
                      "耗时 ms（对数）", ns,
                      [("朴素 ijk", [36.6, 331.3], WARN, None),
                       ("分块 64", [14.6, 95.5], ACCENT, None),
                       ("分块 256", [10.9, 99.9], ACCENT, "5 4")],
                      note="n=256 时块 256 最快，n=512 时块 64 反超：256 的块已超出 L3",
                      logy=True, xticks=ns, yticks=[10, 30, 100, 300],
                      yfmt=lambda v: f"{v:g}")


def chart_power_iter():
    gaps = [0.5, 0.9, 0.99]
    return line_chart("谱 gap 越小，幂迭代越慢（本机实测到 1e-10）", "次特征值 / 主特征值",
                      "所需步数（对数）", gaps,
                      [("实测步数", [38, 224, 2241], ACCENT, None),
                       ("log(1e-10)/log(gap)", [33, 219, 2303], MUTED, "5 4")],
                      note="gap 0.99 要 2241 步：这就是 PCA 与 PageRank 收敛慢的根源",
                      logy=True, xticks=gaps, yticks=[10, 100, 1000, 3000],
                      yfmt=lambda v: f"{v:g}")


def chart_matmul_cost():
    ns = [128, 256, 512, 1024]
    return line_chart("矩阵乘法的代价按 2n³ 涨（本机计时与公式）", "n（对数）",
                      "浮点运算次数（对数）", ns,
                      [("2n³", [2 * n ** 3 for n in ns], ACCENT, None)],
                      note="n=1024 时 21 亿次乘加；这个量级决定了它必须做缓存优化",
                      logx=True, logy=True,
                      xticks=ns, xfmt=lambda v: str(int(v)),
                      yticks=[1e7, 1e8, 1e9, 1e10], yfmt=lambda v: f"{v:.0e}")


def chart_collinear():
    pert = [0.001, 0.01, 1.0]
    return line_chart("列越接近，系数飘得越离谱（本机 200 次重复）", "列间扰动（对数）",
                      "系数标准差（对数）", pert,
                      [("系数标准差", [9.97, 0.98, 0.013], WARN, None)],
                      note="扰动 1e-3 时标准差 9.97：真值 1 的系数已经完全没有信息量",
                      logx=True, logy=True, xticks=pert,
                      xfmt=lambda v: f"{v:g}",
                      yticks=[0.01, 0.1, 1, 10], yfmt=lambda v: f"{v:g}")


def chart_deriv_order():
    hs = [1e-1, 1e-2, 1e-3, 1e-4, 1e-6]
    fwd = [4.294e-02, 4.216e-03, 4.208e-04, 4.207e-05, 4.207e-07]
    ctr = [9.001e-04, 9.005e-06, 9.005e-08, 9.004e-10, 2.772e-11]
    return line_chart("同样缩 10 倍的 h：前向差 10 倍，中心差 100 倍（本机实测）", "步长 h（对数）",
                      "绝对误差（对数）", hs,
                      [("前向差分 ∝ h", fwd, WARN, None), ("中心差分 ∝ h²", ctr, ACCENT, None)],
                      note="h=1e-4 时 4.2e-5 vs 9.0e-10：多算一次函数值，换来四个数量级",
                      logx=True, logy=True,
                      xticks=[1e-6, 1e-4, 1e-2, 1e-1], xfmt=lambda v: f"{v:g}",
                      yticks=[1e-11, 1e-8, 1e-5, 1e-2], yfmt=lambda v: f"{v:.0e}")


def chart_gd_steps():
    kappas = [2, 10, 100]
    return line_chart("条件数每涨 10 倍，梯度下降就要多走 10 倍步数（本机实测）", "条件数（对数）",
                      "到 1e-6 的步数（对数）", kappas,
                      [("梯度下降", [13, 71, 709], ACCENT, None)],
                      note="牛顿法在二次函数上 1 步到位，但每步 O(n³)：总代价要乘起来算",
                      logx=True, logy=True, xticks=kappas,
                      xfmt=lambda v: str(int(v)),
                      yticks=[10, 100, 1000], yfmt=lambda v: f"{v:g}")


def chart_taylor():
    xs = [1, 5, 10]
    return col_chart("e^x 的泰勒展开：x 越大越不可信（本机实测，取 20 项）",
                     ["x=1", "x=5", "x=10"],
                     [("绝对误差", [4.44e-16, 1.20e-05, 35.0], WARN)], "",
                     note="x=10 时取 20 项误差还有 35；收敛半径之外讨论「几项够」没有意义",
                     logy=True)


def chart_float_loss():
    return hbar_chart("三种浮点事故的严重程度（本机 Python 输出）",
                      ["0.1+0.2 与 0.3 的差", "(1e16+1) 被吃掉", "sqrt(1e16+1)−1e8 相消"],
                      [5.55e-17, 1.0, 5.0e-9], "",
                      note="第三项真值 5e-9 却被算成 0：改写公式后才拿得到这个数")


def chart_riemann():
    ns = [10, 40, 160]
    trap = [1.648e-02, 1.028e-03, 6.426e-05]
    simp = [1.095e-04, 4.231e-07, 1.652e-09]
    return line_chart("段数翻 4 倍：梯形降到 1/16，辛普森降到 1/256（本机实测）", "分段数 n（对数）",
                      "绝对误差（对数）", ns,
                      [("梯形 O(h²)", trap, WARN, None), ("辛普森 O(h⁴)", simp, ACCENT, None)],
                      note="同样 160 段：6.4e-5 vs 1.7e-9，差 39,000 倍",
                      logx=True, logy=True, xticks=ns, xfmt=lambda v: str(int(v)),
                      yticks=[1e-9, 1e-7, 1e-5, 1e-3], yfmt=lambda v: f"{v:.0e}")


def chart_hardening():
    return strip_chart("四项基线加固各挡什么（本机编译产物实测）",
                       ["挡固定地址", "挡栈溢出", "挡 GOT 改写", "挡栈上执行"],
                       [("PIE", [3, 1, 1, 1], ""),
                        ("栈保护", [1, 3, 1, 1], ""),
                        ("full RELRO", [1, 1, 3, 1], ""),
                        ("NX", [1, 1, 1, 3], "")],
                       note="3=该项主要作用。四项齐全只算基线，不是「安全」。")


def chart_hardening_cost():
    return col_chart("加固的代价：体积几乎不变（本机实测）",
                     ["无加固", "PIE + canary + RELRO"],
                     [("字节", [15936, 16056], ACCENT)], "B",
                     note="只多 120 字节（0.75%）；性能影响 1%–3%，属于「几乎免费必须做」")


def chart_aslr_entropy():
    return col_chart("ASLR 关掉之后，栈地址完全固定（本机实测）",
                     ["开 ASLR 三次", "关 ASLR 三次"],
                     [("不同地址数", [3, 1], WARN)], "个",
                     note="setarch -R 三次都是 7ffffffdd000：随机化一旦关闭，写死地址就成立",
                     yticks=[0, 1, 2, 3])


def chart_sec_tradeoff():
    return strip_chart("四条常见安全措施各收什么税",
                       ["延迟", "操作步骤", "排障难度", "兼容性"],
                       [("全链路加密", [3, 1, 1, 2], ""),
                        ("多因子认证", [1, 3, 1, 1], ""),
                        ("最小权限", [1, 2, 3, 1], ""),
                        ("严格输入校验", [1, 1, 2, 3], "")],
                       note="3=代价大。排障难度最少被计入，却常是最大的一笔。")


def chart_injection():
    return col_chart("同一句输入，两种写法两种结果（本机 sqlite3）",
                     ["拼接字符串", "参数化查询"],
                     [("返回行数", [1, 0], WARN)], "行",
                     note="本机表只有 1 行；换成 100 万行的表，拼接那条就是 100 万行泄漏",
                     yticks=[0, 1])


def chart_log_leak():
    return col_chart("一次报错能带出多少结构信息（本机实测）",
                     ["绝对路径", "世界可写文件", "监听 socket"],
                     [("数量", [1, 0, 24], ACCENT)], "个",
                     note="路径泄漏是 1 处，但它给的是目录结构；监听 24 个是最需要盘的暴露面")


CHARTS = {
    "growth": chart_growth,
    "sort": chart_sort,
    "quicksort": chart_quicksort,
    "search": chart_search,
    "syscall": chart_syscall,
    "sqlite": chart_sqlite,
    "array": chart_array,
    "memory": chart_memory,
    "pipeline": chart_pipeline,
    "tcp_timeline": chart_tcp_timeline,
    "cert_chain": chart_cert_chain,
    "fork": chart_fork,
    "fsync": chart_fsync,
    "pagecache": chart_pagecache,
    "db_index": chart_db_index,
    "db_txn": chart_db_txn,
    "matmul": chart_matmul,
    "cond": chart_cond,
    "numdiff": chart_numdiff,
    "integration": chart_integration,
    "gd": chart_gd,
    "deps": chart_deps,
    "strings": chart_strings,
    "hash_load": chart_hash_load,
    "cache_hit": chart_cache_hit,
    "proc_thread": chart_proc_thread,
    "list_set": chart_list_set,
    "const_factor": chart_const_factor,
    "struct_choose": chart_struct_choose,
    "fib_growth": chart_fib_growth,
    "pid_limit": chart_pid_limit,
    "mem_pressure": chart_mem_pressure,
    "small_file": chart_small_file,
    "file_free": chart_file_free,
    "switch_cost": chart_switch_cost,
    "wal_vs_delete": chart_wal_vs_delete,
    "write_lock": chart_write_lock,
    "txn_batch": chart_txn_batch,
    "crash_rows": chart_crash_rows,
    "index_selectivity": chart_index_selectivity,
    "index_cost": chart_index_cost,
    "p_false": chart_p_false,
    "variance_add": chart_variance_add,
    "coin_dev": chart_coin_dev,
    "birthday": chart_birthday,
    "simpson": chart_simpson,
    "lib_choice": chart_lib_choice,
    "similarity": chart_similarity,
    "block_tile": chart_block_tile,
    "power_iter": chart_power_iter,
    "matmul_cost": chart_matmul_cost,
    "collinear": chart_collinear,
    "deriv_order": chart_deriv_order,
    "gd_steps": chart_gd_steps,
    "taylor": chart_taylor,
    "float_loss": chart_float_loss,
    "riemann": chart_riemann,
    "hardening": chart_hardening,
    "hardening_cost": chart_hardening_cost,
    "aslr_entropy": chart_aslr_entropy,
    "sec_tradeoff": chart_sec_tradeoff,
    "injection": chart_injection,
    "log_leak": chart_log_leak,
    "host_surface": chart_host_surface,
    "hw_status": chart_hw_status,
    "mc_error": chart_mc_error,
    "clt": chart_clt,
    "ci_coverage": chart_ci_coverage,
}


def main():
    import sys
    if "--list" in sys.argv:
        print("\n".join(CHARTS))
        return 0
    inserted = 0
    for page in DOCS.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        marks = re.findall(r"<!--\s*kb-chart:([a-z_]+)\s*-->", text)
        if not marks:
            continue
        for name in marks:
            if name not in CHARTS:
                print(f"未知图: {name} in {page}")
                continue
            block = f"<!-- kb-chart:{name} -->\n\n" + CHARTS[name]() + "\n\n"
            text = re.sub(
                rf"<!--\s*kb-chart:{name}\s*-->.*?(?=<!--\s*kb-chart:|\n## |\Z)",
                lambda m: block,
                text,
                count=1,
                flags=re.S,
            )
            inserted += 1
        page.write_text(text, encoding="utf-8")
    print(f"插入 {inserted} 张图")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())