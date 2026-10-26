# SVD 为什么比特征分解更通用

> **深度** 入门 ｜ **类型** 实测 ｜ **链** 分解能回答什么

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> <span class="kb-chain__now">SVD为什么比特征分解更通用</span> · [稀疏矩阵怎么存怎么乘](稀疏矩阵怎么存怎么乘.md) · [正交化的数值稳定性](正交化的数值稳定性.md) · [PCA的实际取舍](PCA的实际取舍.md)
</div>


## 结论

**特征分解只对"方阵且可对角化"的矩阵有意义，SVD 对任意矩阵都存在。**
本机实测：随机 5×5 非对称矩阵的特征向量**根本不正交**（`‖VᵀV−I‖` 的非对角元最大到 1.000），
而 SVD 给出的左右奇异向量一定正交。

## 两者在说什么

```text
特征分解：A v = λ v        → "这个方向只被拉伸，不转弯"
  要求：方阵、可对角化；实对称时特征向量正交
SVD：A = U Σ Vᵀ            → "先转 V、再拉伸 Σ、再转 U"
  对任意 m×n 矩阵都存在；U、V 都正交；σ 非负且降序
```

**"特征值可能是复数、特征向量可能不正交"** 是特征分解的常态，不是异常。

## 本机可复现（已实测）

```bash
python3 - <<'PY'
import numpy as np
rng = np.random.default_rng(0)
A = rng.normal(size=(5, 5))
w, V = np.linalg.eig(A)
print("特征值实部范围 %.2f–%.2f" % (w.real.min(), w.real.max()))
print("‖VᵀV−I‖ 的最大非对角元: %.3f" % np.max(np.abs(V.T @ V - np.eye(5))))
M = rng.normal(size=(200, 100))
U, S, Vt = np.linalg.svd(M, full_matrices=False)
for k in (1, 5, 20):
    approx = U[:, :k] @ np.diag(S[:k]) @ Vt[:k]
    err = np.linalg.norm(M - approx, 'fro') / np.linalg.norm(M, 'fro')
    print(f"秩 {k} 近似：相对误差 {err*100:.1f}%，保留能量 {(S[:k]**2).sum()/(S**2).sum()*100:.1f}%")
PY
```

本机输出：

```text
特征值实部范围 -2.51–1.55
‖VᵀV−I‖ 的最大非对角元: 1.000
秩 1 近似：相对误差 98.6%，保留能量 2.7%
秩 5 近似：相对误差 93.2%，保留能量 13.1%
秩 20 近似：相对误差 75.6%，保留能量 42.9%
```

## 秩-k 近似为什么不一定好用

```text
随机矩阵的奇异值分布很平 → 前 20 个只占 42.9% 能量
真实数据（有结构）奇异值衰减快 → 前几个就能占 90%+
```

**"SVD 能做压缩"的前提是数据低秩**，不是 SVD 本身有魔力。
本机这个 200×100 的随机矩阵就是反例：秩 20 还不如不做。

## 什么时候用哪个

```text
用 SVD：任意矩阵、要降维/压缩/求伪逆/最小二乘、要数值稳定
用特征分解：对称矩阵（协方差、图拉普拉斯）、要看"长期行为"（马尔可夫链）
用 QR：只解线性方程组，比 SVD 快
```

**"协方差矩阵是对称的"** 所以 PCA 用特征分解或 SVD 都行，数值上 SVD 更稳。

<!-- kb-chart:svd_rank -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="随机矩阵奇异值分布很平，SVD 压缩基本无效" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="14.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">随机 200×100 矩阵：秩 20 只保留 42.9% 能量（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">%</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="298.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">28.75</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">57.5</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">86.25</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">115</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="132.7" y="71.1" width="43.0" height="222.9" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="154.2" y="65.1" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">98.6</text>
<rect x="320.0" y="83.3" width="43.0" height="210.7" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="341.5" y="77.3" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">93.2</text>
<rect x="507.3" y="123.1" width="43.0" height="170.9" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="528.8" y="117.1" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">75.6</text>
<text x="155.7" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">秩 1</text>
<text x="343.0" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">秩 5</text>
<text x="530.3" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">秩 20</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">随机矩阵奇异值分布很平，SVD 压缩基本无效</text>
</svg>
<figcaption>随机矩阵奇异值分布很平，SVD 压缩基本无效</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
非对称 5×5：特征向量正交性偏差最大 1.000（完全不正交）
随机 200×100：秩 20 保留能量 42.9%，相对误差 75.6%
经验：奇异值衰减到 1% 以下的维度通常可以砍
经验：条件数 = σmax/σmin，超过 1e12 就别直接求逆
经验：伪逆用 SVD 算，别用 (AᵀA)⁻¹Aᵀ（会平方条件数）
```

## 证据强度

- **实测**：正交性偏差与三个秩的误差来自本机 numpy
- **公开经验**：伪逆与条件数的建议
- **推断**：真实数据的奇异值谱形状差异极大，压缩率必须实测

## 不适用的情况

- 小矩阵、良态：直接解方程即可，分解是浪费
- 需要稀疏性：SVD 会变稠密，改用随机化 SVD 或稀疏分解

## 常见错法

- **对非对称矩阵用 `eig` 然后假设特征向量正交**
- **用 `(AᵀA)⁻¹Aᵀ` 求伪逆**
- **以为 SVD 一定能压缩**

## 往下追

- [稀疏矩阵怎么存怎么乘](稀疏矩阵怎么存怎么乘.md)

## 相关

- [线性代数](index.md) · [特征值在说什么](特征值在说什么.md) · [矩阵乘法为什么快慢差几十倍](矩阵乘法在算什么.md)
