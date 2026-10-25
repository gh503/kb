# 快速开始

## 本地预览

需要 Python 3.9 以上。

```bash
git clone https://github.com/gh503/kb.git
cd kb
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

打开 <http://127.0.0.1:8000>。改 `docs/` 下的文件会**自动热更新**，不用重启。

## 目录结构

```text
kb/
├── mkdocs.yml              # 站点配置：名称、导航、主题
├── requirements.txt        # 依赖，本地和 CI 用同一份
├── docs/                   # 所有内容都在这里
│   ├── index.md            # 首页
│   ├── guide/              # 使用指南
│   ├── notes/              # 知识条目
│   ├── about/              # 关于、更新日志
│   └── assets/             # 图片
└── .github/workflows/      # 推送后自动构建并发布
```

## 新增一页

1. 在对应分类下新建文件，例如 `docs/notes/如何备份.md`
2. 在 `mkdocs.yml` 的 `nav:` 里加一行：

   ```yaml
   - 如何备份: notes/如何备份.md
   ```

3. 本地 `mkdocs serve` 看效果；`mkdocs build --strict` 检查死链接
4. 提交并推送：

   ```bash
   git add -A
   git commit -m "新增：如何备份"
   git push
   ```

约 1–2 分钟后线上更新。

## 发布链路

```text
git push → GitHub Actions（构建）→ GitHub Pages（线上）
```

- 构建日志：仓库 **Actions** 标签页
- 线上地址：<https://gh503.github.io/kb/>
- 只有 `main` 分支触发发布
