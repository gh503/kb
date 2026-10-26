# JOIN 为什么慢

> **深度** 入门 ｜ **类型** 实测 ｜ **链** 慢在数据不在 SQL

<div class="kb-chain"><span class="kb-chain__label">本链四页</span><span class="kb-chain__sep">/</span><span class="kb-chain__now">JOIN为什么慢</span><span class="kb-chain__sep">·</span><a href="分页越翻越慢.md">分页越翻越慢</a><span class="kb-chain__sep">·</span><a href="事务批处理为什么快一千倍.md">事务批处理为什么快一千倍</a><span class="kb-chain__sep">·</span><a href="WAL是什么它解决了什么没解决什么.md">WAL是什么它解决了什么没解决什么</a></div>

## 结论

**JOIN 慢，九成不是"数据量大"，而是"被连接的那一边没有索引"。**
本机实测同一个查询：**没索引 4131.92 ms，SQLite 自建临时索引 35.72 ms，手建索引 21.72 ms**——
**190 倍**的差距，SQL 一个字没改。

## 三种执行方式

```text
嵌套循环（Nested Loop）：外层每行都去内层找一遍
  → 内层有索引：SEARCH，每行一次 B 树下降
  → 内层没索引：SCAN，每行扫全表 → O(n×m)，这才是慢的来源

哈希连接（Hash Join）：先给小的那一边建哈希表，再扫另一边
  → 内存够就快；不够就要落盘，退化成两趟排序

排序合并（Merge Join）：两边都按连接键有序，再归并
  → 索引直接提供顺序时最省
```

SQLite 只有前两种（哈希连接在 3.39 之后部分支持）；MySQL 8 / Postgres 三种都有。

## 本机可复现（已实测）

```bash
cd /tmp && rm -f join3.db
python3 - <<'PY'
import sqlite3, time
c = sqlite3.connect('join3.db')
c.executescript("""
CREATE TABLE users(id INTEGER PRIMARY KEY, city TEXT, pad TEXT);
CREATE TABLE small(id INTEGER PRIMARY KEY, city TEXT);
""")
c.executemany("INSERT INTO users VALUES(?,?,?)",
              ((i, f"c{i%200}", "y"*40) for i in range(1, 20001)))
c.executemany("INSERT INTO small VALUES(?,?)",
              ((i, f"c{i%200}") for i in range(1, 2001)))
c.commit()
q = "SELECT count(*) FROM small s JOIN users u ON u.city=s.city"
def t(sql):
    s=time.perf_counter(); c.execute(sql).fetchall(); return round((time.perf_counter()-s)*1000, 2)
c.execute("PRAGMA automatic_index=OFF")
print('无索引      ', t(q), 'ms')
c.execute("PRAGMA automatic_index=ON")
print('自动索引    ', t(q), 'ms')
c.execute("CREATE INDEX idx_users_city ON users(city)")
print('手建索引    ', t(q), 'ms')
print([r[3] for r in c.execute("EXPLAIN QUERY PLAN "+q)])
PY
```

本机输出（2 万 × 2 千行，连接键 `city`）：

```text
无索引       4131.92 ms     计划: SCAN s → SCAN u
自动索引     35.72 ms       计划: SCAN s → SEARCH u USING AUTOMATIC COVERING INDEX
手建索引     21.72 ms       计划: SCAN s → SEARCH u USING COVERING INDEX idx_users_city
```

## 为什么"自动索引"也快，但别依赖它

```text
自动索引是 SQLite 在查询开始时临时建的，只对这一条查询有效
建一次要扫一遍内层表（本机约 14 ms），每条新查询都要重付
它还会消耗写锁：并发场景下建索引和写操作抢同一个锁
```

**"自动索引救急，不救长期"**：一次性的临时查询可以用，进代码的查询必须显式建。

## 什么时候该反范式

```text
1. 连接键区分度低（如城市、状态）：索引帮不上，考虑把值冗余进大表
2. 同一份维表被连接几百万次：宽表比 JOIN 便宜
3. 只读报表：物化视图/汇总表，把 JOIN 挪到写入时
```

**反范式是用写代价换读代价**：维表更新时要同步冗余列，这是新的 bug 面。

## 数字与阈值（本机实测）

```text
无索引 4131.92 ms ｜ 自动索引 35.72 ms ｜ 手建索引 21.72 ms
倍率：190× / 116×
自动索引建一次约 14 ms（扫描 2 万行）
经验：区分度 = 不同值/总行数，< 0.01 的列不适合单独建索引
经验：JOIN 超过 3 张表，先看执行计划，不要凭感觉加索引
```

## 证据强度

- **实测**：三个耗时、两个执行计划都来自本机 SQLite 3.37.2
- **公开经验**：三种连接算法的适用条件
- **推断**："190 倍"来自这一组数据规模，行数与内存不同会变

## 不适用的情况

- 内层表只有几百行：全扫本来就快，加索引收益接近零
- 连接键几乎唯一且两边都有索引：差距会缩小到 2 倍以内

## 常见错法

- **只看"有没有索引"，不看执行计划**
- **给低区分度列建索引，然后 JOIN 还是慢**
- **在 ORM 里隐式 JOIN，从不看生成的 SQL**

## 往下追

- [分页越翻越慢](分页越翻越慢.md)

## 相关

- [数据库](index.md) · [索引什么时候没用](索引什么时候没用.md) · [一条查询是怎么执行的](一条查询是怎么执行的.md)
