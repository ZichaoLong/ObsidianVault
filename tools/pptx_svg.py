"""Export the DrawingML/Office Math subset used by assets/fig/*.pptx.

Read native shapes, group transforms, connector geometry and Office Math.
Do not use the raster fallback branch of mc:AlternateContent. Unsupported
objects fail explicitly so an edited presentation cannot silently lose content.
This is a small exporter for these diagrams, not a general PowerPoint renderer.
"""
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from pathlib import Path
import hashlib
import json
import math
import unicodedata
import xml.etree.ElementTree as ET
from zipfile import ZipFile


NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
}
MATH_FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuMathTeXGyre.ttf')
SANS_FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
CJK_FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
EMU = 12700  # DrawingML units per point; keep geometry and font sizes in points.


def tag(element):
    return element.tag.rsplit('}', 1)[-1]


def find(element, path):
    return element.find(path, NS) if element is not None else None


def val(element, name, default=None):
    return element.get(name, default) if element is not None else default


def number(value):
    return f'{value:.5f}'.rstrip('0').rstrip('.') or '0'


def native_children(element):
    """Choose editable Office Math objects exactly once, never fallback PNGs."""
    for child in element:
        if tag(child) == 'AlternateContent':
            choices = child.findall('mc:Choice', NS)
            if len(choices) != 1 or choices[0].get('Requires') != 'a14':
                raise ValueError('unsupported AlternateContent choice')
            yield from native_children(choices[0])
        else:
            yield child


@dataclass
class Box:
    svg: str = ''
    width: float = 0
    top: float = 0
    bottom: float = 0


def moved(box, x=0, y=0):
    return (f'<g transform="translate({number(x)} {number(y)})">'
            f'{box.svg}</g>')


def row(boxes):
    boxes = list(boxes)
    x, parts = 0, []
    for box in boxes:
        parts.append(moved(box, x))
        x += box.width
    return Box(''.join(parts), x, min((b.top for b in boxes), default=0),
               max((b.bottom for b in boxes), default=0))


def stack(boxes, gap):
    """Office Math paragraphs contain one displayed equation per oMath."""
    boxes = list(boxes)
    if not boxes:
        return Box()
    parts, y = [boxes[0].svg], 0
    for previous, current in zip(boxes, boxes[1:]):
        y += previous.bottom - current.top + gap
        parts.append(moved(current, y=y))
    return Box(''.join(parts), max(b.width for b in boxes), boxes[0].top,
               y + boxes[-1].bottom)


@lru_cache(maxsize=None)
def font(path, bold=False, italic=False):
    from PIL import ImageFont
    if path == SANS_FONT and (bold or italic):
        suffix = ('Bold' if bold else '') + ('Oblique' if italic else '')
        path = path.with_name(f'DejaVuSans-{suffix}.ttf')
    return ImageFont.truetype(str(path), 256, index=2 if path == CJK_FONT else 0)


def text_box(text, size, color='#000000', *, math_font=False, bold=False,
             italic=False, underline=False):
    if not text:
        return Box()
    cjk = any('\u2e80' <= char <= '\u9fff' for char in text)
    path = CJK_FONT if cjk else MATH_FONT if math_font else SANS_FONT
    family = 'Noto Sans CJK SC' if cjk else 'DejaVu Math TeX Gyre' if math_font else 'DejaVu Sans'
    face = font(path, bold, italic)
    _, top, _, bottom = face.getbbox(text, anchor='ls')
    factor = size / 256
    decoration = ' text-decoration="underline"' if underline else ''
    svg = (f'<text xml:space="preserve" font-family="{family}" font-size="{number(size)}" '
           f'fill="{color}" font-weight="{"bold" if bold else "normal"}" '
           f'font-style="{"italic" if italic else "normal"}"'
           f'{decoration}>'
           f'{escape(text)}</text>')
    return Box(svg, face.getlength(text) * factor, top * factor, bottom * factor)


