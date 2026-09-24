# Docs Directory Agent Guidelines (`docs/AGENTS.md`)

> 本文档为 `.context/docs/` 目录的就近局部规约，当 Agent 访问或操作此目录时自动生效。

## 1. 核心红线 (Core Invariants)
- **严禁裸 Markdown (Zero Raw Markdown)**：本目录下的所有文档必须在头部包含合法的 YAML Frontmatter；严禁直接写纯文本正文。
- **单一职责原则**：单篇文档仅聚焦一个清晰的架构方案、操作手册或总结报告，不写万字大杂烩。
- **物理代码锚定 (Mandatory Code Anchors)**：任何架构、手册或排查文档，必须在 Frontmatter 的 `resources` 中提供具体代码行锚点（如 `code://src/path.py#L10-L50`）。

## 2. 命名范式规范 (Naming Conventions)
本目录下文件名严格遵循 `{type}-{slug}[-{YYYYMMDD}].md` 范式：

| 类型 (type) | 命名范式 | 说明与示例 |
| :--- | :--- | :--- |
| `report` | `report-<slug>-YYYYMMDD.md` | **有时效性快照**，必须带日期。例：`report-project-closure-20260923.md` |
| `handoff` | `handoff-<slug>-YYYYMMDD.md` | **跨会话交接凭证**，必须带日期。例：`handoff-auth-refactor-20260924.md` |
| `investigation`| `investigation-<slug>-YYYYMMDD.md` | **重大故障专项排查**，必须带日期。例：`investigation-memory-leak-20260924.md` |
| `architecture` | `architecture-<slug>.md` | **长效核心架构**，严禁带日期后缀。例：`architecture-sync-engine.md` |
| `playbook` | `playbook-<slug>.md` | **长效排障与执行手册**，严禁带日期后缀。例：`playbook-deploy-rollback.md` |
| `note` | `note-<slug>.md` | **长效工程参考笔记**，严禁带日期后缀。例：`note-api-conventions.md` |

## 3. YAML Frontmatter 强制契约 (Schema Contract)
每次新建文档必须包含以下完整结构：

```yaml
---
type: architecture | playbook | report | handoff | investigation | note
title: "<简洁专业的文档标题>"
status: active | completed | resolved | archived
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
summary: "<一句话大白话摘要，50字以内，禁止废话>"
pinned: true | false          # 核心基线设为 true，防止 30 天清理算法触碰
resources:
  - code://src/relative/path.py#L1-L50
  - doc://.context/docs/relative-doc.md
---
```

## 4. 淘汰与归档 (Archival)
已过时或废弃的文档严禁物理删除，统一通过将 Frontmatter 改为 `status: archived` 软归档，由自动化治理工具统一汇总到 `CLEANUP.md`。
