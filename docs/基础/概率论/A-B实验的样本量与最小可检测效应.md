# A/B 实验的样本量与最小可检测效应

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 把不确定性算成数

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><a href="贝叶斯更新怎么做才算得清.md">贝叶斯更新怎么做才算得清</a><span class="kb-chain__sep">·</span><span class="kb-chain__now">A/B 实验的样本量与最小可检测效应</span><span class="kb-chain__sep">·</span><a href="重尾分布为什么让均值失去意义.md">重尾分布为什么让均值失去意义</a><span class="kb-chain__sep">·</span><a href="相关性检验怎么选.md">相关性检验怎么选</a></div>

## 结论

**样本量不够时，"没差异"几乎必然——因为你根本看不见差异。**
本机模拟（基线 10%、每组独立抽样、α=0.05）：
**每组 1000 人时只有 28.7% 的概率检出提升 2 个百分点；5000 人时 89.8%；20000 人时 100%。**

## 三个量绑在一起

```text
效应大小（MDE）：你想发现多大的差异
样本量 n：能拿到多少
功效（power）：真有效应时能检出的概率，惯例 ≥ 80%
  → 三者只能定两个，第三个是算出来的
```

**"先定 MDE，再算 n"** 是唯一正确的顺序；反过来（先有 n 再解释结果）会得到"没有显著差异"的废话。

## 本机可复现（已实测）

```bash
python3 - <<'PY'
import numpy as np
from math import sqrt
rng = np.random.default_rng(42)
def power(n, p1, p2, alpha=0.05, reps=2000):
    z = 1.959964
    hits = 0
    for _ in range(reps):
        a = rng.binomial(n, p1)/n; b = rng.binomial(n, p2)/n
        se = sqrt((a*(1-a) + b*(1-b))/n)
        if se > 0 and (b-a)/se > z: hits += 1
    return hits/reps
for n in (1000, 5000, 20000):
    print(f"n={n:>6}：检出 2 个点的概率 {power(n,0.10,0.12)*100:.1f}%")
for eff in (0.01, 0.02, 0.05):
    print(f"n=20000，效应 {eff*100:.0f} 个点：{power(20000,0.10,0.10+eff)*100:.1f}%")
PY
```

本机输出：

```text
n=  1000：检出 2 个点的概率 28.7%
n=  5000：检出 2 个点的概率 89.8%
n= 20000：检出 2 个点的概率 100.0%
n=20000，效应 1 个点：89.7%
```

## 一个能记住的近似

```text
每组样本量 ≈ 16 × p(1−p) / MDE²     （α=0.05、power=80%）
p=0.10、MDE=0.02 → 16×0.09/0.0004 = 3600/组
p=0.10、MDE=0.01 → 14400/组
```

**"效应减半，样本量翻四倍"**：MDE 与 n 是平方关系，这是实验设计里最贵的一条。

<!-- kb-chart:power_n -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="基线 10%、α=0.05、2000 次模拟；80% 功效的门槛在 3000–4000 之间" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="14.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">每组 1000 人只有 28.7% 能检出 2 个点（本机模拟）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">每组样本量（对数）</text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">检出概率 %</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="298.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="237.5" x2="624" y2="237.5" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="241.5" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">25</text>
<line x1="62" y1="181.0" x2="624" y2="181.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="185.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">50</text>
<line x1="62" y1="124.4" x2="624" y2="124.4" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="128.4" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">75</text>
<line x1="62" y1="67.9" x2="624" y2="67.9" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="71.9" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">100</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<text x="68.4" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1000</text>
<text x="145.0" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">5000</text>
<text x="432.4" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">20000</text>
<polyline points="68.4,229.1 145.0,91.0 432.4,67.9" fill="none" stroke="var(--kb-accent)" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
<circle cx="68.4" cy="229.1" r="3.2" fill="var(--kb-accent)"/>
<circle cx="145.0" cy="91.0" r="3.2" fill="var(--kb-accent)"/>
<circle cx="432.4" cy="67.9" r="3.2" fill="var(--kb-accent)"/>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">基线 10%、α=0.05、2000 次模拟；80% 功效的门槛在 3000–4000 之间</text>
</svg>
<figcaption>基线 10%、α=0.05、2000 次模拟；80% 功效的门槛在 3000–4000 之间</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
n=1000 → 28.7% ｜ n=5000 → 89.8% ｜ n=20000 → 100%（MDE=2 个点，基线 10%）
n=20000 时，1 个点效应 89.7%、2 个点以上 100%
近似公式：n ≈ 16·p(1−p)/MDE²
经验：power < 80% 的实验不要做结论
经验：中途看结果并"到了显著就停"，会显著抬高假阳性
```

## 证据强度

- **实测**：五组功效数字来自本机模拟
- **公开经验**：80% 功效惯例与近似公式
- **推断**：模拟假设独立同分布，真实实验有网络效应与周期性

## 不适用的情况

- 指标是比率以外的分布（如长尾金额）：要用 t 检验或 bootstrap，公式不同
- 有强干扰（大促、节假日）：再大的 n 也救不了

## 常见错法

- **先跑实验，再问"为什么没显著"**
- **看到 p<0.05 就停，忽略"偷看"带来的假阳性**
- **把 MDE 定得极小，然后发现根本凑不够样本**

## 往下追

- [重尾分布为什么让均值失去意义](重尾分布为什么让均值失去意义.md)

## 相关

- [概率论](index.md) · [p 值到底在说什么](p值到底在说什么.md) · [置信区间怎么读](置信区间怎么读.md)
