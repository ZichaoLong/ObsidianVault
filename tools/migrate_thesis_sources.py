#!/usr/bin/env python3
"""Migrate thesis markdown sources while preserving their body content."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path


VAULT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(os.environ.get("LLM_NOTES_SOURCE", "/home/zlong/llm/llm-notes"))
TARGET_DIR = VAULT_ROOT / "10-控制反馈-TokenInstruction" / "历史动机"
SOURCE_INDEX = VAULT_ROOT / "40-原始材料索引" / "控制反馈-历史动机源覆盖.md"
IMAGE_MAP = VAULT_ROOT / "_migration" / "mhtml-image-map.md"


@dataclass(frozen=True)
class SourceSpec:
    source: str
    target: str
    title: str


SOURCES = [
    SourceSpec("content/thesis/写在前面.md", "写在前面.md", "历史动机：写在前面"),
    SourceSpec("content/thesis/AI 的 System1+System2.md", "AI的System1-System2.md", "历史动机：AI 的 System1 + System2"),
    SourceSpec(
        "content/thesis/AI的时间 Scaling Law 的一些理论佐证.md",
        "AI的时间ScalingLaw理论佐证.md",
        "历史动机：AI 的时间 Scaling Law 理论佐证",
    ),
    SourceSpec(
        "content/thesis/控制反馈：Token[Instruction]=Opcode+Operands.md",
        "TokenInstruction-Opcode-Operands.md",
        "历史动机：Token[Instruction] = Opcode + Operands",
    ),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def image_replacements() -> dict[str, str]:
    replacements: dict[str, str] = {}
    if not IMAGE_MAP.exists():
        return replacements
    pattern = re.compile(r"\| `(?P<source>[^`]+)` \| \d+ \| `(?P<url>[^`]+)` \| `!\[\[(?P<attachment>[^\]]+)\]\]` \| ok \|")
    for line in IMAGE_MAP.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            replacements[match.group("url")] = f"![[{match.group('attachment')}]]"
    return replacements


def replace_remote_images(text: str, replacements: dict[str, str]) -> str:
    for url, attachment in replacements.items():
        text = re.sub(r"!\[[^\]]*\]\(" + re.escape(url) + r"(?:\s+\"[^\"]*\")?\)", attachment, text)
    return text


def migrate_source(spec: SourceSpec, replacements: dict[str, str]) -> tuple[Path, Path, str]:
    src = SOURCE_ROOT / spec.source
    dst = TARGET_DIR / spec.target
    body = src.read_text(encoding="utf-8", errors="replace")
    body = replace_remote_images(body, replacements)
    note = "\n".join(
        [
            f"# {spec.title}",
            "",
            "> 这是从 `llm-notes` 迁移的早期历史动机材料。它保留原始论证脉络，不代表当前收缩后的执行主线；当前结论见 [[../当前主线总览|当前主线总览]]。",
            "",
            f"来源：`/home/zlong/llm/llm-notes/{spec.source}`",
            "",
            "---",
            "",
        ]
    )
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(note + body.rstrip() + "\n", encoding="utf-8")
    return src, dst, sha256(src)


def main() -> None:
    replacements = image_replacements()
    rows = []
    for spec in SOURCES:
        src, dst, digest = migrate_source(spec, replacements)
        rel_dst = dst.relative_to(VAULT_ROOT)
        rows.append((spec.source, digest, rel_dst))

    lines = [
        "# 控制反馈：历史动机源覆盖",
        "",
        "迁移整理：2026-06-04",
        "",
        "本页记录早期 thesis 原始材料的迁移情况。这些页面保留原文主体，仅补充历史说明并把远程图片替换为本地附件。",
        "",
        "| 源文件 | sha256 | 迁移去向 | 迁移状态 |",
        "| --- | --- | --- | --- |",
    ]
    for source, digest, rel_dst in rows:
        target_name = rel_dst.stem
        lines.append(f"| `{source}` | `{digest}` | [[../{rel_dst.with_suffix('').as_posix()}\\|{target_name}]] | 已迁移原文主体 |")
    SOURCE_INDEX.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Migrated {len(rows)} thesis sources")
    print(f"Wrote {SOURCE_INDEX}")


if __name__ == "__main__":
    main()
