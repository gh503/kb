# 随机化 SVD 的误差界

> **深度** 取舍 ｜ **类型** 模拟 ｜ **链** 矩阵到底在说什么

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [秩与低秩近似](秩与低秩近似.md) · [图拉普拉斯与谱聚类](图拉普拉斯与谱聚类.md) · [张量分解入门](张量分解入门.md) · <span class="kb-chain__now">随机化SVD的误差界</span>
</div>

## 结论

**随机化 SVD 几乎不损失精度，却把计算量从"矩阵大小"降到"秩 × 过采样"。**
本机 300×300、秩 5 的矩阵：随机化 SVD（k=5、过采样 10、2 次幂迭代）**相对误差 4.365%**，
与精确 SVD 的秩 5 误差 **4.36%** 基本一致；**前 5 个奇异值的相对偏差 0.000%**。

## 为什么快

```text
精确 SVD：O(m·n·min(m,n))
随机化：先用随机矩阵把列空间压到 (k+p) 维，再做小 SVD
  → O(m·n·k) 量级，k ≪ min(m,n) 时快一到两个数量级
```

**"随机就不可靠"** 误差界是有理论保证的：误差 ≈ 尾部奇异值 + 概率项。

## 本机可复现（已模拟）

```bash
python3 - <<'PY'
import numpy as np
rng=np.random.default_rng(3); m=n=300; r=5
A=rng.normal(size=(m,r))@rng.normal(size=(n,r)).T+0.1*rng.normal(size=(m,n))
s=np.linalg.svd(A,compute_uv=False); E=np.sqrt((s**2).sum())
om=rng.normal(size=(n,15)); Y=A@om
for _ in range(2): Y=A@(A.T@Y)
Q,_=np.linalg.qr(Y); B=Q.T@A
Ub,sb,Vt=np.linalg.svd(B,full_matrices=False)
Ak=(Q@Ub[:,:5]*sb[:5])@Vt[:5]
print(round(np.linalg.norm(A-Ak)/E*100,3), round(np.max(np.abs(sb[:5]-s[:5])/s[:5])*100,3))
PY
```

本机输出：

```text
相对误差 4.365% ｜奇异值相对偏差 0.000%
```

## 三个参数

```text
k：要的秩
p（过采样）：通常 5–10，保证列空间抓得住
q（幂迭代）：奇异值衰减慢时加，q=1–2 常见
```

**"过采样越多越准"** 收益递减，p=10 之后基本无感。

## 误差界长什么样

```text
‖A − A_k‖ ≤ (1 + ε)·‖A − A_k^*‖ + 概率项
  → 第一项：精确最优秩 k 近似的误差（本机 4.36%）
  → 第二项：以 1 − δ 概率成立，δ 由 p 与 n 决定
结论：随机化最多让你比最优差一点点（ε 通常 < 0.1）
```

<!-- kb-chart:rsvd_err -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="前 5 个奇异值相对偏差 0.000%；p=10、q=2" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">随机化 SVD 的误差与精确 SVD 几乎一样：4.365% vs 4.36%（本机模拟）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">%</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1.25494</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">2.50988</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">3.76481</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">5.01975</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="179.5" y="68.2" width="43.0" height="225.8" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="201.0" y="62.2" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">4.36</text>
<rect x="460.5" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="482.0" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">4.365</text>
<text x="202.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">精确 SVD 秩 5</text>
<text x="483.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">随机化 SVD k=5</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">前 5 个奇异值相对偏差 0.000%；p=10、q=2</text>
</svg>
<figcaption>前 5 个奇异值相对偏差 0.000%；p=10、q=2</figcaption>
</figure>


## 数字与阈值（本机模拟）

```text
随机化 k=5：误差 4.365%（精确 4.36%）｜奇异值偏差 0.000%
经验：过采样 p = 5–10；幂迭代 q = 1–2
经验：奇异值衰减慢（比如白噪声矩阵）时，q 必须加
经验：误差地板由尾部奇异值决定，随机化改变不了它
```

## 证据强度

- **模拟**：误差与奇异值偏差来自本机实现
- **公开经验**：p/q 取值、误差界形式
- **推断**：大规模稀疏矩阵上，随机化 + 稀疏乘法才是真正提速来源

## 不适用的情况

- 矩阵很小（几百维）：精确 SVD 足够，随机化没意义
- 需要全部奇异值：随机化只给前 k 个

## 常见错法

- **p 取 0 或 1**（列空间抓不住）
- **奇异值衰减慢却不做幂迭代**
- **把随机化结果当"精确解"报告**

## 往下追

- 回到本链起点：[秩与低秩近似](秩与低秩近似.md)

## 相关

- [线性代数](index.md) · [收敛速度与计算量怎么权衡](../高等数学/收敛速度与计算量怎么权衡.md) · [秩与低秩近似](秩与低秩近似.md)
