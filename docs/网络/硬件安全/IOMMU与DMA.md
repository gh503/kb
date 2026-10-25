# IOMMU 与 DMA

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 机器之外的那层

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><a href="SecureBoot挡住了什么.md">SecureBoot挡住了什么</a><span class="kb-chain__sep">·</span><a href="TPM能做什么不能做什么.md">TPM能做什么不能做什么</a><span class="kb-chain__sep">·</span><span class="kb-chain__now">IOMMU与DMA</span><span class="kb-chain__sep">·</span><a href="硬件信任根到哪为止.md">硬件信任根到哪为止</a></div>

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
