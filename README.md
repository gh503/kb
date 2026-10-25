# 知识库

一个用 Markdown 写、能全文搜索、推上去就自动发布的个人知识库。

线上地址：<https://gh503.github.io/kb/>

## 它是什么

- **内容**：`docs/` 下的 Markdown，一页一件事
- **站点**：MkDocs + Material 主题，静态生成，不需要数据库和服务端
- **搜索**：构建时生成索引，浏览器端全文检索，中文可用
- **发布**：`git push` → GitHub Actions 构建 → GitHub Pages 上线

## 本地跑

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve          # http://127.0.0.1:8000
```

只检查能不能构建（死链接、缺失页面会报错）：

```bash
mkdocs build --strict
```

## 写一页

1. `docs/<分类>/<slug>.md`
2. 在 `mkdocs.yml` 的 `nav` 里加一行
3. `git push`

细节见线上「写作规范」。

## 发布

- 只有 `main` 分支触发
- 首次需在 **Settings → Pages → Source** 选 **GitHub Actions**
- 构建失败看 **Actions** 标签页；`--strict` 会把死链接当错误

## 换名字 / 换地址

改 `mkdocs.yml` 里的 `site_name`、`site_url`、`repo_url` 三行即可。

## 许可

未加 `LICENSE`，默认保留所有权利。要放开（例如 CC BY 4.0）再单独加文件。
