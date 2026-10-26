# 知识库

> 收一条只看一件事：**下次遇到同样的处境，这页能不能省掉重新摸索的时间。**
> 现在 691 条，八个域，全部可搜（中文分词，标题权重更高）。

## 先说你现在遇到什么

<div class="grid cards" markdown>

-   :material-database-clock:{ .lg .middle } **查询或接口慢**

    ---

    是没走索引、翻页太深，还是优化器选错计划？三个都能量出来。

    [:octicons-arrow-right-24: 一条查询是怎么执行的](工程/数据库/一条查询是怎么执行的.md)

-   :material-speedometer:{ .lg .middle } **机器变慢、卡、抢不到 CPU**

    ---

    nice、绑核、fd 上限、cgroup 限额，先看是哪一个在挡。

    [:octicons-arrow-right-24: nice 到底有多大用](工程/操作系统/nice到底有多大用.md)

-   :material-harddisk-remove:{ .lg .middle } **怕数据丢，要备份**

    ---

    备份失效的方式几乎都是"备了但恢复不出来"。先看这条。

    [:octicons-arrow-right-24: 备份与恢复该怎么做](工程/数据库/备份与恢复该怎么做.md)

-   :material-account-key:{ .lg .middle } **怀疑有人进过这台机器**

    ---

    提权面有多大、登录记录去哪看、补丁窗口多长——都是只读命令。

    [:octicons-arrow-right-24: 账号与提权面](网络/主机安全/账号与提权面.md)

-   :material-shield-bug:{ .lg .middle } **程序本身脆不脆**

    ---

    PIE、canary、RELRO、ASLR，四项能查能补，代价是 120 字节。

    [:octicons-arrow-right-24: 一个二进制强不强看什么](网络/软件安全/一个二进制强不强看什么.md)

-   :material-magnify-scan:{ .lg .middle } **说不清哪儿不对，只想先看看**

    ---

    全站索引一页看完；四个域的速查各一页，只放数字。

    [:octicons-arrow-right-24: 全站索引](关于/全站索引.md)

</div>

## 再按学科找

<div class="grid cards" markdown>

-   :material-shape-outline:{ .lg .middle } **基础**

    ---

    检索、写作、逻辑，加上概率论、线性代数、高等数学。不解决具体问题，但所有事都要用。

    [:octicons-arrow-right-24: 进入](基础/index.md)

-   :material-wrench-outline:{ .lg .middle } **工程**

    ---

    设计、开发、测试、运维，加上计算机、算法、操作系统、数据库。把东西做出来，并让它持续跑。

    [:octicons-arrow-right-24: 进入](工程/index.md)

-   :material-robot-outline:{ .lg .middle } **智能**

    ---

    AI、机器人。让机器感知、判断、行动。

    [:octicons-arrow-right-24: 进入](智能/index.md)

-   :material-lan-connect:{ .lg .middle } **网络**

    ---

    网络通信、TCP/IP，加上软件安全、主机安全、硬件安全。怎么连上，怎么不被打穿。

    [:octicons-arrow-right-24: 进入](网络/index.md)

-   :material-chart-line:{ .lg .middle } **商业**

    ---

    运营、项目管理。让人用上，把事推完。

    [:octicons-arrow-right-24: 进入](商业/index.md)

-   :material-book-open-variant:{ .lg .middle } **人文**

    ---

    历史、政治、文化、哲学。社会怎么变成现在这样。

    [:octicons-arrow-right-24: 进入](人文/index.md)

-   :material-atom:{ .lg .middle } **自然**

    ---

    物理、化学、生物、地理。世界本身怎么运转。

    [:octicons-arrow-right-24: 进入](自然/index.md)

-   :material-home-outline:{ .lg .middle } **日常**

    ---

    生活、娱乐。不为了产出，为了过日子。

    [:octicons-arrow-right-24: 进入](日常/index.md)

</div>

## 三种找法

- **按处境**：上面六张卡，从"症状"直接进链首页，不用先想它属于哪个学科。
- **按线索**：页面顶部搜索框做全文检索，中文可用；只记得一个词就走这条。
- **按清单**：[全站索引](关于/全站索引.md) 一页看完；[工程速查](工程/速查.md)、[网络速查](网络/速查.md)、[基础速查](基础/速查.md) 只放数字与阈值。

每条条目页顶部有一行「本链四页」：一条链的四页互相直达，不用回学科页绕。

## 写与不写

只看一条：**同样的处境再来一次，这页能不能省掉重新摸索的时间。**
省不掉就不写——收藏夹不是知识库。

具体写法见[写作规范](关于/写作规范.md)，改动记录见[更新日志](关于/更新日志.md)。

## 订阅

[订阅](订阅/index.md)：41 个信息源，每天 07:00 自动抓取，只存标题和链接。
**不进全局搜索**——它每天在变，进了索引会把知识条目淹掉。
