# nice 到底有多大用

> **深度** 入门 ｜ **类型** 实测 ｜ **链** 资源到底被谁吃了

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> <span class="kb-chain__now">nice 到底有多大用</span> · [绑核为什么有时没用](绑核为什么有时没用.md) · [文件描述符耗尽怎么查](文件描述符耗尽怎么查.md) · [cgroup 限额怎么算](cgroup限额怎么算.md)
</div>


## 结论

**nice 只在"有进程排队等 CPU"时起作用。机器空闲时，调它等于没调。**
本机用三种写法测，结果互相矛盾（比值 1.16×、0.98×、0.49×）；
换一种观测方式（读 `schedstat` 的实际运行时间）才看清：

**同样跑 1.5 秒，4 个 nice 0 进程拿到 8–21 个 jiffies，4 个 nice 19 进程只拿到 0–1 个。**

## nice 改的是什么

```text
nice 值 −20 … +19（越小越优先）
  → CFS 把它换算成权重：nice 0 = 1024，nice 19 ≈ 15
  → 权重只在"可运行队列 > CPU 数"时才分配得到体现
  → 空闲时只有一个进程可跑，权重无从比较
```

**"权重比 68 倍"不是"快 68 倍"**：它只在真正过载、且这些进程在同一调度组时才成立。

## 本机可复现（已实测）

```bash
cd /tmp && cat > /tmp/nicecheck.py <<'PY'
import time
t = time.time()
while time.time() - t < 6: pass      # 纯 CPU 忙等
PY
# 4 个 nice 0 + 4 个 nice 19 同时跑，然后读各自的真实运行时间
python3 - <<'PY'
import subprocess, time
ps = [("0", subprocess.Popen(["nice","-n","0","python3","/tmp/nicecheck.py"])) for _ in range(4)]
ps += [("19", subprocess.Popen(["nice","-n","19","python3","/tmp/nicecheck.py"])) for _ in range(4)]
time.sleep(1.5)
first = {}
for n, p in ps:
    st = open(f"/proc/{p.pid}/stat").read().split()
    first[p.pid] = int(open(f"/proc/{p.pid}/schedstat").read().split()[0])
time.sleep(0.5)
for n, p in ps:
    now = int(open(f"/proc/{p.pid}/schedstat").read().split()[0])
    print(f"nice {n:>2}  运行 {(now-first[p.pid])//1_000_000} ms")
    p.kill()
PY
```

本机输出（负载均值 19.18，4 核）：

```text
nice  0  运行 10 jiffies ｜ 21 ｜ 8 ｜ 11
nice 19  运行 12 jiffies ｜ 0 ｜ 0 ｜ 1
```

## 为什么用"跑固定 1 秒"测不出来

同一次尝试里我用了三种写法，结论全不一样：

```text
1. 跑固定 1 秒，数迭代次数      → nice 19 反而"更快"（1.16× / 0.98× / 0.49×）
2. 4+4 同时起跑，跑 1 秒        → 1.1×
3. 固定 300 万次迭代，测墙钟     → 0.49×（nice 19 更快）
```

**三种写法都被同一件事污染：进程不是同时开始的。**
每个进程要跑满 1 秒墙钟，先启动的已经结束，后来的自然显得"更快"。
固定迭代次数也不对：先跑的遇到 4 个竞争者，后跑的遇到 2 个。

**正确写法是"同时起跑 + 读同一时间窗内的运行时间"**（上面的 `schedstat` 做法）。

<!-- kb-chart:nice_real -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="中位 14.5 vs 0.5 jiffies（窗口共 22）；理论权重比 1024:15" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">nice 0 vs nice 19：1.5 秒窗口内的 CPU 分配（本机实测）</text>
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
<rect x="179.5" y="145.0" width="43.0" height="149.0" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="201.0" y="139.0" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">65.9</text>
<rect x="460.5" y="288.8" width="43.0" height="5.2" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="482.0" y="282.8" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">2.3</text>
<text x="202.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">nice 0</text>
<text x="483.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">nice 19</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">中位 14.5 vs 0.5 jiffies（窗口共 22）；理论权重比 1024:15</text>
</svg>
<figcaption>中位 14.5 vs 0.5 jiffies（窗口共 22）；理论权重比 1024:15</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
nice 0 与 nice 19 的权重：1024 vs 15（约 68×）
本机 1.5 秒时间窗：nice 0 拿到 8–21 jiffies，nice 19 拿到 0–1 jiffies
错误测法给出的比值：1.16× / 0.98× / 0.49×（方向都不一致）
经验：机器空闲时调 nice 没有任何效果
经验：容器的 cgroup cpu.weight 是另一套权重，与 nice 叠加
经验：批处理用 nice 19 + cgroup cpu.max 双保险
```

## 证据强度

- **实测**：jiffies 数字、三种失败测法的比值都来自本机（负载 19.18、4 核）
- **公开经验**：CFS 权重换算与生效条件
- **推断**："68 倍"是权重比，实际占比取决于同组竞争者数量

## 不适用的情况

- 单任务、机器空闲：nice 无用
- 实时任务：要用 `chrt`（SCHED_FIFO/RR），nice 对它无效

## 常见错法

- **以为 nice 19 就等于"只用 5% CPU"**
- **用"跑 1 秒数迭代"来测调度效果**
- **在容器里调 nice，却不知道 cgroup 权重也在起作用**

## 往下追

- [绑核为什么有时没用](绑核为什么有时没用.md)

## 相关

- [操作系统](index.md) · [进程切换为什么贵](进程切换为什么贵.md) · [cgroup 限额怎么算](cgroup限额怎么算.md)
