# Agent Context Bundle (.context/) Workspace Guide

`.context/` 是本地研发工作区与 Agent 上下文知识包。统一存放项目开发过程中的架构分析、问题排查、跨会话交接（Handoff）、一次性验证脚本、中间评测数据与沉淀的执行手册（Playbooks）。整体通过 `.gitignore` 排除，不污染 Git 主分支。

## Layout 目录布局

- `docs/` — 常青知识文档（架构设计、Playbook、排查总结、交接记录）。
- `research/` — 跨任务共享的研究与专项评测数据。
- `scripts/` — 工作区索引生成器与通用辅助脚本。
- `tasks/<slug>/` — 准入的任务单元。参见 [tasks/STATUS.md](tasks/STATUS.md)（状态看板）与 [tasks/REGISTRY.md](tasks/REGISTRY.md)（任务准入表）。

## Rules 核心规则

1. **唯一实体身份（Concept as ID）**：每个 Markdown 文档即为一个 Concept，其相对于根目录的路径（不带扩展名）为全局唯一 ID。
2. **知识关联网络（Knowledge Graph）**：文档间通过标准 Markdown 相对链接引用；文档与代码资产通过 Frontmatter 的 `resources`（如 `code://src/service.go#L30`）锚定。
3. **状态枚举**：统一使用标准英文枚举：`active` | `draft` | `in_progress` | `paused` | `completed` | `resolved` | `archived`。
4. **资产写入范围**：所有本地开发上下文、任务方案与评测脚本统一写入 `.context/`；仓库根目录 `docs/` 仅用于公共工程文档。
5. **命名规范**：`docs/` 与 `research/` 下遵循 `{type}-{descriptive-slug}[-{YYYYMMDD}].md`。快照类（`handoff`、`report`、`investigation`）带 `-YYYYMMDD` 日期后缀；常青类（`architecture`、`playbook`、`note`）不带日期后缀。
6. **任务内部资产**：`tasks/<task-slug>/` 下挂载的 `docs/*.md` 与 `plans/*.md` 亦纳管标准 Frontmatter 并由同步脚本收录；`inputs/`、`outputs/` 豁免 Frontmatter。
7. **文档归档**：历史或废弃文档通过设置 Frontmatter `status: archived` 归档。

## 双层索引自动化 (Dual-Layer Automation)

文档顶部的 YAML Frontmatter 是**机器真相层**。
`docs/INDEX.md`、`tasks/STATUS.md`、`CLEANUP.md` 和根目录 `manifest.jsonl` 由同步脚本自动生成。

同步命令：
```bash
python3 .context/scripts/sync_bundle.py
```

## 轻量待办 vs 规范任务

- **分钟/天级临时待办** $\rightarrow$ 直接修改根目录 `TODO.md`（纯 markdown checkbox，无需 frontmatter，不进索引）。
- **跨多次会话/有明确验收标准的复杂问题** $\rightarrow$ 在 `tasks/REGISTRY.md` 记录准入理由后创建独立任务目录 `tasks/<task-slug>/`。
