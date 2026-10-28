"""Exercise builds in fresh repositories without rendering dependencies."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from build import BuildError, check_dependencies, run_build
from check_artifacts import ArtifactRegistry


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='artifact-build-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)

    def registry(self, *, changes=None, scripts=None):
        # Deliberately declare export first: dependencies determine execution.
        groups = [
            {'name': 'export', 'build_mode': 'full', 'depends_on': ['html'],
             'generator': 'export.py', 'command': ['python3', 'export.py'],
             'outputs': ['out/export.txt']},
            {'name': 'html', 'generator': 'html.py',
             'command': ['python3', 'html.py'], 'outputs': ['out/html.txt']},
        ]
        if changes:
            changes(groups)
        data = {'schema_version': 1, 'groups': groups, 'retained': []}
        (self.root / 'generated-artifacts.json').write_text(json.dumps(data))
        (self.root / '.gitignore').write_text('/out/html.txt\n/out/export.txt\n')
        sources = {
            'html.py': (
                'from pathlib import Path\nimport sys\n'
                'assert Path("generated-artifacts.json").is_file()\n'
                'Path("out").mkdir(exist_ok=True)\n'
                'Path("out/html.txt").write_text(sys.executable)\n'
            ),
            'export.py': (
                'from pathlib import Path\n'
                'assert Path("out/html.txt").is_file()\n'
                'Path("out/export.txt").write_text("exported")\n'
            ),
        }
        sources.update(scripts or {})
        for name, source in sources.items():
            (self.root / name).write_text(source)
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
        return ArtifactRegistry(self.root)

    def build(self, registry, *, full=False):
        with contextlib.redirect_stdout(io.StringIO()):
            return run_build(registry, full=full)

    def test_standard_build_leaves_export_optional(self):
        registry = self.registry()
        self.assertEqual(registry.audit()[0], [])
        plan = self.build(registry)
        self.assertEqual([group['name'] for group in plan], ['html'])
        self.assertEqual((self.root / 'out/html.txt').read_text(), sys.executable)
        self.assertFalse((self.root / 'out/export.txt').exists())
        self.assertEqual(registry.audit(True, groups=['html'])[0], [])
        self.assertEqual(registry.audit(True)[0], [
            'generated output is missing or not a file: out/export.txt'])

    def test_full_build_orders_dependencies_and_leaves_sources_clean(self):
        registry = self.registry()
        plan = self.build(registry, full=True)
        self.assertEqual([group['name'] for group in plan], ['html', 'export'])
        self.assertEqual((self.root / 'out/export.txt').read_text(), 'exported')
        self.assertEqual(registry.audit(True), ([], []))
        subprocess.run(['git', 'diff', '--exit-code'], cwd=self.root, check=True)
        self.assertEqual(subprocess.check_output(
            ['git', 'ls-files', '--others', '--exclude-standard'], cwd=self.root), b'')

    def test_cycle_is_rejected_before_build(self):
        def cycle(groups):
            groups[0]['build_mode'] = 'standard'
            groups[1]['depends_on'] = ['export']
        with self.assertRaisesRegex(ValueError, 'cyclic build dependency'):
            self.registry(changes=cycle)
        self.assertFalse((self.root / 'out').exists())

    def test_unknown_dependency_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unknown build dependency'):
            self.registry(changes=lambda groups: groups[0].update(depends_on=['missing']))

    def test_standard_group_cannot_require_full_only_group(self):
        with self.assertRaisesRegex(ValueError, 'standard group depends on full-only'):
            self.registry(changes=lambda groups: groups[1].update(depends_on=['export']))

    def test_generator_failure_stops_dependent_export(self):
        registry = self.registry(scripts={'html.py': 'raise SystemExit(7)\n'})
        with self.assertRaisesRegex(BuildError, r'html failed \(exit 7\)'):
            self.build(registry, full=True)
        self.assertFalse((self.root / 'out/export.txt').exists())

    def test_success_without_declared_output_is_failure(self):
        registry = self.registry(scripts={'html.py': 'pass\n'})
        with self.assertRaisesRegex(BuildError, 'html did not produce: out/html.txt'):
            self.build(registry, full=True)
        self.assertFalse((self.root / 'out/export.txt').exists())

    def test_scoped_audit_still_detects_tracking_errors_elsewhere(self):
        registry = self.registry()
        self.build(registry)
        (self.root / 'out/export.txt').write_text('accidentally tracked')
        subprocess.run(['git', 'add', '-f', 'out/export.txt'], cwd=self.root, check=True)
        self.assertIn('generated output is tracked: out/export.txt',
                      registry.audit(True, groups=['html'])[0])


class DependencyTests(unittest.TestCase):
    @patch('build.importlib.import_module')
    @patch('build.Path.is_file', return_value=True)
    @patch('build.shutil.which', return_value=None)
    def test_standard_build_does_not_require_browser(self, which, is_file, import_module):
        check_dependencies()
        which.assert_not_called()

    @patch('build.importlib.import_module', side_effect=ImportError('not installed'))
    @patch('build.Path.is_file', return_value=False)
    @patch('build.shutil.which', return_value=None)
    def test_missing_dependencies_explain_installation(self, which, is_file, import_module):
        with self.assertRaises(BuildError) as caught:
            check_dependencies(full=True)
        message = str(caught.exception)
        for required in ('Pillow', 'CairoSVG', 'missing font', 'Google Chrome',
                         'pip install -r', 'fonts-noto-cjk-extra', '@playwright/cli@0.1.12'):
            self.assertIn(required, message)


if __name__ == '__main__':
    unittest.main()
