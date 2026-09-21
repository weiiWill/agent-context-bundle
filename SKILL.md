---
name: agent-context-bundle
description: >-
  在项目里建立并维护 `.context/` 本地知识包(Knowledge Bundle)与 Agent 工作区。
  用来存放开发过程中的分析笔记、排查记录、跨会话交接(handoff)、临时脚本、评测数据及沉淀的架构决策与执行手册(playbook)。
  采用"以 Frontmatter 为唯一事实来源、自动生成结构化索引(manifest.jsonl)与汇总看板(INDEX/STATUS)、Markdown 相对链接构建关联网络"的设计，
  配套任务活跃度与时效治理及知识流转漏斗(草稿->任务执行->基准沉淀->归档清理)。
  提供隔离 Sub-agent 工作流编排，支持在新项目中执行 init 初始化以及在已有项目中执行 maintain 巡检维护。
---

# Agent Context Bundle 本地知识包规范

## 核心设计与工作区机制

开发过程中会产生大量高价值的上下文信息：架构分析、问题排查、跨会话交接记录、临时验证脚本、评测中间产物等。若直接提交进 Git 会污染仓库主干与提交历史；若散落在本地则容易流失且无法被 AI Agent 有效检索。

本项目规范将工作区定义为项目级 **Knowledge Bundle**（默认目录为 `.context/`，支持**团队共享模式**与**本地私有沙盒模式**）：
1. **零外部依赖**：纯 Markdown + YAML Frontmatter，无需额外数据库或专属 SDK。
2. **路径即唯一身份（Concept as ID）**：每个文件是一个 Concept，去扩展名的相对路径即为唯一 ID（如 `tasks/api-migration`）。
3. **图谱化关联（Knowledge Graph）**：文档之间通过标准 Markdown 相对链接引用；文档与代码资产通过 Frontmatter 的 `resources`（如 `code://src/service.go#L30`）锚定。
4. **唯一事实来源与自动生成看板（Source of Truth & Generated Views）**：每个文档头部的 YAML Frontmatter 是唯一真实数据源。脚本自动提取并生成供 Agent 5ms 检索的结构化索引（`manifest.jsonl`）与供开发者查阅的汇总看板（`INDEX.md`、`STATUS.md`）。
5. **知识流转漏斗**：支持从临时 Scratchpad（`TODO.md`）到深入 Task/Investigation，再提炼沉淀为长效 Playbook/Architecture 的正向知识流转。
6. **任务活跃度与时效治理**：针对修改自动触碰时间戳，针对 >14 天未更新任务触发停滞预警，针对 >30 天完成任务自动归入清理候选池。

---

## 核心规则与规范

1. **状态枚举**：统一使用标准英文枚举：`active` | `draft` | `in_progress` | `paused` | `completed` | `resolved` | `archived`。
2. **资产写入范围**：所有本地开发上下文、任务方案与评测脚本统一写入 `.context/`；仓库根目录 `docs/` 仅用于公共工程文档。
3. **命名规范**：`docs/` 与 `research/` 下遵循 `{type}-{descriptive-slug}[-{YYYYMMDD}].md`。快照类（`handoff`、`report`、`investigation`）带 `-YYYYMMDD` 日期后缀；长效架构与手册类（`architecture`、`playbook`、`note`）不带日期后缀。
4. **任务内部资产**：`tasks/<task-slug>/` 下挂载的 `docs/*.md` 与 `plans/*.md` 纳管标准 Frontmatter 并由同步脚本收录；`inputs/`、`outputs/` 豁免 Frontmatter。
5. **文档归档**：历史或废弃文档通过设置 Frontmatter `status: archived` 归档。
6. **任务边界与旁路问题留痕**：Agent 执行主任务时若发现非阻塞的次要问题或潜在优化点，严禁节外生枝扩大改动范围，应统一以 `- [ ] [<scope>] <代码位置>: <问题描述>` 追加写入 `.context/TODO.md` 留痕（`<scope>` 为 `global` 或 `task:<slug>`，任务结项时主动检索闭环）。
7. **Task 严格准入双通道**：Task 属于跨多轮会话的大型专项，严禁随意膨胀。新建 Task 仅允许两种方式：用户显式要求立项，或 Agent 提议拆分并**获得人工明确确认**。严禁 Agent 私自创建 Task 目录。

---

## 标准目录骨架

