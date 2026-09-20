这是 `docs/`、`research/` 或 `tasks/*/docs/` 下 Markdown 文件推荐的 Frontmatter 规范，复制并放置在文件最开头：

```markdown
---
type: architecture
title: 统一认证鉴权网关架构设计
status: active
resources:
  - code://src/gateway/auth_handler.go#L42-L180
  - doc://.context/docs/architecture-session-cache.md
tags: [auth, jwt, gateway]
created: 2026-09-04
updated: 2026-09-04
summary: 统一认证鉴权网关的架构设计，含 JWT 签发、多因子校验与分布式会话缓存边界
pinned: false
---

# 正文标题

正文内容从这里开始……
```

## 字段说明

| 字段 | 取值 | 说明 |
|---|---|---|
| `type` | `architecture` / `playbook` / `handoff` / `investigation` / `reading-map` / `report` / `llm-io` / `note` / `task` / `draft` | 决定文档性质并在 `docs/INDEX.md` 中分栏展示。 |
| `title` | 字符串 | 文档可读标题。省略时自动从 Markdown 首个 `#` 标题或文件名提取。 |
| `status` | `active` / `draft` / `in_progress` / `paused` / `completed` / `resolved` / `archived` | 当前生命周期状态。统一使用英文枚举。 |
| `resources` | URI 列表 | 关联的代码位置（如 `code://path/to/file.go#L10`）、外部系统（`issue://`）或其他文档（`doc://...`）。 |
| `tags` | 字符串数组 | 跨文档检索标签，方便通过 `grep 'tags:.*auth'` 快速收敛上下文。 |
| `created` / `updated` | `YYYY-MM-DD` | 每次修改更新 `updated`，同步脚本据此进行时效与归档计算。 |
| `summary` | 一句话（≤50字） | 进入 `docs/INDEX.md` 与 `manifest.jsonl`，概括核心结论或解决的问题。 |
| `pinned` | `true` / `false` | 设为 `true` 可豁免 30 天清理候选审查，适用于核心基线架构与永久手册。 |

## 设计原理与检索方式

通过结构化 Frontmatter 与根目录 `manifest.jsonl`，Agent 无需加载文件正文即可秒级获得上下文全貌。Markdown 间的相对链接和 `resources` 构成了清晰的知识依赖图谱。
