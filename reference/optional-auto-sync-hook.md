# 可选：让索引和 updated 字段自动化 (Hook)

这一步是可选的增强功能。如果不配置 Hook，直接在修改文档后手动运行 `python3 .context/scripts/sync_bundle.py` 同样完全可行。若希望在保存文件时自动续期 `updated:` 并刷新全局索引看板，可以在项目的 `.claude/settings.local.json` 中配置 `PostToolUse` Hook。

Hook 协同工作机制：
1. **真相层时效自维护**：修改目标文件时，`bump_updated.py` 自动将 Frontmatter 的 `updated:` 字段更新为当天日期（幂等操作，已经是当天则不触碰文件）；
2. **展示层看板自动编译**：随后自动调用 `sync_bundle.py` 重新渲染 `docs/INDEX.md`、`tasks/STATUS.md`、`CLEANUP.md` 与 `manifest.jsonl`。

## 配置片段 (`.claude/settings.local.json`)

Hook 的 `if` 过滤采用 `"Write(.context/**)"` 与 `"Edit(.context/**)"`，精确范围交由 `bump_updated.py` 内部的 `in_scope()` 函数判定（排除自动生成的中间看板文件）：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [{
          "type": "command",
          "if": "Write(.context/**)",
          "command": "jq -r '.tool_input.file_path // .tool_response.filePath // empty' | { read -r f; [ -n \"$f\" ] && python3 \"<项目绝对路径>/.context/scripts/bump_updated.py\" \"$f\"; python3 \"<项目绝对路径>/.context/scripts/sync_bundle.py\"; } 2>/dev/null || true",
          "statusMessage": "同步 .context/ 索引"
        }]
      },
      {
        "matcher": "Edit",
        "hooks": [{
          "type": "command",
          "if": "Edit(.context/**)",
          "command": "jq -r '.tool_input.file_path // .tool_response.filePath // empty' | { read -r f; [ -n \"$f\" ] && python3 \"<项目绝对路径>/.context/scripts/bump_updated.py\" \"$f\"; python3 \"<项目绝对路径>/.context/scripts/sync_bundle.py\"; } 2>/dev/null || true",
          "statusMessage": "同步 .context/ 索引"
        }]
      }
    ]
  }
}
```

> **提示**：
> 1. 命令中使用项目绝对路径，保证不同工作目录下均能准确定位脚本。
> 2. 两个脚本末尾均声明 `2>/dev/null || true`，保证任何辅助异常都不会打断主要编码任务。
