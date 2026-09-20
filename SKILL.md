---
name: agent-context-bundle
description: >-
  在项目里建立并维护 `.context/` 本地知识包(Knowledge Bundle)与 Agent 工作区。
  用来存放开发过程中的分析笔记、排查记录、跨会话交接(handoff)、临时脚本、评测数据及沉淀的架构决策与执行手册(playbook)。
  采用"机器可解析的 Frontmatter 作为真相层、INDEX.md/STATUS.md 由脚本自动生成作为展示层、Markdown 相对链接作为语义网络"的标准设计，
  配套自动化双层索引脚本与知识提炼流转管道(草稿->任务排查->长效沉淀->归档清理)。
  提供隔离 Sub-agent 工作流编排，支持在新项目中执行 init 初始化以及在已有项目中执行 maintain 巡检维护。
---

# Agent Context Bundle 本地知识包规范

## 核心设计与工作区机制

开发过程中会产生大量高价值的上下文信息：架构分析、问题排查、跨会话交接记录、临时验证脚本、评测中间产物等。若直接提交进 Git 会污染仓库主干与提交历史；若散落在本地则容易流失且无法被 AI Agent 有效检索。

本项目规范将本地工作区定义为项目级 **Knowledge Bundle**（默认目录为 `.context/`，整体由 `.gitignore` 排除）：
1. **零外部依赖**：纯 Markdown + YAML Frontmatter，无需额外数据库或专属 SDK。
2. **路径即唯一身份（Concept as ID）**：每个文件是一个 Concept，去扩展名的相对路径即为唯一 ID（如 `tasks/api-migration`）。
3. **图谱化关联（Knowledge Graph）**：文档之间通过标准 Markdown 相对链接引用；文档与代码资产通过 Frontmatter 的 `resources`（如 `code://src/service.go#L30`）锚定。
4. **双层架构（Machine Truth + Human Presentation）**：机器检索靠 `manifest.jsonl`，人类浏览靠脚本自动渲染的 `INDEX.md` 与 `STATUS.md`。
5. **知识提炼漏斗**：支持从临时 Scratchpad（`TODO.md`）到深入 Task/Investigation，再提炼沉淀为常青 Playbook/Architecture 的正向知识流转。

---

## 核心规则与规范

1. **状态枚举**：统一使用标准英文枚举：`active` | `draft` | `in_progress` | `paused` | `completed` | `resolved` | `archived`。
2. **资产写入范围**：所有本地开发上下文、任务方案与评测脚本统一写入 `.context/`；仓库根目录 `docs/` 仅用于公共工程文档。
3. **命名规范**：`docs/` 与 `research/` 下遵循 `{type}-{descriptive-slug}[-{YYYYMMDD}].md`。快照类（`handoff`、`report`、`investigation`）带 `-YYYYMMDD` 日期后缀；常青类（`architecture`、`playbook`、`note`）不带日期后缀。
4. **任务内部资产**：`tasks/<task-slug>/` 下挂载的 `docs/*.md` 与 `plans/*.md` 纳管标准 Frontmatter 并由同步脚本收录；`inputs/`、`outputs/` 豁免 Frontmatter。
5. **文档归档**：历史或废弃文档通过设置 Frontmatter `status: archived` 归档。

---

## 标准目录骨架

