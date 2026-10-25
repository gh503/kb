# TPM 能做什么不能做什么

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 机器之外的那层

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><a href="SecureBoot挡住了什么.md">SecureBoot挡住了什么</a><span class="kb-chain__sep">·</span><span class="kb-chain__now">TPM能做什么不能做什么</span><span class="kb-chain__sep">·</span><a href="IOMMU与DMA.md">IOMMU与DMA</a><span class="kb-chain__sep">·</span><a href="硬件信任根到哪为止.md">硬件信任根到哪为止</a></div>

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
