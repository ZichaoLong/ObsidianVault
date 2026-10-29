"""Repository-wide link checks in a source-only checkout, including Obsidian syntax."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from check_links import check_links
from document_links import anchors, references


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='vault-link-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        data = {'schema_version': 2, 'state_file': '.artifact-state.json', 'retained': [],
                'groups': [{'name': 'drawing', 'generator': 'render.py',
                            'command': ['python3', 'render.py'], 'outputs': ['out/diagram.svg']}]}
        (self.root / 'generated-artifacts.json').write_text(json.dumps(data))

    def stage(self, files):
        for name, content in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)

    def test_links_outside_tide_and_exact_missing_generated_paths(self):
        self.stage({'10-line/start.md': '[[../30-notes/target#标题]]\n![图](../out/diagram.svg)',
                    '30-notes/target.md': '# 标题\n'})
        self.assertEqual(check_links(self.root)[0], [])
        self.assertTrue(any('unbuilt target' in e for e in check_links(self.root, require_built=True)[0]))
        (self.root / '10-line/start.md').write_text('![图](../out/unregistered.svg)')
        self.assertTrue(any('missing or ambiguous target' in e for e in check_links(self.root)[0]))

    def test_table_aliases_formatted_headings_reference_links_and_blocks(self):
        self.stage({'start.md': r'[[target#A title\|读我]]' + '\n[x][ref]\n[[target#^example]]\n'
                    '[ref]: <target.md#A%20title> "reference"\n',
                    'target.md': '# [**A title**](https://example.org/wiki/A_(B))\ntext ^example\n'})
        self.assertEqual(check_links(self.root)[0], [])
        (self.root / 'start.md').write_text('[[target#does not exist]]')
        self.assertTrue(any('missing anchor' in e for e in check_links(self.root)[0]))

    def test_code_comments_and_plain_bracket_citations_are_not_links(self):
        text = '`[[example]]`\n```md\n[ghost](missing.md)\n```\n<!-- [[gone]] -->\n[定理][3,6]\n'
        self.assertEqual(list(references(text)), [])

    def test_balanced_parentheses_spaces_and_html_images(self):
        self.stage({'start.md': '[x](note(a).md#Heading)\n[y](<with space.md> "title")\n<img src="image.svg">',
                    'note(a).md': '# Heading\n', 'with space.md': '# Space\n', 'image.svg': '<svg/>'})
        self.assertEqual(check_links(self.root)[0], [])

    def test_duplicate_heading_slugs_and_ambiguous_wiki_names(self):
        self.stage({'start.md': '[x](a/note.md#same-1)\n[[note]]',
                    'a/note.md': '# Same\n## Same\n', 'b/note.md': '# Other\n'})
        errors, _, _ = check_links(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn('ambiguous target note', errors[0])
        self.assertIn('same-1', anchors(self.root / 'a/note.md'))


if __name__ == '__main__':
    unittest.main()
