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
    out.append(text(W - PAD_R + 8, H - 8, xlab, size=11, color=MUTED))
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
    out = []
    for i, (label, color, dash) in enumerate(items):
        yy = y + i * 18
        d = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<line x1="{x}" y1="{yy}" x2="{x+22}" y2="{yy}" stroke="{color}" stroke-width="2.4"{d}/>')
        out.append(text(x + 30, yy + 4, label, size=11, color=INK))
    return out


def wrap(inner, caption):
    return (
        '<figure class="kb-figure">\n'
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(caption)}" '
        'xmlns="http://www.w3.org/2000/svg">\n' + "\n".join(inner) + "\n</svg>\n"
        f'<figcaption>{caption}</figcaption>\n</figure>'
    )


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
    for label, v in zip(labels, values):
        frac = (math.log10(v) - math.log10(min(values) * 0.8)) / (
            math.log10(vmax) - math.log10(min(values) * 0.8))
        w = frac * (x1 - x0)
        inner.append(text(x0 - 10, y + 15, label, size=12, anchor="end", color=INK))
        inner.append(f'<rect x="{x0}" y="{y}" width="{w:.1f}" height="22" rx="4" fill="{ACCENT if v == min(values) else WARN}" opacity="0.85"/>')
        inner.append(text(x0 + w + 8, y + 15, f"{v:g} {unit}", size=12, color=INK, weight="700"))
        y += 46
    if note:
        inner.append(text(x0, y + 8, note, size=11, color=MUTED))
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
    inner = frame("同一份数据，换个访问方式就差几倍", "耗时 ms", "")
    ax, sx, sy = axes(0, 45, 0, 4, [0, 10, 20, 30, 40], [], xfmt=lambda v: f"{v:g}", yfmt=str)
    inner += ax
    rows = [("数组顺序遍历", 10.72, ACCENT), ("链表遍历（顺序 malloc）", 20.36, ACCENT),
            ("数组随机跳访问", 41.78, WARN)]
    y = PAD_T + 26
    for label, v, c in rows:
        w = sx(v) - PAD_L
        inner.append(text(PAD_L - 10, y + 16, label, size=12, anchor="end", color=INK))
        inner.append(f'<rect x="{PAD_L}" y="{y}" width="{w:.1f}" height="22" rx="4" fill="{c}" opacity="0.85"/>')
        inner.append(text(PAD_L + w + 8, y + 16, f"{v:.1f} ms", size=12, color=INK, weight="700"))
        y += 60
    inner.append(text(PAD_L, y + 10, "400 万元素；链表只有 1.9 倍差距，因为节点是顺序分配的", size=11, color=MUTED))
    return wrap(inner, "顺序 vs 随机、数组 vs 链表：局部性的真实代价")


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
    inner.append(text(PAD_L, H - 10, "n=5 时只有 88.7%：偏态数据下 t 区间太窄，会让人误以为结论很确定", size=11, color=MUTED))
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
    inner.append(text(PAD_L, H - 10, "正规方程的误差按 κ² 放大，条件数 1e8 时系数已经错了近一半", size=11, color=MUTED))
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
    inner.append(text(PAD_L, H - 10, "特征值 1 与 10 → 收敛上界 2/10 = 0.2；边界值正好振荡不下降", size=11, color=MUTED))
    return wrap(inner, "步长 0.19 收敛、0.2 振荡、0.21 发散、0.3 五步爆到 1e6")

def chart_deps():
    return _bar_chart("你审过的代码 vs 实际运行的代码（本机 pip list）",
                      ["直接依赖（requirements.txt）", "虚拟环境实际安装"], [2, 187], "个",
                      note="94 倍。攻击面按「实际装进来的包」算，不按你写了几个 import 算。")


def chart_strings():
    return _bar_chart("同一个程序：调试信息会留下多少可读字符串（本机 strings）",
                      ["-O2 无调试信息", "-O0 -g 带调试信息"], [59, 112], "条",
                      note="带 -g 时几乎翻倍，源码路径、变量名、断言文本全部留在产物里。")

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
            text = re.sub(
                rf"<!--\s*kb-chart:{name}\s*-->.*?(?=<!--\s*kb-chart:|\n## |\Z)",
                CHARTS[name]() + "\n\n",
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