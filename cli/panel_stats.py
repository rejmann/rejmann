"""Write computed numbers into panel.yaml and (re)render the SVGs.

Shared by cli/fetch_stats.py (manual `make stats`) and today.py (CI): both
collect the same GitHub numbers, then call :func:`set_values` so panel.yaml
stays the single source of truth for what the SVGs show, and :func:`render` to
rebuild both themes from it.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PANEL_YAML = os.path.join(ROOT, 'panel.yaml')

# Every field today.py / fetch_stats.py can push into panel.yaml. `age_data`
# lives in a `rows:` entry; the rest are keys of the `fields:` block.
WRITABLE_FIELDS = (
    'age_data', 'repo_data', 'contrib_data', 'star_data',
    'commit_data', 'follower_data', 'loc_data', 'loc_add', 'loc_del',
)


def as_text(value):
    return f'{value:,}' if isinstance(value, int) else str(value)


def _set_one(text, field, value):
    """Replace the `value:` bound to `field`, whether it's a `fields:` key or a
    `rows:` inline map carrying `id: <field>`. Returns (text, n_replacements)."""
    field_form = re.compile(
        rf'(^[ \t]*{re.escape(field)}:[ \t]*\{{[^}}\n]*?value:[ \t]*")[^"\n]*(")', re.M)
    text, hits = field_form.subn(rf'\g<1>{value}\g<2>', text)
    if hits:
        return text, hits

    row_form = re.compile(
        rf'^[ \t]*-[ \t]*\{{[^}}\n]*\bid:[ \t]*{re.escape(field)}\b[^}}\n]*\}}', re.M)
    return row_form.subn(
        lambda m: re.sub(r'(value:[ \t]*")[^"\n]*(")', rf'\g<1>{value}\g<2>', m.group(0), count=1),
        text)


def set_values(mapping, path=PANEL_YAML):
    """Rewrite panel.yaml in place, keeping comments and layout. `mapping` is
    {field_id: number|str}; unknown ids are rejected, missing targets raise."""
    unknown = [k for k in mapping if k not in WRITABLE_FIELDS]
    if unknown:
        raise ValueError(f'not writable into panel.yaml: {", ".join(unknown)}')

    with open(path, encoding='utf-8') as f:
        text = f.read()

    written, missing = {}, []
    for field, value in mapping.items():
        value = as_text(value)
        text, hits = _set_one(text, field, value)
        (written.__setitem__(field, value) if hits else missing.append(field))
    if missing:
        raise SystemExit(f'error: no `value:` to update for {", ".join(missing)} in {path}')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return written


def render():
    """Rebuild dark_mode.svg / light_mode.svg from panel.yaml."""
    subprocess.run([sys.executable, os.path.join(HERE, 'panel_to_svg.py')], check=True)
