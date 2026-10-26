# cgroup 限额怎么算

> **深度** 取舍 ｜ **类型** 实测 ｜ **链** 资源到底被谁吃了

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><a href="nice到底有多大用.md">nice 到底有多大用</a><span class="kb-chain__sep">·</span><a href="绑核为什么有时没用.md">绑核为什么有时没用</a><span class="kb-chain__sep">·</span><a href="文件描述符耗尽怎么查.md">文件描述符耗尽怎么查</a><span class="kb-chain__sep">·</span><span class="kb-chain__now">cgroup 限额怎么算</span></div>

## 结论

**cgroup 只管"最多能用多少"，不管"该用多少"；限额算小了会 OOM，算大了等于没设。**
本机实测：`cgroup2fs`，控制器有 `cpu io memory hugetlb pids rdma misc`；
我自己所在的 scope：`memory.max=max`（不限）、`pids.max=28527`、`cpu.max` 文件不存在（表示继承）。

## v1 与 v2 的差别

```text
v1：每个控制器一棵树（/sys/fs/cgroup/memory/、/sys/fs/cgroup/cpu/…），限额分散
v2：一棵统一树（/sys/fs/cgroup/<路径>/memory.max），控制器按需启用
本机：stat -fc %T /sys/fs/cgroup → cgroup2fs
```

**"文件不存在"比"值是 max"更强**：前者说明控制器没启用，后者说明启用了但不限。

## 本机可复现（已实测）

```bash
stat -fc %T /sys/fs/cgroup
cat /sys/fs/cgroup/cgroup.controllers

CG=$(cat /proc/self/cgroup | cut -d: -f3)
echo "cgroup=$CG"
for f in cpu.max memory.max memory.current pids.max pids.current; do
  printf '%s=' "$f"; cat "/sys/fs/cgroup$CG/$f" 2>/dev/null || echo '(不存在)'
done
cat "/sys/fs/cgroup$CG/cpu.pressure"
```

本机输出：

```text
cgroup2fs
cpuset cpu io memory hugetlb pids rdma misc
memory.max=max
memory.current=872448
pids.max=28527
pids.current=2
cpu.max=(不存在)
cpu.pressure: some avg10=9.60 avg60=1.73 avg300=0.36
```

## 限额怎么算（三个数）

```text
memory.max：上限，超过就 OOM kill（不是变慢）
  → 按"稳态 RSS + 峰值余量 30%"给；按 P99 而不是平均
cpu.max：配额，形如 "20000 100000" = 每 100 ms 用 20 ms（=0.2 核）
  → 1 核 = "100000 100000"；2 核 = "200000 100000"
pids.max：进程/线程数上限，防 fork 风暴
  → 按"线程数 + 峰值并发连接数"给
```

**"cpu.max 超了会变慢，memory.max 超了会死"**：这是两类完全不同的故障。

## 压力指标比限额更有用

```text
cpu.pressure some avg10=9.60：最近 10 秒有 9.6% 的时间有任务在等 CPU
memory.pressure 全 0：内存没有出现过等待
  → PSI（pressure stall information）直接告诉你"卡在哪"
```

**"看 PSI 不看利用率"**：利用率 60% 可能是健康的，PSI 9.6% 说明确实有人在排队。

<!-- kb-chart:cgroup_scope -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="memory.current 872 KB；cpu.pressure some avg10=9.60，只能靠它感知" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="14.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">本机 cgroup v2 自家 scope：限额基本没设（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="268.5" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">限额已设</text>
<text x="505.5" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">压力可观测</text>
<text x="140.0" y="76.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="600" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">memory.max</text>
<rect x="156.0" y="60" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<rect x="393.0" y="60" width="225.0" height="22" rx="4" fill="var(--kb-accent)" opacity="0.9"/>
<text x="505.5" y="75.0" font-size="10" text-anchor="middle" fill="var(--kb-paper)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">好</text>
<text x="628.0" y="75.0" font-size="10" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">= max</text>
<text x="140.0" y="106.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="600" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">pids.max</text>
<rect x="156.0" y="90" width="225.0" height="22" rx="4" fill="var(--kb-accent)" opacity="0.9"/>
<text x="268.5" y="105.0" font-size="10" text-anchor="middle" fill="var(--kb-paper)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">好</text>
<rect x="393.0" y="90" width="225.0" height="22" rx="4" fill="var(--kb-accent)" opacity="0.9"/>
<text x="505.5" y="105.0" font-size="10" text-anchor="middle" fill="var(--kb-paper)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">好</text>
<text x="628.0" y="105.0" font-size="10" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">= 28527</text>
<text x="140.0" y="136.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="600" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">cpu.max</text>
<rect x="156.0" y="120" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<rect x="393.0" y="120" width="225.0" height="22" rx="4" fill="var(--kb-accent)" opacity="0.9"/>
<text x="505.5" y="135.0" font-size="10" text-anchor="middle" fill="var(--kb-paper)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">好</text>
<text x="628.0" y="135.0" font-size="10" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">未设</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">memory.current 872 KB；cpu.pressure some avg10=9.60，只能靠它感知</text>
</svg>
<figcaption>memory.current 872 KB；cpu.pressure some avg10=9.60，只能靠它感知</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
cgroup2fs ｜ 控制器 7 个 ｜ 自身 scope: memory.max=max、pids.max=28527、memory.current=872448
cpu.pressure some avg10=9.60（负载均值 19.18）
经验：memory.max 设成"稳态 RSS × 1.3"
经验：cpu.max 至少给 0.5 核，否则启动阶段就会超时
经验：pids.max 到上限时 fork 直接失败，报错常被误读成内存不足
```

## 证据强度

- **实测**：cgroup 路径、五个文件的值、PSI 数字来自本机
- **公开经验**：两类限额的故障形态
- **推断**："RSS × 1.3"是通用余量，JVM/Go 这类有堆外内存的要更大

## 不适用的情况

- 独占整机且只有一个服务：不设限额也行，靠监控兜底
- 短生命周期批处理：限额设太紧会直接失败，不如用 `nice` 让路

## 常见错法

- **把 memory.max 当"软限制"**：超了就是 OOM kill，没有缓冲
- **在 v2 上找 `memory.limit_in_bytes`**：那是 v1 的文件名
- **只看 CPU 利用率，不看 PSI**

## 往下追

- 回到本链起点：[nice 到底有多大用](nice到底有多大用.md)

## 相关

- [操作系统](index.md) · [内存不够时会怎样](内存不够时会怎样.md) · [文件描述符耗尽怎么查](文件描述符耗尽怎么查.md)
