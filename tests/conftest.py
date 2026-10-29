"""Shared fixtures: temp `.context` mini-bundles exercising reference scripts."""
from __future__ import annotations

import shutil
import textwrap
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC_SCRIPT_SRC = REPO_ROOT / "reference" / "sync-bundle-script.py"
BUMP_SCRIPT_SRC = REPO_ROOT / "reference" / "bump-updated-script.py"


def _task_readme(slug: str, updated: str | None = None) -> str:
    today = date.today().isoformat()
    updated = updated or today
    return textwrap.dedent(
        f"""\
        ---
        type: task
        title: Demo task {slug}
        status: in_progress
        created: {today}
        updated: {updated}
        summary: Minimal fixture task for doctor/sync tests
        ---

        # Demo task {slug}

        Fixture task body.
        """
    )


def _doc_md(stem: str) -> str:
    today = date.today().isoformat()
    return textwrap.dedent(
        f"""\
        ---
        type: note
        topic: 【测试笔记】
        title: 【测试笔记】{stem}
        status: active
        created: {today}
        updated: {today}
        summary: Minimal fixture doc for sync tests
        ---

        # 【测试笔记】{stem}

        Fixture doc body.
        """
    )


@pytest.fixture
def context_bundle(tmp_path: Path) -> Path:
    """Build a valid mini `.context` with sync/bump scripts under scripts/."""
    root = tmp_path / ".context"
    scripts = root / "scripts"
    docs = root / "docs"
    tasks = root / "tasks" / "demo-task"
    scripts.mkdir(parents=True)
    docs.mkdir(parents=True)
    tasks.mkdir(parents=True)

    shutil.copy(SYNC_SCRIPT_SRC, scripts / "sync_bundle.py")
    shutil.copy(BUMP_SCRIPT_SRC, scripts / "bump_updated.py")

    (root / "README.md").write_text("# Context Bundle Fixture\n", encoding="utf-8")
    (root / ".gitignore").write_text("TODO.md\n", encoding="utf-8")
    (docs / f"note-fixture-{date.today().strftime('%Y%m%d')}.md").write_text(
        _doc_md("fixture"), encoding="utf-8"
    )
    (tasks / "README.md").write_text(_task_readme("demo-task"), encoding="utf-8")
    (tasks / "progress.md").write_text(
        "# Progress\n\n- [x] initialized fixture\n", encoding="utf-8"
    )
    for sub in ("inputs", "outputs", "scripts", "plans", "docs"):
        (tasks / sub).mkdir()

    return root


@pytest.fixture
def stale_updated() -> str:
    return (date.today() - timedelta(days=3)).isoformat()
