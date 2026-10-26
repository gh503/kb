# TPM 能做什么不能做什么

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 机器之外的那层

<div class="kb-chain" markdown>
<span class="kb-chain__label">本链四页</span> [Secure Boot 挡住了什么](SecureBoot挡住了什么.md) · <span class="kb-chain__now">TPM 能做什么不能做什么</span> · [IOMMU 与 DMA](IOMMU与DMA.md) · [硬件信任根到哪为止](硬件信任根到哪为止.md)
</div>


## 结论

**TPM 是一个"会做密码学、且密钥不出芯片"的小芯片；它不判断你的系统是否安全。**
本机实测：**TPM 2.0 存在**（`/dev/tpm0` 与 `/dev/tpmrm0`，version 2）。

## 它能做四件事

| 能力 | 说明 |
| --- | --- |
| 存密钥 | 私钥不出芯片，只能用不能读 |
| 度量（PCR） | 记录启动各阶段哈希 |
| 密封（seal） | 只有 PCR 符合预期时才解出密钥 |
| 随机数/签名 | 设备身份、密钥证明 |

**"密封"是最有用的**：把磁盘密钥绑到"启动状态"，改引导就解不开。

## 它不能做什么

```text
不能防"系统里有木马"（它只管启动阶段）
不能替代磁盘加密（要配合 LUKS）
不能保证固件没后门
不能在没有 OS 支持时自动生效
```

**"有 TPM"不等于"已启用"**：多数机器有芯片但没配置。

## 本机可复现（已实测）

```bash
ls /dev/tpm*
cat /sys/class/tpm/tpm0/tpm_version_major
cat /sys/class/tpm/tpm0/device/description
```

本机输出：

```text
/dev/tpm0
/dev/tpmrm0
2
TPM 2.0 Device
```

**`/dev/tpmrm0` 是资源管理器**：多进程友好，比直接用 `/dev/tpm0` 安全。

## 怎么用起来（Linux）

```bash
# 1. 看是否被内核识别
dmesg | grep -i tpm         # 或 journalctl -k | grep -i tpm
# 2. 绑 LUKS（需要重装或加新密钥）
sudo systemd-cryptenroll --tpm2-device=auto /dev/sda3
# 3. 校验
sudo cryptsetup luksDump /dev/sda3 | grep -i tpm2
```

**"绑 TPM 的 LUKS"** 才是它最常见的实用价值：开机自动解锁，但换盘/改引导就解不开。

<!-- kb-chart:tpm_ability -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="3=能。它只管启动阶段；系统跑起来之后硬件帮不上忙。" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="14.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">TPM 能做什么、不能做什么（本机 TPM 2.0）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="209.2" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">密钥不出芯片</text>
<text x="327.8" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">度量启动</text>
<text x="446.2" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">判断系统安全</text>
<text x="564.8" y="46.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">替代磁盘加密</text>
<text x="140.0" y="76.0" font-size="12" text-anchor="end" fill="currentColor" font-weight="600" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">TPM 2.0</text>
<rect x="156.0" y="60" width="106.5" height="22" rx="4" fill="var(--kb-accent)" opacity="0.9"/>
<text x="209.2" y="75.0" font-size="10" text-anchor="middle" fill="var(--kb-paper)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">好</text>
<rect x="274.5" y="60" width="106.5" height="22" rx="4" fill="var(--kb-accent)" opacity="0.9"/>
<text x="327.8" y="75.0" font-size="10" text-anchor="middle" fill="var(--kb-paper)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">好</text>
<rect x="393.0" y="60" width="106.5" height="22" rx="4" fill="var(--kb-line)" opacity="0.6"/>
<text x="446.2" y="75.0" font-size="10" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">差</text>
<rect x="511.5" y="60" width="106.5" height="22" rx="4" fill="var(--kb-line)" opacity="0.6"/>
<text x="564.8" y="75.0" font-size="10" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">差</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">3=能。它只管启动阶段；系统跑起来之后硬件帮不上忙。</text>
</svg>
<figcaption>3=能。它只管启动阶段；系统跑起来之后硬件帮不上忙。</figcaption>
</figure>


## 数字与阈值（本机实测）

```text
TPM 2.0 ｜ /dev/tpm0 与 /dev/tpmrm0 均存在
本机磁盘：0 个 LUKS 卷（未使用 TPM 密封）
经验：TPM 1.2 与现代工具兼容性差，优先 2.0
经验：PCR 7 绑 Secure Boot 状态，PCR 0/2 绑固件
```

## 证据强度

- **实测**：设备与版本为本机输出
- **公开经验**：PCR 用途与 cryptenroll 流程
- **推断**："多数机器有芯片但未配置"是普遍观察

## 不适用的情况

- 无 TPM 的老机器：可用纯口令 LUKS，安全性依赖口令强度
- 需要"换硬件也能解密"的场景：TPM 密封会挡住

## 常见错法

- **以为有 TPM 就自动加密了**
- **只绑 TPM 不留恢复口令**（主板坏即数据丢）
- **忽略 PCR 变化导致的无法解锁**

## 往下追

- [IOMMU 与 DMA](IOMMU与DMA.md)

## 相关

- [硬件安全](index.md) · [Secure Boot 挡住了什么](SecureBoot挡住了什么.md)
