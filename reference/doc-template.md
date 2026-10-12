---
type: architecture # architecture | playbook | handoff | investigation | reading-map | report | note
topic: <主题>
title: 【<主题>】<文档标题>
status: active     # draft | active | completed | archived
resources:
  - code://src/service/processor.py#L42
  - doc://.context/docs/architecture-overview-YYYYMMDD.md
created: YYYY-MM-DD
updated: YYYY-MM-DD
summary: 一句话精准说明本文档的核心结论、设计决策或排查结果 (用于 manifest.jsonl 与 INDEX.md 索引)
pinned: false      # true 则豁免 >30 天清理审理
---

# 【<主题>】<文档标题>

文件名必须是 `{type}-{slug}-{YYYYMMDD}.md`。`topic` 写文档类型，如架构方案、架构优化、排查记录，不含方括号。`title` 和上面这个标题都以 `【文档类型】` 开头，后面再写具体内容。

## 1. 背景与上下文 (Context)
- 简述发起本篇文档的背景、要解决的技术问题或决策诉求。

## 2. 核心架构与设计决策 (Architecture & Decisions)
- 详细展开技术方案、时序图或架构权衡。

## 3. 验证与实证依据 (Evidence & Verification)
- 记录支撑该结论的测试输出、基准指标或代码验证命令。

## 4. 后续演进与关联资产 (Related Assets)
- 列出相关的下游任务、关联文档或代码入口。
