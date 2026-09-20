<!-- 本文件由 scripts/sync_bundle.py 自动生成，请勿手动编辑。新增/归档文档后重新运行脚本即可刷新。 -->

# .context/docs 索引

> 按 Frontmatter 里的 `type` 分栏。要新增内容，直接在 `docs/` 下建文件、写好 Frontmatter，然后运行 `python3 scripts/sync_bundle.py`。

## architecture (架构分析)

| 文档 | 路径 | 摘要 | 状态 |
|---|---|---|---|
| （示例)xxx-architecture.md | `docs/xxx-architecture.md` | 覆盖了哪几个模块/链路 | active |

## playbook (实验与优化方法论)

| 文档 | 路径 | 摘要 | 状态 |
|---|---|---|---|
| （示例)xxx-playbook.md | `docs/xxx-playbook.md` | 方法论覆盖的场景+当前验证状态 | active |

## handoff (交接文档)

| 文档 | 路径 | 摘要 | 状态 |
|---|---|---|---|
| （示例)handoff-xxx.md | `docs/handoff-xxx.md` | 交接的是哪块工作 | archived |

## investigation (问题排查)

| 文档 | 路径 | 摘要 | 状态 |
|---|---|---|---|
| （示例)xxx-shape-mismatch.md | `docs/xxx-shape-mismatch.md` | 问题现象一句话概括 | resolved |

## reading-map (导航/教学材料)

| 文档 | 路径 | 摘要 | 状态 |
|---|---|---|---|
| （示例)xxx-reading-map.md | `docs/xxx-reading-map.md` | 指向哪些内容的导航索引 | active |

## report (阶段性汇报)

| 文档 | 路径 | 摘要 | 状态 |
|---|---|---|---|
| （示例)xxx-tech-report-0826.md | `docs/xxx-tech-report-0826.md` | 汇报覆盖的时间段和结论 | archived |

## llm-io (LLM调用输入输出留档)

| 文档 | 路径 | 摘要 | 状态 |
|---|---|---|---|
| （示例)compile-generate_text-input-45d03b.txt | `docs/compile-generate_text-input-45d03b.txt` | 对应哪次调用/哪个case | archived |

---
机器可解析的完整版本见根目录 `.context/manifest.jsonl` (一行一条，含 path/type/status/tags/updated/summary/links)；待清理候选汇总见 `CLEANUP.md`。
