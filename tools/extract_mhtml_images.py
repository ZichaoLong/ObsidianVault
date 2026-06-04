#!/usr/bin/env python3
"""Extract recoverable markdown images from same-name mhtml files."""

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
ATTACHMENT_DIR = VAULT_ROOT / "attachments" / "llm-notes"
OUT_DIR = VAULT_ROOT / "_migration"
MAP_PATH = OUT_DIR / "mhtml-image-map.md"
REMOTE_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((https://clouddocs\.huawei\.com/[^)\s]+)(?:\s+\"[^\"]*\")?\)")
IMG_DATA_RE = re.compile(
    r"<img\b[^>]*\bsrc=[\"']data:image/([^;\"']+);base64,([^\"']+)[\"']",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class MarkdownImageRef:
    markdown_path: Path
    line_number: int
    alt: str
    url: str


@dataclass
class ExtractedImage:
    image_type: str
    raw: bytes


def safe_stem(path: Path) -> str:
    name = path.stem
    name = re.sub(r"[\\/:*?\"<>|()\[\]\s]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "image"


def markdown_image_refs(path: Path) -> list[MarkdownImageRef]:
    refs: list[MarkdownImageRef] = []
    for index, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        for match in REMOTE_IMAGE_RE.finditer(line):
            refs.append(MarkdownImageRef(path, index, match.group(1), match.group(2)))
    return refs


def matching_mhtml(path: Path) -> Path:
    return SOURCE_ROOT / f"{path.stem}.mhtml"


def decoded_html_from_mhtml(path: Path) -> str:
    msg = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    parts = msg.walk() if msg.is_multipart() else [msg]
    for part in parts:
        if part.get_content_type() == "text/html":
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
        raw = base64.b64decode(payload, validate=False)
        if raw:
            images.append(ExtractedImage(image_type, raw))
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


def extension(image_type: str) -> str:
    if image_type == "jpeg":
        return "jpg"
    if image_type in {"png", "jpg", "gif", "webp", "svg"}:
        return image_type
    return "bin"


def main() -> None:
    ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "# mhtml 图片抽取映射",
        "",
        f"来源：`{SOURCE_ROOT}`",
        f"附件目录：`{ATTACHMENT_DIR.relative_to(VAULT_ROOT)}`",
        "",
        "| Markdown | line | original_url | attachment | status |",
        "|---|---:|---|---|---|",
    ]

    written = 0
    for md_path, refs in all_remote_markdown_refs().items():
        rel = md_path.relative_to(SOURCE_ROOT)
        mhtml_path = matching_mhtml(md_path)
        images = extract_body_images(mhtml_path) if mhtml_path.exists() else []
        for idx, ref in enumerate(refs, start=1):
            if idx > len(images):
                lines.append(f"| `{rel}` | {ref.line_number} | `{ref.url}` |  | missing_image |")
                continue
            image = images[idx - 1]
            filename = f"{safe_stem(md_path)}-{idx:02d}.{extension(image.image_type)}"
            out_path = ATTACHMENT_DIR / filename
            out_path.write_bytes(image.raw)
            written += 1
            attachment = out_path.relative_to(VAULT_ROOT)
            lines.append(
                f"| `{rel}` | {ref.line_number} | `{ref.url}` | `![[{attachment}]]` | ok |"
            )

    MAP_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {written} images")
    print(f"Wrote {MAP_PATH}")


if __name__ == "__main__":
    main()
