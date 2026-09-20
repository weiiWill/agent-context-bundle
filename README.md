# Agent Context Bundle

> A lightweight, zero-dependency local context workspace & knowledge graph specification for AI coding agents (Claude Code, Cursor, Antigravity, Codex, etc.).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Format: Pure Markdown + YAML](https://img.shields.io/badge/Format-Markdown%20%2B%20YAML-green.svg)](#)

---

## 🌟 Why Agent Context Bundle? / 为什么需要它？

During AI-assisted software development, agents and developers generate massive amounts of high-value ephemeral knowledge:
- 🏗️ **Architecture & Investigation Notes**: Deep dive analysis, root cause analyses, system invariants.
- 🤝 **Cross-Session Handoffs**: Context preservation when switching between prompts or sessions.
- 🔬 **One-off Verification Scripts & Benchmark Artifacts**: Disposable evaluation code and raw traces.

**The Dilemma**:
- Storing them in the main Git repository pollutes commit history and main branches.
- Storing them untracked without structure leads to lost context and "context drift".

**The Solution**:
`Agent Context Bundle` establishes a structured, Git-isolated `.context/` workspace that turns local project knowledge into a machine-parseable, self-governing **Knowledge Graph**.

---

## 📐 Core Architecture / 核心设计

```
                      +------------------------------------------+
                      |          YAML Frontmatter                |
                      |   (Machine Truth Layer / 机器真相层)      |
                      +------------------------------------------+
                                           |
                                  sync_bundle.py (Engine)
                                           |
            +------------------------------+------------------------------+
            |                                                             |
            v                                                             v
+------------------------+                                   +------------------------+
|    manifest.jsonl      |                                   |  docs/INDEX.md         |
|  (Agent Fast Triage)   |                                   |  tasks/STATUS.md       |
|  grep / jq in <5ms     |                                   |  (Human-Readable Board)|
+------------------------+                                   +------------------------+
```

1. **Zero Lock-in（零外部依赖）**: Pure Markdown + YAML Frontmatter. No database, server, or custom SDK required.
2. **Concept as ID（路径即唯一身份）**: Every document is a Concept; its relative path without extension is its unique ID (e.g., `docs/architecture-pipeline`).
3. **Graph via Markdown Links（图谱化关联）**:
   - **Horizontal (Doc $\leftrightarrow$ Doc)**: Standard relative Markdown links `[title](../path/to/doc.md)`.
   - **Vertical (Doc $\rightarrow$ Code)**: Explicit `resources` URI anchoring (e.g., `code://src/service/processor.py#L45`).
4. **Dual-Layer Indexing（双层架构）**: Machine truth is in frontmatters and aggregated into `manifest.jsonl`. Human-readable boards (`INDEX.md`, `STATUS.md`, `CLEANUP.md`) are automatically rendered by scripts.
5. **Lifecycle Governance（时效治理）**:
   - ⚠️ **Stagnant Tasks**: Flagged if active/in-progress with no updates for >14 days.
   - 🗑️ **Cleanup Candidates**: Listed if completed/archived with no touches for >30 days (unless `pinned: true`).

---

## 📂 Standard Layout / 标准目录骨架

```text
.context/                             # Git-ignored by default
├── AGENTS.md                         # Local workspace guidance for agents
├── manifest.jsonl                    # [Machine Index] Single-line JSON per concept
├── CLEANUP.md                        # [Lifecycle] Cleanup candidates (>30d inactive)
├── TODO.md                           # Lightweight scratchpad (pure markdown checkboxes)
├── docs/                             # Evergreen knowledge
│   ├── INDEX.md                      # [Presentation Layer] Auto-rendered catalog
│   └── <type>-<slug>[-YYYYMMDD].md   # Standalone documents with Frontmatter
├── tasks/                            # Multi-session complex tasks
│   ├── REGISTRY.md                   # Task admission log
│   ├── STATUS.md                     # [Presentation Layer] Task status board
│   └── <task-slug>/
│       ├── README.md                 # Task controller (Frontmatter with status)
│       ├── progress.md               # Append-only chronological execution log
│       └── (optional) inputs/ outputs/ scripts/ plans/ docs/
├── research/                         # Cross-task deep research & evaluation data
└── scripts/
    ├── sync_bundle.py                # Dual-layer index compiler & schema validator
    └── bump_updated.py               # Atomically updates 'updated:' date in frontmatter
```

---

## 🏷️ Standard Frontmatter Schema / 规范元数据

Every managed document starts with a YAML frontmatter block:

```yaml
---
type: architecture | playbook | handoff | investigation | reading-map | report | llm-io | note | task | draft
title: Descriptive Title
status: active | draft | in_progress | paused | completed | resolved | archived
resources:
  - code://src/service/processor.py#L45-L120
  - doc://.context/docs/architecture-pipeline.md
tags: [data-pipeline, streaming, cache]
created: 2026-09-07
updated: 2026-09-20
summary: One-sentence summary explaining the problem solved or core conclusion (<=50 words)
pinned: false
---
```

---

## 🤖 Isolated Sub-agent Workflows / 子 Agent 隔离工作流编排

To keep the primary agent's context window clean and focused on feature development, initialization and maintenance are executed via an **isolated Sub-agent**:

```python
invoke_subagent(
    Role="Context Bundle Engineer",
    TypeName="self",
    Prompt="""Execute Workflow A (init) or Workflow B (maintain)..."""
)
```

### 1. `init` Workflow (New Project Scaffolding)
- Scans target project for `.gitignore` and `AGENTS.md`.
- Generates `.context/{docs,research,tasks,scripts}` skeleton.
- Seeds `sync_bundle.py` and `bump_updated.py`.
- Injects workspace instructions (`.context/AGENTS.md`, `TODO.md`, `REGISTRY.md`).
- Appends `.context/` to `.gitignore` and links into root `AGENTS.md`.
- Compiles initial `manifest.jsonl` and returns health status.

### 2. `maintain` Workflow (Routine Audit & Self-healing)
- **Frontmatter Validation**: Ensures mandatory fields (`type`, `status`, `updated`, `summary`) and validates standard English status enums.
- **Link Topology Audit**: Scans for broken 404 Markdown relative links and verifies `code://` / `doc://` anchors.
- **Index Synchronization**: Runs `sync_bundle.py` to refresh `manifest.jsonl`, `INDEX.md`, `STATUS.md`, and `CLEANUP.md`.
- **Stagnancy Governance**: Flags stagnant tasks (>14 days) and prompts cleanup candidates (>30 days).

---

## 🚀 Installation & Usage / 安装与使用

### Option 1: Install as a Claude Code / AGY Skill (Recommended)

Clone directly into your personal agent skills directory:

```bash
git clone https://github.com/<your-username>/agent-context-bundle.git ~/.claude/skills/agent-context-bundle
```

Once installed, your Agent will automatically discover the skill and can be prompted:
- *"Initialize a .context workspace in this project."*
- *"Audit and sync the .context bundle."*

### Option 2: Local Development Symlink
If you are iterating on the skill itself:

```bash
ln -s /path/to/agent-context-bundle ~/.claude/skills/agent-context-bundle
```

---

## ⚡ Multi-Platform Automation & Hook Matrix / 多平台自动化与守护矩阵

To ensure zero cognitive burden and eliminate manual index updates, `agent-context-bundle` supports seamless code-level lifecycle hooks across major Agent environments:

### 1. Claude Code (`.claude/settings.local.json`)
Auto-bumps `updated:` dates and re-renders the manifest whenever files in `.context/**` are written or edited:
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
          "statusMessage": "🔄 Syncing .context/ bundle"
        }]
      },
      {
        "matcher": "Edit",
        "hooks": [{
          "type": "command",
          "if": "Edit(.context/**)",
          "command": "jq -r '.tool_input.file_path // .tool_response.filePath // empty' | { read -r f; [ -n \"$f\" ] && python3 .context/scripts/bump_updated.py \"$f\"; python3 .context/scripts/sync_bundle.py; } 2>/dev/null || true",
          "statusMessage": "🔄 Syncing .context/ bundle"
        }]
      }
    ]
  }
}
```

### 2. Google Antigravity (`.agents/hooks.json`)
Native AGY lifecycle integration with 5s timeout and fail-open resilience:
```json
{
  "context-bundle-sync": {
    "PostToolUse": [
      {
        "matcher": "write_to_file",
        "hooks": [{ "type": "command", "command": "python3 .context/scripts/sync_bundle.py 2>/dev/null || true" }]
      },
      {
        "matcher": "replace_file_content",
        "hooks": [{ "type": "command", "command": "python3 .context/scripts/sync_bundle.py 2>/dev/null || true" }]
      }
    ]
  }
}
```

### 3. Universal Git Pre-commit Hook
Run `.context/scripts/install_git_hook.sh` to install a local pre-commit guard that automatically syncs and stages updated indexes whenever `.context/` files are committed.

### 4. JSON Schema & VSCode Validation
A formal JSON Schema is provided at `reference/schema/context-frontmatter.schema.json`. Bind it in `.vscode/settings.json` for IDE autocompletion and frontmatter linting:
```json
{
  "yaml.schemas": {
    "./.context/schema/context-frontmatter.schema.json": [
      ".context/docs/**/*.md",
      ".context/tasks/*/README.md"
    ]
  }
}
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
