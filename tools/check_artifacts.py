#!/usr/bin/env python3
"""Check tracked sources, explicit retained artifacts, and rebuildable outputs."""
import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


class ArtifactRegistry:
    def __init__(self, root=ROOT):
        self.root = root.resolve()
        data = json.loads((self.root / 'generated-artifacts.json').read_text())
        if data.get('schema_version') != 1:
            raise ValueError('unsupported artifact manifest schema')
        self.outputs = {}
        self.groups = {}
        self.directories = set()
        self.generators = set()
        self.retained = {}
        for group in data['groups']:
            name = group['name']
            if not isinstance(name, str) or not name or name in self.groups:
                raise ValueError(f'invalid or duplicate build group: {name}')
            if group.get('build_mode', 'standard') not in ('standard', 'full'):
                raise ValueError(f'invalid build mode: {name}')
            dependencies = group.get('depends_on', [])
            if (not isinstance(dependencies, list)
                    or any(not isinstance(item, str) for item in dependencies)):
                raise ValueError(f'invalid build dependencies: {name}')
            generator = self.path(group['generator'])
            command = group['command']
            if (not isinstance(command, list) or len(command) < 2
                    or any(not isinstance(arg, str) or not arg for arg in command)
                    or command[0] not in ('python', 'python3')
                    or command[1] != generator):
                raise ValueError(f'invalid command for {group["name"]}')
            self.groups[name] = group
            self.generators.add(generator)
            for item in group['outputs']:
                path = self.path(item)
                if path in self.outputs:
                    raise ValueError(f'duplicate generated path: {path}')
                self.outputs[path] = group['name']
            self.directories.update(self.path(path) for path in group.get('directories', []))
        for name, group in self.groups.items():
            for dependency in group.get('depends_on', []):
                if dependency not in self.groups:
                    raise ValueError(f'unknown build dependency: {name} -> {dependency}')
                if (group.get('build_mode', 'standard') == 'standard'
                        and self.groups[dependency].get('build_mode', 'standard') == 'full'):
                    raise ValueError(f'standard group depends on full-only group: {name}')
        self.build_plan(full=True)  # Reject cycles even during source-only CI checks.
        for item in data['retained']:
            path = self.path(item['path'])
            if path in self.retained or not item.get('reason', '').strip():
                raise ValueError(f'invalid retained artifact: {path}')
            self.retained[path] = item['reason']
        for directory in self.directories:
            if not any(path.startswith(directory + '/') for path in self.outputs):
                raise ValueError(f'output directory has no registered files: {directory}')

    def path(self, value):
        if not isinstance(value, str) or not value:
            raise ValueError('artifact paths must be nonempty strings')
        path = PurePosixPath(value)
        if (path.is_absolute() or '..' in path.parts or path.as_posix() != value
                or any(char in value for char in '*?[]\\\n\r\0')
                or not (self.root / value).resolve().is_relative_to(self.root)):
            raise ValueError(f'expected an exact repository-relative path: {value}')
        return value

    def recognizes(self, path):
        try:
            name = path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return False
        return name in self.outputs or name in self.directories

    def build_plan(self, full=False):
        ordered, visited, visiting = [], set(), set()

        def visit(name):
            if name in visiting:
                raise ValueError(f'cyclic build dependency at {name}')
            if name in visited:
                return
            visiting.add(name)
            group = self.groups[name]
            for dependency in group.get('depends_on', []):
                visit(dependency)
            visiting.remove(name)
            visited.add(name)
            ordered.append(group)

        for name, group in self.groups.items():
            if full or group.get('build_mode', 'standard') == 'standard':
                visit(name)
        return ordered

    def audit(self, require_built=False, *, groups=None):
        errors = []
        required_groups = set(self.groups) if groups is None else set(groups)
        if required_groups - self.groups.keys():
            raise ValueError('unknown groups in artifact audit')
        tracked = set(subprocess.check_output(
            ['git', 'ls-files', '-z'], cwd=self.root).decode().rstrip('\0').split('\0'))
        names = set(self.outputs) | set(self.retained)
        ignored_result = subprocess.run(
            ['git', 'check-ignore', '--no-index', '-z', '--stdin'], cwd=self.root,
            input='\0'.join(sorted(names))+'\0', capture_output=True, text=True)
        if ignored_result.returncode not in (0, 1):
            raise ValueError(ignored_result.stderr.strip())
        ignored = set(ignored_result.stdout.rstrip('\0').split('\0'))
        missing = []
        for path in sorted(self.outputs):
            if path not in self.retained:
                if path in tracked:
                    errors.append(f'generated output is tracked: {path}')
                if path not in ignored:
                    errors.append(f'generated output is not ignored: {path}')
            target = self.root / path
            if not target.is_file():
                missing.append(path)
                if ((require_built and self.outputs[path] in required_groups)
                        or path in self.retained or target.exists()):
                    errors.append(f'generated output is missing or not a file: {path}')
        for path in sorted(self.generators):
            if path not in tracked or not (self.root / path).is_file():
                errors.append(f'generator must be a tracked source file: {path}')
        for path in sorted(self.retained):
            if path not in tracked or not (self.root / path).is_file():
                errors.append(f'retained artifact is missing or untracked: {path}')
            if path in ignored:
                errors.append(f'retained artifact must not be ignored: {path}')
        for path in sorted(tracked):
            if {'__pycache__', '.playwright-cli'} & set(Path(path).parts):
                errors.append(f'cache or browser scratch file is tracked: {path}')
        return errors, missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-built', action='store_true',
                        help='Require every registered output after a complete build.')
    args = parser.parse_args()
    try:
        registry = ArtifactRegistry()
        errors, missing = registry.audit(args.require_built)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f'artifact manifest: {exc}', file=sys.stderr)
        return 1
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'PASS: {len(registry.outputs)} registered outputs; '
          f'{len(registry.retained)} retained records; tracking and ignore rules match')
    print(f'{"PENDING" if missing else "PASS"}: {len(missing)} outputs await local build')
    return 0


if __name__ == '__main__':
    sys.exit(main())
