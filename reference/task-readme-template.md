---
type: task
title: <任务名称>
status: in_progress
resources:
  - code://path/to/relevant_file.go#L10
  - doc://.context/docs/architecture-relevant.md
updated: YYYY-MM-DD
summary: 一句话说明该任务要解决什么问题、产出什么
---

# <任务名称>

## 目标 (Goal)
详细说明任务目标与验收标准（frontmatter 的 `summary` 是给索引脚本用的浓缩版，此处可充分展开）。

## 当前状态速览 (Status at a Glance)
| 项 | 值 |
|---|---|
| 状态 | `in_progress` / `paused` / `draft` / `completed` / `archived` |
| 最近更新 | YYYY-MM-DD |
| 相关分支/commit | |
| 核心代码资产 | 实际的代码路径（如 `src/service/processor.py`）——若路径失效表明任务需重新校准 |

## 关键结论与决策 (Key Conclusions)
### <主题 1>
架构设计决策，按主题细分为 `###` 小节，避免堆砌混杂。

## 进展记录 (Progress Log)
- YYYY-MM-DD: 做了什么、发现了什么、下一步计划。

> 当进展记录条目超过 5~8 条时，拆分到同级目录的 `progress.md` 中以 append-only 方式追加，保持 README 主控简洁。

## 未完成事项 (Open Items)

### 设计与业务待定 (Design Questions)
- [ ] ...

### 代码具体落地 (Code TODOs)
必须是具体、可核实的断言（如附带代码路径与函数/配置字段名），禁止含糊的“优化一下代码”：
- [ ] ...

---
**维护规则**：更新状态、更新时间或摘要时，只需编辑文件顶部的 Frontmatter 字段，无需重写整份文档。
改完后执行 `python3 .context/scripts/sync_bundle.py` 刷新 `tasks/STATUS.md` 与 `manifest.jsonl`。
连续超过 14 天未更新的活跃任务会被标记为 ⚠️ 停滞；已完成且超 30 天未触碰的会被归入 `CLEANUP.md`。
