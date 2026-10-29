#!/usr/bin/env python3
"""Check local links in all tracked/staged Markdown, plus generated notes."""
import argparse
from collections import defaultdict
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

from check_artifacts import ArtifactRegistry, ROOT
from document_links import anchors, references, resolve


def check_links(root=ROOT, *, require_built=False):
    registry = ArtifactRegistry(root)
    names = subprocess.check_output(['git', 'ls-files', '-z', '--', '*.md'], cwd=root).decode().split('\0')
    names += [p for p in registry.outputs if p.endswith('.md')]
    paths = sorted({root / name for name in names if name and (root / name).is_file()})
    by_name = defaultdict(list)
    for path in paths:
        by_name[path.stem].append(path)
    errors, count = [], 0
    for source in paths:
        for number, raw, wiki in references(source.read_text()):
            location = f'{source.relative_to(root)}:{number}'
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', raw) or raw.startswith('//'):
                continue
            path, separator, anchor = raw.partition('#')
            path = unquote(path.split('?', 1)[0])
            anchor = unquote(anchor)
            destination = resolve(source, path, wiki, by_name, registry)
            count += 1
            if destination is None:
                errors.append(f'{location}: missing or ambiguous target {raw}')
            elif require_built and not destination.exists():
                errors.append(f'{location}: unbuilt target {raw}')
            elif (separator and destination.suffix == '.md' and destination.is_file()
                  and anchor not in anchors(destination)):
                errors.append(f'{location}: missing anchor {raw}')
    return errors, count, len(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-built', action='store_true', help='Also reject missing registered link targets.')
    args = parser.parse_args()
    try:
        errors, count, documents = check_links(require_built=args.require_built)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(f'LINK CHECK FAILED: {exc}', file=sys.stderr)
        return 1
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'PASS: {count} local links across {documents} tracked/generated Markdown documents')
    return 0


if __name__ == '__main__':
    sys.exit(main())
