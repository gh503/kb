# NAT 与端口

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 包是怎么走过去的

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [包怎么找到路](包怎么找到路.md) · <span class="kb-chain__now">NAT与端口</span> · [IPv6迁移要注意什么](IPv6迁移要注意什么.md) · [TTL与traceroute怎么读](TTL与traceroute怎么读.md)
</div>

## 结论

**家里多台机器共用一个公网 IP，靠的是"端口 + 连接跟踪表"这一层映射。**
本机实测：NAT 连接跟踪表用了 **289 / 262,144** 条；一台机器可用的临时端口 **28,232 个**（32768–60999）——
**这就是"单 IP 能同时开多少条出去连接"的硬上限**。

## 三个东西

```text
NAT：改写源 IP/端口（SNAT）或目的 IP/端口（DNAT）
conntrack：记录每条连接的五元组映射，表满就丢新连接
端口：区分同一 IP 上的多条连接；临时端口只有约 2.8 万个
```

**"内网机器有 IP 就能被访问"** 在 NAT 后面不成立：外面没有到它的映射。

## 本机可复现（已实测）

```bash
cat /proc/sys/net/netfilter/nf_conntrack_count   # 289
cat /proc/sys/net/netfilter/nf_conntrack_max     # 262144
cat /proc/sys/net/ipv4/ip_local_port_range        # 32768 60999
```

本机输出：

```text
conntrack 289 / 262,144 ｜ 临时端口 28,232 个
```

## 端口耗尽的算术

```text
单出口 IP、单目的地址：最多约 28,232 条并发连接（每连接一个源端口）
每多一个目的 IP，可再乘一份（五元组不同）
经验：短连接频繁时，TIME_WAIT 会占着端口约 60 s，把上限压低一半
```

**"加到 10 万并发"** 在单 IP 单目的下做不到——不是带宽问题，是端口不够。

## 三种穿透方式

```text
端口映射（DNAT）：路由上把公网端口转到内网 IP，最直接
反向隧道：内网主动连出去，外面通过这条连接进来
打洞（STUN/UPnP）：依赖 NAT 类型，对称 NAT 基本失败
```

<!-- kb-chart:nat_ports -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="单 IP 单目的并发上限 ≈ 2.8 万；短连接被 TIME_WAIT 再压一半" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">NAT 的两条硬上限：conntrack 262,144、临时端口 28,232（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">个</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">144.5</text>
<line x1="62" y1="272.0" x2="624" y2="272.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="276.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">289</text>
<line x1="62" y1="250.0" x2="624" y2="250.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="254.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">578</text>
<line x1="62" y1="228.0" x2="624" y2="228.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="232.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1,156</text>
<line x1="62" y1="206.1" x2="624" y2="206.1" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="210.1" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">2,312</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="132.7" y="56.0" width="43.0" height="238.0" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="154.2" y="50.0" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">262,144</text>
<rect x="320.0" y="272.0" width="43.0" height="22.0" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="341.5" y="266.0" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">289</text>
<rect x="507.3" y="126.7" width="43.0" height="167.3" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="528.8" y="120.7" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">28,232</text>
<text x="155.7" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">conntrack 上限</text>
<text x="343.0" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">conntrack 已用</text>
<text x="530.3" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">临时端口</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">单 IP 单目的并发上限 ≈ 2.8 万；短连接被 TIME_WAIT 再压一半</text>
</svg>
<figcaption>单 IP 单目的并发上限 ≈ 2.8 万；短连接被 TIME_WAIT 再压一半</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
conntrack 289/262,144（0.1%）｜临时端口 28,232 个
经验：单 IP 单目的并发上限 ≈ 2.8 万，短连接按 1/2 打折
经验：conntrack 用到 70% 就要扩容或缩短连接寿命
经验：对称 NAT 下打洞成功率极低，别把它当唯一方案
```

## 证据强度

- **实测**：三个数值来自本机 `/proc`
- **公开经验**：2.8 万上限、70% 水位
- **推断**：家用路由的 conntrack 表通常只有几千到几万条，比本机更早打满

## 不适用的情况

- 全 IPv6 且无 NAT：没有端口映射问题（但防火墙策略仍在）
- 纯内网通信：不经过 NAT

## 常见错法

- **把 NAT 当防火墙**
- **以为端口映射能提升带宽**
- **短连接打满端口后加机器，却没查 TIME_WAIT**

## 往下追

- [IPv6迁移要注意什么](IPv6迁移要注意什么.md)

## 相关

- [TCP-IP](index.md) · [端口与连接上限](端口与连接上限.md) · [包怎么找到路](包怎么找到路.md)
