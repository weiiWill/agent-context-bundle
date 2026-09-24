# Agent Context Bundle (.context/) 工作区指引

本目录统一存放项目开发过程中的架构方案、任务追踪、排查记录与沉淀手册。

## 1. 目录结构与职责
- `docs/` — 长期核心规范与技术方案（架构设计、排查手册、阶段交接）。汇总看板见 [docs/INDEX.md](docs/INDEX.md)。
- `tasks/` — 复杂专项任务工作区（每个任务为一个独立子目录）。状态监控见 [tasks/STATUS.md](tasks/STATUS.md)，准入总表见 [tasks/REGISTRY.md](tasks/REGISTRY.md)。
- `research/` — 探索性调研、技术选型对比与评测数据。
- `scripts/` — 本地自动化运维工具（索引同步、时效治理等）。
- `TODO.md` — 极轻量待办草稿（纯 markdown checkbox，无需 frontmatter，不进索引）。
- `manifest.jsonl` — 自动生成的全仓结构化索引（每行一个 JSON，供快速检索）。

## 2. 检索方式
- **优先查索引**：检索已有上下文时，优先通过 `manifest.jsonl`（`grep` 或 `jq`）或看板（`docs/INDEX.md`、`tasks/STATUS.md`）定位目标，避免盲目打开大量无关文件。

## 3. 核心准则与操作红线
1. **强制 Frontmatter**：除 `TODO.md` 与 `tasks/*/progress.md` 外，所有 Markdown 文档头部必须包含合法的 YAML Frontmatter（作为唯一事实来源）：
   ```yaml
   ---
   type: architecture | playbook | handoff | investigation | note | report | task
   title: 文档清晰标题
   status: active | draft | in_progress | paused | completed | resolved | archived
   created: YYYY-MM-DD
   updated: YYYY-MM-DD
   summary: 一句话大白话摘要（50字以内）
   resources: []      # 关联代码行或文档锚点，如 code://src/auth.py#L1-L20
   ---
   ```
2. **写后必同步闭环**：在 `.context/` 下新增、修改或删除任何文档后，**必须主动执行** `python3 .context/scripts/sync_bundle.py` 重新编译全局索引与看板。
3. **Task 严格准入**：`tasks/` 下的任务是跨多轮会话的大型专项。**严禁 Agent 未经人类明确批准私自创建 `tasks/<slug>` 目录**。立项须在 `tasks/REGISTRY.md` 登记。
4. **旁路问题留痕**：执行任务时若发现非阻塞性旁路问题，严禁擅自扩大改动范围，统一追加至 `.context/TODO.md`（带 `[task:<slug>]` 或 `[global]` 标签）。