```
.context/
├── AGENTS.md                         # 本地工作区引导说明
├── manifest.jsonl                    # [结构化索引] 一行一个 Concept，供 Agent 用 jq/grep 直接解析
├── CLEANUP.md                        # [生命周期] 待归档/待清理候选清单，由脚本自动生成
├── TODO.md                           # 极轻量待办草稿（纯 markdown checkbox，无需 frontmatter）
├── docs/                             # 长期沉淀的核心规范 (Architecture, Playbooks, ADRs, 导航说明)
│   ├── INDEX.md                      # [自动生成看板] 文档分类索引，由脚本自动根据 frontmatter 渲染
│   └── <type>-<slug>[-YYYYMMDD].md   # 每个文档顶部带标准 Frontmatter
├── tasks/                            # 复杂任务生命周期
│   ├── REGISTRY.md                   # 顶层任务准入名单
│   ├── STATUS.md                     # [自动生成看板] 任务状态与活跃度监控看板，由脚本自动生成
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

## Frontmatter 规范（唯一事实来源 SSOT）

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
   - 基于 `reference/todo-template.md` 创建 `.context/TODO.md`（极轻量待办草稿，用于天级记录与旁路问题留痕）；
   - 基于 `reference/tasks-registry-template.md` 创建 `.context/tasks/REGISTRY.md`（任务准入表模板）。

5. **配置工程隔离与自动化守护 (Multi-Platform Hook Matrix)**：
   - **Git 纳管策略选择与配置**：
     - **方案 A（团队共享模式，默认推荐）**：在 `.gitignore` 中配置精细化忽略（仅忽略 `.context/TODO.md`、`tasks/*/progress.md`、`tasks/*/{inputs,outputs}/`），核心文档与 `manifest.jsonl` 纳入 Git 共享；执行 `bash .context/scripts/install_git_hook.sh` 安装 Git 提交拦截器。
     - **方案 B（本地私有沙盒模式）**：若严禁向主仓库提交任何辅助目录，在 `.gitignore` 中追加一行 `.context/` 整体排除，脚本将自动跳过 Git Hook，全权由 Agent 原生 Hook 负责实时同步。
   - 在仓库根目录 `AGENTS.md` 中追加文档维护章节与 `.context/AGENTS.md` 路由指引；
   - **自动化 Hook 矩阵感知与安装**：
     - 若检测到 Claude Code 环境（或存在 `.claude/` 目录），参考 `reference/hooks/claude-settings.json` 在 `.claude/settings.local.json` 中配置 `PostToolUse` 实时同步；
     - 若检测到 Google Antigravity 环境（或存在 `.agents/` 目录），参考 `reference/hooks/antigravity-hooks.json` 在 `.agents/hooks.json` 中配置原生 Hook。

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

### Workflow C: `task` 任务生命周期与结项闭环工作流 (Task Lifecycle & Conclusion SOP)

在日常多会话长线需求开发中，规范任务的准入、推进与半自动沉淀闭环：

1. **立项准入 (Task Admission)**：
   - **触发场景**：用户显式指令（如“为 X 需求建一个任务”）或 Agent 提议拆分并经人工批准；
   - **执行动作**：在 `.context/tasks/<task-slug>/` 下创建 `README.md`（包含 Frontmatter 元数据、目标与代码锚点）和 `progress.md`（纯线性流水），并在 `.context/tasks/REGISTRY.md` 中追加立项记录；
   - **铁律**：严禁 Agent 未经人工明确确认擅自新建任务目录。

2. **推进打卡 (Task Progress)**：
   - **执行动作**：向 `.context/tasks/<task-slug>/progress.md` 追加时间戳推进流水；
   - **自动续期**：底层 Hook 自动将同级 `README.md` 的 `updated:` 字段续期至今日；
   - **自动分卷**：当 `progress.md` 累积超过 200 行时，自动切出 `progress-archive-*.md`，当前文件仅保留摘要与近期流水。

3. **结项与半自动萃取闭环 (Task Conclusion Gate)**：
   - **触发场景**：用户表示“任务已完成 / 准备结项”或 Agent 提请结项；
   - **步骤 1（待办审计）**：执行 `grep 'task:<task-slug>' .context/TODO.md`，向开发者汇报是否有未竟待办并协助清理；
   - **步骤 2（沉淀提议）**：Agent 主动分析该 task 的核心方案与排障经过，向开发者提请：“*本任务已完成。已梳理出《<标题>》，是否批准沉淀至 docs/<type>-<slug>.md？*”；
   - **步骤 3（落盘更新）**：经开发者确认后，生成沉淀文档并绑定 `resources: code://...`，将任务 `README.md` 的 `status` 置为 `completed`。

---

### Workflow D: `distill` 文档沉淀与经验提炼工作流 (Knowledge Distillation)

在日常排障或模块重构后，支持将当前会话的上下文资产快速转化为项目基线资产：

1. **触发意图**：
   - 开发者显式命令：“*把刚才排查 X 的过程沉淀一份 playbook*”、“*把刚才重构的架构设计沉淀成文档*”。
2. **提炼与锚定规范**：
   - 调取 `reference/doc-template.md` 规范模板；
   - 结合当前会话中真实发生的根因分析、排查步骤或技术方案提炼正文；
   - 必须通过 `resources` 显式锚定物理代码行（如 `code://src/service/processor.py#L45-L120`）；
   - 根据价值设定属性：高价值核心设计命名不带日期（如 `architecture-pipeline.md`）并标记 `pinned: true`；阶段性交接带日期后缀（如 `handoff-auth-20260921.md`）；
3. **写入与自动收录**：
   - 写入 `docs/` 目录，底层 Hook 自动在 15ms 内刷新 `manifest.jsonl` 与 `docs/INDEX.md`。

---

## 参考与模板

* [Context 顶层导航与 SOP 模板](reference/context-readme-template.md)
* [标准 Frontmatter 示例](reference/docs-frontmatter-example.md)
* [Frontmatter JSON Schema 规范](reference/schema/context-frontmatter.schema.json)
* [VSCode YAML 补全与校验配置](reference/schema/vscode-settings-snippet.json)
* [Claude Code Hook 配置模板](reference/hooks/claude-settings.json)
* [Antigravity Hook 配置模板](reference/hooks/antigravity-hooks.json)
* [Git Pre-commit 兜底 Hook 安装器](reference/hooks/install-git-hook.sh)
* [文档索引看板 INDEX.md 模板](reference/docs-index-template.md)
* [任务准入表 REGISTRY.md 模板](reference/tasks-registry-template.md)
* [任务主控 README 模板](reference/task-readme-template.md)
* [长任务 progress.md 模板](reference/task-progress-template.md)
* [轻量草稿 TODO.md 模板](reference/todo-template.md)
* [Bundle 索引同步脚本](reference/sync-bundle-script.py)
* [Frontmatter 自动续期脚本](reference/bump-updated-script.py)
