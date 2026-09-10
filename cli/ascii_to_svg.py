#!/usr/bin/env python3
"""Regenerate the ASCII art block inside the profile SVGs.

Reads ``<mode>_mode.txt`` and rewrites only the ``<text class="ascii">`` block of
``<mode>_mode.svg``. The stats panel on the right (the elements filled in by
``today.py``) is left untouched.

Usage:
    python3 cli/ascii_to_svg.py            # regenerate dark and light
    python3 cli/ascii_to_svg.py dark       # regenerate a single mode
    python3 cli/ascii_to_svg.py dark light
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODES = ('dark', 'light')

Y_START = 30   # y of the first ASCII line, matches the opening <text> tag
LINE_HEIGHT = 8

# Matches the whole ASCII block: opening tag (kept as-is), body, closing tag.
ASCII_BLOCK = re.compile(
    r'(<text\b[^>]*\bclass="ascii"[^>]*>\n).*?(\n</text>)',
    re.DOTALL,
)


def escape(text):
    """Normalize stray non-breaking spaces, then XML-escape text content."""
    text = text.replace(' ', ' ')
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def build_tspans(art, x):
    lines = art.split('\n')
    if lines and lines[-1] == '':
        lines.pop()  # trailing newline in the .txt file
    out = []
    for i, line in enumerate(lines):
        y = Y_START + i * LINE_HEIGHT
        out.append(f'<tspan x="{x}" y="{y}">{escape(line.rstrip())}</tspan>')
    return '\n'.join(out)


def regenerate(mode):
    txt_path = os.path.join(ROOT, f'{mode}_mode.txt')
    svg_path = os.path.join(ROOT, f'{mode}_mode.svg')

    with open(txt_path, 'r', encoding='utf-8') as f:
        art = f.read()
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg = f.read()

    match = ASCII_BLOCK.search(svg)
    if not match:
        raise SystemExit(f'error: no <text class="ascii"> block found in {svg_path}')

    x_match = re.search(r'\bx="([^"]+)"', match.group(1))
    x = x_match.group(1) if x_match else '15'

    new_svg = svg[:match.start()] + match.group(1) + build_tspans(art, x) + match.group(2) + svg[match.end():]

    if new_svg != svg:
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(new_svg)
        print(f'ok: {mode}_mode.svg updated from {mode}_mode.txt')
    else:
        print(f'ok: {mode}_mode.svg already up to date')


def main(argv):
    modes = argv[1:] or list(MODES)
    unknown = [m for m in modes if m not in MODES]
    if unknown:
        raise SystemExit(f'error: unknown mode(s): {", ".join(unknown)} (use: {", ".join(MODES)})')
    for mode in modes:
        regenerate(mode)


if __name__ == '__main__':
    main(sys.argv)
