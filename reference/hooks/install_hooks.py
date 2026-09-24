#!/usr/bin/env python3
"""install_hooks.py - 自动侦测当前 Agent 框架并注入原生生命周期 Hook

支持自动识别并注入：
1. Google Antigravity (.agents/hooks.json)
2. Claude Code (.claude/settings.local.json)
3. Git Pre-commit (.git/hooks/pre-commit)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def detect_and_inject(project_root: Path | None = None) -> list[str]:
    if project_root is None:
        project_root = Path.cwd()

    injected: list[str] = []

    # 1. 检测 Antigravity 环境
    is_antigravity = (
        (project_root / ".agents").is_dir()
        or (project_root / "AGENTS.md").exists()
        or Path.home().joinpath(".gemini").is_dir()
        or "GEMINI_CLI" in os.environ
        or "ANTIGRAVITY" in os.environ
    )

    if is_antigravity:
        agents_dir = project_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        hooks_file = agents_dir / "hooks.json"
        
        hook_payload = {
            "context-bundle-sync": {
                "enabled": True,
                "PostToolUse": [
                    {
                        "matcher": "write_to_file",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 .context/scripts/sync_bundle.py 2>/dev/null || true",
                                "timeout": 5
                            }
                        ]
                    },
                    {
                        "matcher": "replace_file_content",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "python3 .context/scripts/sync_bundle.py 2>/dev/null || true",
                                "timeout": 5
                            }
                        ]
                    }
                ]
            }
        }

        existing_hooks = {}
        if hooks_file.exists():
            try:
                existing_hooks = json.loads(hooks_file.read_text(encoding="utf-8"))
            except Exception:
                existing_hooks = {}

        existing_hooks.update(hook_payload)
        hooks_file.write_text(json.dumps(existing_hooks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        injected.append(f"Antigravity Hook -> {hooks_file.relative_to(project_root)}")

    # 2. 检测 Claude Code 环境 (仅当项目本身有 Claude 标记或在 Claude 运行时中生效)
    is_claude = (
        (project_root / ".claude").is_dir()
        or (project_root / "CLAUDE.md").exists()
        or "CLAUDE_CODE" in os.environ
        or "CLAUDE_PROJECT_DIR" in os.environ
    )

    if is_claude:
        claude_dir = project_root / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        settings_file = claude_dir / "settings.local.json"

        claude_hook_entry = [
            {
                "matcher": "Write",
                "hooks": [
                    {
                        "type": "command",
                        "if": "Write(.context/**)",
                        "command": "jq -r '.tool_input.file_path // .tool_response.filePath // empty' | { read -r f; [ -n \"$f\" ] && python3 .context/scripts/bump_updated.py \"$f\"; python3 .context/scripts/sync_bundle.py; } 2>/dev/null || true",
                        "statusMessage": "Auto-syncing .context manifest and boards"
                    }
                ]
            },
            {
                "matcher": "Edit",
                "hooks": [
                    {
                        "type": "command",
                        "if": "Edit(.context/**)",
                        "command": "jq -r '.tool_input.file_path // .tool_response.filePath // empty' | { read -r f; [ -n \"$f\" ] && python3 .context/scripts/bump_updated.py \"$f\"; python3 .context/scripts/sync_bundle.py; } 2>/dev/null || true",
                        "statusMessage": "Auto-syncing .context manifest and boards"
                    }
                ]
            }
        ]

        settings_data = {}
        if settings_file.exists():
            try:
                settings_data = json.loads(settings_file.read_text(encoding="utf-8"))
            except Exception:
                settings_data = {}

        hooks_section = settings_data.setdefault("hooks", {})
        post_tool = hooks_section.setdefault("PostToolUse", [])

        # 检查是否已包含 Write(.context/**)
        has_context_hook = any(
            isinstance(item, dict)
            and any(
                isinstance(h, dict) and ".context/**" in h.get("if", "")
                for h in item.get("hooks", [])
            )
            for item in post_tool
        )

        if not has_context_hook:
            post_tool.extend(claude_hook_entry)
            settings_file.write_text(json.dumps(settings_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            injected.append(f"Claude Code Hook -> {settings_file.relative_to(project_root)}")
        else:
            injected.append(f"Claude Code Hook -> {settings_file.relative_to(project_root)} (已就绪)")

    # 3. 检测 Git 环境
    git_dir = project_root / ".git"
    if git_dir.is_dir():
        install_script = project_root / ".context" / "scripts" / "install_git_hook.sh"
        if install_script.exists():
            try:
                res = subprocess.run(["bash", str(install_script)], cwd=str(project_root), check=True, capture_output=True, text=True)
                if "installed successfully" in res.stdout or "already installed" in res.stdout:
                    injected.append("Git Pre-commit Hook -> .git/hooks/pre-commit")
                elif "globally ignored" in res.stdout:
                    injected.append("Git Pre-commit Hook -> 豁免安装 (本地沙盒模式: .context/ 已被 .gitignore 全局忽略)")
            except Exception:
                pass

    return injected


if __name__ == "__main__":
    results = detect_and_inject()
    if results:
        print("✅ 框架原生 Hook 自动识别与注入完成:")
        for r in results:
            print(f"  - {r}")
    else:
        print("ℹ️ 未识别到支持原生 Hook 的 Agent 框架或已全部配置。")
