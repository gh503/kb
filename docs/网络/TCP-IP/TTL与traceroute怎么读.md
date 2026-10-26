# TTL 与 traceroute 怎么读

> **深度** 取舍 ｜ **类型** 实测 ｜ **链** 包是怎么走过去的

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [包怎么找到路](包怎么找到路.md) · [NAT与端口](NAT与端口.md) · [IPv6迁移要注意什么](IPv6迁移要注意什么.md) · <span class="kb-chain__now">TTL与traceroute怎么读</span>
</div>

## 结论

**TTL 是"还能走几跳"，不是"活了多久"；traceroute 靠的就是让它逐跳归零。**
本机实测到 `1.1.1.1` 三次 ping：**RTT 40.3 / 92.6 / 161.5 ms（mdev 50.9）**——
**同一目标抖动 4 倍**，说明路径上存在排队或代理，不能用单次结果判断"哪一跳慢"。

## 机制

```text
发送方设 TTL=N，每经过一个路由器减 1
减到 0 时，路由器回 ICMP Time Exceeded
traceroute 从 TTL=1 开始递增，逐个逼出路径上的路由器
```

**"TTL 是缓存时间"** 那是 DNS 的 TTL，同名字不同义。

## 本机可复现（已实测）

```bash
ping -c 3 -W 2 1.1.1.1
```

本机输出：

```text
3 packets transmitted, 3 received, 0% packet loss
rtt min/avg/max/mdev = 40.264/92.568/161.522/50.883 ms
```

## 读 traceroute 的三条纪律

```text
1. 星号（* * *）不代表断：很多路由器不回 ICMP
2. 某一跳延迟高但后面恢复正常 → 通常是那台设备"回包慢"，不是链路慢
3. 只看单次结果没有意义：至少跑 3 次，看稳定抬升的那一段
```

**"第 7 跳 300 ms，所以问题在第 7 跳"** 恰恰是最常见的误判。

## 初始 TTL 与跳数估算

```text
对端初始 TTL 常见 64 / 128 / 255（Linux / Windows / 网络设备）
收到 TTL = 初始 - 跳数
  → 收到 52 且对端是 Linux(64) → 约 12 跳
  → 收到 121 且对端是 Windows(128) → 约 7 跳
```

<!-- kb-chart:ttl_jitter -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="mdev 50.9；单次 traceroute 不能用来定位慢在哪一跳" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">同一目标三次 ping：40.3 / 92.6 / 161.5 ms，抖动 4 倍（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">ms</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">46.4312</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">92.8625</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">139.294</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">185.725</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="132.7" y="237.6" width="43.0" height="56.4" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="154.2" y="231.6" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">40.3</text>
<rect x="320.0" y="164.4" width="43.0" height="129.6" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="341.5" y="158.4" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">92.6</text>
<rect x="507.3" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="528.8" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">161.5</text>
<text x="155.7" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">min</text>
<text x="343.0" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">avg</text>
<text x="530.3" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">max</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">mdev 50.9；单次 traceroute 不能用来定位慢在哪一跳</text>
</svg>
<figcaption>mdev 50.9；单次 traceroute 不能用来定位慢在哪一跳</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
1.1.1.1：min 40.3 / avg 92.6 / max 161.5 ms，mdev 50.9（4 倍抖动）
经验：mdev / avg > 0.3 说明路径不稳定，先查本地出口与代理
经验：单跳延迟高但后续正常 → 忽略
经验：ICMP 被限速时，traceroute 的延迟数字不可信
```

## 证据强度

- **实测**：三档 RTT 与 mdev 来自本机 ping
- **公开经验**：星号含义、初始 TTL 惯例
- **推断**：本机经代理出网，路径与真实客户端差异很大

## 不适用的情况

- 应用层限速：ping 正常但业务慢，TTL 无关
- 有状态防火墙丢弃 ICMP：traceroute 全程星号也不代表不通

## 常见错法

- **拿单次 traceroute 定位故障点**
- **把 DNS 的 TTL 与 IP 的 TTL 混为一谈**
- **看到星号就判定链路中断**

## 往下追

- 回到本链起点：[包怎么找到路](包怎么找到路.md)

## 相关

- [TCP-IP](index.md) · [RTT是什么为什么它决定一切](RTT是什么为什么它决定一切.md) · [包怎么找到路](包怎么找到路.md)
