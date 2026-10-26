# Secure Boot 挡住了什么

> **深度** 入门 ｜ **类型** 实测 ｜ **链** 机器之外的那层

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> <span class="kb-chain__now">Secure Boot 挡住了什么</span> · [TPM 能做什么不能做什么](TPM能做什么不能做什么.md) · [IOMMU 与 DMA](IOMMU与DMA.md) · [硬件信任根到哪为止](硬件信任根到哪为止.md)
</div>


## 结论

**Secure Boot 只保证"启动的第一个环节是签过名的"，不保证系统干净。**
本机实测：**EFI 模式，但 Secure Boot 是 disabled**——启动链的信任根没有建立。

## 它挡什么、不挡什么

| 挡住 | 不挡住 |
| --- | --- |
| 篡改的引导程序 | 内核加载后的恶意模块 |
| 未签名的内核 | 用户态木马 |
| 部分固件级 rootkit | 已签名但有毒的驱动 |

**"过了 Secure Boot" ≠ "系统可信"**：它是一段信任链的起点，终点要靠别的东西接。

## 本机可复现（已实测）

```bash
[ -d /sys/firmware/efi ] && echo EFI 模式 || echo BIOS 模式
mokutil --sb-state
```

本机输出：

```text
EFI 模式
SecureBoot disabled
```

**"EFI 模式 + SecureBoot disabled"** 是常见组合：能装任意系统，但少了启动链保护。

## 为什么很多机器是关的

```text
1. 装第三方驱动/内核模块会被拦
2. 双系统、自定义引导会被拦
3. 厂商默认关闭（尤其是旧机型）
```

**"开了就装不上东西"** 是真实摩擦，不是借口。

## 怎么开（以及代价）

```bash
mokutil --sb-state          # 先看当前状态
# 开机进 UEFI 设置 → Security → Secure Boot → Enabled
# 需要给第三方模块签名（MOK）
sudo mokutil --import 模块公钥.der
```

**"开了以后要维护签名"**：每次更新内核模块都要重新签。

<!-- kb-chart:secureboot -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="3=能挡。本机 SecureBoot disabled：这条信任链是断的。" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="16.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">Secure Boot 挡住什么、挡不住什么</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="209.2" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">引导被改</text>
<text x="327.8" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">未签名内核</text>
<text x="446.2" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">用户态木马</text>
<text x="564.8" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">已签名坏驱动</text>
<text x="140.0" y="76.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="600" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">Secure Boot</text>
<rect x="156.0" y="60" width="106.5" height="22" rx="4" fill="var(--kb-accent)" opacity="0.9"/>
<text x="209.2" y="75.0" font-size="10" text-anchor="middle" fill="var(--kb-paper)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">好</text>
<rect x="274.5" y="60" width="106.5" height="22" rx="4" fill="var(--kb-accent)" opacity="0.9"/>
<text x="327.8" y="75.0" font-size="10" text-anchor="middle" fill="var(--kb-paper)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">好</text>
<rect x="393.0" y="60" width="106.5" height="22" rx="4" fill="var(--kb-line)" opacity="0.6"/>
<text x="446.2" y="75.0" font-size="10" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">差</text>
<rect x="511.5" y="60" width="106.5" height="22" rx="4" fill="var(--kb-line)" opacity="0.6"/>
<text x="564.8" y="75.0" font-size="10" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">差</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">3=能挡。本机 SecureBoot disabled：这条信任链是断的。</text>
</svg>
<figcaption>3=能挡。本机 SecureBoot disabled：这条信任链是断的。</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
本机：EFI 模式，SecureBoot disabled
经验：开 Secure Boot 后，未签名模块加载会失败（需 MOK 签名）
经验：笔记本丢失场景，Secure Boot 提供的是"启动完整性"，不是"数据保密"
```

## 证据强度

- **实测**：两项状态为本机输出
- **公开经验**：Secure Boot 的边界与 MOK 流程
- **推断**："旧机型默认关"是普遍现象，未做统计

## 不适用的情况

- 需要自由装内核/驱动的开发机：开了会很痛
- 无 UEFI 的老机器：根本不存在

## 常见错法

- **以为开了 Secure Boot 就"安全了"**
- **关了它却以为没有信任链需求**
- **不备份 MOK 密钥**

## 往下追

- [TPM 能做什么不能做什么](TPM能做什么不能做什么.md)

## 相关

- [硬件安全](index.md) · [硬件信任根到哪为止](硬件信任根到哪为止.md)
