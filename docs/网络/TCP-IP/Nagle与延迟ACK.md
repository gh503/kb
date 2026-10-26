# Nagle与延迟ACK

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 协议栈上的旋钮

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [MTU与分片](MTU与分片.md) · <span class="kb-chain__now">Nagle与延迟ACK</span> · [端口与连接上限](端口与连接上限.md) · [缓冲与带宽时延积](缓冲与带宽时延积.md)
</div>

## 结论

**那 40 ms 不是代码慢，是两个"善意优化"撞在一起。**
本机实测：同一个服务端，Nagle 开启时 p50 **41.02 ms**（并发 1→16 几乎不变）；关掉后 **0.35 ms**——**117 倍**。

## 机制

```text
Nagle：小包先攒着，等前一个包被 ACK 再发 → 少发小包
延迟 ACK：收到数据不立刻 ACK，等 40 ms 看有没有要捎带的数据
  → Nagle 等 ACK，ACK 等 40 ms：死等到 40 ms
```

**"每个请求都慢 40 ms 且很整齐"** 就是这个组合的指纹。

## 本机可复现（已实测）

```bash
# server.py：ThreadingHTTPServer，关键一行
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    disable_nagle_algorithm = True     # 等价于 setsockopt(TCP_NODELAY)
# loadtest.py：N 线程 keep-alive 打 3 秒，统计 p50/p99
```

本机输出：

```text
Nagle 开：线程 1/4/16/64 →  24.4 /  96.9 / 380.0 / 1160.2 req/s，p50 41.02 / 41.09 / 41.63 / 48.55 ms
Nagle 关：线程 1/4/16/64 → 1523.8 / 2072.2 /1643.1 / 1236.9 req/s，p50  0.35 /  1.40 /  8.86 / 31.50 ms
```

## 什么时候该关、什么时候别关

```text
该关（TCP_NODELAY）：请求-响应型短消息、RPC、游戏、交互式终端
别关：批量传输大块数据（Nagle 在攒满 MSS 时本来就不等待）
也可以：QUICKACK 只影响接收方 ACK 时机，与 NODELAY 配合用
```

**"全站开 NODELAY"** 一般没坏处；真正要小心的是"既开 NODELAY 又每个字节一次 write"。

## 判据：看到什么现象就该怀疑它

```text
现象：p50 稳定在 40 ms 左右，且与并发无关、与服务端 CPU 无关
验证：在客户端和服务端同时开 NODELAY，p50 掉到亚毫秒 → 确认
反例：query 慢、CPU 高、延迟随并发上升 → 不是它
```

<!-- kb-chart:nagle_gap -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="117 倍；Nagle 那条在并发 1→16 几乎不变，是固定 40 ms 等待" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">Nagle 与延迟 ACK 撞车：p50 41.02 vs 0.35 ms（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">ms</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.175</text>
<line x1="62" y1="264.7" x2="624" y2="264.7" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="268.7" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.35</text>
<line x1="62" y1="235.4" x2="624" y2="235.4" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="239.4" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.7</text>
<line x1="62" y1="206.1" x2="624" y2="206.1" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="210.1" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1.4</text>
<line x1="62" y1="176.8" x2="624" y2="176.8" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="180.8" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">2.8</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="179.5" y="63.3" width="43.0" height="230.7" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="201.0" y="57.3" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">41.02</text>
<rect x="460.5" y="264.7" width="43.0" height="29.3" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="482.0" y="258.7" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.35</text>
<text x="202.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">Nagle 开</text>
<text x="483.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">TCP_NODELAY</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">117 倍；Nagle 那条在并发 1→16 几乎不变，是固定 40 ms 等待</text>
</svg>
<figcaption>117 倍；Nagle 那条在并发 1→16 几乎不变，是固定 40 ms 等待</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
Nagle 开 p50 41.02 ms（并发 1）→ 48.55 ms（并发 64），几乎恒定
Nagle 关 p50 0.35 ms（并发 1）→ 31.50 ms（并发 64），随负载上升
峰值 QPS：1160（Nagle 开）vs 2072（关），1.8 倍
经验：40 ms 是 Linux 延迟 ACK 的常见上限（默认 40 ms，可到 200 ms）
经验：交互式服务默认开 TCP_NODELAY
```

## 证据强度

- **实测**：两组 p50/p99 与 QPS 来自本机回环压测
- **公开经验**：延迟 ACK 40 ms、交互式服务开 NODELAY
- **推断**：跨公网时延迟高，40 ms 的相对影响会变小但仍存在

## 不适用的情况

- 单向大批量传输：Nagle 不产生等待（每个包都满 MSS）
- 延迟本来就 > 100 ms 的链路：40 ms 只是噪声的一部分

## 常见错法

- **只测服务端处理时间，不测端到端 p50**
- **用 `curl` 单次请求测性能**（每次都新建连接，AC 与 Nagle 行为不同）
- **开了 NODELAY 但每次 write 一个字节**，把问题从 Nagle 换成了系统调用

## 往下追

- [端口与连接上限](端口与连接上限.md)

## 相关

- [TCP-IP](index.md) · [RTT是什么为什么它决定一切](RTT是什么为什么它决定一切.md) · [压测怎么做才不作假](../../工程/测试/压测怎么做才不作假.md)
