#!/usr/bin/env python3
"""Render manual SVGs to PNG and native PPTX diagrams to SVG/PNG/PDF."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
from pptx_svg import Diagram, NS, MATH_FONT, SANS_FONT, CJK_FONT

SVG_NS = {'s': 'http://www.w3.org/2000/svg'}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_vector(svg, diagram=None, report=None):
    root = ET.fromstring(svg)
    for element in root.iter():
        if element.tag.rsplit('}', 1)[-1] in ('image', 'foreignObject', 'script'):
            raise ValueError('expected a standalone vector drawing without raster images or scripts')
    if diagram is not None:
        rendered = root.findall('.//s:g[@data-office-math]', SVG_NS)
        original = diagram.slide.findall('.//m:oMath', NS)
        expected = Counter(hashlib.sha256(ET.tostring(item)).hexdigest() for item in original)
        if Counter(item.get('data-office-math') for item in rendered) != expected:
            raise ValueError('Office Math objects were lost or duplicated')
        by_hash = {item['sha256']: item for item in report['formula_sources']}
        for item in rendered:
            actual = Counter(''.join(text.itertext()) for text in
                             item.findall('.//s:text[@data-office-run]', SVG_NS))
            expected_runs = Counter(run for run in by_hash[item.get('data-office-math')]['runs'] if run)
            if actual != expected_runs:
                raise ValueError('Office Math text changed during export')
    return root


def build(output_dir=HERE):
    import cairosvg
    import PIL
    output_dir = Path(output_dir).resolve()
    report = {'sources': {}, 'rendering': {'Pillow': PIL.__version__, 'CairoSVG': cairosvg.__version__,
              'fonts': {path.name: sha256(path) for path in (MATH_FONT, SANS_FONT, CJK_FONT)}}}
    for name in json.loads((HERE / 'catalog.json').read_text())['sources']:
        source = (HERE / name).resolve()
        if not source.is_relative_to(HERE) or source.suffix not in ('.svg', '.pptx'):
            raise ValueError(f'invalid asset source: {name}')
        destination = output_dir / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix == '.svg':
            svg = source.read_text()
            check_vector(svg)
            entry = {'sha256': sha256(source), 'kind': 'manual SVG'}
            outputs = [destination.with_suffix('.png')]
        else:
            diagram = Diagram(source)
            svg, entry = diagram.render()
            check_vector(svg, diagram, entry)
            target = destination.with_suffix('.svg')
            target.write_text(svg)
            cairosvg.svg2pdf(bytestring=svg.encode(), write_to=str(destination.with_suffix('.pdf')))
            outputs = [target, destination.with_suffix('.png'), destination.with_suffix('.pdf')]
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(destination.with_suffix('.png')))
        entry['outputs'] = {str(path.relative_to(output_dir)): sha256(path) for path in outputs}
        report['sources'][name] = entry
        print(f'Rendered {name}', flush=True)
    (output_dir / 'render-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=HERE,
                        help='Preview outputs elsewhere; relative images/ and fig/ paths are preserved.')
    args = parser.parse_args()
    try:
        report = build(args.output_dir)
    except (ValueError, OSError, KeyError) as exc:
        print(f'ASSET BUILD FAILED: {exc}', file=sys.stderr)
        return 1
    print(f'Checked {len(report["sources"])} editable sources; all SVGs use native text and geometry')
    return 0


if __name__ == '__main__':
    sys.exit(main())
