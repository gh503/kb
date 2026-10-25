# 为什么每次写完就 fsync 会慢一千六百倍

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 文件写下去之后

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><a href="写文件到底写到了哪.md">写文件到底写到了哪</a><span class="kb-chain__sep">·</span><span class="kb-chain__now">为什么每次写完就fsync会慢一千六百倍</span><span class="kb-chain__sep">·</span><a href="文件删了空间没回来.md">文件删了空间没回来</a><span class="kb-chain__sep">·</span><a href="小文件为什么拖垮系统.md">小文件为什么拖垮系统</a></div>

## 结论

**每次写完就 `fdatasync`，等于把"内存速度"换成"磁盘每次等待 7.4 ms"。**
本机实测：同样 8 MB，不 sync 是 **8.91 ms**，每次都 sync 是 **14,820 ms**——**1,663 倍**。

## 账是这么算的

```text
不 sync：2000 次内存拷贝，共 8.91 ms
每次 sync：2000 次 fsync，每次约 7.41 ms 等磁盘确认
         2000 × 7.41 ms = 14,820 ms
```

**"每次 7.41 ms"是这块盘的持久化延迟**，不是它慢——是"等确认"本身要一个往返。

## 本机可复现（已实测）

```c
/* 同一份数据，只差一行 fdatasync */
for (i=0;i<2000;i++){ write(fd,buf,4096); }
/* vs */
for (i=0;i<2000;i++){ write(fd,buf,4096); fdatasync(fd); }
```

本机输出：

```text
buffered write   2000×4KB    8.91 ms  ( 919.7 MB/s)
write+fdatasync  2000×4KB 14820.18 ms  (   0.6 MB/s)
```

**0.6 MB/s 就是"每次写完都等磁盘"的真实吞吐**。

## 正确做法：攒一批再 sync

```text
每 N 条或每 T 毫秒 fsync 一次（N 常取 100–1000，T 取 100 ms–1 s）
代价：崩溃时最多丢 N 条 / T 毫秒的数据
```

**这是"持久性"和"吞吐"的交换点**，没有免费的选项：

| 策略 | 吞吐 | 崩溃丢多少 |
| --- | --- | --- |
| 每条 fsync | 0.6 MB/s | 0 条 |
| 每 100 条 fsync | 约 50 MB/s | ≤ 100 条 |
| 从不 fsync | 920 MB/s | 自上次回写后的全部 |

**数据库的 group commit 就是这张表的工程化**：把并发事务的 sync 合并成一次。

## 什么时候必须每条都 sync

```text
记账、订单状态：丢一条就是错账
分布式协调（etcd/raft 日志）：丢了会破坏一致性
其余大多数：可以按批
```

**判断标准是"丢了这条，业务上能不能重算"**，能重算就别每条 sync。

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="同一份 8 MB 数据，三种写法差三个数量级（本机实测）" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="14.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">同一份 8 MB 数据，三种写法差三个数量级（本机实测）</text>
<text x="632.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">ms</text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="180.0" y="69.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">O_DIRECT 写入</text>
<rect x="190" y="54" width="179.8" height="22" rx="4" fill="var(--kb-warn)" opacity="0.85"/>
<text x="377.8" y="69.0" font-size="12" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">117.57 ms</text>
<text x="180.0" y="115.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">buffered 写入</text>
<rect x="190" y="100" width="14.3" height="22" rx="4" fill="var(--kb-accent)" opacity="0.85"/>
<text x="212.3" y="115.0" font-size="12" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">8.91 ms</text>
<text x="180.0" y="161.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">每条 write 后 fdatasync</text>
<rect x="190" y="146" width="490.0" height="22" rx="4" fill="var(--kb-warn)" opacity="0.85"/>
<text x="688.0" y="161.0" font-size="12" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">14820.2 ms</text>
<text x="190.0" y="200.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">对数刻度。中间那条最快，是因为它只写了内存；最慢那条每次都在等磁盘确认。</text>
</svg>
<figcaption>同一份 8 MB 数据，三种写法差三个数量级（本机实测）</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
不 sync            8.91 ms / 8 MB（919.7 MB/s）
每次 fdatasync 14820.18 ms / 8 MB（0.6 MB/s）
单次 sync 等待     7.41 ms
倍数               1,663×
经验批量           100–1000 条或 100 ms–1 s 一次
```

## 证据强度

- **实测**：两组耗时与单次 sync 延迟为本机输出
- **公式**：总时间 ≈ 次数 × 单次 sync 延迟
- **公开经验**：group commit 的批大小区间

## 不适用的情况

- 写日志且能容忍丢最后几条：按批 sync 即可
- 文件系统已 `sync` 挂载（如某些 U 盘）：每次 write 都同步，策略无从谈起

## 常见错法

- **循环里每条都 fsync**：吞吐掉三个数量级
- **完全不 sync 却承诺持久化**
- **以为 `fdatasync` 与 `fsync` 一样贵**：前者只保证数据，不保证元数据，通常略便宜

## 往下追

- [文件删了空间没回来](文件删了空间没回来.md)

## 相关

- [操作系统](index.md) · [写文件到底写到了哪](写文件到底写到了哪.md)