```
.context/
├── AGENTS.md                         # 本地工作区引导说明
├── manifest.jsonl                    # [机器索引] 一行一个 Concept，供 Agent 用 jq/grep 直接解析
├── CLEANUP.md                        # [生命周期] 待归档/待清理候选清单，由脚本自动生成
├── TODO.md                           # 极轻量待办草稿（纯 markdown checkbox，无需 frontmatter）
├── docs/                             # 常青知识 (Architecture, Playbooks, ADRs, 导航说明)
│   ├── INDEX.md                      # [展示层] 人类可读索引，由脚本自动根据 frontmatter 渲染
│   └── <type>-<slug>[-YYYYMMDD].md   # 每个文档顶部带标准 Frontmatter
├── tasks/                            # 复杂任务生命周期
│   ├── REGISTRY.md                   # 顶层任务准入名单
│   ├── STATUS.md                     # [展示层] 任务状态与停滞扫描看板，由脚本自动生成
│   └── <task-slug>/
│       ├── README.md                 # 任务主控 (带标准 Frontmatter)
│       ├── progress.md               # 线性推进日志 (超长自动分卷归档)
│       └── (按需) inputs/ outputs/ scripts/ plans/ docs/
├── research/                         # 探索性专项调研，同样带 Frontmatter
└── scripts/
    ├── sync_bundle.py                # 核心 Bundle 索引生成与 Schema 校验脚本
    └── bump_updated.py               # Frontmatter updated 字段自动续期工具
```

---

## Frontmatter 规范（机器真相层）

`docs/`、`research/`、`tasks/*/docs/`、`tasks/*/plans/` 以及 `tasks/*/README.md` 顶部包含标准 YAML Frontmatter：

```yaml
---
type: architecture | playbook | handoff | investigation | reading-map | report | llm-io | note | task | draft
title: 文档或任务名称
status: active | draft | in_progress | paused | completed | resolved | archived
resources:
  - code://src/service/processor.py#L45-L120
  - doc://.context/docs/architecture-pipeline.md
tags: [data-pipeline, streaming, cache]
created: YYYY-MM-DD
updated: YYYY-MM-DD
summary: 一句话说明该文档解决了什么问题或讲了什么核心内容 (≤50字)
pinned: false                         # 设为 true 可永久豁免定期归档与清理候选
---
```

---

## 隔离 Agent 工作流编排 (Isolated Sub-agent Workflows)

由于初始化脚手架与全仓上下文巡检包含较多文件读写与路径扫描，为保持主会话上下文窗口的干净专注，**优先派发隔离的子 Agent（Sub-agent）独立执行**。

主 Agent 编排模式：
```python
invoke_subagent(
    Role="Context Bundle Engineer",
    TypeName="self",
    Prompt="""...执行具体 Workflow A (init) 或 Workflow B (maintain)..."""
)
```

### Workflow A: `init` 工作流 (在新项目中初始化)

当需要在新项目中建立 `.context/` 知识包时，子 Agent 按以下步骤执行：

1. **环境探查**：
   - 检查项目根目录是否存在 `.context/`；若已有，提示并切换为维护流程；
   - 检查根目录 `.gitignore` 是否存在；
   - 检查根目录是否存在 `AGENTS.md`。

2. **建立标准目录骨架**：
   - 创建 `.context/docs/`、`.context/research/`、`.context/tasks/`、`.context/scripts/`。

3. **植入自动化引擎与校验规范**：
   - 将 `reference/sync-bundle-script.py` 写入 `.context/scripts/sync_bundle.py`；
   - 将 `reference/bump-updated-script.py` 写入 `.context/scripts/bump_updated.py`；
   - 将 `reference/hooks/install-git-hook.sh` 写入 `.context/scripts/install_git_hook.sh`；
   - 将 `reference/schema/context-frontmatter.schema.json` 写入 `.context/schema/context-frontmatter.schema.json`；
   - 赋予执行权限：`chmod +x .context/scripts/*.py .context/scripts/*.sh`。

4. **初始化模板与待办**：
   - 基于 `reference/context-readme-template.md` 创建 `.context/AGENTS.md`（包含完整 Agent SOP 与三级降级路径）；
   - 创建 `.context/TODO.md`（极轻量待办模板）；
   - 创建 `.context/tasks/REGISTRY.md`（任务准入表模板）。

