# MTU与分片

> **深度** 入门 ｜ **类型** 实测 ｜ **链** 协议栈上的旋钮

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> <span class="kb-chain__now">MTU与分片</span> · [Nagle与延迟ACK](Nagle与延迟ACK.md) · [端口与连接上限](端口与连接上限.md) · [缓冲与带宽时延积](缓冲与带宽时延积.md)
</div>

## 结论

**一个包能装多少，决定了你要付多少"头部税"，也决定了丢一片要重传多少。**
本机实测：路径 MTU **1500**（`ping -M do -s 1472` 通、**1473 不通**）；实测网卡 lo **65536**、无线 **1500**。
换算成开销：MTU 1500 时头部占 **2.67%**，9000 时 **0.44%**，65536 时 **0.06%**。
更狠的是分片：**1% 丢包下，3 片的分片包整包丢失率 2.93%**。

## 三个数

```text
路径 MTU：这条路上单包上限（以太网 1500，隧道/VPN 常更小）
MSS = MTU − 40（IPv4 头 20 + TCP 头 20）
分片：超过 MTU 的包被拆开，丢任意一片，整个包都要重传
```

**"MTU 是链路属性，不是协议属性"**：同一条 TCP 连接，路径变了，能过的包也变了。

## 本机可复现（已实测）

```bash
ping -c1 -M do -s 1472 192.168.1.1   # 通
ping -c1 -M do -s 1473 192.168.1.1   # 100% packet loss（PMTU=1500）
ip link show | grep mtu              # lo 65536、wlo1 1500、eno1 1500
```

```text
本机输出：size 1472 → 1 received ｜ size 1473 → 100% packet loss
MTU  1500：净荷 1460，头开销 2.67%
MTU  9000：净荷 8960，头开销 0.44%
MTU 65536：净荷 65496，头开销 0.06%
```

## 分片的代价是乘法

```text
一个 3 片的包：1% 丢包 → 整包失败 1 − 0.99³ = 2.97%（本机模拟 2.93%）
一个 10 片的包：1 − 0.99¹⁰ = 9.6%
  → 分片越多，重传概率越接近"片数 × 丢包率"
```

**"大包更快"** 只在没有丢包时成立；有丢包时，大包是放大器。

## 怎么避免踩到分片

```text
1. 别在应用层发超过 MSS 的"单条消息"（按 MTU 切块）
2. 隧道/VPN 场景把 MTU 调小（常见 1400 或 1280）
3. 依赖 PMTUD 时，注意有的防火墙把 ICMP "frag needed" 全丢了 → 黑洞
4. 判据：TCP 通、大包不通、小包通 → 先怀疑 MTU 黑洞
```

<!-- kb-chart:mtu_overhead -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="路径 MTU 实测 1500：ping -M do -s 1472 通、1473 不通" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">MTU 越大，头部税越低：2.67% → 0.44% → 0.06%（本机计算）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">%</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="1.0" y="233.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.767625</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1.53525</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">2.30287</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">3.0705</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="132.7" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="154.2" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">2.67</text>
<rect x="320.0" y="256.7" width="43.0" height="37.3" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="341.5" y="250.7" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.44</text>
<rect x="507.3" y="288.9" width="43.0" height="5.1" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="528.8" y="282.9" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0.06</text>
<text x="155.7" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1500</text>
<text x="343.0" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">9000</text>
<text x="530.3" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">65536</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">路径 MTU 实测 1500：ping -M do -s 1472 通、1473 不通</text>
</svg>
<figcaption>路径 MTU 实测 1500：ping -M do -s 1472 通、1473 不通</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
路径 MTU 1500（1472 通 / 1473 不通）｜ lo 65536 ｜ 无线 1500
头开销：1500 → 2.67% ｜ 9000 → 0.44% ｜ 65536 → 0.06%
分片丢失：3 片、1% 丢包 → 2.93%（理论 2.97%）
经验：隧道场景把 MTU 设 1400，能避开绝大多数 PMTU 黑洞
经验：单条消息控制在 1200 字节以内，跨网络最保险
```

## 证据强度

- **实测**：PMTU 探测、三种 MTU 的头开销、分片丢失率为本机运行
- **公开经验**：隧道 MTU 1400、消息 1200 字节
- **推断**：真实网络的丢包不独立，分片放大效应可能更大

## 不适用的情况

- 纯回环通信：MTU 65536，分片几乎不会发生
- 已启用 Path MTU Discovery 且 ICMP 未被拦：内核会自己调

## 常见错法

- **把 MTU 当成"越大越好"，忽略路径上的小 MTU 链路**
- **防火墙拦掉 ICMP frag needed，制造黑洞**
- **应用层一条消息几十 KB，还指望 TCP 帮你切**

## 往下追

- [Nagle与延迟ACK](Nagle与延迟ACK.md)

## 相关

- [TCP-IP](index.md) · [RTT是什么为什么它决定一切](RTT是什么为什么它决定一切.md) · [带宽延迟积是什么](带宽延迟积是什么.md)
