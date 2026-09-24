# Research Directory Agent Guidelines (`research/AGENTS.md`)

> 本文档为 `.context/research/` 目录的就近局部规约，当 Agent 访问或操作此目录时自动生效。

## 1. 核心红线 (Core Invariants)
- **代码库零污染原则**：调研过程中的原型脚本、基准评测数据必须保留在 `research/` 目录或内部工作区，严禁散落至业务源码根目录。
- **结论先行与证据支撑 (Evidence-First)**：调研文档必须有明确的“背景 -> 方案对比 -> 实验证据 -> 最终建议结论（Go / No-Go）”，杜绝空洞的代码摘抄。

## 2. 命名范式规范 (Naming Conventions)
- `investigation-<slug>-YYYYMMDD.md`：单次疑难排查与漏洞深挖（带日期）；
- `evaluation-<slug>.md`：长期有效的框架对比或技术选型评测（常青）。

## 3. YAML Frontmatter 规范
```yaml
---
type: investigation | note
title: "<调研主题标题>"
status: active | resolved | archived
created: YYYY-MM-DD
updated: YYYY-MM-DD
summary: "<调研核心结论与推荐方案>"
resources:
  - code://src/relevant_module.py
  - doc://docs/reference.md
---
```

## 4. 知识流转与退出
调研完成后，若技术方案被正式采纳，必须提炼核心架构决策沉淀至 `.context/docs/architecture-<slug>.md`，原调研文档置为 `status: resolved`。
