#!/usr/bin/env python3
"""Agent Context Bundle 双层索引同步引擎 (Agent Context Bundle Sync Engine)

依据 Context Bundle 规范:
- 唯一事实来源 (SSOT): 各 Markdown 文件的 YAML Frontmatter
- 全局结构化索引: manifest.jsonl (含标准 Concept ID、resources 资产引用、links 相对关联)
- 自动生成看板: docs/INDEX.md、tasks/STATUS.md、CLEANUP.md (由脚本自动渲染，请勿手动编辑)
- 任务活跃度与时效治理: >14 天未更新停滞报警，>30 天完成/暂停任务超期归档审理
- 任务沙盒封闭: 2 核心文件 (README.md, progress.md) + 5 正交子目录 (inputs, outputs, scripts, plans, docs)
- 机械化硬拦截门禁: 顶层骨架白名单、任务子目录规范白名单、任务资产跨域泄漏侦测、大文件防熔断与 --doctor 健康体检

用法:
  python3 scripts/sync_bundle.py           # 常规同步 (更新看板与 manifest.jsonl)
  python3 scripts/sync_bundle.py --doctor  # 全仓健康巡检 (返回退出码 0/1 与详细诊断报告)
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

FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---", re.DOTALL)
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# 统一状态枚举
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

# 任务目录内部规范
ALLOWED_TASK_SUBDIRS = {"inputs", "outputs", "scripts", "plans", "docs"}
ALLOWED_TASK_ROOT_FILES = {"README.md", "progress.md"}
FORBIDDEN_TASK_ALIASES = {
    "dataset": "inputs",
    "data": "inputs",
    "eval": "scripts 或 outputs",
    "report": "docs",
    "research": "docs",
}

# 忽略的系统与编辑器隐藏文件
SYSTEM_IGNORE_PATTERNS = {".DS_Store", "Thumbs.db", ".gitkeep"}


def escape_table_cell(text: str) -> str:
    """转义 Markdown 表格单元格中的特殊字符"""
    if not text:
        return ""
    return str(text).replace("\r\n", " ").replace("\n", " ").replace("|", "\\|").strip()


def parse_frontmatter(text: str) -> dict:
    if text.startswith("\ufeff"):
        text = text[1:]
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
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
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
                raw[k] = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()] if inner else []
                current_key = None
            elif not v:
                current_key = k
                list_items = []
            else:
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
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
    """提取 Markdown 内部相对链接，严防 Base64 / Data URI / 外部链接击穿单行索引"""
    links = []
    for _, url in MD_LINK_RE.findall(text):
        url_clean = url.strip()
        # 过滤外部协议、锚点及 Base64 / Data URI
        if url_clean.startswith(("http://", "https://", "#", "mailto:", "data:", "blob:", "file:")):
            continue
        if len(url_clean) > 256:
            continue
        url_clean = url_clean.split("#")[0].strip()
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
    """检查顶层目录骨架白名单 (杜绝漏检与系统残留误报)"""
    violations = []
    if not BUNDLE_ROOT.exists():
        return violations
    for item in BUNDLE_ROOT.iterdir():
        name = item.name
        if name.startswith(".git") or name in (".agents", ".claude", ".gemini", ".idea", ".vscode"):
            continue
        if name in SYSTEM_IGNORE_PATTERNS:
            continue

        if item.is_symlink() and not item.exists():
            violations.append(f"损坏的顶层软链接: '{name}'。请清理或修复链接目标。")
            continue

        if item.is_dir():
            if name not in ALLOWED_TOP_DIRS:
                violations.append(
                    f"非法顶层目录: '{name}' (仅限 {sorted(ALLOWED_TOP_DIRS)})。任务数据与评测应收敛于 tasks/<slug>/ 内。"
                )
        else:
            if name not in ALLOWED_TOP_FILES:
                violations.append(f"非法顶层文件: '{name}'。请归入 docs/、research/ 或特定任务。")
    return violations


def validate_task_skeleton() -> list[str]:
    """检查 tasks/<slug>/ 内部骨架白名单 (杜绝 dataset, eval, report, research 泛滥)"""
    violations = []
    if not TASKS_DIR.exists():
        return violations

    for item in TASKS_DIR.iterdir():
        if item.name.startswith(".") or item.name in SYSTEM_IGNORE_PATTERNS:
            continue
        if not item.is_dir():
            if item.name not in ("STATUS.md", "REGISTRY.md"):
                violations.append(f"非法任务根区文件: 'tasks/{item.name}'。任务散落文件请移入对应 tasks/<slug>/。")
            continue

        slug = item.name
        for sub_item in item.iterdir():
            sub_name = sub_item.name
            if sub_name.startswith(".") or sub_name in SYSTEM_IGNORE_PATTERNS:
                continue

            if sub_item.is_dir():
                if sub_name in FORBIDDEN_TASK_ALIASES:
                    violations.append(
                        f"任务 '{slug}' 包含违规别名目录: '{sub_name}/'。"
                        f"规范禁止该别名，请将其内容迁移收拢至 '{FORBIDDEN_TASK_ALIASES[sub_name]}/'。"
                    )
                elif sub_name not in ALLOWED_TASK_SUBDIRS:
                    violations.append(
                        f"任务 '{slug}' 包含非法子目录: '{sub_name}/' (仅限 {sorted(ALLOWED_TASK_SUBDIRS)})。"
                        f"请将数据移入 inputs/outputs/，脚本移入 scripts/，方案移入 plans/，文档移入 docs/。"
                    )
            else:
                if sub_name not in ALLOWED_TASK_ROOT_FILES and not sub_name.startswith("progress-archive-"):
                    violations.append(
                        f"任务 '{slug}' 根下存在非标文件: '{sub_name}' (仅限 {sorted(ALLOWED_TASK_ROOT_FILES)})。"
                        f"文档请移入 tasks/{slug}/docs/，临时输出移入 outputs/。"
                    )
    return violations


def validate_scope_leaks(task_slugs: list[str]) -> list[str]:
    """检查是否有任务特化的文档泄漏到 docs/ (全文档类型覆盖 + 单词边界匹配)"""
    leaks = []
    if not DOCS_DIR.exists() or not task_slugs:
        return leaks

    valid_slugs = [re.escape(slug) for slug in task_slugs if len(slug) >= 4]
    if not valid_slugs:
        return leaks

    slug_pattern = re.compile(r"(?:^|[-_])(" + "|".join(valid_slugs) + r")(?:[-_]|$)", re.IGNORECASE)

    for f in DOCS_DIR.glob("*.md"):
        if f.name in ("INDEX.md", "README.md", "AGENTS.md"):
            continue
        stem = f.stem.lower()

        m = slug_pattern.search(stem)
        if m:
            matched_slug = m.group(1)
            leaks.append(
                f"任务特化文档泄漏至 docs/: '{f.name}' 包含任务特征 '{matched_slug}'。请移入 tasks/{matched_slug}/docs/。"
            )
            continue

        try:
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
            task_attr = fm.get("task") or fm.get("task_slug")
            if task_attr and str(task_attr) in task_slugs:
                leaks.append(
                    f"任务特化文档泄漏至 docs/: '{f.name}' Frontmatter 归属任务 '{task_attr}'。请移入 tasks/{task_attr}/docs/。"
                )
        except Exception:
            pass

    return leaks


def validate_blobs() -> list[str]:
    """检查 .context/ 下是否存在非法的未受纳管超大冷数据 (跨平台兼容 + 忽略构建目录)"""
    oversized = []
    for p in BUNDLE_ROOT.rglob("*"):
        if any(part.startswith(".") for part in p.parts):
            continue
        if not p.is_file():
            continue

        parts = set(p.parts)
        if "outputs" in parts or "inputs" in parts:
            continue

        try:
            size = p.stat().st_size
            if size > MAX_FILE_SIZE_BYTES:
                rel = str(p.relative_to(BUNDLE_ROOT))
                oversized.append(
                    f"大体积冷数据超限 ({size // (1024*1024)}MB > 5MB): '{rel}'。"
                    f"严禁直接放置在知识库检索区，请移入对应 tasks/<slug>/outputs/ 或配置 .gitignore。"
                )
        except OSError:
            pass
    return oversized


def validate_tasks_integrity() -> list[str]:
    """检查任务目录的生命周期文件完整性与非空状态"""
    task_errors = []
    if not TASKS_DIR.exists():
        return task_errors

    for task_dir in sorted(TASKS_DIR.iterdir()):
        if not task_dir.is_dir() or task_dir.name.startswith(".") or task_dir.name in SYSTEM_IGNORE_PATTERNS:
            continue
        slug = task_dir.name
        readme = task_dir / "README.md"
        progress = task_dir / "progress.md"

        if not readme.exists():
            task_errors.append(f"任务 '{slug}' 缺失核心文件: README.md")
        elif readme.stat().st_size == 0:
            task_errors.append(f"任务 '{slug}' README.md 为 0 字节空文件，缺失 Frontmatter 元数据")
        else:
            fm = parse_frontmatter(readme.read_text(encoding="utf-8"))
            if not fm:
                task_errors.append(f"任务 '{slug}' README.md 缺失合法的 YAML Frontmatter (--- ... ---)")

        if not progress.exists():
            task_errors.append(f"任务 '{slug}' 缺失流水文件: progress.md")
        elif progress.stat().st_size == 0:
            task_errors.append(f"任务 '{slug}' progress.md 为 0 字节空文件")

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
                "has_frontmatter": bool(fm),
            }
        )
    return entries


def scan_tasks() -> list[dict]:
    entries = []
    if not TASKS_DIR.exists():
        return entries
    for task_dir in sorted(TASKS_DIR.iterdir()):
        if not task_dir.is_dir() or task_dir.name.startswith(".") or task_dir.name in SYSTEM_IGNORE_PATTERNS:
            continue
        slug = task_dir.name
        readme = task_dir / "README.md"
        if not readme.exists():
            continue

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
        is_paused = status == "paused"
        stagnant = is_active and days is not None and days > STAGNANT_DAYS
        stale_paused = is_paused and days is not None and days > CLEANUP_REVIEW_DAYS

        cleanup_candidate = (
            not fm.get("pinned", False)
            and (status in DONE_STATUSES or stale_paused)
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
                "stale_paused": stale_paused,
                "cleanup_candidate": cleanup_candidate,
                "links": extract_links(text),
                "has_frontmatter": bool(fm),
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
            summary = escape_table_cell(item["summary"])
            lines.append(
                f"| [{p.name}]({rel_link}) | {summary} | `{item['status']}` | {res_str} | {item['updated']} | {notes} |"
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
        if e["stagnant"]:
            flag = "🚨 *Stagnant*"
        elif e.get("stale_paused"):
            flag = "⏸️ *Stale Pause*"
        else:
            flag = "OK"
        res_str = f"`{len(e['resources'])} items`" if e["resources"] else "-"
        summary = escape_table_cell(e["summary"])
        lines.append(
            f"| [{e['slug']}]({rel_link}) | `{e['status']}` | {summary} | {res_str} | {e['updated']} | {age} | {flag} |"
        )
    return "\n".join(lines) + "\n"


def render_cleanup_md(entries: list[dict]) -> str:
    candidates = [e for e in entries if e.get("cleanup_candidate")]
    lines = [
        "<!-- Generated automatically by scripts/sync_bundle.py. DO NOT edit manually. -->",
        "",
        "# Cleanup Review Candidates",
        "",
        f"> Policy: Completed/Archived items (or stale paused items) untouched for > {CLEANUP_REVIEW_DAYS} days. Generated at: {date.today().isoformat()}",
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
            summary = escape_table_cell(e["summary"])
            lines.append(
                f"| {e['type']} | `{e['path']}` | `{e['status']}` | {e['age_days']}d | {summary} |"
            )
    return "\n".join(lines) + "\n"


def run_doctor() -> int:
    """全盘健康检查并输出诊断大盘 (严格阻断协议)"""
    print("=" * 60)
    print("🔍 [Context Bundle Doctor] 开始全盘健康检查与规范审计...")
    print("=" * 60)

    task_entries = scan_tasks()
    task_slugs = [
        d.name for d in TASKS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".") and d.name not in SYSTEM_IGNORE_PATTERNS
    ] if TASKS_DIR.exists() else []

    doc_entries = scan_docs()

    skeleton_errs = validate_skeleton()
    task_skeleton_errs = validate_task_skeleton()
    scope_errs = validate_scope_leaks(task_slugs)
    task_integrity_errs = validate_tasks_integrity()
    blob_errs = validate_blobs()

    missing_fm_errs = [
        f"文档缺少 Frontmatter 元数据: '{d['path']}'" for d in doc_entries if not d.get("has_frontmatter")
    ]

    has_errors = bool(
        skeleton_errs or task_skeleton_errs or scope_errs or task_integrity_errs or blob_errs or missing_fm_errs
    )

    # 1. 顶层骨架校验
    if skeleton_errs:
        print("\n❌ [1/5 顶层骨架规范]: FAIL")
        for err in skeleton_errs:
            print(f"   - {err}")
    else:
        print("\n✔ [1/5 顶层骨架规范]: PASS (顶层目录与文件符合规范白名单)")

    # 2. 任务沙盒内部骨架校验
    if task_skeleton_errs:
        print("\n❌ [2/5 任务子目录规范]: FAIL")
        for err in task_skeleton_errs:
            print(f"   - {err}")
    else:
        print("\n✔ [2/5 任务子目录规范]: PASS (任务内部目录严格收敛至 inputs/outputs/scripts/plans/docs)")

    # 3. 任务隔离域外溢校验
    if scope_errs:
        print("\n❌ [3/5 隔离域防外溢]: FAIL")
        for err in scope_errs:
            print(f"   - {err}")
    else:
        print("\n✔ [3/5 隔离域防外溢]: PASS (docs/ 目录下无任务特化资产泄漏)")

    # 4. 任务生命周期文件规范
    if task_integrity_errs:
        print("\n❌ [4/5 任务生命周期规范]: FAIL")
        for err in task_integrity_errs:
            print(f"   - {err}")
    else:
        print(f"\n✔ [4/5 任务生命周期规范]: PASS ({len(task_slugs)} 个任务 README 与 progress 均合法有效)")

    # 5. 冷数据与大文件门禁
    if blob_errs:
        print("\n❌ [5/5 大文件冷数据审计]: FAIL (超限阻断)")
        for err in blob_errs:
            print(f"   - {err}")
    else:
        print("\n✔ [5/5 大文件冷数据审计]: PASS (无 >5MB 的非结构化冷数据违规堆积)")

    # Frontmatter 补充诊断
    if missing_fm_errs:
        print("\n⚠️ [元数据治理审计]: WARNING")
        for err in missing_fm_errs:
            print(f"   - {err}")

    print("\n" + "=" * 60)
    if has_errors:
        print("🚨 Doctor 诊断未通过，存在机械门禁违规项，请根据上方指引修复后重新巡检。")
        return 1
    else:
        print("🎉 知识库状态极佳，所有机械防御门禁均已通过！")
        return 0


def main() -> None:
    if "--doctor" in sys.argv:
        code = run_doctor()
        sys.exit(code)

    doc_entries = scan_docs()
    task_entries = scan_tasks()
    all_entries = doc_entries + task_entries
    task_slugs = [
        d.name for d in TASKS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith(".") and d.name not in SYSTEM_IGNORE_PATTERNS
    ] if TASKS_DIR.exists() else []

    skeleton_errs = validate_skeleton()
    task_skeleton_errs = validate_task_skeleton()
    scope_errs = validate_scope_leaks(task_slugs)

    for err in skeleton_errs:
        print(f"⚠️ [Skeleton Warning] {err}", file=sys.stderr)
    for err in task_skeleton_errs:
        print(f"⚠️ [Task Skeleton Warning] {err}", file=sys.stderr)
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

    # 普通人类输出打印到 stderr，防止破坏 Hook 依赖 stdout 返回 JSON 的契约
    print(
        f"[Context Bundle Sync] Done: {len(doc_entries)} docs, {len(task_entries)} tasks "
        f"({stagnant_count} stagnant, {cleanup_count} cleanup candidates, {mismatch_count} naming alerts), "
        f"manifest -> {manifest_path}",
        file=sys.stderr
    )

    # 如果有严重骨架违规，退出码为 2 (Claude Code / 宿主框架会将 stderr 告警显式浮现给 Agent)
    if skeleton_errs or task_skeleton_errs or scope_errs:
        sys.exit(2)


if __name__ == "__main__":
    main()
