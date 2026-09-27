#!/usr/bin/env bash
# install_git_hook.sh - 注入严密的 Context Bundle pre-commit 门禁 (绑定 --doctor 体检)
# 注意: 仅在 .context/ 被 Git 纳管模式 (Team-Shared Mode) 下生效。
set -euo pipefail

GIT_DIR=$(git rev-parse --git-dir 2>/dev/null || true)
if [ -z "$GIT_DIR" ]; then
    echo "⚠️ Not a git repository. Skipping git hook installation."
    exit 0
fi

# 检查 .context/ 是否已被全局忽略 (Local-Only Mode)
if git check-ignore -q .context 2>/dev/null; then
    echo "ℹ️ .context/ is globally ignored by .gitignore (Local-Only Mode)."
    echo "   Git pre-commit hook will not trigger on .context changes and is skipped."
    echo "   Real-time consistency is handled by IDE/Agent PostToolUse hooks."
    exit 0
fi

HOOK_FILE="$GIT_DIR/hooks/pre-commit"
mkdir -p "$GIT_DIR/hooks"

# 防重复安装标记
MARKER="# Context-Bundle Auto-Sync & Doctor Hook"

if [ -f "$HOOK_FILE" ] && grep -q "$MARKER" "$HOOK_FILE"; then
    echo "✅ Context Bundle pre-commit hook is already installed in $HOOK_FILE"
    exit 0
fi

cat << 'EOF' >> "$HOOK_FILE"

# Context-Bundle Auto-Sync & Doctor Hook
if [ -f ".context/scripts/sync_bundle.py" ]; then
    if git diff --cached --name-only | grep -q '^\.context/'; then
        echo "🔄 [Context Bundle] 正在刷新索引与看板..."
        python3 .context/scripts/sync_bundle.py >&2 || true
        git add .context/manifest.jsonl .context/docs/INDEX.md .context/tasks/STATUS.md .context/CLEANUP.md 2>/dev/null || true

        echo "🔍 [Context Bundle] 正在执行全盘健康体检 (--doctor)..."
        if ! python3 .context/scripts/sync_bundle.py --doctor; then
            echo "❌ [Context Bundle Hook] 提交拦截：.context/ 存在规范违规或健康门禁未通过，请根据上方诊断修复后再提交！" >&2
            exit 1
        fi
    fi
fi
EOF

chmod +x "$HOOK_FILE"
echo "✅ Context Bundle pre-commit hook installed successfully with --doctor verification."
