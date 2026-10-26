# 页表与 TLB 命中率

> **深度** 入门 ｜ **类型** 实测 ｜ **链** 机器到底在等什么

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> <span class="kb-chain__now">页表与 TLB 命中率</span> · [内存屏障与无锁队列](内存屏障与无锁队列.md) · [系统调用与vDSO](系统调用与vDSO.md) · [火焰图怎么读](火焰图怎么读.md)
</div>

## 结论

**每次内存访问都要先翻译地址，翻译结果放在 TLB 里；TLB 装不下，每次访问就多一次查表。**
本机实测随机访问：工作集 **64 KB 102 ns/次、4 MB 154 ns、32 MB 195 ns、256 MB 193 ns、1 GB 231 ns**——
从最小到最大慢 **2.3 倍**，这段额外开销主要就是 TLB 未命中与缓存未命中。

## 四个层次

```text
虚拟地址 → (TLB 查) → 物理地址 → (Cache 查) → 内存
TLB 命中：1 个周期量级
TLB 未命中：走 4 级页表（x86-64），4 次内存访问
大页（2 MB/1 GB）：一个 TLB 项覆盖更多内存 → 命中率上升
```

**"内存访问都一样快"** 在跨页、跨缓存行时完全不成立。

## 本机可复现（已实测）

```bash
python3 - <<'PY'
import array, random, time
def probe(mb):
    n=max(int(mb*1024*1024)//8, 8192)
    arr=array.array('q', range(n)); idx=[random.randrange(n) for _ in range(200000)]
    t=time.perf_counter()
    for i in idx: arr[i]
    return (time.perf_counter()-t)/len(idx)*1e9
for mb in (0.06, 4, 32, 256, 1024): print(mb, round(probe(mb),1))
PY
```

本机输出：

```text
0.06 MB 102 ns ｜ 4 MB 154 ns ｜ 32 MB 195 ns ｜ 256 MB 193 ns ｜ 1 GB 231 ns
```

## 怎么用上

```text
1. 顺序访问：一次 TLB 未命中，后面几千次都命中
2. 结构体拆分（SoA）：热数据集中，减少有效工作集
3. 大页：数据库、JVM 常用（2 MB 页把 TLB 覆盖率放大 512 倍）
4. 对齐与分块：按缓存行（64 B）/页（4 KB）边界组织数据
```

**"用链表更灵活"** 在遍历时几乎每一步都是一次新页访问。

<!-- kb-chart:tlb_steps -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="随机访问；台阶来自 TLB 与缓存未命中，2 MB 大页可放大 512 倍覆盖" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">工作集越大越慢：64 KB 102 ns → 1 GB 231 ns（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">ns</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">66.4125</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">132.825</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">199.237</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">265.65</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="95.2" y="194.2" width="43.0" height="99.8" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="116.7" y="188.2" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">102</text>
<rect x="207.6" y="143.3" width="43.0" height="150.7" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="229.1" y="137.3" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">154</text>
<rect x="320.0" y="103.1" width="43.0" height="190.9" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="341.5" y="97.1" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">195</text>
<rect x="432.4" y="105.1" width="43.0" height="188.9" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="453.9" y="99.1" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">193</text>
<rect x="544.8" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="566.3" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">231</text>
<text x="118.2" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">64 KB</text>
<text x="230.6" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">4 MB</text>
<text x="343.0" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">32 MB</text>
<text x="455.4" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">256 MB</text>
<text x="567.8" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1 GB</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">随机访问；台阶来自 TLB 与缓存未命中，2 MB 大页可放大 512 倍覆盖</text>
</svg>
<figcaption>随机访问；台阶来自 TLB 与缓存未命中，2 MB 大页可放大 512 倍覆盖</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
64 KB → 102 ns ｜4 MB → 154 ns ｜1 GB → 231 ns（2.3 倍）
L1 TLB 通常 64 项、L2 TLB 上千项；4 KB 页 → L2 覆盖约 4–8 MB
经验：工作集 > 8 MB 就开始吃 TLB 未命中
经验：2 MB 大页能把 TLB 覆盖放大 512 倍
经验：随机访问指针结构，延迟按 100–250 ns 估
```

## 证据强度

- **实测**：五档延迟来自本机（Python 循环开销约占 100 ns，所以真实差距更大）
- **公开经验**：TLB 容量量级、大页倍数
- **推断**：换语言后绝对值会降一个量级，但"跨工作集的台阶"仍在

## 不适用的情况

- 全部数据在 L1/L2 内：TLB 全命中，差异可忽略
- IO 密集型：等待磁盘的时间远大于地址翻译

## 常见错法

- **用链表遍历大数据集**
- **把冷热字段塞进同一个结构体**
- **以为加内存就能解决随机访问慢**

## 往下追

- [内存屏障与无锁队列](内存屏障与无锁队列.md)

## 相关

- [计算机](index.md) · [内存分几块](内存分几块.md) · [虚拟内存与缺页](虚拟内存与缺页.md)
