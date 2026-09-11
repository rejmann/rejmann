#!/usr/bin/env python3
"""Build ``dark_mode.svg`` and ``light_mode.svg`` from scratch.

The SVGs are build output: every run deletes them and writes new ones, so no
hand edit or leftover from an older layout survives (and a merge conflict in
them is resolved by simply running this again). Sources:

    panel.yaml       -> info panel on the right + each theme's colors (`themes:`)
    <mode>_mode.txt  -> ASCII art on the left

The canvas grows by one column-width per panel column beyond ``BASE_COLS`` and
never shrinks below the original 985x530 design.

Usage:
    python3 cli/build_svg.py
"""
import math
import os

import yaml

from ascii_to_svg import ASCII_X, Y_START as ASCII_Y, art_lines, build_tspans, last_y
from panel_to_svg import BASE_COLS, PANEL_X, Y_START as PANEL_Y, build_panel, effective_cols

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YAML_PATH = os.path.join(ROOT, 'panel.yaml')

# The stock canvas is 985x530 and was drawn for a 60-column panel that starts at
# x=390 with a ~15px right margin -> one panel column is ~9.667px wide.
BASE_CANVAS_W = 985
BASE_CANVAS_H = 530
CHAR_W = (BASE_CANVAS_W - PANEL_X - 15) / BASE_COLS
PANEL_BOTTOM_PAD = 20    # 510 (last row) + 20 == 530
ASCII_BOTTOM_PAD = 36    # 494 (last art row) + 36 == 530

THEME_KEYS = ('background', 'text', 'key', 'value', 'addColor', 'delColor', 'cc')

TEMPLATE = """<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="{width}px" height="{height}px" font-size="16px">
<style>
@font-face {{
src: local('Consolas'), local('Consolas Bold');
font-family: 'ConsolasFallback';
font-display: swap;
-webkit-size-adjust: 109%;
size-adjust: 109%;
}}
.key {{fill: {key};}}
.value {{fill: {value};}}
.addColor {{fill: {addColor};}}
.delColor {{fill: {delColor};}}
.cc {{fill: {cc};}}
.ascii {{font-size: 6px;}}
text, tspan {{white-space: pre;}}
</style>
<rect width="{width}px" height="{height}px" fill="{background}" rx="15"/>
<text x="{ascii_x}" y="{ascii_y}" fill="{text}" class="ascii">
{ascii}
</text>
<text x="{panel_x}" y="{panel_y}" fill="{text}">
{panel}
</text>
</svg>
"""


def render_svg(mode, theme, panel, panel_last_y, canvas_w):
    missing = [k for k in THEME_KEYS if k not in theme]
    if missing:
        raise SystemExit(f'error: themes.{mode} in panel.yaml is missing: {", ".join(missing)}')

    with open(os.path.join(ROOT, f'{mode}_mode.txt'), encoding='utf-8') as f:
        art = art_lines(f.read())

    canvas_h = max(BASE_CANVAS_H, panel_last_y + PANEL_BOTTOM_PAD, last_y(art) + ASCII_BOTTOM_PAD)
    svg = TEMPLATE.format(
        width=canvas_w, height=canvas_h,
        ascii_x=ASCII_X, ascii_y=ASCII_Y, ascii=build_tspans(art),
        panel_x=PANEL_X, panel_y=PANEL_Y, panel=panel,
        **{k: theme[k] for k in THEME_KEYS},
    )
    return svg, canvas_h


def main():
    with open(YAML_PATH, encoding='utf-8') as f:
        doc = yaml.safe_load(f)
    themes = doc.get('themes') or {}
    if not themes:
        raise SystemExit(f'error: no `themes:` in {YAML_PATH}')

    cols = effective_cols(doc)
    panel, panel_last_y = build_panel(doc, cols)
    canvas_w = max(BASE_CANVAS_W, math.ceil(BASE_CANVAS_W + (cols - BASE_COLS) * CHAR_W))

    # render everything before touching the disk: a failure halfway must not
    # leave the SVGs deleted (CI would commit the deletion)
    outputs = {mode: render_svg(mode, theme, panel, panel_last_y, canvas_w) for mode, theme in themes.items()}

    for mode, (svg, canvas_h) in outputs.items():
        path = os.path.join(ROOT, f'{mode}_mode.svg')
        if os.path.exists(path):
            os.remove(path)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(svg)
        print(f'ok: {mode}_mode.svg recreated ({canvas_w}x{canvas_h}, {cols} cols)')


if __name__ == '__main__':
    main()
