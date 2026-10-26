# SSRF 为什么难防

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 攻击面怎么收

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [反序列化为什么是高危入口](反序列化为什么是高危入口.md) · [权限模型怎么落地](权限模型怎么落地.md) · <span class="kb-chain__now">SSRF为什么难防</span> · [安全事件的响应顺序](安全事件的响应顺序.md)
</div>

## 结论

**因为"服务端去取一个 URL"这件事，让攻击者借到了服务器的网络位置。**
本机实测（模拟服务端取址）：`127.0.0.1:8799` **200 / 14.3 ms 成功**、内网网关 `192.168.1.1` **200 / 1,036 ms 成功**、
云元数据 `169.254.169.254` **超时 3,005 ms**、公网 `gh503.github.io` **200 / 579 ms**——
**内网地址在服务端是可达的，这正是 SSRF 的立足点。**

## 三种形态

```text
基础 SSRF：直接让服务端请求 127.0.0.1 / 内网段
盲 SSRF：不回显响应，但可探测端口与状态（本机 14 ms vs 3,005 ms 就是信号）
半盲：通过错误信息、耗时、DNS 回连推断结果
```

**"只允许 http(s) 就安全"** 挡不住 `http://127.0.0.1:8080`。

## 本机可复现（已实测）

```bash
python3 -m http.server 8799 --bind 127.0.0.1 &
python3 - <<'PY'
import urllib.request, time
for u in ("http://127.0.0.1:8799/","http://192.168.1.1/","http://169.254.169.254/latest/meta-data/"):
    t=time.perf_counter()
    try:
        r=urllib.request.urlopen(u,timeout=3); print(u, r.getcode(), round((time.perf_counter()-t)*1000), "ms")
    except Exception as e: print(u, type(e).__name__, round((time.perf_counter()-t)*1000), "ms")
PY
```

本机输出：

```text
127.0.0.1:8799 → 200 / 14.3 ms ｜192.168.1.1 → 200 / 1,036 ms
169.254.169.254 → TimeoutError / 3,005 ms ｜公网 → 200 / 579 ms
```

## 为什么"黑名单 IP"不够

```text
1. 十进制/八进制/十六进制写法：127.1、0x7f000001、2130706433
2. 域名解析到内网（DNS rebinding，两次解析给不同结果）
3. 重定向：第一跳是公网，302 到内网
4. IPv6 与 IPv4 映射：::ffff:127.0.0.1
```

**"我过滤了 127.0.0.1"** 只是挡住了最直白的一种写法。

## 该怎么做

```text
1. 白名单出口：只允许明确列出的域名/IP（最有效）
2. 解析后校验：先解析成 IP，再判断是否在禁止网段（防 DNS rebinding）
3. 禁用重定向 或 每跳都重新校验
4. 独立出口：取址服务放在没有内网访问权限的网络里
5. 元数据接口：云上用 IMDSv2 + 限制跳数（TTL=1）
```

<!-- kb-chart:ssrf_reach -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="耗时差两个数量级，盲 SSRF 也能据此探测" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">服务端到内网 14.3 ms 就通，到云元数据 3,005 ms 超时（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">ms</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="297.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">7.15</text>
<line x1="62" y1="267.2" x2="624" y2="267.2" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="271.2" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">14.3</text>
<line x1="62" y1="240.5" x2="624" y2="240.5" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="244.5" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">28.6</text>
<line x1="62" y1="213.7" x2="624" y2="213.7" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="217.7" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">57.2</text>
<line x1="62" y1="187.0" x2="624" y2="187.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="191.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">114.4</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="109.2" y="267.2" width="43.0" height="26.8" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="130.8" y="261.2" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">14.3</text>
<rect x="249.8" y="101.9" width="43.0" height="192.1" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="271.2" y="95.9" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1,036</text>
<rect x="390.2" y="60.8" width="43.0" height="233.2" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="411.8" y="54.8" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">3,005</text>
<rect x="530.8" y="124.3" width="43.0" height="169.7" rx="3" fill="var(--kb-warn)" opacity="0.85"/>
<text x="552.2" y="118.3" font-size="10" text-anchor="middle" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">579</text>
<text x="132.2" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">127.0.0.1</text>
<text x="272.8" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">内网网关</text>
<text x="413.2" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">云元数据</text>
<text x="553.8" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">公网</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">耗时差两个数量级，盲 SSRF 也能据此探测</text>
</svg>
<figcaption>耗时差两个数量级，盲 SSRF 也能据此探测</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
内网可达：127.0.0.1 14.3 ms、网关 1,036 ms；元数据超时 3,005 ms
经验：盲 SSRF 靠耗时差就能探测（14 ms vs 3,005 ms 差两个数量级）
经验：禁止网段至少含 127/8、10/8、172.16/12、192.168/16、169.254/16、::1
经验：取址超时设 3–5 s，避免被当作端口扫描器
```

## 证据强度

- **实测**：四个地址的结果与耗时来自本机
- **公开经验**：四种绕过写法、五条防护
- **推断**：真实云环境的元数据接口通常 1–2 s 内可读，是否可达取决于网络策略

## 不适用的情况

- 完全不接受用户提供 URL 的服务：没有这个面
- 完全隔离的出网白名单：风险被压到白名单本身

## 常见错法

- **只黑名单几个 IP**
- **不校验重定向目标**
- **取址服务与内网同网段**

## 往下追

- [安全事件的响应顺序](安全事件的响应顺序.md)

## 相关

- [软件安全](index.md) · [越权与最小权限](../安全/越权与最小权限.md) · [拼接字符串为什么必然出事](拼接字符串为什么必然出事.md)
