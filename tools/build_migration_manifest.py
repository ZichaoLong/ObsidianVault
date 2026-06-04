#!/usr/bin/env python3
"""Generate a migration manifest for ~/llm/llm-notes."""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


VAULT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(os.environ.get("LLM_NOTES_SOURCE", "/home/zlong/llm/llm-notes"))
OUT_DIR = VAULT_ROOT / "_migration"
TSV_PATH = OUT_DIR / "llm-notes-migration-manifest.tsv"
MD_PATH = OUT_DIR / "llm-notes-migration-manifest.md"


@dataclass
class ManifestRow:
    source_path: str
    kind: str
    migrate: str
    target_area: str
    size_bytes: int
    line_count: str
    sha256: str
    git_status: str
    notes: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(path: Path) -> str:
    if path.suffix.lower() != ".md":
        return ""
    with path.open("rb") as f:
        return str(sum(1 for _ in f))


def git_status_map() -> dict[str, str]:
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(SOURCE_ROOT), "status", "--porcelain=v1", "-z"],
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return {}

    result: dict[str, str] = {}
    chunks = raw.split(b"\0")
    i = 0
    while i < len(chunks):
        chunk = chunks[i]
        i += 1
        if not chunk:
            continue
        text = chunk.decode("utf-8", errors="replace")
        status = text[:2]
        path = text[3:]
        result[path] = status
        if status.startswith("R") or status.startswith("C"):
            i += 1
    return result


def classify(rel: str, path: Path) -> tuple[str, str, str, str]:
    suffix = path.suffix.lower()
    if suffix == ".mhtml":
        return (
            "mhtml_reference",
            "no",
            "mhtml-reference-only",
            "Do not migrate; use only for image recovery.",
        )
    if rel.startswith("fig/"):
        return ("asset", "yes", "attachments/llm-notes/fig", "Migrate as attachment.")
    if suffix == ".md":
        if rel.startswith("content/tech-notes/") or rel in {
            "content/scratch/notes.md",
            "content/scratch/draft.md",
        }:
            return ("markdown", "yes", "30-技术笔记", "Background note.")
        if "tide" in rel.lower():
            return ("markdown", "yes", "20-TIDE-去中心化神经网络", "TIDE line.")
        if rel.startswith(("review/", "defense/", "plan/", "status/")):
            if "tide" in rel.lower():
                return ("markdown", "yes", "20-TIDE-去中心化神经网络", "TIDE planning/defense.")
            return ("markdown", "yes", "10-控制反馈-TokenInstruction", "Control-feedback history.")
        if rel.startswith("content/scratch/从链表"):
            return ("markdown", "yes", "20-TIDE-去中心化神经网络", "TIDE source note.")
        if rel.startswith("content/scratch/Load_Store"):
            return ("markdown", "yes", "10-控制反馈-TokenInstruction", "Load/store source note.")
        if rel.startswith("content/thesis/"):
            return ("markdown", "yes", "10-控制反馈-TokenInstruction", "Control-feedback source note.")
        return ("markdown", "yes", "40-原始材料索引", "Needs manual classification.")
    return ("binary", "yes", "attachments/llm-notes/misc", "Migrate as attachment.")


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for path in SOURCE_ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda p: str(p.relative_to(SOURCE_ROOT)))


def build_rows() -> list[ManifestRow]:
    statuses = git_status_map()
    rows: list[ManifestRow] = []
    for path in iter_source_files():
        rel = str(path.relative_to(SOURCE_ROOT))
        kind, migrate, target, notes = classify(rel, path)
        rows.append(
            ManifestRow(
                source_path=rel,
                kind=kind,
                migrate=migrate,
                target_area=target,
                size_bytes=path.stat().st_size,
                line_count=line_count(path),
                sha256=sha256_file(path),
                git_status=statuses.get(rel, ""),
                notes=notes,
            )
        )
    return rows


def write_tsv(rows: list[ManifestRow]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(ManifestRow.__dataclass_fields__.keys())
    with TSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_markdown(rows: list[ManifestRow]) -> None:
    total = len(rows)
    migrate_yes = sum(1 for r in rows if r.migrate == "yes")
    mhtml = sum(1 for r in rows if r.kind == "mhtml_reference")
    markdown = sum(1 for r in rows if r.kind == "markdown")
    untracked = sum(1 for r in rows if r.git_status == "??")

    by_target: dict[str, int] = {}
    for row in rows:
        by_target[row.target_area] = by_target.get(row.target_area, 0) + 1

    lines = [
        "# llm-notes 迁移清单",
        "",
        f"来源：`{SOURCE_ROOT}`",
        "",
        "## 摘要",
        "",
        f"- 文件总数：{total}",
        f"- 需要迁移：{migrate_yes}",
        f"- Markdown：{markdown}",
        f"- mhtml 参考文件：{mhtml}",
        f"- git 未跟踪来源文件：{untracked}",
        "",
        "## 目标区域统计",
        "",
    ]
    for target, count in sorted(by_target.items()):
        lines.append(f"- `{target}`：{count}")

    lines.extend(
        [
            "",
            "## 需要注意",
            "",
            "- `mhtml` 文件不迁移到 Obsidian，只作为图片恢复来源。",
            "- `git_status = ??` 的来源文件同样纳入迁移，避免遗漏未提交内容。",
            "- 详细逐文件清单见 `llm-notes-migration-manifest.tsv`。",
            "",
            "## 逐文件清单",
            "",
            "| source_path | kind | migrate | target_area | git_status | notes |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.source_path.replace("|", "\\|"),
                    row.kind,
                    row.migrate,
                    row.target_area.replace("|", "\\|"),
                    row.git_status,
                    row.notes.replace("|", "\\|"),
                ]
            )
            + " |"
        )

    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_tsv(rows)
    write_markdown(rows)
    print(f"Wrote {TSV_PATH}")
    print(f"Wrote {MD_PATH}")


if __name__ == "__main__":
    main()
