#!/usr/bin/env python3
"""Agent Context Bundle 双层索引同步引擎 (Agent Context Bundle Sync Engine)

依据 Context Bundle 权威元数据与物化视图规范:
- 权威元数据源 (SSOT): 各 Markdown 文件的 YAML Frontmatter
- 物化检索索引: manifest.jsonl (含标准 Concept ID、resources 资产引用、links 图谱关联)
- 聚合只读看板: docs/INDEX.md、tasks/STATUS.md、CLEANUP.md (由脚本自动渲染，请勿手动编辑)
- 任务活跃度与时效治理: >14 天未更新停滞报警，>30 天完成任务超期归档审核
- 状态枚举: 全面采用严格英文 (draft, in_progress, paused, active, completed, resolved, archived)

用法:
  python3 scripts/sync_bundle.py
  (或兼容入口: python3 scripts/sync_manifest.py)
"""
import json
import os
import re
from datetime import date, datetime
from pathlib import Path

STAGNANT_DAYS = 14
CLEANUP_REVIEW_DAYS = 30

BUNDLE_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = BUNDLE_ROOT / "docs"
RESEARCH_DIR = BUNDLE_ROOT / "research"
TASKS_DIR = BUNDLE_ROOT / "tasks"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# 统一严格英文状态枚举
DONE_STATUSES = {"completed", "resolved", "archived"}
ACTIVE_STATUSES = {"in_progress", "active", "draft"}

TYPE_LABELS = {
    "architecture": "architecture (Architecture Analysis & ADR)",
    "playbook": "playbook (Playbooks & Methodologies)",
    "handoff": "handoff (Session Handoffs)",
    "investigation": "investigation (Problem Investigations)",
    "draft": "draft (Design & Implementation Drafts)",
    "reading-map": "reading-map (Reading & Navigation Maps)",
    "report": "report (Periodic Reports)",
    "llm-io": "llm-io (LLM Input/Output Traces)",
    "note": "note (General Notes)",
    "task": "task (Task Units)",
}


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    content = m.group(1)
    raw = {}
    current_key = None
    list_items = []

    for line in content.splitlines():
        line_str = line.strip()
        if not line_str or line_str.startswith("#"):
            continue
        if line_str.startswith("- "):
            item_val = line_str[2:].strip().strip("'\"")
            if current_key:
                list_items.append(item_val)
                raw[current_key] = list(list_items)
            continue
        if ":" in line:
            parts = line.split(":", 1)
            k = parts[0].strip()
            v = parts[1].strip()
            current_key = k
            list_items = []
            if v:
                if v.startswith("[") and v.endswith("]"):
                    raw[k] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
                else:
                    raw[k] = v.strip("'\"")
            else:
                raw[k] = []

    raw["pinned"] = str(raw.get("pinned", "")).strip().lower() == "true"
    if "tags" in raw and isinstance(raw["tags"], str):
        raw["tags"] = [raw["tags"]]
    elif "tags" not in raw:
        raw["tags"] = []

    if "resources" in raw and isinstance(raw["resources"], str):
        raw["resources"] = [raw["resources"]]
    elif "resources" not in raw:
        raw["resources"] = []

    return raw


def extract_title(text: str, fallback: str) -> str:
    m = FRONTMATTER_RE.match(text)
    if m:
        fm = parse_frontmatter(text)
        if "title" in fm and fm["title"]:
            return str(fm["title"]).strip()
    body = text[m.end() :] if m else text
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def extract_links(text: str) -> list[str]:
    links = []
    for _, url in MD_LINK_RE.findall(text):
        if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("#"):
            links.append(url.split("#")[0])
    return sorted(list(set(links)))


def age_days(updated_raw: str) -> int | None:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            d = datetime.strptime(str(updated_raw).strip(), fmt).date()
            return (date.today() - d).days
        except (ValueError, TypeError):
            continue
    return None


