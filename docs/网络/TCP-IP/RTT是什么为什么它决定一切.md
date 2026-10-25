# RTT 是什么为什么它决定一切

> **深度** 入门 ｜ **类型** 量级 ｜ **链** 为什么慢

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><span class="kb-chain__now">RTT 是什么为什么它决定一切</span><span class="kb-chain__sep">·</span><a href="带宽延迟积是什么.md">带宽延迟积是什么</a><span class="kb-chain__sep">·</span><a href="队头阻塞.md">队头阻塞</a><span class="kb-chain__sep">·</span><a href="重传与拥塞控制.md">重传与拥塞控制</a></div>




## 结论

**RTT 是数据过去再回来一趟的时间，任何"要等对方回应"的动作都至少花一个 RTT。**
所以慢不慢，先看**你要等几个 RTT**，再看带宽。

## RTT 从哪来

```text
光在光纤里约 20 万公里/秒（真空 30 万，光纤约 2/3）
跨洋 10,000 公里 → 单程 50 ms → 往返 100 ms（理论下限）
实际还要加：路由跳数、排队、中间设备
```

**"物理下限"决定了再贵的带宽也压不下去**：跨洋 RTT 不可能做到 10 ms。

## 一次页面加载要等几个 RTT

```text
DNS（无缓存）：1 RTT
TCP 握手：1 RTT
TLS 1.3：1 RTT
HTTP 请求 → 首字节：1 RTT（服务端处理另算）
合计：4 RTT 才开始收到内容
```

**跨洋 150 ms × 4 = 600 ms**，这还没算服务端处理与资源加载。

## 减少 RTT 的四种手段

| 手段 | 省掉什么 |
| --- | --- |
| 连接复用 | 省掉 TCP+TLS（2–3 RTT） |
| CDN/边缘节点 | 把 RTT 从 150 ms 降到 10–30 ms |
| DNS 预解析/预连接 | 省掉 DNS + 握手的前置等待 |
| 协议升级（QUIC 0-RTT） | 重连时省掉握手 |

**"CDN 最有效"**：它直接缩短物理距离，而不是优化次数。

## 本机实测

```text
命令：curl -w 'total=%{time_total}' https://gh503.github.io/kb/
环境：Ubuntu 22.04，经本地代理（127.0.0.1:7897）

第 1 次 total=1.436 s
第 2 次 total=0.786 s
第 3 次 total=0.629 s
```

**三次之间差一倍**，说明这个环境里 RTT 波动大（代理 + 跨境链路）。
**结论只能是"该环境的 RTT 不稳定"**，不能当作 GitHub 的常态耗时。

## 怎么测 RTT

```bash
# ICMP（可能被封）
ping -c 5 example.com

# TCP 层（更接近实际，443 端口）
curl -o /dev/null -w 'connect=%{time_connect}\n' https://example.com/

# 但注意 remote_ip：走代理时测的是到代理的 RTT
curl -o /dev/null -w 'ip=%{remote_ip}\n' https://example.com/
```

**"先看 remote_ip"是本轮反复出现的教训**：不加这一步，会把自己的代理当成服务器。

## 数字与阈值（经验判断）

```text
同机房：0.1–1 ms
同城：1–10 ms
跨省：20–50 ms
跨洲：150–250 ms
卫星链路：500–700 ms
首屏可接受：< 1 s（4G），< 500 ms（宽带）
```

## 证据强度

- **实测**：本机三次 total 耗时（见上），**仅代表该代理环境**
- **公式**：光速下限、RTT 次数可推
- **公开经验**：各地 RTT 区间与首屏目标

## 不适用的情况

- 卫星/移动网络：RTT 高且抖动大，优化重点不同
- 内网服务间调用：RTT 极低，瓶颈通常在应用层

## 常见错法

- **用带宽解释慢**：跨洋 100 Mbps 也可能很慢，因为是 RTT 限制
- **只测一次**：波动被当成定论
- **不查 remote_ip**：测的是代理

## 往下追

- [带宽延迟积是什么](带宽延迟积是什么.md)

## 相关

- [TCP-IP](index.md) · [TCP 握手到底几次](TCP握手到底几次.md)
