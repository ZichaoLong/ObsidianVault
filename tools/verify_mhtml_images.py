#!/usr/bin/env python3
"""Verify whether markdown image links can be recovered from same-name mhtml files."""

from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from pathlib import Path


VAULT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(os.environ.get("LLM_NOTES_SOURCE", "/home/zlong/llm/llm-notes"))
OUT_DIR = VAULT_ROOT / "_migration"
REPORT_PATH = OUT_DIR / "mhtml-image-report.md"
REMOTE_IMAGE_RE = re.compile(r"!\[[^\]]*\]\((https://clouddocs\.huawei\.com/[^)\s]+)(?:\s+\"[^\"]*\")?\)")
IMG_DATA_RE = re.compile(
    r"<img\b[^>]*\bsrc=[\"']data:image/([^;\"']+);base64,([^\"']+)[\"']",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class MarkdownImageRef:
    markdown_path: Path
    line_number: int
    url: str


@dataclass
class ExtractedImage:
    image_type: str
    byte_size: int
    valid: bool
    error: str


def markdown_image_refs(path: Path) -> list[MarkdownImageRef]:
    refs: list[MarkdownImageRef] = []
    for index, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        for match in REMOTE_IMAGE_RE.finditer(line):
            refs.append(MarkdownImageRef(path, index, match.group(1)))
    return refs


def matching_mhtml(path: Path) -> Path:
    return SOURCE_ROOT / f"{path.stem}.mhtml"


def decoded_html_from_mhtml(path: Path) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    parts = msg.walk() if msg.is_multipart() else [msg]
    for part in parts:
        ctype = part.get_content_type()
        if ctype == "text/html":
            content = part.get_content()
            if isinstance(content, bytes):
                return content.decode("utf-8", errors="replace")
            return str(content)
    return ""


def extract_body_images(path: Path) -> list[ExtractedImage]:
    html = decoded_html_from_mhtml(path)
    images: list[ExtractedImage] = []
    for match in IMG_DATA_RE.finditer(html):
        image_type = match.group(1).lower()
        payload = re.sub(r"\s+", "", match.group(2))
        try:
            raw = base64.b64decode(payload, validate=False)
            images.append(ExtractedImage(image_type, len(raw), len(raw) > 0, ""))
        except Exception as exc:
            images.append(ExtractedImage(image_type, 0, False, str(exc)))
    return images


def all_remote_markdown_refs() -> dict[Path, list[MarkdownImageRef]]:
    grouped: dict[Path, list[MarkdownImageRef]] = {}
    for path in sorted(SOURCE_ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        refs = markdown_image_refs(path)
        if refs:
            grouped[path] = refs
    return grouped


def write_report() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grouped = all_remote_markdown_refs()
    lines = [
        "# mhtml 图片抽取验证报告",
        "",
        f"来源：`{SOURCE_ROOT}`",
        "",
        "本报告只验证远程 `clouddocs` 图片是否可从同名 `mhtml` 中恢复。",
        "`mhtml` 本体不迁移到 Obsidian。",
        "",
        "## 摘要",
        "",
    ]
    total_refs = sum(len(refs) for refs in grouped.values())
    lines.append(f"- 含远程图片的 Markdown：{len(grouped)}")
    lines.append(f"- 远程图片引用总数：{total_refs}")
    lines.append("")
    lines.append("## 逐文件结果")
    lines.append("")
    lines.append("| Markdown | remote_refs | mhtml | extracted_body_images | valid_images | status |")
    lines.append("|---|---:|---|---:|---:|---|")

    detail_lines: list[str] = []
    for md_path, refs in grouped.items():
        rel = md_path.relative_to(SOURCE_ROOT)
        mhtml = matching_mhtml(md_path)
        if not mhtml.exists():
            status = "missing_mhtml"
            images: list[ExtractedImage] = []
        else:
            images = extract_body_images(mhtml)
            valid_count = sum(1 for image in images if image.valid)
            if valid_count >= len(refs):
                status = "ok"
            elif valid_count > 0:
                status = "partial_needs_review"
            else:
                status = "no_body_images"
        valid_count = sum(1 for image in images if image.valid)
        lines.append(
            f"| `{rel}` | {len(refs)} | `{mhtml.name if mhtml.exists() else ''}` | "
            f"{len(images)} | {valid_count} | {status} |"
        )

        detail_lines.extend(["", f"### `{rel}`", ""])
        for ref in refs:
            detail_lines.append(f"- line {ref.line_number}: `{ref.url}`")
        if images:
            detail_lines.append("")
            detail_lines.append("Extracted body images:")
            for idx, image in enumerate(images, start=1):
                detail_lines.append(
                    f"- image {idx}: type={image.image_type}, bytes={image.byte_size}, valid={image.valid}"
                )

    lines.extend(detail_lines)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT_PATH}")


def main() -> None:
    write_report()


if __name__ == "__main__":
    main()
