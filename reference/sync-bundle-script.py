#!/usr/bin/env python3
"""Agent Context Bundle 双层索引同步引擎 (Agent Context Bundle Sync Engine)

依据 Context Bundle 规范:
- 唯一事实来源 (SSOT): 各 Markdown 文件的 YAML Frontmatter
- 全局结构化索引: manifest.jsonl (含标准 Concept ID、resources 资产引用、links 相对关联)
- 自动生成看板: docs/INDEX.md、tasks/STATUS.md、CLEANUP.md (由脚本自动渲染，请勿手动编辑)
- 任务活跃度与时效治理: >14 天未更新停滞报警，>30 天完成任务超期归档审核
- 状态枚举: 全面采用严格英文 (draft, in_progress, paused, active, completed, resolved, archived)
- 机械化硬拦截门禁: 骨架白名单校验、任务资产跨域泄漏侦测、大体积冷数据熔断与 --doctor 健康自检

用法:
  python3 scripts/sync_bundle.py           # 常规同步 (更新看板与 manifest.jsonl)
  python3 scripts/sync_bundle.py --doctor  # 全仓健康巡检 (返回退出码与详细诊断)
"""
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

STAGNANT_DAYS = 14
CLEANUP_REVIEW_DAYS = 30
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB 限制

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

ALLOWED_TOP_DIRS = {"docs", "tasks", "research", "scripts", "schema"}
ALLOWED_TOP_FILES = {
    "AGENTS.md",
    "manifest.jsonl",
    "CLEANUP.md",
    "TODO.md",
    "CLAUDE.md",
    "GEMINI.md",
    "README.md",
    ".gitignore",
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

        if line_str.startswith("- ") and current_key:
            val = line_str[2:].strip()
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]
            list_items.append(val)
            continue

        if ":" in line_str:
            if current_key and list_items:
                raw[current_key] = list_items
                list_items = []
                current_key = None

            k, _, v = line_str.partition(":")
            k = k.strip()
            v = v.strip()

            if v.startswith("[") and v.endswith("]"):
                inner = v[1:-1].strip()
                if inner:
                    raw[k] = [
                        x.strip().strip("'\"")
                        for x in inner.split(",")
                        if x.strip()
                    ]
                else:
                    raw[k] = []
                current_key = None
            elif not v:
                current_key = k
                list_items = []
            else:
                if (v.startswith('"') and v.endswith('"')) or (
                    v.startswith("'") and v.endswith("'")
                ):
                    v = v[1:-1]
                elif v.lower() == "true":
                    v = True
                elif v.lower() == "false":
                    v = False
                raw[k] = v
                current_key = None

    if current_key and list_items:
        raw[current_key] = list_items

    return raw


def extract_title(text: str, fallback: str) -> str:
    cleaned = FRONTMATTER_RE.sub("", text).strip()
    for line in cleaned.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def extract_links(text: str) -> list[str]:
    links = []
    for _, url in MD_LINK_RE.findall(text):
        if not url.startswith(("http://", "https://", "#", "mailto:")):
            url_clean = url.split("#")[0].strip()
            if url_clean and url_clean not in links:
                links.append(url_clean)
    return links


def age_days(date_val) -> int | None:
    if not date_val:
        return None
    d = None
    if isinstance(date_val, (date, datetime)):
        d = date_val if isinstance(date_val, date) else date_val.date()
    elif isinstance(date_val, str):
        date_str = date_val.strip()[:10]
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None
    if d:
        return (date.today() - d).days
    return None


def validate_skeleton() -> list[str]:
    """检查顶层目录骨架白名单"""
    violations = []
    if not BUNDLE_ROOT.exists():
        return violations
    for item in BUNDLE_ROOT.iterdir():
        name = item.name
        if name.startswith(".git") or name in (".agents", ".claude", ".gemini"):
            continue
        if item.is_dir():
            if name not in ALLOWED_TOP_DIRS:
                violations.append(
                    f"非法顶层目录: '{name}' (仅限 {sorted(ALLOWED_TOP_DIRS)})。任务数据与评测应收敛于 tasks/<slug>/ 内。"
                )
        elif item.is_file():
            if name not in ALLOWED_TOP_FILES:
                violations.append(
                    f"非法顶层文件: '{name}'。请归入 docs/、research/ 或特定任务。"
                )
    return violations


