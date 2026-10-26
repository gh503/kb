# PCA 的实际取舍

> **深度** 取舍 ｜ **类型** 实测 ｜ **链** 分解能回答什么

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [SVD为什么比特征分解更通用](SVD为什么比特征分解更通用.md) · [稀疏矩阵怎么存怎么乘](稀疏矩阵怎么存怎么乘.md) · [正交化的数值稳定性](正交化的数值稳定性.md) · <span class="kb-chain__now">PCA的实际取舍</span>
</div>


## 结论

**"保留 80% 方差"是个坏规则，因为它不告诉你丢掉了什么。**
本机实测（20 维、奇异值线性衰减）：
**前 5 个主成分解释 58.4% 方差，重构相对误差仍 64.5%；前 10 个到 87.6%，误差 35.2%。**

## PCA 在做什么

```text
1. 中心化（减均值）—— 不做这一步，第一主成分会被均值方向吃掉
2. 协方差矩阵的特征分解，或对中心化矩阵做 SVD
3. 取前 k 个方向：解释方差最多、重构误差最小（在平方误差意义下）
```

**"PCA 找的是方差最大的方向"**，不是"最有意义的方向"——两者常常不同。

## 本机可复现（已实测）

```bash
python3 - <<'PY'
import numpy as np
rng = np.random.default_rng(0)
X = rng.normal(size=(1000, 20)) @ np.diag(np.linspace(5, 0.1, 20))
Xc = X - X.mean(0)
U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
ev = S**2 / (S**2).sum()
for k in (1, 3, 5, 10):
    print(f"前 {k:>2} 个主成分：解释方差 {ev[:k].sum()*100:.1f}%，"
          f"重构相对误差 {np.sqrt(1-ev[:k].sum())*100:.1f}%")
PY
```

本机输出：

```text
前  1 个主成分：解释方差 14.7%，重构相对误差 92.4%
前  3 个主成分：解释方差 38.5%，重构相对误差 78.4%
前  5 个主成分：解释方差 58.4%，重构相对误差 64.5%
前 10 个主成分：解释方差 87.6%，重构相对误差 35.2%
```

## 为什么"80% 方差"会骗人

```text
方差占比高 ≠ 信息保留多
  → 高方差方向可能是噪声（测量尺度大的变量）
  → 低方差方向可能承载分类边界（PCA 恰恰会丢掉它）
```

**"PCA 之后分类变差"** 是常见现象：它优化的是重构，不是判别。

## 三个必须一起做的预处理

```text
1. 标准化：各列量纲不同时，先除以标准差（否则大方差变量垄断）
2. 中心化：必须做
3. 异常值处理：PCA 对异常值极敏感（方差被一个点主导）
```

**"忘了标准化"** 是 PCA 最常见的错误：结果只是"选了单位最大的那几列"。

<!-- kb-chart:pca_curve -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="20 维、奇异值线性衰减；重构相对误差对应 92.4%/78.4%/64.5%/35.2%" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="14.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">主成分数与保留方差：前 5 个只有 58.4%（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">主成分个数</text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">解释方差 %</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="298.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.5" x2="624" y2="229.5" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.5" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">25</text>
<line x1="62" y1="165.0" x2="624" y2="165.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="169.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">50</text>
<line x1="62" y1="100.4" x2="624" y2="100.4" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="104.4" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">75</text>
<line x1="62" y1="35.9" x2="624" y2="35.9" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="39.9" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">100</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<text x="62.0" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1</text>
<text x="186.9" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">3</text>
<text x="311.8" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">5</text>
<text x="624.0" y="312.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">10</text>
<polyline points="62.0,256.1 186.9,194.6 311.8,143.3 624.0,67.9" fill="none" stroke="var(--kb-accent)" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
<circle cx="62.0" cy="256.1" r="3.2" fill="var(--kb-accent)"/>
<circle cx="186.9" cy="194.6" r="3.2" fill="var(--kb-accent)"/>
<circle cx="311.8" cy="143.3" r="3.2" fill="var(--kb-accent)"/>
<circle cx="624.0" cy="67.9" r="3.2" fill="var(--kb-accent)"/>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">20 维、奇异值线性衰减；重构相对误差对应 92.4%/78.4%/64.5%/35.2%</text>
</svg>
<figcaption>20 维、奇异值线性衰减；重构相对误差对应 92.4%/78.4%/64.5%/35.2%</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
20 维、奇异值线性衰减：k=5 → 58.4% 方差 / 64.5% 误差；k=10 → 87.6% / 35.2%
经验：解释方差到 90% 常需要 k ≈ 维度的一半（取决于谱形状）
经验：k 的选择要看下游任务指标，不看方差阈值
经验：样本数 < 维度时，主成分数最多 n−1
```

## 证据强度

- **实测**：四组方差与误差来自本机构造数据
- **公开经验**：标准化、中心化、异常值三条预处理
- **推断**：真实数据的谱形状不同，k 的最优值必须用下游指标选

## 不适用的情况

- 变量间非线性关系（流形）：PCA 只能抓线性结构，考虑核 PCA/UMAP
- 维度本来很低（< 5）：降维收益小

## 常见错法

- **不标准化就做 PCA**
- **按"80% 方差"一刀切**
- **用 PCA 降维后再解释主成分的物理含义**（方向是旋转出来的，通常没有名字）

## 往下追

- 回到本链起点：[SVD 为什么比特征分解更通用](SVD为什么比特征分解更通用.md)

## 相关

- [线性代数](index.md) · [正交化的数值稳定性](正交化的数值稳定性.md) · [特征值在说什么](特征值在说什么.md)