class Diagram:
    def __init__(self, path):
        self.path = Path(path)
        with ZipFile(path) as archive:
            slides = [n for n in archive.namelist()
                      if n.startswith('ppt/slides/slide') and n.endswith('.xml')]
            if slides != ['ppt/slides/slide1.xml']:
                raise ValueError('expected a single-slide diagram')
            self.slide = ET.fromstring(archive.read(slides[0]))
            self.size = ET.fromstring(archive.read('ppt/presentation.xml')).find('p:sldSz', NS)
            theme = ET.fromstring(archive.read('ppt/theme/theme1.xml'))
        self.colors = {}
        for entry in theme.find('.//a:clrScheme', NS):
            color = list(entry)[0]
            self.colors[tag(entry)] = color.get('lastClr', color.get('val'))
        self.colors.update({key: self.colors[target] for key, target in
                            {'bg1': 'lt1', 'bg2': 'lt2', 'tx1': 'dk1', 'tx2': 'dk2'}.items()})
        self.line_styles = list(theme.find('.//a:lnStyleLst', NS))
        self.counts = {'shapes': 0, 'connectors': 0, 'groups': 0, 'formulas': 0}
        self.formulas = []

    def color(self, properties, default='#000000'):
        fill = find(properties, 'a:solidFill')
        if fill is None:
            return default
        color = list(fill)[0]
        kind = tag(color)
        raw = color.get('val')
        if kind == 'schemeClr':
            raw = self.colors[raw]
        elif kind == 'sysClr':
            raw = color.get('lastClr')
        elif kind == 'prstClr':
            raw = {'black': '000000', 'white': 'FFFFFF'}[raw]
        elif kind != 'srgbClr':
            raise ValueError(f'unsupported color: {kind}')
        rgb = [int(raw[i:i+2], 16) / 255 for i in (0, 2, 4)]
        for change in color:
            amount = int(change.get('val')) / 100000
            if tag(change) == 'lumMod':
                rgb = [c * amount for c in rgb]
            elif tag(change) == 'lumOff':
                rgb = [c + amount for c in rgb]
            elif tag(change) == 'tint':
                rgb = [c * amount + 1 - amount for c in rgb]
            else:
                raise ValueError(f'unsupported color adjustment: {tag(change)}')
        return '#' + ''.join(f'{round(min(1, max(0, c)) * 255):02x}' for c in rgb)

    def math_box(self, element, size, color='#000000'):
        kind = tag(element)
        if kind == 'r':
            properties = find(element, 'a:rPr')
            text = ''.join(n.text or '' for n in element.findall('m:t', NS))
            style = val(find(element, 'm:rPr/m:sty'), f'{{{NS["m"]}}}val')
            italic = style in ('i', 'bi') or (style != 'p' and val(properties, 'i') == '1')
            # Mathematical alphanumeric Unicode already encodes its own style.
            italic = italic and any(c.isascii() and c.isalpha() for c in text)
            bold = style in ('b', 'bi') or val(properties, 'b') == '1'
            if any('MATHEMATICAL BOLD' in unicodedata.name(c, '') for c in text):
                bold = False  # The Unicode glyph already carries the bold style.
            box = text_box(text, size, self.color(properties, color), math_font=True,
                           italic=italic, bold=bold)
            box.svg = box.svg.replace('<text ', '<text data-office-run="true" ', 1)
            return box
        if kind in ('sSup', 'sSub', 'sSubSup'):
            color = self.color(find(element, f'm:{kind}Pr/m:ctrlPr/a:rPr'), color)
            base = self.math_box(find(element, 'm:e'), size, color)
            parts, right, top, bottom = [base.svg], 0, base.top, base.bottom
            for name, offset in [('sup', -.56 * size), ('sub', .32 * size)]:
                child = find(element, f'm:{name}')
                if child is None:
                    continue
                script = self.math_box(child, size * .7, color)
                parts.append(moved(script, base.width + size * .04, offset))
                right = max(right, script.width + size * .04)
                top, bottom = min(top, script.top + offset), max(bottom, script.bottom + offset)
            return Box(''.join(parts), base.width + right, top, bottom)
        if kind == 'd':
            color = self.color(find(element, 'm:dPr/m:ctrlPr/a:rPr'), color)
            contents = element.findall('m:e', NS)
            if len(contents) != 1:
                raise ValueError('unsupported multi-column delimiter')
            content = self.math_box(contents[0], size, color)
            delimiters = []
            for name, default in [('begChr', '('), ('endChr', ')')]:
                char = val(find(element, f'm:dPr/m:{name}'), f'{{{NS["m"]}}}val', default)
                box = text_box(char, size, color, math_font=True)
                if box.bottom > box.top and content.bottom - content.top > box.bottom - box.top:
                    sy = (content.bottom - content.top) / (box.bottom - box.top)
                    dy = content.top - box.top * sy
                    box = Box(f'<g transform="translate(0 {number(dy)}) scale(1 {number(sy)})">{box.svg}</g>',
                              box.width, content.top, content.bottom)
                delimiters.append(box)
            return row([delimiters[0], content, delimiters[1]])
        if kind in ('oMath', 'e', 'sup', 'sub'):
            return row(self.math_box(child, size, color) for child in element
                       if not tag(child).endswith('Pr'))
        raise ValueError(f'unsupported Office Math object: {kind}')

    def body(self, element, width, height):
        body = find(element, 'p:txBody')
        if body is None:
            return ''
        props = find(body, 'a:bodyPr')
        if val(props, 'vert', 'horz') != 'horz' or int(val(props, 'rot', '0')) != 0:
            raise ValueError('unsupported text rotation')
        left, right, top, bottom = [int(val(props, name, default)) / EMU for name, default in
                                   [('lIns', '91440'), ('rIns', '91440'), ('tIns', '45720'), ('bIns', '45720')]]
        available_w, available_h = width - left - right, height - top - bottom
        lines = []
        for paragraph in body.findall('a:p', NS):
            default = find(paragraph, 'a:endParaRPr')
            size = int(val(default, 'sz', '1800')) / 100
            chunks = []
            for child in paragraph:
                kind = tag(child)
                if kind in ('pPr', 'endParaRPr'):
                    continue
                if kind == 'r':
                    style = find(child, 'a:rPr')
                    chunks.append(text_box(find(child, 'a:t').text or '',
                                           int(val(style, 'sz', size * 100)) / 100,
                                           self.color(style), bold=val(style, 'b') == '1',
                                           italic=val(style, 'i') == '1',
                                           underline=val(style, 'u', 'none') != 'none'))
                elif kind == 'm':
                    formulas = child.findall('.//m:oMath', NS)
                    displayed = []
                    for formula in formulas:
                        math_size = int(val(find(formula, './/a:rPr'), 'sz', size * 100)) / 100
                        box = self.math_box(formula, math_size)
                        digest = hashlib.sha256(ET.tostring(formula)).hexdigest()
                        self.counts['formulas'] += 1
                        self.formulas.append({'sha256': digest,
                                              'runs': [''.join(n.text or '' for n in run.findall('m:t', NS))
                                                       for run in formula.findall('.//m:r', NS)]})
                        box.svg = f'<g data-office-math="{digest}">{box.svg}</g>'
                        displayed.append(box)
                    block = stack(displayed, size * .25)
                    block.svg = f'<g data-equation-lines="{len(displayed)}">{block.svg}</g>'
                    chunks.append(block)
                else:
                    raise ValueError(f'unsupported paragraph object: {kind}')
            line = row(chunks)
            if line.svg:
                lines.append((line, val(find(paragraph, 'a:pPr'), 'algn', 'l')))
        if not lines:
            return ''
        gap = 2
        total_height = sum(b.bottom - b.top for b, _ in lines) + gap * (len(lines) - 1)
        scale = min(1, available_w / max(b.width for b, _ in lines), available_h / total_height)
        if scale <= 0:
            raise ValueError('text box has no usable area')
        y = top
        anchor = val(props, 'anchor', 't')
        if anchor == 'ctr':
            y += (available_h - total_height * scale) / 2
        elif anchor == 'b':
            y += available_h - total_height * scale
        fragments = []
        for box, align in lines:
            x = left
            if align == 'ctr':
                x += (available_w - box.width * scale) / 2
            elif align == 'r':
                x += available_w - box.width * scale
            fragments.append(f'<g transform="translate({number(x)} {number(y - box.top * scale)}) scale({number(scale)})">{box.svg}</g>')
            y += (box.bottom - box.top + gap) * scale
        return ''.join(fragments)

    def line_style(self, element):
        style = find(element, 'p:spPr/a:ln')
        if style is not None and find(style, 'a:noFill') is not None:
            return None
        reference = find(element, 'p:style/a:lnRef')
        index = int(val(reference, 'idx', '0'))
        inherited = self.line_styles[index - 1] if index else None
        if style is None and inherited is None:
            return None
        width = int(val(style, 'w', val(inherited, 'w', '6350'))) / EMU
        color = self.color(style, '#000000')
        dash = val(find(style, 'a:prstDash'), 'val', 'solid')
        dash_values = {'solid': '', 'dash': '4 3', 'dashDot': '4 3 1 3'}[dash]
        attrs = f'fill="none" stroke="{color}" stroke-width="{number(width)}"'
        if dash_values:
            attrs += ' stroke-dasharray="' + ' '.join(number(float(n) * width) for n in dash_values.split()) + '"'
        return style, width, color, attrs

    def shape(self, element, scale_x=1, scale_y=1):
        kind = tag(element)
        self.counts['connectors' if kind == 'cxnSp' else 'shapes'] += 1
        props = find(element, 'p:spPr')
        for unsupported in ('blipFill', 'gradFill', 'pattFill', 'custGeom'):
            if find(props, 'a:' + unsupported) is not None:
                raise ValueError(f'unsupported shape property: {unsupported}')
        transform = find(props, 'a:xfrm')
        if transform is None or int(transform.get('rot', '0')):
            raise ValueError('missing transform or unsupported shape rotation')
        off, ext = find(transform, 'a:off'), find(transform, 'a:ext')
        x, y, w, h = [int(e.get(k)) / EMU for e, k in [(off, 'x'), (off, 'y'), (ext, 'cx'), (ext, 'cy')]]
        preset = find(props, 'a:prstGeom')
        geometry = val(preset, 'prst')
        line = self.line_style(element)
        stroke = line[3] if line else 'fill="none" stroke="none"'
        fill = self.color(props, 'none')
        parts = []
        if geometry in ('rect', 'roundRect'):
            radius = 0
            if geometry == 'roundRect':
                adjust = find(preset, 'a:avLst/a:gd')
                amount = float(val(adjust, 'fmla', 'val 16667').split()[-1]) / 100000
                radius = min(w, h) * min(.5, max(0, amount))
            attributes = stroke.replace('fill="none"', f'fill="{fill}"')
            parts.append(f'<rect width="{number(w)}" height="{number(h)}" rx="{number(radius)}" {attributes}/>')
            # Group resizing changes text-box geometry, but stored font sizes
            # remain in slide points. Lay text out in the transformed box and
            # cancel ancestor scaling so glyphs do not stretch with the group.
            body = self.body(element, w * scale_x, h * scale_y)
            parts.append(f'<g transform="scale({number(1 / scale_x)} {number(1 / scale_y)})">{body}</g>')
        elif geometry in ('straightConnector1', 'curvedConnector3'):
            if not line:
                raise ValueError('connector has no line style')
            sx = -1 if transform.get('flipH') == '1' else 1
            sy = -1 if transform.get('flipV') == '1' else 1
            coords = f'translate({number(w if sx < 0 else 0)} {number(h if sy < 0 else 0)}) scale({sx} {sy})'
            if geometry == 'straightConnector1':
                path = f'M0 0 L{number(w)} {number(h)}'
                angle = math.atan2(h, w)
                start_angle = angle + math.pi
            else:
                adjust = find(preset, 'a:avLst/a:gd')
                a = float(val(adjust, 'fmla', 'val 50000').split()[-1]) / 100000
                # DrawingML curvedConnector3 uses two cubic Bezier segments.
                mid = w * a
                path = (f'M0 0 C{number(mid / 2)} 0 {number(mid)} {number(h / 4)} {number(mid)} {number(h / 2)} '
                        f'C{number(mid)} {number(h * 3 / 4)} {number((mid + w) / 2)} {number(h)} {number(w)} {number(h)}')
                angle, start_angle = 0, math.pi
            drawing = f'<path d="{path}" {stroke}/>'
            if val(line[0], 'cmpd') == 'dbl':
                drawing += f'<path d="{path}" fill="none" stroke="white" stroke-width="{number(line[1] / 3)}"/>'
            for end_name, px, py, direction in [('tailEnd', w, h, angle), ('headEnd', 0, 0, start_angle)]:
                end = find(line[0], f'a:{end_name}')
                if end is not None and end.get('type', 'none') != 'none':
                    if end.get('type') not in ('triangle', 'arrow'):
                        raise ValueError('unsupported arrowhead')
                    length = line[1] * {'sm': 3, 'med': 5, 'lg': 7}[end.get('len', 'med')]
                    half = line[1] * {'sm': 1.5, 'med': 2.5, 'lg': 3.5}[end.get('w', 'med')]
                    if end.get('type') == 'triangle':
                        arrow_path = f'M0 0 L-{number(length)} -{number(half)} L-{number(length)} {number(half)} Z'
                        arrow_style = f'fill="{line[2]}"'
                    else:
                        arrow_path = f'M-{number(length)} -{number(half)} L0 0 L-{number(length)} {number(half)}'
                        arrow_style = f'fill="none" stroke="{line[2]}" stroke-width="{number(line[1])}"'
                    drawing += (f'<path transform="translate({number(px)} {number(py)}) rotate({number(math.degrees(direction))})" '
                                f'd="{arrow_path}" {arrow_style}/>')
            parts.append(f'<g transform="{coords}">{drawing}</g>')
        else:
            raise ValueError(f'unsupported geometry: {geometry}')
        identity = find(element, './/p:cNvPr')
        return (f'<g id="shape-{identity.get("id")}" transform="translate({number(x)} {number(y)})">'
                f'<title>{escape(identity.get("name"))}</title>{"".join(parts)}</g>')

    def children(self, element, scale_x=1, scale_y=1):
        parts = []
        for child in native_children(element):
            kind = tag(child)
            if kind in ('nvGrpSpPr', 'grpSpPr', 'extLst'):
                continue
            if kind in ('sp', 'cxnSp'):
                parts.append(self.shape(child, scale_x, scale_y))
            elif kind == 'grpSp':
                self.counts['groups'] += 1
                t = find(child, 'p:grpSpPr/a:xfrm')
                if t is None or int(t.get('rot', '0')) or t.get('flipH') or t.get('flipV'):
                    raise ValueError('unsupported group transform')
                off, ext, old_off, old_ext = [find(t, 'a:' + name) for name in ('off', 'ext', 'chOff', 'chExt')]
                sx, sy = int(ext.get('cx')) / int(old_ext.get('cx')), int(ext.get('cy')) / int(old_ext.get('cy'))
                x = (int(off.get('x')) - int(old_off.get('x')) * sx) / EMU
                y = (int(off.get('y')) - int(old_off.get('y')) * sy) / EMU
                parts.append(f'<g transform="translate({number(x)} {number(y)}) scale({number(sx)} {number(sy)})">{self.children(child, scale_x * sx, scale_y * sy)}</g>')
            else:
                raise ValueError(f'unsupported slide object: {kind}')
        return ''.join(parts)

    def render(self):
        self.counts = dict.fromkeys(self.counts, 0)
        self.formulas = []
        content = self.children(find(self.slide, 'p:cSld/p:spTree'))
        width, height = int(self.size.get('cx')) / EMU, int(self.size.get('cy')) / EMU
        report = {'source': self.path.name, 'sha256': hashlib.sha256(self.path.read_bytes()).hexdigest(),
                  **self.counts, 'formula_sources': self.formulas}
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{round(width * 4 / 3)}" height="{round(height * 4 / 3)}" '
               f'viewBox="0 0 {number(width)} {number(height)}">'
               f'<title>{escape(self.path.stem)}</title>'
               '<desc>Generated from native PowerPoint shapes and Office Math; edit the PPTX source.</desc>'
               f'<metadata>{escape(json.dumps(report, ensure_ascii=False))}</metadata>'
               f'<rect width="100%" height="100%" fill="white"/>{content}</svg>\n')
        return svg, report
