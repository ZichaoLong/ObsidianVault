"""Shared local Markdown/Obsidian link handling; no rendering dependencies."""
from collections import defaultdict
from functools import lru_cache
from html import unescape
from pathlib import Path
import re


def prose_lines(text):
    fence = None
    for number, line in enumerate(text.splitlines(), 1):
        match = re.match(r'^\s*(?:>\s*)?(`{3,}|~{3,})', line)
        if match:
            marker = match[1]
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            yield number, ''
        else:
            yield number, line if fence is None else ''


def slug(heading):
    heading = re.sub(r'<[^>]+>', '', heading).strip().lower()
    heading = re.sub(r'[^\w\s-]', '', heading)
    return re.sub(r'\s', '-', heading)


def heading_text(heading):
    heading = re.sub(r'\[([^\]]+)\]\((?:[^()]|\([^()]*\))*\)', r'\1', heading)
    heading = re.sub(r'<[^>]+>', '', heading)
    return unescape(re.sub(r'[*`]', '', heading))


@lru_cache(maxsize=None)
def anchors(path):
    result, seen = set(), defaultdict(int)
    for _, line in prose_lines(path.read_text()):
        result.update(re.findall(r'<a\s+id=["\']([^"\']+)["\']', line))
        result.update('^' + value for value in re.findall(r'\^([\w-]+)\s*$', line))
        match = re.match(r'^(?:>\s*)?#{1,6}\s+(.+?)\s*#*$', line)
        if match:
            heading = match[1]
            result.add(heading)
            heading = heading_text(heading)
            result.add(heading)
            key = slug(heading)
            result.add(key + (f'-{seen[key]}' if seen[key] else ''))
            seen[key] += 1
    return result


def link_target(value):
    """Strip an optional Markdown title while preserving <paths with spaces>."""
    value = value.strip()
    if value.startswith('<'):
        return value[1:value.index('>')] if '>' in value else value
    return value.split()[0] if value else ''


def references(text):
    text = re.sub(r'<!--[\s\S]*?-->', lambda m: '\n' * m[0].count('\n'), text)
    lines = [(n, re.sub(r'(`+).*?\1', '', line)) for n, line in prose_lines(text)]
    definitions = {}
    for _, line in lines:
        match = re.match(r'^\s*\[([^\]]+)\]:\s*(.+)', line)
        if match:
            definitions[' '.join(match[1].lower().split())] = link_target(match[2])
    for number, line in lines:
        if re.match(r'^\s*\[[^\]]+\]:', line):
            continue
        for match in re.finditer(r'\[\[([^\]\n]+)\]\]', line):
            yield number, re.split(r'\\?\|', match[1], maxsplit=1)[0], True
        line = re.sub(r'\[\[[^\]\n]+\]\]', '', line)
        # Balanced parentheses in destinations, including filenames and URLs.
        used = []
        for match in re.finditer(r'!?\[[^\]\n]*\]\(', line):
            start = match.end()
            depth, pos = 1, start
            while pos < len(line) and depth:
                if line[pos] == '\\':
                    pos += 2
                    continue
                if line[pos] == '(':
                    depth += 1
                elif line[pos] == ')':
                    depth -= 1
                pos += 1
            if depth == 0:
                yield number, link_target(line[start:pos-1]).replace(r'\(', '(').replace(r'\)', ')'), False
                used.append((match.start(), pos))
        for start, end in reversed(used):
            line = line[:start] + ' ' * (end-start) + line[end:]
        for match in re.finditer(r'!?\[([^\]\n]+)\](?:\[([^\]\n]*)\])?', line):
            key = ' '.join((match[2] or match[1]).lower().split())
            if key in definitions:
                yield number, definitions[key], False
        for match in re.finditer(r'<(?:a|img)\b[^>]*?\b(?:href|src)=["\']([^"\']+)["\']', line):
            yield number, unescape(match[1]), False


def resolve(source, target, wiki, by_name, registry):
    if not target:
        return source
    relative = Path(target)
    if relative.is_absolute():
        candidates = [registry.root / target.lstrip('/')]
    else:
        candidates = [source.parent / relative]
        if wiki:
            candidates.append(registry.root / relative)
    if wiki and relative.suffix != '.md':
        candidates += [path.with_suffix('.md') for path in candidates]
    for path in candidates:
        path = path.resolve()
        if path.is_relative_to(registry.root) and (path.exists() or registry.recognizes(path)):
            return path
    if wiki and '/' not in target and len(by_name[relative.stem]) == 1:
        return by_name[relative.stem][0]
    return None
