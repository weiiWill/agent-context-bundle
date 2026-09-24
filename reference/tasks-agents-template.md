# Tasks Directory Agent Guidelines (`tasks/AGENTS.md`)

> 本文档为 `.context/tasks/` 目录的就近局部规约，当 Agent 访问或操作此目录时自动生效。

## 1. 核心红线 (Core Invariants)
- **立项双通道铁律 (Strict Admission Gate)**：**严禁 Agent 未经人类批准私自新建 Task 目录！**
  仅允许两种途径：
  1. 用户显式要求立项（如“为 X 需求建一个任务”）；
  2. Agent 提出立项拆分提议，并**获得开发者明确确认**。
- **日志防膨胀自动分卷**：单个任务的 `progress.md` 累积超过 200 行时，必须主动切出 `progress-archive-YYYYMMDD.md`，主文件仅保留近 3 次流水与摘要。
- **任务台账必登记**：任何新立项任务，必须在 `.context/tasks/REGISTRY.md` 登记一行立项记录。

## 2. 标准 Task 目录骨架与规范
每个独立 Task 位于 `.context/tasks/<task-slug>/` 下，必须包含：

1. `README.md`（任务主控与方案）：
   ```yaml
   ---
   type: task
   title: "<任务清晰标题>"
   status: active | paused | completed
   created: YYYY-MM-DD
   updated: YYYY-MM-DD
   summary: "<任务目标与核心交付范围>"
   resources:
     - code://src/target_module.py
   ---
   # 任务目标与方案设计
   ```
2. `progress.md`（线性流水账）：
   每次实质推进追加时间戳记录：
   ```markdown
   - YYYY-MM-DD HH:MM: 完成模块 X 核心接口实现与单元测试覆盖。
   ```

## 3. 任务结项闭环门禁 (Task Conclusion SOP)
当任务开发完成准备结项时，必须依次执行：
1. **未竟事项清点**：运行 `grep 'task:<task-slug>' .context/TODO.md`，确认该任务下的待办全部处理或移交；
2. **主动提请经验萃取**：Agent 向开发者提请：“*本任务已完成。已梳理出方案，是否批准沉淀至 docs/<type>-<slug>.md？*”；
3. **闭环落盘**：获得批准后将方案提炼写入 `docs/`，并将本任务 `README.md` 的 `status` 置为 `completed`。
