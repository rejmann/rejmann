"""Info panel of the profile SVGs (right-hand side), rendered from ``panel.yaml``.

Only builds markup; ``build_svg.py`` assembles and writes the SVG files. Rows
carrying an ``id`` keep their ``id`` / ``id_dots`` hooks on the <tspan>s.

Alignment: every content line — and every stats row with a ``{Label:field}`` —
is padded with a dot leader to ``eff`` columns, where ``eff`` is ``width:`` from
the YAML or, if some line is longer than that, the length of that longest line
(with a minimum dot run).
"""
import html
import re

PANEL_X = 390
Y_START = 30
LINE_HEIGHT = 20
MIN_DOTS = 4
PREFIX = '. '            # start of every row inside a section
FIXED_CHARS = 5          # ". " + ":" + the two spaces around the dot leader
BASE_COLS = 60
FLEX = '\x00'            # stands in for a stats row's stretchy dot leader while it's measured


def esc(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def key_markup(key):
    """"Languages.Programming" -> two <tspan class="key"> joined by a literal dot."""
    return '.'.join(f'<tspan class="key">{esc(part)}</tspan>' for part in str(key).split('.'))


def is_content(row):
    return isinstance(row, dict) and 'key' in row and 'raw' not in row and not row.get('spacer')


def strip_tags(text):
    return re.sub(r'<[^>]+>', '', text)


def visible_len(markup):
    """Columns the markup takes once rendered (tags dropped, entities decoded)."""
    return len(html.unescape(strip_tags(markup)))


def stats_dots(length, value):
    """Fixed-width dot leader of a bare {field}: pads `value` out to `length`
    columns, declared per field as `length:` in panel.yaml (0 / absent -> none).
    """
    just = max(0, length - len(value))
    if just <= 2:
        return {0: '', 1: ' ', 2: '. '}[just]
    return ' ' + '.' * just + ' '


def dots_attr(fid, spec):
    dots_class = spec.get('dots_class', 'cc')
    return (f' class="{dots_class}"' if dots_class else '') + f' id="{fid}_dots"'


def value_markup(fid, spec):
    """A today.py-driven value plus its optional prefix and suffix, all in the
    field's class."""
    cls = spec.get('class', 'value')

    def affix(name):
        return f'<tspan class="{cls}">{esc(str(spec[name]))}</tspan>' if spec.get(name) else ''

    value = f'<tspan class="{cls}" id="{fid}">{esc(str(spec.get("value", "0")))}</tspan>'
    return affix('prefix') + value + affix('suffix')


def field_markup(fid, spec):
    """A bare {field}: fixed-width dot leader (if the field declares dots) + value."""
    out = ''
    if spec.get('dots'):
        dots = stats_dots(spec.get('length', 0), str(spec.get('value', '0')))
        out += f'<tspan{dots_attr(fid, spec)}>{dots}</tspan>'
    return out + value_markup(fid, spec)


def render_stats_row(template, fields, cols=0):
    """Expand a stats template string into <tspan> markup.

        {k:Text}       -> <tspan class="key">Text</tspan>
        {Label:field}  -> keyed label + dot leader + value (field must be known)
        {field}        -> bare value (with dot leader if the field declares dots)

    The dot leader of the row's first {Label:field} stretches so the line ends
    at `cols`, lining up with the key/value rows (never below MIN_DOTS; so
    `cols=0` gives the row's natural width). Any later {Label:field} falls back
    to the field's fixed-width leader. Unknown {...} tokens and stray braces are
    left as literal text.
    """
    template = re.sub(r'\{k:([^{}]+)\}', lambda m: key_markup(m.group(1)), template)
    flex = []

    def labeled(m):
        label, fid = m.group(1), m.group(2)
        if fid not in fields:
            return m.group(0)
        if flex:
            return f'{key_markup(label)}:{field_markup(fid, fields[fid])}'
        flex.append(fid)
        return f'{key_markup(label)}:{FLEX}{value_markup(fid, fields[fid])}'

    def bare(m):
        fid = m.group(1)
        return field_markup(fid, fields[fid]) if fid in fields else m.group(0)

    template = re.sub(r'\{([^:{}]+):([A-Za-z_]\w*)\}', labeled, template)
    row = re.sub(r'\{([A-Za-z_]\w*)\}', bare, template)
    if not flex:
        return row

    fid = flex[0]
    used = len(PREFIX) + visible_len(row.replace(FLEX, '')) + 2   # + the spaces around the dots
    dots = max(MIN_DOTS, cols - used)
    return row.replace(FLEX, f'<tspan{dots_attr(fid, fields[fid])}> {"." * dots} </tspan>')


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
        fields = section.get('fields') or {}
        if section.get('title'):
            cols = max(cols, len(f"- {section['title']}") + 8)
        for row in section.get('rows', []):
            if is_content(row):
                cols = max(cols, content_len(row) + MIN_DOTS)
            elif fields and isinstance(row, str) and row != 'spacer':
                cols = max(cols, len(PREFIX) + visible_len(render_stats_row(row, fields)))
    return cols


def build_panel(doc, cols):
    y = Y_START
    lines = [divider_line(y, str(doc['header']), cols)]
    for section in doc.get('sections', []):
        fields = section.get('fields') or {}
        if section.get('title'):
            y += 2 * LINE_HEIGHT   # one blank slot before a titled section
            lines.append(divider_line(y, f"- {section['title']}", cols))
        for row in section.get('rows', []):
            y += LINE_HEIGHT
            prefix = f'<tspan x="{PANEL_X}" y="{y}" class="cc">{PREFIX}</tspan>'
            if row == 'spacer' or (isinstance(row, dict) and row.get('spacer')):
                lines.append(prefix)
            elif isinstance(row, dict) and 'raw' in row:
                lines.append(prefix + row['raw'])
            elif fields and isinstance(row, str):
                lines.append(prefix + render_stats_row(row, fields, cols))
            else:
                lines.append(prefix + content_row(row, cols))
    return '\n'.join(lines), y

