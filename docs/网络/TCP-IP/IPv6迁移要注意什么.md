# IPv6 迁移要注意什么

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 包是怎么走过去的

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [包怎么找到路](包怎么找到路.md) · [NAT与端口](NAT与端口.md) · <span class="kb-chain__now">IPv6迁移要注意什么</span> · [TTL与traceroute怎么读](TTL与traceroute怎么读.md)
</div>

## 结论

**IPv6 不是"地址变长"，是"三件事同时变了"：地址、邻居发现、以及"没有 NAT 意味着每台机器都直接暴露"。**
本机实测：已拿到全球地址并同时存在 **3 个临时（隐私）地址**；头部从 **20 B 变 40 B**，
1500 MTU 下 TCP 有效载荷从 **1472 降到 1452（−1.4%）**。

## 三个必改点

```text
1. 地址：128 位，接口标识通常由 EUI-64 或隐私扩展生成 → 一个网卡多个地址是常态
2. 邻居发现（NDP）：用 ICMPv6 替代 ARP —— 拦了 ICMPv6 就等于断了 IPv6
3. 无 NAT：每台机器都有全球地址 → 防火墙默认策略必须显式拒绝入站
```

**"IPv6 就是把地址写长一点"** 会漏掉防火墙这一条，等于把内网全暴露。

## 本机可复现（已实测）

```bash
ip -6 addr show scope global | grep inet6
ip -6 route | wc -l
python3 -c "print(1500-20-8, 1500-40-8)"    # 1472 1452
```

本机输出：

```text
wlo1：2409:8a2b:...:75ab/64（temporary dynamic）
      另有 2 个 temporary（含已 deprecated 的旧地址）
IPv6 路由 6 条 ｜ 有效载荷 1472 → 1452（−1.4%）
```

## 迁移顺序

```text
1. 先双栈：同时保留 A 与 AAAA，观察 AAAA 的回退率
2. 再改防火墙：默认拒绝入站，只放需要的端口（先于上线）
3. 再改监控与日志：日志字段要能存 39 字符的地址
4. 最后才考虑关 IPv4：多数场景不需要关
```

**"一步切到纯 IPv6"** 会让所有只有 IPv4 的对端直接失联。

## 最容易踩的四个坑

```text
1. 防火墙拦了 ICMPv6 → 邻居发现失败，表现为"时通时不通"
2. 应用存 IP 的字段只有 15 字符（IPv4 长度）→ 截断
3. 日志/风控按 IPv4 正则 → IPv6 全部匹配不上
4. 以为还有 NAT 挡着 → 服务直接暴露在公网
```

<!-- kb-chart:v6_overhead -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="3 个临时地址是本机实测；ICMPv6 被拦 = 邻居发现失败" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">IPv6 头 40 B：1500 MTU 下有效载荷 1472 → 1452（−1.4%，计算）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">B</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">423.2</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">846.4</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1,270</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1,693</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="179.5" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="201.0" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1,472</text>
<rect x="460.5" y="71.0" width="43.0" height="223.0" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="482.0" y="65.0" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1,452</text>
<text x="202.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">IPv4 有效载荷</text>
<text x="483.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">IPv6 有效载荷</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">3 个临时地址是本机实测；ICMPv6 被拦 = 邻居发现失败</text>
</svg>
<figcaption>3 个临时地址是本机实测；ICMPv6 被拦 = 邻居发现失败</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
本机 3 个全球临时地址 ｜ IPv6 路由 6 条
头部 40 B vs 20 B：1500 MTU 下有效载荷 1452 vs 1472（−1.4%）
经验：IPv6 最小 MTU 1280，隧道场景要按 1280 规划
经验：隐私地址默认每 24 小时换一次（本机 preferred 余量约 4 小时）
经验：AAAA 有记录但不可达时，浏览器回退约需 0.3–1 s（Happy Eyeballs）
```

## 证据强度

- **实测**：地址数量、路由数、头部差值来自本机
- **公开经验**：ICMPv6 必需、1280 最小 MTU、Happy Eyeballs 回退
- **推断**：本机在代理后，全球地址的可达性不代表真实公网路径

## 不适用的情况

- 纯内网离线环境：可用 ULA（fc00::/7），不涉及公网暴露
- 老旧设备只支持 IPv4：双栈必须保留

## 常见错法

- **拦掉所有 ICMPv6**
- **数据库字段按 15 字符设计**
- **上了 IPv6 但防火墙默认放行**

## 往下追

- [TTL与traceroute怎么读](TTL与traceroute怎么读.md)

## 相关

- [TCP-IP](index.md) · [NAT与端口](NAT与端口.md) · [MTU与分片](MTU与分片.md)
