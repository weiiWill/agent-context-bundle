---
name: agent-context-bundle
description: >-
  在项目里建立并维护 `.context/` 本地知识包与 Agent 记忆工作区。
  当需要：(1) 初始化知识库工作区与原生 Hook 门禁 (init)；(2) 全仓健康体检、修复断链与停滞治理 (maintain/doctor)；
  (3) 规范发起、推进与结项复杂长线任务 (task)；(4) 提炼沉淀架构方案与排障手册 (distill) 时使用。
---

# Agent Context Bundle 本地知识包规范

## 核心设计与工作区机制

本项目规范将工作区定义为项目级 **Knowledge Bundle**（默认目录为 `.context/`，支持团队共享模式与本地私有沙盒模式）：
1. **零外部依赖**：纯 Markdown + YAML Frontmatter，由纯 Python 标准库驱动，无第三方依赖。
2. **路径即唯一身份（Concept as ID）**：每个文件是一个 Concept，去扩展名的相对路径即为唯一 ID（如 `tasks/api-migration`）。
3. **图谱化关联（Knowledge Graph）**：文档之间通过标准 Markdown 相对链接引用；文档与代码资产通过 Frontmatter 的 `resources`（如 `code://src/service.py#L30`）精准锚定。
4. **唯一事实来源与自动生成看板（SSOT & Generated Views）**：每个文档头部的 YAML Frontmatter 是唯一真实数据源。脚本自动提取并生成供 Agent 毫秒级流式检索的结构化索引（`manifest.jsonl`）与供开发者查阅的汇总看板（`INDEX.md`、`STATUS.md`、`CLEANUP.md`）。
5. **知识流转漏斗**：支持从临时待办（`TODO.md`）到深入任务沙盒（`tasks/<slug>/`），再提炼沉淀为长效架构与手册（`docs/`）的正向流转。
6. **任务活跃度与时效治理**：修改流水自动续期主控时间戳；>14 天未更新触发停滞预警；>30 天完成或超期暂停任务归入待归档候选池。

---

## 核心规则与正交目录结构

### 1. 核心铁律
1. **写后必同步闭环 (Write-then-Sync)**：凡在 `.context/` 下新增、修改或删除 Markdown 文档，必须在同一轮会话中调用 `python3 .context/scripts/sync_bundle.py` 刷新看板与索引。外部 Hook 作为人类编辑时的环境兜底。
2. **Frontmatter 强制门禁**：除 `TODO.md`、`progress.md` 以及 `inputs/`、`outputs/` 外，所有文档顶部必须包含合法的 YAML Frontmatter（包含 `type`, `title`, `status`, `created`, `updated`, `summary` 及代码锚点 `resources`）。
3. **Task 严格准入双通道**：Task 属于跨会话大型专项，严禁随意建立。新建 Task 仅允许两种方式：用户显式要求立项，或 Agent 提议拆分并**获得人工明确确认**。
4. **拒绝规范倒灌**：工程内部仅保留单一高信噪比的 `.context/AGENTS.md`（≤30行），严禁在子目录生成冗余的子级 `AGENTS.md`。

### 2. 标准目录骨架
```text
.context/
├── AGENTS.md                         # 本地工作区极简路由说明 (≤30行)
├── manifest.jsonl                    # [结构化索引] 单行单 Concept，供 Agent 用 grep/jq 流式解析
├── CLEANUP.md                        # [生命周期] 待归档/待清理审理候选看板 (自动生成)
├── TODO.md                           # 极轻量待办草稿 (- [ ] [global] 或 - [ ] [task:<slug>])
├── docs/                             # 长期沉淀的核心资产 (Architecture, Playbooks, ADRs)
│   ├── INDEX.md                      # [自动生成看板] 分类聚合索引
│   └── <type>-<slug>[-YYYYMMDD].md   # 标准沉淀文档 (带 Frontmatter)
├── tasks/                            # 复杂长线任务沙盒
│   ├── REGISTRY.md                   # 任务准入与交付台账
│   ├── STATUS.md                     # [自动生成看板] 任务状态与活跃度监控看板
│   └── <task-slug>/                  # 【2 核心文件 + 5 正交子目录】
│       ├── README.md                 # [核心 1] 任务主控、目标与验收标准 (带 Frontmatter)
│       ├── progress.md               # [核心 2] 纯追加流水日志 (超长自动分卷归档)
│       ├── inputs/                   # 测试数据、外部输入、样本样本 (豁免 Frontmatter)
│       ├── outputs/                  # 评测运行产物、Trace 结果、导出报表 (豁免 Frontmatter)
│       ├── scripts/                  # 该任务特化评测、批量跑批、提取脚本
│       ├── plans/                    # 任务内拆解的详细实施方案 (须带 Frontmatter)
│       └── docs/                     # 任务内特化排查总结、交接快照 (须带 Frontmatter)
├── research/                         # 探索性专项调研 (带 Frontmatter)
└── scripts/
    ├── sync_bundle.py                # 索引同步与 --doctor 门禁校验引擎
    ├── bump_updated.py               # Frontmatter updated 修改日期自动续期工具
    └── install_hooks.py              # 宿主框架生命周期 Hook 自动感知与注入器
```

