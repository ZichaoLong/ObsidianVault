"""Check native PPTX semantics and geometry without installing render fonts."""
from html import escape
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from pptx_svg import Box, Diagram, NS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from assets.render import check_vector

SVG_NS = {'s': 'http://www.w3.org/2000/svg'}


def measure_stub(text, size, color='#000000', **style):
    # Only glyph metrics are replaced. Real font/layout rendering is exercised
    # by the full-build job; these tests run in source-only, stdlib-only CI.
    if not text:
        return Box()
    return Box(f'<text font-size="{size}" fill="{color}">{escape(text)}</text>',
               len(text) * size * .5, -size * .8, size * .2)


class PptxSvgTests(unittest.TestCase):
    def setUp(self):
        self.metrics = patch('pptx_svg.text_box', side_effect=measure_stub)
        self.metrics.start()
        self.addCleanup(self.metrics.stop)

    def diagram(self, name='gpt-diagram'):
        return Diagram(ROOT / 'assets/fig' / (name + '.pptx'))

    def test_every_formula_and_connector_survives_without_raster_fallback(self):
        for name in ('gpt-diagram', 'rnn-diagram', 'sequence-parallel-rnn-diagram'):
            with self.subTest(name=name):
                diagram = self.diagram(name)
                svg, report = diagram.render()
                check_vector(svg, diagram, report)
                self.assertEqual(report['formulas'], len(diagram.slide.findall('.//m:oMath', NS)))
                self.assertEqual(report['connectors'], len(diagram.slide.findall('.//p:cxnSp', NS)))
                self.assertNotIn('<image', svg)
                self.assertEqual((svg, report), diagram.render())

    def test_validator_detects_missing_formula(self):
        diagram = self.diagram()
        svg, report = diagram.render()
        root = ET.fromstring(svg)
        formula = root.find('.//s:g[@data-office-math]', SVG_NS)
        formula.attrib.pop('data-office-math')
        with self.assertRaisesRegex(ValueError, 'lost or duplicated'):
            check_vector(ET.tostring(root), diagram, report)

    def test_validator_detects_changed_formula_text(self):
        diagram = self.diagram()
        svg, report = diagram.render()
        root = ET.fromstring(svg)
        root.find('.//s:text[@data-office-run]', SVG_NS).text = 'changed'
        with self.assertRaisesRegex(ValueError, 'text changed'):
            check_vector(ET.tostring(root), diagram, report)

    def test_equation_paragraph_keeps_multiple_lines(self):
        diagram = self.diagram('sequence-parallel-rnn-diagram')
        svg, _ = diagram.render()
        root = ET.fromstring(svg)
        expected = [len(p.findall('m:oMath', NS)) for p in diagram.slide.findall('.//m:oMathPara', NS)
                    if len(p.findall('m:oMath', NS)) > 1]
        actual = [int(p.get('data-equation-lines')) for p in root.findall('.//s:g[@data-equation-lines]', SVG_NS)
                  if int(p.get('data-equation-lines')) > 1]
        self.assertEqual(actual, expected)
        block = root.find('.//s:g[@data-equation-lines="2"]', SVG_NS)
        self.assertIsNotNone(block)
        # The second displayed equation is translated vertically, not appended
        # horizontally to the first equation and shrunk to fit one line.
        self.assertRegex(list(block)[1].get('transform'), r'^translate\(0 [1-9]')

    def test_new_math_structure_fails_instead_of_disappearing(self):
        diagram = self.diagram()
        formula = diagram.slide.find('.//m:oMath', NS)
        ET.SubElement(formula, f'{{{NS["m"]}}}f')
        with self.assertRaisesRegex(ValueError, 'unsupported Office Math object: f'):
            diagram.render()

    def test_image_fill_is_not_silently_omitted(self):
        diagram = self.diagram()
        props = diagram.slide.find('.//mc:Choice/p:sp/p:spPr', NS)
        ET.SubElement(props, f'{{{NS["a"]}}}blipFill')
        with self.assertRaisesRegex(ValueError, 'unsupported shape property: blipFill'):
            diagram.render()

    def test_curve_uses_drawingml_control_points(self):
        diagram = self.diagram()
        shape = ET.fromstring(f'''<p:cxnSp xmlns:p="{NS['p']}" xmlns:a="{NS['a']}">
          <p:nvCxnSpPr><p:cNvPr id="1" name="curve"/></p:nvCxnSpPr>
          <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="1270000" cy="2540000"/></a:xfrm>
          <a:prstGeom prst="curvedConnector3"><a:avLst><a:gd name="adj1" fmla="val 50000"/></a:avLst></a:prstGeom>
          <a:ln w="12700"/></p:spPr></p:cxnSp>''')
        group = ET.fromstring(diagram.shape(shape))
        self.assertEqual(group.find('.//path').get('d'),
                         'M0 0 C25 0 50 50 50 100 C50 150 75 200 100 200')

    def test_group_resize_does_not_stretch_glyphs(self):
        diagram = self.diagram()
        shape = ET.fromstring(f'''<p:sp xmlns:p="{NS['p']}" xmlns:a="{NS['a']}">
          <p:nvSpPr><p:cNvPr id="1" name="label"/></p:nvSpPr>
          <p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="1270000" cy="1270000"/></a:xfrm>
          <a:prstGeom prst="rect"/></p:spPr>
          <p:txBody><a:bodyPr/><a:p><a:r><a:rPr sz="1400"/><a:t>Label</a:t></a:r></a:p></p:txBody></p:sp>''')
        with patch.object(diagram, 'body', return_value='<text>Label</text>') as body:
            svg = diagram.shape(shape, scale_x=2, scale_y=3)
        body.assert_called_once_with(shape, 200, 300)
        self.assertIn('scale(0.5 0.33333)', svg)


if __name__ == '__main__':
    unittest.main()
