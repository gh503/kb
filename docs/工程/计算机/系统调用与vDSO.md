# 系统调用与 vDSO

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 机器到底在等什么

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [页表与TLB命中率](页表与TLB命中率.md) · [内存屏障与无锁队列](内存屏障与无锁队列.md) · <span class="kb-chain__now">系统调用与vDSO</span> · [火焰图怎么读](火焰图怎么读.md)
</div>

## 结论

**同一个"读时间"，走 vDSO 是 123 ns，真进内核要 771 ns——差 6 倍。**
本机实测 20 万次：`time.time()` **123 ns/次**（vDSO）、`os.getpid()` **771 ns**（系统调用）、`read(/dev/null, 1)` **1,064 ns**。

## 系统调用贵在哪

```text
1. 特权级切换：用户态 → 内核态 → 用户态
2. 寄存器保存/恢复、栈切换
3. 分支预测与缓存局部性被打断（Spectre 缓解又加了一层）
4. 参数校验与权限检查
```

**"一次几微秒不算什么"** 在每秒百万次的循环里就是几十秒。

## 本机可复现（已实测）

```bash
python3 - <<'PY'
import os, time
N=200000
def t(f):
    s=time.perf_counter()
    for _ in range(N): f()
    return (time.perf_counter()-s)/N*1e9
print("time.time  %.0f ns" % t(time.time))
print("getpid     %.0f ns" % t(os.getpid))
fd=os.open("/dev/null", os.O_RDONLY)
print("read       %.0f ns" % t(lambda: os.read(fd,1)))
PY
```

本机输出：

```text
time.time()（vDSO）123 ns ｜ os.getpid()（系统调用）771 ns ｜ read(/dev/null) 1,064 ns
```

## vDSO 是什么

```text
内核把一小段代码映射进用户空间（vdso），读时钟、gettimeofday 等只读操作直接在这跑
  → 不切换特权级，所以 123 ns
  → 只适用于"内核能安全共享的数据"（时间、CPU 信息）
```

**"所有系统调用都能绕过"** 不能：涉及权限、IO、状态变更的必须进内核。

## 减少系统调用的三种手段

```text
1. 批量：readv/writev、recvmmsg、io_uring 一次提交多件事
2. 缓冲：用户态攒够再写（stdio 缓冲、批量提交）
3. 共享内存/无锁环形缓冲：跨进程传数据不进内核
```

**"加线程"** 不减少系统调用次数，只是让它们并行等待。

<!-- kb-chart:vdso_gap -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="特权级切换是主要成本；批量系统调用能摊薄它" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">vDSO 123 ns vs 系统调用 771 ns vs read 1,064 ns（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">ns</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">305.9</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">611.8</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">917.7</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1,224</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="132.7" y="267.9" width="43.0" height="26.1" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="154.2" y="261.9" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">123</text>
<rect x="320.0" y="130.2" width="43.0" height="163.8" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="341.5" y="124.2" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">771</text>
<rect x="507.3" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="528.8" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1,064</text>
<text x="155.7" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">time.time (vDSO)</text>
<text x="343.0" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">getpid</text>
<text x="530.3" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">read(/dev/null)</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">特权级切换是主要成本；批量系统调用能摊薄它</text>
</svg>
<figcaption>特权级切换是主要成本；批量系统调用能摊薄它</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
vDSO 123 ns ｜ 系统调用 771 ns（getpid）｜ read(/dev/null) 1,064 ns
经验：系统调用约 0.5–2 µs，vDSO 约 20–150 ns（差 5–10 倍）
经验：每秒 100 万次系统调用 ≈ 1 秒纯开销
经验：小 IO 合并成批量（writev / 4 KB 以上）能省一个量级
```

## 证据强度

- **实测**：三个数值来自本机
- **公开经验**：0.5–2 µs 量级、批量合并
- **推断**：容器/虚拟化下系统调用更贵（多一层拦截），倍数会变大

## 不适用的情况

- 每请求只几次系统调用：开销可忽略
- 纯计算负载：瓶颈不在内核边界

## 常见错法

- **循环里逐字节 `write`**
- **用 `getpid()` 之类做高频逻辑**
- **以为 `time.time()` 便宜就可以在热路径里随便调**（相对便宜，但不是免费）

## 往下追

- [火焰图怎么读](火焰图怎么读.md)

## 相关

- [计算机](index.md) · [系统调用为什么慢](系统调用为什么慢.md) · [页表与TLB命中率](页表与TLB命中率.md)
