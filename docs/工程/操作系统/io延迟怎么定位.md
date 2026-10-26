# io延迟怎么定位

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 机器为什么突然变慢

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [内核参数怎么调才不背锅](内核参数怎么调才不背锅.md) · [页缓存与脏页回写](页缓存与脏页回写.md) · <span class="kb-chain__now">io延迟怎么定位</span> · [内存压力怎么看出来](内存压力怎么看出来.md)
</div>

## 结论

**平均延迟会骗人，要看分位数和"被卡住的时间占比"。**
本机实测：4 KB 的 `fsync` 跑 60 次，**p50 3.76 ms、p95 5.69 ms、max 6.05 ms**；
而 `/proc/pressure/io` 显示 `some avg300 = 26.55%`——**三成时间有进程在等 IO**。

## 三把尺子

```text
1. 延迟分布：p50 / p95 / p99（iostat 的 await 是平均值）
2. 阻塞时间：PSI 的 some/full（比利用率更接近体感）
3. 队列深度：设备队列排了多少（aqu-sz）
```

**"iostat 的 %util 到 100%"** 在 NVMe 上并不代表饱和，它只统计"有请求在飞"的时间。

## 本机可复现（已实测）

```bash
python3 - <<'PY'
import os, time, statistics
lat=[]
for _ in range(60):
    with open("/tmp/kbtest/fs.tmp","ab") as f:
        f.write(b"y"*4096); f.flush()
        t=time.perf_counter(); os.fsync(f.fileno()); lat.append((time.perf_counter()-t)*1000)
lat.sort(); print(round(statistics.median(lat),2), round(lat[56],2), round(lat[-1],2))
PY
cat /proc/pressure/io
```

本机输出：

```text
4 KB fsync × 60：p50 3.76 ms ｜ p95 5.69 ms ｜ max 6.05 ms
PSI io：some avg10=4.03 avg60=8.04 avg300=26.55 ｜ full avg10=0.05 avg300=12.44
```

## 定位顺序

```text
1. 先看 PSI：some 高 → 有人等 IO；full 高 → 全体都被卡住
2. 再看分位数：p50 正常但 p99 高 → 排队/抖动，不是带宽不够
3. 再看设备：iostat -x 1 的 r_await/w_await 与 aqu-sz
4. 最后看进程：iotop / pidstat -d 找出是谁在写
```

**"磁盘慢"** 有三种完全不同的原因：带宽满、队列深、单次延迟高。

## 判据

```text
p50 高、p99 接近 p50 → 设备本身慢（或同步写每次都要落盘）
p50 低、p99 高 → 排队（并发太高或回写集中）
PSI full 高但带宽低 → 小 IO 太多 / 元数据操作多
```

<!-- kb-chart:fsync_pct -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="PSI io some avg300 = 26.55%：三成时间有进程在等 IO" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">fsync 的分布比平均值有用：p50 3.76、p95 5.69、max 6.05 ms（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">ms</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1.73937</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">3.47875</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">5.21812</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">6.9575</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="132.7" y="153.5" width="43.0" height="140.5" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="154.2" y="147.5" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">3.76</text>
<rect x="320.0" y="81.4" width="43.0" height="212.6" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="341.5" y="75.4" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">5.69</text>
<rect x="507.3" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="528.8" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">6.05</text>
<text x="155.7" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">p50</text>
<text x="343.0" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">p95</text>
<text x="530.3" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">max</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">PSI io some avg300 = 26.55%：三成时间有进程在等 IO</text>
</svg>
<figcaption>PSI io some avg300 = 26.55%：三成时间有进程在等 IO</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
fsync 4 KB：p50 3.76 ms ｜ p95 5.69 ms ｜ max 6.05 ms（60 次）
PSI io：some avg300 26.55% ｜ full avg300 12.44%
经验：p99/p50 > 5 说明有排队，不是设备慢
经验：PSI some > 20% 就该查，full > 5% 已经很痛
经验：fsync 每次 3–6 ms 意味着单线程最多约 200 次/秒
```

## 证据强度

- **实测**：三组延迟与 PSI 数值来自本机
- **公开经验**：p99/p50 判据、PSI 阈值
- **推断**：云盘/网络存储的延迟分布更重尾，p99 常常是 p50 的 10 倍以上

## 不适用的情况

- 全内存负载：没有 IO，用 CPU/memory PSI 代替
- 顺序大 IO（备份、视频）：带宽是主指标，分位数意义小

## 常见错法

- **只看 `iostat` 的平均 await**
- **把 `%util` 当饱和度**
- **用 `dd` 测磁盘**（顺序写 + 缓冲区，测不出真实延迟）

## 往下追

- [内存压力怎么看出来](内存压力怎么看出来.md)

## 相关

- [操作系统](index.md) · [页缓存与脏页回写](页缓存与脏页回写.md) · [测试为什么越来越慢](../测试/测试为什么越来越慢.md)
