#!/usr/bin/env python3
"""Build registered figures and HTML; add PDF/preview export with --full."""
import argparse
import importlib
from pathlib import Path
import shutil
import subprocess
import sys

from check_artifacts import ArtifactRegistry, ROOT


class BuildError(RuntimeError):
    pass


def check_dependencies(full=False):
    """Check the current Tide renderers before starting any output writes."""
    missing = []
    for module, package in [('PIL', 'Pillow'), ('cairosvg', 'CairoSVG / Cairo')]:
        try:
            importlib.import_module(module)
        except (ImportError, OSError) as exc:
            missing.append(f'{package}: {exc}')
    fonts = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuMathTeXGyre.ttf',
    ]
    if full:
        fonts.append('/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc')
        if not shutil.which('playwright-cli'):
            missing.append('playwright-cli is not on PATH')
        if not (shutil.which('google-chrome') or shutil.which('google-chrome-stable')
                or Path('/opt/google/chrome/chrome').is_file()):
            missing.append('Google Chrome is not installed')
    missing.extend(f'missing font: {font}' for font in fonts if not Path(font).is_file())
    if missing:
        instructions = [
            'Build dependencies are missing:', *[f'  - {item}' for item in missing],
            'Install Python dependencies in your active Python environment:',
            '  python3 -m pip install -r 20-tide-decentralized-neural-network/figures/requirements.txt',
            'On Debian/Ubuntu install Cairo and fonts:',
            '  sudo apt-get install libcairo2 fonts-noto-cjk fonts-dejavu-core fonts-dejavu-extra',
        ]
        if full:
            instructions += [
                'For full export also install Google Chrome, Node.js 18+ and:',
                '  sudo apt-get install fonts-noto-cjk-extra',
                '  npm install --global @playwright/cli@0.1.12',
            ]
        raise BuildError('\n'.join(instructions))


def run_build(registry, *, full=False):
    plan = registry.build_plan(full)
    for index, group in enumerate(plan, 1):
        print(f'[{index}/{len(plan)}] {group["name"]}', flush=True)
        # Use the caller's Python/virtual environment, with repository-relative
        # commands executed from the repository root even when invoked elsewhere.
        command = [sys.executable, *group['command'][1:]]
        result = subprocess.run(command, cwd=registry.root)
        if result.returncode:
            raise BuildError(f'{group["name"]} failed (exit {result.returncode}); build stopped')
        missing = [path for path in group['outputs'] if not (registry.root / path).is_file()]
        if missing:
            raise BuildError(f'{group["name"]} did not produce: '+', '.join(missing))
    errors, _ = registry.audit(require_built=True, groups=[group['name'] for group in plan])
    if errors:
        raise BuildError('\n'.join(errors))
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', action='store_true', help='Also export PDF, preview and browser report.')
    args = parser.parse_args()
    try:
        registry = ArtifactRegistry()
        errors, _ = registry.audit()
        if errors:
            raise BuildError('\n'.join(errors))
        check_dependencies(args.full)
        plan = run_build(registry, full=args.full)
        checker = ROOT / '20-tide-decentralized-neural-network/tools/check_documents.py'
        command = [sys.executable, str(checker)]
        if args.full:
            command.append('--require-built')
        subprocess.run(command, cwd=ROOT, check=True)
    except (BuildError, ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(f'BUILD FAILED: {exc}', file=sys.stderr)
        return 1
    print(f'Built and checked {len(plan)} groups / {sum(len(g["outputs"]) for g in plan)} outputs')
    return 0


if __name__ == '__main__':
    sys.exit(main())
