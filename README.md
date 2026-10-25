# 知识库

一个用 Markdown 写、能全文搜索、推上去就自动发布的个人知识库。

线上地址：<https://gh503.github.io/kb/>

## 结构

三层，不再往下加：

```text
领域（6）→ 学科（19）→ 条目
```

| 领域 | 学科 |
| --- | --- |
| 基础 | 通用基础 · 数学 · 逻辑 |
| 工程 | 设计 · 开发 · 测试 · 运维 |
| 商业 | 运营 · 项目管理 |
| 人文 | 历史 · 政治 · 文化 · 哲学 |
| 自然 | 物理 · 化学 · 生物 · 地理 |
| 日常 | 生活 · 娱乐 |

每个学科一页 `index.md`，写清「收什么 / 不收什么」，下面是条目表；条目才是真正的内容。

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
3. 在学科页的条目表里加一行（一句话 + 状态）
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