def scan_docs() -> list[dict]:
    entries = []
    search_files: list[Path] = []
    for base in (DOCS_DIR, RESEARCH_DIR):
        if base.exists():
            search_files.extend(base.rglob("*.md"))
            
    if TASKS_DIR.exists():
        for sub in ("docs", "plans"):
            search_files.extend(TASKS_DIR.glob(f"*/{sub}/*.md"))

    for f in sorted(search_files):
        if f.name in ("INDEX.md", "README.md", "STATUS.md", "CLEANUP.md", "progress.md"):
            continue
        text = f.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        rel_path = str(f.relative_to(BUNDLE_ROOT))
        
        # 对于 tasks 下的子文档，如果既无 frontmatter 且非顶级文档，跳过
        if not fm and not rel_path.startswith(("docs/", "research/")):
            continue
            
        stem = f.stem
        concept_id = rel_path[:-3] if rel_path.endswith(".md") else rel_path
        doc_type = fm.get("type", "note").lower()
        status = str(fm.get("status", "active")).strip().lower()
        
        title = fm.get("title") or extract_title(text, stem)
        updated_raw = fm.get("updated") or fm.get("updated_at") or fm.get("created", "")
        created_raw = fm.get("created") or fm.get("created_at", "")
        days = age_days(updated_raw)
        
        cleanup_candidate = (
            not fm.get("pinned", False)
            and status in DONE_STATUSES
            and days is not None
            and days > CLEANUP_REVIEW_DAYS
        )
        
        prefix = stem.split("-")[0] if "-" in stem else ""
        naming_mismatch = (not rel_path.startswith("tasks/")) and (prefix in TYPE_LABELS and prefix != doc_type)
        
        entries.append(
            {
                "id": concept_id,
                "kind": "doc",
                "path": rel_path,
                "type": doc_type,
                "title": title,
                "status": status,
                "tags": fm.get("tags", []),
                "resources": fm.get("resources", []),
                "created": str(created_raw),
                "updated": str(updated_raw),
                "summary": fm.get("summary") or fm.get("description", ""),
                "pinned": fm.get("pinned", False),
                "age_days": days,
                "cleanup_candidate": cleanup_candidate,
                "naming_mismatch": naming_mismatch,
                "links": extract_links(text),
            }
        )
    return entries


def scan_tasks() -> list[dict]:
    entries = []
    if not TASKS_DIR.exists():
        return entries
    for readme in sorted(TASKS_DIR.glob("*/README.md")):
        slug = readme.parent.name
        rel_path = str(readme.relative_to(BUNDLE_ROOT))
        text = readme.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        
        concept_id = f"tasks/{slug}"
        status = str(fm.get("status", "draft")).strip().lower()
        
        title = fm.get("title") or extract_title(text, slug)
        updated_raw = fm.get("updated") or fm.get("updated_at", "")
        created_raw = fm.get("created") or fm.get("created_at", "")
        days = age_days(updated_raw)
        
        is_active = status in ACTIVE_STATUSES
        stagnant = is_active and days is not None and days > STAGNANT_DAYS
        cleanup_candidate = (
            not fm.get("pinned", False)
            and status in DONE_STATUSES
            and days is not None
            and days > CLEANUP_REVIEW_DAYS
        )
        
        entries.append(
            {
                "id": concept_id,
                "kind": "task",
                "path": rel_path,
                "slug": slug,
                "type": "task",
                "title": title,
                "status": status,
                "tags": fm.get("tags", []),
                "resources": fm.get("resources", []),
                "created": str(created_raw),
                "updated": str(updated_raw or "missing"),
                "summary": fm.get("summary") or fm.get("description", ""),
                "pinned": fm.get("pinned", False),
                "age_days": days,
                "stagnant": stagnant,
                "cleanup_candidate": cleanup_candidate,
                "links": extract_links(text),
            }
        )
    return entries


