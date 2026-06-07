# 中国高校 LaTeX 论文模板追踪器 — 设计文档

## 概述

一个 GitHub 项目，自动追踪中国高校 LaTeX 毕业论文模板的版本、活跃度和技术特性。通过 GitHub Actions 每周自动更新，以 Markdown 表格形式展示结果。

**目标用户**：
- 学生：快速找到自己学校的模板并确认是否最新
- 模板维护者：了解其他学校的更新动态
- 研究者：观察中国高校 LaTeX 模板生态的整体状况

**核心追踪内容**：
- 版本号和发布日期
- 仓库活跃度（commit 频率、最近更新时间）
- 技术特性（LaTeX3、Overleaf 支持、LaTeX 引擎等）

## 技术方案

Python + PyGithub + GitHub Actions。

- 语言：Python 3.10+
- GitHub API 客户端：PyGithub
- 运行环境：GitHub Actions（免费，无需额外服务器）
- 更新频率：每周一自动运行（北京时间 11:00）
- 认证：GitHub Actions 内置 `GITHUB_TOKEN`

## 项目结构

```
thesis_ZN/
├── tracker/
│   ├── __init__.py
│   ├── main.py              # 入口：协调发现、抓取、生成
│   ├── discover.py          # 自动发现：GitHub API 搜索新仓库
│   ├── fetcher.py           # 数据抓取：获取仓库详细信息
│   ├── generator.py         # Markdown 生成：输出表格
│   └── models.py            # 数据结构定义
├── data/
│   ├── repos.json           # 手动维护的仓库列表（种子数据）
│   └── history.json         # 历史快照（用于变化检测）
├── output/
│   ├── README.md            # 自动生成的主页面
│   └── universities/        # 按学校分类的详情页
├── .github/
│   └── workflows/
│       └── update.yml       # 定期更新的 GitHub Actions
├── requirements.txt
└── pyproject.toml
```

## 数据模型

### 静态数据 (`data/repos.json`)

手动维护的仓库列表，每个条目：

```json
{
  "id": "tuna/thuthesis",
  "university": "清华大学",
  "university_en": "Tsinghua University",
  "type": "doctoral|master|bachelor|unified",
  "source": "manual|discovered",
  "added_at": "2026-06-07"
}
```

`type` 字段说明：
- `doctoral`：博士论文模板
- `master`：硕士论文模板
- `bachelor`：本科论文模板
- `unified`：本硕博通用模板

### 运行时数据（每次运行时从 API 获取，不持久化）

- `latest_release`: 最新 release tag 名称
- `release_date`: 最新 release 发布日期
- `last_commit`: 最近 commit 日期
- `commits_last_year`: 过去一年 commit 数量
- `stars`: Star 数
- `forks`: Fork 数
- `open_issues`: Open Issue 数
- `features`: 技术特性列表

## 核心模块

### `discover.py` — 自动发现

通过 GitHub Search API 搜索可能的模板仓库。

搜索策略：
- 关键词组合：`{高校名} + thesis + LaTeX`、`{高校名} + 毕业论文 + template`
- 语言过滤：`language:TeX`
- 排除已有仓库
- Stars 阈值：>= 10 自动加入候选，>= 50 自动确认

候选仓库需要人工确认或达到 Stars 阈值才纳入正式追踪。

### `fetcher.py` — 数据抓取

对每个追踪的仓库，调用 GitHub API 获取：

1. **基本信息**：Stars, Forks, Open Issues, 创建时间, 最近更新时间
2. **Release 信息**：最新 release tag、发布日期；无 release 则用最新 tag
3. **Commit 活跃度**：最近 commit 日期、过去一年 commit 数量
4. **技术特性检测**（从仓库文件结构和 README 推断）：
   - 存在 `latexmkrc` → 支持 latexmk
   - `.cls` 文件中包含 `\ProvidesExplClass` 或 `\RequirePackage{expl3}` → 使用 LaTeX3
   - README 中提到 Overleaf 或存在 `overleaf.tex` → 支持 Overleaf
   - 从 `.cls` 或文档推断 XeLaTeX/LuaLaTeX 支持

### `generator.py` — Markdown 生成

生成两个层级的输出：

**主页面** (`output/README.md`)：
- 汇总统计（追踪总数、活跃数、本周更新数）
- 总览表格：学校 | 模板名 | 版本 | 最近更新 | Stars | 活跃度 | 技术特性
- 按最近更新时间排序
- 活跃度标识：🟢 活跃（3 个月内有 commit）、🟡 一般（6 个月内）、🔴 不活跃（超过 6 个月）、⚪ 无数据

**学校详情页** (`output/universities/{school}.md`)：
- 该校所有模板的详细信息
- 版本历史（最近 5 个 release）
- 技术特性详情
- 仓库直达链接

### `main.py` — 主入口

```python
def main():
    # 1. 加载手动维护的仓库列表
    repos = load_repos("data/repos.json")

    # 2. 自动发现新仓库（可选）
    discovered = discover_new_repos(repos)
    repos = merge_discovered(repos, discovered)

    # 3. 抓取所有仓库的最新信息
    repo_data = [fetcher.fetch(r) for r in repos]

    # 4. 生成 Markdown 输出
    generator.generate_readme(repo_data, "output/README.md")
    generator.generate_detail_pages(repo_data, "output/universities/")

    # 5. 保存历史快照
    save_history(repo_data, "data/history.json")
```

## GitHub Actions 工作流

```yaml
name: Update Templates
on:
  schedule:
    - cron: '0 3 * * 1'  # 每周一 UTC 03:00（北京时间 11:00）
  workflow_dispatch:       # 支持手动触发

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python -m tracker.main
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add output/
          git diff --staged --quiet || git commit -m "chore: update template data [skip ci]"
          git push
```

## 错误处理

- 单个仓库抓取失败：记录错误日志，跳过该仓库，不影响其他仓库
- GitHub API 速率限制：自动等待并重试（PyGithub 内置处理）
- 搜索 API 失败：降级为只更新已知仓库，跳过自动发现
- 所有错误输出到 stderr，GitHub Actions 日志可见

## 种子数据

初始版本基于搜索结果和手动整理，覆盖 985/211 高校的主要模板，预计 30-50 个仓库。已知的主要仓库：

| 仓库 | 学校 | Stars |
|------|------|-------|
| mohuangrui/ucasthesis | 中国科学院大学 | 3.9k |
| sjtug/SJTUThesis | 上海交通大学 | 3.8k |
| TheNetAdmin/zjuthesis | 浙江大学 | 3.7k |
| ustctug/ustcthesis | 中国科学技术大学 | 2.1k |
| tuna/thuthesis | 清华大学 | — |
| NWPUMetaphysicsOffice/Yet-Another-LaTeX-Template-for-NPU-Thesis | 西北工业大学 | 594 |
| mengchaoheng/SCUT_thesis | 华南理工大学 | 554 |

## 未来扩展

以下不在当前设计范围内，但架构支持渐进演化：

- 静态网站：用生成的 JSON 数据驱动 Jekyll/Hugo 站点
- 历史趋势：利用 `history.json` 绘制 Stars/活跃度变化图表
- 自动提交新发现的仓库到 Issues 供人工审核
- 分类标签：支持按学院、学科分类
