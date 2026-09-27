---
type: task
title: <任务名称>
status: in_progress
resources:
  - code://path/to/relevant_file.py#L10
  - doc://.context/docs/architecture-relevant.md
created: YYYY-MM-DD
updated: YYYY-MM-DD
summary: 一句话说明该任务要解决什么问题、产出什么
---

# <任务名称>

## 1. 目标与验收标准 (Goal & Acceptance)
- **核心目标**：详细说明任务目标与交付物（Frontmatter 的 `summary` 是给索引脚本用的浓缩版，此处可充分展开）。
- **验收标准**：
  - [ ] 具体、可核实的验收条件 1
  - [ ] 具体、可核实的验收条件 2

## 2. 任务内部沙盒结构规范 (Sandboxing Anatomy)
本任务目录严格遵循 **2 核心文件 + 5 正交子目录** 结构，严禁创建任何别名目录：
- `README.md`：任务主控与大纲（本文件，带 Frontmatter）
- `progress.md`：线性推进流水日志（立项即创建，纯追加流水，超 200 行自动切卷归档）
- `inputs/`：测试数据集、外部原始输入、样本数据（豁免 Frontmatter）
- `outputs/`：评测运行产物、Trace 结果、中间导出产物（豁免 Frontmatter）
- `scripts/`：该任务特化评测、批量跑批、提取数据的专有脚本
- `plans/`：任务内拆解的详细实施方案或步骤说明（须带 Frontmatter）
- `docs/`：任务内特化排查总结、交接快照或设计说明（须带 Frontmatter）

> ⛔ **严禁创建别名目录**：禁止使用 `dataset/`（一律用 `inputs/`）、禁止使用 `eval/`（脚本进 `scripts/`，结果进 `outputs/`）、禁止使用 `report/` / `research/`（一律用 `docs/`）。

## 3. 当前状态速览 (Status at a Glance)
| 项 | 值 |
|---|---|
| 状态 | `in_progress` / `paused` / `draft` / `completed` / `archived` |
| 最近更新 | YYYY-MM-DD |
| 相关分支/Commit | |
| 核心代码资产 | 实际的代码路径（如 `src/service/processor.py`） |

## 4. 关键结论与决策 (Key Decisions)
### <决策主题 1>
- 记录核心架构设计决策，按主题细分为 `###` 小节，避免堆砌混杂。

## 5. 未完成事项 (Open Items)
### 架构与方案待定
- [ ] ...

### 具体落地待办 (Code TODOs)
- [ ] ...

---
**维护规则**：更新状态、更新时间或摘要时，只需编辑文件顶部的 Frontmatter 字段。
改完后执行 `python3 .context/scripts/sync_bundle.py` 刷新 `tasks/STATUS.md` 与 `manifest.jsonl`。
连续超过 14 天未更新的活跃任务会被标记为 🚨 停滞；暂停超过 30 天标记为 ⏸️ 停滞；已完成且超 30 天未触碰的会被归入 `CLEANUP.md`。
