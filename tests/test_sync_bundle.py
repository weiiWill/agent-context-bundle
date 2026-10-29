"""Fixture tests for doctor / sync / bump_updated (reference scripts)."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest


def _run(script: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd or script.parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )


def test_doctor_pass_on_valid_mini_bundle(context_bundle: Path) -> None:
    result = _run(context_bundle / "scripts" / "sync_bundle.py", "--doctor")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout
    assert "FAIL" not in result.stdout


def test_doctor_fail_on_illegal_top_level_dir(context_bundle: Path) -> None:
    (context_bundle / "dataset").mkdir()
    result = _run(context_bundle / "scripts" / "sync_bundle.py", "--doctor")
    assert result.returncode != 0
    assert "非法顶层目录" in result.stdout or "dataset" in result.stdout


def test_doctor_fail_on_illegal_task_alias_dir(context_bundle: Path) -> None:
    (context_bundle / "tasks" / "demo-task" / "dataset").mkdir()
    result = _run(context_bundle / "scripts" / "sync_bundle.py", "--doctor")
    assert result.returncode != 0
    assert "dataset" in result.stdout


def test_doctor_fail_on_missing_progress(context_bundle: Path) -> None:
    (context_bundle / "tasks" / "demo-task" / "progress.md").unlink()
    result = _run(context_bundle / "scripts" / "sync_bundle.py", "--doctor")
    assert result.returncode != 0
    assert "progress.md" in result.stdout


def test_sync_writes_manifest_jsonl(context_bundle: Path) -> None:
    result = _run(context_bundle / "scripts" / "sync_bundle.py")
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = context_bundle / "manifest.jsonl"
    assert manifest.is_file()
    lines = [ln for ln in manifest.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 1
    records = [json.loads(ln) for ln in lines]
    kinds = {r["kind"] for r in records}
    assert "doc" in kinds
    assert "task" in kinds
    assert any(r.get("id") == "tasks/demo-task" for r in records)


def test_sync_writes_boards(context_bundle: Path) -> None:
    result = _run(context_bundle / "scripts" / "sync_bundle.py")
    assert result.returncode == 0, result.stdout + result.stderr
    index = context_bundle / "docs" / "INDEX.md"
    status = context_bundle / "tasks" / "STATUS.md"
    cleanup = context_bundle / "CLEANUP.md"
    assert index.is_file()
    assert status.is_file()
    assert cleanup.is_file()
    assert "Generated automatically" in index.read_text(encoding="utf-8")
    assert "demo-task" in status.read_text(encoding="utf-8")
    assert "Cleanup Review" in cleanup.read_text(encoding="utf-8")


def test_sync_exit_2_on_skeleton_violation(context_bundle: Path) -> None:
    (context_bundle / "eval").mkdir()
    result = _run(context_bundle / "scripts" / "sync_bundle.py")
    assert result.returncode == 2
    assert (context_bundle / "manifest.jsonl").is_file()


def test_bump_updated_via_progress_redirects_to_readme(
    context_bundle: Path, stale_updated: str
) -> None:
    readme = context_bundle / "tasks" / "demo-task" / "README.md"
    progress = context_bundle / "tasks" / "demo-task" / "progress.md"
    text = readme.read_text(encoding="utf-8")
    readme.write_text(
        text.replace(f"updated: {date.today().isoformat()}", f"updated: {stale_updated}"),
        encoding="utf-8",
    )
    assert f"updated: {stale_updated}" in readme.read_text(encoding="utf-8")

    result = _run(context_bundle / "scripts" / "bump_updated.py", str(progress))
    assert result.returncode == 0, result.stdout + result.stderr
    bumped = readme.read_text(encoding="utf-8")
    assert f"updated: {date.today().isoformat()}" in bumped
    assert f"updated: {stale_updated}" not in bumped
    # progress.md itself must stay frontmatter-free / untouched beyond what we wrote
    assert "---" not in progress.read_text(encoding="utf-8").split("# Progress")[0]


def test_bump_updated_noop_when_already_today(context_bundle: Path) -> None:
    readme = context_bundle / "tasks" / "demo-task" / "README.md"
    before = readme.read_text(encoding="utf-8")
    mtime_before = readme.stat().st_mtime_ns
    result = _run(context_bundle / "scripts" / "bump_updated.py", str(readme))
    assert result.returncode == 0
    assert readme.read_text(encoding="utf-8") == before
    assert readme.stat().st_mtime_ns == mtime_before


def test_bump_updated_out_of_scope_is_noop(context_bundle: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text(
        "---\nupdated: 2020-01-01\n---\n\n# outside\n",
        encoding="utf-8",
    )
    before = outside.read_text(encoding="utf-8")
    result = _run(context_bundle / "scripts" / "bump_updated.py", str(outside))
    assert result.returncode == 0
    assert outside.read_text(encoding="utf-8") == before
