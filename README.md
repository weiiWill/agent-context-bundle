<div align="center">

# 🧠 Agent Context Bundle

**面向 AI 编程智能体的零外部依赖、自愈型本地知识图谱与上下文工作区底座**

<p align="center">
  <a href="README.md">简体中文</a> •
  <a href="README_EN.md">English</a>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![格式: 纯净 Markdown + YAML](https://img.shields.io/badge/Format-Markdown%20%2B%20YAML-success.svg)](#-核心架构设计)
[![检索延迟: <5ms](https://img.shields.io/badge/Query%20Speed-%3C5ms-orange.svg)](#-token-预算与性能基准)
[![跨智能体支持: Claude Code | Cursor | Antigravity | Codex](https://img.shields.io/badge/Agents-Claude%20Code%20%7C%20Cursor%20%7C%20AGY-purple.svg)](#-多平台自动化与守护矩阵)

<p align="center">
  <a href="#-核心痛点ai-智能体的上下文悖论">核心痛点</a> •
  <a href="#-核心架构设计">核心架构</a> •
  <a href="#-知识流转漏斗四阶段">知识漏斗</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-token-预算与性能基准">Token 预算</a> •
  <a href="#-多平台自动化与守护矩阵">自动化守护</a> •
  <a href="#-设计决策与常见疑问-faq">FAQ</a>
</p>

</div>

---

## ⚡ 核心痛点：AI 智能体的上下文悖论

随着 AI 编程助手从“单轮代码补全”演进为“跨多会话自主执行智能体”（如 Claude Code、Google Antigravity、Cursor、OpenAI Codex），智能体与开发者在工程演进中会高频产生大量极具价值的中间态知识：

- 🏗️ **架构决策与深度排查**：系统设计方案、不变量约束、根因分析报告、性能压测结论。
- 🤝 **跨会话上下文连续性**：在切换模型、重开会话或跨天推进大任务时的状态无缝交接。
- 🔬 **临时验证资产**：一次性排查复现脚本、评测数据集、链路跟踪日志。

### 传统管理方式的三大死穴
| 管理方式 | 致命缺陷 |
|---|---|
| **直接提交进主仓 Git** | 大量充斥未定型的个人草稿与过程噪音，严重污染 Git 提交历史与代码审查（PR）。 |
| **散落在本地无序文件** | 缺乏状态机与时效追踪，文档迅速腐烂失效，智能体在跨会话时面临严重的“上下文失忆”。 |
| **引入外部向量数据库/SaaS** | 强依赖外部后台常驻进程与专属 SDK，存在数据锁定风险，且人类开发者在源码目录内完全不可见。 |

### 我们的解法：`Agent Context Bundle`
一套位于 `.context/` 的标准化本地工作区，由极其轻量的毫秒级编译引擎（`sync_bundle.py`）驱动。它将本地 Markdown 文档重塑为一个**高内聚、可瞬时检索、具备自我治理能力的知识图谱**：
1. **<5ms 极速检索，Token 开销削减 99%**：基于单行 JSONL（`manifest.jsonl`），智能体按需靶向加载，无需全量读取大文件。
2. **生命周期自愈，永不腐烂**：内置时间戳自动续期、>14 天活跃任务停滞预警与 >30 天超期垃圾回收。
3. **垂直强锚定物理代码**：通过 `code://path/to/file.go#L42-L80` 直通源码行，彻底杜绝文档与代码脱节。

---

## 📐 核心架构设计

```text
                        ┌──────────────────────────────────────────┐
                        │    Markdown Frontmatter (YAML)           │
                        │    - 唯一事实来源 (Single Source of Truth)   │
                        │    - resources: code://... 垂直代码锚点   │
                        └────────────────────┬─────────────────────┘
                                             │
                                    sync_bundle.py (<15ms)
                                             │
             ┌───────────────────────────────┴───────────────────────────────┐
             ▼                                                               ▼
┌───────────────────────────────┐                               ┌───────────────────────────────┐
│     manifest.jsonl            │                               │    多维只读汇总看板           │
│  [面向智能体的结构化单行索引]  │                               │    [面向人类开发者的全局大盘] │
│  - 每文档仅占单行 JSON        │                               │  - docs/INDEX.md (分类索引)   │
│  - grep / jq 耗时 <5ms        │                               │  - tasks/STATUS.md (任务告警) │
│  - 单次收敛仅耗费 <300 Token  │                               │  - CLEANUP.md (待归档清单)    │
└───────────────────────────────┘                               └───────────────────────────────┘
```

### 架构设计哲学

1. **零外部依赖（Zero External Dependencies）**：纯文本 Markdown + YAML Frontmatter，无需任何本地数据库、常驻守护进程或特定云服务。
2. **路径即唯一身份（Concept as ID）**：每个文件代表一个知识概念（Concept），去除扩展名的相对路径即为其全局唯一 ID（例如 `docs/architecture-gateway`、`tasks/token-migration`）。
3. **双向知识拓扑网络（Bi-Directional Knowledge Topology）**：
   - **横向图谱（Doc $\leftrightarrow$ Doc）**：文档间通过标准 Markdown 相对链接互联（`[会话缓存设计](architecture-cache.md)`）。
   - **纵向图谱（Doc $\rightarrow$ Code）**：通过 Frontmatter 显式锚定物理代码行（`code://src/auth/jwt.go#L42-L80`）。
4. **以 Frontmatter 为唯一事实来源（SSOT）**：文档自身管理元数据；结构化索引（`manifest.jsonl`）与汇总看板（`INDEX.md`、`STATUS.md`、`CLEANUP.md`）均为纯派生物，15ms 内可随时全量重新编译。
5. **解耦的 Git 双纳管模式（Dual-Mode Git Strategy）**：
   - **团队共享模式（推荐）**：精细化忽略草稿与流水日志，核心架构与索引纳管进 Git 版本库，全团队与 CI 共享。
   - **本地私有沙盒模式**：在 `.gitignore` 中整体忽略 `.context/`，作为个人本地私有辅助底座。

---

## 🗂️ 标准目录骨架

```text
.context/
├── AGENTS.md                         # 本地工作区指引与渐进式检索 SOP (L1/L2/L3)
├── TODO.md                           # 阶段 1：轻量带归属草稿纸 (不进索引，0 Token 损耗)
├── manifest.jsonl                    # [编译产物] 面向智能体的单行 JSON 结构化高速检索索引
├── CLEANUP.md                        # [编译产物] 生命周期治理：超 30 天未更新的归档候选表
├── docs/                             # 阶段 3：长期长效沉淀的核心基线资产
│   ├── INDEX.md                      # [编译看板] 自动按类型分类聚合的知识目录大盘
│   ├── architecture-<slug>.md        # 系统核心架构设计与重大决策 ADR (无日期后缀)
│   ├── playbook-<slug>.md            # 标准排障手册、压测及调试 Runbook (无日期后缀)
│   └── handoff-<slug>-<YYYYMMDD>.md  # 带有日期后缀的阶段交接与快照
├── tasks/                            # 阶段 2：跨多轮会话推进的重量级任务舱
│   ├── REGISTRY.md                   # 任务准入总表 (防膨胀双通道管控)
│   ├── STATUS.md                     # [编译看板] 任务进展、更新天数与停滞告警看板
│   └── <task-slug>/
│       ├── README.md                 # 任务主控枢纽 (Frontmatter 包含状态与代码锚点)
│       ├── progress.md               # 线性推进流水日志 (满 200 行自动切分为归档卷)
│       └── (选填) plans/ docs/       # 任务名下的子方案与专属文档
├── research/                         # 跨任务共享的技术选型、Benchmark 与算法评测
└── scripts/
    ├── sync_bundle.py                # 核心同步引擎：编译索引与渲染看板 (<15ms)
    ├── bump_updated.py               # 时间戳自动续期脚本 (原子级更新 frontmatter updated)
    └── install_git_hook.sh           # Git pre-commit 拦截器安装脚本 (智能识别 gitignore)
```

---

## 🌪️ 知识流转漏斗（四阶段生命周期）

系统通过严格的状态机驱动知识在四个阶段有序演进，彻底解决**“上下文丢失”**与**“无用垃圾膨胀”**的矛盾：

```text
【阶段 1：草稿留存】  .context/TODO.md
          │            - 明确归属前缀：[global] 全局待办 或 [task:<slug>] 旁路待办
          ▼            - 绝对排除在索引外，0 Token 检索干扰。
【阶段 2：任务排查】  .context/tasks/<task-slug>/
          │            - 严格双通道准入 (用户显式指令 或 智能体提议+人工明确批准)
          ▼            - 活跃度时效治理：进行中任务 >14 天未改动亮起 ⚠️ Stagnant 告警。
【阶段 3：长效沉淀】  .context/docs/architecture-*.md / playbook-*.md
          │            - 任务结项时萃取核心不变量；pinned: true 获得免清理特权。
          ▼            - 垂直绑定源码行：resources: code://src/path#L10。
【阶段 4：归档清理】  .context/CLEANUP.md
                       - 已完成/已废弃文档超 30 天未触碰自动进入清理待审池。
                       - 结项闭环核对：结项时主动检索 TODO.md，杜绝孤儿待办。
```

### 1. 阶段 1：轻量草稿留存（`TODO.md`）
- **核心定位**：极轻量随手记。供开发者随时记录零碎想法；供智能体在做主线任务时记录发现的次要旁路问题，**严禁节外生枝扩大改动面**。
- **强制归属标签（Scope Attribution）**：
  ```markdown
  - [ ] [global] Makefile: 补充本地压测 docker-compose 启动命令
  - [ ] [task:auth-refactor] src/auth/jwt.go#L42: 顺手修复 Token 过期未捕获边界异常
  ```
- **豁免索引**：编译脚本完全忽略 `TODO.md`，保证 0 字节进入全局索引。

### 2. 阶段 2：任务专项排查（`tasks/<slug>/`）
- **严格准入双通道机制（Strict Two-Gateway Admission）**：Task 是跨多会话的大型重量级专项，**严禁智能体擅自建目录立项**。仅允许两种合法通路：
  1. *通道 1：用户显式指令*（开发者主动要求立项）；
  2. *通道 2：智能体提议拆分 + 必须人工批准*（智能体发现任务超纲，说明原因提议拆分，经用户明确许可后方可立项）。
- **主控与日志双核分离**：
  - `README.md`：主控枢纽，记录 Frontmatter 元数据、目标、代码锚点与核心决策；
  - `progress.md`：纯线性执行流水。编辑流水时，Hook 自动将打卡时间重定向到 `README.md`。
- **自动分卷归档**：流水日志达到约 20-30 条时，自动切分出 `progress-archive-YYYYMMDD-YYYYMMDD.md`，并在原位置留下总结摘要。

### 3. 阶段 3：长效成果沉淀（`docs/`）
- **基线升格（Baseline Promotion）**：任务结项时，把沉淀的高复用架构设计与排障排查步骤提炼为 `docs/architecture-<slug>.md` 或 `docs/playbook-<slug>.md`。
- **源码强锚定**：
  ```yaml
  ---
  type: architecture
  title: 分布式多级会话缓存架构设计
  status: active
  resources:
    - code://src/cache/redis_cluster.go#L45-L120
  summary: 本地 LRU 与 Redis Cluster 双层分布式会话治理与雪崩防护
  pinned: true
  ---
  ```

### 4. 阶段 4：生命周期治理（`CLEANUP.md`）
- **自动垃圾回收（GC）**：任何处于 `completed`、`resolved` 或 `archived` 状态且**超 30 天未触碰**的文件，自动汇集至 `CLEANUP.md`，提醒开发者归档或移出。
- **结项审计闭环**：智能体在将任务标记为 `completed` 前，强制主动执行 `grep 'task:<slug>' .context/TODO.md`，确保派生遗留待办无一遗漏。

---

## 🚀 快速开始

### 1. 安装方式

#### 推荐：作为 Claude Code / AGY 技能直接安装
克隆至个人的 Agent 技能目录：
```bash
git clone https://github.com/weiiWill/agent-context-bundle.git ~/.claude/skills/agent-context-bundle
```

#### 本地开发调试软链接
```bash
ln -s /path/to/agent-context-bundle ~/.claude/skills/agent-context-bundle
```

### 2. 在工程中初始化
在你的项目目录中直接唤起智能体：
> *“请在本工程中初始化 Agent Context Bundle 工作区。”*

编排的隔离子智能体（Sub-agent）将自动：
1. 脚手架生成 `.context/{docs,research,tasks,scripts}` 目录及规范模板；
2. 引导配置 Git 策略：
   - **团队共享模式（默认）**：配置精细化 `.gitignore`，忽略流水日志，将核心架构与索引提交入库；
   - **本地私有模式**：在 `.gitignore` 追加 `.context/` 整体忽略；
3. 安装平台对应的自动化 Hook，并毫秒级编译初始的 `manifest.jsonl` 与看板。

---

## ⚡ 多平台自动化与守护矩阵

实现全流程“零心智负担”。只要保存或编辑文件，Hook 即可在 15 毫秒内完成静默续期与全量看板重编译：

```text
编辑 .context/ 下文档 ──► 触发 PostToolUse Hook ──► bump_updated.py ──► sync_bundle.py ──► 刷新索引与看板
```

### 1. Claude Code 原生配置（`.claude/settings.local.json`）
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
          "statusMessage": "🔄 同步 .context/ 上下文包"
        }]
      },
      {
        "matcher": "Edit",
        "hooks": [{
          "type": "command",
          "if": "Edit(.context/**)",
          "command": "jq -r '.tool_input.file_path // .tool_response.filePath // empty' | { read -r f; [ -n \"$f\" ] && python3 .context/scripts/bump_updated.py \"$f\"; python3 .context/scripts/sync_bundle.py; } 2>/dev/null || true",
          "statusMessage": "🔄 同步 .context/ 上下文包"
        }]
      }
    ]
  }
}
```

### 2. Google Antigravity 原生配置（`.agents/hooks.json`）
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

### 3. Git Pre-commit 兜底拦截器（`install_git_hook.sh`）
- 执行 `bash .context/scripts/install_git_hook.sh` 安装本地提交拦截；
- **智能 Gitignore 感知**：若检测到工程已在 `.gitignore` 中整体忽略 `.context/`，脚本将自动识别并友好退出；若属于团队共享纳管，则在提交时强制执行编译并追加 `git add`，彻底防止脱钩。

### 4. VSCode / Cursor 智能补全与校验
在项目的 `.vscode/settings.json` 中配置内置的 JSON Schema：
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

## 📊 Token 预算与性能基准

### Token 消耗实测对比
以包含 30 篇架构规范、5 个活跃专项任务、10 篇调研评测的中大型工程为例：

| 检索获取方式 | 扫描数据量 | 消耗 Token 上下文 | 单次检索耗时 |
|---|---|---|---|
| **暴力读取原始 Markdown 正文** | 45 个大文件 (~5 KB/篇) | ~75,000 Tokens | ~1,200 ms |
| **全量读取看板大盘文件** | 3 个看板 Markdown | ~4,500 Tokens | ~150 ms |
| **单行 `manifest.jsonl`（靶向过滤）** | 3-5 行单行 JSON | **< 300 Tokens（省 99%）** | **< 5 ms** |

### 核心引擎执行基准
- **全量扫描与编译速度**：在普通开发机上扫描 100 篇文档耗时 **< 15ms**；
- **内存占用**：Python 执行期常驻内存 **< 12MB**；
- **非阻塞容灾设计（Fail-Open）**：即使遇到非致命语法解析异常，脚本恒返回 0，绝不中断智能体正常工作。

---

## ❓ 设计决策与常见疑问 (FAQ)

<details>
<summary><b>为什么不直接使用 SQLite 或本地向量数据库 (Vector DB)？</b></summary>
<br>
向量数据库和嵌入式 SQL 会带来二进制文件冲突、外部守护进程依赖、Schema 升级迁移成本以及对人类开发者的不可见性。纯文本 Markdown + 单行 JSONL 具备真正的零外部依赖、完美适配 Git Diff 审查，并能借助系统自带的极速原生命令（<code>grep</code>、<code>jq</code>）实现毫秒级流式过滤。
</details>

<details>
<summary><b>为什么采用单行 JSONL 而不是常规格式化 JSON 数组？</b></summary>
<br>
采用 JSON 数组（<code>[...]</code>）时，任何工具都必须将整个几万字符的 JSON 解析载入内存才能读取其中一个字段。而基于 <code>manifest.jsonl</code>，智能体可以在 Shell 中直接通过流式管道精准筛选单行，完全无需把整个索引全量倾倒入上下文大模型中：
<pre><code>grep '"type": "architecture"' .context/manifest.jsonl | jq -r '.id'</code></pre>
</details>

<details>
<summary><b>如何彻底避免任务目录通胀和陈旧僵尸文档？</b></summary>
<br>
新建 Task 受到严格的双通道准入机制管控（非用户下达指令或人工明确许可不可建目录）。同时，<code>sync_bundle.py</code> 会自动对 >14 天未触碰的任务打上 <code>⚠️ Stagnant (>14d)</code> 醒目标签，并对 >30 天已结项的任务拉入 <code>CLEANUP.md</code> 清理待审池。
</details>

---

## 📄 开源许可证

本项目基于 [MIT 许可证](LICENSE) 开源。Copyright © 2026 WeiiWill.