def validate_scope_leaks(task_slugs: list[str]) -> list[str]:
    """检查是否有任务特化的文档泄漏到 docs/"""
    leaks = []
    if not DOCS_DIR.exists():
        return leaks

    # 提取任务关键词前缀
    keywords = set()
    for slug in task_slugs:
        keywords.add(slug)
        for part in slug.split("-"):
            if len(part) >= 3 and part not in ("http", "search", "with", "service"):
                keywords.add(part)

    for f in DOCS_DIR.glob("*.md"):
        if f.name in ("INDEX.md", "README.md", "AGENTS.md"):
            continue
        stem = f.stem.lower()
        if stem.startswith("handoff-"):
            for kw in keywords:
                if kw in stem:
                    leaks.append(
                        f"任务特化交接泄漏至 docs/: '{f.name}' 包含任务特征 '{kw}'。请移入对应 tasks/<task-slug>/docs/。"
                    )
                    break
        elif any(eval_id in stem for eval_id in ("eval6335", "eval-20", "eval_analysis")):
            leaks.append(
                f"任务特化排查/评测泄漏至 docs/: '{f.name}'。请移入 tasks/<task-slug>/docs/。"
            )
    return leaks


def validate_blobs() -> list[str]:
    """检查 .context/ 下是否存在非法的未受纳管超大冷数据"""
    oversized = []
    for p in BUNDLE_ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = str(p.relative_to(BUNDLE_ROOT))
        # 允许在 tasks/*/outputs/ 和 tasks/*/inputs/ 下存放评测数据，但其它地方报警
        if "/outputs/" in rel or "/inputs/" in rel:
            continue
        try:
            size = p.stat().st_size
            if size > MAX_FILE_SIZE_BYTES:
                oversized.append(
                    f"大体积文件预警 ({size // (1024*1024)}MB): '{rel}'。大文件严禁直接放置在知识库索引区，请移入 tasks/<slug>/outputs/ 或配置 .gitignore。"
                )
        except OSError:
            pass
    return oversized


def validate_tasks_integrity() -> list[str]:
    """检查任务目录的生命周期文件完整性"""
    task_errors = []
    if not TASKS_DIR.exists():
        return task_errors
    for task_dir in sorted(TASKS_DIR.iterdir()):
        if not task_dir.is_dir() or task_dir.name.startswith("."):
            continue
        slug = task_dir.name
        readme = task_dir / "README.md"
        progress = task_dir / "progress.md"
        if not readme.exists():
            task_errors.append(f"任务 '{slug}' 缺失核心文件: README.md")
        if not progress.exists():
            task_errors.append(f"任务 '{slug}' 缺失流水文件: progress.md")
    return task_errors


def scan_docs() -> list[dict]:
    entries = []
    search_files = []
    if DOCS_DIR.exists():
        search_files.extend(list(DOCS_DIR.glob("*.md")))
    if RESEARCH_DIR.exists():
        search_files.extend(list(RESEARCH_DIR.rglob("*.md")))
    if TASKS_DIR.exists():
        for sub in ("docs", "plans"):
            search_files.extend(list(TASKS_DIR.glob(f"*/{sub}/*.md")))

    for f in sorted(search_files):
        if f.name in (
            "INDEX.md",
            "README.md",
            "STATUS.md",
            "CLEANUP.md",
            "progress.md",
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
        ):
            continue
        text = f.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        rel_path = str(f.relative_to(BUNDLE_ROOT))

        if not fm and not rel_path.startswith(("docs/", "research/")):
            continue

        stem = f.stem
        concept_id = rel_path[:-3] if rel_path.endswith(".md") else rel_path
        doc_type = fm.get("type", "note").lower()
        status = str(fm.get("status", "active")).strip().lower()

        title = fm.get("title") or extract_title(text, stem)
        updated_raw = (
            fm.get("updated") or fm.get("updated_at") or fm.get("created", "")
        )
        created_raw = fm.get("created") or fm.get("created_at", "")
        days = age_days(updated_raw)

        cleanup_candidate = (
            not fm.get("pinned", False)
            and status in DONE_STATUSES
            and days is not None
            and days > CLEANUP_REVIEW_DAYS
        )

        prefix = stem.split("-")[0] if "-" in stem else ""
        naming_mismatch = (not rel_path.startswith("tasks/")) and (
            prefix in TYPE_LABELS and prefix != doc_type
        )

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
    by_type = {}
    for e in doc_entries:
        by_type.setdefault(e["type"], []).append(e)

    for t, label in TYPE_LABELS.items():
        items = by_type.get(t, [])
        if not items:
            continue
        lines.append(f"## {label}\n")
        lines.append(
            "| Document | Summary | Status | Resources | Updated | Notes |"
        )
        lines.append("|---|---|---|---|---|---|")
        for item in items:
            p = Path(item["path"])
            if p.parent == Path("docs"):
                rel_link = p.name
            else:
                rel_link = f"../{item['path']}"
            res_str = (
                f"`{len(item['resources'])} items`"
                if item["resources"]
                else "-"
            )
            notes = "⚠️ *Naming mismatch*" if item["naming_mismatch"] else ""
            lines.append(
                f"| [{p.name}]({rel_link}) | {item['summary']} | `{item['status']}` | {res_str} | {item['updated']} | {notes} |"
            )
        lines.append("")
    return "\n".join(lines)


