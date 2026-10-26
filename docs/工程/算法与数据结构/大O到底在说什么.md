# 大O到底在说什么

> **深度** 入门 ｜ **类型** 公式 ｜ **链** 复杂度怎么估

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> <span class="kb-chain__now">大O到底在说什么</span> · [怎么从代码看出复杂度](怎么从代码看出复杂度.md) · [常数因子什么时候更重要](常数因子什么时候更重要.md) · [平均与最坏差多远](平均与最坏差多远.md)
</div>





## 结论

**大 O 描述的是"输入变大时，代价怎么长"，不是"跑多少秒"。**
它故意丢掉常数与低阶项——**所以 O(n) 的代码完全可能比 O(log n) 的慢**。

## 三个记号

```text
O(f)：上界，"不会比 f 长得更快"
Ω(f)：下界，"至少像 f 这样长"
Θ(f)：紧界，"就是 f 这个量级"
```

日常说"算法复杂度"时，多指 **Θ**，但习惯写 O。

## 常见的五个量级

| 量级 | n=1,000 | n=1,000,000 | 典型 |
| --- | --- | --- | --- |
| O(1) | 1 | 1 | 哈希查找、数组下标 |
| O(log n) | 10 | 20 | 二分查找、B 树 |
| O(n) | 1,000 | 1,000,000 | 遍历 |
| O(n log n) | 10,000 | 20,000,000 | 好的排序 |
| O(n²) | 1,000,000 | 10¹² | 双重循环、冒泡 |

**看最后一行**：n 从 1000 涨到 100 万，O(n²) 的代价涨了 **100 万倍**——这就是它的实际后果。

## 大 O 不算常数

```text
O(n) 但每次要读磁盘：常数是 10 ms → n=100 就要 1 秒
O(n²) 但每次是加法：常数是 1 ns → n=100 只要 10 微秒
```

**常数差了七个数量级时，量级比较就没意义了**——这正是[常数因子什么时候更重要](常数因子什么时候更重要.md)要讲的。

## 怎么读复杂度记号

```text
O(2n) = O(n)      常数系数丢掉
O(n + n²) = O(n²) 低阶项丢掉
O(log₂n) = O(log n) 底数丢掉
```

**"丢掉"不是不重要**：它意味着大 O 只在大 n 时才有指导意义。

