# WAL 是什么，它解决了什么没解决什么

> **深度** 取舍 ｜ **类型** 边界 ｜ **链** 查询为什么慢

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><a href="一条查询是怎么执行的.md">一条查询是怎么执行的</a><span class="kb-chain__sep">·</span><a href="索引什么时候没用.md">索引什么时候没用</a><span class="kb-chain__sep">·</span><a href="事务批处理为什么快一千倍.md">事务批处理为什么快一千倍</a><span class="kb-chain__sep">·</span><span class="kb-chain__now">WAL是什么它解决了什么没解决什么</span></div>

## 结论

**WAL 让"读"不等"写"，但没让"两个写"并行。**
本机实测：WAL 模式下第二个写者照样收到 `database is locked`；收益在**读写并发**，不在写写并发。

## 两种日志模式的区别

| 模式 | 写的时候 | 读的时候 |
| --- | --- | --- |
| 回滚日志（DELETE） | 先把旧页写进日志，再改主文件 | 写期间读会被阻塞 |
| WAL | 只往 `-wal` 文件追加 | 读旧快照，不阻塞 |

**"读旧快照"就是快照隔离的雏形**：读者看到的是事务开始时的数据。

## 本机可复现（已实测）

```python
con.execute('PRAGMA journal_mode=WAL')
# 连接 A：BEGIN IMMEDIATE 并插入一行（不提交）
# 连接 B：也插入一行（timeout=0.2）
```

本机输出：

```text
DELETE 模式第二个写者：database is locked（等了 201.8 ms）
WAL   模式第二个写者：database is locked
WAL 期间另一个连接读 count(*)：(0)   ← 读到了提交前的快照
```

**两个写者互斥是 SQLite 的设计**，不是 WAL 没生效：写锁永远只有一个。

## 批量插入的实测差别

```python
# 20000 行放进一个事务
journal_mode=DELETE   65.4 ms
journal_mode=WAL      55.1 ms
```

只快 **1.2 倍**——因为一个事务只有一次提交，日志模式的差别被摊薄了。
**WAL 的收益主要在"写的同时有人读"**，不在单事务吞吐。

## 什么时候值得开 WAL

```text
有并发读 + 偶尔写（Web 应用、桌面应用）→ 开
纯批量导入、无人读 → 差别很小
多进程同时写 → WAL 也救不了，要换数据库或加队列
```

**"多写"是 SQLite 的硬边界**：它本来就是单写者模型。

## 数字与阈值（本机实测）

```text
单事务 20000 行：DELETE 65.4 ms ／ WAL 55.1 ms（1.2×）
第二写者等待：201.8 ms 后报 database is locked（timeout=0.2）
WAL 期间读到的行数：0（快照隔离）
WAL 文件：写入后主库大小 0.0 MB（数据还在 -wal 里）
```

## 证据强度

- **实测**：四组输出均为本机 sqlite3 结果
- **公开经验**：WAL 的快照隔离语义、单写者模型
- **推断**："收益在读写并发"由单事务吞吐只差 1.2 倍推的

## 不适用的情况

- 网络文件系统上的数据库文件：WAL 依赖共享内存，可能不可用
- 需要多写并发的场景：应换 PostgreSQL/MySQL，而不是调 WAL

## 常见错法

- **以为开了 WAL 就能多写并发**
- **只读场景也开 WAL**：多出 `-wal`/`-shm` 文件，备份时要一起处理
- **备份时只拷主库文件**：会丢掉 `-wal` 里未合并的数据

## 往下追

- 换一条链：[事务到底是什么](事务到底是什么.md)

## 相关

- [数据库](index.md) · [两个写者为什么互相等](两个写者为什么互相等.md)
