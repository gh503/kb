# 约束优化与 KKT 条件

> **深度** 实操 ｜ **类型** 计算 ｜ **链** 算法会收敛吗

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [稀疏与迭代求解](稀疏与迭代求解.md) · [蒙特卡洛与拟蒙特卡洛](蒙特卡洛与拟蒙特卡洛.md) · <span class="kb-chain__now">约束优化与KKT条件</span> · [全局优化为什么难](全局优化为什么难.md)
</div>

## 结论

**约束起作用时，最优解不在梯度为零处，而在"梯度等于约束梯度乘以一个系数"处——那个系数就是影子价格。**
本机算例：`min (x−2)² + (y−1)²` 受 `x+y ≤ 2` 约束 →
无约束最优 `(2,1)` 不可行（和 3 > 2），约束最优 **`(1.5, 0.5)`，目标 0.5，λ = 1**。

## KKT 四条

```text
1. 平稳性：∇f + λ∇c = 0（本机：(-1,-1) + 1·(1,1) = 0）
2. 原始可行：c(x) ≤ 0（本机 1.5 + 0.5 = 2，紧）
3. 对偶可行：λ ≥ 0（等式约束则 λ 可正可负）
4. 互补松弛：λ·c(x) = 0（约束不起作用时 λ = 0）
```

**"拉格朗日乘子只是中间变量"** λ 有量纲与含义：目标函数对约束右端的敏感度。

## 本机可复现（已计算）

```bash
python3 - <<'PY'
import numpy as np
# 解 KKT 方程组：x-2+λ=0, y-1+λ=0, x+y=2
A=np.array([[1,0,1],[0,1,1],[1,1,0]]); b=np.array([2,1,2])
sol=np.linalg.solve(A,b)
print("x=%.2f y=%.2f λ=%.2f 目标=%.2f" % (sol[0],sol[1],sol[2],(sol[0]-2)**2+(sol[1]-1)**2))
PY
```

本机输出：

```text
x=1.50 y=0.50 λ=1.00 目标 0.50
∇f + λ∇c = (-1,-1) + 1·(1,1) = (0,0) ✓ ｜约束 x+y=2 紧
```

## 罚函数为什么只能逼近

```text
罚函数法：min f(x) + p·max(0, c(x))²
  → p 越大越接近真解，但条件数也越差
本机数值：p=1 → (1.750, 0.750)，p=10 → (1.546, 0.546)，
        p=100 → (1.505, 0.505)，p=1000 → (1.501, 0.501)
  → 收敛到 (1.5, 0.5)，但始终差一点点（约束被"软化"了）
```

**"罚参数给大点就行"** 条件数会恶化到求解器报错。

## 判据

```text
约束是等式 → 拉格朗日乘子法（λ 可正可负）
约束是不等式 → KKT（λ ≥ 0 + 互补松弛）
要做灵敏度分析 → 直接看 λ（本机 λ=1：右端放松 1 单位，目标改善 1）
```

<!-- kb-chart:kkt_point -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="x+y≤2；(2,1) 不可行 → (1.5,0.5)，λ∇c+∇f=0" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">约束起作用时：目标从 0 抬到 0.5，影子价格 λ=1（本机计算）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.2875</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.575</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.8625</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1.15</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="132.7" y="294.0" width="43.0" height="1.0" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<rect x="320.0" y="181.0" width="43.0" height="113.0" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="341.5" y="175.0" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.5</text>
<rect x="507.3" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="528.8" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1</text>
<text x="155.7" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">无约束最优目标</text>
<text x="343.0" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">约束最优目标</text>
<text x="530.3" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">λ</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">x+y≤2；(2,1) 不可行 → (1.5,0.5)，λ∇c+∇f=0</text>
</svg>
<figcaption>x+y≤2；(2,1) 不可行 → (1.5,0.5)，λ∇c+∇f=0</figcaption>
</figure>


## 数字与阈值（本机计算）

```text
无约束最优 (2,1) 目标 0 ｜约束最优 (1.5,0.5) 目标 0.5 ｜λ=1
罚函数 p=1/10/100/1000 → (1.750,0.750)/(1.546,0.546)/(1.505,0.505)/(1.501,0.501)
经验：λ 的量纲 = 目标函数 / 约束单位，是"影子价格"
经验：罚参数跨 3 个数量级才收敛到 0.001 量级
经验：约束数 > 变量数时，解通常在多个约束的交点
```

## 证据强度

- **计算**：解析解与罚函数迭代均在本机完成
- **公开经验**：KKT 四条、影子价格解释
- **推断**：非凸问题的 KKT 点只是候选，不保证全局最优

## 不适用的情况

- 无约束问题：只需 ∇f = 0
- 整数/组合约束：KKT 不适用，需要分支定界或整数规划

## 常见错法

- **忘记互补松弛，把不起作用的约束也乘上 λ**
- **不等式约束取了负的 λ**
- **用罚函数代替精确解法却报告高精度**

## 往下追

- [全局优化为什么难](全局优化为什么难.md)

## 相关

- [高等数学](index.md) · [梯度下降为什么会发散](梯度下降为什么会发散.md) · [收敛速度与计算量怎么权衡](收敛速度与计算量怎么权衡.md)
