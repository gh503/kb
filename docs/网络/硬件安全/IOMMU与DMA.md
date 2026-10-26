# IOMMU 与 DMA

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 机器之外的那层

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [Secure Boot 挡住了什么](SecureBoot挡住了什么.md) · [TPM 能做什么不能做什么](TPM能做什么不能做什么.md) · <span class="kb-chain__now">IOMMU 与 DMA</span> · [硬件信任根到哪为止](硬件信任根到哪为止.md)
</div>


## 结论

**DMA 让设备能直接读写内存，绕过 CPU 的权限检查；IOMMU 就是给 DMA 装的那道闸。**
本机实测：**14 个 IOMMU 组，`dmar1` 设备存在**——IOMMU 已在用。

## 没有 IOMMU 会怎样

```text
设备（网卡、USB、雷电）→ 直接写物理内存 → 越过内核权限
恶意设备 = 直接读写任意内存
虚拟机直通设备 = 可访问宿主内存
```

**"插个设备就能读内存"** 是 Thunderbolt/USB4 时代的现实风险。

## 本机可复现（已实测）

```bash
ls /sys/kernel/iommu_groups | wc -l     # 14
ls /sys/class/iommu                    # dmar1
dmesg | grep -i -E 'DMAR|IOMMU'        # 本机 dmesg 受限（dmesg_restrict=1）
```

本机输出：

```text
14
dmar1
（dmesg 读不到，被 dmesg_restrict=1 挡住）
```

**"14 个组"说明设备已被分组隔离**：组内设备共享地址空间，组间隔离。

## 组数量意味着什么

```text
组越细，隔离越好（每个设备一组最佳）
组内共享：一个设备能访问同组其他设备的内存
直通虚拟机时要整组给
```

**"把整组直通"** 是虚拟化里的硬约束，也是很多"设备直通失败"的原因。

## 怎么确认它在工作

```bash
# 内核启动参数应包含
cat /proc/cmdline | tr ' ' '\n' | grep -E 'iommu|intel_iommu|amd_iommu'
# 预期：intel_iommu=on 或 iommu=pt
```

**"有 /sys/class/iommu 条目"** 就说明 IOMMU 已启用，不只是硬件支持。

<!-- kb-chart:iommu_groups -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="组越细隔离越好；直通虚拟机要整组给，这是很多直通失败的根因" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="14.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">设备被隔离成多少个 IOMMU 组（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">个</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="298.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">4.025</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">8.05</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">12.075</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">16.1</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="179.5" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="201.0" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">14</text>
<rect x="460.5" y="277.9" width="43.0" height="16.1" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="482.0" y="271.9" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">1</text>
<text x="202.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">IOMMU 组</text>
<text x="483.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">dmar 单元</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">组越细隔离越好；直通虚拟机要整组给，这是很多直通失败的根因</text>
</svg>
<figcaption>组越细隔离越好；直通虚拟机要整组给，这是很多直通失败的根因</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
IOMMU 组 14 个 ｜ dmar1 存在 ｜ dmesg 受限
经验：直通设备要整组隔离
经验：笔记本开启 IOMMU 可能影响休眠/外设兼容
经验：`iommu=pt` 只给直通设备翻译，性能更好
```

## 证据强度

- **实测**：两项计数为本机输出
- **公开经验**：组隔离与直通约束
- **推断**："组越细越好"是隔离原则，具体分组由固件决定

## 不适用的情况

- 无虚拟化、无外接设备的机器：风险低
- 某些老平台：IOMMU 有缺陷，需要关闭

## 常见错法

- **以为有 IOMMU 就自动隔离**
- **随意直通整组设备**
- **忽略固件层的 DMA 设置**

## 往下追

- [硬件信任根到哪为止](硬件信任根到哪为止.md)

## 相关

- [硬件安全](index.md) · [TPM 能做什么不能做什么](TPM能做什么不能做什么.md)
