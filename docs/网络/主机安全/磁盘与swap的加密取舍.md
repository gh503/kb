# 磁盘与 swap 的加密取舍

> **深度** 取舍 ｜ **类型** 实测 ｜ **链** 日志与完整性

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><a href="文件完整性监控怎么落地.md">文件完整性监控怎么落地</a><span class="kb-chain__sep">·</span><a href="集中日志与审计留存.md">集中日志与审计留存</a><span class="kb-chain__sep">·</span><a href="容器与宿主的安全边界.md">容器与宿主的安全边界</a><span class="kb-chain__sep">·</span><span class="kb-chain__now">磁盘与 swap 的加密取舍</span></div>

## 结论

**全盘加密防的是"机器离手"，不是"机器被入侵"。**
本机实测：**LUKS 卷 0 个、`/etc/crypttab` 不存在、swap 是 22.9 GB 明文分区**——
也就是说，**把这块盘拆下来挂到另一台机器上，所有数据（含内存溢出到 swap 的内容）都能直接读**。

## 加密挡什么、不挡什么

```text
挡住：拆盘读取、丢失/被盗、返修时被翻
不挡：系统运行时的入侵（解密后的数据就在那儿）
不挡：内存取证（冷启动、DMA）
```

**"开机状态等于没加密"**：加密的边界是"关机/离手"那一刻。

## 本机可复现（已实测）

```bash
lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINT | grep -E 'crypt|LUKS' || echo '无 LUKS'
ls /dev/mapper
ls -l /etc/crypttab 2>/dev/null || echo '无 crypttab'
swapon --show
grep -c crypt /etc/fstab
```

本机输出：

```text
无 LUKS
control
无 crypttab
NAME      TYPE      SIZE USED PRIO
/dev/sda2 partition 22.9G  3G   -2
0
```

## swap 为什么必须一起加密

```text
内存不够 → 页被换出到 swap → 里面可能有密钥、密码、会话令牌
swap 明文 = 这些内容以明文落在盘上
休眠（hibernate）= 整个内存写进 swap
```

**"盘加密了、swap 没加密"** 是常见半成品：拆盘的人照样能翻出秘密。

## 三种取舍

```text
1. 全盘 LUKS + 开机手输密码：最强，代价是无人值守重启会卡住
2. LUKS + TPM 自动解锁：能自动开机，但"盘在这台机器上"就等于能解
3. 只加密 /home：轻量，但 /tmp、swap、数据库目录仍在明文
```

**"TPM 自动解锁"把威胁模型从'拆盘'变成'整机被拿走'"**：这时要配 Secure Boot + PCR 绑定才有意义。

<!-- kb-chart:disk_enc -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="拆盘即可读全部数据，包括被换出到 swap 的内存内容" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="14.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">这台机器的存储加密状态：三处全空（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="268.5" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">已加密</text>
<text x="505.5" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">密钥独立保存</text>
<text x="140.0" y="76.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="600" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">LUKS 卷</text>
<rect x="156.0" y="60" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<rect x="393.0" y="60" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<text x="628.0" y="75.0" font-size="10" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0 个</text>
<text x="140.0" y="106.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="600" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">/etc/crypttab</text>
<rect x="156.0" y="90" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<rect x="393.0" y="90" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<text x="628.0" y="105.0" font-size="10" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">不存在</text>
<text x="140.0" y="136.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="600" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">swap</text>
<rect x="156.0" y="120" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<rect x="393.0" y="120" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<text x="628.0" y="135.0" font-size="10" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">22.9 GB 明文</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">拆盘即可读全部数据，包括被换出到 swap 的内存内容</text>
</svg>
<figcaption>拆盘即可读全部数据，包括被换出到 swap 的内存内容</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
LUKS 卷 0 ｜ crypttab 不存在 ｜ swap 22.9 GB（已用 3 GB）｜ fstab 无 crypt 项
经验：笔记本必须全盘加密；swap 必须同盘同加密
经验：加密带来的吞吐损失常见 5%–20%（取决于 CPU 是否有 AES-NI）
经验：恢复密钥要离线保存，丢了就是永久丢数据
经验：加密后无法从盘上恢复"忘记的密码"，这是设计而非缺陷
```

## 证据强度

- **实测**：四项状态来自本机 `lsblk`/`swapon`/`fstab`
- **公开经验**：5%–20% 的吞吐代价区间
- **推断**：TPM 自动解锁的安全强度取决于 PCR 配置，需逐机评估

## 不适用的情况

- 一次性/无敏感数据的机器：加密收益低
- 需要频繁重启且无人值守的设备：手输密码不现实，得配 TPM 或密钥文件

## 常见错法

- **只加密根分区，swap 留在明文**
- **把恢复密钥存在同一块盘上**
- **以为加密能防"已登录的人"**

## 往下追

- 回到本链起点：[文件完整性监控怎么落地](文件完整性监控怎么落地.md)

## 相关

- [主机安全](index.md) · [硬件信任根到哪为止](../硬件安全/硬件信任根到哪为止.md) · [TPM 能做什么不能做什么](../硬件安全/TPM能做什么不能做什么.md)
