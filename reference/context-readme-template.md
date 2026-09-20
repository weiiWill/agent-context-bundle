# Agent Context Bundle (.context/) Workspace Guide

`.context/` 是面向人类开发者与 AI Agent 的本地工作区与知识图谱底座。统一存放项目开发过程中的架构分析、问题排查、跨会话交接（Handoff）、一次性验证脚本、评测数据与沉淀的执行手册（Playbooks）。整体通过 `.gitignore` 排除，不污染 Git 主分支代码与提交历史。

---

## 1. Layout 目录布局

- `docs/` — 常青知识文档（架构设计、Playbook、排查总结、交接记录）。
- `research/` — 跨任务共享的研究与专项评测数据。
- `tasks/<slug>/` — 准入的任务单元。参见 [tasks/STATUS.md](tasks/STATUS.md)（状态看板）与 [tasks/REGISTRY.md](tasks/REGISTRY.md)（任务准入表）。
- `scripts/` — 核心自动化引擎（`sync_bundle.py`、`bump_updated.py`）。
- `manifest.jsonl` — [全局结构化索引] 单行 JSON 索引，供 Agent 秒级直接检索。
- `CLEANUP.md` — [生命周期] 自动生成的待清理/待归档候选清单。
- `TODO.md` — 极轻量待办草稿（纯 markdown checkbox，无需 frontmatter，不进索引）。

---

## 2. Agent 标准操作规范 (Agent Operating SOP)

任何接入本工程的 AI Agent（Claude Code、Antigravity、Cursor、Codex 等）必须遵循以下标准作业程序：

### 2.1 高速检索路径 (Fast Retrieval SOP)
- **L1 优选（极速收敛，5ms / 200 Token）**：
  检索相关知识或任务时，**禁止盲目打开多个大 Markdown 文件**，优先用 `grep` 或 `jq` 检索 `manifest.jsonl`：
  ```bash
  # 查找活跃的交接文档或架构设计
  jq -r 'select(.status=="active" and (.type=="architecture" or .type=="handoff")) | "\(.path): \(.summary)"' .context/manifest.jsonl
  # 查找包含特定标签的资产
  grep '"tags":.*data-pipeline' .context/manifest.jsonl
  ```
- **L2 降级（汇总看板兜底）**：
  若当前环境缺失 `jq` 或 Python 运行受阻，降级阅读自动编译生成的汇总看板：
  - 查阅文档分类：阅读 `.context/docs/INDEX.md`；
  - 查阅任务进展与活跃度：阅读 `.context/tasks/STATUS.md`。
- **L3 极限兜底（文件系统直查）**：
  若看板尚未生成或损坏，直接使用目录查找：
  - 架构与排查：`ls .context/docs/`；
  - 任务主控：`ls .context/tasks/*/README.md`。

### 2.2 安全写入与更新规范 (Safe Modification SOP)
- **Frontmatter 强制要求**：新建或编辑文档时，头部必须包含合法的 YAML Frontmatter（`type`、`title`、`status`、`summary` 为必填项，作为唯一事实来源）。
- **严格英文状态枚举**：统一严格使用：`active` | `draft` | `in_progress` | `paused` | `completed` | `resolved` | `archived`。
- **自动生成的看板与索引禁止手改**：`docs/INDEX.md`、`tasks/STATUS.md`、`CLEANUP.md` 与 `manifest.jsonl` 由同步脚本自动编译，**严禁手动编辑**。
- **修改时效维护**：编辑文档后，将 `updated:` 更新为当天（`YYYY-MM-DD`）；若配置了 Hook 守护，该动作由 Hook 自动且幂等完成。

### 2.3 异常恢复与降级机制 (Graceful Fallback & Recovery)
- **索引损坏一键重构**：若 `manifest.jsonl` 发生冲突或格式损坏，运行 `python3 .context/scripts/sync_bundle.py` 即可在毫秒内根据各文档 Frontmatter 从头重新生成全部索引与看板。
- **缺失 Python 运行环境时**：只需手工维持 Frontmatter 语法合规，后续在宿主环境运行一次 `sync_bundle.py` 即可完成编译。

---

## 3. 自动化守护矩阵 (Hooks & Enforcement)

为了确保“文件修改后索引永不漂移、日期自动续期”，建议在项目中启用代码层 Hook。

### 3.1 Claude Code 环境 (`.claude/settings.local.json`)
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [{
          "type": "command",
          "if": "Write(.context/**)",
          "command": "jq -r '.tool_input.file_path // .tool_response.filePath // empty' | { read -r f; [ -n \"$f\" ] && python3 .context/scripts/bump_updated.py \"$f\"; python3 .context/scripts/sync_bundle.py; } 2>/dev/null || true",
          "statusMessage": "🔄 同步 .context 索引"
        }]
      },
      {
        "matcher": "Edit",
        "hooks": [{
          "type": "command",
          "if": "Edit(.context/**)",
          "command": "jq -r '.tool_input.file_path // .tool_response.filePath // empty' | { read -r f; [ -n \"$f\" ] && python3 .context/scripts/bump_updated.py \"$f\"; python3 .context/scripts/sync_bundle.py; } 2>/dev/null || true",
          "statusMessage": "🔄 同步 .context 索引"
        }]
      }
    ]
  }
}
```

### 3.2 Google Antigravity 环境 (`.agents/hooks.json`)
```json
{
  "context-bundle-sync": {
    "PostToolUse": [
      {
        "matcher": "write_to_file",
        "hooks": [{
          "type": "command",
          "command": "python3 .context/scripts/sync_bundle.py 2>/dev/null || true"
        }]
      },
      {
        "matcher": "replace_file_content",
        "hooks": [{
          "type": "command",
          "command": "python3 .context/scripts/sync_bundle.py 2>/dev/null || true"
        }]
      }
    ]
  }
}
```

### 3.3 Git Pre-commit 兜底
执行 `.context/scripts/install_git_hook.sh` 安装本地提交拦截器，在执行 `git commit` 时若暂存了 `.context/` 改动，自动编译刷新索引。

---

## 4. 知识流转漏斗 (Knowledge Funnel)

- **草稿层**：`TODO.md` 用于天级零碎记录。
- **任务推进**：复杂事项在 `tasks/REGISTRY.md` 登记后，创建 `tasks/<slug>/README.md` 与 `progress.md` 线性推进。
- **常青沉淀**：任务完成后，有价值的架构与方法论提炼移入 `docs/`（如 `docs/architecture-*.md` 或 `docs/playbook-*.md`）。
- **生命周期归档**：历史任务与快照标记为 `status: archived`，逾期 30 天自动汇总至 `CLEANUP.md`。
