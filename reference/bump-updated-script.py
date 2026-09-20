#!/usr/bin/env python3
"""单文件 frontmatter `updated` 字段自动续期 —— 配合 hook 使用的最小工具。

只做一件事:给定一个 .context/ 下的文件路径,如果它的 frontmatter 里 `updated:` 不是今天,
就把这一个值改成今天,其余内容(字段顺序、间距、正文)原样保留、一字不改。
已经是今天则什么都不做(不写文件、不碰mtime),对没有frontmatter或没有`updated`字段的文件
也什么都不做——绝不新增字段、绝不吞掉正文。

`tasks/<slug>/progress.md` 本身不带frontmatter(唯一真相来源是同目录`README.md`),
所以命中 progress.md 时,续期目标会重定向到同目录的 README.md(见 bump_target())。

frontmatter定位逻辑必须和 sync_bundle.py 里的 FRONTMATTER_RE 保持完全一致,
否则两个脚本会对"什么算frontmatter"产生分歧。

用法: python3 scripts/bump_updated.py <被改动文件的绝对或相对路径>
设计给 PostToolUse hook 调用,任何异常都吞掉、退出码恒为0——绝不能因为这个辅助脚本
的问题去打断用户本来的Write/Edit操作。
"""
import re
import sys
from datetime import date
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parent.parent

# 必须和 sync_bundle.py 的 FRONTMATTER_RE 完全一致
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

GENERATED_NAMES = {"INDEX.md", "STATUS.md", "CLEANUP.md", "manifest.jsonl"}


def in_scope(path: Path) -> bool:
    if path.name in GENERATED_NAMES:
        return False
    try:
        rel = path.resolve().relative_to(BUNDLE_ROOT)
    except ValueError:
        return False
    parts = rel.parts
    if not parts:
        return False
    if parts[0] in ("docs", "research", "tasks") and path.suffix == ".md":
        return True
    return False


def bump_target(path: Path) -> Path:
    """progress.md 自己没有frontmatter,续期时改的是同目录README.md。"""
    if path.name == "progress.md":
        return path.parent / "README.md"
    return path


def bump_updated(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return False
    block = m.group(1)
    field_match = re.search(r"^(\s*updated\s*:\s*)(\S.*?)\s*$", block, re.MULTILINE)
    if not field_match:
        return False
    current_value = field_match.group(2).strip()
    today = date.today().isoformat()
    if current_value == today:
        return False
    new_block = block[: field_match.start(2)] + today + block[field_match.end(2) :]
    new_text = text[: m.start(1)] + new_block + text[m.end(1) :]
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        return
    try:
        path = Path(sys.argv[1]).resolve()
        if not path.is_file() or not in_scope(path):
            return
        bump_updated(bump_target(path))
    except Exception:
        return


if __name__ == "__main__":
    main()