> ⛔ **Task 目录别名禁令**：严禁在 `tasks/<slug>/` 下新建 `dataset/`（统一归入 `inputs/`）、`eval/`（脚本归入 `scripts/`，产物归入 `outputs/`）、`report/` 或 `research/`（统一归入 `docs/`）。违者将被 `--doctor` 机械化拦截阻断！

---

## Frontmatter 规范 (唯一事实来源 SSOT)

`docs/`、`research/`、`tasks/*/docs/`、`tasks/*/plans/` 以及 `tasks/*/README.md` 顶部必须包含标准 YAML Frontmatter：

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
pinned: false                         # 设为 true 可永久豁免定期归档与清理审理
---
```

---

## 隔离 Agent 工作流编排 (Sub-agent Workflows)

为保持主会话上下文窗口的干净专注，推荐派发隔离的子 Agent 独立执行脚手架创建或巡检。

### Workflow A: `init` 工作流 (在新项目中初始化)

1. **环境探查**：检查项目根目录是否存在 `.context/`；若已有，提示并切换为维护流程；
2. **建立标准骨架**：创建 `docs/`、`research/`、`tasks/`、`scripts/` 与 `schema/`；
3. **植入自动化引擎**：
   - 写入 `reference/sync-bundle-script.py` -> `.context/scripts/sync_bundle.py`；
   - 写入 `reference/bump-updated-script.py` -> `.context/scripts/bump_updated.py`；
   - 写入 `reference/hooks/install_hooks.py` -> `.context/scripts/install_hooks.py`；
   - 写入 `reference/hooks/install_git_hook.sh` -> `.context/scripts/install_git_hook.sh`；
   - 赋予执行权限：`chmod +x .context/scripts/*.py .context/scripts/*.sh`。
4. **初始化模板文件**：
   - 基于 `reference/context-readme-template.md` 创建 `.context/AGENTS.md`（极简工作区路由）；
   - 基于 `reference/todo-template.md` 创建 `.context/TODO.md`；
   - 基于 `reference/tasks-registry-template.md` 创建 `.context/tasks/REGISTRY.md`。
5. **框架感知与 Hook 原生注入**：
   - 运行 `python3 .context/scripts/install_hooks.py`；
   - **Google Antigravity**：写入 `.agents/hooks.json`，在 `PostToolUse` 中绑定正则 matcher 并严格遵守 stdout `{}` 契约；
   - **Claude Code**：写入 `.claude/settings.local.json`，在 `PostToolUse` 中绑定 `Write(.context/**)`；
   - **Git 门禁**：在 Git 纳管模式下注入 `.git/hooks/pre-commit`，绑定 `--doctor` 体检。
6. **首次全量同步**：
   - 运行 `python3 .context/scripts/sync_bundle.py` 生成初始索引与看板；
   - 运行 `python3 .context/scripts/sync_bundle.py --doctor` 确认全项 PASS。

---

### Workflow B: `maintain` 工作流 (在现有项目中巡检与时效治理)

1. **机械化全盘健康诊断 (`sync_bundle.py --doctor`)**：
   - 运行 `python3 .context/scripts/sync_bundle.py --doctor`，执行 5 重硬门禁自检：
     - **[1/5] 顶层骨架白名单**：拦截非法顶层目录与散落文件；
     - **[2/5] 任务子目录白名单**：严格锁定 `inputs`, `outputs`, `scripts`, `plans`, `docs`，拦截非法别名；
     - **[3/5] 任务沙盒隔离域**：全词边界匹配拦截泄漏至全局 `docs/` 的任务特化文档；
     - **[4/5] 任务生命周期完整性**：检查所有任务是否具备非空的 `README.md`（带 Frontmatter）与 `progress.md`；
     - **[5/5] 大文件冷数据审计**：跨平台审计并拦截 >5MB 的未纳管大文件；
   - 若 Doctor 报告 FAIL，立即就地定位并执行结构规整。
2. **图谱断链检测与修复**：检查 `manifest.jsonl` 中的 `links` 与 `resources`，修复 404 断链；
3. **时效与停滞治理**：
   - 检查 🚨 停滞任务（活跃且 >14 天未更新）与 ⏸️ 僵尸暂停任务（`paused` 且 >30 天未更新）；
   - 整理 `CLEANUP.md` 待清理候选池（>30 天完成/超期暂停任务），经用户确认后归档为 `archived`；
4. **Hook 自愈与全量刷新**：
   - 运行 `python3 .context/scripts/install_hooks.py` 自愈缺失的 Hook；
   - 运行 `python3 .context/scripts/sync_bundle.py` 完成看板刷新。

---

### Workflow C: `task` 任务生命周期与结项闭环工作流

1. **立项准入 (Task Admission)**：
   - 用户显式指令或提议获人工确认后，在 `tasks/<slug>/` 下同时创建 `README.md` 与 `progress.md`，并在 `tasks/REGISTRY.md` 中登记；
2. **推进打卡 (Task Progress)**：
   - 向 `tasks/<slug>/progress.md` 追加流水；更新同级 `README.md` 的 `updated:` 字段；
   - 当 `progress.md` 累积超过 200 行时，自动切出 `progress-archive-*.md`；
3. **结项闭环 (Task Conclusion Gate)**：
   - **待办闭环**：执行 `grep 'task:<slug>' .context/TODO.md`，清理未竟待办；
   - **沉淀提请**：Agent 主动分析核心成果，向开发者提请将高价值经验提炼至 `docs/`；
   - **状态结项与必同步**：将任务 `README.md` 的 `status` 置为 `completed`，并**主动执行 `python3 .context/scripts/sync_bundle.py` 刷新全局看板**。

---

### Workflow D: `distill` 文档沉淀与经验提炼工作流

1. **提炼与锚定规范**：
   - 调取 `reference/doc-template.md` 规范模板；
   - 必须通过 `resources: code://...` 显式锚定物理代码行；
   - 命名遵循 `{type}-{slug}[-{YYYYMMDD}].md` 范式；
2. **写入与主动闭环**：
   - 写入 `docs/` 目录；
   - **Agent 必须立即执行 `python3 .context/scripts/sync_bundle.py` 刷新全局索引与看板**。

---

## 参考与模板

* [Context 工作区指引模板](reference/context-readme-template.md)
* [标准文档创建模板](reference/doc-template.md)
* [标准 Frontmatter 示例](reference/docs-frontmatter-example.md)
* [任务主控 README 模板](reference/task-readme-template.md)
* [长任务 progress.md 模板](reference/task-progress-template.md)
* [轻量草稿 TODO.md 模板](reference/todo-template.md)
* [任务准入表 REGISTRY.md 模板](reference/tasks-registry-template.md)
* [自动化 Hook 配置详细指南](reference/optional-auto-sync-hook.md)
* [Google Antigravity Hook 模板](reference/hooks/antigravity-hooks.json)
* [Claude Code Hook 模板](reference/hooks/claude-settings.json)
* [Git Pre-commit 门禁安装脚本](reference/hooks/install_git_hook.sh)
* [多框架 Hook 自动探查与注入脚本](reference/hooks/install_hooks.py)
* [Bundle 索引同步引擎](reference/sync-bundle-script.py)
* [Frontmatter 自动续期工具](reference/bump-updated-script.py)