def render_docs_index(doc_entries: list[dict]) -> str:
    lines = [
        "<!-- Generated automatically by scripts/sync_bundle.py. DO NOT edit manually. -->",
        "",
        "# Knowledge Index",
        "",
        "> Dual-Layer Architecture: Frontmatter is the Truth Layer, this file is the Presentation Layer.",
        "",
    ]
    by_type: dict[str, list[dict]] = {}
    for e in doc_entries:
        by_type.setdefault(e["type"], []).append(e)
        
    known_keys = list(TYPE_LABELS.keys())
    all_keys = known_keys + [k for k in sorted(by_type.keys()) if k not in known_keys]
    for type_key in all_keys:
        rows = by_type.get(type_key, [])
        if not rows:
            continue
        label = TYPE_LABELS.get(type_key, f"{type_key} (General {type_key.capitalize()} Documents)")
        lines.append(f"## {label}")
        lines.append("")
        lines.append("| Document | Summary | Status | Resources | Updated | Notes |")
        lines.append("|---|---|---|---|---|---|")
        for e in rows:
            name = Path(e["path"]).name
            flag = "⚠️ Naming mismatch with type" if e["naming_mismatch"] else ""
            res_str = f"`{len(e['resources'])} items`" if e["resources"] else "-"
            rel_link = os.path.relpath(BUNDLE_ROOT / e["path"], DOCS_DIR)
            lines.append(
                f"| [{name}]({rel_link}) | {e['summary']} | `{e['status']}` | {res_str} | {e['updated']} | {flag} |"
            )
        lines.append("")
        
    lines.append("---")
    lines.append("Machine-readable structured index: `manifest.jsonl` (queryable via `jq` / `grep`).")
    return "\n".join(lines) + "\n"


def render_tasks_status(task_entries: list[dict]) -> str:
    lines = [
        "<!-- Generated automatically by scripts/sync_bundle.py. DO NOT edit manually. -->",
        "",
        "# Tasks Status Board",
        "",
        f"> Generated at: {date.today().isoformat()}",
        "",
        "| Task Slug | Status | Summary | Resources | Updated | Age | Alerts |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in task_entries:
        flag = "⚠️ Stagnant (>14d)" if e["stagnant"] else ""
        age = f"{e['age_days']}d" if e["age_days"] is not None else "unknown"
        res_str = f"`{len(e['resources'])} items`" if e["resources"] else "-"
        rel_link = os.path.relpath(BUNDLE_ROOT / e["path"], TASKS_DIR)
        lines.append(
            f"| [{e['slug']}]({rel_link}) | `{e['status']}` | {e['summary']} | {res_str} | {e['updated']} | {age} | {flag} |"
        )
    return "\n".join(lines) + "\n"


def render_cleanup_md(entries: list[dict]) -> str:
    candidates = [e for e in entries if e.get("cleanup_candidate")]
    lines = [
        "<!-- Generated automatically by scripts/sync_bundle.py. DO NOT edit manually. -->",
        "",
        "# Cleanup Review Candidates",
        "",
        f"> Policy: Completed/Archived items untouched for > {CLEANUP_REVIEW_DAYS} days. Generated at: {date.today().isoformat()}",
        "",
        "> [!IMPORTANT]",
        "> **Deletion Iron Rules**: Confirm: 1) No other doc or code references it, 2) Reproducible from external code/data, 3) No audit/post-mortem value. If uncertain, keep or mark `pinned: true`.",
        "",
        "| Type | Path | Status | Age | Summary |",
        "|---|---|---|---|---|",
    ]
    if not candidates:
        lines.append("| - | *No cleanup candidates currently* | - | - | - |")
    else:
        for e in candidates:
            lines.append(f"| {e['type']} | `{e['path']}` | `{e['status']}` | {e['age_days']}d | {e['summary']} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    doc_entries = scan_docs()
    task_entries = scan_tasks()
    all_entries = doc_entries + task_entries

    if DOCS_DIR.exists():
        (DOCS_DIR / "INDEX.md").write_text(render_docs_index(doc_entries), encoding="utf-8")
        
    if TASKS_DIR.exists():
        (TASKS_DIR / "STATUS.md").write_text(render_tasks_status(task_entries), encoding="utf-8")

    (BUNDLE_ROOT / "CLEANUP.md").write_text(render_cleanup_md(all_entries), encoding="utf-8")

    manifest_path = BUNDLE_ROOT / "manifest.jsonl"
    with manifest_path.open("w", encoding="utf-8") as f:
        for e in all_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    stagnant_count = sum(1 for e in task_entries if e["stagnant"])
    cleanup_count = sum(1 for e in all_entries if e.get("cleanup_candidate"))
    mismatch_count = sum(1 for e in doc_entries if e.get("naming_mismatch"))
    
    print(
        f"[Context Bundle Sync] Done: {len(doc_entries)} docs, {len(task_entries)} tasks "
        f"({stagnant_count} stagnant, {cleanup_count} cleanup candidates, {mismatch_count} naming alerts), "
        f"manifest -> {manifest_path}"
    )


if __name__ == "__main__":
    main()
