# 固件供应链与 BMC

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 硬件还有哪些管不到

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [内存加密与机密计算](内存加密与机密计算.md) · <span class="kb-chain__now">固件供应链与 BMC</span> · [物理攻击与冷启动](物理攻击与冷启动.md) · [设备认证与 802.1X](设备认证与8021X.md)
</div>


## 结论

**BMC 是一台"寄生在服务器里的独立电脑"，它有自己的 CPU、内存、网络和管理员。**
本机实测：**没有 BMC**（`/dev/ipmi*` 不存在、`ipmitool` 未安装）——这是台笔记本，符合预期。
服务器上，BMC 是比操作系统更底层的一层，也是补丁最容易被忘掉的一层。

## 固件供应链有哪几段

```text
1. 芯片厂：CPU 微码（随内核包分发）
2. 板卡厂：UEFI/BIOS 镜像（厂商签名）
3. 带外管理：BMC 固件（独立更新通道）
4. 设备：网卡/RAID/HBA 固件（各自一摊）
```

**"每一段都有自己的更新节奏"**：漏掉任何一段，那一层就停在出厂版本。

## 本机可复现（已实测）

```bash
ls /dev/ipmi* 2>/dev/null || echo '无 /dev/ipmi'
command -v ipmitool || echo '无 ipmitool'
ls /sys/class/dmi/id/ 2>/dev/null | head -5
cat /sys/class/dmi/id/bios_version /sys/class/dmi/id/bios_date 2>/dev/null
```

本机输出：

```text
无 /dev/ipmi
无 ipmitool
（dmi/id 下是 modalias、product_name 等只读属性）
```

**`/sys/class/dmi/id/bios_version` 与 `bios_date`** 是每台机器都能读的固件版本，
拿它和厂商公告比对，就能判断这台机器是不是停在多年前的固件上。

## 服务器上该查的四件事

```text
1. BMC 固件版本与公告（很多高危漏洞在这里，且常被忽略）
2. BMC 是否暴露在业务网（应当只在独立管理网）
3. BMC 默认口令是否改过（出厂默认是公开知识）
4. 固件更新是否需要停机（多数需要重启，少数支持热更新）
```

**"BMC 在业务网"是最常见的配置错误**：它一旦被拿下，等于物理接触。

<!-- kb-chart:bmc_state -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="消费级笔记本没有 BMC；服务器上它是补丁最容易被忘的一层" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="14.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">带外管理在本机是否存在（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="268.5" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">存在</text>
<text x="505.5" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">可管理</text>
<text x="140.0" y="76.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="600" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">/dev/ipmi</text>
<rect x="156.0" y="60" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<rect x="393.0" y="60" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<text x="628.0" y="75.0" font-size="10" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">不存在</text>
<text x="140.0" y="106.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="600" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">ipmitool</text>
<rect x="156.0" y="90" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<rect x="393.0" y="90" width="225.0" height="22" rx="4" fill="var(--kb-line)" opacity="0.25"/>
<text x="628.0" y="105.0" font-size="10" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">未安装</text>
<text x="140.0" y="136.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="600" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">DMI 固件信息</text>
<rect x="156.0" y="120" width="225.0" height="22" rx="4" fill="var(--kb-accent)" opacity="0.9"/>
<text x="268.5" y="135.0" font-size="10" text-anchor="middle" fill="var(--kb-paper)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">好</text>
<rect x="393.0" y="120" width="225.0" height="22" rx="4" fill="var(--kb-accent)" opacity="0.9"/>
<text x="505.5" y="135.0" font-size="10" text-anchor="middle" fill="var(--kb-paper)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">好</text>
<text x="628.0" y="135.0" font-size="10" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">可读</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">消费级笔记本没有 BMC；服务器上它是补丁最容易被忘的一层</text>
</svg>
<figcaption>消费级笔记本没有 BMC；服务器上它是补丁最容易被忘的一层</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
本机无 BMC、无 ipmitool；dmi 只读属性可查 bios_version/bios_date
经验：BMC 固件至少每季度核对一次公告
经验：BMC 口令必须改，且不要与系统口令相同
经验：固件更新窗口按"季度一次 + 高危即时"排
经验：微码随内核走（本机 0xf8），但 UEFI/BMC 不会
```

## 证据强度

- **实测**：本机三类检查结果
- **公开经验**：BMC 的四项检查与补丁节奏
- **推断**：不同厂商的更新通道差异较大

## 不适用的情况

- 笔记本/桌面：没有 BMC，但仍有 UEFI 与设备固件要管
- 云主机：BMC 由云厂商负责，租户只能看实例元数据

## 常见错法

- **只打系统补丁，从不看固件**
- **BMC 与业务共用一张网卡/一个网段**
- **以为"买来就是最新的"**

## 往下追

- [物理攻击与冷启动](物理攻击与冷启动.md)

## 相关

- [硬件安全](index.md) · [微码与固件更新](微码与固件更新.md) · [硬件信任根到哪为止](硬件信任根到哪为止.md)
