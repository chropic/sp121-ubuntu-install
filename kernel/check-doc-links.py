#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check local Markdown file links in current guides and project entry points."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
pages = [ROOT / name for name in ['README.md', 'CONTRIBUTING.md', 'LICENSE.md',
         'SECURITY.md', 'release/README.md', 'firmware/README.md', 'system/README.md']]
pages += list((ROOT / 'docs').glob('*.md'))
pages += list((ROOT / 'docs/developer').glob('*.md'))
pages += [ROOT / 'kernel/README.md', ROOT / 'kernel/ports/v7.3/README.md']
errors = []
for page in pages:
    text = re.sub(r'```.*?```', '', page.read_text(), flags=re.S)
    for url in re.findall(r'!?\[[^\]\n]*\]\(([^\s)]+)\)', text):
        parts = urlsplit(url)
        if parts.scheme or parts.netloc or not parts.path:
            continue
        target = (page.parent / unquote(parts.path)).resolve()
        if not target.is_relative_to(ROOT) or not target.exists():
            errors.append(f'{page.relative_to(ROOT)}: missing local target {url}')
        elif parts.fragment and target.suffix == '.md':
            headings = set()
            counts = {}
            for title in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', target.read_text(), re.M):
                slug = re.sub(r'[^\w\s-]', '', title.lower()).replace(' ', '-')
                count = counts.get(slug, 0)
                headings.add(slug + (f'-{count}' if count else ''))
                counts[slug] = count + 1
            if unquote(parts.fragment) not in headings:
                errors.append(f'{page.relative_to(ROOT)}: missing heading {url}')
for error in errors:
    print(error, file=sys.stderr)
if errors:
    raise SystemExit(1)
print(f'Documentation links passed ({len(pages)} pages).')