5. **配置工程隔离与自动化守护 (Multi-Platform Hook Matrix)**：
   - 在项目根目录 `.gitignore` 中追加一行 `.context/`，确保过程资产不污染 Git；
   - 在仓库根目录 `AGENTS.md` 中追加文档维护章节与 `.context/AGENTS.md` 路由指引；
   - **自动化 Hook 矩阵感知与安装**：
     - 若检测到 Claude Code 环境（或存在 `.claude/` 目录），参考 `reference/hooks/claude-settings.json` 在 `.claude/settings.local.json` 中配置 `PostToolUse` 实时同步；
     - 若检测到 Google Antigravity 环境（或存在 `.agents/` 目录），参考 `reference/hooks/antigravity-hooks.json` 在 `.agents/hooks.json` 中配置原生 Hook；
     - 执行 `bash .context/scripts/install_git_hook.sh` 安装本地 Git 提交兜底拦截器。

6. **初次索引编译与自检**：
   - 运行 `python3 .context/scripts/sync_bundle.py`；
   - 确认生成初始 `manifest.jsonl`、`docs/INDEX.md`、`tasks/STATUS.md`、`CLEANUP.md`；
   - 向主 Agent 返回初始化成功摘要、目录清单及已启用的 Hook 状态。

---

### Workflow B: `maintain` 工作流 (在现有项目中巡检与维护)

当需要对现有的 `.context/` 知识包进行健康检查、死链扫描或时效治理时，子 Agent 按以下步骤执行：

1. **Frontmatter 规范性校验**：
   - 扫描 `.context/` 下除 `TODO.md`、`progress.md` 及自动生成文件外的所有 Markdown；
   - 依据 `context-frontmatter.schema.json` 检查必须包含合法 Frontmatter（`type`, `status`, `updated`, `summary`）；
   - 检查 `status` 是否属于标准英文枚举值，发现非标格式直接修复。

2. **链接图谱与断链检测**：
   - 扫描所有正文内的 Markdown 相对链接 `[label](relative/path)`；
   - 校验相对路径指向的目标文件是否存在，若发现 404 断链则进行路径修复；
   - 校验 `resources` 中的 `code://` 与 `doc://` 资源路径是否有效。

3. **执行全量索引同步**：
   - 运行 `python3 .context/scripts/sync_bundle.py`；
   - 确保 `manifest.jsonl`、`docs/INDEX.md`、`tasks/STATUS.md` 与 `CLEANUP.md` 处于最新状态。

4. **时效与停滞治理分析**：
   - 统计 ⚠️ 停滞任务（`in_progress` / `active` 且 >14 天未更新）；
   - 统计 🗑️ 清理候选（`completed` / `resolved` / `archived` 且 >30 天未触碰且未 `pinned: true`）；
   - 如有需要归档的任务，经确认后将状态置为 `archived` 并重新同步。

5. **输出结构化巡检报告**：
   - 向主 Agent 返回概览：纳管文档总数、任务状态分布、断链修复数量、停滞告警清单。

---

## 参考与模板

* [Context 顶层导航与 SOP 模板](reference/context-readme-template.md)
* [标准 Frontmatter 示例](reference/docs-frontmatter-example.md)
* [Frontmatter JSON Schema 规范](reference/schema/context-frontmatter.schema.json)
* [VSCode YAML 补全与校验配置](reference/schema/vscode-settings-snippet.json)
* [Claude Code Hook 配置模板](reference/hooks/claude-settings.json)
* [Antigravity Hook 配置模板](reference/hooks/antigravity-hooks.json)
* [Git Pre-commit 兜底 Hook 安装器](reference/hooks/install-git-hook.sh)
* [文档展示层 INDEX.md 模板](reference/docs-index-template.md)
* [任务主控 README 模板](reference/task-readme-template.md)
* [长任务 progress.md 模板](reference/task-progress-template.md)
* [Bundle 索引同步脚本](reference/sync-bundle-script.py)
* [Frontmatter 自动续期脚本](reference/bump-updated-script.py)
