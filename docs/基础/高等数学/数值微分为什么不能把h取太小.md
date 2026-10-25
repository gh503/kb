# 数值微分为什么不能把 h 取太小

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 变化率怎么算

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><a href="导数在算什么.md">导数在算什么</a><span class="kb-chain__sep">·</span><span class="kb-chain__now">数值微分为什么不能把h取太小</span><span class="kb-chain__sep">·</span><a href="泰勒展开能信几项.md">泰勒展开能信几项</a><span class="kb-chain__sep">·</span><a href="浮点误差从哪来.md">浮点误差从哪来</a></div>

## 结论

**h 越小，截断误差越小，但舍入误差越大——总误差是 U 形曲线。**
本机实测：中心差分在 h=1e-6 时误差 2.77e-11（最好），到 h=1e-15 反而变成 **1.48e-2**。

## 两个误差在打架

```text
截断误差：∝ h²（中心差分）  → h 越小越好
舍入误差：∝ ε/h             → h 太小会爆炸
总误差 ≈ C₁h² + C₂ε/h
最优 h ≈ (ε)^(1/3) ≈ 6e-6（双精度）
```

**"h 不能太小"不是玄学，是两个误差的平衡点**。

## 本机可复现（已实测）

```python
for h in (1e-4, 1e-6, 1e-8, 1e-10, 1e-12, 1e-15):
    ctr = (np.sin(1+h) - np.sin(1-h)) / (2*h)
    print(h, abs(ctr - np.cos(1)))
```

本机输出：

```text
     1e-04   9.004e-10
     1e-06   2.772e-11    ← 最优点
     1e-08   2.581e-09
     1e-10   5.848e-08
     1e-12   1.227e-05
     1e-15   1.481e-02    ← 比 h=1e-1 还差
```

**h=1e-15 时误差 1.48e-2**：因为 `1+h` 在双精度下根本存不住 h 的低位，`f(1+h)-f(1-h)` 变成 0/0 附近的噪声。

## 为什么 h=1e-15 直接失效

```text
双精度有效位约 16 位
1 + 1e-15 只能保留到 1.000000000000001
f(x+h) 与 f(x-h) 的差 ≈ 2h·f'(x) ≈ 2e-15
而 f 本身精度只到 1e-16 → 相对噪声 5%
```

**"分子是 1e-15 量级的差，分母是 1e-15"**，全是噪声。

## 实务怎么选 h

```text
中心差分：h ≈ 1e-6（双精度）
前向差分：h ≈ 1e-8
有噪声的数据：h 要更大（噪声/斜率比）
高精度需求：用自动微分或复数步长法
```

**复数步长法**（`imag(f(x+ih))/h`）能到机器精度，但要函数支持复数。

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="截断误差与舍入误差的平衡点：中心差分约在 h=1e-6" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="14.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">数值微分的误差是 U 形：h 太小反而更差</text>
<text x="632.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">步长 h（对数，向左更小）</text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">绝对误差（对数）</text>
<line x1="62" y1="270.4" x2="624" y2="270.4" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="274.4" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1e-11</text>
<line x1="62" y1="199.5" x2="624" y2="199.5" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="203.5" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1e-08</text>
<line x1="62" y1="128.5" x2="624" y2="128.5" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="132.5" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1e-05</text>
<line x1="62" y1="57.6" x2="624" y2="57.6" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="61.6" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1e-02</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<text x="62.0" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1e-15</text>
<text x="62.0" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1e-12</text>
<text x="62.0" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1e-09</text>
<text x="62.0" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1e-06</text>
<text x="62.6" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1e-03</text>
<text x="118.2" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1e-01</text>
<polyline points="118.2,42.7 67.6,66.5 62.6,90.2 62.1,113.8 62.0,161.1 62.0,211.9 62.0,181.3 62.0,113.5 62.0,53.6" fill="none" stroke="var(--kb-warn)" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
<circle cx="118.2" cy="42.7" r="3.2" fill="var(--kb-warn)"/>
<circle cx="67.6" cy="66.5" r="3.2" fill="var(--kb-warn)"/>
<circle cx="62.6" cy="90.2" r="3.2" fill="var(--kb-warn)"/>
<circle cx="62.1" cy="113.8" r="3.2" fill="var(--kb-warn)"/>
<circle cx="62.0" cy="161.1" r="3.2" fill="var(--kb-warn)"/>
<circle cx="62.0" cy="211.9" r="3.2" fill="var(--kb-warn)"/>
<circle cx="62.0" cy="181.3" r="3.2" fill="var(--kb-warn)"/>
<circle cx="62.0" cy="113.5" r="3.2" fill="var(--kb-warn)"/>
<circle cx="62.0" cy="53.6" r="3.2" fill="var(--kb-warn)"/>
<polyline points="118.2,82.4 67.6,129.6 62.6,176.9 62.1,224.2 62.0,259.9 62.0,213.4 62.0,181.3 62.0,126.4 62.0,53.6" fill="none" stroke="var(--kb-accent)" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
<circle cx="118.2" cy="82.4" r="3.2" fill="var(--kb-accent)"/>
<circle cx="67.6" cy="129.6" r="3.2" fill="var(--kb-accent)"/>
<circle cx="62.6" cy="176.9" r="3.2" fill="var(--kb-accent)"/>
<circle cx="62.1" cy="224.2" r="3.2" fill="var(--kb-accent)"/>
<circle cx="62.0" cy="259.9" r="3.2" fill="var(--kb-accent)"/>
<circle cx="62.0" cy="213.4" r="3.2" fill="var(--kb-accent)"/>
<circle cx="62.0" cy="181.3" r="3.2" fill="var(--kb-accent)"/>
<circle cx="62.0" cy="126.4" r="3.2" fill="var(--kb-accent)"/>
<circle cx="62.0" cy="53.6" r="3.2" fill="var(--kb-accent)"/>
<line x1="638" y1="48" x2="660" y2="48" stroke="var(--kb-warn)" stroke-width="2.4"/>
<text x="668.0" y="52.0" font-size="11" text-anchor="start" fill="currentColor" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">前向差分 ∝ h</text>
<line x1="638" y1="66" x2="660" y2="66" stroke="var(--kb-accent)" stroke-width="2.4"/>
<text x="668.0" y="70.0" font-size="11" text-anchor="start" fill="currentColor" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">中心差分 ∝ h²</text>
<text x="62.0" y="247.9" font-size="11" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">中心差分最优 2.8e-11</text>
<text x="68.0" y="43.6" font-size="11" text-anchor="start" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">h=1e-15 全是噪声</text>
</svg>
<figcaption>截断误差与舍入误差的平衡点：中心差分约在 h=1e-6</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
中心差分最优 h≈1e-6，误差 2.77e-11
h=1e-15 时误差 1.48e-2（比 h=1e-1 的 9.0e-4 还差）
前向差分最优 h≈1e-8
经验：数据有噪声时 h 取 1e-3–1e-2
```

## 证据强度

- **实测**：六行误差为本机输出
- **公式**：最优 h ≈ ε^(1/3)（中心）、√ε（前向）
- **公开经验**：复数步长法与噪声数据下的 h 选择

## 不适用的情况

- 自动微分：没有 h，也就没有这个问题
- 解析解可得：直接求导，不用差分

## 常见错法

- **h 取 1e-12 以为更精确**
- **在有噪声数据上用 1e-8**
- **用前向差分做高精度需求**

## 往下追

- [泰勒展开能信几项](泰勒展开能信几项.md)

## 相关

- [高等数学](index.md) · [浮点误差从哪来](浮点误差从哪来.md)
