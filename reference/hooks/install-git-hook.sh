#!/usr/bin/env bash
# install-git-hook.sh - 注入严密的 Context Bundle pre-commit 门禁 (兼容别名)
exec "$(dirname "$0")/install_git_hook.sh" "$@"
