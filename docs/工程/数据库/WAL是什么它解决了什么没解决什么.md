# WAL 是什么，它解决了什么没解决什么

> **深度** 取舍 ｜ **类型** 边界 ｜ **链** 慢在数据不在 SQL

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><a href="JOIN为什么慢.md">JOIN为什么慢</a><span class="kb-chain__sep">·</span><a href="分页越翻越慢.md">分页越翻越慢</a><span class="kb-chain__sep">·</span><a href="事务批处理为什么快一千倍.md">事务批处理为什么快一千倍</a><span class="kb-chain__sep">·</span><span class="kb-chain__now">WAL是什么它解决了什么没解决什么</span></div>

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

<!-- kb-chart:wal_vs_delete -->

<figure class="kb-figure">
<svg viewBox="0 0 720 340" role="img" aria-label="只快 1.2 倍。WAL 的收益在「读写不打架」，不在这点写入时间" xmlns="http://www.w3.org/2000/svg">
<rect x="0" y="0" width="720" height="340" fill="none"/>
<text x="0.0" y="14.0" font-size="13" text-anchor="start" fill="currentColor" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">同一个事务 2 万行：DELETE 日志 vs WAL（本机实测）</text>
<text x="716.0" y="332.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif"></text>
<text x="10.0" y="22.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">ms</text>
<line x1="62" y1="294.0" x2="624" y2="294.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="298.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">0</text>
<line x1="62" y1="229.0" x2="624" y2="229.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="233.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">18.8025</text>
<line x1="62" y1="164.0" x2="624" y2="164.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="168.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">37.605</text>
<line x1="62" y1="99.0" x2="624" y2="99.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="103.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">56.4075</text>
<line x1="62" y1="34.0" x2="624" y2="34.0" stroke="var(--kb-line)" stroke-width="1"/>
<text x="54.0" y="38.0" font-size="11" text-anchor="end" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">75.21</text>
<line x1="62" y1="34" x2="62" y2="294" stroke="var(--kb-line)" stroke-width="1"/>
<rect x="179.5" y="67.9" width="43.0" height="226.1" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="201.0" y="61.9" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">65.4</text>
<rect x="460.5" y="103.5" width="43.0" height="190.5" rx="3" fill="var(--kb-accent)" opacity="0.85"/>
<text x="482.0" y="97.5" font-size="10" text-anchor="middle" fill="var(--kb-accent)" font-weight="700" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">55.1</text>
<text x="202.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">DELETE 模式</text>
<text x="483.5" y="310.0" font-size="11" text-anchor="middle" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">WAL 模式</text>
<text x="62.0" y="332.0" font-size="11" text-anchor="start" fill="var(--kb-ink-mute)" font-weight="400" opacity="1" font-family="system-ui, -apple-system, PingFang SC, Noto Sans CJK SC, sans-serif">只快 1.2 倍。WAL 的收益在「读写不打架」，不在这点写入时间</text>
</svg>
<figcaption>只快 1.2 倍。WAL 的收益在「读写不打架」，不在这点写入时间</figcaption>
</figure>


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
