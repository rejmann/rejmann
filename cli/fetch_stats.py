#!/usr/bin/env python3
"""Fetch the GitHub numbers, write them into panel.yaml, and regenerate the SVGs.

Pulls the same stats ``today.py`` computes — repos, contributed repos, stars,
commits, followers and lines of code — writes them into panel.yaml via
``panel_stats.set_values`` and rebuilds both themes from it. panel.yaml stays the
single source of truth for what ends up in the SVGs. (In CI, ``today.py`` does
the same thing; this script is the manual entry point / ``make stats``.)

Needs the same environment as ``today.py``: ``ACCESS_TOKEN`` and ``USER_NAME``.

Usage:
    python3 cli/fetch_stats.py               # fetch -> panel.yaml -> render
    python3 cli/fetch_stats.py --no-render   # fetch -> panel.yaml only
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from panel_stats import render, set_values  # noqa: E402

ARCHIVE_OWNER = {'id': 'MDQ6VXNlcjU3MzMxMTM0'}


def collect_stats():
    """Return {field_id: number}, mirroring the sequence in today.py's main."""
    os.chdir(ROOT)                 # cache/ lookups in today.py are CWD-relative
    sys.path.insert(0, ROOT)
    import today                   # deps + env only needed for the actual fetch

    login = os.environ['USER_NAME']
    today.OWNER_ID = today.user_getter(login)[0]   # loc_counter_one_repo reads this global

    total_loc = today.loc_query(['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'], 7)
    commit_data = today.commit_counter(7)
    star_data = today.graph_repos_stars('stars', ['OWNER'])
    repo_data = today.graph_repos_stars('repos', ['OWNER'])
    contrib_data = today.graph_repos_stars('repos', ['OWNER', 'COLLABORATOR', 'ORGANIZATION_MEMBER'])
    follower_data = today.follower_getter(login)

    if today.OWNER_ID == ARCHIVE_OWNER:            # add back repos that were deleted
        archived = today.add_archive()
        for i in range(len(total_loc) - 1):
            total_loc[i] += archived[i]
        contrib_data += archived[-1]
        commit_data += int(archived[-2])

    return {
        'repo_data': repo_data,
        'contrib_data': contrib_data,
        'star_data': star_data,
        'commit_data': commit_data,
        'follower_data': follower_data,
        'loc_data': total_loc[2],
        'loc_add': total_loc[0],
        'loc_del': total_loc[1],
    }


def main():
    written = set_values(collect_stats())
    print(f'panel.yaml updated ({len(written)} fields):')
    for field, value in written.items():
        print(f'  {field:<14} {value}')
    if '--no-render' not in sys.argv[1:]:
        render()


if __name__ == '__main__':
    main()
