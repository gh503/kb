# HTTP 在连接上怎么走

> **深度** 实操 ｜ **类型** 方法 ｜ **链** 一次请求经过了什么

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [域名怎么变成 IP](域名怎么变成IP.md) · [TCP 握手到底几次](TCP握手到底几次.md) · [TLS 在握手里做什么](TLS在握手里做什么.md) · <span class="kb-chain__now">HTTP 在连接上怎么走</span>
</div>





## 结论

**HTTP/1.1 一条连接一次一个请求；HTTP/2 一条连接多路复用；HTTP/3 跑在 QUIC 上。**
所以"要不要复用连接"在 1.1 里是优化，在 2 里是默认。

## 三个版本的关键差异

| 版本 | 连接 | 并发 | 队头阻塞 |
| --- | --- | --- | --- |
| HTTP/1.1 | 每域名 6 条左右 | 靠多连接 | 有（应用层） |
| HTTP/2 | 1 条多路复用 | 流（stream） | TCP 层仍有 |
| HTTP/3 | QUIC（UDP） | 流独立 | 基本消除 |

**"HTTP/2 没有队头阻塞"是错的**：TCP 层丢包仍会卡住所有流。

## 本机实测：连接复用的代价差

```text
环境：Ubuntu 22.04，curl 7.81.0，出网经本地代理
命令：同一次 curl 进程请求两个 URL，看 num_connects

第 1 个 URL：num_connects=1  total=1.518 s
第 2 个 URL：num_connects=0  total=0.107 s
```

**第二次省下的是 TCP + TLS 握手**：1.52 s → 0.11 s，**差 14 倍**。
（数字含本地代理开销，绝对耗时不可外推，**但"复用与否差一个数量级"是可复现的结论**。）

## 再看压缩：真实可测的比例

```text
环境：同上
命令：curl -o /dev/null -w '%{size_download}' 分别取原始与 gzip

原始：77,515 字节
gzip：11,571 字节
→ 压缩到 14.9%（约 6.7:1）
```

**这是本轮最硬的一个数**：不依赖网络路径，只取决于内容与压缩算法。

## 一次请求的完整顺序

```text
1. 解析域名 → IP
2. TCP 握手（1 RTT）
3. TLS 握手（1–2 RTT）
4. 发请求，等首字节（TTFB）
5. 传响应体
6. 复用连接发下一个请求，或关闭
```

**"TTFB"包含服务端处理时间**：它慢不代表网络慢，要分开看。

## 能直接用的测量命令

```bash
curl -o /dev/null -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total} ver=%{http_version}\n' \
  https://example.com/
```

**看 `remote_ip` 判断是否走了代理/CDN**：

```bash
curl -o /dev/null -w '%{remote_ip}:%{remote_port}\n' https://example.com/
```

<!-- kb-chart:tcp_timeline -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="首屏之前的四个往返：DNS、TCP、TLS、HTTP 各一次" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">第一次访问一个网站，要等几个往返</text>
<text x="150.0" y="48.0" font-size="12" text-anchor="middle" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">客户端</text>
<text x="560.0" y="48.0" font-size="12" text-anchor="middle" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">服务器</text>
<line x1="150" y1="56" x2="150" y2="300" stroke="var(--kb-line)" stroke-width="1.4"/>
<line x1="560" y1="56" x2="560" y2="300" stroke="var(--kb-line)" stroke-width="1.4"/>
<text x="16.0" y="86.0" font-size="12" text-anchor="start" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1. DNS 解析</text>
<text x="16.0" y="102.0" font-size="10.5" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">查域名 → 拿 IP</text>
<line x1="150" y1="82" x2="560" y2="82" stroke="var(--kb-accent)" stroke-width="1.8"/>
<path d="M552 78 L560 82 L552 86" fill="var(--kb-accent)"/>
<text x="355.0" y="74.0" font-size="10.5" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1 RTT</text>
<text x="16.0" y="148.0" font-size="12" text-anchor="start" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">2. TCP 握手</text>
<text x="16.0" y="164.0" font-size="10.5" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">SYN → SYN-ACK → ACK</text>
<line x1="150" y1="144" x2="560" y2="144" stroke="var(--kb-accent)" stroke-width="1.8"/>
<path d="M552 140 L560 144 L552 148" fill="var(--kb-accent)"/>
<text x="355.0" y="136.0" font-size="10.5" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1 RTT</text>
<text x="16.0" y="210.0" font-size="12" text-anchor="start" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">3. TLS 握手</text>
<text x="16.0" y="226.0" font-size="10.5" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">TLS 1.3 一个往返；1.2 两个</text>
<line x1="150" y1="206" x2="560" y2="206" stroke="var(--kb-accent)" stroke-width="1.8"/>
<path d="M552 202 L560 206 L552 210" fill="var(--kb-accent)"/>
<text x="355.0" y="198.0" font-size="10.5" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1 RTT</text>
<text x="16.0" y="272.0" font-size="12" text-anchor="start" fill="var(--kb-warn)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">4. HTTP 请求</text>
<text x="16.0" y="288.0" font-size="10.5" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">请求 → 响应</text>
<line x1="150" y1="268" x2="560" y2="268" stroke="var(--kb-warn)" stroke-width="1.8"/>
<path d="M552 264 L560 268 L552 272" fill="var(--kb-warn)"/>
<text x="355.0" y="260.0" font-size="10.5" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1 RTT</text>
<text x="16.0" y="318.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">TLS 1.3 之后，前三次往返总共 3 RTT；首次访问常见 4 RTT 起（含 DNS 与连接建立）。</text>
<text x="16.0" y="334.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">连接复用起来之后，后续请求只剩 HTTP 那一个往返。</text>
</svg>
<figcaption>首屏之前的四个往返：DNS、TCP、TLS、HTTP 各一次</figcaption>
</figure>


## 数字与阈值（经验判断）

```text
HTTP/1.1 同域并发连接：6（浏览器惯例）
HTTP/2 单连接并发流：常见 100+
TTFB 目标：< 200 ms（动态页），< 50 ms（静态）
首屏资源数：HTTP/1.1 下尽量 < 30
压缩收益：文本类常见压到 15%–30%
```

## 证据强度

- **实测**：连接复用耗时对比、gzip 压缩比（见上，环境已写明）
- **公开经验**：各版本并发特性、浏览器 6 连接惯例
- **推断**："TTFB 慢不等于网络慢"按阶段拆分推的

## 不适用的情况

- 服务端推送/流式响应：TTFB 含义不同
- 长轮询/SSE/WebSocket：连接语义不同，见[队头阻塞](队头阻塞.md)

## 常见错法

- **每个请求新建连接**：多付握手与 TLS
- **以为 HTTP/2 就没有阻塞**：TCP 层丢包仍会卡
- **只看 total 不看分阶段**：不知道慢在哪一段

## 往下追

- [RTT 是什么为什么它决定一切](RTT是什么为什么它决定一切.md)

## 相关

- [TCP-IP](index.md) · [TLS 在握手里做什么](TLS在握手里做什么.md)