<!-- kb-chart:growth -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="五种复杂度的增长曲线（纵轴为对数刻度）" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">同样从 n=1 到 n=1000，五种复杂度各涨多少</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">n（对数）</text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">操作次数（对数）</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1</text>
<line x1="62" y1="250.7" x2="624" y2="250.7" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="254.7" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">10</text>
<line x1="62" y1="207.3" x2="624" y2="207.3" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="211.3" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">100</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1,000</text>
<line x1="62" y1="120.7" x2="624" y2="120.7" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="124.7" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">10,000</text>
<line x1="62" y1="77.3" x2="624" y2="77.3" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="81.3" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">100,000</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="1.0" y="38.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1,000,000</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<text x="62.0" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1</text>
<text x="63.7" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">4</text>
<text x="70.4" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">16</text>
<text x="97.4" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">64</text>
<text x="205.5" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">256</text>
<text x="624.0" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1000</text>
<polyline points="62.0,294.0 63.7,294.0 70.4,294.0 97.4,294.0 205.5,294.0 624.0,294.0" fill="none" stroke="var(--kb-ink-mute)" stroke-width="2.2" stroke-dasharray="4 4" stroke-linejoin="round" stroke-linecap="round"/>
<polyline points="62.0,294.0 63.7,281.0 70.4,267.9 97.4,260.3 205.5,254.9 624.0,250.7" fill="none" stroke="var(--kb-accent)" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
<polyline points="62.0,294.0 63.7,267.9 70.4,241.8 97.4,215.7 205.5,189.6 624.0,164.0" fill="none" stroke="var(--kb-accent)" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
<polyline points="62.0,294.0 63.7,254.9 70.4,215.7 97.4,182.0 205.5,150.5 624.0,120.7" fill="none" stroke="var(--kb-warn)" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
<circle cx="62.0" cy="294.0" r="3.2" fill="var(--kb-warn)"/>
<circle cx="63.7" cy="254.9" r="3.2" fill="var(--kb-warn)"/>
<circle cx="70.4" cy="215.7" r="3.2" fill="var(--kb-warn)"/>
<circle cx="97.4" cy="182.0" r="3.2" fill="var(--kb-warn)"/>
<circle cx="205.5" cy="150.5" r="3.2" fill="var(--kb-warn)"/>
<circle cx="624.0" cy="120.7" r="3.2" fill="var(--kb-warn)"/>
<polyline points="62.0,294.0 63.7,241.8 70.4,189.6 97.4,137.5 205.5,85.3 624.0,34.0" fill="none" stroke="var(--kb-warn)" stroke-width="2.2" stroke-dasharray="6 4" stroke-linejoin="round" stroke-linecap="round"/>
<circle cx="62.0" cy="294.0" r="3.2" fill="var(--kb-warn)"/>
<circle cx="63.7" cy="241.8" r="3.2" fill="var(--kb-warn)"/>
<circle cx="70.4" cy="189.6" r="3.2" fill="var(--kb-warn)"/>
<circle cx="97.4" cy="137.5" r="3.2" fill="var(--kb-warn)"/>
<circle cx="205.5" cy="85.3" r="3.2" fill="var(--kb-warn)"/>
<circle cx="624.0" cy="34.0" r="3.2" fill="var(--kb-warn)"/>
<line x1="615.8" y1="48" x2="637.8" y2="48" stroke="var(--kb-ink-mute)" stroke-width="2.4" stroke-dasharray="4 4"/>
<text x="645.8" y="52.0" font-size="11" text-anchor="start" fill="currentColor" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">O(1)</text>
<line x1="615.8" y1="66" x2="637.8" y2="66" stroke="var(--kb-accent)" stroke-width="2.4"/>
<text x="645.8" y="70.0" font-size="11" text-anchor="start" fill="currentColor" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">O(log n)</text>
<line x1="615.8" y1="84" x2="637.8" y2="84" stroke="var(--kb-accent)" stroke-width="2.4"/>
<text x="645.8" y="88.0" font-size="11" text-anchor="start" fill="currentColor" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">O(n)</text>
<line x1="615.8" y1="102" x2="637.8" y2="102" stroke="var(--kb-warn)" stroke-width="2.4"/>
<text x="645.8" y="106.0" font-size="11" text-anchor="start" fill="currentColor" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">O(n log n)</text>
<line x1="615.8" y1="120" x2="637.8" y2="120" stroke="var(--kb-warn)" stroke-width="2.4" stroke-dasharray="6 4"/>
<text x="645.8" y="124.0" font-size="11" text-anchor="start" fill="currentColor" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">O(n²)</text>
<text x="618.0" y="48.0" font-size="11" text-anchor="end" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">n=1000 时差 100 万倍</text>
</svg>
<figcaption>五种复杂度的增长曲线（纵轴为对数刻度）</figcaption>
</figure>


## 数字与阈值（公式/经验）

```text
n=1e6 时：O(log n) 约 20 次操作，O(n) 约 1e6 次
经验：n < 100 时，复杂度差异常被常数淹没，直接测更靠谱
经验：n > 1e5 时，O(n²) 基本不可用（除非常数极小）
估算：每秒约 1e8 次简单操作（现代 CPU，粗估）
```

## 证据强度

- **公式**：量级对照表按定义算的
- **公开经验**："每秒约 1e8 次简单操作"的量级估计
- **推断**："n<100 时直接测"按常数与量级的相对大小推的

## 不适用的情况

- 小 n：常数与实现细节主导，量级无指导意义
- 含 IO 的算法：瓶颈在 IO，不在计算复杂度

## 常见错法

- **把大 O 当性能**：它不告诉你秒数
- **忽略常数**：同一量级可以差几十倍
- **用 O(n²) 处理十万条数据**：直接不可用

## 往下追

- [怎么从代码看出复杂度](怎么从代码看出复杂度.md)

## 相关

- [算法与数据结构](index.md) · [排序该用哪个](排序该用哪个.md)