def render_tasks_status(task_entries: list[dict]) -> str:
    lines = [
        "<!-- Generated automatically by scripts/sync_bundle.py. DO NOT edit manually. -->",
        "",
        "# Tasks Status Board",
        "",
        f"> Last synchronized: {date.today().isoformat()}. Run `python3 scripts/sync_bundle.py` to refresh.",
        "",
        "| Task Slug | Status | Summary | Resources | Updated | Age | Alerts |",
        "|---|---|---|---|---|---|---|",
    ]
    if not task_entries:
        lines.append("| - | *No tasks found* | - | - | - | - | - |")
        return "\n".join(lines) + "\n"

    for e in task_entries:
        rel_link = f"{e['slug']}/README.md"
        age = f"{e['age_days']}d" if e["age_days"] is not None else "-"
        flag = "🚨 *Stagnant*" if e["stagnant"] else "OK"
        res_str = f"`{len(e['resources'])} items`" if e["resources"] else "-"
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
            lines.append(
                f"| {e['type']} | `{e['path']}` | `{e['status']}` | {e['age_days']}d | {e['summary']} |"
            )
    return "\n".join(lines) + "\n"


def run_doctor() -> int:
    """全盘健康检查并输出诊断大盘"""
    print("=" * 60)
    print("🔍 [Context Bundle Doctor] 开始全盘健康检查与规范审计...")
    print("=" * 60)

    task_entries = scan_tasks()
    task_slugs = [e["slug"] for e in task_entries]
    doc_entries = scan_docs()

    skeleton_errs = validate_skeleton()
    scope_errs = validate_scope_leaks(task_slugs)
    blob_errs = validate_blobs()
    task_errs = validate_tasks_integrity()

    # 检查缺失 frontmatter 的文档
    missing_fm = []
    for d in doc_entries:
        if not d.get("summary") or d.get("type") == "note" and not d.get("tags"):
            pass

    has_errors = bool(skeleton_errs or scope_errs or blob_errs or task_errs)

    # 1. 骨架校验
    if skeleton_errs:
        print("\n❌ [1/4 顶层目录骨架]: FAIL")
        for err in skeleton_errs:
            print(f"   - {err}")
    else:
        print("\n✔ [1/4 顶层目录骨架]: PASS (所有顶层目录符合规范白名单)")

    # 2. 隔离域外溢校验
    if scope_errs:
        print("\n❌ [2/4 任务沙盒隔离域]: FAIL")
        for err in scope_errs:
            print(f"   - {err}")
    else:
        print("\n✔ [2/4 任务沙盒隔离域]: PASS (docs/ 无任务特化资产泄漏)")

    # 3. 任务生命周期骨架
    if task_errs:
        print("\n❌ [3/4 任务生命周期规范]: FAIL")
        for err in task_errs:
            print(f"   - {err}")
    else:
        print(f"\n✔ [3/4 任务生命周期规范]: PASS ({len(task_slugs)} 个任务均具备 README 与 progress)")

    # 4. 冷数据防熔断检查
    if blob_errs:
        print("\n⚠️ [4/4 大文件冷数据审计]: WARNING")
        for err in blob_errs:
            print(f"   - {err}")
    else:
        print("\n✔ [4/4 大文件冷数据审计]: PASS (无大于 5MB 的非结构化冷数据堆积)")

    print("\n" + "=" * 60)
    if has_errors:
        print("🚨 Doctor 诊断未通过，存在规范违规项，请根据上方指引修复。")
        return 1
    else:
        print("🎉 知识库状态极佳，所有系统检查均已通过！")
        return 0


def main() -> None:
    if "--doctor" in sys.argv:
        code = run_doctor()
        sys.exit(code)

    doc_entries = scan_docs()
    task_entries = scan_tasks()
    all_entries = doc_entries + task_entries
    task_slugs = [e["slug"] for e in task_entries]

    # 执行静默告警检查并输出到终端
    skeleton_errs = validate_skeleton()
    for err in skeleton_errs:
        print(f"⚠️ [Skeleton Warning] {err}", file=sys.stderr)

    scope_errs = validate_scope_leaks(task_slugs)
    for err in scope_errs:
        print(f"⚠️ [Scope Leak Warning] {err}", file=sys.stderr)

    if DOCS_DIR.exists():
        (DOCS_DIR / "INDEX.md").write_text(
            render_docs_index(doc_entries), encoding="utf-8"
        )

    if TASKS_DIR.exists():
        (TASKS_DIR / "STATUS.md").write_text(
            render_tasks_status(task_entries), encoding="utf-8"
        )

    (BUNDLE_ROOT / "CLEANUP.md").write_text(
        render_cleanup_md(all_entries), encoding="utf-8"
    )

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
