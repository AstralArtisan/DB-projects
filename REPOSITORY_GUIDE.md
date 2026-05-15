# 数据库课程项目仓库管理指南

本仓库用于管理四次数据库课程 project 的框架、数据、代码、实验报告和报告图片。当前按主题聚合项目：Olist 电商线放在 `projects/ecommerce/`，SimpleDB 实验放在 `projects/simpledb/`。仓库远程地址：

```bash
git@github.com:AstralArtisan/DB-projects.git
```

## 收录范围

应提交：

- 四次 project 的课程框架与必要说明文件
- 已完成或正在维护的源码、SQL、配置文件
- 实验数据、清洗后的数据、结果数据
- 实验报告、设计报告、报告中引用的图片和源图文件
- 与复现实验直接相关的 `requirements.txt`、`pyproject.toml`、README 等

不应提交：

- `.claude/`、`.codex/`
- 任意目录下的 `CLAUDE.md`、`AGENTS.md`
- Python 缓存：`__pycache__/`、`*.pyc`
- 课程提交压缩包、重复归档包：`*.zip`
- 弃用代码、不再使用的图片和临时文件
- 本次已确认弃用的 `projects/ecommerce/proj1/project1_sql脚本示例&前端代码框架/`

## 每次提交前检查

1. 查看当前变化：

```bash
git status --short
```

2. 检查是否有不应提交的文件：

```bash
git status --short --ignored
git check-ignore -v projects/ecommerce/proj1/.claude/settings.local.json
git check-ignore -v projects/ecommerce/proj1/CLAUDE.md
git check-ignore -v projects/ecommerce/proj3/AGENTS.md
git check-ignore -v projects/ecommerce/proj1/submit.zip
```

3. 检查大文件。GitHub 普通 Git 单文件硬限制是 100MB；接近该限制时不要直接提交，应改用 Git LFS 或只提交样例数据与获取说明。

```bash
git ls-files | xargs -I{} powershell -NoProfile -Command "if (Test-Path '{}') { $f = Get-Item '{}'; if ($f.Length -gt 90000000) { Write-Output \"$($f.FullName) $($f.Length)\" } }"
```

在 Windows PowerShell 中也可以用：

```powershell
Get-ChildItem -Recurse -File |
  Sort-Object Length -Descending |
  Select-Object -First 20 FullName,Length
```

4. 暂存后再次确认清单：

```bash
git add -A
git status --short
git diff --cached --stat
```

## Commit 规范

提交信息使用 Lore Commit Protocol：第一行写变更意图，正文解释约束和取舍，末尾用 git trailer 记录验证情况。

模板：

```text
<why this change exists>

<context, constraints, and approach>

Constraint: <external constraint>
Rejected: <alternative> | <reason>
Confidence: <low|medium|high>
Scope-risk: <narrow|moderate|broad>
Directive: <future warning>
Tested: <verification performed>
Not-tested: <known gaps>
```

示例：

```text
Preserve project 1 deliverables for reproducible review

Project 1 is complete, so this commit records its code, data,
reports, and diagrams while leaving local agent metadata out of
the public repository.

Constraint: Course materials include CSV data that must remain available
Rejected: Commit submit.zip | duplicates tracked source and reports
Confidence: high
Scope-risk: narrow
Directive: Keep local agent files and generated caches ignored
Tested: git status --short; git diff --cached --stat
Not-tested: Re-running full project scripts
```

## 推荐工作流

初始化后常用流程：

```bash
git status --short
git add -A
git diff --cached --stat
git commit
git push
```

新增 project 或整理已有 project 时，优先保持结构清晰：

- `src/` 或主程序文件：代码
- `data/` 或明确命名的数据目录：输入数据
- `reports/`、PDF、Markdown：实验报告
- `figures/`、`images/` 或明确命名图片：报告图片
- `README.md`：运行方式、依赖、数据说明

当前推荐布局：

```text
projects/
  ecommerce/
    shared/
    proj1/
    proj3/
    proj4/
  simpledb/
    proj2/
```

`projects/ecommerce/shared/` 只放跨 project 的配置示例、数据库前置检查和说明，不放 Olist 原始 CSV；原始数据仍归属 `projects/ecommerce/proj1/`。

如果出现弃用代码或不用图片，先移动到本地未跟踪位置或加入 `.gitignore`，不要把不再使用的材料混入提交。
