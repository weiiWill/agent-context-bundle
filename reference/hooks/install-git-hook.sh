#!/usr/bin/env bash
# install-git-hook.sh - Installs or appends pre-commit hook to maintain .context bundle consistency
# NOTE: Only applicable when .context/ is tracked in Git (Team-Shared Mode with granular .gitignore).
set -euo pipefail

GIT_DIR=$(git rev-parse --git-dir 2>/dev/null || true)
if [ -z "$GIT_DIR" ]; then
    echo "⚠️ Not a git repository. Skipping git hook installation."
    exit 0
fi

# Check if .context/ is globally ignored by .gitignore (Local-Only Mode)
if git check-ignore -q .context 2>/dev/null; then
    echo "ℹ️ .context/ is globally ignored by .gitignore (Local-Only Mode)."
    echo "   Git pre-commit hook will not trigger on .context changes and is skipped."
    echo "   Real-time consistency is handled by IDE/Agent PostToolUse hooks."
    exit 0
fi

HOOK_FILE="$GIT_DIR/hooks/pre-commit"
mkdir -p "$GIT_DIR/hooks"

# Marker to prevent duplicate installs
MARKER="# Context-Bundle Auto-Sync Hook"

if [ -f "$HOOK_FILE" ] && grep -q "$MARKER" "$HOOK_FILE"; then
    echo "✅ Context Bundle pre-commit hook is already installed in $HOOK_FILE"
    exit 0
fi

cat << 'EOF' >> "$HOOK_FILE"

# Context-Bundle Auto-Sync Hook
if [ -f ".context/scripts/sync_bundle.py" ]; then
    # Check if any .context files are staged
    if git diff --cached --name-only | grep -q '^\.context/'; then
        python3 .context/scripts/sync_bundle.py >/dev/null 2>&1 || true
        # Stage refreshed manifest and boards if they changed
        git add .context/manifest.jsonl .context/docs/INDEX.md .context/tasks/STATUS.md .context/CLEANUP.md 2>/dev/null || true
    fi
fi
EOF

chmod +x "$HOOK_FILE"
echo "✅ Context Bundle pre-commit hook installed successfully in $HOOK_FILE (Team-Shared Mode)"
