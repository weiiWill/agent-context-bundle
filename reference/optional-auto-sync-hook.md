# 自动化生命周期 Hook 配置指引 (Automated Hooks)

为了保证 `.context/` 知识库的实时一致性，推荐接入各 Agent 框架的原生 Hook。各框架在保存文件时会自动续期 `updated:` 并刷新全局索引与看板。

Hook 协同工作机制：
1. **自动更新修改日期**：修改目标文件时，`bump_updated.py` 自动将 Frontmatter 的 `updated:` 字段更新为当天日期（幂等操作，已经是当天则不触碰文件）；
2. **自动重新编译索引与看板**：随后调用 `sync_bundle.py` 重新渲染 `docs/INDEX.md`、`tasks/STATUS.md`、`CLEANUP.md` 与 `manifest.jsonl`；
3. **错误反馈机制**：不采用静默吞错（移除 `2>/dev/null || true`），一旦检测到非法骨架或任务隔离域泄漏，异常直接反馈给宿主环境促使 Agent 即时纠偏。

---

## 1. Google Antigravity 配置 (`.agents/hooks.json`)

Antigravity 原生支持基于工具名称的正则匹配，且 `PostToolUse` 的 `stdout` 契约要求返回标准 JSON `{}`：

```json
{
  "context-bundle-sync": {
    "enabled": true,
    "PostToolUse": [
      {
        "matcher": "write_to_file|replace_file_content",
        "hooks": [
          {
            "type": "command",
            "command": "(python3 .context/scripts/sync_bundle.py 2>/dev/null || python3 ../.context/scripts/sync_bundle.py) >&2 && echo '{}'",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

---

## 2. Claude Code 配置 (`.claude/settings.local.json`)

Claude Code 原生支持基于参数路径的过滤（Permission Rule Syntax）：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [{
          "type": "command",
          "if": "Write(.context/**)",
          "command": "jq -r '.tool_input.file_path // .tool_response.filePath // empty' | { read -r f; [ -n \"$f\" ] && python3 .context/scripts/bump_updated.py \"$f\"; python3 .context/scripts/sync_bundle.py; }",
          "statusMessage": "Auto-syncing .context manifest and boards"
        }]
      },
      {
        "matcher": "Edit",
        "hooks": [{
          "type": "command",
          "if": "Edit(.context/**)",
          "command": "jq -r '.tool_input.file_path // .tool_response.filePath // empty' | { read -r f; [ -n \"$f\" ] && python3 .context/scripts/bump_updated.py \"$f\"; python3 .context/scripts/sync_bundle.py; }",
          "statusMessage": "Auto-syncing .context manifest and boards"
        }]
      }
    ]
  }
}
```

---

## 3. Git Pre-commit 门禁 (`.git/hooks/pre-commit`)

在支持 Git 纳管的模式下，运行 `.context/scripts/install_git_hook.sh` 自动植入防线。在每次提交前自动校验并强制执行 `--doctor`，一旦存在违规阻断提交。
