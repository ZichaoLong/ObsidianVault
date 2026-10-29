#!/usr/bin/env python3
"""Check tracked sources, explicit retained artifacts, and rebuildable outputs."""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


class ArtifactRegistry:
    def __init__(self, root=ROOT):
        self.root = root.resolve()
        data = json.loads((self.root / 'generated-artifacts.json').read_text())
        if data.get('schema_version') != 2:
            raise ValueError('unsupported artifact manifest schema')
        self.state_file = self.path(data['state_file'])
        self.build_inputs = [self.path(p) for p in data.get('build_inputs', [])]
        self.asset_sources = {self.path(p) for p in data.get('asset_sources', [])}
        self.asset_directories = [self.path(p) for p in data.get('asset_directories', [])]
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
            for field in ('inputs', 'review_sources'):
                paths = group.get(field, [])
                if not isinstance(paths, list) or len(paths) != len(set(paths)):
                    raise ValueError(f'invalid {field}: {name}')
                for path in paths:
                    self.path(path)
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
        if self.state_file in self.outputs or self.state_file in self.retained:
            raise ValueError('build state must be separate from artifacts')
        sources = set(self.build_inputs) | self.asset_sources | self.generators
        for group in self.groups.values():
            sources.update(group.get('inputs', []))
            sources.update(group.get('review_sources', []))
        if sources & self.outputs.keys():
            raise ValueError('a maintained source is also a generated output')

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

    def build_plan(self, full=False, groups=None):
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

        if groups is not None and set(groups) - self.groups.keys():
            raise ValueError('unknown build group: ' + ', '.join(sorted(set(groups) - self.groups.keys())))
        for name, group in self.groups.items():
            if (name in groups if groups is not None else
                    full or group.get('build_mode', 'standard') == 'standard'):
                visit(name)
        return ordered

    def input_paths(self, name):
        group = self.groups[name]
        return sorted({group['generator'], *self.build_inputs, *group.get('inputs', [])})

    def hashes(self, paths):
        return {p: hashlib.sha256((self.root / p).read_bytes()).hexdigest()
                if (self.root / p).is_file() else None for p in sorted(paths)}

    def fingerprint(self, name):
        group = self.groups[name]
        # Review sources are human dependencies, never certification by a build.
        recipe = {k: v for k, v in group.items() if k != 'review_sources'}
        dependencies = group.get('depends_on', [])
        return {'recipe': recipe, 'inputs': self.hashes(self.input_paths(name)),
                'dependencies': {dep: self.fingerprint(dep) for dep in dependencies},
                'dependency_outputs': self.hashes(p for dep in dependencies
                                                 for p in self.groups[dep]['outputs'])}

    def read_state(self):
        path = self.root / self.state_file
        if not path.exists():
            return {}
        data = json.loads(path.read_text())
        if data.get('schema_version') != 1 or not isinstance(data.get('groups'), dict):
            raise ValueError('invalid local build state; remove only ' + self.state_file + ' and rebuild')
        if any(not isinstance(entry, dict) or not isinstance(entry.get('fingerprint'), dict)
               or not isinstance(entry.get('outputs'), dict) for entry in data['groups'].values()):
            raise ValueError('invalid group snapshot in ' + self.state_file)
        return data['groups']

    def write_state(self, state):
        path = self.root / self.state_file
        path.parent.mkdir(parents=True, exist_ok=True)
        # A failed/interrupted write cannot turn a partial snapshot into CURRENT.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump({'schema_version': 1, 'groups': state}, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
            temporary.replace(path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def invalidate(self, name):
        state = self.read_state()
        state.pop(name, None)
        self.write_state(state)

    def record_build(self, name, before):
        if before != ArtifactRegistry(self.root).fingerprint(name):
            raise ValueError(f'{name}: inputs changed during build; rebuild from stable sources')
        outputs = self.hashes(self.groups[name]['outputs'])
        if None in outputs.values():
            raise ValueError(f'{name}: cannot record missing outputs')
        state = self.read_state()
        state[name] = {'fingerprint': before, 'outputs': outputs}
        self.write_state(state)

    def states(self):
        saved, result = self.read_state(), {}
        for group in self.build_plan(full=True):
            name = group['name']
            outputs = self.hashes(group['outputs'])
            if None in outputs.values():
                status, reason = 'MISSING', 'one or more outputs are absent'
            elif name not in saved:
                status, reason = 'UNVERIFIED', 'no successful unified build snapshot'
            elif saved[name].get('fingerprint') != self.fingerprint(name):
                status, reason = 'STALE', 'inputs, recipe or dependency outputs changed'
            elif saved[name].get('outputs') != outputs:
                status, reason = 'STALE', 'output content changed after build'
            elif any(result[dep][0] != 'CURRENT' for dep in group.get('depends_on', [])):
                status, reason = 'STALE', 'an upstream build is not current'
            else:
                status, reason = 'CURRENT', 'matches recorded sources and outputs'
            result[name] = (status, reason)
        return result

    def affected(self, paths):
        paths = {self.path(p.rstrip('/')) for p in paths}
        def matches(candidates):
            return any(p == source or source.startswith(p + '/')
                       for p in paths for source in candidates)
        result = {}
        for group in self.build_plan(full=True):
            name = group['name']
            reasons = []
            if matches(self.input_paths(name)) or 'generated-artifacts.json' in paths:
                reasons.append('REBUILD: direct input or build recipe changed')
            if matches(group.get('review_sources', [])):
                reasons.append('REVIEW: compare definitions/examples with maintained content')
            if any(dep in result for dep in group.get('depends_on', [])):
                reasons.append('DOWNSTREAM: update after the affected upstream group')
            if reasons:
                result[name] = reasons
        return result

    def catalog_errors(self):
        errors = []
        for group in self.groups.values():
            catalog = group.get('catalog')
            if not catalog:
                continue
            expected = set(catalog.get('extra_outputs', []))
            if catalog['kind'] == 'svg-pptx':
                path = self.root / self.path(catalog['path'])
                names = json.loads(path.read_text())['sources']
                if len(names) != len(set(names)):
                    errors.append('duplicate sources in ' + catalog['path'])
                for name in names:
                    source = self.path((path.parent.relative_to(self.root) / name).as_posix())
                    if source not in self.asset_sources or source not in self.input_paths(group['name']):
                        errors.append('catalog source is not registered: ' + source)
                    suffixes = {'.svg': ['.png'], '.pptx': ['.svg', '.png', '.pdf']}
                    for suffix in suffixes[Path(source).suffix]:
                        expected.add(str(Path(source).with_suffix(suffix)))
            elif catalog['kind'] == 'tide-decorators':
                # Parse registration names without importing render dependencies in CI.
                names = []
                for source in catalog['paths']:
                    if source not in self.input_paths(group['name']):
                        errors.append('catalog module is not a build input: ' + source)
                    tree = ast.parse((self.root / self.path(source)).read_text())
                    for node in ast.walk(tree):
                        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                                and node.func.id == 'register'):
                            names.append(ast.literal_eval(node.args[0]))
                if len(names) != len(set(names)):
                    errors.append('duplicate Tide figure names')
                for name in names:
                    for suffix in ('.svg', '.png'):
                        expected.add(self.path(catalog['directory'] + '/' + name + suffix))
            else:
                raise ValueError('unknown catalog kind: ' + catalog['kind'])
            if expected != set(group['outputs']):
                errors.append(f'catalog/output mismatch in {group["name"]}: '
                              + ', '.join(sorted(expected ^ set(group['outputs']))))
        return errors

    def audit(self, require_built=False, *, groups=None):
        errors = []
        required_groups = set(self.groups) if groups is None else set(groups)
        if required_groups - self.groups.keys():
            raise ValueError('unknown groups in artifact audit')
        tracked = set(subprocess.check_output(
            ['git', 'ls-files', '-z'], cwd=self.root).decode().rstrip('\0').split('\0'))
        names = set(self.outputs) | set(self.retained) | {self.state_file}
        ignored_result = subprocess.run(
            ['git', 'check-ignore', '--no-index', '-z', '--stdin'], cwd=self.root,
            input='\0'.join(sorted(names))+'\0', capture_output=True, text=True)
        if ignored_result.returncode not in (0, 1):
            raise ValueError(ignored_result.stderr.strip())
        ignored = set(ignored_result.stdout.rstrip('\0').split('\0'))
        if self.state_file in tracked or self.state_file not in ignored:
            errors.append('local build state must be ignored and untracked: ' + self.state_file)
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
        sources = self.asset_sources | set(self.build_inputs)
        for name, group in self.groups.items():
            sources.update(self.input_paths(name))
            sources.update(group.get('review_sources', []))
        for path in sorted(sources):
            if path not in tracked or not (self.root / path).is_file():
                errors.append('maintained source is missing or untracked: ' + path)
        for path in sorted(self.retained):
            if path not in tracked or not (self.root / path).is_file():
                errors.append(f'retained artifact is missing or untracked: {path}')
            if path in ignored:
                errors.append(f'retained artifact must not be ignored: {path}')
        for path in sorted(tracked):
            if {'__pycache__', '.playwright-cli'} & set(Path(path).parts):
                errors.append(f'cache or browser scratch file is tracked: {path}')
        media = {'.svg', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.pdf', '.pptx', '.html'}
        candidates = {p for p in tracked if Path(p).suffix.lower() in media}
        # Include ignored leftovers inside known asset areas; never delete them.
        for directory in self.asset_directories:
            candidates.update(p.relative_to(self.root).as_posix()
                              for p in (self.root / directory).rglob('*')
                              if p.is_file() and p.suffix.lower() in media | {'.json'})
        for path in sorted(candidates - self.outputs.keys() - self.retained.keys() - self.asset_sources):
            errors.append('unclassified asset (register source, output or retained file): ' + path)
        errors.extend(self.catalog_errors())
        if require_built:
            for name, (status, reason) in self.states().items():
                if name in required_groups and status not in ('CURRENT', 'MISSING'):
                    errors.append(f'{name}: {status}: {reason}')
        return errors, missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-built', action='store_true',
                        help='Require all outputs to exist and match successful build snapshots.')
    parser.add_argument('--group', action='append', help='Scope --require-built to a group (repeatable).')
    parser.add_argument('--affected', nargs='+', default=[], help='Repository-relative changed paths or directories.')
    parser.add_argument('--changed-from', help='Compare tracked working files with this Git commit.')
    args = parser.parse_args()
    try:
        registry = ArtifactRegistry()
        errors, missing = registry.audit(args.require_built, groups=args.group)
        states = registry.states()
        changed = list(args.affected)
        if args.changed_from:
            revision = subprocess.check_output(['git', 'rev-parse', '--verify', '--end-of-options',
                                               args.changed_from + '^{commit}'], cwd=ROOT, text=True).strip()
            changed += subprocess.check_output(['git', 'diff', '--no-renames', '--name-only', '-z',
                                                revision, '--'], cwd=ROOT).decode().rstrip('\0').split('\0')
            changed = [p for p in changed if p]
        affected = registry.affected(changed) if changed else {}
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(f'artifact manifest: {exc}', file=sys.stderr)
        return 1
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'PASS: {len(registry.outputs)} registered outputs; '
          f'{len(registry.retained)} retained records; tracking and ignore rules match')
    print(f'{"PENDING" if missing else "PASS"}: {len(missing)} outputs await local build')
    for name, (status, reason) in states.items():
        print(f'{status}: {name}: {reason}')
    if changed:
        for name, reasons in affected.items():
            print(f'{name}: ' + '; '.join(reasons))
            print(f'  python3 tools/build.py --group {name}')
        if not affected:
            print('No registered build dependencies affected; consult the maintenance map for document updates.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
