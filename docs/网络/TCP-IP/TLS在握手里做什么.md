# TLS 在握手里做什么

> **深度** 取舍 ｜ **类型** 边界 ｜ **链** 一次请求经过了什么

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [域名怎么变成 IP](域名怎么变成IP.md) · [TCP 握手到底几次](TCP握手到底几次.md) · <span class="kb-chain__now">TLS 在握手里做什么</span> · [HTTP 在连接上怎么走](HTTP在连接上怎么走.md)
</div>





## 结论

**TLS 握手解决三件事：确认对方身份、协商出双方都有的密钥、此后全程加密。**
TLS 1.3 把这压进 **1 个 RTT**，TLS 1.2 需要 2 个。

## 三个阶段

```text
1. 身份：服务端出示证书链，客户端验证到受信任的根
2. 密钥：通过密钥交换（如 X25519）算出共享密钥，不直接在网线上传
3. 完成：双方用会话密钥加密后续所有数据
```

**"不传密钥"是关键**：交换的是计算材料，不是密码本身。

## 证书链怎么验

```text
站点证书（*.github.io）
  → 中间 CA（签发者）
    → 根 CA（在系统/浏览器的信任库里）
```

**任何一环缺失或过期，验证就失败**。常见报错是"证书链不完整"。

## 本机实测

```text
环境：Ubuntu 22.04，OpenSSL 3.0.2，出网经本地代理
命令：openssl s_client -connect gh503.github.io:443 \
        -servername gh503.github.io -brief

Protocol version: TLSv1.3
Ciphersuite:     TLS_AES_128_GCM_SHA256
Peer certificate: CN = *.github.io
Signature type:  RSA-PSS
Verification:    OK
Server Temp Key: X25519, 253 bits
```

**可以读出四件事**：协议版本 1.3、用 AES-128-GCM 对称加密、
密钥交换用 X25519（而非 RSA 加密传输）、证书是通配符证书。

**`Verification: OK` 只代表"这条链能验通"**，不代表站点可信或业务安全。

## 一条命令看有效期

```bash
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
  | openssl x509 -noout -dates -subject
```

**`-servername` 不能省**：不传 SNI，服务器可能返回默认证书，验出"证书不匹配"的假故障。

## TLS 1.3 省掉的往返

| 版本 | 握手 RTT | 说明 |
| --- | --- | --- |
| TLS 1.2 | 2 | 需等 ServerHello 后再发密钥材料 |
| TLS 1.3 | 1 | 客户端直接猜密钥参数一起发 |
| 0-RTT 重连 | 0 | 有重放风险，不用于非幂等请求 |

**"0-RTT 有重放风险"**：同一份数据可能被攻击者重放，所以只适合幂等请求。

## 常见误解

```text
✗ "HTTPS 就安全了"——只保护传输，不保护服务端被攻破
✗ "证书越贵越安全"——DV/OV/EV 是验证等级，加密强度相同
✗ "用了 TLS 1.3 就没有中间人"——客户端信任了假根证书仍会被劫持
```

## 数字与阈值（经验判断）

```text
TLS 1.3 握手：1 RTT；TLS 1.2：2 RTT
证书有效期：公开 CA 常见 ≤ 398 天（并趋于缩短）
到期预警：提前 30 天
会话复用：可省掉完整握手（1 RTT → 0）
密钥交换：优先 X25519/ECDHE，不用 RSA 密钥传输
```

## 证据强度

- **实测**：本机 `openssl s_client -brief` 输出（见上），**协议版本与套件为真实协商结果**
- **规范**：TLS 1.2 = 2 RTT、1.3 = 1 RTT，属协议定义，可直接推
- **公开经验**：证书有效期上限与到期预警时间

## 不适用的情况

- 双向认证（mTLS）：客户端也要出示证书
- 内网自签证书：验证链不同，需分发根证书

## 常见错法

- **只查证书不查链**：缺中间证书时部分客户端失败
- **漏传 SNI**：共享 IP 的站点验出假故障
- **把 0-RTT 用在支付**：有重放风险

## 往下追

- [HTTP 在连接上怎么走](HTTP在连接上怎么走.md)

## 相关

- [TCP-IP](index.md) · [TCP 握手到底几次](TCP握手到底几次.md)
