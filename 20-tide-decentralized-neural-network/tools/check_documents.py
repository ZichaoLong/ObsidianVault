#!/usr/bin/env python3
"""Check Tide document links, local formulas, and the canonical boundary.

Run from any directory with Python 3.10 or later. This checks repository
structure and notation; mathematical claims still require their proofs.
Canonical hashes record the reviewed edition. An intentional canonical edit
requires a reviewed diff, a revision record, and an explicit hash update.
"""

from collections import defaultdict
from functools import lru_cache
import hashlib
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote


BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
CANONICAL_HASHES = {
    "settlegraph-learning-note.md":
        "631bb877a197c2d5179b0fa17d4a74d2a294ed9e492278f4f040bb0b1925e362",
    "timed-dag-region-selector-learning-note.md":
        "5a9157fb8f76219d1aaa91a1dc9ed1c1bfc1902f4966e5e03ddee0abf2b24866",
    "positive-delay-graph-finite-cut-learning-note.md":
        "800f7e488fb29cac3d007ea439e639053c6953534f1a554fd11cba34bd72d111",
    "timed-dag-chunk-prefill-learning-note.md":
        "1e23307163ab28e9d74311215bf19a2be66763290198a94d13559d261997430a",
}
REMOVED_ENTRIES = {
    "semantics-anchor",
    "weighted-kv-sparse-activation-example",
    "weighted-kv-layered-example",
}


def prose_lines(text):
    """Keep original line numbers while excluding fenced examples."""
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r"^\s*(?:>\s*)?(`{3,}|~{3,})", line)
        if match:
            marker = match[1]
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            yield number, ""
        else:
            yield number, line if fence is None else ""


def slug(heading):
    heading = re.sub(r"<[^>]+>", "", heading).strip().lower()
    heading = re.sub(r"[^\w\s-]", "", heading)
    return re.sub(r"\s", "-", heading)


@lru_cache(maxsize=None)
def anchors(path):
    text = path.read_text()
    result = set()
    seen = defaultdict(int)
    for _, line in prose_lines(text):
        result.update(re.findall(r'<a\s+id=["\']([^"\']+)["\']', line))
        result.update("^" + value for value in re.findall(r"\^([\w-]+)\s*$", line))
        match = re.match(r"^(?:>\s*)?#{1,6}\s+(.+?)\s*#*$", line)
        if match:
            heading = match[1]
            result.add(heading)  # Obsidian heading links
            key = slug(heading)
            result.add(key + (f"-{seen[key]}" if seen[key] else ""))
            seen[key] += 1
    return result


def references(text):
    for number, line in prose_lines(text):
        for match in re.finditer(r"\[\[([^\]\n]+)\]\]", line):
            yield number, match[1].split("|", 1)[0], True
        for match in re.finditer(r"!?\[[^\]\n]+\]\(([^)\n]+)\)", line):
            yield number, match[1], False


def resolve(source, target, wiki, by_name):
    if not target:
        return source
    relative = Path(target)
    candidates = [source.parent / relative, ROOT / relative]
    if wiki and relative.suffix != ".md":
        candidates += [path.with_suffix(".md") for path in candidates]
    for path in candidates:
        if path.exists():
            return path.resolve()
    if wiki and "/" not in target and len(by_name[relative.stem]) == 1:
        return by_name[relative.stem][0]
    return None


def check_formulas(path, errors):
    """Check local numbered equations and TeX grouping, not their semantics."""
    text = "\n".join(line for _, line in prose_lines(path.read_text()))
    tags = [int(value) for value in re.findall(r"\\tag\{(\d+)\}", text)]
    if tags != list(range(1, len(tags) + 1)):
        errors.append(f"{path.relative_to(ROOT)}: equation tags are not consecutive")
    for number, line in prose_lines(text):
        for value in re.findall(r"式\s*\((\d+)\)", line):
            if int(value) not in tags:
                errors.append(f"{path.relative_to(ROOT)}:{number}: missing equation {value}")
    for match in re.finditer(r"\$\$[\s\S]*?\$\$|\$(?!\$)[^\n$]*\$", text):
        formula = match[0]
        level = 0
        for brace in re.finditer(r"(?<!\\)[{}]", formula):
            level += 1 if brace[0] == "{" else -1
            if level < 0:
                break
        if level != 0:
            number = text.count("\n", 0, match.start()) + 1
            errors.append(f"{path.relative_to(ROOT)}:{number}: unbalanced TeX braces")


def main():
    errors = []
    # Include new documents before staging, while respecting the repository's ignores.
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "*.md"],
        cwd=ROOT,
    ).decode().split("\0")
    paths = sorted({(ROOT / name).resolve() for name in names if name
                    and (ROOT / name).is_file()
                    and not any(part in {".playwright-cli", "appendices"}
                                for part in Path(name).parts)})
    by_name = defaultdict(list)
    for path in paths:
        by_name[path.stem].append(path)
    canonical = {BASE / name for name in CANONICAL_HASHES}
    for name, expected in CANONICAL_HASHES.items():
        path = BASE / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(f"{path.relative_to(ROOT)}: canonical edition changed; review the diff")
    for name in REMOVED_ENTRIES:
        if (BASE / f"{name}.md").exists():
            errors.append(f"{name}.md: obsolete redirect entry has returned")

    links = 0
    inbound = 0
    for source in paths:
        text = source.read_text()
        inside = source.is_relative_to(BASE)
        if inside and any(ord(char) < 32 and char not in "\n\t\r" for char in text):
            errors.append(f"{source.relative_to(ROOT)}: unexpected control character")
        for number, raw, wiki in references(text):
            target = unquote(raw.strip().strip("<>"))
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("//"):
                continue
            path, separator, anchor = target.partition("#")
            destination = resolve(source, path, wiki, by_name)
            concerns_tide = (inside or BASE.name in path or Path(path).stem in REMOVED_ENTRIES
                             or destination is not None and destination.is_relative_to(BASE))
            if not concerns_tide:
                continue
            links += 1
            inbound += not inside
            location = f"{source.relative_to(ROOT)}:{number}"
            if destination is None:
                errors.append(f"{location}: missing target {raw}")
            elif separator and destination.suffix == ".md" and anchor not in anchors(destination):
                errors.append(f"{location}: missing anchor {raw}")
            if source in canonical and destination not in canonical:
                errors.append(f"{location}: canonical textbook refers to downstream material: {raw}")

    local_notes = sorted((BASE / "local-semantics" / "weighted-message").glob("*.md"))
    for path in local_notes:
        check_formulas(path, errors)
    for path in BASE.rglob("*"):
        if path.is_dir() and not any(path.iterdir()):
            errors.append(f"{path.relative_to(ROOT)}: empty directory")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    documents = sum(path.is_relative_to(BASE) for path in paths)
    print("PASS: four canonical editions match; canonical local references stay within the four textbooks")
    print(f"PASS: {links} local Markdown/wiki links ({inbound} incoming) across {documents} Tide documents")
    print(f"PASS: numbered equations and TeX grouping in {len(local_notes)} local textbooks; no empty directories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
