# p 值到底在说什么

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 相关不等于因果之后

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [独立与条件概率](独立与条件概率.md) · [辛普森悖论](辛普森悖论.md) · <span class="kb-chain__now">p值到底在说什么</span> · [置信区间怎么读](置信区间怎么读.md)
</div>


## 结论

**p 值回答的是："如果什么都没发生，看到这么极端结果的概率有多大。"**
它**不回答**"我的假设成立的概率"。本机实测：零假设下 p<0.05 的比例是 **5.5%**——正好是名义的 5%。

## 本机可复现（已实测）

```python
# 两组各 30 个标准正态样本，真实差异为 0
# 计算双样本 t 统计量，再用正态近似换 p 值，重复 5000 次
```

本机输出（numpy 1.21.5，5000 次重复）：

```text
p<0.05 的比例 5.5%      p<0.01 的比例 1.1%
p 值的中位数 0.501（均匀分布应为 0.5）
```

**"中位数 0.501"说明 p 值在零假设下是均匀分布**——它不是一个"有多真"的分数，只是一个分位数。

## 所以 p=0.03 是什么意思

```text
正确：假设没有差异，出现当前或更极端结果的概率是 3%
错误：有 97% 的概率我的假设成立
错误：有 3% 的概率这是巧合
```

**"p 小 = 结果罕见" ≠ "p 小 = 假设为真"**，中间差着基础率与先验。

## 多重比较：p<0.05 的陷阱

```text
做 1 次检验：假阳性 5%
做 20 次检验：至少一次假阳性 1-0.95²⁰ ≈ 64%
```

本机模拟 5000 轮，每轮 20 个零假设检验：

```text
理论 0.642    模拟 0.629
```

**"我试了 20 个指标，终于找到一个显著的"** 就是这么来的。要修正：Bonferroni（α/m）或 FDR。

## 该看什么而不是只看 p

```text
效应量：差多少（百分比、绝对值）
区间：不确定范围有多宽
样本量：能支撑多大的结论
预注册：假设是不是事后编的
```

**p 值不带单位，效应量才带**：p=0.001 可能只对应 0.1% 的提升。

<!-- kb-chart:p_false -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="单次名义 5%、实测 5.5%；20 次检验时理论 64.2%、模拟 62.9%" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">p&lt;0.05 到底有多容易碰巧出现（本机模拟）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">%</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="222.1" x2="624" y2="222.1" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="226.1" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">20</text>
<line x1="62" y1="150.2" x2="624" y2="150.2" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="154.2" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">40</text>
<line x1="62" y1="78.3" x2="624" y2="78.3" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="82.3" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">60</text>
<text x="54.0" y="15.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">80</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="179.5" y="274.2" width="43.0" height="19.8" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="201.0" y="268.2" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">5.5</text>
<rect x="460.5" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="482.0" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">62.9</text>
<text x="202.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">单次检验「显著」</text>
<text x="483.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">20 次检验至少一次</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">单次名义 5%、实测 5.5%；20 次检验时理论 64.2%、模拟 62.9%</text>
</svg>
<figcaption>单次名义 5%、实测 5.5%；20 次检验时理论 64.2%、模拟 62.9%</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
零假设下 p<0.05 的比例 5.5%，p<0.01 的比例 1.1%
p 值中位数 0.501（均匀）
20 次独立检验至少一次 p<0.05：理论 0.642、模拟 0.629
经验：多重比较用 Bonferroni（α/m）或 FDR
经验：A/B 实验先算最小可检测效应，再定样本量
```

## 证据强度

- **实测**：四行数字为本机输出
- **公式**：1-0.95^20 ≈ 0.642
- **公开经验**：Bonferroni/FDR 的用法

## 不适用的情况

- 贝叶斯分析：用后验概率，不用 p 值
- 探索性分析：p 值只应作为线索，不能作为结论

## 常见错法

- **把 p 当"假设为真的概率"**
- **p<0.05 就宣布有效**，不看效应量
- **反复试探直到 p<0.05**（p-hacking）

## 往下追

- [置信区间怎么读](置信区间怎么读.md)

## 相关

- [概率论](index.md) · [置信区间怎么读](置信区间怎么读.md)
