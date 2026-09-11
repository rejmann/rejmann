"""ASCII art block of the profile SVGs, rendered from ``<mode>_mode.txt``.

Only builds markup; ``build_svg.py`` assembles and writes the SVG files.
"""
ASCII_X = 15
Y_START = 30   # y of the first ASCII line, matches the opening <text> tag
LINE_HEIGHT = 8


def escape(text):
    """Normalize stray non-breaking spaces, then XML-escape text content."""
    text = text.replace(' ', ' ')
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def art_lines(art):
    lines = art.split('\n')
    if lines and lines[-1] == '':
        lines.pop()  # trailing newline in the .txt file
    return lines


def last_y(lines):
    """y of the last art row (0 when there is no art)."""
    return Y_START + (len(lines) - 1) * LINE_HEIGHT if lines else 0


def build_tspans(lines, x=ASCII_X):
    out = []
    for i, line in enumerate(lines):
        y = Y_START + i * LINE_HEIGHT
        out.append(f'<tspan x="{x}" y="{y}">{escape(line.rstrip())}</tspan>')
    return '\n'.join(out)

