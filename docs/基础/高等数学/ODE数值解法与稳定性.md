# ODE 数值解法与稳定性

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 数值方法的边界

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [自动微分怎么做到机器精度](自动微分怎么做到机器精度.md) · <span class="kb-chain__now">ODE数值解法与稳定性</span> · [病态问题与预条件](病态问题与预条件.md) · [随机梯度的方差缩减](随机梯度的方差缩减.md)
</div>


## 结论

**步长不是"越小越准"，有一道硬门槛：超过就炸。**
本机实测 y′=−50y、y(0)=1、求 y(1)（真值 1.929e−22）：
**Euler h=0.05 得到 3,325（发散）；h=0.01 得到 7.889e−31；RK4 h=0.05 得到 1.727e−4。**

## 稳定性的判据

```text
Euler 的放大因子：1 + hλ
  λ=−50、h=0.05 → 1−2.5 = −1.5，|−1.5|>1 → 误差每步放大 1.5 倍 → 炸
  h=0.02 → 1−1 = 0（恰好一步归零，偶然的"完美"）
  h=0.01 → 0.5，稳定
门槛：h < 2/|λ| = 0.04
```

**"刚性方程"** 就是指 |λ| 很大、而解本身变化很慢——显式方法被稳定性逼着用极小步长。

## 本机可复现（已实测）

```bash
python3 - <<'PY'
import math
def euler(h):
    y, t = 1.0, 0.0
    while t < 1 - 1e-12:
        y += h*(-50*y); t += h
    return y
def rk4(h):
    y, t = 1.0, 0.0
    g = lambda y: -50*y
    while t < 1 - 1e-12:
        k1 = g(y); k2 = g(y+h*k1/2); k3 = g(y+h*k2/2); k4 = g(y+h*k3)
        y += h*(k1+2*k2+2*k3+k4)/6; t += h
    return y
truth = math.exp(-50)
for h in (0.05, 0.02, 0.01, 0.005):
    print(f"Euler h={h}: {euler(h):.3e}（真值 {truth:.3e}，|1-50h|={abs(1-50*h):.2f}）")
for h in (0.05, 0.02, 0.01):
    print(f"RK4   h={h}: {rk4(h):.3e}")
PY
```

本机输出：

```text
Euler h=0.05: 3.325e+03（真值 1.929e-22，|1-50h|=1.50）
Euler h=0.02: 0.000e+00（|1-50h|=0.00）
Euler h=0.01: 7.889e-31（0.50）
Euler h=0.005: 1.029e-25（0.75）
RK4   h=0.05: 1.727e-04
RK4   h=0.02: 5.030e-22
RK4   h=0.01: 2.007e-22
```

## 三种方法的取舍

```text
Euler：一阶、最简单、稳定性区间最小（h < 2/|λ|）
RK4：四阶、每步四次求值、稳定性区间约 h < 2.8/|λ|，精度高得多
隐式（后向 Euler/BDF）：无条件稳定，但每步要解方程
```

**"刚性就用隐式"**：显式方法在刚性问题上不是"慢"，是"根本算不出"。

## 怎么判断遇上了刚性问题

```text
1. 缩小步长后结果突然从发散变正常（跨过稳定性边界）
2. 解变化很慢，但步长被逼得极小（效率与精度不匹配）
3. 系统里有相差 3 个数量级以上的时间常数
```

**"步长减半结果大变"** 通常不是精度问题，是稳定性问题。

<!-- kb-chart:ode_stable -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="放大因子超过 1 就炸：h=0.05 得 3325，真值 1.9e−22" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">Euler 的稳定门槛：h=0.05 直接发散（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="298.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.43125</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.8625</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1.29375</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1.725</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="109.2" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="130.8" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1.5</text>
<rect x="249.8" y="294.0" width="43.0" height="1.0" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<rect x="390.2" y="218.6" width="43.0" height="75.4" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="411.8" y="212.6" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.5</text>
<rect x="530.8" y="181.0" width="43.0" height="113.0" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="552.2" y="175.0" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.75</text>
<text x="132.2" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">h=0.05</text>
<text x="272.8" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">h=0.02</text>
<text x="413.2" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">h=0.01</text>
<text x="553.8" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">h=0.005</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">放大因子超过 1 就炸：h=0.05 得 3325，真值 1.9e−22</text>
</svg>
<figcaption>放大因子超过 1 就炸：h=0.05 得 3325，真值 1.9e−22</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
λ=−50：Euler 稳定门槛 h<0.04；h=0.05 发散到 3,325（真值 1.9e−22）
RK4 h=0.05 误差 1.7e−4（相对真值差 18 个数量级，但没炸）
Euler h=0.02 恰好 0（放大因子为 0 的巧合）
经验：显式 Euler 稳定区间 h < 2/|λ|max；RK4 约 2.8/|λ|max
经验：刚性比 |λ|max/|λ|min > 100 就该考虑隐式
```

## 证据强度

- **实测**：七组数值来自本机 Python
- **公开经验**：稳定区间常数与刚性判据
- **推断**：这里的"炸"是舍入误差被放大，实际系统还会有截断误差叠加

## 不适用的情况

- 非刚性、短时间积分：Euler 足够
- 需要高精度长时积分（天体力学）：用辛方法保结构

## 常见错法

- **看到结果发散就以为"步长还不够小"**
- **用 Euler 解刚性方程，然后归因于"精度不够"**
- **h=0.02 恰好归零就以为方法很准**

## 往下追

- [病态问题与预条件](病态问题与预条件.md)

## 相关

- [高等数学](index.md) · [梯度下降为什么会发散](梯度下降为什么会发散.md) · [收敛速度与计算量怎么权衡](收敛速度与计算量怎么权衡.md)
