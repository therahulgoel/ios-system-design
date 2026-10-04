#!/usr/bin/env python3
"""Check repository documentation structure without claiming semantic validation."""
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted(p for p in ROOT.rglob('*.md') if '.git' not in p.parts)


def prose_and_fence_errors(path):
    lines = []
    opened = None
    errors = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        marker = re.match(r'^\s*(`{3,}|~{3,})(.*)$', line)
        if marker:
            token, suffix = marker.groups()
            if opened is None:
                opened = (token[0], len(token), number)
            elif token[0] == opened[0] and len(token) >= opened[1] and not suffix.strip():
                opened = None
            continue
        if opened is None:
            lines.append(line)
    if opened:
        errors.append(f'{path.relative_to(ROOT)}:{opened[2]}: unclosed code fence')
    return '\n'.join(lines), errors


def anchors(prose):
    found = set()
    counts = {}
    for line in prose.splitlines():
        match = re.match(r'^#{1,6}\s+(.+?)\s*#*$', line)
        if not match:
            continue
        title = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', match[1])
        title = re.sub(r'<[^>]*>', '', title)
        slug = ''.join(c for c in title.lower() if c in '-_ ' or unicodedata.category(c)[0] in 'LN').replace(' ', '-')
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        found.add(slug if count == 0 else f'{slug}-{count}')
    found.update(re.findall(r'<a\s+(?:name|id)=[\"\']([^\"\']+)', prose))
    return found


def main():
    errors = []
    prosa = {}
    for path in FILES:
        prose, fence_errors = prose_and_fence_errors(path)
        prosa[path] = prose
        errors.extend(fence_errors)
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if any(c in line for c in ('\u2013', '\u2014')):
                errors.append(f'{path.relative_to(ROOT)}:{number}: prohibited long dash')
    for path, prose in prosa.items():
        for match in re.finditer(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', prose):
            target = match[1].strip()
            if target.startswith('<'):
                target = target[1:target.index('>')]
            else:
                target = target.split()[0] if target else ''
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not target:
                continue
            destination = (ROOT / unquote(parsed.path).lstrip('/') if parsed.path.startswith('/') else path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not destination.exists():
                errors.append(f'{path.relative_to(ROOT)}: missing link target {target}')
            elif parsed.fragment and destination.suffix == '.md':
                destination_prose = prosa.get(destination)
                if destination_prose is None:
                    destination_prose, _ = prose_and_fence_errors(destination)
                if unquote(parsed.fragment) not in anchors(destination_prose):
                    errors.append(f'{path.relative_to(ROOT)}: missing anchor {target}')
    readme = (ROOT / 'README.md').read_text()
    for path in sorted((ROOT / 'docs').glob('*.md')):
        if f'(docs/{path.name})' not in readme:
            errors.append(f'README.md: document missing from catalog: {path.name}')
    if errors:
        print('\n'.join(errors))
        return 1
    print(f'Passed: {len(FILES)} Markdown files; local links and anchors, fences, ASCII dash rule, and catalog coverage.')
    print('Not checked: external URL availability, Swift compilation, diagram rendering, or technical correctness.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
