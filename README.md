<div align="center">

# 🧠 Agent Context Bundle

**给 AI 编程助手（Claude Code / Cursor 等）的本地项目记忆库**  
*不污染 Git • 省 99% Token • 跨会话任务与架构经验永不丢失 • 免配数据库*

<p align="center">
  <a href="README.md">简体中文</a> •
  <a href="README_EN.md">English</a>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![格式: 纯 Markdown + YAML](https://img.shields.io/badge/Format-Markdown%20%2B%20YAML-success.svg)](#-核心架构设计)
[![检索延迟: <5ms](https://img.shields.io/badge/Query%20Speed-%3C5ms-orange.svg)](#-token-预算与性能实测)
[![支持智能体: Claude Code | Cursor | Antigravity | Codex](https://img.shields.io/badge/Agents-Claude%20Code%20%7C%20Cursor%20%7C%20AGY-purple.svg)](#-全自动守护不再手动维护)

<p align="center">
  <a href="#-为什么需要它解决-ai-编程的三大痛点">为什么需要它</a> •
  <a href="#-核心架构设计">核心架构</a> •
  <a href="#-知识流转从随手记到长期规范的-4-步">4 步流转</a> •
  <a href="#-快速开始">快速开始</a> •
  <a href="#-token-预算与性能实测">性能表现</a> •
  <a href="#-全自动守护不再手动维护">自动守护</a> •
  <a href="#-常见疑问-faq">FAQ</a>
</p>

</div>

---

## ⚡ 为什么需要它？解决 AI 编程的三大痛点

在用 Claude Code、Cursor、Google Antigravity 等 AI 编程智能体做复杂项目时，我们经常遇到一个死结：**AI 总是“做完就忘”，换个会话就失忆，而想让它记住又极耗 Token。**

开发过程中产生的大量高价值内容（系统架构设计、复杂 Bug 排查记录、跨会话交接、临时验证脚本），目前往往无处安放：

| 传统做法 | 为什么不可行？ |
|---|---|
| **直接提进 Git 仓库** | 充斥大量个人草稿和临时排查日志，严重污染主分支代码与提交历史。 |
| **随便建本地文档** | 缺乏统一规范与更新机制，文档写完就落灰腐烂；新建会话后 AI 根本找不到。 |
| **外挂向量数据库 / SaaS 工具** | 必须安装后台常驻服务或买商业产品，过度复杂，且人类开发者在代码目录里看不到。 |

### 我们的解法：为 AI 打造标准化的本地记忆工作区
只需在项目根目录建一个 `.context/` 目录，搭配轻量脚本 `sync_bundle.py`，就能获得：
1. **跨会话不失忆**：任务进度、核心架构、排障经验结构化留存，新建会话秒级唤醒；
2. **极速检索，节省 99% Token**：AI 通过单行索引（`manifest.jsonl`）靶向检索，**单次定位仅耗费不到 300 Token，延迟 <5ms**，不再把几万字文档全丢进上下文；
3. **直连业务代码**：文档内直接标记 `code://src/service.go#L42-L80`，AI 一键直达代码实现；
4. **完全自动化，文档永不落灰**：保存文件自动打卡更新日期，长期不动自动提醒清理，零维护心智负担。

---

## 📐 核心架构设计

整个记忆库采用**“唯一事实源 + 毫秒级自动生成视图”**的设计模式：

```text
Markdown 文档 (YAML Frontmatter) ─── [唯一事实源 SSOT]
  ├── 元数据字段: id, type, status, tags, summary
  └── 垂直直达源码: resources: code://src/auth.go#L42
       │
       ▼
sync_bundle.py 编译引擎 (<15ms)
       │
       ├──► manifest.jsonl ──────────► 面向 AI：单行流式索引 (grep/jq <5ms, 省 99% Token)
       │
       └──► 自动生成的多维看板 ──────► 面向人类：实时全局大盘
             ├── docs/INDEX.md         - 按类型分类的知识大盘
             ├── tasks/STATUS.md       - 任务进展与停滞预警看板 (>14d ⚠️)
             └── CLEANUP.md            - 超期任务垃圾回收审理池 (>30d)
```

| 架构层级 | 文件载体 | 核心角色 | 关键机制 |
|---|---|---|---|
| **唯一事实源 (SSOT)** | `.context/**/*.md` | 知识与状态定义 | 文档头部 YAML 元数据，垂直绑定源码物理行号 (`code://...#L10`) |
| **极速编译引擎** | `.context/scripts/sync_bundle.py` | 状态同步与索引构建 | <15ms 全量扫描，校验图谱断链与 Schema，零外部依赖 |
| **机器索引层 (AI)** | `.context/manifest.jsonl` | AI 极速按需检索 | 每篇文档仅占一行 JSON，支持 Unix 管道秒级过滤，节省 99% 上下文 |
| **人类视图层 (Human)** | `INDEX.md` / `STATUS.md` / `CLEANUP.md` | 开发者只读大盘 | 100% 自动派生生成，直观展示分类目录、任务活跃度与超期待归档池 |

### 核心设计原则

1. **零外部依赖**：纯原生 Markdown + YAML Frontmatter，无需配置任何数据库、常驻守护进程或外部网络环境。
2. **文件路径即唯一 ID**：每个文档去后缀后的路径就是唯一标识（如 `docs/architecture-gateway`、`tasks/token-migration`）。
3. **文档与代码双向互联**：
   - **文档连文档**：标准 Markdown 相对链接（`[会话缓存设计](architecture-cache.md)`）；
   - **文档连代码**：在文档头直接指定物理代码行（`code://src/auth/jwt.go#L42-L80`）。
4. **灵活的 Git 纳管模式**：
   - **团队共享模式（推荐）**：精细化忽略临时流水，将核心架构、排障手册与索引提交至 Git，全团队与 CI 共享；
   - **本地私有沙盒模式**：在 `.gitignore` 中整体忽略 `.context/`，完全作为个人本地辅助，不向代码库提交一行额外内容。

---

## 🗂️ 标准目录结构

```text
.context/
├── AGENTS.md                         # 规范手册：教 AI 如何高效查阅本工作区与三级降级路径
├── TODO.md                           # 步骤 1：轻量随手草稿纸 (带归属前缀，0 Token 损耗)
├── manifest.jsonl                    # [自动编译] 面向 AI 的单行 JSON 索引，供快速检索
├── CLEANUP.md                        # [自动编译] 任务超时与待归档清单
├── docs/                             # 步骤 3：长期沉淀的核心规范与经验
│   ├── AGENTS.md                     # [层级规约] 强制 Frontmatter 与命名范式，严禁裸写
│   ├── INDEX.md                      # [自动编译] 自动按类型分类聚合的知识目录
│   ├── architecture-<slug>.md        # 核心架构设计与重大决策 ADR (不带日期后缀)
│   ├── playbook-<slug>.md            # 踩坑总结、排障手册与验证流程 (不带日期后缀)
│   └── handoff-<slug>-<YYYYMMDD>.md  # 阶段交接与工作快照 (带日期后缀)
├── tasks/                            # 步骤 2：跨多轮会话推进的复杂任务
│   ├── AGENTS.md                     # [层级规约] 严格立项准入双通道与 200 行分卷流水
│   ├── REGISTRY.md                   # 任务准入表 (防任务无限膨胀)
│   ├── STATUS.md                     # [自动编译] 任务状态与逾期告警大盘
│   └── <task-slug>/
│       ├── README.md                 # 任务主控 (记录目标、状态与关键决策)
│       ├── progress.md               # 线性推进流水 (超 200 行自动切卷归档)
│       └── (选填) plans/ docs/       # 任务名下的子方案
├── research/                         # 跨任务的技术调研、压测评测与选型分析
│   └── AGENTS.md                     # [层级规约] 零污染代码库、结论先行与流转退出
└── scripts/
    ├── AGENTS.md                     # [层级规约] 脚本工具职责与安全变更红线
    ├── sync_bundle.py                # 核心同步引擎：扫描全仓并编译索引 (<15ms)
    ├── install_hooks.py              # 框架自感知引擎：自动探查并向 Antigravity / Claude 注入 Hook
    ├── bump_updated.py               # 时间戳自动续期脚本 (修改文件时自动打卡)
    └── install_git_hook.sh           # Git pre-commit 提交拦截器 (智能识别 gitignore)
```

---

## 🌪️ 知识流转：从随手记到长期规范的 4 步

系统提供了一套像流水线一样清晰的状态机，杜绝“知识写完就丢”或“垃圾任务膨胀”：

```text
[第 1 步：临时随手记]      .context/TODO.md
                     轻量草稿纸 • 标记 [global] 或 [task:<slug>] • 0 索引干扰，0 Token 损耗
                           │
                           ▼ (严格准入：用户下达指令 或 AI 提议并获人工批准)
[第 2 步：多会话任务推进]  .context/tasks/<task-slug>/
                     复杂长线任务 • 主控与流水分离 • 超 14 天未改动亮起 ⚠️ Stagnant 预警
                           │
                           ▼ (任务结项：萃取高价值架构与实操手册)
[3. 沉淀为长期规范]        .context/docs/architecture-*.md / playbook-*.md
                     项目长期基线 • 垂直直达源码 code://... • 标记 pinned: true 永久保护
                           │
                           ▼ (自然超期：已结项且超 30 天未触碰)
[4. 定期归档与清理]        .context/CLEANUP.md
                     超期待归档池 • 结项前主动执行闭环审计，杜绝孤儿待办
```

### 1. 第 1 步：临时随手记（`TODO.md`）
- **定位**：轻量草稿纸。开发者随手记灵感；AI 在做主线任务时如果发现了不相关的旁路小 Bug，**严禁节外生枝扩大改动面**，统一记到这里。
- **强制归属标签**：
  ```markdown
  - [ ] [global] Makefile: 补充本地压测 docker-compose 启动命令
  - [ ] [task:auth-refactor] src/auth/jwt.go#L42: 顺手修复 Token 过期未捕获边界异常
  ```

### 2. 第 2 步：多会话任务执行（`tasks/<slug>/`）
- **严格准入双通道（防任务膨胀）**：AI **绝不能自作主张新建任务目录**。仅支持两条通路：
  1. *通道 1：用户显式下达立项指令*；
  2. *通道 2：AI 提议拆分并由人工明确批准*（AI 发现任务过大，说明原因提议拆分，经确认后方可建目录）。
- **主控与流水日志分离**：
  - `README.md`：核心大纲与状态（包含 Frontmatter 元数据）；
  - `progress.md`：流水账。修改它时，后台 Hook 会自动把修改时间算到 `README.md` 头上；
- **流水日志超长自动分卷**：当推进日志达到约 200 行时，自动切分出 `progress-archive-*.md`，当前文件保留精炼摘要。

### 3. 第 3 步：沉淀为核心规范与手册（`docs/`）
- **经验升格**：任务完成结项时，把沉淀下来的设计与排障套路提炼为 `docs/` 下的规范。
- **垂直直连业务代码**：
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

### 4. 第 4 步：定期归档与清理（`CLEANUP.md`）
- **自动垃圾回收提示**：已完成且**超过 30 天未触碰**的文件，自动列入 `CLEANUP.md` 提醒整理或移出。
- **结项检查闭环**：任务结项前，AI 会主动运行 `grep 'task:<slug>' .context/TODO.md`，杜绝遗留孤儿待办。

---

## 🚀 快速开始

### 1. 安装方式

#### 推荐：作为 Claude Code / AGY 技能直接安装
```bash
git clone https://github.com/weiiWill/agent-context-bundle.git ~/.claude/skills/agent-context-bundle
```

#### 本地开发调试软链接
```bash
ln -s /path/to/agent-context-bundle ~/.claude/skills/agent-context-bundle
```

### 2. 在项目中初始化
在项目终端中对 AI 说：
> *“请在本工程中初始化 Agent Context Bundle 工作区。”*

AI 将自动通过独立的 Sub-agent 执行：
1. 一键生成 `.context/` 骨架与标准模板；
2. 引导确认 Git 策略（团队共享纳管 或 本地私有隔离）；
3. 安装平台对应的保存自动同步 Hook，并秒级编译出初始索引与看板。

### 3. 日常核心使用指令（人机协作实战场景）

初始化完成后，日常开发中完全不需要记忆复杂的命令，用日常自然语言即可调度完整机制：

#### 场景 A：发起与推进长线任务（Task Admission & Progress）
- **发起立项（人工驱动防通胀）**：
  > 🗣️ *“我们要改造用户鉴权模块，为它立项一个任务：auth-refactor。”*  
  > 🤖 **AI 行为**：在 `tasks/auth-refactor/` 下建立主控 `README.md` 与流水 `progress.md`，并在 `tasks/REGISTRY.md` 登记。
- **记录进展**：
  > 🗣️ *“记录今天在 auth-refactor 的进展：已完成 JWT 颁发重构，但发现与网关中间件有偶发超时。”*  
  > 🤖 **AI 行为**：追加流水至 `progress.md`，底层 Hook 自动打卡更新 `README.md` 的修改时间。

#### 场景 B：任务完工结项与经验沉淀（Task Conclusion & Distillation）
- **触发结项**：
  > 🗣️ *“auth-refactor 任务已完成，准备结项。”*  
  > 🤖 **AI 行为**：
  > 1. 自动执行 `grep` 扫描 `TODO.md`，确认是否有遗留的 `[task:auth-refactor]` 未竟事项；
  > 2. **主动向你提议经验萃取**：“*本任务已完成。我梳理了本次改造的核心经验《分布式鉴权架构方案》，是否批准沉淀至 docs/architecture-auth.md？*”；
  > 3. 你回复 *“批准”* 后，AI 一键生成文档、绑定 `resources: code://src/auth/jwt.go#L42` 源码锚点，并将任务置为 `completed`。

#### 场景 C：随手提炼排障手册或架构规范（Knowledge Distillation）
- **显式提炼排障经验**：
  > 🗣️ *“把刚才排查 Redis 连接池偶发泄漏的根因与排障步骤沉淀一份 playbook。”*  
  > 🤖 **AI 行为**：基于标准模板提取本次会话的排查全过程，写入 `docs/playbook-redis-leak.md` 并绑定泄漏代码行，15ms 内自动收录进索引看板。
- **显式沉淀架构设计**：
  > 🗣️ *“把刚才讨论的多级缓存方案沉淀为 architecture 规范，标记为 pinned 永久保护。”*

#### 场景 D：临时待办与旁路问题留痕（Zero-friction Scratchpad）
- **记录不影响主线的待办**：
  > 🗣️ *“记一个待办：后续需要给 Makefile 增加压测目标。”*  
  > 🤖 **AI 行为**：向 `TODO.md` 追加 `- [ ] [global] Makefile: 增加压测目标`。0 字节污染索引。

#### 场景 E：定期体检与知识库自愈（Health Audit & Sync）
- **一键巡检**：
  > 🗣️ *“巡检并同步一下 .context 知识库。”*  
  > 🤖 **AI 行为**：全量检查 Frontmatter 格式合规性、修复 404 断链、刷新所有汇总大盘，并汇报 >14 天停滞任务与 >30 天待归档项。

---

## ⚡ 全自动守护：不再手动维护

保存文件后，Hook 会在 15 毫秒内自动打卡续期并重编索引，彻底解放双手：

```text
编辑保存文档 ──► 触发 Hook ──► 自动更新修改日期 ──► 重新编译索引与看板 (<15ms)
```

> 💡 **全自动一键识别注入**：项目初始化或维护时，只需运行 `python3 .context/scripts/install_hooks.py`，即可自动探测当前宿主框架（Antigravity、Claude Code、Git）并实体化注入原生生命周期 Hook！也可以参考下方手动配置：

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
          "statusMessage": "🔄 同步 .context/ 记忆库"
        }]
      },
      {
        "matcher": "Edit",
        "hooks": [{
          "type": "command",
          "if": "Edit(.context/**)",
          "command": "jq -r '.tool_input.file_path // .tool_response.filePath // empty' | { read -r f; [ -n \"$f\" ] && python3 .context/scripts/bump_updated.py \"$f\"; python3 .context/scripts/sync_bundle.py; } 2>/dev/null || true",
          "statusMessage": "🔄 同步 .context/ 记忆库"
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

### 3. Git Pre-commit 拦截器（`install_git_hook.sh`）
- 运行 `bash .context/scripts/install_git_hook.sh` 安装；
- **智能 Gitignore 识别**：若工程已在 `.gitignore` 中整体排除了 `.context/`，脚本会自动检测并跳过拦截；若属于团队共享模式，则在提交时强制重编译索引并自动暂存，杜绝脏索引入库。

### 4. VSCode / Cursor 编辑自动补全
在 `.vscode/settings.json` 中配置 Schema，编辑 Markdown 头部时支持自动补全与语法检查：
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

## 📊 Token 预算与性能实测

### Token 消耗对比（以 45 篇文档的中大型项目为例）

| 检索获取方式 | 扫描数据量 | 消耗 Token 上下文 | 单次检索耗时 |
|---|---|---|---|
| **暴力读取原始 Markdown 正文** | 45 个大文件 (~5 KB/篇) | ~75,000 Tokens | ~1,200 ms |
| **全量读取看板大盘文件** | 3 个看板 Markdown | ~4,500 Tokens | ~150 ms |
| **单行 `manifest.jsonl`（靶向过滤）** | 3-5 行单行 JSON | **< 300 Tokens（省 99%）** | **< 5 ms** |

### 脚本执行性能
- **全量扫描与编译速度**：扫描 100 篇文档耗时 **< 15ms**；
- **内存占用**：Python 执行期常驻内存 **< 12MB**；
- **防中断容灾设计（Fail-Open）**：即使遇到个别语法错误，脚本恒返回退出码 0，绝不阻断 AI 正常开发。

---

## ❓ 常见疑问 (FAQ)

<details>
<summary><b>为什么不直接用 SQLite 或本地向量数据库 (Vector DB)？</b></summary>
<br>
向量数据库和本地 SQLite 会引入二进制文件、常驻守护进程和复杂的 Schema 迁移，对人类开发者来说如同黑盒。而 Markdown + 单行 JSONL 真正做到零外部依赖，天然支持 Git Diff 审查，通过系统自带的 <code>grep</code> 和 <code>jq</code> 就能实现毫秒级快速流式过滤。
</details>

<details>
<summary><b>为什么使用单行 JSONL，而不是一个格式化的 JSON 数组？</b></summary>
<br>
如果是普通的 JSON 数组（<code>[...]</code>），任何读取工具都必须把整个几十 KB 的文件全量解析进内存。而使用 <code>manifest.jsonl</code>，AI 在终端里使用流式管道命令即可按需过滤目标行，完全不需要把整个索引丢进上下文模型中：
<pre><code>grep '"type": "architecture"' .context/manifest.jsonl | jq -r '.id'</code></pre>
</details>

<details>
<summary><b>如何防止任务越积越多导致整个目录膨胀失控？</b></summary>
<br>
系统设立了严格的任务双通道准入机制（非用户指令或人工确认不可立项）。此外，<code>sync_bundle.py</code> 会自动把超过 14 天未推进的任务标记为 <code>⚠️ Stagnant (>14d)</code> 亮红牌，并把结项超过 30 天的任务抓进 <code>CLEANUP.md</code> 清理待审池。
</details>

---

## 📄 开源许可证

本项目基于 [MIT 许可证](LICENSE) 开源。Copyright © 2026 WeiiWill.
