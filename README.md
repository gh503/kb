# 知识库

一个用 Markdown 写、能全文搜索、推上去就自动发布的个人知识库。

线上地址：<https://gh503.github.io/kb/>

## 结构

三层，不再往下加：

```text
领域（8）→ 学科（39）→ 条目（867）
```

| 领域 | 学科 |
| --- | --- |
| 基础 | 通用基础 · 数学 · 概率论 · 线性代数 · 高等数学 · 逻辑 |
| 工程 | 开发 · 测试 · 运维 · 设计 · 计算机 · 算法与数据结构 · 操作系统 · 数据库 |
| 智能 | AI · 机器人 |
| 网络 | TCP/IP · 网络通信 · 安全 · 软件安全 · 主机安全 · 硬件安全 |
| 商业 | 运营 · 项目管理 · 单位经济 |
| 人文 | 历史 · 政治 · 文化 · 哲学 |
| 自然 | 物理 · 化学 · 生物 · 地理 · 天文 |
| 日常 | 事务 · 健康 · 娱乐 · 家 · 钱 |

每个学科一页 `index.md`，写清「收什么 / 不收什么」，下面是条目表；条目才是真正的内容。

## 订阅

`feeds.opml` 里 41 个信息源、7 类，`.github/workflows/feeds.yml` 每天 07:00（北京时间）
抓一次，归档到 `docs/订阅/YYYY-MM-DD.md`：只存标题、时间、来源、链接，不存正文。

- 归档即状态：不维护已读表，靠扫描已有页面里的链接去重
- 归档页 `search.exclude`，不进全局搜索（新闻每天变，会淹掉知识条目）
- 手动回填：Actions → 抓取订阅 → Run workflow → 勾 `backfill`
- 本地跑：`python3 scripts/fetch_feeds.py --backfill`

## 它是什么

- **内容**：`docs/` 下的 Markdown，一页一件事
- **站点**：MkDocs + Material 主题，静态生成，不需要数据库和服务端
- **搜索**：构建时生成索引，浏览器端全文检索，中文分词可用
- **发布**：`git push` → GitHub Actions（`--strict`）→ GitHub Pages

## 本地跑

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve          # http://127.0.0.1:8000/kb/
```

> 地址带 `/kb/` 前缀，因为 `site_url` 指向 `https://gh503.github.io/kb/`。

只检查能不能构建（死链接、缺页、没进 nav 都会报错）：

```bash
mkdocs build --strict
```

## 写一条

1. `docs/<领域>/<学科>/<条目名>.md`，例如 `docs/工程/开发/内存泄漏排查.md`
2. 在 `mkdocs.yml` 的 `nav` 里加一行
3. 在学科页的条目表里加一行（条目 + 一句话 + 深度，三列）
4. `git push`

文件名用中文名词短语，不带编号和日期。细节见线上「写作规范」。

## 发布

- 只有 `main` 分支触发
- 首次需在 **Settings → Pages → Source** 选 **GitHub Actions**
- 构建失败看 **Actions** 标签页；`--strict` 会把死链接、漏进 nav 的页面当错误

## 换名字 / 换地址

改 `mkdocs.yml` 里的 `site_name`、`site_url`、`repo_url` 三行即可。

## 许可

未加 `LICENSE`，默认保留所有权利。要放开（例如 CC BY 4.0）再单独加文件。
