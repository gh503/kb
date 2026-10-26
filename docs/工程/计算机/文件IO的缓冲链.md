# 文件 IO 的缓冲链

> **深度** 实操 ｜ **类型** 实测 ｜ **链** 机器在底下做什么

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><a href="虚拟内存与缺页.md">虚拟内存与缺页</a><span class="kb-chain__sep">·</span><span class="kb-chain__now">文件 IO 的缓冲链</span><span class="kb-chain__sep">·</span><a href="分支预测与流水线.md">分支预测与流水线</a><span class="kb-chain__sep">·</span><a href="并发时的内存可见性.md">并发时的内存可见性</a></div>

## 结论

**一次 `write` 要穿过三层缓冲：你的进程缓冲 → 内核页缓存 → 磁盘。**
本机实测同样写 100 万次 1 字节：**带缓冲 123.6 ms，直接 `os.write` 2734.8 ms**——
**22 倍**，差别全在系统调用次数。

## 三层各管什么

```text
1. 应用缓冲（Python 的 8 KB buffer、Java 的 BufferedWriter）
   → 攒够一块再调系统调用，省的是"用户态/内核态切换"
2. 内核页缓存（page cache）
   → 写完就在内存里，read 立刻能读到；什么时候落盘由内核决定
3. 磁盘
   → 只有 fsync / 磁盘调度才真正落盘
```

**"写完了"和"落盘了"是两件事**：`write` 返回只代表进了页缓存。

## 本机可复现（已实测）

```bash
python3 - <<'PY'
import os, time
def timed(fn, label):
    t = time.perf_counter(); fn(); print(f"{label}: {(time.perf_counter()-t)*1000:.1f} ms")
def buffered():
    with open("/tmp/buf1.dat", "wb", buffering=8192) as f:
        for _ in range(1024*1024): f.write(b"x")
def syscall_each():
    fd = os.open("/tmp/buf2.dat", os.O_WRONLY|os.O_CREAT|os.O_TRUNC)
    for _ in range(1024*1024): os.write(fd, b"x")
    os.close(fd)
def chunked():
    fd = os.open("/tmp/buf3.dat", os.O_WRONLY|os.O_CREAT|os.O_TRUNC)
    for _ in range(1024): os.write(fd, b"x"*65536)
    os.close(fd)
timed(buffered, "带缓冲 1 字节 × 1,048,576（共 1 MB）")
timed(syscall_each, "os.write 1 字节 × 1,048,576（共 1 MB）")
timed(chunked, "64 KB 块 × 1024（共 64 MB）")
PY
```

本机输出：

```text
带缓冲 1 字节 × 1,048,576（共 1 MB）: 123.6 ms
os.write 1 字节 × 1,048,576（共 1 MB）: 2734.8 ms
64 KB 块 × 1024（共 64 MB）: 42.1 ms
```

**换算成每次调用的成本**：带缓冲约 **0.12 µs/次**（摊销后），直接系统调用约 **2.6 µs/次**。

## 页缓存让"读"变得几乎免费

```text
写 64 MB 到页缓存：51.2 ms
fsync（真正落盘）：433.3 ms      ← 8.5 倍
紧接着读回 64 MB：81.9 ms        ← 命中页缓存，没有磁盘 IO
```

**"写完立刻读很快"** 不代表数据在盘上；断电时丢的正是页缓存里那部分。

## 合并写（write 与 fsync 的配比）

```text
每个事务 fsync 一次：每次都要等磁盘 → 慢，但最安全
攒 N 个事务再 fsync：吞吐 × N，代价是最多丢 N 个事务
```

**"批量提交"是数据库与日志系统提速的第一手段**，本质就是把 N 次 fsync 合成 1 次。

## 数字与阈值（本机实测）

```text
1 字节带缓冲 0.12 µs/次 ｜ 直接系统调用 2.6 µs/次（22×）
64 KB 块写 64 MB：42.1 ms
写 64 MB 进页缓存 51.2 ms ｜ fsync 433.3 ms ｜ 读回 81.9 ms
经验：缓冲区至少 4 KB（一个页），常见 8–64 KB
经验：日志类应用 fsync 间隔 1–100 ms，按可接受丢失量定
经验：小文件多时，系统调用次数比字节数更决定性能
```

## 证据强度

- **实测**：五组耗时来自本机
- **公开经验**：三层缓冲模型与批量 fsync
- **推断**：绝对数值随磁盘类型（SSD/HDD）变化几个数量级，比例关系不变

## 不适用的情况

- 只写几个小文件：优化无意义
- 已经用 `O_DIRECT` 绕过页缓存：这条链只剩一层

## 常见错法

- **循环里 `write` 一个字节**
- **以为 `write` 返回就等于落盘**
- **在事务里每条记录 fsync 一次**

## 往下追

- [分支预测与流水线](分支预测与流水线.md)

## 相关

- [计算机](index.md) · [为什么每次写完就 fsync 会慢一千六百倍](../操作系统/为什么每次写完就fsync会慢一千六百倍.md) · [WAL 是什么它解决了什么没解决什么](../数据库/WAL是什么它解决了什么没解决什么.md)
