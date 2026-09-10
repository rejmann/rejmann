#!/usr/bin/env python3
"""Rebuild the shared info panel of both profile SVGs from ``panel.yaml``.

Rewrites the right-hand ``<text x="390" …>`` block of ``dark_mode.svg`` and
``light_mode.svg`` (the ASCII art on the left and each file's own colors are left
untouched) and, when a value no longer fits, widens the canvas so nothing is
clipped. Rows carrying an ``id`` keep their ``id`` / ``id_dots`` hooks so
``today.py`` can still inject the live GitHub numbers in CI.

Alignment: every content line is padded with a dot leader to ``eff`` columns,
where ``eff`` is ``width:`` from the YAML or, if some line is longer than that,
the length of that longest line (with a minimum dot run). The canvas grows by
one column-width per extra column; it never shrinks below the original design.

Usage:
    python3 cli/panel_to_svg.py
"""
import math
import os
import re

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YAML_PATH = os.path.join(ROOT, 'panel.yaml')
SVGS = ('dark_mode.svg', 'light_mode.svg')

PANEL_X = 390
Y_START = 30
LINE_HEIGHT = 20
MIN_DOTS = 4
FIXED_CHARS = 5          # ". " + ":" + the two spaces around the dot leader

# The stock canvas is 985x530 and was drawn for a 60-column panel that starts at
# x=390 with a ~15px right margin -> one panel column is ~9.667px wide.
BASE_CANVAS_W = 985
BASE_CANVAS_H = 530
BASE_COLS = 60
CHAR_W = (BASE_CANVAS_W - PANEL_X - 15) / BASE_COLS
PANEL_BOTTOM_PAD = 20    # 510 (last row) + 20 == 530
ASCII_BOTTOM_PAD = 36    # 494 (last art row) + 36 == 530

# Opening tag (kept verbatim, so each theme keeps its fill), body, closing tag.
PANEL_BLOCK = re.compile(r'(<text x="390"[^>]*>\n).*?(\n</text>)', re.DOTALL)
ASCII_BLOCK = re.compile(r'<text\b[^>]*\bclass="ascii"[^>]*>.*?</text>', re.DOTALL)


def esc(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def key_markup(key):
    """"Languages.Programming" -> two <tspan class="key"> joined by a literal dot."""
    return '.'.join(f'<tspan class="key">{esc(part)}</tspan>' for part in str(key).split('.'))


def is_content(row):
    return isinstance(row, dict) and 'key' in row and 'raw' not in row and not row.get('spacer')


def content_len(row):
    return FIXED_CHARS + len(str(row['key'])) + len(str(row.get('value', '')))


def divider_line(y, prefix, cols):
    """`<tspan …>prefix</tspan> -———…-—-` — dashes are bare text after the tspan."""
    dashes = max(3, cols - len(prefix) - 5)   # ' -' (2) + '-—-' (3)
    return f'<tspan x="{PANEL_X}" y="{y}">{esc(prefix)}</tspan> -' + '—' * dashes + '-—-'


def content_row(row, cols):
    key, value = str(row['key']), str(row.get('value', ''))
    vid = row.get('id')
    dots = max(MIN_DOTS, cols - content_len(row))
    dots_attr = f' id="{vid}_dots"' if vid else ''
    value_attr = f' id="{vid}"' if vid else ''
    return (
        f'{key_markup(key)}:'
        f'<tspan class="cc"{dots_attr}> {"." * dots} </tspan>'
        f'<tspan class="value"{value_attr}>{esc(value)}</tspan>'
    )


def effective_cols(doc):
    """Target columns, stretched to fit the longest line if one overflows."""
    cols = int(doc.get('width', BASE_COLS))
    cols = max(cols, len(str(doc['header'])) + 8)
    for section in doc.get('sections', []):
        if section.get('title'):
            cols = max(cols, len(f"- {section['title']}") + 8)
        for row in section.get('rows', []):
            if is_content(row):
                cols = max(cols, content_len(row) + MIN_DOTS)
    return cols


def build_panel(doc, cols):
    y = Y_START
    lines = [divider_line(y, str(doc['header']), cols)]
    for section in doc.get('sections', []):
        if section.get('title'):
            y += 2 * LINE_HEIGHT   # one blank slot before a titled section
            lines.append(divider_line(y, f"- {section['title']}", cols))
        for row in section.get('rows', []):
            y += LINE_HEIGHT
            prefix = f'<tspan x="{PANEL_X}" y="{y}" class="cc">. </tspan>'
            if row == 'spacer' or (isinstance(row, dict) and row.get('spacer')):
                lines.append(prefix)
            elif isinstance(row, dict) and 'raw' in row:
                lines.append(prefix + row['raw'])
            else:
                lines.append(prefix + content_row(row, cols))
    return '\n'.join(lines), y


def ascii_max_y(svg):
    block = ASCII_BLOCK.search(svg)
    ys = [int(n) for n in re.findall(r'y="(\d+)"', block.group(0))] if block else []
    return max(ys) if ys else 0


def set_dim(svg, tag, attr, value):
    return re.sub(rf'(<{tag}\b[^>]*\b{attr}=")\d+(px")', rf'\g<1>{value}\g<2>', svg, count=1)


def main():
    with open(YAML_PATH, encoding='utf-8') as f:
        doc = yaml.safe_load(f)

    cols = effective_cols(doc)
    body, last_y = build_panel(doc, cols)
    canvas_w = max(BASE_CANVAS_W, math.ceil(BASE_CANVAS_W + (cols - BASE_COLS) * CHAR_W))

    for name in SVGS:
        path = os.path.join(ROOT, name)
        with open(path, encoding='utf-8') as f:
            svg = f.read()
        match = PANEL_BLOCK.search(svg)
        if not match:
            raise SystemExit(f'error: no <text x="390" …> block found in {path}')

        canvas_h = max(BASE_CANVAS_H, last_y + PANEL_BOTTOM_PAD, ascii_max_y(svg) + ASCII_BOTTOM_PAD)
        new_svg = svg[:match.start()] + match.group(1) + body + match.group(2) + svg[match.end():]
        for tag in ('svg', 'rect'):
            new_svg = set_dim(new_svg, tag, 'width', canvas_w)
            new_svg = set_dim(new_svg, tag, 'height', canvas_h)

        state = 'already up to date'
        if new_svg != svg:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_svg)
            state = f'updated ({canvas_w}x{canvas_h}, {cols} cols)'
        print(f'ok: {name} {state} from panel.yaml')


if __name__ == '__main__':
    main()
