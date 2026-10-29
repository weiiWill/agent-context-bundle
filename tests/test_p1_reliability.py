"""P1 reliability gate: progress auto-split, strict-links doctor, Antigravity detect."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_HOOKS_SRC = REPO_ROOT / "reference" / "hooks" / "install_hooks.py"


def _run(script: Path, *args: str, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd or script.parent.parent,
        capture_output=True,
        text=True,
        check=False,
        env=run_env,
    )


def _dated_entries(n: int, start: date | None = None) -> str:
    start = start or date(2024, 1, 1)
    lines = []
    for i in range(n):
        d = start + timedelta(days=i)
        lines.append(f"- {d.isoformat()}: fixture entry {i + 1} covering work item details.")
    return "\n".join(lines)


def _progress_body(entries: str, *, with_archive_summary: bool = False) -> str:
    parts = ["# Progress Log", ""]
    if with_archive_summary:
        parts.extend(["## Archive Summary", "", "## Log", ""])
    else:
        parts.extend(["## Log", ""])
    parts.append(entries)
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# 1) Progress auto-split
# ---------------------------------------------------------------------------


def test_sync_splits_progress_when_entries_exceed_threshold(context_bundle: Path) -> None:
    progress = context_bundle / "tasks" / "demo-task" / "progress.md"
    # 28 dated entries (> ~20–30 threshold mid-point) → must split
    progress.write_text(_progress_body(_dated_entries(28)), encoding="utf-8")

    result = _run(context_bundle / "scripts" / "sync_bundle.py")
    assert result.returncode in (0, 2), result.stdout + result.stderr

    archives = sorted((context_bundle / "tasks" / "demo-task").glob("progress-archive-*.md"))
    assert len(archives) >= 1, "expected progress-archive-* after oversized log"

    live = progress.read_text(encoding="utf-8")
    live_entries = [ln for ln in live.splitlines() if ln.startswith("- 20")]
    # Live file keeps a short recent window (~8–10), not the full history
    assert len(live_entries) <= 12
    assert "## Archive Summary" in live
    assert "progress-archive-" in live

    archive_text = archives[0].read_text(encoding="utf-8")
    assert "# Progress Log Archive" in archive_text
    assert "- 2024-01-01:" in archive_text


def test_sync_leaves_short_progress_intact(context_bundle: Path) -> None:
    progress = context_bundle / "tasks" / "demo-task" / "progress.md"
    original = _progress_body(_dated_entries(5))
    progress.write_text(original, encoding="utf-8")

    result = _run(context_bundle / "scripts" / "sync_bundle.py")
    assert result.returncode in (0, 2), result.stdout + result.stderr

    archives = list((context_bundle / "tasks" / "demo-task").glob("progress-archive-*.md"))
    assert archives == []
    assert progress.read_text(encoding="utf-8") == original


def test_sync_splits_progress_when_line_count_exceeds_threshold(context_bundle: Path) -> None:
    progress = context_bundle / "tasks" / "demo-task" / "progress.md"
    # Fewer than entry threshold, but pad to >200 lines
    header = "# Progress Log\n\n## Log\n\n"
    entry_block = _dated_entries(8)
    padding = "\n".join(f"<!-- pad line {i} -->" for i in range(220))
    progress.write_text(header + entry_block + "\n" + padding + "\n", encoding="utf-8")

    result = _run(context_bundle / "scripts" / "sync_bundle.py")
    assert result.returncode in (0, 2), result.stdout + result.stderr

    archives = list((context_bundle / "tasks" / "demo-task").glob("progress-archive-*.md"))
    assert len(archives) >= 1
    live_lines = progress.read_text(encoding="utf-8").splitlines()
    assert len(live_lines) < 200


# ---------------------------------------------------------------------------
# 2) Strict-links doctor gate
# ---------------------------------------------------------------------------


def test_doctor_fail_on_broken_relative_markdown_link(context_bundle: Path) -> None:
    doc = next((context_bundle / "docs").glob("note-fixture-*.md"))
    text = doc.read_text(encoding="utf-8")
    doc.write_text(text + "\nSee also [missing](./does-not-exist-anywhere.md).\n", encoding="utf-8")

    result = _run(context_bundle / "scripts" / "sync_bundle.py", "--doctor")
    assert result.returncode != 0
    assert "FAIL" in result.stdout
    assert "does-not-exist-anywhere.md" in result.stdout or "断链" in result.stdout or "link" in result.stdout.lower()


def test_doctor_pass_when_relative_and_code_links_resolve(context_bundle: Path, tmp_path: Path) -> None:
    # Project-root file for code:// resolution (bundle is tmp/.context → project is tmp)
    project_root = context_bundle.parent
    src = project_root / "src"
    src.mkdir()
    (src / "demo.py").write_text("print('ok')\n", encoding="utf-8")

    target = context_bundle / "docs" / "note-peer.md"
    today = date.today().isoformat()
    target.write_text(
        textwrap.dedent(
            f"""\
            ---
            type: note
            topic: 【测试笔记】
            title: 【测试笔记】peer
            status: active
            created: {today}
            updated: {today}
            summary: Peer doc for link resolution
            resources:
              - code://src/demo.py
            ---

            # 【测试笔记】peer

            Peer body.
            """
        ),
        encoding="utf-8",
    )

    doc = next((context_bundle / "docs").glob("note-fixture-*.md"))
    text = doc.read_text(encoding="utf-8")
    # Insert resources + relative link that resolve
    text = text.replace(
        "summary: Minimal fixture doc for sync tests",
        "summary: Minimal fixture doc for sync tests\nresources:\n  - code://src/demo.py",
    )
    doc.write_text(text + "\nSee [peer](./note-peer.md).\n", encoding="utf-8")

    result = _run(context_bundle / "scripts" / "sync_bundle.py", "--doctor")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FAIL" not in result.stdout
    # New gate label present
    assert "[6/" in result.stdout


def test_doctor_fail_on_broken_code_link(context_bundle: Path) -> None:
    doc = next((context_bundle / "docs").glob("note-fixture-*.md"))
    text = doc.read_text(encoding="utf-8")
    text = text.replace(
        "summary: Minimal fixture doc for sync tests",
        "summary: Minimal fixture doc for sync tests\nresources:\n  - code://src/missing_file.py",
    )
    doc.write_text(text, encoding="utf-8")

    result = _run(context_bundle / "scripts" / "sync_bundle.py", "--doctor")
    assert result.returncode != 0
    assert "missing_file.py" in result.stdout or "code://" in result.stdout


# ---------------------------------------------------------------------------
# 3) Antigravity detection (no AGENTS.md false positive)
# ---------------------------------------------------------------------------


@pytest.fixture
def hooks_project(tmp_path: Path) -> Path:
    """Minimal project with install_hooks.py under .context/scripts/."""
    project = tmp_path / "proj"
    scripts = project / ".context" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(INSTALL_HOOKS_SRC, scripts / "install_hooks.py")
    return project


def _clean_env() -> dict[str, str]:
    """Drop Antigravity/Gemini runtime markers so detection is project-local only."""
    return {k: v for k, v in os.environ.items() if k not in ("ANTIGRAVITY", "GEMINI_CLI")}


def test_install_hooks_skips_antigravity_when_only_agents_md(hooks_project: Path) -> None:
    (hooks_project / "AGENTS.md").write_text("# Cursor rules\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(hooks_project / ".context" / "scripts" / "install_hooks.py")],
        cwd=hooks_project,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (hooks_project / ".agents").exists()
    assert "Antigravity" not in result.stdout


def test_install_hooks_injects_antigravity_when_agents_dir(hooks_project: Path) -> None:
    (hooks_project / ".agents").mkdir()
    result = subprocess.run(
        [sys.executable, str(hooks_project / ".context" / "scripts" / "install_hooks.py")],
        cwd=hooks_project,
        capture_output=True,
        text=True,
        check=False,
        env=_clean_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    hooks_file = hooks_project / ".agents" / "hooks.json"
    assert hooks_file.is_file()
    assert "Antigravity" in result.stdout
    assert "context-bundle-sync" in hooks_file.read_text(encoding="utf-8")
