# Scripts Directory Agent Guidelines (`scripts/AGENTS.md`)

> 本文档为 `.context/scripts/` 目录的就近局部规约，当 Agent 访问或操作此目录时自动生效。

## 1. 核心红线 (Core Invariants)
- **只读扫描与安全变更**：严禁未经自动化测试验证随意篡改或重构脚本核心逻辑。
- **免手动执行原则**：本目录下的工具均设计为由框架原生 Hook（`.agents/hooks.json`、`.claude/settings.local.json`）自动触发，仅在初始化或健康修复时由 Agent 显式调用。

## 2. 脚本职能清单
- `sync_bundle.py`：全量扫描目录、解析 Frontmatter、执行死链与时效校验、重新渲染 `manifest.jsonl`、`docs/INDEX.md` 与看板；
- `install_hooks.py`：自动感知宿主框架并实体化注入生命周期 Hook；
- `bump_updated.py`：根据文件改动自动递增 Frontmatter 中的 `updated:` 日期；
- `install_git_hook.sh`：团队协作模式下安装 Git 提交拦截器。
